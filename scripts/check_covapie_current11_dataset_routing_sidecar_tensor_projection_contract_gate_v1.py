#!/usr/bin/env python3
"""Check the Current11 routing tensor-projection contract gate V1."""

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

from covalent_ext.covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1 import (  # noqa: E402
    ARTIFACT_NAMES,
    ERROR_TOKEN,
    build_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1,
)


class _FailClosedParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        del message
        raise ValueError(ERROR_TOKEN)


def _parser() -> argparse.ArgumentParser:
    parser = _FailClosedParser(add_help=False, allow_abbrev=False)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        arguments = _parser().parse_args(argv)
        artifacts = build_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1(
            repo_root=arguments.repo_root,
            state_root=arguments.state_root,
        )
        report = json.loads(artifacts[ARTIFACT_NAMES[3]].decode("utf-8"))
        encoded = json.dumps(
            report,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        )
    except Exception:
        print(ERROR_TOKEN, file=sys.stderr)
        return 1
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
