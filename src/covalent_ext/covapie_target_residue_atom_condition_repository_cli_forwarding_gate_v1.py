"""Formal C4 gate for repository target-residue CLI forwarding V1.

The evaluator binds the published R3/C1/C2/C3 commits, calls the existing R3
retirement evaluator, validates the central C1 parser/resolver contract, and
audits the two selected live callers with Python ASTs.  It performs read-only
Git object queries and lightweight parser/resolver calls only.  It never loads
a checkpoint, executes a caller, runs a model forward, writes output, trains,
or implements reward/RL behavior.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
import json
import os
import re
import stat
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence


__all__ = (
    "evaluate_covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1",
)


_ERROR = (
    "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_REPOSITORY_CLI_FORWARDING_GATE_INVALID"
)
_C1_ERROR = "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_REPOSITORY_CLI_INVALID"
_VERSION = (
    "covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1"
)
_MAX_SOURCE_BYTES = 8 * 1024 * 1024

_R3_COMMIT = "5974ded1dc1aa02a365a23e4a409b9a7fe98a4be"
_R3_PARENT = "8711c1899759ca4c1f4a24f7ff9782b81a257245"
_R3_SUBJECT = "add CovaPIE legacy four-level mask retirement gate v1"
_R3_RESPONSE_SHA256 = (
    "f548c9ede072f12a1608d79767e709604c195a751ca65fb7a8c23638d14c2686"
)
_R3_FILES = {
    "docs/covapie_legacy_four_level_mask_retirement_gate_v1_guide.md": (
        "f7ede7980ddd7c94cf383886710bad3cac9850b7e392ec7ff7ac00f3d02ac9ff"
    ),
    "scripts/check_covapie_legacy_four_level_mask_retirement_gate_v1.py": (
        "a1aedd543b87520617ddbfee4b0fe893e371b5f9b6f3aaae27ec5b967517a339"
    ),
    "src/covalent_ext/covapie_legacy_four_level_mask_retirement_gate_v1.py": (
        "fbe0188c26c0f510f8aa21b8a3bbb21cccff1dc050c844f3f45d544d8fb31c7d"
    ),
    "tests/test_covapie_legacy_four_level_mask_retirement_gate_v1.py": (
        "113a1aa7ff87f6a3b8a0e6de148dc12cca576b81beaae841f55155653e72b072"
    ),
}

_C1_COMMIT = "142e7f72b391ceed3bbecaf22846a08f56933ea5"
_C1_PARENT = _R3_COMMIT
_C1_SUBJECT = (
    "add CovaPIE target residue atom condition repository CLI helper C1 v1"
)
_C1_FILES = {
    "src/covalent_ext/covapie_target_residue_atom_condition_repository_cli_v1.py": (
        "ff02657edd67d643bed4881b3c52df75cb950dffc45c19e5497b07dd65a52dfc"
    ),
    "tests/test_covapie_target_residue_atom_condition_repository_cli_v1.py": (
        "20f272fd9d28020ee5e94457d6913bee2d44c78300c8af6a6b9b11ae0001805e"
    ),
}
_C1_APIS = (
    "add_covapie_target_residue_atom_condition_cli_arguments_v1",
    "resolve_covapie_target_residue_atom_condition_cli_args_v1",
    "load_covapie_target_residue_conditioned_model_from_checkpoint_v1",
)
_TARGET_OPTIONS = (
    "--target_residue_atom_conditioning",
    "--target_chain_id",
    "--target_residue_sequence_number",
)
_EXACT6_FIELDS = (
    "chain_id",
    "residue_sequence_number",
    "residue_insertion_code",
    "residue_name",
    "atom_name",
    "element",
)

_C2_COMMIT = "7cdaf807241e3dc4331d5c0a05eb6a63dd4d5ec4"
_C2_PARENT = _C1_COMMIT
_C2_SUBJECT = (
    "forward CovaPIE target residue selector through generate_ligands C2 v1"
)
_C2_PATH = "generate_ligands.py"
_C2_SHA256 = "0739a7c194ab7794227a57fa28e7f7aea93b2013750e1ce1b1cde5d37b45d9c0"
_C2_BLOB = "418a4efa20d76d415b9f3fbc07a5654593df47e8"

_C3_COMMIT = "bd36211b03792602f382c16badac61eed79c8f9c"
_C3_PARENT = _C2_COMMIT
_C3_SUBJECT = (
    "forward CovaPIE target residue selector through covalent demo C3 v1"
)
_C3_PATH = "scripts/covalent_inpaint_demo.py"
_C3_SHA256 = "4df839da22e77ada99ab05e6d3e7e5ed41bd480618f0cb01163b5ca52f58c5b9"
_C3_BLOB = "96c38442b0fbca37ccfa9bdda5d0831cc7f8f2c9"

_MODEL_GATE_COMMIT = "dd085332c7e2cf58a6ca2e7d71cf022da010d4b4"
_MODEL_GATE_PARENT = "2c504ff2eac0864c146129f4011d902fae5bef69"
_MODEL_GATE_SUBJECT = (
    "add CovaPIE target residue atom condition model consumption gate v1"
)
_MODEL_GATE_FILES = {
    "docs/covapie_target_residue_atom_condition_model_consumption_gate_v1_guide.md": (
        "45752804e529aea4724526b75631c75a57a85f7130239cb35057fe5f6559a6a2"
    ),
    "scripts/check_covapie_target_residue_atom_condition_model_consumption_gate_v1.py": (
        "72730cdf3e6cf2f2fc8ca22f0ad470f0744651153c539f95ce7a262ff32141ee"
    ),
    "src/covalent_ext/covapie_target_residue_atom_condition_model_consumption_gate_v1.py": (
        "473da8ae62fef8eb8669edd8c553509926008767efea2dede60163146f539ee7"
    ),
    "tests/test_covapie_target_residue_atom_condition_model_consumption_gate_v1.py": (
        "22323c59d74f3b58cc7f8235b910b9f0aca616734af35eed895633b9c5f188df"
    ),
}
_MODEL_GATE_BUNDLE_RELATIVE = (
    "covapie-state/manual-review/"
    "covapie_current11_target_residue_atom_condition_model_consumption_gate_bundle_v1.json"
)
_MODEL_GATE_BUNDLE_SIZE = 6449
_MODEL_GATE_BUNDLE_SHA256 = (
    "18edfbc312128315fd9c880e750aeccc41132b34c20c8e34d78a974e39a2c9aa"
)
_MODEL_GATE_INTERNAL_SHA256 = (
    "0ef97cdafe946fefd240c95a94efc8b12be977c899db3b1df4a56a580b53d842"
)

_C4_PATHS = (
    "src/covalent_ext/covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1.py",
    "tests/test_covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1.py",
    "scripts/check_covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1.py",
    "docs/covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1_guide.md",
)
_C4_SUBJECT = (
    "add CovaPIE target residue repository CLI forwarding gate C4 v1"
)

_SUPPORTED_CALLERS = (
    "generate_ligands.py",
    "scripts/covalent_inpaint_demo.py",
)
_CANONICAL_MASK_SEMANTICS = (
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
)

REPOSITORY_CLI_FORWARDING_GATE_RESPONSE_FIELDS = (
    "repository_cli_forwarding_gate_version",
    "repository_cli_forwarding_gate_error_contract",
    "source_R3_commit_identity",
    "source_R3_file_identities",
    "R3_gate_lifecycle_profile",
    "R3_gate_commit",
    "R3_gate_committed",
    "R3_gate_published",
    "R3_response_sha256",
    "active_legacy_reference_count",
    "unresolved_legacy_reference_count",
    "legacy_four_level_full_runtime_retired",
    "canonical_five_level_runtime_complete",
    "retirement_evidence_passed",
    "R3_formal_retirement_bound",
    "source_C1_commit_identity",
    "source_C1_file_identities",
    "C1_public_apis",
    "C1_public_apis_keyword_only",
    "C1_parser_contract",
    "C1_exact6_contract",
    "C1_conditioned_loader_contract",
    "source_model_consumption_formal_gate_contract",
    "C1_central_helper_bound",
    "source_C2_commit_identity",
    "source_C2_file_identity",
    "C2_generate_ligands_ast_evidence",
    "C2_generate_ligands_forwarding_bound",
    "source_C3_commit_identity",
    "source_C3_file_identity",
    "C3_covalent_demo_ast_evidence",
    "C3_covalent_demo_forwarding_bound",
    "selected_v1_supported_callers",
    "supported_caller_count",
    "deferred_callers",
    "deferred_caller_count",
    "canonical_mask_semantic_names",
    "canonical_mask_count",
    "canonical_B2_semantic",
    "canonical_B3_semantic",
    "sixth_mask_added",
    "failure_contract",
    "automatic_target_inference_sources",
    "C4_exact_path_scope",
    "C4_exact_path_scope_count",
    "C4_gate_implemented",
    "C4_gate_lifecycle_profile",
    "C4_gate_commit",
    "C4_gate_committed",
    "C4_gate_published",
    "ready_for_C4_commit_review",
    "repository_cli_selector_forwarding_complete",
    "ready_for_repository_cli_runtime_smoke_planning",
    "recommended_next_step",
    "real_repository_cli_runtime_smoke_executed",
    "training_or_parameter_update",
    "RL_implementation_started",
    "feature_semantics_audit_required_before_training",
    "Step12D_smoke_is_not_final_training_feature_contract",
    "checkpoint_loaded_by_C4_gate",
    "model_forward_executed_by_C4_gate",
    "repository_cli_forwarding_gate_response_sha256",
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


def _raise_invalid(error: BaseException | None = None) -> None:
    if error is None:
        raise ValueError(_ERROR)
    raise ValueError(_ERROR) from error


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
            _raise_invalid()
        return parsed
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


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
        _raise_invalid()
    return completed.stdout


def _git_text(repo_root: Path, arguments: Sequence[str]) -> str:
    try:
        return _git_bytes(repo_root, arguments).decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        _raise_invalid(error)


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
        _raise_invalid()
    return completed.returncode == 0


def _git_blob_bytes(
    repo_root: Path,
    *,
    commit: str,
    relative_path: str,
    expected_sha256: str | None = None,
) -> bytes:
    _canonical_relative_path(relative_path)
    if re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        _raise_invalid()
    row = _git_text(repo_root, ["ls-tree", commit, "--", relative_path])
    match = re.fullmatch(
        rf"100644 blob ([0-9a-f]{{40}})\t{re.escape(relative_path)}\n",
        row,
    )
    if match is None:
        _raise_invalid()
    payload = _git_bytes(repo_root, ["cat-file", "blob", match.group(1)])
    if (
        not payload
        or len(payload) > _MAX_SOURCE_BYTES
        or (expected_sha256 is not None and _sha256(payload) != expected_sha256)
    ):
        _raise_invalid()
    return payload


def _read_live_regular_file(
    repo_root: Path,
    relative_path: str,
    *,
    expected_sha256: str | None = None,
) -> bytes:
    parsed = _canonical_relative_path(relative_path)
    path = repo_root.joinpath(*parsed.parts)
    try:
        metadata = path.lstat()
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_mode & 0o111
            or metadata.st_size <= 0
            or metadata.st_size > _MAX_SOURCE_BYTES
        ):
            _raise_invalid()
        payload = path.read_bytes()
        final = path.lstat()
        if (
            len(payload) != metadata.st_size
            or (metadata.st_dev, metadata.st_ino, metadata.st_size)
            != (final.st_dev, final.st_ino, final.st_size)
            or (expected_sha256 is not None and _sha256(payload) != expected_sha256)
        ):
            _raise_invalid()
        return payload
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _commit_identity(
    repo_root: Path,
    *,
    commit: str,
    parent: str,
    subject: str,
    files: Mapping[str, str],
    statuses: Mapping[str, str],
    require_live: bool,
) -> tuple[dict[str, Any], dict[str, dict[str, object]]]:
    try:
        if set(files) != set(statuses) or not files:
            _raise_invalid()
        metadata = _git_text(
            repo_root,
            ["show", "-s", "--format=%H%x00%P%x00%s%x00%b", commit],
        ).rstrip("\n").split("\x00")
        if metadata != [commit, parent, subject, ""]:
            _raise_invalid()
        rows = _git_text(
            repo_root,
            ["diff-tree", "--no-commit-id", "--name-status", "-r", commit],
        ).splitlines()
        actual_statuses: dict[str, str] = {}
        for row in rows:
            parts = row.split("\t")
            if len(parts) != 2 or parts[0] not in {"A", "M"}:
                _raise_invalid()
            actual_statuses[parts[1]] = parts[0]
        if actual_statuses != dict(statuses):
            _raise_invalid()
        identities: dict[str, dict[str, object]] = {}
        for relative_path, expected_sha256 in files.items():
            row = _git_text(repo_root, ["ls-tree", commit, "--", relative_path])
            match = re.fullmatch(
                rf"100644 blob ([0-9a-f]{{40}})\t{re.escape(relative_path)}\n",
                row,
            )
            if match is None:
                _raise_invalid()
            commit_payload = _git_blob_bytes(
                repo_root,
                commit=commit,
                relative_path=relative_path,
                expected_sha256=expected_sha256,
            )
            if require_live:
                live_payload = _read_live_regular_file(
                    repo_root,
                    relative_path,
                    expected_sha256=expected_sha256,
                )
                if live_payload != commit_payload:
                    _raise_invalid()
            identities[relative_path] = {
                "sha256": expected_sha256,
                "git_blob": match.group(1),
                "git_mode": "100644",
                "live_bytes_match_commit": require_live,
            }
        if not _is_ancestor(repo_root, commit, "HEAD") or not _is_ancestor(
            repo_root, commit, "origin/main"
        ):
            _raise_invalid()
        identity = {
            "commit": commit,
            "parent": parent,
            "subject": subject,
            "body_empty": True,
            "single_parent": True,
            "scope": list(files),
            "scope_count": len(files),
            "ancestor_of_HEAD": True,
            "ancestor_of_origin_main": True,
        }
        return identity, identities
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _parse_python(payload: bytes) -> ast.Module:
    try:
        return ast.parse(payload.decode("utf-8", errors="strict"))
    except Exception as error:
        _raise_invalid(error)


def _attribute_chain(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _attribute_chain(node.value)
        return None if parent is None else f"{parent}.{node.attr}"
    return None


def _calls(tree: ast.AST, name: str) -> list[ast.Call]:
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _attribute_chain(node.func) == name
    ]


def _find_function(tree: ast.Module, name: str) -> ast.FunctionDef:
    candidates = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    if len(candidates) != 1:
        _raise_invalid()
    return candidates[0]


def _keyword_name(call: ast.Call, keyword: str) -> str | None:
    values = [item.value for item in call.keywords if item.arg == keyword]
    if len(values) != 1 or not isinstance(values[0], ast.Name):
        return None
    return values[0].id


def _import_evidence(tree: ast.Module) -> dict[str, object]:
    sites = [
        node
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module
        == "covalent_ext.covapie_target_residue_atom_condition_repository_cli_v1"
    ]
    counts = {
        symbol: sum(alias.name == symbol for site in sites for alias in site.names)
        for symbol in _C1_APIS
    }
    if len(sites) != 1 or counts != {symbol: 1 for symbol in _C1_APIS}:
        _raise_invalid()
    return {"C1_helper_module_import_site_count": 1, "C1_symbol_import_counts": counts}


def _is_none_selector_branch(node: ast.If) -> bool:
    test = node.test
    return (
        isinstance(test, ast.Compare)
        and isinstance(test.left, ast.Name)
        and test.left.id == "target_residue_atom_condition_spec"
        and len(test.ops) == 1
        and isinstance(test.ops[0], ast.Is)
        and len(test.comparators) == 1
        and isinstance(test.comparators[0], ast.Constant)
        and test.comparators[0].value is None
    )


def _contains_call(nodes: Sequence[ast.stmt], name: str) -> int:
    return sum(len(_calls(node, name)) for node in nodes)


def _c1_contract_evidence(
    source_tree: ast.Module,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    try:
        from covalent_ext import (
            covapie_target_residue_atom_condition_repository_cli_v1 as helper,
        )

        if helper.__all__ != _C1_APIS:
            _raise_invalid()
        keyword_only = True
        for name in _C1_APIS:
            signature = inspect.signature(getattr(helper, name))
            if not signature.parameters or any(
                parameter.kind is not inspect.Parameter.KEYWORD_ONLY
                for parameter in signature.parameters.values()
            ):
                keyword_only = False
        if not keyword_only:
            _raise_invalid()

        parser = argparse.ArgumentParser(add_help=False)
        before = set(parser._option_string_actions)
        returned = helper.add_covapie_target_residue_atom_condition_cli_arguments_v1(
            parser=parser
        )
        after = set(parser._option_string_actions)
        if returned is not parser or after - before != set(_TARGET_OPTIONS):
            _raise_invalid()
        legacy = helper.resolve_covapie_target_residue_atom_condition_cli_args_v1(
            arguments=parser.parse_args([])
        )
        exact6 = helper.resolve_covapie_target_residue_atom_condition_cli_args_v1(
            arguments=parser.parse_args(
                [
                    "--target_residue_atom_conditioning",
                    "--target_chain_id",
                    "A",
                    "--target_residue_sequence_number",
                    "123",
                ]
            )
        )
        expected_exact6 = {
            "chain_id": "A",
            "residue_sequence_number": 123,
            "residue_insertion_code": " ",
            "residue_name": "CYS",
            "atom_name": "SG",
            "element": "S",
        }
        invalid_cases = (
            {"target_residue_atom_conditioning": True},
            {
                "target_chain_id": "A",
                "target_residue_sequence_number": 123,
            },
            {"target_unknown": "x"},
            {
                "target_residue_atom_conditioning": 1,
                "target_chain_id": "A",
                "target_residue_sequence_number": 123,
            },
            {
                "target_residue_atom_conditioning": True,
                "target_chain_id": " A ",
                "target_residue_sequence_number": 123,
            },
            {
                "target_residue_atom_conditioning": True,
                "target_chain_id": "A",
                "target_residue_sequence_number": True,
            },
        )
        for case in invalid_cases:
            try:
                helper.resolve_covapie_target_residue_atom_condition_cli_args_v1(
                    arguments=case
                )
            except ValueError as error:
                if str(error) != _C1_ERROR:
                    _raise_invalid()
            else:
                _raise_invalid()
        if legacy is not None or exact6 != expected_exact6 or tuple(exact6) != _EXACT6_FIELDS:
            _raise_invalid()

        loader = _find_function(
            source_tree,
            "load_covapie_target_residue_conditioned_model_from_checkpoint_v1",
        )
        top_level_torch_imports = [
            node
            for node in source_tree.body
            if isinstance(node, (ast.Import, ast.ImportFrom))
            and (
                any(alias.name == "torch" for alias in getattr(node, "names", []))
                or getattr(node, "module", None) == "torch"
            )
        ]
        loader_names = {
            _attribute_chain(node.func)
            for node in ast.walk(loader)
            if isinstance(node, ast.Call)
        }
        if (
            top_level_torch_imports
            or "torch.load" not in loader_names
            or "load_covapie_base_state_dict_into_target_residue_conditioned_model_v1"
            not in loader_names
            or "torch.random.set_rng_state" not in loader_names
            or "model.state_dict" not in loader_names
        ):
            _raise_invalid()
        parser_contract = {
            "added_option_strings": list(_TARGET_OPTIONS),
            "added_option_count": 3,
            "legacy_arguments_return_none": True,
            "partial_selector_rejected": True,
            "unknown_target_field_rejected": True,
        }
        exact6_contract = {
            "selector_type": "Exact6",
            "fields": list(_EXACT6_FIELDS),
            "example": exact6,
            "fixed_fields": {
                "residue_insertion_code": " ",
                "residue_name": "CYS",
                "atom_name": "SG",
                "element": "S",
            },
        }
        loader_contract = {
            "loader_public_api_keyword_only": True,
            "torch_import_is_function_local": True,
            "frozen_checkpoint_identity_checked_before_deserialization": True,
            "conditioned_constructor_enabled": True,
            "single_key_migration_helper_called": True,
            "strict_migration_report_required": True,
            "checkpoint_bytes_rechecked_unchanged": True,
            "CPU_RNG_restored": True,
            "loader_executed_by_C4_gate": False,
        }
        return parser_contract, exact6_contract, loader_contract
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _formal_model_gate_contract(repo_root: Path) -> dict[str, object]:
    try:
        identity, files = _commit_identity(
            repo_root,
            commit=_MODEL_GATE_COMMIT,
            parent=_MODEL_GATE_PARENT,
            subject=_MODEL_GATE_SUBJECT,
            files=_MODEL_GATE_FILES,
            statuses={path: "A" for path in _MODEL_GATE_FILES},
            require_live=False,
        )
        bundle_path = repo_root.parent / _MODEL_GATE_BUNDLE_RELATIVE
        metadata = bundle_path.lstat()
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_mode & 0o111
            or metadata.st_size != _MODEL_GATE_BUNDLE_SIZE
        ):
            _raise_invalid()
        payload = bundle_path.read_bytes()
        final = bundle_path.lstat()
        if (
            len(payload) != _MODEL_GATE_BUNDLE_SIZE
            or _sha256(payload) != _MODEL_GATE_BUNDLE_SHA256
            or (metadata.st_dev, metadata.st_ino, metadata.st_size)
            != (final.st_dev, final.st_ino, final.st_size)
        ):
            _raise_invalid()
        decoded = json.loads(payload.decode("utf-8", errors="strict"))
        if type(decoded) is not dict or _canonical_json_bytes(decoded) != payload:
            _raise_invalid()
        unsigned = dict(decoded)
        internal = unsigned.pop("model_consumption_gate_response_sha256", None)
        if (
            internal != _MODEL_GATE_INTERNAL_SHA256
            or _sha256(_canonical_json_bytes(unsigned)) != internal
            or decoded.get("model_consumption_gate_implemented") is not True
            or decoded.get("model_consumption_implemented") is not True
            or decoded.get("indicator_passed_into_dynamics") is not True
            or decoded.get("indicator_consumed_by_model") is not True
            or decoded.get("ready_for_repository_cli_forwarding_design") is not True
            or decoded.get("training_or_parameter_update") is not False
            or decoded.get("feature_semantics_audit_required_before_training")
            is not True
        ):
            _raise_invalid()
        return {
            "commit_identity": identity,
            "commit_snapshot_file_identities": files,
            "formal_bundle_size": _MODEL_GATE_BUNDLE_SIZE,
            "formal_bundle_transport_sha256": _MODEL_GATE_BUNDLE_SHA256,
            "formal_bundle_internal_sha256": _MODEL_GATE_INTERNAL_SHA256,
            "model_consumption_gate_implemented": True,
            "model_consumption_implemented": True,
            "indicator_passed_into_dynamics": True,
            "indicator_consumed_by_model": True,
            "formal_gate_executed_by_C4_gate": False,
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _c2_ast_evidence(tree: ast.Module) -> dict[str, object]:
    try:
        evidence = _import_evidence(tree)
        counts = {
            "parser_helper_call_count": len(
                _calls(
                    tree,
                    "add_covapie_target_residue_atom_condition_cli_arguments_v1",
                )
            ),
            "parse_args_call_count": len(_calls(tree, "parser.parse_args")),
            "resolver_call_count": len(
                _calls(
                    tree,
                    "resolve_covapie_target_residue_atom_condition_cli_args_v1",
                )
            ),
            "conditioned_loader_call_count": len(
                _calls(
                    tree,
                    "load_covapie_target_residue_conditioned_model_from_checkpoint_v1",
                )
            ),
            "legacy_loader_call_count": len(
                _calls(tree, "LigandPocketDDPM.load_from_checkpoint")
            ),
            "model_to_call_count": len(_calls(tree, "model.to")),
            "model_generate_ligands_call_count": len(
                _calls(tree, "model.generate_ligands")
            ),
            "write_sdf_file_call_count": len(_calls(tree, "utils.write_sdf_file")),
        }
        if counts != {
            "parser_helper_call_count": 1,
            "parse_args_call_count": 1,
            "resolver_call_count": 1,
            "conditioned_loader_call_count": 1,
            "legacy_loader_call_count": 1,
            "model_to_call_count": 1,
            "model_generate_ligands_call_count": 1,
            "write_sdf_file_call_count": 1,
        }:
            _raise_invalid()
        names = (
            "add_covapie_target_residue_atom_condition_cli_arguments_v1",
            "parser.parse_args",
            "resolve_covapie_target_residue_atom_condition_cli_args_v1",
            "LigandPocketDDPM.load_from_checkpoint",
            "model.to",
            "model.generate_ligands",
            "utils.write_sdf_file",
        )
        positions = []
        for name in names:
            calls = _calls(tree, name)
            if len(calls) != 1:
                _raise_invalid()
            positions.append((calls[0].lineno, calls[0].col_offset))
        conditioned_position = _calls(
            tree,
            "load_covapie_target_residue_conditioned_model_from_checkpoint_v1",
        )[0].lineno
        if not (
            positions[0] < positions[1] < positions[2]
            and positions[2][0] < min(positions[3][0], conditioned_position)
            and max(positions[3][0], conditioned_position) < positions[4][0]
            and positions[4] < positions[5] < positions[6]
        ):
            _raise_invalid()
        branches = [node for node in ast.walk(tree) if isinstance(node, ast.If) and _is_none_selector_branch(node)]
        if len(branches) != 1:
            _raise_invalid()
        branch = branches[0]
        if (
            _contains_call(branch.body, "LigandPocketDDPM.load_from_checkpoint") != 1
            or _contains_call(
                branch.body,
                "load_covapie_target_residue_conditioned_model_from_checkpoint_v1",
            )
            != 0
            or _contains_call(branch.orelse, "LigandPocketDDPM.load_from_checkpoint")
            != 0
            or _contains_call(
                branch.orelse,
                "load_covapie_target_residue_conditioned_model_from_checkpoint_v1",
            )
            != 1
            or any(isinstance(node, ast.Try) for node in ast.walk(branch))
        ):
            _raise_invalid()
        generation = _calls(tree, "model.generate_ligands")[0]
        if (
            _keyword_name(generation, "target_residue_atom_condition_spec")
            != "target_residue_atom_condition_spec"
            or len(generation.args) < 4
            or _attribute_chain(generation.args[2]) != "args.resi_list"
            or _attribute_chain(generation.args[3]) != "args.ref_ligand"
        ):
            _raise_invalid()
        imports = [
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        ]
        call_names = {
            _attribute_chain(node.func)
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
        }
        string_constants = {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and type(node.value) is str
        }
        if (
            any("checkpoint_migration" in module for module in imports)
            or any(name and ("prepare_pocket" in name or ".ddpm." in name) for name in call_names)
            or any(option in string_constants for option in _TARGET_OPTIONS)
            or {"CYS", "SG", "S"}.issubset(string_constants)
        ):
            _raise_invalid()
        evidence.update(counts)
        evidence.update(
            {
                "selector_forwarding_keyword_count": 1,
                "required_execution_order_proven": True,
                "legacy_loader_only_when_selector_is_none": True,
                "conditioned_loader_only_in_else": True,
                "conditioned_loader_failure_has_no_fallback": True,
                "selector_forwarded_to_every_batch": True,
                "resi_list_identity_preserved": True,
                "ref_ligand_identity_preserved": True,
                "pocket_selection_not_inferred_from_selector": True,
                "C1_logic_not_duplicated": True,
                "migration_helper_import_count": 0,
                "manual_indicator_creation_count": 0,
                "direct_prepare_pocket_call_count": 0,
                "direct_ddpm_or_dynamics_call_count": 0,
            }
        )
        return evidence
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _literal_assignment(tree: ast.Module, name: str) -> object:
    values = [
        node.value
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (
            node.targets if isinstance(node, ast.Assign) else [node.target]
        )
        if isinstance(target, ast.Name) and target.id == name
    ]
    if len(values) != 1:
        _raise_invalid()
    try:
        return ast.literal_eval(values[0])
    except Exception as error:
        _raise_invalid(error)


def _c3_ast_evidence(tree: ast.Module) -> dict[str, object]:
    try:
        evidence = _import_evidence(tree)
        functions = {
            name: _find_function(tree, name)
            for name in (
                "build_parser",
                "build_canonical_mask",
                "prepare_single_pocket",
                "run_covalent_inpaint",
                "main",
            )
        }
        build_parser_constants = {
            node.value
            for node in ast.walk(functions["build_parser"])
            if isinstance(node, ast.Constant) and type(node.value) is str
        }
        target_flag_count = sum(option in build_parser_constants for option in _TARGET_OPTIONS)
        counts = {
            "build_parser_target_flag_count": target_flag_count,
            "actual_main_parser_helper_call_count": len(
                _calls(
                    functions["main"],
                    "add_covapie_target_residue_atom_condition_cli_arguments_v1",
                )
            ),
            "resolver_call_count": len(
                _calls(
                    functions["main"],
                    "resolve_covapie_target_residue_atom_condition_cli_args_v1",
                )
            ),
            "conditioned_loader_call_count": len(
                _calls(
                    functions["main"],
                    "load_covapie_target_residue_conditioned_model_from_checkpoint_v1",
                )
            ),
            "legacy_loader_call_count": len(
                _calls(functions["main"], "LigandPocketDDPM.load_from_checkpoint")
            ),
            "model_to_call_count": len(_calls(functions["main"], "model.to")),
            "build_long_form_mask_call_count": len(
                _calls(functions["build_canonical_mask"], "build_long_form_mask")
            ),
            "sample_given_pocket_call_count": len(
                _calls(functions["run_covalent_inpaint"], "model.ddpm.sample_given_pocket")
            ),
            "ddpm_inpaint_call_count": len(
                _calls(functions["run_covalent_inpaint"], "model.ddpm.inpaint")
            ),
            "write_sdf_file_call_count": len(
                _calls(functions["main"], "utils.write_sdf_file")
            ),
        }
        expected_counts = {
            "build_parser_target_flag_count": 0,
            "actual_main_parser_helper_call_count": 1,
            "resolver_call_count": 1,
            "conditioned_loader_call_count": 1,
            "legacy_loader_call_count": 1,
            "model_to_call_count": 1,
            "build_long_form_mask_call_count": 1,
            "sample_given_pocket_call_count": 1,
            "ddpm_inpaint_call_count": 2,
            "write_sdf_file_call_count": 1,
        }
        if counts != expected_counts:
            _raise_invalid()
        main = functions["main"]
        helper_calls = _calls(
            main, "add_covapie_target_residue_atom_condition_cli_arguments_v1"
        )
        parse_calls = _calls(main, "parser.parse_args")
        resolver_calls = _calls(
            main, "resolve_covapie_target_residue_atom_condition_cli_args_v1"
        )
        legacy_calls = _calls(main, "LigandPocketDDPM.load_from_checkpoint")
        conditioned_calls = _calls(
            main,
            "load_covapie_target_residue_conditioned_model_from_checkpoint_v1",
        )
        if (
            len(parse_calls) != 1
            or not (
                helper_calls[0].lineno
                < parse_calls[0].lineno
                < resolver_calls[0].lineno
                < min(legacy_calls[0].lineno, conditioned_calls[0].lineno)
            )
        ):
            _raise_invalid()
        branches = [node for node in ast.walk(main) if isinstance(node, ast.If) and _is_none_selector_branch(node)]
        if len(branches) != 1:
            _raise_invalid()
        branch = branches[0]
        if (
            _contains_call(branch.body, "LigandPocketDDPM.load_from_checkpoint") != 1
            or _contains_call(
                branch.orelse,
                "load_covapie_target_residue_conditioned_model_from_checkpoint_v1",
            )
            != 1
            or _contains_call(branch.orelse, "LigandPocketDDPM.load_from_checkpoint")
            != 0
            or any(isinstance(node, ast.Try) for node in ast.walk(branch))
        ):
            _raise_invalid()

        main_run = _calls(main, "run_covalent_inpaint")
        run_prepare = _calls(functions["run_covalent_inpaint"], "prepare_single_pocket")
        prepare_model = _calls(functions["prepare_single_pocket"], "model.prepare_pocket")
        if (
            len(main_run) != 1
            or len(run_prepare) != 1
            or len(prepare_model) != 1
            or _keyword_name(main_run[0], "target_residue_atom_condition_spec")
            != "target_residue_atom_condition_spec"
            or _keyword_name(run_prepare[0], "target_residue_atom_condition_spec")
            != "target_residue_atom_condition_spec"
            or _keyword_name(prepare_model[0], "target_residue_atom_condition_spec")
            != "target_residue_atom_condition_spec"
        ):
            _raise_invalid()
        pocket_calls = _calls(functions["prepare_single_pocket"], "utils.get_pocket_from_ligand")
        if (
            len(pocket_calls) != 1
            or not prepare_model[0].args
            or not isinstance(prepare_model[0].args[0], ast.Name)
            or prepare_model[0].args[0].id != "residues"
        ):
            _raise_invalid()
        sensitive_calls = (
            _calls(functions["run_covalent_inpaint"], "build_canonical_mask")
            + _calls(functions["run_covalent_inpaint"], "model.ddpm.sample_given_pocket")
            + _calls(functions["run_covalent_inpaint"], "model.ddpm.inpaint")
        )
        if any(
            "target_residue_atom_condition_spec" in ast.dump(call)
            for call in sensitive_calls
        ):
            _raise_invalid()
        canonical = _literal_assignment(tree, "CANONICAL_MASK_SEMANTICS")
        mapping = _literal_assignment(tree, "MASK_SEMANTIC_TO_INTERNAL")
        if (
            canonical != _CANONICAL_MASK_SEMANTICS
            or type(mapping) is not dict
            or list(mapping) != list(_CANONICAL_MASK_SEMANTICS)
            or mapping.get("scaffold_plus_warhead") != "B2_scaffold_warhead"
            or mapping.get("scaffold_only") != "B3_scaffold_only"
            or len(mapping) != 5
        ):
            _raise_invalid()
        assignments_to_selector = [
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.Assign, ast.AnnAssign))
            and any(
                isinstance(target, ast.Name)
                and target.id == "target_residue_atom_condition_spec"
                for target in (
                    node.targets if isinstance(node, ast.Assign) else [node.target]
                )
            )
        ]
        if len(assignments_to_selector) != 1:
            _raise_invalid()
        evidence.update(counts)
        evidence.update(
            {
                "main_to_run_selector_forwarding_count": 1,
                "run_to_prepare_selector_forwarding_count": 1,
                "prepare_to_model_selector_forwarding_count": 1,
                "three_layer_selector_forwarding_identity_proven": True,
                "build_parser_R1_mask_contract_preserved": True,
                "actual_main_supports_three_C1_target_flags": True,
                "selector_resolved_before_loader": True,
                "legacy_conditioned_loader_branches_mutually_exclusive": True,
                "conditioned_loader_failure_has_no_fallback": True,
                "pocket_residues_from_get_pocket_from_ligand": True,
                "pocket_residues_identity_preserved": True,
                "selector_not_passed_to_mask_builder": True,
                "selector_not_passed_to_DDPM": True,
                "manual_indicator_creation_count": 0,
                "canonical_mask_count": 5,
                "canonical_B2_internal": "B2_scaffold_warhead",
                "canonical_B3_internal": "B3_scaffold_only",
                "sixth_mask_added": False,
            }
        )
        return evidence
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _deferred_caller_contracts() -> list[dict[str, object]]:
    return [
        {
            "caller": "test.py",
            "deferred": True,
            "reason": "multiple_distinct_pdb_or_pocket_samples_require_per_sample_targets",
            "required_successor_contract": "canonical_per_sample_target_manifest",
            "global_selector_reuse_allowed": False,
        },
        {
            "caller": "optimize.py",
            "deferred": True,
            "reason": "multi_round_diversify_is_outside_the_two_minimal_core_tasks",
            "required_successor_contract": "audit_static_target_reuse_across_every_population_generation",
        },
        {
            "caller": "inpaint.py",
            "deferred": True,
            "reason": "generic_inpaint_overlaps_the_selected_covalent_specific_demo",
            "required_successor_contract": "single_shared_selector_parser_and_error_contract_before_second_inpaint_entry",
        },
        {
            "caller": "colab/DiffSBDD.ipynb",
            "deferred": True,
            "reason": "notebook_clones_upstream_and_uses_a_different_checkpoint",
            "required_successor_contract": "bind_covapie_source_checkpoint_identity_and_migration_helper_distribution",
            "ui_only_change_cannot_claim_support": True,
        },
    ]


def _lifecycle_from_facts(facts: Mapping[str, Any]) -> dict[str, Any]:
    try:
        head = facts["head"]
        origin = facts["origin_main"]
        ahead = facts["ahead"]
        behind = facts["behind"]
        untracked_raw = facts["ordinary_untracked_paths"]
        tracked_gate_raw = facts["tracked_gate_paths"]
        tracked_changes_raw = facts["tracked_changes"]
        staged_changes_raw = facts["staged_changes"]
        regular = facts["regular_gate_paths"] is True
        candidates = facts["c4_candidates"]
        string_lists = (
            untracked_raw,
            tracked_gate_raw,
            tracked_changes_raw,
            staged_changes_raw,
        )
        if (
            type(head) is not str
            or re.fullmatch(r"[0-9a-f]{40}", head) is None
            or type(origin) is not str
            or re.fullmatch(r"[0-9a-f]{40}", origin) is None
            or type(ahead) is not int
            or type(ahead) is bool
            or type(behind) is not int
            or type(behind) is bool
            or min(ahead, behind) < 0
            or any(
                type(items) is not list
                or any(type(item) is not str for item in items)
                or len(items) != len(set(items))
                for items in string_lists
            )
            or type(candidates) is not list
            or any(type(item) is not dict for item in candidates)
        ):
            _raise_invalid()
        untracked = set(untracked_raw)
        tracked_gate = set(tracked_gate_raw)
        tracked_changes = set(tracked_changes_raw)
        staged_changes = set(staged_changes_raw)
        c4_paths = set(_C4_PATHS)
        precommit = (
            head == _C3_COMMIT
            and origin == _C3_COMMIT
            and ahead == 0
            and behind == 0
            and untracked == c4_paths
            and not tracked_gate
            and not tracked_changes
            and not staged_changes
            and regular
            and not candidates
        )
        valid_candidates = [
            item
            for item in candidates
            if type(item.get("commit")) is str
            and re.fullmatch(r"[0-9a-f]{40}", item["commit"]) is not None
            and item.get("subject") == _C4_SUBJECT
            and item.get("parents") == [_C3_COMMIT]
            and type(item.get("paths")) is list
            and all(type(path) is str for path in item["paths"])
            and set(item["paths"]) == c4_paths
            and len(item.get("paths", [])) == len(_C4_PATHS)
            and item.get("head_ancestor") is True
            and item.get("body_empty") is True
            and item.get("gate_commit_modes_bound") is True
            and item.get("gate_commit_blobs_bound") is True
            and item.get("gate_live_bytes_match_commit") is True
        ]
        committed_common = (
            tracked_gate == c4_paths
            and regular
            and not (untracked & c4_paths)
            and not (tracked_changes & c4_paths)
            and not (staged_changes & c4_paths)
            and len(candidates) == 1
            and len(valid_candidates) == 1
        )
        if precommit:
            return {
                "profile": "c4_precommit_candidate",
                "commit": None,
                "committed": False,
                "published": False,
            }
        if committed_common:
            item = valid_candidates[0]
            published = item.get("origin_main_ancestor") is True
            if published:
                return {
                    "profile": "c4_published_successor",
                    "commit": item["commit"],
                    "committed": True,
                    "published": True,
                }
            if (
                head != item["commit"]
                or origin != _C3_COMMIT
                or (ahead, behind) != (1, 0)
                or untracked
                or tracked_changes
                or staged_changes
            ):
                _raise_invalid()
            return {
                "profile": "c4_committed_unpushed",
                "commit": item["commit"],
                "committed": True,
                "published": False,
            }
        _raise_invalid()
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _c4_lifecycle_evidence(repo_root: Path) -> dict[str, Any]:
    head = _git_text(repo_root, ["rev-parse", "HEAD"]).strip()
    origin = _git_text(repo_root, ["rev-parse", "origin/main"]).strip()
    counts = _git_text(
        repo_root, ["rev-list", "--left-right", "--count", "origin/main...HEAD"]
    ).strip().split()
    if len(counts) != 2 or any(re.fullmatch(r"[0-9]+", item) is None for item in counts):
        _raise_invalid()
    behind, ahead = (int(item) for item in counts)
    tracked = set(_git_text(repo_root, ["ls-files"]).splitlines())
    untracked = _git_text(
        repo_root, ["ls-files", "--others", "--exclude-standard"]
    ).splitlines()
    tracked_changes = _git_text(repo_root, ["diff", "--name-only"]).splitlines()
    staged_changes = _git_text(
        repo_root, ["diff", "--cached", "--name-only"]
    ).splitlines()
    live_payloads: dict[str, bytes] = {}
    regular = True
    for relative_path in _C4_PATHS:
        try:
            live_payloads[relative_path] = _read_live_regular_file(
                repo_root, relative_path
            )
        except ValueError:
            regular = False
            break
    candidates: list[dict[str, Any]] = []
    if head != _C3_COMMIT and _is_ancestor(repo_root, _C3_COMMIT, head):
        commits = _git_text(
            repo_root,
            ["rev-list", "--ancestry-path", f"{_C3_COMMIT}..{head}"],
        ).splitlines()
        for commit in commits:
            metadata = _git_text(
                repo_root,
                ["show", "-s", "--format=%H%x00%P%x00%s%x00%b", commit],
            ).rstrip("\n").split("\x00")
            if len(metadata) != 4 or metadata[2] != _C4_SUBJECT:
                continue
            commit_hash, parent_text, subject, body = metadata
            paths = _git_text(
                repo_root,
                ["diff-tree", "--no-commit-id", "--name-only", "-r", commit],
            ).splitlines()
            modes_bound = True
            blobs_bound = True
            live_match = regular
            for relative_path in _C4_PATHS:
                row = _git_text(repo_root, ["ls-tree", commit, "--", relative_path])
                match = re.fullmatch(
                    rf"100644 blob ([0-9a-f]{{40}})\t{re.escape(relative_path)}\n",
                    row,
                )
                if match is None:
                    modes_bound = False
                    blobs_bound = False
                    live_match = False
                    continue
                try:
                    committed_payload = _git_blob_bytes(
                        repo_root,
                        commit=commit,
                        relative_path=relative_path,
                    )
                except ValueError:
                    blobs_bound = False
                    live_match = False
                    continue
                if live_payloads.get(relative_path) != committed_payload:
                    live_match = False
            candidates.append(
                {
                    "commit": commit_hash,
                    "subject": subject,
                    "parents": parent_text.split(),
                    "paths": paths,
                    "head_ancestor": _is_ancestor(repo_root, commit, "HEAD"),
                    "origin_main_ancestor": _is_ancestor(
                        repo_root, commit, "origin/main"
                    ),
                    "body_empty": body == "",
                    "gate_commit_modes_bound": modes_bound,
                    "gate_commit_blobs_bound": blobs_bound,
                    "gate_live_bytes_match_commit": live_match,
                }
            )
    return _lifecycle_from_facts(
        {
            "head": head,
            "origin_main": origin,
            "ahead": ahead,
            "behind": behind,
            "ordinary_untracked_paths": untracked,
            "tracked_gate_paths": sorted(tracked & set(_C4_PATHS)),
            "tracked_changes": tracked_changes,
            "staged_changes": staged_changes,
            "regular_gate_paths": regular,
            "c4_candidates": candidates,
        }
    )


def _lifecycle_claims(profile: str) -> dict[str, object]:
    contracts: dict[str, dict[str, object]] = {
        "c4_precommit_candidate": {
            "C4_gate_committed": False,
            "C4_gate_published": False,
            "ready_for_C4_commit_review": True,
            "repository_cli_selector_forwarding_complete": False,
            "ready_for_repository_cli_runtime_smoke_planning": False,
            "recommended_next_step": (
                "commit_and_push_covapie_target_residue_atom_condition_repository_cli_forwarding_gate_C4_v1"
            ),
        },
        "c4_committed_unpushed": {
            "C4_gate_committed": True,
            "C4_gate_published": False,
            "ready_for_C4_commit_review": False,
            "repository_cli_selector_forwarding_complete": True,
            "ready_for_repository_cli_runtime_smoke_planning": False,
            "recommended_next_step": (
                "push_covapie_target_residue_repository_cli_forwarding_gate_C4_v1"
            ),
        },
        "c4_published_successor": {
            "C4_gate_committed": True,
            "C4_gate_published": True,
            "ready_for_C4_commit_review": False,
            "repository_cli_selector_forwarding_complete": True,
            "ready_for_repository_cli_runtime_smoke_planning": True,
            "recommended_next_step": (
                "design_bounded_covapie_repository_cli_conditioned_runtime_smoke_v1"
            ),
        },
    }
    if profile not in contracts:
        _raise_invalid()
    return dict(contracts[profile])


def _validate_response(
    response: Mapping[str, Any],
    *,
    require_order: bool = True,
) -> bool:
    try:
        if (
            type(response) is not dict
            or len(response) != len(REPOSITORY_CLI_FORWARDING_GATE_RESPONSE_FIELDS)
            or set(response) != set(REPOSITORY_CLI_FORWARDING_GATE_RESPONSE_FIELDS)
            or (
                require_order
                and tuple(response) != REPOSITORY_CLI_FORWARDING_GATE_RESPONSE_FIELDS
            )
        ):
            _raise_invalid()
        unsigned = {
            field: response[field]
            for field in REPOSITORY_CLI_FORWARDING_GATE_RESPONSE_FIELDS
            if field != "repository_cli_forwarding_gate_response_sha256"
        }
        if response["repository_cli_forwarding_gate_response_sha256"] != _sha256(
            _canonical_json_bytes(unsigned)
        ):
            _raise_invalid()
        profile = response["C4_gate_lifecycle_profile"]
        if type(profile) is not str:
            _raise_invalid()
        claims = _lifecycle_claims(profile)
        if any(response[field] != value for field, value in claims.items()):
            _raise_invalid()
        commit = response["C4_gate_commit"]
        if profile == "c4_precommit_candidate":
            if commit is not None:
                _raise_invalid()
        elif type(commit) is not str or re.fullmatch(r"[0-9a-f]{40}", commit) is None:
            _raise_invalid()
        if (
            response["repository_cli_forwarding_gate_version"] != _VERSION
            or response["repository_cli_forwarding_gate_error_contract"] != _ERROR
            or response["R3_formal_retirement_bound"] is not True
            or response["C1_central_helper_bound"] is not True
            or response["C2_generate_ligands_forwarding_bound"] is not True
            or response["C3_covalent_demo_forwarding_bound"] is not True
            or response["selected_v1_supported_callers"] != list(_SUPPORTED_CALLERS)
            or response["supported_caller_count"] != 2
            or response["deferred_caller_count"] != 4
            or response["canonical_mask_semantic_names"]
            != list(_CANONICAL_MASK_SEMANTICS)
            or response["canonical_mask_count"] != 5
            or response["canonical_B2_semantic"] != "scaffold_plus_warhead"
            or response["canonical_B3_semantic"] != "scaffold_only"
            or response["sixth_mask_added"] is not False
            or response["C4_exact_path_scope"] != list(_C4_PATHS)
            or response["C4_exact_path_scope_count"] != 4
            or response["C4_gate_implemented"] is not True
            or response["real_repository_cli_runtime_smoke_executed"] is not False
            or response["training_or_parameter_update"] is not False
            or response["RL_implementation_started"] is not False
            or response["feature_semantics_audit_required_before_training"] is not True
            or response["Step12D_smoke_is_not_final_training_feature_contract"]
            is not True
            or response["checkpoint_loaded_by_C4_gate"] is not False
            or response["model_forward_executed_by_C4_gate"] is not False
        ):
            _raise_invalid()
        _canonical_json_bytes(response)
        return True
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def evaluate_covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1(
    *,
    repo_root: Path,
) -> dict[str, object]:
    """Evaluate the formal C4 forwarding gate without executing runtime code."""

    try:
        if (
            type(repo_root) is not type(Path())
            or not repo_root.is_absolute()
            or not repo_root.is_dir()
            or repo_root.is_symlink()
        ):
            _raise_invalid()

        r3_identity, r3_files = _commit_identity(
            repo_root,
            commit=_R3_COMMIT,
            parent=_R3_PARENT,
            subject=_R3_SUBJECT,
            files=_R3_FILES,
            statuses={path: "A" for path in _R3_FILES},
            require_live=True,
        )
        c1_identity, c1_files = _commit_identity(
            repo_root,
            commit=_C1_COMMIT,
            parent=_C1_PARENT,
            subject=_C1_SUBJECT,
            files=_C1_FILES,
            statuses={path: "A" for path in _C1_FILES},
            require_live=True,
        )
        c2_identity, c2_files = _commit_identity(
            repo_root,
            commit=_C2_COMMIT,
            parent=_C2_PARENT,
            subject=_C2_SUBJECT,
            files={_C2_PATH: _C2_SHA256},
            statuses={_C2_PATH: "M"},
            require_live=True,
        )
        c3_identity, c3_files = _commit_identity(
            repo_root,
            commit=_C3_COMMIT,
            parent=_C3_PARENT,
            subject=_C3_SUBJECT,
            files={_C3_PATH: _C3_SHA256},
            statuses={_C3_PATH: "M"},
            require_live=True,
        )
        if (
            c2_files[_C2_PATH]["git_blob"] != _C2_BLOB
            or c3_files[_C3_PATH]["git_blob"] != _C3_BLOB
        ):
            _raise_invalid()

        from covalent_ext import covapie_legacy_four_level_mask_retirement_gate_v1 as r3

        r3_response = r3.evaluate_covapie_legacy_four_level_mask_retirement_gate_v1(
            repo_root=repo_root
        )
        if (
            r3_response.get("R3_gate_lifecycle_profile")
            != "r3_published_successor"
            or r3_response.get("R3_gate_commit") != _R3_COMMIT
            or r3_response.get("R3_gate_committed") is not True
            or r3_response.get("R3_gate_published") is not True
            or r3_response.get("active_legacy_reference_count") != 0
            or r3_response.get("unresolved_legacy_reference_count") != 0
            or r3_response.get("legacy_four_level_full_runtime_retired") is not True
            or r3_response.get("canonical_five_level_runtime_complete") is not True
            or r3_response.get("retirement_evidence_passed") is not True
            or r3_response.get(
                "legacy_four_level_mask_retirement_gate_response_sha256"
            )
            != _R3_RESPONSE_SHA256
        ):
            _raise_invalid()

        c1_tree = _parse_python(
            _read_live_regular_file(
                repo_root,
                next(path for path in _C1_FILES if path.startswith("src/")),
                expected_sha256=_C1_FILES[
                    next(path for path in _C1_FILES if path.startswith("src/"))
                ],
            )
        )
        parser_contract, exact6_contract, loader_contract = _c1_contract_evidence(
            c1_tree
        )
        formal_model_gate = _formal_model_gate_contract(repo_root)
        c2_ast = _c2_ast_evidence(
            _parse_python(
                _read_live_regular_file(
                    repo_root, _C2_PATH, expected_sha256=_C2_SHA256
                )
            )
        )
        c3_ast = _c3_ast_evidence(
            _parse_python(
                _read_live_regular_file(
                    repo_root, _C3_PATH, expected_sha256=_C3_SHA256
                )
            )
        )
        lifecycle = _c4_lifecycle_evidence(repo_root)
        lifecycle_claims = _lifecycle_claims(lifecycle["profile"])
        deferred = _deferred_caller_contracts()
        failure_contract = {
            "canonical_error": _C1_ERROR,
            "partial_selector_rejected": True,
            "target_fields_without_enable_rejected": True,
            "unknown_target_field_rejected": True,
            "non_bool_enable_rejected": True,
            "unstripped_chain_rejected": True,
            "bool_residue_sequence_number_rejected": True,
            "conditioned_loader_failure_has_no_fallback": True,
        }

        values: dict[str, object] = {
            "repository_cli_forwarding_gate_version": _VERSION,
            "repository_cli_forwarding_gate_error_contract": _ERROR,
            "source_R3_commit_identity": r3_identity,
            "source_R3_file_identities": r3_files,
            "R3_gate_lifecycle_profile": "r3_published_successor",
            "R3_gate_commit": _R3_COMMIT,
            "R3_gate_committed": True,
            "R3_gate_published": True,
            "R3_response_sha256": _R3_RESPONSE_SHA256,
            "active_legacy_reference_count": 0,
            "unresolved_legacy_reference_count": 0,
            "legacy_four_level_full_runtime_retired": True,
            "canonical_five_level_runtime_complete": True,
            "retirement_evidence_passed": True,
            "R3_formal_retirement_bound": True,
            "source_C1_commit_identity": c1_identity,
            "source_C1_file_identities": c1_files,
            "C1_public_apis": list(_C1_APIS),
            "C1_public_apis_keyword_only": True,
            "C1_parser_contract": parser_contract,
            "C1_exact6_contract": exact6_contract,
            "C1_conditioned_loader_contract": loader_contract,
            "source_model_consumption_formal_gate_contract": formal_model_gate,
            "C1_central_helper_bound": True,
            "source_C2_commit_identity": c2_identity,
            "source_C2_file_identity": c2_files[_C2_PATH],
            "C2_generate_ligands_ast_evidence": c2_ast,
            "C2_generate_ligands_forwarding_bound": True,
            "source_C3_commit_identity": c3_identity,
            "source_C3_file_identity": c3_files[_C3_PATH],
            "C3_covalent_demo_ast_evidence": c3_ast,
            "C3_covalent_demo_forwarding_bound": True,
            "selected_v1_supported_callers": list(_SUPPORTED_CALLERS),
            "supported_caller_count": len(_SUPPORTED_CALLERS),
            "deferred_callers": deferred,
            "deferred_caller_count": len(deferred),
            "canonical_mask_semantic_names": list(_CANONICAL_MASK_SEMANTICS),
            "canonical_mask_count": len(_CANONICAL_MASK_SEMANTICS),
            "canonical_B2_semantic": "scaffold_plus_warhead",
            "canonical_B3_semantic": "scaffold_only",
            "sixth_mask_added": False,
            "failure_contract": failure_contract,
            "automatic_target_inference_sources": [],
            "C4_exact_path_scope": list(_C4_PATHS),
            "C4_exact_path_scope_count": len(_C4_PATHS),
            "C4_gate_implemented": True,
            "C4_gate_lifecycle_profile": lifecycle["profile"],
            "C4_gate_commit": lifecycle["commit"],
            "C4_gate_committed": lifecycle_claims["C4_gate_committed"],
            "C4_gate_published": lifecycle_claims["C4_gate_published"],
            "ready_for_C4_commit_review": lifecycle_claims[
                "ready_for_C4_commit_review"
            ],
            "repository_cli_selector_forwarding_complete": lifecycle_claims[
                "repository_cli_selector_forwarding_complete"
            ],
            "ready_for_repository_cli_runtime_smoke_planning": lifecycle_claims[
                "ready_for_repository_cli_runtime_smoke_planning"
            ],
            "recommended_next_step": lifecycle_claims["recommended_next_step"],
            "real_repository_cli_runtime_smoke_executed": False,
            "training_or_parameter_update": False,
            "RL_implementation_started": False,
            "feature_semantics_audit_required_before_training": True,
            "Step12D_smoke_is_not_final_training_feature_contract": True,
            "checkpoint_loaded_by_C4_gate": False,
            "model_forward_executed_by_C4_gate": False,
        }
        response = {
            field: values[field]
            for field in REPOSITORY_CLI_FORWARDING_GATE_RESPONSE_FIELDS
            if field != "repository_cli_forwarding_gate_response_sha256"
        }
        response["repository_cli_forwarding_gate_response_sha256"] = _sha256(
            _canonical_json_bytes(response)
        )
        _validate_response(response)
        return response
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)
