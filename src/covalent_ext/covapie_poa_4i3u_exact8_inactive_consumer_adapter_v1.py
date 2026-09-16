"""Source-bound inactive consumer adaptation for POA 4I3U Exact8.

This module derives five in-memory CPU views from one published Task-A B1
preview.  It maps the approved P/O1P seed only for Task C and converts the two
unavailable PRE/POST geometry placeholders to NaN.  It does not admit samples,
activate a loss, call a model, or create a training/runtime carrier.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, fields, is_dataclass, replace
import hashlib
import math
from pathlib import Path
import stat
import subprocess
from typing import Any, Mapping, NoReturn

import torch

from covalent_ext import (
    covapie_current11_training_tensorizer_v1 as tensorizer_owner,
)
from covalent_ext import (
    covapie_direct_attachment_optional_linker_runtime_v1 as role_owner,
)
from covalent_ext import (
    covapie_poa_4i3u_exact8_real_preview_evidence_v1 as b1_owner,
)
from covalent_ext import (
    covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1
    as ingestion_owner,
)
from covalent_ext import (
    covapie_poa_sample_level_effective_supervision_v1 as metadata_owner,
)


__all__ = (
    "POA4I3UExact8InactiveConsumerAdapterError",
    "POA4I3UExact8InactiveConsumerPreparedV1",
    "POA4I3UExact8InactiveConsumerPayloadV1",
    "POA4I3UExact8InactiveConsumerSummaryV1",
    "POA4I3UExact8SeedAnchorMappingV1",
    "prepare_covapie_poa_4i3u_exact8_inactive_consumer_adapter_v1",
    "build_covapie_poa_4i3u_exact8_inactive_consumer_payload_v1",
    "validate_covapie_poa_4i3u_exact8_inactive_consumer_payload_v1",
)


TASK_ID = "implement_covapie_poa_4i3u_exact8_inactive_consumer_adapter_v1"
SCHEMA_VERSION = "covapie_poa_4i3u_exact8_inactive_consumer_payload_v1"
PREPARED_SCHEMA_VERSION = (
    "covapie_poa_4i3u_exact8_inactive_consumer_prepared_context_v1"
)
RECORD_ROLE = (
    "POA_EXACT8_INACTIVE_CPU_CONSUMER_PAYLOAD_NOT_FORMAL_TRAINING_CARRIER"
)
ERROR_TOKEN = "COVAPIE_POA_4I3U_EXACT8_INACTIVE_CONSUMER_ADAPTER_V1_ERROR"
BASELINE_COMMIT = "e99f978e3357297bda7828ae59da71b3bd99ec20"
PUBLISHED_INGESTION_RESULT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1/"
    "poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1.json"
)
PUBLISHED_INGESTION_SEMANTIC_PROJECTION_SHA256 = (
    "5a43bfb6d98ac3895d0a4029a5c211653dc4837b1790075c4f384523f7b14e00"
)

CANONICAL_TASKS_V1 = (
    (0, "warhead_only", "A", 2, 5),
    (1, "linker_plus_warhead", "B", 3, 4),
    (2, "scaffold_plus_warhead", "B2", 6, 1),
    (3, "scaffold_only", "B3", 4, 3),
    (4, "scaffold_plus_linker_plus_warhead", "C", 7, 0),
)
CANONICAL_TASK_LONG_NAMES_V1 = tuple(row[1] for row in CANONICAL_TASKS_V1)
ALLOWED_CHANGED_SUPERVISION_FIELDS_V1 = frozenset(
    (
        "canonical_task_id",
        "ligand_base_generation_mask",
        "ligand_base_fixed_mask",
        "ligand_base_target_mask",
        "ligand_base_context_mask",
        "ligand_minimal_seed_or_anchor_mask",
        "ligand_minimal_seed_or_anchor_valid",
        "pre_post_geometry_target_angstrom",
    )
)
EXPECTED_SUPERVISION_FIELD_COUNT_V1 = 37
EXPECTED_UNCHANGED_SUPERVISION_FIELD_COUNT_V1 = 29
EXPECTED_EVENT_COUNT_V1 = 8
EXPECTED_LIGAND_COUNT_PER_EVENT_V1 = 7
EXPECTED_PAIR_COUNTS_V1 = (336, 8, 328)

# All direct owners and published snapshots are fixed to Git blobs obtained
# from BASELINE_COMMIT.  Transitive validation remains with the published
# ingestion and B1 owners.
SOURCE_SPECS_V1 = (
    (
        "published_seed_ingestion_owner",
        "src/covalent_ext/"
        "covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1.py",
        45222,
        "9d0b0c331184530913d36d4eff6b0c53d00be0508915ddf0e3807c9739d20e14",
        "a75f9b1d15a472f4ef238619f85a011a15941443",
    ),
    (
        "published_seed_ingestion_result",
        PUBLISHED_INGESTION_RESULT_RELATIVE.as_posix(),
        17716,
        "38e9537c92f01f36dbd4fa9fdae825d944f6148c6a694f18f60a41a88ef0b8c5",
        "93cb4a37ab3a38911e168480b1fb47d3d78a5a40",
    ),
    (
        "published_b1_owner",
        "src/covalent_ext/covapie_poa_4i3u_exact8_real_preview_evidence_v1.py",
        49717,
        "854dd063ac822d7b8e7ddad7a887ec9fd7c78645e09a2166bbc4d46b0ac01649",
        "2dbba7c5e800b609293750f626b01d5f2b064716",
    ),
    (
        "published_b1_result",
        "data/derived/covalent_small/"
        "covapie_poa_4i3u_exact8_real_preview_evidence_v1/"
        "poa_4i3u_exact8_real_preview_evidence_v1.json",
        1522292,
        "98d4ec2e0d8c6fc00816a70b5927240f437d7e8d64a0981751ddc93684906d40",
        "5fd595ca9923d4d6339446cf74d872a74ac78c23",
    ),
    (
        "sample_metadata_owner",
        "src/covalent_ext/covapie_poa_sample_level_effective_supervision_v1.py",
        42406,
        "f4656f414a5d31d5e967b39885dd5d89e9bf205135dbd29b3285e0d1e856367f",
        "747f3e830a63bd208914af64ac08cb9b4ed042c0",
    ),
    (
        "real_structure_preview_schema_owner",
        "src/covalent_ext/covapie_poa_exact16_real_structure_tensor_preview_v1.py",
        61559,
        "91b26dd9e0aae8cbda34c769cf98d766910b9b497f5ca1133105f8858072f989",
        "1048d229f119ec4ae9f4cafd5253a060702a948c",
    ),
    (
        "supervision_tensor_and_numeric_owner",
        "src/covalent_ext/covapie_current11_training_tensorizer_v1.py",
        39144,
        "9fdc3f7f101fab5e5e5452e3d8e9f9b0b1e6e5fa8254a261f36310a1dfd0b606",
        "567f3aacd8480a743353583753e657230f80f9a5",
    ),
    (
        "canonical_role_mask_owner",
        "src/covalent_ext/covapie_direct_attachment_optional_linker_runtime_v1.py",
        37255,
        "434285a43fa0158e62d40f48ed95d137f5fd68ea9b00101cc20674025849c535",
        "bf57bc8c6142efb782c916a85a017bb8ebf07ab8",
    ),
)

PERMISSION_BOUNDARY_V1 = (
    ("NEW_HUMAN_DECISION_CREATED", False),
    ("NEW_FORMAL_ADMISSION_CREATED", False),
    ("ACTIVE_TRAINING_CONSUMER_CONNECTED", False),
    ("CURRENT_TRAIN12_POPULATION_CHANGED", False),
    ("REAL_MODEL_EXECUTED", False),
    ("PARAMETER_UPDATE_PERFORMED", False),
    ("READY_FOR_TRAINING", False),
    ("FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER", True),
    ("STEP12D_IS_ONLY_SMOKE_LEGALITY_CHECK", True),
    ("RUNTIME_SEED_AUTHORITY_ACTIVATED", False),
)


class POA4I3UExact8InactiveConsumerAdapterError(ValueError):
    """Raised when a source, conversion, or inactive boundary is invalid."""


def _fail(reason: str) -> NoReturn:
    raise POA4I3UExact8InactiveConsumerAdapterError(
        f"{ERROR_TOKEN}:{reason}"
    )


@dataclass(frozen=True, slots=True)
class PinnedSourceBindingV1:
    role: str
    repository_relative_path: str
    byte_count: int
    sha256: str
    git_blob_sha1: str


@dataclass(frozen=True, slots=True)
class POA4I3UExact8SeedAnchorMappingV1:
    canonical_event_id: str
    sample_ordinal_0based: int
    ligand_offset_start_0based: int
    approved_seed_atom_ids: tuple[str, str]
    seed_model_sample_local_indices_0based: tuple[int, int]
    seed_model_flat_indices_0based: tuple[int, int]
    seed_source_atom_site_row_indices_0based: tuple[int, int]
    ligand_primary_anchor_atom_id: str
    primary_anchor_model_sample_local_index_0based: int
    primary_anchor_model_flat_index_0based: int
    protein_target_reactive_atom_id: str
    protein_target_reactive_atom_local_index_0based: int
    protein_target_reactive_atom_flat_index_0based: int
    ligand_anchor_distance_reference_semantics: str


@dataclass(frozen=True, slots=True)
class POA4I3UExact8InactiveConsumerSummaryV1:
    event_count: int
    event_task_coverage_count: int
    generated_count_per_event: tuple[int, ...]
    fixed_count_per_event: tuple[int, ...]
    seed_count_per_event: tuple[int, ...]
    geometry_nan_component_count: int
    geometry_valid_component_count: int
    geometry_loss_component_count: int
    pair_candidate_count: int
    pair_positive_count: int
    pair_negative_count: int
    total_pocket_node_count: int
    unchanged_supervision_field_count: int


@dataclass(frozen=True)
class POA4I3UExact8InactiveConsumerPreparedV1:
    schema_version: str
    repository_root: Path
    state_root: Path
    source_bindings: tuple[PinnedSourceBindingV1, ...]
    formal_decision_payload: bytes
    structure_payload_4i3u: bytes
    effective_supervision: metadata_owner.POASampleLevelEffectiveSupervisionResultV1
    published_ingestion_result: dict[str, object]
    base_preview: object
    source_validation_call_counts: tuple[tuple[str, int], ...]
    completeness_seal_sha256: str


@dataclass(frozen=True)
class POA4I3UExact8InactiveConsumerPayloadV1:
    schema_version: str
    record_role: str
    canonical_task_name: str
    canonical_task_alias: str
    canonical_task_id: int
    sample_identities: tuple[str, ...]
    canonical_task_ids: tuple[int, ...]
    structure_source_bindings: tuple[object, ...]
    source_bindings: tuple[PinnedSourceBindingV1, ...]
    prepared_completeness_seal_sha256: str
    ligand_node_offsets: tuple[int, ...]
    pocket_node_offsets: tuple[int, ...]
    ligand_reactive_atom_local_index: torch.Tensor
    ligand_reactive_atom_flat_index: torch.Tensor
    model_input_batch: dict[str, object]
    supervision: tensorizer_owner.CovapieCurrent11TrainingSupervisionTensorsV1
    seed_anchor_mappings: tuple[POA4I3UExact8SeedAnchorMappingV1, ...]
    summary: POA4I3UExact8InactiveConsumerSummaryV1
    permission_boundary: tuple[tuple[str, bool], ...]
    published_b1_reused: bool
    published_seed_ingestion_reused: bool
    local_task_c_seed_mapping_applied: bool
    nan_geometry_conversion_applied: bool
    formal_training_carrier_created: bool
    training_admission_created: bool
    active_training_consumer_connected: bool
    model_forward_executed: bool
    loss_executed: bool
    backward_executed: bool
    optimizer_created: bool
    optimizer_step_executed: bool
    trainer_fit_executed: bool
    training_performed: bool
    ready_for_training: bool


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _git_blob_sha1(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()  # noqa: S324


def _resolve_root(value: object, label: str) -> Path:
    if not isinstance(value, (str, Path)):
        _fail(label + "_PATH_REQUIRED")
    try:
        root = Path(value).resolve(strict=True)
    except OSError as error:
        raise POA4I3UExact8InactiveConsumerAdapterError(
            f"{ERROR_TOKEN}:{label}_RESOLUTION_FAILED"
        ) from error
    if not root.is_dir():
        _fail(label + "_DIRECTORY_REQUIRED")
    return root


def _git_output(repository_root: Path, *arguments: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repository_root), *arguments],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise POA4I3UExact8InactiveConsumerAdapterError(
            f"{ERROR_TOKEN}:BASELINE_GIT_LINEAGE_INVALID"
        ) from error
    return completed.stdout.strip()


def _read_regular_fixed_file(
    *, root: Path, relative: Path, byte_count: int, sha256: str, label: str
) -> bytes:
    if relative.is_absolute() or ".." in relative.parts:
        _fail(label + "_RELATIVE_PATH_INVALID")
    path = root / relative
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
        resolved.relative_to(root)
        if resolved != path.absolute() or not stat.S_ISREG(metadata.st_mode):
            _fail(label + "_REGULAR_NONSYMLINK_FILE_REQUIRED")
        payload = path.read_bytes()
    except (OSError, ValueError) as error:
        raise POA4I3UExact8InactiveConsumerAdapterError(
            f"{ERROR_TOKEN}:{label}_READ_FAILED"
        ) from error
    if len(payload) != byte_count or _sha256(payload) != sha256:
        _fail(label + "_SOURCE_IDENTITY_INVALID")
    return payload


def _fixed_source_bindings(
    repository_root: Path,
) -> tuple[PinnedSourceBindingV1, ...]:
    _git_output(
        repository_root,
        "merge-base",
        "--is-ancestor",
        BASELINE_COMMIT,
        "HEAD",
    )
    bindings: list[PinnedSourceBindingV1] = []
    for role, relative_text, byte_count, sha256, git_blob in SOURCE_SPECS_V1:
        relative = Path(relative_text)
        payload = _read_regular_fixed_file(
            root=repository_root,
            relative=relative,
            byte_count=byte_count,
            sha256=sha256,
            label="PINNED_REPOSITORY_SOURCE:" + relative_text,
        )
        if (
            _git_blob_sha1(payload) != git_blob
            or _git_output(
                repository_root,
                "rev-parse",
                f"{BASELINE_COMMIT}:{relative_text}",
            )
            != git_blob
        ):
            _fail("PINNED_BASELINE_BLOB_INVALID:" + relative_text)
        bindings.append(
            PinnedSourceBindingV1(
                role=role,
                repository_relative_path=relative_text,
                byte_count=byte_count,
                sha256=sha256,
                git_blob_sha1=git_blob,
            )
        )
    return tuple(bindings)


def _digest_update(hasher: Any, value: object) -> None:
    if value is None:
        hasher.update(b"N;")
    elif type(value) is bool:
        hasher.update(b"B1;" if value else b"B0;")
    elif type(value) is int:
        hasher.update(b"I" + str(value).encode("ascii") + b";")
    elif type(value) is float:
        if math.isnan(value):
            encoded = b"nan"
        elif math.isinf(value):
            encoded = b"+inf" if value > 0 else b"-inf"
        else:
            encoded = value.hex().encode("ascii")
        hasher.update(b"F" + encoded + b";")
    elif type(value) is str:
        payload = value.encode("utf-8")
        hasher.update(b"S" + str(len(payload)).encode("ascii") + b":" + payload)
    elif type(value) is bytes:
        hasher.update(b"Y" + str(len(value)).encode("ascii") + b":" + value)
    elif isinstance(value, Path):
        _digest_update(hasher, value.as_posix())
    elif isinstance(value, torch.Tensor):
        tensor = value.detach().contiguous()
        if tensor.device.type != "cpu":
            _fail("PREPARED_TENSOR_MUST_BE_CPU")
        hasher.update(b"T")
        _digest_update(hasher, str(tensor.dtype))
        _digest_update(hasher, str(tensor.device))
        _digest_update(hasher, tuple(tensor.shape))
        raw = tensor.numpy().tobytes(order="C")
        hasher.update(str(len(raw)).encode("ascii") + b":" + raw)
    elif is_dataclass(value) and not isinstance(value, type):
        hasher.update(b"D")
        _digest_update(hasher, type(value).__module__ + "." + type(value).__qualname__)
        for field in fields(value):
            _digest_update(hasher, field.name)
            _digest_update(hasher, getattr(value, field.name))
    elif isinstance(value, Mapping):
        if any(type(key) is not str for key in value):
            _fail("PREPARED_MAPPING_KEYS_MUST_BE_STRINGS")
        hasher.update(b"M")
        for key in sorted(value):
            _digest_update(hasher, key)
            _digest_update(hasher, value[key])
    elif type(value) in (tuple, list):
        hasher.update(b"Q" if type(value) is tuple else b"L")
        _digest_update(hasher, len(value))
        for item in value:
            _digest_update(hasher, item)
    else:
        _fail("PREPARED_SEAL_UNSUPPORTED_VALUE:" + type(value).__name__)


def _prepared_seal(
    prepared: POA4I3UExact8InactiveConsumerPreparedV1,
) -> str:
    hasher = hashlib.sha256()
    for field in fields(prepared):
        if field.name == "completeness_seal_sha256":
            continue
        _digest_update(hasher, field.name)
        _digest_update(hasher, getattr(prepared, field.name))
    return hasher.hexdigest()


def _validate_prepared(
    prepared: object,
) -> POA4I3UExact8InactiveConsumerPreparedV1:
    if type(prepared) is not POA4I3UExact8InactiveConsumerPreparedV1:
        _fail("EXACT_PREPARED_CONTEXT_TYPE_REQUIRED")
    if (
        prepared.schema_version != PREPARED_SCHEMA_VERSION
        or prepared.repository_root != prepared.repository_root.resolve(strict=True)
        or prepared.state_root != prepared.state_root.resolve(strict=True)
        or prepared.completeness_seal_sha256 != _prepared_seal(prepared)
        or prepared.source_validation_call_counts
        != (
            ("ingestion_load_and_compile_public", 1),
            ("ingestion_validate_public", 1),
            ("ingestion_validate_internal_source_recompile", 1),
            ("metadata_builder_public", 1),
            ("b1_assemble_public", 1),
            ("b1_validate_public", 1),
        )
    ):
        _fail("PREPARED_CONTEXT_COMPLETENESS_SEAL_INVALID")
    return prepared


def _task_row(task_name: object) -> tuple[int, str, str, int, int]:
    if type(task_name) is not str:
        _fail("CANONICAL_TASK_LONG_NAME_REQUIRED")
    matches = tuple(row for row in CANONICAL_TASKS_V1 if row[1] == task_name)
    if len(matches) != 1:
        _fail("CANONICAL_EXACT5_TASK_REQUIRED")
    return matches[0]


def _clone_value(value: object) -> object:
    if isinstance(value, torch.Tensor):
        return value.detach().clone()
    if type(value) is dict:
        return {key: _clone_value(item) for key, item in value.items()}
    if type(value) is list:
        return [_clone_value(item) for item in value]
    if type(value) is tuple:
        return tuple(_clone_value(item) for item in value)
    return copy.deepcopy(value)


def _tensor_exact(left: object, right: object) -> bool:
    if not isinstance(left, torch.Tensor) or not isinstance(right, torch.Tensor):
        return False
    if (
        left.dtype != right.dtype
        or left.device != right.device
        or tuple(left.shape) != tuple(right.shape)
    ):
        return False
    if left.is_floating_point():
        left_nan = torch.isnan(left)
        right_nan = torch.isnan(right)
        return bool(
            torch.equal(left_nan, right_nan)
            and torch.equal(left[~left_nan], right[~right_nan])
        )
    return bool(torch.equal(left, right))


def _value_exact(left: object, right: object) -> bool:
    if isinstance(left, torch.Tensor) or isinstance(right, torch.Tensor):
        return _tensor_exact(left, right)
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return (
            tuple(left) == tuple(right)
            and all(_value_exact(left[key], right[key]) for key in left)
        )
    if type(left) in (list, tuple):
        return len(left) == len(right) and all(
            _value_exact(a, b) for a, b in zip(left, right, strict=True)
        )
    return left == right


def _tensor_storage_isolated(left: torch.Tensor, right: torch.Tensor) -> bool:
    return left.numel() == 0 or left.data_ptr() != right.data_ptr()


def _ingestion_event_records(
    prepared: POA4I3UExact8InactiveConsumerPreparedV1,
) -> tuple[dict[str, object], ...]:
    try:
        projection = prepared.published_ingestion_result["semantic_projection"]
        records = projection["event_records"]  # type: ignore[index]
    except (KeyError, TypeError) as error:
        raise POA4I3UExact8InactiveConsumerAdapterError(
            f"{ERROR_TOKEN}:INGESTION_EVENT_RECORDS_INVALID"
        ) from error
    if type(records) is not list or len(records) != EXPECTED_EVENT_COUNT_V1:
        _fail("INGESTION_EXACT8_EVENT_RECORDS_REQUIRED")
    if any(type(record) is not dict for record in records):
        _fail("INGESTION_EVENT_RECORD_OBJECT_REQUIRED")
    return tuple(records)  # type: ignore[return-value]


def _seed_anchor_mapping_for_event(
    *,
    prepared: POA4I3UExact8InactiveConsumerPreparedV1,
    event_record: dict[str, object],
    sample: int,
    ligand_offsets: tuple[int, ...],
    pocket_offsets: tuple[int, ...],
    supervision: tensorizer_owner.CovapieCurrent11TrainingSupervisionTensorsV1,
) -> POA4I3UExact8SeedAnchorMappingV1:
    base = prepared.base_preview
    event_id = base.sample_identities[sample]
    if (
        event_record.get("canonical_event_id") != event_id
        or event_record.get("sample_ordinal_0based") != sample
        or event_record.get("minimal_seed_atom_ids") != ["P", "O1P"]
        or event_record.get("primary_anchor_atom_id") != "P"
    ):
        _fail("INGESTION_EVENT_SEED_IDENTITY_INVALID")
    mappings = event_record.get("seed_atom_mappings")
    primary = event_record.get("primary_anchor_mapping")
    if type(mappings) is not list or len(mappings) != 2 or type(primary) is not dict:
        _fail("INGESTION_EVENT_MAPPING_SCHEMA_INVALID")
    by_atom: dict[str, dict[str, object]] = {}
    for mapping in mappings:
        if type(mapping) is not dict or type(mapping.get("atom_id")) is not str:
            _fail("INGESTION_SEED_ATOM_MAPPING_INVALID")
        by_atom[mapping["atom_id"]] = mapping
    if tuple(by_atom) != ("P", "O1P"):
        _fail("INGESTION_SEED_ATOM_ORDER_INVALID")
    start = ligand_offsets[sample]
    end = ligand_offsets[sample + 1]
    if end - start != EXPECTED_LIGAND_COUNT_PER_EVENT_V1:
        _fail("LIGAND_EVENT_OFFSET_INVALID")
    local_indices: list[int] = []
    flat_indices: list[int] = []
    source_indices: list[int] = []
    for atom_id in ("P", "O1P"):
        mapping = by_atom[atom_id]
        local = mapping.get("model_sample_local_index_0based")
        parser_local = mapping.get("model_parser_local_index_0based")
        source = mapping.get("source_atom_site_row_index_0based")
        b1_flat = mapping.get("model_flat_index_0based")
        if any(type(value) is not int for value in (local, parser_local, source, b1_flat)):
            _fail("INGESTION_SEED_INDEX_EXACT_INT_REQUIRED")
        flat = start + local  # type: ignore[operator]
        if (
            not start <= flat < end
            or parser_local != local
            or int(base.model_input_batch["lig_parser_local_index"][flat].item())
            != local
            or int(base.model_input_batch["lig_source_row_index"][flat].item())
            != source
            or b1_flat != base.ligand_node_offsets[sample] + local  # type: ignore[operator]
        ):
            _fail("INGESTION_TO_CURRENT_BATCH_SEED_REMAP_INVALID")
        local_indices.append(local)  # type: ignore[arg-type]
        flat_indices.append(flat)
        source_indices.append(source)  # type: ignore[arg-type]
    if tuple(local_indices) != (6, 3):
        _fail("APPROVED_P_O1P_LOCAL_INDICES_INVALID")
    if (
        primary.get("atom_id") != "P"
        or primary.get("model_sample_local_index_0based") != local_indices[0]
        or primary.get("source_atom_site_row_index_0based") != source_indices[0]
    ):
        _fail("PRIMARY_ANCHOR_P_MAPPING_INVALID")
    target_local = int(
        supervision.target_residue_reactive_atom_local_index[sample].item()
    )
    target_flat = int(
        supervision.target_residue_reactive_atom_flat_index[sample].item()
    )
    if not pocket_offsets[sample] <= target_flat < pocket_offsets[sample + 1]:
        _fail("PROTEIN_TARGET_SG_CURRENT_BATCH_INDEX_INVALID")
    return POA4I3UExact8SeedAnchorMappingV1(
        canonical_event_id=event_id,
        sample_ordinal_0based=sample,
        ligand_offset_start_0based=start,
        approved_seed_atom_ids=("P", "O1P"),
        seed_model_sample_local_indices_0based=tuple(local_indices),  # type: ignore[arg-type]
        seed_model_flat_indices_0based=tuple(flat_indices),  # type: ignore[arg-type]
        seed_source_atom_site_row_indices_0based=tuple(source_indices),  # type: ignore[arg-type]
        ligand_primary_anchor_atom_id="P",
        primary_anchor_model_sample_local_index_0based=local_indices[0],
        primary_anchor_model_flat_index_0based=flat_indices[0],
        protein_target_reactive_atom_id="SG",
        protein_target_reactive_atom_local_index_0based=target_local,
        protein_target_reactive_atom_flat_index_0based=target_flat,
        ligand_anchor_distance_reference_semantics=(
            "EXISTING_OBSERVED_DISTANCE_TO_PROTEIN_TARGET_CYS_SG_NOT_TO_LIGAND_P"
        ),
    )


def _expected_masks(
    *,
    base: object,
    task_id: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    device = base.supervision.ligand_role_id.device
    total = base.ligand_node_offsets[-1]
    generation = torch.zeros((total, 1), dtype=torch.bool, device=device)
    for sample in range(EXPECTED_EVENT_COUNT_V1):
        start, end = base.ligand_node_offsets[sample : sample + 2]
        roles = base.supervision.ligand_role_id[start:end]
        scaffold = tuple(
            int(index) for index in torch.nonzero(roles == 0).flatten().tolist()
        )
        linker = tuple(
            int(index) for index in torch.nonzero(roles == 1).flatten().tolist()
        )
        warhead = tuple(
            int(index) for index in torch.nonzero(roles == 2).flatten().tolist()
        )
        try:
            mask = role_owner.build_mask_for_role_profile_v1(
                role_profile=role_owner.STRICT_LINKER_PRESENT_V1,
                canonical_task_id=task_id,
                scaffold_atoms=scaffold,
                linker_atoms=linker,
                warhead_atoms=warhead,
                num_ligand_atoms=end - start,
            )
        except Exception as error:
            raise POA4I3UExact8InactiveConsumerAdapterError(
                f"{ERROR_TOKEN}:PUBLISHED_ROLE_MASK_OWNER_REJECTED:"
                f"{type(error).__name__}:{error}"
            ) from error
        generation[start + torch.tensor(mask.masked_atoms, dtype=torch.long), 0] = True
    return generation, ~generation


def _summary(
    payload: POA4I3UExact8InactiveConsumerPayloadV1,
) -> POA4I3UExact8InactiveConsumerSummaryV1:
    supervision = payload.supervision
    generated: list[int] = []
    fixed: list[int] = []
    seeds: list[int] = []
    for sample in range(EXPECTED_EVENT_COUNT_V1):
        start, end = payload.ligand_node_offsets[sample : sample + 2]
        generated.append(
            int(supervision.ligand_base_generation_mask[start:end].sum().item())
        )
        fixed.append(int(supervision.ligand_base_fixed_mask[start:end].sum().item()))
        seeds.append(
            int(supervision.ligand_minimal_seed_or_anchor_mask[start:end].sum().item())
        )
    return POA4I3UExact8InactiveConsumerSummaryV1(
        event_count=EXPECTED_EVENT_COUNT_V1,
        event_task_coverage_count=EXPECTED_EVENT_COUNT_V1,
        generated_count_per_event=tuple(generated),
        fixed_count_per_event=tuple(fixed),
        seed_count_per_event=tuple(seeds),
        geometry_nan_component_count=int(
            torch.isnan(supervision.pre_post_geometry_target_angstrom).sum().item()
        ),
        geometry_valid_component_count=int(
            supervision.pre_post_geometry_component_valid_mask.sum().item()
        ),
        geometry_loss_component_count=int(
            supervision.pre_post_geometry_component_loss_mask.sum().item()
        ),
        pair_candidate_count=int(supervision.pair_candidate_is_positive.numel()),
        pair_positive_count=int(supervision.pair_candidate_is_positive.sum().item()),
        pair_negative_count=int(supervision.pair_candidate_is_negative.sum().item()),
        total_pocket_node_count=payload.pocket_node_offsets[-1],
        unchanged_supervision_field_count=EXPECTED_UNCHANGED_SUPERVISION_FIELD_COUNT_V1,
    )


def prepare_covapie_poa_4i3u_exact8_inactive_consumer_adapter_v1(
    *, repository_root: Path | str, state_root: Path | str
) -> POA4I3UExact8InactiveConsumerPreparedV1:
    """Load, source-revalidate, and assemble one reusable real Task-A preview."""

    try:
        repository = _resolve_root(repository_root, "REPOSITORY_ROOT")
        state = _resolve_root(state_root, "STATE_ROOT")
        if repository == state:
            _fail("REPOSITORY_AND_STATE_ROOT_MUST_DIFFER")
        source_bindings = _fixed_source_bindings(repository)
        published_ingestion_payload = _read_regular_fixed_file(
            root=repository,
            relative=PUBLISHED_INGESTION_RESULT_RELATIVE,
            byte_count=17716,
            sha256=SOURCE_SPECS_V1[1][3],
            label="PUBLISHED_INGESTION_RESULT",
        )
        ingestion_result = (
            ingestion_owner.load_and_compile_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1(
                repository_root=repository,
                state_root=state,
            )
        )
        ingestion_owner.validate_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1(
            result=ingestion_result,
            repository_root=repository,
            state_root=state,
        )
        serialized_ingestion = (
            ingestion_owner.serialize_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1(
                ingestion_result
            )
        )
        if (
            serialized_ingestion != published_ingestion_payload
            or ingestion_result.get("semantic_projection_sha256")
            != PUBLISHED_INGESTION_SEMANTIC_PROJECTION_SHA256
        ):
            _fail("PUBLISHED_INGESTION_BYTE_OR_SEMANTIC_PROJECTION_MISMATCH")

        formal_payload = _read_regular_fixed_file(
            root=state,
            relative=b1_owner.FORMAL_DECISION_STATE_RELATIVE,
            byte_count=b1_owner.FORMAL_DECISION_BYTE_COUNT,
            sha256=b1_owner.FORMAL_DECISION_SHA256,
            label="FORMAL_ROLE_DECISION",
        )
        structure_payload = _read_regular_fixed_file(
            root=state,
            relative=b1_owner.STRUCTURE_STATE_RELATIVE,
            byte_count=b1_owner.STRUCTURE_BYTE_COUNT,
            sha256=b1_owner.STRUCTURE_SHA256,
            label="4I3U_GZIP_STRUCTURE",
        )
        effective = (
            metadata_owner.build_covapie_poa_sample_level_effective_supervision_v1(
                formal_payload
            )
        )
        if not metadata_owner.validate_covapie_poa_sample_level_effective_supervision_v1(
            effective
        ):
            _fail("PUBLISHED_EFFECTIVE_SUPERVISION_VALIDATOR_REJECTED")
        preview = b1_owner.assemble_covapie_poa_4i3u_exact8_real_preview_evidence_v1(
            repository_root=repository,
            formal_decision_payload=formal_payload,
            effective_supervision=effective,
            structure_payloads_by_pdb={"4I3U": structure_payload},
        )
        if not b1_owner.validate_covapie_poa_4i3u_exact8_real_preview_evidence_v1(
            preview,
            repository_root=repository,
            formal_decision_payload=formal_payload,
            effective_supervision=effective,
            structure_payloads_by_pdb={"4I3U": structure_payload},
        ):
            _fail("PUBLISHED_B1_PUBLIC_VALIDATOR_REJECTED")
        if (
            tuple((row[0], row[1], row[2]) for row in CANONICAL_TASKS_V1)
            != tuple((row[0], row[1], row[2]) for row in b1_owner.CANONICAL_TASKS_V1)
            or tuple((row[0], row[1], row[2]) for row in CANONICAL_TASKS_V1)
            != tuple((row[0], row[1], row[2]) for row in tensorizer_owner.CANONICAL_TASKS_V1)
            or tuple(role_owner.valid_canonical_task_ids_for_role_profile_v1(
                role_owner.STRICT_LINKER_PRESENT_V1
            ))
            != tuple(range(5))
            or len(fields(tensorizer_owner.CovapieCurrent11TrainingSupervisionTensorsV1))
            != EXPECTED_SUPERVISION_FIELD_COUNT_V1
        ):
            _fail("PUBLISHED_EXACT5_OR_SUPERVISION_SCHEMA_DRIFT")
        unsealed = POA4I3UExact8InactiveConsumerPreparedV1(
            schema_version=PREPARED_SCHEMA_VERSION,
            repository_root=repository,
            state_root=state,
            source_bindings=source_bindings,
            formal_decision_payload=formal_payload,
            structure_payload_4i3u=structure_payload,
            effective_supervision=effective,
            published_ingestion_result=copy.deepcopy(ingestion_result),
            base_preview=preview,
            source_validation_call_counts=(
                ("ingestion_load_and_compile_public", 1),
                ("ingestion_validate_public", 1),
                ("ingestion_validate_internal_source_recompile", 1),
                ("metadata_builder_public", 1),
                ("b1_assemble_public", 1),
                ("b1_validate_public", 1),
            ),
            completeness_seal_sha256="",
        )
        prepared = replace(
            unsealed, completeness_seal_sha256=_prepared_seal(unsealed)
        )
        return _validate_prepared(prepared)
    except POA4I3UExact8InactiveConsumerAdapterError:
        raise
    except Exception as error:
        raise POA4I3UExact8InactiveConsumerAdapterError(
            f"{ERROR_TOKEN}:PUBLIC_PREPARE_REJECTED:{type(error).__name__}:{error}"
        ) from error


def build_covapie_poa_4i3u_exact8_inactive_consumer_payload_v1(
    *,
    prepared: POA4I3UExact8InactiveConsumerPreparedV1,
    canonical_task_name: str,
) -> POA4I3UExact8InactiveConsumerPayloadV1:
    """Derive one isolated inactive Exact8 view for a canonical long task name."""

    try:
        context = _validate_prepared(prepared)
        task_id, task_name, task_alias, _, _ = _task_row(canonical_task_name)
        base = context.base_preview
        generation, fixed = _expected_masks(base=base, task_id=task_id)
        values = {
            field.name: getattr(base.supervision, field.name).detach().clone()
            for field in fields(tensorizer_owner.CovapieCurrent11TrainingSupervisionTensorsV1)
        }
        values.update(
            {
                "canonical_task_id": torch.full(
                    (EXPECTED_EVENT_COUNT_V1,),
                    task_id,
                    dtype=torch.long,
                    device=generation.device,
                ),
                "ligand_base_generation_mask": generation,
                "ligand_base_fixed_mask": fixed,
                "ligand_base_target_mask": generation.clone(),
                "ligand_base_context_mask": fixed.clone(),
                "pre_post_geometry_target_angstrom": torch.full_like(
                    base.supervision.pre_post_geometry_target_angstrom,
                    float("nan"),
                ),
            }
        )
        event_records = _ingestion_event_records(context)
        seed_mask = values["ligand_minimal_seed_or_anchor_mask"]
        seed_valid = values["ligand_minimal_seed_or_anchor_valid"]
        if task_id == 4:
            seed_mask.zero_()
            seed_valid.fill_(True)
            for sample, event_record in enumerate(event_records):
                for mapping in event_record["seed_atom_mappings"]:  # type: ignore[index]
                    if mapping["atom_id"] in ("P", "O1P"):
                        local = mapping["model_sample_local_index_0based"]
                        seed_mask[base.ligand_node_offsets[sample] + local, 0] = True
        else:
            seed_mask.zero_()
            seed_valid.zero_()
        supervision = tensorizer_owner.CovapieCurrent11TrainingSupervisionTensorsV1(
            **values
        )
        mappings = tuple(
            _seed_anchor_mapping_for_event(
                prepared=context,
                event_record=record,
                sample=sample,
                ligand_offsets=base.ligand_node_offsets,
                pocket_offsets=base.pocket_node_offsets,
                supervision=supervision,
            )
            for sample, record in enumerate(event_records)
        )
        placeholder_summary = POA4I3UExact8InactiveConsumerSummaryV1(
            event_count=0,
            event_task_coverage_count=0,
            generated_count_per_event=(),
            fixed_count_per_event=(),
            seed_count_per_event=(),
            geometry_nan_component_count=0,
            geometry_valid_component_count=0,
            geometry_loss_component_count=0,
            pair_candidate_count=0,
            pair_positive_count=0,
            pair_negative_count=0,
            total_pocket_node_count=0,
            unchanged_supervision_field_count=0,
        )
        payload = POA4I3UExact8InactiveConsumerPayloadV1(
            schema_version=SCHEMA_VERSION,
            record_role=RECORD_ROLE,
            canonical_task_name=task_name,
            canonical_task_alias=task_alias,
            canonical_task_id=task_id,
            sample_identities=tuple(base.sample_identities),
            canonical_task_ids=(task_id,) * EXPECTED_EVENT_COUNT_V1,
            structure_source_bindings=copy.deepcopy(base.structure_source_bindings),
            source_bindings=tuple(context.source_bindings),
            prepared_completeness_seal_sha256=context.completeness_seal_sha256,
            ligand_node_offsets=tuple(base.ligand_node_offsets),
            pocket_node_offsets=tuple(base.pocket_node_offsets),
            ligand_reactive_atom_local_index=(
                base.ligand_reactive_atom_local_index.detach().clone()
            ),
            ligand_reactive_atom_flat_index=(
                base.ligand_reactive_atom_flat_index.detach().clone()
            ),
            model_input_batch=_clone_value(base.model_input_batch),  # type: ignore[arg-type]
            supervision=supervision,
            seed_anchor_mappings=mappings,
            summary=placeholder_summary,
            permission_boundary=PERMISSION_BOUNDARY_V1,
            published_b1_reused=True,
            published_seed_ingestion_reused=True,
            local_task_c_seed_mapping_applied=(task_id == 4),
            nan_geometry_conversion_applied=True,
            formal_training_carrier_created=False,
            training_admission_created=False,
            active_training_consumer_connected=False,
            model_forward_executed=False,
            loss_executed=False,
            backward_executed=False,
            optimizer_created=False,
            optimizer_step_executed=False,
            trainer_fit_executed=False,
            training_performed=False,
            ready_for_training=False,
        )
        object.__setattr__(payload, "summary", _summary(payload))
        validate_covapie_poa_4i3u_exact8_inactive_consumer_payload_v1(
            payload=payload,
            prepared=context,
        )
        return payload
    except POA4I3UExact8InactiveConsumerAdapterError:
        raise
    except Exception as error:
        raise POA4I3UExact8InactiveConsumerAdapterError(
            f"{ERROR_TOKEN}:PUBLIC_BUILD_REJECTED:{type(error).__name__}:{error}"
        ) from error


def validate_covapie_poa_4i3u_exact8_inactive_consumer_payload_v1(
    *,
    payload: object,
    prepared: POA4I3UExact8InactiveConsumerPreparedV1,
) -> bool:
    """Validate source relation, exact field changes, and inactive semantics."""

    try:
        context = _validate_prepared(prepared)
        if type(payload) is not POA4I3UExact8InactiveConsumerPayloadV1:
            _fail("EXACT_INACTIVE_PAYLOAD_TYPE_REQUIRED")
        task_id, task_name, task_alias, generated_count, fixed_count = _task_row(
            payload.canonical_task_name
        )
        base = context.base_preview
        if (
            payload.schema_version != SCHEMA_VERSION
            or payload.record_role != RECORD_ROLE
            or payload.canonical_task_id != task_id
            or payload.canonical_task_alias != task_alias
            or payload.canonical_task_ids != (task_id,) * EXPECTED_EVENT_COUNT_V1
            or payload.sample_identities != base.sample_identities
            or payload.structure_source_bindings != base.structure_source_bindings
            or payload.source_bindings != context.source_bindings
            or payload.prepared_completeness_seal_sha256
            != context.completeness_seal_sha256
            or payload.ligand_node_offsets != base.ligand_node_offsets
            or payload.pocket_node_offsets != base.pocket_node_offsets
            or payload.permission_boundary != PERMISSION_BOUNDARY_V1
        ):
            _fail("PAYLOAD_HEADER_SOURCE_OR_OFFSET_INVALID")
        if not _tensor_exact(
            payload.ligand_reactive_atom_local_index,
            base.ligand_reactive_atom_local_index,
        ) or not _tensor_exact(
            payload.ligand_reactive_atom_flat_index,
            base.ligand_reactive_atom_flat_index,
        ):
            _fail("LIGAND_REACTIVE_INDEX_CHANGED")
        if not _tensor_storage_isolated(
            payload.ligand_reactive_atom_local_index,
            base.ligand_reactive_atom_local_index,
        ) or not _tensor_storage_isolated(
            payload.ligand_reactive_atom_flat_index,
            base.ligand_reactive_atom_flat_index,
        ):
            _fail("LIGAND_REACTIVE_INDEX_STORAGE_SHARED")
        if set(payload.model_input_batch) != set(base.model_input_batch):
            _fail("MODEL_INPUT_BATCH_SCHEMA_CHANGED")
        for name in base.model_input_batch:
            actual = payload.model_input_batch[name]
            expected = base.model_input_batch[name]
            if not _value_exact(actual, expected):
                _fail("MODEL_INPUT_BATCH_FIELD_CHANGED:" + name)
            if isinstance(actual, torch.Tensor) and not _tensor_storage_isolated(
                actual, expected
            ):
                _fail("MODEL_INPUT_BATCH_TENSOR_STORAGE_SHARED:" + name)
            if type(actual) is list and actual is expected:
                _fail("MODEL_INPUT_BATCH_LIST_STORAGE_SHARED:" + name)

        supervision = payload.supervision
        if type(supervision) is not tensorizer_owner.CovapieCurrent11TrainingSupervisionTensorsV1:
            _fail("EXISTING_37_FIELD_SUPERVISION_TYPE_REQUIRED")
        supervision_fields = fields(
            tensorizer_owner.CovapieCurrent11TrainingSupervisionTensorsV1
        )
        if (
            len(supervision_fields) != EXPECTED_SUPERVISION_FIELD_COUNT_V1
            or len(supervision_fields) - len(ALLOWED_CHANGED_SUPERVISION_FIELDS_V1)
            != EXPECTED_UNCHANGED_SUPERVISION_FIELD_COUNT_V1
        ):
            _fail("SUPERVISION_FIELD_COUNT_DRIFT")
        for field in supervision_fields:
            actual = getattr(supervision, field.name)
            expected = getattr(base.supervision, field.name)
            if not _tensor_storage_isolated(actual, expected):
                _fail("SUPERVISION_TENSOR_STORAGE_SHARED:" + field.name)
            if (
                field.name not in ALLOWED_CHANGED_SUPERVISION_FIELDS_V1
                and not _tensor_exact(actual, expected)
            ):
                _fail("UNAUTHORIZED_SUPERVISION_FIELD_CHANGED:" + field.name)

        expected_generation, expected_fixed = _expected_masks(
            base=base, task_id=task_id
        )
        if (
            not _tensor_exact(
                supervision.canonical_task_id,
                torch.full_like(base.supervision.canonical_task_id, task_id),
            )
            or not _tensor_exact(
                supervision.ligand_base_generation_mask, expected_generation
            )
            or not _tensor_exact(supervision.ligand_base_fixed_mask, expected_fixed)
            or not _tensor_exact(
                supervision.ligand_base_target_mask, expected_generation
            )
            or not _tensor_exact(
                supervision.ligand_base_context_mask, expected_fixed
            )
        ):
            _fail("CANONICAL_TASK_OR_ROLE_MASK_ADAPTATION_INVALID")
        for sample in range(EXPECTED_EVENT_COUNT_V1):
            start, end = payload.ligand_node_offsets[sample : sample + 2]
            if (
                int(supervision.ligand_base_generation_mask[start:end].sum().item())
                != generated_count
                or int(supervision.ligand_base_fixed_mask[start:end].sum().item())
                != fixed_count
            ):
                _fail("EVENT_TASK_MASK_COUNT_INVALID")

        expected_mappings = tuple(
            _seed_anchor_mapping_for_event(
                prepared=context,
                event_record=record,
                sample=sample,
                ligand_offsets=payload.ligand_node_offsets,
                pocket_offsets=payload.pocket_node_offsets,
                supervision=supervision,
            )
            for sample, record in enumerate(_ingestion_event_records(context))
        )
        if payload.seed_anchor_mappings != expected_mappings:
            _fail("SEED_PRIMARY_ANCHOR_METADATA_INVALID")
        expected_seed = torch.zeros_like(
            base.supervision.ligand_minimal_seed_or_anchor_mask
        )
        expected_seed_valid = torch.zeros_like(
            base.supervision.ligand_minimal_seed_or_anchor_valid
        )
        if task_id == 4:
            expected_seed_valid.fill_(True)
            for mapping in expected_mappings:
                expected_seed[list(mapping.seed_model_flat_indices_0based), 0] = True
        if (
            not _tensor_exact(
                supervision.ligand_minimal_seed_or_anchor_mask, expected_seed
            )
            or not _tensor_exact(
                supervision.ligand_minimal_seed_or_anchor_valid,
                expected_seed_valid,
            )
        ):
            _fail("TASK_C_ONLY_SEED_TENSOR_MAPPING_INVALID")

        geometry = supervision.pre_post_geometry_target_angstrom
        geometry_valid = supervision.pre_post_geometry_component_valid_mask
        geometry_loss = supervision.pre_post_geometry_component_loss_mask
        if (
            geometry.dtype != torch.float32
            or geometry.device.type != "cpu"
            or tuple(geometry.shape) != (8, 2)
            or not bool(torch.isnan(geometry).all().item())
            or bool(geometry_valid.any().item())
            or bool(geometry_loss.any().item())
            or not bool(
                torch.equal(
                    base.supervision.pre_post_geometry_target_angstrom,
                    torch.zeros_like(
                        base.supervision.pre_post_geometry_target_angstrom
                    ),
                )
            )
        ):
            _fail("INACTIVE_GEOMETRY_NAN_CONVERSION_INVALID")
        try:
            tensorizer_owner._validate_numeric_authority(
                observed=tuple(
                    float(value)
                    for value in supervision.observed_complex_pair_distance_angstrom[:, 0]
                ),
                observed_valid=tuple(
                    bool(value)
                    for value in supervision.observed_complex_pair_distance_valid[:, 0]
                ),
                geometry=tuple(tuple(float(value) for value in row) for row in geometry),
                geometry_valid=tuple(
                    tuple(bool(value) for value in row) for row in geometry_valid
                ),
                geometry_loss=tuple(
                    tuple(bool(value) for value in row) for row in geometry_loss
                ),
            )
        except Exception as error:
            raise POA4I3UExact8InactiveConsumerAdapterError(
                f"{ERROR_TOKEN}:PUBLISHED_NUMERIC_AUTHORITY_REJECTED:"
                f"{type(error).__name__}:{error}"
            ) from error

        if (
            bool(supervision.sample_training_admitted.any().item())
            or bool(supervision.ligand_active_diffusion_loss_mask.any().item())
            or bool(supervision.pair_head_candidate_loss_mask.any().item())
            or bool(supervision.pair_contrastive_sample_loss_mask.any().item())
            or bool(supervision.pre_post_geometry_component_loss_mask.any().item())
        ):
            _fail("TRAINING_ADMISSION_OR_LOSS_MASK_ACTIVATED")
        false_flags = (
            payload.formal_training_carrier_created,
            payload.training_admission_created,
            payload.active_training_consumer_connected,
            payload.model_forward_executed,
            payload.loss_executed,
            payload.backward_executed,
            payload.optimizer_created,
            payload.optimizer_step_executed,
            payload.trainer_fit_executed,
            payload.training_performed,
            payload.ready_for_training,
        )
        if (
            payload.published_b1_reused is not True
            or payload.published_seed_ingestion_reused is not True
            or payload.local_task_c_seed_mapping_applied is not (task_id == 4)
            or payload.nan_geometry_conversion_applied is not True
            or any(flag is not False for flag in false_flags)
        ):
            _fail("INACTIVE_PERMISSION_BOUNDARY_INVALID")
        if (
            payload.summary != _summary(payload)
            or payload.summary.pair_candidate_count != EXPECTED_PAIR_COUNTS_V1[0]
            or payload.summary.pair_positive_count != EXPECTED_PAIR_COUNTS_V1[1]
            or payload.summary.pair_negative_count != EXPECTED_PAIR_COUNTS_V1[2]
            or payload.summary.geometry_nan_component_count != 16
            or payload.summary.geometry_valid_component_count != 0
            or payload.summary.geometry_loss_component_count != 0
            or payload.summary.seed_count_per_event
            != ((2,) * 8 if task_id == 4 else (0,) * 8)
        ):
            _fail("DERIVED_INACTIVE_SUMMARY_INVALID")
        return True
    except POA4I3UExact8InactiveConsumerAdapterError:
        raise
    except Exception as error:
        raise POA4I3UExact8InactiveConsumerAdapterError(
            f"{ERROR_TOKEN}:PUBLIC_VALIDATION_REJECTED:"
            f"{type(error).__name__}:{error}"
        ) from error
