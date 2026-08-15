"""Build the Current11 Task 2 compiler/remap-context handoff contract gate V1."""

from __future__ import annotations

import ast
import hashlib
import json
import stat
import subprocess
from pathlib import Path
from typing import Mapping, NoReturn, Sequence


__all__ = (
    "build_covapie_current11_task2_compiler_remap_context_handoff_contract_gate_v1",
)

_ERROR = (
    "COVAPIE_CURRENT11_TASK2_COMPILER_REMAP_CONTEXT_HANDOFF_"
    "CONTRACT_GATE_V1_ERROR"
)
_BASE_COMMIT = "e9a650dd6ee1f53916d412c1540f0c896188083f"
_BRANCH = "main"
_HEAD_SUBJECT = "add CovaPIE Current11 Task2 remap adapter context v1"
_SELECTED_OPTION = "B"
_ARCHITECTURE = (
    "additive_compiler_context_successor_from_published_remap_context_v1"
)

_MODULE_PATH = (
    "src/covalent_ext/"
    "covapie_current11_task2_compiler_remap_context_handoff_contract_gate_v1.py"
)
_SCRIPT_PATH = (
    "scripts/"
    "check_covapie_current11_task2_compiler_remap_context_handoff_contract_gate_v1.py"
)
_TEST_PATH = (
    "tests/"
    "test_covapie_current11_task2_compiler_remap_context_handoff_contract_gate_v1.py"
)
_GUIDE_PATH = (
    "docs/"
    "covapie_current11_task2_compiler_remap_context_handoff_contract_gate_v1_guide.md"
)
_REPOSITORY_EXACT4 = (_MODULE_PATH, _SCRIPT_PATH, _TEST_PATH, _GUIDE_PATH)

_MANIFEST = (
    "current11_task2_compiler_remap_context_handoff_contract_manifest.json"
)
_CONTEXT_SCHEMA = (
    "current11_task2_compiler_remap_context_handoff_context_schema.json"
)
_API_AND_ERROR = (
    "current11_task2_compiler_remap_context_handoff_api_and_error_contract.json"
)
_REFERENCE_VECTORS = (
    "current11_task2_compiler_remap_context_handoff_reference_vectors.json"
)
_ACCEPTANCE_MATRIX = (
    "current11_task2_compiler_remap_context_handoff_acceptance_matrix.json"
)
_REPORT = (
    "current11_task2_compiler_remap_context_handoff_contract_gate_report.json"
)
_ARTIFACT_NAMES = (
    _MANIFEST,
    _CONTEXT_SCHEMA,
    _API_AND_ERROR,
    _REFERENCE_VECTORS,
    _ACCEPTANCE_MATRIX,
    _REPORT,
)
_STABLE_NAMES = _ARTIFACT_NAMES[:5]
_STABLE_DOMAIN = (
    b"COVAPIE_CURRENT11_TASK2_COMPILER_REMAP_CONTEXT_HANDOFF_"
    b"CONTRACT_GATE_V1\0"
)
_KNOWN_VECTOR_DOMAIN = (
    b"COVAPIE_CURRENT11_TASK2_COMPILER_REMAP_CONTEXT_HANDOFF_"
    b"KNOWN_VECTOR_V1\0"
)
_FUTURE_SEAL_DOMAIN = (
    "COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_"
    "FROM_REMAP_CONTEXT_V1\x00"
)

_DESIGN_REPORT_RELATIVE = (
    "review-scratch/current11-task2-compiler-remap-context-handoff-design-v1/"
    "compiler_remap_context_handoff_design_report.md"
)
_DESIGN_REPORT_IDENTITY = {
    "bytes": 39895,
    "LF": 524,
    "sha256": "10d5c2245b54665f83cab2782651a18ab7569628d07c07697841887e3e27d47e",
    "mode": "0644",
}

_OWNER_SPECS = (
    {
        "owner": "published_remap_adapter_context_v1",
        "path": (
            "src/covalent_ext/"
            "covapie_current11_task2_batch_index_remap_adapter_context_v1.py"
        ),
        "last_change_commit": _BASE_COMMIT,
        "bytes": 43578,
        "LF": 1211,
        "sha256": "1eb764aa4425ad857d59daa625e610a5e015a0a272594f332254998bed8191e6",
        "git_blob": "b4a68ff8193666a3d22f777b111c3ae01178ef8d",
    },
    {
        "owner": "published_remap_hot_loop_contract_gate_v1",
        "path": (
            "src/covalent_ext/"
            "covapie_current11_task2_batch_index_remap_adapter_hot_loop_"
            "contract_gate_v1.py"
        ),
        "last_change_commit": "68cf69574d3f97c57f2c3873c77bc8250f5cbad0",
        "bytes": 58101,
        "LF": 1482,
        "sha256": "5acc793c40d1a899371fd08a02713cd8f1d6105cce04d177317bf03bbdb3cd29",
        "git_blob": "8ba056493e5db83c34e342f3424179ecfe729d77",
    },
    {
        "owner": "historical_compiler_context_v1",
        "path": (
            "src/covalent_ext/"
            "covapie_current11_task2_batch_descriptor_compiler_context_v1.py"
        ),
        "last_change_commit": "83beddbcd468caeb38a6b8a86c15f31dfd430d79",
        "bytes": 11363,
        "LF": 334,
        "sha256": "6f08b17a164d7e58b8ba7b9be9408a1a3f5d64f357bc24f2e52469fed763fd34",
        "git_blob": "8388f883f2d7bca4035485bb541fa596e14c5bb8",
    },
    {
        "owner": "historical_compiler_context_contract_gate_v1",
        "path": (
            "src/covalent_ext/"
            "covapie_current11_task2_batch_descriptor_compiler_context_"
            "contract_gate_v1.py"
        ),
        "last_change_commit": "df3f570d8ec98440856bdfa311387443b24ca1fa",
        "bytes": 38645,
        "LF": 984,
        "sha256": "ffb6096253e9e4cf664a01d1aac796aacb721d5cad82555aee33988f1fffce81",
        "git_blob": "02976f800b6eeb4d0b7be30842e5a4a5f3b812dd",
    },
    {
        "owner": "compiler_v1_current_shared_kernel_bytes",
        "path": (
            "src/covalent_ext/"
            "covapie_current11_task2_batch_descriptor_compiler_v1.py"
        ),
        "last_change_commit": "ac22f9cdb8438cf97e3da6e4668e9b124d484f95",
        "bytes": 31298,
        "LF": 687,
        "sha256": "a7a232a4f344e5cbac152ae8cc51921f4d9bf07deaaab0d55f1ce950e67b524a",
        "git_blob": "26037347244a7b33d23b475d32f565e4580eb7fe",
    },
    {
        "owner": "runtime_batch_observation_extractor_v1",
        "path": (
            "src/covalent_ext/"
            "covapie_current11_runtime_batch_observation_extractor_v1.py"
        ),
        "last_change_commit": "463c481b65a68442f19b9f1b417ce2325434785f",
        "bytes": 9229,
        "LF": 287,
        "sha256": "aa129304b350e1089411803c90890c638526e6e3db79bd55a9460b7a1960c5b9",
        "git_blob": "1f7b978eaa111c7cdd296d256c8cfc6d18242802",
    },
)

_ADAPTER_PUBLIC_EXACT2 = (
    "build_covapie_current11_task2_batch_index_remap_adapter_context_v1",
    "remap_covapie_current11_task2_batch_index_with_context_v1",
)
_ADAPTER_MATERIALIZER = "_validate_context_and_materialize"
_ADAPTER_MATERIALIZER_SIGNATURE = (
    "(context: object) -> tuple[dict[str, object], list[dict[str, object]], "
    "dict[str, object]]"
)
_COMPILER_CONTEXT_PUBLIC_EXACT2 = (
    "build_covapie_current11_task2_batch_descriptor_compiler_context_v1",
    "compile_covapie_current11_task2_batch_descriptor_with_context_v1",
)
_COMPILER_KERNEL = "_compile_with_verified_authority_v1"
_COMPILER_KERNEL_SIGNATURE = (
    "(*, authority: tuple[dict[str, object], list[dict[str, object]], "
    "dict[str, bool]], observation: object) -> dict[str, object]"
)

_FUTURE_MODULE = (
    "src/covalent_ext/"
    "covapie_current11_task2_batch_descriptor_compiler_context_from_"
    "remap_context_v1.py"
)
_FUTURE_PUBLIC_EXACT2 = (
    "build_covapie_current11_task2_batch_descriptor_compiler_context_from_"
    "remap_context_v1",
    "compile_covapie_current11_task2_batch_descriptor_with_remap_handoff_"
    "context_v1",
)
_FUTURE_BUILD_SIGNATURE = "(*, remap_context: object) -> object"
_FUTURE_COMPILE_SIGNATURE = (
    "(*, context: object, observation: dict[str, object]) -> dict[str, object]"
)
_FUTURE_ERROR = (
    "COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_"
    "FROM_REMAP_CONTEXT_V1_ERROR"
)
_FUTURE_CONTEXT_FIELDS = (
    "context_schema_version",
    "context_contract_version",
    "adapter_context_owner_module",
    "adapter_context_owner_schema_version",
    "adapter_context_owner_contract_version",
    "adapter_context_owner_source_sha256",
    "adapter_context_private_materializer",
    "compiler_module",
    "compiler_product_commit",
    "compiler_source_sha256",
    "compiler_private_kernel",
    "compiler_contract_digest",
    "source_contract_digest",
    "provider_digest",
    "historical_authority_compatibility_digest",
    "context_freshness_model",
    "source_exact10",
    "identity_provider_exact11",
    "readiness_template",
    "construction_seal",
)
_FUTURE_CONTEXT_SCHEMA_VERSION = (
    "covapie_current11_task2_batch_descriptor_compiler_context_from_"
    "remap_context_v1"
)
_FUTURE_FRESHNESS_MODEL = "explicit_rebuild_from_caller_owned_remap_context"

_SOURCE_FIELDS = (
    "schema_version",
    "source_projection_digest",
    "source_payload_digest",
    "parser_schema_version",
    "collate_schema_version",
    "source_sample_order",
    "source_pair_values_int64",
    "source_sample_offsets_int64",
    "source_entry_validity_bool",
    "source_sample_validity_bool",
)
_EXACT18_FIELDS = (
    *_SOURCE_FIELDS,
    "batch_sample_order",
    "batch_sample_atom_identity_tables",
    "batch_role_lengths",
    "batch_role_offsets",
    "batch_membership_masks",
    "joint_layout_descriptor",
    "debug_coordinates",
    "debug_rank_metadata",
)
_SOURCE_MAPPING = (
    ("schema_version", "adapter/compiler frozen schema equality", "constant"),
    (
        "source_projection_digest",
        'remap semantic["projection_instance_digest"]',
        "rename_only",
    ),
    (
        "source_payload_digest",
        'remap semantic["payload_bundle_digest"]',
        "rename_only",
    ),
    (
        "parser_schema_version",
        "adapter/compiler frozen parser equality",
        "constant",
    ),
    (
        "collate_schema_version",
        "adapter/compiler frozen collate equality",
        "constant",
    ),
    ("source_sample_order", 'source_contract["sample_order"]', "deep_copy_rename_only"),
    (
        "source_pair_values_int64",
        'source_contract["pair_values_source_row_indices"]',
        "deep_copy_rename_only",
    ),
    (
        "source_sample_offsets_int64",
        'source_contract["sample_pair_offsets"]',
        "deep_copy_rename_only",
    ),
    (
        "source_entry_validity_bool",
        'source_contract["entry_validity"]',
        "deep_copy_rename_only",
    ),
    (
        "source_sample_validity_bool",
        'source_contract["sample_validity"]',
        "deep_copy_rename_only",
    ),
)
_SOURCE_CANONICAL_BYTES = 2735
_SOURCE_CANONICAL_SHA256 = (
    "21bc3eb8a7b2f4b569f17d102715726eda09aed6467782e5477a7cfa285f98f2"
)
_SOURCE_COMPONENT_DIGEST = (
    "ffbd6311d0ae44e0729cf6c659493f14945414d7ce6aac3ddea107a321773aba"
)

_IDENTITY_FIELDS = (
    "sample_index_row_id",
    "sample_preparation_input_id",
    "pdb_id",
    "ligand_comp_id",
)
_ROLE_ORDER = ("pocket", "ligand")
_ROLE_RECORD_FIELDS = (
    "SHA256",
    "committed_projection_matrix_local_index",
    "explicit_hydrogen_count",
    "relative_path",
    "retained_heavy_count",
    "role",
    "root_kind",
    "row_count",
    "row_order_digest",
    "row_order_version",
    "selected_atom_identity",
    "selected_parser_local_index",
    "selected_row_retained",
    "selected_source_row_index_0based",
    "source_to_parser_exact_one",
    "unsupported_nonhydrogen_count",
    "parser_output_atom_count",
    "source_to_parser_local",
)
_ROLE_REQUIRED_FIELDS = (
    "root_kind",
    "relative_path",
    "SHA256",
    "row_count",
    "row_order_digest",
    "row_order_version",
    "selected_source_row_index_0based",
    "selected_parser_local_index",
    "parser_output_atom_count",
    "source_to_parser_local",
    "selected_atom_identity",
)
_ATOM_IDENTITY_FIELDS = (
    "atom_site_id",
    "atom_name",
    "type_symbol",
    "residue_name_or_ligand_comp_id",
    "auth_asym_id",
    "auth_seq_id",
    "label_asym_id",
    "label_seq_id",
)
_PROVIDER_CANONICAL_BYTES = 23364
_PROVIDER_CANONICAL_SHA256 = (
    "1345c9da88fd516677c1730d129ab8a19f487eb0862fa7b7580481bc15a43bc5"
)
_PROVIDER_DIGEST = (
    "a6193bfe7099b9c9436036f75101df31638739a893b598af8ac021bfa46aa186"
)
_PROVIDER_COMPONENT_DIGEST = (
    "1c06fdec0313c481c60eadb9b6c20d278c682908c3681f99995f8fee5109564a"
)

_READINESS_VALUES = {
    "base_atom_feature_width_change_required": False,
    "base_model_parameter_shape_change_required": False,
    "checkpoint_bytes_read": False,
    "checkpoint_state_dict_change_required": False,
    "compiler_input_schema_frozen": True,
    "compiler_output_schema_frozen": True,
    "compiler_reference_composition_passed": True,
    "compiler_status_vocabulary_frozen": True,
    "egnn_or_se3_backbone_change_required": False,
    "feature_semantics_reaudit_required_before_training": True,
    "formal_runtime_carrier_verified": True,
    "identity_provider_verified": True,
    "ready_for_dataloader_integration": False,
    "ready_for_loss_integration": False,
    "ready_for_model_integration": False,
    "ready_for_runtime_batch_observation_extractor_design": True,
    "ready_for_task2_batch_descriptor_compiler_implementation": False,
    "ready_for_training": False,
    "runtime_batch_observation_extractor_implemented": False,
    "source_contract_verified": True,
    "task2_batch_descriptor_compiler_contract_designed": True,
    "task2_batch_descriptor_compiler_contract_gate_implemented": True,
    "task2_batch_descriptor_compiler_contract_gate_passed": True,
    "task2_batch_descriptor_compiler_implemented": True,
}
_READINESS_COMPONENT_DIGEST = (
    "8d6bcae9f365f6c802e9109a8c1e53c1b85c8c8c23f04d005a162c09fcdb6890"
)
_PROVENANCE_COMPONENT_DIGEST = (
    "fb07d38554cec596679ab00bd80d35d392bddd60d0d07e9310439501e498a109"
)
_AUTHORITY_COMPATIBILITY_DIGEST = (
    "e3c7c14e5a94db2bf59b5195ae6902d7fd7269e58a8690589962548860348d44"
)
_COMPILER_CONTRACT_DIGEST = (
    "bb9705173523377f28966064eec7393fbf337dce9ef6c70d2e3fbca3038e2dfd"
)
_SOURCE_CONTRACT_DIGEST = (
    "2c6259312a3292181f00ebbaf787fab05e5a97e5b5475243f2fa8461b54dcdc6"
)

_OUTPUT10_FIELDS = (
    "schema_version",
    "compiler_status",
    "failure_reason",
    "adapter_input_exact18",
    "batch_sample_key_outcomes",
    "source_contract_digest",
    "identity_provider_digest",
    "runtime_schema_binding",
    "provenance",
    "readiness",
)
_SUCCESS_CASES = ("canonical", "reversed", "subset_10_4_0", "singleton_10")
_HARD_FAILURES = (
    ("source_contract_override", "SOURCE_CONTRACT_MISMATCH"),
    ("duplicate_runtime_key", "BATCH_SAMPLE_KEY_DUPLICATED"),
    ("wrong_ligand_length", "ROLE_LENGTH_MISMATCH"),
    ("wrong_ligand_membership", "MEMBERSHIP_MASK_MISMATCH"),
    ("unknown_joint_descriptor", "BATCH_OBSERVATION_SCHEMA_MISMATCH"),
)
_CONTEXT_FAILURES = (
    "wrong_type",
    "wrong_schema_or_version",
    "wrong_owner_lineage",
    "wrong_provider_digest",
    "wrong_authority_compatibility_digest",
    "tampered_frozen_graph",
    "wrong_seal",
    "reconstructed_or_unsealed_context",
)
_CANONICAL_MASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
_ZERO_CALL_VECTOR = {
    "public_remap_context_builder_calls": 0,
    "public_remap_fast_calls": 0,
    "adapter_private_materializer_calls": 0,
    "old_compiler_authority_calls": 0,
    "stable5_parser_calls": 0,
    "reconciliation_calls": 0,
    "successor_calls": 0,
    "B2_state_mount_transition_public_build_calls": 0,
    "formal_validation_calls": 0,
    "historical_compiler_contract_public_build_calls": 0,
}
_REAL_HEAVY_CALL_COUNTS = {
    "real_remap_context_builds": 0,
    "real_remap_fast_calls": 0,
    "old_compiler_authority_calls": 0,
    "historical_compiler_gate_calls": 0,
    "reconciliation_calls": 0,
    "successor_calls": 0,
    "B2_calls": 0,
    "formal_validation_calls": 0,
}

_NEGATIVE_CASES = (
    ("adapter_context_source_identity_drift", "fail_gate"),
    ("adapter_public_exact2_drift", "fail_gate"),
    ("private_helper_missing", "fail_gate"),
    ("private_helper_signature_drift", "fail_gate"),
    ("compiler_context_source_drift", "fail_gate"),
    ("compiler_context_contract_source_drift", "fail_gate"),
    ("compiler_shared_kernel_source_drift", "fail_gate"),
    ("private_compiler_kernel_signature_drift", "fail_gate"),
    ("design_report_identity_drift", "fail_gate"),
    ("source_exact10_field_missing", "reject_contract"),
    ("source_exact10_reordered", "reject_contract"),
    ("source_mapping_wrong_source_key", "reject_contract"),
    ("source_bool_int_type_collapse", "reject_contract"),
    ("provider_length_not_11", "reject_contract"),
    ("provider_sample_identity_drift", "reject_contract"),
    ("provider_role_order_drift", "reject_contract"),
    ("provider_role_field_missing", "reject_contract"),
    ("provider_digest_drift", "reject_contract"),
    ("selected_atom_exact8_drift", "reject_contract"),
    ("source_to_parser_local_recomputed_or_mismatched", "reject_contract"),
    ("readiness_missing_key", "reject_contract"),
    ("readiness_reordered", "reject_contract"),
    ("stale_readiness_modernized", "reject_contract"),
    ("authority_compatibility_digest_drift", "reject_contract"),
    ("future_builder_adds_repo_root", "reject_future_product"),
    ("future_builder_adds_state_root", "reject_future_product"),
    ("future_adapter_public_builder_call_allowed", "reject_future_product"),
    ("future_old_compiler_authority_call_allowed", "reject_future_product"),
    ("future_stable5_parse_allowed", "reject_future_product"),
    ("future_materializer_per_batch_allowed", "reject_future_product"),
    ("bridge_retains_remap_context_object", "reject_future_product"),
    ("output10_adds_bridge_metadata", "reject_future_product"),
    ("hard_failure_normalized", "reject_future_product"),
    ("device_risk_runtime_proven_before_implementation", "reject_readiness"),
    ("dataloader_marked_ready", "reject_readiness"),
    ("training_marked_ready", "reject_readiness"),
)

_PATH_TYPE = type(Path())


class _ContractInvariantError(Exception):
    pass


def _fail() -> NoReturn:
    raise _ContractInvariantError()


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _validate_json_value(value: object, active: set[int] | None = None) -> None:
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) not in (dict, list):
        _fail()
    active = set() if active is None else active
    marker = id(value)
    if marker in active:
        _fail()
    active.add(marker)
    try:
        if type(value) is list:
            for item in value:
                _validate_json_value(item, active)
            return
        for key, item in value.items():
            if type(key) is not str:
                _fail()
            _validate_json_value(item, active)
    finally:
        active.remove(marker)


def _canonical_json(value: object) -> bytes:
    _validate_json_value(value)
    try:
        payload = (
            json.dumps(
                value,
                sort_keys=True,
                indent=2,
                ensure_ascii=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise _ContractInvariantError() from error
    if (
        not payload
        or len(payload) >= 1024 * 1024
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\0" in payload
        or b"\r" in payload
        or not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
    ):
        _fail()
    return payload


def _compact_json(value: object) -> bytes:
    _validate_json_value(value)
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise _ContractInvariantError() from error


def _strict_json(payload: bytes) -> dict[str, object]:
    try:
        value = json.loads(
            payload.decode("utf-8"), parse_constant=lambda _value: _fail()
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise _ContractInvariantError() from error
    if type(value) is not dict or _canonical_json(value) != payload:
        _fail()
    return value


def _framed_digest(domain: bytes, value: object) -> str:
    payload = _compact_json(value)
    digest = hashlib.sha256(domain)
    digest.update(len(payload).to_bytes(8, "big", signed=False))
    digest.update(payload)
    return digest.hexdigest()


def _stable_digest(artifacts: Mapping[str, bytes]) -> str:
    digest = hashlib.sha256(_STABLE_DOMAIN)
    for name in _STABLE_NAMES:
        encoded = name.encode("utf-8")
        payload = artifacts[name]
        digest.update(len(encoded).to_bytes(8, "big", signed=False))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big", signed=False))
        digest.update(payload)
    return digest.hexdigest()


def _require_root(path: Path) -> Path:
    if type(path) is not _PATH_TYPE or not path.is_absolute():
        _fail()
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise _ContractInvariantError() from error
    if (
        resolved != path
        or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
    ):
        _fail()
    return path


def _run_git(repo_root: Path, arguments: Sequence[str]) -> str:
    try:
        completed = subprocess.run(
            ("git", *arguments),
            cwd=repo_root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="strict",
            check=False,
        )
    except (OSError, UnicodeError) as error:
        raise _ContractInvariantError() from error
    if completed.returncode != 0 or completed.stderr:
        _fail()
    return completed.stdout


def _safe_repository_exact4(repo_root: Path) -> None:
    for relative in _REPOSITORY_EXACT4:
        path = repo_root / relative
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
            payload.decode("utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise _ContractInvariantError() from error
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o644
            or not payload
            or len(payload) >= 1024 * 1024
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\0" in payload
            or b"\r" in payload
            or not payload.endswith(b"\n")
            or payload.endswith(b"\n\n")
            or any(
                line.rstrip(b"\r\n").endswith((b" ", b"\t"))
                for line in payload.splitlines(keepends=True)
            )
        ):
            _fail()


def _repository_lifecycle(repo_root: Path) -> tuple[str, dict[str, object]]:
    branch = _run_git(repo_root, ("branch", "--show-current")).strip()
    head = _run_git(repo_root, ("rev-parse", "HEAD")).strip()
    origin = _run_git(repo_root, ("rev-parse", "origin/main")).strip()
    relation = _run_git(
        repo_root, ("rev-list", "--left-right", "--count", "HEAD...origin/main")
    ).strip()
    subject = _run_git(repo_root, ("log", "-1", "--format=%s", "HEAD")).strip()
    if branch != _BRANCH or relation.count("\t") != 1:
        _fail()
    ahead_text, behind_text = relation.split("\t")
    if not ahead_text.isdigit() or not behind_text.isdigit():
        _fail()
    status = _run_git(
        repo_root, ("status", "--porcelain=v1", "--untracked-files=all")
    ).splitlines()
    index = _run_git(
        repo_root, ("ls-files", "--stage", "--", *_REPOSITORY_EXACT4)
    ).splitlines()
    expected_untracked = {f"?? {relative}" for relative in _REPOSITORY_EXACT4}
    if set(status) == expected_untracked and len(status) == len(_REPOSITORY_EXACT4):
        if (
            index
            or head != _BASE_COMMIT
            or origin != _BASE_COMMIT
            or ahead_text != "0"
            or behind_text != "0"
            or subject != _HEAD_SUBJECT
        ):
            _fail()
        lifecycle = "precommit-untracked"
    elif not status and len(index) == len(_REPOSITORY_EXACT4):
        _run_git(repo_root, ("merge-base", "--is-ancestor", _BASE_COMMIT, "HEAD"))
        seen: set[str] = set()
        for row in index:
            try:
                metadata, relative = row.split("\t", 1)
                mode, blob, stage = metadata.split()
            except ValueError as error:
                raise _ContractInvariantError() from error
            if (
                relative not in _REPOSITORY_EXACT4
                or relative in seen
                or mode != "100644"
                or stage != "0"
                or _run_git(
                    repo_root, ("hash-object", "--no-filters", "--", relative)
                ).strip()
                != blob
            ):
                _fail()
            seen.add(relative)
        if seen != set(_REPOSITORY_EXACT4):
            _fail()
        lifecycle = "clean-tracked-successor"
    else:
        _fail()
    _safe_repository_exact4(repo_root)
    return lifecycle, {
        "branch": branch,
        "head": head,
        "origin_main": origin,
        "ahead": int(ahead_text),
        "behind": int(behind_text),
        "head_subject": subject,
    }


def _literal_assignment(tree: ast.Module, name: str) -> object:
    matches = [
        node
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        and (
            isinstance(node.target, ast.Name)
            if isinstance(node, ast.AnnAssign)
            else len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
        )
        and (
            node.target.id
            if isinstance(node, ast.AnnAssign)
            else node.targets[0].id
        )
        == name
    ]
    if len(matches) != 1:
        _fail()
    try:
        return ast.literal_eval(matches[0].value)
    except (ValueError, TypeError) as error:
        raise _ContractInvariantError() from error


def _function_signature(tree: ast.Module, name: str) -> str:
    matches = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    ]
    if len(matches) != 1 or isinstance(matches[0], ast.AsyncFunctionDef):
        _fail()
    function = matches[0]
    if function.returns is None:
        _fail()
    return f"({ast.unparse(function.args)}) -> {ast.unparse(function.returns)}"


def _function_node(tree: ast.Module, name: str) -> ast.FunctionDef:
    matches = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    if len(matches) != 1:
        _fail()
    return matches[0]


def _read_verified_source(
    repo_root: Path, spec: Mapping[str, object]
) -> tuple[str, ast.Module, dict[str, object]]:
    relative = spec.get("path")
    if type(relative) is not str:
        _fail()
    path = repo_root / relative
    try:
        metadata = path.lstat()
        payload = path.read_bytes()
        source = payload.decode("utf-8")
        tree = ast.parse(source, filename=relative)
    except (OSError, UnicodeDecodeError, SyntaxError) as error:
        raise _ContractInvariantError() from error
    observed = {
        "owner": spec.get("owner"),
        "path": relative,
        "last_change_commit": _run_git(
            repo_root, ("log", "-1", "--format=%H", "--", relative)
        ).strip(),
        "bytes": len(payload),
        "LF": payload.count(b"\n"),
        "sha256": _sha256(payload),
        "git_blob": _run_git(
            repo_root, ("hash-object", "--no-filters", "--", relative)
        ).strip(),
    }
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or observed != dict(spec)
        or _run_git(repo_root, ("rev-parse", f"HEAD:{relative}")).strip()
        != spec.get("git_blob")
    ):
        _fail()
    return source, tree, observed


def _validate_function_body_symbols(
    function: ast.FunctionDef, *, required_names: set[str]
) -> None:
    names = {node.id for node in ast.walk(function) if isinstance(node, ast.Name)}
    if not required_names.issubset(names):
        _fail()


def _verify_design_report(state_root: Path) -> dict[str, object]:
    path = state_root / _DESIGN_REPORT_RELATIVE
    try:
        metadata = path.lstat()
        payload = path.read_bytes()
        text = payload.decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise _ContractInvariantError() from error
    observed = {
        "bytes": len(payload),
        "LF": payload.count(b"\n"),
        "sha256": _sha256(payload),
        "mode": f"{stat.S_IMODE(metadata.st_mode):04o}",
    }
    required_fragments = (
        "selected_option=B",
        f"selected_architecture={_ARCHITECTURE}",
        "source_exact10_lossless_mapping=true",
        "provider_exact11_lossless_mapping=true",
        "single_authority_snapshot_shared_between_remap_and_compiler=true",
        "duplicate_stable5_parser_forbidden=true",
        "duplicate_predecessor_acquisition_forbidden=true",
        "ready_for_compiler_remap_context_handoff_contract_gate_implementation=true",
        "ready_for_compiler_remap_context_handoff_implementation=false",
        "feature_semantics_reaudit_required_before_training=true",
        "ready_for_training=false",
        _SOURCE_CANONICAL_SHA256,
        _PROVIDER_CANONICAL_SHA256,
        _PROVIDER_DIGEST,
        _AUTHORITY_COMPATIBILITY_DIGEST,
    )
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or observed != _DESIGN_REPORT_IDENTITY
        or any(fragment not in text for fragment in required_fragments)
    ):
        _fail()
    return {
        "relative_path": _DESIGN_REPORT_RELATIVE,
        **observed,
        "regular_file": True,
        "symlink": False,
    }


def _verify_predecessors(
    repo_root: Path,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    verified: dict[str, tuple[str, ast.Module]] = {}
    identities: list[dict[str, object]] = []
    for spec in _OWNER_SPECS:
        source, tree, identity = _read_verified_source(repo_root, spec)
        owner = spec["owner"]
        if type(owner) is not str:
            _fail()
        verified[owner] = (source, tree)
        identities.append(identity)

    adapter_source, adapter_tree = verified["published_remap_adapter_context_v1"]
    if tuple(_literal_assignment(adapter_tree, "__all__")) != _ADAPTER_PUBLIC_EXACT2:
        _fail()
    expected_adapter_signatures = {
        _ADAPTER_PUBLIC_EXACT2[0]: "(*, repo_root: Path, state_root: Path) -> object",
        _ADAPTER_PUBLIC_EXACT2[1]: (
            "(*, context: object, adapter_input: dict[str, object]) -> "
            "dict[str, object]"
        ),
        _ADAPTER_MATERIALIZER: _ADAPTER_MATERIALIZER_SIGNATURE,
    }
    for name, expected in expected_adapter_signatures.items():
        if _function_signature(adapter_tree, name) != expected:
            _fail()
    if _ADAPTER_MATERIALIZER in _ADAPTER_PUBLIC_EXACT2:
        _fail()
    materializer = _function_node(adapter_tree, _ADAPTER_MATERIALIZER)
    _validate_function_body_symbols(
        materializer,
        required_names={
            "_AdapterContext",
            "_FrozenDictionary",
            "_deep_thaw",
            "_construction_seal",
        },
    )
    classes = {
        node.name: node
        for node in adapter_tree.body
        if isinstance(node, ast.ClassDef)
    }
    context_class = classes.get("_AdapterContext")
    if context_class is None:
        _fail()
    context_fields = tuple(
        node.target.id
        for node in context_class.body
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
    )
    if context_fields != ("_semantic", "_seal"):
        _fail()
    if (
        _literal_assignment(adapter_tree, "CONTEXT_SCHEMA_VERSION")
        != "covapie_current11_task2_batch_index_remap_adapter_context_v1"
        or _literal_assignment(adapter_tree, "CONTEXT_CONTRACT_VERSION")
        != "19649350ac39697138d1c38155a762403fa148db5d7f9ebc518466756c40d1dc"
        or "type(context) is not _AdapterContext" not in adapter_source
        or "_construction_seal(semantic) != context._seal" not in adapter_source
    ):
        _fail()

    unused_context_source, compiler_context_tree = verified[
        "historical_compiler_context_v1"
    ]
    del unused_context_source
    if (
        tuple(_literal_assignment(compiler_context_tree, "__all__"))
        != _COMPILER_CONTEXT_PUBLIC_EXACT2
        or _function_signature(
            compiler_context_tree, _COMPILER_CONTEXT_PUBLIC_EXACT2[0]
        )
        != "(*, repo_root: Path, state_root: Path) -> object"
        or _function_signature(
            compiler_context_tree, _COMPILER_CONTEXT_PUBLIC_EXACT2[1]
        )
        != _FUTURE_COMPILE_SIGNATURE
        or _literal_assignment(
            compiler_context_tree, "_EXPECTED_AUTHORITY_SNAPSHOT_DIGEST"
        )
        != _AUTHORITY_COMPATIBILITY_DIGEST
    ):
        _fail()

    unused_compiler_source, compiler_tree = verified[
        "compiler_v1_current_shared_kernel_bytes"
    ]
    del unused_compiler_source
    if _function_signature(compiler_tree, _COMPILER_KERNEL) != _COMPILER_KERNEL_SIGNATURE:
        _fail()
    compiler_constants = {
        name: _literal_assignment(compiler_tree, name)
        for name in (
            "_CONTRACT_COMMIT",
            "_CONTRACT_DIGEST",
            "_PROVIDER_DIGEST",
            "_REMAP_CONTRACT_DIGEST",
            "_SOURCE_SCHEMA",
            "_PARSER_SCHEMA",
            "_COLLATE_SCHEMA",
            "_PROJECTION_DIGEST",
            "_PAYLOAD_DIGEST",
            "_EXACT18_FIELDS",
            "_IDENTITY_FIELDS",
            "_ROLE_AUTHORITY_FIELDS",
            "_ATOM_IDENTITY_FIELDS",
            "_OUTPUT_FIELDS",
            "_SOURCE_IDENTITIES",
            "_SOURCE_PAIRS",
        )
    }
    if (
        tuple(compiler_constants["_EXACT18_FIELDS"][:10]) != _SOURCE_FIELDS
        or tuple(compiler_constants["_EXACT18_FIELDS"]) != _EXACT18_FIELDS
        or tuple(compiler_constants["_IDENTITY_FIELDS"]) != _IDENTITY_FIELDS
        or tuple(compiler_constants["_ROLE_AUTHORITY_FIELDS"])
        != _ROLE_REQUIRED_FIELDS
        or tuple(compiler_constants["_ATOM_IDENTITY_FIELDS"])
        != _ATOM_IDENTITY_FIELDS
        or tuple(compiler_constants["_OUTPUT_FIELDS"]) != _OUTPUT10_FIELDS
        or compiler_constants["_PROVIDER_DIGEST"] != _PROVIDER_DIGEST
        or compiler_constants["_CONTRACT_DIGEST"] != _COMPILER_CONTRACT_DIGEST
        or compiler_constants["_REMAP_CONTRACT_DIGEST"]
        != _SOURCE_CONTRACT_DIGEST
    ):
        _fail()

    unused_gate_source, historical_gate_tree = verified[
        "historical_compiler_context_contract_gate_v1"
    ]
    del unused_gate_source
    if (
        _literal_assignment(historical_gate_tree, "_PROVIDER_DIGEST")
        != _PROVIDER_DIGEST
        or _literal_assignment(historical_gate_tree, "_SOURCE_CONTRACT_DIGEST")
        != _SOURCE_CONTRACT_DIGEST
    ):
        _fail()
    return identities, compiler_constants


def _source_fixture(constants: Mapping[str, object]) -> dict[str, object]:
    identities = constants.get("_SOURCE_IDENTITIES")
    pairs = constants.get("_SOURCE_PAIRS")
    if type(identities) is not tuple or type(pairs) is not tuple:
        _fail()
    source = {
        "schema_version": constants.get("_SOURCE_SCHEMA"),
        "source_projection_digest": constants.get("_PROJECTION_DIGEST"),
        "source_payload_digest": constants.get("_PAYLOAD_DIGEST"),
        "parser_schema_version": constants.get("_PARSER_SCHEMA"),
        "collate_schema_version": constants.get("_COLLATE_SCHEMA"),
        "source_sample_order": [
            {
                **dict(zip(_IDENTITY_FIELDS, identity, strict=True)),
                "source_sample_index": index,
            }
            for index, identity in enumerate(identities)
        ],
        "source_pair_values_int64": [list(pair) for pair in pairs],
        "source_sample_offsets_int64": list(range(12)),
        "source_entry_validity_bool": [True] * 11,
        "source_sample_validity_bool": [True] * 11,
    }
    _validate_source_reference(source)
    return source


def _validate_source_reference(source: object) -> None:
    if type(source) is not dict or tuple(source) != _SOURCE_FIELDS:
        _fail()
    samples = source.get("source_sample_order")
    pairs = source.get("source_pair_values_int64")
    offsets = source.get("source_sample_offsets_int64")
    if type(samples) is not list or len(samples) != 11:
        _fail()
    for index, sample in enumerate(samples):
        if (
            type(sample) is not dict
            or tuple(sample) != (*_IDENTITY_FIELDS, "source_sample_index")
            or type(sample.get("source_sample_index")) is not int
            or sample.get("source_sample_index") != index
            or any(type(sample.get(field)) is not str for field in _IDENTITY_FIELDS)
        ):
            _fail()
    if (
        type(pairs) is not list
        or len(pairs) != 11
        or any(
            type(pair) is not list
            or len(pair) != 2
            or any(type(value) is not int or value < 0 for value in pair)
            for pair in pairs
        )
        or type(offsets) is not list
        or offsets != list(range(12))
        or any(type(value) is not int for value in offsets)
    ):
        _fail()
    for field in ("source_entry_validity_bool", "source_sample_validity_bool"):
        values = source.get(field)
        if (
            type(values) is not list
            or len(values) != 11
            or any(type(value) is not bool or value is not True for value in values)
        ):
            _fail()
    compact = _compact_json(source)
    if (
        len(compact) != _SOURCE_CANONICAL_BYTES
        or _sha256(compact) != _SOURCE_CANONICAL_SHA256
        or _framed_digest(
            b"COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_"
            b"SOURCE_COMPONENT_V1\0",
            source,
        )
        != _SOURCE_COMPONENT_DIGEST
    ):
        _fail()


def _provider_contract() -> dict[str, object]:
    contract = {
        "container_type": "built-in list",
        "sample_count": 11,
        "sample_record_field_order": ["sample_identity", "roles"],
        "sample_identity_field_order": list(_IDENTITY_FIELDS),
        "source_sample_index_projection": (
            "removed_only_from_nested_provider_identity_and_retained_in_source_exact10"
        ),
        "role_order": list(_ROLE_ORDER),
        "role_record_field_order": list(_ROLE_RECORD_FIELDS),
        "role_record_field_count": 18,
        "compiler_required_role_field_order": list(_ROLE_REQUIRED_FIELDS),
        "role_records_preserved_without_normalization": True,
        "selected_atom_identity_field_order": list(_ATOM_IDENTITY_FIELDS),
        "source_to_parser_local_rule": (
            "preserve_existing_{str(selected_source_row_index_0based):"
            "selected_parser_local_index}_without_recomputation"
        ),
        "canonical_compact_bytes": _PROVIDER_CANONICAL_BYTES,
        "canonical_sha256": _PROVIDER_CANONICAL_SHA256,
        "historical_provider_digest": _PROVIDER_DIGEST,
        "provider_component_digest": _PROVIDER_COMPONENT_DIGEST,
        "provider_deep_exact": True,
        "provider_digest_matches_historical": True,
        "missing_information_count": 0,
        "lossless_mapping": True,
    }
    _validate_provider_contract(contract)
    return contract


def _validate_provider_contract(contract: object) -> None:
    if type(contract) is not dict:
        _fail()
    if (
        contract.get("container_type") != "built-in list"
        or type(contract.get("sample_count")) is not int
        or contract.get("sample_count") != 11
        or contract.get("sample_record_field_order") != ["sample_identity", "roles"]
        or contract.get("sample_identity_field_order") != list(_IDENTITY_FIELDS)
        or contract.get("role_order") != list(_ROLE_ORDER)
        or contract.get("role_record_field_order") != list(_ROLE_RECORD_FIELDS)
        or contract.get("role_record_field_count") != 18
        or contract.get("compiler_required_role_field_order")
        != list(_ROLE_REQUIRED_FIELDS)
        or contract.get("selected_atom_identity_field_order")
        != list(_ATOM_IDENTITY_FIELDS)
        or contract.get("canonical_compact_bytes") != _PROVIDER_CANONICAL_BYTES
        or contract.get("canonical_sha256") != _PROVIDER_CANONICAL_SHA256
        or contract.get("historical_provider_digest") != _PROVIDER_DIGEST
        or contract.get("provider_component_digest") != _PROVIDER_COMPONENT_DIGEST
        or contract.get("provider_deep_exact") is not True
        or contract.get("provider_digest_matches_historical") is not True
        or contract.get("missing_information_count") != 0
        or contract.get("lossless_mapping") is not True
    ):
        _fail()


def _readiness_reference() -> dict[str, object]:
    values = dict(_READINESS_VALUES)
    _validate_readiness_reference(values)
    return {
        "field_order": list(values),
        "values": values,
        "field_count": 24,
        "component_digest": _READINESS_COMPONENT_DIGEST,
        "historical_stale_values_preserved": {
            "runtime_batch_observation_extractor_implemented": False,
            "ready_for_runtime_batch_observation_extractor_design": True,
        },
        "current_truth_report_only": {
            "runtime_batch_observation_extractor_implemented": True,
        },
    }


def _validate_readiness_reference(values: object) -> None:
    if (
        type(values) is not dict
        or tuple(values) != tuple(sorted(_READINESS_VALUES))
        or values != _READINESS_VALUES
        or len(values) != 24
        or any(type(value) is not bool for value in values.values())
        or values.get("runtime_batch_observation_extractor_implemented") is not False
        or values.get("ready_for_runtime_batch_observation_extractor_design") is not True
        or values.get("ready_for_dataloader_integration") is not False
        or values.get("feature_semantics_reaudit_required_before_training") is not True
        or values.get("ready_for_training") is not False
        or _framed_digest(
            b"COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_"
            b"READINESS_COMPONENT_V1\0",
            values,
        )
        != _READINESS_COMPONENT_DIGEST
    ):
        _fail()


def _provenance_reference(constants: Mapping[str, object]) -> dict[str, object]:
    provenance = {
        "context_schema_version": (
            "covapie_current11_task2_batch_descriptor_compiler_context_v1"
        ),
        "compiler_product_commit": (
            "05e8694eb3cdfe9c1aa4cd9728d4820b7322ba5e"
        ),
        "compiler_contract_commit": constants.get("_CONTRACT_COMMIT"),
        "compiler_contract_digest": _COMPILER_CONTRACT_DIGEST,
        "provider_digest": _PROVIDER_DIGEST,
        "formal_carrier_aggregate": (
            "ef426a6d8dee9678ac15dd62b191e9ef9cfb436a01660bd941bd24392dfa9a18"
        ),
        "formal_npz_sha256": (
            "ea3aa7c94b7c88993493662ad6ba7fd95e547ec62612a072f8248a515657e910"
        ),
        "source_contract_digest": _SOURCE_CONTRACT_DIGEST,
    }
    if (
        _framed_digest(
            b"COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_"
            b"PROVENANCE_COMPONENT_V1\0",
            provenance,
        )
        != _PROVENANCE_COMPONENT_DIGEST
    ):
        _fail()
    return provenance


def _known_vector_semantic(
    *, source: dict[str, object], constants: Mapping[str, object]
) -> dict[str, object]:
    semantic = {
        "source_exact10": source,
        "source_mapping_table": [
            {
                "target_field": field,
                "source_authority": authority,
                "operation": operation,
            }
            for field, authority, operation in _SOURCE_MAPPING
        ],
        "source_canonical_compact_bytes": _SOURCE_CANONICAL_BYTES,
        "source_canonical_sha256": _SOURCE_CANONICAL_SHA256,
        "source_component_digest": _SOURCE_COMPONENT_DIGEST,
        "source_deep_exact": True,
        "source_canonical_bytes_exact": True,
        "provider_exact11_contract": _provider_contract(),
        "readiness_exact24": _readiness_reference(),
        "provenance_template": _provenance_reference(constants),
        "provenance_component_digest": _PROVENANCE_COMPONENT_DIGEST,
        "historical_authority_compatibility_digest": (
            _AUTHORITY_COMPATIBILITY_DIGEST
        ),
        "historical_authority_digest_role": (
            "compiler_authority_compatibility_not_future_bridge_construction_seal"
        ),
        "success_case_ids": list(_SUCCESS_CASES),
        "hard_failure_cases": [
            {"case_id": case_id, "compiler_status": status}
            for case_id, status in _HARD_FAILURES
        ],
        "context_programming_failure_ids": list(_CONTEXT_FAILURES),
        "trusted_owner_helper": {
            "name": _ADAPTER_MATERIALIZER,
            "signature": _ADAPTER_MATERIALIZER_SIGNATURE,
            "call_phase": "bridge_build_only",
            "call_count_per_bridge_build": 1,
            "call_count_per_fast_compile": 0,
        },
        "future_bridge_zero_call_vector": dict(_ZERO_CALL_VECTOR),
        "output10_field_order": list(_OUTPUT10_FIELDS),
        "adapter_input_exact18_field_order": list(_EXACT18_FIELDS),
        "output10_bridge_metadata_added": False,
        "canonical_masks": [
            {"semantic_name": name, "display_alias": alias}
            for name, alias in _CANONICAL_MASKS
        ],
    }
    return semantic


def _semantic_readiness() -> dict[str, bool]:
    return {
        "compiler_remap_context_handoff_contract_designed": True,
        "selected_additive_bridge_architecture_frozen": True,
        "source_exact10_lossless_mapping_frozen": True,
        "provider_exact11_lossless_mapping_frozen": True,
        "historical_readiness_parity_frozen": True,
        "historical_authority_compatibility_digest_frozen": True,
        "adapter_context_public_exact2_frozen": True,
        "adapter_context_private_trusted_owner_handoff_frozen": True,
        "historical_compiler_context_frozen": True,
        "compiler_pure_kernel_reuse_frozen": True,
        "single_authority_snapshot_contract_frozen": True,
        "duplicate_stable5_parser_forbidden": True,
        "duplicate_predecessor_acquisition_forbidden": True,
        "device_identity_risk_resolution_contract_defined": True,
        "device_identity_risk_resolution_runtime_proven": False,
        "ready_for_compiler_remap_context_handoff_implementation": False,
        "ready_for_dataloader_integration": False,
        "ready_for_model_integration": False,
        "ready_for_loss_integration": False,
        "feature_semantics_reaudit_required_before_training": True,
        "ready_for_training": False,
        "checkpoint_bytes_read": False,
        "checkpoint_state_dict_change_required": False,
        "base_model_parameter_shape_change_required": False,
        "base_atom_feature_width_change_required": False,
        "egnn_or_se3_backbone_change_required": False,
    }


def _report_readiness(lifecycle: str) -> dict[str, object]:
    if lifecycle not in ("precommit-untracked", "clean-tracked-successor"):
        _fail()
    published_candidate_authorized = lifecycle == "clean-tracked-successor"
    readiness = {
        **_semantic_readiness(),
        "compiler_remap_context_handoff_contract_gate_implemented": True,
        "compiler_remap_context_handoff_contract_gate_passed": True,
        "ready_for_compiler_remap_context_handoff_contract_gate_commit_review": (
            lifecycle == "precommit-untracked"
        ),
        "ready_for_compiler_remap_context_handoff_contract_gate_publication": (
            published_candidate_authorized
        ),
        "ready_for_compiler_remap_context_handoff_implementation": (
            published_candidate_authorized
        ),
        "compiler_remap_context_handoff_implementation_blocker": (
            "NONE"
            if published_candidate_authorized
            else "handoff_contract_gate_not_published"
        ),
        "commit_created": False,
        "push_performed": False,
    }
    return readiness


def _manifest_artifact(
    *, design: Mapping[str, object], owners: Sequence[Mapping[str, object]], known: str
) -> dict[str, object]:
    return {
        "schema_version": (
            "covapie_current11_task2_compiler_remap_context_handoff_"
            "contract_manifest_v1"
        ),
        "selected_option": _SELECTED_OPTION,
        "selected_architecture": _ARCHITECTURE,
        "design_report_identity": dict(design),
        "predecessor_identities": [dict(owner) for owner in owners],
        "published_adapter_context_ownership": {
            "context_schema_version": (
                "covapie_current11_task2_batch_index_remap_adapter_context_v1"
            ),
            "context_contract_and_hot_loop_stable_digest": (
                "19649350ac39697138d1c38155a762403fa148db5d7f9ebc518466756c40d1dc"
            ),
            "public_exact2": list(_ADAPTER_PUBLIC_EXACT2),
            "private_trusted_owner_materializer": _ADAPTER_MATERIALIZER,
        },
        "source_contract": {
            "field_order": list(_SOURCE_FIELDS),
            "canonical_compact_bytes": _SOURCE_CANONICAL_BYTES,
            "canonical_sha256": _SOURCE_CANONICAL_SHA256,
            "source_contract_digest": _SOURCE_CONTRACT_DIGEST,
            "source_component_digest": _SOURCE_COMPONENT_DIGEST,
            "lossless_mapping": True,
        },
        "provider_contract": {
            "sample_count": 11,
            "canonical_compact_bytes": _PROVIDER_CANONICAL_BYTES,
            "canonical_sha256": _PROVIDER_CANONICAL_SHA256,
            "provider_digest": _PROVIDER_DIGEST,
            "provider_component_digest": _PROVIDER_COMPONENT_DIGEST,
            "lossless_mapping": True,
            "missing_information_count": 0,
        },
        "readiness_contract": {
            "field_order": list(_READINESS_VALUES),
            "component_digest": _READINESS_COMPONENT_DIGEST,
            "historical_output10_parity": True,
        },
        "historical_authority_compatibility_digest": (
            _AUTHORITY_COMPATIBILITY_DIGEST
        ),
        "future_bridge": {
            "module": _FUTURE_MODULE,
            "public_exact2": list(_FUTURE_PUBLIC_EXACT2),
            "error_token": _FUTURE_ERROR,
            "context_field_order": list(_FUTURE_CONTEXT_FIELDS),
        },
        "ownership": {
            "single_authority_snapshot_shared_between_remap_and_compiler": True,
            "caller_builds_remap_context_once": True,
            "bridge_materializer_calls_per_build": 1,
            "bridge_retains_remap_context": False,
            "duplicate_stable5_parser_forbidden": True,
            "duplicate_predecessor_acquisition_forbidden": True,
        },
        "output10_parity_domain": {
            "field_order": list(_OUTPUT10_FIELDS),
            "success_case_ids": list(_SUCCESS_CASES),
            "hard_failure_case_ids": [case_id for case_id, _status in _HARD_FAILURES],
            "bridge_metadata_added": False,
        },
        "no_io_and_no_old_chain_contract": True,
        "known_vector_digest": known,
        "readiness": _semantic_readiness(),
    }


def _context_schema_artifact() -> dict[str, object]:
    field_types = {
        "context_schema_version": "str",
        "context_contract_version": "str",
        "adapter_context_owner_module": "str",
        "adapter_context_owner_schema_version": "str",
        "adapter_context_owner_contract_version": "str",
        "adapter_context_owner_source_sha256": "str",
        "adapter_context_private_materializer": "str",
        "compiler_module": "str",
        "compiler_product_commit": "str",
        "compiler_source_sha256": "str",
        "compiler_private_kernel": "str",
        "compiler_contract_digest": "str",
        "source_contract_digest": "str",
        "provider_digest": "str",
        "historical_authority_compatibility_digest": "str",
        "context_freshness_model": "str",
        "source_exact10": "deeply_frozen_mapping",
        "identity_provider_exact11": "deeply_frozen_sequence",
        "readiness_template": "deeply_frozen_mapping",
        "construction_seal": "sha256_hex_str",
    }
    return {
        "schema_version": (
            "covapie_current11_task2_compiler_remap_context_handoff_"
            "context_schema_contract_v1"
        ),
        "future_context_schema_version": _FUTURE_CONTEXT_SCHEMA_VERSION,
        "logical_field_order": list(_FUTURE_CONTEXT_FIELDS),
        "logical_field_count": len(_FUTURE_CONTEXT_FIELDS),
        "field_types": [
            {"field": field, "type": field_types[field]}
            for field in _FUTURE_CONTEXT_FIELDS
        ],
        "fixed_value_contract": {
            "context_schema_version": _FUTURE_CONTEXT_SCHEMA_VERSION,
            "context_contract_version": (
                "published_handoff_gate_report_stable_contract_digest"
            ),
            "adapter_context_owner_module": _OWNER_SPECS[0]["path"],
            "adapter_context_owner_schema_version": (
                "covapie_current11_task2_batch_index_remap_adapter_context_v1"
            ),
            "adapter_context_owner_contract_version": (
                "19649350ac39697138d1c38155a762403fa148db5d7f9ebc518466756c40d1dc"
            ),
            "adapter_context_owner_source_sha256": _OWNER_SPECS[0]["sha256"],
            "adapter_context_private_materializer": _ADAPTER_MATERIALIZER,
            "compiler_module": _OWNER_SPECS[4]["path"],
            "compiler_product_commit": (
                "05e8694eb3cdfe9c1aa4cd9728d4820b7322ba5e"
            ),
            "compiler_source_sha256": _OWNER_SPECS[4]["sha256"],
            "compiler_private_kernel": _COMPILER_KERNEL,
            "compiler_contract_digest": _COMPILER_CONTRACT_DIGEST,
            "source_contract_digest": _SOURCE_CONTRACT_DIGEST,
            "provider_digest": _PROVIDER_DIGEST,
            "historical_authority_compatibility_digest": (
                _AUTHORITY_COMPATIBILITY_DIGEST
            ),
            "context_freshness_model": _FUTURE_FRESHNESS_MODEL,
        },
        "materialized_authority_fields": {
            "source_exact10": "validated_lossless_source_mapping_result",
            "identity_provider_exact11": (
                "validated_lossless_provider_mapping_result"
            ),
            "readiness_template": "historical_readiness_exact24_lexical_order",
        },
        "private_type_contract": {
            "private": True,
            "opaque_to_callers": True,
            "frozen": True,
            "slotted": True,
            "public_constructor": False,
            "public_context_class_export": False,
            "mutable_dict_or_list_reachable": False,
            "global_cache": False,
            "registry": False,
            "singleton": False,
            "pickle_or_copy_private_context": False,
        },
        "seal_contract": {
            "algorithm": "SHA256",
            "domain_utf8_with_terminal_nul": _FUTURE_SEAL_DOMAIN,
            "input": (
                "domain_separated_framed_canonical_compact_json_of_logical_"
                "fields_excluding_construction_seal"
            ),
            "framing_steps": [
                "initialize_sha256_with_domain_utf8_bytes_including_terminal_nul",
                "encode_first_19_fields_as_canonical_compact_json_utf8",
                "append_payload_length_as_unsigned_8_byte_big_endian",
                "append_payload_bytes",
                "emit_lowercase_sha256_hex",
            ],
            "excluded_fields": ["construction_seal"],
            "validation_before_observation_evaluation": True,
        },
        "freshness_model": _FUTURE_FRESHNESS_MODEL,
        "rebuild_semantics": (
            "caller_builds_new_remap_context_then_builds_new_bridge_context"
        ),
        "retained_remap_context": False,
        "disallowed_identity_fields": [
            "absolute_path",
            "inode",
            "st_dev",
            "mtime",
            "timestamp",
            "PID",
            "rank",
            "GPU_id",
            "origin_main",
            "ahead_behind",
            "random_nonce",
            "remap_context_object",
        ],
        "historical_authority_digest_role": (
            "compatibility_digest_not_bridge_construction_seal"
        ),
    }


def _api_and_error_artifact() -> dict[str, object]:
    return {
        "schema_version": (
            "covapie_current11_task2_compiler_remap_context_handoff_"
            "api_and_error_contract_v1"
        ),
        "future_module": _FUTURE_MODULE,
        "future_public_exact2": [
            {
                "name": _FUTURE_PUBLIC_EXACT2[0],
                "signature": _FUTURE_BUILD_SIGNATURE,
                "phase": "bridge_build",
            },
            {
                "name": _FUTURE_PUBLIC_EXACT2[1],
                "signature": _FUTURE_COMPILE_SIGNATURE,
                "phase": "fast_compile",
            },
        ],
        "future_error_token": _FUTURE_ERROR,
        "future_builder_forbidden_parameters": [
            "repo_root",
            "state_root",
            "successor_artifacts",
            "reconciliation_artifacts",
            "formal_paths",
            "device_identity",
        ],
        "trusted_owner_coupling": {
            "owner_module": _OWNER_SPECS[0]["path"],
            "private_helper": _ADAPTER_MATERIALIZER,
            "helper_signature": _ADAPTER_MATERIALIZER_SIGNATURE,
            "helper_call_count_per_build": 1,
            "helper_call_count_per_fast_compile": 0,
            "helper_validates": [
                "exact_private_context_type",
                "schema_and_context_versions",
                "fixed_digests_and_formal_identity",
                "freshness_model",
                "construction_seal",
            ],
            "helper_returns": (
                "fresh_built_in_source_contract_authority_tables_and_semantic"
            ),
            "adapter_public_exact2_unchanged": True,
            "public_accessor_added": False,
            "arbitrary_module_inspection_entitlement": False,
            "owner_validation_bypassed": False,
            "direct_semantic_or_seal_read": False,
            "private_adapter_context_reconstruction": False,
            "owner_monkeypatch": False,
            "owner_error_caught_then_continued": False,
        },
        "single_authority_snapshot": {
            "caller_builds_remap_context_once": True,
            "bridge_consumes_same_object": True,
            "materialize_once_at_build": True,
            "compiler_authority_freeze_once": True,
            "bridge_public_remap_builder_call_count": 0,
            "zero_call_vector": dict(_ZERO_CALL_VECTOR),
        },
        "fast_compile": {
            "validate_type_version_lineage_seal_first": True,
            "fresh_thaw": [
                "source_exact10",
                "identity_provider_exact11",
                "readiness_template",
            ],
            "only_compile_call": _COMPILER_KERNEL,
            "only_compile_call_signature": _COMPILER_KERNEL_SIGNATURE,
            "filesystem_reads": 0,
            "git_calls": 0,
            "subprocess_calls": 0,
            "artifact_writes": 0,
            "context_rebuilds": 0,
            "global_cache_accesses": 0,
            "benchmark_or_millisecond_sla": False,
        },
        "error_semantics": {
            "context_programming_failures": list(_CONTEXT_FAILURES),
            "context_failure_result": _FUTURE_ERROR,
            "context_validation_before_observation_evaluation": True,
            "valid_context_malformed_observation": (
                "existing_compiler_hard_failure_output10"
            ),
            "keyboard_interrupt_or_system_exit_wrapped": False,
        },
        "output10": {
            "field_order": list(_OUTPUT10_FIELDS),
            "whole_built_in_dict_deep_exact": True,
            "bridge_metadata_added": False,
            "historical_readiness_preserved": True,
        },
    }


def _reference_artifact(semantic: Mapping[str, object], known: str) -> dict[str, object]:
    return {
        "schema_version": (
            "covapie_current11_task2_compiler_remap_context_handoff_"
            "reference_vectors_v1"
        ),
        "known_vector_digest": known,
        "known_vector_semantic": dict(semantic),
    }


def _acceptance_artifact() -> dict[str, object]:
    positive = (
        "all_predecessor_identities_exact",
        "design_report_identity_exact",
        "adapter_public_exact2_and_private_helper_exact",
        "compiler_context_exact2_byte_frozen",
        "compiler_private_kernel_exact",
        "source_exact10_lossless_golden_exact",
        "provider_exact11_lossless_golden_exact",
        "readiness_exact24_historical_order_exact",
        "authority_compatibility_digest_exact",
        "single_authority_snapshot_contract_exact",
        "fast_compile_no_io_contract_exact",
        "output10_and_mask_sentinels_exact",
    )
    cases = [
        {
            "case_id": case_id,
            "polarity": "positive",
            "required_result": "accept",
        }
        for case_id in positive
    ]
    cases.extend(
        {
            "case_id": case_id,
            "polarity": "negative",
            "required_result": result,
        }
        for case_id, result in _NEGATIVE_CASES
    )
    return {
        "schema_version": (
            "covapie_current11_task2_compiler_remap_context_handoff_"
            "acceptance_matrix_v1"
        ),
        "case_order": [row["case_id"] for row in cases],
        "positive_case_count": len(positive),
        "negative_case_count": len(_NEGATIVE_CASES),
        "cases": cases,
        "all_gates_fail_closed": True,
    }


def _validate_stable_semantics(artifacts: Mapping[str, bytes], known: str) -> None:
    if tuple(artifacts) != _STABLE_NAMES:
        _fail()
    parsed = {name: _strict_json(payload) for name, payload in artifacts.items()}
    manifest = parsed[_MANIFEST]
    context = parsed[_CONTEXT_SCHEMA]
    api = parsed[_API_AND_ERROR]
    vectors = parsed[_REFERENCE_VECTORS]
    acceptance = parsed[_ACCEPTANCE_MATRIX]
    cases = acceptance.get("cases")
    if (
        manifest.get("selected_option") != "B"
        or manifest.get("selected_architecture") != _ARCHITECTURE
        or manifest.get("known_vector_digest") != known
        or context.get("logical_field_order") != list(_FUTURE_CONTEXT_FIELDS)
        or context.get("logical_field_count") != 20
        or context.get("retained_remap_context") is not False
        or [row.get("name") for row in api.get("future_public_exact2", [])]
        != list(_FUTURE_PUBLIC_EXACT2)
        or api.get("future_error_token") != _FUTURE_ERROR
        or vectors.get("known_vector_digest") != known
        or _framed_digest(
            _KNOWN_VECTOR_DOMAIN, vectors.get("known_vector_semantic")
        )
        != known
        or type(cases) is not list
        or acceptance.get("negative_case_count") != 36
        or [row.get("case_id") for row in cases if row.get("polarity") == "negative"]
        != [case_id for case_id, _result in _NEGATIVE_CASES]
    ):
        _fail()


def _validate_gate_source_lightweight(repo_root: Path) -> None:
    try:
        source = (repo_root / _MODULE_PATH).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=_MODULE_PATH)
    except (OSError, UnicodeError, SyntaxError) as error:
        raise _ContractInvariantError() from error
    if tuple(_literal_assignment(tree, "__all__")) != __all__:
        _fail()
    forbidden_calls = {
        "build_covapie_current11_task2_batch_index_remap_adapter_context_v1",
        "remap_covapie_current11_task2_batch_index_with_context_v1",
        "build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1",
        "build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1",
        "build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1",
        "build_covapie_current11_task2_batch_descriptor_compiler_context_v1",
        "build_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1",
        "_authority",
        "_parse_successor_stable5_v1",
        "_validate_formal",
    }
    imported_modules = {
        alias.name
        for node in tree.body
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_from = {
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module is not None
    }
    if any(name.startswith("covalent_ext") for name in imported_modules | imported_from):
        _fail()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                leaf = node.func.id
            elif isinstance(node.func, ast.Attribute):
                leaf = node.func.attr
            else:
                leaf = None
            if leaf in forbidden_calls:
                _fail()


def _build_impl(*, repo_root: Path, state_root: Path) -> dict[str, bytes]:
    repo = _require_root(repo_root)
    state = _require_root(state_root)
    lifecycle, repository = _repository_lifecycle(repo)
    _validate_gate_source_lightweight(repo)
    design = _verify_design_report(state)
    owners, constants = _verify_predecessors(repo)
    source = _source_fixture(constants)
    known_semantic = _known_vector_semantic(source=source, constants=constants)
    known_digest = _framed_digest(_KNOWN_VECTOR_DOMAIN, known_semantic)
    stable_values = (
        _manifest_artifact(design=design, owners=owners, known=known_digest),
        _context_schema_artifact(),
        _api_and_error_artifact(),
        _reference_artifact(known_semantic, known_digest),
        _acceptance_artifact(),
    )
    artifacts = {
        name: _canonical_json(value)
        for name, value in zip(_STABLE_NAMES, stable_values, strict=True)
    }
    _validate_stable_semantics(artifacts, known_digest)
    stable_digest = _stable_digest(artifacts)
    status = (
        "PASS_COMPILER_REMAP_CONTEXT_HANDOFF_CONTRACT_PRECOMMIT_CANDIDATE_ONLY"
        if lifecycle == "precommit-untracked"
        else "PASS_COMPILER_REMAP_CONTEXT_HANDOFF_CONTRACT_CLEAN_TRACKED_SUCCESSOR"
    )
    artifact_identities = [
        {
            "artifact_index": index,
            "artifact_name": name,
            "stable_digest_participation": True,
            "bytes": len(artifacts[name]),
            "LF": artifacts[name].count(b"\n"),
            "sha256": _sha256(artifacts[name]),
        }
        for index, name in enumerate(_STABLE_NAMES)
    ]
    artifact_identities.append(
        {
            "artifact_index": 5,
            "artifact_name": _REPORT,
            "stable_digest_participation": False,
            "content_identity": "self_excluded",
        }
    )
    report = {
        "schema_version": (
            "covapie_current11_task2_compiler_remap_context_handoff_"
            "contract_gate_report_v1"
        ),
        "gate_status": status,
        "repository_lifecycle": lifecycle,
        "repository": repository,
        "stable_contract_digest": stable_digest,
        "known_vector_digest": known_digest,
        "artifact_file_count": 6,
        "artifact_identities": artifact_identities,
        "design_report_identity_verified": True,
        "predecessor_identities_verified": True,
        "adapter_context_public_exact2_frozen": True,
        "private_materializer_signature_frozen": True,
        "historical_compiler_context_frozen": True,
        "compiler_pure_kernel_frozen": True,
        "source_mapping_contract_passed": True,
        "source_golden_digest_passed": True,
        "provider_mapping_contract_passed": True,
        "provider_mapping_lossless": True,
        "provider_digest_passed": True,
        "readiness_contract_passed": True,
        "authority_compatibility_digest_passed": True,
        "opaque_private_handoff_contract_passed": True,
        "single_authority_snapshot_contract_passed": True,
        "no_old_chain_contract_passed": True,
        "fast_compile_no_io_contract_frozen": True,
        "output10_parity_contract_frozen": True,
        "device_identity_risk_root_cause": (
            "historical_compiler_authority_chain_pins_routing_projection_st_dev_49_"
            "while_current_authorized_state_is_st_dev_50"
        ),
        "device_identity_risk_resolution_contract_defined": True,
        "device_identity_risk_resolution_runtime_proven": False,
        "canonical_mask_exact5_passed": True,
        "runtime_batch_observation_extractor_currently_published": True,
        "real_heavy_call_counts": dict(_REAL_HEAVY_CALL_COUNTS),
        "repository_write_performed": False,
        "state_write_performed": False,
        "checkpoint_bytes_read": False,
        "readiness": _report_readiness(lifecycle),
    }
    artifacts[_REPORT] = _canonical_json(report)
    if type(artifacts) is not dict or tuple(artifacts) != _ARTIFACT_NAMES:
        _fail()
    for name, payload in artifacts.items():
        if type(payload) is not bytes or not name.endswith(".json"):
            _fail()
        _strict_json(payload)
    if _stable_digest(artifacts) != stable_digest:
        _fail()
    return artifacts


def build_covapie_current11_task2_compiler_remap_context_handoff_contract_gate_v1(
    *,
    repo_root: Path,
    state_root: Path,
) -> dict[str, bytes]:
    """Return the deterministic handoff contract Exact6 in memory without writes."""

    try:
        return _build_impl(repo_root=repo_root, state_root=state_root)
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
