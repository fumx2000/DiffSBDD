"""Static, fail-closed gap audit for the five formal CovaPIE modules.

Evidence is read from one immutable source snapshot with ``git show``.  The
only live-tree inspection is the audit's own three-state publication lifecycle
and the separately SHA-bound formal target-condition state.  No model import,
checkpoint read, forward pass, tensorization, training, or file write occurs.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence


__all__ = (
    "evaluate_covapie_five_module_training_path_completion_gap_audit_v1",
)


_ERROR = "COVAPIE_FIVE_MODULE_TRAINING_PATH_COMPLETION_GAP_AUDIT_INVALID"
_VERSION = "covapie_five_module_training_path_completion_gap_audit_v1"
_SOURCE_SNAPSHOT = "be1add10f47911dffea4b7fdf48dcfee36d6edba"
_SOURCE_SUBJECT = (
    "record CovaPIE bounded repository CLI conditioned smoke terminal result v1"
)
_SOURCE_TREE = "8bca3bd8de003f8494e7bbf996a345c0ce0421ca"
_AUDIT_COMMIT_SUBJECT = "add CovaPIE five-module training-path completion gap audit v1"

_MODULE_NAMES = (
    "target_residue_atom_condition_adapter",
    "role_mask_anchor_distance_encoding",
    "ligand_residue_atom_pair_prediction_head",
    "pre_post_covalent_geometry_prediction_head",
    "ligand_residue_pair_contrastive_loss",
)
_SIGNAL_NAMES = (
    "warhead_type_identity",
    "warhead_atom_set",
    "ligand_internal_warhead_boundary",
    "target_residue_atom_condition",
    "ligand_atom_to_residue_atom_pair",
    "pre_post_covalent_geometry",
    "scaffold_linker_anchor_atom_roles",
    "contrastive_negative_sampling_policy",
)
_MASK_NAMES = (
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
)
_MASK_ALIASES = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
_DIMENSIONS = (
    "semantic_contract", "source_data_or_authority", "schema_fields",
    "label_compilation", "materialized_dataset", "dataset_loading",
    "collate_or_batch_contract", "model_input_or_condition",
    "model_head_or_output", "forward_consumption", "supervised_loss",
    "loss_weight_or_config", "checkpoint_compatibility", "unit_tests",
    "formal_gate", "real_runtime_evidence", "training_readiness",
)
_STATUSES = ("complete", "partial", "missing", "blocked", "not_applicable")
_DIMENSION_RECORD_FIELDS = (
    "status", "evidence_paths", "evidence_commits", "evidence_summary",
    "remaining_gap", "blocking_for_training",
)
_SIGNAL_RECORD_FIELDS = (
    "status", "authority_coverage", "evidence_paths", "evidence_commits",
    "model_consumer", "remaining_gap", "blocking_modules", "training_approved",
)
_QUEUE_FIELDS = (
    "priority", "module", "dimension", "gap", "why_it_blocks",
    "smallest_verifiable_increment", "expected_files_or_components",
    "training_or_parameter_update_required",
)
_RESPONSE_FIELDS = (
    "audit_version", "error_contract", "source_snapshot_commit",
    "source_snapshot_subject", "source_snapshot_tree", "audit_lifecycle_profile",
    "audit_commit", "audit_committed", "audit_published",
    "ready_for_audit_commit_review", "canonical_module_names",
    "canonical_module_count", "canonical_supervision_signal_names",
    "canonical_supervision_signal_count", "supervision_signal_readiness_matrix",
    "supervision_signal_completion_summary", "warhead_type_authority_coverage",
    "warhead_type_training_approved", "warhead_type_consumer_resolved",
    "canonical_mask_semantic_names", "canonical_mask_display_aliases",
    "canonical_mask_count", "audit_dimension_names", "audit_dimension_count",
    "allowed_dimension_statuses", "module_audit_matrix",
    "module_completion_summary", "complete_dimension_count_by_module",
    "partial_dimension_count_by_module", "missing_dimension_count_by_module",
    "blocked_dimension_count_by_module", "not_applicable_dimension_count_by_module",
    "training_ready_module_count", "training_not_ready_module_count",
    "cross_module_gaps", "checkpoint_compatibility_risks",
    "feature_semantics_risks", "runtime_validation_gaps", "mainline_blockers",
    "non_blocking_followups", "prioritized_gap_queue", "recommended_next_increment",
    "feature_semantics_contract_audit_completed",
    "unknown_atom_policy_contract_resolved",
    "feature_semantics_known_at_resolution_snapshot",
    "protein_unknown_atom_policy", "ligand_unknown_atom_policy",
    "checkpoint_10d_channel_order_preserved", "silent_zero_vector_fallback_allowed",
    "unknown_atom_runtime_enforcement_integrated",
    "feature_semantics_runtime_enforcement_integrated",
    "canonical_mask_tensors_materialized", "ready_for_tensorization",
    "ready_for_model_integration", "ready_for_training",
    "final_training_feature_semantics_revalidation_required",
    "step12d_smoke_legality_verified", "step12d_final_feature_semantics_contract",
    "one_time_execution_authorization_consumed",
    "bounded_runtime_smoke_execution_count", "bounded_runtime_smoke_passed",
    "exact67_runtime_evidence_available",
    "failure_establishes_model_runtime_failure",
    "failure_establishes_conditioned_plumbing_failure", "real_training_started",
    "parameter_update_performed", "RL_implementation_started",
    "audit_does_not_establish_training_readiness", "response_sha256",
)

_AUDIT_PATHS = (
    "docs/covapie_five_module_training_path_completion_gap_audit_v1_guide.md",
    "scripts/check_covapie_five_module_training_path_completion_gap_audit_v1.py",
    "src/covalent_ext/covapie_five_module_training_path_completion_gap_audit_v1.py",
    "tests/test_covapie_five_module_training_path_completion_gap_audit_v1.py",
)

_C_FEATURE_AUDIT = "5b2013281b03d7bd3e0c59b9985e52494263c69f"
_C_FEATURE_RESOLUTION = "160cdbda8800a535b5c0a81d501babfae9a8615b"
_C_TENSOR_CONTRACT = "335a0320e8bd8ee125e51f927e6cd26d0c05707e"
_C_FIVE_READINESS = "1cdbca345483022ece967b24de37013b77349cd4"
_C_ROLE_CONTRACT = "0fda7b9e8fc56941e005f3e8b5e67fa2ceaa4ca1"
_C_WARHEAD = "0c8d1d10260a028360357b8c309f22676fc81645"
_C_UNIFIED = "51810f19e0bbb96171a7dd3aebd72ef08eda0200"
_C_PAIR_DESIGN = "7f432cecec8a3abed2339e4dd60dfa239cd2cbe7"
_C_PAIR_VALIDATION = "e5563ed50db6e56cbdfb6cc629e5eb4fe9137edf"
_C_TARGET_CONTRACT = "fb59a976f6faaa58829f9a761ae4634bcb05a273"
_C_TARGET_AUTHORITY = "1613c5efbb833f11ac3161d0d960c1342694cd4d"
_C_TARGET_ADAPTER = "eccb30e7a160d1e8591591f4a1e2fbfcdb3dfecb"
_C_TARGET_ADAPTER_GATE = "0e9ff5be4db26bceb585732ae7462cd4eda68a3f"
_C_TARGET_RUNTIME = "75589a94235dde2d0943606e58a1f2216b31d3b2"
_C_TARGET_MODEL = "2c504ff2eac0864c146129f4011d902fae5bef69"
_C_TARGET_MODEL_GATE = "dd085332c7e2cf58a6ca2e7d71cf022da010d4b4"
_C_CLI_GATE = "011b9558d4a59824e3ba51a0d896ec13100b2b1b"
_C_MASK_R1 = "963562e2da9bcc14d67d075a49a7770aecaa2e68"
_C_MASK_R2 = "8711c1899759ca4c1f4a24f7ff9782b81a257245"
_C_MASK_R3 = "5974ded1dc1aa02a365a23e4a409b9a7fe98a4be"
_C_B3_SMOKE = "5637325e644d000bf970cc615351dd277675430d"
_C_NPZ_LOADER = "3c6158daaa912a3fd64acc928faa31ad10360a96"
_C_MASKED_LOSS = "88eb689b29a3d003d7de44e29e8b08deb9e9ea8a"
_C_ATOMWISE_LOSS = "6c9e305def69e721ac9daf2d865e1aed5539cd0c"

_FORMAL_COMMIT_SUBJECTS = {
    _C_FEATURE_AUDIT: "add CovaPIE final training feature-semantics audit v1",
    _C_FEATURE_RESOLUTION: "add CovaPIE training unknown-atom policy resolution v1",
    _C_TENSOR_CONTRACT: "add CovaPIE tensor label and loss-mask contract v1",
    _C_FIVE_READINESS: "add CovaPIE Current11 five auxiliary module label readiness design v1",
}

_FEATURE_AUDIT_SOURCE = "src/covalent_ext/covapie_final_training_feature_semantics_and_unknown_atom_policy_audit_v1.py"
_FEATURE_AUDIT_MANIFEST = "data/derived/covalent_small/covapie_final_training_feature_semantics_and_unknown_atom_policy_audit_v1/covapie_final_training_feature_semantics_and_unknown_atom_policy_audit_manifest.json"
_FEATURE_RESOLUTION_SOURCE = "src/covalent_ext/covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1.py"
_FEATURE_RESOLUTION_MANIFEST = "data/derived/covalent_small/covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1/covapie_training_feature_semantics_and_unknown_atom_policy_resolution_manifest.json"
_TENSOR_SOURCE = "src/covalent_ext/covapie_tensor_label_and_loss_mask_contract_design_v1.py"
_TENSOR_REGISTRY = "data/derived/covalent_small/covapie_tensor_label_and_loss_mask_contract_design_v1/covapie_tensor_label_loss_mask_contract_registry.csv"
_READINESS_SOURCE = "src/covalent_ext/covapie_current11_five_auxiliary_module_label_consumption_readiness_design_v1.py"
_WARHEAD_SOURCE = "src/covalent_ext/covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1.py"
_ROLE_SOURCE = "src/covalent_ext/covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"
_PAIR_SOURCE = "src/covalent_ext/covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_evidence_validation_v1.py"
_TARGET_AUTHORITY_SOURCE = "src/covalent_ext/covapie_current11_target_residue_atom_condition_authority_v1.py"
_TARGET_ADAPTER_SOURCE = "src/covalent_ext/covapie_target_residue_atom_condition_adapter_v1.py"
_TARGET_GATE_SOURCE = "src/covalent_ext/covapie_target_residue_atom_condition_model_consumption_gate_v1.py"
_TERMINAL_SOURCE = "src/covalent_ext/covapie_bounded_repository_cli_conditioned_runtime_smoke_v1.py"
_BOUND_REPOSITORY_PATHS = (
    "lightning_modules.py", "equivariant_diffusion/dynamics.py",
    "equivariant_diffusion/en_diffusion.py", "equivariant_diffusion/conditional_model.py",
    "dataset.py", "train.py", "scripts/covalent_inpaint_demo.py",
    "configs/crossdock_fullatom_cond.yml", "src/covalent_ext/schema.py",
    "src/covalent_ext/masking.py", "src/covalent_ext/npz_dataset.py",
    "src/covalent_ext/batch_adapter.py",
    "src/covalent_ext/masked_loss_adapter_design.py",
    "src/covalent_ext/diffsbdd_atomwise_loss_hook_design.py",
    _FEATURE_AUDIT_SOURCE, _FEATURE_AUDIT_MANIFEST,
    _FEATURE_RESOLUTION_SOURCE, _FEATURE_RESOLUTION_MANIFEST,
    _TENSOR_SOURCE, _TENSOR_REGISTRY, _READINESS_SOURCE, _WARHEAD_SOURCE,
    _ROLE_SOURCE, _PAIR_SOURCE, _TARGET_AUTHORITY_SOURCE, _TARGET_ADAPTER_SOURCE,
    _TARGET_GATE_SOURCE, _TERMINAL_SOURCE,
    "src/covalent_ext/covapie_target_residue_atom_condition_adapter_gate_v1.py",
    "src/covalent_ext/covapie_target_residue_atom_condition_checkpoint_migration_v1.py",
    "src/covalent_ext/covapie_legacy_four_level_mask_retirement_gate_v1.py",
    "docs/covapie_tensor_label_and_loss_mask_contract_design_v1_summary.md",
    "docs/covapie_current11_five_auxiliary_module_label_consumption_readiness_design_v1_guide.md",
    "docs/covapie_target_residue_atom_condition_model_consumption_gate_v1_guide.md",
    "docs/covapie_bounded_repository_cli_conditioned_runtime_smoke_v1_guide.md",
)

_FORMAL_STATE_FILES = (
    ("covapie_current11_target_residue_atom_condition_authority_bundle_v1.json", "a95ae52e091a7117b241269eebd891f3ee97e3ae4a6b4e14fa441ab6a1ed2096"),
    ("covapie_current11_target_residue_atom_condition_adapter_bundle_v1.json", "983c25ea8c52ca54f0c0292990a625e9a9cf0d2370cb517d66a84801d957b65a"),
    ("covapie_current11_target_residue_atom_condition_adapter_gate_bundle_v1.json", "c7e2c9eec92d560fc55206399d9b27df511733821ce3233c3546da38d9992a9d"),
    ("covapie_current11_target_residue_atom_condition_runtime_bridge_gate_bundle_v1.json", "835032d1b0a9d9af9abe0839e9be798f0d4f178bcd9d4af3323592c5e59aa597"),
    ("covapie_current11_target_residue_atom_condition_model_consumption_gate_bundle_v1.json", "18edfbc312128315fd9c880e750aeccc41132b34c20c8e34d78a974e39a2c9aa"),
    ("covapie_current11_unified_effective_authority_view_v1.json", "f4178987f3c3eed0e248f6d3d5f22cb8bce1839d39ab08aff0bff9d2ef9f3774"),
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False,
                          separators=(",", ":")).encode("utf-8")
    except Exception as error:
        raise ValueError(_ERROR) from error


def _run_git(repo_root: Path, arguments: Sequence[str], *, allow_one: bool = False) -> tuple[int, bytes, bytes]:
    completed = subprocess.run(["git", *arguments], cwd=repo_root,
        env={**os.environ, "LC_ALL": "C", "LANG": "C"}, check=False,
        capture_output=True, timeout=30)
    allowed = (0, 1) if allow_one else (0,)
    if completed.returncode not in allowed:
        raise ValueError(_ERROR)
    return completed.returncode, completed.stdout, completed.stderr


def _git(repo_root: Path, arguments: Sequence[str]) -> bytes:
    rc, stdout, stderr = _run_git(repo_root, arguments)
    if rc or stderr:
        raise ValueError(_ERROR)
    return stdout


def _git_text(repo_root: Path, arguments: Sequence[str]) -> str:
    try:
        return _git(repo_root, arguments).decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ValueError(_ERROR) from error


def _is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    rc, stdout, stderr = _run_git(
        repo_root, ["merge-base", "--is-ancestor", ancestor, descendant], allow_one=True)
    if stdout or stderr:
        raise ValueError(_ERROR)
    return rc == 0


def _snapshot_bytes(repo_root: Path, path: str) -> bytes:
    payload = _git(repo_root, ["show", f"{_SOURCE_SNAPSHOT}:{path}"])
    if not payload:
        raise ValueError(_ERROR)
    return payload


def _literal_assignment(tree: ast.Module, name: str) -> object:
    values: list[ast.expr] = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            values.append(node.value)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == name and node.value is not None:
            values.append(node.value)
    if len(values) != 1:
        raise ValueError(_ERROR)
    try:
        return ast.literal_eval(values[0])
    except Exception as error:
        raise ValueError(_ERROR) from error


def _derive_audit_lifecycle(facts: Mapping[str, Any]) -> dict[str, object]:
    """Derive one valid lifecycle profile from synthetic or live Git facts."""
    try:
        if type(facts) is not dict or facts.get("source_ancestor_head") is not True or facts.get("source_ancestor_origin") is not True:
            raise ValueError(_ERROR)
        commits = facts["path_commits"]
        if type(commits) is not list or len(commits) > 1:
            raise ValueError(_ERROR)
        untracked = tuple(facts["ordinary_untracked"])
        worktree_dirty = tuple(facts["worktree_dirty"])
        staged_dirty = tuple(facts["staged_dirty"])
        live = facts["live_paths"]
        if type(live) is not dict or tuple(live) != _AUDIT_PATHS:
            raise ValueError(_ERROR)

        if not commits:
            if (
                facts["head"] != _SOURCE_SNAPSHOT
                or facts["origin"] != _SOURCE_SNAPSHOT
                or (facts["ahead"], facts["behind"]) != (0, 0)
                or untracked != _AUDIT_PATHS
                or worktree_dirty or staged_dirty
                or any(item != {"tracked": False, "mode": "100644", "blob": item["blob"]}
                       or re.fullmatch(r"[0-9a-f]{40}", item["blob"]) is None
                       for item in live.values())
            ):
                raise ValueError(_ERROR)
            return {"audit_lifecycle_profile": "audit_precommit_candidate",
                    "audit_commit": None, "audit_committed": False,
                    "audit_published": False, "ready_for_audit_commit_review": True}

        commit = commits[0]
        if (
            type(commit) is not dict
            or commit.get("subject") != _AUDIT_COMMIT_SUBJECT
            or commit.get("parents") != [_SOURCE_SNAPSHOT]
            or tuple(commit.get("changed_paths", ())) != _AUDIT_PATHS
            or tuple(commit.get("path_modes", {})) != _AUDIT_PATHS
            or tuple(commit.get("path_blobs", {})) != _AUDIT_PATHS
            or any(commit["path_modes"][path] != "100644" for path in _AUDIT_PATHS)
            or any(re.fullmatch(r"[0-9a-f]{40}", commit["path_blobs"][path]) is None for path in _AUDIT_PATHS)
            or re.fullmatch(r"[0-9a-f]{40}", commit.get("commit", "")) is None
            or any(live[path] != {"tracked": True, "mode": "100644", "blob": commit["path_blobs"][path]} for path in _AUDIT_PATHS)
            or any(path in untracked or path in worktree_dirty or path in staged_dirty for path in _AUDIT_PATHS)
            or facts.get("audit_ancestor_head") is not True
        ):
            raise ValueError(_ERROR)
        if facts.get("audit_ancestor_origin") is True:
            return {"audit_lifecycle_profile": "audit_published_successor",
                    "audit_commit": commit["commit"], "audit_committed": True,
                    "audit_published": True, "ready_for_audit_commit_review": False}
        if (
            facts["head"] != commit["commit"] or facts["origin"] != _SOURCE_SNAPSHOT
            or (facts["ahead"], facts["behind"]) != (1, 0)
            or facts.get("repository_clean") is not True
        ):
            raise ValueError(_ERROR)
        return {"audit_lifecycle_profile": "audit_committed_unpushed",
                "audit_commit": commit["commit"], "audit_committed": True,
                "audit_published": False, "ready_for_audit_commit_review": False}
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _collect_lifecycle(repo_root: Path) -> dict[str, object]:
    head = _git_text(repo_root, ["rev-parse", "HEAD"]).strip()
    origin = _git_text(repo_root, ["rev-parse", "refs/remotes/origin/main"]).strip()
    ahead, behind = (int(value) for value in _git_text(
        repo_root, ["rev-list", "--left-right", "--count", "HEAD...refs/remotes/origin/main"]).split())
    revisions = set(_git_text(repo_root, ["rev-list", f"{_SOURCE_SNAPSHOT}..{head}"]).splitlines())
    revisions.update(_git_text(repo_root, ["rev-list", f"{_SOURCE_SNAPSHOT}..{origin}"]).splitlines())
    path_commits: list[dict[str, object]] = []
    for commit_hash in sorted(revisions):
        changed = tuple(sorted(set(_git_text(
            repo_root, ["diff-tree", "--root", "--no-commit-id", "--name-only", "-r", commit_hash]
        ).splitlines()).intersection(_AUDIT_PATHS)))
        if not changed:
            continue
        all_changed = tuple(_git_text(repo_root, ["diff-tree", "--root", "--no-commit-id", "--name-only", "-r", commit_hash]).splitlines())
        modes: dict[str, str] = {}
        blobs: dict[str, str] = {}
        for path in _AUDIT_PATHS:
            line = _git_text(repo_root, ["ls-tree", commit_hash, "--", path]).strip()
            if line:
                metadata, listed = line.split("\t", 1)
                mode, object_type, blob = metadata.split()
                if listed != path or object_type != "blob":
                    raise ValueError(_ERROR)
                modes[path] = mode
                blobs[path] = blob
        path_commits.append({
            "commit": commit_hash,
            "parents": _git_text(repo_root, ["show", "-s", "--format=%P", commit_hash]).split(),
            "subject": _git_text(repo_root, ["show", "-s", "--format=%s", commit_hash]).strip(),
            "changed_paths": list(all_changed), "path_modes": modes, "path_blobs": blobs,
        })
    ordinary = tuple(_git_text(repo_root, ["ls-files", "--others", "--exclude-standard"]).splitlines())
    worktree_dirty = tuple(_git_text(repo_root, ["diff", "--name-only"]).splitlines())
    staged_dirty = tuple(_git_text(repo_root, ["diff", "--cached", "--name-only"]).splitlines())
    live: dict[str, dict[str, object]] = {}
    for path in _AUDIT_PATHS:
        full = repo_root / path
        try:
            mode = full.lstat().st_mode
        except OSError as error:
            raise ValueError(_ERROR) from error
        if not stat.S_ISREG(mode) or full.is_symlink():
            raise ValueError(_ERROR)
        tracked_rc, _, tracked_stderr = _run_git(repo_root, ["ls-files", "--error-unmatch", "--", path], allow_one=True)
        if tracked_rc == 0 and tracked_stderr:
            raise ValueError(_ERROR)
        live[path] = {"tracked": tracked_rc == 0, "mode": "100755" if mode & stat.S_IXUSR else "100644",
                      "blob": _git_text(repo_root, ["hash-object", "--", path]).strip()}
    facts = {
        "head": head, "origin": origin, "ahead": ahead, "behind": behind,
        "source_ancestor_head": _is_ancestor(repo_root, _SOURCE_SNAPSHOT, head),
        "source_ancestor_origin": _is_ancestor(repo_root, _SOURCE_SNAPSHOT, origin),
        "path_commits": path_commits, "ordinary_untracked": ordinary,
        "worktree_dirty": worktree_dirty, "staged_dirty": staged_dirty,
        "live_paths": live,
        "repository_clean": not _git_text(repo_root, ["status", "--porcelain=v1", "--untracked-files=all"]),
    }
    if path_commits:
        audit_hash = path_commits[0]["commit"]
        facts["audit_ancestor_head"] = _is_ancestor(repo_root, audit_hash, head)
        facts["audit_ancestor_origin"] = _is_ancestor(repo_root, audit_hash, origin)
    return _derive_audit_lifecycle(facts)


def _validate_static_repository(repo_root: Path) -> dict[str, object]:
    if type(repo_root) is not type(Path()) or not repo_root.is_dir() or repo_root.is_symlink() or repo_root.resolve(strict=True) != repo_root:
        raise ValueError(_ERROR)
    if (_git_text(repo_root, ["show", "-s", "--format=%s", _SOURCE_SNAPSHOT]).strip() != _SOURCE_SUBJECT
            or _git_text(repo_root, ["rev-parse", f"{_SOURCE_SNAPSHOT}^{{tree}}"]).strip() != _SOURCE_TREE):
        raise ValueError(_ERROR)
    lifecycle = _collect_lifecycle(repo_root)
    commits = {value for key, value in globals().items() if key.startswith("_C_") and type(value) is str}
    if any(re.fullmatch(r"[0-9a-f]{40}", commit) is None or not _is_ancestor(repo_root, commit, _SOURCE_SNAPSHOT) for commit in commits):
        raise ValueError(_ERROR)
    if any(
        _git_text(repo_root, ["show", "-s", "--format=%s", commit]).strip()
        != subject
        for commit, subject in _FORMAL_COMMIT_SUBJECTS.items()
    ):
        raise ValueError(_ERROR)
    for path in _BOUND_REPOSITORY_PATHS:
        _snapshot_bytes(repo_root, path)

    resolution = json.loads(_snapshot_bytes(repo_root, _FEATURE_RESOLUTION_MANIFEST))
    if any((
        resolution.get("feature_semantics_audit_completed") is not True,
        resolution.get("unknown_atom_policy_contract_resolved") is not True,
        resolution.get("feature_semantics_known") is not True,
        resolution.get("protein_unknown_atom_policy") != "fail_closed_rejection_required_for_checkpoint_compatibility",
        resolution.get("ligand_unknown_atom_policy") != "fail_closed_rejection_required_for_checkpoint_compatibility",
        resolution.get("checkpoint_categorical_width") != 10,
        resolution.get("checkpoint_channel_order_preserved") is not True,
        resolution.get("silent_zero_vector_fallback_allowed") is not False,
        resolution.get("unknown_atom_runtime_enforcement_integrated") is not False,
        resolution.get("ready_for_tensorization") is not False,
        resolution.get("ready_for_model_integration") is not False,
        resolution.get("ready_for_training") is not False,
    )):
        raise ValueError(_ERROR)
    audit = json.loads(_snapshot_bytes(repo_root, _FEATURE_AUDIT_MANIFEST))
    if audit.get("feature_semantics_audit_completed") is not True or audit.get("step12d_final_feature_semantics_contract") is not False or audit.get("step12d_smoke_legality_verified") is not True:
        raise ValueError(_ERROR)
    readiness_tree = ast.parse(_snapshot_bytes(repo_root, _READINESS_SOURCE).decode("utf-8"))
    if _literal_assignment(readiness_tree, "_SIGNAL_NAMES") != _SIGNAL_NAMES:
        raise ValueError(_ERROR)
    tensor = _snapshot_bytes(repo_root, _TENSOR_SOURCE).decode("utf-8")
    required_tokens = (
        '"cross_sample_negatives_allowed": False', '"random_negative_sampling_allowed": False',
        '"hard_negative_mining_allowed": False', "pair_contrastive_sample_loss_mask",
        "pair contrastive loss",
    )
    if any(token not in tensor for token in required_tokens):
        raise ValueError(_ERROR)
    return lifecycle


def _dimension(status: str, paths: Sequence[str], commits: Sequence[str], summary: str,
               gap: str = "", blocking: bool = False) -> dict[str, object]:
    return {"status": status, "evidence_paths": list(paths), "evidence_commits": list(commits),
            "evidence_summary": summary, "remaining_gap": gap,
            "blocking_for_training": blocking}


def _matrix(spec: Mapping[str, tuple[str, Sequence[str], Sequence[str], str, str, bool]]) -> dict[str, object]:
    return {dimension: _dimension(*spec[dimension]) for dimension in _DIMENSIONS}


def _target_matrix() -> dict[str, object]:
    authority = (_TARGET_AUTHORITY_SOURCE,)
    adapter = (_TARGET_ADAPTER_SOURCE, "src/covalent_ext/covapie_target_residue_atom_condition_adapter_gate_v1.py")
    model = ("lightning_modules.py", "equivariant_diffusion/dynamics.py", "equivariant_diffusion/en_diffusion.py", "equivariant_diffusion/conditional_model.py")
    gate = (_TARGET_GATE_SOURCE, "docs/covapie_target_residue_atom_condition_model_consumption_gate_v1_guide.md")
    return _matrix({
        "semantic_contract": ("complete", authority, (_C_TARGET_CONTRACT, _C_TARGET_AUTHORITY), "Exact target residue/atom identity is frozen.", "", False),
        "source_data_or_authority": ("complete", authority, (_C_TARGET_AUTHORITY,), "SHA-bound authority covers Current11.", "", False),
        "schema_fields": ("complete", authority + adapter, (_C_TARGET_AUTHORITY, _C_TARGET_ADAPTER), "Selector and per-pocket-node indicator schemas are frozen.", "", False),
        "label_compilation": ("complete", adapter, (_C_TARGET_ADAPTER, _C_TARGET_ADAPTER_GATE), "The adapter compiles one retained target atom per sample.", "", False),
        "materialized_dataset": ("partial", adapter, (_C_TARGET_ADAPTER_GATE,), "Formal bundles exist, but no admitted train/val/test sidecar exists.", "Materialize the split-bound indicator sidecar.", True),
        "dataset_loading": ("complete", ("dataset.py",) + adapter, (_C_TARGET_ADAPTER_GATE,), "The existing dataset path carries the indicator.", "", False),
        "collate_or_batch_contract": ("complete", ("dataset.py",) + adapter, (_C_TARGET_ADAPTER_GATE,), "Concatenation preserves dtype and sample boundaries.", "", False),
        "model_input_or_condition": ("complete", model, (_C_TARGET_RUNTIME, _C_TARGET_MODEL), "The indicator reaches the target embedding.", "", False),
        "model_head_or_output": ("not_applicable", model, (_C_TARGET_MODEL,), "This module is an input adapter, not a prediction head.", "", False),
        "forward_consumption": ("complete", model, (_C_TARGET_MODEL, _C_TARGET_MODEL_GATE), "Frozen forward call sites consume the condition.", "", False),
        "supervised_loss": ("not_applicable", model, (_C_TARGET_MODEL,), "No independent adapter loss is required.", "", False),
        "loss_weight_or_config": ("partial", ("train.py", "configs/crossdock_fullatom_cond.yml"), (_C_TARGET_MODEL,), "The constructor capability exists but formal training config is absent.", "Add fail-closed enablement after prerequisites.", True),
        "checkpoint_compatibility": ("complete", ("src/covalent_ext/covapie_target_residue_atom_condition_checkpoint_migration_v1.py",) + gate, (_C_TARGET_MODEL, _C_TARGET_MODEL_GATE), "Disabled strict-load and zero-initialized migration profiles are gated.", "", False),
        "unit_tests": ("complete", gate, (_C_TARGET_MODEL_GATE, _C_CLI_GATE), "Threading, migration, and CLI negative paths are bound.", "", False),
        "formal_gate": ("complete", gate, (_C_TARGET_MODEL_GATE, _C_CLI_GATE), "Adapter through CLI successor gates exist.", "", False),
        "real_runtime_evidence": ("blocked", (_TERMINAL_SOURCE, "docs/covapie_bounded_repository_cli_conditioned_runtime_smoke_v1_guide.md"), (_SOURCE_SNAPSHOT,), "The one authorized run stopped before Exact67.", "New authorization is required for re-execution.", True),
        "training_readiness": ("blocked", ("train.py", _FEATURE_RESOLUTION_MANIFEST), (_SOURCE_SNAPSHOT, _C_FEATURE_RESOLUTION), "Dataset/config, Exact67, runtime enforcement, and final feature revalidation remain incomplete.", "Close those gates before training.", True),
    })


def _role_matrix() -> dict[str, object]:
    contract = (_ROLE_SOURCE, _TENSOR_SOURCE, "src/covalent_ext/masking.py", "src/covalent_ext/schema.py")
    runtime = ("scripts/covalent_inpaint_demo.py", "src/covalent_ext/covapie_legacy_four_level_mask_retirement_gate_v1.py")
    training = ("src/covalent_ext/npz_dataset.py", "src/covalent_ext/batch_adapter.py", "src/covalent_ext/masked_loss_adapter_design.py", "src/covalent_ext/diffsbdd_atomwise_loss_hook_design.py")
    return _matrix({
        "semantic_contract": ("complete", contract, (_C_ROLE_CONTRACT, _C_TENSOR_CONTRACT), "Five masks, per-atom roles, minimal seed, task-C anchor, anchor distance, and generated/fixed semantics are designed.", "", False),
        "source_data_or_authority": ("partial", (_ROLE_SOURCE, _READINESS_SOURCE), (_C_ROLE_CONTRACT, _C_FIVE_READINESS), "Warhead authority exists; full scaffold/linker/anchor authority does not.", "Freeze Current11 per-atom roles and task-C anchor authority.", True),
        "schema_fields": ("partial", contract, (_C_ROLE_CONTRACT, _C_TENSOR_CONTRACT), "Role, anchor, task ID, generated/fixed, and distance fields are designed but not final-dataset fields.", "Bind them to a final schema.", True),
        "label_compilation": ("partial", contract + runtime, (_C_ROLE_CONTRACT, _C_MASK_R2), "Compilation rules exist without admitted complete role inputs.", "Compile only from approved authority.", True),
        "materialized_dataset": ("missing", (), (), "No admitted dataset materializes all five masks, roles, anchors, and distances.", "Materialize deterministic sidecars.", True),
        "dataset_loading": ("partial", training, (_C_NPZ_LOADER, _C_MASK_R2), "Extension loaders carry prototypes, not the active canonical contract.", "Integrate the active loader.", True),
        "collate_or_batch_contract": ("partial", training + (_TENSOR_SOURCE,), (_C_TENSOR_CONTRACT,), "Offsets and shapes are designed, not formally gated in a real batch.", "Gate flattened batches and mask partitions.", True),
        "model_input_or_condition": ("partial", runtime + training, (_C_MASK_R1, _C_ATOMWISE_LOSS), "Generation and prototypes consume masks; training lacks canonical selection and anchor encoding.", "Thread roles/masks/anchor distance into training.", True),
        "model_head_or_output": ("not_applicable", runtime, (_C_MASK_R1,), "This is an encoding, not a prediction head.", "", False),
        "forward_consumption": ("partial", runtime + ("equivariant_diffusion/en_diffusion.py",), (_C_MASK_R1,), "Inpainting consumes regions; ordinary training does not consume the full encoding.", "Add gated training consumption.", True),
        "supervised_loss": ("partial", training, (_C_MASKED_LOSS, _C_ATOMWISE_LOSS, _C_B3_SMOKE), "Prototype masked diffusion loss includes B3 but production Lightning loss is unchanged.", "Apply active loss only to generated atoms for all five tasks.", True),
        "loss_weight_or_config": ("partial", ("src/covalent_ext/masked_loss_adapter_design.py", "configs/crossdock_fullatom_cond.yml"), (_C_MASKED_LOSS,), "No production task sampling/weight configuration exists.", "Freeze task sampling and region-loss config.", True),
        "checkpoint_compatibility": ("complete", runtime + training, (_C_B3_SMOKE, _C_MASK_R1), "Sidecars preserve the checkpoint input contract.", "", False),
        "unit_tests": ("partial", runtime + (_ROLE_SOURCE,), (_C_ROLE_CONTRACT, _C_MASK_R1, _C_MASK_R2, _C_MASK_R3), "Contract and generation tests exist, not final batch-to-loss tests.", "Add fail-closed integrated tests.", True),
        "formal_gate": ("partial", ("src/covalent_ext/covapie_legacy_four_level_mask_retirement_gate_v1.py", _ROLE_SOURCE), (_C_ROLE_CONTRACT, _C_MASK_R3), "Legacy retirement is gated; complete role/anchor materialization is not.", "Add successor materialization gate.", True),
        "real_runtime_evidence": ("partial", runtime + training, (_C_B3_SMOKE, _C_MASK_R1), "Narrow historical smokes are not five-task training evidence.", "Obtain bounded evidence only after integration.", False),
        "training_readiness": ("blocked", (_ROLE_SOURCE, _TENSOR_SOURCE), (_C_ROLE_CONTRACT, _C_TENSOR_CONTRACT), "Authority, materialization, active loader/forward/loss, runtime enforcement, and revalidation remain incomplete.", "Resolve the role/task-mask materialization contract first.", True),
    })


def _pair_matrix() -> dict[str, object]:
    source = (_PAIR_SOURCE, _TENSOR_SOURCE)
    return _matrix({
        "semantic_contract": ("complete", source, (_C_PAIR_DESIGN, _C_PAIR_VALIDATION, _C_TENSOR_CONTRACT), "Positive pair and candidate-index semantics are frozen.", "", False),
        "source_data_or_authority": ("complete", (_PAIR_SOURCE,), (_C_PAIR_VALIDATION,), "Current11 positive ligand/residue atom mapping validates 11/11.", "", False),
        "schema_fields": ("complete", source, (_C_PAIR_VALIDATION, _C_TENSOR_CONTRACT), "Candidate indices, offsets, positive index, validity, and loss mask are designed.", "", False),
        "label_compilation": ("partial", source, (_C_TENSOR_CONTRACT,), "Metadata builders exist but do not emit admitted tensors.", "Compile candidates and positives into split-bound tensors.", True),
        "materialized_dataset": ("partial", (_PAIR_SOURCE,), (_C_PAIR_VALIDATION,), "Validated metadata exists, not model-facing tensors.", "Materialize pair sidecars.", True),
        "dataset_loading": ("missing", (), (), "No active loader reads candidate-pair tensors.", "Implement loader support.", True),
        "collate_or_batch_contract": ("missing", (), (), "No real batch collates pair candidates and offsets.", "Implement and gate collation.", True),
        "model_input_or_condition": ("missing", (), (), "No candidate pair representation enters the model.", "Design a checkpoint-compatible representation.", True),
        "model_head_or_output": ("missing", (), (), "No pair-scoring head or logits exist.", "Add only after label integration.", True),
        "forward_consumption": ("missing", (), (), "No forward path emits pair logits.", "Thread optional pair output.", True),
        "supervised_loss": ("missing", (), (), "No pair-head supervised objective exists.", "Implement masked positive-pair loss separately from contrastive loss.", True),
        "loss_weight_or_config": ("missing", (), (), "No pair-head weight or enable flag exists.", "Freeze disabled-default config.", True),
        "checkpoint_compatibility": ("blocked", (_TENSOR_SOURCE,), (_C_TENSOR_CONTRACT,), "No migration contract exists for an absent head.", "Define strict disabled and migration profiles.", True),
        "unit_tests": ("partial", source, (_C_PAIR_VALIDATION, _C_TENSOR_CONTRACT), "Metadata and tensor-contract tests exist; model tests do not.", "Add head/forward/loss negative tests later.", True),
        "formal_gate": ("partial", source, (_C_PAIR_VALIDATION, _C_TENSOR_CONTRACT), "Authority and design gates exist without implementation gate.", "Add a successor implementation gate.", True),
        "real_runtime_evidence": ("missing", (), (), "No pair-head runtime evidence exists.", "Defer until the path exists.", False),
        "training_readiness": ("blocked", source, (_C_PAIR_VALIDATION, _C_TENSOR_CONTRACT), "Pair tensors, head, forward, loss, config, and compatibility are incomplete.", "Materialize pair tensors before head work.", True),
    })


def _geometry_matrix() -> dict[str, object]:
    source = (_READINESS_SOURCE, _TENSOR_SOURCE)
    entries = {
        "semantic_contract": ("partial", source, (_C_FIVE_READINESS, _C_TENSOR_CONTRACT), "Component and validity shapes are designed; a complete pre/post target is not authoritative.", "Freeze components, units, frame, periodicity, and sentinel policy.", True),
        "source_data_or_authority": ("partial", (_READINESS_SOURCE,), (_C_FIVE_READINESS,), "Post-covalent distance covers 11/11; complete pre/post authority covers 0/11.", "Acquire or formally derive pre-covalent geometry.", True),
        "schema_fields": ("partial", source, (_C_TENSOR_CONTRACT,), "Geometry values, masks, and validity fields are designed, not final.", "Finalize against authority.", True),
        "label_compilation": ("missing", (), (), "No compiler emits complete geometry labels.", "Implement after authority closure.", True),
        "materialized_dataset": ("missing", (), (), "No complete geometry tensor sidecar exists.", "Materialize after compilation.", True),
        "dataset_loading": ("missing", (), (), "No active loader reads complete geometry targets.", "Implement loader support later.", True),
        "collate_or_batch_contract": ("missing", (), (), "No real batch collates complete geometry targets.", "Gate values and masks later.", True),
        "model_input_or_condition": ("partial", (_TENSOR_SOURCE,), (_C_TENSOR_CONTRACT,), "A future output contract is sketched, not consumed.", "Freeze the representation.", True),
        "model_head_or_output": ("missing", (), (), "No geometry head exists.", "Design after labels.", True),
        "forward_consumption": ("missing", (), (), "No geometry output is threaded.", "Add only with an optional head.", True),
        "supervised_loss": ("missing", (), (), "No component-aware geometry loss exists.", "Define masked losses after authority.", True),
        "loss_weight_or_config": ("missing", (), (), "No geometry weights or enable flag exist.", "Freeze disabled-default config.", True),
        "checkpoint_compatibility": ("blocked", (_TENSOR_SOURCE,), (_C_TENSOR_CONTRACT,), "No absent-head migration contract exists.", "Define compatibility profiles.", True),
        "unit_tests": ("partial", source, (_C_TENSOR_CONTRACT, _C_FIVE_READINESS), "Design validation exists without compiler/model tests.", "Add tests after each bounded increment.", True),
        "formal_gate": ("partial", source, (_C_TENSOR_CONTRACT, _C_FIVE_READINESS), "Readiness/design gates explicitly block implementation.", "Add authority successor first.", True),
        "real_runtime_evidence": ("missing", (), (), "No geometry-head runtime evidence exists.", "Defer until implementation.", False),
        "training_readiness": ("blocked", source, (_C_TENSOR_CONTRACT, _C_FIVE_READINESS), "Authority and the entire loader-to-loss path are incomplete.", "Resolve geometry authority first.", True),
    }
    return _matrix(entries)


def _contrastive_matrix() -> dict[str, object]:
    source = (_PAIR_SOURCE, _TENSOR_SOURCE)
    return _matrix({
        "semantic_contract": ("complete", source, (_C_PAIR_VALIDATION, _C_TENSOR_CONTRACT), "Positive pairs, same-sample deterministic negatives, ordering, offsets, masks, and zero-negative behavior are frozen.", "", False),
        "source_data_or_authority": ("complete", source, (_C_PAIR_VALIDATION, _C_TENSOR_CONTRACT), "Current11 positives cover 11/11 and the negative domain is contract-bound.", "", False),
        "schema_fields": ("complete", (_TENSOR_SOURCE, _TENSOR_REGISTRY), (_C_TENSOR_CONTRACT,), "Negative order, offsets, and pair_contrastive_sample_loss_mask are frozen.", "", False),
        "label_compilation": ("partial", source, (_C_TENSOR_CONTRACT,), "A deterministic builder is designed but not admitted as training tensors.", "Compile same-sample negatives with fail-closed masks.", True),
        "materialized_dataset": ("partial", (_PAIR_SOURCE,), (_C_PAIR_VALIDATION,), "Positive metadata exists; contrastive tensors do not.", "Materialize candidates, negatives, offsets, and masks.", True),
        "dataset_loading": ("missing", (), (), "No active loader reads contrastive tensors.", "Implement loader support.", True),
        "collate_or_batch_contract": ("missing", (), (), "No real batch gates negative offsets/order.", "Implement leakage-safe collation.", True),
        "model_input_or_condition": ("missing", (), (), "The loss has no pair logits to consume.", "Depend explicitly on the pair-head output.", True),
        "model_head_or_output": ("not_applicable", source, (_C_TENSOR_CONTRACT,), "Contrastive loss consumes pair-head logits and is not a sixth head.", "", False),
        "forward_consumption": ("missing", (), (), "Pair logits are absent, so forward cannot feed the objective.", "Implement the pair head first.", True),
        "supervised_loss": ("missing", (), (), "No production contrastive objective exists; a loss mask design is not an implemented loss.", "Implement masked objective and zero-negative behavior after pair logits.", True),
        "loss_weight_or_config": ("missing", (), (), "No contrastive weight or enable policy exists.", "Freeze disabled-default configuration.", True),
        "checkpoint_compatibility": ("blocked", source, (_C_TENSOR_CONTRACT,), "Compatibility depends on the absent pair head and objective config.", "Gate the dependency and migration profile.", True),
        "unit_tests": ("partial", source, (_C_TENSOR_CONTRACT,), "Contract tests bind random=false, hard=false, cross-sample=false, masks, and zero-negative cases.", "Add implemented objective tests later.", True),
        "formal_gate": ("partial", source, (_C_TENSOR_CONTRACT,), "The design gate freezes policy but does not approve implementation/training.", "Add successor gates after tensors and pair head.", True),
        "real_runtime_evidence": ("missing", (), (), "No contrastive objective runtime evidence exists.", "Defer until implementation.", False),
        "training_readiness": ("blocked", source, (_C_PAIR_VALIDATION, _C_TENSOR_CONTRACT), "Tensors, pair logits, objective, weight, compatibility, and final feature gates are incomplete.", "Materialize pair tensors, then pair head, then contrastive loss.", True),
    })


def _signal(status: str, coverage: str, paths: Sequence[str], commits: Sequence[str],
            consumer: str, gap: str, modules: Sequence[str], approved: bool) -> dict[str, object]:
    return {"status": status, "authority_coverage": coverage, "evidence_paths": list(paths),
            "evidence_commits": list(commits), "model_consumer": consumer,
            "remaining_gap": gap, "blocking_modules": list(modules),
            "training_approved": approved}


def _signals() -> dict[str, object]:
    return {
        "warhead_type_identity": _signal("partial", "11/11", (_WARHEAD_SOURCE, _READINESS_SOURCE), (_C_WARHEAD, _C_FIVE_READINESS), "unresolved:future_optional_head_or_condition_encoding_or_evaluation_only", "WARHEAD_TYPE_SUPERVISION_MODEL_CONSUMER_UNRESOLVED; training vocabulary not frozen; unknown-label policy not final", ("role_mask_anchor_distance_encoding",), False),
        "warhead_atom_set": _signal("complete", "11/11", (_WARHEAD_SOURCE, _READINESS_SOURCE), (_C_WARHEAD, _C_FIVE_READINESS), "role_mask_anchor_distance_encoding", "Authority is ready, but full role/mask materialization is not.", ("role_mask_anchor_distance_encoding",), False),
        "ligand_internal_warhead_boundary": _signal("complete", "11/11", (_WARHEAD_SOURCE, _READINESS_SOURCE), (_C_WARHEAD, _C_FIVE_READINESS), "role_mask_anchor_distance_encoding", "Boundary authority is not yet compiled into canonical task tensors.", ("role_mask_anchor_distance_encoding",), False),
        "target_residue_atom_condition": _signal("complete", "11/11", (_TARGET_AUTHORITY_SOURCE, _TARGET_ADAPTER_SOURCE), (_C_TARGET_AUTHORITY, _C_TARGET_ADAPTER), "target_residue_atom_condition_adapter", "No admitted split-bound training sidecar exists.", ("target_residue_atom_condition_adapter",), False),
        "ligand_atom_to_residue_atom_pair": _signal("partial", "11/11", (_PAIR_SOURCE, _TENSOR_SOURCE), (_C_PAIR_VALIDATION, _C_TENSOR_CONTRACT), "ligand_residue_atom_pair_prediction_head;ligand_residue_pair_contrastive_loss", "Validated metadata is not tensorized or consumed by a head.", ("ligand_residue_atom_pair_prediction_head", "ligand_residue_pair_contrastive_loss"), False),
        "pre_post_covalent_geometry": _signal("partial", "post_distance=11/11;complete_pre_post=0/11", (_READINESS_SOURCE, _TENSOR_SOURCE), (_C_FIVE_READINESS, _C_TENSOR_CONTRACT), "pre_post_covalent_geometry_prediction_head", "Complete pre-covalent authority, tensors, head, and loss are absent.", ("pre_post_covalent_geometry_prediction_head",), False),
        "scaffold_linker_anchor_atom_roles": _signal("partial", "warhead_atom_set=11/11;complete_roles_and_task_C_anchor=0/11", (_ROLE_SOURCE, _READINESS_SOURCE), (_C_ROLE_CONTRACT, _C_FIVE_READINESS), "role_mask_anchor_distance_encoding", "Approved scaffold/linker/anchor roles and task-C anchor authority are incomplete.", ("role_mask_anchor_distance_encoding",), False),
        "contrastive_negative_sampling_policy": _signal("partial", "policy_contract=1/1;current11_positive_pairs=11/11", (_TENSOR_SOURCE, _PAIR_SOURCE), (_C_TENSOR_CONTRACT, _C_PAIR_VALIDATION), "ligand_residue_pair_contrastive_loss", "Same-sample deterministic policy is frozen, but leakage grouping, tensors, pair logits, objective, and weight are not integrated.", ("ligand_residue_atom_pair_prediction_head", "ligand_residue_pair_contrastive_loss"), False),
    }


def _queue_item(priority: str, module: str, dimension: str, gap: str, why: str,
                increment: str, components: Sequence[str]) -> dict[str, object]:
    return {"priority": priority, "module": module, "dimension": dimension, "gap": gap,
            "why_it_blocks": why, "smallest_verifiable_increment": increment,
            "expected_files_or_components": list(components),
            "training_or_parameter_update_required": False}


def _build_response(lifecycle: Mapping[str, object]) -> dict[str, object]:
    matrix = {
        "target_residue_atom_condition_adapter": _target_matrix(),
        "role_mask_anchor_distance_encoding": _role_matrix(),
        "ligand_residue_atom_pair_prediction_head": _pair_matrix(),
        "pre_post_covalent_geometry_prediction_head": _geometry_matrix(),
        "ligand_residue_pair_contrastive_loss": _contrastive_matrix(),
    }
    signals = _signals()
    count_maps = {status: {module: sum(row["status"] == status for row in matrix[module].values()) for module in _MODULE_NAMES} for status in _STATUSES}
    summary = {}
    for module in _MODULE_NAMES:
        decisive = [name for name, row in matrix[module].items() if row["blocking_for_training"] and row["status"] != "complete"]
        ready = matrix[module]["training_readiness"]["status"] == "complete" and not decisive
        summary[module] = {"training_ready": ready, "conclusion": "ready" if ready else "not_ready_incomplete_training_path", "decisive_gaps": decisive}
    training_ready_count = sum(item["training_ready"] for item in summary.values())
    signal_summary = {
        "complete_signal_count": sum(row["status"] == "complete" for row in signals.values()),
        "partial_signal_count": sum(row["status"] == "partial" for row in signals.values()),
        "training_approved_signal_count": sum(row["training_approved"] for row in signals.values()),
        "conclusion": "authority_signals_exist_but_no_signal_layer_is_approved_for_training",
    }
    queue = [
        _queue_item("P0", "role_mask_anchor_distance_encoding", "source_data_or_authority", "Current11 lacks approved complete roles and task-C anchor authority.", "Five canonical masks and anchor-distance encoding cannot be materialized truthfully.", "resolve_covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1", ("per-atom role authority", "minimal-seed/task-C anchor contract", "five-mask materialization gate")),
        _queue_item("P1", "target_residue_atom_condition_adapter", "materialized_dataset", "The formal indicator is not an admitted split-bound sidecar.", "The completed adapter cannot feed training data.", "materialize_covapie_target_residue_atom_condition_training_sidecar_v1", ("dataset schema", "sidecar", "loader/collate gate")),
        _queue_item("P1", "supervision_signal:warhead_type_identity", "semantic_contract", "Vocabulary, unknown-label policy, and consumer placement are unresolved.", "The 11/11 authority must not imply a sixth module or an unapproved head.", "freeze_covapie_warhead_type_vocabulary_unknown_and_consumer_placement_contract_v1", ("vocabulary", "unknown-label policy", "optional-head/condition/evaluation-only decision")),
        _queue_item("P1", "ligand_residue_atom_pair_prediction_head", "materialized_dataset", "Pair metadata is not tensorized.", "Neither the pair head nor contrastive loss has a real batch contract.", "materialize_covapie_ligand_residue_pair_training_sidecars_v1", ("candidates", "positives", "offsets", "loss masks")),
        _queue_item("P1", "pre_post_covalent_geometry_prediction_head", "source_data_or_authority", "Complete pre/post geometry authority is absent.", "Geometry labels and loss cannot be compiled.", "design_covapie_pre_post_covalent_geometry_authority_contract_v1", ("source inventory", "components", "units/frame", "validity")),
        _queue_item("P2", "ligand_residue_atom_pair_prediction_head", "model_head_or_output", "No pair scorer/logits/head loss exists.", "Tensorized labels would still have no consumer.", "design_covapie_pair_prediction_optional_head_and_loss_v1", ("pair representation", "logits", "masked head loss", "compatibility")),
        _queue_item("P2", "ligand_residue_pair_contrastive_loss", "supervised_loss", "No production contrastive objective or weight exists.", "The contract mask alone is not an implemented objective.", "design_covapie_pair_contrastive_loss_v1", ("same-sample objective", "zero-negative behavior", "weight", "pair-head dependency")),
        _queue_item("P2", "pre_post_covalent_geometry_prediction_head", "model_head_or_output", "No geometry head/output/loss exists.", "Approved geometry labels would still lack a prediction path.", "design_covapie_geometry_optional_head_and_loss_v1", ("component outputs", "masked losses", "weights", "compatibility")),
        _queue_item("P3", "target_residue_atom_condition_adapter", "loss_weight_or_config", "Training config does not enable the target condition.", "A materialized sidecar would remain disabled.", "integrate_covapie_target_condition_training_configuration_v1", ("argument", "config schema", "fail-closed tests")),
        _queue_item("P4", "target_residue_atom_condition_adapter", "real_runtime_evidence", "Exact67 evidence is unavailable after the consumed smoke.", "Runtime remains unproven without establishing a model/plumbing failure.", "review_covapie_conditioned_runtime_warning_and_reexecution_policy_v1", ("warning classification", "new authorization decision")),
    ]
    response: dict[str, object] = {
        "audit_version": _VERSION, "error_contract": _ERROR,
        "source_snapshot_commit": _SOURCE_SNAPSHOT, "source_snapshot_subject": _SOURCE_SUBJECT,
        "source_snapshot_tree": _SOURCE_TREE, **lifecycle,
        "canonical_module_names": list(_MODULE_NAMES), "canonical_module_count": 5,
        "canonical_supervision_signal_names": list(_SIGNAL_NAMES),
        "canonical_supervision_signal_count": 8,
        "supervision_signal_readiness_matrix": signals,
        "supervision_signal_completion_summary": signal_summary,
        "warhead_type_authority_coverage": "11/11",
        "warhead_type_training_approved": False,
        "warhead_type_consumer_resolved": False,
        "canonical_mask_semantic_names": list(_MASK_NAMES),
        "canonical_mask_display_aliases": [{"semantic_name": name, "display_alias": alias} for name, alias in _MASK_ALIASES],
        "canonical_mask_count": 5, "audit_dimension_names": list(_DIMENSIONS),
        "audit_dimension_count": 17, "allowed_dimension_statuses": list(_STATUSES),
        "module_audit_matrix": matrix, "module_completion_summary": summary,
        "complete_dimension_count_by_module": count_maps["complete"],
        "partial_dimension_count_by_module": count_maps["partial"],
        "missing_dimension_count_by_module": count_maps["missing"],
        "blocked_dimension_count_by_module": count_maps["blocked"],
        "not_applicable_dimension_count_by_module": count_maps["not_applicable"],
        "training_ready_module_count": training_ready_count,
        "training_not_ready_module_count": len(_MODULE_NAMES) - training_ready_count,
        "cross_module_gaps": [
            "No admitted dataset/batch carries canonical role-mask-anchor tensors, pair tensors, geometry tensors, and target sidecars together.",
            "The pair head and contrastive loss are separate modules with an explicit logits dependency; neither is implemented.",
            "Warhead type is a supervision signal with unresolved placement, not a canonical sixth module.",
        ],
        "checkpoint_compatibility_risks": [
            "The checkpoint 10D channel order is preserved and silent unknown-atom zero fallback is forbidden.",
            "Unknown-atom runtime enforcement is not integrated in the final training path.",
            "Absent pair/geometry heads require disabled legacy profiles and explicit migration contracts before implementation.",
        ],
        "feature_semantics_risks": [
            "The feature-semantics contract audit and unknown-atom policy resolution are complete historical gates.",
            "Runtime enforcement of the fail-closed unknown-atom policy is not integrated.",
            "Final training-feature semantics revalidation is still required after loader/model integration.",
            "Step12D was a smoke legality check, not the final training-feature contract.",
        ],
        "runtime_validation_gaps": [
            "one_time_execution_authorization_consumed=true; bounded_runtime_smoke_execution_count=1",
            "bounded_runtime_smoke_passed=false; exact67_runtime_evidence_available=false",
            "The strict import-stderr stop establishes neither model runtime failure nor conditioned plumbing failure.",
            "No five-module batch-to-forward-to-loss runtime evidence exists.",
        ],
        "mainline_blockers": [
            "Canonical role/task-C anchor authority and five-mask materialization are incomplete.",
            "Target sidecar, pair tensors, and complete pre/post geometry tensors are not admitted training fields.",
            "Pair head, contrastive loss, and geometry head paths are absent.",
            "Unknown-atom runtime enforcement and final integrated feature-semantics revalidation remain incomplete.",
        ],
        "non_blocking_followups": [
            "Warhead-type consumer placement may resolve to an optional head, condition encoding, or evaluation-only use without changing the five-module taxonomy.",
            "Exact67 remains a system-validation gap and needs new explicit execution authorization.",
        ],
        "prioritized_gap_queue": queue, "recommended_next_increment": queue[0].copy(),
        "feature_semantics_contract_audit_completed": True,
        "unknown_atom_policy_contract_resolved": True,
        "feature_semantics_known_at_resolution_snapshot": True,
        "protein_unknown_atom_policy": "fail_closed_rejection_required_for_checkpoint_compatibility",
        "ligand_unknown_atom_policy": "fail_closed_rejection_required_for_checkpoint_compatibility",
        "checkpoint_10d_channel_order_preserved": True,
        "silent_zero_vector_fallback_allowed": False,
        "unknown_atom_runtime_enforcement_integrated": False,
        "feature_semantics_runtime_enforcement_integrated": False,
        "canonical_mask_tensors_materialized": False,
        "ready_for_tensorization": False, "ready_for_model_integration": False,
        "ready_for_training": False,
        "final_training_feature_semantics_revalidation_required": True,
        "step12d_smoke_legality_verified": True,
        "step12d_final_feature_semantics_contract": False,
        "one_time_execution_authorization_consumed": True,
        "bounded_runtime_smoke_execution_count": 1,
        "bounded_runtime_smoke_passed": False,
        "exact67_runtime_evidence_available": False,
        "failure_establishes_model_runtime_failure": False,
        "failure_establishes_conditioned_plumbing_failure": False,
        "real_training_started": False, "parameter_update_performed": False,
        "RL_implementation_started": False,
        "audit_does_not_establish_training_readiness": True,
        "response_sha256": "",
    }
    response["response_sha256"] = _sha256(_canonical_json_bytes({key: value for key, value in response.items() if key != "response_sha256"}))
    return response


def _validate_response(response: Mapping[str, Any]) -> None:
    try:
        if (type(response) is not dict or tuple(response) != _RESPONSE_FIELDS
                or response["audit_version"] != _VERSION or response["error_contract"] != _ERROR
                or response["source_snapshot_commit"] != _SOURCE_SNAPSHOT
                or response["source_snapshot_subject"] != _SOURCE_SUBJECT
                or response["source_snapshot_tree"] != _SOURCE_TREE
                or response["canonical_module_names"] != list(_MODULE_NAMES)
                or response["canonical_module_count"] != 5
                or "warhead_type_prediction" in response["canonical_module_names"]
                or response["canonical_supervision_signal_names"] != list(_SIGNAL_NAMES)
                or response["canonical_supervision_signal_count"] != 8
                or response["canonical_mask_semantic_names"] != list(_MASK_NAMES)
                or response["canonical_mask_count"] != 5
                or response["canonical_mask_display_aliases"] != [{"semantic_name": n, "display_alias": a} for n, a in _MASK_ALIASES]
                or response["audit_dimension_names"] != list(_DIMENSIONS)
                or response["audit_dimension_count"] != 17
                or response["allowed_dimension_statuses"] != list(_STATUSES)):
            raise ValueError(_ERROR)
        profile = response["audit_lifecycle_profile"]
        lifecycle_expected = {
            "audit_precommit_candidate": (None, False, False, True),
            "audit_committed_unpushed": (response["audit_commit"], True, False, False),
            "audit_published_successor": (response["audit_commit"], True, True, False),
        }
        if profile not in lifecycle_expected or (response["audit_commit"], response["audit_committed"], response["audit_published"], response["ready_for_audit_commit_review"]) != lifecycle_expected[profile] or (profile != "audit_precommit_candidate" and re.fullmatch(r"[0-9a-f]{40}", response["audit_commit"] or "") is None):
            raise ValueError(_ERROR)

        signals = response["supervision_signal_readiness_matrix"]
        if type(signals) is not dict or tuple(signals) != _SIGNAL_NAMES:
            raise ValueError(_ERROR)
        allowed_commits = {value for key, value in globals().items() if (key.startswith("_C_") or key == "_SOURCE_SNAPSHOT") and type(value) is str}
        for name in _SIGNAL_NAMES:
            row = signals[name]
            if (type(row) is not dict or tuple(row) != _SIGNAL_RECORD_FIELDS
                    or row["status"] not in _STATUSES or not row["authority_coverage"]
                    or not row["evidence_paths"] or not row["evidence_commits"]
                    or any(path not in _BOUND_REPOSITORY_PATHS for path in row["evidence_paths"])
                    or any(commit not in allowed_commits for commit in row["evidence_commits"])
                    or not row["model_consumer"] or not row["remaining_gap"]
                    or any(module not in _MODULE_NAMES for module in row["blocking_modules"])
                    or type(row["training_approved"]) is not bool):
                raise ValueError(_ERROR)
        warhead = signals["warhead_type_identity"]
        if (warhead["authority_coverage"] != "11/11" or warhead["training_approved"] is not False
                or "WARHEAD_TYPE_SUPERVISION_MODEL_CONSUMER_UNRESOLVED" not in warhead["remaining_gap"]
                or response["warhead_type_authority_coverage"] != "11/11"
                or response["warhead_type_training_approved"] is not False
                or response["warhead_type_consumer_resolved"] is not False):
            raise ValueError(_ERROR)
        summary = response["supervision_signal_completion_summary"]
        if summary != {"complete_signal_count": sum(r["status"] == "complete" for r in signals.values()), "partial_signal_count": sum(r["status"] == "partial" for r in signals.values()), "training_approved_signal_count": sum(r["training_approved"] for r in signals.values()), "conclusion": "authority_signals_exist_but_no_signal_layer_is_approved_for_training"}:
            raise ValueError(_ERROR)

        matrix = response["module_audit_matrix"]
        completion = response["module_completion_summary"]
        if type(matrix) is not dict or tuple(matrix) != _MODULE_NAMES or type(completion) is not dict or tuple(completion) != _MODULE_NAMES:
            raise ValueError(_ERROR)
        derived = {status: {} for status in _STATUSES}
        ready_count = 0
        for module in _MODULE_NAMES:
            rows = matrix[module]
            if type(rows) is not dict or tuple(rows) != _DIMENSIONS:
                raise ValueError(_ERROR)
            for status in _STATUSES:
                derived[status][module] = 0
            for dimension in _DIMENSIONS:
                row = rows[dimension]
                if (type(row) is not dict or tuple(row) != _DIMENSION_RECORD_FIELDS
                        or row["status"] not in _STATUSES or not row["evidence_summary"]
                        or type(row["remaining_gap"]) is not str
                        or type(row["blocking_for_training"]) is not bool
                        or any(path not in _BOUND_REPOSITORY_PATHS for path in row["evidence_paths"])
                        or any(commit not in allowed_commits for commit in row["evidence_commits"])
                        or (row["status"] == "complete" and (not row["evidence_paths"] or not row["evidence_commits"]))
                        or (row["status"] == "missing" and (row["evidence_paths"] or row["evidence_commits"]))):
                    raise ValueError(_ERROR)
                derived[row["status"]][module] += 1
            decisive = [name for name, row in rows.items() if row["blocking_for_training"] and row["status"] != "complete"]
            ready = rows["training_readiness"]["status"] == "complete" and not decisive
            ready_count += ready
            if completion[module] != {"training_ready": ready, "conclusion": "ready" if ready else "not_ready_incomplete_training_path", "decisive_gaps": decisive}:
                raise ValueError(_ERROR)
        fields = {"complete": "complete_dimension_count_by_module", "partial": "partial_dimension_count_by_module", "missing": "missing_dimension_count_by_module", "blocked": "blocked_dimension_count_by_module", "not_applicable": "not_applicable_dimension_count_by_module"}
        if any(response[field] != derived[status] for status, field in fields.items()) or response["training_ready_module_count"] != ready_count or response["training_not_ready_module_count"] != 5 - ready_count or ready_count != 0:
            raise ValueError(_ERROR)
        queue = response["prioritized_gap_queue"]
        order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}
        allowed_scopes = set(_MODULE_NAMES) | {"supervision_signal:warhead_type_identity"}
        if type(queue) is not list or not queue:
            raise ValueError(_ERROR)
        last = -1
        for item in queue:
            if (type(item) is not dict or tuple(item) != _QUEUE_FIELDS or item["priority"] not in order
                    or order[item["priority"]] < last or item["module"] not in allowed_scopes
                    or item["dimension"] not in _DIMENSIONS or not item["gap"] or not item["why_it_blocks"]
                    or not item["smallest_verifiable_increment"] or not item["expected_files_or_components"]
                    or item["training_or_parameter_update_required"] is not False):
                raise ValueError(_ERROR)
            last = order[item["priority"]]
        if response["recommended_next_increment"] != queue[0] or queue[0]["module"] != "role_mask_anchor_distance_encoding" or queue[0]["smallest_verifiable_increment"] != "resolve_covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1":
            raise ValueError(_ERROR)
        fixed = {
            "feature_semantics_contract_audit_completed": True,
            "unknown_atom_policy_contract_resolved": True,
            "feature_semantics_known_at_resolution_snapshot": True,
            "protein_unknown_atom_policy": "fail_closed_rejection_required_for_checkpoint_compatibility",
            "ligand_unknown_atom_policy": "fail_closed_rejection_required_for_checkpoint_compatibility",
            "checkpoint_10d_channel_order_preserved": True,
            "silent_zero_vector_fallback_allowed": False,
            "unknown_atom_runtime_enforcement_integrated": False,
            "feature_semantics_runtime_enforcement_integrated": False,
            "canonical_mask_tensors_materialized": False,
            "ready_for_tensorization": False, "ready_for_model_integration": False,
            "ready_for_training": False,
            "final_training_feature_semantics_revalidation_required": True,
            "step12d_smoke_legality_verified": True,
            "step12d_final_feature_semantics_contract": False,
            "one_time_execution_authorization_consumed": True,
            "bounded_runtime_smoke_execution_count": 1,
            "bounded_runtime_smoke_passed": False,
            "exact67_runtime_evidence_available": False,
            "failure_establishes_model_runtime_failure": False,
            "failure_establishes_conditioned_plumbing_failure": False,
            "real_training_started": False, "parameter_update_performed": False,
            "RL_implementation_started": False,
            "audit_does_not_establish_training_readiness": True,
        }
        if any(response[key] != value for key, value in fixed.items()):
            raise ValueError(_ERROR)
        digest = _sha256(_canonical_json_bytes({key: value for key, value in response.items() if key != "response_sha256"}))
        if re.fullmatch(r"[0-9a-f]{64}", response["response_sha256"]) is None or response["response_sha256"] != digest:
            raise ValueError(_ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def evaluate_covapie_five_module_training_path_completion_gap_audit_v1(*, repo_root: Path) -> dict[str, object]:
    """Return the deterministic evidence-bound audit response."""
    try:
        lifecycle = _validate_static_repository(repo_root)
        response = _build_response(lifecycle)
        _validate_response(response)
        return response
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
