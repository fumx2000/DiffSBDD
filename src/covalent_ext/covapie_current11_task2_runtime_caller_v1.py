"""Stateless in-memory Current11 Task 2 runtime caller V1."""

from __future__ import annotations

from typing import NoReturn

from covalent_ext import (
    covapie_current11_runtime_batch_observation_extractor_v1 as _extractor_owner,
)
from covalent_ext import (
    covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1
    as _compiler_owner,
)
from covalent_ext import (
    covapie_current11_task2_batch_index_remap_adapter_context_v1 as _remap_owner,
)


__all__ = (
    "run_covapie_current11_task2_runtime_caller_v1",
)

_ERROR = "COVAPIE_CURRENT11_TASK2_RUNTIME_CALLER_V1_ERROR"
_RESULT_SCHEMA = "covapie_current11_task2_runtime_caller_result_v1"
_EXTRACTOR_ERROR = (
    "COVAPIE_CURRENT11_RUNTIME_BATCH_OBSERVATION_EXTRACTOR_V1_ERROR"
)
_EXACT14_SCHEMA = (
    "covapie_current11_task2_batch_descriptor_compiler_input_v1"
)
_OUTPUT10_SCHEMA = (
    "covapie_current11_task2_batch_descriptor_compiler_output_v1"
)
_EXACT18_SCHEMA = (
    "covapie_current11_task2_batch_index_remap_adapter_input_v1"
)
_OUTPUT17_SCHEMA = (
    "covapie_current11_task2_batch_index_remap_adapter_output_v1"
)

_RESULT_FIELDS = (
    "schema_version",
    "runtime_status",
    "failure_stage",
    "failure_reason",
    "compiler_status",
    "remap_status",
    "batch_sample_keys_or_none",
    "compiler_failure_output10_or_none",
    "remap_output17_or_none",
    "provenance",
    "readiness",
)
_EXACT14_FIELDS = (
    "schema_version",
    "runtime_batch_schema_version",
    "sample_key_schema_version",
    "batch_sample_keys",
    "ligand_lengths",
    "pocket_lengths",
    "ligand_membership",
    "pocket_membership",
    "joint_layout_descriptor",
    "virtual_node_policy",
    "receptors",
    "consistency_buffer_lengths",
    "debug_coordinates",
    "debug_rank_metadata",
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
_EXACT18_FIELDS = (
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
    "batch_sample_order",
    "batch_sample_atom_identity_tables",
    "batch_role_lengths",
    "batch_role_offsets",
    "batch_membership_masks",
    "joint_layout_descriptor",
    "debug_coordinates",
    "debug_rank_metadata",
)
_OUTPUT17_FIELDS = (
    "schema_version",
    "source_projection_digest",
    "source_payload_digest",
    "batch_sample_order",
    "pair_values_source_row_indices",
    "pair_values_parser_local_indices",
    "pair_values_batch_indices",
    "pair_values_joint_global_indices",
    "pair_sample_indices",
    "sample_pair_offsets",
    "entry_validity",
    "sample_validity",
    "source_entry_outcomes",
    "remap_status",
    "failure_reason",
    "provenance",
    "readiness",
)

_EXTRACTOR_REASONS = (
    "missing_names",
    "invalid_sample_key_scalar",
    "invalid_role_length",
    "invalid_membership",
    "unsupported_empty_batch",
    "virtual_nodes_not_supported",
    "buffer_length_mismatch",
    "unsupported_runtime_type",
)
_COMPILER_SUCCESS = "COMPILED_EXACT"
_COMPILER_STRUCTURED_FAILURES = (
    "BATCH_OBSERVATION_SCHEMA_MISMATCH",
    "BATCH_SAMPLE_KEY_INVALID",
    "BATCH_SAMPLE_KEY_DUPLICATED",
    "BATCH_SAMPLE_KEY_UNKNOWN",
    "BATCH_SAMPLE_KEY_AMBIGUOUS",
    "SOURCE_CONTRACT_MISMATCH",
    "IDENTITY_PROVIDER_MISSING",
    "IDENTITY_PROVIDER_MISMATCH",
    "ROLE_TABLE_AUTHORITY_MISSING",
    "ROLE_LENGTH_MISMATCH",
    "MEMBERSHIP_MASK_MISMATCH",
    "VIRTUAL_NODE_POLICY_MISMATCH",
    "NON_SOURCE_SAMPLE_NOT_ADMISSIBLE_IN_CURRENT11_COMPILER_V1",
)
_REMAP_SUCCESS = "REMAPPED_EXACT"
_REMAP_STRUCTURED_FAILURES = (
    "SOURCE_SAMPLE_DUPLICATED",
    "BATCH_SAMPLE_IDENTITY_UNKNOWN",
    "BATCH_SAMPLE_DUPLICATED",
    "SCHEMA_VERSION_MISMATCH",
    "SOURCE_TABLE_IDENTITY_MISMATCH",
    "SOURCE_ROW_OUT_OF_RANGE",
    "SOURCE_ATOM_IDENTITY_MISMATCH",
    "ROLE_MISMATCH",
    "PARSER_ATOM_NOT_FOUND",
    "PARSER_ATOM_NOT_UNIQUE",
    "PARSER_COUNT_MISMATCH",
    "COLLATE_OFFSET_MISSING",
    "COLLATE_LENGTH_MISMATCH",
    "BATCH_INDEX_OUT_OF_RANGE",
    "ENTRY_INVALID",
)

_PROVENANCE_ITEMS = (
    (
        "selected_architecture",
        "additive_stateless_runtime_caller_with_explicit_rank_local_remap_"
        "and_compiler_contexts_v1",
    ),
    (
        "runtime_caller_contract_commit",
        "b1dd9e44ba2877a46d9622b2a24612e523f1a100",
    ),
    (
        "runtime_caller_contract_digest",
        "098c66343e2e924ea75ce6619cac7aa9b46baabd7f0143e80e652764660a1c20",
    ),
    ("runtime_caller_implemented", True),
)
_READINESS_ITEMS = (
    ("runtime_caller_contract_gate_implemented", True),
    ("runtime_caller_contract_gate_passed", True),
    ("runtime_caller_implemented", True),
    ("ready_for_runtime_caller_implementation", False),
    ("ready_for_dataloader_integration", False),
    ("ready_for_model_integration", False),
    ("ready_for_loss_integration", False),
    ("feature_semantics_reaudit_required_before_training", True),
    ("step12d_smoke_is_final_training_feature_contract", False),
    ("ready_for_training", False),
)


class _CallerInvariantError(Exception):
    pass


def _fail() -> NoReturn:
    raise _CallerInvariantError()


def _exact_product(
    value: object,
    *,
    fields: tuple[str, ...],
    schema_version: str,
) -> dict[str, object]:
    if (
        type(value) is not dict
        or tuple(value) != fields
        or value.get("schema_version") != schema_version
    ):
        _fail()
    return value


def _result(
    *,
    runtime_status: str,
    failure_stage: str,
    failure_reason: str,
    compiler_status: str | None,
    remap_status: str | None,
    batch_sample_keys_or_none: object,
    compiler_failure_output10_or_none: object,
    remap_output17_or_none: object,
) -> dict[str, object]:
    result: dict[str, object] = {
        "schema_version": _RESULT_SCHEMA,
        "runtime_status": runtime_status,
        "failure_stage": failure_stage,
        "failure_reason": failure_reason,
        "compiler_status": compiler_status,
        "remap_status": remap_status,
        "batch_sample_keys_or_none": batch_sample_keys_or_none,
        "compiler_failure_output10_or_none": (
            compiler_failure_output10_or_none
        ),
        "remap_output17_or_none": remap_output17_or_none,
        "provenance": dict(_PROVENANCE_ITEMS),
        "readiness": dict(_READINESS_ITEMS),
    }
    if tuple(result) != _RESULT_FIELDS:
        _fail()
    return result


def _run_impl(
    *,
    batch: dict[str, object],
    remap_context: object,
    compiler_context: object,
) -> dict[str, object]:
    try:
        observation = (
            _extractor_owner.extract_covapie_current11_runtime_batch_observation_v1(
                batch=batch,
            )
        )
    except Exception as error:
        if (
            str(error) == _EXTRACTOR_ERROR
            and getattr(error, "reason", None) in _EXTRACTOR_REASONS
        ):
            return _result(
                runtime_status="extractor_failure",
                failure_stage="extractor",
                failure_reason=error.reason,
                compiler_status=None,
                remap_status=None,
                batch_sample_keys_or_none=None,
                compiler_failure_output10_or_none=None,
                remap_output17_or_none=None,
            )
        raise

    observation = _exact_product(
        observation,
        fields=_EXACT14_FIELDS,
        schema_version=_EXACT14_SCHEMA,
    )
    output10 = (
        _compiler_owner.compile_covapie_current11_task2_batch_descriptor_with_remap_handoff_context_v1(
            context=compiler_context,
            observation=observation,
        )
    )
    output10 = _exact_product(
        output10,
        fields=_OUTPUT10_FIELDS,
        schema_version=_OUTPUT10_SCHEMA,
    )
    compiler_status = output10["compiler_status"]
    compiler_reason = output10["failure_reason"]
    if compiler_status == _COMPILER_SUCCESS:
        if compiler_reason != "NONE":
            _fail()
    elif compiler_status in _COMPILER_STRUCTURED_FAILURES:
        if (
            compiler_reason != compiler_status
            or output10["adapter_input_exact18"] is not None
        ):
            _fail()
        return _result(
            runtime_status="compiler_failure",
            failure_stage="compiler",
            failure_reason=compiler_status,
            compiler_status=compiler_status,
            remap_status=None,
            batch_sample_keys_or_none=observation["batch_sample_keys"],
            compiler_failure_output10_or_none=output10,
            remap_output17_or_none=None,
        )
    else:
        _fail()

    exact18 = _exact_product(
        output10["adapter_input_exact18"],
        fields=_EXACT18_FIELDS,
        schema_version=_EXACT18_SCHEMA,
    )
    output17 = (
        _remap_owner.remap_covapie_current11_task2_batch_index_with_context_v1(
            context=remap_context,
            adapter_input=exact18,
        )
    )
    output17 = _exact_product(
        output17,
        fields=_OUTPUT17_FIELDS,
        schema_version=_OUTPUT17_SCHEMA,
    )
    remap_status = output17["remap_status"]
    remap_reason = output17["failure_reason"]
    if remap_status == _REMAP_SUCCESS:
        if remap_reason != "NONE":
            _fail()
        runtime_status = "full_success"
        failure_stage = "none"
    elif remap_status in _REMAP_STRUCTURED_FAILURES:
        if remap_reason != remap_status:
            _fail()
        runtime_status = "remap_failure"
        failure_stage = "remap"
    else:
        _fail()
    return _result(
        runtime_status=runtime_status,
        failure_stage=failure_stage,
        failure_reason=remap_reason,
        compiler_status=compiler_status,
        remap_status=remap_status,
        batch_sample_keys_or_none=observation["batch_sample_keys"],
        compiler_failure_output10_or_none=None,
        remap_output17_or_none=output17,
    )


def run_covapie_current11_task2_runtime_caller_v1(
    *,
    batch: dict[str, object],
    remap_context: object,
    compiler_context: object,
) -> dict[str, object]:
    """Run extractor, compiler, and remap once with caller-owned contexts."""

    try:
        return _run_impl(
            batch=batch,
            remap_context=remap_context,
            compiler_context=compiler_context,
        )
    except Exception as error:
        raise ValueError(_ERROR) from error
