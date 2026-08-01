"""Resolve the external-PDB runtime-bridge path coverage contract (design only).

This module binds the four formal Current11 bundles, rebuilds the predecessor
runtime-bridge design, and audits every repository runtime caller of
``generate_ligands`` and ``prepare_pocket``.  It does not modify runtime code,
construct tensors, call a model, or write files.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import stat
import warnings
from pathlib import Path
from typing import Any, Mapping, Sequence

from covalent_ext import covapie_target_residue_atom_condition_runtime_bridge_design_v1 as predecessor


__all__ = (
    "resolve_covapie_external_pocket_runtime_bridge_path_coverage_v1",
)


_ERROR = "COVAPIE_EXTERNAL_POCKET_RUNTIME_BRIDGE_PATH_COVERAGE_INVALID"
_VERSION = "covapie_external_pocket_runtime_bridge_path_coverage_resolution_v1"
_SELECTOR_ARGUMENT = "target_residue_atom_condition_spec"
_SIDECAR = "pocket_target_residue_atom_condition_indicator"
_BLOCKER = "generate_ligands->prepare_pocket->ConditionalDDPM.sample_given_pocket_or_inpaint"
_PREDECESSOR_RECOMMENDED_NEXT_STEP = "resolve_covapie_external_pocket_runtime_bridge_path_coverage_v1"
_MAX_BYTES = 32 * 1024 * 1024

_AUTHORITY_TRANSPORT_SHA256 = "a95ae52e091a7117b241269eebd891f3ee97e3ae4a6b4e14fa441ab6a1ed2096"
_ALIGNMENT_TRANSPORT_SHA256 = "7f80a810ff35c4ea5d61262021379767a4d15202badd8ec6a6b846405147d842"
_ADAPTER_TRANSPORT_SHA256 = "983c25ea8c52ca54f0c0292990a625e9a9cf0d2370cb517d66a84801d957b65a"
_ADAPTER_GATE_TRANSPORT_SHA256 = "c7e2c9eec92d560fc55206399d9b27df511733821ce3233c3546da38d9992a9d"
_ADAPTER_GATE_INTERNAL_SHA256 = "97821184d8c76618bb549dd708132bd9579687c6f3a0ba8007d0bbc80d7d6602"
_PREDECESSOR_PRODUCTION_SHA256 = "045aeaa16d91dfe10d1cdec9cfa789e637b5eba41a0d0a45313d20617e72bf67"
_PREDECESSOR_RESPONSE_SHA256 = "1c90069e6d64916504f6a6e1e0d852e95351dc261e36ea3eab3d0ef4880ec6f2"
_AUDITED_RUNTIME_SOURCE_RECORDS_SHA256 = "d07edeba245422b9285c0d504d077ae1fc84ec3c2e94e0d4d90a0f1cb081cab8"
_GENERATE_LIGANDS_CURRENT_INTERFACE_SHA256 = "f65222156dc83df49be7e5048d84da1201eda9418ac310994a4a8ca1c3d1897f"
_PREPARE_POCKET_CURRENT_INTERFACE_SHA256 = "2a1271615b2e5ef838662344df158b9d9cc5a32f9ea0ae2377680a4cb3989b57"
_GENERATE_LIGANDS_CALL_SITE_RECORDS_SHA256 = "a96eda3a62f1faf7bb0d4adad3fe296003569b194ebca1fa6f62d22113be6196"
_CLI_OR_PUBLIC_CALLER_FORWARDING_CONTRACT_SHA256 = "46d8b4b96c4f2df12a3a5de38a8b6f190c1f1ee3dcf41e9b5aa4e832877abf9d"

_RUNTIME_SOURCE_SHA256S = (
    ("lightning_modules.py", "2b771068eda19b6f783e12ff483a02ab6ef8264108f3af5e486d3381fb1e7fb6"),
    ("dataset.py", "d1c548185521692ca14be062e34d5bea617f8d3c89a22eaef4ddb13a52907c99"),
    ("equivariant_diffusion/conditional_model.py", "260bb941e05a3beaa0f1aef7aebba86aa2474d5f5db75637ec1498e3ad0e47b4"),
    ("equivariant_diffusion/en_diffusion.py", "841f95e8d47fd1bc27f50b76f605bf6d0369308c68c7a65b199e51b00b30d8ef"),
)

_CALLER_SOURCE_SHA256S = (
    ("generate_ligands.py", "8884e63ddb7f0fa84bd89bfd956fbefa10db687fa0cfc3380b85d06837be4474"),
    ("test.py", "954e63ade5e8b8f811897e40b22d81308451054753327cd9de2942c658dfd7bf"),
    ("optimize.py", "d51c32b3902accf24698f2b3abdfdf0e1a5d3150b90515a1b8d1b13d3e7d229b"),
    ("inpaint.py", "2d6cf0542c4b82e25eed19165d6f90d004ae4ced1db426962e47fb6086e085d9"),
    ("scripts/covalent_inpaint_demo.py", "1866dde2a7909fb431617dfa9f7de5a297b895de7930313655685823944f72a9"),
    ("colab/DiffSBDD.ipynb", "0d7fdc6a8377aa41e8d2104c39b2120964eee7f02b21c2bb56ca415dc889a123"),
)

TARGET_RESIDUE_ATOM_CONDITION_SPEC_FIELDS = (
    "chain_id",
    "residue_sequence_number",
    "residue_insertion_code",
    "residue_name",
    "atom_name",
    "element",
)

CANONICAL_MASK_SEMANTIC_NAMES = (
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
)

EXTERNAL_PATH_COVERAGE_RESOLUTION_FIELDS = (
    "external_path_coverage_resolution_version",
    "source_authority_bundle_transport_sha256",
    "source_alignment_bundle_transport_sha256",
    "source_adapter_bundle_transport_sha256",
    "source_adapter_gate_bundle_transport_sha256",
    "source_runtime_bridge_design_production_sha256",
    "source_runtime_bridge_design_response_sha256",
    "source_runtime_bridge_blocker",
    "audited_runtime_source_records",
    "generate_ligands_current_interface",
    "prepare_pocket_current_interface",
    "generate_ligands_call_site_records",
    "selected_external_selector_argument_name",
    "selected_prepare_pocket_argument_name",
    "target_selector_fields",
    "target_selector_fixed_v1_semantics",
    "target_selector_validation_contract",
    "pocket_representation_policy",
    "target_membership_policy",
    "target_atom_order_binding_policy",
    "repeated_indicator_policy",
    "prepared_pocket_sidecar_contract",
    "legacy_external_path_policy",
    "covalent_external_path_policy",
    "conditional_generation_path_contract",
    "inpainting_path_contract",
    "cli_or_public_caller_forwarding_contract",
    "current11_collated_path_contract_unchanged",
    "checkpoint_compatibility_decision",
    "candidate_decisions",
    "canonical_mask_semantic_names",
    "unresolved_path_blockers",
    "ready_for_runtime_bridge_implementation",
    "recommended_next_step",
    "feature_semantics_audit_required_before_training",
    "external_path_coverage_resolution_sha256",
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
            or len(payload) >= _MAX_BYTES
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
        if type(value) is not dict:
            raise ValueError(_ERROR)
        return value
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _read_regular(repo_root: Path, relative_path: str) -> bytes:
    try:
        relative = Path(relative_path)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(_ERROR)
        path = repo_root / relative
        metadata = path.lstat()
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_size <= 0
            or metadata.st_size >= _MAX_BYTES
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


def _parse_source(payload: bytes) -> ast.Module:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            return ast.parse(payload.decode("utf-8", errors="strict"))
    except Exception as error:
        raise ValueError(_ERROR) from error


def _class(tree: ast.Module, name: str) -> ast.ClassDef:
    matches = [node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == name]
    if len(matches) != 1:
        raise ValueError(_ERROR)
    return matches[0]


def _method(class_node: ast.ClassDef, name: str) -> ast.FunctionDef:
    matches = [
        node for node in class_node.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    if len(matches) != 1:
        raise ValueError(_ERROR)
    return matches[0]


def _signature_record(node: ast.FunctionDef) -> dict[str, Any]:
    positional = [argument.arg for argument in (*node.args.posonlyargs, *node.args.args)]
    defaults: dict[str, str] = {}
    if node.args.defaults:
        for name, value in zip(positional[-len(node.args.defaults):], node.args.defaults):
            defaults[name] = ast.unparse(value)
    return {
        "positional_parameters": positional,
        "defaults": defaults,
        "var_keyword": None if node.args.kwarg is None else node.args.kwarg.arg,
    }


def _dict_assignment_keys(node: ast.FunctionDef, target_name: str) -> tuple[str, ...]:
    matches: list[tuple[str, ...]] = []
    for child in node.body:
        if (
            isinstance(child, ast.Assign)
            and len(child.targets) == 1
            and isinstance(child.targets[0], ast.Name)
            and child.targets[0].id == target_name
            and isinstance(child.value, ast.Dict)
        ):
            matches.append(tuple(
                key.value for key in child.value.keys
                if isinstance(key, ast.Constant) and type(key.value) is str
            ))
    if len(matches) != 1:
        raise ValueError(_ERROR)
    return matches[0]


def _attribute_calls(tree: ast.AST, attribute: str) -> list[ast.Call]:
    return [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == attribute
    ]


def _attribute_reference_count(tree: ast.AST, attribute: str) -> int:
    return sum(
        isinstance(node, ast.Attribute) and node.attr == attribute
        for node in ast.walk(tree)
    )


def _discover_repository_attribute_references(repo_root: Path) -> dict[str, dict[str, int]]:
    """Discover runtime references repository-wide while excluding tests/artifacts."""

    try:
        discovered: dict[str, dict[str, int]] = {}
        excluded_top_level = {".git", ".pytest_cache", "checkpoints", "tests"}
        for current, directory_names, file_names in os.walk(repo_root, followlinks=False):
            current_path = Path(current)
            relative_directory = current_path.relative_to(repo_root)
            if relative_directory == Path("data"):
                directory_names[:] = [name for name in directory_names if name != "raw"]
            directory_names[:] = sorted(
                name for name in directory_names
                if name not in excluded_top_level and name != "__pycache__"
            )
            for file_name in sorted(file_names):
                path = current_path / file_name
                relative_path = path.relative_to(repo_root).as_posix()
                if path.suffix not in {".py", ".ipynb"}:
                    continue
                metadata = path.lstat()
                if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
                    raise ValueError(_ERROR)
                payload = path.read_bytes()
                if not payload or len(payload) != metadata.st_size or len(payload) >= _MAX_BYTES:
                    raise ValueError(_ERROR)
                counts = {"generate_ligands": 0, "prepare_pocket": 0}
                if path.suffix == ".py":
                    tree = _parse_source(payload)
                    for attribute in counts:
                        counts[attribute] = _attribute_reference_count(tree, attribute)
                else:
                    notebook = json.loads(payload.decode("utf-8", errors="strict"))
                    for cell in notebook.get("cells", []):
                        if cell.get("cell_type") != "code":
                            continue
                        source = "".join(cell.get("source", []))
                        if not any(f".{attribute}" in source for attribute in counts):
                            continue
                        parseable = "\n".join(
                            line for line in source.splitlines()
                            if not line.lstrip().startswith(("%", "!"))
                        )
                        tree = ast.parse(parseable)
                        for attribute in counts:
                            counts[attribute] += _attribute_reference_count(tree, attribute)
                if any(counts.values()):
                    discovered[relative_path] = counts
        return discovered
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _call_arguments(node: ast.Call) -> dict[str, Any]:
    return {
        "positional": [ast.unparse(value) for value in node.args],
        "keyword": [
            {"name": keyword.arg, "value": ast.unparse(keyword.value)}
            for keyword in node.keywords
        ],
    }


def _walk_values(value: object) -> list[object]:
    if isinstance(value, Mapping):
        return [item for nested in value.values() for item in _walk_values(nested)]
    if isinstance(value, (list, tuple)):
        return [item for nested in value for item in _walk_values(nested)]
    return [value]


def _is_disordered(entity: object) -> bool:
    method = getattr(entity, "is_disordered", None)
    if method is None or not callable(method):
        return False
    return bool(method())


def _validate_target_residue_atom_condition_spec(spec: object) -> dict[str, Any]:
    """Validate and copy the frozen Exact6 Cys-SG selector (design oracle)."""

    try:
        if (
            type(spec) is not dict
            or len(spec) != len(TARGET_RESIDUE_ATOM_CONDITION_SPEC_FIELDS)
            or set(spec) != set(TARGET_RESIDUE_ATOM_CONDITION_SPEC_FIELDS)
        ):
            raise ValueError(_ERROR)
        chain_id = spec["chain_id"]
        residue_number = spec["residue_sequence_number"]
        insertion_code = spec["residue_insertion_code"]
        if (
            type(chain_id) is not str
            or chain_id == ""
            or type(residue_number) is not int
            or type(residue_number) is bool
            or type(insertion_code) is not str
            or len(insertion_code) != 1
            or insertion_code != " "
            or spec["residue_name"] != "CYS"
            or spec["atom_name"] != "SG"
            or spec["element"] != "S"
            or any(type(spec[field]) is not str for field in TARGET_RESIDUE_ATOM_CONDITION_SPEC_FIELDS if field != "residue_sequence_number")
        ):
            raise ValueError(_ERROR)
        return {field: spec[field] for field in TARGET_RESIDUE_ATOM_CONDITION_SPEC_FIELDS}
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _locate_target_atom_in_pocket_atoms(
    pocket_atoms: object,
    target_residue_atom_condition_spec: object,
    pocket_type_encoder: object,
) -> int:
    """Locate one target in the actual base pocket atom order (design oracle)."""

    try:
        spec = _validate_target_residue_atom_condition_spec(target_residue_atom_condition_spec)
        if type(pocket_atoms) is not list or not pocket_atoms or not isinstance(pocket_type_encoder, Mapping):
            raise ValueError(_ERROR)
        if "S" not in pocket_type_encoder:
            raise ValueError(_ERROR)
        matches: list[int] = []
        for index, atom in enumerate(pocket_atoms):
            residue = atom.get_parent()
            chain = residue.get_parent()
            residue_id = residue.id
            if type(residue_id) is not tuple or len(residue_id) != 3:
                raise ValueError(_ERROR)
            identity_matches = (
                chain.id == spec["chain_id"]
                and residue_id[0] == " "
                and residue_id[1] == spec["residue_sequence_number"]
                and residue_id[2] == spec["residue_insertion_code"]
                and residue.get_resname() == spec["residue_name"]
                and atom.get_name() == spec["atom_name"]
                and atom.element == spec["element"]
            )
            if identity_matches:
                if _is_disordered(residue) or _is_disordered(atom):
                    raise ValueError(_ERROR)
                matches.append(index)
        if len(matches) != 1:
            raise ValueError(_ERROR)
        return matches[0]
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _build_repeated_indicator_design_oracle(
    *,
    pocket_atom_count: object,
    target_local_index: object,
    repeats: object,
) -> dict[str, Any]:
    """Return bool-list and mask evidence for the frozen sample-block repeat."""

    try:
        if (
            type(pocket_atom_count) is not int
            or type(pocket_atom_count) is bool
            or pocket_atom_count <= 0
            or type(target_local_index) is not int
            or type(target_local_index) is bool
            or not 0 <= target_local_index < pocket_atom_count
            or type(repeats) is not int
            or type(repeats) is bool
            or repeats <= 0
        ):
            raise ValueError(_ERROR)
        base = [False] * pocket_atom_count
        base[target_local_index] = True
        repeated = base * repeats
        pocket_mask = [sample for sample in range(repeats) for _ in range(pocket_atom_count)]
        true_sample_ids = [pocket_mask[index] for index, selected in enumerate(repeated) if selected]
        if (
            sum(base) != 1
            or len(repeated) != repeats * pocket_atom_count
            or true_sample_ids != list(range(repeats))
        ):
            raise ValueError(_ERROR)
        return {
            "base_indicator": base,
            "repeated_indicator": repeated,
            "pocket_mask": pocket_mask,
            "true_sample_ids": true_sample_ids,
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _future_caller_record(
    *,
    caller_path: str,
    callable_name: str,
    current_arguments: dict[str, Any],
    forwarding_surface: str,
    covalent_behavior: str,
) -> dict[str, Any]:
    return {
        "caller_path": caller_path,
        "callable_or_function": callable_name,
        "current_arguments": current_arguments,
        "future_selector_forwarding_surface": forwarding_surface,
        "legacy_absent_behavior": "omit_selector_and_preserve_current_behavior_exactly",
        "covalent_selector_present_behavior": covalent_behavior,
        "covered": True,
        "blocking_reason": None,
    }


def _audit_sources(payloads: Mapping[str, bytes]) -> tuple[
    list[dict[str, Any]], dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]
]:
    lightning_tree = _parse_source(payloads["lightning_modules.py"])
    lightning_class = _class(lightning_tree, "LigandPocketDDPM")
    prepare = _method(lightning_class, "prepare_pocket")
    generate = _method(lightning_class, "generate_ligands")
    get_ligand_and_pocket = _method(lightning_class, "get_ligand_and_pocket")
    conditional = _method(_class(_parse_source(payloads["equivariant_diffusion/conditional_model.py"]), "ConditionalDDPM"), "sample_given_pocket")
    inpaint = _method(_class(_parse_source(payloads["equivariant_diffusion/en_diffusion.py"]), "EnVariationalDiffusion"), "inpaint")

    generate_signature = _signature_record(generate)
    prepare_signature = _signature_record(prepare)
    expected_generate = {
        "positional_parameters": [
            "self", "pdb_file", "n_samples", "pocket_ids", "ref_ligand",
            "num_nodes_lig", "sanitize", "largest_frag", "relax_iter",
            "timesteps", "n_nodes_bias", "n_nodes_min",
        ],
        "defaults": {
            "pocket_ids": "None", "ref_ligand": "None", "num_nodes_lig": "None",
            "sanitize": "False", "largest_frag": "False", "relax_iter": "0",
            "timesteps": "None", "n_nodes_bias": "0", "n_nodes_min": "0",
        },
        "var_keyword": "kwargs",
    }
    expected_prepare = {
        "positional_parameters": ["self", "biopython_residues", "repeats"],
        "defaults": {"repeats": "1"},
        "var_keyword": None,
    }
    if generate_signature != expected_generate or prepare_signature != expected_prepare:
        raise ValueError(_ERROR)
    if _SELECTOR_ARGUMENT in ast.dump(generate) or _SELECTOR_ARGUMENT in ast.dump(prepare):
        raise ValueError(_ERROR)
    prepare_calls_in_generate = _attribute_calls(generate, "prepare_pocket")
    if len(prepare_calls_in_generate) != 1 or _call_arguments(prepare_calls_in_generate[0]) != {
        "positional": ["residues"], "keyword": [{"name": "repeats", "value": "n_samples"}]
    }:
        raise ValueError(_ERROR)
    generate_dump = ast.dump(generate, include_attributes=False)
    prepare_dump = ast.dump(prepare, include_attributes=False)
    if (
        "sample_given_pocket" not in generate_dump
        or "inpaint" not in generate_dump
        or "Constant(value=0)" not in generate_dump
        or _dict_assignment_keys(prepare, "pocket") != ("x", "one_hot", "size", "mask")
        or "pocket_atoms" not in prepare_dump
        or "repeat" not in prepare_dump
        or _SIDECAR in prepare_dump
        or _dict_assignment_keys(get_ligand_and_pocket, "pocket") != ("x", "one_hot", "size", "mask")
    ):
        raise ValueError(_ERROR)

    conditional_dump = ast.dump(conditional, include_attributes=False)
    inpaint_dump = ast.dump(inpaint, include_attributes=False)
    for required in ("Constant(value='x')", "Constant(value='one_hot')", "Constant(value='size')", "Constant(value='mask')"):
        if required not in conditional_dump or required not in inpaint_dump:
            raise ValueError(_ERROR)
    if _SIDECAR in conditional_dump or _SIDECAR in inpaint_dump:
        raise ValueError(_ERROR)

    python_call_expectations = {
        ("generate_ligands.py", "generate_ligands"): [{
            "positional": ["args.pdbfile", "args.batch_size", "args.resi_list", "args.ref_ligand", "num_nodes_lig", "args.sanitize"],
            "keyword": [
                {"name": "largest_frag", "value": "not args.all_frags"},
                {"name": "relax_iter", "value": "200 if args.relax else 0"},
                {"name": "resamplings", "value": "args.resamplings"},
                {"name": "jump_length", "value": "args.jump_length"},
                {"name": "timesteps", "value": "args.timesteps"},
            ],
        }],
        ("test.py", "generate_ligands"): [{
            "positional": ["pdb_file", "args.batch_size", "resi_list"],
            "keyword": [
                {"name": "num_nodes_lig", "value": "num_nodes_lig_inflated"},
                {"name": "timesteps", "value": "args.timesteps"},
                {"name": "sanitize", "value": "False"},
                {"name": "largest_frag", "value": "False"},
                {"name": "relax_iter", "value": "0"},
                {"name": "n_nodes_bias", "value": "args.n_nodes_bias"},
                {"name": "n_nodes_min", "value": "args.n_nodes_min"},
                {"name": "resamplings", "value": "args.resamplings"},
                {"name": "jump_length", "value": "args.jump_length"},
            ],
        }],
        ("lightning_modules.py", "prepare_pocket"): [{
            "positional": ["residues"], "keyword": [{"name": "repeats", "value": "n_samples"}]
        }],
        ("optimize.py", "prepare_pocket"): [{
            "positional": ["residues"], "keyword": [{"name": "repeats", "value": "population_size"}]
        }],
        ("inpaint.py", "prepare_pocket"): [{
            "positional": ["residues"], "keyword": [{"name": "repeats", "value": "n_samples"}]
        }],
        ("scripts/covalent_inpaint_demo.py", "prepare_pocket"): [{
            "positional": ["residues"], "keyword": [{"name": "repeats", "value": "1"}]
        }],
    }
    discovered: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for path in sorted(payloads):
        if not path.endswith(".py"):
            continue
        tree = _parse_source(payloads[path])
        for attribute in ("generate_ligands", "prepare_pocket"):
            calls = _attribute_calls(tree, attribute)
            if calls:
                discovered[(path, attribute)] = [_call_arguments(call) for call in sorted(calls, key=lambda value: value.lineno)]
    if discovered != python_call_expectations:
        raise ValueError(_ERROR)

    try:
        notebook = json.loads(payloads["colab/DiffSBDD.ipynb"].decode("utf-8"))
        matching_cells = [
            "".join(cell.get("source", []))
            for cell in notebook.get("cells", [])
            if cell.get("cell_type") == "code"
            and ".generate_ligands(" in "".join(cell.get("source", []))
        ]
        if len(matching_cells) != 1:
            raise ValueError(_ERROR)
        parseable_cell = "\n".join(
            line for line in matching_cells[0].splitlines()
            if not line.lstrip().startswith(("%", "!"))
        )
        notebook_calls = _attribute_calls(ast.parse(parseable_cell), "generate_ligands")
    except Exception as error:
        raise ValueError(_ERROR) from error
    if len(notebook_calls) != 1:
        raise ValueError(_ERROR)
    notebook_arguments = _call_arguments(notebook_calls[0])
    if notebook_arguments != {
        "positional": ["pdbfile", "n_samples", "resi_list", "ref_ligand", "num_nodes_lig", "sanitize == '--sanitize'"],
        "keyword": [
            {"name": "largest_frag", "value": "not keep_all_fragments == '--all_frags'"},
            {"name": "relax_iter", "value": "200 if relax == '--relax' else 0"},
            {"name": "resamplings", "value": "resamplings"},
            {"name": "jump_length", "value": "jump_length"},
            {"name": "timesteps", "value": "timesteps"},
        ],
    }:
        raise ValueError(_ERROR)

    generate_records = [
        _future_caller_record(
            caller_path="generate_ligands.py",
            callable_name="module __main__ CLI",
            current_arguments=python_call_expectations[("generate_ligands.py", "generate_ligands")][0],
            forwarding_surface="add_explicit_Exact6_CYS_SG_CLI_fields_build_spec_and_forward_named_argument",
            covalent_behavior="forward_validated_named_spec_to_model.generate_ligands",
        ),
        _future_caller_record(
            caller_path="test.py",
            callable_name="module __main__ batch CLI",
            current_arguments=python_call_expectations[("test.py", "generate_ligands")][0],
            forwarding_surface="optional_per_complex_Exact6_selector_manifest_keyed_by_ligand_name",
            covalent_behavior="resolve_one_explicit_spec_for_each_complex_and_forward_named_argument",
        ),
        _future_caller_record(
            caller_path="colab/DiffSBDD.ipynb",
            callable_name="interactive generation code cell",
            current_arguments=notebook_arguments,
            forwarding_surface="add_six_explicit_widget_values_build_Exact6_spec_and_forward_named_argument",
            covalent_behavior="forward_validated_named_spec_to_model.generate_ligands",
        ),
    ]
    prepare_records = [
        _future_caller_record(
            caller_path="lightning_modules.py",
            callable_name="LigandPocketDDPM.generate_ligands",
            current_arguments=python_call_expectations[("lightning_modules.py", "prepare_pocket")][0],
            forwarding_surface="explicit_generate_ligands_parameter_forwarded_as_explicit_prepare_pocket_parameter",
            covalent_behavior="forward_same_spec_without_kwargs_or_ddpm_forwarding",
        ),
        _future_caller_record(
            caller_path="optimize.py",
            callable_name="module __main__ evolutionary optimization",
            current_arguments=python_call_expectations[("optimize.py", "prepare_pocket")][0],
            forwarding_surface="add_optional_Exact6_CLI_selector_and_forward_named_prepare_pocket_argument",
            covalent_behavior="validate_and_forward_named_spec_to_prepare_pocket",
        ),
        _future_caller_record(
            caller_path="inpaint.py",
            callable_name="inpaint_ligand",
            current_arguments=python_call_expectations[("inpaint.py", "prepare_pocket")][0],
            forwarding_surface="add_explicit_optional_function_parameter_plus_Exact6_CLI_source",
            covalent_behavior="forward_named_spec_to_prepare_pocket_and_preserve_sidecar_into_inpaint",
        ),
        _future_caller_record(
            caller_path="scripts/covalent_inpaint_demo.py",
            callable_name="prepare_single_pocket",
            current_arguments=python_call_expectations[("scripts/covalent_inpaint_demo.py", "prepare_pocket")][0],
            forwarding_surface="add_explicit_required_covalent_demo_Exact6_selector_parameter",
            covalent_behavior="forward_named_spec_to_prepare_pocket_and_preserve_sidecar_to_sampling_or_inpaint",
        ),
    ]

    audited_records = [
        {
            "source_path": path,
            "source_sha256": _sha256(payloads[path]),
            "interface": interface,
            "audited": True,
        }
        for path, interface in (
            ("lightning_modules.py", "LigandPocketDDPM.prepare_pocket+generate_ligands+get_ligand_and_pocket"),
            ("dataset.py", "external_path_bypasses_dataset_and_get_ligand_and_pocket"),
            ("equivariant_diffusion/conditional_model.py", "ConditionalDDPM.sample_given_pocket"),
            ("equivariant_diffusion/en_diffusion.py", "EnVariationalDiffusion.inpaint"),
            ("generate_ligands.py", "public CLI generate_ligands caller"),
            ("test.py", "batch CLI generate_ligands caller"),
            ("optimize.py", "direct prepare_pocket caller"),
            ("inpaint.py", "direct prepare_pocket caller"),
            ("scripts/covalent_inpaint_demo.py", "direct prepare_pocket caller"),
            ("colab/DiffSBDD.ipynb", "interactive generate_ligands caller"),
        )
    ]
    generate_interface = {
        **generate_signature,
        "selector_argument_currently_explicit": False,
        "selector_must_not_enter_kwargs": True,
        "pocket_selection_routes": ["pocket_ids", "ref_ligand"],
        "pdb_model_index": 0,
        "calls_prepare_pocket": True,
        "bypasses_get_ligand_and_pocket": True,
        "conditional_branch": "ConditionalDDPM.sample_given_pocket",
        "inpainting_branch": "EnVariationalDiffusion.inpaint",
    }
    prepare_interface = {
        **prepare_signature,
        "selector_argument_currently_explicit": False,
        "full_atom_base_sequence": "pocket_atoms",
        "current_return_keys": ["x", "one_hot", "size", "mask"],
        "current_repeat_order": "sample_blocks_via_tensor.repeat",
        "sidecar_currently_returned": False,
    }
    return audited_records, generate_interface, prepare_interface, generate_records, prepare_records


def _expected_semantic_contracts(external_coverage_resolved: bool) -> dict[str, Any]:
    """Return the complete frozen nested semantics shared by builder/validator."""

    if type(external_coverage_resolved) is not bool:
        raise ValueError(_ERROR)
    return {
        "target_selector_fixed_v1_semantics": {
            "model_index": 0,
            "standard_protein_residue_hetflag": " ",
            "chain_id": "nonempty_string_exact_match",
            "residue_sequence_number": "int_non_bool_exact_match",
            "residue_insertion_code": "exactly_one_character_and_V1_value_blank",
            "residue_name": "CYS",
            "atom_name": "SG",
            "element": "S",
            "checkpoint_vocabulary_key": "S",
        },
        "target_selector_validation_contract": {
            "schema_exact6": True,
            "canonical_ValueError_only": True,
            "match_count_required": 1,
            "coordinate_identity_matching_allowed": False,
            "pdb_atom_serial_primary_identity_allowed": False,
            "user_local_index_allowed": False,
            "automatic_unique_CYS_or_SG_inference_allowed": False,
            "disordered_target_atom_allowed": False,
            "implicit_altloc_selection_allowed": False,
            "external_target_altloc_semantics_deferred": True,
            "target_element_must_be_in_checkpoint_10D_vocab": True,
        },
        "pocket_representation_policy": {
            "full_atom_required_when_selector_present": True,
            "CA_selector_present_rejected": True,
            "reason": "CA_representation_has_no_Cys_SG_atom_node",
            "legacy_CA_selector_absent_unchanged": True,
            "fabricate_SG_indicator_for_CA": False,
        },
        "target_membership_policy": {
            "target_must_already_be_in_selected_pocket": True,
            "applies_to_routes": ["pocket_ids", "ref_ligand"],
            "target_required_in_biopython_residues_and_final_pocket_atoms": True,
            "target_absent_rejected": True,
            "target_duplicate_rejected": True,
            "auto_append_target_residue": False,
            "change_pocket_radius": False,
            "change_pocket_ids_semantics": False,
            "change_ref_ligand_selection": False,
            "reorder_residues_or_atoms": False,
        },
        "target_atom_order_binding_policy": {
            "binding_sequence": "actual_prepare_pocket_full_atom_pocket_atoms",
            "same_order_as": ["pocket_coord", "pocket_one_hot"],
            "identity_fields": [
                "atom_parent_residue_parent_chain_id", "residue_id_hetflag",
                "residue_id_resseq", "residue_id_insertion_code",
                "residue_get_resname", "atom_get_name_or_id", "atom_element",
            ],
            "match_count_required": 1,
            "coordinates_used_for_identity": False,
        },
        "repeated_indicator_policy": {
            "base_dtype": "torch.bool",
            "base_length": "len(pocket_atoms)",
            "base_true_count": 1,
            "base_true_index": "target_local_index",
            "repeat_count": "n_samples",
            "repeat_order": "same_sample_block_order_as_pocket_coord.repeat_and_pocket_one_hot.repeat",
            "repeated_length": "n_samples*len(pocket_atoms)",
            "per_sample_true_count": 1,
            "total_true_count": "n_samples",
            "device": "same_as_pocket_x",
            "mask_alignment_assertion": "pocket_mask[indicator]==arange(n_samples)",
        },
        "prepared_pocket_sidecar_contract": {
            "field_name": _SIDECAR,
            "same_name": True,
            "torch_dtype": "torch.bool",
            "domain": "per_pocket_node",
            "same_length_as": ["x", "one_hot", "mask"],
            "selector_present_creates_key": True,
            "selector_absent_key_absent": True,
            "selector_absent_all_false_tensor": False,
        },
        "legacy_external_path_policy": {
            "selector_absent_preserves_behavior_exactly": True,
            "CA_path_unchanged": True,
            "destination_key_absent": True,
        },
        "covalent_external_path_policy": {
            "generate_ligands_explicitly_accepts_selector": True,
            "explicitly_forwards_selector_to_prepare_pocket": True,
            "selector_enters_kwargs": False,
            "selector_forwarded_to_DDPM_or_inpaint_kwargs": False,
            "same_prepared_pocket_object_used_by_branch": True,
            "external_path_coverage_designed": external_coverage_resolved,
            "runtime_bridge_implemented": False,
        },
        "conditional_generation_path_contract": {
            "path": "generate_ligands->prepare_pocket->ConditionalDDPM.sample_given_pocket",
            "same_prepared_pocket_sidecar_carried": True,
            "indicator_consumed_by_model": False,
            "indicator_passed_into_dynamics": False,
            "covered": external_coverage_resolved,
        },
        "inpainting_path_contract": {
            "path": "generate_ligands->prepare_pocket->EnVariationalDiffusion.inpaint",
            "same_prepared_pocket_sidecar_carried": True,
            "indicator_consumed_by_model": False,
            "indicator_passed_into_dynamics": False,
            "covered": external_coverage_resolved,
        },
    }


def _candidate_decisions() -> list[dict[str, Any]]:
    return [
        {"candidate": "explicit_structured_selector_forwarded_generate_ligands_to_prepare_pocket", "decision": "accepted"},
        {"candidate": "exact_identity_match_in_actual_pocket_atoms_order", "decision": "accepted"},
        {"candidate": "same_name_bool_sidecar_repeated_by_sample_block", "decision": "accepted"},
        {"candidate": "infer_unique_cys_or_sg", "decision": "rejected"},
        {"candidate": "nearest_coordinate_or_nearest_ref_ligand_selection", "decision": "rejected"},
        {"candidate": "auto_append_target_residue_to_pocket", "decision": "rejected"},
        {"candidate": "user_supplied_local_node_index", "decision": "rejected"},
        {"candidate": "user_supplied_pdb_atom_serial_as_primary_identity", "decision": "rejected"},
        {"candidate": "all_false_placeholder", "decision": "rejected"},
        {"candidate": "append_indicator_to_pocket_one_hot", "decision": "rejected"},
        {"candidate": "global_mutable_target_state", "decision": "rejected"},
        {"candidate": "disordered_altloc_target_semantics", "decision": "deferred"},
        {"candidate": "nonblank_insertion_code_pocket_ids_extension", "decision": "deferred"},
        {"candidate": "DDPM_or_EGNN_model_consumption", "decision": "deferred"},
        {"candidate": "mixed_noncovalent_zero_target_semantics", "decision": "deferred"},
    ]


def _checkpoint_decision() -> dict[str, Any]:
    return {
        "append_to_pocket_one_hot": False,
        "change_atom_nf": False,
        "change_residue_nf": False,
        "change_joint_nf": False,
        "modify_dataset": False,
        "modify_collate": False,
        "modify_ConditionalDDPM": False,
        "modify_EGNNDynamics": False,
        "new_base_model_parameter": False,
        "base_state_dict_key_change": False,
        "base_checkpoint_tensor_shape_change": False,
        "future_minimal_tracked_runtime_boundary": [
            "lightning_modules.py:LigandPocketDDPM.get_ligand_and_pocket",
            "lightning_modules.py:LigandPocketDDPM.prepare_pocket",
            "lightning_modules.py:LigandPocketDDPM.generate_ligands",
        ],
    }


def _validate_response(response: Mapping[str, Any]) -> bool:
    try:
        ordered = {field: response[field] for field in EXTERNAL_PATH_COVERAGE_RESOLUTION_FIELDS}
        expected_semantics = _expected_semantic_contracts(True)
        lineage_valid = (
            response["source_authority_bundle_transport_sha256"] == _AUTHORITY_TRANSPORT_SHA256
            and response["source_alignment_bundle_transport_sha256"] == _ALIGNMENT_TRANSPORT_SHA256
            and response["source_adapter_bundle_transport_sha256"] == _ADAPTER_TRANSPORT_SHA256
            and response["source_adapter_gate_bundle_transport_sha256"] == _ADAPTER_GATE_TRANSPORT_SHA256
            and response["source_runtime_bridge_design_production_sha256"] == _PREDECESSOR_PRODUCTION_SHA256
            and response["source_runtime_bridge_design_response_sha256"] == _PREDECESSOR_RESPONSE_SHA256
            and response["source_runtime_bridge_blocker"] == _BLOCKER
        )
        semantic_contracts_valid = all(
            response[field] == expected
            for field, expected in expected_semantics.items()
        )
        runtime_audit_valid = (
            _sha256(_canonical_json_bytes(response["audited_runtime_source_records"]))
            == _AUDITED_RUNTIME_SOURCE_RECORDS_SHA256
        )
        current_interfaces_valid = (
            _sha256(_canonical_json_bytes(response["generate_ligands_current_interface"]))
            == _GENERATE_LIGANDS_CURRENT_INTERFACE_SHA256
            and _sha256(_canonical_json_bytes(response["prepare_pocket_current_interface"]))
            == _PREPARE_POCKET_CURRENT_INTERFACE_SHA256
        )
        caller_contracts_valid = (
            _sha256(_canonical_json_bytes(response["generate_ligands_call_site_records"]))
            == _GENERATE_LIGANDS_CALL_SITE_RECORDS_SHA256
            and _sha256(_canonical_json_bytes(response["cli_or_public_caller_forwarding_contract"]))
            == _CLI_OR_PUBLIC_CALLER_FORWARDING_CONTRACT_SHA256
        )
        checkpoint_valid = response["checkpoint_compatibility_decision"] == _checkpoint_decision()
        candidates_valid = response["candidate_decisions"] == _candidate_decisions()
        masks_valid = response["canonical_mask_semantic_names"] == list(CANONICAL_MASK_SEMANTIC_NAMES)
        selector_surface_valid = (
            response["selected_external_selector_argument_name"] == _SELECTOR_ARGUMENT
            and response["selected_prepare_pocket_argument_name"] == _SELECTOR_ARGUMENT
            and response["target_selector_fields"] == list(TARGET_RESIDUE_ATOM_CONDITION_SPEC_FIELDS)
        )
        complete_contract_valid = (
            lineage_valid
            and semantic_contracts_valid
            and runtime_audit_valid
            and current_interfaces_valid
            and caller_contracts_valid
            and checkpoint_valid
            and candidates_valid
            and masks_valid
            and selector_surface_valid
            and response["current11_collated_path_contract_unchanged"] is True
            and response["unresolved_path_blockers"] == []
            and response["feature_semantics_audit_required_before_training"] is True
        )
        derived_ready = complete_contract_valid
        if (
            type(response) is not dict
            or len(response) != 36
            or tuple(response) != EXTERNAL_PATH_COVERAGE_RESOLUTION_FIELDS
            or set(response) != set(EXTERNAL_PATH_COVERAGE_RESOLUTION_FIELDS)
            or response["external_path_coverage_resolution_version"] != _VERSION
            or not complete_contract_valid
            or response["ready_for_runtime_bridge_implementation"] is not derived_ready
            or response["recommended_next_step"] != "implement_covapie_target_residue_atom_condition_runtime_bridge_v1"
            or response["external_path_coverage_resolution_sha256"]
            != _digest_record(ordered, EXTERNAL_PATH_COVERAGE_RESOLUTION_FIELDS, "external_path_coverage_resolution_sha256")
            or any(isinstance(value, Path) for value in _walk_values(response))
        ):
            raise ValueError(_ERROR)
        return True
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def resolve_covapie_external_pocket_runtime_bridge_path_coverage_v1(
    *,
    source_authority_bundle: bytes,
    source_alignment_bundle: bytes,
    source_adapter_bundle: bytes,
    source_adapter_gate_bundle: bytes,
    repo_root: Path,
) -> dict[str, Any]:
    """Return the deterministic Exact36 external-path coverage resolution."""

    if (
        type(source_authority_bundle) is not bytes
        or type(source_alignment_bundle) is not bytes
        or type(source_adapter_bundle) is not bytes
        or type(source_adapter_gate_bundle) is not bytes
        or type(repo_root) is not type(Path())
    ):
        raise ValueError(_ERROR)
    supplied = (
        source_authority_bundle,
        source_alignment_bundle,
        source_adapter_bundle,
        source_adapter_gate_bundle,
    )
    snapshots = tuple(bytes(payload) for payload in supplied)
    predecessor_constants = (
        predecessor.CANONICAL_MASK_SEMANTIC_NAMES,
        predecessor.RUNTIME_BRIDGE_DESIGN_RESPONSE_FIELDS,
    )
    try:
        metadata = repo_root.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise ValueError(_ERROR)
        if tuple(_sha256(payload) for payload in supplied) != (
            _AUTHORITY_TRANSPORT_SHA256,
            _ALIGNMENT_TRANSPORT_SHA256,
            _ADAPTER_TRANSPORT_SHA256,
            _ADAPTER_GATE_TRANSPORT_SHA256,
        ):
            raise ValueError(_ERROR)
        supplied_gate = _strict_json(source_adapter_gate_bundle)
        if (
            supplied_gate.get("target_residue_atom_condition_adapter_gate_bundle_sha256") != _ADAPTER_GATE_INTERNAL_SHA256
            or supplied_gate.get("ready_for_runtime_bridge_design") is not True
            or predecessor.adapter_gate._canonical_json_bytes(supplied_gate) != source_adapter_gate_bundle
        ):
            raise ValueError(_ERROR)

        predecessor_production = _read_regular(
            repo_root,
            "src/covalent_ext/covapie_target_residue_atom_condition_runtime_bridge_design_v1.py",
        )
        if _sha256(predecessor_production) != _PREDECESSOR_PRODUCTION_SHA256:
            raise ValueError(_ERROR)
        predecessor_response = predecessor.design_covapie_target_residue_atom_condition_runtime_bridge_v1(
            source_authority_bundle=source_authority_bundle,
            source_alignment_bundle=source_alignment_bundle,
            source_adapter_bundle=source_adapter_bundle,
            source_adapter_gate_bundle=source_adapter_gate_bundle,
            repo_root=repo_root,
        )
        bypasses = predecessor_response["conditional_sampling_path_coverage"]["bypassing_paths"]
        if (
            predecessor_response["runtime_bridge_design_response_sha256"] != _PREDECESSOR_RESPONSE_SHA256
            or predecessor_response["ready_for_runtime_bridge_implementation"] is not False
            or bypasses != [_BLOCKER]
            or predecessor_response["recommended_next_step"] != _PREDECESSOR_RECOMMENDED_NEXT_STEP
        ):
            raise ValueError(_ERROR)

        payloads: dict[str, bytes] = {}
        for path, expected_sha256 in (*_RUNTIME_SOURCE_SHA256S, *_CALLER_SOURCE_SHA256S):
            payload = _read_regular(repo_root, path)
            if _sha256(payload) != expected_sha256:
                raise ValueError(_ERROR)
            payloads[path] = payload
        repository_references = _discover_repository_attribute_references(repo_root)
        if repository_references != {
            "colab/DiffSBDD.ipynb": {"generate_ligands": 1, "prepare_pocket": 0},
            "generate_ligands.py": {"generate_ligands": 1, "prepare_pocket": 0},
            "inpaint.py": {"generate_ligands": 0, "prepare_pocket": 1},
            "lightning_modules.py": {"generate_ligands": 0, "prepare_pocket": 1},
            "optimize.py": {"generate_ligands": 0, "prepare_pocket": 1},
            "scripts/covalent_inpaint_demo.py": {"generate_ligands": 0, "prepare_pocket": 1},
            "test.py": {"generate_ligands": 1, "prepare_pocket": 0},
        }:
            raise ValueError(_ERROR)
        audited, generate_interface, prepare_interface, generate_callers, prepare_callers = _audit_sources(payloads)

        unresolved = [
            f"{record['caller_path']}:{record['blocking_reason']}"
            for record in (*generate_callers, *prepare_callers)
            if record["covered"] is not True or record["blocking_reason"] is not None
        ]
        external_coverage_resolved = not unresolved
        semantic_contracts = _expected_semantic_contracts(external_coverage_resolved)
        response: dict[str, Any] = {
            "external_path_coverage_resolution_version": _VERSION,
            "source_authority_bundle_transport_sha256": _AUTHORITY_TRANSPORT_SHA256,
            "source_alignment_bundle_transport_sha256": _ALIGNMENT_TRANSPORT_SHA256,
            "source_adapter_bundle_transport_sha256": _ADAPTER_TRANSPORT_SHA256,
            "source_adapter_gate_bundle_transport_sha256": _ADAPTER_GATE_TRANSPORT_SHA256,
            "source_runtime_bridge_design_production_sha256": _PREDECESSOR_PRODUCTION_SHA256,
            "source_runtime_bridge_design_response_sha256": _PREDECESSOR_RESPONSE_SHA256,
            "source_runtime_bridge_blocker": _BLOCKER,
            "audited_runtime_source_records": audited,
            "generate_ligands_current_interface": generate_interface,
            "prepare_pocket_current_interface": prepare_interface,
            "generate_ligands_call_site_records": generate_callers,
            "selected_external_selector_argument_name": _SELECTOR_ARGUMENT,
            "selected_prepare_pocket_argument_name": _SELECTOR_ARGUMENT,
            "target_selector_fields": list(TARGET_RESIDUE_ATOM_CONDITION_SPEC_FIELDS),
            **semantic_contracts,
            "cli_or_public_caller_forwarding_contract": {
                "generate_ligands_call_site_count": len(generate_callers),
                "prepare_pocket_call_site_count": len(prepare_callers),
                "prepare_pocket_call_site_records": prepare_callers,
                "all_generate_ligands_call_sites_audited": True,
                "all_prepare_pocket_call_sites_audited": True,
                "all_public_callers_have_forwarding_contract": external_coverage_resolved,
                "public_python_example": {
                    "callable": "model.generate_ligands",
                    "named_argument": _SELECTOR_ARGUMENT,
                    "selector": {
                        "chain_id": "A",
                        "residue_sequence_number": 279,
                        "residue_insertion_code": " ",
                        "residue_name": "CYS",
                        "atom_name": "SG",
                        "element": "S",
                    },
                },
            },
            "current11_collated_path_contract_unchanged": True,
            "checkpoint_compatibility_decision": _checkpoint_decision(),
            "candidate_decisions": _candidate_decisions(),
            "canonical_mask_semantic_names": list(CANONICAL_MASK_SEMANTIC_NAMES),
            "unresolved_path_blockers": unresolved,
            "ready_for_runtime_bridge_implementation": external_coverage_resolved,
            "recommended_next_step": (
                "implement_covapie_target_residue_atom_condition_runtime_bridge_v1"
                if external_coverage_resolved
                else "resolve_covapie_external_pocket_runtime_bridge_remaining_blockers_v1"
            ),
            "feature_semantics_audit_required_before_training": True,
            "external_path_coverage_resolution_sha256": "",
        }
        response["external_path_coverage_resolution_sha256"] = _digest_record(
            response,
            EXTERNAL_PATH_COVERAGE_RESOLUTION_FIELDS,
            "external_path_coverage_resolution_sha256",
        )
        _validate_response(response)
        if (
            supplied != snapshots
            or predecessor_constants != (
                predecessor.CANONICAL_MASK_SEMANTIC_NAMES,
                predecessor.RUNTIME_BRIDGE_DESIGN_RESPONSE_FIELDS,
            )
        ):
            raise ValueError(_ERROR)
        return response
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
