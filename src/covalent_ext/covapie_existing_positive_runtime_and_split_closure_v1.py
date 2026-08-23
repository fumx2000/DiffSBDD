"""Close existing positive runtime bindings and leakage-safe splits, V1.

This successor consumes the published cumulative1000 products and their
authority audit read-only.  It tensorizes only the seven already-fully-
supervised runtime-incomplete positives, reconciles the five unsplit K36
events with the same published leakage policy, and never performs network,
model, optimizer, checkpoint, or training work.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
import copy
import csv
from dataclasses import dataclass, fields
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path
import stat
import subprocess
from types import SimpleNamespace
from typing import Any, NoReturn

import torch

from covalent_ext import covapie_bulk_cys_sg_dataset_expansion_v1 as bulk_owner
from covalent_ext import covapie_cys_sg_dataset_expansion_pipeline_v1 as split_owner
from covalent_ext import covapie_direct_attachment_optional_linker_runtime_v1 as role_owner
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CANONICAL_TASKS_V1,
    CovapieCurrent11TrainingSupervisionTensorsV1,
)
from covalent_ext.covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1 import (
    CHECKPOINT_CHANNEL_ORDER,
    project_type_symbols_to_checkpoint_heavy_v1,
)


__all__ = (
    "EXISTING_POSITIVE_RUNTIME_SPLIT_CLOSURE_ERROR_V1",
    "OUTPUT_ROOT_RELATIVE_V1",
    "OUTPUT_FILENAMES_V1",
    "RUNTIME_TARGET_EVENT_IDS_V1",
    "K36_EVENT_IDS_V1",
    "ExistingPositiveRuntimeSplitClosureComputationV1",
    "compute_covapie_existing_positive_runtime_and_split_closure_v1",
    "build_covapie_existing_positive_runtime_and_split_closure_artifacts_v1",
    "materialize_covapie_existing_positive_runtime_and_split_closure_artifacts_v1",
    "validate_runtime_adapter_payload_v1",
    "validate_leakage_split_rows_v1",
    "observe_repository_state_v1",
    "classify_repository_profile_v1",
)


EXISTING_POSITIVE_RUNTIME_SPLIT_CLOSURE_ERROR_V1 = (
    "COVAPIE_EXISTING_POSITIVE_RUNTIME_AND_SPLIT_CLOSURE_V1_ERROR"
)
SCHEMA_VERSION_V1 = "covapie_existing_positive_runtime_and_split_closure_v1"
BASELINE_HEAD_V1 = "4a648e83e066d7d5d90467b3f4f3fee3eb69b09b"
BASELINE_PARENT_V1 = "cbc939ff1891702745ac5f308e6b0a5ae0ec2a00"
BASELINE_TREE_V1 = "3e1a358c232cc3bdc6daf3a77cdace8b39821b0f"
BASELINE_SUBJECT_V1 = (
    "add CovaPIE bulk Cys-SG model-usable auto-admission scale-up v1"
)
PUBLICATION_SUBJECT_V1 = (
    "add CovaPIE existing positive runtime and split closure v1"
)

OUTPUT_ROOT_RELATIVE_V1 = Path(
    "data/derived/covalent_small/"
    "covapie_existing_positive_runtime_and_split_closure_v1"
)
RUNTIME_INVENTORY_V1 = "covapie_existing_positive_runtime_binding_inventory_v1.csv"
LEAKAGE_INVENTORY_V1 = (
    "covapie_existing_positive_leakage_split_closure_inventory_v1.csv"
)
POSITIVE_INDEX_V1 = "covapie_current_runtime_model_usable_positive_index_v1.csv"
MANIFEST_V1 = "covapie_existing_positive_runtime_and_split_closure_manifest_v1.json"
SUMMARY_V1 = "covapie_existing_positive_runtime_and_split_closure_summary_v1.json"
OUTPUT_FILENAMES_V1 = (
    RUNTIME_INVENTORY_V1,
    LEAKAGE_INVENTORY_V1,
    POSITIVE_INDEX_V1,
    MANIFEST_V1,
    SUMMARY_V1,
)

SOURCE_RELATIVE_V1 = Path(
    "src/covalent_ext/covapie_existing_positive_runtime_and_split_closure_v1.py"
)
CHECKER_RELATIVE_V1 = Path(
    "scripts/check_covapie_existing_positive_runtime_and_split_closure_v1.py"
)
TEST_RELATIVE_V1 = Path(
    "tests/test_covapie_existing_positive_runtime_and_split_closure_v1.py"
)
AUTHORIZED_PATHS_V1 = frozenset({
    SOURCE_RELATIVE_V1.as_posix(),
    CHECKER_RELATIVE_V1.as_posix(),
    TEST_RELATIVE_V1.as_posix(),
    *((OUTPUT_ROOT_RELATIVE_V1 / name).as_posix() for name in OUTPUT_FILENAMES_V1),
})

SCALEUP_ROOT_V1 = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1"
)
CENSUS_V1 = SCALEUP_ROOT_V1 / "covapie_bulk_cys_sg_cumulative_1000_model_usable_census_v1.csv"
EFFECTIVE_N_V1 = SCALEUP_ROOT_V1 / "covapie_bulk_cys_sg_effective_supervised_n_by_head_v1.json"
SCALEUP_MANIFEST_V1 = SCALEUP_ROOT_V1 / "covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_manifest_v1.json"
SCALEUP_SUMMARY_V1 = SCALEUP_ROOT_V1 / "covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_summary_v1.json"

CANONICAL_EVENTS_V1 = Path(
    "data/derived/covalent_small/covapie_bulk_cys_sg_dataset_expansion_v1/"
    "bulk_pilot_v1/cross_source_canonical_event_manifest_v1.json"
)
BATCH001_COMPONENTS_V1 = Path(
    "data/derived/covalent_small/covapie_batch001_formal_split_leakage_admission_v1/"
    "covapie_batch001_formal_leakage_component_registry_v1.json"
)
BATCH13_INDEX_V1 = Path(
    "data/derived/covalent_small/"
    "covapie_batch001_13event_model_usable_split_materialization_and_activation_boundary_v1/"
    "covapie_batch001_13event_model_usable_split_index_v1.csv"
)
CURRENT11_INDEX_V1 = Path(
    "data/derived/covalent_small/"
    "covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0/"
    "unified_sample_index.csv"
)
CURRENT11_SPLIT_V1 = Path(
    "data/derived/covalent_small/covapie_unified_leakage_split_materialization_smoke_v0/"
    "covapie_sample_split_assignment.csv"
)
DIRECT_LIGAND_ROWS_V1 = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_"
    "exported_step8_topology_v0/ligand_observed_atom_topology_smoke_table.csv"
)
DIRECT_POCKET_ROWS_V1 = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_pocket_extraction_smoke_v0/"
    "real_covalent_confirmed_candidate_pocket_atom_table.csv"
)

AUTHORITY_REGISTRY_V1 = bulk_owner.AUTHORITY_REGISTRY_RELATIVE
LEAKAGE_REGISTRY_V1 = bulk_owner.LEAKAGE_REGISTRY_RELATIVE
BASELINE_LIGAND_EVIDENCE_V1 = split_owner.BASELINE_LIGAND_EVIDENCE_RELATIVE
BASELINE_PROTEIN_EVIDENCE_V1 = split_owner.BASELINE_PROTEIN_EVIDENCE_RELATIVE
BASELINE_GROUP_EVIDENCE_V1 = split_owner.BASELINE_FINAL_GROUP_RELATIVE
BASELINE_GROUP_SPLITS_V1 = split_owner.PUBLISHED_GROUP_SPLIT_RELATIVE

STATE_CACHE_ROOT_RELATIVE_V1 = Path("covapie-state/bulk-multisource-cys-sg-v1")
STATE_CACHE_MANIFEST_V1 = STATE_CACHE_ROOT_RELATIVE_V1 / "cache_manifest_v1.json"
FIRST500_VIEW_RELATIVE_V1 = Path(
    "covapie-state/bulk-500-controlled-execution-v1/attempt-001/"
    "cumulative_processing_view_v1.json"
)

FIXED_REPOSITORY_INPUT_SHA256_V1 = {
    CENSUS_V1: "5998991f4a777dc8364d773e68a438837e656983aab805dae388b64c3619dbc5",
    EFFECTIVE_N_V1: "4f2139907618fc8b7d559a48b306936ae3bb1b5fea7fea3a6e8f96d4b9325426",
    SCALEUP_MANIFEST_V1: "89e69035110abcdae7ef9fd7507d16eb3cb3002de848b244ab3d27f966202ac1",
    SCALEUP_SUMMARY_V1: "e0e0c64c07b32f1e9f6b3d8ed4c9af6ec9b7db77eeb80345e2de7eab54e65561",
    CANONICAL_EVENTS_V1: "d3f35987af92fca669b85d62a86914c7a01bf35d867c4a779e7fc08e76445dae",
    BATCH001_COMPONENTS_V1: "76e6ecae7dfde7c9e5081a0164f9a72628e4f30550e831a8f8ba5cd3d1d16544",
    BATCH13_INDEX_V1: "f22064a20000126b0792a22e241f3cf9d912bc804da7c5f58eb2f5669157faf3",
    CURRENT11_INDEX_V1: "d610e7171ad976f16055584582335ce756ed0210e6c15d6b55a1a234bc92c326",
    CURRENT11_SPLIT_V1: "29ffff244e33e3ec93f2c2b3e5e42a09ce73d7f55019f833e97659301f6a388c",
    DIRECT_LIGAND_ROWS_V1: "b47d03598a077e6201e21585c683fe46a7423d99fae231b47c303657bad89c59",
    DIRECT_POCKET_ROWS_V1: "77dc7777d44ec48ecc985c9c7d66d603756781455b7b3d5c9151dd5800ceaee9",
    AUTHORITY_REGISTRY_V1: "c6f150bd82b1ea45121aa96e1fefb6af3be64584117cc462f74b2e10fd1913e9",
    LEAKAGE_REGISTRY_V1: "24a58a6f9cc551c9b38527c1bfbf64aa2661bf1173b8eabcb44428513bfe15c8",
    BASELINE_LIGAND_EVIDENCE_V1: "982a9f89a89d3a4ad6a3e468cfd16d2fdfd5435cbf6d593e086fbd7fadd3ec73",
    BASELINE_PROTEIN_EVIDENCE_V1: "51f208c2582bc41c265fa35fa18e71e0e0d0634babe63b9735f084aa486a0d30",
    BASELINE_GROUP_EVIDENCE_V1: "768c964f22e19a8fb6232b1fa26c531e53d023042abcd9b1bcca44df2b4f4416",
    BASELINE_GROUP_SPLITS_V1: "ed62fcf56ad87d8a49743517329c97aa98d3a781562fa403b4b43a9b9ea3ffc3",
    Path("src/covalent_ext/covapie_current11_training_tensorizer_v1.py"): "9fdc3f7f101fab5e5e5452e3d8e9f9b0b1e6e5fa8254a261f36310a1dfd0b606",
    Path("src/covalent_ext/covapie_expanded_cys_sg_mixed_profile_tensorizer_v1.py"): "c95bac177ba2ef1dd519bb5659cb97a8367484b1e41553be56fe3b2789ceb932",
    Path("src/covalent_ext/covapie_direct_attachment_optional_linker_runtime_v1.py"): "434285a43fa0158e62d40f48ed95d137f5fd68ea9b00101cc20674025849c535",
    Path("src/covalent_ext/covapie_exact16_post_geometry_partial_supervision_authority_v1.py"): "6f388b42bd58ffed67ed752a9fec9f85e57050fc96a89e6f3d3e90b1281dba44",
    Path("src/covalent_ext/covapie_bulk_cys_sg_dataset_expansion_v1.py"): "ef17777a634284a94662ac3277c02a7fb4efa20375d84fcf88ac074c61e69ce0",
    Path("src/covalent_ext/covapie_cys_sg_dataset_expansion_pipeline_v1.py"): "ece0221669400b75c152edd11c18b36d87056d989344e9bc1ae674612f8d4dd6",
    Path("src/covalent_ext/covapie_unified_leakage_split_materialization_smoke.py"): "4e565e670ef09fd78c65c5aa799378f3efbd965dc896c65d37a6896d71c5212e",
}
FIXED_EXTERNAL_INPUT_SHA256_V1 = {
    STATE_CACHE_MANIFEST_V1: "10057a8fd7e34c5e63a912a44f242926247aef15cffefa942dceb910d3f1cd58",
    FIRST500_VIEW_RELATIVE_V1: "a27d4bf7977d5a175387af83021270c68f9cf3e8db391113dc6f1ff22f0bfc44",
}

RUNTIME_TARGET_EVENT_IDS_V1 = (
    "COVAPIE_CYS_SG_EVENT_V1:6OIM:A:CYS:12-:SG:D:MOV:C25",
    "COVAPIE_CYS_SG_EVENT_V1:6DI9:A:CYS:481-:SG:B:GJJ:C33",
    "COVAPIE_CYS_SG_EVENT_V1:5F2E:A:CYS:12-:SG:E:5UT:C15",
    "COVAPIE_CYS_SG_EVENT_V1:1NFZ:A:CYS:67-:SG:E:EIP:C12",
    "COVAPIE_CYS_SG_EVENT_V1:1NFZ:B:CYS:67-:SG:H:EIP:C12",
    "COVAPIE_CYS_SG_EVENT_V1:2AX0:A:CYS:366-:SG:F:5X:C1",
    "COVAPIE_CYS_SG_EVENT_V1:2AX0:B:CYS:366-:SG:K:5X:C1",
)
AJ3_EVENT_ID_V1 = "COVAPIE_CYS_SG_EVENT_V1:1BWC:A:CYS:58-:SG:D:AJ3:S5"
K36_EVENT_IDS_V1 = (
    "COVAPIE_CYS_SG_EVENT_V1:4DCD:A:CYS:147-:SG:C:K36:C21",
    "COVAPIE_CYS_SG_EVENT_V1:4F49:A:CYS:144-:SG:E:K36:C21",
    "COVAPIE_CYS_SG_EVENT_V1:5WKJ:A:CYS:148-:SG:E:K36:C21",
    "COVAPIE_CYS_SG_EVENT_V1:6L70:A:CYS:144-:SG:C:K36:C21",
    "COVAPIE_CYS_SG_EVENT_V1:6WTT:A:CYS:145-:SG:D:K36:C21",
)
K36_IDENTITY_BY_EVENT_V1 = {
    event_id: event_id.split(":")[1] + "/K36" for event_id in K36_EVENT_IDS_V1
}

EXACT3_SPECS_V1 = {
    RUNTIME_TARGET_EVENT_IDS_V1[0]: (
        "6OIM/MOV",
        Path("data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/6oim_mov_approved_v1/samples/a23745e87b364fe7.materialized.json"),
        Path("data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/6oim_mov_approved_v1/samples/a23745e87b364fe7.tensorized.json"),
    ),
    RUNTIME_TARGET_EVENT_IDS_V1[1]: (
        "6DI9/GJJ",
        Path("data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/6di9_gjj_approved_v1/samples/8483b1e83aa8e1b6.materialized.json"),
        Path("data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/6di9_gjj_approved_v1/samples/8483b1e83aa8e1b6.tensorized.json"),
    ),
    RUNTIME_TARGET_EVENT_IDS_V1[2]: (
        "5F2E/5UT",
        Path("data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/5f2e_5ut_approved_v1/samples/7aeb236b1946e96f.materialized.json"),
        Path("data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/5f2e_5ut_approved_v1/samples/7aeb236b1946e96f.tensorized.json"),
    ),
}

_DATACLASS_FIELDS_V1 = tuple(field.name for field in fields(
    CovapieCurrent11TrainingSupervisionTensorsV1
))
_MODEL_INPUT_FIELDS_V1 = (
    "names", "receptors", "lig_coords", "pocket_coords", "lig_one_hot",
    "pocket_one_hot", "lig_source_row_index", "pocket_source_row_index",
    "lig_parser_local_index", "pocket_parser_local_index", "num_lig_atoms",
    "num_pocket_nodes", "lig_mask", "pocket_mask",
)
_ALLOWED_MAPPING_METHODS_V1 = frozenset((
    "APPROVED_TENSORIZED_ROW_AND_EXACT_ENDPOINT_BINDING",
    "CANONICAL_EVENT_MMCIF_EXACT_ENDPOINT_BINDING",
))
_SPLITS_V1 = ("train", "validation", "test")


class _ClosureInvariantError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _fail(reason: str) -> NoReturn:
    raise _ClosureInvariantError(reason)


def _public_error(error: Exception) -> NoReturn:
    if isinstance(error, _ClosureInvariantError):
        raise ValueError(
            f"{EXISTING_POSITIVE_RUNTIME_SPLIT_CLOSURE_ERROR_V1}:{error.reason}"
        ) from error
    if type(error) is ValueError and str(error).startswith(
        EXISTING_POSITIVE_RUNTIME_SPLIT_CLOSURE_ERROR_V1
    ):
        raise error
    raise ValueError(EXISTING_POSITIVE_RUNTIME_SPLIT_CLOSURE_ERROR_V1) from error


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _json_cell(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _csv_bytes(header: Sequence[str], rows: Sequence[Mapping[str, object]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=tuple(header), lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_bytes())
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise _ClosureInvariantError("JSON_INPUT_INVALID:" + path.as_posix()) from error
    if type(value) is not dict:
        _fail("JSON_ROOT_NOT_OBJECT:" + path.as_posix())
    return value


def _read_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as error:
        raise _ClosureInvariantError("CSV_INPUT_INVALID:" + path.as_posix()) from error
    if reader.fieldnames is None:
        _fail("CSV_HEADER_MISSING:" + path.as_posix())
    return rows


def _binding(path: Path, *, display: str) -> dict[str, object]:
    payload = path.read_bytes()
    return {"path": display, "byte_count": len(payload), "sha256": _sha256(payload)}


def _require_fixed_inputs(repo: Path) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for relative, expected in FIXED_REPOSITORY_INPUT_SHA256_V1.items():
        path = repo / relative
        if not path.is_file():
            _fail("BOUND_INPUT_MISSING:" + relative.as_posix())
        observed = _binding(path, display=relative.as_posix())
        if observed["sha256"] != expected:
            _fail("BOUND_INPUT_SHA256_MISMATCH:" + relative.as_posix())
        result.append(observed)
    for relative, expected in FIXED_EXTERNAL_INPUT_SHA256_V1.items():
        path = repo.parent / relative
        if not path.is_file():
            _fail("EXTERNAL_BOUND_INPUT_MISSING:" + relative.as_posix())
        observed = _binding(path, display=relative.as_posix())
        if observed["sha256"] != expected:
            _fail("EXTERNAL_BOUND_INPUT_SHA256_MISMATCH:" + relative.as_posix())
        result.append(observed)
    return result


def _verify_audit_owner_bindings(
    repo: Path, summary: Mapping[str, Any]
) -> list[dict[str, object]]:
    audit = summary.get("global_current_positive_authority_audit")
    if type(audit) is not dict:
        _fail("PUBLISHED_37_EVENT_AUDIT_MISSING")
    result: list[dict[str, object]] = []
    for raw in audit.get("repository_owner_bindings", ()):
        if type(raw) is not dict:
            _fail("AUDIT_OWNER_BINDING_INVALID")
        relative = raw.get("path")
        expected = raw.get("sha256")
        if type(relative) is not str or type(expected) is not str:
            _fail("AUDIT_OWNER_BINDING_INVALID")
        observed = _binding(repo / relative, display=relative)
        if observed["sha256"] != expected or observed["byte_count"] != raw.get("byte_count"):
            _fail("AUDIT_OWNER_BINDING_DRIFT:" + relative)
        result.append(observed)
    for raw in audit.get("external_owner_bindings", ()):
        if type(raw) is not dict:
            _fail("AUDIT_EXTERNAL_OWNER_BINDING_INVALID")
        relative = raw.get("path")
        expected = raw.get("sha256")
        if type(relative) is not str or type(expected) is not str:
            _fail("AUDIT_EXTERNAL_OWNER_BINDING_INVALID")
        observed = _binding(repo.parent / relative, display=relative)
        if observed["sha256"] != expected or observed["byte_count"] != raw.get("byte_count"):
            _fail("AUDIT_EXTERNAL_OWNER_BINDING_DRIFT:" + relative)
        result.append(observed)
    if len(result) != 18:
        _fail("AUDIT_OWNER_BINDING_COUNT_INVALID")
    return result


def _one_hot(channels: Sequence[int]) -> torch.Tensor:
    if any(type(value) is not int or value not in range(10) for value in channels):
        _fail("FEATURE_CHANNEL_INVALID")
    return torch.eye(10, dtype=torch.float32)[torch.tensor(tuple(channels), dtype=torch.long)]


def _tensor_sha(value: torch.Tensor) -> str:
    cpu = value.detach().to(device="cpu").contiguous()
    return _sha256(cpu.numpy().tobytes())


def _derive_profile(roles: Mapping[str, Sequence[object]]) -> str:
    scaffold = tuple(roles["scaffold_atom_ids"])
    linker = tuple(roles["linker_atom_ids"])
    warhead = tuple(roles["warhead_atom_ids"])
    if scaffold and linker and warhead:
        return role_owner.STRICT_LINKER_PRESENT_V1
    if scaffold and not linker and warhead:
        return role_owner.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1
    _fail("ROLE_PROFILE_NOT_MECHANICALLY_DERIVABLE")


def validate_runtime_adapter_payload_v1(payload: object) -> None:
    """Fail closed on one authority-to-runtime mapping payload."""

    try:
        if type(payload) is not dict:
            _fail("RUNTIME_ADAPTER_PAYLOAD_NOT_OBJECT")
        event_id = payload.get("canonical_event_id")
        if event_id == AJ3_EVENT_ID_V1:
            _fail("AJ3_PROMOTION_FORBIDDEN")
        if event_id != payload.get("expected_canonical_event_id"):
            _fail("CANONICAL_EVENT_MISMATCH")
        if event_id not in RUNTIME_TARGET_EVENT_IDS_V1:
            _fail("RUNTIME_TARGET_OUTSIDE_EXACT7")
        if payload.get("mapping_method") not in _ALLOWED_MAPPING_METHODS_V1:
            _fail("FUZZY_OR_CHEMISTRY_SIGNATURE_ONLY_MAPPING_FORBIDDEN")
        if payload.get("source_bindings_verified") is not True:
            _fail("SOURCE_SHA_DRIFT")
        sources = payload.get("authority_sources")
        if type(sources) is not tuple or not sources or any(
            type(value) is not str or not value for value in sources
        ):
            _fail("AUTHORITY_SOURCE_MISSING")
        retained = payload.get("ligand_atom_ids")
        roles = payload.get("roles")
        if type(retained) is not tuple or not retained or len(set(retained)) != len(retained):
            _fail("LIGAND_ATOM_IDENTITY_INVALID")
        if type(roles) is not dict or set(roles) != {
            "scaffold_atom_ids", "linker_atom_ids", "warhead_atom_ids"
        }:
            _fail("ROLE_AUTHORITY_INVALID")
        role_sequences = tuple(tuple(roles[name]) for name in (
            "scaffold_atom_ids", "linker_atom_ids", "warhead_atom_ids"
        ))
        if any(len(value) != len(set(value)) for value in role_sequences):
            _fail("ROLE_DUPLICATE")
        if any(set(left) & set(right) for index, left in enumerate(role_sequences) for right in role_sequences[index + 1:]):
            _fail("ROLE_OVERLAP")
        union = set().union(*(set(value) for value in role_sequences))
        if union != set(retained):
            _fail("ROLE_GAP_OR_UNKNOWN_ATOM")
        profile = payload.get("role_profile")
        if profile not in role_owner.ROLE_PROFILES_V1:
            _fail("UNSUPPORTED_ROLE_PROFILE")
        if profile != _derive_profile(roles):
            _fail("ROLE_PROFILE_AUTHORITY_MISMATCH")
        validation = role_owner.validate_role_profile_v1(
            role_profile=profile,
            retained_heavy_atoms=retained,
            scaffold_atoms=role_sequences[0],
            linker_atoms=role_sequences[1],
            warhead_atoms=role_sequences[2],
        )
        if validation.valid is not True:
            _fail("ROLE_PROFILE_VALIDATION_FAILED")
        expected_tasks = role_owner.valid_canonical_task_ids_for_role_profile_v1(profile)
        if tuple(payload.get("valid_task_ids", ())) != expected_tasks:
            _fail("ROLE_PROFILE_TASK_DOMAIN_MISMATCH")
        if profile == role_owner.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1 and any(
            task in payload["valid_task_ids"] for task in (1, 2)
        ):
            _fail("DIRECT_ATTACHMENT_TASK1_OR_TASK2_ACTIVATED")
        reactive = payload.get("ligand_reactive_atom_id")
        if (
            reactive != payload.get("expected_ligand_reactive_atom_id")
            or reactive not in set(role_sequences[2])
        ):
            _fail("REACTIVE_PAIR_MISMATCH")
        pair = payload.get("positive_reactive_pair_indices")
        if type(pair) is not tuple or len(pair) != 2:
            _fail("REACTIVE_PAIR_INDEX_INVALID")
        ligand_index, pocket_index = pair
        if (
            type(ligand_index) is not int
            or type(pocket_index) is not int
            or retained[ligand_index] != reactive
            or pocket_index != payload.get("target_reactive_pocket_local_index")
            or pocket_index not in set(payload.get("target_residue_member_indices", ()))
        ):
            _fail("REACTIVE_PAIR_MISMATCH")
        if payload.get("POST_geometry_authoritative") is not True:
            _fail("POST_AUTHORITY_MISSING")
        post = payload.get("POST_distance_angstrom")
        if type(post) is not float or not math.isfinite(post) or post <= 0:
            _fail("POST_GEOMETRY_INVALID")
        if (
            payload.get("PRE_geometry_authoritative") is not False
            or payload.get("PRE_loss_eligible") is not False
            or payload.get("PRE_distance_angstrom") is not None
        ):
            _fail("PRE_FABRICATION")
        if payload.get("feature_compatible") is not True:
            _fail("FEATURE_INCOMPATIBILITY")
        if tuple(payload.get("dataclass_field_names", ())) != _DATACLASS_FIELDS_V1:
            _fail("CURRENT_DATACLASS_FIELD_MISSING")
        if tuple(payload.get("model_input_field_names", ())) != _MODEL_INPUT_FIELDS_V1:
            _fail("CURRENT_MODEL_INPUT_FIELD_MISSING")
        for count_name, source_name, parser_name in (
            ("ligand_atom_count", "ligand_source_row_indices", "ligand_parser_local_indices"),
            ("pocket_atom_count", "pocket_source_row_indices", "pocket_parser_local_indices"),
        ):
            count = payload.get(count_name)
            source_rows = payload.get(source_name)
            parser_rows = payload.get(parser_name)
            if (
                type(count) is not int
                or count <= 0
                or type(source_rows) is not tuple
                or type(parser_rows) is not tuple
                or len(source_rows) != count
                or len(parser_rows) != count
                or any(type(value) is not int or value < 0 for value in source_rows)
                or len(set(source_rows)) != count
                or parser_rows != tuple(range(count))
            ):
                _fail("SOURCE_ROW_OR_PARSER_INDEX_IDENTITY_INVALID")
    except Exception as error:
        _public_error(error)


@dataclass(frozen=True)
class RuntimeClosedSampleV1:
    canonical_event_id: str
    sample_identity: str
    payload: Mapping[str, Any]
    model_input_batch: Mapping[str, object]
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1


@dataclass(frozen=True)
class ExistingPositiveRuntimeSplitClosureComputationV1:
    source_bindings: tuple[Mapping[str, object], ...]
    authority_records_before: tuple[Mapping[str, Any], ...]
    runtime_samples: tuple[RuntimeClosedSampleV1, ...]
    runtime_binding_rows: tuple[Mapping[str, str], ...]
    leakage_split_rows: tuple[Mapping[str, str], ...]
    positive_index_rows: tuple[Mapping[str, str], ...]
    counts: Mapping[str, int]
    existing_split_assignments_changed: bool
    cross_split_leakage_group_count: int


def _validate_training_mask_activation_v1(
    supervision: CovapieCurrent11TrainingSupervisionTensorsV1,
    *,
    training_admitted: bool,
) -> None:
    """Fail closed when training activation differs from final split admission."""

    try:
        if (
            not isinstance(supervision, CovapieCurrent11TrainingSupervisionTensorsV1)
            or type(training_admitted) is not bool
        ):
            _fail("TRAINING_MASK_VALIDATION_INPUT_INVALID")
        sample_admitted = supervision.sample_training_admitted
        if sample_admitted.shape != (1,) or bool(sample_admitted.item()) != training_admitted:
            _fail("SAMPLE_TRAINING_ADMISSION_MISMATCH")
        if (
            supervision.canonical_task_valid.shape != (1,)
            or not bool(supervision.canonical_task_valid.item())
            or not bool(supervision.ligand_role_valid.all().item())
            or not bool(supervision.target_residue_condition_valid.item())
            or not bool(supervision.pair_positive_candidate_valid.item())
            or not bool(supervision.observed_complex_pair_distance_valid.item())
            or not torch.equal(
                supervision.pre_post_geometry_component_valid_mask,
                torch.tensor([[False, True]], dtype=torch.bool),
            )
        ):
            _fail("RUNTIME_LABEL_OR_STRUCTURAL_VALIDITY_LOST")
        expected_geometry_loss = torch.tensor(
            [[False, training_admitted]], dtype=torch.bool
        )
        if not torch.equal(
            supervision.pre_post_geometry_component_loss_mask,
            expected_geometry_loss,
        ):
            _fail("GEOMETRY_LOSS_MASK_ADMISSION_MISMATCH")
        if training_admitted:
            if (
                not torch.equal(
                    supervision.ligand_active_diffusion_loss_mask,
                    supervision.ligand_base_generation_mask,
                )
                or not bool(supervision.ligand_active_diffusion_loss_mask.any().item())
                or not bool(supervision.pair_head_candidate_loss_mask.all().item())
                or not bool(supervision.pair_contrastive_sample_loss_mask.item())
            ):
                _fail("TRAIN_SAMPLE_LOSS_MASK_INACTIVE")
        elif (
            bool(supervision.ligand_active_diffusion_loss_mask.any().item())
            or bool(supervision.pair_head_candidate_loss_mask.any().item())
            or bool(supervision.pair_contrastive_sample_loss_mask.item())
            or bool(supervision.pre_post_geometry_component_loss_mask.any().item())
        ):
            _fail("HELDOUT_TRAINING_LOSS_MASK_ACTIVE")
    except Exception as error:
        _public_error(error)


def _model_batch_and_supervision(
    payload: Mapping[str, Any],
    *,
    task_id: int = 0,
    training_admitted: bool,
) -> tuple[dict[str, object], CovapieCurrent11TrainingSupervisionTensorsV1]:
    if type(training_admitted) is not bool:
        _fail("TRAINING_ADMISSION_NOT_EXPLICIT_BOOL")
    profile = str(payload["role_profile"])
    valid_tasks = tuple(payload["valid_task_ids"])
    if task_id not in valid_tasks:
        _fail("TASK_NOT_APPLICABLE_FOR_ROLE_PROFILE")
    ligand_coordinates = payload["ligand_coordinates"]
    pocket_coordinates = payload["pocket_coordinates"]
    ligand_channels = payload["ligand_channels"]
    pocket_channels = payload["pocket_channels"]
    if not isinstance(ligand_coordinates, torch.Tensor) or not isinstance(pocket_coordinates, torch.Tensor):
        _fail("COORDINATE_TENSOR_MISSING")
    ligand_count = len(ligand_coordinates)
    pocket_count = len(pocket_coordinates)
    if (
        ligand_coordinates.shape != (ligand_count, 3)
        or pocket_coordinates.shape != (pocket_count, 3)
        or not bool(torch.isfinite(ligand_coordinates).all().item())
        or not bool(torch.isfinite(pocket_coordinates).all().item())
    ):
        _fail("COORDINATE_TENSOR_INVALID")
    roles = payload["roles"]
    retained = tuple(payload["ligand_atom_ids"])
    role_by_atom = {
        atom: role_id
        for role_id, name in enumerate(("scaffold_atom_ids", "linker_atom_ids", "warhead_atom_ids"))
        for atom in roles[name]
    }
    role_ids = tuple(role_by_atom[atom] for atom in retained)
    scaffold = tuple(index for index, value in enumerate(role_ids) if value == 0)
    linker = tuple(index for index, value in enumerate(role_ids) if value == 1)
    warhead = tuple(index for index, value in enumerate(role_ids) if value == 2)
    mask = role_owner.build_mask_for_role_profile_v1(
        role_profile=profile,
        canonical_task_id=task_id,
        scaffold_atoms=scaffold,
        linker_atoms=linker,
        warhead_atoms=warhead,
        num_ligand_atoms=ligand_count,
    )
    generation = torch.zeros(ligand_count, dtype=torch.bool)
    generation[list(mask.masked_atoms)] = True
    fixed = ~generation
    compatibility = role_owner.validate_current_lightning_structural_expectations_v1(
        role_profile=profile,
        canonical_task_id=task_id,
        ligand_role_ids=role_ids,
        mask_result=mask,
    )
    if compatibility.valid is not True:
        _fail("MASK_MODEL_CONTRACT_INVALID")

    target_members = tuple(payload["target_residue_member_indices"])
    target_reactive = int(payload["target_reactive_pocket_local_index"])
    ligand_reactive = int(payload["positive_reactive_pair_indices"][0])
    target_membership = torch.zeros(pocket_count, dtype=torch.bool)
    target_membership[list(target_members)] = True
    target_indicator = torch.zeros(pocket_count, dtype=torch.bool)
    target_indicator[target_reactive] = True
    member_tensor = torch.tensor(target_members, dtype=torch.long)
    ligand_local = torch.arange(ligand_count, dtype=torch.long).repeat_interleave(len(member_tensor))
    pocket_local = member_tensor.repeat(ligand_count)
    positive = (ligand_local == ligand_reactive) & (pocket_local == target_reactive)
    if int(positive.sum().item()) != 1:
        _fail("PAIR_POSITIVE_NOT_EXACTLY_ONE")
    positive_index = int(torch.nonzero(positive, as_tuple=False)[0, 0].item())
    negative_count = len(positive) - 1
    if negative_count <= 0:
        _fail("PAIR_NEGATIVE_COUNT_INVALID")

    seed = torch.zeros(ligand_count, dtype=torch.bool)
    seed_ids = tuple(payload.get("minimal_seed_atom_ids", ()))
    if task_id == 4 and seed_ids:
        index_by_atom = {atom: index for index, atom in enumerate(retained)}
        if any(atom not in index_by_atom for atom in seed_ids):
            _fail("MINIMAL_SEED_MAPPING_INVALID")
        seed[[index_by_atom[atom] for atom in seed_ids]] = True
    target_coordinate = pocket_coordinates[target_reactive]
    anchor_distance = torch.linalg.vector_norm(ligand_coordinates - target_coordinate, dim=1, keepdim=True)
    observed = torch.linalg.vector_norm(
        ligand_coordinates[ligand_reactive] - target_coordinate
    ).reshape(1, 1)
    post = float(payload["POST_distance_angstrom"])
    if abs(float(observed.item()) - post) > 0.0015:
        _fail("POST_DISTANCE_COORDINATE_MISMATCH")

    model_batch: dict[str, object] = {
        "names": [payload["sample_identity"]],
        "receptors": [str(payload["canonical_event_id"]).split(":")[1]],
        "lig_coords": ligand_coordinates,
        "pocket_coords": pocket_coordinates,
        "lig_one_hot": _one_hot(ligand_channels),
        "pocket_one_hot": _one_hot(pocket_channels),
        "lig_source_row_index": torch.tensor(payload["ligand_source_row_indices"], dtype=torch.long),
        "pocket_source_row_index": torch.tensor(payload["pocket_source_row_indices"], dtype=torch.long),
        "lig_parser_local_index": torch.tensor(payload["ligand_parser_local_indices"], dtype=torch.long),
        "pocket_parser_local_index": torch.tensor(payload["pocket_parser_local_indices"], dtype=torch.long),
        "num_lig_atoms": torch.tensor([ligand_count], dtype=torch.long),
        "num_pocket_nodes": torch.tensor([pocket_count], dtype=torch.long),
        "lig_mask": torch.zeros(ligand_count, dtype=torch.long),
        "pocket_mask": torch.zeros(pocket_count, dtype=torch.long),
    }
    targets = torch.tensor([[float("nan"), post]], dtype=torch.float32)
    valid = torch.tensor([[False, True]], dtype=torch.bool)
    loss = torch.tensor([[False, training_admitted]], dtype=torch.bool)
    supervision = CovapieCurrent11TrainingSupervisionTensorsV1(
        sample_training_admitted=torch.tensor([training_admitted], dtype=torch.bool),
        canonical_task_id=torch.tensor([task_id], dtype=torch.long),
        canonical_task_valid=torch.ones(1, dtype=torch.bool),
        ligand_role_id=torch.tensor(role_ids, dtype=torch.long),
        ligand_role_valid=torch.ones(ligand_count, dtype=torch.bool),
        ligand_base_generation_mask=generation.unsqueeze(1),
        ligand_base_fixed_mask=fixed.unsqueeze(1),
        ligand_base_target_mask=generation.unsqueeze(1),
        ligand_base_context_mask=fixed.unsqueeze(1),
        ligand_active_diffusion_loss_mask=(
            generation.unsqueeze(1)
            if training_admitted
            else torch.zeros((ligand_count, 1), dtype=torch.bool)
        ),
        ligand_minimal_seed_or_anchor_mask=seed.unsqueeze(1),
        ligand_minimal_seed_or_anchor_valid=torch.tensor(
            [task_id == 4 and bool(seed_ids)], dtype=torch.bool
        ),
        ligand_anchor_distance_angstrom=anchor_distance,
        ligand_anchor_distance_valid=torch.ones((ligand_count, 1), dtype=torch.bool),
        target_residue_membership_mask=target_membership.unsqueeze(1),
        target_residue_reactive_atom_mask=target_indicator.unsqueeze(1),
        target_residue_reactive_atom_local_index=torch.tensor([target_reactive], dtype=torch.long),
        target_residue_reactive_atom_flat_index=torch.tensor([target_reactive], dtype=torch.long),
        target_residue_condition_valid=torch.ones(1, dtype=torch.bool),
        pair_candidate_offsets=torch.tensor([0, len(positive)], dtype=torch.long),
        pair_candidate_batch_index=torch.zeros(len(positive), dtype=torch.long),
        pair_candidate_ligand_local_index=ligand_local,
        pair_candidate_residue_local_index=pocket_local,
        pair_candidate_ligand_flat_index=ligand_local.clone(),
        pair_candidate_pocket_flat_index=pocket_local.clone(),
        pair_candidate_is_positive=positive,
        pair_candidate_is_negative=~positive,
        pair_positive_candidate_index=torch.tensor([positive_index], dtype=torch.long),
        pair_positive_candidate_valid=torch.ones(1, dtype=torch.bool),
        pair_negative_count=torch.tensor([negative_count], dtype=torch.long),
        pair_head_candidate_loss_mask=torch.full(
            (len(positive),), training_admitted, dtype=torch.bool
        ),
        pair_contrastive_sample_loss_mask=torch.tensor(
            [training_admitted], dtype=torch.bool
        ),
        observed_complex_pair_distance_angstrom=observed,
        observed_complex_pair_distance_valid=torch.ones((1, 1), dtype=torch.bool),
        pre_post_geometry_target_angstrom=targets,
        pre_post_geometry_component_valid_mask=valid,
        pre_post_geometry_component_loss_mask=loss,
    )
    if tuple(field.name for field in fields(supervision)) != _DATACLASS_FIELDS_V1:
        _fail("CURRENT_DATACLASS_PARITY_FAILED")
    if not torch.isnan(supervision.pre_post_geometry_target_angstrom[0, 0]):
        _fail("PRE_TARGET_FABRICATED")
    if bool(supervision.pre_post_geometry_component_valid_mask[0, 0]) or bool(
        supervision.pre_post_geometry_component_loss_mask[0, 0]
    ):
        _fail("PRE_MASK_FABRICATED")
    _validate_training_mask_activation_v1(
        supervision, training_admitted=training_admitted
    )
    return model_batch, supervision


def _base_payload(
    *,
    event_id: str,
    sample_identity: str,
    role_profile: str,
    ligand_atom_ids: Sequence[object],
    roles: Mapping[str, Sequence[object]],
    reactive_atom: object,
    ligand_coordinates: torch.Tensor,
    pocket_coordinates: torch.Tensor,
    ligand_channels: Sequence[int],
    pocket_channels: Sequence[int],
    ligand_source_rows: Sequence[int],
    pocket_source_rows: Sequence[int],
    target_members: Sequence[int],
    target_reactive: int,
    post_distance: float,
    minimal_seed: Sequence[object],
    mapping_method: str,
    authority_sources: Sequence[str],
) -> dict[str, Any]:
    retained = tuple(ligand_atom_ids)
    payload: dict[str, Any] = {
        "canonical_event_id": event_id,
        "expected_canonical_event_id": event_id,
        "sample_identity": sample_identity,
        "mapping_method": mapping_method,
        "authority_sources": tuple(authority_sources),
        "source_bindings_verified": True,
        "role_profile": role_profile,
        "valid_task_ids": role_owner.valid_canonical_task_ids_for_role_profile_v1(role_profile),
        "ligand_atom_ids": retained,
        "roles": {name: tuple(roles[name]) for name in (
            "scaffold_atom_ids", "linker_atom_ids", "warhead_atom_ids"
        )},
        "ligand_reactive_atom_id": reactive_atom,
        "expected_ligand_reactive_atom_id": reactive_atom,
        "positive_reactive_pair_indices": (retained.index(reactive_atom), target_reactive),
        "target_residue_member_indices": tuple(target_members),
        "target_reactive_pocket_local_index": target_reactive,
        "POST_geometry_authoritative": True,
        "POST_distance_angstrom": float(post_distance),
        "PRE_geometry_authoritative": False,
        "PRE_loss_eligible": False,
        "PRE_distance_angstrom": None,
        "feature_compatible": True,
        "dataclass_field_names": _DATACLASS_FIELDS_V1,
        "model_input_field_names": _MODEL_INPUT_FIELDS_V1,
        "ligand_atom_count": len(retained),
        "pocket_atom_count": len(pocket_coordinates),
        "ligand_source_row_indices": tuple(ligand_source_rows),
        "pocket_source_row_indices": tuple(pocket_source_rows),
        "ligand_parser_local_indices": tuple(range(len(retained))),
        "pocket_parser_local_indices": tuple(range(len(pocket_coordinates))),
        "minimal_seed_atom_ids": tuple(minimal_seed),
        "ligand_coordinates": ligand_coordinates,
        "pocket_coordinates": pocket_coordinates,
        "ligand_channels": tuple(ligand_channels),
        "pocket_channels": tuple(pocket_channels),
    }
    validate_runtime_adapter_payload_v1(payload)
    return payload


def _exact3_payloads(
    repo: Path,
    audit_by_event: Mapping[str, Mapping[str, Any]],
    canonical_by_event: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    authority_registry = _read_json(repo / AUTHORITY_REGISTRY_V1)
    authority_by_identity: dict[str, dict[str, Any]] = {}
    for authority in authority_registry.get("authorities", ()):
        if type(authority) is not dict:
            _fail("EXACT3_AUTHORITY_INVALID")
        review = json.loads(authority["source_human_review_record_canonical_json"])
        authority_by_identity[review["candidate_identity"]] = review
    ligand_rows = _read_csv(repo / DIRECT_LIGAND_ROWS_V1)
    pocket_rows = _read_csv(repo / DIRECT_POCKET_ROWS_V1)
    for index, row in enumerate(ligand_rows):
        row["__source_row_index_0based"] = str(index)
    for index, row in enumerate(pocket_rows):
        row["__source_row_index_0based"] = str(index)

    result: list[dict[str, Any]] = []
    for event_id, (identity, materialized_path, tensorized_path) in EXACT3_SPECS_V1.items():
        event = canonical_by_event[event_id]
        audit = audit_by_event[event_id]
        materialized = _read_json(repo / materialized_path)
        tensorized = _read_json(repo / tensorized_path)
        review = authority_by_identity.get(identity)
        if (
            review is None
            or materialized.get("candidate_identity") != identity
            or tensorized.get("sample_identity") != identity
            or materialized.get("post_geometry_authority") is not True
            or materialized.get("pre_geometry_authority") is not False
            or tensorized.get("post_geometry_authority") is not True
            or tensorized.get("pre_geometry_authority") is not False
            or audit.get("canonical_event_id") != event_id
        ):
            _fail("EXACT3_PUBLISHED_AUTHORITY_INVALID:" + identity)
        ligand_coordinates = torch.tensor(tensorized["ligand_coordinates_centered"], dtype=torch.float32)
        pocket_coordinates = torch.tensor(tensorized["pocket_coordinates_centered"], dtype=torch.float32)
        ligand_one_hot = torch.tensor(tensorized["ligand_one_hot_10d"], dtype=torch.float32)
        pocket_one_hot = torch.tensor(tensorized["pocket_one_hot_10d"], dtype=torch.float32)
        ligand_channels = tuple(int(value) for value in torch.argmax(ligand_one_hot, dim=1).tolist())
        pocket_channels = tuple(int(value) for value in torch.argmax(pocket_one_hot, dim=1).tolist())
        if (
            ligand_one_hot.shape != (len(ligand_coordinates), 10)
            or pocket_one_hot.shape != (len(pocket_coordinates), 10)
            or not torch.equal(ligand_one_hot, _one_hot(ligand_channels))
            or not torch.equal(pocket_one_hot, _one_hot(pocket_channels))
            or tensorized.get("checkpoint_channel_order") != CHECKPOINT_CHANNEL_ORDER
        ):
            _fail("EXACT3_FEATURE_PROJECTION_INVALID:" + identity)
        pdb_id = str(event["pdb_id"])
        source_ligand = sorted(
            (row for row in ligand_rows if row["pdb_id"] == pdb_id),
            key=lambda row: int(row["rdkit_atom_idx"]),
        )
        source_pocket = [row for row in pocket_rows if row["pdb_id"] == pdb_id]
        namespace = review["machine_evidence"]["canonical_ligand_atom_namespace"]
        retained = tuple(item["atom_id"] for item in namespace)
        if (
            len(source_ligand) != len(ligand_coordinates)
            or len(source_pocket) != len(pocket_coordinates)
            or tuple(int(row["rdkit_atom_idx"]) for row in source_ligand) != retained
            or tuple(int(value) for value in tensorized["role_ids"])
            != tuple(
                0 if atom in review["reviewed_scaffold_atom_ids"] else
                1 if atom in review["reviewed_linker_atom_ids"] else
                2 if atom in review["reviewed_warhead_role_atom_ids"] else -1
                for atom in retained
            )
        ):
            _fail("EXACT3_ROLE_ROW_BINDING_INVALID:" + identity)
        protein_endpoint_id = str(
            review["machine_evidence"]["exact_event_endpoints"]["protein_endpoint_atom_id"]
        )
        target_reactive_matches = [
            index for index, row in enumerate(source_pocket)
            if row["atom_site_id"] == protein_endpoint_id
            and row["auth_atom_id"] == "SG"
            and row["auth_comp_id"] == "CYS"
        ]
        target_members = [
            index for index, row in enumerate(source_pocket)
            if row["auth_comp_id"] == "CYS"
            and row["auth_seq_id"] == str(event["protein_residue_number"])
            and row["label_asym_id"] == str(event["protein_instance"])
        ]
        pair = tuple(int(value) for value in tensorized["positive_reactive_pair_indices"])
        reactive = review["machine_evidence"]["exact_event_endpoints"]["retained_reactive_atom_id"]
        if (
            len(target_reactive_matches) != 1
            or target_reactive_matches[0] not in target_members
            or pair != (retained.index(reactive), target_reactive_matches[0])
        ):
            _fail("EXACT3_REACTIVE_PAIR_BINDING_INVALID:" + identity)
        geometry = tensorized["geometry_component_values_angstrom"]
        geometry_mask = tensorized["geometry_component_authority_mask"]
        if geometry_mask != [False, True] or type(geometry[1]) not in (int, float):
            _fail("EXACT3_POST_GEOMETRY_INVALID:" + identity)
        roles = {
            "scaffold_atom_ids": review["reviewed_scaffold_atom_ids"],
            "linker_atom_ids": review["reviewed_linker_atom_ids"],
            "warhead_atom_ids": review["reviewed_warhead_role_atom_ids"],
        }
        profile = _derive_profile(roles)
        if profile != review["role_profile"] or profile != materialized["role_profile"]:
            _fail("EXACT3_ROLE_PROFILE_INVALID:" + identity)
        result.append(_base_payload(
            event_id=event_id,
            sample_identity=identity,
            role_profile=profile,
            ligand_atom_ids=retained,
            roles=roles,
            reactive_atom=reactive,
            ligand_coordinates=ligand_coordinates,
            pocket_coordinates=pocket_coordinates,
            ligand_channels=ligand_channels,
            pocket_channels=pocket_channels,
            ligand_source_rows=[int(row["__source_row_index_0based"]) for row in source_ligand],
            pocket_source_rows=[int(row["__source_row_index_0based"]) for row in source_pocket],
            target_members=target_members,
            target_reactive=target_reactive_matches[0],
            post_distance=float(geometry[1]),
            minimal_seed=review["reviewed_minimal_seed_atom_ids"],
            mapping_method="APPROVED_TENSORIZED_ROW_AND_EXACT_ENDPOINT_BINDING",
            authority_sources=tuple(audit["authority_sources"]) + (
                DIRECT_LIGAND_ROWS_V1.as_posix(), DIRECT_POCKET_ROWS_V1.as_posix(),
            ),
        ))
    return result


def _cache_payload_entries(repo: Path) -> dict[str, dict[str, Any]]:
    manifest = _read_json(repo.parent / STATE_CACHE_MANIFEST_V1)
    payloads = manifest.get("payloads")
    if type(payloads) is not list:
        _fail("CACHE_MANIFEST_PAYLOADS_INVALID")
    return {str(item["relative_path"]): item for item in payloads if type(item) is dict}


def _read_cache_payload(
    repo: Path, entries: Mapping[str, Mapping[str, Any]], relative: str
) -> tuple[bytes, dict[str, object]]:
    entry = entries.get(relative)
    if type(entry) is not dict:
        _fail("CACHE_PAYLOAD_BINDING_MISSING:" + relative)
    path = repo.parent / STATE_CACHE_ROOT_RELATIVE_V1 / relative
    payload = path.read_bytes()
    if len(payload) != entry.get("byte_count") or _sha256(payload) != entry.get("sha256"):
        _fail("CACHE_PAYLOAD_SHA256_MISMATCH:" + relative)
    return payload, _binding(path, display=(STATE_CACHE_ROOT_RELATIVE_V1 / relative).as_posix())


def _human_exact4_payloads(
    repo: Path,
    audit_by_event: Mapping[str, Mapping[str, Any]],
    canonical_by_event: Mapping[str, Mapping[str, Any]],
    first500_by_event: Mapping[str, Mapping[str, Any]],
    cache_entries: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, object]]]:
    decisions_path = Path(audit_by_event[RUNTIME_TARGET_EVENT_IDS_V1[3]]["authority_sources"][0])
    decisions = _read_json(repo / decisions_path)
    unit_by_event: dict[str, dict[str, Any]] = {}
    for unit in decisions.get("units", ()):
        if type(unit) is dict:
            for event in unit.get("events", ()):
                if type(event) is dict and event.get("canonical_event_id"):
                    unit_by_event[str(event["canonical_event_id"])] = unit
    result: list[dict[str, Any]] = []
    cache_bindings: list[dict[str, object]] = []
    for event_id in RUNTIME_TARGET_EVENT_IDS_V1[3:]:
        event = canonical_by_event[event_id]
        audit = audit_by_event[event_id]
        outcome = first500_by_event[event_id]
        unit = unit_by_event.get(event_id)
        event_decision = next(
            (value for value in unit.get("events", ()) if value.get("canonical_event_id") == event_id),
            None,
        ) if unit else None
        if (
            unit is None
            or event_decision is None
            or unit.get("workflow_status") != "COMPLETED"
            or event_decision.get("event_training_use_decision") != "INCLUDE"
            or event_decision.get("post_geometry_training_usable") != "YES"
            or unit.get("reactive_atom_confirmation", {}).get("status") != "CONFIRMED"
        ):
            _fail("HUMAN_EXACT4_AUTHORITY_INCOMPLETE:" + event_id)
        relative = f"rcsb/structures/{event['pdb_id']}.cif.gz"
        payload, cache_binding = _read_cache_payload(repo, cache_entries, relative)
        if cache_binding not in cache_bindings:
            cache_bindings.append(cache_binding)
        text = bulk_owner._validate_mmcif_payload(payload, str(event["pdb_id"]))
        _tags, connections, status, _error = bulk_owner.struct_conn_owner.parse_struct_conn_loop(text)
        if status == "raw_parse_error":
            _fail("HUMAN_EXACT4_STRUCT_CONN_PARSE_ERROR:" + event_id)
        matches = []
        for row in connections:
            endpoints = bulk_owner._connection_matches_event(row, event)
            if endpoints is not None:
                matches.append((row, endpoints[0], endpoints[1]))
        preferred = set(event["connection_ids"])
        matches.sort(key=lambda item: (
            0 if bulk_owner._conn_value(item[0], "id") in preferred else 1,
            bulk_owner._conn_value(item[0], "id"), item[1]["altloc"], item[2]["altloc"],
        ))
        if len(matches) != 1:
            _fail("HUMAN_EXACT4_CANONICAL_ENDPOINT_NOT_EXACT_ONE:" + event_id)
        connection, protein_endpoint, ligand_endpoint = matches[0]
        atom_rows = bulk_owner.atom_site_owner.extract_atom_site_loop_rows_v0(text)
        row_index = {id(row): index for index, row in enumerate(atom_rows)}
        protein_candidates = bulk_owner._endpoint_candidates(
            atom_rows, endpoint=protein_endpoint, event=event, protein=True
        )
        ligand_candidates = bulk_owner._endpoint_candidates(
            atom_rows, endpoint=ligand_endpoint, event=event, protein=False
        )
        selected_protein, selected_ligand = bulk_owner._select_endpoint_pair(
            protein_candidates,
            ligand_candidates,
            reported_distance=event["rcsb_structure_authority"]["reported_distance_angstrom"],
        )
        ligand_rows = [
            row for row in bulk_owner._selected_ligand_atoms(atom_rows, event, selected_ligand)
            if bulk_owner._atom_value(row, "type_symbol").upper() != "H"
        ]
        pocket_rows = bulk_owner._selected_pocket_atoms(atom_rows, ligand_rows)
        if any(id(row) not in row_index for row in (*ligand_rows, *pocket_rows)):
            _fail("SOURCE_ROW_IDENTITY_LOST:" + event_id)
        ligand_symbols = tuple(
            bulk_owner._atom_value(row, "type_symbol").strip().title() for row in ligand_rows
        )
        pocket_symbols = tuple(
            bulk_owner._atom_value(row, "type_symbol").strip().title() for row in pocket_rows
        )
        projection = project_type_symbols_to_checkpoint_heavy_v1(ligand_symbols + pocket_symbols)
        if projection.sample_rejected or not all(projection.keep_mask):
            _fail("HUMAN_EXACT4_FEATURE_INCOMPATIBLE:" + event_id)
        ligand_channels = projection.checkpoint_channel_indices[:len(ligand_rows)]
        pocket_channels = projection.checkpoint_channel_indices[len(ligand_rows):]
        ligand_coordinates_raw = torch.tensor(
            [bulk_owner._coordinates(row) for row in ligand_rows], dtype=torch.float32
        )
        pocket_coordinates_raw = torch.tensor(
            [bulk_owner._coordinates(row) for row in pocket_rows], dtype=torch.float32
        )
        centroid = torch.cat((ligand_coordinates_raw, pocket_coordinates_raw), dim=0).mean(dim=0)
        ligand_coordinates = ligand_coordinates_raw - centroid
        pocket_coordinates = pocket_coordinates_raw - centroid
        ligand_ids = tuple(bulk_owner._atom_value(row, "label_atom_id") for row in ligand_rows)
        roles = unit["roles"]
        profile = _derive_profile(roles)
        reactive = unit["reactive_atom_confirmation"]["confirmed_atom_id"]
        ligand_reactive_matches = [index for index, atom in enumerate(ligand_ids) if atom == reactive]
        target_reactive_matches = [index for index, row in enumerate(pocket_rows) if row is selected_protein]
        target_identity = (
            bulk_owner._atom_value(selected_protein, "auth_asym_id"),
            bulk_owner._atom_value(selected_protein, "auth_seq_id"),
            bulk_owner._atom_value(selected_protein, "pdbx_PDB_ins_code"),
        )
        target_members = [
            index for index, row in enumerate(pocket_rows)
            if bulk_owner._atom_value(row, "auth_comp_id").upper() == "CYS"
            and (
                bulk_owner._atom_value(row, "auth_asym_id"),
                bulk_owner._atom_value(row, "auth_seq_id"),
                bulk_owner._atom_value(row, "pdbx_PDB_ins_code"),
            ) == target_identity
        ]
        structural = outcome.get("structural_processing", {})
        post_distance = math.dist(
            bulk_owner._coordinates(selected_protein), bulk_owner._coordinates(selected_ligand)
        )
        ligand_inventory = bulk_owner._sha(bulk_owner._canonical_json([
            {
                "atom": bulk_owner._atom_value(row, "label_atom_id"),
                "element": bulk_owner._atom_value(row, "type_symbol").title(),
                "coordinates": list(bulk_owner._coordinates(row)),
            }
            for row in ligand_rows
        ]))
        pocket_inventory = bulk_owner._sha(bulk_owner._canonical_json([
            {
                "asym": bulk_owner._atom_value(row, "label_asym_id"),
                "seq": bulk_owner._atom_value(row, "label_seq_id"),
                "atom": bulk_owner._atom_value(row, "label_atom_id"),
                "element": bulk_owner._atom_value(row, "type_symbol").title(),
                "coordinates": list(bulk_owner._coordinates(row)),
            }
            for row in pocket_rows
        ]))
        if (
            len(ligand_reactive_matches) != 1
            or len(target_reactive_matches) != 1
            or target_reactive_matches[0] not in target_members
            or bulk_owner._conn_value(connection, "id") != structural.get("selected_connection_id")
            or round(post_distance, 6) != structural.get("post_distance_angstrom")
            or len(ligand_rows) != structural.get("ligand_heavy_atom_count")
            or len(pocket_rows) != structural.get("pocket_heavy_atom_count")
            or ligand_inventory != structural.get("ligand_atom_inventory_sha256")
            or pocket_inventory != structural.get("pocket_atom_inventory_sha256")
        ):
            _fail("HUMAN_EXACT4_STRUCTURAL_PARITY_FAILED:" + event_id)
        result.append(_base_payload(
            event_id=event_id,
            sample_identity=event_id,
            role_profile=profile,
            ligand_atom_ids=ligand_ids,
            roles=roles,
            reactive_atom=reactive,
            ligand_coordinates=ligand_coordinates,
            pocket_coordinates=pocket_coordinates,
            ligand_channels=ligand_channels,
            pocket_channels=pocket_channels,
            ligand_source_rows=[row_index[id(row)] for row in ligand_rows],
            pocket_source_rows=[row_index[id(row)] for row in pocket_rows],
            target_members=target_members,
            target_reactive=target_reactive_matches[0],
            post_distance=float(post_distance),
            minimal_seed=(),
            mapping_method="CANONICAL_EVENT_MMCIF_EXACT_ENDPOINT_BINDING",
            authority_sources=tuple(audit["authority_sources"]) + (
                CANONICAL_EVENTS_V1.as_posix(),
                (STATE_CACHE_ROOT_RELATIVE_V1 / relative).as_posix(),
                FIRST500_VIEW_RELATIVE_V1.as_posix(),
            ),
        ))
    return result, cache_bindings


def _extend_leakage_context_with_batch001_v1(
    context: Mapping[str, Any], components: Mapping[str, Any]
) -> dict[str, Any]:
    extended = copy.deepcopy(dict(context))
    extended["existing_groups"] = list(extended["existing_groups"])
    extended["references"] = list(extended["references"])
    extended["group_info"] = dict(extended["group_info"])
    field_by_axis = {
        "LIGAND_GRAPH": "ligand_graph_sha256",
        "LIGAND_SCAFFOLD": "ligand_scaffold_sha256",
        "PROTEIN_ACCESSION": "protein_accession",
        "PROTEIN_EXACT_SEQUENCE": "protein_sequence_sha256",
    }
    rows = components.get("components")
    if type(rows) is not list or len(rows) != 4:
        _fail("BATCH001_FORMAL_COMPONENT_REGISTRY_INVALID")
    existing_ids = {
        group.final_leakage_group_id for group in extended["existing_groups"]
    }
    for row in rows:
        if type(row) is not dict:
            _fail("BATCH001_FORMAL_COMPONENT_INVALID")
        group_id = row.get("formal_group_id")
        split = row.get("formal_split")
        if group_id in existing_ids or split not in _SPLITS_V1:
            _fail("BATCH001_FORMAL_COMPONENT_CONFLICT")
        group = split_owner.LeakageGroupAssignmentV1(
            leakage_key=str(row["leakage_key"]),
            final_leakage_group_id=str(group_id),
            member_count=int(row["full_identity_count"]),
            assigned_split=str(split),
            frozen=True,
            member_identities=tuple(row["full_member_pdb_ligand_identities"]),
        )
        extended["existing_groups"].append(group)
        extended["group_info"][group.final_leakage_group_id] = {
            "leakage_key": group.leakage_key,
            "group_id": group.final_leakage_group_id,
            "split": group.assigned_split,
            "kind": "CUMULATIVE",
        }
        for value in row["source_evidence_linking_axis_values"]:
            axis, separator, observed = str(value).partition(":")
            field = field_by_axis.get(axis)
            if not separator or field is None or not observed:
                continue
            reference = {
                "identity": (
                    "BATCH001_COMPONENT_REFERENCE:"
                    + group.final_leakage_group_id + ":" + axis + ":" + observed
                ),
                "leakage_key": group.leakage_key,
                "group_id": group.final_leakage_group_id,
                "split": group.assigned_split,
                "kind": "CUMULATIVE",
                "ligand_graph_sha256": "",
                "ligand_scaffold_sha256": "",
                "protein_accession": "",
                "protein_sequence_sha256": "",
                "protein_sequence": "",
            }
            reference[field] = observed
            extended["references"].append(reference)
        existing_ids.add(group.final_leakage_group_id)
    return extended


def _target_leakage_predictions_v1(
    repo: Path,
    *,
    first500_by_event: Mapping[str, Mapping[str, Any]],
    cache_entries: Mapping[str, Mapping[str, Any]],
    audit_by_event: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, object]]]:
    authorities, leakage_registry, _historical = bulk_owner._load_frozen_state_v1(repo)
    context = bulk_owner._load_leakage_prediction_context_v1(
        repo, authorities=authorities, leakage_registry=leakage_registry
    )
    context = _extend_leakage_context_with_batch001_v1(
        context, _read_json(repo / BATCH001_COMPONENTS_V1)
    )
    outcomes = [
        copy.deepcopy(dict(first500_by_event[event_id]))
        for event_id in RUNTIME_TARGET_EVENT_IDS_V1[3:]
    ]
    cache_bindings: list[dict[str, object]] = []
    ccd_payload, ccd_binding = _read_cache_payload(
        repo, cache_entries, "rcsb/ccd/K36.cif"
    )
    cache_bindings.append(ccd_binding)
    ccd = bulk_owner.parse_ccd_cif_v1(ccd_payload, ccd_id="K36")
    structural_path = Path(audit_by_event[K36_EVENT_IDS_V1[0]]["authority_sources"][1])
    structural = _read_json(repo / structural_path)
    structural_by_identity = {
        f"{sample['pdb_id']}/K36": sample
        for sample in structural.get("samples", ())
        if type(sample) is dict and sample.get("ligand_component_id") == "K36"
    }
    if set(structural_by_identity) != set(K36_IDENTITY_BY_EVENT_V1.values()):
        _fail("K36_STRUCTURAL_POPULATION_INVALID")
    for event_id in K36_EVENT_IDS_V1:
        identity = K36_IDENTITY_BY_EVENT_V1[event_id]
        sample = structural_by_identity[identity]
        pdb_id = str(sample["pdb_id"])
        relative = f"rcsb/structures/{pdb_id}.cif.gz"
        payload, binding = _read_cache_payload(repo, cache_entries, relative)
        cache_bindings.append(binding)
        try:
            text = gzip.decompress(payload).decode("utf-8", "replace")
        except (OSError, EOFError) as error:
            raise _ClosureInvariantError("K36_CACHE_MMCIF_INVALID:" + identity) from error
        protein_label_asym_id = str(
            sample["explicit_event"]["protein_endpoint"]["label_asym_id"]
        )
        evidence = bulk_owner.build_source_local_leakage_evidence_v1(
            mmcif_text=text,
            protein_label_asym_id=protein_label_asym_id,
            ccd=ccd,
        )
        if evidence.get("complete") is not True:
            _fail("K36_LEAKAGE_EVIDENCE_INCOMPLETE:" + identity)
        outcomes.append({
            "canonical_event_id": event_id,
            "pdb_id": pdb_id,
            "ligand_component_id": "K36",
            "structural_processing": {"leakage_evidence": evidence},
            "stage_statuses": {bulk_owner.BULK_STAGES[11]: "UNASSIGNED_READ_ONLY"},
            "terminal_outcome": "CURRENT_RUNTIME_MODEL_USABLE_SPLIT_PENDING",
            "terminal_reasons": [],
        })
    bulk_owner.apply_leakage_predictions_read_only_v1(
        outcomes, historical=set(), context=context
    )
    by_event = {str(outcome["canonical_event_id"]): outcome for outcome in outcomes}
    if set(by_event) != set(RUNTIME_TARGET_EVENT_IDS_V1[3:]) | set(K36_EVENT_IDS_V1):
        _fail("TARGET_LEAKAGE_POPULATION_INVALID")
    for event_id, outcome in by_event.items():
        if (
            outcome.get("leakage_classification")
            not in {"HISTORICAL_BASELINE_COMPONENT", "SAME_EXISTING_EXPANSION_COMPONENT", "NEW_EXPANSION_COMPONENT"}
            or not outcome.get("leakage_key")
            or not outcome.get("predicted_group_id")
            or outcome.get("predicted_split") not in _SPLITS_V1
        ):
            _fail("TARGET_LEAKAGE_SPLIT_NOT_CLOSED:" + event_id)
    return by_event, cache_bindings


def validate_leakage_split_rows_v1(rows: object) -> None:
    """Validate frozen assignments, group atomicity, and admission separation."""

    try:
        if type(rows) not in (list, tuple) or len(rows) != 37:
            _fail("SPLIT_ROWS_POPULATION_INVALID")
        values = [dict(row) for row in rows]
        if len({row.get("canonical_event_id") for row in values}) != 37:
            _fail("SPLIT_ROWS_IDENTITY_DUPLICATE")
        group_splits: dict[str, set[str]] = {}
        for row in values:
            event_id = row.get("canonical_event_id")
            before_authoritative = row.get("formal_split_authoritative_before") == "true"
            after_authoritative = row.get("formal_split_authoritative_after") == "true"
            before_split = row.get("formal_split_before", "")
            after_split = row.get("formal_split_after", "")
            runtime_after = row.get("current_runtime_model_usable_after") == "true"
            if before_authoritative and (
                after_authoritative is not True or after_split != before_split
            ):
                _fail("EXISTING_SPLIT_CHANGED")
            if after_split and (after_split not in _SPLITS_V1 or not after_authoritative):
                _fail("SPLIT_WITHOUT_FORMAL_AUTHORITY")
            expected_membership = "1" if after_split else "0"
            if row.get("split_membership_count") != expected_membership:
                _fail("TRAIN_VALIDATION_TEST_OVERLAP")
            if after_authoritative and not runtime_after:
                _fail("RUNTIME_INCOMPLETE_EVENT_SPLIT_ADMITTED")
            if event_id == AJ3_EVENT_ID_V1 and (after_authoritative or after_split):
                _fail("AJ3_SPLIT_ADMITTED")
            if event_id in K36_EVENT_IDS_V1 and after_split == "train" and not after_authoritative:
                _fail("K36_CALLED_TRAIN_WITHOUT_FORMAL_SPLIT")
            if (
                row.get("leakage_classification") == "NEW_EXPANSION_COMPONENT"
                and row.get("assignment_policy")
                != "PUBLISHED_GENERIC_ADDITIVE_COMPONENT_LEVEL_SPLIT_POLICY"
            ):
                _fail("NEW_COMPONENT_ARBITRARILY_ASSIGNED_SPLIT")
            group_id = row.get("leakage_group_id_after", "")
            if after_authoritative:
                if not group_id:
                    _fail("FORMAL_SPLIT_GROUP_MISSING")
                group_splits.setdefault(group_id, set()).add(after_split)
            training_ready = row.get("training_admission_readiness") == "FORMAL_TRAIN_ADMITTED"
            if training_ready != bool(runtime_after and after_authoritative and after_split == "train"):
                _fail("TRAINING_ADMISSION_CONJUNCTION_VIOLATED")
        if any(len(splits) != 1 for splits in group_splits.values()):
            _fail("CROSS_SPLIT_LEAKAGE_GROUP")
    except Exception as error:
        _public_error(error)


def _existing_group_maps(
    repo: Path,
    records: Sequence[Mapping[str, Any]],
) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in _read_csv(repo / BATCH13_INDEX_V1):
        result[row["canonical_event_id"]] = row["formal_leakage_group_id"]
    split_by_identity = {
        row["sample_index_row_id"]: row for row in _read_csv(repo / CURRENT11_SPLIT_V1)
    }
    for record in records:
        if record["lineage_id"] == "EXACT16_CURRENT11_STRICT_LINKER_LINEAGE":
            result[str(record["canonical_event_id"])] = split_by_identity[
                str(record["sample_identity"])
            ]["final_leakage_group_id"]
    for event_id, (_identity, materialized, _tensorized) in EXACT3_SPECS_V1.items():
        result[event_id] = str(_read_json(repo / materialized)["leakage_group_id"])
    census_by_event = {
        row["canonical_event_id"]: row for row in _read_csv(repo / CENSUS_V1)
    }
    for event_id in (*RUNTIME_TARGET_EVENT_IDS_V1[3:], AJ3_EVENT_ID_V1):
        result[event_id] = census_by_event[event_id]["leakage_group_id"]
    return result


def _runtime_row(sample: RuntimeClosedSampleV1) -> dict[str, str]:
    payload = sample.payload
    roles = payload["roles"]
    supervision = sample.supervision
    shape_map = {
        field.name: list(getattr(supervision, field.name).shape)
        for field in fields(supervision)
    }
    dtype_map = {
        field.name: str(getattr(supervision, field.name).dtype)
        for field in fields(supervision)
    }
    return {
        "canonical_event_id": sample.canonical_event_id,
        "sample_identity": sample.sample_identity,
        "runtime_binding_status": "CURRENT_RUNTIME_BINDING_CLOSED",
        "mapping_method": str(payload["mapping_method"]),
        "role_profile": str(payload["role_profile"]),
        "valid_task_ids_json": _json_cell(payload["valid_task_ids"]),
        "scaffold_atom_count": str(len(roles["scaffold_atom_ids"])),
        "linker_atom_count": str(len(roles["linker_atom_ids"])),
        "warhead_atom_count": str(len(roles["warhead_atom_ids"])),
        "role_partition_sha256": _sha256(_json_bytes(roles)),
        "ligand_atom_count": str(payload["ligand_atom_count"]),
        "pocket_atom_count": str(payload["pocket_atom_count"]),
        "ligand_coordinates_sha256": _tensor_sha(payload["ligand_coordinates"]),
        "pocket_coordinates_sha256": _tensor_sha(payload["pocket_coordinates"]),
        "ligand_feature_channels_sha256": _sha256(_json_bytes(payload["ligand_channels"])),
        "pocket_feature_channels_sha256": _sha256(_json_bytes(payload["pocket_channels"])),
        "ligand_source_row_indices_sha256": _sha256(_json_bytes(payload["ligand_source_row_indices"])),
        "pocket_source_row_indices_sha256": _sha256(_json_bytes(payload["pocket_source_row_indices"])),
        "ligand_parser_local_indices_sha256": _sha256(_json_bytes(payload["ligand_parser_local_indices"])),
        "pocket_parser_local_indices_sha256": _sha256(_json_bytes(payload["pocket_parser_local_indices"])),
        "ligand_reactive_atom_id": str(payload["ligand_reactive_atom_id"]),
        "positive_reactive_pair_indices_json": _json_cell(payload["positive_reactive_pair_indices"]),
        "target_residue_member_count": str(len(payload["target_residue_member_indices"])),
        "target_reactive_pocket_local_index": str(payload["target_reactive_pocket_local_index"]),
        "POST_distance_angstrom": format(float(payload["POST_distance_angstrom"]), ".6f"),
        "POST_geometry_authoritative": "true",
        "PRE_geometry_authoritative": "false",
        "PRE_loss_eligible": "false",
        "PRE_distance_angstrom": "",
        "current_model_input_fields_json": _json_cell(_MODEL_INPUT_FIELDS_V1),
        "current_supervision_dataclass_field_count": str(len(_DATACLASS_FIELDS_V1)),
        "current_supervision_dataclass_fields_json": _json_cell(_DATACLASS_FIELDS_V1),
        "supervision_field_shapes_json": _json_cell(shape_map),
        "supervision_field_dtypes_json": _json_cell(dtype_map),
        "authority_sources_json": _json_cell(payload["authority_sources"]),
        "failure_reasons_json": "[]",
    }


def _build_global_rows(
    repo: Path,
    records: Sequence[Mapping[str, Any]],
    prediction_by_event: Mapping[str, Mapping[str, Any]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    group_before = _existing_group_maps(repo, records)
    runtime_target_set = set(RUNTIME_TARGET_EVENT_IDS_V1)
    new_split_targets = set(RUNTIME_TARGET_EVENT_IDS_V1[3:]) | set(K36_EVENT_IDS_V1)
    leakage_rows: list[dict[str, str]] = []
    index_rows: list[dict[str, str]] = []
    for record in sorted(records, key=lambda value: str(value["canonical_event_id"])):
        event_id = str(record["canonical_event_id"])
        runtime_before = record["current_runtime_model_usable"] is True
        runtime_after = runtime_before or event_id in runtime_target_set
        before_authoritative = record["formal_split_authoritative"] is True
        before_split = str(record["formal_split"])
        before_group = group_before.get(event_id, "")
        prediction = prediction_by_event.get(event_id)
        if event_id in new_split_targets:
            if prediction is None:
                _fail("NEW_SPLIT_TARGET_PREDICTION_MISSING:" + event_id)
            after_authoritative = True
            after_split = str(prediction["predicted_split"])
            after_group = str(prediction["predicted_group_id"])
            classification = str(prediction["leakage_classification"])
            leakage_key = str(prediction["leakage_key"])
            leakage_complete = "true"
            assignment_policy = "PUBLISHED_GENERIC_ADDITIVE_COMPONENT_LEVEL_SPLIT_POLICY"
            split_status = "FORMAL_SPLIT_CLOSED"
        elif before_authoritative:
            after_authoritative = True
            after_split = before_split
            after_group = before_group
            classification = "FROZEN_EXISTING_AUTHORITATIVE_GROUP"
            leakage_key = before_group
            leakage_complete = "true"
            assignment_policy = "FROZEN_EXISTING_ASSIGNMENT"
            split_status = "FROZEN_FORMAL_SPLIT_PRESERVED"
        else:
            after_authoritative = False
            after_split = ""
            after_group = before_group
            classification = "RUNTIME_INCOMPLETE_NOT_SPLIT_ADMITTED"
            leakage_key = ""
            leakage_complete = "false"
            assignment_policy = "NO_ASSIGNMENT_RUNTIME_INCOMPLETE"
            split_status = "FORMAL_SPLIT_NOT_AUTHORIZED"
        training_ready = (
            "FORMAL_TRAIN_ADMITTED"
            if runtime_after and after_authoritative and after_split == "train"
            else (
                "FORMAL_NONTRAIN_SPLIT_MEMBER"
                if runtime_after and after_authoritative
                else (
                    "RUNTIME_USABLE_WITHOUT_FORMAL_SPLIT"
                    if runtime_after else "RUNTIME_BINDING_INCOMPLETE"
                )
            )
        )
        exclusion = (
            "EVENT_TRAINING_USE_DECISION_INCOMPLETE|"
            "ROLE_AND_REACTIVE_PAIR_HUMAN_AUTHORITY_INCOMPLETE|"
            "CURRENT_RUNTIME_TENSORIZATION_AND_SUPERVISION_BINDING_NOT_PUBLISHED"
            if event_id == AJ3_EVENT_ID_V1 else ""
        )
        leakage_rows.append({
            "canonical_event_id": event_id,
            "sample_identity": str(record["sample_identity"]),
            "lineage_id": str(record["lineage_id"]),
            "current_runtime_model_usable_before": str(runtime_before).lower(),
            "current_runtime_model_usable_after": str(runtime_after).lower(),
            "leakage_evidence_complete": leakage_complete,
            "leakage_classification": classification,
            "leakage_key": leakage_key,
            "leakage_group_id_before": before_group,
            "leakage_group_id_after": after_group,
            "formal_split_authoritative_before": str(before_authoritative).lower(),
            "formal_split_before": before_split,
            "formal_split_authoritative_after": str(after_authoritative).lower(),
            "formal_split_after": after_split,
            "split_membership_count": "1" if after_split else "0",
            "split_closure_status": split_status,
            "assignment_policy": assignment_policy,
            "training_admission_readiness": training_ready,
            "exclusion_reason": exclusion,
        })
        index_rows.append({
            "canonical_event_id": event_id,
            "sample_identity": str(record["sample_identity"]),
            "lineage_id": str(record["lineage_id"]),
            "positive_authority_status": (
                "FULL_POSITIVE_SUPERVISION_AUTHORITY"
                if record["role_label_authoritative"]
                and record["reactive_pair_authoritative"]
                and record["POST_geometry_authoritative"]
                else "TASK_RELEVANCE_ONLY_INCOMPLETE"
            ),
            "role_authority_status": "authoritative" if record["role_label_authoritative"] else "incomplete",
            "reactive_pair_authority_status": "authoritative" if record["reactive_pair_authoritative"] else "incomplete",
            "POST_authority_status": "authoritative" if record["POST_geometry_authoritative"] else "incomplete",
            "PRE_authority_status": "unavailable_not_loss_eligible",
            "runtime_binding_status": (
                "CURRENT_RUNTIME_BINDING_CLOSED"
                if runtime_after else "CURRENT_RUNTIME_BINDING_INCOMPLETE"
            ),
            "current_runtime_model_usable": str(runtime_after).lower(),
            "leakage_group_id": after_group,
            "formal_split_authoritative": str(after_authoritative).lower(),
            "formal_split": after_split,
            "training_admission_readiness": training_ready,
            "exclusion_reason": exclusion,
        })
    validate_leakage_split_rows_v1(leakage_rows)
    return leakage_rows, index_rows


def _validate_counts_and_computation(
    computation: ExistingPositiveRuntimeSplitClosureComputationV1,
) -> None:
    counts = dict(computation.counts)
    expected = {
        "published_positive_authority_event_count_before": 37,
        "full_positive_supervision_event_count_before": 36,
        "current_runtime_model_usable_event_count_before": 29,
        "full_supervision_runtime_incomplete_event_count_before": 7,
        "task_relevance_only_incomplete_event_count_before": 1,
        "runtime_binding_target_event_count": 7,
        "runtime_binding_closed_event_count": 7,
        "runtime_binding_remaining_incomplete_event_count": 0,
        "current_runtime_model_usable_event_count_after": 36,
        "K36_runtime_usable_event_count": 5,
        "K36_formal_split_closed_event_count": 5,
        "K36_formal_split_remaining_unassigned_count": 0,
        "newly_runtime_bound_formal_split_closed_event_count": 7,
        "current_runtime_model_usable_without_formal_split_count_after": 0,
        "formal_training_split_admitted_positive_count_after": 14,
        "formal_validation_split_positive_count_after": 8,
        "formal_test_split_positive_count_after": 14,
        "remaining_positive_but_runtime_incomplete_count": 1,
    }
    if counts != expected:
        _fail("AFTER_COUNT_RECONCILIATION_FAILED")
    if (
        len(computation.runtime_samples) != 7
        or len(computation.runtime_binding_rows) != 7
        or len(computation.leakage_split_rows) != 37
        or len(computation.positive_index_rows) != 37
        or computation.existing_split_assignments_changed is not False
        or computation.cross_split_leakage_group_count != 0
    ):
        _fail("COMPUTATION_POPULATION_OR_SAFETY_INVALID")
    split_by_event = {
        str(row["canonical_event_id"]): row
        for row in computation.leakage_split_rows
    }
    if set(split_by_event) != {
        str(record["canonical_event_id"])
        for record in computation.authority_records_before
    }:
        _fail("TRAINING_ADMISSION_SPLIT_JOIN_POPULATION_INVALID")
    admitted_count = 0
    for sample in computation.runtime_samples:
        row = split_by_event.get(sample.canonical_event_id)
        if row is None:
            _fail("TRAINING_ADMISSION_SPLIT_JOIN_MISSING")
        training_admitted = bool(
            row["current_runtime_model_usable_after"] == "true"
            and row["formal_split_authoritative_after"] == "true"
            and row["formal_split_after"] == "train"
        )
        _validate_training_mask_activation_v1(
            sample.supervision, training_admitted=training_admitted
        )
        admitted_count += int(training_admitted)
    if admitted_count != 1:
        _fail("NEW_EXACT7_TRAINING_ADMISSION_COUNT_INVALID")


def compute_covapie_existing_positive_runtime_and_split_closure_v1(
    *, repository_root: object = None,
) -> ExistingPositiveRuntimeSplitClosureComputationV1:
    """Compute the Exact7 runtime and Exact5 K36 split closure in memory."""

    try:
        repo = Path(__file__).resolve().parents[2] if repository_root is None else repository_root
        if type(repo) is not type(Path()) or not repo.is_absolute() or repo.resolve() != repo:
            _fail("REPOSITORY_ROOT_INVALID")
        fixed_bindings = _require_fixed_inputs(repo)
        summary = _read_json(repo / SCALEUP_SUMMARY_V1)
        manifest = _read_json(repo / SCALEUP_MANIFEST_V1)
        owner_bindings = _verify_audit_owner_bindings(repo, summary)
        audit = summary["global_current_positive_authority_audit"]
        counts_before = audit.get("counts")
        expected_before = {
            "audited_positive_authority_sample_identity_count": 37,
            "audited_positive_authority_canonical_event_count": 37,
            "global_full_event_positive_authority_count": 36,
            "global_task_relevance_only_incomplete_count": 1,
            "global_current_runtime_model_usable_sample_count": 29,
            "global_current_runtime_model_usable_canonical_event_count": 29,
            "global_current_positive_but_runtime_incomplete_count": 8,
            "global_current_runtime_model_usable_without_formal_split_count": 5,
            "formal_training_split_admitted_positive_count": 13,
            "formal_validation_split_positive_count": 6,
            "formal_test_split_positive_count": 5,
            "deduplicated_runtime_canonical_event_overlap_count": 0,
        }
        if counts_before != expected_before:
            _fail("PUBLISHED_BEFORE_COUNTS_DRIFT")
        records = audit.get("records")
        if type(records) is not list or len(records) != 37:
            _fail("PUBLISHED_AUTHORITY_RECORDS_INVALID")
        records_digest = _sha256(_json_bytes(records))
        if records_digest != manifest.get("global_current_authority_audit_bindings", {}).get("audit_records_sha256"):
            _fail("PUBLISHED_AUTHORITY_RECORD_DIGEST_DRIFT")
        audit_by_event = {str(record["canonical_event_id"]): record for record in records}
        derived_exact7 = tuple(sorted(
            event_id for event_id, record in audit_by_event.items()
            if record["positive_authority_exists"] is True
            and record["role_label_authoritative"] is True
            and record["reactive_pair_authoritative"] is True
            and record["POST_geometry_authoritative"] is True
            and record["current_runtime_model_usable"] is False
        ))
        if derived_exact7 != tuple(sorted(RUNTIME_TARGET_EVENT_IDS_V1)):
            _fail("INDEPENDENT_EXACT7_ORACLE_MISMATCH")
        incomplete_only = [
            record for record in records
            if record["positive_authority_exists"] is True
            and not record["role_label_authoritative"]
        ]
        if len(incomplete_only) != 1 or incomplete_only[0]["canonical_event_id"] != AJ3_EVENT_ID_V1:
            _fail("AJ3_INCOMPLETE_ORACLE_MISMATCH")

        canonical = _read_json(repo / CANONICAL_EVENTS_V1)
        canonical_by_event = {
            str(event["canonical_event_id"]): event for event in canonical.get("canonical_events", ())
        }
        if not set(RUNTIME_TARGET_EVENT_IDS_V1) <= set(canonical_by_event):
            _fail("CANONICAL_EVENT_SOURCE_COVERAGE_MISSING")
        first500 = _read_json(repo.parent / FIRST500_VIEW_RELATIVE_V1)
        first500_by_event = {
            str(item["processing_outcome"]["canonical_event_id"]): item["processing_outcome"]
            for item in first500.get("events", ())
        }
        if not set(RUNTIME_TARGET_EVENT_IDS_V1[3:]) <= set(first500_by_event):
            _fail("FIRST500_TARGET_STRUCTURAL_OUTCOME_MISSING")
        cache_entries = _cache_payload_entries(repo)

        payloads = _exact3_payloads(repo, audit_by_event, canonical_by_event)
        human_payloads, human_cache_bindings = _human_exact4_payloads(
            repo, audit_by_event, canonical_by_event, first500_by_event, cache_entries
        )
        payloads.extend(human_payloads)
        if tuple(payload["canonical_event_id"] for payload in payloads) != RUNTIME_TARGET_EVENT_IDS_V1:
            _fail("RUNTIME_PAYLOAD_ORDER_OR_COVERAGE_INVALID")
        predictions, split_cache_bindings = _target_leakage_predictions_v1(
            repo,
            first500_by_event=first500_by_event,
            cache_entries=cache_entries,
            audit_by_event=audit_by_event,
        )
        leakage_rows, index_rows = _build_global_rows(repo, records, predictions)
        split_by_event = {
            str(row["canonical_event_id"]): row for row in leakage_rows
        }
        runtime_samples: list[RuntimeClosedSampleV1] = []
        for payload in payloads:
            event_id = str(payload["canonical_event_id"])
            split_row = split_by_event.get(event_id)
            if split_row is None:
                _fail("RUNTIME_TARGET_FINAL_SPLIT_MISSING:" + event_id)
            training_admitted = bool(
                split_row["current_runtime_model_usable_after"] == "true"
                and split_row["formal_split_authoritative_after"] == "true"
                and split_row["formal_split_after"] == "train"
            )
            for task_id in payload["valid_task_ids"]:
                _model_batch_and_supervision(
                    payload,
                    task_id=task_id,
                    training_admitted=training_admitted,
                )
            model_batch, supervision = _model_batch_and_supervision(
                payload, task_id=0, training_admitted=training_admitted
            )
            runtime_samples.append(RuntimeClosedSampleV1(
                canonical_event_id=event_id,
                sample_identity=str(payload["sample_identity"]),
                payload=payload,
                model_input_batch=model_batch,
                supervision=supervision,
            ))
        split_counts = Counter(
            row["formal_split_after"] for row in leakage_rows
            if row["formal_split_authoritative_after"] == "true"
        )
        runtime_after_count = sum(
            row["current_runtime_model_usable_after"] == "true" for row in leakage_rows
        )
        unsplit_after_count = sum(
            row["current_runtime_model_usable_after"] == "true"
            and row["formal_split_authoritative_after"] == "false"
            for row in leakage_rows
        )
        existing_changed = any(
            row["formal_split_authoritative_before"] == "true"
            and (
                row["formal_split_authoritative_after"] != "true"
                or row["formal_split_after"] != row["formal_split_before"]
            )
            for row in leakage_rows
        )
        authoritative_group_splits: dict[str, set[str]] = {}
        for row in leakage_rows:
            if row["formal_split_authoritative_after"] == "true":
                authoritative_group_splits.setdefault(
                    row["leakage_group_id_after"], set()
                ).add(row["formal_split_after"])
        cross_split = sum(len(values) > 1 for values in authoritative_group_splits.values())
        result = ExistingPositiveRuntimeSplitClosureComputationV1(
            source_bindings=tuple(sorted(
                {
                    (str(binding["path"]), str(binding["sha256"])): binding
                    for binding in (
                        *fixed_bindings, *owner_bindings,
                        *human_cache_bindings, *split_cache_bindings,
                    )
                }.values(),
                key=lambda binding: str(binding["path"]),
            )),
            authority_records_before=tuple(records),
            runtime_samples=tuple(runtime_samples),
            runtime_binding_rows=tuple(_runtime_row(sample) for sample in runtime_samples),
            leakage_split_rows=tuple(leakage_rows),
            positive_index_rows=tuple(index_rows),
            counts={
                "published_positive_authority_event_count_before": 37,
                "full_positive_supervision_event_count_before": 36,
                "current_runtime_model_usable_event_count_before": 29,
                "full_supervision_runtime_incomplete_event_count_before": 7,
                "task_relevance_only_incomplete_event_count_before": 1,
                "runtime_binding_target_event_count": 7,
                "runtime_binding_closed_event_count": len(runtime_samples),
                "runtime_binding_remaining_incomplete_event_count": 7 - len(runtime_samples),
                "current_runtime_model_usable_event_count_after": runtime_after_count,
                "K36_runtime_usable_event_count": 5,
                "K36_formal_split_closed_event_count": sum(
                    row["formal_split_authoritative_after"] == "true"
                    for row in leakage_rows if row["canonical_event_id"] in K36_EVENT_IDS_V1
                ),
                "K36_formal_split_remaining_unassigned_count": sum(
                    row["formal_split_authoritative_after"] == "false"
                    for row in leakage_rows if row["canonical_event_id"] in K36_EVENT_IDS_V1
                ),
                "newly_runtime_bound_formal_split_closed_event_count": sum(
                    row["formal_split_authoritative_after"] == "true"
                    for row in leakage_rows if row["canonical_event_id"] in RUNTIME_TARGET_EVENT_IDS_V1
                ),
                "current_runtime_model_usable_without_formal_split_count_after": unsplit_after_count,
                "formal_training_split_admitted_positive_count_after": split_counts["train"],
                "formal_validation_split_positive_count_after": split_counts["validation"],
                "formal_test_split_positive_count_after": split_counts["test"],
                "remaining_positive_but_runtime_incomplete_count": 37 - runtime_after_count,
            },
            existing_split_assignments_changed=existing_changed,
            cross_split_leakage_group_count=cross_split,
        )
        _validate_counts_and_computation(result)
        return result
    except Exception as error:
        _public_error(error)


def build_covapie_existing_positive_runtime_and_split_closure_artifacts_v1(
    *,
    repository_root: object = None,
    computation: ExistingPositiveRuntimeSplitClosureComputationV1 | None = None,
) -> dict[str, bytes]:
    """Serialize the five deterministic successor artifacts."""

    try:
        repo = Path(__file__).resolve().parents[2] if repository_root is None else repository_root
        if type(repo) is not type(Path()) or not repo.is_absolute() or repo.resolve() != repo:
            _fail("REPOSITORY_ROOT_INVALID")
        result = computation or compute_covapie_existing_positive_runtime_and_split_closure_v1(
            repository_root=repo
        )
        _validate_counts_and_computation(result)
        runtime_header = tuple(result.runtime_binding_rows[0])
        leakage_header = tuple(result.leakage_split_rows[0])
        index_header = tuple(result.positive_index_rows[0])
        runtime_payload = _csv_bytes(runtime_header, result.runtime_binding_rows)
        leakage_payload = _csv_bytes(leakage_header, result.leakage_split_rows)
        index_payload = _csv_bytes(index_header, result.positive_index_rows)
        counts = dict(result.counts)
        k36_rows = [
            row for row in result.leakage_split_rows
            if row["canonical_event_id"] in K36_EVENT_IDS_V1
        ]
        new_runtime_rows = [
            row for row in result.leakage_split_rows
            if row["canonical_event_id"] in RUNTIME_TARGET_EVENT_IDS_V1
        ]
        summary = {
            "schema_version": SCHEMA_VERSION_V1,
            "existing_positive_runtime_split_closure_built": True,
            **counts,
            "runtime_binding_outcomes": [
                {
                    "canonical_event_id": row["canonical_event_id"],
                    "status": row["runtime_binding_status"],
                    "role_profile": row["role_profile"],
                    "valid_task_ids": json.loads(row["valid_task_ids_json"]),
                }
                for row in result.runtime_binding_rows
            ],
            "K36_exact5_leakage_status": [
                {
                    "canonical_event_id": row["canonical_event_id"],
                    "classification": row["leakage_classification"],
                    "leakage_group_id": row["leakage_group_id_after"],
                    "formal_split": row["formal_split_after"],
                    "formal_split_authoritative": True,
                }
                for row in k36_rows
            ],
            "newly_runtime_bound_events": [
                {
                    "canonical_event_id": row["canonical_event_id"],
                    "formal_split_authoritative": (
                        row["formal_split_authoritative_after"] == "true"
                    ),
                    "formal_split": row["formal_split_after"],
                    "training_admission_readiness": row["training_admission_readiness"],
                }
                for row in new_runtime_rows
            ],
            "existing_split_assignments_changed": result.existing_split_assignments_changed,
            "cross_split_leakage_group_count": result.cross_split_leakage_group_count,
            "AJ3_status": {
                "canonical_event_id": AJ3_EVENT_ID_V1,
                "promoted": False,
                "runtime_binding_status": "CURRENT_RUNTIME_BINDING_INCOMPLETE",
                "formal_split_authoritative": False,
            },
            "safety": {
                "PRE_geometry_fabricated": False,
                "new_chemistry_authority_created": False,
                "fuzzy_positive_propagation_performed": False,
                "training_performed": False,
                "Trainer_used": False,
                "backward_performed": False,
                "optimizer_created": False,
                "network_performed": False,
                "bulk_ranks1001_1500_processed": False,
                "data_augmentation_performed": False,
                "cumulative1000_rebuild_invoked": False,
                "cumulative1000_replay_invoked": False,
            },
            "artifact_sha256_excluding_manifest_and_summary": {
                RUNTIME_INVENTORY_V1: _sha256(runtime_payload),
                LEAKAGE_INVENTORY_V1: _sha256(leakage_payload),
                POSITIVE_INDEX_V1: _sha256(index_payload),
            },
            "candidate_precommit_profile_contract_supported": True,
            "published_successor_profile_contract_supported": True,
            "ready_for_gpt_review": True,
            "ready_for_publication": True,
            "recommended_next_step_exactly": (
                "gpt_audit_existing_positive_runtime_and_split_closure_then_publish_if_pass"
            ),
        }
        summary_payload = _json_bytes(summary)
        manifest = {
            "schema_version": SCHEMA_VERSION_V1,
            "baseline_HEAD": BASELINE_HEAD_V1,
            "baseline_parent": BASELINE_PARENT_V1,
            "baseline_tree": BASELINE_TREE_V1,
            "baseline_subject": BASELINE_SUBJECT_V1,
            "publication_subject": PUBLICATION_SUBJECT_V1,
            "published_cumulative1000_bindings": {
                relative.as_posix(): digest
                for relative, digest in FIXED_REPOSITORY_INPUT_SHA256_V1.items()
                if relative in {CENSUS_V1, EFFECTIVE_N_V1, SCALEUP_MANIFEST_V1, SCALEUP_SUMMARY_V1}
            },
            "source_bindings": list(result.source_bindings),
            "current_supervision_dataclass": {
                "owner": "src/covalent_ext/covapie_current11_training_tensorizer_v1.py",
                "type": "CovapieCurrent11TrainingSupervisionTensorsV1",
                "field_count": len(_DATACLASS_FIELDS_V1),
                "fields": list(_DATACLASS_FIELDS_V1),
            },
            "leakage_owner": "apply_leakage_predictions_read_only_v1",
            "new_component_split_policy_owner": (
                "assign_expansion_leakage_splits_v1/"
                "conservative_union_final_leakage_group_v1"
            ),
            "output_sha256_excluding_manifest": {
                RUNTIME_INVENTORY_V1: _sha256(runtime_payload),
                LEAKAGE_INVENTORY_V1: _sha256(leakage_payload),
                POSITIVE_INDEX_V1: _sha256(index_payload),
                SUMMARY_V1: _sha256(summary_payload),
            },
            "candidate_boundary": {
                "exact_file_count": 8,
                "paths": sorted(AUTHORIZED_PATHS_V1),
                "candidate_status": "A",
                "mode": "100644",
            },
            "publication_profiles": {
                "candidate_precommit_untracked": {
                    "HEAD": BASELINE_HEAD_V1,
                    "untracked": sorted(AUTHORIZED_PATHS_V1),
                    "tracked_modifications": [],
                    "staged": [],
                },
                "published_successor": {
                    "single_parent": BASELINE_HEAD_V1,
                    "subject": PUBLICATION_SUBJECT_V1,
                    "changed_paths": sorted(AUTHORIZED_PATHS_V1),
                    "status": "A",
                    "mode": "100644",
                },
            },
            "training_performed": False,
            "network_performed": False,
            "data_augmentation_performed": False,
            "cumulative1000_rebuild_invoked": False,
            "cumulative1000_replay_invoked": False,
        }
        manifest_payload = _json_bytes(manifest)
        return {
            RUNTIME_INVENTORY_V1: runtime_payload,
            LEAKAGE_INVENTORY_V1: leakage_payload,
            POSITIVE_INDEX_V1: index_payload,
            MANIFEST_V1: manifest_payload,
            SUMMARY_V1: summary_payload,
        }
    except Exception as error:
        _public_error(error)


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        temporary.unlink()
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def materialize_covapie_existing_positive_runtime_and_split_closure_artifacts_v1(
    *, repository_root: object = None,
) -> dict[str, str]:
    """Write exactly the five derived outputs; source/checker/tests are separate."""

    try:
        repo = Path(__file__).resolve().parents[2] if repository_root is None else repository_root
        if type(repo) is not type(Path()) or not repo.is_absolute() or repo.resolve() != repo:
            _fail("REPOSITORY_ROOT_INVALID")
        computation = compute_covapie_existing_positive_runtime_and_split_closure_v1(
            repository_root=repo
        )
        artifacts = build_covapie_existing_positive_runtime_and_split_closure_artifacts_v1(
            repository_root=repo, computation=computation
        )
        if tuple(artifacts) != OUTPUT_FILENAMES_V1:
            _fail("OUTPUT_FILENAME_SET_INVALID")
        output_root = repo / OUTPUT_ROOT_RELATIVE_V1
        for name, payload in artifacts.items():
            _atomic_write(output_root / name, payload)
        return {name: _sha256(payload) for name, payload in artifacts.items()}
    except Exception as error:
        _public_error(error)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()


def observe_repository_state_v1(repository_root: Path) -> dict[str, Any]:
    repo = repository_root.resolve()
    changed_entries = []
    for line in _git(
        repo, "diff-tree", "--no-commit-id", "--name-status", "--no-renames", "-r", "HEAD"
    ).splitlines():
        if line:
            status_value, path = line.split("\t", 1)
            changed_entries.append({"status": status_value, "path": path})
    modes = {}
    tree_output = _git(repo, "ls-tree", "-r", "--full-tree", "HEAD", "--", *sorted(AUTHORIZED_PATHS_V1))
    for line in tree_output.splitlines():
        if line:
            metadata, path = line.split("\t", 1)
            mode, object_type, _object_id = metadata.split()
            if object_type == "blob":
                modes[path] = mode
    untracked = [
        value for value in _git(repo, "ls-files", "--others", "--exclude-standard").splitlines()
        if value
    ]
    filesystem_modes = {}
    for relative in untracked:
        path = repo / relative
        if relative in AUTHORIZED_PATHS_V1 and path.is_file():
            filesystem_modes[relative] = format(stat.S_IMODE(path.lstat().st_mode), "04o")
    return {
        "branch": _git(repo, "branch", "--show-current"),
        "HEAD": _git(repo, "rev-parse", "HEAD"),
        "HEAD_parent": _git(repo, "rev-parse", "HEAD^"),
        "head_parent_ids": _git(repo, "show", "-s", "--format=%P", "HEAD").split(),
        "HEAD_tree": _git(repo, "rev-parse", "HEAD^{tree}"),
        "HEAD_subject": _git(repo, "log", "-1", "--format=%s"),
        "origin_main": _git(repo, "rev-parse", "refs/remotes/origin/main"),
        "ahead_behind": _git(repo, "rev-list", "--left-right", "--count", "HEAD...refs/remotes/origin/main").split(),
        "tracked_changes": [value for value in _git(repo, "diff", "--name-only").splitlines() if value],
        "staged_changes": [value for value in _git(repo, "diff", "--cached", "--name-only").splitlines() if value],
        "untracked": untracked,
        "head_changed_entries": changed_entries,
        "head_candidate_path_modes": modes,
        "candidate_filesystem_modes": filesystem_modes,
    }


def _classify_repository_profile_impl_v1(observation: Mapping[str, Any]) -> str:
    """Accept exactly candidate-precommit-untracked or published-successor."""

    common = (
        observation.get("branch") == "main"
        and observation.get("ahead_behind") == ["0", "0"]
        and observation.get("tracked_changes") == []
        and observation.get("staged_changes") == []
    )
    if not common:
        _fail("REPOSITORY_PROFILE_COMMON_STATE_INVALID")
    candidate = (
        observation.get("HEAD") == BASELINE_HEAD_V1
        and observation.get("HEAD_parent") == BASELINE_PARENT_V1
        and observation.get("HEAD_tree") == BASELINE_TREE_V1
        and observation.get("HEAD_subject") == BASELINE_SUBJECT_V1
        and observation.get("origin_main") == BASELINE_HEAD_V1
        and set(observation.get("untracked", ())) == set(AUTHORIZED_PATHS_V1)
        and set(observation.get("candidate_filesystem_modes", ())) == set(AUTHORIZED_PATHS_V1)
        and all(
            mode in {"0644", "0664"}
            for mode in observation.get("candidate_filesystem_modes", {}).values()
        )
    )
    if candidate:
        return "candidate_precommit_untracked"
    published_entries = observation.get("head_changed_entries")
    published = (
        observation.get("HEAD") == observation.get("origin_main")
        and observation.get("HEAD") != BASELINE_HEAD_V1
        and observation.get("head_parent_ids") == [BASELINE_HEAD_V1]
        and observation.get("HEAD_subject") == PUBLICATION_SUBJECT_V1
        and observation.get("untracked") == []
        and type(published_entries) is list
        and len(published_entries) == 8
        and {entry.get("path") for entry in published_entries} == set(AUTHORIZED_PATHS_V1)
        and all(entry.get("status") == "A" for entry in published_entries)
        and observation.get("head_candidate_path_modes")
        == {path: "100644" for path in AUTHORIZED_PATHS_V1}
    )
    if published:
        return "published_successor"
    _fail("REPOSITORY_PROFILE_NOT_RECOGNIZED")


def classify_repository_profile_v1(observation: Mapping[str, Any]) -> str:
    try:
        return _classify_repository_profile_impl_v1(observation)
    except Exception as error:
        _public_error(error)


def _candidate_precommit_profile_passed_v1(repository_profile: object) -> bool:
    """Return the candidate marker value for an already classified real profile."""

    try:
        if repository_profile not in {
            "candidate_precommit_untracked",
            "published_successor",
        }:
            _fail("CANDIDATE_PROFILE_MARKER_INPUT_INVALID")
        return repository_profile == "candidate_precommit_untracked"
    except Exception as error:
        _public_error(error)
