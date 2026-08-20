#!/usr/bin/env python3
"""Fail-closed checker for the exact 1FVG DTT shadow gate V1."""

from __future__ import annotations

from collections import Counter
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence

from covalent_ext import (
    covapie_post_only_auto_negative_dtt_crystallization_reducing_exact_v1 as gate,
)
from covalent_ext import (
    covapie_bulk_post_only_cys_sg_successor_task_domain_routing_v1 as successor,
)


PROTECTED_SOURCE_PATHS = {
    "equivariant_diffusion",
    "lightning_modules.py",
    "dataset.py",
    "data/prepare_crossdocked.py",
    "data/raw",
    "checkpoints",
}
FORBIDDEN_SUFFIXES = {
    ".pt",
    ".ckpt",
    ".pth",
    ".pkl",
    ".lmdb",
    ".tar",
    ".zip",
    ".tgz",
    ".npz",
    ".tmp",
    ".part",
}
PRECOMMIT_CANDIDATE_PROFILE = "DTT_GATE_PRECOMMIT_CANDIDATE"
PUBLISHED_CLEAN_DESCENDANT_PROFILE = "DTT_GATE_PUBLISHED_CLEAN_DESCENDANT"
DTT_S1_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_A3782D89BDEF47C1"


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _git(repo_root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _csv(path: Path, header: Sequence[str]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        _assert(tuple(reader.fieldnames or ()) == tuple(header), path.name + " header")
        rows = list(reader)
    _assert(
        all(
            tuple(row) == tuple(header)
            and all(value is not None for value in row.values())
            for row in rows
        ),
        path.name + " row schema",
    )
    return rows


def _contains_absolute_path(value: object) -> bool:
    if isinstance(value, str):
        return os.path.isabs(value)
    if isinstance(value, list):
        return any(_contains_absolute_path(item) for item in value)
    if isinstance(value, dict):
        return any(
            _contains_absolute_path(key) or _contains_absolute_path(item)
            for key, item in value.items()
        )
    return False


def _contains_key(value: object, forbidden: str) -> bool:
    if isinstance(value, dict):
        return forbidden in value or any(
            _contains_key(item, forbidden) for item in value.values()
        )
    if isinstance(value, list):
        return any(_contains_key(item, forbidden) for item in value)
    return False


def classify_worktree_profile_v1(
    *, modified: Sequence[str], staged: Sequence[str], untracked: Sequence[str]
) -> str:
    modified_set = set(modified)
    staged_set = set(staged)
    untracked_set = set(untracked)
    if modified_set:
        raise AssertionError(
            "modified tracked files: " + ",".join(sorted(modified_set))
        )
    if staged_set:
        raise AssertionError("staged files: " + ",".join(sorted(staged_set)))
    authorized = {path.as_posix() for path in gate.AUTHORIZED_NEW_PATHS}
    if untracked_set == authorized:
        return PRECOMMIT_CANDIDATE_PROFILE
    if not untracked_set:
        return PUBLISHED_CLEAN_DESCENDANT_PROFILE
    raise AssertionError(
        "untracked files match neither exact DTT precommit nor published-clean profile"
    )


def validate_current_human_overlay_coverage_v1(
    *, current_human: Mapping[str, Any], evidence: Mapping[str, Any]
) -> dict[str, Mapping[str, Any]]:
    current_units = gate.validate_current_human_overlay_v1(current_human)
    frozen_units = evidence.get("unit_by_id")
    if not isinstance(frozen_units, Mapping):
        raise AssertionError("frozen review-unit evidence missing")
    _assert(set(current_units) == set(frozen_units), "current human unit coverage")
    for unit_id, current_unit in current_units.items():
        frozen_unit = frozen_units[unit_id]
        if not isinstance(frozen_unit, Mapping):
            raise AssertionError("frozen review unit invalid: " + unit_id)
        current_event_ids = {
            event.get("canonical_event_id") for event in current_unit["events"]
        }
        frozen_event_ids = set(frozen_unit.get("canonical_event_ids", ()))
        _assert(
            current_event_ids == frozen_event_ids,
            "current human event coverage: " + unit_id,
        )
    return current_units


def validate_successor_live_integration_v1(repo_root: Path) -> bool:
    """Validate this immutable DTT gate's live contribution when present."""

    output_root = repo_root / successor.OUTPUT_ROOT_RELATIVE
    manifest = json.loads((output_root / successor.MANIFEST).read_bytes())
    rule_ids = manifest.get("integrated_auto_negative_rule_ids")
    _assert(isinstance(rule_ids, list), "successor integrated rule registry")
    occurrence_count = rule_ids.count(gate.RULE_ID)
    _assert(occurrence_count <= 1, "DTT rule duplicated in successor registry")
    if occurrence_count == 0:
        return False

    expected_bindings = {
        path.as_posix(): dict(expected)
        for path, expected in successor.DTT_GATE_ARTIFACT_BINDINGS.items()
    }
    observed_bindings = {
        path: {
            "byte_count": len((repo_root / path).read_bytes()),
            "sha256": hashlib.sha256((repo_root / path).read_bytes()).hexdigest(),
        }
        for path in expected_bindings
    }
    _assert(observed_bindings == expected_bindings, "immutable DTT artifact bytes")
    _assert(
        manifest.get("published_dtt_gate_artifact_bindings")
        == expected_bindings,
        "successor DTT artifact bindings",
    )

    event_rows = _csv(
        output_root / successor.EVENT_INVENTORY, successor.EVENT_HEADER
    )
    unit_rows = _csv(output_root / successor.UNIT_INVENTORY, successor.UNIT_HEADER)
    dtt_event_rows = [row for row in event_rows if row["rule_id"] == gate.RULE_ID]
    _assert(dtt_event_rows, "successor DTT rule-event evidence missing")
    unit_by_id = {row["review_unit_id"]: row for row in unit_rows}
    _assert(len(unit_by_id) == len(unit_rows), "successor unit inventory duplicate")

    dtt_s1 = unit_by_id[DTT_S1_UNIT_ID]
    _assert(
        dtt_s1["selected_auto_negative_rule_id"] == gate.RULE_ID
        and dtt_s1["final_task_domain_route"]
        == successor.AUTO_NEGATIVE_EXACT_FINAL,
        "DTT-S1 live integration",
    )
    dtt_s1_events = [
        row for row in dtt_event_rows if row["review_unit_id"] == DTT_S1_UNIT_ID
    ]
    _assert(
        len(dtt_s1_events) == 1
        and dtt_s1_events[0]["gate_event_status"]
        == gate.MATCHED_AUTO_NEGATIVE_EXACT,
        "DTT-S1 raw DTT match",
    )

    dtt_s4 = unit_by_id[gate.CALIBRATION_UNIT_ID]
    _assert(
        dtt_s4["selected_auto_negative_rule_id"] == ""
        and dtt_s4["final_task_domain_route"]
        == successor.HUMAN_NOT_RELEVANT_FINAL,
        "DTT-S4 human-negative precedence",
    )
    dtt_s4_events = [
        row
        for row in dtt_event_rows
        if row["review_unit_id"] == gate.CALIBRATION_UNIT_ID
    ]
    _assert(
        len(dtt_s4_events) == 1
        and dtt_s4_events[0]["gate_event_status"]
        == gate.MATCHED_AUTO_NEGATIVE_EXACT,
        "DTT-S4 raw DTT calibration match",
    )

    dtu = unit_by_id[gate.DTU_COUNTEREXAMPLE_UNIT_ID]
    dtu_events = [
        row
        for row in dtt_event_rows
        if row["review_unit_id"] == gate.DTU_COUNTEREXAMPLE_UNIT_ID
    ]
    _assert(
        dtu["selected_auto_negative_rule_id"] != gate.RULE_ID
        and len(dtu_events) == 1
        and dtu_events[0]["gate_event_status"] == gate.NOT_MATCHED,
        "DTU must not auto-negative because of DTT",
    )
    return True


def check_v1(repo_root: Path, cache_root: Path | None = None) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    resolved_cache = (
        cache_root.resolve()
        if cache_root is not None
        else repo_root.parent / gate.CACHE_ROOT_RELATIVE_TO_REPOSITORY_PARENT
    )
    output_root = repo_root / gate.OUTPUT_ROOT_RELATIVE
    _assert(output_root.is_dir(), "output directory missing")
    _assert(
        {item.name for item in output_root.iterdir() if item.is_file()}
        == set(gate.OUTPUT_FILENAMES),
        "output file set mismatch",
    )
    _assert(
        not any(item.suffix in {".tmp", ".part"} for item in output_root.iterdir()),
        "temporary output remains",
    )

    git_state = gate.verify_repository_binding_v1(repo_root)
    _assert(git_state["descendant_repository_compatible"] is True, "descendant Git")
    _assert(git_state["head"] == git_state["origin_main"], "HEAD/origin mismatch")
    _assert((git_state["ahead"], git_state["behind"]) == (0, 0), "divergence")
    _assert(
        git_state["base_successor_routing_commit"]
        == gate.BASE_SUCCESSOR_ROUTING_COMMIT,
        "successor base commit",
    )
    _assert(
        git_state["base_successor_routing_subject"]
        == gate.BASE_SUCCESSOR_ROUTING_SUBJECT,
        "successor base subject",
    )
    _assert(
        git_state["base_successor_routing_commit_is_ancestor_of_head"] is True,
        "successor base HEAD ancestry",
    )
    _assert(
        git_state[
            "base_successor_routing_commit_is_ancestor_of_origin_main"
        ]
        is True,
        "successor base origin ancestry",
    )
    input_hashes = gate.verify_bound_inputs_v1(repo_root)
    gate.load_immutable_dtt_human_gold_v1(repo_root)
    evidence = gate._load_calibration_snapshot_evidence_v1(repo_root)
    context = gate.build_static_rule_context_v1(
        repo_root=repo_root, cache_root=resolved_cache
    )
    _assert(
        context["endpoint_automorphism"]["DTT_ENDPOINT_AUTOMORPHISM_PROVEN"]
        is True,
        "DTT automorphism not proven",
    )
    _assert(
        set(context["endpoint_automorphism"]["reactive_sulfur_orbit"])
        == {"S1", "S4"},
        "DTT sulfur orbit",
    )

    replay_sha = gate.verify_deterministic_replay_v1(repo_root, resolved_cache)
    manifest = json.loads((output_root / gate.RULE_MANIFEST).read_bytes())
    summary = json.loads((output_root / gate.SUMMARY).read_bytes())
    rows = _csv(output_root / gate.SHADOW_INVENTORY, gate.SHADOW_HEADER)
    _assert(not _contains_absolute_path(manifest), "manifest contains absolute path")
    _assert(not _contains_absolute_path(summary), "summary contains absolute path")
    for forbidden in (
        "current_head",
        "head",
        "origin_main",
        "ahead",
        "behind",
        "current_human_overlay_sha256",
        "current_production_registry_sha256",
        "live_workload",
        "execution_timestamp",
    ):
        _assert(not _contains_key(manifest, forbidden), "manifest runtime key: " + forbidden)
        _assert(not _contains_key(summary, forbidden), "summary runtime key: " + forbidden)
    _assert(manifest["schema_version"] == gate.SCHEMA_VERSION, "manifest schema")
    _assert(manifest["rule_id"] == gate.RULE_ID, "manifest rule")
    _assert(manifest["rule_role"] == gate.RULE_ROLE, "manifest role")
    _assert(manifest["artifact_semantics"] == gate.ARTIFACT_SEMANTICS, "semantics")
    _assert(manifest["calibration_unit_id"] == gate.CALIBRATION_UNIT_ID, "gold unit")
    _assert(
        manifest["calibration_artifact_binding"]
        == {
            "git_object": gate.CALIBRATION_COMMIT
            + ":"
            + gate.HUMAN_DECISIONS_RELATIVE.as_posix(),
            "path": gate.HUMAN_DECISIONS_RELATIVE.as_posix(),
            "byte_count": gate.CALIBRATION_HUMAN_BYTES,
            "sha256": gate.CALIBRATION_HUMAN_SHA256,
        },
        "immutable human binding",
    )
    _assert(
        manifest["calibration_human_decision"]["all_event_decisions_blank"]
        is True,
        "calibration event decisions",
    )
    _assert(
        manifest["dtt_stereochemical_identity"]
        == {
            "inchikey": gate.DTT_INCHIKEY,
            "atom_stereo_config": {"C2": "R", "C3": "R"},
        },
        "DTT stereo binding",
    )
    _assert(
        manifest["dtu_counterexample_identity"]["inchikey"] == gate.DTU_INCHIKEY
        and manifest["dtu_counterexample_identity"]["atom_stereo_config"]
        == {"C2": "S", "C3": "R"},
        "DTU stereo binding",
    )
    _assert(
        manifest["derived_endpoint_automorphism"][
            "DTT_ENDPOINT_AUTOMORPHISM_PROVEN"
        ]
        is True
        and set(
            manifest["derived_endpoint_automorphism"]["reactive_sulfur_orbit"]
        )
        == {"S1", "S4"},
        "persisted automorphism",
    )
    _assert(
        manifest["rule_context_source_contains_shadow_unit_or_event_id"] is False,
        "shadow label in context source",
    )
    _assert(
        manifest["rule_context_independent_of_shadow_population"] is True,
        "context population independence",
    )
    _assert(
        manifest["cross_CCD_DTU_generalization_authorized"] is False,
        "DTU authority",
    )
    _assert(tuple(manifest["required_predicates"]) == gate.REQUIRED_PREDICATES, "predicates")
    _assert(
        tuple(manifest["forbidden_sole_predicates"])
        == gate.FORBIDDEN_SOLE_PREDICATES,
        "forbidden predicates",
    )
    _assert(
        manifest["readiness_mode"] == gate.READINESS_MODE
        and manifest["live_integration_ready"] is True
        and manifest["integration_into_live_successor_routing_performed"] is False,
        "manifest readiness",
    )

    _assert(len(rows) == 123, "inventory population")
    _assert(len({row["canonical_event_id"] for row in rows}) == 123, "event uniqueness")
    statuses = Counter(row["evaluation_status"] for row in rows)
    _assert(
        statuses
        == Counter(
            {
                gate.MATCHED_AUTO_NEGATIVE_EXACT: 2,
                gate.NOT_MATCHED: 121,
            }
        ),
        "event status counts",
    )
    matched = [row for row in rows if row["evaluation_status"] == gate.MATCHED_AUTO_NEGATIVE_EXACT]
    _assert(
        {(row["pdb_id"], row["ligand_component_id"], row["ligand_reactive_atom"]) for row in matched}
        == {("1FVG", "DTT", "S4"), ("1FVG", "DTT", "S1")},
        "matched endpoint identity",
    )
    dtu = [row for row in rows if row["ligand_component_id"] == "DTU"]
    _assert(len(dtu) == 1 and dtu[0]["evaluation_status"] == gate.NOT_MATCHED, "DTU result")
    dtu_failed = set(json.loads(dtu[0]["failed_predicates_json"]))
    _assert(
        {
            "exact_dtt_component_identity",
            "exact_dtt_component_graph_sha256",
            "exact_1fvg_source_structure_context",
        }
        <= dtu_failed,
        "DTU failed predicate evidence",
    )
    for component, record in manifest[
        "broader_sulfur_counterexample_observations"
    ].items():
        _assert(record["match_count"] == 0, component + " false positive")
    _assert(
        manifest["same_local_environment_lookalike_observation"][
            "unauthorized_shape_match_count"
        ]
        == 0,
        "local environment false positive",
    )
    _assert(manifest["human_relevant_counterexample_match_count"] == 0, "human positive")

    expected_summary = {
        "candidate_event_count": 123,
        "historical_review_unit_count": 36,
        "observed_shadow_matched_event_count": 2,
        "observed_shadow_matched_unit_count": 2,
        "human_calibration_matched_event_count": 1,
        "human_calibration_matched_unit_count": 1,
        "calibration_snapshot_unreviewed_shadow_auto_negative_event_count": 1,
        "calibration_snapshot_unreviewed_shadow_auto_negative_unit_count": 1,
        "DTU_counterexample_match_count": 0,
        "human_relevant_counterexample_match_count": 0,
        "invalid_evidence_count": 0,
        "generalization_without_sibling_label_leakage": True,
        "DTT_endpoint_automorphism_proven": True,
        "cross_CCD_DTU_generalization_authorized": False,
        "live_integration_ready": True,
        "integration_into_live_successor_routing_performed": False,
        "ready_for_gpt_review": True,
        "successor_routing_modified": False,
        "human_review_overlay_modified": False,
        "production_chemistry_authority_created": False,
        "training_materialization_performed": False,
    }
    for field, expected_value in expected_summary.items():
        _assert(summary.get(field) == expected_value, "summary field: " + field)
    _assert(summary["readiness_mode"] == gate.READINESS_MODE, "summary mode")
    _assert(
        summary["implementation_mode"]
        == "SHADOW_EXACT_GATE_NOT_YET_LIVE_SUCCESSOR_ROUTING",
        "implementation mode",
    )
    _assert(
        summary["recommended_next_step_exactly"]
        == "gpt_audit_DTT_exact_shadow_gate_then_commit_push_DTT_gate",
        "next step",
    )
    _assert(
        summary["output_sha256_excluding_summary"]
        == {
            gate.RULE_MANIFEST: hashlib.sha256(
                (output_root / gate.RULE_MANIFEST).read_bytes()
            ).hexdigest(),
            gate.SHADOW_INVENTORY: hashlib.sha256(
                (output_root / gate.SHADOW_INVENTORY).read_bytes()
            ).hexdigest(),
        },
        "output hash evidence",
    )
    _assert(replay_sha[gate.RULE_MANIFEST] == hashlib.sha256((output_root / gate.RULE_MANIFEST).read_bytes()).hexdigest(), "replay manifest")

    live_integration_observed = validate_successor_live_integration_v1(
        repo_root
    )

    current_human_payload = (repo_root / gate.HUMAN_DECISIONS_RELATIVE).read_bytes()
    current_human = json.loads(current_human_payload)
    current_human_overlay_sha256 = hashlib.sha256(current_human_payload).hexdigest()
    validate_current_human_overlay_coverage_v1(
        current_human=current_human, evidence=evidence
    )

    modified = set(filter(None, _git(repo_root, "diff", "--name-only").splitlines()))
    staged = set(
        filter(None, _git(repo_root, "diff", "--cached", "--name-only").splitlines())
    )
    untracked = set(
        filter(
            None,
            _git(repo_root, "ls-files", "--others", "--exclude-standard").splitlines(),
        )
    )
    worktree_profile = classify_worktree_profile_v1(
        modified=tuple(modified), staged=tuple(staged), untracked=tuple(untracked)
    )
    _assert(
        not any(Path(path).suffix.lower() in FORBIDDEN_SUFFIXES for path in untracked),
        "forbidden untracked suffix",
    )
    _assert(
        not any(
            path == protected or path.startswith(protected + "/")
            for path in modified | staged | untracked
            for protected in PROTECTED_SOURCE_PATHS
        ),
        "protected source touched",
    )
    raw_tracked_count = len(
        [
            line
            for line in _git(repo_root, "ls-files", "data/raw").splitlines()
            if line
        ]
    )
    raw_staged_count = len(
        [path for path in staged if path == "data/raw" or path.startswith("data/raw/")]
    )
    _assert(raw_staged_count == 0, "raw file staged")
    _assert(input_hashes == evidence["input_hashes"], "input binding drift")
    return {
        "rule_id": gate.RULE_ID,
        "candidate_event_count": len(rows),
        "matched_event_count": statuses[gate.MATCHED_AUTO_NEGATIVE_EXACT],
        "matched_unit_count": summary["observed_shadow_matched_unit_count"],
        "DTU_match_count": summary["DTU_counterexample_match_count"],
        "invalid_evidence_count": summary["invalid_evidence_count"],
        "DTT_endpoint_automorphism_proven": summary[
            "DTT_endpoint_automorphism_proven"
        ],
        "live_integration_ready": summary["live_integration_ready"],
        "live_integration_observed": live_integration_observed,
        "untracked_file_count": len(untracked),
        "modified_tracked_file_count": len(modified),
        "staged_file_count": len(staged),
        "runtime_head": git_state["head"],
        "runtime_origin_main": git_state["origin_main"],
        "current_human_overlay_sha256": current_human_overlay_sha256,
        "worktree_profile": worktree_profile,
        "raw_tracked_legacy_count": raw_tracked_count,
        "raw_staged_count": raw_staged_count,
        "protected_source_change_count": 0,
        "forbidden_new_file_count": 0,
        "deterministic_replay_sha256": replay_sha,
        "status": "PASS",
    }


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--cache-root", type=Path)
    return parser.parse_args()


def main() -> None:
    arguments = _arguments()
    print(
        json.dumps(
            check_v1(arguments.repo_root, arguments.cache_root),
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
