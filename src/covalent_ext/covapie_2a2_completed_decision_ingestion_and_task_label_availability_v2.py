"""Thin 2A2 V2 source-binding successor over the frozen V1 science.

V2 changes only active filesystem acceptance. Direct formal sources and the
embedded Exact11 evidence inventory retain their historical mode provenance,
but live files are accepted by the B1 security, content, and executable-class
contract instead of exact numeric POSIX mode equality.
"""

from __future__ import annotations

import ast
from collections import Counter
from collections.abc import Mapping, Sequence
import copy
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, NoReturn

from covalent_ext import (
    covapie_2a2_completed_decision_ingestion_and_task_label_availability_v1
    as two_a2_v1,
)
from covalent_ext import (
    covapie_f24_completed_decision_ingestion_and_task_label_availability_v2
    as f24_v2,
)
from covalent_ext.covapie_source_binding_policy_v2 import (
    SourceBindingPolicyV2Error,
    verify_bound_source_v2,
)


__all__ = (
    "TwoA2SourceBindingV2Error",
    "load_frozen_two_a2_authority_v2",
    "verify_published_two_a2_v1_projection_v2",
)


_ERROR_PREFIX = "COVAPIE_2A2_SOURCE_BINDING_V2_ERROR"

SOURCE_BINDING_POLICY_V2_RELATIVE = Path(
    "src/covalent_ext/covapie_source_binding_policy_v2.py"
)
SOURCE_BINDING_POLICY_V2_BYTE_COUNT = 3704
SOURCE_BINDING_POLICY_V2_SHA256 = (
    "c17f3532e6004b347ff62e5d354ac1843f384196c2207127e17971acd2e2d4ee"
)

F24_V2_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_f24_completed_decision_ingestion_and_task_label_availability_v2.py"
)
F24_V2_BYTE_COUNT = 25212
F24_V2_SHA256 = (
    "c83aa221721849cff1ee9e3fed4154204333edb6207ec6cceb70348802bcf253"
)
F24_V2_CHECKER_RELATIVE = Path(
    "scripts/"
    "check_covapie_f24_completed_decision_ingestion_and_task_label_availability_v2.py"
)
F24_V2_CHECKER_BYTE_COUNT = 44863
F24_V2_CHECKER_SHA256 = (
    "51a8af193c8c2eeb097a53cac66a25c0688b5e9066c6e07f0891fbbf897746a9"
)
F24_V2_PUBLISHED_COMMIT = "a81be8b1260d14b385b0faf05e2ddcc56bd403d8"

TWO_A2_V1_OWNER_BYTE_COUNT = 81311
TWO_A2_V1_OWNER_SHA256 = (
    "57d42fcf673794f27adc7b897c0f51db4304d32f2d35a950b89d63cf4cf7060d"
)
TWO_A2_V1_CHECKER_BYTE_COUNT = 16795
TWO_A2_V1_CHECKER_SHA256 = (
    "dadb213ad9232e7ecd0e7ae55849357ead00b67cfdac9f95f10b8293bce81468"
)
TWO_A2_V1_TEST_BYTE_COUNT = 24462
TWO_A2_V1_TEST_SHA256 = (
    "3fe52260ec2bf8121adb9a6323ec8a624cfa343c6a5cde4393d68dd6b2d4830c"
)

_FROZEN_TWO_A2_V1_CODE_BINDINGS = (
    (
        two_a2_v1.SOURCE_RELATIVE,
        TWO_A2_V1_OWNER_BYTE_COUNT,
        TWO_A2_V1_OWNER_SHA256,
        "published_2A2_V1_owner",
    ),
    (
        two_a2_v1.CHECKER_RELATIVE,
        TWO_A2_V1_CHECKER_BYTE_COUNT,
        TWO_A2_V1_CHECKER_SHA256,
        "published_2A2_V1_checker",
    ),
    (
        two_a2_v1.TEST_RELATIVE,
        TWO_A2_V1_TEST_BYTE_COUNT,
        TWO_A2_V1_TEST_SHA256,
        "published_2A2_V1_tests",
    ),
)

_PUBLISHED_TWO_A2_V1_OUTPUT_BINDINGS = (
    (
        two_a2_v1.OUTPUT_ROOT_RELATIVE / two_a2_v1.SNAPSHOT,
        29063,
        "87cfffd1c9e2e82db6d9aeba2dfedc907b459d89c0160c50fb9fbddee7393000",
        "published_2A2_V1_snapshot",
    ),
    (
        two_a2_v1.OUTPUT_ROOT_RELATIVE / two_a2_v1.MATRIX,
        8950,
        "f6533013dcb2eea5fcee579d906c7ab3009d1db8c9f2d9f906aca5ee0122f52b",
        "published_2A2_V1_matrix",
    ),
    (
        two_a2_v1.OUTPUT_ROOT_RELATIVE / two_a2_v1.SUMMARY,
        4623,
        "6c5a92910becab41a4e3af0317fa3438d6a682e1dac4d4ef1d4e48fe34773ea2",
        "published_2A2_V1_summary",
    ),
    (
        two_a2_v1.OUTPUT_ROOT_RELATIVE / two_a2_v1.MANIFEST,
        19083,
        "af20556b9a9197d2c9ddfd3fc19d01ef43a51f935aa1fdc29bac0e4c5f410287",
        "published_2A2_V1_manifest",
    ),
)

CURRENT_TWO_A2_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_2a2_v1"
)
_CURRENT_TWO_A2_GLOBAL_BINDINGS = (
    (
        CURRENT_TWO_A2_ROOT
        / "covapie_cumulative1000_current_global_readiness_census_with_2a2_v1.csv",
        529994,
        "5b56422e9c8d0ec6c09fe71c49d51fff0c7e7a9720ccf3c4c20dc324e409c57d",
        "current_2A2_global_census_matrix",
    ),
    (
        CURRENT_TWO_A2_ROOT
        / "covapie_cumulative1000_current_global_readiness_summary_with_2a2_v1.json",
        17389,
        "3217bf5e45de40e66f1af22d000a48fef81548c6431c3e6d9349c4824b1c80f3",
        "current_2A2_global_census_summary",
    ),
    (
        CURRENT_TWO_A2_ROOT
        / "covapie_cumulative1000_current_global_readiness_manifest_with_2a2_v1.json",
        47068,
        "c30f8f52fc20495a06f7bead98ac80197f434eeb0b4776a1ef2c152f13d1e2b7",
        "current_2A2_global_census_manifest",
    ),
)

_FROZEN_TWO_A2_V1_CANDIDATE_BINDINGS = [
    {
        "path": relative.as_posix(),
        "path_namespace": "repository_relative",
        "byte_count": byte_count,
        "sha256": sha256,
        "sha256_scope": "file_bytes",
        "source_role": source_role,
    }
    for (relative, byte_count, sha256, _label), source_role in zip(
        _FROZEN_TWO_A2_V1_CODE_BINDINGS,
        ("production_owner", "fail_closed_checker", "targeted_test_contract"),
        strict=True,
    )
]

_EXPECTED_EMBEDDED_ROLES = (
    "machine_evidence_manifest",
    "exact4_event_review",
    "graph_and_role_candidates",
    "human_review_guide",
    "unsigned_human_decision_template",
    "preparation_package_validator",
    "non_authoritative_human_review_scientific_preview",
    "human_review_scientific_preview_validator",
    "published_role_profile_runtime_owner",
    "canonical_role_and_task_semantics_owner",
    "published_1f8_event_task_label_availability",
)
_EXPECTED_EMBEDDED_MODES = (
    "0664",
    "0664",
    "0664",
    "0664",
    "0664",
    "0664",
    "0664",
    "0664",
    "0644",
    "0644",
    "0600",
)

_RUNTIME_MODULE_NAME = (
    "covalent_ext.covapie_direct_attachment_optional_linker_runtime_v1"
)
_FORMAL_VALIDATOR_REPORT = {
    "exact_file_count": 2,
    "files": [
        {
            "byte_count": 26532,
            "line_count": 640,
            "mode": "0o664",
            "name": "2a2_formal_human_decision_v1.json",
            "sha256": (
                "f0b10505af55883a3a4305a637b2299d2d5e1a25ef9f8e979efaad361d7351bd"
            ),
        },
        {
            "byte_count": 69082,
            "line_count": 1450,
            "mode": "0o664",
            "name": "validate_2a2_formal_human_decision_v1.py",
            "sha256": (
                "855ec10d9a311bdbdc3185e6c83b7f7d272e810ebfcbd5aeb9a4230a0d870715"
            ),
        },
    ],
    "formal_authority_created": True,
    "formal_human_decision_valid": True,
    "human_decision_created": True,
    "ingestion_started": False,
    "ready_for_training": False,
    "status": "PASS",
}

_RECONCILIATION_INFORMATIONAL = {
    "status": "INFORMATIONAL_ONLY",
    "reconciled_this_step": False,
    "materialized_this_step": False,
    "current_published": {
        "universe_event_count": 338,
        "universe_review_unit_count": 131,
        "completed_positive_event_count": 91,
        "completed_positive_unit_count": 12,
        "completed_negative_event_count": 24,
        "completed_negative_unit_count": 4,
        "completed_total_event_count": 115,
        "completed_total_unit_count": 16,
        "in_progress_event_count": 0,
        "in_progress_unit_count": 0,
        "unreviewed_event_count": 223,
        "unreviewed_unit_count": 115,
    },
    "future_after_reconciliation": {
        "completed_positive_event_count": 95,
        "completed_positive_unit_count": 13,
        "completed_negative_event_count": 24,
        "completed_negative_unit_count": 4,
        "completed_total_event_count": 119,
        "completed_total_unit_count": 17,
        "unreviewed_event_count": 219,
        "unreviewed_unit_count": 114,
        "in_progress_event_count": 0,
        "in_progress_unit_count": 0,
        "normalized_INCLUDE": 27,
        "normalized_EXCLUDE_FROM_TRAINING_ONLY": 68,
    },
}


class TwoA2SourceBindingV2Error(ValueError):
    """Raised when the additive 2A2 V2 authority cannot be proven."""


def _fail(reason: str) -> NoReturn:
    raise TwoA2SourceBindingV2Error(f"{_ERROR_PREFIX}:{reason}")


def _validated_relative_path(value: object, label: str) -> Path:
    if type(value) is not str or not value:
        _fail("RELATIVE_PATH_INVALID:" + label)
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts:
        _fail("RELATIVE_PATH_INVALID:" + label)
    return relative


def _normalize_overrides(
    overrides: Mapping[Path, Path] | None,
) -> dict[Path, Path]:
    normalized: dict[Path, Path] = {}
    if overrides is None:
        return normalized
    for raw_relative, raw_replacement in overrides.items():
        relative = _validated_relative_path(
            Path(raw_relative).as_posix(), "REPOSITORY_PATH_OVERRIDE_KEY"
        )
        if relative in normalized:
            _fail("REPOSITORY_PATH_OVERRIDE_KEY_DUPLICATE")
        normalized[relative] = Path(raw_replacement)
    return normalized


def _all_two_a2_v1_bindings(
) -> tuple[tuple[Path, str, int, str, str, str | None], ...]:
    return (
        *two_a2_v1.FORMAL_BINDINGS,
        *two_a2_v1.SEMANTIC_OWNER_BINDINGS,
        *two_a2_v1.PRECEDENT_BINDINGS,
        *two_a2_v1.CENSUS_BINDINGS,
        *two_a2_v1.RECONCILIATION_BINDINGS,
    )


def _allowed_static_override_paths() -> set[Path]:
    return {
        *(binding[0] for binding in _all_two_a2_v1_bindings()),
        *(binding[0] for binding in _PUBLISHED_TWO_A2_V1_OUTPUT_BINDINGS),
        *(binding[0] for binding in _CURRENT_TWO_A2_GLOBAL_BINDINGS),
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
    if namespace == "project_parent_relative":
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
        raise TwoA2SourceBindingV2Error(
            f"{_ERROR_PREFIX}:BOUND_SOURCE_REJECTED:{label}:{error}"
        ) from error


def _expected_executable_from_legacy_mode(mode: object, label: str) -> bool:
    if (
        type(mode) is not str
        or len(mode) != 4
        or any(character not in "01234567" for character in mode)
    ):
        _fail("LEGACY_MODE_PROVENANCE_INVALID:" + label)
    return bool(int(mode, 8) & 0o111)


def _binding_record(
    binding: tuple[Path, str, int, str, str, str | None],
) -> dict[str, object]:
    relative, namespace, count, sha256, role, mode = binding
    record: dict[str, object] = {
        "path": relative.as_posix(),
        "path_namespace": namespace,
        "byte_count": count,
        "sha256": sha256,
        "sha256_scope": "file_bytes",
        "source_role": role,
    }
    if mode is not None:
        record["mode"] = mode
    return record


def _binding_records(
    bindings: Sequence[tuple[Path, str, int, str, str, str | None]],
) -> list[dict[str, object]]:
    return [_binding_record(binding) for binding in bindings]


def _literal_assignments_from_payload(
    payload: bytes, names: Sequence[str], label: str
) -> dict[str, object]:
    try:
        tree = ast.parse(payload.decode("utf-8"))
    except (UnicodeDecodeError, SyntaxError) as error:
        raise TwoA2SourceBindingV2Error(
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
                except (TypeError, ValueError) as error:
                    raise TwoA2SourceBindingV2Error(
                        f"{_ERROR_PREFIX}:SOURCE_LITERAL_INVALID:{target.id}"
                    ) from error
    if set(values) != wanted:
        _fail("SOURCE_LITERAL_ASSIGNMENTS_MISSING:" + label)
    return values


def _validate_semantic_owner_payloads(payloads: Mapping[str, bytes]) -> None:
    runtime = _literal_assignments_from_payload(
        payloads["PUBLISHED_ROLE_PROFILE_RUNTIME_OWNER"],
        ("STRICT_LINKER_PRESENT_V1", "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"),
        "PUBLISHED_ROLE_PROFILE_RUNTIME_OWNER",
    )
    canonical = _literal_assignments_from_payload(
        payloads["CANONICAL_ROLE_AND_TASK_SEMANTICS_OWNER"],
        ("EXACT3_ROLES", "CANONICAL_TASKS"),
        "CANONICAL_ROLE_AND_TASK_SEMANTICS_OWNER",
    )
    if runtime != {
        "STRICT_LINKER_PRESENT_V1": "STRICT_LINKER_PRESENT_V1",
        "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1": (
            "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
        ),
    }:
        _fail("RUNTIME_ROLE_PROFILE_CONTRACT_DRIFT")
    if (
        canonical["EXACT3_ROLES"] != ("scaffold", "linker", "warhead")
        or canonical["CANONICAL_TASKS"] != two_a2_v1.CANONICAL_TASKS
    ):
        _fail("GLOBAL_CANONICAL_EXACT5_TASK_CONTRACT_DRIFT")


def _validate_runtime_module_source(repo_root: Path) -> None:
    expected = (repo_root / two_a2_v1.SEMANTIC_OWNER_BINDINGS[0][0]).resolve()
    spec = importlib.util.find_spec(_RUNTIME_MODULE_NAME)
    if spec is None or spec.origin is None or Path(spec.origin).resolve() != expected:
        _fail("PUBLISHED_RUNTIME_MODULE_RESOLUTION_INVALID")
    module = sys.modules.get(_RUNTIME_MODULE_NAME)
    if module is not None:
        origin = getattr(module, "__file__", None)
        if origin is None or Path(origin).resolve() != expected:
            _fail("PUBLISHED_RUNTIME_IMPORTED_SOURCE_INVALID")


def _validate_imported_runtime_module_source(repo_root: Path) -> None:
    expected = (repo_root / two_a2_v1.SEMANTIC_OWNER_BINDINGS[0][0]).resolve()
    module = sys.modules.get(_RUNTIME_MODULE_NAME)
    origin = getattr(module, "__file__", None) if module is not None else None
    if origin is None or Path(origin).resolve() != expected:
        _fail("PUBLISHED_RUNTIME_IMPORTED_SOURCE_INVALID")


def _exercise_published_f24_v2_predecessor(repo_root: Path) -> dict[str, bytes]:
    try:
        artifacts = f24_v2.verify_published_f24_v1_projection_v2(
            repo_root=repo_root
        )
    except f24_v2.F24SourceBindingV2Error as error:
        raise TwoA2SourceBindingV2Error(
            f"{_ERROR_PREFIX}:PUBLISHED_F24_V2_PREDECESSOR_REJECTED:{error}"
        ) from error
    if tuple(artifacts) != (
        "covapie_f24_completed_human_decision_snapshot_v1.json",
        "covapie_f24_event_task_label_availability_v1.csv",
        "covapie_f24_completed_decision_ingestion_summary_v1.json",
        "covapie_f24_completed_decision_ingestion_manifest_v1.json",
    ):
        _fail("PUBLISHED_F24_V2_PREDECESSOR_PROJECTION_INVALID")
    return artifacts


def _verify_static_v1_binding_group(
    *,
    repo_root: Path,
    bindings: Sequence[tuple[Path, str, int, str, str, str | None]],
    overrides: Mapping[Path, Path],
) -> dict[Path, bytes]:
    payloads: dict[Path, bytes] = {}
    for relative, namespace, count, sha256, role, _mode in bindings:
        payloads[relative] = _verify_source(
            path=_resolved_path(
                repo_root=repo_root,
                relative=relative,
                namespace=namespace,
                overrides=overrides,
            ),
            byte_count=count,
            sha256=sha256,
            label=role,
            expected_executable=False,
        )
    return payloads


def _verify_embedded_formal_evidence_v2(
    *,
    repo_root: Path,
    records: object,
    overrides: Mapping[Path, Path],
) -> tuple[list[dict[str, object]], dict[Path, bytes]]:
    if type(records) is not list or len(records) != 11:
        _fail("FORMAL_EVIDENCE_BINDING_COUNT_INVALID")
    required = {
        "path",
        "path_namespace",
        "byte_count",
        "mode",
        "sha256",
        "source_role",
        "regular_file",
        "non_symlink",
    }
    normalized: list[dict[str, object]] = []
    payloads: dict[Path, bytes] = {}
    for index, record in enumerate(records):
        if type(record) is not dict or set(record) != required:
            _fail("FORMAL_EVIDENCE_BINDING_SCHEMA_INVALID")
        role = record.get("source_role")
        label = str(role)
        relative = _validated_relative_path(record.get("path"), label)
        if (
            role != _EXPECTED_EMBEDDED_ROLES[index]
            or record.get("mode") != _EXPECTED_EMBEDDED_MODES[index]
            or record.get("path_namespace") != "project_parent_relative"
            or record.get("regular_file") is not True
            or record.get("non_symlink") is not True
            or type(record.get("byte_count")) is not int
            or record["byte_count"] <= 0
            or type(record.get("sha256")) is not str
            or len(record["sha256"]) != 64
            or any(character not in "0123456789abcdef" for character in record["sha256"])
            or relative in payloads
        ):
            _fail("FORMAL_EVIDENCE_BINDING_BOUNDARY_INVALID:" + label)
        expected_executable = _expected_executable_from_legacy_mode(
            record["mode"], label
        )
        payloads[relative] = _verify_source(
            path=_resolved_path(
                repo_root=repo_root,
                relative=relative,
                namespace="project_parent_relative",
                overrides=overrides,
            ),
            byte_count=record["byte_count"],
            sha256=record["sha256"],
            label=label,
            expected_executable=expected_executable,
        )
        normalized.append(copy.deepcopy(record))
    return normalized, payloads


def _current_two_a2_global_census(
    payloads: Mapping[Path, bytes],
) -> dict[str, int]:
    summary_relative = _CURRENT_TWO_A2_GLOBAL_BINDINGS[1][0]
    try:
        summary = json.loads(payloads[summary_relative])
    except json.JSONDecodeError as error:
        raise TwoA2SourceBindingV2Error(
            f"{_ERROR_PREFIX}:CURRENT_2A2_SUMMARY_JSON_INVALID"
        ) from error
    tasks = {
        task["display_alias"]: task[
            "structurally_applicable_authoritative_role_count"
        ]
        for task in summary.get("canonical_exact5", {}).get("tasks", [])
    }
    observed = {
        "positive": summary.get("chemistry", {}).get("POSITIVE", {}).get("count"),
        "relevant": summary.get("task_relevance", {})
        .get("RELEVANT", {})
        .get("count"),
        "training_INCLUDE": summary.get("training_use", {})
        .get("INCLUDE", {})
        .get("count"),
        "training_EXCLUDE": summary.get("training_use", {})
        .get("EXCLUDE_FROM_TRAINING_ONLY", {})
        .get("count"),
        "future_candidates": summary.get("training_stage", {}).get(
            "future_training_admission_candidate_count"
        ),
        "pair_sample_authority": summary.get("reactive_pair", {}).get(
            "sample_level_authoritative_pair_count"
        ),
        "role_sample_authority": summary.get("role", {}).get(
            "role_partition_sample_authoritative_count"
        ),
        "A": tasks.get("A"),
        "B": tasks.get("B"),
        "B2": tasks.get("B2"),
        "B3": tasks.get("B3"),
        "C": tasks.get("C"),
    }
    expected = {
        "positive": 112,
        "relevant": 113,
        "training_INCLUDE": 44,
        "training_EXCLUDE": 68,
        "future_candidates": 27,
        "pair_sample_authority": 112,
        "role_sample_authority": 112,
        "A": 112,
        "B": 52,
        "B2": 52,
        "B3": 112,
        "C": 112,
    }
    if observed != expected:
        _fail("CURRENT_2A2_GLOBAL_CENSUS_DRIFT")
    return observed  # type: ignore[return-value]


def load_frozen_two_a2_authority_v2(
    *,
    repo_root: Path,
    formal_decision_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]:
    """Load frozen 2A2 authority through B1 without exact-mode acceptance."""

    repo_root = repo_root.resolve()
    overrides = _normalize_overrides(repository_path_overrides)
    formal_relative = two_a2_v1.FORMAL_BINDINGS[0][0]
    if formal_decision_path is not None and formal_relative in overrides:
        _fail("FORMAL_DECISION_PATH_AMBIGUOUS")

    _verify_source(
        path=repo_root / SOURCE_BINDING_POLICY_V2_RELATIVE,
        byte_count=SOURCE_BINDING_POLICY_V2_BYTE_COUNT,
        sha256=SOURCE_BINDING_POLICY_V2_SHA256,
        label="published_source_binding_policy_v2",
        expected_executable=False,
    )
    for relative, byte_count, sha256, label in (
        (
            F24_V2_RELATIVE,
            F24_V2_BYTE_COUNT,
            F24_V2_SHA256,
            "published_F24_V2_successor",
        ),
        (
            F24_V2_CHECKER_RELATIVE,
            F24_V2_CHECKER_BYTE_COUNT,
            F24_V2_CHECKER_SHA256,
            "published_F24_V2_checker",
        ),
        *_FROZEN_TWO_A2_V1_CODE_BINDINGS,
    ):
        _verify_source(
            path=repo_root / relative,
            byte_count=byte_count,
            sha256=sha256,
            label=label,
            expected_executable=False,
        )

    _exercise_published_f24_v2_predecessor(repo_root)

    formal_payloads: dict[Path, bytes] = {}
    for binding in two_a2_v1.FORMAL_BINDINGS:
        relative, namespace, count, sha256, role, historical_mode = binding
        if relative == formal_relative and formal_decision_path is not None:
            path = Path(formal_decision_path)
            if not path.is_absolute():
                path = repo_root / path
        else:
            path = _resolved_path(
                repo_root=repo_root,
                relative=relative,
                namespace=namespace,
                overrides=overrides,
            )
        formal_payloads[relative] = _verify_source(
            path=path,
            byte_count=count,
            sha256=sha256,
            label=role,
            expected_executable=_expected_executable_from_legacy_mode(
                historical_mode, role
            ),
        )

    try:
        formal = two_a2_v1._strict_json(
            formal_payloads[formal_relative], "2A2_FORMAL_DECISION"
        )
        two_a2_v1._validate_formal_decision_v1(formal)
    except two_a2_v1.TwoA2IngestionSafetyError as error:
        raise TwoA2SourceBindingV2Error(
            f"{_ERROR_PREFIX}:TWO_A2_V1_SCIENTIFIC_SEMANTICS_INVALID:{error}"
        ) from error
    evidence = formal.get("evidence_provenance")
    if type(evidence) is not dict:
        _fail("FORMAL_EVIDENCE_PROVENANCE_MISSING")
    evidence_records = evidence.get("source_bindings")
    embedded_relatives = {
        _validated_relative_path(record.get("path"), str(record.get("source_role")))
        for record in evidence_records
        if type(record) is dict
    } if type(evidence_records) is list else set()
    if set(overrides) - (_allowed_static_override_paths() | embedded_relatives):
        _fail("REPOSITORY_PATH_OVERRIDE_UNEXPECTED")

    embedded_bindings, evidence_payloads = _verify_embedded_formal_evidence_v2(
        repo_root=repo_root,
        records=evidence_records,
        overrides=overrides,
    )

    semantic_payloads_by_path = _verify_static_v1_binding_group(
        repo_root=repo_root,
        bindings=two_a2_v1.SEMANTIC_OWNER_BINDINGS,
        overrides=overrides,
    )
    semantic_payloads = {
        binding[4]: semantic_payloads_by_path[binding[0]]
        for binding in two_a2_v1.SEMANTIC_OWNER_BINDINGS
    }
    _validate_semantic_owner_payloads(semantic_payloads)
    _validate_runtime_module_source(repo_root)
    try:
        runtime_result = two_a2_v1._validate_published_runtime(
            formal, evidence_payloads
        )
    except two_a2_v1.TwoA2IngestionSafetyError as error:
        raise TwoA2SourceBindingV2Error(
            f"{_ERROR_PREFIX}:PUBLISHED_RUNTIME_VALIDATION_INVALID:{error}"
        ) from error
    _validate_imported_runtime_module_source(repo_root)

    _verify_static_v1_binding_group(
        repo_root=repo_root,
        bindings=two_a2_v1.PRECEDENT_BINDINGS,
        overrides=overrides,
    )
    census_payloads = _verify_static_v1_binding_group(
        repo_root=repo_root,
        bindings=two_a2_v1.CENSUS_BINDINGS,
        overrides=overrides,
    )
    _verify_static_v1_binding_group(
        repo_root=repo_root,
        bindings=two_a2_v1.RECONCILIATION_BINDINGS,
        overrides=overrides,
    )
    try:
        historical_census = two_a2_v1._current_census_boundary(census_payloads)
        future_census = two_a2_v1._future_census_informational(
            historical_census
        )
    except two_a2_v1.TwoA2IngestionSafetyError as error:
        raise TwoA2SourceBindingV2Error(
            f"{_ERROR_PREFIX}:HISTORICAL_CENSUS_SEMANTICS_INVALID:{error}"
        ) from error

    current_global_payloads: dict[Path, bytes] = {}
    for relative, byte_count, sha256, label in _CURRENT_TWO_A2_GLOBAL_BINDINGS:
        current_global_payloads[relative] = _verify_source(
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
    current_global_census = _current_two_a2_global_census(current_global_payloads)

    direct_modes = [binding[5] for binding in two_a2_v1.FORMAL_BINDINGS]
    embedded_modes = [record["mode"] for record in embedded_bindings]
    all_modes = [*direct_modes, *embedded_modes]
    executable_classes = [
        _expected_executable_from_legacy_mode(mode, "MODE_INVENTORY")
        for mode in all_modes
    ]
    if (
        direct_modes != ["0664", "0664"]
        or embedded_modes != list(_EXPECTED_EMBEDDED_MODES)
        or Counter(all_modes) != {"0664": 10, "0644": 2, "0600": 1}
        or executable_classes != [False] * 13
    ):
        _fail("TWO_A2_EXACT13_MODE_INVENTORY_INVALID")

    return {
        "formal": formal,
        "formal_decision_binding": _binding_record(two_a2_v1.FORMAL_BINDINGS[0]),
        "formal_validator_binding": _binding_record(two_a2_v1.FORMAL_BINDINGS[1]),
        "formal_evidence_bindings": embedded_bindings,
        "semantic_owner_bindings": _binding_records(
            two_a2_v1.SEMANTIC_OWNER_BINDINGS
        ),
        "precedent_bindings": _binding_records(two_a2_v1.PRECEDENT_BINDINGS),
        "current_census_bindings": _binding_records(two_a2_v1.CENSUS_BINDINGS),
        "current_reconciliation_bindings": _binding_records(
            two_a2_v1.RECONCILIATION_BINDINGS
        ),
        "formal_validator_result": copy.deepcopy(_FORMAL_VALIDATOR_REPORT),
        "published_runtime_result": runtime_result,
        "current_published_census_boundary": historical_census,
        "future_census_informational": future_census,
        "reconciliation_informational": copy.deepcopy(
            _RECONCILIATION_INFORMATIONAL
        ),
        "current_2A2_global_census": current_global_census,
        "published_f24_v2_predecessor": {
            "published_F24_V2_successor_bound": True,
            "F24_V2_sha256": F24_V2_SHA256,
            "F24_V2_checker_sha256": F24_V2_CHECKER_SHA256,
            "F24_V2_published_commit": F24_V2_PUBLISHED_COMMIT,
            "F24_V2_projection_actually_called": True,
            "F24_V1_ingestion_projection_preserved": True,
        },
        "source_binding_v2": {
            "combined_helper": "verify_bound_source_v2",
            "direct_mode_bound_source_count": 2,
            "formal_embedded_evidence_count": 11,
            "formal_embedded_evidence_exact_count": 11,
            "total_historical_mode_bearing_records": 13,
            "historical_mode_counts": {"0664": 10, "0644": 2, "0600": 1},
            "expected_executable_classes": executable_classes,
            "all_expected_executable": False,
            "formal_validator_expected_nonexecutable": True,
            "preparation_validator_expected_nonexecutable": True,
            "preview_validator_expected_nonexecutable": True,
            "embedded_1F8_0600_precedent_expected_nonexecutable": True,
            "exact_posix_numeric_mode_semantic_acceptance": False,
            "embedded_exact_posix_numeric_mode_semantic_acceptance": False,
        },
        "runtime_bound_before_role_validation": True,
        "historical_F24_prior_census_preserved": True,
        "historical_informational_future_projection_preserved": True,
        "current_2A2_global_census_unchanged": True,
        "reconciled_this_step": False,
        "ready_for_training": False,
    }


def _validate_published_v1_manifest(
    manifest: Mapping[str, Any],
    expected: Mapping[str, Any],
    bound: Mapping[str, object],
    artifacts: Mapping[str, bytes],
) -> None:
    if manifest != expected:
        _fail("PUBLISHED_V1_MANIFEST_CLOSURE_INVALID")
    output_bindings = manifest.get("output_artifact_bindings", {})
    expected_output_digests = {
        two_a2_v1.SNAPSHOT: _PUBLISHED_TWO_A2_V1_OUTPUT_BINDINGS[0][2],
        two_a2_v1.MATRIX: _PUBLISHED_TWO_A2_V1_OUTPUT_BINDINGS[1][2],
        two_a2_v1.SUMMARY: _PUBLISHED_TWO_A2_V1_OUTPUT_BINDINGS[2][2],
    }
    if (
        manifest.get("candidate_source_bindings")
        != _FROZEN_TWO_A2_V1_CANDIDATE_BINDINGS
        or manifest.get("formal_decision_binding")
        != bound["formal_decision_binding"]
        or manifest.get("formal_validator_binding")
        != bound["formal_validator_binding"]
        or manifest.get("formal_evidence_bindings")
        != bound["formal_evidence_bindings"]
        or manifest.get("semantic_owner_bindings")
        != bound["semantic_owner_bindings"]
        or manifest.get("precedent_bindings") != bound["precedent_bindings"]
        or manifest.get("current_published_census_bindings")
        != bound["current_census_bindings"]
        or manifest.get("current_reconciliation_bindings")
        != bound["current_reconciliation_bindings"]
        or manifest.get("canonical_task_contract")
        != two_a2_v1._canonical_task_contract()
        or manifest.get("chemical_warhead_vs_role_region", {}).get(
            "chemical_warhead_atom_ids"
        )
        is not None
        or manifest.get("chemical_warhead_vs_role_region", {}).get(
            "chemical_warhead_human_authoritative"
        )
        is not False
        or manifest.get("human_authority_ingestion_semantics", {}).get(
            "candidate_for_future_training_admission"
        )
        is not False
        or manifest.get("human_authority_ingestion_semantics", {}).get(
            "training_admitted"
        )
        is not False
        or manifest.get("ready_for_training") is not False
        or manifest.get("manifest_self_sha256_recorded") is not False
        or {
            name: record.get("sha256")
            for name, record in output_bindings.items()
        }
        != expected_output_digests
        or tuple(artifacts) != two_a2_v1.OUTPUT_FILENAMES
    ):
        _fail("PUBLISHED_V1_MANIFEST_SEMANTICS_INVALID")


def verify_published_two_a2_v1_projection_v2(
    *,
    repo_root: Path,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, bytes]:
    """Prove B1-bound 2A2 science equals the published V1 Exact4."""

    repo_root = repo_root.resolve()
    overrides = _normalize_overrides(repository_path_overrides)
    bound = load_frozen_two_a2_authority_v2(
        repo_root=repo_root,
        repository_path_overrides=overrides,
    )
    artifacts: dict[str, bytes] = {}
    for relative, byte_count, sha256, label in (
        _PUBLISHED_TWO_A2_V1_OUTPUT_BINDINGS
    ):
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

    snapshot = two_a2_v1._snapshot(bound)
    snapshot_payload = two_a2_v1._json_bytes(snapshot)
    rows = two_a2_v1._matrix_rows(snapshot)
    matrix_payload = two_a2_v1._csv_bytes(two_a2_v1.MATRIX_HEADER, rows)
    summary_payload = two_a2_v1._json_bytes(
        two_a2_v1._summary_from_rows(
            rows,
            bound["current_published_census_boundary"],
            bound["future_census_informational"],
            bound["reconciliation_informational"],
        )
    )
    source_derived = {
        two_a2_v1.SNAPSHOT: snapshot_payload,
        two_a2_v1.MATRIX: matrix_payload,
        two_a2_v1.SUMMARY: summary_payload,
    }
    if any(artifacts[name] != payload for name, payload in source_derived.items()):
        _fail("PUBLISHED_V1_SCIENTIFIC_PROJECTION_MISMATCH")
    try:
        manifest = json.loads(artifacts[two_a2_v1.MANIFEST])
    except json.JSONDecodeError as error:
        raise TwoA2SourceBindingV2Error(
            f"{_ERROR_PREFIX}:PUBLISHED_V1_MANIFEST_JSON_INVALID"
        ) from error
    expected_manifest = two_a2_v1._manifest(
        bound,
        copy.deepcopy(_FROZEN_TWO_A2_V1_CANDIDATE_BINDINGS),
        artifacts[two_a2_v1.SNAPSHOT],
        artifacts[two_a2_v1.MATRIX],
        artifacts[two_a2_v1.SUMMARY],
    )
    _validate_published_v1_manifest(
        manifest, expected_manifest, bound, artifacts
    )
    return artifacts
