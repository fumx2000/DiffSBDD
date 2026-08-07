from __future__ import annotations

import ast
import builtins
import copy
import hashlib
import importlib.util
import inspect
import json
import stat
import subprocess
import textwrap
from pathlib import Path
from typing import Sequence

import pytest

from covalent_ext import covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1 as contract_gate
from covalent_ext import covapie_current11_task2_batch_descriptor_compiler_v1 as compiler
from covalent_ext import covapie_current11_task2_batch_index_remap_adapter_v1 as adapter


REPO = Path(__file__).resolve().parents[1]
STATE = REPO.parent / "covapie-state"
BASE_COMMIT = "df3f570d8ec98440856bdfa311387443b24ca1fa"
ERROR = "COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_V1_ERROR"
CHECKER_ERROR = (
    "COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_"
    "SHARED_KERNEL_REFACTOR_V1_ERROR"
)
EXACT4 = (
    "src/covalent_ext/covapie_current11_task2_batch_descriptor_compiler_v1.py",
    "scripts/check_covapie_current11_task2_batch_descriptor_compiler_shared_kernel_refactor_v1.py",
    "tests/test_covapie_current11_task2_batch_descriptor_compiler_shared_kernel_refactor_v1.py",
    "docs/covapie_current11_task2_batch_descriptor_compiler_shared_kernel_refactor_v1_guide.md",
)
SUCCESS_SPECS = (
    ("canonical", tuple(range(11)), compiler._JOINT_LAYOUT),
    ("reversed", tuple(reversed(range(11))), compiler._JOINT_LAYOUT),
    ("subset_10_4_0", (10, 4, 0), None),
    ("singleton_10", (10,), None),
)
FAILURE_STATUSES = {
    "source_contract_override": "SOURCE_CONTRACT_MISMATCH",
    "duplicate_runtime_key": "BATCH_SAMPLE_KEY_DUPLICATED",
    "wrong_ligand_length": "ROLE_LENGTH_MISMATCH",
    "wrong_ligand_membership": "MEMBERSHIP_MASK_MISMATCH",
    "unknown_joint_descriptor": "BATCH_OBSERVATION_SCHEMA_MISMATCH",
}


def _readiness_fixture() -> dict[str, bool]:
    return {
        "task2_batch_descriptor_compiler_contract_gate_implemented": True,
        "task2_batch_descriptor_compiler_contract_gate_passed": True,
        "task2_batch_descriptor_compiler_contract_designed": True,
        "formal_runtime_carrier_verified": True,
        "source_contract_verified": True,
        "identity_provider_verified": True,
        "compiler_input_schema_frozen": True,
        "compiler_output_schema_frozen": True,
        "compiler_status_vocabulary_frozen": True,
        "compiler_reference_composition_passed": True,
        "task2_batch_descriptor_compiler_implemented": True,
        "runtime_batch_observation_extractor_implemented": False,
        "ready_for_task2_batch_descriptor_compiler_implementation": False,
        "ready_for_runtime_batch_observation_extractor_design": True,
        "ready_for_dataloader_integration": False,
        "ready_for_model_integration": False,
        "ready_for_loss_integration": False,
        "feature_semantics_reaudit_required_before_training": True,
        "ready_for_training": False,
        "checkpoint_state_dict_change_required": False,
        "base_model_parameter_shape_change_required": False,
        "base_atom_feature_width_change_required": False,
        "egnn_or_se3_backbone_change_required": False,
        "checkpoint_bytes_read": False,
    }


def _source_fixture() -> dict[str, object]:
    return {
        "schema_version": compiler._SOURCE_SCHEMA,
        "source_projection_digest": compiler._PROJECTION_DIGEST,
        "source_payload_digest": compiler._PAYLOAD_DIGEST,
        "parser_schema_version": compiler._PARSER_SCHEMA,
        "collate_schema_version": compiler._COLLATE_SCHEMA,
        "source_sample_order": [
            {
                "sample_index_row_id": identity[0],
                "sample_preparation_input_id": identity[1],
                "pdb_id": identity[2],
                "ligand_comp_id": identity[3],
                "source_sample_index": index,
            }
            for index, identity in enumerate(compiler._SOURCE_IDENTITIES)
        ],
        "source_pair_values_int64": [list(pair) for pair in compiler._SOURCE_PAIRS],
        "source_sample_offsets_int64": list(range(12)),
        "source_entry_validity_bool": [True] * 11,
        "source_sample_validity_bool": [True] * 11,
    }


def _provider_fixture(source: dict[str, object]) -> list[dict[str, object]]:
    samples = source["source_sample_order"]
    assert type(samples) is list
    provider: list[dict[str, object]] = []
    for index, sample in enumerate(samples):
        assert type(sample) is dict
        roles: dict[str, object] = {}
        for role_index, role_name in enumerate(("pocket", "ligand")):
            selected_source = compiler._SOURCE_PAIRS[index][role_index]
            digest = hashlib.sha256(f"test:{index}:{role_name}".encode()).hexdigest()
            roles[role_name] = {
                "root_kind": "repo_root",
                "relative_path": f"fixture/{index}/{role_name}.csv",
                "SHA256": digest,
                "row_count": selected_source + 20,
                "row_order_digest": digest,
                "row_order_version": "physical_csv_data_row_order_v1",
                "selected_source_row_index_0based": selected_source,
                "selected_parser_local_index": 0,
                "parser_output_atom_count": index + role_index + 2,
                "source_to_parser_local": {str(selected_source): 0},
                "selected_atom_identity": {
                    "atom_site_id": str(index + 1),
                    "atom_name": "SG" if role_name == "pocket" else "C1",
                    "type_symbol": "S" if role_name == "pocket" else "C",
                    "residue_name_or_ligand_comp_id": (
                        "CYS" if role_name == "pocket" else sample["ligand_comp_id"]
                    ),
                    "auth_asym_id": "A",
                    "auth_seq_id": str(index + 1),
                    "label_asym_id": "A",
                    "label_seq_id": str(index + 1),
                },
            }
        provider.append(
            {
                "sample_identity": {
                    field: sample[field] for field in compiler._IDENTITY_FIELDS
                },
                "roles": roles,
            }
        )
    return provider


def _authority_fixture() -> tuple[dict[str, object], list[dict[str, object]], dict[str, bool]]:
    source = _source_fixture()
    return source, _provider_fixture(source), _readiness_fixture()


def _membership(lengths: Sequence[int]) -> list[int]:
    return [ordinal for ordinal, length in enumerate(lengths) for _ in range(length)]


def _observation(
    authority: tuple[dict[str, object], list[dict[str, object]], dict[str, bool]],
    order: Sequence[int],
    joint: str | None,
) -> dict[str, object]:
    source, provider, _readiness = authority
    samples = source["source_sample_order"]
    assert type(samples) is list
    ligand = [provider[index]["roles"]["ligand"]["parser_output_atom_count"] for index in order]
    pocket = [provider[index]["roles"]["pocket"]["parser_output_atom_count"] for index in order]
    return {
        "schema_version": compiler._INPUT_SCHEMA,
        "runtime_batch_schema_version": compiler._RUNTIME_SCHEMA,
        "sample_key_schema_version": compiler._SAMPLE_KEY_SCHEMA,
        "batch_sample_keys": [samples[index]["sample_index_row_id"] for index in order],
        "ligand_lengths": ligand,
        "pocket_lengths": pocket,
        "ligand_membership": _membership(ligand),
        "pocket_membership": _membership(pocket),
        "joint_layout_descriptor": joint,
        "virtual_node_policy": compiler._VIRTUAL_POLICY,
        "receptors": [samples[index]["pdb_id"] for index in order],
        "consistency_buffer_lengths": {
            "ligand_coords": sum(ligand),
            "ligand_one_hot": sum(ligand),
            "pocket_coords": sum(pocket),
            "pocket_one_hot": sum(pocket),
        },
        "debug_coordinates": None,
        "debug_rank_metadata": None,
    }


def _failure_cases(
    authority: tuple[dict[str, object], list[dict[str, object]], dict[str, bool]],
) -> dict[str, dict[str, object]]:
    base = _observation(authority, (10, 4, 0), None)

    def changed(field: str, value: object) -> dict[str, object]:
        result = copy.deepcopy(base)
        result[field] = value
        return result

    return {
        "source_contract_override": {
            **copy.deepcopy(base),
            "source_projection_digest": compiler._PROJECTION_DIGEST,
        },
        "duplicate_runtime_key": changed(
            "batch_sample_keys", [base["batch_sample_keys"][0]] * 3
        ),
        "wrong_ligand_length": changed(
            "ligand_lengths", [base["ligand_lengths"][0] + 1, *base["ligand_lengths"][1:]]
        ),
        "wrong_ligand_membership": changed("ligand_membership", []),
        "unknown_joint_descriptor": changed("joint_layout_descriptor", "unknown"),
    }


def _slow_direct(
    monkeypatch: pytest.MonkeyPatch,
    authority: tuple[dict[str, object], list[dict[str, object]], dict[str, bool]],
    observation: dict[str, object],
) -> tuple[dict[str, object], dict[str, object], list[int]]:
    calls: list[int] = []

    def fixture_authority(repo: Path, state: Path):
        assert repo == REPO and state == STATE
        calls.append(1)
        return copy.deepcopy(authority)

    monkeypatch.setattr(compiler, "_authority", fixture_authority)
    slow = compiler.compile_covapie_current11_task2_batch_descriptor_v1(
        repo_root=REPO,
        state_root=STATE,
        observation=copy.deepcopy(observation),
    )
    monkeypatch.setattr(
        compiler,
        "_authority",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("authority called")),
    )
    direct = compiler._compile_with_verified_authority_v1(
        authority=copy.deepcopy(authority),
        observation=copy.deepcopy(observation),
    )
    return slow, direct, calls


def _load_checker():
    specification = importlib.util.spec_from_file_location(
        "covapie_shared_kernel_checker_test", REPO / EXACT4[1]
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _function(source: str, name: str) -> ast.FunctionDef:
    return next(
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def test_public_slow_api_and_all_are_unchanged() -> None:
    assert compiler.__all__ == ("compile_covapie_current11_task2_batch_descriptor_v1",)
    signature = inspect.signature(
        compiler.compile_covapie_current11_task2_batch_descriptor_v1
    )
    assert tuple(signature.parameters) == ("repo_root", "state_root", "observation")
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    assert str(signature.return_annotation) == "dict[str, object]"
    assert compiler._ERROR == ERROR


def test_private_kernel_exists_is_keyword_only_and_is_not_public() -> None:
    kernel = compiler._compile_with_verified_authority_v1
    signature = inspect.signature(kernel)
    assert kernel.__name__ not in compiler.__all__
    assert tuple(signature.parameters) == ("authority", "observation")
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    assert str(signature.parameters["observation"].annotation) == "object"
    assert str(signature.return_annotation) == "dict[str, object]"


def test_compile_validates_two_roots_calls_authority_once_and_kernel_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, object]] = []
    authority = _authority_fixture()
    sentinel = {"sentinel": True}

    def root(path: Path) -> Path:
        calls.append(("root", path))
        return path

    def acquire(repo: Path, state: Path):
        calls.append(("authority", (repo, state)))
        return authority

    def kernel(*, authority: object, observation: object):
        calls.append(("kernel", (authority, observation)))
        return sentinel

    observation: dict[str, object] = {}
    monkeypatch.setattr(compiler, "_require_root", root)
    monkeypatch.setattr(compiler, "_authority", acquire)
    monkeypatch.setattr(compiler, "_compile_with_verified_authority_v1", kernel)
    assert compiler._compile(
        repo_root=REPO, state_root=STATE, observation=observation
    ) is sentinel
    assert calls == [
        ("root", REPO),
        ("root", STATE),
        ("authority", (REPO, STATE)),
        ("kernel", (authority, observation)),
    ]


def test_observation_semantic_body_is_ast_identical_to_published_predecessor() -> None:
    prior = subprocess.run(
        ["git", "show", f"{BASE_COMMIT}:{EXACT4[0]}"],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    ).stdout
    current = (REPO / EXACT4[0]).read_text(encoding="utf-8")
    old_compile = _function(prior, "_compile")
    new_kernel = _function(current, "_compile_with_verified_authority_v1")
    assert len(old_compile.body) > 3 and len(new_kernel.body) > 1
    assert ast.dump(ast.Module(body=old_compile.body[3:], type_ignores=[])) == ast.dump(
        ast.Module(body=new_kernel.body[1:], type_ignores=[])
    )


def test_kernel_source_is_batch_local_and_has_no_root_gate_fs_or_adapter_access() -> None:
    source = textwrap.dedent(
        inspect.getsource(compiler._compile_with_verified_authority_v1)
    )
    tree = ast.parse(source)
    forbidden_names = {
        "repo_root",
        "state_root",
        "_require_root",
        "_authority",
        "_contract_gate",
        "adapter",
        "open",
        "subprocess",
        "git",
    }
    assert not {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and node.id in forbidden_names
    }
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr
        in {
            "open",
            "read_bytes",
            "read_text",
            "write_bytes",
            "write_text",
            "stat",
            "lstat",
            "resolve",
        }
        for node in ast.walk(tree)
    )


def test_direct_kernel_dynamically_calls_no_authority_root_gate_fs_or_adapter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = _authority_fixture()
    observation = _observation(authority, (10,), None)
    counts = {"authority": 0, "root": 0, "gate": 0, "fs": 0, "adapter": 0}

    def forbidden(kind: str):
        def raising(*_args: object, **_kwargs: object):
            counts[kind] += 1
            raise AssertionError(f"{kind} called")

        return raising

    with monkeypatch.context() as guarded:
        guarded.setattr(compiler, "_authority", forbidden("authority"))
        guarded.setattr(compiler, "_require_root", forbidden("root"))
        guarded.setattr(
            contract_gate,
            "build_covapie_current11_task2_batch_descriptor_compiler_contract_gate_v1",
            forbidden("gate"),
        )
        guarded.setattr(
            adapter,
            "build_covapie_current11_task2_batch_index_remap_adapter_v1",
            forbidden("adapter"),
        )
        guarded.setattr(builtins, "open", forbidden("fs"))
        for name in ("open", "read_bytes", "read_text", "stat", "lstat", "resolve"):
            guarded.setattr(Path, name, forbidden("fs"))
        output = compiler._compile_with_verified_authority_v1(
            authority=copy.deepcopy(authority),
            observation=copy.deepcopy(observation),
        )
    assert output["compiler_status"] == "COMPILED_EXACT"
    assert counts == {"authority": 0, "root": 0, "gate": 0, "fs": 0, "adapter": 0}


@pytest.mark.parametrize(("case_id", "order", "joint"), SUCCESS_SPECS)
def test_success_slow_direct_exact_parity(
    monkeypatch: pytest.MonkeyPatch,
    case_id: str,
    order: tuple[int, ...],
    joint: str | None,
) -> None:
    del case_id
    authority = _authority_fixture()
    observation = _observation(authority, order, joint)
    slow, direct, calls = _slow_direct(monkeypatch, authority, observation)
    assert calls == [1]
    assert slow == direct
    assert direct["compiler_status"] == "COMPILED_EXACT"


@pytest.mark.parametrize("case_id", tuple(FAILURE_STATUSES))
def test_representative_hard_failure_slow_direct_exact_parity(
    monkeypatch: pytest.MonkeyPatch, case_id: str
) -> None:
    authority = _authority_fixture()
    observation = _failure_cases(authority)[case_id]
    slow, direct, calls = _slow_direct(monkeypatch, authority, observation)
    assert calls == [1]
    assert slow == direct
    assert direct["compiler_status"] == FAILURE_STATUSES[case_id]
    assert direct["failure_reason"] == FAILURE_STATUSES[case_id]
    assert direct["adapter_input_exact18"] is None


def test_output_exact10_and_adapter_exact18_field_orders_are_unchanged() -> None:
    authority = _authority_fixture()
    output = compiler._compile_with_verified_authority_v1(
        authority=copy.deepcopy(authority),
        observation=_observation(authority, tuple(range(11)), compiler._JOINT_LAYOUT),
    )
    assert tuple(output) == compiler._OUTPUT_FIELDS
    assert tuple(output["adapter_input_exact18"]) == compiler._EXACT18_FIELDS


def test_direct_kernel_does_not_mutate_inputs_and_is_deterministic() -> None:
    authority = _authority_fixture()
    observation = _observation(authority, (10, 4, 0), None)
    authority_before = copy.deepcopy(authority)
    observation_before = copy.deepcopy(observation)
    first = compiler._compile_with_verified_authority_v1(
        authority=authority, observation=observation
    )
    second = compiler._compile_with_verified_authority_v1(
        authority=copy.deepcopy(authority), observation=copy.deepcopy(observation)
    )
    assert authority == authority_before
    assert observation == observation_before
    assert first == second
    assert first is not second
    assert first["adapter_input_exact18"] is not second["adapter_input_exact18"]


def test_kernel_existing_internal_invariant_uses_compiler_private_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = _authority_fixture()
    observation = _observation(authority, (10,), None)
    monkeypatch.setattr(compiler, "_EXACT18_FIELDS", tuple(reversed(compiler._EXACT18_FIELDS)))
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        compiler._compile_with_verified_authority_v1(
            authority=authority, observation=observation
        )


def test_public_slow_wrapper_maps_unexpected_kernel_error_to_compiler_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(compiler, "_authority", lambda _repo, _state: _authority_fixture())
    monkeypatch.setattr(
        compiler,
        "_compile_with_verified_authority_v1",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("unexpected")),
    )
    with pytest.raises(ValueError, match=f"^{ERROR}$") as captured:
        compiler.compile_covapie_current11_task2_batch_descriptor_v1(
            repo_root=REPO, state_root=STATE, observation={}
        )
    assert type(captured.value.__cause__) is RuntimeError


def test_no_hidden_cache_and_context_product_not_exposed_by_compiler() -> None:
    source = inspect.getsource(compiler)
    tree = ast.parse(source)
    assignments = {
        target.id
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (node.targets if isinstance(node, ast.Assign) else (node.target,))
        if isinstance(target, ast.Name)
    }
    assert "lru_cache" not in source
    assert not any("CACHE" in name.upper() for name in assignments)
    assert "build_covapie_current11_task2_batch_descriptor_compiler_context_v1" not in source
    assert "compile_covapie_current11_task2_batch_descriptor_with_context_v1" not in source
    assert not any(
        isinstance(node, ast.ClassDef) and "context" in node.name.lower()
        for node in tree.body
    )


@pytest.mark.parametrize(
    "lifecycle", ("precommit-mixed-candidate", "clean-tracked-successor")
)
def test_checker_lifecycle_accepts_mixed_precommit_and_clean_successor(
    monkeypatch: pytest.MonkeyPatch, lifecycle: str
) -> None:
    checker = _load_checker()
    compiler_path, *new_paths = EXACT4
    head_blob = "a" * 40
    worktree_blob = "b" * 40

    def run_git(_repo: Path, arguments: Sequence[str]) -> str:
        call = tuple(arguments)
        if call == ("status", "--porcelain=v1", "--untracked-files=all"):
            if lifecycle == "precommit-mixed-candidate":
                return "\n".join(
                    [f" M {compiler_path}", *(f"?? {path}" for path in new_paths)]
                ) + "\n"
            return ""
        if call == ("ls-files", "--stage", "--", *EXACT4):
            paths = (compiler_path,) if lifecycle == "precommit-mixed-candidate" else EXACT4
            return "\n".join(f"100644 {head_blob} 0\t{path}" for path in paths) + "\n"
        if call[:2] == ("hash-object", "--no-filters"):
            if lifecycle == "precommit-mixed-candidate":
                return worktree_blob + "\n"
            return head_blob + "\n"
        if call[0] == "rev-parse":
            return head_blob + "\n"
        pytest.fail(f"unexpected git call: {call!r}")

    monkeypatch.setattr(checker, "_run_git", run_git)
    assert checker._repository_lifecycle(REPO) == lifecycle


@pytest.mark.parametrize(
    "bad_status",
    (
        "M  src/covalent_ext/covapie_current11_task2_batch_descriptor_compiler_v1.py",
        " M src/covalent_ext/covapie_current11_task2_batch_descriptor_compiler_v1.py\n?? fifth.txt",
        "?? scripts/check_covapie_current11_task2_batch_descriptor_compiler_shared_kernel_refactor_v1.py",
        "D  src/covalent_ext/covapie_current11_task2_batch_descriptor_compiler_v1.py",
    ),
)
def test_checker_lifecycle_rejects_staged_extra_missing_and_destructive_shapes(
    monkeypatch: pytest.MonkeyPatch, bad_status: str
) -> None:
    checker = _load_checker()
    monkeypatch.setattr(
        checker,
        "_run_git",
        lambda _repo, arguments: bad_status + "\n"
        if tuple(arguments) == ("status", "--porcelain=v1", "--untracked-files=all")
        else "",
    )
    with pytest.raises(ValueError, match=f"^{CHECKER_ERROR}$"):
        checker._repository_lifecycle(REPO)


def test_checker_lineage_is_base_ancestry_only_and_does_not_use_origin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()
    calls: list[tuple[str, ...]] = []

    def run_git(_repo: Path, arguments: Sequence[str]) -> str:
        call = tuple(arguments)
        calls.append(call)
        if call == ("branch", "--show-current"):
            return "main\n"
        if call == ("cat-file", "-e", f"{BASE_COMMIT}^{{commit}}"):
            return ""
        if call == ("merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"):
            return ""
        pytest.fail(f"unexpected git call: {call!r}")

    monkeypatch.setattr(checker, "_run_git", run_git)
    checker._validate_repository_lineage(REPO)
    assert len(calls) == 3
    assert all("origin" not in item for call in calls for item in call)


@pytest.mark.parametrize(
    "arguments",
    (
        (),
        ("--help",),
        ("--repo-root", str(REPO)),
        ("--state-root", str(STATE)),
        ("--repo-root", str(REPO), "--state-root", str(STATE), "--train"),
    ),
)
def test_checker_cli_accepts_no_expanded_scope(arguments: tuple[str, ...]) -> None:
    checker = _load_checker()
    with pytest.raises(ValueError, match=f"^{CHECKER_ERROR}$"):
        checker._main(arguments)


def test_checker_main_is_fixture_only_and_emits_pass(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    checker = _load_checker()
    expected_lifecycle = checker._repository_lifecycle(REPO)
    assert expected_lifecycle in (
        "precommit-mixed-candidate",
        "clean-tracked-successor",
    )
    monkeypatch.setattr(
        checker.compiler,
        "_authority",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("live authority called")
        ),
    )
    assert checker._main(
        ("--repo-root", str(REPO), "--state-root", str(STATE))
    ) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out.count("\n") == 1
    summary = json.loads(captured.out)
    assert summary["status"] == "PASS_SHARED_KERNEL_REFACTOR_ONLY"
    assert summary["repository_lifecycle"] == expected_lifecycle
    assert summary["success_parity"] == {"checked": 4, "passed": 4}
    assert summary["hard_failure_parity"] == {"checked": 5, "passed": 5}
    assert summary["direct_kernel_authority_call_count"] == 0
    assert summary["direct_kernel_filesystem_call_count"] == 0
    assert summary["formal_carrier_and_routing_unchanged"] is True


def test_repository_exact4_are_safe_mixed_precommit_or_clean_successor() -> None:
    status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    ).stdout.splitlines()
    index = subprocess.run(
        ["git", "ls-files", "--stage", "--", *EXACT4],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    ).stdout.splitlines()
    expected_precommit = {
        f" M {EXACT4[0]}",
        *(f"?? {path}" for path in EXACT4[1:]),
    }
    if status:
        assert set(status) == expected_precommit and len(status) == 4
        assert len(index) == 1 and index[0].endswith("\t" + EXACT4[0])
    else:
        assert len(index) == 4
        for row in index:
            metadata, relative = row.split("\t", 1)
            mode, blob, stage = metadata.split()
            assert mode == "100644" and stage == "0" and relative in EXACT4
            worktree = subprocess.run(
                ["git", "hash-object", "--no-filters", relative],
                cwd=REPO,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            ).stdout.strip()
            head = subprocess.run(
                ["git", "rev-parse", f"HEAD:{relative}"],
                cwd=REPO,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            ).stdout.strip()
            assert blob == worktree == head
    for relative in EXACT4:
        path = REPO / relative
        metadata = path.lstat()
        payload = path.read_bytes()
        assert stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
        assert stat.S_IMODE(metadata.st_mode) == 0o644
        assert 0 < len(payload) < 1024 * 1024
        assert not payload.startswith(b"\xef\xbb\xbf")
        assert b"\0" not in payload and b"\r" not in payload
        assert payload.endswith(b"\n") and not payload.endswith(b"\n\n")
        text = payload.decode("utf-8", errors="strict")
        assert all(not line.endswith((" ", "\t")) for line in text.splitlines())
