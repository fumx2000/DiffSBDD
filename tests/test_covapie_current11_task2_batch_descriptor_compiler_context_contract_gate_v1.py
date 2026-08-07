from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import inspect
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Sequence

import pytest

from covalent_ext import covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1 as gate


REPO = Path(__file__).resolve().parents[1]
STATE = REPO.parent / "covapie-state"
ERROR = (
    "COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_"
    "CONTRACT_GATE_V1_ERROR"
)
EXACT4 = gate._REPOSITORY_EXACT4
EXACT6 = gate._ARTIFACT_NAMES


def _source_fixture() -> dict[str, object]:
    samples = []
    for index, identity in enumerate(gate._compiler._SOURCE_IDENTITIES):
        samples.append(
            {
                "sample_index_row_id": identity[0],
                "sample_preparation_input_id": identity[1],
                "pdb_id": identity[2],
                "ligand_comp_id": identity[3],
                "source_sample_index": index,
            }
        )
    return {
        "schema_version": gate._compiler._SOURCE_SCHEMA,
        "source_projection_digest": gate._compiler._PROJECTION_DIGEST,
        "source_payload_digest": gate._compiler._PAYLOAD_DIGEST,
        "parser_schema_version": gate._compiler._PARSER_SCHEMA,
        "collate_schema_version": gate._compiler._COLLATE_SCHEMA,
        "source_sample_order": samples,
        "source_pair_values_int64": [
            list(pair) for pair in gate._compiler._SOURCE_PAIRS
        ],
        "source_sample_offsets_int64": list(range(12)),
        "source_entry_validity_bool": [True] * 11,
        "source_sample_validity_bool": [True] * 11,
    }


def _provider_fixture(source: dict[str, object]) -> list[dict[str, object]]:
    provider: list[dict[str, object]] = []
    samples = source["source_sample_order"]
    assert type(samples) is list
    for index, sample in enumerate(samples):
        assert type(sample) is dict
        roles: dict[str, object] = {}
        for role_index, role_name in enumerate(("pocket", "ligand")):
            selected_source = gate._compiler._SOURCE_PAIRS[index][role_index]
            sha = hashlib.sha256(f"{index}:{role_name}".encode()).hexdigest()
            roles[role_name] = {
                "root_kind": "repo_root",
                "relative_path": f"fixture/{index}/{role_name}.csv",
                "SHA256": sha,
                "row_count": selected_source + 10,
                "row_order_digest": sha,
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
                        "CYS" if role_name == "pocket" else str(sample["ligand_comp_id"])
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
                    field: sample[field] for field in gate._IDENTITY_FIELDS
                },
                "roles": roles,
            }
        )
    return provider


def _authority_fixture() -> tuple[dict[str, object], list[dict[str, object]], dict[str, bool]]:
    source = _source_fixture()
    return source, _provider_fixture(source), gate._expected_compiler_readiness()


def _install_fixture_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> list[tuple[Path, Path]]:
    calls: list[tuple[Path, Path]] = []

    def authority(repo: Path, state: Path):
        calls.append((repo, state))
        return copy.deepcopy(_authority_fixture())

    monkeypatch.setattr(gate._compiler, "_authority", authority)
    monkeypatch.setattr(
        gate._compiler, "_provider_digest", lambda _provider: gate._PROVIDER_DIGEST
    )
    return calls


@pytest.fixture()
def built(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[dict[str, bytes], list[tuple[Path, Path]]]:
    calls = _install_fixture_authority(monkeypatch)
    artifacts = gate.build_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1(
        repo_root=REPO, state_root=STATE
    )
    return artifacts, calls


def _parsed(artifacts: dict[str, bytes]) -> dict[str, dict[str, object]]:
    return {name: json.loads(payload) for name, payload in artifacts.items()}


def _load_checker():
    path = REPO / EXACT4[1]
    specification = importlib.util.spec_from_file_location(
        "covapie_context_contract_checker_test", path
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_public_surface_is_unique_keyword_only_and_import_is_silent() -> None:
    assert gate.__all__ == (
        "build_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1",
    )
    signature = inspect.signature(
        gate.build_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1
    )
    assert tuple(signature.parameters) == ("repo_root", "state_root")
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "import covalent_ext.covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1",
        ],
        cwd=REPO,
        env={
            **os.environ,
            "PYTHONPATH": "src:.",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == ""


def test_source_scope_is_contract_only_and_compiler_public_surface_remains_frozen() -> None:
    path = REPO / EXACT4[0]
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert imports <= set(sys.stdlib_module_names) | {"__future__", "covalent_ext"}
    assert not imports & {"torch", "numpy", "rdkit", "subprocess", "requests"}
    assert not any(isinstance(node, ast.ClassDef) for node in tree.body)
    assert f"def {gate._BUILD_API}" not in source
    assert f"def {gate._FAST_API}" not in source
    assert "@lru_cache" not in source
    module_assignments = {
        target.id
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (
            node.targets if isinstance(node, ast.Assign) else (node.target,)
        )
        if isinstance(target, ast.Name)
    }
    assert not any(name.endswith("_CACHE") for name in module_assignments)
    assert "task2_batch_index_remap_adapter_v1" not in source
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr
        in {"write_text", "write_bytes", "unlink", "mkdir", "rename", "replace"}
        for node in ast.walk(tree)
    )
    assert gate._compiler.__all__ == (gate._SLOW_API,)


def test_exact6_order_and_builder_calls_authority_exactly_once(
    built: tuple[dict[str, bytes], list[tuple[Path, Path]]]
) -> None:
    artifacts, calls = built
    assert type(artifacts) is dict
    assert tuple(artifacts) == EXACT6
    assert calls == [(REPO, STATE)]
    report = _parsed(artifacts)[gate._REPORT]
    assert report["live_authority_build_count"] == 1
    assert report["live_authority_verified"] is True


def test_exact6_are_canonical_safe_json_bytes(
    built: tuple[dict[str, bytes], list[tuple[Path, Path]]]
) -> None:
    artifacts, _calls = built
    for name, payload in artifacts.items():
        assert name.endswith(".json")
        assert type(payload) is bytes and 0 < len(payload) < 1024 * 1024
        assert not payload.startswith(b"\xef\xbb\xbf")
        assert b"\0" not in payload and b"\r" not in payload
        assert payload.endswith(b"\n") and not payload.endswith(b"\n\n")
        assert gate._json(json.loads(payload)) == payload


def test_stable_contract_digest_manual_framing_and_report_exclusion(
    built: tuple[dict[str, bytes], list[tuple[Path, Path]]]
) -> None:
    artifacts, _calls = built
    digest = hashlib.sha256(gate._CONTRACT_DOMAIN)
    for name in EXACT6[:5]:
        encoded = name.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        digest.update(len(artifacts[name]).to_bytes(8, "big"))
        digest.update(artifacts[name])
    report = _parsed(artifacts)[gate._REPORT]
    assert digest.hexdigest() == report["contract_digest"] == gate._stable_digest(artifacts)
    changed = dict(artifacts)
    changed[gate._REPORT] = b"different\n"
    assert gate._stable_digest(changed) == report["contract_digest"]


def test_authority_digest_and_components_use_canonical_domain_framing(
    built: tuple[dict[str, bytes], list[tuple[Path, Path]]]
) -> None:
    artifacts, _calls = built
    parsed = _parsed(artifacts)
    schema = parsed[gate._SCHEMA]
    report = parsed[gate._REPORT]
    snapshot = schema["canonical_semantic_snapshot"]
    assert report["authority_snapshot_digest"] == gate._framed_semantic_digest(
        gate._AUTHORITY_DOMAIN, snapshot
    )
    assert report["provenance_component_digest"] == gate._framed_semantic_digest(
        gate._PROVENANCE_COMPONENT_DOMAIN, snapshot["semantic_provenance"]
    )
    assert report["source_component_digest"] == gate._framed_semantic_digest(
        gate._SOURCE_COMPONENT_DOMAIN, snapshot["source_exact10"]
    )
    assert report["provider_component_digest"] == gate._framed_semantic_digest(
        gate._PROVIDER_COMPONENT_DOMAIN, snapshot["identity_provider_exact11"]
    )
    assert report["readiness_component_digest"] == gate._framed_semantic_digest(
        gate._READINESS_COMPONENT_DOMAIN, snapshot["readiness_template"]
    )
    contract = parsed[gate._MANIFEST]["authority_snapshot_contract"]
    assert contract["framing"] == "SHA256(domain || uint64be(payload_bytes) || payload)"
    assert contract["domain_hex"] == gate._AUTHORITY_DOMAIN.hex()
    assert contract["python_repr_pickle_hash_forbidden"] is True


def test_manifest_freezes_lineage_without_permanent_compiler_source_pin(
    built: tuple[dict[str, bytes], list[tuple[Path, Path]]]
) -> None:
    manifest = _parsed(built[0])[gate._MANIFEST]
    assert manifest["predecessor_base_commit"] == gate._BASE_COMMIT
    lineage = manifest["predecessor_and_provenance"]
    assert lineage["compiler_product_commit"] == gate._COMPILER_PRODUCT_COMMIT
    assert lineage["compiler_contract_commit"] == gate._COMPILER_CONTRACT_COMMIT
    assert lineage["compiler_contract_digest"] == gate._COMPILER_CONTRACT_DIGEST
    assert lineage["provider_digest"] == gate._PROVIDER_DIGEST
    assert lineage["source_contract_digest"] == gate._SOURCE_CONTRACT_DIGEST
    assert lineage["formal_carrier_aggregate"] == gate._FORMAL_CARRIER_AGGREGATE
    assert lineage["formal_npz_sha256"] == gate._FORMAL_NPZ_SHA256
    assert lineage["compiler_pre_refactor_source_identity_is_artifact_provenance_only"] is True
    assert lineage["future_checker_compiler_source_sha_admission_required"] is False
    lifecycle = manifest["repository_lifecycle_contract"]
    assert lifecycle["base_commit_must_be_ancestor_of_or_equal_to_HEAD"] is True
    assert lifecycle["HEAD_must_equal_base"] is False
    assert lifecycle["origin_main_used_for_admission"] is False
    assert lifecycle["HEAD_must_equal_origin_main"] is False


def test_pre_refactor_compiler_source_identity_is_provenance_only_not_future_admission(
    built: tuple[dict[str, bytes], list[tuple[Path, Path]]]
) -> None:
    manifest = _parsed(built[0])[gate._MANIFEST]
    lineage = manifest["predecessor_and_provenance"]
    assert (
        lineage["compiler_pre_refactor_source_sha256"]
        == gate._COMPILER_PRE_REFACTOR_SHA256
    )
    assert (
        lineage["compiler_pre_refactor_source_identity_is_artifact_provenance_only"]
        is True
    )
    assert lineage["future_checker_compiler_source_sha_admission_required"] is False

    checker_source = (REPO / EXACT4[1]).read_text(encoding="utf-8")
    checker_tree = ast.parse(checker_source)
    lineage_function = next(
        node
        for node in checker_tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_validate_repository_lineage"
    )
    lineage_source = ast.get_source_segment(checker_source, lineage_function)
    assert lineage_source is not None
    assert "_COMPILER_PRE_REFACTOR_SHA256" not in checker_source
    assert gate._COMPILER_PRE_REFACTOR_SHA256 not in checker_source
    assert gate._COMPILER_MODULE not in checker_source
    assert '"branch", "--show-current"' in lineage_source
    assert '"cat-file", "-e"' in lineage_source
    assert '"merge-base", "--is-ancestor"' in lineage_source
    assert "origin/main" not in lineage_source


def test_gate_build_does_not_enforce_pre_refactor_compiler_source_sha() -> None:
    admission_functions = (
        gate._build_impl,
        gate._require_root,
        gate._precommit_compatibility,
        gate._validated_authority,
    )
    for function in admission_functions:
        assert "_COMPILER_PRE_REFACTOR_SHA256" not in inspect.getsource(function)


def test_api_error_and_option2_shared_kernel_contract(
    built: tuple[dict[str, bytes], list[tuple[Path, Path]]]
) -> None:
    parsed = _parsed(built[0])
    manifest = parsed[gate._MANIFEST]
    api = parsed[gate._API]
    assert manifest["recommended_architecture"]["option"] == "Option 2"
    assert manifest["public_api_contract"]["future_context_module___all__"] == [
        gate._BUILD_API,
        gate._FAST_API,
    ]
    assert manifest["public_api_contract"]["existing_compiler_module___all__"] == [
        gate._SLOW_API
    ]
    kernel = api["shared_kernel_contract"]
    assert kernel["owner"] == gate._COMPILER_MODULE
    assert kernel["private_conceptual_name"] == gate._PRIVATE_KERNEL
    assert kernel["used_by_slow_and_fast_paths"] is True
    assert all(
        kernel[key] is False
        for key in (
            "root_validation",
            "filesystem_access",
            "gate_access",
            "adapter_access",
            "authority_access",
            "mutates_inputs",
        )
    )
    errors = api["error_contract"]
    assert errors["context_error_token"] == gate._CONTEXT_ERROR
    assert errors["existing_slow_error_token"] == gate._compiler._ERROR
    assert errors["builder_root_authority_gate_formal_provider_failure"][
        "compiler_token_retained_as___cause__"
    ] is True
    assert errors["valid_context_malformed_observation"] == {
        "raises_context_token": False,
        "returns_existing_compiler_hard_failure_exact10": True,
    }


def test_context_schema_immutability_pickle_integrity_and_process_contract(
    built: tuple[dict[str, bytes], list[tuple[Path, Path]]]
) -> None:
    parsed = _parsed(built[0])
    schema = parsed[gate._SCHEMA]
    api = parsed[gate._API]
    assert schema["context_schema_version"] == gate._CONTEXT_SCHEMA
    assert schema["semantic_field_order"] == list(gate._CONTEXT_SEMANTIC_FIELDS)
    assert schema["private_integrity_field_order"] == ["construction_seal"]
    assert schema["recommended_representation"] == "dataclass(frozen=True, slots=True, repr=False)"
    assert schema["reachable_builtin_dict_or_list_allowed"] is False
    assert schema["public_constructor_exposed"] is False
    assert schema["public_mutation_API_exposed"] is False
    assert schema["data_rich_repr_allowed"] is False
    assert schema["pickle_policy"] == {
        "__reduce___must_fail": True,
        "__reduce_ex___must_fail": True,
        "pickleable": False,
    }
    integrity = api["context_integrity_contract"]
    assert integrity["use_time_complexity"] == "O(1)"
    assert integrity["per_batch_provider_rehash"] is False
    assert integrity["per_batch_snapshot_recanonicalization"] is False
    process = api["process_and_dataloader_contract"]
    assert process["builder_calls_per_process"] == 1
    assert process["builder_calls_per_DDP_rank"] == 1
    assert process["context_shared_across_ranks"] is False
    assert process["checkpoint_storage"] is False
    assert process["Dataset_transport"] is False
    assert process["DataLoader_worker_transport"] is False
    assert process["build_inside_worker"] is False


def test_freshness_performance_and_output_parity_are_structural(
    built: tuple[dict[str, bytes], list[tuple[Path, Path]]]
) -> None:
    parsed = _parsed(built[0])
    manifest = parsed[gate._MANIFEST]
    freshness = manifest["freshness_semantics"]
    assert freshness["built_context_survives_external_disk_drift"] is True
    assert freshness["fresh_authority_requires_explicit_rebuild"] is True
    assert freshness["slow_api_rediscovers_drift_on_next_call"] is True
    assert freshness["fast_path_filesystem_polling"] is False
    performance = manifest["performance_acceptance"]
    assert performance == {
        "absolute_latency_SLA": False,
        "builder_authority_call_count": 1,
        "fast_authority_call_count": 0,
        "fast_filesystem_or_git_or_formal_read_count": 0,
        "fast_gate_builder_call_count": 0,
        "slow_fast_output_parity": "exact_deep_equality",
    }
    parity = parsed[gate._API]["output_parity_contract"]
    assert parity["comparison"] == "exact_deep_equality"
    assert parity["output_exact10_field_order"] == list(gate._OUTPUT_FIELDS)
    assert parity["adapter_exact18_field_order"] == list(gate._EXACT18_FIELDS)
    assert parity["context_reuse_metadata_in_compiler_output"] is False


def test_reference_vectors_freeze_exact_four_parity_and_five_hard_failures(
    built: tuple[dict[str, bytes], list[tuple[Path, Path]]]
) -> None:
    vectors = _parsed(built[0])[gate._VECTORS]
    parity = vectors["output_parity_cases"]
    failures = vectors["representative_runtime_hard_failures"]
    contexts = vectors["context_failure_vectors"]
    assert [row["case_id"] for row in parity] == list(gate._PARITY_CASE_IDS)
    assert [row["case_id"] for row in failures] == list(gate._HARD_FAILURE_CASE_IDS)
    assert [row["case_id"] for row in contexts] == list(gate._CONTEXT_FAILURE_IDS)
    for row in parity:
        output = row["existing_slow_output"]
        assert set(output) == set(gate._OUTPUT_FIELDS)
        assert output["compiler_status"] == "COMPILED_EXACT"
        assert set(output["adapter_input_exact18"]) == set(gate._EXACT18_FIELDS)
        assert row["expected_parity"] == "exact_deep_equality"
        assert row["existing_slow_output_digest"] == gate._framed_semantic_digest(
            gate._OUTPUT_VECTOR_DOMAIN, output
        )
    expected_statuses = {
        "source_contract_override": "SOURCE_CONTRACT_MISMATCH",
        "duplicate_runtime_key": "BATCH_SAMPLE_KEY_DUPLICATED",
        "wrong_ligand_length": "ROLE_LENGTH_MISMATCH",
        "wrong_ligand_membership": "MEMBERSHIP_MASK_MISMATCH",
        "unknown_joint_descriptor": "BATCH_OBSERVATION_SCHEMA_MISMATCH",
    }
    for row in failures:
        output = row["existing_slow_output"]
        assert output["compiler_status"] == expected_statuses[row["case_id"]]
        assert output["adapter_input_exact18"] is None
        assert row["expected_fast_behavior"] == (
            "return_existing_output_exactly_without_context_error"
        )
    assert all(row["expected_exception_token"] == gate._CONTEXT_ERROR for row in contexts)
    assert all(row["observation_evaluated"] is False for row in contexts)


def test_acceptance_matrix_is_exact16(
    built: tuple[dict[str, bytes], list[tuple[Path, Path]]]
) -> None:
    acceptance = _parsed(built[0])[gate._ACCEPTANCE]
    rows = acceptance["acceptance_rows"]
    assert acceptance["acceptance_count"] == 16
    assert [row["acceptance_index"] for row in rows] == list(range(16))
    assert [row["acceptance_id"] for row in rows] == [
        "builder_authority_exactly_once",
        "fast_authority_zero",
        "fast_gate_zero",
        "fast_io_zero",
        "slow_public_surface_unchanged",
        "compiler___all___unchanged",
        "context___all___exact2",
        "slow_fast_deep_parity",
        "runtime_hard_failure_parity",
        "invalid_context_token",
        "build_drift_token",
        "deep_immutability",
        "non_pickleable",
        "no_hidden_cache",
        "no_fast_adapter",
        "no_training_surface_interaction",
    ]
    assert acceptance["performance_evidence"]["directional_only"] is True
    assert acceptance["performance_evidence"]["absolute_latency_SLA"] is False


def test_readiness_is_exactly_bounded_to_context_contract(
    built: tuple[dict[str, bytes], list[tuple[Path, Path]]]
) -> None:
    readiness = _parsed(built[0])[gate._REPORT]["readiness"]
    assert readiness == gate._gate_readiness()
    assert readiness["compiler_hot_loop_authority_context_contract_gate_passed"] is True
    assert readiness["compiler_hot_loop_authority_context_implemented"] is False
    assert readiness["compiler_shared_pure_kernel_refactor_implemented"] is False
    assert readiness["ready_for_compiler_hot_loop_authority_context_implementation"] is True
    assert readiness["ready_for_dataloader_integration"] is False
    assert readiness[
        "public_remap_adapter_hot_loop_audit_required_before_dataloader_integration"
    ] is True
    assert readiness["feature_semantics_reaudit_required_before_training"] is True
    assert readiness["ready_for_training"] is False
    assert readiness["checkpoint_bytes_read"] is False


def test_double_build_is_byte_identical_and_each_build_calls_authority_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_fixture_authority(monkeypatch)
    first = gate.build_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1(
        repo_root=REPO, state_root=STATE
    )
    assert len(calls) == 1
    second = gate.build_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1(
        repo_root=REPO, state_root=STATE
    )
    assert len(calls) == 2
    assert first == second


@pytest.mark.parametrize("failure", ("source", "provider", "readiness"))
def test_malformed_authority_fixture_fails_closed(
    monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    source, provider, readiness = _authority_fixture()
    if failure == "source":
        source["source_pair_values_int64"][0][0] += 1
    elif failure == "provider":
        del provider[0]["roles"]["pocket"]["selected_atom_identity"]
    else:
        readiness["ready_for_training"] = True
    calls: list[int] = []

    def authority(_repo: Path, _state: Path):
        calls.append(1)
        return source, provider, readiness

    monkeypatch.setattr(gate._compiler, "_authority", authority)
    monkeypatch.setattr(
        gate._compiler, "_provider_digest", lambda _provider: gate._PROVIDER_DIGEST
    )
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        gate.build_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1(
            repo_root=REPO, state_root=STATE
        )
    assert calls == [1]


def test_builder_performs_no_repository_or_state_write(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo = tmp_path / "repo"
    state = tmp_path / "state"
    repo.mkdir()
    state.mkdir()
    calls = _install_fixture_authority(monkeypatch)
    before = tuple(sorted(str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*")))
    artifacts = gate.build_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1(
        repo_root=repo, state_root=state
    )
    after = tuple(sorted(str(path.relative_to(tmp_path)) for path in tmp_path.rglob("*")))
    assert before == after == ("repo", "state")
    assert tuple(artifacts) == EXACT6
    assert calls == [(repo, state)]


def test_precommit_filter_hides_only_exact4_and_restores(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner = gate._compiler._contract_gate._remap_gate._instance_builder._payload_builder._contract_gate
    fifth = "fifth_untracked_must_remain_visible.txt"

    def fake(_root: Path, arguments: Sequence[str]) -> str:
        assert tuple(arguments) in {
            ("status", "--porcelain=v1", "--untracked-files=all"),
            ("status", "--short"),
        }
        return "\n".join([*(f"?? {path}" for path in EXACT4), f"?? {fifth}"])

    monkeypatch.setattr(owner, "_run_git", fake)
    with gate._precommit_compatibility():
        assert owner._run_git(REPO, ("status", "--short")) == f"?? {fifth}"
    assert owner._run_git is fake


@pytest.mark.parametrize("prefix", (" M ", "M  ", "D  ", "T  ", "UU "))
def test_precommit_filter_rejects_non_untracked_exact4_shape(
    monkeypatch: pytest.MonkeyPatch, prefix: str
) -> None:
    owner = gate._compiler._contract_gate._remap_gate._instance_builder._payload_builder._contract_gate

    def fake(_root: Path, _arguments: Sequence[str]) -> str:
        return prefix + EXACT4[0]

    monkeypatch.setattr(owner, "_run_git", fake)
    with gate._precommit_compatibility(), pytest.raises(ValueError, match=f"^{ERROR}$"):
        owner._run_git(REPO, ("status", "--short"))
    assert owner._run_git is fake


@pytest.mark.parametrize("lifecycle", ("precommit-untracked", "clean-tracked-successor"))
def test_checker_lifecycle_accepts_precommit_and_clean_successor(
    monkeypatch: pytest.MonkeyPatch, lifecycle: str
) -> None:
    checker = _load_checker()
    blob = "a" * 40

    def run_git(_repo: Path, arguments: Sequence[str]) -> str:
        call = tuple(arguments)
        if call == ("status", "--porcelain=v1", "--untracked-files=all"):
            if lifecycle == "precommit-untracked":
                return "\n".join(f"?? {path}" for path in EXACT4) + "\n"
            return ""
        if call == ("ls-files", "--stage", "--", *EXACT4):
            if lifecycle == "precommit-untracked":
                return ""
            return "\n".join(f"100644 {blob} 0\t{path}" for path in EXACT4) + "\n"
        if call[:2] == ("hash-object", "--no-filters") or call[0] == "rev-parse":
            return blob + "\n"
        pytest.fail(f"unexpected git call: {call!r}")

    monkeypatch.setattr(checker, "_run_git", run_git)
    assert checker._repository_lifecycle(REPO) == lifecycle


def test_checker_lifecycle_rejects_fifth_untracked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = _load_checker()

    def run_git(_repo: Path, arguments: Sequence[str]) -> str:
        if tuple(arguments) == (
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ):
            return "\n".join(
                [*(f"?? {path}" for path in EXACT4), "?? fifth.txt"]
            )
        return ""

    monkeypatch.setattr(checker, "_run_git", run_git)
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        checker._repository_lifecycle(REPO)


@pytest.mark.parametrize(
    "head_origin",
    (
        (gate._BASE_COMMIT, gate._BASE_COMMIT),
        ("committed-successor", gate._BASE_COMMIT),
        ("published-successor", "published-successor"),
    ),
)
def test_checker_lineage_uses_base_ancestry_not_origin_admission(
    monkeypatch: pytest.MonkeyPatch, head_origin: tuple[str, str]
) -> None:
    checker = _load_checker()
    head, origin = head_origin
    calls: list[tuple[str, ...]] = []

    def run_git(_repo: Path, arguments: Sequence[str]) -> str:
        call = tuple(arguments)
        calls.append(call)
        if call == ("branch", "--show-current"):
            return "main\n"
        if call == ("cat-file", "-e", f"{checker._BASE_COMMIT}^{{commit}}"):
            return ""
        if call == ("merge-base", "--is-ancestor", checker._BASE_COMMIT, "HEAD"):
            assert head
            return ""
        if call == ("rev-parse", "origin/main"):
            pytest.fail(f"origin unexpectedly used for admission: {origin}")
        pytest.fail(f"unexpected call: {call!r}")

    monkeypatch.setattr(checker, "_run_git", run_git)
    checker._validate_repository_lineage(REPO)
    assert len(calls) == 3


def test_checker_main_calls_gate_once_and_emits_one_compact_line(
    monkeypatch: pytest.MonkeyPatch,
    built: tuple[dict[str, bytes], list[tuple[Path, Path]]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    checker = _load_checker()
    artifacts, _calls = built
    gate_calls: list[int] = []

    def build(*, repo_root: Path, state_root: Path):
        assert repo_root == REPO and state_root == STATE
        gate_calls.append(1)
        return copy.deepcopy(artifacts)

    monkeypatch.setattr(
        checker.gate,
        "build_covapie_current11_task2_batch_descriptor_compiler_context_contract_gate_v1",
        build,
    )
    monkeypatch.setattr(checker, "_validate_repository_lineage", lambda _repo: None)
    monkeypatch.setattr(checker, "_repository_lifecycle", lambda _repo: "precommit-untracked")
    monkeypatch.setattr(checker, "_repository_snapshot", lambda _repo: ("same",))
    monkeypatch.setattr(checker, "_formal_snapshot", lambda _state: ("same",))
    assert checker._main(("--repo-root", str(REPO), "--state-root", str(STATE))) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out.count("\n") == 1
    assert "\n" not in captured.out[:-1]
    summary = json.loads(captured.out)
    assert summary["status"] == "PASS_CONTRACT_ONLY"
    assert summary["live_authority_build_count"] == 1
    assert summary["repository_unchanged"] is True
    assert summary["formal_carrier_and_routing_unchanged"] is True
    assert gate_calls == [1]


@pytest.mark.parametrize(
    "arguments",
    (
        (),
        ("--help",),
        ("--repo-root", str(REPO)),
        ("--state-root", str(STATE)),
        (
            "--repo-root",
            str(REPO),
            "--state-root",
            str(STATE),
            "--train",
            "x",
        ),
    ),
)
def test_checker_cli_rejects_missing_help_and_expanded_scope(
    arguments: tuple[str, ...]
) -> None:
    checker = _load_checker()
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        checker._main(arguments)


def test_repository_exact4_are_safe_precommit_or_clean_tracked_successor() -> None:
    status = subprocess.run(
        [
            "git",
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            *EXACT4,
        ],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    index = subprocess.run(
        ["git", "ls-files", "--stage", "--", *EXACT4],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    assert status.stderr == index.stderr == ""
    status_lines = status.stdout.splitlines()
    index_lines = index.stdout.splitlines()
    if status_lines:
        assert set(status_lines) == {f"?? {path}" for path in EXACT4}
        assert index_lines == []
    else:
        assert len(index_lines) == len(EXACT4)
        for row in index_lines:
            metadata, relative = row.split("\t", 1)
            mode, blob, stage = metadata.split()
            assert mode == "100644" and stage == "0" and relative in EXACT4
            worktree_blob = subprocess.run(
                ["git", "hash-object", "--no-filters", relative],
                cwd=REPO,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            ).stdout.strip()
            head_blob = subprocess.run(
                ["git", "rev-parse", f"HEAD:{relative}"],
                cwd=REPO,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            ).stdout.strip()
            assert blob == worktree_blob == head_blob
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
