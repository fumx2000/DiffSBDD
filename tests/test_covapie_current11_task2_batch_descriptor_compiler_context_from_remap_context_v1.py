from __future__ import annotations

import copy
import gc
import hashlib
import inspect
import json
import os
import pickle
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1
    as bridge,
)
from covalent_ext import (
    covapie_current11_task2_batch_index_remap_adapter_context_v1
    as adapter_context,
)
from scripts import (
    check_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1
    as checker,
)


ROOT = Path(__file__).resolve().parents[1]
STATE = Path(
    "/cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/"
    "covapie-state"
)
CHECKER = ROOT / checker._EXACT4[1]
ERROR = (
    "COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_"
    "FROM_REMAP_CONTEXT_V1_ERROR"
)
CHECK_ERROR = (
    "COVAPIE_CURRENT11_TASK2_BATCH_DESCRIPTOR_COMPILER_CONTEXT_"
    "FROM_REMAP_CONTEXT_V1_CHECK_ERROR"
)


@pytest.fixture(scope="module")
def bundle() -> dict[str, object]:
    lifecycle, unused_repository = checker._repository_lifecycle(ROOT)
    del unused_repository
    remap, acquisition = checker._acquire_remap_context(
        lifecycle=lifecycle,
        repo_root=ROOT,
        state_root=STATE,
    )
    context, build_counts = checker._instrument_bridge_build(remap)
    vectors, compatibility = checker._reference_vectors(context)
    return {
        "lifecycle": lifecycle,
        "remap": remap,
        "acquisition": acquisition,
        "context": context,
        "build_counts": build_counts,
        "vectors": vectors,
        "compatibility": compatibility,
    }


def _environment() -> dict[str, str]:
    return {
        **os.environ,
        "PYTHONPATH": "src:.",
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def _checker(*extra: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        (
            sys.executable,
            "-B",
            str(CHECKER),
            "--repo-root",
            str(ROOT),
            "--state-root",
            str(STATE),
            *extra,
        ),
        cwd=ROOT,
        env=_environment(),
        capture_output=True,
        check=False,
    )


def _expect_error(action: object) -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        action()


def test_public_exact2_signatures_and_error_token() -> None:
    build = (
        bridge.build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1
    )
    compile_fast = (
        bridge.compile_covapie_current11_task2_batch_descriptor_with_remap_handoff_context_v1
    )
    assert bridge.__all__ == (build.__name__, compile_fast.__name__)
    assert str(inspect.signature(build)) == "(*, remap_context: 'object') -> 'object'"
    assert str(inspect.signature(compile_fast)) == (
        "(*, context: 'object', observation: 'dict[str, object]') -> "
        "'dict[str, object]'"
    )
    assert bridge._ERROR == ERROR
    with pytest.raises(TypeError):
        build(object())
    with pytest.raises(TypeError):
        compile_fast(object(), {})


def test_silent_import_and_no_public_context_class() -> None:
    completed = subprocess.run(
        (
            sys.executable,
            "-B",
            "-c",
            (
                "from covalent_ext import "
                "covapie_current11_task2_batch_descriptor_compiler_context_"
                "from_remap_context_v1"
            ),
        ),
        cwd=ROOT,
        env=_environment(),
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == b""
    assert "_BridgeContextV1" not in bridge.__all__
    assert all(not inspect.isclass(getattr(bridge, name)) for name in bridge.__all__)


def test_exact4_file_safety_and_static_dependency_boundary() -> None:
    for relative in checker._EXACT4:
        identity = checker._safe_file(ROOT / relative)
        metadata = (ROOT / relative).lstat()
        assert stat.S_ISREG(metadata.st_mode)
        assert not stat.S_ISLNK(metadata.st_mode)
        assert identity["mode"] == "0644"
    assert all(checker._static_architecture(ROOT).values())


def test_owner_identities_contract_constants_and_real_nul_seal_source() -> None:
    bridge._validate_owner_sources_v1()
    assert adapter_context.__all__ == bridge._ADAPTER_OWNER_EXACT2
    assert adapter_context.CONTEXT_SCHEMA_VERSION == (
        bridge._ADAPTER_CONTEXT_OWNER_SCHEMA_VERSION
    )
    assert adapter_context.CONTEXT_CONTRACT_VERSION == (
        bridge._ADAPTER_CONTEXT_OWNER_CONTRACT_VERSION
    )
    raw = (ROOT / checker._EXACT4[0]).read_bytes()
    assert b"\x00" not in raw
    assert b"\\x00" in raw
    assert bridge._SEAL_DOMAIN.endswith(b"\x00")
    assert not bridge._SEAL_DOMAIN.endswith(b"\\0")


def test_owner_identity_failure_precedes_materializer(
    monkeypatch: pytest.MonkeyPatch, bundle: dict[str, object]
) -> None:
    calls = 0
    original = adapter_context._validate_context_and_materialize

    def materializer(context: object) -> object:
        nonlocal calls
        calls += 1
        return original(context)

    monkeypatch.setattr(adapter_context, "_validate_context_and_materialize", materializer)
    monkeypatch.setattr(bridge, "_ADAPTER_OWNER_BYTES", 43579)
    _expect_error(
        lambda: bridge.build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1(
            remap_context=bundle["remap"]
        )
    )
    assert calls == 0


def test_owner_materializer_failure_called_once_and_stops(
    monkeypatch: pytest.MonkeyPatch, bundle: dict[str, object]
) -> None:
    calls = 0

    def fail(context: object) -> object:
        nonlocal calls
        del context
        calls += 1
        raise ValueError(adapter_context.ERROR_TOKEN)

    monkeypatch.setattr(adapter_context, "_validate_context_and_materialize", fail)
    _expect_error(
        lambda: bridge.build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1(
            remap_context=bundle["remap"]
        )
    )
    assert calls == 1


def test_precommit_or_clean_remap_acquisition_counts_and_restoration(
    bundle: dict[str, object],
) -> None:
    lifecycle = bundle["lifecycle"]
    acquisition = bundle["acquisition"]
    assert acquisition["predecessor_public_call_counts"] == {
        "reconciliation": 1,
        "successor": 1,
        "B2": 1,
    }
    assert acquisition["formal_before_after_call_count"] == 2
    assert acquisition["patch_restoration_passed"] is True
    assert acquisition["production_monkeypatch_used"] is False
    if lifecycle == "precommit-untracked":
        assert acquisition["test_harness_only"] is True
        assert acquisition["real_public_remap_context_build_performed"] is False
    else:
        assert acquisition["test_harness_only"] is False
        assert acquisition["real_public_remap_context_build_performed"] is True


def test_bridge_build_materializer_once_and_old_chain_zero(
    bundle: dict[str, object],
) -> None:
    counts = bundle["build_counts"]
    assert counts["adapter_private_materializer_calls"] == 1
    assert counts["owner_source_reads"] == 2
    assert all(
        value == 0
        for key, value in counts.items()
        if key not in ("adapter_private_materializer_calls", "owner_source_reads")
    )


def test_source_provider_readiness_golden_and_e3(bundle: dict[str, object]) -> None:
    source, provider, readiness = bridge._validate_context_and_materialize_v1(
        bundle["context"]
    )
    assert tuple(source) == bridge._SOURCE_FIELDS
    assert len(provider) == 11
    assert tuple(readiness) == tuple(sorted(readiness))
    assert readiness == dict(bridge._READINESS_EXACT24)
    assert readiness["runtime_batch_observation_extractor_implemented"] is False
    assert readiness["ready_for_runtime_batch_observation_extractor_design"] is True
    assert bundle["compatibility"][
        "historical_authority_compatibility_digest"
    ] == bridge._HISTORICAL_AUTHORITY_COMPATIBILITY_DIGEST
    source_payload = bridge._compact_json_v1(source)
    provider_payload = bridge._compact_json_v1(provider)
    assert len(source_payload) == 2735
    assert hashlib.sha256(source_payload).hexdigest() == (
        bridge._SOURCE_CANONICAL_SHA256
    )
    assert len(provider_payload) == 23364
    assert hashlib.sha256(provider_payload).hexdigest() == (
        bridge._PROVIDER_CANONICAL_SHA256
    )


def test_logical_exact20_seal_and_fixed_fields(bundle: dict[str, object]) -> None:
    context = bundle["context"]
    logical = bridge._logical_context_value_v1(context)
    assert tuple(logical) == bridge._LOGICAL_FIELD_ORDER
    assert len(logical) == 20
    assert tuple(logical[field] for field in bridge._LOGICAL_FIELD_ORDER[:16]) == (
        bridge._FIXED_SEMANTIC_VALUES
    )
    semantic = {field: logical[field] for field in bridge._LOGICAL_FIELD_ORDER[:19]}
    assert logical["construction_seal"] == bridge._construction_seal_v1(semantic)
    assert len(logical["construction_seal"]) == 64
    assert logical["context_contract_version"] == (
        "7de09322699eb9529486f49f5e5c1367317d63143e967f6223b010a4ef972c78"
    )


def test_context_deep_immutable_copy_pickle_and_no_remap_retention(
    bundle: dict[str, object],
) -> None:
    context = bundle["context"]
    remap = bundle["remap"]
    assert type(context._semantic) is bridge._FrozenMapV1
    assert not any(type(value) in (dict, list) for value in gc.get_referents(context))
    assert not any(value is remap for value in gc.get_referents(context))
    with pytest.raises(TypeError, match=f"^{ERROR}$"):
        copy.copy(context)
    with pytest.raises(TypeError, match=f"^{ERROR}$"):
        copy.deepcopy(context)
    with pytest.raises(TypeError, match=f"^{ERROR}$"):
        pickle.dumps(context)
    with pytest.raises(TypeError, match=f"^{ERROR}$"):
        context.__reduce__()
    with pytest.raises(TypeError, match=f"^{ERROR}$"):
        context.__reduce_ex__(4)


def test_same_remap_context_distinct_identity_deterministic_seal(
    bundle: dict[str, object],
) -> None:
    first = bundle["context"]
    second = bridge.build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1(
        remap_context=bundle["remap"]
    )
    first_logical = bridge._logical_context_value_v1(first)
    second_logical = bridge._logical_context_value_v1(second)
    assert first is not second
    assert first_logical == second_logical
    assert first_logical["construction_seal"] == second_logical["construction_seal"]


def test_wrong_builder_type_and_context_tamper_matrix(bundle: dict[str, object]) -> None:
    _expect_error(
        lambda: bridge.build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1(
            remap_context=object()
        )
    )
    matrix = checker._tamper_and_opacity(bundle["context"], bundle["remap"])
    assert matrix["caller_remap_context_retained"] is False
    assert matrix["reachable_builtin_mutable"] is False
    assert all(
        value
        for key, value in matrix.items()
        if key not in ("caller_remap_context_retained", "reachable_builtin_mutable")
    )


def test_success_exact4_whole_output10_parity(bundle: dict[str, object]) -> None:
    rows = bundle["vectors"]["output_parity_cases"]
    assert [row["case_id"] for row in rows] == list(checker._SUCCESS_IDS)
    for row in rows:
        output = bridge.compile_covapie_current11_task2_batch_descriptor_with_remap_handoff_context_v1(
            context=bundle["context"],
            observation=row["observation"],
        )
        assert output == row["existing_slow_output"]
        assert tuple(output) == checker._OUTPUT_FIELDS
        assert output["readiness"] == dict(bridge._READINESS_EXACT24)
        assert set(output) == set(checker._OUTPUT_FIELDS)


def test_hard_failure_exact5_whole_output10_parity(bundle: dict[str, object]) -> None:
    rows = bundle["vectors"]["representative_runtime_hard_failures"]
    assert [row["case_id"] for row in rows] == list(checker._FAILURE_IDS)
    for row in rows:
        output = bridge.compile_covapie_current11_task2_batch_descriptor_with_remap_handoff_context_v1(
            context=bundle["context"],
            observation=row["observation"],
        )
        assert output == row["existing_slow_output"]
        assert output["adapter_input_exact18"] is None
        assert output["compiler_status"] != "COMPILED_EXACT"
        assert tuple(output) == checker._OUTPUT_FIELDS


def test_valid_context_malformed_observation_returns_historical_failure(
    bundle: dict[str, object],
) -> None:
    output = bridge.compile_covapie_current11_task2_batch_descriptor_with_remap_handoff_context_v1(
        context=bundle["context"],
        observation={},
    )
    assert output["compiler_status"] == "BATCH_OBSERVATION_SCHEMA_MISMATCH"
    assert output["failure_reason"] == "BATCH_OBSERVATION_SCHEMA_MISMATCH"
    assert output["readiness"] == dict(bridge._READINESS_EXACT24)


def test_fast_kernel_once_per_call_and_all_old_paths_zero(bundle: dict[str, object]) -> None:
    counts, parity = checker._instrument_fast_calls(
        context=bundle["context"],
        vectors=bundle["vectors"],
    )
    assert counts["fast_call_count"] == 9
    assert counts["compiler_kernel_calls"] == 9
    assert all(
        value == 0
        for key, value in counts.items()
        if key not in ("fast_call_count", "compiler_kernel_calls")
    )
    assert all(parity.values())


def test_clean_profile_decision_support_without_fake_live_proof(
    bundle: dict[str, object],
) -> None:
    bridge_counts = bundle["build_counts"]
    fast_counts = {
        "fast_call_count": 2,
        "compiler_kernel_calls": 2,
        "adapter_private_materializer_calls": 0,
        "public_remap_context_builder_calls": 0,
        "public_remap_fast_calls": 0,
        "old_compiler_authority_calls": 0,
        "stable5_parser_calls": 0,
        "reconciliation_calls": 0,
        "successor_calls": 0,
        "B2_calls": 0,
        "formal_validation_calls": 0,
        "historical_compiler_contract_public_build_calls": 0,
        "owner_source_reads": 0,
        "context_rebuild_calls": 0,
        "subprocess_calls": 0,
    }
    clean = checker._readiness_profile(
        "clean-tracked-successor",
        acquisition={
            "real_public_remap_context_build_performed": True,
            "test_harness_only": False,
            "predecessor_public_call_counts": {
                "reconciliation": 1,
                "successor": 1,
                "B2": 1,
            },
            "formal_before_after_call_count": 2,
        },
        bridge_counts=bridge_counts,
        fast_counts=fast_counts,
        same_object_consumed=True,
    )
    assert clean["device_identity_risk_resolution_runtime_proven"] is True
    assert clean["ready_for_bridge_publication"] is True
    assert clean["ready_for_dataloader_integration"] is False
    precommit = checker._readiness_profile(
        "precommit-untracked",
        acquisition=bundle["acquisition"],
        bridge_counts=bridge_counts,
        fast_counts=fast_counts,
        same_object_consumed=True,
    )
    assert precommit["device_identity_risk_resolution_runtime_proven"] is False
    assert precommit["ready_for_bridge_commit_review"] is True
    assert precommit["ready_for_bridge_publication"] is False


def test_canonical_mask_exact5_includes_scaffold_only_b3() -> None:
    assert checker._CANONICAL_MASKS == (
        ("warhead_only", "A"),
        ("linker_plus_warhead", "B"),
        ("scaffold_plus_warhead", "B2"),
        ("scaffold_only", "B3"),
        ("scaffold_plus_linker_plus_warhead", "C"),
    )
    assert len(checker._CANONICAL_MASKS) == 5


def test_checker_success_shape_precommit_readiness_and_silence() -> None:
    completed = _checker()
    assert completed.returncode == 0
    assert completed.stderr == b""
    assert completed.stdout.count(b"\n") == 1
    result = json.loads(completed.stdout.decode("utf-8"))
    assert result["status"] in (
        "PASS_COMPILER_REMAP_CONTEXT_HANDOFF_PRECOMMIT_CANDIDATE_ONLY",
        "PASS_COMPILER_REMAP_CONTEXT_HANDOFF_RUNTIME_ONLY",
    )
    assert result["success_parity_case_count"] == 4
    assert result["hard_failure_parity_case_count"] == 5
    assert result["whole_output10_parity"] is True
    assert result["bridge_build_call_counts"][
        "adapter_private_materializer_calls"
    ] == 1
    assert result["production_monkeypatch_used"] is False
    assert result["ready_for_dataloader_integration"] is False
    assert result["ready_for_model_integration"] is False
    assert result["ready_for_loss_integration"] is False
    assert result["feature_semantics_reaudit_required_before_training"] is True
    assert result["ready_for_training"] is False
    if result["repository_lifecycle"] == "precommit-untracked":
        assert result["real_public_remap_context_build_performed"] is False
        assert result["device_identity_risk_resolution_runtime_proven"] is False
        assert result["ready_for_bridge_commit_review"] is True
        assert result["ready_for_bridge_publication"] is False


def test_checker_double_run_stdout_byte_identical() -> None:
    first = _checker()
    second = _checker()
    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == b""
    assert first.stdout == second.stdout


@pytest.mark.parametrize(
    "arguments",
    (
        (),
        ("--repo-root", str(ROOT)),
        ("--extra",),
        ("--repo-root", ".", "--state-root", str(STATE)),
    ),
)
def test_checker_invalid_cli_exact_error(arguments: tuple[str, ...]) -> None:
    completed = subprocess.run(
        (sys.executable, "-B", str(CHECKER), *arguments),
        cwd=ROOT,
        env=_environment(),
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 1
    assert completed.stdout == b""
    assert completed.stderr == (CHECK_ERROR + "\n").encode("utf-8")
