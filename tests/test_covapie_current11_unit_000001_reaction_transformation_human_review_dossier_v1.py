from __future__ import annotations

import csv
import hashlib
import importlib.util
import inspect
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Mapping

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_current11_reaction_transformation_evidence_overlay_contract_v1
    as overlay,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_unit_000001_reaction_transformation_human_review_dossier_v1
    as dossier,
)


SCRIPT = ROOT / dossier.SCRIPT_PATH


def _locate_formal_state() -> Path:
    local = ROOT.parent / "covapie-state"
    if local.is_dir():
        return local
    remote = subprocess.check_output(
        ("git", "config", "--get", "remote.origin.url"), cwd=ROOT
    ).decode("utf-8").strip()
    remote_path = Path(remote)
    candidate = remote_path.parent / "covapie-state"
    if not remote_path.is_absolute() or not candidate.is_dir():
        raise AssertionError("formal state unavailable")
    return candidate


FORMAL_STATE = _locate_formal_state()
FORMAL_TARGET = FORMAL_STATE / dossier.DOSSIER_RELATIVE


def _load_materializer():
    spec = importlib.util.spec_from_file_location("transformation_dossier_materializer", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


materializer = _load_materializer()


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _residue_counts(output: Path) -> dict[str, int]:
    parent = output.parent
    return {
        label: len(tuple(parent.glob(pattern))) if parent.exists() else 0
        for label, pattern in (
            ("temp", "*tmp*"),
            ("probe", "*probe*"),
            ("backup", "*backup*"),
        )
    }


def _assert_formal_dossier_target_state_is_valid(
    *,
    state_root: Path,
    output: Path,
    expected_payloads: Mapping[str, bytes],
    require_present: bool | None,
) -> dict[str, object]:
    residues = _residue_counts(output)
    assert residues == {"temp": 0, "probe": 0, "backup": 0}
    present = os.path.lexists(output)
    if require_present is not None:
        assert present is require_present
    if not present:
        assert not output.is_symlink()
        return {"state": "absent", "residue": residues}
    metadata = output.lstat()
    assert stat.S_ISDIR(metadata.st_mode) and not output.is_symlink()
    assert stat.S_IMODE(metadata.st_mode) == 0o755
    entries = tuple(sorted(output.iterdir(), key=lambda item: item.name))
    assert tuple(item.name for item in entries) == tuple(sorted(dossier.DOSSIER_FILES))
    assert len(entries) == 8
    assert sum(item.is_dir() for item in entries) == 0
    assert sum(item.is_symlink() for item in entries) == 0
    for child in entries:
        child_metadata = child.lstat()
        assert stat.S_ISREG(child_metadata.st_mode)
        assert not child.is_symlink()
        assert stat.S_IMODE(child_metadata.st_mode) == 0o644
        assert child.read_bytes() == expected_payloads[child.name]
    report = materializer._check_dossier(
        repo_root=ROOT, state_root=state_root, output_dir=output
    )
    assert report["dossier_file_count"] == 8
    return {
        "state": "published",
        "identity": (metadata.st_dev, metadata.st_ino),
        "mode": "0755",
        "files": tuple(
            (
                child.name,
                child.lstat().st_dev,
                child.lstat().st_ino,
                stat.S_IMODE(child.lstat().st_mode),
                _sha(child.read_bytes()),
            )
            for child in entries
        ),
        "residue": residues,
    }


def _state_snapshot(
    state: Path, expected_payloads: Mapping[str, bytes],
) -> dict[str, object]:
    formal = state == ROOT.parent / "covapie-state"
    editable, editable_identity = dossier._validate_editable(
        ROOT, state, formal=formal
    )
    immutable, immutable_identity = dossier._validate_immutable(
        state, formal=formal
    )
    family, family_identity, workspace, workspace_identity = (
        dossier._validate_family_sources(state, formal=formal)
    )
    family_text = workspace["family_rule_approval_worklist.csv"].decode("utf-8")
    family_rows = list(csv.DictReader(io.StringIO(family_text, newline="")))
    questionnaire = family["human_review_questionnaire.md"].decode("utf-8")
    return {
        "source_tree": dossier._source_snapshot(state),
        "editable_identity": editable_identity,
        "editable_runtime": dossier._editable_runtime_report(editable),
        "immutable_identity": immutable_identity,
        "immutable_sha256": {name: _sha(value) for name, value in immutable.items()},
        "family_workspace_identity": workspace_identity,
        "family_workspace_sha256": {
            name: _sha(value) for name, value in workspace.items()
        },
        "family_human_blank_count": sum(
            row[field] == ""
            for row in family_rows
            for field in overlay.HISTORICAL_HUMAN_FIELDS
        ),
        "family_dossier_identity": family_identity,
        "family_dossier_sha256": {name: _sha(value) for name, value in family.items()},
        "family_questionnaire_blank_count": sum(
            questionnaire.splitlines().count(f"{field}:")
            for field in overlay.HISTORICAL_HUMAN_FIELDS
        ),
        "target": _assert_formal_dossier_target_state_is_valid(
            state_root=state,
            output=state / dossier.DOSSIER_RELATIVE,
            expected_payloads=expected_payloads,
            require_present=None,
        ),
    }


def _copy_tree(source: Path, target: Path) -> None:
    shutil.copytree(source, target, symlinks=False)
    os.chmod(target, 0o755)
    for child in target.iterdir():
        if child.is_file():
            os.chmod(child, 0o644)


def _edit_worklist(path: Path, field: str, value: str) -> None:
    text = path.read_text(encoding="utf-8")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    fields = tuple(reader.fieldnames or ())
    rows = list(reader)
    assert fields == overlay.ALL_FIELDS and len(rows) == 1
    rows[0][field] = value
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    path.write_bytes(stream.getvalue().encode("utf-8"))
    os.chmod(path, 0o644)


def _temporary_state(tmp_path: Path) -> tuple[Path, Path]:
    state = tmp_path / "covapie-state"
    review = state / "manual-review"
    aids = state / "manual-review-aids"
    review.mkdir(parents=True)
    aids.mkdir()

    editable_source = FORMAL_STATE / dossier.EDITABLE_RELATIVE
    _copy_tree(editable_source, state / dossier.EDITABLE_RELATIVE)

    immutable_canonical = FORMAL_STATE / dossier.IMMUTABLE_RELATIVE
    immutable_object = immutable_canonical.parent / os.readlink(immutable_canonical)
    _copy_tree(immutable_object, review / dossier.IMMUTABLE_OBJECT_NAME)
    os.symlink(
        dossier.IMMUTABLE_OBJECT_NAME,
        state / dossier.IMMUTABLE_RELATIVE,
        target_is_directory=True,
    )

    family_canonical = FORMAL_STATE / dossier.FAMILY_WORKSPACE_RELATIVE
    family_object = family_canonical.parent / os.readlink(family_canonical)
    _copy_tree(family_object, review / overlay.WORKSPACE_TARGET)
    os.symlink(
        overlay.WORKSPACE_TARGET,
        state / dossier.FAMILY_WORKSPACE_RELATIVE,
        target_is_directory=True,
    )

    family_dossier = FORMAL_STATE / dossier.FAMILY_DOSSIER_RELATIVE
    _copy_tree(family_dossier, state / dossier.FAMILY_DOSSIER_RELATIVE)
    parent = state / dossier.DOSSIER_PARENT_RELATIVE
    parent.mkdir(parents=True)
    output = state / dossier.DOSSIER_RELATIVE
    return state, output


@pytest.fixture(scope="session")
def built() -> dict[str, bytes]:
    return dossier.build_covapie_current11_unit_000001_reaction_transformation_human_review_dossier_v1(
        repo_root=ROOT,
        state_root=FORMAL_STATE,
    )


@pytest.fixture(scope="module", autouse=True)
def protect_formal_state(built: dict[str, bytes]):
    before = _state_snapshot(FORMAL_STATE, built)
    _assert_formal_dossier_target_state_is_valid(
        state_root=FORMAL_STATE,
        output=FORMAL_TARGET,
        expected_payloads=built,
        require_present=None,
    )
    yield
    after = _state_snapshot(FORMAL_STATE, built)
    assert after == before
    _assert_formal_dossier_target_state_is_valid(
        state_root=FORMAL_STATE,
        output=FORMAL_TARGET,
        expected_payloads=built,
        require_present=None,
    )


def _materialize(tmp_path: Path, built: Mapping[str, bytes]) -> tuple[Path, Path]:
    state, output = _temporary_state(tmp_path)
    del built
    expected = dossier.build_covapie_current11_unit_000001_reaction_transformation_human_review_dossier_v1(
        repo_root=ROOT, state_root=state
    )
    report = materializer._materialize_dossier(
        repo_root=ROOT,
        state_root=state,
        output_dir=output,
        payloads=expected,
    )
    assert report["dossier_file_count"] == 8
    return state, output


def test_unique_keyword_only_public_api() -> None:
    name = (
        "build_covapie_current11_unit_000001_reaction_transformation_"
        "human_review_dossier_v1"
    )
    assert dossier.__all__ == (name,)
    signature = inspect.signature(getattr(dossier, name))
    assert list(signature.parameters) == ["repo_root", "state_root"]
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )


@pytest.mark.parametrize("path", (ROOT / dossier.MODULE_PATH, SCRIPT))
def test_import_is_silent(path: Path) -> None:
    code = (
        "import importlib.util;"
        f"s=importlib.util.spec_from_file_location('silent_target',{str(path)!r});"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m)"
    )
    completed = subprocess.run(
        (sys.executable, "-B", "-c", code),
        cwd=ROOT,
        check=False,
        capture_output=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "src"},
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == b""


def test_base_commit_identity() -> None:
    assert subprocess.check_output(("git", "cat-file", "-t", dossier.BASE_COMMIT), cwd=ROOT).decode().strip() == "commit"
    assert subprocess.check_output(("git", "show", "-s", "--format=%T", dossier.BASE_COMMIT), cwd=ROOT).decode().strip() == dossier.BASE_TREE
    assert subprocess.check_output(("git", "show", "-s", "--format=%P", dossier.BASE_COMMIT), cwd=ROOT).decode().split() == [dossier.BASE_PARENT]
    assert subprocess.check_output(("git", "show", "-s", "--format=%s", dossier.BASE_COMMIT), cwd=ROOT).decode().strip() == dossier.BASE_SUBJECT
    head = subprocess.check_output(("git", "rev-parse", "HEAD"), cwd=ROOT).decode().strip()
    origin = subprocess.check_output(("git", "rev-parse", "refs/remotes/origin/main"), cwd=ROOT).decode().strip()
    assert dossier._is_ancestor(ROOT, dossier.BASE_COMMIT, head)
    assert dossier._is_ancestor(ROOT, dossier.BASE_COMMIT, origin)


def test_controlled_review_formal_candidate_identity() -> None:
    dossier._validate_commit_identity(ROOT)
    assert dossier.CONTROLLED_REVIEW_FORMAL_CANDIDATE_COMMIT == dossier.BASE_PARENT


def test_formal_editable_workspace_identity_and_exact6() -> None:
    payloads, identity = dossier._validate_editable(ROOT, FORMAL_STATE, formal=True)
    assert tuple(payloads) == tuple(dossier.EDITABLE_INITIAL_FILE_SHA256)
    assert {
        name: _sha(payloads[name]) for name in dossier.EDITABLE_REFERENCE_FILES
    } == dossier.EDITABLE_REFERENCE_FILE_SHA256
    assert _sha(payloads["transformation_evidence_worklist.csv"]) == dossier.INITIAL_BLANK_WORKLIST_SHA256
    assert (identity["st_dev"], identity["st_ino"]) == dossier.EDITABLE_IDENTITY
    assert identity["mode"] == "0755"


def test_formal_worklist_exact41_and_exact25_blank() -> None:
    payloads, _identity = dossier._validate_editable(ROOT, FORMAL_STATE, formal=True)
    rows = dossier._validate_worklist(payloads["transformation_evidence_worklist.csv"])
    assert len(rows) == 1
    assert len(rows[0]) == 41
    assert sum(rows[0][field] != "" for field in overlay.FUTURE_FIELDS) == 0


def test_immutable_template_identity_and_exact6() -> None:
    payloads, identity = dossier._validate_immutable(FORMAL_STATE, formal=True)
    assert tuple(payloads) == tuple(dossier.IMMUTABLE_SHA256)
    assert identity["readlink"] == dossier.IMMUTABLE_OBJECT_NAME
    assert (identity["canonical_st_dev"], identity["canonical_st_ino"]) == dossier.IMMUTABLE_CANONICAL_IDENTITY
    assert (identity["object"]["st_dev"], identity["object"]["st_ino"]) == dossier.IMMUTABLE_OBJECT_IDENTITY


def test_family_workspace_identity_exact5_and_210_blank_cells() -> None:
    _fd, _fdi, workspace, identity = dossier._validate_family_sources(FORMAL_STATE, formal=True)
    assert tuple(workspace) == tuple(dossier.FAMILY_WORKSPACE_SHA256)
    assert (identity["canonical_st_dev"], identity["canonical_st_ino"]) == dossier.FAMILY_WORKSPACE_CANONICAL_IDENTITY
    text = workspace["family_rule_approval_worklist.csv"].decode("utf-8")
    import csv
    import io
    rows = list(csv.DictReader(io.StringIO(text, newline="")))
    assert len(rows) * len(overlay.HISTORICAL_HUMAN_FIELDS) == 210
    assert all(row[field] == "" for row in rows for field in overlay.HISTORICAL_HUMAN_FIELDS)


def test_family_dossier_identity_exact6_and_30_blank() -> None:
    family, identity, _workspace, _wi = dossier._validate_family_sources(FORMAL_STATE, formal=True)
    assert tuple(family) == tuple(dossier.FAMILY_DOSSIER_SHA256)
    assert (identity["st_dev"], identity["st_ino"]) == dossier.FAMILY_DOSSIER_IDENTITY
    text = family["human_review_questionnaire.md"].decode("utf-8")
    assert sum(text.splitlines().count(f"{field}:") for field in overlay.HISTORICAL_HUMAN_FIELDS) == 30


def test_builder_is_deterministic_and_read_only() -> None:
    before = dossier._source_snapshot(FORMAL_STATE)
    first = dossier.build_covapie_current11_unit_000001_reaction_transformation_human_review_dossier_v1(repo_root=ROOT, state_root=FORMAL_STATE)
    second = dossier.build_covapie_current11_unit_000001_reaction_transformation_human_review_dossier_v1(repo_root=ROOT, state_root=FORMAL_STATE)
    assert first == second
    assert dossier._source_snapshot(FORMAL_STATE) == before


def test_dossier_exact8(built: dict[str, bytes]) -> None:
    assert tuple(built) == dossier.DOSSIER_FILES
    assert len(built) == 8


@pytest.mark.parametrize(
    ("name", "source"),
    (
        (dossier.GRAPH_FILE, FORMAL_STATE / dossier.FAMILY_DOSSIER_RELATIVE / dossier.GRAPH_FILE),
        (dossier.GAP_FILE, FORMAL_STATE / dossier.EDITABLE_RELATIVE / dossier.GAP_FILE),
        (dossier.SOURCE_FILE, FORMAL_STATE / dossier.EDITABLE_RELATIVE / dossier.SOURCE_FILE),
        (dossier.SCHEMA_FILE, FORMAL_STATE / dossier.EDITABLE_RELATIVE / dossier.SCHEMA_FILE),
    ),
)
def test_four_files_are_byte_copies(built: dict[str, bytes], name: str, source: Path) -> None:
    assert built[name] == source.read_bytes()
    manifest = json.loads(built[dossier.MANIFEST_FILE])
    assert manifest["copied_source_file_sha256"][name] == _sha(source.read_bytes())


def test_summary_frozen_identity_facts(built: dict[str, bytes]) -> None:
    summary = json.loads(built[dossier.SUMMARY_FILE])
    assert summary["review_unit_id"] == dossier.REVIEW_UNIT_ID
    assert summary["parent_review_unit_id"] == dossier.PARENT_REVIEW_UNIT_ID
    assert summary["reaction_family_id"] == dossier.REACTION_FAMILY_ID
    assert summary["warhead_rule_id"] == dossier.WARHEAD_RULE_ID
    assert summary["candidate_local_graph_rule_sha256"] == dossier.CANDIDATE_RULE_SHA256


def test_summary_two_samples_have_exact_order_and_facts(built: dict[str, bytes]) -> None:
    summary = json.loads(built[dossier.SUMMARY_FILE])
    assert summary["samples"] == [dict(sample) for sample in dossier.SAMPLES]
    assert [sample["sample_index_row_id"] for sample in summary["samples"]] == list(overlay.SAMPLE_IDS)


def test_summary_valence_is_gap_signal_only(built: dict[str, bytes]) -> None:
    summary = json.loads(built[dossier.SUMMARY_FILE])
    assert summary["pre_reaction_center_bond_order_sum"] == 4
    assert summary["conditional_post_bond_order_sum_if_internal_bonds_unchanged"] == 5
    assert summary["candidate_valence_ledger_is_gap_signal_only"] is True
    assert summary["candidate_valence_ledger_is_reaction_authority"] is False


def test_summary_missing_authority_and_no_generated_answers(built: dict[str, bytes]) -> None:
    summary = json.loads(built[dossier.SUMMARY_FILE])
    assert summary["formal_post_reaction_authority_count"] == 0
    for field in ("post_reaction_graph_authority", "post_internal_bond_delta_authority", "post_formal_charge_authority", "post_protonation_authority"):
        assert summary[field] == "missing"
    assert "reviewed_bond_order_changes_json" not in summary
    assert "reviewed_leaving_group_contract_json" not in summary


def test_questionnaire_exact25_order(built: dict[str, bytes]) -> None:
    text = built[dossier.QUESTIONNAIRE_FILE].decode("utf-8")
    found = re.findall(r"^field_name: `([^`]+)`$", text, flags=re.MULTILINE)
    assert found == list(overlay.FUTURE_FIELDS)


def test_questionnaire_all_answer_slots_are_blank(built: dict[str, bytes]) -> None:
    text = built[dossier.QUESTIONNAIRE_FILE].decode("utf-8")
    assert text.count("current_status: unreviewed") == 25
    assert text.count("proposed_value:\n") == 25
    assert text.count("supporting_evidence_reference:\n") == 25
    assert text.count("reviewer_notes:\n") == 25
    assert "current_status: not_claimed" not in text


@pytest.mark.parametrize(
    "phrase",
    (
        "non-authoritative human review aid",
        "not the formal\nworklist",
        "cannot be submitted directly",
        "candidate graph is not post-state authority",
        "Missing does not mean not_claimed",
        "empty string does not mean an explicit reviewed empty list",
        "feature-semantics audit remains\nrequired before training",
        "ready_for_training=false",
    ),
)
def test_readme_non_authority_boundaries(built: dict[str, bytes], phrase: str) -> None:
    assert phrase in built[dossier.README_FILE].decode("utf-8")


def test_manifest_source_identities_and_sha(built: dict[str, bytes]) -> None:
    manifest = json.loads(built[dossier.MANIFEST_FILE])
    assert manifest["base_commit"] == dossier.BASE_COMMIT
    assert manifest["controlled_review_formal_candidate_commit"] == dossier.CONTROLLED_REVIEW_FORMAL_CANDIDATE_COMMIT
    assert manifest["source_editable_initial_file_sha256"] == dossier.EDITABLE_INITIAL_FILE_SHA256
    assert manifest["source_editable_reference_file_sha256"] == dossier.EDITABLE_REFERENCE_FILE_SHA256
    assert manifest["source_editable_initial_worklist_sha256"] == dossier.INITIAL_BLANK_WORKLIST_SHA256
    assert manifest["source_editable_live_worklist_binding"] == "exact41_frozen16_only_future25_mutable_v1"
    assert manifest["source_editable_initial_snapshot_semantics"] == "initial_blank_workspace_snapshot_v1"
    assert "source_editable_file_sha256" not in manifest
    assert manifest["source_editable_workspace_identity"]["st_ino"] == dossier.EDITABLE_IDENTITY[1]
    assert manifest["source_family_dossier_identity"]["st_ino"] == dossier.FAMILY_DOSSIER_IDENTITY[1]


def test_manifest_hashes_exact7_without_self_hash(built: dict[str, bytes]) -> None:
    manifest = json.loads(built[dossier.MANIFEST_FILE])
    assert manifest["dossier_file_sha256"] == {name: _sha(built[name]) for name in dossier.DOSSIER_FILES[:-1]}
    assert dossier.MANIFEST_FILE not in manifest["dossier_file_sha256"]


def test_manifest_non_generation_and_readiness_flags(built: dict[str, bytes]) -> None:
    manifest = json.loads(built[dossier.MANIFEST_FILE])
    assert manifest["human_answers_prefilled"] is False
    assert manifest["semantic_validation_performed"] is False
    assert manifest["post_state_generated"] is False
    assert manifest["atom_map_answers_generated"] is False
    assert manifest["authority_changed"] is False
    assert manifest["ready_for_human_evidence_acquisition"] is True
    assert manifest["ready_for_formal_worklist_update"] is False
    assert manifest["ready_for_semantic_validation"] is False
    assert manifest["ready_for_direct_submission"] is False
    assert manifest["feature_semantics_reaudit_required_before_training"] is True
    assert manifest["ready_for_training"] is False


def test_formal_dossier_target_state_is_valid(built: dict[str, bytes]) -> None:
    report = _assert_formal_dossier_target_state_is_valid(
        state_root=FORMAL_STATE,
        output=FORMAL_TARGET,
        expected_payloads=built,
        require_present=None,
    )
    assert report["state"] in {"absent", "published"}


def test_temporary_materialization_succeeds(tmp_path: Path, built: dict[str, bytes]) -> None:
    state, output = _materialize(tmp_path, built)
    assert output.is_dir() and not output.is_symlink()
    assert {path.name for path in output.iterdir()} == set(dossier.DOSSIER_FILES)
    expected = dossier.build_covapie_current11_unit_000001_reaction_transformation_human_review_dossier_v1(
        repo_root=ROOT, state_root=state
    )
    report = _assert_formal_dossier_target_state_is_valid(
        state_root=state,
        output=output,
        expected_payloads=expected,
        require_present=True,
    )
    assert report["state"] == "published"


def test_materialized_modes_ignore_umask(tmp_path: Path, built: dict[str, bytes]) -> None:
    previous = os.umask(0o077)
    try:
        _state, output = _materialize(tmp_path, built)
    finally:
        os.umask(previous)
    assert stat.S_IMODE(output.lstat().st_mode) == 0o755
    assert all(stat.S_IMODE(path.lstat().st_mode) == 0o644 for path in output.iterdir())


def test_cli_check_twice_is_read_only_and_deterministic(tmp_path: Path) -> None:
    state, output = _temporary_state(tmp_path)
    base = (sys.executable, "-B", str(SCRIPT), "--repo-root", str(ROOT), "--state-root", str(state), "--output-dir", str(output))
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    created = subprocess.run(base, cwd=ROOT, check=False, capture_output=True, env=env)
    assert created.returncode == 0 and created.stderr == b""
    before = tuple((path.name, path.lstat().st_ino, _sha(path.read_bytes())) for path in sorted(output.iterdir()))
    first = subprocess.run((*base, "--check"), cwd=ROOT, check=False, capture_output=True, env=env)
    second = subprocess.run((*base, "--check"), cwd=ROOT, check=False, capture_output=True, env=env)
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout and first.stderr == second.stderr == b""
    assert tuple((path.name, path.lstat().st_ino, _sha(path.read_bytes())) for path in sorted(output.iterdir())) == before


def test_future_editable_worklist_keeps_dossier_byte_stable_and_checkable(
    tmp_path: Path,
) -> None:
    state, output = _temporary_state(tmp_path)
    initial = dossier.build_covapie_current11_unit_000001_reaction_transformation_human_review_dossier_v1(
        repo_root=ROOT, state_root=state
    )
    worklist = state / dossier.EDITABLE_RELATIVE / "transformation_evidence_worklist.csv"
    future_value = "human review pending semantic validation"
    _edit_worklist(worklist, "review_notes", future_value)
    editable_payloads, _identity = dossier._validate_editable(
        ROOT, state, formal=False
    )
    runtime = dossier._editable_runtime_report(editable_payloads)
    assert runtime["source_current_future_nonblank_count"] == 1
    edited = dossier.build_covapie_current11_unit_000001_reaction_transformation_human_review_dossier_v1(
        repo_root=ROOT, state_root=state
    )
    assert edited == initial
    assert all(future_value.encode("utf-8") not in payload for payload in edited.values())
    materializer._materialize_dossier(
        repo_root=ROOT, state_root=state, output_dir=output, payloads=edited
    )
    base = (
        sys.executable,
        "-B",
        str(SCRIPT),
        "--repo-root",
        str(ROOT),
        "--state-root",
        str(state),
        "--output-dir",
        str(output),
        "--check",
    )
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    first = subprocess.run(base, cwd=ROOT, check=False, capture_output=True, env=env)
    second = subprocess.run(base, cwd=ROOT, check=False, capture_output=True, env=env)
    assert first.returncode == second.returncode == 0
    assert first.stdout == second.stdout and first.stderr == second.stderr == b""
    report = json.loads(first.stdout)
    assert report["source_current_future_nonblank_count"] == 1
    assert report["semantic_validation_performed"] is False
    assert report["authority_changed"] is False
    assert report["ready_for_direct_submission"] is False
    assert report["ready_for_training"] is False


def test_editable_worklist_frozen_drift_fails_closed(tmp_path: Path) -> None:
    state, output = _temporary_state(tmp_path)
    initial = dossier.build_covapie_current11_unit_000001_reaction_transformation_human_review_dossier_v1(
        repo_root=ROOT, state_root=state
    )
    materializer._materialize_dossier(
        repo_root=ROOT, state_root=state, output_dir=output, payloads=initial
    )
    worklist = state / dossier.EDITABLE_RELATIVE / "transformation_evidence_worklist.csv"
    _edit_worklist(
        worklist,
        overlay.FROZEN_FIELDS[0],
        f"{dossier.REVIEW_UNIT_ID}_DRIFT",
    )
    with pytest.raises(ValueError, match=dossier.ERROR):
        dossier.build_covapie_current11_unit_000001_reaction_transformation_human_review_dossier_v1(
            repo_root=ROOT, state_root=state
        )
    with pytest.raises(ValueError, match=dossier.ERROR):
        materializer._check_dossier(
            repo_root=ROOT, state_root=state, output_dir=output
        )


def test_existing_target_is_preserved(tmp_path: Path, built: dict[str, bytes]) -> None:
    state, output = _temporary_state(tmp_path)
    output.mkdir()
    marker = output / "human.txt"
    marker.write_text("preserve\n", encoding="utf-8")
    identity = materializer._identity(output)
    with pytest.raises(FileExistsError, match=dossier.ERROR):
        materializer._materialize_dossier(repo_root=ROOT, state_root=state, output_dir=output, payloads=built)
    assert materializer._identity(output) == identity
    assert marker.read_bytes() == b"preserve\n"


def test_partial_write_cleanup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, built: dict[str, bytes]) -> None:
    state, output = _temporary_state(tmp_path)
    original = materializer._write_payload
    calls = 0
    def fail_second(path: Path, payload: bytes) -> tuple[int, int]:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected write failure")
        return original(path, payload)
    monkeypatch.setattr(materializer, "_write_payload", fail_second)
    with pytest.raises(OSError, match="injected write failure"):
        materializer._materialize_dossier(repo_root=ROOT, state_root=state, output_dir=output, payloads=built)
    assert not os.path.lexists(output)


def test_file_inode_replacement_is_preserved(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, built: dict[str, bytes]) -> None:
    state, output = _temporary_state(tmp_path)
    original = materializer._write_payload
    first: Path | None = None
    calls = 0
    def replace_then_fail(path: Path, payload: bytes) -> tuple[int, int]:
        nonlocal calls, first
        calls += 1
        if calls == 1:
            first = path
            return original(path, payload)
        assert first is not None
        first.rename(tmp_path / "parked-owned-file")
        first.write_bytes(b"competitor\n")
        os.chmod(first, 0o644)
        raise OSError("trigger cleanup")
    monkeypatch.setattr(materializer, "_write_payload", replace_then_fail)
    with pytest.raises(ValueError, match=dossier.ERROR):
        materializer._materialize_dossier(repo_root=ROOT, state_root=state, output_dir=output, payloads=built)
    assert (output / dossier.README_FILE).read_bytes() == b"competitor\n"


def test_directory_inode_replacement_is_preserved(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, built: dict[str, bytes]) -> None:
    state, output = _temporary_state(tmp_path)
    parked = tmp_path / "parked-owned-directory"
    def replace_directory(path: Path, expected: Mapping[str, bytes], *, expected_directory_identity=None):
        assert path == output and expected_directory_identity is not None
        path.rename(parked)
        path.mkdir()
        (path / "competitor.txt").write_text("preserve\n", encoding="utf-8")
        raise OSError("trigger cleanup")
    monkeypatch.setattr(materializer, "_validate_dossier_tree", replace_directory)
    with pytest.raises(ValueError, match=dossier.ERROR):
        materializer._materialize_dossier(repo_root=ROOT, state_root=state, output_dir=output, payloads=built)
    assert (output / "competitor.txt").read_bytes() == b"preserve\n"
    assert len(tuple(parked.iterdir())) == 8


@pytest.mark.parametrize(
    "case",
    (
        "wrong_name",
        "external_parent",
        "symlink_parent",
        "alias_symlink_to_valid_parent",
        "symlinked_state_root",
        "relative_output_path",
        "relative_state_root",
    ),
)
def test_output_parent_boundary(tmp_path: Path, built: dict[str, bytes], case: str) -> None:
    state, canonical = _temporary_state(tmp_path)
    external = tmp_path / "external"
    external.mkdir()
    marker = external / "marker.txt"
    marker.write_text("preserve\n", encoding="utf-8")
    state_argument = state
    if case == "wrong_name":
        output = canonical.parent / "wrong-name"
    elif case == "external_parent":
        output = external / dossier.REVIEW_UNIT_ID
    elif case == "symlink_parent":
        canonical.parent.rmdir()
        os.symlink(external, canonical.parent, target_is_directory=True)
        output = canonical
    elif case == "alias_symlink_to_valid_parent":
        alias = tmp_path / "valid-parent-alias"
        os.symlink(canonical.parent, alias, target_is_directory=True)
        output = alias / dossier.REVIEW_UNIT_ID
    elif case == "symlinked_state_root":
        state_alias = tmp_path / "state-alias"
        os.symlink(state, state_alias, target_is_directory=True)
        state_argument = state_alias
        output = state_alias / dossier.DOSSIER_RELATIVE
    elif case == "relative_output_path":
        output = Path(os.path.relpath(canonical, ROOT))
    else:
        state_argument = Path(os.path.relpath(state, ROOT))
        output = canonical
    with pytest.raises(ValueError, match=dossier.ERROR):
        materializer._materialize_dossier(
            repo_root=ROOT,
            state_root=state_argument,
            output_dir=output,
            payloads=built,
        )
    command = (
        sys.executable,
        "-B",
        str(SCRIPT),
        "--repo-root",
        str(ROOT),
        "--state-root",
        str(state_argument),
        "--output-dir",
        str(output),
    )
    completed = subprocess.run(
        command,
        cwd=ROOT,
        check=False,
        capture_output=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    assert completed.returncode == 1
    assert completed.stdout == b""
    assert dossier.ERROR.encode("ascii") in completed.stderr
    assert not os.path.lexists(canonical)
    assert marker.read_bytes() == b"preserve\n"
    assert _residue_counts(canonical) == {"temp": 0, "probe": 0, "backup": 0}


@pytest.mark.parametrize("name", dossier.COPIED_FILES)
def test_copied_file_drift_fails_closed(tmp_path: Path, built: dict[str, bytes], name: str) -> None:
    state, output = _materialize(tmp_path, built)
    (output / name).write_bytes((output / name).read_bytes() + b"drift\n")
    with pytest.raises(ValueError, match=dossier.ERROR):
        materializer._check_dossier(repo_root=ROOT, state_root=state, output_dir=output)


@pytest.mark.parametrize("name", (dossier.SUMMARY_FILE, dossier.QUESTIONNAIRE_FILE, dossier.MANIFEST_FILE))
def test_generated_file_drift_fails_closed(tmp_path: Path, built: dict[str, bytes], name: str) -> None:
    state, output = _materialize(tmp_path, built)
    (output / name).write_bytes((output / name).read_bytes() + b"drift\n")
    with pytest.raises(ValueError, match=dossier.ERROR):
        materializer._check_dossier(repo_root=ROOT, state_root=state, output_dir=output)


def _assert_formal_candidate_identity(
    facts: Mapping[str, object], formal_candidate: str, *, published: bool,
) -> None:
    assert re.fullmatch(r"[0-9a-f]{40}", formal_candidate)
    commits = facts["path_commits"]
    assert isinstance(commits, list) and len(commits) == 1
    commit = commits[0]
    assert commit["commit"] == formal_candidate
    assert commit["parents"] == [dossier.BASE_COMMIT]
    assert commit["subject"] == dossier.FORMAL_COMMIT_SUBJECT
    assert commit["changed_paths"] == dossier.CANDIDATE_PATHS
    assert commit["changed_statuses"] == {
        path: "A" for path in dossier.CANDIDATE_PATHS
    }
    assert commit["path_modes"] == {
        path: "100644" for path in dossier.CANDIDATE_PATHS
    }
    assert commit["ancestor_head"] is True
    assert commit["ancestor_origin"] is published
    for path in dossier.CANDIDATE_PATHS:
        blob = commit["path_blobs"][path]
        assert facts["live_paths"][path] == {
            "tracked": True,
            "mode": "100644",
            "index_blob": blob,
            "blob": blob,
        }


def test_current_repository_matches_current_lifecycle() -> None:
    facts = dossier._collect_lifecycle(ROOT)
    lifecycle = dossier._derive_lifecycle(facts)
    profile = lifecycle["lifecycle_profile"]
    assert profile in {
        "transformation_human_review_dossier_precommit_candidate",
        "transformation_human_review_dossier_committed_unpushed",
        "transformation_human_review_dossier_published_successor",
    }
    assert facts["branch"] == dossier.BRANCH == "main"
    assert facts["base_ancestor_head"] is True
    assert facts["base_ancestor_origin"] is True
    if profile == "transformation_human_review_dossier_precommit_candidate":
        assert facts["head"] == facts["origin"] == dossier.BASE_COMMIT
        assert (facts["ahead"], facts["behind"]) == (0, 0)
        assert facts["untracked"] == dossier.CANDIDATE_PATHS
        assert lifecycle["formal_candidate_commit"] == ""
        assert facts["tracked"] == facts["staged"] == ()
        assert all(
            facts["live_paths"][path]["tracked"] is False
            for path in dossier.CANDIDATE_PATHS
        )
        return
    formal_candidate = lifecycle["formal_candidate_commit"]
    candidate_set = set(dossier.CANDIDATE_PATHS)
    assert candidate_set.isdisjoint(facts["tracked"])
    assert candidate_set.isdisjoint(facts["staged"])
    assert candidate_set.isdisjoint(facts["untracked"])
    if profile == "transformation_human_review_dossier_committed_unpushed":
        assert facts["head"] == formal_candidate
        assert facts["origin"] == dossier.BASE_COMMIT
        assert (facts["ahead"], facts["behind"]) == (1, 0)
        _assert_formal_candidate_identity(
            facts, formal_candidate, published=False
        )
        return
    _assert_formal_candidate_identity(facts, formal_candidate, published=True)


def test_lifecycle_exact3_in_base_anchored_temporary_git(tmp_path: Path) -> None:
    repository = tmp_path / ROOT.name
    env = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": "src",
    }
    node = (
        f"{dossier.TEST_PATH}::"
        "test_current_repository_matches_current_lifecycle"
    )
    try:
        subprocess.run(
            (
                "git", "clone", "--no-hardlinks", "--quiet", str(ROOT),
                str(repository),
            ),
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

        def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
            return subprocess.run(
                ("git", *args),
                cwd=repository,
                check=check,
                capture_output=True,
            )

        def run_lifecycle_node() -> None:
            completed = subprocess.run(
                (
                    sys.executable,
                    "-B",
                    "-m",
                    "pytest",
                    "-q",
                    "-p",
                    "no:cacheprovider",
                    node,
                ),
                cwd=repository,
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            assert completed.returncode == 0, completed.stdout + completed.stderr
            assert "1 passed" in completed.stdout

        git("checkout", "-B", "main", dossier.BASE_COMMIT)
        git("update-ref", "refs/remotes/origin/main", dossier.BASE_COMMIT)
        for relative in dossier.CANDIDATE_PATHS:
            assert git(
                "cat-file", "-e", f"{dossier.BASE_COMMIT}:{relative}",
                check=False,
            ).returncode != 0
            target = repository / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
            os.chmod(target, 0o644)
        for relative in dossier.CONTROLLED_REVIEW_SHA256:
            os.chmod(repository / relative, 0o644)
        run_lifecycle_node()

        git("add", *dossier.CANDIDATE_PATHS)
        subprocess.run(
            (
                "git",
                "-c",
                "user.name=CovaPIE Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "-m",
                dossier.FORMAL_COMMIT_SUBJECT,
            ),
            cwd=repository,
            check=True,
            capture_output=True,
        )
        formal = git("rev-parse", "HEAD").stdout.decode("utf-8").strip()
        run_lifecycle_node()
        for relative in dossier.CANDIDATE_PATHS:
            formal_blob = git("rev-parse", f"{formal}:{relative}").stdout.decode().strip()
            index_blob = git("ls-files", "--stage", "--", relative).stdout.decode().split()[1]
            live_blob = git("hash-object", "--no-filters", "--", relative).stdout.decode().strip()
            assert formal_blob == index_blob == live_blob

        unrelated = "UNRELATED_TRANSFORMATION_DOSSIER_SUCCESSOR.txt"
        git("update-ref", "refs/remotes/origin/main", formal)
        (repository / unrelated).write_text(
            "unrelated successor\n", encoding="utf-8"
        )
        os.chmod(repository / unrelated, 0o644)
        git("add", unrelated)
        subprocess.run(
            (
                "git",
                "-c",
                "user.name=CovaPIE Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "-m",
                "unrelated transformation dossier successor",
            ),
            cwd=repository,
            check=True,
            capture_output=True,
        )
        successor = git("rev-parse", "HEAD").stdout.decode().strip()
        changed = git(
            "diff-tree", "--root", "--no-commit-id", "--name-only", "-r",
            successor,
        ).stdout.decode().splitlines()
        assert changed == [unrelated]
        git("update-ref", "refs/remotes/origin/main", successor)
        run_lifecycle_node()
    finally:
        if repository.exists():
            shutil.rmtree(repository)
    assert not os.path.lexists(repository)


def test_candidate_exact4_safety() -> None:
    assert len(dossier.CANDIDATE_PATHS) == 4
    protected = (
        "data/raw/",
        "checkpoints/",
        "equivariant_diffusion/",
        "lightning_modules.py",
        "dataset.py",
        "data/prepare_crossdocked.py",
    )
    forbidden = (
        ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip",
        ".tgz", ".npz", ".tmp", ".part",
    )
    for relative in dossier.CANDIDATE_PATHS:
        path = ROOT / relative
        metadata = path.lstat()
        payload = path.read_bytes()
        assert stat.S_ISREG(metadata.st_mode) and not path.is_symlink()
        assert stat.S_IMODE(metadata.st_mode) == 0o644
        assert len(payload) < 1024 * 1024
        assert not payload.startswith(b"\xef\xbb\xbf") and b"\x00" not in payload
        payload.decode("utf-8")
        assert all(
            not line.endswith((b" ", b"\t")) for line in payload.splitlines()
        )
        assert not relative.startswith(protected)
        assert not relative.endswith(forbidden)
