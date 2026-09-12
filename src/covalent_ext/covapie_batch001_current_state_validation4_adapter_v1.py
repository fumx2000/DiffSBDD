"""Default-off CPU validation4 adapter for a caller-owned Batch001 model.

Preparation resolves the real validation4 population and task slices without
constructing a model.  Execution accepts only the already-existing current
bounded-training model, never loads a checkpoint, and reuses the published
validation4 evaluator's scientific helpers.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import asdict, dataclass, fields, is_dataclass
import hashlib
import json
import math
from pathlib import Path
import stat
import time
from typing import Callable, Mapping, NoReturn, Sequence

import torch
from torch import nn

from covalent_ext import (
    covapie_batch001_13event_model_usable_split_materialization_and_activation_boundary_v1
    as activation_owner,
)
from covalent_ext import (
    covapie_batch001_bounded_training_session_v1 as bounded_owner,
)
from covalent_ext import (
    covapie_current11_auxiliary_model_and_loss_v1 as current_loss_owner,
)
from covalent_ext import (
    covapie_current11_formal_validation4_masked_vlb_nll_v1
    as published_evaluator,
)
from covalent_ext import (
    covapie_current11_training_lightning_module_v1 as current_training_owner,
)
from covalent_ext import covapie_current11_training_tensorizer_v1 as tensorizer_owner


__all__ = (
    "COVAPIE_BATCH001_CURRENT_STATE_VALIDATION4_ADAPTER_ERROR_V1",
    "TASK_ID_V1",
    "VALIDATION_MODEL_WEIGHT_SOURCE_V1",
    "PRIMARY_METRIC_NAME_V1",
    "CANONICAL_MASK_CONTRACT_V1",
    "CURRENT_BOUND_SOURCE_AND_ARTIFACT_SHA256_V1",
    "CovapieBatch001CurrentValidationSourceBindingV1",
    "CovapieBatch001Validation4TaskPlanV1",
    "CovapieBatch001CurrentStateValidation4PrepareSummaryV1",
    "CovapieBatch001PreparedCurrentStateValidation4V1",
    "CovapieBatch001CurrentStateValidation4ResultV1",
    "verify_covapie_batch001_current_state_validation4_sources_v1",
    "prepare_covapie_batch001_current_state_validation4_v1",
    "evaluate_covapie_batch001_current_state_validation4_v1",
    "serialize_covapie_batch001_current_state_validation4_prepare_v1",
    "main",
)


COVAPIE_BATCH001_CURRENT_STATE_VALIDATION4_ADAPTER_ERROR_V1 = (
    "COVAPIE_BATCH001_CURRENT_STATE_VALIDATION4_ADAPTER_V1_ERROR"
)
TASK_ID_V1 = "implement_covapie_batch001_current_state_validation4_adapter_v1"
VALIDATION_MODEL_WEIGHT_SOURCE_V1 = "CURRENT_CALLER_MODEL_STATE"
PRIMARY_METRIC_NAME_V1 = "MASKED_CONDITIONAL_VLB_NLL_V1"
MODEL_STATE_TRAINING_PROVENANCE_V1 = (
    "UNPROVEN_CURRENT_CALLER_MODEL_STATE_NOT_HISTORICAL_OUTPUT644_RECOVERY"
)
NODE_PRIOR_SOURCE_V1 = "CURRENT_CALLER_MODEL_CONFIG_SIZE_DISTRIBUTION"
VALIDATION_CONTEXT_SEED_V1 = 785270185393261049
CANONICAL_MASK_CONTRACT_V1 = (
    (0, "warhead_only", "A"),
    (1, "linker_plus_warhead", "B"),
    (2, "scaffold_plus_warhead", "B2"),
    (3, "scaffold_only", "B3"),
    (4, "scaffold_plus_linker_plus_warhead", "C"),
)

_DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_CACHE_ROOT = (
    _DEFAULT_REPOSITORY_ROOT.parent
    / "covapie-state/bulk-multisource-cys-sg-v1/rcsb"
)
_PATH_TYPE = type(Path())

# Current route owners are explicit fixed expectations.  The published
# evaluator and activation owner are themselves pinned here; their fixed
# predecessor inventories are then merged below, with the two obsolete
# training/loss pins replaced by the current values.
_CURRENT_DIRECT_SOURCE_SHA256_V1 = (
    (
        "src/covalent_ext/covapie_batch001_bounded_training_session_v1.py",
        "f38c3f88822723e44fb55b31a60d0ec1a34236553c71b7e87ecdadd9f7ce3620",
    ),
    (
        "src/covalent_ext/covapie_batch001_hidden_post_forward_adapter_v1.py",
        "a1830928e1784214980ae0c8bdad761802dd46c055c7335be0e7ee31005cd971",
    ),
    (
        "src/covalent_ext/covapie_batch001_feature_post_use_preflight_v1.py",
        "9e91e119a63867e7eda4ac76e0e8080ec774b2ee66e6b2ed8b4f4d9b07a6bf7c",
    ),
    (
        "src/covalent_ext/"
        "covapie_batch001_13event_model_usable_split_materialization_and_"
        "activation_boundary_v1.py",
        "e57d2b8d75cf53cb37992a33e8e41a4075dbf94422243ad6686197722d1b48f7",
    ),
    (
        "src/covalent_ext/"
        "covapie_current11_formal_validation4_masked_vlb_nll_v1.py",
        "3f53e1bb668dfe5751f154793ba0d4e1f1001e9619f7a8613b7df31b522be755",
    ),
    (
        "src/covalent_ext/covapie_current11_training_lightning_module_v1.py",
        "a61041ef44e79c0622645965461bf4cc0275e5f3bec9a756fcf7d36a4c9c391b",
    ),
    (
        "src/covalent_ext/covapie_current11_auxiliary_model_and_loss_v1.py",
        "bb797fdb0c96ce669a348a3ddf3975771398263cdfa2a22f3d9c55b0011271cd",
    ),
)
_CURRENT_SOURCE_OVERRIDES_V1 = dict(_CURRENT_DIRECT_SOURCE_SHA256_V1)


def _merged_fixed_bindings_v1() -> tuple[tuple[str, str], ...]:
    values: list[tuple[str, str]] = list(_CURRENT_DIRECT_SOURCE_SHA256_V1)
    by_path = dict(values)
    predecessor_values = tuple(
        (relative, digest)
        for relative, digest in published_evaluator.BOUND_SOURCE_AND_ARTIFACT_SHA256_V1
        if relative not in _CURRENT_SOURCE_OVERRIDES_V1
    )
    activation_values = tuple(
        (relative, digest)
        for _category, relative, digest, _purpose
        in activation_owner._SOURCE_BINDING_SPECS_V1
    )
    for relative, digest in predecessor_values + activation_values:
        previous = by_path.get(relative)
        if previous is not None:
            if previous != digest:
                raise RuntimeError("CONFLICTING_FIXED_SOURCE_BINDING")
            continue
        values.append((relative, digest))
        by_path[relative] = digest
    return tuple(values)


CURRENT_BOUND_SOURCE_AND_ARTIFACT_SHA256_V1 = _merged_fixed_bindings_v1()

# AST identities bind the exact helper bodies actually reused.  In particular,
# they distinguish the current anchor-visibility semantics from the old
# training/loss source versions without treating a same-named function as
# sufficient evidence.
_BOUND_HELPER_AST_SHA256_V1 = (
    (
        "src/covalent_ext/covapie_current11_training_lightning_module_v1.py",
        "run_covapie_current11_functional_dynamics_with_hidden_v1",
        "f962e5cb45216c4b110c22da7c97691e4edca9db895703d862480c95772a8d4c",
    ),
    (
        "src/covalent_ext/covapie_current11_auxiliary_model_and_loss_v1.py",
        "CovapieCurrent11AuxiliaryModelV1.encode_role_mask_anchor_v1",
        "91d0e3eea0235e9c63f151c9f6eb1ed7df605bafc625d5070105ead6f7d3c6b5",
    ),
    (
        "src/covalent_ext/covapie_current11_auxiliary_model_and_loss_v1.py",
        "CovapieCurrent11AuxiliaryModelV1.forward",
        "ad92d0702e3b8515caedc5014bd5246a56613fded7e2acc5516dcb89bc6322cd",
    ),
    (
        "src/covalent_ext/"
        "covapie_current11_formal_validation4_masked_vlb_nll_v1.py",
        "_audit_formal_authority",
        "c36860b677b6f550923c5d0640a665d0843291627f7e235d85695ba4bc0e6af7",
    ),
    (
        "src/covalent_ext/"
        "covapie_current11_formal_validation4_masked_vlb_nll_v1.py",
        "_task_batches",
        "a22bf7cd4b383d60c4255acc234cf7628878b17a8e91cf0ebad02ee0c9513949",
    ),
    (
        "src/covalent_ext/"
        "covapie_current11_formal_validation4_masked_vlb_nll_v1.py",
        "_evaluate_slice",
        "ab86f54ee0deef50afb14912f3c33cd317f76627866c1ea30af609db651fb425",
    ),
    (
        "src/covalent_ext/"
        "covapie_current11_formal_validation4_masked_vlb_nll_v1.py",
        "_aggregate",
        "fcea608ffa3595e542cf66485b16e1e3aae1f2ddf5fb0eabc99c2f248878196b",
    ),
    (
        "src/covalent_ext/"
        "covapie_current11_formal_validation4_masked_vlb_nll_v1.py",
        "_deterministic_cpu_context",
        "dc439993b22b9d406e4aa13694a49f1c82353da3e76148d32b4a5353aee80038",
    ),
)


@dataclass(frozen=True)
class CovapieBatch001CurrentValidationSourceBindingV1:
    relative_path: str
    expected_sha256: str
    observed_sha256: str
    sha256_verified: bool


@dataclass(frozen=True)
class CovapieBatch001Validation4TaskPlanV1:
    canonical_task_id: int
    canonical_task_name: str
    canonical_task_alias: str
    canonical_event_ids: tuple[str, ...]
    event_count: int
    root_seed_count: int
    planned_task_seed_slice_count: int
    planned_estimate_count: int
    planned_main_dynamics_call_count: int
    planned_t0_dynamics_call_count: int
    all_training_masks_closed: bool


@dataclass(frozen=True)
class CovapieBatch001CurrentStateValidation4PrepareSummaryV1:
    schema_version: str
    task_id: str
    implementation_status: str
    primary_metric_name: str
    validation_model_weight_source: str
    source_bindings: tuple[CovapieBatch001CurrentValidationSourceBindingV1, ...]
    helper_ast_bindings_verified: bool
    current_training_loss_compatibility: tuple[str, ...]
    formal_validation_event_ids: tuple[str, ...]
    formal_train_event_ids: tuple[str, ...]
    formal_test_event_ids: tuple[str, ...]
    validation_ligand_components: tuple[str, ...]
    profile_task_matrix: tuple[tuple[str, tuple[int, ...]], ...]
    task_plans: tuple[CovapieBatch001Validation4TaskPlanV1, ...]
    root_validation_seeds: tuple[int, ...]
    planned_event_count: int
    planned_event_task_combination_count: int
    planned_event_task_seed_estimate_count: int
    planned_task_seed_slice_count: int
    planned_main_dynamics_call_count: int
    planned_t0_dynamics_call_count: int
    planned_total_dynamics_call_count: int
    actual_model_evaluation_count: int
    actual_main_dynamics_call_count: int
    actual_t0_dynamics_call_count: int
    exact_validation4_identity_verified: bool
    train_validation_test_event_intersections_zero: bool
    formal_leakage_group_cross_split_violation_count: int
    validation_training_admission_closed: bool
    validation_training_loss_masks_closed: bool
    labels_retained_for_evaluation: bool
    test_model_input_constructed: bool
    checkpoint_loaded: bool
    model_constructed: bool
    shadow_model_constructed: bool
    optimizer_created: bool
    Trainer_created: bool
    model_evaluation_executed: bool
    backward_executed: bool
    parameter_update_performed: bool
    formal_validation_runtime_validated: bool
    train_validation_lifecycle_integrated: bool
    ready_for_training: bool
    feature_semantics_audit_required_later: bool
    step12d_is_only_smoke_legality_check: bool


@dataclass(frozen=True)
class CovapieBatch001PreparedCurrentStateValidation4V1:
    summary: CovapieBatch001CurrentStateValidation4PrepareSummaryV1
    authority: activation_owner.CovapieBatch001FormalSplitAuthorityV1
    validation_carrier: activation_owner.CovapieBatch001ModelUsableSplitBatchV1
    task_batches: tuple[tuple[int, object], ...]
    leakage_by_event: Mapping[str, str]
    record_by_event: Mapping[str, object]


@dataclass(frozen=True)
class CovapieBatch001CurrentStateValidation4ResultV1:
    implementation_status: str
    metric_evidence_kind: str
    primary_metric_name: str
    validation_model_weight_source: str
    caller_model_stage: str
    caller_stage_evidence: str
    caller_quiescence_asserted: bool
    model_training_provenance_status: str
    historical_output644_model_state_recovered: bool
    source_model_identity: str
    source_model_state_sha256_before: str
    source_model_state_sha256_after: str
    current_node_prior_source: str
    current_node_distribution_sha256_before: str
    current_node_distribution_sha256_after: str
    current_node_distribution_verified: bool
    formal_validation_event_ids: tuple[str, ...]
    root_validation_seeds: tuple[int, ...]
    formal_validation_event_count: int
    formal_validation_task_event_count: int
    formal_validation_estimate_count: int
    formal_validation_task_slice_evaluation_count: int
    main_dynamics_task_slice_call_count: int
    t0_dynamics_task_slice_call_count: int
    total_dynamics_task_slice_call_count: int
    per_estimate_rows: tuple[published_evaluator.FormalValidationEstimateV1, ...]
    per_event_task_seed_means: tuple[
        published_evaluator.FormalValidationEventTaskMeanV1, ...
    ]
    per_event_means: tuple[published_evaluator.FormalValidationEventMeanV1, ...]
    event_macro_masked_conditional_vlb_nll: float
    micro_masked_conditional_vlb_nll: float
    profile_means: tuple[tuple[str, float], ...]
    profile_balanced_masked_conditional_vlb_nll: float
    mean_pair_BCE: float
    mean_POST_geometry_loss: float
    mean_POST_geometry_prediction_angstrom: float
    mean_POST_geometry_target_angstrom: float
    mean_pair_contrastive_loss: float
    mean_task4_historical_joint_nll_with_node_prior_diagnostic: float
    primary_node_prior_included: bool
    source_parameters_unchanged: bool
    source_buffers_unchanged: bool
    source_gradients_unchanged: bool
    source_requires_grad_unchanged: bool
    source_parameter_identities_unchanged: bool
    source_buffer_identities_unchanged: bool
    source_module_identities_unchanged: bool
    source_state_keys_unchanged: bool
    source_configuration_unchanged: bool
    evaluation_carriers_unchanged: bool
    source_training_flags_restored: bool
    CPU_rng_restored: bool
    CPU_determinism_settings_restored: bool
    no_new_parameter_module_or_state_key: bool
    metric_tensors_require_grad: bool
    all_validation_rows_finite: bool
    checkpoint_loaded_inside_validation: bool
    shadow_model_constructed: bool
    optimizer_created: bool
    Trainer_used: bool
    backward_performed: bool
    parameter_update_performed: bool
    runtime_elapsed_seconds: float


@dataclass(frozen=True)
class _ModelStateSnapshotV1:
    model_state_sha256: str
    parameter_entries: tuple[tuple[str, int, bool, str], ...]
    buffer_entries: tuple[tuple[str, int, str], ...]
    gradient_entries: tuple[tuple[str, int | None, str | None], ...]
    module_entries: tuple[tuple[str, int], ...]
    state_keys: tuple[str, ...]
    training_flags: tuple[tuple[str, int, bool], ...]
    configuration_sha256: str
    node_distribution_identity: int | None
    node_distribution_sha256: str


@dataclass(frozen=True)
class _GuardedSliceCollectionV1:
    estimates: tuple[published_evaluator.FormalValidationEstimateV1, ...]
    main_calls: int
    t0_calls: int
    fixed_clean: bool
    indicator_reused: bool
    tensors_require_grad: bool
    before: _ModelStateSnapshotV1
    after: _ModelStateSnapshotV1
    parameters_unchanged: bool
    buffers_unchanged: bool
    gradients_unchanged: bool
    requires_grad_unchanged: bool
    parameter_identities_unchanged: bool
    buffer_identities_unchanged: bool
    module_identities_unchanged: bool
    state_keys_unchanged: bool
    configuration_unchanged: bool
    node_distribution_unchanged: bool
    training_flags_restored: bool
    carriers_unchanged: bool
    CPU_rng_restored: bool
    CPU_determinism_settings_restored: bool
    evidence_kind: str


class _AdapterInvariantError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _fail(reason: str) -> NoReturn:
    raise _AdapterInvariantError(reason)


def _public_error(error: BaseException) -> NoReturn:
    if type(error) is ValueError and str(error).startswith(
        COVAPIE_BATCH001_CURRENT_STATE_VALIDATION4_ADAPTER_ERROR_V1
    ):
        raise error
    reason = error.reason if isinstance(error, _AdapterInvariantError) else "OWNER_REJECTED"
    raise ValueError(
        f"{COVAPIE_BATCH001_CURRENT_STATE_VALIDATION4_ADAPTER_ERROR_V1}:{reason}"
    ) from error


def _require_directory(value: object, *, default: Path, reason: str) -> Path:
    path = default if value is None else value
    if type(path) is not _PATH_TYPE or not path.is_absolute():
        _fail(reason)
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise _AdapterInvariantError(reason) from error
    if resolved != path or path.is_symlink() or not path.is_dir():
        _fail(reason)
    return path


def _sha256_file(path: Path) -> str:
    try:
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            _fail("BOUND_FILE_NOT_SAFE_REGULAR_FILE")
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError as error:
        raise _AdapterInvariantError("BOUND_FILE_READ_FAILED") from error


def _qualified_ast_node(tree: ast.Module, qualified_name: str) -> ast.AST:
    nodes: Sequence[ast.stmt] = tree.body
    found: ast.AST | None = None
    for part in qualified_name.split("."):
        found = next(
            (
                node
                for node in nodes
                if isinstance(
                    node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                )
                and node.name == part
            ),
            None,
        )
        if found is None:
            _fail("BOUND_HELPER_AST_NODE_MISSING:" + qualified_name)
        nodes = found.body
    return found


def _verify_helper_ast_bindings_v1(repository_root: Path) -> None:
    for relative, qualified_name, expected in _BOUND_HELPER_AST_SHA256_V1:
        try:
            tree = ast.parse((repository_root / relative).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, SyntaxError) as error:
            raise _AdapterInvariantError("BOUND_HELPER_SOURCE_INVALID") from error
        node = _qualified_ast_node(tree, qualified_name)
        payload = ast.dump(
            node, annotate_fields=True, include_attributes=False
        ).encode("utf-8")
        if hashlib.sha256(payload).hexdigest() != expected:
            _fail("BOUND_HELPER_AST_SHA256_MISMATCH:" + qualified_name)
    evaluator_tree = ast.parse(
        (
            repository_root
            / "src/covalent_ext/"
            "covapie_current11_formal_validation4_masked_vlb_nll_v1.py"
        ).read_text(encoding="utf-8")
    )
    evaluate_node = _qualified_ast_node(evaluator_tree, "_evaluate_slice")
    calls = tuple(
        node.func.id
        for node in ast.walk(evaluate_node)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    )
    if (
        calls.count("run_covapie_current11_functional_dynamics_with_hidden_v1")
        != 2
        or "compute_covapie_current11_training_losses_v1" in calls
    ):
        _fail("PUBLISHED_EVALUATION_ROUTE_SEMANTICS_INVALID")
    if (
        published_evaluator.run_covapie_current11_functional_dynamics_with_hidden_v1
        is not current_training_owner.run_covapie_current11_functional_dynamics_with_hidden_v1
        or published_evaluator.CovapieCurrent11AuxiliaryModelV1
        is not current_loss_owner.CovapieCurrent11AuxiliaryModelV1
    ):
        _fail("CURRENT_HELPER_IMPORT_IDENTITY_INVALID")


def verify_covapie_batch001_current_state_validation4_sources_v1(
    *, repository_root: object = None
) -> tuple[CovapieBatch001CurrentValidationSourceBindingV1, ...]:
    """Verify the fixed current route plus preserved structural/artifact pins."""

    try:
        repository = _require_directory(
            repository_root,
            default=_DEFAULT_REPOSITORY_ROOT,
            reason="REPOSITORY_ROOT_INVALID",
        )
        bindings = []
        for relative, expected in CURRENT_BOUND_SOURCE_AND_ARTIFACT_SHA256_V1:
            actual = _sha256_file(repository / relative)
            if actual != expected:
                _fail("CURRENT_SOURCE_SHA256_MISMATCH:" + relative)
            bindings.append(CovapieBatch001CurrentValidationSourceBindingV1(
                relative_path=relative,
                expected_sha256=expected,
                observed_sha256=actual,
                sha256_verified=True,
            ))
        # These successor gates add semantic checks beyond byte identity.
        activation_owner.verify_covapie_batch001_model_usable_source_bindings_v1(
            repository_root=repository
        )
        bounded_owner.verify_covapie_batch001_bounded_training_session_sources_v1(
            repository_root=repository
        )
        bounded_owner._validate_model_routing_v1()
        _verify_helper_ast_bindings_v1(repository)
        observed_contract = tuple(
            (int(row[0]), str(row[1]), str(row[2]))
            for row in tensorizer_owner.CANONICAL_TASKS_V1
        )
        if (
            observed_contract != CANONICAL_MASK_CONTRACT_V1
            or bounded_owner.CANONICAL_MASK_CONTRACT_V1
            != CANONICAL_MASK_CONTRACT_V1
            or published_evaluator.PRIMARY_METRIC_NAME_V1
            != PRIMARY_METRIC_NAME_V1
        ):
            _fail("CURRENT_METRIC_OR_EXACT5_CONTRACT_DRIFT")
        return tuple(bindings)
    except BaseException as error:
        _public_error(error)


def _training_masks_closed(supervision: object) -> bool:
    return not any(
        bool(getattr(supervision, name).any().item())
        for name in (
            "sample_training_admitted",
            "ligand_active_diffusion_loss_mask",
            "pair_head_candidate_loss_mask",
            "pair_contrastive_sample_loss_mask",
            "pre_post_geometry_component_loss_mask",
        )
    )


def _prepare_impl(
    *,
    repository_root: Path,
    cache_root: Path,
    source_bindings: tuple[CovapieBatch001CurrentValidationSourceBindingV1, ...],
) -> CovapieBatch001PreparedCurrentStateValidation4V1:
    authority = activation_owner.load_covapie_batch001_formal_split_authority_v1(
        repository_root=repository_root
    )
    legacy_authority = published_evaluator._audit_formal_authority(repository_root)
    validation_carrier = (
        activation_owner.build_covapie_batch001_model_usable_split_batch_v1(
            split="validation",
            epoch=0,
            task_schedule_seed=(
                published_evaluator.VALIDATION_TENSORIZATION_SENTINEL_SEED_V1
            ),
            repository_root=repository_root,
            cache_root=cache_root,
        )
    )
    activation_owner.validate_covapie_batch001_model_usable_split_batch_v1(
        validation_carrier, authority=authority
    )
    if (
        authority.validation_event_ids
        != published_evaluator.FORMAL_VALIDATION_EVENT_IDS_V1
        or authority.train_event_ids
        != published_evaluator.FORMAL_TRAIN_EVENT_IDS_V1
        or validation_carrier.sample_identities != authority.validation_event_ids
        or tuple(item[0] for item in legacy_authority.validation_rows)
        != authority.validation_event_ids
        or tuple(item[0] for item in legacy_authority.train_rows)
        != authority.train_event_ids
        or authority.event_identity_intersection_counts
        != (("train_validation", 0), ("train_test", 0), ("validation_test", 0))
        or authority.formal_leakage_group_cross_split_violation_count != 0
    ):
        _fail("CURRENT_AND_PUBLISHED_FORMAL_AUTHORITY_MISMATCH")
    if (
        validation_carrier.formal_split != "validation"
        or validation_carrier.formal_validation_population_member != (True,) * 4
        or validation_carrier.formal_test_population_member != (False,) * 4
        or validation_carrier.sample_training_admitted != (False,) * 4
        or validation_carrier.model_training_activation_authorized != (False,) * 4
        or validation_carrier.optimizer_population_eligible != (False,) * 4
        or validation_carrier.training_scheduler_eligible != (False,) * 4
        or not _training_masks_closed(validation_carrier.supervision)
    ):
        _fail("VALIDATION_CARRIER_ACTIVATION_BOUNDARY_INVALID")
    task_batches = published_evaluator._task_batches(
        validation_carrier.structural_records
    )
    expected_task_events = tuple(
        tuple(
            event_id
            for event_id, tasks in zip(
                validation_carrier.sample_identities,
                validation_carrier.applicable_task_ids,
            )
            if task_id in tasks
        )
        for task_id in range(5)
    )
    plans = []
    for task_id, preview in task_batches:
        task_name, task_alias = CANONICAL_MASK_CONTRACT_V1[task_id][1:]
        if (
            preview.sample_identities != expected_task_events[task_id]
            or preview.canonical_task_ids != (task_id,) * len(preview.sample_identities)
            or not _training_masks_closed(preview.supervision)
        ):
            _fail("VALIDATION_TASK_SLICE_DOMAIN_INVALID")
        plans.append(CovapieBatch001Validation4TaskPlanV1(
            canonical_task_id=task_id,
            canonical_task_name=task_name,
            canonical_task_alias=task_alias,
            canonical_event_ids=preview.sample_identities,
            event_count=len(preview.sample_identities),
            root_seed_count=4,
            planned_task_seed_slice_count=4,
            planned_estimate_count=4 * len(preview.sample_identities),
            planned_main_dynamics_call_count=4,
            planned_t0_dynamics_call_count=4,
            all_training_masks_closed=True,
        ))
    task_plans = tuple(plans)
    if (
        tuple(plan.event_count for plan in task_plans) != (4, 2, 2, 4, 4)
        or sum(plan.event_count for plan in task_plans) != 16
        or sum(plan.planned_estimate_count for plan in task_plans) != 64
    ):
        _fail("VALIDATION_PLAN_COUNTS_INVALID")
    leakage_by_event = {
        event: group for event, _component, group in legacy_authority.validation_rows
    }
    record_by_event = {
        record.canonical_event_id: record
        for record in validation_carrier.structural_records
    }
    labels = validation_carrier.supervision
    labels_retained = (
        bool(labels.canonical_task_valid.all().item())
        and bool(labels.ligand_role_valid.all().item())
        and bool(labels.pair_positive_candidate_valid.all().item())
        and int(labels.pair_candidate_is_positive.sum().item()) == 4
        and labels.pre_post_geometry_component_valid_mask.tolist()
        == [[False, True]] * 4
    )
    if not labels_retained:
        _fail("VALIDATION_EVALUATION_LABELS_NOT_RETAINED")
    summary = CovapieBatch001CurrentStateValidation4PrepareSummaryV1(
        schema_version="covapie_batch001_current_state_validation4_adapter_v1",
        task_id=TASK_ID_V1,
        implementation_status="PREPARED_NOT_EXECUTED",
        primary_metric_name=PRIMARY_METRIC_NAME_V1,
        validation_model_weight_source=VALIDATION_MODEL_WEIGHT_SOURCE_V1,
        source_bindings=source_bindings,
        helper_ast_bindings_verified=True,
        current_training_loss_compatibility=(
            "PINNED_PUBLISHED_VLB_NLL_EQUATIONS_REUSED_UNMODIFIED",
            "CURRENT_FUNCTIONAL_DYNAMICS_HELPER_AST_BOUND",
            "CURRENT_AUXILIARY_AND_FIXED_ONLY_ANCHOR_ENCODING_AST_BOUND",
            "CURRENT_TRAINING_LOSS_NOT_CALLED",
            "HIDDEN_POST_TRAINING_DENOMINATOR_NOT_CLAIMED_BY_DIAGNOSTICS",
        ),
        formal_validation_event_ids=authority.validation_event_ids,
        formal_train_event_ids=authority.train_event_ids,
        formal_test_event_ids=authority.test_event_ids,
        validation_ligand_components=tuple(
            record.ligand_component_id
            for record in validation_carrier.structural_records
        ),
        profile_task_matrix=published_evaluator.PROFILE_TASK_MATRIX_V1,
        task_plans=task_plans,
        root_validation_seeds=(
            published_evaluator.FORMAL_VALIDATION_ROOT_SEEDS_V1
        ),
        planned_event_count=4,
        planned_event_task_combination_count=16,
        planned_event_task_seed_estimate_count=64,
        planned_task_seed_slice_count=20,
        planned_main_dynamics_call_count=20,
        planned_t0_dynamics_call_count=20,
        planned_total_dynamics_call_count=40,
        actual_model_evaluation_count=0,
        actual_main_dynamics_call_count=0,
        actual_t0_dynamics_call_count=0,
        exact_validation4_identity_verified=True,
        train_validation_test_event_intersections_zero=True,
        formal_leakage_group_cross_split_violation_count=0,
        validation_training_admission_closed=True,
        validation_training_loss_masks_closed=True,
        labels_retained_for_evaluation=True,
        test_model_input_constructed=False,
        checkpoint_loaded=False,
        model_constructed=False,
        shadow_model_constructed=False,
        optimizer_created=False,
        Trainer_created=False,
        model_evaluation_executed=False,
        backward_executed=False,
        parameter_update_performed=False,
        formal_validation_runtime_validated=False,
        train_validation_lifecycle_integrated=False,
        ready_for_training=False,
        feature_semantics_audit_required_later=True,
        step12d_is_only_smoke_legality_check=True,
    )
    return CovapieBatch001PreparedCurrentStateValidation4V1(
        summary=summary,
        authority=authority,
        validation_carrier=validation_carrier,
        task_batches=task_batches,
        leakage_by_event=leakage_by_event,
        record_by_event=record_by_event,
    )


def prepare_covapie_batch001_current_state_validation4_v1(
    *, repository_root: object = None, cache_root: object = None
) -> CovapieBatch001PreparedCurrentStateValidation4V1:
    """Prepare real validation4 task slices without constructing a model."""

    try:
        repository = _require_directory(
            repository_root,
            default=_DEFAULT_REPOSITORY_ROOT,
            reason="REPOSITORY_ROOT_INVALID",
        )
        cache = _require_directory(
            cache_root,
            default=_DEFAULT_CACHE_ROOT,
            reason="CACHE_ROOT_INVALID",
        )
        bindings = verify_covapie_batch001_current_state_validation4_sources_v1(
            repository_root=repository
        )
        return _prepare_impl(
            repository_root=repository,
            cache_root=cache,
            source_bindings=bindings,
        )
    except BaseException as error:
        _public_error(error)


def _update_digest_value(digest: "hashlib._Hash", value: object) -> None:
    if isinstance(value, torch.Tensor):
        tensor = value.detach().cpu().contiguous()
        digest.update(b"T")
        digest.update(str(tensor.dtype).encode("ascii"))
        digest.update(repr(tuple(tensor.shape)).encode("ascii"))
        digest.update(tensor.view(torch.uint8).numpy().tobytes())
        return
    if is_dataclass(value):
        digest.update(b"D")
        for field in fields(value):
            digest.update(field.name.encode("utf-8") + b"\0")
            _update_digest_value(digest, getattr(value, field.name))
        return
    if isinstance(value, Mapping):
        digest.update(b"M")
        for key in sorted(value, key=lambda item: str(item)):
            _update_digest_value(digest, str(key))
            _update_digest_value(digest, value[key])
        return
    if type(value) in (tuple, list):
        digest.update(b"Q" if type(value) is tuple else b"L")
        for item in value:
            _update_digest_value(digest, item)
        return
    if isinstance(value, Path):
        value = value.as_posix()
    if value is None or type(value) in (str, bool, int, float):
        digest.update(type(value).__name__.encode("ascii") + b":")
        digest.update(repr(value).encode("utf-8"))
        return
    if hasattr(value, "__dict__") and not isinstance(value, nn.Module):
        digest.update(type(value).__qualname__.encode("utf-8") + b":")
        _update_digest_value(digest, vars(value))
        return
    digest.update(
        (
            type(value).__module__
            + "."
            + type(value).__qualname__
            + ":"
            + str(id(value))
        ).encode("utf-8")
    )


def _value_sha256(value: object) -> str:
    digest = hashlib.sha256()
    _update_digest_value(digest, value)
    return digest.hexdigest()


def _tensor_sha256(value: torch.Tensor) -> str:
    return _value_sha256(value)


def _state_mapping_sha256(values: Mapping[str, torch.Tensor]) -> str:
    return _value_sha256(tuple((name, values[name]) for name in values))


def _hparam_value(model: nn.Module, name: str) -> object:
    hparams = getattr(model, "hparams", None)
    if isinstance(hparams, Mapping):
        return hparams.get(name)
    return getattr(hparams, name, None)


def _node_distribution_snapshot(model: nn.Module) -> tuple[int | None, str]:
    ddpm = getattr(model, "ddpm", None)
    distribution = getattr(ddpm, "size_distribution", None)
    if distribution is None:
        return None, "ABSENT"
    payload = (
        getattr(distribution, "prob", None),
        getattr(distribution, "idx_to_n_nodes", None),
        tuple(sorted(getattr(distribution, "n_nodes_to_idx", {}).items())),
    )
    return id(distribution), _value_sha256(payload)


def _configuration_sha256(model: nn.Module) -> str:
    names = (
        "mode",
        "loss_type",
        "pocket_representation",
        "virtual_nodes",
        "target_residue_atom_conditioning",
        "auxiliary_loss",
        "atom_nf",
        "aa_nf",
        "x_dims",
        "batch_size",
        "lr",
        "automatic_optimization",
        "covapie_current11_training_enabled",
        "covapie_current11_task_schedule_seed",
        "covapie_current11_pair_contrastive_temperature",
        "covapie_current11_authoritative_supervision_batch_field",
        "covapie_batch001_hidden_post_forward_enabled",
    )
    ddpm = getattr(model, "ddpm", None)
    payload = (
        tuple((name, getattr(model, name, None)) for name in names),
        (
            ("T", getattr(ddpm, "T", None)),
            ("n_dims", getattr(ddpm, "n_dims", None)),
            ("loss_type", getattr(ddpm, "loss_type", None)),
            ("norm_values", getattr(ddpm, "norm_values", None)),
            ("norm_biases", getattr(ddpm, "norm_biases", None)),
        ),
        ("loss_weights_id", id(getattr(model, "covapie_current11_loss_weights", None))),
        ("loss_weights", getattr(model, "covapie_current11_loss_weights", None)),
        ("node_histogram", _hparam_value(model, "node_histogram")),
        (
            "carrier_context_identities",
            tuple(
                id(getattr(model, name, None))
                for name in (
                    "_covapie_current11_task2_remap_context_v1",
                    "_covapie_current11_task2_compiler_context_v1",
                    "train_dataset",
                    "val_dataset",
                    "test_dataset",
                )
            ),
        ),
    )
    return _value_sha256(payload)


def _snapshot_model_state_v1(model: nn.Module) -> _ModelStateSnapshotV1:
    parameters = tuple(model.named_parameters())
    buffers = tuple(model.named_buffers())
    state = model.state_dict()
    distribution_id, distribution_sha = _node_distribution_snapshot(model)
    return _ModelStateSnapshotV1(
        model_state_sha256=_state_mapping_sha256(state),
        parameter_entries=tuple(
            (name, id(value), bool(value.requires_grad), _tensor_sha256(value))
            for name, value in parameters
        ),
        buffer_entries=tuple(
            (name, id(value), _tensor_sha256(value)) for name, value in buffers
        ),
        gradient_entries=tuple(
            (
                name,
                None if value.grad is None else id(value.grad),
                None if value.grad is None else _tensor_sha256(value.grad),
            )
            for name, value in parameters
        ),
        module_entries=tuple(
            (name, id(value)) for name, value in model.named_modules()
        ),
        state_keys=tuple(state),
        training_flags=tuple(
            (name, id(value), bool(value.training))
            for name, value in model.named_modules()
        ),
        configuration_sha256=_configuration_sha256(model),
        node_distribution_identity=distribution_id,
        node_distribution_sha256=distribution_sha,
    )


def _carrier_fingerprint(prepared: CovapieBatch001PreparedCurrentStateValidation4V1) -> str:
    return _value_sha256(tuple(
        (
            task_id,
            preview.sample_identities,
            preview.canonical_task_ids,
            preview.model_input_batch,
            preview.supervision,
        )
        for task_id, preview in prepared.task_batches
    ))


def _validate_current_node_distribution_v1(model: nn.Module) -> str:
    histogram = _hparam_value(model, "node_histogram")
    ddpm = getattr(model, "ddpm", None)
    distribution = getattr(ddpm, "size_distribution", None)
    probability = getattr(distribution, "prob", None)
    indices = getattr(distribution, "idx_to_n_nodes", None)
    reverse = getattr(distribution, "n_nodes_to_idx", None)
    if (
        type(histogram) is not list
        or len(histogram) != 107
        or any(type(row) is not list or len(row) != 1671 for row in histogram)
        or not isinstance(probability, torch.Tensor)
        or probability.device.type != "cpu"
        or probability.shape != (107, 1671)
        or not isinstance(indices, torch.Tensor)
        or indices.device.type != "cpu"
        or indices.shape != (107 * 1671, 2)
        or type(reverse) is not dict
        or len(reverse) != 107 * 1671
        or getattr(model, "max_num_nodes", None) != 106
    ):
        _fail("CURRENT_NODE_DISTRIBUTION_DOMAIN_INVALID")
    source = torch.tensor(histogram, dtype=torch.float32)
    if (
        not bool(torch.isfinite(source).all().item())
        or bool((source < 0).any().item())
    ):
        _fail("CURRENT_NODE_HISTOGRAM_INVALID")
    expected = source + 1.0e-3
    expected = expected / expected.sum()
    if (
        not torch.equal(probability, expected)
        or indices[0].tolist() != [0, 0]
        or indices[-1].tolist() != [106, 1670]
        or reverse.get((0, 0)) != 0
        or reverse.get((106, 1670)) != 107 * 1671 - 1
    ):
        _fail("CURRENT_NODE_DISTRIBUTION_NOT_CONFIG_VERIFIED")
    return _node_distribution_snapshot(model)[1]


def _trainer_running(model: nn.Module) -> bool:
    trainer = vars(model).get("_trainer")
    if trainer is None:
        return False
    state = getattr(trainer, "state", None)
    status = str(getattr(state, "status", "")).lower()
    fit_loop = getattr(trainer, "fit_loop", None)
    return "running" in status or bool(getattr(fit_loop, "running", False))


def _validate_caller_metadata(
    *, caller_model_stage: object, caller_stage_evidence: object,
    caller_confirms_model_is_quiescent: object,
) -> tuple[str, str]:
    if (
        type(caller_model_stage) is not str
        or not caller_model_stage
        or len(caller_model_stage) > 128
        or not caller_model_stage.isascii()
        or type(caller_stage_evidence) is not str
        or not caller_stage_evidence
        or len(caller_stage_evidence) > 512
        or caller_confirms_model_is_quiescent is not True
    ):
        _fail("CALLER_STAGE_OR_QUIESCENCE_EVIDENCE_INVALID")
    return caller_model_stage, caller_stage_evidence


def _validate_current_source_model_v1(model: object) -> str:
    expected_type = bounded_owner.CovapieBatch001BoundedTrainingLigandPocketDDPMV1
    if type(model) is not expected_type or not isinstance(model, nn.Module):
        _fail("CURRENT_BOUNDED_MODEL_EXACT_TYPE_REQUIRED")
    if _trainer_running(model):
        _fail("CONCURRENT_TRAINER_FIT_STATE_REJECTED")
    state = model.state_dict()
    if (
        len(state) != 141
        or any(value.device.type != "cpu" for value in state.values())
        or any(parameter.device.type != "cpu" for parameter in model.parameters())
        or any(buffer.device.type != "cpu" for buffer in model.buffers())
        or getattr(model, "mode", None) != "pocket_conditioning"
        or getattr(model, "loss_type", None) != "l2"
        or getattr(model.ddpm, "loss_type", None) != "l2"
        or getattr(model, "pocket_representation", None) != "full-atom"
        or getattr(model, "atom_nf", None) != 10
        or getattr(model, "aa_nf", None) != 10
        or getattr(model, "virtual_nodes", None) is not False
        or getattr(model, "target_residue_atom_conditioning", None) is not True
        or getattr(model, "covapie_current11_training_enabled", None) is not True
        or getattr(model, "covapie_batch001_hidden_post_forward_enabled", None)
        is not True
        or getattr(model, "covapie_current11_loss_weights", None)
        != bounded_owner.DEFAULT_LOSS_WEIGHTS_V1
    ):
        _fail("CURRENT_BOUNDED_MODEL_CONFIGURATION_INVALID")
    return _validate_current_node_distribution_v1(model)


def _state_parity(
    before: _ModelStateSnapshotV1, after: _ModelStateSnapshotV1
) -> tuple[bool, ...]:
    return (
        tuple((name, digest) for name, _identity, _requires, digest in before.parameter_entries)
        == tuple((name, digest) for name, _identity, _requires, digest in after.parameter_entries),
        tuple((name, digest) for name, _identity, digest in before.buffer_entries)
        == tuple((name, digest) for name, _identity, digest in after.buffer_entries),
        before.gradient_entries == after.gradient_entries,
        tuple((name, requires) for name, _identity, requires, _digest in before.parameter_entries)
        == tuple((name, requires) for name, _identity, requires, _digest in after.parameter_entries),
        tuple((name, identity) for name, identity, _requires, _digest in before.parameter_entries)
        == tuple((name, identity) for name, identity, _requires, _digest in after.parameter_entries),
        tuple((name, identity) for name, identity, _digest in before.buffer_entries)
        == tuple((name, identity) for name, identity, _digest in after.buffer_entries),
        before.module_entries == after.module_entries,
        before.state_keys == after.state_keys,
        before.configuration_sha256 == after.configuration_sha256,
        (
            before.node_distribution_identity == after.node_distribution_identity
            and before.node_distribution_sha256 == after.node_distribution_sha256
        ),
        before.training_flags == after.training_flags,
        before.model_state_sha256 == after.model_state_sha256,
    )


def _guarded_slice_collection_v1(
    *,
    source_model: nn.Module,
    prepared: CovapieBatch001PreparedCurrentStateValidation4V1,
    slice_evaluator: Callable[..., object] = published_evaluator._evaluate_slice,
    evidence_kind: str = "MODEL_EXECUTION",
) -> _GuardedSliceCollectionV1:
    """Run slices under reversible mode/RNG guards and non-repairing state audit."""

    if (
        not isinstance(source_model, nn.Module)
        or type(prepared) is not CovapieBatch001PreparedCurrentStateValidation4V1
        or not callable(slice_evaluator)
        or evidence_kind not in {"MODEL_EXECUTION", "SYNTHETIC_TEST_FIXTURE"}
    ):
        _fail("GUARDED_EVALUATION_ARGUMENT_INVALID")
    before = _snapshot_model_state_v1(source_model)
    carrier_before = _carrier_fingerprint(prepared)
    rng_before = torch.random.get_rng_state().clone()
    environment_before = (
        torch.get_num_threads(),
        torch.are_deterministic_algorithms_enabled(),
        torch.is_deterministic_algorithms_warn_only_enabled(),
    )
    original_modules = tuple(
        (name, module, bool(module.training))
        for name, module in source_model.named_modules()
    )
    caught: Exception | None = None
    estimates: list[published_evaluator.FormalValidationEstimateV1] = []
    main_calls = 0
    t0_calls = 0
    fixed_clean = True
    indicator_reused = True
    tensors_require_grad = False
    try:
        with published_evaluator._deterministic_cpu_context():
            torch.random.default_generator.manual_seed(VALIDATION_CONTEXT_SEED_V1)
            source_model.eval()
            if any(module.training for _name, module in source_model.named_modules()):
                _fail("TEMPORARY_EVAL_MODE_ENTRY_FAILED")
            with torch.inference_mode():
                for root_seed in published_evaluator.FORMAL_VALIDATION_ROOT_SEEDS_V1:
                    for task_id, preview in prepared.task_batches:
                        output = slice_evaluator(
                            model=source_model,
                            preview=preview,
                            task_id=task_id,
                            root_seed=root_seed,
                            leakage_by_event=prepared.leakage_by_event,
                            record_by_event=prepared.record_by_event,
                        )
                        if type(output) is not published_evaluator._SliceOutputV1:
                            _fail("SLICE_EVALUATOR_OUTPUT_TYPE_INVALID")
                        estimates.extend(output.estimates)
                        main_calls += output.main_calls
                        t0_calls += output.t0_calls
                        fixed_clean = fixed_clean and output.fixed_clean
                        indicator_reused = (
                            indicator_reused and output.indicator_reused
                        )
                        tensors_require_grad = (
                            tensors_require_grad or output.tensors_require_grad
                        )
                        if any(
                            module.training
                            for _name, module in source_model.named_modules()
                        ):
                            _fail("EVALUATOR_CHANGED_TEMPORARY_EVAL_MODE")
    except Exception as error:
        caught = error
    finally:
        # Restore only reversible mode state.  Weight/buffer/grad/config changes
        # are intentionally not repaired, so the post-audit cannot be masked.
        for _name, module, training in original_modules:
            module.training = training
    after = _snapshot_model_state_v1(source_model)
    carrier_after = _carrier_fingerprint(prepared)
    rng_restored = torch.equal(rng_before, torch.random.get_rng_state())
    environment_restored = environment_before == (
        torch.get_num_threads(),
        torch.are_deterministic_algorithms_enabled(),
        torch.is_deterministic_algorithms_warn_only_enabled(),
    )
    (
        parameters_unchanged,
        buffers_unchanged,
        gradients_unchanged,
        requires_grad_unchanged,
        parameter_identities_unchanged,
        buffer_identities_unchanged,
        module_identities_unchanged,
        state_keys_unchanged,
        configuration_unchanged,
        node_distribution_unchanged,
        training_flags_restored,
        state_mapping_unchanged,
    ) = _state_parity(before, after)
    carriers_unchanged = carrier_before == carrier_after
    state_checks = (
        parameters_unchanged,
        buffers_unchanged,
        gradients_unchanged,
        requires_grad_unchanged,
        parameter_identities_unchanged,
        buffer_identities_unchanged,
        module_identities_unchanged,
        state_keys_unchanged,
        configuration_unchanged,
        node_distribution_unchanged,
        training_flags_restored,
        state_mapping_unchanged,
    )
    if not all(state_checks):
        _fail("SOURCE_MODEL_STATE_MUTATED_DURING_VALIDATION")
    if not carriers_unchanged:
        _fail("VALIDATION_CARRIER_MUTATED_DURING_EVALUATION")
    if not rng_restored or not environment_restored:
        _fail("CPU_RNG_OR_DETERMINISM_STATE_NOT_RESTORED")
    if caught is not None:
        raise caught
    return _GuardedSliceCollectionV1(
        estimates=tuple(estimates),
        main_calls=main_calls,
        t0_calls=t0_calls,
        fixed_clean=fixed_clean,
        indicator_reused=indicator_reused,
        tensors_require_grad=tensors_require_grad,
        before=before,
        after=after,
        parameters_unchanged=parameters_unchanged,
        buffers_unchanged=buffers_unchanged,
        gradients_unchanged=gradients_unchanged,
        requires_grad_unchanged=requires_grad_unchanged,
        parameter_identities_unchanged=parameter_identities_unchanged,
        buffer_identities_unchanged=buffer_identities_unchanged,
        module_identities_unchanged=module_identities_unchanged,
        state_keys_unchanged=state_keys_unchanged,
        configuration_unchanged=configuration_unchanged,
        node_distribution_unchanged=node_distribution_unchanged,
        training_flags_restored=training_flags_restored,
        carriers_unchanged=carriers_unchanged,
        CPU_rng_restored=rng_restored,
        CPU_determinism_settings_restored=environment_restored,
        evidence_kind=evidence_kind,
    )


def _finite_estimate(row: published_evaluator.FormalValidationEstimateV1) -> bool:
    optional = (
        row.task4_log_pN,
        row.task4_historical_joint_nll_with_node_prior_diagnostic,
    )
    values = (
        row.main_active_epsilon_error,
        row.SNR_weight,
        row.loss_t,
        row.t0_coordinate_loss,
        row.t0_categorical_loss,
        row.negative_log_coordinate_constant,
        row.kl_prior,
        row.masked_delta_log_px,
        row.masked_conditional_vlb_nll,
        row.pair_BCE,
        row.POST_geometry_loss,
        row.POST_geometry_prediction_angstrom,
        row.POST_geometry_target_angstrom,
        row.pair_contrastive_loss,
    )
    return all(math.isfinite(value) for value in values) and all(
        value is None or math.isfinite(value) for value in optional
    )


def _validate_and_aggregate_rows_v1(
    *,
    estimates: tuple[published_evaluator.FormalValidationEstimateV1, ...],
    prepared: CovapieBatch001PreparedCurrentStateValidation4V1,
) -> tuple[
    tuple[published_evaluator.FormalValidationEventTaskMeanV1, ...],
    tuple[published_evaluator.FormalValidationEventMeanV1, ...],
    float,
    float,
    tuple[tuple[str, float], ...],
    float,
]:
    expected_keys = {
        (event_id, task_id, seed)
        for task_id, preview in prepared.task_batches
        for event_id in preview.sample_identities
        for seed in published_evaluator.FORMAL_VALIDATION_ROOT_SEEDS_V1
    }
    observed_keys = tuple(
        (row.canonical_event_id, row.canonical_task_id, row.root_validation_seed)
        for row in estimates
    )
    if (
        len(estimates) != 64
        or len(set(observed_keys)) != 64
        or set(observed_keys) != expected_keys
        or any(
            type(row) is not published_evaluator.FormalValidationEstimateV1
            for row in estimates
        )
    ):
        _fail("ESTIMATE_EXACT_EVENT_TASK_SEED_DOMAIN_INVALID")
    for row in estimates:
        record = prepared.record_by_event.get(row.canonical_event_id)
        expected_name, expected_alias = CANONICAL_MASK_CONTRACT_V1[
            row.canonical_task_id
        ][1:]
        if (
            record is None
            or row.formal_split != "validation"
            or row.canonical_event_id
            in set(
                prepared.authority.train_event_ids
                + prepared.authority.test_event_ids
            )
            or row.pdb_id != record.pdb_id
            or row.ligand_component_id != record.ligand_component_id
            or row.profile != published_evaluator._profile_name(record)
            or row.leakage_group
            != prepared.leakage_by_event[row.canonical_event_id]
            or row.canonical_task_name != expected_name
            or row.canonical_task_alias != expected_alias
            or not _finite_estimate(row)
            or not 1 <= row.main_timestep_int <= 500
            or row.generated_atom_count <= 0
            or row.fixed_atom_count < 0
            or row.target_cys_sg_indicator_count != 1
            or row.pair_candidate_count < 2
            or row.PRE_geometry_valid is not False
            or not row.fixed_ligand_clean_main
            or not row.fixed_ligand_clean_t0
        ):
            _fail("ESTIMATE_ROW_METADATA_OR_NUMERIC_DOMAIN_INVALID")
        expected_dimension = 3 * (
            row.generated_atom_count - int(row.canonical_task_id == 4)
        )
        task4 = row.canonical_task_id == 4
        if (
            row.coordinate_dimension != expected_dimension
            or (row.fixed_atom_count == 0) != task4
            or (row.task4_log_pN is not None) != task4
            or (
                row.task4_historical_joint_nll_with_node_prior_diagnostic
                is not None
            )
            != task4
            or (
                task4
                and not math.isclose(
                    float(
                        row.task4_historical_joint_nll_with_node_prior_diagnostic
                    ),
                    row.masked_conditional_vlb_nll - float(row.task4_log_pN),
                    rel_tol=1.0e-6,
                    abs_tol=1.0e-6,
                )
            )
        ):
            _fail("ESTIMATE_COORDINATE_OR_TASK4_DIAGNOSTIC_INVALID")
    return published_evaluator._aggregate(estimates)


def evaluate_covapie_batch001_current_state_validation4_v1(
    *,
    source_model: object,
    execution_opt_in: object = False,
    caller_model_stage: object,
    caller_stage_evidence: object,
    caller_confirms_model_is_quiescent: object,
    repository_root: object = None,
    cache_root: object = None,
) -> CovapieBatch001CurrentStateValidation4ResultV1:
    """Evaluate one caller-owned current CPU model after explicit opt-in."""

    try:
        if execution_opt_in is not True:
            _fail("EXPLICIT_MODEL_EVALUATION_OPT_IN_REQUIRED")
        stage, stage_evidence = _validate_caller_metadata(
            caller_model_stage=caller_model_stage,
            caller_stage_evidence=caller_stage_evidence,
            caller_confirms_model_is_quiescent=(
                caller_confirms_model_is_quiescent
            ),
        )
        repository = _require_directory(
            repository_root,
            default=_DEFAULT_REPOSITORY_ROOT,
            reason="REPOSITORY_ROOT_INVALID",
        )
        cache = _require_directory(
            cache_root,
            default=_DEFAULT_CACHE_ROOT,
            reason="CACHE_ROOT_INVALID",
        )
        bindings = verify_covapie_batch001_current_state_validation4_sources_v1(
            repository_root=repository
        )
        node_distribution_sha = _validate_current_source_model_v1(source_model)
        prepared = _prepare_impl(
            repository_root=repository,
            cache_root=cache,
            source_bindings=bindings,
        )
        started = time.perf_counter()
        collection = _guarded_slice_collection_v1(
            source_model=source_model,
            prepared=prepared,
        )
        if (
            collection.main_calls != 20
            or collection.t0_calls != 20
            or collection.tensors_require_grad
            or not collection.fixed_clean
            or not collection.indicator_reused
        ):
            _fail("FORMAL_MODEL_EXECUTION_COUNTS_OR_GUARDS_INVALID")
        (
            event_task,
            event_means,
            event_macro,
            micro,
            profile_means,
            profile_balanced,
        ) = _validate_and_aggregate_rows_v1(
            estimates=collection.estimates, prepared=prepared
        )
        estimates = collection.estimates
        task4_joint = published_evaluator._means(tuple(
            float(row.task4_historical_joint_nll_with_node_prior_diagnostic)
            for row in estimates
            if row.task4_historical_joint_nll_with_node_prior_diagnostic
            is not None
        ))
        return CovapieBatch001CurrentStateValidation4ResultV1(
            implementation_status="EXECUTED",
            metric_evidence_kind="REAL_CALLER_MODEL_EXECUTION",
            primary_metric_name=PRIMARY_METRIC_NAME_V1,
            validation_model_weight_source=VALIDATION_MODEL_WEIGHT_SOURCE_V1,
            caller_model_stage=stage,
            caller_stage_evidence=stage_evidence,
            caller_quiescence_asserted=True,
            model_training_provenance_status=MODEL_STATE_TRAINING_PROVENANCE_V1,
            historical_output644_model_state_recovered=False,
            source_model_identity=(
                type(source_model).__module__ + "." + type(source_model).__qualname__
            ),
            source_model_state_sha256_before=(
                collection.before.model_state_sha256
            ),
            source_model_state_sha256_after=collection.after.model_state_sha256,
            current_node_prior_source=NODE_PRIOR_SOURCE_V1,
            current_node_distribution_sha256_before=(
                collection.before.node_distribution_sha256
            ),
            current_node_distribution_sha256_after=(
                collection.after.node_distribution_sha256
            ),
            current_node_distribution_verified=(
                collection.before.node_distribution_sha256
                == node_distribution_sha
                == collection.after.node_distribution_sha256
            ),
            formal_validation_event_ids=(
                published_evaluator.FORMAL_VALIDATION_EVENT_IDS_V1
            ),
            root_validation_seeds=(
                published_evaluator.FORMAL_VALIDATION_ROOT_SEEDS_V1
            ),
            formal_validation_event_count=4,
            formal_validation_task_event_count=16,
            formal_validation_estimate_count=64,
            formal_validation_task_slice_evaluation_count=20,
            main_dynamics_task_slice_call_count=collection.main_calls,
            t0_dynamics_task_slice_call_count=collection.t0_calls,
            total_dynamics_task_slice_call_count=(
                collection.main_calls + collection.t0_calls
            ),
            per_estimate_rows=estimates,
            per_event_task_seed_means=event_task,
            per_event_means=event_means,
            event_macro_masked_conditional_vlb_nll=event_macro,
            micro_masked_conditional_vlb_nll=micro,
            profile_means=profile_means,
            profile_balanced_masked_conditional_vlb_nll=profile_balanced,
            mean_pair_BCE=published_evaluator._means(
                tuple(row.pair_BCE for row in estimates)
            ),
            mean_POST_geometry_loss=published_evaluator._means(
                tuple(row.POST_geometry_loss for row in estimates)
            ),
            mean_POST_geometry_prediction_angstrom=published_evaluator._means(
                tuple(row.POST_geometry_prediction_angstrom for row in estimates)
            ),
            mean_POST_geometry_target_angstrom=published_evaluator._means(
                tuple(row.POST_geometry_target_angstrom for row in estimates)
            ),
            mean_pair_contrastive_loss=published_evaluator._means(
                tuple(row.pair_contrastive_loss for row in estimates)
            ),
            mean_task4_historical_joint_nll_with_node_prior_diagnostic=(
                task4_joint
            ),
            primary_node_prior_included=False,
            source_parameters_unchanged=collection.parameters_unchanged,
            source_buffers_unchanged=collection.buffers_unchanged,
            source_gradients_unchanged=collection.gradients_unchanged,
            source_requires_grad_unchanged=collection.requires_grad_unchanged,
            source_parameter_identities_unchanged=(
                collection.parameter_identities_unchanged
            ),
            source_buffer_identities_unchanged=(
                collection.buffer_identities_unchanged
            ),
            source_module_identities_unchanged=(
                collection.module_identities_unchanged
            ),
            source_state_keys_unchanged=collection.state_keys_unchanged,
            source_configuration_unchanged=collection.configuration_unchanged,
            evaluation_carriers_unchanged=collection.carriers_unchanged,
            source_training_flags_restored=collection.training_flags_restored,
            CPU_rng_restored=collection.CPU_rng_restored,
            CPU_determinism_settings_restored=(
                collection.CPU_determinism_settings_restored
            ),
            no_new_parameter_module_or_state_key=(
                collection.parameter_identities_unchanged
                and collection.buffer_identities_unchanged
                and collection.module_identities_unchanged
                and collection.state_keys_unchanged
            ),
            metric_tensors_require_grad=collection.tensors_require_grad,
            all_validation_rows_finite=True,
            checkpoint_loaded_inside_validation=False,
            shadow_model_constructed=False,
            optimizer_created=False,
            Trainer_used=False,
            backward_performed=False,
            parameter_update_performed=False,
            runtime_elapsed_seconds=time.perf_counter() - started,
        )
    except BaseException as error:
        _public_error(error)


def serialize_covapie_batch001_current_state_validation4_prepare_v1(
    prepared: object,
) -> bytes:
    if type(prepared) is not CovapieBatch001PreparedCurrentStateValidation4V1:
        _public_error(_AdapterInvariantError("PREPARED_RESULT_TYPE_INVALID"))
    return (
        json.dumps(
            asdict(prepared.summary),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare Batch001 current-state validation4; no model execution."
    )
    parser.add_argument("--repository-root", type=Path, default=None)
    parser.add_argument("--cache-root", type=Path, default=None)
    arguments = parser.parse_args(argv)
    prepared = prepare_covapie_batch001_current_state_validation4_v1(
        repository_root=arguments.repository_root,
        cache_root=arguments.cache_root,
    )
    print(
        serialize_covapie_batch001_current_state_validation4_prepare_v1(
            prepared
        ).decode("utf-8"),
        end="",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
