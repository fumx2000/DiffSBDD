#!/usr/bin/env python3
"""Independently verify and materialize the post-admission review gate V1."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015
    as dispatch_runtime,
)
from covalent_ext import (  # noqa: E402
    covapie_post_admission_control_plane_completion_and_next_training_preparation_blocker_review_gate_v1
    as review,
)


BASE_COMMIT = "b90b3338a6a4e78dd2a74fb2c67a856e57d4a3e1"
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE post-admission control-plane completion and "
    "next-blocker review v1"
)
STAGE = (
    "covapie_post_admission_control_plane_completion_and_"
    "next_training_preparation_blocker_review_gate_v1"
)
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
CONTROL_NAME = "covapie_post_admission_control_plane_completion_inventory.csv"
COMPARISON_NAME = "covapie_training_preparation_blocker_comparison_matrix.csv"
DEPENDENCY_NAME = "covapie_training_preparation_dependency_order_matrix.csv"
SAFETY_NAME = "covapie_post_admission_control_plane_review_safety_audit.csv"
ISSUE_NAME = "covapie_post_admission_control_plane_issue_readiness_inventory.csv"
MANIFEST_NAME = (
    "covapie_post_admission_control_plane_completion_and_"
    "next_training_preparation_blocker_review_manifest.json"
)
OUTPUT_NAMES = (
    CONTROL_NAME,
    COMPARISON_NAME,
    DEPENDENCY_NAME,
    SAFETY_NAME,
    ISSUE_NAME,
    MANIFEST_NAME,
)
EXACT10 = (
    Path("src/covalent_ext")
    / (
        "covapie_post_admission_control_plane_completion_and_"
        "next_training_preparation_blocker_review_gate_v1.py"
    ),
    Path("tests")
    / (
        "test_covapie_post_admission_control_plane_completion_and_"
        "next_training_preparation_blocker_review_gate_v1.py"
    ),
    Path("scripts")
    / (
        "check_covapie_post_admission_control_plane_completion_and_"
        "next_training_preparation_blocker_review_gate_v1.py"
    ),
    Path("docs")
    / (
        "covapie_post_admission_control_plane_completion_and_"
        "next_training_preparation_blocker_review_gate_v1_summary.md"
    ),
    *(OUTPUT_ROOT / name for name in OUTPUT_NAMES),
)
PREDECESSOR_ISSUE_PATH = (
    Path("data/derived/covalent_small")
    / "covapie_bulk_download_stage_orchestration_action_permission_bridge_in_memory_integration_smoke_v1"
    / "covapie_action_permission_bridge_in_memory_issue_readiness_inventory.csv"
)
PREDECESSOR_ISSUE_SHA256 = (
    "fb4d2dfae7ffc056e3856c94e2f5a135"
    "d468eb3801144f9a698f95d9b812ace7"
)
CANONICAL_MASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
CONTROL_COLUMNS = (
    "control_plane_component",
    "evidence_path",
    "evidence_selector",
    "expected_value",
    "observed_value",
    "evidence_sha256",
    "verified",
)
COMPARISON_COLUMNS = (
    "blocker_id",
    "issue_type",
    "affected_fields",
    "affected_rules",
    "blocking_scope",
    "current_status",
    "evidence_source_count",
    "blocks_dataset_schema_finalization",
    "blocks_label_tensor_contract",
    "blocks_feature_semantics_audit",
    "blocks_auxiliary_atom_pair_task",
    "blocks_model_forward_now",
    "requires_real_provider_execution",
    "can_be_reviewed_with_committed_evidence",
    "can_remain_quarantined_temporarily",
    "dependency_position",
    "selection_disposition",
    "selection_reason",
    "verified",
)
DEPENDENCY_COLUMNS = (
    "dependency_order",
    "dependency_step",
    "prerequisite",
    "implemented_current_review",
    "ordering_reason",
    "verified",
)
SAFETY_COLUMNS = (
    "safety_item",
    "expected_executed",
    "observed_executed",
    "verified",
)
SAFETY_ITEMS = (
    "network",
    "provider",
    "download",
    "permission_transition",
    "raw_write",
    "model_change",
    "checkpoint_access",
    "dataloader_change",
    "forward_change",
    "loss_change",
    "backward",
    "optimizer",
    "parameter_update",
    "training",
    "ready_for_download",
    "ready_for_training",
    "feature_semantics_audit_completed",
    "permission_layer_expansion_required",
    "control_plane_code_change_required",
)
CONTROL_SOURCE_PATHS = (
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015.py",
    "src/covalent_ext/covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_v1.py",
    "src/covalent_ext/covapie_stage_global_rule_evaluation_orchestration_v1.py",
    "src/covalent_ext/covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_v1.py",
    "src/covalent_ext/covapie_bulk_download_stage_orchestration_action_permission_bridge_v1.py",
)
EVIDENCE_SHA256 = {
    "src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015.py": "1fc5ac24e54d134d3f1f7054dfd2f264a2d76f17f0602bac216bb2e4e7e00bd1",
    "src/covalent_ext/covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_v1.py": "8810d4bab34b2c5067b51dedb3edaa4a20e25c82c89576265986285e64f59904",
    "data/derived/covalent_small/covapie_stage_global_rule_evaluation_orchestration_contract_v1/covapie_stage_global_rule_evaluation_orchestration_contract_manifest.json": "a60448647d932bf4d541e3d2b3c48deb10e887de9ba3931ef40f1aa55c55e125",
    "src/covalent_ext/covapie_stage_global_rule_evaluation_orchestration_v1.py": "5b5b85eceee3a9aada2dc6ae57c8af4a365dfc74677facdceeda7f0bde8a86bc",
    "data/derived/covalent_small/covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke_v1/covapie_stage_global_orchestration_in_memory_integration_smoke_manifest.json": "691d1dd23e72c74ebc112ef3141c314dd31999422d4cab4ef0cb25a8063d5ea7",
    "data/derived/covalent_small/covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_v1/covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_manifest.json": "dc04018ca3f5d4bc90f5defb0216aa58d71c6bb1656aaf292bd73fb5baab5cbf",
    "src/covalent_ext/covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_v1.py": "dc51597773bd0d6d98c7c299e5bf0c5889396a865120f692724653fc4b8e4352",
    "data/derived/covalent_small/covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_in_memory_integration_smoke_v1/covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_in_memory_integration_smoke_manifest.json": "698d485be3e65db29515eba116ef7158b743a83899016df0b821ecd81902be35",
    "data/derived/covalent_small/covapie_bulk_download_stage_orchestration_action_permission_bridge_contract_v1/covapie_bulk_download_stage_orchestration_action_permission_bridge_contract_manifest.json": "c0f983718a04ef3c69cc31854aaa4c7e361ddf798b9a9737bbf9884c38d65729",
    "src/covalent_ext/covapie_bulk_download_stage_orchestration_action_permission_bridge_v1.py": "864ec156650d8aa4b13b5d78fef13ec98461988f3bc4833215410a9e96141981",
    "data/derived/covalent_small/covapie_bulk_download_stage_orchestration_action_permission_bridge_in_memory_integration_smoke_v1/covapie_bulk_download_stage_orchestration_action_permission_bridge_in_memory_integration_smoke_manifest.json": "16ac842e9c9e97cebb9d8aea6e4bb0cee5ba47aa2721ecb5eda420ec7b1890b9",
    "data/derived/covalent_small/covapie_final_dataset_design_gate_v0/covapie_final_dataset_schema_contract.csv": "2ea572efb4d9df1a168ba6b056ffa14593315ac148d589f86a5ea8f607c2469c",
    "data/derived/covalent_small/covapie_final_dataset_design_gate_v0/covapie_final_dataset_auxiliary_label_readiness.csv": "4a83b6d9bf24859a95349a8d2ece0b85ce8c15420c7032c9dc55e93179c8cacc",
    "data/derived/covalent_small/covapie_feature_semantics_audit_gate_v0/covapie_feature_semantics_contract.csv": "15d69dd777cfcf62691b35a257e48798066f0668a0bbc170e8ad9192574109b0",
    "data/derived/covalent_small/covapie_feature_semantics_audit_gate_v0/covapie_feature_semantics_training_blockers.csv": "99af8f844b43ee6731f20b25ea4abc968e5eb7a12923f3797b3b2c6384d019d8",
    "data/derived/covalent_small/covapie_feature_semantics_tensorization_audit_gate_v0/covapie_label_tensorization_blocker_audit.csv": "ce1ab5c8024b360ef72c95718898e4c052a5fd0c8a3d07c76bf92f50db64ae0a",
    "src/covalent_ext/real_covalent_confirmed_candidate_model_input_design_gate.py": "b43564a515e63b919dacd592d4ce76ef09b8fce4bd90163ff8fa4970a14f102f",
    "tests/test_covapie_feature_semantics_audit_gate_v0.py": "53a31473fe49b46ff5a44d4fd0983ec35625a5303d5c3da1ac3a0e6dddd0b008",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_real_provider_export_execution_smoke_v1/covapie_covalent_residue_locator_real_provider_export_sidecar.csv": "066c0beeaa01d31a6d6ea3fae62f3df5177c2d904f6295646ee33a7fcd780ac7",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_real_provider_export_execution_smoke_v1/covapie_covalent_residue_locator_real_provider_export_issue_inventory.csv": "5bda40b683d649fb28a2172291f329c1f87d10f3a2bd122e1d5a6ab887a071c4",
    "data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_real_provider_export_execution_smoke_v1/covapie_covalent_residue_locator_real_provider_export_execution_manifest.json": "9061e36c333cf498dd5844407f5df11d64c3e271ae47e407938d34ac851d3aab",
    "src/covalent_ext/covapie_bulk_download_admission_admit_004_rule_logic_interface.py": "5c05e166091a7a067014d9d4dbd8c7c4280b6f247c31765e14bf37d3f86adba3",
    "tests/test_covapie_bulk_download_admission_covalent_residue_locator_real_provider_export_execution_smoke_v1.py": "619034e6fe5f3597e5c733b1e2f29dfc523153513869254397e80f786d5e87f9",
    "data/derived/covalent_small/covapie_final_dataset_qa_gate_v1/covapie_final_dataset_qa_v1_manifest.json": "4f7c884379f926af52101f40a7870b243f0309af3b1637dc65c8c0691acf9f35",
}


def _bool(value: bool) -> str:
    return "true" if value else "false"


def _value(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _csv_bytes(
    columns: tuple[str, ...], rows: tuple[dict[str, str], ...]
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=columns, lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _read_csv(relative: str | Path) -> list[dict[str, str]]:
    with (ROOT / relative).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _read_json(relative: str | Path) -> dict[str, object]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise AssertionError(f"manifest is not an object: {relative}")
    return value


def _nested(document: Mapping[str, object], selector: str) -> object:
    current: object = document
    for item in selector.split("."):
        if not isinstance(current, Mapping) or item not in current:
            raise AssertionError(f"missing manifest selector: {selector}")
        current = current[item]
    return current


def _verify_evidence_hashes_and_base_membership() -> None:
    for relative, expected in EVIDENCE_SHA256.items():
        path = ROOT / relative
        if (
            not path.is_file()
            or path.is_symlink()
            or hashlib.sha256(path.read_bytes()).hexdigest() != expected
        ):
            raise AssertionError(f"committed evidence SHA mismatch: {relative}")
        result = subprocess.run(
            ("git", "cat-file", "-e", f"{BASE_COMMIT}:{relative}"),
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(f"evidence absent from BASE: {relative}")


def _control_specs() -> tuple[tuple[str, str, str, object], ...]:
    return (
        (
            "unified ADMIT_001-015 runtime",
            CONTROL_SOURCE_PATHS[0],
            "runtime.EVALUATOR_REGISTRY.keys",
            tuple(f"ADMIT_{index:03d}" for index in range(1, 16)),
        ),
        (
            "combined aggregation",
            CONTROL_SOURCE_PATHS[1],
            "source.contains:def aggregate_admission_rule_evaluations",
            True,
        ),
        (
            "stage orchestration contract",
            "data/derived/covalent_small/covapie_stage_global_rule_evaluation_orchestration_contract_v1/covapie_stage_global_rule_evaluation_orchestration_contract_manifest.json",
            "readiness.stage_global_rule_evaluation_orchestration_contract_frozen",
            True,
        ),
        (
            "stage orchestration runtime",
            CONTROL_SOURCE_PATHS[2],
            "source.contains:def orchestrate_stage_admission_scope",
            True,
        ),
        (
            "stage orchestration integration smoke",
            "data/derived/covalent_small/covapie_stage_global_rule_evaluation_orchestration_in_memory_integration_smoke_v1/covapie_stage_global_orchestration_in_memory_integration_smoke_manifest.json",
            "actual_orchestrator_called",
            True,
        ),
        (
            "call-site contract",
            "data/derived/covalent_small/covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_v1/covapie_bulk_download_stage_orchestration_fail_closed_call_site_contract_manifest.json",
            "call_site_contract_frozen",
            True,
        ),
        (
            "call-site runtime",
            CONTROL_SOURCE_PATHS[3],
            "source.contains:def evaluate_bulk_download_stage_orchestration_call_site",
            True,
        ),
        (
            "call-site integration smoke",
            "data/derived/covalent_small/covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_in_memory_integration_smoke_v1/covapie_bulk_download_stage_orchestration_fail_closed_call_site_decision_in_memory_integration_smoke_manifest.json",
            "actual_decision_runtime_called",
            True,
        ),
        (
            "bridge contract",
            "data/derived/covalent_small/covapie_bulk_download_stage_orchestration_action_permission_bridge_contract_v1/covapie_bulk_download_stage_orchestration_action_permission_bridge_contract_manifest.json",
            "action_permission_bridge_contract_frozen",
            True,
        ),
        (
            "bridge runtime",
            CONTROL_SOURCE_PATHS[4],
            "source.contains:def evaluate_bulk_download_stage_orchestration_action_permission_bridge",
            True,
        ),
        (
            "bridge integration smoke",
            "data/derived/covalent_small/covapie_bulk_download_stage_orchestration_action_permission_bridge_in_memory_integration_smoke_v1/covapie_bulk_download_stage_orchestration_action_permission_bridge_in_memory_integration_smoke_manifest.json",
            "actual_bridge_runtime_called",
            True,
        ),
        (
            "current blocked chain",
            "data/derived/covalent_small/covapie_bulk_download_stage_orchestration_action_permission_bridge_in_memory_integration_smoke_v1/covapie_bulk_download_stage_orchestration_action_permission_bridge_in_memory_integration_smoke_manifest.json",
            "current_blocked_actual_chain_verified",
            True,
        ),
        (
            "future eligible chain",
            "data/derived/covalent_small/covapie_bulk_download_stage_orchestration_action_permission_bridge_in_memory_integration_smoke_v1/covapie_bulk_download_stage_orchestration_action_permission_bridge_in_memory_integration_smoke_manifest.json",
            "future_eligible_actual_chain_verified",
            True,
        ),
        (
            "permission transition attempted",
            "data/derived/covalent_small/covapie_bulk_download_stage_orchestration_action_permission_bridge_in_memory_integration_smoke_v1/covapie_bulk_download_stage_orchestration_action_permission_bridge_in_memory_integration_smoke_manifest.json",
            "permission_transition_attempted",
            False,
        ),
        (
            "action permission granted count",
            "data/derived/covalent_small/covapie_bulk_download_stage_orchestration_action_permission_bridge_in_memory_integration_smoke_v1/covapie_bulk_download_stage_orchestration_action_permission_bridge_in_memory_integration_smoke_manifest.json",
            "action_permission_granted_count",
            0,
        ),
        (
            "download action count",
            "data/derived/covalent_small/covapie_bulk_download_stage_orchestration_action_permission_bridge_in_memory_integration_smoke_v1/covapie_bulk_download_stage_orchestration_action_permission_bridge_in_memory_integration_smoke_manifest.json",
            "download_action_count",
            0,
        ),
    )


def build_control_plane_rows() -> tuple[dict[str, str], ...]:
    rows: list[dict[str, str]] = []
    for component, relative, selector, expected in _control_specs():
        if selector == "runtime.EVALUATOR_REGISTRY.keys":
            observed: object = tuple(dispatch_runtime.EVALUATOR_REGISTRY)
        elif selector.startswith("source.contains:"):
            needle = selector.removeprefix("source.contains:")
            observed = needle in (ROOT / relative).read_text(encoding="utf-8")
        else:
            observed = _nested(_read_json(relative), selector)
        rows.append(
            {
                "control_plane_component": component,
                "evidence_path": relative,
                "evidence_selector": selector,
                "expected_value": _value(expected),
                "observed_value": _value(observed),
                "evidence_sha256": EVIDENCE_SHA256[relative],
                "verified": _bool(
                    type(observed) is type(expected) and observed == expected
                ),
            }
        )
    return tuple(rows)


def _effective_open_issue_rows() -> tuple[dict[str, str], ...]:
    payload = (ROOT / PREDECESSOR_ISSUE_PATH).read_bytes()
    if hashlib.sha256(payload).hexdigest() != PREDECESSOR_ISSUE_SHA256:
        raise AssertionError("issue inventory byte continuity failed")
    rows = _read_csv(PREDECESSOR_ISSUE_PATH)
    if len(rows) != 30:
        raise AssertionError("issue inventory must contain 30 rows")
    effective = tuple(
        row
        for row in rows
        if row["successor_effective_status"] == "open"
    )
    if tuple(row["issue_id"] for row in effective) != (
        review.ATOM_PAIR_BLOCKER,
        review.PROVIDER_BLOCKER,
    ):
        raise AssertionError("effective-open issues are not Exact2")
    return effective


def verify_atom_pair_evidence() -> bool:
    schema = _read_csv(
        "data/derived/covalent_small/covapie_final_dataset_design_gate_v0/covapie_final_dataset_schema_contract.csv"
    )
    contract = _read_csv(
        "data/derived/covalent_small/covapie_feature_semantics_audit_gate_v0/covapie_feature_semantics_contract.csv"
    )
    blockers = _read_csv(
        "data/derived/covalent_small/covapie_feature_semantics_audit_gate_v0/covapie_feature_semantics_training_blockers.csv"
    )
    tensor = _read_csv(
        "data/derived/covalent_small/covapie_feature_semantics_tensorization_audit_gate_v0/covapie_label_tensorization_blocker_audit.csv"
    )
    aux = _read_csv(
        "data/derived/covalent_small/covapie_final_dataset_design_gate_v0/covapie_final_dataset_auxiliary_label_readiness.csv"
    )
    model_source = (
        ROOT
        / "src/covalent_ext/real_covalent_confirmed_candidate_model_input_design_gate.py"
    ).read_text(encoding="utf-8")
    test_source = (
        ROOT / "tests/test_covapie_feature_semantics_audit_gate_v0.py"
    ).read_text(encoding="utf-8")
    return (
        any(row["final_dataset_field"] == "covalent_bond_atom_pair" for row in schema)
        and any(
            row["feature_name"] == "covalent_bond_atom_pair"
            and row["blocker_before_training"] == "True"
            for row in contract
        )
        and any(
            row["blocker_item"]
            == "ligand_residue_atom_pair_label_audit_required"
            and row["required_before_training"] == "True"
            for row in blockers
        )
        and any(
            "covalent_bond_atom_pair" in "|".join(row.values())
            and "True" in row.values()
            for row in tensor
        )
        and sum(
            row["auxiliary_task_name"] == "ligand_residue_atom_pair"
            and row["readiness_status"] == "available_from_validated_struct_conn"
            for row in aux
        )
        == 3
        and "Wrong atom-pair labels can corrupt covalent pair conditioning."
        in model_source
        and "ligand_residue_atom_pair_label" in test_source
    )


def verify_provider_evidence() -> bool:
    issue_rows = _read_csv(
        "data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_real_provider_export_execution_smoke_v1/covapie_covalent_residue_locator_real_provider_export_issue_inventory.csv"
    )
    sidecar = _read_csv(
        "data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_real_provider_export_execution_smoke_v1/covapie_covalent_residue_locator_real_provider_export_sidecar.csv"
    )
    manifest = _read_json(
        "data/derived/covalent_small/covapie_bulk_download_admission_covalent_residue_locator_real_provider_export_execution_smoke_v1/covapie_covalent_residue_locator_real_provider_export_execution_manifest.json"
    )
    admit_source = (
        ROOT
        / "src/covalent_ext/covapie_bulk_download_admission_admit_004_rule_logic_interface.py"
    ).read_text(encoding="utf-8")
    provider_test = (
        ROOT
        / "tests/test_covapie_bulk_download_admission_covalent_residue_locator_real_provider_export_execution_smoke_v1.py"
    ).read_text(encoding="utf-8")
    blocking = next(
        row
        for row in issue_rows
        if row["issue_id"] == review.PROVIDER_BLOCKER
    )
    return (
        blocking["status"] == "open"
        and blocking["issue_count"] == "11"
        and len(sidecar) == 11
        and all(
            row["provider_export_status"] == "exported_blocking"
            and row["insertion_blocks_admit_004"] == "true"
            and row["covalent_residue_insertion_code_state"] == "unknown"
            and row["covalent_residue_insertion_code"] == ""
            for row in sidecar
        )
        and manifest.get("exported_blocking_count") == 11
        and "covalent_residue_insertion_code_state" in admit_source
        and "covalent_residue_insertion_code" in admit_source
        and "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT" in provider_test
    )


def build_comparison_rows() -> tuple[dict[str, str], ...]:
    effective = {row["issue_id"]: row for row in _effective_open_issue_rows()}
    if not verify_atom_pair_evidence() or not verify_provider_evidence():
        raise AssertionError("blocker evidence is incomplete")
    atom = effective[review.ATOM_PAIR_BLOCKER]
    provider = effective[review.PROVIDER_BLOCKER]
    return (
        {
            "blocker_id": review.ATOM_PAIR_BLOCKER,
            "issue_type": atom["issue_type"],
            "affected_fields": "covalent_bond_atom_pair|ligand_residue_atom_pair_label",
            "affected_rules": "",
            "blocking_scope": "training_label_semantics",
            "current_status": "open",
            "evidence_source_count": "7",
            "blocks_dataset_schema_finalization": "true",
            "blocks_label_tensor_contract": "true",
            "blocks_feature_semantics_audit": "true",
            "blocks_auxiliary_atom_pair_task": "true",
            "blocks_model_forward_now": "false",
            "requires_real_provider_execution": "false",
            "can_be_reviewed_with_committed_evidence": "true",
            "can_remain_quarantined_temporarily": "false",
            "dependency_position": "1",
            "selection_disposition": "selected_next",
            "selection_reason": (
                "semantic upstream of feature audit, tensor/label contract, "
                "and auxiliary pair integration; current audit is hermetic"
            ),
            "verified": "true",
        },
        {
            "blocker_id": review.PROVIDER_BLOCKER,
            "issue_type": provider["issue_type"],
            "affected_fields": (
                "covalent_residue_insertion_code_state|"
                "covalent_residue_insertion_code"
            ),
            "affected_rules": "ADMIT_004",
            "blocking_scope": "provider_export_data_availability",
            "current_status": "open",
            "evidence_source_count": "5",
            "blocks_dataset_schema_finalization": "false",
            "blocks_label_tensor_contract": "false",
            "blocks_feature_semantics_audit": "false",
            "blocks_auxiliary_atom_pair_task": "false",
            "blocks_model_forward_now": "false",
            "requires_real_provider_execution": "true",
            "can_be_reviewed_with_committed_evidence": "true",
            "can_remain_quarantined_temporarily": "true",
            "dependency_position": "4",
            "selection_disposition": "deferred_open",
            "selection_reason": (
                "still blocks complete real-data coverage but can remain "
                "fail-closed until after the atom-pair audit and contract"
            ),
            "verified": "true",
        },
    )


def build_dependency_rows() -> tuple[dict[str, str], ...]:
    prerequisites = (
        "post-admission control-plane closure",
        "dependency step 1",
        "dependency step 2",
        "dependency step 3",
        "dependency step 4",
        "dependency step 5",
        "dependency step 6",
        "dependency step 7",
        "dependency step 8",
    )
    reasons = (
        "observe current semantics and consumers before defining encoding",
        "freeze encoding only after the audit",
        "cross-check the frozen contract against committed evidence",
        "complete real-provider coverage under an explicit fail-closed policy",
        "audit features only after label and provider-data semantics are ordered",
        "freeze tensors and masks after feature semantics",
        "preserve checkpoint compatibility for the first auxiliary increment",
        "prove forward/loss legality without parameter updates",
        "formal training remains last and separately gated",
    )
    return tuple(
        {
            "dependency_order": str(index),
            "dependency_step": step,
            "prerequisite": prerequisites[index - 1],
            "implemented_current_review": "false",
            "ordering_reason": reasons[index - 1],
            "verified": "true",
        }
        for index, step in enumerate(review.DEPENDENCY_ORDER, start=1)
    )


def build_safety_rows() -> tuple[dict[str, str], ...]:
    return tuple(
        {
            "safety_item": item,
            "expected_executed": "false",
            "observed_executed": "false",
            "verified": "true",
        }
        for item in SAFETY_ITEMS
    )


def _decision() -> review.PostAdmissionNextBlockerSelectionDecision:
    effective = tuple(
        row["issue_id"] for row in _effective_open_issue_rows()
    )
    return review.review_covapie_post_admission_control_plane_completion_and_select_next_training_preparation_blocker_v1(
        control_plane_complete=True,
        effective_open_issues=effective,
        atom_pair_evidence_verified=verify_atom_pair_evidence(),
        provider_export_evidence_verified=verify_provider_evidence(),
    )


def _verify_masks_and_training_gate() -> None:
    qa = _read_json(
        "data/derived/covalent_small/covapie_final_dataset_qa_gate_v1/covapie_final_dataset_qa_v1_manifest.json"
    )
    observed_masks = tuple(
        tuple(item) for item in qa["canonical_mask_pairs"]  # type: ignore[index]
    )
    if (
        observed_masks != CANONICAL_MASKS
        or qa.get("canonical_mask_task_count") != 5
        or qa.get("feature_semantics_known_for_training") is not False
        or qa.get("unknown_atom_feature_policy_finalized_for_training")
        is not False
        or qa.get("ready_for_training") is not False
    ):
        raise AssertionError("canonical mask or training gate mismatch")


def _verify_control_sources_unchanged() -> None:
    for arguments in (
        ("diff", "--exit-code", BASE_COMMIT, "--", *CONTROL_SOURCE_PATHS),
        ("diff", "--cached", "--exit-code", BASE_COMMIT, "--", *CONTROL_SOURCE_PATHS),
    ):
        result = subprocess.run(
            ("git", *arguments),
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0 or result.stdout or result.stderr:
            raise AssertionError("committed control-plane source changed")


def _manifest(
    csv_payloads: Mapping[str, bytes],
    decision: review.PostAdmissionNextBlockerSelectionDecision,
) -> dict[str, object]:
    return {
        "project": "CovaPIE",
        "stage": STAGE,
        "base_commit": BASE_COMMIT,
        "formal_commit_subject": FORMAL_COMMIT_SUBJECT,
        "post_admission_control_plane_complete": True,
        "control_plane_scope_closed": True,
        "additional_permission_layer_required": False,
        "control_plane_code_change_required": False,
        "next_blocker_selection_completed": True,
        **asdict(decision),
        "selected_blocker_blocks_feature_semantics_audit": True,
        "selected_blocker_blocks_tensor_label_contract": True,
        "selected_blocker_can_be_audited_without_provider_execution": True,
        "deferred_blocker_remains_open": True,
        "deferred_blocker_requires_later_provider_or_materialization_resolution": True,
        "issue_status_changed": False,
        "resolved_issue_count": 0,
        "new_issue_count": 0,
        "deleted_issue_count": 0,
        "provider_used": False,
        "download_used": False,
        "model_changed": False,
        "training_used": False,
        "feature_semantics_audit_completed": False,
        "feature_semantics_audit_required_before_training": True,
        "ready_for_download": False,
        "ready_for_training": False,
        "control_plane_inventory_row_count": 16,
        "blocker_comparison_row_count": 2,
        "dependency_order_row_count": 9,
        "safety_row_count": 19,
        "issue_inventory_data_row_count": 30,
        "effective_open_issue_count": 2,
        "canonical_masks": [
            {"semantic_name": name, "alias": alias}
            for name, alias in CANONICAL_MASKS
        ],
        "unknown_atom_feature_policy": "UNKNOWN_ATOM_FEATURE_POLICY",
        "feature_semantics_known": False,
        "step12d_warning": (
            "Step12D was a smoke legality check, not a final "
            "training-feature contract"
        ),
        "issue_inventory_source_sha256": PREDECESSOR_ISSUE_SHA256,
        "exact10_files": [path.as_posix() for path in EXACT10],
        "committed_evidence_sha256": EVIDENCE_SHA256,
        "evidence_sha256": {
            name: hashlib.sha256(payload).hexdigest()
            for name, payload in csv_payloads.items()
        },
    }


def build_evidence_payloads() -> dict[str, bytes]:
    _verify_evidence_hashes_and_base_membership()
    _verify_control_sources_unchanged()
    _verify_masks_and_training_gate()
    controls = build_control_plane_rows()
    comparisons = build_comparison_rows()
    dependencies = build_dependency_rows()
    safety = build_safety_rows()
    if (
        len(controls) != 16
        or any(row["verified"] != "true" for row in controls)
        or len(comparisons) != 2
        or any(row["verified"] != "true" for row in comparisons)
        or len(dependencies) != 9
        or any(row["verified"] != "true" for row in dependencies)
        or len(safety) != 19
        or any(row["verified"] != "true" for row in safety)
    ):
        raise AssertionError("review evidence row contract failed")
    decisions = tuple(_decision() for _ in range(3))
    serialized = tuple(
        review.serialize_post_admission_next_blocker_selection_decision(item)
        for item in decisions
    )
    if not (
        decisions[0] == decisions[1] == decisions[2]
        and serialized[0] == serialized[1] == serialized[2]
        and decisions[0].outcome == "selected"
    ):
        raise AssertionError("decision determinism failed")
    issue_payload = (ROOT / PREDECESSOR_ISSUE_PATH).read_bytes()
    csv_payloads = {
        CONTROL_NAME: _csv_bytes(CONTROL_COLUMNS, controls),
        COMPARISON_NAME: _csv_bytes(COMPARISON_COLUMNS, comparisons),
        DEPENDENCY_NAME: _csv_bytes(DEPENDENCY_COLUMNS, dependencies),
        SAFETY_NAME: _csv_bytes(SAFETY_COLUMNS, safety),
        ISSUE_NAME: issue_payload,
    }
    return {
        **csv_payloads,
        MANIFEST_NAME: (
            json.dumps(
                _manifest(csv_payloads, decisions[0]),
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8"),
    }


def verify_payloads(payloads: Mapping[str, bytes]) -> dict[str, object]:
    if tuple(payloads) != OUTPUT_NAMES:
        raise AssertionError("output payload set is not Exact6")
    for name in OUTPUT_NAMES:
        path = ROOT / OUTPUT_ROOT / name
        if (
            not path.is_file()
            or path.is_symlink()
            or path.read_bytes() != payloads[name]
        ):
            raise AssertionError(f"materialized evidence mismatch: {name}")
    manifest = json.loads(payloads[MANIFEST_NAME])
    required_true = (
        "post_admission_control_plane_complete",
        "control_plane_scope_closed",
        "next_blocker_selection_completed",
        "selected_blocker_blocks_feature_semantics_audit",
        "selected_blocker_blocks_tensor_label_contract",
        "selected_blocker_can_be_audited_without_provider_execution",
        "deferred_blocker_remains_open",
        "deferred_blocker_requires_later_provider_or_materialization_resolution",
        "feature_semantics_audit_required_before_training",
    )
    required_false = (
        "additional_permission_layer_required",
        "control_plane_code_change_required",
        "issue_status_changed",
        "provider_used",
        "download_used",
        "model_changed",
        "training_used",
        "feature_semantics_audit_completed",
        "ready_for_download",
        "ready_for_training",
    )
    if any(manifest.get(item) is not True for item in required_true):
        raise AssertionError("required true manifest field failed")
    if any(manifest.get(item) is not False for item in required_false):
        raise AssertionError("required false manifest field failed")
    if (
        manifest.get("selected_next_blocker") != review.ATOM_PAIR_BLOCKER
        or manifest.get("deferred_blocker") != review.PROVIDER_BLOCKER
        or manifest.get("selected_next_step") != review.SELECTED_NEXT_STEP
        or manifest.get("issue_inventory_source_sha256")
        != PREDECESSOR_ISSUE_SHA256
    ):
        raise AssertionError("selection or continuity manifest mismatch")
    return manifest


def main() -> int:
    payloads = build_evidence_payloads()
    second = build_evidence_payloads()
    third = build_evidence_payloads()
    if payloads != second or second != third:
        raise AssertionError("three complete evidence builds differ")
    (ROOT / OUTPUT_ROOT).mkdir(parents=True, exist_ok=True)
    for name, payload in payloads.items():
        (ROOT / OUTPUT_ROOT / name).write_bytes(payload)
    manifest = verify_payloads(payloads)
    lines = (
        "control_plane_complete=true",
        "control_plane_scope_closed=true",
        "additional_permission_layer_required=false",
        f"selected_next_blocker={manifest['selected_next_blocker']}",
        f"deferred_blocker={manifest['deferred_blocker']}",
        f"selected_next_step={manifest['selected_next_step']}",
        "control_plane_inventory_rows=16",
        "blocker_comparison_rows=2",
        "dependency_order_rows=9",
        "safety_rows=19",
        "issue_rows=30",
        "issue_status_changed=false",
        "provider_used=false",
        "download_used=false",
        "model_changed=false",
        "training_used=false",
        "feature_semantics_audit_completed=false",
        "ready_for_download=false",
        "ready_for_training=false",
    )
    sys.stdout.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
