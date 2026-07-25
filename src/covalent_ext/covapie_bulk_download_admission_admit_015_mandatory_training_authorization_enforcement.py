"""Pure in-memory mandatory ADMIT_015 training-authorization guard.

This module validates one result from the committed Exact15 single-rule
runtime.  A successful return authorizes only the caller's in-memory
continuation; this module performs no protected training action.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields
from typing import NoReturn

from covalent_ext import (
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015
    as exact15_runtime,
)


UnifiedAdmissionRuleEvaluation = (
    exact15_runtime.UnifiedAdmissionRuleEvaluation
)

ERROR_SCHEMA_VERSION = (
    "covapie_admit_015_training_authorization_enforcement_error_v1"
)
ADMISSION_RULE_ID = "ADMIT_015"
ADAPTER_ID = "covapie_admit_015_unified_adapter_v1"
RESULT_SCHEMA_VERSION = "covapie_unified_admission_rule_evaluation_v1"
AUTHORIZATION_ITEM = "current_stage_training_authorized"
RESULT_FIELDS = (
    "schema_version",
    "admission_rule_id",
    "admission_rule_name",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "normalized_values",
    "validated_candidate_fields",
    "consumed_candidate_fields",
    "consumed_context_items",
    "evaluator_io_used",
    "adapter_id",
)
RESULT_TYPES = (
    str,
    str,
    str,
    str,
    bool,
    bool,
    str,
    tuple,
    tuple,
    tuple,
    tuple,
    bool,
    str,
)
ERROR_CODES = (
    "ADMIT_015_TRAINING_AUTHORIZATION_DISPATCH_FAILED",
    "ADMIT_015_TRAINING_AUTHORIZATION_RESULT_INVALID",
    "ADMIT_015_TRAINING_AUTHORIZATION_DENIED",
    "ADMIT_015_TRAINING_AUTHORIZATION_REPLAY_FORBIDDEN",
    "ADMIT_015_TRAINING_AUTHORIZATION_REPEATED_CALL_FORBIDDEN",
    "ADMIT_015_TRAINING_AUTHORIZATION_OVERRIDE_FORBIDDEN",
)


@dataclass(frozen=True)
class Admit015TrainingAuthorizationEnforcementError(RuntimeError):
    """Frozen fail-closed error raised by the mandatory guard."""

    schema_version: str
    error_code: str
    admission_rule_id: str
    reason: str

    def __post_init__(self) -> None:
        values = (
            self.schema_version,
            self.error_code,
            self.admission_rule_id,
            self.reason,
        )
        if any(type(value) is not str for value in values):
            raise TypeError("ADMIT_015 enforcement error fields require str")
        if self.schema_version != ERROR_SCHEMA_VERSION:
            raise ValueError("ADMIT_015 enforcement error schema invalid")
        if self.error_code not in ERROR_CODES:
            raise ValueError("ADMIT_015 enforcement error code invalid")
        if self.admission_rule_id != ADMISSION_RULE_ID:
            raise ValueError("ADMIT_015 enforcement error rule invalid")
        if self.reason != self.error_code:
            raise ValueError("ADMIT_015 enforcement error reason invalid")


def _raise_enforcement_error(error_code: str) -> NoReturn:
    raise Admit015TrainingAuthorizationEnforcementError(
        schema_version=ERROR_SCHEMA_VERSION,
        error_code=error_code,
        admission_rule_id=ADMISSION_RULE_ID,
        reason=error_code,
    )


def _is_exact_pass_result(result: object) -> bool:
    result_type = exact15_runtime.UnifiedAdmissionRuleEvaluation
    try:
        storage = vars(result)
        if type(storage) is not dict or tuple(storage) != RESULT_FIELDS:
            return False
        if tuple(field.name for field in fields(result_type)) != RESULT_FIELDS:
            return False
        values = tuple(getattr(result, name) for name in RESULT_FIELDS)
        if any(
            type(value) is not expected
            for value, expected in zip(values, RESULT_TYPES, strict=True)
        ):
            return False
        if result_type(*values) != result:
            return False
        if (
            result.schema_version != RESULT_SCHEMA_VERSION
            or result.admission_rule_id != ADMISSION_RULE_ID
            or result.outcome != "passed"
            or result.passed is not True
            or result.blocks_candidate is not False
            or result.reason != ""
            or result.normalized_values
            != ((AUTHORIZATION_ITEM, "true"),)
            or result.validated_candidate_fields != ()
            or result.consumed_candidate_fields != ()
            or result.consumed_context_items != (AUTHORIZATION_ITEM,)
            or result.evaluator_io_used is not False
            or result.adapter_id != ADAPTER_ID
        ):
            return False
        normalized_pair = result.normalized_values[0]
        if (
            type(normalized_pair) is not tuple
            or len(normalized_pair) != 2
            or type(normalized_pair[0]) is not str
            or type(normalized_pair[1]) is not str
            or any(
                type(item) is not str
                for item in result.consumed_context_items
            )
        ):
            return False
    except (AttributeError, TypeError, ValueError):
        return False
    return True


def require_admit_015_training_authorization(
    candidate_record: Mapping[str, object],
    *,
    stage_authorization_context: Mapping[str, object] | None,
) -> UnifiedAdmissionRuleEvaluation:
    """Return the one exact passing ADMIT_015 result or raise fail closed."""
    try:
        result = exact15_runtime.evaluate_admission_rule(
            ADMISSION_RULE_ID,
            candidate_record,
            batch_context=None,
            evaluation_context=None,
            download_result_context=None,
            stage_authorization_context=stage_authorization_context,
        )
    except Exception:
        _raise_enforcement_error(ERROR_CODES[0])
    if type(result) is not exact15_runtime.UnifiedAdmissionRuleEvaluation:
        _raise_enforcement_error(ERROR_CODES[1])
    if not _is_exact_pass_result(result):
        _raise_enforcement_error(ERROR_CODES[2])
    return result


# === CovaPIE ADMIT_015 MANDATORY TRAINING AUTHORIZATION ENFORCEMENT PUBLIC CLOSURE END ===
