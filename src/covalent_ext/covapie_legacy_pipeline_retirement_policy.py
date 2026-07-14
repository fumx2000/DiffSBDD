from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable, NoReturn


CANONICAL_FINAL_DATASET_QA_STAGE = "covapie_final_dataset_qa_gate_v1"

SUCCESSOR_AVAILABILITY_VALUES = (
    "tracked",
    "pending_commit",
    "not_materialized",
    "redesign_pending",
)


@dataclass(frozen=True)
class LegacyStageRetirementPolicy:
    stage: str
    legacy_stage_retired: bool
    legacy_stage_executable: bool

    superseded_by_stage: str | None
    superseded_by_manifest_path: str | None
    successor_availability: str

    historical_artifacts_read_only: bool
    legacy_artifact_regeneration_forbidden: bool

    ready_for_training: bool
    ready_to_train_now: bool
    feature_semantics_audit_required_before_training: bool

    recommended_next_step: str
    blocking_reasons: tuple[str, ...]


class LegacyStageRetiredError(RuntimeError):
    def __init__(self, policy: LegacyStageRetirementPolicy) -> None:
        self.stage = policy.stage
        self.superseded_by_stage = policy.superseded_by_stage
        self.successor_availability = policy.successor_availability
        self.recommended_next_step = policy.recommended_next_step
        self.blocking_reasons = policy.blocking_reasons
        message = (
            f"legacy_stage_retired:{self.stage}:"
            f"superseded_by={self.superseded_by_stage}:"
            f"recommended_next_step={self.recommended_next_step}"
        )
        super().__init__(message)


@dataclass(frozen=True)
class LegacyRetirementValidationResult:
    passed: bool
    blocking_reasons: tuple[str, ...]
    validated_policies: tuple[LegacyStageRetirementPolicy, ...]

    registry_count_passed: bool
    stage_order_passed: bool
    stage_uniqueness_passed: bool
    availability_contract_passed: bool
    successor_contract_passed: bool
    retirement_boundary_passed: bool
    training_boundary_passed: bool


_SAMPLE_INDEX_MATERIALIZATION_MANIFEST = (
    "data/derived/covalent_small/"
    "covapie_sample_index_materialization_smoke_v0/"
    "covapie_sample_index_materialization_smoke_manifest.json"
)
_LEAKAGE_SPLIT_DESIGN_MANIFEST = (
    "data/derived/covalent_small/"
    "covapie_leakage_split_design_gate_v0/"
    "covapie_leakage_split_design_gate_manifest.json"
)
_UNIFIED_LEAKAGE_SPLIT_MANIFEST = (
    "data/derived/covalent_small/"
    "covapie_unified_leakage_split_materialization_smoke_v0/"
    "covapie_unified_leakage_split_materialization_smoke_manifest.json"
)
_FINAL_DATASET_MATERIALIZATION_MANIFEST = (
    "data/derived/covalent_small/"
    "covapie_final_dataset_materialization_smoke_v0/"
    "covapie_final_dataset_materialization_smoke_manifest.json"
)

EXPECTED_SHARED_SUCCESSOR_MANIFEST_REFERENCES = {
    _UNIFIED_LEAKAGE_SPLIT_MANIFEST: (
        "covapie_split_leakage_smoke_v0",
        "covapie_split_leakage_qa_gate_v0",
    )
}

EXPECTED_LEGACY_STAGE_COUNT = 13
EXPECTED_SUCCESSOR_AVAILABILITY_COUNTS = (
    ("tracked", 5),
    ("pending_commit", 0),
    ("not_materialized", 1),
    ("redesign_pending", 7),
)
EXPECTED_TRACKED_SUCCESSOR_REFERENCE_COUNT = 5
EXPECTED_UNIQUE_TRACKED_SUCCESSOR_MANIFEST_COUNT = 4


def _retired_policy(
    *,
    stage: str,
    superseded_by_stage: str | None,
    superseded_by_manifest_path: str | None,
    successor_availability: str,
    recommended_next_step: str,
    blocking_reasons: tuple[str, ...] = ("legacy_stage_superseded",),
) -> LegacyStageRetirementPolicy:
    return LegacyStageRetirementPolicy(
        stage=stage,
        legacy_stage_retired=True,
        legacy_stage_executable=False,
        superseded_by_stage=superseded_by_stage,
        superseded_by_manifest_path=superseded_by_manifest_path,
        successor_availability=successor_availability,
        historical_artifacts_read_only=True,
        legacy_artifact_regeneration_forbidden=True,
        ready_for_training=False,
        ready_to_train_now=False,
        feature_semantics_audit_required_before_training=True,
        recommended_next_step=recommended_next_step,
        blocking_reasons=blocking_reasons,
    )


LEGACY_STAGE_RETIREMENT_REGISTRY = (
    _retired_policy(
        stage="covapie_sample_index_smoke_v0",
        superseded_by_stage="covapie_sample_index_materialization_smoke_v0",
        superseded_by_manifest_path=_SAMPLE_INDEX_MATERIALIZATION_MANIFEST,
        successor_availability="tracked",
        recommended_next_step="covapie_sample_index_materialization_smoke",
    ),
    _retired_policy(
        stage="covapie_split_leakage_design_gate_v0",
        superseded_by_stage="covapie_leakage_split_design_gate_v0",
        superseded_by_manifest_path=_LEAKAGE_SPLIT_DESIGN_MANIFEST,
        successor_availability="tracked",
        recommended_next_step="covapie_leakage_split_design_gate",
    ),
    _retired_policy(
        stage="covapie_split_leakage_smoke_v0",
        superseded_by_stage="covapie_unified_leakage_split_materialization_smoke_v0",
        superseded_by_manifest_path=_UNIFIED_LEAKAGE_SPLIT_MANIFEST,
        successor_availability="tracked",
        recommended_next_step="covapie_unified_leakage_split_materialization_smoke",
    ),
    _retired_policy(
        stage="covapie_split_leakage_qa_gate_v0",
        superseded_by_stage="covapie_unified_leakage_split_materialization_smoke_v0",
        superseded_by_manifest_path=_UNIFIED_LEAKAGE_SPLIT_MANIFEST,
        successor_availability="tracked",
        recommended_next_step="covapie_unified_leakage_split_materialization_smoke",
    ),
    _retired_policy(
        stage="covapie_final_dataset_smoke_v0",
        superseded_by_stage="covapie_final_dataset_materialization_smoke_v0",
        superseded_by_manifest_path=_FINAL_DATASET_MATERIALIZATION_MANIFEST,
        successor_availability="tracked",
        recommended_next_step="covapie_final_dataset_materialization_smoke",
    ),
    _retired_policy(
        stage="covapie_final_dataset_qa_gate_v0",
        superseded_by_stage=CANONICAL_FINAL_DATASET_QA_STAGE,
        superseded_by_manifest_path=None,
        successor_availability="not_materialized",
        recommended_next_step=CANONICAL_FINAL_DATASET_QA_STAGE,
        blocking_reasons=(
            "legacy_stage_superseded",
            "canonical_successor_not_materialized",
        ),
    ),
    *(
        _retired_policy(
            stage=stage,
            superseded_by_stage=None,
            superseded_by_manifest_path=None,
            successor_availability="redesign_pending",
            recommended_next_step=CANONICAL_FINAL_DATASET_QA_STAGE,
            blocking_reasons=(
                "legacy_stage_superseded",
                "dataloader_interface_redesign_pending",
            ),
        )
        for stage in (
            "covapie_dataloader_interface_design_gate_v0",
            "covapie_dataloader_interface_smoke_v0",
            "covapie_dataloader_interface_qa_gate_v0",
        )
    ),
    _retired_policy(
        stage="covapie_dataloader_smoke_design_gate_v0",
        superseded_by_stage=None,
        superseded_by_manifest_path=None,
        successor_availability="redesign_pending",
        recommended_next_step=CANONICAL_FINAL_DATASET_QA_STAGE,
        blocking_reasons=(
            "legacy_stage_superseded",
            "dataloader_interface_redesign_pending",
        ),
    ),
    _retired_policy(
        stage="covapie_metadata_dataloader_smoke_v0",
        superseded_by_stage=None,
        superseded_by_manifest_path=None,
        successor_availability="redesign_pending",
        recommended_next_step=CANONICAL_FINAL_DATASET_QA_STAGE,
        blocking_reasons=(
            "legacy_stage_superseded",
            "dataloader_interface_redesign_pending",
        ),
    ),
    _retired_policy(
        stage="covapie_metadata_dataloader_smoke_qa_gate_v0",
        superseded_by_stage=None,
        superseded_by_manifest_path=None,
        successor_availability="redesign_pending",
        recommended_next_step=CANONICAL_FINAL_DATASET_QA_STAGE,
        blocking_reasons=(
            "legacy_stage_superseded",
            "dataloader_interface_redesign_pending",
        ),
    ),
    _retired_policy(
        stage="covapie_actual_dataloader_design_gate_v0",
        superseded_by_stage=None,
        superseded_by_manifest_path=None,
        successor_availability="redesign_pending",
        recommended_next_step=CANONICAL_FINAL_DATASET_QA_STAGE,
        blocking_reasons=(
            "legacy_stage_superseded",
            "dataloader_interface_redesign_pending",
        ),
    ),
)

LEGACY_STAGE_ORDER = tuple(
    policy.stage for policy in LEGACY_STAGE_RETIREMENT_REGISTRY
)
_EXPECTED_POLICY_BY_STAGE = {
    policy.stage: policy for policy in LEGACY_STAGE_RETIREMENT_REGISTRY
}


def build_legacy_stage_retirement_policy(
    stage: str,
) -> LegacyStageRetirementPolicy:
    try:
        policy = _EXPECTED_POLICY_BY_STAGE[stage]
    except KeyError:
        raise KeyError(stage) from None
    return replace(policy)


def raise_legacy_stage_retired(stage: str) -> NoReturn:
    raise LegacyStageRetiredError(build_legacy_stage_retirement_policy(stage))


def build_all_legacy_stage_retirement_policies(
) -> tuple[LegacyStageRetirementPolicy, ...]:
    return tuple(
        build_legacy_stage_retirement_policy(stage) for stage in LEGACY_STAGE_ORDER
    )


def _blocking_reasons_are_valid(policy: LegacyStageRetirementPolicy) -> bool:
    reasons = policy.blocking_reasons
    return (
        bool(reasons)
        and reasons[0] == "legacy_stage_superseded"
        and len(reasons) == len(set(reasons))
    )


def _availability_shape_is_valid(policy: LegacyStageRetirementPolicy) -> bool:
    availability = policy.successor_availability
    if availability in {"tracked", "pending_commit"}:
        return bool(policy.superseded_by_stage) and bool(
            policy.superseded_by_manifest_path
        )
    if availability == "not_materialized":
        return (
            bool(policy.superseded_by_stage)
            and policy.superseded_by_manifest_path is None
            and "canonical_successor_not_materialized" in policy.blocking_reasons
        )
    if availability == "redesign_pending":
        return (
            policy.superseded_by_stage is None
            and policy.superseded_by_manifest_path is None
            and "dataloader_interface_redesign_pending" in policy.blocking_reasons
        )
    return False


def validate_legacy_pipeline_retirement_registry(
    policies: Iterable[LegacyStageRetirementPolicy],
) -> LegacyRetirementValidationResult:
    validated = tuple(policies)
    stages = tuple(policy.stage for policy in validated)

    registry_count_passed = len(validated) == EXPECTED_LEGACY_STAGE_COUNT
    stage_order_passed = stages == LEGACY_STAGE_ORDER
    stage_uniqueness_passed = len(stages) == len(set(stages))
    availability_contract_passed = all(
        policy.successor_availability in SUCCESSOR_AVAILABILITY_VALUES
        for policy in validated
    ) and tuple(
        policy.successor_availability for policy in validated
    ) == tuple(
        policy.successor_availability
        for policy in LEGACY_STAGE_RETIREMENT_REGISTRY
    )

    successor_contract_passed = all(
        _availability_shape_is_valid(policy)
        and bool(policy.recommended_next_step)
        and policy.stage in _EXPECTED_POLICY_BY_STAGE
        and (
            policy.superseded_by_stage,
            policy.superseded_by_manifest_path,
            policy.successor_availability,
            policy.recommended_next_step,
            policy.blocking_reasons,
        )
        == (
            _EXPECTED_POLICY_BY_STAGE[policy.stage].superseded_by_stage,
            _EXPECTED_POLICY_BY_STAGE[policy.stage].superseded_by_manifest_path,
            _EXPECTED_POLICY_BY_STAGE[policy.stage].successor_availability,
            _EXPECTED_POLICY_BY_STAGE[policy.stage].recommended_next_step,
            _EXPECTED_POLICY_BY_STAGE[policy.stage].blocking_reasons,
        )
        for policy in validated
    )
    retirement_boundary_passed = all(
        policy.legacy_stage_retired is True
        and policy.legacy_stage_executable is False
        and policy.historical_artifacts_read_only is True
        and policy.legacy_artifact_regeneration_forbidden is True
        and bool(policy.recommended_next_step)
        and _blocking_reasons_are_valid(policy)
        for policy in validated
    )
    training_boundary_passed = all(
        policy.ready_for_training is False
        and policy.ready_to_train_now is False
        and policy.feature_semantics_audit_required_before_training is True
        for policy in validated
    )

    checks = (
        ("registry_count_invalid", registry_count_passed),
        ("stage_order_invalid", stage_order_passed),
        ("stage_uniqueness_invalid", stage_uniqueness_passed),
        ("availability_contract_invalid", availability_contract_passed),
        ("successor_contract_invalid", successor_contract_passed),
        ("retirement_boundary_invalid", retirement_boundary_passed),
        ("training_boundary_invalid", training_boundary_passed),
    )
    blocking_reasons = tuple(reason for reason, passed in checks if not passed)
    return LegacyRetirementValidationResult(
        passed=not blocking_reasons,
        blocking_reasons=blocking_reasons,
        validated_policies=tuple(replace(policy) for policy in validated),
        registry_count_passed=registry_count_passed,
        stage_order_passed=stage_order_passed,
        stage_uniqueness_passed=stage_uniqueness_passed,
        availability_contract_passed=availability_contract_passed,
        successor_contract_passed=successor_contract_passed,
        retirement_boundary_passed=retirement_boundary_passed,
        training_boundary_passed=training_boundary_passed,
    )


def validate_tracked_successor_manifest_paths(
    policies: Iterable[LegacyStageRetirementPolicy],
    *,
    repo_root: str | Path,
) -> dict[str, Any]:
    tracked = tuple(
        policy
        for policy in policies
        if policy.successor_availability == "tracked"
    )
    root = Path(repo_root).resolve()
    derived_root = (root / "data/derived/covalent_small").resolve()
    raw_root = (root / "data/raw").resolve()
    validated_reference_count = 0
    normalized_path_stages: dict[str, list[str]] = {}
    validated_regular_paths: set[Path] = set()
    blocking_reasons: list[str] = []

    for policy in tracked:
        raw_path = policy.superseded_by_manifest_path
        reason_prefix = policy.stage
        if not raw_path:
            blocking_reasons.append(f"{reason_prefix}:manifest_path_missing")
            continue
        relative = Path(raw_path)
        if relative.is_absolute():
            blocking_reasons.append(f"{reason_prefix}:manifest_path_not_relative")
            continue
        if ".." in relative.parts:
            blocking_reasons.append(f"{reason_prefix}:manifest_path_has_parent_reference")
            continue

        normalized_path = relative.as_posix()
        normalized_path_stages.setdefault(normalized_path, []).append(policy.stage)

        candidate = root / relative
        resolved = candidate.resolve()
        if not resolved.is_relative_to(root):
            blocking_reasons.append(f"{reason_prefix}:manifest_path_outside_repo")
            continue
        if not resolved.is_relative_to(derived_root):
            blocking_reasons.append(f"{reason_prefix}:manifest_path_outside_derived_root")
            continue
        if resolved.is_relative_to(raw_root):
            blocking_reasons.append(f"{reason_prefix}:manifest_path_under_raw")
            continue
        if candidate.is_symlink():
            blocking_reasons.append(f"{reason_prefix}:manifest_path_is_symlink")
            continue
        if not candidate.exists():
            blocking_reasons.append(f"{reason_prefix}:manifest_path_missing")
            continue
        if not candidate.is_file():
            blocking_reasons.append(f"{reason_prefix}:manifest_path_not_regular_file")
            continue
        validated_reference_count += 1
        validated_regular_paths.add(resolved)

    tracked_successor_reference_count = len(tracked)
    unique_manifest_path_count = len(normalized_path_stages)
    unique_regular_file_count = len(validated_regular_paths)
    shared_references = {
        path: tuple(stages)
        for path, stages in normalized_path_stages.items()
        if len(stages) > 1
    }
    shared_manifest_reference_count = len(shared_references)

    shared_contract_passed = True
    for path, stages in shared_references.items():
        if path not in EXPECTED_SHARED_SUCCESSOR_MANIFEST_REFERENCES:
            blocking_reasons.append(
                f"tracked_successor_unexpected_shared_manifest:{path}"
            )
            shared_contract_passed = False
            continue
        if set(stages) != set(EXPECTED_SHARED_SUCCESSOR_MANIFEST_REFERENCES[path]):
            blocking_reasons.append(
                f"tracked_successor_shared_stage_set_mismatch:{path}"
            )
            shared_contract_passed = False
    for path, expected_stages in EXPECTED_SHARED_SUCCESSOR_MANIFEST_REFERENCES.items():
        if set(normalized_path_stages.get(path, ())) != set(expected_stages):
            reason = f"tracked_successor_shared_stage_set_mismatch:{path}"
            if reason not in blocking_reasons:
                blocking_reasons.append(reason)
            shared_contract_passed = False

    reference_count_passed = (
        tracked_successor_reference_count
        == EXPECTED_TRACKED_SUCCESSOR_REFERENCE_COUNT
    )
    validated_reference_count_passed = (
        validated_reference_count == EXPECTED_TRACKED_SUCCESSOR_REFERENCE_COUNT
    )
    unique_manifest_path_count_passed = (
        unique_manifest_path_count
        == EXPECTED_UNIQUE_TRACKED_SUCCESSOR_MANIFEST_COUNT
    )
    unique_regular_file_count_passed = (
        unique_regular_file_count
        == EXPECTED_UNIQUE_TRACKED_SUCCESSOR_MANIFEST_COUNT
    )
    shared_manifest_reference_count_passed = (
        shared_manifest_reference_count
        == len(EXPECTED_SHARED_SUCCESSOR_MANIFEST_REFERENCES)
    )

    if not reference_count_passed:
        blocking_reasons.append("tracked_successor_reference_count_mismatch")
    if not validated_reference_count_passed:
        blocking_reasons.append(
            "tracked_successor_validated_reference_count_mismatch"
        )
    if not unique_manifest_path_count_passed:
        blocking_reasons.append("tracked_successor_unique_path_count_mismatch")
    if not unique_regular_file_count_passed:
        blocking_reasons.append(
            "tracked_successor_unique_regular_file_count_mismatch"
        )
    if not shared_manifest_reference_count_passed:
        blocking_reasons.append(
            "tracked_successor_shared_manifest_reference_count_mismatch"
        )

    passed = (
        reference_count_passed
        and validated_reference_count_passed
        and unique_manifest_path_count_passed
        and unique_regular_file_count_passed
        and shared_manifest_reference_count_passed
        and shared_contract_passed
        and not blocking_reasons
    )
    return {
        "tracked_successor_paths_passed": passed,
        "tracked_successor_reference_count": tracked_successor_reference_count,
        "validated_reference_count": validated_reference_count,
        "unique_manifest_path_count": unique_manifest_path_count,
        "unique_regular_file_count": unique_regular_file_count,
        "shared_manifest_reference_count": shared_manifest_reference_count,
        "shared_manifest_reference_contract_passed": shared_contract_passed,
        "blocking_reasons": tuple(blocking_reasons),
    }
