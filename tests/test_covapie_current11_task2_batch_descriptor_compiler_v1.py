from __future__ import annotations

import ast
import copy
import importlib
import inspect
import json
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Sequence

import pytest

from covalent_ext import covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1 as contract_gate
from covalent_ext import covapie_current11_task2_batch_descriptor_compiler_v1 as compiler
from covalent_ext import covapie_current11_task2_batch_index_remap_adapter_v1 as adapter


REPO = Path(__file__).resolve().parents[1]
STATE = REPO.parent / "covapie-state"
ERROR = "COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_V1_ERROR"
VECTORS = "current11_task2_batch_descriptor_compiler_reference_vectors.json"
OUTPUT_FIELDS = (
    "schema_version", "compiler_status", "failure_reason", "adapter_input_exact18",
    "batch_sample_key_outcomes", "source_contract_digest", "identity_provider_digest",
    "runtime_schema_binding", "provenance", "readiness",
)
EXACT18_FIELDS = (
    "schema_version", "source_projection_digest", "source_payload_digest",
    "parser_schema_version", "collate_schema_version", "source_sample_order",
    "source_pair_values_int64", "source_sample_offsets_int64",
    "source_entry_validity_bool", "source_sample_validity_bool", "batch_sample_order",
    "batch_sample_atom_identity_tables", "batch_role_lengths", "batch_role_offsets",
    "batch_membership_masks", "joint_layout_descriptor", "debug_coordinates",
    "debug_rank_metadata",
)
JOINT = "ligand_segment_then_pocket_segment_v1"
EXACT4 = (
    "src/covalent_ext/covapie_current11_task2_batch_descriptor_compiler_v1.py",
    "scripts/check_covapie_current11_task2_batch_descriptor_compiler_v1.py",
    "tests/test_covapie_current11_task2_batch_descriptor_compiler_v1.py",
    "docs/covapie_current11_task2_batch_descriptor_compiler_v1_guide.md",
)


@pytest.fixture(scope="session")
def exact6() -> dict[str, bytes]:
    with compiler._precommit_compatibility():
        return contract_gate.build_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1(
            repo_root=REPO, state_root=STATE,
        )


@pytest.fixture(scope="session")
def vectors(exact6: dict[str, bytes]) -> dict[str, object]:
    return json.loads(exact6[VECTORS].decode("utf-8"))


@pytest.fixture()
def pinned_gate(monkeypatch: pytest.MonkeyPatch, exact6: dict[str, bytes]) -> list[int]:
    calls: list[int] = []

    def build(*, repo_root: Path, state_root: Path) -> dict[str, bytes]:
        assert repo_root == REPO and state_root == STATE
        calls.append(1)
        return copy.deepcopy(exact6)

    monkeypatch.setattr(contract_gate, "build_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1", build)
    return calls


def _membership(lengths: Sequence[int]) -> list[int]:
    return [ordinal for ordinal, length in enumerate(lengths) for _ in range(length)]


def _observation(base: dict[str, object], order: Sequence[int], joint: str | None = JOINT) -> dict[str, object]:
    ligand = [base["ligand_lengths"][index] for index in order]
    pocket = [base["pocket_lengths"][index] for index in order]
    return {
        "schema_version": base["schema_version"],
        "runtime_batch_schema_version": base["runtime_batch_schema_version"],
        "sample_key_schema_version": base["sample_key_schema_version"],
        "batch_sample_keys": [base["batch_sample_keys"][index] for index in order],
        "ligand_lengths": ligand,
        "pocket_lengths": pocket,
        "ligand_membership": _membership(ligand),
        "pocket_membership": _membership(pocket),
        "joint_layout_descriptor": joint,
        "virtual_node_policy": base["virtual_node_policy"],
        "receptors": [base["receptors"][index] for index in order],
        "consistency_buffer_lengths": {
            "ligand_coords": sum(ligand), "ligand_one_hot": sum(ligand),
            "pocket_coords": sum(pocket), "pocket_one_hot": sum(pocket),
        },
        "debug_coordinates": None,
        "debug_rank_metadata": None,
    }


def _compile(observation: object) -> dict[str, object]:
    return compiler.compile_covapie_current11_task2_batch_descriptor_v1(
        repo_root=REPO, state_root=STATE, observation=observation,
    )


def _by_id(vectors: dict[str, object]) -> dict[str, dict[str, object]]:
    return {row["case_id"]: row for row in vectors["reference_cases"]}


def _normalize_expected(output: dict[str, object]) -> dict[str, object]:
    result = {field: copy.deepcopy(output[field]) for field in OUTPUT_FIELDS}
    if type(result["adapter_input_exact18"]) is dict:
        raw_exact18 = result["adapter_input_exact18"]
        result["adapter_input_exact18"] = {
            field: raw_exact18[field] for field in EXACT18_FIELDS
        }
    result["provenance"] = {
        "contract_evaluator_only": False,
        "compiler_implemented": True,
        "runtime_extractor_implemented": False,
        "remap_executed_by_compiler": False,
        "compiler_contract_commit": "3b390cec784ed73a72f522145b6f26e3d8af704d",
        "compiler_contract_digest": "bb9705173523377f28966064eec7393fbf337dce9ef6c70d2e3fbca3038e2dfd",
    }
    result["readiness"]["task2_batch_descriptor_compiler_implemented"] = True
    result["readiness"]["ready_for_task2_batch_descriptor_compiler_implementation"] = False
    return result


def _mutated(base: dict[str, object], field: str, value: object) -> dict[str, object]:
    result = copy.deepcopy(base)
    if value is _MISSING:
        result.pop(field, None)
    else:
        result[field] = value
    return result


_MISSING = object()


def _observable_failure_cases(base11: dict[str, object]) -> dict[str, dict[str, object]]:
    base = _observation(base11, [10, 4, 0])
    cases = {
        "duplicate_runtime_key": _mutated(base, "batch_sample_keys", [base11["batch_sample_keys"][10]] * 3),
        "unknown_runtime_key": _mutated(base, "batch_sample_keys", ["TOTALLY_UNKNOWN"]),
        "non_source_known_sample": _mutated(base, "batch_sample_keys", ["CYS_SG_SAMPLE_INDEX_999999"]),
        "invalid_key_type": _mutated(base, "batch_sample_keys", [1]),
        "empty_key": _mutated(base, "batch_sample_keys", [""]),
        "untrimmed_key": _mutated(base, "batch_sample_keys", [" CYS_SG_SAMPLE_INDEX_000011"]),
        "wrong_runtime_schema": _mutated(base, "runtime_batch_schema_version", "drift"),
        "wrong_sample_key_schema": _mutated(base, "sample_key_schema_version", "drift"),
        "virtual_policy_mismatch": _mutated(base, "virtual_node_policy", "virtual_nodes_v1"),
        "wrong_ligand_length": _mutated(base, "ligand_lengths", [22, 28, 13]),
        "wrong_pocket_length": _mutated(base, "pocket_lengths", [227, 188, 66]),
        "bool_length": _mutated(base, "ligand_lengths", [True, 28, 13]),
        "float_length": _mutated(base, "ligand_lengths", [21.0, 28, 13]),
        "wrong_ligand_membership": _mutated(base, "ligand_membership", []),
        "wrong_pocket_membership": _mutated(base, "pocket_membership", []),
        "bool_membership": _mutated(base, "ligand_membership", [True] + base["ligand_membership"][1:]),
        "float_membership": _mutated(base, "ligand_membership", [0.0] + base["ligand_membership"][1:]),
        "membership_wrong_ordinal_order": _mutated(base, "ligand_membership", list(reversed(base["ligand_membership"]))),
        "consistency_buffer_mismatch": _mutated(base, "consistency_buffer_lengths", {
            "ligand_coords": 0, "ligand_one_hot": 92, "pocket_coords": 482, "pocket_one_hot": 482,
        }),
        "source_contract_override": {**copy.deepcopy(base), "source_projection_digest": "x"},
        "unknown_joint_descriptor": _mutated(base, "joint_layout_descriptor", "unknown"),
        "unknown_top_level_field": {**copy.deepcopy(base), "unknown_field": 1},
        "missing_required_field": _mutated(base, "ligand_lengths", _MISSING),
        "runtime_name_path_drift": _mutated(base, "batch_sample_keys", ["path/CYS_SG_SAMPLE_INDEX_000011"]),
    }
    return cases


def test_public_api_is_single_keyword_only_symbol_and_import_is_silent() -> None:
    assert compiler.__all__ == ("compile_covapie_current11_task2_batch_descriptor_v1",)
    signature = inspect.signature(compiler.compile_covapie_current11_task2_batch_descriptor_v1)
    assert tuple(signature.parameters) == ("repo_root", "state_root", "observation")
    assert all(value.kind is inspect.Parameter.KEYWORD_ONLY for value in signature.parameters.values())
    completed = subprocess.run(
        [sys.executable, "-c", "import covalent_ext.covapie_current11_task2_batch_descriptor_compiler_v1"],
        cwd=REPO, env={**os.environ, "PYTHONPATH": "src", "PYTHONDONTWRITEBYTECODE": "1"},
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
    )
    assert completed.returncode == 0 and completed.stdout == completed.stderr == ""


def test_source_is_local_stdlib_only_read_only_and_adapter_independent() -> None:
    path = REPO / "src/covalent_ext/covapie_current11_task2_batch_descriptor_compiler_v1.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree) if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    assert not imports & {"torch", "numpy", "rdkit", "openbabel", "subprocess"}
    assert "task2_batch_index_remap_adapter_v1" not in source
    assert "_evaluate" + "_reference_case_v1" not in source
    assert not any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"write_text", "write_bytes", "unlink", "mkdir", "rename", "replace"}
        for node in ast.walk(tree)
    )


def test_gate_exact6_identity_and_frozen_contract(exact6: dict[str, bytes], vectors: dict[str, object]) -> None:
    manifest, parsed_vectors, report = compiler._validate_exact6(exact6)
    assert parsed_vectors == vectors
    assert report["contract_digest"] == "bb9705173523377f28966064eec7393fbf337dce9ef6c70d2e3fbca3038e2dfd"
    assert manifest["validation_order"] == list(compiler._VALIDATION_ORDER)
    assert [row["case_id"] for row in vectors["reference_cases"]] == list(compiler._REFERENCE_IDS)
    assert vectors["identity_provider_digest"] == compiler._PROVIDER_DIGEST


def test_each_public_call_rebuilds_gate(pinned_gate: list[int], vectors: dict[str, object]) -> None:
    base = vectors["canonical_runtime_observation"]
    assert _compile(_observation(base, []))["compiler_status"] == "COMPILED_EXACT"
    assert _compile(_observation(base, [10, 4, 0]))["compiler_status"] == "COMPILED_EXACT"
    assert len(pinned_gate) == 2


def test_success_six_exact_order_and_normalized_parity(pinned_gate: list[int], vectors: dict[str, object]) -> None:
    base = vectors["canonical_runtime_observation"]
    by_id = _by_id(vectors)
    specs = (
        ("canonical_exact11", list(range(11)), JOINT),
        ("reversed_exact11", list(reversed(range(11))), JOINT),
        ("mixed_10_4_0_7_2", [10, 4, 0, 7, 2], JOINT),
        ("subset_10_4_0", [10, 4, 0], JOINT),
        ("no_joint", list(range(11)), None),
        ("empty_batch", [], JOINT),
    )
    for case_id, order, joint in specs:
        output = _compile(_observation(base, order, joint))
        assert tuple(output) == OUTPUT_FIELDS
        assert tuple(output["adapter_input_exact18"]) == EXACT18_FIELDS
        assert list(output.items()) == list(_normalize_expected(by_id[case_id]["compiler_output"]).items())
    empty = _compile(_observation(base, []))["adapter_input_exact18"]
    assert empty["batch_role_offsets"] == {"pocket": [0], "ligand": [0]}
    no_joint = _compile(_observation(base, list(range(11)), None))
    assert no_joint["compiler_status"] == "COMPILED_EXACT"
    assert no_joint["runtime_schema_binding"]["joint_layout_component_status"] == "JOINT_LAYOUT_UNAVAILABLE"


def test_all_24_observation_hard_failures_match_reference_exactly(
    pinned_gate: list[int], vectors: dict[str, object],
) -> None:
    by_id = _by_id(vectors)
    cases = _observable_failure_cases(vectors["canonical_runtime_observation"])
    assert len(cases) == 24
    for case_id, observation in cases.items():
        output = _compile(observation)
        assert tuple(output) == OUTPUT_FIELDS
        assert output["adapter_input_exact18"] is None
        assert output["compiler_status"] == output["failure_reason"]
        assert list(output.items()) == list(_normalize_expected(by_id[case_id]["compiler_output"]).items())


def test_published_35_case_matrix_is_fully_accounted_for(vectors: dict[str, object]) -> None:
    rows = vectors["reference_cases"]
    direct = set(_observable_failure_cases(vectors["canonical_runtime_observation"])) | set(compiler._REFERENCE_IDS[:6])
    authority_only = {
        "provider_missing", "ambiguous_provider_match", "provider_digest_drift",
        "missing_pocket_role", "missing_ligand_role",
    }
    assert len(rows) == 35
    assert direct | authority_only == {row["case_id"] for row in rows}
    assert direct.isdisjoint(authority_only) and len(direct) == 30
    for row in rows:
        output = row["compiler_output"]
        assert set(output) == set(OUTPUT_FIELDS)
        assert output["compiler_status"] == row["expected_compiler_status"]
        assert (output["adapter_input_exact18"] is not None) is row["expected_exact18_present"]


@pytest.mark.parametrize("field", ["ligand_lengths", "pocket_lengths"])
@pytest.mark.parametrize("bad", [True, 1.0])
def test_bool_and_float_role_lengths_fail_closed(
    pinned_gate: list[int], vectors: dict[str, object], field: str, bad: object,
) -> None:
    observation = _observation(vectors["canonical_runtime_observation"], [10, 4, 0])
    observation[field][0] = bad
    assert _compile(observation)["compiler_status"] == "ROLE_LENGTH_MISMATCH"


@pytest.mark.parametrize("field", ["ligand_membership", "pocket_membership"])
@pytest.mark.parametrize("bad", [True, 0.0])
def test_bool_and_float_membership_fail_closed(
    pinned_gate: list[int], vectors: dict[str, object], field: str, bad: object,
) -> None:
    observation = _observation(vectors["canonical_runtime_observation"], [10, 4, 0])
    observation[field][0] = bad
    assert _compile(observation)["compiler_status"] == "MEMBERSHIP_MASK_MISMATCH"


def test_recursive_and_non_json_safe_debug_are_runtime_hard_failures(
    pinned_gate: list[int], vectors: dict[str, object],
) -> None:
    base = vectors["canonical_runtime_observation"]
    recursive: dict[str, object] = {}
    recursive["self"] = recursive
    for value in (recursive, {"bad": {1, 2}}, {1: "non-json-key"}, {"nan": float("nan")}):
        observation = _observation(base, [10])
        observation["debug_coordinates"] = value
        output = _compile(observation)
        assert output["compiler_status"] == "BATCH_OBSERVATION_SCHEMA_MISMATCH"
        assert output["adapter_input_exact18"] is None


def test_debug_is_deep_copied_and_not_identity(pinned_gate: list[int], vectors: dict[str, object]) -> None:
    observation = _observation(vectors["canonical_runtime_observation"], [10])
    observation["debug_coordinates"] = {"coords": [[1.0, 2.0, 3.0]]}
    observation["debug_rank_metadata"] = {"rank": 0}
    output = _compile(observation)
    exact18 = output["adapter_input_exact18"]
    assert exact18["debug_coordinates"] == observation["debug_coordinates"]
    assert exact18["debug_coordinates"] is not observation["debug_coordinates"]
    assert exact18["batch_sample_order"][0]["sample_index_row_id"] == "CYS_SG_SAMPLE_INDEX_000011"


def test_source_override_precedes_other_forbidden_field(
    pinned_gate: list[int], vectors: dict[str, object],
) -> None:
    observation = _observation(vectors["canonical_runtime_observation"], [10])
    observation["source_projection_digest"] = "x"
    observation["model_logits"] = []
    assert _compile(observation)["compiler_status"] == "SOURCE_CONTRACT_MISMATCH"


def test_missing_required_precedes_source_override(
    pinned_gate: list[int], vectors: dict[str, object],
) -> None:
    observation = _observation(vectors["canonical_runtime_observation"], [10])
    del observation["ligand_lengths"]
    observation["source_projection_digest"] = "x"
    assert _compile(observation)["compiler_status"] == "BATCH_OBSERVATION_SCHEMA_MISMATCH"


def test_invalid_key_precedes_duplicate_and_virtual_policy(
    pinned_gate: list[int], vectors: dict[str, object],
) -> None:
    observation = _observation(vectors["canonical_runtime_observation"], [10, 4])
    observation["batch_sample_keys"] = ["", ""]
    observation["virtual_node_policy"] = "bad"
    assert _compile(observation)["compiler_status"] == "BATCH_SAMPLE_KEY_INVALID"


def test_compiler_is_dynamic_adapter_independent(
    monkeypatch: pytest.MonkeyPatch, pinned_gate: list[int], vectors: dict[str, object],
) -> None:
    monkeypatch.setattr(
        adapter, "build_covapie_current11_task2_batch_index_remap_adapter_v1",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("adapter called")),
    )
    output = _compile(_observation(vectors["canonical_runtime_observation"], list(range(11))))
    assert output["compiler_status"] == "COMPILED_EXACT"
    assert output["provenance"]["remap_executed_by_compiler"] is False


def test_compiler_is_dynamic_gate_private_helper_independent(
    monkeypatch: pytest.MonkeyPatch, pinned_gate: list[int], vectors: dict[str, object],
) -> None:
    private_name = "_evaluate" + "_reference_case_v1"
    monkeypatch.setattr(
        contract_gate, private_name,
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("private helper called")),
    )
    assert _compile(_observation(vectors["canonical_runtime_observation"], [10]))["compiler_status"] == "COMPILED_EXACT"


def test_precommit_filters_only_exact_untracked_shapes_and_both_status_commands(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner = contract_gate._remap_gate._instance_builder._payload_builder._contract_gate
    original = owner._run_git

    def fake(_root: Path, _arguments: Sequence[str]) -> str:
        return "\n".join([f"?? {path}" for path in EXACT4] + ["?? fifth.txt"])

    monkeypatch.setattr(owner, "_run_git", fake)
    with compiler._precommit_compatibility():
        for arguments in (
            ("status", "--porcelain=v1", "--untracked-files=all"),
            ("status", "--short"),
        ):
            assert owner._run_git(REPO, arguments) == "?? fifth.txt"
        assert owner._run_git(REPO, ("rev-parse", "HEAD")).startswith("?? " + EXACT4[0])
    assert owner._run_git is fake
    monkeypatch.setattr(owner, "_run_git", original)


@pytest.mark.parametrize("shape", [" M ", "M  ", "A  ", "D  ", "T  ", "UU "])
def test_precommit_rejects_tracked_staged_deleted_type_and_unmerged_shapes(
    monkeypatch: pytest.MonkeyPatch, shape: str,
) -> None:
    owner = contract_gate._remap_gate._instance_builder._payload_builder._contract_gate

    def fake(_root: Path, _arguments: Sequence[str]) -> str:
        return shape + EXACT4[0]

    monkeypatch.setattr(owner, "_run_git", fake)
    with compiler._precommit_compatibility():
        with pytest.raises(ValueError, match=f"^{ERROR}$"):
            owner._run_git(REPO, ("status", "--short"))


def test_precommit_restores_wrapper_after_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    owner = contract_gate._remap_gate._instance_builder._payload_builder._contract_gate
    original = owner._run_git
    with pytest.raises(RuntimeError, match="boom"):
        with compiler._precommit_compatibility():
            raise RuntimeError("boom")
    assert owner._run_git is original


def _changed_json(exact6: dict[str, bytes], name: str, mutate) -> dict[str, bytes]:
    changed = copy.deepcopy(exact6)
    value = json.loads(changed[name].decode("utf-8"))
    mutate(value)
    changed[name] = (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("utf-8")
    return changed


@pytest.mark.parametrize(
    ("case_id", "mutation"),
    (
        ("exact6_order", None),
        ("manifest_bytes", ("manifest",)),
        ("input_bytes", ("input",)),
        ("output_bytes", ("output",)),
        ("vocabulary_bytes", ("vocabulary",)),
        ("reference_bytes", ("reference",)),
        ("report_digest", ("report",)),
        ("provider_digest", ("provider_digest",)),
        ("provider_missing", ("provider_missing",)),
        ("canonical_missing", ("canonical_missing",)),
        ("duplicate_case", ("duplicate_case",)),
        ("source_authority", ("source_authority",)),
    ),
)
def test_gate_drift_raises_fixed_product_token(
    monkeypatch: pytest.MonkeyPatch, exact6: dict[str, bytes], vectors: dict[str, object],
    case_id: str, mutation: object,
) -> None:
    del vectors, mutation
    changed = copy.deepcopy(exact6)
    if case_id == "exact6_order":
        first = next(iter(changed))
        payload = changed.pop(first)
        changed[first] = payload
    elif case_id == "manifest_bytes":
        changed[compiler._MANIFEST] += b" "
    elif case_id == "input_bytes":
        changed[compiler._INPUT] += b" "
    elif case_id == "output_bytes":
        changed[compiler._OUTPUT] += b" "
    elif case_id == "vocabulary_bytes":
        changed[compiler._VOCABULARY] += b" "
    elif case_id == "reference_bytes":
        changed[compiler._VECTORS] += b" "
    elif case_id == "report_digest":
        changed = _changed_json(changed, compiler._REPORT, lambda value: value.update(contract_digest="0" * 64))
    elif case_id == "provider_digest":
        changed = _changed_json(changed, compiler._VECTORS, lambda value: value.update(identity_provider_digest="0" * 64))
    elif case_id == "provider_missing":
        changed = _changed_json(changed, compiler._VECTORS, lambda value: value.pop("identity_provider"))
    elif case_id == "canonical_missing":
        changed = _changed_json(changed, compiler._VECTORS, lambda value: value["reference_cases"].pop(0))
    elif case_id == "duplicate_case":
        changed = _changed_json(changed, compiler._VECTORS, lambda value: value["reference_cases"].__setitem__(1, copy.deepcopy(value["reference_cases"][0])))
    elif case_id == "source_authority":
        def mutate_source(value: dict[str, object]) -> None:
            value["reference_cases"][0]["compiler_output"]["adapter_input_exact18"]["source_pair_values_int64"][0][0] += 1
        changed = _changed_json(changed, compiler._VECTORS, mutate_source)
    monkeypatch.setattr(
        contract_gate, "build_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1",
        lambda **_kwargs: changed,
    )
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        _compile({})


def test_non_dict_and_dict_subclass_are_normal_schema_failures(
    pinned_gate: list[int], vectors: dict[str, object],
) -> None:
    class Observation(dict):
        pass

    for value in ([], Observation(vectors["canonical_runtime_observation"])):
        output = _compile(value)
        assert output["compiler_status"] == "BATCH_OBSERVATION_SCHEMA_MISMATCH"
        assert output["adapter_input_exact18"] is None


@contextmanager
def _adapter_compatibility() -> Iterator[None]:
    owner = adapter._projection_contract_gate
    original = owner._run_git

    def compatible(root: Path, arguments: Sequence[str]) -> str:
        output = original(root, arguments)
        if tuple(arguments) == ("status", "--porcelain=v1", "--untracked-files=all"):
            allowed = {f"?? {path}" for path in EXACT4}
            lines = output.splitlines()
            if any(len(line) >= 4 and line[3:] in EXACT4 and line not in allowed for line in lines):
                raise ValueError(ERROR)
            output = "\n".join(line for line in lines if line not in allowed)
        return output

    try:
        owner._run_git = compatible
        yield
    finally:
        owner._run_git = original


def test_public_adapter_composition_six(
    pinned_gate: list[int], vectors: dict[str, object],
) -> None:
    base = vectors["canonical_runtime_observation"]
    specs = (
        ("canonical_exact11", list(range(11)), JOINT),
        ("reversed_exact11", list(reversed(range(11))), JOINT),
        ("mixed_10_4_0_7_2", [10, 4, 0, 7, 2], JOINT),
        ("subset_10_4_0", [10, 4, 0], JOINT),
        ("no_joint", list(range(11)), None),
        ("empty_batch", [], JOINT),
    )
    for case_id, order, joint in specs:
        exact18 = _compile(_observation(base, order, joint))["adapter_input_exact18"]
        with _adapter_compatibility():
            exact2 = adapter.build_covapie_current11_task2_batch_index_remap_adapter_v1(
                repo_root=REPO, state_root=STATE, adapter_input=copy.deepcopy(exact18),
            )
        output = json.loads(exact2["current11_task2_batch_index_remap_output.json"])
        assert output["remap_status"] == "REMAPPED_EXACT"
        if case_id == "empty_batch":
            assert output["pair_values_batch_indices"] == []
        if case_id == "no_joint":
            assert output["pair_values_joint_global_indices"] is None


@pytest.mark.parametrize(
    "arguments",
    (
        (), ("--help",), ("--observation", "{}"), ("--input", "x"), ("--json", "x"),
        ("--compile",), ("--output", "x"), ("--write",), ("--tensor",), ("--numpy",),
        ("--torch",), ("--dataloader",), ("--model",), ("--head",), ("--loss",),
        ("--train",), ("--extra",), ("--repo-root", str(REPO)),
    ),
)
def test_checker_rejects_help_observation_and_expanded_scope(arguments: tuple[str, ...]) -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/check_covapie_current11_task2_batch_descriptor_compiler_v1.py", *arguments],
        cwd=REPO, env={**os.environ, "PYTHONPATH": "src", "PYTHONDONTWRITEBYTECODE": "1"},
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
    )
    assert completed.returncode == 1
    assert completed.stdout == ""
    assert completed.stderr == ERROR + "\n"


def test_exact4_are_text_safe_0644_and_bounded() -> None:
    for relative in EXACT4:
        path = REPO / relative
        payload = path.read_bytes()
        assert path.stat().st_mode & 0o777 == 0o644
        assert 0 < len(payload) < 1024 * 1024
        assert payload.decode("utf-8").encode("utf-8") == payload
        assert b"\0" not in payload and b"\r" not in payload
