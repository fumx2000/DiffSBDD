#!/usr/bin/env python3
"""Fail-closed checker for the revised exact TS/dUMP shadow gate V1."""

from __future__ import annotations

from collections import Counter, defaultdict
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Sequence

from covalent_ext import covapie_post_only_auto_negative_ts_dump_exact_v1 as gate


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
        {path.name for path in output_root.iterdir() if path.is_file()}
        == set(gate.OUTPUT_FILENAMES),
        "output file set mismatch",
    )
    _assert(
        not any(
            path.is_file() and path.suffix in {".tmp", ".part"}
            for path in output_root.iterdir()
        ),
        "temporary output remains",
    )

    git_state = gate.verify_repository_binding_v1(repo_root)
    _assert(git_state["descendant_repository_compatible"] is True, "descendant git")
    input_hashes = gate.verify_bound_inputs_v1(repo_root)
    gate.load_immutable_human_gold_v1(repo_root)

    current_human_payload = (repo_root / gate.HUMAN_DECISIONS_RELATIVE).read_bytes()
    current_human = json.loads(current_human_payload)
    current_units = gate.validate_current_human_overlay_v1(current_human)
    current_human_sha = hashlib.sha256(current_human_payload).hexdigest()
    _assert(len(current_units) >= 36, "current human overlay unit coverage")

    expected = gate.build_artifacts_v1(
        repo_root=repo_root, cache_root=resolved_cache
    )
    output_hashes: dict[str, str] = {}
    for name in gate.OUTPUT_FILENAMES:
        payload = (output_root / name).read_bytes()
        _assert(payload == expected[name], "deterministic replay mismatch: " + name)
        output_hashes[name] = hashlib.sha256(payload).hexdigest()
    _assert(gate.verify_bound_inputs_v1(repo_root) == input_hashes, "inputs changed")

    manifest = json.loads((output_root / gate.RULE_MANIFEST).read_text())
    summary = json.loads((output_root / gate.SUMMARY).read_text())
    rows = _csv(output_root / gate.SHADOW_INVENTORY, gate.SHADOW_HEADER)
    _assert(not _contains_absolute_path(manifest), "manifest absolute path")
    _assert(not _contains_absolute_path(summary), "summary absolute path")
    _assert(manifest["schema_version"] == gate.SCHEMA_VERSION, "manifest schema")
    _assert(manifest["rule_id"] == gate.RULE_ID, "manifest rule")
    _assert(
        manifest["immutable_calibration_gold_git_object"]
        == gate.CALIBRATION_COMMIT + ":" + gate.HUMAN_DECISIONS_RELATIVE.as_posix(),
        "immutable calibration object",
    )
    _assert(
        manifest["calibration_artifact_binding"]["sha256"]
        == gate.CALIBRATION_HUMAN_SHA256,
        "immutable calibration hash",
    )
    _assert(manifest["input_artifact_sha256"] == input_hashes, "input bindings")
    _assert(manifest["shadow_label_leakage_prohibited"] is True, "label leakage")
    _assert(
        manifest["rule_context_is_independent_of_shadow_evaluation_population"]
        is True,
        "population independence",
    )
    _assert(
        manifest["target_family_context_was_derived_from_shadow_matches"] is False,
        "target context provenance",
    )
    _assert(manifest["descendant_repository_compatible"] is True, "descendant flag")
    _assert(
        "CURRENT_HUMAN_RELEVANT" in manifest["runtime_positive_override_policy"],
        "runtime override policy",
    )
    _assert(
        manifest["shadow_runtime_context_observation"][
            "current_human_overlay_sha256"
        ]
        == current_human_sha,
        "current human SHA reported separately",
    )

    context = manifest["scientific_rule_context"]
    context_json = json.dumps(context, sort_keys=True)
    evidence = gate._load_bound_evidence_v1(repo_root)
    sibling_ids = evidence["unit_by_id"][gate.SIBLING_UNIT_ID]["canonical_event_ids"]
    _assert(gate.SIBLING_UNIT_ID not in context_json, "sibling unit leaked into context")
    _assert(
        all(event_id not in context_json for event_id in sibling_ids),
        "sibling event leaked into context",
    )
    _assert("shadow_expected_counts" not in context_json, "expected count in context")
    _assert(
        context["target_family_context_provenance"]
        == gate.TARGET_FAMILY_CONTEXT_PROVENANCE,
        "target family provenance",
    )
    _assert(
        context["target_family_context_input_sha256"][
            gate.UPSTREAM_ACQUISITION_RELATIVE.as_posix()
        ]
        == gate.INPUT_SHA256[gate.UPSTREAM_ACQUISITION_RELATIVE],
        "target input SHA",
    )
    _assert(context["source_verified_structure_count"] == 175, "source count")
    _assert(context["structured_ec_matched_structure_count"] == 20, "EC count")
    _assert(context["authorized_target_family_key_count"] == 15, "key count")
    _assert(context["rule_identity_excludes_pdb_id"] is True, "PDB identity")
    _assert(context["rule_identity_excludes_chain_id"] is True, "chain identity")
    _assert(
        "structured_catalytic_context_support" not in context["required_predicates"],
        "catalytic semantic overclaim remains",
    )
    _assert(
        "exact_ts_family_accession_sequence_key" in context["required_predicates"],
        "exact TS family predicate missing",
    )
    registry = context["authorized_target_family_registry"]
    _assert(len(registry) == 15, "registry length")
    _assert(
        len(
            {
                (
                    item["protein_accession"],
                    item["protein_sequence_sha256"],
                    item["protein_reactive_atom"],
                    item["structured_target_family_id"],
                )
                for item in registry
            }
        )
        == 15,
        "registry uniqueness",
    )
    _assert(
        all(
            item["structured_target_family_id"] == "EC:2.1.1.45"
            and item["provenance_records"]
            for item in registry
        ),
        "registry structured evidence",
    )

    _assert(len(rows) == 123, "candidate event count")
    _assert(len({row["canonical_event_id"] for row in rows}) == 123, "event IDs")
    counts = Counter(row["evaluation_status"] for row in rows)
    _assert(
        counts
        == Counter(
            {gate.MATCHED_AUTO_NEGATIVE_EXACT: 47, gate.NOT_MATCHED: 76}
        ),
        "observed shadow event counts",
    )
    _assert(counts[gate.INVALID_EVIDENCE] == 0, "invalid evidence")
    matched = [
        row
        for row in rows
        if row["evaluation_status"] == gate.MATCHED_AUTO_NEGATIVE_EXACT
    ]
    matched_by_unit = Counter(row["review_unit_id"] for row in matched)
    _assert(
        matched_by_unit
        == Counter({gate.CALIBRATION_UNIT_ID: 16, gate.SIBLING_UNIT_ID: 31}),
        "matched units",
    )
    _assert(
        all(
            json.loads(row["matched_predicates_json"])
            == list(gate.REQUIRED_PREDICATES)
            for row in matched
        ),
        "matched predicate coverage",
    )

    rows_by_unit: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        rows_by_unit[row["review_unit_id"]].append(row)
    _assert(len(rows_by_unit) == 36, "review unit count")
    for unit_id, unit_rows in rows_by_unit.items():
        all_match = all(
            row["evaluation_status"] == gate.MATCHED_AUTO_NEGATIVE_EXACT
            for row in unit_rows
        )
        _assert(
            all(
                row["shadow_would_auto_negative"]
                == ("true" if all_match else "false")
                for row in unit_rows
            ),
            "unit aggregation: " + unit_id,
        )

    for unit_id in gate.UFP_COUNTEREXAMPLE_UNITS:
        for row in rows_by_unit[unit_id]:
            _assert(row["evaluation_status"] == gate.NOT_MATCHED, "UFP matched")
            failed = gate._reason_failed_predicates(row["evaluation_reason"])
            _assert(
                {
                    "exact_ccd_component_graph_sha256",
                    "exact_radius2_sha256",
                }
                <= failed,
                "UFP exact chemistry boundary",
            )
            _assert(
                "exact_ts_family_accession_sequence_key"
                in json.loads(row["matched_predicates_json"]),
                "UFP TS family recognition",
            )
    for unit_id in gate.HUMAN_RELEVANT_COUNTEREXAMPLE_UNITS:
        _assert(
            all(
                row["evaluation_status"] != gate.MATCHED_AUTO_NEGATIVE_EXACT
                for row in rows_by_unit[unit_id]
            ),
            "human positive matched: " + unit_id,
        )
    _assert(
        all(
            row["evaluation_status"] != gate.MATCHED_AUTO_NEGATIVE_EXACT
            for row in rows_by_unit[gate.PYR_COUNTEREXAMPLE_UNIT]
        ),
        "PYR matched",
    )

    _assert(summary["readiness_mode"] == gate.GENERALIZATION_MODE, "readiness")
    for field in (
        "generalization_without_sibling_label_leakage",
        "target_family_generalization_authorized",
        "live_integration_ready",
        "shadow_label_leakage_removed",
        "rule_context_independent_of_shadow_population",
        "descendant_repository_compatible",
        "current_human_overlay_no_longer_frozen_to_calibration_sha",
        "future_human_positive_override_supported",
        "ready_for_gpt_review",
    ):
        _assert(summary[field] is True, "summary truth: " + field)
    _assert(summary["observed_shadow_matched_event_count"] == 47, "summary events")
    _assert(summary["observed_shadow_matched_unit_count"] == 2, "summary units")
    _assert(summary["UFP_counterexample_match_count"] == 0, "summary UFP")
    _assert(
        summary["calibration_snapshot_human_relevant_match_count"] == 0,
        "summary human positive",
    )
    _assert(summary["PYR_boundary_match_count"] == 0, "summary PYR")
    _assert(
        summary["recommended_next_step_exactly"]
        == "gpt_audit_revised_exact_gate_then_integrate_into_successor_bulk_triage",
        "next step",
    )
    for field in (
        "legacy_triage_artifacts_modified",
        "human_review_overlay_modified",
        "production_chemistry_authority_created",
        "training_materialization_performed",
        "integration_into_live_triage_performed",
    ):
        _assert(summary[field] is False, "safety: " + field)
    _assert(
        summary["output_sha256_excluding_summary"]
        == {
            gate.RULE_MANIFEST: output_hashes[gate.RULE_MANIFEST],
            gate.SHADOW_INVENTORY: output_hashes[gate.SHADOW_INVENTORY],
        },
        "output hashes",
    )

    tracked_worktree = _git(repo_root, "diff", "--name-only")
    staged = _git(repo_root, "diff", "--cached", "--name-only")
    untracked = _git(repo_root, "ls-files", "--others", "--exclude-standard").splitlines()
    _assert(tracked_worktree == "", "existing tracked file modified")
    _assert(staged == "", "staged path exists")
    _assert(
        set(untracked) == {path.as_posix() for path in gate.AUTHORIZED_NEW_PATHS},
        "untracked path set is not exact seven-file scope",
    )
    forbidden_suffixes = {
        ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip",
        ".tgz", ".npz", ".tmp", ".part",
    }
    _assert(
        not any(Path(path).suffix in forbidden_suffixes for path in untracked),
        "forbidden untracked suffix",
    )
    _assert(not any(path.startswith("data/raw/") for path in untracked), "raw")
    return {
        "rule_id": gate.RULE_ID,
        "readiness_mode": summary["readiness_mode"],
        "candidate_event_count": len(rows),
        "observed_matched_event_count": counts[gate.MATCHED_AUTO_NEGATIVE_EXACT],
        "observed_matched_unit_count": len(matched_by_unit),
        "invalid_evidence_count": counts[gate.INVALID_EVIDENCE],
        "target_family_key_count": len(registry),
        "current_human_overlay_sha256": current_human_sha,
        "immutable_calibration_gold_sha256": gate.CALIBRATION_HUMAN_SHA256,
        "deterministic_output_sha256": output_hashes,
        "git_state": git_state,
        "untracked_file_count": len(untracked),
        "staged_file_count": 0,
        "modified_existing_tracked_file_count": 0,
        "ready_for_gpt_review": True,
    }


def main() -> None:
    print(json.dumps(check_v1(Path.cwd()), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
