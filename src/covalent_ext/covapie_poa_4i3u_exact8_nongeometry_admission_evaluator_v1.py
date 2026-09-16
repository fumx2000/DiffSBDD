"""Source-bound POA 4I3U Exact8 scoped non-geometry admission evaluation.

This evaluator does not create formal admission, mutate an inactive payload,
activate a loss, or connect a training consumer.  It evaluates a deliberately
limited candidate policy over one published formal group and the eight 4I3U
events already approved for non-geometry consideration.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, replace
import hashlib
import json
import math
from pathlib import Path
import stat
import subprocess
from typing import NoReturn

import torch

from covalent_ext import (
    covapie_poa_4i3u_exact8_inactive_consumer_adapter_v1 as adapter_owner,
)
from covalent_ext import (
    covapie_poa_4i3u_exact8_real_preview_evidence_v1 as b1_owner,
)
from covalent_ext import (
    covapie_poa_full_component_formal_split_authority_v1 as split_owner,
)
from covalent_ext import (
    covapie_poa_sample_level_effective_supervision_v1 as metadata_owner,
)


__all__ = (
    "POA4I3UExact8NongeometryAdmissionEvaluatorError",
    "POA4I3UExact8NongeometryAdmissionEvaluationContextV1",
    "ScopedEventTaskFactsV1",
    "prepare_covapie_poa_4i3u_exact8_nongeometry_admission_evaluator_v1",
    "build_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1",
    "validate_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1",
    "serialize_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1",
    "evaluate_scoped_event_task_facts_v1",
)


TASK_ID = "implement_covapie_poa_4i3u_exact8_nongeometry_admission_evaluator_v1"
SCHEMA_VERSION = "covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1"
POLICY_SCOPE_ID = "POA_4I3U_EXACT8_CANONICAL5_NONGEOMETRY_USE_SCOPE_V1"
RECORD_ROLE = "UNPUBLISHED_SCOPED_NONGEOMETRY_ADMISSION_EVALUATION_CANDIDATE"
ERROR_TOKEN = "COVAPIE_POA_4I3U_EXACT8_NONGEOMETRY_ADMISSION_EVALUATOR_V1_ERROR"
BASELINE_COMMIT = "74261112981114347e6e514b882ea748ee6d1e38"
FORMAL_GROUP_ID = "COVAPIE_EXPANSION_LEAKAGE_GROUP_F70DB37A8004AF17"
ELIGIBLE = "ELIGIBLE_FOR_SCOPED_NON_GEOMETRY_USE"
BLOCKED = "BLOCKED_FOR_SCOPED_NON_GEOMETRY_USE"
NOT_APPLICABLE = "NOT_APPLICABLE_TO_CANONICAL_TASK"

CANONICAL_TASKS_V1 = (
    (0, "warhead_only", "A", 2, 5, 0),
    (1, "linker_plus_warhead", "B", 3, 4, 0),
    (2, "scaffold_plus_warhead", "B2", 6, 1, 0),
    (3, "scaffold_only", "B3", 4, 3, 0),
    (4, "scaffold_plus_linker_plus_warhead", "C", 7, 0, 2),
)

# These identities were obtained from BASELINE_COMMIT.  Worktree content is
# checked against both the committed blob and these immutable identities.
DIRECT_SOURCE_SPECS_V1 = (
    (
        "inactive_consumer_adapter_owner",
        "src/covalent_ext/covapie_poa_4i3u_exact8_inactive_consumer_adapter_v1.py",
        49851,
        "4eaaf989e89b407c740d287feff4f0979d7d7721dbff9b493fafb022e5e5622f",
        "df1e239ecb88a8cc13a030f1ea0b9b5b878a490b",
    ),
    (
        "seed_ingestion_owner",
        "src/covalent_ext/covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1.py",
        45222,
        "9d0b0c331184530913d36d4eff6b0c53d00be0508915ddf0e3807c9739d20e14",
        "a75f9b1d15a472f4ef238619f85a011a15941443",
    ),
    (
        "seed_ingestion_result",
        "data/derived/covalent_small/covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1/poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1.json",
        17716,
        "38e9537c92f01f36dbd4fa9fdae825d944f6148c6a694f18f60a41a88ef0b8c5",
        "93cb4a37ab3a38911e168480b1fb47d3d78a5a40",
    ),
    (
        "b1_real_preview_owner",
        "src/covalent_ext/covapie_poa_4i3u_exact8_real_preview_evidence_v1.py",
        49717,
        "854dd063ac822d7b8e7ddad7a887ec9fd7c78645e09a2166bbc4d46b0ac01649",
        "2dbba7c5e800b609293750f626b01d5f2b064716",
    ),
    (
        "b1_real_preview_result",
        "data/derived/covalent_small/covapie_poa_4i3u_exact8_real_preview_evidence_v1/poa_4i3u_exact8_real_preview_evidence_v1.json",
        1522292,
        "98d4ec2e0d8c6fc00816a70b5927240f437d7e8d64a0981751ddc93684906d40",
        "5fd595ca9923d4d6339446cf74d872a74ac78c23",
    ),
    (
        "formal_split_owner",
        "src/covalent_ext/covapie_poa_full_component_formal_split_authority_v1.py",
        83848,
        "fa466fc335b664bec5063711a6da9576b0781594f9818f7f34be9f6090d491a8",
        "26cbc15ad3b52708c312b05bfa4a0ffbbc613056",
    ),
    (
        "sample_effective_supervision_owner",
        "src/covalent_ext/covapie_poa_sample_level_effective_supervision_v1.py",
        42406,
        "f4656f414a5d31d5e967b39885dd5d89e9bf205135dbd29b3285e0d1e856367f",
        "747f3e830a63bd208914af64ac08cb9b4ed042c0",
    ),
    (
        "complete_post_runtime_closure_owner_scope_exclusion_only",
        "src/covalent_ext/covapie_existing_positive_runtime_and_split_closure_v1.py",
        103692,
        "dbca845ccaa7859e78301e413c676d40d28e49228471274f99e4d77c55d2816c",
        "e5767e41ce4eb523fdd503824bed09550428c22d",
    ),
)

PERMISSION_BOUNDARY_V1 = {
    "NEW_HUMAN_DECISION_CREATED": False,
    "NEW_FORMAL_ADMISSION_CREATED": False,
    "FORMAL_ADMISSION_EFFECTIVE": False,
    "ACTIVE_TRAINING_CONSUMER_CONNECTED": False,
    "CURRENT_TRAIN12_POPULATION_CHANGED": False,
    "REAL_MODEL_EXECUTED": False,
    "PARAMETER_UPDATE_PERFORMED": False,
    "READY_FOR_TRAINING": False,
    "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER": True,
    "STEP12D_IS_ONLY_SMOKE_LEGALITY_CHECK": True,
    "COMMIT_PERFORMED": False,
    "PUSH_PERFORMED": False,
}


class POA4I3UExact8NongeometryAdmissionEvaluatorError(ValueError):
    """Raised when source binding or scoped rule evaluation fails closed."""


def _fail(reason: str) -> NoReturn:
    raise POA4I3UExact8NongeometryAdmissionEvaluatorError(
        f"{ERROR_TOKEN}:{reason}"
    )


@dataclass(frozen=True, slots=True)
class SourceBindingV1:
    artifact_role: str
    path_namespace: str
    path: str
    byte_count: int
    sha256: str
    git_blob_sha1: str | None


@dataclass(frozen=True, slots=True)
class ScopedEventTaskFactsV1:
    canonical_event_id: str
    canonical_task_id: int
    canonical_task_name: str
    canonical_task_alias: str
    source_bound: bool
    target_population_member: bool
    human_review_completed: bool
    training_use_disposition: str
    human_training_excluded: bool
    explicit_covalent_event: bool
    formal_group_id: str
    formal_split: str
    formal_split_authoritative: bool
    formal_sample_training_admitted_preserved_false: bool
    exact10_feature_inputs_valid: bool
    role_partition_and_reactive_indices_valid: bool
    source_local_flat_mapping_valid: bool
    generated_count: int
    fixed_count: int
    seed_count: int
    seed_mapping_valid: bool
    pair_candidate_count: int
    pair_positive_count: int
    pair_negative_count: int
    pair_indices_sample_local: bool
    observed_complex_distance_finite_and_valid: bool
    geometry_nan_component_count: int
    geometry_valid_component_count: int
    geometry_loss_component_count: int
    inactive_admission_and_loss_masks: bool


@dataclass(frozen=True)
class POA4I3UExact8NongeometryAdmissionEvaluationContextV1:
    repository_root: Path
    state_root: Path
    direct_source_bindings: tuple[SourceBindingV1, ...]
    formal_split_result: split_owner.POAFullComponentFormalSplitAuthorityResultV1
    prepared: adapter_owner.POA4I3UExact8InactiveConsumerPreparedV1
    payloads: tuple[adapter_owner.POA4I3UExact8InactiveConsumerPayloadV1, ...]
    target_event_ids: tuple[str, ...]
    context_seal_sha256: str


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: object, *, newline: bool = False) -> bytes:
    payload = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return payload + (b"\n" if newline else b"")


def _strict_equal(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return len(left) == len(right) and set(left) == set(right) and all(
            _strict_equal(left[key], right[key]) for key in left
        )
    if type(left) is list:
        return len(left) == len(right) and all(
            _strict_equal(a, b) for a, b in zip(left, right, strict=True)
        )
    return left == right


def _resolve_root(value: Path | str, label: str) -> Path:
    if not isinstance(value, (Path, str)):
        _fail(label + "_PATH_REQUIRED")
    path = Path(value).resolve(strict=True)
    if not path.is_dir():
        _fail(label + "_DIRECTORY_REQUIRED")
    return path


def _git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ("git", "-C", str(repository), *arguments),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def _validate_baseline_lineage(
    repository: Path, *, baseline_commit: str = BASELINE_COMMIT
) -> None:
    """Require the fixed baseline commit to exist and anchor current HEAD."""

    if type(baseline_commit) is not str or len(baseline_commit) != 40:
        _fail("BASELINE_COMMIT_ID_INVALID")
    try:
        if _git(repository, "cat-file", "-t", baseline_commit) != "commit":
            _fail("BASELINE_OBJECT_IS_NOT_COMMIT")
        if _git(repository, "cat-file", "-t", "HEAD") != "commit":
            _fail("HEAD_OBJECT_IS_NOT_COMMIT")
    except POA4I3UExact8NongeometryAdmissionEvaluatorError:
        raise
    except Exception as error:
        raise POA4I3UExact8NongeometryAdmissionEvaluatorError(
            f"{ERROR_TOKEN}:BASELINE_OR_HEAD_COMMIT_OBJECT_UNAVAILABLE:"
            f"{type(error).__name__}:{error}"
        ) from error
    try:
        completed = subprocess.run(
            (
                "git", "-C", str(repository), "merge-base", "--is-ancestor",
                baseline_commit, "HEAD",
            ),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except Exception as error:
        raise POA4I3UExact8NongeometryAdmissionEvaluatorError(
            f"{ERROR_TOKEN}:BASELINE_ANCESTRY_GIT_COMMAND_FAILED:"
            f"{type(error).__name__}:{error}"
        ) from error
    if completed.returncode == 1:
        _fail("BASELINE_IS_NOT_ANCESTOR_OF_HEAD")
    if completed.returncode != 0:
        _fail("BASELINE_ANCESTRY_GIT_COMMAND_FAILED")


def _read_regular(path: Path, *, reason: str) -> bytes:
    try:
        status = path.lstat()
    except OSError as error:
        raise POA4I3UExact8NongeometryAdmissionEvaluatorError(
            f"{ERROR_TOKEN}:{reason}_UNREADABLE:{type(error).__name__}"
        ) from error
    if not stat.S_ISREG(status.st_mode) or path.is_symlink():
        _fail(reason + "_REGULAR_NONSYMLINK_REQUIRED")
    return path.read_bytes()


def _source_binding_from_spec(
    repository: Path,
    spec: tuple[str, str, int, str, str],
    *,
    baseline_commit: str = BASELINE_COMMIT,
) -> SourceBindingV1:
    role, relative, byte_count, digest, blob = spec
    committed_blob = _git(
        repository, "rev-parse", f"{baseline_commit}:{relative}"
    )
    payload = _read_regular(repository / relative, reason="DIRECT_SOURCE")
    if (
        committed_blob != blob
        or len(payload) != byte_count
        or _sha256(payload) != digest
    ):
        _fail("DIRECT_SOURCE_IDENTITY_MISMATCH:" + relative)
    return SourceBindingV1(
        artifact_role=role,
        path_namespace="repository_root_relative",
        path=relative,
        byte_count=byte_count,
        sha256=digest,
        git_blob_sha1=blob,
    )


def _direct_source_bindings(repository: Path) -> tuple[SourceBindingV1, ...]:
    try:
        _validate_baseline_lineage(repository)
        return tuple(
            _source_binding_from_spec(repository, spec)
            for spec in DIRECT_SOURCE_SPECS_V1
        )
    except POA4I3UExact8NongeometryAdmissionEvaluatorError:
        raise
    except Exception as error:
        raise POA4I3UExact8NongeometryAdmissionEvaluatorError(
            f"{ERROR_TOKEN}:DIRECT_SOURCE_BINDING_REJECTED:"
            f"{type(error).__name__}:{error}"
        ) from error


def _context_projection(
    context: POA4I3UExact8NongeometryAdmissionEvaluationContextV1,
) -> dict[str, object]:
    return {
        "direct_source_bindings": [asdict(row) for row in context.direct_source_bindings],
        "formal_group_id": context.formal_split_result.formal_group_id,
        "formal_split": context.formal_split_result.formal_split,
        "formal_inventory_sha256": (
            context.formal_split_result.canonical_event_inventory_sha256
        ),
        "prepared_seal_sha256": context.prepared.completeness_seal_sha256,
        "target_event_ids": list(context.target_event_ids),
        "payloads": [
            {
                "task": payload.canonical_task_name,
                "task_id": payload.canonical_task_id,
                "event_ids": list(payload.sample_identities),
                "summary": asdict(payload.summary),
            }
            for payload in context.payloads
        ],
    }


def _validate_repository_binding(
    repository: Path, *, path: str, byte_count: int, sha256: str
) -> None:
    payload = _read_regular(repository / path, reason="TRANSITIVE_REPOSITORY_SOURCE")
    if len(payload) != byte_count or _sha256(payload) != sha256:
        _fail("TRANSITIVE_REPOSITORY_SOURCE_MISMATCH:" + path)


def _metadata_by_event(
    context: POA4I3UExact8NongeometryAdmissionEvaluationContextV1,
) -> dict[str, metadata_owner.POASampleLevelEffectiveSupervisionRecordV1]:
    records = context.prepared.effective_supervision.records
    mapping = {row.canonical_event_id: row for row in records}
    if len(mapping) != len(records):
        _fail("EFFECTIVE_METADATA_EVENT_UNIQUENESS_INVALID")
    return mapping


def _validate_context(
    value: object,
) -> POA4I3UExact8NongeometryAdmissionEvaluationContextV1:
    if type(value) is not POA4I3UExact8NongeometryAdmissionEvaluationContextV1:
        _fail("EXACT_CONTEXT_TYPE_REQUIRED")
    context = value
    if (
        context.repository_root != context.repository_root.resolve(strict=True)
        or context.state_root != context.state_root.resolve(strict=True)
        or context.repository_root == context.state_root
        or context.direct_source_bindings
        != _direct_source_bindings(context.repository_root)
        or context.context_seal_sha256
        != _sha256(_canonical_json_bytes(_context_projection(context)))
    ):
        _fail("CONTEXT_HEADER_OR_SEAL_INVALID")
    if not split_owner.validate_covapie_poa_full_component_formal_split_authority_v1(
        context.formal_split_result
    ):
        _fail("FORMAL_SPLIT_PUBLIC_VALIDATOR_REJECTED")
    for binding in context.formal_split_result.source_bindings:
        _validate_repository_binding(
            context.repository_root,
            path=binding.repository_relative_path,
            byte_count=binding.byte_count,
            sha256=binding.sha256,
        )
    for binding in context.prepared.source_bindings:
        _validate_repository_binding(
            context.repository_root,
            path=binding.repository_relative_path,
            byte_count=binding.byte_count,
            sha256=binding.sha256,
        )
    if (
        len(context.payloads) != 5
        or tuple(payload.canonical_task_name for payload in context.payloads)
        != tuple(row[1] for row in CANONICAL_TASKS_V1)
        or any(
            not adapter_owner.validate_covapie_poa_4i3u_exact8_inactive_consumer_payload_v1(
                payload=payload, prepared=context.prepared
            )
            for payload in context.payloads
        )
    ):
        _fail("EXACT5_INACTIVE_PAYLOAD_VALIDATION_INVALID")
    base_ids = tuple(context.prepared.base_preview.sample_identities)
    ingestion_records = context.prepared.published_ingestion_result[
        "semantic_projection"
    ]["event_records"]
    ingestion_ids = tuple(row["canonical_event_id"] for row in ingestion_records)
    metadata = _metadata_by_event(context)
    metadata_4i3u = tuple(
        row.canonical_event_id
        for row in context.prepared.effective_supervision.records
        if row.pdb_id == "4I3U"
    )
    if (
        len(context.target_event_ids) != 8
        or len(set(context.target_event_ids)) != 8
        or context.target_event_ids != base_ids
        or ingestion_ids != context.target_event_ids
        or set(metadata_4i3u) != set(context.target_event_ids)
        or any(payload.sample_identities != context.target_event_ids for payload in context.payloads)
        or not set(context.target_event_ids).issubset(
            context.formal_split_result.full_member_canonical_event_ids
        )
        or any(event_id not in metadata for event_id in context.target_event_ids)
    ):
        _fail("FOUR_WAY_EXACT8_POPULATION_PARITY_INVALID")
    return context


def prepare_covapie_poa_4i3u_exact8_nongeometry_admission_evaluator_v1(
    *, repository_root: Path | str, state_root: Path | str
) -> POA4I3UExact8NongeometryAdmissionEvaluationContextV1:
    """Build the formal split once and prepare the real inactive CPU data once."""

    try:
        repository = _resolve_root(repository_root, "REPOSITORY_ROOT")
        state = _resolve_root(state_root, "STATE_ROOT")
        if repository == state:
            _fail("REPOSITORY_AND_STATE_ROOT_MUST_DIFFER")
        direct = _direct_source_bindings(repository)
        formal = split_owner.build_covapie_poa_full_component_formal_split_authority_v1(
            repo_root=repository
        )
        if not split_owner.validate_covapie_poa_full_component_formal_split_authority_v1(
            formal
        ):
            _fail("FORMAL_SPLIT_EXPLICIT_VALIDATION_REJECTED")
        if (
            formal.formal_group_id != FORMAL_GROUP_ID
            or formal.formal_split != "train"
            or formal.formal_split_authoritative is not True
            or len(formal.full_member_canonical_event_ids) != 24
            or formal.sample_training_admitted is not False
        ):
            _fail("FORMAL_SPLIT_SCOPE_INVALID")
        prepared = adapter_owner.prepare_covapie_poa_4i3u_exact8_inactive_consumer_adapter_v1(
            repository_root=repository, state_root=state
        )
        payloads = tuple(
            adapter_owner.build_covapie_poa_4i3u_exact8_inactive_consumer_payload_v1(
                prepared=prepared, canonical_task_name=task_name
            )
            for _, task_name, _, _, _, _ in CANONICAL_TASKS_V1
        )
        for payload in payloads:
            adapter_owner.validate_covapie_poa_4i3u_exact8_inactive_consumer_payload_v1(
                payload=payload, prepared=prepared
            )
        target_ids = tuple(payloads[0].sample_identities)
        unsealed = POA4I3UExact8NongeometryAdmissionEvaluationContextV1(
            repository_root=repository,
            state_root=state,
            direct_source_bindings=direct,
            formal_split_result=formal,
            prepared=prepared,
            payloads=payloads,
            target_event_ids=target_ids,
            context_seal_sha256="",
        )
        context = replace(
            unsealed,
            context_seal_sha256=_sha256(
                _canonical_json_bytes(_context_projection(unsealed))
            ),
        )
        return _validate_context(context)
    except POA4I3UExact8NongeometryAdmissionEvaluatorError:
        raise
    except Exception as error:
        raise POA4I3UExact8NongeometryAdmissionEvaluatorError(
            f"{ERROR_TOKEN}:PUBLIC_PREPARE_REJECTED:{type(error).__name__}:{error}"
        ) from error


def _pair_facts(payload: object, sample: int) -> tuple[int, int, int, bool]:
    supervision = payload.supervision
    start = int(supervision.pair_candidate_offsets[sample].item())
    end = int(supervision.pair_candidate_offsets[sample + 1].item())
    ligand_start, ligand_end = payload.ligand_node_offsets[sample : sample + 2]
    pocket_start, pocket_end = payload.pocket_node_offsets[sample : sample + 2]
    positives = 0
    negatives = 0
    mapping_valid = end >= start
    positive_indices: list[int] = []
    for index in range(start, end):
        batch = int(supervision.pair_candidate_batch_index[index].item())
        ligand_local = int(
            supervision.pair_candidate_ligand_local_index[index].item()
        )
        pocket_local = int(
            supervision.pair_candidate_residue_local_index[index].item()
        )
        ligand_flat = int(
            supervision.pair_candidate_ligand_flat_index[index].item()
        )
        pocket_flat = int(
            supervision.pair_candidate_pocket_flat_index[index].item()
        )
        positive = bool(supervision.pair_candidate_is_positive[index].item())
        negative = bool(supervision.pair_candidate_is_negative[index].item())
        positives += int(positive)
        negatives += int(negative)
        if positive:
            positive_indices.append(index)
        mapping_valid = mapping_valid and (
            batch == sample
            and 0 <= ligand_local < ligand_end - ligand_start
            and 0 <= pocket_local < pocket_end - pocket_start
            and ligand_flat == ligand_start + ligand_local
            and pocket_flat == pocket_start + pocket_local
            and positive is not negative
        )
    expected_positive = int(supervision.pair_positive_candidate_index[sample].item())
    mapping_valid = mapping_valid and (
        positive_indices == [expected_positive]
        and bool(supervision.pair_positive_candidate_valid[sample].item())
        and int(supervision.pair_negative_count[sample].item()) == negatives
        and expected_positive >= start
        and expected_positive < end
        and int(supervision.pair_candidate_ligand_local_index[expected_positive].item())
        == int(payload.ligand_reactive_atom_local_index[sample].item())
        and int(supervision.pair_candidate_pocket_flat_index[expected_positive].item())
        == int(supervision.target_residue_reactive_atom_flat_index[sample].item())
    )
    return end - start, positives, negatives, mapping_valid


def _facts_for(
    context: POA4I3UExact8NongeometryAdmissionEvaluationContextV1,
    *, sample: int, payload: object,
) -> ScopedEventTaskFactsV1:
    event_id = context.target_event_ids[sample]
    metadata = _metadata_by_event(context)[event_id]
    formal_matches = tuple(
        row for row in context.formal_split_result.records
        if row.canonical_event_id == event_id
    )
    if len(formal_matches) != 1:
        _fail("FORMAL_EVENT_NOT_EXACTLY_ONE:" + event_id)
    formal = formal_matches[0]
    task = CANONICAL_TASKS_V1[payload.canonical_task_id]
    task_id, task_name, alias, expected_generated, expected_fixed, expected_seed = task
    start, end = payload.ligand_node_offsets[sample : sample + 2]
    pocket_start, pocket_end = payload.pocket_node_offsets[sample : sample + 2]
    supervision = payload.supervision
    model = payload.model_input_batch
    generated = int(supervision.ligand_base_generation_mask[start:end].sum().item())
    fixed = int(supervision.ligand_base_fixed_mask[start:end].sum().item())
    seed = int(
        supervision.ligand_minimal_seed_or_anchor_mask[start:end].sum().item()
    )
    roles = supervision.ligand_role_id[start:end]
    role_valid = supervision.ligand_role_valid[start:end]
    source_local_flat_valid = (
        tuple(model["lig_parser_local_index"][start:end].tolist()) == tuple(range(7))
        and bool((model["lig_source_row_index"][start:end] >= 0).all().item())
        and int(payload.ligand_reactive_atom_flat_index[sample].item())
        == start + int(payload.ligand_reactive_atom_local_index[sample].item())
        and int(supervision.target_residue_reactive_atom_flat_index[sample].item())
        == pocket_start
        + int(supervision.target_residue_reactive_atom_local_index[sample].item())
    )
    exact10_valid = (
        tuple(model["lig_one_hot"][start:end].shape) == (7, 10)
        and model["pocket_one_hot"][pocket_start:pocket_end].shape[1] == 10
        and tuple(model["lig_coords"][start:end].shape) == (7, 3)
        and model["pocket_coords"][pocket_start:pocket_end].shape[1] == 3
        and bool((model["lig_one_hot"][start:end].sum(1) == 1).all().item())
        and bool(
            (model["pocket_one_hot"][pocket_start:pocket_end].sum(1) == 1)
            .all()
            .item()
        )
    )
    roles_and_indices = (
        bool(role_valid.all().item())
        and tuple(sorted(int(value) for value in roles.unique().tolist())) == (0, 1, 2)
        and int((roles == 0).sum().item()) == 4
        and int((roles == 1).sum().item()) == 1
        and int((roles == 2).sum().item()) == 2
        and generated == expected_generated
        and fixed == expected_fixed
        and bool(
            (~(
                supervision.ligand_base_generation_mask[start:end, 0]
                & supervision.ligand_base_fixed_mask[start:end, 0]
            )).all().item()
        )
        and generated + fixed == 7
    )
    seed_mapping_valid = seed == expected_seed
    if task_id == 4:
        mapping = payload.seed_anchor_mappings[sample]
        seed_mapping_valid = seed_mapping_valid and (
            mapping.canonical_event_id == event_id
            and mapping.approved_seed_atom_ids == ("P", "O1P")
            and mapping.seed_model_sample_local_indices_0based == (6, 3)
            and mapping.ligand_primary_anchor_atom_id == "P"
            and mapping.primary_anchor_model_sample_local_index_0based == 6
            and bool(supervision.ligand_minimal_seed_or_anchor_valid[sample].item())
            and mapping.ligand_anchor_distance_reference_semantics
            == "EXISTING_OBSERVED_DISTANCE_TO_PROTEIN_TARGET_CYS_SG_NOT_TO_LIGAND_P"
        )
    else:
        seed_mapping_valid = seed_mapping_valid and not bool(
            supervision.ligand_minimal_seed_or_anchor_valid[sample].item()
        )
    pair_count, positive_count, negative_count, pair_mapping = _pair_facts(
        payload, sample
    )
    observed = float(
        supervision.observed_complex_pair_distance_angstrom[sample, 0].item()
    )
    observed_valid = bool(
        supervision.observed_complex_pair_distance_valid[sample, 0].item()
    )
    geometry = supervision.pre_post_geometry_target_angstrom[sample]
    geometry_valid = supervision.pre_post_geometry_component_valid_mask[sample]
    geometry_loss = supervision.pre_post_geometry_component_loss_mask[sample]
    inactive = (
        not bool(supervision.sample_training_admitted[sample].item())
        and not bool(
            supervision.ligand_active_diffusion_loss_mask[start:end].any().item()
        )
        and not bool(
            supervision.pair_head_candidate_loss_mask[
                int(supervision.pair_candidate_offsets[sample].item()):
                int(supervision.pair_candidate_offsets[sample + 1].item())
            ].any().item()
        )
        and not bool(supervision.pair_contrastive_sample_loss_mask[sample].item())
        and not bool(geometry_loss.any().item())
    )
    return ScopedEventTaskFactsV1(
        canonical_event_id=event_id,
        canonical_task_id=task_id,
        canonical_task_name=task_name,
        canonical_task_alias=alias,
        source_bound=True,
        target_population_member=True,
        human_review_completed=metadata.human_review_completed,
        training_use_disposition=metadata.training_use_disposition,
        human_training_excluded=metadata.human_training_excluded,
        explicit_covalent_event=(
            metadata.chemistry_positive
            and metadata.reactive_pair_authority_available
            and metadata.ligand_component_id == "POA"
            and metadata.ligand_reactive_atom_id == "C2"
            and metadata.target_residue_name == "CYS"
            and metadata.target_residue_atom_id == "SG"
        ),
        formal_group_id=formal.formal_leakage_group_id,
        formal_split=formal.formal_split,
        formal_split_authoritative=formal.formal_split_authoritative,
        formal_sample_training_admitted_preserved_false=(
            formal.sample_training_admitted is False
            and formal.model_training_activation_authorized is False
        ),
        exact10_feature_inputs_valid=exact10_valid,
        role_partition_and_reactive_indices_valid=roles_and_indices,
        source_local_flat_mapping_valid=source_local_flat_valid,
        generated_count=generated,
        fixed_count=fixed,
        seed_count=seed,
        seed_mapping_valid=seed_mapping_valid,
        pair_candidate_count=pair_count,
        pair_positive_count=positive_count,
        pair_negative_count=negative_count,
        pair_indices_sample_local=pair_mapping,
        observed_complex_distance_finite_and_valid=(
            observed_valid and math.isfinite(observed) and observed > 0
        ),
        geometry_nan_component_count=int(torch.isnan(geometry).sum().item()),
        geometry_valid_component_count=int(geometry_valid.sum().item()),
        geometry_loss_component_count=int(geometry_loss.sum().item()),
        inactive_admission_and_loss_masks=inactive,
    )


RULE_DEFINITIONS_V1 = (
    {
        "rule_id": "R01_FIXED_SOURCE_BINDING",
        "provenance_kind": "PUBLISHED_OWNER_AND_BASELINE_GIT_BLOBS",
        "owner_or_scope": "inactive adapter, ingestion, B1, metadata, formal split",
        "fields": ["bytes", "sha256", "git_blob_sha1"],
        "statement": "All consumed owners and snapshots must retain fixed identities.",
    },
    {
        "rule_id": "R02_EXACT8_TARGET_INTERSECTION",
        "provenance_kind": "PROPOSED_SCOPED_POLICY_V1",
        "owner_or_scope": POLICY_SCOPE_ID,
        "fields": ["manual 4I3U INCLUDE", "seed Exact8", "B1 Exact8", "adapter Exact8"],
        "statement": "The four populations must agree exactly; group membership alone is insufficient.",
    },
    {
        "rule_id": "R03_HUMAN_INCLUDE_NONEXCLUDE",
        "provenance_kind": "PUBLISHED_OWNER_FIELDS",
        "owner_or_scope": "covapie_poa_sample_level_effective_supervision_v1",
        "fields": ["human_review_completed", "training_use_disposition", "human_training_excluded"],
        "statement": "An event must be explicitly INCLUDE and not human-excluded.",
    },
    {
        "rule_id": "R04_FORMAL_TRAIN_GROUP",
        "provenance_kind": "PUBLISHED_OWNER_FIELDS",
        "owner_or_scope": "covapie_poa_full_component_formal_split_authority_v1",
        "fields": ["formal_group_id", "formal_split", "formal_split_authoritative"],
        "statement": "The event must belong to the one authoritative train group; reservation stays non-admission.",
    },
    {
        "rule_id": "R05_EXPLICIT_COVALENT_PAIR",
        "provenance_kind": "PUBLISHED_OWNER_FIELDS",
        "owner_or_scope": "sample effective supervision and validated B1",
        "fields": ["chemistry_positive", "C2", "CYS SG", "reactive_pair_authority_available"],
        "statement": "The explicit POA C2 to protein CYS SG event identity must be authoritative.",
    },
    {
        "rule_id": "R06_EXACT10_AND_INDEX_MAPPING",
        "provenance_kind": "PUBLISHED_OWNER_FIELDS",
        "owner_or_scope": "validated inactive adapter payload",
        "fields": ["lig/pocket exact10 one-hot", "source index", "sample-local index", "batch-flat index"],
        "statement": "Element channels and all source/local/flat mappings must remain coherent.",
    },
    {
        "rule_id": "R07_CANONICAL5_ROLE_MASKS",
        "provenance_kind": "PUBLISHED_OWNER_FIELDS",
        "owner_or_scope": "role-mask owner through validated inactive adapter",
        "fields": ["role_id", "generation_mask", "fixed_mask"],
        "statement": "Exactly the canonical five long-name tasks are evaluated with B3 retained.",
    },
    {
        "rule_id": "R08_PAIR_DOMAIN_SCOPED_ELIGIBILITY",
        "provenance_kind": "PROPOSED_SCOPED_POLICY_V1_FROM_VALIDATED_FIELDS",
        "owner_or_scope": POLICY_SCOPE_ID,
        "fields": ["42 candidates/event", "one positive", "41 negatives", "sample-local endpoints"],
        "statement": "The actual validated candidate domain may support scoped pair and contrastive eligibility without activating a loss.",
    },
    {
        "rule_id": "R09_TASK_C_SIGNED_SEED",
        "provenance_kind": "PUBLISHED_OWNER_FIELDS",
        "owner_or_scope": "Task C seed ingestion through inactive adapter",
        "fields": ["P/O1P", "sample-local 6/3", "primary anchor P"],
        "statement": "The approved seed is required only for Task C and does not make seed atoms fixed nodes.",
    },
    {
        "rule_id": "R10_OBSERVED_DISTANCE_SEPARATION",
        "provenance_kind": "PROPOSED_SCOPED_POLICY_V1_FROM_VALIDATED_FIELDS",
        "owner_or_scope": POLICY_SCOPE_ID,
        "fields": ["observed_complex_pair_distance", "geometry target/valid/loss"],
        "statement": "Observed complex C2-SG distance is evidence/input metadata, never PRE/POST training target authority.",
    },
    {
        "rule_id": "R11_GEOMETRY_EXCLUDED",
        "provenance_kind": "PROPOSED_SCOPED_POLICY_V1",
        "owner_or_scope": POLICY_SCOPE_ID,
        "fields": ["NaN geometry target", "valid=false", "loss=false"],
        "statement": "Missing PRE/POST geometry is allowed only because geometry is excluded from this scope.",
    },
    {
        "rule_id": "R12_INACTIVE_BOUNDARY",
        "provenance_kind": "PUBLISHED_OWNER_FIELDS",
        "owner_or_scope": "validated inactive adapter payload",
        "fields": ["sample_training_admitted=false", "all active-loss masks=false"],
        "statement": "Candidate eligibility must not mutate admission or loss activation.",
    },
)


def _rule(rule_id: str, passed: bool, good: str, bad: str) -> dict[str, object]:
    if type(passed) is not bool:
        _fail("RULE_RESULT_EXACT_BOOL_REQUIRED:" + rule_id)
    return {"rule_id": rule_id, "passed": passed, "reason": good if passed else bad}


def evaluate_scoped_event_task_facts_v1(
    facts: ScopedEventTaskFactsV1,
) -> dict[str, object]:
    """Pure fact-layer evaluation; this helper cannot establish source admission."""

    if type(facts) is not ScopedEventTaskFactsV1:
        _fail("EXACT_FACTS_TYPE_REQUIRED")
    if any(
        type(getattr(facts, name)) is not bool
        for name in (
            "source_bound", "target_population_member", "human_review_completed",
            "human_training_excluded", "explicit_covalent_event",
            "formal_split_authoritative",
            "formal_sample_training_admitted_preserved_false",
            "exact10_feature_inputs_valid",
            "role_partition_and_reactive_indices_valid",
            "source_local_flat_mapping_valid", "seed_mapping_valid",
            "pair_indices_sample_local",
            "observed_complex_distance_finite_and_valid",
            "inactive_admission_and_loss_masks",
        )
    ) or any(
        type(getattr(facts, name)) is not int
        for name in (
            "canonical_task_id", "generated_count", "fixed_count", "seed_count",
            "pair_candidate_count", "pair_positive_count", "pair_negative_count",
            "geometry_nan_component_count", "geometry_valid_component_count",
            "geometry_loss_component_count",
        )
    ):
        _fail("FACT_STRICT_BOOL_OR_INT_REQUIRED")
    if not 0 <= facts.canonical_task_id < len(CANONICAL_TASKS_V1):
        _fail("FACT_CANONICAL_TASK_ID_INVALID")
    task = CANONICAL_TASKS_V1[facts.canonical_task_id]
    task_id, task_name, alias, generated, fixed, seed = task
    task_identity = (
        facts.canonical_task_id == task_id
        and facts.canonical_task_name == task_name
        and facts.canonical_task_alias == alias
    )
    rules = [
        _rule("R01_FIXED_SOURCE_BINDING", facts.source_bound,
              "Fixed published sources were revalidated.",
              "No source-bound evidence; PASS text alone is insufficient."),
        _rule("R02_EXACT8_TARGET_INTERSECTION", facts.target_population_member,
              "Event is in the exact four-way 4I3U intersection.",
              "Event is EXCLUDE, held out, or merely an unapproved same-group member."),
        _rule("R03_HUMAN_INCLUDE_NONEXCLUDE",
              facts.human_review_completed
              and facts.training_use_disposition == "INCLUDE"
              and not facts.human_training_excluded,
              "Published human decision is INCLUDE and non-EXCLUDE.",
              "Published human INCLUDE and non-EXCLUDE evidence is not both present."),
        _rule("R04_FORMAL_TRAIN_GROUP",
              facts.formal_group_id == FORMAL_GROUP_ID
              and facts.formal_split == "train"
              and facts.formal_split_authoritative
              and facts.formal_sample_training_admitted_preserved_false,
              "Authoritative train-group membership is present while reservation remains non-admission.",
              "Authoritative formal train-group membership or preserved reservation is missing."),
        _rule("R05_EXPLICIT_COVALENT_PAIR", facts.explicit_covalent_event,
              "Explicit POA C2 to CYS SG event authority is present.",
              "Explicit covalent event evidence is missing."),
        _rule("R06_EXACT10_AND_INDEX_MAPPING",
              facts.exact10_feature_inputs_valid and facts.source_local_flat_mapping_valid,
              "Exact10 channels and source/local/flat indices are coherent.",
              "Feature channels or source/local/flat indices are incoherent."),
        _rule("R07_CANONICAL5_ROLE_MASKS",
              task_identity
              and facts.role_partition_and_reactive_indices_valid
              and (facts.generated_count, facts.fixed_count) == (generated, fixed),
              "Canonical long-name role partition and generated/fixed masks match.",
              "Canonical task identity, role partition, or generated/fixed masks mismatch."),
        _rule("R08_PAIR_DOMAIN_SCOPED_ELIGIBILITY",
              facts.pair_candidate_count == 42
              and facts.pair_positive_count == 1
              and facts.pair_negative_count == 41
              and facts.pair_indices_sample_local,
              "Pair domain has one positive and 41 sample-local negatives.",
              "Pair positive/negative domain or sample-local endpoint mapping is insufficient."),
        _rule("R09_TASK_C_SIGNED_SEED",
              (facts.seed_count == seed and facts.seed_mapping_valid)
              if task_id == 4 else facts.seed_count == 0,
              "Signed P/O1P seed is valid for Task C." if task_id == 4
              else "Seed is correctly not required for this non-C task.",
              "Task C signed seed mapping is absent or invalid." if task_id == 4
              else "A non-C task unexpectedly depends on seed authority."),
        _rule("R10_OBSERVED_DISTANCE_SEPARATION",
              facts.observed_complex_distance_finite_and_valid,
              "Observed complex reactive-pair distance is valid evidence, not a geometry target.",
              "Observed complex reactive-pair distance evidence is unavailable or invalid."),
        _rule("R11_GEOMETRY_EXCLUDED",
              facts.geometry_nan_component_count == 2
              and facts.geometry_valid_component_count == 0
              and facts.geometry_loss_component_count == 0,
              "Both unavailable geometry components are NaN with valid/loss false.",
              "Geometry was fabricated, marked valid, or activated as a loss target."),
        _rule("R12_INACTIVE_BOUNDARY", facts.inactive_admission_and_loss_masks,
              "Admission and every active-loss mask remain false.",
              "Admission or an active-loss mask was enabled."),
    ]
    passed = {row["rule_id"]: row["passed"] for row in rules}
    common = all(
        passed[rule]
        for rule in (
            "R01_FIXED_SOURCE_BINDING", "R02_EXACT8_TARGET_INTERSECTION",
            "R03_HUMAN_INCLUDE_NONEXCLUDE", "R04_FORMAL_TRAIN_GROUP",
            "R05_EXPLICIT_COVALENT_PAIR", "R06_EXACT10_AND_INDEX_MAPPING",
            "R07_CANONICAL5_ROLE_MASKS", "R11_GEOMETRY_EXCLUDED",
            "R12_INACTIVE_BOUNDARY",
        )
    )
    base = common
    pair = common and passed["R08_PAIR_DOMAIN_SCOPED_ELIGIBILITY"]
    pair_prediction = pair and passed["R10_OBSERVED_DISTANCE_SEPARATION"]
    seed_eligible = common and passed["R09_TASK_C_SIGNED_SEED"]
    all_required = pair_prediction and passed["R09_TASK_C_SIGNED_SEED"]
    return {
        "canonical_event_id": facts.canonical_event_id,
        "canonical_task_id": facts.canonical_task_id,
        "canonical_task_name": facts.canonical_task_name,
        "canonical_task_alias": facts.canonical_task_alias,
        "candidate_status": ELIGIBLE if all_required else BLOCKED,
        "eligibility": {
            "base_diffusion_inputs": ELIGIBLE if base else BLOCKED,
            "covalent_pair_prediction": ELIGIBLE if pair_prediction else BLOCKED,
            "pair_contrastive": ELIGIBLE if pair else BLOCKED,
            "task_c_seed_condition": (
                ELIGIBLE if seed_eligible else BLOCKED
            ) if task_id == 4 else NOT_APPLICABLE,
        },
        "facts": asdict(facts),
        "rule_results": rules,
        "blocked_reasons": [row["reason"] for row in rules if not row["passed"]],
    }


def _source_projection(
    context: POA4I3UExact8NongeometryAdmissionEvaluationContextV1,
) -> dict[str, object]:
    ingestion_projection = context.prepared.published_ingestion_result[
        "semantic_projection"
    ]
    signed = ingestion_projection["signed_decision_identity"]
    state_sources = [
        {
            "artifact_role": "formal_human_role_and_training_use_decision",
            "path_namespace": "covapie_state_root_relative",
            "path": b1_owner.FORMAL_DECISION_STATE_RELATIVE.as_posix(),
            "byte_count": len(context.prepared.formal_decision_payload),
            "sha256": _sha256(context.prepared.formal_decision_payload),
        },
        {
            "artifact_role": "4I3U_real_structure_cpu_input",
            "path_namespace": "covapie_state_root_relative",
            "path": b1_owner.STRUCTURE_STATE_RELATIVE.as_posix(),
            "byte_count": len(context.prepared.structure_payload_4i3u),
            "sha256": _sha256(context.prepared.structure_payload_4i3u),
        },
        {
            "artifact_role": "signed_task_c_seed_anchor_decision",
            "path_namespace": signed["path_namespace"],
            "path": signed["path"],
            "byte_count": signed["bytes"],
            "sha256": signed["sha256"],
        },
    ]
    return {
        "direct_policy_and_owner_bindings": [
            asdict(row) for row in context.direct_source_bindings
        ],
        "inactive_adapter_transitive_repository_bindings": [
            asdict(row) for row in context.prepared.source_bindings
        ],
        "formal_split_repository_bindings": [
            asdict(row) for row in context.formal_split_result.source_bindings
        ],
        "state_source_bindings": state_sources,
        "structure_source_bindings": [
            asdict(row) for row in context.payloads[0].structure_source_bindings
        ],
    }


FEATURE_USE_AUDIT_V1 = (
    {
        "subject": "element_channels",
        "actual_fields": ["lig_one_hot", "pocket_one_hot"],
        "checked_use": "source-aligned exact10 one-hot model inputs for scoped base diffusion",
        "boundary": "No new element vocabulary or unknown-atom policy is created.",
    },
    {
        "subject": "roles_and_masks",
        "actual_fields": ["ligand_role_id", "ligand_role_valid", "generation_mask", "fixed_mask"],
        "checked_use": "canonical five structural generation/fixed domains; B3 retained",
        "boundary": "Eligibility is separate from ligand_active_diffusion_loss_mask.",
    },
    {
        "subject": "indices",
        "actual_fields": ["source_atom_site_row", "parser/sample-local", "batch-flat"],
        "checked_use": "identity-preserving ligand, pocket, reactive pair, and seed mapping",
        "boundary": "B1-flat indices are valid only for this fixed prepared batch.",
    },
    {
        "subject": "task_c_seed",
        "actual_fields": ["P/O1P local 6/3", "primary anchor P", "seed mask"],
        "checked_use": "Task C conditional seed eligibility",
        "boundary": "Seed does not become a fixed-node mask and P is not the protein SG distance reference.",
    },
    {
        "subject": "reactive_pair_and_domains",
        "actual_fields": ["POA C2", "CYS SG", "pair candidates/labels/indices"],
        "checked_use": "pair prediction and within-event contrastive candidate eligibility",
        "boundary": "Loss masks remain false; this is not runtime activation.",
    },
    {
        "subject": "coordinates_and_distance",
        "actual_fields": ["observed complex coordinates", "observed C2-SG distance", "PRE/POST target"],
        "checked_use": "observed complex geometry may remain a base input/evidence field",
        "boundary": "PRE/POST targets stay NaN with valid/loss false; observed distance grants no geometry authority.",
    },
)


def _compile_result_impl(
    context: POA4I3UExact8NongeometryAdmissionEvaluationContextV1,
) -> dict[str, object]:
    rows = [
        evaluate_scoped_event_task_facts_v1(
            _facts_for(context, sample=sample, payload=payload)
        )
        for sample in range(8)
        for payload in context.payloads
    ]
    eligible_count = sum(row["candidate_status"] == ELIGIBLE for row in rows)
    semantic_projection: dict[str, object] = {
        "policy_scope_id": POLICY_SCOPE_ID,
        "scope_statement": (
            "Current 4I3U Exact8, published-source-bound, canonical-five non-geometry "
            "data-use eligibility only; not formal admission or runtime acceptance."
        ),
        "baseline_commit": BASELINE_COMMIT,
        "source_bindings": _source_projection(context),
        "rule_definitions": copy.deepcopy(list(RULE_DEFINITIONS_V1)),
        "formal_population": {
            "formal_group_id": context.formal_split_result.formal_group_id,
            "formal_split": context.formal_split_result.formal_split,
            "formal_split_authoritative": context.formal_split_result.formal_split_authoritative,
            "full_component_event_count": len(
                context.formal_split_result.full_member_canonical_event_ids
            ),
            "full_component_identity_count": len(
                context.formal_split_result.full_member_pdb_ligand_identities
            ),
            "sample_training_admitted_preserved": context.formal_split_result.sample_training_admitted,
            "target_event_ids": list(context.target_event_ids),
            "excluded_population_statement": (
                "4I3V Exact8 remains EXCLUDE_FROM_TRAINING_ONLY; 4I3W/G3H has no "
                "sample admission basis in this scope; neither is evaluated as a target."
            ),
        },
        "event_task_records": rows,
        "summary": {
            "event_count": 8,
            "canonical_task_count": 5,
            "event_task_record_count": len(rows),
            "eligible_event_task_record_count": eligible_count,
            "blocked_event_task_record_count": len(rows) - eligible_count,
            "batch_status": (
                "ALL_40_ELIGIBLE_FOR_SCOPED_NON_GEOMETRY_USE"
                if eligible_count == 40
                else "PARTIAL_OR_FULL_BATCH_BLOCKED"
            ),
            "pair_candidate_count": context.payloads[0].summary.pair_candidate_count,
            "pair_positive_count": context.payloads[0].summary.pair_positive_count,
            "pair_negative_count": context.payloads[0].summary.pair_negative_count,
            "total_pocket_node_count": context.payloads[0].summary.total_pocket_node_count,
            "geometry_nan_component_count_per_payload": context.payloads[0].summary.geometry_nan_component_count,
            "geometry_valid_component_count_per_payload": context.payloads[0].summary.geometry_valid_component_count,
            "geometry_loss_component_count_per_payload": context.payloads[0].summary.geometry_loss_component_count,
        },
        "feature_semantics_and_use_check": copy.deepcopy(
            list(FEATURE_USE_AUDIT_V1)
        ),
        "explicitly_unavailable_supervision": [
            "PRE_geometry_training_supervision",
            "POST_geometry_training_supervision",
            "warhead_type_classification_target",
            "reaction_family_target",
            "reusable_warhead_rule_target",
            "chemistry_state_target",
            "new_reaction_mechanism_ground_truth",
            "precursor_ground_truth",
        ],
        "operations_not_executed": [
            "formal_admission_activation", "active_loss_activation", "model_forward",
            "production_loss", "backward", "optimizer_or_trainer", "parameter_update",
            "checkpoint_access", "train12_population_change", "publication",
        ],
        "permission_boundary": dict(PERMISSION_BOUNDARY_V1),
        "execution_accounting": {
            "formal_split_build_public": 1,
            "formal_split_validate_public_explicit": 1,
            "inactive_adapter_prepare_public": 1,
            "inactive_prepare_internal_call_counts": [
                list(row) for row in context.prepared.source_validation_call_counts
            ],
            "inactive_payload_build_public": 5,
            "inactive_payload_validate_public_explicit": 5,
            "structure_parse_count_reported_by_b1_prepare_and_validator": 16,
            "result_compile_uses_existing_context_without_prepare": True,
        },
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "record_role": RECORD_ROLE,
        "semantic_projection": semantic_projection,
        "semantic_projection_sha256": _sha256(
            _canonical_json_bytes(semantic_projection)
        ),
    }


def build_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
    *, context: POA4I3UExact8NongeometryAdmissionEvaluationContextV1
) -> dict[str, object]:
    """Compile one isolated deterministic candidate result without preparing again."""

    try:
        checked = _validate_context(context)
        return _compile_result_impl(checked)
    except POA4I3UExact8NongeometryAdmissionEvaluatorError:
        raise
    except Exception as error:
        raise POA4I3UExact8NongeometryAdmissionEvaluatorError(
            f"{ERROR_TOKEN}:PUBLIC_BUILD_REJECTED:{type(error).__name__}:{error}"
        ) from error


def validate_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
    *, result: object,
    context: POA4I3UExact8NongeometryAdmissionEvaluationContextV1,
) -> bool:
    """Revalidate fixed sources and facts, then compare the complete result."""

    try:
        checked = _validate_context(context)
        if type(result) is not dict or set(result) != {
            "schema_version", "record_role", "semantic_projection",
            "semantic_projection_sha256",
        } or len(result) != 4:
            _fail("RESULT_EXACT_SCHEMA_REQUIRED")
        projection = result.get("semantic_projection")
        if (
            type(projection) is not dict
            or type(result.get("semantic_projection_sha256")) is not str
            or result["semantic_projection_sha256"]
            != _sha256(_canonical_json_bytes(projection))
        ):
            _fail("RESULT_SEMANTIC_PROJECTION_DIGEST_INVALID")
        expected = _compile_result_impl(checked)
        if not _strict_equal(result, expected):
            _fail("RESULT_SOURCE_AND_FACT_RECOMPUTATION_MISMATCH")
        return True
    except POA4I3UExact8NongeometryAdmissionEvaluatorError:
        raise
    except Exception as error:
        raise POA4I3UExact8NongeometryAdmissionEvaluatorError(
            f"{ERROR_TOKEN}:PUBLIC_VALIDATION_REJECTED:"
            f"{type(error).__name__}:{error}"
        ) from error


def serialize_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
    *, result: object,
    context: POA4I3UExact8NongeometryAdmissionEvaluationContextV1,
) -> bytes:
    """Serialize only after complete source/fact revalidation."""

    validate_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
        result=result, context=context
    )
    return _canonical_json_bytes(result, newline=True)
