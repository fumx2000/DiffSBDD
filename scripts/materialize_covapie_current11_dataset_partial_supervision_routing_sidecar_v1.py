#!/usr/bin/env python3
"""Materialize or check the Current11 routing sidecar Exact4."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext.covapie_current11_dataset_partial_supervision_routing_sidecar_formal_materializer_v1 import (  # noqa: E402
    ERROR_TOKEN,
    _verify_existing,
    materialize_covapie_current11_dataset_partial_supervision_routing_sidecar_v1,
)


class _FailClosedParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        del message
        raise ValueError(ERROR_TOKEN)


def _parser() -> argparse.ArgumentParser:
    parser = _FailClosedParser(add_help=False)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--state-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        arguments = _parser().parse_args(argv)
        if arguments.check:
            summary = _verify_existing(
                repo_root=arguments.repo_root,
                state_root=arguments.state_root,
                output_dir=arguments.output_dir,
            )
        else:
            summary = materialize_covapie_current11_dataset_partial_supervision_routing_sidecar_v1(
                repo_root=arguments.repo_root,
                state_root=arguments.state_root,
                output_dir=arguments.output_dir,
            )
        print(json.dumps(summary, sort_keys=True, separators=(",", ":"), allow_nan=False))
        return 0
    except BaseException:
        print(f"ERROR {ERROR_TOKEN}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
