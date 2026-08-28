"""Repository-state-neutral checker for OZJ reconciliation successor V1."""

from __future__ import annotations

import argparse
import ast
from collections import Counter
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
    covapie_completed_human_decision_reconciliation_with_ozj_v1 as subject,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_onl_v1 as onl_successor,
)
from covalent_ext import (  # noqa: E402
    covapie_ozj_completed_decision_ingestion_and_task_label_availability_v1
    as ozj_ingestion_owner,
)


EXACT4_PATHS = (
    "src/covalent_ext/"
    "covapie_completed_human_decision_reconciliation_with_ozj_v1.py",
    "scripts/"
    "check_covapie_completed_human_decision_reconciliation_with_ozj_v1.py",
    "tests/"
    "test_covapie_completed_human_decision_reconciliation_with_ozj_v1.py",
    "docs/covapie_completed_human_decision_reconciliation_with_ozj_v1_guide.md",
)
CURRENT_CENSUS_ROOT = (
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_cht_v1/"
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
        "CHT_RECONCILIATION_PREDECESSOR",
        "src/covalent_ext/"
        "covapie_completed_human_decision_reconciliation_with_cht_v1.py",
        13577,
        "263b6726bee54059a0d52a3f32660601de80429d0f876ac79bf55705064cdf43",
    ),
    (
        "OZJ_INGESTION_OWNER",
        "src/covalent_ext/"
        "covapie_ozj_completed_decision_ingestion_and_task_label_availability_v1.py",
        106888,
        "abb80e28e1e139c3515a01c53468530a815c5554b94053afb607053d14a84deb",
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
        "CURRENT_GLOBAL_CENSUS_WITH_CHT_OWNER",
        "src/covalent_ext/"
        "covapie_cumulative1000_current_global_readiness_census_with_cht_v1.py",
        63414,
        "e478b41dca9555bda1caab2cacd3160f3b0cc98c744d50f2eb46a915fccb6f14",
    ),
    (
        "CURRENT_GLOBAL_CENSUS_WITH_CHT_CSV",
        CURRENT_CENSUS_ROOT
        + "covapie_cumulative1000_current_global_readiness_census_with_cht_v1.csv",
        523894,
        "b51bff3d31d910fa4990a1482e0d3b05364fed86a9cf503de833ddf8851f6384",
    ),
    (
        "CURRENT_GLOBAL_CENSUS_WITH_CHT_SUMMARY",
        CURRENT_CENSUS_ROOT
        + "covapie_cumulative1000_current_global_readiness_summary_with_cht_v1.json",
        15828,
        "b2130b1f0b9cf36455f1bf00e6e5c32e9a4ef250f18bb25f7a902af67c79e0b3",
    ),
    (
        "CURRENT_GLOBAL_CENSUS_WITH_CHT_MANIFEST",
        CURRENT_CENSUS_ROOT
        + "covapie_cumulative1000_current_global_readiness_manifest_with_cht_v1.json",
        38794,
        "168f2a713aa9b0ee6904f414330518342ca553495d17340d94ad9df1f8bc1f33",
    ),
)
OZJ_FORMAL_RELATIVE = (
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "OZJ_COVAPIE_BULK_REVIEW_UNIT_18734D9C06222450/"
    "formal-human-decision-v1/ozj_formal_human_decision_v1.json"
)
OZJ_FORMAL_BYTE_COUNT = 28914
OZJ_FORMAL_SHA256 = (
    "0b14271a4541e69d768e28b6433c87b8b22c21505f6e3bdf075bb94381c3c606"
)
EXPECTED_PUBLIC_API = (
    "CompletedDecisionReconciliationWithOZJError",
    "project_ozj_completed_decision_v1",
    "load_real_completed_decision_sources_with_ozj_v1",
    "reconcile_real_completed_human_decisions_with_ozj_v1",
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
EXPECTED_SOURCE_FACT_COUNTS = (8, 16, 8, 9, 8, 8, 8, 7, 6, 5, 4)
EXPECTED_REVIEW_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 87,
    "completed_positive_unit_count": 11,
    "completed_negative_event_count": 24,
    "completed_negative_unit_count": 4,
    "completed_total_event_count": 111,
    "completed_total_unit_count": 15,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 227,
    "unreviewed_unit_count": 116,
}
EXPECTED_CURRENT_CENSUS = {
    "positive": 100,
    "relevant": 101,
    "training_include": 36,
    "training_exclude": 64,
    "future_candidates": 19,
    "sample_pair_authority": 100,
    "sample_role_authority": 100,
}
EXPECTED_FUTURE_CENSUS = {
    "positive": 104,
    "relevant": 105,
    "training_include": 40,
    "training_exclude": 64,
    "future_candidates": 23,
    "sample_pair_authority": 104,
    "sample_role_authority": 104,
    "strict_profile": 48,
    "direct_profile": 56,
    "warhead_only_A": 104,
    "linker_plus_warhead_B": 48,
    "scaffold_plus_warhead_B2": 48,
    "scaffold_only_B3": 104,
    "scaffold_plus_linker_plus_warhead_C": 104,
}
FORBIDDEN_FACT_ATTRIBUTES = (
    "future_training_candidate",
    "candidate_for_future_training_admission",
    "future_training_admission_status",
    "warhead",
    "linker",
    "scaffold",
    "CAF_OAD",
    "PRE_geometry",
    "POST_geometry",
    "reaction_family",
    "warhead_type",
    "training_admitted",
    "runtime",
)
FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip",
    ".tgz", ".npz", ".pyc", ".tmp", ".part",
)
MAX_FILE_BYTES = 1024 * 1024


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
    observed_sha256 = _sha256(payload)
    if observed_sha256 != expected_sha256:
        raise ValueError("FROZEN_SHA256_MISMATCH:" + label)
    return {
        "artifact_role": label,
        "path": path.as_posix(),
        "byte_count": len(payload),
        "sha256": observed_sha256,
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


def _ordinary_untracked(repo_root: Path) -> tuple[str, ...]:
    completed = subprocess.run(
        ("git", "ls-files", "--others", "--exclude-standard", "-z"),
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    return tuple(
        sorted(
            item.decode("utf-8")
            for item in completed.stdout.split(b"\0")
            if item
        )
    )


def verify_candidate_exact4_v1(repo_root: Path) -> dict[str, object]:
    """Verify Exact4 in candidate-untracked or future tracked-clean state."""

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
    untracked = _ordinary_untracked(root)
    if untracked not in ((), tuple(sorted(EXACT4_PATHS))):
        raise ValueError("ORDINARY_UNTRACKED_INVENTORY_NOT_EXACT4_OR_TRACKED_CLEAN")
    forbidden = [path for path in untracked if path.endswith(FORBIDDEN_SUFFIXES)]
    if forbidden:
        raise ValueError("FORBIDDEN_UNTRACKED_FILE:" + forbidden[0])
    return {
        "count": len(artifacts),
        "artifacts": tuple(artifacts),
        "lifecycle": "CANDIDATE_UNTRACKED" if untracked else "TRACKED_CLEAN",
    }


def _verify_frozen_inputs(repo_root: Path) -> dict[str, object]:
    root = repo_root.resolve()
    artifacts = [
        _verify_file(
            root / relative,
            label=label,
            expected_byte_count=byte_count,
            expected_sha256=sha256,
        )
        for label, relative, byte_count, sha256 in FROZEN_REPOSITORY_FILES
    ]
    artifacts.append(
        _verify_file(
            root.parent / OZJ_FORMAL_RELATIVE,
            label="OZJ_FORMAL_HUMAN_DECISION",
            expected_byte_count=OZJ_FORMAL_BYTE_COUNT,
            expected_sha256=OZJ_FORMAL_SHA256,
        )
    )
    return {"count": len(artifacts), "artifacts": tuple(artifacts)}


def _verify_thin_successor_architecture(repo_root: Path) -> dict[str, object]:
    tree = ast.parse(_read_regular_file(repo_root / EXACT4_PATHS[0], "OZJ_SUCCESSOR"))
    if subject.__all__ != EXPECTED_PUBLIC_API:
        raise ValueError("PUBLIC_API_NOT_MINIMAL_EXACT4")
    if subject.OZJ_TRANSITION_ADAPTER_CREATED is not False:
        raise ValueError("OZJ_TRANSITION_ADAPTER_FLAG_INVALID")
    function_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    if any(
        name.lower().startswith("_adapt_ozj")
        or ("ozj" in name.lower() and "transition" in name.lower())
        for name in function_names
    ):
        raise ValueError("OZJ_TRANSITION_HELPER_CREATED")
    generic_classes = {
        "SourceBinding", "NormalizedCompletedDecisionFact",
        "NormalizedDecisionSource", "ReconciliationResult",
    }
    class_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
    }
    if class_names & generic_classes:
        raise ValueError("GENERIC_DATACLASS_DUPLICATED")
    if function_names & {"_validate_source_binding", "_validate_fact", "_review_summary"}:
        raise ValueError("GENERIC_RECONCILIATION_IMPLEMENTATION_DUPLICATED")
    history_names = {
        "row", "rows", "historical", "historical_rows",
        "adapted_historical", "working",
    }
    if any(
        isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign))
        and any(
            isinstance(target, ast.Subscript)
            and isinstance(target.value, ast.Name)
            and target.value.id in history_names
            for target in (
                node.targets if isinstance(node, ast.Assign) else (node.target,)
            )
        )
        for node in ast.walk(tree)
    ):
        raise ValueError("GENERIC_RECONCILIATION_HISTORY_OVERLAY_DUPLICATED")
    called = [
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]
    expected_once = {
        "cht_source_loader": "load_real_completed_decision_sources_with_cht_v1",
        "ozj_ingestion_loader": "load_frozen_formal_decision_v1",
        "onl_adapter": "_adapt_onl_in_progress_completion_for_generic_reconciliation_v1",
        "generic_reconciler": "reconcile_completed_human_decisions_v1",
    }
    if any(called.count(name) != 1 for name in expected_once.values()):
        raise ValueError("THIN_SUCCESSOR_DELEGATE_AST_COUNTS_INVALID")
    if called.count("reconcile_real_completed_human_decisions_with_cht_v1") != 0:
        raise ValueError("CHT_RESULT_RECONCILIATION_FORBIDDEN")
    if any(
        isinstance(node, (ast.Import, ast.ImportFrom))
        and any(
            token in alias.name
            for alias in node.names
            for token in ("lightning_modules", "equivariant_diffusion", "dataset")
        )
        for node in ast.walk(tree)
    ):
        raise ValueError("TRAINING_OR_MODEL_IMPORT_FORBIDDEN")
    return {
        "public_api": subject.__all__,
        "ozj_transition_adapter_created": False,
        "generic_dataclass_duplication_count": 0,
        "generic_reconciliation_implementation_duplication_count": 0,
        "manual_overlay_count": 0,
        **{
            key + "_ast_call_count": called.count(value)
            for key, value in expected_once.items()
        },
        "cht_reconciler_ast_call_count": 0,
    }


def _verify_generic_fact_thinness(
    source: generic.NormalizedDecisionSource,
) -> dict[str, object]:
    observed_fields = tuple(field.name for field in fields(generic.NormalizedCompletedDecisionFact))
    if observed_fields != EXPECTED_GENERIC_FACT_FIELDS:
        raise ValueError("GENERIC_FACT_FIELD_CONTRACT_DRIFT")
    if len(source.facts) != 4 or any(
        type(fact) is not generic.NormalizedCompletedDecisionFact
        or any(hasattr(fact, name) for name in FORBIDDEN_FACT_ATTRIBUTES)
        for fact in source.facts
    ):
        raise ValueError("OZJ_GENERIC_FACT_NOT_THIN")
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
        raise ValueError("GENERIC_FACT_ACCEPTED_FUTURE_CANDIDATE_FIELD")
    return {
        "field_names": observed_fields,
        "future_candidate_propagated": False,
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
    original_cht = subject.cht_successor.load_real_completed_decision_sources_with_cht_v1
    original_ozj = subject.ozj_ingestion_owner.load_frozen_formal_decision_v1
    original_onl = subject.onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1
    original_generic = subject.generic.reconcile_completed_human_decisions_v1
    calls: Counter[str] = Counter()
    captured_original: tuple[dict[str, str], ...] = ()
    captured_adapted: tuple[dict[str, str], ...] = ()

    def counted_cht(root: Path) -> tuple[generic.NormalizedDecisionSource, ...]:
        calls["cht_source_loader"] += 1
        return original_cht(root)

    def counted_ozj(root: Path) -> dict[str, object]:
        calls["ozj_ingestion_loader"] += 1
        return original_ozj(root)

    def counted_onl(rows: object) -> tuple[dict[str, str], ...]:
        nonlocal captured_original, captured_adapted
        calls["onl_adapter"] += 1
        captured_original = tuple(dict(row) for row in rows)  # type: ignore[arg-type]
        captured_adapted = original_onl(rows)  # type: ignore[arg-type]
        return captured_adapted

    def counted_generic(rows: object, sources: object) -> generic.ReconciliationResult:
        calls["generic_reconciler"] += 1
        return original_generic(rows, sources)  # type: ignore[arg-type]

    subject.cht_successor.load_real_completed_decision_sources_with_cht_v1 = counted_cht
    subject.ozj_ingestion_owner.load_frozen_formal_decision_v1 = counted_ozj
    subject.onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1 = counted_onl
    subject.generic.reconcile_completed_human_decisions_v1 = counted_generic
    try:
        result = subject.reconcile_real_completed_human_decisions_with_ozj_v1(repo_root)
    finally:
        subject.cht_successor.load_real_completed_decision_sources_with_cht_v1 = original_cht
        subject.ozj_ingestion_owner.load_frozen_formal_decision_v1 = original_ozj
        subject.onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1 = original_onl
        subject.generic.reconcile_completed_human_decisions_v1 = original_generic
    expected = Counter(
        {
            "cht_source_loader": 1,
            "ozj_ingestion_loader": 1,
            "onl_adapter": 1,
            "generic_reconciler": 1,
        }
    )
    if calls != expected:
        raise ValueError("PRODUCTION_DELEGATE_RUNTIME_CALL_COUNTS_INVALID")
    return result, dict(calls), captured_original, captured_adapted


def _set_status(row: dict[str, str], status: str) -> None:
    row["current_review_status"] = status
    row["calibration_eligible"] = (
        "true" if status == generic.CURRENTLY_UNREVIEWED else "false"
    )
    row["calibration_exclusion_reason"] = (
        "" if status == generic.CURRENTLY_UNREVIEWED else status
    )


def _expect_generic_failure(rows: object, sources: object, token: str) -> None:
    try:
        generic.reconcile_completed_human_decisions_v1(rows, sources)  # type: ignore[arg-type]
    except generic.CompletedDecisionReconciliationError as error:
        if token not in str(error):
            raise ValueError("GENERIC_FAILURE_TOKEN_INVALID:" + str(error)) from error
    else:
        raise ValueError("GENERIC_FAILURE_NOT_RAISED:" + token)


def _synthetic_row(event_id: str, unit_id: str, count: int = 1) -> dict[str, str]:
    return {
        "raw_priority_rank": "1",
        "raw_review_unit_id": unit_id,
        "raw_unit_event_count": str(count),
        "canonical_event_id": event_id,
        "current_review_status": generic.CURRENTLY_UNREVIEWED,
        "current_status_authority_sources_json": '["synthetic/history.csv"]',
        "calibration_eligible": "true",
        "calibration_exclusion_reason": "",
    }


def _synthetic_source(
    path: str, unit_id: str, event_ids: tuple[str, ...]
) -> generic.NormalizedDecisionSource:
    payload = (path + unit_id).encode("utf-8")
    binding = generic.SourceBinding(
        source_path=path,
        path_namespace="synthetic",
        byte_count=len(payload),
        sha256=_sha256(payload),
        schema_version="synthetic_completed_decision_v1",
        review_unit_id=unit_id,
    )
    return generic.NormalizedDecisionSource(
        binding=binding,
        facts=tuple(
            generic.NormalizedCompletedDecisionFact(
                canonical_event_id=event_id,
                review_unit_id=unit_id,
                human_review_completed=True,
                legacy_completed_review_status=generic.COMPLETED_HUMAN_POSITIVE,
                task_relevance_disposition=generic.TASK_RELEVANT,
                chemistry_disposition=generic.CHEMISTRY_POSITIVE,
                training_disposition=generic.TRAINING_INCLUDE,
                human_training_excluded=False,
                source_decision_schema=binding.schema_version,
                source_decision_sha256=binding.sha256,
                source_binding_path=binding.source_path,
            )
            for event_id in event_ids
        ),
    )


def _verify_generic_protections(
    historical: tuple[dict[str, str], ...],
    adapted: tuple[dict[str, str], ...],
    sources: tuple[generic.NormalizedDecisionSource, ...],
) -> dict[str, bool]:
    ozj_ids = set(subject._OZJ_EVENT_IDS)
    for status in (generic.CURRENTLY_IN_PROGRESS, generic.COMPLETED_HUMAN_POSITIVE):
        drifted = [dict(row) for row in adapted]
        for row in drifted:
            if row["canonical_event_id"] in ozj_ids:
                _set_status(row, status)
        _expect_generic_failure(drifted, sources, "PRIOR_REVIEW_STATUS_NOT_UNREVIEWED")
    mixed = [dict(row) for row in adapted]
    row = next(row for row in mixed if row["canonical_event_id"] in ozj_ids)
    _set_status(row, generic.CURRENTLY_IN_PROGRESS)
    _expect_generic_failure(mixed, sources, "HISTORICAL_REVIEW_UNIT_STATUS_MIXED")
    _expect_generic_failure(historical, sources, "PRIOR_REVIEW_STATUS_NOT_UNREVIEWED")

    row1 = _synthetic_row("event-1", "unit-1")
    source1 = _synthetic_source("source-1.json", "unit-1", ("event-1",))
    source2 = _synthetic_source("source-2.json", "unit-1", ("event-1",))
    stable_collision = replace(source1, binding=replace(source1.binding))
    _expect_generic_failure((row1,), (source1, source2), "CROSS_SOURCE_EVENT_COLLISION")
    _expect_generic_failure((row1,), (source1, source1), "SOURCE_BINDING_DUPLICATE")
    _expect_generic_failure((row1,), (source1, stable_collision), "SOURCE_BINDING_DUPLICATE")
    rows2 = (
        _synthetic_row("event-1", "unit-1", 2),
        _synthetic_row("event-2", "unit-1", 2),
    )
    _expect_generic_failure(rows2, (source1,), "SOURCE_REVIEW_UNIT_EVENT_SET_MISMATCH")
    outside = _synthetic_source("outside.json", "unit-1", ("outside",))
    _expect_generic_failure((row1,), (outside,), "EVENT_NOT_IN_HISTORICAL_UNIVERSE")
    mismatch = _synthetic_row("event-1", "unit-other")
    _expect_generic_failure((mismatch,), (source1,), "FACT_HISTORICAL_REVIEW_UNIT_MISMATCH")
    malformed = replace(source1, facts=(replace(source1.facts[0], human_review_completed=False),))
    _expect_generic_failure((row1,), (malformed,), "HUMAN_REVIEW_NOT_COMPLETED")
    return {
        "ozj_in_progress_rejected": True,
        "ozj_completed_rejected": True,
        "ozj_mixed_status_rejected": True,
        "original_onl_prior_rejected": True,
        "cross_source_collision_rejected": True,
        "duplicate_binding_rejected": True,
        "stable_identity_collision_rejected": True,
        "incomplete_unit_coverage_rejected": True,
        "outside_universe_rejected": True,
        "historical_unit_mismatch_rejected": True,
        "malformed_fact_rejected": True,
    }


def _published_census_state(repo_root: Path) -> dict[str, object]:
    csv_path = repo_root / FROZEN_REPOSITORY_FILES[6][1]
    summary_path = repo_root / FROZEN_REPOSITORY_FILES[7][1]
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
    ozj_ids = set(subject._OZJ_EVENT_IDS)
    ozj_rows = [row for row in rows if row.get("canonical_event_id") in ozj_ids]
    if len(ozj_rows) != 4 or any(
        row.get("review_unit_id") != subject._OZJ_REVIEW_UNIT_ID
        or row.get("current_review_status") != generic.CURRENTLY_UNREVIEWED
        or row.get("chemistry_disposition") != "UNRESOLVED"
        or row.get("task_relevance_disposition") != "UNRESOLVED"
        or row.get("training_use_disposition") != "UNRESOLVED"
        for row in ozj_rows
    ):
        raise ValueError("PUBLISHED_CURRENT_CENSUS_OZJ_STATE_INVALID")
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
    return {"counts": counts, "summary": summary}


def _verify_future_census_informational(
    source: generic.NormalizedDecisionSource,
    bound: dict[str, object],
    published: dict[str, object],
) -> dict[str, int]:
    summary = published["summary"]
    normalized = bound.get("normalized")
    if type(summary) is not dict or type(normalized) is not dict or len(source.facts) != 4:
        raise ValueError("FUTURE_CENSUS_INPUT_INVALID")
    events = normalized.get("events")
    if type(events) is not list or len(events) != 4 or any(
        type(event) is not dict
        or event.get("candidate_for_future_training_admission") is not True
        or event.get("future_training_admission_status")
        != ozj_ingestion_owner.FUTURE_STATUS
        or event.get("future_training_candidate_is_training_admission") is not False
        or event.get("training_admitted") is not False
        for event in events
    ):
        raise ValueError("FUTURE_CENSUS_OZJ_CANDIDACY_INPUT_INVALID")
    if any(
        fact.task_relevance_disposition != generic.TASK_RELEVANT
        or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
        or fact.training_disposition != generic.TRAINING_INCLUDE
        or fact.human_training_excluded is not False
        for fact in source.facts
    ):
        raise ValueError("FUTURE_CENSUS_OZJ_DELTA_INVALID")
    tasks = summary["canonical_exact5"]["tasks"]
    task_counts = {
        task["semantic_name"]: task["structurally_applicable_authoritative_role_count"]
        for task in tasks
    }
    observed = {
        "positive": summary["chemistry"]["POSITIVE"]["count"] + 4,
        "relevant": summary["task_relevance"]["RELEVANT"]["count"] + 4,
        "training_include": summary["training_use"]["INCLUDE"]["count"] + 4,
        "training_exclude": summary["training_use"][generic.TRAINING_EXCLUDE]["count"],
        "future_candidates": summary["training_stage"]["future_training_admission_candidate_count"] + 4,
        "sample_pair_authority": summary["reactive_pair"]["sample_level_authoritative_pair_count"] + 4,
        "sample_role_authority": summary["role"]["role_partition_sample_authoritative_count"] + 4,
        "strict_profile": summary["role"]["role_profile_counts"]["STRICT_LINKER_PRESENT_V1"] + 4,
        "direct_profile": summary["role"]["role_profile_counts"]["DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"],
        "warhead_only_A": task_counts["warhead_only"] + 4,
        "linker_plus_warhead_B": task_counts["linker_plus_warhead"] + 4,
        "scaffold_plus_warhead_B2": task_counts["scaffold_plus_warhead"] + 4,
        "scaffold_only_B3": task_counts["scaffold_only"] + 4,
        "scaffold_plus_linker_plus_warhead_C": task_counts["scaffold_plus_linker_plus_warhead"] + 4,
    }
    if observed != EXPECTED_FUTURE_CENSUS:
        raise ValueError("FUTURE_CENSUS_INFORMATIONAL_DERIVATION_INVALID")
    return observed


def run_check_v1(repo_root: Path) -> dict[str, object]:
    """Run all read-only OZJ reconciliation checks and return evidence."""

    root = repo_root.resolve()
    exact4 = verify_candidate_exact4_v1(root)
    frozen = _verify_frozen_inputs(root)
    architecture = _verify_thin_successor_architecture(root)

    source = subject.project_ozj_completed_decision_v1(repo_root=root)
    thinness = _verify_generic_fact_thinness(source)
    if (
        type(source) is not generic.NormalizedDecisionSource
        or tuple(fact.canonical_event_id for fact in source.facts)
        != tuple(sorted(subject._OZJ_EVENT_IDS))
        or len(source.facts) != 4
        or any(
            fact.task_relevance_disposition != generic.TASK_RELEVANT
            or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
            or fact.training_disposition != generic.TRAINING_INCLUDE
            or fact.human_training_excluded is not False
            for fact in source.facts
        )
    ):
        raise ValueError("OZJ_SOURCE_PROJECTION_INVALID")
    bound = ozj_ingestion_owner.load_frozen_formal_decision_v1(root)

    historical = generic.load_real_historical_reconciliation_v1(root)
    subject._prove_ozj_original_unreviewed_prior_v1(historical)
    result, calls, captured_original, captured_adapted = _run_production_pipeline_counted(root)
    subject._prove_ozj_rows_unchanged_after_onl_normalization_v1(
        captured_original, captured_adapted
    )

    sources = subject.load_real_completed_decision_sources_with_ozj_v1(root)
    event_ids = [fact.canonical_event_id for item in sources for fact in item.facts]
    if (
        len(sources) != 11
        or tuple(len(item.facts) for item in sources) != EXPECTED_SOURCE_FACT_COUNTS
        or len({item.binding.stable_identity for item in sources}) != 11
        or len({item.binding.review_unit_id for item in sources}) != 11
        or len(event_ids) != 87
        or len(set(event_ids)) != 87
    ):
        raise ValueError("EXACT11_SOURCE_COMPOSITION_INVALID")
    if result.review_summary != EXPECTED_REVIEW_SUMMARY:
        raise ValueError("RECONCILIATION_SUMMARY_INVALID")
    dispositions = Counter(fact.training_disposition for fact in result.normalized_facts)
    if dispositions != Counter(
        {generic.TRAINING_INCLUDE: 23, generic.TRAINING_EXCLUDE: 64}
    ):
        raise ValueError("NORMALIZED_TRAINING_DISPOSITIONS_INVALID")
    final_ozj = {
        row["canonical_event_id"]: row
        for row in result.reconciled_rows
        if row["canonical_event_id"] in set(subject._OZJ_EVENT_IDS)
    }
    expected_authority = json.dumps(
        [source.binding.source_path], separators=(",", ":"), sort_keys=True
    )
    if len(final_ozj) != 4 or any(
        row["raw_review_unit_id"] != subject._OZJ_REVIEW_UNIT_ID
        or row["current_review_status"] != generic.COMPLETED_HUMAN_POSITIVE
        or row["calibration_eligible"] != "false"
        or row["calibration_exclusion_reason"] != generic.COMPLETED_HUMAN_POSITIVE
        or row["current_status_authority_sources_json"] != expected_authority
        for row in final_ozj.values()
    ):
        raise ValueError("FINAL_OZJ_RECONCILED_ROWS_INVALID")

    normal = generic.reconcile_completed_human_decisions_v1(captured_adapted, sources)
    reversed_result = generic.reconcile_completed_human_decisions_v1(
        captured_adapted, tuple(reversed(sources))
    )
    if normal != reversed_result or normal != result:
        raise ValueError("SOURCE_ORDER_NOT_DETERMINISTIC")
    protections = _verify_generic_protections(historical, captured_adapted, sources)

    published = _published_census_state(root)
    future = _verify_future_census_informational(source, bound, published)
    pending = published["summary"]["top_pending_review_units_by_event_yield"]  # type: ignore[index]
    next_pending = pending[1]
    if (
        pending[0].get("review_unit_id") != subject._OZJ_REVIEW_UNIT_ID
        or next_pending.get("review_unit_id")
        != "COVAPIE_BULK_REVIEW_UNIT_2557BFE1E3B5C4C5"
        or next_pending.get("ligand_component_ids") != ["F24"]
        or next_pending.get("event_count") != 4
        or next_pending.get("pdb_ids") != ["3V4X"]
    ):
        raise ValueError("EXPECTED_NEXT_PENDING_F24_INVALID")

    return {
        "check": "PASS",
        "exact4": exact4,
        "frozen_bindings": frozen,
        "architecture": architecture,
        "delegate_runtime_calls": calls,
        "generic_fact_thinness": thinness,
        "source_fact_counts": EXPECTED_SOURCE_FACT_COUNTS,
        "source_count": 11,
        "normalized_fact_count": 87,
        "event_collisions": 0,
        "ozj_prior": {
            "event_count": 4,
            "status": generic.CURRENTLY_UNREVIEWED,
            "calibration_eligible": True,
            "calibration_exclusion_reason": "",
            "transition_adapter": "NOT_CREATED",
        },
        "onl_adapter_left_ozj_unchanged": True,
        "review_summary": result.review_summary,
        "pending_event_count": result.review_summary["unreviewed_event_count"],
        "pending_unit_count": result.review_summary["unreviewed_unit_count"],
        "training_dispositions": dict(dispositions),
        "ozj_delta": {
            "normalized_include": 4,
            "normalized_exclude": 0,
            "formal_training_admission": 0,
        },
        "generic_protections": protections,
        "source_order_deterministic": True,
        "published_current_census": published["counts"],
        "global_census_update": "NOT_DONE",
        "future_census_informational_only": future,
        "next_pending_informational_only": {
            "ligand": "F24",
            "review_unit_id": next_pending["review_unit_id"],
            "event_count": 4,
            "pdb_ids": ("3V4X",),
        },
        "no_training_or_model_work": True,
        "ready_for_external_review": True,
        "ready_for_training": False,
        "feature_semantics": "AUDIT_REQUIRED_LATER",
        "step12d": "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    report = run_check_v1(args.repo_root)
    if report["ready_for_training"] is not False:
        raise ValueError("READY_FOR_TRAINING_MUST_BE_FALSE")
    print("check=" + report["check"])
    print("source_bindings=11")
    print("normalized_facts=87")
    print("completed_positive=87")
    print("pending=227")
    print("published_global_positive=100")
    print("future_global_positive=104_INFORMATIONAL_ONLY")
    print("next_pending=F24_INFORMATIONAL_ONLY")
    print("global_census_update=NOT_DONE")
    print("READY_FOR_TRAINING=false")
    print("feature_semantics=AUDIT_REQUIRED_LATER")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
