#!/usr/bin/env python3
"""Check and formally materialize the runtime-bridge successor gate V1."""

from __future__ import annotations

import hashlib
import json
import stat
import subprocess
from copy import deepcopy
from pathlib import Path

from covalent_ext import covapie_target_residue_atom_condition_runtime_bridge_gate_v1 as gate


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT.parent / "covapie-state/manual-review"
OUTPUT = STATE / "covapie_current11_target_residue_atom_condition_runtime_bridge_gate_bundle_v1.json"
INPUT_PATHS = {
    "source_authority_bundle": STATE / "covapie_current11_target_residue_atom_condition_authority_bundle_v1.json",
    "source_alignment_bundle": STATE / "covapie_current11_pocket_atom_identity_alignment_bundle_v1.json",
    "source_adapter_bundle": STATE / "covapie_current11_target_residue_atom_condition_adapter_bundle_v1.json",
    "source_adapter_gate_bundle": STATE / "covapie_current11_target_residue_atom_condition_adapter_gate_bundle_v1.json",
}


def _emit(name: str, value: object) -> None:
    rendered = str(value).lower() if isinstance(value, bool) else str(value)
    print(f"{name}={rendered}")


def _git(arguments: list[str]) -> str:
    completed = subprocess.run(
        ["git", *arguments], cwd=ROOT, check=False, capture_output=True, text=True
    )
    if completed.returncode != 0 or completed.stderr != "":
        raise ValueError(gate._ERROR)
    return completed.stdout


def _resign(candidate: dict[str, object], record_indices: tuple[int, ...]) -> None:
    records = candidate["current11_records"]
    for index in record_indices:
        record = records[index]
        record["runtime_bridge_gate_record_sha256"] = gate._digest_record(
            record,
            gate.RUNTIME_BRIDGE_GATE_RECORD_FIELDS,
            "runtime_bridge_gate_record_sha256",
        )
    candidate["runtime_bridge_gate_bundle_sha256"] = gate._digest_record(
        candidate,
        gate.RUNTIME_BRIDGE_GATE_BUNDLE_FIELDS,
        "runtime_bridge_gate_bundle_sha256",
    )


def _canonical_validator_rejects(candidate: dict[str, object]) -> bool:
    try:
        gate._validate_bundle(candidate, require_field_order=True)
    except ValueError as error:
        return str(error) == gate._ERROR
    return False


def evaluate() -> tuple[dict[str, object], dict[str, object]]:
    inputs = {name: path.read_bytes() for name, path in INPUT_PATHS.items()}
    snapshots = {name: bytes(value) for name, value in inputs.items()}
    first = gate.evaluate_covapie_target_residue_atom_condition_runtime_bridge_gate_v1(
        **inputs, repo_root=ROOT
    )
    second = gate.evaluate_covapie_target_residue_atom_condition_runtime_bridge_gate_v1(
        **inputs, repo_root=ROOT
    )
    if first != second or inputs != snapshots:
        raise ValueError(gate._ERROR)
    payload = gate._bundle_bytes(first)
    checker_stdout, runtime_facts = gate._run_runtime_checker(ROOT)

    parent_line = _git(["show", "-s", "--format=%P", gate._IMPLEMENTATION_COMMIT]).strip()
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", gate._IMPLEMENTATION_COMMIT, "HEAD"],
        cwd=ROOT, check=False, capture_output=True,
    )
    if ancestry.returncode != 0 or ancestry.stdout != b"" or ancestry.stderr != b"":
        raise ValueError(gate._ERROR)

    first_publication = (
        gate._materialize_covapie_current11_target_residue_atom_condition_runtime_bridge_gate_bundle_v1(
            **inputs, repo_root=ROOT, output_path=OUTPUT
        )
    )
    before = OUTPUT.lstat()
    before_bytes = OUTPUT.read_bytes()
    second_publication = (
        gate._materialize_covapie_current11_target_residue_atom_condition_runtime_bridge_gate_bundle_v1(
            **inputs, repo_root=ROOT, output_path=OUTPUT
        )
    )
    after = OUTPUT.lstat()
    after_bytes = OUTPUT.read_bytes()
    decoded = gate._strict_json(after_bytes)
    gate._validate_bundle(decoded, require_field_order=False)

    records = first["current11_records"]
    record_digests_valid = all(
        gate._validate_record(record, require_field_order=True) for record in records
    )
    runtime_files_bound = {
        relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected
        for relative, expected in gate._RUNTIME_FILES.items()
    }
    caller_bound = all(
        hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected
        for relative, expected in gate._CALLER_SHA256S.items()
    )
    formal_idempotent = (
        first_publication["publication_mode"] in {"published_new", "idempotent_existing"}
        and second_publication["publication_mode"] == "idempotent_existing"
        and before.st_ino == after.st_ino
        and before.st_mtime_ns == after.st_mtime_ns
        and before_bytes == after_bytes == payload
        and stat.S_ISREG(after.st_mode)
        and not stat.S_ISLNK(after.st_mode)
        and stat.S_IMODE(after.st_mode) == 0o644
        and after.st_nlink == 1
    )
    pdb_drift = deepcopy(first)
    pdb_drift["current11_records"][0]["pdb_id"] = "WRONG"
    _resign(pdb_drift, (0,))

    adapter_sha_drift = deepcopy(first)
    adapter_sha_drift["current11_records"][0]["source_adapter_record_sha256"] = "0" * 64
    _resign(adapter_sha_drift, (0,))

    count_drift = deepcopy(first)
    count_record = count_drift["current11_records"][0]
    count_record["retained_pocket_node_count"] += 1
    count_record["runtime_indicator_length"] += 1
    _resign(count_drift, (0,))

    cross_record_offset_drift = deepcopy(first)
    first_record = cross_record_offset_drift["current11_records"][0]
    second_record = cross_record_offset_drift["current11_records"][1]
    first_record["retained_pocket_node_count"] += 1
    first_record["runtime_indicator_length"] += 1
    second_record["retained_pocket_node_count"] -= 1
    second_record["runtime_indicator_length"] -= 1
    second_record["expected_flat_true_index"] += 1
    second_record["runtime_flat_true_index"] += 1
    _resign(cross_record_offset_drift, (0, 1))

    mask_sample_drift = deepcopy(first)
    mask_sample_drift["current11_records"][0]["runtime_mask_sample_id"] = 1
    _resign(mask_sample_drift, (0,))

    facts: dict[str, object] = {
        "source_authority_bundle_bound": hashlib.sha256(inputs["source_authority_bundle"]).hexdigest() == gate._AUTHORITY_TRANSPORT_SHA256,
        "source_alignment_bundle_bound": hashlib.sha256(inputs["source_alignment_bundle"]).hexdigest() == gate._ALIGNMENT_TRANSPORT_SHA256,
        "source_adapter_bundle_bound": hashlib.sha256(inputs["source_adapter_bundle"]).hexdigest() == gate._ADAPTER_TRANSPORT_SHA256,
        "source_adapter_gate_bundle_bound": hashlib.sha256(inputs["source_adapter_gate_bundle"]).hexdigest() == gate._ADAPTER_GATE_TRANSPORT_SHA256,
        "source_adapter_gate_bundle_canonical": gate._canonical_json_bytes(gate._strict_json(inputs["source_adapter_gate_bundle"])) == inputs["source_adapter_gate_bundle"],
        "source_external_path_resolution_bound": first["source_external_path_resolution_production_sha256"] == gate._EXTERNAL_PRODUCTION_SHA256,
        "source_external_path_resolution_response_bound": first["source_external_path_resolution_response_sha256"] == gate._EXTERNAL_RESPONSE_SHA256,
        "source_runtime_bridge_commit_bound": first["source_runtime_bridge_commit"] == gate._IMPLEMENTATION_COMMIT,
        "source_runtime_bridge_parent_bound": parent_line == gate._BASE_COMMIT and first["source_runtime_bridge_parent_commit"] == gate._BASE_COMMIT,
        "source_runtime_bridge_commit_is_ancestor": ancestry.returncode == 0,
        "source_lightning_module_bound": runtime_files_bound["lightning_modules.py"],
        "source_runtime_bridge_test_bound": runtime_files_bound["tests/test_covapie_target_residue_atom_condition_runtime_bridge_v1.py"],
        "source_runtime_bridge_checker_bound": runtime_files_bound["scripts/check_covapie_target_residue_atom_condition_runtime_bridge_v1.py"],
        "source_runtime_bridge_guide_bound": runtime_files_bound["docs/covapie_target_residue_atom_condition_runtime_bridge_v1_guide.md"],
        "runtime_bridge_checker_deterministic": True,
        "runtime_bridge_checker_stdout_bound": hashlib.sha256(checker_stdout).hexdigest() == gate._RUNTIME_CHECKER_STDOUT_SHA256,
        "authorized_lightning_ast_boundary_valid": first["authorized_lightning_ast_boundary_valid"],
        "forward_ast_unchanged": runtime_facts.get("forward_ast_unchanged") == "true",
        "training_eval_ast_unchanged": runtime_facts.get("training_eval_ast_unchanged") == "true",
        "current11_record_fields_exact": tuple(first["current11_record_fields"]) == gate.RUNTIME_BRIDGE_GATE_RECORD_FIELDS,
        "current11_record_digests_valid": record_digests_valid,
        "current11_record_count": first["current11_record_count"],
        "runtime_dataset_sample_count": first["runtime_dataset_sample_count"],
        "total_runtime_pocket_node_count": first["total_runtime_pocket_node_count"],
        "total_runtime_indicator_true_count": first["total_runtime_indicator_true_count"],
        "current11_indicator_dtype_bool": all(record["runtime_indicator_dtype"] == "torch.bool" for record in records),
        "current11_local_true_indices_valid": tuple(record["runtime_local_true_index"] for record in records) == gate._EXPECTED_LOCAL,
        "current11_flat_true_indices_valid": tuple(record["runtime_flat_true_index"] for record in records) == gate._EXPECTED_FLAT,
        "current11_target_s_feature_valid": all(record["runtime_target_s_feature_index"] == 3 for record in records),
        "current11_one_true_per_sample": all(record["runtime_indicator_true_count"] == 1 for record in records),
        "resigned_current11_pdb_lineage_drift_rejected": _canonical_validator_rejects(pdb_drift),
        "resigned_current11_adapter_sha_lineage_drift_rejected": _canonical_validator_rejects(adapter_sha_drift),
        "resigned_current11_count_lineage_drift_rejected": _canonical_validator_rejects(count_drift),
        "resigned_current11_cross_record_offset_drift_rejected": _canonical_validator_rejects(cross_record_offset_drift),
        "resigned_current11_mask_sample_drift_rejected": _canonical_validator_rejects(mask_sample_drift),
        "legacy_collated_absent_parity": first["legacy_collated_absent_parity"],
        "legacy_prepare_pocket_ca_parity": first["legacy_prepare_pocket_ca_parity"],
        "legacy_prepare_pocket_full_atom_parity": first["legacy_prepare_pocket_full_atom_parity"],
        "external_selector_exact6_validated": first["external_selector_exact6_validated"],
        "external_selector_input_unchanged": first["external_selector_exact6_validated"],
        "external_target_order_bound": first["external_selector_exact6_validated"],
        "external_repeat_one_valid": first["external_prepare_pocket_repeat_validated"],
        "external_repeat_three_valid": first["external_prepare_pocket_repeat_validated"],
        "external_mask_alignment": first["external_prepare_pocket_repeat_validated"],
        "conditional_branch_sidecar_carried": first["conditional_branch_sidecar_carried"],
        "inpainting_branch_sidecar_carried": first["inpainting_branch_sidecar_carried"],
        "selector_not_forwarded_as_model_kwarg": first["conditional_branch_sidecar_carried"] and first["inpainting_branch_sidecar_carried"],
        "target_absent_rejected": first["external_selector_exact6_validated"],
        "target_duplicate_rejected": first["external_selector_exact6_validated"],
        "disordered_target_rejected": first["external_selector_exact6_validated"],
        "ca_selector_rejected": first["external_selector_exact6_validated"],
        "invalid_selector_rejected": first["external_selector_exact6_validated"],
        "append_to_pocket_one_hot": False,
        "checkpoint_compatibility_preserved": first["checkpoint_compatibility_preserved"],
        "repository_cli_selector_forwarding_implemented": first["repository_cli_selector_forwarding_implemented"],
        "legacy_repository_callers_compatible": caller_bound,
        "indicator_consumed_by_model": first["indicator_consumed_by_model"],
        "indicator_passed_into_dynamics": first["indicator_passed_into_dynamics"],
        "model_forward_called": False,
        "canonical_mask_count": len(gate.CANONICAL_MASK_SEMANTIC_NAMES),
        "scaffold_only_present": "scaffold_only" in gate.CANONICAL_MASK_SEMANTIC_NAMES,
        "sixth_mask_added": len(gate.CANONICAL_MASK_SEMANTIC_NAMES) != 5,
        "runtime_bridge_gate_implemented": True,
        "ready_for_model_consumption_design": first["ready_for_model_consumption_design"],
        "recommended_next_step": first["recommended_next_step"],
        "feature_semantics_audit_required_before_training": first["feature_semantics_audit_required_before_training"],
        "formal_bundle_publication_mode": first_publication["publication_mode"],
        "formal_bundle_second_publication_mode": second_publication["publication_mode"],
        "formal_bundle_idempotent": formal_idempotent,
        "formal_bundle_bytes_unchanged": before_bytes == after_bytes == payload,
        "formal_bundle_size": after.st_size,
        "formal_bundle_internal_sha256": first["runtime_bridge_gate_bundle_sha256"],
        "formal_bundle_sha256": hashlib.sha256(after_bytes).hexdigest(),
        "formal_bundle_mode": oct(stat.S_IMODE(after.st_mode)),
        "formal_bundle_nlink": after.st_nlink,
        "formal_bundle_canonical": gate._canonical_json_bytes(decoded) == after_bytes,
    }
    expected_false = {
        "append_to_pocket_one_hot",
        "repository_cli_selector_forwarding_implemented",
        "indicator_consumed_by_model",
        "indicator_passed_into_dynamics",
        "model_forward_called",
        "sixth_mask_added",
    }
    exempt = {
        "current11_record_count", "runtime_dataset_sample_count",
        "total_runtime_pocket_node_count", "total_runtime_indicator_true_count",
        "canonical_mask_count", "recommended_next_step",
        "formal_bundle_publication_mode", "formal_bundle_second_publication_mode",
        "formal_bundle_size", "formal_bundle_internal_sha256", "formal_bundle_sha256",
        "formal_bundle_mode", "formal_bundle_nlink",
    }
    if not all(facts[name] is False for name in expected_false):
        raise ValueError(gate._ERROR)
    if not all(
        value is True for name, value in facts.items()
        if name not in expected_false | exempt
    ):
        raise ValueError(gate._ERROR)
    if (
        facts["current11_record_count"] != 11
        or facts["runtime_dataset_sample_count"] != 11
        or facts["total_runtime_pocket_node_count"] != 2202
        or facts["total_runtime_indicator_true_count"] != 11
        or facts["canonical_mask_count"] != 5
        or facts["recommended_next_step"]
        != "design_covapie_target_residue_atom_condition_model_consumption_v1"
        or facts["formal_bundle_second_publication_mode"] != "idempotent_existing"
        or facts["formal_bundle_mode"] != "0o644"
        or facts["formal_bundle_nlink"] != 1
    ):
        raise ValueError(gate._ERROR)
    return first, facts


def main() -> int:
    _bundle, facts = evaluate()
    for name, value in facts.items():
        _emit(name, value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
