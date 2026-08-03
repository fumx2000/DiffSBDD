#!/usr/bin/env python3
"""Check the terminalized result of the bounded conditioned runtime smoke."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_bounded_repository_cli_conditioned_runtime_smoke_v1 as implementation,
)


_CHECK_ERROR = "COVAPIE_BOUNDED_REPOSITORY_CLI_CONDITIONED_RUNTIME_SMOKE_CHECK_INVALID"


def _emit(name: str, value: object) -> None:
    if isinstance(value, bool):
        rendered = str(value).lower()
    elif isinstance(value, (dict, list)):
        rendered = json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        )
    else:
        rendered = str(value)
    print(f"{name}={rendered}")


def _assert_static_contract(response: Mapping[str, object]) -> None:
    if (
        type(response) is not dict
        or tuple(response) != implementation._IMPLEMENTATION_RESPONSE_FIELDS
        or len(response) != len(implementation._IMPLEMENTATION_RESPONSE_FIELDS)
        or not implementation._validate_implementation_response(response)
        or json.loads(implementation._canonical_json_bytes(response)) != response
        or response["bounded_runtime_smoke_implementation_complete"] is not True
        or response["default_checker_real_runtime_smoke_executed"] is not False
        or not implementation._validate_terminal_lifecycle_evidence(
            response["git_precondition"]
        )
        or response["published_design_response_binding"][
            "published_snapshot_response_sha256"
        ]
        != implementation._DESIGN_RESPONSE_SHA256
        or response["one_time_execution_authorization_consumed"] is not True
        or response["one_time_execution_record"][
            "bounded_runtime_smoke_execution_count"
        ]
        != 1
        or response["one_time_execution_record"]["bounded_runtime_smoke_passed"]
        is not False
        or response["exact67_runtime_evidence_available"] is not False
        or response["ready_for_one_time_bounded_runtime_smoke_execution"] is not False
        or response["reexecution_requires_new_explicit_user_authorization"]
        is not True
        or response["failure_establishes_model_runtime_failure"] is not False
        or response["failure_establishes_conditioned_plumbing_failure"] is not False
        or response["recommended_next_step"]
        != "audit_covapie_five_module_training_path_completion_gaps_v1"
        or response["training_or_parameter_update"] is not False
        or response["RL_implementation_started"] is not False
    ):
        raise ValueError(_CHECK_ERROR)


def _parse_arguments(arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--execute-once",
        action="store_true",
        help="report that the one-time execution authorization is consumed",
    )
    return parser.parse_args(arguments)


def main(arguments: list[str] | None = None) -> int:
    parsed = _parse_arguments(sys.argv[1:] if arguments is None else arguments)
    if parsed.execute_once:
        implementation._guard_one_time_execution_authorization_v1()
    first = implementation.evaluate_covapie_bounded_repository_cli_conditioned_runtime_smoke_implementation_v1(
        repo_root=ROOT
    )
    second = implementation.evaluate_covapie_bounded_repository_cli_conditioned_runtime_smoke_implementation_v1(
        repo_root=ROOT
    )
    if first != second or implementation._canonical_json_bytes(
        first
    ) != implementation._canonical_json_bytes(second):
        raise ValueError(_CHECK_ERROR)
    _assert_static_contract(first)

    _emit(
        "bounded_runtime_smoke_implementation_complete",
        first["bounded_runtime_smoke_implementation_complete"],
    )
    _emit("implementation_response_field_count", len(first))
    _emit(
        "implementation_response_sha256",
        first["bounded_runtime_smoke_implementation_response_sha256"],
    )
    _emit(
        "design_published_snapshot_response_sha256",
        first["published_design_response_binding"][
            "published_snapshot_response_sha256"
        ],
    )
    _emit(
        "design_current_response_sha256",
        first["published_design_response_binding"]["current_response_sha256"],
    )
    _emit(
        "fresh_runtime_source_revalidated",
        first["fresh_runtime_source_revalidation"][
            "all_live_bytes_match_snapshot"
        ],
    )
    _emit(
        "runtime_evidence_required_field_count",
        first["runtime_evidence_schema"]["required_field_count"],
    )
    _emit(
        "default_checker_real_runtime_smoke_executed",
        first["default_checker_real_runtime_smoke_executed"],
    )
    _emit("training_or_parameter_update", first["training_or_parameter_update"])
    _emit("RL_implementation_started", first["RL_implementation_started"])
    _emit("one_time_execution_only", first["one_time_execution_only"])
    _emit(
        "repeat_without_new_user_authorization",
        first["repeat_without_new_user_authorization"],
    )
    _emit(
        "ready_for_one_time_bounded_runtime_smoke_execution",
        first["ready_for_one_time_bounded_runtime_smoke_execution"],
    )
    lifecycle = first["git_precondition"]
    _emit("terminal_lifecycle_profile", lifecycle["profile"])
    _emit("terminal_commit", lifecycle["terminal_commit"])
    _emit("terminal_committed", lifecycle["terminal_committed"])
    _emit("terminal_published", lifecycle["terminal_published"])
    _emit(
        "ready_for_terminalized_implementation_commit_review",
        lifecycle["ready_for_terminalized_implementation_commit_review"],
    )
    _emit("current_HEAD", lifecycle["current_HEAD"])
    _emit("current_origin_main", lifecycle["current_origin_main"])
    _emit(
        "one_time_execution_authorization_consumed",
        first["one_time_execution_authorization_consumed"],
    )
    _emit(
        "bounded_runtime_smoke_execution_count",
        first["one_time_execution_record"]["bounded_runtime_smoke_execution_count"],
    )
    _emit(
        "bounded_runtime_smoke_passed",
        first["one_time_execution_record"]["bounded_runtime_smoke_passed"],
    )
    _emit(
        "exact67_runtime_evidence_available",
        first["exact67_runtime_evidence_available"],
    )
    _emit(
        "reexecution_requires_new_explicit_user_authorization",
        first["reexecution_requires_new_explicit_user_authorization"],
    )
    _emit(
        "failure_establishes_model_runtime_failure",
        first["failure_establishes_model_runtime_failure"],
    )
    _emit(
        "failure_establishes_conditioned_plumbing_failure",
        first["failure_establishes_conditioned_plumbing_failure"],
    )
    _emit("recommended_next_step", first["recommended_next_step"])
    _emit("checker_mode", "static_only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
