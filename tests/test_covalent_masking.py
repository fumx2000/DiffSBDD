from __future__ import annotations

import ast
import inspect
from dataclasses import fields
from pathlib import Path
import sys
from typing import get_args, get_type_hints

import pytest
import torch

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
    LONG_FORM_MASK_BUILDERS,
    LONG_FORM_MASK_COMPONENTS,
    build_canonical_mask,
    build_long_form_mask,
    resolve_canonical_mask_semantic,
)
from covalent_ext.schema import CanonicalMaskSemantic, LongFormMaskLevel, MaskResult


SCAFFOLD = [0, 1, 2]
LINKER = [3, 4]
WARHEAD = [5, 6]
NUM_ATOMS = 7
EXPECTED_SEMANTICS = (
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
)
EXPECTED_LEVELS = (
    "A_warhead_only",
    "B_linker_warhead",
    "B2_scaffold_warhead",
    "B3_scaffold_only",
    "C_scaffold_linker_warhead",
)
EXPECTED_MAPPING = dict(zip(EXPECTED_SEMANTICS, EXPECTED_LEVELS))
EXPECTED_MASKS = {
    "warhead_only": ((0, 1, 2, 3, 4), (5, 6), [1, 1, 1, 1, 1, 0, 0]),
    "linker_plus_warhead": ((0, 1, 2), (3, 4, 5, 6), [1, 1, 1, 0, 0, 0, 0]),
    "scaffold_plus_warhead": ((3, 4), (0, 1, 2, 5, 6), [0, 0, 0, 1, 1, 0, 0]),
    "scaffold_only": ((3, 4, 5, 6), (0, 1, 2), [0, 0, 0, 1, 1, 1, 1]),
    "scaffold_plus_linker_plus_warhead": ((), (0, 1, 2, 3, 4, 5, 6), [0, 0, 0, 0, 0, 0, 0]),
}
LEGACY_SYMBOLS = {
    "MaskType",
    "build_four_level_mask",
    "MASK_BUILDERS",
    "mask_warhead",
    "mask_linker_and_warhead",
    "mask_scaffold",
    "mask_whole_ligand",
}


def assert_mask(result, level, visible, masked, lig_fixed):
    assert result.mask_type == level
    assert result.visible_atoms == tuple(visible)
    assert result.masked_atoms == tuple(masked)
    assert torch.equal(result.lig_fixed, torch.tensor(lig_fixed, dtype=torch.long))


def canonical_mask(semantic):
    return build_canonical_mask(
        mask_semantic=semantic,
        scaffold_atoms=SCAFFOLD,
        linker_atoms=LINKER,
        warhead_atoms=WARHEAD,
        num_ligand_atoms=NUM_ATOMS,
    )


def toy_sample():
    return {
        "pre_reaction_ligand_graph": {"atom_symbols": ["C"] * NUM_ATOMS},
        "scaffold_atoms": SCAFFOLD,
        "linker_atoms": LINKER,
        "warhead_atoms": WARHEAD,
    }


def test_canonical_types_order_mapping_and_no_sixth_mask():
    assert get_args(CanonicalMaskSemantic) == EXPECTED_SEMANTICS
    assert get_args(LongFormMaskLevel) == EXPECTED_LEVELS
    assert CANONICAL_MASK_SEMANTICS == EXPECTED_SEMANTICS
    assert CANONICAL_MASK_SEMANTIC_TO_LEVEL == EXPECTED_MAPPING
    assert tuple(LONG_FORM_MASK_COMPONENTS) == EXPECTED_LEVELS
    assert tuple(LONG_FORM_MASK_BUILDERS) == EXPECTED_LEVELS
    assert len(CANONICAL_MASK_SEMANTICS) == 5


@pytest.mark.parametrize("semantic", EXPECTED_SEMANTICS)
def test_canonical_five_level_toy_masks(semantic):
    visible, masked, fixed = EXPECTED_MASKS[semantic]
    assert_mask(
        canonical_mask(semantic),
        EXPECTED_MAPPING[semantic],
        visible,
        masked,
        fixed,
    )


def test_canonical_b2_and_b3_are_distinct():
    b2 = canonical_mask("scaffold_plus_warhead")
    b3 = canonical_mask("scaffold_only")
    assert b2.visible_atoms != b3.visible_atoms
    assert b2.masked_atoms != b3.masked_atoms


@pytest.mark.parametrize(
    "rejected",
    [
        "",
        "unknown",
        " warhead_only ",
        "A",
        "B",
        "B2",
        "B3",
        "C",
        "A_warhead_only",
        "B_linker_warhead",
        "B2_scaffold_warhead",
        "B3_scaffold_only",
        "C_scaffold_linker_warhead",
        None,
        0,
        1,
        True,
        False,
    ],
)
def test_resolver_and_public_builder_fail_closed(rejected):
    with pytest.raises(
        ValueError, match="^COVAPIE_CANONICAL_MASK_SEMANTIC_INVALID$"
    ):
        resolve_canonical_mask_semantic(rejected)
    with pytest.raises(
        ValueError, match="^COVAPIE_CANONICAL_MASK_SEMANTIC_INVALID$"
    ):
        canonical_mask(rejected)


def test_legacy_api_is_not_exposed_or_importable():
    assert all(not hasattr(masking, name) for name in LEGACY_SYMBOLS - {"MaskType"})
    assert not hasattr(schema, "MaskType")
    for module_name, symbol in (
        ("covalent_ext.schema", "MaskType"),
        ("covalent_ext.masking", "build_four_level_mask"),
        ("covalent_ext.masking", "MASK_BUILDERS"),
        ("covalent_ext.masking", "mask_scaffold"),
    ):
        with pytest.raises(ImportError):
            exec(f"from {module_name} import {symbol}", {})


def test_active_sources_have_no_legacy_definitions_imports_calls_or_names():
    for relative_path in (
        "src/covalent_ext/masking.py",
        "src/covalent_ext/schema.py",
        "src/covalent_ext/dataset.py",
        "scripts/check_covalent_masking.py",
    ):
        tree = ast.parse(
            (REPO_ROOT / relative_path).read_text(encoding="utf-8"),
            filename=relative_path,
        )
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                assert node.name not in LEGACY_SYMBOLS
            if isinstance(node, ast.Name):
                assert node.id not in LEGACY_SYMBOLS
            if isinstance(node, ast.Attribute):
                assert node.attr not in LEGACY_SYMBOLS
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                assert all(
                    alias.name not in LEGACY_SYMBOLS
                    and alias.asname not in LEGACY_SYMBOLS
                    for alias in node.names
                )


def test_expanded_dataset_consumers_use_canonical_keys_by_ast():
    legacy_short_keys = {"A", "B", "B2", "C"}
    consumer_paths = (
        "scripts/check_covalent_dataset.py",
        "scripts/check_covalent_real_small.py",
        "tests/test_covalent_real_small_builder.py",
        "tests/test_covalent_dataset.py",
    )
    assert len(consumer_paths) == 4
    for relative_path in consumer_paths:
        tree = ast.parse(
            (REPO_ROOT / relative_path).read_text(encoding="utf-8"),
            filename=relative_path,
        )
        names = {
            node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
        }
        assert "CANONICAL_MASK_SEMANTICS" in names
        assert "CANONICAL_MASK_SEMANTIC_TO_LEVEL" in names
        for node in ast.walk(tree):
            if isinstance(node, (ast.List, ast.Set, ast.Tuple)) and all(
                isinstance(element, ast.Constant)
                and type(element.value) is str
                for element in node.elts
            ):
                values = tuple(element.value for element in node.elts)
                assert not (
                    len(values) == 4 and set(values) == legacy_short_keys
                )
            if (
                isinstance(node, ast.Subscript)
                and isinstance(node.value, ast.Name)
                and node.value.id == "masks"
                and isinstance(node.slice, ast.Constant)
            ):
                assert node.slice.value not in legacy_short_keys


def test_dataset_build_mask_signature_and_canonical_five_results():
    dataset = CovalentJsonlDataset.__new__(CovalentJsonlDataset)
    assert list(inspect.signature(dataset.build_mask).parameters) == [
        "sample",
        "mask_semantic",
    ]
    masks = dataset.build_all_masks(toy_sample())
    assert tuple(masks) == EXPECTED_SEMANTICS
    assert len(masks) == 5
    for semantic, result in masks.items():
        visible, masked, fixed = EXPECTED_MASKS[semantic]
        assert_mask(result, EXPECTED_MAPPING[semantic], visible, masked, fixed)


@pytest.mark.parametrize("rejected", ["A", "B", "B2", "B3", "C", *EXPECTED_LEVELS])
def test_dataset_rejects_short_aliases_and_internal_levels(rejected):
    dataset = CovalentJsonlDataset.__new__(CovalentJsonlDataset)
    with pytest.raises(
        ValueError, match="^COVAPIE_CANONICAL_MASK_SEMANTIC_INVALID$"
    ):
        dataset.build_mask(toy_sample(), rejected)


def test_schema_uses_canonical_sample_field_and_internal_result_level():
    sample_fields = {field.name for field in fields(schema.CovalentSample)}
    assert "mask_semantic" in sample_fields
    assert "mask_type" not in sample_fields
    assert get_type_hints(schema.CovalentSample)["mask_semantic"] == CanonicalMaskSemantic
    assert get_type_hints(MaskResult)["mask_type"] == LongFormMaskLevel


@pytest.mark.parametrize(
    ("scaffold", "linker", "warhead", "message"),
    [
        (None, LINKER, WARHEAD, "scaffold_atoms is missing"),
        (SCAFFOLD, None, WARHEAD, "linker_atoms is missing"),
        (SCAFFOLD, LINKER, None, "warhead_atoms is missing"),
        ([], LINKER, WARHEAD, "scaffold_atoms"),
        (SCAFFOLD, [], WARHEAD, "linker_atoms"),
        (SCAFFOLD, LINKER, [], "warhead_atoms"),
    ],
)
def test_partition_missing_and_empty_regions_fail_closed(
    scaffold, linker, warhead, message
):
    with pytest.raises(ValueError, match=message):
        build_long_form_mask(
            "B3_scaffold_only", scaffold, linker, warhead, NUM_ATOMS
        )


@pytest.mark.parametrize(
    ("scaffold", "linker", "warhead", "num_atoms", "message"),
    [
        ([0, 1], [1, 2], [3], 4, "disjoint"),
        ([0, 9], [1], [2], 3, "outside"),
        ([0, 0], [1], [2], 3, "duplicate"),
        ([0], [1], [2], 0, "positive"),
        ([0], [1], [2], -1, "positive"),
    ],
)
def test_partition_overlap_range_duplicate_and_atom_count_fail_closed(
    scaffold, linker, warhead, num_atoms, message
):
    with pytest.raises(ValueError, match=message):
        build_long_form_mask(
            "A_warhead_only", scaffold, linker, warhead, num_atoms
        )
