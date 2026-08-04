#!/usr/bin/env python3
"""Deterministic checker for the canonical role/task-mask contract V1."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1
    as contract,
)


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def main() -> int:
    first = contract.evaluate_covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1(
        repo_root=ROOT,
    )
    second = contract.evaluate_covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1(
        repo_root=ROOT,
    )
    contract._validate_response_v1(first)
    contract._validate_response_v1(second)
    first_bytes = _canonical_bytes(first)
    second_bytes = _canonical_bytes(second)
    safe = (
        first_bytes == second_bytes
        and first["canonical_role_count"] == 3
        and first["canonical_task_count"] == 5
        and first["canonical_task_truth_table"][3]["semantic_name"] == "scaffold_only"
        and first["role_task_mask_contract_resolved"] is True
        and first["primary_role_authority_complete"] is False
        and first["minimal_seed_anchor_authority_complete"] is False
        and first["canonical_mask_tensors_materialized"] is False
        and first["ready_for_tensor_materialization_smoke"] is False
        and first["ready_for_model_integration"] is False
        and first["ready_for_training"] is False
        and first["checkpoint_atom_feature_width"] == 10
        and first["checkpoint_feature_concatenation_allowed"] is False
        and first["final_training_feature_semantics_revalidation_required"] is True
        and len(first["evidence_records"]) == 20
        and first["failure_matrix_case_count"] == 34
        and first["contract_lifecycle_profile"] in {
            "contract_precommit_candidate",
            "contract_committed_unpushed",
            "contract_published_successor",
        }
        and first["candidate_scope_verified"] is True
        and first["recommended_next_increment"]
        == "resolve_covapie_role_annotation_input_authority_gaps_v1"
        and first["commit_created"] is False
        and first["push_performed"] is False
    )
    if not safe:
        raise ValueError(contract._ERROR)

    print(f"base_head={first['base_head']}")
    print(f"base_head_subject={first['base_head_subject']}")
    print(f"origin_main={first['origin_main']}")
    print(f"ahead_behind={first['ahead']}/{first['behind']}")
    print(f"contract_lifecycle_profile={first['contract_lifecycle_profile']}")
    print(f"contract_commit={first['contract_commit']}")
    print(f"contract_committed={str(first['contract_committed']).lower()}")
    print(f"contract_published={str(first['contract_published']).lower()}")
    print(f"ready_for_contract_commit_review={str(first['ready_for_contract_commit_review']).lower()}")
    print(f"evidence_record_count={len(first['evidence_records'])}")
    print(f"canonical_role_count={first['canonical_role_count']}")
    print(f"canonical_task_count={first['canonical_task_count']}")
    print(f"field_contract_count={first['field_contract_count']}")
    print(f"failure_matrix_case_count={first['failure_matrix_case_count']}")
    print(f"warhead_atom_set_authority_coverage={first['warhead_atom_set_authority_coverage']}")
    print(f"ligand_internal_warhead_boundary_authority_coverage={first['ligand_internal_warhead_boundary_authority_coverage']}")
    print(f"role_assignment_authority_coverage={first['role_assignment_authority_coverage']}")
    print(f"minimal_seed_anchor_authority_coverage={first['minimal_seed_anchor_authority_coverage']}")
    for field in (
        "role_task_mask_contract_resolved",
        "primary_role_authority_complete",
        "minimal_seed_anchor_authority_complete",
        "base_task_masks_derivable",
        "synthetic_base_task_masks_derivable",
        "real_role_task_mask_materialization_ready",
        "canonical_mask_tensors_materialized",
        "ready_for_tensor_materialization_smoke",
        "ready_for_model_integration",
        "ready_for_training",
        "candidate_scope_verified",
        "commit_created",
        "push_performed",
    ):
        print(f"{field}={str(first[field]).lower()}")
    print(f"recommended_next_increment={first['recommended_next_increment']}")
    print(f"response_exact_field_count={len(first)}")
    print(f"response_sha256={first['response_sha256']}")
    print(f"response_canonical_bytes={len(first_bytes)}")
    print(f"response_canonical_sha256={hashlib.sha256(first_bytes).hexdigest()}")
    print(f"response_double_evaluation_byte_identical={str(first_bytes == second_bytes).lower()}")
    print(f"safety_boundary_verified={str(safe).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
