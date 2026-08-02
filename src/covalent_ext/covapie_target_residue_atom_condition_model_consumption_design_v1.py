"""Pure design audit for CovaPIE target-residue model consumption V1.

This module binds the formal runtime-bridge gate, the unchanged DiffSBDD model
sources, and the legacy full-atom conditional checkpoint.  It returns a
deterministic architecture contract; it does not instantiate a model, execute a
forward path, alter a state dict, or write any file.
"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import warnings
from pathlib import Path
from typing import Any, Mapping, Sequence

import torch

from covalent_ext import covapie_target_residue_atom_condition_runtime_bridge_gate_v1 as gate


__all__ = (
    "design_covapie_target_residue_atom_condition_model_consumption_v1",
)


_ERROR = "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_MODEL_CONSUMPTION_DESIGN_INVALID"
_VERSION = "covapie_target_residue_atom_condition_model_consumption_design_v1"
_GATE_COMMIT = "148689cc0716a56f3eb991f762af0010c5849f3a"
_GATE_PARENT = "75589a94235dde2d0943606e58a1f2216b31d3b2"
_GATE_BUNDLE_TRANSPORT_SHA256 = "835032d1b0a9d9af9abe0839e9be798f0d4f178bcd9d4af3323592c5e59aa597"
_GATE_BUNDLE_INTERNAL_SHA256 = "035d45fb50a15e29b367a6af71d9ca28019b5d77c5d5ed82d253b78570e5750d"
_GATE_PRODUCTION_PATH = (
    "src/covalent_ext/"
    "covapie_target_residue_atom_condition_runtime_bridge_gate_v1.py"
)
_GATE_PRODUCTION_SHA256 = "3b7a9a485eecee122eefcbe8c2eb1f076d7711c9a77bb39ebf2e0249481d703e"
_FIELD = "pocket_target_residue_atom_condition_indicator"
_ENABLE_FLAG = "target_residue_atom_conditioning"
_PARAMETER = "target_residue_atom_condition_embedding"
_NEW_STATE_KEY = "ddpm.dynamics.target_residue_atom_condition_embedding"
_INJECTION_POINT = (
    "after_residue_encoder_before_atom_residue_concatenation_and_before_time_concatenation"
)
_CHECKPOINT_PATH = "checkpoints/crossdocked_fullatom_cond.ckpt"
_CHECKPOINT_SIZE = 17861341
_CHECKPOINT_SHA256 = "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
_CHECKPOINT_KEY_MANIFEST_SHA256 = "3ff753379384502f43a65ea8e9116a47d08a404420966b4fd671c307ad98faaa"
_CHECKPOINT_SHAPE_MANIFEST_SHA256 = "94e426ea3d114d50dbac63f2f8af7b3f5c14ca97df8a99afebbd3838473c0692"
_CURRENT11_LINEAGE_PROJECTION_SHA256 = (
    "c4918fd0ee226de4bdee5aded27e06b615ca56c8f5085c044ef035cf172d71e9"
)

_SOURCE_SHA256 = {
    "lightning_modules.py": "8d111f8c45d90cbdf6d0dcf7f4e4796bc7ebe0f1b0065e750eab0a16b4c01d5a",
    "equivariant_diffusion/conditional_model.py": "260bb941e05a3beaa0f1aef7aebba86aa2474d5f5db75637ec1498e3ad0e47b4",
    "equivariant_diffusion/en_diffusion.py": "841f95e8d47fd1bc27f50b76f605bf6d0369308c68c7a65b199e51b00b30d8ef",
    "equivariant_diffusion/dynamics.py": "16b008598de7c61c0b5575e3af02f9b1a9e6697559864df1591314e4b4ec6b9f",
    "equivariant_diffusion/egnn_new.py": "87001209a047133519371d4a01e3e2bdddc55bf3d41e9a7ff68a2664badc2333",
}

CANONICAL_MASK_SEMANTIC_NAMES = (
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
)

MODEL_CONSUMPTION_DESIGN_RESPONSE_FIELDS = (
    "model_consumption_design_version",
    "source_runtime_bridge_gate_bundle_transport_sha256",
    "source_runtime_bridge_gate_bundle_sha256",
    "source_runtime_bridge_gate_production_sha256",
    "source_runtime_bridge_gate_commit",
    "source_lightning_module_sha256",
    "source_conditional_model_sha256",
    "source_en_diffusion_sha256",
    "source_dynamics_sha256",
    "source_egnn_sha256",
    "source_checkpoint_sha256",
    "source_checkpoint_size",
    "checkpoint_profile",
    "audited_dynamics_call_site_records",
    "audited_checkpoint_load_site_records",
    "selected_condition_field_name",
    "selected_enable_flag_name",
    "selected_dynamics_argument_name",
    "selected_injection_module",
    "selected_injection_point",
    "selected_condition_representation",
    "selected_parameter_name",
    "selected_parameter_shape",
    "selected_parameter_initialization",
    "selected_parameter_creation_policy",
    "legacy_disabled_state_dict_policy",
    "base_to_conditioned_checkpoint_migration_policy",
    "conditioned_checkpoint_strict_load_policy",
    "condition_presence_semantics",
    "mixed_batch_semantics",
    "normalization_and_noise_policy",
    "equivariance_contract",
    "conditional_training_path_contract",
    "conditional_eval_path_contract",
    "conditional_sampling_path_contract",
    "joint_training_path_contract",
    "inpainting_path_contract",
    "simple_conditional_path_contract",
    "candidate_decisions",
    "existing_state_dict_compatibility_decision",
    "canonical_mask_semantic_names",
    "implementation_scope",
    "unresolved_blockers",
    "ready_for_model_consumption_implementation",
    "recommended_next_step",
    "feature_semantics_audit_required_before_training",
    "model_consumption_design_response_sha256",
)

_EXPECTED_DYNAMICS_SITES = (
    ("equivariant_diffusion/conditional_model.py", "ConditionalDDPM", "sample_p_xh_given_z0", 119),
    ("equivariant_diffusion/conditional_model.py", "ConditionalDDPM", "forward", 253),
    ("equivariant_diffusion/conditional_model.py", "ConditionalDDPM", "forward", 306),
    ("equivariant_diffusion/conditional_model.py", "ConditionalDDPM", "sample_p_zs_given_zt", 445),
    ("equivariant_diffusion/en_diffusion.py", "EnVariationalDiffusion", "sample_p_xh_given_z0", 270),
    ("equivariant_diffusion/en_diffusion.py", "EnVariationalDiffusion", "forward", 378),
    ("equivariant_diffusion/en_diffusion.py", "EnVariationalDiffusion", "forward", 436),
    ("equivariant_diffusion/en_diffusion.py", "EnVariationalDiffusion", "sample_p_zs_given_zt", 516),
)

_EXPECTED_CHECKPOINT_SITE_IDENTITIES = {
    ("colab/DiffSBDD.ipynb", "LigandPocketDDPM.load_from_checkpoint", "notebook_code_cell"),
    ("data/prepare_crossdocked.py", "torch.load", "<module>"),
    ("generate_ligands.py", "LigandPocketDDPM.load_from_checkpoint", "<module>"),
    ("inpaint.py", "LigandPocketDDPM.load_from_checkpoint", "<module>"),
    ("optimize.py", "LigandPocketDDPM.load_from_checkpoint", "<module>"),
    ("process_crossdock.py", "torch.load", "<module>"),
    ("scripts/covalent_inpaint_demo.py", "LigandPocketDDPM.load_from_checkpoint", "main"),
    ("src/covalent_ext/checkpoint_compatible_model_instantiation.py", "torch.load", "load_checkpoint_shape_reference_v0"),
    ("src/covalent_ext/checkpoint_compatible_pretrained_load_smoke.py", "torch.load", "load_checkpoint_state_dict_for_smoke_v0"),
    ("src/covalent_ext/checkpoint_compatible_pretrained_load_smoke.py", "load_state_dict", "strict_load_checkpoint_weights_v0"),
    ("src/covalent_ext/checkpoint_original_config_instantiation_design.py", "torch.load", "load_checkpoint_hparams_for_design_v0"),
    ("src/covalent_ext/first_checkpointed_training_dry_run.py", "torch.load", "run_resume_smoke_v0"),
    ("src/covalent_ext/first_checkpointed_training_dry_run.py", "load_state_dict", "run_resume_smoke_v0"),
    ("src/covalent_ext/first_checkpointed_training_dry_run_review.py", "torch.load", "_torch_load_cpu"),
    ("src/covalent_ext/pretrained_checkpoint_architecture_reconciliation.py", "torch.load", "load_checkpoint_architecture_evidence_v0"),
    ("src/covalent_ext/pretrained_checkpoint_load_smoke.py", "torch.load", "load_pretrained_checkpoint_payload_v0"),
    ("src/covalent_ext/pretrained_checkpoint_load_smoke.py", "load_state_dict", "attempt_load_pretrained_state_dict_v0"),
    ("src/covalent_ext/covapie_target_residue_atom_condition_model_consumption_design_v1.py", "torch.load", "_inspect_checkpoint"),
    ("test.py", "LigandPocketDDPM.load_from_checkpoint", "<module>"),
    ("tests/test_first_checkpointed_training_dry_run_v0.py", "torch.load", "test_script_run_writes_single_checkpoint_metadata_resume_reports_and_summary"),
    ("train.py", "torch.load", "<module>"),
}

_MODEL_CLI_LOAD_PATHS = {
    "colab/DiffSBDD.ipynb",
    "generate_ligands.py",
    "inpaint.py",
    "optimize.py",
    "scripts/covalent_inpaint_demo.py",
    "test.py",
}


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _response_digest(response: Mapping[str, Any]) -> str:
    if tuple(response) != MODEL_CONSUMPTION_DESIGN_RESPONSE_FIELDS:
        raise ValueError(_ERROR)
    return _sha256(_canonical_json_bytes({
        field: response[field]
        for field in MODEL_CONSUMPTION_DESIGN_RESPONSE_FIELDS
        if field != "model_consumption_design_response_sha256"
    }))


def _read_regular(path: Path, *, expected_size: int | None = None) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise ValueError(_ERROR)
    payload = path.read_bytes()
    if expected_size is not None and len(payload) != expected_size:
        raise ValueError(_ERROR)
    return payload


def _git(repo_root: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", *arguments], cwd=repo_root, check=False, capture_output=True,
    )
    if completed.returncode != 0 or completed.stderr != b"":
        raise ValueError(_ERROR)
    return completed.stdout


def _context_for_call(
    node: ast.Call, parents: Mapping[ast.AST, ast.AST],
) -> tuple[str, str]:
    method = "<module>"
    class_name = "<module>"
    parent = parents.get(node)
    while parent is not None:
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            method = parent.name
            ancestor = parents.get(parent)
            while ancestor is not None:
                if isinstance(ancestor, ast.ClassDef):
                    class_name = ancestor.name
                    break
                ancestor = parents.get(ancestor)
            break
        parent = parents.get(parent)
    return class_name, method


def _parse_ast(payload: bytes, filename: str) -> ast.Module:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ast.parse(payload.decode("utf-8"), filename=filename)


def _dynamics_profile(class_name: str, method: str, line: int) -> str:
    profiles = {
        ("ConditionalDDPM", "sample_p_xh_given_z0", 119): (
            "conditional_final_xh_sampling_reached_by_sample_given_pocket_diversify_and_inpaint"
        ),
        ("ConditionalDDPM", "forward", 253): "conditional_training_or_eval_main_t_prediction",
        ("ConditionalDDPM", "forward", 306): "conditional_eval_t0_prediction",
        ("ConditionalDDPM", "sample_p_zs_given_zt", 445): (
            "conditional_iterative_sampling_reached_by_sample_given_pocket_diversify_and_inpaint"
        ),
        ("EnVariationalDiffusion", "sample_p_xh_given_z0", 270): (
            "joint_final_xh_sampling_reached_by_sample_and_inpaint"
        ),
        ("EnVariationalDiffusion", "forward", 378): "joint_training_or_eval_main_t_prediction",
        ("EnVariationalDiffusion", "forward", 436): "joint_eval_t0_prediction",
        ("EnVariationalDiffusion", "sample_p_zs_given_zt", 516): (
            "joint_iterative_sampling_reached_by_sample_and_inpaint"
        ),
    }
    return profiles[(class_name, method, line)]


def _dynamics_condition_source(class_name: str, method: str) -> str:
    if method == "forward":
        return (
            f"top_level_validated_{_FIELD}_from_pocket_dictionary_then_explicitly_threaded"
        )
    if class_name == "ConditionalDDPM":
        return (
            f"static_{_FIELD}_threaded_from_sample_given_pocket_diversify_or_conditional_inpaint"
        )
    return f"static_{_FIELD}_threaded_from_joint_inpaint_or_none_for_unconditional_joint_sample"


def _audit_dynamics_call_sites(repo_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    discovered: list[tuple[str, str, str, int]] = []
    for relative_path in (
        "equivariant_diffusion/conditional_model.py",
        "equivariant_diffusion/en_diffusion.py",
    ):
        tree = _parse_ast(_read_regular(repo_root / relative_path), relative_path)
        parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            function = node.func
            if not (
                isinstance(function, ast.Attribute)
                and function.attr == "dynamics"
                and isinstance(function.value, ast.Name)
                and function.value.id == "self"
            ):
                continue
            class_name, method = _context_for_call(node, parents)
            identity = (relative_path, class_name, method, node.lineno)
            discovered.append(identity)
            records.append({
                "source_path": relative_path,
                "source_line": node.lineno,
                "class": class_name,
                "method": method,
                "training_eval_sampling_profile": _dynamics_profile(
                    class_name, method, node.lineno
                ),
                "current_arguments": [ast.unparse(argument) for argument in node.args],
                "future_condition_argument_source": _dynamics_condition_source(
                    class_name, method
                ),
                "condition_present_behavior": (
                    f"pass_{_FIELD}_explicitly_to_EGNNDynamics_after_top_level_validation;"
                    f"require_{_ENABLE_FLAG}_true"
                ),
                "condition_absent_behavior": (
                    f"pass_{_FIELD}=None_and_preserve_legacy_behavior"
                ),
                "covered": True,
                "blocking_reason": [],
            })
    records.sort(key=lambda item: (item["source_path"], item["source_line"]))
    if (
        len(discovered) != len(_EXPECTED_DYNAMICS_SITES)
        or set(discovered) != set(_EXPECTED_DYNAMICS_SITES)
    ):
        raise ValueError(_ERROR)
    return records


def _checkpoint_call_kind(function: ast.expr) -> str | None:
    if not isinstance(function, ast.Attribute):
        return None
    if (
        function.attr == "load_from_checkpoint"
        and isinstance(function.value, ast.Name)
        and function.value.id == "LigandPocketDDPM"
    ):
        return "LigandPocketDDPM.load_from_checkpoint"
    if (
        function.attr == "load"
        and isinstance(function.value, ast.Name)
        and function.value.id == "torch"
    ):
        return "torch.load"
    if function.attr == "load_state_dict":
        return "load_state_dict"
    return None


def _checkpoint_strict_semantics(kind: str, api: str) -> str:
    if kind == "LigandPocketDDPM.load_from_checkpoint":
        return "strict_true_framework_default_pytorch_lightning_1_8_4"
    if kind == "torch.load":
        return "not_a_state_dict_application"
    if ".load_state_dict" in api and api.startswith("optimizer."):
        return "optimizer_state_load_has_no_model_strict_argument"
    if "strict=False" in api:
        return "explicit_strict_false_historical_smoke_only"
    if "strict=True" in api:
        return "explicit_strict_true"
    return "model_load_state_dict_strict_true_framework_default"


def _checkpoint_site_policies(
    path: str, kind: str, api: str,
) -> tuple[str, str, str, bool]:
    cli_impact = path in _MODEL_CLI_LOAD_PATHS
    if kind == "LigandPocketDDPM.load_from_checkpoint":
        return (
            "legacy_disabled_checkpoint_loads_strictly_with_default_false_enable_flag",
            "conditioned_checkpoint_requires_saved_true_enable_flag_and_strict_load",
            (
                "add_explicit_profile_selection_and_use_exact_one_key_in_memory_migration_helper_"
                "for_base_to_conditioned_loading;never_blanket_strict_false"
            ),
            cli_impact,
        )
    if path == "train.py":
        return (
            "reads_legacy_hyper_parameters_before_trainer_resume",
            "conditioned_resume_requires_flag_true_and_strict_conditioned_state_contract",
            "training_entry_requires_feature_semantics_audit_before_any_conditioned_training",
            True,
        )
    if path in {"data/prepare_crossdocked.py", "process_crossdock.py"}:
        return (
            "loads_dataset_split_not_model_checkpoint",
            "not_a_conditioned_model_load_surface",
            "none_dataset_split_only",
            False,
        )
    if path.endswith("model_consumption_design_v1.py"):
        return (
            "read_only_cpu_checkpoint_schema_audit",
            "read_only_cpu_checkpoint_schema_audit",
            "none_design_audit_never_applies_state_dict",
            False,
        )
    if path.endswith("first_checkpointed_training_dry_run.py") or path.endswith(
        "first_checkpointed_training_dry_run_v0.py"
    ):
        return (
            "historical_dry_run_checkpoint_contract",
            "not_reusable_as_conditioned_DiffSBDD_migration",
            "leave_historical_stage_unchanged",
            False,
        )
    if "strict=False" in api:
        return (
            "historical_partial_pretrained_smoke",
            "forbidden_for_base_to_conditioned_migration",
            "leave_historical_smoke_unchanged_and_do_not_call_it_from_conditioned_loader",
            False,
        )
    return (
        "historical_read_only_or_strict_checkpoint_evidence_path",
        "conditioned_use_requires_exact_new_key_contract_if_ever_reused",
        "no_current_CLI_change;future_helper_must_enforce_exact_shared_keys_shapes_and_one_missing_key",
        False,
    )


def _candidate_checkpoint_paths(repo_root: Path) -> list[str]:
    completed = subprocess.run(
        [
            "rg", "-l", "-g", "*.py", "-g", "*.ipynb",
            r"LigandPocketDDPM\.load_from_checkpoint|torch\.load|\.load_state_dict\s*\(",
            ".",
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode not in (0, 1) or completed.stderr != "":
        raise ValueError(_ERROR)
    return sorted(
        line[2:] if line.startswith("./") else line
        for line in completed.stdout.splitlines()
        if line
    )


def _audit_checkpoint_load_sites(repo_root: Path) -> list[dict[str, Any]]:
    raw_records: list[dict[str, Any]] = []
    for relative_path in _candidate_checkpoint_paths(repo_root):
        payload = _read_regular(repo_root / relative_path)
        if relative_path.endswith(".ipynb"):
            notebook = json.loads(payload)
            for cell_index, cell in enumerate(notebook.get("cells", [])):
                if cell.get("cell_type") != "code":
                    continue
                for source_line, text in enumerate(cell.get("source", []), start=1):
                    if "LigandPocketDDPM.load_from_checkpoint(" not in text:
                        continue
                    raw_records.append({
                        "caller_path": relative_path,
                        "source_location": f"cell_{cell_index}_line_{source_line}",
                        "context": "notebook_code_cell",
                        "load_kind": "LigandPocketDDPM.load_from_checkpoint",
                        "current_api": text.strip(),
                    })
            continue
        tree = _parse_ast(payload, relative_path)
        parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            kind = _checkpoint_call_kind(node.func)
            if kind is None:
                continue
            class_name, method = _context_for_call(node, parents)
            context = method if class_name == "<module>" else f"{class_name}.{method}"
            raw_records.append({
                "caller_path": relative_path,
                "source_location": f"line_{node.lineno}",
                "context": context,
                "load_kind": kind,
                "current_api": ast.unparse(node),
            })
    raw_records.sort(key=lambda item: (
        item["caller_path"], item["source_location"], item["current_api"]
    ))
    identities = {
        (record["caller_path"], record["load_kind"], record["context"])
        for record in raw_records
    }
    if identities != _EXPECTED_CHECKPOINT_SITE_IDENTITIES or len(raw_records) != 24:
        raise ValueError(_ERROR)

    records: list[dict[str, Any]] = []
    for raw in raw_records:
        legacy, conditioned, migration, cli = _checkpoint_site_policies(
            raw["caller_path"], raw["load_kind"], raw["current_api"]
        )
        records.append({
            **raw,
            "current_strict_semantics": _checkpoint_strict_semantics(
                raw["load_kind"], raw["current_api"]
            ),
            "legacy_profile": legacy,
            "conditioned_profile": conditioned,
            "future_migration_surface": migration,
            "cli_impact": cli,
            "covered": True,
            "blocking_reason": [],
        })
    return records


def _namespace_value(value: object, name: str) -> object:
    if isinstance(value, Mapping):
        return value.get(name)
    return getattr(value, name, None)


def _inspect_checkpoint(repo_root: Path) -> dict[str, Any]:
    checkpoint_path = repo_root / _CHECKPOINT_PATH
    checkpoint_bytes = _read_regular(checkpoint_path, expected_size=_CHECKPOINT_SIZE)
    if _sha256(checkpoint_bytes) != _CHECKPOINT_SHA256:
        raise ValueError(_ERROR)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        payload = torch.load(checkpoint_path, map_location="cpu")
    if type(payload) is not dict:
        raise ValueError(_ERROR)
    expected_top_level = [
        "epoch", "global_step", "pytorch-lightning_version", "state_dict",
        "loops", "callbacks", "optimizer_states", "lr_schedulers",
        "hparams_name", "hyper_parameters",
    ]
    if list(payload) != expected_top_level:
        raise ValueError(_ERROR)
    state_dict = payload.get("state_dict")
    hparams = payload.get("hyper_parameters")
    if not isinstance(state_dict, Mapping) or type(hparams) is not dict:
        raise ValueError(_ERROR)
    ordered_keys = list(state_dict)
    tensor_manifest: list[dict[str, Any]] = []
    for key, tensor in state_dict.items():
        if type(key) is not str or not isinstance(tensor, torch.Tensor):
            raise ValueError(_ERROR)
        tensor_manifest.append({
            "key": key,
            "shape": list(tensor.shape),
            "dtype": str(tensor.dtype),
        })
    if (
        len(ordered_keys) != 122
        or _sha256(_canonical_json_bytes(ordered_keys))
        != _CHECKPOINT_KEY_MANIFEST_SHA256
        or _sha256(_canonical_json_bytes(tensor_manifest))
        != _CHECKPOINT_SHAPE_MANIFEST_SHA256
    ):
        raise ValueError(_ERROR)
    egnn_params = hparams.get("egnn_params")
    mode = hparams.get("mode")
    pocket_representation = hparams.get("pocket_representation")
    joint_nf = _namespace_value(egnn_params, "joint_nf")
    atom_nf = state_dict["ddpm.dynamics.atom_encoder.0.weight"].shape[1]
    residue_nf = state_dict["ddpm.dynamics.residue_encoder.0.weight"].shape[1]
    egnn_input_nf = state_dict["ddpm.dynamics.egnn.embedding.weight"].shape[1]
    condition_time = egnn_input_nf == joint_nf + 1
    if (
        mode != "pocket_conditioning"
        or pocket_representation != "full-atom"
        or joint_nf != 32
        or atom_nf != 10
        or residue_nf != 10
        or condition_time is not True
        or _NEW_STATE_KEY in state_dict
    ):
        raise ValueError(_ERROR)
    dynamics_keys = [key for key in ordered_keys if key.startswith("ddpm.dynamics.")]
    if len(dynamics_keys) != 120:
        raise ValueError(_ERROR)
    return {
        "checkpoint_top_level_keys": expected_top_level,
        "state_dict_key_count": len(ordered_keys),
        "state_dict_ordered_key_manifest_sha256": _CHECKPOINT_KEY_MANIFEST_SHA256,
        "state_dict_shape_dtype_manifest_sha256": _CHECKPOINT_SHAPE_MANIFEST_SHA256,
        "state_dict_tensor_shape_dtype_manifest": tensor_manifest,
        "hyper_parameters_mode": mode,
        "hyper_parameters_pocket_representation": pocket_representation,
        "joint_nf": joint_nf,
        "atom_nf": atom_nf,
        "residue_nf": residue_nf,
        "condition_time": condition_time,
        "condition_time_evidence": (
            "EGNNDynamics_default_true_and_checkpoint_egnn_input_nf_equals_joint_nf_plus_one"
        ),
        "egnn_input_nf": egnn_input_nf,
        "egnn_dynamics_state_key_prefix": "ddpm.dynamics.",
        "egnn_dynamics_state_key_count": len(dynamics_keys),
        "egnn_dynamics_state_key_prefixes": [
            "ddpm.dynamics.atom_encoder.",
            "ddpm.dynamics.atom_decoder.",
            "ddpm.dynamics.residue_encoder.",
            "ddpm.dynamics.residue_decoder.",
            "ddpm.dynamics.egnn.",
        ],
        "egnn_dynamics_state_keys": dynamics_keys,
        "selected_enabled_parameter_full_state_key": _NEW_STATE_KEY,
        "selected_enabled_parameter_actual_shape_for_checkpoint": [joint_nf],
        "selected_enabled_parameter_present_in_base_checkpoint": False,
    }


def _signature_matrix() -> list[dict[str, Any]]:
    return [
        {
            "source_path": "lightning_modules.py",
            "class": "LigandPocketDDPM",
            "method": "__init__",
            "future_change": f"add_{_ENABLE_FLAG}=False_and_forward_to_EGNNDynamics",
            "validation": "constructor_flag_bool_fail_closed",
        },
        {
            "source_path": "equivariant_diffusion/dynamics.py",
            "class": "EGNNDynamics",
            "method": "__init__",
            "future_change": f"add_{_ENABLE_FLAG}=False_and_create_optional_parameter",
            "validation": "disabled_register_parameter_None_enabled_exact_zero_Parameter_joint_nf",
        },
        {
            "source_path": "equivariant_diffusion/dynamics.py",
            "class": "EGNNDynamics",
            "method": "forward",
            "future_change": f"append_{_FIELD}=None",
            "validation": "lightweight_None_or_bool_1D_length_equals_xh_residues",
        },
        {
            "source_path": "equivariant_diffusion/conditional_model.py",
            "class": "ConditionalDDPM",
            "method": "forward",
            "future_change": f"append_{_FIELD}=None;extract_from_pocket_if_not_explicit",
            "validation": "top_level_full_once_then_main_t_and_eval_t0_explicit_pass",
        },
        {
            "source_path": "equivariant_diffusion/conditional_model.py",
            "class": "ConditionalDDPM",
            "method": "sample_p_zs_given_zt",
            "future_change": f"append_{_FIELD}=None_and_pass_to_dynamics",
            "validation": "already_top_level_validated_static_tensor",
        },
        {
            "source_path": "equivariant_diffusion/conditional_model.py",
            "class": "ConditionalDDPM",
            "method": "sample_p_xh_given_z0",
            "future_change": f"append_{_FIELD}=None_and_pass_to_dynamics",
            "validation": "already_top_level_validated_static_tensor",
        },
        {
            "source_path": "equivariant_diffusion/conditional_model.py",
            "class": "ConditionalDDPM",
            "method": "sample_given_pocket",
            "future_change": f"append_{_FIELD}=None;extract_validate_once_then_thread_each_timestep_and_final",
            "validation": "top_level_full_once",
        },
        {
            "source_path": "equivariant_diffusion/conditional_model.py",
            "class": "ConditionalDDPM",
            "method": "diversify",
            "future_change": f"append_{_FIELD}=None;extract_validate_once_then_thread",
            "validation": "top_level_full_once",
        },
        {
            "source_path": "equivariant_diffusion/conditional_model.py",
            "class": "ConditionalDDPM",
            "method": "inpaint",
            "future_change": f"append_{_FIELD}=None;extract_validate_once_then_thread_each_timestep_and_final",
            "validation": "top_level_full_once",
        },
        {
            "source_path": "equivariant_diffusion/conditional_model.py",
            "class": "SimpleConditionalDDPM",
            "method": "forward",
            "future_change": f"append_{_FIELD}=None_and_forward_explicitly_to_super",
            "validation": "super_top_level_validation_without_silent_drop",
        },
        {
            "source_path": "equivariant_diffusion/conditional_model.py",
            "class": "SimpleConditionalDDPM",
            "method": "sample_given_pocket",
            "future_change": f"append_{_FIELD}=None_and_forward_explicitly_to_super",
            "validation": "super_top_level_validation_without_silent_drop",
        },
        {
            "source_path": "equivariant_diffusion/en_diffusion.py",
            "class": "EnVariationalDiffusion",
            "method": "forward",
            "future_change": f"append_{_FIELD}=None;extract_from_pocket_if_not_explicit",
            "validation": "top_level_full_once_then_main_t_and_eval_t0_explicit_pass",
        },
        {
            "source_path": "equivariant_diffusion/en_diffusion.py",
            "class": "EnVariationalDiffusion",
            "method": "sample_p_zs_given_zt",
            "future_change": f"append_{_FIELD}=None_and_pass_to_dynamics",
            "validation": "already_top_level_validated_static_tensor",
        },
        {
            "source_path": "equivariant_diffusion/en_diffusion.py",
            "class": "EnVariationalDiffusion",
            "method": "sample_p_xh_given_z0",
            "future_change": f"append_{_FIELD}=None_and_pass_to_dynamics",
            "validation": "already_top_level_validated_static_tensor",
        },
        {
            "source_path": "equivariant_diffusion/en_diffusion.py",
            "class": "EnVariationalDiffusion",
            "method": "inpaint",
            "future_change": f"append_{_FIELD}=None;extract_validate_once_then_thread_each_timestep_and_final",
            "validation": "top_level_full_once",
        },
        {
            "source_path": "equivariant_diffusion/en_diffusion.py",
            "class": "EnVariationalDiffusion",
            "method": "sample",
            "future_change": "no_condition_argument_unconditional_joint_generation_has_no_target_identity",
            "validation": "condition_present_profile_unsupported_fail_closed_by_absent_input_surface",
        },
    ]


def _candidate_decisions() -> list[dict[str, Any]]:
    return [
        {
            "candidate": "append_indicator_to_pocket_one_hot",
            "decision": "rejected",
            "reasons": [
                "changes_residue_nf",
                "changes_residue_encoder_input_tensor_shape",
                "changes_existing_checkpoint_weight_shape",
                "misclassifies_static_semantics_as_diffusion_feature",
            ],
        },
        {
            "candidate": "append_indicator_to_time_channel",
            "decision": "rejected",
            "reasons": [
                "changes_EGNN_in_node_nf",
                "changes_first_layer_weight_shape",
                "conflates_time_and_target_semantics",
            ],
        },
        {
            "candidate": "duplicate_target_coordinates_or_add_target_pseudo_node",
            "decision": "rejected",
            "reasons": [
                "changes_node_count",
                "changes_graph_edges",
                "breaks_existing_pocket_node_identity_and_checkpoint_distribution",
            ],
        },
        {
            "candidate": "expand_edge_type_embedding",
            "decision": "deferred",
            "reasons": [
                "requires_edge_embedding_vocabulary_or_shape_change",
                "v1_complexity_too_high",
            ],
        },
        {
            "candidate": "fixed_nonlearnable_hidden_channel_shift",
            "decision": "rejected",
            "reasons": [
                "old_checkpoint_would_immediately_change_condition_present_behavior",
                "lacks_zero_initialized_learnable_gate",
            ],
        },
        {
            "candidate": "multi_layer_condition_encoder",
            "decision": "rejected_for_v1",
            "reasons": [
                "too_many_parameters",
                "checkpoint_migration_surface_too_large",
                "v1_does_not_need_an_MLP",
            ],
        },
        {
            "candidate": "optional_zero_initialized_target_node_embedding_after_residue_encoder",
            "decision": "accepted",
            "reasons": [
                "preserves_atom_residue_and_EGNN_input_widths",
                "adds_exactly_one_optional_joint_nf_parameter",
                "zero_initialization_preserves_initial_output_parity",
                "injects_invariant_scalar_hidden_semantics_before_existing_message_passing",
            ],
        },
    ]


def _constructor_audit() -> list[dict[str, Any]]:
    return [
        {
            "constructed_class": "EGNNDynamics",
            "source_path": "lightning_modules.py",
            "source_line": 393,
            "construction_form": "direct_EGNNDynamics_call_in_LigandPocketDDPM.__init__",
            "future_flag_source": f"LigandPocketDDPM.{_ENABLE_FLAG}_default_false",
            "covered": True,
        },
        {
            "constructed_class": "EnVariationalDiffusion",
            "source_path": "lightning_modules.py",
            "source_line": 315,
            "construction_form": "ddpm_models_mode_joint_dispatch_at_line_417",
            "covered": True,
        },
        {
            "constructed_class": "ConditionalDDPM",
            "source_path": "lightning_modules.py",
            "source_line": 316,
            "construction_form": "ddpm_models_mode_pocket_conditioning_dispatch_at_line_417",
            "covered": True,
        },
        {
            "constructed_class": "SimpleConditionalDDPM",
            "source_path": "lightning_modules.py",
            "source_line": 317,
            "construction_form": "ddpm_models_mode_pocket_conditioning_simple_dispatch_at_line_417",
            "covered": True,
        },
    ]


def _git_commit_is_ancestor(
    *,
    repo_root: Path,
    base_commit: str,
    head_ref: str,
) -> bool:
    """Return whether ``base_commit`` is an ancestor of ``head_ref``."""

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
            raise ValueError(_ERROR)
        completed = subprocess.run(
            ["git", "merge-base", "--is-ancestor", base_commit, head_ref],
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
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _validate_formal_gate(source_bundle: bytes, repo_root: Path) -> dict[str, Any]:
    if _sha256(source_bundle) != _GATE_BUNDLE_TRANSPORT_SHA256:
        raise ValueError(_ERROR)
    decoded = gate._strict_json(source_bundle)
    if gate._canonical_json_bytes(decoded) != source_bundle:
        raise ValueError(_ERROR)
    gate._validate_bundle(decoded, require_field_order=False)
    projection = gate._current11_runtime_bridge_gate_record_lineage_projection(
        decoded["current11_records"]
    )
    if (
        decoded["runtime_bridge_gate_bundle_sha256"]
        != _GATE_BUNDLE_INTERNAL_SHA256
        or _sha256(gate._canonical_json_bytes(projection))
        != _CURRENT11_LINEAGE_PROJECTION_SHA256
        or decoded["current11_record_count"] != 11
        or decoded["total_runtime_pocket_node_count"] != 2202
        or decoded["total_runtime_indicator_true_count"] != 11
        or decoded["ready_for_model_consumption_design"] is not True
        or decoded["recommended_next_step"]
        != "design_covapie_target_residue_atom_condition_model_consumption_v1"
        or decoded["repository_cli_selector_forwarding_implemented"] is not False
        or decoded["indicator_consumed_by_model"] is not False
        or decoded["indicator_passed_into_dynamics"] is not False
        or decoded["feature_semantics_audit_required_before_training"] is not True
    ):
        raise ValueError(_ERROR)

    gate_source = _read_regular(repo_root / _GATE_PRODUCTION_PATH)
    if (
        _sha256(gate_source) != _GATE_PRODUCTION_SHA256
        or _git(repo_root, "show", f"{_GATE_COMMIT}:{_GATE_PRODUCTION_PATH}")
        != gate_source
        or _git(repo_root, "show", "-s", "--format=%P", _GATE_COMMIT).strip().decode()
        != _GATE_PARENT
        or not _git_commit_is_ancestor(
            repo_root=repo_root,
            base_commit=_GATE_COMMIT,
            head_ref="HEAD",
        )
        or not _git_commit_is_ancestor(
            repo_root=repo_root,
            base_commit=_GATE_COMMIT,
            head_ref="origin/main",
        )
    ):
        raise ValueError(_ERROR)
    return decoded


def _validate_sources(repo_root: Path) -> dict[str, str]:
    actual: dict[str, str] = {}
    for relative_path, expected in _SOURCE_SHA256.items():
        payload = _read_regular(repo_root / relative_path)
        if (
            _sha256(payload) != expected
            or _git(repo_root, "show", f"{_GATE_COMMIT}:{relative_path}") != payload
        ):
            raise ValueError(_ERROR)
        actual[relative_path] = expected
    lightning = _read_regular(repo_root / "lightning_modules.py").decode("utf-8")
    required_constructor_fragments = (
        "net_dynamics = EGNNDynamics(",
        "'joint': EnVariationalDiffusion",
        "'pocket_conditioning': ConditionalDDPM",
        "'pocket_conditioning_simple': SimpleConditionalDDPM",
        "self.ddpm = ddpm_models[self.mode](",
    )
    if any(fragment not in lightning for fragment in required_constructor_fragments):
        raise ValueError(_ERROR)
    return actual


def _contains_path(value: object) -> bool:
    if isinstance(value, Path):
        return True
    if isinstance(value, Mapping):
        return any(_contains_path(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_path(item) for item in value)
    return False


def design_covapie_target_residue_atom_condition_model_consumption_v1(
    *,
    source_runtime_bridge_gate_bundle: bytes,
    repo_root: Path,
) -> dict[str, Any]:
    """Return the deterministic Exact47 model-consumption design contract."""

    try:
        if type(source_runtime_bridge_gate_bundle) is not bytes or not isinstance(
            repo_root, Path
        ):
            raise ValueError(_ERROR)
        _validate_formal_gate(source_runtime_bridge_gate_bundle, repo_root)
        source_hashes = _validate_sources(repo_root)
        dynamics_records = _audit_dynamics_call_sites(repo_root)
        checkpoint_records = _audit_checkpoint_load_sites(repo_root)
        checkpoint_profile = _inspect_checkpoint(repo_root)
        signatures = _signature_matrix()

        conditional_training = {
            "entry": "ConditionalDDPM.forward",
            "top_level_validation_once": True,
            "main_t_dynamics_site": "equivariant_diffusion/conditional_model.py:253",
            "same_static_indicator_each_internal_call": True,
            "covered": any(
                record["class"] == "ConditionalDDPM"
                and record["method"] == "forward"
                and record["source_line"] == 253
                for record in dynamics_records
            ),
        }
        conditional_eval = {
            "entry": "ConditionalDDPM.forward",
            "top_level_validation_once": True,
            "main_t_dynamics_site": "equivariant_diffusion/conditional_model.py:253",
            "t0_dynamics_site": "equivariant_diffusion/conditional_model.py:306",
            "same_static_indicator_for_both_predictions": True,
            "covered": all(
                any(
                    record["class"] == "ConditionalDDPM"
                    and record["method"] == "forward"
                    and record["source_line"] == line
                    for record in dynamics_records
                )
                for line in (253, 306)
            ),
        }
        conditional_sampling = {
            "entries": [
                "ConditionalDDPM.sample_given_pocket",
                "ConditionalDDPM.diversify",
                "ConditionalDDPM.inpaint",
            ],
            "top_level_validation_once_per_entry": True,
            "iterative_dynamics_site": "equivariant_diffusion/conditional_model.py:445",
            "final_t0_dynamics_site": "equivariant_diffusion/conditional_model.py:119",
            "same_static_indicator_reused_every_denoising_timestep": True,
            "covered": all(
                any(
                    record["class"] == "ConditionalDDPM"
                    and record["source_line"] == line
                    for record in dynamics_records
                )
                for line in (119, 445)
            ),
        }
        joint_training = {
            "entry": "EnVariationalDiffusion.forward",
            "top_level_validation_once": True,
            "main_t_dynamics_site": "equivariant_diffusion/en_diffusion.py:378",
            "eval_t0_dynamics_site": "equivariant_diffusion/en_diffusion.py:436",
            "pocket_coordinates_may_follow_existing_joint_policy": True,
            "condition_has_no_direct_coordinate_injection": True,
            "covered": all(
                any(
                    record["class"] == "EnVariationalDiffusion"
                    and record["source_line"] == line
                    for record in dynamics_records
                )
                for line in (378, 436)
            ),
        }
        inpainting = {
            "entries": [
                "ConditionalDDPM.inpaint",
                "EnVariationalDiffusion.inpaint",
            ],
            "top_level_validation_once_per_entry": True,
            "conditional_iterative_and_final_sites": [
                "equivariant_diffusion/conditional_model.py:445",
                "equivariant_diffusion/conditional_model.py:119",
            ],
            "joint_iterative_and_final_sites": [
                "equivariant_diffusion/en_diffusion.py:516",
                "equivariant_diffusion/en_diffusion.py:270",
            ],
            "same_static_indicator_reused_during_resampling": True,
            "covered": all(
                any(record["source_line"] == line for record in dynamics_records)
                for line in (119, 270, 445, 516)
            ),
        }
        simple_conditional = {
            "forward_override": (
                f"must_add_and_explicitly_forward_{_FIELD}_to_ConditionalDDPM.forward"
            ),
            "sample_given_pocket_override": (
                f"must_add_and_explicitly_forward_{_FIELD}_to_ConditionalDDPM.sample_given_pocket"
            ),
            "inpaint": "inherits_ConditionalDDPM.inpaint_and_uses_same_top_level_contract",
            "generate_ligands_exact_type_branch": (
                "current_profile_unsupported_and_fail_closed_with_NotImplementedError;"
                "condition_is_not_silently_dropped"
            ),
            "covered": all(
                any(
                    item["class"] == "SimpleConditionalDDPM"
                    and item["method"] == method
                    for item in signatures
                )
                for method in ("forward", "sample_given_pocket")
            ),
        }

        unresolved: list[str] = []
        if not all(record["covered"] for record in dynamics_records):
            unresolved.append("dynamics_call_site_not_covered")
        if not all(record["covered"] for record in checkpoint_records):
            unresolved.append("checkpoint_load_site_not_covered")
        path_contracts = (
            conditional_training,
            conditional_eval,
            conditional_sampling,
            joint_training,
            inpainting,
            simple_conditional,
        )
        if not all(contract["covered"] for contract in path_contracts):
            unresolved.append("model_consumption_path_not_covered")
        ready = not unresolved
        recommended = (
            "implement_covapie_target_residue_atom_condition_model_consumption_v1"
            if ready
            else "resolve_covapie_target_residue_atom_condition_model_consumption_blockers_v1"
        )

        response: dict[str, Any] = {
            "model_consumption_design_version": _VERSION,
            "source_runtime_bridge_gate_bundle_transport_sha256": _GATE_BUNDLE_TRANSPORT_SHA256,
            "source_runtime_bridge_gate_bundle_sha256": _GATE_BUNDLE_INTERNAL_SHA256,
            "source_runtime_bridge_gate_production_sha256": _GATE_PRODUCTION_SHA256,
            "source_runtime_bridge_gate_commit": _GATE_COMMIT,
            "source_lightning_module_sha256": source_hashes["lightning_modules.py"],
            "source_conditional_model_sha256": source_hashes["equivariant_diffusion/conditional_model.py"],
            "source_en_diffusion_sha256": source_hashes["equivariant_diffusion/en_diffusion.py"],
            "source_dynamics_sha256": source_hashes["equivariant_diffusion/dynamics.py"],
            "source_egnn_sha256": source_hashes["equivariant_diffusion/egnn_new.py"],
            "source_checkpoint_sha256": _CHECKPOINT_SHA256,
            "source_checkpoint_size": _CHECKPOINT_SIZE,
            "checkpoint_profile": checkpoint_profile,
            "audited_dynamics_call_site_records": dynamics_records,
            "audited_checkpoint_load_site_records": checkpoint_records,
            "selected_condition_field_name": _FIELD,
            "selected_enable_flag_name": _ENABLE_FLAG,
            "selected_dynamics_argument_name": _FIELD,
            "selected_injection_module": "EGNNDynamics",
            "selected_injection_point": _INJECTION_POINT,
            "selected_condition_representation": "same_name_per_pocket_node_bool_sidecar",
            "selected_parameter_name": _PARAMETER,
            "selected_parameter_shape": ["joint_nf"],
            "selected_parameter_initialization": "all_zeros",
            "selected_parameter_creation_policy": {
                "flag_default": False,
                "disabled": f"register_parameter_{_PARAMETER}_None",
                "enabled": "create_exactly_one_Parameter_shape_joint_nf_initialized_all_zeros",
                "dtype": "follows_module_parameter_dtype",
                "additional_parameters": [],
                "buffers_added": [],
            },
            "legacy_disabled_state_dict_policy": {
                "enable_flag": False,
                "new_parameter_key_present": False,
                "existing_key_set_unchanged": True,
                "existing_tensor_shapes_unchanged": True,
                "legacy_strict_load": True,
                "missing_keys": [],
                "unexpected_keys": [],
            },
            "base_to_conditioned_checkpoint_migration_policy": {
                "enable_flag": True,
                "new_full_state_key": _NEW_STATE_KEY,
                "read_old_checkpoint_into_memory_copy": True,
                "construct_conditioned_model": True,
                "shared_key_set_and_shape_comparison_required": True,
                "allowed_missing_keys_before_fill": [_NEW_STATE_KEY],
                "allowed_unexpected_keys": [],
                "fill_from_current_model_zero_initialized_tensor": True,
                "final_load_state_dict_strict": True,
                "final_missing_keys": [],
                "final_unexpected_keys": [],
                "blanket_strict_false": False,
                "automatic_reshape": False,
                "disk_checkpoint_modified": False,
            },
            "conditioned_checkpoint_strict_load_policy": {
                "enable_flag": True,
                "new_full_state_key_required": _NEW_STATE_KEY,
                "strict_load": True,
                "fallback_to_nonstrict": False,
            },
            "condition_presence_semantics": {
                "validation_boundary": "top_level_validate_once_then_thread_static_tensor",
                "top_level_entries": [
                    "ConditionalDDPM.forward",
                    "ConditionalDDPM.sample_given_pocket",
                    "ConditionalDDPM.diversify",
                    "ConditionalDDPM.inpaint",
                    "SimpleConditionalDDPM.forward",
                    "SimpleConditionalDDPM.sample_given_pocket",
                    "EnVariationalDiffusion.forward",
                    "EnVariationalDiffusion.inpaint",
                ],
                "top_level_validation": [
                    "tensor", "torch.bool", "one_dimensional", "node_aligned",
                    "safe_device_transfer", "exactly_one_true_per_sample",
                ],
                "dynamics_defensive_validation": [
                    "None_or_tensor", "torch.bool", "one_dimensional",
                    "length_equals_len_xh_residues",
                ],
                "legacy_absent": {
                    "sidecar_key": "absent",
                    "allowed_enable_flags": [False, True],
                    "embedding_added": False,
                    "legacy_output_preserved": True,
                },
                "covalent_present": {
                    "sidecar_key": "present",
                    "dtype": "torch.bool",
                    "ndim": 1,
                    "length": "len_pocket_nodes",
                    "true_count_per_sample": 1,
                    "required_enable_flag": True,
                    "flag_false_fail_closed": True,
                },
                "present_all_false": {
                    "accepted": False,
                    "present_all_false_semantics_deferred": True,
                },
            },
            "mixed_batch_semantics": {
                "mixed_covalent_noncovalent_same_batch_supported": False,
                "mixed_noncovalent_zero_target_semantics_deferred": True,
                "reason": "no_formal_per_sample_condition_presence_mask",
                "pure_covalent_batch_supported": True,
                "separate_legacy_batch_supported": True,
            },
            "normalization_and_noise_policy": {
                "static_discrete_semantics": True,
                "indicator_normalized": False,
                "indicator_noised": False,
                "indicator_centered": False,
                "indicator_rotated": False,
                "indicator_decoded": False,
                "indicator_added_to_xh_pocket": False,
                "indicator_contributes_to_reconstruction_loss": False,
                "normalize_dictionary_may_preserve_sidecar_unchanged": True,
                "same_static_tensor_reused_each_denoising_timestep": True,
            },
            "equivariance_contract": {
                "indicator_semantics": "rotation_translation_invariant_scalar_label",
                "injection_target": "hidden_scalar_features_only",
                "coordinate_injection": False,
                "distance_change": False,
                "edge_construction_change": False,
                "coordinate_update_mask_change": False,
                "translation_equivariance_preserved": True,
                "rotation_equivariance_preserved": True,
                "reflection_policy": "unchanged_from_original_model",
                "node_permutation_equivariance_preserved": True,
                "oracles": [
                    "translation_does_not_change_condition_embedding",
                    "rotation_does_not_change_condition_embedding",
                    "consistent_pocket_node_mask_indicator_permutation_moves_target_embedding_row",
                    "indicator_not_concatenated_into_direct_coordinate_input",
                ],
            },
            "conditional_training_path_contract": conditional_training,
            "conditional_eval_path_contract": conditional_eval,
            "conditional_sampling_path_contract": conditional_sampling,
            "joint_training_path_contract": joint_training,
            "inpainting_path_contract": inpainting,
            "simple_conditional_path_contract": simple_conditional,
            "candidate_decisions": _candidate_decisions(),
            "existing_state_dict_compatibility_decision": {
                "existing_state_dict_keys_unchanged_when_disabled": True,
                "existing_tensor_shapes_unchanged_in_all_profiles": True,
                "enabled_exactly_one_new_key": _NEW_STATE_KEY,
                "enabled_exactly_one_new_parameter_count": checkpoint_profile["joint_nf"],
                "atom_nf_changed": False,
                "residue_nf_changed": False,
                "joint_nf_changed": False,
                "EGNN_in_node_nf_changed": False,
                "checkpoint_compatible": True,
            },
            "canonical_mask_semantic_names": list(CANONICAL_MASK_SEMANTIC_NAMES),
            "implementation_scope": {
                "model_consumption_designed": True,
                "model_consumption_implemented": False,
                "model_modified": False,
                "forward_modified": False,
                "loss_modified": False,
                "new_model_parameter_created": False,
                "indicator_consumed_by_model": False,
                "indicator_passed_into_dynamics": False,
                "training_or_parameter_update": False,
                "global_mutable_state_used": False,
                "future_primary_modified_files": [
                    "lightning_modules.py",
                    "equivariant_diffusion/dynamics.py",
                    "equivariant_diffusion/conditional_model.py",
                    "equivariant_diffusion/en_diffusion.py",
                ],
                "egnn_new_expected_unchanged": True,
                "dataset_and_collate_unchanged": True,
                "runtime_bridge_gate_and_formal_bundles_unchanged": True,
                "checkpoint_files_unchanged": True,
                "repository_cli_selector_forwarding_in_scope": False,
                "constructor_site_records": _constructor_audit(),
                "future_signature_change_matrix": signatures,
                "forbidden_threading_mechanisms": [
                    "global_variable", "module_mutable_current_mask_state",
                    "hook_side_channel", "thread_local_state", "singleton",
                    "kwargs_only_indicator_transport",
                ],
                "semantic_injection_pseudocode": (
                    "h_residues=residue_encoder(h_residues);"
                    "h_residues+=indicator.to(h_residues)*target_residue_atom_condition_embedding"
                ),
                "target_pocket_node_only_at_injection": True,
                "non_target_pocket_rows_unchanged_at_injection": True,
                "ligand_rows_not_directly_injected": True,
                "information_propagates_via_existing_EGNN_messages": True,
            },
            "unresolved_blockers": unresolved,
            "ready_for_model_consumption_implementation": ready,
            "recommended_next_step": recommended,
            "feature_semantics_audit_required_before_training": True,
            "model_consumption_design_response_sha256": "",
        }
        if tuple(response) != MODEL_CONSUMPTION_DESIGN_RESPONSE_FIELDS:
            raise ValueError(_ERROR)
        response["model_consumption_design_response_sha256"] = _response_digest(response)
        if _contains_path(response):
            raise ValueError(_ERROR)
        return response
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
