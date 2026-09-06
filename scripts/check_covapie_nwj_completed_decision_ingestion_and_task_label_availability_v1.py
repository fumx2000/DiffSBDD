#!/usr/bin/env python3
"""Independently check an NWJ ingestion Exact7 candidate or successor."""

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
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_nwj_completed_decision_ingestion_and_task_label_availability_v1 as owner,
)


ERROR = "COVAPIE_NWJ_INGESTION_CHECK_V1_ERROR"
CANDIDATE_UNTRACKED = "CANDIDATE_UNTRACKED"
TRACKED_CLEAN = "TRACKED_CLEAN"
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
PROTECTED_PATHS = (
    "data/raw",
    "checkpoints",
    "equivariant_diffusion",
    "lightning_modules.py",
    "dataset.py",
    "data/prepare_crossdocked.py",
)

FORMAL_BYTES = 24265
FORMAL_SHA256 = "1e53df67e44b61d8103148036cf59d976974d7481754af700cc0cd89dfadeaff"
VALIDATOR_BYTES = 68924
VALIDATOR_SHA256 = "1cc1bb5ea615bcf662ac1410dc15ef3aa82991e6243dec461cb8ada20078336d"
EVENT_BYTES = 8973
EVENT_SHA256 = "b19881efa97e8f61e6ae3dab9f44f6343c32fcc3c721929ab91f00b484136b2c"
GRAPH_BYTES = 33453
GRAPH_SHA256 = "f12d9132b47e1390aad1fa14dbd0f76c74be64730a42b89f6691eade3833a8a4"
CCD_BYTES = 10154
CCD_SHA256 = "938d3d511360aecf600222289e6cd436aee223c52da62d0e0c613e558d912c3e"

CHECK_W = ("CAV", "OAE")
CHECK_L: tuple[str, ...] = ()
CHECK_S = (
    "C2",
    "C4",
    "C5",
    "C6",
    "CAG",
    "CAH",
    "CAI",
    "CAJ",
    "CAK",
    "CAL",
    "CAM",
    "CAN",
    "CAO",
    "CAX",
    "CAY",
    "CAZ",
    "CBA",
    "N1",
    "N3",
    "NAA",
    "NAB",
    "NAS",
    "NBF",
)
CHECK_SEED = ("CAX", "CAI", "CAK")
CHECK_EVENTS = (
    ("COVAPIE_CYS_SG_EVENT_V1:4CM5:A:CYS:168-:SG:F:NWJ:CAV", "674", "1.799966"),
    ("COVAPIE_CYS_SG_EVENT_V1:4CM5:B:CYS:168-:SG:H:NWJ:CAV", "675", "1.822254"),
    ("COVAPIE_CYS_SG_EVENT_V1:4CM5:C:CYS:168-:SG:J:NWJ:CAV", "676", "1.818468"),
    ("COVAPIE_CYS_SG_EVENT_V1:4CM5:D:CYS:168-:SG:L:NWJ:CAV", "677", "1.828650"),
)


def fail(reason: str) -> None:
    raise RuntimeError(ERROR + ":" + reason)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ("git", *args),
        cwd=repo_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        fail("GIT_COMMAND_FAILED:" + ":".join(args))
    return result.stdout.strip()


def is_ancestor(repo_root: Path, older: str, newer: str) -> bool:
    result = subprocess.run(
        ("git", "merge-base", "--is-ancestor", older, newer),
        cwd=repo_root,
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if result.returncode not in (0, 1):
        fail("GIT_ANCESTRY_CHECK_FAILED")
    return result.returncode == 0


def file_record(repo_root: Path, relative: Path) -> dict[str, object]:
    path = repo_root / relative
    try:
        metadata = path.lstat()
        payload = path.read_bytes()
    except OSError as error:
        raise RuntimeError(
            ERROR + ":FILE_READ_FAILED:" + relative.as_posix()
        ) from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        fail("FILE_NOT_REGULAR_NON_SYMLINK:" + relative.as_posix())
    if metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
        fail("FILE_EXECUTABLE:" + relative.as_posix())
    if (
        not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
        or b"\r" in payload
        or b"\x00" in payload
        or payload.startswith(b"\xef\xbb\xbf")
    ):
        fail("FILE_TEXT_HYGIENE_INVALID:" + relative.as_posix())
    try:
        payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise RuntimeError(
            ERROR + ":FILE_UTF8_INVALID:" + relative.as_posix()
        ) from error
    return {
        "path": relative.as_posix(),
        "bytes": len(payload),
        "LOC": len(payload.decode("utf-8").splitlines()),
        "SHA256": sha256(payload),
        "mode": stat.filemode(metadata.st_mode),
        "class": "REGULAR_NON_SYMLINK_NON_EXECUTABLE",
    }


def check_git_lifecycle(repo_root: Path) -> dict[str, object]:
    branch = git(repo_root, "branch", "--show-current")
    head = git(repo_root, "rev-parse", "HEAD")
    origin = git(repo_root, "rev-parse", "origin/main")
    if branch != "main":
        fail("BRANCH_NOT_MAIN")
    if not is_ancestor(repo_root, owner.BASELINE_COMMIT, head):
        fail("BASELINE_NOT_ANCESTOR_OF_HEAD")
    if not is_ancestor(repo_root, owner.BASELINE_COMMIT, origin):
        fail("BASELINE_NOT_ANCESTOR_OF_ORIGIN_MAIN")
    if not is_ancestor(repo_root, origin, head):
        fail("ORIGIN_MAIN_NOT_ANCESTOR_OF_HEAD")
    try:
        behind, ahead = (
            int(value)
            for value in git(
                repo_root,
                "rev-list",
                "--left-right",
                "--count",
                "origin/main...HEAD",
            ).split()
        )
    except ValueError as error:
        raise RuntimeError(ERROR + ":AHEAD_BEHIND_PARSE_FAILED") from error
    if behind != 0:
        fail("HEAD_BEHIND_ORIGIN_MAIN")

    tracked_modified = git(repo_root, "diff", "--name-only").splitlines()
    staged = git(repo_root, "diff", "--cached", "--name-only").splitlines()
    untracked = git(
        repo_root, "ls-files", "--others", "--exclude-standard"
    ).splitlines()
    expected = [path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS]
    expected_set = set(expected)
    if tracked_modified:
        fail("TRACKED_MODIFICATIONS_PRESENT")
    if staged:
        fail("STAGED_INDEX_NOT_EMPTY")
    if set(untracked) == expected_set and len(untracked) == 7:
        profile = CANDIDATE_UNTRACKED
        if (
            head != owner.BASELINE_COMMIT
            or origin != owner.BASELINE_COMMIT
            or ahead != 0
        ):
            fail("CANDIDATE_UNTRACKED_BASELINE_PROFILE_DRIFT")
    elif not untracked:
        profile = TRACKED_CLEAN
        tracked = set(git(repo_root, "ls-files", "--", *expected).splitlines())
        if tracked != expected_set:
            fail("TRACKED_CLEAN_EXACT7_NOT_TRACKED")
        changed = set(
            git(
                repo_root,
                "diff",
                "--name-only",
                owner.BASELINE_COMMIT + "..HEAD",
            ).splitlines()
        )
        if not expected_set.issubset(changed):
            fail("TRACKED_CLEAN_EXACT7_NOT_DESCENDED_FROM_BASELINE")
    else:
        fail("ORDINARY_UNTRACKED_NOT_EXACT7_OR_EMPTY")

    changed = set(
        git(
            repo_root,
            "diff",
            "--name-only",
            owner.BASELINE_COMMIT + "..HEAD",
        ).splitlines()
    )
    protected_changed = {
        path
        for path in changed
        if any(path == root or path.startswith(root + "/") for root in PROTECTED_PATHS)
    }
    if protected_changed:
        fail("PROTECTED_HISTORY_CHANGED")
    history_scope = expected_set | changed
    forbidden = {path for path in history_scope if path.endswith(FORBIDDEN_SUFFIXES)}
    if forbidden:
        fail("FORBIDDEN_SUFFIX_IN_CANDIDATE_HISTORY")
    return {
        "profile": profile,
        "branch": branch,
        "HEAD": head,
        "origin_main": origin,
        "ahead": ahead,
        "behind": behind,
        "tracked_modification_count": 0,
        "staged_count": 0,
        "ordinary_untracked_count": len(untracked),
        "ordinary_untracked_paths": untracked,
        "raw_changed_since_baseline_count": 0,
        "protected_source_changed_since_baseline_count": 0,
        "forbidden_candidate_file_count": 0,
    }


def strict_json(payload: bytes, label: str) -> dict[str, object]:
    if payload.startswith(b"\xef\xbb\xbf") or b"\x00" in payload:
        fail("JSON_TEXT_INVALID:" + label)

    def pairs_hook(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                fail("JSON_DUPLICATE_KEY:" + label + ":" + key)
            result[key] = value
        return result

    try:
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=pairs_hook,
            parse_constant=lambda value: fail("JSON_NONFINITE:" + label),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError(ERROR + ":JSON_INVALID:" + label) from error
    if type(value) is not dict:
        fail("JSON_ROOT_NOT_OBJECT:" + label)
    return value


def parse_csv(payload: bytes, label: str) -> list[dict[str, str]]:
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    except UnicodeDecodeError as error:
        raise RuntimeError(ERROR + ":CSV_INVALID:" + label) from error
    if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
        fail("CSV_HEADER_INVALID:" + label)
    rows = list(reader)
    if any(None in row for row in rows):
        fail("CSV_WIDTH_INVALID:" + label)
    return rows


def _expect(mapping: object, expected: Mapping[str, object], reason: str) -> None:
    if type(mapping) is not dict:
        fail(reason + ":NOT_OBJECT")
    for key, value in expected.items():
        if type(mapping.get(key)) is not type(value) or mapping.get(key) != value:
            fail(reason + ":" + key)


def independently_check_frozen_sources(repo_root: Path) -> dict[str, object]:
    specs = (
        (repo_root.parent / owner.FORMAL_DECISION_RELATIVE, FORMAL_BYTES, FORMAL_SHA256),
        (repo_root.parent / owner.FORMAL_VALIDATOR_RELATIVE, VALIDATOR_BYTES, VALIDATOR_SHA256),
        (repo_root.parent / owner.EVENT_EVIDENCE_RELATIVE, EVENT_BYTES, EVENT_SHA256),
        (repo_root.parent / owner.GRAPH_EVIDENCE_RELATIVE, GRAPH_BYTES, GRAPH_SHA256),
        (repo_root.parent / owner.CCD_RELATIVE, CCD_BYTES, CCD_SHA256),
    )
    records = []
    payloads: dict[Path, bytes] = {}
    for path, expected_bytes, expected_sha in specs:
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
        except OSError as error:
            raise RuntimeError(ERROR + ":FROZEN_SOURCE_READ_FAILED") from error
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            fail("FROZEN_SOURCE_CLASS_INVALID")
        if len(payload) != expected_bytes or sha256(payload) != expected_sha:
            fail("FROZEN_SOURCE_IDENTITY_DRIFT:" + path.name)
        payloads[path] = payload
        records.append(
            {"name": path.name, "bytes": len(payload), "SHA256": sha256(payload)}
        )

    formal = strict_json(
        payloads[repo_root.parent / owner.FORMAL_DECISION_RELATIVE],
        "INDEPENDENT_FORMAL",
    )
    _expect(
        formal,
        {
            "schema_version": "covapie_nwj_exact4_formal_human_decision_v1",
            "record_role": "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY",
        },
        "FORMAL_ROOT_DRIFT",
    )
    _expect(
        formal.get("formal_state"),
        {
            "approved": True,
            "unsigned": False,
            "authorization_origin": "EXTERNAL_HUMAN_CHAT_REVIEW",
            "reviewer_id": "fmx",
            "attestor_id": "fmx",
            "human_authority_created": True,
            "human_decision_created": True,
            "human_review_completed": True,
            "formal_authority_created": True,
            "formal_decision_created": True,
        },
        "FORMAL_STATE_DRIFT",
    )
    _expect(
        formal.get("sample_identity"),
        {
            "PDB": "4CM5",
            "ligand_component_id": "NWJ",
            "review_unit_id": owner.EXPECTED_REVIEW_UNIT_ID,
            "scope": owner.EXPECTED_SCOPE,
            "event_count": 4,
            "canonical_event_ids": [row[0] for row in CHECK_EVENTS],
            "scaleup_event_ranks": [674, 675, 676, 677],
        },
        "FORMAL_IDENTITY_DRIFT",
    )
    decisions = formal.get("formal_decisions")
    if type(decisions) is not dict:
        fail("FORMAL_DECISIONS_MISSING")
    _expect(
        decisions.get("D1_observed_covalent_chemistry"),
        {
            "decision": "POSITIVE",
            "human_authoritative_sample_conclusion": "stable Cys168 thioester linkage",
            "initial_thioacetal_then_oxidation": "AUTHOR_PROPOSED_PRESUMED_MECHANISM_ONLY",
            "asserted_as_proven_mechanism": False,
        },
        "FORMAL_D1_DRIFT",
    )
    _expect(
        decisions.get("D2_generation_domain_relevance"),
        {
            "decision": "IN_DOMAIN",
            "TbPTR1_Ki_app_micromolar": 0.2,
            "T_b_brucei_IC50_micromolar": 7.75,
        },
        "FORMAL_D2_DRIFT",
    )
    _expect(
        decisions.get("D3_reactive_pair"),
        {
            "protein_atom": "SG",
            "ligand_atom": "CAV",
            "scope": owner.EXPECTED_SCOPE,
            "reusable_pair_authority": False,
            "ligand_wide_authority": False,
            "cross_structure_generalization": False,
        },
        "FORMAL_D3_DRIFT",
    )
    _expect(
        decisions.get("D4_role_partition"),
        {
            "selected_candidate": "CANDIDATE_A_DIRECT_FORMYL",
            "role_profile": "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
            "candidate_B_runtime_valid_nonselected_alternative": True,
            "candidate_B_selected": False,
            "candidate_B_authoritative": False,
        },
        "FORMAL_D4_DRIFT",
    )
    _expect(
        decisions.get("D5_structural_task_applicability"),
        {
            "decision": [0, 3, 4],
            "task_label_authority": False,
            "event_task_label_rows_materialized": False,
            "mask_tensor_targets_created": False,
        },
        "FORMAL_D5_DRIFT",
    )
    _expect(
        decisions.get("D6_later_training_use"),
        {
            "decision": "INCLUDE",
            "future_training_admission_candidate": True,
            "formal_training_admitted": False,
            "training_admission_created": False,
            "training_materialization_allowed": False,
            "READY_FOR_TRAINING": False,
            "TRAINING_STARTED": False,
        },
        "FORMAL_D6_DRIFT",
    )
    selected = formal.get("selected_role_context")
    _expect(
        selected,
        {
            "candidate_id": "CANDIDATE_A_DIRECT_FORMYL",
            "warhead_atom_ids": list(CHECK_W),
            "linker_atom_ids": [],
            "scaffold_atom_ids": list(CHECK_S),
            "task_ids": [0, 3, 4],
        },
        "FORMAL_SELECTED_ROLE_DRIFT",
    )
    _expect(
        selected.get("minimal_seed"),
        {
            "atom_ids": list(CHECK_SEED),
            "primary_scaffold_side_anchor": "CAX",
            "runtime_valid": True,
        },
        "FORMAL_SELECTED_SEED_DRIFT",
    )
    alternative = formal.get("retained_nonselected_alternative")
    _expect(
        alternative,
        {
            "candidate_id": "CANDIDATE_B_PHENYL_LINKER",
            "candidate_B_runtime_valid_nonselected_alternative": True,
            "candidate_B_selected": False,
            "candidate_B_authoritative": False,
        },
        "FORMAL_ALTERNATIVE_DRIFT",
    )
    _expect(
        formal.get("PRE_boundary"),
        {
            "candidate_PRE_free_source_graph_count_per_event": 1,
            "source_mapping_count_per_event": 0,
            "PRE_source_mapping_status": "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
            "final_PRE_reaction_status": "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
            "PRE_authority": False,
            "POST_to_PRE_copy": False,
            "PRE_zero_fill": False,
        },
        "FORMAL_PRE_DRIFT",
    )
    _expect(
        formal.get("POST_boundary"),
        {
            "Exact4_observed_POST_geometry": True,
            "explicit_covalent_evidence": True,
            "distance_only": False,
            "POST_geometry_training_authority": False,
            "POST_geometry_training_target_created": False,
        },
        "FORMAL_POST_DRIFT",
    )
    _expect(
        formal.get("readiness"),
        {
            "FORMAL_TRAINING_ADMITTED": False,
            "FEATURE_SEMANTICS_AUDIT_PERFORMED": False,
            "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": True,
            "READY_FOR_TRAINING": False,
            "TRAINING_STARTED": False,
        },
        "FORMAL_READINESS_DRIFT",
    )

    graph = strict_json(
        payloads[repo_root.parent / owner.GRAPH_EVIDENCE_RELATIVE],
        "INDEPENDENT_GRAPH",
    )["CCD_complete_heavy_atom_graph"]
    atom_ids = tuple(sorted(row["atom_id"] for row in graph["atom_inventory"]))
    if atom_ids != tuple(sorted((*CHECK_W, *CHECK_L, *CHECK_S))):
        fail("INDEPENDENT_GRAPH_EXACT25_DRIFT")
    bonds = tuple(
        (row["atom_id_1"], row["atom_id_2"], row["bond_order"])
        for row in graph["bond_inventory"]
    )
    if len(bonds) != 28:
        fail("INDEPENDENT_GRAPH_EXACT28_BONDS_DRIFT")
    role = {
        atom: label
        for label, atoms in (("W", CHECK_W), ("L", CHECK_L), ("S", CHECK_S))
        for atom in atoms
    }
    boundaries = []
    for left, right, order in bonds:
        if role[left] == role[right]:
            continue
        pair = (role[left], role[right])
        if pair == ("S", "W"):
            boundaries.append((left, right, order))
        elif pair == ("W", "S"):
            boundaries.append((right, left, order))
        else:
            fail("INDEPENDENT_GRAPH_UNEXPECTED_BOUNDARY")
    if boundaries != [("CAX", "CAV", "SING")]:
        fail("INDEPENDENT_GRAPH_BOUNDARY_DRIFT")

    source_text = (repo_root / owner.SOURCE_RELATIVE).read_text(encoding="utf-8")
    tree = ast.parse(source_text)
    imported_modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    if "subprocess" in imported_modules or any(
        "validate_nwj_formal_human_decision_v1" in name
        for name in imported_modules
    ):
        fail("PRODUCTION_FORMAL_VALIDATOR_EXECUTABLE_DEPENDENCY")
    return {
        "source_count": 5,
        "records": records,
        "formal_json_independently_validated": True,
        "formal_validator_provenance_identity_only": True,
        "formal_validator_imported": False,
        "formal_validator_executed_by_production": False,
        "formal_validator_subprocessed_by_production": False,
        "independent_graph_exact25": True,
        "independent_boundary": "CAX-CAV/SING",
    }


def independently_check_artifacts(
    repo_root: Path, artifacts: Mapping[str, bytes]
) -> dict[str, object]:
    if set(artifacts) != set(owner.OUTPUT_FILENAMES):
        fail("ARTIFACT_INVENTORY_NOT_EXACT4")
    snapshot = strict_json(artifacts[owner.SNAPSHOT], "SNAPSHOT")
    summary = strict_json(artifacts[owner.SUMMARY], "SUMMARY")
    manifest = strict_json(artifacts[owner.MANIFEST], "MANIFEST")
    rows = parse_csv(artifacts[owner.MATRIX], "MATRIX")
    if len(rows) != 4 or tuple(rows[0]) != owner.MATRIX_HEADER:
        fail("MATRIX_NOT_EXACT4_OR_HEADER_DRIFT")
    if tuple(
        (row["canonical_event_id"], row["scaleup_rank"], row["POST_distance_angstrom"])
        for row in rows
    ) != CHECK_EVENTS:
        fail("MATRIX_EVENT_IDENTITY_OR_POST_DRIFT")
    expected_constant_cells = {
        "PDB": "4CM5",
        "review_unit_id": owner.EXPECTED_REVIEW_UNIT_ID,
        "human_task_relevance_decision": "IN_DOMAIN",
        "human_chemistry_decision": "POSITIVE",
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "CAV",
        "explicit_covalent_evidence": "true",
        "distance_only_inference": "false",
        "pair_authority_scope": owner.EXPECTED_SCOPE,
        "reusable_pair_authority": "false",
        "ligand_wide_authority": "false",
        "cross_structure_generalization": "false",
        "role_profile": "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
        "selected_role_candidate": "CANDIDATE_A_DIRECT_FORMYL",
        "warhead_atom_ids_json": '["CAV","OAE"]',
        "linker_atom_ids_json": "[]",
        "scaffold_atom_ids_json": json.dumps(
            list(CHECK_S), separators=(",", ":")
        ),
        "minimal_seed_atom_ids_json": '["CAX","CAI","CAK"]',
        "primary_anchor": "CAX",
        "boundary_json": '{"bond_order":"SING","scaffold_atom_id":"CAX","warhead_atom_id":"CAV"}',
        "canonical_task_count": "5",
        "B3_present": "true",
        "sixth_task": "false",
        "direct_profile_applicable_task_ids_json": "[0,3,4]",
        "task_label_authority": "false",
        "event_task_label_rows_materialized": "false",
        "mask_tensor_targets_created": "false",
        "training_mask_targets_available_now": "false",
        "candidate_PRE_free_source_graph_count_per_event": "1",
        "source_mapping_count_per_event": "0",
        "PRE_source_mapping_status": "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
        "final_PRE_reaction_status": "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
        "PRE_authority": "false",
        "POST_to_PRE_copy": "false",
        "PRE_zero_fill": "false",
        "Exact4_observed_POST_geometry": "true",
        "POST_geometry_training_authority": "false",
        "POST_geometry_training_target_created": "false",
        "formal_training_admitted": "false",
        "training_admission_created": "false",
        "training_materialization_allowed": "false",
        "parameter_update_authorization": "false",
        "FEATURE_SEMANTICS_AUDIT_PERFORMED": "false",
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": "true",
        "ready_for_training": "false",
        "TRAINING_STARTED": "false",
    }
    for row in rows:
        for key, value in expected_constant_cells.items():
            if row.get(key) != value:
                fail("MATRIX_HIGH_VALUE_CELL_DRIFT:" + key)

    _expect(
        snapshot,
        {
            "projection_of_frozen_formal_human_authority": True,
            "new_human_authority_created_by_ingestion": False,
            "network_required": False,
        },
        "SNAPSHOT_ROOT_DRIFT",
    )
    _expect(
        snapshot.get("sample_identity"),
        {
            "ligand": "NWJ",
            "PDB": "4CM5",
            "review_unit_id": owner.EXPECTED_REVIEW_UNIT_ID,
            "authority_scope": owner.EXPECTED_SCOPE,
            "event_count": 4,
            "scaleup_ranks": [674, 675, 676, 677],
            "canonical_event_ids": [row[0] for row in CHECK_EVENTS],
        },
        "SNAPSHOT_IDENTITY_DRIFT",
    )
    pair = snapshot.get("reactive_pair_authority")
    _expect(
        pair,
        {
            "protein_reactive_atom": "SG",
            "ligand_reactive_atom": "CAV",
            "pair_authority_scope": owner.EXPECTED_SCOPE,
            "sample_level_authoritative": True,
            "reusable_pair_authority": False,
            "ligand_wide_authority": False,
            "cross_structure_generalization": False,
        },
        "SNAPSHOT_PAIR_DRIFT",
    )
    role = snapshot.get("selected_role_partition")
    _expect(
        role,
        {
            "selected_role_candidate": "CANDIDATE_A_DIRECT_FORMYL",
            "role_profile": "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
            "warhead_atom_ids": list(CHECK_W),
            "linker_atom_ids": [],
            "scaffold_atom_ids": list(CHECK_S),
            "minimal_seed_atom_ids": list(CHECK_SEED),
            "primary_anchor": "CAX",
            "boundary": {
                "scaffold_atom_id": "CAX",
                "warhead_atom_id": "CAV",
                "bond_order": "SING",
            },
            "reusable_role_authority": False,
        },
        "SNAPSHOT_ROLE_DRIFT",
    )
    _expect(
        snapshot.get("retained_nonselected_alternative"),
        {
            "candidate_id": "CANDIDATE_B_PHENYL_LINKER",
            "runtime_valid_nonselected_alternative": True,
            "selected": False,
            "authoritative": False,
            "event_labels_created": False,
        },
        "SNAPSHOT_CANDIDATE_B_DRIFT",
    )
    tasks = snapshot.get("canonical_task_contract")
    _expect(
        tasks,
        {
            "global_canonical_task_count": 5,
            "B3_present": True,
            "sixth_task": False,
            "direct_profile_applicable_task_ids": [0, 3, 4],
            "task_label_authority": False,
            "event_task_label_rows_materialized": False,
            "mask_tensor_targets_created": False,
            "training_mask_targets_available_now": False,
        },
        "SNAPSHOT_EXACT5_DRIFT",
    )
    if [row["semantic_long_name"] for row in tasks["global_canonical_tasks"]] != [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]:
        fail("SNAPSHOT_EXACT5_LONG_NAMES_DRIFT")
    _expect(
        snapshot.get("PRE_boundary"),
        {
            "candidate_PRE_free_source_graph_count_per_event": 1,
            "source_mapping_count_per_event": 0,
            "PRE_source_mapping_status": "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
            "final_PRE_reaction_status": "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
            "PRE_authority": False,
            "POST_to_PRE_copy": False,
            "PRE_zero_fill": False,
            "PRE_coordinates_invented": False,
            "PRE_topology_invented": False,
            "leaving_group_invented": False,
            "reagent_invented": False,
            "reaction_edit_invented": False,
        },
        "SNAPSHOT_PRE_DRIFT",
    )
    _expect(
        snapshot.get("POST_boundary"),
        {
            "Exact4_observed_POST_geometry": True,
            "explicit_covalent_evidence": True,
            "distance_only": False,
            "POST_geometry_training_authority": False,
            "POST_geometry_training_target_created": False,
        },
        "SNAPSHOT_POST_DRIFT",
    )
    _expect(
        snapshot.get("training_boundary"),
        {
            "human_training_use_disposition": "INCLUDE",
            "future_training_admission_candidate": True,
            "formal_training_admitted": False,
            "training_admission_created": False,
            "training_materialization_allowed": False,
            "task_label_authority": False,
            "mask_tensor_targets_created": False,
            "parameter_update_authorization": False,
            "FEATURE_SEMANTICS_AUDIT_PERFORMED": False,
            "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": True,
            "READY_FOR_TRAINING": False,
            "TRAINING_STARTED": False,
        },
        "SNAPSHOT_TRAINING_DRIFT",
    )
    _expect(
        summary,
        {
            "event_count": 4,
            "selected_role_profile": "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
            "applicable_task_ids": [0, 3, 4],
            "human_training_use_disposition": "INCLUDE",
            "future_training_admission_candidate": True,
            "formal_training_admitted": False,
            "ready_for_training": False,
            "reconciliation_performed": False,
            "census_refresh_performed": False,
            "queue_refresh_performed": False,
        },
        "SUMMARY_DRIFT",
    )
    _expect(
        manifest,
        {
            "candidate_publication_file_count": 7,
            "candidate_publication_paths": [
                path.as_posix() for path in owner.CANDIDATE_PUBLICATION_PATHS
            ],
            "output_artifact_count": 4,
            "output_paths": [
                path.as_posix() for path in owner.OUTPUT_RELATIVE_PATHS
            ],
            "formal_validator_provenance_identity_only": True,
            "formal_validator_imported": False,
            "formal_validator_executed_by_production": False,
            "formal_validator_subprocessed_by_production": False,
            "manifest_self_SHA256_recorded": False,
            "READY_FOR_TRAINING": False,
            "TRAINING_STARTED": False,
        },
        "MANIFEST_DRIFT",
    )
    _expect(
        manifest.get("operation_boundary"),
        {
            "reconciliation_performed": False,
            "census_refresh_performed": False,
            "queue_refresh_performed": False,
            "dataset_materialization_performed": False,
            "tensor_materialization_performed": False,
            "training_performed": False,
            "commit_performed": False,
            "push_performed": False,
        },
        "MANIFEST_OPERATION_DRIFT",
    )
    active = manifest.get("active_source_bindings")
    if type(active) is not list or len(active) != manifest.get("active_source_binding_count"):
        fail("MANIFEST_ACTIVE_BINDING_COUNT_DRIFT")
    formal_binding = [
        row
        for row in active
        if row.get("path") == owner.FORMAL_DECISION_RELATIVE.as_posix()
    ]
    validator_binding = [
        row
        for row in active
        if row.get("path") == owner.FORMAL_VALIDATOR_RELATIVE.as_posix()
    ]
    if len(formal_binding) != 1 or len(validator_binding) != 1:
        fail("MANIFEST_FORMAL_BINDINGS_NOT_EXACT1")
    _expect(
        formal_binding[0],
        {
            "byte_count": FORMAL_BYTES,
            "SHA256": FORMAL_SHA256,
            "validation_method": "PARSED_AND_INDEPENDENTLY_VALIDATED_AUTHORITY",
        },
        "MANIFEST_FORMAL_BINDING_DRIFT",
    )
    _expect(
        validator_binding[0],
        {
            "byte_count": VALIDATOR_BYTES,
            "SHA256": VALIDATOR_SHA256,
            "validation_method": "PROVENANCE_IDENTITY_ONLY_NOT_IMPORTED_EXECUTED_OR_SUBPROCESSED",
        },
        "MANIFEST_VALIDATOR_BINDING_DRIFT",
    )
    for value in manifest.values():
        if type(value) is str and value.startswith("/"):
            fail("MANIFEST_ABSOLUTE_PATH_VALUE")
    return {
        "event_count": 4,
        "matrix_column_count": len(owner.MATRIX_HEADER),
        "selected_candidate": "CANDIDATE_A_DIRECT_FORMYL",
        "candidate_B_nonselected_provenance": True,
        "pair": "SG:CAV",
        "applicable_task_ids": [0, 3, 4],
        "Exact5_B3_no_sixth": True,
        "PRE_mapping_status": "PRE_SOURCE_GRAPH_MAPPING_INCOMPATIBLE",
        "READY_FOR_TRAINING": False,
        "independent_artifact_validation": True,
    }


def main() -> int:
    repo_root = REPO_ROOT
    lifecycle = check_git_lifecycle(repo_root)
    file_records = [
        file_record(repo_root, path) for path in owner.CANDIDATE_PUBLICATION_PATHS
    ]
    sources = independently_check_frozen_sources(repo_root)
    artifacts = {
        name: (repo_root / owner.OUTPUT_ROOT_RELATIVE / name).read_bytes()
        for name in owner.OUTPUT_FILENAMES
    }
    independent = independently_check_artifacts(repo_root, artifacts)
    owner_result = owner.check_materialized_v1(repo_root)
    if owner_result.get("status") != "PASS":
        fail("OWNER_MATERIALIZED_CHECK_FAILED")
    result = {
        "COVAPIE_NWJ_COMPLETED_DECISION_INGESTION_V1_PASS": True,
        "NWJ_COMPLETED_DECISION_INGESTION_V1_PASS": True,
        "mode": "READ_ONLY_CHECK",
        "lifecycle": lifecycle,
        "files": file_records,
        "frozen_sources": sources,
        "independent_artifacts": independent,
        "owner_materialized_check": owner_result,
        "candidate_publication_file_count": 7,
        "output_artifact_count": 4,
        "PROJECTION_OF_FROZEN_FORMAL_HUMAN_AUTHORITY": True,
        "NEW_HUMAN_AUTHORITY_CREATED_BY_INGESTION": False,
        "SELECTED_ROLE_CANDIDATE": "CANDIDATE_A_DIRECT_FORMYL",
        "DIRECT_PROFILE_APPLICABLE_TASK_IDS": [0, 3, 4],
        "TASK_LABEL_AUTHORITY": False,
        "EVENT_TASK_LABEL_ROWS_MATERIALIZED": False,
        "MASK_TENSOR_TARGETS_CREATED": False,
        "FORMAL_TRAINING_ADMITTED": False,
        "TRAINING_ADMISSION_CREATED": False,
        "TRAINING_MATERIALIZATION_ALLOWED": False,
        "RECONCILIATION_PERFORMED": False,
        "CENSUS_REFRESH_PERFORMED": False,
        "QUEUE_REFRESH_PERFORMED": False,
        "FEATURE_SEMANTICS_AUDIT_PERFORMED": False,
        "FEATURE_SEMANTICS_AUDIT_REQUIRED_BEFORE_TRAINING": True,
        "READY_FOR_TRAINING": False,
        "TRAINING_STARTED": False,
        "COMMIT_PERFORMED": False,
        "PUSH_PERFORMED": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
