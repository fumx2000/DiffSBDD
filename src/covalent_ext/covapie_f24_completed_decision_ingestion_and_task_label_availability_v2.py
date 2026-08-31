"""Thin F24 V2 source-binding successor over the frozen V1 science.

V2 changes only active filesystem acceptance. Every consumed authority is
bound through the published B1 gate. Frozen F24 V1 provenance, scientific
semantics, published artifacts, and all training boundaries remain unchanged.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
import json
import importlib.util
from pathlib import Path
import sys
from typing import NoReturn

from covalent_ext import (
    covapie_f24_completed_decision_ingestion_and_task_label_availability_v1
    as f24_v1,
)
from covalent_ext import (
    covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2
    as ozj_v2,
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
    "F24SourceBindingV2Error",
    "load_frozen_f24_authority_v2",
    "verify_published_f24_v1_projection_v2",
)


_ERROR_PREFIX = "COVAPIE_F24_SOURCE_BINDING_V2_ERROR"

SOURCE_BINDING_POLICY_V2_RELATIVE = Path(
    "src/covalent_ext/covapie_source_binding_policy_v2.py"
)
SOURCE_BINDING_POLICY_V2_BYTE_COUNT = 3704
SOURCE_BINDING_POLICY_V2_SHA256 = (
    "c17f3532e6004b347ff62e5d354ac1843f384196c2207127e17971acd2e2d4ee"
)

OZJ_V2_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2.py"
)
OZJ_V2_BYTE_COUNT = 30745
OZJ_V2_SHA256 = (
    "51af9985cf4de28d48cc55eab71b536472220221d160ee6070677512ba22ef21"
)
OZJ_V2_CHECKER_RELATIVE = Path(
    "scripts/"
    "check_covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2.py"
)
OZJ_V2_CHECKER_BYTE_COUNT = 42913
OZJ_V2_CHECKER_SHA256 = (
    "dec67ac8e86273d49b3da048a7286b900b1171f93ffe85a07a6c1830383dd825"
)
OZJ_V2_PUBLISHED_COMMIT = "33d08ee6069592f0fe28ca53bed5615f578d10fc"

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

F24_V1_OWNER_BYTE_COUNT = 77160
F24_V1_OWNER_SHA256 = (
    "c67c88f83e535fd4319425459b97dcfc22f90a3b617b5ddbf1e8f315e2de0525"
)
F24_V1_CHECKER_BYTE_COUNT = 15600
F24_V1_CHECKER_SHA256 = (
    "d057ff1695f9797fd2c54f9c91737fde6edd7580c471759350d179bb807565a7"
)
F24_V1_TEST_BYTE_COUNT = 23978
F24_V1_TEST_SHA256 = (
    "f2c0a9c082178db596d98ec051251b71158bb791a2ec55eebecdf9f93bf0cc77"
)

_FROZEN_F24_V1_CODE_BINDINGS = (
    (
        f24_v1.SOURCE_RELATIVE,
        F24_V1_OWNER_BYTE_COUNT,
        F24_V1_OWNER_SHA256,
        "published_F24_V1_owner",
    ),
    (
        f24_v1.CHECKER_RELATIVE,
        F24_V1_CHECKER_BYTE_COUNT,
        F24_V1_CHECKER_SHA256,
        "published_F24_V1_checker",
    ),
    (
        f24_v1.TEST_RELATIVE,
        F24_V1_TEST_BYTE_COUNT,
        F24_V1_TEST_SHA256,
        "published_F24_V1_tests",
    ),
)

_PUBLISHED_F24_V1_OUTPUT_BINDINGS = (
    (
        f24_v1.OUTPUT_ROOT_RELATIVE / f24_v1.SNAPSHOT,
        22044,
        "d53ff475b0d86b076b5649916cd7118821e8c883daba5727b1efd7f051b8de11",
        "published_F24_V1_snapshot",
    ),
    (
        f24_v1.OUTPUT_ROOT_RELATIVE / f24_v1.MATRIX,
        7641,
        "516c3ea3ac291c5039e1def72a891b54fd42d5aa45388f27b436a655467cd28c",
        "published_F24_V1_matrix",
    ),
    (
        f24_v1.OUTPUT_ROOT_RELATIVE / f24_v1.SUMMARY,
        3462,
        "be67578dac2c6593bc75b256cd9c344c90f8650662443ff5cd316bb68b18b385",
        "published_F24_V1_summary",
    ),
    (
        f24_v1.OUTPUT_ROOT_RELATIVE / f24_v1.MANIFEST,
        16125,
        "02f56545297fb78c2b2cbd205115d9dca680a8446bfb753109428b698bdd5dfd",
        "published_F24_V1_manifest",
    ),
)

_FROZEN_DUAL_V2_BINDINGS = (
    (
        OZJ_V2_RELATIVE,
        OZJ_V2_BYTE_COUNT,
        OZJ_V2_SHA256,
        "published_OZJ_V2_successor",
    ),
    (
        OZJ_V2_CHECKER_RELATIVE,
        OZJ_V2_CHECKER_BYTE_COUNT,
        OZJ_V2_CHECKER_SHA256,
        "published_OZJ_V2_checker",
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

_RUNTIME_MODULE_NAME = (
    "covalent_ext.covapie_direct_attachment_optional_linker_runtime_v1"
)
_FORMAL_VALIDATOR_REPORT = {
    "exact_event_count": 4,
    "exact_file_count": 2,
    "formal_human_decision_created": True,
    "formal_validator": "PASS",
    "published_runtime_validation": "PASS",
    "ready_for_training": False,
    "schema_version": f24_v1.FORMAL_DECISION_SCHEMA,
    "semantic_digest_verified": True,
    "status": "PASS",
}


class F24SourceBindingV2Error(ValueError):
    """Raised when the additive F24 V2 authority cannot be proven."""


def _fail(reason: str) -> NoReturn:
    raise F24SourceBindingV2Error(f"{_ERROR_PREFIX}:{reason}")


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


def _all_f24_v1_bindings(
) -> tuple[tuple[Path, str, int, str, str, str | None], ...]:
    return (
        *f24_v1.FORMAL_BINDINGS,
        *f24_v1.PREPARATION_BINDINGS,
        *f24_v1.SEMANTIC_OWNER_BINDINGS,
        *f24_v1.PRECEDENT_BINDINGS,
        *f24_v1.CENSUS_BINDINGS,
    )


def _allowed_override_paths() -> set[Path]:
    return {
        *(row[0] for row in _all_f24_v1_bindings()),
        *(row[0] for row in _PUBLISHED_F24_V1_OUTPUT_BINDINGS),
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
        raise F24SourceBindingV2Error(
            f"{_ERROR_PREFIX}:BOUND_SOURCE_REJECTED:{label}:{error}"
        ) from error


def _expected_executable_from_legacy_mode(mode: str) -> bool:
    if len(mode) != 4 or any(character not in "01234567" for character in mode):
        _fail("LEGACY_MODE_PROVENANCE_INVALID")
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
        raise F24SourceBindingV2Error(
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
                    raise F24SourceBindingV2Error(
                        f"{_ERROR_PREFIX}:SOURCE_LITERAL_INVALID:{target.id}"
                    ) from error
    if set(values) != wanted:
        _fail("SOURCE_LITERAL_ASSIGNMENTS_MISSING:" + label)
    return values


def _validate_semantic_owner_payloads(payloads: Mapping[str, bytes]) -> None:
    runtime = _literal_assignments_from_payload(
        payloads["PUBLISHED_DIRECT_ROLE_RUNTIME_OWNER"],
        ("DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",),
        "PUBLISHED_DIRECT_ROLE_RUNTIME_OWNER",
    )
    canonical = _literal_assignments_from_payload(
        payloads["CANONICAL_ROLE_AND_TASK_SEMANTICS_OWNER"],
        ("EXACT3_ROLES", "CANONICAL_TASKS"),
        "CANONICAL_ROLE_AND_TASK_SEMANTICS_OWNER",
    )
    if runtime["DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"] != f24_v1.EXPECTED_ROLE_PROFILE:
        _fail("DIRECT_PROFILE_RUNTIME_CONTRACT_DRIFT")
    if (
        canonical["EXACT3_ROLES"] != ("scaffold", "linker", "warhead")
        or canonical["CANONICAL_TASKS"] != f24_v1.CANONICAL_TASKS
    ):
        _fail("GLOBAL_CANONICAL_EXACT5_TASK_CONTRACT_DRIFT")


def _validate_runtime_module_source(repo_root: Path) -> None:
    expected = (repo_root / f24_v1.SEMANTIC_OWNER_BINDINGS[0][0]).resolve()
    spec = importlib.util.find_spec(_RUNTIME_MODULE_NAME)
    if spec is None or spec.origin is None or Path(spec.origin).resolve() != expected:
        _fail("PUBLISHED_RUNTIME_MODULE_RESOLUTION_INVALID")
    module = sys.modules.get(_RUNTIME_MODULE_NAME)
    if module is not None:
        origin = getattr(module, "__file__", None)
        if origin is None or Path(origin).resolve() != expected:
            _fail("PUBLISHED_RUNTIME_IMPORTED_SOURCE_INVALID")


def _validate_imported_runtime_module_source(repo_root: Path) -> None:
    expected = (repo_root / f24_v1.SEMANTIC_OWNER_BINDINGS[0][0]).resolve()
    module = sys.modules.get(_RUNTIME_MODULE_NAME)
    origin = getattr(module, "__file__", None) if module is not None else None
    if origin is None or Path(origin).resolve() != expected:
        _fail("PUBLISHED_RUNTIME_IMPORTED_SOURCE_INVALID")


def _exercise_published_ozj_v2_predecessor(repo_root: Path) -> dict[str, bytes]:
    try:
        artifacts = ozj_v2.verify_published_ozj_v1_projection_v2(
            repo_root=repo_root
        )
    except ozj_v2.OZJSourceBindingV2Error as error:
        raise F24SourceBindingV2Error(
            f"{_ERROR_PREFIX}:PUBLISHED_OZJ_V2_PREDECESSOR_REJECTED:{error}"
        ) from error
    expected = (
        "covapie_ozj_completed_human_decision_snapshot_v1.json",
        "covapie_ozj_event_task_label_availability_v1.csv",
        "covapie_ozj_completed_decision_ingestion_summary_v1.json",
        "covapie_ozj_completed_decision_ingestion_manifest_v1.json",
    )
    if tuple(artifacts) != expected:
        _fail("PUBLISHED_OZJ_V2_PREDECESSOR_PROJECTION_INVALID")
    return artifacts


def _exercise_published_yun_v2_predecessor(repo_root: Path) -> dict[str, bytes]:
    try:
        artifacts = yun_v2.verify_published_yun_v1_projection_v2(
            repo_root=repo_root
        )
    except yun_v2.YUNSourceBindingV2Error as error:
        raise F24SourceBindingV2Error(
            f"{_ERROR_PREFIX}:PUBLISHED_YUN_V2_PREDECESSOR_REJECTED:{error}"
        ) from error
    expected = (
        "covapie_yun_completed_human_decision_snapshot_v1.json",
        "covapie_yun_event_task_label_availability_v1.csv",
        "covapie_yun_completed_decision_ingestion_summary_v1.json",
        "covapie_yun_completed_decision_ingestion_manifest_v1.json",
    )
    if tuple(artifacts) != expected:
        _fail("PUBLISHED_YUN_V2_PREDECESSOR_PROJECTION_INVALID")
    return artifacts


def _validate_v1_precedent_payloads(
    payloads: Mapping[str, bytes],
    ozj_artifacts: Mapping[str, bytes],
    yun_artifacts: Mapping[str, bytes],
) -> None:
    if (
        payloads["OZJ_INGESTION_MATRIX_PRECEDENT"]
        != ozj_artifacts["covapie_ozj_event_task_label_availability_v1.csv"]
        or payloads["YUN_DIRECT_INCLUDE_MATRIX_PRECEDENT"]
        != yun_artifacts["covapie_yun_event_task_label_availability_v1.csv"]
    ):
        _fail("HISTORICAL_V1_PRECEDENT_MATRIX_NOT_PRESERVED")


def load_frozen_f24_authority_v2(
    *,
    repo_root: Path,
    formal_decision_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]:
    """Load frozen F24 authority through B1 without exact-mode acceptance."""

    repo_root = repo_root.resolve()
    overrides = _normalize_overrides(repository_path_overrides)
    if set(overrides) - _allowed_override_paths():
        _fail("REPOSITORY_PATH_OVERRIDE_UNEXPECTED")
    formal_relative = f24_v1.FORMAL_BINDINGS[0][0]
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
    for relative, byte_count, sha256, label in _FROZEN_F24_V1_CODE_BINDINGS:
        _verify_source(
            path=repo_root / relative,
            byte_count=byte_count,
            sha256=sha256,
            label=label,
            expected_executable=False,
        )

    ozj_artifacts = _exercise_published_ozj_v2_predecessor(repo_root)
    yun_artifacts = _exercise_published_yun_v2_predecessor(repo_root)

    formal_payloads: dict[Path, bytes] = {}
    for binding in f24_v1.FORMAL_BINDINGS:
        relative, namespace, count, sha256, role, legacy_mode = binding
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
        if legacy_mode is None:
            _fail("FORMAL_LEGACY_MODE_PROVENANCE_MISSING")
        formal_payloads[relative] = _verify_source(
            path=path,
            byte_count=count,
            sha256=sha256,
            label=role,
            expected_executable=_expected_executable_from_legacy_mode(legacy_mode),
        )

    preparation_payloads: dict[Path, bytes] = {}
    for binding in f24_v1.PREPARATION_BINDINGS:
        relative, namespace, count, sha256, role, legacy_mode = binding
        if legacy_mode is None:
            _fail("PREPARATION_LEGACY_MODE_PROVENANCE_MISSING")
        preparation_payloads[relative] = _verify_source(
            path=_resolved_path(
                repo_root=repo_root,
                relative=relative,
                namespace=namespace,
                overrides=overrides,
            ),
            byte_count=count,
            sha256=sha256,
            label=role,
            expected_executable=_expected_executable_from_legacy_mode(legacy_mode),
        )

    semantic_payloads: dict[str, bytes] = {}
    for relative, namespace, count, sha256, role, _mode in (
        f24_v1.SEMANTIC_OWNER_BINDINGS
    ):
        semantic_payloads[role] = _verify_source(
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
    _validate_semantic_owner_payloads(semantic_payloads)

    precedent_payloads: dict[str, bytes] = {}
    for relative, namespace, count, sha256, role, _mode in f24_v1.PRECEDENT_BINDINGS:
        precedent_payloads[role] = _verify_source(
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
    _validate_v1_precedent_payloads(
        precedent_payloads, ozj_artifacts, yun_artifacts
    )

    census_payloads: dict[Path, bytes] = {}
    for relative, namespace, count, sha256, role, _mode in f24_v1.CENSUS_BINDINGS:
        census_payloads[relative] = _verify_source(
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

    try:
        formal = json.loads(formal_payloads[formal_relative])
    except json.JSONDecodeError as error:
        raise F24SourceBindingV2Error(
            f"{_ERROR_PREFIX}:FORMAL_DECISION_JSON_INVALID"
        ) from error
    try:
        preparation = f24_v1._load_preparation(preparation_payloads)
        _validate_runtime_module_source(repo_root)
        runtime_result = f24_v1._validate_formal_decision_v1(formal, preparation)
        _validate_imported_runtime_module_source(repo_root)
        census_boundary = f24_v1._current_census_boundary(
            repo_root, census_payloads
        )
    except f24_v1.F24IngestionSafetyError as error:
        raise F24SourceBindingV2Error(
            f"{_ERROR_PREFIX}:F24_V1_SCIENTIFIC_SEMANTICS_INVALID:{error}"
        ) from error

    mode_bound = (*f24_v1.FORMAL_BINDINGS, *f24_v1.PREPARATION_BINDINGS)
    historical_modes = [binding[5] for binding in mode_bound]
    expected_executable = [
        _expected_executable_from_legacy_mode(str(mode))
        for mode in historical_modes
    ]
    if historical_modes != ["0664"] * 8 or expected_executable != [False] * 8:
        _fail("F24_MODE_BOUND_SOURCE_INVENTORY_INVALID")

    return {
        "formal_decision_binding": _binding_record(f24_v1.FORMAL_BINDINGS[0]),
        "formal_validator_binding": _binding_record(f24_v1.FORMAL_BINDINGS[1]),
        "preparation_exact6_bindings": _binding_records(
            f24_v1.PREPARATION_BINDINGS
        ),
        "immutable_semantic_owner_bindings": _binding_records(
            f24_v1.SEMANTIC_OWNER_BINDINGS
        ),
        "precedent_bindings": _binding_records(f24_v1.PRECEDENT_BINDINGS),
        "current_published_census_bindings": _binding_records(
            f24_v1.CENSUS_BINDINGS
        ),
        "formal_validator_result": dict(_FORMAL_VALIDATOR_REPORT),
        "published_runtime_result": runtime_result,
        "current_published_census_boundary": census_boundary,
        "formal": formal,
        "preparation": preparation,
        "dual_published_v2_predecessors": {
            "published_OZJ_V2_successor_bound": True,
            "OZJ_V2_sha256": OZJ_V2_SHA256,
            "OZJ_V2_published_commit": OZJ_V2_PUBLISHED_COMMIT,
            "OZJ_V2_projection_actually_called": True,
            "OZJ_V1_ingestion_projection_preserved": True,
            "published_YUN_V2_successor_bound": True,
            "YUN_V2_sha256": YUN_V2_SHA256,
            "YUN_V2_published_commit": YUN_V2_PUBLISHED_COMMIT,
            "YUN_V2_projection_actually_called": True,
            "YUN_V1_DIRECT_INCLUDE_projection_preserved": True,
        },
        "source_binding_v2": {
            "combined_helper": "verify_bound_source_v2",
            "legacy_mode_metadata_classification": [
                "LEGACY_PROVENANCE_METADATA_PRESERVED",
                "SECURITY_EXECUTABLE_CLASS_INPUT",
            ],
            "historical_mode_bound_source_count": 8,
            "historical_modes": historical_modes,
            "expected_executable_classes": expected_executable,
            "formal_validator_expected_executable": False,
            "review_package_validator_expected_executable": False,
            "exact_posix_numeric_mode_semantic_acceptance": False,
        },
    }


def verify_published_f24_v1_projection_v2(
    *,
    repo_root: Path,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, bytes]:
    """Prove source-derived F24 science equals the published V1 Exact4."""

    repo_root = repo_root.resolve()
    overrides = _normalize_overrides(repository_path_overrides)
    bound = load_frozen_f24_authority_v2(
        repo_root=repo_root,
        repository_path_overrides=overrides,
    )
    artifacts: dict[str, bytes] = {}
    for relative, byte_count, sha256, label in _PUBLISHED_F24_V1_OUTPUT_BINDINGS:
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

    snapshot = f24_v1._snapshot(bound)
    source_derived = {
        f24_v1.SNAPSHOT: f24_v1._json_bytes(snapshot),
        f24_v1.MATRIX: f24_v1._csv_bytes(
            f24_v1.MATRIX_HEADER, f24_v1._matrix_rows(snapshot)
        ),
        f24_v1.SUMMARY: f24_v1._json_bytes(f24_v1._summary()),
    }
    if any(artifacts[name] != payload for name, payload in source_derived.items()):
        _fail("PUBLISHED_V1_SCIENTIFIC_PROJECTION_MISMATCH")
    try:
        manifest = json.loads(artifacts[f24_v1.MANIFEST])
    except json.JSONDecodeError as error:
        raise F24SourceBindingV2Error(
            f"{_ERROR_PREFIX}:PUBLISHED_V1_MANIFEST_JSON_INVALID"
        ) from error
    candidate_bindings = [
        {
            "path": relative.as_posix(),
            "path_namespace": "repository_relative",
            "byte_count": byte_count,
            "sha256": sha256,
            "sha256_scope": "file_bytes",
            "source_role": role,
        }
        for (relative, byte_count, sha256, _label), role in zip(
            _FROZEN_F24_V1_CODE_BINDINGS,
            ("production_owner", "fail_closed_checker", "targeted_test_contract"),
            strict=True,
        )
    ]
    expected_manifest = f24_v1._manifest(
        bound,
        candidate_bindings,
        artifacts[f24_v1.SNAPSHOT],
        artifacts[f24_v1.MATRIX],
        artifacts[f24_v1.SUMMARY],
    )
    if (
        manifest != expected_manifest
        or manifest.get("formal_decision_binding")
        != bound["formal_decision_binding"]
        or manifest.get("formal_validator_binding")
        != bound["formal_validator_binding"]
        or manifest.get("preparation_exact6_bindings")
        != bound["preparation_exact6_bindings"]
        or manifest.get("immutable_semantic_owner_bindings")
        != bound["immutable_semantic_owner_bindings"]
        or manifest.get("precedent_bindings") != bound["precedent_bindings"]
        or manifest.get("current_published_census_bindings")
        != bound["current_published_census_bindings"]
        or manifest.get("canonical_task_contract")
        != f24_v1._canonical_task_contract()
        or manifest.get("authority_boundary") != f24_v1._authority_boundary()
        or manifest.get("chemical_warhead_vs_role_region", {}).get(
            "sets_are_intentionally_distinct"
        )
        is not True
        or manifest.get("ready_for_training") is not False
    ):
        _fail("PUBLISHED_V1_MANIFEST_SEMANTICS_INVALID")
    return artifacts
