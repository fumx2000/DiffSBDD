#!/usr/bin/env python
"""Check the minimal DiffSBDD runtime environment."""

from __future__ import annotations

import importlib
import sys


def check_import(module_name: str, display_name: str | None = None) -> bool:
    name = display_name or module_name
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        print(f"[FAIL] {name}: {type(exc).__name__}: {exc}")
        return False

    version = getattr(module, "__version__", "version unknown")
    print(f"[ OK ] {name}: {version}")
    return True


def check_torch() -> bool:
    try:
        import torch
    except Exception as exc:
        print(f"[FAIL] torch: {type(exc).__name__}: {exc}")
        return False

    print(f"[ OK ] torch: {torch.__version__}")
    print(f"[INFO] torch cuda build: {torch.version.cuda}")
    print(f"[INFO] cuda available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"[INFO] cuda device count: {torch.cuda.device_count()}")
        print(f"[INFO] cuda device 0: {torch.cuda.get_device_name(0)}")
    return True


def check_rdkit_smoke() -> bool:
    try:
        from rdkit import Chem
    except Exception as exc:
        print(f"[FAIL] rdkit smoke: {type(exc).__name__}: {exc}")
        return False

    mol = Chem.MolFromSmiles("CCO")
    if mol is None or mol.GetNumAtoms() != 3:
        print("[FAIL] rdkit smoke: could not parse ethanol SMILES")
        return False

    print("[ OK ] rdkit smoke: parsed CCO")
    return True


def main() -> int:
    print(f"[INFO] python: {sys.version.split()[0]}")
    print(f"[INFO] executable: {sys.executable}")

    checks = [
        check_torch(),
        check_import("torch_scatter"),
        check_import("pytorch_lightning"),
        check_import("rdkit"),
        check_rdkit_smoke(),
        check_import("Bio", "biopython"),
        check_import("openbabel"),
        check_import("yaml", "pyyaml"),
        check_import("numpy"),
        check_import("scipy"),
    ]

    if all(checks):
        print("[ OK ] environment check passed")
        return 0

    print("[FAIL] environment check failed")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
