from __future__ import annotations

import copy
import hashlib
import importlib
import inspect
import json
import stat
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE_NAME = "covalent_ext.covapie_five_module_training_path_completion_gap_audit_v1"
ERROR = "COVAPIE_FIVE_MODULE_TRAINING_PATH_COMPLETION_GAP_AUDIT_INVALID"
SOURCE = "be1add10f47911dffea4b7fdf48dcfee36d6edba"
MODULES = (
    "target_residue_atom_condition_adapter",
    "role_mask_anchor_distance_encoding",
    "ligand_residue_atom_pair_prediction_head",
    "pre_post_covalent_geometry_prediction_head",
    "ligand_residue_pair_contrastive_loss",
)
SIGNALS = (
    "warhead_type_identity",
    "warhead_atom_set",
    "ligand_internal_warhead_boundary",
    "target_residue_atom_condition",
    "ligand_atom_to_residue_atom_pair",
    "pre_post_covalent_geometry",
    "scaffold_linker_anchor_atom_roles",
    "contrastive_negative_sampling_policy",
)
MASKS = (
    "warhead_only", "linker_plus_warhead", "scaffold_plus_warhead",
    "scaffold_only", "scaffold_plus_linker_plus_warhead",
)
DIMENSIONS = (
    "semantic_contract", "source_data_or_authority", "schema_fields",
    "label_compilation", "materialized_dataset", "dataset_loading",
    "collate_or_batch_contract", "model_input_or_condition",
    "model_head_or_output", "forward_consumption", "supervised_loss",
    "loss_weight_or_config", "checkpoint_compatibility", "unit_tests",
    "formal_gate", "real_runtime_evidence", "training_readiness",
)
STATUSES = ("complete", "partial", "missing", "blocked", "not_applicable")


@pytest.fixture(scope="module")
def audit_module():
    return importlib.import_module(MODULE_NAME)


@pytest.fixture(scope="module")
def response(audit_module):
    return audit_module.evaluate_covapie_five_module_training_path_completion_gap_audit_v1(repo_root=ROOT)


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


def test_public_api_keyword_only_and_silent_import(audit_module):
    assert audit_module.__all__ == (
        "evaluate_covapie_five_module_training_path_completion_gap_audit_v1",
    )
    signature = inspect.signature(audit_module.evaluate_covapie_five_module_training_path_completion_gap_audit_v1)
    assert tuple(signature.parameters) == ("repo_root",)
    assert signature.parameters["repo_root"].kind is inspect.Parameter.KEYWORD_ONLY
    with pytest.raises(TypeError):
        audit_module.evaluate_covapie_five_module_training_path_completion_gap_audit_v1(ROOT)
    code = (
        "import contextlib,io,sys;"
        "o=io.StringIO();e=io.StringIO();"
        f"\nwith contextlib.redirect_stdout(o),contextlib.redirect_stderr(e): import {MODULE_NAME};"
        "\nassert o.getvalue()=='' and e.getvalue()=='';"
        "\nassert 'torch' not in sys.modules"
    )
    completed = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT,
        env={"PYTHONPATH": f"{ROOT}:{ROOT / 'src'}"}, check=False,
        capture_output=True, text=True)
    assert (completed.returncode, completed.stdout, completed.stderr) == (0, "", "")


def test_response_field_order_source_and_digest(audit_module, response):
    assert tuple(response) == audit_module._RESPONSE_FIELDS
    assert response["source_snapshot_commit"] == SOURCE
    assert response["source_snapshot_subject"] == "record CovaPIE bounded repository CLI conditioned smoke terminal result v1"
    assert response["source_snapshot_tree"] == "8bca3bd8de003f8494e7bbf996a345c0ce0421ca"
    unsigned = {key: value for key, value in response.items() if key != "response_sha256"}
    assert response["response_sha256"] == hashlib.sha256(canonical_bytes(unsigned)).hexdigest()
    audit_module._validate_response(copy.deepcopy(response))


def test_canonical_five_module_taxonomy_is_exact(response):
    assert tuple(response["canonical_module_names"]) == MODULES
    assert response["canonical_module_count"] == 5
    assert "warhead_type_prediction" not in response["canonical_module_names"]
    assert "ligand_residue_pair_contrastive_loss" in response["canonical_module_names"]


def test_eight_signal_layer_is_exact_and_separate(response):
    assert tuple(response["canonical_supervision_signal_names"]) == SIGNALS
    assert response["canonical_supervision_signal_count"] == 8
    assert tuple(response["supervision_signal_readiness_matrix"]) == SIGNALS
    assert "warhead_type_identity" not in response["canonical_module_names"]


@pytest.mark.parametrize("signal", SIGNALS)
def test_every_signal_has_evidence_and_training_boundary(response, signal):
    row = response["supervision_signal_readiness_matrix"][signal]
    assert tuple(row) == (
        "status", "authority_coverage", "evidence_paths", "evidence_commits",
        "model_consumer", "remaining_gap", "blocking_modules", "training_approved",
    )
    assert row["status"] in STATUSES
    assert row["authority_coverage"]
    assert row["evidence_paths"] and row["evidence_commits"]
    assert row["model_consumer"] and row["remaining_gap"]
    assert type(row["training_approved"]) is bool


def test_warhead_type_is_11_of_11_but_not_training_approved(response):
    row = response["supervision_signal_readiness_matrix"]["warhead_type_identity"]
    assert row["authority_coverage"] == "11/11"
    assert row["training_approved"] is False
    assert "WARHEAD_TYPE_SUPERVISION_MODEL_CONSUMER_UNRESOLVED" in row["remaining_gap"]
    assert "optional_head_or_condition_encoding_or_evaluation_only" in row["model_consumer"]
    assert response["warhead_type_authority_coverage"] == "11/11"
    assert response["warhead_type_training_approved"] is False
    assert response["warhead_type_consumer_resolved"] is False


def test_masks_are_exact_five_with_b2_and_b3(response):
    assert tuple(response["canonical_mask_semantic_names"]) == MASKS
    assert response["canonical_mask_count"] == 5
    aliases = response["canonical_mask_display_aliases"]
    assert aliases[2] == {"semantic_name": "scaffold_plus_warhead", "display_alias": "B2"}
    assert aliases[3] == {"semantic_name": "scaffold_only", "display_alias": "B3"}


def test_exact17_dimensions_and_status_vocabulary(response):
    assert tuple(response["audit_dimension_names"]) == DIMENSIONS
    assert response["audit_dimension_count"] == 17
    assert tuple(response["allowed_dimension_statuses"]) == STATUSES
    for module in MODULES:
        assert tuple(response["module_audit_matrix"][module]) == DIMENSIONS
        assert len(response["module_audit_matrix"][module]) == 17


@pytest.mark.parametrize("module", MODULES)
@pytest.mark.parametrize("dimension", DIMENSIONS)
def test_every_dimension_record_is_complete(response, module, dimension):
    row = response["module_audit_matrix"][module][dimension]
    assert tuple(row) == (
        "status", "evidence_paths", "evidence_commits", "evidence_summary",
        "remaining_gap", "blocking_for_training",
    )
    assert row["status"] in STATUSES
    assert row["evidence_summary"]
    assert type(row["blocking_for_training"]) is bool
    if row["status"] == "complete":
        assert row["evidence_paths"] and row["evidence_commits"]
    if row["status"] == "missing":
        assert row["evidence_paths"] == [] and row["evidence_commits"] == []


def test_module_boundaries_are_not_merged(response):
    target = response["module_audit_matrix"]["target_residue_atom_condition_adapter"]
    role = response["module_audit_matrix"]["role_mask_anchor_distance_encoding"]
    pair = response["module_audit_matrix"]["ligand_residue_atom_pair_prediction_head"]
    contrastive = response["module_audit_matrix"]["ligand_residue_pair_contrastive_loss"]
    assert target["model_head_or_output"]["status"] == "not_applicable"
    assert target["supervised_loss"]["status"] == "not_applicable"
    assert target["forward_consumption"]["status"] == "complete"
    assert role["model_head_or_output"]["status"] == "not_applicable"
    assert "anchor distance" in role["semantic_contract"]["evidence_summary"]
    assert pair["model_head_or_output"]["status"] == "missing"
    assert "separately from contrastive" in pair["supervised_loss"]["remaining_gap"]
    assert contrastive["model_head_or_output"]["status"] == "not_applicable"
    assert contrastive["forward_consumption"]["status"] == "missing"
    assert contrastive["supervised_loss"]["status"] == "missing"


def test_contrastive_negative_policy_is_bound(response):
    rows = response["module_audit_matrix"]["ligand_residue_pair_contrastive_loss"]
    text = canonical_bytes(rows).decode("ascii")
    assert "same-sample deterministic negatives" in text
    assert "random=false" in text
    assert "hard=false" in text
    assert "cross-sample=false" in text
    assert "zero-negative" in text
    assert "pair_contrastive_sample_loss_mask" in text


def test_counts_and_all_five_not_ready_are_derived(response):
    assert response["training_ready_module_count"] == 0
    assert response["training_not_ready_module_count"] == 5
    for module in MODULES:
        assert response["module_completion_summary"][module]["training_ready"] is False
        counts = sum(response[field][module] for field in (
            "complete_dimension_count_by_module", "partial_dimension_count_by_module",
            "missing_dimension_count_by_module", "blocked_dimension_count_by_module",
            "not_applicable_dimension_count_by_module",
        ))
        assert counts == 17
        assert response["module_audit_matrix"][module]["training_readiness"]["status"] == "blocked"


def test_feature_state_binds_audit_resolution_and_remaining_gaps(response):
    assert response["feature_semantics_contract_audit_completed"] is True
    assert response["unknown_atom_policy_contract_resolved"] is True
    assert response["feature_semantics_known_at_resolution_snapshot"] is True
    policy = "fail_closed_rejection_required_for_checkpoint_compatibility"
    assert response["protein_unknown_atom_policy"] == policy
    assert response["ligand_unknown_atom_policy"] == policy
    assert response["checkpoint_10d_channel_order_preserved"] is True
    assert response["silent_zero_vector_fallback_allowed"] is False
    assert response["unknown_atom_runtime_enforcement_integrated"] is False
    assert response["feature_semantics_runtime_enforcement_integrated"] is False
    assert response["canonical_mask_tensors_materialized"] is False
    assert response["ready_for_tensorization"] is False
    assert response["ready_for_model_integration"] is False
    assert response["ready_for_training"] is False
    assert response["final_training_feature_semantics_revalidation_required"] is True
    risks = " ".join(response["feature_semantics_risks"])
    assert "complete historical gates" in risks
    assert "Step12D" in risks
    assert "feature_semantics_known=False" not in risks
    assert "UNKNOWN_ATOM_FEATURE_POLICY" not in risks


def test_step12d_runtime_and_no_training_boundary(response):
    assert response["step12d_smoke_legality_verified"] is True
    assert response["step12d_final_feature_semantics_contract"] is False
    assert response["one_time_execution_authorization_consumed"] is True
    assert response["bounded_runtime_smoke_execution_count"] == 1
    assert response["bounded_runtime_smoke_passed"] is False
    assert response["exact67_runtime_evidence_available"] is False
    assert response["failure_establishes_model_runtime_failure"] is False
    assert response["failure_establishes_conditioned_plumbing_failure"] is False
    assert response["real_training_started"] is False
    assert response["parameter_update_performed"] is False
    assert response["RL_implementation_started"] is False
    assert response["audit_does_not_establish_training_readiness"] is True


def test_queue_order_membership_and_recommendation(response):
    queue = response["prioritized_gap_queue"]
    increments = [item["smallest_verifiable_increment"] for item in queue]
    assert [item["priority"] for item in queue] == sorted(
        [item["priority"] for item in queue], key=lambda value: int(value[1]))
    expected = {
        "resolve_covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1",
        "materialize_covapie_target_residue_atom_condition_training_sidecar_v1",
        "freeze_covapie_warhead_type_vocabulary_unknown_and_consumer_placement_contract_v1",
        "materialize_covapie_ligand_residue_pair_training_sidecars_v1",
        "design_covapie_pre_post_covalent_geometry_authority_contract_v1",
        "design_covapie_pair_prediction_optional_head_and_loss_v1",
        "design_covapie_pair_contrastive_loss_v1",
        "design_covapie_geometry_optional_head_and_loss_v1",
        "integrate_covapie_target_condition_training_configuration_v1",
        "review_covapie_conditioned_runtime_warning_and_reexecution_policy_v1",
    }
    assert expected.issubset(increments)
    assert response["recommended_next_increment"] == queue[0]
    assert queue[0]["module"] == "role_mask_anchor_distance_encoding"
    assert queue[0]["smallest_verifiable_increment"] == "resolve_covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1"
    assert all(item["training_or_parameter_update_required"] is False for item in queue)


def _lifecycle_facts(audit_module, state: str) -> dict[str, object]:
    paths = audit_module._AUDIT_PATHS
    blobs = {path: hashlib.sha1(("blob:" + path).encode()).hexdigest() for path in paths}
    live = {path: {"tracked": state != "pre", "mode": "100644", "blob": blobs[path]} for path in paths}
    base: dict[str, object] = {
        "head": SOURCE, "origin": SOURCE, "ahead": 0, "behind": 0,
        "source_ancestor_head": True, "source_ancestor_origin": True,
        "path_commits": [], "ordinary_untracked": paths if state == "pre" else (),
        "worktree_dirty": (), "staged_dirty": (), "live_paths": live,
        "repository_clean": state != "pre",
    }
    if state != "pre":
        commit_hash = "a" * 40
        base["path_commits"] = [{
            "commit": commit_hash, "parents": [SOURCE],
            "subject": audit_module._AUDIT_COMMIT_SUBJECT,
            "changed_paths": list(paths),
            "path_modes": {path: "100644" for path in paths},
            "path_blobs": blobs,
        }]
        base["audit_ancestor_head"] = True
        if state == "committed":
            base.update({"head": commit_hash, "ahead": 1,
                         "audit_ancestor_origin": False})
        else:
            successor = commit_hash if state == "published" else "c" * 40
            base.update({"head": successor, "origin": successor,
                         "audit_ancestor_origin": True})
    return base


@pytest.mark.parametrize(
    ("state", "profile", "committed", "published", "review"),
    (
        ("pre", "audit_precommit_candidate", False, False, True),
        ("committed", "audit_committed_unpushed", True, False, False),
        ("published", "audit_published_successor", True, True, False),
        ("future", "audit_published_successor", True, True, False),
    ),
)
def test_synthetic_lifecycle_profiles_and_future_successor(audit_module, state, profile, committed, published, review):
    facts = _lifecycle_facts(audit_module, state)
    if state == "published":
        assert facts["head"] == facts["path_commits"][0]["commit"]
        assert facts["origin"] == facts["path_commits"][0]["commit"]
    if state == "future":
        assert facts["head"] != facts["path_commits"][0]["commit"]
        assert facts["origin"] != facts["path_commits"][0]["commit"]
    result = audit_module._derive_audit_lifecycle(facts)
    assert result["audit_lifecycle_profile"] == profile
    assert result["audit_committed"] is committed
    assert result["audit_published"] is published
    assert result["ready_for_audit_commit_review"] is review


def test_live_tree_lifecycle_matches_current_repository_state(audit_module, response):
    lifecycle = {
        "audit_lifecycle_profile": response["audit_lifecycle_profile"],
        "audit_commit": response["audit_commit"],
        "audit_committed": response["audit_committed"],
        "audit_published": response["audit_published"],
        "ready_for_audit_commit_review": response[
            "ready_for_audit_commit_review"
        ],
    }

    def git_output(*arguments: str) -> str:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0, completed.stderr
        assert completed.stderr == ""
        return completed.stdout.strip()

    def assert_ancestor(ancestor: str, descendant: str) -> None:
        completed = subprocess.run(
            ["git", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0, completed.stderr
        assert completed.stdout == ""
        assert completed.stderr == ""

    def assert_audit_commit_and_live_files(audit_commit: str) -> None:
        assert git_output("show", "-s", "--format=%s", audit_commit) == (
            "add CovaPIE five-module training-path completion gap audit v1"
        )
        assert git_output("show", "-s", "--format=%P", audit_commit).split() == [
            SOURCE
        ]
        changed = [
            line.split("\t", 1)
            for line in git_output(
                "diff-tree",
                "--root",
                "--no-commit-id",
                "--name-status",
                "-r",
                audit_commit,
            ).splitlines()
        ]
        assert len(changed) == 4
        assert {path for status_code, path in changed if status_code == "A"} == set(
            audit_module._AUDIT_PATHS
        )
        assert all(status_code == "A" for status_code, _path in changed)

        tracked = set(git_output("ls-files").splitlines())
        for relative_path in audit_module._AUDIT_PATHS:
            tree_line = git_output("ls-tree", audit_commit, "--", relative_path)
            metadata, tree_path = tree_line.split("\t", 1)
            mode, object_type, commit_blob = metadata.split()
            assert tree_path == relative_path
            assert mode == "100644"
            assert object_type == "blob"
            assert relative_path in tracked
            live_path = ROOT / relative_path
            assert stat.S_ISREG(live_path.lstat().st_mode)
            assert not live_path.is_symlink()
            assert stat.S_IMODE(live_path.lstat().st_mode) == 0o644
            assert git_output("hash-object", "--", relative_path) == commit_blob

        assert git_output(
            "diff", "--name-only", "--", *audit_module._AUDIT_PATHS
        ) == ""
        assert git_output(
            "diff", "--cached", "--name-only", "--", *audit_module._AUDIT_PATHS
        ) == ""

    actual_head = git_output("rev-parse", "HEAD")
    actual_origin_main = git_output("rev-parse", "refs/remotes/origin/main")
    ahead, behind = (
        int(value)
        for value in git_output(
            "rev-list",
            "--left-right",
            "--count",
            "HEAD...refs/remotes/origin/main",
        ).split()
    )
    assert response["source_snapshot_commit"] == SOURCE
    assert_ancestor(SOURCE, actual_head)
    assert_ancestor(SOURCE, actual_origin_main)

    profile = lifecycle["audit_lifecycle_profile"]
    if profile == "audit_precommit_candidate":
        assert lifecycle == {
            "audit_lifecycle_profile": "audit_precommit_candidate",
            "audit_commit": None,
            "audit_committed": False,
            "audit_published": False,
            "ready_for_audit_commit_review": True,
        }
        assert (actual_head, actual_origin_main, ahead, behind) == (
            SOURCE,
            SOURCE,
            0,
            0,
        )
        tracked = set(git_output("ls-files").splitlines())
        ordinary_untracked = set(
            git_output("ls-files", "--others", "--exclude-standard").splitlines()
        )
        assert ordinary_untracked == set(audit_module._AUDIT_PATHS)
        for relative_path in audit_module._AUDIT_PATHS:
            assert relative_path not in tracked
            assert relative_path in ordinary_untracked
            live_path = ROOT / relative_path
            assert stat.S_ISREG(live_path.lstat().st_mode)
            assert not live_path.is_symlink()
            assert stat.S_IMODE(live_path.lstat().st_mode) == 0o644
    elif profile == "audit_committed_unpushed":
        audit_commit = lifecycle["audit_commit"]
        assert audit_commit == actual_head
        assert lifecycle == {
            "audit_lifecycle_profile": "audit_committed_unpushed",
            "audit_commit": actual_head,
            "audit_committed": True,
            "audit_published": False,
            "ready_for_audit_commit_review": False,
        }
        assert (actual_origin_main, ahead, behind) == (SOURCE, 1, 0)
        assert git_output("status", "--porcelain=v1", "--untracked-files=all") == ""
        assert_audit_commit_and_live_files(audit_commit)
    elif profile == "audit_published_successor":
        audit_commit = lifecycle["audit_commit"]
        assert isinstance(audit_commit, str)
        assert len(audit_commit) == 40
        assert all(character in "0123456789abcdef" for character in audit_commit)
        assert lifecycle == {
            "audit_lifecycle_profile": "audit_published_successor",
            "audit_commit": audit_commit,
            "audit_committed": True,
            "audit_published": True,
            "ready_for_audit_commit_review": False,
        }
        assert_ancestor(audit_commit, actual_head)
        assert_ancestor(audit_commit, actual_origin_main)
        assert_audit_commit_and_live_files(audit_commit)
    else:
        pytest.fail(f"unexpected live audit lifecycle profile: {profile}")


def _bad_subject(facts, _module):
    facts["path_commits"][0]["subject"] = "wrong subject"


def _bad_parent(facts, _module):
    facts["path_commits"][0]["parents"] = ["0" * 40]


def _bad_path(facts, _module):
    facts["path_commits"][0]["changed_paths"].append("fifth-file.txt")


def _bad_mode(facts, module):
    facts["path_commits"][0]["path_modes"][module._AUDIT_PATHS[0]] = "100755"


def _bad_blob(facts, module):
    facts["path_commits"][0]["path_blobs"][module._AUDIT_PATHS[0]] = "z" * 40


def _live_drift(facts, module):
    facts["live_paths"][module._AUDIT_PATHS[0]]["blob"] = "0" * 40


@pytest.mark.parametrize("mutation", (_bad_subject, _bad_parent, _bad_path, _bad_mode, _bad_blob, _live_drift))
def test_lifecycle_bad_subject_parent_path_mode_blob_or_live_drift_fails_closed(audit_module, mutation):
    facts = _lifecycle_facts(audit_module, "published")
    mutation(facts, audit_module)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        audit_module._derive_audit_lifecycle(facts)


def test_deterministic_double_evaluation(audit_module, response):
    second = audit_module.evaluate_covapie_five_module_training_path_completion_gap_audit_v1(repo_root=ROOT)
    assert second == response
    assert canonical_bytes(second) == canonical_bytes(response)


def test_tampered_repo_and_source_binding_fail_closed(audit_module, monkeypatch):
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        audit_module.evaluate_covapie_five_module_training_path_completion_gap_audit_v1(repo_root=ROOT.parent)
    monkeypatch.setattr(audit_module, "_SOURCE_SNAPSHOT", "0" * 40)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        audit_module.evaluate_covapie_five_module_training_path_completion_gap_audit_v1(repo_root=ROOT)


@pytest.mark.parametrize("mutation", (
    lambda value: value.__setitem__("canonical_module_count", 6),
    lambda value: value["canonical_module_names"].append("warhead_type_prediction"),
    lambda value: value.__setitem__("canonical_supervision_signal_count", 7),
    lambda value: value["supervision_signal_readiness_matrix"]["warhead_type_identity"].__setitem__("training_approved", True),
    lambda value: value["module_audit_matrix"][MODULES[0]]["training_readiness"].__setitem__("status", "complete"),
    lambda value: value.__setitem__("feature_semantics_contract_audit_completed", False),
    lambda value: value.__setitem__("unknown_atom_policy_contract_resolved", False),
    lambda value: value.__setitem__("feature_semantics_runtime_enforcement_integrated", True),
    lambda value: value.__setitem__("final_training_feature_semantics_revalidation_required", False),
    lambda value: value.__setitem__("audit_lifecycle_profile", "always_untracked"),
    lambda value: value.__setitem__("response_sha256", "0" * 64),
))
def test_tampered_response_fails_closed(audit_module, response, mutation):
    changed = copy.deepcopy(response)
    mutation(changed)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        audit_module._validate_response(changed)
