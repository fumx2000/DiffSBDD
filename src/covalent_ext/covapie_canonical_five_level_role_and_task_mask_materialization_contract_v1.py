"""Resolve the canonical CovaPIE role/task-mask materialization contract V1.

This gate is metadata-only.  It reads immutable Git blobs and the nine-file
untracked candidate, but it does not import Torch, execute a provider, read a
checkpoint or tensor archive, write a file, or touch a runtime training path.
Every invalid or ambiguous state fails with one stable error contract.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import os
import re
import stat
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence


__all__ = (
    "evaluate_covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1",
)


_ERROR = "COVAPIE_CANONICAL_FIVE_LEVEL_ROLE_AND_TASK_MASK_MATERIALIZATION_CONTRACT_INVALID"
_VERSION = "covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1"
_REPOSITORY = "fumx2000/DiffSBDD"
_REMOTE = "git@github.com:fumx2000/DiffSBDD.git"
_BRANCH = "main"
_BASE = "540be2e4162b2b6a7f1090d41f852e5ac87be459"
_BASE_SUBJECT = "add CovaPIE five-module training-path completion gap audit v1"
_CONTRACT_COMMIT_SUBJECT = (
    "add CovaPIE canonical five-level role and task mask materialization contract v1"
)
_RECOMMENDED_NEXT_INCREMENT = "resolve_covapie_role_annotation_input_authority_gaps_v1"

_TENSOR_COMMIT = "335a0320e8bd8ee125e51f927e6cd26d0c05707e"
_FEATURE_COMMIT = "160cdbda8800a535b5c0a81d501babfae9a8615b"
_CURRENT11_COMMIT = "1cdbca345483022ece967b24de37013b77349cd4"
_ROLE_COMMIT = "0fda7b9e8fc56941e005f3e8b5e67fa2ceaa4ca1"
_R1_COMMIT = "963562e2da9bcc14d67d075a49a7770aecaa2e68"
_R2_COMMIT = "8711c1899759ca4c1f4a24f7ff9782b81a257245"
_R3_COMMIT = "5974ded1dc1aa02a365a23e4a409b9a7fe98a4be"

_EVIDENCE_SUBJECTS = {
    _BASE: _BASE_SUBJECT,
    _TENSOR_COMMIT: "add CovaPIE tensor label and loss-mask contract v1",
    _FEATURE_COMMIT: "add CovaPIE training unknown-atom policy resolution v1",
    _CURRENT11_COMMIT: "add CovaPIE Current11 five auxiliary module label readiness design v1",
    _ROLE_COMMIT: "add CovaPIE ligand role and minimal seed annotation contract v1",
    _R1_COMMIT: "migrate CovaPIE covalent demo to canonical five-level masks R1",
    _R2_COMMIT: "retire CovaPIE legacy four-level core mask API and consumers R2 v1",
    _R3_COMMIT: "add CovaPIE legacy four-level mask retirement gate v1",
}

_DATA_ROOT = (
    "data/derived/covalent_small/"
    "covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1"
)
_SOURCE_INVENTORY_PATH = f"{_DATA_ROOT}/covapie_role_task_mask_source_inventory.csv"
_TASK_TABLE_PATH = f"{_DATA_ROOT}/covapie_canonical_task_truth_table.csv"
_FIELD_REGISTRY_PATH = f"{_DATA_ROOT}/covapie_role_task_mask_field_contract_registry.csv"
_FAILURE_MATRIX_PATH = f"{_DATA_ROOT}/covapie_role_task_mask_failure_matrix.csv"
_MANIFEST_PATH = f"{_DATA_ROOT}/covapie_role_task_mask_contract_manifest.json"

_CANDIDATE_PATHS = tuple(sorted((
    _SOURCE_INVENTORY_PATH,
    _TASK_TABLE_PATH,
    _FIELD_REGISTRY_PATH,
    _FAILURE_MATRIX_PATH,
    _MANIFEST_PATH,
    "docs/covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1_guide.md",
    "scripts/check_covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1.py",
    "src/covalent_ext/covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1.py",
    "tests/test_covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1.py",
)))

_GENERATED_EVIDENCE_PATHS = (
    _SOURCE_INVENTORY_PATH,
    _TASK_TABLE_PATH,
    _FIELD_REGISTRY_PATH,
    _FAILURE_MATRIX_PATH,
    _MANIFEST_PATH,
)

_FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip",
    ".tgz", ".npz", ".tmp", ".part", ".pdb", ".sdf",
)

_EVIDENCE_SPECS = (
    ("E01", _BASE, "src/covalent_ext/covapie_five_module_training_path_completion_gap_audit_v1.py", "2bbcc9b48c5ccd65c1e0b897c71f8bc3f571d2fbd22665542c4956949acd1f39", "current_gap_audit_source"),
    ("E02", _BASE, "scripts/check_covapie_five_module_training_path_completion_gap_audit_v1.py", "d715c444bb85f6b02e626f237f5d940c120f6f2b510078e41ef7ed3880280282", "current_gap_audit_checker"),
    ("E03", _BASE, "tests/test_covapie_five_module_training_path_completion_gap_audit_v1.py", "bb0aa0838bea1f9dc72fcb401221b5cdc12582bbcc4e84cd3ce2fb57ea6693f0", "current_gap_audit_tests"),
    ("E04", _BASE, "docs/covapie_five_module_training_path_completion_gap_audit_v1_guide.md", "d8ddbe610bcad82d076bc1f83e16cff016d399567083e59aae9726217a517a7b", "current_gap_audit_guide"),
    ("E05", _TENSOR_COMMIT, "src/covalent_ext/covapie_tensor_label_and_loss_mask_contract_design_v1.py", "3d2d03cda56dfb4a54370444f255f9bb0ab433aaeb837901e769098272ff51ac", "tensor_contract_source"),
    ("E06", _TENSOR_COMMIT, "data/derived/covalent_small/covapie_tensor_label_and_loss_mask_contract_design_v1/covapie_tensor_label_loss_mask_contract_registry.csv", "dde4a96d1b38f1aa095fb8285616ff2877f91b2274be8bbf7a2e53e1250ec933", "tensor_contract_registry"),
    ("E07", _TENSOR_COMMIT, "data/derived/covalent_small/covapie_tensor_label_and_loss_mask_contract_design_v1/covapie_tensor_label_loss_mask_issue_readiness_inventory.csv", "5a9dfcf4e9ebeba82adda99e72f956f16420424169ffbc8f6c3e85834e6ceaf8", "tensor_issue_inventory"),
    ("E08", _TENSOR_COMMIT, "data/derived/covalent_small/covapie_tensor_label_and_loss_mask_contract_design_v1/covapie_tensor_label_loss_mask_failure_matrix.csv", "1c400aa13904f63f07de087d6c7efe048daa39fe47ae8649e3f0eb4ebd8b5e9f", "tensor_failure_matrix"),
    ("E09", _TENSOR_COMMIT, "data/derived/covalent_small/covapie_tensor_label_and_loss_mask_contract_design_v1/covapie_tensor_label_and_loss_mask_contract_design_manifest.json", "c0611d39074321744156c7ac3a527c54d4a84bd76c798a74fdbc1260b1bc6bcc", "tensor_contract_manifest"),
    ("E10", _FEATURE_COMMIT, "src/covalent_ext/covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1.py", "1d80862e7c4fa3215ac3f307a45ce3bc8f1e0d4613728133a0ea3118df2df241", "feature_resolution_source"),
    ("E11", _FEATURE_COMMIT, "data/derived/covalent_small/covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1/covapie_training_feature_semantics_and_unknown_atom_policy_resolution_manifest.json", "24cb60ca4f080a72e8c60aef63d105d82ec2f432eecc9b90f3341f52576bb6e0", "feature_resolution_manifest"),
    ("E12", _CURRENT11_COMMIT, "src/covalent_ext/covapie_current11_five_auxiliary_module_label_consumption_readiness_design_v1.py", "6e4b2b26545c039e61acc3821deaee86859eff0ed44b5deaca4290f187ee7681", "current11_readiness_source"),
    ("E13", _CURRENT11_COMMIT, "docs/covapie_current11_five_auxiliary_module_label_consumption_readiness_design_v1_guide.md", "7a91a7f8a3d981c60eb684248e01f9eab65f43b28c5c5bee015699de9697daea", "current11_readiness_guide"),
    ("E14", _BASE, "src/covalent_ext/masking.py", "a11ac211cedf14168c2866be960aa99703082b207234b016db0b8929c895c3c6", "canonical_mask_runtime"),
    ("E15", _BASE, "src/covalent_ext/schema.py", "06f8d3fb6cc402ffdd03660c31fe849e8718b7ba3960b50584fb87a0941de64a", "canonical_mask_schema"),
    ("E16", _BASE, "src/covalent_ext/dataset.py", "44605b78b428156f11b398307299506ddc899269d355de78cce3853d78f74a2c", "canonical_dataset"),
    ("E17", _BASE, "scripts/covalent_inpaint_demo.py", "4df839da22e77ada99ab05e6d3e7e5ed41bd480618f0cb01163b5ca52f58c5b9", "canonical_demo"),
    ("E18", _ROLE_COMMIT, "data/derived/covalent_small/covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1/covapie_ligand_role_and_minimal_seed_annotation_contract_design_manifest.json", "cf79865f91ef140b6c69010ce2e56c2ff24937a5aa7fa3eac0f8c53bc907764a", "role_seed_contract_manifest"),
    ("E19", _ROLE_COMMIT, "data/derived/covalent_small/covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1/covapie_current11_role_annotation_input_readiness_matrix.csv", "6def11ca3c1ec974479c3fa96d3f2c985b994eed86d6132008236fb18bca3d4b", "current11_role_seed_readiness"),
    ("E20", _ROLE_COMMIT, "data/derived/covalent_small/covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1/covapie_ligand_role_and_seed_contract_registry.csv", "872ecd0754ff941bee207161a54eecd1dd256d382044c38075b1c8ede89dba3d", "role_seed_contract_registry"),
)

_EVIDENCE_BY_ID = {spec[0]: spec for spec in _EVIDENCE_SPECS}

_PRIMARY_ROLES = (
    (0, "scaffold"),
    (1, "linker"),
    (2, "warhead"),
)

_TASK_SPECS = (
    (0, "warhead_only", "A", ("warhead",), ("scaffold", "linker")),
    (1, "linker_plus_warhead", "B", ("linker", "warhead"), ("scaffold",)),
    (2, "scaffold_plus_warhead", "B2", ("scaffold", "warhead"), ("linker",)),
    (3, "scaffold_only", "B3", ("scaffold",), ("linker", "warhead")),
    (4, "scaffold_plus_linker_plus_warhead", "C", ("scaffold", "linker", "warhead"), ()),
)

_TASK_INTERNAL_LEVELS = {
    "warhead_only": "A_warhead_only",
    "linker_plus_warhead": "B_linker_warhead",
    "scaffold_plus_warhead": "B2_scaffold_warhead",
    "scaffold_only": "B3_scaffold_only",
    "scaffold_plus_linker_plus_warhead": "C_scaffold_linker_warhead",
}

_SUPPORTED_HEAVY_SYMBOLS = ("C", "N", "O", "S", "B", "Br", "Cl", "P", "I", "F")
_CHECKPOINT_CHANNEL_ORDER = "C:0|N:1|O:2|S:3|B:4|Br:5|Cl:6|P:7|I:8|F:9"

_FIELD_CONTRACTS = (
    ("F01", "ligand_role_id", "int64", "1", "[N_ligand]", "flattened_ligand_index_0based", "flattened from retained-heavy local indices by ligand_node_offsets", "no_padding_rows_admitted", "-1 iff ligand_role_valid is false", "0|1|2 iff valid=true; -1 iff valid=false; all admitted base-mask rows valid", "0=scaffold|1=linker|2=warhead|-1=invalid_sentinel", "true", "false"),
    ("F02", "ligand_role_valid", "bool", "1", "[N_ligand]", "flattened_ligand_index_0based", "same row domain and order as ligand_role_id", "no_padding_rows_admitted", "companion requires ligand_role_id=-1 when false", "true for every row used to derive base masks; incomplete role authority cannot be training-admitted", "true=Exact3 role id valid|false=role id is -1 sentinel", "true", "false"),
    ("F03", "canonical_task_id", "int64", "1", "[B]", "batch_sample_index_0based", "one task id per sample", "no_padding_samples_admitted", "no sentinel without canonical_task_valid=false", "valid values are exact int 0..4 and bool is rejected", "0..4 map only through long semantic names", "true", "false"),
    ("F04", "canonical_task_valid", "bool", "1", "[B]", "batch_sample_index_0based", "same sample order as canonical_task_id", "no_padding_samples_admitted", "not_applicable", "false disables active diffusion loss for the sample", "true=task id valid", "true", "false"),
    ("F05", "ligand_base_generation_mask", "bool", "2", "[N_ligand,1]", "flattened_ligand_index_0based", "flattened local rows; future runtime adapter squeezes final axis", "no_padding_rows_admitted", "not_applicable", "requires valid Exact3 role and task authority", "true=generated active base region", "true", "false"),
    ("F06", "ligand_base_fixed_mask", "bool", "2", "[N_ligand,1]", "flattened_ligand_index_0based", "flattened local rows; squeeze(-1) and cast to int64 for future lig_fixed adapter", "no_padding_rows_admitted", "not_applicable", "complement of base generation on admitted retained-heavy rows", "true=preserved base context", "true", "false"),
    ("F07", "ligand_base_target_mask", "bool", "2", "[N_ligand,1]", "flattened_ligand_index_0based", "identical row domain to base generation", "no_padding_rows_admitted", "not_applicable", "equals ligand_base_generation_mask", "true=generated target", "true", "false"),
    ("F08", "ligand_base_context_mask", "bool", "2", "[N_ligand,1]", "flattened_ligand_index_0based", "identical row domain to base fixed", "no_padding_rows_admitted", "not_applicable", "equals ligand_base_fixed_mask and excludes seed sidecar semantics", "true=preserved base context", "true", "false"),
    ("F09", "ligand_active_diffusion_loss_mask", "bool", "2", "[N_ligand,1]", "flattened_ligand_index_0based", "broadcast sample validity and admission over ligand rows", "padding_false_but_padding_is_not_label_availability", "not_applicable", "generation AND role_valid AND task_valid AND sample_training_admitted", "true=active masked-diffusion loss atom", "true", "false"),
    ("F10", "ligand_minimal_seed_or_anchor_mask", "bool", "2", "[N_ligand,1]", "flattened_ligand_index_0based", "orthogonal flag on retained ligand heavy rows", "no_padding_rows_admitted", "not_applicable", "only Task C; valid=true requires at least one true atom", "true=additional condition without changing base masks or loss", "true", "false"),
    ("F11", "ligand_minimal_seed_or_anchor_valid", "bool", "1", "[B]", "batch_sample_index_0based", "one condition-valid flag per sample", "no_padding_samples_admitted", "not_applicable", "A/B/B2/B3 false; Task C true only with formal nonempty authority", "true=seed or anchor mask authoritative", "true", "false"),
    ("F12", "sample_training_admitted", "bool", "1", "[B]", "batch_sample_index_0based", "broadcast only into active loss mask", "padding_false_but_padding_is_not_label_availability", "not_applicable", "false sample contributes no active diffusion loss", "true=sample admitted for training", "true", "false"),
    ("F13", "ligand_anchor_distance_angstrom", "float32", "2", "[N_ligand,1]", "flattened_ligand_index_0based", "same retained-heavy ligand row order", "no_padding_rows_admitted", "not_applicable", "valid only when target residue reactive atom is available", "Euclidean distance to target_residue_reactive_atom", "true", "false"),
    ("F14", "ligand_anchor_distance_valid", "bool", "2", "[N_ligand,1]", "flattened_ligand_index_0based", "same rows as ligand_anchor_distance_angstrom", "no_padding_rows_admitted", "not_applicable", "false when target residue reactive atom is unavailable", "true=distance label valid", "true", "false"),
)

_FAILURE_CASES = (
    ("X01", "canonical_task_count_not_five", "exact5_task_registry"),
    ("X02", "scaffold_only_B3_missing", "B3_required"),
    ("X03", "B2_B3_swapped", "semantic_truth_table"),
    ("X04", "short_alias_is_only_semantic_authority", "long_name_authority"),
    ("X05", "sixth_mask_added", "exact5_task_registry"),
    ("X06", "fourth_primary_role_added", "exact3_role_vocabulary"),
    ("X07", "role_partition_overlap", "disjoint_partition"),
    ("X08", "role_partition_incomplete", "exhaustive_partition"),
    ("X09", "role_index_out_of_range_or_duplicate", "retained_index_validation"),
    ("X10", "explicit_H_in_role_domain", "retained_heavy_domain"),
    ("X11", "source_full_table_index_used_as_retained_index", "index_space_binding"),
    ("X12", "bool_accepted_as_task_or_role_id", "exact_int_id_types"),
    ("X13", "generation_fixed_overlap", "base_partition_disjoint"),
    ("X14", "generation_fixed_not_exhaustive", "base_partition_exhaustive"),
    ("X15", "target_context_overlap", "target_context_partition"),
    ("X16", "Task_C_has_base_fixed_primary_atom", "Task_C_base_mask"),
    ("X17", "seed_or_anchor_used_as_fourth_role", "orthogonal_seed_sidecar"),
    ("X18", "seed_or_anchor_used_as_sixth_mask", "orthogonal_seed_sidecar"),
    ("X19", "seed_sidecar_silently_changes_lig_fixed", "base_mask_independence"),
    ("X20", "non_C_task_enables_seed_condition", "Task_C_only_condition"),
    ("X21", "missing_seed_authority_marked_materializable", "authority_readiness_gate"),
    ("X22", "warhead_complement_claims_scaffold_linker_separated", "authority_non_inference"),
    ("X23", "ligand_internal_boundary_claims_complete_roles", "authority_non_inference"),
    ("X24", "anchor_distance_reinterpreted_as_ligand_seed_distance", "anchor_distance_reference"),
    ("X25", "active_loss_includes_fixed_atom", "active_loss_formula"),
    ("X26", "active_loss_includes_invalid_sample", "active_loss_formula"),
    ("X27", "sidecar_concatenated_into_checkpoint_10D", "checkpoint_boundary"),
    ("X28", "runtime_loader_model_forward_or_loss_modified", "candidate_scope"),
    ("X29", "tensor_checkpoint_runtime_or_training_boundary_crossed", "execution_boundary"),
    ("X30", "critical_response_field_tampered_with_recomputed_digest", "response_integrity"),
    ("X31", "empty_primary_role_region", "nonempty_exact3_partition"),
    ("X32", "role_id_validity_sentinel_mismatch", "role_validity_pair_contract"),
    ("X33", "seed_bundle_validator_bypass", "final_bundle_seed_validation"),
    ("X34", "candidate_lifecycle_not_commit_survivable", "exact3_contract_lifecycle"),
)

_FIELD_COLUMNS = (
    "contract_id", "field_name", "dtype", "rank", "shape", "index_space",
    "local_flat_relationship", "padding_policy", "sentinel_policy",
    "validity_policy", "polarity_or_semantics", "sidecar_only",
    "materialized_v1",
)

_RESPONSE_FIELDS = (
    "contract_version", "error_contract", "repository", "branch", "base_head",
    "base_head_subject", "origin_main", "ahead", "behind",
    "contract_lifecycle_profile", "contract_commit", "contract_committed",
    "contract_published", "ready_for_contract_commit_review", "candidate_paths",
    "evidence_records", "predecessor_open_issue", "predecessor_open_issue_reason",
    "canonical_role_vocabulary", "canonical_role_count", "canonical_task_truth_table",
    "canonical_task_count", "semantic_long_names_authoritative",
    "display_aliases_runtime_input_allowed", "base_task_mask_matches_runtime",
    "task_c_base_generation", "task_c_base_fixed",
    "task_c_seed_conditioning_semantics", "minimal_seed_is_primary_role",
    "minimal_seed_is_canonical_task", "field_contract_registry",
    "field_contract_count", "runtime_lig_fixed_polarity", "future_adapter_relation",
    "active_diffusion_loss_rule", "anchor_distance_semantic_name",
    "anchor_distance_reference", "anchor_distance_unit", "anchor_distance_frame",
    "anchor_distance_shape", "warhead_atom_set_authority_coverage",
    "ligand_internal_warhead_boundary_authority_coverage",
    "role_task_mask_contract_resolved", "primary_role_authority_complete",
    "minimal_seed_anchor_authority_complete", "role_assignment_authority_coverage",
    "minimal_seed_anchor_authority_coverage", "base_task_masks_derivable",
    "synthetic_base_task_masks_derivable", "real_role_task_mask_materialization_ready",
    "canonical_mask_tensors_materialized", "ready_for_tensor_materialization_smoke",
    "ready_for_model_integration", "ready_for_training", "checkpoint_atom_feature_width",
    "checkpoint_channel_order", "new_role_task_seed_tensors_are_sidecars",
    "checkpoint_feature_concatenation_allowed", "model_state_dict_changed",
    "checkpoint_migration_required", "feature_semantics_contract_audit_completed",
    "unknown_atom_policy_contract_resolved", "unknown_atom_runtime_enforcement_integrated",
    "silent_zero_vector_fallback_allowed", "unsupported_nonhydrogen_policy",
    "final_training_feature_semantics_revalidation_required", "failure_matrix_case_count",
    "failure_matrix_cases", "synthetic_truth_table_verified", "candidate_scope_verified",
    "runtime_mask_changed", "dataloader_changed", "model_changed", "forward_changed",
    "loss_changed", "tensor_materialization_performed", "checkpoint_access_performed",
    "runtime_smoke_performed", "training_performed", "fine_tuning_performed",
    "parameter_update_performed", "reward_or_rl_performed", "generated_evidence_files",
    "recommended_next_increment", "commit_created", "push_performed",
    "response_field_count", "response_sha256",
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except Exception as error:
        raise ValueError(_ERROR) from error


def _strict_json_object(payload: bytes) -> dict[str, Any]:
    try:
        text = payload.decode("utf-8", errors="strict")
        value = json.loads(text)
    except Exception as error:
        raise ValueError(_ERROR) from error
    if type(value) is not dict or not text.endswith("\n"):
        raise ValueError(_ERROR)
    return value


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    try:
        text = payload.decode("utf-8", errors="strict")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        rows = list(reader)
    except Exception as error:
        raise ValueError(_ERROR) from error
    if not text.endswith("\n") or reader.fieldnames is None or any(None in row for row in rows):
        raise ValueError(_ERROR)
    return rows


def _run_git(repo_root: Path, arguments: Sequence[str], *, allow_one: bool = False) -> tuple[int, bytes, bytes]:
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=repo_root,
            env={**os.environ, "LC_ALL": "C", "LANG": "C"},
            check=False,
            capture_output=True,
            timeout=30,
        )
    except Exception as error:
        raise ValueError(_ERROR) from error
    allowed = (0, 1) if allow_one else (0,)
    if completed.returncode not in allowed:
        raise ValueError(_ERROR)
    return completed.returncode, completed.stdout, completed.stderr


def _git(repo_root: Path, arguments: Sequence[str]) -> bytes:
    returncode, stdout, stderr = _run_git(repo_root, arguments)
    if returncode or stderr:
        raise ValueError(_ERROR)
    return stdout


def _git_text(repo_root: Path, arguments: Sequence[str]) -> str:
    try:
        return _git(repo_root, arguments).decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ValueError(_ERROR) from error


def _snapshot_bytes(repo_root: Path, evidence_id: str) -> bytes:
    try:
        _identifier, commit, path, expected_sha256, _purpose = _EVIDENCE_BY_ID[evidence_id]
    except Exception as error:
        raise ValueError(_ERROR) from error
    payload = _git(repo_root, ["show", f"{commit}:{path}"])
    if not payload or _sha256(payload) != expected_sha256:
        raise ValueError(_ERROR)
    return payload


def _literal_assignment(tree: ast.Module, name: str) -> object:
    values: list[ast.expr] = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            values.append(node.value)
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == name
            and node.value is not None
        ):
            values.append(node.value)
    if len(values) != 1:
        raise ValueError(_ERROR)
    try:
        return ast.literal_eval(values[0])
    except Exception as error:
        raise ValueError(_ERROR) from error


def _literal_type_alias_members(tree: ast.Module, name: str) -> tuple[str, ...]:
    values = [
        node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)
    ]
    if len(values) != 1 or not isinstance(values[0], ast.Subscript):
        raise ValueError(_ERROR)
    expression = values[0]
    if not isinstance(expression.value, ast.Name) or expression.value.id != "Literal":
        raise ValueError(_ERROR)
    slice_value = expression.slice
    elements = slice_value.elts if isinstance(slice_value, ast.Tuple) else [slice_value]
    try:
        result = tuple(ast.literal_eval(element) for element in elements)
    except Exception as error:
        raise ValueError(_ERROR) from error
    if not all(type(item) is str for item in result):
        raise ValueError(_ERROR)
    return result


def _validate_candidate_changes_v1(
    *,
    tracked_worktree_paths: object,
    staged_paths: object,
    ordinary_untracked_paths: object,
) -> None:
    if (
        type(tracked_worktree_paths) is not tuple
        or type(staged_paths) is not tuple
        or type(ordinary_untracked_paths) is not tuple
        or tracked_worktree_paths
        or staged_paths
        or ordinary_untracked_paths != _CANDIDATE_PATHS
    ):
        raise ValueError(_ERROR)


def _derive_contract_lifecycle_v1(facts: object) -> dict[str, object]:
    """Derive one of the three exact contract publication profiles."""

    if type(facts) is not dict:
        raise ValueError(_ERROR)
    try:
        commits = facts["path_commits"]
        live = facts["live_paths"]
        tracked = facts["tracked_worktree_paths"]
        staged = facts["staged_paths"]
        untracked = facts["ordinary_untracked_paths"]
        if (
            facts["base_ancestor_head"] is not True
            or facts["base_ancestor_origin"] is not True
            or type(commits) is not list
            or len(commits) > 1
            or type(live) is not dict
            or tuple(live) != _CANDIDATE_PATHS
            or type(tracked) is not tuple
            or type(staged) is not tuple
            or type(untracked) is not tuple
        ):
            raise ValueError(_ERROR)

        if not commits:
            _validate_candidate_changes_v1(
                tracked_worktree_paths=tracked,
                staged_paths=staged,
                ordinary_untracked_paths=untracked,
            )
            if (
                facts["head"] != _BASE
                or facts["origin"] != _BASE
                or (facts["ahead"], facts["behind"]) != (0, 0)
                or any(
                    item.get("tracked") is not False
                    or item.get("mode") != "100644"
                    or re.fullmatch(r"[0-9a-f]{40}", str(item.get("blob", ""))) is None
                    for item in live.values()
                )
            ):
                raise ValueError(_ERROR)
            return {
                "contract_lifecycle_profile": "contract_precommit_candidate",
                "contract_commit": None,
                "contract_committed": False,
                "contract_published": False,
                "ready_for_contract_commit_review": True,
            }

        commit = commits[0]
        if (
            type(commit) is not dict
            or re.fullmatch(r"[0-9a-f]{40}", str(commit.get("commit", ""))) is None
            or commit.get("parents") != [_BASE]
            or commit.get("subject") != _CONTRACT_COMMIT_SUBJECT
            or tuple(commit.get("changed_paths", ())) != _CANDIDATE_PATHS
            or commit.get("changed_statuses") != {path: "A" for path in _CANDIDATE_PATHS}
            or tuple(commit.get("path_modes", {})) != _CANDIDATE_PATHS
            or tuple(commit.get("path_blobs", {})) != _CANDIDATE_PATHS
            or any(commit["path_modes"][path] != "100644" for path in _CANDIDATE_PATHS)
            or any(
                re.fullmatch(r"[0-9a-f]{40}", commit["path_blobs"][path]) is None
                for path in _CANDIDATE_PATHS
            )
            or any(
                live[path]
                != {
                    "tracked": True,
                    "mode": "100644",
                    "index_blob": commit["path_blobs"][path],
                    "blob": commit["path_blobs"][path],
                }
                for path in _CANDIDATE_PATHS
            )
            or any(path in tracked or path in staged or path in untracked for path in _CANDIDATE_PATHS)
            or commit.get("ancestor_head") is not True
        ):
            raise ValueError(_ERROR)

        if commit.get("ancestor_origin") is True:
            return {
                "contract_lifecycle_profile": "contract_published_successor",
                "contract_commit": commit["commit"],
                "contract_committed": True,
                "contract_published": True,
                "ready_for_contract_commit_review": False,
            }
        if (
            facts["head"] != commit["commit"]
            or facts["origin"] != _BASE
            or (facts["ahead"], facts["behind"]) != (1, 0)
            or facts["repository_clean"] is not True
        ):
            raise ValueError(_ERROR)
        return {
            "contract_lifecycle_profile": "contract_committed_unpushed",
            "contract_commit": commit["commit"],
            "contract_committed": True,
            "contract_published": False,
            "ready_for_contract_commit_review": False,
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    returncode, stdout, stderr = _run_git(
        repo_root,
        ["merge-base", "--is-ancestor", ancestor, descendant],
        allow_one=True,
    )
    if stdout or stderr:
        raise ValueError(_ERROR)
    return returncode == 0


def _collect_live_candidate_identity_v1(
    repo_root: Path, path: str
) -> dict[str, object]:
    """Collect index identity separately from actual worktree-byte identity."""

    if type(repo_root) is not type(Path()) or type(path) is not str or path not in _CANDIDATE_PATHS:
        raise ValueError(_ERROR)
    candidate = repo_root / path
    try:
        metadata = candidate.lstat()
    except OSError as error:
        raise ValueError(_ERROR) from error
    worktree_blob = _git_text(
        repo_root, ["hash-object", "--no-filters", "--", path]
    ).strip()
    if re.fullmatch(r"[0-9a-f]{40}", worktree_blob) is None:
        raise ValueError(_ERROR)
    index_line = _git_text(repo_root, ["ls-files", "--stage", "--", path]).strip()
    if index_line:
        try:
            index_metadata, listed_path = index_line.split("\t", 1)
            mode, index_blob, stage = index_metadata.split()
        except ValueError as error:
            raise ValueError(_ERROR) from error
        if (
            listed_path != path
            or stage != "0"
            or re.fullmatch(r"[0-9a-f]{40}", index_blob) is None
        ):
            raise ValueError(_ERROR)
        return {
            "tracked": True,
            "mode": mode,
            "index_blob": index_blob,
            "blob": worktree_blob,
        }
    return {
        "tracked": False,
        "mode": f"100{stat.S_IMODE(metadata.st_mode):03o}",
        "blob": worktree_blob,
    }


def _collect_contract_lifecycle_v1(
    repo_root: Path,
    *,
    head: str,
    origin: str,
    ahead: int,
    behind: int,
) -> dict[str, object]:
    tracked = tuple(sorted(_git_text(repo_root, ["diff", "--name-only"]).splitlines()))
    staged = tuple(sorted(_git_text(repo_root, ["diff", "--cached", "--name-only"]).splitlines()))
    untracked = tuple(sorted(_git_text(repo_root, ["ls-files", "--others", "--exclude-standard"]).splitlines()))
    revisions = set(_git_text(repo_root, ["rev-list", f"{_BASE}..{head}"]).splitlines())
    revisions.update(_git_text(repo_root, ["rev-list", f"{_BASE}..{origin}"]).splitlines())
    path_commits: list[dict[str, object]] = []
    for commit_hash in sorted(revisions):
        status_lines = _git_text(
            repo_root,
            ["diff-tree", "--root", "--no-commit-id", "--name-status", "-r", commit_hash],
        ).splitlines()
        statuses: dict[str, str] = {}
        for line in status_lines:
            parts = line.split("\t")
            if len(parts) != 2:
                raise ValueError(_ERROR)
            status_code, path = parts
            statuses[path] = status_code
        if not set(statuses).intersection(_CANDIDATE_PATHS):
            continue
        modes: dict[str, str] = {}
        blobs: dict[str, str] = {}
        for path in _CANDIDATE_PATHS:
            line = _git_text(repo_root, ["ls-tree", commit_hash, "--", path]).strip()
            if line:
                metadata, listed_path = line.split("\t", 1)
                mode, object_type, blob = metadata.split()
                if listed_path != path or object_type != "blob":
                    raise ValueError(_ERROR)
                modes[path] = mode
                blobs[path] = blob
        path_commits.append({
            "commit": commit_hash,
            "parents": _git_text(repo_root, ["show", "-s", "--format=%P", commit_hash]).split(),
            "subject": _git_text(repo_root, ["show", "-s", "--format=%s", commit_hash]).strip(),
            "changed_paths": tuple(sorted(statuses)),
            "changed_statuses": {path: statuses[path] for path in sorted(statuses)},
            "path_modes": {path: modes[path] for path in sorted(modes)},
            "path_blobs": {path: blobs[path] for path in sorted(blobs)},
            "ancestor_head": _is_ancestor(repo_root, commit_hash, head),
            "ancestor_origin": _is_ancestor(repo_root, commit_hash, origin),
        })

    live = {
        path: _collect_live_candidate_identity_v1(repo_root, path)
        for path in _CANDIDATE_PATHS
    }
    return {
        "head": head,
        "origin": origin,
        "ahead": ahead,
        "behind": behind,
        "base_ancestor_head": _is_ancestor(repo_root, _BASE, head),
        "base_ancestor_origin": _is_ancestor(repo_root, _BASE, origin),
        "tracked_worktree_paths": tracked,
        "staged_paths": staged,
        "ordinary_untracked_paths": untracked,
        "repository_clean": not tracked and not staged and not untracked,
        "path_commits": path_commits,
        "live_paths": live,
    }


def _validate_repository_state(repo_root: Path) -> dict[str, object]:
    if type(repo_root) is not type(Path()) or not repo_root.is_dir():
        raise ValueError(_ERROR)
    head = _git_text(repo_root, ["rev-parse", "HEAD"]).strip()
    origin = _git_text(repo_root, ["rev-parse", "refs/remotes/origin/main"]).strip()
    branch = _git_text(repo_root, ["branch", "--show-current"]).strip()
    remote = _git_text(repo_root, ["remote", "get-url", "origin"]).strip()
    counts = _git_text(
        repo_root,
        ["rev-list", "--left-right", "--count", "HEAD...refs/remotes/origin/main"],
    ).split()
    if len(counts) != 2:
        raise ValueError(_ERROR)
    ahead, behind = (int(value) for value in counts)
    if (
        branch != _BRANCH
        or remote != _REMOTE
    ):
        raise ValueError(_ERROR)
    lifecycle = _derive_contract_lifecycle_v1(
        _collect_contract_lifecycle_v1(
            repo_root,
            head=head,
            origin=origin,
            ahead=ahead,
            behind=behind,
        )
    )
    for path in _CANDIDATE_PATHS:
        candidate = repo_root / path
        try:
            metadata = candidate.lstat()
        except OSError as error:
            raise ValueError(_ERROR) from error
        if (
            not stat.S_ISREG(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o644
            or metadata.st_size <= 0
            or metadata.st_size > 262_144
            or path.lower().endswith(_FORBIDDEN_SUFFIXES)
        ):
            raise ValueError(_ERROR)
    return {
        "head": _BASE,
        "origin": origin,
        "branch": branch,
        "subject": _BASE_SUBJECT,
        "ahead": ahead,
        "behind": behind,
        **lifecycle,
    }


def _evidence_records(repo_root: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    checked_subjects: dict[str, str] = {}
    for evidence_id, commit, path, expected_sha256, purpose in _EVIDENCE_SPECS:
        if commit not in checked_subjects:
            subject = _git_text(repo_root, ["show", "-s", "--format=%s", commit]).strip()
            if subject != _EVIDENCE_SUBJECTS[commit]:
                raise ValueError(_ERROR)
            checked_subjects[commit] = subject
        payload = _git(repo_root, ["show", f"{commit}:{path}"])
        observed_sha256 = _sha256(payload)
        if not payload or observed_sha256 != expected_sha256:
            raise ValueError(_ERROR)
        records.append({
            "evidence_id": evidence_id,
            "commit": commit,
            "subject": checked_subjects[commit],
            "path": path,
            "sha256": observed_sha256,
            "purpose": purpose,
            "verified": True,
        })
    for commit in (_R1_COMMIT, _R2_COMMIT, _R3_COMMIT):
        subject = _git_text(repo_root, ["show", "-s", "--format=%s", commit]).strip()
        returncode, stdout, stderr = _run_git(
            repo_root, ["merge-base", "--is-ancestor", commit, _BASE], allow_one=True
        )
        if subject != _EVIDENCE_SUBJECTS[commit] or returncode != 0 or stdout or stderr:
            raise ValueError(_ERROR)
    return records


def _task_rows() -> list[dict[str, str]]:
    return [
        {
            "task_id": str(task_id),
            "semantic_name": semantic_name,
            "display_alias": alias,
            "generated_primary_roles": ";".join(generated),
            "fixed_primary_roles": ";".join(fixed),
            "base_generation_equals_target": "true",
            "base_fixed_equals_context": "true",
            "seed_condition_changes_base_masks": "false",
            "verified": "true",
        }
        for task_id, semantic_name, alias, generated, fixed in _TASK_SPECS
    ]


def _field_rows() -> list[dict[str, str]]:
    return [dict(zip(_FIELD_COLUMNS, values)) for values in _FIELD_CONTRACTS]


def _failure_rows() -> list[dict[str, str]]:
    return [
        {
            "failure_id": failure_id,
            "failure_case": case,
            "guard": guard,
            "expected_outcome": "fail_closed",
            "covered_by_test": "true",
            "verified": "true",
        }
        for failure_id, case, guard in _FAILURE_CASES
    ]


def _validate_runtime_contract(repo_root: Path) -> None:
    masking_payload = _snapshot_bytes(repo_root, "E14")
    try:
        masking_tree = ast.parse(masking_payload.decode("utf-8", errors="strict"))
    except Exception as error:
        raise ValueError(_ERROR) from error
    expected_names = tuple(spec[1] for spec in _TASK_SPECS)
    if _literal_assignment(masking_tree, "CANONICAL_MASK_SEMANTICS") != expected_names:
        raise ValueError(_ERROR)
    if _literal_assignment(masking_tree, "CANONICAL_MASK_SEMANTIC_TO_LEVEL") != _TASK_INTERNAL_LEVELS:
        raise ValueError(_ERROR)
    observed_components = _literal_assignment(masking_tree, "LONG_FORM_MASK_COMPONENTS")
    expected_components = {
        _TASK_INTERNAL_LEVELS[semantic]: {"target": generated, "context": fixed}
        for _task_id, semantic, _alias, generated, fixed in _TASK_SPECS
    }
    if observed_components != expected_components:
        raise ValueError(_ERROR)
    functions = {
        node.name: node for node in masking_tree.body if isinstance(node, ast.FunctionDef)
    }
    resolver = functions.get("resolve_canonical_mask_semantic")
    if resolver is None:
        raise ValueError(_ERROR)
    resolver_text = ast.unparse(resolver)
    if (
        "mask_semantic not in CANONICAL_MASK_SEMANTIC_TO_LEVEL" not in resolver_text
        or "return CANONICAL_MASK_SEMANTIC_TO_LEVEL[mask_semantic]" not in resolver_text
    ):
        raise ValueError(_ERROR)

    schema_payload = _snapshot_bytes(repo_root, "E15")
    schema_tree = ast.parse(schema_payload.decode("utf-8", errors="strict"))
    if _literal_type_alias_members(schema_tree, "CanonicalMaskSemantic") != expected_names:
        raise ValueError(_ERROR)

    demo_payload = _snapshot_bytes(repo_root, "E17")
    demo_tree = ast.parse(demo_payload.decode("utf-8", errors="strict"))
    if (
        _literal_assignment(demo_tree, "CANONICAL_MASK_SEMANTICS") != expected_names
        or _literal_assignment(demo_tree, "MASK_SEMANTIC_TO_INTERNAL") != _TASK_INTERNAL_LEVELS
    ):
        raise ValueError(_ERROR)

    dataset_text = _snapshot_bytes(repo_root, "E16").decode("utf-8", errors="strict")
    if (
        "for mask_semantic in CANONICAL_MASK_SEMANTICS" not in dataset_text
        or "build_canonical_mask(" not in dataset_text
    ):
        raise ValueError(_ERROR)


def _signal_facts_from_current11_source(payload: bytes) -> dict[str, dict[str, object]]:
    try:
        tree = ast.parse(payload.decode("utf-8", errors="strict"))
    except Exception as error:
        raise ValueError(_ERROR) from error
    functions = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_build_signal_records"
    ]
    if len(functions) != 1:
        raise ValueError(_ERROR)
    records: dict[str, dict[str, object]] = {}
    for call in ast.walk(functions[0]):
        if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name) or call.func.id != "_signal_record":
            continue
        keywords = {keyword.arg: keyword.value for keyword in call.keywords if keyword.arg is not None}
        required = ("signal_name", "authoritative_sample_coverage", "readiness_status")
        if not all(name in keywords for name in required):
            raise ValueError(_ERROR)
        try:
            values = {name: ast.literal_eval(keywords[name]) for name in required}
            for optional in ("forbidden_interpretations", "missing_semantics"):
                values[optional] = ast.literal_eval(keywords[optional])
        except Exception as error:
            raise ValueError(_ERROR) from error
        signal_name = values.pop("signal_name")
        if type(signal_name) is not str or signal_name in records:
            raise ValueError(_ERROR)
        records[signal_name] = values
    if len(records) != 8:
        raise ValueError(_ERROR)
    return records


def _validate_predecessor_evidence(repo_root: Path) -> dict[str, object]:
    feature = _strict_json_object(_snapshot_bytes(repo_root, "E11"))
    if (
        feature.get("feature_semantics_audit_completed") is not True
        or feature.get("feature_semantics_known") is not True
        or feature.get("unknown_atom_policy_contract_resolved") is not True
        or feature.get("unknown_atom_runtime_enforcement_integrated") is not False
        or feature.get("checkpoint_categorical_width") != 10
        or feature.get("checkpoint_channel_order") != _CHECKPOINT_CHANNEL_ORDER
        or feature.get("checkpoint_channel_order_preserved") is not True
        or feature.get("silent_zero_vector_fallback_allowed") is not False
        or feature.get("unsupported_nonhydrogen_handling") != "reject_sample_fail_closed"
        or feature.get("canonical_mask_tensors_materialized") is not False
        or feature.get("ready_for_training") is not False
    ):
        raise ValueError(_ERROR)

    tensor_manifest = _strict_json_object(_snapshot_bytes(repo_root, "E09"))
    if (
        tensor_manifest.get("base_checkpoint_atom_feature_width") != 10
        or tensor_manifest.get("base_checkpoint_atom_feature_width_changed") is not False
        or tensor_manifest.get("generation_masks_are_not_loss_masks") is not True
        or tensor_manifest.get("padding_masks_are_not_label_availability_masks") is not True
        or tensor_manifest.get("role_vocabulary") != ["scaffold", "linker", "warhead"]
        or tensor_manifest.get("role_assignments_current11_complete") is not False
        or tensor_manifest.get("minimal_seed_or_anchor_authority_present") is not False
        or tensor_manifest.get("checkpoint_access") is not False
        or tensor_manifest.get("training_used") is not False
    ):
        raise ValueError(_ERROR)

    issue_rows = _csv_rows(_snapshot_bytes(repo_root, "E07"))
    matching_issues = [
        row for row in issue_rows
        if row.get("issue_id") == "COVALENT_CONDITION_AND_TASK_MASK_TENSOR_CONTRACT_UNRESOLVED"
    ]
    if (
        len(matching_issues) != 1
        or matching_issues[0].get("successor_effective_status") != "open"
        or matching_issues[0].get("blocking_reason")
        != "current11 per-atom role and minimal-seed/anchor authority missing"
    ):
        raise ValueError(_ERROR)

    registry = {row.get("contract_id"): row for row in _csv_rows(_snapshot_bytes(repo_root, "E06"))}
    role_row = registry.get("ligand_role_id")
    distance_row = registry.get("ligand_anchor_distance_angstrom")
    seed_row = registry.get("ligand_minimal_seed_or_anchor_mask")
    if (
        role_row is None
        or role_row.get("value_domain_or_vocabulary") != "0:scaffold|1:linker|2:warhead"
        or role_row.get("index_space") != "flattened_ligand_index_0based"
        or seed_row is None
        or seed_row.get("blocking_reason") != "minimal_seed_or_anchor_authority_missing"
        or distance_row is None
        or distance_row.get("unit") != "angstrom"
        or distance_row.get("shape") != "[N_ligand,1]"
        or distance_row.get("coordinate_frame") != "centering_invariant_euclidean_distance"
        or "target residue reactive atom" not in distance_row.get("derivation_rule", "")
    ):
        raise ValueError(_ERROR)

    signals = _signal_facts_from_current11_source(_snapshot_bytes(repo_root, "E12"))
    warhead = signals.get("warhead_atom_set")
    boundary = signals.get("ligand_internal_warhead_boundary")
    roles = signals.get("scaffold_linker_anchor_atom_roles")
    if (
        warhead is None
        or warhead["authoritative_sample_coverage"] != "11/11"
        or warhead["readiness_status"] != "authority_ready"
        or boundary is None
        or boundary["authoritative_sample_coverage"] != "11/11"
        or boundary["readiness_status"] != "authority_ready"
        or "ligand_atom_to_residue_atom_pair" not in boundary["forbidden_interpretations"]
        or roles is None
        or roles["authoritative_sample_coverage"] != "0/11"
        or roles["readiness_status"] != "partial_requires_additional_contract"
        or tuple(roles["missing_semantics"])
        != ("scaffold_atom_ids", "linker_atom_ids", "anchor_atom_ids", "minimal_seed_atom_ids")
    ):
        raise ValueError(_ERROR)

    role_manifest = _strict_json_object(_snapshot_bytes(repo_root, "E18"))
    readiness_rows = _csv_rows(_snapshot_bytes(repo_root, "E19"))
    role_registry = {
        row.get("contract_id"): row
        for row in _csv_rows(_snapshot_bytes(repo_root, "E20"))
    }
    partition_contract = role_registry.get("LRMSC_002")
    expected_blockers = [
        "atom_indexed_pre_reaction_connectivity_not_frozen",
        "atom_indexed_pre_reaction_bond_orders_not_frozen",
        "reaction_family_labels_missing",
        "approved_warhead_rules_missing",
        "current11_human_gold_review_missing",
        "COVALENT_CONDITION_AND_TASK_MASK_TENSOR_CONTRACT_UNRESOLVED",
        "COVALENT_GEOMETRY_AND_AUXILIARY_LABEL_CONTRACT_UNRESOLVED",
    ]
    if (
        len(readiness_rows) != role_manifest.get("current11_readiness_row_count")
        or role_manifest.get("canonical_roles") != ["scaffold", "linker", "warhead"]
        or role_manifest.get("canonical_role_count") != 3
        or role_manifest.get("canonical_task_count") != 5
        or role_manifest.get("role_annotation_materialized") is not False
        or role_manifest.get("minimal_seed_materialized") is not False
        or role_manifest.get("ready_for_current11_role_annotation_proposal_generation") is not False
        or role_manifest.get("ready_for_current11_minimal_seed_proposal_generation") is not False
        or role_manifest.get("current11_role_proposal_generation_ready_count") != 0
        or role_manifest.get("current11_minimal_seed_proposal_generation_ready_count") != 0
        or role_manifest.get("recommended_next_step") != _RECOMMENDED_NEXT_INCREMENT
        or role_manifest.get("remaining_readiness_blockers") != expected_blockers
        or partition_contract is None
        or partition_contract.get("semantic_name") != "role_atom_set_partition"
        or partition_contract.get("derivation_rule") != "disjoint exhaustive partition"
        or partition_contract.get("index_space") != "retained_heavy_local_index_0based"
        or partition_contract.get("validity_semantics") != "no H; all roles nonempty"
        or partition_contract.get("ambiguity_semantics") != "overlap or gap blocked"
        or partition_contract.get("verified") != "true"
    ):
        raise ValueError(_ERROR)
    role_authority_count = sum(
        row.get("role_proposal_generation_ready") == "true"
        and row.get("human_gold_review_completed") == "true"
        for row in readiness_rows
    )
    seed_authority_count = sum(
        row.get("minimal_seed_proposal_generation_ready") == "true"
        and row.get("human_gold_review_completed") == "true"
        for row in readiness_rows
    )
    if (
        not readiness_rows
        or any(row.get("verified") != "true" for row in readiness_rows)
        or role_authority_count
        != role_manifest.get("current11_role_proposal_generation_ready_count")
        or seed_authority_count
        != role_manifest.get("current11_minimal_seed_proposal_generation_ready_count")
    ):
        raise ValueError(_ERROR)
    denominator = len(readiness_rows)
    current_audit_text = _snapshot_bytes(repo_root, "E01").decode("utf-8", errors="strict")
    if '"final_training_feature_semantics_revalidation_required": True' not in current_audit_text:
        raise ValueError(_ERROR)
    return {
        "predecessor_issue": matching_issues[0]["issue_id"],
        "predecessor_issue_reason": matching_issues[0]["blocking_reason"],
        "warhead_coverage": warhead["authoritative_sample_coverage"],
        "boundary_coverage": boundary["authoritative_sample_coverage"],
        "role_coverage": f"{role_authority_count}/{denominator}",
        "seed_coverage": f"{seed_authority_count}/{denominator}",
        "primary_role_authority_complete": role_authority_count == denominator,
        "seed_authority_complete": seed_authority_count == denominator,
        "recommended_next_increment": role_manifest["recommended_next_step"],
    }


def _contract_spec_v1() -> dict[str, object]:
    return {
        "primary_roles": [
            {"role_id": role_id, "semantic_name": name}
            for role_id, name in _PRIMARY_ROLES
        ],
        "tasks": [
            {
                "task_id": task_id,
                "semantic_name": semantic,
                "display_alias": alias,
                "generated_primary_roles": list(generated),
                "fixed_primary_roles": list(fixed),
            }
            for task_id, semantic, alias, generated, fixed in _TASK_SPECS
        ],
        "long_names_are_semantic_authority": True,
        "display_aliases_are_runtime_inputs": False,
        "minimal_seed_is_primary_role": False,
        "minimal_seed_is_canonical_task": False,
        "task_c_seed_semantics": "orthogonal_conditioning_sidecar_does_not_change_base_masks_or_active_loss",
        "anchor_distance_reference": "target_residue_reactive_atom",
        "anchor_distance_is_seed_locator": False,
        "warhead_complement_separates_scaffold_and_linker": False,
        "ligand_internal_boundary_is_complete_role_authority": False,
        "sidecars_concatenated_to_checkpoint_10d": False,
        "checkpoint_feature_width": 10,
        "runtime_mask_changed": False,
        "dataloader_changed": False,
        "model_changed": False,
        "forward_changed": False,
        "loss_changed": False,
        "tensor_materialization_performed": False,
        "checkpoint_access_performed": False,
        "runtime_smoke_performed": False,
        "training_performed": False,
        "parameter_update_performed": False,
        "reward_or_rl_performed": False,
    }


def _validate_contract_spec_v1(spec: object) -> None:
    expected = _contract_spec_v1()
    if type(spec) is not dict or _canonical_json_bytes(spec) != _canonical_json_bytes(expected):
        raise ValueError(_ERROR)
    roles = spec["primary_roles"]
    tasks = spec["tasks"]
    if (
        len(roles) != 3
        or [(row["role_id"], row["semantic_name"]) for row in roles] != list(_PRIMARY_ROLES)
        or len(tasks) != 5
        or tasks[3]["semantic_name"] != "scaffold_only"
        or tasks[3]["display_alias"] != "B3"
        or tasks[2]["semantic_name"] == tasks[3]["semantic_name"]
        or tasks[4]["fixed_primary_roles"] != []
    ):
        raise ValueError(_ERROR)


def _exact_int_sequence(values: object) -> tuple[int, ...]:
    if type(values) not in (list, tuple):
        raise ValueError(_ERROR)
    result = tuple(values)
    if any(type(value) is not int for value in result):
        raise ValueError(_ERROR)
    return result


def _validate_role_partition_v1(
    *,
    ligand_atom_symbols: object,
    role_id_by_atom: object,
    scaffold_indices: object,
    linker_indices: object,
    warhead_indices: object,
    index_space: object,
) -> None:
    if (
        type(ligand_atom_symbols) not in (list, tuple)
        or type(index_space) is not str
        or index_space != "retained_heavy_local_index_0based"
    ):
        raise ValueError(_ERROR)
    symbols = tuple(ligand_atom_symbols)
    roles = _exact_int_sequence(role_id_by_atom)
    groups = tuple(
        _exact_int_sequence(values)
        for values in (scaffold_indices, linker_indices, warhead_indices)
    )
    atom_count = len(symbols)
    if (
        atom_count <= 0
        or len(roles) != atom_count
        or any(not group for group in groups)
        or any(type(symbol) is not str or symbol not in _SUPPORTED_HEAVY_SYMBOLS for symbol in symbols)
        or any(role not in (0, 1, 2) for role in roles)
        or any(len(set(group)) != len(group) for group in groups)
        or any(index < 0 or index >= atom_count for group in groups for index in group)
    ):
        raise ValueError(_ERROR)
    sets = tuple(set(group) for group in groups)
    if (
        any(sets[left] & sets[right] for left in range(3) for right in range(left + 1, 3))
        or set().union(*sets) != set(range(atom_count))
        or any(roles[index] != role_id for role_id, group in enumerate(groups) for index in group)
    ):
        raise ValueError(_ERROR)


def _validate_bool_sequence(values: object, length: int) -> tuple[bool, ...]:
    if type(values) not in (list, tuple):
        raise ValueError(_ERROR)
    result = tuple(values)
    if len(result) != length or any(type(value) is not bool for value in result):
        raise ValueError(_ERROR)
    return result


def _validate_role_id_validity_pairs_v1(
    *, role_ids: object, role_valid: object
) -> tuple[tuple[int, ...], tuple[bool, ...]]:
    """Validate the closed Exact3 IDs and their only invalid sentinel."""

    roles = _exact_int_sequence(role_ids)
    valid = _validate_bool_sequence(role_valid, len(roles))
    if not roles or any(
        (is_valid and role_id not in (0, 1, 2))
        or (not is_valid and role_id != -1)
        for role_id, is_valid in zip(roles, valid)
    ):
        raise ValueError(_ERROR)
    return roles, valid


def _derive_base_masks_v1(
    *,
    role_ids: object,
    task_id: object,
    role_valid: object,
    canonical_task_valid: object,
    sample_training_admitted: object,
    seed_mask: object,
    seed_valid: object,
) -> dict[str, tuple[bool, ...]]:
    roles, valid_roles = _validate_role_id_validity_pairs_v1(
        role_ids=role_ids,
        role_valid=role_valid,
    )
    if (
        not all(valid_roles)
        or type(task_id) is not int
        or task_id not in range(5)
        or type(canonical_task_valid) is not bool
        or type(sample_training_admitted) is not bool
        or type(seed_valid) is not bool
    ):
        raise ValueError(_ERROR)
    seed = _validate_bool_sequence(seed_mask, len(roles))
    if task_id != 4:
        if seed_valid or any(seed):
            raise ValueError(_ERROR)
    elif seed_valid:
        if not any(seed):
            raise ValueError(_ERROR)
    elif any(seed):
        raise ValueError(_ERROR)
    generated_names = set(_TASK_SPECS[task_id][3])
    role_names = dict(_PRIMARY_ROLES)
    generation = tuple(role_names[role] in generated_names for role in roles)
    fixed = tuple(not value for value in generation)
    active = tuple(
        generation[index]
        and valid_roles[index]
        and canonical_task_valid
        and sample_training_admitted
        for index in range(len(roles))
    )
    bundle = {
        "generation": generation,
        "fixed": fixed,
        "target": generation,
        "context": fixed,
        "seed": seed,
        "active_loss": active,
    }
    _validate_mask_bundle_v1(
        bundle=bundle,
        role_ids=roles,
        task_id=task_id,
        role_valid=valid_roles,
        canonical_task_valid=canonical_task_valid,
        sample_training_admitted=sample_training_admitted,
        seed_valid=seed_valid,
    )
    return bundle


def _validate_mask_bundle_v1(
    *,
    bundle: object,
    role_ids: object,
    task_id: object,
    role_valid: object,
    canonical_task_valid: object,
    sample_training_admitted: object,
    seed_valid: object,
) -> None:
    if type(bundle) is not dict or tuple(bundle) != (
        "generation", "fixed", "target", "context", "seed", "active_loss"
    ):
        raise ValueError(_ERROR)
    roles, valid_roles = _validate_role_id_validity_pairs_v1(
        role_ids=role_ids,
        role_valid=role_valid,
    )
    if (
        not all(valid_roles)
        or type(task_id) is not int
        or task_id not in range(5)
        or type(seed_valid) is not bool
    ):
        raise ValueError(_ERROR)
    if type(canonical_task_valid) is not bool or type(sample_training_admitted) is not bool:
        raise ValueError(_ERROR)
    masks = {
        name: _validate_bool_sequence(bundle[name], len(roles))
        for name in bundle
    }
    generation = masks["generation"]
    fixed = masks["fixed"]
    target = masks["target"]
    context = masks["context"]
    seed = masks["seed"]
    if (
        generation != target
        or fixed != context
        or any(left and right for left, right in zip(generation, fixed))
        or not all(left or right for left, right in zip(generation, fixed))
        or any(left and right for left, right in zip(target, context))
        or not all(left or right for left, right in zip(target, context))
        or (task_id == 4 and any(fixed))
        or (task_id != 4 and (seed_valid or any(seed)))
        or (task_id == 4 and seed_valid != any(seed))
        or any(value and not valid_roles[index] for index, value in enumerate(seed))
    ):
        raise ValueError(_ERROR)
    expected_generated = set(_TASK_SPECS[task_id][3])
    role_names = dict(_PRIMARY_ROLES)
    expected_generation = tuple(role_names[role] in expected_generated for role in roles)
    expected_active = tuple(
        expected_generation[index]
        and valid_roles[index]
        and canonical_task_valid
        and sample_training_admitted
        for index in range(len(roles))
    )
    if generation != expected_generation or masks["active_loss"] != expected_active:
        raise ValueError(_ERROR)


def _verify_synthetic_truth_table_v1() -> list[dict[str, object]]:
    symbols = ("C", "N", "O", "S", "C", "N")
    roles = (0, 0, 1, 1, 2, 2)
    _validate_role_partition_v1(
        ligand_atom_symbols=symbols,
        role_id_by_atom=roles,
        scaffold_indices=(0, 1),
        linker_indices=(2, 3),
        warhead_indices=(4, 5),
        index_space="retained_heavy_local_index_0based",
    )
    rows: list[dict[str, object]] = []
    for task_id, semantic, _alias, _generated, _fixed in _TASK_SPECS:
        seed = (True, False, False, False, False, False) if task_id == 4 else (False,) * 6
        bundle = _derive_base_masks_v1(
            role_ids=roles,
            task_id=task_id,
            role_valid=(True,) * 6,
            canonical_task_valid=True,
            sample_training_admitted=True,
            seed_mask=seed,
            seed_valid=task_id == 4,
        )
        rows.append({
            "task_id": task_id,
            "semantic_name": semantic,
            "generation": list(bundle["generation"]),
            "fixed": list(bundle["fixed"]),
            "seed": list(bundle["seed"]),
            "active_loss": list(bundle["active_loss"]),
        })
    if (
        len(rows) != 5
        or rows[4]["generation"] != [True] * 6
        or rows[4]["fixed"] != [False] * 6
        or not any(rows[4]["seed"])
        or tuple(row["semantic_name"] for row in rows) != tuple(spec[1] for spec in _TASK_SPECS)
    ):
        raise ValueError(_ERROR)
    return rows


def _validate_artifacts(repo_root: Path, evidence_records: Sequence[Mapping[str, object]]) -> dict[str, object]:
    source_rows = _csv_rows((repo_root / _SOURCE_INVENTORY_PATH).read_bytes())
    expected_source_rows = [
        {
            "evidence_id": str(record["evidence_id"]),
            "commit": str(record["commit"]),
            "subject": str(record["subject"]),
            "path": str(record["path"]),
            "sha256": str(record["sha256"]),
            "purpose": str(record["purpose"]),
            "verified": "true",
        }
        for record in evidence_records
    ]
    task_rows = _csv_rows((repo_root / _TASK_TABLE_PATH).read_bytes())
    field_rows = _csv_rows((repo_root / _FIELD_REGISTRY_PATH).read_bytes())
    failure_rows = _csv_rows((repo_root / _FAILURE_MATRIX_PATH).read_bytes())
    if (
        source_rows != expected_source_rows
        or task_rows != _task_rows()
        or field_rows != _field_rows()
        or failure_rows != _failure_rows()
    ):
        raise ValueError(_ERROR)
    manifest = _strict_json_object((repo_root / _MANIFEST_PATH).read_bytes())
    expected_fields = (
        "contract_version", "base_commit", "canonical_role_count",
        "canonical_task_count", "source_inventory_row_count",
        "field_contract_row_count", "failure_matrix_row_count",
        "authority_coverages", "readiness", "semantic_resolutions",
        "checkpoint_compatibility", "execution_boundary", "evidence_sha256",
        "recommended_next_increment",
    )
    evidence_sha256 = {
        Path(path).name: _sha256((repo_root / path).read_bytes())
        for path in (
            _SOURCE_INVENTORY_PATH,
            _TASK_TABLE_PATH,
            _FIELD_REGISTRY_PATH,
            _FAILURE_MATRIX_PATH,
        )
    }
    if (
        tuple(manifest) != expected_fields
        or manifest["contract_version"] != _VERSION
        or manifest["base_commit"] != _BASE
        or manifest["canonical_role_count"] != 3
        or manifest["canonical_task_count"] != 5
        or manifest["source_inventory_row_count"] != len(_EVIDENCE_SPECS)
        or manifest["field_contract_row_count"] != len(_FIELD_CONTRACTS)
        or manifest["failure_matrix_row_count"] != len(_FAILURE_CASES)
        or manifest["evidence_sha256"] != evidence_sha256
        or Path(_MANIFEST_PATH).name in manifest["evidence_sha256"]
        or any(value.startswith("/") for value in manifest["evidence_sha256"])
        or manifest["semantic_resolutions"] != {
            "primary_role_vocabulary": "0=scaffold|1=linker|2=warhead",
            "base_task_mask_contract": "byte_semantic_equivalent_to_current_canonical_runtime",
            "task_c_base_generation": "scaffold|linker|warhead",
            "task_c_base_fixed": "empty",
            "minimal_seed_or_anchor": "orthogonal_conditioning_sidecar",
            "seed_changes_base_generation_or_fixed": False,
            "active_diffusion_loss": "base_generation AND role_valid AND canonical_task_valid AND sample_training_admitted",
            "anchor_distance_reference": "target_residue_reactive_atom",
            "primary_role_regions_nonempty": True,
            "role_id_validity_rule": "valid=true iff role_id in 0|1|2; valid=false iff role_id=-1",
        }
        or manifest["checkpoint_compatibility"] != {
            "atom_feature_width": 10,
            "channel_order": _CHECKPOINT_CHANNEL_ORDER,
            "new_tensors_are_sidecars": True,
            "sidecar_concatenation_allowed": False,
            "model_state_dict_changed": False,
            "checkpoint_migration_required": False,
            "final_training_feature_semantics_revalidation_required": True,
        }
        or manifest["execution_boundary"] != {
            "runtime_mask_changed": False,
            "dataloader_changed": False,
            "model_changed": False,
            "forward_changed": False,
            "loss_changed": False,
            "tensor_materialization_performed": False,
            "checkpoint_access_performed": False,
            "runtime_smoke_performed": False,
            "training_performed": False,
            "fine_tuning_performed": False,
            "parameter_update_performed": False,
            "reward_or_rl_performed": False,
            "commit_created": False,
            "push_performed": False,
        }
        or manifest["recommended_next_increment"]
        != _RECOMMENDED_NEXT_INCREMENT
    ):
        raise ValueError(_ERROR)
    return manifest


def _expected_evidence_response_records_v1() -> list[dict[str, object]]:
    return [
        {
            "evidence_id": evidence_id,
            "commit": commit,
            "subject": _EVIDENCE_SUBJECTS[commit],
            "path": path,
            "sha256": sha256,
            "purpose": purpose,
            "verified": True,
        }
        for evidence_id, commit, path, sha256, purpose in _EVIDENCE_SPECS
    ]


def _coverage_complete_v1(value: object) -> bool:
    if type(value) is not str or re.fullmatch(r"[0-9]+/[1-9][0-9]*", value) is None:
        raise ValueError(_ERROR)
    numerator_text, denominator_text = value.split("/", 1)
    numerator, denominator = int(numerator_text), int(denominator_text)
    if numerator > denominator:
        raise ValueError(_ERROR)
    return numerator == denominator


def _validate_response_lifecycle_v1(response: Mapping[str, object]) -> None:
    profile = response["contract_lifecycle_profile"]
    commit = response["contract_commit"]
    if type(response["ahead"]) is not int or type(response["behind"]) is not int:
        raise ValueError(_ERROR)
    if profile == "contract_precommit_candidate":
        valid = (
            commit is None
            and response["origin_main"] == _BASE
            and (response["ahead"], response["behind"]) == (0, 0)
            and response["contract_committed"] is False
            and response["contract_published"] is False
            and response["ready_for_contract_commit_review"] is True
        )
    elif profile == "contract_committed_unpushed":
        valid = (
            type(commit) is str
            and re.fullmatch(r"[0-9a-f]{40}", commit) is not None
            and commit != _BASE
            and response["origin_main"] == _BASE
            and (response["ahead"], response["behind"]) == (1, 0)
            and response["contract_committed"] is True
            and response["contract_published"] is False
            and response["ready_for_contract_commit_review"] is False
        )
    elif profile == "contract_published_successor":
        valid = (
            type(commit) is str
            and re.fullmatch(r"[0-9a-f]{40}", commit) is not None
            and commit != _BASE
            and type(response["origin_main"]) is str
            and re.fullmatch(r"[0-9a-f]{40}", response["origin_main"]) is not None
            and type(response["ahead"]) is int
            and response["ahead"] >= 0
            and type(response["behind"]) is int
            and response["behind"] >= 0
            and response["contract_committed"] is True
            and response["contract_published"] is True
            and response["ready_for_contract_commit_review"] is False
        )
    else:
        valid = False
    if not valid:
        raise ValueError(_ERROR)


def _validate_response_v1(response: object) -> None:
    if type(response) is not dict or tuple(response) != _RESPONSE_FIELDS:
        raise ValueError(_ERROR)
    unsigned = {key: response[key] for key in _RESPONSE_FIELDS[:-1]}
    role_table = [
        {"role_id": role_id, "semantic_name": semantic_name}
        for role_id, semantic_name in _PRIMARY_ROLES
    ]
    task_table = [
        {
            "task_id": task_id,
            "semantic_name": semantic_name,
            "display_alias": alias,
            "generated_primary_roles": list(generated),
            "fixed_primary_roles": list(fixed),
        }
        for task_id, semantic_name, alias, generated, fixed in _TASK_SPECS
    ]
    exact_values: dict[str, object] = {
        "contract_version": _VERSION,
        "error_contract": _ERROR,
        "repository": _REPOSITORY,
        "branch": _BRANCH,
        "base_head": _BASE,
        "base_head_subject": _BASE_SUBJECT,
        "candidate_paths": list(_CANDIDATE_PATHS),
        "evidence_records": _expected_evidence_response_records_v1(),
        "predecessor_open_issue": "COVALENT_CONDITION_AND_TASK_MASK_TENSOR_CONTRACT_UNRESOLVED",
        "predecessor_open_issue_reason": "current11 per-atom role and minimal-seed/anchor authority missing",
        "canonical_role_vocabulary": role_table,
        "canonical_role_count": 3,
        "canonical_task_truth_table": task_table,
        "canonical_task_count": 5,
        "semantic_long_names_authoritative": True,
        "display_aliases_runtime_input_allowed": False,
        "base_task_mask_matches_runtime": True,
        "task_c_base_generation": ["scaffold", "linker", "warhead"],
        "task_c_base_fixed": [],
        "task_c_seed_conditioning_semantics": "orthogonal_conditioning_sidecar_does_not_change_base_masks_or_active_loss",
        "minimal_seed_is_primary_role": False,
        "minimal_seed_is_canonical_task": False,
        "field_contract_registry": _field_rows(),
        "field_contract_count": len(_FIELD_CONTRACTS),
        "runtime_lig_fixed_polarity": "1=fixed|0=generated",
        "future_adapter_relation": "lig_fixed=ligand_base_fixed_mask.squeeze(-1).cast(int64)",
        "active_diffusion_loss_rule": "base_generation AND role_valid AND canonical_task_valid AND sample_training_admitted",
        "anchor_distance_semantic_name": "ligand_to_target_reactive_atom_distance_angstrom",
        "anchor_distance_reference": "target_residue_reactive_atom",
        "anchor_distance_unit": "angstrom",
        "anchor_distance_frame": "centering_invariant_euclidean_distance",
        "anchor_distance_shape": "[N_ligand,1]",
        "warhead_atom_set_authority_coverage": "11/11",
        "ligand_internal_warhead_boundary_authority_coverage": "11/11",
        "role_task_mask_contract_resolved": True,
        "primary_role_authority_complete": False,
        "minimal_seed_anchor_authority_complete": False,
        "role_assignment_authority_coverage": "0/11",
        "minimal_seed_anchor_authority_coverage": "0/11",
        "base_task_masks_derivable": False,
        "synthetic_base_task_masks_derivable": True,
        "real_role_task_mask_materialization_ready": False,
        "canonical_mask_tensors_materialized": False,
        "ready_for_tensor_materialization_smoke": False,
        "ready_for_model_integration": False,
        "ready_for_training": False,
        "checkpoint_atom_feature_width": 10,
        "checkpoint_channel_order": _CHECKPOINT_CHANNEL_ORDER,
        "new_role_task_seed_tensors_are_sidecars": True,
        "checkpoint_feature_concatenation_allowed": False,
        "model_state_dict_changed": False,
        "checkpoint_migration_required": False,
        "feature_semantics_contract_audit_completed": True,
        "unknown_atom_policy_contract_resolved": True,
        "unknown_atom_runtime_enforcement_integrated": False,
        "silent_zero_vector_fallback_allowed": False,
        "unsupported_nonhydrogen_policy": "reject_sample_fail_closed",
        "final_training_feature_semantics_revalidation_required": True,
        "failure_matrix_case_count": len(_FAILURE_CASES),
        "failure_matrix_cases": [case for _identifier, case, _guard in _FAILURE_CASES],
        "synthetic_truth_table_verified": True,
        "candidate_scope_verified": True,
        "runtime_mask_changed": False,
        "dataloader_changed": False,
        "model_changed": False,
        "forward_changed": False,
        "loss_changed": False,
        "tensor_materialization_performed": False,
        "checkpoint_access_performed": False,
        "runtime_smoke_performed": False,
        "training_performed": False,
        "fine_tuning_performed": False,
        "parameter_update_performed": False,
        "reward_or_rl_performed": False,
        "generated_evidence_files": list(_GENERATED_EVIDENCE_PATHS),
        "recommended_next_increment": _RECOMMENDED_NEXT_INCREMENT,
        "commit_created": False,
        "push_performed": False,
        "response_field_count": len(_RESPONSE_FIELDS),
    }
    role_complete = _coverage_complete_v1(response["role_assignment_authority_coverage"])
    seed_complete = _coverage_complete_v1(response["minimal_seed_anchor_authority_coverage"])
    if (
        response["response_sha256"] != _sha256(_canonical_json_bytes(unsigned))
        or any(response[key] != value for key, value in exact_values.items())
        or _coverage_complete_v1(response["warhead_atom_set_authority_coverage"]) is not True
        or _coverage_complete_v1(response["ligand_internal_warhead_boundary_authority_coverage"]) is not True
        or response["primary_role_authority_complete"] is not role_complete
        or response["minimal_seed_anchor_authority_complete"] is not seed_complete
        or response["base_task_masks_derivable"] is not role_complete
        or response["real_role_task_mask_materialization_ready"] is not (role_complete and seed_complete)
    ):
        raise ValueError(_ERROR)
    _validate_response_lifecycle_v1(response)


def evaluate_covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1(
    *,
    repo_root: Path,
) -> dict[str, object]:
    """Return the deterministic contract/readiness decision without side effects."""

    try:
        state = _validate_repository_state(repo_root)
        evidence_records = _evidence_records(repo_root)
        _validate_runtime_contract(repo_root)
        predecessor = _validate_predecessor_evidence(repo_root)
        spec = _contract_spec_v1()
        _validate_contract_spec_v1(spec)
        synthetic_rows = _verify_synthetic_truth_table_v1()
        manifest = _validate_artifacts(repo_root, evidence_records)

        if (
            manifest["authority_coverages"] != {
                "warhead_atom_set": predecessor["warhead_coverage"],
                "ligand_internal_warhead_boundary": predecessor["boundary_coverage"],
                "complete_primary_role_assignment": predecessor["role_coverage"],
                "minimal_seed_or_anchor": predecessor["seed_coverage"],
            }
            or manifest["readiness"] != {
                "role_task_mask_contract_resolved": True,
                "primary_role_authority_complete": False,
                "minimal_seed_anchor_authority_complete": False,
                "canonical_mask_tensors_materialized": False,
                "ready_for_tensor_materialization_smoke": False,
                "ready_for_model_integration": False,
                "ready_for_training": False,
            }
        ):
            raise ValueError(_ERROR)

        task_table = [
            {
                "task_id": task_id,
                "semantic_name": semantic,
                "display_alias": alias,
                "generated_primary_roles": list(generated),
                "fixed_primary_roles": list(fixed),
            }
            for task_id, semantic, alias, generated, fixed in _TASK_SPECS
        ]
        role_table = [
            {"role_id": role_id, "semantic_name": name}
            for role_id, name in _PRIMARY_ROLES
        ]
        field_registry = _field_rows()
        response: dict[str, object] = {
            "contract_version": _VERSION,
            "error_contract": _ERROR,
            "repository": _REPOSITORY,
            "branch": state["branch"],
            "base_head": state["head"],
            "base_head_subject": state["subject"],
            "origin_main": state["origin"],
            "ahead": state["ahead"],
            "behind": state["behind"],
            "contract_lifecycle_profile": state["contract_lifecycle_profile"],
            "contract_commit": state["contract_commit"],
            "contract_committed": state["contract_committed"],
            "contract_published": state["contract_published"],
            "ready_for_contract_commit_review": state["ready_for_contract_commit_review"],
            "candidate_paths": list(_CANDIDATE_PATHS),
            "evidence_records": evidence_records,
            "predecessor_open_issue": predecessor["predecessor_issue"],
            "predecessor_open_issue_reason": predecessor["predecessor_issue_reason"],
            "canonical_role_vocabulary": role_table,
            "canonical_role_count": len(role_table),
            "canonical_task_truth_table": task_table,
            "canonical_task_count": len(task_table),
            "semantic_long_names_authoritative": True,
            "display_aliases_runtime_input_allowed": False,
            "base_task_mask_matches_runtime": True,
            "task_c_base_generation": ["scaffold", "linker", "warhead"],
            "task_c_base_fixed": [],
            "task_c_seed_conditioning_semantics": "orthogonal_conditioning_sidecar_does_not_change_base_masks_or_active_loss",
            "minimal_seed_is_primary_role": False,
            "minimal_seed_is_canonical_task": False,
            "field_contract_registry": field_registry,
            "field_contract_count": len(field_registry),
            "runtime_lig_fixed_polarity": "1=fixed|0=generated",
            "future_adapter_relation": "lig_fixed=ligand_base_fixed_mask.squeeze(-1).cast(int64)",
            "active_diffusion_loss_rule": "base_generation AND role_valid AND canonical_task_valid AND sample_training_admitted",
            "anchor_distance_semantic_name": "ligand_to_target_reactive_atom_distance_angstrom",
            "anchor_distance_reference": "target_residue_reactive_atom",
            "anchor_distance_unit": "angstrom",
            "anchor_distance_frame": "centering_invariant_euclidean_distance",
            "anchor_distance_shape": "[N_ligand,1]",
            "warhead_atom_set_authority_coverage": predecessor["warhead_coverage"],
            "ligand_internal_warhead_boundary_authority_coverage": predecessor["boundary_coverage"],
            "role_task_mask_contract_resolved": True,
            "primary_role_authority_complete": predecessor["primary_role_authority_complete"],
            "minimal_seed_anchor_authority_complete": predecessor["seed_authority_complete"],
            "role_assignment_authority_coverage": predecessor["role_coverage"],
            "minimal_seed_anchor_authority_coverage": predecessor["seed_coverage"],
            "base_task_masks_derivable": predecessor["primary_role_authority_complete"],
            "synthetic_base_task_masks_derivable": bool(synthetic_rows),
            "real_role_task_mask_materialization_ready": False,
            "canonical_mask_tensors_materialized": False,
            "ready_for_tensor_materialization_smoke": False,
            "ready_for_model_integration": False,
            "ready_for_training": False,
            "checkpoint_atom_feature_width": 10,
            "checkpoint_channel_order": _CHECKPOINT_CHANNEL_ORDER,
            "new_role_task_seed_tensors_are_sidecars": True,
            "checkpoint_feature_concatenation_allowed": False,
            "model_state_dict_changed": False,
            "checkpoint_migration_required": False,
            "feature_semantics_contract_audit_completed": True,
            "unknown_atom_policy_contract_resolved": True,
            "unknown_atom_runtime_enforcement_integrated": False,
            "silent_zero_vector_fallback_allowed": False,
            "unsupported_nonhydrogen_policy": "reject_sample_fail_closed",
            "final_training_feature_semantics_revalidation_required": True,
            "failure_matrix_case_count": len(_FAILURE_CASES),
            "failure_matrix_cases": [case for _identifier, case, _guard in _FAILURE_CASES],
            "synthetic_truth_table_verified": True,
            "candidate_scope_verified": True,
            "runtime_mask_changed": False,
            "dataloader_changed": False,
            "model_changed": False,
            "forward_changed": False,
            "loss_changed": False,
            "tensor_materialization_performed": False,
            "checkpoint_access_performed": False,
            "runtime_smoke_performed": False,
            "training_performed": False,
            "fine_tuning_performed": False,
            "parameter_update_performed": False,
            "reward_or_rl_performed": False,
            "generated_evidence_files": list(_GENERATED_EVIDENCE_PATHS),
            "recommended_next_increment": predecessor["recommended_next_increment"],
            "commit_created": False,
            "push_performed": False,
            "response_field_count": len(_RESPONSE_FIELDS),
            "response_sha256": "",
        }
        if tuple(response) != _RESPONSE_FIELDS:
            raise ValueError(_ERROR)
        response["response_sha256"] = _sha256(
            _canonical_json_bytes({key: response[key] for key in _RESPONSE_FIELDS[:-1]})
        )
        _validate_response_v1(response)
        return response
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
