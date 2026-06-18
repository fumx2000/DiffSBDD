#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def download_single_pdb(pdb_id: str, output: str | Path) -> Path:
    pdb_id = pdb_id.strip().upper()
    if not pdb_id:
        raise ValueError("pdb_id must not be empty")

    output = Path(output)
    url = f"https://files.rcsb.org/download/{pdb_id}.pdb"

    try:
        with urlopen(url, timeout=60) as response:
            data = response.read()
    except HTTPError as exc:
        raise RuntimeError(f"failed to download {pdb_id} from RCSB ({url}): HTTP {exc.code}") from exc
    except URLError as exc:
        raise RuntimeError(f"failed to download {pdb_id} from RCSB ({url}): {exc.reason}") from exc

    if not data.startswith((b"HEADER", b"TITLE", b"COMPND", b"REMARK")):
        raise RuntimeError(f"downloaded data for {pdb_id} does not look like a PDB file")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download one PDB file from RCSB.")
    parser.add_argument("--pdb_id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        output = download_single_pdb(args.pdb_id, args.output)
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"downloaded {args.pdb_id.upper()} to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
