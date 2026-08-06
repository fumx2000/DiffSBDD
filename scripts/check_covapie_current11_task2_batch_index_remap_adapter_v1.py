#!/usr/bin/env python3
"""Check the in-memory Current11 Task 2 batch-index remap adapter V1."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from covalent_ext import covapie_current11_task2_batch_index_remap_adapter_v1 as adapter


_ERROR = "COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_ADAPTER_V1_ERROR"


class _Parser(argparse.ArgumentParser):
    def error(self, _message: str) -> None:
        raise ValueError(_ERROR)


def _arguments(argv: list[str]) -> argparse.Namespace:
    parser = _Parser(add_help=False, allow_abbrev=False)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--state-root", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        arguments = _arguments(sys.argv[1:] if argv is None else argv)
        repo_root = Path(arguments.repo_root)
        state_root = Path(arguments.state_root)
        adapter_input = adapter._build_canonical_adapter_input_v1(
            repo_root=repo_root,
            state_root=state_root,
        )
        artifacts = adapter.build_covapie_current11_task2_batch_index_remap_adapter_v1(
            repo_root=repo_root,
            state_root=state_root,
            adapter_input=adapter_input,
        )
        report = json.loads(
            artifacts["current11_task2_batch_index_remap_adapter_report.json"].decode("utf-8"),
            parse_constant=lambda _value: (_ for _ in ()).throw(ValueError(_ERROR)),
        )
        if (
            type(report) is not dict
            or report.get("adapter_status") != "PASS_IN_MEMORY_TASK2_BATCH_INDEX_REMAP_ONLY"
            or report.get("remap_status") != "REMAPPED_EXACT"
            or report.get("failure_reason") != "NONE"
        ):
            raise ValueError(_ERROR)
        line = json.dumps(
            report,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except BaseException:
        sys.stderr.write(_ERROR + "\n")
        return 1
    sys.stdout.write(line + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
