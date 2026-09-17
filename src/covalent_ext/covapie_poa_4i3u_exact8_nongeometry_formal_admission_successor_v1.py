"""Source-bound formal-admission successor for POA 4I3U Exact8.

This module consumes the published non-geometry admission evaluation.  It does
not repeat that evaluator's R01--R12 formulas, alter any inactive payload, make
the candidate effective, or connect a training consumer.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, replace
import hashlib
import json
from pathlib import Path
import stat
import subprocess
from typing import NoReturn

from covalent_ext import (
    covapie_poa_4i3u_exact8_nongeometry_admission_evaluator_v1
    as evaluation_owner,
)


__all__ = (
    "POA4I3UExact8NongeometryFormalAdmissionSuccessorError",
    "POA4I3UExact8NongeometryFormalAdmissionSuccessorContextV1",
    "prepare_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1",
    "build_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1",
    "validate_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1",
    "serialize_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1",
    "materialize_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1",
    "query_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1",
)


TASK_ID = (
    "implement_covapie_poa_4i3u_exact8_nongeometry_"
    "formal_admission_successor_v1"
)
SCHEMA_VERSION = (
    "covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1"
)
POLICY_SCOPE_ID = (
    "POA_4I3U_EXACT8_CANONICAL5_NONGEOMETRY_"
    "FORMAL_ADMISSION_SUCCESSOR_SCOPE_V1"
)
POLICY_VERSION = "v1"
RECORD_ROLE = "UNPUBLISHED_SOURCE_BOUND_FORMAL_ADMISSION_SUCCESSOR_CANDIDATE"
ERROR_TOKEN = (
    "COVAPIE_POA_4I3U_EXACT8_NONGEOMETRY_"
    "FORMAL_ADMISSION_SUCCESSOR_V1_ERROR"
)

BASELINE_COMMIT = "ca28e3749ae08caf7af9f16273b79e2be46f87b3"
FORMAL_GROUP_ID = "COVAPIE_EXPANSION_LEAKAGE_GROUP_F70DB37A8004AF17"
FORMAL_SPLIT = "train"
SOURCE_EVALUATION_SCHEMA = (
    "covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1"
)
SOURCE_EVALUATION_SCOPE = (
    "POA_4I3U_EXACT8_CANONICAL5_NONGEOMETRY_USE_SCOPE_V1"
)
SOURCE_EVALUATION_SEMANTIC_SHA256 = (
    "7fe0fccabf353c81d67e73a83500830e231703597ada3c6293277d8ddda73925"
)
SOURCE_ELIGIBLE = "ELIGIBLE_FOR_SCOPED_NON_GEOMETRY_USE"
SOURCE_BLOCKED = "BLOCKED_FOR_SCOPED_NON_GEOMETRY_USE"
SOURCE_NOT_APPLICABLE = "NOT_APPLICABLE_TO_CANONICAL_TASK"
ADMIT_SCOPED = "ADMIT_SCOPED_NON_GEOMETRY_ONLY"
USE_GRANTED = "GRANTED_SCOPED_NON_GEOMETRY_USE"
USE_NOT_APPLICABLE = "NOT_GRANTED_NOT_APPLICABLE_TO_CANONICAL_TASK"

CANONICAL_TASKS_V1 = (
    (0, "warhead_only", "A"),
    (1, "linker_plus_warhead", "B"),
    (2, "scaffold_plus_warhead", "B2"),
    (3, "scaffold_only", "B3"),
    (4, "scaffold_plus_linker_plus_warhead", "C"),
)

TARGET_EVENT_IDS_V1 = (
    "COVAPIE_CYS_SG_EVENT_V1:4I3U:A:CYS:291-:SG:I:POA:C2",
    "COVAPIE_CYS_SG_EVENT_V1:4I3U:B:CYS:291-:SG:J:POA:C2",
    "COVAPIE_CYS_SG_EVENT_V1:4I3U:C:CYS:291-:SG:K:POA:C2",
    "COVAPIE_CYS_SG_EVENT_V1:4I3U:D:CYS:291-:SG:L:POA:C2",
    "COVAPIE_CYS_SG_EVENT_V1:4I3U:E:CYS:291-:SG:M:POA:C2",
    "COVAPIE_CYS_SG_EVENT_V1:4I3U:F:CYS:291-:SG:N:POA:C2",
    "COVAPIE_CYS_SG_EVENT_V1:4I3U:G:CYS:291-:SG:O:POA:C2",
    "COVAPIE_CYS_SG_EVENT_V1:4I3U:H:CYS:291-:SG:P:POA:C2",
)

SOURCE_SPECS_V1 = (
    (
        "published_nongeometry_admission_evaluator",
        "src/covalent_ext/"
        "covapie_poa_4i3u_exact8_nongeometry_admission_evaluator_v1.py",
        52834,
        "92b9e4ea6839476575446f48fa21edfce47089aef7c0e5e5b4119ce7f360b235",
        "209540298d6e00597e79b7068a11c17601c4fa50",
    ),
    (
        "published_nongeometry_admission_evaluation",
        "data/derived/covalent_small/"
        "covapie_poa_4i3u_exact8_nongeometry_admission_evaluator_v1/"
        "poa_4i3u_exact8_nongeometry_admission_evaluation_v1.json",
        144300,
        "9d599bca7e1e5b63927051af25307c376cd63bba0053991090822562501f4828",
        "fd548d53b24a8071265bf4f25aba598177777d94",
    ),
)

SOURCE_RULE_IDS_V1 = tuple(f"R{number:02d}_{suffix}" for number, suffix in (
    (1, "FIXED_SOURCE_BINDING"),
    (2, "EXACT8_TARGET_INTERSECTION"),
    (3, "HUMAN_INCLUDE_NONEXCLUDE"),
    (4, "FORMAL_TRAIN_GROUP"),
    (5, "EXPLICIT_COVALENT_PAIR"),
    (6, "EXACT10_AND_INDEX_MAPPING"),
    (7, "CANONICAL5_ROLE_MASKS"),
    (8, "PAIR_DOMAIN_SCOPED_ELIGIBILITY"),
    (9, "TASK_C_SIGNED_SEED"),
    (10, "OBSERVED_DISTANCE_SEPARATION"),
    (11, "GEOMETRY_EXCLUDED"),
    (12, "INACTIVE_BOUNDARY"),
))

COMMON_USE_RULE_IDS_V1 = (
    "R01_FIXED_SOURCE_BINDING",
    "R02_EXACT8_TARGET_INTERSECTION",
    "R03_HUMAN_INCLUDE_NONEXCLUDE",
    "R04_FORMAL_TRAIN_GROUP",
    "R05_EXPLICIT_COVALENT_PAIR",
    "R06_EXACT10_AND_INDEX_MAPPING",
    "R07_CANONICAL5_ROLE_MASKS",
    "R11_GEOMETRY_EXCLUDED",
    "R12_INACTIVE_BOUNDARY",
)
USE_REQUIREMENTS_V1 = (
    ("base_diffusion_inputs", COMMON_USE_RULE_IDS_V1),
    (
        "covalent_pair_prediction",
        COMMON_USE_RULE_IDS_V1
        + ("R08_PAIR_DOMAIN_SCOPED_ELIGIBILITY", "R10_OBSERVED_DISTANCE_SEPARATION"),
    ),
    (
        "pair_contrastive",
        COMMON_USE_RULE_IDS_V1 + ("R08_PAIR_DOMAIN_SCOPED_ELIGIBILITY",),
    ),
    (
        "task_c_seed_condition",
        COMMON_USE_RULE_IDS_V1 + ("R09_TASK_C_SIGNED_SEED",),
    ),
)

PROHIBITED_USE_DEFINITIONS_V1 = (
    (
        "PRE_geometry_training_supervision",
        "No PRE geometry target, validity, or loss authority is granted.",
    ),
    (
        "POST_geometry_training_supervision",
        "No POST geometry target, validity, or loss authority is granted.",
    ),
    ("warhead_type", "No warhead-type target or reusable label is granted."),
    ("reaction_family", "No reaction-family target is granted."),
    ("reusable_warhead_rule", "No reusable warhead rule is created."),
    ("chemistry_state", "No chemistry-state ground truth is granted."),
    ("precursor_ground_truth", "No precursor ground truth is granted."),
    ("mechanism_ground_truth", "No reaction-mechanism ground truth is granted."),
    ("model_execution", "No model forward, loss, or training execution is granted."),
    ("parameter_update", "No backward, optimizer, or parameter update is granted."),
    ("weight_save", "No model-weight or checkpoint save is granted."),
)

EXECUTION_CONDITIONS_V1 = (
    (
        "C01_EXTERNAL_REVIEW_AND_PUBLICATION_REQUIRED",
        "This candidate must be externally reviewed and published before it can become effective.",
    ),
    (
        "C02_FEATURE_SEMANTICS_AND_USE_AUDIT_REQUIRED",
        "An active consumer requires a feature-semantics and intended-use audit.",
    ),
    (
        "C03_UNKNOWN_ATOM_FEATURE_POLICY_MUST_BE_RESOLVED_OR_AUDITED",
        "UNKNOWN_ATOM_FEATURE_POLICY and feature_semantics_known=False remain unresolved.",
    ),
    (
        "C04_ACTIVE_CONSUMER_INTEGRATION_REQUIRES_SEPARATE_AUTHORITY",
        "Consumer wiring, tensor loss masks, and runtime activation require separate authority.",
    ),
    (
        "C05_STEP12D_REMAINS_SMOKE_ONLY",
        "Step12D proves smoke legality only, not a final training-feature contract.",
    ),
)

PERMISSION_BOUNDARY_V1 = {
    "FORMAL_ADMISSION_SUCCESSOR_CANDIDATE_CREATED": True,
    "FORMAL_ADMISSION_EFFECTIVE": False,
    "NEW_HUMAN_DECISION_CREATED": False,
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


class POA4I3UExact8NongeometryFormalAdmissionSuccessorError(ValueError):
    """Raised when fixed sources or the exact successor contract fail closed."""


def _fail(reason: str) -> NoReturn:
    raise POA4I3UExact8NongeometryFormalAdmissionSuccessorError(
        f"{ERROR_TOKEN}:{reason}"
    )


@dataclass(frozen=True, slots=True)
class SourceBindingV1:
    artifact_role: str
    path_namespace: str
    path: str
    byte_count: int
    sha256: str
    git_blob_sha1: str


@dataclass(frozen=True)
class POA4I3UExact8NongeometryFormalAdmissionSuccessorContextV1:
    repository_root: Path
    state_root: Path
    source_bindings: tuple[SourceBindingV1, ...]
    evaluation_context: (
        evaluation_owner.POA4I3UExact8NongeometryAdmissionEvaluationContextV1
    )
    frozen_evaluation_result: dict[str, object]
    frozen_evaluation_bytes: bytes
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
    try:
        path = Path(value).resolve(strict=True)
    except OSError as error:
        raise POA4I3UExact8NongeometryFormalAdmissionSuccessorError(
            f"{ERROR_TOKEN}:{label}_PATH_UNAVAILABLE:{type(error).__name__}"
        ) from error
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


def _validate_baseline_lineage(repository: Path) -> None:
    try:
        if _git(repository, "cat-file", "-t", BASELINE_COMMIT) != "commit":
            _fail("BASELINE_OBJECT_IS_NOT_COMMIT")
        completed = subprocess.run(
            (
                "git", "-C", str(repository), "merge-base", "--is-ancestor",
                BASELINE_COMMIT, "HEAD",
            ),
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except POA4I3UExact8NongeometryFormalAdmissionSuccessorError:
        raise
    except Exception as error:
        raise POA4I3UExact8NongeometryFormalAdmissionSuccessorError(
            f"{ERROR_TOKEN}:BASELINE_LINEAGE_UNAVAILABLE:{type(error).__name__}"
        ) from error
    if completed.returncode == 1:
        _fail("BASELINE_IS_NOT_ANCESTOR_OF_HEAD")
    if completed.returncode != 0:
        _fail("BASELINE_ANCESTRY_GIT_COMMAND_FAILED")


def _read_regular(path: Path, reason: str) -> bytes:
    try:
        status = path.lstat()
    except OSError as error:
        raise POA4I3UExact8NongeometryFormalAdmissionSuccessorError(
            f"{ERROR_TOKEN}:{reason}_UNREADABLE:{type(error).__name__}"
        ) from error
    if not stat.S_ISREG(status.st_mode) or path.is_symlink():
        _fail(reason + "_REGULAR_NONSYMLINK_REQUIRED")
    try:
        return path.read_bytes()
    except OSError as error:
        raise POA4I3UExact8NongeometryFormalAdmissionSuccessorError(
            f"{ERROR_TOKEN}:{reason}_UNREADABLE:{type(error).__name__}"
        ) from error


def _fixed_source_bindings(repository: Path) -> tuple[SourceBindingV1, ...]:
    _validate_baseline_lineage(repository)
    rows: list[SourceBindingV1] = []
    for role, relative, byte_count, digest, blob in SOURCE_SPECS_V1:
        try:
            committed_blob = _git(
                repository, "rev-parse", f"{BASELINE_COMMIT}:{relative}"
            )
        except Exception as error:
            raise POA4I3UExact8NongeometryFormalAdmissionSuccessorError(
                f"{ERROR_TOKEN}:FIXED_SOURCE_GIT_BLOB_UNAVAILABLE:"
                f"{relative}:{type(error).__name__}"
            ) from error
        payload = _read_regular(repository / relative, "FIXED_SOURCE")
        if (
            committed_blob != blob
            or len(payload) != byte_count
            or _sha256(payload) != digest
        ):
            _fail("FIXED_SOURCE_IDENTITY_MISMATCH:" + relative)
        rows.append(SourceBindingV1(
            artifact_role=role,
            path_namespace="repository_root_relative",
            path=relative,
            byte_count=byte_count,
            sha256=digest,
            git_blob_sha1=blob,
        ))
    return tuple(rows)


def _parse_json_object(payload: bytes, reason: str) -> dict[str, object]:
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise POA4I3UExact8NongeometryFormalAdmissionSuccessorError(
            f"{ERROR_TOKEN}:{reason}_JSON_INVALID:{type(error).__name__}"
        ) from error
    if type(value) is not dict:
        _fail(reason + "_JSON_OBJECT_REQUIRED")
    return value


def _context_projection(
    context: POA4I3UExact8NongeometryFormalAdmissionSuccessorContextV1,
) -> dict[str, object]:
    return {
        "source_bindings": [asdict(row) for row in context.source_bindings],
        "evaluation_context_seal_sha256": context.evaluation_context.context_seal_sha256,
        "frozen_evaluation_sha256": _sha256(context.frozen_evaluation_bytes),
        "frozen_evaluation_semantic_sha256": context.frozen_evaluation_result.get(
            "semantic_projection_sha256"
        ),
        "target_event_ids": list(context.target_event_ids),
    }


def _validate_context(
    value: object,
) -> POA4I3UExact8NongeometryFormalAdmissionSuccessorContextV1:
    if type(value) is not POA4I3UExact8NongeometryFormalAdmissionSuccessorContextV1:
        _fail("EXACT_CONTEXT_TYPE_REQUIRED")
    context = value
    if (
        context.repository_root != context.repository_root.resolve(strict=True)
        or context.state_root != context.state_root.resolve(strict=True)
        or context.repository_root == context.state_root
        or context.source_bindings != _fixed_source_bindings(context.repository_root)
        or type(context.frozen_evaluation_bytes) is not bytes
        or type(context.frozen_evaluation_result) is not dict
        or type(context.target_event_ids) is not tuple
        or context.context_seal_sha256
        != _sha256(_canonical_json_bytes(_context_projection(context)))
    ):
        _fail("CONTEXT_HEADER_SOURCE_OR_SEAL_INVALID")

    result_binding = context.source_bindings[1]
    current_bytes = _read_regular(
        context.repository_root / result_binding.path,
        "PUBLISHED_EVALUATION",
    )
    if current_bytes != context.frozen_evaluation_bytes:
        _fail("PUBLISHED_EVALUATION_BYTES_CHANGED")
    current_result = _parse_json_object(current_bytes, "PUBLISHED_EVALUATION")
    if not _strict_equal(current_result, context.frozen_evaluation_result):
        _fail("PUBLISHED_EVALUATION_CONTEXT_COPY_CHANGED")
    try:
        if not evaluation_owner.validate_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
            result=current_result,
            context=context.evaluation_context,
        ):
            _fail("PUBLISHED_EVALUATION_PUBLIC_VALIDATOR_REJECTED")
        serialized = evaluation_owner.serialize_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
            result=current_result,
            context=context.evaluation_context,
        )
    except POA4I3UExact8NongeometryFormalAdmissionSuccessorError:
        raise
    except Exception as error:
        raise POA4I3UExact8NongeometryFormalAdmissionSuccessorError(
            f"{ERROR_TOKEN}:PUBLISHED_EVALUATION_REVALIDATION_REJECTED:"
            f"{type(error).__name__}:{error}"
        ) from error
    if serialized != current_bytes:
        _fail("PUBLISHED_EVALUATION_CANONICAL_BYTES_MISMATCH")
    projection = current_result.get("semantic_projection")
    if (
        current_result.get("schema_version") != SOURCE_EVALUATION_SCHEMA
        or current_result.get("semantic_projection_sha256")
        != SOURCE_EVALUATION_SEMANTIC_SHA256
        or type(projection) is not dict
        or projection.get("policy_scope_id") != SOURCE_EVALUATION_SCOPE
        or projection.get("formal_population", {}).get("target_event_ids")
        != list(context.target_event_ids)
        or tuple(context.evaluation_context.target_event_ids)
        != context.target_event_ids
        or context.target_event_ids != TARGET_EVENT_IDS_V1
    ):
        _fail("PUBLISHED_EVALUATION_FIXED_SCOPE_INVALID")
    return context


def prepare_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
    *, repository_root: Path | str, state_root: Path | str
) -> POA4I3UExact8NongeometryFormalAdmissionSuccessorContextV1:
    """Prepare the published evaluator once and bind its frozen result."""

    try:
        repository = _resolve_root(repository_root, "REPOSITORY_ROOT")
        state = _resolve_root(state_root, "STATE_ROOT")
        if repository == state:
            _fail("REPOSITORY_AND_STATE_ROOT_MUST_DIFFER")
        bindings = _fixed_source_bindings(repository)
        evaluation_context = evaluation_owner.prepare_covapie_poa_4i3u_exact8_nongeometry_admission_evaluator_v1(
            repository_root=repository,
            state_root=state,
        )
        evaluation_bytes = _read_regular(
            repository / bindings[1].path,
            "PUBLISHED_EVALUATION",
        )
        evaluation_result = _parse_json_object(
            evaluation_bytes, "PUBLISHED_EVALUATION"
        )
        if not evaluation_owner.validate_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
            result=evaluation_result,
            context=evaluation_context,
        ):
            _fail("PUBLISHED_EVALUATION_PUBLIC_VALIDATOR_REJECTED")
        if evaluation_owner.serialize_covapie_poa_4i3u_exact8_nongeometry_admission_evaluation_v1(
            result=evaluation_result,
            context=evaluation_context,
        ) != evaluation_bytes:
            _fail("PUBLISHED_EVALUATION_CANONICAL_BYTES_MISMATCH")
        unsealed = POA4I3UExact8NongeometryFormalAdmissionSuccessorContextV1(
            repository_root=repository,
            state_root=state,
            source_bindings=bindings,
            evaluation_context=evaluation_context,
            frozen_evaluation_result=copy.deepcopy(evaluation_result),
            frozen_evaluation_bytes=bytes(evaluation_bytes),
            target_event_ids=tuple(evaluation_context.target_event_ids),
            context_seal_sha256="",
        )
        context = replace(
            unsealed,
            context_seal_sha256=_sha256(
                _canonical_json_bytes(_context_projection(unsealed))
            ),
        )
        return _validate_context(context)
    except POA4I3UExact8NongeometryFormalAdmissionSuccessorError:
        raise
    except Exception as error:
        raise POA4I3UExact8NongeometryFormalAdmissionSuccessorError(
            f"{ERROR_TOKEN}:PUBLIC_PREPARE_REJECTED:{type(error).__name__}:{error}"
        ) from error


def _exact_dict(value: object, keys: set[str], reason: str) -> dict[str, object]:
    if type(value) is not dict or set(value) != keys or len(value) != len(keys):
        _fail(reason + "_EXACT_SCHEMA_REQUIRED")
    return value


def _derive_successor_from_verified_evaluation(
    evaluation: object,
) -> dict[str, object]:
    """Map an already verified evaluation; never establishes source truth itself."""

    source = _exact_dict(
        evaluation,
        {"schema_version", "record_role", "semantic_projection", "semantic_projection_sha256"},
        "SOURCE_EVALUATION",
    )
    if (
        source["schema_version"] != SOURCE_EVALUATION_SCHEMA
        or source["semantic_projection_sha256"] != SOURCE_EVALUATION_SEMANTIC_SHA256
    ):
        _fail("SOURCE_EVALUATION_FIXED_IDENTITY_INVALID")
    projection = source["semantic_projection"]
    if type(projection) is not dict or projection.get("policy_scope_id") != SOURCE_EVALUATION_SCOPE:
        _fail("SOURCE_EVALUATION_SCOPE_INVALID")
    population = projection.get("formal_population")
    if type(population) is not dict:
        _fail("SOURCE_FORMAL_POPULATION_REQUIRED")
    target_ids = population.get("target_event_ids")
    if (
        type(target_ids) is not list
        or len(target_ids) != 8
        or any(type(item) is not str for item in target_ids)
        or len(set(target_ids)) != 8
        or tuple(target_ids) != TARGET_EVENT_IDS_V1
        or population.get("formal_group_id") != FORMAL_GROUP_ID
        or population.get("formal_split") != FORMAL_SPLIT
        or population.get("formal_split_authoritative") is not True
        or type(population.get("full_component_event_count")) is not int
        or population.get("full_component_event_count") != 24
        or population.get("sample_training_admitted_preserved") is not False
    ):
        _fail("SOURCE_FORMAL_POPULATION_SCOPE_INVALID")
    rows = projection.get("event_task_records")
    if type(rows) is not list or len(rows) != 40:
        _fail("SOURCE_EXACT40_RECORDS_REQUIRED")

    expected_keys = [
        (event_id, task_name)
        for event_id in target_ids
        for _, task_name, _ in CANONICAL_TASKS_V1
    ]
    actual_keys: list[tuple[str, str]] = []
    admission_rows: list[dict[str, object]] = []
    for position, source_row in enumerate(rows):
        row = _exact_dict(
            source_row,
            {
                "blocked_reasons", "candidate_status", "canonical_event_id",
                "canonical_task_alias", "canonical_task_id", "canonical_task_name",
                "eligibility", "facts", "rule_results",
            },
            f"SOURCE_RECORD_{position}",
        )
        event_id = row["canonical_event_id"]
        task_id = row["canonical_task_id"]
        task_name = row["canonical_task_name"]
        task_alias = row["canonical_task_alias"]
        if (
            type(event_id) is not str
            or type(task_id) is not int
            or not 0 <= task_id < len(CANONICAL_TASKS_V1)
            or type(task_name) is not str
            or type(task_alias) is not str
        ):
            _fail(f"SOURCE_RECORD_IDENTITY_TYPE_INVALID:{position}")
        canonical_task = CANONICAL_TASKS_V1[task_id]
        if (task_id, task_name, task_alias) != canonical_task:
            _fail(f"SOURCE_RECORD_CANONICAL_TASK_INVALID:{event_id}:{task_name}")
        actual_keys.append((event_id, task_name))

        if row["candidate_status"] != SOURCE_ELIGIBLE:
            _fail(f"SOURCE_RECORD_BLOCKED:{event_id}:{task_name}")
        blocked_reasons = row["blocked_reasons"]
        if type(blocked_reasons) is not list or blocked_reasons:
            _fail(f"SOURCE_RECORD_BLOCKED_REASONS_PRESENT:{event_id}:{task_name}")
        facts = row["facts"]
        if type(facts) is not dict or (
            facts.get("formal_group_id") != FORMAL_GROUP_ID
            or facts.get("formal_split") != FORMAL_SPLIT
            or facts.get("formal_split_authoritative") is not True
            or facts.get("formal_sample_training_admitted_preserved_false") is not True
            or facts.get("inactive_admission_and_loss_masks") is not True
        ):
            _fail(f"SOURCE_RECORD_FORMAL_OR_INACTIVE_BOUNDARY_INVALID:{event_id}:{task_name}")
        eligibility = _exact_dict(
            row["eligibility"],
            {name for name, _ in USE_REQUIREMENTS_V1},
            f"SOURCE_RECORD_ELIGIBILITY_{position}",
        )
        expected_seed = SOURCE_ELIGIBLE if task_id == 4 else SOURCE_NOT_APPLICABLE
        if (
            any(
                type(eligibility[name]) is not str
                for name, _ in USE_REQUIREMENTS_V1
            )
            or eligibility["base_diffusion_inputs"] != SOURCE_ELIGIBLE
            or eligibility["covalent_pair_prediction"] != SOURCE_ELIGIBLE
            or eligibility["pair_contrastive"] != SOURCE_ELIGIBLE
            or eligibility["task_c_seed_condition"] != expected_seed
        ):
            _fail(f"SOURCE_RECORD_REQUIRED_USE_NOT_ELIGIBLE:{event_id}:{task_name}")

        rule_results = row["rule_results"]
        if type(rule_results) is not list or len(rule_results) != len(SOURCE_RULE_IDS_V1):
            _fail(f"SOURCE_RECORD_RULE_COUNT_INVALID:{event_id}:{task_name}")
        rule_basis: list[dict[str, object]] = []
        rule_passed: dict[str, bool] = {}
        for rule_position, source_rule in enumerate(rule_results):
            rule = _exact_dict(
                source_rule,
                {"rule_id", "passed", "reason"},
                f"SOURCE_RULE_{position}_{rule_position}",
            )
            if (
                type(rule["rule_id"]) is not str
                or rule["rule_id"] != SOURCE_RULE_IDS_V1[rule_position]
                or type(rule["passed"]) is not bool
                or type(rule["reason"]) is not str
                or not rule["passed"]
            ):
                _fail(
                    f"SOURCE_RULE_BLOCKED_OR_INVALID:{event_id}:{task_name}:"
                    f"{rule.get('rule_id')}"
                )
            rule_passed[rule["rule_id"]] = rule["passed"]
            rule_basis.append({"rule_id": rule["rule_id"], "passed": True})

        use_decisions: list[dict[str, object]] = []
        allowed_names: list[str] = []
        not_applicable_names: list[str] = []
        for use_name, required_rule_ids in USE_REQUIREMENTS_V1:
            source_status = eligibility[use_name]
            applicable = not (use_name == "task_c_seed_condition" and task_id != 4)
            if applicable:
                if source_status != SOURCE_ELIGIBLE or not all(
                    rule_passed.get(rule_id) is True for rule_id in required_rule_ids
                ):
                    _fail(f"SOURCE_USE_RULE_BASIS_BLOCKED:{event_id}:{task_name}:{use_name}")
                use_decision = USE_GRANTED
                allowed_names.append(use_name)
            else:
                if source_status != SOURCE_NOT_APPLICABLE:
                    _fail(f"SOURCE_USE_NA_STATUS_INVALID:{event_id}:{task_name}:{use_name}")
                use_decision = USE_NOT_APPLICABLE
                not_applicable_names.append(use_name)
            use_decisions.append({
                "use_name": use_name,
                "source_eligibility": source_status,
                "admission_use_decision": use_decision,
                "required_source_rule_ids": list(required_rule_ids),
            })

        admission_rows.append({
            "evaluation_record_key": {
                "canonical_event_id": event_id,
                "canonical_task_name": task_name,
            },
            "canonical_event_id": event_id,
            "canonical_task_id": task_id,
            "canonical_task_name": task_name,
            "canonical_task_alias": task_alias,
            "formal_group_id": FORMAL_GROUP_ID,
            "formal_split": FORMAL_SPLIT,
            "source_candidate_status": row["candidate_status"],
            "source_rule_basis": rule_basis,
            "admission_decision": ADMIT_SCOPED,
            "use_decisions": use_decisions,
            "allowed_use_names": allowed_names,
            "non_applicable_use_names": not_applicable_names,
            "prohibited_use_names": [name for name, _ in PROHIBITED_USE_DEFINITIONS_V1],
            "subsequent_execution_condition_ids": [
                condition_id for condition_id, _ in EXECUTION_CONDITIONS_V1
            ],
        })

    if actual_keys != expected_keys or len(set(actual_keys)) != 40:
        _fail("SOURCE_EXACT8_CANONICAL5_KEY_MATRIX_INVALID")

    source_bindings = [
        {
            "artifact_role": role,
            "path_namespace": "repository_root_relative",
            "path": path,
            "byte_count": byte_count,
            "sha256": sha256,
            "git_blob_sha1": git_blob,
        }
        for role, path, byte_count, sha256, git_blob in SOURCE_SPECS_V1
    ]
    semantic_projection: dict[str, object] = {
        "admission_policy": {
            "policy_scope_id": POLICY_SCOPE_ID,
            "policy_version": POLICY_VERSION,
            "candidate_status": "PROPOSED_FOR_EXTERNAL_REVIEW_AND_PUBLICATION",
            "effective_status": "NOT_EFFECTIVE_UNTIL_REVIEWED_AND_PUBLISHED",
            "consumer_status": "NO_ACTIVE_TRAINING_CONSUMER_CONNECTED",
            "scope_statement": (
                "Exact8 by canonical-five source-bound non-geometry data-use "
                "admission candidate; distinct from effectiveness and consumption."
            ),
        },
        "source_evaluation_identity": {
            "schema_version": SOURCE_EVALUATION_SCHEMA,
            "policy_scope_id": SOURCE_EVALUATION_SCOPE,
            "semantic_projection_sha256": SOURCE_EVALUATION_SEMANTIC_SHA256,
            "frozen_at_commit": BASELINE_COMMIT,
            "source_bindings": source_bindings,
        },
        "formal_population": {
            "formal_group_id": FORMAL_GROUP_ID,
            "formal_split": FORMAL_SPLIT,
            "formal_split_authoritative": True,
            "full_component_event_count": 24,
            "target_event_count": 8,
            "target_event_ids": list(target_ids),
            "scope_exclusion_statement": (
                "Only the approved 4I3U Exact8 is admitted by this candidate; "
                "4I3V, 4I3W/G3H, all other same-group members, and heldout events remain outside scope."
            ),
        },
        "canonical_tasks": [
            {
                "canonical_task_id": task_id,
                "canonical_task_name": task_name,
                "canonical_task_alias": alias,
            }
            for task_id, task_name, alias in CANONICAL_TASKS_V1
        ],
        "use_policy": {
            "grantable_use_names": [name for name, _ in USE_REQUIREMENTS_V1],
            "base_diffusion_inputs_boundary": (
                "Permission is limited to the validated base inputs; it does not "
                "approve every diffusion target, loss, scientific semantic, or execution."
            ),
            "prohibited_use_definitions": [
                {"use_name": name, "boundary": boundary}
                for name, boundary in PROHIBITED_USE_DEFINITIONS_V1
            ],
            "subsequent_execution_conditions": [
                {"condition_id": condition_id, "statement": statement}
                for condition_id, statement in EXECUTION_CONDITIONS_V1
            ],
        },
        "event_task_admission_records": admission_rows,
        "summary": {
            "event_count": 8,
            "canonical_task_count": 5,
            "event_task_admission_record_count": 40,
            "admit_scoped_nongeometry_record_count": 40,
            "base_diffusion_inputs_granted_count": 40,
            "covalent_pair_prediction_granted_count": 40,
            "pair_contrastive_granted_count": 40,
            "task_c_seed_condition_granted_count": 8,
            "task_c_seed_condition_not_applicable_count": 32,
            "batch_status": "EXACT8_CANONICAL5_ADMIT_SCOPED_NON_GEOMETRY_ONLY",
        },
        "permission_boundary": copy.deepcopy(PERMISSION_BOUNDARY_V1),
        "operations_not_executed": [
            "publication", "formal_admission_activation", "consumer_connection",
            "tensor_or_loss_mask_mutation", "model_forward", "production_loss",
            "backward", "optimizer_or_trainer", "parameter_update", "weight_save",
            "checkpoint_access", "train12_population_change",
        ],
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "record_role": RECORD_ROLE,
        "semantic_projection": semantic_projection,
        "semantic_projection_sha256": _sha256(
            _canonical_json_bytes(semantic_projection)
        ),
    }


def build_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
    *, context: POA4I3UExact8NongeometryFormalAdmissionSuccessorContextV1
) -> dict[str, object]:
    """Compile one isolated deterministic successor from the verified evaluation."""

    try:
        checked = _validate_context(context)
        return _derive_successor_from_verified_evaluation(
            copy.deepcopy(checked.frozen_evaluation_result)
        )
    except POA4I3UExact8NongeometryFormalAdmissionSuccessorError:
        raise
    except Exception as error:
        raise POA4I3UExact8NongeometryFormalAdmissionSuccessorError(
            f"{ERROR_TOKEN}:PUBLIC_BUILD_REJECTED:{type(error).__name__}:{error}"
        ) from error


def validate_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
    *, result: object,
    context: POA4I3UExact8NongeometryFormalAdmissionSuccessorContextV1,
) -> bool:
    """Revalidate published sources, rederive the successor, and compare strictly."""

    try:
        checked = _validate_context(context)
        candidate = _exact_dict(
            result,
            {"schema_version", "record_role", "semantic_projection", "semantic_projection_sha256"},
            "SUCCESSOR_RESULT",
        )
        if (
            candidate.get("schema_version") != SCHEMA_VERSION
            or candidate.get("record_role") != RECORD_ROLE
            or type(candidate.get("semantic_projection")) is not dict
            or type(candidate.get("semantic_projection_sha256")) is not str
            or candidate["semantic_projection_sha256"]
            != _sha256(_canonical_json_bytes(candidate["semantic_projection"]))
        ):
            _fail("SUCCESSOR_RESULT_HEADER_OR_DIGEST_INVALID")
        expected = _derive_successor_from_verified_evaluation(
            copy.deepcopy(checked.frozen_evaluation_result)
        )
        if not _strict_equal(candidate, expected):
            _fail("SUCCESSOR_RESULT_SOURCE_REDERIVATION_MISMATCH")
        return True
    except POA4I3UExact8NongeometryFormalAdmissionSuccessorError:
        raise
    except Exception as error:
        raise POA4I3UExact8NongeometryFormalAdmissionSuccessorError(
            f"{ERROR_TOKEN}:PUBLIC_VALIDATION_REJECTED:"
            f"{type(error).__name__}:{error}"
        ) from error


def serialize_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
    *, result: object,
    context: POA4I3UExact8NongeometryFormalAdmissionSuccessorContextV1,
) -> bytes:
    """Return stable canonical JSON only after complete source revalidation."""

    validate_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
        result=result,
        context=context,
    )
    return _canonical_json_bytes(result, newline=True)


def materialize_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
    *, result: object,
    context: POA4I3UExact8NongeometryFormalAdmissionSuccessorContextV1,
    target_path: Path | str,
) -> bool:
    """Create the explicit target once; an existing target is compared, never overwritten."""

    payload = serialize_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
        result=result,
        context=context,
    )
    if not isinstance(target_path, (Path, str)):
        _fail("MATERIALIZATION_TARGET_PATH_REQUIRED")
    target = Path(target_path)
    try:
        parent = target.parent.resolve(strict=True)
    except OSError as error:
        raise POA4I3UExact8NongeometryFormalAdmissionSuccessorError(
            f"{ERROR_TOKEN}:MATERIALIZATION_PARENT_UNAVAILABLE:{type(error).__name__}"
        ) from error
    resolved_target = parent / target.name
    try:
        with resolved_target.open("xb") as handle:
            handle.write(payload)
        return True
    except FileExistsError:
        current = _read_regular(resolved_target, "MATERIALIZED_RESULT")
        if current != payload:
            _fail("MATERIALIZED_RESULT_EXISTS_WITH_DIFFERENT_BYTES")
        return False
    except OSError as error:
        raise POA4I3UExact8NongeometryFormalAdmissionSuccessorError(
            f"{ERROR_TOKEN}:MATERIALIZATION_WRITE_FAILED:{type(error).__name__}"
        ) from error


def query_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
    *, result: object,
    context: POA4I3UExact8NongeometryFormalAdmissionSuccessorContextV1,
    canonical_event_id: str,
    canonical_task_name: str,
    use_name: str,
) -> dict[str, object]:
    """Return one granted use only after validating the complete fixed successor."""

    validate_covapie_poa_4i3u_exact8_nongeometry_formal_admission_successor_v1(
        result=result,
        context=context,
    )
    if type(canonical_event_id) is not str or canonical_event_id not in context.target_event_ids:
        _fail("QUERY_EVENT_OUT_OF_SCOPE")
    task_names = tuple(name for _, name, _ in CANONICAL_TASKS_V1)
    if type(canonical_task_name) is not str or canonical_task_name not in task_names:
        _fail("QUERY_CANONICAL_TASK_OUT_OF_SCOPE")
    use_names = tuple(name for name, _ in USE_REQUIREMENTS_V1)
    if type(use_name) is not str or use_name not in use_names:
        _fail("QUERY_USE_UNKNOWN_OR_PROHIBITED")
    projection = result["semantic_projection"]
    matching = [
        row
        for row in projection["event_task_admission_records"]
        if row["canonical_event_id"] == canonical_event_id
        and row["canonical_task_name"] == canonical_task_name
    ]
    if len(matching) != 1:
        _fail("QUERY_EVENT_TASK_RECORD_NOT_UNIQUE")
    row = matching[0]
    uses = [item for item in row["use_decisions"] if item["use_name"] == use_name]
    if len(uses) != 1 or uses[0]["admission_use_decision"] != USE_GRANTED:
        _fail("QUERY_USE_NOT_GRANTED")
    response = {
        "canonical_event_id": canonical_event_id,
        "canonical_task_name": canonical_task_name,
        "use_name": use_name,
        "formal_group_id": row["formal_group_id"],
        "formal_split": row["formal_split"],
        "admission_decision": row["admission_decision"],
        "admission_use_decision": uses[0]["admission_use_decision"],
        "required_source_rule_ids": list(uses[0]["required_source_rule_ids"]),
        "formal_admission_effective": False,
        "active_training_consumer_connected": False,
    }
    return copy.deepcopy(response)
