#!/usr/bin/env python3
"""Repository-state-neutral checker for ONL reconciliation successor V1."""

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
    covapie_completed_human_decision_reconciliation_with_g3h_v1 as g3h_successor,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_onl_v1 as subject,
)
from covalent_ext import (  # noqa: E402
    covapie_onl_completed_decision_ingestion_and_task_label_availability_v1
    as onl_ingestion_owner,
)


EXACT4_PATHS = (
    "src/covalent_ext/"
    "covapie_completed_human_decision_reconciliation_with_onl_v1.py",
    "scripts/"
    "check_covapie_completed_human_decision_reconciliation_with_onl_v1.py",
    "tests/"
    "test_covapie_completed_human_decision_reconciliation_with_onl_v1.py",
    "docs/covapie_completed_human_decision_reconciliation_with_onl_v1_guide.md",
)
FROZEN_REPOSITORY_FILES = (
    (
        "GENERIC_RECONCILIATION_PREDECESSOR",
        "src/covalent_ext/covapie_completed_human_decision_reconciliation_v1.py",
        35925,
        "2fcdf85f4753cedf6fe803ae1640fbf65484cdad2bc67732b5d9fdc24b8c3548",
    ),
    (
        "G3H_RECONCILIATION_SUCCESSOR",
        "src/covalent_ext/"
        "covapie_completed_human_decision_reconciliation_with_g3h_v1.py",
        12686,
        "2e1e0775b8123d7266bcc6d462a9b39c0ce3c0c9385e7aba4eee1f2fb5c367a6",
    ),
    (
        "ONL_INGESTION_OWNER",
        "src/covalent_ext/"
        "covapie_onl_completed_decision_ingestion_and_task_label_availability_v1.py",
        61281,
        "abbf2f2bbc5d144395f78b80ece5a7b52ebd2ddefd802b9cf023fe15beb23d7a",
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
ONL_FORMAL_RELATIVE = (
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "ONL_COVAPIE_BULK_REVIEW_UNIT_FC5A3060FADCBA74/"
    "formal-human-decision-v1/onl_formal_human_decision_v1.json"
)
ONL_FORMAL_BYTE_COUNT = 28678
ONL_FORMAL_SHA256 = (
    "eb68b63046b561e857ae84640843914960c974ce7807be1ee18aba3f107581d5"
)
ONL_DERIVED_BINDINGS = (
    (
        onl_ingestion_owner.OUTPUT_ROOT_RELATIVE
        / onl_ingestion_owner.SNAPSHOT,
        29840,
        "3ad211c80345130b7238fbae6046d61749c2f81784b359ecd2b71af6f06ae536",
    ),
    (
        onl_ingestion_owner.OUTPUT_ROOT_RELATIVE / onl_ingestion_owner.MATRIX,
        14822,
        "175f2f070967fb33e0133501a488cf30022818dbbadcd4b85f3ab497afda969c",
    ),
    (
        onl_ingestion_owner.OUTPUT_ROOT_RELATIVE / onl_ingestion_owner.SUMMARY,
        2096,
        "def73b5efef357c43a2796ffe9b1c660cf70c506baaa7e05523bf53894525d80",
    ),
)
CURRENT_CENSUS_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_v1/"
    "covapie_cumulative1000_current_global_readiness_census_v1.csv"
)
CURRENT_CENSUS_BYTE_COUNT = 497477
CURRENT_CENSUS_SHA256 = (
    "f4f44058a68f8161969b84a7e6b5efde08d6cd1d59520010c4f742d78b171dc9"
)
CURRENT_CENSUS_SUMMARY_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_v1/"
    "covapie_cumulative1000_current_global_readiness_summary_v1.json"
)
CURRENT_CENSUS_SUMMARY_BYTE_COUNT = 13681
CURRENT_CENSUS_SUMMARY_SHA256 = (
    "569625aef3b22d12af528e2afe61ed5ebf381f84642a063a81970894b80dc74a"
)
EXPECTED_PUBLIC_API = (
    "CompletedDecisionReconciliationWithONLError",
    "project_onl_completed_decision_v1",
    "load_real_completed_decision_sources_with_onl_v1",
    "reconcile_real_completed_human_decisions_with_onl_v1",
)
EXPECTED_CANONICAL_TASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
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
    if len(payload) >= MAX_FILE_BYTES:
        raise ValueError("EXACT4_FILE_TOO_LARGE:" + label)
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
    """Verify only the four portable successor candidate paths."""

    bindings: list[dict[str, object]] = []
    for relative in EXACT4_PATHS:
        path = repo_root.resolve() / relative
        payload = _read_regular_file(path, "EXACT4:" + relative)
        _validate_text_payload(payload, relative)
        mode = stat.S_IMODE(path.stat().st_mode)
        if mode != 0o644:
            raise ValueError("EXACT4_MODE_NOT_0644:" + relative)
        if path.name.endswith(FORBIDDEN_SUFFIXES):
            raise ValueError("EXACT4_FORBIDDEN_SUFFIX:" + relative)
        bindings.append(
            {
                "path": relative,
                "byte_count": len(payload),
                "sha256": _sha256(payload),
                "mode": "0644",
            }
        )
    return {
        "candidate_file_count": len(bindings),
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
    bindings.append(
        _verify_frozen_file(
            root.parent / ONL_FORMAL_RELATIVE,
            label="ONL_FORMAL_HUMAN_DECISION",
            expected_byte_count=ONL_FORMAL_BYTE_COUNT,
            expected_sha256=ONL_FORMAL_SHA256,
        )
    )
    for relative, byte_count, sha256 in ONL_DERIVED_BINDINGS:
        bindings.append(
            _verify_frozen_file(
                root / relative,
                label="ONL_INGESTION_OUTPUT:" + relative.name,
                expected_byte_count=byte_count,
                expected_sha256=sha256,
            )
        )
    bindings.extend(
        (
            _verify_frozen_file(
                root / CURRENT_CENSUS_RELATIVE,
                label="PUBLISHED_CURRENT_GLOBAL_CENSUS",
                expected_byte_count=CURRENT_CENSUS_BYTE_COUNT,
                expected_sha256=CURRENT_CENSUS_SHA256,
            ),
            _verify_frozen_file(
                root / CURRENT_CENSUS_SUMMARY_RELATIVE,
                label="PUBLISHED_CURRENT_GLOBAL_CENSUS_SUMMARY",
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
        "copy",
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
    if class_names != {"CompletedDecisionReconciliationWithONLError"}:
        raise ValueError("SUCCESSOR_NEW_DATA_CLASS_OR_CLASS_INVALID")
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
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            called_names.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            called_names.add(node.func.attr)
    if called_names & forbidden_calls:
        raise ValueError("SUCCESSOR_MATERIALIZATION_CALL_FORBIDDEN")
    required_delegations = {
        "load_frozen_formal_decision_v1",
        "load_real_completed_decision_sources_with_g3h_v1",
        "load_real_historical_reconciliation_v1",
        "reconcile_completed_human_decisions_v1",
    }
    if not required_delegations <= called_names:
        raise ValueError("SUCCESSOR_REQUIRED_DELEGATION_MISSING")
    if tuple(subject.__all__) != EXPECTED_PUBLIC_API:
        raise ValueError("SUCCESSOR_PUBLIC_API_INVALID")
    if (
        "_adapt_onl_in_progress_completion_for_generic_reconciliation_v1"
        in subject.__all__
    ):
        raise ValueError("PRIVATE_TRANSITION_ADAPTER_EXPOSED")
    return {
        "generic_predecessor_types_reused": True,
        "generic_reconciliation_engine_reused": True,
        "g3h_exact3_loader_reused": True,
        "onl_ingestion_owner_reused": True,
        "new_normalized_data_classes_created": 0,
        "materialization_calls_created": 0,
        "model_or_training_imports_created": 0,
    }


def _published_positive_count(repo_root: Path) -> int:
    payload = _read_regular_file(
        repo_root.resolve() / CURRENT_CENSUS_RELATIVE,
        "PUBLISHED_CURRENT_GLOBAL_CENSUS",
    )
    try:
        text = payload.decode("utf-8")
        rows = tuple(csv.DictReader(io.StringIO(text, newline="")))
    except (UnicodeDecodeError, csv.Error) as error:
        raise ValueError("PUBLISHED_CURRENT_GLOBAL_CENSUS_PARSE_FAILED") from error
    return sum(row.get("chemistry_disposition") == "POSITIVE" for row in rows)


def run_check_v1(repo_root: Path) -> dict[str, object]:
    """Execute frozen identity, transition, delegation, and census gates."""

    root = repo_root.resolve()
    candidate = verify_candidate_exact4_v1(root)
    frozen = _verify_frozen_inputs(root)
    architecture = _verify_thin_successor_architecture(root)

    onl_source = subject.project_onl_completed_decision_v1(repo_root=root)
    sources = subject.load_real_completed_decision_sources_with_onl_v1(root)
    if type(onl_source) is not generic.NormalizedDecisionSource or any(
        type(fact) is not generic.NormalizedCompletedDecisionFact
        for fact in onl_source.facts
    ):
        raise ValueError("GENERIC_NORMALIZED_TYPES_NOT_REUSED")
    if len(sources) != 4:
        raise ValueError("REAL_SOURCE_COUNT_NOT_EXACT4")
    if [len(source.facts) for source in sources] != [8, 16, 8, 9]:
        raise ValueError("REAL_SOURCE_COMPOSITION_NOT_8_16_8_9")
    if len({source.binding.review_unit_id for source in sources}) != 4:
        raise ValueError("REAL_REVIEW_UNITS_NOT_EXACT4")
    if len({source.binding.stable_identity for source in sources}) != 4:
        raise ValueError("REAL_SOURCE_IDENTITIES_NOT_EXACT4")
    all_source_ids = [
        fact.canonical_event_id for source in sources for fact in source.facts
    ]
    if len(all_source_ids) != 41 or len(set(all_source_ids)) != 41:
        raise ValueError("REAL_NORMALIZED_FACTS_NOT_COLLISION_FREE_EXACT41")
    if tuple(fact.canonical_event_id for fact in onl_source.facts) != (
        subject._ONL_EVENT_IDS
    ):
        raise ValueError("ONL_NORMALIZED_EVENT_IDS_NOT_EXACT9")
    if any(
        fact.human_review_completed is not True
        or fact.legacy_completed_review_status
        != generic.COMPLETED_HUMAN_POSITIVE
        or fact.task_relevance_disposition != generic.TASK_RELEVANT
        or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
        or fact.training_disposition != generic.TRAINING_EXCLUDE
        or fact.human_training_excluded is not True
        or fact.source_decision_schema != subject._ONL_FORMAL_DECISION_SCHEMA
        or fact.source_decision_sha256 != subject._ONL_FORMAL_DECISION_SHA256
        or fact.source_binding_path
        != subject._ONL_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
        for fact in onl_source.facts
    ):
        raise ValueError("ONL_NORMALIZED_FACT_SEMANTICS_INVALID")

    historical = generic.load_real_historical_reconciliation_v1(root)
    historical_copy = tuple(dict(row) for row in historical)
    historical_onl = [
        row
        for row in historical
        if row["canonical_event_id"] in set(subject._ONL_EVENT_IDS)
    ]
    in_progress = [
        row
        for row in historical
        if row["current_review_status"] == generic.CURRENTLY_IN_PROGRESS
    ]
    if (
        len(historical) != 338
        or len({row["raw_review_unit_id"] for row in historical}) != 131
        or len(historical_onl) != 9
        or len(in_progress) != 9
        or {row["canonical_event_id"] for row in in_progress}
        != set(subject._ONL_EVENT_IDS)
        or {row["raw_review_unit_id"] for row in in_progress}
        != {subject._ONL_REVIEW_UNIT_ID}
        or any(
            row["current_review_status"] != generic.CURRENTLY_IN_PROGRESS
            or row["calibration_eligible"] != "false"
            or row["calibration_exclusion_reason"]
            != generic.CURRENTLY_IN_PROGRESS
            for row in historical_onl
        )
    ):
        raise ValueError("ORIGINAL_ONL_PRIOR_TRANSITION_PROOF_INVALID")

    try:
        generic.reconcile_completed_human_decisions_v1(historical, sources)
    except generic.CompletedDecisionReconciliationError as error:
        if not str(error).startswith("PRIOR_REVIEW_STATUS_NOT_UNREVIEWED:"):
            raise ValueError("ORIGINAL_GENERIC_FAILURE_TOKEN_INVALID") from error
        original_generic_failure = str(error).split(":", 1)[0]
    else:
        raise ValueError("ORIGINAL_GENERIC_CALL_DID_NOT_FAIL_CLOSED")

    adapted = (
        subject._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
            historical
        )
    )
    if historical != historical_copy:
        raise ValueError("PRIVATE_ADAPTER_MUTATED_ORIGINAL_ROWS")
    for before, after in zip(historical, adapted, strict=True):
        changed = {key for key in before if before[key] != after[key]}
        if before["canonical_event_id"] in set(subject._ONL_EVENT_IDS):
            if changed != subject._ALLOWED_TRANSITION_FIELDS:
                raise ValueError("PRIVATE_ADAPTER_ONL_FIELD_BOUNDARY_INVALID")
        elif changed:
            raise ValueError("PRIVATE_ADAPTER_CHANGED_NON_ONL_ROW")

    direct = generic.reconcile_completed_human_decisions_v1(adapted, sources)
    reversed_order = generic.reconcile_completed_human_decisions_v1(
        adapted, tuple(reversed(sources))
    )
    runner = subject.reconcile_real_completed_human_decisions_with_onl_v1(root)
    if direct != reversed_order or direct != runner:
        raise ValueError("REAL_RECONCILIATION_DELEGATION_OR_ORDER_INVALID")
    if type(runner) is not generic.ReconciliationResult:
        raise ValueError("GENERIC_RECONCILIATION_RESULT_TYPE_NOT_REUSED")
    if len(runner.source_bindings) != 4 or len(runner.normalized_facts) != 41:
        raise ValueError("REAL_RESULT_SOURCE_OR_FACT_COUNT_INVALID")

    summary = runner.review_summary
    expected_summary = {
        "universe_event_count": 338,
        "universe_review_unit_count": 131,
        "completed_positive_event_count": 41,
        "completed_positive_unit_count": 4,
        "completed_negative_event_count": 24,
        "completed_negative_unit_count": 4,
        "completed_total_event_count": 65,
        "completed_total_unit_count": 8,
        "unreviewed_event_count": 273,
        "unreviewed_unit_count": 123,
        "in_progress_event_count": 0,
        "in_progress_unit_count": 0,
    }
    if summary != expected_summary:
        raise ValueError("REAL_RECONCILIATION_SUMMARY_INVALID")
    pending_events = (
        summary["unreviewed_event_count"] + summary["in_progress_event_count"]
    )
    pending_units = (
        summary["unreviewed_unit_count"] + summary["in_progress_unit_count"]
    )
    if (
        pending_events != 273
        or pending_units != 123
        or summary["completed_total_event_count"] + pending_events != 338
    ):
        raise ValueError("REAL_RECONCILIATION_ARITHMETIC_INVALID")

    training_counts = Counter(
        fact.training_disposition for fact in runner.normalized_facts
    )
    if training_counts != Counter(
        {generic.TRAINING_INCLUDE: 12, generic.TRAINING_EXCLUDE: 29}
    ):
        raise ValueError("NORMALIZED_TRAINING_DISPOSITION_COUNTS_INVALID")

    onl_path = subject._ONL_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
    expected_authority = json.dumps([onl_path], separators=(",", ":"))
    final_onl_rows = [
        row
        for row in runner.reconciled_rows
        if row["canonical_event_id"] in set(subject._ONL_EVENT_IDS)
    ]
    if len(final_onl_rows) != 9 or any(
        row["current_review_status"] != generic.COMPLETED_HUMAN_POSITIVE
        or row["current_status_authority_sources_json"] != expected_authority
        or row["calibration_eligible"] != "false"
        or row["calibration_exclusion_reason"]
        != generic.COMPLETED_HUMAN_POSITIVE
        for row in final_onl_rows
    ):
        raise ValueError("ONL_FINAL_RECONCILED_ROWS_INVALID")

    prior = g3h_successor.reconcile_real_completed_human_decisions_with_g3h_v1(
        root
    )
    prior_pending_events = (
        prior.review_summary["unreviewed_event_count"]
        + prior.review_summary["in_progress_event_count"]
    )
    prior_training = Counter(
        fact.training_disposition for fact in prior.normalized_facts
    )
    deltas = {
        "onl_completed_positive_delta": (
            summary["completed_positive_event_count"]
            - prior.review_summary["completed_positive_event_count"]
        ),
        "onl_in_progress_delta": (
            summary["in_progress_event_count"]
            - prior.review_summary["in_progress_event_count"]
        ),
        "onl_pending_delta": pending_events - prior_pending_events,
        "onl_training_excluded_delta": (
            training_counts[generic.TRAINING_EXCLUDE]
            - prior_training[generic.TRAINING_EXCLUDE]
        ),
        "onl_training_include_delta": (
            training_counts[generic.TRAINING_INCLUDE]
            - prior_training[generic.TRAINING_INCLUDE]
        ),
    }
    if deltas != {
        "onl_completed_positive_delta": 9,
        "onl_in_progress_delta": -9,
        "onl_pending_delta": -9,
        "onl_training_excluded_delta": 9,
        "onl_training_include_delta": 0,
    }:
        raise ValueError("ONL_RECONCILIATION_DELTA_INVALID")

    task_contract = onl_ingestion_owner._canonical_task_contract()
    task_pairs = tuple(
        (task["semantic_long_name"], task["display_alias"])
        for task in task_contract["global_canonical_tasks"]
    )
    if (
        task_pairs != EXPECTED_CANONICAL_TASKS
        or task_contract["global_canonical_task_count"] != 5
        or task_contract["B3_present"] is not True
        or task_contract["sixth_task_created"] is not False
    ):
        raise ValueError("GLOBAL_CANONICAL_EXACT5_INVALID")

    published_positive = _published_positive_count(root)
    if published_positive != 49:
        raise ValueError("PUBLISHED_GLOBAL_POSITIVE_COUNT_NOT_49")

    output = {
        **candidate,
        **frozen,
        **architecture,
        "repository_state_neutral": True,
        "historical_authority_modified": False,
        "source_binding_count": 4,
        "normalized_fact_count": 41,
        "onl_prior_in_progress_event_count": 9,
        "onl_prior_in_progress_unit_count": 1,
        "original_generic_failure": original_generic_failure,
        "private_transition_adapter_in_memory_only": True,
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
        "global_census_updated": False,
        "published_global_positive_count": published_positive,
        "ready_for_current_global_census_refresh": True,
        "expected_next_global_positive_count": 58,
        "global_canonical_exact5_unchanged": True,
        "onl_completed_decision_reconciled": True,
        "feature_semantics": "AUDIT_REQUIRED_LATER",
        "ready_for_training": False,
        "model_work_performed": False,
    }
    if output["candidate_file_count"] != 4:
        raise ValueError("CANDIDATE_FILE_COUNT_NOT_EXACT4")
    required_true = (
        "repository_state_neutral",
        "generic_predecessor_types_reused",
        "generic_reconciliation_engine_reused",
        "g3h_exact3_loader_reused",
        "onl_ingestion_owner_reused",
        "private_transition_adapter_in_memory_only",
        "ready_for_current_global_census_refresh",
        "global_canonical_exact5_unchanged",
        "onl_completed_decision_reconciled",
    )
    if any(output[key] is not True for key in required_true):
        raise ValueError("REQUIRED_TRUE_SAFETY_VALUE_INVALID")
    required_false = (
        "historical_authority_modified",
        "pair_authority_created",
        "role_authority_created",
        "geometry_authority_created",
        "global_census_updated",
        "ready_for_training",
        "model_work_performed",
    )
    if any(output[key] is not False for key in required_false):
        raise ValueError("REQUIRED_FALSE_SAFETY_VALUE_INVALID")
    if output["training_admitted_count_created"] != 0:
        raise ValueError("TRAINING_ADMISSION_CREATED")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    arguments = parser.parse_args()
    result = run_check_v1(arguments.repo_root)
    for key in (
        "repository_state_neutral",
        "candidate_file_count",
        "source_binding_count",
        "normalized_fact_count",
        "onl_prior_in_progress_event_count",
        "onl_prior_in_progress_unit_count",
        "original_generic_failure",
        "private_transition_adapter_in_memory_only",
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
        "onl_completed_positive_delta",
        "onl_in_progress_delta",
        "onl_pending_delta",
        "onl_training_excluded_delta",
        "onl_training_include_delta",
        "training_admitted_count_created",
        "global_census_updated",
        "published_global_positive_count",
        "ready_for_current_global_census_refresh",
        "expected_next_global_positive_count",
        "global_canonical_exact5_unchanged",
        "onl_completed_decision_reconciled",
        "feature_semantics",
        "ready_for_training",
        "model_work_performed",
    ):
        value = result[key]
        rendered = str(value).lower() if type(value) is bool else str(value)
        print(key + "=" + rendered)
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
