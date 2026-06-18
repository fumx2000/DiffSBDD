#!/usr/bin/env python
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


RCSB_BASE = "https://files.rcsb.org"


@dataclass(frozen=True)
class DownloadTarget:
    url: str
    filename: str
    required: bool


def download_file(target: DownloadTarget, output_dir: Path) -> bool:
    output_path = output_dir / target.filename
    try:
        with urlopen(target.url, timeout=60) as response:  # noqa: S310 - fixed RCSB URLs from CLI IDs.
            payload = response.read()
    except HTTPError as exc:
        message = f"{exc.code} {exc.reason}"
        if target.required:
            raise RuntimeError(f"required download failed: {target.url}: {message}") from exc
        print(f"warning: optional download failed: {target.url}: {message}")
        return False
    except URLError as exc:
        if target.required:
            raise RuntimeError(f"required download failed: {target.url}: {exc.reason}") from exc
        print(f"warning: optional download failed: {target.url}: {exc.reason}")
        return False

    output_path.write_bytes(payload)
    print(f"downloaded: {target.url} -> {output_path} ({len(payload)} bytes)")
    return True


def build_targets(pdb_id: str, ligand_id: str) -> list[DownloadTarget]:
    pdb_id = pdb_id.upper()
    ligand_id = ligand_id.upper()
    return [
        DownloadTarget(f"{RCSB_BASE}/download/{pdb_id}.cif", f"{pdb_id}.cif", True),
        DownloadTarget(f"{RCSB_BASE}/ligands/download/{ligand_id}.cif", f"{ligand_id}.cif", True),
        DownloadTarget(f"{RCSB_BASE}/ligands/download/{ligand_id}_ideal.sdf", f"{ligand_id}_ideal.sdf", True),
        DownloadTarget(f"{RCSB_BASE}/ligands/download/{ligand_id}_model.sdf", f"{ligand_id}_model.sdf", False),
        DownloadTarget(f"{RCSB_BASE}/ligands/download/{ligand_id}_model.mol2", f"{ligand_id}_model.mol2", False),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Download reference files for one RCSB PDB ligand.")
    parser.add_argument("--pdb_id", required=True)
    parser.add_argument("--ligand_id", required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    successes = []
    for target in build_targets(args.pdb_id, args.ligand_id):
        successes.append((target.filename, download_file(target, args.output_dir)))

    print("download_summary:")
    for filename, ok in successes:
        print(f"{filename}: {'OK' if ok else 'FAILED_OPTIONAL'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
