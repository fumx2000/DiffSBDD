#!/usr/bin/env python3
"""Check the exact CovaPIE ranks 501--1000 scale-up candidate V1."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1 as scaleup,
)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _git(*arguments: str, env: dict[str, str] | None = None,
         input_text: str | None = None) -> str:
    return subprocess.run(
        ["git", *arguments], cwd=REPO_ROOT, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        env=env, input=input_text,
    ).stdout.strip()


def _independent_oracles() -> dict[str, object]:
    canonical_path = REPO_ROOT / scaleup.CANONICAL_RELATIVE
    canonical = json.loads(canonical_path.read_bytes())
    events = canonical["canonical_events"]
    if len(events) != 2387 or len({event["canonical_event_id"] for event in events}) != 2387:
        raise ValueError("INDEPENDENT_CANONICAL_2387_ORACLE_FAILED")
    outcomes_path = (
        REPO_ROOT / "data/derived/covalent_small/"
        "covapie_bulk_cys_sg_dataset_expansion_v1/bulk_pilot_v1/"
        "bulk_processing_outcomes_v1.json"
    )
    outcomes = json.loads(outcomes_path.read_bytes())["events"]
    known_routes = {
        "KNOWN_EXISTING_APPROVED_SAMPLE", "KNOWN_EXISTING_QUARANTINE",
        "KNOWN_RUNTIME_EXTENSION",
    }
    controls = {item["canonical_event_id"] for item in outcomes
                if item["terminal_outcome"] in known_routes}
    if len(controls) != 27 or len(events) - len(controls) != 2360:
        raise ValueError("INDEPENDENT_27_2360_ORACLE_FAILED")
    first_path = (
        REPO_ROOT / "data/derived/covalent_small/"
        "covapie_bulk_500_new_event_scale_up_rehearsal_v1/"
        "covapie_bulk_500_new_event_cohort_v1.csv"
    )
    first = list(csv.DictReader(io.StringIO(first_path.read_text(encoding="utf-8"))))
    next_rows = list(csv.DictReader(io.StringIO(
        (REPO_ROOT / scaleup.OUTPUT_ROOT_RELATIVE / scaleup.COHORT)
        .read_text(encoding="utf-8")
    )))
    if [int(row["scaleup_rank"]) for row in first] != list(range(1, 501)):
        raise ValueError("INDEPENDENT_FIRST500_RANK_ORACLE_FAILED")
    if [int(row["scaleup_rank"]) for row in next_rows] != list(range(501, 1001)):
        raise ValueError("INDEPENDENT_NEXT500_RANK_ORACLE_FAILED")
    first_ids = [row["canonical_event_id"] for row in first]
    next_ids = [row["canonical_event_id"] for row in next_rows]
    if len(set(next_ids)) != 500 or set(first_ids) & set(next_ids) or len(set(first_ids + next_ids)) != 1000:
        raise ValueError("INDEPENDENT_CUMULATIVE1000_UNION_ORACLE_FAILED")
    routing = list(csv.DictReader(io.StringIO(
        (REPO_ROOT / scaleup.FIRST500_ROUTING).read_text(encoding="utf-8")
    )))
    partitions: dict[str, int] = {}
    for row in routing:
        partitions[row["post_only_partition"]] = partitions.get(row["post_only_partition"], 0) + 1
    expected = {
        "POST_ONLY_V1_REVIEW_CANDIDATE": 210,
        "BLOCKED_EXISTING_GROUP_CONFLICT": 196,
        "BLOCKED_REPRESENTATION_GAP": 31,
        "OUTSIDE_STRUCTURAL_ELIGIBILITY": 63,
    }
    if partitions != expected:
        raise ValueError("INDEPENDENT_FIRST500_PARTITION_ORACLE_FAILED")
    return {
        "canonical_event_count": len(events), "known_control_count": len(controls),
        "ranked_new_count": len(events) - len(controls),
        "first500_count": len(first_ids), "next500_count": len(next_ids),
        "cumulative1000_unique_count": len(set(first_ids + next_ids)),
        "remaining_ranked_new_count": 2360 - 1000,
        "first500_partition_counts": partitions,
    }


def _simulate_published_successor() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="covapie-scaleup-index-") as directory:
        index = Path(directory) / "index"
        env = dict(os.environ)
        env["GIT_INDEX_FILE"] = str(index)
        _git("read-tree", scaleup.BASELINE_HEAD, env=env)
        for relative in sorted(scaleup.AUTHORIZED_PATHS):
            path = REPO_ROOT / relative
            blob = _git("hash-object", "-w", "--", str(path))
            _git("update-index", "--add", "--cacheinfo", f"100644,{blob},{relative}", env=env)
        tree = _git("write-tree", env=env)
        commit = _git("commit-tree", tree, "-p", scaleup.BASELINE_HEAD,
                      input_text=scaleup.PUBLICATION_SUBJECT + "\n")
        parent_ids = _git("show", "-s", "--format=%P", commit).split()
        subject = _git("log", "-1", "--format=%s", commit)
        changed_entries = []
        for line in _git(
            "diff-tree", "--no-commit-id", "--name-status", "--no-renames",
            "-r", commit,
        ).splitlines():
            status_value, path = line.split("\t", 1)
            changed_entries.append({"status": status_value, "path": path})
        modes = {}
        for line in _git(
            "ls-tree", "-r", "--full-tree", commit, "--",
            *sorted(scaleup.AUTHORIZED_PATHS),
        ).splitlines():
            metadata, path = line.split("\t", 1)
            modes[path] = metadata.split()[0]
        observation = {
            "branch": "main", "HEAD": commit,
            "HEAD_parent": parent_ids[0] if len(parent_ids) == 1 else "",
            "head_parent_ids": parent_ids, "HEAD_tree": tree,
            "HEAD_subject": subject, "head_changed_entries": changed_entries,
            "head_candidate_path_modes": modes, "origin_main": commit,
            "ahead_behind": "0\t0", "tracked_changes": [],
            "staged_changes": [], "untracked": [],
        }
        if scaleup.classify_repository_profile_v1(observation) != "published_successor":
            raise ValueError("PUBLISHED_SUCCESSOR_POSITIVE_SIMULATION_FAILED")

        cases: dict[str, dict[str, object]] = {}
        cases["wrong_parent"] = {"HEAD_parent": "1" * 40, "head_parent_ids": ["1" * 40]}
        cases["wrong_subject"] = {"HEAD_subject": "wrong publication subject"}
        cases["extra_changed_path"] = {
            "head_changed_entries": changed_entries + [{"status": "A", "path": "extra.txt"}]
        }
        cases["missing_candidate_path"] = {
            "head_changed_entries": changed_entries[:-1],
            "head_candidate_path_modes": {
                key: value for key, value in modes.items()
                if key != changed_entries[-1]["path"]
            },
        }
        mutated_status = copy.deepcopy(changed_entries)
        mutated_status[0]["status"] = "M"
        cases["modified_instead_of_added"] = {"head_changed_entries": mutated_status}
        mutated_modes = dict(modes)
        python_path = next(path for path in sorted(modes) if path.endswith(".py"))
        mutated_modes[python_path] = "100755"
        cases["executable_python_mode"] = {"head_candidate_path_modes": mutated_modes}
        cases["extra_untracked_file"] = {"untracked": ["extra.txt"]}
        cases["two_parent_metadata"] = {
            "HEAD_parent": "", "head_parent_ids": [scaleup.BASELINE_HEAD, "2" * 40]
        }
        cases["head_origin_mismatch"] = {"origin_main": "3" * 40}
        cases["ahead_behind_mismatch"] = {"ahead_behind": "1\t0"}
        negative_results = {}
        for name, mutation in cases.items():
            candidate = copy.deepcopy(observation)
            candidate.update(mutation)
            try:
                scaleup.classify_repository_profile_v1(candidate)
            except scaleup.ScaleupSafetyError:
                negative_results[name] = True
            else:
                raise ValueError("PUBLISHED_SUCCESSOR_NEGATIVE_SIMULATION_FAILED:" + name)
        return {
            "simulated_commit": commit, "simulated_tree": tree,
            "single_parent": parent_ids[0], "subject": subject,
            "changed_path_count": len(changed_entries), "all_modes_100644": True,
            "positive_simulation_passed": True,
            "negative_simulations": negative_results,
            "negative_simulations_passed": all(negative_results.values()),
        }


def check(*, simulate_published: bool) -> dict[str, object]:
    observation = scaleup.observe_repository_state_v1(REPO_ROOT)
    profile = scaleup.classify_repository_profile_v1(observation)
    expected = scaleup.build_artifacts_v1(repo_root=REPO_ROOT)
    output_root = REPO_ROOT / scaleup.OUTPUT_ROOT_RELATIVE
    for name, payload in expected.items():
        path = output_root / name
        if not path.is_file() or path.read_bytes() != payload:
            raise ValueError("CANDIDATE_ARTIFACT_BYTE_MISMATCH:" + name)
    actual_paths = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in REPO_ROOT.rglob("*") if path.is_file()
        and (path.relative_to(REPO_ROOT).as_posix() in scaleup.AUTHORIZED_PATHS)
    }
    if actual_paths != set(scaleup.AUTHORIZED_PATHS):
        raise ValueError("EXACT11_PATH_SET_MISMATCH")
    if any(stat.S_IMODE((REPO_ROOT / path).stat().st_mode) != 0o644
           for path in scaleup.AUTHORIZED_PATHS):
        raise ValueError("EXACT11_MODE_MISMATCH")
    if list(REPO_ROOT.rglob("*.part")) or list(REPO_ROOT.rglob("*.tmp")):
        raise ValueError("REPOSITORY_PARTIAL_FILE_PRESENT")
    overlay = scaleup.overlay_attempt_root_v1(REPO_ROOT)
    if list(overlay.rglob("*.part")) or list(overlay.rglob("*.tmp")):
        raise ValueError("OVERLAY_PARTIAL_FILE_PRESENT")
    replay = scaleup.replay_no_network_v1(repo_root=REPO_ROOT)
    oracles = _independent_oracles()
    summary = json.loads(expected[scaleup.SUMMARY])
    manifest = json.loads(expected[scaleup.MANIFEST])
    effective = json.loads(expected[scaleup.EFFECTIVE_N])
    census = list(csv.DictReader(io.StringIO(expected[scaleup.CENSUS].decode("utf-8"))))
    processing = json.loads(expected[scaleup.PROCESSING])
    if len(census) != 1000 or len(processing["events"]) != 500:
        raise ValueError("FINAL_POPULATION_RECONCILIATION_FAILED")
    if manifest["canonical_cache_before"] != manifest["canonical_cache_after"]:
        raise ValueError("CANONICAL_CACHE_IMMUTABILITY_FAILED")
    if summary["safety"]["training_performed"] is not False:
        raise ValueError("TRAINING_SAFETY_FLAG_FAILED")
    if not effective["raw_label_N_distinguished_from_runtime_effective_N"]:
        raise ValueError("RAW_EFFECTIVE_N_DISTINCTION_FAILED")
    audit = summary["global_current_positive_authority_audit"]
    counts = audit["counts"]
    if (
        audit["audit_complete"] is not True
        or counts["global_current_runtime_model_usable_sample_count"] != 29
        or counts["global_current_runtime_model_usable_canonical_event_count"] != 29
        or counts["global_current_positive_but_runtime_incomplete_count"] != 8
        or counts["formal_training_split_admitted_positive_count"] != 13
        or set(effective["scopes"]) != {
            "cumulative1000_ranked_new_scope",
            "global_current_runtime_authority_scope",
        }
    ):
        raise ValueError("GLOBAL_CURRENT_AUTHORITY_AUDIT_FAILED")
    forbidden = (".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip",
                 ".tgz", ".npz", ".tmp", ".part")
    candidate_forbidden = [path for path in scaleup.AUTHORIZED_PATHS if path.endswith(forbidden)]
    if candidate_forbidden:
        raise ValueError("FORBIDDEN_CANDIDATE_SUFFIX")
    simulation = _simulate_published_successor() if simulate_published else None
    positive_simulation = bool(
        simulation and simulation["positive_simulation_passed"]
    )
    negative_simulations = bool(
        simulation and simulation["negative_simulations_passed"]
    )
    return {
        "schema_version": scaleup.SCHEMA_VERSION,
        "candidate_precommit_profile_passed": profile == "candidate_precommit_untracked",
        "published_successor_profile_simulation_passed": positive_simulation,
        "published_successor_negative_simulations_passed": negative_simulations,
        "real_published_successor_exact11_enforced": True,
        "repository_profile": profile, "independent_oracles": oracles,
        "deterministic_replay": replay, "published_simulation": simulation,
        "candidate_files": {
            relative: {"byte_count": (REPO_ROOT / relative).stat().st_size,
                       "sha256": _sha((REPO_ROOT / relative).read_bytes()),
                       "mode": "100644"}
            for relative in sorted(scaleup.AUTHORIZED_PATHS)
        },
        "ready_for_gpt_review": True,
        "ready_for_publication": positive_simulation and negative_simulations,
        "ready_for_next_bulk_scale_decision": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate-published-successor", action="store_true")
    args = parser.parse_args()
    result = check(simulate_published=args.simulate_published_successor)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
