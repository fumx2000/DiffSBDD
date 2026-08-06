#!/usr/bin/env python3
"""Check the Current11 Task 2 batch-index remap contract gate in memory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import NoReturn, Sequence

from covalent_ext.covapie_current11_task2_batch_index_remap_contract_gate_v1 import (
    build_covapie_current11_task2_batch_index_remap_contract_gate_v1,
)


_ERROR = "COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_CONTRACT_GATE_V1_ERROR"
_REPORT = "current11_task2_batch_index_remap_contract_gate_report.json"


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        del message
        raise ValueError(_ERROR)


def _main(arguments: Sequence[str]) -> int:
    parser = _Parser(add_help=False, allow_abbrev=False)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--state-root", required=True, type=Path)
    namespace = parser.parse_args(arguments)
    artifacts = build_covapie_current11_task2_batch_index_remap_contract_gate_v1(
        repo_root=namespace.repo_root,
        state_root=namespace.state_root,
    )
    report = json.loads(artifacts[_REPORT].decode("utf-8"))
    readiness = report.get("readiness")
    if (
        report.get("gate_status") != "PASS_CONTRACT_ONLY"
        or type(readiness) is not dict
        or readiness.get("task2_batch_index_remap_contract_gate_passed") is not True
        or readiness.get("ready_for_training") is not False
    ):
        raise ValueError(_ERROR)
    sys.stdout.write(
        json.dumps(
            report,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_main(sys.argv[1:]))
    except BaseException as error:
        if type(error) is SystemExit and type(error.code) is int and error.code == 0:
            raise
        sys.stderr.write(_ERROR + "\n")
        raise SystemExit(1) from None
