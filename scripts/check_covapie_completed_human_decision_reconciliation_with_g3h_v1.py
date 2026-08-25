#!/usr/bin/env python3
"""Repository-state-neutral checker for G3H reconciliation successor V1."""

from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import stat
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_v1 as predecessor,
)
from covalent_ext import (  # noqa: E402
    covapie_completed_human_decision_reconciliation_with_g3h_v1 as subject,
)


EXACT4_PATHS = (
    "src/covalent_ext/"
    "covapie_completed_human_decision_reconciliation_with_g3h_v1.py",
    "scripts/"
    "check_covapie_completed_human_decision_reconciliation_with_g3h_v1.py",
    "tests/"
    "test_covapie_completed_human_decision_reconciliation_with_g3h_v1.py",
    "docs/covapie_completed_human_decision_reconciliation_with_g3h_v1_guide.md",
)
PREDECESSOR_RELATIVE = (
    "src/covalent_ext/covapie_completed_human_decision_reconciliation_v1.py"
)
PREDECESSOR_BYTE_COUNT = 35925
PREDECESSOR_SHA256 = (
    "2fcdf85f4753cedf6fe803ae1640fbf65484cdad2bc67732b5d9fdc24b8c3548"
)
G3H_INGESTION_PREDECESSOR_RELATIVE = (
    "src/covalent_ext/"
    "covapie_g3h_completed_decision_ingestion_and_task_label_availability_v1.py"
)
G3H_INGESTION_PREDECESSOR_BYTE_COUNT = 72232
G3H_INGESTION_PREDECESSOR_SHA256 = (
    "ce64741183a384a238ebd8e905b4fd14b03c662021aa1e3ba3a23828a803d418"
)
HISTORICAL_RELATIVE = (
    "data/derived/covalent_small/"
    "covapie_cumulative1000_high_yield_human_review_authority_calibration_v1/"
    "covapie_cumulative1000_current_review_status_reconciliation_v1.csv"
)
HISTORICAL_BYTE_COUNT = 99335
HISTORICAL_SHA256 = (
    "4eb608e2d97b60230ae1e0ca4e4be6a7fe8b3dc45af3467cbc98f685c385862f"
)
FFQ_FORMAL_RELATIVE = (
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "FFQ_COVAPIE_BULK_REVIEW_UNIT_431D2725ADFC9E9D/"
    "formal-human-decision-v1/ffq_formal_human_decision_v1.json"
)
POA_FORMAL_RELATIVE = (
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "POA_COVAPIE_BULK_REVIEW_UNIT_6A4D564E712634EB/"
    "formal-human-decision-v1/poa_formal_human_decision_v1.json"
)
G3H_FORMAL_RELATIVE = (
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "G3H_COVAPIE_BULK_REVIEW_UNIT_5C788252BB9BA078/"
    "formal-human-decision-v1/g3h_formal_human_decision_v1.json"
)
FORMAL_BINDINGS = (
    (
        "FFQ_FORMAL_DECISION",
        FFQ_FORMAL_RELATIVE,
        14197,
        "ba0670519064399b2ecb0c73631009c8c6c4d3c14512377ecfaad0d87388e149",
    ),
    (
        "POA_FORMAL_DECISION",
        POA_FORMAL_RELATIVE,
        15675,
        "263eec2e33a7b50001f6c058959b9218601fc7fb122dc97e937b517f98c90ba8",
    ),
    (
        "G3H_FORMAL_DECISION",
        G3H_FORMAL_RELATIVE,
        22456,
        "872ac01500180f752928aeb2fb44287b7fa9cad7070e1b17a45f0d19b25d5203",
    ),
)
G3H_EVENT_IDS = (
    "COVAPIE_CYS_SG_EVENT_V1:4I3W:A:CYS:291-:SG:I:G3H:C1",
    "COVAPIE_CYS_SG_EVENT_V1:4I3W:B:CYS:291-:SG:K:G3H:C1",
    "COVAPIE_CYS_SG_EVENT_V1:4I3W:C:CYS:291-:SG:M:G3H:C1",
    "COVAPIE_CYS_SG_EVENT_V1:4I3W:D:CYS:291-:SG:O:G3H:C1",
    "COVAPIE_CYS_SG_EVENT_V1:4I3W:E:CYS:291-:SG:Q:G3H:C1",
    "COVAPIE_CYS_SG_EVENT_V1:4I3W:F:CYS:291-:SG:S:G3H:C1",
    "COVAPIE_CYS_SG_EVENT_V1:4I3W:G:CYS:291-:SG:U:G3H:C1",
    "COVAPIE_CYS_SG_EVENT_V1:4I3W:H:CYS:291-:SG:W:G3H:C1",
)
EXPECTED_PUBLIC_API = (
    "CompletedDecisionReconciliationWithG3HError",
    "project_g3h_formal_decision_v1",
    "load_real_completed_decision_sources_with_g3h_v1",
    "reconcile_real_completed_human_decisions_with_g3h_v1",
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
    """Verify the exact successor paths and portable text/file invariants."""

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
            root / PREDECESSOR_RELATIVE,
            label="GENERIC_RECONCILIATION_PREDECESSOR",
            expected_byte_count=PREDECESSOR_BYTE_COUNT,
            expected_sha256=PREDECESSOR_SHA256,
        ),
        _verify_frozen_file(
            root / G3H_INGESTION_PREDECESSOR_RELATIVE,
            label="G3H_INGESTION_PREDECESSOR",
            expected_byte_count=G3H_INGESTION_PREDECESSOR_BYTE_COUNT,
            expected_sha256=G3H_INGESTION_PREDECESSOR_SHA256,
        ),
        _verify_frozen_file(
            root / HISTORICAL_RELATIVE,
            label="HISTORICAL_RECONCILIATION",
            expected_byte_count=HISTORICAL_BYTE_COUNT,
            expected_sha256=HISTORICAL_SHA256,
        ),
    ]
    for label, relative, byte_count, sha256 in FORMAL_BINDINGS:
        bindings.append(
            _verify_frozen_file(
                root.parent / relative,
                label=label,
                expected_byte_count=byte_count,
                expected_sha256=sha256,
            )
        )
    return {"frozen_input_bindings": bindings}


def _verify_thin_successor_architecture(repo_root: Path) -> dict[str, object]:
    module_path = repo_root.resolve() / EXACT4_PATHS[0]
    tree = ast.parse(_read_regular_file(module_path, "SUCCESSOR_MODULE"))
    allowed_imports = {
        "__future__",
        "collections.abc",
        "hashlib",
        "json",
        "pathlib",
        "typing",
    }
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 1 and node.module is None:
                continue
            imported_modules.add(node.module or "")
    if not imported_modules <= allowed_imports:
        raise ValueError("SUCCESSOR_IMPORT_BOUNDARY_INVALID")
    class_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
    }
    if class_names != {"CompletedDecisionReconciliationWithG3HError"}:
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
    illegal_calls = called_names & forbidden_calls
    if illegal_calls:
        raise ValueError("SUCCESSOR_MATERIALIZATION_CALL_FORBIDDEN")
    if tuple(subject.__all__) != EXPECTED_PUBLIC_API:
        raise ValueError("SUCCESSOR_PUBLIC_API_INVALID")
    return {
        "predecessor_types_reused": True,
        "predecessor_reconciliation_engine_reused": True,
        "new_normalized_data_classes_created": 0,
        "materialization_calls_created": 0,
        "model_or_training_imports_created": 0,
    }


def run_check_v1(repo_root: Path) -> dict[str, object]:
    """Execute all frozen identity, projection, composition, and count gates."""

    root = repo_root.resolve()
    candidate = verify_candidate_exact4_v1(root)
    frozen = _verify_frozen_inputs(root)
    architecture = _verify_thin_successor_architecture(root)

    g3h_payload = _read_regular_file(
        root.parent / G3H_FORMAL_RELATIVE,
        "G3H_FORMAL_DECISION",
    )
    g3h_source = subject.project_g3h_formal_decision_v1(g3h_payload)
    sources = subject.load_real_completed_decision_sources_with_g3h_v1(root)
    if type(g3h_source) is not predecessor.NormalizedDecisionSource or any(
        type(fact) is not predecessor.NormalizedCompletedDecisionFact
        for fact in g3h_source.facts
    ):
        raise ValueError("PREDECESSOR_NORMALIZED_TYPES_NOT_REUSED")
    historical_rows = predecessor.load_real_historical_reconciliation_v1(root)
    historical_copy = tuple(dict(row) for row in historical_rows)
    direct_result = predecessor.reconcile_completed_human_decisions_v1(
        historical_rows,
        sources,
    )
    runner_result = subject.reconcile_real_completed_human_decisions_with_g3h_v1(
        root
    )
    if type(runner_result) is not predecessor.ReconciliationResult:
        raise ValueError("PREDECESSOR_RECONCILIATION_RESULT_TYPE_NOT_REUSED")
    if direct_result != runner_result:
        raise ValueError("REAL_RUNNER_DELEGATION_RESULT_MISMATCH")
    if historical_rows != historical_copy:
        raise ValueError("HISTORICAL_ROWS_MUTATED_IN_MEMORY")
    historical_g3h_rows = {
        row["canonical_event_id"]: row
        for row in historical_rows
        if row["canonical_event_id"] in G3H_EVENT_IDS
    }
    if set(historical_g3h_rows) != set(G3H_EVENT_IDS) or any(
        row["current_review_status"] != predecessor.CURRENTLY_UNREVIEWED
        for row in historical_g3h_rows.values()
    ):
        raise ValueError("G3H_PRIOR_HISTORICAL_STATUS_NOT_EXACT8_UNREVIEWED")

    if len(sources) != 3:
        raise ValueError("REAL_SOURCE_COUNT_NOT_EXACT3")
    if len({source.binding.review_unit_id for source in sources}) != 3:
        raise ValueError("REAL_REVIEW_UNITS_NOT_EXACT3")
    if len({source.binding.stable_identity for source in sources}) != 3:
        raise ValueError("REAL_SOURCE_IDENTITIES_NOT_EXACT3")
    if len(g3h_source.facts) != 8:
        raise ValueError("G3H_NORMALIZED_FACT_COUNT_NOT_EXACT8")
    if tuple(fact.canonical_event_id for fact in g3h_source.facts) != G3H_EVENT_IDS:
        raise ValueError("G3H_NORMALIZED_EVENT_IDS_NOT_EXACT8")

    result = runner_result
    summary = result.review_summary
    expected_summary = {
        "universe_event_count": 338,
        "completed_positive_event_count": 32,
        "completed_negative_event_count": 24,
        "completed_total_event_count": 56,
        "unreviewed_event_count": 273,
        "in_progress_event_count": 9,
    }
    if any(summary.get(key) != value for key, value in expected_summary.items()):
        raise ValueError("REAL_RECONCILIATION_SUMMARY_INVALID")
    pending = summary["unreviewed_event_count"] + summary["in_progress_event_count"]
    if pending != 282 or summary["completed_total_event_count"] + pending != 338:
        raise ValueError("REAL_RECONCILIATION_ARITHMETIC_INVALID")
    if len(result.source_bindings) != 3 or len(result.normalized_facts) != 32:
        raise ValueError("REAL_RECONCILIATION_SOURCE_OR_FACT_COUNT_INVALID")

    training_counts = Counter(
        fact.training_disposition for fact in result.normalized_facts
    )
    if training_counts != Counter(
        {predecessor.TRAINING_INCLUDE: 12, predecessor.TRAINING_EXCLUDE: 20}
    ):
        raise ValueError("NORMALIZED_TRAINING_DISPOSITION_COUNTS_INVALID")

    g3h_path = G3H_FORMAL_RELATIVE
    g3h_facts = tuple(
        fact
        for fact in result.normalized_facts
        if fact.source_binding_path == g3h_path
    )
    if len(g3h_facts) != 8 or any(
        fact.legacy_completed_review_status
        != predecessor.COMPLETED_HUMAN_POSITIVE
        or fact.task_relevance_disposition != predecessor.TASK_RELEVANT
        or fact.chemistry_disposition != predecessor.CHEMISTRY_POSITIVE
        or fact.training_disposition != predecessor.TRAINING_EXCLUDE
        or fact.human_training_excluded is not True
        for fact in g3h_facts
    ):
        raise ValueError("G3H_NORMALIZED_FACT_SEMANTICS_INVALID")
    g3h_rows = {
        row["canonical_event_id"]: row
        for row in result.reconciled_rows
        if row["canonical_event_id"] in G3H_EVENT_IDS
    }
    expected_authority_json = json.dumps([g3h_path], separators=(",", ":"))
    if set(g3h_rows) != set(G3H_EVENT_IDS) or any(
        row["current_review_status"] != predecessor.COMPLETED_HUMAN_POSITIVE
        or row["current_status_authority_sources_json"] != expected_authority_json
        or row["calibration_eligible"] != "false"
        or row["calibration_exclusion_reason"]
        != predecessor.COMPLETED_HUMAN_POSITIVE
        for row in g3h_rows.values()
    ):
        raise ValueError("G3H_RECONCILED_ROWS_INVALID")

    old_result = predecessor.reconcile_real_completed_human_decisions_v1(root)
    old_pending = (
        old_result.review_summary["unreviewed_event_count"]
        + old_result.review_summary["in_progress_event_count"]
    )
    if (
        summary["completed_positive_event_count"]
        - old_result.review_summary["completed_positive_event_count"]
        != 8
        or pending - old_pending != -8
    ):
        raise ValueError("G3H_DELTA_INVALID")

    output = {
        **candidate,
        **frozen,
        **architecture,
        "repository_state_neutral": True,
        "historical_reconciliation_modified": False,
        "formal_decision_binding_count": 3,
        "source_binding_count": 3,
        "normalized_fact_count": 32,
        "g3h_prior_unreviewed_count": 8,
        "g3h_reconciled_positive_count": 8,
        "universe_event_count": 338,
        "completed_positive_event_count": 32,
        "completed_negative_event_count": 24,
        "completed_total_event_count": 56,
        "unreviewed_event_count": 273,
        "in_progress_event_count": 9,
        "pending_event_count": 282,
        "training_include_count": 12,
        "training_excluded_count": 20,
        "g3h_completed_positive_delta": 8,
        "g3h_pending_delta": -8,
        "g3h_training_excluded_delta": 8,
        "g3h_training_include_delta": 0,
        "training_admitted_count_created": 0,
        "pair_authority_created": False,
        "role_authority_created": False,
        "global_readiness_census_materialized": False,
        "model_work_performed": False,
        "global_canonical_exact5_unchanged": True,
        "current_global_reconciliation_g3h_gap_closed": True,
        "current_global_readiness_census_complete": False,
        "ready_for_current_global_readiness_census_successor": True,
        "feature_semantics_audit_required_later": True,
        "ready_for_formal_training": False,
    }
    if output["candidate_file_count"] != 4:
        raise ValueError("CANDIDATE_FILE_COUNT_NOT_EXACT4")
    if output["training_admitted_count_created"] != 0:
        raise ValueError("TRAINING_ADMISSION_CREATED")
    if output["global_readiness_census_materialized"] is not False:
        raise ValueError("GLOBAL_READINESS_CENSUS_MATERIALIZED")
    if output["model_work_performed"] is not False:
        raise ValueError("MODEL_WORK_PERFORMED")
    required_true = (
        "repository_state_neutral",
        "predecessor_types_reused",
        "predecessor_reconciliation_engine_reused",
        "global_canonical_exact5_unchanged",
        "current_global_reconciliation_g3h_gap_closed",
        "ready_for_current_global_readiness_census_successor",
        "feature_semantics_audit_required_later",
    )
    if any(output[key] is not True for key in required_true):
        raise ValueError("REQUIRED_TRUE_SAFETY_VALUE_INVALID")
    required_false = (
        "historical_reconciliation_modified",
        "pair_authority_created",
        "role_authority_created",
        "global_readiness_census_materialized",
        "model_work_performed",
        "current_global_readiness_census_complete",
        "ready_for_formal_training",
    )
    if any(output[key] is not False for key in required_false):
        raise ValueError("REQUIRED_FALSE_SAFETY_VALUE_INVALID")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    arguments = parser.parse_args()
    result = run_check_v1(arguments.repo_root)
    for key in (
        "repository_state_neutral",
        "candidate_file_count",
        "historical_reconciliation_modified",
        "formal_decision_binding_count",
        "source_binding_count",
        "normalized_fact_count",
        "g3h_prior_unreviewed_count",
        "g3h_reconciled_positive_count",
        "universe_event_count",
        "completed_positive_event_count",
        "completed_negative_event_count",
        "completed_total_event_count",
        "unreviewed_event_count",
        "in_progress_event_count",
        "pending_event_count",
        "training_include_count",
        "training_excluded_count",
        "g3h_completed_positive_delta",
        "g3h_pending_delta",
        "g3h_training_excluded_delta",
        "g3h_training_include_delta",
        "training_admitted_count_created",
        "pair_authority_created",
        "role_authority_created",
        "global_readiness_census_materialized",
        "model_work_performed",
        "global_canonical_exact5_unchanged",
        "current_global_reconciliation_g3h_gap_closed",
        "current_global_readiness_census_complete",
        "ready_for_current_global_readiness_census_successor",
        "feature_semantics_audit_required_later",
        "ready_for_formal_training",
    ):
        value = result[key]
        rendered = str(value).lower() if type(value) is bool else str(value)
        print(key + "=" + rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
