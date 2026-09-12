"""Read-only Batch001 carrier feature and hidden-POST preflight V1.

This owner builds the published train5 and validation4 CPU carriers for task
schedule epochs 0--4.  It audits the source-to-carrier feature/index boundary
and independently reconstructs eligibility for the scoped
``independent_hidden_post_distance_v1`` purpose.  The reconstruction is audit
only: it neither calls nor replaces the production loss gate.

No checkpoint, model, forward, loss, backward, optimizer, or Trainer API is
used by this module.
"""

from __future__ import annotations

import argparse
import ast
import csv
from dataclasses import asdict, dataclass, fields, is_dataclass
import hashlib
import io
import json
import math
from pathlib import Path
import stat
import sys
from typing import Mapping, NoReturn, Sequence

import torch

from covalent_ext import (
    covapie_batch001_13event_model_usable_split_materialization_and_activation_boundary_v1
    as activation_owner,
)
from covalent_ext import covapie_batch001_positive_structural_input_v1 as structural_owner
from covalent_ext import (
    covapie_batch001_to_existing_mixed_profile_supervision_bridge_v1
    as preview_owner,
)
from covalent_ext import (
    covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1
    as feature_owner,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CANONICAL_TASKS_V1,
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


__all__ = (
    "BATCH001_FEATURE_POST_USE_PREFLIGHT_ERROR_V1",
    "PILOT_POST_PURPOSE_V1",
    "BOUND_SOURCE_SHA256_V1",
    "EXPECTED_TRAIN_HIDDEN_POST_ELIGIBLE_COUNTS_V1",
    "CovapieBatch001PreflightSourceBindingV1",
    "CovapieBatch001HiddenPostEligibilityRowV1",
    "CovapieBatch001HiddenPostEpochSummaryV1",
    "CovapieBatch001FeaturePostUsePreflightResultV1",
    "verify_covapie_batch001_feature_post_use_preflight_sources_v1",
    "validate_covapie_batch001_feature_projection_policy_v1",
    "audit_covapie_batch001_feature_post_use_carrier_v1",
    "run_covapie_batch001_feature_post_use_preflight_v1",
    "serialize_covapie_batch001_feature_post_use_preflight_result_v1",
    "main",
)


BATCH001_FEATURE_POST_USE_PREFLIGHT_ERROR_V1 = (
    "COVAPIE_BATCH001_FEATURE_POST_USE_PREFLIGHT_V1_ERROR"
)
TASK_ID_V1 = "implement_covapie_batch001_feature_post_use_preflight_v1"
PILOT_POST_PURPOSE_V1 = "independent_hidden_post_distance_v1"
LEGACY_POST_PURPOSE_V1 = "existing_component_masks_v1"
EXPECTED_TRAIN_HIDDEN_POST_ELIGIBLE_COUNTS_V1 = (5, 4, 5, 4, 2)
TASK_SCHEDULE_SEED_V1 = 0
TASK_EPOCHS_V1 = (0, 1, 2, 3, 4)

CURRENT_TRAINING_SOURCE_V1 = (
    "src/covalent_ext/covapie_current11_training_lightning_module_v1.py"
)
CURRENT_LOSS_SOURCE_V1 = (
    "src/covalent_ext/covapie_current11_auxiliary_model_and_loss_v1.py"
)
LEGACY_FORMAL_INTEGRATION_SOURCE_V1 = (
    "src/covalent_ext/"
    "covapie_batch001_formal_training_datamodule_and_train_validation_"
    "integration_v1.py"
)
BATCH001_LEGACY_ADAPTER_SOURCE_V1 = (
    "src/covalent_ext/covapie_batch001_train5_bounded_trainer_fit_smoke_v1.py"
)
PUBLISHED_SPLIT_INDEX_V1 = (
    "data/derived/covalent_small/"
    "covapie_batch001_13event_model_usable_split_materialization_and_"
    "activation_boundary_v1/"
    "covapie_batch001_13event_model_usable_split_index_v1.csv"
)

CURRENT_SOURCE_SHA256_V1 = {
    CURRENT_TRAINING_SOURCE_V1: (
        "a61041ef44e79c0622645965461bf4cc0275e5f3bec9a756fcf7d36a4c9c391b"
    ),
    CURRENT_LOSS_SOURCE_V1: (
        "bb797fdb0c96ce669a348a3ddf3975771398263cdfa2a22f3d9c55b0011271cd"
    ),
}
LEGACY_FORMAL_INTEGRATION_PINS_V1 = {
    CURRENT_TRAINING_SOURCE_V1: (
        "d3d21b920785f791652cb456465a8bb375a09cdf0e24e5e84415b01f82cd6485"
    ),
    CURRENT_LOSS_SOURCE_V1: (
        "5bf91b3af56ec0e5c2dec3ebb13e56695ca74c17bbbbb65f35e8d9249d6fc60f"
    ),
}

# These are fixed expectations, not values discovered and accepted at runtime.
BOUND_SOURCE_SHA256_V1 = (
    (
        "src/covalent_ext/"
        "covapie_batch001_13event_model_usable_split_materialization_and_"
        "activation_boundary_v1.py",
        "e57d2b8d75cf53cb37992a33e8e41a4075dbf94422243ad6686197722d1b48f7",
    ),
    (
        "src/covalent_ext/covapie_batch001_positive_structural_input_v1.py",
        "c4cada3c5d3e8e86176b097cc5546854122162055437e4667288ba2f82629067",
    ),
    (
        "src/covalent_ext/"
        "covapie_batch001_to_existing_mixed_profile_supervision_bridge_v1.py",
        "168c819e0422b110880676c1a99b82a8531e94f9849a3dcfb7d4c45dbdd73400",
    ),
    (
        "src/covalent_ext/"
        "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1.py",
        "1d80862e7c4fa3215ac3f307a45ce3bc8f1e0d4613728133a0ea3118df2df241",
    ),
    (
        "src/covalent_ext/covapie_direct_attachment_optional_linker_runtime_v1.py",
        "434285a43fa0158e62d40f48ed95d137f5fd68ea9b00101cc20674025849c535",
    ),
    (
        "src/covalent_ext/covapie_current11_training_tensorizer_v1.py",
        "9fdc3f7f101fab5e5e5452e3d8e9f9b0b1e6e5fa8254a261f36310a1dfd0b606",
    ),
    (
        "src/covalent_ext/"
        "covapie_tensor_label_and_loss_mask_contract_design_v1.py",
        "3d2d03cda56dfb4a54370444f255f9bb0ab433aaeb837901e769098272ff51ac",
    ),
    (
        "src/covalent_ext/"
        "covapie_batch001_train5_admission_aware_cpu_forward_loss_smoke_v1.py",
        "3f19d39148f374d14744fa714a2e7d648a37099168d539c14e7e2320d390ec21",
    ),
    (
        BATCH001_LEGACY_ADAPTER_SOURCE_V1,
        "ab4659abeed0a93a442dae68cc339a389c6fbee10e3747f36735117cb89a54c7",
    ),
    (
        CURRENT_TRAINING_SOURCE_V1,
        CURRENT_SOURCE_SHA256_V1[CURRENT_TRAINING_SOURCE_V1],
    ),
    (
        CURRENT_LOSS_SOURCE_V1,
        CURRENT_SOURCE_SHA256_V1[CURRENT_LOSS_SOURCE_V1],
    ),
    (
        LEGACY_FORMAL_INTEGRATION_SOURCE_V1,
        "0cdaccb222c23aff98c158cdedc1f33b23e2b2c815219545c8ecddb04c929a53",
    ),
    (
        PUBLISHED_SPLIT_INDEX_V1,
        "f22064a20000126b0792a22e241f3cf9d912bc804da7c5f58eb2f5669157faf3",
    ),
)

_MODEL_INPUT_FIELDS_V1 = frozenset((
    "names",
    "receptors",
    "lig_coords",
    "pocket_coords",
    "lig_one_hot",
    "pocket_one_hot",
    "lig_source_row_index",
    "pocket_source_row_index",
    "lig_parser_local_index",
    "pocket_parser_local_index",
    "num_lig_atoms",
    "num_pocket_nodes",
    "lig_mask",
    "pocket_mask",
))

_EXPECTED_CANONICAL_TASKS_V1 = (
    (0, "warhead_only", "A", (2,)),
    (1, "linker_plus_warhead", "B", (1, 2)),
    (2, "scaffold_plus_warhead", "B2", (0, 2)),
    (3, "scaffold_only", "B3", (0,)),
    (4, "scaffold_plus_linker_plus_warhead", "C", (0, 1, 2)),
)
_EXPECTED_GROUPS_V1 = (
    (
        "train",
        (
            "COVAPIE_EXPANSION_LEAKAGE_GROUP_B603B4C07705F93D",
            "COVAPIE_EXPANSION_LEAKAGE_GROUP_3157B39692D4D3EA",
        ),
    ),
    (
        "validation",
        (
            "COVAPIE_EXPANSION_LEAKAGE_GROUP_8B76795E5CE26D95",
            "COVAPIE_EXPANSION_LEAKAGE_GROUP_AD79B40D8A505F37",
        ),
    ),
    ("test", ("COVAPIE_LEAKAGE_GROUP_000005",)),
)
_PATH_TYPE = type(Path())


@dataclass(frozen=True)
class CovapieBatch001PreflightSourceBindingV1:
    relative_path: str
    expected_sha256: str
    observed_sha256: str
    sha256_verified: bool
    legacy_formal_integration_sha256: str
    differs_from_legacy_formal_integration: bool


@dataclass(frozen=True)
class CovapieBatch001HiddenPostEligibilityRowV1:
    formal_split: str
    epoch: int
    canonical_event_id: str
    canonical_task_id: int
    canonical_task_semantic_name: str
    canonical_task_display_alias: str
    positive_endpoint_ligand_local_index: int
    positive_endpoint_ligand_flat_index: int
    positive_endpoint_pocket_local_index: int
    positive_endpoint_pocket_flat_index: int
    positive_endpoint_generated: bool
    positive_endpoint_fixed: bool
    original_post_request: bool
    original_post_component_valid: bool
    sample_training_admitted: bool
    canonical_task_valid: bool
    target_condition_valid: bool
    positive_pair_valid: bool
    preflight_effective_hidden_post_eligible: bool
    exclusion_reasons: tuple[str, ...]


@dataclass(frozen=True)
class CovapieBatch001HiddenPostEpochSummaryV1:
    formal_split: str
    epoch: int
    canonical_task_ids: tuple[int, ...]
    effective_hidden_post_eligible_count: int


@dataclass(frozen=True)
class CovapieBatch001FeaturePostUsePreflightResultV1:
    schema_version: str
    task_id: str
    pilot_post_purpose: str
    source_bindings: tuple[CovapieBatch001PreflightSourceBindingV1, ...]
    split_event_ids: tuple[tuple[str, tuple[str, ...]], ...]
    split_leakage_groups: tuple[tuple[str, tuple[str, ...]], ...]
    carrier_fingerprints: tuple[tuple[str, int, str], ...]
    hidden_post_rows: tuple[CovapieBatch001HiddenPostEligibilityRowV1, ...]
    hidden_post_epoch_summaries: tuple[
        CovapieBatch001HiddenPostEpochSummaryV1, ...
    ]
    train_hidden_post_eligible_counts: tuple[int, ...]
    validation_hidden_post_eligible_counts: tuple[int, ...]
    exact10_channel_order: str
    exact5_semantic_names: tuple[str, ...]
    actual_carrier_split_count: int
    actual_carrier_event_epoch_count: int
    test_carrier_constructed: bool
    scoped_carrier_feature_preflight_pass: bool
    scoped_hidden_post_eligibility_preflight_pass: bool
    current_source_bindings_verified: bool
    current_source_differs_from_legacy_pins: bool
    current_interface_semantics_verified_statically: bool
    legacy_trainer_routing_updated: bool
    production_loss_gate_called: bool
    checkpoint_loaded: bool
    model_instantiated: bool
    model_or_loss_executed: bool
    parameter_update_performed_this_round: bool
    training_started: bool
    ready_for_training: bool
    feature_semantics_audit_required_later: bool
    step12d_is_only_smoke_legality_check: bool
    summary_sha256: str


class _PreflightInvariantError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _fail(reason: str) -> NoReturn:
    raise _PreflightInvariantError(reason)


def _public_error(error: BaseException) -> NoReturn:
    if type(error) is ValueError and str(error).startswith(
        BATCH001_FEATURE_POST_USE_PREFLIGHT_ERROR_V1
    ):
        raise error
    reason = error.reason if isinstance(error, _PreflightInvariantError) else "OWNER_REJECTED"
    raise ValueError(
        f"{BATCH001_FEATURE_POST_USE_PREFLIGHT_ERROR_V1}:{reason}"
    ) from error


def _require_directory(value: object, *, default: Path, reason: str) -> Path:
    path = default if value is None else value
    if type(path) is not _PATH_TYPE or not path.is_absolute():
        _fail(reason)
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise _PreflightInvariantError(reason) from error
    if resolved != path or path.is_symlink() or not path.is_dir():
        _fail(reason)
    return path


def _read_safe_file(path: Path) -> bytes:
    try:
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            _fail("BOUND_SOURCE_NOT_SAFE_REGULAR_FILE:" + path.as_posix())
        return path.read_bytes()
    except OSError as error:
        raise _PreflightInvariantError("BOUND_SOURCE_READ_FAILED") from error


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_default(value: object) -> object:
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(type(value).__name__)


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
            default=_json_default,
        )
        + "\n"
    ).encode("utf-8")


def _literal_tuple_pins(source: bytes, assignment_name: str) -> dict[str, str]:
    try:
        tree = ast.parse(source.decode("utf-8"))
    except (UnicodeError, SyntaxError) as error:
        raise _PreflightInvariantError("LEGACY_INTEGRATION_SOURCE_INVALID") from error
    assignment = None
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else ()
        if any(isinstance(target, ast.Name) and target.id == assignment_name for target in targets):
            assignment = node.value
            break
    if not isinstance(assignment, ast.Tuple):
        _fail("LEGACY_SOURCE_PIN_ASSIGNMENT_MISSING")
    result: dict[str, str] = {}
    for entry in assignment.elts:
        if not isinstance(entry, ast.Tuple) or len(entry.elts) != 2:
            continue
        try:
            relative = ast.literal_eval(entry.elts[0])
            digest = ast.literal_eval(entry.elts[1])
        except (ValueError, TypeError):
            continue
        if type(relative) is str and type(digest) is str:
            result[relative] = digest
    return result


def _call_keyword_sets(source: bytes, function_name: str) -> tuple[frozenset[str], ...]:
    try:
        tree = ast.parse(source.decode("utf-8"))
    except (UnicodeError, SyntaxError) as error:
        raise _PreflightInvariantError("BOUND_SOURCE_PYTHON_INVALID") from error
    result = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = (
            node.func.id
            if isinstance(node.func, ast.Name)
            else node.func.attr
            if isinstance(node.func, ast.Attribute)
            else ""
        )
        if name == function_name:
            result.append(frozenset(keyword.arg for keyword in node.keywords if keyword.arg))
    return tuple(result)


def _validate_current_interface_semantics(
    payloads: Mapping[str, bytes], legacy_pins: Mapping[str, str]
) -> None:
    if any(
        legacy_pins.get(relative) != expected
        for relative, expected in LEGACY_FORMAL_INTEGRATION_PINS_V1.items()
    ):
        _fail("LEGACY_FORMAL_INTEGRATION_PIN_DRIFT")
    training_calls = _call_keyword_sets(
        payloads[CURRENT_TRAINING_SOURCE_V1],
        "compute_covapie_current11_training_losses_v1",
    )
    adapter_calls = _call_keyword_sets(
        payloads[BATCH001_LEGACY_ADAPTER_SOURCE_V1],
        "compute_covapie_current11_training_losses_v1",
    )
    required_current_keywords = {
        "post_geometry_loss_purpose",
        "ligand_batch_index",
        "pocket_batch_index",
    }
    if (
        not any(required_current_keywords.issubset(keywords) for keywords in training_calls)
        or not adapter_calls
        or any("post_geometry_loss_purpose" in keywords for keywords in adapter_calls)
    ):
        _fail("CURRENT_VS_BATCH001_POST_ROUTING_INTERFACE_INVALID")
    training_text = payloads[CURRENT_TRAINING_SOURCE_V1].decode("utf-8")
    loss_text = payloads[CURRENT_LOSS_SOURCE_V1].decode("utf-8")
    if (
        'post_geometry_loss_purpose: str = "existing_component_masks_v1"'
        not in training_text
        or "def _hidden_post_effective_component_loss_mask_v1(" not in loss_text
        or "& endpoint_is_hidden" not in loss_text
        or "anchor_valid_mask & fixed_mask & ~generation_mask" not in loss_text
    ):
        _fail("CURRENT_FEATURE_OR_POST_INTERFACE_SEMANTICS_MISSING")


def verify_covapie_batch001_feature_post_use_preflight_sources_v1(
    *, repository_root: object = None
) -> tuple[CovapieBatch001PreflightSourceBindingV1, ...]:
    """Verify fixed current/data pins and the frozen legacy-pin comparison."""

    try:
        repo = _require_directory(
            repository_root,
            default=Path(__file__).resolve().parents[2],
            reason="REPOSITORY_ROOT_INVALID",
        )
        payloads: dict[str, bytes] = {}
        bindings = []
        for relative, expected in BOUND_SOURCE_SHA256_V1:
            payload = _read_safe_file(repo / relative)
            observed = _sha256(payload)
            if observed != expected:
                _fail("BOUND_SOURCE_SHA256_MISMATCH:" + relative)
            payloads[relative] = payload
            legacy = LEGACY_FORMAL_INTEGRATION_PINS_V1.get(relative, "")
            bindings.append(CovapieBatch001PreflightSourceBindingV1(
                relative_path=relative,
                expected_sha256=expected,
                observed_sha256=observed,
                sha256_verified=True,
                legacy_formal_integration_sha256=legacy,
                differs_from_legacy_formal_integration=bool(legacy and legacy != observed),
            ))
        legacy_pins = _literal_tuple_pins(
            payloads[LEGACY_FORMAL_INTEGRATION_SOURCE_V1],
            "BOUND_SOURCE_SHA256_V1",
        )
        _validate_current_interface_semantics(payloads, legacy_pins)
        if not all(
            next(
                binding for binding in bindings if binding.relative_path == relative
            ).differs_from_legacy_formal_integration
            for relative in CURRENT_SOURCE_SHA256_V1
        ):
            _fail("CURRENT_SOURCE_NOT_DISTINCT_FROM_FROZEN_LEGACY_PIN")
        return tuple(bindings)
    except BaseException as error:
        _public_error(error)


def validate_covapie_batch001_feature_projection_policy_v1() -> bool:
    """Exercise Exact10, H exclusion, and fail-closed non-H rejection."""

    try:
        tokens = tuple(item[0] for item in feature_owner.CHECKPOINT_VOCABULARY)
        if tokens != ("C", "N", "O", "S", "B", "Br", "Cl", "P", "I", "F"):
            _fail("CHECKPOINT_EXACT10_ORDER_INVALID")
        projection = feature_owner.project_type_symbols_to_checkpoint_heavy_v1(
            ("C", "H", "Br", "F")
        )
        if (
            projection.sample_rejected
            or projection.outcome != "passed"
            or projection.keep_mask != (True, False, True, True)
            or projection.source_to_projected_index != (0, None, 1, 2)
            or projection.checkpoint_channel_indices != (0, None, 5, 9)
        ):
            _fail("EXPLICIT_HYDROGEN_PROJECTION_POLICY_INVALID")
        for values in (("C", "Se"), ("C", ""), ("C", None)):
            rejected = feature_owner.project_type_symbols_to_checkpoint_heavy_v1(values)
            if (
                not rejected.sample_rejected
                or rejected.outcome != "invalid"
                or any(rejected.keep_mask)
                or any(item is not None for item in rejected.checkpoint_channel_indices)
            ):
                _fail("UNSUPPORTED_OR_INVALID_ATOM_NOT_REJECTED")
        return True
    except BaseException as error:
        _public_error(error)


def _tensor_bytes(value: torch.Tensor) -> bytes:
    contiguous = value.detach().contiguous().cpu()
    return contiguous.view(torch.uint8).numpy().tobytes()


def _carrier_fingerprint(
    carrier: activation_owner.CovapieBatch001ModelUsableSplitBatchV1,
) -> str:
    digest = hashlib.sha256()
    digest.update(carrier.formal_split.encode("utf-8"))
    digest.update(str(carrier.epoch).encode("ascii"))
    digest.update(str(carrier.task_schedule_seed).encode("ascii"))
    digest.update(_canonical_json_bytes(carrier.sample_identities))
    for name in sorted(carrier.model_input_batch):
        value = carrier.model_input_batch[name]
        digest.update(name.encode("utf-8"))
        if isinstance(value, torch.Tensor):
            digest.update(str(value.dtype).encode("ascii"))
            digest.update(str(tuple(value.shape)).encode("ascii"))
            digest.update(_tensor_bytes(value))
        else:
            digest.update(_canonical_json_bytes(value))
    for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1):
        value = getattr(carrier.supervision, field.name)
        digest.update(field.name.encode("utf-8"))
        digest.update(str(value.dtype).encode("ascii"))
        digest.update(str(tuple(value.shape)).encode("ascii"))
        digest.update(_tensor_bytes(value))
    return digest.hexdigest()


def _require_tensor(
    value: object,
    *,
    name: str,
    dtype: torch.dtype,
    ndim: int,
) -> torch.Tensor:
    if (
        not isinstance(value, torch.Tensor)
        or value.dtype != dtype
        or value.ndim != ndim
        or value.device.type != "cpu"
        or value.requires_grad
    ):
        _fail("CARRIER_TENSOR_INVALID:" + name)
    return value


def _offsets(counts: Sequence[int]) -> tuple[int, ...]:
    result = [0]
    for count in counts:
        if type(count) is not int or count <= 0:
            _fail("NODE_COUNT_INVALID")
        result.append(result[-1] + count)
    return tuple(result)


def _expected_roles(
    record: structural_owner.CovapieBatch001PositiveStructuralRecordV1,
) -> torch.Tensor:
    result = torch.full(
        (len(record.ligand_retained_heavy_atoms),), -1, dtype=torch.long
    )
    for role, indices in enumerate((
        record.scaffold_retained_local_indices,
        record.linker_retained_local_indices,
        record.warhead_retained_local_indices,
    )):
        result[list(indices)] = role
    if bool((result < 0).any().item()):
        _fail("LIGAND_ROLE_PARTITION_GAP")
    return result


def _validate_model_input_and_feature_boundary(
    carrier: activation_owner.CovapieBatch001ModelUsableSplitBatchV1,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    model = carrier.model_input_batch
    records = carrier.structural_records
    if type(model) is not dict or frozenset(model) != _MODEL_INPUT_FIELDS_V1:
        _fail("MODEL_INPUT_FIELD_BOUNDARY_INVALID")
    if (
        model["names"] != list(carrier.sample_identities)
        or model["receptors"] != [record.pdb_id for record in records]
    ):
        _fail("MODEL_INPUT_IDENTITY_ORDER_INVALID")
    ligand_counts = tuple(len(record.ligand_retained_heavy_atoms) for record in records)
    pocket_counts = tuple(len(record.pocket_retained_heavy_atoms) for record in records)
    ligand_offsets = _offsets(ligand_counts)
    pocket_offsets = _offsets(pocket_counts)
    ligand_rows = tuple(row for record in records for row in record.ligand_retained_heavy_atoms)
    pocket_rows = tuple(row for record in records for row in record.pocket_retained_heavy_atoms)
    ligand_total, pocket_total = len(ligand_rows), len(pocket_rows)

    lig_coords = _require_tensor(
        model["lig_coords"], name="lig_coords", dtype=torch.float32, ndim=2
    )
    pocket_coords = _require_tensor(
        model["pocket_coords"], name="pocket_coords", dtype=torch.float32, ndim=2
    )
    lig_one_hot = _require_tensor(
        model["lig_one_hot"], name="lig_one_hot", dtype=torch.float32, ndim=2
    )
    pocket_one_hot = _require_tensor(
        model["pocket_one_hot"], name="pocket_one_hot", dtype=torch.float32, ndim=2
    )
    if (
        tuple(lig_coords.shape) != (ligand_total, 3)
        or tuple(pocket_coords.shape) != (pocket_total, 3)
        or tuple(lig_one_hot.shape) != (ligand_total, 10)
        or tuple(pocket_one_hot.shape) != (pocket_total, 10)
        or not bool(torch.isfinite(lig_coords).all().item())
        or not bool(torch.isfinite(pocket_coords).all().item())
    ):
        _fail("COORDINATE_OR_EXACT10_SHAPE_INVALID")
    expected_lig_coords = torch.tensor(
        tuple(row.coordinates_angstrom for row in ligand_rows), dtype=torch.float32
    )
    expected_pocket_coords = torch.tensor(
        tuple(row.coordinates_angstrom for row in pocket_rows), dtype=torch.float32
    )
    expected_lig_channels = torch.tensor(
        tuple(row.checkpoint_channel_index for row in ligand_rows), dtype=torch.long
    )
    expected_pocket_channels = torch.tensor(
        tuple(row.checkpoint_channel_index for row in pocket_rows), dtype=torch.long
    )
    if (
        not torch.equal(lig_coords, expected_lig_coords)
        or not torch.equal(pocket_coords, expected_pocket_coords)
        or not torch.equal(lig_one_hot, torch.eye(10)[expected_lig_channels])
        or not torch.equal(pocket_one_hot, torch.eye(10)[expected_pocket_channels])
        or not torch.equal(lig_one_hot.sum(1), torch.ones(ligand_total))
        or not torch.equal(pocket_one_hot.sum(1), torch.ones(pocket_total))
        or bool(((lig_one_hot != 0) & (lig_one_hot != 1)).any().item())
        or bool(((pocket_one_hot != 0) & (pocket_one_hot != 1)).any().item())
    ):
        _fail("EXACT10_VALUE_OR_CHANNEL_PROJECTION_INVALID")
    for row in (*ligand_rows, *pocket_rows):
        if (
            row.type_symbol == "H"
            or row.type_symbol not in feature_owner.CHECKPOINT_TOKEN_TO_INDEX
            or feature_owner.CHECKPOINT_TOKEN_TO_INDEX[row.type_symbol]
            != row.checkpoint_channel_index
        ):
            _fail("RETAINED_ATOM_FEATURE_SEMANTICS_INVALID")

    fields_and_expected = (
        ("lig_source_row_index", tuple(row.source_atom_site_row_index_0based for row in ligand_rows)),
        ("pocket_source_row_index", tuple(row.source_atom_site_row_index_0based for row in pocket_rows)),
        ("lig_parser_local_index", tuple(index for count in ligand_counts for index in range(count))),
        ("pocket_parser_local_index", tuple(index for count in pocket_counts for index in range(count))),
        ("lig_mask", tuple(sample for sample, count in enumerate(ligand_counts) for _ in range(count))),
        ("pocket_mask", tuple(sample for sample, count in enumerate(pocket_counts) for _ in range(count))),
    )
    for name, expected in fields_and_expected:
        value = _require_tensor(model[name], name=name, dtype=torch.long, ndim=1)
        if value.tolist() != list(expected):
            _fail("MODEL_INPUT_INDEX_OR_MEMBERSHIP_MISMATCH:" + name)
    if (
        _require_tensor(model["num_lig_atoms"], name="num_lig_atoms", dtype=torch.long, ndim=1).tolist()
        != list(ligand_counts)
        or _require_tensor(model["num_pocket_nodes"], name="num_pocket_nodes", dtype=torch.long, ndim=1).tolist()
        != list(pocket_counts)
    ):
        _fail("MODEL_INPUT_NODE_COUNTS_INVALID")
    return ligand_offsets, pocket_offsets


def _validate_supervision_and_build_rows(
    carrier: activation_owner.CovapieBatch001ModelUsableSplitBatchV1,
    ligand_offsets: tuple[int, ...],
    pocket_offsets: tuple[int, ...],
) -> tuple[CovapieBatch001HiddenPostEligibilityRowV1, ...]:
    supervision = carrier.supervision
    if not isinstance(supervision, CovapieCurrent11TrainingSupervisionTensorsV1):
        _fail("SUPERVISION_TYPE_INVALID")
    for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1):
        value = getattr(supervision, field.name)
        if not isinstance(value, torch.Tensor) or value.device.type != "cpu" or value.requires_grad:
            _fail("SUPERVISION_TENSOR_DOMAIN_INVALID:" + field.name)
    records = carrier.structural_records
    batch_size = len(records)
    expected_ids = (
        activation_owner.FORMAL_TRAIN_EVENT_IDS_V1
        if carrier.formal_split == "train"
        else activation_owner.FORMAL_VALIDATION_EVENT_IDS_V1
        if carrier.formal_split == "validation"
        else None
    )
    admitted_value = carrier.formal_split == "train"
    if (
        expected_ids is None
        or carrier.sample_identities != expected_ids
        or carrier.task_schedule_seed != TASK_SCHEDULE_SEED_V1
        or carrier.epoch not in TASK_EPOCHS_V1
        or carrier.sample_training_admitted != (admitted_value,) * batch_size
        or carrier.model_training_activation_authorized != (admitted_value,) * batch_size
        or carrier.optimizer_population_eligible != (admitted_value,) * batch_size
        or carrier.training_scheduler_eligible != (admitted_value,) * batch_size
        or carrier.formal_validation_population_member
        != (carrier.formal_split == "validation",) * batch_size
        or any(carrier.formal_test_population_member)
    ):
        _fail("SPLIT_ACTIVATION_BOUNDARY_INVALID")
    if carrier.formal_split == "validation" and any(
        item is not None for item in carrier.training_scheduled_task_ids
    ):
        _fail("VALIDATION_TRAINING_SCHEDULE_ACTIVE")

    task_ids = supervision.canonical_task_id.tolist()
    if (
        task_ids != list(carrier.preview_tensorization_task_ids)
        or not bool(supervision.canonical_task_valid.all().item())
        or supervision.sample_training_admitted.tolist() != [admitted_value] * batch_size
    ):
        _fail("CARRIER_TASK_OR_ADMISSION_TENSOR_INVALID")
    ligand_mask = _require_tensor(
        carrier.model_input_batch["lig_mask"], name="lig_mask", dtype=torch.long, ndim=1
    )
    pocket_mask = _require_tensor(
        carrier.model_input_batch["pocket_mask"], name="pocket_mask", dtype=torch.long, ndim=1
    )
    expected_roles = torch.cat(tuple(_expected_roles(record) for record in records))
    if (
        not torch.equal(supervision.ligand_role_id, expected_roles)
        or not bool(supervision.ligand_role_valid.all().item())
    ):
        _fail("LIGAND_ROLE_ID_OR_VALIDITY_INVALID")
    generated_roles_by_task = {row[0]: frozenset(row[3]) for row in CANONICAL_TASKS_V1}
    expected_generation = torch.tensor(
        tuple(
            int(expected_roles[index].item()) in generated_roles_by_task[task_ids[int(ligand_mask[index].item())]]
            for index in range(len(ligand_mask))
        ),
        dtype=torch.bool,
    ).unsqueeze(1)
    generation = supervision.ligand_base_generation_mask
    fixed = supervision.ligand_base_fixed_mask
    if (
        generation.dtype != torch.bool
        or fixed.dtype != torch.bool
        or generation.shape != (len(ligand_mask), 1)
        or fixed.shape != generation.shape
        or not torch.equal(generation, expected_generation)
        or bool((generation & fixed).any().item())
        or not bool((generation | fixed).all().item())
        or not torch.equal(supervision.ligand_base_target_mask, generation)
        or not torch.equal(supervision.ligand_base_context_mask, fixed)
    ):
        _fail("GENERATION_FIXED_OR_TASK_ROLE_CONTRACT_INVALID")
    expected_active = generation & supervision.canonical_task_valid[ligand_mask].unsqueeze(1)
    expected_active &= supervision.sample_training_admitted[ligand_mask].unsqueeze(1)
    if not torch.equal(supervision.ligand_active_diffusion_loss_mask, expected_active):
        _fail("ACTIVE_DIFFUSION_MASK_INVALID")
    if (
        bool(supervision.ligand_minimal_seed_or_anchor_mask.any().item())
        or bool(supervision.ligand_minimal_seed_or_anchor_valid.any().item())
        or any(record.minimal_seed_authority_available for record in records)
    ):
        _fail("UNAVAILABLE_MINIMAL_SEED_WAS_UPGRADED")

    for sample, record in enumerate(records):
        pocket_nodes = torch.nonzero(pocket_mask == sample, as_tuple=False).flatten()
        expected_members = torch.zeros(len(pocket_nodes), dtype=torch.bool)
        expected_members[list(record.target_cys_pocket_local_indices)] = True
        expected_reactive = torch.zeros(len(pocket_nodes), dtype=torch.bool)
        expected_reactive[record.target_sg_pocket_local_index] = True
        pocket_slice = slice(pocket_offsets[sample], pocket_offsets[sample + 1])
        if (
            not torch.equal(
                supervision.target_residue_membership_mask[pocket_slice, 0],
                expected_members,
            )
            or not torch.equal(
                supervision.target_residue_reactive_atom_mask[pocket_slice, 0],
                expected_reactive,
            )
            or int(supervision.target_residue_reactive_atom_local_index[sample].item())
            != record.target_sg_pocket_local_index
            or int(supervision.target_residue_reactive_atom_flat_index[sample].item())
            != int(pocket_nodes[record.target_sg_pocket_local_index].item())
        ):
            _fail("TARGET_CYS_SG_CONDITION_OR_MEMBERSHIP_INVALID")
        target_coordinate = carrier.model_input_batch["pocket_coords"][
            supervision.target_residue_reactive_atom_flat_index[sample]
        ]
        ligand_slice = slice(ligand_offsets[sample], ligand_offsets[sample + 1])
        expected_anchor = torch.linalg.vector_norm(
            carrier.model_input_batch["lig_coords"][ligand_slice] - target_coordinate,
            dim=1,
            keepdim=True,
        )
        if (
            not torch.allclose(
                supervision.ligand_anchor_distance_angstrom[ligand_slice],
                expected_anchor,
                rtol=0,
                atol=1e-6,
            )
            or not bool(supervision.ligand_anchor_distance_valid[ligand_slice].all().item())
        ):
            _fail("TASK_C_ANCHOR_DISTANCE_CONTRACT_INVALID")

    offsets = supervision.pair_candidate_offsets.tolist()
    candidate_count = len(supervision.pair_candidate_batch_index)
    if (
        len(offsets) != batch_size + 1
        or offsets[0] != 0
        or offsets[-1] != candidate_count
        or any(left >= right for left, right in zip(offsets, offsets[1:]))
    ):
        _fail("PAIR_OFFSETS_INVALID")
    candidate_fields = (
        supervision.pair_candidate_batch_index,
        supervision.pair_candidate_ligand_local_index,
        supervision.pair_candidate_residue_local_index,
        supervision.pair_candidate_ligand_flat_index,
        supervision.pair_candidate_pocket_flat_index,
        supervision.pair_candidate_is_positive,
    )
    if any(len(value) != candidate_count for value in candidate_fields):
        _fail("PAIR_CANDIDATE_LENGTH_INVALID")
    if (
        supervision.pre_post_geometry_target_angstrom.shape != (batch_size, 2)
        or supervision.pre_post_geometry_component_valid_mask.shape != (batch_size, 2)
        or supervision.pre_post_geometry_component_loss_mask.shape != (batch_size, 2)
        or not bool(torch.isnan(supervision.pre_post_geometry_target_angstrom[:, 0]).all().item())
        or bool(supervision.pre_post_geometry_component_valid_mask[:, 0].any().item())
        or bool(supervision.pre_post_geometry_component_loss_mask[:, 0].any().item())
        or not bool(torch.isfinite(supervision.pre_post_geometry_target_angstrom[:, 1]).all().item())
        or not bool(supervision.observed_complex_pair_distance_valid.all().item())
    ):
        _fail("PRE_POST_OR_DIAGNOSTIC_CONTRACT_INVALID")

    rows = []
    for sample, record in enumerate(records):
        start, end = offsets[sample : sample + 2]
        positive_index = int(supervision.pair_positive_candidate_index[sample].item())
        positive_valid = bool(supervision.pair_positive_candidate_valid[sample].item())
        if positive_index < start or positive_index >= end:
            _fail("POSITIVE_CANDIDATE_OUTSIDE_SAMPLE_OFFSETS")
        ligand_nodes = torch.nonzero(ligand_mask == sample, as_tuple=False).flatten()
        pocket_nodes = torch.nonzero(pocket_mask == sample, as_tuple=False).flatten()
        ligand_local = int(supervision.pair_candidate_ligand_local_index[positive_index].item())
        pocket_local = int(supervision.pair_candidate_residue_local_index[positive_index].item())
        ligand_flat = int(supervision.pair_candidate_ligand_flat_index[positive_index].item())
        pocket_flat = int(supervision.pair_candidate_pocket_flat_index[positive_index].item())
        if (
            ligand_local < 0
            or ligand_local >= len(ligand_nodes)
            or pocket_local < 0
            or pocket_local >= len(pocket_nodes)
            or int(ligand_nodes[ligand_local].item()) != ligand_flat
            or int(pocket_nodes[pocket_local].item()) != pocket_flat
            or int(ligand_mask[ligand_flat].item()) != sample
            or int(pocket_mask[pocket_flat].item()) != sample
            or int(supervision.pair_candidate_batch_index[positive_index].item()) != sample
            or not bool(supervision.pair_candidate_is_positive[positive_index].item())
            or ligand_local != record.ligand_reactive_retained_local_index
            or pocket_local != record.target_sg_pocket_local_index
            or pocket_flat
            != int(supervision.target_residue_reactive_atom_flat_index[sample].item())
            or not bool(supervision.ligand_role_valid[ligand_flat].item())
            or int(supervision.ligand_role_id[ligand_flat].item()) != 2
        ):
            _fail("POSITIVE_PAIR_ENDPOINT_OR_INDEPENDENT_MEMBERSHIP_INVALID")
        generated = bool(generation[ligand_flat, 0].item())
        is_fixed = bool(fixed[ligand_flat, 0].item())
        post_request = bool(
            supervision.pre_post_geometry_component_loss_mask[sample, 1].item()
        )
        post_valid = bool(
            supervision.pre_post_geometry_component_valid_mask[sample, 1].item()
        )
        admitted = bool(supervision.sample_training_admitted[sample].item())
        task_valid = bool(supervision.canonical_task_valid[sample].item())
        target_valid = bool(supervision.target_residue_condition_valid[sample].item())
        exclusion_reasons = []
        for value, reason in (
            (post_request, "post_request_false"),
            (post_valid, "post_component_invalid"),
            (admitted, "sample_not_admitted"),
            (task_valid, "canonical_task_invalid"),
            (target_valid, "target_condition_invalid"),
            (positive_valid, "positive_pair_invalid"),
            (generated, "positive_endpoint_not_generated"),
            (not is_fixed, "positive_endpoint_fixed"),
        ):
            if not value:
                exclusion_reasons.append(reason)
        effective = not exclusion_reasons
        task_id = task_ids[sample]
        task = CANONICAL_TASKS_V1[task_id]
        if task_id == 3 and (
            generated
            or not is_fixed
            or not post_valid
            or not _is_finite_positive(
                float(supervision.pre_post_geometry_target_angstrom[sample, 1].item())
            )
        ):
            _fail("B3_FIXED_WARHEAD_POST_LABEL_PRESERVATION_INVALID")
        observed = float(
            supervision.observed_complex_pair_distance_angstrom[sample, 0].item()
        )
        target = float(supervision.pre_post_geometry_target_angstrom[sample, 1].item())
        if (
            not _is_finite_positive(observed)
            or abs(observed - target) > 1e-6
            or abs(target - record.post_reactive_pair_distance_angstrom) > 1e-6
        ):
            _fail("POST_TARGET_OR_OBSERVED_DIAGNOSTIC_INVALID")
        rows.append(CovapieBatch001HiddenPostEligibilityRowV1(
            formal_split=carrier.formal_split,
            epoch=carrier.epoch,
            canonical_event_id=record.canonical_event_id,
            canonical_task_id=task_id,
            canonical_task_semantic_name=task[1],
            canonical_task_display_alias=task[2],
            positive_endpoint_ligand_local_index=ligand_local,
            positive_endpoint_ligand_flat_index=ligand_flat,
            positive_endpoint_pocket_local_index=pocket_local,
            positive_endpoint_pocket_flat_index=pocket_flat,
            positive_endpoint_generated=generated,
            positive_endpoint_fixed=is_fixed,
            original_post_request=post_request,
            original_post_component_valid=post_valid,
            sample_training_admitted=admitted,
            canonical_task_valid=task_valid,
            target_condition_valid=target_valid,
            positive_pair_valid=positive_valid,
            preflight_effective_hidden_post_eligible=effective,
            exclusion_reasons=tuple(exclusion_reasons),
        ))
    if carrier.formal_split == "validation" and (
        bool(supervision.ligand_active_diffusion_loss_mask.any().item())
        or bool(supervision.pair_head_candidate_loss_mask.any().item())
        or bool(supervision.pair_contrastive_sample_loss_mask.any().item())
        or bool(supervision.pre_post_geometry_component_loss_mask.any().item())
    ):
        _fail("VALIDATION_TRAINING_LOSS_MASK_ACTIVE")
    return tuple(rows)


def _is_finite_positive(value: float) -> bool:
    return math.isfinite(value) and value > 0


def audit_covapie_batch001_feature_post_use_carrier_v1(
    carrier: object,
) -> tuple[str, tuple[CovapieBatch001HiddenPostEligibilityRowV1, ...]]:
    """Audit one already-built train or validation carrier without mutation."""

    try:
        if type(carrier) is not activation_owner.CovapieBatch001ModelUsableSplitBatchV1:
            _fail("CARRIER_TYPE_INVALID")
        before = _carrier_fingerprint(carrier)
        ligand_offsets, pocket_offsets = _validate_model_input_and_feature_boundary(carrier)
        rows = _validate_supervision_and_build_rows(
            carrier, ligand_offsets, pocket_offsets
        )
        after = _carrier_fingerprint(carrier)
        if before != after:
            _fail("CARRIER_MUTATED_BY_PREFLIGHT")
        return before, rows
    except BaseException as error:
        _public_error(error)


def _validate_split_index(
    payload: bytes,
) -> tuple[tuple[tuple[str, tuple[str, ...]], ...], tuple[tuple[str, tuple[str, ...]], ...]]:
    try:
        rows = tuple(csv.DictReader(io.StringIO(payload.decode("utf-8"), newline="")))
    except (UnicodeError, csv.Error) as error:
        raise _PreflightInvariantError("PUBLISHED_SPLIT_INDEX_INVALID") from error
    expected_ids = (
        ("train", activation_owner.FORMAL_TRAIN_EVENT_IDS_V1),
        ("validation", activation_owner.FORMAL_VALIDATION_EVENT_IDS_V1),
        ("test", activation_owner.FORMAL_TEST_EVENT_IDS_V1),
    )
    if len(rows) != 13 or len({row.get("canonical_event_id") for row in rows}) != 13:
        _fail("PUBLISHED_SPLIT_INDEX_POPULATION_INVALID")
    by_split = {
        split: tuple(row for row in rows if row.get("formal_split") == split)
        for split, _ids in expected_ids
    }
    observed_groups = []
    group_to_splits: dict[str, set[str]] = {}
    for split, ids in expected_ids:
        split_rows = by_split[split]
        if {row.get("canonical_event_id") for row in split_rows} != set(ids):
            _fail("PUBLISHED_SPLIT_EVENT_SET_INVALID:" + split)
        groups = tuple(dict.fromkeys(str(row.get("formal_leakage_group_id")) for row in split_rows))
        observed_groups.append((split, groups))
        for group in groups:
            group_to_splits.setdefault(group, set()).add(split)
        admitted = split == "train"
        for row in split_rows:
            component = row.get("ligand_component_id")
            expected_tasks = "0|3|4" if component == "PX5" else "0|1|2|3|4"
            if (
                row.get("split_admission_authoritative") != "true"
                or row.get("model_usable") != "true"
                or row.get("sample_training_admitted") != str(admitted).lower()
                or row.get("model_training_activation_authorized") != str(admitted).lower()
                or row.get("optimizer_population_eligible") != str(admitted).lower()
                or row.get("training_scheduler_eligible") != str(admitted).lower()
                or row.get("applicable_task_ids") != expected_tasks
                or (not admitted and row.get("training_scheduled_task_id") != "")
            ):
                _fail("PUBLISHED_SPLIT_ACTIVATION_OR_TASK_INVALID:" + split)
    if tuple(observed_groups) != _EXPECTED_GROUPS_V1 or any(
        len(splits) != 1 for splits in group_to_splits.values()
    ):
        _fail("PUBLISHED_LEAKAGE_GROUP_BOUNDARY_INVALID")
    return tuple(expected_ids), tuple(observed_groups)


def _build_carriers_v1(
    *, repository_root: Path, cache_root: Path
) -> tuple[
    activation_owner.CovapieBatch001FormalSplitAuthorityV1,
    tuple[activation_owner.CovapieBatch001ModelUsableSplitBatchV1, ...],
]:
    context = activation_owner._build_context(
        repository_root=repository_root, cache_root=cache_root
    )
    carriers = []
    for epoch in TASK_EPOCHS_V1:
        for split in ("train", "validation"):
            carriers.append(activation_owner._build_split_from_context(
                context=context,
                split=split,
                epoch=epoch,
                task_schedule_seed=TASK_SCHEDULE_SEED_V1,
            ))
    return context.authority, tuple(carriers)


def run_covapie_batch001_feature_post_use_preflight_v1(
    *, repository_root: object = None, cache_root: object = None
) -> CovapieBatch001FeaturePostUsePreflightResultV1:
    """Run the scoped real-carrier preflight without model or loss execution."""

    try:
        repo = _require_directory(
            repository_root,
            default=Path(__file__).resolve().parents[2],
            reason="REPOSITORY_ROOT_INVALID",
        )
        cache = _require_directory(
            cache_root,
            default=repo.parent / "covapie-state/bulk-multisource-cys-sg-v1/rcsb",
            reason="CACHE_ROOT_INVALID",
        )
        bindings = verify_covapie_batch001_feature_post_use_preflight_sources_v1(
            repository_root=repo
        )
        validate_covapie_batch001_feature_projection_policy_v1()
        split_ids, split_groups = _validate_split_index(
            _read_safe_file(repo / PUBLISHED_SPLIT_INDEX_V1)
        )
        authority, carriers = _build_carriers_v1(
            repository_root=repo, cache_root=cache
        )
        if (
            authority.train_event_ids != activation_owner.FORMAL_TRAIN_EVENT_IDS_V1
            or authority.validation_event_ids
            != activation_owner.FORMAL_VALIDATION_EVENT_IDS_V1
            or authority.test_event_ids != activation_owner.FORMAL_TEST_EVENT_IDS_V1
            or authority.formal_leakage_group_cross_split_violation_count != 0
            or authority.event_identity_intersection_counts
            != (("train_validation", 0), ("train_test", 0), ("validation_test", 0))
        ):
            _fail("FORMAL_SPLIT_AUTHORITY_INVALID")
        fingerprints = []
        all_rows = []
        summaries = []
        for carrier in carriers:
            fingerprint, rows = audit_covapie_batch001_feature_post_use_carrier_v1(
                carrier
            )
            fingerprints.append((carrier.formal_split, carrier.epoch, fingerprint))
            all_rows.extend(rows)
            summaries.append(CovapieBatch001HiddenPostEpochSummaryV1(
                formal_split=carrier.formal_split,
                epoch=carrier.epoch,
                canonical_task_ids=tuple(carrier.preview_tensorization_task_ids),
                effective_hidden_post_eligible_count=sum(
                    row.preflight_effective_hidden_post_eligible for row in rows
                ),
            ))
        train_counts = tuple(
            item.effective_hidden_post_eligible_count
            for item in summaries
            if item.formal_split == "train"
        )
        validation_counts = tuple(
            item.effective_hidden_post_eligible_count
            for item in summaries
            if item.formal_split == "validation"
        )
        if train_counts != EXPECTED_TRAIN_HIDDEN_POST_ELIGIBLE_COUNTS_V1:
            _fail("TRAIN_HIDDEN_POST_ELIGIBILITY_COUNT_MISMATCH:" + repr(train_counts))
        if validation_counts != (0, 0, 0, 0, 0):
            _fail("VALIDATION_HIDDEN_POST_ELIGIBILITY_MUST_BE_ZERO")
        if tuple(CANONICAL_TASKS_V1) != _EXPECTED_CANONICAL_TASKS_V1:
            _fail("CANONICAL_EXACT5_DRIFT")
        for sample in range(5):
            if {
                summaries[2 * epoch].canonical_task_ids[sample]
                for epoch in TASK_EPOCHS_V1
            } != set(range(5)):
                _fail("TRAIN5_FIVE_EPOCH_TASK_CYCLE_INCOMPLETE")
        if any(
            carrier.applicable_task_ids
            != tuple(
                (0, 3, 4) if record.ligand_component_id == "PX5" else (0, 1, 2, 3, 4)
                for record in carrier.structural_records
            )
            for carrier in carriers
            if carrier.formal_split == "validation"
        ):
            _fail("VALIDATION_PROFILE_TASK_DOMAIN_INVALID")
        result_values = dict(
            schema_version="covapie_batch001_feature_post_use_preflight_v1",
            task_id=TASK_ID_V1,
            pilot_post_purpose=PILOT_POST_PURPOSE_V1,
            source_bindings=bindings,
            split_event_ids=split_ids,
            split_leakage_groups=split_groups,
            carrier_fingerprints=tuple(fingerprints),
            hidden_post_rows=tuple(all_rows),
            hidden_post_epoch_summaries=tuple(summaries),
            train_hidden_post_eligible_counts=train_counts,
            validation_hidden_post_eligible_counts=validation_counts,
            exact10_channel_order=feature_owner.CHECKPOINT_CHANNEL_ORDER,
            exact5_semantic_names=tuple(row[1] for row in CANONICAL_TASKS_V1),
            actual_carrier_split_count=len(carriers),
            actual_carrier_event_epoch_count=len(all_rows),
            test_carrier_constructed=False,
            scoped_carrier_feature_preflight_pass=True,
            scoped_hidden_post_eligibility_preflight_pass=True,
            current_source_bindings_verified=True,
            current_source_differs_from_legacy_pins=True,
            current_interface_semantics_verified_statically=True,
            legacy_trainer_routing_updated=False,
            production_loss_gate_called=False,
            checkpoint_loaded=False,
            model_instantiated=False,
            model_or_loss_executed=False,
            parameter_update_performed_this_round=False,
            training_started=False,
            ready_for_training=False,
            feature_semantics_audit_required_later=True,
            step12d_is_only_smoke_legality_check=True,
        )
        digest = _sha256(_canonical_json_bytes(result_values))
        return CovapieBatch001FeaturePostUsePreflightResultV1(
            **result_values, summary_sha256=digest
        )
    except BaseException as error:
        _public_error(error)


def serialize_covapie_batch001_feature_post_use_preflight_result_v1(
    result: object,
) -> bytes:
    if type(result) is not CovapieBatch001FeaturePostUsePreflightResultV1:
        raise ValueError(BATCH001_FEATURE_POST_USE_PREFLIGHT_ERROR_V1)
    return _canonical_json_bytes(asdict(result))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=None)
    parser.add_argument("--cache-root", type=Path, default=None)
    arguments = parser.parse_args(argv)
    try:
        result = run_covapie_batch001_feature_post_use_preflight_v1(
            repository_root=arguments.repository_root,
            cache_root=arguments.cache_root,
        )
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1
    sys.stdout.buffer.write(
        serialize_covapie_batch001_feature_post_use_preflight_result_v1(result)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
