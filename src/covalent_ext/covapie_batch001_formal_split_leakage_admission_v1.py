"""Formal batch-001 leakage-component and split-admission successor V1.

This additive metadata owner reproduces the published 527-event read-only
prediction, recovers complete leakage components, and then supplies all four
eligible new components together to the published split successor.  The
read-only split remains provenance; the independently checked joint assignment
is the split-authority candidate.  No model, tensorization, loss, training,
network, cache, checkpoint, or historical-registry mutation is performed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import copy
import csv
from fractions import Fraction
import hashlib
import io
from itertools import product
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
from typing import Any, Mapping, NoReturn, Sequence

from covalent_ext import covapie_bulk_500_event_executor_v1 as executor_owner
from covalent_ext import covapie_bulk_cys_sg_dataset_expansion_v1 as bulk_owner
from covalent_ext import covapie_cys_sg_dataset_expansion_pipeline_v1 as split_owner


__all__ = (
    "BATCH001_FORMAL_SPLIT_LEAKAGE_ADMISSION_ERROR_V1",
    "OUTPUT_ROOT_RELATIVE_V1",
    "OUTPUT_FILENAMES_V1",
    "FormalComponentAdmissionV1",
    "IndependentFormalAssignmentOracleV1",
    "Batch001FormalSplitAdmissionComputationV1",
    "compute_covapie_batch001_formal_split_admission_v1",
    "validate_covapie_batch001_formal_split_admission_v1",
    "build_covapie_batch001_formal_split_admission_artifacts_v1",
    "materialize_covapie_batch001_formal_split_admission_artifacts_v1",
)


BATCH001_FORMAL_SPLIT_LEAKAGE_ADMISSION_ERROR_V1 = (
    "COVAPIE_BATCH001_FORMAL_SPLIT_LEAKAGE_ADMISSION_V1_ERROR"
)
OUTPUT_ROOT_RELATIVE_V1 = Path(
    "data/derived/covalent_small/"
    "covapie_batch001_formal_split_leakage_admission_v1"
)
SOURCE_BINDING_INVENTORY_V1 = (
    "covapie_batch001_split_admission_source_binding_inventory_v1.csv"
)
COMPONENT_REGISTRY_V1 = (
    "covapie_batch001_formal_leakage_component_registry_v1.json"
)
EVENT_ADMISSION_V1 = "covapie_batch001_formal_event_split_admission_v1.csv"
MANIFEST_V1 = "covapie_batch001_formal_split_leakage_admission_manifest_v1.json"
OUTPUT_FILENAMES_V1 = (
    SOURCE_BINDING_INVENTORY_V1,
    COMPONENT_REGISTRY_V1,
    EVENT_ADMISSION_V1,
    MANIFEST_V1,
)

_DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_ATTEMPT_RELATIVE_TO_REPOSITORY_PARENT_V1 = Path(
    "covapie-state/bulk-500-controlled-execution-v1/attempt-001/"
    "incremental_processing_outcomes_v1.json"
)
_PATH_TYPE = type(Path())

_BRIDGE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_batch001_to_existing_mixed_profile_supervision_bridge_v1"
)
_BRIDGE_READINESS = _BRIDGE_ROOT / (
    "covapie_batch001_event_model_integration_readiness_v1.csv"
)

_FIXED_REPOSITORY_BINDINGS_V1: tuple[tuple[str, str, str, str], ...] = (
    (
        "PUBLISHED_BATCH001_BRIDGE",
        (_BRIDGE_ROOT / "covapie_batch001_event_model_integration_readiness_v1.csv").as_posix(),
        "c7a04904b83b72128ff2b1ea472333bded8c4c04bc70230114baef9265f76cbd",
        "exact batch001 target population and read-only split provenance",
    ),
    (
        "PUBLISHED_BATCH001_BRIDGE",
        (_BRIDGE_ROOT / "covapie_batch001_model_input_source_binding_inventory_v1.csv").as_posix(),
        "02bff8eca47af169264a0bbd2ac2448d9a6c2376a29ad530177fb246cbc95d53",
        "published bridge source lineage",
    ),
    (
        "PUBLISHED_BATCH001_BRIDGE",
        (_BRIDGE_ROOT / "covapie_batch001_model_bound_structural_evidence_v1.json").as_posix(),
        "cca589fa4ac372c159b2e00ba4f59a7c794e21a10f1b3fcffbd477de42cd8f2e",
        "published bridge structural evidence",
    ),
    (
        "PUBLISHED_BATCH001_BRIDGE",
        (_BRIDGE_ROOT / "covapie_batch001_to_existing_mixed_profile_supervision_bridge_manifest_v1.json").as_posix(),
        "0db31ffc0a75c8d3a742ff300e30aac0825aaf01cbfd4d79e163395f29e01ecc",
        "published bridge manifest",
    ),
    (
        "PUBLISHED_SOURCE_OWNER",
        "src/covalent_ext/covapie_batch001_positive_structural_input_v1.py",
        "c4cada3c5d3e8e86176b097cc5546854122162055437e4667288ba2f82629067",
        "batch001 structural source owner",
    ),
    (
        "PUBLISHED_SOURCE_OWNER",
        "src/covalent_ext/covapie_batch001_to_existing_mixed_profile_supervision_bridge_v1.py",
        "168c819e0422b110880676c1a99b82a8531e94f9849a3dcfb7d4c45dbdd73400",
        "batch001 bridge source owner",
    ),
    (
        "PUBLISHED_LEAKAGE_OWNER",
        "src/covalent_ext/covapie_bulk_cys_sg_dataset_expansion_v1.py",
        "ef17777a634284a94662ac3277c02a7fb4efa20375d84fcf88ac074c61e69ce0",
        "read-only predictor and current linking axes",
    ),
    (
        "PUBLISHED_SPLIT_OWNER",
        "src/covalent_ext/covapie_cys_sg_dataset_expansion_pipeline_v1.py",
        "ece0221669400b75c152edd11c18b36d87056d989344e9bc1ae674612f8d4dd6",
        "frozen-group loaders and formal joint split successor",
    ),
    (
        "PUBLISHED_SPLIT_POLICY_OWNER",
        "src/covalent_ext/covapie_unified_leakage_split_materialization_smoke.py",
        "4e565e670ef09fd78c65c5aa799378f3efbd965dc896c65d37a6896d71c5212e",
        "split ranks, target fractions, and policy",
    ),
    (
        "PUBLISHED_EXECUTOR_OWNER",
        "src/covalent_ext/covapie_bulk_500_event_executor_v1.py",
        "8de3f553be8e1ce78077c5920548eff5f7bb73c81632178765489b511ca55d04",
        "exact 250 historical plus 27 control plus 250 incremental context",
    ),
    (
        "FROZEN_LEAKAGE_SPLIT_POPULATION",
        split_owner.PUBLISHED_GROUP_SPLIT_RELATIVE.as_posix(),
        "ed62fcf56ad87d8a49743517329c97aa98d3a781562fa403b4b43a9b9ea3ffc3",
        "five frozen historical groups",
    ),
    (
        "FROZEN_CUMULATIVE_LEAKAGE_REGISTRY",
        bulk_owner.LEAKAGE_REGISTRY_RELATIVE.as_posix(),
        "24a58a6f9cc551c9b38527c1bfbf64aa2661bf1173b8eabcb44428513bfe15c8",
        "two frozen cumulative expansion groups",
    ),
    (
        "FROZEN_REUSABLE_AUTHORITY_REGISTRY",
        bulk_owner.AUTHORITY_REGISTRY_RELATIVE.as_posix(),
        "c6f150bd82b1ea45121aa96e1fefb6af3be64584117cc462f74b2e10fd1913e9",
        "cumulative reference evidence owners",
    ),
    (
        "FROZEN_HISTORICAL_IDENTITY_POPULATION",
        bulk_owner.CURRENT11_INDEX_RELATIVE.as_posix(),
        "d610e7171ad976f16055584582335ce756ed0210e6c15d6b55a1a234bc92c326",
        "historical exact16 identity reconstruction",
    ),
    (
        "FROZEN_HISTORICAL_REFERENCE_EVIDENCE",
        split_owner.BASELINE_LIGAND_EVIDENCE_RELATIVE.as_posix(),
        "982a9f89a89d3a4ad6a3e468cfd16d2fdfd5435cbf6d593e086fbd7fadd3ec73",
        "historical ligand graph and scaffold references",
    ),
    (
        "FROZEN_HISTORICAL_REFERENCE_EVIDENCE",
        split_owner.BASELINE_PROTEIN_EVIDENCE_RELATIVE.as_posix(),
        "51f208c2582bc41c265fa35fa18e71e0e0d0634babe63b9735f084aa486a0d30",
        "historical protein accession and sequence references",
    ),
    (
        "FROZEN_HISTORICAL_REFERENCE_EVIDENCE",
        split_owner.BASELINE_FINAL_GROUP_RELATIVE.as_posix(),
        "768c964f22e19a8fb6232b1fa26c531e53d023042abcd9b1bcca44df2b4f4416",
        "historical sample-to-group membership",
    ),
)

_ATTEMPT_SHA256_V1 = (
    "d891a267dc4493cfceda33b70ab4a200d9f806e1bff38c4b6f39b69a1a3548d7"
)

_EXPECTED_COMPONENTS_V1: dict[str, dict[str, Any]] = {
    "DJK": {
        "leakage_key": "COVAPIE_BULK_READ_ONLY_COMPONENT_V1:227960edeb205fb2b98c7d99043f8909ce56e587c2d8e9fdc535aa5d3c8acd48",
        "group_id": "COVAPIE_EXPANSION_LEAKAGE_GROUP_B603B4C07705F93D",
        "read_only_split": "train",
        "formal_split": "train",
        "identities": ("2HWO/RBS", "2HWP/DJK", "2QLQ/SR2", "2QQ7/SR2", "3LOK/DJK"),
        "event_ids": (
            "COVAPIE_CYS_SG_EVENT_V1:2HWO:A:CYS:345-:SG:C:RBS:C51",
            "COVAPIE_CYS_SG_EVENT_V1:2HWO:B:CYS:345-:SG:D:RBS:C51",
            "COVAPIE_CYS_SG_EVENT_V1:2HWP:A:CYS:345-:SG:C:DJK:C51",
            "COVAPIE_CYS_SG_EVENT_V1:2HWP:B:CYS:345-:SG:D:DJK:C51",
            "COVAPIE_CYS_SG_EVENT_V1:2QLQ:A:CYS:345-:SG:C:SR2:C51",
            "COVAPIE_CYS_SG_EVENT_V1:2QLQ:A:CYS:483-:SG:D:SR2:C51",
            "COVAPIE_CYS_SG_EVENT_V1:2QLQ:B:CYS:345-:SG:E:SR2:C51",
            "COVAPIE_CYS_SG_EVENT_V1:2QQ7:A:CYS:345-:SG:C:SR2:C51",
            "COVAPIE_CYS_SG_EVENT_V1:2QQ7:B:CYS:345-:SG:D:SR2:C51",
            "COVAPIE_CYS_SG_EVENT_V1:3LOK:A:CYS:345-:SG:C:DJK:C51",
            "COVAPIE_CYS_SG_EVENT_V1:3LOK:B:CYS:345-:SG:D:DJK:C51",
        ),
        "target_event_ids": (
            "COVAPIE_CYS_SG_EVENT_V1:3LOK:A:CYS:345-:SG:C:DJK:C51",
            "COVAPIE_CYS_SG_EVENT_V1:3LOK:B:CYS:345-:SG:D:DJK:C51",
        ),
    },
    "LN5": {
        "leakage_key": "COVAPIE_BULK_READ_ONLY_COMPONENT_V1:fd3d6a6c653ec6c2852f7ff88ab15bbf7ab06e9d54a055b5e313ca549c73fe77",
        "group_id": "COVAPIE_EXPANSION_LEAKAGE_GROUP_8B76795E5CE26D95",
        "read_only_split": "train",
        "formal_split": "validation",
        "identities": ("3I4A/LN5",),
        "event_ids": (
            "COVAPIE_CYS_SG_EVENT_V1:3I4A:A:CYS:274-:SG:C:LN5:CZ",
            "COVAPIE_CYS_SG_EVENT_V1:3I4A:B:CYS:274-:SG:D:LN5:CZ",
        ),
        "target_event_ids": (
            "COVAPIE_CYS_SG_EVENT_V1:3I4A:A:CYS:274-:SG:C:LN5:CZ",
            "COVAPIE_CYS_SG_EVENT_V1:3I4A:B:CYS:274-:SG:D:LN5:CZ",
        ),
    },
    "PX5": {
        "leakage_key": "COVAPIE_BULK_READ_ONLY_COMPONENT_V1:65ead884437070087b63b7bf1e4a80ea6dda048ba26dc012eb62577b425254a0",
        "group_id": "COVAPIE_EXPANSION_LEAKAGE_GROUP_AD79B40D8A505F37",
        "read_only_split": "train",
        "formal_split": "validation",
        "identities": ("3O6T/PX5",),
        "event_ids": (
            "COVAPIE_CYS_SG_EVENT_V1:3O6T:A:CYS:37-:SG:E:PX5:C15",
            "COVAPIE_CYS_SG_EVENT_V1:3O6T:C:CYS:37-:SG:G:PX5:C15",
        ),
        "target_event_ids": (
            "COVAPIE_CYS_SG_EVENT_V1:3O6T:A:CYS:37-:SG:E:PX5:C15",
            "COVAPIE_CYS_SG_EVENT_V1:3O6T:C:CYS:37-:SG:G:PX5:C15",
        ),
    },
    "PTG": {
        "leakage_key": "COVAPIE_BULK_READ_ONLY_COMPONENT_V1:de9b0d1526ac235256cb969f47ef40fdb01e8cc1481e4e10dd3823ac04763917",
        "group_id": "COVAPIE_EXPANSION_LEAKAGE_GROUP_3157B39692D4D3EA",
        "read_only_split": "validation",
        "formal_split": "train",
        "identities": (
            "2VV4/6OB", "2VV4/6OC", "2ZK1/PTG", "2ZK2/PTG", "2ZK3/OCX",
            "2ZK4/OCR", "2ZK5/NRO", "3ADW/OCR", "3B0R/GW9",
        ),
        "event_ids": (
            "COVAPIE_CYS_SG_EVENT_V1:2VV4:A:CYS:285-:SG:C:6OC:C8",
            "COVAPIE_CYS_SG_EVENT_V1:2VV4:B:CYS:285-:SG:D:6OB:C10",
            "COVAPIE_CYS_SG_EVENT_V1:2ZK1:A:CYS:285-:SG:C:PTG:C8",
            "COVAPIE_CYS_SG_EVENT_V1:2ZK1:B:CYS:285-:SG:D:PTG:C8",
            "COVAPIE_CYS_SG_EVENT_V1:2ZK2:A:CYS:285-:SG:D:PTG:C8",
            "COVAPIE_CYS_SG_EVENT_V1:2ZK3:A:CYS:285-:SG:C:OCX:C11",
            "COVAPIE_CYS_SG_EVENT_V1:2ZK3:B:CYS:285-:SG:D:OCX:C11",
            "COVAPIE_CYS_SG_EVENT_V1:2ZK4:A:CYS:285-:SG:C:OCR:C9",
            "COVAPIE_CYS_SG_EVENT_V1:2ZK4:B:CYS:285-:SG:D:OCR:C9",
            "COVAPIE_CYS_SG_EVENT_V1:2ZK5:A:CYS:285-:SG:C:NRO:C8",
            "COVAPIE_CYS_SG_EVENT_V1:2ZK5:B:CYS:285-:SG:D:NRO:C8",
            "COVAPIE_CYS_SG_EVENT_V1:3ADW:A:CYS:285-:SG:D:OCR:C9",
            "COVAPIE_CYS_SG_EVENT_V1:3ADW:B:CYS:285-:SG:E:OCR:C9",
            "COVAPIE_CYS_SG_EVENT_V1:3B0R:A:CYS:285-:SG:C:GW9:C9",
            "COVAPIE_CYS_SG_EVENT_V1:3B0R:B:CYS:285-:SG:D:GW9:C9",
        ),
        "target_event_ids": (
            "COVAPIE_CYS_SG_EVENT_V1:2ZK1:A:CYS:285-:SG:C:PTG:C8",
            "COVAPIE_CYS_SG_EVENT_V1:2ZK1:B:CYS:285-:SG:D:PTG:C8",
            "COVAPIE_CYS_SG_EVENT_V1:2ZK2:A:CYS:285-:SG:D:PTG:C8",
        ),
    },
}

_EXPECTED_NDU_EVENT_IDS_V1 = (
    "COVAPIE_CYS_SG_EVENT_V1:3B9H:A:CYS:146-:SG:D:NDU:C6",
    "COVAPIE_CYS_SG_EVENT_V1:3BHL:A:CYS:146-:SG:C:NDU:C6",
    "COVAPIE_CYS_SG_EVENT_V1:3BHL:B:CYS:146-:SG:G:NDU:C6",
    "COVAPIE_CYS_SG_EVENT_V1:3BHR:A:CYS:146-:SG:E:NDU:C6",
)


@dataclass(frozen=True)
class FormalComponentAdmissionV1:
    component_name: str
    leakage_key: str
    classification: str
    linking_axes: tuple[str, ...]
    source_evidence_linking_axis_values: tuple[str, ...]
    full_member_pdb_ligand_identities: tuple[str, ...]
    full_member_canonical_event_ids: tuple[str, ...]
    batch001_target_event_ids: tuple[str, ...]
    non_target_component_event_ids: tuple[str, ...]
    read_only_group_id: str
    read_only_split: str
    formal_group_id: str
    formal_split: str
    group_parity: bool
    split_parity: bool
    formal_assignment_status: str
    formal_assignment_is_authority_candidate: bool


@dataclass(frozen=True)
class IndependentFormalAssignmentOracleV1:
    candidate_assignment_count: int
    valid_assignment_count: int
    group_order: tuple[tuple[str, str, int, int | None], ...]
    new_key_order: tuple[str, ...]
    selected_full_signature: tuple[int, ...]
    selected_sample_counts: tuple[int, int, int]
    selected_group_counts: tuple[int, int, int]
    selected_objective_fractions: tuple[str, str, str]
    best_pre_signature_objective: tuple[str, str, str]
    tie_count_before_signature: int
    selected_assignment: tuple[tuple[str, str, str], ...]
    lexicographic_minimum_tie_break_applied: bool


@dataclass(frozen=True)
class Batch001FormalSplitAdmissionComputationV1:
    source_bindings: tuple[Mapping[str, object], ...]
    context_counts: Mapping[str, int]
    read_only_prediction_reproduced_exactly: bool
    read_only_prediction_is_authority: bool
    read_only_prediction_copied_as_authority: bool
    formal_assignment_mode: str
    formal_joint_assignment_recomputed: bool
    components: tuple[FormalComponentAdmissionV1, ...]
    owner_assignment: tuple[tuple[str, str, str], ...]
    oracle: IndependentFormalAssignmentOracleV1
    formal_owner_independent_oracle_parity: bool
    input_order_case_count: int
    input_order_independence_verified: bool
    existing_groups_before: tuple[Mapping[str, object], ...]
    existing_groups_after: tuple[Mapping[str, object], ...]
    cross_split_leakage_violations: tuple[Mapping[str, object], ...]
    event_rows: tuple[Mapping[str, str], ...]
    randomization_used: bool
    random_seed_used: bool
    manual_split_override: bool


class _AdmissionInvariantError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _fail(reason: str) -> NoReturn:
    raise _AdmissionInvariantError(reason)


def _public_error(error: Exception) -> NoReturn:
    if isinstance(error, _AdmissionInvariantError):
        raise ValueError(
            f"{BATCH001_FORMAL_SPLIT_LEAKAGE_ADMISSION_ERROR_V1}:{error.reason}"
        ) from error
    if type(error) is ValueError and str(error).startswith(
        BATCH001_FORMAL_SPLIT_LEAKAGE_ADMISSION_ERROR_V1
    ):
        raise error
    raise ValueError(
        f"{BATCH001_FORMAL_SPLIT_LEAKAGE_ADMISSION_ERROR_V1}:"
        f"REUSED_OWNER_REJECTED:{str(error)}"
    ) from error


def _require_repository_root(value: object) -> Path:
    path = _DEFAULT_REPOSITORY_ROOT if value is None else value
    if type(path) is not _PATH_TYPE or not path.is_absolute():
        _fail("REPOSITORY_ROOT_INVALID")
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise _AdmissionInvariantError("REPOSITORY_ROOT_INVALID") from error
    if resolved != path or not path.is_dir() or path.is_symlink():
        _fail("REPOSITORY_ROOT_INVALID")
    return path


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _owner_canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _csv_bytes(header: Sequence[str], rows: Sequence[Mapping[str, object]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=tuple(header), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: row.get(field, "") for field in header})
    return buffer.getvalue().encode("utf-8")


def _verify_file_sha_v1(path: Path, expected_sha256: str, reason: str) -> bytes:
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise _AdmissionInvariantError(reason + "_UNREADABLE") from error
    if _sha256(payload) != expected_sha256:
        _fail(reason + "_SHA256_MISMATCH")
    return payload


def _binding_row(
    *, category: str, root_kind: str, relative_path: str,
    expected_sha256: str, payload: bytes, consumed_for: str,
) -> dict[str, object]:
    actual = _sha256(payload)
    if actual != expected_sha256:
        _fail("SOURCE_BINDING_SHA256_MISMATCH:" + relative_path)
    return {
        "source_category": category,
        "source_root_kind": root_kind,
        "relative_path": relative_path,
        "expected_sha256": expected_sha256,
        "actual_sha256": actual,
        "byte_count": len(payload),
        "consumed_for": consumed_for,
        "sha256_verified": True,
    }


def _source_binding_rows_v1(
    repo: Path, inputs: Mapping[str, Any], leakage_registry: Any,
) -> tuple[Mapping[str, object], ...]:
    rows: dict[tuple[str, str], dict[str, object]] = {}

    def add(
        category: str, root_kind: str, relative: str,
        expected: str, consumed_for: str,
    ) -> None:
        base = repo if root_kind == "REPOSITORY_ROOT" else repo.parent
        payload = _verify_file_sha_v1(
            base / relative, expected, "SOURCE_BINDING:" + relative,
        )
        key = (root_kind, relative)
        row = _binding_row(
            category=category, root_kind=root_kind, relative_path=relative,
            expected_sha256=expected, payload=payload, consumed_for=consumed_for,
        )
        prior = rows.get(key)
        if prior is not None and prior["expected_sha256"] != expected:
            _fail("SOURCE_BINDING_DUPLICATE_PATH_CONFLICT:" + relative)
        if prior is None:
            rows[key] = row

    for category, relative, expected, consumed_for in _FIXED_REPOSITORY_BINDINGS_V1:
        add(category, "REPOSITORY_ROOT", relative, expected, consumed_for)
    add(
        "PUBLISHED_ATTEMPT001_OUTCOMES",
        "REPOSITORY_PARENT",
        _ATTEMPT_RELATIVE_TO_REPOSITORY_PARENT_V1.as_posix(),
        _ATTEMPT_SHA256_V1,
        "250-event incremental lane and published target predictions",
    )
    for item in inputs["bindings"]["published_rehearsal"]:
        add(
            "PUBLISHED_500_EVENT_REHEARSAL", "REPOSITORY_ROOT",
            str(item["path"]), str(item["sha256"]),
            "exact cumulative 500-event cohort and acquisition planning context",
        )
    for name, category, consumed in (
        ("canonical_event_manifest", "PUBLISHED_CANONICAL_EVENT_POPULATION", "canonical event identity population"),
        ("historical_processing_outcomes", "PUBLISHED_HISTORICAL_OUTCOMES", "250 frozen historical plus 27 control outcomes"),
    ):
        item = inputs["bindings"][name]
        add(category, "REPOSITORY_ROOT", str(item["path"]), str(item["sha256"]), consumed)
    registry_directory = repo / bulk_owner.LEAKAGE_REGISTRY_RELATIVE.parent
    for artifact in leakage_registry.source_artifacts:
        if artifact.path_scope == "REPOSITORY_ROOT_RELATIVE":
            root_kind = "REPOSITORY_ROOT"
            relative = artifact.path
        elif artifact.path_scope == "REGISTRY_DIRECTORY_RELATIVE":
            root_kind = "REPOSITORY_ROOT"
            relative = (bulk_owner.LEAKAGE_REGISTRY_RELATIVE.parent / artifact.path).as_posix()
            if not (registry_directory / artifact.path).is_file():
                _fail("CUMULATIVE_PROVENANCE_SOURCE_UNREADABLE:" + artifact.path)
        else:
            _fail("CUMULATIVE_PROVENANCE_PATH_SCOPE_INVALID")
        add(
            "CUMULATIVE_REGISTRY_PROVENANCE", root_kind, relative,
            artifact.sha256, "validated frozen cumulative group provenance",
        )
    return tuple(rows[key] for key in sorted(rows))


def _load_bridge_rows_v1(repo: Path) -> list[dict[str, str]]:
    with (repo / _BRIDGE_READINESS).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if (
        len(rows) != 13
        or len({row.get("canonical_event_id") for row in rows}) != 13
        or any(row.get("model_integration_preview_ready") != "true" for row in rows)
        or any(row.get("split_admission_authoritative") != "false" for row in rows)
        or any(row.get("sample_training_admitted") != "false" for row in rows)
    ):
        _fail("PUBLISHED_BATCH001_BRIDGE_POPULATION_INVALID")
    expected_targets = {
        event_id
        for item in _EXPECTED_COMPONENTS_V1.values()
        for event_id in item["target_event_ids"]
    } | set(_EXPECTED_NDU_EVENT_IDS_V1)
    if {row["canonical_event_id"] for row in rows} != expected_targets:
        _fail("PUBLISHED_BATCH001_TARGET_EVENT_SET_INVALID")
    return rows


def _snapshot_existing_groups_v1(
    groups: Sequence[Any],
) -> tuple[Mapping[str, object], ...]:
    return tuple({
        "leakage_key": group.leakage_key,
        "final_leakage_group_id": group.final_leakage_group_id,
        "member_count": group.member_count,
        "assigned_split": group.assigned_split,
        "frozen": group.frozen,
        "member_identities": tuple(group.member_identities),
    } for group in groups)


def _reproduce_read_only_context_v1(repo: Path) -> tuple[
    list[dict[str, Any]], list[dict[str, str]], Mapping[str, Any], Any,
    tuple[Mapping[str, object], ...], Mapping[str, int], tuple[Mapping[str, object], ...],
]:
    inputs = executor_owner.load_published_executor_inputs_v1(repo)
    context = executor_owner.build_processing_context_v1(repo)
    attempt_path = repo.parent / _ATTEMPT_RELATIVE_TO_REPOSITORY_PARENT_V1
    attempt_payload = _verify_file_sha_v1(
        attempt_path, _ATTEMPT_SHA256_V1, "ATTEMPT001_INCREMENTAL_OUTCOMES",
    )
    try:
        attempt = json.loads(attempt_payload)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise _AdmissionInvariantError("ATTEMPT001_SCHEMA_INVALID") from error
    attempt_events = attempt.get("events") if type(attempt) is dict else None
    if (
        type(attempt_events) is not list
        or len(attempt_events) != 250
        or attempt.get("frozen_historical_outcomes_in_leakage_context") != 250
        or attempt.get("frozen_control_outcomes_in_leakage_context") != 27
        or attempt.get("leakage_batch_population_count") != 527
    ):
        _fail("ATTEMPT001_CONTEXT_COUNTS_INVALID")
    combined = copy.deepcopy([
        *inputs["historical_outcomes"],
        *inputs["control_outcomes"],
        *attempt_events,
    ])
    existing_groups = tuple(context.leakage_context["existing_groups"])
    references = tuple(context.leakage_context["references"])
    historical_groups = sum(
        not group.leakage_key.startswith("COVAPIE_REAL_EXACT4_LEAKAGE_V1:")
        for group in existing_groups
    )
    cumulative_groups = len(existing_groups) - historical_groups
    counts = {
        "historical_frozen_outcome_count": len(inputs["historical_outcomes"]),
        "known_control_outcome_count": len(inputs["control_outcomes"]),
        "incremental_attempt_outcome_count": len(attempt_events),
        "full_predictor_population_count": len(combined),
        "frozen_reference_record_count": len(references),
        "frozen_leakage_group_count": len(existing_groups),
        "frozen_historical_group_count": historical_groups,
        "frozen_cumulative_group_count": cumulative_groups,
    }
    if counts != {
        "historical_frozen_outcome_count": 250,
        "known_control_outcome_count": 27,
        "incremental_attempt_outcome_count": 250,
        "full_predictor_population_count": 527,
        "frozen_reference_record_count": 14,
        "frozen_leakage_group_count": 7,
        "frozen_historical_group_count": 5,
        "frozen_cumulative_group_count": 2,
    }:
        _fail("FULL_PREDICTOR_CONTEXT_COUNTS_INVALID")
    original_attempt_by_id = {
        str(item["canonical_event_id"]): item for item in attempt_events
    }
    bulk_owner.apply_leakage_predictions_read_only_v1(
        combined,
        historical=context.historical_identities,
        context=context.leakage_context,
    )
    bridge_rows = _load_bridge_rows_v1(repo)
    target_ids = {row["canonical_event_id"] for row in bridge_rows}
    reproduced_by_id = {
        str(item["canonical_event_id"]): item
        for item in combined if item["canonical_event_id"] in target_ids
    }
    parity_fields = (
        "leakage_classification", "leakage_key", "predicted_group_id",
        "predicted_split", "leakage_linking_axes",
    )
    if set(reproduced_by_id) != target_ids or not target_ids <= set(original_attempt_by_id):
        _fail("TARGET13_NOT_PRESENT_IN_FULL_ATTEMPT_CONTEXT")
    for event_id in sorted(target_ids):
        before = original_attempt_by_id[event_id]
        after = reproduced_by_id[event_id]
        if any(before.get(field) != after.get(field) for field in parity_fields):
            _fail("TARGET_READ_ONLY_REPRODUCTION_MISMATCH:" + event_id)
        before_complete = bool(
            before.get("structural_processing", {}).get("leakage_evidence", {}).get("complete")
        )
        after_complete = bool(
            after.get("structural_processing", {}).get("leakage_evidence", {}).get("complete")
        )
        if before_complete != after_complete:
            _fail("TARGET_READ_ONLY_EVIDENCE_COMPLETENESS_MISMATCH:" + event_id)
    source_rows = _source_binding_rows_v1(repo, inputs, context.leakage_registry)
    return (
        combined, bridge_rows, context.leakage_context, context.leakage_registry,
        _snapshot_existing_groups_v1(existing_groups), counts, source_rows,
    )


def _independent_complete_components_v1(
    outcomes: Sequence[Mapping[str, Any]],
) -> Mapping[str, tuple[Mapping[str, Any], ...]]:
    candidates = [
        item for item in outcomes
        if item.get("structural_processing", {}).get("leakage_evidence")
    ]
    parent = {
        str(item["canonical_event_id"]): str(item["canonical_event_id"])
        for item in candidates
    }

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(left: str, right: str) -> None:
        lroot, rroot = find(left), find(right)
        if lroot != rroot:
            parent[max(lroot, rroot)] = min(lroot, rroot)

    for index, left in enumerate(candidates):
        left_evidence = left["structural_processing"]["leakage_evidence"]
        if left_evidence.get("complete") is not True:
            continue
        for right in candidates[index + 1:]:
            right_evidence = right["structural_processing"]["leakage_evidence"]
            if (
                right_evidence.get("complete") is True
                and bulk_owner._leakage_linking_axes_v1(left_evidence, right_evidence)
            ):
                union(str(left["canonical_event_id"]), str(right["canonical_event_id"]))
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for item in candidates:
        grouped.setdefault(find(str(item["canonical_event_id"])), []).append(item)
    return {
        root: tuple(sorted(members, key=lambda item: str(item["canonical_event_id"])))
        for root, members in sorted(grouped.items())
    }


def _recover_target_components_v1(
    outcomes: Sequence[Mapping[str, Any]], bridge_rows: Sequence[Mapping[str, str]],
) -> tuple[FormalComponentAdmissionV1, ...]:
    by_event_id = {str(item["canonical_event_id"]): item for item in outcomes}
    independent = _independent_complete_components_v1(outcomes)
    root_by_event = {
        str(item["canonical_event_id"]): root
        for root, members in independent.items() for item in members
    }
    target_ids = {row["canonical_event_id"] for row in bridge_rows}
    result: list[FormalComponentAdmissionV1] = []
    for component_name in ("DJK", "LN5", "PX5", "PTG"):
        expected = _EXPECTED_COMPONENTS_V1[component_name]
        seed = expected["target_event_ids"][0]
        root = root_by_event.get(seed)
        if root is None:
            _fail("TARGET_COMPONENT_SEED_NOT_IN_COMPLETE_COMPONENT:" + component_name)
        members = independent[root]
        event_ids = tuple(str(item["canonical_event_id"]) for item in members)
        identities = tuple(sorted({
            str(item["pdb_id"]) + "/" + str(item["ligand_component_id"])
            for item in members
        }))
        member_keys = {item.get("leakage_key") for item in members}
        classifications = {item.get("leakage_classification") for item in members}
        groups = {item.get("predicted_group_id") for item in members}
        splits = {item.get("predicted_split") for item in members}
        if (
            event_ids != expected["event_ids"]
            or identities != expected["identities"]
            or member_keys != {expected["leakage_key"]}
            or classifications != {"NEW_EXPANSION_COMPONENT"}
            or groups != {expected["group_id"]}
            or splits != {expected["read_only_split"]}
        ):
            _fail("FULL_TARGET_COMPONENT_MEMBERSHIP_OR_PREDICTION_INVALID:" + component_name)
        policy_axes: set[str] = set()
        source_axes: set[str] = set()
        for index, left in enumerate(members):
            left_evidence = left["structural_processing"]["leakage_evidence"]
            source_axes.update(str(axis) for axis in left_evidence.get("linking_axes", ()))
            for right in members[index + 1:]:
                policy_axes.update(bulk_owner._leakage_linking_axes_v1(
                    left_evidence,
                    right["structural_processing"]["leakage_evidence"],
                ))
        component_targets = tuple(event_id for event_id in event_ids if event_id in target_ids)
        if component_targets != expected["target_event_ids"]:
            _fail("BATCH001_TARGET_COMPONENT_SUBSET_INVALID:" + component_name)
        result.append(FormalComponentAdmissionV1(
            component_name=component_name,
            leakage_key=expected["leakage_key"],
            classification="NEW_EXPANSION_COMPONENT",
            linking_axes=tuple(sorted(policy_axes)),
            source_evidence_linking_axis_values=tuple(sorted(source_axes)),
            full_member_pdb_ligand_identities=identities,
            full_member_canonical_event_ids=event_ids,
            batch001_target_event_ids=component_targets,
            non_target_component_event_ids=tuple(
                event_id for event_id in event_ids if event_id not in target_ids
            ),
            read_only_group_id=expected["group_id"],
            read_only_split=expected["read_only_split"],
            formal_group_id="",
            formal_split="",
            group_parity=False,
            split_parity=False,
            formal_assignment_status="NOT_YET_FORMALLY_ASSIGNED",
            formal_assignment_is_authority_candidate=False,
        ))
    for event_id in _EXPECTED_NDU_EVENT_IDS_V1:
        event = by_event_id[event_id]
        evidence = event["structural_processing"]["leakage_evidence"]
        if (
            evidence.get("complete") is not False
            or event.get("leakage_classification") != "LEAKAGE_EVIDENCE_INCOMPLETE"
            or event.get("leakage_key") is not None
            or event.get("predicted_group_id") is not None
            or event.get("predicted_split") != "UNASSIGNED_READ_ONLY"
        ):
            _fail("NDU_FAIL_CLOSED_READ_ONLY_STATE_INVALID:" + event_id)
    return tuple(result)


def _formal_proxies_v1(
    components: Sequence[FormalComponentAdmissionV1],
) -> tuple[SimpleNamespace, ...]:
    return tuple(
        SimpleNamespace(candidate_identity=identity, leakage_key=component.leakage_key)
        for component in components
        for identity in component.full_member_pdb_ligand_identities
    )


def _fraction_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def independent_exhaustive_formal_assignment_oracle_v1(
    proxies: Sequence[Any], *, existing_groups: Sequence[Any],
) -> IndependentFormalAssignmentOracleV1:
    """Independently enumerate the documented 3^N successor objective."""

    existing_by_key: dict[str, Any] = {}
    prior_member_to_key: dict[str, str] = {}
    for group in existing_groups:
        if (
            group.leakage_key in existing_by_key
            or group.frozen is not True
            or group.assigned_split not in split_owner.split_owner.SPLITS
            or group.member_count <= 0
            or tuple(sorted(group.member_identities)) != tuple(group.member_identities)
            or group.member_count != len(group.member_identities)
        ):
            _fail("ORACLE_EXISTING_GROUP_POPULATION_INVALID")
        existing_by_key[group.leakage_key] = group
        for identity in group.member_identities:
            if identity in prior_member_to_key:
                _fail("ORACLE_EXISTING_MEMBER_DUPLICATED")
            prior_member_to_key[identity] = group.leakage_key
    members_by_key: dict[str, set[str]] = {}
    identity_to_key: dict[str, str] = {}
    for proxy in proxies:
        identity = str(proxy.candidate_identity)
        key = str(proxy.leakage_key)
        if not identity or not key:
            _fail("ORACLE_PROXY_INVALID")
        if identity in identity_to_key and identity_to_key[identity] != key:
            _fail("ORACLE_PROXY_IDENTITY_KEY_CONFLICT")
        if identity in prior_member_to_key and prior_member_to_key[identity] != key:
            _fail("ORACLE_REGISTERED_IDENTITY_KEY_CONFLICT")
        identity_to_key[identity] = key
        members_by_key.setdefault(key, set()).add(identity)
    groups: list[dict[str, Any]] = []
    for group in existing_groups:
        extra = members_by_key.get(group.leakage_key, set()) - set(group.member_identities)
        groups.append({
            "key": group.leakage_key,
            "id": group.final_leakage_group_id,
            "member_count": group.member_count + len(extra),
            "fixed_rank": split_owner.split_owner.RANK[group.assigned_split],
        })
    new_keys = sorted(set(members_by_key) - set(existing_by_key))
    for key in new_keys:
        group_id = "COVAPIE_EXPANSION_LEAKAGE_GROUP_" + _sha256(
            _owner_canonical_json_bytes({
                "policy": "conservative_union_final_leakage_group_v1",
                "leakage_key": key,
            })
        )[:16].upper()
        groups.append({
            "key": key,
            "id": group_id,
            "member_count": len(members_by_key[key]),
            "fixed_rank": None,
        })
    groups.sort(key=lambda item: item["id"])
    new_keys = sorted(new_keys, key=lambda key: next(
        item["id"] for item in groups if item["key"] == key
    ))
    if len(new_keys) != 4:
        _fail("ORACLE_REQUIRES_EXACTLY_FOUR_NEW_COMPONENTS")
    target = split_owner.split_owner.TARGET
    splits = split_owner.split_owner.SPLITS
    total_samples = sum(int(item["member_count"]) for item in groups)
    group_count = len(groups)
    valid: list[tuple[tuple[Any, ...], tuple[int, int, int], tuple[int, int, int]]] = []
    for ranks in product(range(3), repeat=len(new_keys)):
        new_rank = dict(zip(new_keys, ranks))
        signature = tuple(
            item["fixed_rank"] if item["fixed_rank"] is not None
            else new_rank[item["key"]]
            for item in groups
        )
        sample_counts = tuple(sum(
            int(item["member_count"])
            for item, rank in zip(groups, signature)
            if rank == split_rank
        ) for split_rank in range(3))
        group_counts = tuple(signature.count(rank) for rank in range(3))
        if (
            min(group_counts) < 1
            or sample_counts[0] < sample_counts[1]
            or sample_counts[0] < sample_counts[2]
        ):
            continue
        pre_signature = (
            sum(abs(
                Fraction(sample_counts[index]) - target[splits[index]] * total_samples
            ) for index in range(3)),
            max(abs(
                Fraction(sample_counts[index]) - target[splits[index]] * total_samples
            ) for index in range(3)),
            sum(abs(
                Fraction(group_counts[index]) - target[splits[index]] * group_count
            ) for index in range(3)),
        )
        valid.append((pre_signature + (signature,), sample_counts, group_counts))
    if not valid:
        _fail("ORACLE_NO_VALID_FROZEN_ASSIGNMENT")
    selected = min(valid, key=lambda item: item[0])
    objective = selected[0]
    selected_signature = objective[3]
    best_pre_signature = objective[:3]
    tie_count = sum(item[0][:3] == best_pre_signature for item in valid)
    assignment = tuple(sorted(
        (
            item["key"], item["id"],
            splits[selected_signature[index]],
        )
        for index, item in enumerate(groups)
    ))
    tied_signatures = [
        item[0][3] for item in valid if item[0][:3] == best_pre_signature
    ]
    return IndependentFormalAssignmentOracleV1(
        candidate_assignment_count=3 ** len(new_keys),
        valid_assignment_count=len(valid),
        group_order=tuple((
            str(item["key"]), str(item["id"]), int(item["member_count"]),
            item["fixed_rank"],
        ) for item in groups),
        new_key_order=tuple(new_keys),
        selected_full_signature=tuple(selected_signature),
        selected_sample_counts=selected[1],
        selected_group_counts=selected[2],
        selected_objective_fractions=tuple(
            _fraction_text(value) for value in best_pre_signature
        ),
        best_pre_signature_objective=tuple(
            _fraction_text(value) for value in best_pre_signature
        ),
        tie_count_before_signature=tie_count,
        selected_assignment=assignment,
        lexicographic_minimum_tie_break_applied=(
            tuple(selected_signature) == min(tied_signatures)
        ),
    )


def _normalized_assignment(
    value: Mapping[str, tuple[str, str]],
) -> tuple[tuple[str, str, str], ...]:
    return tuple(sorted((key, group_id, split) for key, (group_id, split) in value.items()))


def _formal_assignment_order_cases_v1(
    components: Sequence[FormalComponentAdmissionV1],
) -> tuple[tuple[str, tuple[SimpleNamespace, ...]], ...]:
    by_key = {component.leakage_key: component for component in components}
    by_group = {component.read_only_group_id: component for component in components}

    def proxies_for(ordered: Sequence[FormalComponentAdmissionV1], reverse_members: bool = False) -> tuple[SimpleNamespace, ...]:
        result: list[SimpleNamespace] = []
        for component in ordered:
            identities = component.full_member_pdb_ligand_identities
            if reverse_members:
                identities = tuple(reversed(identities))
            result.extend(
                SimpleNamespace(candidate_identity=identity, leakage_key=component.leakage_key)
                for identity in identities
            )
        return tuple(result)

    original = tuple(components)
    return (
        ("ORIGINAL_COMPONENT_ORDER", proxies_for(original)),
        ("REVERSE_ALL_PROXIES", tuple(reversed(proxies_for(original)))),
        ("SORTED_BY_LEAKAGE_KEY", proxies_for(tuple(by_key[key] for key in sorted(by_key)))),
        ("SORTED_BY_GROUP_ID", proxies_for(tuple(by_group[key] for key in sorted(by_group)))),
        ("ROTATE_COMPONENTS_LEFT", proxies_for((*original[1:], original[0]))),
        ("REVERSE_COMPONENTS_AND_MEMBERS", proxies_for(tuple(reversed(original)), True)),
    )


def _cross_component_leakage_violations_v1(
    outcomes: Sequence[Mapping[str, Any]],
    components: Sequence[FormalComponentAdmissionV1],
    references: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, object], ...]:
    by_event = {str(item["canonical_event_id"]): item for item in outcomes}
    violations: list[Mapping[str, object]] = []
    for left_index, left_component in enumerate(components):
        for right_component in components[left_index + 1:]:
            for left_id in left_component.full_member_canonical_event_ids:
                left_evidence = by_event[left_id]["structural_processing"]["leakage_evidence"]
                for right_id in right_component.full_member_canonical_event_ids:
                    axes = bulk_owner._leakage_linking_axes_v1(
                        left_evidence,
                        by_event[right_id]["structural_processing"]["leakage_evidence"],
                    )
                    if axes:
                        violations.append({
                            "left": left_id, "right": right_id,
                            "left_group": left_component.formal_group_id,
                            "right_group": right_component.formal_group_id,
                            "left_split": left_component.formal_split,
                            "right_split": right_component.formal_split,
                            "linking_axes": axes,
                        })
        for event_id in left_component.full_member_canonical_event_ids:
            evidence = by_event[event_id]["structural_processing"]["leakage_evidence"]
            for reference in references:
                axes = bulk_owner._leakage_linking_axes_v1(evidence, reference)
                if axes and reference["group_id"] != left_component.formal_group_id:
                    violations.append({
                        "left": event_id,
                        "right": reference["identity"],
                        "left_group": left_component.formal_group_id,
                        "right_group": reference["group_id"],
                        "left_split": left_component.formal_split,
                        "right_split": reference["split"],
                        "linking_axes": axes,
                    })
    return tuple(sorted(violations, key=lambda item: (
        str(item["left"]), str(item["right"]), str(item["left_group"]),
    )))


def _event_admission_rows_v1(
    bridge_rows: Sequence[Mapping[str, str]], outcomes: Sequence[Mapping[str, Any]],
    components: Sequence[FormalComponentAdmissionV1],
) -> tuple[Mapping[str, str], ...]:
    outcome_by_id = {str(item["canonical_event_id"]): item for item in outcomes}
    component_by_event = {
        event_id: component
        for component in components for event_id in component.batch001_target_event_ids
    }
    result: list[Mapping[str, str]] = []
    for bridge_row in bridge_rows:
        event_id = bridge_row["canonical_event_id"]
        outcome = outcome_by_id[event_id]
        component = component_by_event.get(event_id)
        evidence = outcome["structural_processing"]["leakage_evidence"]
        if component is None:
            if event_id not in _EXPECTED_NDU_EVENT_IDS_V1:
                _fail("TARGET_EVENT_HAS_NO_FORMAL_COMPONENT_OR_NDU_BOUNDARY")
            result.append({
                "canonical_event_id": event_id,
                "review_unit_id": bridge_row["review_unit_id"],
                "ligand_component_id": bridge_row["ligand_component_id"],
                "model_integration_preview_ready": "true",
                "leakage_evidence_complete": "false",
                "leakage_classification": "LEAKAGE_EVIDENCE_INCOMPLETE",
                "leakage_key": "",
                "read_only_group_id": "",
                "read_only_split": "UNASSIGNED_READ_ONLY",
                "formal_leakage_group_id": "",
                "assigned_split": "",
                "group_parity": "not_applicable",
                "split_parity": "not_applicable",
                "read_only_prediction_is_authority": "false",
                "formal_joint_assignment_is_authority_candidate": "false",
                "split_admission_authoritative": "false",
                "split_admission_status": "UNRESOLVED_FAIL_CLOSED",
                "split_admission_reason": "LEAKAGE_EVIDENCE_INCOMPLETE",
                "sample_training_admitted": "false",
                "model_training_activation_authorized": "false",
            })
            continue
        result.append({
            "canonical_event_id": event_id,
            "review_unit_id": bridge_row["review_unit_id"],
            "ligand_component_id": bridge_row["ligand_component_id"],
            "model_integration_preview_ready": "true",
            "leakage_evidence_complete": "true" if evidence.get("complete") is True else "false",
            "leakage_classification": component.classification,
            "leakage_key": component.leakage_key,
            "read_only_group_id": component.read_only_group_id,
            "read_only_split": component.read_only_split,
            "formal_leakage_group_id": component.formal_group_id,
            "assigned_split": component.formal_split,
            "group_parity": str(component.group_parity).lower(),
            "split_parity": str(component.split_parity).lower(),
            "read_only_prediction_is_authority": "false",
            "formal_joint_assignment_is_authority_candidate": "true",
            "split_admission_authoritative": "true",
            "split_admission_status": "FORMALLY_ADMITTED_TO_FROZEN_SPLIT",
            "split_admission_reason": "FORMAL_JOINT_ASSIGNMENT_RECOMPUTED_WITH_OWNER_ORACLE_PARITY",
            "sample_training_admitted": "false",
            "model_training_activation_authorized": "false",
        })
    return tuple(result)


def _validate_computation_v1(
    computation: Batch001FormalSplitAdmissionComputationV1,
) -> None:
    if type(computation) is not Batch001FormalSplitAdmissionComputationV1:
        _fail("COMPUTATION_TYPE_INVALID")
    expected_counts = {
        "historical_frozen_outcome_count": 250,
        "known_control_outcome_count": 27,
        "incremental_attempt_outcome_count": 250,
        "full_predictor_population_count": 527,
        "frozen_reference_record_count": 14,
        "frozen_leakage_group_count": 7,
        "frozen_historical_group_count": 5,
        "frozen_cumulative_group_count": 2,
    }
    if dict(computation.context_counts) != expected_counts:
        _fail("FULL_CONTEXT_COUNT_INVALID")
    if (
        computation.read_only_prediction_reproduced_exactly is not True
        or computation.read_only_prediction_is_authority is not False
        or computation.read_only_prediction_copied_as_authority is not False
        or computation.formal_assignment_mode != "JOINT_ALL_FOUR_COMPONENTS"
        or computation.formal_joint_assignment_recomputed is not True
        or computation.randomization_used is not False
        or computation.random_seed_used is not False
        or computation.manual_split_override is not False
    ):
        _fail("FORMAL_VS_READ_ONLY_AUTHORITY_SEMANTICS_INVALID")
    if len(computation.components) != 4:
        _fail("FORMAL_COMPONENT_COUNT_INVALID")
    component_by_name = {item.component_name: item for item in computation.components}
    if set(component_by_name) != set(_EXPECTED_COMPONENTS_V1):
        _fail("FORMAL_COMPONENT_NAME_SET_INVALID")
    group_to_split: dict[str, str] = {}
    for name, expected in _EXPECTED_COMPONENTS_V1.items():
        item = component_by_name[name]
        expected_non_target = tuple(
            event_id for event_id in expected["event_ids"]
            if event_id not in set(expected["target_event_ids"])
        )
        expected_status = (
            "READ_ONLY_SPLIT_CONFIRMED_BY_FORMAL_JOINT_ASSIGNMENT"
            if expected["read_only_split"] == expected["formal_split"]
            else "READ_ONLY_SPLIT_SUPERSEDED_BY_FORMAL_JOINT_ASSIGNMENT"
        )
        if (
            item.leakage_key != expected["leakage_key"]
            or item.classification != "NEW_EXPANSION_COMPONENT"
            or not item.linking_axes
            or item.full_member_pdb_ligand_identities != expected["identities"]
            or item.full_member_canonical_event_ids != expected["event_ids"]
            or item.batch001_target_event_ids != expected["target_event_ids"]
            or item.non_target_component_event_ids != expected_non_target
            or item.read_only_group_id != expected["group_id"]
            or item.read_only_split != expected["read_only_split"]
            or item.formal_group_id != expected["group_id"]
            or item.formal_split != expected["formal_split"]
            or item.group_parity is not True
            or item.split_parity is not (
                expected["read_only_split"] == expected["formal_split"]
            )
            or item.formal_assignment_status != expected_status
            or item.formal_assignment_is_authority_candidate is not True
        ):
            _fail("FORMAL_COMPONENT_CONTRACT_INVALID:" + name)
        prior = group_to_split.get(item.formal_group_id)
        if prior is not None and prior != item.formal_split:
            _fail("SAME_FORMAL_GROUP_ASSIGNED_MULTIPLE_SPLITS")
        group_to_split[item.formal_group_id] = item.formal_split
    oracle = computation.oracle
    if (
        oracle.candidate_assignment_count != 81
        or oracle.valid_assignment_count != 46
        or oracle.selected_objective_fractions != ("4", "2", "27/5")
        or oracle.best_pre_signature_objective != ("4", "2", "27/5")
        or oracle.tie_count_before_signature != 3
        or oracle.selected_full_signature != (2, 0, 0, 1, 1, 0, 0, 1, 1, 0, 2)
        or oracle.selected_sample_counts != (23, 4, 3)
        or oracle.selected_group_counts != (5, 4, 2)
        or oracle.lexicographic_minimum_tie_break_applied is not True
    ):
        _fail("INDEPENDENT_EXHAUSTIVE_ORACLE_CONTRACT_INVALID")
    if (
        computation.formal_owner_independent_oracle_parity is not True
        or computation.owner_assignment != oracle.selected_assignment
    ):
        _fail("FORMAL_OWNER_INDEPENDENT_ORACLE_MISMATCH")
    if (
        computation.input_order_case_count < 6
        or computation.input_order_independence_verified is not True
    ):
        _fail("FORMAL_INPUT_ORDER_INDEPENDENCE_INVALID")
    if (
        len(computation.existing_groups_before) != 7
        or computation.existing_groups_before != computation.existing_groups_after
        or any(item.get("frozen") is not True for item in computation.existing_groups_before)
    ):
        _fail("EXISTING_FROZEN_GROUP_MUTATION_DETECTED")
    if computation.cross_split_leakage_violations:
        _fail("CROSS_GROUP_MUST_LINK_EDGE_DETECTED")
    if len(computation.event_rows) != 13 or len({row["canonical_event_id"] for row in computation.event_rows}) != 13:
        _fail("EVENT_ADMISSION_EXACT13_INVALID")
    admitted = [row for row in computation.event_rows if row["split_admission_authoritative"] == "true"]
    unresolved = [row for row in computation.event_rows if row["split_admission_status"] == "UNRESOLVED_FAIL_CLOSED"]
    if (
        len(admitted) != 9
        or sum(row["assigned_split"] == "train" for row in admitted) != 5
        or sum(row["assigned_split"] == "validation" for row in admitted) != 4
        or any(row["assigned_split"] == "test" for row in admitted)
        or len(unresolved) != 4
        or {row["canonical_event_id"] for row in unresolved} != set(_EXPECTED_NDU_EVENT_IDS_V1)
    ):
        _fail("EVENT_ADMISSION_COUNTS_INVALID")
    for row in computation.event_rows:
        if (
            row["model_integration_preview_ready"] != "true"
            or row["sample_training_admitted"] != "false"
            or row["model_training_activation_authorized"] != "false"
            or row["read_only_prediction_is_authority"] != "false"
        ):
            _fail("MODEL_ACTIVATION_OR_READ_ONLY_AUTHORITY_VIOLATION")
        if row["canonical_event_id"] in _EXPECTED_NDU_EVENT_IDS_V1 and (
            row["leakage_evidence_complete"] != "false"
            or row["leakage_key"] != ""
            or row["formal_leakage_group_id"] != ""
            or row["assigned_split"] != ""
            or row["split_admission_authoritative"] != "false"
            or row["split_admission_reason"] != "LEAKAGE_EVIDENCE_INCOMPLETE"
        ):
            _fail("NDU_FORMAL_ADMISSION_FAIL_CLOSED_VIOLATION")
    if not computation.source_bindings or any(
        row.get("sha256_verified") is not True
        or row.get("actual_sha256") != row.get("expected_sha256")
        for row in computation.source_bindings
    ):
        _fail("SOURCE_BINDING_INVENTORY_INVALID")


def validate_covapie_batch001_formal_split_admission_v1(
    computation: object,
) -> bool:
    try:
        _validate_computation_v1(computation)  # type: ignore[arg-type]
        return True
    except Exception as error:
        _public_error(error)


def compute_covapie_batch001_formal_split_admission_v1(
    *, repository_root: object = None,
) -> Batch001FormalSplitAdmissionComputationV1:
    """Recompute all authority evidence in memory and fail closed."""

    try:
        repo = _require_repository_root(repository_root)
        (
            outcomes, bridge_rows, leakage_context, _leakage_registry,
            frozen_snapshot, context_counts, source_bindings,
        ) = _reproduce_read_only_context_v1(repo)
        components = _recover_target_components_v1(outcomes, bridge_rows)
        existing_groups = tuple(leakage_context["existing_groups"])
        proxies = _formal_proxies_v1(components)
        owner_map = split_owner.assign_expansion_leakage_splits_v1(
            proxies, existing_groups=existing_groups,
        )
        owner_assignment = _normalized_assignment(owner_map)
        oracle = independent_exhaustive_formal_assignment_oracle_v1(
            proxies, existing_groups=existing_groups,
        )
        if owner_assignment != oracle.selected_assignment:
            _fail("FORMAL_OWNER_INDEPENDENT_ORACLE_MISMATCH")
        formalized: list[FormalComponentAdmissionV1] = []
        for component in components:
            group_id, formal_split = owner_map[component.leakage_key]
            expected = _EXPECTED_COMPONENTS_V1[component.component_name]
            if group_id != expected["group_id"] or formal_split != expected["formal_split"]:
                _fail("FRESH_FORMAL_JOINT_RESULT_UNEXPECTED:" + component.component_name)
            group_parity = group_id == component.read_only_group_id
            if not group_parity:
                _fail("FORMAL_READ_ONLY_GROUP_PARITY_FAILED:" + component.component_name)
            split_parity = formal_split == component.read_only_split
            formalized.append(replace(
                component,
                formal_group_id=group_id,
                formal_split=formal_split,
                group_parity=group_parity,
                split_parity=split_parity,
                formal_assignment_status=(
                    "READ_ONLY_SPLIT_CONFIRMED_BY_FORMAL_JOINT_ASSIGNMENT"
                    if split_parity
                    else "READ_ONLY_SPLIT_SUPERSEDED_BY_FORMAL_JOINT_ASSIGNMENT"
                ),
                formal_assignment_is_authority_candidate=True,
            ))
        finalized_components = tuple(formalized)
        order_cases = _formal_assignment_order_cases_v1(finalized_components)
        for _name, case_proxies in order_cases:
            case_owner = _normalized_assignment(
                split_owner.assign_expansion_leakage_splits_v1(
                    case_proxies, existing_groups=existing_groups,
                )
            )
            case_oracle = independent_exhaustive_formal_assignment_oracle_v1(
                case_proxies, existing_groups=existing_groups,
            )
            if case_owner != owner_assignment or case_oracle != oracle:
                _fail("FORMAL_ASSIGNMENT_INPUT_ORDER_DEPENDENCE_DETECTED")
        violations = _cross_component_leakage_violations_v1(
            outcomes, finalized_components, tuple(leakage_context["references"]),
        )
        event_rows = _event_admission_rows_v1(
            bridge_rows, outcomes, finalized_components,
        )
        computation = Batch001FormalSplitAdmissionComputationV1(
            source_bindings=source_bindings,
            context_counts=context_counts,
            read_only_prediction_reproduced_exactly=True,
            read_only_prediction_is_authority=False,
            read_only_prediction_copied_as_authority=False,
            formal_assignment_mode="JOINT_ALL_FOUR_COMPONENTS",
            formal_joint_assignment_recomputed=True,
            components=finalized_components,
            owner_assignment=owner_assignment,
            oracle=oracle,
            formal_owner_independent_oracle_parity=True,
            input_order_case_count=len(order_cases),
            input_order_independence_verified=True,
            existing_groups_before=frozen_snapshot,
            existing_groups_after=_snapshot_existing_groups_v1(existing_groups),
            cross_split_leakage_violations=violations,
            event_rows=event_rows,
            randomization_used=False,
            random_seed_used=False,
            manual_split_override=False,
        )
        _validate_computation_v1(computation)
        return computation
    except Exception as error:
        _public_error(error)


_SOURCE_HEADER_V1 = (
    "source_category", "source_root_kind", "relative_path",
    "expected_sha256", "actual_sha256", "byte_count", "consumed_for",
    "sha256_verified",
)
_EVENT_HEADER_V1 = (
    "canonical_event_id", "review_unit_id", "ligand_component_id",
    "model_integration_preview_ready", "leakage_evidence_complete",
    "leakage_classification", "leakage_key", "read_only_group_id",
    "read_only_split", "formal_leakage_group_id", "assigned_split",
    "group_parity", "split_parity", "read_only_prediction_is_authority",
    "formal_joint_assignment_is_authority_candidate",
    "split_admission_authoritative", "split_admission_status",
    "split_admission_reason", "sample_training_admitted",
    "model_training_activation_authorized",
)


def _component_artifact_v1(
    computation: Batch001FormalSplitAdmissionComputationV1,
) -> dict[str, object]:
    return {
        "schema_version": "covapie_batch001_formal_leakage_component_registry_v1",
        "artifact_role": "ADDITIVE_FULL_COMPONENT_LEAKAGE_MEMBERSHIP_AND_FORMAL_SPLIT_RESERVATION",
        "component_count": 4,
        "components": [{
            **asdict(component),
            "full_event_count": len(component.full_member_canonical_event_ids),
            "full_identity_count": len(component.full_member_pdb_ligand_identities),
            "batch001_target_event_count": len(component.batch001_target_event_ids),
            "non_target_component_event_count": len(component.non_target_component_event_ids),
            "non_target_members_are_training_samples": False,
            "non_target_members_inherit_split_reservation_only": True,
        } for component in computation.components],
    }


def _oracle_artifact_v1(oracle: IndependentFormalAssignmentOracleV1) -> dict[str, object]:
    value = asdict(oracle)
    value["selected_objective_tuple"] = [
        *oracle.selected_objective_fractions,
        list(oracle.selected_full_signature),
    ]
    return value


def build_covapie_batch001_formal_split_admission_artifacts_v1(
    *, repository_root: object = None,
) -> dict[str, bytes]:
    """Build the exact four deterministic successor authority artifacts."""

    try:
        computation = compute_covapie_batch001_formal_split_admission_v1(
            repository_root=repository_root,
        )
        source_payload = _csv_bytes(_SOURCE_HEADER_V1, computation.source_bindings)
        component_payload = _canonical_json_bytes(_component_artifact_v1(computation))
        event_payload = _csv_bytes(_EVENT_HEADER_V1, computation.event_rows)
        manifest = {
            "schema_version": "covapie_batch001_formal_split_leakage_admission_manifest_v1",
            "stage": "complete_covapie_batch001_formal_split_leakage_admission_successor_v2",
            "artifact_role": "FORMAL_SPLIT_AUTHORITY_CANDIDATE_NOT_MODEL_TRAINING_ACTIVATION",
            "artifact_bindings": {
                SOURCE_BINDING_INVENTORY_V1: {"sha256": _sha256(source_payload)},
                COMPONENT_REGISTRY_V1: {"sha256": _sha256(component_payload)},
                EVENT_ADMISSION_V1: {"sha256": _sha256(event_payload)},
            },
            "context_counts": dict(computation.context_counts),
            "prediction_and_formal_assignment": {
                "read_only_prediction_reproduced_exactly": True,
                "read_only_prediction_is_authority": False,
                "read_only_prediction_copied_as_authority": False,
                "formal_joint_assignment_recomputed": True,
                "formal_joint_assignment_is_split_authority_candidate": True,
                "formal_assignment_mode": computation.formal_assignment_mode,
                "formal_read_only_group_parity": True,
                "formal_read_only_split_parity": False,
                "read_only_split_superseded_event_count": 7,
                "read_only_split_difference_is_prediction_error": False,
            },
            "read_only_vs_formal_components": [{
                "component_name": item.component_name,
                "leakage_key": item.leakage_key,
                "read_only_group_id": item.read_only_group_id,
                "formal_group_id": item.formal_group_id,
                "read_only_split": item.read_only_split,
                "formal_split": item.formal_split,
                "group_parity": item.group_parity,
                "split_parity": item.split_parity,
                "formal_assignment_status": item.formal_assignment_status,
            } for item in computation.components],
            "independent_exhaustive_formal_assignment_oracle": _oracle_artifact_v1(
                computation.oracle
            ),
            "formal_owner_independent_oracle_parity": True,
            "input_order_independence": {
                "case_count": computation.input_order_case_count,
                "verified": computation.input_order_independence_verified,
            },
            "population_counts": {
                "batch001_positive_event_count": 13,
                "formal_split_admission_event_count": 9,
                "formal_train_event_count": 5,
                "formal_validation_event_count": 4,
                "formal_test_event_count": 0,
                "formal_unresolved_event_count": 4,
                "DJK_formal_train_event_count": 2,
                "PTG_formal_train_event_count": 3,
                "LN5_formal_validation_event_count": 2,
                "PX5_formal_validation_event_count": 2,
                "NDU_unresolved_event_count": 4,
                "model_integration_preview_ready_event_count": 13,
                "model_training_activation_authorized_event_count": 0,
            },
            "frozen_group_invariants": {
                "existing_frozen_group_count": 7,
                "existing_frozen_groups_modified": False,
                "existing_frozen_group_split_change_count": 0,
                "existing_frozen_group_member_change_count": 0,
                "old_cumulative_registry_modified": False,
            },
            "cross_component_leakage_audit": {
                "current_linking_policy_recomputed": True,
                "cross_split_leakage_violation_count": len(
                    computation.cross_split_leakage_violations
                ),
            },
            "assignment_controls": {
                "randomization_used": False,
                "random_seed_used": False,
                "manual_split_override": False,
                "formal_assignment_recomputed": True,
            },
            "safety": {
                "network_used": False,
                "cache_modified": False,
                "checkpoint_read": False,
                "GPU_used": False,
                "tensorization_performed": False,
                "model_forward_performed": False,
                "loss_performed": False,
                "backward_performed": False,
                "optimizer_step_performed": False,
                "Trainer_used": False,
                "training_performed": False,
                "repository_existing_files_modified": False,
                "external_manual_review_workspace_modified": False,
            },
            "ready_for_gpt_review": True,
            "ready_for_admission_aware_cpu_model_smoke": True,
            "ready_for_training": False,
            "full_training_authorized": False,
            "recommended_next_step_exactly": "gpt_audit_batch001_formal_split_admission_then_publish_and_build_admission_aware_train5_cpu_forward_loss_smoke_v1",
        }
        manifest_payload = _canonical_json_bytes(manifest)
        return {
            SOURCE_BINDING_INVENTORY_V1: source_payload,
            COMPONENT_REGISTRY_V1: component_payload,
            EVENT_ADMISSION_V1: event_payload,
            MANIFEST_V1: manifest_payload,
        }
    except Exception as error:
        _public_error(error)


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def materialize_covapie_batch001_formal_split_admission_artifacts_v1(
    *, repository_root: object = None,
) -> dict[str, bytes]:
    """Write exactly the four authorized additive metadata artifacts."""

    try:
        repo = _require_repository_root(repository_root)
        artifacts = build_covapie_batch001_formal_split_admission_artifacts_v1(
            repository_root=repo,
        )
        output_root = repo / OUTPUT_ROOT_RELATIVE_V1
        if output_root.exists():
            unexpected = {
                path.name for path in output_root.iterdir()
                if path.name not in OUTPUT_FILENAMES_V1
            }
            if unexpected:
                _fail("OUTPUT_DIRECTORY_CONTAINS_UNEXPECTED_FILES")
        for name in OUTPUT_FILENAMES_V1:
            _atomic_write(output_root / name, artifacts[name])
        return artifacts
    except Exception as error:
        _public_error(error)
