#!/usr/bin/env python3
"""Check the Current11 tensor projection instance builder without writing it."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import NoReturn, Sequence

from covalent_ext.covapie_current11_tensor_projection_instance_builder_v1 import (
    build_covapie_current11_tensor_projection_instance_v1,
)


_ERROR = "COVAPIE_CURRENT11_TENSOR_PROJECTION_INSTANCE_BUILDER_V1_ERROR"
_REPORT_NAME = "current11_tensor_projection_instance_builder_report.json"


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        del message
        raise ValueError(_ERROR)


def _main(arguments: Sequence[str]) -> int:
    parser = _Parser(add_help=False, allow_abbrev=False)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--state-root", required=True, type=Path)
    namespace = parser.parse_args(arguments)
    artifacts = build_covapie_current11_tensor_projection_instance_v1(
        repo_root=namespace.repo_root,
        state_root=namespace.state_root,
    )
    report = json.loads(artifacts[_REPORT_NAME].decode("utf-8"))
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
