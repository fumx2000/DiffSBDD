"""Independent R3 gate for retirement of the legacy four-level mask API.

The evaluator reads the immutable R2 Git tree, classifies every relevant
legacy reference, and checks the live canonical runtime without writing to the
repository, index, or working tree.  It performs no network access, model
forward, training, parameter update, or checkpoint operation.
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
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence


__all__ = (
    "evaluate_covapie_legacy_four_level_mask_retirement_gate_v1",
)


_ERROR = "COVAPIE_LEGACY_FOUR_LEVEL_MASK_RETIREMENT_GATE_INVALID"
_VERSION = "covapie_legacy_four_level_mask_retirement_gate_v1"
_R2_COMMIT = "8711c1899759ca4c1f4a24f7ff9782b81a257245"
_R2_PARENT = "963562e2da9bcc14d67d075a49a7770aecaa2e68"
_R2_TREE = "0824061a545d54f6d11cc4b6eb20c2d605f595db"
_R2_SUBJECT = "retire CovaPIE legacy four-level core mask API and consumers R2 v1"
_R3_SUBJECT = "add CovaPIE legacy four-level mask retirement gate v1"
_MAX_BLOB_BYTES = 32 * 1024 * 1024

_R2_FILES: dict[str, str] = {
    "src/covalent_ext/masking.py": "a11ac211cedf14168c2866be960aa99703082b207234b016db0b8929c895c3c6",
    "src/covalent_ext/schema.py": "06f8d3fb6cc402ffdd03660c31fe849e8718b7ba3960b50584fb87a0941de64a",
    "src/covalent_ext/dataset.py": "44605b78b428156f11b398307299506ddc899269d355de78cce3853d78f74a2c",
    "scripts/check_covalent_masking.py": "185ece63a6c8434e39365a058c2a48c7dd2e8ec390beaa7b883d2569f469d9bc",
    "scripts/check_covalent_dataset.py": "623ce2a046c325700f27629484dfabeeecc43a6efe5eae56c8a9ae64b30d1e94",
    "scripts/check_covalent_real_small.py": "10a8ab2c74b1808ddce79c49f043cac272dd44c62bd6816e59c33d3ec2b01a6b",
    "tests/test_covalent_masking.py": "750ccc128a09f54e5b9898cb0a2a86eef89ada920395079ce2551b35b4965a8b",
    "tests/test_b3_scaffold_only_mask_implementation_v0.py": "7a13b09bd9908987e9597499415e817b6ed8c34854a08c4741227e5610419c93",
    "tests/test_covalent_real_small_builder.py": "e7e320d8316e1b1d6dfbdae7b417b2423c05d954fb3b0dfe4a6ce28c6f985538",
    "tests/test_covalent_dataset.py": "49ba7adc87441f67f8b428462add02409335df1a9c8b97138e0652b56b934e17",
}
_R3_PATHS = (
    "src/covalent_ext/covapie_legacy_four_level_mask_retirement_gate_v1.py",
    "tests/test_covapie_legacy_four_level_mask_retirement_gate_v1.py",
    "scripts/check_covapie_legacy_four_level_mask_retirement_gate_v1.py",
    "docs/covapie_legacy_four_level_mask_retirement_gate_v1_guide.md",
)
_LEGACY_SYMBOLS = (
    "MaskType",
    "build_four_level_mask",
    "MASK_BUILDERS",
    "mask_warhead",
    "mask_linker_and_warhead",
    "mask_scaffold",
    "mask_whole_ligand",
)
_LEGACY_CLI = "--mask_level"
_LEGACY_SHORT_TOKENS = ("A", "B", "B2", "B3", "C")
_CANONICAL_SEMANTICS = (
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
)
_CANONICAL_LEVELS = (
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "B3_scaffold_only",
    "C_scaffold_linker_warhead",
)
_DATASET_CONSUMERS = (
    "scripts/check_covalent_dataset.py",
    "scripts/check_covalent_real_small.py",
    "tests/test_covalent_real_small_builder.py",
    "tests/test_covalent_dataset.py",
)
_NEGATIVE_TEST_PATH = "tests/test_real_covalent_feature_mapping_loader_gate_v0.py"
_NEGATIVE_TEST_SHA256 = "b6542c898dddf73f3fe4c307d373a46c47294d857dffb42f58abdc3e00c80309"
_HISTORICAL_B3_FILES = {
    "src/covalent_ext/b3_scaffold_only_mask_implementation.py": "e142d6aa7f64722f4e07391f80d7106c9a3b7cd4a7dcfed77b69231e209575d5",
    "scripts/check_b3_scaffold_only_mask_implementation_v0.py": "16fe45ec778ab4e50181eeaa03b1a0e1a79bea9cc4ce693f5d423c08f122548b",
}
_SCAN_METHODS = (
    "python_ast",
    "notebook_json_code_cell_ast",
    "structured_schema_inspection",
    "controlled_text_search",
)
_CLASSIFICATIONS = (
    "active_runtime",
    "current_positive_test",
    "negative_rejection_evidence",
    "historical_read_only",
    "design_or_documentation_evidence",
    "gate_control_evidence",
)

LEGACY_FOUR_LEVEL_MASK_RETIREMENT_GATE_RESPONSE_FIELDS = (
    "legacy_four_level_mask_retirement_gate_version",
    "source_R2_commit",
    "source_R2_parent",
    "source_R2_tree",
    "source_R2_subject",
    "source_R2_scope",
    "source_R2_file_sha256s",
    "scan_subject_commit",
    "scan_evidence_mode",
    "scan_methods",
    "scanned_tracked_path_count",
    "scanned_python_path_count",
    "scanned_notebook_path_count",
    "scanned_notebook_code_cell_count",
    "python_parse_error_count",
    "active_legacy_reference_records",
    "active_legacy_reference_count",
    "unresolved_legacy_reference_records",
    "unresolved_legacy_reference_count",
    "retained_read_only_reference_records",
    "retained_read_only_reference_count",
    "reference_classification_counts",
    "required_negative_runtime_evidence",
    "historical_read_only_legacy_evidence_retained",
    "negative_legacy_token_rejection_evidence_retained",
    "legacy_core_provider_removed",
    "legacy_schema_type_removed",
    "legacy_cli_flag_removed",
    "canonical_mask_semantic_names",
    "canonical_mask_count",
    "canonical_B2_semantic",
    "canonical_B3_semantic",
    "sixth_mask_added",
    "canonical_five_level_runtime_complete",
    "retirement_evidence_passed",
    "R3_gate_implemented",
    "R3_gate_lifecycle_profile",
    "R3_gate_commit",
    "R3_gate_committed",
    "R3_gate_published",
    "ready_for_R3_commit_review",
    "legacy_four_level_full_runtime_retired",
    "ready_for_repository_cli_forwarding_C1",
    "recommended_next_step",
    "training_or_parameter_update",
    "feature_semantics_audit_required_before_training",
    "legacy_four_level_mask_retirement_gate_response_sha256",
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _git_bytes(repo_root: Path, arguments: Sequence[str]) -> bytes:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        env={**os.environ, "LC_ALL": "C", "LANG": "C"},
        check=False,
        capture_output=True,
        timeout=30,
    )
    if completed.returncode != 0 or completed.stderr:
        raise ValueError(_ERROR)
    return completed.stdout


def _git_text(repo_root: Path, arguments: Sequence[str]) -> str:
    try:
        return _git_bytes(repo_root, arguments).decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ValueError(_ERROR) from error


def _is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=repo_root,
        env={**os.environ, "LC_ALL": "C", "LANG": "C"},
        check=False,
        capture_output=True,
        timeout=30,
    )
    if completed.stdout or completed.stderr or completed.returncode not in (0, 1):
        raise ValueError(_ERROR)
    return completed.returncode == 0


def _canonical_relative_path(relative_path: str) -> PurePosixPath:
    try:
        parsed = PurePosixPath(relative_path)
        if (
            type(relative_path) is not str
            or not relative_path
            or "\x00" in relative_path
            or parsed.is_absolute()
            or ".." in parsed.parts
            or parsed.as_posix() != relative_path
            or relative_path.startswith("./")
            or "//" in relative_path
        ):
            raise ValueError(_ERROR)
        return parsed
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _git_snapshot_blob_bytes(
    repo_root: Path,
    *,
    commit: str,
    relative_path: str,
    expected_sha256: str | None = None,
    maximum: int = _MAX_BLOB_BYTES,
) -> bytes:
    """Read one nonempty immutable Git blob using read-only object commands."""

    try:
        _canonical_relative_path(relative_path)
        if (
            type(repo_root) is not type(Path())
            or not repo_root.is_dir()
            or repo_root.is_symlink()
            or type(commit) is not str
            or re.fullmatch(r"[0-9a-f]{40}", commit) is None
            or (
                expected_sha256 is not None
                and (
                    type(expected_sha256) is not str
                    or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None
                )
            )
            or type(maximum) is not int
            or type(maximum) is bool
            or maximum <= 1
        ):
            raise ValueError(_ERROR)
        object_spec = f"{commit}:{relative_path}"
        if _git_bytes(repo_root, ["cat-file", "-t", object_spec]) != b"blob\n":
            raise ValueError(_ERROR)
        size_payload = _git_bytes(repo_root, ["cat-file", "-s", object_spec])
        try:
            size = int(size_payload.decode("ascii").strip())
        except (UnicodeDecodeError, ValueError) as error:
            raise ValueError(_ERROR) from error
        if size <= 0 or size >= maximum:
            raise ValueError(_ERROR)
        payload = _git_bytes(repo_root, ["show", object_spec])
        if len(payload) != size:
            raise ValueError(_ERROR)
        if expected_sha256 is not None and _sha256(payload) != expected_sha256:
            raise ValueError(_ERROR)
        return payload
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _git_snapshot_blob_batch(
    repo_root: Path, *, commit: str, relative_paths: Sequence[str]
) -> dict[str, bytes]:
    """Read a duplicate-free set of immutable blobs in one batch process."""

    try:
        if (
            type(commit) is not str
            or re.fullmatch(r"[0-9a-f]{40}", commit) is None
            or not relative_paths
            or len(relative_paths) != len(set(relative_paths))
        ):
            raise ValueError(_ERROR)
        for relative_path in relative_paths:
            _canonical_relative_path(relative_path)
        request = "".join(f"{commit}:{path}\n" for path in relative_paths).encode("utf-8")
        completed = subprocess.run(
            ["git", "cat-file", "--batch"],
            cwd=repo_root,
            env={**os.environ, "LC_ALL": "C", "LANG": "C"},
            input=request,
            check=False,
            capture_output=True,
            timeout=60,
        )
        if completed.returncode != 0 or completed.stderr:
            raise ValueError(_ERROR)
        stream = io.BytesIO(completed.stdout)
        result: dict[str, bytes] = {}
        for relative_path in relative_paths:
            header = stream.readline()
            match = re.fullmatch(rb"[0-9a-f]{40} blob ([0-9]+)\n", header)
            if match is None:
                raise ValueError(_ERROR)
            size = int(match.group(1))
            if size <= 0 or size >= _MAX_BLOB_BYTES:
                raise ValueError(_ERROR)
            payload = stream.read(size)
            if len(payload) != size or stream.read(1) != b"\n":
                raise ValueError(_ERROR)
            result[relative_path] = payload
        if stream.read() or len(result) != len(relative_paths):
            raise ValueError(_ERROR)
        return result
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _read_live_regular_file(
    repo_root: Path,
    relative_path: str,
    *,
    require_non_executable: bool = False,
) -> bytes:
    """Read one bounded live regular file without accepting symlink traversal."""

    try:
        parsed = _canonical_relative_path(relative_path)
        if (
            type(repo_root) is not type(Path())
            or not repo_root.is_dir()
            or repo_root.is_symlink()
            or type(require_non_executable) is not bool
        ):
            raise ValueError(_ERROR)
        current = repo_root
        for component in parsed.parts:
            current = current / component
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                raise ValueError(_ERROR)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_size <= 0
            or metadata.st_size >= _MAX_BLOB_BYTES
            or (require_non_executable and metadata.st_mode & 0o111)
        ):
            raise ValueError(_ERROR)
        with current.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            if (
                not stat.S_ISREG(opened.st_mode)
                or (opened.st_dev, opened.st_ino) != (metadata.st_dev, metadata.st_ino)
            ):
                raise ValueError(_ERROR)
            payload = handle.read(_MAX_BLOB_BYTES)
        if len(payload) != metadata.st_size:
            raise ValueError(_ERROR)
        return payload
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _bind_live_canonical_core(repo_root: Path) -> None:
    """Bind the three imported canonical providers to their immutable R2 blobs."""

    for relative_path in (
        "src/covalent_ext/masking.py",
        "src/covalent_ext/schema.py",
        "src/covalent_ext/dataset.py",
    ):
        live_payload = _read_live_regular_file(
            repo_root, relative_path, require_non_executable=True
        )
        snapshot_payload = _git_snapshot_blob_bytes(
            repo_root,
            commit=_R2_COMMIT,
            relative_path=relative_path,
            expected_sha256=_R2_FILES[relative_path],
        )
        if live_payload != snapshot_payload:
            raise ValueError(_ERROR)


def _r2_source_evidence(repo_root: Path) -> tuple[list[str], list[str]]:
    metadata = _git_text(
        repo_root,
        ["show", "-s", "--format=%H%x00%P%x00%T%x00%s%x00%b", _R2_COMMIT],
    )
    parts = metadata.rstrip("\n").split("\x00")
    if parts != [_R2_COMMIT, _R2_PARENT, _R2_TREE, _R2_SUBJECT, ""]:
        raise ValueError(_ERROR)
    scope = _git_text(
        repo_root,
        ["diff-tree", "--no-commit-id", "--name-only", "-r", _R2_COMMIT],
    ).splitlines()
    if len(scope) != len(set(scope)) or set(scope) != set(_R2_FILES):
        raise ValueError(_ERROR)
    for relative_path, expected_sha256 in _R2_FILES.items():
        row = _git_text(repo_root, ["ls-tree", _R2_COMMIT, "--", relative_path])
        if not row.startswith("100644 blob ") or not row.endswith(f"\t{relative_path}\n"):
            raise ValueError(_ERROR)
        _git_snapshot_blob_bytes(
            repo_root,
            commit=_R2_COMMIT,
            relative_path=relative_path,
            expected_sha256=expected_sha256,
        )
    if not _is_ancestor(repo_root, _R2_COMMIT, "HEAD") or not _is_ancestor(
        repo_root, _R2_COMMIT, "origin/main"
    ):
        raise ValueError(_ERROR)
    paths = _git_text(
        repo_root, ["ls-tree", "-r", "--name-only", _R2_COMMIT]
    ).splitlines()
    if not paths or len(paths) != len(set(paths)):
        raise ValueError(_ERROR)
    for relative_path in paths:
        _canonical_relative_path(relative_path)
    return sorted(scope), paths


def _attribute_chain(node: ast.AST) -> str | None:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def _literal_strings(node: ast.AST) -> list[tuple[str, int]]:
    return [
        (child.value, child.lineno)
        for child in ast.walk(node)
        if isinstance(child, ast.Constant) and type(child.value) is str
    ]


def _raw_python_records(tree: ast.AST, relative_path: str) -> list[tuple[str, str, str, str]]:
    records: set[tuple[str, str, str, str]] = set()

    def add(line: int, symbol: str, kind: str) -> None:
        records.add((relative_path, str(line), symbol, kind))

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in _LEGACY_SYMBOLS:
            add(node.lineno, node.name, "python_definition")
        elif isinstance(node, ast.ClassDef) and node.name in _LEGACY_SYMBOLS:
            add(node.lineno, node.name, "python_class_definition")
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if alias.name in _LEGACY_SYMBOLS:
                    add(node.lineno, alias.name, "python_import")
        if isinstance(node, ast.Name) and node.id in _LEGACY_SYMBOLS:
            add(node.lineno, node.id, "python_name")
        if isinstance(node, ast.Attribute) and node.attr in _LEGACY_SYMBOLS:
            add(node.lineno, node.attr, "python_attribute")
        if isinstance(node, ast.Call):
            called = _attribute_chain(node.func)
            final_name = called.split(".")[-1] if called else None
            if final_name in _LEGACY_SYMBOLS:
                add(node.lineno, final_name, "python_call")
            if final_name == "add_argument" and node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant) and first.value == _LEGACY_CLI:
                    add(first.lineno, _LEGACY_CLI, "cli_add_argument")
                for keyword in node.keywords:
                    if keyword.arg == "choices":
                        for token, line in _literal_strings(keyword.value):
                            if token in _LEGACY_SHORT_TOKENS:
                                add(line, token, "exact_short_token_choice")
            if final_name in {"build_canonical_mask", "resolve_canonical_mask_semantic", "build_mask"}:
                for token, line in _literal_strings(node):
                    if token in _LEGACY_SHORT_TOKENS:
                        add(line, token, "short_token_runtime_call")
        if isinstance(node, ast.Constant) and type(node.value) is str:
            if node.value in _LEGACY_SYMBOLS:
                add(node.lineno, node.value, "exact_legacy_string_literal")
            elif node.value == _LEGACY_CLI:
                add(node.lineno, node.value, "exact_legacy_cli_literal")
        if isinstance(node, ast.Compare):
            comparison_names = {
                child.id for child in ast.walk(node) if isinstance(child, ast.Name)
            } | {
                child.attr for child in ast.walk(node) if isinstance(child, ast.Attribute)
            }
            if any(
                re.search(r"mask|level|semantic|alias|token", name, re.I)
                for name in comparison_names
            ):
                for token, line in _literal_strings(node):
                    if token in _LEGACY_SHORT_TOKENS:
                        add(line, token, "exact_short_token_comparison")
        if isinstance(node, ast.Subscript):
            item = node.slice
            value_chain = _attribute_chain(node.value) or ""
            if (
                isinstance(item, ast.Constant)
                and item.value in _LEGACY_SHORT_TOKENS
                and re.search(r"mask", value_chain, re.I)
            ):
                add(item.lineno, item.value, "exact_short_subscript_key")
            chain = _attribute_chain(node.value)
            if chain in {"Literal", "typing.Literal"}:
                for token, line in _literal_strings(item):
                    if token in _LEGACY_SHORT_TOKENS:
                        add(line, token, "short_token_literal_type")
        if isinstance(node, (ast.For, ast.AsyncFor)):
            target_names = {
                child.id for child in ast.walk(node.target) if isinstance(child, ast.Name)
            }
            iter_strings = _literal_strings(node.iter)
            rejection_context = any(
                re.search(r"unsupported|rejected|invalid", name, re.I)
                for name in target_names
            ) or any(value in _LEGACY_SYMBOLS for value, _line in iter_strings)
            if rejection_context:
                for token, line in iter_strings:
                    if token in _LEGACY_SHORT_TOKENS:
                        add(line, token, "negative_short_token_collection")
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            target_names = {
                child.id
                for target in targets
                for child in ast.walk(target)
                if isinstance(child, ast.Name)
            } | {
                child.attr
                for target in targets
                for child in ast.walk(target)
                if isinstance(child, ast.Attribute)
            }
            if (
                isinstance(value, (ast.List, ast.Tuple, ast.Set, ast.Dict))
                and any(
                    re.search(r"mask|level|semantic|alias|token", name, re.I)
                    for name in target_names
                )
            ):
                values = [value for value, _line in _literal_strings(value)]
                token_values = [value for value in values if value in _LEGACY_SHORT_TOKENS]
                if len(token_values) >= 4 and set(token_values) >= {"A", "B", "B2", "C"}:
                    for token, line in _literal_strings(value):
                        if token in _LEGACY_SHORT_TOKENS:
                            kind = (
                                "exact_short_dictionary_key"
                                if isinstance(value, ast.Dict)
                                else "exact_short_token_collection"
                            )
                            add(line, token, kind)
    return sorted(records)


def _sanitize_notebook_code(source: str) -> str:
    lines = source.splitlines()
    return "\n".join(
        "pass" if line.lstrip().startswith(("%", "!")) else line for line in lines
    )


def _text_has_exact(text: str, token: str) -> bool:
    if token.startswith("--"):
        return token in text
    return re.search(
        rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])", text
    ) is not None


def _controlled_text_records(text: str, relative_path: str) -> list[tuple[str, str, str, str]]:
    records: set[tuple[str, str, str, str]] = set()
    for line_number, line in enumerate(text.splitlines(), start=1):
        for symbol in (*_LEGACY_SYMBOLS, _LEGACY_CLI):
            if _text_has_exact(line, symbol):
                records.add((relative_path, str(line_number), symbol, "controlled_text_exact_reference"))
        if PurePosixPath(relative_path).suffix.lower() == ".md":
            for token in _LEGACY_SHORT_TOKENS:
                relevant_context = bool(
                    re.search(r"mask|canonical|legacy|historical|short token|alias", line, re.I)
                )
                code_span = relevant_context and f"`{token}`" in line
                b2_b3_context = token in {"B2", "B3"} and relevant_context and _text_has_exact(line, token)
                exact_collection = bool(
                    re.search(r"(?<![A-Za-z0-9_])A/B/B2(?:/B3)?/C(?![A-Za-z0-9_])", line)
                )
                collection_member = exact_collection and (
                    token != "B3" or "/B3/" in line
                )
                if code_span or b2_b3_context or collection_member:
                    records.add((relative_path, str(line_number), token, "controlled_text_short_alias_evidence"))
    return sorted(records)


def _structured_short_token_records(
    payload: bytes, relative_path: str
) -> list[tuple[str, str, str, str]]:
    suffix = PurePosixPath(relative_path).suffix.lower()
    records: set[tuple[str, str, str, str]] = set()
    if suffix == ".json":
        try:
            value = json.loads(payload)
        except Exception as error:
            raise ValueError(_ERROR) from error

        def walk(item: object, location: str, mask_context: bool) -> None:
            if isinstance(item, dict):
                for key, child in item.items():
                    key_text = str(key)
                    child_context = bool(
                        re.search(
                            r"(^|_)(mask_(level|type|semantic|alias)|short_mask_tokens?|"
                            r"mask_levels?|mask_aliases?|legacy_mask_(level|token)s?)(_|$)",
                            key_text,
                            re.I,
                        )
                    )
                    if child_context and key_text in _LEGACY_SHORT_TOKENS:
                        records.add((relative_path, location, key_text, "structured_json_short_key"))
                    walk(child, f"{location}.{key_text}", child_context)
            elif isinstance(item, list):
                for index, child in enumerate(item):
                    walk(child, f"{location}[{index}]", mask_context)
            elif mask_context and type(item) is str and item in _LEGACY_SHORT_TOKENS:
                records.add((relative_path, location, item, "structured_json_short_value"))

        walk(value, "$", False)
    elif suffix == ".csv":
        try:
            text = payload.decode("utf-8", errors="strict")
            rows = list(csv.DictReader(io.StringIO(text)))
        except Exception as error:
            raise ValueError(_ERROR) from error
        for row_number, row in enumerate(rows, start=2):
            for field, value in row.items():
                if value in _LEGACY_SHORT_TOKENS and bool(
                    re.search(
                        r"(^|_)(mask_(level|type|semantic|alias)|short_mask_token|"
                        r"legacy_mask_(level|token))(_|$)",
                        field or "",
                        re.I,
                    )
                ):
                    records.add((relative_path, str(row_number), value, "structured_csv_short_value"))
    return sorted(records)


_REVIEWED_DESIGN_DOC_NAMES = (
    "b3_backward_smoke_v0_summary.md",
    "b3_pretrained_masked_loss_smoke_v0_summary.md",
    "b3_scaffold_only_mask_design_v0_summary.md",
    "b3_scaffold_only_mask_implementation_v0_summary.md",
    "b3_scaffold_only_mask_sweep_v0_summary.md",
    "b3_single_optimizer_step_smoke_v0_summary.md",
    "covalent_data_schema.md",
    "covalent_real_dataset_building.md",
    "covapie_batch_raw_read_extraction_design_gate_v0_summary.md",
    "covapie_batch_raw_read_extraction_smoke_v0_summary.md",
    "covapie_batch_scale_data_preparation_design_gate_v0_summary.md",
    "covapie_bulk_download_admission_admit_004_residue_identity_atom_name_semantics_design_gate_v1_summary.md",
    "covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_contract_v1_summary.md",
    "covapie_bulk_download_admission_covalent_residue_locator_historical_raw_fingerprint_authority_consolidation_gate_v1_summary.md",
    "covapie_bulk_download_design_gate_v0_summary.md",
    "covapie_candidate_allowlist_materialization_smoke_v0_summary.md",
    "covapie_candidate_allowlist_qa_gate_v0_summary.md",
    "covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1_summary.md",
    "covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1_summary.md",
    "covapie_covalent_bond_atom_pair_encoding_contract_design_gate_v1_summary.md",
    "covapie_covpdb_metadata_only_acquisition_smoke_v0_summary.md",
    "covapie_current11_five_auxiliary_module_label_consumption_readiness_design_v1_guide.md",
    "covapie_current11_pocket_atom_identity_alignment_v1_guide.md",
    "covapie_current11_unified_effective_authority_view_v1_guide.md",
    "covapie_diffsbdd_loader_adapter_implementation_qa_gate_v0_summary.md",
    "covapie_extraction_qa_gate_v0_summary.md",
    "covapie_feature_semantics_audit_gate_v0_summary.md",
    "covapie_feature_semantics_resolution_design_gate_v0_summary.md",
    "covapie_feature_semantics_resolution_smoke_qa_gate_v0_summary.md",
    "covapie_feature_semantics_resolution_smoke_v0_summary.md",
    "covapie_feature_semantics_tensorization_audit_gate_v0_summary.md",
    "covapie_final_dataset_materialization_smoke_v0_summary.md",
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1_summary.md",
    "covapie_sample_index_design_gate_v0_summary.md",
    "covapie_sample_index_materialization_smoke_v0_summary.md",
    "covapie_sample_index_qa_gate_v0_summary.md",
    "covapie_target_residue_atom_condition_adapter_design_v1_guide.md",
    "covapie_target_residue_atom_condition_contract_design_v1_guide.md",
    "covapie_target_residue_atom_condition_repository_cli_forwarding_design_v1_guide.md",
    "diffsbdd_atomwise_loss_hook_shape_sweep_v0_summary.md",
    "diffsbdd_forward_mask_level_sweep_v0_summary.md",
    "longer_no_checkpoint_training_dry_run_review_v0_summary.md",
    "longer_no_checkpoint_training_dry_run_v0_summary.md",
    "optimizer_smoke_design_v0_summary.md",
    "pretrained_masked_loss_microbatch_design_v0_summary.md",
    "pretrained_masked_loss_smoke_v0_summary.md",
    "real_covalent_confirmed_candidate_diffsbdd_loader_adapter_design_gate_v0_summary.md",
    "real_covalent_confirmed_candidate_diffsbdd_loader_adapter_implementation_smoke_v0_summary.md",
    "real_covalent_confirmed_candidate_loader_shape_dry_run_design_gate_v0_summary.md",
    "real_covalent_confirmed_candidate_loader_shape_dry_run_execution_smoke_v0_summary.md",
    "real_covalent_confirmed_candidate_loader_shape_dry_run_qa_gate_v0_summary.md",
    "real_covalent_confirmed_candidate_model_input_design_gate_v0_summary.md",
    "real_covalent_confirmed_candidate_model_input_materialization_smoke_v0_summary.md",
    "real_covalent_confirmed_candidate_model_input_qa_gate_v0_summary.md",
    "real_covalent_confirmed_candidate_sample_index_design_gate_v0_summary.md",
    "real_covalent_confirmed_candidate_sample_index_materialization_smoke_v0_summary.md",
    "real_covalent_confirmed_candidate_sample_index_qa_gate_v0_summary.md",
    "real_covalent_leakage_aware_split_design_gate_v0_summary.md",
    "real_covalent_training_loop_design_gate_v0_summary.md",
    "tiny_training_dry_run_design_v0_summary.md",
    "training_tensor_batch_adapter_v0_summary.md",
    "training_tensor_design_review_summary.md",
)

_REVIEWED_DESIGN_SOURCE_NAMES = (
    "b3_scaffold_only_mask_design.py",
    "covapie_batch_raw_read_extraction_design_gate.py",
    "covapie_batch_raw_read_extraction_smoke.py",
    "covapie_batch_scale_data_preparation_design_gate.py",
    "covapie_batch_scale_data_preparation_smoke.py",
    "covapie_bulk_download_admission_admit_015_mandatory_training_authorization_enforcement_contract_design_gate.py",
    "covapie_bulk_download_admission_candidate_record_id_semantics_design_gate.py",
    "covapie_bulk_download_admission_candidate_record_id_semantics_integration_gate.py",
    "covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_contract_design_gate.py",
    "covapie_bulk_download_admission_combined_permission_semantics_contract_design_gate.py",
    "covapie_bulk_download_admission_covalent_residue_locator_historical_raw_fingerprint_authority_consolidation_gate.py",
    "covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_design_gate.py",
    "covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_integration_gate.py",
    "covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_design_gate.py",
    "covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_smoke.py",
    "covapie_bulk_download_admission_covalent_residue_locator_real_parser_provider_pipeline_integration_design_gate.py",
    "covapie_bulk_download_admission_covalent_residue_locator_real_raw_source_precondition_gate.py",
    "covapie_bulk_download_admission_ligand_comp_id_semantics_design_gate.py",
    "covapie_bulk_download_admission_ligand_comp_id_semantics_integration_gate.py",
    "covapie_bulk_download_admission_pdb_identifier_semantics_design_gate.py",
    "covapie_bulk_download_admission_pdb_identifier_semantics_integration_gate.py",
    "covapie_bulk_download_design_gate.py",
    "covapie_bulk_download_stage_orchestration_action_permission_bridge_in_memory_integration_smoke_v1.py",
    "covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_in_memory_integration_smoke_v1.py",
    "covapie_candidate_allowlist_creation_gate.py",
    "covapie_candidate_allowlist_materialization_design_gate.py",
    "covapie_candidate_allowlist_materialization_smoke.py",
    "covapie_candidate_allowlist_qa_gate.py",
    "covapie_candidate_metadata_materialization_design_gate.py",
    "covapie_candidate_metadata_materialization_qa_gate.py",
    "covapie_candidate_metadata_materialization_smoke.py",
    "covapie_canonical_final_dataset_bulk_download_admission_design_gate.py",
    "covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate.py",
    "covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_evidence_validation_v1.py",
    "covapie_covalent_bond_atom_pair_encoding_contract_design_gate_v1.py",
    "covapie_covpdb_complex_card_metadata_acquisition_qa_gate.py",
    "covapie_covpdb_raw_structure_event_annotation_design_gate.py",
    "covapie_covpdb_raw_structure_event_annotation_qa_gate.py",
    "covapie_covpdb_raw_structure_event_annotation_smoke.py",
    "covapie_current11_five_auxiliary_module_label_consumption_readiness_design_v1.py",
    "covapie_cys_sg_acquired_annotation_manual_review_gate.py",
    "covapie_cys_sg_discovery_support_review_gate.py",
    "covapie_cys_sg_future_struct_conn_controlled_raw_acquisition_gate.py",
    "covapie_cys_sg_future_struct_conn_crosscheck_execution_gate.py",
    "covapie_cys_sg_future_struct_conn_crosscheck_gate.py",
    "covapie_cys_sg_ligand_covale_annotation_alignment_gate.py",
    "covapie_cys_sg_manual_review_decision_application_gate.py",
    "covapie_cys_sg_manual_review_decision_input_by_user.py",
    "covapie_cys_sg_ready_candidate_materialization_gate.py",
    "covapie_cys_sg_result_review_decision_application_gate.py",
    "covapie_cys_sg_result_review_decision_input_by_user.py",
    "covapie_cys_sg_struct_conn_crosscheck_result_review_gate.py",
    "covapie_cys_sg_targeted_annotation_acquisition_smoke.py",
    "covapie_cys_sg_targeted_metadata_expansion_gate.py",
    "covapie_cys_sg_targeted_metadata_expansion_next_batch_gate.py",
    "covapie_cys_sg_targeted_metadata_next_batch_acquisition_smoke.py",
    "covapie_diffsbdd_loader_adapter_implementation_qa_gate.py",
    "covapie_external_metadata_index_download_design_gate.py",
    "covapie_external_source_registry_configuration_gate.py",
    "covapie_extraction_qa_gate.py",
    "covapie_final_dataset_design_gate.py",
    "covapie_final_dataset_materialization_smoke.py",
    "covapie_final_dataset_qa_gate.py",
    "covapie_final_dataset_qa_gate_v1.py",
    "covapie_final_dataset_smoke.py",
    "covapie_final_training_feature_semantics_and_unknown_atom_policy_audit_v1.py",
    "covapie_independent_group_expansion_acquisition_execution_smoke.py",
    "covapie_independent_group_expansion_batch_independence_evidence_materialization_smoke.py",
    "covapie_independent_group_expansion_batch_sample_index_materialization_smoke.py",
    "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke.py",
    "covapie_independent_group_expansion_candidate_review_gate.py",
    "covapie_independent_group_expansion_design_gate.py",
    "covapie_independent_group_expansion_struct_conn_crosscheck_smoke.py",
    "covapie_leakage_split_design_gate.py",
    "covapie_leakage_split_review_gate.py",
    "covapie_metadata_source_inventory_gate.py",
    "covapie_real_provider_export_blocking_row_quarantine_materialization_v1.py",
    "covapie_real_provider_export_blocking_rows_resolution_or_quarantine_policy_audit_v1.py",
    "covapie_sample_index_design_gate.py",
    "covapie_sample_index_materialization_smoke.py",
    "covapie_sample_index_qa_gate.py",
    "covapie_sample_preparation_design_gate.py",
    "covapie_sample_preparation_execution_smoke.py",
    "covapie_sample_preparation_qa_gate.py",
    "covapie_small_pilot_candidate_expansion_gate.py",
    "covapie_small_pilot_download_manifest_gate.py",
    "covapie_small_pilot_manifest_rerun_gate.py",
    "covapie_specialized_covalent_database_source_acquisition_design_gate.py",
    "covapie_split_leakage_smoke.py",
    "covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke_v1.py",
    "covapie_target_residue_atom_condition_adapter_design_v1.py",
    "covapie_target_residue_atom_condition_repository_cli_forwarding_design_v1.py",
    "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1.py",
    "covapie_unified_independence_group_assignment_and_sample_index_merge_smoke.py",
    "real_covalent_confirmed_candidate_diffsbdd_loader_adapter_design_gate.py",
    "real_covalent_confirmed_candidate_diffsbdd_loader_adapter_implementation_smoke.py",
    "real_covalent_confirmed_candidate_loader_shape_dry_run_design_gate.py",
    "real_covalent_confirmed_candidate_loader_shape_dry_run_execution_smoke.py",
    "real_covalent_confirmed_candidate_loader_shape_dry_run_qa_gate.py",
    "real_covalent_confirmed_candidate_model_input_design_gate.py",
    "real_covalent_confirmed_candidate_model_input_materialization_smoke.py",
    "real_covalent_confirmed_candidate_model_input_qa_gate.py",
    "real_covalent_confirmed_candidate_sample_index_design_gate.py",
    "real_covalent_confirmed_candidate_sample_index_materialization_smoke.py",
    "real_covalent_confirmed_candidate_sample_index_qa_gate.py",
)

_REVIEWED_GATE_SCRIPT_NAMES = (
    "check_covalent_masking.py",
    "check_covapie_bulk_download_admission_admit_015_mandatory_training_authorization_enforcement_contract_v1.py",
    "check_covapie_bulk_download_stage_orchestration_action_permission_bridge_contract_v1.py",
    "check_covapie_bulk_download_stage_orchestration_action_permission_bridge_v1.py",
    "check_covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_v1.py",
    "check_covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_v1.py",
    "check_covapie_covalent_bond_atom_pair_current_semantics_and_downstream_consumers_audit_gate_v1.py",
    "check_covapie_covalent_bond_atom_pair_encoding_contract_design_gate_v1.py",
    "check_covapie_post_admission_control_plane_completion_and_next_training_preparation_blocker_review_gate_v1.py",
    "check_covapie_stage_global_rule_evaluation_orchestration_v1.py",
    "check_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1.py",
)

_REVIEWED_GATE_TEST_NAMES = (
    "test_covalent_inpaint_demo_mask_semantic_v1.py",
    "test_covalent_masking.py",
    "test_covapie_batch_scale_data_preparation_design_gate_v0.py",
    "test_covapie_batch_scale_data_preparation_smoke_v0.py",
    "test_covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_contract_v1.py",
    "test_covapie_bulk_download_admission_combined_permission_semantics_contract_v1.py",
    "test_covapie_bulk_download_admission_covalent_residue_locator_minimal_schema_extension_design_gate_v1.py",
    "test_covapie_bulk_download_admission_covalent_residue_locator_parser_provider_provenance_export_smoke_v1.py",
    "test_covapie_bulk_download_admission_covalent_residue_locator_real_parser_provider_pipeline_integration_design_gate_v1.py",
    "test_covapie_bulk_download_admission_covalent_residue_locator_real_raw_source_precondition_gate_v1.py",
    "test_covapie_bulk_download_admission_ligand_comp_id_semantics_design_gate_v1.py",
    "test_covapie_bulk_download_admission_pdb_identifier_semantics_integration_gate_v1.py",
    "test_covapie_covalent_bond_atom_pair_encoding_contract_design_gate_v1.py",
    "test_covapie_covpdb_complex_card_metadata_acquisition_qa_gate_v0.py",
    "test_covapie_covpdb_raw_structure_event_annotation_design_gate_v0.py",
    "test_covapie_feature_semantics_audit_gate_v0.py",
    "test_covapie_final_dataset_materialization_smoke_v0.py",
    "test_covapie_final_dataset_qa_gate_v1.py",
    "test_covapie_final_training_feature_semantics_and_unknown_atom_policy_audit_v1.py",
    "test_covapie_independent_group_expansion_batch_independence_evidence_materialization_smoke_v0.py",
    "test_covapie_independent_group_expansion_batch_sample_index_materialization_smoke_v0.py",
    "test_covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0.py",
    "test_covapie_stage_global_rule_evaluation_orchestration_v1.py",
    "test_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1.py",
    "test_real_covalent_confirmed_candidate_sample_index_design_gate_v0.py",
)

_HISTORICAL_REFERENCE_PATHS = {
    "data/derived/covalent_small/b3_scaffold_only_mask_design_v0/b3_scaffold_only_mask_design_manifest.json",
    "data/derived/covalent_small/b3_scaffold_only_mask_design_v0/b3_scaffold_only_mask_design_report.csv",
    "data/derived/covalent_small/b3_scaffold_only_mask_design_v0/b3_scaffold_only_mask_protocol.json",
    "src/covalent_ext/b3_scaffold_only_mask_implementation.py",
    "scripts/check_diffsbdd_atomwise_loss_hook_prototype_v0.py",
    "scripts/check_diffsbdd_backward_smoke_v0.py",
    "scripts/check_diffsbdd_single_batch_forward_shape_smoke_v0.py",
    "tests/test_b3_scaffold_only_mask_sweep_v0.py",
}
_GATE_CONTROL_REFERENCE_PATHS = {
    "scripts/check_covalent_masking.py",
    "tests/test_covalent_inpaint_demo_mask_semantic_v1.py",
    "tests/test_covalent_masking.py",
}
_DESIGN_REFERENCE_PATHS = {
    "docs/covapie_target_residue_atom_condition_repository_cli_forwarding_design_v1_guide.md",
    "src/covalent_ext/b3_scaffold_only_mask_design.py",
    "src/covalent_ext/covapie_target_residue_atom_condition_repository_cli_forwarding_design_v1.py",
}
_DANGEROUS_REFERENCE_KINDS = frozenset(
    {
        "python_definition",
        "python_class_definition",
        "python_import",
        "python_name",
        "python_attribute",
        "python_call",
        "cli_add_argument",
        "exact_short_token_choice",
        "short_token_literal_type",
        "exact_short_subscript_key",
        "short_token_runtime_call",
    }
)
_REVIEWED_LEGACY_VALUES = frozenset(
    {*_LEGACY_SYMBOLS, _LEGACY_CLI, *_LEGACY_SHORT_TOKENS}
)
_HISTORICAL_ALLOWED_KINDS = frozenset(
    {
        "cli_add_argument",
        "controlled_text_exact_reference",
        "exact_legacy_cli_literal",
        "exact_short_token_comparison",
        "python_call",
        "python_import",
        "python_name",
        "structured_json_short_value",
    }
)
_NEGATIVE_ALLOWED_REFERENCES = frozenset(
    {
        ("160", "negative_short_token_collection", "B2"),
        ("160", "negative_short_token_collection", "B3"),
        ("160", "exact_legacy_string_literal", "mask_scaffold"),
    }
)
_DESIGN_ALLOWED_KINDS = frozenset(
    {
        "controlled_text_exact_reference",
        "controlled_text_short_alias_evidence",
        "exact_legacy_cli_literal",
        "exact_legacy_string_literal",
        "exact_short_dictionary_key",
        "exact_short_token_collection",
        "exact_short_token_comparison",
    }
)
_GATE_CONTROL_ALLOWED_KINDS = frozenset(
    {
        "exact_legacy_cli_literal",
        "exact_legacy_string_literal",
        "exact_short_token_collection",
        "exact_short_token_comparison",
        "negative_short_token_collection",
    }
)


def _build_reviewed_retained_path_policies() -> dict[str, dict[str, Any]]:
    """Build an exact-path allowlist; no directory prefix grants retention."""

    policies: dict[str, dict[str, Any]] = {}

    def register(
        path: str,
        *,
        allowed_kinds: frozenset[str],
        allowed_symbols: frozenset[str],
        classification: str,
        retained_reason: str,
    ) -> None:
        _canonical_relative_path(path)
        if path in policies or classification not in _CLASSIFICATIONS:
            raise ValueError(_ERROR)
        policies[path] = {
            "allowed_kinds": allowed_kinds,
            "allowed_symbols": allowed_symbols,
            "classification": classification,
            "retained_reason": retained_reason,
        }

    for path in sorted(_HISTORICAL_REFERENCE_PATHS):
        register(
            path,
            allowed_kinds=_HISTORICAL_ALLOWED_KINDS,
            allowed_symbols=_REVIEWED_LEGACY_VALUES,
            classification="historical_read_only",
            retained_reason="frozen_historical_mask_evidence",
        )
    register(
        _NEGATIVE_TEST_PATH,
        allowed_kinds=frozenset(
            kind for _location, kind, _symbol in _NEGATIVE_ALLOWED_REFERENCES
        ),
        allowed_symbols=frozenset(
            symbol for _location, _kind, symbol in _NEGATIVE_ALLOWED_REFERENCES
        ),
        classification="negative_rejection_evidence",
        retained_reason="legacy_token_is_explicitly_rejected",
    )
    for name in _REVIEWED_DESIGN_DOC_NAMES:
        path = f"docs/{name}"
        register(
            path,
            allowed_kinds=_DESIGN_ALLOWED_KINDS,
            allowed_symbols=_REVIEWED_LEGACY_VALUES,
            classification="design_or_documentation_evidence",
            retained_reason=(
                "reviewed_retirement_design_evidence"
                if path in _DESIGN_REFERENCE_PATHS
                else "reviewed_mask_alias_documentation_evidence"
            ),
        )
    for name in _REVIEWED_DESIGN_SOURCE_NAMES:
        path = f"src/covalent_ext/{name}"
        register(
            path,
            allowed_kinds=_DESIGN_ALLOWED_KINDS,
            allowed_symbols=_REVIEWED_LEGACY_VALUES,
            classification="design_or_documentation_evidence",
            retained_reason=(
                "reviewed_retirement_design_evidence"
                if path in _DESIGN_REFERENCE_PATHS
                else "canonical_short_alias_display_or_reporting_evidence"
            ),
        )
    for name in _REVIEWED_GATE_SCRIPT_NAMES:
        path = f"scripts/{name}"
        register(
            path,
            allowed_kinds=_GATE_CONTROL_ALLOWED_KINDS,
            allowed_symbols=_REVIEWED_LEGACY_VALUES,
            classification="gate_control_evidence",
            retained_reason=(
                "current_gate_asserts_legacy_surface_absence_or_rejection"
                if path in _GATE_CONTROL_REFERENCE_PATHS
                else "canonical_short_alias_display_or_reporting_assertion"
            ),
        )
    for name in _REVIEWED_GATE_TEST_NAMES:
        path = f"tests/{name}"
        register(
            path,
            allowed_kinds=_GATE_CONTROL_ALLOWED_KINDS,
            allowed_symbols=_REVIEWED_LEGACY_VALUES,
            classification="gate_control_evidence",
            retained_reason=(
                "current_gate_asserts_legacy_surface_absence_or_rejection"
                if path in _GATE_CONTROL_REFERENCE_PATHS
                else "canonical_short_alias_display_or_reporting_assertion"
            ),
        )
    return policies


_REVIEWED_RETAINED_PATH_POLICIES = _build_reviewed_retained_path_policies()
# The digest binds the complete ordered tuples
# (path, line_or_cell, token, kind, classification, retained_reason).  This is
# an exact retained-set freeze: additions, removals, line/context changes, or
# reclassification all change the digest and fail closed.
_EXPECTED_RETAINED_RECORD_COUNT = 758
_EXPECTED_RETAINED_RECORDS_SHA256 = (
    "1ec8b3efe196ecb35b818c727abef049224f8cd64670288c65ff5a3974e5610a"
)


def _classify_raw_reference(
    raw: tuple[str, str, str, str],
    *,
    negative_context_valid: bool,
) -> tuple[str, str] | None:
    """Classify one raw record; ``None`` means unresolved and fails closed."""

    path, location, symbol, kind = raw
    policy = _REVIEWED_RETAINED_PATH_POLICIES.get(path)
    if policy is not None:
        reference_allowed = (
            kind in policy["allowed_kinds"]
            and symbol in policy["allowed_symbols"]
        )
        if path == _NEGATIVE_TEST_PATH:
            reference_allowed = (
                reference_allowed
                and negative_context_valid
                and (location, kind, symbol) in _NEGATIVE_ALLOWED_REFERENCES
            )
        if reference_allowed:
            return policy["classification"], policy["retained_reason"]

    if kind in _DANGEROUS_REFERENCE_KINDS:
        if path.startswith("tests/"):
            return "current_positive_test", "positive_legacy_test_blocker"
        return "active_runtime", "active_legacy_runtime_blocker"
    return None


def _negative_rejection_context_evidence(repo_root: Path) -> bool:
    """Prove the three reviewed negative records occur in a rejection loop."""

    payload = _git_snapshot_blob_bytes(
        repo_root,
        commit=_R2_COMMIT,
        relative_path=_NEGATIVE_TEST_PATH,
        expected_sha256=_NEGATIVE_TEST_SHA256,
    )
    try:
        source = payload.decode("utf-8", errors="strict")
        tree = ast.parse(source, filename=_NEGATIVE_TEST_PATH)
    except (UnicodeDecodeError, SyntaxError) as error:
        raise ValueError(_ERROR) from error
    candidates = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.For, ast.AsyncFor))
        and isinstance(node.target, ast.Name)
        and node.target.id == "unsupported"
        and [value for value, _line in _literal_strings(node.iter)]
        == ["B3", "B2", "mask_scaffold", "legacy_short_B2"]
    ]
    if len(candidates) != 1:
        raise ValueError(_ERROR)
    candidate = candidates[0]
    calls = {
        _attribute_chain(node.func)
        for node in ast.walk(candidate)
        if isinstance(node, ast.Call)
    }
    handlers = [
        handler
        for node in ast.walk(candidate)
        if isinstance(node, ast.Try)
        for handler in node.handlers
    ]
    handler_types = {
        handler.type.id
        for handler in handlers
        if isinstance(handler.type, ast.Name)
    }
    context = ast.get_source_segment(source, candidate)
    context_valid = (
        type(context) is str
        and candidate.lineno == 160
        and candidate.end_lineno is not None
        and candidate.end_lineno >= candidate.lineno
        and "expected_reactive_atom_region_for_mask_level_v0" in calls
        and "ValueError" in handler_types
        and "unsupported_mask_level:" in context
        and "unexpectedly accepted" in context
    )
    if not context_valid:
        raise ValueError(_ERROR)
    return True


def _record(
    raw: tuple[str, str, str, str], classification: str, retained_reason: str
) -> dict[str, Any]:
    path, line_or_cell, symbol, kind = raw
    negative = classification == "negative_rejection_evidence"
    active = classification in {"active_runtime", "current_positive_test"}
    return {
        "path": path,
        "line_or_cell": line_or_cell,
        "symbol_or_token": symbol,
        "reference_kind": kind,
        "classification": classification,
        "active_runtime": active,
        "runtime_importable": False,
        "runtime_callable": False,
        "schema_admissible": False,
        "training_admissible": False,
        "automatic_translation_allowed": False,
        "positive_legacy_behavior_required": classification == "current_positive_test",
        "retained_reason": retained_reason,
    }


def _scan_legacy_references(
    repo_root: Path, repository_paths: Sequence[str], *, enforce_expected: bool = True
) -> dict[str, Any]:
    negative_context_valid = _negative_rejection_context_evidence(repo_root)
    raw_records: set[tuple[str, str, str, str]] = set()
    python_count = 0
    notebook_count = 0
    notebook_code_count = 0
    notebook_code_hits = 0
    parse_errors = 0
    text_suffixes = {".md", ".json", ".csv", ".txt", ".toml", ".yaml", ".yml"}
    scan_paths = [
        relative_path for relative_path in repository_paths
        if PurePosixPath(relative_path).suffix.lower()
        in ({".py", ".ipynb"} | text_suffixes)
    ]
    payloads = _git_snapshot_blob_batch(
        repo_root, commit=_R2_COMMIT, relative_paths=scan_paths
    )
    for relative_path in scan_paths:
        suffix = PurePosixPath(relative_path).suffix.lower()
        payload = payloads[relative_path]
        if suffix == ".py":
            python_count += 1
            try:
                tree = ast.parse(payload.decode("utf-8", errors="strict"), filename=relative_path)
            except (UnicodeDecodeError, SyntaxError):
                parse_errors += 1
                continue
            raw_records.update(_raw_python_records(tree, relative_path))
        elif suffix == ".ipynb":
            notebook_count += 1
            try:
                notebook = json.loads(payload)
                cells = notebook["cells"]
                if type(notebook) is not dict or type(cells) is not list:
                    raise ValueError(_ERROR)
            except Exception as error:
                if type(error) is ValueError and str(error) == _ERROR:
                    raise
                raise ValueError(_ERROR) from error
            for cell_index, cell in enumerate(cells):
                if type(cell) is not dict:
                    raise ValueError(_ERROR)
                source_value = cell.get("source", [])
                if type(source_value) is list and all(type(item) is str for item in source_value):
                    source = "".join(source_value)
                elif type(source_value) is str:
                    source = source_value
                else:
                    raise ValueError(_ERROR)
                if cell.get("cell_type") == "code":
                    notebook_code_count += 1
                    try:
                        tree = ast.parse(
                            _sanitize_notebook_code(source),
                            filename=f"{relative_path}:cell[{cell_index}]",
                        )
                    except SyntaxError:
                        parse_errors += 1
                        continue
                    cell_records = _raw_python_records(tree, relative_path)
                    adjusted = {
                        (path, f"cell[{cell_index}]:{line}", symbol, kind)
                        for path, line, symbol, kind in cell_records
                    }
                    notebook_code_hits += len(adjusted)
                    raw_records.update(adjusted)
                else:
                    for path, line, symbol, kind in _controlled_text_records(source, relative_path):
                        raw_records.add((path, f"cell[{cell_index}]:{line}", symbol, kind))
        else:
            try:
                text = payload.decode("utf-8", errors="strict")
            except UnicodeDecodeError:
                continue
            raw_records.update(_controlled_text_records(text, relative_path))
            raw_records.update(_structured_short_token_records(payload, relative_path))
    if parse_errors:
        raise ValueError(_ERROR)

    retained: list[dict[str, Any]] = []
    active: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    classified_tuples: list[tuple[str, str, str, str, str, str]] = []
    for raw in sorted(raw_records):
        classification_result = _classify_raw_reference(
            raw, negative_context_valid=negative_context_valid
        )
        if classification_result is None:
            unresolved_classification = (
                "current_positive_test"
                if raw[0].startswith("tests/")
                else "active_runtime"
            )
            unresolved.append(
                _record(raw, unresolved_classification, "unreviewed_reference")
            )
            continue
        classification, reason = classification_result
        classified_tuples.append((*raw, classification, reason))
        item = _record(raw, classification, reason)
        if item["active_runtime"]:
            active.append(item)
        else:
            retained.append(item)
    inventory_sha256 = _sha256(_canonical_json_bytes(classified_tuples))
    if enforce_expected and (
        unresolved
        or len(retained) != _EXPECTED_RETAINED_RECORD_COUNT
        or inventory_sha256 != _EXPECTED_RETAINED_RECORDS_SHA256
    ):
        raise ValueError(_ERROR)
    counts = {classification: 0 for classification in _CLASSIFICATIONS}
    for item in (*active, *retained):
        counts[item["classification"]] += 1
    return {
        "python_count": python_count,
        "notebook_count": notebook_count,
        "notebook_code_count": notebook_code_count,
        "notebook_code_hits": notebook_code_hits,
        "parse_errors": parse_errors,
        "raw_records": sorted(raw_records),
        "classified_tuples": classified_tuples,
        "inventory_sha256": inventory_sha256,
        "active": active,
        "unresolved": unresolved,
        "retained": retained,
        "counts": counts,
    }


def _top_level_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(target.id for target in node.targets if isinstance(target, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def _annotation_text(node: ast.AST | None) -> str:
    return ast.unparse(node) if node is not None else ""


def _structured_schema_evidence(repo_root: Path) -> dict[str, bool]:
    payload = _git_snapshot_blob_bytes(
        repo_root,
        commit=_R2_COMMIT,
        relative_path="src/covalent_ext/schema.py",
        expected_sha256=_R2_FILES["src/covalent_ext/schema.py"],
    )
    tree = ast.parse(payload.decode("utf-8"))
    names = _top_level_names(tree)
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}

    def field_annotation(class_name: str, field: str) -> str | None:
        node = classes.get(class_name)
        if node is None:
            return None
        matches = [
            child for child in node.body
            if isinstance(child, ast.AnnAssign)
            and isinstance(child.target, ast.Name)
            and child.target.id == field
        ]
        return _annotation_text(matches[0].annotation) if len(matches) == 1 else None

    evidence = {
        "MaskType_absent": "MaskType" not in names,
        "CanonicalMaskSemantic_present": "CanonicalMaskSemantic" in names,
        "CovalentSample_mask_semantic_present": field_annotation("CovalentSample", "mask_semantic") == "CanonicalMaskSemantic",
        "CovalentSample_mask_type_absent": field_annotation("CovalentSample", "mask_type") is None,
        "MaskResult_mask_type_long_form": field_annotation("MaskResult", "mask_type") == "LongFormMaskLevel",
    }
    if not all(evidence.values()):
        raise ValueError(_ERROR)
    return evidence


def _import_fails(module_name: str, symbol: str) -> bool:
    try:
        module = importlib.import_module(module_name)
        getattr(module, symbol)
    except (ImportError, AttributeError):
        return True
    return False


def _negative_and_canonical_runtime_evidence(repo_root: Path) -> tuple[dict[str, bool], dict[str, Any]]:
    _bind_live_canonical_core(repo_root)
    masking = importlib.import_module("covalent_ext.masking")
    schema = importlib.import_module("covalent_ext.schema")
    dataset_module = importlib.import_module("covalent_ext.dataset")
    import_failures = {
        "MaskType": _import_fails("covalent_ext.schema", "MaskType"),
        "build_four_level_mask": _import_fails("covalent_ext.masking", "build_four_level_mask"),
        "MASK_BUILDERS": _import_fails("covalent_ext.masking", "MASK_BUILDERS"),
        "mask_scaffold": _import_fails("covalent_ext.masking", "mask_scaffold"),
    }
    if not all(import_failures.values()):
        raise ValueError(_ERROR)

    common = {
        "scaffold_atoms": [0, 1, 2],
        "linker_atoms": [3, 4],
        "warhead_atoms": [5, 6],
        "num_ligand_atoms": 7,
    }
    short_rejected: dict[str, bool] = {}
    for token in _LEGACY_SHORT_TOKENS:
        try:
            masking.build_canonical_mask(mask_semantic=token, **common)
        except ValueError as error:
            short_rejected[token] = str(error) == "COVAPIE_CANONICAL_MASK_SEMANTIC_INVALID"
        else:
            short_rejected[token] = False
    dataset = dataset_module.CovalentJsonlDataset.__new__(dataset_module.CovalentJsonlDataset)
    sample = {
        "pre_reaction_ligand_graph": {"atom_symbols": ["C"] * 7},
        "scaffold_atoms": [0, 1, 2],
        "linker_atoms": [3, 4],
        "warhead_atoms": [5, 6],
    }
    dataset_short_rejected: dict[str, bool] = {}
    for token in _LEGACY_SHORT_TOKENS:
        try:
            dataset.build_mask(sample, token)
        except ValueError as error:
            dataset_short_rejected[token] = str(error) == "COVAPIE_CANONICAL_MASK_SEMANTIC_INVALID"
        else:
            dataset_short_rejected[token] = False

    demo_payload = _git_snapshot_blob_bytes(
        repo_root, commit=_R2_COMMIT, relative_path="scripts/covalent_inpaint_demo.py"
    )
    demo_tree = ast.parse(demo_payload.decode("utf-8"))
    legacy_cli_present = any(
        isinstance(node, ast.Call)
        and _attribute_chain(node.func) is not None
        and _attribute_chain(node.func).endswith("add_argument")
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == _LEGACY_CLI
        for node in ast.walk(demo_tree)
    )
    negative = {
        "legacy_builder_importable": not import_failures["build_four_level_mask"],
        "legacy_builder_callable": callable(getattr(masking, "build_four_level_mask", None)),
        "legacy_registry_present": hasattr(masking, "MASK_BUILDERS"),
        "legacy_schema_type_present": hasattr(schema, "MaskType"),
        "legacy_cli_flag_present": legacy_cli_present,
        "legacy_short_token_runtime_input_supported": not all(short_rejected.values()),
        "legacy_dataset_short_key_supported": not all(dataset_short_rejected.values()),
    }
    if any(negative.values()):
        raise ValueError(_ERROR)

    results: dict[str, Any] = {}
    for semantic in _CANONICAL_SEMANTICS:
        result = masking.build_canonical_mask(mask_semantic=semantic, **common)
        results[semantic] = {
            "mask_type": result.mask_type,
            "visible_atoms": list(result.visible_atoms),
            "masked_atoms": list(result.masked_atoms),
            "lig_fixed": result.lig_fixed.tolist(),
        }
    all_masks = dataset.build_all_masks(sample)
    canonical = {
        "semantic_names_exact": tuple(masking.CANONICAL_MASK_SEMANTICS) == _CANONICAL_SEMANTICS,
        "levels_exact": tuple(masking.CANONICAL_MASK_SEMANTIC_TO_LEVEL.values()) == _CANONICAL_LEVELS,
        "toy_results": results,
        "dataset_mask_names": list(all_masks),
        "dataset_exact_five": tuple(all_masks) == _CANONICAL_SEMANTICS,
        "B2_B3_distinct": (
            results["scaffold_plus_warhead"]["visible_atoms"] != results["scaffold_only"]["visible_atoms"]
            and results["scaffold_plus_warhead"]["masked_atoms"] != results["scaffold_only"]["masked_atoms"]
        ),
    }
    expected_toy = {
        "warhead_only": ("A_warhead_only", [0, 1, 2, 3, 4], [5, 6], [1, 1, 1, 1, 1, 0, 0]),
        "linker_plus_warhead": ("B_linker_warhead", [0, 1, 2], [3, 4, 5, 6], [1, 1, 1, 0, 0, 0, 0]),
        "scaffold_plus_warhead": ("B2_scaffold_warhead", [3, 4], [0, 1, 2, 5, 6], [0, 0, 0, 1, 1, 0, 0]),
        "scaffold_only": ("B3_scaffold_only", [3, 4, 5, 6], [0, 1, 2], [0, 0, 0, 1, 1, 1, 1]),
        "scaffold_plus_linker_plus_warhead": ("C_scaffold_linker_warhead", [], [0, 1, 2, 3, 4, 5, 6], [0, 0, 0, 0, 0, 0, 0]),
    }
    canonical["toy_exact"] = all(
        (
            results[name]["mask_type"],
            results[name]["visible_atoms"],
            results[name]["masked_atoms"],
            results[name]["lig_fixed"],
        ) == expected
        for name, expected in expected_toy.items()
    )
    if not all(
        canonical[key] is True
        for key in ("semantic_names_exact", "levels_exact", "dataset_exact_five", "B2_B3_distinct", "toy_exact")
    ):
        raise ValueError(_ERROR)
    return negative, canonical


def _canonical_consumer_evidence(repo_root: Path) -> None:
    for relative_path in _DATASET_CONSUMERS:
        payload = _git_snapshot_blob_bytes(
            repo_root,
            commit=_R2_COMMIT,
            relative_path=relative_path,
            expected_sha256=_R2_FILES[relative_path],
        )
        tree = ast.parse(payload.decode("utf-8"))
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        if not {"CANONICAL_MASK_SEMANTICS", "CANONICAL_MASK_SEMANTIC_TO_LEVEL"}.issubset(names):
            raise ValueError(_ERROR)
        if any(
            isinstance(node, ast.Subscript)
            and isinstance(node.slice, ast.Constant)
            and node.slice.value in _LEGACY_SHORT_TOKENS
            for node in ast.walk(tree)
        ):
            raise ValueError(_ERROR)


def _historical_and_negative_evidence(repo_root: Path) -> None:
    for relative_path, expected_sha256 in {
        **_HISTORICAL_B3_FILES,
        _NEGATIVE_TEST_PATH: _NEGATIVE_TEST_SHA256,
    }.items():
        _git_snapshot_blob_bytes(
            repo_root,
            commit=_R2_COMMIT,
            relative_path=relative_path,
            expected_sha256=expected_sha256,
        )
    forbidden_module = "covalent_ext.b3_scaffold_only_mask_implementation"
    active_paths = (
        "src/covalent_ext/__init__.py",
        "src/covalent_ext/masking.py",
        "src/covalent_ext/schema.py",
        "src/covalent_ext/dataset.py",
        "scripts/covalent_inpaint_demo.py",
        "scripts/check_covalent_masking.py",
    )
    test_paths = [
        path for path in _git_text(repo_root, ["ls-tree", "-r", "--name-only", _R2_COMMIT]).splitlines()
        if path.startswith("tests/") and path.endswith(".py") and path != "tests/test_b3_scaffold_only_mask_implementation_v0.py"
    ]
    import_audit_paths = list((*active_paths, *test_paths))
    import_payloads = _git_snapshot_blob_batch(
        repo_root, commit=_R2_COMMIT, relative_paths=import_audit_paths
    )
    for relative_path in import_audit_paths:
        payload = import_payloads[relative_path]
        tree = ast.parse(payload.decode("utf-8"))
        imports = {
            node.module for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        imports.update(
            alias.name for node in ast.walk(tree)
            if isinstance(node, ast.Import) for alias in node.names
        )
        if forbidden_module in imports or "check_b3_scaffold_only_mask_implementation_v0" in imports:
            raise ValueError(_ERROR)
    negative_tree = ast.parse(
        _git_snapshot_blob_bytes(
            repo_root,
            commit=_R2_COMMIT,
            relative_path=_NEGATIVE_TEST_PATH,
            expected_sha256=_NEGATIVE_TEST_SHA256,
        ).decode("utf-8")
    )
    constants = {
        node.value for node in ast.walk(negative_tree)
        if isinstance(node, ast.Constant) and type(node.value) is str
    }
    if (
        not {"B2", "B3", "mask_scaffold"}.issubset(constants)
        or not any(value.startswith("unsupported_mask_level:") for value in constants)
    ):
        raise ValueError(_ERROR)


def _lifecycle_from_facts(facts: Mapping[str, Any]) -> dict[str, Any]:
    try:
        head = facts["head"]
        origin = facts["origin_main"]
        raw_untracked = facts["ordinary_untracked_paths"]
        raw_tracked_gate = facts["tracked_gate_paths"]
        raw_tracked_changes = facts["tracked_changes"]
        raw_staged_changes = facts["staged_changes"]
        regular_gate_paths = facts["regular_gate_paths"] is True
        candidates = facts["r3_candidates"]
        string_lists = (
            raw_untracked,
            raw_tracked_gate,
            raw_tracked_changes,
            raw_staged_changes,
        )
        if (
            type(head) is not str
            or re.fullmatch(r"[0-9a-f]{40}", head) is None
            or type(origin) is not str
            or re.fullmatch(r"[0-9a-f]{40}", origin) is None
            or any(
                type(items) is not list
                or any(type(item) is not str for item in items)
                or len(items) != len(set(items))
                for items in string_lists
            )
            or type(candidates) is not list
            or any(type(item) is not dict for item in candidates)
        ):
            raise ValueError(_ERROR)
        untracked = set(raw_untracked)
        tracked_gate = set(raw_tracked_gate)
        tracked_changes = set(raw_tracked_changes)
        staged_changes = set(raw_staged_changes)
        r3_paths = set(_R3_PATHS)
        precommit = (
            head == _R2_COMMIT
            and origin == _R2_COMMIT
            and not tracked_gate
            and untracked == r3_paths
            and not tracked_changes
            and not staged_changes
            and regular_gate_paths
            and not candidates
        )
        valid_candidates = [
            item for item in candidates
            if type(item.get("commit")) is str
            and re.fullmatch(r"[0-9a-f]{40}", item["commit"]) is not None
            and item.get("subject") == _R3_SUBJECT
            and item.get("parents") == [_R2_COMMIT]
            and type(item.get("paths")) is list
            and all(type(path) is str for path in item["paths"])
            and set(item["paths"]) == r3_paths
            and len(item.get("paths", [])) == len(_R3_PATHS)
            and item.get("head_ancestor") is True
            and item.get("body_empty") is True
            and item.get("gate_commit_modes_bound") is True
            and item.get("gate_commit_blobs_bound") is True
            and item.get("gate_live_bytes_match_commit") is True
        ]
        committed = (
            tracked_gate == r3_paths
            and regular_gate_paths
            and not (untracked & r3_paths)
            and not (tracked_changes & r3_paths)
            and not (staged_changes & r3_paths)
            and len(candidates) == 1
            and len(valid_candidates) == 1
        )
        if precommit:
            return {
                "profile": "r3_precommit_candidate",
                "commit": None,
                "committed": False,
                "published": False,
            }
        if committed:
            item = valid_candidates[0]
            published = item.get("origin_main_ancestor") is True
            if not published and (untracked or tracked_changes or staged_changes):
                raise ValueError(_ERROR)
            return {
                "profile": "r3_published_successor" if published else "r3_committed_unpushed",
                "commit": item["commit"],
                "committed": True,
                "published": published,
            }
        raise ValueError(_ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _r3_lifecycle_evidence(repo_root: Path) -> dict[str, Any]:
    head = _git_text(repo_root, ["rev-parse", "HEAD"]).strip()
    origin = _git_text(repo_root, ["rev-parse", "origin/main"]).strip()
    tracked = set(_git_text(repo_root, ["ls-files"]).splitlines())
    untracked = _git_text(
        repo_root, ["ls-files", "--others", "--exclude-standard"]
    ).splitlines()
    tracked_changes = _git_text(repo_root, ["diff", "--name-only"]).splitlines()
    staged_changes = _git_text(repo_root, ["diff", "--cached", "--name-only"]).splitlines()
    live_payloads: dict[str, bytes] = {}
    regular = True
    for relative_path in _R3_PATHS:
        try:
            live_payloads[relative_path] = _read_live_regular_file(
                repo_root, relative_path
            )
        except ValueError:
            regular = False
            break
    candidate_commits: list[dict[str, Any]] = []
    if head != _R2_COMMIT and _is_ancestor(repo_root, _R2_COMMIT, head):
        commits = _git_text(
            repo_root, ["rev-list", "--ancestry-path", f"{_R2_COMMIT}..{head}"]
        ).splitlines()
        for commit in commits:
            metadata = _git_text(
                repo_root, ["show", "-s", "--format=%H%x00%P%x00%s%x00%b", commit]
            ).rstrip("\n").split("\x00")
            if len(metadata) != 4:
                continue
            commit_hash, parent_text, subject, body = metadata
            if subject != _R3_SUBJECT:
                continue
            parents = parent_text.split()
            paths = _git_text(
                repo_root, ["diff-tree", "--no-commit-id", "--name-only", "-r", commit]
            ).splitlines()
            modes_bound = True
            blobs_bound = True
            live_bytes_match = regular
            for relative_path in _R3_PATHS:
                row = _git_text(repo_root, ["ls-tree", commit, "--", relative_path])
                match = re.fullmatch(
                    rf"100644 blob ([0-9a-f]{{40}})\t{re.escape(relative_path)}\n",
                    row,
                )
                if match is None:
                    modes_bound = False
                    blobs_bound = False
                    live_bytes_match = False
                    continue
                try:
                    commit_payload = _git_snapshot_blob_bytes(
                        repo_root, commit=commit, relative_path=relative_path
                    )
                except ValueError:
                    blobs_bound = False
                    live_bytes_match = False
                    continue
                if live_payloads.get(relative_path) != commit_payload:
                    live_bytes_match = False
            candidate_commits.append(
                {
                    "commit": commit_hash,
                    "subject": subject,
                    "parents": parents,
                    "paths": paths,
                    "head_ancestor": _is_ancestor(repo_root, commit, "HEAD"),
                    "origin_main_ancestor": _is_ancestor(repo_root, commit, "origin/main"),
                    "body_empty": body == "",
                    "gate_commit_modes_bound": modes_bound,
                    "gate_commit_blobs_bound": blobs_bound,
                    "gate_live_bytes_match_commit": live_bytes_match,
                }
            )
    return _lifecycle_from_facts(
        {
            "head": head,
            "origin_main": origin,
            "ordinary_untracked_paths": untracked,
            "tracked_gate_paths": sorted(tracked & set(_R3_PATHS)),
            "tracked_changes": tracked_changes,
            "staged_changes": staged_changes,
            "regular_gate_paths": regular,
            "r3_candidates": candidate_commits,
        }
    )


def _validate_response(response: Mapping[str, Any], *, require_order: bool = True) -> bool:
    try:
        if (
            type(response) is not dict
            or len(response) != 47
            or set(response) != set(LEGACY_FOUR_LEVEL_MASK_RETIREMENT_GATE_RESPONSE_FIELDS)
            or (require_order and tuple(response) != LEGACY_FOUR_LEVEL_MASK_RETIREMENT_GATE_RESPONSE_FIELDS)
        ):
            raise ValueError(_ERROR)
        unsigned = {
            field: response[field]
            for field in LEGACY_FOUR_LEVEL_MASK_RETIREMENT_GATE_RESPONSE_FIELDS
            if field != "legacy_four_level_mask_retirement_gate_response_sha256"
        }
        if response["legacy_four_level_mask_retirement_gate_response_sha256"] != _sha256(_canonical_json_bytes(unsigned)):
            raise ValueError(_ERROR)
        _canonical_json_bytes(response)
        return True
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def evaluate_covapie_legacy_four_level_mask_retirement_gate_v1(
    *,
    repo_root: Path,
) -> dict[str, Any]:
    """Evaluate immutable R2 retirement evidence and the R3 lifecycle."""

    try:
        if (
            type(repo_root) is not type(Path())
            or not repo_root.is_dir()
            or repo_root.is_symlink()
        ):
            raise ValueError(_ERROR)
        scope, repository_paths = _r2_source_evidence(repo_root)
        scan = _scan_legacy_references(repo_root, repository_paths)
        _structured_schema_evidence(repo_root)
        negative, canonical = _negative_and_canonical_runtime_evidence(repo_root)
        _canonical_consumer_evidence(repo_root)
        _historical_and_negative_evidence(repo_root)
        lifecycle = _r3_lifecycle_evidence(repo_root)

        evidence_passed = (
            not scan["active"]
            and not scan["unresolved"]
            and scan["notebook_code_hits"] == 0
            and not any(negative.values())
            and canonical["toy_exact"] is True
            and canonical["dataset_exact_five"] is True
            and canonical["B2_B3_distinct"] is True
        )
        if not evidence_passed:
            raise ValueError(_ERROR)
        committed = lifecycle["committed"]
        published = lifecycle["published"]
        recommended = (
            "commit_and_push_covapie_legacy_four_level_mask_retirement_gate_v1"
            if not committed
            else (
                "push_covapie_legacy_four_level_mask_retirement_gate_v1"
                if not published
                else "begin_repository_cli_forwarding_C1"
            )
        )
        response: dict[str, Any] = {
            "legacy_four_level_mask_retirement_gate_version": _VERSION,
            "source_R2_commit": _R2_COMMIT,
            "source_R2_parent": _R2_PARENT,
            "source_R2_tree": _R2_TREE,
            "source_R2_subject": _R2_SUBJECT,
            "source_R2_scope": scope,
            "source_R2_file_sha256s": dict(_R2_FILES),
            "scan_subject_commit": _R2_COMMIT,
            "scan_evidence_mode": "frozen_R2_commit_snapshot",
            "scan_methods": list(_SCAN_METHODS),
            "scanned_tracked_path_count": len(repository_paths),
            "scanned_python_path_count": scan["python_count"],
            "scanned_notebook_path_count": scan["notebook_count"],
            "scanned_notebook_code_cell_count": scan["notebook_code_count"],
            "python_parse_error_count": scan["parse_errors"],
            "active_legacy_reference_records": scan["active"],
            "active_legacy_reference_count": len(scan["active"]),
            "unresolved_legacy_reference_records": scan["unresolved"],
            "unresolved_legacy_reference_count": len(scan["unresolved"]),
            "retained_read_only_reference_records": scan["retained"],
            "retained_read_only_reference_count": len(scan["retained"]),
            "reference_classification_counts": scan["counts"],
            "required_negative_runtime_evidence": negative,
            "historical_read_only_legacy_evidence_retained": True,
            "negative_legacy_token_rejection_evidence_retained": True,
            "legacy_core_provider_removed": True,
            "legacy_schema_type_removed": True,
            "legacy_cli_flag_removed": True,
            "canonical_mask_semantic_names": list(_CANONICAL_SEMANTICS),
            "canonical_mask_count": len(_CANONICAL_SEMANTICS),
            "canonical_B2_semantic": "scaffold_plus_warhead",
            "canonical_B3_semantic": "scaffold_only",
            "sixth_mask_added": False,
            "canonical_five_level_runtime_complete": True,
            "retirement_evidence_passed": evidence_passed,
            "R3_gate_implemented": True,
            "R3_gate_lifecycle_profile": lifecycle["profile"],
            "R3_gate_commit": lifecycle["commit"],
            "R3_gate_committed": committed,
            "R3_gate_published": published,
            "ready_for_R3_commit_review": evidence_passed and not committed,
            "legacy_four_level_full_runtime_retired": evidence_passed and committed,
            "ready_for_repository_cli_forwarding_C1": evidence_passed and published,
            "recommended_next_step": recommended,
            "training_or_parameter_update": False,
            "feature_semantics_audit_required_before_training": True,
        }
        response["legacy_four_level_mask_retirement_gate_response_sha256"] = _sha256(
            _canonical_json_bytes(response)
        )
        _validate_response(response)
        return response
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
