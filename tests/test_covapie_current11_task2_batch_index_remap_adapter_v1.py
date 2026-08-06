from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from covalent_ext import covapie_current11_task2_batch_index_remap_adapter_v1 as adapter


REPO = Path(__file__).resolve().parents[1]
STATE = REPO.parent / "covapie-state"
MODULE = REPO / "src/covalent_ext/covapie_current11_task2_batch_index_remap_adapter_v1.py"
CHECKER = REPO / "scripts/check_covapie_current11_task2_batch_index_remap_adapter_v1.py"
GUIDE = REPO / "docs/covapie_current11_task2_batch_index_remap_adapter_v1_guide.md"
EXACT4 = (MODULE, CHECKER, Path(__file__), GUIDE)
OUTPUT_NAME = "current11_task2_batch_index_remap_output.json"
REPORT_NAME = "current11_task2_batch_index_remap_adapter_report.json"
ERROR = "COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_ADAPTER_V1_ERROR"


def _git_status() -> bytes:
    return subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=REPO,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout


@pytest.fixture(scope="session")
def contract_exact6() -> dict[str, bytes]:
    return adapter._contract_exact6(REPO, STATE)


@pytest.fixture(scope="session")
def canonical_input(contract_exact6: dict[str, bytes]) -> dict[str, object]:
    original = adapter._contract_gate.build_covapie_current11_task2_batch_index_remap_contract_gate_v1
    adapter._contract_gate.build_covapie_current11_task2_batch_index_remap_contract_gate_v1 = (
        lambda **_kwargs: copy.deepcopy(contract_exact6)
    )
    try:
        return adapter._build_canonical_adapter_input_v1(repo_root=REPO, state_root=STATE)
    finally:
        adapter._contract_gate.build_covapie_current11_task2_batch_index_remap_contract_gate_v1 = original


@pytest.fixture(autouse=True)
def cached_gate(monkeypatch: pytest.MonkeyPatch, contract_exact6: dict[str, bytes]) -> None:
    monkeypatch.setattr(
        adapter._contract_gate,
        "build_covapie_current11_task2_batch_index_remap_contract_gate_v1",
        lambda **_kwargs: copy.deepcopy(contract_exact6),
    )


def _build(value: dict[str, object]) -> tuple[dict[str, bytes], dict[str, object], dict[str, object]]:
    artifacts = adapter.build_covapie_current11_task2_batch_index_remap_adapter_v1(
        repo_root=REPO,
        state_root=STATE,
        adapter_input=value,
    )
    output = json.loads(artifacts[OUTPUT_NAME])
    report = json.loads(artifacts[REPORT_NAME])
    return artifacts, output, report


def _recompute_batch(value: dict[str, object]) -> None:
    lengths = value["batch_role_lengths"]
    value["batch_role_offsets"] = {}
    value["batch_membership_masks"] = {}
    for role in ("pocket", "ligand"):
        offsets = [0]
        mask = []
        for ordinal, length in enumerate(lengths[role]):
            offsets.append(offsets[-1] + length)
            mask.extend([ordinal] * length)
        value["batch_role_offsets"][role] = offsets
        value["batch_membership_masks"][role] = mask


def _ordered(value: dict[str, object], order: list[int]) -> dict[str, object]:
    result = copy.deepcopy(value)
    result["batch_sample_order"] = [result["batch_sample_order"][index] for index in order]
    result["batch_sample_atom_identity_tables"] = [
        result["batch_sample_atom_identity_tables"][index] for index in order
    ]
    result["batch_role_lengths"] = {
        role: [result["batch_role_lengths"][role][index] for index in order]
        for role in ("pocket", "ligand")
    }
    _recompute_batch(result)
    return result


def _non_source_only(value: dict[str, object]) -> dict[str, object]:
    result = _ordered(value, [])
    identity = {
        "source_sample_index": 999,
        "sample_index_row_id": "NON_SOURCE_001",
        "sample_preparation_input_id": "NON_SOURCE_PREP_001",
        "pdb_id": "9ZZZ",
        "ligand_comp_id": "ZZZ",
    }
    table = copy.deepcopy(value["batch_sample_atom_identity_tables"][0])
    table["sample_identity"] = copy.deepcopy(identity)
    result["batch_sample_order"] = [identity]
    result["batch_sample_atom_identity_tables"] = [table]
    result["batch_role_lengths"] = {
        role: [table["roles"][role]["parser_output_atom_count"]]
        for role in ("pocket", "ligand")
    }
    _recompute_batch(result)
    return result


def _assert_contract_rejection(value: dict[str, object], status: str) -> None:
    first, output, report = _build(value)
    second, second_output, second_report = _build(value)
    assert first == second
    assert output == second_output and report == second_report
    assert output["remap_status"] == status and output["failure_reason"] == status
    for field in (
        "pair_values_source_row_indices",
        "pair_values_parser_local_indices",
        "pair_values_batch_indices",
        "pair_sample_indices",
        "entry_validity",
    ):
        assert output[field] == []
    assert output["pair_values_joint_global_indices"] is None
    assert report["adapter_status"] == "FAIL_CLOSED_INPUT_REJECTED"


def _manual_digest(payload: bytes) -> str:
    name = OUTPUT_NAME.encode("utf-8")
    digest = hashlib.sha256()
    digest.update(b"COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_ADAPTER_V1\0")
    digest.update(len(name).to_bytes(8, "big"))
    digest.update(name)
    digest.update(len(payload).to_bytes(8, "big"))
    digest.update(payload)
    return digest.hexdigest()


def test_public_api_is_unique_keyword_only_and_silent_import() -> None:
    assert adapter.__all__ == ("build_covapie_current11_task2_batch_index_remap_adapter_v1",)
    signature = inspect.signature(adapter.build_covapie_current11_task2_batch_index_remap_adapter_v1)
    assert list(signature.parameters) == ["repo_root", "state_root", "adapter_input"]
    assert all(value.kind is inspect.Parameter.KEYWORD_ONLY for value in signature.parameters.values())
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(REPO / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    process = subprocess.run(
        [sys.executable, "-c", "import covalent_ext.covapie_current11_task2_batch_index_remap_adapter_v1"],
        cwd=REPO,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert process.returncode == 0 and process.stdout == b"" and process.stderr == b""


def test_module_imports_are_stdlib_or_local_and_no_runtime_hooks() -> None:
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert imports <= {
        "__future__",
        "copy",
        "csv",
        "hashlib",
        "io",
        "json",
        "os",
        "stat",
        "contextlib",
        "pathlib",
        "typing",
        "covalent_ext",
    }
    text = MODULE.read_text(encoding="utf-8").lower()
    for forbidden in ("import torch", "import numpy", "import rdkit", "openbabel"):
        assert forbidden not in text
    assert "subprocess" not in imports
    assert "_evaluate_reference_case(" not in text


def test_exact4_file_contract() -> None:
    for path in EXACT4:
        metadata = path.lstat()
        payload = path.read_bytes()
        assert path.is_file() and not path.is_symlink()
        assert metadata.st_mode & 0o777 == 0o644
        assert len(payload) < 1024 * 1024
        assert not payload.startswith(b"\xef\xbb\xbf")
        assert b"\0" not in payload and b"\r" not in payload
        assert payload.endswith(b"\n") and not payload.endswith(b"\n\n")
        assert all(not line.endswith((b" ", b"\t")) for line in payload.splitlines())


def test_canonical_exact18_exact2_and_input_immutability(canonical_input: dict[str, object]) -> None:
    value = copy.deepcopy(canonical_input)
    before = copy.deepcopy(value)
    first, output, report = _build(value)
    second, _, _ = _build(value)
    assert len(value) == 18 and tuple(value) == adapter._INPUT_FIELD_ORDER
    assert value == before
    assert type(first) is dict and tuple(first) == (OUTPUT_NAME, REPORT_NAME)
    assert type(first[OUTPUT_NAME]) is bytes and type(first[REPORT_NAME]) is bytes
    assert first == second
    assert [sample["source_sample_index"] for sample in value["source_sample_order"]] == list(range(11))
    assert all(type(sample["source_sample_index"]) is int for sample in value["source_sample_order"])
    assert output["remap_status"] == "REMAPPED_EXACT"
    assert report["adapter_status"] == "PASS_IN_MEMORY_TASK2_BATCH_INDEX_REMAP_ONLY"


def test_canonical_remap_values(canonical_input: dict[str, object]) -> None:
    artifacts, output, report = _build(copy.deepcopy(canonical_input))
    assert len(artifacts[OUTPUT_NAME]) == 7872
    assert artifacts[OUTPUT_NAME].count(b"\n") == 416
    assert hashlib.sha256(artifacts[OUTPUT_NAME]).hexdigest() == "af21df0f1686bc898ae51d57c5dcfaf9f2d3c4488906ef241f7c98fdb04a9a3c"
    assert len(artifacts[REPORT_NAME]) == 2505
    assert artifacts[REPORT_NAME].count(b"\n") == 61
    assert hashlib.sha256(artifacts[REPORT_NAME]).hexdigest() == "1af588f06e58316077c43c331306d338a121d14a3fa17038a682114729ad78f4"
    assert set(output) == set(adapter._OUTPUT_FIELD_ORDER) and len(output) == 17
    assert output["pair_values_source_row_indices"] == [list(pair) for pair in adapter._SOURCE_PAIRS]
    assert output["pair_values_parser_local_indices"] == [
        [49, 3], [15, 3], [12, 3], [33, 3], [31, 27], [50, 21],
        [48, 16], [53, 20], [52, 21], [53, 18], [84, 5],
    ]
    assert output["pair_values_batch_indices"] == [
        [49, 3], [81, 16], [182, 29], [299, 42], [505, 91], [712, 113],
        [988, 151], [1260, 197], [1516, 240], [1766, 280], [2058, 307],
    ]
    assert output["pair_values_joint_global_indices"] == [
        [372, 3], [404, 16], [505, 29], [622, 42], [828, 91], [1035, 113],
        [1311, 151], [1583, 197], [1839, 240], [2089, 280], [2381, 307],
    ]
    assert output["pair_sample_indices"] == list(range(11))
    assert output["sample_pair_offsets"] == list(range(12))
    assert output["entry_validity"] == [True] * 11
    assert output["sample_validity"] == [True] * 11
    assert {row["status"] for row in output["source_entry_outcomes"]} == {"REMAPPED_EXACT"}
    assert output["failure_reason"] == "NONE"
    assert report["remap_output_digest"] == _manual_digest(artifacts[OUTPUT_NAME])
    assert report["remap_output_digest"] == "7e141fadc5a39bbad17e33eceb24f67efeff15d8057d785c56eebe940ff5a658"


@pytest.mark.parametrize(
    ("order", "expected_pairs", "expected_not_in_batch"),
    [
        (list(reversed(range(11))), 11, 0),
        ([10, 4, 0, 7, 2], 5, 6),
        ([10, 4, 0], 3, 8),
    ],
)
def test_permutation_mixed_and_subset(
    canonical_input: dict[str, object],
    order: list[int],
    expected_pairs: int,
    expected_not_in_batch: int,
) -> None:
    value = _ordered(canonical_input, order)
    _, output, report = _build(value)
    assert output["remap_status"] == "REMAPPED_EXACT"
    assert len(output["pair_values_source_row_indices"]) == expected_pairs
    assert output["pair_sample_indices"] == list(range(expected_pairs))
    assert output["sample_pair_offsets"] == list(range(expected_pairs + 1))
    assert sum(row["status"] == "NOT_IN_BATCH" for row in output["source_entry_outcomes"]) == expected_not_in_batch
    assert report["batch_pair_count"] == expected_pairs


def test_shuffle_recomputes_offsets_and_keeps_local_indices(canonical_input: dict[str, object]) -> None:
    value = _ordered(canonical_input, [10, 4, 0, 7, 2])
    _, output, _ = _build(value)
    assert output["pair_values_parser_local_indices"] == [
        [84, 5], [31, 27], [49, 3], [53, 20], [12, 3]
    ]
    assert output["pair_values_batch_indices"] == [
        [84, 5], [259, 48], [465, 52], [535, 82], [751, 107]
    ]
    assert output["pair_sample_indices"] == [0, 1, 2, 3, 4]


def test_no_joint_preserves_segment_success(canonical_input: dict[str, object]) -> None:
    value = copy.deepcopy(canonical_input)
    value["joint_layout_descriptor"] = None
    _, output, report = _build(value)
    assert output["remap_status"] == "REMAPPED_EXACT"
    assert output["pair_values_joint_global_indices"] is None
    assert output["provenance"]["joint_index_status"] == "JOINT_INDEX_SPACE_UNAVAILABLE"
    assert report["joint_index_status"] == "JOINT_INDEX_SPACE_UNAVAILABLE"


def test_exact15_absent_joint_and_debug_do_not_select(canonical_input: dict[str, object]) -> None:
    canonical_artifacts, canonical_output, _ = _build(copy.deepcopy(canonical_input))
    value = copy.deepcopy(canonical_input)
    for field in adapter._INPUT_FIELD_ORDER[15:]:
        del value[field]
    artifacts, output, report = _build(value)
    assert len(value) == 15
    assert output["remap_status"] == "REMAPPED_EXACT"
    assert output["pair_values_joint_global_indices"] is None
    assert report["input_optional_field_count"] == 0
    debug = copy.deepcopy(canonical_input)
    debug["debug_coordinates"] = {"arbitrary": [999.0, -999.0]}
    debug["debug_rank_metadata"] = {"rank": 12345}
    debug_artifacts, debug_output, _ = _build(debug)
    assert debug_output == canonical_output
    assert debug_artifacts[OUTPUT_NAME] == canonical_artifacts[OUTPUT_NAME]
    invalid_debug = copy.deepcopy(canonical_input)
    invalid_debug["debug_coordinates"] = []
    _, rejected, _ = _build(invalid_debug)
    assert rejected["remap_status"] == "SCHEMA_VERSION_MISMATCH"


def test_complete_non_source_sample_has_zero_pairs(canonical_input: dict[str, object]) -> None:
    value = _non_source_only(canonical_input)
    _, output, _ = _build(value)
    assert output["remap_status"] == "REMAPPED_EXACT"
    assert output["pair_values_source_row_indices"] == []
    assert output["sample_pair_offsets"] == [0, 0]
    assert output["sample_validity"] == [True]
    assert [row["status"] for row in output["source_entry_outcomes"]] == ["NOT_IN_BATCH"] * 11


@pytest.mark.parametrize("role", ("pocket", "ligand"))
@pytest.mark.parametrize("kind", ("bool", "float"))
def test_membership_requires_exact_int64_ordinals(
    canonical_input: dict[str, object], role: str, kind: str
) -> None:
    value = copy.deepcopy(canonical_input)
    original = value["batch_membership_masks"][role]
    if kind == "bool":
        value["batch_membership_masks"][role] = [bool(item) for item in original]
    else:
        value["batch_membership_masks"][role] = [float(item) for item in original]
    _assert_contract_rejection(value, "COLLATE_LENGTH_MISMATCH")


@pytest.mark.parametrize("role", ("pocket", "ligand"))
@pytest.mark.parametrize("kind", ("float", "bool", "wrong_type", "wrong_length"))
def test_offsets_require_exact_nonnegative_int_prefix_sum(
    canonical_input: dict[str, object], role: str, kind: str
) -> None:
    value = copy.deepcopy(canonical_input)
    original = value["batch_role_offsets"][role]
    if kind == "float":
        value["batch_role_offsets"][role] = [float(item) for item in original]
    elif kind == "bool":
        value["batch_role_offsets"][role] = [False, *original[1:]]
    elif kind == "wrong_type":
        value["batch_role_offsets"][role][1] = "1"
    else:
        value["batch_role_offsets"][role] = original[:-1]
    _assert_contract_rejection(value, "COLLATE_OFFSET_MISSING")


@pytest.mark.parametrize("role", ("pocket", "ligand"))
@pytest.mark.parametrize("kind", ("bool", "float", "negative", "wrong_length"))
def test_lengths_require_exact_nonnegative_int_values(
    canonical_input: dict[str, object], role: str, kind: str
) -> None:
    value = copy.deepcopy(canonical_input)
    if kind == "bool":
        value["batch_role_lengths"][role][0] = True
    elif kind == "float":
        value["batch_role_lengths"][role][0] = float(value["batch_role_lengths"][role][0])
    elif kind == "negative":
        value["batch_role_lengths"][role][0] = -1
    else:
        value["batch_role_lengths"][role] = value["batch_role_lengths"][role][:-1]
    _assert_contract_rejection(value, "COLLATE_LENGTH_MISMATCH")


@pytest.mark.parametrize("relative", ("../escape.csv", "/tmp/escape.csv", "a/../b.csv"))
def test_non_source_relative_path_must_be_safe(
    canonical_input: dict[str, object], relative: str
) -> None:
    value = _non_source_only(canonical_input)
    value["batch_sample_atom_identity_tables"][0]["roles"]["pocket"]["relative_path"] = relative
    _assert_contract_rejection(value, "SOURCE_TABLE_IDENTITY_MISMATCH")


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("selected_source_row_index_0based", "row_count"),
        ("selected_source_row_index_0based", -1),
        ("selected_parser_local_index", "parser_output_atom_count"),
        ("selected_parser_local_index", -1),
    ),
)
def test_non_source_selected_indices_are_in_bounds(
    canonical_input: dict[str, object], field: str, replacement: object
) -> None:
    value = _non_source_only(canonical_input)
    role = value["batch_sample_atom_identity_tables"][0]["roles"]["pocket"]
    role[field] = role[replacement] if type(replacement) is str else replacement
    _assert_contract_rejection(value, "SOURCE_TABLE_IDENTITY_MISMATCH")


@pytest.mark.parametrize(
    ("kind", "status"),
    (
        ("missing", "PARSER_ATOM_NOT_FOUND"),
        ("list", "PARSER_ATOM_NOT_UNIQUE"),
        ("bool", "SOURCE_TABLE_IDENTITY_MISMATCH"),
        ("float", "SOURCE_TABLE_IDENTITY_MISMATCH"),
        ("different", "SOURCE_TABLE_IDENTITY_MISMATCH"),
    ),
)
def test_non_source_selected_mapping_is_exact(
    canonical_input: dict[str, object], kind: str, status: str
) -> None:
    value = _non_source_only(canonical_input)
    role = value["batch_sample_atom_identity_tables"][0]["roles"]["pocket"]
    key = str(role["selected_source_row_index_0based"])
    if kind == "missing":
        del role["source_to_parser_local"][key]
    elif kind == "list":
        role["source_to_parser_local"][key] = [role["selected_parser_local_index"]]
    elif kind == "bool":
        role["source_to_parser_local"][key] = True
    elif kind == "float":
        role["source_to_parser_local"][key] = float(role["selected_parser_local_index"])
    else:
        role["source_to_parser_local"][key] = role["selected_parser_local_index"] + 1
    _assert_contract_rejection(value, status)


@pytest.mark.parametrize(
    ("kind", "field", "replacement"),
    (
        ("empty", "atom_name", ""),
        ("whitespace", "type_symbol", " C "),
        ("missing", "auth_asym_id", None),
        ("non_string", "label_seq_id", 7),
        ("label_whitespace", "label_seq_id", " 7 "),
    ),
)
def test_non_source_atom_identity_exact8_strings(
    canonical_input: dict[str, object], kind: str, field: str, replacement: object
) -> None:
    value = _non_source_only(canonical_input)
    atom = value["batch_sample_atom_identity_tables"][0]["roles"]["pocket"]["selected_atom_identity"]
    if kind == "missing":
        del atom[field]
    else:
        atom[field] = replacement
    _assert_contract_rejection(value, "SOURCE_ATOM_IDENTITY_MISMATCH")


@pytest.mark.parametrize(
    ("mutation", "status"),
    [
        (lambda value: value.update(schema_version="wrong"), "SCHEMA_VERSION_MISMATCH"),
        (lambda value: value.update(source_projection_digest="0" * 64), "SCHEMA_VERSION_MISMATCH"),
        (lambda value: value.update(source_payload_digest="0" * 64), "SCHEMA_VERSION_MISMATCH"),
        (lambda value: value.update(parser_schema_version="wrong"), "SCHEMA_VERSION_MISMATCH"),
        (lambda value: value.update(collate_schema_version="wrong"), "SCHEMA_VERSION_MISMATCH"),
        (lambda value: value.update(joint_layout_descriptor="unknown"), "SCHEMA_VERSION_MISMATCH"),
        (lambda value: value["source_entry_validity_bool"].__setitem__(0, False), "ENTRY_INVALID"),
        (lambda value: value["source_pair_values_int64"].__setitem__(0, [-1, 3]), "SOURCE_ROW_OUT_OF_RANGE"),
        (lambda value: value["source_pair_values_int64"].__setitem__(0, [999, 3]), "SOURCE_ROW_OUT_OF_RANGE"),
    ],
)
def test_lineage_source_and_joint_fail_closed(
    canonical_input: dict[str, object], mutation: object, status: str
) -> None:
    value = copy.deepcopy(canonical_input)
    mutation(value)
    first, output, report = _build(value)
    second, _, _ = _build(value)
    assert first == second
    assert output["remap_status"] == status and output["failure_reason"] == status
    assert output["pair_values_source_row_indices"] == []
    assert output["pair_values_joint_global_indices"] is None
    assert report["adapter_status"] == "FAIL_CLOSED_INPUT_REJECTED"
    assert report["readiness"]["public_batch_index_remap_adapter_passed"] is False


@pytest.mark.parametrize("field", list(adapter._INPUT_FIELD_ORDER[:15]))
def test_missing_required_field_is_contract_rejection(
    canonical_input: dict[str, object], field: str
) -> None:
    value = copy.deepcopy(canonical_input)
    del value[field]
    _, output, report = _build(value)
    assert output["remap_status"] == "SCHEMA_VERSION_MISMATCH"
    assert report["adapter_status"] == "FAIL_CLOSED_INPUT_REJECTED"


@pytest.mark.parametrize("alias", list(adapter._LEGACY_ALIASES))
def test_legacy_alias_is_rejected(canonical_input: dict[str, object], alias: str) -> None:
    value = copy.deepcopy(canonical_input)
    value[alias] = []
    _, output, _ = _build(value)
    assert output["remap_status"] == "SCHEMA_VERSION_MISMATCH"


def test_unknown_nineteenth_field_is_rejected(canonical_input: dict[str, object]) -> None:
    value = copy.deepcopy(canonical_input)
    value["unknown_field"] = None
    _, output, _ = _build(value)
    assert output["remap_status"] == "SCHEMA_VERSION_MISMATCH"


@pytest.mark.parametrize("bad", [[], {"value": float("nan")}, {"value": float("inf")}, {"value": object()}])
def test_non_dict_or_non_json_input_raises_value_error(bad: object) -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        adapter.build_covapie_current11_task2_batch_index_remap_adapter_v1(
            repo_root=REPO, state_root=STATE, adapter_input=bad
        )


def test_batch_duplicate_and_malformed_identity(canonical_input: dict[str, object]) -> None:
    duplicate = copy.deepcopy(canonical_input)
    duplicate["batch_sample_order"][1] = copy.deepcopy(duplicate["batch_sample_order"][0])
    duplicate["batch_sample_atom_identity_tables"][1]["sample_identity"] = copy.deepcopy(
        duplicate["batch_sample_order"][0]
    )
    _, output, _ = _build(duplicate)
    assert output["remap_status"] == "BATCH_SAMPLE_DUPLICATED"
    malformed = copy.deepcopy(canonical_input)
    malformed["batch_sample_order"][0]["pdb_id"] = " 6BV6"
    _, output, _ = _build(malformed)
    assert output["remap_status"] == "BATCH_SAMPLE_IDENTITY_UNKNOWN"


def test_source_duplicate(canonical_input: dict[str, object]) -> None:
    value = copy.deepcopy(canonical_input)
    value["source_sample_order"][1] = copy.deepcopy(value["source_sample_order"][0])
    _, output, _ = _build(value)
    assert output["remap_status"] == "SOURCE_SAMPLE_DUPLICATED"


@pytest.mark.parametrize(("ordinal", "replacement"), ((0, False), (1, True)))
def test_source_sample_index_bool_cannot_impersonate_int(
    canonical_input: dict[str, object], ordinal: int, replacement: bool
) -> None:
    value = copy.deepcopy(canonical_input)
    value["source_sample_order"][ordinal]["source_sample_index"] = replacement
    _assert_contract_rejection(value, "SOURCE_TABLE_IDENTITY_MISMATCH")


@pytest.mark.parametrize(("ordinal", "replacement"), ((0, 0.0), (1, 1.0), (2, 2.0)))
def test_source_sample_index_float_cannot_impersonate_int(
    canonical_input: dict[str, object], ordinal: int, replacement: float
) -> None:
    value = copy.deepcopy(canonical_input)
    value["source_sample_order"][ordinal]["source_sample_index"] = replacement
    _assert_contract_rejection(value, "SOURCE_TABLE_IDENTITY_MISMATCH")


@pytest.mark.parametrize(
    "mutation",
    (
        "missing_index",
        "string_index",
        "negative_index",
        "wrong_nonnegative_index",
        "unknown_field",
        "missing_identity_field",
    ),
)
def test_source_sample_record_requires_exact_keys_types_and_values(
    canonical_input: dict[str, object], mutation: str
) -> None:
    value = copy.deepcopy(canonical_input)
    record = value["source_sample_order"][0]
    if mutation == "missing_index":
        del record["source_sample_index"]
    elif mutation == "string_index":
        record["source_sample_index"] = "0"
    elif mutation == "negative_index":
        record["source_sample_index"] = -1
    elif mutation == "wrong_nonnegative_index":
        record["source_sample_index"] = 10
    elif mutation == "unknown_field":
        record["unknown_field"] = "unexpected"
    else:
        del record["ligand_comp_id"]
    _assert_contract_rejection(value, "SOURCE_TABLE_IDENTITY_MISMATCH")


@pytest.mark.parametrize(
    ("mutate", "status"),
    [
        (lambda role: role.update(SHA256="0" * 64, row_order_digest="0" * 64), "SOURCE_TABLE_IDENTITY_MISMATCH"),
        (lambda role: role.update(relative_path="wrong/table.csv"), "SOURCE_TABLE_IDENTITY_MISMATCH"),
        (lambda role: role.update(row_count=999), "SOURCE_TABLE_IDENTITY_MISMATCH"),
        (lambda role: role.update(row_order_version="wrong"), "SOURCE_TABLE_IDENTITY_MISMATCH"),
        (lambda role: role.update(selected_parser_local_index=0), "SOURCE_TABLE_IDENTITY_MISMATCH"),
        (lambda role: role["selected_atom_identity"].update(atom_name="WRONG"), "SOURCE_ATOM_IDENTITY_MISMATCH"),
        (lambda role: role["selected_atom_identity"].pop("label_seq_id"), "SOURCE_ATOM_IDENTITY_MISMATCH"),
        (lambda role: role["selected_atom_identity"].update(label_seq_id="changed"), "SOURCE_ATOM_IDENTITY_MISMATCH"),
        (lambda role: role.update(parser_output_atom_count=999), "PARSER_COUNT_MISMATCH"),
        (lambda role: role.update(source_to_parser_local={}), "PARSER_ATOM_NOT_FOUND"),
        (lambda role: role.update(source_to_parser_local={"88": [49, 50]}), "PARSER_ATOM_NOT_UNIQUE"),
    ],
)
def test_authority_fail_closed(
    canonical_input: dict[str, object], mutate: object, status: str
) -> None:
    value = copy.deepcopy(canonical_input)
    mutate(value["batch_sample_atom_identity_tables"][0]["roles"]["pocket"])
    _, output, _ = _build(value)
    assert output["remap_status"] == status


def test_role_offsets_and_membership_fail_closed(canonical_input: dict[str, object]) -> None:
    role_swap = copy.deepcopy(canonical_input)
    roles = role_swap["batch_sample_atom_identity_tables"][0]["roles"]
    roles["pocket"], roles["ligand"] = roles["ligand"], roles["pocket"]
    _, output, _ = _build(role_swap)
    assert output["remap_status"] == "ROLE_MISMATCH"
    offset = copy.deepcopy(canonical_input)
    offset["batch_role_offsets"]["pocket"][1] += 1
    _, output, _ = _build(offset)
    assert output["remap_status"] == "COLLATE_OFFSET_MISSING"
    membership = copy.deepcopy(canonical_input)
    membership["batch_membership_masks"]["ligand"][0] = 1
    _, output, _ = _build(membership)
    assert output["remap_status"] == "COLLATE_LENGTH_MISMATCH"


def _synthetic_p_gt_1() -> tuple[dict[str, object], list[dict[str, object]]]:
    identities = [
        {
            "source_sample_index": index,
            "sample_index_row_id": f"S{index}",
            "sample_preparation_input_id": f"P{index}",
            "pdb_id": f"X{index}",
            "ligand_comp_id": f"L{index}",
        }
        for index in range(2)
    ]
    authority = []
    for index, identity in enumerate(identities):
        roles = {}
        for role in ("pocket", "ligand"):
            digest = hashlib.sha256(f"{index}:{role}".encode()).hexdigest()
            roles[role] = {
                "role": role,
                "root_kind": "repo_root",
                "relative_path": f"synthetic/S{index}/{role}.csv",
                "SHA256": digest,
                "row_count": 2,
                "row_order_digest": digest,
                "row_order_version": "physical_csv_data_row_order_v1",
                "selected_source_row_index_0based": 0,
                "selected_parser_local_index": 0,
                "parser_output_atom_count": 2,
                "selected_atom_identity": {
                    "atom_site_id": f"{index}-{role}",
                    "atom_name": "C0",
                    "type_symbol": "C",
                    "residue_name_or_ligand_comp_id": f"R{index}",
                    "auth_asym_id": "A",
                    "auth_seq_id": str(index),
                    "label_asym_id": "A",
                    "label_seq_id": "",
                },
                "source_to_parser_local": {"0": 0, "1": 1},
            }
        authority.append({"sample_identity": copy.deepcopy(identity), "roles": roles})
    order = [1, 0]
    case = {
        "source_sample_order": identities,
        "source_pair_values_int64": [[0, 0], [1, 1], [0, 0]],
        "source_sample_offsets_int64": [0, 2, 3],
        "source_entry_validity_bool": [True, True, True],
        "source_sample_validity_bool": [True, True],
        "batch_sample_order": [copy.deepcopy(identities[index]) for index in order],
        "batch_sample_atom_identity_tables": [copy.deepcopy(authority[index]) for index in order],
        "batch_role_lengths": {"pocket": [2, 2], "ligand": [2, 2]},
        "batch_role_offsets": {"pocket": [0, 2, 4], "ligand": [0, 2, 4]},
        "batch_membership_masks": {"pocket": [0, 0, 1, 1], "ligand": [0, 0, 1, 1]},
        "joint_layout_descriptor": adapter._JOINT_LAYOUT,
    }
    return case, authority


def test_private_engine_p_gt_1_zero_and_negative_boundaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case, authority = _synthetic_p_gt_1()
    output = adapter._remap_engine(case, authoritative_tables=authority)
    assert output["sample_pair_offsets"] == [0, 1, 3]
    assert output["pair_values_source_row_indices"] == [[0, 0], [0, 0], [1, 1]]
    assert output["pair_values_parser_local_indices"] == [[0, 0], [0, 0], [1, 1]]
    assert output["pair_values_batch_indices"] == [[0, 0], [2, 2], [3, 3]]
    assert output["pair_values_joint_global_indices"] == [[4, 0], [6, 2], [7, 3]]
    bad = copy.deepcopy(case)
    bad["source_pair_values_int64"][0] = [-1, 0]
    with pytest.raises(adapter._InputFailure) as captured:
        adapter._remap_engine(bad, authoritative_tables=authority)
    assert captured.value.status == "SOURCE_ROW_OUT_OF_RANGE"
    out_of_range = copy.deepcopy(case)
    out_of_range_authority = copy.deepcopy(authority)
    table = out_of_range["batch_sample_atom_identity_tables"][1]["roles"]["pocket"]
    expected = out_of_range_authority[0]["roles"]["pocket"]
    table["selected_parser_local_index"] = 2
    table["source_to_parser_local"]["0"] = 2
    expected["selected_parser_local_index"] = 2
    expected["source_to_parser_local"]["0"] = 2
    with pytest.raises(adapter._InputFailure) as captured:
        adapter._remap_engine(out_of_range, authoritative_tables=out_of_range_authority)
    assert captured.value.status == "SOURCE_TABLE_IDENTITY_MISMATCH"
    monkeypatch.setattr(
        adapter,
        "_validate_role_structure",
        lambda role_table, _expected_role: role_table,
    )
    with pytest.raises(adapter._InputFailure) as captured:
        adapter._remap_engine(out_of_range, authoritative_tables=out_of_range_authority)
    assert captured.value.status == "BATCH_INDEX_OUT_OF_RANGE"


def test_private_gate_evaluator_is_never_called(
    monkeypatch: pytest.MonkeyPatch, canonical_input: dict[str, object]
) -> None:
    monkeypatch.setattr(
        adapter._contract_gate,
        "_evaluate_reference_case",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("called")),
    )
    _, output, _ = _build(copy.deepcopy(canonical_input))
    assert output["remap_status"] == "REMAPPED_EXACT"


def test_gate_api_called_exactly_twice(
    monkeypatch: pytest.MonkeyPatch,
    contract_exact6: dict[str, bytes],
    canonical_input: dict[str, object],
) -> None:
    calls = []

    def build(**kwargs: object) -> dict[str, bytes]:
        calls.append(kwargs)
        return copy.deepcopy(contract_exact6)

    monkeypatch.setattr(
        adapter._contract_gate,
        "build_covapie_current11_task2_batch_index_remap_contract_gate_v1",
        build,
    )
    _build(copy.deepcopy(canonical_input))
    assert len(calls) == 2
    assert all(call == {"repo_root": REPO, "state_root": STATE} for call in calls)


def test_compatibility_filter_is_exact_and_restores(monkeypatch: pytest.MonkeyPatch) -> None:
    original = adapter._projection_contract_gate._run_git
    exact = "\n".join(f"?? {path}" for path in adapter._REPOSITORY_EXACT4)
    extra = "?? unexpected-fifth-file.txt"
    monkeypatch.setattr(
        adapter._projection_contract_gate,
        "_run_git",
        lambda _root, _args: exact + "\n" + extra,
    )
    fake = adapter._projection_contract_gate._run_git
    with adapter._gate_status_compatibility():
        assert adapter._projection_contract_gate._run_git(REPO, ("status", "--porcelain=v1", "--untracked-files=all")) == extra
    assert adapter._projection_contract_gate._run_git is fake
    monkeypatch.setattr(
        adapter._projection_contract_gate,
        "_run_git",
        lambda _root, _args: " M " + adapter._REPOSITORY_EXACT4[0],
    )
    fake = adapter._projection_contract_gate._run_git
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        with adapter._gate_status_compatibility():
            adapter._projection_contract_gate._run_git(REPO, ("status", "--porcelain=v1", "--untracked-files=all"))
    assert adapter._projection_contract_gate._run_git is fake
    monkeypatch.setattr(adapter._projection_contract_gate, "_run_git", original)


def test_git_and_formal_snapshots_unchanged(canonical_input: dict[str, object]) -> None:
    canonical = STATE / adapter._FORMAL_RELATIVE
    status_before = _git_status()
    formal_before = adapter._formal_snapshot(canonical)
    _build(copy.deepcopy(canonical_input))
    assert _git_status() == status_before
    assert adapter._formal_snapshot(canonical) == formal_before
    lines = status_before.decode().splitlines()
    assert lines == [] or set(lines) == {f"?? {path.relative_to(REPO).as_posix()}" for path in EXACT4}


def test_output_and_report_safety_readiness(canonical_input: dict[str, object]) -> None:
    artifacts, output, report = _build(copy.deepcopy(canonical_input))
    for payload in artifacts.values():
        assert len(payload) < 1024 * 1024
        assert payload.endswith(b"\n") and not payload.endswith(b"\n\n")
        assert b"\0" not in payload and b"\r" not in payload and not payload.startswith(b"\xef\xbb\xbf")
    stable_text = artifacts[OUTPUT_NAME].decode()
    for forbidden in (str(REPO), str(STATE), "origin/main", "ahead", "behind", '"HEAD"'):
        assert forbidden not in stable_text
    readiness = output["readiness"]
    expected_true = {
        "public_batch_index_remap_adapter_implemented",
        "public_batch_index_remap_adapter_passed",
        "remap_output_built_in_memory",
        "canonical_reference_remap_succeeded",
        "ready_for_batch_descriptor_compiler_design",
        "feature_semantics_reaudit_required_before_training",
    }
    assert all(readiness[key] is True for key in expected_true)
    assert all(
        readiness[key] is False
        for key in (
            "formal_remap_materialized",
            "torch_tensor_materialized",
            "numpy_artifact_materialized",
            "dataloader_modified",
            "model_modified",
            "forward_modified",
            "loss_modified",
            "ready_for_dataloader_integration",
            "ready_for_model_integration",
            "ready_for_loss_integration",
            "ready_for_training",
        )
    )
    assert report["artifact_file_count"] == 2
    assert report["artifact_identities"][1]["content_identity"] == "self_excluded"
    assert report["remap_contract_exact6_double_build_identical"] is True
    assert report["formal_snapshot_unchanged"] is True


def _load_checker() -> object:
    spec = importlib.util.spec_from_file_location("adapter_checker_v1", CHECKER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_checker_success_compact_report_only(
    monkeypatch: pytest.MonkeyPatch, canonical_input: dict[str, object]
) -> None:
    checker = _load_checker()
    artifacts, _, _ = _build(copy.deepcopy(canonical_input))
    monkeypatch.setattr(adapter, "_build_canonical_adapter_input_v1", lambda **_kwargs: copy.deepcopy(canonical_input))
    monkeypatch.setattr(
        adapter,
        "build_covapie_current11_task2_batch_index_remap_adapter_v1",
        lambda **_kwargs: copy.deepcopy(artifacts),
    )
    assert checker.main(["--repo-root", str(REPO), "--state-root", str(STATE)]) == 0


@pytest.mark.parametrize(
    "arguments",
    [
        [], ["-h"], ["--help"], ["--repo-root", str(REPO)],
        ["--state-root", str(STATE)], ["--output", "x"], ["--output-dir", "x"],
        ["--write"], ["--materialize"], ["--remap-input", "x"], ["--batch-file", "x"],
        ["--json"], ["--torch"], ["--numpy"], ["--dataloader"], ["--model"],
        ["--forward"], ["--head"], ["--loss"], ["--train"],
        ["--schema-override", "x"], ["--status-override", "x"], ["extra"],
    ],
)
def test_checker_rejects_forbidden_cli(arguments: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    checker = _load_checker()
    assert checker.main(arguments) == 1
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ERROR + "\n"
