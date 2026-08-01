"""Pure design audit for the target-residue atom-condition runtime bridge V1.

The public function binds the four formal Current11 predecessor bundles and
the frozen runtime sources.  It describes, but does not implement, a
same-name boolean sidecar in the pocket runtime dictionary.  No value from
this module is passed to DDPM dynamics or to EGNN.
"""

from __future__ import annotations

import ast
import hashlib
import json
import stat
from pathlib import Path
from typing import Any, Mapping, Sequence

from covalent_ext import covapie_target_residue_atom_condition_adapter_gate_v1 as adapter_gate


__all__ = (
    "design_covapie_target_residue_atom_condition_runtime_bridge_v1",
)


_ERROR = "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_RUNTIME_BRIDGE_DESIGN_INVALID"
_VERSION = "covapie_target_residue_atom_condition_runtime_bridge_design_v1"
_FIELD = "pocket_target_residue_atom_condition_indicator"
_MAX_BYTES = 32 * 1024 * 1024

_AUTHORITY_TRANSPORT_SHA256 = "a95ae52e091a7117b241269eebd891f3ee97e3ae4a6b4e14fa441ab6a1ed2096"
_ALIGNMENT_TRANSPORT_SHA256 = "7f80a810ff35c4ea5d61262021379767a4d15202badd8ec6a6b846405147d842"
_ADAPTER_TRANSPORT_SHA256 = "983c25ea8c52ca54f0c0292990a625e9a9cf0d2370cb517d66a84801d957b65a"
_ADAPTER_GATE_TRANSPORT_SHA256 = "c7e2c9eec92d560fc55206399d9b27df511733821ce3233c3546da38d9992a9d"
_ADAPTER_GATE_INTERNAL_SHA256 = "97821184d8c76618bb549dd708132bd9579687c6f3a0ba8007d0bbc80d7d6602"
_ADAPTER_GATE_PRODUCTION_SHA256 = "11f3cc471427b1d2b56d36e8bca43448136ef0256ebde76e2f78058edf0f029b"

_RUNTIME_SOURCE_SHA256S = (
    ("dataset.py", "d1c548185521692ca14be062e34d5bea617f8d3c89a22eaef4ddb13a52907c99"),
    ("lightning_modules.py", "2b771068eda19b6f783e12ff483a02ab6ef8264108f3af5e486d3381fb1e7fb6"),
    ("equivariant_diffusion/conditional_model.py", "260bb941e05a3beaa0f1aef7aebba86aa2474d5f5db75637ec1498e3ad0e47b4"),
    ("equivariant_diffusion/en_diffusion.py", "841f95e8d47fd1bc27f50b76f605bf6d0369308c68c7a65b199e51b00b30d8ef"),
    ("equivariant_diffusion/dynamics.py", "16b008598de7c61c0b5575e3af02f9b1a9e6697559864df1591314e4b4ec6b9f"),
)

CANONICAL_MASK_SEMANTIC_NAMES = (
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
)

RUNTIME_BRIDGE_DESIGN_RESPONSE_FIELDS = (
    "runtime_bridge_design_version",
    "source_authority_bundle_transport_sha256",
    "source_alignment_bundle_transport_sha256",
    "source_adapter_bundle_transport_sha256",
    "source_adapter_gate_bundle_transport_sha256",
    "source_adapter_gate_bundle_sha256",
    "source_adapter_gate_production_sha256",
    "current_runtime_interface_records",
    "source_batch_field_name",
    "destination_pocket_field_name",
    "selected_bridge_location",
    "selected_bridge_representation",
    "field_optional_for_legacy_batches",
    "field_required_when_present_contract",
    "field_torch_dtype",
    "field_runtime_shape",
    "per_sample_cardinality_policy",
    "normalization_preservation_policy",
    "centering_rotation_policy",
    "training_path_coverage",
    "evaluation_path_coverage",
    "conditional_sampling_path_coverage",
    "indicator_passed_into_dynamics",
    "checkpoint_compatibility_decision",
    "candidate_decisions",
    "canonical_mask_semantic_names",
    "ready_for_runtime_bridge_implementation",
    "recommended_next_step",
    "feature_semantics_audit_required_before_training",
    "runtime_bridge_design_response_sha256",
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
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
    ]
    if len(matches) != 1 or not isinstance(matches[0], ast.FunctionDef):
        raise ValueError(_ERROR)
    return matches[0]


def _calls_attribute(node: ast.AST, owner: str, attribute: str) -> bool:
    return any(
        isinstance(child, ast.Call)
        and isinstance(child.func, ast.Attribute)
        and child.func.attr == attribute
        and isinstance(child.func.value, ast.Name)
        and child.func.value.id == owner
        for child in ast.walk(node)
    )


def _calls_self_attribute(node: ast.AST, attribute: str) -> bool:
    return _calls_attribute(node, "self", attribute)


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
            keys = tuple(
                key.value for key in child.value.keys
                if isinstance(key, ast.Constant) and type(key.value) is str
            )
            matches.append(keys)
    if len(matches) != 1:
        raise ValueError(_ERROR)
    return matches[0]


def _subscript_string_keys(node: ast.AST, owner: str) -> set[str]:
    keys: set[str] = set()
    for child in ast.walk(node):
        if (
            isinstance(child, ast.Subscript)
            and isinstance(child.value, ast.Name)
            and child.value.id == owner
            and isinstance(child.slice, ast.Constant)
            and type(child.slice.value) is str
        ):
            keys.add(child.slice.value)
    return keys


def _assigned_subscript_keys(node: ast.AST, owner: str) -> set[str]:
    keys: set[str] = set()
    for child in ast.walk(node):
        if not isinstance(child, (ast.Assign, ast.AugAssign)):
            continue
        targets = child.targets if isinstance(child, ast.Assign) else [child.target]
        for target in targets:
            if (
                isinstance(target, ast.Subscript)
                and isinstance(target.value, ast.Name)
                and target.value.id == owner
                and isinstance(target.slice, ast.Constant)
                and type(target.slice.value) is str
            ):
                keys.add(target.slice.value)
    return keys


def _path_record(path: str, *, uses_get: bool, route: str) -> dict[str, Any]:
    return {
        "path": path,
        "route": route,
        "uses_get_ligand_and_pocket": uses_get,
        "bridge_field_available_after_get_ligand_and_pocket": uses_get,
        "bridge_field_preserved_in_pocket_dictionary": uses_get,
        "bridge_field_consumed_by_model": False,
    }


def _audit_dataset(tree: ast.Module, source_sha256: str) -> dict[str, Any]:
    dataset = _class(tree, "ProcessedLigandPocketDataset")
    initializer = _method(dataset, "__init__")
    collate = _method(dataset, "collate_fn")
    initializer_text = ast.dump(initializer, include_attributes=False)
    collate_text = ast.dump(collate, include_attributes=False)
    split_audited = (
        "Constant(value='lig')" in initializer_text
        and "Constant(value='pocket_mask')" in initializer_text
        and "IfExp" in initializer_text
    )
    collate_audited = (
        "Constant(value='mask')" in collate_text
        and collate_text.count("attr='cat'") >= 2
        and "attr='ones'" in collate_text
    )
    if not split_audited or not collate_audited or "lig" in _FIELD or "mask" in _FIELD:
        raise ValueError(_ERROR)
    return {
        "source_path": "dataset.py",
        "source_sha256": source_sha256,
        "interface": "ProcessedLigandPocketDataset.__init__+collate_fn",
        "field_split_by_pocket_mask": True,
        "field_collated_by_direct_torch_cat": True,
        "field_rebuilt_as_batch_membership_mask": False,
        "audited": True,
    }


def _audit_lightning(tree: ast.Module, source_sha256: str) -> tuple[dict[str, Any], dict[str, Any]]:
    lightning = _class(tree, "LigandPocketDDPM")
    get_method = _method(lightning, "get_ligand_and_pocket")
    if _dict_assignment_keys(get_method, "ligand") != ("x", "one_hot", "size", "mask"):
        raise ValueError(_ERROR)
    if _dict_assignment_keys(get_method, "pocket") != ("x", "one_hot", "size", "mask"):
        raise ValueError(_ERROR)
    call_sites = tuple(
        node.name for node in lightning.body
        if isinstance(node, ast.FunctionDef) and _calls_self_attribute(node, "get_ligand_and_pocket")
    )
    expected_call_sites = (
        "forward",
        "sample_and_analyze_given_pocket",
        "sample_and_save_given_pocket",
        "sample_chain_and_save_given_pocket",
    )
    if call_sites != expected_call_sites or _FIELD in _subscript_string_keys(get_method, "pocket"):
        raise ValueError(_ERROR)

    training_step = _method(lightning, "training_step")
    shared_eval = _method(lightning, "_shared_eval")
    validation_step = _method(lightning, "validation_step")
    test_step = _method(lightning, "test_step")
    generate_ligands = _method(lightning, "generate_ligands")
    if (
        not _calls_self_attribute(training_step, "forward")
        or not _calls_self_attribute(shared_eval, "forward")
        or not _calls_self_attribute(validation_step, "_shared_eval")
        or not _calls_self_attribute(test_step, "_shared_eval")
        or not _calls_self_attribute(generate_ligands, "prepare_pocket")
        or _calls_self_attribute(generate_ligands, "get_ligand_and_pocket")
        or not _calls_attribute(generate_ligands, "self", "prepare_pocket")
    ):
        raise ValueError(_ERROR)
    generate_dump = ast.dump(generate_ligands, include_attributes=False)
    if "attr='sample_given_pocket'" not in generate_dump or "attr='inpaint'" not in generate_dump:
        raise ValueError(_ERROR)

    record = {
        "source_path": "lightning_modules.py",
        "source_sha256": source_sha256,
        "interface": "LigandPocketDDPM.get_ligand_and_pocket",
        "current_ligand_keys": ["x", "one_hot", "size", "mask"],
        "current_pocket_keys": ["x", "one_hot", "size", "mask"],
        "get_ligand_and_pocket_call_sites": list(call_sites),
        "external_pdb_generate_ligands_bypasses_get_ligand_and_pocket": True,
        "runtime_bridge_implemented": False,
        "audited": True,
    }
    path_facts = {
        "training_forward": True,
        "validation_forward": True,
        "test_forward": True,
        "collated_given_pocket_methods": list(expected_call_sites[1:]),
        "external_pdb_generate_ligands_bypass": True,
    }
    return record, path_facts


def _audit_conditional(tree: ast.Module, source_sha256: str) -> dict[str, Any]:
    conditional = _class(tree, "ConditionalDDPM")
    consumed: set[str] = set()
    for node in conditional.body:
        if isinstance(node, ast.FunctionDef):
            consumed.update(_subscript_string_keys(node, "pocket"))
    if consumed != {"x", "one_hot", "size", "mask"} or _FIELD in consumed:
        raise ValueError(_ERROR)
    return {
        "source_path": "equivariant_diffusion/conditional_model.py",
        "source_sha256": source_sha256,
        "interface": "ConditionalDDPM",
        "consumed_pocket_keys": sorted(consumed),
        "indicator_consumed": False,
        "audited": True,
    }


def _audit_normalize(tree: ast.Module, source_sha256: str) -> dict[str, Any]:
    diffusion = _class(tree, "EnVariationalDiffusion")
    normalize = _method(diffusion, "normalize")
    assigned = _assigned_subscript_keys(normalize, "pocket")
    if assigned != {"x", "one_hot"} or _FIELD in assigned:
        raise ValueError(_ERROR)
    return {
        "source_path": "equivariant_diffusion/en_diffusion.py",
        "source_sha256": source_sha256,
        "interface": "EnVariationalDiffusion.normalize",
        "mutated_pocket_keys": sorted(assigned),
        "additional_pocket_keys_preserved_by_dictionary_identity": True,
        "audited": True,
    }


def _audit_dynamics(tree: ast.Module, source_sha256: str) -> dict[str, Any]:
    dynamics = _class(tree, "EGNNDynamics")
    forward = _method(dynamics, "forward")
    arguments = tuple(argument.arg for argument in forward.args.args)
    expected = ("self", "xh_atoms", "xh_residues", "t", "mask_atoms", "mask_residues")
    if arguments != expected or any("indicator" in argument for argument in arguments):
        raise ValueError(_ERROR)
    return {
        "source_path": "equivariant_diffusion/dynamics.py",
        "source_sha256": source_sha256,
        "interface": "EGNNDynamics.forward",
        "forward_arguments": list(arguments[1:]),
        "accepts_indicator": False,
        "audited": True,
    }


def _validate_present_indicator(indicator: object, sample_node_counts: object) -> bool:
    """Validate the frozen Current11 present-field contract (design oracle only)."""

    try:
        if (
            type(indicator) is not list
            or type(sample_node_counts) is not list
            or not sample_node_counts
            or any(type(count) is not int or type(count) is bool or count <= 0 for count in sample_node_counts)
            or any(type(value) is not bool for value in indicator)
            or len(indicator) != sum(sample_node_counts)
        ):
            raise ValueError(_ERROR)
        offset = 0
        for count in sample_node_counts:
            sample_values = indicator[offset:offset + count]
            if sum(value is True for value in sample_values) != 1:
                raise ValueError(_ERROR)
            offset += count
        return True
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


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
        "future_minimal_implementation_boundary": "lightning_modules.py:LigandPocketDDPM.get_ligand_and_pocket",
    }


def _candidate_decisions() -> list[dict[str, Any]]:
    return [
        {
            "candidate": "same_name_bool_key_in_pocket_runtime_dictionary",
            "decision": "accepted",
            "reason": "preserves_node_alignment_feature_width_return_arity_and_checkpoint_state",
        },
        {
            "candidate": "append_indicator_to_pocket_one_hot",
            "decision": "rejected",
            "reason": "changes_residue_nf_residue_encoder_and_checkpoint_tensor_shapes",
        },
        {
            "candidate": "per_sample_local_target_index_scalar",
            "decision": "rejected",
            "reason": "fragile_after_collate_or_reorder_and_not_flat_node_aligned",
        },
        {
            "candidate": "duplicate_target_xyz_or_atom_one_hot",
            "decision": "rejected",
            "reason": "duplicates_views_that_can_drift_after_centering_rotation_or_normalization",
        },
        {
            "candidate": "module_global_singleton_cache_or_implicit_hook_state",
            "decision": "rejected",
            "reason": "hidden_mutable_state_is_unsafe_for_batches_multi_gpu_and_sampling",
        },
        {
            "candidate": "modify_ConditionalDDPM_or_EGNNDynamics_or_add_condition_encoder",
            "decision": "deferred",
            "reason": "belongs_to_model_consumption_not_runtime_bridge",
        },
    ]


def _walk_values(value: object) -> list[object]:
    if isinstance(value, Mapping):
        return [item for nested in value.values() for item in _walk_values(nested)]
    if isinstance(value, (list, tuple)):
        return [item for nested in value for item in _walk_values(nested)]
    return [value]


def _validate_response(response: Mapping[str, Any]) -> bool:
    try:
        ordered = {field: response[field] for field in RUNTIME_BRIDGE_DESIGN_RESPONSE_FIELDS}
        if (
            type(response) is not dict
            or len(response) != 30
            or tuple(response) != RUNTIME_BRIDGE_DESIGN_RESPONSE_FIELDS
            or set(response) != set(RUNTIME_BRIDGE_DESIGN_RESPONSE_FIELDS)
            or response["runtime_bridge_design_version"] != _VERSION
            or response["source_batch_field_name"] != _FIELD
            or response["destination_pocket_field_name"] != _FIELD
            or response["selected_bridge_location"] != "LigandPocketDDPM.get_ligand_and_pocket_to_pocket_runtime_dictionary"
            or response["selected_bridge_representation"] != "same_name_per_pocket_node_bool_sidecar"
            or response["field_optional_for_legacy_batches"] is not True
            or response["field_torch_dtype"] != "torch.bool"
            or response["field_runtime_shape"] != "[sum(num_pocket_nodes)]"
            or response["indicator_passed_into_dynamics"] is not False
            or tuple(response["canonical_mask_semantic_names"]) != CANONICAL_MASK_SEMANTIC_NAMES
            or response["feature_semantics_audit_required_before_training"] is not True
            or response["runtime_bridge_design_response_sha256"]
            != _digest_record(ordered, RUNTIME_BRIDGE_DESIGN_RESPONSE_FIELDS, "runtime_bridge_design_response_sha256")
            or any(isinstance(value, Path) for value in _walk_values(response))
        ):
            raise ValueError(_ERROR)
        return True
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def design_covapie_target_residue_atom_condition_runtime_bridge_v1(
    *,
    source_authority_bundle: bytes,
    source_alignment_bundle: bytes,
    source_adapter_bundle: bytes,
    source_adapter_gate_bundle: bytes,
    repo_root: Path,
) -> dict[str, Any]:
    """Return the deterministic Exact30 runtime-bridge design response."""

    if (
        type(source_authority_bundle) is not bytes
        or type(source_alignment_bundle) is not bytes
        or type(source_adapter_bundle) is not bytes
        or type(source_adapter_gate_bundle) is not bytes
        or type(repo_root) is not type(Path())
    ):
        raise ValueError(_ERROR)
    snapshots = (
        bytes(source_authority_bundle),
        bytes(source_alignment_bundle),
        bytes(source_adapter_bundle),
        bytes(source_adapter_gate_bundle),
    )
    predecessor_constants = (
        adapter_gate.CANONICAL_MASK_SEMANTIC_NAMES,
        adapter_gate.TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_RECORD_FIELDS,
        adapter_gate.TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_BUNDLE_FIELDS,
    )
    try:
        if predecessor_constants[0] != CANONICAL_MASK_SEMANTIC_NAMES:
            raise ValueError(_ERROR)
        metadata = repo_root.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise ValueError(_ERROR)
        supplied = (
            source_authority_bundle,
            source_alignment_bundle,
            source_adapter_bundle,
            source_adapter_gate_bundle,
        )
        expected_transport = (
            _AUTHORITY_TRANSPORT_SHA256,
            _ALIGNMENT_TRANSPORT_SHA256,
            _ADAPTER_TRANSPORT_SHA256,
            _ADAPTER_GATE_TRANSPORT_SHA256,
        )
        if tuple(_sha256(payload) for payload in supplied) != expected_transport:
            raise ValueError(_ERROR)

        gate_production = _read_regular(
            repo_root,
            "src/covalent_ext/covapie_target_residue_atom_condition_adapter_gate_v1.py",
        )
        if _sha256(gate_production) != _ADAPTER_GATE_PRODUCTION_SHA256:
            raise ValueError(_ERROR)

        # The formal predecessor must be rebuilt, including its runtime dataset
        # exercise, and its canonical transport bytes must match exactly.
        recompiled_gate = adapter_gate.evaluate_covapie_target_residue_atom_condition_adapter_gate_v1(
            source_authority_bundle=source_authority_bundle,
            source_alignment_bundle=source_alignment_bundle,
            source_adapter_bundle=source_adapter_bundle,
            repo_root=repo_root,
        )
        if adapter_gate._bundle_bytes(recompiled_gate) != source_adapter_gate_bundle:
            raise ValueError(_ERROR)
        supplied_gate = _strict_json(source_adapter_gate_bundle)
        adapter_gate._validate_gate_bundle(supplied_gate, require_field_order=False)
        if (
            supplied_gate.get("target_residue_atom_condition_adapter_gate_bundle_sha256")
            != _ADAPTER_GATE_INTERNAL_SHA256
            or supplied_gate.get("target_residue_atom_condition_adapter_gate_record_count") != 11
            or supplied_gate.get("runtime_dataset_sample_count") != 11
            or supplied_gate.get("total_runtime_pocket_node_count") != 2202
            or supplied_gate.get("total_runtime_indicator_true_count") != 11
            or supplied_gate.get("all_records_runtime_ready_unique") is not True
            or supplied_gate.get("ready_for_runtime_bridge_design") is not True
            or supplied_gate.get("recommended_next_step")
            != "design_covapie_target_residue_atom_condition_runtime_bridge_v1"
            or supplied_gate.get("feature_semantics_audit_required_before_training") is not True
            or adapter_gate._canonical_json_bytes(supplied_gate) != source_adapter_gate_bundle
        ):
            raise ValueError(_ERROR)

        payloads: dict[str, bytes] = {}
        for path, expected_sha256 in _RUNTIME_SOURCE_SHA256S:
            payload = _read_regular(repo_root, path)
            if _sha256(payload) != expected_sha256:
                raise ValueError(_ERROR)
            payloads[path] = payload

        dataset_record = _audit_dataset(
            _parse_source(payloads["dataset.py"]), dict(_RUNTIME_SOURCE_SHA256S)["dataset.py"]
        )
        lightning_record, path_facts = _audit_lightning(
            _parse_source(payloads["lightning_modules.py"]),
            dict(_RUNTIME_SOURCE_SHA256S)["lightning_modules.py"],
        )
        conditional_record = _audit_conditional(
            _parse_source(payloads["equivariant_diffusion/conditional_model.py"]),
            dict(_RUNTIME_SOURCE_SHA256S)["equivariant_diffusion/conditional_model.py"],
        )
        normalize_record = _audit_normalize(
            _parse_source(payloads["equivariant_diffusion/en_diffusion.py"]),
            dict(_RUNTIME_SOURCE_SHA256S)["equivariant_diffusion/en_diffusion.py"],
        )
        dynamics_record = _audit_dynamics(
            _parse_source(payloads["equivariant_diffusion/dynamics.py"]),
            dict(_RUNTIME_SOURCE_SHA256S)["equivariant_diffusion/dynamics.py"],
        )
        runtime_records = [
            dataset_record,
            lightning_record,
            conditional_record,
            normalize_record,
            dynamics_record,
        ]

        training_paths = [
            _path_record(
                "training_step->forward->get_ligand_and_pocket",
                uses_get=path_facts["training_forward"],
                route="collated_batch",
            )
        ]
        evaluation_paths = [
            _path_record(
                "validation_step->_shared_eval->forward->get_ligand_and_pocket",
                uses_get=path_facts["validation_forward"],
                route="collated_batch",
            ),
            _path_record(
                "test_step->_shared_eval->forward->get_ligand_and_pocket",
                uses_get=path_facts["test_forward"],
                route="collated_batch",
            ),
        ]
        conditional_paths = [
            _path_record(
                f"{name}->get_ligand_and_pocket->ConditionalDDPM.sample_given_pocket",
                uses_get=True,
                route="collated_batch",
            )
            for name in path_facts["collated_given_pocket_methods"]
        ]
        conditional_paths.append(
            _path_record(
                "generate_ligands->prepare_pocket->ConditionalDDPM.sample_given_pocket_or_inpaint",
                uses_get=False,
                route="external_pdb_given_pocket_and_inpainting",
            )
        )
        bypasses = [path["path"] for path in conditional_paths if not path["uses_get_ligand_and_pocket"]]
        ready = (
            all(path["uses_get_ligand_and_pocket"] for path in training_paths)
            and all(path["uses_get_ligand_and_pocket"] for path in evaluation_paths)
            and not bypasses
        )

        response: dict[str, Any] = {
            "runtime_bridge_design_version": _VERSION,
            "source_authority_bundle_transport_sha256": _AUTHORITY_TRANSPORT_SHA256,
            "source_alignment_bundle_transport_sha256": _ALIGNMENT_TRANSPORT_SHA256,
            "source_adapter_bundle_transport_sha256": _ADAPTER_TRANSPORT_SHA256,
            "source_adapter_gate_bundle_transport_sha256": _ADAPTER_GATE_TRANSPORT_SHA256,
            "source_adapter_gate_bundle_sha256": _ADAPTER_GATE_INTERNAL_SHA256,
            "source_adapter_gate_production_sha256": _ADAPTER_GATE_PRODUCTION_SHA256,
            "current_runtime_interface_records": runtime_records,
            "source_batch_field_name": _FIELD,
            "destination_pocket_field_name": _FIELD,
            "selected_bridge_location": "LigandPocketDDPM.get_ligand_and_pocket_to_pocket_runtime_dictionary",
            "selected_bridge_representation": "same_name_per_pocket_node_bool_sidecar",
            "field_optional_for_legacy_batches": True,
            "field_required_when_present_contract": {
                "torch_dtype": "torch.bool",
                "domain": "per_pocket_node",
                "shape": "[sum(num_pocket_nodes)]",
                "device": "same_as_pocket_x",
                "node_order": "identical_to_pocket_x_and_pocket_one_hot",
                "current11_field_required": True,
                "legacy_absent_creates_destination_key": False,
                "legacy_absent_creates_all_false_tensor": False,
                "mixed_noncovalent_zero_target_semantics_deferred": True,
            },
            "field_torch_dtype": "torch.bool",
            "field_runtime_shape": "[sum(num_pocket_nodes)]",
            "per_sample_cardinality_policy": {
                "current11_resolved_covalent_true_count": 1,
                "all_false_when_present_allowed": False,
                "multiple_true_allowed": False,
                "node_length_mismatch_allowed": False,
                "legacy_field_absent_allowed": True,
                "mixed_noncovalent_zero_target_semantics_deferred": True,
            },
            "normalization_preservation_policy": {
                "normalize_mutates_only_pocket_x_and_one_hot": True,
                "sidecar_key_preserved": True,
                "sidecar_value_not_normalized": True,
            },
            "centering_rotation_policy": {
                "identity_source": _FIELD,
                "coordinate_lookup_for_identity_allowed": False,
                "derived_views_persisted": False,
                "derived_views": [
                    "target_condition_flat_indices",
                    "target_condition_xyz",
                    "target_condition_atom_one_hot",
                    "target_condition_batch_ids",
                ],
                "derived_xyz_uses_current_centered_normalized_pocket_coordinates": True,
            },
            "training_path_coverage": {
                "paths": training_paths,
                "all_paths_use_get_ligand_and_pocket": all(
                    path["uses_get_ligand_and_pocket"] for path in training_paths
                ),
            },
            "evaluation_path_coverage": {
                "paths": evaluation_paths,
                "all_paths_use_get_ligand_and_pocket": all(
                    path["uses_get_ligand_and_pocket"] for path in evaluation_paths
                ),
            },
            "conditional_sampling_path_coverage": {
                "collated_given_pocket_paths_covered": True,
                "actual_inpainting_paths_audited": True,
                "paths": conditional_paths,
                "bypassing_paths": bypasses,
                "all_paths_use_get_ligand_and_pocket": not bypasses,
            },
            "indicator_passed_into_dynamics": False,
            "checkpoint_compatibility_decision": _checkpoint_decision(),
            "candidate_decisions": _candidate_decisions(),
            "canonical_mask_semantic_names": list(CANONICAL_MASK_SEMANTIC_NAMES),
            "ready_for_runtime_bridge_implementation": ready,
            "recommended_next_step": (
                "implement_covapie_target_residue_atom_condition_runtime_bridge_v1"
                if ready
                else "resolve_covapie_external_pocket_runtime_bridge_path_coverage_v1"
            ),
            "feature_semantics_audit_required_before_training": True,
            "runtime_bridge_design_response_sha256": "",
        }
        response["runtime_bridge_design_response_sha256"] = _digest_record(
            response,
            RUNTIME_BRIDGE_DESIGN_RESPONSE_FIELDS,
            "runtime_bridge_design_response_sha256",
        )
        _validate_response(response)
        if (
            supplied != snapshots
            or predecessor_constants
            != (
                adapter_gate.CANONICAL_MASK_SEMANTIC_NAMES,
                adapter_gate.TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_RECORD_FIELDS,
                adapter_gate.TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_GATE_BUNDLE_FIELDS,
            )
        ):
            raise ValueError(_ERROR)
        return response
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
