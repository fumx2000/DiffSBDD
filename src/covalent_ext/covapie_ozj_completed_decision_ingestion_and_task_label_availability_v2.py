"""Thin OZJ V2 source-binding successor over the frozen V1 science.

V2 changes only active filesystem acceptance. Every directly consumed source
is read through the published B1 combined gate. The published CHT V2 STRICT
architecture successor and published YUN V2 INCLUDE successor are both bound
and exercised. Frozen OZJ V1 provenance, scientific semantics, artifacts, and
the training boundary remain unchanged.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
import csv
import io
import json
from pathlib import Path
from typing import NoReturn

from covalent_ext import (
    covapie_cht_completed_decision_ingestion_and_task_label_availability_v2
    as cht_v2,
)
from covalent_ext import (
    covapie_ozj_completed_decision_ingestion_and_task_label_availability_v1
    as ozj_v1,
)
from covalent_ext import (
    covapie_yun_completed_decision_ingestion_and_task_label_availability_v2
    as yun_v2,
)
from covalent_ext.covapie_source_binding_policy_v2 import (
    SourceBindingPolicyV2Error,
    verify_bound_source_v2,
)


__all__ = (
    "OZJSourceBindingV2Error",
    "load_frozen_ozj_authority_v2",
    "verify_published_ozj_v1_projection_v2",
)


_ERROR_PREFIX = "COVAPIE_OZJ_SOURCE_BINDING_V2_ERROR"

SOURCE_BINDING_POLICY_V2_RELATIVE = Path(
    "src/covalent_ext/covapie_source_binding_policy_v2.py"
)
SOURCE_BINDING_POLICY_V2_BYTE_COUNT = 3704
SOURCE_BINDING_POLICY_V2_SHA256 = (
    "c17f3532e6004b347ff62e5d354ac1843f384196c2207127e17971acd2e2d4ee"
)

CHT_V2_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_cht_completed_decision_ingestion_and_task_label_availability_v2.py"
)
CHT_V2_BYTE_COUNT = 27636
CHT_V2_SHA256 = (
    "e163f77de8bb03f107efc955ce8662291f9b39deb0ba341b72494d07b97cf87a"
)
CHT_V2_CHECKER_RELATIVE = Path(
    "scripts/"
    "check_covapie_cht_completed_decision_ingestion_and_task_label_availability_v2.py"
)
CHT_V2_CHECKER_BYTE_COUNT = 38205
CHT_V2_CHECKER_SHA256 = (
    "9642786fb9807da59f189a4a9023b0e9310c06780b357054b464179ddc5a226d"
)
CHT_V2_PUBLISHED_COMMIT = "9e7d520de0baa5e5f107985f45b97f576bbd8fc0"

YUN_V2_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_yun_completed_decision_ingestion_and_task_label_availability_v2.py"
)
YUN_V2_BYTE_COUNT = 21294
YUN_V2_SHA256 = (
    "a10c929ea86258ac39bc787b3108d622b65c97617e62b19a44bf3711fbffbd52"
)
YUN_V2_CHECKER_RELATIVE = Path(
    "scripts/"
    "check_covapie_yun_completed_decision_ingestion_and_task_label_availability_v2.py"
)
YUN_V2_CHECKER_BYTE_COUNT = 28382
YUN_V2_CHECKER_SHA256 = (
    "f0de27832eb557d1f1150ecddc00a023c7e1d81642cc1c92ef606b302c2a54b2"
)
YUN_V2_PUBLISHED_COMMIT = "5a34e260e57598ab62905f0171e43a67acc188e2"

OZJ_V1_OWNER_BYTE_COUNT = 106888
OZJ_V1_OWNER_SHA256 = (
    "abb80e28e1e139c3515a01c53468530a815c5554b94053afb607053d14a84deb"
)
OZJ_V1_CHECKER_BYTE_COUNT = 22027
OZJ_V1_CHECKER_SHA256 = (
    "84289cd412b31c8baecc5bf777adde17341c0e6a37caf85de48ab6a926378e15"
)
OZJ_V1_TEST_BYTE_COUNT = 26659
OZJ_V1_TEST_SHA256 = (
    "e4a6e6b32624427c36e2b2ed970615bc8b78b9d4151c5634fb0078fdde0984cc"
)

_FROZEN_OZJ_V1_CODE_BINDINGS = (
    (
        ozj_v1.SOURCE_RELATIVE,
        OZJ_V1_OWNER_BYTE_COUNT,
        OZJ_V1_OWNER_SHA256,
        "published_OZJ_V1_owner",
    ),
    (
        ozj_v1.CHECKER_RELATIVE,
        OZJ_V1_CHECKER_BYTE_COUNT,
        OZJ_V1_CHECKER_SHA256,
        "published_OZJ_V1_checker",
    ),
    (
        ozj_v1.TEST_RELATIVE,
        OZJ_V1_TEST_BYTE_COUNT,
        OZJ_V1_TEST_SHA256,
        "published_OZJ_V1_tests",
    ),
)

_PUBLISHED_OZJ_V1_OUTPUT_BINDINGS = (
    (
        ozj_v1.OUTPUT_ROOT_RELATIVE / ozj_v1.SNAPSHOT,
        31404,
        "3458c3559963b09f69495ffe8cf43511a1e84b7de5ad0c84279ccdcd100a4b25",
        "published_OZJ_V1_snapshot",
    ),
    (
        ozj_v1.OUTPUT_ROOT_RELATIVE / ozj_v1.MATRIX,
        9031,
        "b039dbde52e2fe6a46866cdce0a378fc6dcc942e4a552845ce664fd80f1009d3",
        "published_OZJ_V1_matrix",
    ),
    (
        ozj_v1.OUTPUT_ROOT_RELATIVE / ozj_v1.SUMMARY,
        4803,
        "305bb814c97a450e8dc95961433daf1e9aca942537469153a89d7e322c6c3214",
        "published_OZJ_V1_summary",
    ),
    (
        ozj_v1.OUTPUT_ROOT_RELATIVE / ozj_v1.MANIFEST,
        18554,
        "ca1e305920afd724c138ed572764bd3147039345034ebd172dfb1e274a4a1468",
        "published_OZJ_V1_manifest",
    ),
)

_FROZEN_DUAL_V2_BINDINGS = (
    (
        CHT_V2_RELATIVE,
        CHT_V2_BYTE_COUNT,
        CHT_V2_SHA256,
        "published_CHT_V2_successor",
    ),
    (
        CHT_V2_CHECKER_RELATIVE,
        CHT_V2_CHECKER_BYTE_COUNT,
        CHT_V2_CHECKER_SHA256,
        "published_CHT_V2_checker",
    ),
    (
        YUN_V2_RELATIVE,
        YUN_V2_BYTE_COUNT,
        YUN_V2_SHA256,
        "published_YUN_V2_successor",
    ),
    (
        YUN_V2_CHECKER_RELATIVE,
        YUN_V2_CHECKER_BYTE_COUNT,
        YUN_V2_CHECKER_SHA256,
        "published_YUN_V2_checker",
    ),
)


class OZJSourceBindingV2Error(ValueError):
    """Raised when the additive OZJ V2 authority cannot be proven."""


def _fail(reason: str) -> NoReturn:
    raise OZJSourceBindingV2Error(f"{_ERROR_PREFIX}:{reason}")


def _normalize_overrides(
    overrides: Mapping[Path, Path] | None,
) -> dict[Path, Path]:
    normalized: dict[Path, Path] = {}
    if overrides is None:
        return normalized
    for raw_relative, raw_replacement in overrides.items():
        relative = Path(raw_relative)
        replacement = Path(raw_replacement)
        if relative.is_absolute() or relative in normalized:
            _fail("REPOSITORY_PATH_OVERRIDE_KEY_INVALID")
        normalized[relative] = replacement
    return normalized


def _allowed_override_paths() -> set[Path]:
    return {
        ozj_v1.FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT,
        *(row[0] for row in ozj_v1.FROZEN_REVIEW_PACKAGE_BINDINGS),
        *(row[0] for row in ozj_v1.IMMUTABLE_SEMANTIC_OWNER_BINDINGS),
        *(row[0] for row in ozj_v1.ARCHITECTURE_PRECEDENT_BINDINGS),
        *(row[0] for row in ozj_v1.INCLUDE_REPOSITORY_PRECEDENT_BINDINGS),
        *(row[0] for row in ozj_v1.INCLUDE_PARENT_PRECEDENT_BINDINGS),
        *(row[0] for row in ozj_v1.CURRENT_CENSUS_BINDINGS),
        *(row[0] for row in _PUBLISHED_OZJ_V1_OUTPUT_BINDINGS),
    }


def _resolved_path(
    *,
    repo_root: Path,
    relative: Path,
    namespace: str,
    overrides: Mapping[Path, Path],
) -> Path:
    if relative in overrides:
        replacement = overrides[relative]
        return replacement if replacement.is_absolute() else repo_root / replacement
    if namespace == "repository_relative":
        return repo_root / relative
    if namespace in {"repository_parent_relative", "project_parent_relative"}:
        return repo_root.parent / relative
    _fail("PATH_NAMESPACE_UNSUPPORTED:" + namespace)


def _verify_source(
    *,
    path: Path,
    byte_count: int,
    sha256: str,
    label: str,
    expected_executable: bool,
) -> bytes:
    try:
        return verify_bound_source_v2(
            path=path,
            expected_byte_count=byte_count,
            expected_sha256=sha256,
            label=label,
            expected_executable=expected_executable,
        )
    except SourceBindingPolicyV2Error as error:
        raise OZJSourceBindingV2Error(
            f"{_ERROR_PREFIX}:BOUND_SOURCE_REJECTED:{label}:{error}"
        ) from error


def _expected_executable_from_legacy_mode(mode: str) -> bool:
    if len(mode) != 4 or any(character not in "01234567" for character in mode):
        _fail("LEGACY_MODE_PROVENANCE_INVALID")
    return bool(int(mode, 8) & 0o111)


def _binding_rows(
    bindings: Sequence[tuple[Path, int, str, str]], *, namespace: str
) -> list[dict[str, object]]:
    return [
        {
            "path": relative.as_posix(),
            "path_namespace": namespace,
            "byte_count": byte_count,
            "sha256": sha256,
            "sha256_scope": "file_bytes",
            "source_role": role,
            "verification_status": "MATCHED",
        }
        for relative, byte_count, sha256, role in bindings
    ]


def _review_binding_rows() -> list[dict[str, object]]:
    return [
        {
            "path": relative.as_posix(),
            "path_namespace": "project_parent_relative",
            "byte_count": byte_count,
            "sha256": sha256,
            "sha256_scope": "file_bytes",
            "source_role": role,
            "mode": mode,
            "verification_status": "MATCHED",
        }
        for relative, byte_count, sha256, role, mode
        in ozj_v1.FROZEN_REVIEW_PACKAGE_BINDINGS
    ]


def _literal_assignments_from_payload(
    payload: bytes, names: Sequence[str], label: str
) -> dict[str, object]:
    try:
        tree = ast.parse(payload.decode("utf-8"))
    except (UnicodeDecodeError, SyntaxError) as error:
        raise OZJSourceBindingV2Error(
            f"{_ERROR_PREFIX}:SOURCE_AST_INVALID:{label}"
        ) from error
    wanted = set(names)
    values: dict[str, object] = {}
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Name) and target.id in wanted:
                try:
                    values[target.id] = ast.literal_eval(node.value)
                except (ValueError, TypeError) as error:
                    raise OZJSourceBindingV2Error(
                        f"{_ERROR_PREFIX}:SOURCE_LITERAL_INVALID:{target.id}"
                    ) from error
    if set(values) != wanted:
        _fail("SOURCE_LITERAL_ASSIGNMENTS_MISSING:" + label)
    return values


def _validate_semantic_owner_payloads(payloads: Mapping[str, bytes]) -> None:
    runtime = _literal_assignments_from_payload(
        payloads["strict_profile_runtime_semantics_owner"],
        ("STRICT_LINKER_PRESENT_V1",),
        "strict_profile_runtime_semantics_owner",
    )
    canonical = _literal_assignments_from_payload(
        payloads["canonical_role_and_task_semantics_owner"],
        ("EXACT3_ROLES", "CANONICAL_TASKS"),
        "canonical_role_and_task_semantics_owner",
    )
    if runtime["STRICT_LINKER_PRESENT_V1"] != ozj_v1.EXPECTED_ROLE_PROFILE:
        _fail("STRICT_PROFILE_RUNTIME_CONTRACT_DRIFT")
    if (
        canonical["EXACT3_ROLES"] != ("scaffold", "linker", "warhead")
        or canonical["CANONICAL_TASKS"] != ozj_v1.CANONICAL_TASKS
    ):
        _fail("GLOBAL_CANONICAL_EXACT5_TASK_CONTRACT_DRIFT")


def _validate_cht_architecture_precedent(
    payloads: Mapping[str, bytes], cht_artifacts: Mapping[str, bytes]
) -> None:
    matrix = payloads["CHT_STRICT_EXACT5_MATRIX_PRECEDENT"]
    if matrix != cht_artifacts[
        "covapie_cht_event_task_label_availability_v1.csv"
    ]:
        _fail("CHT_V1_SCIENTIFIC_MATRIX_NOT_PRESERVED")
    try:
        rows = list(csv.DictReader(io.StringIO(matrix.decode("utf-8"))))
    except UnicodeDecodeError as error:
        raise OZJSourceBindingV2Error(
            f"{_ERROR_PREFIX}:CHT_ARCHITECTURE_PRECEDENT_PARSE_FAILED"
        ) from error
    if len(rows) != 5 or any(
        row.get("role_profile") != ozj_v1.EXPECTED_ROLE_PROFILE
        or row.get("strict_profile_applicable_task_ids_json") != "[0,1,2,3,4]"
        or json.loads(row.get("canonical_task_applicability_json", "[]"))[3]
        .get("semantic_long_name") != "scaffold_only"
        for row in rows
    ):
        _fail("CHT_STRICT_EXACT5_ARCHITECTURE_PRECEDENT_INVALID")


def _validate_yun_include_precedent(
    payloads: Mapping[str, bytes], yun_artifacts: Mapping[str, bytes]
) -> None:
    matrix = payloads["YUN_INCLUDE_PUBLISHED_MATRIX_PRECEDENT"]
    if matrix != yun_artifacts[
        "covapie_yun_event_task_label_availability_v1.csv"
    ]:
        _fail("YUN_V1_INCLUDE_SCIENTIFIC_PROJECTION_NOT_PRESERVED")
    try:
        rows = list(csv.DictReader(io.StringIO(matrix.decode("utf-8"))))
        formal = json.loads(payloads["YUN_INCLUDE_FORMAL_PRECEDENT"])
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OZJSourceBindingV2Error(
            f"{_ERROR_PREFIX}:YUN_INCLUDE_PRECEDENT_PARSE_FAILED"
        ) from error
    training = formal.get("training_use_human_decision", {})
    if (
        training.get("D5_human_choice") != "INCLUDE"
        or training.get("human_training_excluded") is not False
        or training.get("training_use_include") is not True
        or training.get("future_training_admission_candidate") is not None
        or training.get("future_training_admission_candidate_status")
        != ozj_v1.FORMAL_FUTURE_STATUS
        or training.get("formal_training_admitted") is not False
        or training.get("training_admission_created") is not False
    ):
        _fail("YUN_INCLUDE_FORMAL_NULL_DEFERRED_PRECEDENT_INVALID")
    if len(rows) != 7 or any(
        row.get("formal_event_training_use_decision") != "INCLUDE"
        or row.get("human_training_excluded") != "false"
        or row.get("training_use_allowed") != "true"
        or row.get("candidate_for_future_training_admission") != "true"
        or row.get("future_training_admission_status") != ozj_v1.FUTURE_STATUS
        or row.get("future_training_candidate_derived_by_ingestion") != "true"
        or row.get("future_training_candidate_is_training_admission") != "false"
        or row.get("training_admitted") != "false"
        or row.get("training_materialization_allowed_now") != "false"
        or row.get("current_runtime_model_usable") != "false"
        for row in rows
    ):
        _fail("YUN_INCLUDE_INGESTION_DERIVATION_PRECEDENT_INVALID")


def _validate_current_census_payloads(payloads: Mapping[Path, bytes]) -> None:
    csv_relative = ozj_v1.CURRENT_CENSUS_BINDINGS[1][0]
    summary_relative = ozj_v1.CURRENT_CENSUS_BINDINGS[2][0]
    try:
        rows = list(
            csv.DictReader(io.StringIO(payloads[csv_relative].decode("utf-8")))
        )
        summary = json.loads(payloads[summary_relative])
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OZJSourceBindingV2Error(
            f"{_ERROR_PREFIX}:CURRENT_CENSUS_PARSE_FAILED"
        ) from error
    authority = summary.get("authority_boundary", {})
    training = summary.get("training_stage", {})
    if (
        summary.get("schema_version")
        != "covapie_cumulative1000_current_global_readiness_census_with_cht_v1"
        or summary.get("chemistry", {}).get("POSITIVE", {}).get("count") != 100
        or summary.get("task_relevance", {}).get("RELEVANT", {}).get("count")
        != 101
        or summary.get("training_use", {})
        .get("EXCLUDE_FROM_TRAINING_ONLY", {})
        .get("count")
        != 64
        or training.get("training_use_include_count") != 36
        or training.get("future_training_admission_candidate_count") != 19
        or authority.get("next_priority_review_ligand") != "OZJ"
        or authority.get("next_priority_review_event_count") != 4
        or authority.get("next_priority_review_unit")
        != ozj_v1.EXPECTED_REVIEW_UNIT_ID
    ):
        _fail("CURRENT_CENSUS_SUMMARY_BOUNDARY_INVALID")
    ozj_rows = [row for row in rows if row.get("ligand_component_id") == "OZJ"]
    if (
        len(ozj_rows) != 4
        or tuple(row.get("canonical_event_id") for row in ozj_rows)
        != ozj_v1.EXPECTED_EVENT_IDS
        or [int(row["scaleup_rank"]) for row in ozj_rows]
        != list(ozj_v1.EXPECTED_RANKS)
        or any(
            row.get("current_global_status") != "CURRENTLY_UNREVIEWED"
            or row.get("current_review_status") != "CURRENTLY_UNREVIEWED"
            or row.get("chemistry_disposition") != "UNRESOLVED"
            or row.get("task_relevance_disposition") != "UNRESOLVED"
            or row.get("training_use_disposition") != "UNRESOLVED"
            for row in ozj_rows
        )
    ):
        _fail("CURRENT_CENSUS_OZJ_PRIOR_STATE_INVALID")


def _exercise_published_cht_v2_precedent(repo_root: Path) -> dict[str, bytes]:
    try:
        artifacts = cht_v2.verify_published_cht_v1_projection_v2(
            repo_root=repo_root
        )
    except cht_v2.CHTSourceBindingV2Error as error:
        raise OZJSourceBindingV2Error(
            f"{_ERROR_PREFIX}:PUBLISHED_CHT_V2_PRECEDENT_REJECTED:{error}"
        ) from error
    if tuple(artifacts) != (
        "covapie_cht_completed_human_decision_snapshot_v1.json",
        "covapie_cht_event_task_label_availability_v1.csv",
        "covapie_cht_completed_decision_ingestion_summary_v1.json",
        "covapie_cht_completed_decision_ingestion_manifest_v1.json",
    ):
        _fail("PUBLISHED_CHT_V2_PRECEDENT_PROJECTION_INVALID")
    return artifacts


def _exercise_published_yun_v2_precedent(repo_root: Path) -> dict[str, bytes]:
    try:
        artifacts = yun_v2.verify_published_yun_v1_projection_v2(
            repo_root=repo_root
        )
    except yun_v2.YUNSourceBindingV2Error as error:
        raise OZJSourceBindingV2Error(
            f"{_ERROR_PREFIX}:PUBLISHED_YUN_V2_PRECEDENT_REJECTED:{error}"
        ) from error
    if tuple(artifacts) != (
        "covapie_yun_completed_human_decision_snapshot_v1.json",
        "covapie_yun_event_task_label_availability_v1.csv",
        "covapie_yun_completed_decision_ingestion_summary_v1.json",
        "covapie_yun_completed_decision_ingestion_manifest_v1.json",
    ):
        _fail("PUBLISHED_YUN_V2_PRECEDENT_PROJECTION_INVALID")
    return artifacts


def load_frozen_ozj_authority_v2(
    *,
    repo_root: Path,
    formal_decision_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]:
    """Load frozen OZJ authority through B1 without exact-mode acceptance."""

    repo_root = repo_root.resolve()
    overrides = _normalize_overrides(repository_path_overrides)
    if set(overrides) - _allowed_override_paths():
        _fail("REPOSITORY_PATH_OVERRIDE_UNEXPECTED")
    formal_relative = ozj_v1.FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT
    if formal_decision_path is not None and formal_relative in overrides:
        _fail("FORMAL_DECISION_PATH_AMBIGUOUS")

    _verify_source(
        path=repo_root / SOURCE_BINDING_POLICY_V2_RELATIVE,
        byte_count=SOURCE_BINDING_POLICY_V2_BYTE_COUNT,
        sha256=SOURCE_BINDING_POLICY_V2_SHA256,
        label="published_source_binding_policy_v2",
        expected_executable=False,
    )
    for relative, byte_count, sha256, label in _FROZEN_DUAL_V2_BINDINGS:
        _verify_source(
            path=repo_root / relative,
            byte_count=byte_count,
            sha256=sha256,
            label=label,
            expected_executable=False,
        )
    for relative, byte_count, sha256, label in _FROZEN_OZJ_V1_CODE_BINDINGS:
        _verify_source(
            path=repo_root / relative,
            byte_count=byte_count,
            sha256=sha256,
            label=label,
            expected_executable=False,
        )

    cht_artifacts = _exercise_published_cht_v2_precedent(repo_root)
    yun_artifacts = _exercise_published_yun_v2_precedent(repo_root)

    if formal_decision_path is None:
        formal_path = _resolved_path(
            repo_root=repo_root,
            relative=formal_relative,
            namespace="repository_parent_relative",
            overrides=overrides,
        )
    else:
        formal_path = Path(formal_decision_path)
        if not formal_path.is_absolute():
            formal_path = repo_root / formal_path
    formal_payload = _verify_source(
        path=formal_path,
        byte_count=ozj_v1.FORMAL_DECISION_BYTE_COUNT,
        sha256=ozj_v1.FORMAL_DECISION_SHA256,
        label="formal_OZJ_human_decision",
        expected_executable=False,
    )

    review_executable_classes: list[bool] = []
    for relative, byte_count, sha256, label, legacy_mode in (
        ozj_v1.FROZEN_REVIEW_PACKAGE_BINDINGS
    ):
        expected_executable = _expected_executable_from_legacy_mode(legacy_mode)
        review_executable_classes.append(expected_executable)
        _verify_source(
            path=_resolved_path(
                repo_root=repo_root,
                relative=relative,
                namespace="project_parent_relative",
                overrides=overrides,
            ),
            byte_count=byte_count,
            sha256=sha256,
            label=label,
            expected_executable=expected_executable,
        )
    if review_executable_classes != [False] * 6:
        _fail("OZJ_REVIEW_EXECUTABLE_CLASS_INVENTORY_INVALID")

    semantic_payloads: dict[str, bytes] = {}
    for relative, byte_count, sha256, label in (
        ozj_v1.IMMUTABLE_SEMANTIC_OWNER_BINDINGS
    ):
        semantic_payloads[label] = _verify_source(
            path=_resolved_path(
                repo_root=repo_root,
                relative=relative,
                namespace="repository_relative",
                overrides=overrides,
            ),
            byte_count=byte_count,
            sha256=sha256,
            label=label,
            expected_executable=False,
        )
    _validate_semantic_owner_payloads(semantic_payloads)

    architecture_payloads: dict[str, bytes] = {}
    for relative, byte_count, sha256, label in (
        ozj_v1.ARCHITECTURE_PRECEDENT_BINDINGS
    ):
        architecture_payloads[label] = _verify_source(
            path=_resolved_path(
                repo_root=repo_root,
                relative=relative,
                namespace="repository_relative",
                overrides=overrides,
            ),
            byte_count=byte_count,
            sha256=sha256,
            label=label,
            expected_executable=False,
        )
    _validate_cht_architecture_precedent(architecture_payloads, cht_artifacts)

    include_payloads: dict[str, bytes] = {}
    for bindings, namespace in (
        (ozj_v1.INCLUDE_REPOSITORY_PRECEDENT_BINDINGS, "repository_relative"),
        (ozj_v1.INCLUDE_PARENT_PRECEDENT_BINDINGS, "repository_parent_relative"),
    ):
        for relative, byte_count, sha256, label in bindings:
            include_payloads[label] = _verify_source(
                path=_resolved_path(
                    repo_root=repo_root,
                    relative=relative,
                    namespace=namespace,
                    overrides=overrides,
                ),
                byte_count=byte_count,
                sha256=sha256,
                label=label,
                expected_executable=False,
            )
    _validate_yun_include_precedent(include_payloads, yun_artifacts)

    census_payloads: dict[Path, bytes] = {}
    for relative, byte_count, sha256, label in ozj_v1.CURRENT_CENSUS_BINDINGS:
        census_payloads[relative] = _verify_source(
            path=_resolved_path(
                repo_root=repo_root,
                relative=relative,
                namespace="repository_relative",
                overrides=overrides,
            ),
            byte_count=byte_count,
            sha256=sha256,
            label=label,
            expected_executable=False,
        )
    _validate_current_census_payloads(census_payloads)

    try:
        formal = json.loads(formal_payload)
        normalized = ozj_v1._validate_formal_decision_v1(formal)
    except json.JSONDecodeError as error:
        raise OZJSourceBindingV2Error(
            f"{_ERROR_PREFIX}:FORMAL_DECISION_JSON_INVALID"
        ) from error
    except ozj_v1.OZJIngestionSafetyError as error:
        raise OZJSourceBindingV2Error(
            f"{_ERROR_PREFIX}:FORMAL_DECISION_SEMANTICS_INVALID:{error}"
        ) from error

    return {
        "formal": formal,
        "normalized": normalized,
        "formal_decision_binding": ozj_v1._formal_binding(),
        "frozen_review_package_bindings": _review_binding_rows(),
        "immutable_semantic_owner_bindings": _binding_rows(
            ozj_v1.IMMUTABLE_SEMANTIC_OWNER_BINDINGS,
            namespace="repository_relative",
        ),
        "architecture_precedent_bindings": _binding_rows(
            ozj_v1.ARCHITECTURE_PRECEDENT_BINDINGS,
            namespace="repository_relative",
        ),
        "include_semantic_precedent_bindings": [
            *_binding_rows(
                ozj_v1.INCLUDE_REPOSITORY_PRECEDENT_BINDINGS,
                namespace="repository_relative",
            ),
            *_binding_rows(
                ozj_v1.INCLUDE_PARENT_PRECEDENT_BINDINGS,
                namespace="repository_parent_relative",
            ),
        ],
        "current_published_census_bindings": _binding_rows(
            ozj_v1.CURRENT_CENSUS_BINDINGS,
            namespace="repository_relative",
        ),
        "dual_published_v2_predecessors": {
            "published_CHT_V2_successor_bound": True,
            "CHT_V2_sha256": CHT_V2_SHA256,
            "CHT_V2_published_commit": CHT_V2_PUBLISHED_COMMIT,
            "CHT_V2_source_binding_migration_active": True,
            "CHT_V2_projection_actually_called": True,
            "CHT_V1_scientific_matrix_preserved": True,
            "published_YUN_V2_successor_bound": True,
            "YUN_V2_sha256": YUN_V2_SHA256,
            "YUN_V2_published_commit": YUN_V2_PUBLISHED_COMMIT,
            "YUN_V2_source_binding_migration_active": True,
            "YUN_V2_projection_actually_called": True,
            "YUN_V1_INCLUDE_projection_preserved": True,
        },
        "source_binding_v2": {
            "combined_helper": "verify_bound_source_v2",
            "legacy_mode_metadata_classification": [
                "LEGACY_PROVENANCE_METADATA_PRESERVED",
                "SECURITY_EXECUTABLE_CLASS_INPUT",
            ],
            "historical_review_modes": ["0664"] * 6,
            "review_source_expected_executable_classes": [False] * 6,
            "review_package_validator_expected_executable": False,
            "exact_posix_numeric_mode_semantic_acceptance": False,
        },
    }


def verify_published_ozj_v1_projection_v2(
    *,
    repo_root: Path,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, bytes]:
    """Prove source-derived OZJ science equals the published V1 Exact4."""

    repo_root = repo_root.resolve()
    overrides = _normalize_overrides(repository_path_overrides)
    bound = load_frozen_ozj_authority_v2(
        repo_root=repo_root,
        repository_path_overrides=overrides,
    )
    artifacts: dict[str, bytes] = {}
    for relative, byte_count, sha256, label in _PUBLISHED_OZJ_V1_OUTPUT_BINDINGS:
        artifacts[relative.name] = _verify_source(
            path=_resolved_path(
                repo_root=repo_root,
                relative=relative,
                namespace="repository_relative",
                overrides=overrides,
            ),
            byte_count=byte_count,
            sha256=sha256,
            label=label,
            expected_executable=False,
        )

    snapshot = ozj_v1._snapshot(bound)
    source_derived = {
        ozj_v1.SNAPSHOT: ozj_v1._json_bytes(snapshot),
        ozj_v1.MATRIX: ozj_v1._csv_bytes(
            ozj_v1.MATRIX_HEADER, ozj_v1._matrix_rows(snapshot)
        ),
        ozj_v1.SUMMARY: ozj_v1._json_bytes(ozj_v1._summary()),
    }
    if any(artifacts[name] != payload for name, payload in source_derived.items()):
        _fail("PUBLISHED_V1_SCIENTIFIC_PROJECTION_MISMATCH")
    try:
        manifest = json.loads(artifacts[ozj_v1.MANIFEST])
    except json.JSONDecodeError as error:
        raise OZJSourceBindingV2Error(
            f"{_ERROR_PREFIX}:PUBLISHED_V1_MANIFEST_JSON_INVALID"
        ) from error
    if (
        manifest.get("candidate_source_bindings")
        != [
            {
                "path": relative.as_posix(),
                "path_namespace": "repository_relative",
                "byte_count": byte_count,
                "sha256": sha256,
                "sha256_scope": "file_bytes",
                "source_role": role,
            }
            for (relative, byte_count, sha256, _label), role in zip(
                _FROZEN_OZJ_V1_CODE_BINDINGS,
                ("production_owner", "fail_closed_checker", "targeted_test_contract"),
                strict=True,
            )
        ]
        or manifest.get("formal_decision_binding")
        != bound["formal_decision_binding"]
        or manifest.get("frozen_formal_evidence_provenance")
        != bound["frozen_review_package_bindings"]
        or manifest.get("architecture_precedent_bindings")
        != bound["architecture_precedent_bindings"]
        or manifest.get("include_semantic_precedent_bindings")
        != bound["include_semantic_precedent_bindings"]
        or manifest.get("immutable_semantic_owner_bindings")
        != bound["immutable_semantic_owner_bindings"]
        or manifest.get("current_published_census_bindings")
        != bound["current_published_census_bindings"]
        or manifest.get("canonical_task_contract")
        != ozj_v1._canonical_task_contract()
        or manifest.get("source_CCD_and_topology_boundary")
        != ozj_v1._source_ccd_and_event_topology_boundary()
        or manifest.get("authority_boundary") != ozj_v1._authority_boundary()
        or manifest.get("human_authority_ingestion_semantics")
        != {
            "authority_source": ozj_v1.AUTHORITY_SOURCE,
            "authority_scope": ozj_v1.AUTHORITY_SCOPE,
            "authority_ingested": True,
            "authority_created_by_ingestion": False,
            "formal_event_training_use_decision": "INCLUDE",
            "human_training_excluded": False,
            "training_use_allowed": True,
            "training_use_include": True,
            "formal_future_training_admission_candidate": None,
            "formal_future_training_admission_candidate_status":
                ozj_v1.FORMAL_FUTURE_STATUS,
            "candidate_for_future_training_admission": True,
            "future_training_admission_status": ozj_v1.FUTURE_STATUS,
            "future_training_candidate_derived_by_ingestion": True,
            "future_training_candidate_is_training_admission": False,
            "training_admitted": False,
        }
        or manifest.get("output_artifact_bindings")
        != {
            name: {"sha256": sha256}
            for name, sha256 in (
                (ozj_v1.SNAPSHOT, _PUBLISHED_OZJ_V1_OUTPUT_BINDINGS[0][2]),
                (ozj_v1.MATRIX, _PUBLISHED_OZJ_V1_OUTPUT_BINDINGS[1][2]),
                (ozj_v1.SUMMARY, _PUBLISHED_OZJ_V1_OUTPUT_BINDINGS[2][2]),
            )
        }
        or manifest.get("ready_for_training") is not False
    ):
        _fail("PUBLISHED_V1_MANIFEST_SEMANTICS_INVALID")
    return artifacts
