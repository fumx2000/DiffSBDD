from __future__ import annotations

import builtins
import copy
import hashlib
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, Mapping, NoReturn

import numpy as np
import pytest
import torch

from dataset import ProcessedLigandPocketDataset
from covalent_ext import (
    covapie_current11_runtime_batch_observation_extractor_v1 as extractor,
)
from covalent_ext import (
    covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1
    as bridge,
)
from covalent_ext import (
    covapie_current11_task2_batch_descriptor_compiler_v1 as compiler,
)
from covalent_ext import (
    covapie_current11_task2_batch_index_remap_adapter_context_v1 as remap_context,
)
from covalent_ext import (
    covapie_current11_task2_batch_index_remap_adapter_v1 as remap_owner,
)
from covalent_ext import (
    covapie_current11_task2_runtime_caller_contract_gate_v1 as gate,
)
from scripts import (
    check_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1
    as bridge_checker,
)
from scripts import (
    check_covapie_current11_task2_runtime_caller_contract_gate_v1 as checker,
)


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT.parent / "covapie-state"
NPZ = (
    STATE
    / "formal-sidecars/current11-runtime-sample-and-role-order-carrier-v1/"
    "current11_runtime_sample_and_role_order_carrier.npz"
)
CHECKER = ROOT / gate._SCRIPT_PATH
CALLER_ERROR = "COVAPIE_CURRENT11_TASK2_RUNTIME_CALLER_V1_ERROR"
GATE_ERROR = "COVAPIE_CURRENT11_TASK2_RUNTIME_CALLER_CONTRACT_GATE_V1_ERROR"
CHECK_ERROR = (
    "COVAPIE_CURRENT11_TASK2_RUNTIME_CALLER_CONTRACT_GATE_V1_CHECK_ERROR"
)
_LIFECYCLE_STATUS = {
    "precommit-untracked": (
        "PASS_RUNTIME_CALLER_CONTRACT_GATE_PRECOMMIT_CANDIDATE_ONLY"
    ),
    "clean-tracked-successor": (
        "PASS_RUNTIME_CALLER_CONTRACT_GATE_PUBLISHED_SUCCESSOR"
    ),
}


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return gate.build_covapie_current11_task2_runtime_caller_contract_gate_v1(
        repo_root=ROOT,
        state_root=STATE,
    )


@pytest.fixture(scope="module")
def parsed(artifacts: dict[str, bytes]) -> dict[str, dict[str, object]]:
    return {
        name: json.loads(payload.decode("utf-8"))
        for name, payload in artifacts.items()
    }


@pytest.fixture(scope="module")
def runtime_bundle() -> dict[str, object]:
    lifecycle, _repository = gate._repository_lifecycle(ROOT)
    if lifecycle not in _LIFECYCLE_STATUS:
        raise AssertionError("unsupported_runtime_caller_gate_lifecycle")
    remap, acquisition = bridge_checker._acquire_remap_context(
        lifecycle=lifecycle,
        repo_root=ROOT,
        state_root=STATE,
    )
    compiler_context = (
        bridge.build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1(
            remap_context=remap
        )
    )
    dataset = ProcessedLigandPocketDataset(NPZ, center=False)
    return {
        "remap": remap,
        "compiler": compiler_context,
        "dataset": dataset,
        "acquisition": acquisition,
        "lifecycle": lifecycle,
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


def _manual_stable_digest(artifacts: Mapping[str, bytes]) -> str:
    digest = hashlib.sha256(
        b"COVAPIE_CURRENT11_TASK2_RUNTIME_CALLER_CONTRACT_GATE_V1\0"
    )
    for name in gate._STABLE_NAMES:
        encoded = name.encode("utf-8")
        payload = artifacts[name]
        digest.update(len(encoded).to_bytes(8, "big", signed=False))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big", signed=False))
        digest.update(payload)
    return digest.hexdigest()


def _batch_fingerprint(value: object) -> object:
    if isinstance(value, torch.Tensor):
        return (
            "tensor",
            id(value),
            str(value.dtype),
            str(value.device),
            tuple(value.shape),
            int(value._version),
            value.detach().cpu().clone(),
        )
    if type(value) is dict:
        return (
            "dict",
            id(value),
            tuple((key, _batch_fingerprint(item)) for key, item in value.items()),
        )
    if type(value) is list:
        return ("list", id(value), tuple(_batch_fingerprint(item) for item in value))
    if type(value) is tuple:
        return ("tuple", id(value), tuple(_batch_fingerprint(item) for item in value))
    return ("scalar", type(value).__name__, value)


def _fingerprint_equal(left: object, right: object) -> bool:
    if type(left) is tuple and type(right) is tuple:
        if len(left) != len(right):
            return False
        if left and left[0] == "tensor" and right[0] == "tensor":
            return left[:-1] == right[:-1] and torch.equal(left[-1], right[-1])
        return all(_fingerprint_equal(a, b) for a, b in zip(left, right))
    return left == right


def _programming_error(cause: Exception) -> NoReturn:
    raise ValueError(CALLER_ERROR) from cause


def _validate_exact_product(
    value: object,
    fields: tuple[str, ...],
    schema_version: str,
) -> dict[str, object]:
    if (
        type(value) is not dict
        or tuple(value) != fields
        or value.get("schema_version") != schema_version
    ):
        _programming_error(ValueError("malformed_product"))
    return value


def _test_only_contract_oracle(
    *,
    batch: dict[str, object],
    remap: object,
    compiler_context: object,
    extract_fn: Callable[..., dict[str, object]] = (
        extractor.extract_covapie_current11_runtime_batch_observation_v1
    ),
    compile_fn: Callable[..., dict[str, object]] = (
        bridge.compile_covapie_current11_task2_batch_descriptor_with_remap_handoff_context_v1
    ),
    remap_fn: Callable[..., dict[str, object]] = (
        remap_context.remap_covapie_current11_task2_batch_index_with_context_v1
    ),
) -> tuple[dict[str, object], dict[str, int]]:
    """Test oracle for the frozen contract; this is not a product caller."""
    counts = {"extractor": 0, "compiler": 0, "remap": 0}
    batch_before = _batch_fingerprint(batch)
    try:
        counts["extractor"] += 1
        observation = extract_fn(batch=batch)
    except Exception as error:
        if (
            str(error) == extractor._ERROR
            and getattr(error, "reason", None) in gate._EXTRACTOR_REASONS
        ):
            result = {
                "schema_version": gate._RESULT_SCHEMA_VERSION,
                "runtime_status": "extractor_failure",
                "failure_stage": "extractor",
                "failure_reason": error.reason,
                "compiler_status": None,
                "remap_status": None,
                "batch_sample_keys_or_none": None,
                "compiler_failure_output10_or_none": None,
                "remap_output17_or_none": None,
                "provenance": {"selected_architecture": gate._ARCHITECTURE},
                "readiness": dict(gate._READINESS),
            }
            return result, counts
        _programming_error(error)
    if not _fingerprint_equal(batch_before, _batch_fingerprint(batch)):
        _programming_error(ValueError("input_batch_mutated"))
    observation = _validate_exact_product(
        observation,
        gate._EXACT14_FIELDS,
        "covapie_current11_task2_batch_descriptor_compiler_input_v1",
    )
    observation_before = copy.deepcopy(observation)
    try:
        counts["compiler"] += 1
        output10 = compile_fn(context=compiler_context, observation=observation)
    except Exception as error:
        _programming_error(error)
    if observation != observation_before:
        _programming_error(ValueError("observation_mutated"))
    output10 = _validate_exact_product(
        output10,
        gate._COMPILER_OUTPUT_FIELDS,
        "covapie_current11_task2_batch_descriptor_compiler_output_v1",
    )
    compiler_status = output10["compiler_status"]
    if compiler_status == gate._COMPILER_OVERALL_SUCCESS_STATUS:
        if output10["failure_reason"] != "NONE":
            _programming_error(ValueError("compiler_success_failure_reason"))
    elif compiler_status in gate._COMPILER_STRUCTURED_FAILURE_STATUSES:
        if (
            output10["failure_reason"] != compiler_status
            or output10["adapter_input_exact18"] is not None
        ):
            _programming_error(ValueError("compiler_failure_invariant"))
        result = {
            "schema_version": gate._RESULT_SCHEMA_VERSION,
            "runtime_status": "compiler_failure",
            "failure_stage": "compiler",
            "failure_reason": output10["failure_reason"],
            "compiler_status": compiler_status,
            "remap_status": None,
            "batch_sample_keys_or_none": observation["batch_sample_keys"],
            "compiler_failure_output10_or_none": output10,
            "remap_output17_or_none": None,
            "provenance": {"selected_architecture": gate._ARCHITECTURE},
            "readiness": dict(gate._READINESS),
        }
        return result, counts
    else:
        _programming_error(ValueError("compiler_status_not_allowed_as_overall"))
    exact18 = _validate_exact_product(
        output10["adapter_input_exact18"],
        gate._EXACT18_FIELDS,
        "covapie_current11_task2_batch_index_remap_adapter_input_v1",
    )
    exact18_before = copy.deepcopy(exact18)
    try:
        counts["remap"] += 1
        output17 = remap_fn(context=remap, adapter_input=exact18)
    except Exception as error:
        _programming_error(error)
    if exact18 != exact18_before:
        _programming_error(ValueError("exact18_mutated"))
    output17 = _validate_exact_product(
        output17,
        gate._REMAP_OUTPUT_FIELDS,
        "covapie_current11_task2_batch_index_remap_adapter_output_v1",
    )
    remap_status = output17["remap_status"]
    if remap_status == gate._REMAP_OVERALL_SUCCESS_STATUS:
        if output17["failure_reason"] != "NONE":
            _programming_error(ValueError("remap_success_failure_reason"))
        success = True
    elif remap_status in gate._REMAP_STRUCTURED_FAILURE_STATUSES:
        if output17["failure_reason"] != remap_status:
            _programming_error(ValueError("remap_failure_invariant"))
        success = False
    else:
        _programming_error(ValueError("remap_status_not_allowed_as_overall"))
    result = {
        "schema_version": gate._RESULT_SCHEMA_VERSION,
        "runtime_status": "full_success" if success else "remap_failure",
        "failure_stage": "none" if success else "remap",
        "failure_reason": output17["failure_reason"],
        "compiler_status": compiler_status,
        "remap_status": remap_status,
        "batch_sample_keys_or_none": observation["batch_sample_keys"],
        "compiler_failure_output10_or_none": None,
        "remap_output17_or_none": output17,
        "provenance": {"selected_architecture": gate._ARCHITECTURE},
        "readiness": dict(gate._READINESS),
    }
    return result, counts


def _collate(dataset: ProcessedLigandPocketDataset, indices: list[int]) -> dict[str, object]:
    return dataset.collate_fn([dataset[index] for index in indices])


def test_public_signature_error_and_silent_import() -> None:
    build = gate.build_covapie_current11_task2_runtime_caller_contract_gate_v1
    assert gate.__all__ == (build.__name__,)
    assert str(inspect.signature(build)) == (
        "(*, repo_root: 'Path', state_root: 'Path') -> 'dict[str, bytes]'"
    )
    with pytest.raises(TypeError):
        build(ROOT, STATE)
    completed = subprocess.run(
        (
            sys.executable,
            "-B",
            "-c",
            "from covalent_ext import covapie_current11_task2_runtime_caller_contract_gate_v1",
        ),
        cwd=ROOT,
        env=_environment(),
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == b""


def test_exact7_names_types_canonical_and_deterministic(
    artifacts: dict[str, bytes],
) -> None:
    assert tuple(artifacts) == gate._ARTIFACT_NAMES
    assert len(artifacts) == 7
    second = gate.build_covapie_current11_task2_runtime_caller_contract_gate_v1(
        repo_root=ROOT,
        state_root=STATE,
    )
    assert artifacts == second
    for payload in artifacts.values():
        value = json.loads(payload.decode("utf-8"))
        assert type(value) is dict
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


def test_stable_digest_independent_and_report_self_excluded(
    artifacts: dict[str, bytes], parsed: dict[str, dict[str, object]]
) -> None:
    digest = _manual_stable_digest(artifacts)
    assert digest == checker._STABLE_CONTRACT_DIGEST
    assert parsed[gate._REPORT]["stable_contract_digest"] == digest
    changed = dict(artifacts)
    changed[gate._REPORT] += b"x"
    assert _manual_stable_digest(changed) == digest


def test_repository_environment_identity_and_pins(
    parsed: dict[str, dict[str, object]]
) -> None:
    framework = parsed[gate._FRAMEWORK]
    declared = framework["repository_declared_environment"]
    assert declared == {
        "python": "3.10.4",
        "pytorch": "2.0.1=*cuda11.8*",
        "cudatoolkit": "11.8",
        "pytorch_lightning": "1.8.4",
        "environment_yaml_identity": {
            "mode": "0644",
            "bytes": 505,
            "LF": 29,
            "sha256": "a63682607def274b362787a2bd9250a9192a1b898b13632285725901401ea156",
            "git_blob": "9af8f3507cb691a0271bff36ba5341025c3a8bda",
        },
        "authority_role": "primary_reproducible_compatibility_baseline",
    }
    assert "observed_active_interpreter_environment" not in framework
    gate._validate_environment(ROOT)


def _synthetic_clean_git(
    *, head: str, origin: str, ahead: int, behind: int,
) -> Callable[[Path, tuple[str, ...]], str]:
    blob = "a" * 40
    index = "".join(
        f"100644 {blob} 0\t{relative}\n"
        for relative in gate._REPOSITORY_EXACT4
    )

    def run(unused_root: Path, arguments: tuple[str, ...]) -> str:
        del unused_root
        if arguments == ("branch", "--show-current"):
            return "main\n"
        if arguments == ("rev-parse", "HEAD"):
            return head + "\n"
        if arguments == ("rev-parse", "origin/main"):
            return origin + "\n"
        if arguments == (
            "rev-list", "--left-right", "--count", "HEAD...origin/main"
        ):
            return f"{ahead}\t{behind}\n"
        if arguments == ("log", "-1", "--format=%s", "HEAD"):
            return "synthetic clean successor\n"
        if arguments == ("status", "--porcelain=v1", "--untracked-files=all"):
            return ""
        if arguments == ("ls-files", "--stage", "--", *gate._REPOSITORY_EXACT4):
            return index
        if arguments == ("merge-base", "--is-ancestor", gate._BASE_COMMIT, "HEAD"):
            return ""
        if arguments[:3] == ("hash-object", "--no-filters", "--"):
            return blob + "\n"
        if arguments[0] == "rev-parse" and arguments[1].startswith("HEAD:"):
            return blob + "\n"
        raise AssertionError(arguments)

    return run


def test_clean_tracked_successor_requires_published_origin(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    published = "b" * 40
    monkeypatch.setattr(
        gate,
        "_run_git",
        _synthetic_clean_git(head=published, origin=published, ahead=0, behind=0),
    )
    lifecycle, repository = gate._repository_lifecycle(ROOT)
    assert lifecycle == "clean-tracked-successor"
    assert repository["head"] == repository["origin_main"] == published
    assert repository["ahead"] == repository["behind"] == 0


def test_clean_committed_unpushed_successor_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        gate,
        "_run_git",
        _synthetic_clean_git(
            head="b" * 40,
            origin=gate._BASE_COMMIT,
            ahead=1,
            behind=0,
        ),
    )
    with pytest.raises(ValueError, match=f"^{GATE_ERROR}$"):
        gate._repository_lifecycle(ROOT)


def test_clean_committed_behind_origin_successor_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        gate,
        "_run_git",
        _synthetic_clean_git(
            head=gate._BASE_COMMIT,
            origin="c" * 40,
            ahead=0,
            behind=1,
        ),
    )
    with pytest.raises(ValueError, match=f"^{GATE_ERROR}$"):
        gate._repository_lifecycle(ROOT)


def test_lightning_1_8_4_official_source_evidence_and_scope(
    parsed: dict[str, dict[str, object]]
) -> None:
    framework = parsed[gate._FRAMEWORK]
    sources = framework["official_pytorch_lightning_1_8_4_source_evidence"]
    assert len(sources) == 6
    assert [row["relative_path"] for row in sources] == [
        row[0] for row in gate._PL_1_8_4_SOURCES
    ]
    assert all(len(row["sha256"]) == 64 for row in sources)
    assert all("/1.8.4/" in row["official_source_url"] for row in sources)
    assert framework["audited_order"] == [
        "DataLoader_output",
        "on_before_batch_transfer",
        "transfer_batch_to_device",
        "on_after_batch_transfer",
        "training_validation_test_step",
    ]
    assert framework["single_device_supported_scope"] is True
    assert framework["DDP_supported_scope"] is True
    assert framework["DataParallel_not_supported_by_this_v1"] is True
    assert framework["rank_main_process_hook_not_dataloader_worker"] is True
    assert framework["worker_context_pickle_required"] is False
    assert framework["arbitrary_lightning_version_or_strategy_claimed"] is False


def test_2_6_5_snapshot_is_historical_corroboration_not_current_claim(
    parsed: dict[str, dict[str, object]]
) -> None:
    framework = parsed[gate._FRAMEWORK]
    snapshot = framework["corroborating_engineering_environment_snapshot"]
    assert snapshot == {
        "python_executable": "/usr/bin/python",
        "python": "3.12.0",
        "pytorch": "2.5.1+cu124",
        "pytorch_lightning": "2.6.5",
        "snapshot_scope": "design_audit_observation_only",
        "dependency_authority": False,
        "runtime_execution_environment_requirement": False,
        "checker_current_environment_claim": False,
    }
    assert framework["current_environment_exact_version_required"] is False
    assert framework["current_environment_not_required"] is True
    assert framework[
        "corroborating_2_6_5_order_supports_declared_baseline"
    ] is True


def test_active_interpreter_exact_version_independence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "executable", "/synthetic/non_authority/python")
    monkeypatch.setattr(torch, "__version__", "0.0.synthetic")
    artifacts = gate.build_covapie_current11_task2_runtime_caller_contract_gate_v1(
        repo_root=ROOT,
        state_root=STATE,
    )
    framework = json.loads(artifacts[gate._FRAMEWORK].decode("utf-8"))
    assert framework["current_environment_exact_version_required"] is False
    assert framework["current_environment_not_required"] is True
    gate_source = (ROOT / gate._MODULE_PATH).read_text(encoding="utf-8")
    checker_source = (ROOT / gate._SCRIPT_PATH).read_text(encoding="utf-8")
    assert "import pytorch_lightning" not in gate_source + checker_source
    assert "observed_active_pytorch_lightning" not in checker_source


def test_exact11_terminal_and_retention_contract(
    parsed: dict[str, dict[str, object]]
) -> None:
    schema = parsed[gate._RESULT_SCHEMA]
    assert schema["runtime_result_schema_version"] == gate._RESULT_SCHEMA_VERSION
    assert schema["field_order"] == list(gate._RESULT_FIELDS)
    assert schema["exact_field_count"] == 11
    assert schema["terminal_classes"] == list(gate._TERMINAL_CLASSES)
    assert schema["success_output10_retained"] is False
    assert schema["success_exact18_retained"] is False
    assert schema["compiler_failure_output10_retention"] == "whole_exact_output10"
    assert schema["remap_output17_retention"] == "whole_exact_output17_when_remap_called"


def test_status_reason_and_exception_boundary_are_explicit_artifact_contracts(
    parsed: dict[str, dict[str, object]]
) -> None:
    routing = parsed[gate._ROUTING]
    assert routing["status_failure_reason_invariants"] == {
        "compiler_success_failure_reason_required": "NONE",
        "compiler_failure_reason_must_equal_compiler_status": True,
        "remap_success_failure_reason_required": "NONE",
        "remap_failure_reason_must_equal_remap_status": True,
        "status_failure_reason_inconsistency": "programming_error",
    }
    programming = routing["programming_error"]
    assert programming["caller_normalizes_Exception"] is True
    assert programming["caller_catches_BaseException"] is False
    assert programming["keyboard_interrupt_not_normalized_by_caller"] is True
    assert programming["system_exit_not_normalized_by_caller"] is True


def test_overall_status_eligibility_is_exact_artifact_contract(
    parsed: dict[str, dict[str, object]]
) -> None:
    routing = parsed[gate._ROUTING]
    assert routing["compiler_overall_success_status"] == "COMPILED_EXACT"
    assert routing["compiler_component_only_non_overall_statuses"] == [
        "JOINT_LAYOUT_UNAVAILABLE"
    ]
    assert routing["compiler_structured_failure_statuses"] == list(
        gate._COMPILER_STRUCTURED_FAILURE_STATUSES
    )
    assert routing["remap_overall_success_status"] == "REMAPPED_EXACT"
    assert routing["remap_non_overall_statuses"] == [
        "NOT_IN_BATCH",
        "JOINT_INDEX_SPACE_UNAVAILABLE",
    ]
    assert routing["remap_structured_failure_statuses"] == list(
        gate._REMAP_STRUCTURED_FAILURE_STATUSES
    )
    assert routing["known_but_non_overall_status_seen_as_overall"] == (
        "programming_error"
    )
    assert routing["compiler_failure"]["compiler_status_must_be_in"] == list(
        gate._COMPILER_STRUCTURED_FAILURE_STATUSES
    )
    assert routing["remap_failure"]["remap_status_must_be_in"] == list(
        gate._REMAP_STRUCTURED_FAILURE_STATUSES
    )


def test_zero_conversion_deep_exact_and_product_sources() -> None:
    gate._validate_product_contracts(ROOT)
    assert extractor._FIELDS == compiler._INPUT_FIELDS == gate._EXACT14_FIELDS
    assert compiler._EXACT18_FIELDS == remap_owner._INPUT_FIELD_ORDER
    assert compiler._EXACT18_FIELDS == gate._EXACT18_FIELDS
    assert gate._COMPILER_OUTPUT_FIELDS == compiler._OUTPUT_FIELDS
    assert gate._REMAP_OUTPUT_FIELDS == remap_owner._OUTPUT_FIELD_ORDER
    assert compiler._STATUS_ORDER == (
        gate._COMPILER_OVERALL_SUCCESS_STATUS,
        *gate._COMPILER_COMPONENT_ONLY_NON_OVERALL_STATUSES,
        *gate._COMPILER_STRUCTURED_FAILURE_STATUSES,
    )
    assert remap_owner._STATUS_ORDER == (
        gate._REMAP_OVERALL_SUCCESS_STATUS,
        gate._REMAP_NON_OVERALL_STATUSES[0],
        *gate._REMAP_STRUCTURED_FAILURE_STATUSES[:-1],
        gate._REMAP_NON_OVERALL_STATUSES[1],
        gate._REMAP_STRUCTURED_FAILURE_STATUSES[-1],
    )


@pytest.mark.parametrize(
    "owner_name",
    (
        "covapie_current11_task2_batch_descriptor_compiler_v1.py",
        "covapie_current11_task2_batch_index_remap_adapter_v1.py",
    ),
)
def test_pinned_owner_overall_status_order_drift_fails_closed(
    monkeypatch: pytest.MonkeyPatch, owner_name: str,
) -> None:
    original = gate._literal_assignment

    def drift(path: Path, name: str) -> object:
        value = original(path, name)
        if path.name == owner_name and name == "_STATUS_ORDER":
            return tuple(reversed(value))
        return value

    monkeypatch.setattr(gate, "_literal_assignment", drift)
    with pytest.raises(ValueError, match=f"^{GATE_ERROR}$"):
        gate._validate_product_contracts(ROOT)


def test_lifecycle_no_io_masks_and_readiness(
    parsed: dict[str, dict[str, object]]
) -> None:
    lifecycle = parsed[gate._LIFECYCLE]
    startup = lifecycle["startup_lifecycle"]
    per_batch = lifecycle["per_batch_lifecycle"]
    calls = lifecycle["per_batch_call_vector"]
    assert startup["remap_context_build_count"] == 1
    assert startup["compiler_context_build_count"] == 1
    assert startup["same_remap_object_consumed_by_bridge"] is True
    assert startup["same_remap_context_used_for_fast_remap"] is True
    assert per_batch["remap_context_builds"] == 0
    assert per_batch["compiler_context_builds"] == 0
    assert per_batch["worker_context_build_count"] == 0
    assert per_batch["pickle_required"] is False
    assert per_batch["global_singleton"] is False
    zero_keys = set(calls) - {
        "extractor_calls",
        "compiler_bridge_fast_calls",
        "remap_context_fast_calls",
    }
    assert all(calls[key] == 0 for key in zero_keys)
    assert lifecycle["canonical_masks"] == [
        {"semantic_long_name": long_name, "display_alias": alias}
        for long_name, alias in gate._CANONICAL_MASKS
    ]
    assert lifecycle["canonical_mask_count"] == 5
    assert lifecycle["readiness"] == gate._READINESS


@pytest.mark.parametrize(
    ("case_id", "indices"),
    (
        ("canonical", list(range(11))),
        ("reversed", list(reversed(range(11)))),
        ("subset_10_4_0", [10, 4, 0]),
        ("singleton_10", [10]),
    ),
)
def test_pure_composition_four_success_cases_exact_call_vector_and_no_mutation(
    runtime_bundle: dict[str, object], case_id: str, indices: list[int]
) -> None:
    del case_id
    dataset = runtime_bundle["dataset"]
    assert isinstance(dataset, ProcessedLigandPocketDataset)
    batch = _collate(dataset, indices)
    before = _batch_fingerprint(batch)
    result, counts = _test_only_contract_oracle(
        batch=batch,
        remap=runtime_bundle["remap"],
        compiler_context=runtime_bundle["compiler"],
    )
    assert tuple(result) == gate._RESULT_FIELDS
    assert result["runtime_status"] == "full_success"
    assert result["compiler_status"] == "COMPILED_EXACT"
    assert result["remap_status"] == "REMAPPED_EXACT"
    assert result["compiler_failure_output10_or_none"] is None
    assert result["remap_output17_or_none"][
        "pair_values_joint_global_indices"
    ] is None
    assert result["remap_output17_or_none"]["failure_reason"] == "NONE"
    assert result["remap_output17_or_none"]["provenance"][
        "joint_layout_descriptor"
    ] is None
    assert result["remap_output17_or_none"]["provenance"][
        "joint_index_status"
    ] == "JOINT_INDEX_SPACE_UNAVAILABLE"
    assert counts == {"extractor": 1, "compiler": 1, "remap": 1}
    assert _fingerprint_equal(before, _batch_fingerprint(batch))


def test_extractor_failure_routes_and_short_circuits(runtime_bundle: dict[str, object]) -> None:
    dataset = runtime_bundle["dataset"]
    batch = _collate(dataset, [10])
    batch["lig_mask"] = batch["lig_mask"].clone()
    batch["lig_mask"][0] = 1
    result, counts = _test_only_contract_oracle(
        batch=batch,
        remap=runtime_bundle["remap"],
        compiler_context=runtime_bundle["compiler"],
    )
    assert result["runtime_status"] == "extractor_failure"
    assert result["failure_stage"] == "extractor"
    assert result["failure_reason"] == "invalid_membership"
    assert counts == {"extractor": 1, "compiler": 0, "remap": 0}


def test_compiler_structured_failure_preserves_whole_output10(
    runtime_bundle: dict[str, object]
) -> None:
    dataset = runtime_bundle["dataset"]
    batch = _collate(dataset, [10])
    batch["names"] = [np.str_("not-a-current11-sample")]
    captured: dict[str, object] = {}

    def compile_capture(**kwargs: object) -> dict[str, object]:
        output = bridge.compile_covapie_current11_task2_batch_descriptor_with_remap_handoff_context_v1(
            **kwargs
        )
        captured["output"] = output
        return output

    result, counts = _test_only_contract_oracle(
        batch=batch,
        remap=runtime_bundle["remap"],
        compiler_context=runtime_bundle["compiler"],
        compile_fn=compile_capture,
    )
    assert result["runtime_status"] == "compiler_failure"
    assert result["compiler_status"] == "BATCH_SAMPLE_KEY_UNKNOWN"
    assert result["compiler_failure_output10_or_none"] is captured["output"]
    assert captured["output"]["adapter_input_exact18"] is None
    assert counts == {"extractor": 1, "compiler": 1, "remap": 0}


def test_remap_structured_failure_preserves_whole_output17(
    runtime_bundle: dict[str, object]
) -> None:
    dataset = runtime_bundle["dataset"]
    batch = _collate(dataset, [10])
    observation = extractor.extract_covapie_current11_runtime_batch_observation_v1(
        batch=batch
    )
    output10 = bridge.compile_covapie_current11_task2_batch_descriptor_with_remap_handoff_context_v1(
        context=runtime_bundle["compiler"], observation=observation
    )
    malformed = copy.deepcopy(output10["adapter_input_exact18"])
    malformed["schema_version"] = "wrong"
    failure17 = remap_context.remap_covapie_current11_task2_batch_index_with_context_v1(
        context=runtime_bundle["remap"], adapter_input=malformed
    )
    assert failure17["remap_status"] != "REMAPPED_EXACT"

    def remap_failure(**unused: object) -> dict[str, object]:
        del unused
        return failure17

    result, counts = _test_only_contract_oracle(
        batch=batch,
        remap=runtime_bundle["remap"],
        compiler_context=runtime_bundle["compiler"],
        remap_fn=remap_failure,
    )
    assert result["runtime_status"] == "remap_failure"
    assert result["remap_output17_or_none"] is failure17
    assert counts == {"extractor": 1, "compiler": 1, "remap": 1}


@pytest.mark.parametrize(
    "case_id",
    (
        "compiler_success_reason_mismatch",
        "compiler_failure_reason_mismatch",
        "remap_success_reason_mismatch",
        "remap_failure_reason_mismatch",
    ),
)
def test_status_failure_reason_mismatch_is_programming_error(
    runtime_bundle: dict[str, object], case_id: str,
) -> None:
    dataset = runtime_bundle["dataset"]
    batch = _collate(dataset, [10])

    def compile_mismatch(**kwargs: object) -> dict[str, object]:
        output = bridge.compile_covapie_current11_task2_batch_descriptor_with_remap_handoff_context_v1(
            **kwargs
        )
        if case_id == "compiler_success_reason_mismatch":
            output["failure_reason"] = "ROLE_LENGTH_MISMATCH"
        else:
            output["compiler_status"] = "BATCH_SAMPLE_KEY_UNKNOWN"
            output["failure_reason"] = "BATCH_SAMPLE_KEY_INVALID"
            output["adapter_input_exact18"] = None
        return output

    def remap_mismatch(**kwargs: object) -> dict[str, object]:
        output = remap_context.remap_covapie_current11_task2_batch_index_with_context_v1(
            **kwargs
        )
        if case_id == "remap_success_reason_mismatch":
            output["failure_reason"] = "ROLE_MISMATCH"
        else:
            output["remap_status"] = "SCHEMA_VERSION_MISMATCH"
            output["failure_reason"] = "ROLE_MISMATCH"
        return output

    overrides: dict[str, Callable[..., dict[str, object]]] = {}
    if case_id.startswith("compiler_"):
        overrides["compile_fn"] = compile_mismatch
    else:
        overrides["remap_fn"] = remap_mismatch
    with pytest.raises(ValueError, match=f"^{CALLER_ERROR}$") as captured:
        _test_only_contract_oracle(
            batch=batch,
            remap=runtime_bundle["remap"],
            compiler_context=runtime_bundle["compiler"],
            **overrides,
        )
    assert captured.value.__cause__ is not None


@pytest.mark.parametrize(
    ("stage", "status"),
    (
        pytest.param(
            "compiler",
            "JOINT_LAYOUT_UNAVAILABLE",
            id="compiler_component_only_overall_negative",
        ),
        pytest.param(
            "remap",
            "NOT_IN_BATCH",
            id="remap_NOT_IN_BATCH_overall_negative",
        ),
        pytest.param(
            "remap",
            "JOINT_INDEX_SPACE_UNAVAILABLE",
            id="remap_JOINT_INDEX_SPACE_UNAVAILABLE_overall_negative",
        ),
    ),
)
def test_known_but_non_overall_status_is_programming_error_with_chaining(
    runtime_bundle: dict[str, object], stage: str, status: str,
) -> None:
    dataset = runtime_bundle["dataset"]
    batch = _collate(dataset, [10])

    def compiler_non_overall(**kwargs: object) -> dict[str, object]:
        output = bridge.compile_covapie_current11_task2_batch_descriptor_with_remap_handoff_context_v1(
            **kwargs
        )
        output["compiler_status"] = status
        output["failure_reason"] = status
        output["adapter_input_exact18"] = None
        return output

    def remap_non_overall(**kwargs: object) -> dict[str, object]:
        output = remap_context.remap_covapie_current11_task2_batch_index_with_context_v1(
            **kwargs
        )
        output["remap_status"] = status
        output["failure_reason"] = status
        return output

    override = (
        {"compile_fn": compiler_non_overall}
        if stage == "compiler"
        else {"remap_fn": remap_non_overall}
    )
    with pytest.raises(ValueError, match=f"^{CALLER_ERROR}$") as captured:
        _test_only_contract_oracle(
            batch=batch,
            remap=runtime_bundle["remap"],
            compiler_context=runtime_bundle["compiler"],
            **override,
        )
    assert captured.value.__cause__ is not None


@pytest.mark.parametrize(
    ("stage", "exception_type"),
    (
        ("extractor", KeyboardInterrupt),
        ("compiler", SystemExit),
    ),
)
def test_baseexception_control_flow_is_not_normalized_by_caller(
    runtime_bundle: dict[str, object],
    stage: str,
    exception_type: type[BaseException],
) -> None:
    dataset = runtime_bundle["dataset"]
    batch = _collate(dataset, [10])

    def interrupt(**unused: object) -> dict[str, object]:
        del unused
        raise exception_type()

    overrides: dict[str, Callable[..., dict[str, object]]] = {
        "extract_fn" if stage == "extractor" else "compile_fn": interrupt
    }
    with pytest.raises(exception_type):
        _test_only_contract_oracle(
            batch=batch,
            remap=runtime_bundle["remap"],
            compiler_context=runtime_bundle["compiler"],
            **overrides,
        )


@pytest.mark.parametrize(
    "stage",
    ("extractor_exception", "malformed_compiler", "unknown_compiler", "malformed_remap"),
)
def test_programming_error_normalization_and_chaining(
    runtime_bundle: dict[str, object], stage: str
) -> None:
    dataset = runtime_bundle["dataset"]
    batch = _collate(dataset, [10])

    def explode(**unused: object) -> dict[str, object]:
        del unused
        raise RuntimeError("boom")

    def malformed_compiler(**unused: object) -> dict[str, object]:
        del unused
        return {}

    def unknown_compiler(**kwargs: object) -> dict[str, object]:
        output = bridge.compile_covapie_current11_task2_batch_descriptor_with_remap_handoff_context_v1(
            **kwargs
        )
        output["compiler_status"] = "UNKNOWN"
        return output

    options: dict[str, dict[str, Callable[..., dict[str, object]]]] = {
        "extractor_exception": {"extract_fn": explode},
        "malformed_compiler": {"compile_fn": malformed_compiler},
        "unknown_compiler": {"compile_fn": unknown_compiler},
        "malformed_remap": {"remap_fn": malformed_compiler},
    }
    with pytest.raises(ValueError, match=f"^{CALLER_ERROR}$") as captured:
        _test_only_contract_oracle(
            batch=batch,
            remap=runtime_bundle["remap"],
            compiler_context=runtime_bundle["compiler"],
            **options[stage],
        )
    assert captured.value.__cause__ is not None


def test_input_mutation_negative_is_programming_error(runtime_bundle: dict[str, object]) -> None:
    dataset = runtime_bundle["dataset"]
    batch = _collate(dataset, [10])

    def mutate(*, batch: dict[str, object]) -> dict[str, object]:
        observation = extractor.extract_covapie_current11_runtime_batch_observation_v1(
            batch=batch
        )
        batch["names"].append("mutation")
        return observation

    with pytest.raises(ValueError, match=f"^{CALLER_ERROR}$"):
        _test_only_contract_oracle(
            batch=batch,
            remap=runtime_bundle["remap"],
            compiler_context=runtime_bundle["compiler"],
            extract_fn=mutate,
        )


def test_virtual_node_negative_fails_closed_without_strip_or_repair(
    runtime_bundle: dict[str, object]
) -> None:
    dataset = runtime_bundle["dataset"]
    batch = _collate(dataset, [10])
    batch["num_virtual_atoms"] = torch.tensor([1], dtype=torch.int64)
    result, counts = _test_only_contract_oracle(
        batch=batch,
        remap=runtime_bundle["remap"],
        compiler_context=runtime_bundle["compiler"],
    )
    assert result["runtime_status"] == "extractor_failure"
    assert result["failure_reason"] == "virtual_nodes_not_supported"
    assert counts == {"extractor": 1, "compiler": 0, "remap": 0}
    assert torch.equal(batch["num_virtual_atoms"], torch.tensor([1]))


def test_target_residue_extra_field_is_independent(runtime_bundle: dict[str, object]) -> None:
    dataset = runtime_bundle["dataset"]
    batch = _collate(dataset, [10])
    baseline = extractor.extract_covapie_current11_runtime_batch_observation_v1(
        batch=batch
    )
    batch["pocket_target_residue_atom_condition_indicator"] = torch.zeros(
        int(batch["pocket_coords"].shape[0]), dtype=torch.bool
    )
    observed = extractor.extract_covapie_current11_runtime_batch_observation_v1(
        batch=batch
    )
    assert observed == baseline
    result, unused_counts = _test_only_contract_oracle(
        batch=batch,
        remap=runtime_bundle["remap"],
        compiler_context=runtime_bundle["compiler"],
    )
    assert result["runtime_status"] == "full_success"


def test_runtime_bundle_acquisition_matches_exact_repository_lifecycle(
    runtime_bundle: dict[str, object],
) -> None:
    lifecycle, _repository = gate._repository_lifecycle(ROOT)
    if lifecycle not in _LIFECYCLE_STATUS:
        raise AssertionError("unsupported_runtime_caller_gate_lifecycle")
    assert runtime_bundle["lifecycle"] == lifecycle
    acquisition = runtime_bundle["acquisition"]
    expected_profile = {
        "precommit-untracked": {
            "test_harness_only": True,
            "real_public_remap_context_build_performed": False,
        },
        "clean-tracked-successor": {
            "test_harness_only": False,
            "real_public_remap_context_build_performed": True,
        },
    }[lifecycle]
    assert {
        key: acquisition[key] for key in expected_profile
    } == expected_profile
    assert acquisition["predecessor_public_call_counts"] == {
        "reconciliation": 1,
        "successor": 1,
        "B2": 1,
    }
    assert acquisition["formal_before_after_call_count"] == 2
    assert acquisition["production_monkeypatch_used"] is False


def test_context_same_object_call_counts_and_per_batch_no_io(
    runtime_bundle: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    acquisition = runtime_bundle["acquisition"]
    assert acquisition["predecessor_public_call_counts"] == {
        "reconciliation": 1,
        "successor": 1,
        "B2": 1,
    }
    dataset = runtime_bundle["dataset"]
    batch = _collate(dataset, [10])
    counts = {
        "remap_builder": 0,
        "compiler_builder": 0,
        "filesystem": 0,
        "subprocess": 0,
        "open": 0,
    }

    def forbidden(name: str) -> Callable[..., NoReturn]:
        def call(*args: object, **kwargs: object) -> NoReturn:
            del args, kwargs
            counts[name] += 1
            raise AssertionError(name)

        return call

    monkeypatch.setattr(
        remap_context,
        "build_covapie_current11_task2_batch_index_remap_adapter_context_v1",
        forbidden("remap_builder"),
    )
    monkeypatch.setattr(
        bridge,
        "build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1",
        forbidden("compiler_builder"),
    )
    monkeypatch.setattr(Path, "open", forbidden("filesystem"))
    monkeypatch.setattr(subprocess, "run", forbidden("subprocess"))
    monkeypatch.setattr(builtins, "open", forbidden("open"))
    result, call_vector = _test_only_contract_oracle(
        batch=batch,
        remap=runtime_bundle["remap"],
        compiler_context=runtime_bundle["compiler"],
    )
    assert result["runtime_status"] == "full_success"
    assert call_vector == {"extractor": 1, "compiler": 1, "remap": 1}
    assert counts == {key: 0 for key in counts}


def test_gate_is_static_and_does_not_import_product_or_framework_modules() -> None:
    source = (ROOT / gate._MODULE_PATH).read_text(encoding="utf-8")
    forbidden = (
        "import torch",
        "import pytorch_lightning",
        "from dataset import",
        "from covalent_ext import",
        "ProcessedLigandPocketDataset",
        "def run_covapie_current11_task2_runtime_caller_v1",
        "def on_before_batch_transfer",
    )
    assert all(token not in source for token in forbidden)


def test_owner_or_design_tamper_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    changed = dict(gate._DESIGN_REPORT_IDENTITY)
    changed["bytes"] = int(changed["bytes"]) + 1
    monkeypatch.setattr(gate, "_DESIGN_REPORT_IDENTITY", changed)
    with pytest.raises(ValueError, match=f"^{GATE_ERROR}$"):
        gate.build_covapie_current11_task2_runtime_caller_contract_gate_v1(
            repo_root=ROOT, state_root=STATE
        )


def test_checker_success_shape_readiness_and_silence() -> None:
    lifecycle, _repository = gate._repository_lifecycle(ROOT)
    if lifecycle not in _LIFECYCLE_STATUS:
        raise AssertionError("unsupported_runtime_caller_gate_lifecycle")
    completed = _checker()
    assert completed.returncode == 0
    assert completed.stderr == b""
    assert completed.stdout.count(b"\n") == 1
    result = json.loads(completed.stdout.decode("utf-8"))
    assert result["status"] == _LIFECYCLE_STATUS[lifecycle]
    assert result["repository_lifecycle"] == lifecycle
    assert result["repository_declared_pytorch_lightning"] == "1.8.4"
    assert result["corroborating_audit_snapshot_pytorch_lightning"] == "2.6.5"
    assert "observed_active_pytorch_lightning" not in result
    assert result["current_environment_exact_version_required"] is False
    assert result["current_environment_not_required"] is True
    assert result[
        "clean_tracked_successor_requires_HEAD_equals_origin_main"
    ] is True
    assert result["committed_unpushed_successor_rejected"] is True
    assert result["compiler_status_failure_reason_invariant_frozen"] is True
    assert result["remap_status_failure_reason_invariant_frozen"] is True
    assert result["compiler_overall_status_eligibility_frozen"] is True
    assert result["remap_overall_status_eligibility_frozen"] is True
    assert result["known_but_non_overall_status_rejected"] is True
    assert result["caller_catches_BaseException"] is False
    assert result["KeyboardInterrupt_not_normalized"] is True
    assert result["Option_B_retained"] is True
    assert result["runtime_result_exact_field_count"] == 11
    assert result["terminal_class_count"] == 5
    assert result["runtime_caller_contract_gate_implemented"] is True
    assert result["runtime_caller_contract_gate_passed"] is True
    assert result["ready_for_runtime_caller_implementation"] is True
    assert result["ready_for_dataloader_integration"] is False
    assert result["ready_for_model_integration"] is False
    assert result["ready_for_loss_integration"] is False
    assert result["feature_semantics_reaudit_required_before_training"] is True
    assert result["ready_for_training"] is False


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
def test_checker_invalid_cli_fails_closed(arguments: tuple[str, ...]) -> None:
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
