"""Bounded design for a future real repository CLI conditioned smoke V1.

This module is deliberately a design evaluator, not a smoke executor.  It
binds published predecessor evidence and freezes the future execution and
evidence contracts without importing the model, loading a checkpoint,
executing a caller, writing a fixture, or running generation.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence


__all__ = (
    "evaluate_covapie_bounded_repository_cli_conditioned_runtime_smoke_design_v1",
)


_ERROR = "COVAPIE_BOUNDED_REPOSITORY_CLI_CONDITIONED_RUNTIME_SMOKE_DESIGN_INVALID"
_VERSION = "covapie_bounded_repository_cli_conditioned_runtime_smoke_design_v1"
_MAX_SOURCE_BYTES = 8 * 1024 * 1024

_C4_COMMIT = "011b9558d4a59824e3ba51a0d896ec13100b2b1b"
_C4_PARENT = "bd36211b03792602f382c16badac61eed79c8f9c"
_C4_SUBJECT = "add CovaPIE target residue repository CLI forwarding gate C4 v1"
_C4_FILES = {
    "src/covalent_ext/covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1.py": (
        "62a5e13a58e4fa3d6e4dc007eaf2eb842434c3d9d3245b843d2fae83fbb58622"
    ),
    "tests/test_covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1.py": (
        "b4bb07af5345782a7c1c6d28546a4da75d04c3d8f00ae2e65e1a92282d2f08d1"
    ),
    "scripts/check_covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1.py": (
        "a33b4985f6151eee116cda97324482ce9b025698636f21d6ec57e13dd8e786a2"
    ),
    "docs/covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1_guide.md": (
        "4d6da36d0c027d06e2c5211d9d578205300800be3b0d5bf39136e50bfaae2974"
    ),
}
_C4_RESPONSE_FIELD_COUNT = 62
_C4_RESPONSE_SHA256 = (
    "b455fe78165cf13f8277a866e1bc8069c980f98080eb0026302c9047d1d8d224"
)
_C4_CHECKER_STDOUT_SHA256 = (
    "4526973c08805ac70442e24bdce29f256a5a48d94ab6e5f616ead3aa5a42c553"
)

_C1_COMMIT = "142e7f72b391ceed3bbecaf22846a08f56933ea5"
_C1_HELPER_PATH = (
    "src/covalent_ext/covapie_target_residue_atom_condition_repository_cli_v1.py"
)
_C1_HELPER_SHA256 = (
    "ff02657edd67d643bed4881b3c52df75cb950dffc45c19e5497b07dd65a52dfc"
)
_C1_APIS = (
    "add_covapie_target_residue_atom_condition_cli_arguments_v1",
    "resolve_covapie_target_residue_atom_condition_cli_args_v1",
    "load_covapie_target_residue_conditioned_model_from_checkpoint_v1",
)
_CHECKPOINT_PATH = "checkpoints/crossdocked_fullatom_cond.ckpt"
_CHECKPOINT_SIZE = 17_861_341
_CHECKPOINT_SHA256 = (
    "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
)

_C2_COMMIT = "7cdaf807241e3dc4331d5c0a05eb6a63dd4d5ec4"
_C2_PARENT = _C1_COMMIT
_C2_SUBJECT = "forward CovaPIE target residue selector through generate_ligands C2 v1"
_C2_PATH = "generate_ligands.py"
_C2_SHA256 = "0739a7c194ab7794227a57fa28e7f7aea93b2013750e1ce1b1cde5d37b45d9c0"
_C2_BLOB = "418a4efa20d76d415b9f3fbc07a5654593df47e8"

_RUNTIME_SOURCE_FILES = {
    "lightning_modules.py": {
        "sha256": "7431b5cf24d4f918df961eb97c75f2e296c8b3c523fb627063f3a6c2f08fc983",
        "git_blob": "d19f18ec2841a9a3163d099f4df451d97ce795d4",
    },
    "equivariant_diffusion/conditional_model.py": {
        "sha256": "a61dc44f376b3efc0365f558b09470f71b35dd2606c216f5abf0ba06d5a1b4a9",
        "git_blob": "4c4ffab13830506f7442c8ccb2e7cdad5bbcfae2",
    },
    "utils.py": {
        "sha256": "2d8fdc954f025e70717b992a1382d8a020eff9170af8e92c961e74759287793b",
        "git_blob": "75450035d1dcd28590d487b3c5c0eaff79fced8a",
    },
}
_RUNTIME_SOURCE_SNAPSHOT_COMMIT = _C4_COMMIT
_CURRENT_MAINLINE_PRIORITY = (
    "implement_and_execute_bounded_covapie_repository_cli_conditioned_runtime_smoke_v1"
)
_POST_SMOKE_MAINLINE_PRIORITY = (
    "audit_covapie_five_module_training_path_completion_gaps_v1"
)

_SELECTED_CALLER = "generate_ligands.py"
_DEFERRED_CALLERS = ("scripts/covalent_inpaint_demo.py",)
_CANONICAL_MASK_SEMANTICS = (
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
)
_EXACT6_SELECTOR = {
    "chain_id": "A",
    "residue_sequence_number": 1,
    "residue_insertion_code": " ",
    "residue_name": "CYS",
    "atom_name": "SG",
    "element": "S",
}

_PDB_TEXT = (
    "ATOM      1  N   CYS A   1       0.000   0.000   0.000  1.00  0.00           N\n"
    "ATOM      2  CA  CYS A   1       1.458   0.000   0.000  1.00  0.00           C\n"
    "ATOM      3  C   CYS A   1       1.958   1.430   0.000  1.00  0.00           C\n"
    "ATOM      4  O   CYS A   1       1.210   2.370   0.000  1.00  0.00           O\n"
    "ATOM      5  CB  CYS A   1       2.050  -0.780   1.180  1.00  0.00           C\n"
    "ATOM      6  SG  CYS A   1       3.780  -0.620   1.250  1.00  0.00           S\n"
    "TER       7      CYS A   1\n"
    "END\n"
)
_PDB_SHA256 = "ccad2ee5cd8cc2459003790d837bbdc68fede63cdb5ea575f433250048f302c3"

_CLI_ARGV = (
    "generate_ligands.py",
    _CHECKPOINT_PATH,
    "--pdbfile",
    "<TEMP>/input/minimal_cys_sg.pdb",
    "--resi_list",
    "A:1",
    "--outfile",
    "<TEMP>/output/generated.sdf",
    "--n_samples",
    "1",
    "--batch_size",
    "1",
    "--num_nodes_lig",
    "4",
    "--timesteps",
    "1",
    "--target_residue_atom_conditioning",
    "--target_chain_id",
    "A",
    "--target_residue_sequence_number",
    "1",
)
_EXCLUDED_CLI_OPTIONS = (
    "--ref_ligand",
    "--sanitize",
    "--relax",
    "--all_frags",
)
_CHILD_ENVIRONMENT = {
    "CUDA_VISIBLE_DEVICES": "",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONPATH": ".:src:scripts",
    "OMP_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
}
_RANDOM_SEEDS = {
    "random.seed": 0,
    "numpy.random.seed": 0,
    "torch.manual_seed": 0,
    "torch.set_num_threads": 1,
    "torch.set_num_interop_threads": {
        "value": 1,
        "only_if_supported_and_not_initialized": True,
    },
}
_RESOURCE_BOUNDS = {
    "device": "cpu",
    "cuda_available": False,
    "A100_used": False,
    "n_samples": 1,
    "batch_size": 1,
    "num_nodes_lig": 4,
    "timesteps": 1,
    "automatic_bound_expansion_allowed": False,
}
_OBSERVER_TARGETS = (
    "resolve_covapie_target_residue_atom_condition_cli_args_v1",
    "load_covapie_target_residue_conditioned_model_from_checkpoint_v1",
    "LigandPocketDDPM.load_from_checkpoint",
    "LigandPocketDDPM.prepare_pocket",
    "LigandPocketDDPM.generate_ligands",
)
_EVIDENCE_FIELDS = (
    "evidence_schema_version",
    "caller",
    "argv",
    "environment",
    "child_returncode",
    "resolved_device",
    "cuda_available",
    "stdout_byte_count",
    "stdout_sha256",
    "stderr_byte_count",
    "stderr_sha256",
    "resolver_call_count",
    "selector",
    "conditioned_loader_call_count",
    "legacy_loader_call_count",
    "checkpoint_path",
    "map_location",
    "model_target_residue_atom_conditioning",
    "dynamics_target_residue_atom_conditioning",
    "condition_embedding_shape",
    "condition_embedding_all_zero",
    "state_key_count",
    "prepare_pocket_call_count",
    "pocket_size",
    "indicator_field_present",
    "indicator_dtype",
    "indicator_shape",
    "indicator_true_count",
    "indicator_true_atom",
    "generate_ligands_call_count",
    "n_samples",
    "pocket_ids",
    "ref_ligand",
    "timesteps",
    "selector_object_is_resolver_output",
    "ddpm_type",
    "dynamics_forward_call_count",
    "model_forward_executed",
    "real_generation_path_executed",
    "training_step_executed",
    "backward_executed",
    "optimizer_created",
    "optimizer_step_executed",
    "scheduler_step_executed",
    "all_parameter_grads_none",
    "model_state_digest_before",
    "model_state_digest_after",
    "parameter_values_modified",
    "parameter_versions_modified",
    "checkpoint_size_before",
    "checkpoint_size_after",
    "checkpoint_mtime_ns_before",
    "checkpoint_mtime_ns_after",
    "checkpoint_sha256_before",
    "checkpoint_sha256_after",
    "checkpoint_bytes_unchanged",
    "forbidden_save_api_call_count",
    "generated_molecule_count",
    "output_sdf_exists",
    "output_sdf_regular",
    "output_sdf_symlink",
    "output_sdf_size",
    "output_sdf_record_count",
    "chemical_generation_quality_validated",
    "workspace_st_dev",
    "workspace_st_ino",
    "workspace_allowed_relative_paths",
)

BOUNDED_REPOSITORY_CLI_CONDITIONED_RUNTIME_SMOKE_DESIGN_RESPONSE_FIELDS = (
    "bounded_runtime_smoke_design_version",
    "bounded_runtime_smoke_design_error_contract",
    "bounded_runtime_smoke_design_complete",
    "bounded_runtime_smoke_implementation_deferred",
    "fresh_runtime_source_revalidation_required_before_implementation",
    "current_mainline_priority",
    "source_C4_commit_identity",
    "source_C4_file_identities",
    "C4_published_response_binding",
    "C4_published_checker_stdout_binding",
    "C4_published_bound",
    "repository_cli_selector_forwarding_complete",
    "selected_runtime_smoke_caller",
    "deferred_runtime_smoke_callers",
    "deferred_runtime_smoke_caller_count",
    "caller_scope_boundary",
    "source_C1_binding",
    "C1_public_apis",
    "real_checkpoint_binding",
    "source_C2_commit_identity",
    "source_C2_file_identity",
    "runtime_source_bindings",
    "C2_generate_ligands_ast_evidence",
    "C2_generate_ligands_bound",
    "canonical_mask_semantic_names",
    "canonical_mask_count",
    "temporary_PDB_contract",
    "Exact6_runtime_contract",
    "CLI_argv_contract",
    "CLI_argument_semantics",
    "child_environment_contract",
    "random_seed_contract",
    "resource_bounds",
    "subprocess_execution_contract",
    "transparent_observer_contract",
    "runtime_evidence_schema",
    "output_acceptance_contract",
    "parameter_immutability_contract",
    "checkpoint_immutability_contract",
    "temporary_workspace_contract",
    "timeout_contract",
    "real_runtime_smoke_executed",
    "model_forward_executed",
    "training_or_parameter_update",
    "RL_implementation_started",
    "feature_semantics_audit_required_before_training",
    "smoke_does_not_validate_feature_semantics",
    "ready_for_bounded_runtime_smoke_implementation",
    "recommended_next_step",
    "bounded_runtime_smoke_design_response_sha256",
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
        ):
            _raise_invalid()
        return parsed
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _read_regular_file(
    repo_root: Path,
    relative_path: str,
    *,
    expected_size: int | None = None,
    expected_sha256: str | None = None,
) -> tuple[bytes, os.stat_result]:
    try:
        parsed = _canonical_relative_path(relative_path)
        path = repo_root.joinpath(*parsed.parts)
        before = path.lstat()
        if (
            stat.S_ISLNK(before.st_mode)
            or not stat.S_ISREG(before.st_mode)
            or before.st_mode & 0o111
            or before.st_size <= 0
            or (expected_size is not None and before.st_size != expected_size)
            or (expected_size is None and before.st_size > _MAX_SOURCE_BYTES)
        ):
            _raise_invalid()
        payload = path.read_bytes()
        after = path.lstat()
        if (
            len(payload) != before.st_size
            or (before.st_dev, before.st_ino, before.st_size, before.st_mode)
            != (after.st_dev, after.st_ino, after.st_size, after.st_mode)
            or (expected_sha256 is not None and _sha256(payload) != expected_sha256)
        ):
            _raise_invalid()
        return payload, after
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


def _bind_commit(
    repo_root: Path,
    *,
    commit: str,
    parent: str,
    subject: str,
    files: Mapping[str, str],
    statuses: Mapping[str, str],
) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
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
            committed = _git_bytes(repo_root, ["show", f"{commit}:{relative_path}"])
            live, live_stat = _read_regular_file(
                repo_root, relative_path, expected_sha256=expected_sha256
            )
            if committed != live or _sha256(committed) != expected_sha256:
                _raise_invalid()
            identities[relative_path] = {
                "sha256": expected_sha256,
                "git_blob": match.group(1),
                "git_mode": "100644",
                "live_bytes_match_commit": True,
                "ordinary_regular": stat.S_ISREG(live_stat.st_mode),
                "symlink": False,
                "executable": bool(live_stat.st_mode & 0o111),
                "mode_stable_during_read": True,
            }
        if not _is_ancestor(repo_root, commit, "HEAD") or not _is_ancestor(
            repo_root, commit, "origin/main"
        ):
            _raise_invalid()
        return (
            {
                "commit": commit,
                "parent": parent,
                "subject": subject,
                "body_empty": True,
                "single_parent": True,
                "exact_path_scope": list(files),
                "exact_path_scope_count": len(files),
                "ancestor_of_HEAD": True,
                "ancestor_of_origin_main": True,
            },
            identities,
        )
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _runtime_source_snapshot_lifecycle_from_facts(
    facts: Mapping[str, object],
) -> dict[str, object]:
    try:
        required = {
            "snapshot_commit",
            "current_HEAD",
            "current_origin_main",
            "snapshot_is_ancestor_of_HEAD",
            "snapshot_is_ancestor_of_origin_main",
        }
        if type(facts) is not dict or set(facts) != required:
            _raise_invalid()
        snapshot = facts["snapshot_commit"]
        head = facts["current_HEAD"]
        origin = facts["current_origin_main"]
        head_ancestor = facts["snapshot_is_ancestor_of_HEAD"]
        origin_ancestor = facts["snapshot_is_ancestor_of_origin_main"]
        if (
            snapshot != _RUNTIME_SOURCE_SNAPSHOT_COMMIT
            or type(head) is not str
            or re.fullmatch(r"[0-9a-f]{40}", head) is None
            or type(origin) is not str
            or re.fullmatch(r"[0-9a-f]{40}", origin) is None
            or type(head_ancestor) is not bool
            or type(origin_ancestor) is not bool
            or head_ancestor is not True
            or origin_ancestor is not True
        ):
            _raise_invalid()
        return {
            "snapshot_commit": snapshot,
            "current_HEAD": head,
            "current_origin_main": origin,
            "snapshot_is_ancestor_of_HEAD": True,
            "snapshot_is_ancestor_of_origin_main": True,
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _runtime_source_file_identity_from_facts(
    facts: Mapping[str, object],
) -> dict[str, object]:
    try:
        required = {
            "relative_path",
            "snapshot_sha256",
            "snapshot_git_blob",
            "snapshot_git_mode",
            "live_sha256",
            "live_bytes_match_snapshot",
            "ordinary_regular",
            "symlink",
            "executable",
            "mode_stable_during_read",
        }
        if type(facts) is not dict or set(facts) != required:
            _raise_invalid()
        relative_path = facts["relative_path"]
        if type(relative_path) is not str or relative_path not in _RUNTIME_SOURCE_FILES:
            _raise_invalid()
        expected = _RUNTIME_SOURCE_FILES[relative_path]
        if (
            facts["snapshot_sha256"] != expected["sha256"]
            or facts["live_sha256"] != expected["sha256"]
            or facts["snapshot_git_blob"] != expected["git_blob"]
            or facts["snapshot_git_mode"] != "100644"
            or facts["live_bytes_match_snapshot"] is not True
            or facts["ordinary_regular"] is not True
            or facts["symlink"] is not False
            or facts["executable"] is not False
            or facts["mode_stable_during_read"] is not True
        ):
            _raise_invalid()
        return {
            "sha256": expected["sha256"],
            "git_blob": expected["git_blob"],
            "git_mode": "100644",
            "live_bytes_match_snapshot": True,
            "ordinary_regular": True,
            "symlink": False,
            "executable": False,
            "mode_stable_during_read": True,
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _bind_runtime_sources(repo_root: Path) -> dict[str, object]:
    try:
        current_head = _git_text(repo_root, ["rev-parse", "HEAD"]).strip()
        current_origin = _git_text(
            repo_root, ["rev-parse", "origin/main"]
        ).strip()
        lifecycle = _runtime_source_snapshot_lifecycle_from_facts(
            {
                "snapshot_commit": _RUNTIME_SOURCE_SNAPSHOT_COMMIT,
                "current_HEAD": current_head,
                "current_origin_main": current_origin,
                "snapshot_is_ancestor_of_HEAD": _is_ancestor(
                    repo_root, _RUNTIME_SOURCE_SNAPSHOT_COMMIT, current_head
                ),
                "snapshot_is_ancestor_of_origin_main": _is_ancestor(
                    repo_root, _RUNTIME_SOURCE_SNAPSHOT_COMMIT, current_origin
                ),
            }
        )
        files: dict[str, dict[str, object]] = {}
        for relative_path, expected in _RUNTIME_SOURCE_FILES.items():
            row = _git_text(
                repo_root,
                ["ls-tree", _RUNTIME_SOURCE_SNAPSHOT_COMMIT, "--", relative_path],
            )
            match = re.fullmatch(
                rf"([0-9]{{6}}) blob ([0-9a-f]{{40}})\t{re.escape(relative_path)}\n",
                row,
            )
            if match is None:
                _raise_invalid()
            snapshot_payload = _git_bytes(
                repo_root,
                ["show", f"{_RUNTIME_SOURCE_SNAPSHOT_COMMIT}:{relative_path}"],
            )
            live_payload, live_stat = _read_regular_file(
                repo_root,
                relative_path,
                expected_sha256=expected["sha256"],
            )
            files[relative_path] = _runtime_source_file_identity_from_facts(
                {
                    "relative_path": relative_path,
                    "snapshot_sha256": _sha256(snapshot_payload),
                    "snapshot_git_blob": match.group(2),
                    "snapshot_git_mode": match.group(1),
                    "live_sha256": _sha256(live_payload),
                    "live_bytes_match_snapshot": snapshot_payload == live_payload,
                    "ordinary_regular": stat.S_ISREG(live_stat.st_mode),
                    "symlink": stat.S_ISLNK(live_stat.st_mode),
                    "executable": bool(live_stat.st_mode & 0o111),
                    "mode_stable_during_read": True,
                }
            )
        return {
            **lifecycle,
            "files": files,
            "source_count": len(files),
            "all_live_bytes_match_snapshot": True,
            "all_ordinary_regular": True,
            "all_non_symlink": True,
            "all_non_executable": True,
            "all_modes_stable_during_read": True,
            "drift_requires_design_revalidation_before_implementation": True,
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
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


def _contains_call(nodes: Sequence[ast.stmt], name: str) -> int:
    return sum(len(_calls(node, name)) for node in nodes)


def _selector_none_branch(node: ast.If) -> bool:
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


def _c2_ast_evidence(payload: bytes) -> dict[str, object]:
    try:
        tree = ast.parse(payload.decode("utf-8", errors="strict"))
        helper_imports = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module
            == "covalent_ext.covapie_target_residue_atom_condition_repository_cli_v1"
        ]
        if (
            len(helper_imports) != 1
            or len(helper_imports[0].names) != len(_C1_APIS)
            or {alias.name for alias in helper_imports[0].names} != set(_C1_APIS)
            or any(alias.asname is not None for alias in helper_imports[0].names)
        ):
            _raise_invalid()
        names = {
            "parser_helper_call_count": (
                "add_covapie_target_residue_atom_condition_cli_arguments_v1"
            ),
            "parse_args_call_count": "parser.parse_args",
            "resolver_call_count": (
                "resolve_covapie_target_residue_atom_condition_cli_args_v1"
            ),
            "conditioned_loader_call_count": (
                "load_covapie_target_residue_conditioned_model_from_checkpoint_v1"
            ),
            "legacy_loader_call_count": "LigandPocketDDPM.load_from_checkpoint",
            "model_generate_ligands_call_count": "model.generate_ligands",
            "write_sdf_file_call_count": "utils.write_sdf_file",
        }
        counts = {field: len(_calls(tree, call_name)) for field, call_name in names.items()}
        if any(value != 1 for value in counts.values()):
            _raise_invalid()
        positions = {
            field: (_calls(tree, call_name)[0].lineno, _calls(tree, call_name)[0].col_offset)
            for field, call_name in names.items()
        }
        if not (
            positions["parser_helper_call_count"] < positions["parse_args_call_count"]
            < positions["resolver_call_count"]
            and positions["resolver_call_count"][0]
            < min(
                positions["legacy_loader_call_count"][0],
                positions["conditioned_loader_call_count"][0],
            )
            and max(
                positions["legacy_loader_call_count"][0],
                positions["conditioned_loader_call_count"][0],
            )
            < positions["model_generate_ligands_call_count"][0]
            < positions["write_sdf_file_call_count"][0]
        ):
            _raise_invalid()
        branches = [
            node for node in ast.walk(tree) if isinstance(node, ast.If) and _selector_none_branch(node)
        ]
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
            or any(isinstance(item, ast.Try) for item in ast.walk(branch))
        ):
            _raise_invalid()
        generation = _calls(tree, "model.generate_ligands")[0]
        selector_keywords = [
            keyword
            for keyword in generation.keywords
            if keyword.arg == "target_residue_atom_condition_spec"
        ]
        if (
            len(selector_keywords) != 1
            or not isinstance(selector_keywords[0].value, ast.Name)
            or selector_keywords[0].value.id != "target_residue_atom_condition_spec"
            or len(generation.args) < 4
            or _attribute_chain(generation.args[2]) != "args.resi_list"
            or _attribute_chain(generation.args[3]) != "args.ref_ligand"
        ):
            _raise_invalid()
        enclosing_loops = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.For) and generation in tuple(ast.walk(node))
        ]
        if len(enclosing_loops) != 1:
            _raise_invalid()
        evidence: dict[str, object] = {
            "C1_helper_import_statement_count": 1,
            "C1_helper_imported_names": list(_C1_APIS),
            "C1_helpers_each_imported_once": True,
            **counts,
            "selector_forwarding_keyword_count": 1,
            "selector_resolved_before_loader": True,
            "legacy_and_conditioned_branches_mutually_exclusive": True,
            "conditioned_loader_failure_has_no_legacy_fallback": True,
            "selector_forwarded_inside_only_batch_loop": True,
            "selector_forwarded_to_every_batch": True,
            "pocket_ids_argument_identity": "args.resi_list",
            "ref_ligand_argument_identity": "args.ref_ligand",
        }
        return evidence
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _pdb_contract() -> dict[str, object]:
    try:
        payload = _PDB_TEXT.encode("utf-8")
        lines = _PDB_TEXT.splitlines()
        if (
            _sha256(payload) != _PDB_SHA256
            or len(payload) != 505
            or not _PDB_TEXT.endswith("\n")
            or "\r" in _PDB_TEXT
            or len(lines) != 8
            or lines[-2:] != ["TER       7      CYS A   1", "END"]
        ):
            _raise_invalid()
        atoms: list[dict[str, object]] = []
        for line in lines[:6]:
            if len(line) != 78 or line[0:6] != "ATOM  ":
                _raise_invalid()
            atoms.append(
                {
                    "name": line[12:16].strip(),
                    "element": line[76:78].strip(),
                    "altloc": line[16],
                    "residue_name": line[17:20],
                    "chain_id": line[21],
                    "residue_sequence_number": int(line[22:26]),
                    "insertion_code": line[26],
                    "coordinates": [
                        float(line[30:38]),
                        float(line[38:46]),
                        float(line[46:54]),
                    ],
                }
            )
        expected_names = ["N", "CA", "C", "O", "CB", "SG"]
        expected_elements = ["N", "C", "C", "O", "C", "S"]
        expected_coordinates = [
            [0.000, 0.000, 0.000],
            [1.458, 0.000, 0.000],
            [1.958, 1.430, 0.000],
            [1.210, 2.370, 0.000],
            [2.050, -0.780, 1.180],
            [3.780, -0.620, 1.250],
        ]
        if (
            [atom["name"] for atom in atoms] != expected_names
            or [atom["element"] for atom in atoms] != expected_elements
            or [atom["coordinates"] for atom in atoms] != expected_coordinates
            or any(
                atom["altloc"] != " "
                or atom["residue_name"] != "CYS"
                or atom["chain_id"] != "A"
                or atom["residue_sequence_number"] != 1
                or atom["insertion_code"] != " "
                for atom in atoms
            )
        ):
            _raise_invalid()
        return {
            "relative_path": "input/minimal_cys_sg.pdb",
            "encoding": "utf-8",
            "line_ending": "LF",
            "terminal_newline": True,
            "pdb_text": _PDB_TEXT,
            "byte_count": len(payload),
            "sha256": _PDB_SHA256,
            "model_count": 1,
            "residue_count": 1,
            "atom_count": len(atoms),
            "SG_count": sum(atom["name"] == "SG" for atom in atoms),
            "atom_names": expected_names,
            "elements": expected_elements,
            "coordinates": expected_coordinates,
            "chain_id": "A",
            "residue_sequence_number": 1,
            "insertion_code": " ",
            "residue_name": "CYS",
            "target_atom_name": "SG",
            "target_element": "S",
            "altloc": " ",
            "TER_present": True,
            "END_present": True,
            "repository_file_created": False,
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def _validate_response(response: Mapping[str, Any]) -> bool:
    try:
        if (
            type(response) is not dict
            or tuple(response) != BOUNDED_REPOSITORY_CLI_CONDITIONED_RUNTIME_SMOKE_DESIGN_RESPONSE_FIELDS
            or len(response)
            != len(BOUNDED_REPOSITORY_CLI_CONDITIONED_RUNTIME_SMOKE_DESIGN_RESPONSE_FIELDS)
        ):
            _raise_invalid()
        unsigned = {
            field: response[field]
            for field in BOUNDED_REPOSITORY_CLI_CONDITIONED_RUNTIME_SMOKE_DESIGN_RESPONSE_FIELDS
            if field != "bounded_runtime_smoke_design_response_sha256"
        }
        if response["bounded_runtime_smoke_design_response_sha256"] != _sha256(
            _canonical_json_bytes(unsigned)
        ):
            _raise_invalid()
        runtime_sources = response["runtime_source_bindings"]
        observers = response["transparent_observer_contract"]
        forward_probe = observers.get("forward_probe") if type(observers) is dict else None
        evidence = response["runtime_evidence_schema"]
        if (
            response["bounded_runtime_smoke_design_version"] != _VERSION
            or response["bounded_runtime_smoke_design_error_contract"] != _ERROR
            or response["bounded_runtime_smoke_design_complete"] is not True
            or response["bounded_runtime_smoke_implementation_deferred"] is not False
            or response[
                "fresh_runtime_source_revalidation_required_before_implementation"
            ]
            is not True
            or response["current_mainline_priority"] != _CURRENT_MAINLINE_PRIORITY
            or response["C4_published_bound"] is not True
            or response["repository_cli_selector_forwarding_complete"] is not True
            or response["selected_runtime_smoke_caller"] != _SELECTED_CALLER
            or response["deferred_runtime_smoke_callers"] != list(_DEFERRED_CALLERS)
            or response["deferred_runtime_smoke_caller_count"] != 1
            or response["canonical_mask_semantic_names"]
            != list(_CANONICAL_MASK_SEMANTICS)
            or response["canonical_mask_count"] != 5
            or response["real_runtime_smoke_executed"] is not False
            or response["model_forward_executed"] is not False
            or response["training_or_parameter_update"] is not False
            or response["RL_implementation_started"] is not False
            or response["feature_semantics_audit_required_before_training"] is not True
            or response["smoke_does_not_validate_feature_semantics"] is not True
            or type(runtime_sources) is not dict
            or runtime_sources.get("snapshot_commit")
            != _RUNTIME_SOURCE_SNAPSHOT_COMMIT
            or type(runtime_sources.get("current_HEAD")) is not str
            or re.fullmatch(
                r"[0-9a-f]{40}", runtime_sources.get("current_HEAD", "")
            )
            is None
            or type(runtime_sources.get("current_origin_main")) is not str
            or re.fullmatch(
                r"[0-9a-f]{40}", runtime_sources.get("current_origin_main", "")
            )
            is None
            or runtime_sources.get("snapshot_is_ancestor_of_HEAD") is not True
            or runtime_sources.get("snapshot_is_ancestor_of_origin_main") is not True
            or runtime_sources.get("source_count") != 3
            or set(runtime_sources.get("files", {})) != set(_RUNTIME_SOURCE_FILES)
            or runtime_sources.get("all_live_bytes_match_snapshot") is not True
            or runtime_sources.get("all_ordinary_regular") is not True
            or runtime_sources.get("all_non_symlink") is not True
            or runtime_sources.get("all_non_executable") is not True
            or runtime_sources.get("all_modes_stable_during_read") is not True
            or type(forward_probe) is not dict
            or forward_probe.get("hook_target") != "model.ddpm.dynamics"
            or forward_probe.get("hook_API") != "register_forward_hook"
            or forward_probe.get("ddpm_type") != "ConditionalDDPM"
            or forward_probe.get("timesteps") != 1
            or forward_probe.get("expected_dynamics_forward_call_count") != 2
            or evidence.get("required_field_count") != 67
            or response["subprocess_execution_contract"].get(
                "one_time_execution_only"
            )
            is not True
            or response["subprocess_execution_contract"].get(
                "repeat_without_new_user_authorization"
            )
            is not False
            or response["subprocess_execution_contract"].get(
                "post_smoke_mainline_priority"
            )
            != _POST_SMOKE_MAINLINE_PRIORITY
            or response["subprocess_execution_contract"].get(
                "smoke_success_does_not_establish_training_readiness"
            )
            is not True
            or response["subprocess_execution_contract"].get(
                "smoke_failure_does_not_authorize_architecture_expansion"
            )
            is not True
            or response["ready_for_bounded_runtime_smoke_implementation"] is not True
            or response["recommended_next_step"] != _CURRENT_MAINLINE_PRIORITY
        ):
            _raise_invalid()
        _canonical_json_bytes(response)
        return True
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)


def evaluate_covapie_bounded_repository_cli_conditioned_runtime_smoke_design_v1(
    *,
    repo_root: Path,
) -> dict[str, object]:
    """Evaluate the bounded design without executing any real runtime path."""

    try:
        if (
            type(repo_root) is not type(Path())
            or not repo_root.is_absolute()
            or not repo_root.is_dir()
            or repo_root.is_symlink()
        ):
            _raise_invalid()

        c4_identity, c4_files = _bind_commit(
            repo_root,
            commit=_C4_COMMIT,
            parent=_C4_PARENT,
            subject=_C4_SUBJECT,
            files=_C4_FILES,
            statuses={path: "A" for path in _C4_FILES},
        )
        from covalent_ext import (
            covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1
            as c4,
        )

        c4_response = c4.evaluate_covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1(
            repo_root=repo_root
        )
        if (
            type(c4_response) is not dict
            or len(c4_response) != _C4_RESPONSE_FIELD_COUNT
            or tuple(c4_response) != c4.REPOSITORY_CLI_FORWARDING_GATE_RESPONSE_FIELDS
            or c4_response.get("C4_gate_lifecycle_profile") != "c4_published_successor"
            or c4_response.get("C4_gate_commit") != _C4_COMMIT
            or c4_response.get("C4_gate_committed") is not True
            or c4_response.get("C4_gate_published") is not True
            or c4_response.get("repository_cli_selector_forwarding_complete") is not True
            or c4_response.get("ready_for_repository_cli_runtime_smoke_planning") is not True
            or c4_response.get("repository_cli_forwarding_gate_response_sha256")
            != _C4_RESPONSE_SHA256
        ):
            _raise_invalid()

        c1_payload, c1_stat = _read_regular_file(
            repo_root,
            _C1_HELPER_PATH,
            expected_sha256=_C1_HELPER_SHA256,
        )
        c1_tree = ast.parse(c1_payload.decode("utf-8", errors="strict"))
        c1_exports = [
            node.value
            for node in c1_tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets)
        ]
        if len(c1_exports) != 1 or ast.literal_eval(c1_exports[0]) != _C1_APIS:
            _raise_invalid()

        checkpoint_payload, checkpoint_stat = _read_regular_file(
            repo_root,
            _CHECKPOINT_PATH,
            expected_size=_CHECKPOINT_SIZE,
            expected_sha256=_CHECKPOINT_SHA256,
        )
        if len(checkpoint_payload) != _CHECKPOINT_SIZE:
            _raise_invalid()
        del checkpoint_payload

        c2_identity, c2_files = _bind_commit(
            repo_root,
            commit=_C2_COMMIT,
            parent=_C2_PARENT,
            subject=_C2_SUBJECT,
            files={_C2_PATH: _C2_SHA256},
            statuses={_C2_PATH: "M"},
        )
        c2_file = c2_files[_C2_PATH]
        if c2_file["git_blob"] != _C2_BLOB:
            _raise_invalid()
        c2_payload, _ = _read_regular_file(
            repo_root, _C2_PATH, expected_sha256=_C2_SHA256
        )
        c2_ast = _c2_ast_evidence(c2_payload)
        runtime_sources = _bind_runtime_sources(repo_root)
        predecessor_c2_ast = c4_response.get("C2_generate_ligands_ast_evidence")
        if (
            type(predecessor_c2_ast) is not dict
            or predecessor_c2_ast.get("selector_forwarding_keyword_count") != 1
            or predecessor_c2_ast.get("required_execution_order_proven") is not True
            or predecessor_c2_ast.get("conditioned_loader_failure_has_no_fallback")
            is not True
            or predecessor_c2_ast.get("selector_forwarded_to_every_batch") is not True
        ):
            _raise_invalid()

        pdb_contract = _pdb_contract()
        values: dict[str, object] = {
            "bounded_runtime_smoke_design_version": _VERSION,
            "bounded_runtime_smoke_design_error_contract": _ERROR,
            "bounded_runtime_smoke_design_complete": True,
            "bounded_runtime_smoke_implementation_deferred": False,
            "fresh_runtime_source_revalidation_required_before_implementation": True,
            "current_mainline_priority": _CURRENT_MAINLINE_PRIORITY,
            "source_C4_commit_identity": c4_identity,
            "source_C4_file_identities": c4_files,
            "C4_published_response_binding": {
                "exact_field_count": _C4_RESPONSE_FIELD_COUNT,
                "response_sha256": _C4_RESPONSE_SHA256,
                "lifecycle_profile": "c4_published_successor",
                "gate_commit": _C4_COMMIT,
                "gate_committed": True,
                "gate_published": True,
                "ready_for_repository_cli_runtime_smoke_planning": True,
            },
            "C4_published_checker_stdout_binding": {
                "checker_path": "scripts/check_covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1.py",
                "stdout_sha256": _C4_CHECKER_STDOUT_SHA256,
                "returncode": 0,
                "stderr_empty": True,
            },
            "C4_published_bound": True,
            "repository_cli_selector_forwarding_complete": True,
            "selected_runtime_smoke_caller": _SELECTED_CALLER,
            "deferred_runtime_smoke_callers": list(_DEFERRED_CALLERS),
            "deferred_runtime_smoke_caller_count": len(_DEFERRED_CALLERS),
            "caller_scope_boundary": {
                "generate_ligands_only": True,
                "covalent_demo_runtime_smoke_deferred": True,
                "reason": (
                    "covalent_demo_requires_a_real_ligand_exact_five_mask_atom_groups_"
                    "and_an_inpainting_output_contract"
                ),
                "combine_callers_in_v1": False,
            },
            "source_C1_binding": {
                "commit": _C1_COMMIT,
                "helper_path": _C1_HELPER_PATH,
                "helper_sha256": _C1_HELPER_SHA256,
                "live_file_regular": True,
                "ordinary_regular": stat.S_ISREG(c1_stat.st_mode),
                "symlink": False,
                "executable": bool(c1_stat.st_mode & 0o111),
                "mode_stable_during_read": True,
                "checkpoint_loaded_by_design": False,
                "torch_model_imported_by_design": False,
            },
            "C1_public_apis": list(_C1_APIS),
            "real_checkpoint_binding": {
                "path": _CHECKPOINT_PATH,
                "size": checkpoint_stat.st_size,
                "sha256": _CHECKPOINT_SHA256,
                "regular_file": True,
                "ordinary_regular": stat.S_ISREG(checkpoint_stat.st_mode),
                "symlink": False,
                "executable": bool(checkpoint_stat.st_mode & 0o111),
                "mode_stable_during_read": True,
                "future_loader": _C1_APIS[2],
                "future_map_location": "cpu",
                "copy_allowed": False,
                "rewrite_allowed": False,
                "direct_migration_helper_allowed": False,
                "strict_false_allowed": False,
                "deserialized_by_design": False,
            },
            "source_C2_commit_identity": c2_identity,
            "source_C2_file_identity": c2_file,
            "runtime_source_bindings": runtime_sources,
            "C2_generate_ligands_ast_evidence": c2_ast,
            "C2_generate_ligands_bound": True,
            "canonical_mask_semantic_names": list(_CANONICAL_MASK_SEMANTICS),
            "canonical_mask_count": len(_CANONICAL_MASK_SEMANTICS),
            "temporary_PDB_contract": pdb_contract,
            "Exact6_runtime_contract": {
                "selector": dict(_EXACT6_SELECTOR),
                "selector_field_order": list(_EXACT6_SELECTOR),
                "unique_target_count": 1,
                "target": "CYS A 1 SG S",
                "target_inferred_from_reference_ligand": False,
                "target_inferred_from_distance": False,
            },
            "CLI_argv_contract": list(_CLI_ARGV),
            "CLI_argument_semantics": {
                "excluded_options": list(_EXCLUDED_CLI_OPTIONS),
                "pocket_ids": ["A:1"],
                "ref_ligand": None,
                "target_flags_supplied": 3,
                "target_from_explicit_C1_selector_only": True,
            },
            "child_environment_contract": dict(_CHILD_ENVIRONMENT),
            "random_seed_contract": dict(_RANDOM_SEEDS),
            "resource_bounds": dict(_RESOURCE_BOUNDS),
            "subprocess_execution_contract": {
                "dedicated_smoke_executor_required": True,
                "child_steps": [
                    "set_fixed_random_seeds",
                    "install_transparent_observers",
                    "set_sys_argv",
                    "runpy.run_path_generate_ligands_as_main",
                    "write_canonical_evidence_JSON_outside_repository",
                    "exit",
                ],
                "runpy_path": "generate_ligands.py",
                "runpy_run_name": "__main__",
                "working_directory": "repository_root",
                "torch_grad_enabled": False,
                "real_conditioned_loader": True,
                "real_generation": True,
                "mocks_used": False,
                "caller_main_executed_by_design": False,
                "one_time_execution_only": True,
                "repeat_without_new_user_authorization": False,
                "post_smoke_mainline_priority": _POST_SMOKE_MAINLINE_PRIORITY,
                "smoke_success_does_not_establish_training_readiness": True,
                "smoke_failure_does_not_authorize_architecture_expansion": True,
            },
            "transparent_observer_contract": {
                "wrapper_targets": list(_OBSERVER_TARGETS),
                "wrapper_target_count": len(_OBSERVER_TARGETS),
                "each_calls_original_exactly_once_per_observed_call": True,
                "arguments_modified": False,
                "return_values_modified": False,
                "model_replaced": False,
                "sampling_mocked": False,
                "PDB_mocked": False,
                "SDF_mocked": False,
                "selector_identity_recorded": True,
                "forward_probe": {
                    "hook_target": "model.ddpm.dynamics",
                    "hook_API": "register_forward_hook",
                    "ddpm_type": "ConditionalDDPM",
                    "timesteps": 1,
                    "expected_dynamics_forward_call_count": 2,
                    "callback_action": "increment_counter_only",
                    "callback_return_value": None,
                    "inputs_modified": False,
                    "output_modified": False,
                    "remove_in_finally": True,
                    "forbidden_hook_targets": [
                        "model",
                        "model.ddpm",
                        "LigandPocketDDPM",
                        "ConditionalDDPM",
                    ],
                    "forward_call_sources": [
                        "sample_p_zs_given_zt_reverse_denoising_step",
                        "sample_p_xh_given_z0_final_decode",
                    ],
                    "fail_closed_requires_exact_count": True,
                    "greater_than_zero_only_is_insufficient": True,
                    "model_forward_executed_required": True,
                },
                "forward_probe_modifies_output": False,
                "call_profile_records_training_backward_optimizer_scheduler_and_save_APIs": True,
                "observer_evidence_only": True,
            },
            "runtime_evidence_schema": {
                "canonical_JSON": {
                    "sort_keys": True,
                    "ensure_ascii": True,
                    "allow_nan": False,
                    "separators": [",", ":"],
                },
                "required_fields": list(_EVIDENCE_FIELDS),
                "required_field_count": len(_EVIDENCE_FIELDS),
                "evidence_relative_path": "evidence/runtime_smoke_evidence.json",
                "fail_closed_on_missing_or_extra_fields": True,
            },
            "output_acceptance_contract": {
                "generated_molecule_count_allowed": [0, 1],
                "chemical_generation_quality_is_acceptance_condition": False,
                "sanitize_success_required": False,
                "specific_SMILES_required": False,
                "specific_atom_types_required": False,
                "specific_geometry_required": False,
                "nonempty_SDF_record_required": False,
                "output_metadata_required": [
                    "output_sdf_exists",
                    "output_sdf_regular",
                    "output_sdf_symlink",
                    "output_sdf_size",
                    "output_sdf_record_count",
                ],
                "chemical_generation_quality_validated": False,
            },
            "parameter_immutability_contract": {
                "model_forward_allowed": True,
                "training_step_executed": False,
                "backward_executed": False,
                "optimizer_created": False,
                "optimizer_step_executed": False,
                "scheduler_step_executed": False,
                "all_parameter_grads_none": True,
                "state_dict_digest_before_equals_after": True,
                "parameter_values_modified": False,
                "parameter_versions_modified": False,
                "state_digest_includes_sorted_keys_dtypes_shapes_and_tensor_bytes": True,
            },
            "checkpoint_immutability_contract": {
                "bytes_unchanged": True,
                "size_unchanged": True,
                "mtime_ns_unchanged": True,
                "sha256_unchanged": True,
                "torch_save_called": False,
                "save_checkpoint_called": False,
                "state_dict_written_to_disk": False,
            },
            "temporary_workspace_contract": {
                "root_parent": "/tmp",
                "basename_pattern": (
                    "covapie_bounded_repository_cli_conditioned_runtime_smoke_v1_"
                    "<timestamp>_<random>"
                ),
                "must_not_exist_before_creation": True,
                "outside_repository": True,
                "record_st_dev_and_st_ino": True,
                "allowed_relative_paths": [
                    "input/minimal_cys_sg.pdb",
                    "output/generated.sdf",
                    "evidence/runtime_smoke_evidence.json",
                    "logs/stdout.bin",
                    "logs/stderr.bin",
                ],
                "logs_optional": True,
                "other_paths_allowed": False,
                "cleanup_on_success_failure_and_timeout": True,
                "cleanup_only_if_st_dev_and_st_ino_match": True,
                "cleanup_follows_symlinks": False,
                "competitor_path_deleted": False,
                "runtime_generated_repository_paths": [],
            },
            "timeout_contract": {
                "parent_timeout_seconds": 300,
                "timeout_fails_closed": True,
                "timeout_cleanup_required": True,
                "child_returncode_required": 0,
                "stderr_must_be_empty": True,
                "stdout_content_contract": None,
                "stdout_and_stderr_byte_counts_and_sha256_required": True,
            },
            "real_runtime_smoke_executed": False,
            "model_forward_executed": False,
            "training_or_parameter_update": False,
            "RL_implementation_started": False,
            "feature_semantics_audit_required_before_training": True,
            "smoke_does_not_validate_feature_semantics": True,
            "ready_for_bounded_runtime_smoke_implementation": True,
            "recommended_next_step": _CURRENT_MAINLINE_PRIORITY,
        }
        response = {
            field: values[field]
            for field in BOUNDED_REPOSITORY_CLI_CONDITIONED_RUNTIME_SMOKE_DESIGN_RESPONSE_FIELDS
            if field != "bounded_runtime_smoke_design_response_sha256"
        }
        response["bounded_runtime_smoke_design_response_sha256"] = _sha256(
            _canonical_json_bytes(response)
        )
        _validate_response(response)
        return response
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        _raise_invalid(error)
