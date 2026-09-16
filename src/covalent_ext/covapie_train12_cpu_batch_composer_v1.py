"""Independent, source-bound train12 CPU data carrier; no model or training.

The published train10 carrier remains a complete first source block. JUG and
GJJ remain READY2 native objects; only their approved core enters model input.
Validation takes the original prepared context to compare the two new blocks
against freshly built owner objects, not merely against a recomputed seal.
"""

from __future__ import annotations

import copy
import hashlib
import math
import stat
import subprocess
from dataclasses import dataclass, fields, is_dataclass, replace
from pathlib import Path
from typing import NoReturn

import torch

from covalent_ext import covapie_train10_cpu_batch_composer_v1 as train10
from covalent_ext import covapie_jug_gjj_ready2_data_adapter_v1 as ready2
from covalent_ext import covapie_direct_attachment_optional_linker_runtime_v1 as roles
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CANONICAL_TASKS_V1,
    CovapieCurrent11TrainingSupervisionTensorsV1,
    canonical_task_id_for_covapie_current11_sample_v1,
)

__all__ = (
    "TRAIN12_CPU_BATCH_COMPOSER_ERROR_V1",
    "TRAIN12_SAMPLE_IDENTITIES_V1",
    "TRAIN12_CANONICAL_EVENT_IDS_V1",
    "CovapieTrain12CpuBatchPreparedV1",
    "CovapieTrain12SchedulerBindingV1",
    "CovapieTrain12SourceBlockV1",
    "CovapieTrain12CpuEpochBatchV1",
    "prepare_covapie_train12_cpu_batch_composer_v1",
    "build_covapie_train12_cpu_epoch_batch_v1",
    "validate_covapie_train12_cpu_epoch_batch_v1",
)

TRAIN12_CPU_BATCH_COMPOSER_ERROR_V1 = "COVAPIE_TRAIN12_CPU_BATCH_COMPOSER_V1_ERROR"
TRAIN12_CPU_BATCH_SCHEMA_V1 = "covapie_train12_cpu_epoch_batch_v1"
_PREPARED_SCHEMA_V1 = "covapie_train12_cpu_batch_composer_prepared_v1"
TRAIN12_SAMPLE_IDENTITIES_V1 = train10.TRAIN10_SAMPLE_IDENTITIES_V1 + tuple(
    target[1] for target in ready2.TARGETS_V1
)
TRAIN12_CANONICAL_EVENT_IDS_V1 = train10.TRAIN10_CANONICAL_EVENT_IDS_V1 + tuple(
    target[0] for target in ready2.TARGETS_V1
)
_ROOT_DOMAIN = b"COVAPIE_TRAIN12_CPU_BATCH_COMPOSER_V1\0"
_TOKEN = object()
_SOURCE_SPECS = (
    ("src/covalent_ext/covapie_train10_cpu_batch_composer_v1.py", 72926,
     "5c5e7fee4804586e0c6d2a9bdf39a301dd154da92ff2d029f971d6b2b77d2ddd"),
    ("src/covalent_ext/covapie_jug_gjj_ready2_data_adapter_v1.py", 17161,
     "d7f143341ed4bd4ad10f4c03e4273273beaa4dcbb8c4e99b7b0f5e725a81de6d"),
    ("src/covalent_ext/covapie_current11_training_tensorizer_v1.py", 39144,
     "9fdc3f7f101fab5e5e5452e3d8e9f9b0b1e6e5fa8254a261f36310a1dfd0b606"),
    ("src/covalent_ext/covapie_direct_attachment_optional_linker_runtime_v1.py", 37255,
     "434285a43fa0158e62d40f48ed95d137f5fd68ea9b00101cc20674025849c535"),
)
_EXPECTED_TASKS = (
    (0, "warhead_only", "A", (2,)),
    (1, "linker_plus_warhead", "B", (1, 2)),
    (2, "scaffold_plus_warhead", "B2", (0, 2)),
    (3, "scaffold_only", "B3", (0,)),
    (4, "scaffold_plus_linker_plus_warhead", "C", (0, 1, 2)),
)
_JUG_SIDE_FIELDS = frozenset((
    "covapie_current11_task2_runtime_result_v1",
    "covapie_current11_authoritative_training_supervision_v1",
))
_BLOCK_KINDS = ("PUBLISHED_TRAIN10_V1", "READY2_JUG_NATIVE_V1", "READY2_GJJ_NATIVE_V1")
_JUG_SCHEDULER = "CURRENT11_TENSORIZER_EXACT5_V1"
_GJJ_SCHEDULER = "DIRECT_ATTACHMENT_ROLE_PROFILE_VALID_TASK_SET_V1"


def _fail(reason: str) -> NoReturn:
    raise ValueError(f"{TRAIN12_CPU_BATCH_COMPOSER_ERROR_V1}:{reason}")


def _epoch_seed(epoch: object, seed: object) -> tuple[int, int]:
    if type(epoch) is not int or not 0 <= epoch <= 4 or type(seed) is not int or seed != 0:
        _fail("EPOCH_OR_SEED_OUTSIDE_CPU_V1_DOMAIN")
    return epoch, seed


def _verify_direct_helpers(repo: Path) -> tuple[tuple[str, int, str], ...]:
    for name, length, expected in _SOURCE_SPECS:
        path = repo / name
        try:
            metadata = path.stat()
            if (path.resolve(strict=True) != path or not stat.S_ISREG(metadata.st_mode)
                    or path.is_symlink()):
                _fail("HELPER_NOT_SAFE_REGULAR_FILE:" + name)
            payload = path.read_bytes()
            blob = subprocess.run(("git", "show", "HEAD:" + name), cwd=repo,
                                  stdin=subprocess.DEVNULL, capture_output=True, check=False)
        except OSError as error:
            raise ValueError(TRAIN12_CPU_BATCH_COMPOSER_ERROR_V1 + ":HELPER_UNAVAILABLE:" + name) from error
        if len(payload) != length or hashlib.sha256(payload).hexdigest() != expected or blob.returncode or blob.stdout != payload:
            _fail("PUBLISHED_HELPER_DRIFT:" + name)
    return _SOURCE_SPECS


def _assert_contracts() -> None:
    train10._assert_supervision_contract_v1()
    if (tuple(CANONICAL_TASKS_V1) != _EXPECTED_TASKS
            or ready2.TASK_NAMES_V1 != tuple(task[1] for task in _EXPECTED_TASKS)
            or len(TRAIN12_SAMPLE_IDENTITIES_V1) != 12
            or len(set(TRAIN12_SAMPLE_IDENTITIES_V1)) != 12
            or len(set(TRAIN12_CANONICAL_EVENT_IDS_V1)) != 12
            or len(set(target[2] for target in ready2.TARGETS_V1)) != 2
            or not set(train10.TRAIN10_CANONICAL_EVENT_IDS_V1).isdisjoint(
                target[0] for target in ready2.TARGETS_V1)):
        _fail("EXACT12_OR_EXACT5_POPULATION_DRIFT")


def _formal_groups(train_prepared: object, native_prepared: object) -> tuple[str, ...]:
    """Only inspect the owners' pinned published formal split scope."""
    repo = train_prepared.repository_root
    before = ready2._bindings(repo)
    binding, payload = train10._read_bound_source_v1(repo, train10._DIRECT_SOURCE_SPECS_V1[0])
    if binding != train_prepared.source_bindings[0] or before != native_prepared._bindings:
        _fail("FORMAL_SOURCE_BINDING_DRIFT")
    rows = train10._csv_rows_v1(payload)
    selected = {}
    for event, identity in zip(TRAIN12_CANONICAL_EVENT_IDS_V1, TRAIN12_SAMPLE_IDENTITIES_V1):
        matches = [row for row in rows if row["canonical_event_id"] == event]
        if (len(matches) != 1 or matches[0]["sample_identity"] != identity
                or matches[0]["formal_split_authoritative_after"] != "true"
                or matches[0]["formal_split_after"] != "train"
                or matches[0]["training_admission_readiness"] != "FORMAL_TRAIN_ADMITTED"
                or matches[0]["leakage_evidence_complete"] != "true"
                or matches[0]["split_membership_count"] != "1"):
            _fail("EVENT_FORMAL_SPLIT_OR_GROUP_INVALID")
        selected[event] = matches[0]["leakage_group_id_after"]
    groups = tuple(selected[event] for event in TRAIN12_CANONICAL_EVENT_IDS_V1)
    if (groups[:10] != train_prepared.leakage_group_ids
            or groups[10:] != tuple(target[2] for target in ready2.TARGETS_V1)
            or len(set(groups)) != 5
            or set(groups[:10]) & set(groups[10:])):
        _fail("FORMAL_FIVE_GROUP_BOUNDARY_INVALID")
    for group in set(groups):
        splits = {row["formal_split_after"] for row in rows
                  if row["leakage_group_id_after"] == group
                  and row["formal_split_authoritative_after"] == "true"}
        if splits != {"train"}:
            _fail("HELDOUT_GROUP_INTERSECTION")
    if ready2._bindings(repo) != before:
        _fail("FORMAL_SOURCE_CHANGED_DURING_CHECK")
    return groups


def _valid_native_domain(native: object) -> str:
    payload = native._gjj.payload
    profile = payload.get("role_profile")
    tasks = payload.get("valid_task_ids")
    if (profile != roles.STRICT_LINKER_PRESENT_V1
            or type(tasks) not in (list, tuple)
            or tuple(tasks) != tuple(range(5))
            or any(type(task) is not int for task in tasks)
            or tuple(roles.valid_canonical_task_ids_for_role_profile_v1(profile)) != tuple(tasks)
            or native._gjj_runtime_row.get("role_profile") != profile):
        _fail("GJJ_NATIVE_ROLE_PROFILE_OR_VALID_SET_INVALID")
    return profile


class CovapieTrain12CpuBatchPreparedV1:
    """Own both published prepared contexts, without exposing mutable epochs."""

    __slots__ = ("_repo", "_state", "_cache", "_train10", "_ready2",
                 "_groups", "_gjj_profile", "_helper_bindings", "_seal")

    def __init__(self, *, token: object, train_prepared: object, native_prepared: object,
                 groups: tuple[str, ...], gjj_profile: str) -> None:
        if token is not _TOKEN:
            _fail("PREPARED_CONSTRUCTION_NOT_AUTHORIZED")
        self._repo = train_prepared.repository_root
        self._state = train_prepared.state_root
        self._cache = train_prepared.cache_root
        self._train10 = train_prepared
        self._ready2 = native_prepared
        self._groups = groups
        self._gjj_profile = gjj_profile
        self._helper_bindings = _SOURCE_SPECS
        self._seal = _prepared_seal(self)

    @property
    def schema_version(self) -> str:
        return _PREPARED_SCHEMA_V1

    @property
    def sample_identities(self) -> tuple[str, ...]:
        return TRAIN12_SAMPLE_IDENTITIES_V1

    @property
    def canonical_event_ids(self) -> tuple[str, ...]:
        return TRAIN12_CANONICAL_EVENT_IDS_V1

    @property
    def leakage_group_ids(self) -> tuple[str, ...]:
        return self._groups

    @property
    def verified_distinct_leakage_group_count(self) -> int:
        return len(set(self._groups))

    @property
    def ready_for_training(self) -> bool:
        return False

    @property
    def feature_semantics_audit_required_later(self) -> bool:
        return True

    @property
    def step12d_is_only_smoke_legality_check(self) -> bool:
        return True


def _digest(domain: bytes, value: object) -> str:
    digest = hashlib.sha256(_ROOT_DOMAIN + domain + b"\0")
    train10._digest_value_v1(digest, value)
    return digest.hexdigest()


def _prepared_seal(value: CovapieTrain12CpuBatchPreparedV1) -> str:
    return _digest(b"PREPARED", (
        value._repo, value._state, value._cache, value._groups,
        value._gjj_profile, value._helper_bindings,
        train10._prepared_seal_v1(value._train10), ready2._seal(value._ready2),
    ))


def _validate_prepared(value: object) -> CovapieTrain12CpuBatchPreparedV1:
    if type(value) is not CovapieTrain12CpuBatchPreparedV1:
        _fail("PREPARED_TYPE_INVALID")
    _assert_contracts()
    _verify_direct_helpers(value._repo)
    try:
        train10._validate_prepared_v1(value._train10)
    except Exception as error:
        _fail("PUBLISHED_TRAIN10_PREPARED_INVALID:" + str(error))
    try:
        ready2._validate(value._ready2)
    except Exception as error:
        _fail("PUBLISHED_READY2_PREPARED_INVALID:" + str(error))
    if (value.schema_version != _PREPARED_SCHEMA_V1
            or (value._repo, value._state, value._cache) !=
            (value._train10.repository_root, value._train10.state_root, value._train10.cache_root)
            or (value._repo, value._state, value._cache) !=
            (value._ready2._repo, value._ready2._state, value._ready2._cache)
            or value._helper_bindings != _SOURCE_SPECS
            or value._gjj_profile != _valid_native_domain(value._ready2)
            or value._groups != _formal_groups(value._train10, value._ready2)
            or value._seal != _prepared_seal(value)):
        _fail("PREPARED_SOURCE_OR_MUTATION_SEAL_INVALID")
    return value


@dataclass(frozen=True)
class CovapieTrain12SchedulerBindingV1:
    scheduler_owner: str
    canonical_event_id: str
    identity_key: str
    role_profile: str
    valid_task_ids: tuple[int, ...]
    canonical_task_id: int


@dataclass(frozen=True)
class CovapieTrain12SourceBlockV1:
    source_kind: str
    sample_start: int
    sample_end: int
    native_owner: str
    sample_identities: tuple[str, ...]
    canonical_event_ids: tuple[str, ...]
    leakage_group_ids: tuple[str, ...]
    formal_splits: tuple[str, ...]
    scheduled_task_ids: tuple[int, ...]
    scheduler_binding: CovapieTrain12SchedulerBindingV1 | None
    native_source_bindings: tuple[object, ...]
    source_object: object
    core_snapshot: dict[str, object]
    supervision_snapshot: CovapieCurrent11TrainingSupervisionTensorsV1
    offsets_slpq: tuple[int, int, int, int]
    payload_sha256: str


def _block_seal(block: CovapieTrain12SourceBlockV1) -> str:
    return _digest(b"SOURCE_BLOCK", tuple(
        getattr(block, field.name) for field in fields(block) if field.name != "payload_sha256"
    ))


@dataclass(frozen=True)
class CovapieTrain12CpuEpochBatchV1:
    schema_version: str
    sample_identities: tuple[str, ...]
    canonical_event_ids: tuple[str, ...]
    leakage_group_ids: tuple[str, ...]
    formal_splits: tuple[str, ...]
    batch_positions: tuple[int, ...]
    role_profiles: tuple[str, ...]
    scheduled_task_ids: tuple[int, ...]
    epoch: int
    task_schedule_seed: int
    model_input_batch: dict[str, object]
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1
    source_audit_blocks: tuple[CovapieTrain12SourceBlockV1, ...]
    prepared_source_seal: str
    direct_helper_bindings: tuple[tuple[str, int, str], ...]
    training_session_active: bool
    model_consumer_integrated: bool
    datamodule_integrated: bool
    trainer_integrated: bool
    real_model_executed: bool
    parameter_update_performed: bool
    ready_for_training: bool
    feature_semantics_audit_required_later: bool
    step12d_is_only_smoke_legality_check: bool
    payload_sha256: str


def _batch_seal(batch: CovapieTrain12CpuEpochBatchV1) -> str:
    return _digest(b"BATCH", tuple(
        getattr(batch, field.name) for field in fields(batch) if field.name != "payload_sha256"
    ))


def _equal(left: object, right: object) -> bool:
    if isinstance(left, torch.Tensor) or isinstance(right, torch.Tensor):
        return isinstance(left, torch.Tensor) and isinstance(right, torch.Tensor) and train10._tensor_exact_v1(left, right)
    if type(left) is dict and type(right) is dict:
        return set(left) == set(right) and all(_equal(left[key], right[key]) for key in left)
    if type(left) in (tuple, list) and type(right) is type(left):
        return len(left) == len(right) and all(_equal(a, b) for a, b in zip(left, right))
    if type(left) is float and type(right) is float and math.isnan(left) and math.isnan(right):
        return True
    if type(left) is type(right) and is_dataclass(left) and not isinstance(left, type):
        return all(_equal(getattr(left, field.name), getattr(right, field.name))
                   for field in fields(left))
    return type(left) is type(right) and left == right


def _supervision_equal(left: object, right: object) -> bool:
    return (type(left) is CovapieCurrent11TrainingSupervisionTensorsV1
            and type(right) is type(left)
            and all(train10._tensor_exact_v1(getattr(left, field.name), getattr(right, field.name))
                    for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1)))


def _native_core(item: object, *, kind: str, identity: str) -> dict[str, object]:
    if type(item) is not dict:
        _fail("NATIVE_MODEL_INPUT_TYPE_INVALID")
    expected = set(train10._MODEL_CORE_FIELDS_V1)
    if kind == _BLOCK_KINDS[1]:
        expected |= set(_JUG_SIDE_FIELDS)
        if any(type(item.get(name)) is not dict for name in _JUG_SIDE_FIELDS):
            _fail("JUG_AUDIT_SIDECAR_MISSING_OR_INVALID")
    elif kind != _BLOCK_KINDS[2]:
        _fail("NON_NATIVE_SOURCE_KIND")
    if set(item) != expected:
        _fail("NATIVE_EXACT_FIELD_SET_OR_UNKNOWN_FIELD_INVALID")
    core = {name: train10._clone_value_v1(item[name]) for name in train10._MODEL_CORE_FIELDS_V1}
    try:
        train10._validate_model_core_v1(core, expected_names=(identity,))
    except train10._ComposerInvariantError as error:
        _fail("NATIVE_CORE_INVALID:" + error.reason)
    return core


def _validated_domains(model: object, supervision: object, *, names: tuple[str, ...]) -> None:
    try:
        train10._validate_collated_domains_v1(model, supervision, expected_names=names)
    except train10._ComposerInvariantError as error:
        _fail("COLLATED_DOMAIN_INVALID:" + error.reason)


def _schedule(prepared: CovapieTrain12CpuBatchPreparedV1, *, epoch: int,
              ordinal: int) -> CovapieTrain12SchedulerBindingV1:
    event, identity, _group = ready2.TARGETS_V1[ordinal]
    if ordinal == 0:
        task = canonical_task_id_for_covapie_current11_sample_v1(
            sample_key=identity, epoch=epoch, task_schedule_seed=0)
        owner, profile, domain = _JUG_SCHEDULER, roles.STRICT_LINKER_PRESENT_V1, tuple(range(5))
    else:
        profile = _valid_native_domain(prepared._ready2)
        domain = tuple(prepared._ready2._gjj.payload["valid_task_ids"])
        task = roles.canonical_task_id_for_valid_task_set_v1(
            sample_identity=identity, epoch=epoch, task_schedule_seed=0, valid_task_ids=domain)
        owner = _GJJ_SCHEDULER
    if type(task) is not int or task not in domain or domain != tuple(range(5)):
        _fail("NATIVE_EXACT5_SCHEDULE_DOMAIN_INVALID")
    return CovapieTrain12SchedulerBindingV1(owner, event, identity, profile, domain, task)


def _make_block(*, kind: str, start: int, source: object, core: dict[str, object],
                supervision: CovapieCurrent11TrainingSupervisionTensorsV1,
                scheduler: CovapieTrain12SchedulerBindingV1 | None,
                offsets: tuple[int, int, int, int], groups: tuple[str, ...]) -> CovapieTrain12SourceBlockV1:
    if kind == _BLOCK_KINDS[0]:
        count = 10
        owner = "PUBLISHED_TRAIN10_CPU_BATCH_COMPOSER_V1"
        identities, events, tasks = source.sample_identities, source.canonical_event_ids, source.scheduled_task_ids
        bindings = tuple(copy.deepcopy(source.direct_source_bindings + source.batch001_source_authority_bindings + source.legacy_source_bindings))
    else:
        count = 1
        owner = source.native_owner
        identities, events = (source.sample_identity,), (source.canonical_event_id,)
        tasks = (scheduler.canonical_task_id,)
        bindings = copy.deepcopy(source.native_source_bindings)
    block = CovapieTrain12SourceBlockV1(kind, start, start + count, owner,
              identities, events, groups[start:start + count], ("train",) * count,
              tasks, scheduler, bindings, copy.deepcopy(source),
              train10._clone_model_input_v1(core), train10._clone_supervision_v1(supervision),
              offsets, "")
    return replace(block, payload_sha256=_block_seal(block))


def _counts(model: dict[str, object], supervision: object) -> tuple[int, int, int, int]:
    return (len(model["names"]), len(model["lig_coords"]), len(model["pocket_coords"]),
            int(supervision.pair_candidate_offsets[-1].item()))


def _roundtrip(batch: CovapieTrain12CpuEpochBatchV1) -> None:
    """Inverse S/L/P/Q slices, then zero-tolerance NaN-aware source comparison."""
    model, sup = batch.model_input_batch, batch.supervision
    for block in batch.source_audit_blocks:
        s, l, p, q = block.offsets_slpq
        core, original = block.core_snapshot, block.supervision_snapshot
        ns, nl, np, nq = _counts(core, original)
        if block.sample_start != s or block.sample_end != s + ns:
            _fail("SOURCE_SAMPLE_OFFSET_INVALID")
        for key in train10._MODEL_SAMPLE_FIELDS_V1:
            observed = model[key][s:s + ns]
            if not _equal(observed, core[key]):
                _fail("SOURCE_SAMPLE_CORE_ROUNDTRIP:" + key)
        for key in train10._MODEL_LIGAND_FIELDS_V1:
            if not _equal(model[key][l:l + nl], core[key]):
                _fail("SOURCE_LIGAND_CORE_ROUNDTRIP:" + key)
        for key in train10._MODEL_POCKET_FIELDS_V1:
            if not _equal(model[key][p:p + np], core[key]):
                _fail("SOURCE_POCKET_CORE_ROUNDTRIP:" + key)
        if (not _equal(model["lig_mask"][l:l + nl] - s, core["lig_mask"])
                or not _equal(model["pocket_mask"][p:p + np] - s, core["pocket_mask"])):
            _fail("SOURCE_MEMBERSHIP_ROUNDTRIP")
        for name in train10._SAMPLE_SUPERVISION_FIELDS_V1:
            if not _equal(getattr(sup, name)[s:s + ns], getattr(original, name)):
                _fail("SOURCE_SAMPLE_SUPERVISION_ROUNDTRIP:" + name)
        for name in train10._LIGAND_SUPERVISION_FIELDS_V1:
            if not _equal(getattr(sup, name)[l:l + nl], getattr(original, name)):
                _fail("SOURCE_LIGAND_SUPERVISION_ROUNDTRIP:" + name)
        for name in train10._POCKET_SUPERVISION_FIELDS_V1:
            if not _equal(getattr(sup, name)[p:p + np], getattr(original, name)):
                _fail("SOURCE_POCKET_SUPERVISION_ROUNDTRIP:" + name)
        for name in train10._CANDIDATE_DIRECT_SUPERVISION_FIELDS_V1:
            if not _equal(getattr(sup, name)[q:q + nq], getattr(original, name)):
                _fail("SOURCE_CANDIDATE_SUPERVISION_ROUNDTRIP:" + name)
        index_expectations = (
            ("target_residue_reactive_atom_flat_index", slice(s, s + ns),
             train10._offset_valid_indices_v1(original.target_residue_reactive_atom_flat_index,
                 offset=p, valid=original.target_residue_condition_valid)),
            ("pair_candidate_batch_index", slice(q, q + nq), original.pair_candidate_batch_index + s),
            ("pair_candidate_ligand_flat_index", slice(q, q + nq), original.pair_candidate_ligand_flat_index + l),
            ("pair_candidate_pocket_flat_index", slice(q, q + nq), original.pair_candidate_pocket_flat_index + p),
            ("pair_positive_candidate_index", slice(s, s + ns),
             train10._offset_valid_indices_v1(original.pair_positive_candidate_index,
                 offset=q, valid=original.pair_positive_candidate_valid)),
            ("pair_candidate_offsets", slice(s, s + ns + 1), original.pair_candidate_offsets + q),
        )
        for name, segment, expected in index_expectations:
            if not _equal(getattr(sup, name)[segment], expected):
                _fail("SOURCE_SLPQ_REMAP_ROUNDTRIP:" + name)


def _validate_impl(batch: object, prepared: object) -> bool:
    valid = _validate_prepared(prepared)
    if type(batch) is not CovapieTrain12CpuEpochBatchV1:
        _fail("BATCH_TYPE_INVALID")
    epoch, seed = _epoch_seed(batch.epoch, batch.task_schedule_seed)
    if (batch.schema_version != TRAIN12_CPU_BATCH_SCHEMA_V1
            or batch.sample_identities != TRAIN12_SAMPLE_IDENTITIES_V1
            or batch.canonical_event_ids != TRAIN12_CANONICAL_EVENT_IDS_V1
            or batch.leakage_group_ids != valid._groups
            or batch.formal_splits != ("train",) * 12
            or batch.batch_positions != tuple(range(12))
            or len(batch.role_profiles) != 12
            or batch.role_profiles[10:] != (roles.STRICT_LINKER_PRESENT_V1, valid._gjj_profile)
            or batch.prepared_source_seal != valid._seal
            or batch.direct_helper_bindings != _SOURCE_SPECS
            or any((batch.training_session_active, batch.model_consumer_integrated,
                    batch.datamodule_integrated, batch.trainer_integrated,
                    batch.real_model_executed, batch.parameter_update_performed,
                    batch.ready_for_training))
            or not batch.feature_semantics_audit_required_later
            or not batch.step12d_is_only_smoke_legality_check
            or type(batch.source_audit_blocks) is not tuple
            or len(batch.source_audit_blocks) != 3):
        _fail("BATCH_POPULATION_SOURCE_OR_READINESS_INVALID")
    if batch.payload_sha256 != _batch_seal(batch):
        _fail("BATCH_OR_METADATA_MUTATION_SEAL_INVALID")
    first = batch.source_audit_blocks[0]
    if type(first) is not CovapieTrain12SourceBlockV1 or type(first.source_object) is not train10.CovapieTrain10CpuEpochBatchV1:
        _fail("TRAIN10_SOURCE_CARRIER_TYPE_INVALID")
    try:
        train10.validate_covapie_train10_cpu_epoch_batch_v1(first.source_object)
    except Exception as error:
        _fail("PUBLISHED_TRAIN10_CARRIER_INVALID:" + str(error))
    if (first.source_object.epoch != epoch or first.source_object.task_schedule_seed != seed
            or first.source_object.role_profiles != batch.role_profiles[:10]
            or first.source_object.scheduled_task_ids != batch.scheduled_task_ids[:10]):
        _fail("TRAIN10_SCHEDULE_OR_PROFILE_DRIFT")
    sources = []
    for ordinal, block in enumerate(batch.source_audit_blocks):
        if type(block) is not CovapieTrain12SourceBlockV1 or block.source_kind != _BLOCK_KINDS[ordinal]:
            _fail("SOURCE_BLOCK_KIND_INVALID")
        if ordinal == 0:
            source = first.source_object
            core = train10._clone_model_input_v1(source.model_input_batch)
            supervision = source.supervision
            owner = "PUBLISHED_TRAIN10_CPU_BATCH_COMPOSER_V1"
            scheduler = None
            identities, events, tasks = source.sample_identities, source.canonical_event_ids, source.scheduled_task_ids
            native_bindings = source.direct_source_bindings + source.batch001_source_authority_bindings + source.legacy_source_bindings
        else:
            scheduler = _schedule(valid, epoch=epoch, ordinal=ordinal - 1)
            name = _EXPECTED_TASKS[scheduler.canonical_task_id][1]
            source = ready2.build_covapie_jug_gjj_ready2_canonical_task_data_v1(
                valid._ready2, canonical_event_id=scheduler.canonical_event_id,
                canonical_task_name=name)
            core = _native_core(source.model_input_batch, kind=block.source_kind,
                                identity=scheduler.identity_key)
            supervision = source.supervision
            owner, native_bindings = source.native_owner, source.native_source_bindings
            identities, events, tasks = (source.sample_identity,), (source.canonical_event_id,), (scheduler.canonical_task_id,)
            if (source.canonical_task_name != name or source.formal_split != "train"
                    or source.formal_leakage_group_id != ready2.TARGETS_V1[ordinal - 1][2]):
                _fail("FRESH_READY2_NATIVE_OWNER_MISMATCH")
        if (block.sample_start != (0 if ordinal == 0 else 9 + ordinal)
                or block.sample_end != (10 if ordinal == 0 else 10 + ordinal)
                or block.sample_identities != identities or block.canonical_event_ids != events
                or block.leakage_group_ids != valid._groups[block.sample_start:block.sample_end]
                or block.formal_splits != ("train",) * len(identities)
                or block.native_owner != owner or block.scheduled_task_ids != tasks
                or block.scheduler_binding != scheduler
                or not _equal(block.native_source_bindings, native_bindings)
                or (ordinal and (type(block.source_object) is not ready2.Ready2EventTaskV1
                                 or not _equal(block.source_object, source)))
                or not _equal(block.core_snapshot, core)
                or not _supervision_equal(block.supervision_snapshot, supervision)):
            _fail("SOURCE_NATIVE_REFERENCE_OR_SNAPSHOT_EQUIVALENCE_INVALID")
        if block.payload_sha256 != _block_seal(block):
            _fail("SOURCE_BLOCK_MUTATION_SEAL_INVALID")
        _validated_domains(block.core_snapshot, block.supervision_snapshot, names=identities)
        sources.append((block.core_snapshot, block.supervision_snapshot))
    offsets = (0, 0, 0, 0)
    for block in batch.source_audit_blocks:
        if block.offsets_slpq != offsets:
            _fail("SOURCE_SLPQ_OFFSET_BOUNDARY_INVALID")
        offsets = tuple(a + b for a, b in zip(offsets, _counts(block.core_snapshot, block.supervision_snapshot)))
    if offsets[0] != 12:
        _fail("SOURCE_SAMPLE_TOTAL_INVALID")
    if tuple(task for block in batch.source_audit_blocks for task in block.scheduled_task_ids) != batch.scheduled_task_ids:
        _fail("THREE_SOURCE_TASK_SCHEDULE_NOT_PRESERVED")
    _validated_domains(batch.model_input_batch, batch.supervision,
                       names=TRAIN12_SAMPLE_IDENTITIES_V1)
    if (tuple(batch.supervision.canonical_task_id.tolist()) != batch.scheduled_task_ids
            or not bool(batch.supervision.canonical_task_valid.all().item())
            or not bool(batch.supervision.sample_training_admitted.all().item())):
        _fail("TASK_AND_NATIVE_ADMISSION_NOT_PRESERVED")
    _roundtrip(batch)
    if valid._seal != _prepared_seal(valid):
        _fail("PREPARED_MUTATED_DURING_VALIDATION")
    return True


def prepare_covapie_train12_cpu_batch_composer_v1(
    repository_root: object, state_root: object, cache_root: object,
) -> CovapieTrain12CpuBatchPreparedV1:
    """Exactly one train10 prepare and one READY2 prepare; upstream scopes overlap."""
    _assert_contracts()
    repo, state, cache = train10._roots(repository_root, state_root, cache_root)
    _verify_direct_helpers(repo)
    first = train10.prepare_covapie_train10_cpu_batch_composer_v1(repo, state, cache)
    second = ready2.prepare_covapie_jug_gjj_ready2_data_adapter_v1(
        repository_root=repo, state_root=state, cache_root=cache)
    groups = _formal_groups(first, second)
    profile = _valid_native_domain(second)
    result = CovapieTrain12CpuBatchPreparedV1(token=_TOKEN, train_prepared=first,
                          native_prepared=second, groups=groups, gjj_profile=profile)
    _validate_prepared(result)
    return result


def build_covapie_train12_cpu_epoch_batch_v1(
    prepared: object, epoch: object, task_schedule_seed: object = 0,
) -> CovapieTrain12CpuEpochBatchV1:
    """Compose three independent native CPU blocks; no source re-preparation."""
    epoch, seed = _epoch_seed(epoch, task_schedule_seed)
    valid = _validate_prepared(prepared)
    original_seal = valid._seal
    first = train10.build_covapie_train10_cpu_epoch_batch_v1(valid._train10, epoch, seed)
    train10.validate_covapie_train10_cpu_epoch_batch_v1(first)
    blocks = []
    core_first = train10._clone_model_input_v1(first.model_input_batch)
    blocks.append(_make_block(kind=_BLOCK_KINDS[0], start=0, source=first,
        core=core_first, supervision=first.supervision, scheduler=None,
        offsets=(0, 0, 0, 0), groups=valid._groups))
    offsets = _counts(core_first, first.supervision)
    for ordinal in range(2):
        scheduler = _schedule(valid, epoch=epoch, ordinal=ordinal)
        native = ready2.build_covapie_jug_gjj_ready2_canonical_task_data_v1(
            valid._ready2, canonical_event_id=scheduler.canonical_event_id,
            canonical_task_name=_EXPECTED_TASKS[scheduler.canonical_task_id][1])
        kind = _BLOCK_KINDS[ordinal + 1]
        core = _native_core(native.model_input_batch, kind=kind,
                            identity=scheduler.identity_key)
        _validated_domains(core, native.supervision, names=(scheduler.identity_key,))
        block = _make_block(kind=kind, start=10 + ordinal, source=native, core=core,
                   supervision=native.supervision, scheduler=scheduler,
                   offsets=offsets, groups=valid._groups)
        blocks.append(block)
        offsets = tuple(a + b for a, b in zip(offsets, _counts(core, native.supervision)))
    model, supervision = train10._collate_core_blocks_v1(tuple(
        (block.core_snapshot, block.supervision_snapshot) for block in blocks))
    result = CovapieTrain12CpuEpochBatchV1(
        TRAIN12_CPU_BATCH_SCHEMA_V1, TRAIN12_SAMPLE_IDENTITIES_V1,
        TRAIN12_CANONICAL_EVENT_IDS_V1, valid._groups, ("train",) * 12,
        tuple(range(12)), first.role_profiles + (roles.STRICT_LINKER_PRESENT_V1, valid._gjj_profile),
        first.scheduled_task_ids + tuple(block.scheduled_task_ids[0] for block in blocks[1:]),
        epoch, seed, model, supervision, tuple(blocks), original_seal,
        _SOURCE_SPECS, False, False, False, False, False, False, False,
        True, True, "")
    result = replace(result, payload_sha256=_batch_seal(result))
    _validate_impl(result, valid)
    if original_seal != _prepared_seal(valid):
        _fail("PREPARED_POLLUTED_BY_BUILD")
    return result


def validate_covapie_train12_cpu_epoch_batch_v1(
    batch: object, prepared: object,
) -> bool:
    """Check against both published owners, formal group scope, and all 37 fields."""
    return _validate_impl(batch, prepared)
