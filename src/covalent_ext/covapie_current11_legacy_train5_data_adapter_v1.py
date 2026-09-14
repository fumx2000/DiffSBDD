"""Source-bound CPU data adapter for the five legacy Current11 train events.

The adapter reuses the published Current11 Task2 runtime, machine/human
authority, supervision materializer, scheduler, and mixed-profile tensorizer.
It performs no model, Trainer, optimizer, checkpoint, or parameter operation.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import stat
import struct
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, NoReturn, Sequence

import numpy as np
import torch

from covalent_ext import (
    covapie_current11_role_seed_human_gold_ingestion_compiler_v1
    as _human_compiler,
)
from covalent_ext import (
    covapie_current11_task2_lightning_runtime_integration_v1
    as _runtime_integration,
)
from covalent_ext import (
    covapie_current11_trainable_supervision_materializer_v1 as _materializer,
)
from covalent_ext import (
    covapie_expanded_cys_sg_mixed_profile_tensorizer_v1 as _mixed_tensorizer,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CANONICAL_TASKS_V1,
    canonical_task_id_for_covapie_current11_sample_v1,
)


__all__ = (
    "ADAPTER_ERROR_V1",
    "CANONICAL_TARGETS_V1",
    "CovapieCurrent11LegacyTrain5PreparedV1",
    "SourceBindingV1",
    "prepare_covapie_current11_legacy_train5_data_adapter_v1",
    "tensorize_covapie_current11_legacy_train5_epoch_v1",
)


ADAPTER_ERROR_V1 = "COVAPIE_CURRENT11_LEGACY_TRAIN5_DATA_ADAPTER_V1_ERROR"
ADAPTER_SCHEMA_V1 = "covapie_current11_legacy_train5_data_adapter_v1"
TARGET_LEAKAGE_GROUP_V1 = "COVAPIE_LEAKAGE_GROUP_000004"
CANONICAL_TARGETS_V1 = (
    (
        "CYS_SG_SAMPLE_INDEX_000006",
        "COVAPIE_CYS_SG_EVENT_V1:1AU3:A:CYS:25-:SG:B:PCM:C22",
        "1AU3",
        "PCM",
        "C22",
    ),
    (
        "CYS_SG_SAMPLE_INDEX_000007",
        "COVAPIE_CYS_SG_EVENT_V1:1AU4:A:CYS:25-:SG:B:INP:C17",
        "1AU4",
        "INP",
        "C17",
    ),
    (
        "CYS_SG_SAMPLE_INDEX_000008",
        "COVAPIE_CYS_SG_EVENT_V1:1AYU:A:CYS:25-:SG:B:INA:C21",
        "1AYU",
        "INA",
        "C21",
    ),
    (
        "CYS_SG_SAMPLE_INDEX_000009",
        "COVAPIE_CYS_SG_EVENT_V1:1AYV:A:CYS:25-:SG:B:IN6:C21",
        "1AYV",
        "IN6",
        "C21",
    ),
    (
        "CYS_SG_SAMPLE_INDEX_000010",
        "COVAPIE_CYS_SG_EVENT_V1:1AYW:A:CYS:25-:SG:B:IN3:C21",
        "1AYW",
        "IN3",
        "C21",
    ),
)

_CURRENT11_SAMPLE_ORDER = tuple(
    f"CYS_SG_SAMPLE_INDEX_{index:06d}" for index in range(1, 12)
)
_EXPECTED_CANONICAL_TASKS = (
    (0, "warhead_only", "A", (2,)),
    (1, "linker_plus_warhead", "B", (1, 2)),
    (2, "scaffold_plus_warhead", "B2", (0, 2)),
    (3, "scaffold_only", "B3", (0,)),
    (4, "scaffold_plus_linker_plus_warhead", "C", (0, 1, 2)),
)
_SIDECAR_FIELD = "covapie_current11_task2_runtime_result_v1"
_SEAL_DOMAIN = b"COVAPIE_CURRENT11_LEGACY_TRAIN5_DATA_ADAPTER_V1\0"
_CONSTRUCTION_TOKEN = object()

_LEAKAGE_INDEX = (
    "data/derived/covalent_small/"
    "covapie_existing_positive_runtime_and_split_closure_v1/"
    "covapie_existing_positive_leakage_split_closure_inventory_v1.csv"
)
_POSITIVE_INDEX = (
    "data/derived/covalent_small/"
    "covapie_existing_positive_runtime_and_split_closure_v1/"
    "covapie_current_runtime_model_usable_positive_index_v1.csv"
)
_CLOSURE_MANIFEST = (
    "data/derived/covalent_small/"
    "covapie_existing_positive_runtime_and_split_closure_v1/"
    "covapie_existing_positive_runtime_and_split_closure_manifest_v1.json"
)
_CURRENT11_INDEX = (
    "data/derived/covalent_small/"
    "covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0/"
    "unified_sample_index.csv"
)
_CURRENT11_SPLIT = (
    "data/derived/covalent_small/"
    "covapie_unified_leakage_split_materialization_smoke_v0/"
    "covapie_sample_split_assignment.csv"
)
_CURRENT11_GROUP = (
    "data/derived/covalent_small/"
    "covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0/"
    "covapie_final_leakage_group_assignment.csv"
)
_FEATURE_RESOLUTION_MANIFEST = (
    "data/derived/covalent_small/"
    "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1/"
    "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_manifest.json"
)
_FINAL_FEATURE_AUDIT_MANIFEST = (
    "data/derived/covalent_small/"
    "covapie_final_training_feature_semantics_and_unknown_atom_policy_audit_v1/"
    "covapie_final_training_feature_semantics_and_unknown_atom_policy_audit_manifest.json"
)
_CARRIER = (
    "formal-sidecars/current11-runtime-sample-and-role-order-carrier-v1/"
    "current11_runtime_sample_and_role_order_carrier.npz"
)
_CARRIER_BINDING = (
    "formal-sidecars/current11-runtime-sample-and-role-order-carrier-v1/"
    "current11_runtime_sample_and_role_order_carrier_binding_report.json"
)


@dataclass(frozen=True)
class SourceBindingV1:
    """One immutable direct-source identity used by the adapter."""

    root: str
    relative_path: str
    byte_count: int
    sha256: str


_DIRECT_SOURCE_BINDINGS = (
    SourceBindingV1("repository", _LEAKAGE_INDEX, 16053, "2f673a8ca76217af1517d8254de79799d4fea333d9892af13a3ab0eeb90d8259"),
    SourceBindingV1("repository", _POSITIVE_INDEX, 13511, "5485305a750129e437ef68b43c758f9f0586add41fe54ee1d621b6c5bde62410"),
    SourceBindingV1("repository", _CLOSURE_MANIFEST, 17242, "5a94d4a35a0cc7b5495175bd4e94e26ab2a8ba796ed59ea1e1e4695575936944"),
    SourceBindingV1("repository", _CURRENT11_INDEX, 14340, "d610e7171ad976f16055584582335ce756ed0210e6c15d6b55a1a234bc92c326"),
    SourceBindingV1("repository", _CURRENT11_SPLIT, 2412, "29ffff244e33e3ec93f2c2b3e5e42a09ce73d7f55019f833e97659301f6a388c"),
    SourceBindingV1("repository", _CURRENT11_GROUP, 6316, "768c964f22e19a8fb6232b1fa26c531e53d023042abcd9b1bcca44df2b4f4416"),
    SourceBindingV1("repository", "data/derived/covalent_small/covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_evidence_validation_v1/covapie_atom_pair_atom_table_mapping_validation_matrix.csv", 13364, "9f26b25ed11d186a02a1f859de10a105605ce3af13805ac5a4be1ad73199df45"),
    SourceBindingV1("repository", "data/derived/covalent_small/covapie_role_annotation_input_authority_gap_resolution_v1/covapie_current11_role_input_authority_matrix.csv", 7510, "fc7897121bf216488c239ecd2ad678bc23501f72db1fea85212b083c5af7b06b"),
    SourceBindingV1("repository", "data/derived/covalent_small/covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1/covapie_current11_family_rule_authority_binding_matrix.csv", 7826, "7064c1d0153ba1399bfdae8affcf21ead3f27e8a933987cd025ba5101a92bb61"),
    SourceBindingV1("repository", "data/derived/covalent_small/covapie_independent_group_expansion_batch_independence_evidence_materialization_smoke_v0/covapie_ligand_graph_scaffold_evidence.csv", 11271, "982a9f89a89d3a4ad6a3e468cfd16d2fdfd5435cbf6d593e086fbd7fadd3ec73"),
    SourceBindingV1("repository", _FEATURE_RESOLUTION_MANIFEST, 6395, "24cb60ca4f080a72e8c60aef63d105d82ec2f432eecc9b90f3341f52576bb6e0"),
    SourceBindingV1("repository", _FINAL_FEATURE_AUDIT_MANIFEST, 4721, "8e9aa9e853556715f1f6920b6bb80c1aa0ab22344b4118ba63f988d0ae659dbe"),
    SourceBindingV1("repository", "src/covalent_ext/covapie_current11_task2_batch_index_remap_adapter_context_v1.py", 43578, "1eb764aa4425ad857d59daa625e610a5e015a0a272594f332254998bed8191e6"),
    SourceBindingV1("repository", "src/covalent_ext/covapie_current11_task2_lightning_runtime_integration_v1.py", 5020, "40b997b48ccaa7483532dc2404c443c43536a9b3e676cac78489e38cd7a9661c"),
    SourceBindingV1("repository", "src/covalent_ext/covapie_current11_trainable_supervision_materializer_v1.py", 68393, "0dddcb645dc26eacc864fa2c6b59db5cbd34ed2da3e8bf7abb26d5daee9672ff"),
    SourceBindingV1("repository", "src/covalent_ext/covapie_current11_role_seed_human_gold_ingestion_compiler_v1.py", 13749, "066ddd0b7c31e3795adab63a929492deaa4510e9b6e2bec7d0aa57065694d382"),
    SourceBindingV1("repository", "src/covalent_ext/covapie_current11_training_tensorizer_v1.py", 39144, "9fdc3f7f101fab5e5e5452e3d8e9f9b0b1e6e5fa8254a261f36310a1dfd0b606"),
    SourceBindingV1("repository", "src/covalent_ext/covapie_expanded_cys_sg_mixed_profile_tensorizer_v1.py", 58048, "c95bac177ba2ef1dd519bb5659cb97a8367484b1e41553be56fe3b2789ceb932"),
    SourceBindingV1("repository", "src/covalent_ext/covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1.py", 64861, "1d80862e7c4fa3215ac3f307a45ce3bc8f1e0d4613728133a0ea3118df2df241"),
    SourceBindingV1("state", _CARRIER, 196172, "ea3aa7c94b7c88993493662ad6ba7fd95e547ec62612a072f8248a515657e910"),
    SourceBindingV1("state", _CARRIER_BINDING, 1654, "596d0b2d5464942b21ca1379c1458de750c786f1d990114c72f0f1aee4586fc0"),
    SourceBindingV1("state", "manual-review-aids/current11-trainable-supervision-role-seed-v1/current11_role_seed_review_decisions.csv", 361892, "104cc3ec5c9cf6a250f07348695c0a52ca938ed3be082a61e4a983e6f1359ae4"),
    SourceBindingV1("state", "manual-review/covapie_current11_target_residue_atom_condition_authority_bundle_v1.json", 12964, "a95ae52e091a7117b241269eebd891f3ee97e3ae4a6b4e14fa441ab6a1ed2096"),
    SourceBindingV1("state", "manual-review/covapie_current11_pocket_atom_identity_alignment_bundle_v1.json", 56971, "7f80a810ff35c4ea5d61262021379767a4d15202badd8ec6a6b846405147d842"),
    SourceBindingV1("state", "manual-review/covapie_current11_unified_effective_authority_view_v1.json", 32639, "f4178987f3c3eed0e248f6d3d5f22cb8bce1839d39ab08aff0bff9d2ef9f3774"),
    SourceBindingV1("state", "formal-sidecars/current11-dataset-partial-supervision-routing-sidecar-v1/current11_dataset_partial_supervision_routing_records.csv", 69557, "751e32f46ab386604386167bdffd38f762472bbc9fdff4af7167a979ac68af03"),
    SourceBindingV1("state", "formal-sidecars/current11-dataset-partial-supervision-routing-sidecar-v1/current11_dataset_partial_supervision_routing_manifest.json", 43109, "3a2c2e8170f20ed0a8ea97798a5945ec846cd36d81fe950aa58fee6311984a7d"),
)


class _AdapterInvariantError(Exception):
    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def _fail(reason: str) -> NoReturn:
    raise _AdapterInvariantError(reason)


def _public_error(error: Exception) -> NoReturn:
    if type(error) is ValueError and str(error).startswith(ADAPTER_ERROR_V1):
        raise error
    reason = error.reason if isinstance(error, _AdapterInvariantError) else "OWNER_OR_SOURCE_FAILURE"
    raise ValueError(f"{ADAPTER_ERROR_V1}:{reason}") from error


def _root(value: object, *, reason: str) -> Path:
    if not isinstance(value, (str, Path)) or isinstance(value, bool):
        _fail(reason)
    path = Path(value)
    if not path.is_absolute():
        _fail(reason)
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise _AdapterInvariantError(reason) from error
    if resolved != path or not path.is_dir():
        _fail(reason)
    return path


def _roots(repository_root: object, state_root: object) -> tuple[Path, Path]:
    repository = _root(repository_root, reason="REPOSITORY_ROOT_INVALID")
    state = _root(state_root, reason="STATE_ROOT_INVALID")
    if state != repository.parent / "covapie-state":
        _fail("ROOT_RELATIONSHIP_INVALID")
    return repository, state


def _git_head_bytes(repository: Path, relative_path: str) -> bytes:
    try:
        result = subprocess.run(
            ("git", "show", f"HEAD:{relative_path}"),
            cwd=repository,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as error:
        raise _AdapterInvariantError("REPOSITORY_SOURCE_NOT_PUBLISHED") from error
    if result.returncode != 0:
        _fail("REPOSITORY_SOURCE_NOT_PUBLISHED")
    return result.stdout


def _read_bound_source(
    *, repository: Path, state: Path, binding: SourceBindingV1
) -> bytes:
    if type(binding) is not SourceBindingV1 or binding.root not in ("repository", "state"):
        _fail("SOURCE_BINDING_INVALID")
    relative = Path(binding.relative_path)
    if relative.is_absolute() or ".." in relative.parts:
        _fail("SOURCE_BINDING_INVALID")
    root = repository if binding.root == "repository" else state
    path = root / relative
    try:
        resolved = path.resolve(strict=True)
        metadata = path.stat()
        payload = path.read_bytes()
    except OSError as error:
        raise _AdapterInvariantError("SOURCE_UNAVAILABLE") from error
    if not resolved.is_relative_to(root) or not stat.S_ISREG(metadata.st_mode):
        _fail("SOURCE_NOT_SAFE_REGULAR_FILE")
    if len(payload) != binding.byte_count or hashlib.sha256(payload).hexdigest() != binding.sha256:
        _fail("SOURCE_BINDING_DRIFT")
    if binding.root == "repository" and _git_head_bytes(repository, binding.relative_path) != payload:
        _fail("REPOSITORY_SOURCE_DIFFERS_FROM_HEAD")
    return payload


def _validated_direct_sources(repository: Path, state: Path) -> dict[str, bytes]:
    if len(_DIRECT_SOURCE_BINDINGS) != 27 or len(set(_DIRECT_SOURCE_BINDINGS)) != 27:
        _fail("DIRECT_SOURCE_REGISTRY_INVALID")
    result: dict[str, bytes] = {}
    for binding in _DIRECT_SOURCE_BINDINGS:
        key = f"{binding.root}:{binding.relative_path}"
        if key in result:
            _fail("DIRECT_SOURCE_REGISTRY_INVALID")
        result[key] = _read_bound_source(
            repository=repository,
            state=state,
            binding=binding,
        )
    return result


def _csv_rows(payload: bytes, *, source: str) -> list[dict[str, str]]:
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""), strict=True)
        rows = list(reader)
    except (UnicodeDecodeError, csv.Error) as error:
        raise _AdapterInvariantError("CSV_SOURCE_INVALID") from error
    if reader.fieldnames is None or not rows or any(None in row for row in rows):
        _fail("CSV_SOURCE_INVALID")
    return rows


def _json_object(payload: bytes) -> dict[str, object]:
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise _AdapterInvariantError("JSON_SOURCE_INVALID") from error
    if type(value) is not dict:
        _fail("JSON_SOURCE_INVALID")
    return value


def _one(rows: Sequence[Mapping[str, str]], key: str, value: str) -> Mapping[str, str]:
    matches = [row for row in rows if row.get(key) == value]
    if len(matches) != 1:
        _fail("SOURCE_ROW_NOT_EXACTLY_ONE")
    return matches[0]


def _validate_target_specs_v1(targets: object) -> None:
    if type(targets) not in (tuple, list):
        _fail("TARGET_SPEC_INVALID")
    candidate = tuple(targets)
    if candidate != CANONICAL_TARGETS_V1 or len(candidate) != 5:
        _fail("TARGET_POPULATION_OR_ORDER_INVALID")
    samples: list[str] = []
    events: list[str] = []
    for item in candidate:
        if type(item) not in (tuple, list) or len(item) != 5:
            _fail("TARGET_SPEC_INVALID")
        sample, event, pdb_id, ligand, atom = item
        expected = f"COVAPIE_CYS_SG_EVENT_V1:{pdb_id}:A:CYS:25-:SG:B:{ligand}:{atom}"
        if event != expected:
            _fail("TARGET_EVENT_IDENTITY_MISMATCH")
        samples.append(sample)
        events.append(event)
    if len(set(samples)) != 5 or len(set(events)) != 5:
        _fail("TARGET_IDENTITY_DUPLICATE")


def _validate_source_semantics(sources: Mapping[str, bytes]) -> None:
    def repo(name: str) -> bytes:
        value = sources.get(f"repository:{name}")
        if type(value) is not bytes:
            _fail("DIRECT_SOURCE_SET_INVALID")
        return value

    def state(name: str) -> bytes:
        value = sources.get(f"state:{name}")
        if type(value) is not bytes:
            _fail("DIRECT_SOURCE_SET_INVALID")
        return value

    leakage_rows = _csv_rows(repo(_LEAKAGE_INDEX), source=_LEAKAGE_INDEX)
    positive_rows = _csv_rows(repo(_POSITIVE_INDEX), source=_POSITIVE_INDEX)
    index_rows = _csv_rows(repo(_CURRENT11_INDEX), source=_CURRENT11_INDEX)
    split_rows = _csv_rows(repo(_CURRENT11_SPLIT), source=_CURRENT11_SPLIT)
    group_rows = _csv_rows(repo(_CURRENT11_GROUP), source=_CURRENT11_GROUP)
    target_samples = {item[0] for item in CANONICAL_TARGETS_V1}
    group_members = [
        row
        for row in leakage_rows
        if row.get("leakage_group_id_after") == TARGET_LEAKAGE_GROUP_V1
    ]
    if (
        len(group_members) != 5
        or {row.get("sample_identity") for row in group_members} != target_samples
        or {row.get("formal_split_after") for row in group_members} != {"train"}
    ):
        _fail("TARGET_GROUP_OR_SPLIT_INVALID")
    for sample, event, pdb_id, ligand, atom in CANONICAL_TARGETS_V1:
        leakage = _one(leakage_rows, "sample_identity", sample)
        positive = _one(positive_rows, "sample_identity", sample)
        index = _one(index_rows, "sample_index_row_id", sample)
        split = _one(split_rows, "sample_index_row_id", sample)
        group = _one(group_rows, "sample_index_row_id", sample)
        if (
            leakage.get("canonical_event_id") != event
            or positive.get("canonical_event_id") != event
            or index.get("pdb_id") != pdb_id
            or index.get("ligand_comp_id") != ligand
            or index.get("ligand_covalent_atom_name") != atom
        ):
            _fail("TARGET_SOURCE_IDENTITY_MISMATCH")
        if not (
            leakage.get("current_runtime_model_usable_after") == "true"
            and leakage.get("leakage_evidence_complete") == "true"
            and leakage.get("leakage_group_id_after") == TARGET_LEAKAGE_GROUP_V1
            and leakage.get("formal_split_authoritative_after") == "true"
            and leakage.get("formal_split_after") == "train"
            and leakage.get("training_admission_readiness") == "FORMAL_TRAIN_ADMITTED"
            and positive.get("runtime_binding_status") == "CURRENT_RUNTIME_BINDING_CLOSED"
            and positive.get("positive_authority_status") == "FULL_POSITIVE_SUPERVISION_AUTHORITY"
            and positive.get("role_authority_status") == "authoritative"
            and positive.get("reactive_pair_authority_status") == "authoritative"
            and positive.get("POST_authority_status") == "authoritative"
            and positive.get("PRE_authority_status") == "unavailable_not_loss_eligible"
        ):
            _fail("TARGET_FORMAL_CLOSURE_INVALID")
        if not (
            split.get("final_leakage_group_id") == TARGET_LEAKAGE_GROUP_V1
            and split.get("final_leakage_group_member_count") == "5"
            and split.get("assigned_split") == "train"
            and split.get("sample_split_assignment_passed") == "True"
            and group.get("final_leakage_group_id") == TARGET_LEAKAGE_GROUP_V1
            and group.get("final_leakage_group_member_count") == "5"
            and group.get("final_group_assignment_passed") == "True"
        ):
            _fail("TARGET_PUBLISHED_SPLIT_INVALID")

    closure = _json_object(repo(_CLOSURE_MANIFEST))
    output_hashes = closure.get("output_sha256_excluding_manifest")
    if type(output_hashes) is not dict:
        _fail("CLOSURE_MANIFEST_INVALID")
    for path in (_LEAKAGE_INDEX, _POSITIVE_INDEX):
        expected = output_hashes.get(Path(path).name)
        if expected != hashlib.sha256(repo(path)).hexdigest():
            _fail("CLOSURE_OUTPUT_BINDING_INVALID")

    feature = _json_object(repo(_FEATURE_RESOLUTION_MANIFEST))
    historical = _json_object(repo(_FINAL_FEATURE_AUDIT_MANIFEST))
    if not (
        feature.get("schema_version")
        == "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1"
        and feature.get("feature_semantics_known") is True
        and feature.get("unknown_atom_feature_policy_resolved") is True
        and feature.get("unknown_atom_runtime_enforcement_integrated") is False
        and feature.get("ready_for_training") is False
        and historical.get("feature_semantics_known") is False
        and historical.get("unknown_atom_feature_policy_resolved") is False
        and historical.get("ready_for_training") is False
    ):
        _fail("FEATURE_SEMANTICS_BOUNDARY_INVALID")

    binding = _json_object(state(_CARRIER_BINDING))
    carrier_sha = hashlib.sha256(state(_CARRIER)).hexdigest()
    if not (
        binding.get("schema_version")
        == "covapie_current11_runtime_sample_and_role_order_carrier_binding_report_v1"
        and binding.get("runtime_npz_sha256") == carrier_sha
        and binding.get("status") == "PASS_FORMAL_RUNTIME_CARRIER_BUNDLE_EXACT"
        and binding.get("sample_count") == 11
        and binding.get("array_count") == 12
        and binding.get("ligand_atom_count") == 323
        and binding.get("pocket_atom_count") == 2202
        and binding.get("ready_for_training") is False
        and binding.get("feature_semantics_reaudit_required_before_training") is True
    ):
        _fail("FORMAL_CARRIER_BINDING_INVALID")


def _raw_batch_from_carrier(carrier_bytes: bytes) -> dict[str, object]:
    expected = {
        "names": ((11,), np.dtype("<U27")),
        "receptors": ((11,), np.dtype("<U4")),
        "lig_mask": ((323,), np.dtype("int64")),
        "pocket_mask": ((2202,), np.dtype("int64")),
        "lig_coords": ((323, 3), np.dtype("float32")),
        "pocket_coords": ((2202, 3), np.dtype("float32")),
        "lig_one_hot": ((323, 10), np.dtype("float32")),
        "pocket_one_hot": ((2202, 10), np.dtype("float32")),
        "lig_source_row_index": ((323,), np.dtype("int64")),
        "pocket_source_row_index": ((2202,), np.dtype("int64")),
        "lig_parser_local_index": ((323,), np.dtype("int64")),
        "pocket_parser_local_index": ((2202,), np.dtype("int64")),
    }
    try:
        with np.load(io.BytesIO(carrier_bytes), allow_pickle=False) as carrier:
            if set(carrier.files) != set(expected):
                _fail("FORMAL_CARRIER_ARRAY_SET_INVALID")
            arrays = {name: carrier[name].copy() for name in carrier.files}
    except _AdapterInvariantError:
        raise
    except (OSError, ValueError) as error:
        raise _AdapterInvariantError("FORMAL_CARRIER_NPZ_INVALID") from error
    for name, (shape, dtype) in expected.items():
        value = arrays[name]
        if value.shape != shape or value.dtype != dtype or not value.flags.c_contiguous:
            _fail("FORMAL_CARRIER_ARRAY_CONTRACT_INVALID")
    names = tuple(str(value) for value in arrays.pop("names").tolist())
    receptors = tuple(str(value) for value in arrays.pop("receptors").tolist())
    if names != _CURRENT11_SAMPLE_ORDER or receptors != (
        "6BV6", "6BV8", "6BV5", "1AEC", "1AIM", "1AU3", "1AU4", "1AYU", "1AYV", "1AYW", "1B02"
    ):
        _fail("FORMAL_CARRIER_IDENTITY_ORDER_INVALID")
    for prefix, total in (("lig", 323), ("pocket", 2202)):
        membership = arrays[f"{prefix}_mask"]
        counts = np.bincount(membership, minlength=11)
        if (
            int(membership.min()) != 0
            or int(membership.max()) != 10
            or int(counts.sum()) != total
            or bool((counts <= 0).any())
            or not np.array_equal(membership, np.repeat(np.arange(11), counts))
        ):
            _fail("FORMAL_CARRIER_MEMBERSHIP_INVALID")
        offsets = np.concatenate((np.asarray([0]), np.cumsum(counts)))
        expected_local = np.concatenate(
            [np.arange(int(right - left)) for left, right in zip(offsets, offsets[1:])]
        )
        if not np.array_equal(arrays[f"{prefix}_parser_local_index"], expected_local):
            _fail("FORMAL_CARRIER_LOCAL_INDEX_INVALID")
        one_hot = arrays[f"{prefix}_one_hot"]
        if not bool(np.all((one_hot == 0.0) | (one_hot == 1.0))) or not bool(
            np.all(one_hot.sum(axis=1) == 1.0)
        ):
            _fail("FORMAL_CARRIER_ONE_HOT_INVALID")
        if not bool(np.isfinite(arrays[f"{prefix}_coords"]).all()):
            _fail("FORMAL_CARRIER_COORDINATES_INVALID")
        if bool((arrays[f"{prefix}_source_row_index"] < 0).any()):
            _fail("FORMAL_CARRIER_SOURCE_INDEX_INVALID")
    batch: dict[str, object] = {"names": list(names), "receptors": list(receptors)}
    for name, value in arrays.items():
        batch[name] = torch.from_numpy(value)
    batch["num_lig_atoms"] = torch.tensor(
        [int((batch["lig_mask"] == index).sum().item()) for index in range(11)],
        dtype=torch.long,
    )
    batch["num_pocket_nodes"] = torch.tensor(
        [int((batch["pocket_mask"] == index).sum().item()) for index in range(11)],
        dtype=torch.long,
    )
    if any(
        isinstance(value, torch.Tensor) and value.device.type != "cpu"
        for value in batch.values()
    ):
        _fail("FORMAL_CARRIER_NON_CPU_TENSOR")
    return batch


def _digest_value(digest: object, value: object) -> None:
    update = digest.update
    if value is None:
        update(b"N")
    elif type(value) is bool:
        update(b"B1" if value else b"B0")
    elif type(value) is int:
        update(b"I" + str(value).encode("ascii") + b"\0")
    elif type(value) is float:
        update(b"F" + struct.pack(">d", value))
    elif type(value) is str:
        encoded = value.encode("utf-8")
        update(b"S" + str(len(encoded)).encode("ascii") + b":" + encoded)
    elif isinstance(value, Path):
        _digest_value(digest, str(value))
    elif isinstance(value, torch.Tensor):
        tensor = value.detach().cpu().contiguous()
        update(b"T")
        _digest_value(digest, str(tensor.dtype))
        _digest_value(digest, tuple(tensor.shape))
        update(tensor.numpy().tobytes(order="C"))
    elif type(value) in (tuple, list):
        update(b"Q" if type(value) is tuple else b"L")
        _digest_value(digest, len(value))
        for item in value:
            _digest_value(digest, item)
    elif type(value) is dict:
        if any(type(key) is not str for key in value):
            _fail("PREPARED_PAYLOAD_TYPE_INVALID")
        update(b"D")
        for key in sorted(value):
            _digest_value(digest, key)
            _digest_value(digest, value[key])
    elif type(value) is SourceBindingV1:
        _digest_value(
            digest,
            (value.root, value.relative_path, value.byte_count, value.sha256),
        )
    else:
        _fail("PREPARED_PAYLOAD_TYPE_INVALID")


class CovapieCurrent11LegacyTrain5PreparedV1:
    """Opaque, tamper-evident prepared Current11 carrier/authority triple."""

    __slots__ = (
        "_repository_root",
        "_state_root",
        "_sample_order",
        "_canonical_event_ids",
        "_formal_splits",
        "_source_bindings",
        "_runtime_batch",
        "_authoritative_supervision",
        "_seal",
    )

    def __init__(
        self,
        *,
        token: object,
        repository_root: Path,
        state_root: Path,
        runtime_batch: dict[str, object],
        authoritative_supervision: dict[str, object],
    ) -> None:
        if token is not _CONSTRUCTION_TOKEN:
            raise ValueError(ADAPTER_ERROR_V1)
        self._repository_root = repository_root
        self._state_root = state_root
        self._sample_order = tuple(item[0] for item in CANONICAL_TARGETS_V1)
        self._canonical_event_ids = tuple(item[1] for item in CANONICAL_TARGETS_V1)
        self._formal_splits = ("train",) * 5
        self._source_bindings = _DIRECT_SOURCE_BINDINGS
        self._runtime_batch = copy.deepcopy(runtime_batch)
        self._authoritative_supervision = copy.deepcopy(authoritative_supervision)
        self._seal = _prepared_seal(self)

    @property
    def schema_version(self) -> str:
        return ADAPTER_SCHEMA_V1

    @property
    def repository_root(self) -> Path:
        return self._repository_root

    @property
    def state_root(self) -> Path:
        return self._state_root

    @property
    def sample_order(self) -> tuple[str, ...]:
        return self._sample_order

    @property
    def canonical_event_ids(self) -> tuple[str, ...]:
        return self._canonical_event_ids

    @property
    def formal_splits(self) -> tuple[str, ...]:
        return self._formal_splits

    @property
    def source_bindings(self) -> tuple[SourceBindingV1, ...]:
        return self._source_bindings

    @property
    def owner_generated_output17_used(self) -> bool:
        return True

    @property
    def post_supervision_overlay_applied(self) -> bool:
        return False

    @property
    def post_authority_source_traceable(self) -> bool:
        return True

    @property
    def training_session_active(self) -> bool:
        return False

    @property
    def ready_for_training(self) -> bool:
        return False

    @property
    def feature_semantics_audit_required_later(self) -> bool:
        return True

    @property
    def step12d_is_only_smoke_legality_check(self) -> bool:
        return True


def _prepared_seal(prepared: CovapieCurrent11LegacyTrain5PreparedV1) -> str:
    digest = hashlib.sha256(_SEAL_DOMAIN)
    _digest_value(
        digest,
        (
            prepared._repository_root,
            prepared._state_root,
            prepared._sample_order,
            prepared._canonical_event_ids,
            prepared._formal_splits,
            prepared._source_bindings,
            prepared._runtime_batch,
            prepared._authoritative_supervision,
        ),
    )
    return digest.hexdigest()


def _validate_prepared(
    prepared: object,
) -> CovapieCurrent11LegacyTrain5PreparedV1:
    if type(prepared) is not CovapieCurrent11LegacyTrain5PreparedV1:
        _fail("PREPARED_IDENTITY_INVALID")
    expected_samples = tuple(item[0] for item in CANONICAL_TARGETS_V1)
    expected_events = tuple(item[1] for item in CANONICAL_TARGETS_V1)
    if (
        prepared._sample_order != expected_samples
        or prepared._canonical_event_ids != expected_events
        or prepared._formal_splits != ("train",) * 5
        or prepared._source_bindings != _DIRECT_SOURCE_BINDINGS
        or type(prepared._runtime_batch) is not dict
        or type(prepared._authoritative_supervision) is not dict
        or type(prepared._seal) is not str
        or len(prepared._seal) != 64
    ):
        _fail("PREPARED_METADATA_TAMPERED")
    if _prepared_seal(prepared) != prepared._seal:
        _fail("PREPARED_PAYLOAD_TAMPERED")
    return prepared


def _validate_runtime_result(runtime_batch: object) -> dict[str, object]:
    if type(runtime_batch) is not dict:
        _fail("OWNER_RUNTIME_BATCH_INVALID")
    runtime_result = runtime_batch.get(_SIDECAR_FIELD)
    if not (
        type(runtime_result) is dict
        and runtime_result.get("runtime_status") == "full_success"
        and runtime_result.get("compiler_status") == "COMPILED_EXACT"
        and runtime_result.get("remap_status") == "REMAPPED_EXACT"
        and type(runtime_result.get("remap_output17_or_none")) is dict
        and runtime_result["remap_output17_or_none"].get("remap_status")
        == "REMAPPED_EXACT"
    ):
        _fail("OWNER_GENERATED_OUTPUT17_INVALID")
    return runtime_result


def _validate_runtime_and_authority(
    runtime_batch: object, authoritative_supervision: object
) -> None:
    _validate_runtime_result(runtime_batch)
    if type(authoritative_supervision) is not dict:
        _fail("OWNER_RUNTIME_OR_AUTHORITY_INVALID")
    if authoritative_supervision.get("sample_keys") != list(_CURRENT11_SAMPLE_ORDER):
        _fail("AUTHORITATIVE_SUPERVISION_ORDER_INVALID")
    try:
        _materializer.validate_authoritative_current11_training_supervision_v1(
            authoritative_supervision=authoritative_supervision
        )
    except Exception as error:
        raise _AdapterInvariantError("AUTHORITATIVE_SUPERVISION_INVALID") from error


def _prepare_impl(
    *, repository_root: object, state_root: object
) -> CovapieCurrent11LegacyTrain5PreparedV1:
    repository, state = _roots(repository_root, state_root)
    _validate_target_specs_v1(CANONICAL_TARGETS_V1)
    if tuple(CANONICAL_TASKS_V1) != _EXPECTED_CANONICAL_TASKS:
        _fail("CANONICAL_EXACT5_CONTRACT_DRIFT")
    sources_before = _validated_direct_sources(repository, state)
    _validate_source_semantics(sources_before)
    raw_batch = _raw_batch_from_carrier(sources_before[f"state:{_CARRIER}"])
    remap_context, compiler_context = (
        _runtime_integration.build_or_reuse_covapie_current11_task2_lightning_runtime_context_pair_v1(
            repository_root=str(repository),
            state_root=str(state),
            remap_context=None,
            compiler_context=None,
        )
    )
    runtime_batch = (
        _runtime_integration.attach_covapie_current11_task2_lightning_runtime_result_v1(
            enabled=True,
            batch=raw_batch,
            remap_context=remap_context,
            compiler_context=compiler_context,
        )
    )
    if type(runtime_batch) is not dict:
        _fail("OWNER_RUNTIME_BATCH_INVALID")
    runtime_result = _validate_runtime_result(runtime_batch)
    machine_payload = _materializer.load_covapie_current11_machine_authority_payload_v1(
        repo_root=repository,
        state_root=state,
        runtime_output17=runtime_result.get("remap_output17_or_none"),
    )
    compiled = _human_compiler.load_and_compile_covapie_current11_role_seed_human_gold_v1(
        state_root=state,
        machine_authority_payload=machine_payload,
    )
    if type(compiled) is not dict:
        _fail("HUMAN_GOLD_COMPILATION_INVALID")
    bundle = _materializer.build_current11_training_supervision_v1(
        authority_payload=compiled.get("compiled_authority_payload")
    )
    if type(bundle) is not dict:
        _fail("SUPERVISION_MATERIALIZATION_INVALID")
    authoritative = bundle.get("authoritative_supervision")
    summary = bundle.get("summary")
    if not (
        type(authoritative) is dict
        and type(summary) is dict
        and summary.get("exact3_role_human_gold_count") == 11
        and summary.get("minimal_seed_human_gold_count") == 11
        and summary.get("real_admitted_sample_count") == 11
        and summary.get("observed_geometry_count") == 11
        and summary.get("pre_geometry_authoritative_count") == 0
        and summary.get("post_geometry_authoritative_count") == 0
    ):
        _fail("SUPERVISION_MATERIALIZATION_INVALID")
    _validate_runtime_and_authority(runtime_batch, authoritative)
    sources_after = _validated_direct_sources(repository, state)
    if sources_after != sources_before:
        _fail("SOURCE_CHANGED_DURING_PREPARE")
    return CovapieCurrent11LegacyTrain5PreparedV1(
        token=_CONSTRUCTION_TOKEN,
        repository_root=repository,
        state_root=state,
        runtime_batch=runtime_batch,
        authoritative_supervision=authoritative,
    )


def prepare_covapie_current11_legacy_train5_data_adapter_v1(
    repository_root: object,
    state_root: object,
) -> CovapieCurrent11LegacyTrain5PreparedV1:
    """Prepare one source-bound CPU carrier/runtime/authority component."""

    try:
        return _prepare_impl(
            repository_root=repository_root,
            state_root=state_root,
        )
    except Exception as error:
        _public_error(error)


def _tensorize_impl(
    *, prepared: object, epoch: object, task_schedule_seed: object
) -> tuple[_mixed_tensorizer.CovapieExpandedCysSgTensorizedSampleV1, ...]:
    if type(epoch) is not int or type(epoch) is bool or epoch < 0:
        _fail("EPOCH_INVALID")
    if (
        type(task_schedule_seed) is not int
        or type(task_schedule_seed) is bool
        or not 0 <= task_schedule_seed <= 2**63 - 1
    ):
        _fail("TASK_SCHEDULE_SEED_INVALID")
    valid = _validate_prepared(prepared)
    _validated_direct_sources(valid._repository_root, valid._state_root)
    runtime_batch = copy.deepcopy(valid._runtime_batch)
    authoritative = copy.deepcopy(valid._authoritative_supervision)
    _validate_runtime_and_authority(runtime_batch, authoritative)
    runtime_result = runtime_batch[_SIDECAR_FIELD]
    result: list[_mixed_tensorizer.CovapieExpandedCysSgTensorizedSampleV1] = []
    for sample_identity in valid._sample_order:
        task_id = canonical_task_id_for_covapie_current11_sample_v1(
            sample_key=sample_identity,
            epoch=epoch,
            task_schedule_seed=task_schedule_seed,
        )
        item = _mixed_tensorizer.tensorize_covapie_expanded_cys_sg_sample_v1(
            sample_identity=sample_identity,
            task_id=task_id,
            device="cpu",
            epoch=epoch,
            task_schedule_seed=task_schedule_seed,
            current11_batch=runtime_batch,
            current11_runtime_result=runtime_result,
            current11_authoritative_supervision=authoritative,
        )
        if (
            type(item)
            is not _mixed_tensorizer.CovapieExpandedCysSgTensorizedSampleV1
            or item.sample_identity != sample_identity
        ):
            _fail("TENSORIZER_RESULT_INVALID")
        result.append(item)
    if tuple(item.sample_identity for item in result) != valid._sample_order:
        _fail("TENSORIZED_TARGET_ORDER_INVALID")
    if _prepared_seal(valid) != valid._seal:
        _fail("PREPARED_MUTATED_DURING_TENSORIZATION")
    _validated_direct_sources(valid._repository_root, valid._state_root)
    return tuple(result)


def tensorize_covapie_current11_legacy_train5_epoch_v1(
    prepared: object,
    epoch: object,
    task_schedule_seed: object = 0,
) -> tuple[_mixed_tensorizer.CovapieExpandedCysSgTensorizedSampleV1, ...]:
    """Return the fixed-order five real CPU samples for one canonical epoch."""

    try:
        return _tensorize_impl(
            prepared=prepared,
            epoch=epoch,
            task_schedule_seed=task_schedule_seed,
        )
    except Exception as error:
        _public_error(error)


def main(argv: Sequence[str] | None = None) -> int:
    """Prepare only and print a scalar, non-authoritative status summary."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    arguments = parser.parse_args(argv)
    prepared = prepare_covapie_current11_legacy_train5_data_adapter_v1(
        arguments.repository_root,
        arguments.state_root,
    )
    print(
        "PREPARE_STATUS=PASS "
        f"TARGET_SAMPLE_COUNT={len(prepared.sample_order)} "
        f"DIRECT_SOURCE_BINDING_COUNT={len(prepared.source_bindings)} "
        "OWNER_GENERATED_OUTPUT17_USED=true "
        "POST_SUPERVISION_OVERLAY_APPLIED=false "
        "TRAINING_SESSION_ACTIVE=false "
        "READY_FOR_TRAINING=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
