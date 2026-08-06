#!/usr/bin/env python3
"""Check the Current11 tensor-projection payload builder V1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import NoReturn, Sequence


_ROOT = Path(__file__).resolve().parents[1]
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from covalent_ext import (  # noqa: E402
    covapie_current11_tensor_projection_payload_builder_v1 as _builder,
)


class _FailClosedParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        del message
        raise ValueError(_builder._ERROR)


def _parser() -> argparse.ArgumentParser:
    parser = _FailClosedParser(add_help=False, allow_abbrev=False)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        arguments = _parser().parse_args(argv)
        artifacts = (
            _builder.build_covapie_current11_tensor_projection_payload_bundle_v1(
                repo_root=arguments.repo_root,
                state_root=arguments.state_root,
            )
        )
        if (
            type(artifacts) is not dict
            or tuple(artifacts) != _builder._ARTIFACT_NAMES
            or len(artifacts) != 8
        ):
            raise ValueError(_builder._ERROR)
        report = json.loads(artifacts[_builder._ARTIFACT_NAMES[7]])
        readiness = report.get("readiness")
        if (
            type(report) is not dict
            or report.get("builder_status")
            != "PASS_IN_MEMORY_PAYLOAD_BUNDLE_ONLY"
            or report.get("artifact_file_count") != 8
            or report.get("payload_cell_count") != 55
            or report.get("valid_payload_cell_count") != 55
            or report.get("candidate_payload_cell_count") != 0
            or report.get("loss_authorized_cell_count") != 0
            or report.get("runtime_consumer_available_cell_count") != 0
            or report.get("audited_exact5_task_payload_bundle_built_in_memory")
            is not True
            or report.get("full_exact25_projection_instance_materialized")
            is not False
            or report.get("formal_payload_bundle_materialized") is not False
            or report.get("tensor_materialized") is not False
            or report.get("data_availability_matrix_materialized") is not False
            or report.get("candidate_payloads_materialized") is not False
            or type(readiness) is not dict
            or readiness.get("feature_semantics_reaudit_required_before_training")
            is not True
            or readiness.get("ready_for_training") is not False
        ):
            raise ValueError(_builder._ERROR)
        encoded = json.dumps(
            report,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        )
    except Exception:
        print(_builder._ERROR, file=sys.stderr)
        return 1
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
