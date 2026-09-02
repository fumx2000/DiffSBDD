#!/usr/bin/env python3
"""Fail-closed checker for the CER completed-decision ingestion Exact7."""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_cer_completed_decision_ingestion_and_task_label_availability_v1
    as owner,
)
from covalent_ext.covapie_source_binding_policy_v2 import (  # noqa: E402
    SourceBindingPolicyV2Error,
    verify_bound_source_v2,
)


ERROR = "COVAPIE_CER_INGESTION_CHECK_FAILED"
BASELINE_HEAD = "146caa0a2d8dc93f048b52d34d34a8c893954b6b"
CANDIDATE_UNTRACKED = "CANDIDATE_UNTRACKED"
TRACKED_CLEAN = "TRACKED_CLEAN"
FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".tmp", ".part", ".pyc", ".log",
)
PROTECTED_PREFIXES = (
    "data/raw/", "checkpoints/", "equivariant_diffusion/", "covapie-state/",
)
PROTECTED_FILES = {
    "lightning_modules.py", "dataset.py", "data/prepare_crossdocked.py",
}


def fail(reason: str) -> None:
    raise SystemExit(ERROR + ":" + reason)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def run_git(*arguments: str) -> str:
    allowed = {
        "diff", "ls-files", "merge-base", "rev-list", "rev-parse", "status",
    }
    if not arguments or arguments[0] not in allowed:
        fail("GIT_SUBCOMMAND_FORBIDDEN")
    result = subprocess.run(
        ("git", *arguments),
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        fail("GIT_COMMAND_FAILED:" + arguments[0])
    return result.stdout.rstrip("\n")


def check_text_file(relative: str) -> dict[str, object]:
    path = REPO_ROOT / relative
    try:
        payload = path.read_bytes()
    except OSError:
        fail("CANDIDATE_READ_FAILED:" + relative)
    if (
        not payload
        or len(payload) >= 1024 * 1024
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\x00" in payload
        or b"\r" in payload
        or not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
    ):
        fail("TEXT_HYGIENE_INVALID:" + relative)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        fail("UTF8_INVALID:" + relative)
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        fail("TRAILING_WHITESPACE:" + relative)
    digest = sha256(payload)
    try:
        verified = verify_bound_source_v2(
            path=path,
            expected_byte_count=len(payload),
            expected_sha256=digest,
            label="CER_EXACT7:" + relative,
            expected_executable=False,
        )
    except SourceBindingPolicyV2Error:
        fail("CANDIDATE_SECURITY_OR_EXECUTABLE_CLASS_INVALID:" + relative)
    if verified != payload:
        fail("CANDIDATE_UNSTABLE:" + relative)
    return {
        "path": relative,
        "byte_count": len(payload),
        "SHA256": digest,
        "executable_class": "NON_EXECUTABLE",
    }


def classify_repository_profile(
    *,
    expected_paths: tuple[str, ...],
    tracked_paths: set[str],
    ordinary_untracked: set[str],
    status_lines: tuple[str, ...],
    working_diff: set[str],
    cached_diff: set[str],
) -> str:
    expected = set(expected_paths)
    if len(expected_paths) != 7 or len(expected) != 7:
        fail("EXPECTED_INVENTORY_NOT_EXACT7")
    tracked_candidate = expected & tracked_paths
    if tracked_candidate and tracked_candidate != expected:
        fail("MIXED_TRACKING_STATE")
    if working_diff:
        fail("TRACKED_WORKTREE_MODIFICATION_PRESENT")
    if cached_diff:
        fail("STAGED_INDEX_CHANGE_PRESENT")
    if len(status_lines) != len(set(status_lines)):
        fail("DUPLICATE_STATUS_ENTRY")
    if not tracked_candidate:
        if ordinary_untracked != expected:
            fail("ORDINARY_UNTRACKED_NOT_STRICT_EXACT7")
        if set(status_lines) != {"?? " + path for path in expected}:
            fail("CANDIDATE_STATUS_NOT_STRICT_EXACT7")
        return CANDIDATE_UNTRACKED
    if ordinary_untracked or status_lines:
        fail("TRACKED_CLEAN_STATE_DIRTY")
    return TRACKED_CLEAN


def validate_repository_relation_values(
    *,
    profile: str,
    expected_paths: set[str],
    head: str,
    origin_main: str,
    ahead: int,
    behind: int,
    baseline_is_ancestor_of_head: bool,
    baseline_is_ancestor_of_origin: bool,
    origin_is_ancestor_of_head: bool,
    changed_since_baseline: set[str],
) -> None:
    if profile == CANDIDATE_UNTRACKED:
        if not (
            head == BASELINE_HEAD
            and origin_main == BASELINE_HEAD
            and (ahead, behind) == (0, 0)
            and baseline_is_ancestor_of_head
            and baseline_is_ancestor_of_origin
            and origin_is_ancestor_of_head
            and not changed_since_baseline
        ):
            fail("CANDIDATE_BASELINE_RELATION_INVALID")
        return
    if profile != TRACKED_CLEAN:
        fail("REPOSITORY_PROFILE_INVALID")
    missing_candidate_paths = expected_paths - changed_since_baseline
    if (
        not baseline_is_ancestor_of_head
        or not baseline_is_ancestor_of_origin
        or not origin_is_ancestor_of_head
        or head == BASELINE_HEAD
        or behind != 0
        or ahead < 0
        or missing_candidate_paths
    ):
        fail("TRACKED_CLEAN_PUBLICATION_SCOPE_INVALID")
    if (ahead == 0) != (origin_main == head):
        fail("TRACKED_CLEAN_ORIGIN_RELATION_INVALID")


def verify_repository_relation(profile: str, expected_paths: set[str]) -> None:
    head = run_git("rev-parse", "HEAD")
    origin_main = run_git("rev-parse", "origin/main")
    relation = run_git(
        "rev-list", "--left-right", "--count", "HEAD...origin/main"
    ).split()
    if len(relation) != 2 or any(not item.isdigit() for item in relation):
        fail("REPOSITORY_RELATION_INVALID")
    ahead, behind = (int(item) for item in relation)
    changed_since_baseline: set[str] = set()
    if profile == TRACKED_CLEAN:
        ancestry: list[bool] = []
        for older, newer in (
            (BASELINE_HEAD, "HEAD"),
            (BASELINE_HEAD, "origin/main"),
            ("origin/main", "HEAD"),
        ):
            try:
                run_git("merge-base", "--is-ancestor", older, newer)
            except SystemExit:
                ancestry.append(False)
            else:
                ancestry.append(True)
        (
            baseline_is_ancestor_of_head,
            baseline_is_ancestor_of_origin,
            origin_is_ancestor_of_head,
        ) = ancestry
        changed_since_baseline = set(
            filter(
                None,
                run_git("diff", "--name-only", BASELINE_HEAD + "..HEAD").splitlines(),
            )
        )
    else:
        baseline_is_ancestor_of_head = True
        baseline_is_ancestor_of_origin = True
        origin_is_ancestor_of_head = True
    validate_repository_relation_values(
        profile=profile,
        expected_paths=expected_paths,
        head=head,
        origin_main=origin_main,
        ahead=ahead,
        behind=behind,
        baseline_is_ancestor_of_head=baseline_is_ancestor_of_head,
        baseline_is_ancestor_of_origin=baseline_is_ancestor_of_origin,
        origin_is_ancestor_of_head=origin_is_ancestor_of_head,
        changed_since_baseline=changed_since_baseline,
    )


def observed_cer_candidate_paths() -> set[str]:
    paths = [
        *(REPO_ROOT / "src/covalent_ext").glob(
            "covapie_cer_completed_decision_ingestion_and_task_label_availability_v1.py"
        ),
        *(REPO_ROOT / "scripts").glob(
            "check_covapie_cer_completed_decision_ingestion_and_task_label_availability_v1.py"
        ),
        *(REPO_ROOT / "tests").glob(
            "test_covapie_cer_completed_decision_ingestion_and_task_label_availability_v1.py"
        ),
    ]
    output_root = REPO_ROOT / owner.OUTPUT_ROOT_RELATIVE
    if output_root.is_dir() and not output_root.is_symlink():
        paths.extend(output_root.iterdir())
    return {path.relative_to(REPO_ROOT).as_posix() for path in paths}


def check_candidate_inventory() -> tuple[list[dict[str, object]], str]:
    expected = tuple(path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS)
    expected_set = set(expected)
    if observed_cer_candidate_paths() != expected_set:
        fail("CER_CANDIDATE_FILESET_NOT_EXACT7")
    tracked = set(filter(None, run_git("ls-files").splitlines()))
    ordinary_untracked = set(
        filter(
            None,
            run_git("ls-files", "--others", "--exclude-standard").splitlines(),
        )
    )
    status_lines = tuple(
        filter(
            None,
            run_git("status", "--short", "--untracked-files=all").splitlines(),
        )
    )
    working_diff = set(filter(None, run_git("diff", "--name-only").splitlines()))
    cached_diff = set(
        filter(None, run_git("diff", "--cached", "--name-only").splitlines())
    )
    profile = classify_repository_profile(
        expected_paths=expected,
        tracked_paths=tracked,
        ordinary_untracked=ordinary_untracked,
        status_lines=status_lines,
        working_diff=working_diff,
        cached_diff=cached_diff,
    )
    verify_repository_relation(profile, expected_set)
    if any(Path(path).suffix.lower() in FORBIDDEN_SUFFIXES for path in expected):
        fail("FORBIDDEN_CANDIDATE_SUFFIX")
    if any(
        path in PROTECTED_FILES
        or any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES)
        for path in expected
    ):
        fail("PROTECTED_CANDIDATE_PATH")
    if any(
        word in path for path in expected
        for word in ("reconciliation", "census_refresh", "queue_refresh")
    ):
        fail("FORBIDDEN_ADJACENT_ARTIFACT_IN_CANDIDATE")
    records = [check_text_file(path) for path in expected]
    return records, profile


MappingLike = dict[str, object]


def binding_path(record: MappingLike) -> Path:
    relative = Path(str(record["path"]))
    if relative.is_absolute() or ".." in relative.parts:
        fail("BOUND_PATH_INVALID")
    namespace = record["namespace"]
    if namespace == "repository_relative":
        return REPO_ROOT / relative
    if namespace == "project_parent_relative":
        return REPO_ROOT.parent / relative
    fail("BOUND_NAMESPACE_INVALID")


def verify_binding_records(records: object, expected_count: int) -> None:
    if type(records) is not list or len(records) != expected_count:
        fail("BOUND_RECORD_COUNT_INVALID")
    for record in records:
        if type(record) is not dict:
            fail("BOUND_RECORD_INVALID")
        if set(record) != {
            "path", "namespace", "byte_count", "SHA256",
            "expected_executable_class", "source_role",
        }:
            fail("BOUND_RECORD_SHAPE_INVALID")
        expected_class = record["expected_executable_class"]
        if expected_class not in {"EXECUTABLE", "NON_EXECUTABLE"}:
            fail("BOUND_EXECUTABLE_CLASS_INVALID")
        try:
            verify_bound_source_v2(
                path=binding_path(record),
                expected_byte_count=int(record["byte_count"]),
                expected_sha256=str(record["SHA256"]),
                label="CER_CHECKER_BOUND_SOURCE:" + str(record["source_role"]),
                expected_executable=expected_class == "EXECUTABLE",
            )
        except (SourceBindingPolicyV2Error, ValueError):
            fail("BOUND_SOURCE_VERIFICATION_FAILED:" + str(record["source_role"]))


def check_formal_validator_lifecycle() -> None:
    source = (REPO_ROOT / owner.SOURCE_RELATIVE).read_text(encoding="utf-8")
    tree = ast.parse(source, filename=owner.SOURCE_RELATIVE.as_posix())
    forbidden_imports = {"subprocess", "runpy", "importlib"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] in forbidden_imports for alias in node.names):
                fail("PRODUCTION_FORBIDDEN_IMPORT")
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in forbidden_imports:
                fail("PRODUCTION_FORBIDDEN_IMPORT_FROM")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in {
                "exec", "eval", "compile", "__import__",
            }:
                fail("PRODUCTION_DYNAMIC_EXECUTION_CALL")
    forbidden_tokens = (
        "execute_formal_validator", "_run_formal_validator",
        "subprocess_formal_validator",
    )
    if any(token in source for token in forbidden_tokens):
        fail("PRODUCTION_FORMAL_VALIDATOR_EXECUTION_HOOK")


def check_independent_semantics(artifacts: dict[str, bytes]) -> None:
    snapshot = json.loads(artifacts[owner.SNAPSHOT])
    summary = json.loads(artifacts[owner.SUMMARY])
    manifest = json.loads(artifacts[owner.MANIFEST])
    rows = list(
        csv.DictReader(io.StringIO(artifacts[owner.MATRIX].decode("utf-8")))
    )
    human = snapshot.get("human_authorization", {})
    if [human.get(key) for key in (
        "D1_task_relevance", "D2_chemistry", "D3_reactive_pair",
        "D4_role_candidate", "D5_training_use",
    )] != [
        "RELEVANT", "POSITIVE", "CONFIRM_OBSERVED_PAIR",
        "SELECT_CANDIDATE_3", "INCLUDE",
    ]:
        fail("SNAPSHOT_D1_D5_INVALID")
    provenance = snapshot.get("D6_provenance", {})
    if (
        provenance.get("D6_draft_origin") != "ASSISTANT_DRAFT_ACCEPTED_BY_HUMAN"
        or provenance.get("D6_human_reviewed_and_accepted") is not True
        or provenance.get("D6_human_authorized") is not True
        or provenance.get("D6_human_authored") is not False
        or provenance.get("formal_decision_authority_is_human") is not True
        or provenance.get("machine_scientific_authority_created") is not False
    ):
        fail("SNAPSHOT_D6_PROVENANCE_INVALID")
    role = snapshot.get("selected_role_partition", {})
    if (
        role.get("selected_role_candidate_index_0based") != 3
        or role.get("role_profile") != owner.EXPECTED_ROLE_PROFILE
        or role.get("warhead_role_atom_ids") != list(owner.WARHEAD_ROLE)
        or role.get("linker_atom_ids") != []
        or role.get("scaffold_atom_ids") != list(owner.SCAFFOLD_ROLE)
        or role.get("boundary_bonds") != list(owner.BOUNDARY_BONDS)
        or role.get("sample_level_authoritative") is not True
        or role.get("reusable") is not False
    ):
        fail("SNAPSHOT_ROLE_AUTHORITY_INVALID")
    if (
        len(rows) != 4
        or tuple(row["canonical_event_id"] for row in rows) != owner.EXPECTED_EVENT_IDS
        or tuple(int(row["scaleup_rank"]) for row in rows) != owner.EXPECTED_RANKS
    ):
        fail("MATRIX_EXACT4_INVALID")
    for row in rows:
        applicability = json.loads(row["canonical_task_applicability_json"])
        if (
            row["protein_reactive_atom"] != "SG"
            or row["ligand_reactive_atom"] != "C2"
            or row["reactive_pair_human_authoritative"] != "true"
            or row["role_partition_human_authoritative"] != "true"
            or row["direct_profile_applicable_task_ids_json"] != "[0,3,4]"
            or [item["task_id"] for item in applicability if item["structurally_applicable"]]
            != [0, 3, 4]
            or row["authoritative_task_labels_created"] != "false"
            or row["event_task_label_rows_materialized"] != "false"
            or row["human_training_use_disposition"] != "INCLUDE"
            or row["formal_training_admitted"] != "false"
            or row["training_materialization_allowed"] != "false"
            or row["PRE_status"] != owner.PRE_STATUS
            or row["PRE_topology_authority"] != "false"
            or row["POST_source_evidence_available"] != "true"
            or row["POST_geometry_training_authority"] != "false"
            or row["reusable_chemistry_authority"] != "false"
            or row["reusable_pair_rule_created"] != "false"
            or row["reusable_role_authority"] != "false"
        ):
            fail("MATRIX_AUTHORITY_BOUNDARY_INVALID")
    required_summary = {
        "event_count": 4,
        "human_review_completed_count": 4,
        "task_relevant_count": 4,
        "chemistry_positive_count": 4,
        "reactive_pair_human_authoritative_count": 4,
        "role_partition_human_authoritative_count": 4,
        "DIRECT_event_count": 4,
        "STRICT_event_count": 0,
        "training_use_INCLUDE_count": 4,
        "applicable_task_set_counts": {"[0,3,4]": 4},
        "PRE_topology_authority_count": 0,
        "POST_geometry_training_authority_count": 0,
        "formal_training_admitted_count": 0,
        "reusable_chemistry_authority_count": 0,
        "reusable_pair_authority_count": 0,
        "reusable_role_authority_count": 0,
        "INGESTION_COMPLETE": True,
        "RECONCILIATION": False,
        "CENSUS_REFRESH": False,
        "QUEUE_REFRESH": False,
        "READY_FOR_TRAINING": False,
    }
    if any(summary.get(key) != value for key, value in required_summary.items()):
        fail("SUMMARY_COUNTS_OR_BOUNDARY_INVALID")
    census = manifest.get("current_census_boundary", {})
    if [census.get(key) for key in (
        "completed_positive_event_count", "completed_positive_unit_count",
        "completed_event_count", "completed_unit_count",
        "unreviewed_event_count", "unreviewed_unit_count",
    )] != [99, 14, 127, 19, 211, 112]:
        fail("CURRENT_CENSUS_BASELINE_INVALID")
    if (
        manifest.get("candidate_publication_file_count") != 7
        or manifest.get("output_artifact_count") != 4
        or manifest.get("formal_semantics_independently_validated") is not True
        or manifest.get("frozen_formal_validator_imported") is not False
        or manifest.get("frozen_formal_validator_executed") is not False
        or manifest.get("numeric_POSIX_semantic_identity") is not False
        or manifest.get("new_human_authority_created_by_ingestion") is not False
        or manifest.get("projection_of_frozen_formal_human_authority") is not True
        or manifest.get("READY_FOR_TRAINING") is not False
        or manifest.get("MANIFEST_SELF_SHA256_PROHIBITED") is not True
    ):
        fail("MANIFEST_BOUNDARY_INVALID")
    verify_binding_records([manifest["formal_decision_binding"]], 1)
    verify_binding_records([manifest["formal_validator_binding"]], 1)
    verify_binding_records([manifest["source_binding_policy_binding"]], 1)
    verify_binding_records(manifest["semantic_owner_bindings"], 2)
    verify_binding_records(manifest["current_census_bindings"], 4)


def check_determinism(live: dict[str, bytes]) -> None:
    first = owner.build_artifacts_v1(REPO_ROOT)
    second = owner.build_artifacts_v1(REPO_ROOT)
    if live != first or first != second:
        fail("DETERMINISTIC_DOUBLE_BUILD_FAILED")
    with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
        first_root = Path(first_dir)
        second_root = Path(second_dir)
        first_written = owner.materialize_artifacts_v1(REPO_ROOT, output_root=first_root)
        second_written = owner.materialize_artifacts_v1(REPO_ROOT, output_root=second_root)
        for name in owner.OUTPUT_FILENAMES:
            if not (
                live[name]
                == first_written[name]
                == second_written[name]
                == (first_root / name).read_bytes()
                == (second_root / name).read_bytes()
            ):
                fail("TEMP_MATERIALIZATION_DRIFT:" + name)


def check_lifecycle_simulations(expected_paths: set[str]) -> dict[str, bool]:
    expected = tuple(sorted(expected_paths))
    expected_set = set(expected)
    future_successor_paths = {
        "src/covalent_ext/synthetic_future_reconciliation_v1.py",
        "data/derived/covalent_small/synthetic_future_census_v1.json",
    }
    candidate = classify_repository_profile(
        expected_paths=expected,
        tracked_paths=set(),
        ordinary_untracked=expected_set,
        status_lines=tuple("?? " + path for path in expected),
        working_diff=set(),
        cached_diff=set(),
    )
    tracked = classify_repository_profile(
        expected_paths=expected,
        tracked_paths=set(expected),
        ordinary_untracked=set(),
        status_lines=(),
        working_diff=set(),
        cached_diff=set(),
    )

    relation_facts: dict[str, object] = {
        "profile": TRACKED_CLEAN,
        "expected_paths": expected_set,
        "head": "synthetic-immediate-unpushed-publication",
        "origin_main": BASELINE_HEAD,
        "ahead": 1,
        "behind": 0,
        "baseline_is_ancestor_of_head": True,
        "baseline_is_ancestor_of_origin": True,
        "origin_is_ancestor_of_head": True,
        "changed_since_baseline": expected_set,
    }

    def relation_fails(**overrides: object) -> bool:
        facts = dict(relation_facts)
        facts.update(overrides)
        try:
            validate_repository_relation_values(**facts)  # type: ignore[arg-type]
        except SystemExit:
            return True
        return False

    classification_facts: dict[str, object] = {
        "expected_paths": expected,
        "tracked_paths": expected_set,
        "ordinary_untracked": set(),
        "status_lines": (),
        "working_diff": set(),
        "cached_diff": set(),
    }

    def classification_fails(**overrides: object) -> bool:
        facts = dict(classification_facts)
        facts.update(overrides)
        try:
            classify_repository_profile(**facts)  # type: ignore[arg-type]
        except SystemExit:
            return True
        return False

    validate_repository_relation_values(
        profile=CANDIDATE_UNTRACKED,
        expected_paths=expected_set,
        head=BASELINE_HEAD,
        origin_main=BASELINE_HEAD,
        ahead=0,
        behind=0,
        baseline_is_ancestor_of_head=True,
        baseline_is_ancestor_of_origin=True,
        origin_is_ancestor_of_head=True,
        changed_since_baseline=set(),
    )
    validate_repository_relation_values(**relation_facts)  # type: ignore[arg-type]
    validate_repository_relation_values(
        profile=TRACKED_CLEAN,
        expected_paths=expected_set,
        head="synthetic-immediate-publication",
        origin_main="synthetic-immediate-publication",
        ahead=0,
        behind=0,
        baseline_is_ancestor_of_head=True,
        baseline_is_ancestor_of_origin=True,
        origin_is_ancestor_of_head=True,
        changed_since_baseline=expected_set,
    )
    validate_repository_relation_values(
        profile=TRACKED_CLEAN,
        expected_paths=expected_set,
        head="synthetic-multi-commit-descendant",
        origin_main=BASELINE_HEAD,
        ahead=3,
        behind=0,
        baseline_is_ancestor_of_head=True,
        baseline_is_ancestor_of_origin=True,
        origin_is_ancestor_of_head=True,
        changed_since_baseline=expected_set,
    )
    validate_repository_relation_values(
        profile=TRACKED_CLEAN,
        expected_paths=expected_set,
        head="synthetic-future-successor-descendant",
        origin_main=BASELINE_HEAD,
        ahead=5,
        behind=0,
        baseline_is_ancestor_of_head=True,
        baseline_is_ancestor_of_origin=True,
        origin_is_ancestor_of_head=True,
        changed_since_baseline=expected_set | future_successor_paths,
    )
    validate_repository_relation_values(
        profile=TRACKED_CLEAN,
        expected_paths=expected_set,
        head="synthetic-reconciliation-local-descendant",
        origin_main="synthetic-cer-published-descendant",
        ahead=1,
        behind=0,
        baseline_is_ancestor_of_head=True,
        baseline_is_ancestor_of_origin=True,
        origin_is_ancestor_of_head=True,
        changed_since_baseline=expected_set | future_successor_paths,
    )
    negative_relations = {
        "baseline_not_ancestor_of_head": relation_fails(
            baseline_is_ancestor_of_head=False
        ),
        "remote_rewind_before_baseline": relation_fails(
            baseline_is_ancestor_of_origin=False
        ),
        "origin_divergence": relation_fails(origin_is_ancestor_of_head=False),
        "behind_remote": relation_fails(behind=1),
        "missing_candidate": relation_fails(
            changed_since_baseline=(expected_set - {expected[0]})
            | future_successor_paths
        ),
    }
    dirty_states = {
        "mixed": classification_fails(
            tracked_paths={expected[0]},
            ordinary_untracked=set(expected[1:]),
            status_lines=tuple("?? " + path for path in expected[1:]),
        ),
        "working": classification_fails(working_diff={expected[0]}),
        "staged": classification_fails(cached_diff={expected[0]}),
        "untracked": classification_fails(
            ordinary_untracked={"synthetic-unrelated.txt"},
            status_lines=("?? synthetic-unrelated.txt",),
        ),
    }
    if (
        candidate != CANDIDATE_UNTRACKED
        or tracked != TRACKED_CLEAN
        or not all(negative_relations.values())
        or not all(dirty_states.values())
    ):
        fail("LIFECYCLE_SIMULATION_INVALID")
    return {
        "candidate_untracked_simulation": True,
        "tracked_clean_simulation": True,
        "tracked_clean_immediate_committed_unpushed": True,
        "tracked_clean_immediate_pushed": True,
        "tracked_clean_allows_multiple_commits": True,
        "tracked_clean_allows_unrelated_successor_paths": True,
        "tracked_clean_allows_unpushed_successor_after_prior_publication": True,
        "tracked_clean_missing_candidate_path_fails": True,
        "tracked_clean_baseline_not_ancestor_of_head_fails": True,
        "tracked_clean_remote_rewind_before_baseline_fails": True,
        "tracked_clean_origin_divergence_fails": True,
        "tracked_clean_behind_remote_fails": True,
        "mixed_lifecycle_fail_closed": True,
        "dirty_state_fail_closed": True,
    }


def check_forbidden_files(expected_paths: set[str]) -> None:
    for relative in expected_paths:
        if Path(relative).suffix.lower() in FORBIDDEN_SUFFIXES:
            fail("FORBIDDEN_SUFFIX:" + relative)
        if (REPO_ROOT / relative).stat().st_size > 1024 * 1024:
            fail("UNEXPECTED_LARGE_CANDIDATE_FILE:" + relative)
    transient = [
        path
        for root in (
            REPO_ROOT / "src/covalent_ext",
            REPO_ROOT / "scripts",
            REPO_ROOT / "tests",
            REPO_ROOT / owner.OUTPUT_ROOT_RELATIVE,
        )
        if root.exists()
        for path in root.rglob("*")
        if path.is_file()
        and (
            path.suffix.lower() in FORBIDDEN_SUFFIXES
            or "__pycache__" in path.parts
        )
    ]
    if transient:
        fail("TRANSIENT_OR_FORBIDDEN_FILE_PRESENT")


def main() -> int:
    candidate_records, repository_profile = check_candidate_inventory()
    expected_paths = {path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS}
    check_forbidden_files(expected_paths)
    check_formal_validator_lifecycle()
    owner_report = owner.check_materialized_v1(REPO_ROOT)
    live = {
        name: (REPO_ROOT / owner.OUTPUT_ROOT_RELATIVE / name).read_bytes()
        for name in owner.OUTPUT_FILENAMES
    }
    owner.validate_completed_decision_projection_v1(live, repo_root=REPO_ROOT)
    check_independent_semantics(live)
    check_determinism(live)
    lifecycle = check_lifecycle_simulations(expected_paths)
    result = {
        "status": "PASS",
        "schema_version": owner.SCHEMA_VERSION,
        "repository_profile": repository_profile,
        "candidate_exact_file_count": 7,
        "candidate_files": candidate_records,
        "output_exact_file_count": 4,
        "event_count": 4,
        "formal_semantics_independently_validated": True,
        "formal_validator_provenance_identity_only": True,
        "formal_validator_imported": False,
        "formal_validator_executed": False,
        "formal_validator_subprocess_called": False,
        "deterministic_double_build": True,
        "tracked_modifications": 0,
        "staged_changes": 0,
        "ordinary_untracked_strict_exact7": repository_profile == CANDIDATE_UNTRACKED,
        "protected_source_diffs": 0,
        "forbidden_new_files": 0,
        "RECONCILIATION": False,
        "CENSUS_REFRESH": False,
        "QUEUE_REFRESH": False,
        "TRAINING_STARTED": False,
        "READY_FOR_TRAINING": False,
        "lifecycle": lifecycle,
        "owner_check": owner_report,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("PASS")
    print(repository_profile)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
