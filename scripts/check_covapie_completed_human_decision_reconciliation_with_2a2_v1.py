#!/usr/bin/env python3
"""Repository-state-neutral checker for 2A2 reconciliation successor V1."""

from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
import csv
from dataclasses import fields
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
    covapie_2a2_completed_decision_ingestion_and_task_label_availability_v1
    as two_a2_ingestion_owner,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_v1 as generic,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_2a2_v1 as subject,
)


EXACT4_PATHS = (
    "src/covalent_ext/"
    "covapie_completed_human_decision_reconciliation_with_2a2_v1.py",
    "scripts/"
    "check_covapie_completed_human_decision_reconciliation_with_2a2_v1.py",
    "tests/"
    "test_covapie_completed_human_decision_reconciliation_with_2a2_v1.py",
    "docs/covapie_completed_human_decision_reconciliation_with_2a2_v1_guide.md",
)
CURRENT_CENSUS_ROOT = (
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_f24_v1/"
)
CURRENT_CENSUS_CSV = (
    CURRENT_CENSUS_ROOT
    + "covapie_cumulative1000_current_global_readiness_census_with_f24_v1.csv"
)
CURRENT_CENSUS_SUMMARY = (
    CURRENT_CENSUS_ROOT
    + "covapie_cumulative1000_current_global_readiness_summary_with_f24_v1.json"
)
FROZEN_REPOSITORY_FILES = (
    (
        "GENERIC_RECONCILIATION_OWNER",
        "src/covalent_ext/covapie_completed_human_decision_reconciliation_v1.py",
        35925,
        "2fcdf85f4753cedf6fe803ae1640fbf65484cdad2bc67732b5d9fdc24b8c3548",
    ),
    (
        "ONL_NORMALIZATION_OWNER",
        "src/covalent_ext/"
        "covapie_completed_human_decision_reconciliation_with_onl_v1.py",
        13046,
        "f2c94ac8b4fe8f3706d0de288e2d5bb24ef211cf56d39e8362b43bdb17a2f475",
    ),
    (
        "F24_RECONCILIATION_SOURCE_PREDECESSOR",
        "src/covalent_ext/"
        "covapie_completed_human_decision_reconciliation_with_f24_v1.py",
        21089,
        "7ab2d47d247e6a342645b1a1b78352671d5d60a2902f1ef21fad9241a83ee325",
    ),
    (
        "F24_RECONCILIATION_CHECKER",
        "scripts/"
        "check_covapie_completed_human_decision_reconciliation_with_f24_v1.py",
        40998,
        "ac53d8e94887bbd9eecc40e2bc5fae06fb9145afc8bc58316cb401985e41058e",
    ),
    (
        "F24_RECONCILIATION_TESTS",
        "tests/"
        "test_covapie_completed_human_decision_reconciliation_with_f24_v1.py",
        41054,
        "8168e5c45ff6d9d07509a8816c8edab373d997341fe90940dc84f1b3f8cfce89",
    ),
    (
        "F24_RECONCILIATION_GUIDE",
        "docs/covapie_completed_human_decision_reconciliation_with_f24_v1_guide.md",
        6622,
        "41479b5f181787801c4685494a529c0bede08bfffaff789ff8dcceaad16868cf",
    ),
    (
        "2A2_INGESTION_OWNER",
        "src/covalent_ext/"
        "covapie_2a2_completed_decision_ingestion_and_task_label_availability_v1.py",
        81311,
        "57d42fcf673794f27adc7b897c0f51db4304d32f2d35a950b89d63cf4cf7060d",
    ),
    (
        "2A2_PUBLISHED_MATRIX_CROSS_CHECK_ONLY",
        "data/derived/covalent_small/"
        "covapie_2a2_completed_decision_ingestion_and_task_label_availability_v1/"
        "covapie_2a2_event_task_label_availability_v1.csv",
        8950,
        "f6533013dcb2eea5fcee579d906c7ab3009d1db8c9f2d9f906aca5ee0122f52b",
    ),
    (
        "CURRENT_F24_CENSUS_OWNER",
        "src/covalent_ext/"
        "covapie_cumulative1000_current_global_readiness_census_with_f24_v1.py",
        64468,
        "9afb435cb5110c68946a4356482665b2325707bacc96754aca2fa54337a2022b",
    ),
    (
        "CURRENT_F24_CENSUS_CSV",
        CURRENT_CENSUS_CSV,
        527918,
        "0660614ee950828cbb468cc72fdb776b26a6257e144cbae5df2a6d2a2c8f9b74",
    ),
    (
        "CURRENT_F24_CENSUS_SUMMARY",
        CURRENT_CENSUS_SUMMARY,
        16992,
        "4a75f817138379c25fc67186b3316e400c0850ecbb2611fa8d8158860cf39c9b",
    ),
    (
        "CURRENT_F24_CENSUS_MANIFEST",
        CURRENT_CENSUS_ROOT
        + "covapie_cumulative1000_current_global_readiness_manifest_with_f24_v1.json",
        44602,
        "eb8111311d984705d437f496e1cdd5e41899883203665d1f4b366c832bae3347",
    ),
    (
        "HISTORICAL_RECONCILIATION",
        "data/derived/covalent_small/"
        "covapie_cumulative1000_high_yield_human_review_authority_calibration_v1/"
        "covapie_cumulative1000_current_review_status_reconciliation_v1.csv",
        99335,
        "4eb608e2d97b60230ae1e0ca4e4be6a7fe8b3dc45af3467cbc98f685c385862f",
    ),
)
EXPECTED_PUBLIC_API = (
    "CompletedDecisionReconciliationWith2A2Error",
    "project_2a2_completed_decision_v1",
    "load_real_completed_decision_sources_with_2a2_v1",
    "reconcile_real_completed_human_decisions_with_2a2_v1",
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
EXPECTED_PREDECESSOR_SOURCE_FACT_COUNTS = (
    8, 16, 8, 9, 8, 8, 8, 7, 6, 5, 4, 4,
)
EXPECTED_SOURCE_FACT_COUNTS = (*EXPECTED_PREDECESSOR_SOURCE_FACT_COUNTS, 4)
EXPECTED_REVIEW_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 95,
    "completed_positive_unit_count": 13,
    "completed_negative_event_count": 24,
    "completed_negative_unit_count": 4,
    "completed_total_event_count": 119,
    "completed_total_unit_count": 17,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 219,
    "unreviewed_unit_count": 114,
}
EXPECTED_CURRENT_CENSUS = {
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
EXPECTED_FUTURE_CENSUS = {
    "positive": 112,
    "relevant": 113,
    "training_include": 44,
    "training_exclude": 68,
    "future_candidates": 27,
    "sample_pair_authority": 112,
    "sample_role_authority": 112,
    "strict_profile": 52,
    "direct_profile": 60,
    "warhead_only_A": 112,
    "linker_plus_warhead_B": 52,
    "scaffold_plus_warhead_B2": 52,
    "scaffold_only_B3": 112,
    "scaffold_plus_linker_plus_warhead_C": 112,
}
EXPECTED_NEXT_PENDING = {
    "review_unit_id": "COVAPIE_BULK_REVIEW_UNIT_7D83F048AF8A2295",
    "raw_priority_rank": 17,
    "event_count": 4,
    "ligand_component_ids": ("I12",),
    "pdb_ids": ("1WOF", "2AMP"),
}
FORBIDDEN_FACT_ATTRIBUTES = (
    "chemical_warhead_atom_ids",
    "warhead_role_atom_ids",
    "linker_atom_ids",
    "scaffold_atom_ids",
    "role_profile",
    "role_boundaries",
    "selected_candidate",
    "canonical_task_applicability",
    "minimal_seed",
    "POST_geometry",
    "PRE_topology",
    "PRE_geometry",
    "engineered_target_site",
    "disulfide_trapping_context",
    "future_training_candidate",
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
        or len(expected_paths) != 4
        or len(set(expected_paths)) != 4
        or any(type(path) is not str or not path for path in expected_paths)
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
    expected_untracked_status = tuple(sorted("?? " + path for path in expected_paths))
    if (
        not tracked_exact4
        and status == expected_untracked_status
        and not working
        and not cached
    ):
        return _CANDIDATE_UNTRACKED
    if tracked_exact4 == expected and not status and not working and not cached:
        return _TRACKED_CLEAN
    raise ValueError(
        "REPOSITORY_PROFILE_NOT_EXACT_CANDIDATE_UNTRACKED_OR_TRACKED_CLEAN"
    )


def _repository_observations(repo_root: Path) -> dict[str, object]:
    tracked = _git_nul_items(repo_root, ("git", "ls-files", "-z"), "TRACKED_PATHS")
    status = _git_nul_items(
        repo_root,
        ("git", "status", "--short", "--untracked-files=all", "-z"),
        "STATUS_SHORT_ALL",
    )
    working = _git_nul_items(
        repo_root, ("git", "diff", "--name-only", "-z"), "WORKING_DIFF"
    )
    cached = _git_nul_items(
        repo_root,
        ("git", "diff", "--cached", "--name-only", "-z"),
        "CACHED_DIFF",
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
        if "__pycache__" in path.split("/") or path.endswith(FORBIDDEN_SUFFIXES)
    )
    if forbidden:
        raise ValueError("FORBIDDEN_OR_TRANSIENT_REPOSITORY_PATH:" + forbidden[0])


def _ignored_transient_paths(repo_root: Path) -> tuple[str, ...]:
    ignored = _git_nul_items(
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
            for line in ignored
            if line.startswith("!! ")
            for path in (_status_entry_path(line),)
            if "__pycache__" in path.rstrip("/").split("/")
            or path.endswith((".pyc", ".tmp", ".part", ".log"))
        )
    )


def verify_candidate_exact4_v1(repo_root: Path) -> dict[str, object]:
    """Verify one of the two permitted Exact4 repository profiles."""

    root = repo_root.resolve()
    artifacts: list[dict[str, object]] = []
    for relative in EXACT4_PATHS:
        path = root / relative
        payload = _read_regular_file(path, relative)
        _validate_text_payload(payload, relative)
        if len(payload) >= MAX_FILE_BYTES:
            raise ValueError("EXACT4_FILE_TOO_LARGE:" + relative)
        artifacts.append(
            {
                "path": relative,
                "byte_count": len(payload),
                "line_count": len(payload.decode("utf-8").splitlines()),
                "sha256": _sha256(payload),
                "mode": f"{stat.S_IMODE(path.stat().st_mode):04o}",
            }
        )
    observations = _repository_observations(root)
    tracked_paths = observations["tracked_paths"]
    status_lines = observations["status_lines"]
    working = observations["working_tree_diff_paths"]
    cached = observations["cached_diff_paths"]
    assert type(tracked_paths) is set
    assert type(status_lines) is tuple
    assert type(working) is tuple
    assert type(cached) is tuple
    _reject_dirty_forbidden_or_transient_paths(status_lines, working, cached)
    ignored = _ignored_transient_paths(root)
    if ignored:
        raise ValueError("IGNORED_TRANSIENT_REPOSITORY_PATH:" + ignored[0])
    lifecycle = _classify_repository_profile(
        expected_paths=EXACT4_PATHS,
        tracked_paths=tracked_paths,
        status_lines=status_lines,
        working_tree_diff_paths=working,
        cached_diff_paths=cached,
    )
    return {
        "count": len(artifacts),
        "artifacts": tuple(artifacts),
        "lifecycle": lifecycle,
        "supported_successful_profiles": _SUPPORTED_REPOSITORY_PROFILES,
        "third_successful_profile": False,
        "tracked_exact4_count": len(set(EXACT4_PATHS) & tracked_paths),
        "git_status_entry_count": len(status_lines),
        "working_tree_diff_count": len(working),
        "cached_diff_count": len(cached),
    }


def _verify_frozen_inputs(repo_root: Path) -> dict[str, object]:
    artifacts = [
        _verify_file(
            repo_root.resolve() / relative,
            label=label,
            expected_byte_count=byte_count,
            expected_sha256=digest,
        )
        for label, relative, byte_count, digest in FROZEN_REPOSITORY_FILES
    ]
    return {"count": len(artifacts), "artifacts": tuple(artifacts)}


def _verify_thin_successor_architecture(repo_root: Path) -> dict[str, object]:
    payload = _read_regular_file(repo_root / EXACT4_PATHS[0], "2A2_SUCCESSOR")
    tree = ast.parse(payload)
    if subject.__all__ != EXPECTED_PUBLIC_API:
        raise ValueError("PUBLIC_API_NOT_MINIMAL_EXACT4")
    if subject.TWO_A2_TRANSITION_ADAPTER_CREATED is not False:
        raise ValueError("2A2_TRANSITION_ADAPTER_FLAG_INVALID")
    function_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    if any(
        name.lower().startswith("_adapt_2a2")
        or ("2a2" in name.lower() and "transition" in name.lower())
        for name in function_names
    ):
        raise ValueError("2A2_TRANSITION_HELPER_CREATED")
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
        "f24_source_loader": "load_real_completed_decision_sources_with_f24_v1",
        "two_a2_projector": "project_2a2_completed_decision_v1",
        "two_a2_ingestion_loader": "load_frozen_formal_decision_v1",
        "onl_adapter": "_adapt_onl_in_progress_completion_for_generic_reconciliation_v1",
        "generic_reconciler": "reconcile_completed_human_decisions_v1",
    }
    if any(called.count(name) != 1 for name in expected_once.values()):
        raise ValueError("THIN_SUCCESSOR_DELEGATE_AST_COUNTS_INVALID")
    if called.count("reconcile_real_completed_human_decisions_with_f24_v1") != 0:
        raise ValueError("F24_RESULT_RECONCILIATION_FORBIDDEN")
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    if imported & {"json", "csv", "dataset", "lightning_modules", "equivariant_diffusion"}:
        raise ValueError("PARSING_TRAINING_OR_MODEL_IMPORT_FORBIDDEN")
    source_text = payload.decode("utf-8")
    if any(
        token in source_text
        for token in (
            "covapie_2a2_event_task_label_availability_v1.csv",
            "completed_human_decision_snapshot_v1.json",
            "I12",
            "COVAPIE_BULK_REVIEW_UNIT_7D83F048AF8A2295",
        )
    ):
        raise ValueError("SECOND_AUTHORITY_OR_NEXT_PENDING_HARDCODE_CREATED")
    return {
        "public_api": subject.__all__,
        "two_a2_transition_adapter_created": False,
        "direct_formal_json_parse_count": 0,
        "manual_overlay_count": 0,
        **{
            key + "_ast_call_count": called.count(value)
            for key, value in expected_once.items()
        },
        "f24_reconciliation_result_ast_call_count": 0,
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
        raise ValueError("2A2_GENERIC_FACT_NOT_THIN")
    try:
        generic.NormalizedCompletedDecisionFact(
            **{
                field: getattr(source.facts[0], field)
                for field in EXPECTED_GENERIC_FACT_FIELDS
            },
            future_training_candidate=True,
        )
    except TypeError:
        pass
    else:
        raise ValueError("GENERIC_FACT_ACCEPTED_RICH_FIELD")
    return {
        "field_names": observed,
        "chemical_warhead_projected": False,
        "role_partition_projected": False,
        "pre_or_post_projected": False,
        "minimal_seed_projected": False,
        "future_candidate_projected": False,
        "training_admission_projected": False,
    }


def _run_production_pipeline_counted(
    repo_root: Path,
    validated_bound: dict[str, object],
) -> tuple[
    generic.ReconciliationResult,
    dict[str, int],
    tuple[dict[str, str], ...],
    tuple[dict[str, str], ...],
]:
    """Count direct delegates while using a prevalidated ingestion response."""

    original_f24_loader = (
        subject.f24_successor.load_real_completed_decision_sources_with_f24_v1
    )
    original_projector = subject.project_2a2_completed_decision_v1
    original_ingestion = (
        subject.two_a2_ingestion_owner.load_frozen_formal_decision_v1
    )
    original_onl = (
        subject.onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1
    )
    original_generic = subject.generic.reconcile_completed_human_decisions_v1
    original_f24_result = (
        subject.f24_successor.reconcile_real_completed_human_decisions_with_f24_v1
    )
    calls: Counter[str] = Counter()
    captured_original: tuple[dict[str, str], ...] = ()
    captured_adapted: tuple[dict[str, str], ...] = ()

    def counted_f24_loader(root: Path) -> tuple[generic.NormalizedDecisionSource, ...]:
        calls["f24_source_loader"] += 1
        return original_f24_loader(root)

    def counted_projector(*, repo_root: Path) -> generic.NormalizedDecisionSource:
        calls["two_a2_projector"] += 1
        return original_projector(repo_root=repo_root)

    def counted_ingestion(root: Path) -> dict[str, object]:
        del root
        calls["two_a2_ingestion_loader"] += 1
        return validated_bound

    def counted_onl(rows: object) -> tuple[dict[str, str], ...]:
        nonlocal captured_original, captured_adapted
        calls["onl_adapter"] += 1
        captured_original = tuple(dict(row) for row in rows)  # type: ignore[arg-type]
        captured_adapted = original_onl(rows)  # type: ignore[arg-type]
        return captured_adapted

    def counted_generic(rows: object, sources: object) -> generic.ReconciliationResult:
        calls["generic_reconciler"] += 1
        return original_generic(rows, sources)  # type: ignore[arg-type]

    def forbidden_f24_result(_root: Path) -> generic.ReconciliationResult:
        calls["f24_reconciliation_result"] += 1
        raise ValueError("F24_RECONCILIATION_RESULT_CALLED")

    subject.f24_successor.load_real_completed_decision_sources_with_f24_v1 = counted_f24_loader
    subject.project_2a2_completed_decision_v1 = counted_projector
    subject.two_a2_ingestion_owner.load_frozen_formal_decision_v1 = counted_ingestion
    subject.onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1 = counted_onl
    subject.generic.reconcile_completed_human_decisions_v1 = counted_generic
    subject.f24_successor.reconcile_real_completed_human_decisions_with_f24_v1 = forbidden_f24_result
    try:
        result = subject.reconcile_real_completed_human_decisions_with_2a2_v1(repo_root)
    finally:
        subject.f24_successor.load_real_completed_decision_sources_with_f24_v1 = original_f24_loader
        subject.project_2a2_completed_decision_v1 = original_projector
        subject.two_a2_ingestion_owner.load_frozen_formal_decision_v1 = original_ingestion
        subject.onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1 = original_onl
        subject.generic.reconcile_completed_human_decisions_v1 = original_generic
        subject.f24_successor.reconcile_real_completed_human_decisions_with_f24_v1 = original_f24_result
    expected = Counter(
        {
            "f24_source_loader": 1,
            "two_a2_projector": 1,
            "two_a2_ingestion_loader": 1,
            "onl_adapter": 1,
            "generic_reconciler": 1,
        }
    )
    if calls != expected:
        raise ValueError("PRODUCTION_DELEGATE_RUNTIME_CALL_COUNTS_INVALID")
    return result, dict(calls), captured_original, captured_adapted


def _verify_reconciliation_counts_v1(
    result: generic.ReconciliationResult,
) -> Counter[str]:
    if result.review_summary != EXPECTED_REVIEW_SUMMARY:
        raise ValueError("RECONCILIATION_SUMMARY_INVALID")
    dispositions = Counter(
        fact.training_disposition for fact in result.normalized_facts
    )
    if dispositions != Counter(
        {generic.TRAINING_INCLUDE: 27, generic.TRAINING_EXCLUDE: 68}
    ):
        raise ValueError("NORMALIZED_TRAINING_DISPOSITIONS_INVALID")
    return dispositions


def _verify_source_order_determinism_v1(
    adapted_rows: tuple[dict[str, str], ...],
    sources: tuple[generic.NormalizedDecisionSource, ...],
    expected_result: generic.ReconciliationResult,
) -> None:
    normal = generic.reconcile_completed_human_decisions_v1(
        adapted_rows, sources
    )
    reversed_result = generic.reconcile_completed_human_decisions_v1(
        adapted_rows, tuple(reversed(sources))
    )
    if normal != reversed_result or normal != expected_result:
        raise ValueError("SOURCE_ORDER_NOT_DETERMINISTIC")


def _published_census_state(repo_root: Path) -> dict[str, object]:
    try:
        rows = tuple(
            csv.DictReader(
                io.StringIO(
                    _read_regular_file(repo_root / CURRENT_CENSUS_CSV, "CURRENT_CENSUS")
                    .decode("utf-8"),
                    newline="",
                )
            )
        )
        summary = json.loads(
            _read_regular_file(
                repo_root / CURRENT_CENSUS_SUMMARY, "CURRENT_CENSUS_SUMMARY"
            )
        )
    except (UnicodeDecodeError, csv.Error, json.JSONDecodeError) as error:
        raise ValueError("PUBLISHED_CURRENT_CENSUS_PARSE_FAILED") from error
    if len(rows) != 1000 or type(summary) is not dict:
        raise ValueError("PUBLISHED_CURRENT_CENSUS_NOT_EXACT1000")
    target_ids = set(subject._TWO_A2_EVENT_IDS)
    target_rows = [row for row in rows if row.get("canonical_event_id") in target_ids]
    if len(target_rows) != 4 or any(
        row.get("review_unit_id") != subject._TWO_A2_REVIEW_UNIT_ID
        or row.get("current_global_status") != generic.CURRENTLY_UNREVIEWED
        or row.get("human_review_completed") != "false"
        or row.get("chemistry_disposition") != "UNRESOLVED"
        or row.get("task_relevance_disposition") != "UNRESOLVED"
        or row.get("training_use_disposition") != "UNRESOLVED"
        or row.get("formal_training_admitted") != "false"
        for row in target_rows
    ):
        raise ValueError("PUBLISHED_CURRENT_CENSUS_2A2_STATE_INVALID")
    task_counts = {
        task["semantic_name"]: task["structurally_applicable_authoritative_role_count"]
        for task in summary["canonical_exact5"]["tasks"]
    }
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
            row.get("future_training_admission_candidate") == "true" for row in rows
        ),
        "sample_pair_authority": summary["reactive_pair"]["sample_level_authoritative_pair_count"],
        "sample_role_authority": summary["role"]["role_partition_sample_authoritative_count"],
        "strict_profile": summary["role"]["role_profile_counts"]["STRICT_LINKER_PRESENT_V1"],
        "direct_profile": summary["role"]["role_profile_counts"]["DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"],
        "warhead_only_A": task_counts["warhead_only"],
        "linker_plus_warhead_B": task_counts["linker_plus_warhead"],
        "scaffold_plus_warhead_B2": task_counts["scaffold_plus_warhead"],
        "scaffold_only_B3": task_counts["scaffold_only"],
        "scaffold_plus_linker_plus_warhead_C": task_counts["scaffold_plus_linker_plus_warhead"],
    }
    if counts != EXPECTED_CURRENT_CENSUS:
        raise ValueError("PUBLISHED_CURRENT_CENSUS_COUNTS_INVALID")
    return {"counts": counts, "summary": summary, "rows": rows}


def _verify_future_census_informational(
    source: generic.NormalizedDecisionSource,
    bound: dict[str, object],
    published: dict[str, object],
) -> dict[str, int]:
    current = published["counts"]
    formal = bound.get("formal")
    if type(current) is not dict or type(formal) is not dict or len(source.facts) != 4:
        raise ValueError("FUTURE_CENSUS_INPUT_INVALID")
    subject._validate_rich_2a2_semantics_v1(bound)
    role = formal["selected_role_partition"]
    canonical = formal["canonical_Exact5_and_sample_applicability"]
    if role["role_profile"] != "STRICT_LINKER_PRESENT_V1":
        raise ValueError("FUTURE_CENSUS_ROLE_PROFILE_INVALID")
    applicable = {
        task["semantic_name"]
        for task in canonical["tasks"]
        if task["structurally_applicable_to_2A2"] is True
    }
    include_delta = sum(
        fact.training_disposition == generic.TRAINING_INCLUDE for fact in source.facts
    )
    exclude_delta = sum(
        fact.training_disposition == generic.TRAINING_EXCLUDE for fact in source.facts
    )
    observed = {
        "positive": current["positive"] + 4,
        "relevant": current["relevant"] + 4,
        "training_include": current["training_include"] + include_delta,
        "training_exclude": current["training_exclude"] + exclude_delta,
        "future_candidates": current["future_candidates"],
        "sample_pair_authority": current["sample_pair_authority"] + 4,
        "sample_role_authority": current["sample_role_authority"] + 4,
        "strict_profile": current["strict_profile"] + 4,
        "direct_profile": current["direct_profile"],
        "warhead_only_A": current["warhead_only_A"] + (4 if "warhead_only" in applicable else 0),
        "linker_plus_warhead_B": current["linker_plus_warhead_B"] + (4 if "linker_plus_warhead" in applicable else 0),
        "scaffold_plus_warhead_B2": current["scaffold_plus_warhead_B2"] + (4 if "scaffold_plus_warhead" in applicable else 0),
        "scaffold_only_B3": current["scaffold_only_B3"] + (4 if "scaffold_only" in applicable else 0),
        "scaffold_plus_linker_plus_warhead_C": current["scaffold_plus_linker_plus_warhead_C"] + (4 if "scaffold_plus_linker_plus_warhead" in applicable else 0),
    }
    if observed != EXPECTED_FUTURE_CENSUS:
        raise ValueError("FUTURE_CENSUS_INFORMATIONAL_DERIVATION_INVALID")
    return observed


def _derive_next_pending(result: generic.ReconciliationResult) -> dict[str, object]:
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
    parts = [event_id.split(":") for event_id in event_ids]
    result_value = {
        "review_unit_id": rows[0]["raw_review_unit_id"],
        "raw_priority_rank": int(rows[0]["raw_priority_rank"]),
        "event_count": len(event_ids),
        "ligand_component_ids": tuple(sorted({part[-2] for part in parts})),
        "pdb_ids": tuple(sorted({part[1] for part in parts})),
        "event_ids": event_ids,
    }
    if (
        len(event_ids) != int(rows[0]["raw_unit_event_count"])
        or any(result_value[key] != value for key, value in EXPECTED_NEXT_PENDING.items())
    ):
        raise ValueError("NEXT_PENDING_DERIVATION_INVALID")
    return result_value


def _expect_subject_failure(callable_: object, token: str) -> None:
    try:
        callable_()  # type: ignore[operator]
    except subject.CompletedDecisionReconciliationWith2A2Error as error:
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
        lambda: subject._project_validated_2a2_binding_v1(drifted_binding),
        "2A2_FORMAL_DECISION_BINDING_INVALID",
    )
    drifted_role = json.loads(json.dumps(bound))
    drifted_role["formal"]["selected_role_partition"]["role_profile"] = "WRONG"
    _expect_subject_failure(
        lambda: subject._project_validated_2a2_binding_v1(drifted_role),
        "2A2_CANDIDATE4_STRICT_ROLE_PARTITION_INVALID",
    )
    missing = tuple(
        row
        for row in historical
        if row["canonical_event_id"] != subject._TWO_A2_EVENT_IDS[0]
    )
    _expect_subject_failure(
        lambda: subject._prove_2a2_original_unreviewed_prior_v1(missing),
        "2A2_HISTORICAL_EVENT_MISSING",
    )
    changed = [dict(row) for row in adapted]
    row = next(
        row
        for row in changed
        if row["canonical_event_id"] == subject._TWO_A2_EVENT_IDS[0]
    )
    row["current_status_authority_sources_json"] = '["unexpected"]'
    _expect_subject_failure(
        lambda: subject._prove_2a2_rows_unchanged_after_onl_normalization_v1(
            historical, changed
        ),
        "ONL_ADAPTER_CHANGED_2A2_ROW",
    )
    return {
        "formal_binding_drift_rejected": True,
        "rich_role_drift_rejected": True,
        "missing_historical_event_rejected": True,
        "onl_2a2_mutation_rejected": True,
    }


def run_check_v1(repo_root: Path) -> dict[str, object]:
    """Run all read-only 2A2 reconciliation checks and return evidence."""

    root = repo_root.resolve()
    exact4 = verify_candidate_exact4_v1(root)
    frozen = _verify_frozen_inputs(root)
    architecture = _verify_thin_successor_architecture(root)

    bound = two_a2_ingestion_owner.load_frozen_formal_decision_v1(root)
    subject._validate_rich_2a2_semantics_v1(bound)
    source = subject._project_validated_2a2_binding_v1(bound)
    thinness = _verify_generic_fact_thinness(source)

    historical = generic.load_real_historical_reconciliation_v1(root)
    subject._prove_2a2_original_unreviewed_prior_v1(historical)
    result, calls, captured_original, captured_adapted = (
        _run_production_pipeline_counted(root, bound)
    )
    subject._prove_2a2_rows_unchanged_after_onl_normalization_v1(
        captured_original, captured_adapted
    )

    sources = subject.load_real_completed_decision_sources_with_2a2_v1(root)
    event_ids = [fact.canonical_event_id for item in sources for fact in item.facts]
    if (
        len(sources) != 13
        or tuple(len(item.facts) for item in sources) != EXPECTED_SOURCE_FACT_COUNTS
        or len({item.binding.stable_identity for item in sources}) != 13
        or len({item.binding.review_unit_id for item in sources}) != 13
        or len(event_ids) != 95
        or len(set(event_ids)) != 95
    ):
        raise ValueError("EXACT13_SOURCE_COMPOSITION_INVALID")
    dispositions = _verify_reconciliation_counts_v1(result)

    target_ids = set(subject._TWO_A2_EVENT_IDS)
    target_facts = {
        fact.canonical_event_id: fact
        for fact in result.normalized_facts
        if fact.canonical_event_id in target_ids
    }
    target_rows = {
        row["canonical_event_id"]: row
        for row in result.reconciled_rows
        if row["canonical_event_id"] in target_ids
    }
    expected_authority = json.dumps(
        [source.binding.source_path], separators=(",", ":"), sort_keys=True
    )
    if len(target_facts) != 4 or any(
        fact.review_unit_id != subject._TWO_A2_REVIEW_UNIT_ID
        or fact.human_review_completed is not True
        or fact.legacy_completed_review_status != generic.COMPLETED_HUMAN_POSITIVE
        or fact.task_relevance_disposition != generic.TASK_RELEVANT
        or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
        or fact.training_disposition != generic.TRAINING_EXCLUDE
        or fact.human_training_excluded is not True
        for fact in target_facts.values()
    ):
        raise ValueError("FINAL_2A2_NORMALIZED_FACTS_INVALID")
    if len(target_rows) != 4 or any(
        row["raw_review_unit_id"] != subject._TWO_A2_REVIEW_UNIT_ID
        or row["current_review_status"] != generic.COMPLETED_HUMAN_POSITIVE
        or row["calibration_eligible"] != "false"
        or row["calibration_exclusion_reason"] != generic.COMPLETED_HUMAN_POSITIVE
        or row["current_status_authority_sources_json"] != expected_authority
        for row in target_rows.values()
    ):
        raise ValueError("FINAL_2A2_RECONCILED_ROWS_INVALID")

    _verify_source_order_determinism_v1(captured_adapted, sources, result)
    try:
        generic.reconcile_completed_human_decisions_v1(captured_original, sources)
    except generic.CompletedDecisionReconciliationError as error:
        if "PRIOR_REVIEW_STATUS_NOT_UNREVIEWED" not in str(error):
            raise ValueError("ORIGINAL_ONL_FAILURE_TOKEN_INVALID") from error
    else:
        raise ValueError("ORIGINAL_ONL_PRIOR_NOT_REJECTED")

    f24_result = (
        subject.f24_successor.reconcile_real_completed_human_decisions_with_f24_v1(root)
    )
    f24_dispositions = Counter(
        fact.training_disposition for fact in f24_result.normalized_facts
    )
    delta = {
        "completed_positive_events": (
            result.review_summary["completed_positive_event_count"]
            - f24_result.review_summary["completed_positive_event_count"]
        ),
        "completed_positive_units": (
            result.review_summary["completed_positive_unit_count"]
            - f24_result.review_summary["completed_positive_unit_count"]
        ),
        "completed_total_events": (
            result.review_summary["completed_total_event_count"]
            - f24_result.review_summary["completed_total_event_count"]
        ),
        "completed_total_units": (
            result.review_summary["completed_total_unit_count"]
            - f24_result.review_summary["completed_total_unit_count"]
        ),
        "pending_events": (
            result.review_summary["unreviewed_event_count"]
            - f24_result.review_summary["unreviewed_event_count"]
        ),
        "pending_units": (
            result.review_summary["unreviewed_unit_count"]
            - f24_result.review_summary["unreviewed_unit_count"]
        ),
        "include": dispositions[generic.TRAINING_INCLUDE]
        - f24_dispositions[generic.TRAINING_INCLUDE],
        "exclude": dispositions[generic.TRAINING_EXCLUDE]
        - f24_dispositions[generic.TRAINING_EXCLUDE],
    }
    if delta != {
        "completed_positive_events": 4,
        "completed_positive_units": 1,
        "completed_total_events": 4,
        "completed_total_units": 1,
        "pending_events": -4,
        "pending_units": -1,
        "include": 0,
        "exclude": 4,
    }:
        raise ValueError("2A2_RECONCILIATION_DELTA_INVALID")

    published = _published_census_state(root)
    future = _verify_future_census_informational(source, bound, published)
    next_pending = _derive_next_pending(result)
    protections = _verify_fail_closed_probes(
        bound, captured_original, captured_adapted
    )

    return {
        "check": "PASS",
        "exact4": exact4,
        "frozen_bindings": frozen,
        "architecture": architecture,
        "delegate_runtime_calls": calls,
        "generic_fact_thinness": thinness,
        "source_fact_counts": EXPECTED_SOURCE_FACT_COUNTS,
        "source_count": 13,
        "review_unit_count": 13,
        "normalized_fact_count": 95,
        "unique_normalized_fact_ids": 95,
        "event_collisions": 0,
        "two_a2_prior": {
            "event_count": 4,
            "status": generic.CURRENTLY_UNREVIEWED,
            "calibration_eligible": True,
            "calibration_exclusion_reason": "",
            "transition_adapter": "NOT_CREATED",
        },
        "onl_adapter_left_2a2_unchanged": True,
        "review_summary": result.review_summary,
        "training_dispositions": dict(dispositions),
        "two_a2_delta_from_f24": delta,
        "rich_semantics_boundary": {
            "candidate4_validated_upstream": True,
            "strict_role_validated_upstream": True,
            "chemical_warhead_validated_upstream": True,
            "pre_post_seed_boundaries_validated_upstream": True,
            "future_candidate_false_validated_upstream": True,
            "training_admission_false_validated_upstream": True,
            "projected_into_generic_fact": False,
        },
        "fail_closed_probes": protections,
        "source_order_deterministic": True,
        "published_current_census": published["counts"],
        "global_census_update": "NOT_DONE",
        "priority_queue_update": "NOT_DONE",
        "future_census_informational_only": future,
        "future_census_status": (
            "INFORMATIONAL_ONLY_NOT_CURRENT_GLOBAL_STATE_NOT_MATERIALIZED_THIS_STEP"
        ),
        "next_pending_derived_informational_only": next_pending,
        "i12_review_started": False,
        "reconciliation_materialized": False,
        "no_training_or_model_work": True,
        "ready_for_external_review": True,
        "ready_for_training": False,
        "feature_semantics": "AUDIT_REQUIRED_LATER",
        "step12d": (
            "SMOKE_LEGALITY_VALIDATION_ONLY_NOT_FINAL_TRAINING_FEATURE_CONTRACT"
        ),
        "filesystem_mode_authority_tech_debt": (
            "DEFERRED_UNTIL_AFTER_2A2_END_TO_END_CLOSURE"
        ),
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
    print("source_bindings=13")
    print("normalized_facts=95")
    print("completed_positive=95")
    print("pending=219")
    print("published_global_positive=108")
    print("future_global_positive=112_INFORMATIONAL_ONLY")
    print("next_pending=DERIVED_FROM_RECONCILIATION_INFORMATIONAL_ONLY")
    print("global_census_update=NOT_DONE")
    print("priority_queue_update=NOT_DONE")
    print("I12_REVIEW_STARTED=false")
    print("READY_FOR_TRAINING=false")
    print("feature_semantics=AUDIT_REQUIRED_LATER")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
