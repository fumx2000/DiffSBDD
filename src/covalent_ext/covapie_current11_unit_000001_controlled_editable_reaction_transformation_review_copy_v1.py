"""Build the controlled editable Current11 UNIT_000001 review copy.

The sole public builder is metadata-only and read-only.  It validates the
formally published immutable acquisition template and returns the initial
Exact6 editable-review payload in memory.  It does not publish a workspace or
fill, validate, approve, submit, or ingest transformation evidence.
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
    covapie_current11_unit_000001_reaction_transformation_evidence_acquisition_template_v1
    as source_template,
)


__all__ = (
    "build_covapie_current11_unit_000001_controlled_editable_reaction_"
    "transformation_review_copy_v1",
)


REVIEW_COPY_VERSION = (
    "covapie_current11_unit_000001_controlled_editable_reaction_"
    "transformation_review_copy_v1"
)
ERROR = f"{REVIEW_COPY_VERSION}_validation_failed"
BASE_COMMIT = "dfc5dd59f4fff16b2bd85e321a277cdfe8aa9713"
BASE_TREE = "f54d9c34a9a38c3e8a2650abf6ec184b61409508"
BASE_PARENT = "767668bff04bb57021d16be0d2c0f002401993fc"
BASE_SUBJECT = (
    "add CovaPIE Current11 reaction transformation evidence acquisition "
    "template materializer v1"
)
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE Current11 controlled editable reaction transformation "
    "review copy v1"
)
BRANCH = "main"

SOURCE_TEMPLATE_VERSION = (
    "covapie_current11_unit_000001_reaction_transformation_evidence_"
    "acquisition_template_v1"
)
SOURCE_WORKSPACE_NAME = (
    "current11-reaction-transformation-evidence-acquisition-template-v1"
)
SOURCE_OBJECT_NAME = (
    ".current11-reaction-transformation-evidence-acquisition-template-v1."
    "object-1p9gz5wu"
)
SOURCE_CANONICAL_IDENTITY = (49, 177964065736)
SOURCE_OBJECT_IDENTITY = (49, 178292049039)
SOURCE_MANIFEST_SHA256 = (
    "61878d2ee9da387ae28384f5a8bfb7adae30ee141304aefb6bd77fdac91a382e"
)

README_FILE = "README.md"
WORKLIST_FILE = "transformation_evidence_worklist.csv"
SCHEMA_FILE = "structured_json_schema_templates.json"
GAP_FILE = "sample_transformation_gap_evidence.csv"
SOURCE_FILE = "source_authority_inventory_snapshot.csv"
SOURCE_MANIFEST_FILE = "template_manifest.json"
MANIFEST_FILE = "editable_review_manifest.json"
SOURCE_FILES = (
    README_FILE,
    WORKLIST_FILE,
    SCHEMA_FILE,
    GAP_FILE,
    SOURCE_FILE,
    SOURCE_MANIFEST_FILE,
)
REVIEW_FILES = (
    README_FILE,
    WORKLIST_FILE,
    SCHEMA_FILE,
    GAP_FILE,
    SOURCE_FILE,
    MANIFEST_FILE,
)
MUTABLE_FILES = (WORKLIST_FILE,)
IMMUTABLE_REFERENCE_FILES = (
    README_FILE,
    SCHEMA_FILE,
    GAP_FILE,
    SOURCE_FILE,
    MANIFEST_FILE,
)
SOURCE_FILE_SHA256 = {
    README_FILE: "cc2988689c3d603b4a72a1bace848fd4c9231e0f11856b925b98b3069210b2e7",
    WORKLIST_FILE: "c7063e8070de3ecd1fdf4dfc19ffd91ef09dbeac48d80fbc6f01c9369d647423",
    SCHEMA_FILE: "ddde07b4b28ee45163d0cb09a9e08ea8712c255a20b1b7fd72dbb7da110f07c6",
    GAP_FILE: "599c75f0f97896c0eea73dbde5041a446f23cb5d30e7da36c186a908561e1134",
    SOURCE_FILE: "fb638a9573cfba0561879b8f8b030c453bd5b3fe693c983eb6fa65f1b7cc4e28",
    SOURCE_MANIFEST_FILE: SOURCE_MANIFEST_SHA256,
}
SOURCE_FILE_BYTES = {
    README_FILE: 1124,
    WORKLIST_FILE: 2473,
    SCHEMA_FILE: 2847,
    GAP_FILE: 2415,
    SOURCE_FILE: 13357,
    SOURCE_MANIFEST_FILE: 2912,
}
SOURCE_FILE_LINES = {
    README_FILE: 21,
    WORKLIST_FILE: 2,
    SCHEMA_FILE: 110,
    GAP_FILE: 3,
    SOURCE_FILE: 36,
    SOURCE_MANIFEST_FILE: 53,
}

WORKSPACE_NAME = "current11-reaction-transformation-review-v1"
PUBLICATION_SCHEME = "exclusive_real_directory_editable_workspace_v1"

MODULE_PATH = (
    "src/covalent_ext/covapie_current11_unit_000001_controlled_editable_"
    "reaction_transformation_review_copy_v1.py"
)
SCRIPT_PATH = (
    "scripts/materialize_covapie_current11_unit_000001_controlled_editable_"
    "reaction_transformation_review_copy_v1.py"
)
TEST_PATH = (
    "tests/test_covapie_current11_unit_000001_controlled_editable_reaction_"
    "transformation_review_copy_v1.py"
)
GUIDE_PATH = (
    "docs/covapie_current11_unit_000001_controlled_editable_reaction_"
    "transformation_review_copy_v1_guide.md"
)
CANDIDATE_PATHS = tuple(sorted((MODULE_PATH, SCRIPT_PATH, TEST_PATH, GUIDE_PATH)))

SOURCE_CANDIDATE_PATHS = tuple(sorted((
    source_template.MODULE_PATH,
    source_template.SCRIPT_PATH,
    source_template.TEST_PATH,
    source_template.GUIDE_PATH,
)))
SOURCE_MATERIALIZER_SHA256 = {
    source_template.MODULE_PATH:
        "345c40bc279f75c1fc069e546c1f0d58a80b00db67991b8a3563182347933d42",
    source_template.SCRIPT_PATH:
        "ab35243ec15dea9023d38772ffd4d657d4ec4f2e172c827a92660ef9deb87875",
    source_template.TEST_PATH:
        "dc3e8dc086c059cce9e9258cc75780a2ab8553fc51ba8f197509427915237f76",
    source_template.GUIDE_PATH:
        "b8422e4f2560594d79efdd2ce4b624c4a4e628eea71701afe680050feb780144",
}

README_TEXT = """# CovaPIE Current11 controlled editable transformation review copy v1

This is a controlled editable review copy derived from the formally published
immutable acquisition template for
`CURRENT11_REACTION_TRANSFORMATION_REVIEW_UNIT_000001`.

Only `transformation_evidence_worklist.csv` is editable. Its Exact16 frozen
fields must never change; its Exact25 future fields may be filled only by a
later human or curation workflow. An empty string means unreviewed. An
explicit canonical empty list means reviewed and confirmed to contain no
records. These
states must not be confused. `README.md`, the three reference data files, and
`editable_review_manifest.json` are immutable reference files.

This copy is not a submission or an authority.
It does not prove a reaction mechanism.
The candidate valence ledger remains a gap signal only. Completed
entries still require independent semantic validation and identity/full-
semantics attestation. Before formal training, the feature-semantics audit is
still required. `ready_for_training=false`.
"""


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
        if not text.endswith("\n") or text.endswith("\n\n"):
            raise ValueError(ERROR)
        value = json.loads(text)
        if type(value) is not expected_type or _canonical_json_bytes(value) != payload:
            raise ValueError(ERROR)
        return value
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _strict_csv(payload: bytes, fields: Sequence[str]) -> list[dict[str, str]]:
    try:
        if (
            type(payload) is not bytes
            or not payload
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\x00" in payload
        ):
            raise ValueError(ERROR)
        text = payload.decode("utf-8")
        if "\r" in text or not text.endswith("\n"):
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
    try:
        completed = subprocess.run(
            ("git", "merge-base", "--is-ancestor", ancestor, descendant),
            cwd=repo_root,
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as error:
        raise ValueError(ERROR) from error
    if completed.returncode not in (0, 1):
        raise ValueError(ERROR)
    return completed.returncode == 0


def _validate_source_materializer_commit(repo_root: Path) -> None:
    try:
        if (
            _git_text(repo_root, ("cat-file", "-t", BASE_COMMIT)).strip()
            != "commit"
            or _git_text(repo_root, ("show", "-s", "--format=%T", BASE_COMMIT)).strip()
            != BASE_TREE
            or _git_text(repo_root, ("show", "-s", "--format=%P", BASE_COMMIT)).split()
            != [BASE_PARENT]
            or _git_text(repo_root, ("show", "-s", "--format=%s", BASE_COMMIT)).strip()
            != BASE_SUBJECT
        ):
            raise ValueError(ERROR)
        lines = _git_text(
            repo_root,
            ("diff-tree", "--root", "--no-commit-id", "--name-status", "-r", BASE_COMMIT),
        ).splitlines()
        statuses = {
            parts[1]: parts[0]
            for parts in (line.split("\t") for line in lines)
            if len(parts) == 2
        }
        if (
            tuple(sorted(statuses)) != SOURCE_CANDIDATE_PATHS
            or statuses != {path: "A" for path in SOURCE_CANDIDATE_PATHS}
        ):
            raise ValueError(ERROR)
        for path in SOURCE_CANDIDATE_PATHS:
            formal = _git_blob(repo_root, BASE_COMMIT, path)
            candidate = repo_root / path
            metadata = candidate.lstat()
            line = _git_text(repo_root, ("ls-tree", BASE_COMMIT, "--", path)).strip()
            tree_metadata, listed = line.split("\t", 1)
            mode, kind, blob = tree_metadata.split()
            if (
                listed != path
                or mode != "100644"
                or kind != "blob"
                or not _is_hex(blob, 40)
                or _sha256(formal) != SOURCE_MATERIALIZER_SHA256[path]
                or not stat.S_ISREG(metadata.st_mode)
                or candidate.is_symlink()
                or stat.S_IMODE(metadata.st_mode) != 0o644
                or candidate.read_bytes() != formal
            ):
                raise ValueError(ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _validate_source_semantics(payloads: Mapping[str, bytes]) -> None:
    try:
        if tuple(payloads) != SOURCE_FILES:
            raise ValueError(ERROR)
        source_template._validate_payloads(dict(payloads))
        rows = _strict_csv(payloads[WORKLIST_FILE], overlay.ALL_FIELDS)
        schemas = _strict_json(payloads[SCHEMA_FILE], dict)
        gap_rows = _strict_csv(payloads[GAP_FILE], overlay.GAP_MATRIX_COLUMNS)
        source_rows = _strict_csv(
            payloads[SOURCE_FILE], overlay.SOURCE_INVENTORY_COLUMNS
        )
        manifest = _strict_json(payloads[SOURCE_MANIFEST_FILE], dict)
        required_false = (
            "human_answers_prefilled",
            "post_state_generated",
            "atom_map_answers_generated",
            "approved_smarts_generated",
            "approval_decision_generated",
            "formal_worklist_modified",
            "authority_changed",
            "review_submission_compiled",
            "review_ingested",
            "authority_bundle_generated",
            "role_or_seed_generated",
            "tensor_materialized",
            "model_changed",
            "training_used",
            "ready_for_direct_submission",
            "ready_for_training",
        )
        if (
            len(rows) != 1
            or len(overlay.ALL_FIELDS) != 41
            or len(overlay.FROZEN_FIELDS) != 16
            or len(overlay.FUTURE_FIELDS) != 25
            or {field: rows[0][field] for field in overlay.FROZEN_FIELDS}
            != overlay._frozen_initial_values()
            or any(rows[0][field] != "" for field in overlay.FUTURE_FIELDS)
            or len(schemas) != 8
            or len(gap_rows) != 2
            or len(source_rows) != 35
            or sum(
                row["authoritative_for_transformation"] == "true"
                for row in source_rows
            ) != 0
            or manifest.get("template_version") != SOURCE_TEMPLATE_VERSION
            or manifest.get("formal_post_reaction_authority_count") != 0
            or manifest.get("ready_for_controlled_editable_copy") is not True
            or manifest.get("feature_semantics_reaudit_required_before_training")
            is not True
            or any(manifest.get(field) is not False for field in required_false)
        ):
            raise ValueError(ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _validate_source_template_tree(
    *, repo_root: Path, state_root: Path,
) -> dict[str, bytes]:
    try:
        canonical = state_root / "manual-review" / SOURCE_WORKSPACE_NAME
        canonical_metadata = canonical.lstat()
        relative_target = os.readlink(canonical)
        if (
            not stat.S_ISLNK(canonical_metadata.st_mode)
            or type(relative_target) is not str
            or relative_target != SOURCE_OBJECT_NAME
            or Path(relative_target).is_absolute()
            or "/" in relative_target
            or ".." in relative_target
        ):
            raise ValueError(ERROR)
        object_directory = canonical.parent / relative_target
        object_metadata = object_directory.lstat()
        entries = tuple(sorted(object_directory.iterdir(), key=lambda item: item.name))
        formal_state_root = repo_root.parent / "covapie-state"
        require_formal_identity = state_root == formal_state_root
        if (
            not stat.S_ISDIR(object_metadata.st_mode)
            or object_directory.is_symlink()
            or stat.S_IMODE(object_metadata.st_mode) != 0o755
            or tuple(item.name for item in entries) != tuple(sorted(SOURCE_FILES))
            or (
                require_formal_identity
                and (canonical_metadata.st_dev, canonical_metadata.st_ino)
                != SOURCE_CANONICAL_IDENTITY
            )
            or (
                require_formal_identity
                and (object_metadata.st_dev, object_metadata.st_ino)
                != SOURCE_OBJECT_IDENTITY
            )
        ):
            raise ValueError(ERROR)
        unordered: dict[str, bytes] = {}
        for path in entries:
            metadata = path.lstat()
            payload = path.read_bytes()
            payload.decode("utf-8")
            if (
                not stat.S_ISREG(metadata.st_mode)
                or path.is_symlink()
                or stat.S_IMODE(metadata.st_mode) != 0o644
                or metadata.st_size != SOURCE_FILE_BYTES[path.name]
                or payload.count(b"\n") != SOURCE_FILE_LINES[path.name]
                or _sha256(payload) != SOURCE_FILE_SHA256[path.name]
                or payload.startswith(b"\xef\xbb\xbf")
                or b"\x00" in payload
            ):
                raise ValueError(ERROR)
            unordered[path.name] = payload
        payloads = {name: unordered[name] for name in SOURCE_FILES}
        _validate_source_semantics(payloads)
        return payloads
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _manifest(source_payloads: Mapping[str, bytes]) -> dict[str, object]:
    if tuple(source_payloads) != SOURCE_FILES:
        raise ValueError(ERROR)
    source_manifest = _strict_json(source_payloads[SOURCE_MANIFEST_FILE], dict)
    return {
        "approval_decision_generated": False,
        "approved_smarts_generated": False,
        "atom_map_answers_generated": False,
        "authority_bundle_generated": False,
        "authority_changed": False,
        "base_commit": BASE_COMMIT,
        "candidate_valence_ledger_is_gap_signal_only": True,
        "editable_field_count": 25,
        "editable_fields": list(overlay.FUTURE_FIELDS),
        "feature_semantics_reaudit_required_before_training": True,
        "field_count": 41,
        "formal_worklist_modified": False,
        "frozen_field_count": 16,
        "frozen_fields": list(overlay.FROZEN_FIELDS),
        "full_semantics_attestation_completed": False,
        "human_answers_prefilled": False,
        "identity_attestation_completed": False,
        "immutable_reference_files": list(IMMUTABLE_REFERENCE_FILES),
        "initial_future_nonblank_count": 0,
        "initial_worklist_sha256": SOURCE_FILE_SHA256[WORKLIST_FILE],
        "model_changed": False,
        "mutable_files": list(MUTABLE_FILES),
        "parent_review_unit_id": source_manifest["parent_review_unit_id"],
        "post_state_generated": False,
        "publication_scheme": PUBLICATION_SCHEME,
        "reaction_family_id": source_manifest["reaction_family_id"],
        "ready_for_direct_submission": False,
        "ready_for_human_evidence_entry": True,
        "ready_for_semantic_validation": False,
        "ready_for_training": False,
        "review_copy_version": REVIEW_COPY_VERSION,
        "review_ingested": False,
        "review_submission_compiled": False,
        "role_or_seed_generated": False,
        "row_count": 1,
        "semantic_validation_performed": False,
        "source_template_file_sha256": dict(SOURCE_FILE_SHA256),
        "source_template_manifest_sha256": SOURCE_MANIFEST_SHA256,
        "source_template_version": SOURCE_TEMPLATE_VERSION,
        "tensor_materialized": False,
        "training_used": False,
        "transformation_review_unit_id": source_manifest[
            "transformation_review_unit_id"
        ],
        "warhead_rule_id": source_manifest["warhead_rule_id"],
    }


def _build_payloads(source_payloads: Mapping[str, bytes]) -> dict[str, bytes]:
    _validate_source_semantics(source_payloads)
    payloads = {
        README_FILE: README_TEXT.encode("utf-8"),
        WORKLIST_FILE: source_payloads[WORKLIST_FILE],
        SCHEMA_FILE: source_payloads[SCHEMA_FILE],
        GAP_FILE: source_payloads[GAP_FILE],
        SOURCE_FILE: source_payloads[SOURCE_FILE],
        MANIFEST_FILE: _canonical_json_bytes(_manifest(source_payloads)),
    }
    if tuple(payloads) != REVIEW_FILES:
        raise ValueError(ERROR)
    return payloads


def _validate_initial_payloads(
    payloads: Mapping[str, bytes], source_payloads: Mapping[str, bytes],
) -> None:
    try:
        if (
            type(payloads) is not dict
            or tuple(payloads) != REVIEW_FILES
            or any(type(value) is not bytes for value in payloads.values())
            or any(
                not value
                or len(value) >= 1024 * 1024
                or value.startswith(b"\xef\xbb\xbf")
                or b"\x00" in value
                for value in payloads.values()
            )
            or payloads[README_FILE] != README_TEXT.encode("utf-8")
            or payloads[WORKLIST_FILE] != source_payloads[WORKLIST_FILE]
            or any(
                payloads[name] != source_payloads[name]
                for name in (SCHEMA_FILE, GAP_FILE, SOURCE_FILE)
            )
            or _strict_json(payloads[MANIFEST_FILE], dict)
            != _manifest(source_payloads)
        ):
            raise ValueError(ERROR)
        rows = _strict_csv(payloads[WORKLIST_FILE], overlay.ALL_FIELDS)
        if (
            len(rows) != 1
            or {field: rows[0][field] for field in overlay.FROZEN_FIELDS}
            != overlay._frozen_initial_values()
            or any(rows[0][field] != "" for field in overlay.FUTURE_FIELDS)
        ):
            raise ValueError(ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _collect_live_identity(repo_root: Path, path: str) -> dict[str, object]:
    candidate = repo_root / path
    try:
        metadata = candidate.lstat()
    except OSError as error:
        raise ValueError(ERROR) from error
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
        return {
            "tracked": True,
            "mode": mode,
            "index_blob": index_blob,
            "blob": blob,
        }
    return {"tracked": False, "mode": "100644", "blob": blob}


def _collect_lifecycle(repo_root: Path) -> dict[str, object]:
    head = _git_text(repo_root, ("rev-parse", "HEAD")).strip()
    origin = _git_text(repo_root, ("rev-parse", "refs/remotes/origin/main")).strip()
    ahead_text, behind_text = _git_text(
        repo_root,
        ("rev-list", "--left-right", "--count", "HEAD...refs/remotes/origin/main"),
    ).split()
    revisions = set(_git_text(repo_root, ("rev-list", f"{BASE_COMMIT}..{head}")).splitlines())
    revisions.update(
        _git_text(repo_root, ("rev-list", f"{BASE_COMMIT}..{origin}")).splitlines()
    )
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
        "untracked": tuple(sorted(
            _git_text(repo_root, ("ls-files", "--others", "--exclude-standard")).splitlines()
        )),
        "porcelain": tuple(sorted(
            _git_text(repo_root, ("status", "--porcelain=v1", "--untracked-files=all")).splitlines()
        )),
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
            or type(facts["porcelain"]) is not tuple
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
                or any(
                    item["tracked"] is not False or item["mode"] != "100644"
                    for item in facts["live_paths"].values()
                )
            ):
                raise ValueError(ERROR)
            return {
                "origin_main": BASE_COMMIT,
                "ahead": 0,
                "behind": 0,
                "lifecycle_profile": "controlled_transformation_review_copy_precommit_candidate",
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
                "lifecycle_profile": "controlled_transformation_review_copy_published_successor",
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
            "lifecycle_profile": "controlled_transformation_review_copy_committed_unpushed",
            "formal_candidate_commit": commit["commit"],
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def build_covapie_current11_unit_000001_controlled_editable_reaction_transformation_review_copy_v1(
    *,
    repo_root: Path,
    state_root: Path,
) -> dict[str, bytes]:
    """Return the deterministic initial Exact6 editable-review payload."""

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
        _validate_source_materializer_commit(repository)
        source_payloads = _validate_source_template_tree(
            repo_root=repository, state_root=state
        )
        _derive_lifecycle(_collect_lifecycle(repository))
        payloads = _build_payloads(source_payloads)
        second = _build_payloads(source_payloads)
        if payloads != second:
            raise ValueError(ERROR)
        _validate_initial_payloads(payloads, source_payloads)
        return payloads
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error
