"""Design-only ADMIT_013 formal evaluator interface contract gate.

This module freezes the future seven-keyword signature, structural and business
precedence, and Exact12 result representation.  It intentionally defines no
``evaluate_admit_013`` function, formal ``Admit013EvaluationResult`` type,
adapter, registry entry, dispatcher route, provider/download operation, or
training operation.
"""
from __future__ import annotations

import ast
import csv
import ctypes
import hashlib
import inspect
import io
import json
import os
import re
import stat
import subprocess
import tempfile
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any


PROJECT = "CovaPIE"
STAGE = "covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1"
BASE_COMMIT = "2eea08835c4ef88d5b810509134f8eef94e3e99e"
BASE_PARENT = "30c644de3973ba2968ecaa8ebff97159c07678b9"
BASE_SUBJECT = "add CovaPIE ADMIT_013 download outcome and integrity contract v1"
RECOMMENDED_NEXT_STEP = "implement_covapie_admit_013_standalone_evaluator_interface_v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE

ADMISSION_RULE_ID = "ADMIT_013"
DOWNLOAD_FIELDS = (
    "download_result_status",
    "observed_http_status",
    "observed_content_length_bytes",
    "observed_sha256",
)
AUTHORITY_FIELDS = (
    "expected_content_length_bytes",
    "expected_sha256",
    "explicit_integrity_verdict",
)
PARAMETERS = (*DOWNLOAD_FIELDS, *AUTHORITY_FIELDS)
RESULT_FIELDS = (
    "admission_rule_id",
    "outcome",
    "passed",
    "blocks_candidate",
    "reason",
    "canonical_download_result_record",
    "canonical_integrity_authority_record",
    "validated_download_result_fields",
    "validated_integrity_authority_fields",
    "consumed_download_result_fields",
    "consumed_integrity_authority_fields",
    "evaluator_io_used",
)
OUTCOMES = ("passed", "blocked", "invalid")
VALIDATION_PHASES = (
    "Exact4_presence",
    "Exact4_type_value",
    "Exact3_optional_authority_type_value",
    "Exact7_business_outcome",
    "passed",
)

MISSING_REASONS = (
    "DOWNLOAD_RESULT_STATUS_MISSING",
    "OBSERVED_HTTP_STATUS_MISSING",
    "OBSERVED_CONTENT_LENGTH_BYTES_MISSING",
    "OBSERVED_SHA256_MISSING",
)
DOWNLOAD_TYPE_REASONS = (
    "DOWNLOAD_RESULT_STATUS_TYPE_INVALID",
    "OBSERVED_HTTP_STATUS_TYPE_INVALID",
    "OBSERVED_CONTENT_LENGTH_BYTES_TYPE_INVALID",
    "OBSERVED_SHA256_TYPE_INVALID",
)
DOWNLOAD_VALUE_REASONS = (
    "DOWNLOAD_RESULT_STATUS_VALUE_INVALID",
    "OBSERVED_HTTP_STATUS_RANGE_INVALID",
    "OBSERVED_CONTENT_LENGTH_BYTES_RANGE_INVALID",
    "OBSERVED_SHA256_FORMAT_INVALID",
)
AUTHORITY_TYPE_REASONS = (
    "EXPECTED_CONTENT_LENGTH_BYTES_TYPE_INVALID",
    "EXPECTED_SHA256_TYPE_INVALID",
    "EXPLICIT_INTEGRITY_VERDICT_TYPE_INVALID",
)
AUTHORITY_VALUE_REASONS = (
    "EXPECTED_CONTENT_LENGTH_BYTES_RANGE_INVALID",
    "EXPECTED_SHA256_FORMAT_INVALID",
    "EXPLICIT_INTEGRITY_VERDICT_VALUE_INVALID",
)
BUSINESS_REASONS = (
    "DOWNLOAD_RESULT_STATUS_FAILURE",
    "OBSERVED_HTTP_STATUS_NOT_SUCCESS",
    "OBSERVED_CONTENT_EMPTY",
    "OBSERVED_SHA256_MISMATCH",
    "EXPLICIT_INTEGRITY_VERDICT_FAILED",
    "OBSERVED_CONTENT_LENGTH_MISMATCH",
    "INTEGRITY_AUTHORITY_MISSING",
)
REASON_VOCABULARY = (
    "",
    *MISSING_REASONS,
    *(reason for index in range(4) for reason in (
        DOWNLOAD_TYPE_REASONS[index], DOWNLOAD_VALUE_REASONS[index]
    )),
    *(reason for index in range(3) for reason in (
        AUTHORITY_TYPE_REASONS[index], AUTHORITY_VALUE_REASONS[index]
    )),
    *BUSINESS_REASONS,
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}", flags=re.ASCII)


class _DesignMissingValue:
    __slots__ = ()


_DESIGN_MISSING = _DesignMissingValue()


class _StringSubclass(str):
    pass


class _IntSubclass(int):
    pass


class _TupleSubclass(tuple):
    pass


class _PairTupleSubclass(tuple):
    pass


def _signature_design() -> inspect.Signature:
    return inspect.Signature(
        [
            inspect.Parameter(
                name,
                inspect.Parameter.KEYWORD_ONLY,
                default=_DESIGN_MISSING,
                annotation=object,
            )
            for name in PARAMETERS
        ],
        return_annotation="Admit013EvaluationResult",
    )


FORMAL_SIGNATURE_DESIGN = _signature_design()
FUTURE_PUBLIC_SIGNATURE = (
    "evaluate_admit_013(*, download_result_status: object = _MISSING, "
    "observed_http_status: object = _MISSING, "
    "observed_content_length_bytes: object = _MISSING, "
    "observed_sha256: object = _MISSING, "
    "expected_content_length_bytes: object = _MISSING, "
    "expected_sha256: object = _MISSING, "
    "explicit_integrity_verdict: object = _MISSING) -> Admit013EvaluationResult"
)


@dataclass(frozen=True)
class Admit013FormalEvaluatorInterfaceContractDesign:
    signature: object = FORMAL_SIGNATURE_DESIGN
    parameter_order: tuple[str, ...] = PARAMETERS
    result_field_order: tuple[str, ...] = RESULT_FIELDS

    def __post_init__(self) -> None:
        if type(self) is not Admit013FormalEvaluatorInterfaceContractDesign:
            raise TypeError("interface ContractDesign subclasses are forbidden")
        if self.signature is not FORMAL_SIGNATURE_DESIGN:
            raise ValueError("formal signature Design identity changed")


def _download_value_valid(index: int, value: object) -> bool:
    if index == 0:
        return type(value) is str and value in {"success", "failure"}
    if index == 1:
        return type(value) is int and 100 <= value <= 599
    if index == 2:
        return type(value) is int and value >= 0
    return type(value) is str and _SHA256_RE.fullmatch(value) is not None


def _authority_value_valid(index: int, value: object) -> bool:
    if index == 0:
        return type(value) is int and value >= 0
    if index == 1:
        return type(value) is str and _SHA256_RE.fullmatch(value) is not None
    return type(value) is str and value in {"verified", "failed"}


def _pair_record_valid(
    value: object,
    names: tuple[str, ...],
    validator: Any,
    *,
    require_complete: bool,
) -> bool:
    if type(value) is not tuple:
        return False
    if require_complete and len(value) != len(names):
        return False
    positions = []
    for pair in value:
        if type(pair) is not tuple or len(pair) != 2 or type(pair[0]) is not str:
            return False
        if pair[0] not in names:
            return False
        index = names.index(pair[0])
        if not validator(index, pair[1]):
            return False
        positions.append(index)
    return positions == sorted(set(positions))


def _name_tuple_valid(value: object, names: tuple[str, ...], *, prefix: bool) -> bool:
    if type(value) is not tuple or any(type(item) is not str for item in value):
        return False
    if prefix:
        return value == names[:len(value)]
    positions = [names.index(item) for item in value if item in names]
    return len(positions) == len(value) and positions == sorted(set(positions))


def _business_reason(
    download: tuple[tuple[str, object], ...],
    authority: tuple[tuple[str, object], ...],
) -> str:
    values = dict(download)
    authorities = dict(authority)
    if values[DOWNLOAD_FIELDS[0]] == "failure":
        return BUSINESS_REASONS[0]
    if not 200 <= values[DOWNLOAD_FIELDS[1]] <= 299:
        return BUSINESS_REASONS[1]
    if values[DOWNLOAD_FIELDS[2]] == 0:
        return BUSINESS_REASONS[2]
    if (
        AUTHORITY_FIELDS[1] in authorities
        and authorities[AUTHORITY_FIELDS[1]] != values[DOWNLOAD_FIELDS[3]]
    ):
        return BUSINESS_REASONS[3]
    if authorities.get(AUTHORITY_FIELDS[2]) == "failed":
        return BUSINESS_REASONS[4]
    if (
        AUTHORITY_FIELDS[0] in authorities
        and authorities[AUTHORITY_FIELDS[0]] != values[DOWNLOAD_FIELDS[2]]
    ):
        return BUSINESS_REASONS[5]
    strong = (
        authorities.get(AUTHORITY_FIELDS[1]) == values[DOWNLOAD_FIELDS[3]]
        or authorities.get(AUTHORITY_FIELDS[2]) == "verified"
    )
    return "" if strong else BUSINESS_REASONS[6]


@dataclass(frozen=True)
class Admit013EvaluationResultContractDesign:
    admission_rule_id: object
    outcome: object
    passed: object
    blocks_candidate: object
    reason: object
    canonical_download_result_record: object
    canonical_integrity_authority_record: object
    validated_download_result_fields: object
    validated_integrity_authority_fields: object
    consumed_download_result_fields: object
    consumed_integrity_authority_fields: object
    evaluator_io_used: object

    def __post_init__(self) -> None:
        if type(self) is not Admit013EvaluationResultContractDesign:
            raise TypeError("result ContractDesign subclasses are forbidden")
        if tuple(field.name for field in fields(type(self))) != RESULT_FIELDS:
            raise TypeError("result ContractDesign storage order changed")
        if any(
            type(value) is not str
            for value in (self.admission_rule_id, self.outcome, self.reason)
        ):
            raise TypeError("result string fields require exact built-in str")
        if any(
            type(value) is not bool
            for value in (self.passed, self.blocks_candidate, self.evaluator_io_used)
        ):
            raise TypeError("result boolean fields require exact built-in bool")
        tuple_values = (
            self.canonical_download_result_record,
            self.canonical_integrity_authority_record,
            self.validated_download_result_fields,
            self.validated_integrity_authority_fields,
            self.consumed_download_result_fields,
            self.consumed_integrity_authority_fields,
        )
        if any(type(value) is not tuple for value in tuple_values):
            raise TypeError("result tuple fields require exact built-in tuple")
        if self.admission_rule_id != ADMISSION_RULE_ID or self.outcome not in OUTCOMES:
            raise ValueError("result identity or outcome invalid")
        if self.passed is not (self.outcome == "passed"):
            raise ValueError("passed flag contradicts outcome")
        if self.blocks_candidate is not (self.outcome != "passed"):
            raise ValueError("blocks_candidate contradicts outcome")
        if self.reason not in REASON_VOCABULARY:
            raise ValueError("reason is outside the closed Exact26 vocabulary")
        if (self.reason == "") is not (self.outcome == "passed"):
            raise ValueError("reason empty iff passed invariant failed")
        if self.evaluator_io_used is not False:
            raise ValueError("evaluator_io_used must be exact false")
        if not _pair_record_valid(
            self.canonical_download_result_record,
            DOWNLOAD_FIELDS,
            _download_value_valid,
            require_complete=self.canonical_download_result_record != (),
        ):
            raise ValueError("canonical download record malformed")
        if not _pair_record_valid(
            self.canonical_integrity_authority_record,
            AUTHORITY_FIELDS,
            _authority_value_valid,
            require_complete=False,
        ):
            raise ValueError("canonical authority record malformed")
        if not _name_tuple_valid(
            self.validated_download_result_fields, DOWNLOAD_FIELDS, prefix=True
        ) or not _name_tuple_valid(
            self.consumed_download_result_fields, DOWNLOAD_FIELDS, prefix=True
        ):
            raise ValueError("download validated/consumed tuple malformed")
        if not _name_tuple_valid(
            self.validated_integrity_authority_fields, AUTHORITY_FIELDS, prefix=False
        ) or not _name_tuple_valid(
            self.consumed_integrity_authority_fields, AUTHORITY_FIELDS, prefix=True
        ):
            raise ValueError("authority validated/consumed tuple malformed")
        if self.validated_integrity_authority_fields != tuple(
            pair[0] for pair in self.canonical_integrity_authority_record
        ):
            raise ValueError("authority canonical and validated names disagree")

        if self.reason in MISSING_REASONS:
            index = MISSING_REASONS.index(self.reason)
            expected = (
                "blocked", (), (), DOWNLOAD_FIELDS[:index], (),
                DOWNLOAD_FIELDS[:index + 1], (),
            )
        elif self.reason in DOWNLOAD_TYPE_REASONS or self.reason in DOWNLOAD_VALUE_REASONS:
            reasons = (
                DOWNLOAD_TYPE_REASONS
                if self.reason in DOWNLOAD_TYPE_REASONS
                else DOWNLOAD_VALUE_REASONS
            )
            index = reasons.index(self.reason)
            expected = (
                "invalid", (), (), DOWNLOAD_FIELDS[:index], (), DOWNLOAD_FIELDS, (),
            )
        elif self.reason in AUTHORITY_TYPE_REASONS or self.reason in AUTHORITY_VALUE_REASONS:
            reasons = (
                AUTHORITY_TYPE_REASONS
                if self.reason in AUTHORITY_TYPE_REASONS
                else AUTHORITY_VALUE_REASONS
            )
            index = reasons.index(self.reason)
            if len(self.canonical_download_result_record) != 4:
                raise ValueError("authority failure requires complete canonical Exact4")
            if any(
                AUTHORITY_FIELDS.index(pair[0]) >= index
                for pair in self.canonical_integrity_authority_record
            ):
                raise ValueError("authority canonical record includes failure/later field")
            expected = (
                "invalid",
                self.canonical_download_result_record,
                self.canonical_integrity_authority_record,
                DOWNLOAD_FIELDS,
                self.validated_integrity_authority_fields,
                DOWNLOAD_FIELDS,
                AUTHORITY_FIELDS[:index + 1],
            )
        else:
            if len(self.canonical_download_result_record) != 4:
                raise ValueError("business result requires complete canonical Exact4")
            business_reason = _business_reason(
                self.canonical_download_result_record,
                self.canonical_integrity_authority_record,
            )
            expected_outcome = "passed" if business_reason == "" else "blocked"
            if self.reason != business_reason:
                raise ValueError("business result reason contradicts frozen precedence")
            expected = (
                expected_outcome,
                self.canonical_download_result_record,
                self.canonical_integrity_authority_record,
                DOWNLOAD_FIELDS,
                self.validated_integrity_authority_fields,
                DOWNLOAD_FIELDS,
                AUTHORITY_FIELDS,
            )
        observed = (
            self.outcome,
            self.canonical_download_result_record,
            self.canonical_integrity_authority_record,
            self.validated_download_result_fields,
            self.validated_integrity_authority_fields,
            self.consumed_download_result_fields,
            self.consumed_integrity_authority_fields,
        )
        if observed != expected:
            raise ValueError("result state contradicts frozen reason semantics")


def validate_admit_013_evaluation_result_contract_design(value: object) -> bool:
    if type(value) is not Admit013EvaluationResultContractDesign:
        raise TypeError("exact Admit013 EvaluationResult ContractDesign required")
    reconstructed = Admit013EvaluationResultContractDesign(
        *(getattr(value, name) for name in RESULT_FIELDS)
    )
    if reconstructed != value:
        raise ValueError("result ContractDesign reconstruction mismatch")
    return True


def _make_result(
    outcome: str,
    reason: str,
    download: tuple[tuple[str, object], ...],
    authority: tuple[tuple[str, object], ...],
    validated_download: tuple[str, ...],
    validated_authority: tuple[str, ...],
    consumed_download: tuple[str, ...],
    consumed_authority: tuple[str, ...],
) -> Admit013EvaluationResultContractDesign:
    return Admit013EvaluationResultContractDesign(
        ADMISSION_RULE_ID,
        outcome,
        outcome == "passed",
        outcome != "passed",
        reason,
        download,
        authority,
        validated_download,
        validated_authority,
        consumed_download,
        consumed_authority,
        False,
    )


def classify_admit_013_formal_evaluator_interface_design(
    *,
    download_result_status: object = _DESIGN_MISSING,
    observed_http_status: object = _DESIGN_MISSING,
    observed_content_length_bytes: object = _DESIGN_MISSING,
    observed_sha256: object = _DESIGN_MISSING,
    expected_content_length_bytes: object = _DESIGN_MISSING,
    expected_sha256: object = _DESIGN_MISSING,
    explicit_integrity_verdict: object = _DESIGN_MISSING,
) -> Admit013EvaluationResultContractDesign:
    """Pure in-memory Design oracle; this is not the future public evaluator."""
    download_values = (
        download_result_status,
        observed_http_status,
        observed_content_length_bytes,
        observed_sha256,
    )
    authority_values = (
        expected_content_length_bytes,
        expected_sha256,
        explicit_integrity_verdict,
    )
    for index, value in enumerate(download_values):
        if value is _DESIGN_MISSING:
            return _make_result(
                "blocked", MISSING_REASONS[index], (), (), DOWNLOAD_FIELDS[:index], (),
                DOWNLOAD_FIELDS[:index + 1], (),
            )

    download_record: list[tuple[str, object]] = []
    for index, value in enumerate(download_values):
        expected_type = (str, int, int, str)[index]
        if type(value) is not expected_type:
            return _make_result(
                "invalid", DOWNLOAD_TYPE_REASONS[index], (), (), DOWNLOAD_FIELDS[:index], (),
                DOWNLOAD_FIELDS, (),
            )
        if not _download_value_valid(index, value):
            return _make_result(
                "invalid", DOWNLOAD_VALUE_REASONS[index], (), (), DOWNLOAD_FIELDS[:index], (),
                DOWNLOAD_FIELDS, (),
            )
        download_record.append((DOWNLOAD_FIELDS[index], value))
    canonical_download = tuple(download_record)

    authority_record: list[tuple[str, object]] = []
    for index, value in enumerate(authority_values):
        if value is _DESIGN_MISSING:
            continue
        expected_type = (int, str, str)[index]
        if type(value) is not expected_type:
            return _make_result(
                "invalid", AUTHORITY_TYPE_REASONS[index], canonical_download,
                tuple(authority_record), DOWNLOAD_FIELDS,
                tuple(pair[0] for pair in authority_record), DOWNLOAD_FIELDS,
                AUTHORITY_FIELDS[:index + 1],
            )
        if not _authority_value_valid(index, value):
            return _make_result(
                "invalid", AUTHORITY_VALUE_REASONS[index], canonical_download,
                tuple(authority_record), DOWNLOAD_FIELDS,
                tuple(pair[0] for pair in authority_record), DOWNLOAD_FIELDS,
                AUTHORITY_FIELDS[:index + 1],
            )
        authority_record.append((AUTHORITY_FIELDS[index], value))
    canonical_authority = tuple(authority_record)
    reason = _business_reason(canonical_download, canonical_authority)
    outcome = "passed" if reason == "" else "blocked"
    return _make_result(
        outcome, reason, canonical_download, canonical_authority, DOWNLOAD_FIELDS,
        tuple(pair[0] for pair in canonical_authority), DOWNLOAD_FIELDS,
        AUTHORITY_FIELDS,
    )


CONTRACT_FILE = "covapie_admit_013_formal_evaluator_interface_and_result_contract.csv"
ROUTING_FILE = "covapie_admit_013_formal_evaluator_routing_and_consumption_contract.csv"
TRUTH_FILE = "covapie_admit_013_formal_evaluator_interface_truth_matrix.csv"
SOURCE_FILE = "covapie_admit_013_formal_evaluator_interface_source_boundary_audit.csv"
ISSUE_FILE = "covapie_admit_013_formal_evaluator_interface_issue_readiness_inventory.csv"
MANIFEST_FILE = "covapie_admit_013_formal_evaluator_interface_contract_manifest.json"
OUTPUT_FILES = (
    CONTRACT_FILE,
    ROUTING_FILE,
    TRUTH_FILE,
    SOURCE_FILE,
    ISSUE_FILE,
    MANIFEST_FILE,
)

SOURCE_SHA256 = {
    "src/covalent_ext/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_design_gate.py": "bcec99607dc5a27a6b62fe788c93f4a24f12d9af387a6e14c7d1695d2c4482b8",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1/covapie_admit_013_download_outcome_policy_contract.csv": "2b64ce56c122ede2ea125944c164243e5bb7dc3da89c50607f29dd647208b43a",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1/covapie_admit_013_integrity_authority_contract.csv": "d95035d109a2c62646f11c822b50b18ab2e25ded1bfebd13e82a37b9723fa0e1",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1/covapie_admit_013_failure_taxonomy_and_precedence.csv": "42bead68915f7260aa2c48dabfe2968623de85a039a20a3b78682af246469031",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1/covapie_admit_013_download_outcome_and_integrity_truth_matrix.csv": "7e856eb5ebd995793dcd82fb75266c7ee6f6a8b06b7785f3a70713a96b8efdbb",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1/covapie_admit_013_issue_readiness_inventory.csv": "240012c88668a3228139052d3920d02b839329fdda41280d31b5382b9de3620c",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1/covapie_admit_013_download_outcome_and_integrity_contract_manifest.json": "1bbfe88f459946b78bb14e5b0b672582d508a838bef220ecf292fa84d15f934d",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_preconditions_audit_v1/covapie_admit_013_formal_evaluator_precondition_matrix.csv": "4b411c86cce23351d4aec3d58a894d161ab163e0305fdd91853bc54f16aa1fdf",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_preconditions_audit_v1/covapie_admit_013_issue_readiness_inventory.csv": "204923bbf26c286c14ce4feaeb7934b279cafa54287ba96b4e2455fd84cf1198",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_013_rule_logic_interface_preconditions_audit_v1/covapie_admit_013_formal_evaluator_preconditions_manifest.json": "63f0f96a960135117b0c4c8d3f80d1991cb8138e7df69d3917e921a6a4c74ce0",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_download_integrity_field_contract_v1/covapie_admit_012_download_integrity_field_contract.csv": "03aef0a14257d9a2c028fcc3dd84c161c29b09bca1a1c71456edc66e2e73c9ce",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_interface_and_result_contract.csv": "682192b492979d9b6114381cbfc02d57c349e3cd8db2541a01177235d34c04e6",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_formal_evaluator_interface_contract_v1/covapie_admit_012_formal_evaluator_routing_and_consumption_contract.csv": "44709c3a679368476c87bcd97dafa2f9cf9bddb4af534c6eb950c565d0919aec",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_contract.csv": "c5c383e9a9e17c5eb5a4b2c92455da89a78e66f75df7ff31ce0494f08281433e",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_rule_logic_interface_v1/covapie_admit_012_rule_logic_interface_manifest.json": "ad131895c0acfdaf5b350105031647bdcac9667370fb6cd43baf8826bea995c8",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1/covapie_admit_012_unified_adapter_contract.csv": "12228051428134223dc4db4ec418ced573637047189056f1fb8df908ca2fe6c8",
    "data/derived/covalent_small/covapie_bulk_download_admission_admit_012_unified_adapter_contract_v1/covapie_admit_012_unified_adapter_contract_manifest.json": "1df0e2a09817b7763ec4eb767663db169d3239385094da151af28150c2c55d25",
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012.py": "4d9a49806d4ef71a95c8ad032dfa061f7473b1cb55a573459c155f0cd5d57282",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1/covapie_admit_001_to_012_registry_and_identity_audit.csv": "57ed1f04df27c7b30ec4cea97aead99e7788a2968f77245280850ae26f399e59",
    "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012_v1/covapie_admit_001_to_012_runtime_manifest.json": "bc909aefd86b62139fbb62025d9c323988a4c232ab9c960efb291fb0c196cee3",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_rule_registry.csv": "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_schema_contract.csv": "44ca53db60e210ffe1200d32f449c1fd94107f2775ed19b9c14f3a1e982e9710",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_rule_executability_matrix.csv": "a7782e48cac282b047a392ee20b5b26a72fa1b2208a3889edf8b1c8af923921b",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_field_semantics_matrix.csv": "a64a746cd13eb8f8421fcab1298f5657147e7882b8c786cf956f8096187966a1",
    "data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_evaluation_context_contract.csv": "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0",
}
SOURCE_PATHS = tuple(Path(path) for path in SOURCE_SHA256)
SOURCE_PATH_LIST_SHA256 = hashlib.sha256(
    json.dumps([path.as_posix() for path in SOURCE_PATHS], separators=(",", ":")).encode()
).hexdigest()
SOURCE_PATH_SHA256_PAIRS_SHA256 = hashlib.sha256(
    json.dumps(
        [[path.as_posix(), SOURCE_SHA256[path.as_posix()]] for path in SOURCE_PATHS],
        separators=(",", ":"),
    ).encode()
).hexdigest()


@dataclass(frozen=True)
class _Source:
    path: Path
    content: bytes
    sha256: str
    base_mode: str


def _git(arguments: list[str], *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *arguments], cwd=REPO_ROOT, capture_output=True, text=text, check=False
    )


def _identity(item: os.stat_result) -> tuple[int, int, int]:
    return item.st_dev, item.st_ino, item.st_mode


def _assert_repo_root() -> tuple[int, int, int]:
    item = os.lstat(REPO_ROOT)
    if (
        stat.S_ISLNK(item.st_mode)
        or not stat.S_ISDIR(item.st_mode)
        or REPO_ROOT.resolve(strict=True) != REPO_ROOT
    ):
        raise ValueError("unsafe repository root")
    return _identity(item)


def _assert_parent_chain(path: Path) -> None:
    current = (REPO_ROOT / path).parent
    while current != REPO_ROOT:
        item = os.lstat(current)
        if stat.S_ISLNK(item.st_mode) or not stat.S_ISDIR(item.st_mode):
            raise ValueError("unsafe source parent chain")
        current = current.parent


def _pinned_read(path: Path, expected_identity: tuple[int, int, int]) -> bytes:
    absolute = REPO_ROOT / path
    if _identity(os.lstat(absolute)) != expected_identity:
        raise ValueError("source identity drift before open")
    descriptor = os.open(
        absolute,
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        if _identity(os.fstat(descriptor)) != expected_identity:
            raise ValueError("source stat/open race")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        if _identity(os.fstat(descriptor)) != expected_identity:
            raise ValueError("source FD identity drift")
        if _identity(os.lstat(absolute)) != expected_identity:
            raise ValueError("source lexical identity drift")
        _assert_parent_chain(path)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _assert_base_lineage() -> None:
    identity = _git(["show", "-s", "--format=%H%n%P%n%s", BASE_COMMIT])
    ancestor = _git(["merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"])
    if identity.returncode or ancestor.returncode:
        raise ValueError("base lineage unavailable")
    if identity.stdout.splitlines() != [BASE_COMMIT, BASE_PARENT, BASE_SUBJECT]:
        raise ValueError("base identity drift")


def build_frozen_source_snapshot() -> tuple[_Source, ...]:
    root_identity = _assert_repo_root()
    _assert_base_lineage()
    if len(SOURCE_PATHS) != 25 or len(set(SOURCE_PATHS)) != 25:
        raise ValueError("source boundary must be fixed Exact25")
    structures: list[tuple[Path, str, tuple[int, int, int]]] = []
    for path in SOURCE_PATHS:
        if (
            path.is_absolute()
            or ".." in path.parts
            or path.parts[:2] == ("data", "raw")
            or path.parts[0] == "checkpoints"
            or STAGE in path.parts
        ):
            raise ValueError("unsafe source path")
        _assert_parent_chain(path)
        absolute = REPO_ROOT / path
        item = os.lstat(absolute)
        tree = _git(["ls-tree", BASE_COMMIT, "--", path.as_posix()])
        tracked = _git(["ls-files", "--error-unmatch", "--", path.as_posix()])
        head, separator, tree_path = tree.stdout.partition("\t")
        parts = head.split()
        if (
            tree.returncode
            or tracked.returncode
            or tracked.stdout.splitlines() != [path.as_posix()]
            or not separator
            or tree_path.strip() != path.as_posix()
            or len(parts) != 3
            or parts[0] not in {"100644", "100755"}
            or parts[1] != "blob"
            or stat.S_ISLNK(item.st_mode)
            or not stat.S_ISREG(item.st_mode)
            or absolute.resolve(strict=True) != absolute
        ):
            raise ValueError(f"unsafe committed source: {path}")
        structures.append((path, parts[0], _identity(item)))
    records = []
    for path, mode, frozen_identity in structures:
        base = _git(["show", f"{BASE_COMMIT}:{path.as_posix()}"], text=False)
        current = _pinned_read(path, frozen_identity)
        digest = hashlib.sha256(current).hexdigest()
        if (
            base.returncode
            or not isinstance(base.stdout, bytes)
            or hashlib.sha256(base.stdout).hexdigest() != digest
            or digest != SOURCE_SHA256[path.as_posix()]
        ):
            raise ValueError(f"source SHA drift: {path}")
        records.append(_Source(path, current, digest, mode))
    if _assert_repo_root() != root_identity:
        raise ValueError("repository root identity drift")
    return tuple(records)


def _source(snapshot: tuple[_Source, ...], suffix: str) -> _Source:
    matches = [record for record in snapshot if record.path.as_posix().endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f"source lookup not unique: {suffix}")
    return matches[0]


def _source_rows(snapshot: tuple[_Source, ...], suffix: str) -> list[dict[str, str]]:
    return list(
        csv.DictReader(io.StringIO(_source(snapshot, suffix).content.decode(), newline=""))
    )


def _source_json(snapshot: tuple[_Source, ...], suffix: str) -> dict[str, Any]:
    return json.loads(_source(snapshot, suffix).content)


def _validate_predecessors(snapshot: tuple[_Source, ...]) -> None:
    outcome_manifest = _source_json(
        snapshot, "covapie_admit_013_download_outcome_and_integrity_contract_manifest.json"
    )
    outcome_truth = _source_rows(
        snapshot, "covapie_admit_013_download_outcome_and_integrity_truth_matrix.csv"
    )
    failure = _source_rows(snapshot, "covapie_admit_013_failure_taxonomy_and_precedence.csv")
    authority = _source_rows(snapshot, "covapie_admit_013_integrity_authority_contract.csv")
    preconditions = _source_rows(snapshot, "covapie_admit_013_formal_evaluator_precondition_matrix.csv")
    precondition_issues = _source_rows(
        snapshot,
        "covapie_bulk_download_admission_admit_013_rule_logic_interface_preconditions_audit_v1/covapie_admit_013_issue_readiness_inventory.csv",
    )
    field_contract = _source_rows(snapshot, "covapie_admit_012_download_integrity_field_contract.csv")
    standalone = _source_json(snapshot, "covapie_admit_012_rule_logic_interface_manifest.json")
    adapter = _source_json(snapshot, "covapie_admit_012_unified_adapter_contract_manifest.json")
    runtime = _source_json(snapshot, "covapie_admit_001_to_012_runtime_manifest.json")
    registry = _source_rows(snapshot, "covapie_bulk_download_admission_rule_registry.csv")
    rule = next(row for row in registry if row["admission_rule_id"] == ADMISSION_RULE_ID)
    if not (
        outcome_manifest["base_commit"] == BASE_PARENT
        and outcome_manifest["exact4_fields"] == list(DOWNLOAD_FIELDS)
        and outcome_manifest["integrity_authority_fields"] == list(AUTHORITY_FIELDS)
        and outcome_manifest["business_failure_precedence"] == list(BUSINESS_REASONS)
        and outcome_manifest["row_counts"]["truth_matrix"] == len(outcome_truth) == 23
        and [row["reason"] for row in failure] == [*BUSINESS_REASONS, ""]
        and [row["authority_name"] for row in authority] == list(AUTHORITY_FIELDS)
        and all(row["presence_required"] == "false" for row in authority)
        and len(preconditions) == 32
        and [row["precondition_id"] for row in preconditions]
        == [f"PRE_{index:03d}" for index in range(1, 33)]
        and len(precondition_issues) == 23
        and next(row for row in preconditions if row["precondition_id"] == "PRE_029")["completeness_status"] == "incomplete"
        and next(row for row in preconditions if row["precondition_id"] == "PRE_030")["completeness_status"] == "incomplete"
        and [row["field_name"] for row in field_contract] == list(DOWNLOAD_FIELDS)
        and standalone["evaluate_admit_012_implemented"] is True
        and adapter["admit_012_unified_adapter_contract_frozen"] is True
        and runtime["registered_rule_count"] == 12
        and runtime["known_not_registered_rule_ids"] == ["ADMIT_013", "ADMIT_014", "ADMIT_015"]
        and runtime["combined_candidate_verdict_implemented"] is False
        and runtime["cross_rule_aggregation_implemented"] is False
        and rule == {
            "admission_rule_id": "ADMIT_013",
            "admission_rule_name": "download_failure_fail_closed",
            "evidence_source": "future_download_result",
            "required_status": "non_success_or_integrity_failure_not_admitted",
            "failure_severity": "blocking",
            "blocking_reason": "download_failure_must_fail_closed",
            "evaluation_phase": "post_download",
            "network_required": "false",
            "raw_structure_required": "false",
            "ready_for_future_implementation": "true",
        }
    ):
        raise ValueError("predecessor formal-interface evidence mismatch")


CONTRACT_COLUMNS = (
    "contract_order", "contract_section", "section_order", "public_name",
    "formal_type", "presence", "default_or_absence", "source_envelope",
    "validation_rule", "invariant", "contract_passed",
)
ROUTING_COLUMNS = (
    "route_order", "case_id", "contract_kind", "source_envelope", "source_key",
    "formal_parameter", "presence", "missing_representation", "consumed_semantics",
    "validated_semantics", "canonical_semantics", "adapter_responsibility",
    "evaluator_responsibility", "route_passed",
)
TRUTH_COLUMNS = (
    "case_order", "case_id", "case_group", "assertion_kind", "inherited_case_id",
    *(f"{name}_representation" for name in PARAMETERS),
    "expected_outcome", "expected_reason", "expected_canonical_download_result_record",
    "expected_canonical_integrity_authority_record",
    "expected_validated_download_result_fields",
    "expected_validated_integrity_authority_fields",
    "expected_consumed_download_result_fields",
    "expected_consumed_integrity_authority_fields",
    "expected_passed", "expected_blocks_candidate", "expected_evaluator_io_used",
    "observed_design_result", "case_passed",
)
SOURCE_COLUMNS = (
    "source_order", "source_relative_path", "source_kind", "expected_sha256",
    "observed_sha256", "base_blob_sha256", "base_tree_mode", "git_tracked",
    "filesystem_regular", "non_symlink", "parent_chain_non_symlink",
    "pinned_fd_no_follow_read", "raw_checkpoint_excluded", "audit_result",
)
ISSUE_COLUMNS = (
    "inherited_order", "issue_id", "issue_type", "affected_fields", "affected_rules",
    "severity", "status", "blocking_scope", "blocking_reason", "issue_origin",
    "integration_transition", "issue_count", "inherited_effective_status",
    "inherited_transition_stage", "inherited_transition_action",
    "inherited_transition_evidence", "successor_effective_status",
    "successor_transition_stage", "successor_transition_action",
    "successor_transition_evidence",
)


def _contract_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def add(
        section: str,
        name: str,
        formal_type: str,
        presence: str,
        default: str,
        source: str,
        validation: str,
        invariant: str,
    ) -> None:
        rows.append({
            "contract_order": str(len(rows) + 1),
            "contract_section": section,
            "section_order": str(1 + sum(row["contract_section"] == section for row in rows)),
            "public_name": name,
            "formal_type": formal_type,
            "presence": presence,
            "default_or_absence": default,
            "source_envelope": source,
            "validation_rule": validation,
            "invariant": invariant,
            "contract_passed": "true",
        })

    download_rules = (
        "exact built-in str; success|failure",
        "exact built-in int; inclusive structural range 100..599",
        "exact built-in int; >= 0; zero structurally legal",
        "exact built-in str; ASCII lowercase [0-9a-f]{64}",
    )
    authority_rules = (
        "when present exact built-in int; >= 0; corroborating only",
        "when present exact built-in str; ASCII lowercase [0-9a-f]{64}; exact match is strong authority",
        "when present exact built-in str; verified|failed; verified is strong authority",
    )
    for name, rule in zip(DOWNLOAD_FIELDS, download_rules, strict=True):
        add(
            "signature_parameter", name, "object", "required",
            "future private _MISSING singleton", "download_result_context",
            f"keyword-only; {rule}",
            "missing distinct from None/False/0/empty; no normalization",
        )
    for name, rule in zip(AUTHORITY_FIELDS, authority_rules, strict=True):
        add(
            "signature_parameter", name, "object", "optional",
            "future private _MISSING singleton means legal absence", "evaluation_context",
            f"keyword-only; {rule}",
            "missing omitted from canonical/validated but still consumed during authority phase",
        )
    result_types = (
        "exact str", "exact str", "exact bool", "exact bool", "exact str",
        "exact tuple of exact pair tuples", "exact tuple of exact pair tuples",
        "exact tuple of exact str", "exact tuple of exact str",
        "exact tuple of exact str", "exact tuple of exact str", "exact bool",
    )
    for name, formal_type in zip(RESULT_FIELDS, result_types, strict=True):
        add(
            "result_field", name, formal_type, "required", "not_applicable",
            "standalone_evaluator_result", "Exact12 ordered field",
            "exact dataclass storage order; reconstructable in that order",
        )
    invariants = (
        ("passed_iff_outcome", "passed == (outcome == 'passed')"),
        ("blocks_iff_not_passed", "blocks_candidate == (outcome != 'passed')"),
        ("reason_empty_iff_passed", "reason == '' iff outcome == passed"),
        ("io", "evaluator_io_used is exact false"),
        ("missing_outcome", "Exact4 missing reason implies blocked"),
        ("structural_invalid_outcome", "Exact4/Exact3 type/value reason implies invalid"),
        ("business_outcome", "Exact7 business reason implies blocked"),
        ("canonical_download", "empty before Exact4 structural success; otherwise complete ordered Exact4 pairs"),
        ("canonical_authority", "ordered subset of present structurally valid Exact3 pairs only"),
        ("validated_download", "ordered names completed before failure; complete after Exact4 success"),
        ("validated_authority", "ordered names for provided structurally valid authorities only"),
        ("consumed_download", "actual ordered lookup prefix; complete after presence phase"),
        ("consumed_authority", "actual Exact3 lookup prefix including missing optional names"),
        ("canonical_exactness", "outer/pairs exact tuple; names exact str; raw values retain exact type"),
        ("sentinel_no_leak", "no runtime or Design missing sentinel in any result representation"),
    )
    for name, rule in invariants:
        add(
            "result_invariant", name, "invariant", "required", "not_applicable",
            "result_contract", rule, rule,
        )
    for reason in REASON_VOCABULARY:
        add(
            "reason_vocabulary", reason if reason else "<empty>", "exact str", "required",
            "not_applicable", "result_contract", "closed Exact26 vocabulary member",
            "no UNKNOWN/OTHER/INTERNAL_ERROR/UNEXPECTED/catch-all/free text",
        )
    for phase in VALIDATION_PHASES:
        add(
            "validation_phase", phase, "precedence_phase", "required", "not_applicable",
            "standalone_evaluator", phase, "first failure returns immediately",
        )
    for rank, reason in enumerate((*BUSINESS_REASONS, ""), 1):
        add(
            "business_precedence", reason if reason else "<passed>", "precedence_step",
            "required", "not_applicable", "standalone_evaluator",
            f"rank {rank}", "structural validation completes before business evaluation",
        )
    for name in (
        "evaluate_admit_013_not_implemented",
        "Admit013EvaluationResult_not_implemented",
        "adapter_registry_exact13_not_implemented",
    ):
        add(
            "formal_symbol_state", name, "design assertion", "required", "not_applicable",
            "production_design_gate", "formal runtime symbol absent", "Design names are not runtime symbols",
        )
    return rows


def _routing_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    def add(
        case_id: str,
        kind: str,
        envelope: str,
        key: str,
        parameter: str,
        presence: str,
        missing: str,
        consumed: str,
        validated: str,
        canonical: str,
        adapter: str,
        evaluator: str,
    ) -> None:
        rows.append({
            "route_order": str(len(rows) + 1), "case_id": case_id,
            "contract_kind": kind, "source_envelope": envelope, "source_key": key,
            "formal_parameter": parameter, "presence": presence,
            "missing_representation": missing, "consumed_semantics": consumed,
            "validated_semantics": validated, "canonical_semantics": canonical,
            "adapter_responsibility": adapter, "evaluator_responsibility": evaluator,
            "route_passed": "true",
        })

    for name in DOWNLOAD_FIELDS:
        add(
            f"ROUTE_{name.upper()}", "route", "download_result_context", name, name,
            "required", "future private missing singleton", "case-dependent Exact4 prefix",
            "case-dependent Exact4 validated names", "raw value pair after all Exact4 structural success",
            "future extraction and scalar pass-through only", "presence/type/value validation",
        )
    for name in AUTHORITY_FIELDS:
        add(
            f"ROUTE_{name.upper()}", "route", "evaluation_context", name, name,
            "optional", "future private missing singleton is legal absence", "Exact3 checked prefix",
            "present-valid authority names only", "present-valid raw pair only",
            "future optional lookup and scalar pass-through only", "optional type/value validation",
        )
    for envelope in (
        "candidate_record", "batch_context", "stage_authorization_context", "fallback_envelope",
        "filesystem", "network", "raw", "provider_or_download_execution_inside_evaluator",
    ):
        add(
            f"FORBIDDEN_{envelope.upper()}", "forbidden_route", envelope, "*", "",
            "forbidden", "not_applicable", "none", "none", "none",
            "must not source any formal parameter", "does not access envelope or I/O",
        )
    for index, name in enumerate(DOWNLOAD_FIELDS):
        add(
            f"MISSING_{name.upper()}", "consumption_case", "standalone_evaluator", name, name,
            "required", "private singleton", "|".join(DOWNLOAD_FIELDS[:index + 1]),
            "|".join(DOWNLOAD_FIELDS[:index]), "empty", "route scalar by identity",
            "blocked at first missing during Exact4 presence",
        )
        add(
            f"INVALID_{name.upper()}", "consumption_case", "standalone_evaluator", name, name,
            "required", "present invalid", "|".join(DOWNLOAD_FIELDS),
            "|".join(DOWNLOAD_FIELDS[:index]), "empty", "route scalar by identity",
            "invalid at first Exact4 type/value failure",
        )
    for index, name in enumerate(AUTHORITY_FIELDS):
        add(
            f"INVALID_{name.upper()}", "consumption_case", "standalone_evaluator", name, name,
            "optional", "present invalid", "|".join(AUTHORITY_FIELDS[:index + 1]),
            "provided valid authority names before failure",
            "provided valid authority pairs before failure", "route optional scalar by identity",
            "invalid before every business reason",
        )
    for case_id in ("BUSINESS_BLOCKED", "PASSED"):
        add(
            case_id, "consumption_case", "standalone_evaluator", "Exact7", "Exact7",
            "mixed required/optional", "optional absence legal", "complete Exact4|complete Exact3 lookups",
            "complete Exact4 names|present-valid Exact3 names",
            "complete Exact4 pairs|present-valid Exact3 pairs", "route only two authorized envelopes",
            "pure in-memory business evaluation with no normalization/recompute",
        )
    add(
        "NO_ADMIT012_RESULT_DEPENDENCY", "dependency_boundary", "none",
        "Admit012EvaluationResult", "", "forbidden", "not_applicable", "none", "none", "none",
        "ADMIT_012 may only be a logical pipeline prerequisite",
        "no prior_admit_012_result or cross-rule Python object consumption",
    )
    add(
        "SCALAR_ONLY", "call_shape", "two authorized envelopes", "Exact7", "Exact7 scalar keywords",
        "mixed required/optional", "private singleton only", "no Mapping consumption",
        "no Mapping consumption", "no Mapping result input", "future adapter extracts scalars",
        "no dynamic Mapping/policy-context/*args/**kwargs",
    )
    return rows


SHA_A = "0123456789abcdef" * 4
SHA_B = "abcdef0123456789" * 4


@dataclass(frozen=True)
class _Case:
    case_id: str
    group: str
    values: tuple[object, object, object, object, object, object, object]
    outcome: str
    reason: str
    inherited_case_id: str = ""
    negative_result_case: str = ""


def _base_values() -> tuple[object, object, object, object, object, object, object]:
    return ("success", 200, 10, SHA_A, _DESIGN_MISSING, SHA_A, _DESIGN_MISSING)


def _with(
    values: tuple[object, object, object, object, object, object, object],
    **changes: object,
) -> tuple[object, object, object, object, object, object, object]:
    result = list(values)
    for name, value in changes.items():
        result[PARAMETERS.index(name)] = value
    return tuple(result)  # type: ignore[return-value]


def _interface_cases() -> list[_Case]:
    base = _base_values()
    cases: list[_Case] = []
    for index, name in enumerate(DOWNLOAD_FIELDS):
        values = list(base)
        values[index] = _DESIGN_MISSING
        cases.append(_Case(f"PRESENCE_{name.upper()}_MISSING", "exact4_presence", tuple(values), "blocked", MISSING_REASONS[index]))
    cases.extend((
        _Case("PRESENCE_FIRST_AND_LATER_MISSING", "exact4_presence", _with(base, download_result_status=_DESIGN_MISSING, observed_sha256=_DESIGN_MISSING), "blocked", MISSING_REASONS[0]),
        _Case("PRESENCE_SECOND_AND_LATER_MISSING", "exact4_presence", _with(base, observed_http_status=_DESIGN_MISSING, observed_sha256=_DESIGN_MISSING), "blocked", MISSING_REASONS[1]),
        _Case("PRESENCE_FIRST_MISSING_AUTHORITY_INVALID", "cross_phase_precedence", _with(base, download_result_status=_DESIGN_MISSING, expected_content_length_bytes=None), "blocked", MISSING_REASONS[0]),
    ))

    status_invalid = (
        ("NONE", None, DOWNLOAD_TYPE_REASONS[0]),
        ("FALSE", False, DOWNLOAD_TYPE_REASONS[0]),
        ("ZERO", 0, DOWNLOAD_TYPE_REASONS[0]),
        ("STR_SUBCLASS", _StringSubclass("success"), DOWNLOAD_TYPE_REASONS[0]),
        ("UPPERCASE", "SUCCESS", DOWNLOAD_VALUE_REASONS[0]),
        ("EMPTY", "", DOWNLOAD_VALUE_REASONS[0]),
        ("UNKNOWN", "pending", DOWNLOAD_VALUE_REASONS[0]),
    )
    for label, value, reason in status_invalid:
        cases.append(_Case(f"STATUS_{label}", "download_result_status_validation", _with(base, download_result_status=value), "invalid", reason))

    http_invalid = (
        ("BOOL", True, DOWNLOAD_TYPE_REASONS[1]),
        ("INT_SUBCLASS", _IntSubclass(200), DOWNLOAD_TYPE_REASONS[1]),
        ("FLOAT", 200.0, DOWNLOAD_TYPE_REASONS[1]),
        ("STR", "200", DOWNLOAD_TYPE_REASONS[1]),
        ("LOW_99", 99, DOWNLOAD_VALUE_REASONS[1]),
        ("HIGH_600", 600, DOWNLOAD_VALUE_REASONS[1]),
    )
    for label, value, reason in http_invalid:
        cases.append(_Case(f"HTTP_{label}", "observed_http_status_validation", _with(base, observed_http_status=value), "invalid", reason))
    for value, outcome, reason in (
        (100, "blocked", BUSINESS_REASONS[1]), (199, "blocked", BUSINESS_REASONS[1]),
        (200, "passed", ""), (299, "passed", ""),
        (300, "blocked", BUSINESS_REASONS[1]), (599, "blocked", BUSINESS_REASONS[1]),
    ):
        cases.append(_Case(f"HTTP_BOUNDARY_{value}", "observed_http_status_boundary", _with(base, observed_http_status=value), outcome, reason))

    content_invalid = (
        ("BOOL", False, DOWNLOAD_TYPE_REASONS[2]),
        ("INT_SUBCLASS", _IntSubclass(10), DOWNLOAD_TYPE_REASONS[2]),
        ("FLOAT", 10.0, DOWNLOAD_TYPE_REASONS[2]),
        ("STR", "10", DOWNLOAD_TYPE_REASONS[2]),
        ("NEGATIVE", -1, DOWNLOAD_VALUE_REASONS[2]),
    )
    for label, value, reason in content_invalid:
        cases.append(_Case(f"CONTENT_{label}", "observed_content_length_validation", _with(base, observed_content_length_bytes=value), "invalid", reason))
    cases.extend((
        _Case("CONTENT_ZERO_STRUCTURAL_BUSINESS_BLOCK", "observed_content_length_boundary", _with(base, observed_content_length_bytes=0), "blocked", BUSINESS_REASONS[2]),
        _Case("CONTENT_POSITIVE", "observed_content_length_boundary", _with(base, observed_content_length_bytes=1), "passed", ""),
    ))

    sha_invalid = (
        ("NONE", None, DOWNLOAD_TYPE_REASONS[3]),
        ("BYTES", SHA_A.encode(), DOWNLOAD_TYPE_REASONS[3]),
        ("STR_SUBCLASS", _StringSubclass(SHA_A), DOWNLOAD_TYPE_REASONS[3]),
        ("UPPERCASE", SHA_A.upper(), DOWNLOAD_VALUE_REASONS[3]),
        ("LENGTH_63", SHA_A[:-1], DOWNLOAD_VALUE_REASONS[3]),
        ("LENGTH_65", SHA_A + "0", DOWNLOAD_VALUE_REASONS[3]),
        ("NON_HEX", "g" + SHA_A[1:], DOWNLOAD_VALUE_REASONS[3]),
        ("WHITESPACE", " " + SHA_A[:-1], DOWNLOAD_VALUE_REASONS[3]),
    )
    for label, value, reason in sha_invalid:
        cases.append(_Case(f"OBSERVED_SHA_{label}", "observed_sha256_validation", _with(base, observed_sha256=value), "invalid", reason))
    cases.append(_Case("OBSERVED_SHA_VALID_GRAMMAR_NOT_SELF_AUTHORITY", "observed_sha256_validation", _with(base, expected_sha256=_DESIGN_MISSING), "blocked", BUSINESS_REASONS[6]))

    expected_length_cases = (
        ("MISSING", _DESIGN_MISSING, "passed", ""),
        ("NONE", None, "invalid", AUTHORITY_TYPE_REASONS[0]),
        ("BOOL", False, "invalid", AUTHORITY_TYPE_REASONS[0]),
        ("INT_SUBCLASS", _IntSubclass(10), "invalid", AUTHORITY_TYPE_REASONS[0]),
        ("NEGATIVE", -1, "invalid", AUTHORITY_VALUE_REASONS[0]),
        ("ZERO", 0, "blocked", BUSINESS_REASONS[5]),
        ("MATCH", 10, "passed", ""),
        ("MISMATCH", 11, "blocked", BUSINESS_REASONS[5]),
    )
    for label, value, outcome, reason in expected_length_cases:
        cases.append(_Case(f"EXPECTED_LENGTH_{label}", "expected_content_length_optional", _with(base, expected_content_length_bytes=value), outcome, reason))

    expected_sha_cases = (
        ("MISSING", _DESIGN_MISSING, "passed", "", "verified"),
        ("NONE", None, "invalid", AUTHORITY_TYPE_REASONS[1], _DESIGN_MISSING),
        ("BYTES", SHA_A.encode(), "invalid", AUTHORITY_TYPE_REASONS[1], _DESIGN_MISSING),
        ("STR_SUBCLASS", _StringSubclass(SHA_A), "invalid", AUTHORITY_TYPE_REASONS[1], _DESIGN_MISSING),
        ("UPPERCASE", SHA_A.upper(), "invalid", AUTHORITY_VALUE_REASONS[1], _DESIGN_MISSING),
        ("WRONG_LENGTH", SHA_A[:-1], "invalid", AUTHORITY_VALUE_REASONS[1], _DESIGN_MISSING),
        ("WRONG_CHARACTER", "g" + SHA_A[1:], "invalid", AUTHORITY_VALUE_REASONS[1], _DESIGN_MISSING),
        ("MATCH", SHA_A, "passed", "", _DESIGN_MISSING),
        ("MISMATCH", SHA_B, "blocked", BUSINESS_REASONS[3], _DESIGN_MISSING),
    )
    for label, value, outcome, reason, verdict in expected_sha_cases:
        cases.append(_Case(f"EXPECTED_SHA_{label}", "expected_sha256_optional", _with(base, expected_sha256=value, explicit_integrity_verdict=verdict), outcome, reason))

    verdict_cases = (
        ("MISSING", _DESIGN_MISSING, "passed", ""),
        ("NONE", None, "invalid", AUTHORITY_TYPE_REASONS[2]),
        ("BOOL", False, "invalid", AUTHORITY_TYPE_REASONS[2]),
        ("STR_SUBCLASS", _StringSubclass("verified"), "invalid", AUTHORITY_TYPE_REASONS[2]),
        ("EMPTY", "", "invalid", AUTHORITY_VALUE_REASONS[2]),
        ("UPPERCASE", "VERIFIED", "invalid", AUTHORITY_VALUE_REASONS[2]),
        ("UNKNOWN", "unknown", "invalid", AUTHORITY_VALUE_REASONS[2]),
        ("VERIFIED", "verified", "passed", ""),
        ("FAILED", "failed", "blocked", BUSINESS_REASONS[4]),
    )
    for label, value, outcome, reason in verdict_cases:
        cases.append(_Case(f"VERDICT_{label}", "explicit_integrity_verdict_optional", _with(base, explicit_integrity_verdict=value), outcome, reason))

    cases.extend((
        _Case("CROSS_EXACT4_TYPE_AUTHORITY_INVALID", "cross_phase_precedence", _with(base, download_result_status=None, expected_content_length_bytes=None), "invalid", DOWNLOAD_TYPE_REASONS[0]),
        _Case("CROSS_EXACT4_VALUE_AUTHORITY_INVALID", "cross_phase_precedence", _with(base, download_result_status="", expected_content_length_bytes=None), "invalid", DOWNLOAD_VALUE_REASONS[0]),
        _Case("CROSS_EXPECTED_LENGTH_INVALID_STATUS_FAILURE", "cross_phase_precedence", _with(base, download_result_status="failure", expected_content_length_bytes=None), "invalid", AUTHORITY_TYPE_REASONS[0]),
        _Case("CROSS_EXPECTED_SHA_INVALID_STATUS_FAILURE", "cross_phase_precedence", _with(base, download_result_status="failure", expected_sha256=None), "invalid", AUTHORITY_TYPE_REASONS[1]),
        _Case("CROSS_VERDICT_INVALID_STATUS_FAILURE", "cross_phase_precedence", _with(base, download_result_status="failure", explicit_integrity_verdict=None), "invalid", AUTHORITY_TYPE_REASONS[2]),
        _Case("CROSS_AUTHORITY_INVALID_HTTP", "cross_phase_precedence", _with(base, observed_http_status=500, expected_sha256=None), "invalid", AUTHORITY_TYPE_REASONS[1]),
        _Case("CROSS_AUTHORITY_INVALID_ZERO", "cross_phase_precedence", _with(base, observed_content_length_bytes=0, expected_sha256=None), "invalid", AUTHORITY_TYPE_REASONS[1]),
        _Case("CROSS_AUTHORITY_INVALID_SHA_MISMATCH", "cross_phase_precedence", _with(base, expected_sha256=SHA_B, explicit_integrity_verdict=None), "invalid", AUTHORITY_TYPE_REASONS[2]),
        _Case("CROSS_MULTIPLE_AUTHORITY_INVALID_FIRST", "cross_phase_precedence", _with(base, expected_content_length_bytes=None, expected_sha256=None, explicit_integrity_verdict=None), "invalid", AUTHORITY_TYPE_REASONS[0]),
        _Case("CROSS_MULTIPLE_AUTHORITY_INVALID_SECOND", "cross_phase_precedence", _with(base, expected_content_length_bytes=_DESIGN_MISSING, expected_sha256=None, explicit_integrity_verdict=None), "invalid", AUTHORITY_TYPE_REASONS[1]),
        _Case("CROSS_VALID_AUTHORITY_BEFORE_LATER_INVALID", "cross_phase_precedence", _with(base, expected_content_length_bytes=10, expected_sha256=SHA_A, explicit_integrity_verdict=None), "invalid", AUTHORITY_TYPE_REASONS[2]),
    ))
    return cases


def _decode_inherited(value: str, *, integer: bool = False) -> object:
    if value == "<MISSING>":
        return _DESIGN_MISSING
    return int(value) if integer else value


def _inherited_business_cases(snapshot: tuple[_Source, ...]) -> list[_Case]:
    rows = _source_rows(
        snapshot, "covapie_admit_013_download_outcome_and_integrity_truth_matrix.csv"
    )
    cases = []
    for row in rows:
        values = (
            row[DOWNLOAD_FIELDS[0]],
            int(row[DOWNLOAD_FIELDS[1]]),
            int(row[DOWNLOAD_FIELDS[2]]),
            row[DOWNLOAD_FIELDS[3]],
            _decode_inherited(row[AUTHORITY_FIELDS[0]], integer=True),
            _decode_inherited(row[AUTHORITY_FIELDS[1]]),
            _decode_inherited(row[AUTHORITY_FIELDS[2]]),
        )
        cases.append(_Case(
            f"BUSINESS23_{row['case_id']}", "inherited_exact7_business_projection", values,
            row["expected_outcome"], row["expected_reason"], row["case_id"],
        ))
    return cases


NEGATIVE_RESULT_CASES = (
    "WRONG_TOP_LEVEL_RESULT_TYPE", "RESULT_SUBCLASS", "STORAGE_NOT_EXACT_DATACLASS",
    "MISSING_FIELD", "EXTRA_FIELD", "FIELD_REORDER", "PASSED_INT_ONE",
    "BLOCKS_INT_ZERO", "CANONICAL_OUTER_LIST", "MALFORMED_PAIR", "PAIR_LIST",
    "PAIR_SUBCLASS", "TUPLE_SUBCLASS", "WRONG_PAIR_NAME", "WRONG_PAIR_ORDER",
    "DUPLICATE_PAIR", "EXTRA_PAIR", "CANONICAL_AUTHORITY_CONTAINS_MISSING_FIELD",
    "VALIDATED_TUPLE_LIST", "CONSUMED_TUPLE_LIST", "VALIDATED_NAME_NOT_EXACT_STR",
    "CONSUMED_NAME_NOT_EXACT_STR", "DESIGN_SENTINEL_LEAK", "EVALUATOR_IO_TRUE",
    "OUTCOME_REASON_INVARIANT_CONFLICT", "ADMISSION_RULE_ID_DRIFT",
)


class _ResultSubclass(Admit013EvaluationResultContractDesign):
    pass


@dataclass(frozen=True)
class _WrongOrderResult:
    outcome: object
    admission_rule_id: object


def _reject_negative_result(
    case_id: str, baseline: Admit013EvaluationResultContractDesign
) -> str:
    values = {name: getattr(baseline, name) for name in RESULT_FIELDS}
    download = baseline.canonical_download_result_record
    try:
        if case_id == "WRONG_TOP_LEVEL_RESULT_TYPE":
            validate_admit_013_evaluation_result_contract_design(object())
        elif case_id == "RESULT_SUBCLASS":
            _ResultSubclass(*(values[name] for name in RESULT_FIELDS))
        elif case_id in {"STORAGE_NOT_EXACT_DATACLASS", "MISSING_FIELD", "EXTRA_FIELD"}:
            mapping = dict(values)
            if case_id == "MISSING_FIELD":
                mapping.pop("reason")
            elif case_id == "EXTRA_FIELD":
                mapping["extra"] = True
            validate_admit_013_evaluation_result_contract_design(mapping)
        elif case_id == "FIELD_REORDER":
            validate_admit_013_evaluation_result_contract_design(_WrongOrderResult("passed", ADMISSION_RULE_ID))
        else:
            if case_id == "PASSED_INT_ONE":
                values["passed"] = 1
            elif case_id == "BLOCKS_INT_ZERO":
                values["blocks_candidate"] = 0
            elif case_id == "CANONICAL_OUTER_LIST":
                values["canonical_download_result_record"] = list(download)
            elif case_id == "MALFORMED_PAIR":
                values["canonical_download_result_record"] = ((DOWNLOAD_FIELDS[0],), *download[1:])
            elif case_id == "PAIR_LIST":
                values["canonical_download_result_record"] = (list(download[0]), *download[1:])
            elif case_id == "PAIR_SUBCLASS":
                values["canonical_download_result_record"] = (_PairTupleSubclass(download[0]), *download[1:])
            elif case_id == "TUPLE_SUBCLASS":
                values["canonical_download_result_record"] = _TupleSubclass(download)
            elif case_id == "WRONG_PAIR_NAME":
                values["canonical_download_result_record"] = (("wrong", download[0][1]), *download[1:])
            elif case_id == "WRONG_PAIR_ORDER":
                values["canonical_download_result_record"] = tuple(reversed(download))
            elif case_id == "DUPLICATE_PAIR":
                values["canonical_download_result_record"] = (download[0], download[0], *download[2:])
            elif case_id == "EXTRA_PAIR":
                values["canonical_download_result_record"] = (*download, ("extra", "value"))
            elif case_id == "CANONICAL_AUTHORITY_CONTAINS_MISSING_FIELD":
                values["canonical_integrity_authority_record"] = ((AUTHORITY_FIELDS[0], _DESIGN_MISSING),)
                values["validated_integrity_authority_fields"] = (AUTHORITY_FIELDS[0],)
            elif case_id == "VALIDATED_TUPLE_LIST":
                values["validated_download_result_fields"] = list(DOWNLOAD_FIELDS)
            elif case_id == "CONSUMED_TUPLE_LIST":
                values["consumed_download_result_fields"] = list(DOWNLOAD_FIELDS)
            elif case_id == "VALIDATED_NAME_NOT_EXACT_STR":
                values["validated_download_result_fields"] = (_StringSubclass(DOWNLOAD_FIELDS[0]), *DOWNLOAD_FIELDS[1:])
            elif case_id == "CONSUMED_NAME_NOT_EXACT_STR":
                values["consumed_integrity_authority_fields"] = (_StringSubclass(AUTHORITY_FIELDS[0]), *AUTHORITY_FIELDS[1:])
            elif case_id == "DESIGN_SENTINEL_LEAK":
                values["canonical_download_result_record"] = ((DOWNLOAD_FIELDS[0], _DESIGN_MISSING), *download[1:])
            elif case_id == "EVALUATOR_IO_TRUE":
                values["evaluator_io_used"] = True
            elif case_id == "OUTCOME_REASON_INVARIANT_CONFLICT":
                values.update(outcome="blocked", passed=False, blocks_candidate=True, reason="")
            elif case_id == "ADMISSION_RULE_ID_DRIFT":
                values["admission_rule_id"] = "ADMIT_012"
            Admit013EvaluationResultContractDesign(*(values[name] for name in RESULT_FIELDS))
    except (TypeError, ValueError) as error:
        return f"RESULT_CONTRACT_REJECTED:{type(error).__name__}"
    raise ValueError(f"negative result case accepted: {case_id}")


def _expected_result(case: _Case) -> Admit013EvaluationResultContractDesign:
    values = case.values
    if case.reason in MISSING_REASONS:
        index = MISSING_REASONS.index(case.reason)
        return _make_result("blocked", case.reason, (), (), DOWNLOAD_FIELDS[:index], (), DOWNLOAD_FIELDS[:index + 1], ())
    if case.reason in DOWNLOAD_TYPE_REASONS or case.reason in DOWNLOAD_VALUE_REASONS:
        reasons = DOWNLOAD_TYPE_REASONS if case.reason in DOWNLOAD_TYPE_REASONS else DOWNLOAD_VALUE_REASONS
        index = reasons.index(case.reason)
        return _make_result("invalid", case.reason, (), (), DOWNLOAD_FIELDS[:index], (), DOWNLOAD_FIELDS, ())
    download = tuple((name, value) for name, value in zip(DOWNLOAD_FIELDS, values[:4], strict=True))
    if case.reason in AUTHORITY_TYPE_REASONS or case.reason in AUTHORITY_VALUE_REASONS:
        reasons = AUTHORITY_TYPE_REASONS if case.reason in AUTHORITY_TYPE_REASONS else AUTHORITY_VALUE_REASONS
        index = reasons.index(case.reason)
        authority = tuple(
            (AUTHORITY_FIELDS[position], values[4 + position])
            for position in range(index)
            if values[4 + position] is not _DESIGN_MISSING
        )
        return _make_result(
            "invalid", case.reason, download, authority, DOWNLOAD_FIELDS,
            tuple(pair[0] for pair in authority), DOWNLOAD_FIELDS, AUTHORITY_FIELDS[:index + 1],
        )
    authority = tuple(
        (name, value)
        for name, value in zip(AUTHORITY_FIELDS, values[4:], strict=True)
        if value is not _DESIGN_MISSING
    )
    return _make_result(
        case.outcome, case.reason, download, authority, DOWNLOAD_FIELDS,
        tuple(pair[0] for pair in authority), DOWNLOAD_FIELDS, AUTHORITY_FIELDS,
    )


def _representation(value: object) -> str:
    if value is _DESIGN_MISSING:
        return "<MISSING>"
    if type(value) is _StringSubclass:
        return f"<str-subclass:{str(value)!r}>"
    if type(value) is _IntSubclass:
        return f"<int-subclass:{int(value)}>"
    if type(value) is bytes:
        return f"<bytes:{value.decode(errors='backslashreplace')!r}>"
    if type(value) is object:
        return "<object>"
    return repr(value)


def _result_values(result: Admit013EvaluationResultContractDesign) -> tuple[object, ...]:
    return tuple(getattr(result, name) for name in RESULT_FIELDS)


def _truth_rows(snapshot: tuple[_Source, ...]) -> list[dict[str, str]]:
    cases = [*_interface_cases(), *_inherited_business_cases(snapshot)]
    baseline = _expected_result(_Case("BASE", "base", _base_values(), "passed", ""))
    cases.extend(
        _Case(case_id, "result_invariant_negative", _base_values(), "passed", "", negative_result_case=case_id)
        for case_id in NEGATIVE_RESULT_CASES
    )
    rows = []
    for order, case in enumerate(cases, 1):
        expected = _expected_result(case)
        if case.negative_result_case:
            observed = _reject_negative_result(case.negative_result_case, baseline)
            passed = observed.startswith("RESULT_CONTRACT_REJECTED:")
            assertion_kind = "result_contract_rejection"
        else:
            kwargs = dict(zip(PARAMETERS, case.values, strict=True))
            observed_result = classify_admit_013_formal_evaluator_interface_design(**kwargs)
            observed = repr(_result_values(observed_result))
            passed = observed_result == expected
            assertion_kind = "formal_interface_projection"
        rows.append({
            "case_order": str(order), "case_id": case.case_id, "case_group": case.group,
            "assertion_kind": assertion_kind, "inherited_case_id": case.inherited_case_id,
            **{
                f"{name}_representation": _representation(value)
                for name, value in zip(PARAMETERS, case.values, strict=True)
            },
            "expected_outcome": expected.outcome, "expected_reason": expected.reason,
            "expected_canonical_download_result_record": repr(expected.canonical_download_result_record),
            "expected_canonical_integrity_authority_record": repr(expected.canonical_integrity_authority_record),
            "expected_validated_download_result_fields": repr(expected.validated_download_result_fields),
            "expected_validated_integrity_authority_fields": repr(expected.validated_integrity_authority_fields),
            "expected_consumed_download_result_fields": repr(expected.consumed_download_result_fields),
            "expected_consumed_integrity_authority_fields": repr(expected.consumed_integrity_authority_fields),
            "expected_passed": str(expected.passed).lower(),
            "expected_blocks_candidate": str(expected.blocks_candidate).lower(),
            "expected_evaluator_io_used": "false", "observed_design_result": observed,
            "case_passed": str(passed).lower(),
        })
    if not all(row["case_passed"] == "true" for row in rows):
        raise ValueError("Design truth mismatch")
    if any("DesignMissing" in "|".join(row.values()) or "0x" in row["observed_design_result"] for row in rows):
        raise ValueError("Design sentinel representation leaked")
    return rows


ISSUE_TRANSITIONS = {
    "ADMIT_013_STANDALONE_SIGNATURE_UNRESOLVED": (
        "exact seven-keyword-only signature with private missing singleton defaults"
    ),
    "ADMIT_013_RESULT_CONTRACT_UNRESOLVED": (
        "Exact12 result contract, Exact5 validation precedence, and exact representation invariants"
    ),
}
ISSUE_TRANSITION_ACTION = "resolved_by_successor_formal_interface_contract_design"


def _issue_rows(snapshot: tuple[_Source, ...]) -> list[dict[str, str]]:
    inherited = _source_rows(
        snapshot,
        "covapie_bulk_download_admission_admit_013_download_outcome_and_integrity_contract_v1/covapie_admit_013_issue_readiness_inventory.csv",
    )
    rows = []
    for row in inherited:
        evidence = ISSUE_TRANSITIONS.get(row["issue_id"])
        rows.append({
            "inherited_order": row["inherited_order"],
            **{
                name: row[name]
                for name in (
                    "issue_id", "issue_type", "affected_fields", "affected_rules",
                    "severity", "status", "blocking_scope", "blocking_reason",
                    "issue_origin", "integration_transition", "issue_count",
                )
            },
            "inherited_effective_status": row["effective_status"],
            "inherited_transition_stage": row["transition_stage"],
            "inherited_transition_action": row["transition_action"],
            "inherited_transition_evidence": row["transition_evidence"],
            "successor_effective_status": "resolved" if evidence else row["effective_status"],
            "successor_transition_stage": STAGE if evidence else "",
            "successor_transition_action": ISSUE_TRANSITION_ACTION if evidence else "unchanged",
            "successor_transition_evidence": evidence or "inherited effective state retained",
        })
    by_id = {row["issue_id"]: row for row in rows}
    if len(rows) != 23 or [row["inherited_order"] for row in rows] != [str(index) for index in range(1, 24)]:
        raise ValueError("Exact23 issue identity/order drift")
    if any(by_id[issue]["successor_effective_status"] != "resolved" for issue in ISSUE_TRANSITIONS):
        raise ValueError("Exact2 interface issue transition failed")
    if by_id["UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE"]["affected_rules"] != "ADMIT_013|ADMIT_014|ADMIT_015":
        raise ValueError("unified coverage affected-rules drift")
    for issue in (
        "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
        "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
    ):
        if by_id[issue]["successor_effective_status"] != "open":
            raise ValueError("required open issue was closed")
    return rows


def _source_rows_for_artifact(snapshot: tuple[_Source, ...]) -> list[dict[str, str]]:
    return [{
        "source_order": str(index),
        "source_relative_path": record.path.as_posix(),
        "source_kind": (
            "python_source" if record.path.suffix == ".py"
            else "committed_csv" if record.path.suffix == ".csv"
            else "committed_manifest" if record.path.suffix == ".json"
            else "tracked_text"
        ),
        "expected_sha256": record.sha256,
        "observed_sha256": record.sha256,
        "base_blob_sha256": record.sha256,
        "base_tree_mode": record.base_mode,
        "git_tracked": "true", "filesystem_regular": "true", "non_symlink": "true",
        "parent_chain_non_symlink": "true", "pinned_fd_no_follow_read": "true",
        "raw_checkpoint_excluded": "true", "audit_result": "passed",
    } for index, record in enumerate(snapshot, 1)]


TRUE_READINESS = (
    "admit_013_preconditions_audited",
    "admit_013_download_outcome_and_integrity_contract_designed",
    "admit_013_standalone_signature_frozen",
    "admit_013_formal_result_contract_frozen",
    "admit_013_formal_evaluator_interface_contract_frozen",
    "admit_013_validation_precedence_resolved",
    "admit_013_future_evaluator_pure_in_memory_possible",
    "ready_for_admit_013_standalone_evaluator_interface_implementation",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "evaluate_admit_013_implemented",
    "Admit013EvaluationResult_implemented",
    "admit_013_rule_logic_implemented",
    "admit_013_unified_adapter_contract_frozen",
    "admit_013_unified_adapter_implemented",
    "admit_013_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_013_implemented",
    "provider_mapping_validated",
    "real_provider_evaluation_ready",
    "ready_for_bulk_download_now",
    "combined_candidate_verdict_implemented",
    "cross_rule_aggregation_implemented",
    "ready_for_training",
    "step12d_is_final_training_feature_contract",
)


def _readiness() -> dict[str, bool]:
    return {**{name: True for name in TRUE_READINESS}, **{name: False for name in FALSE_READINESS}}


def _csv_bytes(columns: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=columns, lineterminator="\n", extrasaction="raise"
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def build_artifacts(snapshot: tuple[_Source, ...] | None = None) -> dict[str, bytes]:
    frozen = build_frozen_source_snapshot() if snapshot is None else snapshot
    _validate_predecessors(frozen)
    contract_rows = _contract_rows()
    routing_rows = _routing_rows()
    truth_rows = _truth_rows(frozen)
    source_rows = _source_rows_for_artifact(frozen)
    issue_rows = _issue_rows(frozen)
    payloads = {
        CONTRACT_FILE: _csv_bytes(CONTRACT_COLUMNS, contract_rows),
        ROUTING_FILE: _csv_bytes(ROUTING_COLUMNS, routing_rows),
        TRUTH_FILE: _csv_bytes(TRUTH_COLUMNS, truth_rows),
        SOURCE_FILE: _csv_bytes(SOURCE_COLUMNS, source_rows),
        ISSUE_FILE: _csv_bytes(ISSUE_COLUMNS, issue_rows),
    }
    group_counts = {
        group: sum(row["case_group"] == group for row in truth_rows)
        for group in sorted({row["case_group"] for row in truth_rows})
    }
    output_sha256 = {
        name: hashlib.sha256(content).hexdigest() for name, content in payloads.items()
    }
    readiness = _readiness()
    manifest: dict[str, Any] = {
        "manifest_schema_version": "covapie_admit_013_formal_evaluator_interface_contract_manifest_v1",
        "project": PROJECT,
        "stage": STAGE,
        "base_commit": BASE_COMMIT,
        "base_parent": BASE_PARENT,
        "base_subject": BASE_SUBJECT,
        "admission_rule_id": ADMISSION_RULE_ID,
        "admission_rule_name": "download_failure_fail_closed",
        "evidence_source": "future_download_result",
        "required_status": "non_success_or_integrity_failure_not_admitted",
        "failure_severity": "blocking",
        "blocking_reason": "download_failure_must_fail_closed",
        "evaluation_phase": "post_download",
        "future_function_name": "evaluate_admit_013",
        "future_result_type_name": "Admit013EvaluationResult",
        "future_public_signature": FUTURE_PUBLIC_SIGNATURE,
        "signature_parameters": list(PARAMETERS),
        "signature_parameter_count": 7,
        "signature_all_keyword_only": True,
        "signature_varargs": False,
        "signature_varkw": False,
        "signature_dynamic_mapping_or_policy_context": False,
        "signature_private_missing_singleton_defaults": True,
        "download_result_fields": list(DOWNLOAD_FIELDS),
        "integrity_authority_fields": list(AUTHORITY_FIELDS),
        "authority_fields_optional": True,
        "outcome_vocabulary": list(OUTCOMES),
        "reason_vocabulary": list(REASON_VOCABULARY),
        "reason_vocabulary_count_including_empty": 26,
        "validation_phase_order": list(VALIDATION_PHASES),
        "business_failure_precedence": list(BUSINESS_REASONS),
        "result_fields": list(RESULT_FIELDS),
        "result_field_count": 12,
        "result_field_exact_types": [
            "str", "str", "bool", "bool", "str", "tuple", "tuple", "tuple",
            "tuple", "tuple", "tuple", "bool",
        ],
        "result_invariants": [
            "passed == (outcome == passed)",
            "blocks_candidate == (outcome != passed)",
            "reason empty iff outcome passed",
            "evaluator_io_used is exact false",
        ],
        "canonical_download_result_representation": "exact ordered tuple of Exact4 exact two-item pair tuples; original exact value types",
        "canonical_integrity_authority_representation": "exact ordered subset tuple of present-valid Exact3 exact two-item pair tuples; missing omitted",
        "validated_semantics": "Exact4 ordered successful prefix; Exact3 ordered present-valid names only",
        "consumed_semantics": "actual ordered lookups; missing Exact4 includes failure name; authority phase includes missing optional names",
        "routing_contract": {
            "download_result_context": list(DOWNLOAD_FIELDS),
            "evaluation_context": list(AUTHORITY_FIELDS),
            "forbidden_envelopes": [
                "candidate_record", "batch_context", "stage_authorization_context",
                "fallback_envelope", "filesystem", "network", "raw",
                "provider_or_download_execution_inside_evaluator",
            ],
            "scalar_keyword_consumption_only": True,
            "Admit012EvaluationResult_consumed": False,
        },
        "formal_evaluator_implemented": False,
        "formal_result_type_defined": False,
        "unified_adapter_or_registry_or_exact13_runtime_changed": False,
        "design_oracle": "classify_admit_013_formal_evaluator_interface_design",
        "design_result_type": "Admit013EvaluationResultContractDesign",
        "source_count": len(frozen),
        "source_path_list_sha256": SOURCE_PATH_LIST_SHA256,
        "source_path_sha256_pairs_sha256": SOURCE_PATH_SHA256_PAIRS_SHA256,
        "source_boundary": [
            {"path": record.path.as_posix(), "sha256": record.sha256, "base_tree_mode": record.base_mode}
            for record in frozen
        ],
        "output_file_count": 6,
        "output_files": list(OUTPUT_FILES),
        "output_sha256": output_sha256,
        "row_counts": {
            "interface_result_contract": len(contract_rows),
            "routing_consumption": len(routing_rows),
            "truth_matrix": len(truth_rows),
            "inherited_business_projection": 23,
            "result_negative": len(NEGATIVE_RESULT_CASES),
            "source_boundary": len(source_rows),
            "issue_inventory": len(issue_rows),
        },
        "truth_matrix_group_counts": group_counts,
        "issue_transition_count": 2,
        "issue_transition_ids": list(ISSUE_TRANSITIONS),
        "issue_transition_action": ISSUE_TRANSITION_ACTION,
        "remaining_open_issue_ids": [
            "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
            "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
            "UNIFIED_ADMISSION_RULE_COVERAGE_INCOMPLETE",
            "UNIFIED_ADMISSION_CROSS_RULE_AGGREGATION_SEMANTICS_UNRESOLVED",
        ],
        "readiness": readiness,
        "safety": {
            "provider": False,
            "network": False,
            "download": False,
            "raw": False,
            "model_or_checkpoint": False,
            "dataloader": False,
            "runtime_change": False,
            "training": False,
            "stage_commit_push": False,
        },
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
        "step12d_status": "smoke_legality_only_not_final_training_feature_contract",
        "feature_semantics_audit_requirement": "required_before_training; historical UNKNOWN_ATOM_FEATURE_POLICY and feature_semantics_known=False require audit",
        "rename_policy": "RENAME_NOREPLACE_required; GPFS_EINVAL_fails_closed; no_os.replace_fallback",
        "all_checks_passed": True,
    }
    payloads[MANIFEST_FILE] = (
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    ).encode()
    return {name: payloads[name] for name in OUTPUT_FILES}


def _rename_noreplace(source: Path, destination: Path) -> None:
    if os.uname().machine not in {"x86_64", "amd64"}:
        raise ValueError("renameat2 syscall number unavailable")
    result = ctypes.CDLL(None, use_errno=True).syscall(
        316, -100, os.fsencode(source), -100, os.fsencode(destination), 1
    )
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), destination)


def _write_leaf(path: Path, data: bytes) -> None:
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
        0o644,
    )
    try:
        view = memoryview(data)
        while view:
            view = view[os.write(descriptor, view):]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _read_output_at(
    root_fd: int, name: str, expected_identity: tuple[int, int, int]
) -> bytes:
    if _identity(os.lstat(name, dir_fd=root_fd)) != expected_identity:
        raise ValueError("output leaf identity drift before open")
    descriptor = os.open(
        name,
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
        dir_fd=root_fd,
    )
    try:
        if _identity(os.fstat(descriptor)) != expected_identity:
            raise ValueError("output leaf stat/open race")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        if _identity(os.fstat(descriptor)) != expected_identity:
            raise ValueError("output leaf FD identity drift")
        if _identity(os.lstat(name, dir_fd=root_fd)) != expected_identity:
            raise ValueError("output leaf lexical identity drift")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _read_exact_output_set(root: Path, payloads: dict[str, bytes]) -> bool:
    parent_identity = _identity(os.lstat(root.parent))
    root_item = os.lstat(root)
    root_identity = _identity(root_item)
    if (
        stat.S_ISLNK(root_item.st_mode)
        or not stat.S_ISDIR(root_item.st_mode)
        or root.resolve(strict=True) != root
    ):
        raise ValueError("unsafe output root")
    root_fd = os.open(
        root,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        if _identity(os.fstat(root_fd)) != root_identity:
            raise ValueError("output root stat/open race")
        if set(os.listdir(root_fd)) != set(OUTPUT_FILES):
            return False
        leaf_identities = {}
        for name in OUTPUT_FILES:
            item = os.lstat(name, dir_fd=root_fd)
            if stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode):
                raise ValueError("unsafe output leaf")
            leaf_identities[name] = _identity(item)
        matches = all(
            _read_output_at(root_fd, name, leaf_identities[name]) == payloads[name]
            for name in OUTPUT_FILES
        )
        if _identity(os.lstat(root.parent)) != parent_identity:
            raise ValueError("output parent identity drift")
        if _identity(os.fstat(root_fd)) != root_identity or _identity(os.lstat(root)) != root_identity:
            raise ValueError("output root identity drift")
        if set(os.listdir(root_fd)) != set(OUTPUT_FILES):
            raise ValueError("output inventory drift")
        if any(
            _identity(os.lstat(name, dir_fd=root_fd)) != leaf_identities[name]
            for name in OUTPUT_FILES
        ):
            raise ValueError("output leaf identity drift after traversal")
        return matches
    finally:
        os.close(root_fd)


def _cleanup_owned_staging(staging: Path) -> None:
    if not staging.exists() or staging.is_symlink() or not staging.is_dir():
        return
    entries = {entry.name: entry for entry in staging.iterdir()}
    if set(entries) - set(OUTPUT_FILES):
        return
    for entry in entries.values():
        item = os.lstat(entry)
        if stat.S_ISREG(item.st_mode) and not stat.S_ISLNK(item.st_mode):
            entry.unlink()
    try:
        staging.rmdir()
    except OSError:
        pass


def materialize_contract(output_root: Path | None = None) -> dict[str, Any]:
    root = REPO_ROOT / DEFAULT_OUTPUT_ROOT if output_root is None else Path(output_root)
    parent = root.parent
    parent_item = os.lstat(parent)
    if (
        stat.S_ISLNK(parent_item.st_mode)
        or not stat.S_ISDIR(parent_item.st_mode)
        or parent.resolve(strict=True) != parent
    ):
        raise ValueError("unsafe output parent")
    payloads = build_artifacts()
    if root.exists() or root.is_symlink():
        if _read_exact_output_set(root, payloads):
            return json.loads(payloads[MANIFEST_FILE])
        raise ValueError("existing output set mismatch")
    staging = Path(
        tempfile.mkdtemp(prefix=f".{root.name}.", suffix=".staging", dir=parent)
    )
    try:
        for name in OUTPUT_FILES:
            _write_leaf(staging / name, payloads[name])
        _fsync_directory(staging)
        _rename_noreplace(staging, root)
        _fsync_directory(parent)
        if not _read_exact_output_set(root, payloads):
            raise ValueError("published output postverify failed")
    except BaseException:
        _cleanup_owned_staging(staging)
        raise
    return json.loads(payloads[MANIFEST_FILE])


def run_covapie_bulk_download_admission_admit_013_formal_evaluator_interface_contract_v1(
    output_root: Path | None = None,
) -> dict[str, Any]:
    """Explicitly materialize the deterministic Exact6 Design evidence set."""
    return materialize_contract(output_root)
