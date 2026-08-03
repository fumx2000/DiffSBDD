from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from covalent_ext.masking import build_canonical_mask


HISTORICAL_SOURCE = REPO_ROOT / "src/covalent_ext/b3_scaffold_only_mask_implementation.py"
HISTORICAL_CHECKER = REPO_ROOT / "scripts/check_b3_scaffold_only_mask_implementation_v0.py"
HISTORICAL_SOURCE_SHA256 = (
    "e142d6aa7f64722f4e07391f80d7106c9a3b7cd4a7dcfed77b69231e209575d5"
)
HISTORICAL_CHECKER_SHA256 = (
    "16fe45ec778ab4e50181eeaa03b1a0e1a79bea9cc4ce693f5d423c08f122548b"
)
HISTORICAL_STAGE = "b3_scaffold_only_mask_implementation_v0"
HISTORICAL_OUTPUT_ROOT = REPO_ROOT / f"data/derived/covalent_small/{HISTORICAL_STAGE}"
SCAFFOLD = [0, 1, 2]
LINKER = [3, 4]
WARHEAD = [5, 6]
NUM_ATOMS = 7


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_historical_source_and_checker_bytes_are_frozen_read_only_evidence():
    assert _sha256(HISTORICAL_SOURCE) == HISTORICAL_SOURCE_SHA256
    assert _sha256(HISTORICAL_CHECKER) == HISTORICAL_CHECKER_SHA256


def test_historical_derived_outputs_exist_and_identify_the_historical_stage():
    manifest_path = HISTORICAL_OUTPUT_ROOT / "b3_scaffold_only_mask_implementation_manifest.json"
    report_path = HISTORICAL_OUTPUT_ROOT / "b3_scaffold_only_mask_implementation_report.csv"
    audit_path = HISTORICAL_OUTPUT_ROOT / "b3_scaffold_only_mask_api_audit_report.csv"
    assert manifest_path.is_file()
    assert report_path.is_file()
    assert audit_path.is_file()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    with report_path.open(newline="", encoding="utf-8") as handle:
        report_stages = {row["stage"] for row in csv.DictReader(handle)}
    with audit_path.open(newline="", encoding="utf-8") as handle:
        audit_stages = {row["stage"] for row in csv.DictReader(handle)}
    assert manifest["stage"] == HISTORICAL_STAGE
    assert report_stages == {HISTORICAL_STAGE}
    assert audit_stages == {HISTORICAL_STAGE}


def test_current_test_does_not_import_or_execute_historical_code():
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"), filename=__file__)
    forbidden_modules = {
        "covalent_ext.b3_scaffold_only_mask_implementation",
        "check_b3_scaffold_only_mask_implementation_v0",
    }
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
    assert imported_modules.isdisjoint(forbidden_modules)
    assert "covalent_ext.b3_scaffold_only_mask_implementation" not in sys.modules


def test_current_package_and_active_runtime_do_not_depend_on_historical_module():
    active_paths = (
        "src/covalent_ext/__init__.py",
        "src/covalent_ext/schema.py",
        "src/covalent_ext/masking.py",
        "src/covalent_ext/dataset.py",
        "scripts/check_covalent_masking.py",
        "scripts/covalent_inpaint_demo.py",
    )
    forbidden_module = "covalent_ext.b3_scaffold_only_mask_implementation"
    for relative_path in active_paths:
        tree = ast.parse(
            (REPO_ROOT / relative_path).read_text(encoding="utf-8"),
            filename=relative_path,
        )
        imports = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module
        }
        imports.update(
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        )
        assert forbidden_module not in imports


def test_current_canonical_b2_and_b3_are_independently_distinct():
    common = {
        "scaffold_atoms": SCAFFOLD,
        "linker_atoms": LINKER,
        "warhead_atoms": WARHEAD,
        "num_ligand_atoms": NUM_ATOMS,
    }
    b2 = build_canonical_mask(mask_semantic="scaffold_plus_warhead", **common)
    b3 = build_canonical_mask(mask_semantic="scaffold_only", **common)
    assert b2.mask_type == "B2_scaffold_warhead"
    assert b2.visible_atoms == tuple(LINKER)
    assert b2.masked_atoms == tuple(SCAFFOLD + WARHEAD)
    assert b3.mask_type == "B3_scaffold_only"
    assert b3.visible_atoms == tuple(LINKER + WARHEAD)
    assert b3.masked_atoms == tuple(SCAFFOLD)
    assert b2.visible_atoms != b3.visible_atoms
    assert b2.masked_atoms != b3.masked_atoms


def test_no_protected_source_diff_is_present():
    result = subprocess.run(
        ["git", "diff", "--quiet", "--", "equivariant_diffusion/", "lightning_modules.py"],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0


def test_no_forbidden_artifacts_in_historical_output_root():
    forbidden = {
        ".pt",
        ".pkl",
        ".lmdb",
        ".tar",
        ".zip",
        ".tgz",
        ".ckpt",
        ".pth",
        ".npz",
    }
    assert [
        path
        for path in HISTORICAL_OUTPUT_ROOT.rglob("*")
        if path.is_file() and path.suffix in forbidden
    ] == []
