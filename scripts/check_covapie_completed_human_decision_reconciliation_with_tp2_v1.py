#!/usr/bin/env python3
"""Fail-closed checker for the TP2 completed-decision reconciliation Exact4."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import stat
import subprocess
import sys
from typing import Any, NoReturn

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from covalent_ext import covapie_completed_human_decision_reconciliation_v1 as generic  # noqa: E402
from covalent_ext import covapie_completed_human_decision_reconciliation_with_4lh_v1 as predecessor  # noqa: E402
from covalent_ext import covapie_completed_human_decision_reconciliation_with_tp2_v1 as subject  # noqa: E402
from covalent_ext import covapie_tp2_completed_decision_ingestion_and_task_label_availability_v1 as ingestion  # noqa: E402

BASELINE_COMMIT = "ecd40d0790d45d45bf27b246798b21f7d6dcd7e2"
CANDIDATE_UNTRACKED = "CANDIDATE_UNTRACKED"
TRACKED_CLEAN = "TRACKED_CLEAN"
DEPENDENCY_BINDINGS = (
    ("GENERIC_OWNER", "src/covalent_ext/covapie_completed_human_decision_reconciliation_v1.py", 35925, "2fcdf85f4753cedf6fe803ae1640fbf65484cdad2bc67732b5d9fdc24b8c3548"),
    ("WITH_4LH_PREDECESSOR_OWNER", predecessor.SOURCE_RELATIVE.as_posix(), 30628, "911396f60c985d6c32e1dcbff025a89d5bbcf07b2fed11a99e774272f7128391"),
    ("WITH_4LH_PREDECESSOR_ARTIFACT", predecessor.OUTPUT_RELATIVE.as_posix(), 331767, "1d21c8baff3c451f3e184dd20aaee90dd69d89fcfa7312e614dd5bcd8ca85b54"),
    ("TP2_INGESTION_OWNER", ingestion.SOURCE_RELATIVE.as_posix(), 78257, "7921cf1677a8477242224894b335bf6697804b857d27b8b652a8e3008f4e5615"),
    ("TP2_INGESTION_SNAPSHOT", (ingestion.OUTPUT_ROOT_RELATIVE / ingestion.SNAPSHOT).as_posix(), 40730, "f623a7f92ae16693bf570ab1ab5fa3ce416cc1d7a6ee6be0df597e623286290f"),
    ("TP2_INGESTION_MATRIX", (ingestion.OUTPUT_ROOT_RELATIVE / ingestion.MATRIX).as_posix(), 12367, "ba4ff589c3e8fdc971659db789ba66a296e332514bbe225af72748b164ec3971"),
    ("TP2_INGESTION_SUMMARY", (ingestion.OUTPUT_ROOT_RELATIVE / ingestion.SUMMARY).as_posix(), 1899, "821b0201d60bd516ffac5d2909b02f285c29620615dd8e8c0597afec711d89aa"),
    ("TP2_INGESTION_MANIFEST", (ingestion.OUTPUT_ROOT_RELATIVE / ingestion.MANIFEST).as_posix(), 23632, "367ca3b99905faebe85eaeeee9cd5bb7f6635844dc5b83de3455696173ab4648"),
)
FORBIDDEN_SUFFIXES = (".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pyc", ".tmp", ".part")
PROTECTED_PREFIXES = ("data/raw/", "checkpoints/", "equivariant_diffusion/", "covapie-state/")
PROTECTED_FILES = {"lightning_modules.py", "dataset.py", "data/prepare_crossdocked.py"}


def _fail(token: str) -> NoReturn:
    raise ValueError("COVAPIE_TP2_RECONCILIATION_V1_ERROR:" + token)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_regular(path: Path, label: str) -> bytes:
    try:
        metadata, payload = path.lstat(), path.read_bytes()
    except OSError as error:
        raise ValueError("READ_FAILED:" + label) from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        _fail("NOT_REGULAR_FILE:" + label)
    return payload


def _git(root: Path, *arguments: str) -> str:
    if not arguments or arguments[0] not in {"diff", "ls-files", "merge-base", "rev-list", "rev-parse", "status"}:
        _fail("GIT_SUBCOMMAND_FORBIDDEN")
    process = subprocess.run(("git", *arguments), cwd=root, text=True, capture_output=True, check=False)
    if process.returncode:
        _fail("GIT_COMMAND_FAILED:" + arguments[0])
    return process.stdout.rstrip("\n")


def _ancestor(root: Path, older: str, newer: str) -> bool:
    process = subprocess.run(("git", "merge-base", "--is-ancestor", older, newer), cwd=root, capture_output=True, check=False)
    if process.returncode not in (0, 1):
        _fail("GIT_ANCESTRY_CHECK_FAILED")
    return process.returncode == 0


def classify_repository_profile(
    *, expected_paths: tuple[str, ...], tracked_paths: set[str],
    ordinary_untracked: set[str], status_lines: tuple[str, ...],
    working_diff: set[str], cached_diff: set[str],
) -> str:
    expected = set(expected_paths)
    if len(expected_paths) != 4 or len(expected) != 4:
        _fail("EXPECTED_INVENTORY_NOT_EXACT4")
    tracked_candidate = expected & tracked_paths
    if tracked_candidate and tracked_candidate != expected:
        _fail("MIXED_TRACKING_STATE")
    if working_diff:
        _fail("TRACKED_WORKTREE_MODIFICATION_PRESENT")
    if cached_diff:
        _fail("STAGED_INDEX_CHANGE_PRESENT")
    if not tracked_candidate:
        if ordinary_untracked != expected or set(status_lines) != {"?? " + path for path in expected}:
            _fail("CANDIDATE_UNTRACKED_NOT_STRICT_EXACT4")
        return CANDIDATE_UNTRACKED
    if ordinary_untracked or status_lines:
        _fail("TRACKED_CLEAN_STATE_DIRTY")
    return TRACKED_CLEAN


def validate_repository_relation_values(
    *, profile: str, expected_paths: set[str], head: str, origin_main: str,
    ahead: int, behind: int, baseline_is_ancestor_of_head: bool,
    baseline_is_ancestor_of_origin: bool, origin_is_ancestor_of_head: bool,
    changed_since_baseline: set[str],
) -> None:
    if profile == CANDIDATE_UNTRACKED:
        if not (
            head == origin_main == BASELINE_COMMIT and (ahead, behind) == (0, 0)
            and baseline_is_ancestor_of_head and baseline_is_ancestor_of_origin
            and origin_is_ancestor_of_head and not changed_since_baseline
        ):
            _fail("CANDIDATE_BASELINE_RELATION_INVALID")
        return
    if profile != TRACKED_CLEAN:
        _fail("REPOSITORY_PROFILE_INVALID")
    if (
        not baseline_is_ancestor_of_head or not baseline_is_ancestor_of_origin
        or not origin_is_ancestor_of_head or head == BASELINE_COMMIT or behind != 0
        or ahead < 0 or not expected_paths <= changed_since_baseline
        or ((ahead == 0) != (origin_main == head))
    ):
        _fail("TRACKED_CLEAN_PUBLICATION_RELATION_INVALID")


def _validate_history_scope(changed: set[str]) -> None:
    for path in sorted(changed):
        if path in PROTECTED_FILES or any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES):
            _fail("PROTECTED_PATH_CHANGED_SINCE_BASELINE:" + path)
        if Path(path).suffix.lower() in FORBIDDEN_SUFFIXES:
            _fail("FORBIDDEN_SUFFIX_CHANGED_SINCE_BASELINE:" + path)


def _verify_repository(root: Path) -> dict[str, object]:
    paths = tuple(path.as_posix() for path in subject.EXACT4_PATHS)
    tracked = set(filter(None, _git(root, "ls-files").splitlines()))
    untracked = set(filter(None, _git(root, "ls-files", "--others", "--exclude-standard").splitlines()))
    status_lines = tuple(filter(None, _git(root, "status", "--short", "--untracked-files=all").splitlines()))
    working = set(filter(None, _git(root, "diff", "--name-only").splitlines()))
    cached = set(filter(None, _git(root, "diff", "--cached", "--name-only").splitlines()))
    profile = classify_repository_profile(
        expected_paths=paths, tracked_paths=tracked, ordinary_untracked=untracked,
        status_lines=status_lines, working_diff=working, cached_diff=cached,
    )
    head = _git(root, "rev-parse", "HEAD")
    origin = _git(root, "rev-parse", "origin/main")
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    relation = _git(root, "rev-list", "--left-right", "--count", "HEAD...origin/main").split()
    if branch != "main" or len(relation) != 2 or any(not part.isdigit() for part in relation):
        _fail("REPOSITORY_IDENTITY_INVALID")
    ahead, behind = map(int, relation)
    changed = set() if profile == CANDIDATE_UNTRACKED else set(filter(None, _git(root, "diff", "--name-only", BASELINE_COMMIT + "..HEAD").splitlines()))
    validate_repository_relation_values(
        profile=profile, expected_paths=set(paths), head=head, origin_main=origin,
        ahead=ahead, behind=behind,
        baseline_is_ancestor_of_head=True if profile == CANDIDATE_UNTRACKED else _ancestor(root, BASELINE_COMMIT, "HEAD"),
        baseline_is_ancestor_of_origin=True if profile == CANDIDATE_UNTRACKED else _ancestor(root, BASELINE_COMMIT, "origin/main"),
        origin_is_ancestor_of_head=True if profile == CANDIDATE_UNTRACKED else _ancestor(root, "origin/main", "HEAD"),
        changed_since_baseline=changed,
    )
    _validate_history_scope(changed)
    return {"branch": branch, "HEAD": head, "origin_main": origin, "ahead": ahead, "behind": behind, "lifecycle": profile, "tracked_modification_count": 0, "staged_count": 0, "ordinary_untracked_count": len(untracked)}


def _verify_dependencies(root: Path) -> list[dict[str, object]]:
    reports = []
    for role, relative, byte_count, digest in DEPENDENCY_BINDINGS:
        payload = _read_regular(root / relative, role)
        if len(payload) != byte_count or _sha256(payload) != digest:
            _fail("PUBLISHED_DEPENDENCY_DRIFT:" + role)
        reports.append({"role": role, "path": relative, "bytes": len(payload), "SHA256": digest})
    return reports


def _verify_exact4_files(root: Path) -> list[dict[str, object]]:
    reports = []
    for relative in subject.EXACT4_PATHS:
        path = root / relative
        payload = _read_regular(path, relative.as_posix())
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError("EXACT4_NOT_UTF8:" + relative.as_posix()) from error
        mode = stat.S_IMODE(path.lstat().st_mode)
        if text.startswith("\ufeff") or "\r" in text or "\x00" in text or mode & 0o111:
            _fail("EXACT4_TEXT_OR_MODE_INVALID:" + relative.as_posix())
        reports.append({"path": relative.as_posix(), "bytes": len(payload), "LOC": len(text.splitlines()), "SHA256": _sha256(payload), "filesystem_mode": format(mode, "04o"), "git_mode": "100644"})
    return reports


def _strict_json(payload: bytes, label: str) -> dict[str, Any]:
    try:
        return generic._strict_json_object(payload, label)
    except generic.CompletedDecisionReconciliationError as error:
        raise ValueError(label + "_INVALID:" + str(error)) from error


def _expected_projection_from_ingestion(bound: dict[str, object]) -> list[dict[str, object]]:
    subject._validate_rich_tp2_boundary_v1(bound)
    compatibility = bound.get("generic_Exact11_compatibility")
    if type(compatibility) is not dict or type(compatibility.get("facts")) is not list:
        _fail("INGESTION_GENERIC_PROJECTION_INVALID")
    return copy.deepcopy(compatibility["facts"])


def _stable_identity(binding: dict[str, object]) -> str:
    return f"{binding.get('path_namespace')}:{binding.get('source_path')}@{binding.get('sha256')}"


def _verify_artifact_semantics(
    artifact: dict[str, Any], *, predecessor_artifact: dict[str, Any],
    expected_projection: list[dict[str, object]],
) -> dict[str, object]:
    """Check direct semantics before any serialized-byte comparison."""

    if tuple(artifact) != subject._ARTIFACT_FIELDS:
        _fail("ARTIFACT_TOP_LEVEL_SCHEMA_INVALID")
    if tuple(predecessor_artifact) != subject._ARTIFACT_FIELDS:
        _fail("PREDECESSOR_ARTIFACT_TOP_LEVEL_SCHEMA_INVALID")
    bindings, facts, rows = artifact.get("source_bindings"), artifact.get("normalized_facts"), artifact.get("reconciled_rows")
    old_bindings, old_facts, old_rows = predecessor_artifact.get("source_bindings"), predecessor_artifact.get("normalized_facts"), predecessor_artifact.get("reconciled_rows")
    if not all(isinstance(value, list) for value in (bindings, facts, rows, old_bindings, old_facts, old_rows)):
        _fail("ARTIFACT_COLLECTION_TYPE_INVALID")
    assert isinstance(bindings, list) and isinstance(facts, list) and isinstance(rows, list)
    assert isinstance(old_bindings, list) and isinstance(old_facts, list) and isinstance(old_rows, list)
    if len(old_bindings) != 23 or len(old_facts) != 135 or len(old_rows) != 338 or predecessor_artifact.get("review_summary") != subject._PREDECESSOR_REVIEW_SUMMARY:
        _fail("PUBLISHED_PREDECESSOR_ARTIFACT_INVALID")
    if len(bindings) != 24 or len(facts) != 139 or len(rows) != 338:
        _fail("ARTIFACT_EXACT_COUNTS_INVALID")
    if any(type(item) is not dict or set(item) != set(subject._SOURCE_BINDING_FIELDS) or item.get("path_namespace") != "repository_parent_relative" or str(item.get("source_path", "")).startswith("/") for item in bindings):
        _fail("ARTIFACT_SOURCE_BINDING_SCHEMA_INVALID")
    if len({_stable_identity(item) for item in bindings}) != 24 or len({item["review_unit_id"] for item in bindings}) != 24:
        _fail("ARTIFACT_SOURCE_IDENTITY_DUPLICATE")
    if any(type(item) is not dict or set(item) != set(subject._GENERIC_FACT_FIELDS) or subject._FORBIDDEN_RICH_FACT_FIELDS & set(item) for item in facts):
        _fail("ARTIFACT_GENERIC_FACT_NOT_EXACT11")
    if bindings[:-1] != old_bindings:
        _fail("PREDECESSOR_SOURCE_PREFIX_INVALID")
    expected_binding = {
        "source_path": ingestion.FORMAL_DECISION_RELATIVE.as_posix(),
        "path_namespace": "repository_parent_relative", "byte_count": 17825,
        "sha256": "95fc125eefe09dd7ed81c9e95f2b76a084b889ece239aed5eb96215409315dc0",
        "schema_version": ingestion.FORMAL_DECISION_SCHEMA,
        "review_unit_id": ingestion.EXPECTED_REVIEW_UNIT_ID,
    }
    if bindings[-1] != expected_binding:
        _fail("TP2_SOURCE_BINDING_INVALID")
    if facts[:135] != old_facts:
        _fail("PREDECESSOR_FACT_PREFIX_INVALID")
    if facts[135:] != expected_projection:
        _fail("TP2_FACTS_NOT_EXACT_INGESTION_PROJECTION")
    if any(
        item.get("legacy_completed_review_status") != generic.COMPLETED_HUMAN_NEGATIVE
        or item.get("task_relevance_disposition") != generic.TASK_NOT_RELEVANT
        or item.get("chemistry_disposition") != generic.CHEMISTRY_POSITIVE
        or item.get("training_disposition") != generic.TRAINING_NOT_APPLICABLE
        or item.get("human_training_excluded") is not False
        for item in facts[135:]
    ):
        _fail("TP2_CLASSIFICATION_INVALID")
    if artifact.get("review_summary") != subject._SUCCESSOR_REVIEW_SUMMARY:
        _fail("ARTIFACT_REVIEW_SUMMARY_INVALID")
    target_ids = set(ingestion.EXPECTED_EVENT_IDS)
    changed_target = changed_non_target = 0
    for old, new in zip(old_rows, rows, strict=True):
        if old.get("canonical_event_id") not in target_ids:
            changed_non_target += old != new
            continue
        changed = {key for key in old if old[key] != new[key]}
        if (
            changed != subject._ALLOWED_RECONCILIATION_FIELDS
            or new.get("current_review_status") != generic.COMPLETED_HUMAN_NEGATIVE
            or new.get("current_status_authority_sources_json") != generic._canonical_json([ingestion.FORMAL_DECISION_RELATIVE.as_posix()])
            or new.get("calibration_eligible") != "false"
            or new.get("calibration_exclusion_reason") != generic.COMPLETED_HUMAN_NEGATIVE
        ):
            _fail("TP2_RECONCILIATION_TRANSITION_INVALID")
        changed_target += old != new
    if (changed_target, changed_non_target) != (4, 0):
        _fail("RECONCILIATION_DELTA_NOT_EXACT4_ONLY")
    return {"source_count": 24, "accepted_fact_count": 139, "reconciled_row_count": 338, "changed_target_rows": 4, "unchanged_rows": 334, "non_target_changed_rows": 0, "duplicate_count": 0}


def _verify_coverage_contract(
    predecessor_coverage: dict[str, object], successor_coverage: dict[str, object],
    predecessor_facts: list[dict[str, object]], successor_facts: list[dict[str, object]],
) -> None:
    if predecessor_coverage != subject.PREDECESSOR_COVERAGE_SUMMARY or predecessor_coverage != predecessor.SUCCESSOR_COVERAGE_SUMMARY:
        _fail("PREDECESSOR_COVERAGE_DRIFT")
    if successor_coverage != subject.SUCCESSOR_COVERAGE_SUMMARY:
        _fail("SUCCESSOR_COVERAGE_DRIFT")
    before_distribution = predecessor_coverage.get("decision_category_distribution")
    after_distribution = successor_coverage.get("decision_category_distribution")
    if type(before_distribution) is not dict or type(after_distribution) is not dict:
        _fail("COVERAGE_DISTRIBUTION_NOT_OBJECT")
    for coverage, facts, source_count in ((predecessor_coverage, predecessor_facts, 23), (successor_coverage, successor_facts, 24)):
        if (
            coverage.get("accepted_fact_count") != len(facts)
            or coverage.get("accepted_review_unit_count") != source_count
            or coverage.get("stable_source_identity_count") != source_count
            or coverage.get("remaining_unreviewed_chemistry_event_count") != 338 - len(facts)
            or coverage.get("remaining_unreviewed_review_unit_upper_bound") != 131 - source_count
            or coverage.get("label_ready_event_count") != 16
            or coverage.get("training_mask_target_count") != 0
            or coverage.get("training_authority") is not False
        ):
            _fail("COVERAGE_DIRECT_EVIDENCE_MISMATCH")
    if (
        sum(before_distribution.values()) != len(predecessor_facts)
        or sum(after_distribution.values()) != len(successor_facts)
        or after_distribution["task_domain_negative"] - before_distribution["task_domain_negative"] != 4
        or any(
            after_distribution[key] != before_distribution[key]
            for key in ("chemistry_positive", "chemistry_negative", "task_domain_positive")
        )
        or successor_facts[:135] != predecessor_facts
        or any(
            fact.get("task_relevance_disposition") != generic.TASK_NOT_RELEVANT
            or fact.get("chemistry_disposition") != generic.CHEMISTRY_POSITIVE
            for fact in successor_facts[135:]
        )
    ):
        _fail("COVERAGE_TP2_TASK_DOMAIN_NEGATIVE_DELTA_INVALID")


def _verify_byte_identity(expected: bytes, observed: bytes) -> None:
    if expected != observed:
        _fail("MATERIALIZED_ARTIFACT_BYTES_MISMATCH")


def _expect_tamper(token: str, callback) -> str:
    try:
        callback()
    except ValueError as error:
        if token not in str(error) or (
            token != "MATERIALIZED_ARTIFACT_BYTES_MISMATCH"
            and "MATERIALIZED_ARTIFACT_BYTES_MISMATCH" in str(error)
        ):
            raise
        return token
    _fail("TAMPER_PROBE_DID_NOT_FAIL:" + token)


def _tamper_probes(artifact: dict[str, Any], old: dict[str, Any], projection: list[dict[str, object]]) -> dict[str, str]:
    def semantic(candidate: dict[str, Any]) -> None:
        _verify_artifact_semantics(candidate, predecessor_artifact=old, expected_projection=projection)
    probes: dict[str, str] = {}
    candidate = copy.deepcopy(artifact); candidate["normalized_facts"][0], candidate["normalized_facts"][1] = candidate["normalized_facts"][1], candidate["normalized_facts"][0]
    probes["predecessor_fact_reorder"] = _expect_tamper("PREDECESSOR_FACT_PREFIX_INVALID", lambda: semantic(candidate))
    candidate = copy.deepcopy(artifact); candidate["normalized_facts"][-1]["chemistry_disposition"] = "NEGATIVE"
    probes["tp2_classification_drift"] = _expect_tamper("TP2_FACTS_NOT_EXACT_INGESTION_PROJECTION", lambda: semantic(candidate))
    candidate = copy.deepcopy(artifact); candidate["normalized_facts"].pop()
    probes["missing_tp2_fact"] = _expect_tamper("ARTIFACT_EXACT_COUNTS_INVALID", lambda: semantic(candidate))
    candidate = copy.deepcopy(artifact); candidate["source_bindings"][-1] = copy.deepcopy(candidate["source_bindings"][0])
    probes["duplicate_source_identity"] = _expect_tamper("ARTIFACT_SOURCE_IDENTITY_DUPLICATE", lambda: semantic(candidate))
    candidate = copy.deepcopy(artifact); candidate["normalized_facts"][-1]["role_profile"] = "STRICT_LINKER_PRESENT_V1"
    probes["rich_field_leak"] = _expect_tamper("ARTIFACT_GENERIC_FACT_NOT_EXACT11", lambda: semantic(candidate))
    candidate = copy.deepcopy(artifact); candidate["reconciled_rows"][0]["calibration_eligible"] = "false" if candidate["reconciled_rows"][0]["calibration_eligible"] == "true" else "true"
    probes["non_target_row_change"] = _expect_tamper("RECONCILIATION_DELTA_NOT_EXACT4_ONLY", lambda: semantic(candidate))
    candidate = copy.deepcopy(artifact); candidate["review_summary"]["unreviewed_event_count"] += 1
    probes["review_summary_drift"] = _expect_tamper("ARTIFACT_REVIEW_SUMMARY_INVALID", lambda: semantic(candidate))
    coverage = copy.deepcopy(subject.SUCCESSOR_COVERAGE_SUMMARY); coverage["accepted_fact_count"] = 138
    probes["coverage_count_drift"] = _expect_tamper("SUCCESSOR_COVERAGE_DRIFT", lambda: _verify_coverage_contract(subject.PREDECESSOR_COVERAGE_SUMMARY, coverage, old["normalized_facts"], artifact["normalized_facts"]))
    payload = json.dumps(artifact).encode()
    probes["raw_byte_corruption"] = _expect_tamper("MATERIALIZED_ARTIFACT_BYTES_MISMATCH", lambda: _verify_byte_identity(payload, payload + b" "))
    return probes


def _lifecycle_simulations() -> dict[str, bool]:
    paths = tuple(path.as_posix() for path in subject.EXACT4_PATHS); expected = set(paths)
    if classify_repository_profile(expected_paths=paths, tracked_paths=set(), ordinary_untracked=expected, status_lines=tuple("?? " + path for path in paths), working_diff=set(), cached_diff=set()) != CANDIDATE_UNTRACKED:
        _fail("CANDIDATE_SIMULATION_FAILED")
    if classify_repository_profile(expected_paths=paths, tracked_paths=expected, ordinary_untracked=set(), status_lines=(), working_diff=set(), cached_diff=set()) != TRACKED_CLEAN:
        _fail("TRACKED_SIMULATION_FAILED")
    common = dict(profile=TRACKED_CLEAN, expected_paths=expected, behind=0, baseline_is_ancestor_of_head=True, baseline_is_ancestor_of_origin=True, origin_is_ancestor_of_head=True, changed_since_baseline=expected)
    validate_repository_relation_values(**common, head="successor", origin_main=BASELINE_COMMIT, ahead=1)
    validate_repository_relation_values(**common, head="successor", origin_main="successor", ahead=0)
    validate_repository_relation_values(**{**common, "changed_since_baseline": {*expected, "docs/later.md"}}, head="later", origin_main="successor", ahead=1)
    return {"candidate_untracked": True, "tracked_clean": True, "committed_unpushed": True, "pushed_successor": True, "later_clean_descendant": True}


def check(root: Path = ROOT) -> dict[str, object]:
    root = root.resolve()
    repository = _verify_repository(root)
    dependencies = _verify_dependencies(root)
    exact4 = _verify_exact4_files(root)
    ingestion_report = ingestion.check_materialized_v1(root)
    bound = ingestion.load_frozen_formal_decision_v1(root)
    projection = _expected_projection_from_ingestion(bound)
    old = _strict_json(_read_regular(root / predecessor.OUTPUT_RELATIVE, "PREDECESSOR_ARTIFACT"), "PREDECESSOR_ARTIFACT")
    observed_payload = _read_regular(root / subject.OUTPUT_RELATIVE, "TP2_ARTIFACT")
    artifact = _strict_json(observed_payload, "TP2_ARTIFACT")
    artifact_report = _verify_artifact_semantics(artifact, predecessor_artifact=old, expected_projection=projection)
    _verify_coverage_contract(subject.PREDECESSOR_COVERAGE_SUMMARY, subject.SUCCESSOR_COVERAGE_SUMMARY, old["normalized_facts"], artifact["normalized_facts"])
    expected_payload = subject.build_artifact_v1(root)
    _verify_byte_identity(expected_payload, observed_payload)
    materialized = {
        "status": "PASS", "artifact_count": 1, "source_count": 24,
        "accepted_fact_count": 139, "byte_identical_to_rebuild": True,
        "training_authority": False, "ready_for_training": False,
    }
    tamper = _tamper_probes(artifact, old, projection)
    lifecycle = _lifecycle_simulations()
    if not (
        ingestion_report.get("status") == "PASS" and materialized.get("status") == "PASS"
        and subject.SUCCESSOR_COVERAGE_SUMMARY["training_authority"] is False
        and bound["formal_document"]["canonical_Exact5"]["B3_present"] is True
        and bound["formal_document"]["canonical_Exact5"]["sixth_task"] is False
    ):
        _fail("FINAL_READINESS_BOUNDARY_INVALID")
    return {
        "status": "PASS", "repository": repository, "dependencies": dependencies,
        "Exact4_files": exact4, "artifact": artifact_report,
        "source_chain": {"predecessor_sources": 23, "successor_sources": 24, "predecessor_facts": 135, "successor_facts": 139, "prefix_preserved": True},
        "TP2_boundary": {"event_count": 4, "legacy_status": generic.COMPLETED_HUMAN_NEGATIVE, "task_relevance": generic.TASK_NOT_RELEVANT, "chemistry": generic.CHEMISTRY_POSITIVE, "training_disposition": generic.TRAINING_NOT_APPLICABLE, "human_training_excluded": False, "pair": "SG-S1", "B3_present": True, "sixth_task": False, "training_authority": False},
        "review_summary": artifact["review_summary"],
        "coverage": {"predecessor": subject.PREDECESSOR_COVERAGE_SUMMARY, "successor": subject.SUCCESSOR_COVERAGE_SUMMARY},
        "ingestion_check": ingestion_report, "materialized_check": materialized,
        "tamper_probes": tamper, "lifecycle_simulations": lifecycle,
        "artifact_deterministic": observed_payload == expected_payload,
        "census_refresh": False, "queue_refresh": False, "next_review_started": False,
        "training_started": False, "feature_semantics_audit_performed": False,
        "feature_semantics_audit_required_later": True,
        "Step12D_is_final_training_feature_contract": False,
    }


def main() -> int:
    try:
        report = check(ROOT)
    except Exception as error:
        print("TP2_COMPLETED_DECISION_RECONCILIATION_V1_PASS=false")
        print("ERROR=" + str(error))
        return 1
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    print("TP2_COMPLETED_DECISION_RECONCILIATION_V1_PASS=true")
    print("PREDECESSOR_SOURCE_COUNT=23")
    print("SUCCESSOR_SOURCE_COUNT=24")
    print("PREDECESSOR_FACT_COUNT=135")
    print("SUCCESSOR_FACT_COUNT=139")
    print("TP2_FACT_COUNT=4")
    print("READY_FOR_TRAINING=false")
    print("TRAINING_STARTED=false")
    print("COMMIT=false")
    print("PUSH=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
