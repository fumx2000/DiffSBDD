from __future__ import annotations

import ast
import hashlib
import importlib.util
import inspect
import json
import os
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Sequence

import pytest

from covalent_ext import (
    covapie_current11_task2_batch_index_remap_adapter_hot_loop_contract_gate_v1
    as gate,
)
from covalent_ext import (
    covapie_current11_task2_batch_index_remap_adapter_v1 as adapter_owner,
)


ROOT = Path(__file__).resolve().parents[1]
STATE = Path(
    "/cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/"
    "covapie-state"
)
CHECKER_PATH = (
    ROOT
    / "scripts/check_covapie_current11_task2_batch_index_remap_adapter_hot_loop_"
    "contract_gate_v1.py"
)


def _load_checker() -> ModuleType:
    specification = importlib.util.spec_from_file_location(
        "covapie_hot_loop_contract_checker_test_module",
        CHECKER_PATH,
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return gate.build_covapie_current11_task2_batch_index_remap_adapter_hot_loop_contract_gate_v1(
        repo_root=ROOT,
        state_root=STATE,
    )


@pytest.fixture(scope="module")
def parsed(artifacts: dict[str, bytes]) -> dict[str, dict[str, object]]:
    return {
        name: json.loads(payload.decode("utf-8"))
        for name, payload in artifacts.items()
    }


def _manual_digest(artifacts: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    digest.update(
        b"COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_ADAPTER_HOT_LOOP_"
        b"CONTRACT_GATE_V1\0"
    )
    for name in gate.STABLE_ARTIFACT_NAMES:
        encoded = name.encode("utf-8")
        payload = artifacts[name]
        digest.update(len(encoded).to_bytes(8, "big", signed=False))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big", signed=False))
        digest.update(payload)
    return digest.hexdigest()


def _subprocess_env() -> dict[str, str]:
    return {
        **os.environ,
        "PYTHONPATH": "src:.",
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def test_public_gate_exact1_keyword_only_signature() -> None:
    function = (
        gate.build_covapie_current11_task2_batch_index_remap_adapter_hot_loop_contract_gate_v1
    )
    signature = inspect.signature(function)
    assert gate.__all__ == (function.__name__,)
    assert tuple(signature.parameters) == ("repo_root", "state_root")
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    assert str(signature) == (
        "(*, repo_root: 'Path', state_root: 'Path') -> 'dict[str, bytes]'"
    )


def test_public_gate_rejects_positional_arguments() -> None:
    with pytest.raises(TypeError):
        gate.build_covapie_current11_task2_batch_index_remap_adapter_hot_loop_contract_gate_v1(
            ROOT,
            STATE,
        )


def test_silent_import() -> None:
    completed = subprocess.run(
        (
            sys.executable,
            "-B",
            "-c",
            (
                "from covalent_ext import "
                "covapie_current11_task2_batch_index_remap_adapter_hot_loop_"
                "contract_gate_v1"
            ),
        ),
        cwd=ROOT,
        env=_subprocess_env(),
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == b""
    assert completed.stderr == b""


def test_error_token_exact_and_fail_closed() -> None:
    assert gate.ERROR_TOKEN == (
        "COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_ADAPTER_HOT_LOOP_"
        "CONTRACT_GATE_V1_ERROR"
    )
    with pytest.raises(ValueError, match=f"^{gate.ERROR_TOKEN}$"):
        gate.build_covapie_current11_task2_batch_index_remap_adapter_hot_loop_contract_gate_v1(
            repo_root=Path("."),
            state_root=STATE,
        )


def test_exact6_order_and_builtin_bytes(artifacts: dict[str, bytes]) -> None:
    assert type(artifacts) is dict
    assert tuple(artifacts) == gate.ARTIFACT_NAMES
    assert gate.ARTIFACT_NAMES == (
        "current11_task2_batch_index_remap_adapter_hot_loop_manifest.json",
        "current11_task2_batch_index_remap_adapter_hot_loop_context_contract.json",
        "current11_task2_batch_index_remap_adapter_hot_loop_runtime_contract.json",
        "current11_task2_batch_index_remap_adapter_hot_loop_authority_and_freshness_contract.json",
        "current11_task2_batch_index_remap_adapter_hot_loop_negative_matrix.json",
        "current11_task2_batch_index_remap_adapter_hot_loop_contract_gate_report.json",
    )
    assert len(artifacts) == 6
    assert all(type(payload) is bytes for payload in artifacts.values())


def test_all_artifacts_are_canonical_json(artifacts: dict[str, bytes]) -> None:
    for payload in artifacts.values():
        value = json.loads(payload.decode("utf-8"))
        assert payload == (
            json.dumps(
                value,
                sort_keys=True,
                indent=2,
                ensure_ascii=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")


def test_all_artifacts_obey_byte_safety(artifacts: dict[str, bytes]) -> None:
    for payload in artifacts.values():
        assert 0 < len(payload) < 1024 * 1024
        assert not payload.startswith(b"\xef\xbb\xbf")
        assert b"\0" not in payload
        assert b"\r" not in payload
        assert payload.endswith(b"\n")
        assert not payload.endswith(b"\n\n")


def test_stable_digest_independent_framing(
    artifacts: dict[str, bytes],
    parsed: dict[str, dict[str, object]],
) -> None:
    digest = _manual_digest(artifacts)
    assert digest == gate._manual_stable_digest(artifacts)
    assert parsed[gate.REPORT_NAME]["stable_contract_digest"] == digest


def test_report_is_self_excluded_from_stable_digest(
    artifacts: dict[str, bytes],
) -> None:
    changed = dict(artifacts)
    changed[gate.REPORT_NAME] = b"{}\n"
    assert _manual_digest(changed) == _manual_digest(artifacts)
    assert gate.REPORT_NAME not in gate.STABLE_ARTIFACT_NAMES


def test_architecture_name_exact(parsed: dict[str, dict[str, object]]) -> None:
    manifest = parsed[gate.MANIFEST_NAME]
    report = parsed[gate.REPORT_NAME]
    assert gate.ARCHITECTURE_NAME == (
        "explicit_successor_authority_context_plus_output17_only_no_io_"
        "fast_path_v1"
    )
    assert manifest["architecture_name"] == gate.ARCHITECTURE_NAME
    assert report["architecture_name"] == gate.ARCHITECTURE_NAME


def test_current_adapter_unchanged_contract(
    parsed: dict[str, dict[str, object]],
) -> None:
    manifest = parsed[gate.MANIFEST_NAME]
    assert manifest["existing_slow_public_adapter_source_unchanged"] is True
    assert manifest["existing_slow_public_adapter_api_unchanged"] is True
    assert manifest["existing_slow_public_adapter_exact2_semantics_unchanged"] is True


def test_no_adapter_or_shared_kernel_refactor(
    parsed: dict[str, dict[str, object]],
) -> None:
    manifest = parsed[gate.MANIFEST_NAME]
    assert manifest["adapter_source_refactor_required"] is False
    assert manifest["shared_kernel_refactor_required"] is False
    assert manifest["full_remap_algorithm_copy_forbidden"] is True
    assert manifest["fast_path_reuses_frozen_adapter_private_pure_helpers"] is True


def test_future_public_api_exact2_names(
    parsed: dict[str, dict[str, object]],
) -> None:
    context = parsed[gate.CONTEXT_CONTRACT_NAME]
    names = [row["name"] for row in gate.FUTURE_PUBLIC_APIS]
    assert names == [
        "build_covapie_current11_task2_batch_index_remap_adapter_context_v1",
        "remap_covapie_current11_task2_batch_index_with_context_v1",
    ]
    assert context["future_product___all___exact2"] == names
    assert context["future_product_public_api_count"] == 2


def test_future_context_api_signature_exact(
    parsed: dict[str, dict[str, object]],
) -> None:
    context = parsed[gate.CONTEXT_CONTRACT_NAME]
    assert context["future_product_public_api_exact2"][0]["signature"] == (
        "(*, repo_root: Path, state_root: Path) -> object"
    )
    assert context["future_product_public_api_exact2"][0]["keyword_only"] is True


def test_future_fast_api_signature_exact(
    parsed: dict[str, dict[str, object]],
) -> None:
    context = parsed[gate.CONTEXT_CONTRACT_NAME]
    assert context["future_product_public_api_exact2"][1]["signature"] == (
        "(*, context: object, adapter_input: dict[str, object]) -> "
        "dict[str, object]"
    )
    assert context["future_product_public_api_exact2"][1]["keyword_only"] is True


def test_no_public_context_class(parsed: dict[str, dict[str, object]]) -> None:
    context = parsed[gate.CONTEXT_CONTRACT_NAME]
    assert context["public_context_class_allowed"] is False


def test_future_context_product_exact4_contract_is_frozen_and_disjoint_from_current_gate(
    parsed: dict[str, dict[str, object]],
) -> None:
    context = parsed[gate.CONTEXT_CONTRACT_NAME]
    expected = (
        "src/covalent_ext/covapie_current11_task2_batch_index_remap_adapter_"
        "context_v1.py",
        "scripts/check_covapie_current11_task2_batch_index_remap_adapter_"
        "context_v1.py",
        "tests/test_covapie_current11_task2_batch_index_remap_adapter_context_"
        "v1.py",
        "docs/covapie_current11_task2_batch_index_remap_adapter_context_v1_"
        "guide.md",
    )
    future_paths = tuple(context["future_context_product_exact4"])
    assert future_paths == gate.FUTURE_CONTEXT_PRODUCT_EXACT4 == expected
    assert context["future_context_product_path_count"] == 4
    assert len(set(future_paths)) == 4
    assert set(future_paths).isdisjoint(gate.REPOSITORY_EXACT4)
    for relative in future_paths:
        path = PurePosixPath(relative)
        assert not path.is_absolute()
        assert ".." not in path.parts
        assert str(path) == relative


def test_logical_context_exact20_order(
    parsed: dict[str, dict[str, object]],
) -> None:
    context = parsed[gate.CONTEXT_CONTRACT_NAME]
    assert tuple(context["logical_context_field_order"]) == (
        gate.LOGICAL_CONTEXT_FIELD_ORDER
    )
    assert len(gate.LOGICAL_CONTEXT_FIELD_ORDER) == 20
    assert context["logical_context_field_count"] == 20


def test_context_is_opaque_tamper_evident_and_immutable(
    parsed: dict[str, dict[str, object]],
) -> None:
    semantics = parsed[gate.CONTEXT_CONTRACT_NAME]["context_semantics"]
    assert semantics["opaque"] is True
    assert semantics["caller_not_inspect_for_contract"] is True
    assert semantics["tamper_evident"] is True
    assert semantics["semantically_immutable"] is True
    assert semantics["deep_immutable_representation_required"] is True


def test_context_seal_and_corruption_fail_closed(
    parsed: dict[str, dict[str, object]],
) -> None:
    semantics = parsed[gate.CONTEXT_CONTRACT_NAME]["context_semantics"]
    assert semantics["fast_validates_type_version_and_seal"] is True
    assert semantics["construction_seal_covers_all_semantic_payload"] is True
    assert semantics["altered_or_corrupted_context_fails_closed"] is True
    assert semantics["caller_semantic_mutation_allowed"] is False


def test_clean_context_acquisition_reconciliation_once(
    parsed: dict[str, dict[str, object]],
) -> None:
    acquisition = parsed[gate.CONTEXT_CONTRACT_NAME][
        "clean_tracked_successor_authority_acquisition"
    ]
    assert acquisition["reconciliation_public_build_count"] == 1
    assert acquisition["reconciliation_stable_digest_required"] == (
        gate.RECONCILIATION_STABLE_DIGEST
    )


def test_clean_context_acquisition_successor_once(
    parsed: dict[str, dict[str, object]],
) -> None:
    acquisition = parsed[gate.CONTEXT_CONTRACT_NAME][
        "clean_tracked_successor_authority_acquisition"
    ]
    assert acquisition["successor_public_build_count"] == 1
    assert acquisition["successor_stable5_digest_required"] == (
        gate.SUCCESSOR_STABLE5_DIGEST
    )


def test_context_direct_b2_zero_successor_internal_once(
    parsed: dict[str, dict[str, object]],
) -> None:
    acquisition = parsed[gate.CONTEXT_CONTRACT_NAME][
        "clean_tracked_successor_authority_acquisition"
    ]
    assert acquisition["successor_internal_B2_public_build_count"] == 1
    assert acquisition["context_builder_direct_B2_public_build_count"] == 0


def test_context_old_contract_and_historical_builders_zero(
    parsed: dict[str, dict[str, object]],
) -> None:
    acquisition = parsed[gate.CONTEXT_CONTRACT_NAME][
        "clean_tracked_successor_authority_acquisition"
    ]
    assert acquisition["adapter_contract_exact6_count"] == 0
    assert acquisition["historical_remap_public_gate_count"] == 0
    assert acquisition["historical_payload_builder_count"] == 0
    assert acquisition["historical_instance_builder_count"] == 0


def test_context_reconciliation_model_and_target_exact(
    parsed: dict[str, dict[str, object]],
) -> None:
    acquisition = parsed[gate.CONTEXT_CONTRACT_NAME][
        "clean_tracked_successor_authority_acquisition"
    ]
    assert acquisition["runtime_target_required"] == gate.RUNTIME_TARGET
    assert acquisition["selected_reconciliation_model_required"] == (
        gate.SELECTED_RECONCILIATION_MODEL
    )


def test_context_precommit_fixture_lifecycle(
    parsed: dict[str, dict[str, object]],
) -> None:
    profile = parsed[gate.CONTEXT_CONTRACT_NAME][
        "repository_lifecycle_contract"
    ]["precommit_untracked"]
    assert profile["real_public_context_builder_required_to_succeed"] is False
    assert profile["test_harness_exact_predecessor_artifact_injection_allowed"] is True
    assert profile["fixture_unit_and_candidate_only_validation"] is True
    assert profile["production_monkeypatch_allowed"] is False
    assert profile["production_git_status_hiding_allowed"] is False


def test_context_clean_successor_live_lifecycle(
    parsed: dict[str, dict[str, object]],
) -> None:
    profile = parsed[gate.CONTEXT_CONTRACT_NAME][
        "repository_lifecycle_contract"
    ]["clean_tracked_successor"]
    assert profile["real_reconciliation_public_build_once_required"] is True
    assert profile["real_successor_public_build_once_required"] is True
    assert profile["real_context_public_build_live_proof_required"] is True


def test_formal_build_validation_before_after(
    parsed: dict[str, dict[str, object]],
) -> None:
    formal = parsed[gate.CONTEXT_CONTRACT_NAME]["formal_build_time_validation"]
    assert formal["adapter_validate_formal_before_count"] == 1
    assert formal["adapter_validate_formal_after_count"] == 1
    assert formal["formal_before_must_equal_formal_after"] is True


def test_formal_semantic_identity_excludes_machine_facts(
    parsed: dict[str, dict[str, object]],
) -> None:
    formal = parsed[gate.CONTEXT_CONTRACT_NAME]["formal_build_time_validation"]
    assert formal["mount_id_is_semantic_identity"] is False
    assert formal["parent_mount_id_is_semantic_identity"] is False
    assert formal["mtime_is_semantic_identity"] is False
    assert formal["pid_is_semantic_identity"] is False


def test_successor_parser_reuses_exact5_low_level_helpers(
    parsed: dict[str, dict[str, object]],
) -> None:
    parser = parsed[gate.CONTEXT_CONTRACT_NAME]["successor_stable5_parser"]
    rows = parser["reused_low_level_helpers"]
    assert len(rows) == len(gate.SUCCESSOR_PARSE_HELPER_SIGNATURES) == 5
    assert [row["helper_name"] for row in rows] == list(
        gate.SUCCESSOR_PARSE_HELPER_SIGNATURES
    )


def test_successor_parser_has_no_old_report_or_synthetic_report(
    parsed: dict[str, dict[str, object]],
) -> None:
    parser = parsed[gate.CONTEXT_CONTRACT_NAME]["successor_stable5_parser"]
    assert parser["adapter_old_parse_contract_called"] is False
    assert parser["historical_old_report_required"] is False
    assert parser["synthetic_old_report_created"] is False
    assert parser["successor_report_independently_validated"] is True


def test_successor_parser_validation_coverage(
    parsed: dict[str, dict[str, object]],
) -> None:
    coverage = parsed[gate.CONTEXT_CONTRACT_NAME]["successor_stable5_parser"][
        "validation_coverage"
    ]
    assert len(coverage) == 11
    assert "exact11_sample_order" in coverage
    assert "exact22_authority_roles" in coverage
    assert "selected_atom_identities" in coverage


def test_explicit_freshness_model_and_lifetime(
    parsed: dict[str, dict[str, object]],
) -> None:
    cache = parsed[gate.CONTEXT_CONTRACT_NAME]["cache_and_lifetime"]
    assert cache["context_freshness_model"] == "explicit_rebuild_by_owner"
    assert cache["context_build_frequency"] == (
        "once_per_process_or_ddp_rank_per_authority_snapshot"
    )
    assert cache["context_auto_refresh"] is False


def test_no_pickle_global_lru_singleton_or_cross_process_cache(
    parsed: dict[str, dict[str, object]],
) -> None:
    cache = parsed[gate.CONTEXT_CONTRACT_NAME]["cache_and_lifetime"]
    assert cache["pickle_contract_defined"] is False
    assert cache["global_registry_allowed"] is False
    assert cache["global_cache_allowed"] is False
    assert cache["lru_cache_allowed"] is False
    assert cache["hidden_mutable_cache_allowed"] is False
    assert cache["hidden_singleton_context_allowed"] is False
    assert cache["cross_process_shared_cache_allowed"] is False


def test_runtime_returns_builtin_output17_only(
    parsed: dict[str, dict[str, object]],
) -> None:
    returns = parsed[gate.RUNTIME_CONTRACT_NAME]["fast_return_contract"]
    assert returns["built_in_output17_dict_only"] is True
    assert returns["logical_output_object_count"] == 1
    assert returns["exact2_bytes_bundle_returned"] is False


def test_runtime_target_and_exact17_order(
    parsed: dict[str, dict[str, object]],
) -> None:
    runtime = parsed[gate.RUNTIME_CONTRACT_NAME]
    assert runtime["runtime_target"] == "current_public_adapter_output17_v1"
    assert tuple(runtime["output17_field_order"]) == gate.OUTPUT17_FIELD_ORDER
    assert tuple(adapter_owner._OUTPUT_FIELD_ORDER) == gate.OUTPUT17_FIELD_ORDER
    assert runtime["output17_field_count"] == 17


def test_runtime_success_whole_output17_exact(
    parsed: dict[str, dict[str, object]],
) -> None:
    runtime = parsed[gate.RUNTIME_CONTRACT_NAME]
    assert runtime[
        "same_exact_input_success_whole_output17_canonical_bytes_exact"
    ] is True


def test_runtime_failure_whole_output17_exact(
    parsed: dict[str, dict[str, object]],
) -> None:
    runtime = parsed[gate.RUNTIME_CONTRACT_NAME]
    assert runtime[
        "same_exact_input_failure_whole_output17_canonical_bytes_exact"
    ] is True
    assert runtime[
        "provenance_readiness_offsets_validity_null_and_bool_int_exact"
    ] is True


def test_historical_failure_not_runtime_golden_and_no_normalization(
    parsed: dict[str, dict[str, object]],
) -> None:
    runtime = parsed[gate.RUNTIME_CONTRACT_NAME]
    assert runtime["historical_private_failure_runtime_golden"] is False
    assert runtime["failure_normalization_forbidden"] is True


def test_old_and_new_report_absent_from_fast_return(
    parsed: dict[str, dict[str, object]],
) -> None:
    runtime = parsed[gate.RUNTIME_CONTRACT_NAME]
    returns = runtime["fast_return_contract"]
    assert runtime["old_adapter_report_returned_by_fast_path"] is False
    assert runtime["old_adapter_report_authoritative_for_fast_path"] is False
    assert returns["adapter_report_returned"] is False
    assert returns["new_fast_report_defined"] is False


def test_runtime_input_schema_exact_from_adapter(
    parsed: dict[str, dict[str, object]],
) -> None:
    input_contract = parsed[gate.RUNTIME_CONTRACT_NAME]["input_contract"]
    assert tuple(input_contract["field_order"]) == tuple(adapter_owner._INPUT_FIELD_ORDER)
    assert set(input_contract["required_fields"]) == set(adapter_owner._INPUT_REQUIRED)
    assert set(input_contract["optional_fields"]) == set(adapter_owner._INPUT_OPTIONAL)
    assert set(input_contract["legacy_aliases_forbidden"]) == set(
        adapter_owner._LEGACY_ALIASES
    )


def test_runtime_preserves_input_and_context(
    parsed: dict[str, dict[str, object]],
) -> None:
    runtime = parsed[gate.RUNTIME_CONTRACT_NAME]
    assert runtime["input_contract"]["caller_input_preserved"] is True
    assert runtime["context_contract"]["context_mutation_forbidden"] is True
    assert runtime["context_contract"][
        "context_rebuild_or_refresh_during_fast_call"
    ] is False


def test_fast_structural_matrix_exact15_zero(
    parsed: dict[str, dict[str, object]],
) -> None:
    counts = parsed[gate.RUNTIME_CONTRACT_NAME][
        "fast_per_batch_structural_acceptance_counts"
    ]
    assert len(counts) == 15
    assert set(counts.values()) == {0}


def test_fast_no_authority_or_historical_calls(
    parsed: dict[str, dict[str, object]],
) -> None:
    counts = parsed[gate.RUNTIME_CONTRACT_NAME][
        "fast_per_batch_structural_acceptance_counts"
    ]
    for field in (
        "reconciliation_public_build_count",
        "successor_public_build_count",
        "B2_public_build_count",
        "historical_contract_public_gate_count",
        "adapter_contract_exact6_count",
        "adapter_parse_contract_count",
        "adapter_validate_formal_count",
    ):
        assert counts[field] == 0


def test_fast_no_filesystem_git_subprocess_or_writes(
    parsed: dict[str, dict[str, object]],
) -> None:
    counts = parsed[gate.RUNTIME_CONTRACT_NAME][
        "fast_per_batch_structural_acceptance_counts"
    ]
    for field in (
        "formal_filesystem_read_count",
        "other_filesystem_read_count",
        "git_call_count",
        "subprocess_call_count",
        "report_generation_count",
        "artifact_write_count",
        "global_cache_lookup_count",
        "context_rebuild_count",
    ):
        assert counts[field] == 0


def test_no_latency_sla_or_benchmark_requirement(
    parsed: dict[str, dict[str, object]],
) -> None:
    performance = parsed[gate.RUNTIME_CONTRACT_NAME]["performance_boundary"]
    assert performance["absolute_latency_SLA_defined"] is False
    assert performance["benchmark_loop_required"] is False
    assert performance["one_shot_ms_threshold_forbidden"] is True
    assert performance["acceptance_is_structural_not_millisecond_threshold"] is True


def test_frozen_adapter_private_pure_helper_signatures_exact6(
    parsed: dict[str, dict[str, object]],
) -> None:
    orchestration = parsed[gate.RUNTIME_CONTRACT_NAME]["orchestration"]
    rows = orchestration["frozen_adapter_private_pure_helper_rows"]
    assert orchestration["frozen_adapter_private_pure_helper_count"] == 6
    assert [row["helper_name"] for row in rows] == list(
        gate.ADAPTER_PURE_HELPER_SIGNATURES
    )
    assert {row["helper_name"]: row["signature"] for row in rows} == (
        gate.ADAPTER_PURE_HELPER_SIGNATURES
    )


def test_no_full_algorithm_copy_or_second_precedence(
    parsed: dict[str, dict[str, object]],
) -> None:
    orchestration = parsed[gate.RUNTIME_CONTRACT_NAME]["orchestration"]
    assert orchestration["full_remap_algorithm_copy_forbidden"] is True
    assert orchestration["second_status_precedence_implementation_forbidden"] is True
    assert orchestration["status_precedence_owner"] == (
        "current_public_runtime_adapter._STATUS_ORDER"
    )


@pytest.mark.parametrize("owner_name", tuple(gate.OWNER_SPECS))
def test_published_owner_identity_exact(owner_name: str) -> None:
    row = gate._verify_owner_identity(ROOT, owner_name, gate.OWNER_SPECS[owner_name])
    assert row["head_and_worktree_exact"] is True
    assert row["git_mode"] == "100644"
    assert row["worktree_mode"] == "0644"
    assert row["commit_ancestor_or_equal_head"] is True


@pytest.mark.parametrize("evidence_name", tuple(gate.REVIEWED_EVIDENCE_SPECS))
def test_reviewed_evidence_identity_exact(evidence_name: str) -> None:
    spec = gate.REVIEWED_EVIDENCE_SPECS[evidence_name]
    path = STATE / spec["relative_path"]
    metadata = path.lstat()
    payload = path.read_bytes()
    assert stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
    assert stat.S_IMODE(metadata.st_mode) == 0o644
    assert (
        len(payload),
        payload.count(b"\n"),
        hashlib.sha256(payload).hexdigest(),
    ) == (spec["bytes"], spec["LF"], spec["sha256"])


def test_reviewed_lightweight_probe_contract_evidence(
    parsed: dict[str, dict[str, object]],
) -> None:
    report = parsed[gate.REPORT_NAME]
    assert report["lightweight_semantic_parity_probe_passed"] is True
    assert report["lightweight_success_case_count"] == 3
    assert report["lightweight_failure_case_count"] == 2
    assert report["lightweight_probe_rerun"] is False


def test_reviewed_one_heavy_structural_evidence(
    parsed: dict[str, dict[str, object]],
) -> None:
    report = parsed[gate.REPORT_NAME]
    assert report["one_heavy_cached_authority_C_and_D_ran"] is True
    assert report["one_heavy_formal_caching_output17_unchanged"] is True
    assert report["one_heavy_old_report_authoritative"] is False
    assert report["one_heavy_probe_rerun"] is False
    assert report["benchmark_or_timing_performed"] is False


def test_reconciliation_and_successor_digests_exact(
    parsed: dict[str, dict[str, object]],
) -> None:
    authority = parsed[gate.AUTHORITY_CONTRACT_NAME]
    assert authority["reconciliation_contract_digest"] == (
        "9250ff7948d353222f7a2c5b34fdfceee92ae03b73be802af80a214db004203f"
    )
    assert authority["successor_stable5_digest"] == (
        "2c6259312a3292181f00ebbaf787fab05e5a97e5b5475243f2fa8461b54dcdc6"
    )


def test_authority_explicit_rebuild_and_stale_wording(
    parsed: dict[str, dict[str, object]],
) -> None:
    authority = parsed[gate.AUTHORITY_CONTRACT_NAME]
    assert authority["context_freshness_model"] == "explicit_rebuild_by_owner"
    assert authority["context_build_does_not_auto_refresh"] is True
    assert authority["fast_path_silent_rebuild_or_refresh"] is False
    assert authority["per_batch_freshness_filesystem_check"] is False
    assert "owner must explicitly rebuild" in authority["stale_context_semantics"]
    assert "no current-filesystem" in authority["stale_context_semantics"]


def test_authority_per_rank_lifetime_and_device_owner(
    parsed: dict[str, dict[str, object]],
) -> None:
    authority = parsed[gate.AUTHORITY_CONTRACT_NAME]
    assert authority[
        "one_context_per_process_or_ddp_rank_per_authority_snapshot"
    ] is True
    assert authority["device_transition_authority_owned_by_successor_B2_chain"] is True
    assert authority["context_does_not_reinvent_device_policy"] is True


def test_compiler_context_not_integrated_and_risk_preserved(
    parsed: dict[str, dict[str, object]],
) -> None:
    authority = parsed[gate.AUTHORITY_CONTRACT_NAME]
    assert authority["current_adapter_directly_accepts_successor_exact6"] is False
    assert authority["current_compiler_context_uses_successor_authority"] is False
    assert authority["compiler_context_rebuild_device_identity_risk"] is True
    assert authority["compiler_context_integration_performed"] is False


def test_negative_matrix_exact48_unique_and_fail_closed(
    parsed: dict[str, dict[str, object]],
) -> None:
    negative = parsed[gate.NEGATIVE_MATRIX_NAME]
    case_ids = [row["case_id"] for row in negative["cases"]]
    assert negative["case_count"] == len(gate.NEGATIVE_CASES) == 48
    assert len(case_ids) == len(set(case_ids))
    assert case_ids == [case_id for case_id, unused in gate.NEGATIVE_CASES]
    assert negative["all_cases_fail_closed"] is True
    assert {row["required_verdict"] for row in negative["cases"]} == {
        "REJECT_FAIL_CLOSED"
    }


def test_negative_matrix_covers_required_boundaries(
    parsed: dict[str, dict[str, object]],
) -> None:
    case_ids = {
        row["case_id"] for row in parsed[gate.NEGATIVE_MATRIX_NAME]["cases"]
    }
    assert {
        "context_api_positional_expansion",
        "full_remap_algorithm_copied",
        "context_seal_missing",
        "fast_calls_successor",
        "fast_filesystem_read",
        "fast_failure_differs",
        "failure_normalization",
        "context_auto_refresh",
        "absolute_latency_sla",
        "training_ready_true",
        "canonical_mask_contract_changed",
    }.issubset(case_ids)


def test_canonical_mask_exact5_including_scaffold_only_b3(
    parsed: dict[str, dict[str, object]],
) -> None:
    expected = (
        ("warhead_only", "A"),
        ("linker_plus_warhead", "B"),
        ("scaffold_plus_warhead", "B2"),
        ("scaffold_only", "B3"),
        ("scaffold_plus_linker_plus_warhead", "C"),
    )
    assert gate.CANONICAL_MASKS == expected
    manifest = parsed[gate.MANIFEST_NAME]
    assert manifest["canonical_mask_count"] == 5
    assert manifest["canonical_masks_modified"] is False
    assert manifest["canonical_mask_semantics"][3] == {
        "semantic_name": "scaffold_only",
        "display_alias": "B3",
    }


def test_readiness_matches_current_repository_lifecycle(
    parsed: dict[str, dict[str, object]],
) -> None:
    lifecycle = gate._repository_lifecycle(ROOT)
    assert parsed[gate.REPORT_NAME]["repository_lifecycle"] == lifecycle
    readiness = parsed[gate.REPORT_NAME]["readiness"]
    expected_context_ready = lifecycle == "clean-tracked-successor"
    assert readiness["remap_adapter_hot_loop_contract_designed"] is True
    assert readiness["remap_adapter_hot_loop_contract_gate_implemented"] is True
    assert readiness["remap_adapter_hot_loop_contract_gate_passed"] is True
    assert readiness[
        "ready_for_remap_adapter_hot_loop_contract_gate_commit_review"
    ] is True
    assert readiness[
        "ready_for_remap_adapter_context_runtime_implementation"
    ] is expected_context_ready
    assert readiness["context_runtime_blocker"] == (
        "NONE"
        if expected_context_ready
        else "hot_loop_contract_gate_not_published"
    )


def test_public_build_clean_successor_authorizes_context_runtime_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        gate,
        "_repository_lifecycle",
        lambda unused: "clean-tracked-successor",
    )
    artifacts = gate.build_covapie_current11_task2_batch_index_remap_adapter_hot_loop_contract_gate_v1(
        repo_root=ROOT,
        state_root=STATE,
    )
    report = json.loads(artifacts[gate.REPORT_NAME].decode("utf-8"))
    readiness = report["readiness"]
    assert report["repository_lifecycle"] == "clean-tracked-successor"
    assert report["stable_contract_digest"] == (
        "19649350ac39697138d1c38155a762403fa148db5d7f9ebc518466756c40d1dc"
    )
    assert readiness[
        "ready_for_remap_adapter_context_runtime_implementation"
    ] is True
    assert readiness["context_runtime_blocker"] == "NONE"
    assert readiness[
        "ready_for_public_remap_adapter_hot_loop_contract_implementation"
    ] is False
    assert readiness["ready_for_dataloader_integration"] is False
    assert readiness["ready_for_training"] is False
    checker = _load_checker()
    assert checker._verify_artifacts(
        artifacts,
        lifecycle="clean-tracked-successor",
    ) == report


def test_readiness_rejects_unknown_lifecycle() -> None:
    with pytest.raises(gate._ContractInvariantError):
        gate._readiness("unknown-lifecycle")


def test_readiness_dataloader_model_loss_all_false(
    parsed: dict[str, dict[str, object]],
) -> None:
    readiness = parsed[gate.REPORT_NAME]["readiness"]
    assert readiness["ready_for_dataloader_integration"] is False
    assert readiness["ready_for_model_integration"] is False
    assert readiness["ready_for_loss_integration"] is False


def test_feature_reaudit_and_training_boundary(
    parsed: dict[str, dict[str, object]],
) -> None:
    readiness = parsed[gate.REPORT_NAME]["readiness"]
    assert readiness["feature_semantics_reaudit_required_before_training"] is True
    assert readiness["step12d_smoke_is_final_training_feature_contract"] is False
    assert readiness["ready_for_training"] is False
    assert readiness["checkpoint_bytes_read"] is False
    assert readiness["model_parameter_shape_change_required"] is False


def test_no_commit_or_push_claim(parsed: dict[str, dict[str, object]]) -> None:
    readiness = parsed[gate.REPORT_NAME]["readiness"]
    assert readiness["commit_created"] is False
    assert readiness["push_performed"] is False


def test_current_repository_lifecycle_is_supported() -> None:
    assert gate._repository_lifecycle(ROOT) in (
        "precommit-untracked",
        "clean-tracked-successor",
    )


@pytest.mark.parametrize(
    "lifecycle",
    ("precommit-untracked", "clean-tracked-successor"),
)
def test_repository_lifecycle_profiles_simulated(
    monkeypatch: pytest.MonkeyPatch,
    lifecycle: str,
) -> None:
    blob = "a" * 40

    def run_git(unused: Path, arguments: Sequence[str]) -> str:
        call = tuple(arguments)
        if call == ("status", "--porcelain=v1", "--untracked-files=all"):
            if lifecycle == "precommit-untracked":
                return "\n".join(
                    f"?? {path}" for path in gate.REPOSITORY_EXACT4
                )
            return ""
        if call == ("ls-files", "--stage", "--", *gate.REPOSITORY_EXACT4):
            if lifecycle == "precommit-untracked":
                return ""
            return "\n".join(
                f"100644 {blob} 0\t{path}" for path in gate.REPOSITORY_EXACT4
            )
        if call[:2] == ("hash-object", "--no-filters"):
            return blob + "\n"
        if call[0] == "rev-parse":
            return blob + "\n"
        pytest.fail(f"unexpected git call: {call!r}")

    monkeypatch.setattr(gate, "_run_git", run_git)
    assert gate._repository_lifecycle(ROOT) == lifecycle


def test_fifth_repository_file_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def run_git(unused: Path, arguments: Sequence[str]) -> str:
        call = tuple(arguments)
        if call == ("status", "--porcelain=v1", "--untracked-files=all"):
            return "\n".join(
                [
                    *(f"?? {path}" for path in gate.REPOSITORY_EXACT4),
                    "?? fifth-file.txt",
                ]
            )
        if call == ("ls-files", "--stage", "--", *gate.REPOSITORY_EXACT4):
            return ""
        pytest.fail(f"unexpected git call: {call!r}")

    monkeypatch.setattr(gate, "_run_git", run_git)
    with pytest.raises(gate._ContractInvariantError):
        gate._repository_lifecycle(ROOT)


def test_gate_source_has_no_forbidden_public_or_heavy_calls() -> None:
    source = (ROOT / gate.MODULE_PATH).read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden = {
        "build_covapie_current11_task2_batch_index_remap_adapter_v1",
        "build_covapie_current11_task2_batch_index_remap_contract_gate_v1",
        "build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1",
        "build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1",
        "build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1",
        "_contract_exact6",
        "_parse_contract",
        "_validate_formal",
        "_remap_engine",
        "_failure_output",
    }
    called = {
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Attribute, ast.Name))
    }
    assert called.isdisjoint(forbidden)


def test_gate_double_build_byte_identical(artifacts: dict[str, bytes]) -> None:
    second = gate.build_covapie_current11_task2_batch_index_remap_adapter_hot_loop_contract_gate_v1(
        repo_root=ROOT,
        state_root=STATE,
    )
    assert second == artifacts
    assert all(second[name] == artifacts[name] for name in gate.ARTIFACT_NAMES)


def test_gate_artifact_validator_rejects_tamper(
    artifacts: dict[str, bytes],
) -> None:
    changed = dict(artifacts)
    changed[gate.MANIFEST_NAME] = b"{}\n"
    with pytest.raises(gate._ContractInvariantError):
        gate._validate_artifacts(changed)


def test_checker_static_contract_validation() -> None:
    checker = _load_checker()
    checker._static_product_validation(ROOT)


def test_checker_independently_validates_owners_and_helper_signatures() -> None:
    checker = _load_checker()
    assert checker._owner_and_helper_validation(ROOT) == 6


def test_checker_cli_passes_with_one_compact_json_line() -> None:
    completed = subprocess.run(
        (
            sys.executable,
            "-B",
            str(CHECKER_PATH),
            "--repo-root",
            str(ROOT),
            "--state-root",
            str(STATE),
        ),
        cwd=ROOT,
        env=_subprocess_env(),
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stderr == b""
    assert completed.stdout.count(b"\n") == 1
    assert b" " not in completed.stdout.rstrip(b"\n")
    summary = json.loads(completed.stdout)
    assert summary["status"] == "PASS_REMAP_ADAPTER_HOT_LOOP_CONTRACT_ONLY"
    assert summary["repository_lifecycle"] in (
        "precommit-untracked",
        "clean-tracked-successor",
    )
    assert summary["public_gate_build_count"] == 2
    assert summary["double_build_byte_identical"] is True
    assert summary["frozen_adapter_private_pure_helper_count"] == 6
    assert summary[
        "ready_for_remap_adapter_hot_loop_contract_gate_commit_review"
    ] is True
    expected_context_ready = (
        summary["repository_lifecycle"] == "clean-tracked-successor"
    )
    assert summary[
        "ready_for_remap_adapter_context_runtime_implementation"
    ] is expected_context_ready
    assert summary["context_runtime_blocker"] == (
        "NONE"
        if expected_context_ready
        else "hot_loop_contract_gate_not_published"
    )
    assert summary["ready_for_training"] is False


def test_checker_cli_rejects_unknown_option() -> None:
    completed = subprocess.run(
        (
            sys.executable,
            "-B",
            str(CHECKER_PATH),
            "--repo-root",
            str(ROOT),
            "--state-root",
            str(STATE),
            "--device",
            "cpu",
        ),
        cwd=ROOT,
        env=_subprocess_env(),
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 1
    assert completed.stdout == b""
    assert completed.stderr == (gate.ERROR_TOKEN + "\n").encode("ascii")


def test_repo_and_reviewed_evidence_read_only_during_build() -> None:
    before_repository = gate._repository_snapshot(ROOT)
    before_evidence = gate._evidence_snapshot(STATE)
    gate.build_covapie_current11_task2_batch_index_remap_adapter_hot_loop_contract_gate_v1(
        repo_root=ROOT,
        state_root=STATE,
    )
    assert gate._repository_snapshot(ROOT) == before_repository
    assert gate._evidence_snapshot(STATE) == before_evidence
