#!/usr/bin/env python3
"""Run the CovaPIE 500-event executor; safe no-network preflight by default."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from covalent_ext import covapie_bulk_500_event_executor_v1 as executor


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "CovaPIE additive 500-event executor. The default mode performs "
            "read-only preflight with zero network requests and zero cache writes."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--cache-root", type=Path)
    parser.add_argument(
        "--mode",
        choices=(
            executor.PREFLIGHT_NO_NETWORK,
            executor.CONTROLLED_NETWORK_EXECUTION,
        ),
        default=executor.PREFLIGHT_NO_NETWORK,
    )
    parser.add_argument(
        "--authorize-network-execution",
        action="store_true",
        help=(
            "Required in addition to CONTROLLED_NETWORK_EXECUTION mode; invalid "
            "in preflight mode."
        ),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        help="Explicit task-owned external output root required for controlled mode.",
    )
    arguments = parser.parse_args()
    result = executor.run_v1(
        repo_root=arguments.repo_root,
        mode=arguments.mode,
        network_authorized=arguments.authorize_network_execution,
        cache_root=arguments.cache_root,
        output_root=arguments.output_root,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
