"""Read-only CPU reuse of two formally admitted, independently owned events.

Preparation builds the published Current11 eleven-sample runtime/authority
context and the existing-positive seven-event computation. Only the genuine
JUG 000003 and GJJ 6DI9/GJJ owner objects are returned. This is not train12.
"""

from __future__ import annotations

import copy
import csv
from dataclasses import dataclass, fields
import hashlib
import io
import json
from pathlib import Path
import subprocess
from typing import NoReturn

import torch

from covalent_ext import covapie_current11_legacy_train5_data_adapter_v1 as legacy
from covalent_ext import covapie_existing_positive_runtime_and_split_closure_v1 as positive
from covalent_ext import covapie_expanded_cys_sg_mixed_profile_tensorizer_v1 as mixed
from covalent_ext.covapie_current11_training_tensorizer_v1 import CANONICAL_TASKS_V1
from covalent_ext.covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1 import CHECKPOINT_CHANNEL_ORDER
from covalent_ext import covapie_train10_cpu_batch_composer_v1 as train10


ERROR_V1 = "COVAPIE_JUG_GJJ_READY2_DATA_ADAPTER_V1_ERROR"
TARGETS_V1 = (
    ("COVAPIE_CYS_SG_EVENT_V1:6BV5:A:CYS:353-:SG:B:JUG:CAG", "CYS_SG_SAMPLE_INDEX_000003", "COVAPIE_LEAKAGE_GROUP_000001"),
    ("COVAPIE_CYS_SG_EVENT_V1:6DI9:A:CYS:481-:SG:B:GJJ:C33", "6DI9/GJJ", "COVAPIE_EXPANSION_LEAKAGE_GROUP_29510E7F8D2A7A5F"),
)
TASK_NAMES_V1 = (
    "warhead_only", "linker_plus_warhead", "scaffold_plus_warhead",
    "scaffold_only", "scaffold_plus_linker_plus_warhead",
)
_BASE = "data/derived/covalent_small/covapie_existing_positive_runtime_and_split_closure_v1/"
_GJJ = "data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/6di9_gjj_approved_v1/samples/"
_PINS = {
    _BASE + "covapie_current_runtime_model_usable_positive_index_v1.csv": "5485305a750129e437ef68b43c758f9f0586add41fe54ee1d621b6c5bde62410",
    _BASE + "covapie_existing_positive_leakage_split_closure_inventory_v1.csv": "2f673a8ca76217af1517d8254de79799d4fea333d9892af13a3ab0eeb90d8259",
    _BASE + "covapie_existing_positive_runtime_binding_inventory_v1.csv": "b8a0f4c2bc8ca46141775f0a5fa54322d12db685b37c930659f6f4a1ca3b4052",
    _BASE + "covapie_existing_positive_runtime_and_split_closure_manifest_v1.json": "5a94d4a35a0cc7b5495175bd4e94e26ab2a8ba796ed59ea1e1e4695575936944",
    _GJJ + "8483b1e83aa8e1b6.materialized.json": "254b76c7c9da09d559adbb59489b39ed39d95934d34362dfe53cecbee28ed6bd",
    _GJJ + "8483b1e83aa8e1b6.tensorized.json": "d128d0d5da6bccfdb29c8d951cdae61c4d27618f974ede5fbba8716d795d7db6",
}
_EXPECTED_TASKS = (
    (0, "warhead_only", "A", (2,)),
    (1, "linker_plus_warhead", "B", (1, 2)),
    (2, "scaffold_plus_warhead", "B2", (0, 2)),
    (3, "scaffold_only", "B3", (0,)),
    (4, "scaffold_plus_linker_plus_warhead", "C", (0, 1, 2)),
)


def _fail(reason: str) -> NoReturn:
    raise ValueError(f"{ERROR_V1}:{reason}")


def _root(value: object, name: str) -> Path:
    if not isinstance(value, (Path, str)) or isinstance(value, bool):
        _fail(name + "_ROOT_INVALID")
    path = Path(value)
    if not path.is_absolute() or not path.is_dir() or path.resolve(strict=True) != path:
        _fail(name + "_ROOT_INVALID")
    return path


def _bound(repo: Path, name: str) -> bytes:
    expected = _PINS[name]
    path = repo / name
    if path.resolve(strict=True) != path or not path.is_file():
        _fail("SOURCE_NOT_REGULAR:" + name)
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != expected:
        _fail("SOURCE_SHA_DRIFT:" + name)
    blob = subprocess.run(("git", "show", f"HEAD:{name}"), cwd=repo,
                          stdin=subprocess.DEVNULL, capture_output=True, check=False)
    if blob.returncode or blob.stdout != payload:
        _fail("SOURCE_NOT_EQUAL_COMMITTED_HEAD:" + name)
    return payload


def _rows(payload: bytes) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""), strict=True)
    rows = list(reader)
    if not rows or reader.fieldnames is None or any(None in row for row in rows):
        _fail("PUBLISHED_CSV_INVALID")
    return rows


def _one(rows: list[dict[str, str]], event: str, sample: str) -> dict[str, str]:
    matches = [row for row in rows if row.get("canonical_event_id") == event]
    if len(matches) != 1 or matches[0].get("sample_identity") != sample:
        _fail("TARGET_EVENT_AND_NATIVE_IDENTITY_MISMATCH")
    return matches[0]


def _bindings(repo: Path) -> tuple[tuple[str, str], ...]:
    data = {name: _bound(repo, name) for name in _PINS}
    manifest = json.loads(data[_BASE + "covapie_existing_positive_runtime_and_split_closure_manifest_v1.json"])
    hashes = manifest.get("output_sha256_excluding_manifest", {})
    for name in tuple(_PINS)[:3]:
        if hashes.get(Path(name).name) != _PINS[name]:
            _fail("PUBLISHED_MANIFEST_OUTPUT_DRIFT")
    positives = _rows(data[_BASE + "covapie_current_runtime_model_usable_positive_index_v1.csv"])
    leakage = _rows(data[_BASE + "covapie_existing_positive_leakage_split_closure_inventory_v1.csv"])
    runtime = _rows(data[_BASE + "covapie_existing_positive_runtime_binding_inventory_v1.csv"])
    if tuple(CANONICAL_TASKS_V1) != _EXPECTED_TASKS or len(TASK_NAMES_V1) != 5:
        _fail("CANONICAL_EXACT5_DRIFT")
    if any(event in train10.TRAIN10_CANONICAL_EVENT_IDS_V1 or sample in train10.TRAIN10_SAMPLE_IDENTITIES_V1
           for event, sample, _group in TARGETS_V1):
        _fail("EXISTING_TRAIN10_EVENT_OR_IDENTITY_OVERLAP")
    train_groups = {row["leakage_group_id_after"] for row in leakage
                    if row.get("sample_identity") in train10.TRAIN10_SAMPLE_IDENTITIES_V1}
    if len(train_groups) != 3 or train_groups & {target[2] for target in TARGETS_V1}:
        _fail("EXISTING_TRAIN10_GROUP_CONFLICT")
    heldout_groups = {row["leakage_group_id_after"] for row in leakage
                      if row.get("formal_split_authoritative_after") == "true"
                      and row.get("formal_split_after") in ("validation", "test")}
    if heldout_groups & {target[2] for target in TARGETS_V1}:
        _fail("HELDOUT_GROUP_CONFLICT")
    for event, sample, group in TARGETS_V1:
        p, l = _one(positives, event, sample), _one(leakage, event, sample)
        if not (
            p["leakage_group_id"] == l["leakage_group_id_after"] == group
            and p["formal_split"] == l["formal_split_after"] == "train"
            and p["formal_split_authoritative"] == l["formal_split_authoritative_after"] == "true"
            and p["training_admission_readiness"] == l["training_admission_readiness"] == "FORMAL_TRAIN_ADMITTED"
            and p["runtime_binding_status"] == "CURRENT_RUNTIME_BINDING_CLOSED"
            and p["positive_authority_status"] == "FULL_POSITIVE_SUPERVISION_AUTHORITY"
            and p["role_authority_status"] == p["reactive_pair_authority_status"] == p["POST_authority_status"] == "authoritative"
            and p["PRE_authority_status"] == "unavailable_not_loss_eligible"
            and l["leakage_evidence_complete"] == "true"
            and l["split_membership_count"] == "1"
        ):
            _fail("FORMAL_ADMISSION_OR_SUPERVISION_DRIFT")
        group_splits = {row["formal_split_after"] for row in leakage
                        if row["leakage_group_id_after"] == group and row["formal_split_authoritative_after"] == "true"}
        if group_splits != {"train"}:
            _fail("GROUP_SPLIT_CONFLICT")
    gjj = _one(runtime, TARGETS_V1[1][0], TARGETS_V1[1][1])
    if (gjj["runtime_binding_status"] != "CURRENT_RUNTIME_BINDING_CLOSED"
        or tuple(json.loads(gjj["valid_task_ids_json"])) != tuple(range(5))
        or gjj["current_supervision_dataclass_field_count"] != "37"
        or gjj["failure_reasons_json"] != "[]"
        or gjj["POST_geometry_authoritative"] != "true"
        or gjj["PRE_loss_eligible"] != "false"):
        _fail("GJJ_PUBLISHED_RUNTIME_DOMAIN_DRIFT")
    tensorized = json.loads(data[_GJJ + "8483b1e83aa8e1b6.tensorized.json"])
    materialized = json.loads(data[_GJJ + "8483b1e83aa8e1b6.materialized.json"])
    if (tensorized.get("sample_identity") != TARGETS_V1[1][1]
        or materialized.get("candidate_identity") != TARGETS_V1[1][1]
        or tensorized.get("checkpoint_channel_order") != CHECKPOINT_CHANNEL_ORDER
        or tensorized.get("canonical_task_names") != list(TASK_NAMES_V1)):
        _fail("GJJ_APPROVED_PAYLOAD_BINDING_DRIFT")
    return tuple(sorted(_PINS.items()))


def _seal(prepared: Ready2PreparedV1) -> str:
    digest = hashlib.sha256(b"COVAPIE_READY2_NATIVE_CPU_PREPARED_V1\0")
    native = prepared._gjj
    legacy._digest_value(digest, (
        str(prepared._repo), str(prepared._state), str(prepared._cache),
        prepared._bindings, prepared._legacy._seal, native.canonical_event_id,
        native.sample_identity, native.payload, native.model_input_batch,
        tuple(getattr(native.supervision, field.name) for field in fields(native.supervision)),
        prepared._gjj_runtime_row, prepared._gjj_source_bindings,
    ))
    return digest.hexdigest()


class Ready2PreparedV1:
    """One opaque upstream prepare; the returned target count is exactly two."""

    __slots__ = ("_repo", "_state", "_cache", "_legacy", "_gjj", "_bindings",
                 "_gjj_runtime_row", "_gjj_source_bindings", "_seal")

    def __init__(self, *, repo: Path, state: Path, cache: Path, legacy_context: object,
                 gjj_native: object, bindings: object, gjj_runtime_row: object,
                 gjj_source_bindings: object) -> None:
        self._repo, self._state, self._cache = repo, state, cache
        self._legacy = legacy_context
        self._gjj = copy.deepcopy(gjj_native)
        self._bindings = bindings
        self._gjj_runtime_row = copy.deepcopy(gjj_runtime_row)
        self._gjj_source_bindings = copy.deepcopy(gjj_source_bindings)
        self._seal = _seal(self)

    @property
    def upstream_construction_scope(self) -> dict[str, int]:
        return {"current11_runtime_samples": 11, "positive_closure_runtime_samples": 7,
                "positive_closure_task_checks": 35, "positive_closure_default_task_builds": 7,
                "returned_target_events": 2}


@dataclass(frozen=True)
class Ready2EventTaskV1:
    canonical_event_id: str
    sample_identity: str
    formal_leakage_group_id: str
    formal_split: str
    canonical_task_name: str
    native_owner: str
    model_input_batch: dict[str, object]
    supervision: object
    source_bindings: tuple[tuple[str, str], ...]
    native_source_bindings: tuple[object, ...]
    upstream_construction_scope: dict[str, int]


def _validate(prepared: object) -> Ready2PreparedV1:
    if type(prepared) is not Ready2PreparedV1:
        _fail("PREPARED_TYPE_INVALID")
    legacy._validate_prepared(prepared._legacy)
    if prepared._gjj.canonical_event_id != TARGETS_V1[1][0] or prepared._gjj.sample_identity != TARGETS_V1[1][1]:
        _fail("GJJ_NATIVE_IDENTITY_DRIFT")
    if not prepared._gjj_source_bindings or any(type(binding) is not dict or not binding.get("sha256")
                                                for binding in prepared._gjj_source_bindings):
        _fail("GJJ_NATIVE_SOURCE_BINDINGS_INVALID")
    positive.validate_runtime_adapter_payload_v1(prepared._gjj.payload)
    if _seal(prepared) != prepared._seal:
        _fail("PREPARED_OR_NATIVE_OBJECT_MUTATED")
    return prepared


def prepare_covapie_jug_gjj_ready2_data_adapter_v1(
    *, repository_root: object, state_root: object, cache_root: object,
) -> Ready2PreparedV1:
    """Verify committed admission then reuse full, read-only native contexts once."""

    repo, state, cache = (_root(repository_root, "REPOSITORY"),
                          _root(state_root, "STATE"), _root(cache_root, "CACHE"))
    if state != repo.parent / "covapie-state" or cache != state / "bulk-multisource-cys-sg-v1/rcsb":
        _fail("EXPLICIT_ROOT_RELATIONSHIP_INVALID")
    bindings = _bindings(repo)
    old = legacy.prepare_covapie_current11_legacy_train5_data_adapter_v1(repo, state)
    computed = positive.compute_covapie_existing_positive_runtime_and_split_closure_v1(repository_root=repo)
    sample = [item for item in computed.runtime_samples if item.canonical_event_id == TARGETS_V1[1][0]]
    rows = [item for item in computed.runtime_binding_rows if item["canonical_event_id"] == TARGETS_V1[1][0]]
    if len(sample) != 1 or len(rows) != 1 or sample[0].sample_identity != TARGETS_V1[1][1]:
        _fail("GJJ_OWNER_COMPUTATION_NOT_EXACTLY_ONE")
    positive.validate_runtime_adapter_payload_v1(sample[0].payload)
    published = _one(_rows(_bound(repo, _BASE + "covapie_existing_positive_runtime_binding_inventory_v1.csv")), *TARGETS_V1[1][:2])
    if rows[0] != published or positive._runtime_row(sample[0]) != published:
        _fail("GJJ_OWNER_RUNTIME_ROW_DIFFERS_FROM_PUBLISHED")
    if not any(row["canonical_event_id"] == TARGETS_V1[1][0]
               and row["training_admission_readiness"] == "FORMAL_TRAIN_ADMITTED"
               and row["formal_split_after"] == "train"
               and row["leakage_group_id_after"] == TARGETS_V1[1][2]
               for row in computed.leakage_split_rows):
        _fail("GJJ_OWNER_FORMAL_SPLIT_MISMATCH")
    if old._authoritative_supervision["sample_keys"][2] != TARGETS_V1[0][1]:
        _fail("JUG_NATIVE_CONTEXT_IDENTITY_MISMATCH")
    if not computed.counts["runtime_binding_closed_event_count"] == 7 or len(computed.runtime_samples) != 7:
        _fail("POSITIVE_OWNER_CONSTRUCTION_SCOPE_MISMATCH")
    if _bindings(repo) != bindings:
        _fail("SOURCE_CHANGED_DURING_PREPARE")
    return Ready2PreparedV1(repo=repo, state=state, cache=cache,
                            legacy_context=old, gjj_native=sample[0], bindings=bindings,
                            gjj_runtime_row=rows[0], gjj_source_bindings=computed.source_bindings)


def build_covapie_jug_gjj_ready2_canonical_task_data_v1(
    prepared: object, *, canonical_event_id: object, canonical_task_name: object,
) -> Ready2EventTaskV1:
    """Return exactly one owner-generated CPU singleton; names are semantic."""

    valid = _validate(prepared)
    if canonical_task_name not in TASK_NAMES_V1 or type(canonical_task_name) is not str:
        _fail("CANONICAL_TASK_NOT_IN_EXACT5")
    if type(canonical_event_id) is not str or canonical_event_id not in (TARGETS_V1[0][0], TARGETS_V1[1][0]):
        _fail("NON_TARGET_EVENT_REJECTED")
    if _bindings(valid._repo) != valid._bindings:
        _fail("FORMAL_SOURCE_CHANGED_SINCE_PREPARE")
    task_id = next(task[0] for task in CANONICAL_TASKS_V1 if task[1] == canonical_task_name)
    if canonical_event_id == TARGETS_V1[0][0]:
        old = valid._legacy
        runtime_batch = copy.deepcopy(old._runtime_batch)
        authority = copy.deepcopy(old._authoritative_supervision)
        legacy._validate_runtime_and_authority(runtime_batch, authority)
        native = mixed.tensorize_covapie_expanded_cys_sg_sample_v1(
            sample_identity=TARGETS_V1[0][1], task_id=task_id, device="cpu",
            epoch=None, task_schedule_seed=0, current11_batch=runtime_batch,
            current11_runtime_result=runtime_batch[legacy._SIDECAR_FIELD],
            current11_authoritative_supervision=authority,
        )
        model, supervision, owner = native.model_input_batch, native.supervision, "CURRENT11_MIXED_PROFILE_TENSORIZER_V1"
        if native.sample_identity != TARGETS_V1[0][1] or native.valid_task_ids != tuple(range(5)):
            _fail("JUG_NATIVE_TENSORIZER_IDENTITY_OR_TASK_DOMAIN_INVALID")
        target = TARGETS_V1[0]
        native_bindings = tuple((binding.root, binding.relative_path, binding.byte_count, binding.sha256)
                                for binding in old.source_bindings)
    else:
        sample = copy.deepcopy(valid._gjj)
        positive.validate_runtime_adapter_payload_v1(sample.payload)
        if positive._runtime_row(sample) != valid._gjj_runtime_row:
            _fail("GJJ_NATIVE_ROW_MUTATED")
        model, supervision = positive._model_batch_and_supervision(
            sample.payload, task_id=task_id, training_admitted=True,
        )
        positive._validate_training_mask_activation_v1(supervision, training_admitted=True)
        owner, target = "EXISTING_POSITIVE_RUNTIME_SPLIT_CLOSURE_V1", TARGETS_V1[1]
        native_bindings = copy.deepcopy(valid._gjj_source_bindings)
    if not bool(supervision.sample_training_admitted.item()) or int(supervision.canonical_task_id.item()) != task_id:
        _fail("OWNER_TASK_OR_ADMISSION_MISMATCH")
    if model["names"] != [target[1]] or any(value.device.type != "cpu" for value in model.values() if isinstance(value, torch.Tensor)):
        _fail("MODEL_BATCH_NATIVE_IDENTITY_OR_DEVICE_INVALID")
    if _seal(valid) != valid._seal:
        _fail("NATIVE_CONTEXT_CHANGED_DURING_BUILD")
    return Ready2EventTaskV1(target[0], target[1], target[2], "train", canonical_task_name,
                             owner, model, supervision, valid._bindings, native_bindings,
                             valid.upstream_construction_scope)
