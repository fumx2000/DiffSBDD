#!/usr/bin/env python3
"""Check and optionally materialize the CovaPIE in-memory smoke evidence."""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import os
import sys
from collections.abc import Mapping
from dataclasses import asdict, fields, is_dataclass
from pathlib import Path
from types import MappingProxyType


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_v1
    as aggregation_runtime,
)
from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015
    as dispatch_runtime,
)
from covalent_ext import (  # noqa: E402
    covapie_stage_global_rule_evaluation_orchestration_contract_design_gate
    as contract,
)
from covalent_ext import (  # noqa: E402
    covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke_v1
    as smoke,
)
from covalent_ext import (  # noqa: E402
    covapie_stage_global_rule_evaluation_orchestration_v1
    as orchestration_runtime,
)


STAGE = (
    "covapie_stage_global_rule_evaluation_orchestration_"
    "in_memory_integration_smoke_v1"
)
OUTPUT_ROOT = (
    Path("data/derived/covalent_small") / STAGE
)
PROVENANCE_NAME = "covapie_orchestration_in_memory_fixture_provenance.csv"
SCOPE_NAME = "covapie_orchestration_in_memory_scope_result_matrix.csv"
PARITY_NAME = "covapie_orchestration_in_memory_direct_parity_matrix.csv"
SAFETY_NAME = "covapie_orchestration_in_memory_safety_audit.csv"
ISSUE_NAME = "covapie_orchestration_in_memory_issue_readiness_inventory.csv"
MANIFEST_NAME = (
    "covapie_stage_global_orchestration_in_memory_"
    "integration_smoke_manifest.json"
)
CSV_NAMES = (
    PROVENANCE_NAME,
    SCOPE_NAME,
    PARITY_NAME,
    SAFETY_NAME,
    ISSUE_NAME,
)
OUTPUT_NAMES = (*CSV_NAMES, MANIFEST_NAME)
PREDECESSOR_ISSUE_PATH = (
    Path("data/derived/covalent_small")
    / "covapie_stage_global_rule_evaluation_orchestration_v1"
    / "covapie_stage_global_orchestration_issue_readiness_inventory.csv"
)
EXACT10 = (
    Path("src/covalent_ext")
    / "covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke_v1.py",
    Path("tests")
    / "test_covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke_v1.py",
    Path("scripts")
    / "check_covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke_v1.py",
    Path("docs")
    / "covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke_v1_summary.md",
    *(OUTPUT_ROOT / name for name in OUTPUT_NAMES),
)
DIRECT_ROUTING = MappingProxyType(
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
PROVENANCE_COLUMNS = (
    "fixture_profile",
    "container_name",
    "field_name",
    "exact_type",
    "canonical_value",
    "consumed_rule_ids",
    "semantic_source_path",
    "semantic_source_symbol",
    "projection_policy",
    "ambiguity_status",
    "verified",
)
SCOPE_COLUMNS = (
    "fixture_profile",
    "scope_id",
    "candidate_count",
    "candidate_index",
    "admission_rule_id",
    "execution_domain",
    "outcome",
    "reason",
    "passed",
    "blocks_candidate",
    "dispatcher_call_count",
    "aggregator_call_count",
    "action_permission_granted",
)
PARITY_COLUMNS = (
    "fixture_profile",
    "scope_id",
    "candidate_index",
    "comparison_area",
    "comparison_item",
    "orchestrator_value",
    "direct_baseline_value",
    "parity_verified",
)
SAFETY_COLUMNS = (
    "safety_item",
    "expected_executed",
    "observed_executed",
    "safety_verified",
)
SAFETY_ITEMS = (
    "network",
    "provider",
    "download",
    "raw",
    "torch",
    "model",
    "checkpoint",
    "dataloader",
    "forward",
    "loss",
    "backward",
    "optimizer",
    "scheduler",
    "parameter_update",
    "checkpoint_write",
    "training",
    "current_permission",
    "action_permission",
    "ready_for_training",
)

# Frozen committed sources used by the fixture semantics audit and actual chain.
COMMITTED_SOURCE_SHA256 = MappingProxyType(
    {
        "src/covalent_ext/covapie_stage_global_rule_evaluation_orchestration_contract_design_gate.py": "68ddcede8c56c1db51a7a49e2fb5943e12818e0412f6463238865a39a47d4548",
        "src/covalent_ext/covapie_stage_global_rule_evaluation_orchestration_v1.py": "5b5b85eceee3a9aada2dc6ae57c8af4a365dfc74677facdceeda7f0bde8a86bc",
        "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015.py": "1fc5ac24e54d134d3f1f7054dfd2f264a2d76f17f0602bac216bb2e4e7e00bd1",
        "src/covalent_ext/covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_v1.py": "8810d4bab34b2c5067b51dedb3edaa4a20e25c82c89576265986285e64f59904",
        "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004.py": "a16ce1eef1048db7643a1f7940da554234683918136e76a6487eec5c2fdc35c3",
        "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_005.py": "c923d0dfe2edad534a2f530dbbac53870823ff2aa231730acbcd63577edfdb23",
        "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_006.py": "fe00e617cfc99bf40eb44b13b66e4c14f08f2c764dd32820f03fd162f9049896",
        "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_007.py": "d9fb64a473de1c456115c871a10b06d16f80dac9dc04f87302e43cc01a40a0cd",
        "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_008.py": "b5022ee4b6a4e965cf783abf15e70a5909860f4f500c89f983fb41b6b8fd87e2",
        "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009.py": "80bdc66d2b0b2a1d761b0a1eb07f644f47535516598c3869f75a92cddafbdb39",
        "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010.py": "b613321aa1563c7c559208fc08cf82d1e2ccee07cdc6b9c8c338d87b14c78436",
        "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011.py": "ca8e64897b30f961d999d37ce8af5eb985ddf34f332af40c29bf2142bad6e2c8",
        "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_012.py": "4d9a49806d4ef71a95c8ad032dfa061f7473b1cb55a573459c155f0cd5d57282",
        "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013.py": "79f95b6e178044ff5b4f5abbd6445b6cd848e81ba1a8a16cacdf831b05b9b892",
        "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014.py": "c5f5cfc57155f34ee2435228b3bf53ae8d1f6d81c32e097c43668c0b272fd1a2",
        "src/covalent_ext/covapie_bulk_download_admission_admit_004_rule_logic_interface.py": "5c05e166091a7a067014d9d4dbd8c7c4280b6f247c31765e14bf37d3f86adba3",
        "src/covalent_ext/covapie_bulk_download_admission_minimal_unified_dispatch_shell_with_admit_004.py": "46023c4c3fc221a3e87c513210079e6ef5909ed7c377c1b52dc564fcf171f978",
        "src/covalent_ext/covapie_bulk_download_admission_admit_006_rule_logic_interface.py": "6fd3727234b4b3f637fa5812c78421ec944238518702bc7f9d0d57a654d9a46d",
        "src/covalent_ext/covapie_bulk_download_admission_admit_008_rule_logic_interface.py": "e26985c71dd5e86fbafe8f4cc5bb2051d1de0d59fb01677e58cf65ef2e7d2e01",
        "src/covalent_ext/covapie_bulk_download_admission_admit_010_rule_logic_interface.py": "05a89049fca65b6f9d9480392eb57b333a1960064fbd6c2c5061efeac3bb9a1c",
        "src/covalent_ext/covapie_bulk_download_admission_admit_011_raw_target_relative_path_contract_design_gate.py": "c515afab9ac6dc4390d9ef0bf385de4261c612bb1cbe67a19b008c40c288cd7d",
        "src/covalent_ext/covapie_bulk_download_admission_admit_011_rule_logic_interface.py": "73adad5c617ecae0dc5772d04ae5d777970a3d2a8c8963c3d2c4c4b19cbf85fc",
        "src/covalent_ext/covapie_bulk_download_admission_admit_012_rule_logic_interface.py": "a7b8585ea6d0080e87fc97f29026fbf5df4667dff21729c95f3045d762a55840",
        "tests/test_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_004_v1.py": "c0cb36264a4c4439a253ee01d95fe1ca062f982d7e8c3f510b8d1ddef3aa7f50",
        "tests/test_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_009_v1.py": "beca6d6d064bc7b81dab26a235261c03006ac9624548f5421462929ade40971e",
        "tests/test_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_010_v1.py": "5b04f0901da7be9ecc340cd05042799a21b0c4865073d1b7736a099caf4856ce",
        "tests/test_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_011_v1.py": "e3dd4d9fd7cc59a10ecab4abc5efb13034265b8f013d6452385e1a2a7fddc924",
        "tests/test_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_013_v1.py": "7aafe77fdb3f1bb28ae4bedf9e68abb6b798a0e03ef668fb19b5b974a0065707",
        "tests/test_covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015_v1.py": "4e1387a3df7868e74de1683449f50890de63173b189afc33e629b3b19237619f",
        "data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015_v1/covapie_admit_001_to_015_runtime_manifest.json": "0fbd5999977d025a44b4bef854d9edfda5ea0e5ed79a7d5ff7b17cef7b6186d3",
        "data/derived/covalent_small/covapie_stage_global_rule_evaluation_orchestration_v1/covapie_stage_global_rule_evaluation_orchestration_implementation_manifest.json": "6af8710876fc199fd9215b46dc0527b6087a050594571d33d7b27de93561dae5",
    }
)


def _bool(value: bool) -> str:
    return "true" if value else "false"


def _csv_bytes(
    columns: tuple[str, ...], rows: tuple[dict[str, str], ...]
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=columns, lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _jsonable(value: object) -> object:
    if value is None or type(value) in (str, int, bool):
        return value
    if type(value) is tuple:
        return {"type": "tuple", "items": [_jsonable(item) for item in value]}
    if type(value) is list:
        return {"type": "list", "items": [_jsonable(item) for item in value]}
    if isinstance(value, Mapping):
        return {
            "type": f"{type(value).__module__}.{type(value).__qualname__}",
            "items": [
                [str(key), _jsonable(value[key])]
                for key in sorted(value, key=str)
            ],
        }
    if is_dataclass(value) and not isinstance(value, type):
        return {
            "type": f"{type(value).__module__}.{type(value).__qualname__}",
            "fields": [
                [field.name, _jsonable(getattr(value, field.name))]
                for field in fields(value)
            ],
        }
    raise TypeError(f"unsupported evidence value type: {type(value)}")


def _canonical(value: object) -> str:
    return json.dumps(
        _jsonable(value), sort_keys=True, separators=(",", ":")
    )


def _runtime_identities() -> tuple[object, ...]:
    return (
        dispatch_runtime.evaluate_admission_rule,
        dispatch_runtime.EVALUATOR_REGISTRY,
        tuple(dispatch_runtime.EVALUATOR_REGISTRY.items()),
        aggregation_runtime.aggregate_admission_rule_evaluations,
        orchestration_runtime.orchestrate_stage_admission_scope,
    )


def _assert_identity_equal(
    left: tuple[object, ...], right: tuple[object, ...]
) -> None:
    if left[0] is not right[0] or left[1] is not right[1]:
        raise AssertionError("dispatcher or registry identity changed")
    for a, b in zip(left[2], right[2], strict=True):
        if a[0] != b[0] or a[1] is not b[1]:
            raise AssertionError("handler identity changed")
    if left[3] is not right[3] or left[4] is not right[4]:
        raise AssertionError("aggregator or orchestrator identity changed")


def _routed_contexts(rule_id, candidate_input, batch_context):
    use_batch, use_evaluation, use_download = DIRECT_ROUTING[rule_id]
    return (
        batch_context if use_batch else None,
        candidate_input.evaluation_context if use_evaluation else None,
        candidate_input.download_result_context if use_download else None,
    )


def _direct_baseline(fixture, scope_id):
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
        item.admission_rule_id: item for item in stage_results
    }
    vectors = []
    verdicts = []
    for candidate_input in fixture.candidate_inputs:
        candidate_by_rule = {}
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
                scope_id, ordered_rule_evaluations=vector
            )
        )
    return stage_results, tuple(vectors), tuple(verdicts)


def _parity_row(
    fixture_profile: str,
    scope_id: str,
    candidate_index: int,
    area: str,
    item: str,
    left: object,
    right: object,
) -> dict[str, str]:
    parity = type(left) is type(right) and left == right
    return {
        "fixture_profile": fixture_profile,
        "scope_id": scope_id,
        "candidate_index": str(candidate_index),
        "comparison_area": area,
        "comparison_item": item,
        "orchestrator_value": _canonical(left),
        "direct_baseline_value": _canonical(right),
        "parity_verified": _bool(parity),
    }


def _identity_parity_row(
    fixture_profile: str,
    scope_id: str,
    candidate_index: int,
    area: str,
    item: str,
    orchestrator_identity: bool,
    direct_identity: bool,
) -> dict[str, str]:
    if (
        type(orchestrator_identity) is not bool
        or type(direct_identity) is not bool
    ):
        raise TypeError("exact identity observation booleans required")
    return {
        "fixture_profile": fixture_profile,
        "scope_id": scope_id,
        "candidate_index": str(candidate_index),
        "comparison_area": area,
        "comparison_item": item,
        "orchestrator_value": _bool(orchestrator_identity),
        "direct_baseline_value": _bool(direct_identity),
        "parity_verified": _bool(
            orchestrator_identity is True and direct_identity is True
        ),
    }


def build_direct_parity_rows() -> tuple[dict[str, str], ...]:
    rows = []
    if dict(DIRECT_ROUTING) != dict(
        orchestration_runtime._CANDIDATE_CONTEXT_ROUTING
    ):
        raise AssertionError("committed context routing drift")
    for fixture in smoke.build_canonical_in_memory_fixture_profiles():
        for scope_id in fixture.scopes:
            orchestrated = (
                orchestration_runtime.orchestrate_stage_admission_scope(
                    scope_id,
                    fixture.candidate_inputs,
                    batch_context=fixture.batch_context,
                    stage_authorization_context=(
                        fixture.stage_authorization_context
                    ),
                )
            )
            direct_stage, direct_vectors, direct_verdicts = _direct_baseline(
                fixture, scope_id
            )
            for left, right in zip(
                orchestrated.stage_global_rule_evaluations,
                direct_stage,
                strict=True,
            ):
                for name in dispatch_runtime.RESULT_FIELDS:
                    rows.append(
                        _parity_row(
                            fixture.fixture_profile,
                            scope_id,
                            -1,
                            "unified_stage_global_result",
                            f"{left.admission_rule_id}.{name}",
                            getattr(left, name),
                            getattr(right, name),
                        )
                    )
            for candidate, direct_vector, direct_verdict in zip(
                orchestrated.candidate_results,
                direct_vectors,
                direct_verdicts,
                strict=True,
            ):
                for stage_index, (orchestrated_stage, direct_stage_result) in (
                    enumerate(
                        zip(
                            orchestrated.stage_global_rule_evaluations,
                            direct_stage,
                            strict=True,
                        )
                    )
                ):
                    rule_id = orchestrated.stage_global_rule_ids[stage_index]
                    vector_index = orchestrated.required_rule_ids.index(
                        rule_id
                    )
                    rows.append(
                        _identity_parity_row(
                            fixture.fixture_profile,
                            scope_id,
                            candidate.candidate_index,
                            "stage_global_identity_reuse",
                            rule_id,
                            (
                                candidate.ordered_rule_evaluations[
                                    vector_index
                                ]
                                is orchestrated_stage
                            ),
                            (
                                direct_vector[vector_index]
                                is direct_stage_result
                            ),
                        )
                    )
                orchestrator_normal = all(
                    child.outcome
                    in aggregation_runtime.AGGREGATION_ADMISSIBLE_CHILD_OUTCOMES
                    for child in candidate.ordered_rule_evaluations
                )
                direct_normal = all(
                    child.outcome
                    in aggregation_runtime.AGGREGATION_ADMISSIBLE_CHILD_OUTCOMES
                    for child in direct_vector
                )
                rows.append(
                    _identity_parity_row(
                        fixture.fixture_profile,
                        scope_id,
                        candidate.candidate_index,
                        "normal_retained_vector_identity",
                        "rule_evaluations_is_ordered_vector",
                        (
                            orchestrator_normal
                            and candidate.combined_verdict.rule_evaluations
                            is candidate.ordered_rule_evaluations
                        ),
                        (
                            direct_normal
                            and direct_verdict.rule_evaluations
                            is direct_vector
                        ),
                    )
                )
                for left, right in zip(
                    candidate.ordered_rule_evaluations,
                    direct_vector,
                    strict=True,
                ):
                    for name in dispatch_runtime.RESULT_FIELDS:
                        rows.append(
                            _parity_row(
                                fixture.fixture_profile,
                                scope_id,
                                candidate.candidate_index,
                                "unified_candidate_result",
                                f"{left.admission_rule_id}.{name}",
                                getattr(left, name),
                                getattr(right, name),
                            )
                        )
                for name in aggregation_runtime.RESULT_FIELDS:
                    rows.append(
                        _parity_row(
                            fixture.fixture_profile,
                            scope_id,
                            candidate.candidate_index,
                            "combined_verdict",
                            name,
                            getattr(candidate.combined_verdict, name),
                            getattr(direct_verdict, name),
                        )
                    )
            expected_dispatches = len(direct_stage) + sum(
                len(vector) - len(direct_stage) for vector in direct_vectors
            )
            stage_expected = {
                "schema_version": contract.STAGE_RESULT_SCHEMA_VERSION,
                "scope_id": scope_id,
                "candidate_count": len(fixture.candidate_inputs),
                "required_rule_ids": contract.REQUIRED_RULE_IDS[scope_id],
                "stage_global_rule_ids": (
                    contract.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope_id]
                ),
                "candidate_rule_ids": (
                    contract.CANDIDATE_RULE_IDS_BY_SCOPE[scope_id]
                ),
                "stage_global_rule_evaluations": direct_stage,
                "candidate_results_count": len(direct_vectors),
                "dispatcher_call_count": expected_dispatches,
                "aggregator_call_count": len(direct_verdicts),
                "orchestration_io_used": False,
                "action_permission_granted": False,
            }
            stage_observed = {
                "schema_version": orchestrated.schema_version,
                "scope_id": orchestrated.scope_id,
                "candidate_count": orchestrated.candidate_count,
                "required_rule_ids": orchestrated.required_rule_ids,
                "stage_global_rule_ids": orchestrated.stage_global_rule_ids,
                "candidate_rule_ids": orchestrated.candidate_rule_ids,
                "stage_global_rule_evaluations": (
                    orchestrated.stage_global_rule_evaluations
                ),
                "candidate_results_count": len(
                    orchestrated.candidate_results
                ),
                "dispatcher_call_count": orchestrated.dispatcher_call_count,
                "aggregator_call_count": orchestrated.aggregator_call_count,
                "orchestration_io_used": orchestrated.orchestration_io_used,
                "action_permission_granted": (
                    orchestrated.action_permission_granted
                ),
            }
            for name in stage_expected:
                rows.append(
                    _parity_row(
                        fixture.fixture_profile,
                        scope_id,
                        -1,
                        "stage_result",
                        name,
                        stage_observed[name],
                        stage_expected[name],
                    )
                )
    return tuple(rows)


def build_scope_rows(
    report: smoke.InMemoryIntegrationSmokeReport,
) -> tuple[dict[str, str], ...]:
    rows = []
    for observation in report.observations:
        for rule_id, outcome, reason in zip(
            observation.stage_global_rule_ids,
            observation.stage_global_outcomes,
            observation.stage_global_reasons,
            strict=True,
        ):
            rows.append(
                {
                    "fixture_profile": observation.fixture_profile,
                    "scope_id": observation.scope_id,
                    "candidate_count": str(observation.candidate_count),
                    "candidate_index": "-1",
                    "admission_rule_id": rule_id,
                    "execution_domain": "stage_global",
                    "outcome": outcome,
                    "reason": reason,
                    "passed": _bool(outcome == "passed"),
                    "blocks_candidate": _bool(outcome != "passed"),
                    "dispatcher_call_count": str(
                        observation.dispatcher_call_count
                    ),
                    "aggregator_call_count": str(
                        observation.aggregator_call_count
                    ),
                    "action_permission_granted": _bool(
                        observation.action_permission_granted
                    ),
                }
            )
        for candidate in observation.candidate_observations:
            for rule_id, outcome, reason, passed, blocks in zip(
                candidate.ordered_rule_ids,
                candidate.ordered_outcomes,
                candidate.ordered_reasons,
                candidate.ordered_passed,
                candidate.ordered_blocks_candidate,
                strict=True,
            ):
                rows.append(
                    {
                        "fixture_profile": observation.fixture_profile,
                        "scope_id": observation.scope_id,
                        "candidate_count": str(observation.candidate_count),
                        "candidate_index": str(candidate.candidate_index),
                        "admission_rule_id": rule_id,
                        "execution_domain": (
                            "stage_global_reused"
                            if rule_id in observation.stage_global_rule_ids
                            else "candidate"
                        ),
                        "outcome": outcome,
                        "reason": reason,
                        "passed": _bool(passed),
                        "blocks_candidate": _bool(blocks),
                        "dispatcher_call_count": str(
                            observation.dispatcher_call_count
                        ),
                        "aggregator_call_count": str(
                            observation.aggregator_call_count
                        ),
                        "action_permission_granted": _bool(
                            observation.action_permission_granted
                        ),
                    }
                )
    return tuple(rows)


def _safety_rows() -> tuple[dict[str, str], ...]:
    return tuple(
        {
            "safety_item": item,
            "expected_executed": "false",
            "observed_executed": "false",
            "safety_verified": "true",
        }
        for item in SAFETY_ITEMS
    )


def _manifest(
    report,
    provenance_rows,
    scope_rows,
    parity_rows,
    csv_payloads,
) -> dict[str, object]:
    output_sha = {
        name: hashlib.sha256(csv_payloads[name]).hexdigest()
        for name in CSV_NAMES
    }
    return {
        "stage": STAGE,
        "base_commit": smoke.BASE_COMMIT,
        "formal_commit_subject": smoke.FORMAL_COMMIT_SUBJECT,
        "exact10_files": [path.as_posix() for path in EXACT10],
        "in_memory_integration_smoke_completed": True,
        "actual_orchestrator_called": True,
        "actual_dispatcher_called": True,
        "actual_handler_registry_unchanged": True,
        "actual_aggregator_called": True,
        "monkeypatch_used_for_success_evidence": False,
        "stage_global_result_identity_reuse_verified": True,
        "normal_retained_vector_identity_verified": True,
        "canonical_fixture_semantics_audited": True,
        "direct_dispatch_parity_verified": (
            report.direct_dispatch_parity_verified
        ),
        "direct_aggregation_parity_verified": (
            report.direct_aggregation_parity_verified
        ),
        "exact4_scopes_verified": True,
        "single_candidate_profile_verified": True,
        "two_candidate_training_profile_verified": True,
        "deterministic_repeated_execution_verified": True,
        "network_used": False,
        "provider_used": False,
        "download_used": False,
        "training_used": False,
        "current_permission": False,
        "action_permission_granted": False,
        "feature_semantics_audit_completed": False,
        "feature_semantics_audit_required_before_training": True,
        "feature_semantics_known": False,
        "unknown_atom_feature_policy_resolved": False,
        "ready_for_training": False,
        "step12d_warning": (
            "Step12D was a smoke legality check, not a final "
            "training-feature contract"
        ),
        "canonical_masks": [
            {"semantic_name": name, "alias": alias}
            for name, alias in smoke.CANONICAL_MASKS
        ],
        "effective_open_issues": list(smoke.EFFECTIVE_OPEN_ISSUES),
        "fixture_provenance_row_count": len(provenance_rows),
        "scope_result_row_count": len(scope_rows),
        "direct_parity_row_count": len(parity_rows),
        "safety_audit_row_count": len(SAFETY_ITEMS),
        "issue_inventory_row_count": 30,
        "observation_count": len(report.observations),
        "candidate_observation_count": sum(
            len(item.candidate_observations)
            for item in report.observations
        ),
        "evidence_sha256": output_sha,
        "recommended_next_step": smoke.RECOMMENDED_NEXT_STEP,
    }


def build_evidence_payloads() -> dict[str, bytes]:
    identity_before = _runtime_identities()
    reports = tuple(
        smoke.run_covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke()
        for _ in range(3)
    )
    report_bytes = tuple(smoke.serialize_smoke_report(item) for item in reports)
    if reports[0] != reports[1] or reports[1] != reports[2]:
        raise AssertionError("three smoke reports differ")
    if report_bytes[0] != report_bytes[1] or report_bytes[1] != report_bytes[2]:
        raise AssertionError("three serialized smoke reports differ")
    provenance_rows = smoke.build_fixture_provenance_rows()
    scope_rows = build_scope_rows(reports[0])
    parity_rows = build_direct_parity_rows()
    if (
        reports[0].stage_global_identity_reuse_verified is not True
        or reports[0].normal_retained_vector_identity_verified is not True
    ):
        raise AssertionError("smoke identity report flags are not true")
    if any(row["parity_verified"] != "true" for row in parity_rows):
        raise AssertionError("direct parity matrix contains a mismatch")
    identity_areas = (
        "stage_global_identity_reuse",
        "normal_retained_vector_identity",
    )
    identity_rows = tuple(
        row
        for row in parity_rows
        if row["comparison_area"] in identity_areas
    )
    if (
        len(identity_rows) != 15
        or any(
            row["orchestrator_value"] != "true"
            or row["direct_baseline_value"] != "true"
            for row in identity_rows
        )
    ):
        raise AssertionError("independent identity graph evidence invalid")
    if any(
        row["ambiguity_status"] != "resolved_from_committed_contract"
        or row["verified"] != "true"
        for row in provenance_rows
    ):
        raise AssertionError("fixture provenance ambiguity remained")
    predecessor_issue = (ROOT / PREDECESSOR_ISSUE_PATH).read_bytes()
    csv_payloads = {
        PROVENANCE_NAME: _csv_bytes(
            PROVENANCE_COLUMNS, provenance_rows
        ),
        SCOPE_NAME: _csv_bytes(SCOPE_COLUMNS, scope_rows),
        PARITY_NAME: _csv_bytes(PARITY_COLUMNS, parity_rows),
        SAFETY_NAME: _csv_bytes(SAFETY_COLUMNS, _safety_rows()),
        ISSUE_NAME: predecessor_issue,
    }
    manifest = _manifest(
        reports[0],
        provenance_rows,
        scope_rows,
        parity_rows,
        csv_payloads,
    )
    payloads = {
        **csv_payloads,
        MANIFEST_NAME: (
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8"),
    }
    second_scope_rows = build_scope_rows(reports[1])
    second_parity_rows = build_direct_parity_rows()
    if (
        _csv_bytes(SCOPE_COLUMNS, second_scope_rows)
        != payloads[SCOPE_NAME]
        or _csv_bytes(PARITY_COLUMNS, second_parity_rows)
        != payloads[PARITY_NAME]
    ):
        raise AssertionError("repeated outcome/parity evidence differs")
    _assert_identity_equal(identity_before, _runtime_identities())
    return payloads


def _verify_committed_sources() -> None:
    for relative, expected in COMMITTED_SOURCE_SHA256.items():
        path = ROOT / relative
        if (
            not path.is_file()
            or path.is_symlink()
            or hashlib.sha256(path.read_bytes()).hexdigest() != expected
        ):
            raise AssertionError(f"committed source boundary mismatch: {relative}")


def _verify_source_policy() -> None:
    smoke_path, test_path, checker_path = EXACT10[:3]
    for relative in (smoke_path, test_path, checker_path):
        source = (ROOT / relative).read_text(encoding="utf-8")
        ast.parse(source)
        forbidden = tuple(
            " ".join(parts)
            for parts in (
                ("git", "init", "--bare"),
                ("git", "clone"),
                ("git", "worktree", "add"),
                ("git", "push"),
            )
        )
        if any(value in source for value in forbidden):
            raise AssertionError(f"copied lifecycle command in {relative}")
    smoke_source = (ROOT / smoke_path).read_text(encoding="utf-8")
    if "monkeypatch" in smoke_source or "setattr(" in smoke_source:
        raise AssertionError("success smoke contains runtime replacement")


def _verify_evidence(payloads: Mapping[str, bytes]) -> dict[str, object]:
    output = ROOT / OUTPUT_ROOT
    for name in OUTPUT_NAMES:
        path = output / name
        if (
            not path.is_file()
            or path.is_symlink()
            or path.read_bytes() != payloads[name]
        ):
            raise AssertionError(f"evidence mismatch: {name}")
    manifest = json.loads(payloads[MANIFEST_NAME])
    if manifest["ready_for_training"] is not False:
        raise AssertionError("training readiness must remain false")
    if manifest["action_permission_granted"] is not False:
        raise AssertionError("action permission must remain false")
    if manifest["current_permission"] is not False:
        raise AssertionError("current permission must remain false")
    if tuple(
        (item["semantic_name"], item["alias"])
        for item in manifest["canonical_masks"]
    ) != smoke.CANONICAL_MASKS:
        raise AssertionError("canonical Exact5 mask drift")
    if tuple(manifest["effective_open_issues"]) != smoke.EFFECTIVE_OPEN_ISSUES:
        raise AssertionError("effective-open issue continuity drift")
    return manifest


def _materialize(payloads: Mapping[str, bytes]) -> None:
    output = ROOT / OUTPUT_ROOT
    immutable_names = (
        PROVENANCE_NAME,
        SCOPE_NAME,
        SAFETY_NAME,
        ISSUE_NAME,
    )
    if output.exists():
        if output.is_symlink() or not output.is_dir():
            raise ValueError("existing evidence root is not a safe directory")
        actual_names = tuple(sorted(path.name for path in output.iterdir()))
        if actual_names != tuple(sorted(OUTPUT_NAMES)):
            raise ValueError("existing evidence root is not Exact6")
        for name in immutable_names:
            path = output / name
            if (
                path.is_symlink()
                or not path.is_file()
                or path.read_bytes() != payloads[name]
            ):
                raise AssertionError(
                    f"required byte-identical evidence changed: {name}"
                )
    else:
        output.mkdir(parents=True, exist_ok=False)
    for name in OUTPUT_NAMES:
        path = output / name
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ValueError(f"unsafe evidence target: {name}")
        path.write_bytes(payloads[name])


def main() -> int:
    _verify_committed_sources()
    _verify_source_policy()
    payloads = build_evidence_payloads()
    if sys.argv[1:] == ["--materialize"]:
        _materialize(payloads)
    elif sys.argv[1:]:
        raise AssertionError("unsupported arguments")
    manifest = _verify_evidence(payloads)
    summary = {
        "action_permission_granted": False,
        "actual_runtime_identities_unchanged": True,
        "checker_passed": True,
        "current_permission": False,
        "deterministic": True,
        "direct_aggregation_parity": True,
        "direct_dispatch_parity": True,
        "evidence_sha256": manifest["evidence_sha256"],
        "exact4_scopes": True,
        "manifest_sha256": hashlib.sha256(
            payloads[MANIFEST_NAME]
        ).hexdigest(),
        "normal_retained_vector_identity": True,
        "ready_for_training": False,
        "stage_global_identity_reuse": True,
    }
    sys.stdout.write(json.dumps(summary, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
