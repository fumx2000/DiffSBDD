"""Build the unfilled Current11 UNIT_000001 transformation evidence template.

The builder is metadata-only and read-only.  It validates the published
reaction-transformation overlay, its frozen review workspace and dossier, and
the repository lifecycle before returning an in-memory Exact6 payload.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import stat
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, Sequence

from covalent_ext import (
    covapie_current11_reaction_transformation_evidence_overlay_contract_v1
    as overlay,
)


__all__ = (
    "build_covapie_current11_unit_000001_reaction_transformation_evidence_acquisition_template_v1",
)


TEMPLATE_VERSION = (
    "covapie_current11_unit_000001_reaction_transformation_evidence_"
    "acquisition_template_v1"
)
ERROR = f"{TEMPLATE_VERSION}_validation_failed"
BASE_COMMIT = "767668bff04bb57021d16be0d2c0f002401993fc"
OVERLAY_FORMAL_COMMIT = BASE_COMMIT
OVERLAY_TREE = "0c5fcf20a1b38b8ca7ae0be3d37d4dd27fc633ea"
OVERLAY_PARENT = "35a87a46b08b1362c990c10e95b7ab03d1865af5"
OVERLAY_SUBJECT = (
    "add CovaPIE Current11 reaction transformation evidence overlay contract v1"
)
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE Current11 reaction transformation evidence acquisition "
    "template materializer v1"
)
BRANCH = "main"
WORKSPACE_NAME = (
    "current11-reaction-transformation-evidence-acquisition-template-v1"
)
PUBLICATION_SCHEME = "relative_symlink_to_immutable_sibling_v1"
OBJECT_DIRECTORY_PREFIX = f".{WORKSPACE_NAME}.object-"

README_FILE = "README.md"
WORKLIST_FILE = "transformation_evidence_worklist.csv"
SCHEMA_FILE = "structured_json_schema_templates.json"
GAP_FILE = "sample_transformation_gap_evidence.csv"
SOURCE_FILE = "source_authority_inventory_snapshot.csv"
MANIFEST_FILE = "template_manifest.json"
TEMPLATE_FILES = (
    README_FILE,
    WORKLIST_FILE,
    SCHEMA_FILE,
    GAP_FILE,
    SOURCE_FILE,
    MANIFEST_FILE,
)

MODULE_PATH = (
    "src/covalent_ext/covapie_current11_unit_000001_reaction_"
    "transformation_evidence_acquisition_template_v1.py"
)
SCRIPT_PATH = (
    "scripts/materialize_covapie_current11_unit_000001_reaction_"
    "transformation_evidence_acquisition_template_v1.py"
)
TEST_PATH = (
    "tests/test_covapie_current11_unit_000001_reaction_transformation_"
    "evidence_acquisition_template_v1.py"
)
GUIDE_PATH = (
    "docs/covapie_current11_unit_000001_reaction_transformation_evidence_"
    "acquisition_template_v1_guide.md"
)
CANDIDATE_PATHS = tuple(sorted((MODULE_PATH, SCRIPT_PATH, TEST_PATH, GUIDE_PATH)))

OVERLAY_CANDIDATE_PATHS = tuple(sorted((
    overlay.MODULE_PATH,
    overlay.CHECKER_PATH,
    overlay.TEST_PATH,
    overlay.GUIDE_PATH,
    *overlay.ARTIFACT_PATHS,
)))
OVERLAY_ARTIFACT_SHA256 = {
    overlay.SOURCE_INVENTORY_PATH:
        "fb638a9573cfba0561879b8f8b030c453bd5b3fe693c983eb6fa65f1b7cc4e28",
    overlay.FIELD_CONTRACT_PATH:
        "fea5081dc98500bbce7eb891f28b110046e1bc4da084f5ae1abefc261656be1b",
    overlay.GAP_MATRIX_PATH:
        "599c75f0f97896c0eea73dbde5041a446f23cb5d30e7da36c186a908561e1134",
    overlay.FAILURE_MATRIX_PATH:
        "dc9291ed12f53750642bbb7e91853ed1d80400846b7de5054c92090be0168171",
    overlay.MANIFEST_PATH:
        "a12c91efd4d3a2b50ce477375cf887a5d64e22e185ab03c640ad5f75664ecd28",
}
OVERLAY_MODULE_SHA256 = (
    "4f277f4cf68f64c0b61647e1388e285b89bf3668892727258912ebdb036fe1a3"
)

README_TEXT = """# CovaPIE Current11 transformation evidence acquisition template v1

This directory is the immutable initial acquisition template for
`CURRENT11_REACTION_TRANSFORMATION_REVIEW_UNIT_000001`.
It is not an editable review submission and contains no transformation answers. All 25 future
human/authority fields are empty strings.

An empty string means unreviewed. An explicit canonical empty list, once
entered through the future controlled review process, means that a reviewer
has reviewed the relevant question and confirmed that there are no records.
Those two states must never be confused.

The candidate valence ledger is a gap signal only. It does not prove a
reaction mechanism or any post-reaction state. This template does not generate
an atom-map answer, an approved SMARTS, or an approval decision, and it does
not constitute family, rule, or transformation authority. It must not be used
directly as a submission.

A later controlled process may create an editable copy from this immutable
template. Before any formal training, the feature-semantics successor audit is
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


def _csv_bytes(
    fields: Sequence[str], rows: Sequence[Mapping[str, object]],
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=list(fields),
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    for row in rows:
        if tuple(row) != tuple(fields):
            raise ValueError(ERROR)
        writer.writerow(row)
    return stream.getvalue().encode("utf-8")


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


def _run_git(repo_root: Path, args: Sequence[str], *, check: bool = True) -> bytes:
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
    if check and completed.returncode != 0:
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


def _validate_overlay_commit_identity(repo_root: Path) -> dict[str, bytes]:
    try:
        if (
            _git_text(repo_root, ("cat-file", "-t", OVERLAY_FORMAL_COMMIT)).strip()
            != "commit"
            or _git_text(
                repo_root, ("show", "-s", "--format=%T", OVERLAY_FORMAL_COMMIT)
            ).strip() != OVERLAY_TREE
            or _git_text(
                repo_root, ("show", "-s", "--format=%P", OVERLAY_FORMAL_COMMIT)
            ).split() != [OVERLAY_PARENT]
            or _git_text(
                repo_root, ("show", "-s", "--format=%s", OVERLAY_FORMAL_COMMIT)
            ).strip() != OVERLAY_SUBJECT
        ):
            raise ValueError(ERROR)
        status_lines = _git_text(
            repo_root,
            (
                "diff-tree", "--root", "--no-commit-id", "--name-status", "-r",
                OVERLAY_FORMAL_COMMIT,
            ),
        ).splitlines()
        statuses = {
            parts[1]: parts[0]
            for parts in (line.split("\t") for line in status_lines)
            if len(parts) == 2
        }
        if (
            tuple(sorted(statuses)) != OVERLAY_CANDIDATE_PATHS
            or statuses != {path: "A" for path in OVERLAY_CANDIDATE_PATHS}
        ):
            raise ValueError(ERROR)
        for path in OVERLAY_CANDIDATE_PATHS:
            line = _git_text(
                repo_root, ("ls-tree", OVERLAY_FORMAL_COMMIT, "--", path)
            ).strip()
            metadata, listed = line.split("\t", 1)
            mode, kind, blob = metadata.split()
            if (
                listed != path
                or mode != "100644"
                or kind != "blob"
                or not _is_hex(blob, 40)
            ):
                raise ValueError(ERROR)
        artifacts = {
            path: _git_blob(repo_root, OVERLAY_FORMAL_COMMIT, path)
            for path in overlay.ARTIFACT_PATHS
        }
        if (
            tuple(artifacts) != tuple(OVERLAY_ARTIFACT_SHA256)
            or any(
                _sha256(artifacts[path]) != OVERLAY_ARTIFACT_SHA256[path]
                for path in artifacts
            )
        ):
            raise ValueError(ERROR)
        formal_module = _git_blob(
            repo_root, OVERLAY_FORMAL_COMMIT, overlay.MODULE_PATH
        )
        live_module = repo_root / overlay.MODULE_PATH
        live_metadata = live_module.lstat()
        if (
            _sha256(formal_module) != OVERLAY_MODULE_SHA256
            or not stat.S_ISREG(live_metadata.st_mode)
            or live_module.is_symlink()
            or stat.S_IMODE(live_metadata.st_mode) != 0o644
            or live_module.read_bytes() != formal_module
        ):
            raise ValueError(ERROR)
        return artifacts
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _validate_overlay_response(response: object) -> None:
    try:
        expected = {
            "lifecycle_profile": "transformation_overlay_published_successor",
            "formal_candidate_commit": OVERLAY_FORMAL_COMMIT,
            "unit_count": 1,
            "sample_count": 2,
            "field_count": 41,
            "gap_count": 2,
            "failure_count": 28,
            "schema_gap_detected": True,
            "formal_post_reaction_authority_count": 0,
            "family_identity_evidence_ready": True,
            "complete_rule_evidence_ready": False,
            "candidate_valence_ledger_is_gap_signal_only": True,
            "candidate_valence_ledger_is_reaction_authority": False,
            "feature_semantics_reaudit_required_before_training": True,
            "ready_for_training": False,
        }
        if type(response) is not dict or any(
            response.get(field) != value for field, value in expected.items()
        ):
            raise ValueError(ERROR)
        expected_sha = {
            Path(path).name: digest
            for path, digest in OVERLAY_ARTIFACT_SHA256.items()
        }
        if response.get("artifact_sha256") != expected_sha:
            raise ValueError(ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _validate_overlay_artifacts(artifacts: Mapping[str, bytes]) -> None:
    try:
        if type(artifacts) is not dict or tuple(artifacts) != tuple(overlay.ARTIFACT_PATHS):
            raise ValueError(ERROR)
        field_rows = _strict_csv(
            artifacts[overlay.FIELD_CONTRACT_PATH], overlay.FIELD_CONTRACT_COLUMNS
        )
        gap_rows = _strict_csv(
            artifacts[overlay.GAP_MATRIX_PATH], overlay.GAP_MATRIX_COLUMNS
        )
        source_rows = _strict_csv(
            artifacts[overlay.SOURCE_INVENTORY_PATH],
            overlay.SOURCE_INVENTORY_COLUMNS,
        )
        failure_rows = _strict_csv(
            artifacts[overlay.FAILURE_MATRIX_PATH], overlay.FAILURE_MATRIX_COLUMNS
        )
        manifest = _strict_json(artifacts[overlay.MANIFEST_PATH], dict)
        if (
            field_rows != list(overlay._field_contract_rows())
            or gap_rows != list(overlay._gap_rows())
            or source_rows != list(overlay._source_inventory_rows())
            or failure_rows != list(overlay._failure_rows())
            or len(field_rows) != 41
            or len(gap_rows) != 2
            or len(source_rows) != 35
            or len(failure_rows) != 28
            or manifest["formal_post_reaction_authority_count"] != 0
            or manifest["complete_rule_evidence_ready_for_human_decision"] is not False
            or manifest["feature_semantics_reaudit_required_before_training"] is not True
            or manifest["ready_for_training"] is not False
        ):
            raise ValueError(ERROR)
        overlay._validate_structured_json_schema_contracts_v1()
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _source_overlay_sha_witness() -> dict[str, str]:
    return {
        Path(path).name: OVERLAY_ARTIFACT_SHA256[path]
        for path in overlay.ARTIFACT_PATHS
    }


def _build_worklist(artifacts: Mapping[str, bytes]) -> bytes:
    rows = _strict_csv(
        artifacts[overlay.FIELD_CONTRACT_PATH], overlay.FIELD_CONTRACT_COLUMNS
    )
    if [row["field_order_0based"] for row in rows] != [
        str(index) for index in range(41)
    ]:
        raise ValueError(ERROR)
    fields = tuple(row["field_name"] for row in rows)
    if fields != overlay.ALL_FIELDS:
        raise ValueError(ERROR)
    record: dict[str, str] = {}
    for index, row in enumerate(rows):
        future = index >= len(overlay.FROZEN_FIELDS)
        if (
            row["frozen"] != ("false" if future else "true")
            or row["human_or_authority_fillable"]
            != ("true" if future else "false")
            or row["initial_value"] != ("" if future else row["initial_value"])
        ):
            raise ValueError(ERROR)
        record[row["field_name"]] = "" if future else row["initial_value"]
    if (
        {field: record[field] for field in overlay.FROZEN_FIELDS}
        != overlay._frozen_initial_values()
        or any(record[field] != "" for field in overlay.FUTURE_FIELDS)
    ):
        raise ValueError(ERROR)
    return _csv_bytes(fields, (record,))


def _manifest(other_five: Mapping[str, bytes]) -> dict[str, object]:
    if tuple(other_five) != TEMPLATE_FILES[:-1]:
        raise ValueError(ERROR)
    return {
        "approval_decision_generated": False,
        "approved_smarts_generated": False,
        "atom_map_answers_generated": False,
        "authority_bundle_generated": False,
        "authority_changed": False,
        "base_commit": BASE_COMMIT,
        "candidate_valence_ledger_is_gap_signal_only": True,
        "candidate_valence_ledger_is_reaction_authority": False,
        "feature_semantics_reaudit_required_before_training": True,
        "field_count": 41,
        "formal_post_reaction_authority_count": 0,
        "formal_worklist_modified": False,
        "frozen_field_count": 16,
        "future_field_count": 25,
        "future_nonblank_count": 0,
        "gap_evidence_row_count": 2,
        "human_answers_prefilled": False,
        "model_changed": False,
        "overlay_formal_commit": OVERLAY_FORMAL_COMMIT,
        "parent_review_unit_id": overlay.PARENT_REVIEW_UNIT_ID,
        "post_state_generated": False,
        "reaction_family_id": overlay.REACTION_FAMILY_ID,
        "ready_for_controlled_editable_copy": True,
        "ready_for_direct_submission": False,
        "ready_for_training": False,
        "review_ingested": False,
        "review_submission_compiled": False,
        "role_or_seed_generated": False,
        "sample_count": 2,
        "schema_template_count": 8,
        "source_inventory_row_count": 35,
        "source_overlay_artifact_sha256": _source_overlay_sha_witness(),
        "template_file_count": 6,
        "template_file_sha256": {
            name: _sha256(other_five[name]) for name in TEMPLATE_FILES[:-1]
        },
        "template_version": TEMPLATE_VERSION,
        "tensor_materialized": False,
        "training_used": False,
        "transformation_review_unit_id": overlay.TRANSFORMATION_REVIEW_UNIT_ID,
        "warhead_rule_id": overlay.WARHEAD_RULE_ID,
    }


def _build_payloads(artifacts: Mapping[str, bytes]) -> dict[str, bytes]:
    payloads: dict[str, bytes] = {
        README_FILE: README_TEXT.encode("utf-8"),
        WORKLIST_FILE: _build_worklist(artifacts),
        SCHEMA_FILE: _canonical_json_bytes(deepcopy(overlay.STRUCTURED_JSON_SCHEMAS)),
        GAP_FILE: artifacts[overlay.GAP_MATRIX_PATH],
        SOURCE_FILE: artifacts[overlay.SOURCE_INVENTORY_PATH],
    }
    payloads[MANIFEST_FILE] = _canonical_json_bytes(_manifest(payloads))
    if tuple(payloads) != TEMPLATE_FILES:
        raise ValueError(ERROR)
    return payloads


def _validate_payloads(payloads: object) -> None:
    try:
        if (
            type(payloads) is not dict
            or tuple(payloads) != TEMPLATE_FILES
            or any(type(value) is not bytes for value in payloads.values())
            or any(
                not value
                or len(value) >= 1024 * 1024
                or value.startswith(b"\xef\xbb\xbf")
                or b"\x00" in value
                for value in payloads.values()
            )
            or payloads[README_FILE] != README_TEXT.encode("utf-8")
            or _sha256(payloads[GAP_FILE])
            != OVERLAY_ARTIFACT_SHA256[overlay.GAP_MATRIX_PATH]
            or _sha256(payloads[SOURCE_FILE])
            != OVERLAY_ARTIFACT_SHA256[overlay.SOURCE_INVENTORY_PATH]
        ):
            raise ValueError(ERROR)
        fields, rows = overlay.ALL_FIELDS, _strict_csv(
            payloads[WORKLIST_FILE], overlay.ALL_FIELDS
        )
        if (
            len(rows) != 1
            or tuple(rows[0]) != fields
            or {field: rows[0][field] for field in overlay.FROZEN_FIELDS}
            != overlay._frozen_initial_values()
            or any(rows[0][field] != "" for field in overlay.FUTURE_FIELDS)
        ):
            raise ValueError(ERROR)
        schemas = _strict_json(payloads[SCHEMA_FILE], dict)
        overlay._validate_structured_json_schema_contracts_v1()
        if schemas != overlay.STRUCTURED_JSON_SCHEMAS:
            raise ValueError(ERROR)
        gap_rows = _strict_csv(payloads[GAP_FILE], overlay.GAP_MATRIX_COLUMNS)
        source_rows = _strict_csv(
            payloads[SOURCE_FILE], overlay.SOURCE_INVENTORY_COLUMNS
        )
        if (
            gap_rows != list(overlay._gap_rows())
            or len(gap_rows) != 2
            or source_rows != list(overlay._source_inventory_rows())
            or len(source_rows) != 35
            or any(
                row["authoritative_for_transformation"] != "false"
                for row in source_rows
            )
        ):
            raise ValueError(ERROR)
        manifest = _strict_json(payloads[MANIFEST_FILE], dict)
        if manifest != _manifest({
            name: payloads[name] for name in TEMPLATE_FILES[:-1]
        }):
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
    blob = _git_text(
        repo_root, ("hash-object", "--no-filters", "--", path)
    ).strip()
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
    origin = _git_text(
        repo_root, ("rev-parse", "refs/remotes/origin/main")
    ).strip()
    ahead_text, behind_text = _git_text(
        repo_root,
        ("rev-list", "--left-right", "--count", "HEAD...refs/remotes/origin/main"),
    ).split()
    revisions = set(
        _git_text(repo_root, ("rev-list", f"{BASE_COMMIT}..{head}")).splitlines()
    )
    revisions.update(
        _git_text(repo_root, ("rev-list", f"{BASE_COMMIT}..{origin}")).splitlines()
    )
    path_commits: list[dict[str, object]] = []
    for commit in sorted(revisions):
        lines = _git_text(
            repo_root,
            (
                "diff-tree", "--root", "--no-commit-id", "--name-status", "-r",
                commit,
            ),
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
                metadata, listed = line.split("\t", 1)
                mode, kind, blob = metadata.split()
                if listed != path or kind != "blob":
                    raise ValueError(ERROR)
                modes[path], blobs[path] = mode, blob
        path_commits.append({
            "commit": commit,
            "parents": _git_text(
                repo_root, ("show", "-s", "--format=%P", commit)
            ).split(),
            "subject": _git_text(
                repo_root, ("show", "-s", "--format=%s", commit)
            ).strip(),
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
        "tracked": tuple(sorted(
            _git_text(repo_root, ("diff", "--name-only")).splitlines()
        )),
        "staged": tuple(sorted(
            _git_text(repo_root, ("diff", "--cached", "--name-only")).splitlines()
        )),
        "untracked": tuple(sorted(
            _git_text(
                repo_root, ("ls-files", "--others", "--exclude-standard")
            ).splitlines()
        )),
        "porcelain": tuple(sorted(
            _git_text(
                repo_root,
                ("status", "--porcelain=v1", "--untracked-files=all"),
            ).splitlines()
        )),
        "path_commits": path_commits,
        "live_paths": {
            path: _collect_live_identity(repo_root, path)
            for path in CANDIDATE_PATHS
        },
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
                "lifecycle_profile": (
                    "transformation_template_materializer_precommit_candidate"
                ),
                "formal_candidate_commit": "",
            }
        commit = commits[0]
        if (
            not _is_hex(commit["commit"], 40)
            or commit["parents"] != [BASE_COMMIT]
            or commit["subject"] != FORMAL_COMMIT_SUBJECT
            or commit["changed_paths"] != CANDIDATE_PATHS
            or commit["changed_statuses"]
            != {path: "A" for path in CANDIDATE_PATHS}
            or any(
                commit["path_modes"].get(path) != "100644"
                for path in CANDIDATE_PATHS
            )
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
                path in facts["tracked"]
                or path in facts["staged"]
                or path in facts["untracked"]
                for path in CANDIDATE_PATHS
            )
        ):
            raise ValueError(ERROR)
        if commit["ancestor_origin"] is True:
            return {
                "origin_main": facts["origin"],
                "ahead": facts["ahead"],
                "behind": facts["behind"],
                "lifecycle_profile": (
                    "transformation_template_materializer_published_successor"
                ),
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
            "lifecycle_profile": (
                "transformation_template_materializer_committed_unpushed"
            ),
            "formal_candidate_commit": commit["commit"],
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error


def _build_for_validation(
    *, repo_root: Path, state_root: Path, validate_candidate: bool,
) -> tuple[dict[str, bytes], dict[str, object]]:
    artifacts = _validate_overlay_commit_identity(repo_root)
    _validate_overlay_artifacts(artifacts)
    overlay_response = (
        overlay.evaluate_covapie_current11_reaction_transformation_evidence_overlay_contract_v1(
            repo_root=repo_root,
            state_root=state_root,
        )
    )
    _validate_overlay_response(overlay_response)
    if overlay_response["artifact_sha256"] != _source_overlay_sha_witness():
        raise ValueError(ERROR)
    lifecycle = (
        _derive_lifecycle(_collect_lifecycle(repo_root))
        if validate_candidate
        else {
            "origin_main": BASE_COMMIT,
            "ahead": 0,
            "behind": 0,
            "lifecycle_profile": (
                "transformation_template_materializer_precommit_candidate"
            ),
            "formal_candidate_commit": "",
        }
    )
    payloads = _build_payloads(artifacts)
    second = _build_payloads(artifacts)
    if payloads != second:
        raise ValueError(ERROR)
    _validate_payloads(payloads)
    return payloads, lifecycle


def build_covapie_current11_unit_000001_reaction_transformation_evidence_acquisition_template_v1(
    *,
    repo_root: Path,
    state_root: Path,
) -> dict[str, bytes]:
    """Return the deterministic, unfilled Exact6 acquisition template."""

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
            or _git_text(repository, ("rev-parse", "--show-toplevel")).strip()
            != str(repository)
        ):
            raise ValueError(ERROR)
        payloads, _lifecycle = _build_for_validation(
            repo_root=repository,
            state_root=state,
            validate_candidate=True,
        )
        return payloads
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR:
            raise
        raise ValueError(ERROR) from error
