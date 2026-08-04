from __future__ import annotations

import copy
import csv
import importlib.util
import inspect
import io
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import covalent_ext.covapie_current11_reaction_family_and_warhead_rule_approval_review_package_v1 as review  # noqa: E402


SCRIPT_PATH = ROOT / "scripts/materialize_covapie_current11_reaction_family_and_warhead_rule_approval_review_package_v1.py"
SPEC = importlib.util.spec_from_file_location("review_materializer_v1", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
materializer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(materializer)


def _csv_rows(payload: bytes) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    return tuple(reader.fieldnames or ()), list(reader)


@pytest.fixture(scope="module")
def built() -> tuple[dict[str, bytes], dict[str, object], dict[str, object]]:
    return review._build_for_validation(ROOT, validate_candidate=True)


def _temporary_state_root(tmp_path: Path) -> tuple[Path, Path]:
    state_root = tmp_path / "covapie-state"
    parent = state_root / "manual-review"
    parent.mkdir(parents=True)
    output = parent / review.WORKSPACE_NAME
    return state_root, output


def test_builder_is_keyword_only_deterministic_exact5_and_metadata_only(
    built: tuple[dict[str, bytes], dict[str, object], dict[str, object]],
) -> None:
    first = review.build_covapie_current11_reaction_family_and_warhead_rule_approval_review_package_v1(
        repo_root=ROOT,
    )
    second = review.build_covapie_current11_reaction_family_and_warhead_rule_approval_review_package_v1(
        repo_root=ROOT,
    )
    assert first == second == built[0]
    assert tuple(first) == review.WORKSPACE_FILES
    assert all(isinstance(payload, bytes) and 0 < len(payload) < 1024 * 1024 for payload in first.values())
    assert all(not payload.startswith(b"\xef\xbb\xbf") and b"\x00" not in payload for payload in first.values())
    assert first["family_rule_approval_worklist.csv"].endswith(b"\n")
    assert not first["family_rule_approval_worklist.csv"].endswith(b"\n\n")
    assert first["sample_support_evidence.csv"].endswith(b"\n")
    with pytest.raises(TypeError):
        review.build_covapie_current11_reaction_family_and_warhead_rule_approval_review_package_v1(ROOT)  # type: ignore[misc]
    module_source = (ROOT / review.CANDIDATE_PATHS[-2]).read_text(encoding="utf-8")
    assert "import torch" not in module_source.lower()
    assert "import rdkit" not in module_source.lower()


def test_exact7_review_units_and_sample_counts_are_derived(
    built: tuple[dict[str, bytes], dict[str, object], dict[str, object]],
) -> None:
    state = built[1]
    units = state["review_units"]
    assert isinstance(units, list) and len(units) == 7
    assert [row["warhead_rule_id"] for row in units] == sorted(row["warhead_rule_id"] for row in units)
    assert [row["sample_count"] for row in units] == [2, 2, 1, 3, 1, 1, 1]
    assert sum(row["sample_count"] for row in units) == 11
    assert len({row["reaction_family_id"] for row in units}) == 7


def test_exact11_sample_support_maps_each_sample_once(
    built: tuple[dict[str, bytes], dict[str, object], dict[str, object]],
) -> None:
    rows = built[1]["sample_support"]
    assert isinstance(rows, list) and len(rows) == 11
    assert len({row["sample_index_row_id"] for row in rows}) == 11
    assert set(row["effective_boundary_cardinality"] for row in rows) == {1, 2}
    assert sum(row["effective_boundary_cardinality"] == 1 for row in rows) == 6
    assert sum(row["effective_boundary_cardinality"] == 2 for row in rows) == 5
    assert all(row["sample_supports_candidate_identity"] == "true" for row in rows)
    assert all(row["sample_attests_full_family_or_rule_semantics"] == "false" for row in rows)


def test_all_human_fields_are_blank_and_decision_vocabularies_are_closed(
    built: tuple[dict[str, bytes], dict[str, object], dict[str, object]],
) -> None:
    fields, rows = _csv_rows(built[0]["family_rule_approval_worklist.csv"])
    assert fields == review.WORKLIST_FIELDS
    assert len(rows) == 7
    assert all(row[field] == "" for row in rows for field in review.HUMAN_FIELDS)
    assert review.FAMILY_DECISIONS == (
        "approve_reaction_family_identity", "revise_reaction_family_identity",
        "quarantine_reaction_family",
    )
    assert review.RULE_DECISIONS == (
        "approve_complete_warhead_rule", "revise_warhead_rule",
        "quarantine_warhead_rule",
    )


def test_candidate_graph_is_separated_from_approved_pattern(
    built: tuple[dict[str, bytes], dict[str, object], dict[str, object]],
) -> None:
    evidence = json.loads(built[0]["family_rule_candidate_evidence.json"])
    _fields, worklist = _csv_rows(built[0]["family_rule_approval_worklist.csv"])
    assert len(evidence) == 7
    assert all(row["evidence_status"] == "candidate_supporting_evidence_only" for row in evidence)
    assert all(row["approved_authority"] is False for row in evidence)
    assert all(row["current_approval_state"]["candidate_local_graph_is_approved_structural_pattern"] is False for row in evidence)
    assert all(row["approved_warhead_smarts_currently_available"] == "false" for row in worklist)
    assert all(row["formal_equivalent_structural_contract_currently_available"] == "false" for row in worklist)
    assert all(row["reviewed_warhead_smarts"] == "" for row in worklist)


def test_repository_contract_artifacts_and_failure_registry(
    built: tuple[dict[str, bytes], dict[str, object], dict[str, object]],
) -> None:
    review._validate_repository_contract_artifacts(ROOT, built[1])
    failure_payload = (ROOT / review.FAILURE_MATRIX_PATH).read_bytes()
    rows = review._strict_csv(failure_payload, review.FAILURE_MATRIX_COLUMNS)
    assert len(rows) == len(review.FAILURE_SPECS) == 49
    assert [row["case_id"] for row in rows] == [f"X{number:02d}" for number in range(1, 50)]
    assert all(row["fails_closed"] == "true" and row["verified"] == "true" for row in rows)


def _object_directories(parent: Path) -> list[Path]:
    return sorted(parent.glob(f"{review.OBJECT_DIRECTORY_PREFIX}*"))


def _exercise_publication_failure(
    case_id: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    payloads: dict[str, bytes],
) -> None:
    state_root, output = _temporary_state_root(tmp_path)
    parent = output.parent
    if case_id == "X31":
        output.mkdir()
        with pytest.raises(FileExistsError, match=review.ERROR):
            materializer._materialize_review_workspace(
                repo_root=ROOT, state_root=state_root, output_dir=output,
                payloads=payloads,
            )
        assert output.is_dir()
    elif case_id == "X32":
        competitor = tmp_path / "competitor"
        competitor.mkdir()
        output.symlink_to(competitor, target_is_directory=True)
        with pytest.raises(FileExistsError, match=review.ERROR):
            materializer._materialize_review_workspace(
                repo_root=ROOT, state_root=state_root, output_dir=output,
                payloads=payloads,
            )
        assert output.is_symlink() and competitor.is_dir()
    elif case_id == "X33":
        outside = tmp_path / review.WORKSPACE_NAME
        with pytest.raises(ValueError, match=review.ERROR):
            materializer._materialize_review_workspace(
                repo_root=ROOT, state_root=state_root, output_dir=outside,
                payloads=payloads,
            )
        assert not outside.exists()
    elif case_id == "X34":
        original = materializer._write_payload
        count = 0

        def fail_second(path: Path, payload: bytes) -> tuple[int, int]:
            nonlocal count
            count += 1
            if count == 2:
                raise OSError("injected write failure")
            return original(path, payload)

        monkeypatch.setattr(materializer, "_write_payload", fail_second)
        with pytest.raises(OSError, match="injected write failure"):
            materializer._materialize_review_workspace(
                repo_root=ROOT, state_root=state_root, output_dir=output,
                payloads=payloads,
            )
        assert not os.path.lexists(output)
        assert not _object_directories(parent)
    elif case_id == "X35":
        def fail_symlink(
            source: str, destination: Path, *, target_is_directory: bool,
        ) -> None:
            raise OSError("injected symlink failure")

        monkeypatch.setattr(materializer.os, "symlink", fail_symlink)
        with pytest.raises(OSError, match="injected symlink failure"):
            materializer._materialize_review_workspace(
                repo_root=ROOT, state_root=state_root, output_dir=output,
                payloads=payloads,
        )
        assert not os.path.lexists(output)
        assert not _object_directories(parent)
    elif case_id == "X36":
        original = materializer._write_payload
        first_path: Path | None = None
        count = 0

        def replace_then_fail(path: Path, payload: bytes) -> tuple[int, int]:
            nonlocal first_path, count
            count += 1
            if count == 1:
                first_path = path
                return original(path, payload)
            assert first_path is not None
            first_path.rename(tmp_path / "parked-created-file")
            first_path.write_bytes(b"competitor\n")
            os.chmod(first_path, 0o644)
            raise OSError("trigger cleanup")

        monkeypatch.setattr(materializer, "_write_payload", replace_then_fail)
        with pytest.raises(ValueError, match=review.ERROR):
            materializer._materialize_review_workspace(
                repo_root=ROOT, state_root=state_root, output_dir=output,
                payloads=payloads,
            )
        leftovers = _object_directories(parent)
        assert len(leftovers) == 1
        assert (leftovers[0] / "README.md").read_bytes() == b"competitor\n"
        assert not os.path.lexists(output)
    elif case_id == "X37":
        parked = tmp_path / "parked-original-object"

        def replace_object_inode(
            source: str, destination: Path, *, target_is_directory: bool,
        ) -> None:
            object_directory = Path(destination).parent / source
            object_directory.rename(parked)
            object_directory.mkdir()
            raise OSError("trigger inode-safe cleanup")

        monkeypatch.setattr(materializer.os, "symlink", replace_object_inode)
        with pytest.raises(ValueError, match=review.ERROR):
            materializer._materialize_review_workspace(
                repo_root=ROOT, state_root=state_root, output_dir=output,
                payloads=payloads,
            )
        replacements = _object_directories(parent)
        assert len(replacements) == 1 and replacements[0].is_dir()
        assert parked.is_dir() and len(tuple(parked.iterdir())) == 5
        assert not os.path.lexists(output)
    elif case_id == "X38":
        materializer._materialize_review_workspace(
            repo_root=ROOT, state_root=state_root, output_dir=output,
            payloads=payloads,
        )
        object_directory = output.parent / os.readlink(output)
        os.chmod(object_directory / "README.md", 0o600)
        with pytest.raises(ValueError, match=review.ERROR):
            materializer._validate_canonical_workspace_entry_v1(output, payloads)
        assert stat.S_IMODE((object_directory / "README.md").stat().st_mode) == 0o600
    elif case_id in {"X45", "X46", "X47", "X48"}:
        materializer._materialize_review_workspace(
            repo_root=ROOT, state_root=state_root, output_dir=output,
            payloads=payloads,
        )
        original_target = os.readlink(output)
        original_object = parent / original_target
        materializer._validate_canonical_workspace_entry_v1(output, payloads)
        if case_id == "X45":
            output.unlink()
            output.symlink_to("../escape", target_is_directory=True)
            assert os.readlink(output) != original_target
        elif case_id == "X46":
            output.unlink()
            output.symlink_to("wrong-object", target_is_directory=True)
            assert os.readlink(output) != original_target
        elif case_id == "X47":
            parked = tmp_path / "parked-broken-object"
            original_object.rename(parked)
            assert output.is_symlink() and not output.exists()
        else:
            parked = tmp_path / "parked-valid-object"
            original_object.rename(parked)
            original_object.write_bytes(b"competitor object type\n")
            assert original_object.is_file()
        with pytest.raises(ValueError, match=review.ERROR):
            materializer._validate_canonical_workspace_entry_v1(output, payloads)
    else:
        raise AssertionError(case_id)


@pytest.mark.parametrize("case_id", [f"X{number:02d}" for number in range(1, 50)])
def test_failure_matrix_case_fails_closed(
    case_id: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    built: tuple[dict[str, bytes], dict[str, object], dict[str, object]],
) -> None:
    payloads, state, response = built
    if case_id in (
        {f"X{number:02d}" for number in range(31, 39)}
        | {f"X{number:02d}" for number in range(45, 49)}
    ):
        _exercise_publication_failure(case_id, tmp_path, monkeypatch, payloads)
        return
    baseline, validator = review._failure_baseline(case_id, state, payloads, response)
    validator(copy.deepcopy(baseline))
    mutated = copy.deepcopy(baseline)
    review._apply_failure_mutation(case_id, mutated)
    assert mutated != baseline
    with pytest.raises(ValueError, match=review.ERROR):
        validator(mutated)


def test_relative_symlink_publication_success_and_exact_tree(
    tmp_path: Path,
    built: tuple[dict[str, bytes], dict[str, object], dict[str, object]],
) -> None:
    state_root, output = _temporary_state_root(tmp_path)
    report = materializer._materialize_review_workspace(
        repo_root=ROOT, state_root=state_root, output_dir=output,
        payloads=built[0],
    )
    assert report["file_count"] == 5
    assert report["publication_scheme"] == review.PUBLICATION_SCHEME
    assert report["canonical_entry_type"] == "symlink"
    assert output.is_symlink()
    relative_target = os.readlink(output)
    assert "/" not in relative_target and ".." not in relative_target
    assert relative_target.startswith(review.OBJECT_DIRECTORY_PREFIX)
    object_directory = output.parent / relative_target
    assert stat.S_IMODE(object_directory.lstat().st_mode) == 0o755
    assert all(stat.S_ISREG(path.lstat().st_mode) and stat.S_IMODE(path.lstat().st_mode) == 0o644 for path in object_directory.iterdir())
    assert not list(output.parent.glob(f".{review.WORKSPACE_NAME}.tmp-*"))


def test_existing_target_protection_preserves_human_edit(
    tmp_path: Path,
    built: tuple[dict[str, bytes], dict[str, object], dict[str, object]],
) -> None:
    state_root, output = _temporary_state_root(tmp_path)
    output.mkdir()
    human = output / "human-edit.txt"
    human.write_text("preserve me\n", encoding="utf-8")
    with pytest.raises(FileExistsError, match=review.ERROR):
        materializer._materialize_review_workspace(
            repo_root=ROOT, state_root=state_root, output_dir=output,
            payloads=built[0],
        )
    assert human.read_text(encoding="utf-8") == "preserve me\n"


def test_existing_arbitrary_symlink_is_preserved(
    tmp_path: Path,
    built: tuple[dict[str, bytes], dict[str, object], dict[str, object]],
) -> None:
    state_root, output = _temporary_state_root(tmp_path)
    competitor = tmp_path / "competitor-directory"
    competitor.mkdir()
    output.symlink_to(competitor, target_is_directory=True)
    identity = (output.lstat().st_dev, output.lstat().st_ino)
    with pytest.raises(FileExistsError, match=review.ERROR):
        materializer._materialize_review_workspace(
            repo_root=ROOT, state_root=state_root, output_dir=output,
            payloads=built[0],
        )
    assert (output.lstat().st_dev, output.lstat().st_ino) == identity
    assert output.resolve() == competitor
    assert not _object_directories(output.parent)


def test_symlink_eexist_race_preserves_competitor_inode_and_cleans_object(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    built: tuple[dict[str, bytes], dict[str, object], dict[str, object]],
) -> None:
    state_root, output = _temporary_state_root(tmp_path)
    original_symlink = materializer.os.symlink
    competitor_identity: tuple[int, int] | None = None

    def create_competitor_then_publish(
        source: str, destination: Path, *, target_is_directory: bool,
    ) -> None:
        nonlocal competitor_identity
        Path(destination).mkdir()
        marker = Path(destination) / "human-edit.txt"
        marker.write_text("preserve\n", encoding="utf-8")
        metadata = Path(destination).lstat()
        competitor_identity = (metadata.st_dev, metadata.st_ino)
        original_symlink(
            source, destination, target_is_directory=target_is_directory,
        )

    monkeypatch.setattr(materializer.os, "symlink", create_competitor_then_publish)
    with pytest.raises(FileExistsError):
        materializer._materialize_review_workspace(
            repo_root=ROOT, state_root=state_root, output_dir=output,
            payloads=built[0],
        )
    assert competitor_identity is not None
    assert (output.lstat().st_dev, output.lstat().st_ino) == competitor_identity
    assert (output / "human-edit.txt").read_text(encoding="utf-8") == "preserve\n"
    assert not _object_directories(output.parent)


def test_temp_state_checker_twice_is_read_only_and_byte_identical(
    tmp_path: Path,
    built: tuple[dict[str, bytes], dict[str, object], dict[str, object]],
) -> None:
    state_root, output = _temporary_state_root(tmp_path)
    materializer._materialize_review_workspace(
        repo_root=ROOT, state_root=state_root, output_dir=output,
        payloads=built[0],
    )
    command = (
        sys.executable, str(SCRIPT_PATH), "--repo-root", str(ROOT),
        "--state-root", str(state_root), "--check",
    )
    first = subprocess.run(command, cwd=ROOT, capture_output=True, check=False)
    second = subprocess.run(command, cwd=ROOT, capture_output=True, check=False)
    assert (first.returncode, second.returncode) == (0, 0)
    assert first.stderr == second.stderr == b""
    assert first.stdout == second.stdout
    report = json.loads(first.stdout)
    assert report["publication_scheme"] == review.PUBLICATION_SCHEME
    assert report["canonical_entry_type"] == "symlink"


def _synthetic_lifecycle_witnesses() -> tuple[dict[str, object], ...]:
    precommit = review._derive_lifecycle(review._synthetic_lifecycle_facts("review_package_precommit_candidate"))
    committed_facts = review._synthetic_lifecycle_facts("review_package_committed_unpushed")
    committed = review._derive_lifecycle(copy.deepcopy(committed_facts))
    published_facts = copy.deepcopy(committed_facts)
    published_facts["origin"] = published_facts["path_commits"][0]["commit"]
    published_facts["ahead"] = 0
    published_facts["path_commits"][0]["ancestor_origin"] = True
    published = review._derive_lifecycle(published_facts)
    return precommit, committed, published


def test_static_exact8_lifecycle_schema_for_exact3_profiles() -> None:
    witnesses = _synthetic_lifecycle_witnesses()
    assert tuple(witness["review_package_lifecycle_profile"] for witness in witnesses) == (
        "review_package_precommit_candidate",
        "review_package_committed_unpushed",
        "review_package_published_successor",
    )
    for witness in witnesses:
        assert tuple(witness) == review._RESPONSE_LIFECYCLE_FIELDS
        review._validate_lifecycle_witness(witness)
    invalid = dict(witnesses[0])
    invalid["unknown"] = False
    with pytest.raises(ValueError, match=review.ERROR):
        review._validate_lifecycle_witness(invalid)


def test_branch_aware_live_tree_lifecycle_and_response_external_witness(
    built: tuple[dict[str, bytes], dict[str, object], dict[str, object]],
) -> None:
    facts = review._collect_lifecycle(ROOT)
    lifecycle = review._derive_lifecycle(facts)
    profile = lifecycle["review_package_lifecycle_profile"]
    if profile == "review_package_precommit_candidate":
        assert facts["head"] == facts["origin"] == review.BASE_COMMIT
        assert (facts["ahead"], facts["behind"]) == (0, 0)
        assert not facts["tracked"] and not facts["staged"]
        assert facts["untracked"] == review.CANDIDATE_PATHS
        assert facts["porcelain"] == tuple(f"?? {path}" for path in review.CANDIDATE_PATHS)
    elif profile == "review_package_committed_unpushed":
        assert facts["origin"] == review.BASE_COMMIT
        assert (facts["ahead"], facts["behind"]) == (1, 0)
        assert not facts["tracked"] and not facts["staged"] and not facts["untracked"]
        assert not facts["porcelain"]
    elif profile == "review_package_published_successor":
        assert facts["path_commits"][0]["ancestor_head"] is True
        assert facts["path_commits"][0]["ancestor_origin"] is True
        assert all(facts["live_paths"][path]["blob"] == facts["path_commits"][0]["path_blobs"][path] for path in review.CANDIDATE_PATHS)
    else:
        pytest.fail(f"unknown lifecycle profile: {profile}")
    external = {field: lifecycle[field] for field in review._RESPONSE_LIFECYCLE_FIELDS}
    workspace_hash_witness = review._workspace_file_sha256_witness_v1(
        built[0],
    )
    review._validate_response(
        built[2],
        expected_lifecycle=external,
        expected_workspace_file_sha256=workspace_hash_witness,
    )
    assert len(built[2]["response_sha256"]) == 64


def test_complete_targeted_actual_git_survivability_exact3(tmp_path: Path) -> None:
    repository = tmp_path / "lifecycle-repository"
    subprocess.run(
        ("git", "clone", "--no-hardlinks", "--quiet", str(ROOT), str(repository)),
        check=True, capture_output=True,
    )
    subprocess.run(
        ("git", "remote", "set-url", "origin", review.REMOTE),
        cwd=repository, check=True, capture_output=True,
    )
    cloned_initial_head = subprocess.run(
        ("git", "rev-parse", "HEAD"), cwd=repository, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    assert len(cloned_initial_head) == 40
    assert set(cloned_initial_head) <= set("0123456789abcdef")

    # The lifecycle fixture must be anchored to BASE_COMMIT because ROOT may
    # already contain the formal review-package commit or a later successor.
    subprocess.run(
        ("git", "checkout", "-B", review.BRANCH, review.BASE_COMMIT),
        cwd=repository, check=True, capture_output=True,
    )
    subprocess.run(
        ("git", "update-ref", "refs/remotes/origin/main", review.BASE_COMMIT),
        cwd=repository, check=True, capture_output=True,
    )
    resolved_test_base_head = subprocess.run(
        ("git", "rev-parse", "HEAD"), cwd=repository, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    resolved_test_origin = subprocess.run(
        ("git", "rev-parse", "refs/remotes/origin/main"), cwd=repository,
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    resolved_test_branch = subprocess.run(
        ("git", "branch", "--show-current"), cwd=repository, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    assert resolved_test_base_head == review.BASE_COMMIT
    assert resolved_test_origin == review.BASE_COMMIT
    assert resolved_test_branch == review.BRANCH
    for relative in review.CANDIDATE_PATHS:
        absent_at_base = subprocess.run(
            ("git", "cat-file", "-e", f"{review.BASE_COMMIT}:{relative}"),
            cwd=repository, check=False, capture_output=True,
        )
        assert absent_at_base.returncode != 0

    for relative in review.CANDIDATE_PATHS:
        destination = repository / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
        os.chmod(destination, 0o644)
    precommit_facts = review._collect_lifecycle(repository)
    assert precommit_facts["head"] == review.BASE_COMMIT
    assert precommit_facts["origin"] == review.BASE_COMMIT
    assert (precommit_facts["ahead"], precommit_facts["behind"]) == (0, 0)
    assert not precommit_facts["tracked"] and not precommit_facts["staged"]
    assert precommit_facts["untracked"] == review.CANDIDATE_PATHS
    assert precommit_facts["porcelain"] == tuple(
        f"?? {relative}" for relative in review.CANDIDATE_PATHS
    )
    assert all(
        record["tracked"] is False and record["mode"] == "100644"
        for record in precommit_facts["live_paths"].values()
    )
    precommit = review._derive_lifecycle(precommit_facts)
    assert precommit["review_package_lifecycle_profile"] == "review_package_precommit_candidate"

    subprocess.run(
        ("git", "add", "--", *review.CANDIDATE_PATHS),
        cwd=repository, check=True, capture_output=True,
    )
    subprocess.run(
        (
            "git", "-c", "user.name=CovaPIE Test",
            "-c", "user.email=covapie-test@example.invalid", "commit", "-m",
            review.FORMAL_COMMIT_SUBJECT,
        ),
        cwd=repository, check=True, capture_output=True,
    )
    committed_facts = review._collect_lifecycle(repository)
    assert committed_facts["origin"] == review.BASE_COMMIT
    assert (committed_facts["ahead"], committed_facts["behind"]) == (1, 0)
    assert len(committed_facts["path_commits"]) == 1
    formal_facts = committed_facts["path_commits"][0]
    assert formal_facts["parents"] == [review.BASE_COMMIT]
    assert formal_facts["subject"] == review.FORMAL_COMMIT_SUBJECT
    assert formal_facts["changed_paths"] == review.CANDIDATE_PATHS
    assert formal_facts["changed_statuses"] == {
        relative: "A" for relative in review.CANDIDATE_PATHS
    }
    assert formal_facts["path_modes"] == {
        relative: "100644" for relative in review.CANDIDATE_PATHS
    }
    committed = review._derive_lifecycle(committed_facts)
    assert committed["review_package_lifecycle_profile"] == "review_package_committed_unpushed"
    formal_commit = committed["review_package_commit"]
    assert committed_facts["head"] == formal_commit
    assert formal_commit != review.BASE_COMMIT

    subprocess.run(
        ("git", "update-ref", "refs/remotes/origin/main", str(formal_commit)),
        cwd=repository, check=True, capture_output=True,
    )
    unrelated = repository / "UNRELATED_LIFECYCLE_WITNESS.txt"
    unrelated.write_text("unrelated successor\n", encoding="utf-8")
    subprocess.run(
        ("git", "add", "--", unrelated.name),
        cwd=repository, check=True, capture_output=True,
    )
    subprocess.run(
        (
            "git", "-c", "user.name=CovaPIE Test",
            "-c", "user.email=covapie-test@example.invalid", "commit", "-m",
            "add unrelated lifecycle witness",
        ),
        cwd=repository, check=True, capture_output=True,
    )
    successor = subprocess.run(
        ("git", "rev-parse", "HEAD"), cwd=repository, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    subprocess.run(
        ("git", "update-ref", "refs/remotes/origin/main", successor),
        cwd=repository, check=True, capture_output=True,
    )
    successor_paths = subprocess.run(
        ("git", "diff-tree", "--no-commit-id", "--name-only", "-r", successor),
        cwd=repository, check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    assert successor_paths == [unrelated.name]
    assert subprocess.run(
        ("git", "merge-base", "--is-ancestor", str(formal_commit), "HEAD"),
        cwd=repository, check=False, capture_output=True,
    ).returncode == 0
    assert subprocess.run(
        (
            "git", "merge-base", "--is-ancestor", str(formal_commit),
            "refs/remotes/origin/main",
        ),
        cwd=repository, check=False, capture_output=True,
    ).returncode == 0
    published_facts = review._collect_lifecycle(repository)
    assert published_facts["head"] == successor
    assert published_facts["origin"] == successor
    assert len(published_facts["path_commits"]) == 1
    published_formal_facts = published_facts["path_commits"][0]
    assert published_formal_facts["commit"] == formal_commit
    assert all(
        published_facts["live_paths"][relative] == {
            "tracked": True,
            "mode": "100644",
            "index_blob": published_formal_facts["path_blobs"][relative],
            "blob": published_formal_facts["path_blobs"][relative],
        }
        for relative in review.CANDIDATE_PATHS
    )
    published = review._derive_lifecycle(published_facts)
    assert published["review_package_lifecycle_profile"] == "review_package_published_successor"
    assert published["review_package_commit"] == formal_commit


def test_index_worktree_drift_and_parent_mismatch_fail_closed() -> None:
    committed_facts = review._synthetic_lifecycle_facts("review_package_committed_unpushed")
    drift = copy.deepcopy(committed_facts)
    drift["live_paths"][review.CANDIDATE_PATHS[0]]["blob"] = "f" * 40
    with pytest.raises(ValueError, match=review.ERROR):
        review._derive_lifecycle(drift)
    parent = copy.deepcopy(committed_facts)
    parent["path_commits"][0]["parents"] = ["b" * 40]
    with pytest.raises(ValueError, match=review.ERROR):
        review._derive_lifecycle(parent)


def test_workspace_hash_witness_is_exact_ordered_typed_and_required(
    built: tuple[dict[str, bytes], dict[str, object], dict[str, object]],
) -> None:
    payloads = built[0]
    witness = review._workspace_file_sha256_witness_v1(payloads)
    assert type(witness) is dict
    assert tuple(witness) == review.WORKSPACE_FILES
    assert all(
        type(digest) is str and len(digest) == 64
        and digest == digest.lower()
        and set(digest) <= set("0123456789abcdef")
        for digest in witness.values()
    )
    review._validate_workspace_hash_witness_v1(witness)

    class DictSubclass(dict[str, str]):
        pass

    invalid_witnesses: list[object] = [
        DictSubclass(witness),
        dict(reversed(tuple(witness.items()))),
        {key: value for key, value in witness.items() if key != "README.md"},
        {**witness, "extra.txt": "a" * 64},
        {key: (False if key == "README.md" else value) for key, value in witness.items()},
        {key: (b"a" * 64 if key == "README.md" else value) for key, value in witness.items()},
        {key: ("A" * 64 if key == "README.md" else value) for key, value in witness.items()},
    ]
    for invalid in invalid_witnesses:
        with pytest.raises(ValueError, match=review.ERROR):
            review._validate_workspace_hash_witness_v1(invalid)

    class PayloadDictSubclass(dict[str, bytes]):
        pass

    invalid_payloads: list[object] = [
        PayloadDictSubclass(payloads),
        dict(reversed(tuple(payloads.items()))),
        {key: value for key, value in payloads.items() if key != "README.md"},
        {**payloads, "extra.txt": b"extra\n"},
        {key: (bytearray(value) if key == "README.md" else value) for key, value in payloads.items()},
        {key: (b"" if key == "README.md" else value) for key, value in payloads.items()},
        {key: (b"x" * (1024 * 1024) if key == "README.md" else value) for key, value in payloads.items()},
    ]
    for invalid in invalid_payloads:
        with pytest.raises(ValueError, match=review.ERROR):
            review._workspace_file_sha256_witness_v1(invalid)  # type: ignore[arg-type]

    signature = inspect.signature(review._validate_response)
    parameter = signature.parameters["expected_workspace_file_sha256"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is inspect.Parameter.empty
    lifecycle = {
        field: built[2][field] for field in review._RESPONSE_LIFECYCLE_FIELDS
    }
    with pytest.raises(TypeError):
        review._validate_response(built[2], expected_lifecycle=lifecycle)


def test_workspace_file_sha256_valid_looking_substitution_fails_external_witness(
    built: tuple[dict[str, bytes], dict[str, object], dict[str, object]],
) -> None:
    lifecycle_witness = {
        field: built[2][field] for field in review._RESPONSE_LIFECYCLE_FIELDS
    }
    workspace_hash_witness = review._workspace_file_sha256_witness_v1(
        built[0],
    )
    response = review._build_response(lifecycle_witness, built[0])
    response_hashes = response["workspace_file_sha256"]
    assert isinstance(response_hashes, dict)
    assert response_hashes == workspace_hash_witness
    assert response_hashes is not workspace_hash_witness
    frozen_workspace_hash_witness = copy.deepcopy(workspace_hash_witness)
    replacement = "f" * 64
    assert response_hashes["README.md"] != replacement
    response_hashes["README.md"] = replacement
    assert workspace_hash_witness == frozen_workspace_hash_witness
    review._rehash_response(response)
    with pytest.raises(ValueError, match=review.ERROR):
        review._validate_response(
            response,
            expected_lifecycle=lifecycle_witness,
            expected_workspace_file_sha256=workspace_hash_witness,
        )


@pytest.mark.parametrize(
    "profile,field,value",
    (
        ("published", "origin_main", "b" * 40),
        ("published", "ahead", 3),
        ("published", "behind", 2),
        ("committed", "binding_commit", "b" * 40),
        ("committed", "review_package_commit", "b" * 40),
        ("published", "binding_commit", "b" * 40),
        ("published", "review_package_commit", "b" * 40),
        ("committed", "review_package_commit", review.BASE_COMMIT),
        ("published", "review_package_commit", review.BASE_COMMIT),
        ("published", "ahead", False),
        ("published", "behind", False),
        ("committed", "__extra__", "value"),
        ("committed", "__missing__", "binding_commit"),
    ),
)
def test_response_fixed_schema_exact_types_and_external_witness_fail_closed(
    profile: str,
    field: str,
    value: object,
    built: tuple[dict[str, bytes], dict[str, object], dict[str, object]],
) -> None:
    _precommit, committed, published = _synthetic_lifecycle_witnesses()
    lifecycle = committed if profile == "committed" else published
    response = review._build_response(lifecycle, built[0])
    external_lifecycle = copy.deepcopy(lifecycle)
    external_workspace_hash = review._workspace_file_sha256_witness_v1(
        built[0],
    )
    review._validate_response(
        response,
        expected_lifecycle=external_lifecycle,
        expected_workspace_file_sha256=external_workspace_hash,
    )
    mutated = copy.deepcopy(response)
    if field == "__extra__":
        mutated["extra_response_field"] = value
    elif field == "__missing__":
        del mutated[str(value)]
    else:
        mutated[field] = value
    review._rehash_response(mutated)
    assert mutated != response
    with pytest.raises(ValueError, match=review.ERROR):
        review._validate_response(
            mutated,
            expected_lifecycle=external_lifecycle,
            expected_workspace_file_sha256=external_workspace_hash,
        )


def test_silent_import_has_no_output_or_side_effects() -> None:
    before = subprocess.run(
        ["git", "status", "--porcelain=v1"], cwd=ROOT,
        check=True, capture_output=True,
    ).stdout
    command = (
        "import covalent_ext."
        "covapie_current11_reaction_family_and_warhead_rule_"
        "approval_review_package_v1"
    )
    result = subprocess.run(
        [sys.executable, "-c", command], cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(SRC)},
        check=False, capture_output=True, timeout=30,
    )
    after = subprocess.run(
        ["git", "status", "--porcelain=v1"], cwd=ROOT,
        check=True, capture_output=True,
    ).stdout
    assert result.returncode == 0
    assert result.stdout == result.stderr == b""
    assert before == after
