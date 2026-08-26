#!/usr/bin/env python3
"""Repository-state-neutral checker for 2VS reconciliation successor V1."""

from __future__ import annotations

import argparse
import ast
from collections import Counter
import csv
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
    covapie_completed_human_decision_reconciliation_with_2vs_v1 as subject,
)
from covalent_ext import (  # noqa: E402
    covapie_2vs_completed_decision_ingestion_and_task_label_availability_v1
    as two_vs_ingestion_owner,
)


EXACT4_PATHS = (
    "src/covalent_ext/"
    "covapie_completed_human_decision_reconciliation_with_2vs_v1.py",
    "scripts/"
    "check_covapie_completed_human_decision_reconciliation_with_2vs_v1.py",
    "tests/"
    "test_covapie_completed_human_decision_reconciliation_with_2vs_v1.py",
    "docs/covapie_completed_human_decision_reconciliation_with_2vs_v1_guide.md",
)
FROZEN_REPOSITORY_FILES = (
    (
        "GENERIC_RECONCILIATION_PREDECESSOR",
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
        "PRF_RECONCILIATION_SUCCESSOR",
        "src/covalent_ext/"
        "covapie_completed_human_decision_reconciliation_with_prf_v1.py",
        11728,
        "ce4db4fcbf909852a6fca1a919ee50750279a8a6ca0968d4b33ae8f510bd0f74",
    ),
    (
        "2VS_INGESTION_OWNER",
        "src/covalent_ext/"
        "covapie_2vs_completed_decision_ingestion_and_task_label_availability_v1.py",
        79775,
        "8812b4f9d0c77af4228b6f71ec9183867fec778311b290f8362a1164081e1409",
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
TWO_VS_FORMAL_RELATIVE = (
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "2VS_COVAPIE_BULK_REVIEW_UNIT_5834329D9E2A1F22/"
    "formal-human-decision-v1/2vs_formal_human_decision_v1.json"
)
TWO_VS_FORMAL_BYTE_COUNT = 28640
TWO_VS_FORMAL_SHA256 = (
    "49f33bb2a21669ddb7ab8e98cfa710380e031b280855d5f3ebe6796cde2d06aa"
)
CURRENT_CENSUS_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_prf_v1/"
    "covapie_cumulative1000_current_global_readiness_census_with_prf_v1.csv"
)
CURRENT_CENSUS_BYTE_COUNT = 506220
CURRENT_CENSUS_SHA256 = (
    "a707cb60c8f788f9ad0e94e89c4038226cfa5f94c15b0afcfa6e36adca3c1b12"
)
CURRENT_CENSUS_SUMMARY_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_prf_v1/"
    "covapie_cumulative1000_current_global_readiness_summary_with_prf_v1.json"
)
CURRENT_CENSUS_SUMMARY_BYTE_COUNT = 14742
CURRENT_CENSUS_SUMMARY_SHA256 = (
    "82d4d36beb21efb2a588beaea9d3b9c61a6275596482e39ff45341e4cbe316f7"
)
EXPECTED_PUBLIC_API = (
    "CompletedDecisionReconciliationWith2VSError",
    "project_2vs_completed_decision_v1",
    "load_real_completed_decision_sources_with_2vs_v1",
    "reconcile_real_completed_human_decisions_with_2vs_v1",
)
EXPECTED_2VS_EVENT_IDS = (
    "COVAPIE_CYS_SG_EVENT_V1:4NPI:A:CYS:302-:SG:G:2VS:CA6",
    "COVAPIE_CYS_SG_EVENT_V1:4NPI:B:CYS:302-:SG:J:2VS:CA6",
    "COVAPIE_CYS_SG_EVENT_V1:4NPI:C:CYS:302-:SG:M:2VS:CA6",
    "COVAPIE_CYS_SG_EVENT_V1:4NPI:D:CYS:302-:SG:P:2VS:CA6",
    "COVAPIE_CYS_SG_EVENT_V1:4OUB:A:CYS:302-:SG:G:2VS:CA6",
    "COVAPIE_CYS_SG_EVENT_V1:4OUB:B:CYS:302-:SG:J:2VS:CA6",
    "COVAPIE_CYS_SG_EVENT_V1:4OUB:C:CYS:302-:SG:M:2VS:CA6",
    "COVAPIE_CYS_SG_EVENT_V1:4OUB:D:CYS:302-:SG:P:2VS:CA6",
)
EXPECTED_CANONICAL_TASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
EXPECTED_NEXT_CENSUS_DERIVATION = {
    "chemistry_positive": 74,
    "chemistry_unresolved": 840,
    "task_relevant": 75,
    "task_unresolved": 839,
    "training_include": 29,
    "training_exclude": 45,
    "training_unresolved": 840,
    "completed_human_positive": 57,
    "currently_unreviewed": 257,
    "sample_pair_authority": 74,
    "sample_role_authority": 74,
    "strict_profile": 31,
    "direct_profile": 43,
    "task_A": 74,
    "task_B": 31,
    "task_B2": 31,
    "task_B3": 74,
    "task_C": 74,
    "missing_split_within_positive": 33,
    "missing_tensor_within_positive": 33,
    "missing_tensor_composition": ("G3H8", "ONL9", "PRF8", "2VS8"),
    "missing_POST_training_authority": 57,
    "missing_admission": 69,
    "feature_semantics_pending_positive": 74,
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
MAX_CANDIDATE_BYTES = 1024 * 1024


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_regular_file(path: Path, label: str) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise ValueError("NOT_REGULAR_FILE:" + label)
    try:
        return path.read_bytes()
    except OSError as error:
        raise ValueError("READ_FAILED:" + label) from error


def _verify_frozen_file(
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
    """Verify exactly the four portable 2VS reconciliation candidate paths."""

    root = repo_root.resolve()
    matching = {
        path.relative_to(root).as_posix()
        for path in root.rglob(
            "*covapie_completed_human_decision_reconciliation_with_2vs_v1*"
        )
        if path.is_file()
    }
    if matching != set(EXACT4_PATHS):
        raise ValueError("2VS_RECONCILIATION_CANDIDATE_INVENTORY_NOT_EXACT4")

    bindings: list[dict[str, object]] = []
    total_bytes = 0
    for relative in EXACT4_PATHS:
        path = root / relative
        payload = _read_regular_file(path, "EXACT4:" + relative)
        _validate_text_payload(payload, relative)
        mode = stat.S_IMODE(path.stat().st_mode)
        if mode != 0o644:
            raise ValueError("EXACT4_MODE_NOT_0644:" + relative)
        if path.name.endswith(FORBIDDEN_SUFFIXES):
            raise ValueError("EXACT4_FORBIDDEN_SUFFIX:" + relative)
        total_bytes += len(payload)
        bindings.append(
            {
                "path": relative,
                "byte_count": len(payload),
                "sha256": _sha256(payload),
                "mode": "0644",
            }
        )
    if total_bytes >= MAX_CANDIDATE_BYTES:
        raise ValueError("EXACT4_TOTAL_BYTES_NOT_BELOW_1_MIB")
    return {
        "candidate_file_count": len(bindings),
        "candidate_total_bytes": total_bytes,
        "candidate_file_bindings": bindings,
    }


def _verify_frozen_inputs(repo_root: Path) -> dict[str, object]:
    root = repo_root.resolve()
    bindings = [
        _verify_frozen_file(
            root / relative,
            label=label,
            expected_byte_count=byte_count,
            expected_sha256=sha256,
        )
        for label, relative, byte_count, sha256 in FROZEN_REPOSITORY_FILES
    ]
    bindings.extend(
        (
            _verify_frozen_file(
                root.parent / TWO_VS_FORMAL_RELATIVE,
                label="2VS_FORMAL_HUMAN_DECISION",
                expected_byte_count=TWO_VS_FORMAL_BYTE_COUNT,
                expected_sha256=TWO_VS_FORMAL_SHA256,
            ),
            _verify_frozen_file(
                root / CURRENT_CENSUS_RELATIVE,
                label="PUBLISHED_CURRENT_GLOBAL_CENSUS_WITH_PRF",
                expected_byte_count=CURRENT_CENSUS_BYTE_COUNT,
                expected_sha256=CURRENT_CENSUS_SHA256,
            ),
            _verify_frozen_file(
                root / CURRENT_CENSUS_SUMMARY_RELATIVE,
                label="PUBLISHED_CURRENT_GLOBAL_CENSUS_SUMMARY_WITH_PRF",
                expected_byte_count=CURRENT_CENSUS_SUMMARY_BYTE_COUNT,
                expected_sha256=CURRENT_CENSUS_SUMMARY_SHA256,
            ),
        )
    )
    return {"frozen_input_bindings": bindings}


def _verify_thin_successor_architecture(repo_root: Path) -> dict[str, object]:
    module_path = repo_root.resolve() / EXACT4_PATHS[0]
    tree = ast.parse(_read_regular_file(module_path, "SUCCESSOR_MODULE"))
    allowed_imports = {
        "__future__",
        "collections",
        "collections.abc",
        "pathlib",
        "typing",
    }
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 1:
                continue
            imported_modules.add(node.module or "")
    if not imported_modules <= allowed_imports:
        raise ValueError("SUCCESSOR_IMPORT_BOUNDARY_INVALID")

    class_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
    }
    if class_names != {"CompletedDecisionReconciliationWith2VSError"}:
        raise ValueError("SUCCESSOR_NEW_DATA_CLASS_OR_CLASS_INVALID")
    function_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    if any(
        name.lower().startswith("_adapt_2vs")
        or ("2vs" in name.lower() and "transition" in name.lower())
        for name in function_names
    ):
        raise ValueError("2VS_TRANSITION_ADAPTER_CREATED")
    if subject.TWO_VS_TRANSITION_ADAPTER_CREATED is not False:
        raise ValueError("2VS_TRANSITION_ADAPTER_FLAG_INVALID")
    if any(
        isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign))
        and any(
            isinstance(target, ast.Subscript)
            for target in (
                node.targets
                if isinstance(node, ast.Assign)
                else (node.target,)
            )
        )
        for node in ast.walk(tree)
    ):
        raise ValueError("2VS_ROW_STATE_MUTATION_LOGIC_CREATED")

    forbidden_calls = {
        "open",
        "mkdir",
        "touch",
        "unlink",
        "rename",
        "replace",
        "write_bytes",
        "write_text",
    }
    called_names: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            called_names.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            called_names.append(node.func.attr)
    if set(called_names) & forbidden_calls:
        raise ValueError("SUCCESSOR_MATERIALIZATION_CALL_FORBIDDEN")
    required_delegations = {
        "load_frozen_formal_decision_v1",
        "load_real_completed_decision_sources_with_prf_v1",
        "load_real_historical_reconciliation_v1",
        "_adapt_onl_in_progress_completion_for_generic_reconciliation_v1",
        "reconcile_completed_human_decisions_v1",
    }
    if not required_delegations <= set(called_names):
        raise ValueError("SUCCESSOR_REQUIRED_DELEGATION_MISSING")
    if called_names.count(
        "_adapt_onl_in_progress_completion_for_generic_reconciliation_v1"
    ) != 1:
        raise ValueError("ONL_TRANSITION_OWNER_NOT_REUSED_EXACTLY_ONCE")
    if "reconcile_real_completed_human_decisions_with_prf_v1" in called_names:
        raise ValueError("PRF_RECONCILED_ROWS_REUSED_AS_INPUT")
    if tuple(subject.__all__) != EXPECTED_PUBLIC_API:
        raise ValueError("SUCCESSOR_PUBLIC_API_INVALID")
    return {
        "generic_predecessor_types_reused": True,
        "generic_reconciliation_engine_reused": True,
        "prf_exact5_source_loader_reused": True,
        "onl_transition_owner_reused_exactly_once": True,
        "two_vs_ingestion_owner_reused": True,
        "two_vs_transition_adapter_created": False,
        "new_normalized_data_classes_created": 0,
        "materialization_calls_created": 0,
        "model_or_training_imports_created": 0,
    }


def _published_positive_count(repo_root: Path) -> int:
    payload = _read_regular_file(
        repo_root.resolve() / CURRENT_CENSUS_RELATIVE,
        "PUBLISHED_CURRENT_GLOBAL_CENSUS_WITH_PRF",
    )
    try:
        text = payload.decode("utf-8")
        rows = tuple(csv.DictReader(io.StringIO(text, newline="")))
    except (UnicodeDecodeError, csv.Error) as error:
        raise ValueError("PUBLISHED_CURRENT_GLOBAL_CENSUS_PARSE_FAILED") from error
    if len(rows) != 1000:
        raise ValueError("PUBLISHED_CURRENT_GLOBAL_CENSUS_NOT_EXACT1000")
    return sum(row.get("chemistry_disposition") == "POSITIVE" for row in rows)


def _set_status(row: dict[str, str], status: str) -> None:
    row["current_review_status"] = status
    row["calibration_eligible"] = (
        "true" if status == generic.CURRENTLY_UNREVIEWED else "false"
    )
    row["calibration_exclusion_reason"] = (
        "" if status == generic.CURRENTLY_UNREVIEWED else status
    )


def run_check_v1(repo_root: Path) -> dict[str, object]:
    """Execute frozen identity, 2VS prior, delegation, and census gates."""

    root = repo_root.resolve()
    candidate = verify_candidate_exact4_v1(root)
    frozen = _verify_frozen_inputs(root)
    architecture = _verify_thin_successor_architecture(root)

    source = subject.project_2vs_completed_decision_v1(repo_root=root)
    if (
        type(source) is not generic.NormalizedDecisionSource
        or type(source.binding) is not generic.SourceBinding
        or any(
            type(fact) is not generic.NormalizedCompletedDecisionFact
            for fact in source.facts
        )
    ):
        raise ValueError("GENERIC_NORMALIZED_TYPES_NOT_REUSED")
    if tuple(fact.canonical_event_id for fact in source.facts) != (
        EXPECTED_2VS_EVENT_IDS
    ):
        raise ValueError("2VS_NORMALIZED_EVENT_IDS_NOT_EXACT8")
    if any(
        fact.human_review_completed is not True
        or fact.legacy_completed_review_status
        != generic.COMPLETED_HUMAN_POSITIVE
        or fact.task_relevance_disposition != generic.TASK_RELEVANT
        or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
        or fact.training_disposition != generic.TRAINING_EXCLUDE
        or fact.human_training_excluded is not True
        or fact.source_decision_schema != subject._2VS_FORMAL_DECISION_SCHEMA
        or fact.source_decision_sha256 != subject._2VS_FORMAL_DECISION_SHA256
        or fact.source_binding_path
        != subject._2VS_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
        for fact in source.facts
    ):
        raise ValueError("2VS_NORMALIZED_FACT_SEMANTICS_INVALID")

    historical = generic.load_real_historical_reconciliation_v1(root)
    historical_copy = tuple(dict(row) for row in historical)
    subject._prove_2vs_original_unreviewed_prior_v1(historical)
    historical_2vs = [
        row
        for row in historical
        if row["canonical_event_id"] in set(EXPECTED_2VS_EVENT_IDS)
    ]
    if len(historical_2vs) != 8 or any(
        row["raw_review_unit_id"] != subject._2VS_REVIEW_UNIT_ID
        or row["current_review_status"] != generic.CURRENTLY_UNREVIEWED
        or row["calibration_eligible"] != "true"
        or row["calibration_exclusion_reason"] != ""
        for row in historical_2vs
    ):
        raise ValueError("ORIGINAL_2VS_PRIOR_PROOF_INVALID")

    sources = subject.load_real_completed_decision_sources_with_2vs_v1(root)
    if len(sources) != 6 or [len(item.facts) for item in sources] != [
        8,
        16,
        8,
        9,
        8,
        8,
    ]:
        raise ValueError("REAL_SOURCE_COMPOSITION_NOT_8_16_8_9_8_8")
    if len({item.binding.review_unit_id for item in sources}) != 6:
        raise ValueError("REAL_REVIEW_UNITS_NOT_EXACT6")
    if len({item.binding.stable_identity for item in sources}) != 6:
        raise ValueError("REAL_SOURCE_IDENTITIES_NOT_EXACT6")
    all_source_ids = [
        fact.canonical_event_id for item in sources for fact in item.facts
    ]
    if len(all_source_ids) != 57 or len(set(all_source_ids)) != 57:
        raise ValueError("REAL_NORMALIZED_FACTS_NOT_COLLISION_FREE_EXACT57")

    try:
        generic.reconcile_completed_human_decisions_v1(historical, sources)
    except generic.CompletedDecisionReconciliationError as error:
        if not str(error).startswith("PRIOR_REVIEW_STATUS_NOT_UNREVIEWED:"):
            raise ValueError("ORIGINAL_GENERIC_FAILURE_TOKEN_INVALID") from error
        failed_event_id = str(error).split(":", 1)[1]
        if failed_event_id not in set(onl_successor._ONL_EVENT_IDS):
            raise ValueError("ORIGINAL_GENERIC_FAILURE_NOT_ONL") from error
        original_generic_failure = str(error).split(":", 1)[0]
    else:
        raise ValueError("ORIGINAL_GENERIC_CALL_DID_NOT_FAIL_CLOSED")

    adapted = onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
        historical
    )
    if historical != historical_copy:
        raise ValueError("ONL_ADAPTER_MUTATED_ORIGINAL_ROWS")
    subject._prove_2vs_rows_unchanged_after_onl_normalization_v1(
        historical, adapted
    )
    adapted_2vs = {
        row["canonical_event_id"]: row
        for row in adapted
        if row["canonical_event_id"] in set(EXPECTED_2VS_EVENT_IDS)
    }
    original_2vs = {
        row["canonical_event_id"]: row
        for row in historical
        if row["canonical_event_id"] in set(EXPECTED_2VS_EVENT_IDS)
    }
    if original_2vs != adapted_2vs:
        raise ValueError("ONL_ADAPTER_CHANGED_2VS_ROWS")

    drifted = [dict(row) for row in adapted]
    for row in drifted:
        if row["canonical_event_id"] in set(EXPECTED_2VS_EVENT_IDS):
            _set_status(row, generic.CURRENTLY_IN_PROGRESS)
    try:
        generic.reconcile_completed_human_decisions_v1(drifted, sources)
    except generic.CompletedDecisionReconciliationError as error:
        if not str(error).startswith("PRIOR_REVIEW_STATUS_NOT_UNREVIEWED:"):
            raise ValueError("2VS_GENERIC_PRIOR_FAILURE_TOKEN_INVALID") from error
        two_vs_generic_failure = str(error).split(":", 1)[0]
    else:
        raise ValueError("2VS_GENERIC_PRIOR_DRIFT_DID_NOT_FAIL_CLOSED")

    one_drifted = [dict(row) for row in adapted]
    one_target = next(
        row
        for row in one_drifted
        if row["canonical_event_id"] == EXPECTED_2VS_EVENT_IDS[0]
    )
    _set_status(one_target, generic.CURRENTLY_IN_PROGRESS)
    try:
        generic.reconcile_completed_human_decisions_v1(one_drifted, sources)
    except generic.CompletedDecisionReconciliationError as error:
        if not str(error).startswith("HISTORICAL_REVIEW_UNIT_STATUS_MIXED:"):
            raise ValueError("2VS_SINGLE_ROW_DRIFT_FAILURE_TOKEN_INVALID") from error
        two_vs_single_row_failure = str(error).split(":", 1)[0]
    else:
        raise ValueError("2VS_SINGLE_ROW_DRIFT_DID_NOT_FAIL_CLOSED")

    direct = generic.reconcile_completed_human_decisions_v1(adapted, sources)
    reversed_order = generic.reconcile_completed_human_decisions_v1(
        adapted, tuple(reversed(sources))
    )
    if direct != reversed_order:
        raise ValueError("REAL_RECONCILIATION_SOURCE_ORDER_INVALID")
    if type(direct) is not generic.ReconciliationResult:
        raise ValueError("GENERIC_RECONCILIATION_RESULT_TYPE_NOT_REUSED")
    if len(direct.source_bindings) != 6 or len(direct.normalized_facts) != 57:
        raise ValueError("REAL_RESULT_SOURCE_OR_FACT_COUNT_INVALID")

    expected_summary = {
        "universe_event_count": 338,
        "universe_review_unit_count": 131,
        "completed_positive_event_count": 57,
        "completed_positive_unit_count": 6,
        "completed_negative_event_count": 24,
        "completed_negative_unit_count": 4,
        "completed_total_event_count": 81,
        "completed_total_unit_count": 10,
        "unreviewed_event_count": 257,
        "unreviewed_unit_count": 121,
        "in_progress_event_count": 0,
        "in_progress_unit_count": 0,
    }
    summary = direct.review_summary
    if summary != expected_summary:
        raise ValueError("REAL_RECONCILIATION_SUMMARY_INVALID")
    pending_events = (
        summary["unreviewed_event_count"] + summary["in_progress_event_count"]
    )
    pending_units = (
        summary["unreviewed_unit_count"] + summary["in_progress_unit_count"]
    )
    if (
        pending_events != 257
        or pending_units != 121
        or summary["completed_positive_event_count"]
        + summary["completed_negative_event_count"]
        != summary["completed_total_event_count"]
        or summary["completed_total_event_count"] + pending_events != 338
    ):
        raise ValueError("REAL_RECONCILIATION_ARITHMETIC_INVALID")

    training_counts = Counter(
        fact.training_disposition for fact in direct.normalized_facts
    )
    if training_counts != Counter(
        {generic.TRAINING_INCLUDE: 12, generic.TRAINING_EXCLUDE: 45}
    ):
        raise ValueError("NORMALIZED_TRAINING_DISPOSITION_COUNTS_INVALID")

    two_vs_path = (
        subject._2VS_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
    )
    expected_authority = json.dumps([two_vs_path], separators=(",", ":"))
    final_2vs_rows = [
        row
        for row in direct.reconciled_rows
        if row["canonical_event_id"] in set(EXPECTED_2VS_EVENT_IDS)
    ]
    if len(final_2vs_rows) != 8 or any(
        row["current_review_status"] != generic.COMPLETED_HUMAN_POSITIVE
        or row["current_status_authority_sources_json"] != expected_authority
        or row["calibration_eligible"] != "false"
        or row["calibration_exclusion_reason"]
        != generic.COMPLETED_HUMAN_POSITIVE
        for row in final_2vs_rows
    ):
        raise ValueError("2VS_FINAL_RECONCILED_ROWS_INVALID")
    forbidden_authority_lexemes = (
        "snapshot",
        "matrix",
        "onl",
        "prf",
        "adapter",
        "normalization",
    )
    if any(
        any(
            lexeme in row["current_status_authority_sources_json"].lower()
            for lexeme in forbidden_authority_lexemes
        )
        for row in final_2vs_rows
    ):
        raise ValueError("2VS_FINAL_STATUS_AUTHORITY_CONTAMINATED")

    prior = generic.reconcile_completed_human_decisions_v1(
        adapted,
        sources[:-1],
    )
    prior_pending_events = (
        prior.review_summary["unreviewed_event_count"]
        + prior.review_summary["in_progress_event_count"]
    )
    prior_pending_units = (
        prior.review_summary["unreviewed_unit_count"]
        + prior.review_summary["in_progress_unit_count"]
    )
    prior_training = Counter(
        fact.training_disposition for fact in prior.normalized_facts
    )
    deltas = {
        "two_vs_completed_positive_delta": (
            summary["completed_positive_event_count"]
            - prior.review_summary["completed_positive_event_count"]
        ),
        "two_vs_completed_total_delta": (
            summary["completed_total_event_count"]
            - prior.review_summary["completed_total_event_count"]
        ),
        "two_vs_unreviewed_delta": (
            summary["unreviewed_event_count"]
            - prior.review_summary["unreviewed_event_count"]
        ),
        "two_vs_in_progress_delta": (
            summary["in_progress_event_count"]
            - prior.review_summary["in_progress_event_count"]
        ),
        "two_vs_pending_delta": pending_events - prior_pending_events,
        "two_vs_pending_unit_delta": pending_units - prior_pending_units,
        "two_vs_training_excluded_delta": (
            training_counts[generic.TRAINING_EXCLUDE]
            - prior_training[generic.TRAINING_EXCLUDE]
        ),
        "two_vs_training_include_delta": (
            training_counts[generic.TRAINING_INCLUDE]
            - prior_training[generic.TRAINING_INCLUDE]
        ),
    }
    if deltas != {
        "two_vs_completed_positive_delta": 8,
        "two_vs_completed_total_delta": 8,
        "two_vs_unreviewed_delta": -8,
        "two_vs_in_progress_delta": 0,
        "two_vs_pending_delta": -8,
        "two_vs_pending_unit_delta": -1,
        "two_vs_training_excluded_delta": 8,
        "two_vs_training_include_delta": 0,
    }:
        raise ValueError("2VS_RECONCILIATION_DELTA_INVALID")

    task_pairs = tuple(
        (semantic_name, display_alias)
        for _task_id, semantic_name, display_alias, _generated, _fixed
        in two_vs_ingestion_owner.CANONICAL_TASKS
    )
    if (
        task_pairs != EXPECTED_CANONICAL_TASKS
        or len(two_vs_ingestion_owner.CANONICAL_TASKS) != 5
        or (3, "scaffold_only", "B3")
        != two_vs_ingestion_owner.CANONICAL_TASKS[3][:3]
    ):
        raise ValueError("GLOBAL_CANONICAL_EXACT5_INVALID")

    published_positive = _published_positive_count(root)
    if published_positive != 66:
        raise ValueError("PUBLISHED_GLOBAL_POSITIVE_COUNT_NOT_66")
    expected_next_positive = (
        published_positive + deltas["two_vs_completed_positive_delta"]
    )
    if expected_next_positive != 74:
        raise ValueError("EXPECTED_NEXT_GLOBAL_POSITIVE_COUNT_NOT_74")

    output = {
        **candidate,
        **frozen,
        **architecture,
        "repository_state_neutral": True,
        "historical_authority_modified": False,
        "source_binding_count": 6,
        "normalized_fact_count": 57,
        "two_vs_prior_unreviewed_event_count": 8,
        "two_vs_prior_unreviewed_unit_count": 1,
        "original_generic_failure": original_generic_failure,
        "two_vs_generic_prior_failure": two_vs_generic_failure,
        "two_vs_single_row_failure": two_vs_single_row_failure,
        "two_vs_rows_unchanged_by_onl_adapter": True,
        **expected_summary,
        "pending_event_count": pending_events,
        "pending_review_unit_count": pending_units,
        "training_include_count": training_counts[generic.TRAINING_INCLUDE],
        "training_excluded_count": training_counts[generic.TRAINING_EXCLUDE],
        **deltas,
        "training_admitted_count_created": 0,
        "pair_authority_created": False,
        "role_authority_created": False,
        "geometry_authority_created": False,
        "pre_topology_created": False,
        "global_census_updated": False,
        "global_census_update": "NOT_DONE",
        "published_global_positive_count": published_positive,
        "two_vs_reconciliation_local_positive_delta": 8,
        "ready_for_current_global_census_refresh": True,
        "expected_next_global_positive_count": expected_next_positive,
        "expected_next_census_derivation_status": (
            "EXPECTED_NEXT_CENSUS_DERIVATION"
        ),
        "expected_next_census_derivation": dict(
            EXPECTED_NEXT_CENSUS_DERIVATION
        ),
        "global_canonical_exact5_unchanged": True,
        "two_vs_completed_decision_reconciled": True,
        "feature_semantics": "AUDIT_REQUIRED_LATER",
        "ready_for_training": False,
        "model_or_training_work_performed": False,
    }
    if output["candidate_file_count"] != 4:
        raise ValueError("CANDIDATE_FILE_COUNT_NOT_EXACT4")
    required_true = (
        "repository_state_neutral",
        "generic_predecessor_types_reused",
        "generic_reconciliation_engine_reused",
        "prf_exact5_source_loader_reused",
        "onl_transition_owner_reused_exactly_once",
        "two_vs_ingestion_owner_reused",
        "two_vs_rows_unchanged_by_onl_adapter",
        "ready_for_current_global_census_refresh",
        "global_canonical_exact5_unchanged",
        "two_vs_completed_decision_reconciled",
    )
    if any(output[key] is not True for key in required_true):
        raise ValueError("REQUIRED_TRUE_SAFETY_VALUE_INVALID")
    required_false = (
        "historical_authority_modified",
        "two_vs_transition_adapter_created",
        "pair_authority_created",
        "role_authority_created",
        "geometry_authority_created",
        "pre_topology_created",
        "global_census_updated",
        "ready_for_training",
        "model_or_training_work_performed",
    )
    if any(output[key] is not False for key in required_false):
        raise ValueError("REQUIRED_FALSE_SAFETY_VALUE_INVALID")
    if output["training_admitted_count_created"] != 0:
        raise ValueError("TRAINING_ADMISSION_CREATED")
    if output["global_census_update"] != "NOT_DONE":
        raise ValueError("GLOBAL_CENSUS_UPDATE_STATUS_INVALID")
    if output["expected_next_census_derivation_status"] != (
        "EXPECTED_NEXT_CENSUS_DERIVATION"
    ):
        raise ValueError("EXPECTED_NEXT_CENSUS_STATUS_INVALID")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    arguments = parser.parse_args()
    result = run_check_v1(arguments.repo_root)
    for key in (
        "repository_state_neutral",
        "candidate_file_count",
        "candidate_total_bytes",
        "source_binding_count",
        "normalized_fact_count",
        "two_vs_prior_unreviewed_event_count",
        "two_vs_prior_unreviewed_unit_count",
        "two_vs_transition_adapter_created",
        "onl_transition_owner_reused_exactly_once",
        "two_vs_rows_unchanged_by_onl_adapter",
        "original_generic_failure",
        "two_vs_generic_prior_failure",
        "two_vs_single_row_failure",
        "universe_event_count",
        "universe_review_unit_count",
        "completed_positive_event_count",
        "completed_positive_unit_count",
        "completed_negative_event_count",
        "completed_negative_unit_count",
        "completed_total_event_count",
        "completed_total_unit_count",
        "unreviewed_event_count",
        "unreviewed_unit_count",
        "in_progress_event_count",
        "in_progress_unit_count",
        "pending_event_count",
        "pending_review_unit_count",
        "training_include_count",
        "training_excluded_count",
        "two_vs_completed_positive_delta",
        "two_vs_completed_total_delta",
        "two_vs_unreviewed_delta",
        "two_vs_pending_delta",
        "two_vs_pending_unit_delta",
        "two_vs_training_excluded_delta",
        "two_vs_training_include_delta",
        "training_admitted_count_created",
        "global_census_updated",
        "global_census_update",
        "published_global_positive_count",
        "ready_for_current_global_census_refresh",
        "expected_next_global_positive_count",
        "expected_next_census_derivation_status",
        "global_canonical_exact5_unchanged",
        "two_vs_completed_decision_reconciled",
        "feature_semantics",
        "ready_for_training",
        "model_or_training_work_performed",
    ):
        value = result[key]
        rendered = str(value).lower() if type(value) is bool else str(value)
        print(key + "=" + rendered)
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
