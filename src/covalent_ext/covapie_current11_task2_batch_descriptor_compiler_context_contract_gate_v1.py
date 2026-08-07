"""Build the Current11 Task 2 compiler-context contract gate V1."""

from __future__ import annotations

import copy
import hashlib
import json
import stat
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Mapping, NoReturn, Sequence

from covalent_ext import covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1 as _predecessor
from covalent_ext import covapie_current11_task2_batch_descriptor_compiler_v1 as _compiler


__all__ = (
    "build_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1",
)

_ERROR = (
    "COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_"
    "CONTRACT_GATE_V1_ERROR"
)
_CONTEXT_ERROR = "COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_V1_ERROR"
_CONTRACT_SCHEMA = (
    "covapie_current11_task2_batch_descriptor_compiler_context_contract_v1"
)
_CONTEXT_SCHEMA = "covapie_current11_task2_batch_descriptor_compiler_context_v1"
_SCHEMA_ARTIFACT_SCHEMA = (
    "covapie_current11_task2_batch_descriptor_compiler_context_schema_contract_v1"
)
_API_ARTIFACT_SCHEMA = (
    "covapie_current11_task2_batch_descriptor_compiler_context_api_and_error_contract_v1"
)
_REFERENCE_SCHEMA = (
    "covapie_current11_task2_batch_descriptor_compiler_context_reference_vectors_v1"
)
_ACCEPTANCE_SCHEMA = (
    "covapie_current11_task2_batch_descriptor_compiler_context_acceptance_matrix_v1"
)
_REPORT_SCHEMA = (
    "covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_report_v1"
)

_BASE_COMMIT = "463c481b65a68442f19b9f1b417ce2325434785f"
_COMPILER_PRODUCT_COMMIT = "05e8694eb3cdfe9c1aa4cd9728d4820b7322ba5e"
_COMPILER_PRE_REFACTOR_SHA256 = (
    "6adaa3082de5d0d87854c502e2426967104523d5eb791c94746c38766529a3a5"
)
_COMPILER_CONTRACT_COMMIT = "3b390cec784ed73a72f522145b6f26e3d8af704d"
_COMPILER_CONTRACT_DIGEST = (
    "bb9705173523377f28966064eec7393fbf337dce9ef6c70d2e3fbca3038e2dfd"
)
_PROVIDER_DIGEST = (
    "a6193bfe7099b9c9436036f75101df31638739a893b598af8ac021bfa46aa186"
)
_SOURCE_CONTRACT_DIGEST = (
    "2c6259312a3292181f00ebbaf787fab05e5a97e5b5475243f2fa8461b54dcdc6"
)
_FORMAL_CARRIER_AGGREGATE = (
    "ef426a6d8dee9678ac15dd62b191e9ef9cfb436a01660bd941bd24392dfa9a18"
)
_FORMAL_NPZ_SHA256 = (
    "ea3aa7c94b7c88993493662ad6ba7fd95e547ec62612a072f8248a515657e910"
)

_CONTEXT_MODULE = (
    "src/covalent_ext/"
    "covapie_current11_task2_batch_descriptor_compiler_context_v1.py"
)
_COMPILER_MODULE = (
    "src/covalent_ext/covapie_current11_task2_batch_descriptor_compiler_v1.py"
)
_BUILD_API = "build_covapie_current11_task2_batch_descriptor_compiler_context_v1"
_FAST_API = "compile_covapie_current11_task2_batch_descriptor_with_context_v1"
_SLOW_API = "compile_covapie_current11_task2_batch_descriptor_v1"
_PRIVATE_KERNEL = "_compile_with_verified_authority_v1"

_MANIFEST = (
    "current11_task2_batch_descriptor_compiler_context_contract_manifest.json"
)
_SCHEMA = "current11_task2_batch_descriptor_compiler_context_schema.json"
_API = (
    "current11_task2_batch_descriptor_compiler_context_api_and_error_contract.json"
)
_VECTORS = (
    "current11_task2_batch_descriptor_compiler_context_reference_vectors.json"
)
_ACCEPTANCE = (
    "current11_task2_batch_descriptor_compiler_context_acceptance_matrix.json"
)
_REPORT = (
    "current11_task2_batch_descriptor_compiler_context_contract_gate_report.json"
)
_ARTIFACT_NAMES = (_MANIFEST, _SCHEMA, _API, _VECTORS, _ACCEPTANCE, _REPORT)
_STABLE_NAMES = _ARTIFACT_NAMES[:5]

_REPOSITORY_EXACT4 = (
    "src/covalent_ext/"
    "covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1.py",
    "scripts/"
    "check_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1.py",
    "tests/"
    "test_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1.py",
    "docs/"
    "covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1_guide.md",
)

_CONTRACT_DOMAIN = (
    b"COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_CONTRACT_GATE_V1\0"
)
_AUTHORITY_DOMAIN = (
    b"COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_"
    b"AUTHORITY_SNAPSHOT_V1\0"
)
_PROVENANCE_COMPONENT_DOMAIN = (
    b"COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_"
    b"PROVENANCE_COMPONENT_V1\0"
)
_SOURCE_COMPONENT_DOMAIN = (
    b"COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_"
    b"SOURCE_COMPONENT_V1\0"
)
_PROVIDER_COMPONENT_DOMAIN = (
    b"COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_"
    b"PROVIDER_COMPONENT_V1\0"
)
_READINESS_COMPONENT_DOMAIN = (
    b"COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_"
    b"READINESS_COMPONENT_V1\0"
)
_OBSERVATION_VECTOR_DOMAIN = (
    b"COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_"
    b"OBSERVATION_VECTOR_V1\0"
)
_OUTPUT_VECTOR_DOMAIN = (
    b"COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_"
    b"SLOW_OUTPUT_VECTOR_V1\0"
)

_SOURCE_FIELDS = tuple(_compiler._SOURCE_FIELDS)
_IDENTITY_FIELDS = tuple(_compiler._IDENTITY_FIELDS)
_ROLE_AUTHORITY_FIELDS = tuple(_compiler._ROLE_AUTHORITY_FIELDS)
_ATOM_IDENTITY_FIELDS = tuple(_compiler._ATOM_IDENTITY_FIELDS)
_EXACT18_FIELDS = tuple(_compiler._EXACT18_FIELDS)
_OUTPUT_FIELDS = tuple(_compiler._OUTPUT_FIELDS)
_JOINT_LAYOUT = _compiler._JOINT_LAYOUT

_CONTEXT_SEMANTIC_FIELDS = (
    "context_schema_version",
    "compiler_product_commit",
    "compiler_contract_commit",
    "compiler_contract_digest",
    "provider_digest",
    "formal_carrier_aggregate",
    "formal_npz_sha256",
    "source_contract_digest",
    "authority_snapshot_digest",
    "source_exact10",
    "identity_provider_exact11",
    "readiness_template",
)
_CONTEXT_PRIVATE_INTEGRITY_FIELDS = ("construction_seal",)
_PARITY_CASE_IDS = ("canonical", "reversed", "subset_10_4_0", "singleton_10")
_HARD_FAILURE_CASE_IDS = (
    "source_contract_override",
    "duplicate_runtime_key",
    "wrong_ligand_length",
    "wrong_ligand_membership",
    "unknown_joint_descriptor",
)
_CONTEXT_FAILURE_IDS = (
    "wrong_context_type",
    "wrong_schema",
    "wrong_authority_digest",
    "wrong_provider_digest",
    "unsealed_or_reconstructed_context",
)


def _fail() -> NoReturn:
    raise ValueError(_ERROR)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json(value: object) -> bytes:
    try:
        text = json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise ValueError(_ERROR) from error
    payload = (text + "\n").encode("utf-8")
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


def _compact(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise ValueError(_ERROR) from error


def _strict_json(payload: bytes) -> dict[str, object]:
    try:
        value = json.loads(
            payload.decode("utf-8"), parse_constant=lambda _value: _fail()
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(_ERROR) from error
    if type(value) is not dict or _json(value) != payload:
        _fail()
    return value


def _framed_semantic_digest(domain: bytes, value: object) -> str:
    payload = _compact(value)
    digest = hashlib.sha256(domain)
    digest.update(len(payload).to_bytes(8, "big", signed=False))
    digest.update(payload)
    return digest.hexdigest()


def _stable_digest(artifacts: Mapping[str, bytes]) -> str:
    digest = hashlib.sha256(_CONTRACT_DOMAIN)
    for name in _STABLE_NAMES:
        encoded = name.encode("utf-8")
        payload = artifacts[name]
        digest.update(len(encoded).to_bytes(8, "big", signed=False))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big", signed=False))
        digest.update(payload)
    return digest.hexdigest()


def _require_root(path: Path) -> Path:
    if type(path) is not type(Path()) or not path.is_absolute():
        _fail()
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ValueError(_ERROR) from error
    if resolved != path or stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        _fail()
    return path


@contextmanager
def _precommit_compatibility() -> Iterator[None]:
    owner = _compiler._contract_gate._remap_gate._instance_builder._payload_builder._contract_gate
    original = owner._run_git

    def compatible(root: Path, arguments: Sequence[str]) -> str:
        output = original(root, arguments)
        if tuple(arguments) in {
            ("status", "--porcelain=v1", "--untracked-files=all"),
            ("status", "--short"),
        }:
            allowed = {f"?? {path}" for path in _REPOSITORY_EXACT4}
            lines = output.splitlines()
            if any(
                len(line) >= 4
                and line[3:] in _REPOSITORY_EXACT4
                and line not in allowed
                for line in lines
            ):
                _fail()
            output = "\n".join(line for line in lines if line not in allowed)
        return output

    try:
        owner._run_git = compatible
        yield
    finally:
        owner._run_git = original


def _expected_compiler_readiness() -> dict[str, bool]:
    return {
        "task2_batch_descriptor_compiler_contract_gate_implemented": True,
        "task2_batch_descriptor_compiler_contract_gate_passed": True,
        "task2_batch_descriptor_compiler_contract_designed": True,
        "formal_runtime_carrier_verified": True,
        "source_contract_verified": True,
        "identity_provider_verified": True,
        "compiler_input_schema_frozen": True,
        "compiler_output_schema_frozen": True,
        "compiler_status_vocabulary_frozen": True,
        "compiler_reference_composition_passed": True,
        "task2_batch_descriptor_compiler_implemented": True,
        "runtime_batch_observation_extractor_implemented": False,
        "ready_for_task2_batch_descriptor_compiler_implementation": False,
        "ready_for_runtime_batch_observation_extractor_design": True,
        "ready_for_dataloader_integration": False,
        "ready_for_model_integration": False,
        "ready_for_loss_integration": False,
        "feature_semantics_reaudit_required_before_training": True,
        "ready_for_training": False,
        "checkpoint_state_dict_change_required": False,
        "base_model_parameter_shape_change_required": False,
        "base_atom_feature_width_change_required": False,
        "egnn_or_se3_backbone_change_required": False,
        "checkpoint_bytes_read": False,
    }


def _gate_readiness() -> dict[str, bool]:
    return {
        "compiler_hot_loop_authority_context_contract_designed": True,
        "compiler_hot_loop_authority_context_contract_gate_implemented": True,
        "compiler_hot_loop_authority_context_contract_gate_passed": True,
        "compiler_hot_loop_authority_context_implemented": False,
        "compiler_shared_pure_kernel_refactor_implemented": False,
        "runtime_batch_observation_extractor_implemented": True,
        "task2_batch_descriptor_compiler_implemented": True,
        "ready_for_compiler_hot_loop_authority_context_implementation": True,
        "ready_for_dataloader_integration": False,
        "public_remap_adapter_hot_loop_audit_required_before_dataloader_integration": True,
        "ready_for_model_integration": False,
        "ready_for_loss_integration": False,
        "feature_semantics_reaudit_required_before_training": True,
        "ready_for_training": False,
        "checkpoint_state_dict_change_required": False,
        "base_model_parameter_shape_change_required": False,
        "base_atom_feature_width_change_required": False,
        "egnn_or_se3_backbone_change_required": False,
        "checkpoint_bytes_read": False,
    }


def _validated_authority(
    authority: object,
) -> tuple[dict[str, object], list[dict[str, object]], dict[str, bool]]:
    if type(authority) is not tuple or len(authority) != 3:
        _fail()
    source_raw, provider_raw, readiness_raw = authority
    try:
        source = copy.deepcopy(source_raw)
        provider = copy.deepcopy(provider_raw)
        readiness = copy.deepcopy(readiness_raw)
    except BaseException as error:
        raise ValueError(_ERROR) from error
    try:
        source = _compiler._validate_source(source)
        provider = _compiler._validate_provider(provider, source)
    except BaseException as error:
        raise ValueError(_ERROR) from error
    if (
        type(source) is not dict
        or tuple(source) != _SOURCE_FIELDS
        or type(provider) is not list
        or _compiler._provider_digest(provider) != _PROVIDER_DIGEST
        or type(readiness) is not dict
        or readiness != _expected_compiler_readiness()
        or any(type(value) is not bool for value in readiness.values())
    ):
        _fail()
    return source, provider, readiness


def _authority_snapshot(
    source: dict[str, object],
    provider: list[dict[str, object]],
    readiness: dict[str, bool],
) -> tuple[dict[str, object], dict[str, str], str]:
    provenance = {
        "context_schema_version": _CONTEXT_SCHEMA,
        "compiler_product_commit": _COMPILER_PRODUCT_COMMIT,
        "compiler_contract_commit": _COMPILER_CONTRACT_COMMIT,
        "compiler_contract_digest": _COMPILER_CONTRACT_DIGEST,
        "provider_digest": _PROVIDER_DIGEST,
        "formal_carrier_aggregate": _FORMAL_CARRIER_AGGREGATE,
        "formal_npz_sha256": _FORMAL_NPZ_SHA256,
        "source_contract_digest": _SOURCE_CONTRACT_DIGEST,
    }
    snapshot = {
        "schema_version": _CONTEXT_SCHEMA,
        "semantic_provenance": provenance,
        "field_and_schema_order": {
            "context_semantic_fields": list(_CONTEXT_SEMANTIC_FIELDS),
            "source_exact10_fields": list(_SOURCE_FIELDS),
            "identity_fields": list(_IDENTITY_FIELDS),
            "provider_role_order": ["pocket", "ligand"],
            "role_authority_fields": list(_ROLE_AUTHORITY_FIELDS),
            "atom_identity_fields": list(_ATOM_IDENTITY_FIELDS),
            "readiness_fields": list(readiness),
        },
        "source_exact10": copy.deepcopy(source),
        "identity_provider_exact11": copy.deepcopy(provider),
        "readiness_template": copy.deepcopy(readiness),
    }
    components = {
        "provenance_component_digest": _framed_semantic_digest(
            _PROVENANCE_COMPONENT_DOMAIN, provenance
        ),
        "source_component_digest": _framed_semantic_digest(
            _SOURCE_COMPONENT_DOMAIN, source
        ),
        "provider_component_digest": _framed_semantic_digest(
            _PROVIDER_COMPONENT_DOMAIN, provider
        ),
        "readiness_component_digest": _framed_semantic_digest(
            _READINESS_COMPONENT_DOMAIN, readiness
        ),
    }
    return snapshot, components, _framed_semantic_digest(_AUTHORITY_DOMAIN, snapshot)


def _membership(lengths: Sequence[int]) -> list[int]:
    return [ordinal for ordinal, length in enumerate(lengths) for _ in range(length)]


def _observation(
    order: Sequence[int],
    source: Mapping[str, object],
    provider: Sequence[Mapping[str, object]],
    *,
    joint: str | None,
) -> dict[str, object]:
    samples = source["source_sample_order"]
    if type(samples) is not list:
        _fail()
    ligand = [provider[index]["roles"]["ligand"]["parser_output_atom_count"] for index in order]
    pocket = [provider[index]["roles"]["pocket"]["parser_output_atom_count"] for index in order]
    if any(type(value) is not int or value < 0 for value in ligand + pocket):
        _fail()
    return {
        "schema_version": _compiler._INPUT_SCHEMA,
        "runtime_batch_schema_version": _compiler._RUNTIME_SCHEMA,
        "sample_key_schema_version": _compiler._SAMPLE_KEY_SCHEMA,
        "batch_sample_keys": [samples[index]["sample_index_row_id"] for index in order],
        "ligand_lengths": ligand,
        "pocket_lengths": pocket,
        "ligand_membership": _membership(ligand),
        "pocket_membership": _membership(pocket),
        "joint_layout_descriptor": joint,
        "virtual_node_policy": _compiler._VIRTUAL_POLICY,
        "receptors": [samples[index]["pdb_id"] for index in order],
        "consistency_buffer_lengths": {
            "ligand_coords": sum(ligand),
            "ligand_one_hot": sum(ligand),
            "pocket_coords": sum(pocket),
            "pocket_one_hot": sum(pocket),
        },
        "debug_coordinates": None,
        "debug_rank_metadata": None,
    }


def _product_output(
    observation: object,
    *,
    source: dict[str, object],
    provider: list[dict[str, object]],
    readiness: dict[str, bool],
) -> dict[str, object]:
    evaluator_provider_digest = _predecessor._provider_digest(provider)
    evaluated = _predecessor._evaluate_reference_case_v1(
        observation,
        source_contract=copy.deepcopy(source),
        identity_provider=copy.deepcopy(provider),
        expected_identity_provider_digest=evaluator_provider_digest,
    )
    exact18 = evaluated.get("adapter_input_exact18")
    outcomes = evaluated.get("batch_sample_key_outcomes")
    binding = evaluated.get("runtime_schema_binding")
    if (
        exact18 is not None and (type(exact18) is not dict or tuple(exact18) != _EXACT18_FIELDS)
    ):
        _fail()
    if type(outcomes) is not list or type(binding) is not dict:
        _fail()
    output = _compiler._output(
        str(evaluated.get("compiler_status")),
        exact18=copy.deepcopy(exact18),
        outcomes=copy.deepcopy(outcomes),
        joint_status=str(binding.get("joint_layout_component_status")),
        readiness=readiness,
    )
    if type(output) is not dict or tuple(output) != _OUTPUT_FIELDS:
        _fail()
    return output


def _reference_vectors(
    source: dict[str, object],
    provider: list[dict[str, object]],
    readiness: dict[str, bool],
    authority_digest: str,
    components: Mapping[str, str],
) -> dict[str, object]:
    parity_specs = (
        ("canonical", tuple(range(11)), _JOINT_LAYOUT),
        ("reversed", tuple(reversed(range(11))), _JOINT_LAYOUT),
        ("subset_10_4_0", (10, 4, 0), None),
        ("singleton_10", (10,), None),
    )
    parity: list[dict[str, object]] = []
    for case_id, order, joint in parity_specs:
        observation = _observation(order, source, provider, joint=joint)
        output = _product_output(
            observation, source=source, provider=provider, readiness=readiness
        )
        if output.get("compiler_status") != "COMPILED_EXACT":
            _fail()
        parity.append(
            {
                "case_id": case_id,
                "expected_parity": "exact_deep_equality",
                "observation": observation,
                "observation_digest": _framed_semantic_digest(
                    _OBSERVATION_VECTOR_DOMAIN, observation
                ),
                "existing_slow_output": output,
                "existing_slow_output_digest": _framed_semantic_digest(
                    _OUTPUT_VECTOR_DOMAIN, output
                ),
            }
        )

    base = _observation((10, 4, 0), source, provider, joint=None)
    failures: list[tuple[str, dict[str, object]]] = []

    def changed(field: str, value: object) -> dict[str, object]:
        result = copy.deepcopy(base)
        result[field] = value
        return result

    failures.extend(
        (
            (
                "source_contract_override",
                {**copy.deepcopy(base), "source_projection_digest": _compiler._PROJECTION_DIGEST},
            ),
            (
                "duplicate_runtime_key",
                changed("batch_sample_keys", [base["batch_sample_keys"][0]] * 3),
            ),
            (
                "wrong_ligand_length",
                changed(
                    "ligand_lengths",
                    [base["ligand_lengths"][0] + 1, *base["ligand_lengths"][1:]],
                ),
            ),
            ("wrong_ligand_membership", changed("ligand_membership", [])),
            ("unknown_joint_descriptor", changed("joint_layout_descriptor", "unknown")),
        )
    )
    hard_failures: list[dict[str, object]] = []
    for case_id, observation in failures:
        output = _product_output(
            observation, source=source, provider=provider, readiness=readiness
        )
        if (
            output.get("compiler_status") == "COMPILED_EXACT"
            or output.get("adapter_input_exact18") is not None
        ):
            _fail()
        hard_failures.append(
            {
                "case_id": case_id,
                "expected_fast_behavior": "return_existing_output_exactly_without_context_error",
                "observation": observation,
                "observation_digest": _framed_semantic_digest(
                    _OBSERVATION_VECTOR_DOMAIN, observation
                ),
                "existing_slow_output": output,
                "existing_slow_output_digest": _framed_semantic_digest(
                    _OUTPUT_VECTOR_DOMAIN, output
                ),
            }
        )
    return {
        "schema_version": _REFERENCE_SCHEMA,
        "public_api_definitions": {
            "future_context_module___all__": [_BUILD_API, _FAST_API],
            "existing_compiler_module___all__": [_SLOW_API],
        },
        "authority_snapshot_identity": {
            "authority_snapshot_digest": authority_digest,
            "provider_digest": _PROVIDER_DIGEST,
            "source_contract_digest": _SOURCE_CONTRACT_DIGEST,
            "formal_carrier_aggregate": _FORMAL_CARRIER_AGGREGATE,
            "formal_npz_sha256": _FORMAL_NPZ_SHA256,
            **dict(components),
        },
        "context_provenance_fields": list(_CONTEXT_SEMANTIC_FIELDS[:9]),
        "output_parity_cases": parity,
        "representative_runtime_hard_failures": hard_failures,
        "context_failure_vectors": [
            {
                "case_id": case_id,
                "expected_exception_token": _CONTEXT_ERROR,
                "observation_evaluated": False,
            }
            for case_id in _CONTEXT_FAILURE_IDS
        ],
    }


def _manifest_artifact(authority_digest: str, components: Mapping[str, str]) -> dict[str, object]:
    return {
        "schema_version": _CONTRACT_SCHEMA,
        "contract_name": "Current11 Task2 batch descriptor compiler context contract",
        "contract_version": "v1",
        "predecessor_base_commit": _BASE_COMMIT,
        "predecessor_and_provenance": {
            "compiler_product_commit": _COMPILER_PRODUCT_COMMIT,
            "compiler_pre_refactor_source_sha256": _COMPILER_PRE_REFACTOR_SHA256,
            "compiler_contract_commit": _COMPILER_CONTRACT_COMMIT,
            "compiler_contract_digest": _COMPILER_CONTRACT_DIGEST,
            "provider_digest": _PROVIDER_DIGEST,
            "source_contract_digest": _SOURCE_CONTRACT_DIGEST,
            "formal_carrier_aggregate": _FORMAL_CARRIER_AGGREGATE,
            "formal_npz_sha256": _FORMAL_NPZ_SHA256,
            "compiler_pre_refactor_source_identity_is_artifact_provenance_only": True,
            "future_checker_compiler_source_sha_admission_required": False,
        },
        "repository_lifecycle_contract": {
            "required_branch": "main",
            "base_commit_must_exist": True,
            "base_commit_must_be_ancestor_of_or_equal_to_HEAD": True,
            "HEAD_must_equal_base": False,
            "origin_main_used_for_admission": False,
            "HEAD_must_equal_origin_main": False,
        },
        "module_placement": {
            "future_context_module": _CONTEXT_MODULE,
            "existing_compiler_module": _COMPILER_MODULE,
        },
        "public_api_contract": {
            "future_context_module___all__": [_BUILD_API, _FAST_API],
            "existing_compiler_module___all__": [_SLOW_API],
            "all_parameters_keyword_only": True,
            "public_context_class": False,
        },
        "recommended_architecture": {
            "option": "Option 2",
            "compiler_owned_private_shared_kernel": _PRIVATE_KERNEL,
            "slow_path": ["validate canonical roots", "fresh _authority exactly once", "shared pure kernel"],
            "context_builder": ["validate canonical roots", "fresh _authority exactly once", "deep freeze", "seal opaque context"],
            "fast_path": ["O(1) context validation", "shared pure kernel"],
            "shared_observation_validation_implementation_count": 1,
            "shared_Exact18_construction_implementation_count": 1,
            "shared_output_logic_implementation_count": 1,
            "production_monkeypatch_forbidden": True,
            "hidden_global_cache_forbidden": True,
            "lru_cache_forbidden": True,
            "first_call_implicit_cache_forbidden": True,
        },
        "authority_snapshot_contract": {
            "authority_snapshot_digest": authority_digest,
            **dict(components),
            "canonical_encoding": "UTF-8 canonical compact JSON",
            "json_options": {
                "ensure_ascii": True,
                "allow_nan": False,
                "sort_keys": True,
                "separators": [",", ":"],
            },
            "framing": "SHA256(domain || uint64be(payload_bytes) || payload)",
            "domain_ascii_escaped": (
                "COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_"
                "AUTHORITY_SNAPSHOT_V1\\0"
            ),
            "domain_hex": _AUTHORITY_DOMAIN.hex(),
            "python_repr_pickle_hash_forbidden": True,
        },
        "freshness_semantics": {
            "meaning": "immutable authority snapshot verified at builder time",
            "built_context_survives_external_disk_drift": True,
            "fresh_authority_requires_explicit_rebuild": True,
            "slow_api_rediscovers_drift_on_next_call": True,
            "fast_path_filesystem_polling": False,
            "fast_path_authority_switching": False,
        },
        "performance_acceptance": {
            "absolute_latency_SLA": False,
            "builder_authority_call_count": 1,
            "fast_authority_call_count": 0,
            "fast_gate_builder_call_count": 0,
            "fast_filesystem_or_git_or_formal_read_count": 0,
            "slow_fast_output_parity": "exact_deep_equality",
        },
        "readiness": _gate_readiness(),
    }


def _schema_artifact(
    snapshot: dict[str, object], authority_digest: str, components: Mapping[str, str]
) -> dict[str, object]:
    return {
        "schema_version": _SCHEMA_ARTIFACT_SCHEMA,
        "context_schema_version": _CONTEXT_SCHEMA,
        "context_visibility": "private_opaque_exact_type",
        "recommended_representation": "dataclass(frozen=True, slots=True, repr=False)",
        "equivalent_representation_allowed": True,
        "semantic_field_order": list(_CONTEXT_SEMANTIC_FIELDS),
        "private_integrity_field_order": list(_CONTEXT_PRIVATE_INTEGRITY_FIELDS),
        "nested_representation": "private frozen records and tuples only",
        "reachable_builtin_dict_or_list_allowed": False,
        "public_constructor_exposed": False,
        "public_mutation_API_exposed": False,
        "data_rich_repr_allowed": False,
        "pickle_policy": {
            "pickleable": False,
            "__reduce___must_fail": True,
            "__reduce_ex___must_fail": True,
        },
        "semantic_identity_exclusions": [
            "absolute_repo_path",
            "absolute_state_path",
            "origin/main",
            "ahead/behind",
            "mtime",
            "inode",
            "device",
            "formal_hidden_object_nonce",
            "timestamp",
            "random_nonce",
        ],
        "authority_snapshot_digest": authority_digest,
        "authority_snapshot_component_digests": dict(components),
        "canonical_semantic_snapshot": snapshot,
    }


def _api_artifact() -> dict[str, object]:
    return {
        "schema_version": _API_ARTIFACT_SCHEMA,
        "future_context_module": {
            "relative_path": _CONTEXT_MODULE,
            "__all__": [_BUILD_API, _FAST_API],
            "public_apis": [
                {
                    "name": _BUILD_API,
                    "signature": "(*, repo_root: Path, state_root: Path) -> object",
                    "parameters": ["repo_root", "state_root"],
                    "keyword_only": True,
                },
                {
                    "name": _FAST_API,
                    "signature": "(*, context: object, observation: dict[str, object]) -> dict[str, object]",
                    "parameters": ["context", "observation"],
                    "keyword_only": True,
                },
            ],
            "public_context_class": False,
        },
        "existing_compiler_module": {
            "relative_path": _COMPILER_MODULE,
            "__all__": [_SLOW_API],
            "slow_API_signature": "(*, repo_root: Path, state_root: Path, observation: dict[str, object]) -> dict[str, object]",
            "signature_and_semantics_unchanged": True,
        },
        "shared_kernel_contract": {
            "owner": _COMPILER_MODULE,
            "private_conceptual_name": _PRIVATE_KERNEL,
            "pure_batch_local": True,
            "used_by_slow_and_fast_paths": True,
            "root_validation": False,
            "filesystem_access": False,
            "gate_access": False,
            "adapter_access": False,
            "authority_access": False,
            "mutates_inputs": False,
        },
        "context_integrity_contract": {
            "use_time_complexity": "O(1)",
            "checks": [
                "exact private context type",
                "exact context schema version",
                "fixed compiler contract provider formal and source digests",
                "stored authority snapshot digest",
                "module-private construction seal",
            ],
            "per_batch_provider_rehash": False,
            "per_batch_snapshot_recanonicalization": False,
            "cryptographic_hostile_same_process_boundary": False,
            "reflection_and_object_setattr_in_scope": False,
        },
        "process_and_dataloader_contract": {
            "builder_calls_per_process": 1,
            "builder_calls_per_DDP_rank": 1,
            "context_shared_across_ranks": False,
            "distributed_collective_transport": False,
            "checkpoint_storage": False,
            "Dataset_transport": False,
            "DataLoader_worker_transport": False,
            "build_inside_worker": False,
            "rank_main_process_flow": "batch -> extractor -> fast compiler(context)",
        },
        "output_parity_contract": {
            "comparison": "exact_deep_equality",
            "output_exact10_field_order": list(_OUTPUT_FIELDS),
            "adapter_exact18_field_order": list(_EXACT18_FIELDS),
            "context_reuse_metadata_in_compiler_output": False,
            "all_values_statuses_failures_outcomes_provenance_readiness_included": True,
        },
        "error_contract": {
            "context_error_token": _CONTEXT_ERROR,
            "existing_slow_error_token": _compiler._ERROR,
            "builder_root_authority_gate_formal_provider_failure": {
                "raises": _CONTEXT_ERROR,
                "compiler_token_retained_as___cause__": True,
            },
            "invalid_context": {"raises": _CONTEXT_ERROR},
            "valid_context_malformed_observation": {
                "raises_context_token": False,
                "returns_existing_compiler_hard_failure_exact10": True,
            },
            "fast_unexpected_shared_kernel_invariant": {"raises": _CONTEXT_ERROR},
            "slow_unexpected_shared_kernel_invariant": {"raises": _compiler._ERROR},
        },
    }


def _acceptance_artifact() -> dict[str, object]:
    rows = (
        ("builder_authority_exactly_once", "compiler._authority call count", 1),
        ("fast_authority_zero", "fast compiler compiler._authority call count", 0),
        ("fast_gate_zero", "fast compiler gate builder call count", 0),
        ("fast_io_zero", "fast compiler filesystem git formal read count", 0),
        ("slow_public_surface_unchanged", "existing slow API signature unchanged", True),
        ("compiler___all___unchanged", "existing compiler __all__", [_SLOW_API]),
        ("context___all___exact2", "future context module __all__", [_BUILD_API, _FAST_API]),
        ("slow_fast_deep_parity", "parity case IDs", list(_PARITY_CASE_IDS)),
        ("runtime_hard_failure_parity", "hard-failure case IDs", list(_HARD_FAILURE_CASE_IDS)),
        ("invalid_context_token", "invalid or forged context token", _CONTEXT_ERROR),
        ("build_drift_token", "context build drift token", _CONTEXT_ERROR),
        ("deep_immutability", "dict or list reachable from context", False),
        ("non_pickleable", "context pickleable", False),
        ("no_hidden_cache", "global lru or first-call cache", False),
        ("no_fast_adapter", "adapter call count in fast compiler", 0),
        ("no_training_surface_interaction", "checkpoint model dataloader interaction", False),
    )
    return {
        "schema_version": _ACCEPTANCE_SCHEMA,
        "acceptance_count": len(rows),
        "acceptance_rows": [
            {"acceptance_index": index, "acceptance_id": item[0], "assertion": item[1], "expected": item[2]}
            for index, item in enumerate(rows)
        ],
        "performance_evidence": {
            "directional_only": True,
            "absolute_latency_SLA": False,
            "design_audit_single_shot_order": [10, 4, 0],
            "public_total_seconds": 577.1654076240957,
            "authority_build_seconds": 565.6954654380679,
            "preverified_batch_compile_seconds": 0.00043270736932754517,
            "authority_fraction": 0.9801271142821192,
        },
    }


def _validate_artifact(name: str, payload: bytes) -> None:
    if (
        type(payload) is not bytes
        or not payload
        or len(payload) >= 1024 * 1024
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\0" in payload
        or b"\r" in payload
        or not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
        or not name.endswith(".json")
    ):
        _fail()
    _strict_json(payload)


def _build_impl(*, repo_root: Path, state_root: Path) -> dict[str, bytes]:
    repo = _require_root(repo_root)
    state = _require_root(state_root)
    with _precommit_compatibility():
        live_authority = _compiler._authority(repo, state)
    source, provider, readiness = _validated_authority(live_authority)
    snapshot, components, authority_digest = _authority_snapshot(
        source, provider, readiness
    )
    stable_values = (
        _manifest_artifact(authority_digest, components),
        _schema_artifact(snapshot, authority_digest, components),
        _api_artifact(),
        _reference_vectors(source, provider, readiness, authority_digest, components),
        _acceptance_artifact(),
    )
    artifacts = {
        name: _json(value) for name, value in zip(_STABLE_NAMES, stable_values)
    }
    contract_digest = _stable_digest(artifacts)
    identities = [
        {
            "artifact_index": index,
            "artifact_name": name,
            "stable_digest_participation": True,
            "bytes": len(artifacts[name]),
            "LF": artifacts[name].count(b"\n"),
            "SHA256": _sha(artifacts[name]),
        }
        for index, name in enumerate(_STABLE_NAMES)
    ]
    identities.append(
        {
            "artifact_index": 5,
            "artifact_name": _REPORT,
            "stable_digest_participation": False,
            "content_identity": "self_excluded",
        }
    )
    artifacts[_REPORT] = _json(
        {
            "schema_version": _REPORT_SCHEMA,
            "gate_status": "PASS_CONTRACT_ONLY",
            "contract_digest": contract_digest,
            "authority_snapshot_digest": authority_digest,
            **components,
            "provider_digest": _PROVIDER_DIGEST,
            "source_contract_digest": _SOURCE_CONTRACT_DIGEST,
            "formal_carrier_aggregate": _FORMAL_CARRIER_AGGREGATE,
            "formal_npz_sha256": _FORMAL_NPZ_SHA256,
            "artifact_file_count": 6,
            "artifact_identities": identities,
            "live_authority_build_count": 1,
            "live_authority_verified": True,
            "source_exact10_field_count": len(_SOURCE_FIELDS),
            "identity_provider_sample_count": len(provider),
            "identity_provider_role_count": sum(
                len(row["roles"]) for row in provider
            ),
            "output_parity_case_count": len(_PARITY_CASE_IDS),
            "runtime_hard_failure_case_count": len(_HARD_FAILURE_CASE_IDS),
            "context_failure_case_count": len(_CONTEXT_FAILURE_IDS),
            "repository_write_performed": False,
            "state_write_performed": False,
            "checkpoint_bytes_read": False,
            "readiness": _gate_readiness(),
        }
    )
    if type(artifacts) is not dict or tuple(artifacts) != _ARTIFACT_NAMES:
        _fail()
    for name, payload in artifacts.items():
        _validate_artifact(name, payload)
    if _stable_digest(artifacts) != contract_digest:
        _fail()
    return artifacts


def build_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1(
    *, repo_root: Path, state_root: Path
) -> dict[str, bytes]:
    """Return the deterministic context contract Exact6 in memory without writes."""
    try:
        return _build_impl(repo_root=repo_root, state_root=state_root)
    except BaseException as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
