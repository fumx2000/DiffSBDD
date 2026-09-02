#!/usr/bin/env python3
"""Fail-closed checker for the 4M5 completed-decision ingestion Exact7."""

from __future__ import annotations

import ast
import copy
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
    covapie_4m5_completed_decision_ingestion_and_task_label_availability_v1
    as owner,
)
from covalent_ext.covapie_source_binding_policy_v2 import (  # noqa: E402
    SourceBindingPolicyV2Error,
    verify_bound_source_v2,
)


ERROR = "COVAPIE_4M5_INGESTION_CHECK_FAILED"
BASELINE_HEAD = "4b59e3a1a9cd07cfb48c19df4ac50de740dc98a9"
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
            label="FOUR_M5_EXACT7:" + relative,
            expected_executable=False,
        )
    except SourceBindingPolicyV2Error:
        fail("CANDIDATE_SECURITY_OR_EXECUTABLE_CLASS_INVALID:" + relative)
    if verified != payload:
        fail("CANDIDATE_UNSTABLE:" + relative)
    return {
        "path": relative,
        "byte_count": len(payload),
        "LOC": len(text.splitlines()),
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
    if (
        not baseline_is_ancestor_of_head
        or not baseline_is_ancestor_of_origin
        or not origin_is_ancestor_of_head
        or head == BASELINE_HEAD
        or behind != 0
        or ahead < 0
        or not expected_paths <= changed_since_baseline
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
            result = subprocess.run(
                ("git", "merge-base", "--is-ancestor", older, newer),
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            ancestry.append(result.returncode == 0)
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


def observed_candidate_paths() -> set[str]:
    paths = [
        *(REPO_ROOT / "src/covalent_ext").glob(
            "covapie_4m5_completed_decision_ingestion_and_task_label_availability_v1.py"
        ),
        *(REPO_ROOT / "scripts").glob(
            "check_covapie_4m5_completed_decision_ingestion_and_task_label_availability_v1.py"
        ),
        *(REPO_ROOT / "tests").glob(
            "test_covapie_4m5_completed_decision_ingestion_and_task_label_availability_v1.py"
        ),
    ]
    output_root = REPO_ROOT / owner.OUTPUT_ROOT_RELATIVE
    if output_root.is_dir() and not output_root.is_symlink():
        paths.extend(output_root.iterdir())
    return {path.relative_to(REPO_ROOT).as_posix() for path in paths}


def check_candidate_inventory() -> tuple[list[dict[str, object]], str]:
    expected = tuple(path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS)
    expected_set = set(expected)
    if observed_candidate_paths() != expected_set:
        fail("FOUR_M5_CANDIDATE_FILESET_NOT_EXACT7")
    tracked = set(filter(None, run_git("ls-files").splitlines()))
    ordinary_untracked = set(
        filter(None, run_git("ls-files", "--others", "--exclude-standard").splitlines())
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
                label="FOUR_M5_CHECKER_BOUND:" + str(record["source_role"]),
                expected_executable=expected_class == "EXECUTABLE",
            )
        except (SourceBindingPolicyV2Error, ValueError):
            fail("BOUND_SOURCE_VERIFICATION_FAILED:" + str(record["source_role"]))


def check_formal_validator_lifecycle() -> None:
    source = (REPO_ROOT / owner.SOURCE_RELATIVE).read_text(encoding="utf-8")
    tree = ast.parse(source, filename=owner.SOURCE_RELATIVE.as_posix())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] in {"subprocess", "runpy"} for alias in node.names):
                fail("PRODUCTION_FORBIDDEN_IMPORT")
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] in {"subprocess", "runpy"}:
                fail("PRODUCTION_FORBIDDEN_IMPORT_FROM")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in {
                "exec", "eval", "compile", "__import__",
            }:
                fail("PRODUCTION_DYNAMIC_EXECUTION_CALL")
            if (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "importlib"
                and node.func.attr == "import_module"
            ):
                if (
                    len(node.args) != 1
                    or not isinstance(node.args[0], ast.Constant)
                    or node.args[0].value
                    != "covalent_ext.covapie_direct_attachment_optional_linker_runtime_v1"
                ):
                    fail("PRODUCTION_IMPORTLIB_TARGET_INVALID")
    forbidden_tokens = (
        "execute_formal_validator", "_run_formal_validator",
        "subprocess_formal_validator",
        "covalent_ext.validate_4m5_formal_human_decision_v1",
    )
    if any(token in source for token in forbidden_tokens):
        fail("PRODUCTION_FORMAL_VALIDATOR_EXECUTION_HOOK")
    if any(
        name.startswith("validate_4m5_formal_human_decision_v1")
        for name in sys.modules
    ):
        fail("FORMAL_VALIDATOR_IMPORTED")


def check_frozen_formal_independently() -> None:
    formal_path = REPO_ROOT.parent / owner.FORMAL_DECISION_RELATIVE
    validator_path = REPO_ROOT.parent / owner.FORMAL_VALIDATOR_RELATIVE
    formal_payload = formal_path.read_bytes()
    validator_payload = validator_path.read_bytes()
    if (
        len(formal_payload) != 29089
        or sha256(formal_payload)
        != "5e37540220ac44b281b20bfb796f5c2994d0ab402fb5f65acc03fb6f6b1febfb"
        or len(validator_payload) != 56100
        or sha256(validator_payload)
        != "098b0d783dc098632ebd7d67a4e3d74f9f61f96452c50b2e8d3cc14057bd3d84"
    ):
        fail("FROZEN_FORMAL_EXACT2_IDENTITY_INVALID")
    formal = strict_json(formal_payload, "FROZEN_FORMAL")
    recorded = formal.get("formal_semantic_canonical_sha256")
    clone = copy.deepcopy(formal)
    clone.pop("formal_semantic_canonical_sha256", None)
    recomputed = sha256(
        json.dumps(
            clone,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    )
    if (
        recorded
        != "c2a18158dd9c841f8022150edbf42de74b84016bb8566c112bd63aa1b3badfa9"
        or recomputed != recorded
        or formal.get("schema_version")
        != "covapie_4m5_exact4_formal_human_decision_v1"
        or formal.get("record_role")
        != "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY"
    ):
        fail("FORMAL_SEMANTIC_IDENTITY_INVALID")
    human = formal.get("human_authorization")
    if type(human) is not dict or [
        human.get("D1_task_relevance"),
        human.get("D2_chemistry"),
        human.get("D3_reactive_pair"),
        human.get("D4_role_candidate"),
        human.get("D5_training_use"),
    ] != [
        "RELEVANT", "POSITIVE", "CONFIRM_OBSERVED_PAIR",
        "SELECT_CANDIDATE_0", "INCLUDE",
    ]:
        fail("FORMAL_D1_D5_INVALID")
    d6 = human.get("D6_scientific_context")
    if (
        type(d6) is not str
        or len(d6.encode("utf-8")) != 699
        or sha256(d6.encode("utf-8"))
        != "21d0c0558174f2da548a1430333b639da273399bd020d2a64cde8a8e1511a254"
        or human.get("reviewer_id") != "fmx"
        or human.get("attestor_id") != "fmx"
        or human.get("authorization_origin") != "EXTERNAL_HUMAN_CHAT_AUTHORIZATION"
        or human.get("formal_decision_authority_is_human") is not True
        or human.get("human_choices_externally_authorized") is not True
        or human.get("machine_approval_claimed") is not False
        or human.get("machine_scientific_authority_created") is not False
    ):
        fail("FORMAL_D6_OR_HUMAN_PROVENANCE_INVALID")
    identity = formal.get("identity")
    events = formal.get("event_level_formal_human_decisions")
    if (
        type(identity) is not dict
        or identity.get("canonical_event_ids") != list(owner.EXPECTED_EVENT_IDS)
        or identity.get("scaleup_ranks") != [973, 974, 975, 976]
        or identity.get("pdb_ids") != ["5AZT", "5AZV"]
        or identity.get("contexts_collapsed") is not False
        or type(events) is not list
        or len(events) != 4
        or [row.get("canonical_event_id") for row in events]
        != list(owner.EXPECTED_EVENT_IDS)
        or len({row.get("canonical_event_id") for row in events}) != 4
    ):
        fail("FORMAL_EXACT4_IDENTITY_INVALID")
    role = formal.get("selected_role_partition")
    if (
        type(role) is not dict
        or role.get("D4_human_choice") != "SELECT_CANDIDATE_0"
        or role.get("selected_candidate_index_0based") != 0
        or role.get("role_profile") != "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
        or role.get("W") != list(owner.WARHEAD_ROLE)
        or role.get("L") != []
        or role.get("S") != list(owner.SCAFFOLD_ROLE)
        or role.get("W_L_S_counts") != [9, 0, 16]
        or role.get("Exact25_count") != 25
        or role.get("applicable_task_ids") != [0, 3, 4]
        or role.get("reusable_role_rule_created") is not False
    ):
        fail("FORMAL_CANDIDATE0_ROLE_INVALID")
    tasks = formal.get("canonical_Exact5_and_sample_applicability")
    if (
        type(tasks) is not dict
        or tasks.get("global_canonical_task_count") != 5
        or tasks.get("B3_present") is not True
        or tasks.get("sixth_task_present") is not False
        or tasks.get("sample_applicable_task_ids") != [0, 3, 4]
        or tasks.get("authoritative_task_labels_created") is not False
        or tasks.get("event_task_label_rows_materialized") is not False
    ):
        fail("FORMAL_EXACT5_OR_LABEL_BOUNDARY_INVALID")
    pre = formal.get("PRE_POST_boundary")
    if (
        type(pre) is not dict
        or pre.get("supporting_PRE_source_graph_count_per_event") != 1
        or pre.get("PRE_source_graph_present") is not True
        or pre.get("PRE_source_graph_count_per_event") != 1
        or pre.get("PRE_mapping_count_per_event") != 0
        or pre.get("PRE_mapping_status")
        != "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE"
        or pre.get("PRE_status") != "PRE_REACTION_UNRESOLVED"
        or pre.get("PRE_topology_authority") is not False
        or pre.get("PRE_geometry_authority") is not False
        or pre.get("PRE_coordinates_authority") is not False
    ):
        fail("FORMAL_PRE_BOUNDARY_INVALID")
    post = formal.get("POST_evidence_boundary")
    training = formal.get("training_use_boundary")
    pair = formal.get("reactive_pair_authority")
    if (
        type(post) is not dict
        or post.get("POST_source_evidence_count") != 4
        or post.get("POST_geometry_training_authority") is not False
        or type(training) is not dict
        or training.get("future_training_admission_candidate") is not True
        or training.get("formal_training_admitted") is not False
        or training.get("training_materialization_allowed") is not False
        or type(pair) is not dict
        or pair.get("protein_reactive_atom") != "SG"
        or pair.get("ligand_reactive_atom") != "C15"
        or pair.get("authority_scope") != owner.PAIR_AUTHORITY_SCOPE
        or pair.get("reusable_pair_rule_created") is not False
    ):
        fail("FORMAL_POST_TRAINING_OR_PAIR_BOUNDARY_INVALID")


def check_current_census_independently() -> None:
    payload = (REPO_ROOT / owner.CENSUS_MATRIX_RELATIVE).read_bytes()
    try:
        rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))
    except UnicodeDecodeError:
        fail("CURRENT_CENSUS_UTF8_INVALID")
    targets = [
        row for row in rows
        if row.get("canonical_event_id") in set(owner.EXPECTED_EVENT_IDS)
    ]
    if (
        len(rows) != 1000
        or len({row.get("canonical_event_id") for row in rows}) != 1000
        or len(targets) != 4
        or tuple(row.get("canonical_event_id") for row in targets)
        != owner.EXPECTED_EVENT_IDS
        or tuple(int(row["scaleup_rank"]) for row in targets)
        != owner.EXPECTED_RANKS
    ):
        fail("CURRENT_CENSUS_EXACT4_INVALID")
    expected = {
        "current_global_status": "CURRENTLY_UNREVIEWED",
        "current_review_status": "CURRENTLY_UNREVIEWED",
        "human_review_completed": "false",
        "chemistry_disposition": "UNRESOLVED",
        "task_relevance_disposition": "UNRESOLVED",
        "training_use_disposition": "UNRESOLVED",
        "formal_training_admitted": "false",
    }
    if any(
        any(row.get(key) != value for key, value in expected.items())
        for row in targets
    ):
        fail("CURRENT_CENSUS_PRE_INGESTION_STATE_INVALID")


def check_independent_projection(artifacts: dict[str, bytes]) -> None:
    snapshot = strict_json(artifacts[owner.SNAPSHOT], "SNAPSHOT")
    summary = strict_json(artifacts[owner.SUMMARY], "SUMMARY")
    manifest = strict_json(artifacts[owner.MANIFEST], "MANIFEST")
    try:
        rows = list(
            csv.DictReader(io.StringIO(artifacts[owner.MATRIX].decode("utf-8")))
        )
    except UnicodeDecodeError:
        fail("MATRIX_UTF8_INVALID")
    human = snapshot.get("human_authorization")
    if type(human) is not dict or [
        human.get("D1_task_relevance"),
        human.get("D2_chemistry"),
        human.get("D3_reactive_pair"),
        human.get("D4_role_candidate"),
        human.get("D5_training_use"),
    ] != [
        "RELEVANT", "POSITIVE", "CONFIRM_OBSERVED_PAIR",
        "SELECT_CANDIDATE_0", "INCLUDE",
    ]:
        fail("SNAPSHOT_D1_D5_INVALID")
    contexts = snapshot.get("context_preservation")
    if (
        type(contexts) is not dict
        or contexts.get("contexts_collapsed") is not False
        or [
            (row.get("pdb_id"), row.get("protein_context"), row.get("cys_residue"), row.get("event_count"))
            for row in contexts.get("contexts", [])
        ]
        != [
            ("5AZT", "PPARalpha", "Cys275", 2),
            ("5AZV", "PPARgamma", "Cys285", 2),
        ]
    ):
        fail("SNAPSHOT_CONTEXTS_INVALID")
    role = snapshot.get("selected_role_partition")
    if (
        type(role) is not dict
        or role.get("selected_role_candidate_index_0based") != 0
        or role.get("role_profile") != owner.EXPECTED_ROLE_PROFILE
        or role.get("warhead_role_atom_ids") != list(owner.WARHEAD_ROLE)
        or role.get("linker_atom_ids") != []
        or role.get("scaffold_atom_ids") != list(owner.SCAFFOLD_ROLE)
        or role.get("boundary_bonds") != list(owner.BOUNDARY_BONDS)
        or role.get("Exact25_count") != 25
        or role.get("warhead_connected") is not True
        or role.get("linker_connected_or_empty") is not True
        or role.get("scaffold_connected") is not True
        or role.get("sample_level_authoritative") is not True
        or role.get("reusable") is not False
    ):
        fail("SNAPSHOT_ROLE_AUTHORITY_INVALID")
    runtime = snapshot.get("structural_validation")
    published = role.get("published_DIRECT_runtime_validation")
    if (
        type(runtime) is not dict
        or runtime.get("partition_pairwise_disjoint") is not True
        or runtime.get("partition_exhaustive") is not True
        or runtime.get("missing_atom_ids") != []
        or runtime.get("extra_atom_ids") != []
        or type(published) is not dict
        or published.get("validator") != "validate_role_profile_v1"
        or published.get("valid") is not True
        or published.get("reasons") != []
        or published.get("applicable_task_ids") != [0, 3, 4]
    ):
        fail("SNAPSHOT_INDEPENDENT_OR_RUNTIME_VALIDATION_INVALID")
    tasks = snapshot.get("canonical_task_contract")
    if (
        type(tasks) is not dict
        or tasks.get("global_canonical_task_count") != 5
        or tasks.get("B3_present") is not True
        or tasks.get("sixth_task_present") is not False
        or tasks.get("direct_profile_applicable_task_ids") != [0, 3, 4]
        or tasks.get("authoritative_task_labels_created") is not False
        or tasks.get("event_task_label_rows_materialized") is not False
    ):
        fail("SNAPSHOT_EXACT5_OR_TASK_LABEL_BOUNDARY_INVALID")
    pre = snapshot.get("PRE_boundary")
    post = snapshot.get("POST_boundary")
    training = snapshot.get("training_boundary")
    reusable = snapshot.get("reusable_authority_boundary")
    if (
        type(pre) is not dict
        or pre.get("PRE_source_graph_present") is not True
        or pre.get("PRE_source_graph_count_per_event") != 1
        or pre.get("PRE_mapping_count_per_event") != 0
        or pre.get("PRE_mapping_status") != owner.PRE_MAPPING_STATUS
        or pre.get("PRE_status") != owner.PRE_STATUS
        or pre.get("PRE_topology_authority") is not False
        or type(post) is not dict
        or post.get("POST_source_evidence_count") != 4
        or post.get("POST_geometry_training_authority") is not False
        or type(training) is not dict
        or training.get("human_training_use_disposition") != "INCLUDE"
        or training.get("future_training_admission_candidate") is not True
        or training.get("formal_training_admitted") is not False
        or type(reusable) is not dict
        or any(value is not False for value in reusable.values())
    ):
        fail("SNAPSHOT_PRE_POST_TRAINING_OR_REUSABLE_BOUNDARY_INVALID")
    if (
        len(rows) != 4
        or tuple(row["canonical_event_id"] for row in rows)
        != owner.EXPECTED_EVENT_IDS
        or tuple(int(row["scaleup_rank"]) for row in rows)
        != owner.EXPECTED_RANKS
        or [row["POST_distance_angstrom"] for row in rows]
        != ["1.785022", "1.829385", "1.766225", "1.755127"]
    ):
        fail("MATRIX_EXACT4_INVALID")
    for row in rows:
        applicability = json.loads(row["canonical_task_applicability_json"])
        if (
            row["protein_reactive_atom"] != "SG"
            or row["ligand_reactive_atom"] != "C15"
            or row["reactive_pair_human_authoritative"] != "true"
            or row["role_partition_human_authoritative"] != "true"
            or row["direct_profile_applicable_task_ids_json"] != "[0,3,4]"
            or [
                item["task_id"] for item in applicability
                if item["structurally_applicable"]
            ]
            != [0, 3, 4]
            or row["authoritative_task_labels_created"] != "false"
            or row["event_task_label_rows_materialized"] != "false"
            or row["PRE_source_graph_present"] != "true"
            or row["PRE_source_graph_count_per_event"] != "1"
            or row["PRE_mapping_count_per_event"] != "0"
            or row["PRE_mapping_status"] != owner.PRE_MAPPING_STATUS
            or row["PRE_topology_authority"] != "false"
            or row["POST_source_evidence_available"] != "true"
            or row["POST_geometry_training_authority"] != "false"
            or row["formal_training_admitted"] != "false"
            or row["reusable_chemistry_authority"] != "false"
            or row["reusable_pair_rule_created"] != "false"
            or row["reusable_role_authority"] != "false"
        ):
            fail("MATRIX_AUTHORITY_BOUNDARY_INVALID")
    expected_summary = {
        "ingested_event_count": 4,
        "human_completed_event_count": 4,
        "positive_chemistry_event_count": 4,
        "sample_pair_authority_event_count": 4,
        "role_authority_event_count": 4,
        "DIRECT_event_count": 4,
        "training_use_INCLUDE_event_count": 4,
        "future_training_admission_candidate_count": 4,
        "formal_training_admitted_count": 0,
        "PRE_source_graph_present_event_count": 4,
        "PRE_mapping_available_event_count": 0,
        "PRE_authority_event_count": 0,
        "POST_source_evidence_event_count": 4,
        "POST_training_authority_event_count": 0,
        "authoritative_task_labels_created": False,
        "event_task_label_rows_materialized": False,
        "FOUR_M5_COMPLETED_DECISION_INGESTED": True,
        "RECONCILIATION": False,
        "CENSUS_REFRESH": False,
        "QUEUE_REFRESH": False,
        "TRAINING_STARTED": False,
        "READY_FOR_TRAINING": False,
    }
    if any(summary.get(key) != value for key, value in expected_summary.items()):
        fail("SUMMARY_COUNTS_OR_BOUNDARY_INVALID")
    exact5_counts = summary.get("canonical_Exact5_applicable_event_counts")
    if exact5_counts != {
        "warhead_only": 4,
        "linker_plus_warhead": 0,
        "scaffold_plus_warhead": 0,
        "scaffold_only": 4,
        "scaffold_plus_linker_plus_warhead": 4,
    }:
        fail("SUMMARY_EXACT5_COUNTS_INVALID")
    census = manifest.get("current_census_boundary")
    if type(census) is not dict or [
        census.get("completed_positive_event_count"),
        census.get("completed_positive_unit_count"),
        census.get("completed_event_count"),
        census.get("completed_unit_count"),
        census.get("unreviewed_event_count"),
        census.get("unreviewed_unit_count"),
    ] != [103, 15, 131, 20, 207, 111]:
        fail("CURRENT_CENSUS_BASELINE_INVALID")
    if (
        manifest.get("candidate_publication_file_count") != 7
        or manifest.get("output_artifact_count") != 4
        or manifest.get("formal_semantics_independently_validated") is not True
        or manifest.get("frozen_formal_validator_imported") is not False
        or manifest.get("frozen_formal_validator_executed") is not False
        or manifest.get("formal_validator_runtime_dependency") is not False
        or manifest.get("authoritative_task_labels_created") is not False
        or manifest.get("event_task_label_rows_materialized") is not False
        or manifest.get("FORMAL_TRAINING_ADMITTED") is not False
        or manifest.get("READY_FOR_TRAINING") is not False
        or manifest.get("manifest_self_SHA256_recorded") is not False
        or manifest.get("MANIFEST_SELF_SHA256_PROHIBITED") is not True
    ):
        fail("MANIFEST_BOUNDARY_INVALID")
    verify_binding_records([manifest["formal_decision_binding"]], 1)
    verify_binding_records([manifest["formal_validator_binding"]], 1)
    verify_binding_records([manifest["structural_graph_binding"]], 1)
    verify_binding_records([manifest["source_binding_policy_binding"]], 1)
    verify_binding_records(manifest["semantic_owner_bindings"], 2)
    verify_binding_records(manifest["current_census_bindings"], 4)
    verify_binding_records(manifest["candidate_source_bindings"], 3)
    output_bindings = manifest.get("output_artifact_bindings")
    if type(output_bindings) is not dict or owner.MANIFEST in output_bindings:
        fail("MANIFEST_SELF_HASH_PROHIBITION_INVALID")
    for name in (owner.SNAPSHOT, owner.MATRIX, owner.SUMMARY):
        binding = output_bindings.get(name)
        if (
            type(binding) is not dict
            or binding.get("byte_count") != len(artifacts[name])
            or binding.get("SHA256") != sha256(artifacts[name])
            or binding.get("expected_executable_class") != "NON_EXECUTABLE"
        ):
            fail("OUTPUT_BINDING_INVALID:" + name)


def check_determinism(live: dict[str, bytes]) -> None:
    first = owner.build_artifacts_v1(REPO_ROOT)
    second = owner.build_artifacts_v1(REPO_ROOT)
    if live != first or first != second:
        fail("DETERMINISTIC_DOUBLE_BUILD_FAILED")
    with (
        tempfile.TemporaryDirectory() as first_dir,
        tempfile.TemporaryDirectory() as second_dir,
    ):
        first_root = Path(first_dir)
        second_root = Path(second_dir)
        first_written = owner.materialize_artifacts_v1(
            REPO_ROOT, output_root=first_root
        )
        second_written = owner.materialize_artifacts_v1(
            REPO_ROOT, output_root=second_root
        )
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
    successor_paths = {
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
        tracked_paths=expected_set,
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
        head="synthetic-immediate-pushed-publication",
        origin_main="synthetic-immediate-pushed-publication",
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
        changed_since_baseline=expected_set | successor_paths,
    )
    validate_repository_relation_values(
        profile=TRACKED_CLEAN,
        expected_paths=expected_set,
        head="synthetic-local-successor",
        origin_main="synthetic-published-ingestion",
        ahead=1,
        behind=0,
        baseline_is_ancestor_of_head=True,
        baseline_is_ancestor_of_origin=True,
        origin_is_ancestor_of_head=True,
        changed_since_baseline=expected_set | successor_paths,
    )
    negative_relations = {
        "baseline_rewind": relation_fails(baseline_is_ancestor_of_head=False),
        "origin_rewind": relation_fails(baseline_is_ancestor_of_origin=False),
        "origin_divergence": relation_fails(origin_is_ancestor_of_head=False),
        "behind_remote": relation_fails(behind=1),
        "missing_candidate": relation_fails(
            changed_since_baseline=(expected_set - {expected[0]}) | successor_paths
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
        "tracked_clean_allows_origin_between_baseline_and_head": True,
        "missing_candidate_path_fails": True,
        "baseline_rewind_fails": True,
        "origin_rewind_fails": True,
        "origin_divergence_fails": True,
        "behind_remote_fails": True,
        "mixed_lifecycle_fails": True,
        "dirty_state_fails": True,
    }


def check_forbidden_files(expected_paths: set[str]) -> None:
    for relative in expected_paths:
        path = REPO_ROOT / relative
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            fail("FORBIDDEN_SUFFIX:" + relative)
        if path.stat().st_size > 1024 * 1024:
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
    check_frozen_formal_independently()
    check_current_census_independently()
    owner_report = owner.check_materialized_v1(REPO_ROOT)
    live = {
        name: (REPO_ROOT / owner.OUTPUT_ROOT_RELATIVE / name).read_bytes()
        for name in owner.OUTPUT_FILENAMES
    }
    owner.validate_completed_decision_projection_v1(live, repo_root=REPO_ROOT)
    check_independent_projection(live)
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
        "published_DIRECT_runtime_validation": True,
        "PRE_source_graph_present_mapping_incompatible_preserved": True,
        "authoritative_task_labels_created": False,
        "event_task_label_rows_materialized": False,
        "deterministic_double_build": True,
        "tracked_modifications": 0,
        "staged_changes": 0,
        "ordinary_untracked_strict_exact7": (
            repository_profile == CANDIDATE_UNTRACKED
        ),
        "protected_source_diffs": 0,
        "forbidden_new_files": 0,
        "RECONCILIATION": False,
        "CENSUS_REFRESH": False,
        "QUEUE_REFRESH": False,
        "FORMAL_TRAINING_ADMITTED": False,
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
