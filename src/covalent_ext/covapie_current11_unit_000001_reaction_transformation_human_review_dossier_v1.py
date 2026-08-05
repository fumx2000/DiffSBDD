"""Build the non-authoritative UNIT_000001 transformation review dossier.

The sole public API is metadata-only, read-only, and fail closed.  It binds the
controlled editable review workspace, its immutable acquisition template, and
the existing family/rule review aids before returning an in-memory Exact8.
It never supplies transformation answers or changes review authority.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import stat
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence

from covalent_ext import (
    covapie_current11_reaction_transformation_evidence_overlay_contract_v1
    as overlay,
)
from covalent_ext import (
    covapie_current11_unit_000001_controlled_editable_reaction_transformation_review_copy_v1
    as editable,
)


__all__ = (
    "build_covapie_current11_unit_000001_reaction_transformation_"
    "human_review_dossier_v1",
)


DOSSIER_VERSION = (
    "covapie_current11_unit_000001_reaction_transformation_"
    "human_review_dossier_v1"
)
ERROR = f"{DOSSIER_VERSION}_validation_failed"
BASE_COMMIT = "9fbb1da5da504e6dadd89ace90a9e5959f1ba3de"
BASE_TREE = "323259cf0d0ce878a9a6a98592944a6a73ab842d"
BASE_PARENT = "5bb379a0b5226d6532dfb1a934ba09621c67dbd8"
BASE_SUBJECT = "add CovaPIE controlled review umask portability fixture v1"
CONTROLLED_REVIEW_FORMAL_CANDIDATE_COMMIT = BASE_PARENT
CONTROLLED_REVIEW_TREE = "2da4b67a4621eaba9408273c66e0f4d473354eee"
CONTROLLED_REVIEW_PARENT = "dfc5dd59f4fff16b2bd85e321a277cdfe8aa9713"
CONTROLLED_REVIEW_SUBJECT = (
    "add CovaPIE Current11 controlled editable reaction transformation "
    "review copy v1"
)
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE Current11 reaction transformation human review dossier v1"
)
BRANCH = "main"
PUBLICATION_SCHEME = "exclusive_real_directory_non_authoritative_review_aid_v1"

REVIEW_UNIT_ID = "CURRENT11_REACTION_TRANSFORMATION_REVIEW_UNIT_000001"
PARENT_REVIEW_UNIT_ID = "CURRENT11_FAMILY_RULE_APPROVAL_REVIEW_UNIT_000001"
REACTION_FAMILY_ID = "COVAPIE_CYS_SG_REACTION_FAMILY_11AA213C661B48E3"
WARHEAD_RULE_ID = "COVAPIE_CYS_SG_WARHEAD_RULE_106441A31FA4F951"
CANDIDATE_RULE_SHA256 = (
    "106441a31fa4f9516c174c5a0fa89709e820ebeeff419ba30883ea34a1c26bb6"
)

README_FILE = "README.md"
GRAPH_FILE = "candidate_local_graph.svg"
SUMMARY_FILE = "frozen_transformation_review_summary.json"
QUESTIONNAIRE_FILE = "human_transformation_evidence_questionnaire.md"
GAP_FILE = "sample_transformation_gap_evidence.csv"
SOURCE_FILE = "source_authority_inventory_snapshot.csv"
SCHEMA_FILE = "structured_json_schema_templates.json"
MANIFEST_FILE = "dossier_manifest.json"
DOSSIER_FILES = (
    README_FILE,
    GRAPH_FILE,
    SUMMARY_FILE,
    QUESTIONNAIRE_FILE,
    GAP_FILE,
    SOURCE_FILE,
    SCHEMA_FILE,
    MANIFEST_FILE,
)
COPIED_FILES = (GRAPH_FILE, GAP_FILE, SOURCE_FILE, SCHEMA_FILE)

EDITABLE_RELATIVE = "manual-review/current11-reaction-transformation-review-v1"
IMMUTABLE_NAME = (
    "current11-reaction-transformation-evidence-acquisition-template-v1"
)
IMMUTABLE_RELATIVE = f"manual-review/{IMMUTABLE_NAME}"
IMMUTABLE_OBJECT_NAME = f".{IMMUTABLE_NAME}.object-1p9gz5wu"
FAMILY_WORKSPACE_RELATIVE = "manual-review/current11-family-rule-approval-v1"
FAMILY_DOSSIER_RELATIVE = (
    "manual-review-aids/current11-family-rule-approval-v1/"
    f"{PARENT_REVIEW_UNIT_ID}"
)
DOSSIER_PARENT_RELATIVE = (
    "manual-review-aids/current11-reaction-transformation-review-v1"
)
DOSSIER_RELATIVE = f"{DOSSIER_PARENT_RELATIVE}/{REVIEW_UNIT_ID}"

EDITABLE_IDENTITY = (49, 178292049034)
IMMUTABLE_CANONICAL_IDENTITY = (49, 177964065736)
IMMUTABLE_OBJECT_IDENTITY = (49, 178292049039)
FAMILY_WORKSPACE_CANONICAL_IDENTITY = (49, 177964064880)
FAMILY_WORKSPACE_OBJECT_IDENTITY = (49, 177964064865)
FAMILY_DOSSIER_IDENTITY = (49, 177964065463)

EDITABLE_INITIAL_FILE_SHA256 = {
    "README.md": "a8c9710c62b75185715b9b10ee018add7c268951b3584782fdf2ef95d30aa830",
    "editable_review_manifest.json": "9ba268f512df012c4a2ca0c01f1d72d4ced44ad7d440fbb1b4da0c84f595ed19",
    GAP_FILE: "599c75f0f97896c0eea73dbde5041a446f23cb5d30e7da36c186a908561e1134",
    SOURCE_FILE: "fb638a9573cfba0561879b8f8b030c453bd5b3fe693c983eb6fa65f1b7cc4e28",
    SCHEMA_FILE: "ddde07b4b28ee45163d0cb09a9e08ea8712c255a20b1b7fd72dbb7da110f07c6",
    "transformation_evidence_worklist.csv": "c7063e8070de3ecd1fdf4dfc19ffd91ef09dbeac48d80fbc6f01c9369d647423",
}
EDITABLE_REFERENCE_FILES = (
    "README.md",
    SCHEMA_FILE,
    GAP_FILE,
    SOURCE_FILE,
    "editable_review_manifest.json",
)
EDITABLE_REFERENCE_FILE_SHA256 = {
    name: EDITABLE_INITIAL_FILE_SHA256[name] for name in EDITABLE_REFERENCE_FILES
}
INITIAL_BLANK_WORKLIST_SHA256 = EDITABLE_INITIAL_FILE_SHA256[
    "transformation_evidence_worklist.csv"
]
EDITABLE_LIVE_WORKLIST_BINDING = "exact41_frozen16_only_future25_mutable_v1"
EDITABLE_INITIAL_SNAPSHOT_SEMANTICS = "initial_blank_workspace_snapshot_v1"
IMMUTABLE_SHA256 = dict(editable.SOURCE_FILE_SHA256)
FAMILY_WORKSPACE_SHA256 = dict(overlay.WORKSPACE_SHA256)
FAMILY_DOSSIER_SHA256 = dict(overlay.DOSSIER_SHA256)

MODULE_PATH = (
    "src/covalent_ext/covapie_current11_unit_000001_reaction_transformation_"
    "human_review_dossier_v1.py"
)
SCRIPT_PATH = (
    "scripts/materialize_covapie_current11_unit_000001_reaction_"
    "transformation_human_review_dossier_v1.py"
)
TEST_PATH = (
    "tests/test_covapie_current11_unit_000001_reaction_transformation_"
    "human_review_dossier_v1.py"
)
GUIDE_PATH = (
    "docs/covapie_current11_unit_000001_reaction_transformation_"
    "human_review_dossier_v1_guide.md"
)
CANDIDATE_PATHS = tuple(sorted((MODULE_PATH, SCRIPT_PATH, TEST_PATH, GUIDE_PATH)))
CONTROLLED_REVIEW_SHA256 = {
    editable.GUIDE_PATH: "608117659af1ddf54d5275aba8b3ea4166dd94bc2afa7f446917d4dd9fb1f035",
    editable.SCRIPT_PATH: "56d13787940fdc40e0ffa60675edc0af8cfc83e98ff54c119e82d5f198660dd8",
    editable.MODULE_PATH: "9634451caa657501099cb1ba67a9e5c06e7e2aa507ebacdcbb84cccfee64cd75",
    editable.TEST_PATH: "e7068c81b739af014190a040ed3c354074619dfaab8dc7dc8d4646761e5e6520",
}

SAMPLES = (
    {
        "sample_index_row_id": "CYS_SG_SAMPLE_INDEX_000008",
        "pdb_id": "1AYU",
        "ligand_identity": "INA",
        "ligand_reactive_atom_id": "C21",
        "target_residue_atom": "CYS:SG",
        "effective_boundary_cardinality": 2,
    },
    {
        "sample_index_row_id": "CYS_SG_SAMPLE_INDEX_000010",
        "pdb_id": "1AYW",
        "ligand_identity": "IN3",
        "ligand_reactive_atom_id": "C21",
        "target_residue_atom": "CYS:SG",
        "effective_boundary_cardinality": 2,
    },
)

README_TEXT = """# CovaPIE Current11 transformation human review dossier v1

This Exact8 is a non-authoritative human review aid. It is not the formal
worklist, it cannot be submitted directly, and every file in this dossier is
reference-only. The formal editable file remains
`STATE_ROOT/manual-review/current11-reaction-transformation-review-v1/transformation_evidence_worklist.csv`.
Updating that worklist is a later, independent controlled step.

The candidate graph is not post-state authority. The pre-reaction center
bond-order sum 4 and conditional sum 5 are conflict/gap signals only; they do
not determine a transformation. Missing does not mean not_claimed, and an
empty string does not mean an explicit reviewed empty list. Every answer must
be supplied explicitly by a human reviewer or curator.

Completed evidence still requires independent semantic validation and
identity/full-semantics attestation. The feature-semantics audit remains
required before training. `ready_for_training=false`.
"""

QUESTION_SPECS = tuple(
    (
        field,
        f"What human-reviewed evidence establishes `{field}`?",
        (
            "canonical JSON conforming to structured_json_schema_templates.json"
            if field.endswith("_json")
            else "explicit human-reviewed scalar value"
        ),
    )
    for field in overlay.FUTURE_FIELDS
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _is_hex(value: object, length: int) -> bool:
    return (
        type(value) is str
        and len(value) == length
        and re.fullmatch(r"[0-9a-f]+", value) is not None
    )


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return (
            json.dumps(
                value,
                sort_keys=True,
                indent=2,
                ensure_ascii=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("ascii")
    except (TypeError, ValueError) as error:
        raise ValueError(ERROR) from error


def _strict_json(payload: bytes, expected_type: type) -> Any:
    try:
        if (
            type(payload) is not bytes
            or not payload
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\x00" in payload
        ):
            raise ValueError(ERROR)
        text = payload.decode("utf-8")
        value = json.loads(text)
        if (
            not text.endswith("\n")
            or text.endswith("\n\n")
            or type(value) is not expected_type
            or _canonical_json_bytes(value) != payload
        ):
            raise ValueError(ERROR)
        return value
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _strict_csv(payload: bytes, fields: Sequence[str]) -> list[dict[str, str]]:
    try:
        text = payload.decode("utf-8")
        if (
            not payload
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\x00" in payload
            or "\r" in text
            or not text.endswith("\n")
        ):
            raise ValueError(ERROR)
        reader = csv.DictReader(io.StringIO(text, newline=""))
        if tuple(reader.fieldnames or ()) != tuple(fields):
            raise ValueError(ERROR)
        rows = list(reader)
        if any(None in row or tuple(row) != tuple(fields) for row in rows):
            raise ValueError(ERROR)
        return rows
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _run_git(repo_root: Path, args: Sequence[str]) -> bytes:
    try:
        completed = subprocess.run(
            ("git", *args),
            cwd=repo_root,
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as error:
        raise ValueError(ERROR) from error
    if completed.returncode != 0:
        raise ValueError(ERROR)
    return completed.stdout


def _git_text(repo_root: Path, args: Sequence[str]) -> str:
    try:
        return _run_git(repo_root, args).decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(ERROR) from error


def _git_blob(repo_root: Path, commit: str, path: str) -> bytes:
    if not _is_hex(commit, 40) or Path(path).is_absolute() or ".." in Path(path).parts:
        raise ValueError(ERROR)
    return _run_git(repo_root, ("show", f"{commit}:{path}"))


def _is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    completed = subprocess.run(
        ("git", "merge-base", "--is-ancestor", ancestor, descendant),
        cwd=repo_root,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode not in (0, 1):
        raise ValueError(ERROR)
    return completed.returncode == 0


def _validate_commit_identity(repo_root: Path) -> None:
    try:
        expected = (
            (BASE_COMMIT, BASE_TREE, BASE_PARENT, BASE_SUBJECT),
            (
                CONTROLLED_REVIEW_FORMAL_CANDIDATE_COMMIT,
                CONTROLLED_REVIEW_TREE,
                CONTROLLED_REVIEW_PARENT,
                CONTROLLED_REVIEW_SUBJECT,
            ),
        )
        for commit, tree, parent, subject in expected:
            if (
                _git_text(repo_root, ("cat-file", "-t", commit)).strip() != "commit"
                or _git_text(repo_root, ("show", "-s", "--format=%T", commit)).strip()
                != tree
                or _git_text(repo_root, ("show", "-s", "--format=%P", commit)).split()
                != [parent]
                or _git_text(repo_root, ("show", "-s", "--format=%s", commit)).strip()
                != subject
            ):
                raise ValueError(ERROR)
        lines = _git_text(
            repo_root,
            (
                "diff-tree",
                "--root",
                "--no-commit-id",
                "--name-status",
                "-r",
                CONTROLLED_REVIEW_FORMAL_CANDIDATE_COMMIT,
            ),
        ).splitlines()
        statuses = {
            parts[1]: parts[0]
            for parts in (line.split("\t") for line in lines)
            if len(parts) == 2
        }
        if (
            tuple(sorted(statuses)) != tuple(sorted(CONTROLLED_REVIEW_SHA256))
            or statuses != {path: "A" for path in CONTROLLED_REVIEW_SHA256}
        ):
            raise ValueError(ERROR)
        for path, digest in CONTROLLED_REVIEW_SHA256.items():
            formal = _git_blob(repo_root, CONTROLLED_REVIEW_FORMAL_CANDIDATE_COMMIT, path)
            live = repo_root / path
            metadata = live.lstat()
            if (
                _sha256(formal) != digest
                or not stat.S_ISREG(metadata.st_mode)
                or live.is_symlink()
                or stat.S_IMODE(metadata.st_mode) != 0o644
                or live.read_bytes() != formal
            ):
                raise ValueError(ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _read_exact_directory(
    path: Path,
    expected_sha: Mapping[str, str],
    *,
    formal_identity: tuple[int, int] | None,
) -> tuple[dict[str, bytes], dict[str, object]]:
    try:
        metadata = path.lstat()
        entries = tuple(sorted(path.iterdir(), key=lambda item: item.name))
        if (
            not stat.S_ISDIR(metadata.st_mode)
            or path.is_symlink()
            or stat.S_IMODE(metadata.st_mode) != 0o755
            or tuple(item.name for item in entries) != tuple(sorted(expected_sha))
            or (
                formal_identity is not None
                and (metadata.st_dev, metadata.st_ino) != formal_identity
            )
        ):
            raise ValueError(ERROR)
        unordered: dict[str, bytes] = {}
        for child in entries:
            child_metadata = child.lstat()
            payload = child.read_bytes()
            payload.decode("utf-8")
            if (
                not stat.S_ISREG(child_metadata.st_mode)
                or child.is_symlink()
                or stat.S_IMODE(child_metadata.st_mode) != 0o644
                or child_metadata.st_size != len(payload)
                or not payload
                or len(payload) >= 1024 * 1024
                or payload.startswith(b"\xef\xbb\xbf")
                or b"\x00" in payload
                or _sha256(payload) != expected_sha[child.name]
            ):
                raise ValueError(ERROR)
            unordered[child.name] = payload
        return (
            {name: unordered[name] for name in expected_sha},
            {
                "entry_type": "real_directory",
                "st_dev": metadata.st_dev,
                "st_ino": metadata.st_ino,
                "mode": "0755",
            },
        )
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _validate_worklist(
    payload: bytes, *, require_future_blank: bool = False,
) -> list[dict[str, str]]:
    rows = _strict_csv(payload, overlay.ALL_FIELDS)
    if (
        len(rows) != 1
        or len(overlay.FROZEN_FIELDS) != 16
        or len(overlay.FUTURE_FIELDS) != 25
        or {field: rows[0][field] for field in overlay.FROZEN_FIELDS}
        != overlay._frozen_initial_values()
        or (
            require_future_blank
            and any(rows[0][field] != "" for field in overlay.FUTURE_FIELDS)
        )
    ):
        raise ValueError(ERROR)
    return rows


def _validate_editable(
    repo_root: Path, state_root: Path, *, formal: bool,
) -> tuple[dict[str, bytes], dict[str, object]]:
    del repo_root
    workspace = state_root / EDITABLE_RELATIVE
    try:
        metadata = workspace.lstat()
        entries = tuple(sorted(workspace.iterdir(), key=lambda item: item.name))
        if (
            not stat.S_ISDIR(metadata.st_mode)
            or workspace.is_symlink()
            or stat.S_IMODE(metadata.st_mode) != 0o755
            or tuple(item.name for item in entries)
            != tuple(sorted(EDITABLE_INITIAL_FILE_SHA256))
            or (
                formal
                and (metadata.st_dev, metadata.st_ino) != EDITABLE_IDENTITY
            )
        ):
            raise ValueError(ERROR)
        unordered: dict[str, bytes] = {}
        for child in entries:
            child_metadata = child.lstat()
            payload = child.read_bytes()
            payload.decode("utf-8")
            if (
                not stat.S_ISREG(child_metadata.st_mode)
                or child.is_symlink()
                or stat.S_IMODE(child_metadata.st_mode) != 0o644
                or child_metadata.st_size != len(payload)
                or not payload
                or len(payload) >= 1024 * 1024
                or payload.startswith(b"\xef\xbb\xbf")
                or b"\x00" in payload
                or (
                    child.name in EDITABLE_REFERENCE_FILE_SHA256
                    and _sha256(payload)
                    != EDITABLE_REFERENCE_FILE_SHA256[child.name]
                )
            ):
                raise ValueError(ERROR)
            unordered[child.name] = payload
        payloads = {
            name: unordered[name] for name in EDITABLE_INITIAL_FILE_SHA256
        }
        _validate_worklist(payloads["transformation_evidence_worklist.csv"])
        manifest = _strict_json(payloads["editable_review_manifest.json"], dict)
        if (
            manifest.get("formal_worklist_modified") is not False
            or manifest.get("human_answers_prefilled") is not False
            or manifest.get("semantic_validation_performed") is not False
            or manifest.get("ready_for_training") is not False
        ):
            raise ValueError(ERROR)
        return payloads, {
            "entry_type": "real_directory",
            "st_dev": metadata.st_dev,
            "st_ino": metadata.st_ino,
            "mode": "0755",
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _editable_runtime_report(payloads: Mapping[str, bytes]) -> dict[str, object]:
    rows = _validate_worklist(payloads["transformation_evidence_worklist.csv"])
    return {
        "source_current_worklist_sha256": _sha256(
            payloads["transformation_evidence_worklist.csv"]
        ),
        "source_current_future_nonblank_count": sum(
            rows[0][field] != "" for field in overlay.FUTURE_FIELDS
        ),
    }


def _validate_immutable(
    state_root: Path, *, formal: bool,
) -> tuple[dict[str, bytes], dict[str, object]]:
    canonical = state_root / IMMUTABLE_RELATIVE
    try:
        canonical_metadata = canonical.lstat()
        target = os.readlink(canonical)
        if (
            not stat.S_ISLNK(canonical_metadata.st_mode)
            or target != IMMUTABLE_OBJECT_NAME
            or (
                formal
                and (canonical_metadata.st_dev, canonical_metadata.st_ino)
                != IMMUTABLE_CANONICAL_IDENTITY
            )
        ):
            raise ValueError(ERROR)
        payloads, object_identity = _read_exact_directory(
            canonical.parent / target,
            IMMUTABLE_SHA256,
            formal_identity=IMMUTABLE_OBJECT_IDENTITY if formal else None,
        )
        _validate_worklist(
            payloads["transformation_evidence_worklist.csv"],
            require_future_blank=True,
        )
        return payloads, {
            "canonical_entry_type": "symlink",
            "canonical_st_dev": canonical_metadata.st_dev,
            "canonical_st_ino": canonical_metadata.st_ino,
            "readlink": target,
            "object": object_identity,
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _validate_family_sources(
    state_root: Path, *, formal: bool,
) -> tuple[dict[str, bytes], dict[str, object], dict[str, bytes], dict[str, object]]:
    canonical = state_root / FAMILY_WORKSPACE_RELATIVE
    try:
        canonical_metadata = canonical.lstat()
        target = os.readlink(canonical)
        if (
            not stat.S_ISLNK(canonical_metadata.st_mode)
            or target != overlay.WORKSPACE_TARGET
            or (
                formal
                and (canonical_metadata.st_dev, canonical_metadata.st_ino)
                != FAMILY_WORKSPACE_CANONICAL_IDENTITY
            )
        ):
            raise ValueError(ERROR)
        workspace, object_identity = _read_exact_directory(
            canonical.parent / target,
            FAMILY_WORKSPACE_SHA256,
            formal_identity=FAMILY_WORKSPACE_OBJECT_IDENTITY if formal else None,
        )
        worklist_text = workspace["family_rule_approval_worklist.csv"].decode("utf-8")
        reader = csv.DictReader(io.StringIO(worklist_text, newline=""))
        rows = list(reader)
        if (
            len(rows) != 7
            or any(
                row.get(field) != ""
                for row in rows
                for field in overlay.HISTORICAL_HUMAN_FIELDS
            )
        ):
            raise ValueError(ERROR)
        dossier, dossier_identity = _read_exact_directory(
            state_root / FAMILY_DOSSIER_RELATIVE,
            FAMILY_DOSSIER_SHA256,
            formal_identity=FAMILY_DOSSIER_IDENTITY if formal else None,
        )
        questionnaire = dossier["human_review_questionnaire.md"].decode("utf-8")
        if any(
            questionnaire.splitlines().count(f"{field}:") != 1
            for field in overlay.HISTORICAL_HUMAN_FIELDS
        ):
            raise ValueError(ERROR)
        return (
            dossier,
            dossier_identity,
            workspace,
            {
                "canonical_entry_type": "symlink",
                "canonical_st_dev": canonical_metadata.st_dev,
                "canonical_st_ino": canonical_metadata.st_ino,
                "readlink": target,
                "object": object_identity,
            },
        )
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _source_snapshot(state_root: Path) -> tuple[tuple[object, ...], ...]:
    paths = (
        state_root / EDITABLE_RELATIVE,
        state_root / IMMUTABLE_RELATIVE,
        state_root / "manual-review" / IMMUTABLE_OBJECT_NAME,
        state_root / FAMILY_WORKSPACE_RELATIVE,
        state_root / "manual-review" / overlay.WORKSPACE_TARGET,
        state_root / FAMILY_DOSSIER_RELATIVE,
    )
    snapshot: list[tuple[object, ...]] = []
    for path in paths:
        metadata = path.lstat()
        snapshot.append(
            (
                str(path.relative_to(state_root)),
                metadata.st_dev,
                metadata.st_ino,
                metadata.st_mode,
                metadata.st_size,
                os.readlink(path) if path.is_symlink() else "",
            )
        )
        if path.is_dir() and not path.is_symlink():
            for child in sorted(path.iterdir(), key=lambda item: item.name):
                child_metadata = child.lstat()
                payload = child.read_bytes()
                snapshot.append(
                    (
                        str(child.relative_to(state_root)),
                        child_metadata.st_dev,
                        child_metadata.st_ino,
                        child_metadata.st_mode,
                        child_metadata.st_size,
                        _sha256(payload),
                    )
                )
    return tuple(snapshot)


def _summary() -> dict[str, object]:
    return {
        "candidate_formed_bond_order": "single",
        "candidate_local_graph_rule_sha256": CANDIDATE_RULE_SHA256,
        "candidate_valence_ledger_is_gap_signal_only": True,
        "candidate_valence_ledger_is_reaction_authority": False,
        "complete_atom_map_contract_available": False,
        "complete_rule_evidence_ready_for_human_decision": False,
        "conditional_post_bond_order_sum_if_internal_bonds_unchanged": 5,
        "dossier_version": DOSSIER_VERSION,
        "formal_post_reaction_authority_count": 0,
        "parent_review_unit_id": PARENT_REVIEW_UNIT_ID,
        "plural_attachment_map_contract_available": False,
        "post_formal_charge_authority": "missing",
        "post_internal_bond_delta_authority": "missing",
        "post_protonation_authority": "missing",
        "post_reaction_graph_authority": "missing",
        "pre_reaction_center_bond_order_sum": 4,
        "reaction_family_id": REACTION_FAMILY_ID,
        "review_unit_id": REVIEW_UNIT_ID,
        "sample_count": 2,
        "samples": [dict(sample) for sample in SAMPLES],
        "warhead_rule_id": WARHEAD_RULE_ID,
    }


def _questionnaire_bytes() -> bytes:
    lines = [
        "# Blank human transformation evidence questionnaire",
        "",
        f"Review unit: `{REVIEW_UNIT_ID}`",
        "",
        "All answer slots are intentionally blank. Missing is not not_claimed, and",
        "a blank slot is not an explicit reviewed empty list.",
        "",
    ]
    for index, (field, question, shape) in enumerate(QUESTION_SPECS, start=1):
        lines.extend(
            (
                f"## {index:02d}. {field}",
                "",
                f"field_name: `{field}`",
                "current_status: unreviewed",
                f"required_evidence_or_question: {question}",
                f"expected_value_shape: {shape}",
                "proposed_value:",
                "supporting_evidence_reference:",
                "reviewer_notes:",
                "",
            )
        )
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8")


def _validate_gap(payload: bytes) -> None:
    rows = _strict_csv(payload, overlay.GAP_MATRIX_COLUMNS)
    projected = [
        {
            "sample_index_row_id": row["sample_index_row_id"],
            "pdb_id": row["pdb_id"],
            "ligand_identity": row["ligand_identity"],
            "ligand_reactive_atom_id": row["ligand_reactive_atom_id"],
            "target_residue_atom": row["target_residue_atom"],
            "effective_boundary_cardinality": int(row["effective_boundary_cardinality"]),
        }
        for row in rows
    ]
    if projected != [dict(sample) for sample in SAMPLES]:
        raise ValueError(ERROR)
    for row in rows:
        if (
            row["candidate_formed_bond_order"] != "single"
            or row["pre_reaction_center_bond_order_sum"] != "4"
            or row["conditional_post_bond_order_sum_if_internal_bonds_unchanged"]
            != "5"
            or row["post_reaction_graph_authority"] != "missing"
            or row["post_internal_bond_delta_authority"] != "missing"
            or row["post_formal_charge_authority"] != "missing"
            or row["post_protonation_authority"] != "missing"
            or row["complete_atom_map_contract_available"] != "false"
            or row["plural_attachment_map_contract_available"] != "false"
            or row["complete_rule_evidence_ready_for_human_decision"] != "false"
        ):
            raise ValueError(ERROR)


def _manifest(
    generated_seven: Mapping[str, bytes],
    editable_identity: Mapping[str, object],
    immutable_identity: Mapping[str, object],
    family_dossier_identity: Mapping[str, object],
    family_workspace_identity: Mapping[str, object],
) -> dict[str, object]:
    if tuple(generated_seven) != DOSSIER_FILES[:-1]:
        raise ValueError(ERROR)
    return {
        "approval_decision_generated": False,
        "approved_smarts_generated": False,
        "atom_map_answers_generated": False,
        "authority_bundle_generated": False,
        "authority_changed": False,
        "base_commit": BASE_COMMIT,
        "controlled_review_formal_candidate_commit": (
            CONTROLLED_REVIEW_FORMAL_CANDIDATE_COMMIT
        ),
        "copied_source_file_sha256": {
            GRAPH_FILE: FAMILY_DOSSIER_SHA256[GRAPH_FILE],
            GAP_FILE: EDITABLE_INITIAL_FILE_SHA256[GAP_FILE],
            SOURCE_FILE: EDITABLE_INITIAL_FILE_SHA256[SOURCE_FILE],
            SCHEMA_FILE: EDITABLE_INITIAL_FILE_SHA256[SCHEMA_FILE],
        },
        "dossier_file_count": 8,
        "dossier_file_sha256": {
            name: _sha256(payload) for name, payload in generated_seven.items()
        },
        "dossier_version": DOSSIER_VERSION,
        "feature_semantics_reaudit_required_before_training": True,
        "formal_worklist_modified": False,
        "full_semantics_attestation_completed": False,
        "human_answers_prefilled": False,
        "identity_attestation_completed": False,
        "model_changed": False,
        "non_authoritative_review_aid": True,
        "parent_review_unit_id": PARENT_REVIEW_UNIT_ID,
        "post_state_generated": False,
        "prefilled_answer_count": 0,
        "publication_scheme": PUBLICATION_SCHEME,
        "question_count": 25,
        "questionnaire_answer_slot_count": 75,
        "reaction_family_id": REACTION_FAMILY_ID,
        "ready_for_direct_submission": False,
        "ready_for_formal_worklist_update": False,
        "ready_for_human_evidence_acquisition": True,
        "ready_for_semantic_validation": False,
        "ready_for_training": False,
        "review_ingested": False,
        "review_submission_compiled": False,
        "review_unit_id": REVIEW_UNIT_ID,
        "role_or_seed_generated": False,
        "sample_count": 2,
        "semantic_validation_performed": False,
        "source_editable_initial_file_sha256": dict(
            EDITABLE_INITIAL_FILE_SHA256
        ),
        "source_editable_initial_snapshot_semantics": (
            EDITABLE_INITIAL_SNAPSHOT_SEMANTICS
        ),
        "source_editable_initial_worklist_sha256": (
            INITIAL_BLANK_WORKLIST_SHA256
        ),
        "source_editable_live_worklist_binding": EDITABLE_LIVE_WORKLIST_BINDING,
        "source_editable_reference_file_sha256": dict(
            EDITABLE_REFERENCE_FILE_SHA256
        ),
        "source_editable_workspace_identity": dict(editable_identity),
        "source_editable_workspace_path": EDITABLE_RELATIVE,
        "source_family_dossier_identity": dict(family_dossier_identity),
        "source_family_workspace_identity": dict(family_workspace_identity),
        "source_immutable_template_identity": dict(immutable_identity),
        "tensor_materialized": False,
        "training_used": False,
        "warhead_rule_id": WARHEAD_RULE_ID,
    }


def _build_payloads(
    editable_payloads: Mapping[str, bytes],
    editable_identity: Mapping[str, object],
    immutable_identity: Mapping[str, object],
    family_dossier: Mapping[str, bytes],
    family_dossier_identity: Mapping[str, object],
    family_workspace_identity: Mapping[str, object],
) -> dict[str, bytes]:
    payloads: dict[str, bytes] = {
        README_FILE: README_TEXT.encode("utf-8"),
        GRAPH_FILE: family_dossier[GRAPH_FILE],
        SUMMARY_FILE: _canonical_json_bytes(_summary()),
        QUESTIONNAIRE_FILE: _questionnaire_bytes(),
        GAP_FILE: editable_payloads[GAP_FILE],
        SOURCE_FILE: editable_payloads[SOURCE_FILE],
        SCHEMA_FILE: editable_payloads[SCHEMA_FILE],
    }
    payloads[MANIFEST_FILE] = _canonical_json_bytes(
        _manifest(
            payloads,
            editable_identity,
            immutable_identity,
            family_dossier_identity,
            family_workspace_identity,
        )
    )
    return payloads


def _validate_payloads(payloads: object) -> None:
    try:
        if (
            type(payloads) is not dict
            or tuple(payloads) != DOSSIER_FILES
            or any(type(payload) is not bytes for payload in payloads.values())
            or any(
                not payload
                or len(payload) >= 1024 * 1024
                or payload.startswith(b"\xef\xbb\xbf")
                or b"\x00" in payload
                for payload in payloads.values()
            )
            or payloads[README_FILE] != README_TEXT.encode("utf-8")
            or _strict_json(payloads[SUMMARY_FILE], dict) != _summary()
        ):
            raise ValueError(ERROR)
        _validate_gap(payloads[GAP_FILE])
        questionnaire = payloads[QUESTIONNAIRE_FILE].decode("utf-8")
        positions = [questionnaire.index(f"field_name: `{field}`") for field in overlay.FUTURE_FIELDS]
        if (
            positions != sorted(positions)
            or len(set(positions)) != 25
            or questionnaire.count("current_status: unreviewed") != 25
            or questionnaire.count("proposed_value:\n") != 25
            or questionnaire.count("supporting_evidence_reference:\n") != 25
            or questionnaire.count("reviewer_notes:\n") != 25
        ):
            raise ValueError(ERROR)
        manifest = _strict_json(payloads[MANIFEST_FILE], dict)
        if (
            manifest.get("dossier_file_sha256")
            != {name: _sha256(payloads[name]) for name in DOSSIER_FILES[:-1]}
            or MANIFEST_FILE in manifest["dossier_file_sha256"]
            or manifest.get("prefilled_answer_count") != 0
            or manifest.get("question_count") != 25
            or manifest.get("dossier_file_count") != 8
            or manifest.get("ready_for_human_evidence_acquisition") is not True
        ):
            raise ValueError(ERROR)
        false_fields = (
            "formal_worklist_modified",
            "human_answers_prefilled",
            "semantic_validation_performed",
            "identity_attestation_completed",
            "full_semantics_attestation_completed",
            "approval_decision_generated",
            "approved_smarts_generated",
            "post_state_generated",
            "atom_map_answers_generated",
            "authority_changed",
            "review_submission_compiled",
            "review_ingested",
            "authority_bundle_generated",
            "role_or_seed_generated",
            "tensor_materialized",
            "model_changed",
            "training_used",
            "ready_for_formal_worklist_update",
            "ready_for_semantic_validation",
            "ready_for_direct_submission",
            "ready_for_training",
        )
        if any(manifest.get(field) is not False for field in false_fields):
            raise ValueError(ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _collect_live_identity(repo_root: Path, path: str) -> dict[str, object]:
    candidate = repo_root / path
    metadata = candidate.lstat()
    if (
        not stat.S_ISREG(metadata.st_mode)
        or candidate.is_symlink()
        or stat.S_IMODE(metadata.st_mode) != 0o644
    ):
        raise ValueError(ERROR)
    blob = _git_text(repo_root, ("hash-object", "--no-filters", "--", path)).strip()
    line = _git_text(repo_root, ("ls-files", "--stage", "--", path)).strip()
    if not _is_hex(blob, 40):
        raise ValueError(ERROR)
    if line:
        metadata_text, listed = line.split("\t", 1)
        mode, index_blob, stage = metadata_text.split()
        if listed != path or stage != "0" or not _is_hex(index_blob, 40):
            raise ValueError(ERROR)
        return {"tracked": True, "mode": mode, "index_blob": index_blob, "blob": blob}
    return {"tracked": False, "mode": "100644", "blob": blob}


def _collect_lifecycle(repo_root: Path) -> dict[str, object]:
    head = _git_text(repo_root, ("rev-parse", "HEAD")).strip()
    origin = _git_text(repo_root, ("rev-parse", "refs/remotes/origin/main")).strip()
    ahead_text, behind_text = _git_text(
        repo_root,
        ("rev-list", "--left-right", "--count", "HEAD...refs/remotes/origin/main"),
    ).split()
    revisions = set(_git_text(repo_root, ("rev-list", f"{BASE_COMMIT}..{head}")).splitlines())
    revisions.update(_git_text(repo_root, ("rev-list", f"{BASE_COMMIT}..{origin}")).splitlines())
    path_commits: list[dict[str, object]] = []
    for commit in sorted(revisions):
        lines = _git_text(
            repo_root,
            ("diff-tree", "--root", "--no-commit-id", "--name-status", "-r", commit),
        ).splitlines()
        statuses = {
            parts[1]: parts[0]
            for parts in (line.split("\t") for line in lines)
            if len(parts) == 2
        }
        if not set(statuses).intersection(CANDIDATE_PATHS):
            continue
        modes: dict[str, str] = {}
        blobs: dict[str, str] = {}
        for path in CANDIDATE_PATHS:
            line = _git_text(repo_root, ("ls-tree", commit, "--", path)).strip()
            if line:
                tree_metadata, listed = line.split("\t", 1)
                mode, kind, blob = tree_metadata.split()
                if listed != path or kind != "blob":
                    raise ValueError(ERROR)
                modes[path], blobs[path] = mode, blob
        path_commits.append({
            "commit": commit,
            "parents": _git_text(repo_root, ("show", "-s", "--format=%P", commit)).split(),
            "subject": _git_text(repo_root, ("show", "-s", "--format=%s", commit)).strip(),
            "changed_paths": tuple(sorted(statuses)),
            "changed_statuses": {path: statuses[path] for path in sorted(statuses)},
            "path_modes": modes,
            "path_blobs": blobs,
            "ancestor_head": _is_ancestor(repo_root, commit, head),
            "ancestor_origin": _is_ancestor(repo_root, commit, origin),
        })
    return {
        "head": head,
        "origin": origin,
        "ahead": int(ahead_text),
        "behind": int(behind_text),
        "branch": _git_text(repo_root, ("branch", "--show-current")).strip(),
        "base_ancestor_head": _is_ancestor(repo_root, BASE_COMMIT, head),
        "base_ancestor_origin": _is_ancestor(repo_root, BASE_COMMIT, origin),
        "tracked": tuple(sorted(_git_text(repo_root, ("diff", "--name-only")).splitlines())),
        "staged": tuple(sorted(_git_text(repo_root, ("diff", "--cached", "--name-only")).splitlines())),
        "untracked": tuple(sorted(_git_text(repo_root, ("ls-files", "--others", "--exclude-standard")).splitlines())),
        "porcelain": tuple(sorted(_git_text(repo_root, ("status", "--porcelain=v1", "--untracked-files=all")).splitlines())),
        "path_commits": path_commits,
        "live_paths": {path: _collect_live_identity(repo_root, path) for path in CANDIDATE_PATHS},
    }


def _derive_lifecycle(facts: object) -> dict[str, object]:
    try:
        if (
            type(facts) is not dict
            or facts["branch"] != BRANCH
            or facts["base_ancestor_head"] is not True
            or facts["base_ancestor_origin"] is not True
            or type(facts["path_commits"]) is not list
            or len(facts["path_commits"]) > 1
            or tuple(facts["live_paths"]) != CANDIDATE_PATHS
        ):
            raise ValueError(ERROR)
        commits = facts["path_commits"]
        if not commits:
            if (
                facts["head"] != BASE_COMMIT
                or facts["origin"] != BASE_COMMIT
                or (facts["ahead"], facts["behind"]) != (0, 0)
                or facts["tracked"]
                or facts["staged"]
                or facts["untracked"] != CANDIDATE_PATHS
                or facts["porcelain"]
                != tuple(sorted(f"?? {path}" for path in CANDIDATE_PATHS))
                or any(item["tracked"] is not False for item in facts["live_paths"].values())
            ):
                raise ValueError(ERROR)
            return {
                "origin_main": BASE_COMMIT,
                "ahead": 0,
                "behind": 0,
                "lifecycle_profile": "transformation_human_review_dossier_precommit_candidate",
                "formal_candidate_commit": "",
            }
        commit = commits[0]
        if (
            not _is_hex(commit["commit"], 40)
            or commit["parents"] != [BASE_COMMIT]
            or commit["subject"] != FORMAL_COMMIT_SUBJECT
            or commit["changed_paths"] != CANDIDATE_PATHS
            or commit["changed_statuses"] != {path: "A" for path in CANDIDATE_PATHS}
            or any(commit["path_modes"].get(path) != "100644" for path in CANDIDATE_PATHS)
            or any(
                facts["live_paths"][path] != {
                    "tracked": True,
                    "mode": "100644",
                    "index_blob": commit["path_blobs"].get(path),
                    "blob": commit["path_blobs"].get(path),
                }
                for path in CANDIDATE_PATHS
            )
            or commit["ancestor_head"] is not True
            or any(
                path in facts["tracked"] or path in facts["staged"] or path in facts["untracked"]
                for path in CANDIDATE_PATHS
            )
        ):
            raise ValueError(ERROR)
        if commit["ancestor_origin"] is True:
            return {
                "origin_main": facts["origin"],
                "ahead": facts["ahead"],
                "behind": facts["behind"],
                "lifecycle_profile": "transformation_human_review_dossier_published_successor",
                "formal_candidate_commit": commit["commit"],
            }
        if (
            facts["head"] != commit["commit"]
            or facts["origin"] != BASE_COMMIT
            or (facts["ahead"], facts["behind"]) != (1, 0)
            or facts["tracked"]
            or facts["staged"]
            or facts["untracked"]
            or facts["porcelain"]
        ):
            raise ValueError(ERROR)
        return {
            "origin_main": BASE_COMMIT,
            "ahead": 1,
            "behind": 0,
            "lifecycle_profile": "transformation_human_review_dossier_committed_unpushed",
            "formal_candidate_commit": commit["commit"],
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def build_covapie_current11_unit_000001_reaction_transformation_human_review_dossier_v1(
    *,
    repo_root: Path,
    state_root: Path,
) -> dict[str, bytes]:
    """Return the deterministic, non-authoritative in-memory dossier Exact8."""

    try:
        if (
            not isinstance(repo_root, Path)
            or not isinstance(state_root, Path)
            or not repo_root.is_absolute()
            or not state_root.is_absolute()
        ):
            raise ValueError(ERROR)
        repository = repo_root.resolve(strict=True)
        state = state_root.resolve(strict=True)
        if (
            repository != repo_root
            or state != state_root
            or state_root.is_symlink()
            or _git_text(repository, ("rev-parse", "--show-toplevel")).strip()
            != str(repository)
        ):
            raise ValueError(ERROR)
        formal = state == repository.parent / "covapie-state"
        before = _source_snapshot(state)
        _validate_commit_identity(repository)
        editable_payloads, editable_identity = _validate_editable(
            repository, state, formal=formal
        )
        immutable_payloads, immutable_identity = _validate_immutable(
            state, formal=formal
        )
        family_dossier, family_dossier_identity, _workspace, workspace_identity = (
            _validate_family_sources(state, formal=formal)
        )
        if any(
            immutable_payloads[name] != editable_payloads[name]
            for name in (GAP_FILE, SOURCE_FILE, SCHEMA_FILE)
        ):
            raise ValueError(ERROR)
        _validate_gap(editable_payloads[GAP_FILE])
        _derive_lifecycle(_collect_lifecycle(repository))
        payloads = _build_payloads(
            editable_payloads,
            editable_identity,
            immutable_identity,
            family_dossier,
            family_dossier_identity,
            workspace_identity,
        )
        second = _build_payloads(
            editable_payloads,
            editable_identity,
            immutable_identity,
            family_dossier,
            family_dossier_identity,
            workspace_identity,
        )
        if payloads != second or _source_snapshot(state) != before:
            raise ValueError(ERROR)
        _validate_payloads(payloads)
        return payloads
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error
