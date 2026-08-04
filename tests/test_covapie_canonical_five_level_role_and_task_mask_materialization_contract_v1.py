from __future__ import annotations

import ast
import copy
import hashlib
import inspect
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
MODULE_NAME = (
    "covalent_ext."
    "covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1"
)

from covalent_ext import (  # noqa: E402
    covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1
    as subject,
)


ERROR = subject._ERROR


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


@pytest.fixture(scope="module")
def response() -> dict[str, object]:
    return subject.evaluate_covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1(
        repo_root=ROOT,
    )


def _valid_partition() -> dict[str, object]:
    return {
        "ligand_atom_symbols": ("C", "N", "O", "S", "C", "N"),
        "role_id_by_atom": (0, 0, 1, 1, 2, 2),
        "scaffold_indices": (0, 1),
        "linker_indices": (2, 3),
        "warhead_indices": (4, 5),
        "index_space": "retained_heavy_local_index_0based",
    }


def _valid_bundle(task_id: int = 1) -> dict[str, tuple[bool, ...]]:
    return subject._derive_base_masks_v1(
        role_ids=(0, 0, 1, 1, 2, 2),
        task_id=task_id,
        role_valid=(True,) * 6,
        canonical_task_valid=True,
        sample_training_admitted=True,
        seed_mask=(False,) * 6,
        seed_valid=False,
    )


def _validate_bundle(
    bundle: dict[str, tuple[bool, ...]],
    *,
    task_id: int = 1,
    role_valid: tuple[bool, ...] = (True,) * 6,
    task_valid: bool = True,
    admitted: bool = True,
    seed_valid: bool = False,
) -> None:
    subject._validate_mask_bundle_v1(
        bundle=bundle,
        role_ids=(0, 0, 1, 1, 2, 2),
        task_id=task_id,
        role_valid=role_valid,
        canonical_task_valid=task_valid,
        sample_training_admitted=admitted,
        seed_valid=seed_valid,
    )


def test_public_api_keyword_only_silent_and_torch_free() -> None:
    assert subject.__all__ == (
        "evaluate_covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1",
    )
    function = subject.evaluate_covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1
    signature = inspect.signature(function)
    assert tuple(signature.parameters) == ("repo_root",)
    assert signature.parameters["repo_root"].kind is inspect.Parameter.KEYWORD_ONLY
    with pytest.raises(TypeError):
        function(ROOT)  # type: ignore[misc]
    code = (
        "import contextlib,io,sys;"
        "o=io.StringIO();e=io.StringIO();"
        f"\nwith contextlib.redirect_stdout(o),contextlib.redirect_stderr(e): import {MODULE_NAME};"
        "\nassert o.getvalue()=='' and e.getvalue()=='';"
        "\nassert 'torch' not in sys.modules"
    )
    environment = dict(os.environ)
    environment["PYTHONPATH"] = f"{ROOT / 'src'}:{environment.get('PYTHONPATH', '')}"
    completed = subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert (completed.returncode, completed.stdout, completed.stderr) == (0, "", "")


def test_response_order_digest_and_double_evaluation(response: dict[str, object]) -> None:
    assert tuple(response) == subject._RESPONSE_FIELDS
    assert response["response_field_count"] == len(subject._RESPONSE_FIELDS)
    unsigned = {key: response[key] for key in subject._RESPONSE_FIELDS[:-1]}
    assert response["response_sha256"] == hashlib.sha256(_canonical_bytes(unsigned)).hexdigest()
    second = subject.evaluate_covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1(
        repo_root=ROOT,
    )
    assert _canonical_bytes(response) == _canonical_bytes(second)
    subject._validate_response_v1(copy.deepcopy(response))


def test_static_base_identity_candidate_scope_and_evidence(
    response: dict[str, object],
) -> None:
    assert response["repository"] == "fumx2000/DiffSBDD"
    assert response["branch"] == "main"
    assert response["base_head"] == subject._BASE
    assert response["base_head_subject"] == subject._BASE_SUBJECT
    assert response["candidate_paths"] == list(subject._CANDIDATE_PATHS)
    assert len(response["evidence_records"]) == 20
    assert response["evidence_records"][-1]["evidence_id"] == "E20"
    assert response["evidence_records"][-1]["sha256"] == (
        "872ecd0754ff941bee207161a54eecd1dd256d382044c38075b1c8ede89dba3d"
    )
    assert all(record["verified"] is True for record in response["evidence_records"])


def _live_git(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert (completed.returncode, completed.stderr) == (0, "")
    return completed.stdout


def _assert_live_formal_contract_identity(commit: str) -> None:
    assert _live_git("show", "-s", "--format=%s", commit).strip() == (
        subject._CONTRACT_COMMIT_SUBJECT
    )
    assert _live_git("show", "-s", "--format=%P", commit).split() == [subject._BASE]
    status_lines = _live_git(
        "diff-tree", "--root", "--no-commit-id", "--name-status", "-r", commit
    ).splitlines()
    statuses = {}
    for line in status_lines:
        status_code, path = line.split("\t")
        statuses[path] = status_code
    assert tuple(sorted(statuses)) == subject._CANDIDATE_PATHS
    assert statuses == {path: "A" for path in subject._CANDIDATE_PATHS}

    for path in subject._CANDIDATE_PATHS:
        tree_metadata, tree_path = _live_git("ls-tree", commit, "--", path).strip().split(
            "\t", 1
        )
        tree_mode, object_type, commit_blob = tree_metadata.split()
        assert (tree_path, tree_mode, object_type) == (path, "100644", "blob")
        index_metadata, index_path = _live_git(
            "ls-files", "--stage", "--", path
        ).strip().split("\t", 1)
        index_mode, index_blob, stage = index_metadata.split()
        actual_worktree_blob = _live_git(
            "hash-object", "--no-filters", "--", path
        ).strip()
        assert (index_path, index_mode, stage) == (path, "100644", "0")
        assert index_blob == commit_blob
        assert actual_worktree_blob == commit_blob

    assert not _live_git("diff", "--name-only", "--", *subject._CANDIDATE_PATHS)
    assert not _live_git(
        "diff", "--cached", "--name-only", "--", *subject._CANDIDATE_PATHS
    )


def test_live_tree_contract_lifecycle_matches_current_repository_state(
    response: dict[str, object],
) -> None:
    actual_head = _live_git("rev-parse", "HEAD").strip()
    actual_origin = _live_git("rev-parse", "refs/remotes/origin/main").strip()
    actual_ahead, actual_behind = (
        int(value)
        for value in _live_git(
            "rev-list", "--left-right", "--count", "HEAD...refs/remotes/origin/main"
        ).split()
    )
    tracked = tuple(sorted(_live_git("diff", "--name-only").splitlines()))
    staged = tuple(sorted(_live_git("diff", "--cached", "--name-only").splitlines()))
    untracked = tuple(
        sorted(_live_git("ls-files", "--others", "--exclude-standard").splitlines())
    )
    status_lines = tuple(
        sorted(_live_git("status", "--porcelain=v1", "--untracked-files=all").splitlines())
    )
    profile = response["contract_lifecycle_profile"]
    assert response["origin_main"] == actual_origin
    assert (response["ahead"], response["behind"]) == (actual_ahead, actual_behind)

    if profile == "contract_precommit_candidate":
        assert actual_head == actual_origin == subject._BASE
        assert (actual_ahead, actual_behind) == (0, 0)
        assert tracked == staged == ()
        assert untracked == subject._CANDIDATE_PATHS
        assert status_lines == tuple(f"?? {path}" for path in subject._CANDIDATE_PATHS)
        for path in subject._CANDIDATE_PATHS:
            assert not _live_git("ls-files", "--stage", "--", path)
            assert stat.S_IMODE((ROOT / path).lstat().st_mode) == 0o644
        assert response["contract_commit"] is None
        assert response["contract_committed"] is False
        assert response["contract_published"] is False
        assert response["ready_for_contract_commit_review"] is True
    elif profile == "contract_committed_unpushed":
        contract_commit = response["contract_commit"]
        assert type(contract_commit) is str
        assert actual_head == contract_commit
        assert actual_origin == subject._BASE
        assert (actual_ahead, actual_behind) == (1, 0)
        assert tracked == staged == untracked == status_lines == ()
        assert response["contract_committed"] is True
        assert response["contract_published"] is False
        assert response["ready_for_contract_commit_review"] is False
        _assert_live_formal_contract_identity(contract_commit)
    elif profile == "contract_published_successor":
        contract_commit = response["contract_commit"]
        assert type(contract_commit) is str
        for descendant in (actual_head, actual_origin):
            completed = subprocess.run(
                ["git", "merge-base", "--is-ancestor", contract_commit, descendant],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            assert (completed.returncode, completed.stdout, completed.stderr) == (0, "", "")
        assert not set(subject._CANDIDATE_PATHS).intersection(tracked, staged, untracked)
        assert all(line[3:] not in subject._CANDIDATE_PATHS for line in status_lines)
        assert response["contract_committed"] is True
        assert response["contract_published"] is True
        assert response["ready_for_contract_commit_review"] is False
        _assert_live_formal_contract_identity(contract_commit)
    else:
        pytest.fail(f"unknown contract lifecycle profile: {profile!r}")


def test_exact3_role_and_exact5_task_contract(response: dict[str, object]) -> None:
    assert response["canonical_role_vocabulary"] == [
        {"role_id": 0, "semantic_name": "scaffold"},
        {"role_id": 1, "semantic_name": "linker"},
        {"role_id": 2, "semantic_name": "warhead"},
    ]
    tasks = response["canonical_task_truth_table"]
    assert [row["semantic_name"] for row in tasks] == [spec[1] for spec in subject._TASK_SPECS]
    assert tasks[2]["display_alias"] == "B2"
    assert tasks[3] == {
        "task_id": 3,
        "semantic_name": "scaffold_only",
        "display_alias": "B3",
        "generated_primary_roles": ["scaffold"],
        "fixed_primary_roles": ["linker", "warhead"],
    }
    assert tasks[4]["fixed_primary_roles"] == []
    assert response["semantic_long_names_authoritative"] is True
    assert response["display_aliases_runtime_input_allowed"] is False


def test_task_c_base_mask_and_seed_sidecar_are_orthogonal() -> None:
    without_seed = subject._derive_base_masks_v1(
        role_ids=(0, 0, 1, 1, 2, 2),
        task_id=4,
        role_valid=(True,) * 6,
        canonical_task_valid=True,
        sample_training_admitted=True,
        seed_mask=(False,) * 6,
        seed_valid=False,
    )
    with_seed = subject._derive_base_masks_v1(
        role_ids=(0, 0, 1, 1, 2, 2),
        task_id=4,
        role_valid=(True,) * 6,
        canonical_task_valid=True,
        sample_training_admitted=True,
        seed_mask=(True, False, False, False, False, False),
        seed_valid=True,
    )
    for key in ("generation", "fixed", "target", "context", "active_loss"):
        assert with_seed[key] == without_seed[key]
    assert with_seed["generation"] == (True,) * 6
    assert with_seed["fixed"] == (False,) * 6
    assert any(with_seed["seed"])
    assert len(subject._TASK_SPECS) == 5


def test_synthetic_truth_table_is_exact() -> None:
    rows = subject._verify_synthetic_truth_table_v1()
    assert len(rows) == 5
    assert rows[0]["generation"] == [False, False, False, False, True, True]
    assert rows[1]["generation"] == [False, False, True, True, True, True]
    assert rows[2]["generation"] == [True, True, False, False, True, True]
    assert rows[3]["generation"] == [True, True, False, False, False, False]
    assert rows[4]["generation"] == [True] * 6
    assert rows[4]["fixed"] == [False] * 6


@pytest.mark.parametrize(
    "mutation",
    (
        lambda value: value["tasks"].pop(),
        lambda value: value["tasks"].__setitem__(3, value["tasks"][2]),
        lambda value: value["tasks"].__setitem__(slice(2, 4), [value["tasks"][3], value["tasks"][2]]),
        lambda value: value.__setitem__("long_names_are_semantic_authority", False),
        lambda value: value["tasks"].append(copy.deepcopy(value["tasks"][-1])),
        lambda value: value["primary_roles"].append({"role_id": 3, "semantic_name": "anchor"}),
        lambda value: value.__setitem__("minimal_seed_is_primary_role", True),
        lambda value: value.__setitem__(
            "task_c_seed_conditioning_semantics", "seed_changes_base_masks"
        ),
        lambda value: value.__setitem__("minimal_seed_is_canonical_task", True),
        lambda value: value.__setitem__("warhead_complement_separates_scaffold_and_linker", True),
        lambda value: value.__setitem__("ligand_internal_boundary_is_complete_role_authority", True),
        lambda value: value.__setitem__("anchor_distance_reference", "ligand_minimal_seed_atom"),
        lambda value: value.__setitem__("sidecars_concatenated_to_checkpoint_10d", True),
        lambda value: value.__setitem__("checkpoint_feature_width", 11),
        lambda value: value.__setitem__("runtime_mask_changed", True),
        lambda value: value.__setitem__("dataloader_changed", True),
        lambda value: value.__setitem__("model_changed", True),
        lambda value: value.__setitem__("forward_changed", True),
        lambda value: value.__setitem__("loss_changed", True),
        lambda value: value.__setitem__("tensor_materialization_performed", True),
        lambda value: value.__setitem__("checkpoint_access_performed", True),
        lambda value: value.__setitem__("runtime_smoke_performed", True),
        lambda value: value.__setitem__("training_performed", True),
        lambda value: value.__setitem__("parameter_update_performed", True),
        lambda value: value.__setitem__("reward_or_rl_performed", True),
    ),
)
def test_contract_spec_mutations_fail_closed(mutation) -> None:
    changed = subject._contract_spec_v1()
    mutation(changed)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        subject._validate_contract_spec_v1(changed)


def test_valid_role_partition() -> None:
    subject._validate_role_partition_v1(**_valid_partition())


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("linker_indices", (1, 2, 3)),
        ("warhead_indices", (5,)),
        ("warhead_indices", (4, 6)),
        ("warhead_indices", (4, 4, 5)),
        ("ligand_atom_symbols", ("C", "N", "O", "S", "H", "N")),
        ("index_space", "source_full_atom_row_index_0based"),
        ("role_id_by_atom", (0, 0, 1, 1, 2, True)),
        ("scaffold_indices", (False, 1)),
    ),
)
def test_invalid_role_partitions_fail_closed(field: str, value: object) -> None:
    arguments = _valid_partition()
    arguments[field] = value
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        subject._validate_role_partition_v1(**arguments)


@pytest.mark.parametrize(
    ("field", "role_ids"),
    (
        ("scaffold_indices", (1, 1, 1, 1, 2, 2)),
        ("linker_indices", (0, 0, 0, 0, 2, 2)),
        ("warhead_indices", (0, 0, 1, 1, 1, 1)),
    ),
)
def test_each_empty_primary_role_region_fails_closed(
    field: str, role_ids: tuple[int, ...]
) -> None:
    arguments = _valid_partition()
    arguments[field] = ()
    arguments["role_id_by_atom"] = role_ids
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        subject._validate_role_partition_v1(**arguments)


@pytest.mark.parametrize(
    ("role_ids", "role_valid"),
    (
        ((0, 1, 2), (True, True, True)),
        ((-1,), (False,)),
        ((0, -1, 2), (True, False, True)),
    ),
)
def test_role_id_validity_pairs_accept_only_exact_contract(
    role_ids: tuple[int, ...], role_valid: tuple[bool, ...]
) -> None:
    assert subject._validate_role_id_validity_pairs_v1(
        role_ids=role_ids, role_valid=role_valid
    ) == (role_ids, role_valid)


@pytest.mark.parametrize(
    ("role_ids", "role_valid"),
    (
        ((0,), (False,)),
        ((-1,), (True,)),
        ((1,), (False,)),
        ((-2,), (False,)),
        ((3,), (True,)),
        ((True,), (True,)),
        ((0, 1), (True,)),
        ({"role": 0}, (True,)),
        ((0,), {"valid": True}),
    ),
)
def test_role_id_validity_sentinel_mismatches_fail_closed(
    role_ids: object, role_valid: object
) -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        subject._validate_role_id_validity_pairs_v1(
            role_ids=role_ids, role_valid=role_valid
        )


def test_bool_task_id_fails_closed() -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        subject._derive_base_masks_v1(
            role_ids=(0, 1, 2),
            task_id=True,
            role_valid=(True, True, True),
            canonical_task_valid=True,
            sample_training_admitted=True,
            seed_mask=(False, False, False),
            seed_valid=False,
        )


@pytest.mark.parametrize(
    "mutation",
    (
        lambda value: value.__setitem__("fixed", (True, False, False, False, False, False)),
        lambda value: (
            value.__setitem__("generation", (False, False, False, True, True, True)),
            value.__setitem__("target", (False, False, False, True, True, True)),
        ),
        lambda value: value.__setitem__("context", (True, True, True, False, False, False)),
        lambda value: value.__setitem__("active_loss", (True,) * 6),
    ),
)
def test_mask_partition_and_active_loss_mutations_fail_closed(mutation) -> None:
    changed = copy.deepcopy(_valid_bundle())
    mutation(changed)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _validate_bundle(changed)


def test_task_c_base_fixed_atom_fails_closed() -> None:
    changed = subject._derive_base_masks_v1(
        role_ids=(0, 0, 1, 1, 2, 2),
        task_id=4,
        role_valid=(True,) * 6,
        canonical_task_valid=True,
        sample_training_admitted=True,
        seed_mask=(True, False, False, False, False, False),
        seed_valid=True,
    )
    changed["generation"] = (False, True, True, True, True, True)
    changed["target"] = changed["generation"]
    changed["fixed"] = (True, False, False, False, False, False)
    changed["context"] = changed["fixed"]
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _validate_bundle(changed, task_id=4, seed_valid=True)


def test_non_c_seed_condition_fails_closed() -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        subject._derive_base_masks_v1(
            role_ids=(0, 1, 2),
            task_id=0,
            role_valid=(True, True, True),
            canonical_task_valid=True,
            sample_training_admitted=True,
            seed_mask=(True, False, False),
            seed_valid=True,
        )


def test_seed_cannot_silently_modify_base_fixed_mask() -> None:
    bundle = subject._derive_base_masks_v1(
        role_ids=(0, 0, 1, 1, 2, 2),
        task_id=4,
        role_valid=(True,) * 6,
        canonical_task_valid=True,
        sample_training_admitted=True,
        seed_mask=(True, False, False, False, False, False),
        seed_valid=True,
    )
    bundle["generation"] = (False, True, True, True, True, True)
    bundle["target"] = bundle["generation"]
    bundle["fixed"] = bundle["seed"]
    bundle["context"] = bundle["fixed"]
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _validate_bundle(bundle, task_id=4, seed_valid=True)


@pytest.mark.parametrize(
    ("task_id", "seed", "seed_valid"),
    (
        (1, (True, False, False, False, False, False), False),
        (1, (False,) * 6, True),
        (4, (True, False, False, False, False, False), False),
        (4, (False,) * 6, True),
    ),
)
def test_final_bundle_validator_independently_rejects_seed_bypass(
    task_id: int, seed: tuple[bool, ...], seed_valid: bool
) -> None:
    bundle = _valid_bundle(task_id)
    bundle["seed"] = seed
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _validate_bundle(bundle, task_id=task_id, seed_valid=seed_valid)


def test_active_loss_excludes_invalid_role_task_and_sample() -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        subject._derive_base_masks_v1(
            role_ids=(0, -1, 2),
            task_id=1,
            role_valid=(True, False, True),
            canonical_task_valid=True,
            sample_training_admitted=True,
            seed_mask=(False, False, False),
            seed_valid=False,
        )
    task_invalid = subject._derive_base_masks_v1(
        role_ids=(0, 1, 2),
        task_id=1,
        role_valid=(True, True, True),
        canonical_task_valid=False,
        sample_training_admitted=True,
        seed_mask=(False, False, False),
        seed_valid=False,
    )
    sample_invalid = subject._derive_base_masks_v1(
        role_ids=(0, 1, 2),
        task_id=1,
        role_valid=(True, True, True),
        canonical_task_valid=True,
        sample_training_admitted=False,
        seed_mask=(False, False, False),
        seed_valid=False,
    )
    assert task_invalid["active_loss"] == (False, False, False)
    assert sample_invalid["active_loss"] == (False, False, False)


def test_invalid_role_row_cannot_generate_or_be_fixed_even_if_sample_not_admitted() -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        subject._derive_base_masks_v1(
            role_ids=(0, -1, 2),
            task_id=1,
            role_valid=(True, False, True),
            canonical_task_valid=False,
            sample_training_admitted=False,
            seed_mask=(False, False, False),
            seed_valid=False,
        )


def test_active_loss_in_invalid_sample_fails_closed() -> None:
    changed = _valid_bundle()
    changed["active_loss"] = (False, False, True, False, False, False)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _validate_bundle(changed, task_valid=False, admitted=False)


@pytest.mark.parametrize(
    "arguments",
    (
        {
            "tracked_worktree_paths": ("src/covalent_ext/masking.py",),
            "staged_paths": (),
            "ordinary_untracked_paths": subject._CANDIDATE_PATHS,
        },
        {
            "tracked_worktree_paths": (),
            "staged_paths": ("src/covalent_ext/dataset.py",),
            "ordinary_untracked_paths": subject._CANDIDATE_PATHS,
        },
        {
            "tracked_worktree_paths": (),
            "staged_paths": (),
            "ordinary_untracked_paths": subject._CANDIDATE_PATHS + ("forbidden.npz",),
        },
    ),
)
def test_candidate_scope_modification_fails_closed(arguments: dict[str, object]) -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        subject._validate_candidate_changes_v1(**arguments)


def _synthetic_lifecycle_facts(profile: str) -> dict[str, object]:
    blobs = {
        path: hashlib.sha1(path.encode("utf-8")).hexdigest()
        for path in subject._CANDIDATE_PATHS
    }
    base: dict[str, object] = {
        "head": subject._BASE,
        "origin": subject._BASE,
        "ahead": 0,
        "behind": 0,
        "base_ancestor_head": True,
        "base_ancestor_origin": True,
        "tracked_worktree_paths": (),
        "staged_paths": (),
        "ordinary_untracked_paths": subject._CANDIDATE_PATHS,
        "repository_clean": False,
        "path_commits": [],
        "live_paths": {
            path: {"tracked": False, "mode": "100644", "blob": blobs[path]}
            for path in subject._CANDIDATE_PATHS
        },
    }
    if profile == "contract_precommit_candidate":
        return base
    commit_hash = "a" * 40
    published = profile in {
        "contract_published_successor",
        "contract_published_future_successor",
    }
    future_successor = profile == "contract_published_future_successor"
    commit = {
        "commit": commit_hash,
        "parents": [subject._BASE],
        "subject": subject._CONTRACT_COMMIT_SUBJECT,
        "changed_paths": subject._CANDIDATE_PATHS,
        "changed_statuses": {path: "A" for path in subject._CANDIDATE_PATHS},
        "path_modes": {path: "100644" for path in subject._CANDIDATE_PATHS},
        "path_blobs": blobs,
        "ancestor_head": True,
        "ancestor_origin": published,
    }
    base.update({
        "head": "c" * 40 if future_successor else commit_hash,
        "origin": "c" * 40 if future_successor else (commit_hash if published else subject._BASE),
        "ahead": 0 if published else 1,
        "ordinary_untracked_paths": (),
        "repository_clean": True,
        "path_commits": [commit],
        "live_paths": {
            path: {
                "tracked": True,
                "mode": "100644",
                "index_blob": blobs[path],
                "blob": blobs[path],
            }
            for path in subject._CANDIDATE_PATHS
        },
    })
    return base


@pytest.mark.parametrize(
    "profile",
    (
        "contract_precommit_candidate",
        "contract_committed_unpushed",
        "contract_published_successor",
    ),
)
def test_exact3_contract_lifecycle_profiles_are_commit_survivable(profile: str) -> None:
    result = subject._derive_contract_lifecycle_v1(_synthetic_lifecycle_facts(profile))
    assert result["contract_lifecycle_profile"] == profile
    assert result["contract_committed"] is (profile != "contract_precommit_candidate")
    assert result["contract_published"] is (profile == "contract_published_successor")
    assert result["ready_for_contract_commit_review"] is (
        profile == "contract_precommit_candidate"
    )


def test_published_contract_lifecycle_allows_future_unrelated_successor() -> None:
    facts = _synthetic_lifecycle_facts("contract_published_future_successor")
    result = subject._derive_contract_lifecycle_v1(facts)
    assert facts["head"] == facts["origin"] == "c" * 40
    assert facts["head"] != facts["path_commits"][0]["commit"]
    assert facts["origin"] != facts["path_commits"][0]["commit"]
    assert len(facts["path_commits"]) == 1
    assert result == {
        "contract_lifecycle_profile": "contract_published_successor",
        "contract_commit": "a" * 40,
        "contract_committed": True,
        "contract_published": True,
        "ready_for_contract_commit_review": False,
    }


def test_index_identity_cannot_hide_actual_worktree_blob_drift(monkeypatch) -> None:
    facts = _synthetic_lifecycle_facts("contract_committed_unpushed")
    path = subject._CANDIDATE_PATHS[0]
    formal_blob = facts["path_commits"][0]["path_blobs"][path]
    drifted_worktree_blob = "b" * 40

    def fake_git_text(repo_root: Path, arguments: list[str]) -> str:
        assert repo_root == ROOT
        if arguments[:2] == ["hash-object", "--no-filters"]:
            return f"{drifted_worktree_blob}\n"
        if arguments[:2] == ["ls-files", "--stage"]:
            return f"100644 {formal_blob} 0\t{path}\n"
        raise AssertionError(arguments)

    monkeypatch.setattr(subject, "_git_text", fake_git_text)
    identity = subject._collect_live_candidate_identity_v1(ROOT, path)
    assert facts["tracked_worktree_paths"] == ()
    assert facts["staged_paths"] == ()
    assert identity["index_blob"] == formal_blob
    assert identity["blob"] == drifted_worktree_blob != formal_blob
    facts["live_paths"][path] = identity
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        subject._derive_contract_lifecycle_v1(facts)


@pytest.mark.parametrize(
    "mutation",
    (
        lambda value: value["path_commits"][0].__setitem__("parents", []),
        lambda value: value["path_commits"][0].__setitem__("subject", "wrong subject"),
        lambda value: value["path_commits"][0]["changed_statuses"].__setitem__(
            subject._CANDIDATE_PATHS[0], "M"
        ),
        lambda value: value["path_commits"][0]["path_modes"].__setitem__(
            subject._CANDIDATE_PATHS[0], "100755"
        ),
        lambda value: value["live_paths"][subject._CANDIDATE_PATHS[0]].__setitem__(
            "blob", "b" * 40
        ),
        lambda value: value.__setitem__("repository_clean", False),
        lambda value: value["path_commits"].append(copy.deepcopy(value["path_commits"][0])),
    ),
)
def test_non_survivable_contract_lifecycle_fails_closed(mutation) -> None:
    facts = _synthetic_lifecycle_facts("contract_committed_unpushed")
    mutation(facts)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        subject._derive_contract_lifecycle_v1(facts)


def test_authority_readiness_is_evidence_derived_and_fail_closed(response: dict[str, object]) -> None:
    assert response["warhead_atom_set_authority_coverage"] == "11/11"
    assert response["ligand_internal_warhead_boundary_authority_coverage"] == "11/11"
    assert response["role_assignment_authority_coverage"] == "0/11"
    assert response["minimal_seed_anchor_authority_coverage"] == "0/11"
    assert response["primary_role_authority_complete"] is False
    assert response["minimal_seed_anchor_authority_complete"] is False
    assert response["real_role_task_mask_materialization_ready"] is False
    changed = copy.deepcopy(response)
    changed["minimal_seed_anchor_authority_complete"] = True
    changed["real_role_task_mask_materialization_ready"] = True
    changed["response_sha256"] = hashlib.sha256(
        _canonical_bytes({key: changed[key] for key in subject._RESPONSE_FIELDS[:-1]})
    ).hexdigest()
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        subject._validate_response_v1(changed)


def test_anchor_distance_and_checkpoint_boundaries(response: dict[str, object]) -> None:
    assert response["anchor_distance_reference"] == "target_residue_reactive_atom"
    assert response["anchor_distance_semantic_name"] == "ligand_to_target_reactive_atom_distance_angstrom"
    assert response["anchor_distance_unit"] == "angstrom"
    assert response["anchor_distance_shape"] == "[N_ligand,1]"
    assert response["checkpoint_atom_feature_width"] == 10
    assert response["new_role_task_seed_tensors_are_sidecars"] is True
    assert response["checkpoint_feature_concatenation_allowed"] is False
    assert response["model_state_dict_changed"] is False
    assert response["checkpoint_migration_required"] is False


def test_artifacts_are_exact_deterministic_and_manifest_has_no_self_hash() -> None:
    records = subject._evidence_records(ROOT)
    manifest = subject._validate_artifacts(ROOT, records)
    assert manifest["source_inventory_row_count"] == 20
    assert manifest["field_contract_row_count"] == 14
    assert manifest["failure_matrix_row_count"] == 34
    assert Path(subject._MANIFEST_PATH).name not in manifest["evidence_sha256"]
    assert all(not value.startswith("/") for value in manifest["evidence_sha256"])


def test_failure_matrix_is_exact34_and_cases_are_test_bound(response: dict[str, object]) -> None:
    assert response["failure_matrix_case_count"] == 34
    assert len(response["failure_matrix_cases"]) == 34
    rows = subject._csv_rows((ROOT / subject._FAILURE_MATRIX_PATH).read_bytes())
    assert len(rows) == 34
    assert all(row["expected_outcome"] == "fail_closed" for row in rows)
    assert all(row["covered_by_test"] == "true" for row in rows)


def test_response_order_digest_and_readiness_tampering_fail_closed(
    response: dict[str, object],
) -> None:
    changed = copy.deepcopy(response)
    changed["response_sha256"] = "0" * 64
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        subject._validate_response_v1(changed)

    reordered = copy.deepcopy(response)
    first_value = reordered.pop("contract_version")
    reordered["contract_version"] = first_value
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        subject._validate_response_v1(reordered)


@pytest.mark.parametrize(
    "mutation",
    (
        lambda value: value.__setitem__("contract_version", "tampered"),
        lambda value: value.__setitem__("error_contract", "tampered"),
        lambda value: value["candidate_paths"].pop(),
        lambda value: value["evidence_records"][0].__setitem__("verified", False),
        lambda value: value["canonical_role_vocabulary"][0].__setitem__(
            "semantic_name", "anchor"
        ),
        lambda value: value["canonical_task_truth_table"][3].__setitem__(
            "display_alias", "B2"
        ),
        lambda value: value.__setitem__("canonical_task_count", 6),
        lambda value: value["task_c_base_fixed"].append("scaffold"),
        lambda value: value.__setitem__("minimal_seed_is_primary_role", True),
        lambda value: value.__setitem__(
            "task_c_seed_conditioning_semantics", "seed_changes_base_masks"
        ),
        lambda value: value["field_contract_registry"][0].__setitem__(
            "sentinel_policy", "not_applicable"
        ),
        lambda value: value.__setitem__("runtime_lig_fixed_polarity", "1=generated"),
        lambda value: value.__setitem__("role_assignment_authority_coverage", "1/11"),
        lambda value: value.__setitem__("minimal_seed_anchor_authority_coverage", "1/11"),
        lambda value: value.__setitem__("primary_role_authority_complete", True),
        lambda value: value.__setitem__("ready_for_training", True),
        lambda value: value.__setitem__("anchor_distance_reference", "ligand_seed_atom"),
        lambda value: value.__setitem__("checkpoint_atom_feature_width", 11),
        lambda value: value.__setitem__("checkpoint_channel_order", "tampered"),
        lambda value: value.__setitem__("runtime_mask_changed", True),
        lambda value: value["generated_evidence_files"].pop(),
        lambda value: value.__setitem__("recommended_next_increment", "tampered"),
        lambda value: value.__setitem__(
            "contract_lifecycle_profile",
            {
                "contract_precommit_candidate": "contract_committed_unpushed",
                "contract_committed_unpushed": "contract_published_successor",
                "contract_published_successor": "contract_precommit_candidate",
            }[value["contract_lifecycle_profile"]],
        ),
        lambda value: value.__setitem__(
            "ready_for_contract_commit_review",
            not value["ready_for_contract_commit_review"],
        ),
        lambda value: value.__setitem__("commit_created", True),
    ),
)
def test_critical_response_tampering_with_recomputed_digest_fails_closed(
    response: dict[str, object], mutation
) -> None:
    changed = copy.deepcopy(response)
    mutation(changed)
    assert _canonical_bytes(changed) != _canonical_bytes(response), (
        "critical response mutation must not be a no-op"
    )
    changed["response_sha256"] = hashlib.sha256(
        _canonical_bytes({key: changed[key] for key in subject._RESPONSE_FIELDS[:-1]})
    ).hexdigest()
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        subject._validate_response_v1(changed)


def test_source_has_no_torch_model_or_checkpoint_import() -> None:
    path = ROOT / "src/covalent_ext" / (
        "covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1.py"
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported.update(
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    )
    assert imported.isdisjoint({"torch", "lightning_modules", "equivariant_diffusion"})


def test_final_readiness_and_execution_boundaries_remain_false(
    response: dict[str, object],
) -> None:
    assert response["role_task_mask_contract_resolved"] is True
    for field in (
        "canonical_mask_tensors_materialized",
        "ready_for_tensor_materialization_smoke",
        "ready_for_model_integration",
        "ready_for_training",
        "runtime_mask_changed",
        "dataloader_changed",
        "model_changed",
        "forward_changed",
        "loss_changed",
        "tensor_materialization_performed",
        "checkpoint_access_performed",
        "runtime_smoke_performed",
        "training_performed",
        "fine_tuning_performed",
        "parameter_update_performed",
        "reward_or_rl_performed",
        "commit_created",
        "push_performed",
    ):
        assert response[field] is False
    assert response["final_training_feature_semantics_revalidation_required"] is True
    assert response["recommended_next_increment"] == (
        "resolve_covapie_role_annotation_input_authority_gaps_v1"
    )
