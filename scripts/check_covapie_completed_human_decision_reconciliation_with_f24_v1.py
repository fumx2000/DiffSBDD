"""Repository-state-neutral checker for F24 reconciliation successor V1."""

from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
import csv
from dataclasses import fields, replace
import hashlib
import io
import json
from pathlib import Path
import stat
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_v1 as generic,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_f24_v1 as subject,
)
from covalent_ext import (  # noqa: E402
    covapie_f24_completed_decision_ingestion_and_task_label_availability_v1
    as f24_ingestion_owner,
)


EXACT4_PATHS = (
    "src/covalent_ext/"
    "covapie_completed_human_decision_reconciliation_with_f24_v1.py",
    "scripts/"
    "check_covapie_completed_human_decision_reconciliation_with_f24_v1.py",
    "tests/"
    "test_covapie_completed_human_decision_reconciliation_with_f24_v1.py",
    "docs/covapie_completed_human_decision_reconciliation_with_f24_v1_guide.md",
)
CURRENT_CENSUS_ROOT = (
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_ozj_v1/"
)
FROZEN_REPOSITORY_FILES = (
    (
        "GENERIC_RECONCILIATION_OWNER",
        "src/covalent_ext/covapie_completed_human_decision_reconciliation_v1.py",
        35925,
        "2fcdf85f4753cedf6fe803ae1640fbf65484cdad2bc67732b5d9fdc24b8c3548",
    ),
    (
        "ONL_RECONCILIATION_SUCCESSOR",
        "src/covalent_ext/"
        "covapie_completed_human_decision_reconciliation_with_onl_v1.py",
        13046,
        "f2c94ac8b4fe8f3706d0de288e2d5bb24ef211cf56d39e8362b43bdb17a2f475",
    ),
    (
        "OZJ_RECONCILIATION_PREDECESSOR",
        "src/covalent_ext/"
        "covapie_completed_human_decision_reconciliation_with_ozj_v1.py",
        16102,
        "d021e64fa6af1da41246d0618e3a38f8d079c0100e74d7ff4aec80f395d843f0",
    ),
    (
        "OZJ_RECONCILIATION_CHECKER",
        "scripts/"
        "check_covapie_completed_human_decision_reconciliation_with_ozj_v1.py",
        35422,
        "0d12f444913e31b3ccbc6156f701e0b8b52ac2847892d4c51bd7386c077c1dad",
    ),
    (
        "OZJ_RECONCILIATION_TESTS",
        "tests/test_covapie_completed_human_decision_reconciliation_with_ozj_v1.py",
        34798,
        "e6ab679503834686b5abae7ffe232a91470d4740ad7c951e09ba7a655505a52e",
    ),
    (
        "OZJ_RECONCILIATION_GUIDE",
        "docs/covapie_completed_human_decision_reconciliation_with_ozj_v1_guide.md",
        6509,
        "87bba8c1ea108bc1313f917a51b57430b7ac8c82d5d8aad4c777c29be2d208cc",
    ),
    (
        "F24_INGESTION_OWNER",
        "src/covalent_ext/"
        "covapie_f24_completed_decision_ingestion_and_task_label_availability_v1.py",
        77160,
        "c67c88f83e535fd4319425459b97dcfc22f90a3b617b5ddbf1e8f315e2de0525",
    ),
    (
        "F24_PUBLISHED_MATRIX_CROSS_CHECK_ONLY",
        "data/derived/covalent_small/"
        "covapie_f24_completed_decision_ingestion_and_task_label_availability_v1/"
        "covapie_f24_event_task_label_availability_v1.csv",
        7641,
        "516c3ea3ac291c5039e1def72a891b54fd42d5aa45388f27b436a655467cd28c",
    ),
    (
        "HISTORICAL_RECONCILIATION",
        "data/derived/covalent_small/"
        "covapie_cumulative1000_high_yield_human_review_authority_calibration_v1/"
        "covapie_cumulative1000_current_review_status_reconciliation_v1.csv",
        99335,
        "4eb608e2d97b60230ae1e0ca4e4be6a7fe8b3dc45af3467cbc98f685c385862f",
    ),
    (
        "CURRENT_GLOBAL_CENSUS_WITH_OZJ_OWNER",
        "src/covalent_ext/"
        "covapie_cumulative1000_current_global_readiness_census_with_ozj_v1.py",
        63980,
        "140c5668b9662829eb359d09504348baf99533ce78cec8307f057a93bf130d0a",
    ),
    (
        "CURRENT_GLOBAL_CENSUS_WITH_OZJ_CSV",
        CURRENT_CENSUS_ROOT
        + "covapie_cumulative1000_current_global_readiness_census_with_ozj_v1.csv",
        525890,
        "1d73fe9702988244006063ab522b3e8222837879c6f00d8deac032a54db2f9b6",
    ),
    (
        "CURRENT_GLOBAL_CENSUS_WITH_OZJ_SUMMARY",
        CURRENT_CENSUS_ROOT
        + "covapie_cumulative1000_current_global_readiness_summary_with_ozj_v1.json",
        15982,
        "d6b249101eaec5e50d6d9585a05c9de0485bcea24d4d4143444429ab97408f56",
    ),
    (
        "CURRENT_GLOBAL_CENSUS_WITH_OZJ_MANIFEST",
        CURRENT_CENSUS_ROOT
        + "covapie_cumulative1000_current_global_readiness_manifest_with_ozj_v1.json",
        41425,
        "a56a5c7351b66b472bc644792b4a092e110ba01ab20ae28546c3be5caf80dd4d",
    ),
)
F24_FORMAL_RELATIVE = (
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "F24_COVAPIE_BULK_REVIEW_UNIT_2557BFE1E3B5C4C5/"
    "formal-human-decision-v1/f24_formal_human_decision_v1.json"
)
F24_FORMAL_BYTE_COUNT = 26652
F24_FORMAL_SHA256 = (
    "ec2bc7c96e6272e99202a8cdbdef330ea4c1189f5fd47abe43f55de2a2db5f22"
)
EXPECTED_PUBLIC_API = (
    "CompletedDecisionReconciliationWithF24Error",
    "project_f24_completed_decision_v1",
    "load_real_completed_decision_sources_with_f24_v1",
    "reconcile_real_completed_human_decisions_with_f24_v1",
)
EXPECTED_GENERIC_FACT_FIELDS = (
    "canonical_event_id",
    "review_unit_id",
    "human_review_completed",
    "legacy_completed_review_status",
    "task_relevance_disposition",
    "chemistry_disposition",
    "training_disposition",
    "human_training_excluded",
    "source_decision_schema",
    "source_decision_sha256",
    "source_binding_path",
)
EXPECTED_PREDECESSOR_SOURCE_FACT_COUNTS = (8, 16, 8, 9, 8, 8, 8, 7, 6, 5, 4)
EXPECTED_SOURCE_FACT_COUNTS = (*EXPECTED_PREDECESSOR_SOURCE_FACT_COUNTS, 4)
EXPECTED_REVIEW_SUMMARY = {
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
}
EXPECTED_CURRENT_CENSUS = {
    "positive": 104,
    "relevant": 105,
    "training_include": 40,
    "training_exclude": 64,
    "future_candidates": 23,
    "sample_pair_authority": 104,
    "sample_role_authority": 104,
}
EXPECTED_FUTURE_CENSUS = {
    "positive": 108,
    "relevant": 109,
    "training_include": 44,
    "training_exclude": 64,
    "future_candidates": 27,
    "sample_pair_authority": 108,
    "sample_role_authority": 108,
    "strict_profile": 48,
    "direct_profile": 60,
    "warhead_only_A": 108,
    "linker_plus_warhead_B": 48,
    "scaffold_plus_warhead_B2": 48,
    "scaffold_only_B3": 108,
    "scaffold_plus_linker_plus_warhead_C": 108,
}
FORBIDDEN_FACT_ATTRIBUTES = (
    "chemical_warhead_atom_ids",
    "warhead_role_atom_ids",
    "role_profile",
    "role_boundary",
    "selected_candidate",
    "canonical_task_applicability",
    "minimal_seed",
    "candidate_for_future_training_admission",
    "future_training_admission_status",
    "training_admitted",
    "reaction_family",
    "warhead_rule",
    "warhead_type",
)
FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip",
    ".tgz", ".npz", ".pyc", ".tmp", ".part", ".log",
)
MAX_FILE_BYTES = 1024 * 1024
_CANDIDATE_UNTRACKED = "CANDIDATE_UNTRACKED"
_TRACKED_CLEAN = "TRACKED_CLEAN"
_SUPPORTED_REPOSITORY_PROFILES = (_CANDIDATE_UNTRACKED, _TRACKED_CLEAN)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_regular_file(path: Path, label: str) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise ValueError("NOT_REGULAR_FILE:" + label)
    try:
        return path.read_bytes()
    except OSError as error:
        raise ValueError("READ_FAILED:" + label) from error


def _verify_file(
    path: Path,
    *,
    label: str,
    expected_byte_count: int,
    expected_sha256: str,
) -> dict[str, object]:
    payload = _read_regular_file(path, label)
    if len(payload) != expected_byte_count:
        raise ValueError("FROZEN_BYTE_COUNT_MISMATCH:" + label)
    digest = _sha256(payload)
    if digest != expected_sha256:
        raise ValueError("FROZEN_SHA256_MISMATCH:" + label)
    return {
        "artifact_role": label,
        "path": path.as_posix(),
        "byte_count": len(payload),
        "sha256": digest,
    }


def _validate_text_payload(payload: bytes, label: str) -> None:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError("EXACT4_NOT_UTF8:" + label) from error
    if payload.startswith(b"\xef\xbb\xbf"):
        raise ValueError("EXACT4_UTF8_BOM_FORBIDDEN:" + label)
    if "\x00" in text or "\r" in text:
        raise ValueError("EXACT4_TEXT_INVARIANT_INVALID:" + label)
    if not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
        raise ValueError("EXACT4_TERMINAL_LF_INVALID:" + label)
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        raise ValueError("EXACT4_TRAILING_WHITESPACE:" + label)


def _git_nul_items(
    repo_root: Path, command: tuple[str, ...], label: str
) -> tuple[str, ...]:
    try:
        completed = subprocess.run(
            command,
            cwd=repo_root,
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        raise ValueError("GIT_OBSERVATION_FAILED:" + label) from error
    try:
        return tuple(
            sorted(
                item.decode("utf-8")
                for item in completed.stdout.split(b"\0")
                if item
            )
        )
    except UnicodeDecodeError as error:
        raise ValueError("GIT_OBSERVATION_NOT_UTF8:" + label) from error


def _classify_repository_profile(
    *,
    expected_paths: tuple[str, ...],
    tracked_paths: set[str],
    status_lines: tuple[str, ...],
    working_tree_diff_paths: tuple[str, ...],
    cached_diff_paths: tuple[str, ...],
) -> str:
    """Accept only an exact untracked candidate or an exact tracked-clean tree."""

    if (
        type(expected_paths) is not tuple
        or not expected_paths
        or any(type(path) is not str or not path for path in expected_paths)
        or len(set(expected_paths)) != len(expected_paths)
        or type(tracked_paths) is not set
        or any(type(path) is not str for path in tracked_paths)
        or type(status_lines) is not tuple
        or any(type(line) is not str for line in status_lines)
        or type(working_tree_diff_paths) is not tuple
        or any(type(path) is not str for path in working_tree_diff_paths)
        or type(cached_diff_paths) is not tuple
        or any(type(path) is not str for path in cached_diff_paths)
    ):
        raise ValueError("REPOSITORY_PROFILE_OBSERVATION_TYPE_INVALID")

    expected = set(expected_paths)
    tracked_exact4 = expected & tracked_paths
    status = tuple(sorted(status_lines))
    working = tuple(sorted(working_tree_diff_paths))
    cached = tuple(sorted(cached_diff_paths))
    expected_untracked_status = tuple(
        sorted("?? " + path for path in expected_paths)
    )
    if (
        not tracked_exact4
        and status == expected_untracked_status
        and not working
        and not cached
    ):
        return _CANDIDATE_UNTRACKED
    if (
        tracked_exact4 == expected
        and not status
        and not working
        and not cached
    ):
        return _TRACKED_CLEAN
    raise ValueError(
        "REPOSITORY_PROFILE_NOT_EXACT_CANDIDATE_UNTRACKED_OR_TRACKED_CLEAN"
    )


def _repository_observations(repo_root: Path) -> dict[str, object]:
    tracked = _git_nul_items(
        repo_root,
        ("git", "ls-files", "-z"),
        "TRACKED_PATHS",
    )
    status = _git_nul_items(
        repo_root,
        ("git", "status", "--short", "--untracked-files=all", "-z"),
        "STATUS_SHORT_ALL",
    )
    working = _git_nul_items(
        repo_root,
        ("git", "diff", "--name-only", "-z"),
        "WORKING_TREE_DIFF_PATHS",
    )
    cached = _git_nul_items(
        repo_root,
        ("git", "diff", "--cached", "--name-only", "-z"),
        "CACHED_DIFF_PATHS",
    )
    return {
        "tracked_paths": set(tracked),
        "status_lines": status,
        "working_tree_diff_paths": working,
        "cached_diff_paths": cached,
    }


def _status_entry_path(status_line: str) -> str:
    return status_line[3:] if len(status_line) >= 4 else status_line


def _reject_dirty_forbidden_or_transient_paths(
    status_lines: tuple[str, ...],
    working_tree_diff_paths: tuple[str, ...],
    cached_diff_paths: tuple[str, ...],
) -> None:
    observed = {
        *(_status_entry_path(line) for line in status_lines),
        *working_tree_diff_paths,
        *cached_diff_paths,
    }
    forbidden = sorted(
        path
        for path in observed
        if "__pycache__" in path.split("/")
        or path.endswith(FORBIDDEN_SUFFIXES)
    )
    if forbidden:
        raise ValueError("FORBIDDEN_OR_TRANSIENT_REPOSITORY_PATH:" + forbidden[0])


def _ignored_transient_paths(repo_root: Path) -> tuple[str, ...]:
    ignored_status = _git_nul_items(
        repo_root,
        (
            "git", "status", "--short", "--untracked-files=all",
            "--ignored=matching", "-z",
        ),
        "IGNORED_STATUS",
    )
    return tuple(
        sorted(
            path
            for line in ignored_status
            if line.startswith("!! ")
            for path in (_status_entry_path(line),)
            if "__pycache__" in path.rstrip("/").split("/")
            or path.endswith((".pyc", ".tmp", ".part", ".log"))
        )
    )


def verify_candidate_exact4_v1(repo_root: Path) -> dict[str, object]:
    """Verify an exact untracked candidate or an exact tracked-clean tree."""

    root = repo_root.resolve()
    artifacts: list[dict[str, object]] = []
    for relative in EXACT4_PATHS:
        path = root / relative
        payload = _read_regular_file(path, relative)
        _validate_text_payload(payload, relative)
        if len(payload) >= MAX_FILE_BYTES:
            raise ValueError("EXACT4_FILE_TOO_LARGE:" + relative)
        mode = stat.S_IMODE(path.stat().st_mode)
        artifacts.append(
            {
                "path": relative,
                "byte_count": len(payload),
                "line_count": len(payload.decode("utf-8").splitlines()),
                "sha256": _sha256(payload),
                "mode": f"{mode:04o}",
            }
        )
    observations = _repository_observations(root)
    tracked_paths = observations["tracked_paths"]
    status_lines = observations["status_lines"]
    working_tree_diff_paths = observations["working_tree_diff_paths"]
    cached_diff_paths = observations["cached_diff_paths"]
    assert type(tracked_paths) is set
    assert type(status_lines) is tuple
    assert type(working_tree_diff_paths) is tuple
    assert type(cached_diff_paths) is tuple
    _reject_dirty_forbidden_or_transient_paths(
        status_lines,
        working_tree_diff_paths,
        cached_diff_paths,
    )
    ignored_transients = _ignored_transient_paths(root)
    if ignored_transients:
        raise ValueError("IGNORED_TRANSIENT_REPOSITORY_PATH:" + ignored_transients[0])
    lifecycle = _classify_repository_profile(
        expected_paths=EXACT4_PATHS,
        tracked_paths=tracked_paths,
        status_lines=status_lines,
        working_tree_diff_paths=working_tree_diff_paths,
        cached_diff_paths=cached_diff_paths,
    )
    return {
        "count": len(artifacts),
        "artifacts": tuple(artifacts),
        "lifecycle": lifecycle,
        "supported_successful_profiles": _SUPPORTED_REPOSITORY_PROFILES,
        "third_successful_profile": False,
        "tracked_exact4_count": len(set(EXACT4_PATHS) & tracked_paths),
        "git_status_entry_count": len(status_lines),
        "working_tree_diff_count": len(working_tree_diff_paths),
        "cached_diff_count": len(cached_diff_paths),
    }


def _verify_frozen_inputs(repo_root: Path) -> dict[str, object]:
    root = repo_root.resolve()
    artifacts = [
        _verify_file(
            root / relative,
            label=label,
            expected_byte_count=byte_count,
            expected_sha256=digest,
        )
        for label, relative, byte_count, digest in FROZEN_REPOSITORY_FILES
    ]
    artifacts.append(
        _verify_file(
            root.parent / F24_FORMAL_RELATIVE,
            label="F24_FORMAL_HUMAN_DECISION",
            expected_byte_count=F24_FORMAL_BYTE_COUNT,
            expected_sha256=F24_FORMAL_SHA256,
        )
    )
    return {"count": len(artifacts), "artifacts": tuple(artifacts)}


def _verify_thin_successor_architecture(repo_root: Path) -> dict[str, object]:
    tree = ast.parse(_read_regular_file(repo_root / EXACT4_PATHS[0], "F24_SUCCESSOR"))
    if subject.__all__ != EXPECTED_PUBLIC_API:
        raise ValueError("PUBLIC_API_NOT_MINIMAL_EXACT4")
    if subject.F24_TRANSITION_ADAPTER_CREATED is not False:
        raise ValueError("F24_TRANSITION_ADAPTER_FLAG_INVALID")
    function_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    if any(
        name.lower().startswith("_adapt_f24")
        or ("f24" in name.lower() and "transition" in name.lower())
        for name in function_names
    ):
        raise ValueError("F24_TRANSITION_HELPER_CREATED")
    class_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
    }
    if class_names & {
        "SourceBinding",
        "NormalizedCompletedDecisionFact",
        "NormalizedDecisionSource",
        "ReconciliationResult",
    }:
        raise ValueError("GENERIC_DATACLASS_DUPLICATED")
    if function_names & {"_validate_source_binding", "_validate_fact", "_review_summary"}:
        raise ValueError("GENERIC_RECONCILIATION_IMPLEMENTATION_DUPLICATED")
    called = [
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Attribute, ast.Name))
    ]
    expected_once = {
        "predecessor_source_loader": "load_real_completed_decision_sources_with_ozj_v1",
        "f24_projector": "project_f24_completed_decision_v1",
        "f24_ingestion_loader": "load_frozen_formal_decision_v1",
        "onl_adapter": "_adapt_onl_in_progress_completion_for_generic_reconciliation_v1",
        "generic_reconciler": "reconcile_completed_human_decisions_v1",
    }
    if any(called.count(name) != 1 for name in expected_once.values()):
        raise ValueError("THIN_SUCCESSOR_DELEGATE_AST_COUNTS_INVALID")
    if called.count("reconcile_real_completed_human_decisions_with_ozj_v1") != 0:
        raise ValueError("OZJ_RESULT_RECONCILIATION_FORBIDDEN")
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    if imported & {"json", "csv", "dataset", "lightning_modules", "equivariant_diffusion"}:
        raise ValueError("PARSING_TRAINING_OR_MODEL_IMPORT_FORBIDDEN")
    source_text = _read_regular_file(repo_root / EXACT4_PATHS[0], "F24_SUCCESSOR").decode()
    if any(
        token in source_text
        for token in (
            "covapie_f24_event_task_label_availability_v1.csv",
            "completed_human_decision_snapshot",
            "global_readiness_summary",
            "global_readiness_manifest",
        )
    ):
        raise ValueError("SECOND_RECONCILIATION_AUTHORITY_PATH_CREATED")
    return {
        "public_api": subject.__all__,
        "f24_transition_adapter_created": False,
        "direct_formal_json_parse_count": 0,
        "manual_overlay_count": 0,
        **{
            key + "_ast_call_count": called.count(value)
            for key, value in expected_once.items()
        },
        "ozj_reconciler_ast_call_count": 0,
    }


def _verify_generic_fact_thinness(
    source: generic.NormalizedDecisionSource,
) -> dict[str, object]:
    observed = tuple(field.name for field in fields(generic.NormalizedCompletedDecisionFact))
    if observed != EXPECTED_GENERIC_FACT_FIELDS:
        raise ValueError("GENERIC_FACT_FIELD_CONTRACT_DRIFT")
    if len(source.facts) != 4 or any(
        type(fact) is not generic.NormalizedCompletedDecisionFact
        or any(hasattr(fact, name) for name in FORBIDDEN_FACT_ATTRIBUTES)
        for fact in source.facts
    ):
        raise ValueError("F24_GENERIC_FACT_NOT_THIN")
    try:
        generic.NormalizedCompletedDecisionFact(
            **{
                field: getattr(source.facts[0], field)
                for field in EXPECTED_GENERIC_FACT_FIELDS
            },
            candidate_for_future_training_admission=True,
        )
    except TypeError:
        pass
    else:
        raise ValueError("GENERIC_FACT_ACCEPTED_FUTURE_CANDIDATE_FIELD")
    return {
        "field_names": observed,
        "chemical_warhead_projected": False,
        "warhead_role_projected": False,
        "future_candidate_projected": False,
        "training_admission_field_present": False,
    }


def _run_production_pipeline_counted(
    repo_root: Path,
) -> tuple[
    generic.ReconciliationResult,
    dict[str, int],
    tuple[dict[str, str], ...],
    tuple[dict[str, str], ...],
]:
    original_predecessor = (
        subject.ozj_successor.load_real_completed_decision_sources_with_ozj_v1
    )
    original_projector = subject.project_f24_completed_decision_v1
    original_ingestion = subject.f24_ingestion_owner.load_frozen_formal_decision_v1
    original_onl = (
        subject.onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1
    )
    original_generic = subject.generic.reconcile_completed_human_decisions_v1
    calls: Counter[str] = Counter()
    captured_original: tuple[dict[str, str], ...] = ()
    captured_adapted: tuple[dict[str, str], ...] = ()

    def counted_predecessor(root: Path) -> tuple[generic.NormalizedDecisionSource, ...]:
        calls["predecessor_source_loader"] += 1
        return original_predecessor(root)

    def counted_projector(*, repo_root: Path) -> generic.NormalizedDecisionSource:
        calls["f24_projector"] += 1
        return original_projector(repo_root=repo_root)

    def counted_ingestion(root: Path) -> dict[str, object]:
        calls["f24_ingestion_loader"] += 1
        return original_ingestion(root)

    def counted_onl(rows: object) -> tuple[dict[str, str], ...]:
        nonlocal captured_original, captured_adapted
        calls["onl_adapter"] += 1
        captured_original = tuple(dict(row) for row in rows)  # type: ignore[arg-type]
        captured_adapted = original_onl(rows)  # type: ignore[arg-type]
        return captured_adapted

    def counted_generic(rows: object, sources: object) -> generic.ReconciliationResult:
        calls["generic_reconciler"] += 1
        return original_generic(rows, sources)  # type: ignore[arg-type]

    subject.ozj_successor.load_real_completed_decision_sources_with_ozj_v1 = counted_predecessor
    subject.project_f24_completed_decision_v1 = counted_projector
    subject.f24_ingestion_owner.load_frozen_formal_decision_v1 = counted_ingestion
    subject.onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1 = counted_onl
    subject.generic.reconcile_completed_human_decisions_v1 = counted_generic
    try:
        result = subject.reconcile_real_completed_human_decisions_with_f24_v1(repo_root)
    finally:
        subject.ozj_successor.load_real_completed_decision_sources_with_ozj_v1 = original_predecessor
        subject.project_f24_completed_decision_v1 = original_projector
        subject.f24_ingestion_owner.load_frozen_formal_decision_v1 = original_ingestion
        subject.onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1 = original_onl
        subject.generic.reconcile_completed_human_decisions_v1 = original_generic
    expected = Counter(
        {
            "predecessor_source_loader": 1,
            "f24_projector": 1,
            "f24_ingestion_loader": 1,
            "onl_adapter": 1,
            "generic_reconciler": 1,
        }
    )
    if calls != expected:
        raise ValueError("PRODUCTION_DELEGATE_RUNTIME_CALL_COUNTS_INVALID")
    return result, dict(calls), captured_original, captured_adapted


def _published_census_state(repo_root: Path) -> dict[str, object]:
    csv_path = repo_root / FROZEN_REPOSITORY_FILES[10][1]
    summary_path = repo_root / FROZEN_REPOSITORY_FILES[11][1]
    try:
        rows = tuple(
            csv.DictReader(
                io.StringIO(
                    _read_regular_file(csv_path, "CURRENT_CENSUS").decode("utf-8"),
                    newline="",
                )
            )
        )
        summary = json.loads(_read_regular_file(summary_path, "CURRENT_CENSUS_SUMMARY"))
    except (UnicodeDecodeError, csv.Error, json.JSONDecodeError) as error:
        raise ValueError("PUBLISHED_CURRENT_CENSUS_PARSE_FAILED") from error
    if len(rows) != 1000:
        raise ValueError("PUBLISHED_CURRENT_CENSUS_NOT_EXACT1000")
    f24_ids = set(subject._F24_EVENT_IDS)
    f24_rows = [row for row in rows if row.get("canonical_event_id") in f24_ids]
    if len(f24_rows) != 4 or any(
        row.get("review_unit_id") != subject._F24_REVIEW_UNIT_ID
        or row.get("current_global_status") != generic.CURRENTLY_UNREVIEWED
        or row.get("human_review_completed") != "false"
        or row.get("chemistry_disposition") != "UNRESOLVED"
        or row.get("task_relevance_disposition") != "UNRESOLVED"
        or row.get("training_use_disposition") != "UNRESOLVED"
        or row.get("formal_training_admitted") != "false"
        for row in f24_rows
    ):
        raise ValueError("PUBLISHED_CURRENT_CENSUS_F24_STATE_INVALID")
    counts = {
        "positive": sum(
            row.get("chemistry_disposition") == generic.CHEMISTRY_POSITIVE
            for row in rows
        ),
        "relevant": sum(
            row.get("task_relevance_disposition") == generic.TASK_RELEVANT
            for row in rows
        ),
        "training_include": sum(
            row.get("training_use_disposition") == generic.TRAINING_INCLUDE
            for row in rows
        ),
        "training_exclude": sum(
            row.get("training_use_disposition") == generic.TRAINING_EXCLUDE
            for row in rows
        ),
        "future_candidates": sum(
            row.get("future_training_admission_candidate") == "true"
            for row in rows
        ),
        "sample_pair_authority": summary["reactive_pair"]["sample_level_authoritative_pair_count"],
        "sample_role_authority": summary["role"]["role_partition_sample_authoritative_count"],
    }
    if counts != EXPECTED_CURRENT_CENSUS:
        raise ValueError("PUBLISHED_CURRENT_CENSUS_COUNTS_INVALID")
    return {"counts": counts, "summary": summary, "rows": rows}


def _verify_future_census_informational(
    source: generic.NormalizedDecisionSource,
    bound: dict[str, object],
    published: dict[str, object],
) -> dict[str, int]:
    summary = published["summary"]
    formal = bound.get("formal")
    if type(summary) is not dict or type(formal) is not dict or len(source.facts) != 4:
        raise ValueError("FUTURE_CENSUS_INPUT_INVALID")
    subject._validate_rich_f24_semantics_v1(bound)
    derived_training = f24_ingestion_owner._training_boundary()
    if (
        derived_training.get("candidate_for_future_training_admission") is not True
        or derived_training.get("future_training_candidate_derived_by_ingestion") is not True
        or derived_training.get("future_training_candidate_is_training_admission") is not False
        or derived_training.get("training_admitted") is not False
    ):
        raise ValueError("FUTURE_CENSUS_F24_CANDIDACY_INPUT_INVALID")
    canonical = formal["canonical_Exact5_and_sample_applicability"]
    applicable_semantics = {
        task["semantic_name"]
        for task in canonical["tasks"]
        if task["structurally_applicable_to_F24"] is True
    }
    task_counts = {
        task["semantic_name"]: task["structurally_applicable_authoritative_role_count"]
        for task in summary["canonical_exact5"]["tasks"]
    }
    observed = {
        "positive": summary["chemistry"]["POSITIVE"]["count"] + 4,
        "relevant": summary["task_relevance"]["RELEVANT"]["count"] + 4,
        "training_include": summary["training_use"]["INCLUDE"]["count"] + 4,
        "training_exclude": summary["training_use"][generic.TRAINING_EXCLUDE]["count"],
        "future_candidates": summary["training_stage"]["future_training_admission_candidate_count"] + 4,
        "sample_pair_authority": summary["reactive_pair"]["sample_level_authoritative_pair_count"] + 4,
        "sample_role_authority": summary["role"]["role_partition_sample_authoritative_count"] + 4,
        "strict_profile": summary["role"]["role_profile_counts"]["STRICT_LINKER_PRESENT_V1"],
        "direct_profile": summary["role"]["role_profile_counts"]["DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"] + 4,
        "warhead_only_A": task_counts["warhead_only"] + (4 if "warhead_only" in applicable_semantics else 0),
        "linker_plus_warhead_B": task_counts["linker_plus_warhead"] + (4 if "linker_plus_warhead" in applicable_semantics else 0),
        "scaffold_plus_warhead_B2": task_counts["scaffold_plus_warhead"] + (4 if "scaffold_plus_warhead" in applicable_semantics else 0),
        "scaffold_only_B3": task_counts["scaffold_only"] + (4 if "scaffold_only" in applicable_semantics else 0),
        "scaffold_plus_linker_plus_warhead_C": task_counts["scaffold_plus_linker_plus_warhead"] + (4 if "scaffold_plus_linker_plus_warhead" in applicable_semantics else 0),
    }
    if observed != EXPECTED_FUTURE_CENSUS:
        raise ValueError("FUTURE_CENSUS_INFORMATIONAL_DERIVATION_INVALID")
    return observed


def _derive_next_pending(
    result: generic.ReconciliationResult,
) -> dict[str, object]:
    units: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for row in result.reconciled_rows:
        if row["current_review_status"] == generic.CURRENTLY_UNREVIEWED:
            units[row["raw_review_unit_id"]].append(row)
    if not units:
        raise ValueError("NO_PENDING_REVIEW_UNIT")
    rows = min(
        units.values(),
        key=lambda values: (
            min(int(row["raw_priority_rank"]) for row in values),
            values[0]["raw_review_unit_id"],
        ),
    )
    event_ids = tuple(sorted(row["canonical_event_id"] for row in rows))
    ligand_ids = tuple(sorted({event_id.split(":")[-2] for event_id in event_ids}))
    if (
        len(event_ids) != int(rows[0]["raw_unit_event_count"])
        or rows[0]["raw_review_unit_id"] == subject._F24_REVIEW_UNIT_ID
    ):
        raise ValueError("NEXT_PENDING_DERIVATION_INVALID")
    return {
        "review_unit_id": rows[0]["raw_review_unit_id"],
        "raw_priority_rank": int(rows[0]["raw_priority_rank"]),
        "event_count": len(event_ids),
        "ligand_component_ids": ligand_ids,
        "event_ids": event_ids,
    }


def _expect_subject_failure(callable_: object, token: str) -> None:
    try:
        callable_()  # type: ignore[operator]
    except subject.CompletedDecisionReconciliationWithF24Error as error:
        if token not in str(error):
            raise ValueError("SUBJECT_FAILURE_TOKEN_INVALID:" + str(error)) from error
    else:
        raise ValueError("SUBJECT_FAILURE_NOT_RAISED:" + token)


def _verify_fail_closed_probes(
    bound: dict[str, object],
    historical: tuple[dict[str, str], ...],
    adapted: tuple[dict[str, str], ...],
) -> dict[str, bool]:
    drifted_binding = json.loads(json.dumps(bound))
    drifted_binding["formal_decision_binding"]["sha256"] = "0" * 64
    _expect_subject_failure(
        lambda: subject._project_validated_f24_binding_v1(drifted_binding),
        "F24_FORMAL_DECISION_BINDING_INVALID",
    )
    drifted_role = json.loads(json.dumps(bound))
    drifted_role["formal"]["selected_role_partition"]["role_profile"] = "WRONG"
    _expect_subject_failure(
        lambda: subject._project_validated_f24_binding_v1(drifted_role),
        "F24_REVISED_ROLE_PARTITION_INVALID",
    )
    missing = tuple(
        row for row in historical
        if row["canonical_event_id"] != subject._F24_EVENT_IDS[0]
    )
    _expect_subject_failure(
        lambda: subject._prove_f24_original_unreviewed_prior_v1(missing),
        "F24_HISTORICAL_EVENT_MISSING",
    )
    changed = [dict(row) for row in adapted]
    row = next(
        row for row in changed
        if row["canonical_event_id"] == subject._F24_EVENT_IDS[0]
    )
    row["current_status_authority_sources_json"] = '["unexpected"]'
    _expect_subject_failure(
        lambda: subject._prove_f24_rows_unchanged_after_onl_normalization_v1(
            historical, changed
        ),
        "ONL_ADAPTER_CHANGED_F24_ROW",
    )
    return {
        "formal_binding_drift_rejected": True,
        "rich_role_drift_rejected": True,
        "missing_historical_event_rejected": True,
        "onl_f24_mutation_rejected": True,
    }


def run_check_v1(repo_root: Path) -> dict[str, object]:
    """Run all read-only F24 reconciliation checks and return evidence."""

    root = repo_root.resolve()
    exact4 = verify_candidate_exact4_v1(root)
    frozen = _verify_frozen_inputs(root)
    architecture = _verify_thin_successor_architecture(root)

    source = subject.project_f24_completed_decision_v1(repo_root=root)
    thinness = _verify_generic_fact_thinness(source)
    bound = f24_ingestion_owner.load_frozen_formal_decision_v1(root)
    subject._validate_rich_f24_semantics_v1(bound)

    historical = generic.load_real_historical_reconciliation_v1(root)
    subject._prove_f24_original_unreviewed_prior_v1(historical)
    result, calls, captured_original, captured_adapted = _run_production_pipeline_counted(root)
    subject._prove_f24_rows_unchanged_after_onl_normalization_v1(
        captured_original, captured_adapted
    )

    sources = subject.load_real_completed_decision_sources_with_f24_v1(root)
    event_ids = [fact.canonical_event_id for item in sources for fact in item.facts]
    if (
        len(sources) != 12
        or tuple(len(item.facts) for item in sources) != EXPECTED_SOURCE_FACT_COUNTS
        or len({item.binding.stable_identity for item in sources}) != 12
        or len({item.binding.review_unit_id for item in sources}) != 12
        or len(event_ids) != 91
        or len(set(event_ids)) != 91
    ):
        raise ValueError("EXACT12_SOURCE_COMPOSITION_INVALID")
    if result.review_summary != EXPECTED_REVIEW_SUMMARY:
        raise ValueError("RECONCILIATION_SUMMARY_INVALID")
    dispositions = Counter(fact.training_disposition for fact in result.normalized_facts)
    if dispositions != Counter(
        {generic.TRAINING_INCLUDE: 27, generic.TRAINING_EXCLUDE: 64}
    ):
        raise ValueError("NORMALIZED_TRAINING_DISPOSITIONS_INVALID")
    f24_facts = {
        fact.canonical_event_id: fact
        for fact in result.normalized_facts
        if fact.canonical_event_id in set(subject._F24_EVENT_IDS)
    }
    final_f24 = {
        row["canonical_event_id"]: row
        for row in result.reconciled_rows
        if row["canonical_event_id"] in set(subject._F24_EVENT_IDS)
    }
    expected_authority = json.dumps(
        [source.binding.source_path], separators=(",", ":"), sort_keys=True
    )
    if len(f24_facts) != 4 or any(
        fact.review_unit_id != subject._F24_REVIEW_UNIT_ID
        or fact.human_review_completed is not True
        or fact.legacy_completed_review_status != generic.COMPLETED_HUMAN_POSITIVE
        or fact.task_relevance_disposition != generic.TASK_RELEVANT
        or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
        or fact.training_disposition != generic.TRAINING_INCLUDE
        or fact.human_training_excluded is not False
        for fact in f24_facts.values()
    ):
        raise ValueError("FINAL_F24_NORMALIZED_FACTS_INVALID")
    if len(final_f24) != 4 or any(
        row["raw_review_unit_id"] != subject._F24_REVIEW_UNIT_ID
        or row["current_review_status"] != generic.COMPLETED_HUMAN_POSITIVE
        or row["calibration_eligible"] != "false"
        or row["calibration_exclusion_reason"] != generic.COMPLETED_HUMAN_POSITIVE
        or row["current_status_authority_sources_json"] != expected_authority
        for row in final_f24.values()
    ):
        raise ValueError("FINAL_F24_RECONCILED_ROWS_INVALID")

    normal = generic.reconcile_completed_human_decisions_v1(captured_adapted, sources)
    reversed_result = generic.reconcile_completed_human_decisions_v1(
        captured_adapted, tuple(reversed(sources))
    )
    if normal != reversed_result or normal != result:
        raise ValueError("SOURCE_ORDER_NOT_DETERMINISTIC")
    try:
        generic.reconcile_completed_human_decisions_v1(captured_original, sources)
    except generic.CompletedDecisionReconciliationError as error:
        if "PRIOR_REVIEW_STATUS_NOT_UNREVIEWED" not in str(error):
            raise ValueError("ORIGINAL_ONL_FAILURE_TOKEN_INVALID") from error
    else:
        raise ValueError("ORIGINAL_ONL_PRIOR_NOT_REJECTED")

    published = _published_census_state(root)
    future = _verify_future_census_informational(source, bound, published)
    next_pending = _derive_next_pending(result)
    protections = _verify_fail_closed_probes(bound, captured_original, captured_adapted)

    return {
        "check": "PASS",
        "exact4": exact4,
        "frozen_bindings": frozen,
        "architecture": architecture,
        "delegate_runtime_calls": calls,
        "generic_fact_thinness": thinness,
        "source_fact_counts": EXPECTED_SOURCE_FACT_COUNTS,
        "source_count": 12,
        "review_unit_count": 12,
        "normalized_fact_count": 91,
        "unique_normalized_fact_ids": 91,
        "event_collisions": 0,
        "f24_prior": {
            "event_count": 4,
            "status": generic.CURRENTLY_UNREVIEWED,
            "calibration_eligible": True,
            "calibration_exclusion_reason": "",
            "transition_adapter": "NOT_CREATED",
        },
        "onl_adapter_left_f24_unchanged": True,
        "review_summary": result.review_summary,
        "training_dispositions": dict(dispositions),
        "rich_semantics_boundary": {
            "chemical_warhead_5_set_validated_upstream": True,
            "warhead_role_7_set_validated_upstream": True,
            "D4_revised_role_validated_upstream": True,
            "direct_role_boundary_validated_upstream": True,
            "canonical_A_B3_C_validated_upstream": True,
            "future_candidate_validated_upstream": True,
            "projected_into_generic_fact": False,
            "reason": "OUTSIDE_GENERIC_RECONCILIATION_CONTRACT",
        },
        "fail_closed_probes": protections,
        "source_order_deterministic": True,
        "published_current_census": published["counts"],
        "global_census_update": "NOT_DONE",
        "priority_queue_update": "NOT_DONE",
        "future_census_informational_only": future,
        "next_pending_derived_informational_only": next_pending,
        "reconciliation_materialized": False,
        "no_training_or_model_work": True,
        "ready_for_external_review": True,
        "ready_for_training": False,
        "feature_semantics": "AUDIT_REQUIRED_LATER",
        "step12d": "SMOKE_LEGALITY_VALIDATION_ONLY_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    report = run_check_v1(args.repo_root)
    if report["ready_for_training"] is not False:
        raise ValueError("READY_FOR_TRAINING_MUST_BE_FALSE")
    print("check=" + report["check"])
    print("lifecycle=" + report["exact4"]["lifecycle"])
    print("source_bindings=12")
    print("normalized_facts=91")
    print("completed_positive=91")
    print("pending=223")
    print("published_global_positive=104")
    print("future_global_positive=108_INFORMATIONAL_ONLY")
    print("next_pending=DERIVED_FROM_RECONCILIATION_INFORMATIONAL_ONLY")
    print("global_census_update=NOT_DONE")
    print("priority_queue_update=NOT_DONE")
    print("READY_FOR_TRAINING=false")
    print("feature_semantics=AUDIT_REQUIRED_LATER")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
