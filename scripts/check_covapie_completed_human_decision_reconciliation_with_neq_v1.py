#!/usr/bin/env python3
"""Repository-state-neutral checker for NEQ reconciliation successor V1."""

from __future__ import annotations

import argparse
import ast
from collections import Counter
import csv
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
import stat
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_v1 as generic,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_onl_v1 as onl_successor,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_neq_v1 as subject,
)
from covalent_ext import (  # noqa: E402
    covapie_neq_completed_decision_ingestion_and_task_label_availability_v1
    as neq_ingestion_owner,
)


EXACT4_PATHS = (
    "src/covalent_ext/"
    "covapie_completed_human_decision_reconciliation_with_neq_v1.py",
    "scripts/"
    "check_covapie_completed_human_decision_reconciliation_with_neq_v1.py",
    "tests/"
    "test_covapie_completed_human_decision_reconciliation_with_neq_v1.py",
    "docs/covapie_completed_human_decision_reconciliation_with_neq_v1_guide.md",
)
CURRENT_CENSUS_ROOT = (
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_yun_v1/"
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
        "YUN_RECONCILIATION_SUCCESSOR",
        "src/covalent_ext/"
        "covapie_completed_human_decision_reconciliation_with_yun_v1.py",
        11824,
        "84c6c57666ec96dfdb1f39a9dd87d097efff2eb000e6bf10281f29471540c287",
    ),
    (
        "NEQ_INGESTION_OWNER",
        "src/covalent_ext/"
        "covapie_neq_completed_decision_ingestion_and_task_label_availability_v1.py",
        96020,
        "dee80c8ce26e0be030d3063e8ab9831c1bc0650c6a2dc9798c3c21007faae290",
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
        "CURRENT_GLOBAL_CENSUS_WITH_YUN_OWNER",
        "src/covalent_ext/"
        "covapie_cumulative1000_current_global_readiness_census_with_yun_v1.py",
        62922,
        "c26608686cf293026a5a4f52de931fb2de169eb7462338656dd252abc5177624",
    ),
    (
        "CURRENT_GLOBAL_CENSUS_WITH_YUN_CSV",
        CURRENT_CENSUS_ROOT
        + "covapie_cumulative1000_current_global_readiness_census_with_yun_v1.csv",
        518137,
        "28eaa9833d69f191bf7eee91956588324ea1a3d145ebe5a99a31752a42e962e3",
    ),
    (
        "CURRENT_GLOBAL_CENSUS_WITH_YUN_SUMMARY",
        CURRENT_CENSUS_ROOT
        + "covapie_cumulative1000_current_global_readiness_summary_with_yun_v1.json",
        15391,
        "084d264f874547544a6b674cc1672298d2ac4eb08f61d139aa654f975d1c5767",
    ),
    (
        "CURRENT_GLOBAL_CENSUS_WITH_YUN_MANIFEST",
        CURRENT_CENSUS_ROOT
        + "covapie_cumulative1000_current_global_readiness_manifest_with_yun_v1.json",
        33503,
        "a4ee67e647dd87eee1021ad496567df4e3664f47a3951837bb9ba41a91e8e58e",
    ),
)
NEQ_FORMAL_RELATIVE = (
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "NEQ_COVAPIE_BULK_REVIEW_UNIT_0E0F340A9F98DA62/"
    "formal-human-decision-v1/neq_formal_human_decision_v1.json"
)
NEQ_FORMAL_BYTE_COUNT = 33908
NEQ_FORMAL_SHA256 = (
    "c5aa577f8b507b9bf6eb8d22207c8c11e3858ddd138c034d31d6f32d40b6c73c"
)
EXPECTED_PUBLIC_API = (
    "CompletedDecisionReconciliationWithNEQError",
    "project_neq_completed_decision_v1",
    "load_real_completed_decision_sources_with_neq_v1",
    "reconcile_real_completed_human_decisions_with_neq_v1",
)
EXPECTED_SOURCE_FACT_COUNTS = (8, 16, 8, 9, 8, 8, 8, 7, 6)
EXPECTED_REVIEW_SUMMARY = {
    "universe_event_count": 338,
    "universe_review_unit_count": 131,
    "completed_positive_event_count": 78,
    "completed_positive_unit_count": 9,
    "completed_negative_event_count": 24,
    "completed_negative_unit_count": 4,
    "completed_total_event_count": 102,
    "completed_total_unit_count": 13,
    "in_progress_event_count": 0,
    "in_progress_unit_count": 0,
    "unreviewed_event_count": 236,
    "unreviewed_unit_count": 118,
}
EXPECTED_NEXT_CENSUS_DERIVATION = {
    "chemistry_positive": 95,
    "chemistry_negative": 0,
    "chemistry_not_established": 86,
    "chemistry_unresolved": 819,
    "task_relevant": 96,
    "task_not_relevant": 86,
    "task_unresolved": 818,
    "training_include": 36,
    "training_exclude": 59,
    "training_not_applicable": 86,
    "training_unresolved": 819,
    "future_training_candidates": 19,
    "sample_pair_authority": 95,
    "sample_role_authority": 95,
    "strict_profile": 39,
    "direct_profile": 56,
    "task_A": 95,
    "task_B": 39,
    "task_B2": 39,
    "task_B3": 95,
    "task_C": 95,
    "current_runtime_model_usable": 17,
    "formal_training_admitted": 5,
    "ready_for_formal_training": 0,
    "missing_split_within_positive": 54,
    "missing_split_within_include": 11,
    "missing_tensor_within_positive": 54,
    "missing_tensor_within_include": 7,
    "missing_tensor_composition": (
        "G3H8",
        "ONL9",
        "PRF8",
        "2VS8",
        "1F8 8",
        "YUN7",
        "NEQ6",
    ),
    "all_missing_are_training_excluded_population": False,
    "pair_authority_absent_all": 905,
    "pair_authority_absent_within_positive": 0,
    "role_authority_absent_all": 905,
    "role_authority_absent_within_positive": 0,
    "human_training_exclusion_within_positive": 59,
    "missing_POST_training_authority": 78,
    "missing_POST_training_authority_within_include": 19,
    "missing_admission": 90,
    "missing_admission_within_include": 31,
    "feature_semantics_pending_positive": 95,
}
FORBIDDEN_SUFFIXES = (
    ".pt",
    ".ckpt",
    ".pth",
    ".pkl",
    ".lmdb",
    ".tar",
    ".zip",
    ".tgz",
    ".npz",
    ".pyc",
    ".tmp",
    ".part",
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


def verify_candidate_exact4_v1(repo_root: Path) -> dict[str, object]:
    """Verify the four portable NEQ reconciliation candidate files."""

    root = repo_root.resolve()
    artifacts: list[dict[str, object]] = []
    for relative in EXACT4_PATHS:
        path = root / relative
        payload = _read_regular_file(path, relative)
        _validate_text_payload(payload, relative)
        if len(payload) >= MAX_FILE_BYTES:
            raise ValueError("EXACT4_FILE_TOO_LARGE:" + relative)
        mode = stat.S_IMODE(path.stat().st_mode)
        expected_mode = 0o755 if relative.startswith("scripts/") else 0o644
        if mode != expected_mode:
            raise ValueError("EXACT4_MODE_INVALID:" + relative)
        artifacts.append(
            {
                "path": relative,
                "byte_count": len(payload),
                "line_count": len(payload.decode("utf-8").splitlines()),
                "sha256": _sha256(payload),
                "mode": f"{mode:04o}",
            }
        )
    return {"count": len(artifacts), "artifacts": tuple(artifacts)}


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
            root.parent / NEQ_FORMAL_RELATIVE,
            label="NEQ_FORMAL_HUMAN_DECISION",
            expected_byte_count=NEQ_FORMAL_BYTE_COUNT,
            expected_sha256=NEQ_FORMAL_SHA256,
        )
    )
    return {"count": len(artifacts), "artifacts": tuple(artifacts)}


def _verify_thin_successor_architecture(repo_root: Path) -> dict[str, object]:
    path = repo_root.resolve() / EXACT4_PATHS[0]
    tree = ast.parse(_read_regular_file(path, "NEQ_SUCCESSOR"))
    if subject.__all__ != EXPECTED_PUBLIC_API:
        raise ValueError("PUBLIC_API_NOT_MINIMAL_EXACT4")
    if subject.NEQ_TRANSITION_ADAPTER_CREATED is not False:
        raise ValueError("NEQ_TRANSITION_ADAPTER_FLAG_INVALID")
    function_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    if any(
        name.lower().startswith("_adapt_neq")
        or ("neq" in name.lower() and "transition" in name.lower())
        for name in function_names
    ):
        raise ValueError("NEQ_TRANSITION_HELPER_CREATED")
    forbidden_classes = {
        "SourceBinding",
        "NormalizedCompletedDecisionFact",
        "NormalizedDecisionSource",
        "ReconciliationResult",
    }
    class_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
    }
    if class_names & forbidden_classes:
        raise ValueError("GENERIC_DATACLASS_DUPLICATED")
    history_names = {
        "row",
        "rows",
        "historical",
        "historical_rows",
        "adapted_historical",
        "working",
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
        raise ValueError("NEQ_HISTORY_REWRITE_IMPLEMENTED")
    called = [
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    ]
    expected_once = (
        "load_real_historical_reconciliation_v1",
        "_adapt_onl_in_progress_completion_for_generic_reconciliation_v1",
        "load_real_completed_decision_sources_with_yun_v1",
        "reconcile_completed_human_decisions_v1",
    )
    if any(called.count(name) != 1 for name in expected_once):
        raise ValueError("THIN_SUCCESSOR_DELEGATE_AST_COUNTS_INVALID")
    if "reconcile_real_completed_human_decisions_with_yun_v1" in called:
        raise ValueError("YUN_RESULT_SECOND_RECONCILIATION_FORBIDDEN")
    return {
        "public_api": subject.__all__,
        "neq_transition_adapter_created": False,
        "onl_adapter_ast_call_count": called.count(expected_once[1]),
        "generic_reconciler_ast_call_count": called.count(expected_once[3]),
    }


def _published_census_state(repo_root: Path) -> dict[str, object]:
    root = repo_root.resolve()
    csv_path = root / FROZEN_REPOSITORY_FILES[6][1]
    payload = _read_regular_file(csv_path, "PUBLISHED_CURRENT_GLOBAL_CENSUS_WITH_YUN")
    try:
        rows = tuple(
            csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
        )
    except (UnicodeDecodeError, csv.Error) as error:
        raise ValueError("PUBLISHED_CURRENT_GLOBAL_CENSUS_PARSE_FAILED") from error
    if len(rows) != 1000:
        raise ValueError("PUBLISHED_CURRENT_GLOBAL_CENSUS_NOT_EXACT1000")
    neq_ids = set(subject._NEQ_EVENT_IDS)
    neq_rows = [row for row in rows if row.get("canonical_event_id") in neq_ids]
    if len(neq_rows) != 6 or any(
        row.get("review_unit_id") != subject._NEQ_REVIEW_UNIT_ID
        or row.get("current_review_status") != generic.CURRENTLY_UNREVIEWED
        or row.get("chemistry_disposition") != "UNRESOLVED"
        or row.get("task_relevance_disposition") != "UNRESOLVED"
        or row.get("training_use_disposition") != "UNRESOLVED"
        for row in neq_rows
    ):
        raise ValueError("PUBLISHED_CURRENT_CENSUS_NEQ_STATE_INVALID")
    summary_path = root / FROZEN_REPOSITORY_FILES[7][1]
    try:
        summary = json.loads(
            _read_regular_file(
                summary_path, "PUBLISHED_CURRENT_GLOBAL_CENSUS_SUMMARY_WITH_YUN"
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError("PUBLISHED_CURRENT_GLOBAL_SUMMARY_PARSE_FAILED") from error
    state = {
        "positive": sum(
            row.get("chemistry_disposition") == generic.CHEMISTRY_POSITIVE
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
    }
    if state != {
        "positive": 89,
        "training_include": 36,
        "training_exclude": 53,
        "future_candidates": 19,
    }:
        raise ValueError("PUBLISHED_CURRENT_GLOBAL_COUNTS_INVALID")
    return {"counts": state, "summary": summary}


def _verify_next_census_derivation(
    source: generic.NormalizedDecisionSource,
    published: dict[str, object],
) -> dict[str, object]:
    """Derive informational next values without materializing census output."""

    summary = published["summary"]
    if type(summary) is not dict:
        raise ValueError("PUBLISHED_CURRENT_GLOBAL_SUMMARY_INVALID")
    try:
        chemistry = summary["chemistry"]
        task = summary["task_relevance"]
        training = summary["training_use"]
        stage = summary["training_stage"]
        pair = summary["reactive_pair"]
        role = summary["role"]
        exact5 = summary["canonical_exact5"]
        blockers = summary["blockers"]
    except (KeyError, TypeError) as error:
        raise ValueError("PUBLISHED_CURRENT_DERIVATION_INPUT_INVALID") from error
    delta = len(source.facts)
    if delta != 6 or any(
        fact.training_disposition != generic.TRAINING_EXCLUDE
        or fact.task_relevance_disposition != generic.TASK_RELEVANT
        or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
        or fact.human_training_excluded is not True
        for fact in source.facts
    ):
        raise ValueError("NEQ_INFORMATIONAL_DELTA_INPUT_INVALID")
    missing_tensor = blockers["missing_tensor_integration"]
    observed = {
        "chemistry_positive": chemistry["POSITIVE"]["count"] + delta,
        "chemistry_negative": chemistry["NEGATIVE"]["count"],
        "chemistry_not_established": chemistry["NOT_ESTABLISHED"]["count"],
        "chemistry_unresolved": chemistry["UNRESOLVED"]["count"] - delta,
        "task_relevant": task["RELEVANT"]["count"] + delta,
        "task_not_relevant": task["NOT_RELEVANT"]["count"],
        "task_unresolved": task["UNRESOLVED"]["count"] - delta,
        "training_include": training["INCLUDE"]["count"],
        "training_exclude": training["EXCLUDE_FROM_TRAINING_ONLY"]["count"]
        + delta,
        "training_not_applicable": training["NOT_APPLICABLE"]["count"],
        "training_unresolved": training["UNRESOLVED"]["count"] - delta,
        "future_training_candidates": stage[
            "future_training_admission_candidate_count"
        ],
        "sample_pair_authority": pair["sample_level_authoritative_pair_count"]
        + delta,
        "sample_role_authority": role[
            "role_partition_sample_authoritative_count"
        ]
        + delta,
        "strict_profile": role["role_profile_counts"]["STRICT_LINKER_PRESENT_V1"],
        "direct_profile": role["role_profile_counts"][
            "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
        ]
        + delta,
        "task_A": exact5["tasks"][0][
            "structurally_applicable_authoritative_role_count"
        ]
        + delta,
        "task_B": exact5["tasks"][1][
            "structurally_applicable_authoritative_role_count"
        ],
        "task_B2": exact5["tasks"][2][
            "structurally_applicable_authoritative_role_count"
        ],
        "task_B3": exact5["tasks"][3][
            "structurally_applicable_authoritative_role_count"
        ]
        + delta,
        "task_C": exact5["tasks"][4][
            "structurally_applicable_authoritative_role_count"
        ]
        + delta,
        "current_runtime_model_usable": stage[
            "current_runtime_model_usable_count"
        ],
        "formal_training_admitted": stage["formal_training_admitted_count"],
        "ready_for_formal_training": stage[
            "ready_for_formal_training_event_count"
        ],
        "missing_split_within_positive": blockers["missing_split_authority"][
            "within_positive_89"
        ]
        + delta,
        "missing_split_within_include": blockers["missing_split_authority"][
            "within_include_36"
        ],
        "missing_tensor_within_positive": missing_tensor["within_positive_89"]
        + delta,
        "missing_tensor_within_include": missing_tensor["within_include_36"],
        "missing_tensor_composition": (
            "G3H8",
            "ONL9",
            "PRF8",
            "2VS8",
            "1F8 8",
            "YUN7",
            "NEQ6",
        ),
        "all_missing_are_training_excluded_population": missing_tensor[
            "all_missing_are_training_excluded_population"
        ],
        "pair_authority_absent_all": blockers["pair_authority_absent"][
            "all_1000"
        ]
        - delta,
        "pair_authority_absent_within_positive": 0,
        "role_authority_absent_all": blockers["role_authority_absent"][
            "all_1000"
        ]
        - delta,
        "role_authority_absent_within_positive": 0,
        "human_training_exclusion_within_positive": blockers[
            "human_training_exclusion"
        ]["within_positive_89"]
        + delta,
        "missing_POST_training_authority": blockers[
            "missing_POST_training_authority"
        ]["within_positive_89"]
        + delta,
        "missing_POST_training_authority_within_include": blockers[
            "missing_POST_training_authority"
        ]["within_include_36"],
        "missing_admission": blockers["missing_training_admission"][
            "within_positive_89"
        ]
        + delta,
        "missing_admission_within_include": blockers[
            "missing_training_admission"
        ]["within_include_36"],
        "feature_semantics_pending_positive": blockers[
            "feature_semantics_pending"
        ]["within_positive_89"]
        + delta,
    }
    if observed != EXPECTED_NEXT_CENSUS_DERIVATION:
        raise ValueError("EXPECTED_NEXT_CENSUS_DERIVATION_INVALID")
    return observed


def _run_production_pipeline_counted(
    repo_root: Path,
) -> tuple[
    generic.ReconciliationResult,
    dict[str, int],
    tuple[dict[str, str], ...],
    tuple[dict[str, str], ...],
]:
    """Run the public production path and count its two delegates."""

    original_onl = (
        onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1
    )
    original_generic = generic.reconcile_completed_human_decisions_v1
    calls: Counter[str] = Counter()
    captured_original: tuple[dict[str, str], ...] = ()
    captured_adapted: tuple[dict[str, str], ...] = ()

    def counted_onl(rows: object) -> tuple[dict[str, str], ...]:
        nonlocal captured_original, captured_adapted
        calls["onl_adapter"] += 1
        captured_original = tuple(dict(row) for row in rows)  # type: ignore[arg-type]
        captured_adapted = original_onl(rows)  # type: ignore[arg-type]
        return captured_adapted

    def counted_generic(rows: object, sources: object) -> generic.ReconciliationResult:
        calls["generic_reconciler"] += 1
        return original_generic(rows, sources)  # type: ignore[arg-type]

    subject.onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1 = (
        counted_onl
    )
    subject.generic.reconcile_completed_human_decisions_v1 = counted_generic
    try:
        result = subject.reconcile_real_completed_human_decisions_with_neq_v1(
            repo_root
        )
    finally:
        subject.onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1 = (
            original_onl
        )
        subject.generic.reconcile_completed_human_decisions_v1 = original_generic
    if calls != Counter({"onl_adapter": 1, "generic_reconciler": 1}):
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


def _expect_generic_failure(
    rows: object, sources: object, expected_token: str
) -> None:
    try:
        generic.reconcile_completed_human_decisions_v1(rows, sources)  # type: ignore[arg-type]
    except generic.CompletedDecisionReconciliationError as error:
        if expected_token not in str(error):
            raise ValueError("GENERIC_FAILURE_TOKEN_INVALID:" + str(error)) from error
    else:
        raise ValueError("GENERIC_FAILURE_NOT_RAISED:" + expected_token)


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
    facts = tuple(
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
    )
    return generic.NormalizedDecisionSource(binding=binding, facts=facts)


def _verify_generic_protections(
    historical: tuple[dict[str, str], ...],
    adapted: tuple[dict[str, str], ...],
    sources: tuple[generic.NormalizedDecisionSource, ...],
) -> dict[str, bool]:
    neq_ids = set(subject._NEQ_EVENT_IDS)
    for status in (
        generic.CURRENTLY_IN_PROGRESS,
        generic.COMPLETED_HUMAN_POSITIVE,
    ):
        drifted = [dict(row) for row in adapted]
        for row in drifted:
            if row["canonical_event_id"] in neq_ids:
                _set_status(row, status)
        _expect_generic_failure(
            drifted, sources, "PRIOR_REVIEW_STATUS_NOT_UNREVIEWED"
        )
    mixed = [dict(row) for row in adapted]
    row = next(row for row in mixed if row["canonical_event_id"] in neq_ids)
    _set_status(row, generic.CURRENTLY_IN_PROGRESS)
    _expect_generic_failure(mixed, sources, "HISTORICAL_REVIEW_UNIT_STATUS_MIXED")
    _expect_generic_failure(
        historical, sources, "PRIOR_REVIEW_STATUS_NOT_UNREVIEWED"
    )

    row1 = _synthetic_row("event-1", "unit-1")
    source1 = _synthetic_source("source-1.json", "unit-1", ("event-1",))
    source2 = _synthetic_source("source-2.json", "unit-1", ("event-1",))
    _expect_generic_failure(
        (row1,), (source1, source2), "CROSS_SOURCE_EVENT_COLLISION"
    )
    _expect_generic_failure(
        (row1,), (source1, source1), "SOURCE_BINDING_DUPLICATE"
    )
    rows2 = (
        _synthetic_row("event-1", "unit-1", 2),
        _synthetic_row("event-2", "unit-1", 2),
    )
    _expect_generic_failure(
        rows2, (source1,), "SOURCE_REVIEW_UNIT_EVENT_SET_MISMATCH"
    )
    outside = _synthetic_source("outside.json", "unit-1", ("outside",))
    _expect_generic_failure(
        (row1,), (outside,), "EVENT_NOT_IN_HISTORICAL_UNIVERSE"
    )
    mismatch_row = _synthetic_row("event-1", "unit-other")
    _expect_generic_failure(
        (mismatch_row,), (source1,), "FACT_HISTORICAL_REVIEW_UNIT_MISMATCH"
    )
    non_unreviewed = _synthetic_row("event-1", "unit-1")
    _set_status(non_unreviewed, generic.COMPLETED_HUMAN_POSITIVE)
    _expect_generic_failure(
        (non_unreviewed,), (source1,), "PRIOR_REVIEW_STATUS_NOT_UNREVIEWED"
    )
    return {
        "whole_neq_in_progress_rejected": True,
        "whole_neq_completed_rejected": True,
        "one_neq_mixed_status_rejected": True,
        "original_onl_prior_rejected": True,
        "cross_source_collision_rejected": True,
        "duplicate_binding_rejected": True,
        "incomplete_unit_coverage_rejected": True,
        "outside_historical_universe_rejected": True,
        "historical_unit_mismatch_rejected": True,
        "non_unreviewed_prior_rejected": True,
    }


def run_check_v1(repo_root: Path) -> dict[str, object]:
    """Run all read-only NEQ reconciliation checks and return evidence."""

    root = repo_root.resolve()
    exact4 = verify_candidate_exact4_v1(root)
    frozen = _verify_frozen_inputs(root)
    architecture = _verify_thin_successor_architecture(root)

    source = subject.project_neq_completed_decision_v1(repo_root=root)
    if (
        type(source) is not generic.NormalizedDecisionSource
        or tuple(fact.canonical_event_id for fact in source.facts)
        != subject._NEQ_EVENT_IDS
        or len(source.facts) != 6
        or any(
            fact.task_relevance_disposition != generic.TASK_RELEVANT
            or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
            or fact.training_disposition != generic.TRAINING_EXCLUDE
            or fact.human_training_excluded is not True
            for fact in source.facts
        )
    ):
        raise ValueError("NEQ_SOURCE_PROJECTION_INVALID")
    bound = neq_ingestion_owner.load_frozen_formal_decision_v1(root)
    normalized_events = bound.get("normalized", {}).get("events", [])  # type: ignore[union-attr]
    if len(normalized_events) != 6 or any(
        event.get("decision_finalized") is not True
        or event.get("training_admitted") is not False
        for event in normalized_events
    ):
        raise ValueError("NEQ_OWNER_VALIDATED_ADMISSION_STATE_INVALID")

    historical = generic.load_real_historical_reconciliation_v1(root)
    subject._prove_neq_original_unreviewed_prior_v1(historical)
    neq_ids = set(subject._NEQ_EVENT_IDS)
    original_neq = {
        row["canonical_event_id"]: row
        for row in historical
        if row["canonical_event_id"] in neq_ids
    }
    if len(original_neq) != 6:
        raise ValueError("NEQ_ORIGINAL_PRIOR_NOT_EXACT6")

    result, calls, captured_original, captured_adapted = (
        _run_production_pipeline_counted(root)
    )
    subject._prove_neq_rows_unchanged_after_onl_normalization_v1(
        captured_original, captured_adapted
    )
    captured_original_neq = {
        row["canonical_event_id"]: row
        for row in captured_original
        if row["canonical_event_id"] in neq_ids
    }
    captured_adapted_neq = {
        row["canonical_event_id"]: row
        for row in captured_adapted
        if row["canonical_event_id"] in neq_ids
    }
    if captured_original_neq != captured_adapted_neq:
        raise ValueError("ONL_ADAPTER_CHANGED_NEQ_ROWS")

    sources = subject.load_real_completed_decision_sources_with_neq_v1(root)
    if (
        len(sources) != 9
        or tuple(len(item.facts) for item in sources)
        != EXPECTED_SOURCE_FACT_COUNTS
        or len({item.binding.stable_identity for item in sources}) != 9
        or len({item.binding.review_unit_id for item in sources}) != 9
        or len(
            {
                fact.canonical_event_id
                for item in sources
                for fact in item.facts
            }
        )
        != 78
    ):
        raise ValueError("EXACT9_SOURCE_COMPOSITION_INVALID")
    if result.review_summary != EXPECTED_REVIEW_SUMMARY:
        raise ValueError("RECONCILIATION_SUMMARY_INVALID")
    if len(result.source_bindings) != 9 or len(result.normalized_facts) != 78:
        raise ValueError("RECONCILIATION_BINDING_OR_FACT_COUNT_INVALID")

    dispositions = Counter(
        fact.training_disposition for fact in result.normalized_facts
    )
    if dispositions != Counter(
        {generic.TRAINING_INCLUDE: 19, generic.TRAINING_EXCLUDE: 59}
    ):
        raise ValueError("NORMALIZED_TRAINING_DISPOSITIONS_INVALID")
    final_neq = {
        row["canonical_event_id"]: row
        for row in result.reconciled_rows
        if row["canonical_event_id"] in neq_ids
    }
    expected_authority = json.dumps(
        [source.binding.source_path], separators=(",", ":"), sort_keys=True
    )
    if len(final_neq) != 6 or any(
        row["raw_review_unit_id"] != subject._NEQ_REVIEW_UNIT_ID
        or row["current_review_status"] != generic.COMPLETED_HUMAN_POSITIVE
        or row["calibration_eligible"] != "false"
        or row["calibration_exclusion_reason"]
        != generic.COMPLETED_HUMAN_POSITIVE
        or row["current_status_authority_sources_json"] != expected_authority
        for row in final_neq.values()
    ):
        raise ValueError("FINAL_NEQ_RECONCILED_ROWS_INVALID")

    delta = {
        "completed_positive": result.review_summary[
            "completed_positive_event_count"
        ]
        - 72,
        "completed_total": result.review_summary["completed_total_event_count"]
        - 96,
        "unreviewed": result.review_summary["unreviewed_event_count"] - 242,
        "pending": result.review_summary["unreviewed_event_count"] - 242,
        "pending_units": result.review_summary["unreviewed_unit_count"] - 119,
        "normalized_include": dispositions[generic.TRAINING_INCLUDE] - 19,
        "normalized_exclude": dispositions[generic.TRAINING_EXCLUDE] - 53,
        "training_admission": sum(
            event.get("training_admitted") is True for event in normalized_events
        ),
    }
    if delta != {
        "completed_positive": 6,
        "completed_total": 6,
        "unreviewed": -6,
        "pending": -6,
        "pending_units": -1,
        "normalized_include": 0,
        "normalized_exclude": 6,
        "training_admission": 0,
    }:
        raise ValueError("EXACT_NEQ_DELTA_INVALID")

    adapted = tuple(dict(row) for row in captured_adapted)
    normal = generic.reconcile_completed_human_decisions_v1(adapted, sources)
    reversed_result = generic.reconcile_completed_human_decisions_v1(
        adapted, tuple(reversed(sources))
    )
    if normal != reversed_result or normal != result:
        raise ValueError("SOURCE_ORDER_NOT_DETERMINISTIC")
    protections = _verify_generic_protections(historical, adapted, sources)

    published = _published_census_state(root)
    next_census = _verify_next_census_derivation(source, published)
    summary = published["summary"]
    next_pending = summary["top_pending_review_units_by_event_yield"][1]  # type: ignore[index]
    if (
        next_pending.get("review_unit_id")
        != "COVAPIE_BULK_REVIEW_UNIT_BCA0E7B8C2B33410"
        or next_pending.get("ligand_component_ids") != ["CHT"]
        or next_pending.get("event_count") != 5
        or next_pending.get("pdb_ids") != ["4V3F", "5A2D"]
    ):
        raise ValueError("EXPECTED_NEXT_PENDING_HEAD_INVALID")

    return {
        "check": "PASS",
        "exact4": exact4,
        "frozen_bindings": frozen,
        "architecture": architecture,
        "neq_projection": {
            "event_count": 6,
            "task_relevance": generic.TASK_RELEVANT,
            "chemistry": generic.CHEMISTRY_POSITIVE,
            "training_disposition": generic.TRAINING_EXCLUDE,
            "human_training_excluded": True,
            "training_admitted": False,
            "formal_authority": source.binding.source_path,
        },
        "original_prior": {
            "event_count": 6,
            "status": generic.CURRENTLY_UNREVIEWED,
            "calibration_eligible": True,
            "neq_transition_adapter": "NOT_CREATED",
        },
        "delegate_runtime_calls": calls,
        "onl_adapter_left_neq_unchanged": True,
        "source_fact_counts": EXPECTED_SOURCE_FACT_COUNTS,
        "review_summary": result.review_summary,
        "training_dispositions": dict(dispositions),
        "neq_delta": delta,
        "generic_protections": protections,
        "source_order_deterministic": True,
        "published_current_census": published["counts"],
        "global_census_update": "NOT_DONE",
        "expected_next_census_informational_only": next_census,
        "expected_next_pending_informational_only": {
            "review_unit_id": next_pending["review_unit_id"],
            "ligand": "CHT",
            "event_count": 5,
            "pdb_ids": ("4V3F", "5A2D"),
        },
        "ready_for_current_global_census_refresh": True,
        "ready_for_training": False,
        "feature_semantics": "AUDIT_REQUIRED_LATER",
        "step12d": "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    report = run_check_v1(args.repo_root)
    print("check=" + report["check"])
    print("source_bindings=9")
    print("normalized_facts=78")
    print("completed_positive=78")
    print("pending=236")
    print("published_global_positive=89")
    print("expected_next_global_positive=95_INFORMATIONAL_ONLY")
    print("global_census_update=NOT_DONE")
    print("READY_FOR_TRAINING=false")
    print("feature_semantics=AUDIT_REQUIRED_LATER")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
