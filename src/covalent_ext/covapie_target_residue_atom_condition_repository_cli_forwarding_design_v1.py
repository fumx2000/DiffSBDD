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
        caller_payloads[relative_path] = _regular_file_bytes(
            repo_root, relative_path, expected_sha256=expected_sha256
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
    lightning_payload = _regular_file_bytes(
        repo_root, "lightning_modules.py", expected_sha256=_LIGHTNING_SHA256
    )
    _regular_file_bytes(
        repo_root,
        "src/covalent_ext/covapie_target_residue_atom_condition_checkpoint_migration_v1.py",
        expected_sha256=_MIGRATION_SHA256,
    )
    masking_payload = _regular_file_bytes(
        repo_root,
        "src/covalent_ext/masking.py",
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
    return {
        "incremental_commits_required": True,
        "ordered_steps": [
            {
                "step": "R1",
                "phase": "legacy_four_level_mask_retirement",
                "objective": "remove_legacy_four_level_core_runtime_interfaces",
                "paths": [
                    "src/covalent_ext/masking.py",
                    "src/covalent_ext/schema.py",
                    "src/covalent_ext/dataset.py",
                    "scripts/check_covalent_masking.py",
                    "tests/test_covalent_masking.py",
                    "tests/test_b3_scaffold_only_mask_implementation_v0.py",
                ],
                "completion_contract": {
                    "legacy_four_level_core_api_retired": True,
                    "legacy_four_level_full_runtime_retired": False,
                    "reason_full_runtime_not_retired": (
                        "covalent_inpaint_demo_remains_for_R2"
                    ),
                },
            },
            {
                "step": "R2",
                "phase": "legacy_four_level_mask_retirement",
                "objective": (
                    "remove_final_active_cli_caller_dependency_on_legacy_four_level_masks"
                ),
                "paths": [
                    "scripts/covalent_inpaint_demo.py",
                    "tests/test_covalent_inpaint_demo_mask_semantic_v1.py",
                ],
                "completion_contract": {
                    "legacy_mask_flag_removed": "--mask_level",
                    "only_canonical_mask_flag_added": "--mask_semantic",
                    "accepted_runtime_mask_inputs": list(
                        CANONICAL_MASK_SEMANTIC_NAMES
                    ),
                    "short_alias_runtime_inputs_rejected": list(
                        _LEGACY_SHORT_TOKENS
                    ),
                    "runtime_builder": "build_long_form_mask",
                    "candidate_full_runtime_retirement_requires_R3_gate": True,
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
        ],
        "single_commit_for_all_increments_allowed": False,
        "cli_forwarding_may_begin_before_R3": False,
    }


def _legacy_mask_reference_inventory(repo_root: Path) -> dict[str, Any]:
    tracked = set(_git(repo_root, "ls-files").splitlines())
    ordinary_untracked = set(
        _git(repo_root, "ls-files", "--others", "--exclude-standard").splitlines()
    )
    if ordinary_untracked != set(_DESIGN_PATHS):
        raise ValueError(_ERROR)
    repository_paths = sorted(tracked | ordinary_untracked)
    grep_pattern = (
        "build_four_level_mask|MASK_BUILDERS|MaskType|mask_warhead|"
        "mask_linker_and_warhead|mask_scaffold|mask_whole_ligand|"
        "--mask_level|choices"
    )
    tracked_candidates = set(
        _git(repo_root, "grep", "-l", "-I", "-E", grep_pattern, "--").splitlines()
    )
    candidate_paths = sorted(tracked_candidates | ordinary_untracked)
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
        path = repo_root / relative_path
        if path.suffix.lower() not in allowed_suffixes:
            continue
        metadata = path.lstat()
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_size >= _MAX_SOURCE_BYTES
        ):
            raise ValueError(_ERROR)
        try:
            text = path.read_text(encoding="utf-8")
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
            if active or test_only:
                retirement_increment = (
                    "R2"
                    if relative_path == "scripts/covalent_inpaint_demo.py"
                    else "R1"
                )
                post_increment_expected_status = (
                    "final_active_cli_dependency_removed_pending_R3_gate"
                    if retirement_increment == "R2"
                    else "core_legacy_dependency_removed_full_retirement_still_false"
                )
            else:
                retirement_increment = None
                post_increment_expected_status = (
                    "retained_read_only_non_active_legacy_evidence"
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
        "inventory_version": "covapie_legacy_four_level_mask_reference_inventory_v1",
        "scanned_repository_file_count": len(repository_paths),
        "scanned_text_file_count": scanned_text_file_count,
        "notebook_json_file_count": notebook_count,
        "notebook_json_cell_source_audited": True,
        "searched_symbols_and_tokens": [
            *_LEGACY_MASK_SYMBOLS,
            "choices_A_B_B2_C",
        ],
        "reference_count": len(inventory),
        "classification_counts": classifications,
        "active_legacy_reference_count": len(active_records),
        "active_legacy_reference_paths": sorted(
            {item["path"] for item in active_records}
        ),
        "active_legacy_reference_path_count": len(
            {item["path"] for item in active_records}
        ),
        "current_active_reference_count": len(active_records),
        "current_active_reference_path_count": len(
            {item["path"] for item in active_records}
        ),
        "target_active_reference_count": 0,
        "target_active_reference_path_count": 0,
        "records": inventory,
        "unresolved_legacy_mask_references": unresolved,
        "unresolved_active_reference_count": len(unresolved),
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


def _ready_for_legacy_four_level_mask_retirement_implementation(
    inventory: Mapping[str, Any],
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
        and inventory.get("unresolved_active_reference_count") == 0
        and inventory.get("current_active_reference_count") == 14
        and inventory.get("current_active_reference_path_count") == 5
        and len(active_records) == 14
        and all(
            item.get("retirement_increment") in {"R1", "R2"}
            and item.get("required_future_action")
            != "UNRESOLVED_ACTIVE_LEGACY_REFERENCE"
            for item in active_records
        )
        and canonical_five_level_contract_complete is True
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
        caller_audit = _caller_audit(repo_root)
        model_source_evidence = _model_and_mask_source_audit(repo_root)
        legacy_mask_inventory = _legacy_mask_reference_inventory(repo_root)
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
            "task": "protein_known_ligand_and_cys_sg_local_generation",
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
            "canonical_input_flag": "--mask_semantic",
            "legacy_input_flag": None,
            "canonical_five_level_target_selected": True,
            "canonical_five_level_contract_complete": True,
            "legacy_four_level_retirement_selected": True,
            "legacy_four_level_retirement_implemented": False,
            "retirement_R3_gate_passed": False,
            "retirement_R3_gate_committed": False,
            "current_legacy_four_level_runtime_present": True,
            "current_legacy_four_level_cli_input_present": True,
            "current_legacy_four_level_schema_present": True,
            "current_active_legacy_reference_count": legacy_mask_inventory[
                "current_active_reference_count"
            ],
            "current_active_legacy_reference_path_count": legacy_mask_inventory[
                "current_active_reference_path_count"
            ],
            "target_active_legacy_reference_count": 0,
            "target_active_legacy_reference_path_count": 0,
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
        retirement_implementation_ready = (
            _ready_for_legacy_four_level_mask_retirement_implementation(
                legacy_mask_inventory,
                canonical_five_level_contract_complete=mask_contract[
                    "canonical_five_level_contract_complete"
                ],
            )
        )
        mask_contract[
            "ready_for_legacy_four_level_mask_retirement_implementation"
        ] = retirement_implementation_ready
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
                mask_contract["current_active_legacy_reference_count"] == 14,
                mask_contract["current_active_legacy_reference_path_count"] == 5,
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
                retirement_implementation_ready,
                mask_contract["canonical_B2_semantic"]
                == "scaffold_plus_warhead",
                mask_contract["canonical_B3_semantic"] == "scaffold_only",
                "scaffold_only" in CANONICAL_MASK_SEMANTIC_NAMES,
                mask_contract["sixth_mask_added"] is False,
                failure_contract["fail_closed"] is True,
            )
        )
        retirement_implemented = (
            legacy_mask_inventory["current_active_reference_count"] == 0
            and legacy_mask_inventory["current_active_reference_path_count"] == 0
            and legacy_mask_inventory["unresolved_active_reference_count"] == 0
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
            "recommended_next_step": "implement_covapie_legacy_four_level_mask_retirement_v1",
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
