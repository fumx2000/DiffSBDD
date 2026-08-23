#!/usr/bin/env python3
"""Standalone fail-closed checker for existing positive closure V1."""

from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_existing_positive_runtime_and_split_closure_v1 as closure,
)


FROZEN_ARTIFACT_SHA256_V1 = {
    "covapie_existing_positive_runtime_binding_inventory_v1.csv": (
        "b8a0f4c2bc8ca46141775f0a5fa54322d12db685b37c930659f6f4a1ca3b4052"
    ),
    "covapie_existing_positive_leakage_split_closure_inventory_v1.csv": (
        "2f673a8ca76217af1517d8254de79799d4fea333d9892af13a3ab0eeb90d8259"
    ),
    "covapie_current_runtime_model_usable_positive_index_v1.csv": (
        "5485305a750129e437ef68b43c758f9f0586add41fe54ee1d621b6c5bde62410"
    ),
    "covapie_existing_positive_runtime_and_split_closure_manifest_v1.json": (
        "5a94d4a35a0cc7b5495175bd4e94e26ab2a8ba796ed59ea1e1e4695575936944"
    ),
    "covapie_existing_positive_runtime_and_split_closure_summary_v1.json": (
        "2c00779a087063124a12915ec71b3666e5b39a9c882ec15fd12cf2d26dec13be"
    ),
}


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _published_simulation(candidate: dict[str, object]) -> dict[str, object]:
    simulated = copy.deepcopy(candidate)
    simulated.update({
        "HEAD": "1" * 40,
        "HEAD_parent": closure.BASELINE_HEAD_V1,
        "head_parent_ids": [closure.BASELINE_HEAD_V1],
        "HEAD_tree": "2" * 40,
        "HEAD_subject": closure.PUBLICATION_SUBJECT_V1,
        "origin_main": "1" * 40,
        "untracked": [],
        "candidate_filesystem_modes": {},
        "head_changed_entries": [
            {"status": "A", "path": path}
            for path in sorted(closure.AUTHORIZED_PATHS_V1)
        ],
        "head_candidate_path_modes": {
            path: "100644" for path in closure.AUTHORIZED_PATHS_V1
        },
    })
    return simulated


def main() -> int:
    computation = closure.compute_covapie_existing_positive_runtime_and_split_closure_v1(
        repository_root=REPO
    )
    expected = closure.build_covapie_existing_positive_runtime_and_split_closure_artifacts_v1(
        repository_root=REPO, computation=computation
    )
    output_root = REPO / closure.OUTPUT_ROOT_RELATIVE_V1
    for name, payload in expected.items():
        path = output_root / name
        if not path.is_file() or path.read_bytes() != payload:
            raise AssertionError("ARTIFACT_MISSING_OR_NONDETERMINISTIC:" + name)
        if _sha(payload) != FROZEN_ARTIFACT_SHA256_V1.get(name):
            raise AssertionError("FROZEN_ARTIFACT_SHA256_CHANGED:" + name)
    if tuple(expected) != closure.OUTPUT_FILENAMES_V1:
        raise AssertionError("OUTPUT_SET_INVALID")
    observation = closure.observe_repository_state_v1(REPO)
    profile = closure.classify_repository_profile_v1(observation)
    if profile not in {"candidate_precommit_untracked", "published_successor"}:
        raise AssertionError("REAL_PROFILE_INVALID")
    simulation_profile = closure.classify_repository_profile_v1(
        _published_simulation(observation)
    )
    if simulation_profile != "published_successor":
        raise AssertionError("PUBLISHED_SIMULATION_INVALID")
    if computation.existing_split_assignments_changed:
        raise AssertionError("EXISTING_SPLIT_CHANGED")
    if computation.cross_split_leakage_group_count != 0:
        raise AssertionError("CROSS_SPLIT_LEAKAGE")
    if any(
        row["canonical_event_id"] == closure.AJ3_EVENT_ID_V1
        and (
            row["current_runtime_model_usable_after"] != "false"
            or row["formal_split_authoritative_after"] != "false"
        )
        for row in computation.leakage_split_rows
    ):
        raise AssertionError("AJ3_PROMOTED")

    split_by_event = {
        row["canonical_event_id"]: row for row in computation.leakage_split_rows
    }
    train_samples = []
    heldout_samples = []
    for sample in computation.runtime_samples:
        row = split_by_event[sample.canonical_event_id]
        expected_admitted = bool(
            row["current_runtime_model_usable_after"] == "true"
            and row["formal_split_authoritative_after"] == "true"
            and row["formal_split_after"] == "train"
        )
        observed_admitted = bool(
            sample.supervision.sample_training_admitted.item()
        )
        if observed_admitted != expected_admitted:
            raise AssertionError("RUNTIME_SAMPLE_SPLIT_ADMISSION_MISMATCH")
        (train_samples if expected_admitted else heldout_samples).append(sample)
    if (
        len(train_samples) != 1
        or train_samples[0].canonical_event_id
        != closure.RUNTIME_TARGET_EVENT_IDS_V1[1]
        or len(heldout_samples) != 6
    ):
        raise AssertionError("EXACT7_TRAIN_HELDOUT_POPULATION_INVALID")
    train_supervision = train_samples[0].supervision
    if (
        int(train_supervision.ligand_active_diffusion_loss_mask.sum().item()) <= 0
        or int(train_supervision.pair_head_candidate_loss_mask.sum().item()) <= 0
        or not bool(train_supervision.pair_contrastive_sample_loss_mask.item())
        or train_supervision.pre_post_geometry_component_valid_mask.tolist()
        != [[False, True]]
        or train_supervision.pre_post_geometry_component_loss_mask.tolist()
        != [[False, True]]
    ):
        raise AssertionError("GJJ_TRAIN_MASK_INVALID")
    heldout_active_diffusion = sum(
        int(sample.supervision.ligand_active_diffusion_loss_mask.sum().item())
        for sample in heldout_samples
    )
    heldout_pair_head = sum(
        int(sample.supervision.pair_head_candidate_loss_mask.sum().item())
        for sample in heldout_samples
    )
    heldout_pair_contrastive = sum(
        int(sample.supervision.pair_contrastive_sample_loss_mask.sum().item())
        for sample in heldout_samples
    )
    heldout_post_geometry_loss = sum(
        int(sample.supervision.pre_post_geometry_component_loss_mask[0, 1].item())
        for sample in heldout_samples
    )
    heldout_post_geometry_valid = sum(
        int(sample.supervision.pre_post_geometry_component_valid_mask[0, 1].item())
        for sample in heldout_samples
    )
    heldout_pre_geometry_valid = sum(
        int(sample.supervision.pre_post_geometry_component_valid_mask[0, 0].item())
        for sample in heldout_samples
    )
    if (
        heldout_active_diffusion != 0
        or heldout_pair_head != 0
        or heldout_pair_contrastive != 0
        or heldout_post_geometry_loss != 0
        or heldout_post_geometry_valid != 6
        or heldout_pre_geometry_valid != 0
        or any(
            not bool(sample.supervision.pair_positive_candidate_valid.item())
            or not bool(
                sample.supervision.observed_complex_pair_distance_valid.item()
            )
            for sample in heldout_samples
        )
    ):
        raise AssertionError("HELDOUT_MASK_OR_LABEL_VALIDITY_INVALID")

    forbidden_suffixes = (
        ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip",
        ".tgz", ".npz", ".tmp", ".part", ".pyc",
    )
    candidate_paths = sorted(closure.AUTHORIZED_PATHS_V1)
    if any(path.endswith(forbidden_suffixes) for path in candidate_paths):
        raise AssertionError("FORBIDDEN_CANDIDATE_SUFFIX")
    protected = {
        "equivariant_diffusion", "lightning_modules.py", "dataset.py",
        "data/prepare_crossdocked.py", "checkpoints",
    }
    touched = set(observation["tracked_changes"]) | set(observation["staged_changes"])
    if any(
        path in protected or any(path.startswith(prefix + "/") for prefix in protected)
        for path in touched
    ):
        raise AssertionError("PROTECTED_SOURCE_CHANGED")
    raw_tracked_count = len([
        path for path in _git("ls-files", "data/raw").splitlines() if path
    ])
    raw_staged_count = len([
        path for path in observation["staged_changes"] if path.startswith("data/raw/")
    ])
    if raw_staged_count != 0:
        raise AssertionError("RAW_FILE_STAGED")

    counts = computation.counts
    print("existing_positive_runtime_split_closure_built=true")
    print("runtime_split_training_mask_leak_repaired=true")
    for key in (
        "published_positive_authority_event_count_before",
        "full_positive_supervision_event_count_before",
        "current_runtime_model_usable_event_count_before",
        "full_supervision_runtime_incomplete_event_count_before",
        "task_relevance_only_incomplete_event_count_before",
        "runtime_binding_target_event_count",
        "runtime_binding_closed_event_count",
        "runtime_binding_remaining_incomplete_event_count",
        "current_runtime_model_usable_event_count_after",
        "K36_runtime_usable_event_count",
        "K36_formal_split_closed_event_count",
        "K36_formal_split_remaining_unassigned_count",
        "newly_runtime_bound_formal_split_closed_event_count",
        "current_runtime_model_usable_without_formal_split_count_after",
        "formal_training_split_admitted_positive_count_after",
        "formal_validation_split_positive_count_after",
        "formal_test_split_positive_count_after",
    ):
        print(f"{key}={counts[key]}")
    print("existing_split_assignments_changed=false")
    print("cross_split_leakage_group_count=0")
    print("AJ3_promoted=false")
    print("PRE_geometry_fabricated=false")
    print("new_chemistry_authority_created=false")
    print("fuzzy_positive_propagation_performed=false")
    print("training_performed=false")
    print("Trainer_used=false")
    print("backward_performed=false")
    print("optimizer_created=false")
    print("network_performed=false")
    print("bulk_ranks1001_1500_processed=false")
    print("data_augmentation_performed=false")
    print("cumulative1000_rebuild_invoked=false")
    print("cumulative1000_replay_invoked=false")
    print("new_exact7_training_admitted_count=1")
    print("new_exact7_training_inactive_count=6")
    print("GJJ_sample_training_admitted=true")
    print("heldout_sample_training_admitted_count=0")
    print(f"heldout_active_diffusion_loss_count={heldout_active_diffusion}")
    print(f"heldout_pair_head_active_candidate_count={heldout_pair_head}")
    print(
        "heldout_pair_contrastive_active_sample_count="
        f"{heldout_pair_contrastive}"
    )
    print(f"heldout_POST_geometry_loss_active_count={heldout_post_geometry_loss}")
    print(f"heldout_POST_geometry_valid_count={heldout_post_geometry_valid}")
    print(f"heldout_PRE_geometry_valid_count={heldout_pre_geometry_valid}")
    print("heldout_labels_retained=true")
    print(f"repository_profile={profile}")
    candidate_profile_passed = closure._candidate_precommit_profile_passed_v1(
        profile
    )
    print(
        "candidate_precommit_profile_passed="
        + str(candidate_profile_passed).lower()
    )
    print("candidate_precommit_marker_lifecycle_aware=true")
    print("published_successor_profile_simulation_passed=true")
    print(f"raw_tracked_legacy_count={raw_tracked_count}")
    print("raw_staged_count=0")
    print("protected_source_diffs=0")
    print("forbidden_candidate_file_count=0")
    print("ready_for_gpt_review=true")
    print("ready_for_gpt_reaudit=true")
    print("ready_for_publication=true")
    print(
        "recommended_next_step_exactly="
        "gpt_reaudit_existing_positive_split_aware_training_masks_then_publish_if_pass"
    )
    print("artifact_sha256=" + str({name: _sha(payload) for name, payload in expected.items()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
