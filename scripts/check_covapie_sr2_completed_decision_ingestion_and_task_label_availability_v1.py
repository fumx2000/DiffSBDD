#!/usr/bin/env python3
"""Fail-closed repository checker for the SR2 ingestion Exact7."""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
from pathlib import Path
import stat
import subprocess
import sys
from typing import Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_sr2_completed_decision_ingestion_and_task_label_availability_v1
    as owner,
)
from covalent_ext.covapie_source_binding_policy_v2 import (  # noqa: E402
    SourceBindingPolicyV2Error,
    verify_bound_source_v2,
)


ERROR = "COVAPIE_SR2_INGESTION_CHECK_FAILED"
BASELINE_HEAD = "362c469b98bcd49d7ac0e4acfa99d2a2bae0f1dd"
CANDIDATE_UNTRACKED = "CANDIDATE_UNTRACKED"
TRACKED_CLEAN = "TRACKED_CLEAN"
FORBIDDEN_SUFFIXES = (
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz",
    ".npz", ".tmp", ".part", ".pyc", ".log",
)
PROTECTED_PREFIXES = (
    "data/raw/", "checkpoints/", "equivariant_diffusion/", "covapie-state/",
)
PROTECTED_FILES = {"lightning_modules.py", "dataset.py", "data/prepare_crossdocked.py"}


def fail(reason: str) -> None:
    raise SystemExit(ERROR + ":" + reason)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def strict_json(payload: bytes, label: str) -> dict[str, object]:
    if payload.startswith(b"\xef\xbb\xbf"):
        fail("JSON_BOM:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        fail("JSON_UTF8:" + label)

    def pairs_hook(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                fail("JSON_DUPLICATE_KEY:" + label + ":" + key)
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        fail("JSON_NONFINITE:" + label + ":" + value)

    try:
        result = json.loads(
            text, object_pairs_hook=pairs_hook, parse_constant=reject_constant
        )
    except json.JSONDecodeError:
        fail("JSON_PARSE:" + label)
    if type(result) is not dict:
        fail("JSON_ROOT:" + label)
    return result


def run_git(*arguments: str) -> str:
    allowed = {"branch", "diff", "ls-files", "merge-base", "rev-list", "rev-parse"}
    if not arguments or arguments[0] not in allowed:
        fail("GIT_SUBCOMMAND_FORBIDDEN")
    result = subprocess.run(
        ("git", *arguments), cwd=REPO_ROOT, check=False,
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        fail("GIT_COMMAND_FAILED:" + arguments[0])
    return result.stdout.rstrip("\n")


def check_text_file(relative: str) -> dict[str, object]:
    path = REPO_ROOT / relative
    try:
        metadata = path.lstat()
        payload = path.read_bytes()
    except OSError:
        fail("CANDIDATE_READ_FAILED:" + relative)
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        fail("CANDIDATE_NOT_REGULAR:" + relative)
    if metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
        fail("CANDIDATE_EXECUTABLE:" + relative)
    if (
        not payload or len(payload) >= 1024 * 1024
        or payload.startswith(b"\xef\xbb\xbf") or b"\x00" in payload
        or b"\r" in payload or not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
    ):
        fail("TEXT_HYGIENE_INVALID:" + relative)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        fail("UTF8_INVALID:" + relative)
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        fail("TRAILING_WHITESPACE:" + relative)
    try:
        verified = verify_bound_source_v2(
            path=path,
            expected_byte_count=len(payload),
            expected_sha256=sha256(payload),
            label="SR2_CANDIDATE:" + relative,
            expected_executable=False,
        )
    except SourceBindingPolicyV2Error:
        fail("CANDIDATE_SECURITY_FAILED:" + relative)
    if verified != payload:
        fail("CANDIDATE_UNSTABLE:" + relative)
    return {"path": relative, "byte_count": len(payload), "SHA256": sha256(payload)}


def classify_repository_profile(
    *,
    head: str,
    origin: str,
    tracked_modifications: set[str],
    staged_paths: set[str],
    untracked_paths: set[str],
    expected_paths: set[str],
) -> str:
    if tracked_modifications or staged_paths:
        fail("WORKTREE_OR_INDEX_NOT_CLEAN")
    if untracked_paths == expected_paths:
        if head != BASELINE_HEAD or origin != BASELINE_HEAD:
            fail("CANDIDATE_UNTRACKED_BASELINE_DRIFT")
        return CANDIDATE_UNTRACKED
    if not untracked_paths:
        return TRACKED_CLEAN
    fail("ORDINARY_UNTRACKED_INVENTORY_NOT_EXACT7")


def validate_repository_relation_values(
    *,
    profile: str,
    head: str,
    origin: str,
    ahead: int,
    behind: int,
    baseline_ancestor_of_head: bool,
    baseline_ancestor_of_origin: bool,
    origin_ancestor_of_head: bool,
    changed_paths: set[str],
    expected_paths: set[str],
) -> None:
    if profile == CANDIDATE_UNTRACKED:
        if (
            head != BASELINE_HEAD or origin != BASELINE_HEAD
            or ahead != 0 or behind != 0 or changed_paths
        ):
            fail("CANDIDATE_UNTRACKED_RELATION_INVALID")
        return
    if profile != TRACKED_CLEAN:
        fail("REPOSITORY_PROFILE_INVALID")
    if (
        not baseline_ancestor_of_head or not baseline_ancestor_of_origin
        or not origin_ancestor_of_head or behind != 0
        or not expected_paths.issubset(changed_paths)
    ):
        fail("TRACKED_CLEAN_RELATION_INVALID")
    if ahead < 0 or (head == origin and ahead != 0) or (head != origin and ahead < 1):
        fail("TRACKED_CLEAN_AHEAD_INVALID")


def _merge_base_is_ancestor(older: str, newer: str) -> bool:
    result = subprocess.run(
        ("git", "merge-base", "--is-ancestor", older, newer),
        cwd=REPO_ROOT, check=False, capture_output=True, text=True,
    )
    if result.returncode not in (0, 1):
        fail("GIT_ANCESTRY_FAILED")
    return result.returncode == 0


def check_candidate_inventory() -> tuple[list[dict[str, object]], str]:
    expected_order = [path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS]
    expected = set(expected_order)
    if run_git("branch", "--show-current") != "main":
        fail("BRANCH_NOT_MAIN")
    head = run_git("rev-parse", "HEAD")
    origin = run_git("rev-parse", "origin/main")
    tracked = set(filter(None, run_git("diff", "--name-only").splitlines()))
    staged = set(filter(None, run_git("diff", "--cached", "--name-only").splitlines()))
    untracked = set(
        filter(None, run_git("ls-files", "--others", "--exclude-standard").splitlines())
    )
    profile = classify_repository_profile(
        head=head,
        origin=origin,
        tracked_modifications=tracked,
        staged_paths=staged,
        untracked_paths=untracked,
        expected_paths=expected,
    )
    counts = run_git("rev-list", "--left-right", "--count", "origin/main...HEAD").split()
    if len(counts) != 2:
        fail("AHEAD_BEHIND_PARSE_FAILED")
    behind, ahead = map(int, counts)
    changed = set(
        filter(None, run_git("diff", "--name-only", BASELINE_HEAD + "..HEAD").splitlines())
    )
    validate_repository_relation_values(
        profile=profile,
        head=head,
        origin=origin,
        ahead=ahead,
        behind=behind,
        baseline_ancestor_of_head=_merge_base_is_ancestor(BASELINE_HEAD, head),
        baseline_ancestor_of_origin=_merge_base_is_ancestor(BASELINE_HEAD, origin),
        origin_ancestor_of_head=_merge_base_is_ancestor(origin, head),
        changed_paths=changed,
        expected_paths=expected,
    )
    if profile == TRACKED_CLEAN:
        tracked_candidate = set(
            filter(None, run_git("ls-files", "--", *expected_order).splitlines())
        )
        if tracked_candidate != expected:
            fail("TRACKED_CLEAN_EXACT7_NOT_TRACKED")
    return [check_text_file(relative) for relative in expected_order], profile


def check_formal_validator_lifecycle() -> None:
    source = (REPO_ROOT / owner.SOURCE_RELATIVE).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_module = "validate_sr2_formal_human_decision_v1"
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(forbidden_module in alias.name for alias in node.names):
                fail("FORMAL_VALIDATOR_IMPORTED")
        elif isinstance(node, ast.ImportFrom):
            if forbidden_module in (node.module or "") or any(
                forbidden_module in alias.name for alias in node.names
            ):
                fail("FORMAL_VALIDATOR_IMPORTED")
        elif isinstance(node, ast.Call):
            for child in ast.walk(node):
                if (
                    isinstance(child, ast.Constant)
                    and isinstance(child.value, str)
                    and forbidden_module in child.value
                ):
                    fail("FORMAL_VALIDATOR_CALL_PRESENT")
    if "import subprocess" in source or "from subprocess" in source:
        fail("OWNER_SUBPROCESS_DEPENDENCY_FORBIDDEN")
    bound = owner.load_frozen_formal_decision_v1(REPO_ROOT)
    if (
        bound["formal_validator_provenance_identity_only"] is not True
        or bound["formal_validator_imported"] is not False
        or bound["formal_validator_executed"] is not False
        or bound["formal_validator_subprocess_called"] is not False
        or bound["formal_validator_runtime_dependency"] is not False
    ):
        fail("FORMAL_VALIDATOR_LIFECYCLE_PROJECTION_INVALID")


def check_frozen_formal_independently() -> None:
    decision_path = REPO_ROOT.parent / owner.FORMAL_DECISION_RELATIVE
    validator_path = REPO_ROOT.parent / owner.FORMAL_VALIDATOR_RELATIVE
    for path, expected_bytes, expected_sha, label in (
        (
            decision_path,
            34106,
            "b41c84d6519efce267410d5e95b017366c9b5b8820a6f5878c9a893404b6defa",
            "FORMAL_JSON",
        ),
        (
            validator_path,
            86374,
            "5526d2205c5cc2da494e0263d33d2bf5a275fa9c5e18d51c3b3e1ec918b89e57",
            "FORMAL_VALIDATOR",
        ),
    ):
        payload = path.read_bytes()
        if len(payload) != expected_bytes or sha256(payload) != expected_sha:
            fail(label + "_IDENTITY_DRIFT")
    formal = strict_json(decision_path.read_bytes(), "FORMAL_JSON")
    clone = dict(formal)
    literal = clone.pop("formal_decision_semantic_canonical_sha256", None)
    digest = sha256(
        json.dumps(
            clone, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
    )
    if literal != owner.FORMAL_SEMANTIC_CANONICAL_SHA256 or digest != literal:
        fail("FORMAL_SEMANTIC_DIGEST_INVALID")
    owner._validate_formal_document(formal)


def check_current_census_independently() -> None:
    matrix_path = REPO_ROOT / owner.CENSUS_MATRIX_RELATIVE
    before = matrix_path.read_bytes()
    rows = list(csv.DictReader(io.StringIO(before.decode("utf-8"))))
    target = [row for row in rows if row["canonical_event_id"] in owner.EXPECTED_EVENT_IDS]
    if (
        len(rows) != 1000
        or tuple(row["canonical_event_id"] for row in target) != owner.EXPECTED_EVENT_IDS
        or tuple(int(row["scaleup_rank"]) for row in target) != owner.EXPECTED_RANKS
    ):
        fail("CURRENT_CENSUS_SR2_IDENTITY_INVALID")
    for row in target:
        if (
            row["current_global_status"] != "CURRENTLY_UNREVIEWED"
            or row["current_review_status"] != "CURRENTLY_UNREVIEWED"
            or row["human_review_completed"] != "false"
            or row["chemistry_disposition"] != "UNRESOLVED"
            or row["task_relevance_disposition"] != "UNRESOLVED"
            or row["training_use_disposition"] != "UNRESOLVED"
            or row["formal_training_admitted"] != "false"
        ):
            fail("CURRENT_CENSUS_SR2_PRIOR_STATE_INVALID")
    if matrix_path.read_bytes() != before:
        fail("CURRENT_CENSUS_CHANGED_DURING_CHECK")


def check_structural_graph_independently() -> None:
    path = REPO_ROOT.parent / owner.STRUCTURAL_GRAPH_RELATIVE
    payload = path.read_bytes()
    if (
        len(payload) != 142747
        or sha256(payload)
        != "a370deed014ec8a304b74ea0120e0c3615e72a4f391f8854c96e6a4284290ea4"
    ):
        fail("STRUCTURAL_GRAPH_IDENTITY_INVALID")
    graph = strict_json(payload, "STRUCTURAL_GRAPH")
    atom_ids = tuple(row["atom_id"] for row in graph["heavy_atoms"])
    bonds = tuple(
        (row["atom_id_1"], row["atom_id_2"], row["bond_order"])
        for row in graph["heavy_bonds"]
    )
    candidate = graph["full_candidate_inventory"][15]
    if (
        atom_ids != owner.HEAVY_ATOMS or bonds != owner.HEAVY_BONDS
        or candidate["index_0based"] != 15
        or candidate["profile"] != owner.EXPECTED_ROLE_PROFILE
        or candidate["W"] != list(owner.WARHEAD_ROLE)
        or candidate["L"] != []
        or candidate["S"] != list(owner.SCAFFOLD_ROLE)
        or candidate["boundary_bonds"] != list(owner.BOUNDARY_BONDS)
        or candidate["applicable_task_ids"] != [0, 3, 4]
        or candidate["human_selected"] is not False
        or candidate["machine_selected"] is not False
    ):
        fail("STRUCTURAL_GRAPH_CANDIDATE15_INVALID")
    owner._validate_structural_graph(payload)


def check_independent_projection(artifacts: Mapping[str, bytes]) -> None:
    snapshot = strict_json(artifacts[owner.SNAPSHOT], "SNAPSHOT")
    summary = strict_json(artifacts[owner.SUMMARY], "SUMMARY")
    manifest = strict_json(artifacts[owner.MANIFEST], "MANIFEST")
    rows = list(csv.DictReader(io.StringIO(artifacts[owner.MATRIX].decode("utf-8"))))
    if (
        snapshot["completed_lane"] != owner.EXPECTED_COMPLETED_LANE
        or snapshot["task_relevance"] != "RELEVANT"
        or snapshot["chemistry"] != "POSITIVE"
        or snapshot["human_training_excluded"] is not False
        or snapshot["future_training_admission_candidate"] is not True
        or snapshot["training_eligibility"] is not False
        or len(rows) != 4
    ):
        fail("SNAPSHOT_HIGH_LEVEL_BOUNDARY_INVALID")
    required_false = (
        "human_training_excluded", "training_admitted", "formal_training_admitted",
        "training_materialization_allowed_now", "training_materialization_allowed",
        "tensor_target_created", "model_supervision_usable",
        "training_mask_targets_available_now", "current_runtime_model_usable",
        "parameter_update_authorization", "READY_FOR_TRAINING",
        "POST_geometry_training_authority", "POST_geometry_training_target_created",
        "POST_geometry_training_label_available_now",
        "dataset_mutated", "training_dataset_changed", "tensorization_performed",
        "loader_modified", "batch_modified", "model_forward", "loss", "backward",
        "optimizer", "parameter_update", "training",
    )
    for row in rows:
        if (
            row["completed_lane"] != owner.EXPECTED_COMPLETED_LANE
            or row["task_relevance"] != "RELEVANT"
            or row["chemistry"] != "POSITIVE"
            or row["formal_event_training_use_decision"] != owner.TRAINING_USE_DECISION
            or row["training_use_allowed"] != "true"
            or row["candidate_for_future_training_admission"] != "true"
            or row["future_training_admission_candidate"] != "true"
            or row["future_training_admission_status"] != owner.FUTURE_STATUS
            or row["metadata_only"] != "true"
            or any(row[field] != "false" for field in required_false)
        ):
            fail("MATRIX_FUTURE_CANDIDATE_NON_ADMISSION_INVALID")
    if (
        summary["human_training_excluded_event_count"] != 0
        or summary["training_use_allowed_event_count"] != 4
        or summary["future_training_admission_candidate_count"] != 4
        or summary["formal_training_admitted_count"] != 0
        or summary["tensor_target_created_event_count"] != 0
        or summary["READY_FOR_TRAINING"] is not False
    ):
        fail("SUMMARY_FUTURE_CANDIDATE_NON_ADMISSION_INVALID")
    if (
        manifest["frozen_formal_validator_provenance_identity_only"] is not True
        or manifest["frozen_formal_validator_imported"] is not False
        or manifest["frozen_formal_validator_executed"] is not False
        or manifest["frozen_formal_validator_subprocess_called"] is not False
        or manifest["formal_validator_runtime_dependency"] is not False
        or manifest["NEVER_IMPORT_FORMAL_VALIDATOR"] is not True
        or manifest["NEVER_EXECUTE_FORMAL_VALIDATOR"] is not True
        or manifest["manifest_self_SHA256_recorded"] is not False
    ):
        fail("MANIFEST_LIFECYCLE_INVALID")
    bindings = manifest["output_artifact_bindings"]
    for name in (owner.SNAPSHOT, owner.MATRIX, owner.SUMMARY):
        record = bindings[name]
        if (
            record["byte_count"] != len(artifacts[name])
            or record["SHA256"] != sha256(artifacts[name])
        ):
            fail("OUTPUT_BINDING_INVALID:" + name)
    for record in manifest["candidate_source_bindings"]:
        payload = (REPO_ROOT / record["path"]).read_bytes()
        if record["byte_count"] != len(payload) or record["SHA256"] != sha256(payload):
            fail("CANDIDATE_SOURCE_BINDING_INVALID:" + record["path"])


def check_determinism(live: Mapping[str, bytes]) -> None:
    first = owner.build_artifacts_v1(REPO_ROOT)
    second = owner.build_artifacts_v1(REPO_ROOT)
    if first != second or dict(live) != first:
        fail("DOUBLE_BUILD_NOT_BYTE_IDENTICAL")


def check_lifecycle_simulations(expected_paths: set[str]) -> dict[str, bool]:
    cases = (
        {
            "profile": TRACKED_CLEAN,
            "head": "1" * 40,
            "origin": BASELINE_HEAD,
            "ahead": 1,
            "behind": 0,
            "baseline_ancestor_of_head": True,
            "baseline_ancestor_of_origin": True,
            "origin_ancestor_of_head": True,
            "changed_paths": expected_paths,
        },
        {
            "profile": TRACKED_CLEAN,
            "head": "2" * 40,
            "origin": "2" * 40,
            "ahead": 0,
            "behind": 0,
            "baseline_ancestor_of_head": True,
            "baseline_ancestor_of_origin": True,
            "origin_ancestor_of_head": True,
            "changed_paths": expected_paths,
        },
        {
            "profile": TRACKED_CLEAN,
            "head": "3" * 40,
            "origin": "2" * 40,
            "ahead": 3,
            "behind": 0,
            "baseline_ancestor_of_head": True,
            "baseline_ancestor_of_origin": True,
            "origin_ancestor_of_head": True,
            "changed_paths": expected_paths | {"docs/later-unrelated.md"},
        },
    )
    for case in cases:
        validate_repository_relation_values(expected_paths=expected_paths, **case)
    rejected = 0
    for mutation in (
        {"behind": 1}, {"origin_ancestor_of_head": False},
        {"baseline_ancestor_of_origin": False}, {"changed_paths": set()},
    ):
        case = dict(cases[-1])
        case.update(mutation)
        try:
            validate_repository_relation_values(expected_paths=expected_paths, **case)
        except SystemExit:
            rejected += 1
    if rejected != 4:
        fail("LIFECYCLE_NEGATIVE_SIMULATION_FAILED")
    return {
        "immediate_committed_unpushed": True,
        "immediate_pushed": True,
        "multiple_later_commits": True,
        "unrelated_later_committed_paths": True,
        "origin_between_baseline_and_HEAD": True,
        "behind_rejected": True,
    }


def check_forbidden_files(expected_paths: set[str]) -> None:
    for relative in expected_paths:
        if relative.endswith(FORBIDDEN_SUFFIXES):
            fail("FORBIDDEN_CANDIDATE_SUFFIX:" + relative)
        if relative.startswith(PROTECTED_PREFIXES) or relative in PROTECTED_FILES:
            fail("PROTECTED_CANDIDATE_PATH:" + relative)
    forbidden_untracked = [
        path for path in run_git("ls-files", "--others", "--exclude-standard").splitlines()
        if path.endswith(FORBIDDEN_SUFFIXES)
    ]
    if forbidden_untracked:
        fail("FORBIDDEN_UNTRACKED_FILE")


def main() -> int:
    inventory, profile = check_candidate_inventory()
    expected_paths = {path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS}
    check_forbidden_files(expected_paths)
    check_formal_validator_lifecycle()
    check_frozen_formal_independently()
    check_structural_graph_independently()
    check_current_census_independently()
    live = {
        name: (REPO_ROOT / owner.OUTPUT_ROOT_RELATIVE / name).read_bytes()
        for name in owner.OUTPUT_FILENAMES
    }
    owner.validate_completed_decision_projection_v1(live, repo_root=REPO_ROOT)
    check_independent_projection(live)
    check_determinism(live)
    materialized = owner.check_materialized_v1(REPO_ROOT)
    lifecycle = check_lifecycle_simulations(expected_paths)
    result = {
        "status": "PASS",
        "repository_profile": profile,
        "candidate_file_count": len(inventory),
        "candidate_inventory": inventory,
        "event_count": 4,
        "scaleup_ranks": [321, 323, 337, 338],
        "completed_lane": owner.EXPECTED_COMPLETED_LANE,
        "formal_validator_executed": False,
        "formal_semantics_independently_validated": True,
        "double_build_byte_identical": True,
        "lifecycle_simulations": lifecycle,
        "SR2_INGESTION_CANDIDATE_PASS": True,
        "SR2_FORMAL_DECISION_BOUND": True,
        "SR2_FORMAL_VALIDATOR_PROVENANCE_ONLY": True,
        "SR2_FORMAL_SEMANTICS_INDEPENDENTLY_VALIDATED": True,
        "SR2_COMPLETED_DECISION_METADATA_PROJECTED": True,
        "SR2_TASK_RELEVANT": True,
        "SR2_CHEMISTRY_POSITIVE": True,
        "SR2_SAMPLE_SG_C51_AUTHORITY_AVAILABLE": True,
        "SR2_SAMPLE_ROLE_AUTHORITY_AVAILABLE": True,
        "D5_INCLUDE": True,
        "HUMAN_TRAINING_EXCLUDED": False,
        "FUTURE_TRAINING_ADMISSION_CANDIDATE": True,
        "FORMAL_TRAINING_ADMITTED": False,
        "TRAINING_ADMISSION_CREATED": False,
        "TRAINING_MATERIALIZATION_ALLOWED": False,
        "TENSOR_TARGET_CREATED": False,
        "CURRENT_RUNTIME_MODEL_USABLE": False,
        "PRE_REACTION_UNRESOLVED": True,
        "EXACT5_B3_PRESENT": True,
        "SIXTH_TASK": False,
        "REUSABLE_C51_AUTHORITY": False,
        "REACTION_FAMILY_AUTHORITY": False,
        "WARHEAD_RULE_AUTHORITY": False,
        "WARHEAD_TYPE_AUTHORITY": False,
        "READY_FOR_EXTERNAL_REVIEW": True,
        "RECONCILIATION": False,
        "CENSUS_REFRESH": False,
        "QUEUE_REFRESH": False,
        "TRAINING_STARTED": False,
        "READY_FOR_TRAINING": False,
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER": True,
        "COMMIT": False,
        "PUSH": False,
        "materialized_check": materialized,
    }
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
