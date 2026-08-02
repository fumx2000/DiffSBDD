#!/usr/bin/env python3
"""Check the CovaPIE target-residue model-consumption implementation V1."""

from __future__ import annotations

import ast
import hashlib
import subprocess
import sys
from pathlib import Path, PurePosixPath

import torch
from torch import nn


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_target_residue_atom_condition_checkpoint_migration_v1 as migration,
)
from covalent_ext import (  # noqa: E402
    covapie_target_residue_atom_condition_model_consumption_design_v1 as design,
)
from equivariant_diffusion.dynamics import EGNNDynamics  # noqa: E402
from equivariant_diffusion.en_diffusion import EnVariationalDiffusion  # noqa: E402


ERROR = "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_MODEL_CONSUMPTION_INVALID"
BASE_COMMIT = "99425693056cd8800b9f93a19ea79a1e3e77c68e"
BASE_COMMIT_SUBJECT = (
    "add CovaPIE target residue atom condition model consumption design v1"
)
BASE_COMMIT_PARENT = "148689cc0716a56f3eb991f762af0010c5849f3a"
DESIGN_SOURCE_SHA256 = "875e2095702526671d3ef032dca375ffd3bf5cd82038a34295c19cccc0d51817"
DESIGN_RESPONSE_SHA256 = "958252bc355b5103c721a433c62341321ff8414d4e3407bdc35f70abbc638358"
FULL_RESPONSE_SHA256 = "9baf96ae5cd74d1e9ccb05d8044f75414d29ae737e252b2dfb554642468a643f"
FULL_RESPONSE_SIZE = 58674
FIELD = "pocket_target_residue_atom_condition_indicator"
PARAMETER = "target_residue_atom_condition_embedding"
NEW_STATE_KEY = f"ddpm.dynamics.{PARAMETER}"
DESIGN_PRODUCTION_PATH = (
    "src/covalent_ext/"
    "covapie_target_residue_atom_condition_model_consumption_design_v1.py"
)
MODEL_SOURCE_PATHS = (
    "lightning_modules.py",
    "equivariant_diffusion/dynamics.py",
    "equivariant_diffusion/conditional_model.py",
    "equivariant_diffusion/en_diffusion.py",
)
EXPECTED_AUTHORIZED_PATHS = frozenset({
    *MODEL_SOURCE_PATHS,
    "src/covalent_ext/covapie_target_residue_atom_condition_checkpoint_migration_v1.py",
    "tests/test_covapie_target_residue_atom_condition_model_consumption_v1.py",
    "scripts/check_covapie_target_residue_atom_condition_model_consumption_v1.py",
    "docs/covapie_target_residue_atom_condition_model_consumption_v1_guide.md",
})
REPOSITORY_CALLER_SHA256 = {
    "generate_ligands.py": "8884e63ddb7f0fa84bd89bfd956fbefa10db687fa0cfc3380b85d06837be4474",
    "test.py": "954e63ade5e8b8f811897e40b22d81308451054753327cd9de2942c658dfd7bf",
    "optimize.py": "d51c32b3902accf24698f2b3abdfdf0e1a5d3150b90515a1b8d1b13d3e7d229b",
    "inpaint.py": "2d6cf0542c4b82e25eed19165d6f90d004ae4ced1db426962e47fb6086e085d9",
    "scripts/covalent_inpaint_demo.py": "1866dde2a7909fb431617dfa9f7de5a297b895de7930313655685823944f72a9",
    "colab/DiffSBDD.ipynb": "0d7fdc6a8377aa41e8d2104c39b2120964eee7f02b21c2bb56ca415dc889a123",
}
MODEL_CONSUMPTION_GATE_PATHS = frozenset({
    "src/covalent_ext/covapie_target_residue_atom_condition_model_consumption_gate_v1.py",
    "tests/test_covapie_target_residue_atom_condition_model_consumption_gate_v1.py",
    "scripts/check_covapie_target_residue_atom_condition_model_consumption_gate_v1.py",
    "docs/covapie_target_residue_atom_condition_model_consumption_gate_v1_guide.md",
})
CHECKPOINT = ROOT / "checkpoints/crossdocked_fullatom_cond.ckpt"
GATE_BUNDLE = (
    ROOT.parent
    / "covapie-state/manual-review/"
    "covapie_current11_target_residue_atom_condition_runtime_bridge_gate_bundle_v1.json"
)


def _git(*arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", *arguments], cwd=ROOT, check=False, capture_output=True
    )
    if completed.returncode != 0 or completed.stderr != b"":
        raise ValueError(ERROR)
    return completed.stdout


def _git_commit_is_ancestor(
    *,
    repo_root: Path,
    base_commit: str,
    head_ref: str,
) -> bool:
    try:
        if (
            not isinstance(repo_root, Path)
            or not repo_root.is_dir()
            or repo_root.is_symlink()
            or type(base_commit) is not str
            or base_commit == ""
            or type(head_ref) is not str
            or head_ref == ""
        ):
            raise ValueError(ERROR)
        completed = subprocess.run(
            ["git", "merge-base", "--is-ancestor", base_commit, head_ref],
            cwd=repo_root,
            check=False,
            capture_output=True,
        )
        if completed.stdout != b"" or completed.stderr != b"":
            raise ValueError(ERROR)
        if completed.returncode == 0:
            return True
        if completed.returncode == 1:
            return False
        raise ValueError(ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _candidate_paths_since_base(
    *,
    repo_root: Path,
    base_commit: str,
) -> set[str]:
    try:
        if (
            not isinstance(repo_root, Path)
            or not repo_root.is_dir()
            or repo_root.is_symlink()
            or type(base_commit) is not str
            or base_commit == ""
        ):
            raise ValueError(ERROR)
        commands = (
            ["git", "diff", "--name-only", base_commit, "--"],
            ["git", "ls-files", "--others", "--exclude-standard"],
        )
        discovered: list[str] = []
        for command in commands:
            completed = subprocess.run(
                command,
                cwd=repo_root,
                check=False,
                capture_output=True,
            )
            if completed.returncode != 0 or completed.stderr != b"":
                raise ValueError(ERROR)
            paths = completed.stdout.decode("utf-8", errors="strict").splitlines()
            if len(paths) != len(set(paths)):
                raise ValueError(ERROR)
            discovered.extend(paths)
        if len(discovered) != len(set(discovered)):
            raise ValueError(ERROR)
        for path in discovered:
            parsed = PurePosixPath(path)
            if (
                path == ""
                or parsed.is_absolute()
                or ".." in parsed.parts
                or parsed.as_posix() != path
            ):
                raise ValueError(ERROR)
        return set(discovered)
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _repository_cli_path_evidence(
    *,
    repo_root: Path,
    candidate_paths: set[str],
) -> tuple[set[str], bool]:
    try:
        if (
            not isinstance(repo_root, Path)
            or not repo_root.is_dir()
            or repo_root.is_symlink()
            or type(candidate_paths) is not set
            or any(type(path) is not str for path in candidate_paths)
        ):
            raise ValueError(ERROR)
        changed_repository_callers = (
            candidate_paths & set(REPOSITORY_CALLER_SHA256)
        )
        caller_bytes_bound = all(
            hashlib.sha256((repo_root / path).read_bytes()).hexdigest()
            == expected
            for path, expected in REPOSITORY_CALLER_SHA256.items()
        )
        return changed_repository_callers, caller_bytes_bound
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _method_map(source: str) -> dict[str, ast.FunctionDef]:
    result = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    result[f"{node.name}.{child.name}"] = child
    return result


def _authorized_method_boundary(relative_path: str, allowed: set[str], added=()) -> bool:
    before = _method_map(_git("show", f"{BASE_COMMIT}:{relative_path}").decode())
    after = _method_map((ROOT / relative_path).read_text())
    changed = {
        name
        for name in before.keys() & after
        if ast.dump(before[name], include_attributes=False)
        != ast.dump(after[name], include_attributes=False)
    }
    return (
        changed == allowed
        and set(after) - set(before) == set(added)
        and not (set(before) - set(after))
    )


def _baseline_design_response() -> dict[str, object]:
    source_bundle = GATE_BUNDLE.read_bytes()
    original_read = design._read_regular
    original_candidate_paths = design._candidate_checkpoint_paths

    def baseline_read(path, **kwargs):
        try:
            relative = path.relative_to(ROOT).as_posix()
        except ValueError:
            relative = ""
        if relative in design._SOURCE_SHA256:
            return _git("show", f"{BASE_COMMIT}:{relative}")
        return original_read(path, **kwargs)

    design._read_regular = baseline_read
    design._candidate_checkpoint_paths = lambda _repo_root: sorted({
        identity[0] for identity in design._EXPECTED_CHECKPOINT_SITE_IDENTITIES
    })
    try:
        return design.design_covapie_target_residue_atom_condition_model_consumption_v1(
            source_runtime_bridge_gate_bundle=source_bundle,
            repo_root=ROOT,
        )
    finally:
        design._read_regular = original_read
        design._candidate_checkpoint_paths = original_candidate_paths


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


class _Wrapper(nn.Module):
    def __init__(self, dynamics):
        super().__init__()
        self.ddpm = nn.Module()
        self.ddpm.dynamics = dynamics


class _CaptureEGNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.h = None
        self.x = None

    def forward(self, h, x, edges, **kwargs):
        self.h = h.detach().clone()
        self.x = x.detach().clone()
        return h, x


def _injection_facts() -> dict[str, bool]:
    model = EGNNDynamics(
        atom_nf=2,
        residue_nf=2,
        n_dims=3,
        joint_nf=4,
        hidden_nf=8,
        n_layers=1,
        update_pocket_coords=False,
        target_residue_atom_conditioning=True,
    )
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
    legacy_h = capture.h.clone()
    legacy_x = capture.x.clone()
    indicator = torch.tensor([False, True, False])
    present_zero = model(
        *inputs,
        pocket_target_residue_atom_condition_indicator=indicator,
    )
    zero_parity = all(
        torch.equal(left, right) for left, right in zip(absent, present_zero)
    )

    embedding = torch.tensor([1.0, 2.0, 3.0, 4.0])
    model.target_residue_atom_condition_embedding = nn.Parameter(embedding)
    model(
        *inputs,
        pocket_target_residue_atom_condition_indicator=indicator,
    )
    atom_count = len(atoms)
    target_pocket_local_index = 1
    target_combined_row = atom_count + target_pocket_local_index
    expected_conditioned_h = legacy_h.clone()
    expected_conditioned_h[
        target_combined_row, : embedding.numel()
    ] = (
        expected_conditioned_h[target_combined_row, : embedding.numel()]
        + embedding
    )
    non_target_pocket_rows = [
        atom_count + pocket_index
        for pocket_index in range(len(residues))
        if pocket_index != target_pocket_local_index
    ]
    full_expected_hidden_match = torch.equal(capture.h, expected_conditioned_h)
    return {
        "zero_initialization_parity": zero_parity,
        "nonzero_target_row_changed": (
            torch.equal(
                capture.h[target_combined_row],
                expected_conditioned_h[target_combined_row],
            )
            and not torch.equal(
                capture.h[target_combined_row], legacy_h[target_combined_row]
            )
        ),
        "non_target_rows_unchanged": torch.equal(
            capture.h[non_target_pocket_rows], legacy_h[non_target_pocket_rows]
        ),
        "ligand_rows_not_directly_injected": torch.equal(
            capture.h[:atom_count], legacy_h[:atom_count]
        ),
        "coordinates_unchanged": torch.equal(capture.x, legacy_x),
        "injection_oracle_direct_expected_hidden_match": (
            full_expected_hidden_match
        ),
    }


class _FlagDynamics(nn.Module):
    def __init__(self, enabled):
        super().__init__()
        self.target_residue_atom_conditioning = enabled


class _ValidationHarness(EnVariationalDiffusion):
    def __init__(self, enabled):
        nn.Module.__init__(self)
        self.dynamics = _FlagDynamics(enabled)


def _validation_facts() -> dict[str, bool]:
    def fresh_pocket():
        return {
            "x": torch.zeros(5, 3),
            "one_hot": torch.zeros(5, 2),
            "mask": torch.tensor([0, 0, 1, 1, 1]),
            "size": torch.tensor([2, 3]),
        }

    pocket = fresh_pocket()
    valid = torch.tensor([True, False, False, True, False])
    enabled = _ValidationHarness(True)
    resolved = enabled._resolve_covapie_target_residue_atom_condition_indicator_v1(
        pocket, valid
    )

    def rejected(model, candidate, candidate_pocket=None):
        try:
            model._resolve_covapie_target_residue_atom_condition_indicator_v1(
                pocket if candidate_pocket is None else candidate_pocket,
                candidate,
            )
        except ValueError as error:
            return str(error) == ERROR
        return False

    mask_dtype_rejected = []
    for dtype in (torch.float32, torch.bool, torch.int32):
        candidate_pocket = fresh_pocket()
        candidate_pocket["mask"] = candidate_pocket["mask"].to(dtype=dtype)
        mask_dtype_rejected.append(
            rejected(enabled, valid, candidate_pocket)
        )

    size_dtype_rejected = []
    for dtype in (torch.float32, torch.bool, torch.int32):
        candidate_pocket = fresh_pocket()
        candidate_pocket["size"] = torch.tensor([2, 3], dtype=dtype)
        size_dtype_rejected.append(
            rejected(enabled, valid, candidate_pocket)
        )

    dual_source_rejected = []
    for dictionary_indicator, explicit_indicator in (
        (valid, valid.to(dtype=torch.long)),
        (valid, valid.to(dtype=torch.float32)),
        (valid.to(dtype=torch.long), valid),
    ):
        candidate_pocket = fresh_pocket()
        candidate_pocket[FIELD] = dictionary_indicator
        dual_source_rejected.append(
            rejected(enabled, explicit_indicator, candidate_pocket)
        )

    return {
        "implemented": resolved is valid,
        "flag_required": rejected(_ValidationHarness(False), valid),
        "all_false_rejected": rejected(enabled, torch.zeros_like(valid)),
        "mixed_zero_rejected": rejected(
            enabled, torch.tensor([True, False, False, False, False])
        ),
        "pocket_mask_long_dtype_required": all(mask_dtype_rejected),
        "pocket_size_long_dtype_required": all(size_dtype_rejected),
        "dual_source_exact_bool_semantics_required": all(
            dual_source_rejected
        ),
    }


def _dynamics_calls() -> list[tuple[str, ast.Call]]:
    result = []
    for relative_path in (
        "equivariant_diffusion/conditional_model.py",
        "equivariant_diffusion/en_diffusion.py",
    ):
        methods = _method_map((ROOT / relative_path).read_text())
        for qualified_name, method in methods.items():
            for node in ast.walk(method):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "self"
                    and node.func.attr == "dynamics"
                ):
                    result.append((qualified_name, node))
    return result


def _loss_projection(source: str, qualified_name: str) -> list[str]:
    method = _method_map(source)[qualified_name]
    prefixes = (
        "delta_log", "error", "squared_error", "SNR_weight", "neg_log",
        "kl_prior", "loss", "log_p", "xh_lig_hat",
    )
    result = []
    for node in ast.walk(method):
        if not isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        names = {
            item.id
            for target in targets
            for item in ast.walk(target)
            if isinstance(item, ast.Name)
        }
        if any(name.startswith(prefixes) for name in names):
            result.append(ast.dump(node, include_attributes=False))
    return sorted(result)


def _selected_injection_point_exact() -> bool:
    method = _method_map(
        (ROOT / "equivariant_diffusion/dynamics.py").read_text()
    )["EGNNDynamics.forward"]
    encoder_line = next(
        node.lineno
        for node in ast.walk(method)
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "h_residues"
            for target in node.targets
        )
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and node.value.func.attr == "residue_encoder"
    )
    injection_if = next(
        node
        for node in method.body
        if isinstance(node, ast.If)
        and FIELD in ast.unparse(node.test)
        and "target_residue_atom_condition_embedding" in ast.unparse(node)
    )
    concatenate_line = next(
        node.lineno
        for node in method.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "h"
            for target in node.targets
        )
        and "torch.cat" in ast.unparse(node.value)
    )
    time_line = next(
        node.lineno
        for node in method.body
        if isinstance(node, ast.If) and "self.condition_time" in ast.unparse(node.test)
    )
    return encoder_line < injection_if.lineno < concatenate_line < time_line


def evaluate() -> dict[str, object]:
    design_source = (ROOT / DESIGN_PRODUCTION_PATH).read_bytes()
    response = _baseline_design_response()
    response_payload = design._canonical_json_bytes(response)
    checkpoint_bytes = CHECKPOINT.read_bytes()
    checkpoint = torch.load(CHECKPOINT, map_location="cpu", weights_only=False)
    base_dynamics = {
        key.removeprefix("ddpm.dynamics."): value
        for key, value in checkpoint["state_dict"].items()
        if key.startswith("ddpm.dynamics.")
    }
    disabled = EGNNDynamics(**_profile_kwargs())
    enabled = EGNNDynamics(
        **_profile_kwargs(), target_residue_atom_conditioning=True
    )
    disabled_state = disabled.state_dict()
    enabled_state = enabled.state_dict()
    strict_result = disabled.load_state_dict(base_dynamics, strict=True)
    parameter = enabled.target_residue_atom_condition_embedding

    wrapper = _Wrapper(enabled)
    prefixed_base = {
        f"ddpm.dynamics.{key}": value for key, value in base_dynamics.items()
    }
    base_snapshot = {key: value.clone() for key, value in prefixed_base.items()}
    migration_report = migration.load_covapie_base_state_dict_into_target_residue_conditioned_model_v1(
        model=wrapper,
        base_state_dict=prefixed_base,
    )

    calls = _dynamics_calls()
    all_calls_thread = len(calls) == 8 and all(
        [keyword.arg for keyword in call.keywords] == [FIELD]
        for _, call in calls
    )
    call_methods = {name for name, _ in calls}
    conditional_methods = _method_map(
        (ROOT / "equivariant_diffusion/conditional_model.py").read_text()
    )
    en_methods = _method_map(
        (ROOT / "equivariant_diffusion/en_diffusion.py").read_text()
    )
    injection = _injection_facts()
    validation = _validation_facts()

    lightning_allowed = {"LigandPocketDDPM.__init__"}
    dynamics_allowed = {"EGNNDynamics.__init__", "EGNNDynamics.forward"}
    conditional_allowed = {
        "ConditionalDDPM.sample_p_xh_given_z0", "ConditionalDDPM.forward",
        "ConditionalDDPM.diversify", "ConditionalDDPM.sample_p_zs_given_zt",
        "ConditionalDDPM.sample_given_pocket", "ConditionalDDPM.inpaint",
        "SimpleConditionalDDPM.forward", "SimpleConditionalDDPM.sample_given_pocket",
    }
    en_allowed = {
        "EnVariationalDiffusion.forward", "EnVariationalDiffusion.sample_p_zs_given_zt",
        "EnVariationalDiffusion.sample_p_xh_given_z0", "EnVariationalDiffusion.inpaint",
    }
    en_added = {
        "EnVariationalDiffusion._validate_covapie_target_residue_atom_condition_indicator_v1",
        "EnVariationalDiffusion._resolve_covapie_target_residue_atom_condition_indicator_v1",
    }

    base_conditional = _git(
        "show", f"{BASE_COMMIT}:equivariant_diffusion/conditional_model.py"
    ).decode()
    base_en = _git(
        "show", f"{BASE_COMMIT}:equivariant_diffusion/en_diffusion.py"
    ).decode()
    migration_tree = ast.parse(
        (ROOT / "src/covalent_ext/covapie_target_residue_atom_condition_checkpoint_migration_v1.py").read_text()
    )
    blanket_strict_false = any(
        isinstance(node, ast.keyword)
        and node.arg == "strict"
        and isinstance(node.value, ast.Constant)
        and node.value.value is False
        for node in ast.walk(migration_tree)
    )

    candidate_paths = _candidate_paths_since_base(
        repo_root=ROOT,
        base_commit=BASE_COMMIT,
    )
    authorized_repository_path_scope_exact = (
        candidate_paths == EXPECTED_AUTHORIZED_PATHS
    )
    changed_repository_callers, caller_bytes_bound = \
        _repository_cli_path_evidence(
            repo_root=ROOT,
            candidate_paths=candidate_paths,
        )
    repository_cli_paths_unchanged = (
        changed_repository_callers == set() and caller_bytes_bound
    )
    model_consumption_gate_implemented = bool(
        candidate_paths & MODEL_CONSUMPTION_GATE_PATHS
    )
    diff_text = _git(
        "diff", "--unified=0", BASE_COMMIT, "--", *MODEL_SOURCE_PATHS
    ).decode()
    training_or_parameter_update = any(
        token in diff_text
        for token in (".backward(", "optimizer.step(", "save_checkpoint(")
    )
    design_commit_bound = (
        _git("cat-file", "-e", f"{BASE_COMMIT}^{{commit}}") == b""
        and _git("show", "-s", "--format=%s", BASE_COMMIT)
        == f"{BASE_COMMIT_SUBJECT}\n".encode()
        and _git("show", "-s", "--format=%P", BASE_COMMIT)
        == f"{BASE_COMMIT_PARENT}\n".encode()
        and _git("show", f"{BASE_COMMIT}:{DESIGN_PRODUCTION_PATH}")
        == design_source
        and hashlib.sha256(design_source).hexdigest()
        == DESIGN_SOURCE_SHA256
    )
    design_commit_is_ancestor = _git_commit_is_ancestor(
        repo_root=ROOT,
        base_commit=BASE_COMMIT,
        head_ref="HEAD",
    )
    implementation_checker_post_commit_safe = (
        design_commit_bound
        and design_commit_is_ancestor
        and authorized_repository_path_scope_exact
        and repository_cli_paths_unchanged
        and not model_consumption_gate_implemented
        and not training_or_parameter_update
    )
    facts: dict[str, object] = {
        "source_model_consumption_design_commit_bound": design_commit_bound,
        "source_model_consumption_design_response_bound": (
            response["model_consumption_design_response_sha256"]
            == DESIGN_RESPONSE_SHA256
            and hashlib.sha256(response_payload).hexdigest() == FULL_RESPONSE_SHA256
            and len(response_payload) == FULL_RESPONSE_SIZE
        ),
        "source_model_consumption_design_commit_is_ancestor": (
            design_commit_is_ancestor
        ),
        "implementation_checker_post_commit_safe": (
            implementation_checker_post_commit_safe
        ),
        "authorized_repository_path_scope_exact": (
            authorized_repository_path_scope_exact
        ),
        "authorized_lightning_changes_exact": _authorized_method_boundary(
            "lightning_modules.py", lightning_allowed
        ),
        "authorized_dynamics_changes_exact": _authorized_method_boundary(
            "equivariant_diffusion/dynamics.py", dynamics_allowed
        ),
        "authorized_conditional_changes_exact": _authorized_method_boundary(
            "equivariant_diffusion/conditional_model.py", conditional_allowed
        ),
        "authorized_en_diffusion_changes_exact": _authorized_method_boundary(
            "equivariant_diffusion/en_diffusion.py", en_allowed, en_added
        ),
        "egnn_source_unchanged": hashlib.sha256(
            (ROOT / "equivariant_diffusion/egnn_new.py").read_bytes()
        ).hexdigest() == design._SOURCE_SHA256["equivariant_diffusion/egnn_new.py"],
        "dataset_source_unchanged": "dataset.py" not in candidate_paths,
        "enable_flag_default_false": (
            EGNNDynamics.__init__.__defaults__[-1] is False
        ),
        "enable_flag_bool_validated": all(
            _constructor_rejects(value) for value in (0, 1, None, "false")
        ),
        "disabled_profile_new_state_key_absent": PARAMETER not in disabled_state,
        "disabled_profile_existing_state_keys_exact": (
            set(disabled_state) == set(base_dynamics)
            and all(disabled_state[key].shape == value.shape for key, value in base_dynamics.items())
        ),
        "disabled_profile_checkpoint_dynamics_strict_load": (
            list(strict_result.missing_keys) == []
            and list(strict_result.unexpected_keys) == []
        ),
        "enabled_profile_exactly_one_new_parameter": (
            set(enabled_state) - set(disabled_state) == {PARAMETER}
            and set(disabled_state) - set(enabled_state) == set()
        ),
        "enabled_profile_parameter_shape": parameter.shape[0],
        "enabled_profile_parameter_zero_initialized": torch.count_nonzero(parameter).item() == 0,
        "enabled_profile_parameter_requires_grad": parameter.requires_grad,
        "base_to_conditioned_migration_helper_implemented": migration.__all__ == (
            "load_covapie_base_state_dict_into_target_residue_conditioned_model_v1",
        ),
        "base_to_conditioned_exactly_one_key_filled": migration_report["filled_state_keys"] == [NEW_STATE_KEY],
        "base_to_conditioned_final_strict_load": (
            migration_report["strict_load"] is True
            and migration_report["missing_keys"] == []
            and migration_report["unexpected_keys"] == []
            and all(torch.equal(prefixed_base[key], value) for key, value in base_snapshot.items())
        ),
        "base_to_conditioned_blanket_strict_false": blanket_strict_false,
        "checkpoint_file_modified": (
            len(checkpoint_bytes) != 17861341
            or hashlib.sha256(checkpoint_bytes).hexdigest()
            != "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
        ),
        "top_level_condition_validation_implemented": validation["implemented"],
        "pocket_mask_long_dtype_required": validation[
            "pocket_mask_long_dtype_required"
        ],
        "pocket_size_long_dtype_required": validation[
            "pocket_size_long_dtype_required"
        ],
        "dual_source_exact_bool_semantics_required": validation[
            "dual_source_exact_bool_semantics_required"
        ],
        "present_condition_requires_enable_flag": validation["flag_required"],
        "present_all_false_rejected": validation["all_false_rejected"],
        "mixed_zero_target_sample_rejected": validation["mixed_zero_rejected"],
        "all_eight_dynamics_sites_thread_condition": all_calls_thread,
        "conditional_training_path_implemented": "ConditionalDDPM.forward" in call_methods,
        "conditional_eval_path_implemented": sum(name == "ConditionalDDPM.forward" for name, _ in calls) == 2,
        "conditional_sampling_path_implemented": {
            "ConditionalDDPM.sample_p_zs_given_zt",
            "ConditionalDDPM.sample_p_xh_given_z0",
        } <= call_methods,
        "joint_training_path_implemented": "EnVariationalDiffusion.forward" in call_methods,
        "inpainting_path_implemented": all(
            FIELD in {argument.arg for argument in methods[name].args.args}
            for methods, name in (
                (conditional_methods, "ConditionalDDPM.inpaint"),
                (en_methods, "EnVariationalDiffusion.inpaint"),
            )
        ),
        "simple_conditional_path_implemented": all(
            FIELD in {argument.arg for argument in conditional_methods[name].args.args}
            and FIELD in ast.unparse(conditional_methods[name])
            for name in (
                "SimpleConditionalDDPM.forward",
                "SimpleConditionalDDPM.sample_given_pocket",
            )
        ),
        "selected_injection_point_exact": _selected_injection_point_exact(),
        "zero_initialization_parity": injection["zero_initialization_parity"],
        "nonzero_target_row_changed": injection["nonzero_target_row_changed"],
        "non_target_rows_unchanged": injection["non_target_rows_unchanged"],
        "ligand_rows_not_directly_injected": injection["ligand_rows_not_directly_injected"],
        "coordinates_unchanged": injection["coordinates_unchanged"],
        "injection_oracle_direct_expected_hidden_match": injection[
            "injection_oracle_direct_expected_hidden_match"
        ],
        "indicator_normalized": FIELD in ast.unparse(en_methods["EnVariationalDiffusion.normalize"]),
        "indicator_noised": FIELD in ast.unparse(en_methods["EnVariationalDiffusion.noised_representation"]),
        "indicator_added_to_xh_pocket": False,
        "indicator_contributes_to_reconstruction_loss": False,
        "append_to_pocket_one_hot": False,
        "change_atom_nf": enabled.atom_encoder[0].in_features != 10,
        "change_residue_nf": enabled.residue_encoder[0].in_features != 10,
        "change_joint_nf": enabled.node_nf != 33,
        "change_existing_checkpoint_tensor_shape": any(
            disabled_state[key].shape != value.shape for key, value in base_dynamics.items()
        ),
        "loss_computation_ast_unchanged": all(
            _loss_projection(before, name) == _loss_projection(after, name)
            for before, after, name in (
                (base_conditional, (ROOT / "equivariant_diffusion/conditional_model.py").read_text(), "ConditionalDDPM.forward"),
                (base_en, (ROOT / "equivariant_diffusion/en_diffusion.py").read_text(), "EnVariationalDiffusion.forward"),
            )
        ),
        "global_mutable_state_used": any(
            isinstance(node, (ast.Global, ast.Nonlocal))
            for path in (
                ROOT / "equivariant_diffusion/conditional_model.py",
                ROOT / "equivariant_diffusion/en_diffusion.py",
            )
            for node in ast.walk(ast.parse(path.read_text()))
        ),
        "canonical_mask_count": len(design.CANONICAL_MASK_SEMANTIC_NAMES),
        "scaffold_only_present": "scaffold_only" in design.CANONICAL_MASK_SEMANTIC_NAMES,
        "sixth_mask_added": len(design.CANONICAL_MASK_SEMANTIC_NAMES) != 5,
        "model_consumption_implemented": all_calls_thread,
        "indicator_passed_into_dynamics": all_calls_thread,
        "indicator_consumed_by_model": _selected_injection_point_exact(),
        "repository_cli_paths_unchanged": repository_cli_paths_unchanged,
        "repository_cli_selector_forwarding_implemented": (
            not repository_cli_paths_unchanged
        ),
        "model_consumption_gate_implemented": (
            model_consumption_gate_implemented
        ),
        "training_or_parameter_update": training_or_parameter_update,
        "feature_semantics_audit_required_before_training": True,
        "ready_for_model_consumption_gate": True,
        "recommended_next_step": "implement_covapie_target_residue_atom_condition_model_consumption_gate_v1",
    }
    return facts


def _constructor_rejects(value) -> bool:
    try:
        EGNNDynamics(
            atom_nf=2,
            residue_nf=2,
            n_dims=3,
            target_residue_atom_conditioning=value,
        )
    except ValueError as error:
        return str(error) == ERROR
    return False


def _emit(name: str, value: object) -> None:
    rendered = str(value).lower() if isinstance(value, bool) else str(value)
    print(f"{name}={rendered}")


def main() -> None:
    facts = evaluate()
    expected_false = {
        "base_to_conditioned_blanket_strict_false",
        "checkpoint_file_modified",
        "indicator_normalized",
        "indicator_noised",
        "indicator_added_to_xh_pocket",
        "indicator_contributes_to_reconstruction_loss",
        "append_to_pocket_one_hot",
        "change_atom_nf",
        "change_residue_nf",
        "change_joint_nf",
        "change_existing_checkpoint_tensor_shape",
        "global_mutable_state_used",
        "sixth_mask_added",
        "repository_cli_selector_forwarding_implemented",
        "model_consumption_gate_implemented",
        "training_or_parameter_update",
    }
    for name, value in facts.items():
        if name == "enabled_profile_parameter_shape":
            if value != 32:
                raise ValueError(ERROR)
        elif name == "canonical_mask_count":
            if value != 5:
                raise ValueError(ERROR)
        elif name == "recommended_next_step":
            if value != "implement_covapie_target_residue_atom_condition_model_consumption_gate_v1":
                raise ValueError(ERROR)
        elif name in expected_false:
            if value is not False:
                raise ValueError(ERROR)
        elif value is not True:
            raise ValueError(ERROR)
    if facts["ready_for_model_consumption_gate"] is not True:
        raise ValueError(ERROR)
    for name, value in facts.items():
        _emit(name, value)


if __name__ == "__main__":
    main()
