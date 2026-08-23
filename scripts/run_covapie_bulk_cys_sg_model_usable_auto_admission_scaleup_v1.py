#!/usr/bin/env python3
"""Run the CovaPIE ranks 501--1000 scale-up V1."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from covalent_ext import (  # noqa: E402
    covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1 as scaleup,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", choices=(
            scaleup.PREFLIGHT_NO_NETWORK,
            scaleup.CONTROLLED_NETWORK_EXECUTION,
            scaleup.REPLAY_NO_NETWORK,
        ), default=scaleup.DEFAULT_MODE,
    )
    parser.add_argument("--authorize-network", action="store_true")
    arguments = parser.parse_args()
    result = scaleup.run_v1(
        repo_root=REPO_ROOT, mode=arguments.mode,
        network_authorized=arguments.authorize_network,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
