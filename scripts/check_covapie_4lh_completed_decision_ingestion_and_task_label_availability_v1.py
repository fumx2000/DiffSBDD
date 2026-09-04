#!/usr/bin/env python3
"""Check the uncommitted or tracked-clean 4LH ingestion Exact7 candidate."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
import stat
import subprocess
import sys
from typing import Mapping

from covalent_ext import covapie_4lh_completed_decision_ingestion_and_task_label_availability_v1 as owner


ERROR = "COVAPIE_4LH_INGESTION_CHECK_V1_ERROR"
CANDIDATE_UNTRACKED = "CANDIDATE_UNTRACKED"
TRACKED_CLEAN = "TRACKED_CLEAN"
PROTECTED_PATHS = (
    "data/raw", "checkpoints", "equivariant_diffusion", "lightning_modules.py",
    "dataset.py", "data/prepare_crossdocked.py", "../covapie-state",
)
FORBIDDEN_SUFFIXES = (".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pyc", ".tmp", ".part")
GRAPH_EVIDENCE_RELATIVE = Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/4LH_COVAPIE_BULK_REVIEW_UNIT_C4EFE734A5B0CF57/review-preparation-v1/4lh_graph_and_review_evidence_v1.json")
GRAPH_EVIDENCE_BYTES = 28785
GRAPH_EVIDENCE_SHA256 = "e2c89e3846b5961df2a6bf1bb3c6ac89943a0bbb59e33832da637248fc9c7e2a"
CHECK_W = ("CAP", "CAQ", "CBE", "OAE", "NBA")
CHECK_L: tuple[str, ...] = ()
CHECK_S = (
    "C2", "C4", "C5", "C6", "CAA", "CAB", "CAH", "CAI", "CAJ", "CAK", "CAL", "CAN", "CAO",
    "CAR", "CAS", "CAT", "CAU", "CAV", "CBF", "CBH", "CBI", "CBK", "CBL", "CL5", "N1", "N3",
    "NAZ", "NBB", "NBO", "NBP", "OBC",
)


def fail(reason: str) -> None:
    raise RuntimeError(ERROR + ":" + reason)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(("git", *args), cwd=repo_root, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        fail("GIT_COMMAND_FAILED:" + ":".join(args))
    return result.stdout.strip()


def is_ancestor(repo_root: Path, older: str, newer: str) -> bool:
    result = subprocess.run(("git", "merge-base", "--is-ancestor", older, newer), cwd=repo_root, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode not in (0, 1):
        fail("GIT_ANCESTRY_CHECK_FAILED")
    return result.returncode == 0


def file_record(repo_root: Path, relative: Path) -> dict[str, object]:
    path = repo_root / relative
    try:
        metadata = path.lstat()
        payload = path.read_bytes()
    except OSError as error:
        raise RuntimeError(ERROR + ":FILE_READ_FAILED:" + relative.as_posix()) from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        fail("FILE_NOT_REGULAR_NON_SYMLINK:" + relative.as_posix())
    if metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
        fail("FILE_EXECUTABLE:" + relative.as_posix())
    if not payload.endswith(b"\n") or b"\r" in payload or b"\x00" in payload:
        fail("FILE_TEXT_HYGIENE_INVALID:" + relative.as_posix())
    return {"path": relative.as_posix(), "bytes": len(payload), "LOC": len(payload.decode("utf-8").splitlines()), "SHA256": sha256(payload), "mode": stat.filemode(metadata.st_mode), "class": "REGULAR_NON_SYMLINK_NON_EXECUTABLE"}


def check_git_lifecycle(repo_root: Path) -> dict[str, object]:
    branch = git(repo_root, "branch", "--show-current")
    head = git(repo_root, "rev-parse", "HEAD")
    origin = git(repo_root, "rev-parse", "origin/main")
    if branch != "main":
        fail("BRANCH_NOT_MAIN")
    if not is_ancestor(repo_root, owner.BASELINE_COMMIT, head) or not is_ancestor(repo_root, owner.BASELINE_COMMIT, origin):
        fail("BASELINE_NOT_ANCESTOR")
    if not is_ancestor(repo_root, origin, head):
        fail("ORIGIN_MAIN_NOT_ANCESTOR_OF_HEAD")
    try:
        behind, ahead = (int(value) for value in git(repo_root, "rev-list", "--left-right", "--count", "origin/main...HEAD").split())
    except ValueError as error:
        raise RuntimeError(ERROR + ":AHEAD_BEHIND_PARSE_FAILED") from error
    if behind != 0:
        fail("HEAD_BEHIND_ORIGIN_MAIN")
    tracked_modified = git(repo_root, "diff", "--name-only").splitlines()
    staged = git(repo_root, "diff", "--cached", "--name-only").splitlines()
    untracked = git(repo_root, "ls-files", "--others", "--exclude-standard").splitlines()
    expected = [path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS]
    expected_set = set(expected)
    if tracked_modified:
        fail("TRACKED_MODIFICATIONS_PRESENT")
    if staged:
        fail("STAGED_INDEX_NOT_EMPTY")
    if set(untracked) == expected_set and len(untracked) == 7:
        profile = CANDIDATE_UNTRACKED
        if head != owner.BASELINE_COMMIT or origin != owner.BASELINE_COMMIT or ahead != 0:
            fail("CANDIDATE_UNTRACKED_BASELINE_PROFILE_DRIFT")
    elif not untracked:
        profile = TRACKED_CLEAN
        tracked = set(git(repo_root, "ls-files", "--", *expected).splitlines())
        if tracked != expected_set:
            fail("TRACKED_CLEAN_EXACT7_NOT_TRACKED")
    else:
        fail("ORDINARY_UNTRACKED_NOT_EXACT7_OR_EMPTY")
    changed = set(git(repo_root, "diff", "--name-only", owner.BASELINE_COMMIT + "..HEAD").splitlines())
    if profile == TRACKED_CLEAN and not expected_set.issubset(changed):
        fail("TRACKED_CLEAN_EXACT7_NOT_DESCENDED_FROM_BASELINE")
    if any(path == protected or path.startswith(protected + "/") for path in changed for protected in PROTECTED_PATHS):
        fail("PROTECTED_HISTORY_CHANGED")
    history_scope = expected_set | (changed if profile == TRACKED_CLEAN else set())
    if any(path.endswith(FORBIDDEN_SUFFIXES) for path in history_scope):
        fail("FORBIDDEN_SUFFIX_IN_CANDIDATE_HISTORY")
    return {"profile": profile, "branch": branch, "HEAD": head, "origin_main": origin, "ahead": ahead, "behind": behind, "tracked_modification_count": 0, "staged_count": 0, "ordinary_untracked_count": len(untracked), "ordinary_untracked_paths": untracked, "raw_changed_since_baseline_count": 0, "protected_source_changed_since_baseline_count": 0, "forbidden_candidate_file_count": 0}


def strict_json(payload: bytes, label: str) -> dict[str, object]:
    try:
        value = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError(ERROR + ":JSON_INVALID:" + label) from error
    if type(value) is not dict:
        fail("JSON_ROOT_NOT_OBJECT:" + label)
    return value


def _connected(
    atom_ids: tuple[str, ...], bonds: tuple[tuple[str, str, str], ...]
) -> bool:
    if not atom_ids:
        return True
    allowed = set(atom_ids)
    adjacency = {atom_id: set() for atom_id in allowed}
    for left, right, _order in bonds:
        if left in allowed and right in allowed:
            adjacency[left].add(right)
            adjacency[right].add(left)
    visited: set[str] = set()
    pending = [atom_ids[0]]
    while pending:
        atom_id = pending.pop()
        if atom_id in visited:
            continue
        visited.add(atom_id)
        pending.extend(adjacency[atom_id] - visited)
    return visited == allowed


def independently_check_frozen_graph(repo_root: Path) -> dict[str, object]:
    payload = (repo_root.parent / GRAPH_EVIDENCE_RELATIVE).read_bytes()
    if len(payload) != GRAPH_EVIDENCE_BYTES or sha256(payload) != GRAPH_EVIDENCE_SHA256:
        fail("INDEPENDENT_GRAPH_SOURCE_BINDING_DRIFT")
    document = strict_json(payload, "INDEPENDENT_FROZEN_GRAPH")
    graph = document.get("canonical_heavy_atom_graph")
    if type(graph) is not dict:
        fail("INDEPENDENT_GRAPH_MISSING")
    atoms = graph.get("atom_inventory")
    raw_bonds = graph.get("bond_inventory")
    if type(atoms) is not list or type(raw_bonds) is not list:
        fail("INDEPENDENT_GRAPH_INVENTORY_INVALID")
    atom_ids = tuple(
        sorted(row.get("atom_id") for row in atoms if type(row) is dict)
    )
    expected_atoms = tuple(sorted((*CHECK_W, *CHECK_L, *CHECK_S)))
    if (
        graph.get("heavy_atom_count") != 36
        or len(atom_ids) != 36
        or atom_ids != expected_atoms
    ):
        fail("INDEPENDENT_GRAPH_EXACT36_DRIFT")
    bonds = tuple(
        (row.get("atom_id_1"), row.get("atom_id_2"), row.get("bond_order"))
        for row in raw_bonds
        if type(row) is dict
    )
    if graph.get("heavy_heavy_bond_count") != 39 or len(bonds) != 39:
        fail("INDEPENDENT_GRAPH_EXACT39_BONDS_DRIFT")
    atom_set = set(atom_ids)
    if any(
        type(left) is not str
        or type(right) is not str
        or type(order) is not str
        or left not in atom_set
        or right not in atom_set
        or left == right
        for left, right, order in bonds
    ):
        fail("INDEPENDENT_GRAPH_BOND_INVALID")
    W, L, S = set(CHECK_W), set(CHECK_L), set(CHECK_S)
    pairwise_disjoint = not (W & L or W & S or L & S)
    exhaustive = W | L | S == atom_set
    W_connected = _connected(CHECK_W, bonds)  # type: ignore[arg-type]
    L_connected_or_empty = not CHECK_L or _connected(CHECK_L, bonds)  # type: ignore[arg-type]
    S_connected = _connected(CHECK_S, bonds)  # type: ignore[arg-type]
    reactive_CAP_in_W = "CAP" in W
    if not pairwise_disjoint or not exhaustive:
        fail("INDEPENDENT_GRAPH_PARTITION_INVALID")
    if not W_connected:
        fail("INDEPENDENT_GRAPH_W_DISCONNECTED")
    if not L_connected_or_empty:
        fail("INDEPENDENT_GRAPH_L_DISCONNECTED")
    if not S_connected:
        fail("INDEPENDENT_GRAPH_S_DISCONNECTED")
    if not reactive_CAP_in_W:
        fail("INDEPENDENT_GRAPH_CAP_NOT_IN_W")
    role = {atom_id: name for name, values in (("W", W), ("L", L), ("S", S)) for atom_id in values}
    boundaries: list[tuple[str, str, str]] = []
    for left, right, order in bonds:  # type: ignore[misc]
        if role[left] == role[right]:
            continue
        if (role[left], role[right]) == ("S", "W"):
            boundaries.append((left, right, order))
        elif (role[left], role[right]) == ("W", "S"):
            boundaries.append((right, left, order))
        else:
            fail("INDEPENDENT_GRAPH_UNEXPECTED_BOUNDARY_CLASS")
    if boundaries != [("CBH", "NBA", "SING")]:
        fail("INDEPENDENT_GRAPH_DIRECT_BOUNDARY_NOT_UNIQUE_EXACT")
    return {
        "Exact36_count": 36,
        "W_count": 5,
        "L_count": 0,
        "S_count": 31,
        "partition_pairwise_disjoint": pairwise_disjoint,
        "partition_exhaustive": exhaustive,
        "W_connected": W_connected,
        "L_connected_or_empty": L_connected_or_empty,
        "S_connected": S_connected,
        "reactive_CAP_in_W": reactive_CAP_in_W,
        "cross_role_boundary_count": 1,
        "cross_role_boundary": "CBH-NBA/SING",
    }


def independently_check_sources(repo_root: Path) -> dict[str, object]:
    records = []
    for binding in owner.ACTIVE_BINDINGS:
        relative, namespace, byte_count, digest, executable, role, method = binding
        path = repo_root / relative if namespace == "repository_relative" else repo_root.parent / relative
        metadata = path.lstat()
        payload = path.read_bytes()
        if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode) or len(payload) != byte_count or sha256(payload) != digest:
            fail("SOURCE_BINDING_DRIFT:" + relative.as_posix())
        observed_executable = bool(metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
        if observed_executable is not executable:
            fail("SOURCE_EXECUTABLE_CLASS_DRIFT:" + relative.as_posix())
        records.append({"path": relative.as_posix(), "bytes": len(payload), "SHA256": digest, "source_role": role, "validation_method": method})
    formal = strict_json((repo_root.parent / owner.FORMAL_DECISION_RELATIVE).read_bytes(), "FORMAL")
    clone = dict(formal)
    literal = clone.pop("formal_semantic_canonical_sha256", None)
    semantic = sha256(json.dumps(clone, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8"))
    if literal != owner.FORMAL_SEMANTIC_CANONICAL_SHA256 or semantic != owner.FORMAL_SEMANTIC_CANONICAL_SHA256:
        fail("FORMAL_SEMANTIC_DIGEST_DRIFT")
    d6 = formal.get("human_approved_context")
    if type(d6) is not dict or d6.get("D6_utf8_bytes") != 1501 or d6.get("D6_sha256") != owner.EXPECTED_D6_SHA256:
        fail("D6_BINDING_DRIFT")
    if len(owner.EXPECTED_D6.encode("utf-8")) != 1501 or sha256(owner.EXPECTED_D6.encode("utf-8")) != owner.EXPECTED_D6_SHA256:
        fail("D6_INTERNAL_DRIFT")
    source_text = (repo_root / owner.SOURCE_RELATIVE).read_text(encoding="utf-8")
    forbidden_runtime_patterns = ("import validate_4lh_formal_human_decision_v1", "from validate_4lh_formal_human_decision_v1", "run_path(", "exec(")
    if any(pattern in source_text for pattern in forbidden_runtime_patterns):
        fail("FROZEN_FORMAL_VALIDATOR_RUNTIME_DEPENDENCY")
    return {"active_source_binding_count": len(records), "records": records, "formal_semantic_SHA256": semantic, "D6_SHA256": owner.EXPECTED_D6_SHA256, "formal_validator_provenance_only": True}


def independently_check_projection(repo_root: Path, artifacts: Mapping[str, bytes]) -> dict[str, object]:
    structural = independently_check_frozen_graph(repo_root)
    snapshot = strict_json(artifacts[owner.SNAPSHOT], "SNAPSHOT")
    summary = strict_json(artifacts[owner.SUMMARY], "SUMMARY")
    manifest = strict_json(artifacts[owner.MANIFEST], "MANIFEST")
    reader = csv.DictReader(io.StringIO(artifacts[owner.MATRIX].decode("utf-8"), newline=""))
    rows = list(reader)
    if tuple(reader.fieldnames or ()) != owner.MATRIX_HEADER or len(rows) != 4:
        fail("MATRIX_INVENTORY_DRIFT")
    if tuple(row["canonical_event_id"] for row in rows) != owner.EXPECTED_EVENT_IDS or tuple(int(row["scaleup_rank"]) for row in rows) != owner.EXPECTED_RANKS:
        fail("EXACT4_ID_OR_RANK_DRIFT")
    for row in rows:
        exact = {
            "human_review_completed": "true", "human_task_relevance_decision": "RELEVANT",
            "task_relevance_human_authoritative": "true", "human_chemistry_decision": "POSITIVE",
            "chemistry_known_positive": "true", "chemistry_human_authoritative": "true",
            "negative_chemistry": "false", "task_domain_negative": "false", "protein_reactive_atom": "SG",
            "ligand_reactive_atom": "CAP", "reactive_pair_human_authoritative": "true",
            "pair_authority_scope": owner.PAIR_AUTHORITY_SCOPE, "all_4LH_uses_CAP_authority": "false",
            "role_profile": owner.EXPECTED_ROLE_PROFILE, "warhead_atoms_json": json.dumps(list(owner.WARHEAD_ATOMS), separators=(",", ":")),
            "linker_atoms_json": "[]", "scaffold_atoms_json": json.dumps(list(owner.SCAFFOLD_ATOMS), separators=(",", ":")),
            "W_L_S_counts_json": "[5,0,31]", "Exact36_count": "36",
            "partition_pairwise_disjoint": "true", "partition_exhaustive": "true",
            "warhead_connected": "true", "linker_connected_or_empty": "true",
            "scaffold_connected": "true", "reactive_CAP_in_W": "true",
            "boundary_bonds_json": '[{"bond_order":"SING","scaffold_atom_id":"CBH","warhead_atom_id":"NBA"}]',
            "B3_present": "true", "sixth_task": "false",
            "direct_profile_applicable_task_ids_json": "[0,3,4]", "authoritative_task_labels_created": "false",
            "event_task_label_rows_materialized": "false", "human_training_use_disposition": "INCLUDE",
            "future_training_admission_candidate": "true", "formal_training_admitted": "false",
            "training_materialization_allowed": "false", "training_mask_targets_available_now": "false",
            "ready_for_training": "false", "supporting_PRE_source_graph_count": "1", "PRE_source_graph_present": "true",
            "PRE_source_graph_count": "1", "PRE_mapping_count": "2", "PRE_mapping_status": owner.PRE_MAPPING_STATUS,
            "PRE_status": owner.PRE_STATUS, "PRE_topology_authority": "false", "PRE_geometry_authority": "false",
            "PRE_coordinates_authority": "false", "POST_source_evidence_available": "true",
            "POST_geometry_training_authority": "false", "reusable_chemistry_authority": "false",
            "reusable_pair_authority": "false", "reusable_role_authority": "false",
            "authority_source": owner.AUTHORITY_SOURCE, "projection_of_frozen_formal_human_authority": "true",
            "new_human_authority_created_by_ingestion": "false",
        }
        for key, value in exact.items():
            if row.get(key) != value:
                fail("MATRIX_SEMANTIC_DRIFT:" + key)
    role = snapshot.get("selected_role_partition")
    if type(role) is not dict or role.get("direct_scaffold_warhead_boundary") != owner.BOUNDARY or role.get("minimal_seed_atom_ids") != list(owner.MINIMAL_SEED) or role.get("primary_anchor_atom_id") != "CBH":
        fail("SNAPSHOT_ROLE_BOUNDARY_SEED_DRIFT")
    runtime = role.get("published_DIRECT_runtime_validation")
    if type(runtime) is not dict or runtime.get("valid") is not True or runtime.get("reasons") != [] or runtime.get("applicable_task_ids") != [0, 3, 4]:
        fail("SNAPSHOT_RUNTIME_DRIFT")
    census = snapshot.get("current_census_boundary")
    if type(census) is not dict or census.get("4LH_current_global_status") != "CURRENTLY_UNREVIEWED" or census.get("current_pending_rank") != 1:
        fail("CURRENT_CENSUS_BOUNDARY_DRIFT")
    required_summary = {"event_count": 4, "human_review_completed": 4, "task_relevant": 4, "chemistry_positive": 4, "pair_authoritative": 4, "role_authoritative": 4, "DIRECT_profile": 4, "human_training_INCLUDE": 4, "future_training_candidates": 4, "formal_training_admitted": 0, "ready_for_training": 0, "PRE_authority": 0, "POST_training_authority": 0}
    for key, value in required_summary.items():
        if summary.get(key) != value:
            fail("SUMMARY_COUNT_DRIFT:" + key)
    if manifest.get("manifest_self_SHA256_recorded") is not False or manifest.get("output_artifact_count") != 4 or manifest.get("candidate_publication_file_count") != 7:
        fail("MANIFEST_BOUNDARY_DRIFT")
    return {"event_count": 4, "matrix_column_count": len(owner.MATRIX_HEADER), "runtime_valid": True, "applicable_task_ids": [0, 3, 4], "B3_present": True, "sixth_task": False, "independent_structural_proof": structural, "matrix_connectivity_claims_source_verified": True}


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    lifecycle = check_git_lifecycle(repo_root)
    sources = independently_check_sources(repo_root)
    materialized = owner.check_materialized_v1(repo_root)
    inventory = [file_record(repo_root, path) for path in owner.CANDIDATE_PUBLICATION_PATHS]
    if len(inventory) != 7 or len({row["path"] for row in inventory}) != 7:
        fail("CANDIDATE_INVENTORY_NOT_EXACT7")
    output_root = repo_root / owner.OUTPUT_ROOT_RELATIVE
    if {path.name for path in output_root.iterdir()} != set(owner.OUTPUT_FILENAMES):
        fail("OUTPUT_INVENTORY_NOT_EXACT4")
    artifacts = {name: (output_root / name).read_bytes() for name in owner.OUTPUT_FILENAMES}
    projection = independently_check_projection(repo_root, artifacts)
    if materialized.get("READY_FOR_EXTERNAL_REVIEW") is not True or materialized.get("READY_FOR_TRAINING") is not False:
        fail("READINESS_GATE_DRIFT")
    result = {
        "status": "PASS", "lifecycle": lifecycle, "candidate_Exact7": inventory,
        "source_bindings": sources, "materialized": materialized, "projection": projection,
        "independent_structural_proof": projection["independent_structural_proof"],
        "4LH_COMPLETED_DECISION_INGESTION_V1_PASS": True, "EVENT_COUNT": 4,
        "TASK_RELEVANCE": "RELEVANT", "CHEMISTRY": "POSITIVE", "PAIR_AUTHORITY_COUNT": 4,
        "ROLE_AUTHORITY_COUNT": 4, "ROLE_PROFILE": owner.EXPECTED_ROLE_PROFILE,
        "W_COUNT": 5, "L_COUNT": 0, "S_COUNT": 31, "DIRECT_BOUNDARY": "CBH-NBA/SING",
        "MINIMAL_SEED": list(owner.MINIMAL_SEED), "APPLICABLE_TASK_IDS": [0, 3, 4],
        "EXACT5_B3_PRESENT": True, "SIXTH_TASK": False, "HUMAN_TRAINING_USE": "INCLUDE",
        "FUTURE_TRAINING_ADMISSION_CANDIDATE": True, "FORMAL_TRAINING_ADMITTED": False,
        "TRAINING_MATERIALIZATION_ALLOWED": False, "READY_FOR_TRAINING": False, "TRAINING_STARTED": False,
        "PRE_MAPPING_STATUS": owner.PRE_MAPPING_STATUS, "PRE_STATUS": owner.PRE_STATUS,
        "POST_SOURCE_EVIDENCE_COUNT": 4, "POST_TRAINING_AUTHORITY_COUNT": 0,
        "PROJECTION_OF_FROZEN_FORMAL_AUTHORITY": True, "NEW_HUMAN_AUTHORITY_CREATED_BY_INGESTION": False,
        "INDEPENDENT_W_CONNECTIVITY": True, "INDEPENDENT_L_CONNECTIVITY_OR_EMPTY": True,
        "INDEPENDENT_S_CONNECTIVITY": True, "INDEPENDENT_REACTIVE_CAP_IN_W": True,
        "INDEPENDENT_DIRECT_BOUNDARY": "CBH-NBA/SING",
        "MATRIX_CONNECTIVITY_CLAIMS_SOURCE_VERIFIED": True,
        "GIT_REPOSITORY_CLEAN_EXCEPT_EXACT7_UNTRACKED": lifecycle["profile"] == CANDIDATE_UNTRACKED,
        "RECONCILIATION": False, "CENSUS_REFRESH": False, "QUEUE_REFRESH": False,
        "COMMIT": False, "PUSH": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, owner.FourLHIngestionSafetyError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error
