"""Thin CHT V2 source-binding successor over the frozen V1 science.

V2 changes only active filesystem acceptance. Every directly consumed source is
read through the published B1 combined gate, while the published NEQ V2 module
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
    covapie_cht_completed_decision_ingestion_and_task_label_availability_v1
    as cht_v1,
)
from covalent_ext import (
    covapie_neq_completed_decision_ingestion_and_task_label_availability_v2
    as neq_v2,
)
from covalent_ext.covapie_source_binding_policy_v2 import (
    SourceBindingPolicyV2Error,
    verify_bound_source_v2,
)


__all__ = (
    "CHTSourceBindingV2Error",
    "load_frozen_cht_authority_v2",
    "verify_published_cht_v1_projection_v2",
)


_ERROR_PREFIX = "COVAPIE_CHT_SOURCE_BINDING_V2_ERROR"

SOURCE_BINDING_POLICY_V2_RELATIVE = Path(
    "src/covalent_ext/covapie_source_binding_policy_v2.py"
)
SOURCE_BINDING_POLICY_V2_BYTE_COUNT = 3704
SOURCE_BINDING_POLICY_V2_SHA256 = (
    "c17f3532e6004b347ff62e5d354ac1843f384196c2207127e17971acd2e2d4ee"
)

NEQ_V2_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_neq_completed_decision_ingestion_and_task_label_availability_v2.py"
)
NEQ_V2_BYTE_COUNT = 26491
NEQ_V2_SHA256 = (
    "21c6d4f13589a72d8762185108eaa26387c124121bdbbed8f6258b689b0a9b4d"
)
NEQ_V2_CHECKER_RELATIVE = Path(
    "scripts/"
    "check_covapie_neq_completed_decision_ingestion_and_task_label_availability_v2.py"
)
NEQ_V2_CHECKER_BYTE_COUNT = 36383
NEQ_V2_CHECKER_SHA256 = (
    "07c8a64442752a39aaba448db79b5f8299ea97524485e75be956de62337e465b"
)
NEQ_V2_PUBLISHED_COMMIT = "baab1358bcc8f776df20d8dc76ed476d51ba27f3"

CHT_V1_OWNER_BYTE_COUNT = 103035
CHT_V1_OWNER_SHA256 = (
    "7a5561f1cb35465a2dbe6af8121f06a07b7aea6d82051e3945352cf1c669aff7"
)
CHT_V1_CHECKER_BYTE_COUNT = 19529
CHT_V1_CHECKER_SHA256 = (
    "39749991b39d90f07e109e2393227e145e0df95571023fbc7faa4d5987dd27cd"
)
CHT_V1_TEST_BYTE_COUNT = 29814
CHT_V1_TEST_SHA256 = (
    "0919c4254b5643336c8d32eb8b3baf1b87ed25a2c2b5b6bbcc2d224bfcfad157"
)

_FROZEN_CHT_V1_CODE_BINDINGS = (
    (
        cht_v1.SOURCE_RELATIVE,
        CHT_V1_OWNER_BYTE_COUNT,
        CHT_V1_OWNER_SHA256,
        "published_CHT_V1_owner",
    ),
    (
        cht_v1.CHECKER_RELATIVE,
        CHT_V1_CHECKER_BYTE_COUNT,
        CHT_V1_CHECKER_SHA256,
        "published_CHT_V1_checker",
    ),
    (
        cht_v1.TEST_RELATIVE,
        CHT_V1_TEST_BYTE_COUNT,
        CHT_V1_TEST_SHA256,
        "published_CHT_V1_tests",
    ),
)

_PUBLISHED_CHT_V1_OUTPUT_BINDINGS = (
    (
        cht_v1.OUTPUT_ROOT_RELATIVE / cht_v1.SNAPSHOT,
        30409,
        "9185ecb6ee62349c4f4cc9c384c30c1fa6d5dedc9e3eaa50e2e352f72e74a163",
        "published_CHT_V1_snapshot",
    ),
    (
        cht_v1.OUTPUT_ROOT_RELATIVE / cht_v1.MATRIX,
        10225,
        "a754c0764ec61eacf7ec64dabdc370e4bca5a00abdfb94ea3923b52be55df6b6",
        "published_CHT_V1_matrix",
    ),
    (
        cht_v1.OUTPUT_ROOT_RELATIVE / cht_v1.SUMMARY,
        4266,
        "22e89e8938438f01d35aa1b66be0613f5fc532cd495f9b424b5500458eee91f6",
        "published_CHT_V1_summary",
    ),
    (
        cht_v1.OUTPUT_ROOT_RELATIVE / cht_v1.MANIFEST,
        18366,
        "f4614719cd554c47eb67f895415e8595f00a346095ffb53cffd4bffec0e85b59",
        "published_CHT_V1_manifest",
    ),
)

_FROZEN_UPSTREAM_V2_BINDINGS = (
    (
        NEQ_V2_RELATIVE,
        NEQ_V2_BYTE_COUNT,
        NEQ_V2_SHA256,
        "published_NEQ_V2_successor",
    ),
    (
        NEQ_V2_CHECKER_RELATIVE,
        NEQ_V2_CHECKER_BYTE_COUNT,
        NEQ_V2_CHECKER_SHA256,
        "published_NEQ_V2_checker",
    ),
)


class CHTSourceBindingV2Error(ValueError):
    """Raised when the additive CHT V2 authority cannot be proven."""


def _fail(reason: str) -> NoReturn:
    raise CHTSourceBindingV2Error(f"{_ERROR_PREFIX}:{reason}")


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
        cht_v1.FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT,
        *(row[0] for row in cht_v1.FROZEN_REVIEW_PACKAGE_BINDINGS),
        *(row[0] for row in cht_v1.IMMUTABLE_SEMANTIC_OWNER_BINDINGS),
        *(row[0] for row in cht_v1.ARCHITECTURE_PRECEDENT_BINDINGS),
        *(row[0] for row in cht_v1.EXCLUDE_SEMANTIC_PRECEDENT_BINDINGS),
        *(row[0] for row in cht_v1.CURRENT_CENSUS_BINDINGS),
        *(row[0] for row in _PUBLISHED_CHT_V1_OUTPUT_BINDINGS),
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
        raise CHTSourceBindingV2Error(
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
        in cht_v1.FROZEN_REVIEW_PACKAGE_BINDINGS
    ]


def _literal_assignments_from_payload(
    payload: bytes, names: Sequence[str], label: str
) -> dict[str, object]:
    try:
        tree = ast.parse(payload.decode("utf-8"))
    except (UnicodeDecodeError, SyntaxError) as error:
        raise CHTSourceBindingV2Error(
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
                    raise CHTSourceBindingV2Error(
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
    if runtime["STRICT_LINKER_PRESENT_V1"] != cht_v1.EXPECTED_ROLE_PROFILE:
        _fail("STRICT_PROFILE_RUNTIME_CONTRACT_DRIFT")
    if (
        canonical["EXACT3_ROLES"] != ("scaffold", "linker", "warhead")
        or canonical["CANONICAL_TASKS"] != cht_v1.CANONICAL_TASKS
    ):
        _fail("GLOBAL_CANONICAL_EXACT5_TASK_CONTRACT_DRIFT")


def _validate_neq_scientific_matrix(
    payload: bytes, published_payload: bytes
) -> None:
    if payload != published_payload:
        _fail("NEQ_V1_SCIENTIFIC_MATRIX_NOT_PRESERVED")
    try:
        rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))
    except UnicodeDecodeError as error:
        raise CHTSourceBindingV2Error(
            f"{_ERROR_PREFIX}:NEQ_SCIENTIFIC_MATRIX_PARSE_FAILED"
        ) from error
    required = {
        "canonical_event_id",
        "human_task_relevance_decision",
        "chemistry_known_positive",
        "negative_chemistry",
        "task_domain_negative",
        "formal_event_training_use_decision",
        "human_training_excluded",
        "training_use_allowed",
        "candidate_for_future_training_admission",
        "training_admitted",
    }
    if not rows or not required.issubset(rows[0]):
        _fail("NEQ_V1_SCIENTIFIC_MATRIX_VOCABULARY_DRIFT")
    if any(
        row["human_task_relevance_decision"] != "RELEVANT"
        or row["chemistry_known_positive"] != "true"
        or row["negative_chemistry"] != "false"
        or row["task_domain_negative"] != "false"
        or row["formal_event_training_use_decision"]
        != "EXCLUDE_FROM_TRAINING_ONLY"
        or row["human_training_excluded"] != "true"
        or row["training_use_allowed"] != "false"
        or row["candidate_for_future_training_admission"] != "false"
        or row["training_admitted"] != "false"
        for row in rows
    ):
        _fail("NEQ_V1_SCIENTIFIC_MATRIX_EXCLUDE_SEMANTICS_DRIFT")


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
        raise CHTSourceBindingV2Error(
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
    csv_relative = cht_v1.CURRENT_CENSUS_BINDINGS[1][0]
    summary_relative = cht_v1.CURRENT_CENSUS_BINDINGS[2][0]
    try:
        rows = list(
            csv.DictReader(io.StringIO(payloads[csv_relative].decode("utf-8")))
        )
        summary = json.loads(payloads[summary_relative])
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CHTSourceBindingV2Error(
            f"{_ERROR_PREFIX}:CURRENT_CENSUS_PARSE_FAILED"
        ) from error
    authority = summary.get("authority_boundary", {})
    training = summary.get("training_stage", {})
    if (
        summary.get("schema_version")
        != "covapie_cumulative1000_current_global_readiness_census_with_neq_v1"
        or summary.get("chemistry", {}).get("POSITIVE", {}).get("count") != 95
        or summary.get("task_relevance", {}).get("RELEVANT", {}).get("count")
        != 96
        or summary.get("training_use", {})
        .get("EXCLUDE_FROM_TRAINING_ONLY", {})
        .get("count")
        != 59
        or training.get("training_use_include_count") != 36
        or training.get("future_training_admission_candidate_count") != 19
        or authority.get("next_priority_review_ligand") != "CHT"
        or authority.get("next_priority_review_event_count") != 5
        or authority.get("next_priority_review_unit")
        != cht_v1.EXPECTED_REVIEW_UNIT_ID
    ):
        _fail("CURRENT_CENSUS_SUMMARY_BOUNDARY_INVALID")
    cht_rows = [row for row in rows if row.get("ligand_component_id") == "CHT"]
    if (
        len(cht_rows) != 5
        or tuple(row.get("canonical_event_id") for row in cht_rows)
        != cht_v1.EXPECTED_EVENT_IDS
        or [int(row["scaleup_rank"]) for row in cht_rows]
        != list(cht_v1.EXPECTED_RANKS)
        or any(
            row.get("current_global_status") != "CURRENTLY_UNREVIEWED"
            or row.get("current_review_status") != "CURRENTLY_UNREVIEWED"
            or row.get("chemistry_disposition") != "UNRESOLVED"
            or row.get("task_relevance_disposition") != "UNRESOLVED"
            or row.get("training_use_disposition") != "UNRESOLVED"
            for row in cht_rows
        )
    ):
        _fail("CURRENT_CENSUS_CHT_PRIOR_STATE_INVALID")


def _exercise_published_neq_v2_precedent(repo_root: Path) -> dict[str, bytes]:
    try:
        artifacts = neq_v2.verify_published_neq_v1_projection_v2(
            repo_root=repo_root
        )
    except neq_v2.NEQSourceBindingV2Error as error:
        raise CHTSourceBindingV2Error(
            f"{_ERROR_PREFIX}:PUBLISHED_NEQ_V2_PRECEDENT_REJECTED:{error}"
        ) from error
    expected = (
        "covapie_neq_completed_human_decision_snapshot_v1.json",
        "covapie_neq_event_task_label_availability_v1.csv",
        "covapie_neq_completed_decision_ingestion_summary_v1.json",
        "covapie_neq_completed_decision_ingestion_manifest_v1.json",
    )
    if tuple(artifacts) != expected:
        _fail("PUBLISHED_NEQ_V2_PRECEDENT_PROJECTION_INVALID")
    return artifacts


def load_frozen_cht_authority_v2(
    *,
    repo_root: Path,
    formal_decision_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]:
    """Load frozen CHT authority through B1 without exact-mode acceptance."""

    repo_root = repo_root.resolve()
    overrides = _normalize_overrides(repository_path_overrides)
    unexpected = set(overrides) - _allowed_override_paths()
    if unexpected:
        _fail("REPOSITORY_PATH_OVERRIDE_UNEXPECTED")
    formal_relative = cht_v1.FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT
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
    for relative, byte_count, sha256, label in _FROZEN_CHT_V1_CODE_BINDINGS:
        _verify_source(
            path=repo_root / relative,
            byte_count=byte_count,
            sha256=sha256,
            label=label,
            expected_executable=False,
        )

    neq_artifacts = _exercise_published_neq_v2_precedent(repo_root)

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
        byte_count=cht_v1.FORMAL_DECISION_BYTE_COUNT,
        sha256=cht_v1.FORMAL_DECISION_SHA256,
        label="formal_CHT_human_decision",
        expected_executable=False,
    )

    for relative, byte_count, sha256, label, legacy_mode in (
        cht_v1.FROZEN_REVIEW_PACKAGE_BINDINGS
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
        cht_v1.IMMUTABLE_SEMANTIC_OWNER_BINDINGS
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
        cht_v1.ARCHITECTURE_PRECEDENT_BINDINGS
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
    _validate_neq_scientific_matrix(
        architecture_payloads[
            "NEQ_LATEST_MATRIX_AND_EXCLUDE_VOCABULARY_PRECEDENT"
        ],
        neq_artifacts["covapie_neq_event_task_label_availability_v1.csv"],
    )

    exclude_payloads: dict[str, bytes] = {}
    for relative, byte_count, sha256, label in (
        cht_v1.EXCLUDE_SEMANTIC_PRECEDENT_BINDINGS
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
    for relative, byte_count, sha256, label in cht_v1.CURRENT_CENSUS_BINDINGS:
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
        normalized = cht_v1._validate_formal_decision_v1(formal)
    except json.JSONDecodeError as error:
        raise CHTSourceBindingV2Error(
            f"{_ERROR_PREFIX}:FORMAL_DECISION_JSON_INVALID"
        ) from error
    except cht_v1.CHTIngestionSafetyError as error:
        raise CHTSourceBindingV2Error(
            f"{_ERROR_PREFIX}:FORMAL_DECISION_SEMANTICS_INVALID:{error}"
        ) from error

    return {
        "formal": formal,
        "normalized": normalized,
        "formal_decision_binding": cht_v1._formal_binding(),
        "frozen_review_package_bindings": _review_binding_rows(),
        "immutable_semantic_owner_bindings": _binding_rows(
            cht_v1.IMMUTABLE_SEMANTIC_OWNER_BINDINGS,
            namespace="repository_relative",
        ),
        "architecture_precedent_bindings": _binding_rows(
            cht_v1.ARCHITECTURE_PRECEDENT_BINDINGS,
            namespace="repository_relative",
        ),
        "exclude_semantic_precedent_bindings": _binding_rows(
            cht_v1.EXCLUDE_SEMANTIC_PRECEDENT_BINDINGS,
            namespace="repository_relative",
        ),
        "current_published_census_bindings": _binding_rows(
            cht_v1.CURRENT_CENSUS_BINDINGS,
            namespace="repository_relative",
        ),
        "upstream_v2_migration_precedent": {
            "published_NEQ_V2_successor_bound": True,
            "NEQ_V2_sha256": NEQ_V2_SHA256,
            "NEQ_V2_published_commit": NEQ_V2_PUBLISHED_COMMIT,
            "NEQ_V2_source_binding_acceptance_active": True,
            "NEQ_V2_projection_actually_called": True,
            "NEQ_V1_scientific_matrix_preserved": True,
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


def verify_published_cht_v1_projection_v2(
    *,
    repo_root: Path,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, bytes]:
    """Prove source-derived CHT science equals the published V1 Exact4."""

    repo_root = repo_root.resolve()
    overrides = _normalize_overrides(repository_path_overrides)
    bound = load_frozen_cht_authority_v2(
        repo_root=repo_root,
        repository_path_overrides=overrides,
    )
    artifacts: dict[str, bytes] = {}
    for relative, byte_count, sha256, label in _PUBLISHED_CHT_V1_OUTPUT_BINDINGS:
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

    snapshot = cht_v1._snapshot(bound)
    source_derived = {
        cht_v1.SNAPSHOT: cht_v1._json_bytes(snapshot),
        cht_v1.MATRIX: cht_v1._csv_bytes(
            cht_v1.MATRIX_HEADER, cht_v1._matrix_rows(snapshot)
        ),
        cht_v1.SUMMARY: cht_v1._json_bytes(cht_v1._summary()),
    }
    if any(artifacts[name] != payload for name, payload in source_derived.items()):
        _fail("PUBLISHED_V1_SCIENTIFIC_PROJECTION_MISMATCH")
    try:
        manifest = json.loads(artifacts[cht_v1.MANIFEST])
    except json.JSONDecodeError as error:
        raise CHTSourceBindingV2Error(
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
                _FROZEN_CHT_V1_CODE_BINDINGS,
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
        or manifest.get("exclude_semantic_precedent_bindings")
        != bound["exclude_semantic_precedent_bindings"]
        or manifest.get("immutable_semantic_owner_bindings")
        != bound["immutable_semantic_owner_bindings"]
        or manifest.get("current_published_census_bindings")
        != bound["current_published_census_bindings"]
        or manifest.get("canonical_task_contract")
        != cht_v1._canonical_task_contract()
        or manifest.get("source_CCD_and_topology_boundary")
        != cht_v1._source_ccd_and_event_topology_boundary()
        or manifest.get("authority_boundary") != cht_v1._authority_boundary()
        or manifest.get("human_authority_ingestion_semantics")
        != {
            "authority_source": cht_v1.AUTHORITY_SOURCE,
            "authority_scope": cht_v1.AUTHORITY_SCOPE,
            "authority_ingested": True,
            "authority_created_by_ingestion": False,
            "formal_event_training_use_decision": "EXCLUDE_FROM_TRAINING_ONLY",
            "human_training_excluded": True,
            "training_use_allowed": False,
            "candidate_for_future_training_admission": False,
            "training_admitted": False,
        }
        or manifest.get("output_artifact_bindings")
        != {
            name: {"sha256": sha256}
            for name, sha256 in (
                (cht_v1.SNAPSHOT, _PUBLISHED_CHT_V1_OUTPUT_BINDINGS[0][2]),
                (cht_v1.MATRIX, _PUBLISHED_CHT_V1_OUTPUT_BINDINGS[1][2]),
                (cht_v1.SUMMARY, _PUBLISHED_CHT_V1_OUTPUT_BINDINGS[2][2]),
            )
        }
        or manifest.get("ready_for_training") is not False
    ):
        _fail("PUBLISHED_V1_MANIFEST_SEMANTICS_INVALID")
    return artifacts
