"""Thin NEQ V2 source-binding successor over the frozen V1 science.

V2 changes only active filesystem acceptance. Every directly consumed source is
read through the published B1 combined gate, while the published YUN V2 module
is exercised as the upstream migration precedent. Frozen V1 provenance,
scientific semantics, artifacts, and the training boundary remain unchanged.
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
    covapie_neq_completed_decision_ingestion_and_task_label_availability_v1
    as neq_v1,
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
    "NEQSourceBindingV2Error",
    "load_frozen_neq_authority_v2",
    "verify_published_neq_v1_projection_v2",
)


_ERROR_PREFIX = "COVAPIE_NEQ_SOURCE_BINDING_V2_ERROR"

SOURCE_BINDING_POLICY_V2_RELATIVE = Path(
    "src/covalent_ext/covapie_source_binding_policy_v2.py"
)
SOURCE_BINDING_POLICY_V2_BYTE_COUNT = 3704
SOURCE_BINDING_POLICY_V2_SHA256 = (
    "c17f3532e6004b347ff62e5d354ac1843f384196c2207127e17971acd2e2d4ee"
)

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

NEQ_V1_OWNER_BYTE_COUNT = 96020
NEQ_V1_OWNER_SHA256 = (
    "dee80c8ce26e0be030d3063e8ab9831c1bc0650c6a2dc9798c3c21007faae290"
)
NEQ_V1_CHECKER_BYTE_COUNT = 22964
NEQ_V1_CHECKER_SHA256 = (
    "42f5f6a1b38f6d316a9b5ddc6535ce42514e9309cd3f01b474e50a0bb5496db0"
)
NEQ_V1_TEST_BYTE_COUNT = 27544
NEQ_V1_TEST_SHA256 = (
    "90bdab21a123b430e7964e9be4b19def9154c35394f5bc6e3e2e01581974f53d"
)

_FROZEN_NEQ_V1_CODE_BINDINGS = (
    (
        neq_v1.SOURCE_RELATIVE,
        NEQ_V1_OWNER_BYTE_COUNT,
        NEQ_V1_OWNER_SHA256,
        "published_NEQ_V1_owner",
    ),
    (
        neq_v1.CHECKER_RELATIVE,
        NEQ_V1_CHECKER_BYTE_COUNT,
        NEQ_V1_CHECKER_SHA256,
        "published_NEQ_V1_checker",
    ),
    (
        neq_v1.TEST_RELATIVE,
        NEQ_V1_TEST_BYTE_COUNT,
        NEQ_V1_TEST_SHA256,
        "published_NEQ_V1_tests",
    ),
)

_PUBLISHED_NEQ_V1_OUTPUT_BINDINGS = (
    (
        neq_v1.OUTPUT_ROOT_RELATIVE / neq_v1.SNAPSHOT,
        33094,
        "9f3b8a29410852fe9fdd42cea10f8778e84a1ffe0627b1795fd6380989a2db1c",
        "published_NEQ_V1_snapshot",
    ),
    (
        neq_v1.OUTPUT_ROOT_RELATIVE / neq_v1.MATRIX,
        11706,
        "b4b9a301440724464cb92f1b0f28ef1151b24b12eb3ec001a971dacda3632d4a",
        "published_NEQ_V1_matrix",
    ),
    (
        neq_v1.OUTPUT_ROOT_RELATIVE / neq_v1.SUMMARY,
        4196,
        "a6e3fe3326e1cc51746817b547d0b737d3f4be56fe4d5427667c11d9bf019ef3",
        "published_NEQ_V1_summary",
    ),
    (
        neq_v1.OUTPUT_ROOT_RELATIVE / neq_v1.MANIFEST,
        18257,
        "4c6ad894929b93a0f450bcad56488aa2c4993de58e88660fd14819b3bd332488",
        "published_NEQ_V1_manifest",
    ),
)

_FROZEN_UPSTREAM_V2_BINDINGS = (
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


class NEQSourceBindingV2Error(ValueError):
    """Raised when the additive NEQ V2 authority cannot be proven."""


def _fail(reason: str) -> NoReturn:
    raise NEQSourceBindingV2Error(f"{_ERROR_PREFIX}:{reason}")


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
        neq_v1.FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT,
        *(row[0] for row in neq_v1.FROZEN_REVIEW_PACKAGE_BINDINGS),
        *(row[0] for row in neq_v1.IMMUTABLE_SEMANTIC_OWNER_BINDINGS),
        *(row[0] for row in neq_v1.YUN_SCHEMA_PRECEDENT_BINDINGS),
        *(row[0] for row in neq_v1.EXCLUDE_SEMANTIC_PRECEDENT_BINDINGS),
        *(row[0] for row in neq_v1.CURRENT_CENSUS_BINDINGS),
        *(row[0] for row in _PUBLISHED_NEQ_V1_OUTPUT_BINDINGS),
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
        raise NEQSourceBindingV2Error(
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
        in neq_v1.FROZEN_REVIEW_PACKAGE_BINDINGS
    ]


def _literal_assignments_from_payload(
    payload: bytes, names: Sequence[str], label: str
) -> dict[str, object]:
    try:
        tree = ast.parse(payload.decode("utf-8"))
    except (UnicodeDecodeError, SyntaxError) as error:
        raise NEQSourceBindingV2Error(
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
                    raise NEQSourceBindingV2Error(
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
    if runtime["DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"] != neq_v1.EXPECTED_ROLE_PROFILE:
        _fail("DIRECT_PROFILE_RUNTIME_CONTRACT_DRIFT")
    if (
        canonical["EXACT3_ROLES"] != ("scaffold", "linker", "warhead")
        or canonical["CANONICAL_TASKS"] != neq_v1.CANONICAL_TASKS
    ):
        _fail("GLOBAL_CANONICAL_EXACT5_TASK_CONTRACT_DRIFT")


def _validate_yun_schema_payload(payload: bytes, published_payload: bytes) -> None:
    if payload != published_payload:
        _fail("YUN_V1_SCIENTIFIC_MATRIX_NOT_PRESERVED")
    try:
        header = next(csv.reader(io.StringIO(payload.decode("utf-8"))))
    except (UnicodeDecodeError, StopIteration) as error:
        raise NEQSourceBindingV2Error(
            f"{_ERROR_PREFIX}:YUN_SCHEMA_PRECEDENT_PARSE_FAILED"
        ) from error
    required = {
        "canonical_event_id",
        "scaleup_rank",
        "pdb_id",
        "model_number",
        "protein_chain_or_asym",
        "cys_residue_id",
        "ligand_component_id",
        "human_task_relevance_decision",
        "chemistry_known_positive",
        "negative_chemistry",
        "task_domain_negative",
        "formal_event_training_use_decision",
        "human_training_excluded",
        "training_use_allowed",
        "candidate_for_future_training_admission",
        "training_admitted",
        "training_materialization_allowed_now",
        "current_runtime_model_usable",
        "authority_source",
        "authority_scope",
        "authority_ingested",
        "authority_created_by_this_ingestion",
    }
    if not required.issubset(header):
        _fail("YUN_V1_SCIENTIFIC_MATRIX_VOCABULARY_DRIFT")


def _validate_exclude_precedent_payloads(payloads: Mapping[str, bytes]) -> None:
    try:
        one_f8 = list(
            csv.DictReader(
                io.StringIO(
                    payloads["1F8_EXCLUDE_PUBLISHED_MATRIX_PRECEDENT"].decode(
                        "utf-8"
                    )
                )
            )
        )
        two_vs = list(
            csv.DictReader(
                io.StringIO(
                    payloads["2VS_EXCLUDE_PUBLISHED_MATRIX_PRECEDENT"].decode(
                        "utf-8"
                    )
                )
            )
        )
    except UnicodeDecodeError as error:
        raise NEQSourceBindingV2Error(
            f"{_ERROR_PREFIX}:EXCLUDE_PRECEDENT_PARSE_FAILED"
        ) from error
    for label, rows in (("1F8", one_f8), ("2VS", two_vs)):
        if len(rows) != 8:
            _fail(label + "_EXCLUDE_PRECEDENT_EVENT_COUNT_INVALID")
        if any(
            row.get("human_task_relevance_decision") != "RELEVANT"
            or row.get("chemistry_known_positive") != "true"
            or row.get("negative_chemistry") != "false"
            or row.get("task_domain_negative") != "false"
            or row.get("formal_event_training_use_decision")
            != "EXCLUDE_FROM_TRAINING_ONLY"
            or row.get("human_training_excluded") != "true"
            or row.get("training_use_allowed") != "false"
            or row.get("candidate_for_future_training_admission") != "false"
            or row.get("training_admitted") != "false"
            or row.get("training_materialization_allowed_now") != "false"
            or row.get("current_runtime_model_usable") != "false"
            for row in rows
        ):
            _fail(label + "_EXCLUDE_SEMANTIC_PRECEDENT_INVALID")


def _validate_prior_census_payloads(payloads: Mapping[Path, bytes]) -> None:
    csv_relative = neq_v1.CURRENT_CENSUS_BINDINGS[1][0]
    summary_relative = neq_v1.CURRENT_CENSUS_BINDINGS[2][0]
    try:
        rows = list(
            csv.DictReader(io.StringIO(payloads[csv_relative].decode("utf-8")))
        )
        summary = json.loads(payloads[summary_relative])
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise NEQSourceBindingV2Error(
            f"{_ERROR_PREFIX}:CURRENT_CENSUS_PARSE_FAILED"
        ) from error
    authority = summary.get("authority_boundary", {})
    training = summary.get("training_stage", {})
    if (
        summary.get("schema_version")
        != "covapie_cumulative1000_current_global_readiness_census_with_yun_v1"
        or summary.get("chemistry", {}).get("POSITIVE", {}).get("count") != 89
        or summary.get("training_use", {})
        .get("EXCLUDE_FROM_TRAINING_ONLY", {})
        .get("count")
        != 53
        or training.get("training_use_include_count") != 36
        or training.get("future_training_admission_candidate_count") != 19
        or authority.get("next_priority_review_ligand") != "NEQ"
        or authority.get("next_priority_review_event_count") != 6
        or authority.get("next_priority_review_unit") != neq_v1.EXPECTED_REVIEW_UNIT_ID
    ):
        _fail("CURRENT_CENSUS_SUMMARY_BOUNDARY_INVALID")
    neq_rows = [row for row in rows if row.get("ligand_component_id") == "NEQ"]
    if (
        len(neq_rows) != 6
        or tuple(row.get("canonical_event_id") for row in neq_rows)
        != neq_v1.EXPECTED_EVENT_IDS
        or [int(row["scaleup_rank"]) for row in neq_rows]
        != list(neq_v1.EXPECTED_RANKS)
        or any(
            row.get("current_global_status") != "CURRENTLY_UNREVIEWED"
            or row.get("current_review_status") != "CURRENTLY_UNREVIEWED"
            or row.get("chemistry_disposition") != "UNRESOLVED"
            or row.get("task_relevance_disposition") != "UNRESOLVED"
            or row.get("training_use_disposition") != "UNRESOLVED"
            for row in neq_rows
        )
    ):
        _fail("CURRENT_CENSUS_NEQ_PRIOR_STATE_INVALID")


def _exercise_published_yun_v2_precedent(repo_root: Path) -> dict[str, bytes]:
    try:
        artifacts = yun_v2.verify_published_yun_v1_projection_v2(
            repo_root=repo_root
        )
    except yun_v2.YUNSourceBindingV2Error as error:
        raise NEQSourceBindingV2Error(
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


def load_frozen_neq_authority_v2(
    *,
    repo_root: Path,
    formal_decision_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]:
    """Load frozen NEQ authority through B1 without exact-mode acceptance."""

    repo_root = repo_root.resolve()
    overrides = _normalize_overrides(repository_path_overrides)
    unexpected = set(overrides) - _allowed_override_paths()
    if unexpected:
        _fail("REPOSITORY_PATH_OVERRIDE_UNEXPECTED")
    formal_relative = neq_v1.FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT
    if formal_decision_path is not None and formal_relative in overrides:
        _fail("FORMAL_DECISION_PATH_AMBIGUOUS")

    _verify_source(
        path=repo_root / SOURCE_BINDING_POLICY_V2_RELATIVE,
        byte_count=SOURCE_BINDING_POLICY_V2_BYTE_COUNT,
        sha256=SOURCE_BINDING_POLICY_V2_SHA256,
        label="published_source_binding_policy_v2",
        expected_executable=False,
    )
    for relative, byte_count, sha256, label in _FROZEN_UPSTREAM_V2_BINDINGS:
        _verify_source(
            path=repo_root / relative,
            byte_count=byte_count,
            sha256=sha256,
            label=label,
            expected_executable=False,
        )
    for relative, byte_count, sha256, label in _FROZEN_NEQ_V1_CODE_BINDINGS:
        _verify_source(
            path=repo_root / relative,
            byte_count=byte_count,
            sha256=sha256,
            label=label,
            expected_executable=False,
        )

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
        byte_count=neq_v1.FORMAL_DECISION_BYTE_COUNT,
        sha256=neq_v1.FORMAL_DECISION_SHA256,
        label="formal_NEQ_human_decision",
        expected_executable=False,
    )

    for relative, byte_count, sha256, label, legacy_mode in (
        neq_v1.FROZEN_REVIEW_PACKAGE_BINDINGS
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
        neq_v1.IMMUTABLE_SEMANTIC_OWNER_BINDINGS
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

    yun_schema_payloads: dict[str, bytes] = {}
    for relative, byte_count, sha256, label in neq_v1.YUN_SCHEMA_PRECEDENT_BINDINGS:
        yun_schema_payloads[label] = _verify_source(
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
    _validate_yun_schema_payload(
        yun_schema_payloads["YUN_LATEST_MATRIX_VOCABULARY_PRECEDENT"],
        yun_artifacts["covapie_yun_event_task_label_availability_v1.csv"],
    )

    exclude_payloads: dict[str, bytes] = {}
    for relative, byte_count, sha256, label in (
        neq_v1.EXCLUDE_SEMANTIC_PRECEDENT_BINDINGS
    ):
        exclude_payloads[label] = _verify_source(
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
    _validate_exclude_precedent_payloads(exclude_payloads)

    census_payloads: dict[Path, bytes] = {}
    for relative, byte_count, sha256, label in neq_v1.CURRENT_CENSUS_BINDINGS:
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
    _validate_prior_census_payloads(census_payloads)

    try:
        formal = json.loads(formal_payload)
        normalized = neq_v1._validate_formal_decision_v1(formal)
    except json.JSONDecodeError as error:
        raise NEQSourceBindingV2Error(
            f"{_ERROR_PREFIX}:FORMAL_DECISION_JSON_INVALID"
        ) from error
    except neq_v1.NEQIngestionSafetyError as error:
        raise NEQSourceBindingV2Error(
            f"{_ERROR_PREFIX}:FORMAL_DECISION_SEMANTICS_INVALID:{error}"
        ) from error

    return {
        "formal": formal,
        "normalized": normalized,
        "formal_decision_binding": neq_v1._formal_binding(),
        "frozen_review_package_bindings": _review_binding_rows(),
        "immutable_semantic_owner_bindings": _binding_rows(
            neq_v1.IMMUTABLE_SEMANTIC_OWNER_BINDINGS,
            namespace="repository_relative",
        ),
        "yun_schema_precedent_bindings": _binding_rows(
            neq_v1.YUN_SCHEMA_PRECEDENT_BINDINGS,
            namespace="repository_relative",
        ),
        "exclude_semantic_precedent_bindings": _binding_rows(
            neq_v1.EXCLUDE_SEMANTIC_PRECEDENT_BINDINGS,
            namespace="repository_relative",
        ),
        "current_published_census_bindings": _binding_rows(
            neq_v1.CURRENT_CENSUS_BINDINGS,
            namespace="repository_relative",
        ),
        "upstream_v2_migration_precedent": {
            "published_YUN_V2_successor_bound": True,
            "YUN_V2_sha256": YUN_V2_SHA256,
            "YUN_V2_published_commit": YUN_V2_PUBLISHED_COMMIT,
            "YUN_V2_source_binding_acceptance_active": True,
            "YUN_V1_scientific_matrix_preserved": True,
        },
        "source_binding_v2": {
            "combined_helper": "verify_bound_source_v2",
            "legacy_mode_metadata_classification": [
                "LEGACY_PROVENANCE_METADATA_PRESERVED",
                "SECURITY_EXECUTABLE_CLASS_INPUT",
            ],
            "exact_posix_numeric_mode_semantic_acceptance": False,
        },
    }


def verify_published_neq_v1_projection_v2(
    *,
    repo_root: Path,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, bytes]:
    """Prove source-derived NEQ science equals the published V1 Exact4."""

    repo_root = repo_root.resolve()
    overrides = _normalize_overrides(repository_path_overrides)
    bound = load_frozen_neq_authority_v2(
        repo_root=repo_root,
        repository_path_overrides=overrides,
    )
    artifacts: dict[str, bytes] = {}
    for relative, byte_count, sha256, label in _PUBLISHED_NEQ_V1_OUTPUT_BINDINGS:
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

    snapshot = neq_v1._snapshot(bound)
    source_derived = {
        neq_v1.SNAPSHOT: neq_v1._json_bytes(snapshot),
        neq_v1.MATRIX: neq_v1._csv_bytes(
            neq_v1.MATRIX_HEADER, neq_v1._matrix_rows(snapshot)
        ),
        neq_v1.SUMMARY: neq_v1._json_bytes(neq_v1._summary()),
    }
    if any(artifacts[name] != payload for name, payload in source_derived.items()):
        _fail("PUBLISHED_V1_SCIENTIFIC_PROJECTION_MISMATCH")
    try:
        manifest = json.loads(artifacts[neq_v1.MANIFEST])
    except json.JSONDecodeError as error:
        raise NEQSourceBindingV2Error(
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
                _FROZEN_NEQ_V1_CODE_BINDINGS,
                ("production_owner", "fail_closed_checker", "targeted_test_contract"),
                strict=True,
            )
        ]
        or manifest.get("frozen_formal_evidence_provenance")
        != bound["frozen_review_package_bindings"]
        or manifest.get("yun_schema_precedent_bindings")
        != bound["yun_schema_precedent_bindings"]
        or manifest.get("exclude_semantic_precedent_bindings")
        != bound["exclude_semantic_precedent_bindings"]
        or manifest.get("immutable_semantic_owner_bindings")
        != bound["immutable_semantic_owner_bindings"]
        or manifest.get("current_published_census_bindings")
        != bound["current_published_census_bindings"]
        or manifest.get("canonical_task_contract")
        != neq_v1._canonical_task_contract()
        or manifest.get("source_CCD_and_topology_boundary")
        != neq_v1._source_ccd_and_event_topology_boundary()
        or manifest.get("authority_boundary") != neq_v1._authority_boundary()
        or manifest.get("output_artifact_bindings")
        != {
            name: {"sha256": sha256}
            for name, sha256 in (
                (neq_v1.SNAPSHOT, _PUBLISHED_NEQ_V1_OUTPUT_BINDINGS[0][2]),
                (neq_v1.MATRIX, _PUBLISHED_NEQ_V1_OUTPUT_BINDINGS[1][2]),
                (neq_v1.SUMMARY, _PUBLISHED_NEQ_V1_OUTPUT_BINDINGS[2][2]),
            )
        }
        or manifest.get("ready_for_training") is not False
    ):
        _fail("PUBLISHED_V1_MANIFEST_SEMANTICS_INVALID")
    return artifacts
