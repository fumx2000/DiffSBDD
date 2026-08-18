"""Unified Current11/K36 structural tensorization for the Exact5 contract.

Current11 inputs are delegated byte-for-byte to the published Current11
tensorizer.  Recovered K36 inputs are resolved from the SHA-bound effective
supervision carrier and the published canonical structural evidence.  The
direct-profile branch emits the same supervision dataclass consumed by the
existing CovaPIE model bridge; it performs no model execution or state write.
"""

from __future__ import annotations

import copy
import hashlib
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, NoReturn, Sequence

import torch

from covalent_ext import (
    covapie_direct_attachment_optional_linker_runtime_v1 as direct_runtime,
)
from covalent_ext import (
    covapie_k36_w1_recovered7_authority_ingestion_and_effective_supervision_successor_v1
    as k36_successor,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CANONICAL_TASKS_V1 as CURRENT11_CANONICAL_TASKS_V1,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
    canonical_task_id_for_covapie_current11_sample_v1,
    tensorize_covapie_current11_training_supervision_v1,
)
from covalent_ext.covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1 import (
    CHECKPOINT_CHANNEL_ORDER,
    project_type_symbols_to_checkpoint_heavy_v1,
)


__all__ = (
    "MIXED_PROFILE_TENSORIZER_ERROR_V1",
    "GLOBAL_ROLE_VOCABULARY_V1",
    "GLOBAL_TASK_VOCABULARY_V1",
    "CURRENT11_MEMBER_IDENTITIES_V1",
    "K36_MEMBER_IDENTITIES_V1",
    "K36_VALID_TASK_IDS_V1",
    "K36_NOT_APPLICABLE_TASK_IDS_V1",
    "K36_EFFECTIVE_CARRIER_SHA256_V1",
    "K36_STRUCTURAL_EVIDENCE_SHA256_V1",
    "CovapieExpandedCysSgTensorizedSampleV1",
    "valid_task_ids_for_covapie_expanded_cys_sg_sample_v1",
    "tensorize_covapie_expanded_cys_sg_sample_v1",
)


MIXED_PROFILE_TENSORIZER_ERROR_V1 = (
    "COVAPIE_EXPANDED_CYS_SG_MIXED_PROFILE_TENSORIZER_V1_ERROR"
)
GLOBAL_ROLE_VOCABULARY_V1 = (
    (0, "scaffold"),
    (1, "linker"),
    (2, "warhead"),
)
GLOBAL_TASK_VOCABULARY_V1 = CURRENT11_CANONICAL_TASKS_V1

STRICT_LINKER_PRESENT_V1 = direct_runtime.STRICT_LINKER_PRESENT_V1
DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1 = (
    direct_runtime.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1
)
CURRENT11_MEMBER_IDENTITIES_V1 = tuple(
    f"CYS_SG_SAMPLE_INDEX_{index:06d}" for index in range(1, 12)
)
K36_MEMBER_IDENTITIES_V1 = (
    "4DCD/K36",
    "4F49/K36",
    "5WKJ/K36",
    "6L70/K36",
    "6WTT/K36",
)
K36_VALID_TASK_IDS_V1 = (0, 3, 4)
K36_NOT_APPLICABLE_TASK_IDS_V1 = (1, 2)
CURRENT11_VALID_TASK_IDS_V1 = (0, 1, 2, 3, 4)

K36_EFFECTIVE_CARRIER_RELATIVE_PATH_V1 = Path(
    "formal-sidecars/k36-w1-recovered7-effective-supervision-v1/"
    "covapie_k36_w1_recovered7_effective_supervision_v1.json"
)
K36_EFFECTIVE_CARRIER_SHA256_V1 = (
    "bd448b021ee0882f4bfe0826206616b83cdc7f69d9544f4533098aceed3a558c"
)
K36_STRUCTURAL_EVIDENCE_RELATIVE_PATH_V1 = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_recovered7_canonical_topology_exact10_pocket_closure_v1/"
    "covapie_cys_sg_recovered7_canonical_model_graph_and_pocket_evidence.json"
)
K36_STRUCTURAL_EVIDENCE_SHA256_V1 = (
    "c0a5196f94284bc78c49f1a981798c85b1fd5869237d54f30ba239321c3eb799"
)
K36_RECORD_SHA256_BY_IDENTITY_V1 = {
    "4DCD/K36": "0a4f376e8c0921ac41768ba89d7ed1ae239b821f1214df130c0e939ffda058c9",
    "4F49/K36": "3f0b4d3cec9ed2664c6525cb649eace685d00b700247afa891813ed4d00998e0",
    "5WKJ/K36": "5bbbe12fc57118535dece273e8884f82173e144c140497b4ce376908d7605a6a",
    "6L70/K36": "fab6f8b74e11b11439cf2053060cdabd695a5f5f50e2bc57acf20d443ccd4acc",
    "6WTT/K36": "c5dd0c205c8eb3f440a5fc0d44b326547dcf6c5327715d6cdbc8f074d38dcc15",
}
K36_TOPOLOGY_SEMANTIC_SHA256_V1 = (
    "ce787a2d8b579f21d08de1069b1cac60aadbf1093df9239e711ec31bc723fada"
)

_PATH_TYPE = type(Path())
_DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_STATE_ROOT = _DEFAULT_REPOSITORY_ROOT.parent / "covapie-state"
_MODEL_BATCH_CORE_FIELDS_V1 = frozenset((
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
_STRUCTURAL_EVIDENCE_FIELDS_V1 = frozenset((
    "component_topology_authorities",
    "distance_based_bond_inference_used",
    "downstream_authority_owners",
    "downstream_authority_source_sha256",
    "k36_independent_sample_mapping_count",
    "k36_shared_topology_reuse",
    "published_execution_commit",
    "published_execution_manifest_sha256",
    "published_recovery_snapshot_sha256",
    "rdkit_used",
    "reused_owners",
    "samples",
    "schema_version",
))
_STRUCTURAL_EVIDENCE_SCHEMA_V1 = (
    "covapie_cys_sg_recovered7_canonical_topology_exact10_pocket_closure_v1"
)
_ATOM_IDENTITY_FIELDS_V1 = (
    "atom_site_id",
    "auth_asym_id",
    "auth_atom_id",
    "auth_comp_id",
    "auth_seq_id",
    "group_PDB",
    "insertion_code",
    "label_alt_id",
    "label_asym_id",
    "label_atom_id",
    "label_comp_id",
    "label_seq_id",
    "model_num",
    "occupancy",
    "source_atom_site_row_index_0based",
    "type_symbol",
    "x",
    "y",
    "z",
)


@dataclass(frozen=True)
class CovapieExpandedCysSgTensorizedSampleV1:
    """Non-model wrapper around the existing model batch and supervision."""

    sample_identity: str
    role_profile: str
    valid_task_ids: tuple[int, ...]
    model_input_batch: dict[str, object]
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1

    def __post_init__(self) -> None:
        if (
            type(self.sample_identity) is not str
            or self.role_profile not in (
                STRICT_LINKER_PRESENT_V1,
                DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1,
            )
            or self.valid_task_ids not in (
                CURRENT11_VALID_TASK_IDS_V1,
                K36_VALID_TASK_IDS_V1,
            )
            or type(self.model_input_batch) is not dict
            or not _MODEL_BATCH_CORE_FIELDS_V1.issubset(self.model_input_batch)
            or not isinstance(
                self.supervision,
                CovapieCurrent11TrainingSupervisionTensorsV1,
            )
        ):
            raise ValueError(MIXED_PROFILE_TENSORIZER_ERROR_V1)


class _MixedProfileInvariantError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _fail(reason: str) -> NoReturn:
    raise _MixedProfileInvariantError(reason)


def _public_error(error: Exception) -> NoReturn:
    if isinstance(error, _MixedProfileInvariantError):
        raise ValueError(
            f"{MIXED_PROFILE_TENSORIZER_ERROR_V1}:{error.reason}"
        ) from error
    if (
        type(error) is ValueError
        and str(error).startswith(MIXED_PROFILE_TENSORIZER_ERROR_V1)
    ):
        raise error
    raise ValueError(MIXED_PROFILE_TENSORIZER_ERROR_V1) from error


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _profile_for_identity(sample_identity: object) -> str:
    if type(sample_identity) is not str:
        _fail("SAMPLE_IDENTITY_NOT_IN_INTEGRATION_POPULATION")
    if sample_identity in K36_MEMBER_IDENTITIES_V1:
        return DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1
    if sample_identity in CURRENT11_MEMBER_IDENTITIES_V1:
        return STRICT_LINKER_PRESENT_V1
    _fail("SAMPLE_IDENTITY_NOT_IN_INTEGRATION_POPULATION")


def valid_task_ids_for_covapie_expanded_cys_sg_sample_v1(
    sample_identity: object,
) -> tuple[int, ...]:
    """Expose deterministic per-sample applicability for future schedulers."""

    try:
        profile = _profile_for_identity(sample_identity)
        return direct_runtime.valid_canonical_task_ids_for_role_profile_v1(
            profile
        )
    except Exception as error:
        _public_error(error)


def _require_task(task_id: object, *, profile: str) -> int:
    if type(task_id) is not int or task_id not in range(5):
        _fail("CANONICAL_TASK_ID_INVALID")
    valid = direct_runtime.valid_canonical_task_ids_for_role_profile_v1(profile)
    if task_id not in valid:
        _fail("TASK_NOT_APPLICABLE_FOR_ROLE_PROFILE")
    return task_id


def _require_root(value: object, *, default: Path) -> Path:
    path = default if value is None else value
    if type(path) is not _PATH_TYPE or not path.is_absolute():
        _fail("SOURCE_ROOT_INVALID")
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise _MixedProfileInvariantError("SOURCE_ROOT_INVALID") from error
    if (
        resolved != path
        or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
    ):
        _fail("SOURCE_ROOT_INVALID")
    return path


def _safe_relative_file(root: Path, relative: object) -> Path:
    if type(relative) is not str:
        _fail("SOURCE_RELATIVE_PATH_INVALID")
    pure = Path(relative)
    if (
        not relative
        or "\\" in relative
        or pure.is_absolute()
        or pure.parts in ((), (".",))
        or ".." in pure.parts
    ):
        _fail("SOURCE_RELATIVE_PATH_INVALID")
    path = root / pure
    current = root
    try:
        for part in pure.parts:
            current = current / part
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                _fail("SOURCE_SYMLINK_FORBIDDEN")
        if not path.resolve(strict=True).is_relative_to(root):
            _fail("SOURCE_PATH_ESCAPE")
    except _MixedProfileInvariantError:
        raise
    except (OSError, RuntimeError) as error:
        raise _MixedProfileInvariantError("SOURCE_FILE_UNAVAILABLE") from error
    return path


def _read_exact_file(
    root: Path, relative: Path | str, *, expected_sha256: str
) -> bytes:
    path = _safe_relative_file(root, str(relative))
    try:
        metadata = path.lstat()
        payload = path.read_bytes()
    except OSError as error:
        raise _MixedProfileInvariantError("SOURCE_FILE_UNAVAILABLE") from error
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or _sha256(payload) != expected_sha256
    ):
        _fail("SOURCE_SHA256_MISMATCH")
    return payload


def _validated_k36_carrier_semantics_v1(
    payload: bytes,
) -> dict[str, dict[str, Any]]:
    try:
        parsed = k36_successor.strict_parse_authority_json_v1(payload)
        k36_successor.validate_covapie_k36_w1_recovered7_effective_supervision_v1(
            parsed
        )
    except Exception as error:
        raise _MixedProfileInvariantError(
            "K36_EFFECTIVE_CARRIER_SEMANTICS_INVALID"
        ) from error
    summary = parsed.get("ingestion_effective_authority_summary")
    records = parsed.get("effective_supervision_records")
    if (
        type(summary) is not dict
        or summary.get("effective_supervision_materialized") is not False
        or summary.get("state_modified") is not False
        or type(records) is not list
    ):
        _fail("K36_HISTORICAL_PAYLOAD_STATE_INVALID")
    by_identity: dict[str, dict[str, Any]] = {}
    for record in records:
        if type(record) is not dict:
            _fail("K36_EFFECTIVE_RECORD_INVALID")
        identity = record.get("sample_identity")
        if type(identity) is not str or identity in by_identity:
            _fail("K36_EFFECTIVE_RECORD_IDENTITY_INVALID")
        if (
            record.get("effective_supervision_record_sha256")
            != K36_RECORD_SHA256_BY_IDENTITY_V1.get(identity)
            or k36_successor.effective_supervision_record_sha256_v1(record)
            != K36_RECORD_SHA256_BY_IDENTITY_V1.get(identity)
        ):
            _fail("K36_EFFECTIVE_RECORD_SHA256_INVALID")
        by_identity[identity] = record
    if tuple(sorted(by_identity)) != K36_MEMBER_IDENTITIES_V1:
        _fail("K36_EFFECTIVE_EXACT5_POPULATION_INVALID")
    return by_identity


def _dict(value: object, reason: str) -> dict[str, Any]:
    if type(value) is not dict:
        _fail(reason)
    return value


def _list(value: object, reason: str) -> list[Any]:
    if type(value) is not list:
        _fail(reason)
    return value


def _validated_k36_structural_semantics_v1(
    payload: bytes,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    try:
        parsed = k36_successor.strict_parse_authority_json_v1(payload)
    except Exception as error:
        raise _MixedProfileInvariantError(
            "K36_STRUCTURAL_EVIDENCE_JSON_INVALID"
        ) from error
    if (
        frozenset(parsed) != _STRUCTURAL_EVIDENCE_FIELDS_V1
        or parsed.get("schema_version") != _STRUCTURAL_EVIDENCE_SCHEMA_V1
        or parsed.get("distance_based_bond_inference_used") is not False
        or parsed.get("rdkit_used") is not False
        or parsed.get("k36_independent_sample_mapping_count") != 5
        or parsed.get("k36_shared_topology_reuse") is not True
    ):
        _fail("K36_STRUCTURAL_EVIDENCE_CONTRACT_INVALID")
    topology_by_component = _dict(
        parsed.get("component_topology_authorities"),
        "K36_TOPOLOGY_AUTHORITY_INVALID",
    )
    topology = _dict(
        topology_by_component.get("K36"), "K36_TOPOLOGY_AUTHORITY_INVALID"
    )
    if (
        topology.get("component_id") != "K36"
        or topology.get("authoritative_topology_source_found") is not True
        or topology.get("semantic_topology_sha256")
        != K36_TOPOLOGY_SEMANTIC_SHA256_V1
        or topology.get("bond_order_available") is not True
        or topology.get("reaction_specific_post_graph_proven") is not False
    ):
        _fail("K36_TOPOLOGY_AUTHORITY_INVALID")
    samples = _list(parsed.get("samples"), "K36_STRUCTURAL_SAMPLES_INVALID")
    by_identity: dict[str, dict[str, Any]] = {}
    for sample in samples:
        item = _dict(sample, "K36_STRUCTURAL_SAMPLE_INVALID")
        pdb_id = item.get("pdb_id")
        component_id = item.get("ligand_component_id")
        if type(pdb_id) is not str or type(component_id) is not str:
            _fail("K36_STRUCTURAL_SAMPLE_IDENTITY_INVALID")
        identity = f"{pdb_id}/{component_id}"
        if component_id != "K36":
            continue
        if identity in by_identity:
            _fail("K36_STRUCTURAL_SAMPLE_IDENTITY_DUPLICATE")
        by_identity[identity] = item
    if tuple(sorted(by_identity)) != K36_MEMBER_IDENTITIES_V1:
        _fail("K36_STRUCTURAL_EXACT5_POPULATION_INVALID")
    return by_identity, topology


def _identity_matches(
    left: Mapping[str, Any], right: Mapping[str, Any]
) -> bool:
    return all(left.get(field) == right.get(field) for field in _ATOM_IDENTITY_FIELDS_V1)


def _coordinates(rows: Sequence[Mapping[str, Any]]) -> torch.Tensor:
    try:
        coordinates = torch.tensor(
            [
                [float(row[axis]) for axis in ("x", "y", "z")]
                for row in rows
            ],
            dtype=torch.float32,
        )
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        raise _MixedProfileInvariantError("STRUCTURAL_COORDINATES_INVALID") from error
    if coordinates.ndim != 2 or coordinates.shape[1:] != (3,) or not bool(
        torch.isfinite(coordinates).all().item()
    ):
        _fail("STRUCTURAL_COORDINATES_INVALID")
    return coordinates


def _validated_exact10_rows(
    rows: object, *, expected_count: int | None = None
) -> tuple[list[dict[str, Any]], tuple[int, ...]]:
    values = _list(rows, "MODEL_BOUND_ATOM_ROWS_INVALID")
    if expected_count is not None and len(values) != expected_count:
        _fail("MODEL_BOUND_ATOM_COUNT_INVALID")
    normalized: list[dict[str, Any]] = []
    for value in values:
        normalized.append(_dict(value, "MODEL_BOUND_ATOM_ROW_INVALID"))
    symbols = tuple(row.get("type_symbol") for row in normalized)
    projection = project_type_symbols_to_checkpoint_heavy_v1(symbols)
    if (
        projection.sample_rejected
        or any(
            symbol_class != "supported_checkpoint_heavy_atom"
            for symbol_class in projection.symbol_classes
        )
        or not all(projection.keep_mask)
    ):
        _fail("EXACT10_MODEL_BOUND_PROJECTION_INVALID")
    channels = tuple(projection.checkpoint_channel_indices)
    if (
        len(channels) != len(normalized)
        or any(type(channel) is not int for channel in channels)
        or any(
            row.get("exact10_channel_index") != channel
            for row, channel in zip(normalized, channels)
        )
    ):
        _fail("EXACT10_CHANNEL_BINDING_INVALID")
    source_indices = tuple(
        row.get("source_atom_site_row_index_0based") for row in normalized
    )
    if (
        any(type(index) is not int or index < 0 for index in source_indices)
        or len(source_indices) != len(set(source_indices))
    ):
        _fail("MODEL_BOUND_ATOM_ORDER_MAPPING_AMBIGUOUS")
    return normalized, channels


def _one_hot(channels: Sequence[int]) -> torch.Tensor:
    if any(type(channel) is not int or channel not in range(10) for channel in channels):
        _fail("EXACT10_CHANNEL_INVALID")
    return torch.eye(10, dtype=torch.float32)[
        torch.tensor(tuple(channels), dtype=torch.long)
    ]


def _explicit_retained_bonds(
    topology: Mapping[str, Any], retained_atom_ids: set[str]
) -> tuple[direct_runtime.ExplicitBondV1, ...]:
    bonds = _list(
        topology.get("component_internal_bonds"), "K36_TOPOLOGY_BONDS_INVALID"
    )
    result: list[direct_runtime.ExplicitBondV1] = []
    for raw in bonds:
        bond = _dict(raw, "K36_TOPOLOGY_BOND_INVALID")
        atom_1 = bond.get("atom_id_1")
        atom_2 = bond.get("atom_id_2")
        order = bond.get("normalized_bond_order")
        if atom_1 in retained_atom_ids and atom_2 in retained_atom_ids:
            if type(atom_1) is not str or type(atom_2) is not str or type(order) is not str:
                _fail("K36_TOPOLOGY_BOND_INVALID")
            result.append(direct_runtime.ExplicitBondV1(atom_1, atom_2, order))
    if not result:
        _fail("K36_RETAINED_TOPOLOGY_EMPTY")
    return tuple(result)


def _validated_k36_sample_sources_v1(
    *,
    repository_root: Path,
    record: dict[str, Any],
    structural_sample: dict[str, Any],
    topology: dict[str, Any],
) -> dict[str, Any]:
    identity = record.get("sample_identity")
    if (
        identity not in K36_MEMBER_IDENTITIES_V1
        or identity
        != f"{structural_sample.get('pdb_id')}/{structural_sample.get('ligand_component_id')}"
        or record.get("role_profile") != DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1
        or record.get("retained_heavy_atom_count") != 29
        or record.get("reviewed_scaffold_atom_count") != 27
        or record.get("reviewed_linker_atom_count") != 0
        or record.get("reviewed_warhead_role_atom_count") != 2
        or tuple(record.get("valid_task_ids", ())) != K36_VALID_TASK_IDS_V1
        or tuple(record.get("not_applicable_task_ids", ()))
        != K36_NOT_APPLICABLE_TASK_IDS_V1
        or record.get("reviewed_active_warhead_atom_ids") != ["C21", "O22"]
        or record.get("reviewed_warhead_role_atom_ids") != ["C21", "O22"]
        or record.get("reviewed_linker_atom_ids") != []
        or record.get("minimal_seed_atom_ids") != ["C20", "N19"]
        or record.get("ligand_reactive_atom_id") != "C21"
        or record.get("target_residue_name") != "CYS"
        or record.get("target_residue_atom_id") != "SG"
        or record.get("PRE_geometry_supervision_authority_status")
        != "NOT_ESTABLISHED"
    ):
        _fail("K36_EFFECTIVE_SAMPLE_CONTRACT_INVALID")
    boundary = _dict(
        record.get("direct_boundary_semantics"), "K36_DIRECT_BOUNDARY_INVALID"
    )
    if boundary != {
        "boundary_profile": "DIRECT_SCAFFOLD_WARHEAD_SINGLE_BOUNDARY_V1",
        "boundary_count": 1,
        "scaffold_side_atom_id": "C20",
        "warhead_side_atom_id": "C21",
        "bond_order": "single",
        "linker_present": False,
    }:
        _fail("K36_DIRECT_BOUNDARY_INVALID")

    raw_source = _dict(
        structural_sample.get("raw_source"), "K36_RAW_SOURCE_INVALID"
    )
    raw_path = raw_source.get("path")
    raw_sha256 = raw_source.get("sha256")
    if type(raw_path) is not str or type(raw_sha256) is not str:
        _fail("K36_RAW_SOURCE_INVALID")
    _read_exact_file(repository_root, raw_path, expected_sha256=raw_sha256)

    ligand_rows, ligand_channels = _validated_exact10_rows(
        structural_sample.get("canonical_model_bound_ligand_atoms"),
        expected_count=29,
    )
    ligand_atom_ids = tuple(row.get("label_atom_id") for row in ligand_rows)
    if (
        any(type(atom_id) is not str or not atom_id for atom_id in ligand_atom_ids)
        or len(ligand_atom_ids) != len(set(ligand_atom_ids))
        or set(ligand_atom_ids) != set(record.get("retained_heavy_atom_ids", ()))
        or any(ligand_atom_ids.count(atom_id) != 1 for atom_id in (
            "C21", "O22", "C20", "N19"
        ))
    ):
        _fail("K36_LIGAND_ATOM_ID_ORDER_MAPPING_INVALID")
    ligand_index = {atom_id: index for index, atom_id in enumerate(ligand_atom_ids)}
    scaffold_ids = tuple(record.get("reviewed_scaffold_atom_ids", ()))
    linker_ids = tuple(record.get("reviewed_linker_atom_ids", ()))
    warhead_ids = tuple(record.get("reviewed_warhead_role_atom_ids", ()))
    if (
        len(scaffold_ids) != 27
        or linker_ids
        or warhead_ids != ("C21", "O22")
        or set(scaffold_ids).isdisjoint(warhead_ids) is not True
        or set(scaffold_ids) | set(warhead_ids) != set(ligand_atom_ids)
    ):
        _fail("K36_ROLE_PARTITION_INVALID")
    scaffold_indices = tuple(ligand_index[atom_id] for atom_id in scaffold_ids)
    linker_indices: tuple[int, ...] = ()
    warhead_indices = tuple(ligand_index[atom_id] for atom_id in warhead_ids)
    role_ids = tuple(
        2 if atom_id in set(warhead_ids) else 0 for atom_id in ligand_atom_ids
    )
    retained_bonds = _explicit_retained_bonds(topology, set(ligand_atom_ids))
    role_validation = direct_runtime.validate_role_profile_v1(
        role_profile=DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1,
        retained_heavy_atoms=ligand_atom_ids,
        scaffold_atoms=scaffold_ids,
        linker_atoms=linker_ids,
        warhead_atoms=warhead_ids,
        reactive_atom_id="C21",
        direct_scaffold_warhead_boundaries=(("C20", "C21", "single"),),
        explicit_graph_bonds=retained_bonds,
    )
    if (
        role_validation.valid is not True
        or role_validation.scaffold_count != 27
        or role_validation.linker_count != 0
        or role_validation.warhead_count != 2
        or role_validation.direct_scaffold_warhead_boundary is None
        or role_validation.direct_scaffold_warhead_boundary.boundary_valid
        is not True
    ):
        _fail("K36_PUBLISHED_ROLE_RUNTIME_REJECTED")
    seed_validation = direct_runtime.validate_minimal_seed_for_role_profile_v1(
        role_profile=DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1,
        seed_atoms=("C20", "N19"),
        scaffold_atoms=scaffold_ids,
        linker_atoms=linker_ids,
        warhead_atoms=warhead_ids,
        explicit_graph_bonds=retained_bonds,
        direct_boundary=role_validation.direct_scaffold_warhead_boundary,
    )
    if (
        seed_validation.valid is not True
        or seed_validation.primary_anchor_atom_id != "C20"
    ):
        _fail("K36_PUBLISHED_SEED_RUNTIME_REJECTED")

    explicit_event = _dict(
        structural_sample.get("explicit_event"), "K36_EXPLICIT_EVENT_INVALID"
    )
    event_edge = _dict(
        explicit_event.get("protein_ligand_covalent_event_edge"),
        "K36_EXPLICIT_EVENT_EDGE_INVALID",
    )
    protein_endpoint = _dict(
        explicit_event.get("protein_endpoint"),
        "K36_PROTEIN_ENDPOINT_INVALID",
    )
    ligand_endpoint = _dict(
        explicit_event.get("ligand_endpoint"),
        "K36_LIGAND_ENDPOINT_INVALID",
    )
    if (
        event_edge.get("evidence_kind")
        != "MMCIF_STRUCT_CONN_EXACT_ENDPOINT_PAIR"
        or event_edge.get("part_of_ligand_internal_topology") is not False
        or event_edge.get("protein_atom_name") != "SG"
        or event_edge.get("ligand_atom_name") != "C21"
        or protein_endpoint.get("auth_comp_id") != "CYS"
        or protein_endpoint.get("auth_atom_id") != "SG"
        or ligand_endpoint.get("auth_comp_id") != "K36"
        or ligand_endpoint.get("auth_atom_id") != "C21"
    ):
        _fail("K36_EXPLICIT_EVENT_ENDPOINTS_INVALID")
    ligand_endpoint_matches = [
        index
        for index, row in enumerate(ligand_rows)
        if _identity_matches(row, ligand_endpoint)
    ]
    if ligand_endpoint_matches != [ligand_index["C21"]]:
        _fail("K36_REACTIVE_C21_MAPPING_INVALID")

    pocket_block = _dict(
        structural_sample.get("canonical_pocket"), "K36_POCKET_INVALID"
    )
    if (
        pocket_block.get("protein_only_group_PDB_ATOM") is not True
        or pocket_block.get("target_cys_present") is not True
        or pocket_block.get("target_sg_present") is not True
    ):
        _fail("K36_POCKET_INVALID")
    pocket_rows, pocket_channels = _validated_exact10_rows(
        pocket_block.get("retained_atoms")
    )
    protein_endpoint_matches = [
        index
        for index, row in enumerate(pocket_rows)
        if _identity_matches(row, protein_endpoint)
    ]
    if len(protein_endpoint_matches) != 1:
        _fail("K36_TARGET_SG_MAPPING_NOT_EXACTLY_ONE")
    target_sg_index = protein_endpoint_matches[0]
    target_identity = tuple(
        protein_endpoint.get(field)
        for field in ("model_num", "auth_asym_id", "auth_seq_id", "insertion_code")
    )
    target_member_indices = tuple(
        index
        for index, row in enumerate(pocket_rows)
        if row.get("auth_comp_id") == "CYS"
        and tuple(
            row.get(field)
            for field in (
                "model_num", "auth_asym_id", "auth_seq_id", "insertion_code"
            )
        ) == target_identity
    )
    if (
        not target_member_indices
        or target_sg_index not in target_member_indices
        or sum(
            (pocket_rows[index].get("auth_atom_id") == "SG")
            for index in target_member_indices
        ) != 1
        or pocket_channels[target_sg_index] != 3
    ):
        _fail("K36_TARGET_CYS_SG_MEMBERSHIP_INVALID")
    exact10 = _dict(structural_sample.get("exact10"), "K36_EXACT10_INVALID")
    if (
        exact10.get("channel_order") != CHECKPOINT_CHANNEL_ORDER
        or exact10.get("status") != "EXACT10_PASS"
        or exact10.get("unsupported_nonh_model_bound_atoms") != []
        or exact10.get("unknown_or_other_channel_present") is not False
        or exact10.get("zero_vector_fallback_used") is not False
        or structural_sample.get("mechanical_closure_status")
        != "MECHANICAL_CLOSURE_PASS"
    ):
        _fail("K36_EXACT10_INVALID")
    return {
        "ligand_rows": ligand_rows,
        "ligand_channels": ligand_channels,
        "ligand_atom_ids": ligand_atom_ids,
        "ligand_index": ligand_index,
        "pocket_rows": pocket_rows,
        "pocket_channels": pocket_channels,
        "target_member_indices": target_member_indices,
        "target_sg_index": target_sg_index,
        "scaffold_indices": scaffold_indices,
        "linker_indices": linker_indices,
        "warhead_indices": warhead_indices,
        "role_ids": role_ids,
    }


def _direct_supervision_v1(
    *,
    task_id: int,
    device: torch.device,
    ligand_coordinates: torch.Tensor,
    pocket_coordinates: torch.Tensor,
    sources: Mapping[str, Any],
) -> CovapieCurrent11TrainingSupervisionTensorsV1:
    ligand_count = len(ligand_coordinates)
    pocket_count = len(pocket_coordinates)
    scaffold = sources["scaffold_indices"]
    linker = sources["linker_indices"]
    warhead = sources["warhead_indices"]
    role_ids = sources["role_ids"]
    mask_result = direct_runtime.build_mask_for_role_profile_v1(
        role_profile=DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1,
        canonical_task_id=task_id,
        scaffold_atoms=scaffold,
        linker_atoms=linker,
        warhead_atoms=warhead,
        num_ligand_atoms=ligand_count,
    )
    compatibility = direct_runtime.validate_current_lightning_structural_expectations_v1(
        role_profile=DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1,
        canonical_task_id=task_id,
        ligand_role_ids=role_ids,
        mask_result=mask_result,
    )
    if compatibility.valid is not True:
        _fail("K36_MASK_MODEL_CONTRACT_INVALID")
    generation = torch.zeros(ligand_count, dtype=torch.bool, device=device)
    generation[list(mask_result.masked_atoms)] = True
    fixed = ~generation
    role_tensor = torch.tensor(role_ids, dtype=torch.long, device=device)
    expected_generated_by_role = torch.tensor(
        [role in set(GLOBAL_TASK_VOCABULARY_V1[task_id][3]) for role in role_ids],
        dtype=torch.bool,
        device=device,
    )
    if not torch.equal(generation, expected_generated_by_role):
        _fail("K36_MASK_TASK_ROLE_SEMANTICS_INVALID")

    task_c = task_id == 4
    seed = torch.zeros(ligand_count, dtype=torch.bool, device=device)
    if task_c:
        seed[[sources["ligand_index"]["C20"], sources["ligand_index"]["N19"]]] = True

    target_membership = torch.zeros(
        pocket_count, dtype=torch.bool, device=device
    )
    target_membership[list(sources["target_member_indices"])] = True
    target_sg_index = sources["target_sg_index"]
    target_reactive = torch.zeros(pocket_count, dtype=torch.bool, device=device)
    target_reactive[target_sg_index] = True
    ligand_c21_index = sources["ligand_index"]["C21"]

    member_local = torch.tensor(
        sources["target_member_indices"], dtype=torch.long, device=device
    )
    ligand_local = torch.arange(
        ligand_count, dtype=torch.long, device=device
    ).repeat_interleave(len(member_local))
    pocket_local = member_local.repeat(ligand_count)
    positive = (ligand_local == ligand_c21_index) & (
        pocket_local == target_sg_index
    )
    if int(positive.sum().item()) != 1:
        _fail("K36_PAIR_POSITIVE_NOT_EXACTLY_ONE")
    positive_index = int(torch.nonzero(positive, as_tuple=False)[0, 0].item())
    negative_count = len(positive) - 1
    if negative_count <= 0:
        _fail("K36_PAIR_NEGATIVE_CONTRACT_INVALID")

    ligand_device = ligand_coordinates.to(device=device, dtype=torch.float32)
    pocket_device = pocket_coordinates.to(device=device, dtype=torch.float32)
    target_coordinate = pocket_device[target_sg_index]
    anchor_distance = torch.linalg.vector_norm(
        ligand_device - target_coordinate, dim=1, keepdim=True
    )
    observed_distance = torch.linalg.vector_norm(
        ligand_device[ligand_c21_index] - target_coordinate
    ).reshape(1, 1)
    if not bool(torch.isfinite(anchor_distance).all().item()) or not bool(
        torch.isfinite(observed_distance).all().item()
    ):
        _fail("K36_DISTANCE_TENSORS_INVALID")

    return CovapieCurrent11TrainingSupervisionTensorsV1(
        sample_training_admitted=torch.ones(1, dtype=torch.bool, device=device),
        canonical_task_id=torch.tensor([task_id], dtype=torch.long, device=device),
        canonical_task_valid=torch.ones(1, dtype=torch.bool, device=device),
        ligand_role_id=role_tensor,
        ligand_role_valid=torch.ones(ligand_count, dtype=torch.bool, device=device),
        ligand_base_generation_mask=generation.unsqueeze(1),
        ligand_base_fixed_mask=fixed.unsqueeze(1),
        ligand_base_target_mask=generation.unsqueeze(1),
        ligand_base_context_mask=fixed.unsqueeze(1),
        ligand_active_diffusion_loss_mask=generation.unsqueeze(1),
        ligand_minimal_seed_or_anchor_mask=seed.unsqueeze(1),
        ligand_minimal_seed_or_anchor_valid=torch.tensor(
            [task_c], dtype=torch.bool, device=device
        ),
        ligand_anchor_distance_angstrom=anchor_distance,
        ligand_anchor_distance_valid=torch.ones(
            (ligand_count, 1), dtype=torch.bool, device=device
        ),
        target_residue_membership_mask=target_membership.unsqueeze(1),
        target_residue_reactive_atom_mask=target_reactive.unsqueeze(1),
        target_residue_reactive_atom_local_index=torch.tensor(
            [target_sg_index], dtype=torch.long, device=device
        ),
        target_residue_reactive_atom_flat_index=torch.tensor(
            [target_sg_index], dtype=torch.long, device=device
        ),
        target_residue_condition_valid=torch.ones(
            1, dtype=torch.bool, device=device
        ),
        pair_candidate_offsets=torch.tensor(
            [0, len(positive)], dtype=torch.long, device=device
        ),
        pair_candidate_batch_index=torch.zeros(
            len(positive), dtype=torch.long, device=device
        ),
        pair_candidate_ligand_local_index=ligand_local,
        pair_candidate_residue_local_index=pocket_local,
        pair_candidate_ligand_flat_index=ligand_local.clone(),
        pair_candidate_pocket_flat_index=pocket_local.clone(),
        pair_candidate_is_positive=positive,
        pair_candidate_is_negative=~positive,
        pair_positive_candidate_index=torch.tensor(
            [positive_index], dtype=torch.long, device=device
        ),
        pair_positive_candidate_valid=torch.ones(
            1, dtype=torch.bool, device=device
        ),
        pair_negative_count=torch.tensor(
            [negative_count], dtype=torch.long, device=device
        ),
        pair_head_candidate_loss_mask=torch.ones(
            len(positive), dtype=torch.bool, device=device
        ),
        pair_contrastive_sample_loss_mask=torch.ones(
            1, dtype=torch.bool, device=device
        ),
        observed_complex_pair_distance_angstrom=observed_distance,
        observed_complex_pair_distance_valid=torch.ones(
            (1, 1), dtype=torch.bool, device=device
        ),
        pre_post_geometry_target_angstrom=torch.full(
            (1, 2), float("nan"), dtype=torch.float32, device=device
        ),
        pre_post_geometry_component_valid_mask=torch.zeros(
            (1, 2), dtype=torch.bool, device=device
        ),
        pre_post_geometry_component_loss_mask=torch.zeros(
            (1, 2), dtype=torch.bool, device=device
        ),
    )


def _tensorize_k36_v1(
    *,
    sample_identity: str,
    task_id: int,
    device: object,
    repository_root: object,
    state_root: object,
) -> CovapieExpandedCysSgTensorizedSampleV1:
    repo = _require_root(repository_root, default=_DEFAULT_REPOSITORY_ROOT)
    state = _require_root(state_root, default=_DEFAULT_STATE_ROOT)
    carrier_payload = _read_exact_file(
        state,
        K36_EFFECTIVE_CARRIER_RELATIVE_PATH_V1,
        expected_sha256=K36_EFFECTIVE_CARRIER_SHA256_V1,
    )
    records = _validated_k36_carrier_semantics_v1(carrier_payload)
    evidence_payload = _read_exact_file(
        repo,
        K36_STRUCTURAL_EVIDENCE_RELATIVE_PATH_V1,
        expected_sha256=K36_STRUCTURAL_EVIDENCE_SHA256_V1,
    )
    structural_samples, topology = _validated_k36_structural_semantics_v1(
        evidence_payload
    )
    sources = _validated_k36_sample_sources_v1(
        repository_root=repo,
        record=records[sample_identity],
        structural_sample=structural_samples[sample_identity],
        topology=topology,
    )
    try:
        model_device = torch.device(device)
    except (TypeError, RuntimeError) as error:
        raise _MixedProfileInvariantError("MODEL_DEVICE_INVALID") from error
    ligand_coordinates = _coordinates(sources["ligand_rows"])
    pocket_coordinates = _coordinates(sources["pocket_rows"])
    ligand_channels = sources["ligand_channels"]
    pocket_channels = sources["pocket_channels"]
    ligand_source = tuple(
        row["source_atom_site_row_index_0based"] for row in sources["ligand_rows"]
    )
    pocket_source = tuple(
        row["source_atom_site_row_index_0based"] for row in sources["pocket_rows"]
    )
    ligand_count = len(ligand_coordinates)
    pocket_count = len(pocket_coordinates)
    model_batch: dict[str, object] = {
        "names": [sample_identity],
        "receptors": [sample_identity.split("/", 1)[0]],
        "lig_coords": ligand_coordinates,
        "pocket_coords": pocket_coordinates,
        "lig_one_hot": _one_hot(ligand_channels),
        "pocket_one_hot": _one_hot(pocket_channels),
        "lig_source_row_index": torch.tensor(ligand_source, dtype=torch.long),
        "pocket_source_row_index": torch.tensor(pocket_source, dtype=torch.long),
        "lig_parser_local_index": torch.arange(ligand_count, dtype=torch.long),
        "pocket_parser_local_index": torch.arange(pocket_count, dtype=torch.long),
        "num_lig_atoms": torch.tensor([ligand_count], dtype=torch.long),
        "num_pocket_nodes": torch.tensor([pocket_count], dtype=torch.long),
        "lig_mask": torch.zeros(ligand_count, dtype=torch.long),
        "pocket_mask": torch.zeros(pocket_count, dtype=torch.long),
    }
    supervision = _direct_supervision_v1(
        task_id=task_id,
        device=model_device,
        ligand_coordinates=ligand_coordinates,
        pocket_coordinates=pocket_coordinates,
        sources=sources,
    )
    return CovapieExpandedCysSgTensorizedSampleV1(
        sample_identity=sample_identity,
        role_profile=DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1,
        valid_task_ids=K36_VALID_TASK_IDS_V1,
        model_input_batch=model_batch,
        supervision=supervision,
    )


def _current11_offsets(
    authority: Mapping[str, Any], *, name: str, batch_size: int, total: int
) -> tuple[int, ...]:
    value = authority.get(name)
    if type(value) not in (list, tuple):
        _fail("CURRENT11_NODE_OFFSETS_INVALID")
    offsets = tuple(value)
    if (
        len(offsets) != batch_size + 1
        or any(type(item) is not int for item in offsets)
        or offsets[0] != 0
        or offsets[-1] != total
        or any(left >= right for left, right in zip(offsets, offsets[1:]))
    ):
        _fail("CURRENT11_NODE_OFFSETS_INVALID")
    return offsets  # type: ignore[return-value]


def _current11_tensor_slice(
    batch: Mapping[str, Any], name: str, start: int, end: int
) -> torch.Tensor:
    value = batch.get(name)
    if not isinstance(value, torch.Tensor) or value.ndim == 0 or len(value) < end:
        _fail("CURRENT11_MODEL_BATCH_TENSOR_INVALID")
    return value[start:end].clone()


def _current11_sequence_slice(
    value: object, *, start: int, end: int, reason: str
) -> list[Any]:
    if type(value) not in (list, tuple) or len(value) < end:
        _fail(reason)
    return copy.deepcopy(list(value[start:end]))


def _slice_current11_singleton_inputs_v1(
    *,
    sample_identity: str,
    sample_ordinal: int,
    batch: dict[str, object],
    runtime_result: dict[str, object],
    authoritative_supervision: dict[str, object],
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    sample_keys = authoritative_supervision.get("sample_keys")
    if (
        type(sample_keys) is not list
        or not 0 <= sample_ordinal < len(sample_keys)
        or sample_keys[sample_ordinal] != sample_identity
    ):
        _fail("CURRENT11_SINGLETON_SELECTION_INVALID")
    batch_size = len(sample_keys)
    ligand_coordinates = batch.get("lig_coords")
    pocket_coordinates = batch.get("pocket_coords")
    if (
        not isinstance(ligand_coordinates, torch.Tensor)
        or not isinstance(pocket_coordinates, torch.Tensor)
    ):
        _fail("CURRENT11_MODEL_BATCH_TENSOR_INVALID")
    ligand_offsets = _current11_offsets(
        authoritative_supervision,
        name="ligand_node_offsets",
        batch_size=batch_size,
        total=len(ligand_coordinates),
    )
    pocket_offsets = _current11_offsets(
        authoritative_supervision,
        name="pocket_node_offsets",
        batch_size=batch_size,
        total=len(pocket_coordinates),
    )
    ligand_start, ligand_end = ligand_offsets[
        sample_ordinal:sample_ordinal + 2
    ]
    pocket_start, pocket_end = pocket_offsets[
        sample_ordinal:sample_ordinal + 2
    ]
    ligand_count = ligand_end - ligand_start
    pocket_count = pocket_end - pocket_start

    names = batch.get("names")
    receptors = batch.get("receptors")
    if (
        type(names) not in (list, tuple)
        or type(receptors) not in (list, tuple)
        or len(names) != batch_size
        or len(receptors) != batch_size
        or str(names[sample_ordinal]) != sample_identity
    ):
        _fail("CURRENT11_MODEL_BATCH_IDENTITY_INVALID")
    ligand_mask = _current11_tensor_slice(
        batch, "lig_mask", ligand_start, ligand_end
    )
    pocket_mask = _current11_tensor_slice(
        batch, "pocket_mask", pocket_start, pocket_end
    )
    try:
        ligand_mask = ligand_mask - sample_ordinal
        pocket_mask = pocket_mask - sample_ordinal
    except (RuntimeError, TypeError) as error:
        raise _MixedProfileInvariantError(
            "CURRENT11_MODEL_BATCH_MEMBERSHIP_INVALID"
        ) from error
    singleton_batch: dict[str, object] = {
        "names": [names[sample_ordinal]],
        "receptors": [receptors[sample_ordinal]],
        "lig_coords": _current11_tensor_slice(
            batch, "lig_coords", ligand_start, ligand_end
        ),
        "pocket_coords": _current11_tensor_slice(
            batch, "pocket_coords", pocket_start, pocket_end
        ),
        "lig_one_hot": _current11_tensor_slice(
            batch, "lig_one_hot", ligand_start, ligand_end
        ),
        "pocket_one_hot": _current11_tensor_slice(
            batch, "pocket_one_hot", pocket_start, pocket_end
        ),
        "lig_source_row_index": _current11_tensor_slice(
            batch, "lig_source_row_index", ligand_start, ligand_end
        ),
        "pocket_source_row_index": _current11_tensor_slice(
            batch, "pocket_source_row_index", pocket_start, pocket_end
        ),
        "lig_parser_local_index": _current11_tensor_slice(
            batch, "lig_parser_local_index", ligand_start, ligand_end
        ),
        "pocket_parser_local_index": _current11_tensor_slice(
            batch, "pocket_parser_local_index", pocket_start, pocket_end
        ),
        "num_lig_atoms": _current11_tensor_slice(
            batch, "num_lig_atoms", sample_ordinal, sample_ordinal + 1
        ),
        "num_pocket_nodes": _current11_tensor_slice(
            batch, "num_pocket_nodes", sample_ordinal, sample_ordinal + 1
        ),
        "lig_mask": ligand_mask,
        "pocket_mask": pocket_mask,
    }
    indicator_name = "pocket_target_residue_atom_condition_indicator"
    if indicator_name in batch:
        singleton_batch[indicator_name] = _current11_tensor_slice(
            batch, indicator_name, pocket_start, pocket_end
        )

    output17 = runtime_result.get("remap_output17_or_none")
    if (
        type(output17) is not dict
        or runtime_result.get("runtime_status") != "full_success"
        or runtime_result.get("batch_sample_keys_or_none") != sample_keys
    ):
        _fail("CURRENT11_RUNTIME_RESULT_INVALID")
    pair_offsets_raw = output17.get("sample_pair_offsets")
    if type(pair_offsets_raw) not in (list, tuple) or len(pair_offsets_raw) != batch_size + 1:
        _fail("CURRENT11_RUNTIME_PAIR_OFFSETS_INVALID")
    pair_offsets = tuple(pair_offsets_raw)
    if (
        any(type(item) is not int for item in pair_offsets)
        or pair_offsets[0] != 0
        or any(left > right for left, right in zip(pair_offsets, pair_offsets[1:]))
    ):
        _fail("CURRENT11_RUNTIME_PAIR_OFFSETS_INVALID")
    pair_start, pair_end = pair_offsets[sample_ordinal:sample_ordinal + 2]
    pair_sample_indices = _current11_sequence_slice(
        output17.get("pair_sample_indices"),
        start=pair_start,
        end=pair_end,
        reason="CURRENT11_RUNTIME_PAIR_SAMPLE_INDICES_INVALID",
    )
    if pair_sample_indices != [sample_ordinal] * (pair_end - pair_start):
        _fail("CURRENT11_RUNTIME_PAIR_SAMPLE_INDICES_INVALID")
    batch_pairs = _current11_sequence_slice(
        output17.get("pair_values_batch_indices"),
        start=pair_start,
        end=pair_end,
        reason="CURRENT11_RUNTIME_PAIRS_INVALID",
    )
    parser_pairs = _current11_sequence_slice(
        output17.get("pair_values_parser_local_indices"),
        start=pair_start,
        end=pair_end,
        reason="CURRENT11_RUNTIME_PAIRS_INVALID",
    )
    normalized_batch_pairs: list[list[int]] = []
    for pair in batch_pairs:
        if (
            type(pair) not in (list, tuple)
            or len(pair) != 2
            or any(type(item) is not int for item in pair)
        ):
            _fail("CURRENT11_RUNTIME_PAIRS_INVALID")
        normalized_batch_pairs.append(
            [pair[0] - pocket_start, pair[1] - ligand_start]
        )
    joint_pairs_raw = output17.get("pair_values_joint_global_indices")
    normalized_joint_pairs: list[list[int]] | None = None
    if joint_pairs_raw is not None:
        joint_pairs = _current11_sequence_slice(
            joint_pairs_raw,
            start=pair_start,
            end=pair_end,
            reason="CURRENT11_RUNTIME_JOINT_PAIRS_INVALID",
        )
        normalized_joint_pairs = []
        for pair in joint_pairs:
            if (
                type(pair) not in (list, tuple)
                or len(pair) != 2
                or any(type(item) is not int for item in pair)
            ):
                _fail("CURRENT11_RUNTIME_JOINT_PAIRS_INVALID")
            normalized_joint_pairs.append(
                [pair[0] - len(ligand_coordinates) - pocket_start + ligand_count,
                 pair[1] - ligand_start]
            )
    sample_order = _current11_sequence_slice(
        output17.get("batch_sample_order"),
        start=sample_ordinal,
        end=sample_ordinal + 1,
        reason="CURRENT11_RUNTIME_SAMPLE_ORDER_INVALID",
    )
    singleton_output17: dict[str, object] = {
        "batch_sample_order": sample_order,
        "pair_values_parser_local_indices": parser_pairs,
        "pair_values_batch_indices": normalized_batch_pairs,
        "pair_values_joint_global_indices": normalized_joint_pairs,
        "pair_sample_indices": [0] * (pair_end - pair_start),
        "sample_pair_offsets": [0, pair_end - pair_start],
        "entry_validity": _current11_sequence_slice(
            output17.get("entry_validity"),
            start=pair_start,
            end=pair_end,
            reason="CURRENT11_RUNTIME_ENTRY_VALIDITY_INVALID",
        ),
        "sample_validity": _current11_sequence_slice(
            output17.get("sample_validity"),
            start=sample_ordinal,
            end=sample_ordinal + 1,
            reason="CURRENT11_RUNTIME_SAMPLE_VALIDITY_INVALID",
        ),
        "remap_status": output17.get("remap_status"),
        "failure_reason": output17.get("failure_reason"),
    }
    singleton_runtime: dict[str, object] = {
        "runtime_status": "full_success",
        "batch_sample_keys_or_none": [sample_identity],
        "remap_output17_or_none": singleton_output17,
    }
    singleton_batch["covapie_current11_task2_runtime_result_v1"] = (
        singleton_runtime
    )

    binding = authoritative_supervision.get("formal_carrier_feature_binding")
    if type(binding) is not dict:
        _fail("CURRENT11_FORMAL_FEATURE_BINDING_INVALID")
    singleton_binding: dict[str, object] = {
        "schema_version": binding.get("schema_version"),
        "checkpoint_channel_order": binding.get("checkpoint_channel_order"),
    }
    for name, start, end in (
        ("ligand_source_row_index", ligand_start, ligand_end),
        ("pocket_source_row_index", pocket_start, pocket_end),
        ("ligand_checkpoint_channel_index", ligand_start, ligand_end),
        ("pocket_checkpoint_channel_index", pocket_start, pocket_end),
    ):
        singleton_binding[name] = _current11_sequence_slice(
            binding.get(name),
            start=start,
            end=end,
            reason="CURRENT11_FORMAL_FEATURE_BINDING_INVALID",
        )
    singleton_binding["ligand_parser_local_index"] = (
        _current11_sequence_slice(
            binding.get("ligand_parser_local_index"),
            start=ligand_start,
            end=ligand_end,
            reason="CURRENT11_FORMAL_FEATURE_BINDING_INVALID",
        )
    )
    singleton_binding["pocket_parser_local_index"] = (
        _current11_sequence_slice(
            binding.get("pocket_parser_local_index"),
            start=pocket_start,
            end=pocket_end,
            reason="CURRENT11_FORMAL_FEATURE_BINDING_INVALID",
        )
    )
    singleton_authority: dict[str, object] = {
        "schema_version": authoritative_supervision.get("schema_version"),
        "sample_keys": [sample_identity],
        "formal_carrier_feature_binding": singleton_binding,
        "ligand_node_offsets": [0, ligand_count],
        "pocket_node_offsets": [0, pocket_count],
        "ligand_role_id": _current11_sequence_slice(
            authoritative_supervision.get("ligand_role_id"),
            start=ligand_start,
            end=ligand_end,
            reason="CURRENT11_LIGAND_AUTHORITY_INVALID",
        ),
        "ligand_role_valid": _current11_sequence_slice(
            authoritative_supervision.get("ligand_role_valid"),
            start=ligand_start,
            end=ligand_end,
            reason="CURRENT11_LIGAND_AUTHORITY_INVALID",
        ),
        "ligand_minimal_seed_or_anchor_mask": _current11_sequence_slice(
            authoritative_supervision.get("ligand_minimal_seed_or_anchor_mask"),
            start=ligand_start,
            end=ligand_end,
            reason="CURRENT11_SEED_AUTHORITY_INVALID",
        ),
        "ligand_minimal_seed_or_anchor_valid": _current11_sequence_slice(
            authoritative_supervision.get("ligand_minimal_seed_or_anchor_valid"),
            start=sample_ordinal,
            end=sample_ordinal + 1,
            reason="CURRENT11_SEED_AUTHORITY_INVALID",
        ),
        "sample_training_admitted": _current11_sequence_slice(
            authoritative_supervision.get("sample_training_admitted"),
            start=sample_ordinal,
            end=sample_ordinal + 1,
            reason="CURRENT11_SAMPLE_AUTHORITY_INVALID",
        ),
        "target_residue_membership_mask": _current11_sequence_slice(
            authoritative_supervision.get("target_residue_membership_mask"),
            start=pocket_start,
            end=pocket_end,
            reason="CURRENT11_TARGET_AUTHORITY_INVALID",
        ),
        "observed_complex_pair_distance_angstrom": _current11_sequence_slice(
            authoritative_supervision.get("observed_complex_pair_distance_angstrom"),
            start=sample_ordinal,
            end=sample_ordinal + 1,
            reason="CURRENT11_GEOMETRY_AUTHORITY_INVALID",
        ),
        "observed_complex_pair_distance_valid": _current11_sequence_slice(
            authoritative_supervision.get("observed_complex_pair_distance_valid"),
            start=sample_ordinal,
            end=sample_ordinal + 1,
            reason="CURRENT11_GEOMETRY_AUTHORITY_INVALID",
        ),
        "pre_post_geometry_target_angstrom": _current11_sequence_slice(
            authoritative_supervision.get("pre_post_geometry_target_angstrom"),
            start=sample_ordinal,
            end=sample_ordinal + 1,
            reason="CURRENT11_GEOMETRY_AUTHORITY_INVALID",
        ),
        "pre_post_geometry_component_valid_mask": _current11_sequence_slice(
            authoritative_supervision.get(
                "pre_post_geometry_component_valid_mask"
            ),
            start=sample_ordinal,
            end=sample_ordinal + 1,
            reason="CURRENT11_GEOMETRY_AUTHORITY_INVALID",
        ),
        "pre_post_geometry_component_loss_mask": _current11_sequence_slice(
            authoritative_supervision.get(
                "pre_post_geometry_component_loss_mask"
            ),
            start=sample_ordinal,
            end=sample_ordinal + 1,
            reason="CURRENT11_GEOMETRY_AUTHORITY_INVALID",
        ),
    }
    singleton_batch["covapie_current11_authoritative_training_supervision_v1"] = (
        singleton_authority
    )
    return singleton_batch, singleton_runtime, singleton_authority


def _tensorize_current11_v1(
    *,
    sample_identity: str,
    task_id: int,
    device: object,
    epoch: object,
    task_schedule_seed: object,
    batch: object,
    runtime_result: object,
    authoritative_supervision: object,
) -> CovapieExpandedCysSgTensorizedSampleV1:
    if (
        type(batch) is not dict
        or type(runtime_result) is not dict
        or type(authoritative_supervision) is not dict
        or not _MODEL_BATCH_CORE_FIELDS_V1.issubset(batch)
    ):
        _fail("CURRENT11_PUBLISHED_INPUTS_REQUIRED")
    sample_keys = authoritative_supervision.get("sample_keys")
    if type(sample_keys) is not list or sample_keys.count(sample_identity) != 1:
        _fail("CURRENT11_SAMPLE_IDENTITY_NOT_EXACTLY_ONE")
    if type(task_schedule_seed) is not int or type(task_schedule_seed) is bool:
        _fail("CURRENT11_TASK_SCHEDULE_SEED_INVALID")
    if epoch is None:
        matching_epochs = tuple(
            candidate_epoch
            for candidate_epoch in range(5)
            if canonical_task_id_for_covapie_current11_sample_v1(
                sample_key=sample_identity,
                epoch=candidate_epoch,
                task_schedule_seed=task_schedule_seed,
            ) == task_id
        )
        if len(matching_epochs) != 1:
            _fail("CURRENT11_TASK_SCHEDULE_RESOLUTION_INVALID")
        resolved_epoch = matching_epochs[0]
    else:
        if type(epoch) is not int or type(epoch) is bool or epoch < 0:
            _fail("CURRENT11_EPOCH_INVALID")
        resolved_epoch = epoch
        if canonical_task_id_for_covapie_current11_sample_v1(
            sample_key=sample_identity,
            epoch=resolved_epoch,
            task_schedule_seed=task_schedule_seed,
        ) != task_id:
            _fail("CURRENT11_REQUESTED_TASK_SCHEDULE_MISMATCH")
    singleton_batch, singleton_runtime, singleton_authority = (
        _slice_current11_singleton_inputs_v1(
            sample_identity=sample_identity,
            sample_ordinal=sample_keys.index(sample_identity),
            batch=batch,
            runtime_result=runtime_result,
            authoritative_supervision=authoritative_supervision,
        )
    )
    supervision = tensorize_covapie_current11_training_supervision_v1(
        batch=singleton_batch,
        runtime_result=singleton_runtime,
        authoritative_supervision=singleton_authority,
        device=device,
        epoch=resolved_epoch,
        task_schedule_seed=task_schedule_seed,
    )
    if (
        supervision.canonical_task_id.shape != (1,)
        or int(supervision.canonical_task_id[0].item()) != task_id
    ):
        _fail("CURRENT11_DELEGATED_TASK_MISMATCH")
    return CovapieExpandedCysSgTensorizedSampleV1(
        sample_identity=sample_identity,
        role_profile=STRICT_LINKER_PRESENT_V1,
        valid_task_ids=CURRENT11_VALID_TASK_IDS_V1,
        model_input_batch=singleton_batch,
        supervision=supervision,
    )


def tensorize_covapie_expanded_cys_sg_sample_v1(
    *,
    sample_identity: object,
    task_id: object,
    device: object = "cpu",
    epoch: object = None,
    task_schedule_seed: object = 0,
    current11_batch: object = None,
    current11_runtime_result: object = None,
    current11_authoritative_supervision: object = None,
    repository_root: object = None,
    state_root: object = None,
) -> CovapieExpandedCysSgTensorizedSampleV1:
    """Tensorize one strict or direct identity through one Exact5 API.

    Current11 calls must supply the already-published batch/runtime/authority
    triple.  K36 calls resolve their immutable local sources and reject any
    Current11-only inputs.  This API does not collate or execute a model.
    """

    try:
        profile = _profile_for_identity(sample_identity)
        canonical_task_id = _require_task(task_id, profile=profile)
        if type(sample_identity) is not str:
            _fail("SAMPLE_IDENTITY_INVALID")
        identity = sample_identity
        if profile == STRICT_LINKER_PRESENT_V1:
            if repository_root is not None or state_root is not None:
                _fail("CURRENT11_K36_SOURCE_ROOTS_FORBIDDEN")
            return _tensorize_current11_v1(
                sample_identity=identity,
                task_id=canonical_task_id,
                device=device,
                epoch=epoch,
                task_schedule_seed=task_schedule_seed,
                batch=current11_batch,
                runtime_result=current11_runtime_result,
                authoritative_supervision=(
                    current11_authoritative_supervision
                ),
            )
        if any(
            value is not None
            for value in (
                current11_batch,
                current11_runtime_result,
                current11_authoritative_supervision,
            )
        ):
            _fail("K36_CURRENT11_INPUTS_FORBIDDEN")
        if (
            epoch is not None
            or type(task_schedule_seed) is not int
            or task_schedule_seed != 0
        ):
            _fail("K36_EXPLICIT_TASK_DOES_NOT_ACCEPT_SCHEDULE_INPUTS")
        return _tensorize_k36_v1(
            sample_identity=identity,
            task_id=canonical_task_id,
            device=device,
            repository_root=repository_root,
            state_root=state_root,
        )
    except Exception as error:
        _public_error(error)
