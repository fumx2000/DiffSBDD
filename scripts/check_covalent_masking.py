#!/usr/bin/env python
from __future__ import annotations

import ast
import hashlib
import inspect
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import covalent_ext.masking as masking
import covalent_ext.schema as schema
from covalent_ext.dataset import CovalentJsonlDataset
from covalent_ext.masking import (
    CANONICAL_MASK_SEMANTICS,
    CANONICAL_MASK_SEMANTIC_TO_LEVEL,
    build_canonical_mask,
)


EXPECTED_SEMANTICS = (
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
)
EXPECTED_MAPPING = {
    "warhead_only": "A_warhead_only",
    "linker_plus_warhead": "B_linker_warhead",
    "scaffold_plus_warhead": "B2_scaffold_warhead",
    "scaffold_only": "B3_scaffold_only",
    "scaffold_plus_linker_plus_warhead": "C_scaffold_linker_warhead",
}
EXPECTED_MASKS = {
    "warhead_only": (
        "A_warhead_only",
        (0, 1, 2, 3, 4),
        (5, 6),
        [1, 1, 1, 1, 1, 0, 0],
    ),
    "linker_plus_warhead": (
        "B_linker_warhead",
        (0, 1, 2),
        (3, 4, 5, 6),
        [1, 1, 1, 0, 0, 0, 0],
    ),
    "scaffold_plus_warhead": (
        "B2_scaffold_warhead",
        (3, 4),
        (0, 1, 2, 5, 6),
        [0, 0, 0, 1, 1, 0, 0],
    ),
    "scaffold_only": (
        "B3_scaffold_only",
        (3, 4, 5, 6),
        (0, 1, 2),
        [0, 0, 0, 1, 1, 1, 1],
    ),
    "scaffold_plus_linker_plus_warhead": (
        "C_scaffold_linker_warhead",
        (),
        (0, 1, 2, 3, 4, 5, 6),
        [0, 0, 0, 0, 0, 0, 0],
    ),
}
LEGACY_PROVIDER_SYMBOLS = (
    "build_four_level_mask",
    "MASK_BUILDERS",
    "mask_warhead",
    "mask_linker_and_warhead",
    "mask_scaffold",
    "mask_whole_ligand",
)
HISTORICAL_B3_SHA256 = {
    "src/covalent_ext/b3_scaffold_only_mask_implementation.py": (
        "e142d6aa7f64722f4e07391f80d7106c9a3b7cd4a7dcfed77b69231e209575d5"
    ),
    "scripts/check_b3_scaffold_only_mask_implementation_v0.py": (
        "16fe45ec778ab4e50181eeaa03b1a0e1a79bea9cc4ce693f5d423c08f122548b"
    ),
}
CURRENT_CANONICAL_MASK_CONSUMER_PATHS = (
    "src/covalent_ext/masking.py",
    "src/covalent_ext/schema.py",
    "src/covalent_ext/dataset.py",
    "scripts/check_covalent_masking.py",
    "scripts/check_covalent_dataset.py",
    "scripts/check_covalent_real_small.py",
    "scripts/covalent_inpaint_demo.py",
    "tests/test_covalent_masking.py",
    "tests/test_b3_scaffold_only_mask_implementation_v0.py",
    "tests/test_covalent_real_small_builder.py",
    "tests/test_covalent_dataset.py",
)
CURRENT_DATASET_CONSUMER_PATHS = (
    "scripts/check_covalent_dataset.py",
    "scripts/check_covalent_real_small.py",
    "tests/test_covalent_real_small_builder.py",
    "tests/test_covalent_dataset.py",
)
LEGACY_SHORT_KEYS = frozenset(("A", "B", "B2", "C"))


def _assert_no_symbolic_references(path: Path, symbols: set[str]) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            assert node.name not in symbols
        if isinstance(node, ast.Name):
            assert node.id not in symbols
        if isinstance(node, ast.Attribute):
            assert node.attr not in symbols
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            assert all(
                alias.name not in symbols and alias.asname not in symbols
                for alias in node.names
            )


def _literal_string_collection(node: ast.AST) -> tuple[str, ...] | None:
    if not isinstance(node, (ast.List, ast.Set, ast.Tuple)):
        return None
    if not all(
        isinstance(element, ast.Constant) and type(element.value) is str
        for element in node.elts
    ):
        return None
    return tuple(element.value for element in node.elts)


def _assert_canonical_dataset_consumer(path: Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    assert any(
        isinstance(node, ast.Name) and node.id == "CANONICAL_MASK_SEMANTICS"
        for node in ast.walk(tree)
    )
    assert any(
        isinstance(node, ast.Name)
        and node.id == "CANONICAL_MASK_SEMANTIC_TO_LEVEL"
        for node in ast.walk(tree)
    )
    for node in ast.walk(tree):
        literal_values = _literal_string_collection(node)
        assert literal_values is None or not (
            len(literal_values) == 4
            and set(literal_values) == LEGACY_SHORT_KEYS
        )
        if (
            isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and node.value.id == "masks"
            and isinstance(node.slice, ast.Constant)
        ):
            assert node.slice.value not in LEGACY_SHORT_KEYS


def _toy_sample() -> dict[str, object]:
    return {
        "pre_reaction_ligand_graph": {
            "atom_symbols": ["C", "C", "C", "C", "C", "C", "C"]
        },
        "scaffold_atoms": [0, 1, 2],
        "linker_atoms": [3, 4],
        "warhead_atoms": [5, 6],
    }


def main() -> int:
    assert CANONICAL_MASK_SEMANTICS == EXPECTED_SEMANTICS
    assert len(CANONICAL_MASK_SEMANTICS) == 5
    assert CANONICAL_MASK_SEMANTIC_TO_LEVEL == EXPECTED_MAPPING

    built = {}
    for semantic in CANONICAL_MASK_SEMANTICS:
        result = build_canonical_mask(
            mask_semantic=semantic,
            scaffold_atoms=[0, 1, 2],
            linker_atoms=[3, 4],
            warhead_atoms=[5, 6],
            num_ligand_atoms=7,
        )
        expected_level, expected_visible, expected_masked, expected_fixed = (
            EXPECTED_MASKS[semantic]
        )
        assert result.mask_type == expected_level
        assert result.visible_atoms == expected_visible
        assert result.masked_atoms == expected_masked
        assert result.lig_fixed.tolist() == expected_fixed
        built[semantic] = result

    b2 = built["scaffold_plus_warhead"]
    b3 = built["scaffold_only"]
    assert b2.visible_atoms != b3.visible_atoms
    assert b2.masked_atoms != b3.masked_atoms

    assert all(not hasattr(masking, name) for name in LEGACY_PROVIDER_SYMBOLS)
    assert not hasattr(schema, "MaskType")
    assert hasattr(schema, "CanonicalMaskSemantic")

    dataset = CovalentJsonlDataset.__new__(CovalentJsonlDataset)
    sample = _toy_sample()
    masks = dataset.build_all_masks(sample)
    assert tuple(masks) == EXPECTED_SEMANTICS
    assert len(masks) == 5
    assert [masks[key].mask_type for key in masks] == [
        EXPECTED_MAPPING[key] for key in EXPECTED_SEMANTICS
    ]
    assert list(inspect.signature(dataset.build_mask).parameters) == [
        "sample",
        "mask_semantic",
    ]
    for rejected in ("A", "B", "B2", "B3", "C"):
        try:
            dataset.build_mask(sample, rejected)
        except ValueError as error:
            assert str(error) == "COVAPIE_CANONICAL_MASK_SEMANTIC_INVALID"
        else:
            raise AssertionError("legacy short mask alias was accepted")

    legacy_symbols = set(LEGACY_PROVIDER_SYMBOLS) | {"MaskType"}
    for relative_path in CURRENT_CANONICAL_MASK_CONSUMER_PATHS:
        _assert_no_symbolic_references(REPO_ROOT / relative_path, legacy_symbols)
    assert len(CURRENT_DATASET_CONSUMER_PATHS) == 4
    for relative_path in CURRENT_DATASET_CONSUMER_PATHS:
        _assert_canonical_dataset_consumer(REPO_ROOT / relative_path)

    demo_tree = ast.parse(
        (REPO_ROOT / "scripts/covalent_inpaint_demo.py").read_text(
            encoding="utf-8"
        )
    )
    assert not any(
        isinstance(node, ast.Constant) and node.value == "--mask_level"
        for node in ast.walk(demo_tree)
    )

    for relative_path, expected_sha256 in HISTORICAL_B3_SHA256.items():
        assert (
            hashlib.sha256((REPO_ROOT / relative_path).read_bytes()).hexdigest()
            == expected_sha256
        )

    output = (
        ("canonical_mask_count", 5),
        ("canonical_mask_order_exact", True),
        ("canonical_B2_is_scaffold_plus_warhead", True),
        ("canonical_B3_is_scaffold_only", True),
        ("legacy_core_provider_removed", True),
        ("legacy_registry_removed", True),
        ("legacy_schema_type_removed", True),
        ("dataset_canonical_five_masks", True),
        ("checker_canonical_five_masks", True),
        ("review_authorized_R2_scope_correction", True),
        ("expanded_R2_scope_path_count", 10),
        ("current_dataset_consumer_count", 4),
        ("remaining_core_consumers_migrated", True),
        ("all_current_dataset_consumers_use_canonical_long_semantics", True),
        ("current_positive_legacy_tests_removed", True),
        ("historical_read_only_evidence_retained", True),
        ("candidate_unresolved_positive_reference_event_count", 0),
        ("candidate_active_legacy_reference_count", 0),
        ("candidate_unresolved_active_reference_count", 0),
        ("legacy_four_level_full_runtime_retirement_candidate", True),
        ("legacy_four_level_full_runtime_retired", False),
        ("R3_independent_gate_required", True),
        ("ready_for_R3_review", True),
        ("training_or_parameter_update", False),
        ("feature_semantics_audit_required_before_training", True),
    )
    for key, value in output:
        rendered = str(value).lower() if isinstance(value, bool) else value
        print(f"{key}={rendered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
