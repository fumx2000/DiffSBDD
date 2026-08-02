from __future__ import annotations

import ast
import hashlib
import importlib.util
import inspect
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest
import torch
import torch.nn.functional as F


ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "6f3ba8eb0dcb2982a14f5bdc0c7319b0a4e79250"
FIELD = "pocket_target_residue_atom_condition_indicator"
ERROR = "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_RUNTIME_BRIDGE_INVALID"
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


def _load_checker_module():
    checker_path = (
        ROOT
        / "scripts/check_covapie_target_residue_atom_condition_runtime_bridge_v1.py"
    )
    specification = importlib.util.spec_from_file_location(
        "covapie_runtime_bridge_checker", checker_path
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _source_at_base() -> str:
    return subprocess.run(
        ["git", "show", f"{BASE_COMMIT}:lightning_modules.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _load_runtime(source: str, include_helpers: bool):
    tree = ast.parse(source)
    class_node = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "LigandPocketDDPM"
    )
    methods = [
        deepcopy(node)
        for node in class_node.body
        if isinstance(node, ast.FunctionDef) and node.name in METHODS
    ]
    body = []
    if include_helpers:
        body.extend(
            deepcopy(node)
            for node in tree.body
            if (
                isinstance(node, (ast.Assign, ast.AnnAssign))
                and any(
                    isinstance(target, ast.Name)
                    and target.id.startswith("_COVAPIE_")
                    for target in (
                        node.targets if isinstance(node, ast.Assign)
                        else [node.target]
                    )
                )
            )
        )
        body.extend(
            deepcopy(node)
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name in HELPERS
        )
    body.append(
        ast.ClassDef(
            name="LigandPocketDDPM",
            bases=[],
            keywords=[],
            body=methods,
            decorator_list=[],
        )
    )
    isolated = ast.fix_missing_locations(ast.Module(body=body, type_ignores=[]))

    class ConditionalDDPM:
        pass

    class EnVariationalDiffusion:
        pass

    module = ModuleType("isolated_lightning_modules")
    namespace = module.__dict__
    namespace.update({
        "np": np,
        "torch": torch,
        "F": F,
        "FLOAT_TYPE": torch.float32,
        "INT_TYPE": torch.int64,
        "three_to_one": lambda name: {"CYS": "C", "ALA": "A"}[name],
        "ConditionalDDPM": ConditionalDDPM,
        "EnVariationalDiffusion": EnVariationalDiffusion,
    })
    exec(compile(isolated, "<isolated-lightning-modules>", "exec"), namespace)
    return module


@pytest.fixture(scope="session")
def runtime():
    return _load_runtime((ROOT / "lightning_modules.py").read_text(), True)


@pytest.fixture(scope="session")
def baseline_runtime():
    return _load_runtime(_source_at_base(), False)


def _spec(**updates):
    value = {
        "chain_id": "A",
        "residue_sequence_number": 145,
        "residue_insertion_code": " ",
        "residue_name": "CYS",
        "atom_name": "SG",
        "element": "S",
    }
    value.update(updates)
    return value


def _error(action):
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        action()


class _Chain:
    def __init__(self, chain_id="A"):
        self.id = chain_id


class _Residue:
    def __init__(self, name="CYS", number=145, chain="A", disordered=False):
        self.id = (" ", number, " ")
        self._name = name
        self._parent = _Chain(chain)
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
    def __init__(
        self,
        residue,
        name,
        element,
        coord,
        *,
        disordered=False,
        altloc=" ",
    ):
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


def _full_atom_residues():
    ala = _Residue("ALA", 10, "A")
    _Atom(ala, "CA", "C", [0.0, 0.0, 0.0])
    cys = _Residue("CYS", 145, "A")
    _Atom(cys, "CA", "C", [1.0, 0.0, 0.0])
    _Atom(cys, "SG", "S", [2.0, 0.0, 0.0])
    _Atom(cys, "N", "N", [3.0, 0.0, 0.0])
    return [ala, cys]


def _model(runtime, representation="full-atom"):
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


def _batch(counts=(2, 3), indicator=None):
    total = sum(counts)
    data = {
        "lig_coords": torch.zeros(len(counts), 3),
        "lig_one_hot": torch.zeros(len(counts), 4),
        "num_lig_atoms": torch.ones(len(counts), dtype=torch.int64),
        "lig_mask": torch.arange(len(counts), dtype=torch.int64),
        "pocket_coords": torch.arange(total * 3, dtype=torch.float32).view(total, 3),
        "pocket_one_hot": torch.zeros(total, 7),
        "num_pocket_nodes": torch.tensor(counts, dtype=torch.int64),
        "pocket_mask": torch.repeat_interleave(
            torch.arange(len(counts), dtype=torch.int64),
            torch.tensor(counts, dtype=torch.int64),
        ),
    }
    if indicator is not None:
        data[FIELD] = indicator
    return data


def _assert_tensor_dict_equal(left, right):
    assert tuple(left) == tuple(right)
    for key in left:
        assert torch.equal(left[key], right[key])


def test_exact6_selector_returns_ordered_copy_without_mutation(runtime):
    selector = _spec()
    snapshot = deepcopy(selector)
    validated = runtime._validate_covapie_target_residue_atom_condition_spec_v1(
        selector
    )
    assert selector == snapshot
    assert validated == selector
    assert validated is not selector
    assert tuple(validated) == (
        "chain_id",
        "residue_sequence_number",
        "residue_insertion_code",
        "residue_name",
        "atom_name",
        "element",
    )


@pytest.mark.parametrize(
    "selector",
    [
        None,
        [],
        {**_spec(), "extra": 1},
        {key: value for key, value in _spec().items() if key != "element"},
        _spec(chain_id=""),
        _spec(chain_id=1),
        _spec(residue_sequence_number=True),
        _spec(residue_sequence_number="145"),
        _spec(residue_insertion_code=""),
        _spec(residue_insertion_code="A"),
        _spec(residue_name="SER"),
        _spec(atom_name="CA"),
        _spec(element="C"),
    ],
)
def test_invalid_selectors_fail_closed(runtime, selector):
    _error(
        lambda: runtime._validate_covapie_target_residue_atom_condition_spec_v1(
            selector
        )
    )


def test_locator_binds_identity_not_coordinate(runtime):
    wrong = _Residue("CYS", 146, "A")
    wrong_atom = _Atom(wrong, "SG", "S", [9.0, 9.0, 9.0])
    target = _Residue("CYS", 145, "A")
    target_atom = _Atom(target, "SG", "S", [9.0, 9.0, 9.0])
    assert runtime._locate_covapie_target_residue_atom_in_pocket_atoms_v1(
        [wrong_atom, target_atom], _spec(), {"S": 2}
    ) == 1


def test_locator_rejects_absent_duplicate_and_missing_s_vocab(runtime):
    target = _Residue()
    atom = _Atom(target, "SG", "S", [0, 0, 0])
    _error(
        lambda: runtime._locate_covapie_target_residue_atom_in_pocket_atoms_v1(
            [atom], _spec(residue_sequence_number=999), {"S": 2}
        )
    )
    _error(
        lambda: runtime._locate_covapie_target_residue_atom_in_pocket_atoms_v1(
            [atom, atom], _spec(), {"S": 2}
        )
    )
    _error(
        lambda: runtime._locate_covapie_target_residue_atom_in_pocket_atoms_v1(
            [atom], _spec(), {"C": 0}
        )
    )


@pytest.mark.parametrize(
    "residue_disordered,atom_disordered,altloc",
    [(True, False, " "), (False, True, " "), (False, False, "A")],
)
def test_locator_rejects_disorder_and_implicit_altloc(
    runtime, residue_disordered, atom_disordered, altloc
):
    residue = _Residue(disordered=residue_disordered)
    atom = _Atom(
        residue,
        "SG",
        "S",
        [0, 0, 0],
        disordered=atom_disordered,
        altloc=altloc,
    )
    _error(
        lambda: runtime._locate_covapie_target_residue_atom_in_pocket_atoms_v1(
            [atom], _spec(), {"S": 2}
        )
    )


def test_get_ligand_and_pocket_legacy_parity_and_arity(runtime, baseline_runtime):
    data = _batch()
    current = _model(runtime)
    baseline = _model(baseline_runtime)
    current_result = current.get_ligand_and_pocket(data)
    baseline_result = baseline.get_ligand_and_pocket(data)
    assert len(current_result) == len(baseline_result) == 2
    _assert_tensor_dict_equal(current_result[0], baseline_result[0])
    _assert_tensor_dict_equal(current_result[1], baseline_result[1])
    assert tuple(current_result[1]) == ("x", "one_hot", "size", "mask")


def test_get_ligand_and_pocket_preserves_bool_sidecar(runtime):
    indicator = torch.tensor([False, True, True, False, False])
    model = _model(runtime)
    _ligand, pocket = model.get_ligand_and_pocket(_batch(indicator=indicator))
    assert tuple(pocket) == ("x", "one_hot", "size", "mask", FIELD)
    assert torch.equal(pocket[FIELD], indicator)
    assert pocket[FIELD].dtype == torch.bool
    assert pocket[FIELD].device == pocket["x"].device
    assert pocket["one_hot"].shape[1] == 7
    assert torch.equal(pocket["mask"][pocket[FIELD]], torch.tensor([0, 1]))


@pytest.mark.parametrize(
    "indicator",
    [
        torch.tensor([0, 1, 1, 0, 0], dtype=torch.int64),
        torch.tensor([False, False, True, False, False]),
        torch.tensor([True, True, True, False, False]),
        torch.tensor([False, True, True, False]),
        torch.tensor([[False], [True], [True], [False], [False]]),
    ],
)
def test_get_ligand_and_pocket_rejects_invalid_indicators(runtime, indicator):
    _error(
        lambda: _model(runtime).get_ligand_and_pocket(
            _batch(indicator=indicator)
        )
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("num_pocket_nodes", torch.tensor([2, 2])),
        ("pocket_mask", torch.tensor([0, 0, 0, 1, 1])),
    ],
)
def test_get_ligand_and_pocket_rejects_mask_size_mismatch(runtime, field, value):
    data = _batch(indicator=torch.tensor([False, True, True, False, False]))
    data[field] = value
    _error(lambda: _model(runtime).get_ligand_and_pocket(data))


def test_get_ligand_and_pocket_rejects_empty_collated_pocket(runtime):
    _error(
        lambda: _model(runtime).get_ligand_and_pocket(
            _batch((), indicator=torch.zeros(0, dtype=torch.bool))
        )
    )


def test_current11_formal_collated_bridge(runtime):
    bundle = json.loads(ADAPTER_BUNDLE.read_text())
    records = bundle["target_residue_atom_condition_adapter_records"]
    counts = [record["retained_pocket_node_count"] for record in records]
    indicator = torch.tensor(
        [
            selected
            for record in records
            for selected in record[FIELD]
        ],
        dtype=torch.bool,
    )
    data = _batch(tuple(counts), indicator)
    _ligand, pocket = _model(runtime).get_ligand_and_pocket(data)
    assert len(indicator) == len(pocket[FIELD]) == 2202
    assert indicator.dtype == pocket[FIELD].dtype == torch.bool
    assert int(pocket[FIELD].sum()) == 11
    assert tuple(torch.nonzero(pocket[FIELD]).flatten().tolist()) == EXPECTED_FLAT
    assert torch.equal(pocket[FIELD], indicator)
    assert torch.equal(pocket["mask"][pocket[FIELD]], torch.arange(11))


def test_prepare_pocket_legacy_ca_parity(runtime, baseline_runtime):
    residues = []
    for number, name, coord in ((1, "ALA", [0, 0, 0]), (2, "CYS", [1, 2, 3])):
        residue = _Residue(name, number)
        _Atom(residue, "CA", "C", coord)
        residues.append(residue)
    current = _model(runtime, "CA").prepare_pocket(residues, repeats=2)
    baseline = _model(baseline_runtime, "CA").prepare_pocket(residues, repeats=2)
    _assert_tensor_dict_equal(current, baseline)
    assert tuple(current) == ("x", "one_hot", "size", "mask")


def test_prepare_pocket_legacy_full_atom_parity(runtime, baseline_runtime):
    residues = _full_atom_residues()
    current = _model(runtime).prepare_pocket(residues, repeats=2)
    baseline = _model(baseline_runtime).prepare_pocket(residues, repeats=2)
    _assert_tensor_dict_equal(current, baseline)
    assert tuple(current) == ("x", "one_hot", "size", "mask")


def test_prepare_pocket_selector_requires_full_atom(runtime):
    _error(lambda: _model(runtime, "CA").prepare_pocket([], 1, _spec()))


def test_prepare_pocket_rejects_checkpoint_vocab_without_s(runtime):
    model = _model(runtime)
    model.pocket_type_encoder = {"C": 0, "N": 1}
    _error(
        lambda: model.prepare_pocket(
            _full_atom_residues(), 1,
            target_residue_atom_condition_spec=_spec(),
        )
    )


@pytest.mark.parametrize("repeats", [1, 3])
def test_prepare_pocket_sidecar_order_repeat_and_mask_alignment(runtime, repeats):
    residues = _full_atom_residues()
    legacy = _model(runtime).prepare_pocket(residues, repeats=repeats)
    selector = _spec()
    snapshot = deepcopy(selector)
    pocket = _model(runtime).prepare_pocket(
        residues,
        repeats=repeats,
        target_residue_atom_condition_spec=selector,
    )
    assert selector == snapshot
    assert pocket[FIELD].dtype == torch.bool
    assert pocket[FIELD].device == pocket["x"].device
    assert len(pocket[FIELD]) == repeats * 4
    assert tuple(torch.nonzero(pocket[FIELD]).flatten().tolist()) == tuple(
        2 + sample * 4 for sample in range(repeats)
    )
    assert torch.equal(pocket["mask"][pocket[FIELD]], torch.arange(repeats))
    for key in ("x", "one_hot", "size", "mask"):
        assert torch.equal(pocket[key], legacy[key])


@pytest.mark.parametrize("repeats", [0, -1, True, 1.5])
def test_prepare_pocket_selector_rejects_invalid_repeats(runtime, repeats):
    _error(
        lambda: _model(runtime).prepare_pocket(
            _full_atom_residues(), repeats=repeats,
            target_residue_atom_condition_spec=_spec()
        )
    )


def _scatter_mean(values, mask, dim=0):
    assert dim == 0
    return torch.stack([values[mask == sample].mean(0) for sample in range(int(mask.max()) + 1)])


def _exercise_generate(runtime, branch, selector):
    model = _model(runtime)
    model.x_dims = 3
    model.atom_nf = 2
    model.dataset_info = {}
    prepared = {
        "x": torch.tensor([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]).repeat(2, 1),
        "one_hot": torch.zeros(4, 3),
        "size": torch.tensor([2, 2]),
        "mask": torch.tensor([0, 0, 1, 1]),
        FIELD: torch.tensor([False, True, False, True]),
    }
    seen = {}

    def prepare(residues, repeats, target_residue_atom_condition_spec):
        seen["prepare"] = (residues, repeats, target_residue_atom_condition_spec)
        return prepared

    model.prepare_pocket = prepare
    ddpm_class = (
        runtime.ConditionalDDPM
        if branch == "conditional"
        else runtime.EnVariationalDiffusion
    )
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
    result = model.generate_ligands(
        "unused.pdb",
        2,
        ref_ligand="unused.sdf",
        num_nodes_lig=torch.ones(2, dtype=torch.int64),
        target_residue_atom_condition_spec=selector,
        probe="only-inpaint",
    )
    return result, prepared, seen


def test_generate_ligands_signature_is_explicit(runtime):
    signature = inspect.signature(runtime.LigandPocketDDPM.generate_ligands)
    assert signature.parameters["target_residue_atom_condition_spec"].default is None
    assert list(signature.parameters)[-2:] == [
        "target_residue_atom_condition_spec",
        "kwargs",
    ]


@pytest.mark.parametrize("branch", ["conditional", "inpainting"])
def test_generate_ligands_forwards_selector_and_same_pocket(runtime, branch):
    selector = _spec()
    molecules, prepared, seen = _exercise_generate(runtime, branch, selector)
    assert len(molecules) == 2
    assert seen["prepare"][1:] == (2, selector)
    assert seen["pocket"] is prepared
    assert torch.equal(seen["pocket"][FIELD], prepared[FIELD])
    if branch == "conditional":
        assert seen["sample_kwargs"] == {"timesteps": None}
    else:
        assert seen["inpaint_kwargs"] == {
            "timesteps": None,
            "probe": "only-inpaint",
        }
        assert "target_residue_atom_condition_spec" not in seen["inpaint_kwargs"]


def test_generate_ligands_legacy_selector_absent(runtime):
    _molecules, _prepared, seen = _exercise_generate(runtime, "conditional", None)
    assert seen["prepare"][2] is None


def _definitions(tree, kind):
    return {
        node.name: ast.dump(node, include_attributes=False)
        for node in tree.body
        if isinstance(node, kind)
    }


def test_authorized_ast_change_boundary_is_exact():
    base = ast.parse(_source_at_base())
    current = ast.parse((ROOT / "lightning_modules.py").read_text())
    base_class = next(node for node in base.body if isinstance(node, ast.ClassDef) and node.name == "LigandPocketDDPM")
    current_class = next(node for node in current.body if isinstance(node, ast.ClassDef) and node.name == "LigandPocketDDPM")
    base_methods = _definitions(SimpleNamespace(body=base_class.body), ast.FunctionDef)
    current_methods = _definitions(SimpleNamespace(body=current_class.body), ast.FunctionDef)
    changed = {name for name in base_methods if base_methods[name] != current_methods[name]}
    assert changed == set(METHODS)
    assert set(current_methods) == set(base_methods)
    for name in ("forward", "training_step", "_shared_eval", "validation_step", "test_step"):
        assert current_methods[name] == base_methods[name]


def test_only_private_task_helpers_were_added():
    base = ast.parse(_source_at_base())
    current = ast.parse((ROOT / "lightning_modules.py").read_text())
    base_functions = _definitions(base, ast.FunctionDef)
    current_functions = _definitions(current, ast.FunctionDef)
    assert set(current_functions) - set(base_functions) == set(HELPERS)


def test_no_runtime_import_path_dependency_or_one_hot_append():
    current = ast.parse((ROOT / "lightning_modules.py").read_text())
    imports = [node for node in current.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    assert all(
        not (
            isinstance(node, ast.ImportFrom)
            and node.module in {"covalent_ext", "src.covalent_ext"}
        )
        for node in imports
    )
    source = (ROOT / "lightning_modules.py").read_text()
    assert "sys.path" not in source
    get_method = next(
        node
        for node in ast.walk(current)
        if isinstance(node, ast.FunctionDef) and node.name == "get_ligand_and_pocket"
    )
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"cat", "concat", "concatenate"}
        for node in ast.walk(get_method)
    )


def test_model_sources_and_checkpoint_unchanged():
    expected = {
        "equivariant_diffusion/conditional_model.py": "260bb941e05a3beaa0f1aef7aebba86aa2474d5f5db75637ec1498e3ad0e47b4",
        "equivariant_diffusion/en_diffusion.py": "841f95e8d47fd1bc27f50b76f605bf6d0369308c68c7a65b199e51b00b30d8ef",
        "equivariant_diffusion/dynamics.py": "16b008598de7c61c0b5575e3af02f9b1a9e6697559864df1591314e4b4ec6b9f",
        "checkpoints/crossdocked_fullatom_cond.ckpt": "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c",
    }
    for relative, digest in expected.items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest
    assert (ROOT / "checkpoints/crossdocked_fullatom_cond.ckpt").stat().st_size == 17861341


def test_checkpoint_state_contract_has_no_module_parameter_or_buffer_change():
    tree = ast.parse((ROOT / "lightning_modules.py").read_text())
    added_helpers = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in HELPERS
    ]
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"Parameter", "register_buffer", "add_module"}
        for helper in added_helpers
        for node in ast.walk(helper)
    )


def test_canonical_five_mask_contract_and_no_training_execution():
    canonical = (
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    )
    design_source = (
        ROOT
        / "src/covalent_ext/"
        "covapie_target_residue_atom_condition_runtime_bridge_design_v1.py"
    ).read_text()
    design_tree = ast.parse(design_source)
    assignment = next(
        node for node in design_tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "CANONICAL_MASK_SEMANTIC_NAMES" for target in node.targets)
    )
    assert ast.literal_eval(assignment.value) == canonical
    assert "optimizer.step" not in (ROOT / "lightning_modules.py").read_text()


def test_checker_is_deterministic_and_reports_required_contract():
    command = [
        sys.executable,
        "scripts/check_covapie_target_residue_atom_condition_runtime_bridge_v1.py",
    ]
    first = subprocess.run(
        command, cwd=ROOT, check=True, capture_output=True, text=True
    )
    second = subprocess.run(
        command, cwd=ROOT, check=True, capture_output=True, text=True
    )
    assert first.stdout == second.stdout
    assert first.stderr == second.stderr == ""
    required = {
        "authorized_lightning_method_changes_exact=true",
        "authorized_lightning_base_commit_is_ancestor=true",
        "source_external_path_resolution_response_sha256=8406e5baef6e67fca331d54963f56e6ac9137c5f1afa3a963e7010c491afa9dc",
        "collated_current11_indicator_length=2202",
        "collated_current11_indicator_true_count=11",
        "collated_current11_flat_true_indices_valid=true",
        "prepare_pocket_legacy_ca_parity=true",
        "prepare_pocket_legacy_full_atom_parity=true",
        "generate_ligands_selector_forwarded_exact=true",
        "conditional_branch_sidecar_carried=true",
        "inpainting_branch_sidecar_carried=true",
        "append_to_pocket_one_hot=false",
        "indicator_consumed_by_model=false",
        "indicator_passed_into_dynamics=false",
        "runtime_bridge_implemented=true",
        "ready_for_runtime_bridge_gate=true",
        "recommended_next_step=implement_covapie_target_residue_atom_condition_runtime_bridge_gate_v1",
    }
    assert required <= set(first.stdout.splitlines())


def test_checker_git_ancestor_contract_supports_post_commit_head(tmp_path):
    checker = _load_checker_module()

    def git(*arguments):
        return subprocess.run(
            ["git", *arguments],
            cwd=tmp_path,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    git("init")
    git("config", "user.name", "CovaPIE Test")
    git("config", "user.email", "covapie-test@example.invalid")
    tracked = tmp_path / "tracked.txt"
    tracked.write_text("base\n", encoding="utf-8")
    git("add", "tracked.txt")
    git("commit", "-m", "base")
    base_commit = git("rev-parse", "HEAD")
    tracked.write_text("successor\n", encoding="utf-8")
    git("commit", "-am", "successor")
    successor_commit = git("rev-parse", "HEAD")

    assert checker._git_commit_is_ancestor(
        repo_root=tmp_path, base_commit=base_commit
    ) is True
    assert checker._git_commit_is_ancestor(
        repo_root=tmp_path,
        base_commit=successor_commit,
        head_ref=base_commit,
    ) is False
    assert checker._git_commit_is_ancestor(
        repo_root=tmp_path,
        base_commit=base_commit,
        head_ref=base_commit,
    ) is True

    checker_source = Path(checker.__file__).read_text(encoding="utf-8")
    assert "head == BASE_COMMIT" not in checker_source
    assert '["git", "rev-parse", "HEAD"]' not in checker_source


def test_checker_legacy_caller_compatibility_is_hash_derived(tmp_path):
    checker = _load_checker_module()
    caller_root = tmp_path / "callers"
    nested = caller_root / "scripts"
    nested.mkdir(parents=True)
    first = caller_root / "entry.py"
    second = nested / "demo.py"
    first.write_bytes(b"entry-v1\n")
    second.write_bytes(b"demo-v1\n")
    expected = {
        "entry.py": hashlib.sha256(first.read_bytes()).hexdigest(),
        "scripts/demo.py": hashlib.sha256(second.read_bytes()).hexdigest(),
    }

    assert checker._protected_repository_callers_unchanged(
        repo_root=caller_root, expected_sha256s=expected
    ) is True
    second.write_bytes(b"demo-drift\n")
    assert checker._protected_repository_callers_unchanged(
        repo_root=caller_root, expected_sha256s=expected
    ) is False

    second.write_bytes(b"demo-v1\n")
    link_target = nested / "link-target.py"
    link_target.write_bytes(b"demo-v1\n")
    second.unlink()
    second.symlink_to(link_target.name)
    assert checker._protected_repository_callers_unchanged(
        repo_root=caller_root, expected_sha256s=expected
    ) is False
    assert checker._protected_repository_callers_unchanged(
        repo_root=caller_root,
        expected_sha256s={str(first.resolve()): expected["entry.py"]},
    ) is False
    assert checker._protected_repository_callers_unchanged(
        repo_root=caller_root,
        expected_sha256s={"../entry.py": expected["entry.py"]},
    ) is False


def test_checker_import_is_silent_and_side_effect_free():
    checker = ROOT / "scripts/check_covapie_target_residue_atom_condition_runtime_bridge_v1.py"
    code = (
        "import importlib.util;"
        f"s=importlib.util.spec_from_file_location('bridge_check',{str(checker)!r});"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m)"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert completed.stdout == completed.stderr == ""
