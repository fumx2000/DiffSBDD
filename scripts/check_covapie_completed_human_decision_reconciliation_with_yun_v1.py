#!/usr/bin/env python3
"""Repository-state-neutral checker for YUN reconciliation successor V1."""

from __future__ import annotations

import argparse
import ast
from collections import Counter
from dataclasses import replace
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
    covapie_completed_human_decision_reconciliation_with_yun_v1 as subject,
)
from covalent_ext import (  # noqa: E402
    covapie_yun_completed_decision_ingestion_and_task_label_availability_v1
    as yun_ingestion_owner,
)


EXACT4_PATHS = (
    "src/covalent_ext/"
    "covapie_completed_human_decision_reconciliation_with_yun_v1.py",
    "scripts/"
    "check_covapie_completed_human_decision_reconciliation_with_yun_v1.py",
    "tests/"
    "test_covapie_completed_human_decision_reconciliation_with_yun_v1.py",
    "docs/covapie_completed_human_decision_reconciliation_with_yun_v1_guide.md",
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
        "1F8_RECONCILIATION_SUCCESSOR",
        "src/covalent_ext/"
        "covapie_completed_human_decision_reconciliation_with_1f8_v1.py",
        11913,
        "496b4958679852de66905924c08aaa798b4536dd0aeb28c116f558c1e514cdce",
    ),
    (
        "YUN_INGESTION_OWNER",
        "src/covalent_ext/"
        "covapie_yun_completed_decision_ingestion_and_task_label_availability_v1.py",
        82003,
        "8339aaa2c57fe1637ab4e4feb7db964fc76224957687d2e0752e28ba3b093928",
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
        "CURRENT_GLOBAL_CENSUS_OWNER_WITH_1F8",
        "src/covalent_ext/"
        "covapie_cumulative1000_current_global_readiness_census_with_1f8_v1.py",
        55130,
        "cacb60cc5436b7744e7a545f275da44eb33a38825d04d91248ed91146f25f972",
    ),
    (
        "CURRENT_GLOBAL_CENSUS_WITH_1F8",
        "data/derived/covalent_small/"
        "covapie_cumulative1000_current_global_readiness_census_with_1f8_v1/"
        "covapie_cumulative1000_current_global_readiness_census_with_1f8_v1.csv",
        514588,
        "31d6add9d59d5eb9b40e8603eb9631230a75efa1f52590c3556827f62441175d",
    ),
    (
        "CURRENT_GLOBAL_CENSUS_SUMMARY_WITH_1F8",
        "data/derived/covalent_small/"
        "covapie_cumulative1000_current_global_readiness_census_with_1f8_v1/"
        "covapie_cumulative1000_current_global_readiness_summary_with_1f8_v1.json",
        15062,
        "9a341222ff0932603f900042579b47f6969c50259bfd0d89d75dffe55bf3641f",
    ),
    (
        "CURRENT_GLOBAL_CENSUS_MANIFEST_WITH_1F8",
        "data/derived/covalent_small/"
        "covapie_cumulative1000_current_global_readiness_census_with_1f8_v1/"
        "covapie_cumulative1000_current_global_readiness_manifest_with_1f8_v1.json",
        30872,
        "e9c159fa53550d3fd0a62e9cad0017255bae23a1952f8066e92ca4a56b0b7602",
    ),
)
YUN_FORMAL_RELATIVE = (
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "YUN_COVAPIE_BULK_REVIEW_UNIT_1138FFC288DFD03D/"
    "formal-human-decision-v1/yun_formal_human_decision_v1.json"
)
YUN_FORMAL_BYTE_COUNT = 30722
YUN_FORMAL_SHA256 = (
    "b4eeebe03354e820d9658225997c34b58b41c66f4dfe126230024306816e1140"
)
CURRENT_CENSUS_RELATIVE = Path(FROZEN_REPOSITORY_FILES[6][1])
EXPECTED_PUBLIC_API = (
    "CompletedDecisionReconciliationWithYUNError",
    "project_yun_completed_decision_v1",
    "load_real_completed_decision_sources_with_yun_v1",
    "reconcile_real_completed_human_decisions_with_yun_v1",
)
EXPECTED_YUN_EVENT_IDS = (
    "COVAPIE_CYS_SG_EVENT_V1:4LL0:A:CYS:797-:SG:C:YUN:CAN",
    "COVAPIE_CYS_SG_EVENT_V1:4LL0:B:CYS:797-:SG:D:YUN:CAN",
    "COVAPIE_CYS_SG_EVENT_V1:4LRM:A:CYS:800-:SG:F:YUN:CAN",
    "COVAPIE_CYS_SG_EVENT_V1:4LRM:B:CYS:800-:SG:G:YUN:CAN",
    "COVAPIE_CYS_SG_EVENT_V1:4LRM:C:CYS:800-:SG:H:YUN:CAN",
    "COVAPIE_CYS_SG_EVENT_V1:4LRM:D:CYS:800-:SG:I:YUN:CAN",
    "COVAPIE_CYS_SG_EVENT_V1:4LRM:E:CYS:800-:SG:J:YUN:CAN",
)
EXPECTED_CANONICAL_TASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
EXPECTED_NEXT_CENSUS_DERIVATION = {
    "chemistry_positive": 89,
    "chemistry_negative": 0,
    "chemistry_not_established": 86,
    "chemistry_unresolved": 825,
    "task_relevant": 90,
    "task_not_relevant": 86,
    "task_unresolved": 824,
    "training_include": 36,
    "training_exclude": 53,
    "training_not_applicable": 86,
    "training_unresolved": 825,
    "completed_human_positive": 72,
    "currently_unreviewed": 242,
    "sample_pair_authority": 89,
    "sample_role_authority": 89,
    "strict_profile": 39,
    "direct_profile": 50,
    "task_A": 89,
    "task_B": 39,
    "task_B2": 39,
    "task_B3": 89,
    "task_C": 89,
    "future_training_candidates": 19,
    "current_runtime_model_usable": 17,
    "formal_training_admitted": 5,
    "ready_for_formal_training": 0,
    "missing_split_within_positive": 48,
    "missing_split_within_include": 11,
    "missing_tensor_within_positive": 48,
    "missing_tensor_within_include": 7,
    "missing_tensor_composition": ("G3H8", "ONL9", "PRF8", "2VS8", "1F8 8", "YUN7"),
    "all_missing_are_training_excluded_population": False,
    "pair_authority_absent_all": 911,
    "pair_authority_absent_within_positive": 0,
    "role_authority_absent_all": 911,
    "role_authority_absent_within_positive": 0,
    "human_training_exclusion_within_positive": 53,
    "missing_POST_training_authority": 72,
    "missing_POST_training_authority_within_include": 19,
    "missing_admission": 84,
    "missing_admission_within_include": 31,
    "feature_semantics_pending_positive": 89,
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
    """Verify exactly the four portable YUN reconciliation candidate paths."""

    root = repo_root.resolve()
    matching = {
        path.relative_to(root).as_posix()
        for path in root.rglob(
            "*covapie_completed_human_decision_reconciliation_with_yun_v1*"
        )
        if path.is_file()
    }
    if matching != set(EXACT4_PATHS):
        raise ValueError("YUN_RECONCILIATION_CANDIDATE_INVENTORY_NOT_EXACT4")

    bindings: list[dict[str, object]] = []
    for relative in EXACT4_PATHS:
        path = root / relative
        payload = _read_regular_file(path, "EXACT4:" + relative)
        _validate_text_payload(payload, relative)
        mode = stat.S_IMODE(path.stat().st_mode)
        if mode != 0o644:
            raise ValueError("EXACT4_MODE_NOT_0644:" + relative)
        if path.name.endswith(FORBIDDEN_SUFFIXES):
            raise ValueError("EXACT4_FORBIDDEN_SUFFIX:" + relative)
        if len(payload) >= MAX_FILE_BYTES:
            raise ValueError("EXACT4_FILE_NOT_BELOW_1_MIB:" + relative)
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
            root.parent / YUN_FORMAL_RELATIVE,
            label="YUN_FORMAL_HUMAN_DECISION",
            expected_byte_count=YUN_FORMAL_BYTE_COUNT,
            expected_sha256=YUN_FORMAL_SHA256,
        )
    )
    return {"frozen_input_bindings": bindings}


def _verify_thin_successor_architecture(repo_root: Path) -> dict[str, object]:
    tree = ast.parse(_read_regular_file(repo_root.resolve() / EXACT4_PATHS[0], "MODULE"))
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
    if class_names != {"CompletedDecisionReconciliationWithYUNError"}:
        raise ValueError("SUCCESSOR_NEW_DATA_CLASS_OR_CLASS_INVALID")
    function_names = {
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    if any(
        name.lower().startswith("_adapt_yun")
        or ("yun" in name.lower() and "transition" in name.lower())
        for name in function_names
    ):
        raise ValueError("YUN_TRANSITION_ADAPTER_CREATED")
    if subject.YUN_TRANSITION_ADAPTER_CREATED is not False:
        raise ValueError("YUN_TRANSITION_ADAPTER_FLAG_INVALID")
    if any(
        isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign))
        and any(
            isinstance(target, ast.Subscript)
            for target in (
                node.targets if isinstance(node, ast.Assign) else (node.target,)
            )
        )
        for node in ast.walk(tree)
    ):
        raise ValueError("YUN_ROW_STATE_MUTATION_LOGIC_CREATED")

    called_names: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            called_names.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            called_names.append(node.func.attr)
    forbidden_calls = {
        "open",
        "mkdir",
        "touch",
        "unlink",
        "rename",
        "replace",
        "write_bytes",
        "write_text",
        "forward",
        "backward",
        "step",
    }
    if set(called_names) & forbidden_calls:
        raise ValueError("SUCCESSOR_MATERIALIZATION_OR_TRAINING_CALL_FORBIDDEN")
    required_delegations = {
        "load_frozen_formal_decision_v1",
        "load_real_completed_decision_sources_with_1f8_v1",
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
    if called_names.count("reconcile_completed_human_decisions_v1") != 1:
        raise ValueError("GENERIC_RECONCILER_NOT_DELEGATED_EXACTLY_ONCE")
    if "reconcile_real_completed_human_decisions_with_1f8_v1" in called_names:
        raise ValueError("1F8_RECONCILED_ROWS_REUSED_AS_INPUT")
    if tuple(subject.__all__) != EXPECTED_PUBLIC_API:
        raise ValueError("SUCCESSOR_PUBLIC_API_INVALID")
    return {
        "generic_predecessor_types_reused": True,
        "generic_reconciliation_engine_reused_exactly_once": True,
        "one_f8_exact7_source_loader_reused": True,
        "onl_transition_owner_reused_exactly_once": True,
        "yun_ingestion_owner_reused": True,
        "yun_transition_adapter_created": False,
        "new_normalized_data_classes_created": 0,
        "materialization_calls_created": 0,
        "model_or_training_imports_created": 0,
    }


def _published_census_state(repo_root: Path) -> dict[str, int]:
    payload = _read_regular_file(
        repo_root.resolve() / CURRENT_CENSUS_RELATIVE,
        "PUBLISHED_CURRENT_GLOBAL_CENSUS_WITH_1F8",
    )
    try:
        rows = tuple(
            csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
        )
    except (UnicodeDecodeError, csv.Error) as error:
        raise ValueError("PUBLISHED_CURRENT_GLOBAL_CENSUS_PARSE_FAILED") from error
    if len(rows) != 1000:
        raise ValueError("PUBLISHED_CURRENT_GLOBAL_CENSUS_NOT_EXACT1000")
    yun_rows = [
        row for row in rows if row.get("canonical_event_id") in EXPECTED_YUN_EVENT_IDS
    ]
    if len(yun_rows) != 7 or any(
        row.get("current_review_status") != generic.CURRENTLY_UNREVIEWED
        or row.get("chemistry_disposition") != "UNRESOLVED"
        for row in yun_rows
    ):
        raise ValueError("PUBLISHED_CURRENT_CENSUS_YUN_STATE_INVALID")
    summary_path = repo_root.resolve() / FROZEN_REPOSITORY_FILES[7][1]
    try:
        summary = json.loads(
            _read_regular_file(
                summary_path, "PUBLISHED_CURRENT_GLOBAL_CENSUS_SUMMARY_WITH_1F8"
            )
        )
    except json.JSONDecodeError as error:
        raise ValueError("PUBLISHED_CURRENT_GLOBAL_SUMMARY_PARSE_FAILED") from error
    state = {
        "positive": sum(
            row.get("chemistry_disposition") == "POSITIVE" for row in rows
        ),
        "training_include": summary.get("training_stage", {}).get(
            "training_use_include_count"
        ),
        "future_candidates": summary.get("training_stage", {}).get(
            "future_training_admission_candidate_count"
        ),
    }
    if state != {
        "positive": 82,
        "training_include": 29,
        "future_candidates": 12,
    }:
        raise ValueError("PUBLISHED_CURRENT_GLOBAL_COUNTS_INVALID")
    return state


def _verify_expected_next_census_derivation(
    repo_root: Path,
    source: generic.NormalizedDecisionSource,
    reconciliation: generic.ReconciliationResult,
    published: dict[str, int],
) -> dict[str, object]:
    """Derive informational next values without materializing census output."""

    summary_path = repo_root.resolve() / FROZEN_REPOSITORY_FILES[7][1]
    try:
        current = json.loads(
            _read_regular_file(
                summary_path, "PUBLISHED_CURRENT_GLOBAL_CENSUS_SUMMARY_WITH_1F8"
            )
        )
        chemistry = current["chemistry"]
        task = current["task_relevance"]
        training = current["training_use"]
        training_stage = current["training_stage"]
        pair = current["reactive_pair"]
        role = current["role"]
        exact5 = current["canonical_exact5"]
        blockers = current["blockers"]
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        raise ValueError("PUBLISHED_CURRENT_DERIVATION_INPUT_INVALID") from error

    expected_current_blockers = {
        "chemistry_unresolved": 832,
        "pair_absent": 918,
        "role_absent": 918,
        "human_training_exclusion": 53,
        "missing_split_positive": 41,
        "missing_split_include": 4,
        "missing_tensor_positive": 41,
        "missing_tensor_include": 0,
        "missing_POST_positive": 65,
        "missing_POST_include": 12,
        "missing_admission_positive": 77,
        "missing_admission_include": 24,
        "feature_semantics_positive": 82,
    }
    observed_current_blockers = {
        "chemistry_unresolved": blockers["chemistry_unresolved"]["all_1000"],
        "pair_absent": blockers["pair_authority_absent"]["all_1000"],
        "role_absent": blockers["role_authority_absent"]["all_1000"],
        "human_training_exclusion": blockers["human_training_exclusion"][
            "within_positive_82"
        ],
        "missing_split_positive": blockers["missing_split_authority"][
            "within_positive_82"
        ],
        "missing_split_include": blockers["missing_split_authority"][
            "within_include_29"
        ],
        "missing_tensor_positive": blockers["missing_tensor_integration"][
            "within_positive_82"
        ],
        "missing_tensor_include": blockers["missing_tensor_integration"][
            "within_include_29"
        ],
        "missing_POST_positive": blockers["missing_POST_training_authority"][
            "within_positive_82"
        ],
        "missing_POST_include": blockers["missing_POST_training_authority"][
            "within_include_29"
        ],
        "missing_admission_positive": blockers["missing_training_admission"][
            "within_positive_82"
        ],
        "missing_admission_include": blockers["missing_training_admission"][
            "within_include_29"
        ],
        "feature_semantics_positive": blockers["feature_semantics_pending"][
            "within_positive_82"
        ],
    }
    if observed_current_blockers != expected_current_blockers:
        raise ValueError("PUBLISHED_CURRENT_BLOCKER_BASELINE_INVALID")
    if blockers["missing_tensor_integration"]["missing_source_composition"] != {
        "G3H": 8,
        "ONL": 9,
        "PRF": 8,
        "2VS": 8,
        "1F8": 8,
    }:
        raise ValueError("PUBLISHED_CURRENT_TENSOR_COMPOSITION_INVALID")

    bound = yun_ingestion_owner.load_frozen_formal_decision_v1(repo_root)
    events = bound.get("normalized", {}).get("events", [])
    if len(events) != 7 or any(
        event.get("candidate_for_future_training_admission") is not True
        or event.get("training_admitted") is not False
        for event in events
    ):
        raise ValueError("YUN_INFORMATIONAL_FUTURE_CANDIDACY_INVALID")
    delta = len(source.facts)
    if delta != 7 or any(
        fact.training_disposition != generic.TRAINING_INCLUDE
        or fact.human_training_excluded is not False
        for fact in source.facts
    ):
        raise ValueError("YUN_INFORMATIONAL_DELTA_INPUT_INVALID")

    observed = {
        "chemistry_positive": chemistry["POSITIVE"]["count"] + delta,
        "chemistry_negative": chemistry["NEGATIVE"]["count"],
        "chemistry_not_established": chemistry["NOT_ESTABLISHED"]["count"],
        "chemistry_unresolved": chemistry["UNRESOLVED"]["count"] - delta,
        "task_relevant": task["RELEVANT"]["count"] + delta,
        "task_not_relevant": task["NOT_RELEVANT"]["count"],
        "task_unresolved": task["UNRESOLVED"]["count"] - delta,
        "training_include": training["INCLUDE"]["count"] + delta,
        "training_exclude": training["EXCLUDE_FROM_TRAINING_ONLY"]["count"],
        "training_not_applicable": training["NOT_APPLICABLE"]["count"],
        "training_unresolved": training["UNRESOLVED"]["count"] - delta,
        "completed_human_positive": reconciliation.review_summary[
            "completed_positive_event_count"
        ],
        "currently_unreviewed": reconciliation.review_summary[
            "unreviewed_event_count"
        ],
        "sample_pair_authority": pair["sample_level_authoritative_pair_count"]
        + delta,
        "sample_role_authority": role[
            "role_partition_sample_authoritative_count"
        ]
        + delta,
        "strict_profile": role["role_profile_counts"][
            "STRICT_LINKER_PRESENT_V1"
        ],
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
        "future_training_candidates": published["future_candidates"] + delta,
        "current_runtime_model_usable": training_stage[
            "current_runtime_model_usable_count"
        ],
        "formal_training_admitted": training_stage["formal_training_admitted_count"],
        "ready_for_formal_training": training_stage[
            "ready_for_formal_training_event_count"
        ],
        "missing_split_within_positive": observed_current_blockers[
            "missing_split_positive"
        ]
        + delta,
        "missing_split_within_include": observed_current_blockers[
            "missing_split_include"
        ]
        + delta,
        "missing_tensor_within_positive": observed_current_blockers[
            "missing_tensor_positive"
        ]
        + delta,
        "missing_tensor_within_include": observed_current_blockers[
            "missing_tensor_include"
        ]
        + delta,
        "missing_tensor_composition": (
            "G3H8",
            "ONL9",
            "PRF8",
            "2VS8",
            "1F8 8",
            "YUN7",
        ),
        "all_missing_are_training_excluded_population": False,
        "pair_authority_absent_all": observed_current_blockers["pair_absent"]
        - delta,
        "pair_authority_absent_within_positive": 0,
        "role_authority_absent_all": observed_current_blockers["role_absent"]
        - delta,
        "role_authority_absent_within_positive": 0,
        "human_training_exclusion_within_positive": observed_current_blockers[
            "human_training_exclusion"
        ],
        "missing_POST_training_authority": observed_current_blockers[
            "missing_POST_positive"
        ]
        + delta,
        "missing_POST_training_authority_within_include": (
            observed_current_blockers["missing_POST_include"] + delta
        ),
        "missing_admission": observed_current_blockers[
            "missing_admission_positive"
        ]
        + delta,
        "missing_admission_within_include": observed_current_blockers[
            "missing_admission_include"
        ]
        + delta,
        "feature_semantics_pending_positive": observed_current_blockers[
            "feature_semantics_positive"
        ]
        + delta,
    }
    if observed != EXPECTED_NEXT_CENSUS_DERIVATION:
        raise ValueError("EXPECTED_NEXT_CENSUS_DERIVATION_INVALID")
    return observed


def _run_production_pipeline_counted(
    repo_root: Path,
) -> tuple[generic.ReconciliationResult, dict[str, int]]:
    """Run the public production path and prove its two delegates run once."""

    original_onl = (
        onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1
    )
    original_generic = generic.reconcile_completed_human_decisions_v1
    calls: Counter[str] = Counter()

    def counted_onl(rows: object) -> tuple[dict[str, str], ...]:
        calls["onl_adapter"] += 1
        return original_onl(rows)

    def counted_generic(rows: object, sources: object) -> generic.ReconciliationResult:
        calls["generic_reconciler"] += 1
        return original_generic(rows, sources)

    subject.onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1 = (
        counted_onl
    )
    subject.generic.reconcile_completed_human_decisions_v1 = counted_generic
    try:
        result = subject.reconcile_real_completed_human_decisions_with_yun_v1(
            repo_root
        )
    finally:
        subject.onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1 = (
            original_onl
        )
        subject.generic.reconcile_completed_human_decisions_v1 = original_generic
    if calls != Counter({"onl_adapter": 1, "generic_reconciler": 1}):
        raise ValueError("PRODUCTION_DELEGATE_RUNTIME_CALL_COUNTS_INVALID")
    return result, dict(calls)


def _set_status(row: dict[str, str], status: str) -> None:
    row["current_review_status"] = status
    row["calibration_eligible"] = (
        "true" if status == generic.CURRENTLY_UNREVIEWED else "false"
    )
    row["calibration_exclusion_reason"] = (
        "" if status == generic.CURRENTLY_UNREVIEWED else status
    )


def _expect_generic_failure(
    rows: object,
    sources: object,
    token: str,
) -> str:
    try:
        generic.reconcile_completed_human_decisions_v1(rows, sources)
    except generic.CompletedDecisionReconciliationError as error:
        if not str(error).startswith(token):
            raise ValueError("GENERIC_FAILURE_TOKEN_INVALID:" + str(error)) from error
        return str(error).split(":", 1)[0]
    raise ValueError("GENERIC_FAILURE_NOT_RAISED:" + token)


def _verify_generic_protections(
    adapted: tuple[dict[str, str], ...],
    sources: tuple[generic.NormalizedDecisionSource, ...],
) -> dict[str, str]:
    duplicate_binding = _expect_generic_failure(
        adapted, (*sources, sources[0]), "SOURCE_BINDING_DUPLICATE:"
    )

    original = sources[-1]
    incomplete = replace(original, facts=original.facts[:-1])
    incomplete_coverage = _expect_generic_failure(
        adapted,
        (*sources[:-1], incomplete),
        "SOURCE_REVIEW_UNIT_EVENT_SET_MISMATCH:",
    )
    outside_fact = replace(
        original.facts[0], canonical_event_id="COVAPIE_SYNTHETIC_OUTSIDE_YUN"
    )
    outside = replace(original, facts=(outside_fact, *original.facts[1:]))
    event_outside = _expect_generic_failure(
        adapted, (*sources[:-1], outside), "EVENT_NOT_IN_HISTORICAL_UNIVERSE:"
    )

    mismatched_rows = [dict(row) for row in adapted]
    for row in mismatched_rows:
        if row["canonical_event_id"] in set(EXPECTED_YUN_EVENT_IDS):
            row["raw_review_unit_id"] = "DRIFTED_YUN_REVIEW_UNIT"
    source_historical_mismatch = _expect_generic_failure(
        mismatched_rows,
        sources,
        "FACT_HISTORICAL_REVIEW_UNIT_MISMATCH:",
    )

    clone_binding = replace(
        original.binding,
        source_path="synthetic/yun_collision.json",
        sha256="1" * 64,
    )
    clone_facts = tuple(
        replace(
            fact,
            source_decision_sha256=clone_binding.sha256,
            source_binding_path=clone_binding.source_path,
        )
        for fact in original.facts
    )
    clone = generic.NormalizedDecisionSource(
        binding=clone_binding, facts=clone_facts
    )
    cross_source_collision = _expect_generic_failure(
        adapted, (*sources, clone), "CROSS_SOURCE_EVENT_COLLISION:"
    )
    return {
        "duplicate_source_binding_failure": duplicate_binding,
        "incomplete_review_unit_coverage_failure": incomplete_coverage,
        "source_event_outside_historical_failure": event_outside,
        "source_historical_review_unit_mismatch_failure": source_historical_mismatch,
        "cross_source_collision_failure": cross_source_collision,
    }


def run_check_v1(repo_root: Path) -> dict[str, object]:
    """Execute frozen identity, YUN prior, delegation, and census gates."""

    root = repo_root.resolve()
    candidate = verify_candidate_exact4_v1(root)
    frozen = _verify_frozen_inputs(root)
    architecture = _verify_thin_successor_architecture(root)
    production_result, production_calls = _run_production_pipeline_counted(root)

    source = subject.project_yun_completed_decision_v1(repo_root=root)
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
        EXPECTED_YUN_EVENT_IDS
    ):
        raise ValueError("YUN_NORMALIZED_EVENT_IDS_NOT_EXACT7")
    if any(
        fact.human_review_completed is not True
        or fact.legacy_completed_review_status
        != generic.COMPLETED_HUMAN_POSITIVE
        or fact.task_relevance_disposition != generic.TASK_RELEVANT
        or fact.chemistry_disposition != generic.CHEMISTRY_POSITIVE
        or fact.training_disposition != generic.TRAINING_INCLUDE
        or fact.human_training_excluded is not False
        or fact.source_decision_schema != subject._YUN_FORMAL_DECISION_SCHEMA
        or fact.source_decision_sha256 != subject._YUN_FORMAL_DECISION_SHA256
        or fact.source_binding_path
        != subject._YUN_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
        for fact in source.facts
    ):
        raise ValueError("YUN_NORMALIZED_FACT_SEMANTICS_INVALID")

    historical = generic.load_real_historical_reconciliation_v1(root)
    historical_copy = tuple(dict(row) for row in historical)
    subject._prove_yun_original_unreviewed_prior_v1(historical)
    historical_yun = [
        row
        for row in historical
        if row["canonical_event_id"] in set(EXPECTED_YUN_EVENT_IDS)
    ]
    if len(historical_yun) != 7 or any(
        row["raw_review_unit_id"] != subject._YUN_REVIEW_UNIT_ID
        or row["current_review_status"] != generic.CURRENTLY_UNREVIEWED
        or row["calibration_eligible"] != "true"
        or row["calibration_exclusion_reason"] != ""
        for row in historical_yun
    ):
        raise ValueError("ORIGINAL_YUN_PRIOR_PROOF_INVALID")

    sources = subject.load_real_completed_decision_sources_with_yun_v1(root)
    if len(sources) != 8 or [len(item.facts) for item in sources] != [
        8,
        16,
        8,
        9,
        8,
        8,
        8,
        7,
    ]:
        raise ValueError("REAL_SOURCE_COMPOSITION_NOT_8_16_8_9_8_8_8_7")
    if len({item.binding.review_unit_id for item in sources}) != 8:
        raise ValueError("REAL_REVIEW_UNITS_NOT_EXACT8")
    if len({item.binding.stable_identity for item in sources}) != 8:
        raise ValueError("REAL_SOURCE_IDENTITIES_NOT_EXACT8")
    all_source_ids = [
        fact.canonical_event_id for item in sources for fact in item.facts
    ]
    if len(all_source_ids) != 72 or len(set(all_source_ids)) != 72:
        raise ValueError("REAL_NORMALIZED_FACTS_NOT_COLLISION_FREE_EXACT72")

    original_generic_failure = _expect_generic_failure(
        historical, sources, "PRIOR_REVIEW_STATUS_NOT_UNREVIEWED:"
    )
    adapted = onl_successor._adapt_onl_in_progress_completion_for_generic_reconciliation_v1(
        historical
    )
    if historical != historical_copy:
        raise ValueError("ONL_ADAPTER_MUTATED_ORIGINAL_ROWS")
    subject._prove_yun_rows_unchanged_after_onl_normalization_v1(
        historical, adapted
    )
    original_yun = {
        row["canonical_event_id"]: row
        for row in historical
        if row["canonical_event_id"] in set(EXPECTED_YUN_EVENT_IDS)
    }
    adapted_yun = {
        row["canonical_event_id"]: row
        for row in adapted
        if row["canonical_event_id"] in set(EXPECTED_YUN_EVENT_IDS)
    }
    if original_yun != adapted_yun:
        raise ValueError("ONL_ADAPTER_CHANGED_YUN_ROWS")

    drifted = [dict(row) for row in adapted]
    for row in drifted:
        if row["canonical_event_id"] in set(EXPECTED_YUN_EVENT_IDS):
            _set_status(row, generic.CURRENTLY_IN_PROGRESS)
    yun_generic_prior_failure = _expect_generic_failure(
        drifted, sources, "PRIOR_REVIEW_STATUS_NOT_UNREVIEWED:"
    )
    one_drifted = [dict(row) for row in adapted]
    one_target = next(
        row
        for row in one_drifted
        if row["canonical_event_id"] == EXPECTED_YUN_EVENT_IDS[0]
    )
    _set_status(one_target, generic.CURRENTLY_IN_PROGRESS)
    yun_single_row_failure = _expect_generic_failure(
        one_drifted, sources, "HISTORICAL_REVIEW_UNIT_STATUS_MIXED:"
    )

    direct = generic.reconcile_completed_human_decisions_v1(adapted, sources)
    reversed_order = generic.reconcile_completed_human_decisions_v1(
        adapted, tuple(reversed(sources))
    )
    if direct != reversed_order:
        raise ValueError("REAL_RECONCILIATION_SOURCE_ORDER_INVALID")
    if type(direct) is not generic.ReconciliationResult:
        raise ValueError("GENERIC_RECONCILIATION_RESULT_TYPE_NOT_REUSED")
    if production_result != direct:
        raise ValueError("PRODUCTION_AND_DIRECT_RECONCILIATION_DIFFER")
    if len(direct.source_bindings) != 8 or len(direct.normalized_facts) != 72:
        raise ValueError("REAL_RESULT_SOURCE_OR_FACT_COUNT_INVALID")

    expected_summary = {
        "universe_event_count": 338,
        "universe_review_unit_count": 131,
        "completed_positive_event_count": 72,
        "completed_positive_unit_count": 8,
        "completed_negative_event_count": 24,
        "completed_negative_unit_count": 4,
        "completed_total_event_count": 96,
        "completed_total_unit_count": 12,
        "unreviewed_event_count": 242,
        "unreviewed_unit_count": 119,
        "in_progress_event_count": 0,
        "in_progress_unit_count": 0,
    }
    summary = direct.review_summary
    if summary != expected_summary:
        raise ValueError("REAL_RECONCILIATION_SUMMARY_INVALID")
    pending_events = summary["unreviewed_event_count"] + summary["in_progress_event_count"]
    pending_units = summary["unreviewed_unit_count"] + summary["in_progress_unit_count"]
    if (
        pending_events != 242
        or pending_units != 119
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
        {generic.TRAINING_INCLUDE: 19, generic.TRAINING_EXCLUDE: 53}
    ):
        raise ValueError("NORMALIZED_TRAINING_DISPOSITION_COUNTS_INVALID")

    yun_path = subject._YUN_FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix()
    expected_authority = json.dumps([yun_path], separators=(",", ":"))
    final_yun_rows = [
        row
        for row in direct.reconciled_rows
        if row["canonical_event_id"] in set(EXPECTED_YUN_EVENT_IDS)
    ]
    if len(final_yun_rows) != 7 or any(
        row["current_review_status"] != generic.COMPLETED_HUMAN_POSITIVE
        or row["current_status_authority_sources_json"] != expected_authority
        or row["calibration_eligible"] != "false"
        or row["calibration_exclusion_reason"]
        != generic.COMPLETED_HUMAN_POSITIVE
        for row in final_yun_rows
    ):
        raise ValueError("YUN_FINAL_RECONCILED_ROWS_INVALID")
    forbidden_authority_lexemes = (
        "snapshot",
        "matrix",
        "1f8",
        "onl",
        "adapter",
        "normalization",
    )
    if any(
        any(
            lexeme in row["current_status_authority_sources_json"].lower()
            for lexeme in forbidden_authority_lexemes
        )
        for row in final_yun_rows
    ):
        raise ValueError("YUN_FINAL_STATUS_AUTHORITY_CONTAMINATED")

    prior = generic.reconcile_completed_human_decisions_v1(adapted, sources[:-1])
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
        "yun_completed_positive_delta": summary["completed_positive_event_count"]
        - prior.review_summary["completed_positive_event_count"],
        "yun_completed_total_delta": summary["completed_total_event_count"]
        - prior.review_summary["completed_total_event_count"],
        "yun_unreviewed_delta": summary["unreviewed_event_count"]
        - prior.review_summary["unreviewed_event_count"],
        "yun_in_progress_delta": summary["in_progress_event_count"]
        - prior.review_summary["in_progress_event_count"],
        "yun_pending_delta": pending_events - prior_pending_events,
        "yun_pending_unit_delta": pending_units - prior_pending_units,
        "yun_training_excluded_delta": training_counts[generic.TRAINING_EXCLUDE]
        - prior_training[generic.TRAINING_EXCLUDE],
        "yun_training_include_delta": training_counts[generic.TRAINING_INCLUDE]
        - prior_training[generic.TRAINING_INCLUDE],
    }
    if deltas != {
        "yun_completed_positive_delta": 7,
        "yun_completed_total_delta": 7,
        "yun_unreviewed_delta": -7,
        "yun_in_progress_delta": 0,
        "yun_pending_delta": -7,
        "yun_pending_unit_delta": -1,
        "yun_training_excluded_delta": 0,
        "yun_training_include_delta": 7,
    }:
        raise ValueError("YUN_RECONCILIATION_DELTA_INVALID")

    task_pairs = tuple(
        (semantic_name, display_alias)
        for _task_id, semantic_name, display_alias, _generated, _fixed
        in yun_ingestion_owner.CANONICAL_TASKS
    )
    if (
        task_pairs != EXPECTED_CANONICAL_TASKS
        or len(yun_ingestion_owner.CANONICAL_TASKS) != 5
        or (3, "scaffold_only", "B3")
        != yun_ingestion_owner.CANONICAL_TASKS[3][:3]
    ):
        raise ValueError("GLOBAL_CANONICAL_EXACT5_INVALID")

    protections = _verify_generic_protections(adapted, sources)
    published = _published_census_state(root)
    published_positive = published["positive"]
    expected_next_positive = (
        published_positive + deltas["yun_completed_positive_delta"]
    )
    if expected_next_positive != 89:
        raise ValueError("EXPECTED_NEXT_GLOBAL_POSITIVE_COUNT_NOT_89")
    next_derivation = _verify_expected_next_census_derivation(
        root, source, direct, published
    )

    return {
        **candidate,
        **frozen,
        **architecture,
        **protections,
        "repository_state_neutral": True,
        "production_onl_adapter_call_count": production_calls["onl_adapter"],
        "production_generic_reconciler_call_count": production_calls[
            "generic_reconciler"
        ],
        "historical_authority_modified": False,
        "source_binding_count": 8,
        "normalized_fact_count": 72,
        "yun_prior_unreviewed_event_count": 7,
        "yun_prior_unreviewed_unit_count": 1,
        "original_generic_failure": original_generic_failure,
        "yun_generic_prior_failure": yun_generic_prior_failure,
        "yun_single_row_failure": yun_single_row_failure,
        "yun_rows_unchanged_by_onl_adapter": True,
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
        "published_training_include_count": published["training_include"],
        "published_future_candidate_count": published["future_candidates"],
        "yun_reconciliation_local_positive_delta": 7,
        "ready_for_current_global_census_refresh": True,
        "expected_next_global_positive_count": expected_next_positive,
        "expected_next_census_derivation_status": "INFORMATIONAL_ONLY",
        "expected_next_census_derivation": next_derivation,
        "expected_next_pending_head": "NEQ/EXACT6_INFORMATIONAL_ONLY",
        "expected_next_pending_review_unit": "COVAPIE_BULK_REVIEW_UNIT_0E0F340A9F98DA62",
        "expected_next_pending_pdb_ids": ("3V61", "3V62"),
        "canonical_task_count": 5,
        "scaffold_only_B3_present": True,
        "ready_for_training": False,
        "feature_semantics": "AUDIT_REQUIRED_LATER",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    result = run_check_v1(args.repo_root)
    for key in (
        "candidate_file_count",
        "source_binding_count",
        "normalized_fact_count",
        "completed_positive_event_count",
        "completed_positive_unit_count",
        "completed_negative_event_count",
        "completed_total_event_count",
        "unreviewed_event_count",
        "pending_event_count",
        "pending_review_unit_count",
        "training_include_count",
        "training_excluded_count",
        "published_global_positive_count",
        "expected_next_global_positive_count",
        "global_census_update",
        "ready_for_training",
        "feature_semantics",
    ):
        print(f"{key}={result[key]}")
    print("covapie_completed_human_decision_reconciliation_with_yun_v1=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
