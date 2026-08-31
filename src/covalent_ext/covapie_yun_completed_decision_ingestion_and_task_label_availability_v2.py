"""Thin YUN V2 source-binding successor over the frozen V1 science.

V2 changes only active filesystem acceptance.  Every consumed source is read
through the published B1 combined gate.  Frozen V1 provenance, scientific
semantics, published artifacts, and the training boundary remain unchanged.
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
    covapie_yun_completed_decision_ingestion_and_task_label_availability_v1
    as yun_v1,
)
from covalent_ext.covapie_source_binding_policy_v2 import (
    SourceBindingPolicyV2Error,
    verify_bound_source_v2,
)


__all__ = (
    "YUNSourceBindingV2Error",
    "load_frozen_yun_authority_v2",
    "verify_published_yun_v1_projection_v2",
)


_ERROR_PREFIX = "COVAPIE_YUN_SOURCE_BINDING_V2_ERROR"

SOURCE_BINDING_POLICY_V2_RELATIVE = Path(
    "src/covalent_ext/covapie_source_binding_policy_v2.py"
)
SOURCE_BINDING_POLICY_V2_BYTE_COUNT = 3704
SOURCE_BINDING_POLICY_V2_SHA256 = (
    "c17f3532e6004b347ff62e5d354ac1843f384196c2207127e17971acd2e2d4ee"
)

YUN_V1_OWNER_BYTE_COUNT = 82003
YUN_V1_OWNER_SHA256 = (
    "8339aaa2c57fe1637ab4e4feb7db964fc76224957687d2e0752e28ba3b093928"
)
YUN_V1_CHECKER_BYTE_COUNT = 18235
YUN_V1_CHECKER_SHA256 = (
    "c5472def8826aa76d238030558ae58a06fd5db7f3a1235554774ee374bc5fb76"
)
YUN_V1_TEST_BYTE_COUNT = 22323
YUN_V1_TEST_SHA256 = (
    "0b796683ecd8e4af8647a75d8f034cbbca688f15a529314ada129b009c7929fb"
)

_PUBLISHED_YUN_V1_OUTPUT_BINDINGS = (
    (
        yun_v1.OUTPUT_ROOT_RELATIVE / yun_v1.SNAPSHOT,
        34388,
        "6ce626eb5fcbc8f875f727732daa6047ac35152319db8cfe444725e648d6a012",
        "published_YUN_V1_snapshot",
    ),
    (
        yun_v1.OUTPUT_ROOT_RELATIVE / yun_v1.MATRIX,
        13886,
        "f5c58990490282a9a3ab5218f8ed83f8cead6062fdeb06c4fedc10665630ca0e",
        "published_YUN_V1_matrix",
    ),
    (
        yun_v1.OUTPUT_ROOT_RELATIVE / yun_v1.SUMMARY,
        3983,
        "899faf081224d113bd6e8b277464dbb0b0ee1a992d5262d9b34736b68f42c32e",
        "published_YUN_V1_summary",
    ),
    (
        yun_v1.OUTPUT_ROOT_RELATIVE / yun_v1.MANIFEST,
        16350,
        "18eb6bbfcebb0498b84da22d2e32770f10cf3f3a03f4db6aa58b0c9e6d34204c",
        "published_YUN_V1_manifest",
    ),
)

_FROZEN_V1_CODE_BINDINGS = (
    (
        yun_v1.SOURCE_RELATIVE,
        YUN_V1_OWNER_BYTE_COUNT,
        YUN_V1_OWNER_SHA256,
        "published_YUN_V1_owner",
    ),
    (
        yun_v1.CHECKER_RELATIVE,
        YUN_V1_CHECKER_BYTE_COUNT,
        YUN_V1_CHECKER_SHA256,
        "published_YUN_V1_checker",
    ),
    (
        yun_v1.TEST_RELATIVE,
        YUN_V1_TEST_BYTE_COUNT,
        YUN_V1_TEST_SHA256,
        "published_YUN_V1_tests",
    ),
)


class YUNSourceBindingV2Error(ValueError):
    """Raised when the additive YUN V2 authority cannot be proven."""


def _fail(reason: str) -> NoReturn:
    raise YUNSourceBindingV2Error(f"{_ERROR_PREFIX}:{reason}")


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
        yun_v1.FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT,
        *(row[0] for row in yun_v1.FROZEN_REVIEW_PACKAGE_BINDINGS),
        *(row[0] for row in yun_v1.IMMUTABLE_SEMANTIC_OWNER_BINDINGS),
        *(row[0] for row in yun_v1.INCLUDE_REPOSITORY_PRECEDENT_BINDINGS),
        *(row[0] for row in yun_v1.INCLUDE_PARENT_PRECEDENT_BINDINGS),
        *(row[0] for row in yun_v1.CURRENT_CENSUS_BINDINGS),
        *(row[0] for row in _PUBLISHED_YUN_V1_OUTPUT_BINDINGS),
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
        raise YUNSourceBindingV2Error(
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
        in yun_v1.FROZEN_REVIEW_PACKAGE_BINDINGS
    ]


def _literal_assignments_from_payload(
    payload: bytes, names: Sequence[str], label: str
) -> dict[str, object]:
    try:
        tree = ast.parse(payload.decode("utf-8"))
    except (UnicodeDecodeError, SyntaxError) as error:
        raise YUNSourceBindingV2Error(
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
                    raise YUNSourceBindingV2Error(
                        f"{_ERROR_PREFIX}:SOURCE_LITERAL_INVALID:{target.id}"
                    ) from error
    if set(values) != wanted:
        _fail("SOURCE_LITERAL_ASSIGNMENTS_MISSING:" + label)
    return values


def _validate_semantic_owner_payloads(payloads: Mapping[str, bytes]) -> None:
    runtime = _literal_assignments_from_payload(
        payloads["direct_profile_runtime_semantics_owner"],
        ("DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",),
        "direct_profile_runtime_semantics_owner",
    )
    canonical = _literal_assignments_from_payload(
        payloads["canonical_role_and_task_semantics_owner"],
        ("EXACT3_ROLES", "CANONICAL_TASKS"),
        "canonical_role_and_task_semantics_owner",
    )
    if runtime["DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"] != yun_v1.EXPECTED_ROLE_PROFILE:
        _fail("DIRECT_PROFILE_RUNTIME_CONTRACT_DRIFT")
    if (
        canonical["EXACT3_ROLES"] != ("scaffold", "linker", "warhead")
        or canonical["CANONICAL_TASKS"] != yun_v1.CANONICAL_TASKS
    ):
        _fail("GLOBAL_CANONICAL_EXACT5_TASK_CONTRACT_DRIFT")


def _validate_include_precedent_payloads(payloads: Mapping[str, bytes]) -> None:
    try:
        ffq_rows = list(
            csv.DictReader(
                io.StringIO(
                    payloads["FFQ_INCLUDE_PUBLISHED_MATRIX_PRECEDENT"].decode(
                        "utf-8"
                    )
                )
            )
        )
        poa = json.loads(payloads["POA_INCLUDE_FORMAL_PRECEDENT"])
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise YUNSourceBindingV2Error(
            f"{_ERROR_PREFIX}:INCLUDE_PRECEDENT_PARSE_FAILED"
        ) from error
    included = [
        row
        for row in ffq_rows
        if row.get("formal_event_training_use_decision") == "INCLUDE"
    ]
    if len(included) != 4 or any(
        row.get("training_use_allowed") != "true"
        or row.get("candidate_for_future_training_admission") != "true"
        or row.get("future_training_admission_status") != yun_v1.FUTURE_STATUS
        or row.get("training_admitted") != "false"
        or row.get("training_materialization_allowed_now") != "false"
        or row.get("current_runtime_model_usable") != "false"
        for row in included
    ):
        _fail("FFQ_INCLUDE_SEMANTIC_PRECEDENT_INVALID")
    poa_include = [
        row
        for row in poa.get("subgroup_human_decisions", [])
        if row.get("event_training_use_decision") == "INCLUDE"
    ]
    if (
        len(poa_include) != 1
        or poa_include[0].get("training_admission_created") is not False
        or poa.get("authority_boundary", {}).get("training_admission_created")
        is not False
        or poa.get("authority_boundary", {}).get("ready_for_training") is not False
    ):
        _fail("POA_INCLUDE_SEMANTIC_PRECEDENT_INVALID")


def _validate_current_census_payloads(payloads: Mapping[Path, bytes]) -> None:
    csv_relative = yun_v1.CURRENT_CENSUS_BINDINGS[1][0]
    summary_relative = yun_v1.CURRENT_CENSUS_BINDINGS[2][0]
    try:
        rows = list(
            csv.DictReader(io.StringIO(payloads[csv_relative].decode("utf-8")))
        )
        summary = json.loads(payloads[summary_relative])
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise YUNSourceBindingV2Error(
            f"{_ERROR_PREFIX}:CURRENT_CENSUS_PARSE_FAILED"
        ) from error
    boundary = summary.get("authority_boundary", {})
    training = summary.get("training_stage", {})
    if (
        summary.get("schema_version")
        != "covapie_cumulative1000_current_global_readiness_census_with_1f8_v1"
        or summary.get("chemistry", {}).get("POSITIVE", {}).get("count") != 82
        or training.get("future_training_admission_candidate_count") != 12
        or training.get("training_use_include_count") != 29
        or boundary.get("next_priority_review_ligand") != "YUN"
        or boundary.get("next_priority_review_event_count") != 7
        or boundary.get("next_priority_review_unit") != yun_v1.EXPECTED_REVIEW_UNIT_ID
    ):
        _fail("CURRENT_CENSUS_SUMMARY_BOUNDARY_INVALID")
    yun_rows = [row for row in rows if row.get("ligand_component_id") == "YUN"]
    if (
        len(yun_rows) != 7
        or tuple(row.get("canonical_event_id") for row in yun_rows)
        != yun_v1.EXPECTED_EVENT_IDS
        or [int(row["scaleup_rank"]) for row in yun_rows]
        != list(yun_v1.EXPECTED_RANKS)
        or any(
            row.get("current_global_status") != "CURRENTLY_UNREVIEWED"
            or row.get("current_review_status") != "CURRENTLY_UNREVIEWED"
            or row.get("chemistry_disposition") != "UNRESOLVED"
            for row in yun_rows
        )
    ):
        _fail("CURRENT_CENSUS_YUN_PRIOR_STATE_INVALID")


def load_frozen_yun_authority_v2(
    *,
    repo_root: Path,
    formal_decision_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]:
    """Load frozen YUN authority through B1 without exact-mode acceptance."""

    repo_root = repo_root.resolve()
    overrides = _normalize_overrides(repository_path_overrides)
    unexpected = set(overrides) - _allowed_override_paths()
    if unexpected:
        _fail("REPOSITORY_PATH_OVERRIDE_UNEXPECTED")
    formal_relative = yun_v1.FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT
    if formal_decision_path is not None and formal_relative in overrides:
        _fail("FORMAL_DECISION_PATH_AMBIGUOUS")

    _verify_source(
        path=repo_root / SOURCE_BINDING_POLICY_V2_RELATIVE,
        byte_count=SOURCE_BINDING_POLICY_V2_BYTE_COUNT,
        sha256=SOURCE_BINDING_POLICY_V2_SHA256,
        label="published_source_binding_policy_v2",
        expected_executable=False,
    )
    for relative, byte_count, sha256, label in _FROZEN_V1_CODE_BINDINGS:
        _verify_source(
            path=repo_root / relative,
            byte_count=byte_count,
            sha256=sha256,
            label=label,
            expected_executable=False,
        )

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
        byte_count=yun_v1.FORMAL_DECISION_BYTE_COUNT,
        sha256=yun_v1.FORMAL_DECISION_SHA256,
        label="formal_YUN_human_decision",
        expected_executable=False,
    )

    for relative, byte_count, sha256, label, legacy_mode in (
        yun_v1.FROZEN_REVIEW_PACKAGE_BINDINGS
    ):
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
            expected_executable=_expected_executable_from_legacy_mode(legacy_mode),
        )

    semantic_payloads: dict[str, bytes] = {}
    for relative, byte_count, sha256, label in (
        yun_v1.IMMUTABLE_SEMANTIC_OWNER_BINDINGS
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

    include_payloads: dict[str, bytes] = {}
    for bindings, namespace in (
        (yun_v1.INCLUDE_REPOSITORY_PRECEDENT_BINDINGS, "repository_relative"),
        (yun_v1.INCLUDE_PARENT_PRECEDENT_BINDINGS, "repository_parent_relative"),
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
    _validate_include_precedent_payloads(include_payloads)

    census_payloads: dict[Path, bytes] = {}
    for relative, byte_count, sha256, label in yun_v1.CURRENT_CENSUS_BINDINGS:
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
        normalized = yun_v1._validate_formal_decision_v1(formal)
    except json.JSONDecodeError as error:
        raise YUNSourceBindingV2Error(
            f"{_ERROR_PREFIX}:FORMAL_DECISION_JSON_INVALID"
        ) from error
    except yun_v1.YUNIngestionSafetyError as error:
        raise YUNSourceBindingV2Error(
            f"{_ERROR_PREFIX}:FORMAL_DECISION_SEMANTICS_INVALID:{error}"
        ) from error

    return {
        "formal": formal,
        "normalized": normalized,
        "formal_decision_binding": yun_v1._formal_binding(),
        "frozen_review_package_bindings": _review_binding_rows(),
        "immutable_semantic_owner_bindings": _binding_rows(
            yun_v1.IMMUTABLE_SEMANTIC_OWNER_BINDINGS,
            namespace="repository_relative",
        ),
        "include_semantic_precedent_bindings": [
            *_binding_rows(
                yun_v1.INCLUDE_REPOSITORY_PRECEDENT_BINDINGS,
                namespace="repository_relative",
            ),
            *_binding_rows(
                yun_v1.INCLUDE_PARENT_PRECEDENT_BINDINGS,
                namespace="repository_parent_relative",
            ),
        ],
        "current_published_census_bindings": _binding_rows(
            yun_v1.CURRENT_CENSUS_BINDINGS,
            namespace="repository_relative",
        ),
        "source_binding_v2": {
            "combined_helper": "verify_bound_source_v2",
            "legacy_mode_metadata_classification": [
                "LEGACY_PROVENANCE_METADATA_PRESERVED",
                "SECURITY_EXECUTABLE_CLASS_INPUT",
            ],
            "exact_posix_numeric_mode_semantic_acceptance": False,
        },
    }


def verify_published_yun_v1_projection_v2(
    *,
    repo_root: Path,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, bytes]:
    """Prove source-derived YUN science equals the published V1 Exact4."""

    repo_root = repo_root.resolve()
    overrides = _normalize_overrides(repository_path_overrides)
    bound = load_frozen_yun_authority_v2(
        repo_root=repo_root,
        repository_path_overrides=overrides,
    )
    artifacts: dict[str, bytes] = {}
    for relative, byte_count, sha256, label in _PUBLISHED_YUN_V1_OUTPUT_BINDINGS:
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

    snapshot = yun_v1._snapshot(bound)
    source_derived = {
        yun_v1.SNAPSHOT: yun_v1._json_bytes(snapshot),
        yun_v1.MATRIX: yun_v1._csv_bytes(
            yun_v1.MATRIX_HEADER, yun_v1._matrix_rows(snapshot)
        ),
        yun_v1.SUMMARY: yun_v1._json_bytes(yun_v1._summary()),
    }
    if any(artifacts[name] != payload for name, payload in source_derived.items()):
        _fail("PUBLISHED_V1_SCIENTIFIC_PROJECTION_MISMATCH")
    try:
        manifest = json.loads(artifacts[yun_v1.MANIFEST])
    except json.JSONDecodeError as error:
        raise YUNSourceBindingV2Error(
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
                _FROZEN_V1_CODE_BINDINGS,
                ("production_owner", "fail_closed_checker", "targeted_test_contract"),
                strict=True,
            )
        ]
        or manifest.get("frozen_formal_evidence_provenance")
        != bound["frozen_review_package_bindings"]
        or manifest.get("canonical_task_contract") != yun_v1._canonical_task_contract()
        or manifest.get("authority_boundary") != yun_v1._authority_boundary()
        or manifest.get("output_artifact_bindings")
        != {
            name: {"sha256": sha256}
            for name, sha256 in (
                (yun_v1.SNAPSHOT, _PUBLISHED_YUN_V1_OUTPUT_BINDINGS[0][2]),
                (yun_v1.MATRIX, _PUBLISHED_YUN_V1_OUTPUT_BINDINGS[1][2]),
                (yun_v1.SUMMARY, _PUBLISHED_YUN_V1_OUTPUT_BINDINGS[2][2]),
            )
        }
        or manifest.get("ready_for_training") is not False
    ):
        _fail("PUBLISHED_V1_MANIFEST_SEMANTICS_INVALID")
    return artifacts
