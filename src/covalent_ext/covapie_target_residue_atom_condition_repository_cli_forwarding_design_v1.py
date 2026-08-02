"""Repository CLI forwarding design for target-residue conditioning V1.

This module audits the six repository callers and proves that the frozen base
checkpoint can be migrated, strictly and in memory, to the already implemented
conditioned model profile.  It does not implement CLI forwarding, write files,
run a model forward, or perform training/parameter updates.
"""

from __future__ import annotations

import ast
import contextlib
import hashlib
import io
import json
import os
import re
import stat
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any


__all__ = (
    "design_covapie_target_residue_atom_condition_repository_cli_forwarding_v1",
)


_ERROR = "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_REPOSITORY_CLI_FORWARDING_DESIGN_INVALID"
_VERSION = "covapie_target_residue_atom_condition_repository_cli_forwarding_design_v1"
_GATE_COMMIT = "dd085332c7e2cf58a6ca2e7d71cf022da010d4b4"
_GATE_PARENT = "2c504ff2eac0864c146129f4011d902fae5bef69"
_GATE_TREE = "b03de4940ca6fdce838bebc3b1e2a6f0f390f181"
_GATE_SUBJECT = "add CovaPIE target residue atom condition model consumption gate v1"
_IMPLEMENTATION_COMMIT = "2c504ff2eac0864c146129f4011d902fae5bef69"
_RUNTIME_BRIDGE_GATE_COMMIT = "148689cc0716a56f3eb991f762af0010c5849f3a"
_RUNTIME_DESIGN_BASELINE_COMMIT = (
    "f24d4bb1007986701d644c9ff3c94786b3872c21"
)
_RUNTIME_DESIGN_BASELINE_PARENT = "510b67d5882ef18c95251e93490bf4482b7682ee"
_RUNTIME_DESIGN_BASELINE_SUBJECT = (
    "fix CovaPIE repository CLI forwarding design commit lifecycle v1"
)
_BUNDLE_SIZE = 6449
_BUNDLE_TRANSPORT_SHA256 = "18edfbc312128315fd9c880e750aeccc41132b34c20c8e34d78a974e39a2c9aa"
_BUNDLE_INTERNAL_SHA256 = "0ef97cdafe946fefd240c95a94efc8b12be977c899db3b1df4a56a580b53d842"
_CHECKPOINT_SIZE = 17861341
_CHECKPOINT_SHA256 = "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
_CHECKPOINT_PATH = "checkpoints/crossdocked_fullatom_cond.ckpt"
_NEW_STATE_KEY = "ddpm.dynamics.target_residue_atom_condition_embedding"
_MAX_SOURCE_BYTES = 8 * 1024 * 1024
_MAX_CHECKPOINT_BYTES = 32 * 1024 * 1024

_GATE_FILES = {
    "src/covalent_ext/covapie_target_residue_atom_condition_model_consumption_gate_v1.py": "473da8ae62fef8eb8669edd8c553509926008767efea2dede60163146f539ee7",
    "tests/test_covapie_target_residue_atom_condition_model_consumption_gate_v1.py": "22323c59d74f3b58cc7f8235b910b9f0aca616734af35eed895633b9c5f188df",
    "scripts/check_covapie_target_residue_atom_condition_model_consumption_gate_v1.py": "72730cdf3e6cf2f2fc8ca22f0ad470f0744651153c539f95ce7a262ff32141ee",
    "docs/covapie_target_residue_atom_condition_model_consumption_gate_v1_guide.md": "45752804e529aea4724526b75631c75a57a85f7130239cb35057fe5f6559a6a2",
}
_CALLER_SHA256S = {
    "generate_ligands.py": "8884e63ddb7f0fa84bd89bfd956fbefa10db687fa0cfc3380b85d06837be4474",
    "test.py": "954e63ade5e8b8f811897e40b22d81308451054753327cd9de2942c658dfd7bf",
    "optimize.py": "d51c32b3902accf24698f2b3abdfdf0e1a5d3150b90515a1b8d1b13d3e7d229b",
    "inpaint.py": "2d6cf0542c4b82e25eed19165d6f90d004ae4ced1db426962e47fb6086e085d9",
    "scripts/covalent_inpaint_demo.py": "1866dde2a7909fb431617dfa9f7de5a297b895de7930313655685823944f72a9",
    "colab/DiffSBDD.ipynb": "0d7fdc6a8377aa41e8d2104c39b2120964eee7f02b21c2bb56ca415dc889a123",
}
_LIGHTNING_SHA256 = "7431b5cf24d4f918df961eb97c75f2e296c8b3c523fb627063f3a6c2f08fc983"
_MIGRATION_SHA256 = "0c47bdc136e41d16e62d87210333bb84e7295a57abd8ba9a377cf41d33ab76c8"
_MASKING_SHA256 = "48bfba93c95222da4d889a9e9e788826ca3577b9126aa9260e26e0e948bb59c5"
_COVALENT_DATASET_SHA256 = "2b2098f7fd2aeba20d20240f5bd7777a2c9ff210120f68aa3a61a7cf92bd992a"
_COVALENT_MASKING_CHECKER_SHA256 = "ff825f177469b94d54ac0c2524c1562ecf3fe1d24ff55847a267eb858af01142"
_HISTORICAL_B3_SOURCE_SHA256 = "e142d6aa7f64722f4e07391f80d7106c9a3b7cd4a7dcfed77b69231e209575d5"
_HISTORICAL_B3_CHECKER_SHA256 = "16fe45ec778ab4e50181eeaa03b1a0e1a79bea9cc4ce693f5d423c08f122548b"
_CURRENT_B3_TEST_SHA256 = "8becf069acbefcbb22889bb41435777fcb342e293ef9e94e95ed3a106d767501"
_NEGATIVE_LEGACY_TOKEN_TEST_SHA256 = "b6542c898dddf73f3fe4c307d373a46c47294d857dffb42f58abdc3e00c80309"

_SUPPORTED_CALLERS = (
    "generate_ligands.py",
    "scripts/covalent_inpaint_demo.py",
)
_DEFERRED_CALLERS = (
    "test.py",
    "optimize.py",
    "inpaint.py",
    "colab/DiffSBDD.ipynb",
)
CANONICAL_MASK_SEMANTIC_NAMES = (
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
)
_MASK_LONG_TO_INTERNAL = {
    "warhead_only": "A_warhead_only",
    "linker_plus_warhead": "B_linker_warhead",
    "scaffold_plus_warhead": "B2_scaffold_warhead",
    "scaffold_only": "B3_scaffold_only",
    "scaffold_plus_linker_plus_warhead": "C_scaffold_linker_warhead",
}
_MASK_LONG_TO_DISPLAY_ALIAS = {
    "warhead_only": "A",
    "linker_plus_warhead": "B",
    "scaffold_plus_warhead": "B2",
    "scaffold_only": "B3",
    "scaffold_plus_linker_plus_warhead": "C",
}
_LEGACY_MASK_SYMBOLS = (
    "build_four_level_mask",
    "MASK_BUILDERS",
    "MaskType",
    "mask_warhead",
    "mask_linker_and_warhead",
    "mask_scaffold",
    "mask_whole_ligand",
    "--mask_level",
)
_LEGACY_INTERNAL_LONG_FORM_NAMES = tuple(_MASK_LONG_TO_INTERNAL.values())
_LEGACY_SHORT_TOKENS = tuple(_MASK_LONG_TO_DISPLAY_ALIAS.values())
_DESIGN_PATHS = (
    "src/covalent_ext/covapie_target_residue_atom_condition_repository_cli_forwarding_design_v1.py",
    "tests/test_covapie_target_residue_atom_condition_repository_cli_forwarding_design_v1.py",
    "scripts/check_covapie_target_residue_atom_condition_repository_cli_forwarding_design_v1.py",
    "docs/covapie_target_residue_atom_condition_repository_cli_forwarding_design_v1_guide.md",
)
_KNOWN_FUTURE_TASK_NEW_PATHS = (
    "tests/test_covalent_inpaint_demo_mask_semantic_v1.py",
    "src/covalent_ext/covapie_legacy_four_level_mask_retirement_gate_v1.py",
    "tests/test_covapie_legacy_four_level_mask_retirement_gate_v1.py",
    "scripts/check_covapie_legacy_four_level_mask_retirement_gate_v1.py",
    "docs/covapie_legacy_four_level_mask_retirement_gate_v1_guide.md",
    "src/covalent_ext/covapie_target_residue_atom_condition_repository_cli_v1.py",
    "tests/test_covapie_target_residue_atom_condition_repository_cli_v1.py",
    "src/covalent_ext/covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1.py",
    "tests/test_covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1.py",
    "scripts/check_covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1.py",
    "docs/covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1_guide.md",
)
_ACTIVE_LEGACY_MASK_PATHS = {
    "src/covalent_ext/masking.py",
    "src/covalent_ext/schema.py",
    "src/covalent_ext/dataset.py",
    "scripts/covalent_inpaint_demo.py",
    "scripts/check_covalent_masking.py",
}
_CALL_NAMES = (
    "LigandPocketDDPM.load_from_checkpoint",
    "model.generate_ligands",
    "model.prepare_pocket",
    "model.ddpm.inpaint",
    "model.ddpm.diversify",
)
_EXPECTED_CALL_COUNTS = {
    "LigandPocketDDPM.load_from_checkpoint": 6,
    "model.generate_ligands": 3,
    "model.prepare_pocket": 3,
    "model.ddpm.inpaint": 3,
    "model.ddpm.diversify": 1,
}
_EXPECTED_HPARAMETER_KEYS = {
    "augment_noise",
    "augment_rotation",
    "auxiliary_loss",
    "batch_size",
    "clip_grad",
    "datadir",
    "dataset",
    "diffusion_params",
    "egnn_params",
    "eval_epochs",
    "eval_params",
    "loss_params",
    "lr",
    "mode",
    "node_histogram",
    "num_workers",
    "outdir",
    "pocket_representation",
    "virtual_nodes",
    "visualize_chain_epoch",
    "visualize_sample_epoch",
}

REPOSITORY_CLI_FORWARDING_DESIGN_RESPONSE_FIELDS = (
    "repository_cli_forwarding_design_version",
    "source_model_consumption_gate_bundle_transport_sha256",
    "source_model_consumption_gate_bundle_sha256",
    "source_model_consumption_gate_commit",
    "source_model_consumption_implementation_commit",
    "source_runtime_bridge_gate_commit",
    "source_generate_ligands_sha256",
    "source_test_sha256",
    "source_optimize_sha256",
    "source_inpaint_sha256",
    "source_covalent_inpaint_demo_sha256",
    "source_colab_notebook_sha256",
    "source_lightning_module_sha256",
    "source_checkpoint_migration_sha256",
    "audited_caller_count",
    "audited_checkpoint_load_site_count",
    "audited_model_generate_ligands_call_count",
    "audited_prepare_pocket_direct_call_count",
    "audited_ddpm_inpaint_direct_call_count",
    "audited_ddpm_diversify_direct_call_count",
    "selected_v1_supported_callers",
    "deferred_callers",
    "selected_cli_enable_flag",
    "selected_cli_chain_flag",
    "selected_cli_residue_sequence_number_flag",
    "selected_exact6_compilation_contract",
    "selected_legacy_mode_contract",
    "selected_conditioned_mode_contract",
    "selected_conditioned_checkpoint_load_strategy",
    "selected_checkpoint_migration_helper",
    "selected_generate_ligands_forwarding_contract",
    "selected_covalent_inpaint_forwarding_contract",
    "selected_mask_semantic_normalization_contract",
    "selected_test_manifest_deferral_contract",
    "selected_notebook_deferral_contract",
    "selected_failure_contract",
    "canonical_mask_semantic_names",
    "repository_cli_selector_forwarding_implemented",
    "ready_for_repository_cli_forwarding_implementation",
    "recommended_next_step",
    "training_or_parameter_update",
    "feature_semantics_audit_required_before_training",
    "repository_cli_forwarding_design_response_sha256",
)


class _DuplicateKeyError(ValueError):
    pass


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


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError(key)
        result[key] = value
    return result


def _strict_json(payload: bytes) -> dict[str, Any]:
    if (
        type(payload) is not bytes
        or not payload
        or len(payload) >= _MAX_SOURCE_BYTES
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\x00" in payload
        or payload.endswith((b"\n", b"\r"))
    ):
        raise ValueError(_ERROR)
    try:
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=lambda _value: (_ for _ in ()).throw(ValueError(_ERROR)),
        )
    except Exception as error:
        raise ValueError(_ERROR) from error
    if type(value) is not dict or _canonical_json_bytes(value) != payload:
        raise ValueError(_ERROR)
    return value


def _regular_file_bytes(
    repo_root: Path,
    relative_path: str,
    *,
    expected_sha256: str,
    expected_size: int | None = None,
    max_size: int = _MAX_SOURCE_BYTES,
) -> bytes:
    path = repo_root / relative_path
    metadata = path.lstat()
    if (
        not stat.S_ISREG(metadata.st_mode)
        or stat.S_ISLNK(metadata.st_mode)
        or metadata.st_size <= 0
        or metadata.st_size >= max_size
        or (expected_size is not None and metadata.st_size != expected_size)
    ):
        raise ValueError(_ERROR)
    payload = path.read_bytes()
    if len(payload) != metadata.st_size or _sha256(payload) != expected_sha256:
        raise ValueError(_ERROR)
    return payload


def _git_snapshot_blob_bytes(
    repo_root: Path,
    *,
    commit: str,
    relative_path: str,
    max_size: int = _MAX_SOURCE_BYTES,
) -> bytes:
    if (
        type(commit) is not str
        or re.fullmatch(r"[0-9a-f]{40}", commit) is None
        or type(relative_path) is not str
        or not relative_path
        or "\x00" in relative_path
        or Path(relative_path).is_absolute()
        or ".." in Path(relative_path).parts
        or type(max_size) is not int
        or type(max_size) is bool
        or max_size <= 1
    ):
        raise ValueError(_ERROR)
    object_spec = f"{commit}:{relative_path}"
    environment = {**os.environ, "LC_ALL": "C", "LANG": "C"}

    def run(*arguments: str) -> bytes:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=repo_root,
            env=environment,
            check=False,
            capture_output=True,
            timeout=30,
        )
        if completed.returncode != 0 or completed.stderr:
            raise ValueError(_ERROR)
        return completed.stdout

    object_type = run("cat-file", "-t", object_spec)
    if object_type != b"blob\n":
        raise ValueError(_ERROR)
    size_payload = run("cat-file", "-s", object_spec)
    try:
        size = int(size_payload.decode("ascii").strip())
    except (UnicodeDecodeError, ValueError) as error:
        raise ValueError(_ERROR) from error
    if size <= 0 or size >= max_size:
        raise ValueError(_ERROR)
    payload = run("show", object_spec)
    if len(payload) != size:
        raise ValueError(_ERROR)
    return payload


def _git_snapshot_file_bytes(
    repo_root: Path,
    *,
    commit: str,
    relative_path: str,
    expected_sha256: str,
    max_size: int = _MAX_SOURCE_BYTES,
) -> bytes:
    if (
        type(expected_sha256) is not str
        or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None
    ):
        raise ValueError(_ERROR)
    payload = _git_snapshot_blob_bytes(
        repo_root,
        commit=commit,
        relative_path=relative_path,
        max_size=max_size,
    )
    if _sha256(payload) != expected_sha256:
        raise ValueError(_ERROR)
    return payload


def _git(repo_root: Path, *args: str) -> str:
    environment = dict(os.environ)
    environment.update({"LC_ALL": "C", "LANG": "C"})
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if completed.returncode != 0 or completed.stderr:
        raise ValueError(_ERROR)
    return completed.stdout.rstrip("\n")


def _design_path_lifecycle_evidence(repo_root: Path) -> dict[str, Any]:
    tracked_paths = set(_git(repo_root, "ls-files").splitlines())
    ordinary_untracked_paths = set(
        _git(
            repo_root,
            "ls-files",
            "--others",
            "--exclude-standard",
        ).splitlines()
    )
    design_paths = set(_DESIGN_PATHS)
    tracked_design_paths = tracked_paths & design_paths
    untracked_design_paths = ordinary_untracked_paths & design_paths
    known_future_paths = set(_KNOWN_FUTURE_TASK_NEW_PATHS)
    known_future_untracked_paths = ordinary_untracked_paths & known_future_paths
    unknown_ordinary_untracked_paths = ordinary_untracked_paths - (
        design_paths | known_future_paths
    )
    design_paths_overlap = tracked_design_paths & untracked_design_paths

    for relative_path in sorted(design_paths | ordinary_untracked_paths):
        try:
            metadata = (repo_root / relative_path).lstat()
        except OSError as error:
            raise ValueError(_ERROR) from error
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise ValueError(_ERROR)

    precommit_untracked = (
        not tracked_design_paths
        and untracked_design_paths == design_paths
        and ordinary_untracked_paths == design_paths
        and not unknown_ordinary_untracked_paths
        and not design_paths_overlap
    )
    design_successor_worktree = (
        tracked_design_paths == design_paths
        and not untracked_design_paths
        and not ordinary_untracked_paths
        and not unknown_ordinary_untracked_paths
        and not design_paths_overlap
    )
    published_with_known_future_task = (
        tracked_design_paths == design_paths
        and not untracked_design_paths
        and bool(ordinary_untracked_paths)
        and ordinary_untracked_paths == known_future_untracked_paths
        and not unknown_ordinary_untracked_paths
        and not design_paths_overlap
    )
    profiles = {
        "initial_design_precommit": precommit_untracked,
        "design_successor_worktree": design_successor_worktree,
        "published_design_with_known_future_task": (
            published_with_known_future_task
        ),
    }
    if sum(profiles.values()) != 1:
        raise ValueError(_ERROR)
    profile = next(name for name, selected in profiles.items() if selected)
    return {
        "design_lifecycle_profile": profile,
        "tracked_paths": sorted(tracked_paths),
        "ordinary_untracked_paths": sorted(ordinary_untracked_paths),
        "tracked_design_paths": sorted(tracked_design_paths),
        "untracked_design_paths": sorted(untracked_design_paths),
        "known_future_task_new_paths": sorted(known_future_paths),
        "known_future_task_untracked_paths": sorted(
            known_future_untracked_paths
        ),
        "unknown_ordinary_untracked_paths": sorted(
            unknown_ordinary_untracked_paths
        ),
        "design_paths_all_tracked": tracked_design_paths == design_paths,
        "design_paths_all_untracked": untracked_design_paths == design_paths,
        "ordinary_untracked_count": len(ordinary_untracked_paths),
        "known_future_task_untracked_count": len(
            known_future_untracked_paths
        ),
        "unknown_ordinary_untracked_count": len(
            unknown_ordinary_untracked_paths
        ),
        "known_future_task_untracked_paths_supported": True,
        "unknown_untracked_paths_rejected": True,
        "lifecycle_valid": True,
    }


def _is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=repo_root,
        env={**os.environ, "LC_ALL": "C", "LANG": "C"},
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if completed.stdout or completed.stderr or completed.returncode not in (0, 1):
        raise ValueError(_ERROR)
    return completed.returncode == 0


def _runtime_design_baseline_source_evidence(
    repo_root: Path,
) -> dict[str, Any]:
    commit_lines = _git(
        repo_root,
        "show",
        "-s",
        "--format=%H%n%P%n%s",
        _RUNTIME_DESIGN_BASELINE_COMMIT,
    ).splitlines()
    if commit_lines != [
        _RUNTIME_DESIGN_BASELINE_COMMIT,
        _RUNTIME_DESIGN_BASELINE_PARENT,
        _RUNTIME_DESIGN_BASELINE_SUBJECT,
    ]:
        raise ValueError(_ERROR)
    evidence = {
        "runtime_design_baseline_commit": _RUNTIME_DESIGN_BASELINE_COMMIT,
        "runtime_design_baseline_parent": _RUNTIME_DESIGN_BASELINE_PARENT,
        "runtime_design_baseline_subject": _RUNTIME_DESIGN_BASELINE_SUBJECT,
        "runtime_design_baseline_commit_exists": True,
        "runtime_design_baseline_commit_single_parent": True,
        "runtime_design_baseline_commit_is_head_ancestor": _is_ancestor(
            repo_root, _RUNTIME_DESIGN_BASELINE_COMMIT, "HEAD"
        ),
        "runtime_design_baseline_commit_is_origin_main_ancestor": _is_ancestor(
            repo_root, _RUNTIME_DESIGN_BASELINE_COMMIT, "origin/main"
        ),
        "snapshot_network_access": False,
        "snapshot_working_tree_independent": True,
        "snapshot_index_independent": True,
        "snapshot_regular_blob_required": True,
        "snapshot_nonempty_required": True,
        "snapshot_size_bounded": True,
        "snapshot_sha256_bound": True,
    }
    if not all(
        evidence[name] is True
        for name in (
            "runtime_design_baseline_commit_exists",
            "runtime_design_baseline_commit_single_parent",
            "runtime_design_baseline_commit_is_head_ancestor",
            "runtime_design_baseline_commit_is_origin_main_ancestor",
            "snapshot_working_tree_independent",
            "snapshot_index_independent",
            "snapshot_regular_blob_required",
            "snapshot_nonempty_required",
            "snapshot_size_bounded",
            "snapshot_sha256_bound",
        )
    ):
        raise ValueError(_ERROR)
    return evidence


def _gate_source_evidence(repo_root: Path) -> dict[str, bool]:
    commit_lines = _git(
        repo_root,
        "show",
        "-s",
        "--format=%H%n%P%n%T%n%s",
        _GATE_COMMIT,
    ).splitlines()
    if commit_lines != [_GATE_COMMIT, _GATE_PARENT, _GATE_TREE, _GATE_SUBJECT]:
        raise ValueError(_ERROR)
    for relative_path, expected_sha256 in _GATE_FILES.items():
        _regular_file_bytes(
            repo_root,
            relative_path,
            expected_sha256=expected_sha256,
        )
    evidence = {
        "gate_commit_metadata_bound": True,
        "gate_four_file_identity_bound": True,
        "gate_commit_is_head_ancestor": _is_ancestor(repo_root, _GATE_COMMIT, "HEAD"),
        "gate_commit_is_origin_main_ancestor": _is_ancestor(
            repo_root, _GATE_COMMIT, "origin/main"
        ),
    }
    if not all(evidence.values()):
        raise ValueError(_ERROR)
    return evidence


def _validate_gate_bundle(payload: bytes) -> dict[str, Any]:
    if len(payload) != _BUNDLE_SIZE or _sha256(payload) != _BUNDLE_TRANSPORT_SHA256:
        raise ValueError(_ERROR)
    bundle = _strict_json(payload)
    digest_payload = dict(bundle)
    internal = digest_payload.pop("model_consumption_gate_response_sha256", None)
    if (
        len(bundle) != 43
        or internal != _BUNDLE_INTERNAL_SHA256
        or _sha256(_canonical_json_bytes(digest_payload)) != internal
        or bundle.get("model_consumption_gate_implemented") is not True
        or bundle.get("ready_for_repository_cli_forwarding_design") is not True
        or bundle.get("recommended_next_step")
        != "design_covapie_target_residue_atom_condition_repository_cli_forwarding_v1"
        or bundle.get("training_or_parameter_update") is not False
        or bundle.get("feature_semantics_audit_required_before_training") is not True
        or bundle.get("source_model_consumption_implementation_commit")
        != _IMPLEMENTATION_COMMIT
        or bundle.get("source_runtime_bridge_gate_commit")
        != _RUNTIME_BRIDGE_GATE_COMMIT
    ):
        raise ValueError(_ERROR)
    repository_contract = bundle.get("repository_cli_contract")
    if (
        type(repository_contract) is not dict
        or repository_contract.get("caller_count") != 6
        or repository_contract.get("caller_sha256s_bound") is not True
        or repository_contract.get("repository_cli_paths_unchanged") is not True
        or repository_contract.get("repository_cli_selector_forwarding_implemented")
        is not False
    ):
        raise ValueError(_ERROR)
    return bundle


def _attribute_chain(node: ast.expr) -> str | None:
    names: list[str] = []
    while isinstance(node, ast.Attribute):
        names.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    names.append(node.id)
    return ".".join(reversed(names))


def _call_counts(tree: ast.AST) -> dict[str, int]:
    counts = {name: 0 for name in _CALL_NAMES}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _attribute_chain(node.func)
        if name in counts:
            counts[name] += 1
    return counts


def _notebook_call_counts(payload: bytes) -> tuple[dict[str, int], int]:
    try:
        notebook = json.loads(
            payload.decode("utf-8"), object_pairs_hook=_unique_object
        )
    except Exception as error:
        raise ValueError(_ERROR) from error
    if type(notebook) is not dict or type(notebook.get("cells")) is not list:
        raise ValueError(_ERROR)
    total = {name: 0 for name in _CALL_NAMES}
    code_cell_count = 0
    for index, cell in enumerate(notebook["cells"]):
        if type(cell) is not dict or cell.get("cell_type") != "code":
            continue
        source = cell.get("source")
        if type(source) is not list or any(type(line) is not str for line in source):
            raise ValueError(_ERROR)
        sanitized = "\n".join(
            "pass" if line.lstrip().startswith(("%", "!")) else line
            for line in "".join(source).splitlines()
        )
        try:
            tree = ast.parse(
                sanitized, filename=f"colab/DiffSBDD.ipynb:cell[{index}]"
            )
        except SyntaxError as error:
            raise ValueError(_ERROR) from error
        for name, count in _call_counts(tree).items():
            total[name] += count
        code_cell_count += 1
    if code_cell_count != 8:
        raise ValueError(_ERROR)
    return total, code_cell_count


def _caller_audit(repo_root: Path) -> dict[str, Any]:
    by_caller: dict[str, dict[str, int]] = {}
    caller_payloads: dict[str, bytes] = {}
    for relative_path, expected_sha256 in _CALLER_SHA256S.items():
        caller_payloads[relative_path] = _git_snapshot_file_bytes(
            repo_root,
            commit=_RUNTIME_DESIGN_BASELINE_COMMIT,
            relative_path=relative_path,
            expected_sha256=expected_sha256,
        )
    for relative_path in tuple(_CALLER_SHA256S)[:-1]:
        try:
            tree = ast.parse(
                caller_payloads[relative_path].decode("utf-8"),
                filename=relative_path,
            )
        except (UnicodeDecodeError, SyntaxError) as error:
            raise ValueError(_ERROR) from error
        by_caller[relative_path] = _call_counts(tree)
    notebook_counts, code_cell_count = _notebook_call_counts(
        caller_payloads["colab/DiffSBDD.ipynb"]
    )
    by_caller["colab/DiffSBDD.ipynb"] = notebook_counts
    totals = {
        name: sum(per_caller[name] for per_caller in by_caller.values())
        for name in _CALL_NAMES
    }
    if totals != _EXPECTED_CALL_COUNTS:
        raise ValueError(_ERROR)

    notebook_text = caller_payloads["colab/DiffSBDD.ipynb"].decode("utf-8")
    if (
        "git clone https://github.com/arneschneuing/DiffSBDD.git" not in notebook_text
        or "moad_fullatom_cond.ckpt" not in notebook_text
        or "crossdocked_fullatom_cond.ckpt" in notebook_text
    ):
        raise ValueError(_ERROR)
    return {
        "evidence_mode": "frozen_runtime_baseline_snapshot",
        "runtime_design_baseline_commit": _RUNTIME_DESIGN_BASELINE_COMMIT,
        "by_caller": by_caller,
        "totals": totals,
        "notebook_code_cell_count": code_cell_count,
        "notebook_json_cell_source_audited": True,
        "notebook_distribution_mismatch_confirmed": True,
    }


def _find_class_method(tree: ast.Module, class_name: str, method_name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == method_name:
                    return child
    raise ValueError(_ERROR)


def _model_and_mask_source_audit(repo_root: Path) -> dict[str, bool]:
    lightning_payload = _git_snapshot_file_bytes(
        repo_root,
        commit=_RUNTIME_DESIGN_BASELINE_COMMIT,
        relative_path="lightning_modules.py",
        expected_sha256=_LIGHTNING_SHA256,
    )
    _git_snapshot_file_bytes(
        repo_root,
        commit=_RUNTIME_DESIGN_BASELINE_COMMIT,
        relative_path="src/covalent_ext/covapie_target_residue_atom_condition_checkpoint_migration_v1.py",
        expected_sha256=_MIGRATION_SHA256,
    )
    masking_payload = _git_snapshot_file_bytes(
        repo_root,
        commit=_RUNTIME_DESIGN_BASELINE_COMMIT,
        relative_path="src/covalent_ext/masking.py",
        expected_sha256=_MASKING_SHA256,
    )
    try:
        lightning_tree = ast.parse(lightning_payload.decode("utf-8"))
        masking_tree = ast.parse(masking_payload.decode("utf-8"))
    except (UnicodeDecodeError, SyntaxError) as error:
        raise ValueError(_ERROR) from error
    generate = _find_class_method(lightning_tree, "LigandPocketDDPM", "generate_ligands")
    prepare = _find_class_method(lightning_tree, "LigandPocketDDPM", "prepare_pocket")
    generate_args = [argument.arg for argument in generate.args.args]
    prepare_args = [argument.arg for argument in prepare.args.args]
    generate_prepare_calls = [
        node
        for node in ast.walk(generate)
        if isinstance(node, ast.Call)
        and _attribute_chain(node.func) == "self.prepare_pocket"
    ]
    generate_forwarded = (
        len(generate_prepare_calls) == 1
        and any(
            keyword.arg == "target_residue_atom_condition_spec"
            for keyword in generate_prepare_calls[0].keywords
        )
    )
    long_form_functions = {
        node.name
        for node in masking_tree.body
        if isinstance(node, ast.FunctionDef)
    }
    evidence = {
        "baseline_snapshot_bound": True,
        "generate_ligands_selector_parameter_present": (
            "target_residue_atom_condition_spec" in generate_args
        ),
        "generate_ligands_forwards_selector_to_prepare_pocket": generate_forwarded,
        "prepare_pocket_selector_parameter_present": (
            "target_residue_atom_condition_spec" in prepare_args
        ),
        "prepare_pocket_builds_indicator": (
            "pocket_target_residue_atom_condition_indicator"
            in lightning_payload.decode("utf-8")
        ),
        "build_long_form_mask_present": "build_long_form_mask" in long_form_functions,
        "build_four_level_mask_present_only_as_legacy": (
            "build_four_level_mask" in long_form_functions
        ),
        "canonical_mask_count_five": len(CANONICAL_MASK_SEMANTIC_NAMES) == 5,
        "scaffold_only_present": "scaffold_only" in CANONICAL_MASK_SEMANTIC_NAMES,
    }
    if not all(evidence.values()):
        raise ValueError(_ERROR)
    return evidence


def _python_reference_kinds(tree: ast.AST, symbol: str) -> set[str]:
    kinds: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if any(alias.name == symbol for alias in node.names):
                kinds.add("python_import")
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name == symbol:
                kinds.add("python_definition")
        if isinstance(node, ast.Name) and node.id == symbol:
            kinds.add("python_name")
        if isinstance(node, ast.Attribute) and node.attr == symbol:
            kinds.add("python_attribute")
        if isinstance(node, ast.Call):
            called = _attribute_chain(node.func)
            if called is not None and called.split(".")[-1] == symbol:
                kinds.add("python_call")
            if symbol == "--mask_level" and node.args:
                first = node.args[0]
                if isinstance(first, ast.Constant) and first.value == symbol:
                    kinds.add("cli_option_definition")
    return kinds


def _has_exact_legacy_choice_set(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if keyword.arg != "choices" or not isinstance(
                keyword.value, (ast.List, ast.Tuple, ast.Set)
            ):
                continue
            values = [
                element.value
                for element in keyword.value.elts
                if isinstance(element, ast.Constant)
                and type(element.value) is str
            ]
            if len(values) == 4 and set(values) == {"A", "B", "B2", "C"}:
                return True
    return False


def _import_count(tree: ast.AST, *, module: str, symbol: str) -> int:
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.module == module
        for alias in node.names
        if alias.name == symbol
    )


def _call_count(tree: ast.AST, symbol: str) -> int:
    return sum(
        1
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and _attribute_chain(node.func) is not None
        and _attribute_chain(node.func).split(".")[-1] == symbol
    )


def _function_string_constants(tree: ast.AST, function_name: str) -> set[str]:
    functions = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == function_name
    ]
    if len(functions) != 1:
        raise ValueError(_ERROR)
    return {
        node.value
        for node in ast.walk(functions[0])
        if isinstance(node, ast.Constant) and type(node.value) is str
    }


def _retirement_dependency_order_evidence(repo_root: Path) -> dict[str, Any]:
    """Prove from source and step scopes that consumers move before providers."""

    paths = {
        "provider": "src/covalent_ext/masking.py",
        "demo": "scripts/covalent_inpaint_demo.py",
        "dataset": "src/covalent_ext/dataset.py",
        "checker": "scripts/check_covalent_masking.py",
    }
    trees: dict[str, ast.Module] = {}
    expected_sha256s = {
        "provider": _MASKING_SHA256,
        "demo": _CALLER_SHA256S["scripts/covalent_inpaint_demo.py"],
        "dataset": _COVALENT_DATASET_SHA256,
        "checker": _COVALENT_MASKING_CHECKER_SHA256,
    }
    for name, relative_path in paths.items():
        payload = _git_snapshot_file_bytes(
            repo_root,
            commit=_RUNTIME_DESIGN_BASELINE_COMMIT,
            relative_path=relative_path,
            expected_sha256=expected_sha256s[name],
        )
        try:
            trees[name] = ast.parse(payload.decode("utf-8"), filename=relative_path)
        except (UnicodeDecodeError, SyntaxError) as error:
            raise ValueError(_ERROR) from error

    provider_symbols = {
        node.name
        for node in trees["provider"].body
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    }
    provider_symbols.update(
        target.id
        for node in trees["provider"].body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (
            node.targets if isinstance(node, ast.Assign) else [node.target]
        )
        if isinstance(target, ast.Name)
    )
    required_provider_symbols = set(_LEGACY_MASK_SYMBOLS[:-1]) - {"MaskType"}
    provider_symbols_present = required_provider_symbols.issubset(provider_symbols)

    provider_symbol = _LEGACY_MASK_SYMBOLS[0]
    demo_import_count = _import_count(
        trees["demo"], module="covalent_ext.masking", symbol=provider_symbol
    )
    demo_call_count = _call_count(trees["demo"], provider_symbol)
    dataset_import_count = _import_count(
        trees["dataset"], module="covalent_ext.masking", symbol=provider_symbol
    )
    dataset_call_count = _call_count(trees["dataset"], provider_symbol)
    dataset_mask_type_import_count = _import_count(
        trees["dataset"], module="covalent_ext.schema", symbol="MaskType"
    )
    checker_registry_import_count = _import_count(
        trees["checker"], module="covalent_ext.masking", symbol="MASK_BUILDERS"
    )
    legacy_choice_set = {"A", "B", "B2", "C"}
    demo_choices_present = _has_exact_legacy_choice_set(trees["demo"])
    demo_mask_level_present = bool(
        _python_reference_kinds(trees["demo"], _LEGACY_MASK_SYMBOLS[-1])
        & {"cli_option_definition"}
    )
    dataset_choices = _function_string_constants(
        trees["dataset"], "build_all_masks"
    )
    checker_constants = {
        node.value
        for node in ast.walk(trees["checker"])
        if isinstance(node, ast.Constant) and type(node.value) is str
    }
    dataset_uses_legacy_choices = legacy_choice_set.issubset(dataset_choices)
    checker_iterates_legacy_choices = legacy_choice_set.issubset(
        checker_constants
    )

    active_consumer_paths = sorted(
        path
        for path, active in {
            paths["demo"]: demo_import_count > 0 and demo_call_count > 0,
            paths["dataset"]: (
                dataset_import_count > 0
                and dataset_call_count > 0
                and dataset_mask_type_import_count > 0
                and dataset_uses_legacy_choices
            ),
            paths["checker"]: (
                checker_registry_import_count > 0
                and checker_iterates_legacy_choices
            ),
        }.items()
        if active
    )
    expected_active_consumers = sorted(
        [paths["demo"], paths["dataset"], paths["checker"]]
    )
    legacy_provider_has_active_consumers = (
        provider_symbols_present
        and active_consumer_paths == expected_active_consumers
    )

    scope = _future_retirement_implementation_scope()
    steps = scope["ordered_steps"]
    step_positions = {step["step"]: index for index, step in enumerate(steps)}
    r1 = steps[step_positions["R1"]]
    r2 = steps[step_positions["R2"]]
    r1_paths = set(r1["paths"])
    r2_paths = set(r2["paths"])
    consumer_migration_step = "R1"
    provider_removal_step = "R2"
    consumer_migration_precedes_provider_removal = (
        step_positions[consumer_migration_step]
        < step_positions[provider_removal_step]
    )
    r1_contract = r1["completion_contract"]
    r2_contract = r2["completion_contract"]
    r1_migrates_demo_and_keeps_provider = (
        paths["demo"] in r1_paths
        and paths["provider"] not in r1_paths
        and r1_contract.get("legacy_four_level_demo_consumer_removed") is True
        and r1_contract.get("legacy_four_level_core_provider_still_present")
        is True
    )
    r2_removes_provider_and_migrates_remaining_consumers = (
        {paths["provider"], paths["dataset"], paths["checker"]}
        .issubset(r2_paths)
        and r2_contract.get("legacy_core_provider_removed") is True
        and r2_contract.get("remaining_core_consumers_migrated") is True
    )
    no_intermediate_missing_import_state = all(
        (
            consumer_migration_precedes_provider_removal,
            r1_migrates_demo_and_keeps_provider,
            r2_removes_provider_and_migrates_remaining_consumers,
        )
    )
    historical_boundary_files = {
        "historical_B3_source_sha256_bound": (
            "src/covalent_ext/b3_scaffold_only_mask_implementation.py",
            _HISTORICAL_B3_SOURCE_SHA256,
        ),
        "historical_B3_checker_sha256_bound": (
            "scripts/check_b3_scaffold_only_mask_implementation_v0.py",
            _HISTORICAL_B3_CHECKER_SHA256,
        ),
        "current_B3_test_sha256_bound": (
            "tests/test_b3_scaffold_only_mask_implementation_v0.py",
            _CURRENT_B3_TEST_SHA256,
        ),
        "negative_legacy_token_test_sha256_bound": (
            "tests/test_real_covalent_feature_mapping_loader_gate_v0.py",
            _NEGATIVE_LEGACY_TOKEN_TEST_SHA256,
        ),
    }
    historical_boundary_evidence = {}
    for evidence_name, (relative_path, expected_sha256) in (
        historical_boundary_files.items()
    ):
        _git_snapshot_file_bytes(
            repo_root,
            commit=_RUNTIME_DESIGN_BASELINE_COMMIT,
            relative_path=relative_path,
            expected_sha256=expected_sha256,
        )
        historical_boundary_evidence[evidence_name] = True
    return {
        "evidence_mode": "frozen_runtime_baseline_snapshot",
        "runtime_design_baseline_commit": _RUNTIME_DESIGN_BASELINE_COMMIT,
        "legacy_provider_path": paths["provider"],
        "active_consumer_paths": active_consumer_paths,
        "provider_symbol": provider_symbol,
        "provider_symbols_present": provider_symbols_present,
        "consumer_import_count": demo_import_count + dataset_import_count,
        "consumer_call_count": demo_call_count + dataset_call_count,
        "legacy_provider_has_active_consumers": (
            legacy_provider_has_active_consumers
        ),
        "provider_removal_before_consumer_migration_safe": (
            not legacy_provider_has_active_consumers
        ),
        "legacy_demo_imports_four_level_builder": demo_import_count == 1,
        "legacy_demo_calls_four_level_builder": demo_call_count == 1,
        "legacy_demo_mask_level_flag_present": demo_mask_level_present,
        "legacy_demo_exact_A_B_B2_C_choices_present": demo_choices_present,
        "dataset_imports_four_level_builder": dataset_import_count == 1,
        "dataset_imports_MaskType": dataset_mask_type_import_count == 1,
        "dataset_build_all_masks_uses_A_B_B2_C": dataset_uses_legacy_choices,
        "checker_imports_MASK_BUILDERS": checker_registry_import_count == 1,
        "checker_iterates_A_B_B2_C": checker_iterates_legacy_choices,
        "consumer_migration_step": consumer_migration_step,
        "provider_removal_step": provider_removal_step,
        "consumer_migration_precedes_provider_removal": (
            consumer_migration_precedes_provider_removal
        ),
        "provider_removal_precedes_consumer_migration": (
            step_positions[provider_removal_step]
            < step_positions[consumer_migration_step]
        ),
        "R1_migrates_demo_and_keeps_provider": (
            r1_migrates_demo_and_keeps_provider
        ),
        "R2_removes_provider_and_migrates_remaining_consumers": (
            r2_removes_provider_and_migrates_remaining_consumers
        ),
        "no_intermediate_missing_import_state": (
            no_intermediate_missing_import_state
        ),
        **historical_boundary_evidence,
    }


def _text_has_symbol(text: str, symbol: str) -> bool:
    if symbol.startswith("--"):
        return symbol in text
    return re.search(
        rf"(?<![A-Za-z0-9_]){re.escape(symbol)}(?![A-Za-z0-9_])",
        text,
    ) is not None


def _legacy_reference_classification(
    relative_path: str,
) -> tuple[bool, bool, bool, bool, str]:
    active_actions = {
        "src/covalent_ext/masking.py": (
            "remove_legacy_builder_registry_and_wrappers_retain_build_long_form_mask"
        ),
        "src/covalent_ext/schema.py": (
            "replace_MaskType_with_canonical_long_semantic_schema"
        ),
        "src/covalent_ext/dataset.py": (
            "migrate_dataset_mask_api_and_keys_to_canonical_long_semantics"
        ),
        "scripts/covalent_inpaint_demo.py": (
            "replace_mask_level_and_four_level_builder_with_mask_semantic_and_long_form_builder"
        ),
        "scripts/check_covalent_masking.py": (
            "migrate_checker_to_canonical_five_level_runtime_contract"
        ),
    }
    if relative_path in active_actions:
        return True, False, False, False, active_actions[relative_path]
    if relative_path.startswith("tests/"):
        if relative_path == "tests/test_real_covalent_feature_mapping_loader_gate_v0.py":
            action = "retain_negative_legacy_token_evidence"
        else:
            action = (
                "migrate_legacy_runtime_expectation_to_retirement_and_canonical_semantics"
            )
        return False, True, False, False, action
    if relative_path.startswith("docs/"):
        return False, False, True, False, "retain_read_only_or_retirement_documentation"
    if relative_path.startswith("data/derived/"):
        return False, False, False, True, "preserve_read_only_historical_evidence"
    if (
        relative_path.startswith("src/covalent_ext/b3_scaffold_only_mask_")
        or (
            relative_path.startswith("scripts/")
            and Path(relative_path).stem.endswith("_v0")
        )
    ):
        return False, False, False, True, "preserve_read_only_historical_evidence"
    if relative_path in {_DESIGN_PATHS[0], _DESIGN_PATHS[2]}:
        return False, False, False, False, "retain_design_inventory_evidence"
    return True, False, False, False, "UNRESOLVED_ACTIVE_LEGACY_REFERENCE"


def _future_retirement_implementation_scope() -> dict[str, Any]:
    ordered_steps = [
        {
            "step": "R1",
            "task_name": (
                "implement_covapie_covalent_demo_canonical_five_level_mask_migration_r1_v1"
            ),
            "phase": "legacy_four_level_mask_retirement",
            "objective": (
                "migrate_active_covalent_demo_mask_consumer_to_canonical_five_level_semantics"
            ),
            "paths": [
                "scripts/covalent_inpaint_demo.py",
                "tests/test_covalent_inpaint_demo_mask_semantic_v1.py",
            ],
            "forbidden_paths": [
                "src/covalent_ext/masking.py",
                "src/covalent_ext/schema.py",
                "src/covalent_ext/dataset.py",
                "scripts/check_covalent_masking.py",
            ],
            "mask_surface_contract": {
                "legacy_builder_import_removed": _LEGACY_MASK_SYMBOLS[0],
                "canonical_builder_import_added": "build_long_form_mask",
                "legacy_mask_flag_removed": _LEGACY_MASK_SYMBOLS[-1],
                "only_canonical_mask_flag_added": "--mask_semantic",
                "accepted_runtime_mask_inputs": list(
                    CANONICAL_MASK_SEMANTIC_NAMES
                ),
                "canonical_to_internal_mapping": dict(_MASK_LONG_TO_INTERNAL),
                "short_alias_runtime_inputs_rejected": list(
                    _LEGACY_SHORT_TOKENS
                ),
                "legacy_internal_long_form_inputs_rejected": list(
                    _LEGACY_INTERNAL_LONG_FORM_NAMES
                ),
                "unknown_empty_or_non_string_mask_rejected": True,
                "target_residue_cli_arguments_added": False,
                "checkpoint_loader_modified": False,
                "model_forward_executed": False,
            },
            "completion_contract": {
                "covalent_demo_canonical_mask_surface_migrated": True,
                "legacy_four_level_demo_consumer_removed": True,
                "legacy_four_level_core_provider_still_present": True,
                "legacy_four_level_core_api_retired": False,
                "legacy_four_level_full_runtime_retired": False,
                "R2_still_required": True,
                "R3_gate_still_required": True,
            },
        },
        {
            "step": "R2",
            "task_name": (
                "implement_covapie_legacy_four_level_core_api_retirement_r2_v1"
            ),
            "phase": "legacy_four_level_mask_retirement",
            "objective": (
                "remove_legacy_core_provider_schema_dataset_checker_interfaces_and_migrate_positive_tests"
            ),
            "paths": [
                "src/covalent_ext/masking.py",
                "src/covalent_ext/schema.py",
                "src/covalent_ext/dataset.py",
                "scripts/check_covalent_masking.py",
                "tests/test_covalent_masking.py",
                "tests/test_b3_scaffold_only_mask_implementation_v0.py",
            ],
            "legacy_core_symbols_removed": list(_LEGACY_MASK_SYMBOLS[:-1]),
            "canonical_core_symbols_retained": [
                "LongFormMaskLevel",
                "LONG_FORM_MASK_COMPONENTS",
                "build_long_form_mask",
            ],
            "canonical_core_migration_contract": {
                "schema_accepts_legacy_short_tokens": False,
                "dataset_API_uses_canonical_long_semantic_names": True,
                "dataset_build_all_masks_exactly_five": True,
                "dataset_build_all_masks_semantics": list(
                    CANONICAL_MASK_SEMANTIC_NAMES
                ),
                "checker_validates_canonical_five_level_contract": True,
                "current_tests_require_positive_legacy_behavior": False,
            },
            "historical_B3_boundary": {
                "source_path": (
                    "src/covalent_ext/b3_scaffold_only_mask_implementation.py"
                ),
                "source_modified": False,
                "source_sha256": _HISTORICAL_B3_SOURCE_SHA256,
                "source_read_only": True,
                "source_active_runtime": False,
                "source_current_runtime_importable_required": False,
                "historical_checker_modified_or_run": False,
                "historical_checker_sha256": _HISTORICAL_B3_CHECKER_SHA256,
                "test_path": (
                    "tests/test_b3_scaffold_only_mask_implementation_v0.py"
                ),
                "current_test_sha256": _CURRENT_B3_TEST_SHA256,
                "test_imports_historical_module_after_R2": False,
                "test_runs_historical_checker_after_R2": False,
                "test_requires_positive_legacy_behavior_after_R2": False,
                "test_preserves_history_by_read_only_bytes_or_sha": True,
                "test_independently_checks_canonical_B2_and_B3": True,
            },
            "negative_legacy_token_evidence_boundary": {
                "path": (
                    "tests/test_real_covalent_feature_mapping_loader_gate_v0.py"
                ),
                "current_sha256": _NEGATIVE_LEGACY_TOKEN_TEST_SHA256,
                "modified_in_R1": False,
                "modified_in_R2": False,
                "retirement_increment": None,
                "required_future_action": (
                    "retain_negative_legacy_token_evidence"
                ),
                "active_runtime": False,
                "positive_legacy_behavior_required": False,
                "negative_legacy_token_rejection_evidence_retained": True,
            },
            "completion_contract": {
                "legacy_core_provider_removed": True,
                "remaining_core_consumers_migrated": True,
                "candidate_active_legacy_reference_count": 0,
                "legacy_four_level_full_runtime_retirement_candidate": True,
                "legacy_four_level_full_runtime_retired": False,
                "R3_independent_gate_required": True,
            },
        },
        {
            "step": "R3",
            "phase": "legacy_four_level_mask_retirement",
            "objective": "formal_zero_active_legacy_reference_retirement_gate",
            "paths": [
                "src/covalent_ext/covapie_legacy_four_level_mask_retirement_gate_v1.py",
                "tests/test_covapie_legacy_four_level_mask_retirement_gate_v1.py",
                "scripts/check_covapie_legacy_four_level_mask_retirement_gate_v1.py",
                "docs/covapie_legacy_four_level_mask_retirement_gate_v1_guide.md",
            ],
        },
        {
            "step": "C1",
            "phase": "repository_cli_forwarding",
            "objective": "implement_central_target_residue_cli_helper",
            "paths": [
                "src/covalent_ext/covapie_target_residue_atom_condition_repository_cli_v1.py",
                "tests/test_covapie_target_residue_atom_condition_repository_cli_v1.py",
            ],
        },
        {
            "step": "C2",
            "phase": "repository_cli_forwarding",
            "objective": "forward_generate_ligands_cli",
            "paths": ["generate_ligands.py"],
        },
        {
            "step": "C3",
            "phase": "repository_cli_forwarding",
            "objective": "forward_target_selector_through_covalent_demo",
            "paths": ["scripts/covalent_inpaint_demo.py"],
        },
        {
            "step": "C4",
            "phase": "repository_cli_forwarding",
            "objective": "formal_repository_cli_forwarding_gate",
            "paths": [
                "src/covalent_ext/covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1.py",
                "tests/test_covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1.py",
                "scripts/check_covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1.py",
                "docs/covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1_guide.md",
            ],
        },
    ]
    positions = {
        step["step"]: index for index, step in enumerate(ordered_steps)
    }
    return {
        "incremental_commits_required": True,
        "ordered_steps": ordered_steps,
        "consumer_migration_precedes_provider_removal": (
            positions["R1"] < positions["R2"]
        ),
        "provider_removal_precedes_consumer_migration": (
            positions["R2"] < positions["R1"]
        ),
        "single_commit_for_all_increments_allowed": False,
        "cli_forwarding_may_begin_before_R3": False,
        "C1_before_committed_R3_allowed": False,
    }


def _legacy_mask_reference_inventory(repo_root: Path) -> dict[str, Any]:
    _design_path_lifecycle_evidence(repo_root)
    repository_paths = _git(
        repo_root,
        "ls-tree",
        "-r",
        "--name-only",
        _RUNTIME_DESIGN_BASELINE_COMMIT,
    ).splitlines()
    grep_pattern = (
        "build_four_level_mask|MASK_BUILDERS|MaskType|mask_warhead|"
        "mask_linker_and_warhead|mask_scaffold|mask_whole_ligand|"
        "--mask_level|choices"
    )
    grep_output = _git(
        repo_root,
        "grep",
        "-l",
        "-I",
        "-E",
        grep_pattern,
        _RUNTIME_DESIGN_BASELINE_COMMIT,
        "--",
    ).splitlines()
    snapshot_prefix = f"{_RUNTIME_DESIGN_BASELINE_COMMIT}:"
    if any(not item.startswith(snapshot_prefix) for item in grep_output):
        raise ValueError(_ERROR)
    snapshot_candidates = {
        item.removeprefix(snapshot_prefix) for item in grep_output
    }
    candidate_paths = sorted(snapshot_candidates | set(_DESIGN_PATHS))
    inventory: list[dict[str, Any]] = []
    scanned_text_file_count = 0
    notebook_count = 0
    allowed_suffixes = {
        ".py",
        ".pyi",
        ".ipynb",
        ".md",
        ".json",
        ".csv",
        ".txt",
        ".toml",
        ".yaml",
        ".yml",
    }
    for relative_path in candidate_paths:
        path = Path(relative_path)
        if path.suffix.lower() not in allowed_suffixes:
            continue
        payload = _git_snapshot_blob_bytes(
            repo_root,
            commit=_RUNTIME_DESIGN_BASELINE_COMMIT,
            relative_path=relative_path,
        )
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError:
            continue
        scanned_text_file_count += 1
        symbol_kinds: dict[str, set[str]] = {}
        if path.suffix == ".py":
            try:
                tree = ast.parse(text, filename=relative_path)
            except SyntaxError as error:
                raise ValueError(_ERROR) from error
            for symbol in _LEGACY_MASK_SYMBOLS:
                if _text_has_symbol(text, symbol):
                    kinds = _python_reference_kinds(tree, symbol)
                    if not kinds:
                        kinds = {"python_text_reference"}
                    symbol_kinds[symbol] = kinds
            if _has_exact_legacy_choice_set(tree):
                symbol_kinds["choices_A_B_B2_C"] = {"cli_legacy_choice_set"}
        elif path.suffix == ".ipynb":
            try:
                notebook = json.loads(text, object_pairs_hook=_unique_object)
            except Exception as error:
                raise ValueError(_ERROR) from error
            cells = notebook.get("cells") if type(notebook) is dict else None
            if type(cells) is not list:
                raise ValueError(_ERROR)
            notebook_count += 1
            for cell_index, cell in enumerate(cells):
                if type(cell) is not dict or type(cell.get("source")) is not list:
                    continue
                source = "".join(cell["source"])
                source_kind = (
                    "notebook_code_cell_source"
                    if cell.get("cell_type") == "code"
                    else "notebook_markdown_cell_source"
                )
                for symbol in _LEGACY_MASK_SYMBOLS:
                    if _text_has_symbol(source, symbol):
                        symbol_kinds.setdefault(symbol, set()).add(source_kind)
                if cell.get("cell_type") == "code":
                    sanitized = "\n".join(
                        "pass" if line.lstrip().startswith(("%", "!")) else line
                        for line in source.splitlines()
                    )
                    try:
                        tree = ast.parse(
                            sanitized,
                            filename=f"{relative_path}:cell[{cell_index}]",
                        )
                    except SyntaxError as error:
                        raise ValueError(_ERROR) from error
                    if _has_exact_legacy_choice_set(tree):
                        symbol_kinds.setdefault(
                            "choices_A_B_B2_C", set()
                        ).add("notebook_cli_legacy_choice_set")
        else:
            for symbol in _LEGACY_MASK_SYMBOLS:
                if _text_has_symbol(text, symbol):
                    symbol_kinds[symbol] = {"read_only_text_reference"}

        for symbol in sorted(symbol_kinds):
            active, test_only, documentation_only, historical, action = (
                _legacy_reference_classification(relative_path)
            )
            if active:
                retirement_increment = (
                    "R1"
                    if relative_path == "scripts/covalent_inpaint_demo.py"
                    else "R2"
                )
                post_increment_expected_status = (
                    "demo_consumer_removed_core_provider_still_present"
                    if retirement_increment == "R1"
                    else "candidate_active_legacy_zero_pending_R3_gate"
                )
            elif test_only and relative_path != (
                "tests/test_real_covalent_feature_mapping_loader_gate_v0.py"
            ):
                retirement_increment = "R2"
                post_increment_expected_status = (
                    "positive_legacy_behavior_replaced_by_canonical_or_read_only_evidence"
                )
            else:
                retirement_increment = None
                post_increment_expected_status = (
                    "retained_negative_or_read_only_non_active_legacy_evidence"
                )
            inventory.append(
                {
                    "path": relative_path,
                    "symbol_or_token": symbol,
                    "reference_kind": sorted(symbol_kinds[symbol]),
                    "active_runtime": active,
                    "test_only": test_only,
                    "documentation_only": documentation_only,
                    "historical_freeze_only": historical,
                    "required_future_action": action,
                    "retirement_increment": retirement_increment,
                    "positive_legacy_behavior_required": (
                        test_only
                        and relative_path
                        != "tests/test_real_covalent_feature_mapping_loader_gate_v0.py"
                    ),
                    "post_increment_expected_status": (
                        post_increment_expected_status
                    ),
                }
            )

    inventory.sort(key=lambda item: (item["path"], item["symbol_or_token"]))
    future_scope = _future_retirement_implementation_scope()
    scoped_paths = {
        path
        for step in future_scope["ordered_steps"]
        if step["step"] in {"R1", "R2"}
        for path in step["paths"]
    }
    active_records = [item for item in inventory if item["active_runtime"]]
    unresolved = [
        item
        for item in active_records
        if item["required_future_action"] == "UNRESOLVED_ACTIVE_LEGACY_REFERENCE"
        or item["path"] not in scoped_paths
    ]
    classifications = {
        "active_runtime": sum(item["active_runtime"] for item in inventory),
        "test_only": sum(item["test_only"] for item in inventory),
        "documentation_only": sum(
            item["documentation_only"] for item in inventory
        ),
        "historical_freeze_only": sum(
            item["historical_freeze_only"] for item in inventory
        ),
        "design_evidence_only": sum(
            not item["active_runtime"]
            and not item["test_only"]
            and not item["documentation_only"]
            and not item["historical_freeze_only"]
            for item in inventory
        ),
    }
    if (
        not inventory
        or sum(classifications.values()) != len(inventory)
        or not all(
            item["required_future_action"]
            and sum(
                (
                    item["active_runtime"],
                    item["test_only"],
                    item["documentation_only"],
                    item["historical_freeze_only"],
                    not item["active_runtime"]
                    and not item["test_only"]
                    and not item["documentation_only"]
                    and not item["historical_freeze_only"],
                )
            )
            == 1
            for item in inventory
        )
    ):
        raise ValueError(_ERROR)
    return {
        "inventory_version": "covapie_legacy_four_level_mask_reference_baseline_inventory_v1",
        "evidence_mode": "frozen_runtime_baseline_snapshot",
        "runtime_design_baseline_commit": _RUNTIME_DESIGN_BASELINE_COMMIT,
        "inventory_claims_live_runtime_state": False,
        "scanned_repository_file_count": len(repository_paths),
        "scanned_text_file_count": scanned_text_file_count,
        "notebook_json_file_count": notebook_count,
        "notebook_json_cell_source_audited": True,
        "searched_symbols_and_tokens": [
            *_LEGACY_MASK_SYMBOLS,
            "choices_A_B_B2_C",
        ],
        "baseline_reference_count": len(inventory),
        "classification_counts": classifications,
        "baseline_active_legacy_reference_count": len(active_records),
        "baseline_active_legacy_reference_paths": sorted(
            {item["path"] for item in active_records}
        ),
        "baseline_active_legacy_reference_path_count": len(
            {item["path"] for item in active_records}
        ),
        "target_active_reference_count": 0,
        "target_active_reference_path_count": 0,
        "live_active_legacy_reference_count_claimed": False,
        "records": inventory,
        "unresolved_legacy_mask_references": unresolved,
        "baseline_unresolved_active_reference_count": len(unresolved),
        "inventory_complete": True,
        "all_active_legacy_references_in_future_scope": not unresolved,
        "all_active_references_have_future_actions": all(
            item["required_future_action"]
            != "UNRESOLVED_ACTIVE_LEGACY_REFERENCE"
            for item in active_records
        ),
        "full_retirement_requires_R1": True,
        "full_retirement_requires_R2": True,
        "full_retirement_requires_R3_gate": True,
        "future_retirement_implementation_scope": future_scope,
    }


def _ready_for_covalent_demo_canonical_mask_migration_R1(
    inventory: Mapping[str, Any],
    dependency_evidence: Mapping[str, Any],
    *,
    canonical_five_level_contract_complete: bool,
) -> bool:
    records = inventory.get("records") if isinstance(inventory, Mapping) else None
    active_records = (
        [item for item in records if item.get("active_runtime") is True]
        if isinstance(records, list)
        and all(isinstance(item, Mapping) for item in records)
        else []
    )
    return (
        isinstance(inventory, Mapping)
        and inventory.get("inventory_complete") is True
        and inventory.get("all_active_legacy_references_in_future_scope") is True
        and inventory.get("all_active_references_have_future_actions") is True
        and inventory.get("unresolved_legacy_mask_references") == []
        and inventory.get("baseline_unresolved_active_reference_count") == 0
        and inventory.get("baseline_active_legacy_reference_count") == 14
        and inventory.get("baseline_active_legacy_reference_path_count") == 5
        and len(active_records) == 14
        and all(
            item.get("retirement_increment") in {"R1", "R2"}
            and item.get("required_future_action")
            != "UNRESOLVED_ACTIVE_LEGACY_REFERENCE"
            for item in active_records
        )
        and all(
            item.get("retirement_increment") == "R1"
            for item in active_records
            if item.get("path") == "scripts/covalent_inpaint_demo.py"
        )
        and isinstance(dependency_evidence, Mapping)
        and dependency_evidence.get("legacy_provider_has_active_consumers")
        is True
        and dependency_evidence.get(
            "consumer_migration_precedes_provider_removal"
        )
        is True
        and dependency_evidence.get("no_intermediate_missing_import_state")
        is True
        and canonical_five_level_contract_complete is True
    )


def _ready_for_legacy_core_api_retirement_R2(
    dependency_evidence: Mapping[str, Any],
    *,
    R1_committed: bool,
) -> bool:
    return (
        isinstance(dependency_evidence, Mapping)
        and R1_committed is True
        and dependency_evidence.get(
            "consumer_migration_precedes_provider_removal"
        )
        is True
        and dependency_evidence.get("provider_symbols_present") is True
        and dependency_evidence.get("legacy_demo_imports_four_level_builder")
        is False
        and dependency_evidence.get("legacy_demo_calls_four_level_builder")
        is False
        and dependency_evidence.get("legacy_demo_mask_level_flag_present")
        is False
    )


def _zero_active_legacy_reference_retirement_gate_contract() -> dict[str, Any]:
    return {
        "gate_step": "R3",
        "post_retirement_active_legacy_reference_count": 0,
        "post_retirement_unresolved_legacy_reference_count": 0,
        "required_negative_runtime_evidence": {
            "legacy_builder_importable": False,
            "legacy_builder_callable": False,
            "legacy_schema_type_present": False,
            "legacy_cli_flag_present": False,
            "legacy_short_token_runtime_input_supported": False,
        },
        "canonical_five_level_runtime_complete": True,
        "scan_coverage": [
            "all_tracked_python_files",
            "all_current_non_historical_tests",
            "all_active_scripts",
            "notebook_json_code_cell_source",
            "schema_and_type_aliases",
            "imports_definitions_calls_and_registries",
            "cli_argument_definitions_and_choice_sets",
            "string_comparisons_against_short_tokens",
            "dataset_keys_and_apis_with_short_only_semantics",
        ],
        "scan_methods": [
            "python_ast",
            "notebook_json_cell_source_ast",
            "structured_schema_inspection",
            "controlled_text_search",
        ],
        "broad_ignore_docs_allowed": False,
        "broad_ignore_data_allowed": False,
        "historical_whitelist_paths": [
            "data/derived/covalent_small/b3_scaffold_only_mask_design_v0/b3_scaffold_only_mask_design_report.csv",
            "data/derived/covalent_small/b3_scaffold_only_mask_design_v0/b3_scaffold_only_mask_protocol.json",
            "scripts/check_diffsbdd_atomwise_loss_hook_prototype_v0.py",
            "scripts/check_diffsbdd_backward_smoke_v0.py",
            "scripts/check_diffsbdd_single_batch_forward_shape_smoke_v0.py",
            "src/covalent_ext/b3_scaffold_only_mask_design.py",
            "src/covalent_ext/b3_scaffold_only_mask_implementation.py",
            "docs/covapie_target_residue_atom_condition_repository_cli_forwarding_design_v1_guide.md",
            "src/covalent_ext/covapie_target_residue_atom_condition_repository_cli_forwarding_design_v1.py",
        ],
        "formal_predecessor_bundle_whitelist": [
            "covapie-state/manual-review/covapie_current11_target_residue_atom_condition_model_consumption_gate_bundle_v1.json"
        ],
        "whitelist_entry_contract": {
            "explicitly_classified": True,
            "read_only": True,
            "active_runtime": False,
            "runtime_importable": False,
            "runtime_callable": False,
            "schema_admissible": False,
            "training_admissible": False,
            "automatic_translation_allowed": False,
            "positive_legacy_behavior_required_by_current_tests": False,
        },
        "repository_text_must_contain_zero_legacy_strings": False,
        "correct_terminal_condition": (
            "zero_active_legacy_references_with_explicit_read_only_historical_evidence_retained"
        ),
        "gate_must_pass_and_be_committed_before_C1": True,
    }


def _checkpoint_evidence(repo_root: Path) -> dict[str, Any]:
    checkpoint_path = repo_root / _CHECKPOINT_PATH
    checkpoint_bytes = _regular_file_bytes(
        repo_root,
        _CHECKPOINT_PATH,
        expected_sha256=_CHECKPOINT_SHA256,
        expected_size=_CHECKPOINT_SIZE,
        max_size=_MAX_CHECKPOINT_BYTES,
    )
    try:
        import torch

        from covalent_ext.covapie_target_residue_atom_condition_checkpoint_migration_v1 import (
            load_covapie_base_state_dict_into_target_residue_conditioned_model_v1,
        )
        from lightning_modules import LigandPocketDDPM

        entry_rng = torch.random.get_rng_state().clone()
        try:
            payload = torch.load(
                io.BytesIO(checkpoint_bytes),
                map_location="cpu",
                weights_only=False,
            )
            if type(payload) is not dict:
                raise ValueError(_ERROR)
            hyper_parameters = payload.get("hyper_parameters")
            state_dict = payload.get("state_dict")
            if (
                type(hyper_parameters) is not dict
                or set(hyper_parameters) != _EXPECTED_HPARAMETER_KEYS
                or not isinstance(state_dict, Mapping)
                or len(state_dict) != 122
                or any(
                    type(key) is not str or not isinstance(value, torch.Tensor)
                    for key, value in state_dict.items()
                )
                or hyper_parameters.get("mode") != "pocket_conditioning"
                or hyper_parameters.get("pocket_representation") != "full-atom"
                or getattr(hyper_parameters.get("egnn_params"), "joint_nf", None) != 32
                or "target_residue_atom_conditioning" in hyper_parameters
            ):
                raise ValueError(_ERROR)

            base_keys = list(state_dict)
            base_ids = {key: id(value) for key, value in state_dict.items()}
            base_versions = {key: value._version for key, value in state_dict.items()}
            base_snapshots = {
                key: value.detach().clone() for key, value in state_dict.items()
            }
            constructor_arguments = dict(hyper_parameters)
            constructor_arguments["target_residue_atom_conditioning"] = True
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
                io.StringIO()
            ):
                model = LigandPocketDDPM(**constructor_arguments)
                migration_report = load_covapie_base_state_dict_into_target_residue_conditioned_model_v1(
                    model=model,
                    base_state_dict=state_dict,
                )

            dynamics = getattr(getattr(model, "ddpm", None), "dynamics", None)
            new_parameter = getattr(
                dynamics, "target_residue_atom_condition_embedding", None
            )
            mapping_unchanged = base_keys == list(state_dict)
            tensor_objects_unchanged = all(
                id(state_dict[key]) == base_ids[key] for key in base_keys
            )
            tensor_versions_unchanged = all(
                state_dict[key]._version == base_versions[key] for key in base_keys
            )
            tensor_values_unchanged = all(
                torch.equal(state_dict[key], base_snapshots[key]) for key in base_keys
            )
            file_unchanged = (
                checkpoint_path.stat().st_size == _CHECKPOINT_SIZE
                and _sha256(checkpoint_path.read_bytes()) == _CHECKPOINT_SHA256
            )
            strict_ready = all(
                (
                    model.target_residue_atom_conditioning is True,
                    getattr(dynamics, "target_residue_atom_conditioning", None)
                    is True,
                    isinstance(new_parameter, torch.nn.Parameter),
                    list(new_parameter.shape) == [32],
                    int(torch.count_nonzero(new_parameter).item()) == 0,
                    migration_report.get("filled_state_keys") == [_NEW_STATE_KEY],
                    migration_report.get("base_state_key_count") == 122,
                    migration_report.get("model_state_key_count") == 123,
                    migration_report.get("missing_keys") == [],
                    migration_report.get("unexpected_keys") == [],
                    migration_report.get("strict_load") is True,
                    migration_report.get("base_state_dict_modified") is False,
                    mapping_unchanged,
                    tensor_objects_unchanged,
                    tensor_versions_unchanged,
                    tensor_values_unchanged,
                    file_unchanged,
                )
            )
            if not strict_ready:
                raise ValueError(_ERROR)
            return {
                "checkpoint_size": _CHECKPOINT_SIZE,
                "checkpoint_sha256": _CHECKPOINT_SHA256,
                "top_level_keys": list(payload),
                "hyper_parameters_type": "dict",
                "hyper_parameters_keys": sorted(hyper_parameters),
                "state_dict_key_count": len(state_dict),
                "mode": hyper_parameters["mode"],
                "pocket_representation": hyper_parameters[
                    "pocket_representation"
                ],
                "joint_nf": hyper_parameters["egnn_params"].joint_nf,
                "enabled_model_constructed": True,
                "exactly_one_key_filled": True,
                "filled_state_keys": [_NEW_STATE_KEY],
                "missing_keys": [],
                "unexpected_keys": [],
                "final_strict_load": True,
                "blanket_strict_false": False,
                "new_parameter_zero_initialized": True,
                "base_mapping_unchanged": True,
                "base_tensors_unchanged": True,
                "checkpoint_file_modified": False,
                "model_forward_executed": False,
                "training_or_parameter_update": False,
            }
        finally:
            torch.random.set_rng_state(entry_rng)
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _resolve_target_arguments_contract_v1(arguments: Mapping[str, Any]) -> dict[str, Any] | None:
    """Pure design oracle for the future shared CLI argument resolver."""

    try:
        if not isinstance(arguments, Mapping) or any(type(key) is not str for key in arguments):
            raise ValueError(_ERROR)
        allowed = {
            "target_residue_atom_conditioning",
            "target_chain_id",
            "target_residue_sequence_number",
        }
        if any(key.startswith("target_") and key not in allowed for key in arguments):
            raise ValueError(_ERROR)
        missing = object()
        enabled = arguments.get("target_residue_atom_conditioning", missing)
        chain = arguments.get("target_chain_id")
        residue_number = arguments.get("target_residue_sequence_number")
        if enabled is not missing and type(enabled) is not bool:
            raise ValueError(_ERROR)
        if (
            (enabled is missing or enabled is False)
            and chain is None
            and residue_number is None
        ):
            return None
        if (
            enabled is not True
            or type(chain) is not str
            or not chain
            or chain != chain.strip()
            or type(residue_number) is not int
            or type(residue_number) is bool
        ):
            raise ValueError(_ERROR)
        return {
            "chain_id": chain,
            "residue_sequence_number": residue_number,
            "residue_insertion_code": " ",
            "residue_name": "CYS",
            "atom_name": "SG",
            "element": "S",
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _resolve_canonical_mask_semantic_contract_v1(
    value: object,
) -> dict[str, str]:
    """Resolve only a canonical long semantic name; aliases fail closed."""

    try:
        if type(value) is not str or value not in _MASK_LONG_TO_INTERNAL:
            raise ValueError(_ERROR)
        return {
            "canonical_semantic_name": value,
            "internal_long_form_mask": _MASK_LONG_TO_INTERNAL[value],
            "display_alias": _MASK_LONG_TO_DISPLAY_ALIAS[value],
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _deferred_caller_contracts() -> list[dict[str, Any]]:
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


def _validate_response(response: Mapping[str, Any], *, require_order: bool) -> None:
    if (
        type(response) is not dict
        or set(response) != set(REPOSITORY_CLI_FORWARDING_DESIGN_RESPONSE_FIELDS)
        or (require_order and tuple(response) != REPOSITORY_CLI_FORWARDING_DESIGN_RESPONSE_FIELDS)
        or len(response) != 43
    ):
        raise ValueError(_ERROR)
    digest_payload = dict(response)
    digest = digest_payload.pop("repository_cli_forwarding_design_response_sha256")
    if (
        type(digest) is not str
        or len(digest) != 64
        or digest != digest.lower()
        or digest != _sha256(_canonical_json_bytes(digest_payload))
    ):
        raise ValueError(_ERROR)
    try:
        encoded = _canonical_json_bytes(response)
    except Exception as error:
        raise ValueError(_ERROR) from error
    if not encoded:
        raise ValueError(_ERROR)


def design_covapie_target_residue_atom_condition_repository_cli_forwarding_v1(
    *,
    source_model_consumption_gate_bundle: bytes,
    repo_root: Path,
) -> dict[str, Any]:
    """Return the deterministic Exact43 repository CLI forwarding design."""

    try:
        if (
            type(source_model_consumption_gate_bundle) is not bytes
            or not isinstance(repo_root, Path)
            or not repo_root.is_absolute()
            or not repo_root.is_dir()
        ):
            raise ValueError(_ERROR)
        source_snapshot = bytes(source_model_consumption_gate_bundle)
        bundle = _validate_gate_bundle(source_model_consumption_gate_bundle)
        gate_evidence = _gate_source_evidence(repo_root)
        baseline_source_evidence = _runtime_design_baseline_source_evidence(
            repo_root
        )
        caller_audit = _caller_audit(repo_root)
        model_source_evidence = _model_and_mask_source_audit(repo_root)
        legacy_mask_inventory = _legacy_mask_reference_inventory(repo_root)
        retirement_dependency_evidence = (
            _retirement_dependency_order_evidence(repo_root)
        )
        checkpoint = _checkpoint_evidence(repo_root)
        if source_model_consumption_gate_bundle != source_snapshot:
            raise ValueError(_ERROR)

        deferrals = _deferred_caller_contracts()
        exact6_example = _resolve_target_arguments_contract_v1(
            {
                "target_residue_atom_conditioning": True,
                "target_chain_id": "A",
                "target_residue_sequence_number": 123,
            }
        )
        legacy_example = _resolve_target_arguments_contract_v1({})
        canonical_mask_examples = [
            _resolve_canonical_mask_semantic_contract_v1(name)
            for name in CANONICAL_MASK_SEMANTIC_NAMES
        ]
        if (
            exact6_example is None
            or legacy_example is not None
            or [
                item["canonical_semantic_name"]
                for item in canonical_mask_examples
            ]
            != list(CANONICAL_MASK_SEMANTIC_NAMES)
        ):
            raise ValueError(_ERROR)

        exact6_contract = {
            "selector_type": "Exact6",
            "compiled_fields": [
                "chain_id",
                "residue_sequence_number",
                "residue_insertion_code",
                "residue_name",
                "atom_name",
                "element",
            ],
            "fixed_fields": {
                "residue_insertion_code": " ",
                "residue_name": "CYS",
                "atom_name": "SG",
                "element": "S",
            },
            "user_overridable_fields": ["chain_id", "residue_sequence_number"],
            "user_override_of_fixed_fields_allowed": False,
            "blank_insertion_code_cys_sg_s_only": True,
            "automatic_target_inference_sources": [],
            "resi_list_inference_allowed": False,
            "ref_ligand_inference_allowed": False,
            "distance_or_nearest_s_inference_allowed": False,
            "design_oracle_example": exact6_example,
        }
        legacy_contract = {
            "conditioned_mode": False,
            "target_enable_flag_absent_or_exact_false": True,
            "selector": None,
            "generate_ligands_non_mask_behavior_unchanged": True,
            "existing_checkpoint_loader_path_retained": True,
            "loader_call": "LigandPocketDDPM.load_from_checkpoint(checkpoint_path,map_location=map_location)",
            "silent_fallback_from_partial_selector_allowed": False,
            "legacy_mask_compatibility_claimed": False,
        }
        conditioned_contract = {
            "conditioned_mode": True,
            "target_enable_flag_exact_bool_required": True,
            "enable_flag_required": True,
            "nonempty_already_stripped_chain_required": True,
            "chain_automatic_trim_allowed": False,
            "exact_int_residue_sequence_number_required": True,
            "bool_residue_sequence_number_rejected": True,
            "partial_arguments_rejected": True,
            "target_fields_without_enable_flag_rejected": True,
            "unknown_target_fields_rejected": True,
            "selector_compiled_before_model_or_pocket_call": True,
            "conditioned_model_required": True,
        }
        checkpoint_strategy = {
            "checkpoint_path": _CHECKPOINT_PATH,
            "checkpoint_size": checkpoint["checkpoint_size"],
            "checkpoint_sha256": checkpoint["checkpoint_sha256"],
            "read_only_payload_load": True,
            "top_level_keys": checkpoint["top_level_keys"],
            "hyper_parameters_type": checkpoint["hyper_parameters_type"],
            "hyper_parameters_keys": checkpoint["hyper_parameters_keys"],
            "state_dict_key_count": checkpoint["state_dict_key_count"],
            "mode": checkpoint["mode"],
            "pocket_representation": checkpoint["pocket_representation"],
            "joint_nf": checkpoint["joint_nf"],
            "override": {"target_residue_atom_conditioning": True},
            "enabled_model_constructed": checkpoint["enabled_model_constructed"],
            "exactly_one_key_filled": checkpoint["exactly_one_key_filled"],
            "filled_state_keys": checkpoint["filled_state_keys"],
            "final_strict_load": checkpoint["final_strict_load"],
            "missing_keys": checkpoint["missing_keys"],
            "unexpected_keys": checkpoint["unexpected_keys"],
            "blanket_strict_false": checkpoint["blanket_strict_false"],
            "new_parameter_zero_initialized": checkpoint[
                "new_parameter_zero_initialized"
            ],
            "base_mapping_unchanged": checkpoint["base_mapping_unchanged"],
            "base_tensors_unchanged": checkpoint["base_tensors_unchanged"],
            "checkpoint_file_modified": checkpoint["checkpoint_file_modified"],
            "checkpoint_disk_rewrite_allowed": False,
            "model_forward_executed": checkpoint["model_forward_executed"],
        }
        helper_contract = {
            "central_module": "src/covalent_ext/covapie_target_residue_atom_condition_repository_cli_v1.py",
            "public_apis": [
                "add_covapie_target_residue_atom_condition_cli_arguments_v1",
                "resolve_covapie_target_residue_atom_condition_cli_args_v1",
                "load_covapie_target_residue_conditioned_model_from_checkpoint_v1",
            ],
            "responsibilities": [
                "argument_definition",
                "Exact6_compilation",
                "conditioned_checkpoint_loading",
                "canonical_error_normalization",
            ],
            "duplicate_parser_or_loader_logic_allowed": False,
            "migration_helper": "load_covapie_base_state_dict_into_target_residue_conditioned_model_v1",
            "migration_helper_module": "src/covalent_ext/covapie_target_residue_atom_condition_checkpoint_migration_v1.py",
        }
        generate_contract = {
            "caller": "generate_ligands.py",
            "task": "empty_or_selected_pocket_plus_cys_sg_to_conditioned_ligands",
            "shared_cli_arguments_added": True,
            "loader_selected_by_conditioned_mode": True,
            "forward_to": "model.generate_ligands",
            "forward_keyword": "target_residue_atom_condition_spec",
            "selector_forwarding_site_count": 1,
            "legacy_defaults_unchanged": True,
            "batch_loop_unchanged": True,
            "sdf_write_unchanged": True,
            "num_nodes_logic_unchanged": True,
            "sanitize_relax_logic_unchanged": True,
            "indicator_true_count_per_sample": 1,
        }
        inpaint_contract = {
            "caller": "scripts/covalent_inpaint_demo.py",
            "baseline_covalent_demo_sha256": _CALLER_SHA256S[
                "scripts/covalent_inpaint_demo.py"
            ],
            "baseline_source_commit": _RUNTIME_DESIGN_BASELINE_COMMIT,
            "contract_claims_live_demo_sha256": False,
            "task": "protein_known_ligand_and_cys_sg_local_generation",
            "mask_surface_migration_step": "R1",
            "target_residue_forwarding_step": "C3",
            "R1_scope_is_mask_surface_only": True,
            "R1_adds_target_residue_cli_arguments": False,
            "R1_modifies_checkpoint_loader": False,
            "R1_executes_model_forward": False,
            "forward_path": [
                "run_covalent_inpaint",
                "prepare_single_pocket",
                "model.prepare_pocket",
            ],
            "forward_keyword": "target_residue_atom_condition_spec",
            "prepare_pocket_selector_forwarding_site_count": 1,
            "pocket_dictionary_carries_indicator_to_sample_or_inpaint": True,
            "manual_indicator_creation_allowed": False,
            "direct_dynamics_call_allowed": False,
            "canonical_mask_flag": "--mask_semantic",
            "legacy_mask_flag": None,
            "mask_builder": "build_long_form_mask",
            "all_five_canonical_masks_reachable": True,
            "legacy_four_level_fallback_allowed": False,
        }
        mask_contract = {
            "design_evidence_mode": "frozen_runtime_baseline_snapshot",
            "runtime_design_baseline_commit": _RUNTIME_DESIGN_BASELINE_COMMIT,
            "runtime_design_baseline_source_evidence": (
                baseline_source_evidence
            ),
            "design_baseline_snapshot_immutable": True,
            "design_checker_claims_live_runtime_state": False,
            "implementation_phase_live_state_requires_phase_specific_gate": True,
            "recommended_next_step_is_design_baseline_recommendation": True,
            "R1_candidate_will_not_invalidate_design_tests": True,
            "phase_gate_responsibilities": {
                "repository_CLI_design": (
                    "prove_R1_R2_R3_need_order_and_contracts_from_frozen_baseline"
                ),
                "R1_tests_and_checker": (
                    "prove_demo_canonical_five_level_migration_complete"
                ),
                "R2_tests_and_checker": (
                    "prove_core_legacy_API_removed_and_remaining_consumers_migrated"
                ),
                "R3_gate": "prove_live_active_legacy_reference_count_zero",
            },
            "canonical_input_flag": "--mask_semantic",
            "legacy_input_flag": None,
            "canonical_five_level_target_selected": True,
            "canonical_five_level_contract_complete": True,
            "legacy_four_level_retirement_selected": True,
            "legacy_four_level_retirement_implemented": False,
            "retirement_R3_gate_passed": False,
            "retirement_R3_gate_committed": False,
            "baseline_legacy_four_level_runtime_present": True,
            "baseline_legacy_four_level_cli_input_present": True,
            "baseline_legacy_four_level_schema_present": True,
            "baseline_legacy_provider_has_active_consumers": (
                retirement_dependency_evidence[
                    "legacy_provider_has_active_consumers"
                ]
            ),
            "baseline_provider_removal_before_consumer_migration_safe": (
                retirement_dependency_evidence[
                    "provider_removal_before_consumer_migration_safe"
                ]
            ),
            "retirement_dependency_order_valid": (
                retirement_dependency_evidence[
                    "consumer_migration_precedes_provider_removal"
                ]
                and retirement_dependency_evidence[
                    "no_intermediate_missing_import_state"
                ]
            ),
            "retirement_dependency_order_evidence": (
                retirement_dependency_evidence
            ),
            "baseline_reference_count": legacy_mask_inventory[
                "baseline_reference_count"
            ],
            "baseline_active_legacy_reference_count": legacy_mask_inventory[
                "baseline_active_legacy_reference_count"
            ],
            "baseline_active_legacy_reference_path_count": legacy_mask_inventory[
                "baseline_active_legacy_reference_path_count"
            ],
            "target_active_legacy_reference_count": 0,
            "target_active_legacy_reference_path_count": 0,
            "live_active_legacy_reference_count_claimed": False,
            "target_legacy_four_level_runtime_supported": False,
            "target_legacy_four_level_cli_input_supported": False,
            "target_legacy_short_alias_input_supported": False,
            "target_legacy_automatic_translation_allowed": False,
            "historical_read_only_legacy_evidence_retained": True,
            "short_alias_report_only": True,
            "target_legacy_short_mask_tokens_training_accepted": False,
            "ambiguous_legacy_B2_reinterpretation_allowed": False,
            "canonical_B2_semantic": "scaffold_plus_warhead",
            "canonical_B3_semantic": "scaffold_only",
            "canonical_long_names": list(CANONICAL_MASK_SEMANTIC_NAMES),
            "long_name_to_internal": dict(_MASK_LONG_TO_INTERNAL),
            "long_name_to_display_alias": dict(_MASK_LONG_TO_DISPLAY_ALIAS),
            "canonical_resolver_examples": canonical_mask_examples,
            "target_internal_builder": "build_long_form_mask",
            "target_legacy_builder_fallback_allowed": False,
            "canonical_mask_count": 5,
            "scaffold_plus_warhead_present": True,
            "scaffold_only_present": True,
            "sixth_mask_added": False,
            "test_real_covalent_feature_mapping_loader_gate_v0_modified_in_R1": False,
            "test_real_covalent_feature_mapping_loader_gate_v0_modified_in_R2": False,
            "negative_legacy_token_rejection_evidence_retained": True,
            "historical_B3_source_modified_in_R2": False,
            "legacy_reference_inventory": legacy_mask_inventory,
            "unresolved_legacy_mask_references": legacy_mask_inventory[
                "unresolved_legacy_mask_references"
            ],
            "future_retirement_implementation_scope": legacy_mask_inventory[
                "future_retirement_implementation_scope"
            ],
            "zero_active_legacy_reference_retirement_gate_contract": (
                _zero_active_legacy_reference_retirement_gate_contract()
            ),
            "active_residual_categories_that_must_reach_zero": [
                "active_runtime_definitions",
                "active_runtime_imports",
                "active_runtime_calls",
                "active_runtime_registries",
                "active_schema_types",
                "active_dataset_keys_and_apis",
                "active_cli_options",
                "active_cli_choice_sets",
                "active_checker_expectations",
                "current_non_historical_positive_legacy_runtime_tests",
            ],
        }
        R1_ready = _ready_for_covalent_demo_canonical_mask_migration_R1(
            legacy_mask_inventory,
            retirement_dependency_evidence,
            canonical_five_level_contract_complete=mask_contract[
                "canonical_five_level_contract_complete"
            ],
        )
        R1_committed = all(
            retirement_dependency_evidence[name] is False
            for name in (
                "legacy_demo_imports_four_level_builder",
                "legacy_demo_calls_four_level_builder",
                "legacy_demo_mask_level_flag_present",
            )
        )
        R2_ready = _ready_for_legacy_core_api_retirement_R2(
            retirement_dependency_evidence,
            R1_committed=R1_committed,
        )
        mask_contract["ready_for_covalent_demo_canonical_mask_migration_R1"] = (
            R1_ready
        )
        mask_contract["ready_for_legacy_core_api_retirement_R2"] = R2_ready
        failure_contract = {
            "error": "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_REPOSITORY_CLI_INVALID",
            "fail_closed": True,
            "silent_legacy_downgrade_allowed": False,
            "rejected_conditions": [
                "partial_target_arguments",
                "unsupported_checkpoint",
                "checkpoint_sha_or_size_drift",
                "checkpoint_mode_mismatch",
                "non_full_atom_pocket_representation",
                "conditioned_model_not_enabled",
                "migration_more_than_one_missing_key",
                "migration_unexpected_key",
                "target_cys_sg_missing",
                "target_cys_sg_duplicate",
                "ca_pocket",
                "nonblank_insertion_code_request",
                "incorrect_or_unknown_mask_semantic",
                "legacy_short_mask_token",
                "legacy_internal_long_form_name_as_cli_input",
                "legacy_mask_level_flag",
                "non_bool_target_enable_flag",
                "unstripped_target_chain",
            ],
            "legacy_mask_token_automatic_migration": False,
            "historical_B2_automatic_interpretation": None,
            "explicit_offline_provenance_bound_legacy_migration_required": True,
        }

        design_evidence_complete = all(
            (
                all(gate_evidence.values()),
                bundle["model_consumption_gate_implemented"] is True,
                bundle["ready_for_repository_cli_forwarding_design"] is True,
                len(caller_audit["by_caller"]) == 6,
                caller_audit["totals"] == _EXPECTED_CALL_COUNTS,
                caller_audit["notebook_json_cell_source_audited"] is True,
                tuple(_SUPPORTED_CALLERS)
                == ("generate_ligands.py", "scripts/covalent_inpaint_demo.py"),
                tuple(item["caller"] for item in deferrals) == _DEFERRED_CALLERS,
                all(item["deferred"] is True for item in deferrals),
                all(model_source_evidence.values()),
                checkpoint_strategy["enabled_model_constructed"] is True,
                checkpoint_strategy["exactly_one_key_filled"] is True,
                checkpoint_strategy["final_strict_load"] is True,
                checkpoint_strategy["missing_keys"] == [],
                checkpoint_strategy["unexpected_keys"] == [],
                checkpoint_strategy["checkpoint_file_modified"] is False,
                conditioned_contract["target_enable_flag_exact_bool_required"]
                is True,
                len(CANONICAL_MASK_SEMANTIC_NAMES) == 5,
                mask_contract["canonical_five_level_target_selected"] is True,
                mask_contract["canonical_five_level_contract_complete"] is True,
                mask_contract["legacy_four_level_retirement_selected"] is True,
                mask_contract["legacy_four_level_retirement_implemented"]
                is False,
                all(
                    baseline_source_evidence[name] is True
                    for name in (
                        "runtime_design_baseline_commit_exists",
                        "runtime_design_baseline_commit_single_parent",
                        "runtime_design_baseline_commit_is_head_ancestor",
                        "runtime_design_baseline_commit_is_origin_main_ancestor",
                    )
                ),
                mask_contract["design_checker_claims_live_runtime_state"]
                is False,
                mask_contract["baseline_reference_count"] == 45,
                mask_contract["baseline_active_legacy_reference_count"] == 14,
                mask_contract[
                    "baseline_active_legacy_reference_path_count"
                ]
                == 5,
                mask_contract["target_active_legacy_reference_count"] == 0,
                mask_contract["target_active_legacy_reference_path_count"] == 0,
                mask_contract["target_legacy_four_level_runtime_supported"]
                is False,
                mask_contract[
                    "target_legacy_four_level_cli_input_supported"
                ]
                is False,
                mask_contract["target_legacy_short_alias_input_supported"]
                is False,
                mask_contract["target_legacy_automatic_translation_allowed"]
                is False,
                legacy_mask_inventory["inventory_complete"] is True,
                legacy_mask_inventory[
                    "all_active_legacy_references_in_future_scope"
                ]
                is True,
                mask_contract["retirement_dependency_order_valid"] is True,
                R1_ready,
                R2_ready is False,
                mask_contract["canonical_B2_semantic"]
                == "scaffold_plus_warhead",
                mask_contract["canonical_B3_semantic"] == "scaffold_only",
                "scaffold_only" in CANONICAL_MASK_SEMANTIC_NAMES,
                mask_contract["sixth_mask_added"] is False,
                failure_contract["fail_closed"] is True,
            )
        )
        retirement_implemented = (
            mask_contract["design_checker_claims_live_runtime_state"] is False
            and mask_contract["retirement_R3_gate_passed"] is True
            and mask_contract["retirement_R3_gate_committed"] is True
        )
        repository_cli_forwarding_ready = (
            design_evidence_complete and retirement_implemented
        )
        values: dict[str, Any] = {
            "repository_cli_forwarding_design_version": _VERSION,
            "source_model_consumption_gate_bundle_transport_sha256": _BUNDLE_TRANSPORT_SHA256,
            "source_model_consumption_gate_bundle_sha256": _BUNDLE_INTERNAL_SHA256,
            "source_model_consumption_gate_commit": _GATE_COMMIT,
            "source_model_consumption_implementation_commit": _IMPLEMENTATION_COMMIT,
            "source_runtime_bridge_gate_commit": _RUNTIME_BRIDGE_GATE_COMMIT,
            "source_generate_ligands_sha256": _CALLER_SHA256S["generate_ligands.py"],
            "source_test_sha256": _CALLER_SHA256S["test.py"],
            "source_optimize_sha256": _CALLER_SHA256S["optimize.py"],
            "source_inpaint_sha256": _CALLER_SHA256S["inpaint.py"],
            "source_covalent_inpaint_demo_sha256": _CALLER_SHA256S[
                "scripts/covalent_inpaint_demo.py"
            ],
            "source_colab_notebook_sha256": _CALLER_SHA256S[
                "colab/DiffSBDD.ipynb"
            ],
            "source_lightning_module_sha256": _LIGHTNING_SHA256,
            "source_checkpoint_migration_sha256": _MIGRATION_SHA256,
            "audited_caller_count": len(caller_audit["by_caller"]),
            "audited_checkpoint_load_site_count": caller_audit["totals"][
                "LigandPocketDDPM.load_from_checkpoint"
            ],
            "audited_model_generate_ligands_call_count": caller_audit["totals"][
                "model.generate_ligands"
            ],
            "audited_prepare_pocket_direct_call_count": caller_audit["totals"][
                "model.prepare_pocket"
            ],
            "audited_ddpm_inpaint_direct_call_count": caller_audit["totals"][
                "model.ddpm.inpaint"
            ],
            "audited_ddpm_diversify_direct_call_count": caller_audit["totals"][
                "model.ddpm.diversify"
            ],
            "selected_v1_supported_callers": list(_SUPPORTED_CALLERS),
            "deferred_callers": deferrals,
            "selected_cli_enable_flag": "--target_residue_atom_conditioning",
            "selected_cli_chain_flag": "--target_chain_id",
            "selected_cli_residue_sequence_number_flag": "--target_residue_sequence_number",
            "selected_exact6_compilation_contract": exact6_contract,
            "selected_legacy_mode_contract": legacy_contract,
            "selected_conditioned_mode_contract": conditioned_contract,
            "selected_conditioned_checkpoint_load_strategy": checkpoint_strategy,
            "selected_checkpoint_migration_helper": helper_contract,
            "selected_generate_ligands_forwarding_contract": generate_contract,
            "selected_covalent_inpaint_forwarding_contract": inpaint_contract,
            "selected_mask_semantic_normalization_contract": mask_contract,
            "selected_test_manifest_deferral_contract": deferrals[0],
            "selected_notebook_deferral_contract": deferrals[3],
            "selected_failure_contract": failure_contract,
            "canonical_mask_semantic_names": list(CANONICAL_MASK_SEMANTIC_NAMES),
            "repository_cli_selector_forwarding_implemented": False,
            "ready_for_repository_cli_forwarding_implementation": (
                repository_cli_forwarding_ready
            ),
            "recommended_next_step": (
                "implement_covapie_covalent_demo_canonical_five_level_mask_migration_r1_v1"
            ),
            "training_or_parameter_update": False,
            "feature_semantics_audit_required_before_training": True,
        }
        response = {
            field: values[field]
            for field in REPOSITORY_CLI_FORWARDING_DESIGN_RESPONSE_FIELDS
            if field != "repository_cli_forwarding_design_response_sha256"
        }
        response["repository_cli_forwarding_design_response_sha256"] = _sha256(
            _canonical_json_bytes(response)
        )
        _validate_response(response, require_order=True)
        return response
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
