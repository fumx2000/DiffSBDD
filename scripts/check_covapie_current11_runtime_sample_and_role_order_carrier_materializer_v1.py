#!/usr/bin/env python3
"""Check the Current11 runtime carrier materializer without writing state."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from covalent_ext import covapie_current11_runtime_sample_and_role_order_carrier_materializer_v1 as _materializer


_ERROR = "COVAPIE_CURRENT11_RUNTIME_SAMPLE_AND_ROLE_ORDER_CARRIER_MATERIALIZER_V1_CHECK_ERROR"


def _arguments(values: list[str]) -> tuple[Path, Path]:
    if len(values) != 4:
        raise ValueError(_ERROR)
    parsed: dict[str, Path] = {}
    for index in (0, 2):
        option = values[index]
        value = values[index + 1]
        if option not in {"--repo-root", "--state-root"} or option in parsed or not value:
            raise ValueError(_ERROR)
        parsed[option] = Path(value)
    if set(parsed) != {"--repo-root", "--state-root"}:
        raise ValueError(_ERROR)
    return parsed["--repo-root"], parsed["--state-root"]


def _implementation_readiness() -> dict[str, bool]:
    return {
        "runtime_sample_and_role_order_carrier_materializer_implemented": True,
        "runtime_sample_and_role_order_carrier_materializer_passed": True,
        "deterministic_runtime_carrier_npz_builder_implemented": True,
        "gpfs_atomic_alias_publication_implemented": True,
        "temporary_materialization_smoke_passed": True,
        "materializer_implemented": True,
        "formal_runtime_carrier_materialized": False,
        "runtime_batch_sample_key_available": False,
        "runtime_batch_sample_key_exact_one_for_current11": False,
        "runtime_batch_role_order_binding_available": False,
        "current11_atom_identity_provider_available": True,
        "general_non_source_identity_provider_available": False,
        "ready_for_formal_runtime_carrier_materialization_execution": True,
        "ready_for_batch_descriptor_compiler_contract_gate_implementation": False,
        "ready_for_task2_batch_descriptor_compiler_implementation": False,
        "ready_for_runtime_batch_observation_extractor_design": True,
        "ready_for_dataloader_integration": False,
        "ready_for_model_integration": False,
        "ready_for_loss_integration": False,
        "feature_semantics_reaudit_required_before_training": True,
        "ready_for_training": False,
    }


def _check(repo_root: Path, state_root: Path) -> dict[str, object]:
    first = _materializer._build_candidate_bundle(
        repo_root=repo_root, state_root=state_root
    )
    second = _materializer._build_candidate_bundle(
        repo_root=repo_root, state_root=state_root
    )
    if first != second:
        raise ValueError(_ERROR)
    validated = _materializer._validate_candidate_bundle(first)
    canonical = state_root / _materializer._CANONICAL_RELATIVE
    try:
        canonical.lstat()
    except FileNotFoundError:
        formal = False
        status = "PASS_MATERIALIZER_IMPLEMENTATION_ONLY"
        readiness = _implementation_readiness()
        verification = None
    else:
        formal = True
        status = "PASS_FORMAL_RUNTIME_CARRIER_MATERIALIZED"
        verification = _materializer._verify_existing(
            repo_root=repo_root, state_root=state_root
        )
        readiness = {
            **_implementation_readiness(),
            **_materializer._formal_readiness(),
            "ready_for_formal_runtime_carrier_materialization_execution": False,
        }
    if readiness["formal_runtime_carrier_materialized"] is not formal:
        raise ValueError(_ERROR)
    return {
        "status": status,
        "candidate_artifact_count": 4,
        "candidate_array_count": 12,
        "candidate_npz_bytes": len(first[_materializer._NPZ]),
        "candidate_npz_sha256": _materializer._sha(first[_materializer._NPZ]),
        "candidate_aggregate_sha256": _materializer._aggregate_sha256(first),
        "candidate_binding_report_status": validated["report"]["status"],
        "candidate_double_build_byte_identical": True,
        "real_state_read_only": True,
        "verification": verification,
        "readiness": readiness,
    }


def main() -> int:
    try:
        repo_root, state_root = _arguments(sys.argv[1:])
        result = _check(repo_root, state_root)
    except BaseException:
        sys.stdout.write("")
        sys.stderr.write(_ERROR + "\n")
        return 1
    sys.stdout.write(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
