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
from typing import Callable, NoReturn

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
    covapie_current11_task2_batch_index_remap_adapter_context_v1 as remap_owner,
)
from covalent_ext import (
    covapie_current11_task2_runtime_caller_contract_gate_v1 as gate,
)
from covalent_ext import covapie_current11_task2_runtime_caller_v1 as caller
from scripts import (
    check_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1
    as bridge_checker,
)
from scripts import check_covapie_current11_task2_runtime_caller_v1 as checker


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT.parent / "covapie-state"
NPZ = STATE / checker._FORMAL_CARRIER
CHECKER = ROOT / checker._EXACT4[1]
CALLER_ERROR = "COVAPIE_CURRENT11_TASK2_RUNTIME_CALLER_V1_ERROR"
CHECK_ERROR = "COVAPIE_CURRENT11_TASK2_RUNTIME_CALLER_V1_CHECK_ERROR"


@pytest.fixture(scope="module")
def runtime_bundle() -> dict[str, object]:
    lifecycle, repository = checker._repository_lifecycle(ROOT)
    remap_context, acquisition = bridge_checker._acquire_remap_context(
        lifecycle=lifecycle,
        repo_root=ROOT,
        state_root=STATE,
    )
    compiler_context = (
        bridge.build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1(
            remap_context=remap_context,
        )
    )
    return {
        "lifecycle": lifecycle,
        "repository": repository,
        "remap_context": remap_context,
        "compiler_context": compiler_context,
        "acquisition": acquisition,
        "dataset": ProcessedLigandPocketDataset(NPZ, center=False),
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


def _collate(
    runtime_bundle: dict[str, object], indices: list[int]
) -> dict[str, object]:
    dataset = runtime_bundle["dataset"]
    assert isinstance(dataset, ProcessedLigandPocketDataset)
    return dataset.collate_fn([dataset[index] for index in indices])


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


def _run_counted(
    monkeypatch: pytest.MonkeyPatch,
    *,
    batch: dict[str, object],
    remap_context: object,
    compiler_context: object,
    extract_fn: Callable[..., dict[str, object]] | None = None,
    compile_fn: Callable[..., dict[str, object]] | None = None,
    remap_fn: Callable[..., dict[str, object]] | None = None,
) -> tuple[dict[str, object], dict[str, int], dict[str, object]]:
    extract_target = (
        caller._extractor_owner.extract_covapie_current11_runtime_batch_observation_v1
        if extract_fn is None
        else extract_fn
    )
    compile_target = (
        caller._compiler_owner.compile_covapie_current11_task2_batch_descriptor_with_remap_handoff_context_v1
        if compile_fn is None
        else compile_fn
    )
    remap_target = (
        caller._remap_owner.remap_covapie_current11_task2_batch_index_with_context_v1
        if remap_fn is None
        else remap_fn
    )
    counts = {"extractor": 0, "compiler": 0, "remap": 0}
    captured: dict[str, object] = {}

    def extract_wrapper(**kwargs: object) -> dict[str, object]:
        counts["extractor"] += 1
        output = extract_target(**kwargs)
        captured["observation"] = output
        return output

    def compile_wrapper(**kwargs: object) -> dict[str, object]:
        counts["compiler"] += 1
        observation = kwargs["observation"]
        before = copy.deepcopy(observation)
        output = compile_target(**kwargs)
        captured["observation_unchanged"] = observation == before
        captured["output10"] = output
        return output

    def remap_wrapper(**kwargs: object) -> dict[str, object]:
        counts["remap"] += 1
        exact18 = kwargs["adapter_input"]
        before = copy.deepcopy(exact18)
        output = remap_target(**kwargs)
        captured["exact18"] = exact18
        captured["exact18_unchanged"] = exact18 == before
        captured["output17"] = output
        return output

    with monkeypatch.context() as patch:
        patch.setattr(
            caller._extractor_owner,
            "extract_covapie_current11_runtime_batch_observation_v1",
            extract_wrapper,
        )
        patch.setattr(
            caller._compiler_owner,
            "compile_covapie_current11_task2_batch_descriptor_with_remap_handoff_context_v1",
            compile_wrapper,
        )
        patch.setattr(
            caller._remap_owner,
            "remap_covapie_current11_task2_batch_index_with_context_v1",
            remap_wrapper,
        )
        result = caller.run_covapie_current11_task2_runtime_caller_v1(
            batch=batch,
            remap_context=remap_context,
            compiler_context=compiler_context,
        )
    return result, counts, captured


def _real_failure17(runtime_bundle: dict[str, object]) -> dict[str, object]:
    batch = _collate(runtime_bundle, [10])
    observation = extractor.extract_covapie_current11_runtime_batch_observation_v1(
        batch=batch
    )
    output10 = bridge.compile_covapie_current11_task2_batch_descriptor_with_remap_handoff_context_v1(
        context=runtime_bundle["compiler_context"], observation=observation
    )
    malformed = copy.deepcopy(output10["adapter_input_exact18"])
    malformed["schema_version"] = "wrong"
    output17 = remap_owner.remap_covapie_current11_task2_batch_index_with_context_v1(
        context=runtime_bundle["remap_context"], adapter_input=malformed
    )
    assert output17["remap_status"] == "SCHEMA_VERSION_MISMATCH"
    return output17


def _assert_caller_error(call: Callable[[], object]) -> None:
    with pytest.raises(ValueError, match=f"^{CALLER_ERROR}$") as captured:
        call()
    assert captured.value.__cause__ is not None


def test_public_api_signature_all_and_silent_import() -> None:
    run = caller.run_covapie_current11_task2_runtime_caller_v1
    assert caller.__all__ == (run.__name__,)
    assert str(inspect.signature(run)) == (
        "(*, batch: 'dict[str, object]', remap_context: 'object', "
        "compiler_context: 'object') -> 'dict[str, object]'"
    )
    with pytest.raises(TypeError):
        run({}, object(), object())
    completed = subprocess.run(
        (
            sys.executable,
            "-B",
            "-c",
            "from covalent_ext import covapie_current11_task2_runtime_caller_v1",
        ),
        cwd=ROOT,
        env=_environment(),
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == b""


def test_contract_binding_exact_fields_statuses_provenance_and_readiness() -> None:
    assert caller._ERROR == gate._CALLER_ERROR
    assert caller._RESULT_FIELDS == gate._RESULT_FIELDS
    assert caller._EXACT14_FIELDS == gate._EXACT14_FIELDS
    assert caller._OUTPUT10_FIELDS == gate._COMPILER_OUTPUT_FIELDS
    assert caller._EXACT18_FIELDS == gate._EXACT18_FIELDS
    assert caller._OUTPUT17_FIELDS == gate._REMAP_OUTPUT_FIELDS
    assert caller._EXTRACTOR_REASONS == gate._EXTRACTOR_REASONS
    assert caller._COMPILER_STRUCTURED_FAILURES == (
        gate._COMPILER_STRUCTURED_FAILURE_STATUSES
    )
    assert caller._REMAP_STRUCTURED_FAILURES == gate._REMAP_STRUCTURED_FAILURE_STATUSES
    assert dict(caller._PROVENANCE_ITEMS) == {
        "selected_architecture": gate._ARCHITECTURE,
        "runtime_caller_contract_commit": checker._BASE_COMMIT,
        "runtime_caller_contract_digest": checker._CONTRACT_DIGEST,
        "runtime_caller_implemented": True,
    }
    readiness = dict(caller._READINESS_ITEMS)
    assert all(type(value) is bool for value in readiness.values())
    assert readiness == {
        "runtime_caller_contract_gate_implemented": True,
        "runtime_caller_contract_gate_passed": True,
        "runtime_caller_implemented": True,
        "ready_for_runtime_caller_implementation": False,
        "ready_for_dataloader_integration": False,
        "ready_for_model_integration": False,
        "ready_for_loss_integration": False,
        "feature_semantics_reaudit_required_before_training": True,
        "step12d_smoke_is_final_training_feature_contract": False,
        "ready_for_training": False,
    }


def test_product_import_boundary_and_static_no_io_source() -> None:
    source = (ROOT / checker._EXACT4[0]).read_text(encoding="utf-8")
    forbidden = (
        "import dataset",
        "from dataset",
        "import torch",
        "import pytorch_lightning",
        "lightning_modules",
        "runtime_caller_contract_gate_v1 as",
        "from pathlib",
        "import pathlib",
        "import subprocess",
        "repo_root",
        "state_root",
        "build_covapie_current11_task2_batch_index_remap_adapter_context_v1(",
        "build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1(",
        "open(",
        "Path(",
        "git ",
    )
    assert all(token not in source for token in forbidden)
    checker._validate_product_contract(ROOT)


def test_runtime_context_acquisition_profile(runtime_bundle: dict[str, object]) -> None:
    lifecycle = runtime_bundle["lifecycle"]
    acquisition = runtime_bundle["acquisition"]
    expected = {
        "precommit-untracked": (True, False),
        "clean-tracked-successor": (False, True),
    }[lifecycle]
    assert acquisition["test_harness_only"] is expected[0]
    assert acquisition["real_public_remap_context_build_performed"] is expected[1]
    assert acquisition["predecessor_public_call_counts"] == {
        "reconciliation": 1,
        "successor": 1,
        "B2": 1,
    }
    assert acquisition["formal_before_after_call_count"] == 2
    assert acquisition["production_monkeypatch_used"] is False


@pytest.mark.parametrize(
    ("case_id", "indices"),
    (
        ("canonical", list(range(11))),
        ("reversed", list(reversed(range(11)))),
        ("subset_10_4_0", [10, 4, 0]),
        ("singleton_10", [10]),
    ),
)
def test_formal_four_success_cases_exact11_zero_conversion_and_no_mutation(
    runtime_bundle: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    case_id: str,
    indices: list[int],
) -> None:
    del case_id
    batch = _collate(runtime_bundle, indices)
    before = _batch_fingerprint(batch)
    result, counts, captured = _run_counted(
        monkeypatch,
        batch=batch,
        remap_context=runtime_bundle["remap_context"],
        compiler_context=runtime_bundle["compiler_context"],
    )
    assert type(result) is dict
    assert tuple(result) == caller._RESULT_FIELDS
    assert result["schema_version"] == caller._RESULT_SCHEMA
    assert result["runtime_status"] == "full_success"
    assert result["failure_stage"] == "none"
    assert result["failure_reason"] == "NONE"
    assert result["compiler_status"] == "COMPILED_EXACT"
    assert result["remap_status"] == "REMAPPED_EXACT"
    assert result["batch_sample_keys_or_none"] is captured["observation"][
        "batch_sample_keys"
    ]
    assert result["compiler_failure_output10_or_none"] is None
    assert result["remap_output17_or_none"] is captured["output17"]
    assert result["remap_output17_or_none"][
        "pair_values_joint_global_indices"
    ] is None
    assert result["remap_output17_or_none"]["provenance"][
        "joint_index_status"
    ] == "JOINT_INDEX_SPACE_UNAVAILABLE"
    assert counts == {"extractor": 1, "compiler": 1, "remap": 1}
    assert captured["observation_unchanged"] is True
    assert captured["exact18_unchanged"] is True
    assert _fingerprint_equal(before, _batch_fingerprint(batch))
    assert captured["output10"] is not result.get("compiler_failure_output10_or_none")
    assert all(captured["exact18"] is not value for value in result.values())


def test_extractor_failure_terminal_precedence_and_exact11(
    runtime_bundle: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    batch = _collate(runtime_bundle, [10])
    batch["lig_mask"] = batch["lig_mask"].clone()
    batch["lig_mask"][0] = 1
    before = _batch_fingerprint(batch)
    result, counts, unused = _run_counted(
        monkeypatch,
        batch=batch,
        remap_context=object(),
        compiler_context=object(),
    )
    del unused
    assert tuple(result) == caller._RESULT_FIELDS
    assert result == {
        "schema_version": caller._RESULT_SCHEMA,
        "runtime_status": "extractor_failure",
        "failure_stage": "extractor",
        "failure_reason": "invalid_membership",
        "compiler_status": None,
        "remap_status": None,
        "batch_sample_keys_or_none": None,
        "compiler_failure_output10_or_none": None,
        "remap_output17_or_none": None,
        "provenance": dict(caller._PROVENANCE_ITEMS),
        "readiness": dict(caller._READINESS_ITEMS),
    }
    assert counts == {"extractor": 1, "compiler": 0, "remap": 0}
    assert _fingerprint_equal(before, _batch_fingerprint(batch))


def test_compiler_failure_terminal_retains_same_whole_output10(
    runtime_bundle: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    batch = _collate(runtime_bundle, [10])
    batch["names"] = [np.str_("not-a-current11-sample")]
    before = _batch_fingerprint(batch)
    result, counts, captured = _run_counted(
        monkeypatch,
        batch=batch,
        remap_context=object(),
        compiler_context=runtime_bundle["compiler_context"],
    )
    assert result["runtime_status"] == "compiler_failure"
    assert result["failure_stage"] == "compiler"
    assert result["failure_reason"] == "BATCH_SAMPLE_KEY_UNKNOWN"
    assert result["compiler_status"] == "BATCH_SAMPLE_KEY_UNKNOWN"
    assert result["remap_status"] is None
    assert result["compiler_failure_output10_or_none"] is captured["output10"]
    assert captured["output10"]["adapter_input_exact18"] is None
    assert result["remap_output17_or_none"] is None
    assert counts == {"extractor": 1, "compiler": 1, "remap": 0}
    assert captured["observation_unchanged"] is True
    assert _fingerprint_equal(before, _batch_fingerprint(batch))


def test_remap_failure_terminal_retains_same_whole_output17(
    runtime_bundle: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    failure17 = _real_failure17(runtime_bundle)
    batch = _collate(runtime_bundle, [10])

    def remap_failure(**unused: object) -> dict[str, object]:
        del unused
        return failure17

    result, counts, captured = _run_counted(
        monkeypatch,
        batch=batch,
        remap_context=runtime_bundle["remap_context"],
        compiler_context=runtime_bundle["compiler_context"],
        remap_fn=remap_failure,
    )
    assert result["runtime_status"] == "remap_failure"
    assert result["failure_stage"] == "remap"
    assert result["failure_reason"] == "SCHEMA_VERSION_MISMATCH"
    assert result["compiler_status"] == "COMPILED_EXACT"
    assert result["remap_status"] == "SCHEMA_VERSION_MISMATCH"
    assert result["compiler_failure_output10_or_none"] is None
    assert result["remap_output17_or_none"] is failure17
    assert captured["output17"] is failure17
    assert counts == {"extractor": 1, "compiler": 1, "remap": 1}
    assert captured["observation_unchanged"] is True
    assert captured["exact18_unchanged"] is True


@pytest.mark.parametrize(
    "case_id",
    (
        "unexpected_extractor_exception",
        "extractor_error_unknown_reason",
        "malformed_exact14",
    ),
)
def test_extractor_programming_errors_are_normalized_with_chaining(
    runtime_bundle: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    case_id: str,
) -> None:
    batch = _collate(runtime_bundle, [10])

    class UnexpectedExtractorError(ValueError):
        reason = "not_frozen"

    def stage(**unused: object) -> dict[str, object]:
        del unused
        if case_id == "unexpected_extractor_exception":
            raise RuntimeError("boom")
        if case_id == "extractor_error_unknown_reason":
            raise UnexpectedExtractorError(extractor._ERROR)
        return {}

    _assert_caller_error(
        lambda: _run_counted(
            monkeypatch,
            batch=batch,
            remap_context=object(),
            compiler_context=object(),
            extract_fn=stage,
        )
    )


@pytest.mark.parametrize(
    "case_id",
    (
        "compiler_exception",
        "malformed_output10",
        "unknown_compiler_status",
        "component_status_overall",
        "success_reason_mismatch",
        "failure_reason_mismatch",
        "success_exact18_missing",
        "success_exact18_malformed",
    ),
)
def test_compiler_programming_error_matrix(
    runtime_bundle: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    case_id: str,
) -> None:
    batch = _collate(runtime_bundle, [10])
    real_compile = (
        caller._compiler_owner.compile_covapie_current11_task2_batch_descriptor_with_remap_handoff_context_v1
    )

    def compile_case(**kwargs: object) -> dict[str, object]:
        if case_id == "compiler_exception":
            raise RuntimeError("boom")
        if case_id == "malformed_output10":
            return {}
        output = real_compile(**kwargs)
        if case_id == "unknown_compiler_status":
            output["compiler_status"] = "UNKNOWN"
            output["failure_reason"] = "UNKNOWN"
            output["adapter_input_exact18"] = None
        elif case_id == "component_status_overall":
            output["compiler_status"] = "JOINT_LAYOUT_UNAVAILABLE"
            output["failure_reason"] = "JOINT_LAYOUT_UNAVAILABLE"
            output["adapter_input_exact18"] = None
        elif case_id == "success_reason_mismatch":
            output["failure_reason"] = "ROLE_LENGTH_MISMATCH"
        elif case_id == "failure_reason_mismatch":
            output["compiler_status"] = "BATCH_SAMPLE_KEY_UNKNOWN"
            output["failure_reason"] = "BATCH_SAMPLE_KEY_INVALID"
            output["adapter_input_exact18"] = None
        elif case_id == "success_exact18_missing":
            output["adapter_input_exact18"] = None
        elif case_id == "success_exact18_malformed":
            output["adapter_input_exact18"] = {}
        return output

    _assert_caller_error(
        lambda: _run_counted(
            monkeypatch,
            batch=batch,
            remap_context=runtime_bundle["remap_context"],
            compiler_context=runtime_bundle["compiler_context"],
            compile_fn=compile_case,
        )
    )


@pytest.mark.parametrize(
    "case_id",
    (
        "remap_exception",
        "malformed_output17",
        "unknown_remap_status",
        "not_in_batch_overall",
        "joint_unavailable_overall",
        "success_reason_mismatch",
        "failure_reason_mismatch",
    ),
)
def test_remap_programming_error_matrix(
    runtime_bundle: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    case_id: str,
) -> None:
    batch = _collate(runtime_bundle, [10])
    real_remap = caller._remap_owner.remap_covapie_current11_task2_batch_index_with_context_v1

    def remap_case(**kwargs: object) -> dict[str, object]:
        if case_id == "remap_exception":
            raise RuntimeError("boom")
        if case_id == "malformed_output17":
            return {}
        output = real_remap(**kwargs)
        if case_id == "unknown_remap_status":
            output["remap_status"] = "UNKNOWN"
            output["failure_reason"] = "UNKNOWN"
        elif case_id == "not_in_batch_overall":
            output["remap_status"] = "NOT_IN_BATCH"
            output["failure_reason"] = "NOT_IN_BATCH"
        elif case_id == "joint_unavailable_overall":
            output["remap_status"] = "JOINT_INDEX_SPACE_UNAVAILABLE"
            output["failure_reason"] = "JOINT_INDEX_SPACE_UNAVAILABLE"
        elif case_id == "success_reason_mismatch":
            output["failure_reason"] = "ROLE_MISMATCH"
        elif case_id == "failure_reason_mismatch":
            output["remap_status"] = "SCHEMA_VERSION_MISMATCH"
            output["failure_reason"] = "ROLE_MISMATCH"
        return output

    _assert_caller_error(
        lambda: _run_counted(
            monkeypatch,
            batch=batch,
            remap_context=runtime_bundle["remap_context"],
            compiler_context=runtime_bundle["compiler_context"],
            remap_fn=remap_case,
        )
    )


@pytest.mark.parametrize(
    ("stage", "exception_type"),
    (
        ("extractor", KeyboardInterrupt),
        ("compiler", SystemExit),
        ("remap", GeneratorExit),
    ),
)
def test_baseexception_control_flow_propagates_unchanged(
    runtime_bundle: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
    stage: str,
    exception_type: type[BaseException],
) -> None:
    batch = _collate(runtime_bundle, [10])

    def interrupt(**unused: object) -> dict[str, object]:
        del unused
        raise exception_type()

    options = {
        "extractor": {"extract_fn": interrupt},
        "compiler": {"compile_fn": interrupt},
        "remap": {"remap_fn": interrupt},
    }[stage]
    with pytest.raises(exception_type):
        _run_counted(
            monkeypatch,
            batch=batch,
            remap_context=runtime_bundle["remap_context"],
            compiler_context=runtime_bundle["compiler_context"],
            **options,
        )


def test_target_residue_sidecar_is_semantically_independent_and_unchanged(
    runtime_bundle: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    baseline_batch = _collate(runtime_bundle, [10, 4, 0])
    sidecar_batch = _collate(runtime_bundle, [10, 4, 0])
    sidecar_batch["pocket_target_residue_atom_condition_indicator"] = torch.zeros(
        int(sidecar_batch["pocket_coords"].shape[0]), dtype=torch.bool
    )
    before = _batch_fingerprint(sidecar_batch)
    baseline, unused_counts, unused_capture = _run_counted(
        monkeypatch,
        batch=baseline_batch,
        remap_context=runtime_bundle["remap_context"],
        compiler_context=runtime_bundle["compiler_context"],
    )
    del unused_counts, unused_capture
    with_sidecar, counts, unused_capture = _run_counted(
        monkeypatch,
        batch=sidecar_batch,
        remap_context=runtime_bundle["remap_context"],
        compiler_context=runtime_bundle["compiler_context"],
    )
    del unused_capture
    assert with_sidecar == baseline
    assert counts == {"extractor": 1, "compiler": 1, "remap": 1}
    assert _fingerprint_equal(before, _batch_fingerprint(sidecar_batch))


def test_virtual_node_negative_short_circuits_without_repair(
    runtime_bundle: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    batch = _collate(runtime_bundle, [10])
    batch["num_virtual_atoms"] = torch.tensor([1], dtype=torch.int64)
    before = _batch_fingerprint(batch)
    result, counts, unused = _run_counted(
        monkeypatch,
        batch=batch,
        remap_context=object(),
        compiler_context=object(),
    )
    del unused
    assert result["runtime_status"] == "extractor_failure"
    assert result["failure_reason"] == "virtual_nodes_not_supported"
    assert counts == {"extractor": 1, "compiler": 0, "remap": 0}
    assert _fingerprint_equal(before, _batch_fingerprint(batch))


def test_fresh_provenance_and_readiness_for_all_returned_terminals(
    runtime_bundle: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    failure17 = _real_failure17(runtime_bundle)

    def remap_failure(**unused: object) -> dict[str, object]:
        del unused
        return failure17

    def batches() -> tuple[
        tuple[dict[str, object], object, object, object], ...
    ]:
        extractor_batch = _collate(runtime_bundle, [10])
        extractor_batch["lig_mask"] = extractor_batch["lig_mask"].clone()
        extractor_batch["lig_mask"][0] = 1
        compiler_batch = _collate(runtime_bundle, [10])
        compiler_batch["names"] = [np.str_("not-a-current11-sample")]
        return (
            (extractor_batch, object(), object(), None),
            (
                compiler_batch,
                object(),
                runtime_bundle["compiler_context"],
                None,
            ),
            (
                _collate(runtime_bundle, [10]),
                runtime_bundle["remap_context"],
                runtime_bundle["compiler_context"],
                remap_failure,
            ),
            (
                _collate(runtime_bundle, [10]),
                runtime_bundle["remap_context"],
                runtime_bundle["compiler_context"],
                None,
            ),
        )

    for batch, remap_context, compiler_context, remap_fn in batches():
        first, unused_counts, unused_capture = _run_counted(
            monkeypatch,
            batch=batch,
            remap_context=remap_context,
            compiler_context=compiler_context,
            remap_fn=remap_fn,
        )
        del unused_counts, unused_capture
        first["provenance"]["mutation"] = True
        first["readiness"]["mutation"] = True
        second, unused_counts, unused_capture = _run_counted(
            monkeypatch,
            batch=batch,
            remap_context=remap_context,
            compiler_context=compiler_context,
            remap_fn=remap_fn,
        )
        del unused_counts, unused_capture
        assert type(second["provenance"]) is dict
        assert type(second["readiness"]) is dict
        assert second["provenance"] == dict(caller._PROVENANCE_ITEMS)
        assert second["readiness"] == dict(caller._READINESS_ITEMS)
        assert first["provenance"] is not second["provenance"]
        assert first["readiness"] is not second["readiness"]


def test_per_batch_no_context_build_no_predecessor_no_io(
    runtime_bundle: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    batch = _collate(runtime_bundle, [10])
    counts = {
        "remap_context_builder": 0,
        "compiler_context_builder": 0,
        "old_compiler_authority": 0,
        "stable5_parser": 0,
        "reconciliation": 0,
        "successor": 0,
        "B2_or_hot_loop_gate": 0,
        "formal_authority": 0,
        "path_open": 0,
        "builtins_open": 0,
        "subprocess": 0,
    }

    def forbidden(name: str) -> Callable[..., NoReturn]:
        def call(*args: object, **kwargs: object) -> NoReturn:
            del args, kwargs
            counts[name] += 1
            raise AssertionError(name)

        return call

    monkeypatch.setattr(
        remap_owner,
        "build_covapie_current11_task2_batch_index_remap_adapter_context_v1",
        forbidden("remap_context_builder"),
    )
    monkeypatch.setattr(
        bridge,
        "build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1",
        forbidden("compiler_context_builder"),
    )
    for public_name in getattr(bridge._compiler, "__all__", ()):
        public = getattr(bridge._compiler, public_name, None)
        if callable(public):
            monkeypatch.setattr(
                bridge._compiler,
                public_name,
                forbidden("old_compiler_authority"),
            )
    monkeypatch.setattr(
        remap_owner,
        "_parse_successor_stable5_v1",
        forbidden("stable5_parser"),
    )
    for owner, count_name in (
        (remap_owner._reconciliation_owner, "reconciliation"),
        (remap_owner._successor_owner, "successor"),
        (remap_owner._hot_loop_owner, "B2_or_hot_loop_gate"),
    ):
        for public_name in getattr(owner, "__all__", ()):
            public = getattr(owner, public_name, None)
            if callable(public):
                monkeypatch.setattr(owner, public_name, forbidden(count_name))
    monkeypatch.setattr(
        remap_owner._adapter_owner,
        "_validate_formal",
        forbidden("formal_authority"),
    )
    monkeypatch.setattr(Path, "open", forbidden("path_open"))
    monkeypatch.setattr(builtins, "open", forbidden("builtins_open"))
    monkeypatch.setattr(subprocess, "run", forbidden("subprocess"))
    result = caller.run_covapie_current11_task2_runtime_caller_v1(
        batch=batch,
        remap_context=runtime_bundle["remap_context"],
        compiler_context=runtime_bundle["compiler_context"],
    )
    assert result["runtime_status"] == "full_success"
    assert counts == {key: 0 for key in counts}


def _synthetic_clean_git(
    *, head: str, origin: str, ahead: int, behind: int
) -> Callable[[Path, tuple[str, ...]], str]:
    blob = "a" * 40
    index = "".join(
        f"100644 {blob} 0\t{relative}\n" for relative in checker._EXACT4
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
            "rev-list",
            "--left-right",
            "--count",
            "HEAD...origin/main",
        ):
            return f"{ahead}\t{behind}\n"
        if arguments == ("log", "-1", "--format=%s", "HEAD"):
            return "synthetic clean successor\n"
        if arguments == ("status", "--porcelain=v1", "--untracked-files=all"):
            return ""
        if arguments == ("ls-files", "--stage", "--", *checker._EXACT4):
            return index
        if arguments == (
            "merge-base",
            "--is-ancestor",
            checker._BASE_COMMIT,
            "HEAD",
        ):
            return ""
        if arguments[:3] == ("hash-object", "--no-filters", "--"):
            return blob + "\n"
        if arguments[0] == "rev-parse" and arguments[1].startswith("HEAD:"):
            return blob + "\n"
        raise AssertionError(arguments)

    return run


def test_repository_lifecycle_actual_supported_profile() -> None:
    lifecycle, repository = checker._repository_lifecycle(ROOT)
    assert lifecycle in {
        "precommit-untracked",
        "clean-tracked-successor",
    }
    assert repository["head"] == repository["origin_main"]
    assert repository["ahead"] == repository["behind"] == 0
    if lifecycle == "precommit-untracked":
        assert repository["head"] == checker._BASE_COMMIT
    else:
        assert repository["head"] != checker._BASE_COMMIT


def test_repository_lifecycle_accepts_clean_published_successor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    published = "b" * 40
    monkeypatch.setattr(
        checker,
        "_run_git",
        _synthetic_clean_git(
            head=published, origin=published, ahead=0, behind=0
        ),
    )
    lifecycle, repository = checker._repository_lifecycle(ROOT)
    assert lifecycle == "clean-tracked-successor"
    assert repository["head"] == repository["origin_main"] == published


def test_repository_lifecycle_rejects_committed_unpushed_successor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        checker,
        "_run_git",
        _synthetic_clean_git(
            head="b" * 40,
            origin=checker._BASE_COMMIT,
            ahead=1,
            behind=0,
        ),
    )
    with pytest.raises(checker._CheckError):
        checker._repository_lifecycle(ROOT)


def test_checker_success_exact_line_reference_coverage_and_readiness() -> None:
    lifecycle, unused_repository = checker._repository_lifecycle(ROOT)
    del unused_repository
    assert lifecycle in {
        "precommit-untracked",
        "clean-tracked-successor",
    }
    completed = _checker()
    assert completed.returncode == 0
    assert completed.stderr == b""
    assert completed.stdout.count(b"\n") == 1
    result = json.loads(completed.stdout.decode("utf-8"))
    assert result["status"] == "PASS_CURRENT11_TASK2_RUNTIME_CALLER_V1"
    assert result["repository_lifecycle"] == lifecycle
    assert result["contract_commit_binding"] == checker._BASE_COMMIT
    assert result["contract_digest_binding"] == checker._CONTRACT_DIGEST
    assert result["caller_error_token"] == CALLER_ERROR
    assert result["runtime_result_exact_field_count"] == 11
    assert [row["case_id"] for row in result["success_cases"]] == [
        "canonical",
        "reversed",
        "subset_10_4_0",
        "singleton_10",
    ]
    assert all(
        row["call_vector"] == {"extractor": 1, "compiler": 1, "remap": 1}
        for row in result["success_cases"]
    )
    assert result["extractor_failure"]["call_vector"] == {
        "extractor": 1,
        "compiler": 0,
        "remap": 0,
    }
    assert result["compiler_failure"]["call_vector"] == {
        "extractor": 1,
        "compiler": 1,
        "remap": 0,
    }
    assert result["per_batch_context_build_count"] == 0
    assert result["per_batch_filesystem_calls"] == 0
    assert result["per_batch_filesystem_mutations"] == 0
    assert result["persistent_artifacts_written"] == 0
    assert result["runtime_caller_contract_gate_implemented"] is True
    assert result["runtime_caller_contract_gate_passed"] is True
    assert result["runtime_caller_implemented"] is True
    assert result["ready_for_runtime_caller_implementation"] is False
    assert result["ready_for_dataloader_integration"] is False
    assert result["ready_for_model_integration"] is False
    assert result["ready_for_loss_integration"] is False
    assert result["feature_semantics_reaudit_required_before_training"] is True
    assert result["ready_for_training"] is False


def test_checker_double_run_stdout_byte_identical_and_hash_stable() -> None:
    first = _checker()
    second = _checker()
    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == b""
    assert first.stdout == second.stdout
    assert hashlib.sha256(first.stdout).hexdigest() == hashlib.sha256(
        second.stdout
    ).hexdigest()


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
