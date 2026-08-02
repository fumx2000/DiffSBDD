"""Successor gate for the CovaPIE target-residue runtime bridge V1.

The gate binds the committed bridge, reconstructs its Current11 and external
runtime evidence with an isolated AST loader, and preserves the checkpoint and
legacy caller boundaries.  It never imports the complete Lightning module,
calls a model forward path, or mutates repository state.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import secrets
import stat
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any, Mapping, Sequence

import numpy as np
import torch
import torch.nn.functional as F

from covalent_ext import covapie_current11_pocket_atom_identity_alignment_v1 as alignment
from covalent_ext import covapie_current11_target_residue_atom_condition_authority_v1 as authority
from covalent_ext import covapie_target_residue_atom_condition_adapter_gate_v1 as adapter_gate
from covalent_ext import covapie_target_residue_atom_condition_adapter_v1 as adapter


__all__ = (
    "evaluate_covapie_target_residue_atom_condition_runtime_bridge_gate_v1",
)


_ERROR = "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_RUNTIME_BRIDGE_GATE_INVALID"
_RUNTIME_ERROR = "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_RUNTIME_BRIDGE_INVALID"
_VERSION = "covapie_target_residue_atom_condition_runtime_bridge_gate_v1"
_RECORD_VERSION = "covapie_target_residue_atom_condition_runtime_bridge_gate_record_v1"
_FIELD = "pocket_target_residue_atom_condition_indicator"
_BASE_COMMIT = "6f3ba8eb0dcb2982a14f5bdc0c7319b0a4e79250"
_IMPLEMENTATION_COMMIT = "75589a94235dde2d0943606e58a1f2216b31d3b2"
_IMPLEMENTATION_SUBJECT = "add CovaPIE target residue atom condition runtime bridge v1"
_AUTHORITY_TRANSPORT_SHA256 = "a95ae52e091a7117b241269eebd891f3ee97e3ae4a6b4e14fa441ab6a1ed2096"
_ALIGNMENT_TRANSPORT_SHA256 = "7f80a810ff35c4ea5d61262021379767a4d15202badd8ec6a6b846405147d842"
_ADAPTER_TRANSPORT_SHA256 = "983c25ea8c52ca54f0c0292990a625e9a9cf0d2370cb517d66a84801d957b65a"
_ADAPTER_GATE_TRANSPORT_SHA256 = "c7e2c9eec92d560fc55206399d9b27df511733821ce3233c3546da38d9992a9d"
_ADAPTER_GATE_INTERNAL_SHA256 = "97821184d8c76618bb549dd708132bd9579687c6f3a0ba8007d0bbc80d7d6602"
_EXTERNAL_PRODUCTION_SHA256 = "02bbf44ca3602576b252678f499a1219e4d3ee2db170ed2abd474983cf5a3232"
_EXTERNAL_RESPONSE_SHA256 = "8406e5baef6e67fca331d54963f56e6ac9137c5f1afa3a963e7010c491afa9dc"
_LIGHTNING_SHA256 = "8d111f8c45d90cbdf6d0dcf7f4e4796bc7ebe0f1b0065e750eab0a16b4c01d5a"
_RUNTIME_TEST_SHA256 = "1283855160f2ca52884ec79e16330f5b7885cc81d6fcb74a90c1832564392868"
_RUNTIME_CHECKER_SHA256 = "211ece15b5a8595c2fc539724fa59a463bbb35b4ce04da1603f4f4880a7d8560"
_RUNTIME_GUIDE_SHA256 = "e8cd93b0cc45b3245483442f6667541eae81390466e31cae26221dbf723b5942"
_RUNTIME_CHECKER_STDOUT_SHA256 = "1e872567f4ae09be6dc15bf1ef7bbd738c6f4fb395cddb067cde4e6acf3e4218"
_CHECKPOINT_SHA256 = "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
_CHECKPOINT_SIZE = 17861341
_MAX_BYTES = 32 * 1024 * 1024
_MAX_BUNDLE_BYTES = 2 * 1024 * 1024

_RUNTIME_FILES = {
    "lightning_modules.py": _LIGHTNING_SHA256,
    "tests/test_covapie_target_residue_atom_condition_runtime_bridge_v1.py": _RUNTIME_TEST_SHA256,
    "scripts/check_covapie_target_residue_atom_condition_runtime_bridge_v1.py": _RUNTIME_CHECKER_SHA256,
    "docs/covapie_target_residue_atom_condition_runtime_bridge_v1_guide.md": _RUNTIME_GUIDE_SHA256,
}
_PROTECTED_SOURCES = {
    "dataset.py": "d1c548185521692ca14be062e34d5bea617f8d3c89a22eaef4ddb13a52907c99",
    "equivariant_diffusion/conditional_model.py": "260bb941e05a3beaa0f1aef7aebba86aa2474d5f5db75637ec1498e3ad0e47b4",
    "equivariant_diffusion/en_diffusion.py": "841f95e8d47fd1bc27f50b76f605bf6d0369308c68c7a65b199e51b00b30d8ef",
    "equivariant_diffusion/dynamics.py": "16b008598de7c61c0b5575e3af02f9b1a9e6697559864df1591314e4b4ec6b9f",
}
_CALLER_SHA256S = {
    "generate_ligands.py": "8884e63ddb7f0fa84bd89bfd956fbefa10db687fa0cfc3380b85d06837be4474",
    "test.py": "954e63ade5e8b8f811897e40b22d81308451054753327cd9de2942c658dfd7bf",
    "optimize.py": "d51c32b3902accf24698f2b3abdfdf0e1a5d3150b90515a1b8d1b13d3e7d229b",
    "inpaint.py": "2d6cf0542c4b82e25eed19165d6f90d004ae4ced1db426962e47fb6086e085d9",
    "scripts/covalent_inpaint_demo.py": "1866dde2a7909fb431617dfa9f7de5a297b895de7930313655685823944f72a9",
    "colab/DiffSBDD.ipynb": "0d7fdc6a8377aa41e8d2104c39b2120964eee7f02b21c2bb56ca415dc889a123",
}
_EXPECTED_SAMPLES = tuple(f"CYS_SG_SAMPLE_INDEX_{index:06d}" for index in range(1, 12))
_EXPECTED_LOCAL = (49, 15, 12, 33, 31, 50, 48, 53, 52, 53, 84)
_EXPECTED_FLAT = (49, 81, 182, 299, 505, 712, 988, 1260, 1516, 1766, 2058)
_CURRENT11_LINEAGE_PROJECTION_SHA256 = "c4918fd0ee226de4bdee5aded27e06b615ca56c8f5085c044ef035cf172d71e9"
_CURRENT11_LINEAGE_PROJECTION_FIELDS = (
    "sample",
    "pdb_id",
    "source_adapter_record_sha256",
    "retained_pocket_node_count",
    "expected_local_true_index",
    "expected_flat_true_index",
    "runtime_mask_sample_id",
)
_METHODS = ("get_ligand_and_pocket", "prepare_pocket", "generate_ligands")
_HELPERS = (
    "_validate_covapie_target_residue_atom_condition_spec_v1",
    "_locate_covapie_target_residue_atom_in_pocket_atoms_v1",
    "_build_covapie_repeated_target_residue_atom_condition_indicator_v1",
    "_validate_covapie_collated_target_residue_atom_condition_indicator_v1",
)
_CONSTANTS = (
    "_COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_SPEC_FIELDS",
    "_COVAPIE_POCKET_TARGET_RESIDUE_ATOM_CONDITION_INDICATOR_FIELD",
    "_COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_RUNTIME_BRIDGE_ERROR",
)

CANONICAL_MASK_SEMANTIC_NAMES = (
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
)

RUNTIME_BRIDGE_GATE_RECORD_FIELDS = (
    "runtime_bridge_gate_record_version",
    "sample",
    "pdb_id",
    "source_adapter_record_sha256",
    "retained_pocket_node_count",
    "expected_local_true_index",
    "expected_flat_true_index",
    "runtime_indicator_dtype",
    "runtime_indicator_length",
    "runtime_indicator_true_count",
    "runtime_local_true_index",
    "runtime_flat_true_index",
    "runtime_target_s_feature_index",
    "runtime_pocket_one_hot_width",
    "runtime_mask_sample_id",
    "sidecar_field_name",
    "node_order_preserved",
    "status",
    "blockers",
    "runtime_bridge_gate_record_sha256",
)

RUNTIME_BRIDGE_GATE_BUNDLE_FIELDS = (
    "runtime_bridge_gate_version",
    "source_authority_bundle_transport_sha256",
    "source_alignment_bundle_transport_sha256",
    "source_adapter_bundle_transport_sha256",
    "source_adapter_gate_bundle_transport_sha256",
    "source_adapter_gate_bundle_sha256",
    "source_external_path_resolution_production_sha256",
    "source_external_path_resolution_response_sha256",
    "source_runtime_bridge_commit",
    "source_runtime_bridge_parent_commit",
    "source_lightning_module_sha256",
    "source_runtime_bridge_test_sha256",
    "source_runtime_bridge_checker_sha256",
    "source_runtime_bridge_guide_sha256",
    "source_runtime_bridge_checker_stdout_sha256",
    "sidecar_field_name",
    "current11_record_fields",
    "current11_records",
    "current11_record_count",
    "runtime_dataset_sample_count",
    "total_runtime_pocket_node_count",
    "total_runtime_indicator_true_count",
    "collated_flat_true_indices",
    "legacy_collated_absent_parity",
    "legacy_prepare_pocket_ca_parity",
    "legacy_prepare_pocket_full_atom_parity",
    "external_selector_exact6_validated",
    "external_prepare_pocket_repeat_validated",
    "conditional_branch_sidecar_carried",
    "inpainting_branch_sidecar_carried",
    "authorized_lightning_ast_boundary_valid",
    "checkpoint_compatibility_preserved",
    "repository_cli_selector_forwarding_implemented",
    "indicator_consumed_by_model",
    "indicator_passed_into_dynamics",
    "ready_for_model_consumption_design",
    "recommended_next_step",
    "feature_semantics_audit_required_before_training",
    "runtime_bridge_gate_bundle_sha256",
)


class _DuplicateKeyError(ValueError):
    pass


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":")
    ).encode("utf-8")


def _digest_record(record: Mapping[str, Any], fields: Sequence[str], digest_field: str) -> str:
    if tuple(record) != tuple(fields):
        raise ValueError(_ERROR)
    return _sha256(
        _canonical_json_bytes({field: record[field] for field in fields if field != digest_field})
    )


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


def _read_regular(path: Path, *, maximum: int = _MAX_BYTES) -> bytes:
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


def _git(repo_root: Path, arguments: list[str], *, allow_one: bool = False) -> bytes:
    completed = subprocess.run(
        ["git", *arguments], cwd=repo_root, check=False, capture_output=True
    )
    valid_codes = (0, 1) if allow_one else (0,)
    if completed.returncode not in valid_codes or completed.stderr != b"":
        raise ValueError(_ERROR)
    return completed.stdout


def _git_show(repo_root: Path, commit: str, relative_path: str) -> bytes:
    relative = Path(relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(_ERROR)
    return _git(repo_root, ["show", f"{commit}:{relative.as_posix()}"])


def _method_map(tree: ast.Module) -> dict[str, str]:
    class_node = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "LigandPocketDDPM"
    )
    return {
        node.name: ast.dump(node, include_attributes=False)
        for node in class_node.body if isinstance(node, ast.FunctionDef)
    }


def _other_class_map(tree: ast.Module) -> dict[str, str]:
    return {
        node.name: ast.dump(node, include_attributes=False)
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name != "LigandPocketDDPM"
    }


def _load_runtime(source: str, *, include_bridge: bool) -> ModuleType:
    tree = ast.parse(source)
    class_node = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "LigandPocketDDPM"
    )
    body: list[ast.stmt] = []
    if include_bridge:
        for name in _CONSTANTS:
            matches = [
                node for node in tree.body
                if isinstance(node, (ast.Assign, ast.AnnAssign))
                and any(
                    isinstance(target, ast.Name) and target.id == name
                    for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
                )
            ]
            if len(matches) != 1:
                raise ValueError(_ERROR)
            body.append(deepcopy(matches[0]))
        for name in _HELPERS:
            matches = [
                node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == name
            ]
            if len(matches) != 1:
                raise ValueError(_ERROR)
            body.append(deepcopy(matches[0]))
    methods = [
        deepcopy(node) for node in class_node.body
        if isinstance(node, ast.FunctionDef) and node.name in _METHODS
    ]
    if len(methods) != len(_METHODS):
        raise ValueError(_ERROR)
    body.append(ast.ClassDef("LigandPocketDDPM", [], [], methods, []))
    isolated = ast.fix_missing_locations(ast.Module(body=body, type_ignores=[]))

    class ConditionalDDPM:
        pass

    class EnVariationalDiffusion:
        pass

    module = ModuleType("covapie_runtime_bridge_gate_isolated")
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
    exec(compile(isolated, "<covapie-runtime-bridge-gate-isolated>", "exec"), module.__dict__)
    return module


def _spec(**updates: object) -> dict[str, object]:
    value: dict[str, object] = {
        "chain_id": "A",
        "residue_sequence_number": 145,
        "residue_insertion_code": " ",
        "residue_name": "CYS",
        "atom_name": "SG",
        "element": "S",
    }
    value.update(updates)
    return value


class _Chain:
    def __init__(self, chain_id: str = "A"):
        self.id = chain_id


class _Residue:
    def __init__(
        self, name: str = "CYS", number: int = 145, chain: str = "A",
        disordered: bool = False,
    ):
        self.id = (" ", number, " ")
        self._name = name
        self._parent = _Chain(chain)
        self._disordered = disordered
        self._atoms: list[_Atom] = []

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
    def __init__(
        self, residue: _Residue, name: str, element: str, coordinate: Sequence[float],
        *, disordered: bool = False, altloc: str = " ",
    ):
        self._parent = residue
        self._name = name
        self.element = element
        self._coordinate = np.asarray(coordinate, dtype=np.float32)
        self._disordered = disordered
        self._altloc = altloc
        residue._atoms.append(self)

    def get_parent(self):
        return self._parent

    def get_name(self):
        return self._name

    def get_coord(self):
        return self._coordinate

    def is_disordered(self):
        return self._disordered

    def get_altloc(self):
        return self._altloc


def _full_atom_residues() -> list[_Residue]:
    ala = _Residue("ALA", 10)
    _Atom(ala, "CA", "C", (0, 0, 0))
    cys = _Residue("CYS", 145)
    _Atom(cys, "CA", "C", (1, 0, 0))
    _Atom(cys, "SG", "S", (2, 0, 0))
    _Atom(cys, "N", "N", (3, 0, 0))
    return [ala, cys]


def _model(runtime: ModuleType, representation: str = "full-atom"):
    model = runtime.LigandPocketDDPM()
    model.device = torch.device("cpu")
    model.virtual_nodes = False
    model.pocket_representation = representation
    model.pocket_type_encoder = (
        {"A": 0, "C": 1} if representation == "CA" else {"C": 0, "N": 1, "S": 2}
    )
    return model


def _batch(counts: Sequence[int], indicator: torch.Tensor | None, one_hot_width: int = 10):
    total = sum(counts)
    data = {
        "lig_coords": torch.zeros(len(counts), 3),
        "lig_one_hot": torch.zeros(len(counts), 4),
        "num_lig_atoms": torch.ones(len(counts), dtype=torch.int64),
        "lig_mask": torch.arange(len(counts), dtype=torch.int64),
        "pocket_coords": torch.arange(total * 3, dtype=torch.float32).view(total, 3),
        "pocket_one_hot": torch.zeros(total, one_hot_width),
        "num_pocket_nodes": torch.tensor(counts, dtype=torch.int64),
        "pocket_mask": torch.repeat_interleave(
            torch.arange(len(counts), dtype=torch.int64),
            torch.tensor(counts, dtype=torch.int64),
        ),
    }
    if indicator is not None:
        data[_FIELD] = indicator
    return data


def _same_tensor_dict(left: Mapping[str, torch.Tensor], right: Mapping[str, torch.Tensor]) -> bool:
    return tuple(left) == tuple(right) and all(torch.equal(left[key], right[key]) for key in left)


def _rejects_runtime(action) -> bool:
    try:
        action()
    except ValueError as error:
        return str(error) == _RUNTIME_ERROR
    return False


def _scatter_mean(values: torch.Tensor, mask: torch.Tensor, dim: int = 0) -> torch.Tensor:
    if dim != 0:
        raise ValueError(_ERROR)
    return torch.stack(
        [values[mask == sample].mean(0) for sample in range(int(mask.max()) + 1)]
    )


def _exercise_generate(runtime: ModuleType, branch: str, selector: dict[str, object]):
    model = _model(runtime)
    model.x_dims = 3
    model.atom_nf = 2
    model.dataset_info = {}
    prepared = {
        "x": torch.tensor([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]).repeat(2, 1),
        "one_hot": torch.zeros(4, 3),
        "size": torch.tensor([2, 2]),
        "mask": torch.tensor([0, 0, 1, 1]),
        _FIELD: torch.tensor([False, True, False, True]),
    }
    seen: dict[str, Any] = {}

    def prepare(residues, repeats, target_residue_atom_condition_spec):
        seen["prepare"] = (residues, repeats, target_residue_atom_condition_spec)
        return prepared

    model.prepare_pocket = prepare
    ddpm_class = runtime.ConditionalDDPM if branch == "conditional" else runtime.EnVariationalDiffusion
    model.ddpm = ddpm_class()
    model.ddpm.eval = lambda: None

    def outputs(pocket):
        seen["pocket"] = pocket
        ligand = torch.zeros(2, 5)
        ligand[:, 3] = 1
        return ligand, torch.cat((pocket["x"], pocket["one_hot"]), dim=1), torch.arange(2), pocket["mask"]

    if branch == "conditional":
        def sample_given_pocket(pocket, num_nodes_lig, timesteps=None):
            seen["sample_kwargs"] = {"timesteps": timesteps}
            return outputs(pocket)
        model.ddpm.sample_given_pocket = sample_given_pocket
    else:
        def inpaint(ligand, pocket, lig_fixed, pocket_fixed, **kwargs):
            seen["inpaint_kwargs"] = kwargs
            return outputs(pocket)
        model.ddpm.inpaint = inpaint

    residues = object()
    runtime.PDBParser = lambda QUIET: SimpleNamespace(
        get_structure=lambda _name, _path: [object()]
    )
    runtime.utils = SimpleNamespace(
        get_pocket_from_ligand=lambda structure, ref: residues,
        num_nodes_to_batch_mask=lambda count, nodes, device: torch.arange(count),
        batch_to_list=lambda values, mask: [values[mask == sample] for sample in range(2)],
    )
    runtime.scatter_mean = _scatter_mean
    runtime.build_molecule = lambda *args, **kwargs: object()
    runtime.process_molecule = lambda molecule, **kwargs: molecule
    molecules = model.generate_ligands(
        "unused.pdb", 2, ref_ligand="unused.sdf",
        num_nodes_lig=torch.ones(2, dtype=torch.int64),
        target_residue_atom_condition_spec=selector,
        probe="only-inpaint",
    )
    return molecules, prepared, seen


def _run_runtime_checker(repo_root: Path) -> tuple[bytes, dict[str, str]]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = "src"
    command = [
        sys.executable,
        "-B",
        "scripts/check_covapie_target_residue_atom_condition_runtime_bridge_v1.py",
    ]
    outputs: list[bytes] = []
    for _ in range(2):
        completed = subprocess.run(
            command, cwd=repo_root, env=environment, check=False,
            capture_output=True, timeout=180,
        )
        if completed.returncode != 0 or completed.stderr != b"":
            raise ValueError(_ERROR)
        outputs.append(completed.stdout)
    if outputs[0] != outputs[1] or _sha256(outputs[0]) != _RUNTIME_CHECKER_STDOUT_SHA256:
        raise ValueError(_ERROR)
    parsed: dict[str, str] = {}
    try:
        for line in outputs[0].decode("utf-8", errors="strict").splitlines():
            key, value = line.split("=", 1)
            if not key or key in parsed:
                raise ValueError(_ERROR)
            parsed[key] = value
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
    expected_true = {
        "authorized_lightning_base_commit_is_ancestor",
        "authorized_lightning_method_changes_exact",
        "unauthorized_lightning_methods_unchanged",
        "forward_ast_unchanged",
        "training_eval_ast_unchanged",
        "collated_current11_flat_true_indices_valid",
        "collated_current11_one_true_per_sample",
        "prepare_pocket_legacy_ca_parity",
        "prepare_pocket_legacy_full_atom_parity",
        "generate_ligands_selector_forwarded_exact",
        "conditional_branch_sidecar_carried",
        "inpainting_branch_sidecar_carried",
        "legacy_repository_callers_compatible",
        "runtime_bridge_implemented",
        "ready_for_runtime_bridge_gate",
    }
    expected_false = {
        "append_to_pocket_one_hot",
        "base_state_dict_change",
        "checkpoint_tensor_shape_change",
        "indicator_consumed_by_model",
        "indicator_passed_into_dynamics",
        "model_forward_called",
        "runtime_bridge_gate_implemented",
    }
    if (
        any(parsed.get(key) != "true" for key in expected_true)
        or any(parsed.get(key) != "false" for key in expected_false)
        or parsed.get("collated_current11_indicator_length") != "2202"
        or parsed.get("collated_current11_indicator_true_count") != "11"
        or parsed.get("recommended_next_step")
        != "implement_covapie_target_residue_atom_condition_runtime_bridge_gate_v1"
    ):
        raise ValueError(_ERROR)
    return outputs[0], parsed


def _is_lowercase_sha256(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _expected_current11_runtime_bridge_gate_record_lineage(
    adapter_records: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """Project the formal adapter lineage used by both builder and validator."""

    try:
        if type(adapter_records) is not list or len(adapter_records) != 11:
            raise ValueError(_ERROR)
        projection: list[dict[str, Any]] = []
        flat_start = 0
        for sample_index, adapter_record in enumerate(adapter_records):
            expected_sample = _EXPECTED_SAMPLES[sample_index]
            sample = adapter_record.get("sample_index_row_id")
            pdb_id = adapter_record.get("pdb_id")
            source_sha256 = adapter_record.get(
                "target_residue_atom_condition_adapter_record_sha256"
            )
            count = adapter_record.get("retained_pocket_node_count")
            local_index = adapter_record.get("target_retained_model_local_index")
            if (
                type(adapter_record) is not dict
                or sample != expected_sample
                or type(pdb_id) is not str
                or not pdb_id
                or not _is_lowercase_sha256(source_sha256)
                or type(count) is not int
                or type(count) is bool
                or count <= 0
                or type(local_index) is not int
                or type(local_index) is bool
                or not 0 <= local_index < count
            ):
                raise ValueError(_ERROR)
            projection.append({
                "sample": sample,
                "pdb_id": pdb_id,
                "source_adapter_record_sha256": source_sha256,
                "retained_pocket_node_count": count,
                "expected_local_true_index": local_index,
                "expected_flat_true_index": flat_start + local_index,
                "runtime_mask_sample_id": sample_index,
            })
            flat_start += count
        result = tuple(projection)
        if (
            flat_start != 2202
            or tuple(item["expected_flat_true_index"] for item in result)
            != _EXPECTED_FLAT
            or _sha256(_canonical_json_bytes(result))
            != _CURRENT11_LINEAGE_PROJECTION_SHA256
        ):
            raise ValueError(_ERROR)
        return result
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _current11_runtime_bridge_gate_record_lineage_projection(
    records: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], ...]:
    """Project the lineage-bearing fields from candidate Exact20 records."""

    try:
        if type(records) is not list or len(records) != 11:
            raise ValueError(_ERROR)
        return tuple({
            field: record[field]
            for field in _CURRENT11_LINEAGE_PROJECTION_FIELDS
        } for record in records)
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _validate_record(record: Mapping[str, Any], *, require_field_order: bool) -> bool:
    try:
        ordered = {field: record[field] for field in RUNTIME_BRIDGE_GATE_RECORD_FIELDS}
        count = record["retained_pocket_node_count"]
        local = record["expected_local_true_index"]
        if (
            type(record) is not dict
            or len(record) != 20
            or set(record) != set(RUNTIME_BRIDGE_GATE_RECORD_FIELDS)
            or (require_field_order and tuple(record) != RUNTIME_BRIDGE_GATE_RECORD_FIELDS)
            or record["runtime_bridge_gate_record_version"] != _RECORD_VERSION
            or type(record["sample"]) is not str or not record["sample"]
            or type(record["pdb_id"]) is not str or not record["pdb_id"]
            or not _is_lowercase_sha256(record["source_adapter_record_sha256"])
            or type(count) is not int or type(count) is bool or count <= 0
            or type(local) is not int or type(local) is bool or not 0 <= local < count
            or type(record["expected_flat_true_index"]) is not int
            or type(record["expected_flat_true_index"]) is bool
            or record["expected_flat_true_index"] < 0
            or record["runtime_indicator_dtype"] != "torch.bool"
            or type(record["runtime_indicator_length"]) is not int
            or type(record["runtime_indicator_length"]) is bool
            or record["runtime_indicator_length"] <= 0
            or record["runtime_indicator_length"] != count
            or type(record["runtime_indicator_true_count"]) is not int
            or type(record["runtime_indicator_true_count"]) is bool
            or record["runtime_indicator_true_count"] != 1
            or type(record["runtime_local_true_index"]) is not int
            or type(record["runtime_local_true_index"]) is bool
            or record["runtime_local_true_index"] != local
            or type(record["runtime_flat_true_index"]) is not int
            or type(record["runtime_flat_true_index"]) is bool
            or record["runtime_flat_true_index"] != record["expected_flat_true_index"]
            or type(record["runtime_target_s_feature_index"]) is not int
            or type(record["runtime_target_s_feature_index"]) is bool
            or record["runtime_target_s_feature_index"] != 3
            or type(record["runtime_pocket_one_hot_width"]) is not int
            or type(record["runtime_pocket_one_hot_width"]) is bool
            or record["runtime_pocket_one_hot_width"] != 10
            or type(record["runtime_mask_sample_id"]) is not int
            or type(record["runtime_mask_sample_id"]) is bool
            or not 0 <= record["runtime_mask_sample_id"] <= 10
            or record["sidecar_field_name"] != _FIELD
            or record["node_order_preserved"] is not True
            or record["status"] != "runtime_bridge_gate_ready_unique"
            or record["blockers"] != []
            or record["runtime_bridge_gate_record_sha256"]
            != _digest_record(
                ordered, RUNTIME_BRIDGE_GATE_RECORD_FIELDS,
                "runtime_bridge_gate_record_sha256",
            )
        ):
            raise ValueError(_ERROR)
        return True
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _validate_bundle(bundle: Mapping[str, Any], *, require_field_order: bool) -> bool:
    try:
        ordered = {field: bundle[field] for field in RUNTIME_BRIDGE_GATE_BUNDLE_FIELDS}
        records = bundle["current11_records"]
        if (
            type(bundle) is not dict
            or len(bundle) != 39
            or set(bundle) != set(RUNTIME_BRIDGE_GATE_BUNDLE_FIELDS)
            or (require_field_order and tuple(bundle) != RUNTIME_BRIDGE_GATE_BUNDLE_FIELDS)
            or bundle["runtime_bridge_gate_version"] != _VERSION
            or bundle["source_authority_bundle_transport_sha256"] != _AUTHORITY_TRANSPORT_SHA256
            or bundle["source_alignment_bundle_transport_sha256"] != _ALIGNMENT_TRANSPORT_SHA256
            or bundle["source_adapter_bundle_transport_sha256"] != _ADAPTER_TRANSPORT_SHA256
            or bundle["source_adapter_gate_bundle_transport_sha256"] != _ADAPTER_GATE_TRANSPORT_SHA256
            or bundle["source_adapter_gate_bundle_sha256"] != _ADAPTER_GATE_INTERNAL_SHA256
            or bundle["source_external_path_resolution_production_sha256"] != _EXTERNAL_PRODUCTION_SHA256
            or bundle["source_external_path_resolution_response_sha256"] != _EXTERNAL_RESPONSE_SHA256
            or bundle["source_runtime_bridge_commit"] != _IMPLEMENTATION_COMMIT
            or bundle["source_runtime_bridge_parent_commit"] != _BASE_COMMIT
            or bundle["source_lightning_module_sha256"] != _LIGHTNING_SHA256
            or bundle["source_runtime_bridge_test_sha256"] != _RUNTIME_TEST_SHA256
            or bundle["source_runtime_bridge_checker_sha256"] != _RUNTIME_CHECKER_SHA256
            or bundle["source_runtime_bridge_guide_sha256"] != _RUNTIME_GUIDE_SHA256
            or bundle["source_runtime_bridge_checker_stdout_sha256"] != _RUNTIME_CHECKER_STDOUT_SHA256
            or bundle["sidecar_field_name"] != _FIELD
            or tuple(bundle["current11_record_fields"]) != RUNTIME_BRIDGE_GATE_RECORD_FIELDS
            or type(records) is not list or len(records) != 11
            or bundle["current11_record_count"] != 11
            or bundle["runtime_dataset_sample_count"] != 11
            or bundle["total_runtime_pocket_node_count"] != 2202
            or bundle["total_runtime_indicator_true_count"] != 11
            or tuple(bundle["collated_flat_true_indices"]) != _EXPECTED_FLAT
            or any(bundle[field] is not True for field in (
                "legacy_collated_absent_parity",
                "legacy_prepare_pocket_ca_parity",
                "legacy_prepare_pocket_full_atom_parity",
                "external_selector_exact6_validated",
                "external_prepare_pocket_repeat_validated",
                "conditional_branch_sidecar_carried",
                "inpainting_branch_sidecar_carried",
                "authorized_lightning_ast_boundary_valid",
                "checkpoint_compatibility_preserved",
                "ready_for_model_consumption_design",
                "feature_semantics_audit_required_before_training",
            ))
            or bundle["repository_cli_selector_forwarding_implemented"] is not False
            or bundle["indicator_consumed_by_model"] is not False
            or bundle["indicator_passed_into_dynamics"] is not False
            or bundle["recommended_next_step"]
            != "design_covapie_target_residue_atom_condition_model_consumption_v1"
        ):
            raise ValueError(_ERROR)
        for record in records:
            _validate_record(record, require_field_order=require_field_order)
        lineage_projection = (
            _current11_runtime_bridge_gate_record_lineage_projection(records)
        )
        flat_start = 0
        for sample_index, record in enumerate(records):
            expected_flat = flat_start + record["expected_local_true_index"]
            if (
                record["expected_flat_true_index"] != expected_flat
                or record["runtime_flat_true_index"] != expected_flat
                or record["runtime_mask_sample_id"] != sample_index
                or record["runtime_local_true_index"]
                != record["expected_local_true_index"]
                or record["runtime_indicator_length"]
                != record["retained_pocket_node_count"]
            ):
                raise ValueError(_ERROR)
            flat_start += record["retained_pocket_node_count"]
        if (
            _sha256(_canonical_json_bytes(lineage_projection))
            != _CURRENT11_LINEAGE_PROJECTION_SHA256
            or flat_start != 2202
            or sum(record["retained_pocket_node_count"] for record in records)
            != bundle["total_runtime_pocket_node_count"]
            or sum(record["runtime_indicator_true_count"] for record in records)
            != bundle["total_runtime_indicator_true_count"]
            or tuple(record["sample"] for record in records) != _EXPECTED_SAMPLES
            or tuple(record["expected_local_true_index"] for record in records) != _EXPECTED_LOCAL
            or tuple(record["expected_flat_true_index"] for record in records) != _EXPECTED_FLAT
            or tuple(record["runtime_mask_sample_id"] for record in records) != tuple(range(11))
            or bundle["runtime_bridge_gate_bundle_sha256"]
            != _digest_record(
                ordered, RUNTIME_BRIDGE_GATE_BUNDLE_FIELDS,
                "runtime_bridge_gate_bundle_sha256",
            )
        ):
            raise ValueError(_ERROR)
        return True
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _walk_values(value: object) -> list[object]:
    if isinstance(value, Mapping):
        return [item for nested in value.values() for item in _walk_values(nested)]
    if isinstance(value, (list, tuple)):
        return [item for nested in value for item in _walk_values(nested)]
    return [value]


def evaluate_covapie_target_residue_atom_condition_runtime_bridge_gate_v1(
    *,
    source_authority_bundle: bytes,
    source_alignment_bundle: bytes,
    source_adapter_bundle: bytes,
    source_adapter_gate_bundle: bytes,
    repo_root: Path,
) -> dict[str, Any]:
    """Evaluate and return deterministic in-memory successor-gate evidence."""

    if (
        type(source_authority_bundle) is not bytes
        or type(source_alignment_bundle) is not bytes
        or type(source_adapter_bundle) is not bytes
        or type(source_adapter_gate_bundle) is not bytes
        or type(repo_root) is not type(Path())
    ):
        raise ValueError(_ERROR)
    snapshots = tuple(
        bytes(value) for value in (
            source_authority_bundle,
            source_alignment_bundle,
            source_adapter_bundle,
            source_adapter_gate_bundle,
        )
    )
    predecessor_snapshot = (
        authority.TARGET_RESIDUE_ATOM_CONDITION_AUTHORITY_BUNDLE_FIELDS,
        alignment.POCKET_ATOM_IDENTITY_ALIGNMENT_BUNDLE_FIELDS,
        adapter.TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_BUNDLE_FIELDS,
        adapter_gate.TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_BUNDLE_FIELDS,
    )
    try:
        root_metadata = repo_root.lstat()
        if stat.S_ISLNK(root_metadata.st_mode) or not stat.S_ISDIR(root_metadata.st_mode):
            raise ValueError(_ERROR)
        supplied_payloads = (
            source_authority_bundle,
            source_alignment_bundle,
            source_adapter_bundle,
            source_adapter_gate_bundle,
        )
        expected_transports = (
            _AUTHORITY_TRANSPORT_SHA256,
            _ALIGNMENT_TRANSPORT_SHA256,
            _ADAPTER_TRANSPORT_SHA256,
            _ADAPTER_GATE_TRANSPORT_SHA256,
        )
        if tuple(_sha256(value) for value in supplied_payloads) != expected_transports:
            raise ValueError(_ERROR)
        authority_bundle = _strict_json(source_authority_bundle)
        alignment_bundle = _strict_json(source_alignment_bundle)
        adapter_bundle = _strict_json(source_adapter_bundle)
        adapter_gate_bundle = _strict_json(source_adapter_gate_bundle)
        authority._validate_bundle(authority_bundle, require_field_order=False)
        alignment._validate_alignment_bundle(alignment_bundle, require_field_order=False)
        adapter._validate_adapter_bundle(adapter_bundle, require_field_order=False)
        adapter_gate._validate_gate_bundle(adapter_gate_bundle, require_field_order=False)
        if (
            adapter_gate_bundle.get("target_residue_atom_condition_adapter_gate_bundle_sha256")
            != _ADAPTER_GATE_INTERNAL_SHA256
        ):
            raise ValueError(_ERROR)

        parents = _git(repo_root, ["show", "-s", "--format=%P", _IMPLEMENTATION_COMMIT]).decode().strip().split()
        subject = _git(repo_root, ["show", "-s", "--format=%s", _IMPLEMENTATION_COMMIT]).decode().rstrip("\n")
        ancestry = subprocess.run(
            ["git", "merge-base", "--is-ancestor", _IMPLEMENTATION_COMMIT, "HEAD"],
            cwd=repo_root, check=False, capture_output=True,
        )
        if (
            parents != [_BASE_COMMIT]
            or subject != _IMPLEMENTATION_SUBJECT
            or ancestry.returncode != 0
            or ancestry.stdout != b""
            or ancestry.stderr != b""
        ):
            raise ValueError(_ERROR)
        runtime_payloads: dict[str, bytes] = {}
        for relative_path, expected_sha256 in _RUNTIME_FILES.items():
            committed = _git_show(repo_root, _IMPLEMENTATION_COMMIT, relative_path)
            current = _read_regular(repo_root / relative_path)
            if committed != current or _sha256(committed) != expected_sha256:
                raise ValueError(_ERROR)
            runtime_payloads[relative_path] = current
        external_relative = (
            "src/covalent_ext/"
            "covapie_external_pocket_runtime_bridge_path_coverage_resolution_v1.py"
        )
        if _sha256(_read_regular(repo_root / external_relative)) != _EXTERNAL_PRODUCTION_SHA256:
            raise ValueError(_ERROR)
        checker_stdout, checker_facts = _run_runtime_checker(repo_root)
        if (
            checker_facts.get("source_external_path_resolution_response_sha256")
            != _EXTERNAL_RESPONSE_SHA256
            or _sha256(checker_stdout) != _RUNTIME_CHECKER_STDOUT_SHA256
        ):
            raise ValueError(_ERROR)

        current_source = runtime_payloads["lightning_modules.py"].decode("utf-8", errors="strict")
        base_payload = _git_show(repo_root, _BASE_COMMIT, "lightning_modules.py")
        base_source = base_payload.decode("utf-8", errors="strict")
        current_tree = ast.parse(current_source)
        base_tree = ast.parse(base_source)
        current_methods = _method_map(current_tree)
        base_methods = _method_map(base_tree)
        changed_methods = {
            name for name in base_methods if current_methods.get(name) != base_methods[name]
        }
        current_functions = {
            node.name for node in current_tree.body if isinstance(node, ast.FunctionDef)
        }
        base_functions = {
            node.name for node in base_tree.body if isinstance(node, ast.FunctionDef)
        }
        current_imports = [
            ast.dump(node, include_attributes=False) for node in current_tree.body
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        base_imports = [
            ast.dump(node, include_attributes=False) for node in base_tree.body
            if isinstance(node, (ast.Import, ast.ImportFrom))
        ]
        authorized_ast = (
            set(current_methods) == set(base_methods)
            and changed_methods == set(_METHODS)
            and current_functions - base_functions == set(_HELPERS)
            and not (base_functions - current_functions)
            and _other_class_map(current_tree) == _other_class_map(base_tree)
            and current_imports == base_imports
            and "sys.path" not in current_source
            and "covalent_ext" not in current_source
            and all(current_methods[name] == base_methods[name] for name in (
                "forward", "training_step", "_shared_eval", "validation_step", "test_step"
            ))
        )
        if not authorized_ast:
            raise ValueError(_ERROR)
        runtime = _load_runtime(current_source, include_bridge=True)
        baseline = _load_runtime(base_source, include_bridge=False)
        if (
            runtime._COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_SPEC_FIELDS
            != ("chain_id", "residue_sequence_number", "residue_insertion_code", "residue_name", "atom_name", "element")
            or runtime._COVAPIE_POCKET_TARGET_RESIDUE_ATOM_CONDITION_INDICATOR_FIELD != _FIELD
            or runtime._COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_RUNTIME_BRIDGE_ERROR != _RUNTIME_ERROR
        ):
            raise ValueError(_ERROR)

        adapter_records = adapter_bundle.get("target_residue_atom_condition_adapter_records")
        alignment_records = alignment_bundle.get("pocket_atom_identity_alignment_records")
        if (
            type(adapter_records) is not list or len(adapter_records) != 11
            or type(alignment_records) is not list or len(alignment_records) != 11
            or tuple(record.get("sample_index_row_id") for record in adapter_records) != _EXPECTED_SAMPLES
            or tuple(record.get("target_retained_model_local_index") for record in adapter_records) != _EXPECTED_LOCAL
        ):
            raise ValueError(_ERROR)
        expected_lineage = (
            _expected_current11_runtime_bridge_gate_record_lineage(adapter_records)
        )
        symbol_to_index = alignment._checkpoint_symbol_to_index()
        if symbol_to_index.get("S") != 3 or set(symbol_to_index.values()) != set(range(10)):
            raise ValueError(_ERROR)
        counts: list[int] = []
        coordinates: list[np.ndarray] = []
        one_hots: list[np.ndarray] = []
        indicators: list[np.ndarray] = []
        for adapter_record, alignment_record in zip(adapter_records, alignment_records):
            count = adapter_record.get("retained_pocket_node_count")
            local = adapter_record.get("target_retained_model_local_index")
            values = adapter_record.get(_FIELD)
            relative_path = alignment_record.get("source_pocket_atom_table_path")
            if (
                type(count) is not int or type(count) is bool or count <= 0
                or type(local) is not int or type(local) is bool
                or type(values) is not list or len(values) != count
                or any(type(value) is not bool for value in values)
                or sum(value is True for value in values) != 1 or values[local] is not True
                or adapter_record.get("source_alignment_record_sha256")
                != alignment_record.get("pocket_atom_identity_alignment_record_sha256")
                or type(relative_path) is not str
            ):
                raise ValueError(_ERROR)
            table_payload = alignment._read_regular(repo_root, relative_path)
            if _sha256(table_payload) != alignment_record.get("source_pocket_atom_table_sha256"):
                raise ValueError(_ERROR)
            _fieldnames, rows = alignment._csv_rows(table_payload)
            retained_indices = alignment_record.get("retained_source_pocket_row_indices")
            if type(retained_indices) is not list or len(retained_indices) != count:
                raise ValueError(_ERROR)
            retained_rows = [rows[index] for index in retained_indices]
            coordinate_bytes = alignment._float32_bytes(retained_rows)
            one_hot_bytes = alignment._one_hot_float32_bytes(retained_rows, symbol_to_index)
            coordinate_array = np.frombuffer(coordinate_bytes, dtype="<f4").reshape(count, 3).copy()
            one_hot_array = np.frombuffer(one_hot_bytes, dtype="<f4").reshape(count, 10).copy()
            if (
                _sha256(coordinate_bytes) != alignment_record.get("retained_pocket_coordinate_float32_bytes_sha256")
                or _sha256(one_hot_bytes) != alignment_record.get("retained_pocket_one_hot_bytes_sha256")
                or retained_rows[local].get("type_symbol") != "S"
                or np.flatnonzero(one_hot_array[local]).tolist() != [3]
                or float(one_hot_array[local].sum()) != 1.0
            ):
                raise ValueError(_ERROR)
            counts.append(count)
            coordinates.append(coordinate_array)
            one_hots.append(one_hot_array)
            indicators.append(np.asarray(values, dtype=np.bool_))
        indicator = torch.from_numpy(np.concatenate(indicators))
        data = _batch(counts, indicator)
        data["pocket_coords"] = torch.from_numpy(np.concatenate(coordinates))
        data["pocket_one_hot"] = torch.from_numpy(np.concatenate(one_hots))
        _ligand, pocket = _model(runtime).get_ligand_and_pocket(data)
        runtime_indicator = pocket[_FIELD]
        flat_indices = tuple(torch.nonzero(runtime_indicator, as_tuple=False).flatten().tolist())
        if (
            sum(counts) != 2202 or len(runtime_indicator) != 2202
            or runtime_indicator.dtype != torch.bool or int(runtime_indicator.sum()) != 11
            or flat_indices != _EXPECTED_FLAT
            or not torch.equal(pocket["mask"][runtime_indicator], torch.arange(11))
        ):
            raise ValueError(_ERROR)

        records: list[dict[str, Any]] = []
        flat_start = 0
        for sample_index, (adapter_record, count, lineage) in enumerate(
            zip(adapter_records, counts, expected_lineage)
        ):
            local = lineage["expected_local_true_index"]
            block = runtime_indicator[flat_start:flat_start + count]
            runtime_local = int(torch.nonzero(block, as_tuple=False).flatten().item())
            runtime_flat = flat_start + runtime_local
            target_row = pocket["one_hot"][runtime_flat]
            feature_indices = torch.nonzero(target_row, as_tuple=False).flatten().tolist()
            record: dict[str, Any] = {
                "runtime_bridge_gate_record_version": _RECORD_VERSION,
                "sample": lineage["sample"],
                "pdb_id": lineage["pdb_id"],
                "source_adapter_record_sha256": lineage["source_adapter_record_sha256"],
                "retained_pocket_node_count": lineage["retained_pocket_node_count"],
                "expected_local_true_index": local,
                "expected_flat_true_index": lineage["expected_flat_true_index"],
                "runtime_indicator_dtype": str(block.dtype),
                "runtime_indicator_length": len(block),
                "runtime_indicator_true_count": int(block.sum()),
                "runtime_local_true_index": runtime_local,
                "runtime_flat_true_index": runtime_flat,
                "runtime_target_s_feature_index": feature_indices[0] if len(feature_indices) == 1 else -1,
                "runtime_pocket_one_hot_width": int(pocket["one_hot"].shape[1]),
                "runtime_mask_sample_id": lineage["runtime_mask_sample_id"],
                "sidecar_field_name": _FIELD,
                "node_order_preserved": bool(torch.equal(pocket["one_hot"], data["pocket_one_hot"])),
                "status": "runtime_bridge_gate_ready_unique",
                "blockers": [],
                "runtime_bridge_gate_record_sha256": "",
            }
            record["runtime_bridge_gate_record_sha256"] = _digest_record(
                record, RUNTIME_BRIDGE_GATE_RECORD_FIELDS,
                "runtime_bridge_gate_record_sha256",
            )
            _validate_record(record, require_field_order=True)
            records.append(record)
            flat_start += count

        legacy_data = _batch((2, 3), None, one_hot_width=7)
        current_legacy = _model(runtime).get_ligand_and_pocket(legacy_data)
        base_legacy = _model(baseline).get_ligand_and_pocket(legacy_data)
        legacy_collated = (
            len(current_legacy) == len(base_legacy) == 2
            and _same_tensor_dict(current_legacy[0], base_legacy[0])
            and _same_tensor_dict(current_legacy[1], base_legacy[1])
            and tuple(current_legacy[1]) == ("x", "one_hot", "size", "mask")
            and _FIELD not in current_legacy[1]
        )
        ca_residues: list[_Residue] = []
        for number, name, coordinate in ((1, "ALA", (0, 0, 0)), (2, "CYS", (1, 2, 3))):
            residue = _Residue(name, number)
            _Atom(residue, "CA", "C", coordinate)
            ca_residues.append(residue)
        current_ca = _model(runtime, "CA").prepare_pocket(ca_residues, 2)
        base_ca = _model(baseline, "CA").prepare_pocket(ca_residues, 2)
        current_full = _model(runtime).prepare_pocket(_full_atom_residues(), 2)
        base_full = _model(baseline).prepare_pocket(_full_atom_residues(), 2)
        legacy_ca = _same_tensor_dict(current_ca, base_ca) and tuple(current_ca) == ("x", "one_hot", "size", "mask")
        legacy_full = _same_tensor_dict(current_full, base_full) and tuple(current_full) == ("x", "one_hot", "size", "mask")

        selector = _spec()
        selector_snapshot = deepcopy(selector)
        validated = runtime._validate_covapie_target_residue_atom_condition_spec_v1(selector)
        invalid_selectors = [
            {**_spec(), "extra": 1},
            {key: value for key, value in _spec().items() if key != "element"},
            _spec(chain_id=""), _spec(chain_id=1),
            _spec(residue_sequence_number=True), _spec(residue_sequence_number="145"),
            _spec(residue_insertion_code=""), _spec(residue_insertion_code="A"),
            _spec(residue_name="SER"), _spec(atom_name="CA"), _spec(element="C"),
        ]
        selector_negatives = all(
            _rejects_runtime(
                lambda candidate=candidate:
                runtime._validate_covapie_target_residue_atom_condition_spec_v1(candidate)
            ) for candidate in invalid_selectors
        )
        target_residue = _Residue()
        target_atom = _Atom(target_residue, "SG", "S", (9, 9, 9))
        wrong_residue = _Residue("CYS", 146)
        wrong_atom = _Atom(wrong_residue, "SG", "S", (9, 9, 9))
        target_order = runtime._locate_covapie_target_residue_atom_in_pocket_atoms_v1(
            [wrong_atom, target_atom], selector, {"S": 2}
        ) == 1
        absent = _rejects_runtime(lambda: runtime._locate_covapie_target_residue_atom_in_pocket_atoms_v1([wrong_atom], selector, {"S": 2}))
        duplicate = _rejects_runtime(lambda: runtime._locate_covapie_target_residue_atom_in_pocket_atoms_v1([target_atom, target_atom], selector, {"S": 2}))
        missing_vocab = _rejects_runtime(lambda: runtime._locate_covapie_target_residue_atom_in_pocket_atoms_v1([target_atom], selector, {"C": 0}))
        disorder_checks = []
        for residue_disordered, atom_disordered, altloc in (
            (True, False, " "), (False, True, " "), (False, False, "A")
        ):
            disordered_residue = _Residue(disordered=residue_disordered)
            disordered_atom = _Atom(
                disordered_residue, "SG", "S", (0, 0, 0),
                disordered=atom_disordered, altloc=altloc,
            )
            disorder_checks.append(_rejects_runtime(
                lambda atom=disordered_atom:
                runtime._locate_covapie_target_residue_atom_in_pocket_atoms_v1([atom], selector, {"S": 2})
            ))
        ca_selector = _rejects_runtime(
            lambda: _model(runtime, "CA").prepare_pocket([], 1, selector)
        )
        repeat_results = []
        for repeats in (1, 3):
            residues = _full_atom_residues()
            legacy = _model(runtime).prepare_pocket(residues, repeats)
            prepared = _model(runtime).prepare_pocket(
                residues, repeats, target_residue_atom_condition_spec=selector
            )
            prepared_indicator = prepared[_FIELD]
            repeat_results.append(
                selector == selector_snapshot
                and prepared_indicator.dtype == torch.bool
                and prepared_indicator.device == prepared["x"].device
                and len(prepared_indicator) == 4 * repeats
                and tuple(torch.nonzero(prepared_indicator).flatten().tolist())
                == tuple(2 + block * 4 for block in range(repeats))
                and torch.equal(prepared["mask"][prepared_indicator], torch.arange(repeats))
                and all(torch.equal(prepared[key], legacy[key]) for key in ("x", "one_hot", "size", "mask"))
            )
        invalid_repeats = all(
            _rejects_runtime(
                lambda repeats=repeats: _model(runtime).prepare_pocket(
                    _full_atom_residues(), repeats,
                    target_residue_atom_condition_spec=selector,
                )
            ) for repeats in (0, -1, True, 1.5)
        )
        invalid_indicators = [
            torch.tensor([0, 1, 1, 0, 0], dtype=torch.int64),
            torch.tensor([False, False, True, False, False]),
            torch.tensor([True, True, True, False, False]),
            torch.tensor([False, True, True, False]),
            torch.tensor([[False], [True], [True], [False], [False]]),
        ]
        collated_negatives = all(
            _rejects_runtime(
                lambda value=value: _model(runtime).get_ligand_and_pocket(_batch((2, 3), value))
            ) for value in invalid_indicators
        )
        conditional_molecules, conditional_pocket, conditional_seen = _exercise_generate(runtime, "conditional", selector)
        inpaint_molecules, inpaint_pocket, inpaint_seen = _exercise_generate(runtime, "inpainting", selector)
        conditional_carried = (
            len(conditional_molecules) == 2
            and conditional_seen.get("prepare", (None, None, None))[1:] == (2, selector)
            and conditional_seen.get("pocket") is conditional_pocket
            and conditional_seen.get("sample_kwargs") == {"timesteps": None}
        )
        inpainting_carried = (
            len(inpaint_molecules) == 2
            and inpaint_seen.get("prepare", (None, None, None))[1:] == (2, selector)
            and inpaint_seen.get("pocket") is inpaint_pocket
            and inpaint_seen.get("inpaint_kwargs") == {"timesteps": None, "probe": "only-inpaint"}
            and "target_residue_atom_condition_spec" not in inpaint_seen.get("inpaint_kwargs", {})
        )
        external_valid = (
            selector == selector_snapshot and validated == selector and validated is not selector
            and tuple(validated) == runtime._COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_SPEC_FIELDS
            and target_order and selector_negatives and absent and duplicate and missing_vocab
            and all(disorder_checks) and ca_selector
        )
        external_repeat = all(repeat_results) and invalid_repeats and collated_negatives

        protected_sources = all(
            _sha256(_read_regular(repo_root / relative)) == expected
            for relative, expected in _PROTECTED_SOURCES.items()
        )
        callers = all(
            _sha256(_read_regular(repo_root / relative)) == expected
            for relative, expected in _CALLER_SHA256S.items()
        )
        checkpoint_path = repo_root / "checkpoints/crossdocked_fullatom_cond.ckpt"
        checkpoint_metadata = checkpoint_path.lstat()
        checkpoint = (
            stat.S_ISREG(checkpoint_metadata.st_mode)
            and not stat.S_ISLNK(checkpoint_metadata.st_mode)
            and checkpoint_metadata.st_size == _CHECKPOINT_SIZE
            and _sha256(_read_regular(checkpoint_path)) == _CHECKPOINT_SHA256
            and protected_sources
            and callers
            and not any(
                isinstance(node, ast.Call)
                and (
                    (isinstance(node.func, ast.Attribute) and node.func.attr in {
                        "register_buffer", "register_parameter", "add_module"
                    })
                    or (isinstance(node.func, ast.Name) and node.func.id == "Parameter")
                )
                for node in ast.walk(current_tree)
                if getattr(node, "lineno", 0) <= 283 or getattr(node, "lineno", 0) >= 473
            )
        )

        readiness_evidence = (
            authorized_ast, checkpoint, legacy_collated, legacy_ca, legacy_full,
            external_valid, external_repeat, conditional_carried, inpainting_carried,
            len(records) == 11, sum(counts) == 2202, int(runtime_indicator.sum()) == 11,
            callers, len(CANONICAL_MASK_SEMANTIC_NAMES) == 5,
            "scaffold_only" in CANONICAL_MASK_SEMANTIC_NAMES,
        )
        ready = all(readiness_evidence)
        if not ready:
            raise ValueError(_ERROR)
        bundle: dict[str, Any] = {
            "runtime_bridge_gate_version": _VERSION,
            "source_authority_bundle_transport_sha256": _AUTHORITY_TRANSPORT_SHA256,
            "source_alignment_bundle_transport_sha256": _ALIGNMENT_TRANSPORT_SHA256,
            "source_adapter_bundle_transport_sha256": _ADAPTER_TRANSPORT_SHA256,
            "source_adapter_gate_bundle_transport_sha256": _ADAPTER_GATE_TRANSPORT_SHA256,
            "source_adapter_gate_bundle_sha256": _ADAPTER_GATE_INTERNAL_SHA256,
            "source_external_path_resolution_production_sha256": _EXTERNAL_PRODUCTION_SHA256,
            "source_external_path_resolution_response_sha256": _EXTERNAL_RESPONSE_SHA256,
            "source_runtime_bridge_commit": _IMPLEMENTATION_COMMIT,
            "source_runtime_bridge_parent_commit": _BASE_COMMIT,
            "source_lightning_module_sha256": _LIGHTNING_SHA256,
            "source_runtime_bridge_test_sha256": _RUNTIME_TEST_SHA256,
            "source_runtime_bridge_checker_sha256": _RUNTIME_CHECKER_SHA256,
            "source_runtime_bridge_guide_sha256": _RUNTIME_GUIDE_SHA256,
            "source_runtime_bridge_checker_stdout_sha256": _RUNTIME_CHECKER_STDOUT_SHA256,
            "sidecar_field_name": _FIELD,
            "current11_record_fields": list(RUNTIME_BRIDGE_GATE_RECORD_FIELDS),
            "current11_records": records,
            "current11_record_count": len(records),
            "runtime_dataset_sample_count": len(records),
            "total_runtime_pocket_node_count": sum(counts),
            "total_runtime_indicator_true_count": int(runtime_indicator.sum()),
            "collated_flat_true_indices": list(flat_indices),
            "legacy_collated_absent_parity": legacy_collated,
            "legacy_prepare_pocket_ca_parity": legacy_ca,
            "legacy_prepare_pocket_full_atom_parity": legacy_full,
            "external_selector_exact6_validated": external_valid,
            "external_prepare_pocket_repeat_validated": external_repeat,
            "conditional_branch_sidecar_carried": conditional_carried,
            "inpainting_branch_sidecar_carried": inpainting_carried,
            "authorized_lightning_ast_boundary_valid": authorized_ast,
            "checkpoint_compatibility_preserved": checkpoint,
            "repository_cli_selector_forwarding_implemented": False,
            "indicator_consumed_by_model": False,
            "indicator_passed_into_dynamics": False,
            "ready_for_model_consumption_design": ready,
            "recommended_next_step": "design_covapie_target_residue_atom_condition_model_consumption_v1",
            "feature_semantics_audit_required_before_training": True,
            "runtime_bridge_gate_bundle_sha256": "",
        }
        bundle["runtime_bridge_gate_bundle_sha256"] = _digest_record(
            bundle, RUNTIME_BRIDGE_GATE_BUNDLE_FIELDS,
            "runtime_bridge_gate_bundle_sha256",
        )
        _validate_bundle(bundle, require_field_order=True)
        if (
            tuple(bytes(value) for value in supplied_payloads) != snapshots
            or predecessor_snapshot != (
                authority.TARGET_RESIDUE_ATOM_CONDITION_AUTHORITY_BUNDLE_FIELDS,
                alignment.POCKET_ATOM_IDENTITY_ALIGNMENT_BUNDLE_FIELDS,
                adapter.TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_BUNDLE_FIELDS,
                adapter_gate.TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_BUNDLE_FIELDS,
            )
            or any(isinstance(value, Path) for value in _walk_values(bundle))
        ):
            raise ValueError(_ERROR)
        return bundle
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _bundle_bytes(bundle: Mapping[str, Any]) -> bytes:
    try:
        _validate_bundle(bundle, require_field_order=True)
        payload = _canonical_json_bytes(bundle)
        decoded = _strict_json(payload)
        _validate_bundle(decoded, require_field_order=False)
        if _canonical_json_bytes(decoded) != payload:
            raise ValueError(_ERROR)
        return payload
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _read_fd_all(file_descriptor: int, expected_size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = expected_size
    while remaining:
        chunk = os.read(file_descriptor, min(remaining, 1024 * 1024))
        if not chunk:
            raise ValueError(_ERROR)
        chunks.append(chunk)
        remaining -= len(chunk)
    if os.read(file_descriptor, 1):
        raise ValueError(_ERROR)
    return b"".join(chunks)


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
        not stat.S_ISLNK(metadata.st_mode) and stat.S_ISREG(metadata.st_mode)
        and metadata.st_dev == device and metadata.st_ino == inode
    ):
        path.unlink()


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _materialize_covapie_current11_target_residue_atom_condition_runtime_bridge_gate_bundle_v1(
    *,
    source_authority_bundle: bytes,
    source_alignment_bundle: bytes,
    source_adapter_bundle: bytes,
    source_adapter_gate_bundle: bytes,
    repo_root: Path,
    output_path: Path,
) -> dict[str, Any]:
    """Publish canonical gate bytes once, without replacement or touching."""

    if type(output_path) is not type(Path()):
        raise ValueError(_ERROR)
    try:
        bundle = evaluate_covapie_target_residue_atom_condition_runtime_bridge_gate_v1(
            source_authority_bundle=source_authority_bundle,
            source_alignment_bundle=source_alignment_bundle,
            source_adapter_bundle=source_adapter_bundle,
            source_adapter_gate_bundle=source_adapter_gate_bundle,
            repo_root=repo_root,
        )
        if bundle["ready_for_model_consumption_design"] is not True:
            raise ValueError(_ERROR)
        payload = _bundle_bytes(bundle)
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
            read_descriptor = os.open(temporary, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            try:
                metadata = os.fstat(read_descriptor)
                reread = _read_fd_all(read_descriptor, metadata.st_size)
            finally:
                os.close(read_descriptor)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or stat.S_IMODE(metadata.st_mode) != 0o644
                or metadata.st_nlink != 1
                or metadata.st_dev != created_device
                or metadata.st_ino != created_inode
                or reread != payload
            ):
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
            temporary_metadata = temporary.lstat()
            if (
                linked.st_dev != temporary_metadata.st_dev
                or linked.st_ino != temporary_metadata.st_ino
                or linked.st_nlink != 2
            ):
                raise ValueError(_ERROR)
            _remove_created_inode(temporary, created_device, created_inode)
            _fsync_directory(parent)
            final = output_path.lstat()
            if (
                final.st_dev != created_device or final.st_ino != created_inode
                or final.st_nlink != 1 or stat.S_IMODE(final.st_mode) != 0o644
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
