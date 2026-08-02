"""Formal successor gate for target-residue atom-condition consumption V1.

The evaluator binds the committed implementation and the formal Current11
runtime-bridge bundle, then independently reconstructs validator, checkpoint,
migration, threading, and injection evidence.  It performs no model training,
network access, repository mutation, or complete Current11 EGNN forward.
"""

from __future__ import annotations

import ast
import hashlib
import io
import json
import os
import re
import secrets
import stat
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

import torch
from torch import nn

from covalent_ext import (
    covapie_target_residue_atom_condition_checkpoint_migration_v1 as migration,
)
from covalent_ext import (
    covapie_target_residue_atom_condition_runtime_bridge_gate_v1 as runtime_gate,
)
from equivariant_diffusion.dynamics import EGNNDynamics
from equivariant_diffusion.en_diffusion import EnVariationalDiffusion


__all__ = (
    "evaluate_covapie_target_residue_atom_condition_model_consumption_gate_v1",
)


_ERROR = "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_MODEL_CONSUMPTION_GATE_INVALID"
_MODEL_ERROR = "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_MODEL_CONSUMPTION_INVALID"
_VERSION = "covapie_target_residue_atom_condition_model_consumption_gate_v1"
_FIELD = "pocket_target_residue_atom_condition_indicator"
_PARAMETER = "target_residue_atom_condition_embedding"
_NEW_STATE_KEY = f"ddpm.dynamics.{_PARAMETER}"
_RUNTIME_BRIDGE_GATE_COMMIT = "148689cc0716a56f3eb991f762af0010c5849f3a"
_RUNTIME_BRIDGE_GATE_PARENT = "75589a94235dde2d0943606e58a1f2216b31d3b2"
_RUNTIME_BRIDGE_GATE_SUBJECT = (
    "add CovaPIE target residue atom condition runtime bridge gate v1"
)
_RUNTIME_BRIDGE_GATE_PRODUCTION_PATH = (
    "src/covalent_ext/"
    "covapie_target_residue_atom_condition_runtime_bridge_gate_v1.py"
)
_RUNTIME_BRIDGE_GATE_PRODUCTION_SHA256 = (
    "3b7a9a485eecee122eefcbe8c2eb1f076d7711c9a77bb39ebf2e0249481d703e"
)
_DESIGN_COMMIT = "99425693056cd8800b9f93a19ea79a1e3e77c68e"
_IMPLEMENTATION_COMMIT = "2c504ff2eac0864c146129f4011d902fae5bef69"
_IMPLEMENTATION_PARENT = "99425693056cd8800b9f93a19ea79a1e3e77c68e"
_IMPLEMENTATION_TREE = "01a72bd9c3e313c2833cd22edae351a56abaec84"
_IMPLEMENTATION_SUBJECT = (
    "add CovaPIE target residue atom condition model consumption v1"
)
_GATE_EVIDENCE_MODE = "frozen_predecessor_commit_snapshot"
_GATE_CLAIMS_LIVE_SUCCESSOR_REPOSITORY_CALLERS = False
_SUCCESSOR_RUNTIME_STATE_REQUIRES_PHASE_SPECIFIC_GATE = True
_RUNTIME_TRANSPORT_SHA256 = (
    "835032d1b0a9d9af9abe0839e9be798f0d4f178bcd9d4af3323592c5e59aa597"
)
_RUNTIME_INTERNAL_SHA256 = (
    "035d45fb50a15e29b367a6af71d9ca28019b5d77c5d5ed82d253b78570e5750d"
)
_RUNTIME_SIZE = 12811
_CURRENT11_LINEAGE_PROJECTION_SHA256 = (
    "c4918fd0ee226de4bdee5aded27e06b615ca56c8f5085c044ef035cf172d71e9"
)
_CHECKPOINT_SHA256 = (
    "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
)
_CHECKPOINT_SIZE = 17861341
_MAX_FILE_BYTES = 32 * 1024 * 1024
_MAX_BUNDLE_BYTES = 2 * 1024 * 1024

_IMPLEMENTATION_FILES = {
    "lightning_modules.py": (
        "7431b5cf24d4f918df961eb97c75f2e296c8b3c523fb627063f3a6c2f08fc983"
    ),
    "equivariant_diffusion/dynamics.py": (
        "204370982696136884b50126dbd5211559d0caed51c92cb4d1ae62066ab00b8d"
    ),
    "equivariant_diffusion/conditional_model.py": (
        "a61dc44f376b3efc0365f558b09470f71b35dd2606c216f5abf0ba06d5a1b4a9"
    ),
    "equivariant_diffusion/en_diffusion.py": (
        "46a00db84d05ea568786b99b42b1b20c448cec8a99638d162b23b59794172b10"
    ),
    "src/covalent_ext/covapie_target_residue_atom_condition_checkpoint_migration_v1.py": (
        "0c47bdc136e41d16e62d87210333bb84e7295a57abd8ba9a377cf41d33ab76c8"
    ),
    "tests/test_covapie_target_residue_atom_condition_model_consumption_v1.py": (
        "afb53736011844cd3c669eb5f5be8d62f52dff6e3ef54d13cfce6bcafe1c394f"
    ),
    "scripts/check_covapie_target_residue_atom_condition_model_consumption_v1.py": (
        "6c50f3c7630f161419256b06da8da5fb2904d921f70d7edb52a0f0c12ac95d55"
    ),
    "docs/covapie_target_residue_atom_condition_model_consumption_v1_guide.md": (
        "c208d982fedb88e555d9c6c2d4375735f618b9dd46b3425308342cbbd394cc0b"
    ),
}
_DESIGN_MODEL_SHA256S = {
    "lightning_modules.py": "8d111f8c45d90cbdf6d0dcf7f4e4796bc7ebe0f1b0065e750eab0a16b4c01d5a",
    "equivariant_diffusion/dynamics.py": "16b008598de7c61c0b5575e3af02f9b1a9e6697559864df1591314e4b4ec6b9f",
    "equivariant_diffusion/conditional_model.py": "260bb941e05a3beaa0f1aef7aebba86aa2474d5f5db75637ec1498e3ad0e47b4",
    "equivariant_diffusion/en_diffusion.py": "841f95e8d47fd1bc27f50b76f605bf6d0369308c68c7a65b199e51b00b30d8ef",
}
_CALLER_SHA256S = {
    "generate_ligands.py": "8884e63ddb7f0fa84bd89bfd956fbefa10db687fa0cfc3380b85d06837be4474",
    "test.py": "954e63ade5e8b8f811897e40b22d81308451054753327cd9de2942c658dfd7bf",
    "optimize.py": "d51c32b3902accf24698f2b3abdfdf0e1a5d3150b90515a1b8d1b13d3e7d229b",
    "inpaint.py": "2d6cf0542c4b82e25eed19165d6f90d004ae4ced1db426962e47fb6086e085d9",
    "scripts/covalent_inpaint_demo.py": "1866dde2a7909fb431617dfa9f7de5a297b895de7930313655685823944f72a9",
    "colab/DiffSBDD.ipynb": "0d7fdc6a8377aa41e8d2104c39b2120964eee7f02b21c2bb56ca415dc889a123",
}
_PROTECTED_SHA256S = {
    "equivariant_diffusion/egnn_new.py": (
        "87001209a047133519371d4a01e3e2bdddc55bf3d41e9a7ff68a2664badc2333"
    ),
    "dataset.py": "d1c548185521692ca14be062e34d5bea617f8d3c89a22eaef4ddb13a52907c99",
}
_EXPECTED_COUNTS = (66, 104, 96, 208, 188, 278, 267, 257, 249, 261, 228)
_EXPECTED_FLAT = (49, 81, 182, 299, 505, 712, 988, 1260, 1516, 1766, 2058)
_LINEAGE_FIELDS = (
    "sample",
    "pdb_id",
    "source_adapter_record_sha256",
    "retained_pocket_node_count",
    "expected_local_true_index",
    "expected_flat_true_index",
    "runtime_mask_sample_id",
)

CANONICAL_MASK_SEMANTIC_NAMES = (
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
)

MODEL_CONSUMPTION_GATE_RESPONSE_FIELDS = (
    "model_consumption_gate_version",
    "source_runtime_bridge_gate_bundle_transport_sha256",
    "source_runtime_bridge_gate_bundle_sha256",
    "source_runtime_bridge_gate_commit",
    "source_model_consumption_design_commit",
    "source_model_consumption_implementation_commit",
    "source_model_consumption_implementation_parent",
    "source_model_consumption_implementation_tree",
    "source_lightning_module_sha256",
    "source_dynamics_sha256",
    "source_conditional_model_sha256",
    "source_en_diffusion_sha256",
    "source_checkpoint_migration_sha256",
    "source_model_consumption_test_sha256",
    "source_model_consumption_checker_sha256",
    "source_model_consumption_guide_sha256",
    "current11_record_count",
    "total_runtime_pocket_node_count",
    "total_runtime_indicator_true_count",
    "current11_lineage_projection_sha256",
    "checkpoint_sha256",
    "checkpoint_size",
    "disabled_profile_contract",
    "enabled_profile_contract",
    "base_to_conditioned_migration_contract",
    "top_level_condition_validation_contract",
    "current11_condition_validation_contract",
    "dynamics_threading_contract",
    "injection_contract",
    "deterministic_oracle_contract",
    "state_dict_compatibility_contract",
    "repository_cli_contract",
    "canonical_mask_semantic_names",
    "implementation_source_scope",
    "model_consumption_implemented",
    "indicator_passed_into_dynamics",
    "indicator_consumed_by_model",
    "model_consumption_gate_implemented",
    "ready_for_repository_cli_forwarding_design",
    "recommended_next_step",
    "training_or_parameter_update",
    "feature_semantics_audit_required_before_training",
    "model_consumption_gate_response_sha256",
)


class _DuplicateKeyError(ValueError):
    pass


class _CaptureEGNN(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.h: torch.Tensor | None = None
        self.x: torch.Tensor | None = None

    def forward(self, h, x, edges, **kwargs):
        self.h = h.detach().clone()
        self.x = x.detach().clone()
        return h, x


class _MigrationWrapper(nn.Module):
    def __init__(self, dynamics: nn.Module) -> None:
        super().__init__()
        self.ddpm = nn.Module()
        self.ddpm.dynamics = dynamics


class _FlagDynamics(nn.Module):
    def __init__(self, enabled: bool) -> None:
        super().__init__()
        self.target_residue_atom_conditioning = enabled


class _ValidationHarness(EnVariationalDiffusion):
    def __init__(self, enabled: bool) -> None:
        nn.Module.__init__(self)
        self.dynamics = _FlagDynamics(enabled)


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


def _reject_constant(_value: str) -> None:
    raise ValueError(_ERROR)


def _strict_json(payload: bytes) -> dict[str, Any]:
    try:
        if (
            type(payload) is not bytes
            or not payload
            or len(payload) >= _MAX_BUNDLE_BYTES
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\x00" in payload
            or payload.endswith((b"\n", b"\r"))
        ):
            raise ValueError(_ERROR)
        value = json.loads(
            payload.decode("utf-8", errors="strict"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
        if type(value) is not dict or _canonical_json_bytes(value) != payload:
            raise ValueError(_ERROR)
        return value
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _read_regular(path: Path, *, maximum: int = _MAX_FILE_BYTES) -> bytes:
    try:
        metadata = path.lstat()
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_size <= 0
            or metadata.st_size >= maximum
        ):
            raise ValueError(_ERROR)
        payload = path.read_bytes()
        if len(payload) != metadata.st_size:
            raise ValueError(_ERROR)
        return payload
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _git_snapshot_file_bytes(
    repo_root: Path,
    *,
    commit: str,
    relative_path: str,
    expected_sha256: str,
    maximum: int = _MAX_FILE_BYTES,
) -> bytes:
    """Return one immutable SHA-bound Git blob without repository mutation."""

    try:
        parsed = PurePosixPath(relative_path)
        if (
            not isinstance(repo_root, Path)
            or not repo_root.is_dir()
            or repo_root.is_symlink()
            or type(commit) is not str
            or re.fullmatch(r"[0-9a-f]{40}", commit) is None
            or type(relative_path) is not str
            or not relative_path
            or "\x00" in relative_path
            or parsed.is_absolute()
            or ".." in parsed.parts
            or parsed.as_posix() != relative_path
            or type(expected_sha256) is not str
            or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None
            or type(maximum) is not int
            or type(maximum) is bool
            or maximum <= 1
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
            if completed.returncode != 0 or completed.stderr != b"":
                raise ValueError(_ERROR)
            return completed.stdout

        if run("cat-file", "-t", object_spec) != b"blob\n":
            raise ValueError(_ERROR)
        size_payload = run("cat-file", "-s", object_spec)
        try:
            size = int(size_payload.decode("ascii").strip())
        except (UnicodeDecodeError, ValueError) as error:
            raise ValueError(_ERROR) from error
        if size <= 0 or size >= maximum:
            raise ValueError(_ERROR)
        payload = run("show", object_spec)
        if len(payload) != size or _sha256(payload) != expected_sha256:
            raise ValueError(_ERROR)
        return payload
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _git(repo_root: Path, arguments: Sequence[str]) -> bytes:
    completed = subprocess.run(
        ["git", *arguments], cwd=repo_root, check=False, capture_output=True
    )
    if completed.returncode != 0 or completed.stderr != b"":
        raise ValueError(_ERROR)
    return completed.stdout


def _is_ancestor(repo_root: Path, commit: str, ref: str) -> bool:
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, ref],
        cwd=repo_root,
        check=False,
        capture_output=True,
    )
    if completed.stdout != b"" or completed.stderr != b"":
        raise ValueError(_ERROR)
    if completed.returncode == 0:
        return True
    if completed.returncode == 1:
        return False
    raise ValueError(_ERROR)


def _method_map(source: str) -> dict[str, ast.FunctionDef]:
    result: dict[str, ast.FunctionDef] = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    result[f"{node.name}.{child.name}"] = child
    return result


def _method_boundary(
    before_source: str,
    after_source: str,
    *,
    changed_expected: set[str],
    added_expected: set[str] | None = None,
) -> bool:
    before = _method_map(before_source)
    after = _method_map(after_source)
    changed = {
        name
        for name in before.keys() & after
        if ast.dump(before[name], include_attributes=False)
        != ast.dump(after[name], include_attributes=False)
    }
    return (
        changed == changed_expected
        and set(after) - set(before) == (added_expected or set())
        and not (set(before) - set(after))
    )


def _loss_projection(source: str, qualified_name: str) -> list[str]:
    method = _method_map(source)[qualified_name]
    prefixes = (
        "delta_log",
        "error",
        "squared_error",
        "SNR_weight",
        "neg_log",
        "kl_prior",
        "loss",
        "log_p",
        "xh_lig_hat",
    )
    projection: list[str] = []
    for node in ast.walk(method):
        if not isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        names = {
            child.id
            for target in targets
            for child in ast.walk(target)
            if isinstance(child, ast.Name)
        }
        if any(name.startswith(prefixes) for name in names):
            projection.append(ast.dump(node, include_attributes=False))
    return sorted(projection)


def _profile_kwargs() -> dict[str, object]:
    return {
        "atom_nf": 10,
        "residue_nf": 10,
        "n_dims": 3,
        "joint_nf": 32,
        "device": "cpu",
        "hidden_nf": 128,
        "n_layers": 5,
        "attention": True,
        "tanh": True,
        "norm_constant": 1,
        "inv_sublayers": 1,
        "sin_embedding": False,
        "normalization_factor": 100,
        "aggregation_method": "sum",
        "edge_cutoff_ligand": None,
        "edge_cutoff_pocket": 5.0,
        "edge_cutoff_interaction": 5.0,
        "update_pocket_coords": False,
        "reflection_equivariant": False,
    }


def _tiny_dynamics() -> EGNNDynamics:
    return EGNNDynamics(
        atom_nf=2,
        residue_nf=2,
        n_dims=3,
        joint_nf=4,
        hidden_nf=8,
        n_layers=1,
        update_pocket_coords=False,
        target_residue_atom_conditioning=True,
    )


def _rejects_model(action) -> bool:
    try:
        action()
    except ValueError as error:
        return str(error) == _MODEL_ERROR
    return False


def _checkpoint_evidence(repo_root: Path) -> tuple[dict[str, Any], ...]:
    checkpoint_path = repo_root / "checkpoints/crossdocked_fullatom_cond.ckpt"
    checkpoint_bytes = _read_regular(checkpoint_path)
    if (
        len(checkpoint_bytes) != _CHECKPOINT_SIZE
        or _sha256(checkpoint_bytes) != _CHECKPOINT_SHA256
    ):
        raise ValueError(_ERROR)
    checkpoint = torch.load(
        io.BytesIO(checkpoint_bytes), map_location="cpu", weights_only=False
    )
    if type(checkpoint) is not dict or not isinstance(checkpoint.get("state_dict"), dict):
        raise ValueError(_ERROR)
    base_dynamics = {
        key.removeprefix("ddpm.dynamics."): value
        for key, value in checkpoint["state_dict"].items()
        if key.startswith("ddpm.dynamics.")
    }
    if len(base_dynamics) != 120:
        raise ValueError(_ERROR)

    disabled = EGNNDynamics(**_profile_kwargs())
    enabled = EGNNDynamics(
        **_profile_kwargs(), target_residue_atom_conditioning=True
    )
    disabled_state = disabled.state_dict()
    enabled_state = enabled.state_dict()
    strict_result = disabled.load_state_dict(base_dynamics, strict=True)
    parameter = enabled.target_residue_atom_condition_embedding

    disabled_contract = {
        "target_residue_atom_conditioning": (
            disabled.target_residue_atom_conditioning
        ),
        "new_parameter_key_absent": _PARAMETER not in disabled_state,
        "state_key_count": len(disabled_state),
        "checkpoint_dynamics_strict_load": (
            list(strict_result.missing_keys) == []
            and list(strict_result.unexpected_keys) == []
        ),
        "missing_keys": list(strict_result.missing_keys),
        "unexpected_keys": list(strict_result.unexpected_keys),
    }
    enabled_contract = {
        "target_residue_atom_conditioning": enabled.target_residue_atom_conditioning,
        "exactly_one_new_parameter": (
            set(enabled_state) - set(disabled_state) == {_PARAMETER}
            and not (set(disabled_state) - set(enabled_state))
        ),
        "parameter_name": _PARAMETER,
        "parameter_shape": list(parameter.shape),
        "parameter_all_zeros": int(torch.count_nonzero(parameter).item()) == 0,
        "parameter_requires_grad": parameter.requires_grad,
        "existing_keys_unchanged": (
            set(disabled_state) == set(base_dynamics)
            and set(disabled_state) <= set(enabled_state)
        ),
        "existing_shapes_unchanged": all(
            disabled_state[key].shape == enabled_state[key].shape == value.shape
            for key, value in base_dynamics.items()
        ),
    }

    wrapper = _MigrationWrapper(enabled)
    prefixed_base = {
        f"ddpm.dynamics.{key}": value for key, value in base_dynamics.items()
    }
    mapping_keys = tuple(prefixed_base)
    mapping_ids = {key: id(value) for key, value in prefixed_base.items()}
    mapping_snapshots = {key: value.detach().clone() for key, value in prefixed_base.items()}
    report = migration.load_covapie_base_state_dict_into_target_residue_conditioned_model_v1(
        model=wrapper, base_state_dict=prefixed_base
    )
    shared_unchanged = all(
        id(prefixed_base[key]) == mapping_ids[key]
        and torch.equal(prefixed_base[key], mapping_snapshots[key])
        for key in mapping_keys
    )

    def migration_rejected(candidate: Mapping[str, torch.Tensor], model=wrapper) -> bool:
        return _rejects_model(
            lambda: migration.load_covapie_base_state_dict_into_target_residue_conditioned_model_v1(
                model=model, base_state_dict=candidate
            )
        )

    first_key = next(iter(prefixed_base))
    missing = dict(prefixed_base)
    missing.pop(first_key)
    unexpected = dict(prefixed_base)
    unexpected["unexpected"] = torch.zeros(1)
    shape_key = next(key for key, value in prefixed_base.items() if value.numel() > 1)
    shape_drift = dict(prefixed_base)
    shape_drift[shape_key] = shape_drift[shape_key].reshape(-1)[:-1]
    dtype_key = next(
        key for key, value in prefixed_base.items() if value.is_floating_point()
    )
    dtype_drift = dict(prefixed_base)
    dtype_drift[dtype_key] = dtype_drift[dtype_key].to(torch.float64)
    nonzero_enabled = EGNNDynamics(
        **_profile_kwargs(), target_residue_atom_conditioning=True
    )
    nonzero_enabled.target_residue_atom_condition_embedding = nn.Parameter(
        torch.ones(32)
    )
    nonzero_wrapper = _MigrationWrapper(nonzero_enabled)

    migration_contract = {
        "exactly_one_key_filled": report["filled_state_keys"] == [_NEW_STATE_KEY],
        "filled_key": _NEW_STATE_KEY,
        "final_strict_load": (
            report["strict_load"] is True
            and report["missing_keys"] == []
            and report["unexpected_keys"] == []
        ),
        "missing_keys": report["missing_keys"],
        "unexpected_keys": report["unexpected_keys"],
        "base_mapping_unchanged": tuple(prefixed_base) == mapping_keys,
        "shared_tensors_unchanged": shared_unchanged,
        "disk_checkpoint_unchanged": (
            _read_regular(checkpoint_path) == checkpoint_bytes
        ),
        "blanket_strict_false": False,
        "additional_missing_rejected": migration_rejected(missing),
        "unexpected_rejected": migration_rejected(unexpected),
        "shape_drift_rejected": migration_rejected(shape_drift),
        "dtype_drift_rejected": migration_rejected(dtype_drift),
        "nonzero_new_parameter_rejected": migration_rejected(
            prefixed_base, nonzero_wrapper
        ),
    }
    state_contract = {
        "base_state_key_count": len(base_dynamics),
        "disabled_state_key_count": len(disabled_state),
        "enabled_state_key_count": len(enabled_state),
        "atom_nf": enabled.atom_encoder[0].in_features,
        "residue_nf": enabled.residue_encoder[0].in_features,
        "joint_nf": enabled.node_nf - 1,
        "condition_time": enabled.condition_time,
        "checkpoint_sha256_verified_before_and_after": (
            _sha256(checkpoint_bytes) == _CHECKPOINT_SHA256
            and _read_regular(checkpoint_path) == checkpoint_bytes
        ),
    }
    return disabled_contract, enabled_contract, migration_contract, state_contract


def _fresh_current11(
    counts: Sequence[int], flat_indices: Sequence[int]
) -> tuple[dict[str, torch.Tensor], torch.Tensor]:
    size = torch.tensor(counts, dtype=torch.long)
    mask = torch.repeat_interleave(torch.arange(len(size), dtype=torch.long), size)
    indicator = torch.zeros(int(size.sum().item()), dtype=torch.bool)
    indicator[list(flat_indices)] = True
    return {
        "x": torch.zeros(len(indicator), 3),
        "one_hot": torch.zeros(len(indicator), 10),
        "size": size,
        "mask": mask,
    }, indicator


def _validation_evidence(
    runtime_bundle: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    records = runtime_bundle["current11_records"]
    counts = tuple(record["retained_pocket_node_count"] for record in records)
    flat_indices = tuple(record["expected_flat_true_index"] for record in records)
    if counts != _EXPECTED_COUNTS or flat_indices != _EXPECTED_FLAT:
        raise ValueError(_ERROR)
    pocket, indicator = _fresh_current11(counts, flat_indices)
    snapshots = {key: value.detach().clone() for key, value in pocket.items()}
    indicator_snapshot = indicator.detach().clone()
    enabled = _ValidationHarness(True)
    resolved = enabled._resolve_covapie_target_residue_atom_condition_indicator_v1(
        pocket, indicator
    )

    def rejected(candidate_pocket, candidate) -> bool:
        return _rejects_model(
            lambda: enabled._resolve_covapie_target_residue_atom_condition_indicator_v1(
                candidate_pocket, candidate
            )
        )

    mask_rejections: dict[str, bool] = {}
    for dtype in (torch.float32, torch.bool, torch.int32):
        candidate, valid = _fresh_current11(counts, flat_indices)
        candidate["mask"] = candidate["mask"].to(dtype=dtype)
        mask_rejections[str(dtype)] = rejected(candidate, valid)
    size_rejections: dict[str, bool] = {}
    for dtype in (torch.float32, torch.bool, torch.int32):
        candidate, valid = _fresh_current11(counts, flat_indices)
        candidate["size"] = candidate["size"].to(dtype=dtype)
        size_rejections[str(dtype)] = rejected(candidate, valid)

    all_false_pocket, all_false = _fresh_current11(counts, flat_indices)
    all_false.zero_()
    zero_pocket, zero_sample = _fresh_current11(counts, flat_indices)
    zero_sample[flat_indices[0]] = False
    multiple_pocket, multiple_sample = _fresh_current11(counts, flat_indices)
    additional = 0 if flat_indices[0] != 0 else 1
    multiple_sample[additional] = True
    dual_int_pocket, dual_bool = _fresh_current11(counts, flat_indices)
    dual_int_pocket[_FIELD] = dual_bool
    dual_float_pocket, dual_bool_float = _fresh_current11(counts, flat_indices)
    dual_float_pocket[_FIELD] = dual_bool_float

    top_level_contract = {
        "pocket_mask_long_dtype_required": all(mask_rejections.values()),
        "pocket_size_long_dtype_required": all(size_rejections.values()),
        "float_mask_rejected": mask_rejections["torch.float32"],
        "bool_mask_rejected": mask_rejections["torch.bool"],
        "int32_mask_rejected": mask_rejections["torch.int32"],
        "float_size_rejected": size_rejections["torch.float32"],
        "bool_size_rejected": size_rejections["torch.bool"],
        "int32_size_rejected": size_rejections["torch.int32"],
        "present_all_false_rejected": rejected(all_false_pocket, all_false),
        "zero_target_sample_rejected": rejected(zero_pocket, zero_sample),
        "multiple_target_sample_rejected": rejected(
            multiple_pocket, multiple_sample
        ),
        "bool_int_dual_source_pseudo_equality_rejected": rejected(
            dual_int_pocket, dual_bool.to(torch.long)
        ),
        "bool_float_dual_source_pseudo_equality_rejected": rejected(
            dual_float_pocket, dual_bool_float.to(torch.float32)
        ),
        "dual_source_exact_bool_semantics_required": True,
    }
    current11_contract = {
        "accepted": resolved is indicator,
        "returned_object_is_original_indicator": resolved is indicator,
        "one_true_per_sample": all(
            int(indicator[pocket["mask"] == index].sum().item()) == 1
            for index in range(len(counts))
        ),
        "inputs_unchanged": (
            torch.equal(indicator, indicator_snapshot)
            and all(torch.equal(pocket[key], value) for key, value in snapshots.items())
        ),
        "pocket_x_shape": list(pocket["x"].shape),
        "pocket_one_hot_shape": list(pocket["one_hot"].shape),
        "pocket_size_dtype": str(pocket["size"].dtype),
        "pocket_mask_dtype": str(pocket["mask"].dtype),
        "indicator_dtype": str(indicator.dtype),
        "indicator_true_count": int(indicator.sum().item()),
        "complete_egnn_forward_executed": False,
    }
    return top_level_contract, current11_contract


def _injection_once(seed: int) -> dict[str, bool]:
    torch.manual_seed(seed)
    model = _tiny_dynamics()
    capture = _CaptureEGNN()
    model.egnn = capture
    model.eval()
    atoms = torch.tensor(
        [[0.0, 0.0, 0.0, 1.0, 0.0], [1.0, 0.0, 0.0, 0.0, 1.0]]
    )
    residues = torch.tensor(
        [
            [0.0, 1.0, 0.0, 1.0, 0.0],
            [0.0, 2.0, 0.0, 0.0, 1.0],
            [0.0, 3.0, 0.0, 1.0, 0.0],
        ]
    )
    t = torch.tensor([0.25])
    atom_mask = torch.zeros(2, dtype=torch.long)
    residue_mask = torch.zeros(3, dtype=torch.long)
    inputs = (atoms, residues, t, atom_mask, residue_mask)
    absent = model(*inputs)
    legacy_h = capture.h.detach().clone()
    legacy_x = capture.x.detach().clone()
    indicator = torch.tensor([False, True, False])
    present_zero = model(
        *inputs, pocket_target_residue_atom_condition_indicator=indicator
    )
    zero_parity = all(
        torch.equal(left, right) for left, right in zip(absent, present_zero)
    )
    embedding = torch.tensor([1.0, 2.0, 3.0, 4.0])
    model.target_residue_atom_condition_embedding = nn.Parameter(embedding)
    model(*inputs, pocket_target_residue_atom_condition_indicator=indicator)
    conditioned_h = capture.h.detach().clone()
    conditioned_x = capture.x.detach().clone()
    target_row = len(atoms) + 1
    expected_h = legacy_h.clone()
    expected_h[target_row, :4] = expected_h[target_row, :4] + embedding
    non_target_pocket_rows = [len(atoms), len(atoms) + 2]
    return {
        "zero_initialization_parity": zero_parity,
        "nonzero_target_row_changed": (
            not torch.equal(conditioned_h[target_row], legacy_h[target_row])
            and torch.equal(conditioned_h[target_row], expected_h[target_row])
        ),
        "non_target_pocket_rows_unchanged": torch.equal(
            conditioned_h[non_target_pocket_rows], legacy_h[non_target_pocket_rows]
        ),
        "ligand_rows_not_directly_injected": torch.equal(
            conditioned_h[: len(atoms)], legacy_h[: len(atoms)]
        ),
        "coordinates_unchanged": (
            torch.equal(conditioned_x, legacy_x)
            and torch.equal(
                conditioned_x,
                torch.cat((atoms[:, :3], residues[:, :3]), dim=0),
            )
        ),
        "direct_expected_complete_hidden_match": torch.equal(
            conditioned_h, expected_h
        ),
    }


def _injection_evidence() -> tuple[dict[str, Any], dict[str, Any]]:
    rng_state_before = torch.random.get_rng_state().clone()
    try:
        try:
            seeds = tuple(range(16))
            results = tuple(_injection_once(seed) for seed in seeds)
            keys = tuple(results[0])
            injection_contract = {
                key: all(result[key] for result in results) for key in keys
            }
            injection_contract["selected_injection_point_exact"] = True
        finally:
            torch.random.set_rng_state(rng_state_before)
        cpu_rng_state_restored = torch.equal(
            torch.random.get_rng_state(), rng_state_before
        )
        if not cpu_rng_state_restored:
            raise ValueError(_ERROR)
        oracle_contract = {
            "fixed_seed_count": len(seeds),
            "fixed_seeds": list(seeds),
            "multi_seed_stable": all(all(result.values()) for result in results),
            "cpu_rng_state_restored": cpu_rng_state_restored,
            "direct_expected_hidden_used": True,
            "backward_executed": False,
            "optimizer_step_executed": False,
        }
        return injection_contract, oracle_contract
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _runtime_bridge_gate_source_evidence(repo_root: Path) -> dict[str, bool]:
    """Bind the runtime-gate commit, production blob, import, and lineage."""

    try:
        commit_exists = (
            _git(
                repo_root,
                ["cat-file", "-e", f"{_RUNTIME_BRIDGE_GATE_COMMIT}^{{commit}}"],
            )
            == b""
        )
        parent_bound = _git(
            repo_root,
            ["show", "-s", "--format=%P", _RUNTIME_BRIDGE_GATE_COMMIT],
        ) == f"{_RUNTIME_BRIDGE_GATE_PARENT}\n".encode()
        subject_bound = _git(
            repo_root,
            ["show", "-s", "--format=%s", _RUNTIME_BRIDGE_GATE_COMMIT],
        ) == f"{_RUNTIME_BRIDGE_GATE_SUBJECT}\n".encode()
        production_path = repo_root / _RUNTIME_BRIDGE_GATE_PRODUCTION_PATH
        working_bytes = _read_regular(production_path)
        committed_bytes = _git(
            repo_root,
            [
                "show",
                f"{_RUNTIME_BRIDGE_GATE_COMMIT}:"
                f"{_RUNTIME_BRIDGE_GATE_PRODUCTION_PATH}",
            ],
        )
        working_sha256_bound = (
            _sha256(working_bytes) == _RUNTIME_BRIDGE_GATE_PRODUCTION_SHA256
        )
        committed_sha256_bound = (
            _sha256(committed_bytes) == _RUNTIME_BRIDGE_GATE_PRODUCTION_SHA256
        )
        working_and_committed_bytes_equal = working_bytes == committed_bytes
        imported_module_path_bound = (
            Path(runtime_gate.__file__).resolve(strict=True)
            == production_path.resolve(strict=True)
        )
        evidence = {
            "runtime_gate_commit_exists": commit_exists,
            "runtime_gate_unique_parent_bound": parent_bound,
            "runtime_gate_subject_bound": subject_bound,
            "runtime_gate_working_sha256_bound": working_sha256_bound,
            "runtime_gate_committed_sha256_bound": committed_sha256_bound,
            "runtime_gate_working_and_committed_bytes_equal": (
                working_and_committed_bytes_equal
            ),
            "runtime_gate_is_implementation_ancestor": _is_ancestor(
                repo_root, _RUNTIME_BRIDGE_GATE_COMMIT, _IMPLEMENTATION_COMMIT
            ),
            "runtime_gate_is_head_ancestor": _is_ancestor(
                repo_root, _RUNTIME_BRIDGE_GATE_COMMIT, "HEAD"
            ),
            "runtime_gate_is_origin_main_ancestor": _is_ancestor(
                repo_root, _RUNTIME_BRIDGE_GATE_COMMIT, "origin/main"
            ),
            "runtime_gate_imported_module_path_bound": imported_module_path_bound,
        }
        if not _all_true(evidence):
            raise ValueError(_ERROR)
        return evidence
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _source_evidence(repo_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    parents = _git(repo_root, ["show", "-s", "--format=%P", _IMPLEMENTATION_COMMIT])
    tree = _git(repo_root, ["show", "-s", "--format=%T", _IMPLEMENTATION_COMMIT])
    subject = _git(repo_root, ["show", "-s", "--format=%s", _IMPLEMENTATION_COMMIT])
    raw_commit = _git(repo_root, ["cat-file", "commit", _IMPLEMENTATION_COMMIT])
    message = raw_commit.split(b"\n\n", 1)[1]
    paths = _git(
        repo_root,
        ["diff-tree", "--no-commit-id", "--name-only", "-r", _IMPLEMENTATION_COMMIT],
    ).decode("utf-8", errors="strict").splitlines()
    shortstat = _git(
        repo_root,
        ["diff", "--shortstat", _IMPLEMENTATION_PARENT, _IMPLEMENTATION_COMMIT],
    )
    if (
        parents != f"{_IMPLEMENTATION_PARENT}\n".encode()
        or tree != f"{_IMPLEMENTATION_TREE}\n".encode()
        or subject != f"{_IMPLEMENTATION_SUBJECT}\n".encode()
        or message != f"{_IMPLEMENTATION_SUBJECT}\n".encode()
        or len(paths) != len(_IMPLEMENTATION_FILES)
        or set(paths) != set(_IMPLEMENTATION_FILES)
        or shortstat != b" 8 files changed, 2704 insertions(+), 41 deletions(-)\n"
        or not _is_ancestor(repo_root, _IMPLEMENTATION_COMMIT, "HEAD")
        or not _is_ancestor(repo_root, _IMPLEMENTATION_COMMIT, "origin/main")
    ):
        raise ValueError(_ERROR)

    sources: dict[str, str] = {}
    for relative_path, expected_sha256 in _IMPLEMENTATION_FILES.items():
        committed = _git_snapshot_file_bytes(
            repo_root,
            commit=_IMPLEMENTATION_COMMIT,
            relative_path=relative_path,
            expected_sha256=expected_sha256,
        )
        if relative_path.endswith(".py"):
            sources[relative_path] = committed.decode("utf-8", errors="strict")

    for relative_path, expected_sha256 in _PROTECTED_SHA256S.items():
        design_blob = _git_snapshot_file_bytes(
            repo_root,
            commit=_DESIGN_COMMIT,
            relative_path=relative_path,
            expected_sha256=expected_sha256,
        )
        implementation_blob = _git_snapshot_file_bytes(
            repo_root,
            commit=_IMPLEMENTATION_COMMIT,
            relative_path=relative_path,
            expected_sha256=expected_sha256,
        )
        if design_blob != implementation_blob:
            raise ValueError(_ERROR)
    for relative_path, expected_sha256 in _CALLER_SHA256S.items():
        _git_snapshot_file_bytes(
            repo_root,
            commit=_IMPLEMENTATION_COMMIT,
            relative_path=relative_path,
            expected_sha256=expected_sha256,
        )

    before = {
        path: _git_snapshot_file_bytes(
            repo_root,
            commit=_DESIGN_COMMIT,
            relative_path=path,
            expected_sha256=expected_sha256,
        ).decode("utf-8", errors="strict")
        for path, expected_sha256 in _DESIGN_MODEL_SHA256S.items()
    }
    boundaries = {
        "lightning_only_authorized_change": _method_boundary(
            before["lightning_modules.py"],
            sources["lightning_modules.py"],
            changed_expected={"LigandPocketDDPM.__init__"},
        ),
        "dynamics_only_authorized_changes": _method_boundary(
            before["equivariant_diffusion/dynamics.py"],
            sources["equivariant_diffusion/dynamics.py"],
            changed_expected={"EGNNDynamics.__init__", "EGNNDynamics.forward"},
        ),
        "conditional_only_authorized_changes": _method_boundary(
            before["equivariant_diffusion/conditional_model.py"],
            sources["equivariant_diffusion/conditional_model.py"],
            changed_expected={
                "ConditionalDDPM.sample_p_xh_given_z0",
                "ConditionalDDPM.forward",
                "ConditionalDDPM.diversify",
                "ConditionalDDPM.sample_p_zs_given_zt",
                "ConditionalDDPM.sample_given_pocket",
                "ConditionalDDPM.inpaint",
                "SimpleConditionalDDPM.forward",
                "SimpleConditionalDDPM.sample_given_pocket",
            },
        ),
        "en_diffusion_only_authorized_changes": _method_boundary(
            before["equivariant_diffusion/en_diffusion.py"],
            sources["equivariant_diffusion/en_diffusion.py"],
            changed_expected={
                "EnVariationalDiffusion.forward",
                "EnVariationalDiffusion.sample_p_zs_given_zt",
                "EnVariationalDiffusion.sample_p_xh_given_z0",
                "EnVariationalDiffusion.inpaint",
            },
            added_expected={
                "EnVariationalDiffusion._validate_covapie_target_residue_atom_condition_indicator_v1",
                "EnVariationalDiffusion._resolve_covapie_target_residue_atom_condition_indicator_v1",
            },
        ),
    }
    calls: list[ast.Call] = []
    for path in (
        "equivariant_diffusion/conditional_model.py",
        "equivariant_diffusion/en_diffusion.py",
    ):
        calls.extend(
            node
            for node in ast.walk(ast.parse(sources[path]))
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "self"
            and node.func.attr == "dynamics"
        )
    dynamics_method = _method_map(sources["equivariant_diffusion/dynamics.py"])[
        "EGNNDynamics.forward"
    ]
    encoder_line = next(
        node.lineno
        for node in ast.walk(dynamics_method)
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "h_residues" for target in node.targets)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and node.value.func.attr == "residue_encoder"
    )
    injection_if = next(
        node
        for node in dynamics_method.body
        if isinstance(node, ast.If)
        and _FIELD in ast.unparse(node.test)
        and _PARAMETER in ast.unparse(node)
    )
    concatenate_line = next(
        node.lineno
        for node in dynamics_method.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "h" for target in node.targets)
        and "torch.cat" in ast.unparse(node.value)
    )
    time_line = next(
        node.lineno
        for node in dynamics_method.body
        if isinstance(node, ast.If) and "self.condition_time" in ast.unparse(node.test)
    )
    en_before = _method_map(before["equivariant_diffusion/en_diffusion.py"])
    en_after = _method_map(sources["equivariant_diffusion/en_diffusion.py"])
    loss_unchanged = all(
        _loss_projection(before[path], method)
        == _loss_projection(sources[path], method)
        for path, method in (
            ("equivariant_diffusion/conditional_model.py", "ConditionalDDPM.forward"),
            ("equivariant_diffusion/en_diffusion.py", "EnVariationalDiffusion.forward"),
        )
    )
    dynamics_contract = {
        **boundaries,
        "dynamics_call_site_count": len(calls),
        "all_eight_sites_thread_long_semantic_keyword": (
            len(calls) == 8
            and all([keyword.arg for keyword in call.keywords] == [_FIELD] for call in calls)
        ),
        "selected_injection_point_exact": (
            encoder_line < injection_if.lineno < concatenate_line < time_line
        ),
        "loss_computation_ast_unchanged": loss_unchanged,
        "normalization_ast_unchanged": (
            ast.dump(en_before["EnVariationalDiffusion.normalize"], include_attributes=False)
            == ast.dump(en_after["EnVariationalDiffusion.normalize"], include_attributes=False)
        ),
        "noise_representation_ast_unchanged": (
            ast.dump(en_before["EnVariationalDiffusion.noised_representation"], include_attributes=False)
            == ast.dump(en_after["EnVariationalDiffusion.noised_representation"], include_attributes=False)
        ),
        "unconditional_joint_sample_ast_unchanged": (
            ast.dump(en_before["EnVariationalDiffusion.sample"], include_attributes=False)
            == ast.dump(en_after["EnVariationalDiffusion.sample"], include_attributes=False)
        ),
        "egnn_new_unchanged": True,
        "dataset_unchanged": True,
    }
    implementation_contract = {
        "implementation_commit_subject_bound": True,
        "implementation_commit_body_empty": True,
        "implementation_commit_single_parent": True,
        "implementation_commit_tree_bound": True,
        "implementation_commit_is_head_ancestor": True,
        "implementation_commit_is_origin_main_ancestor": True,
        "implementation_eight_file_scope_bound": True,
        "implementation_stat_bound": True,
        "implementation_commit_snapshot_bytes_bound": True,
    }
    return dynamics_contract, implementation_contract


def _runtime_bundle_evidence(payload: bytes) -> tuple[dict[str, Any], str]:
    if len(payload) != _RUNTIME_SIZE or _sha256(payload) != _RUNTIME_TRANSPORT_SHA256:
        raise ValueError(_ERROR)
    bundle = _strict_json(payload)
    try:
        runtime_gate._validate_bundle(bundle, require_field_order=False)
    except Exception as error:
        raise ValueError(_ERROR) from error
    if (
        bundle.get("runtime_bridge_gate_bundle_sha256") != _RUNTIME_INTERNAL_SHA256
        or bundle.get("source_runtime_bridge_commit")
        != "75589a94235dde2d0943606e58a1f2216b31d3b2"
        or bundle.get("current11_record_count") != 11
        or bundle.get("total_runtime_pocket_node_count") != 2202
        or bundle.get("total_runtime_indicator_true_count") != 11
    ):
        raise ValueError(_ERROR)
    projection = tuple(
        {field: record[field] for field in _LINEAGE_FIELDS}
        for record in bundle["current11_records"]
    )
    projection_sha256 = _sha256(_canonical_json_bytes(projection))
    if projection_sha256 != _CURRENT11_LINEAGE_PROJECTION_SHA256:
        raise ValueError(_ERROR)
    return bundle, projection_sha256


def _all_true(mapping: Mapping[str, Any], *, exempt: set[str] | None = None) -> bool:
    omitted = exempt or set()
    return all(value is True for key, value in mapping.items() if key not in omitted)


def _validate_response(response: Mapping[str, Any], *, require_order: bool) -> bool:
    try:
        if (
            type(response) is not dict
            or len(response) != 43
            or set(response) != set(MODEL_CONSUMPTION_GATE_RESPONSE_FIELDS)
            or (require_order and tuple(response) != MODEL_CONSUMPTION_GATE_RESPONSE_FIELDS)
            or response["model_consumption_gate_version"] != _VERSION
            or response["model_consumption_gate_response_sha256"]
            != _sha256(
                _canonical_json_bytes(
                    {
                        field: response[field]
                        for field in MODEL_CONSUMPTION_GATE_RESPONSE_FIELDS
                        if field != "model_consumption_gate_response_sha256"
                    }
                )
            )
        ):
            raise ValueError(_ERROR)
        return True
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def evaluate_covapie_target_residue_atom_condition_model_consumption_gate_v1(
    *,
    source_runtime_bridge_gate_bundle: bytes,
    repo_root: Path,
) -> dict[str, Any]:
    """Evaluate the formal gate without writing files or changing CPU RNG."""

    entry_rng_state = torch.random.get_rng_state().clone()
    try:
        if (
            type(source_runtime_bridge_gate_bundle) is not bytes
            or type(repo_root) is not type(Path())
            or not repo_root.is_dir()
            or repo_root.is_symlink()
        ):
            raise ValueError(_ERROR)
        runtime_bundle, lineage_sha256 = _runtime_bundle_evidence(
            source_runtime_bridge_gate_bundle
        )
        runtime_gate_source_evidence = _runtime_bridge_gate_source_evidence(
            repo_root
        )
        dynamics_contract, implementation_contract = _source_evidence(repo_root)
        (
            disabled_contract,
            enabled_contract,
            migration_contract,
            state_contract,
        ) = _checkpoint_evidence(repo_root)
        top_validation, current11_validation = _validation_evidence(runtime_bundle)
        injection_contract, oracle_contract = _injection_evidence()
        torch.random.set_rng_state(entry_rng_state)
        public_api_rng_state_restored = torch.equal(
            torch.random.get_rng_state(), entry_rng_state
        )
        if not public_api_rng_state_restored:
            raise ValueError(_ERROR)

        disabled_ready = (
            disabled_contract["target_residue_atom_conditioning"] is False
            and disabled_contract["new_parameter_key_absent"] is True
            and disabled_contract["state_key_count"] == 120
            and disabled_contract["checkpoint_dynamics_strict_load"] is True
            and disabled_contract["missing_keys"] == []
            and disabled_contract["unexpected_keys"] == []
        )
        enabled_ready = (
            enabled_contract["target_residue_atom_conditioning"] is True
            and enabled_contract["exactly_one_new_parameter"] is True
            and enabled_contract["parameter_name"] == _PARAMETER
            and enabled_contract["parameter_shape"] == [32]
            and enabled_contract["parameter_all_zeros"] is True
            and enabled_contract["parameter_requires_grad"] is True
            and enabled_contract["existing_keys_unchanged"] is True
            and enabled_contract["existing_shapes_unchanged"] is True
        )
        migration_ready = (
            _all_true(
                migration_contract,
                exempt={"filled_key", "missing_keys", "unexpected_keys", "blanket_strict_false"},
            )
            and migration_contract["filled_key"] == _NEW_STATE_KEY
            and migration_contract["missing_keys"] == []
            and migration_contract["unexpected_keys"] == []
            and migration_contract["blanket_strict_false"] is False
        )
        validation_ready = _all_true(top_validation) and all(
            (
                current11_validation["accepted"] is True,
                current11_validation["returned_object_is_original_indicator"] is True,
                current11_validation["one_true_per_sample"] is True,
                current11_validation["inputs_unchanged"] is True,
                current11_validation["pocket_x_shape"] == [2202, 3],
                current11_validation["pocket_one_hot_shape"] == [2202, 10],
                current11_validation["pocket_size_dtype"] == "torch.int64",
                current11_validation["pocket_mask_dtype"] == "torch.int64",
                current11_validation["indicator_dtype"] == "torch.bool",
                current11_validation["indicator_true_count"] == 11,
                current11_validation["complete_egnn_forward_executed"] is False,
            )
        )
        threading_ready = _all_true(
            dynamics_contract, exempt={"dynamics_call_site_count"}
        ) and dynamics_contract["dynamics_call_site_count"] == 8
        injection_ready = _all_true(injection_contract)
        oracle_ready = (
            oracle_contract["fixed_seed_count"] == 16
            and oracle_contract["fixed_seeds"] == list(range(16))
            and oracle_contract["multi_seed_stable"] is True
            and oracle_contract["cpu_rng_state_restored"] is True
            and oracle_contract["direct_expected_hidden_used"] is True
            and oracle_contract["backward_executed"] is False
            and oracle_contract["optimizer_step_executed"] is False
        )
        source_ready = _all_true(implementation_contract)
        runtime_gate_source_ready = _all_true(runtime_gate_source_evidence)
        state_ready = (
            state_contract["base_state_key_count"] == 120
            and state_contract["disabled_state_key_count"] == 120
            and state_contract["enabled_state_key_count"] == 121
            and state_contract["atom_nf"] == 10
            and state_contract["residue_nf"] == 10
            and state_contract["joint_nf"] == 32
            and state_contract["condition_time"] is True
            and state_contract["checkpoint_sha256_verified_before_and_after"] is True
        )
        repository_cli_contract = {
            "repository_cli_paths_unchanged": True,
            "repository_cli_selector_forwarding_implemented": False,
            "caller_count": len(_CALLER_SHA256S),
            "caller_sha256s_bound": True,
        }
        training_or_parameter_update = False
        indicator_passed = threading_ready
        indicator_consumed = (
            injection_ready
            and dynamics_contract["selected_injection_point_exact"] is True
        )
        model_consumption_implemented = (
            indicator_passed and indicator_consumed and validation_ready
        )
        gate_implemented = all(
            (
                source_ready,
                runtime_gate_source_ready,
                disabled_ready,
                enabled_ready,
                migration_ready,
                validation_ready,
                threading_ready,
                injection_ready,
                oracle_ready,
                state_ready,
                model_consumption_implemented,
                repository_cli_contract["repository_cli_paths_unchanged"],
                not repository_cli_contract[
                    "repository_cli_selector_forwarding_implemented"
                ],
                len(CANONICAL_MASK_SEMANTIC_NAMES) == 5,
                "scaffold_only" in CANONICAL_MASK_SEMANTIC_NAMES,
                not training_or_parameter_update,
            )
        )
        ready_for_cli_design = (
            gate_implemented
            and model_consumption_implemented
            and repository_cli_contract["repository_cli_paths_unchanged"]
            and not repository_cli_contract[
                "repository_cli_selector_forwarding_implemented"
            ]
            and not training_or_parameter_update
        )
        values: dict[str, Any] = {
            "model_consumption_gate_version": _VERSION,
            "source_runtime_bridge_gate_bundle_transport_sha256": _RUNTIME_TRANSPORT_SHA256,
            "source_runtime_bridge_gate_bundle_sha256": _RUNTIME_INTERNAL_SHA256,
            "source_runtime_bridge_gate_commit": _RUNTIME_BRIDGE_GATE_COMMIT,
            "source_model_consumption_design_commit": _DESIGN_COMMIT,
            "source_model_consumption_implementation_commit": _IMPLEMENTATION_COMMIT,
            "source_model_consumption_implementation_parent": _IMPLEMENTATION_PARENT,
            "source_model_consumption_implementation_tree": _IMPLEMENTATION_TREE,
            "source_lightning_module_sha256": _IMPLEMENTATION_FILES["lightning_modules.py"],
            "source_dynamics_sha256": _IMPLEMENTATION_FILES["equivariant_diffusion/dynamics.py"],
            "source_conditional_model_sha256": _IMPLEMENTATION_FILES["equivariant_diffusion/conditional_model.py"],
            "source_en_diffusion_sha256": _IMPLEMENTATION_FILES["equivariant_diffusion/en_diffusion.py"],
            "source_checkpoint_migration_sha256": _IMPLEMENTATION_FILES["src/covalent_ext/covapie_target_residue_atom_condition_checkpoint_migration_v1.py"],
            "source_model_consumption_test_sha256": _IMPLEMENTATION_FILES["tests/test_covapie_target_residue_atom_condition_model_consumption_v1.py"],
            "source_model_consumption_checker_sha256": _IMPLEMENTATION_FILES["scripts/check_covapie_target_residue_atom_condition_model_consumption_v1.py"],
            "source_model_consumption_guide_sha256": _IMPLEMENTATION_FILES["docs/covapie_target_residue_atom_condition_model_consumption_v1_guide.md"],
            "current11_record_count": runtime_bundle["current11_record_count"],
            "total_runtime_pocket_node_count": runtime_bundle["total_runtime_pocket_node_count"],
            "total_runtime_indicator_true_count": runtime_bundle["total_runtime_indicator_true_count"],
            "current11_lineage_projection_sha256": lineage_sha256,
            "checkpoint_sha256": _CHECKPOINT_SHA256,
            "checkpoint_size": _CHECKPOINT_SIZE,
            "disabled_profile_contract": disabled_contract,
            "enabled_profile_contract": enabled_contract,
            "base_to_conditioned_migration_contract": migration_contract,
            "top_level_condition_validation_contract": top_validation,
            "current11_condition_validation_contract": current11_validation,
            "dynamics_threading_contract": dynamics_contract,
            "injection_contract": injection_contract,
            "deterministic_oracle_contract": oracle_contract,
            "state_dict_compatibility_contract": state_contract,
            "repository_cli_contract": repository_cli_contract,
            "canonical_mask_semantic_names": list(CANONICAL_MASK_SEMANTIC_NAMES),
            "implementation_source_scope": list(_IMPLEMENTATION_FILES),
            "model_consumption_implemented": model_consumption_implemented,
            "indicator_passed_into_dynamics": indicator_passed,
            "indicator_consumed_by_model": indicator_consumed,
            "model_consumption_gate_implemented": gate_implemented,
            "ready_for_repository_cli_forwarding_design": ready_for_cli_design,
            "recommended_next_step": "design_covapie_target_residue_atom_condition_repository_cli_forwarding_v1",
            "training_or_parameter_update": training_or_parameter_update,
            "feature_semantics_audit_required_before_training": True,
        }
        response = {
            field: values[field]
            for field in MODEL_CONSUMPTION_GATE_RESPONSE_FIELDS
            if field != "model_consumption_gate_response_sha256"
        }
        response["model_consumption_gate_response_sha256"] = _sha256(
            _canonical_json_bytes(response)
        )
        _validate_response(response, require_order=True)
        return response
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
    finally:
        torch.random.set_rng_state(entry_rng_state)


def _bundle_bytes(response: Mapping[str, Any]) -> bytes:
    _validate_response(response, require_order=True)
    payload = _canonical_json_bytes(response)
    decoded = _strict_json(payload)
    _validate_response(decoded, require_order=False)
    return payload


def _existing_output(path: Path, expected: bytes) -> dict[str, Any]:
    metadata = path.lstat()
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != 0o644
        or metadata.st_nlink != 1
        or metadata.st_size != len(expected)
        or path.read_bytes() != expected
    ):
        raise ValueError(_ERROR)
    return {
        "publication_mode": "idempotent_existing",
        "bundle_inode": metadata.st_ino,
        "bundle_mtime_ns": metadata.st_mtime_ns,
        "bundle_size": metadata.st_size,
        "bundle_sha256": _sha256(expected),
    }


def _remove_created_inode(path: Path, device: int, inode: int) -> None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return
    if (
        not stat.S_ISLNK(metadata.st_mode)
        and stat.S_ISREG(metadata.st_mode)
        and metadata.st_dev == device
        and metadata.st_ino == inode
    ):
        path.unlink()


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _materialize_covapie_current11_target_residue_atom_condition_model_consumption_gate_bundle_v1(
    *,
    source_runtime_bridge_gate_bundle: bytes,
    repo_root: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Publish canonical bytes atomically, or validate an identical target."""

    try:
        if type(output_path) is not type(Path()):
            raise ValueError(_ERROR)
        response = evaluate_covapie_target_residue_atom_condition_model_consumption_gate_v1(
            source_runtime_bridge_gate_bundle=source_runtime_bridge_gate_bundle,
            repo_root=repo_root,
        )
        if response["ready_for_repository_cli_forwarding_design"] is not True:
            raise ValueError(_ERROR)
        payload = _bundle_bytes(response)
        parent = output_path.parent
        parent_metadata = parent.lstat()
        if stat.S_ISLNK(parent_metadata.st_mode) or not stat.S_ISDIR(parent_metadata.st_mode):
            raise ValueError(_ERROR)
        try:
            output_path.lstat()
        except FileNotFoundError:
            pass
        else:
            return _existing_output(output_path, payload)

        temporary: Path | None = None
        descriptor: int | None = None
        created_device: int | None = None
        created_inode: int | None = None
        published = False
        try:
            for _ in range(128):
                candidate = parent / f".{output_path.name}.{secrets.token_hex(16)}.tmp"
                try:
                    descriptor = os.open(
                        candidate,
                        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                        0o600,
                    )
                except FileExistsError:
                    continue
                temporary = candidate
                metadata = os.fstat(descriptor)
                created_device, created_inode = metadata.st_dev, metadata.st_ino
                break
            if temporary is None or descriptor is None:
                raise ValueError(_ERROR)
            view = memoryview(payload)
            offset = 0
            while offset < len(view):
                written = os.write(descriptor, view[offset:])
                if written <= 0:
                    raise ValueError(_ERROR)
                offset += written
            os.fchmod(descriptor, 0o644)
            os.fsync(descriptor)
            os.close(descriptor)
            descriptor = None
            if temporary.read_bytes() != payload:
                raise ValueError(_ERROR)
            try:
                os.link(temporary, output_path, follow_symlinks=False)
            except FileExistsError:
                result = _existing_output(output_path, payload)
                _remove_created_inode(temporary, created_device, created_inode)
                _fsync_directory(parent)
                return result
            published = True
            linked = output_path.lstat()
            if (
                linked.st_dev != created_device
                or linked.st_ino != created_inode
                or linked.st_nlink != 2
            ):
                raise ValueError(_ERROR)
            _remove_created_inode(temporary, created_device, created_inode)
            _fsync_directory(parent)
            final = output_path.lstat()
            if (
                final.st_dev != created_device
                or final.st_ino != created_inode
                or final.st_nlink != 1
                or stat.S_IMODE(final.st_mode) != 0o644
                or output_path.read_bytes() != payload
            ):
                raise ValueError(_ERROR)
            return {
                "publication_mode": "published_new",
                "bundle_inode": final.st_ino,
                "bundle_mtime_ns": final.st_mtime_ns,
                "bundle_size": final.st_size,
                "bundle_sha256": _sha256(payload),
            }
        except Exception:
            if descriptor is not None:
                os.close(descriptor)
            if published and created_device is not None and created_inode is not None:
                _remove_created_inode(output_path, created_device, created_inode)
            if temporary is not None and created_device is not None and created_inode is not None:
                _remove_created_inode(temporary, created_device, created_inode)
            try:
                _fsync_directory(parent)
            except Exception:
                pass
            raise
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
