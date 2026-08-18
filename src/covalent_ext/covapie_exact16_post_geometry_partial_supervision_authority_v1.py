"""Exact16 observed-complex to POST geometry authority successor V1.

This additive owner freezes the two-component PRE/POST registry, validates the
profile-specific source/provenance chain for the exact Current11 + K36
population, and returns a copied supervision bundle with POST-only partial
supervision.  It never reconstructs PRE geometry and performs no model,
optimizer, Trainer, checkpoint, or state-writing operation.
"""

from __future__ import annotations

import csv
import hashlib
import io
import math
import re
import stat
from dataclasses import dataclass, replace
from pathlib import Path
from typing import NoReturn, Sequence

import torch

from covalent_ext import (
    covapie_current11_trainable_supervision_materializer_v1 as current11_materializer,
)
from covalent_ext import (
    covapie_expanded_cys_sg_mixed_profile_tensorizer_v1 as mixed_tensorizer,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
)
from covalent_ext.covapie_expanded_cys_sg_mixed_profile_batch_scheduler_and_one_batch_smoke_v1 import (
    EXACT16_MEMBER_IDENTITIES_V1,
    CovapieExpandedCysSgMixedBatchV1,
    validate_covapie_expanded_cys_sg_exact16_mixed_batch_v1,
)


__all__ = (
    "COVAPIE_EXACT16_POST_GEOMETRY_PARTIAL_SUPERVISION_AUTHORITY_V1_ERROR",
    "PRE_COVALENT_REACTIVE_PAIR_DISTANCE_ANGSTROM",
    "POST_COVALENT_REACTIVE_PAIR_DISTANCE_ANGSTROM",
    "PRE_COVALENT_REACTIVE_PAIR_DISTANCE_COMPONENT_INDEX_V1",
    "POST_COVALENT_REACTIVE_PAIR_DISTANCE_COMPONENT_INDEX_V1",
    "GEOMETRY_COMPONENT_REGISTRY_V1",
    "OBSERVED_DISTANCE_AGREEMENT_TOLERANCE_ANGSTROM_V1",
    "CovapieExact16GeometryComponentV1",
    "CovapieExact16PostGeometrySourceBindingV1",
    "CovapieExact16PostGeometryAuthorityEvidenceV1",
    "CovapieExact16PostGeometryPartialSupervisionAuthorityResultV1",
    "derive_covapie_exact16_post_geometry_authority_evidence_v1",
    "bind_covapie_exact16_post_geometry_partial_supervision_authority_v1",
    "validate_covapie_exact16_post_geometry_partial_supervision_authority_v1",
)


COVAPIE_EXACT16_POST_GEOMETRY_PARTIAL_SUPERVISION_AUTHORITY_V1_ERROR = (
    "COVAPIE_EXACT16_POST_GEOMETRY_PARTIAL_SUPERVISION_AUTHORITY_V1_ERROR"
)

PRE_COVALENT_REACTIVE_PAIR_DISTANCE_ANGSTROM = (
    "PRE_COVALENT_REACTIVE_PAIR_DISTANCE_ANGSTROM"
)
POST_COVALENT_REACTIVE_PAIR_DISTANCE_ANGSTROM = (
    "POST_COVALENT_REACTIVE_PAIR_DISTANCE_ANGSTROM"
)
PRE_COVALENT_REACTIVE_PAIR_DISTANCE_COMPONENT_INDEX_V1 = 0
POST_COVALENT_REACTIVE_PAIR_DISTANCE_COMPONENT_INDEX_V1 = 1
OBSERVED_DISTANCE_AGREEMENT_TOLERANCE_ANGSTROM_V1 = 0.0015


@dataclass(frozen=True)
class CovapieExact16GeometryComponentV1:
    component_index: int
    semantic_name: str
    unit: str
    formal_definition: str


GEOMETRY_COMPONENT_REGISTRY_V1 = (
    CovapieExact16GeometryComponentV1(
        component_index=0,
        semantic_name=PRE_COVALENT_REACTIVE_PAIR_DISTANCE_ANGSTROM,
        unit="angstrom",
        formal_definition=(
            "distance between the exact authoritative protein reactive atom "
            "and exact authoritative ligand reactive atom in a canonical "
            "authoritative pre-covalent state"
        ),
    ),
    CovapieExact16GeometryComponentV1(
        component_index=1,
        semantic_name=POST_COVALENT_REACTIVE_PAIR_DISTANCE_ANGSTROM,
        unit="angstrom",
        formal_definition=(
            "distance between the same exact authoritative reactive pair in "
            "a resolved authoritative post-covalent state"
        ),
    ),
)


@dataclass(frozen=True)
class CovapieExact16PostGeometrySourceBindingV1:
    source_root_kind: str
    relative_path: str
    sha256: str
    sha256_verified: bool


@dataclass(frozen=True)
class CovapieExact16PostGeometryAuthorityEvidenceV1:
    sample_identity: str
    role_profile: str
    source_complex_identity: str
    source_bindings: tuple[CovapieExact16PostGeometrySourceBindingV1, ...]
    explicit_event_evidence_kind: str
    explicit_event_valid: bool
    protein_endpoint_comp_id: str
    protein_endpoint_atom_id: str
    ligand_endpoint_comp_id: str
    ligand_endpoint_atom_id: str
    protein_endpoint_retained_flat_index: int
    ligand_endpoint_retained_flat_index: int
    protein_endpoint_mapping_count: int
    ligand_endpoint_mapping_count: int
    protein_endpoint_coordinate_angstrom: tuple[float, float, float]
    ligand_endpoint_coordinate_angstrom: tuple[float, float, float]
    recorded_observed_distance_angstrom: float
    distance_agreement_tolerance_angstrom: float
    positive_pair_candidate_index: int
    positive_pair_ligand_flat_index: int
    positive_pair_pocket_flat_index: int
    positive_pair_sample_index: int
    sample_training_admitted: bool
    ligand_endpoint_altloc_identity: str
    event_selected_ligand_altloc_identity: str


@dataclass(frozen=True)
class CovapieExact16PostGeometryPartialSupervisionAuthorityResultV1:
    sample_identities: tuple[str, ...]
    geometry_component_registry: tuple[CovapieExact16GeometryComponentV1, ...]
    authority_evidence: tuple[
        CovapieExact16PostGeometryAuthorityEvidenceV1, ...
    ]
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1


class _AuthorityInvariantError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _fail(reason: str) -> NoReturn:
    raise _AuthorityInvariantError(reason)


def _public_error(error: Exception) -> NoReturn:
    if isinstance(error, _AuthorityInvariantError):
        raise ValueError(
            f"{COVAPIE_EXACT16_POST_GEOMETRY_PARTIAL_SUPERVISION_AUTHORITY_V1_ERROR}:"
            f"{error.reason}"
        ) from error
    if (
        type(error) is ValueError
        and str(error).startswith(
            COVAPIE_EXACT16_POST_GEOMETRY_PARTIAL_SUPERVISION_AUTHORITY_V1_ERROR
        )
    ):
        raise error
    raise ValueError(
        COVAPIE_EXACT16_POST_GEOMETRY_PARTIAL_SUPERVISION_AUTHORITY_V1_ERROR
    ) from error


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_PATH_TYPE = type(Path())
_CURRENT11_INDEX_RELATIVE_PATH = Path(
    "data/derived/covalent_small/"
    "covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0/"
    "unified_sample_index.csv"
)
_CURRENT11_INDEX_SHA256 = (
    "d610e7171ad976f16055584582335ce756ed0210e6c15d6b55a1a234bc92c326"
)
_CURRENT11_MAPPING_RELATIVE_PATH = Path(
    "data/derived/covalent_small/"
    "covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_"
    "evidence_validation_v1/"
    "covapie_atom_pair_atom_table_mapping_validation_matrix.csv"
)
_CURRENT11_MAPPING_SHA256 = (
    "9f26b25ed11d186a02a1f859de10a105605ce3af13805ac5a4be1ad73199df45"
)
_CURRENT11_IDENTITY_AND_REACTIVE_ATOM_V1 = (
    ("CYS_SG_SAMPLE_INDEX_000001", "6BV6", "JUG", "CAG"),
    ("CYS_SG_SAMPLE_INDEX_000002", "6BV8", "JUG", "CAG"),
    ("CYS_SG_SAMPLE_INDEX_000003", "6BV5", "JUG", "CAG"),
    ("CYS_SG_SAMPLE_INDEX_000004", "1AEC", "E64", "C2"),
    ("CYS_SG_SAMPLE_INDEX_000005", "1AIM", "ZYA", "CM"),
    ("CYS_SG_SAMPLE_INDEX_000006", "1AU3", "PCM", "C22"),
    ("CYS_SG_SAMPLE_INDEX_000007", "1AU4", "INP", "C17"),
    ("CYS_SG_SAMPLE_INDEX_000008", "1AYU", "INA", "C21"),
    ("CYS_SG_SAMPLE_INDEX_000009", "1AYV", "IN6", "C21"),
    ("CYS_SG_SAMPLE_INDEX_000010", "1AYW", "IN3", "C21"),
    ("CYS_SG_SAMPLE_INDEX_000011", "1B02", "UFP", "C6"),
)
_EXPECTED_IDENTITY = {
    sample: (pdb_id, ligand_comp_id, ligand_atom_id)
    for sample, pdb_id, ligand_comp_id, ligand_atom_id
    in _CURRENT11_IDENTITY_AND_REACTIVE_ATOM_V1
}
_EXPECTED_IDENTITY.update({
    identity: (identity.split("/", 1)[0], "K36", "C21")
    for identity in mixed_tensorizer.K36_MEMBER_IDENTITIES_V1
})
_EXPECTED_K36_ALTLOC_V1 = {
    identity: ("B" if identity == "5WKJ/K36" else "NONE")
    for identity in mixed_tensorizer.K36_MEMBER_IDENTITIES_V1
}


def _require_root(value: object, *, reason: str) -> Path:
    if type(value) is not _PATH_TYPE or not value.is_absolute():
        _fail(reason)
    path = value
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise _AuthorityInvariantError(reason) from error
    if (
        resolved != path
        or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
    ):
        _fail(reason)
    return path


def _safe_file(root: Path, relative: object) -> Path:
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
    current = root
    try:
        for part in pure.parts:
            current = current / part
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                _fail("SOURCE_SYMLINK_FORBIDDEN")
        if not current.resolve(strict=True).is_relative_to(root):
            _fail("SOURCE_PATH_ESCAPE")
        metadata = current.lstat()
    except _AuthorityInvariantError:
        raise
    except (OSError, RuntimeError) as error:
        raise _AuthorityInvariantError("SOURCE_FILE_UNAVAILABLE") from error
    if not stat.S_ISREG(metadata.st_mode):
        _fail("SOURCE_FILE_UNAVAILABLE")
    return current


def _read_source(
    root: Path, relative: object, *, expected_sha256: str | None = None
) -> tuple[bytes, str]:
    path = _safe_file(root, relative)
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise _AuthorityInvariantError("SOURCE_FILE_UNAVAILABLE") from error
    digest = hashlib.sha256(payload).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        _fail("SOURCE_SHA256_MISMATCH")
    return payload, digest


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    try:
        text = payload.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        rows = list(reader)
    except (UnicodeDecodeError, csv.Error) as error:
        raise _AuthorityInvariantError("SOURCE_CSV_INVALID") from error
    if reader.fieldnames is None or not rows:
        _fail("SOURCE_CSV_INVALID")
    return rows


def _binding(
    *, root_kind: str, relative_path: str, sha256: str
) -> CovapieExact16PostGeometrySourceBindingV1:
    return CovapieExact16PostGeometrySourceBindingV1(
        source_root_kind=root_kind,
        relative_path=relative_path,
        sha256=sha256,
        sha256_verified=True,
    )


def _batch_offsets(counts: torch.Tensor, *, reason: str) -> tuple[int, ...]:
    if (
        not isinstance(counts, torch.Tensor)
        or counts.dtype != torch.long
        or counts.shape != (16,)
        or bool((counts <= 0).any().item())
    ):
        _fail(reason)
    result = [0]
    for value in counts.tolist():
        result.append(result[-1] + int(value))
    return tuple(result)


def _coordinates(value: object, *, reason: str) -> tuple[float, float, float]:
    if type(value) not in (list, tuple) or len(value) != 3:
        _fail(reason)
    result = tuple(value)
    if any(type(item) is not float or not math.isfinite(item) for item in result):
        _fail(reason)
    return result  # type: ignore[return-value]


def _one_row_by_key(
    rows: Sequence[dict[str, str]], *, field: str, value: str, reason: str
) -> dict[str, str]:
    matches = [row for row in rows if row.get(field) == value]
    if len(matches) != 1:
        _fail(reason)
    return matches[0]


def _float_text(
    value: object, *, reason: str, positive: bool = False
) -> float:
    if type(value) is not str:
        _fail(reason)
    try:
        result = float(value)
    except (ValueError, OverflowError) as error:
        raise _AuthorityInvariantError(reason) from error
    if not math.isfinite(result) or (positive and result <= 0):
        _fail(reason)
    return result


def _close(left: float, right: float, *, tolerance: float) -> bool:
    return math.isfinite(left) and math.isfinite(right) and abs(left - right) <= tolerance


def _positive_pair(
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1,
    *,
    sample_index: int,
) -> tuple[int, int, int]:
    positive_index = int(
        supervision.pair_positive_candidate_index[sample_index].item()
    )
    if (
        not bool(supervision.pair_positive_candidate_valid[sample_index].item())
        or not 0 <= positive_index < len(supervision.pair_candidate_is_positive)
        or not bool(supervision.pair_candidate_is_positive[positive_index].item())
    ):
        _fail("POSITIVE_PAIR_INVALID")
    return (
        positive_index,
        int(supervision.pair_candidate_ligand_flat_index[positive_index].item()),
        int(supervision.pair_candidate_pocket_flat_index[positive_index].item()),
    )


def _extract_current11_evidence(
    *,
    repository_root: Path,
    mixed_batch: CovapieExpandedCysSgMixedBatchV1,
    current11_machine_authority_payload: object,
    ligand_offsets: tuple[int, ...],
    pocket_offsets: tuple[int, ...],
) -> list[CovapieExact16PostGeometryAuthorityEvidenceV1]:
    try:
        validated_bundle = (
            current11_materializer.build_current11_training_supervision_v1(
                authority_payload=current11_machine_authority_payload
            )
        )
    except Exception as error:
        raise _AuthorityInvariantError(
            "CURRENT11_MACHINE_AUTHORITY_PAYLOAD_INVALID"
        ) from error
    if type(current11_machine_authority_payload) is not dict:
        _fail("CURRENT11_MACHINE_AUTHORITY_PAYLOAD_INVALID")
    payload = current11_machine_authority_payload
    if (
        validated_bundle.get("schema_version")
        != current11_materializer.TRAINABLE_SUPERVISION_MATERIALIZATION_SCHEMA_V1
        or payload.get("schema_version")
        != current11_materializer.MACHINE_AUTHORITY_PAYLOAD_SCHEMA_V1
        or tuple(payload.get("sample_order", ()))
        != mixed_tensorizer.CURRENT11_MEMBER_IDENTITIES_V1
        or type(payload.get("samples")) is not list
    ):
        _fail("CURRENT11_MACHINE_AUTHORITY_PAYLOAD_INVALID")
    payload_samples = payload["samples"]

    index_payload, index_digest = _read_source(
        repository_root,
        str(_CURRENT11_INDEX_RELATIVE_PATH),
        expected_sha256=_CURRENT11_INDEX_SHA256,
    )
    mapping_payload, mapping_digest = _read_source(
        repository_root,
        str(_CURRENT11_MAPPING_RELATIVE_PATH),
        expected_sha256=_CURRENT11_MAPPING_SHA256,
    )
    index_rows = _csv_rows(index_payload)
    mapping_rows = _csv_rows(mapping_payload)
    supervision = mixed_batch.supervision
    model_batch = mixed_batch.model_input_batch
    ligand_model_coordinates = model_batch.get("lig_coords")
    pocket_model_coordinates = model_batch.get("pocket_coords")
    if not isinstance(ligand_model_coordinates, torch.Tensor) or not isinstance(
        pocket_model_coordinates, torch.Tensor
    ):
        _fail("MODEL_COORDINATES_INVALID")

    result: list[CovapieExact16PostGeometryAuthorityEvidenceV1] = []
    for sample_index, expected_identity in enumerate(
        mixed_tensorizer.CURRENT11_MEMBER_IDENTITIES_V1
    ):
        raw_sample = payload_samples[sample_index]
        if type(raw_sample) is not dict:
            _fail("CURRENT11_MACHINE_AUTHORITY_SAMPLE_INVALID")
        sample = raw_sample
        index_row = _one_row_by_key(
            index_rows,
            field="sample_index_row_id",
            value=expected_identity,
            reason="CURRENT11_INDEX_IDENTITY_INVALID",
        )
        expected_pdb, expected_ligand, expected_ligand_atom = _EXPECTED_IDENTITY[
            expected_identity
        ]
        if (
            sample.get("sample_key") != expected_identity
            or sample.get("pdb_id") != expected_pdb
            or sample.get("ligand_comp_id") != expected_ligand
            or sample.get("mandatory_provenance_valid") is not True
            or index_row.get("pdb_id") != expected_pdb
            or index_row.get("ligand_comp_id") != expected_ligand
            or index_row.get("covalent_event_count") != "1"
            or index_row.get("ligand_residue_atom_pair_count") != "1"
        ):
            _fail("CURRENT11_SAMPLE_IDENTITY_OR_PROVENANCE_INVALID")
        target = sample.get("target_residue")
        pair = sample.get("positive_pair")
        ligand_nodes = sample.get("ligand_nodes")
        pocket_nodes = sample.get("pocket_nodes")
        if (
            type(target) is not dict
            or type(pair) is not dict
            or type(ligand_nodes) is not list
            or type(pocket_nodes) is not list
            or target.get("residue_name") != "CYS"
            or target.get("reactive_atom_name") != "SG"
            or pair.get("authority_class") != "AUTHORITATIVE_MACHINE_DERIVED"
        ):
            _fail("CURRENT11_REACTIVE_PAIR_AUTHORITY_INVALID")
        ligand_local = pair.get("ligand_local_index")
        pocket_local = pair.get("pocket_local_index")
        if (
            type(ligand_local) is not int
            or type(pocket_local) is not int
            or not 0 <= ligand_local < len(ligand_nodes)
            or not 0 <= pocket_local < len(pocket_nodes)
        ):
            _fail("CURRENT11_REACTIVE_PAIR_MAPPING_INVALID")
        ligand_node = ligand_nodes[ligand_local]
        pocket_node = pocket_nodes[pocket_local]
        if (
            type(ligand_node) is not dict
            or type(pocket_node) is not dict
            or ligand_node.get("atom_name") != expected_ligand_atom
            or pocket_node.get("atom_name") != "SG"
            or pocket_node.get("residue_name") != "CYS"
        ):
            _fail("CURRENT11_REACTIVE_ENDPOINT_INVALID")

        event_relative = index_row.get("covalent_event_table_path")
        pair_relative = index_row.get("ligand_residue_atom_pair_table_path")
        event_payload, event_digest = _read_source(
            repository_root, event_relative
        )
        pair_payload, pair_digest = _read_source(
            repository_root, pair_relative
        )
        event_rows = _csv_rows(event_payload)
        pair_rows = _csv_rows(pair_payload)
        if len(event_rows) != 1 or len(pair_rows) != 1:
            _fail("CURRENT11_EXPLICIT_EVENT_NOT_EXACTLY_ONE")
        event = event_rows[0]
        pair_observation = pair_rows[0]
        if (
            event.get("sample_preparation_input_id")
            != index_row.get("sample_preparation_input_id")
            or event.get("pdb_id") != expected_pdb
            or event.get("expected_het_id") != expected_ligand
            or event.get("conn_id") != index_row.get("conn_id")
            or event.get("conn_type_id") != "covale"
            or event.get("event_source") not in {
                "raw_struct_conn",
                "raw_struct_conn_step14al_crosschecked",
            }
            or event.get("event_status") != "validated"
            or event.get("residue_comp_id") != "CYS"
            or event.get("residue_atom_name") != "SG"
            or event.get("ligand_comp_id") != expected_ligand
            or event.get("ligand_atom_name") != expected_ligand_atom
            or event.get("covalent_bond_atom_pair")
            != f"SG--{expected_ligand_atom}"
        ):
            _fail("CURRENT11_EXPLICIT_EVENT_INVALID")
        if (
            pair_observation.get("sample_preparation_input_id")
            != index_row.get("sample_preparation_input_id")
            or pair_observation.get("pdb_id") != expected_pdb
            or pair_observation.get("expected_het_id") != expected_ligand
            or pair_observation.get("residue_atom_name") != "SG"
            or pair_observation.get("ligand_atom_name") != expected_ligand_atom
            or pair_observation.get("validation_status") not in {
                "validated_from_raw_struct_conn_and_atom_site",
                "validated_from_step14al_struct_conn_and_raw_atom_site",
            }
            or pair_observation.get("residue_atom_site_id")
            != pocket_node.get("atom_site_id")
            or pair_observation.get("ligand_atom_site_id")
            != ligand_node.get("atom_site_id")
        ):
            _fail("CURRENT11_OBSERVED_PAIR_RECORD_INVALID")

        mapping_by_role: dict[str, dict[str, str]] = {}
        for row in mapping_rows:
            if row.get("sample_index_row_id") == expected_identity:
                role = row.get("entity_role")
                if type(role) is not str or role in mapping_by_role:
                    _fail("CURRENT11_MAPPING_RECORD_INVALID")
                mapping_by_role[role] = row
        if set(mapping_by_role) != {"ligand_atom", "target_residue_atom"}:
            _fail("CURRENT11_MAPPING_RECORD_INVALID")
        source_bindings = [
            _binding(
                root_kind="repository",
                relative_path=str(_CURRENT11_INDEX_RELATIVE_PATH),
                sha256=index_digest,
            ),
            _binding(
                root_kind="repository",
                relative_path=str(_CURRENT11_MAPPING_RELATIVE_PATH),
                sha256=mapping_digest,
            ),
            _binding(
                root_kind="repository",
                relative_path=event_relative,
                sha256=event_digest,
            ),
            _binding(
                root_kind="repository",
                relative_path=pair_relative,
                sha256=pair_digest,
            ),
        ]
        for role, expected_path, expected_source_index in (
            ("ligand_atom", index_row.get("ligand_atom_table_path"), ligand_node.get("source_row_index")),
            ("target_residue_atom", index_row.get("pocket_atom_table_path"), pocket_node.get("source_row_index")),
        ):
            mapping = mapping_by_role[role]
            if (
                mapping.get("target_table_path") != expected_path
                or mapping.get("candidate_match_count") != "1"
                or mapping.get("expected_match_count") != "1"
                or mapping.get("matched_row_index_0based")
                != str(expected_source_index)
                or mapping.get("mapping_outcome") != "mapped"
                or mapping.get("mapping_reason") != "exact_one_identity_mapping"
                or mapping.get("coordinate_crosscheck_passed") != "true"
                or mapping.get("source_row_order_sha_bound") != "true"
                or mapping.get("verified") != "true"
                or not isinstance(expected_path, str)
            ):
                _fail("CURRENT11_MAPPING_RECORD_INVALID")
            _table_payload, table_digest = _read_source(
                repository_root,
                expected_path,
                expected_sha256=mapping.get("target_table_sha256"),
            )
            source_bindings.append(_binding(
                root_kind="repository",
                relative_path=expected_path,
                sha256=table_digest,
            ))

        protein_coordinate = _coordinates(
            pocket_node.get("coordinates"),
            reason="CURRENT11_PROTEIN_COORDINATE_INVALID",
        )
        ligand_coordinate = _coordinates(
            ligand_node.get("coordinates"),
            reason="CURRENT11_LIGAND_COORDINATE_INVALID",
        )
        pair_protein_coordinate = tuple(
            _float_text(
                pair_observation.get(f"residue_{axis}"),
                reason="CURRENT11_PAIR_COORDINATE_INVALID",
            )
            for axis in ("x", "y", "z")
        )
        pair_ligand_coordinate = tuple(
            _float_text(
                pair_observation.get(f"ligand_{axis}"),
                reason="CURRENT11_PAIR_COORDINATE_INVALID",
            )
            for axis in ("x", "y", "z")
        )
        if any(
            not _close(left, right, tolerance=1e-5)
            for left, right in zip(protein_coordinate, pair_protein_coordinate)
        ) or any(
            not _close(left, right, tolerance=1e-5)
            for left, right in zip(ligand_coordinate, pair_ligand_coordinate)
        ):
            _fail("CURRENT11_PAIR_COORDINATE_MISMATCH")
        observed = _float_text(
            pair_observation.get("bond_distance_angstrom"),
            reason="CURRENT11_OBSERVED_DISTANCE_INVALID",
            positive=True,
        )
        index_observed = _float_text(
            index_row.get("bond_distance_angstrom"),
            reason="CURRENT11_OBSERVED_DISTANCE_INVALID",
            positive=True,
        )
        sample_observed = sample.get("observed_complex_pair_distance_angstrom")
        if (
            type(sample_observed) is not float
            or sample.get("observed_complex_pair_distance_valid") is not True
            or not _close(
                observed,
                index_observed,
                tolerance=OBSERVED_DISTANCE_AGREEMENT_TOLERANCE_ANGSTROM_V1,
            )
            or not _close(
                observed,
                sample_observed,
                tolerance=OBSERVED_DISTANCE_AGREEMENT_TOLERANCE_ANGSTROM_V1,
            )
        ):
            _fail("CURRENT11_OBSERVED_DISTANCE_SOURCE_MISMATCH")

        ligand_flat = ligand_offsets[sample_index] + ligand_local
        pocket_flat = pocket_offsets[sample_index] + pocket_local
        positive_index, positive_ligand, positive_pocket = _positive_pair(
            supervision, sample_index=sample_index
        )
        if positive_ligand != ligand_flat or positive_pocket != pocket_flat:
            _fail("CURRENT11_POSITIVE_PAIR_MISMATCH")
        if (
            not torch.allclose(
                ligand_model_coordinates[ligand_flat].detach().cpu(),
                torch.tensor(ligand_coordinate),
                rtol=0,
                atol=1e-5,
            )
            or not torch.allclose(
                pocket_model_coordinates[pocket_flat].detach().cpu(),
                torch.tensor(protein_coordinate),
                rtol=0,
                atol=1e-5,
            )
        ):
            _fail("CURRENT11_RETAINED_MODEL_COORDINATE_MISMATCH")
        result.append(CovapieExact16PostGeometryAuthorityEvidenceV1(
            sample_identity=expected_identity,
            role_profile=mixed_tensorizer.STRICT_LINKER_PRESENT_V1,
            source_complex_identity=f"{expected_pdb}/{expected_ligand}",
            source_bindings=tuple(source_bindings),
            explicit_event_evidence_kind="RAW_STRUCT_CONN_EXACT_ENDPOINT_PAIR",
            explicit_event_valid=True,
            protein_endpoint_comp_id="CYS",
            protein_endpoint_atom_id="SG",
            ligand_endpoint_comp_id=expected_ligand,
            ligand_endpoint_atom_id=expected_ligand_atom,
            protein_endpoint_retained_flat_index=pocket_flat,
            ligand_endpoint_retained_flat_index=ligand_flat,
            protein_endpoint_mapping_count=int(
                mapping_by_role["target_residue_atom"]["candidate_match_count"]
            ),
            ligand_endpoint_mapping_count=int(
                mapping_by_role["ligand_atom"]["candidate_match_count"]
            ),
            protein_endpoint_coordinate_angstrom=protein_coordinate,
            ligand_endpoint_coordinate_angstrom=ligand_coordinate,
            recorded_observed_distance_angstrom=observed,
            distance_agreement_tolerance_angstrom=(
                OBSERVED_DISTANCE_AGREEMENT_TOLERANCE_ANGSTROM_V1
            ),
            positive_pair_candidate_index=positive_index,
            positive_pair_ligand_flat_index=positive_ligand,
            positive_pair_pocket_flat_index=positive_pocket,
            positive_pair_sample_index=sample_index,
            sample_training_admitted=bool(
                supervision.sample_training_admitted[sample_index].item()
            ),
            ligand_endpoint_altloc_identity="NOT_APPLICABLE",
            event_selected_ligand_altloc_identity="NOT_APPLICABLE",
        ))
    return result


def _extract_k36_evidence(
    *,
    repository_root: Path,
    state_root: Path,
    mixed_batch: CovapieExpandedCysSgMixedBatchV1,
    ligand_offsets: tuple[int, ...],
    pocket_offsets: tuple[int, ...],
) -> list[CovapieExact16PostGeometryAuthorityEvidenceV1]:
    carrier_payload = mixed_tensorizer._read_exact_file(
        state_root,
        mixed_tensorizer.K36_EFFECTIVE_CARRIER_RELATIVE_PATH_V1,
        expected_sha256=mixed_tensorizer.K36_EFFECTIVE_CARRIER_SHA256_V1,
    )
    records = mixed_tensorizer._validated_k36_carrier_semantics_v1(
        carrier_payload
    )
    structural_payload = mixed_tensorizer._read_exact_file(
        repository_root,
        mixed_tensorizer.K36_STRUCTURAL_EVIDENCE_RELATIVE_PATH_V1,
        expected_sha256=mixed_tensorizer.K36_STRUCTURAL_EVIDENCE_SHA256_V1,
    )
    structural_samples, topology = (
        mixed_tensorizer._validated_k36_structural_semantics_v1(
            structural_payload
        )
    )
    supervision = mixed_batch.supervision
    model_batch = mixed_batch.model_input_batch
    ligand_model_coordinates = model_batch.get("lig_coords")
    pocket_model_coordinates = model_batch.get("pocket_coords")
    if not isinstance(ligand_model_coordinates, torch.Tensor) or not isinstance(
        pocket_model_coordinates, torch.Tensor
    ):
        _fail("MODEL_COORDINATES_INVALID")

    result: list[CovapieExact16PostGeometryAuthorityEvidenceV1] = []
    for local_ordinal, identity in enumerate(
        mixed_tensorizer.K36_MEMBER_IDENTITIES_V1
    ):
        sample_index = 11 + local_ordinal
        structural_sample = structural_samples[identity]
        sources = mixed_tensorizer._validated_k36_sample_sources_v1(
            repository_root=repository_root,
            record=records[identity],
            structural_sample=structural_sample,
            topology=topology,
        )
        explicit_event = structural_sample.get("explicit_event")
        raw_source = structural_sample.get("raw_source")
        if type(explicit_event) is not dict or type(raw_source) is not dict:
            _fail("K36_SOURCE_PROVENANCE_INVALID")
        event_edge = explicit_event.get("protein_ligand_covalent_event_edge")
        protein_endpoint = explicit_event.get("protein_endpoint")
        ligand_endpoint = explicit_event.get("ligand_endpoint")
        if (
            type(event_edge) is not dict
            or type(protein_endpoint) is not dict
            or type(ligand_endpoint) is not dict
            or event_edge.get("evidence_kind")
            != "MMCIF_STRUCT_CONN_EXACT_ENDPOINT_PAIR"
        ):
            _fail("K36_EXPLICIT_EVENT_INVALID")
        ligand_rows = sources["ligand_rows"]
        pocket_rows = sources["pocket_rows"]
        ligand_local = sources["ligand_index"]["C21"]
        pocket_local = sources["target_sg_index"]
        ligand_row = ligand_rows[ligand_local]
        pocket_row = pocket_rows[pocket_local]
        ligand_matches = [
            index for index, row in enumerate(ligand_rows)
            if mixed_tensorizer._identity_matches(row, ligand_endpoint)
        ]
        protein_matches = [
            index for index, row in enumerate(pocket_rows)
            if mixed_tensorizer._identity_matches(row, protein_endpoint)
        ]
        if ligand_matches != [ligand_local] or protein_matches != [pocket_local]:
            _fail("K36_REACTIVE_ENDPOINT_MAPPING_INVALID")
        ligand_coordinate = tuple(
            float(ligand_row[axis]) for axis in ("x", "y", "z")
        )
        protein_coordinate = tuple(
            float(pocket_row[axis]) for axis in ("x", "y", "z")
        )
        if any(
            not math.isfinite(value)
            for value in ligand_coordinate + protein_coordinate
        ):
            _fail("K36_REACTIVE_ENDPOINT_COORDINATE_INVALID")
        ligand_flat = ligand_offsets[sample_index] + ligand_local
        pocket_flat = pocket_offsets[sample_index] + pocket_local
        positive_index, positive_ligand, positive_pocket = _positive_pair(
            supervision, sample_index=sample_index
        )
        if positive_ligand != ligand_flat or positive_pocket != pocket_flat:
            _fail("K36_POSITIVE_PAIR_MISMATCH")
        if (
            not torch.allclose(
                ligand_model_coordinates[ligand_flat].detach().cpu(),
                torch.tensor(ligand_coordinate),
                rtol=0,
                atol=1e-5,
            )
            or not torch.allclose(
                pocket_model_coordinates[pocket_flat].detach().cpu(),
                torch.tensor(protein_coordinate),
                rtol=0,
                atol=1e-5,
            )
        ):
            _fail("K36_RETAINED_MODEL_COORDINATE_MISMATCH")
        observed = math.dist(ligand_coordinate, protein_coordinate)
        raw_path = raw_source.get("path")
        raw_sha256 = raw_source.get("sha256")
        if (
            type(raw_path) is not str
            or type(raw_sha256) is not str
            or _SHA256.fullmatch(raw_sha256) is None
        ):
            _fail("K36_RAW_SOURCE_BINDING_INVALID")
        selected_altloc = ligand_endpoint.get("label_alt_id")
        retained_altloc = ligand_row.get("label_alt_id")
        if type(selected_altloc) is not str or type(retained_altloc) is not str:
            _fail("K36_ALTLOC_IDENTITY_INVALID")
        result.append(CovapieExact16PostGeometryAuthorityEvidenceV1(
            sample_identity=identity,
            role_profile=mixed_tensorizer.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1,
            source_complex_identity=identity,
            source_bindings=(
                _binding(
                    root_kind="state",
                    relative_path=str(
                        mixed_tensorizer.K36_EFFECTIVE_CARRIER_RELATIVE_PATH_V1
                    ),
                    sha256=mixed_tensorizer.K36_EFFECTIVE_CARRIER_SHA256_V1,
                ),
                _binding(
                    root_kind="repository",
                    relative_path=str(
                        mixed_tensorizer.K36_STRUCTURAL_EVIDENCE_RELATIVE_PATH_V1
                    ),
                    sha256=mixed_tensorizer.K36_STRUCTURAL_EVIDENCE_SHA256_V1,
                ),
                _binding(
                    root_kind="repository",
                    relative_path=raw_path,
                    sha256=raw_sha256,
                ),
            ),
            explicit_event_evidence_kind="MMCIF_STRUCT_CONN_EXACT_ENDPOINT_PAIR",
            explicit_event_valid=True,
            protein_endpoint_comp_id=str(protein_endpoint.get("auth_comp_id")),
            protein_endpoint_atom_id=str(protein_endpoint.get("auth_atom_id")),
            ligand_endpoint_comp_id=str(ligand_endpoint.get("auth_comp_id")),
            ligand_endpoint_atom_id=str(ligand_endpoint.get("auth_atom_id")),
            protein_endpoint_retained_flat_index=pocket_flat,
            ligand_endpoint_retained_flat_index=ligand_flat,
            protein_endpoint_mapping_count=len(protein_matches),
            ligand_endpoint_mapping_count=len(ligand_matches),
            protein_endpoint_coordinate_angstrom=protein_coordinate,
            ligand_endpoint_coordinate_angstrom=ligand_coordinate,
            recorded_observed_distance_angstrom=observed,
            distance_agreement_tolerance_angstrom=(
                OBSERVED_DISTANCE_AGREEMENT_TOLERANCE_ANGSTROM_V1
            ),
            positive_pair_candidate_index=positive_index,
            positive_pair_ligand_flat_index=positive_ligand,
            positive_pair_pocket_flat_index=positive_pocket,
            positive_pair_sample_index=sample_index,
            sample_training_admitted=bool(
                supervision.sample_training_admitted[sample_index].item()
            ),
            ligand_endpoint_altloc_identity=retained_altloc,
            event_selected_ligand_altloc_identity=selected_altloc,
        ))
    return result


def _validate_unbound_geometry(
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1,
) -> None:
    target = supervision.pre_post_geometry_target_angstrom
    valid = supervision.pre_post_geometry_component_valid_mask
    loss = supervision.pre_post_geometry_component_loss_mask
    observed = supervision.observed_complex_pair_distance_angstrom
    observed_valid = supervision.observed_complex_pair_distance_valid
    if (
        target.shape != (16, 2)
        or not target.dtype.is_floating_point
        or valid.dtype != torch.bool
        or valid.shape != (16, 2)
        or loss.dtype != torch.bool
        or loss.shape != (16, 2)
        or observed.shape != (16, 1)
        or not observed.dtype.is_floating_point
        or observed_valid.dtype != torch.bool
        or observed_valid.shape != (16, 1)
    ):
        _fail("GEOMETRY_FIELD_SHAPE_OR_DTYPE_INVALID")
    if bool(torch.isfinite(target[:, 0]).any().item()):
        _fail("PRE_FINITE_TARGET_WITHOUT_AUTHORITY")
    if bool(valid[:, 0].any().item()):
        _fail("PRE_VALID_WITHOUT_AUTHORITY")
    if bool(loss[:, 0].any().item()):
        _fail("PRE_LOSS_WITHOUT_AUTHORITY")
    if (
        bool(torch.isfinite(target[:, 1]).any().item())
        or bool(valid[:, 1].any().item())
        or bool(loss[:, 1].any().item())
    ):
        _fail("POST_ALREADY_BOUND_OR_UNAUTHORIZED")
    if (
        not bool(torch.isnan(target).all().item())
        or not bool(observed_valid.all().item())
        or not bool(torch.isfinite(observed).all().item())
        or bool((observed <= 0).any().item())
    ):
        _fail("OBSERVED_GEOMETRY_FIELD_INVALID")


def _validate_evidence(
    *,
    mixed_batch: CovapieExpandedCysSgMixedBatchV1,
    evidence: tuple[CovapieExact16PostGeometryAuthorityEvidenceV1, ...],
) -> None:
    if (
        len(evidence) != 16
        or tuple(item.sample_identity for item in evidence)
        != EXACT16_MEMBER_IDENTITIES_V1
    ):
        _fail("EXACT16_AUTHORITY_EVIDENCE_POPULATION_INVALID")
    supervision = mixed_batch.supervision
    model_batch = mixed_batch.model_input_batch
    ligand_coordinates = model_batch.get("lig_coords")
    pocket_coordinates = model_batch.get("pocket_coords")
    ligand_mask = model_batch.get("lig_mask")
    pocket_mask = model_batch.get("pocket_mask")
    if any(
        not isinstance(value, torch.Tensor)
        for value in (
            ligand_coordinates, pocket_coordinates, ligand_mask, pocket_mask
        )
    ):
        _fail("MODEL_ENDPOINT_BUFFERS_INVALID")
    assert isinstance(ligand_coordinates, torch.Tensor)
    assert isinstance(pocket_coordinates, torch.Tensor)
    assert isinstance(ligand_mask, torch.Tensor)
    assert isinstance(pocket_mask, torch.Tensor)
    for sample_index, item in enumerate(evidence):
        if type(item) is not CovapieExact16PostGeometryAuthorityEvidenceV1:
            _fail("AUTHORITY_EVIDENCE_TYPE_INVALID")
        expected_pdb, expected_ligand, expected_ligand_atom = _EXPECTED_IDENTITY[
            item.sample_identity
        ]
        expected_profile = (
            mixed_tensorizer.STRICT_LINKER_PRESENT_V1
            if sample_index < 11
            else mixed_tensorizer.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1
        )
        expected_event_kind = (
            "RAW_STRUCT_CONN_EXACT_ENDPOINT_PAIR"
            if sample_index < 11
            else "MMCIF_STRUCT_CONN_EXACT_ENDPOINT_PAIR"
        )
        if (
            item.role_profile != expected_profile
            or item.source_complex_identity
            != f"{expected_pdb}/{expected_ligand}"
            or item.explicit_event_evidence_kind != expected_event_kind
            or item.explicit_event_valid is not True
        ):
            _fail("EXPLICIT_EVENT_OR_SOURCE_IDENTITY_INVALID")
        if (
            item.protein_endpoint_comp_id != "CYS"
            or item.protein_endpoint_atom_id != "SG"
            or item.ligand_endpoint_comp_id != expected_ligand
            or item.ligand_endpoint_atom_id != expected_ligand_atom
        ):
            _fail("REACTIVE_ENDPOINT_IDENTITY_INVALID")
        if (
            type(item.source_bindings) is not tuple
            or not item.source_bindings
            or any(
                type(binding) is not CovapieExact16PostGeometrySourceBindingV1
                or binding.source_root_kind not in {"repository", "state"}
                or type(binding.relative_path) is not str
                or not binding.relative_path
                or type(binding.sha256) is not str
                or _SHA256.fullmatch(binding.sha256) is None
                or binding.sha256_verified is not True
                for binding in item.source_bindings
            )
        ):
            _fail("SOURCE_SHA256_BINDING_INVALID")
        if (
            type(item.protein_endpoint_mapping_count) is not int
            or item.protein_endpoint_mapping_count != 1
            or type(item.ligand_endpoint_mapping_count) is not int
            or item.ligand_endpoint_mapping_count != 1
        ):
            _fail("REACTIVE_ENDPOINT_MAPPING_NOT_UNIQUE")
        ligand_flat = item.ligand_endpoint_retained_flat_index
        pocket_flat = item.protein_endpoint_retained_flat_index
        if (
            type(ligand_flat) is not int
            or type(pocket_flat) is not int
            or not 0 <= ligand_flat < len(ligand_coordinates)
            or not 0 <= pocket_flat < len(pocket_coordinates)
            or int(ligand_mask[ligand_flat].item()) != sample_index
            or int(pocket_mask[pocket_flat].item()) != sample_index
        ):
            _fail("REACTIVE_ENDPOINT_NOT_RETAINED_OR_CROSS_SAMPLE")
        protein_coordinate = item.protein_endpoint_coordinate_angstrom
        ligand_coordinate = item.ligand_endpoint_coordinate_angstrom
        if (
            type(protein_coordinate) is not tuple
            or len(protein_coordinate) != 3
            or type(ligand_coordinate) is not tuple
            or len(ligand_coordinate) != 3
            or any(
                type(value) is not float or not math.isfinite(value)
                for value in protein_coordinate + ligand_coordinate
            )
        ):
            _fail("REACTIVE_ENDPOINT_COORDINATE_NONFINITE")
        if (
            not torch.allclose(
                ligand_coordinates[ligand_flat].detach().cpu(),
                torch.tensor(ligand_coordinate),
                rtol=0,
                atol=1e-5,
            )
            or not torch.allclose(
                pocket_coordinates[pocket_flat].detach().cpu(),
                torch.tensor(protein_coordinate),
                rtol=0,
                atol=1e-5,
            )
        ):
            _fail("REACTIVE_ENDPOINT_RETAINED_COORDINATE_MISMATCH")
        if (
            type(item.distance_agreement_tolerance_angstrom) is not float
            or item.distance_agreement_tolerance_angstrom
            != OBSERVED_DISTANCE_AGREEMENT_TOLERANCE_ANGSTROM_V1
            or type(item.recorded_observed_distance_angstrom) is not float
            or not math.isfinite(item.recorded_observed_distance_angstrom)
            or item.recorded_observed_distance_angstrom <= 0
        ):
            _fail("OBSERVED_DISTANCE_POLICY_INVALID")
        recomputed = math.dist(protein_coordinate, ligand_coordinate)
        if not _close(
            recomputed,
            item.recorded_observed_distance_angstrom,
            tolerance=item.distance_agreement_tolerance_angstrom,
        ):
            _fail("OBSERVED_DISTANCE_COORDINATE_INCONSISTENT")
        observed_tensor_value = float(
            supervision.observed_complex_pair_distance_angstrom[
                sample_index, 0
            ].item()
        )
        if not bool(
            supervision.observed_complex_pair_distance_valid[
                sample_index, 0
            ].item()
        ) or not _close(
            observed_tensor_value,
            item.recorded_observed_distance_angstrom,
            tolerance=item.distance_agreement_tolerance_angstrom,
        ):
            _fail("OBSERVED_FIELD_SOURCE_MISMATCH")
        actual_positive, actual_ligand, actual_pocket = _positive_pair(
            supervision, sample_index=sample_index
        )
        if (
            item.positive_pair_candidate_index != actual_positive
            or item.positive_pair_ligand_flat_index != actual_ligand
            or item.positive_pair_pocket_flat_index != actual_pocket
            or item.positive_pair_ligand_flat_index != ligand_flat
            or item.positive_pair_pocket_flat_index != pocket_flat
        ):
            _fail("POSITIVE_PAIR_IDENTITY_MISMATCH")
        if (
            item.positive_pair_sample_index != sample_index
            or int(
                supervision.pair_candidate_batch_index[actual_positive].item()
            ) != sample_index
        ):
            _fail("CROSS_SAMPLE_PAIR_MISMATCH")
        if (
            item.sample_training_admitted is not True
            or not bool(
                supervision.sample_training_admitted[sample_index].item()
            )
        ):
            _fail("SAMPLE_NOT_TRAINING_ADMITTED")
        if sample_index < 11:
            if (
                item.ligand_endpoint_altloc_identity != "NOT_APPLICABLE"
                or item.event_selected_ligand_altloc_identity
                != "NOT_APPLICABLE"
            ):
                _fail("CURRENT11_ALTLOC_SEMANTICS_INVALID")
        else:
            expected_altloc = _EXPECTED_K36_ALTLOC_V1[item.sample_identity]
            if (
                item.ligand_endpoint_altloc_identity != expected_altloc
                or item.event_selected_ligand_altloc_identity != expected_altloc
            ):
                _fail("K36_EVENT_SELECTED_ALTLOC_IDENTITY_INVALID")


def derive_covapie_exact16_post_geometry_authority_evidence_v1(
    *,
    mixed_batch: object,
    current11_machine_authority_payload: object,
    repository_root: object,
    state_root: object,
) -> tuple[CovapieExact16PostGeometryAuthorityEvidenceV1, ...]:
    """Re-derive Exact16 POST evidence from the existing authoritative paths."""

    try:
        if type(mixed_batch) is not CovapieExpandedCysSgMixedBatchV1:
            _fail("MIXED_BATCH_TYPE_INVALID")
        _validate_unbound_geometry(mixed_batch.supervision)
        try:
            validate_covapie_expanded_cys_sg_exact16_mixed_batch_v1(
                mixed_batch
            )
        except Exception as error:
            raise _AuthorityInvariantError("HISTORICAL_EXACT16_BATCH_INVALID") from error
        repository = _require_root(
            repository_root, reason="REPOSITORY_ROOT_INVALID"
        )
        state = _require_root(state_root, reason="STATE_ROOT_INVALID")
        ligand_offsets = _batch_offsets(
            mixed_batch.model_input_batch.get("num_lig_atoms"),
            reason="LIGAND_NODE_COUNTS_INVALID",
        )
        pocket_offsets = _batch_offsets(
            mixed_batch.model_input_batch.get("num_pocket_nodes"),
            reason="POCKET_NODE_COUNTS_INVALID",
        )
        evidence = tuple(
            _extract_current11_evidence(
                repository_root=repository,
                mixed_batch=mixed_batch,
                current11_machine_authority_payload=(
                    current11_machine_authority_payload
                ),
                ligand_offsets=ligand_offsets,
                pocket_offsets=pocket_offsets,
            )
            + _extract_k36_evidence(
                repository_root=repository,
                state_root=state,
                mixed_batch=mixed_batch,
                ligand_offsets=ligand_offsets,
                pocket_offsets=pocket_offsets,
            )
        )
        _validate_evidence(mixed_batch=mixed_batch, evidence=evidence)
        return evidence
    except Exception as error:
        _public_error(error)


def _validate_bound_result(
    result: CovapieExact16PostGeometryPartialSupervisionAuthorityResultV1,
) -> None:
    if (
        result.sample_identities != EXACT16_MEMBER_IDENTITIES_V1
        or result.geometry_component_registry != GEOMETRY_COMPONENT_REGISTRY_V1
        or len(result.authority_evidence) != 16
        or not isinstance(
            result.supervision,
            CovapieCurrent11TrainingSupervisionTensorsV1,
        )
    ):
        _fail("BOUND_RESULT_METADATA_INVALID")
    supervision = result.supervision
    target = supervision.pre_post_geometry_target_angstrom
    valid = supervision.pre_post_geometry_component_valid_mask
    loss = supervision.pre_post_geometry_component_loss_mask
    observed = supervision.observed_complex_pair_distance_angstrom
    if (
        target.shape != (16, 2)
        or int(torch.isfinite(target[:, 0]).sum().item()) != 0
        or int(valid[:, 0].sum().item()) != 0
        or int(loss[:, 0].sum().item()) != 0
        or int(torch.isfinite(target[:, 1]).sum().item()) != 16
        or int(valid[:, 1].sum().item()) != 16
        or int(loss[:, 1].sum().item()) != 16
        or not bool(torch.isnan(target[:, 0]).all().item())
        or not bool(torch.isfinite(target[:, 1]).all().item())
        or not bool((target[:, 1] > 0).all().item())
        or target.untyped_storage().data_ptr()
        == observed.untyped_storage().data_ptr()
    ):
        _fail("POST_ONLY_PARTIAL_SUPERVISION_INVALID")
    expected = torch.tensor(
        [
            item.recorded_observed_distance_angstrom
            for item in result.authority_evidence
        ],
        dtype=target.dtype,
        device=target.device,
    )
    if not torch.allclose(
        target[:, 1],
        expected,
        rtol=0,
        atol=OBSERVED_DISTANCE_AGREEMENT_TOLERANCE_ANGSTROM_V1,
    ):
        _fail("POST_TARGET_SOURCE_VALUE_MISMATCH")


def bind_covapie_exact16_post_geometry_partial_supervision_authority_v1(
    *,
    mixed_batch: object,
    authority_evidence: object,
) -> CovapieExact16PostGeometryPartialSupervisionAuthorityResultV1:
    """Validate authority and copy Exact16 supervision with POST-only labels."""

    try:
        if type(mixed_batch) is not CovapieExpandedCysSgMixedBatchV1:
            _fail("MIXED_BATCH_TYPE_INVALID")
        supervision = mixed_batch.supervision
        _validate_unbound_geometry(supervision)
        try:
            validate_covapie_expanded_cys_sg_exact16_mixed_batch_v1(
                mixed_batch
            )
        except Exception as error:
            raise _AuthorityInvariantError("HISTORICAL_EXACT16_BATCH_INVALID") from error
        if type(authority_evidence) not in (list, tuple):
            _fail("AUTHORITY_EVIDENCE_SEQUENCE_INVALID")
        evidence = tuple(authority_evidence)
        _validate_evidence(mixed_batch=mixed_batch, evidence=evidence)
        targets = torch.full_like(
            supervision.pre_post_geometry_target_angstrom, float("nan")
        )
        targets[:, POST_COVALENT_REACTIVE_PAIR_DISTANCE_COMPONENT_INDEX_V1] = (
            torch.tensor(
                [item.recorded_observed_distance_angstrom for item in evidence],
                dtype=targets.dtype,
                device=targets.device,
            )
        )
        valid = torch.zeros_like(
            supervision.pre_post_geometry_component_valid_mask
        )
        loss = torch.zeros_like(
            supervision.pre_post_geometry_component_loss_mask
        )
        valid[:, POST_COVALENT_REACTIVE_PAIR_DISTANCE_COMPONENT_INDEX_V1] = True
        loss[:, POST_COVALENT_REACTIVE_PAIR_DISTANCE_COMPONENT_INDEX_V1] = True
        bound_supervision = replace(
            supervision,
            pre_post_geometry_target_angstrom=targets,
            pre_post_geometry_component_valid_mask=valid,
            pre_post_geometry_component_loss_mask=loss,
        )
        result = (
            CovapieExact16PostGeometryPartialSupervisionAuthorityResultV1(
                sample_identities=EXACT16_MEMBER_IDENTITIES_V1,
                geometry_component_registry=GEOMETRY_COMPONENT_REGISTRY_V1,
                authority_evidence=evidence,
                supervision=bound_supervision,
            )
        )
        _validate_bound_result(result)
        return result
    except Exception as error:
        _public_error(error)


def validate_covapie_exact16_post_geometry_partial_supervision_authority_v1(
    *, result: object
) -> None:
    """Fail closed on a materialized successor result without source I/O."""

    try:
        if type(result) is not (
            CovapieExact16PostGeometryPartialSupervisionAuthorityResultV1
        ):
            _fail("BOUND_RESULT_TYPE_INVALID")
        _validate_bound_result(result)
        return None
    except Exception as error:
        _public_error(error)
