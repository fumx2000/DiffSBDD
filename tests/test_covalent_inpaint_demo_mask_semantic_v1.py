from __future__ import annotations

import ast
import inspect
from pathlib import Path

import pytest

from scripts import covalent_inpaint_demo as demo


ROOT = Path(__file__).resolve().parents[1]
DEMO_PATH = ROOT / "scripts/covalent_inpaint_demo.py"
DEMO_SOURCE = DEMO_PATH.read_text(encoding="utf-8")
DEMO_TREE = ast.parse(DEMO_SOURCE)

SCAFFOLD = [0, 1, 2]
LINKER = [3, 4]
WARHEAD = [5, 6]
NUM_ATOMS = 7

EXPECTED_MASKS = (
    (
        "warhead_only",
        "A_warhead_only",
        (0, 1, 2, 3, 4),
        (5, 6),
        [1, 1, 1, 1, 1, 0, 0],
    ),
    (
        "linker_plus_warhead",
        "B_linker_warhead",
        (0, 1, 2),
        (3, 4, 5, 6),
        [1, 1, 1, 0, 0, 0, 0],
    ),
    (
        "scaffold_plus_warhead",
        "B2_scaffold_warhead",
        (3, 4),
        (0, 1, 2, 5, 6),
        [0, 0, 0, 1, 1, 0, 0],
    ),
    (
        "scaffold_only",
        "B3_scaffold_only",
        (3, 4, 5, 6),
        (0, 1, 2),
        [0, 0, 0, 1, 1, 1, 1],
    ),
    (
        "scaffold_plus_linker_plus_warhead",
        "C_scaffold_linker_warhead",
        (),
        (0, 1, 2, 3, 4, 5, 6),
        [0, 0, 0, 0, 0, 0, 0],
    ),
)

INVALID_MASK_SEMANTICS = (
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
)


def _parser_argv(mask_semantic: str) -> list[str]:
    return [
        "--protein_pdb",
        "protein.pdb",
        "--ligand_sdf",
        "ligand.sdf",
        "--scaffold_atoms",
        "0 1 2",
        "--linker_atoms",
        "3 4",
        "--warhead_atoms",
        "5 6",
        "--mask_semantic",
        mask_semantic,
        "--checkpoint",
        "model.ckpt",
        "--output",
        "output.sdf",
    ]


def _dotted_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def _option_definitions(option: str) -> list[ast.Call]:
    return [
        node
        for node in ast.walk(DEMO_TREE)
        if isinstance(node, ast.Call)
        and _dotted_name(node.func).endswith(".add_argument")
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == option
    ]


@pytest.mark.parametrize(
    ("semantic", "internal", "visible", "masked", "lig_fixed"),
    EXPECTED_MASKS,
)
def test_canonical_mapping_and_toy_mask_result(
    semantic, internal, visible, masked, lig_fixed
):
    assert demo.resolve_mask_semantic(semantic) == internal

    result = demo.build_canonical_mask(
        mask_semantic=semantic,
        scaffold_atoms=SCAFFOLD,
        linker_atoms=LINKER,
        warhead_atoms=WARHEAD,
        num_ligand_atoms=NUM_ATOMS,
    )

    assert result.mask_type == internal
    assert result.visible_atoms == visible
    assert result.masked_atoms == masked
    assert result.lig_fixed.tolist() == lig_fixed


def test_canonical_order_mapping_and_count_are_exact():
    expected_semantics = tuple(case[0] for case in EXPECTED_MASKS)
    expected_mapping = {case[0]: case[1] for case in EXPECTED_MASKS}

    assert demo.CANONICAL_MASK_SEMANTICS == expected_semantics
    assert demo.MASK_SEMANTIC_TO_INTERNAL == expected_mapping
    assert len(demo.CANONICAL_MASK_SEMANTICS) == 5
    assert demo.MASK_SEMANTIC_TO_INTERNAL["scaffold_plus_warhead"] == "B2_scaffold_warhead"
    assert demo.MASK_SEMANTIC_TO_INTERNAL["scaffold_only"] == "B3_scaffold_only"


def test_b2_and_b3_masks_are_explicitly_distinct():
    b2 = demo.build_canonical_mask(
        mask_semantic="scaffold_plus_warhead",
        scaffold_atoms=SCAFFOLD,
        linker_atoms=LINKER,
        warhead_atoms=WARHEAD,
        num_ligand_atoms=NUM_ATOMS,
    )
    b3 = demo.build_canonical_mask(
        mask_semantic="scaffold_only",
        scaffold_atoms=SCAFFOLD,
        linker_atoms=LINKER,
        warhead_atoms=WARHEAD,
        num_ligand_atoms=NUM_ATOMS,
    )

    assert b2.masked_atoms != b3.masked_atoms
    assert b2.visible_atoms != b3.visible_atoms


@pytest.mark.parametrize("invalid", INVALID_MASK_SEMANTICS)
def test_resolver_rejects_noncanonical_values_with_exact_error(invalid):
    with pytest.raises(ValueError) as exc_info:
        demo.resolve_mask_semantic(invalid)

    assert exc_info.value.args == ("COVAPIE_COVALENT_DEMO_MASK_SEMANTIC_INVALID",)


@pytest.mark.parametrize("semantic", demo.CANONICAL_MASK_SEMANTICS)
def test_parser_accepts_each_canonical_long_semantic(semantic):
    args = demo.build_parser().parse_args(_parser_argv(semantic))

    assert args.mask_semantic == semantic
    assert hasattr(args, "mask_semantic")
    assert not hasattr(args, "mask_level")


@pytest.mark.parametrize(
    "invalid",
    (
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
    ),
)
def test_parser_rejects_short_aliases_and_internal_names(invalid):
    with pytest.raises(SystemExit) as exc_info:
        demo.build_parser().parse_args(_parser_argv(invalid))

    assert exc_info.value.code == 2


def test_parser_surface_is_exact_and_has_no_target_residue_forwarding():
    parser = demo.build_parser()
    actions_by_option = {
        option: action for action in parser._actions for option in action.option_strings
    }

    assert tuple(actions_by_option["--mask_semantic"].choices) == demo.CANONICAL_MASK_SEMANTICS
    assert "--mask_level" not in actions_by_option
    assert "--target_residue_atom_conditioning" not in actions_by_option
    assert "--target_chain_id" not in actions_by_option
    assert "--target_residue_sequence_number" not in actions_by_option


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"scaffold_atoms": [0, 1], "linker_atoms": [1, 2]}, "disjoint"),
        ({"warhead_atoms": [5, 7]}, "outside"),
        ({"linker_atoms": [3, 3]}, "duplicate"),
        ({"scaffold_atoms": []}, "nonempty"),
    ),
)
def test_pure_mask_builder_preserves_long_form_partition_validation(kwargs, message):
    atom_groups = {
        "scaffold_atoms": SCAFFOLD,
        "linker_atoms": LINKER,
        "warhead_atoms": WARHEAD,
    }
    atom_groups.update(kwargs)

    with pytest.raises(ValueError, match=message):
        demo.build_canonical_mask(
            mask_semantic="warhead_only",
            num_ligand_atoms=NUM_ATOMS,
            **atom_groups,
        )


@pytest.mark.parametrize("semantic", demo.CANONICAL_MASK_SEMANTICS)
def test_whole_ligand_operation_selection_is_exact(semantic):
    assert demo.is_whole_ligand_generation_semantic(semantic) is (
        semantic == "scaffold_plus_linker_plus_warhead"
    )


def test_legacy_c_is_rejected_before_whole_ligand_selection():
    with pytest.raises(ValueError) as exc_info:
        demo.is_whole_ligand_generation_semantic("C")

    assert exc_info.value.args == ("COVAPIE_COVALENT_DEMO_MASK_SEMANTIC_INVALID",)


def test_demo_runtime_public_parameter_surface_uses_only_mask_semantic():
    parameters = inspect.signature(demo.run_covalent_inpaint).parameters

    assert "mask_semantic" in parameters
    assert "mask_level" not in parameters


def test_demo_ast_preserves_runtime_calls_and_migrates_builder_once():
    imports = [
        alias.name
        for node in ast.walk(DEMO_TREE)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    ]
    call_names = [
        _dotted_name(node.func)
        for node in ast.walk(DEMO_TREE)
        if isinstance(node, ast.Call)
    ]

    assert imports.count("build_four_level_mask") == 0
    assert call_names.count("build_four_level_mask") == 0
    assert imports.count("build_long_form_mask") == 1
    assert call_names.count("build_long_form_mask") == 1
    assert call_names.count("LigandPocketDDPM.load_from_checkpoint") == 1
    assert call_names.count("model.ddpm.sample_given_pocket") == 1
    assert call_names.count("model.ddpm.inpaint") == 2
    assert call_names.count("is_whole_ligand_generation_semantic") == 1


def test_demo_ast_has_only_the_canonical_mask_cli_definition():
    assert len(_option_definitions("--mask_level")) == 0
    assert len(_option_definitions("--mask_semantic")) == 1

    legacy_choices = 0
    for node in ast.walk(DEMO_TREE):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if keyword.arg != "choices":
                continue
            try:
                value = ast.literal_eval(keyword.value)
            except (ValueError, TypeError):
                continue
            if value == ["A", "B", "B2", "C"]:
                legacy_choices += 1
    assert legacy_choices == 0
