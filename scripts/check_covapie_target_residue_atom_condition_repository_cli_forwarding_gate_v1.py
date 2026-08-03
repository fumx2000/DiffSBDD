#!/usr/bin/env python3
"""Check any valid lifecycle profile of the formal C4 forwarding gate."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1
    as gate,
)


_CHECK_ERROR = (
    "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_REPOSITORY_CLI_FORWARDING_GATE_CHECK_INVALID"
)


def _emit(name: str, value: object) -> None:
    rendered = str(value).lower() if isinstance(value, bool) else str(value)
    print(f"{name}={rendered}")


def _validate_lifecycle_response(response: Mapping[str, object]) -> bool:
    profile = response.get("C4_gate_lifecycle_profile")
    commit = response.get("C4_gate_commit")
    claims = (
        response.get("C4_gate_committed"),
        response.get("C4_gate_published"),
        response.get("ready_for_C4_commit_review"),
        response.get("repository_cli_selector_forwarding_complete"),
        response.get("ready_for_repository_cli_runtime_smoke_planning"),
        response.get("recommended_next_step"),
    )
    contracts = {
        "c4_precommit_candidate": (
            None,
            (
                False,
                False,
                True,
                False,
                False,
                "commit_and_push_covapie_target_residue_atom_condition_repository_cli_forwarding_gate_C4_v1",
            ),
        ),
        "c4_committed_unpushed": (
            "commit",
            (
                True,
                False,
                False,
                True,
                False,
                "push_covapie_target_residue_repository_cli_forwarding_gate_C4_v1",
            ),
        ),
        "c4_published_successor": (
            "commit",
            (
                True,
                True,
                False,
                True,
                True,
                "design_bounded_covapie_repository_cli_conditioned_runtime_smoke_v1",
            ),
        ),
    }
    if (
        type(profile) is not str
        or profile not in contracts
        or any(type(value) is not bool for value in claims[:5])
        or type(claims[5]) is not str
    ):
        raise ValueError(_CHECK_ERROR)
    commit_contract, expected_claims = contracts[profile]
    commit_valid = (
        commit is None
        if commit_contract is None
        else type(commit) is str
        and re.fullmatch(r"[0-9a-f]{40}", commit) is not None
    )
    if not commit_valid or claims != expected_claims:
        raise ValueError(_CHECK_ERROR)
    return True


def main() -> int:
    first = gate.evaluate_covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1(
        repo_root=ROOT
    )
    second = gate.evaluate_covapie_target_residue_atom_condition_repository_cli_forwarding_gate_v1(
        repo_root=ROOT
    )
    if first != second:
        raise ValueError(_CHECK_ERROR)
    if (
        tuple(first) != gate.REPOSITORY_CLI_FORWARDING_GATE_RESPONSE_FIELDS
        or len(first) != len(gate.REPOSITORY_CLI_FORWARDING_GATE_RESPONSE_FIELDS)
        or not gate._validate_response(first)
        or not _validate_lifecycle_response(first)
        or json.loads(gate._canonical_json_bytes(first)) != first
    ):
        raise ValueError(_CHECK_ERROR)
    unsigned = {
        field: first[field]
        for field in gate.REPOSITORY_CLI_FORWARDING_GATE_RESPONSE_FIELDS
        if field != "repository_cli_forwarding_gate_response_sha256"
    }
    if first["repository_cli_forwarding_gate_response_sha256"] != hashlib.sha256(
        gate._canonical_json_bytes(unsigned)
    ).hexdigest():
        raise ValueError(_CHECK_ERROR)

    _emit("R3_gate_published", first["R3_gate_published"])
    _emit("R3_formal_retirement_bound", first["R3_formal_retirement_bound"])
    _emit("C1_central_helper_bound", first["C1_central_helper_bound"])
    _emit(
        "C2_generate_ligands_forwarding_bound",
        first["C2_generate_ligands_forwarding_bound"],
    )
    _emit(
        "C3_covalent_demo_forwarding_bound",
        first["C3_covalent_demo_forwarding_bound"],
    )
    _emit("supported_caller_count", first["supported_caller_count"])
    _emit("deferred_caller_count", first["deferred_caller_count"])
    _emit("canonical_mask_count", first["canonical_mask_count"])
    _emit("C4_gate_lifecycle_profile", first["C4_gate_lifecycle_profile"])
    _emit("C4_gate_committed", first["C4_gate_committed"])
    _emit("C4_gate_published", first["C4_gate_published"])
    _emit(
        "repository_cli_selector_forwarding_complete",
        first["repository_cli_selector_forwarding_complete"],
    )
    _emit(
        "ready_for_repository_cli_runtime_smoke_planning",
        first["ready_for_repository_cli_runtime_smoke_planning"],
    )
    _emit("training_or_parameter_update", first["training_or_parameter_update"])
    _emit("RL_implementation_started", first["RL_implementation_started"])
    _emit(
        "feature_semantics_audit_required_before_training",
        first["feature_semantics_audit_required_before_training"],
    )
    _emit(
        "Step12D_smoke_is_not_final_training_feature_contract",
        first["Step12D_smoke_is_not_final_training_feature_contract"],
    )
    _emit(
        "repository_cli_forwarding_gate_response_sha256",
        first["repository_cli_forwarding_gate_response_sha256"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
