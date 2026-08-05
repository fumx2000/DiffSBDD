#!/usr/bin/env python3
"""Check the Current11 dataset routing sidecar without materializing it."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import NoReturn, Sequence


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext.covapie_current11_dataset_partial_supervision_routing_sidecar_v1 import (  # noqa: E402
    ERROR_TOKEN,
    build_covapie_current11_dataset_partial_supervision_routing_sidecar_v1,
)


def _identity(payload: bytes) -> dict[str, object]:
    return {
        "bytes": len(payload),
        "lines": payload.count(b"\n"),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


class _FailClosedParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        del message
        raise ValueError(ERROR_TOKEN)


def _parser() -> argparse.ArgumentParser:
    parser = _FailClosedParser(add_help=False)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--state-root", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        artifacts = build_covapie_current11_dataset_partial_supervision_routing_sidecar_v1(
            repo_root=args.repo_root, state_root=args.state_root
        )
        manifest = json.loads(
            artifacts["current11_dataset_partial_supervision_routing_manifest.json"]
        )
        output = {
            "schema_version": manifest["schema_version"],
            "artifact_file_count": len(artifacts),
            "artifacts": {name: _identity(payload) for name, payload in artifacts.items()},
            "sample_count": manifest["sample_count"],
            "task_count": manifest["semantic_task_count"],
            "record_count": manifest["routing_record_count"],
            "global_counts": manifest["global_state_counts"],
            "unit_parity": manifest["unit_000001_parity"],
            "readiness": manifest["readiness"],
            "repository_lifecycle": manifest["repository_lifecycle"],
        }
        print(json.dumps(output, sort_keys=True, separators=(",", ":"), allow_nan=False))
        return 0
    except Exception:
        print(f"ERROR {ERROR_TOKEN}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
