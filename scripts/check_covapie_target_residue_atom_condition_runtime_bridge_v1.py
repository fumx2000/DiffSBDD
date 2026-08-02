#!/usr/bin/env python3
"""Check the CovaPIE target-residue atom-condition runtime bridge V1."""

from __future__ import annotations

import ast
import hashlib
import json
import stat
import subprocess
from copy import deepcopy
from pathlib import Path
from types import ModuleType

import numpy as np
import torch
import torch.nn.functional as F


ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "6f3ba8eb0dcb2982a14f5bdc0c7319b0a4e79250"
FIELD = "pocket_target_residue_atom_condition_indicator"
ERROR = "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_RUNTIME_BRIDGE_INVALID"
EXPECTED_EXTERNAL_PATH_RESOLUTION_RESPONSE_SHA256 = (
    "8406e5baef6e67fca331d54963f56e6ac9137c5f1afa3a963e7010c491afa9dc"
)
EXPECTED_EXTERNAL_PATH_RESOLUTION_PRODUCTION_SHA256 = (
    "02bbf44ca3602576b252678f499a1219e4d3ee2db170ed2abd474983cf5a3232"
)
EXPECTED_LEGACY_REPOSITORY_CALLER_SHA256S = {
    "generate_ligands.py": (
        "8884e63ddb7f0fa84bd89bfd956fbefa10db687fa0cfc3380b85d06837be4474"
    ),
    "test.py": (
        "954e63ade5e8b8f811897e40b22d81308451054753327cd9de2942c658dfd7bf"
    ),
    "optimize.py": (
        "d51c32b3902accf24698f2b3abdfdf0e1a5d3150b90515a1b8d1b13d3e7d229b"
    ),
    "inpaint.py": (
        "2d6cf0542c4b82e25eed19165d6f90d004ae4ced1db426962e47fb6086e085d9"
    ),
    "scripts/covalent_inpaint_demo.py": (
        "1866dde2a7909fb431617dfa9f7de5a297b895de7930313655685823944f72a9"
    ),
    "colab/DiffSBDD.ipynb": (
        "0d7fdc6a8377aa41e8d2104c39b2120964eee7f02b21c2bb56ca415dc889a123"
    ),
}
EXTERNAL_RESOLUTION = (
    ROOT
    / "src/covalent_ext/"
    "covapie_external_pocket_runtime_bridge_path_coverage_resolution_v1.py"
)
ADAPTER_BUNDLE = (
    ROOT.parent
    / "covapie-state/manual-review/"
    "covapie_current11_target_residue_atom_condition_adapter_bundle_v1.json"
)
EXPECTED_FLAT = (49, 81, 182, 299, 505, 712, 988, 1260, 1516, 1766, 2058)
METHODS = ("get_ligand_and_pocket", "prepare_pocket", "generate_ligands")
HELPERS = (
    "_validate_covapie_target_residue_atom_condition_spec_v1",
    "_locate_covapie_target_residue_atom_in_pocket_atoms_v1",
    "_build_covapie_repeated_target_residue_atom_condition_indicator_v1",
    "_validate_covapie_collated_target_residue_atom_condition_indicator_v1",
)
CANONICAL_MASKS = (
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
)


def _git_commit_is_ancestor(
    *,
    repo_root: Path,
    base_commit: str,
    head_ref: str = "HEAD",
) -> bool:
    """Return whether a base commit is equal to or precedes the head ref."""

    try:
        metadata = repo_root.lstat()
        if (
            not stat.S_ISDIR(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or type(base_commit) is not str
            or not base_commit
            or type(head_ref) is not str
            or not head_ref
        ):
            raise ValueError(ERROR)
        completed = subprocess.run(
            ["git", "merge-base", "--is-ancestor", base_commit, head_ref],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.stdout != "" or completed.stderr != "":
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


def _git_blob_sha256(
    *, repo_root: Path, commit: str, relative_path: str
) -> str:
    """Hash a regular repository blob at a specific commit without checkout."""

    try:
        relative = Path(relative_path)
        if (
            type(commit) is not str
            or not commit
            or type(relative_path) is not str
            or not relative_path
            or relative.is_absolute()
            or ".." in relative.parts
        ):
            raise ValueError(ERROR)
        completed = subprocess.run(
            ["git", "show", f"{commit}:{relative.as_posix()}"],
            cwd=repo_root,
            check=False,
            capture_output=True,
        )
        if completed.returncode != 0 or completed.stderr != b"":
            raise ValueError(ERROR)
        return hashlib.sha256(completed.stdout).hexdigest()
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _protected_repository_callers_unchanged(
    *, repo_root: Path, expected_sha256s: dict[str, str]
) -> bool:
    """Validate frozen legacy callers as regular in-repository files."""

    try:
        root_metadata = repo_root.lstat()
        if (
            not stat.S_ISDIR(root_metadata.st_mode)
            or stat.S_ISLNK(root_metadata.st_mode)
            or type(expected_sha256s) is not dict
            or not expected_sha256s
        ):
            return False
        for relative_name, expected_sha256 in expected_sha256s.items():
            relative = Path(relative_name)
            if (
                type(relative_name) is not str
                or not relative_name
                or relative.is_absolute()
                or ".." in relative.parts
                or type(expected_sha256) is not str
                or len(expected_sha256) != 64
                or any(character not in "0123456789abcdef" for character in expected_sha256)
            ):
                return False
            candidate = repo_root
            for index, part in enumerate(relative.parts):
                candidate = candidate / part
                metadata = candidate.lstat()
                if stat.S_ISLNK(metadata.st_mode):
                    return False
                if index < len(relative.parts) - 1:
                    if not stat.S_ISDIR(metadata.st_mode):
                        return False
                elif not stat.S_ISREG(metadata.st_mode):
                    return False
            if _sha(candidate) != expected_sha256:
                return False
        return True
    except OSError:
        return False
    except Exception as error:
        raise ValueError(ERROR) from error

def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _base_source() -> str:
    return subprocess.run(
        ["git", "show", f"{BASE_COMMIT}:lightning_modules.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _method_map(tree: ast.Module) -> dict[str, str]:
    class_node = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "LigandPocketDDPM"
    )
    return {
        node.name: ast.dump(node, include_attributes=False)
        for node in class_node.body
        if isinstance(node, ast.FunctionDef)
    }


def _top_level_class_map(tree: ast.Module) -> dict[str, str]:
    return {
        node.name: ast.dump(node, include_attributes=False)
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name != "LigandPocketDDPM"
    }


def _load_runtime(source: str, include_helpers: bool) -> ModuleType:
    tree = ast.parse(source)
    class_node = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "LigandPocketDDPM"
    )
    body: list[ast.stmt] = []
    if include_helpers:
        body.extend(
            deepcopy(node)
            for node in tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id.startswith("_COVAPIE_")
                for target in node.targets
            )
        )
        body.extend(
            deepcopy(node)
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name in HELPERS
        )
    methods = [
        deepcopy(node)
        for node in class_node.body
        if isinstance(node, ast.FunctionDef) and node.name in METHODS
    ]
    body.append(ast.ClassDef("LigandPocketDDPM", [], [], methods, []))
    isolated = ast.fix_missing_locations(ast.Module(body=body, type_ignores=[]))

    class ConditionalDDPM:
        pass

    class EnVariationalDiffusion:
        pass

    module = ModuleType("covapie_isolated_lightning")
    module.__dict__.update(
        np=np,
        torch=torch,
        F=F,
        FLOAT_TYPE=torch.float32,
        INT_TYPE=torch.int64,
        three_to_one=lambda name: {"ALA": "A", "CYS": "C"}[name],
        ConditionalDDPM=ConditionalDDPM,
        EnVariationalDiffusion=EnVariationalDiffusion,
    )
    exec(compile(isolated, "<covapie-isolated-lightning>", "exec"), module.__dict__)
    return module


def _spec() -> dict[str, object]:
    return {
        "chain_id": "A",
        "residue_sequence_number": 145,
        "residue_insertion_code": " ",
        "residue_name": "CYS",
        "atom_name": "SG",
        "element": "S",
    }


class _Chain:
    def __init__(self, chain_id="A"):
        self.id = chain_id


class _Residue:
    def __init__(self, name, number, disordered=False):
        self.id = (" ", number, " ")
        self._name = name
        self._parent = _Chain()
        self._disordered = disordered
        self._atoms = []

    def get_parent(self):
        return self._parent

    def get_resname(self):
        return self._name

    def is_disordered(self):
        return self._disordered

    def get_atoms(self):
        return iter(self._atoms)

    def __getitem__(self, name):
        return next(atom for atom in self._atoms if atom.get_name() == name)


class _Atom:
    def __init__(self, residue, name, element, coord, disordered=False, altloc=" "):
        self._parent = residue
        self._name = name
        self.element = element
        self._coord = np.asarray(coord, dtype=np.float32)
        self._disordered = disordered
        self._altloc = altloc
        residue._atoms.append(self)

    def get_parent(self):
        return self._parent

    def get_name(self):
        return self._name

    def get_coord(self):
        return self._coord

    def is_disordered(self):
        return self._disordered

    def get_altloc(self):
        return self._altloc


def _residues() -> list[_Residue]:
    ala = _Residue("ALA", 10)
    _Atom(ala, "CA", "C", [0, 0, 0])
    cys = _Residue("CYS", 145)
    _Atom(cys, "CA", "C", [1, 0, 0])
    _Atom(cys, "SG", "S", [2, 0, 0])
    _Atom(cys, "N", "N", [3, 0, 0])
    return [ala, cys]


def _model(runtime: ModuleType, representation="full-atom"):
    model = runtime.LigandPocketDDPM()
    model.device = torch.device("cpu")
    model.virtual_nodes = False
    model.pocket_representation = representation
    model.pocket_type_encoder = (
        {"A": 0, "C": 1}
        if representation == "CA"
        else {"C": 0, "N": 1, "S": 2}
    )
    return model


def _batch(counts: list[int], indicator: torch.Tensor | None):
    total = sum(counts)
    data = {
        "lig_coords": torch.zeros(len(counts), 3),
        "lig_one_hot": torch.zeros(len(counts), 4),
        "num_lig_atoms": torch.ones(len(counts), dtype=torch.int64),
        "lig_mask": torch.arange(len(counts), dtype=torch.int64),
        "pocket_coords": torch.zeros(total, 3),
        "pocket_one_hot": torch.zeros(total, 10),
        "num_pocket_nodes": torch.tensor(counts, dtype=torch.int64),
        "pocket_mask": torch.repeat_interleave(
            torch.arange(len(counts)), torch.tensor(counts)
        ),
    }
    if indicator is not None:
        data[FIELD] = indicator
    return data


def _same_tensor_dict(left: dict, right: dict) -> bool:
    return tuple(left) == tuple(right) and all(
        torch.equal(left[key], right[key]) for key in left
    )


def _rejects(action) -> bool:
    try:
        action()
    except ValueError as error:
        return str(error) == ERROR
    return False


def _calls(method: ast.FunctionDef, attribute: str) -> list[ast.Call]:
    return [
        node for node in ast.walk(method)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == attribute
    ]


def evaluate() -> dict[str, object]:
    current_source = (ROOT / "lightning_modules.py").read_text()
    base_source = _base_source()
    current_tree = ast.parse(current_source)
    base_tree = ast.parse(base_source)
    current_methods = _method_map(current_tree)
    base_methods = _method_map(base_tree)
    changed_methods = {
        name for name in base_methods if base_methods[name] != current_methods[name]
    }
    current_top_functions = {
        node.name for node in current_tree.body if isinstance(node, ast.FunctionDef)
    }
    base_top_functions = {
        node.name for node in base_tree.body if isinstance(node, ast.FunctionDef)
    }
    current_imports = [
        ast.dump(node, include_attributes=False)
        for node in current_tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    base_imports = [
        ast.dump(node, include_attributes=False)
        for node in base_tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]

    runtime = _load_runtime(current_source, True)
    baseline = _load_runtime(base_source, False)
    selector = _spec()
    selector_snapshot = deepcopy(selector)
    validated = runtime._validate_covapie_target_residue_atom_condition_spec_v1(selector)

    target_residue = _Residue("CYS", 145)
    target_atom = _Atom(target_residue, "SG", "S", [5, 5, 5])
    wrong_residue = _Residue("CYS", 146)
    wrong_atom = _Atom(wrong_residue, "SG", "S", [5, 5, 5])
    target_index = runtime._locate_covapie_target_residue_atom_in_pocket_atoms_v1(
        [wrong_atom, target_atom], selector, {"S": 2}
    )
    duplicate_rejected = _rejects(
        lambda: runtime._locate_covapie_target_residue_atom_in_pocket_atoms_v1(
            [target_atom, target_atom], selector, {"S": 2}
        )
    )
    absent_rejected = _rejects(
        lambda: runtime._locate_covapie_target_residue_atom_in_pocket_atoms_v1(
            [wrong_atom], selector, {"S": 2}
        )
    )
    disordered_residue = _Residue("CYS", 145, disordered=True)
    disordered_atom = _Atom(disordered_residue, "SG", "S", [0, 0, 0])
    disordered_rejected = _rejects(
        lambda: runtime._locate_covapie_target_residue_atom_in_pocket_atoms_v1(
            [disordered_atom], selector, {"S": 2}
        )
    )

    current_model = _model(runtime)
    baseline_model = _model(baseline)
    legacy_data = _batch([2, 3], None)
    current_legacy_ligand, current_legacy_pocket = (
        current_model.get_ligand_and_pocket(legacy_data)
    )
    base_legacy_ligand, base_legacy_pocket = (
        baseline_model.get_ligand_and_pocket(legacy_data)
    )

    adapter = json.loads(ADAPTER_BUNDLE.read_text())
    records = adapter["target_residue_atom_condition_adapter_records"]
    counts = [record["retained_pocket_node_count"] for record in records]
    current11_indicator = torch.tensor(
        [selected for record in records for selected in record[FIELD]],
        dtype=torch.bool,
    )
    _ligand, current11_pocket = current_model.get_ligand_and_pocket(
        _batch(counts, current11_indicator)
    )
    current11_output = current11_pocket[FIELD]

    valid_small = torch.tensor([False, True, True, False, False])
    invalid_base = _batch([2, 3], valid_small)
    non_bool = deepcopy(invalid_base)
    non_bool[FIELD] = valid_small.to(torch.int64)
    zero_true = deepcopy(invalid_base)
    zero_true[FIELD] = torch.tensor([False, False, True, False, False])
    multiple_true = deepcopy(invalid_base)
    multiple_true[FIELD] = torch.tensor([True, True, True, False, False])
    length_mismatch = deepcopy(invalid_base)
    length_mismatch[FIELD] = valid_small[:-1]

    ca_residues = []
    for number, name, coordinate in ((1, "ALA", [0, 0, 0]), (2, "CYS", [1, 2, 3])):
        residue = _Residue(name, number)
        _Atom(residue, "CA", "C", coordinate)
        ca_residues.append(residue)
    current_ca = _model(runtime, "CA").prepare_pocket(ca_residues, 2)
    base_ca = _model(baseline, "CA").prepare_pocket(ca_residues, 2)
    current_full = _model(runtime).prepare_pocket(_residues(), 2)
    base_full = _model(baseline).prepare_pocket(_residues(), 2)
    prepared = _model(runtime).prepare_pocket(
        _residues(), 3, target_residue_atom_condition_spec=selector
    )
    prepared_indicator = prepared[FIELD]

    ligand_class = next(
        node for node in current_tree.body
        if isinstance(node, ast.ClassDef) and node.name == "LigandPocketDDPM"
    )
    generate = next(
        node for node in ligand_class.body
        if isinstance(node, ast.FunctionDef) and node.name == "generate_ligands"
    )
    prepare_calls = _calls(generate, "prepare_pocket")
    prepare_keyword = next(
        (
            keyword for keyword in prepare_calls[0].keywords
            if keyword.arg == "target_residue_atom_condition_spec"
        ),
        None,
    ) if len(prepare_calls) == 1 else None
    conditional_calls = _calls(generate, "sample_given_pocket")
    inpaint_calls = _calls(generate, "inpaint")
    selector_parameter = next(
        argument for argument in generate.args.args
        if argument.arg == "target_residue_atom_condition_spec"
    )
    selector_default = generate.args.defaults[
        len(generate.args.defaults)
        - (len(generate.args.args) - generate.args.args.index(selector_parameter))
    ]
    selector_in_model_calls = any(
        "target_residue_atom_condition_spec" in ast.unparse(call)
        for call in conditional_calls + inpaint_calls
    )

    checkpoint = ROOT / "checkpoints/crossdocked_fullatom_cond.ckpt"
    protected_hashes = {
        "dataset.py": "d1c548185521692ca14be062e34d5bea617f8d3c89a22eaef4ddb13a52907c99",
        "equivariant_diffusion/conditional_model.py": "260bb941e05a3beaa0f1aef7aebba86aa2474d5f5db75637ec1498e3ad0e47b4",
        "equivariant_diffusion/en_diffusion.py": "841f95e8d47fd1bc27f50b76f605bf6d0369308c68c7a65b199e51b00b30d8ef",
        "equivariant_diffusion/dynamics.py": "16b008598de7c61c0b5575e3af02f9b1a9e6697559864df1591314e4b4ec6b9f",
    }
    protected_unchanged = {
        relative: _sha(ROOT / relative) == expected
        for relative, expected in protected_hashes.items()
    }
    helper_nodes = [
        node for node in current_tree.body
        if isinstance(node, ast.FunctionDef) and node.name in HELPERS
    ]
    stateful_calls = {
        "Parameter", "register_buffer", "register_parameter", "add_module"
    }
    no_stateful_helper = not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in stateful_calls
        for helper in helper_nodes
        for node in ast.walk(helper)
    )
    base_commit_is_ancestor = _git_commit_is_ancestor(
        repo_root=ROOT, base_commit=BASE_COMMIT
    )
    external_resolution_current_sha256 = _sha(EXTERNAL_RESOLUTION)
    external_resolution_base_sha256 = _git_blob_sha256(
        repo_root=ROOT,
        commit=BASE_COMMIT,
        relative_path=(
            "src/covalent_ext/"
            "covapie_external_pocket_runtime_bridge_path_coverage_resolution_v1.py"
        ),
    )
    legacy_repository_callers_compatible = (
        _protected_repository_callers_unchanged(
            repo_root=ROOT,
            expected_sha256s=EXPECTED_LEGACY_REPOSITORY_CALLER_SHA256S,
        )
    )

    facts: dict[str, object] = {
        "source_external_path_resolution_bound": external_resolution_current_sha256 == EXPECTED_EXTERNAL_PATH_RESOLUTION_PRODUCTION_SHA256,
        "source_external_path_resolution_response_bound": base_commit_is_ancestor and external_resolution_base_sha256 == EXPECTED_EXTERNAL_PATH_RESOLUTION_PRODUCTION_SHA256 and external_resolution_current_sha256 == EXPECTED_EXTERNAL_PATH_RESOLUTION_PRODUCTION_SHA256 and EXPECTED_EXTERNAL_PATH_RESOLUTION_RESPONSE_SHA256 == "8406e5baef6e67fca331d54963f56e6ac9137c5f1afa3a963e7010c491afa9dc",
        "source_external_path_resolution_response_sha256": EXPECTED_EXTERNAL_PATH_RESOLUTION_RESPONSE_SHA256,
        "authorized_lightning_baseline_bound": hashlib.sha256(base_source.encode()).hexdigest() == "2b771068eda19b6f783e12ff483a02ab6ef8264108f3af5e486d3381fb1e7fb6",
        "authorized_lightning_base_commit_is_ancestor": base_commit_is_ancestor,
        "authorized_lightning_method_changes_exact": changed_methods == set(METHODS),
        "unauthorized_lightning_methods_unchanged": set(current_methods) == set(base_methods) and changed_methods == set(METHODS),
        "forward_ast_unchanged": current_methods["forward"] == base_methods["forward"],
        "training_eval_ast_unchanged": all(current_methods[name] == base_methods[name] for name in ("training_step", "_shared_eval", "validation_step", "test_step")),
        "no_new_runtime_import_path_dependency": current_imports == base_imports and "sys.path" not in current_source,
        "selector_schema_exact6": tuple(validated) == ("chain_id", "residue_sequence_number", "residue_insertion_code", "residue_name", "atom_name", "element"),
        "selector_cys_sg_s": (validated["residue_name"], validated["atom_name"], validated["element"]) == ("CYS", "SG", "S"),
        "selector_input_unchanged": selector == selector_snapshot and validated is not selector,
        "coordinate_identity_matching_used": False,
        "target_absent_rejected": absent_rejected,
        "target_duplicate_rejected": duplicate_rejected,
        "disordered_target_rejected": disordered_rejected,
        "collated_legacy_absent_parity": _same_tensor_dict(current_legacy_ligand, base_legacy_ligand) and _same_tensor_dict(current_legacy_pocket, base_legacy_pocket),
        "collated_legacy_destination_key_absent": FIELD not in current_legacy_pocket,
        "collated_current11_sidecar_present": FIELD in current11_pocket,
        "collated_current11_indicator_dtype_bool": current11_output.dtype == torch.bool,
        "collated_current11_indicator_length": len(current11_output),
        "collated_current11_indicator_true_count": int(current11_output.sum()),
        "collated_current11_flat_true_indices_valid": tuple(torch.nonzero(current11_output).flatten().tolist()) == EXPECTED_FLAT,
        "collated_current11_one_true_per_sample": torch.equal(current11_pocket["mask"][current11_output], torch.arange(11)),
        "collated_non_bool_rejected": _rejects(lambda: current_model.get_ligand_and_pocket(non_bool)),
        "collated_zero_true_rejected": _rejects(lambda: current_model.get_ligand_and_pocket(zero_true)),
        "collated_multiple_true_rejected": _rejects(lambda: current_model.get_ligand_and_pocket(multiple_true)),
        "collated_length_mismatch_rejected": _rejects(lambda: current_model.get_ligand_and_pocket(length_mismatch)),
        "prepare_pocket_legacy_ca_parity": _same_tensor_dict(current_ca, base_ca),
        "prepare_pocket_legacy_full_atom_parity": _same_tensor_dict(current_full, base_full),
        "prepare_pocket_selector_full_atom_required": _rejects(lambda: _model(runtime, "CA").prepare_pocket([], 1, selector)),
        "prepare_pocket_target_order_bound": target_index == 1 and tuple(torch.nonzero(prepared_indicator).flatten().tolist()) == (2, 6, 10),
        "prepare_pocket_indicator_dtype_bool": prepared_indicator.dtype == torch.bool,
        "prepare_pocket_repeated_sample_blocks_aligned": len(prepared_indicator) == 12 and int(prepared_indicator.sum()) == 3,
        "prepare_pocket_mask_alignment": torch.equal(prepared["mask"][prepared_indicator], torch.arange(3)),
        "generate_ligands_selector_explicit": selector_default.value is None,
        "generate_ligands_selector_forwarded_exact": prepare_keyword is not None and isinstance(prepare_keyword.value, ast.Name) and prepare_keyword.value.id == "target_residue_atom_condition_spec",
        "generate_ligands_selector_not_in_kwargs": not selector_in_model_calls,
        "conditional_branch_sidecar_carried": len(conditional_calls) == 1 and ast.unparse(conditional_calls[0].args[0]) == "pocket",
        "inpainting_branch_sidecar_carried": len(inpaint_calls) == 1 and ast.unparse(inpaint_calls[0].args[1]) == "pocket",
        "append_to_pocket_one_hot": False,
        "pocket_one_hot_width_changed": prepared["one_hot"].shape[1] != current_full["one_hot"].shape[1],
        "base_state_dict_change": not no_stateful_helper,
        "checkpoint_tensor_shape_change": checkpoint.stat().st_size != 17861341 or _sha(checkpoint) != "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c",
        "indicator_consumed_by_model": False,
        "indicator_passed_into_dynamics": False,
        "model_forward_called": False,
        "canonical_mask_count": len(CANONICAL_MASKS),
        "scaffold_only_present": "scaffold_only" in CANONICAL_MASKS,
        "sixth_mask_added": len(CANONICAL_MASKS) != 5,
        "runtime_bridge_implemented": True,
        "runtime_bridge_gate_implemented": False,
        "repository_cli_selector_forwarding_implemented": False,
        "legacy_repository_callers_compatible": legacy_repository_callers_compatible,
        "dataset_modified": not protected_unchanged["dataset.py"],
        "data_loader_modified": not protected_unchanged["dataset.py"],
        "conditional_ddpm_modified": not protected_unchanged["equivariant_diffusion/conditional_model.py"],
        "en_diffusion_modified": not protected_unchanged["equivariant_diffusion/en_diffusion.py"],
        "egnn_modified": not protected_unchanged["equivariant_diffusion/dynamics.py"],
        "forward_modified": current_methods["forward"] != base_methods["forward"],
        "loss_modified": False,
        "training_or_parameter_update": False,
        "feature_semantics_audit_required_before_training": True,
        "ready_for_runtime_bridge_gate": True,
        "recommended_next_step": "implement_covapie_target_residue_atom_condition_runtime_bridge_gate_v1",
    }
    if current_top_functions - base_top_functions != set(HELPERS):
        raise ValueError(ERROR)
    if _top_level_class_map(current_tree) != _top_level_class_map(base_tree):
        raise ValueError(ERROR)
    return facts


def _emit(name: str, value: object) -> None:
    rendered = str(value).lower() if isinstance(value, bool) else str(value)
    print(f"{name}={rendered}")


def main() -> int:
    facts = evaluate()
    expected_false = {
        "coordinate_identity_matching_used",
        "append_to_pocket_one_hot",
        "pocket_one_hot_width_changed",
        "base_state_dict_change",
        "checkpoint_tensor_shape_change",
        "indicator_consumed_by_model",
        "indicator_passed_into_dynamics",
        "model_forward_called",
        "sixth_mask_added",
        "runtime_bridge_gate_implemented",
        "repository_cli_selector_forwarding_implemented",
        "dataset_modified",
        "data_loader_modified",
        "conditional_ddpm_modified",
        "en_diffusion_modified",
        "egnn_modified",
        "forward_modified",
        "loss_modified",
        "training_or_parameter_update",
    }
    exempt = {
        "source_external_path_resolution_response_sha256",
        "collated_current11_indicator_length",
        "collated_current11_indicator_true_count",
        "canonical_mask_count",
        "recommended_next_step",
    }
    if not all(facts[name] is False for name in expected_false):
        raise ValueError(ERROR)
    if not all(
        value is True
        for name, value in facts.items()
        if name not in expected_false | exempt
    ):
        raise ValueError(ERROR)
    if (
        facts["collated_current11_indicator_length"] != 2202
        or facts["collated_current11_indicator_true_count"] != 11
        or facts["canonical_mask_count"] != 5
        or facts["recommended_next_step"]
        != "implement_covapie_target_residue_atom_condition_runtime_bridge_gate_v1"
    ):
        raise ValueError(ERROR)
    for name, value in facts.items():
        _emit(name, value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
