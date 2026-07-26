"""Hermetic in-memory integration smoke for stage admission orchestration.

The public smoke uses the committed orchestrator, Exact15 dispatcher,
standalone evaluator adapters, and combined aggregator without replacing any
callable or registry.  Fixture construction and all runtime work are pure in
memory.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from types import MappingProxyType

from covalent_ext import (
    covapie_bulk_download_admission_admit_004_rule_logic_interface as admit004,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_006_rule_logic_interface as admit006,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_008_rule_logic_interface as admit008,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_010_rule_logic_interface as admit010,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate
    as admit011_contract,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_011_rule_logic_interface as admit011,
)
from covalent_ext import (
    covapie_bulk_download_admission_admit_012_rule_logic_interface as admit012,
)
from covalent_ext import (
    covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_v1
    as aggregation_runtime,
)
from covalent_ext import (
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015
    as dispatch_runtime,
)
from covalent_ext import (
    covapie_stage_global_rule_evaluation_orchestration_contract_design_gate
    as contract,
)
from covalent_ext import (
    covapie_stage_global_rule_evaluation_orchestration_v1
    as orchestration_runtime,
)


BASE_COMMIT = "92aaa56a590e063b8fb0defda54444dc3bd1e6f8"
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE stage-global orchestration in-memory integration smoke v1"
)
FIXTURE_PROFILE_SINGLE = "canonical_single_candidate_exact4"
FIXTURE_PROFILE_TWO = "canonical_two_candidate_training_scope"
FIXTURE_PROFILE_IDS = (FIXTURE_PROFILE_SINGLE, FIXTURE_PROFILE_TWO)
CANONICAL_MASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
EFFECTIVE_OPEN_ISSUES = (
    "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
    "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
)
RECOMMENDED_NEXT_STEP = (
    "design_covapie_bulk_download_stage_orchestration_"
    "fail_closed_call_site_contract_v1"
)

UNIFIED_PARITY_FIELDS = dispatch_runtime.RESULT_FIELDS
COMBINED_PARITY_FIELDS = aggregation_runtime.RESULT_FIELDS
_CANDIDATE_CONTEXT_ROUTING = MappingProxyType(
    {
        "ADMIT_001": (True, False, False),
        "ADMIT_002": (False, False, False),
        "ADMIT_003": (False, False, False),
        "ADMIT_004": (False, True, False),
        "ADMIT_005": (False, False, False),
        "ADMIT_006": (False, True, False),
        "ADMIT_007": (False, True, False),
        "ADMIT_008": (False, True, False),
        "ADMIT_009": (True, True, False),
        "ADMIT_010": (False, True, False),
        "ADMIT_011": (False, True, False),
        "ADMIT_012": (False, True, True),
        "ADMIT_013": (False, True, True),
    }
)


@dataclass(frozen=True)
class CanonicalInMemoryFixtureProfile:
    fixture_profile: str
    scopes: tuple[str, ...]
    candidate_inputs: tuple[
        contract.AdmissionCandidateOrchestrationInput, ...
    ]
    batch_context: Mapping[str, object]
    stage_authorization_context: Mapping[str, object]


@dataclass(frozen=True)
class InMemoryIntegrationCandidateObservation:
    candidate_index: int
    ordered_rule_ids: tuple[str, ...]
    ordered_outcomes: tuple[str, ...]
    ordered_reasons: tuple[str, ...]
    ordered_passed: tuple[bool, ...]
    ordered_blocks_candidate: tuple[bool, ...]
    combined_outcome: str
    combined_reason: str
    dispatcher_call_count: int
    aggregator_call_count: int


@dataclass(frozen=True)
class InMemoryIntegrationScopeObservation:
    fixture_profile: str
    scope_id: str
    candidate_count: int
    stage_global_rule_ids: tuple[str, ...]
    stage_global_outcomes: tuple[str, ...]
    stage_global_reasons: tuple[str, ...]
    candidate_observations: tuple[
        InMemoryIntegrationCandidateObservation, ...
    ]
    dispatcher_call_count: int
    aggregator_call_count: int
    orchestration_io_used: bool
    action_permission_granted: bool


@dataclass(frozen=True)
class InMemoryIntegrationSmokeReport:
    observations: tuple[InMemoryIntegrationScopeObservation, ...]
    direct_dispatch_parity_verified: bool
    direct_aggregation_parity_verified: bool
    committed_runtime_identity_unchanged: bool
    stage_global_identity_reuse_verified: bool
    normal_retained_vector_identity_verified: bool
    network_used: bool
    provider_used: bool
    download_used: bool
    training_used: bool
    ready_for_training: bool


def _runtime_identity_snapshot() -> tuple[object, ...]:
    return (
        dispatch_runtime.evaluate_admission_rule,
        dispatch_runtime.EVALUATOR_REGISTRY,
        tuple(
            (rule_id, handler)
            for rule_id, handler in dispatch_runtime.EVALUATOR_REGISTRY.items()
        ),
        aggregation_runtime.aggregate_admission_rule_evaluations,
        orchestration_runtime.orchestrate_stage_admission_scope,
    )


_COMMITTED_RUNTIME_IDENTITIES = _runtime_identity_snapshot()


def _assert_identity_snapshot(
    left: tuple[object, ...], right: tuple[object, ...]
) -> None:
    if left[0] is not right[0] or left[1] is not right[1]:
        raise RuntimeError("committed dispatcher or registry identity changed")
    left_registry = left[2]
    right_registry = right[2]
    if (
        type(left_registry) is not tuple
        or type(right_registry) is not tuple
        or len(left_registry) != len(right_registry)
    ):
        raise RuntimeError("committed registry identity vector malformed")
    for left_item, right_item in zip(
        left_registry, right_registry, strict=True
    ):
        if (
            type(left_item) is not tuple
            or type(right_item) is not tuple
            or left_item[0] != right_item[0]
            or left_item[1] is not right_item[1]
        ):
            raise RuntimeError("committed handler registry identity changed")
    if left[3] is not right[3] or left[4] is not right[4]:
        raise RuntimeError("committed aggregator or orchestrator identity changed")


def _candidate_record(candidate_index: int) -> dict[str, object]:
    number = candidate_index + 1
    return {
        "candidate_record_id": f"REC_{number}",
        "pdb_id": f"{number}abc",
        "ligand_comp_id": f"L{number}",
        "covalent_residue_name": "CYS",
        "covalent_residue_chain_id": chr(65 + candidate_index),
        "covalent_residue_index": str(42 + candidate_index),
        "covalent_residue_atom_name": "SG",
        "covalent_residue_locator_namespace": "auth",
        "covalent_residue_insertion_code_state": "absent",
        "covalent_residue_insertion_code": "",
        "covalent_residue_locator_provenance_source_id": (
            f"covapie:synthetic:{number}"
        ),
        "covalent_residue_locator_provenance_sha256": str(number) * 64,
        "covalent_event_evidence_source": (
            admit006.CANONICAL_ENUM_MEMBERS[0]
        ),
        "topology_restoration_disposition": (
            admit008.CANONICAL_ENUM_MEMBERS[0]
        ),
        "duplicate_identity_key": (
            "covapie_dup_v1_sha256_" + str(number) * 64
        ),
        "leakage_group_id": f"COVAPIE_LEAKAGE_GROUP_{number:06d}",
        "raw_target_relative_path": (
            f"data/raw/covapie_candidate_{number}.cif"
        ),
    }


def _evaluation_context(
    candidate_record: Mapping[str, object], candidate_index: int
) -> dict[str, object]:
    number = candidate_index + 1
    leakage_group_id = candidate_record["leakage_group_id"]
    if type(leakage_group_id) is not str:
        raise TypeError("canonical leakage group fixture type drift")
    sample = f"SAMPLE_{number:06d}"
    return {
        admit004.EVIDENCE_CONTEXT_KEY: {
            "schema_version": admit004.EVIDENCE_CONTEXT_SCHEMA_VERSION,
            "attested_candidate_fields": {
                name: candidate_record[name]
                for name in admit004.CANDIDATE_FIELDS
            },
            "provider_evidence_outcome": "passed",
            "provider_evidence_reason": "",
            "four_way_present_value_exact_equality_attested": True,
            "present_value_quote_class_roundtrip_verified": True,
        },
        "allowed_covalent_evidence_classes": (
            admit006.ALLOWED_COVALENT_EVIDENCE_CLASSES
        ),
        "allowed_topology_restoration_dispositions": (
            admit008.ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS
        ),
        "duplicate_identity_key_contract": (
            "covapie_duplicate_identity_key_contract_v1"
        ),
        "leakage_group_assignment_provenance_contract": (
            admit010._valid_contract(
                candidate=leakage_group_id,
                sample=sample,
                members=(sample,),
            )
        ),
        "raw_target_relative_path_contract": admit011_contract.DEFAULT_CONTRACT,
        "existing_raw_target_relative_paths": admit011._empty_snapshot(),
        "allowed_download_result_statuses": (
            admit012.FORMAL_CONTEXT_VALUES[0]
        ),
        "successful_http_status_contract": (
            admit012.FORMAL_CONTEXT_VALUES[1]
        ),
        "content_length_contract": admit012.FORMAL_CONTEXT_VALUES[2],
        "sha256_format_contract": admit012.FORMAL_CONTEXT_VALUES[3],
        "expected_content_length_bytes": 7,
        "expected_sha256": "abcdef0123456789" * 4,
        "explicit_integrity_verdict": "verified",
    }


def _download_result_context() -> dict[str, object]:
    return {
        "download_result_status": "success",
        "observed_http_status": 200,
        "observed_content_length_bytes": 7,
        "observed_sha256": "abcdef0123456789" * 4,
    }


def _candidate_input(
    candidate_index: int,
) -> contract.AdmissionCandidateOrchestrationInput:
    candidate_record = _candidate_record(candidate_index)
    return contract.AdmissionCandidateOrchestrationInput(
        candidate_record=candidate_record,
        evaluation_context=_evaluation_context(
            candidate_record, candidate_index
        ),
        download_result_context=_download_result_context(),
    )


def build_canonical_in_memory_fixture_profiles(
) -> tuple[CanonicalInMemoryFixtureProfile, ...]:
    """Build both fixed profiles with no filesystem or external access."""
    single_inputs = (_candidate_input(0),)
    two_inputs = (_candidate_input(0), _candidate_input(1))

    def batch(
        inputs: tuple[contract.AdmissionCandidateOrchestrationInput, ...],
    ) -> dict[str, object]:
        return {
            "batch_candidate_record_ids": tuple(
                item.candidate_record["candidate_record_id"]
                for item in inputs
            ),
            "batch_duplicate_identity_keys": (),
        }

    def authorization() -> dict[str, object]:
        return {
            "current_stage_download_authorized": False,
            "current_stage_training_authorized": False,
        }

    return (
        CanonicalInMemoryFixtureProfile(
            fixture_profile=FIXTURE_PROFILE_SINGLE,
            scopes=contract.SCOPE_IDS,
            candidate_inputs=single_inputs,
            batch_context=batch(single_inputs),
            stage_authorization_context=authorization(),
        ),
        CanonicalInMemoryFixtureProfile(
            fixture_profile=FIXTURE_PROFILE_TWO,
            scopes=("training_execution_admission_permission",),
            candidate_inputs=two_inputs,
            batch_context=batch(two_inputs),
            stage_authorization_context=authorization(),
        ),
    )


def _routed_contexts(
    rule_id: str,
    candidate_input: contract.AdmissionCandidateOrchestrationInput,
    batch_context: Mapping[str, object],
) -> tuple[
    Mapping[str, object] | None,
    Mapping[str, object] | None,
    Mapping[str, object] | None,
]:
    use_batch, use_evaluation, use_download = _CANDIDATE_CONTEXT_ROUTING[
        rule_id
    ]
    return (
        batch_context if use_batch else None,
        candidate_input.evaluation_context if use_evaluation else None,
        candidate_input.download_result_context if use_download else None,
    )


def _validate_stage_global_identity_reuse(
    required_rule_ids: tuple[str, ...],
    stage_global_results: tuple[object, ...],
    candidate_vectors: tuple[tuple[object, ...], ...],
) -> None:
    """Require each vector to reuse every stage-global result by identity."""
    for stage_index, stage_result in enumerate(stage_global_results):
        rule_id = stage_result.admission_rule_id
        try:
            vector_index = required_rule_ids.index(rule_id)
        except ValueError as exc:
            raise RuntimeError(
                "stage-global identity rule membership invalid"
            ) from exc
        for candidate_vector in candidate_vectors:
            if candidate_vector[vector_index] is not stage_result:
                raise RuntimeError(
                    "stage-global result identity reuse failed"
                )


def _validate_normal_retained_vector_identity(
    candidate_vectors: tuple[tuple[object, ...], ...],
    combined_verdicts: tuple[object, ...],
) -> None:
    """Require normal aggregator branches to retain their input tuple."""
    if len(candidate_vectors) != len(combined_verdicts):
        raise RuntimeError("retained-vector identity cardinality invalid")
    for candidate_vector, combined_verdict in zip(
        candidate_vectors, combined_verdicts, strict=True
    ):
        normal_branch = all(
            child.outcome
            in aggregation_runtime.AGGREGATION_ADMISSIBLE_CHILD_OUTCOMES
            for child in candidate_vector
        )
        if (
            normal_branch
            and combined_verdict.rule_evaluations is not candidate_vector
        ):
            raise RuntimeError(
                "normal combined verdict retained-vector identity failed"
            )


def _direct_baseline(
    fixture: CanonicalInMemoryFixtureProfile, scope_id: str
) -> tuple[
    tuple[object, ...],
    tuple[tuple[object, ...], ...],
    tuple[object, ...],
]:
    stage_results = tuple(
        dispatch_runtime.evaluate_admission_rule(
            rule_id,
            contract.STAGE_GLOBAL_CANDIDATE_SENTINEL,
            batch_context=None,
            evaluation_context=None,
            download_result_context=None,
            stage_authorization_context=fixture.stage_authorization_context,
        )
        for rule_id in contract.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope_id]
    )
    stage_by_rule = {
        value.admission_rule_id: value for value in stage_results
    }
    vectors: list[tuple[object, ...]] = []
    verdicts: list[object] = []
    for candidate_input in fixture.candidate_inputs:
        candidate_by_rule: dict[str, object] = {}
        for rule_id in contract.CANDIDATE_RULE_IDS_BY_SCOPE[scope_id]:
            batch, evaluation, download = _routed_contexts(
                rule_id, candidate_input, fixture.batch_context
            )
            candidate_by_rule[rule_id] = (
                dispatch_runtime.evaluate_admission_rule(
                    rule_id,
                    candidate_input.candidate_record,
                    batch_context=batch,
                    evaluation_context=evaluation,
                    download_result_context=download,
                    stage_authorization_context=None,
                )
            )
        vector = tuple(
            (
                stage_by_rule[rule_id]
                if rule_id in stage_by_rule
                else candidate_by_rule[rule_id]
            )
            for rule_id in contract.REQUIRED_RULE_IDS[scope_id]
        )
        vectors.append(vector)
        verdicts.append(
            aggregation_runtime.aggregate_admission_rule_evaluations(
                scope_id,
                ordered_rule_evaluations=vector,
            )
        )
    direct_vectors = tuple(vectors)
    direct_verdicts = tuple(verdicts)
    _validate_stage_global_identity_reuse(
        contract.REQUIRED_RULE_IDS[scope_id],
        stage_results,
        direct_vectors,
    )
    _validate_normal_retained_vector_identity(
        direct_vectors, direct_verdicts
    )
    return stage_results, direct_vectors, direct_verdicts


def _same_fields(
    left: object, right: object, names: tuple[str, ...]
) -> bool:
    if type(left) is not type(right):
        return False
    for name in names:
        left_value = getattr(left, name)
        right_value = getattr(right, name)
        if type(left_value) is not type(right_value) or left_value != right_value:
            return False
    return True


def _observe(
    fixture: CanonicalInMemoryFixtureProfile,
    scope_id: str,
) -> tuple[InMemoryIntegrationScopeObservation, bool, bool]:
    orchestrated = orchestration_runtime.orchestrate_stage_admission_scope(
        scope_id,
        fixture.candidate_inputs,
        batch_context=fixture.batch_context,
        stage_authorization_context=fixture.stage_authorization_context,
    )
    direct_stage, direct_vectors, direct_verdicts = _direct_baseline(
        fixture, scope_id
    )
    orchestrated_vectors = tuple(
        item.ordered_rule_evaluations
        for item in orchestrated.candidate_results
    )
    orchestrated_verdicts = tuple(
        item.combined_verdict for item in orchestrated.candidate_results
    )
    _validate_stage_global_identity_reuse(
        orchestrated.required_rule_ids,
        orchestrated.stage_global_rule_evaluations,
        orchestrated_vectors,
    )
    _validate_normal_retained_vector_identity(
        orchestrated_vectors, orchestrated_verdicts
    )
    dispatch_parity = (
        len(orchestrated.stage_global_rule_evaluations) == len(direct_stage)
        and len(orchestrated.candidate_results) == len(direct_vectors)
    )
    if dispatch_parity:
        dispatch_parity = all(
            _same_fields(left, right, UNIFIED_PARITY_FIELDS)
            for left, right in zip(
                orchestrated.stage_global_rule_evaluations,
                direct_stage,
                strict=True,
            )
        )
    if dispatch_parity:
        dispatch_parity = all(
            _same_fields(left, right, UNIFIED_PARITY_FIELDS)
            for candidate_result, direct_vector in zip(
                orchestrated.candidate_results,
                direct_vectors,
                strict=True,
            )
            for left, right in zip(
                candidate_result.ordered_rule_evaluations,
                direct_vector,
                strict=True,
            )
        )
    aggregation_parity = (
        len(orchestrated.candidate_results) == len(direct_verdicts)
        and all(
            _same_fields(
                candidate_result.combined_verdict,
                direct_verdict,
                COMBINED_PARITY_FIELDS,
            )
            for candidate_result, direct_verdict in zip(
                orchestrated.candidate_results,
                direct_verdicts,
                strict=True,
            )
        )
    )
    expected_dispatches = len(
        contract.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope_id]
    ) + len(fixture.candidate_inputs) * len(
        contract.CANDIDATE_RULE_IDS_BY_SCOPE[scope_id]
    )
    if (
        orchestrated.required_rule_ids != contract.REQUIRED_RULE_IDS[scope_id]
        or orchestrated.stage_global_rule_ids
        != contract.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope_id]
        or orchestrated.candidate_rule_ids
        != contract.CANDIDATE_RULE_IDS_BY_SCOPE[scope_id]
        or orchestrated.dispatcher_call_count != expected_dispatches
        or orchestrated.aggregator_call_count != len(fixture.candidate_inputs)
        or orchestrated.orchestration_io_used is not False
        or orchestrated.action_permission_granted is not False
    ):
        raise RuntimeError("committed orchestration result invariant drift")
    observations = tuple(
        InMemoryIntegrationCandidateObservation(
            candidate_index=item.candidate_index,
            ordered_rule_ids=tuple(
                value.admission_rule_id
                for value in item.ordered_rule_evaluations
            ),
            ordered_outcomes=tuple(
                value.outcome for value in item.ordered_rule_evaluations
            ),
            ordered_reasons=tuple(
                value.reason for value in item.ordered_rule_evaluations
            ),
            ordered_passed=tuple(
                value.passed for value in item.ordered_rule_evaluations
            ),
            ordered_blocks_candidate=tuple(
                value.blocks_candidate
                for value in item.ordered_rule_evaluations
            ),
            combined_outcome=item.combined_verdict.outcome,
            combined_reason=item.combined_verdict.reason,
            dispatcher_call_count=item.dispatcher_call_count,
            aggregator_call_count=item.aggregator_call_count,
        )
        for item in orchestrated.candidate_results
    )
    return (
        InMemoryIntegrationScopeObservation(
            fixture_profile=fixture.fixture_profile,
            scope_id=scope_id,
            candidate_count=orchestrated.candidate_count,
            stage_global_rule_ids=orchestrated.stage_global_rule_ids,
            stage_global_outcomes=tuple(
                value.outcome
                for value in orchestrated.stage_global_rule_evaluations
            ),
            stage_global_reasons=tuple(
                value.reason
                for value in orchestrated.stage_global_rule_evaluations
            ),
            candidate_observations=observations,
            dispatcher_call_count=orchestrated.dispatcher_call_count,
            aggregator_call_count=orchestrated.aggregator_call_count,
            orchestration_io_used=orchestrated.orchestration_io_used,
            action_permission_granted=(
                orchestrated.action_permission_granted
            ),
        ),
        dispatch_parity,
        aggregation_parity,
    )


def run_covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke(
) -> InMemoryIntegrationSmokeReport:
    """Execute the fixed actual-runtime smoke without I/O or injection."""
    _assert_identity_snapshot(
        _COMMITTED_RUNTIME_IDENTITIES, _runtime_identity_snapshot()
    )
    observations: list[InMemoryIntegrationScopeObservation] = []
    dispatch_parity: list[bool] = []
    aggregation_parity: list[bool] = []
    fixtures = build_canonical_in_memory_fixture_profiles()
    for fixture in fixtures:
        for scope_id in fixture.scopes:
            observation, dispatch_ok, aggregation_ok = _observe(
                fixture, scope_id
            )
            observations.append(observation)
            dispatch_parity.append(dispatch_ok)
            aggregation_parity.append(aggregation_ok)
    _assert_identity_snapshot(
        _COMMITTED_RUNTIME_IDENTITIES, _runtime_identity_snapshot()
    )
    if False in dispatch_parity or False in aggregation_parity:
        raise RuntimeError("direct committed-runtime parity failed")
    return InMemoryIntegrationSmokeReport(
        observations=tuple(observations),
        direct_dispatch_parity_verified=True,
        direct_aggregation_parity_verified=True,
        committed_runtime_identity_unchanged=True,
        stage_global_identity_reuse_verified=True,
        normal_retained_vector_identity_verified=True,
        network_used=False,
        provider_used=False,
        download_used=False,
        training_used=False,
        ready_for_training=False,
    )


def serialize_smoke_report(
    report: InMemoryIntegrationSmokeReport,
) -> bytes:
    """Return a deterministic address-free JSON serialization."""
    if type(report) is not InMemoryIntegrationSmokeReport:
        raise TypeError("exact smoke report required")
    return (
        json.dumps(
            asdict(report),
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _canonical_jsonable(value: object) -> object:
    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) is tuple:
        return {
            "exact_type": "builtins.tuple",
            "items": [_canonical_jsonable(item) for item in value],
        }
    if type(value) is list:
        return {
            "exact_type": "builtins.list",
            "items": [_canonical_jsonable(item) for item in value],
        }
    if isinstance(value, Mapping):
        return {
            "exact_type": (
                f"{type(value).__module__}.{type(value).__qualname__}"
            ),
            "items": [
                [key, _canonical_jsonable(value[key])]
                for key in sorted(value)
            ],
        }
    if is_dataclass(value) and not isinstance(value, type):
        return {
            "exact_type": (
                f"{type(value).__module__}.{type(value).__qualname__}"
            ),
            "fields": [
                [item.name, _canonical_jsonable(getattr(value, item.name))]
                for item in fields(value)
            ],
        }
    raise TypeError(f"unsupported canonical fixture value type: {type(value)}")


def canonical_value_representation(value: object) -> str:
    return json.dumps(
        _canonical_jsonable(value),
        sort_keys=True,
        separators=(",", ":"),
    )


def exact_type_name(value: object) -> str:
    return f"{type(value).__module__}.{type(value).__qualname__}"


_CANDIDATE_PROVENANCE = MappingProxyType(
    {
        "candidate_record_id": (
            "ADMIT_001",
            "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004.py",
            "_evaluate_registered_admit_001; tests::_valid_spec",
        ),
        "pdb_id": (
            "ADMIT_002",
            "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004.py",
            "_evaluate_registered_admit_002; tests::_valid_spec",
        ),
        "ligand_comp_id": (
            "ADMIT_003",
            "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004.py",
            "_evaluate_registered_admit_003; tests::_valid_spec",
        ),
        **{
            name: (
                "ADMIT_004|ADMIT_005"
                if name
                in ("covalent_residue_name", "covalent_residue_atom_name")
                else "ADMIT_004",
                "src/covalent_ext/covapie_bulk_download_admission_admit_004_rule_logic_interface.py",
                "CANDIDATE_FIELDS; minimal_dispatch::_base_candidate",
            )
            for name in admit004.CANDIDATE_FIELDS
        },
        "covalent_event_evidence_source": (
            "ADMIT_006|ADMIT_007",
            "src/covalent_ext/covapie_bulk_download_admission_admit_006_rule_logic_interface.py",
            "CANONICAL_ENUM_MEMBERS; ALLOWED_COVALENT_EVIDENCE_CLASSES",
        ),
        "topology_restoration_disposition": (
            "ADMIT_008",
            "src/covalent_ext/covapie_bulk_download_admission_admit_008_rule_logic_interface.py",
            "CANONICAL_ENUM_MEMBERS; ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS",
        ),
        "duplicate_identity_key": (
            "ADMIT_009",
            "tests/test_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1.py",
            "KEY; _candidate; _kwargs",
        ),
        "leakage_group_id": (
            "ADMIT_010",
            "tests/test_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1.py",
            "SCALAR; PROVENANCE",
        ),
        "raw_target_relative_path": (
            "ADMIT_011",
            "tests/test_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1.py",
            "SCALAR; CONTRACT; SNAPSHOT",
        ),
    }
)

_EVALUATION_PROVENANCE = MappingProxyType(
    {
        admit004.EVIDENCE_CONTEXT_KEY: (
            "ADMIT_004",
            "src/covalent_ext/covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004.py",
            "_base_context",
        ),
        "allowed_covalent_evidence_classes": (
            "ADMIT_006|ADMIT_007",
            "src/covalent_ext/covapie_bulk_download_admission_admit_006_rule_logic_interface.py",
            "ALLOWED_COVALENT_EVIDENCE_CLASSES",
        ),
        "allowed_topology_restoration_dispositions": (
            "ADMIT_008",
            "src/covalent_ext/covapie_bulk_download_admission_admit_008_rule_logic_interface.py",
            "ALLOWED_TOPOLOGY_RESTORATION_DISPOSITIONS",
        ),
        "duplicate_identity_key_contract": (
            "ADMIT_009",
            "tests/test_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1.py",
            "POLICY; _kwargs",
        ),
        "leakage_group_assignment_provenance_contract": (
            "ADMIT_010",
            "src/covalent_ext/covapie_bulk_download_admission_admit_010_rule_logic_interface.py",
            "_valid_contract",
        ),
        "raw_target_relative_path_contract": (
            "ADMIT_011",
            "src/covalent_ext/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate.py",
            "DEFAULT_CONTRACT",
        ),
        "existing_raw_target_relative_paths": (
            "ADMIT_011",
            "src/covalent_ext/covapie_bulk_download_admission_admit_011_rule_logic_interface.py",
            "_empty_snapshot",
        ),
        "allowed_download_result_statuses": (
            "ADMIT_012",
            "src/covalent_ext/covapie_bulk_download_admission_admit_012_rule_logic_interface.py",
            "FORMAL_CONTEXT_VALUES[0]",
        ),
        "successful_http_status_contract": (
            "ADMIT_012",
            "src/covalent_ext/covapie_bulk_download_admission_admit_012_rule_logic_interface.py",
            "FORMAL_CONTEXT_VALUES[1]",
        ),
        "content_length_contract": (
            "ADMIT_012",
            "src/covalent_ext/covapie_bulk_download_admission_admit_012_rule_logic_interface.py",
            "FORMAL_CONTEXT_VALUES[2]",
        ),
        "sha256_format_contract": (
            "ADMIT_012",
            "src/covalent_ext/covapie_bulk_download_admission_admit_012_rule_logic_interface.py",
            "FORMAL_CONTEXT_VALUES[3]",
        ),
        "expected_content_length_bytes": (
            "ADMIT_013",
            "tests/test_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1.py",
            "VALID_AUTHORITY",
        ),
        "expected_sha256": (
            "ADMIT_013",
            "tests/test_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1.py",
            "VALID_AUTHORITY",
        ),
        "explicit_integrity_verdict": (
            "ADMIT_013",
            "tests/test_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1.py",
            "VALID_AUTHORITY",
        ),
    }
)


def _provenance_row(
    fixture_profile: str,
    container_name: str,
    field_name: str,
    value: object,
    semantic: tuple[str, str, str],
) -> dict[str, str]:
    consumed, path, symbol = semantic
    return {
        "fixture_profile": fixture_profile,
        "container_name": container_name,
        "field_name": field_name,
        "exact_type": exact_type_name(value),
        "canonical_value": canonical_value_representation(value),
        "consumed_rule_ids": consumed,
        "semantic_source_path": path,
        "semantic_source_symbol": symbol,
        "projection_policy": "deterministically_projected_from_committed_fixture_contract",
        "ambiguity_status": "resolved_from_committed_contract",
        "verified": "true",
    }


def build_fixture_provenance_rows() -> tuple[dict[str, str], ...]:
    rows: list[dict[str, str]] = []
    for fixture in build_canonical_in_memory_fixture_profiles():
        for candidate_index, candidate_input in enumerate(
            fixture.candidate_inputs
        ):
            suffix = f"[{candidate_index}]"
            for name, value in candidate_input.candidate_record.items():
                rows.append(
                    _provenance_row(
                        fixture.fixture_profile,
                        f"candidate_record{suffix}",
                        name,
                        value,
                        _CANDIDATE_PROVENANCE[name],
                    )
                )
            evaluation = candidate_input.evaluation_context
            if evaluation is None:
                raise RuntimeError("canonical evaluation context missing")
            for name, value in evaluation.items():
                rows.append(
                    _provenance_row(
                        fixture.fixture_profile,
                        f"evaluation_context{suffix}",
                        name,
                        value,
                        _EVALUATION_PROVENANCE[name],
                    )
                )
            download = candidate_input.download_result_context
            if download is None:
                raise RuntimeError("canonical download context missing")
            for name, value in download.items():
                rows.append(
                    _provenance_row(
                        fixture.fixture_profile,
                        f"download_result_context{suffix}",
                        name,
                        value,
                        (
                            "ADMIT_012|ADMIT_013",
                            "tests/test_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1.py",
                            "VALID_DOWNLOAD",
                        ),
                    )
                )
        for name, value in fixture.batch_context.items():
            semantic = (
                (
                    "ADMIT_001",
                    "tests/test_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004_v1.py",
                    "_valid_spec",
                )
                if name == "batch_candidate_record_ids"
                else (
                    "ADMIT_009",
                    "tests/test_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1.py",
                    "_kwargs",
                )
            )
            rows.append(
                _provenance_row(
                    fixture.fixture_profile,
                    "batch_context",
                    name,
                    value,
                    semantic,
                )
            )
        for name, value in fixture.stage_authorization_context.items():
            rule_id = "ADMIT_014" if "download" in name else "ADMIT_015"
            rows.append(
                _provenance_row(
                    fixture.fixture_profile,
                    "stage_authorization_context",
                    name,
                    value,
                    (
                        rule_id,
                        "tests/test_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015_v1.py",
                        (
                            "current_stage_download_authorized"
                            if rule_id == "ADMIT_014"
                            else "current_stage_training_authorized"
                        ),
                    ),
                )
            )
    return tuple(rows)
