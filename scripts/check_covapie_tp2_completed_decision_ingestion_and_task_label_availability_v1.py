#!/usr/bin/env python3
"""Check the uncommitted or tracked-clean TP2 ingestion Exact7 candidate."""

from __future__ import annotations

import csv
from dataclasses import fields
import hashlib
import importlib
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

from covalent_ext import covapie_tp2_completed_decision_ingestion_and_task_label_availability_v1 as owner  # noqa: E402


ERROR = "COVAPIE_TP2_INGESTION_CHECK_V1_ERROR"
CANDIDATE_UNTRACKED = "CANDIDATE_UNTRACKED"
TRACKED_CLEAN = "TRACKED_CLEAN"
PROTECTED_PATHS = (
    "data/raw", "checkpoints", "equivariant_diffusion", "lightning_modules.py",
    "dataset.py", "data/prepare_crossdocked.py", "../covapie-state",
)
FORBIDDEN_SUFFIXES = (".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".pyc", ".tmp", ".part")

FORMAL_BYTES = 17825
FORMAL_SHA256 = "95fc125eefe09dd7ed81c9e95f2b76a084b889ece239aed5eb96215409315dc0"
FORMAL_SCHEMA = "covapie_tp2_exact4_formal_human_decision_v1"
SEMANTIC_SHA256 = "d1090a6073f5af89a82fcb204edc5854b901233fe435931ed83459ee4485e352"
D6_BYTES = 2202
D6_SHA256 = "92d77b46a67bdc489292c2417d268b94fa86eff3a2b4cbb68a35c4d687426cf5"
GRAPH_BYTES = 27352
GRAPH_SHA256 = "556513eced9b57254b2c53c14c0d121fd66c15f9f93b3a62ddc08a257e04dcf1"
REVIEW_UNIT = "COVAPIE_BULK_REVIEW_UNIT_C750E9F706F9E0AF"
CHECK_EVENTS = (
    "COVAPIE_CYS_SG_EVENT_V1:1F4C:A:CYS:146-:SG:F:TP2:S1",
    "COVAPIE_CYS_SG_EVENT_V1:1F4C:B:CYS:146-:SG:I:TP2:S1",
    "COVAPIE_CYS_SG_EVENT_V1:1F4D:A:CYS:143-:SG:E:TP2:S1",
    "COVAPIE_CYS_SG_EVENT_V1:1F4D:B:CYS:143-:SG:I:TP2:S1",
)
CHECK_W = ("S1",)
CHECK_L = ("C2", "C3", "N4")
CHECK_S = ("C5", "O21", "C6", "C20", "C19", "C18", "N7", "S8", "O16", "O17", "C9", "C10", "C11", "C12", "C13", "C14", "C15")
CHECK_SEED = ("C5", "O21", "C6")
CHECK_BOUNDARIES = (
    ("warhead-linker", "S1", "C2", "SING"),
    ("linker-scaffold", "N4", "C5", "SING"),
)
GENERIC_FIELDS = (
    "canonical_event_id", "review_unit_id", "human_review_completed",
    "legacy_completed_review_status", "task_relevance_disposition",
    "chemistry_disposition", "training_disposition", "human_training_excluded",
    "source_decision_schema", "source_decision_sha256", "source_binding_path",
)


def fail(reason: str) -> None:
    raise RuntimeError(ERROR + ":" + reason)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


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
        metadata, payload = path.lstat(), path.read_bytes()
    except OSError as error:
        raise RuntimeError(ERROR + ":FILE_READ_FAILED:" + relative.as_posix()) from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        fail("FILE_NOT_REGULAR_NON_SYMLINK:" + relative.as_posix())
    if metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
        fail("FILE_EXECUTABLE:" + relative.as_posix())
    if not payload.endswith(b"\n") or b"\r" in payload or b"\x00" in payload:
        fail("FILE_TEXT_HYGIENE_INVALID:" + relative.as_posix())
    return {
        "path": relative.as_posix(), "bytes": len(payload),
        "LOC": len(payload.decode("utf-8").splitlines()), "SHA256": sha256(payload),
        "mode": stat.filemode(metadata.st_mode),
        "class": "REGULAR_NON_SYMLINK_NON_EXECUTABLE",
    }


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
    return {
        "profile": profile, "branch": branch, "HEAD": head, "origin_main": origin,
        "ahead": ahead, "behind": behind, "tracked_modification_count": 0,
        "staged_count": 0, "ordinary_untracked_count": len(untracked),
        "ordinary_untracked_paths": untracked, "raw_changed_since_baseline_count": 0,
        "protected_source_changed_since_baseline_count": 0,
        "forbidden_candidate_file_count": 0,
    }


def strict_json(payload: bytes, label: str) -> dict[str, object]:
    if payload.startswith(b"\xef\xbb\xbf") or b"\x00" in payload:
        fail("JSON_TEXT_INVALID:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RuntimeError(ERROR + ":JSON_UTF8_INVALID:" + label) from error

    def hook(pairs: list[tuple[str, object]]) -> dict[str, object]:
        value: dict[str, object] = {}
        for key, child in pairs:
            if key in value:
                fail("JSON_DUPLICATE_KEY:" + label + ":" + key)
            value[key] = child
        return value

    try:
        value = json.loads(text, object_pairs_hook=hook)
    except json.JSONDecodeError as error:
        raise RuntimeError(ERROR + ":JSON_INVALID:" + label) from error
    if type(value) is not dict:
        fail("JSON_ROOT_NOT_OBJECT:" + label)
    return value


def _connected(atom_ids: tuple[str, ...], bonds: tuple[tuple[str, str, str], ...]) -> bool:
    allowed = set(atom_ids)
    if not allowed:
        return False
    adjacency = {atom: set() for atom in allowed}
    for left, right, _order in bonds:
        if left in allowed and right in allowed:
            adjacency[left].add(right)
            adjacency[right].add(left)
    visited: set[str] = set()
    pending = [atom_ids[0]]
    while pending:
        atom = pending.pop()
        if atom in visited:
            continue
        visited.add(atom)
        pending.extend(adjacency[atom] - visited)
    return visited == allowed


def independently_check_frozen_graph(repo_root: Path) -> dict[str, object]:
    payload = (repo_root.parent / owner.GRAPH_EVIDENCE_RELATIVE).read_bytes()
    if len(payload) != GRAPH_BYTES or sha256(payload) != GRAPH_SHA256:
        fail("INDEPENDENT_GRAPH_SOURCE_BINDING_DRIFT")
    document = strict_json(payload, "INDEPENDENT_FROZEN_GRAPH")
    graph = document.get("canonical_heavy_atom_graph")
    if type(graph) is not dict:
        fail("INDEPENDENT_GRAPH_MISSING")
    atoms, raw_bonds = graph.get("atom_inventory"), graph.get("bond_inventory")
    if type(atoms) is not list or type(raw_bonds) is not list:
        fail("INDEPENDENT_GRAPH_INVENTORY_INVALID")
    atom_ids = tuple(sorted(row.get("atom_id") for row in atoms if type(row) is dict))
    expected_atoms = tuple(sorted((*CHECK_W, *CHECK_L, *CHECK_S)))
    if graph.get("heavy_atom_count") != 21 or atom_ids != expected_atoms or len(atom_ids) != 21:
        fail("INDEPENDENT_GRAPH_EXACT21_DRIFT")
    bonds = tuple((row.get("atom_id_1"), row.get("atom_id_2"), row.get("bond_order")) for row in raw_bonds if type(row) is dict)
    if graph.get("heavy_heavy_bond_count") != 22 or len(bonds) != 22:
        fail("INDEPENDENT_GRAPH_EXACT22_BONDS_DRIFT")
    atom_set = set(atom_ids)
    if any(type(left) is not str or type(right) is not str or type(order) is not str or left not in atom_set or right not in atom_set or left == right for left, right, order in bonds):
        fail("INDEPENDENT_GRAPH_BOND_INVALID")
    bonds = bonds  # type: ignore[assignment]
    W, L, S = set(CHECK_W), set(CHECK_L), set(CHECK_S)
    pairwise = not (W & L or W & S or L & S)
    exhaustive = W | L | S == atom_set
    connectivity = {
        "W": _connected(CHECK_W, bonds), "L": _connected(CHECK_L, bonds),
        "S": _connected(CHECK_S, bonds),
    }
    if not pairwise or not exhaustive or not all(connectivity.values()) or "S1" not in W:
        fail("INDEPENDENT_GRAPH_PARTITION_OR_CONNECTIVITY_INVALID")
    role = {atom: name for name, values in (("W", W), ("L", L), ("S", S)) for atom in values}
    boundaries: list[tuple[str, str, str, str]] = []
    for left, right, order in bonds:
        if role[left] == role[right]:
            continue
        if {role[left], role[right]} == {"W", "L"}:
            boundaries.append(("warhead-linker", left if role[left] == "W" else right, right if role[left] == "W" else left, order))
        elif {role[left], role[right]} == {"L", "S"}:
            boundaries.append(("linker-scaffold", left if role[left] == "L" else right, right if role[left] == "L" else left, order))
        else:
            fail("INDEPENDENT_GRAPH_UNEXPECTED_BOUNDARY_CLASS")
    if sorted(boundaries) != sorted(CHECK_BOUNDARIES) or len(boundaries) != 2:
        fail("INDEPENDENT_GRAPH_BOUNDARIES_NOT_EXACT2")
    return {
        "Exact21_count": 21, "W_count": 1, "L_count": 3, "S_count": 17,
        "partition_pairwise_disjoint": pairwise, "partition_exhaustive": exhaustive,
        "W_connected": True, "L_connected": True, "S_connected": True,
        "reactive_S1_in_W": True, "cross_role_boundary_count": 2,
        "cross_role_boundaries": ["S1-C2/SING", "N4-C5/SING"],
        "heavy_atoms": atom_ids, "heavy_bonds": bonds,
    }


def independently_check_formal(repo_root: Path) -> dict[str, object]:
    payload = (repo_root.parent / owner.FORMAL_DECISION_RELATIVE).read_bytes()
    if len(payload) != FORMAL_BYTES or sha256(payload) != FORMAL_SHA256:
        fail("FORMAL_SOURCE_IDENTITY_DRIFT")
    formal = strict_json(payload, "FORMAL")
    if formal.get("schema_version") != FORMAL_SCHEMA or formal.get("record_role") != "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY":
        fail("FORMAL_SCHEMA_OR_ROLE_DRIFT")
    semantic_keys = (
        "POST_boundary", "PRE_boundary", "canonical_Exact5", "formal_decisions",
        "formal_state", "record_role", "reusable_authority_map", "sample_authority_map",
        "sample_identity", "schema_version", "selected_role_context", "training_boundary",
    )
    semantic = sha256(canonical_json({key: formal[key] for key in semantic_keys}))
    freeze = formal.get("semantic_freeze")
    if type(freeze) is not dict or freeze.get("semantic_canonical_SHA256") != SEMANTIC_SHA256 or semantic != SEMANTIC_SHA256:
        fail("FORMAL_SEMANTIC_SHA_DRIFT")
    decisions = formal.get("formal_decisions")
    if type(decisions) is not dict:
        fail("FORMAL_DECISIONS_MISSING")
    required = {
        "D1_task_relevance": "NOT_RELEVANT", "D2_chemistry": "POSITIVE",
        "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR", "D4_role_candidate": "SELECT_CANDIDATE_0",
        "D5_training_use": "NOT_APPLICABLE",
    }
    for key, value in required.items():
        row = decisions.get(key)
        if type(row) is not dict or row.get("decision") != value:
            fail("FORMAL_DECISION_DRIFT:" + key)
    if decisions["D3_reactive_pair"].get("protein_atom") != "SG" or decisions["D3_reactive_pair"].get("ligand_atom") != "S1":
        fail("FORMAL_D3_PAIR_DRIFT")
    d5 = decisions["D5_training_use"]
    if d5.get("human_training_excluded") is not False or d5.get("future_training_admission_candidate") is not False:
        fail("FORMAL_D5_BOUNDARY_DRIFT")
    d6 = decisions.get("D6_human_scientific_context")
    if type(d6) is not dict or type(d6.get("text")) is not str:
        fail("FORMAL_D6_MISSING")
    d6_payload = d6["text"].encode("utf-8")
    if len(d6_payload) != D6_BYTES or sha256(d6_payload) != D6_SHA256 or d6.get("UTF8_byte_count") != D6_BYTES or d6.get("SHA256") != D6_SHA256:
        fail("FORMAL_D6_IDENTITY_DRIFT")
    identity = formal.get("sample_identity")
    if type(identity) is not dict or tuple(identity.get("canonical_event_ids", ())) != CHECK_EVENTS or identity.get("scaleup_ranks") != [42, 43, 44, 45] or identity.get("raw_priority_rank") != 27:
        fail("FORMAL_EXACT4_IDENTITY_DRIFT")
    role = formal.get("selected_role_context")
    if type(role) is not dict or role.get("warhead_atom_ids") != list(CHECK_W) or role.get("linker_atom_ids") != list(CHECK_L) or role.get("scaffold_atom_ids") != list(CHECK_S):
        fail("FORMAL_ROLE_DRIFT")
    if role.get("role_profile") != "STRICT_LINKER_PRESENT_V1" or role.get("role_derived_task_ids") != [0, 1, 2, 3, 4]:
        fail("FORMAL_ROLE_PROFILE_OR_TASK_DRIFT")
    seed = role.get("minimal_seed")
    if type(seed) is not dict or seed.get("atom_ids") != list(CHECK_SEED) or seed.get("primary_anchor") != "C5":
        fail("FORMAL_SEED_DRIFT")
    exact5 = formal.get("canonical_Exact5")
    if type(exact5) is not dict or exact5.get("task_count") != 5 or exact5.get("B3_present") is not True or exact5.get("sixth_task") is not False or exact5.get("role_derived_structural_applicability_task_ids") != [0, 1, 2, 3, 4]:
        fail("FORMAL_EXACT5_DRIFT")
    pre, post, training, reusable = formal.get("PRE_boundary"), formal.get("POST_boundary"), formal.get("training_boundary"), formal.get("reusable_authority_map")
    if type(pre) is not dict or pre.get("PRE_MAPPING_STATUS") != "PRE_SOURCE_GRAPH_NOT_AVAILABLE" or pre.get("PRE_STATUS") != "PRE_REACTION_UNRESOLVED" or any(pre.get(key) is not False for key in ("PRE_topology_authority", "PRE_geometry_authority", "PRE_coordinates_authority")):
        fail("FORMAL_PRE_DRIFT")
    if type(post) is not dict or post.get("POST_source_evidence_available") is not True or post.get("POST_geometry_training_authority") is not False:
        fail("FORMAL_POST_DRIFT")
    if type(training) is not dict or training.get("human_training_use") != "NOT_APPLICABLE" or training.get("human_training_excluded") is not False or any(training.get(key) is not False for key in ("future_training_admission_candidate", "formal_training_admitted", "training_mask_targets_available_now", "current_runtime_model_usable", "READY_FOR_TRAINING")):
        fail("FORMAL_TRAINING_DRIFT")
    if type(reusable) is not dict or any(value is not False for value in reusable.values()):
        fail("FORMAL_REUSABLE_AUTHORITY_DRIFT")
    state = formal.get("formal_state")
    if type(state) is not dict or state.get("reviewer_id") != "fmx" or state.get("attestor_id") != "fmx" or state.get("authorization_origin") != "EXTERNAL_HUMAN_CHAT_REVIEW" or state.get("machine_scientific_authority") is not False or state.get("machine_human_approval") is not False:
        fail("FORMAL_HUMAN_STATE_DRIFT")
    source_text = (repo_root / owner.SOURCE_RELATIVE).read_text(encoding="utf-8")
    forbidden = ("import validate_tp2_formal_human_decision_v1", "from validate_tp2_formal_human_decision_v1", "run_path(", "exec(")
    if any(pattern in source_text for pattern in forbidden):
        fail("FROZEN_FORMAL_VALIDATOR_RUNTIME_DEPENDENCY")
    return {"bytes": len(payload), "SHA256": FORMAL_SHA256, "schema": FORMAL_SCHEMA, "semantic_SHA256": semantic, "D6_bytes": len(d6_payload), "D6_SHA256": sha256(d6_payload), "validator_provenance_only": True}


def independently_check_runtime_and_generic(repo_root: Path, graph: Mapping[str, object]) -> dict[str, object]:
    runtime = importlib.import_module("covalent_ext.covapie_direct_attachment_optional_linker_runtime_v1")
    bonds = tuple(graph["heavy_bonds"])
    role = runtime.validate_role_profile_v1(
        role_profile="STRICT_LINKER_PRESENT_V1", retained_heavy_atoms=tuple(graph["heavy_atoms"]),
        scaffold_atoms=CHECK_S, linker_atoms=CHECK_L, warhead_atoms=CHECK_W,
        reactive_atom_id="S1", explicit_graph_bonds=bonds,
    )
    seed = runtime.validate_minimal_seed_for_role_profile_v1(
        role_profile="STRICT_LINKER_PRESENT_V1", seed_atoms=CHECK_SEED,
        scaffold_atoms=CHECK_S, linker_atoms=CHECK_L, warhead_atoms=CHECK_W,
        explicit_graph_bonds=bonds, primary_anchor_atom_id="C5",
    )
    task_ids = tuple(runtime.valid_canonical_task_ids_for_role_profile_v1("STRICT_LINKER_PRESENT_V1"))
    if role.valid is not True or tuple(role.reasons) != () or (role.warhead_count, role.linker_count, role.scaffold_count) != (1, 3, 17):
        fail("INDEPENDENT_STRICT_RUNTIME_FAILED")
    if seed.valid is not True or tuple(seed.reasons) != () or seed.primary_anchor_atom_id != "C5":
        fail("INDEPENDENT_SEED_RUNTIME_FAILED")
    if task_ids != (0, 1, 2, 3, 4):
        fail("INDEPENDENT_STRICT_TASK_IDS_DRIFT")

    generic = importlib.import_module("covalent_ext.covapie_completed_human_decision_reconciliation_v1")
    binding = generic.SourceBinding(
        source_path=owner.FORMAL_DECISION_RELATIVE.as_posix(), path_namespace="repository_parent_relative",
        byte_count=FORMAL_BYTES, sha256=FORMAL_SHA256, schema_version=FORMAL_SCHEMA,
        review_unit_id=REVIEW_UNIT,
    )
    generic._validate_source_binding(binding)
    facts = []
    for event_id in CHECK_EVENTS:
        fact = generic.NormalizedCompletedDecisionFact(
            canonical_event_id=event_id, review_unit_id=REVIEW_UNIT,
            human_review_completed=True, legacy_completed_review_status="COMPLETED_HUMAN_NEGATIVE",
            task_relevance_disposition="NOT_RELEVANT", chemistry_disposition="POSITIVE",
            training_disposition="NOT_APPLICABLE", human_training_excluded=False,
            source_decision_schema=FORMAL_SCHEMA, source_decision_sha256=FORMAL_SHA256,
            source_binding_path=owner.FORMAL_DECISION_RELATIVE.as_posix(),
        )
        if tuple(field.name for field in fields(fact)) != GENERIC_FIELDS:
            fail("INDEPENDENT_GENERIC_FACT_NOT_EXACT11")
        generic._validate_fact(fact, binding)
        projected = {field.name: getattr(fact, field.name) for field in fields(fact)}
        if set(projected) != set(GENERIC_FIELDS):
            fail("INDEPENDENT_GENERIC_RICH_FIELD_LEAK")
        facts.append(projected)
    return {"role_valid": True, "role_reasons": [], "seed_valid": True, "seed_reasons": [], "applicable_task_ids": list(task_ids), "generic_Exact11_accepted_count": len(facts), "generic_facts": facts}


def independently_check_sources(repo_root: Path) -> dict[str, object]:
    records = []
    for binding in owner.ACTIVE_BINDINGS:
        relative, namespace, byte_count, digest, executable, role, method = binding
        path = repo_root / relative if namespace == "repository_relative" else repo_root.parent / relative
        metadata, payload = path.lstat(), path.read_bytes()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode) or len(payload) != byte_count or sha256(payload) != digest:
            fail("SOURCE_BINDING_DRIFT:" + relative.as_posix())
        observed_executable = bool(metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))
        if observed_executable is not executable:
            fail("SOURCE_EXECUTABLE_CLASS_DRIFT:" + relative.as_posix())
        records.append({"path": relative.as_posix(), "bytes": len(payload), "SHA256": digest, "source_role": role, "validation_method": method})
    formal = independently_check_formal(repo_root)
    return {"active_source_binding_count": len(records), "records": records, "formal": formal, "formal_validator_provenance_only": True}


def independently_check_census(repo_root: Path) -> dict[str, object]:
    path = repo_root / owner.CENSUS_MATRIX_RELATIVE
    rows = list(csv.DictReader(io.StringIO(path.read_text(encoding="utf-8"), newline="")))
    if len(rows) != 1000 or len({row["canonical_event_id"] for row in rows}) != 1000:
        fail("INDEPENDENT_CENSUS_UNIVERSE_DRIFT")
    targets = [row for row in rows if row["canonical_event_id"] in set(CHECK_EVENTS)]
    if len(targets) != 4 or tuple(row["canonical_event_id"] for row in targets) != CHECK_EVENTS:
        fail("INDEPENDENT_CENSUS_TP2_EXACT4_DRIFT")
    expected = {
        "current_global_status": "CURRENTLY_UNREVIEWED", "current_review_status": "CURRENTLY_UNREVIEWED",
        "human_review_completed": "false", "chemistry_disposition": "UNRESOLVED",
        "task_relevance_disposition": "UNRESOLVED", "training_use_disposition": "UNRESOLVED",
        "reactive_pair_sample_authoritative": "false", "role_partition_sample_authoritative": "false",
        "formal_training_admitted": "false", "structurally_applicable_task_ids_json": "null",
    }
    for row in targets:
        for key, value in expected.items():
            if row.get(key) != value:
                fail("INDEPENDENT_CENSUS_TP2_PRIOR_DRIFT:" + key)
    summary = strict_json((repo_root / owner.CENSUS_SUMMARY_RELATIVE).read_bytes(), "CENSUS_SUMMARY")
    pending = summary.get("top_pending_review_units_by_event_yield")
    if type(pending) is not list or not pending or type(pending[0]) is not dict or pending[0].get("review_unit_id") != REVIEW_UNIT or pending[0].get("rank") != 1 or pending[0].get("raw_priority_rank") != 27:
        fail("INDEPENDENT_CENSUS_PENDING_DRIFT")
    return {"row_count": 1000, "TP2_event_count": 4, "status": "CURRENTLY_UNREVIEWED", "current_pending_rank": 1, "raw_priority_rank": 27}


def independently_check_projection(repo_root: Path, artifacts: Mapping[str, bytes]) -> dict[str, object]:
    graph = independently_check_frozen_graph(repo_root)
    runtime_generic = independently_check_runtime_and_generic(repo_root, graph)
    census = independently_check_census(repo_root)
    snapshot = strict_json(artifacts[owner.SNAPSHOT], "SNAPSHOT")
    summary = strict_json(artifacts[owner.SUMMARY], "SUMMARY")
    manifest = strict_json(artifacts[owner.MANIFEST], "MANIFEST")
    reader = csv.DictReader(io.StringIO(artifacts[owner.MATRIX].decode("utf-8"), newline=""))
    rows = list(reader)
    if tuple(reader.fieldnames or ()) != owner.MATRIX_HEADER or len(rows) != 4:
        fail("MATRIX_INVENTORY_DRIFT")
    if tuple(row["canonical_event_id"] for row in rows) != CHECK_EVENTS or tuple(int(row["scaleup_rank"]) for row in rows) != (42, 43, 44, 45):
        fail("MATRIX_EXACT4_ID_OR_RANK_DRIFT")
    exact = {
        "completed_lane": "COMPLETED_TASK_DOMAIN_NEGATIVE",
        "legacy_completed_review_status": "COMPLETED_HUMAN_NEGATIVE",
        "human_review_completed": "true", "task_relevance": "NOT_RELEVANT",
        "chemistry": "POSITIVE", "negative_chemistry": "false",
        "task_domain_negative": "true", "positive_generative_supervision_eligible": "false",
        "reactive_pair_human_authoritative": "true", "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "S1", "role_partition_human_authoritative": "true",
        "role_profile": "STRICT_LINKER_PRESENT_V1", "warhead_atoms_json": '["S1"]',
        "linker_atoms_json": '["C2","C3","N4"]',
        "scaffold_atoms_json": canonical_json(list(CHECK_S)).decode("utf-8"),
        "W_L_S_counts_json": "[1,3,17]", "Exact21_count": "21",
        "partition_pairwise_disjoint": "true", "partition_exhaustive": "true",
        "warhead_connected": "true", "linker_connected": "true", "scaffold_connected": "true",
        "reactive_S1_in_W": "true", "minimal_seed_atoms_json": '["C5","O21","C6"]',
        "primary_anchor_atom_id": "C5", "global_canonical_task_count": "5",
        "B3_present": "true", "sixth_task": "false",
        "structurally_applicable_task_ids_json": "[0,1,2,3,4]",
        "task_applicability_determined": "true",
        "authoritative_task_labels_created": "false", "event_task_label_rows_materialized": "false",
        "human_training_use_disposition": "NOT_APPLICABLE",
        "training_use_human_authoritative": "true", "human_training_excluded": "false",
        "future_training_admission_candidate": "false", "formal_training_admitted": "false",
        "training_mask_targets_available_now": "false", "current_runtime_model_usable": "false",
        "READY_FOR_TRAINING": "false", "supporting_PRE_source_graph_count": "0",
        "PRE_source_graph_present": "false", "PRE_source_graph_count": "0", "PRE_mapping_count": "0",
        "PRE_mapping_status": "PRE_SOURCE_GRAPH_NOT_AVAILABLE", "PRE_status": "PRE_REACTION_UNRESOLVED",
        "PRE_topology_authority": "false", "PRE_geometry_authority": "false",
        "POST_source_evidence_available": "true", "explicit_covalent_evidence": "true",
        "POST_geometry_training_authority": "false", "reusable_chemistry_authority": "false",
        "reusable_pair_authority": "false", "reusable_role_authority": "false",
        "projection_of_frozen_formal_human_authority": "true",
        "new_human_authority_created_by_ingestion": "false",
    }
    for row in rows:
        for key, value in exact.items():
            if row.get(key) != value:
                fail("MATRIX_SEMANTIC_DRIFT:" + key)
    role = snapshot.get("selected_role_partition")
    if type(role) is not dict or role.get("boundary_bonds") != list(owner.BOUNDARY_BONDS) or role.get("minimal_seed_atom_ids") != list(CHECK_SEED) or role.get("primary_anchor_atom_id") != "C5":
        fail("SNAPSHOT_ROLE_BOUNDARY_SEED_DRIFT")
    generic_snapshot = snapshot.get("generic_Exact11_compatibility")
    if type(generic_snapshot) is not dict or generic_snapshot.get("accepted_fact_count") != 4 or generic_snapshot.get("generic_fact_field_count") != 11 or generic_snapshot.get("rich_fields_leaked") is not False:
        fail("SNAPSHOT_GENERIC_EXACT11_DRIFT")
    required_counts = {
        "event_count": 4, "chemistry_positive_event_count": 4,
        "task_not_relevant_event_count": 4,
        "task_domain_negative_chemistry_positive_event_count": 4,
        "pair_authoritative_event_count": 4, "role_authoritative_event_count": 4,
        "STRICT_profile_event_count": 4,
        "canonical_mask_structural_labels_available_event_count": 4,
        "task_applicability_determined_event_count": 4,
        "authoritative_task_label_event_count": 0,
        "training_NOT_APPLICABLE_event_count": 4,
        "future_training_admission_candidate_count": 0,
        "formal_training_admitted_count": 0, "POST_source_evidence_count": 4,
        "POST_training_authority_count": 0, "PRE_authority_count": 0,
    }
    for key, value in required_counts.items():
        if summary.get(key) != value:
            fail("SUMMARY_COUNT_DRIFT:" + key)
    if summary.get("completed_lane") != "COMPLETED_TASK_DOMAIN_NEGATIVE":
        fail("SUMMARY_COMPLETED_LANE_DRIFT")
    if manifest.get("manifest_self_SHA256_recorded") is not False or manifest.get("candidate_publication_file_count") != 7 or manifest.get("output_artifact_count") != 4 or manifest.get("active_source_binding_count") != 14:
        fail("MANIFEST_BOUNDARY_DRIFT")
    return {
        "event_count": 4, "matrix_column_count": len(owner.MATRIX_HEADER),
        "independent_structural_proof": {key: graph[key] for key in graph if key not in {"heavy_atoms", "heavy_bonds"}},
        "runtime_and_generic": runtime_generic, "current_census": census,
        "applicable_task_ids": [0, 1, 2, 3, 4], "B3_present": True,
        "sixth_task": False, "matrix_connectivity_claims_source_verified": True,
    }


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
    first, second = owner.build_artifacts_v1(repo_root), owner.build_artifacts_v1(repo_root)
    if first != second or first != artifacts:
        fail("DETERMINISTIC_OUTPUT_BYTES_DRIFT")
    if materialized.get("READY_FOR_EXTERNAL_REVIEW") is not True or materialized.get("READY_FOR_TRAINING") is not False:
        fail("READINESS_GATE_DRIFT")
    result = {
        "status": "PASS", "lifecycle": lifecycle, "candidate_Exact7": inventory,
        "source_bindings": sources, "materialized": materialized, "projection": projection,
        "TP2_COMPLETED_DECISION_INGESTION_V1_PASS": True, "EVENT_COUNT": 4,
        "COMPLETED_LANE": "COMPLETED_TASK_DOMAIN_NEGATIVE",
        "TASK_RELEVANCE": "NOT_RELEVANT", "CHEMISTRY": "POSITIVE",
        "GENERIC_LEGACY_STATUS": "COMPLETED_HUMAN_NEGATIVE",
        "GENERIC_TRAINING_DISPOSITION": "NOT_APPLICABLE", "HUMAN_TRAINING_EXCLUDED": False,
        "PAIR_AUTHORITY_COUNT": 4, "ROLE_AUTHORITY_COUNT": 4,
        "ROLE_PROFILE": "STRICT_LINKER_PRESENT_V1", "W_COUNT": 1, "L_COUNT": 3, "S_COUNT": 17,
        "ROLE_BOUNDARIES": ["S1-C2/SING", "N4-C5/SING"],
        "MINIMAL_SEED": ["C5", "O21", "C6"], "PRIMARY_ANCHOR": "C5",
        "TASK_APPLICABILITY_DETERMINED": True, "APPLICABLE_TASK_IDS": [0, 1, 2, 3, 4],
        "EXACT5_B3_PRESENT": True, "SIXTH_TASK": False,
        "AUTHORITATIVE_TASK_LABELS_CREATED": False,
        "EVENT_TASK_LABEL_ROWS_MATERIALIZED": False,
        "FUTURE_TRAINING_ADMISSION_CANDIDATE": False,
        "FORMAL_TRAINING_ADMITTED": False, "TRAINING_MASK_TARGETS_AVAILABLE_NOW": False,
        "PRE_MAPPING_STATUS": "PRE_SOURCE_GRAPH_NOT_AVAILABLE",
        "PRE_STATUS": "PRE_REACTION_UNRESOLVED", "POST_SOURCE_EVIDENCE_COUNT": 4,
        "POST_GEOMETRY_TRAINING_AUTHORITY_COUNT": 0,
        "REUSABLE_AUTHORITY_CREATED": False, "READY_FOR_TRAINING": False,
        "TRAINING_STARTED": False, "RECONCILIATION": False, "CENSUS_REFRESH": False,
        "QUEUE_REFRESH": False,
        "GIT_REPOSITORY_CLEAN_EXCEPT_EXACT7_UNTRACKED": lifecycle["profile"] == CANDIDATE_UNTRACKED,
        "COMMIT": False, "PUSH": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, owner.TP2IngestionSafetyError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1) from error
