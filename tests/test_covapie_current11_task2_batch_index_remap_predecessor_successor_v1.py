from __future__ import annotations

import ast
import copy
import functools
import hashlib
import importlib.util
import inspect
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Sequence

import pytest


ROOT = Path(__file__).resolve().parents[1]
STATE = (ROOT.parent / "covapie-state").resolve(strict=True)
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_current11_task2_batch_index_remap_contract_gate_v1 as remap_owner,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_task2_batch_index_remap_predecessor_successor_v1 as b3,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1
    as b2,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_tensor_projection_instance_builder_v1 as instance_owner,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_tensor_projection_payload_builder_v1 as payload_owner,
)


CHECKER_PATH = ROOT / b3.SCRIPT_PATH


def _load_checker() -> ModuleType:
    name = "covapie_remap_predecessor_successor_checker_test"
    spec = importlib.util.spec_from_file_location(name, CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fixture_b2_build() -> dict[str, bytes]:
    original = b2._repository_lifecycle
    try:
        b2._repository_lifecycle = lambda unused: "clean-tracked-successor"
        return b2.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1(
            repo_root=ROOT,
            state_root=STATE,
        )
    finally:
        b2._repository_lifecycle = original


@pytest.fixture(scope="module")
def b2_artifacts() -> dict[str, bytes]:
    return _fixture_b2_build()


@pytest.fixture(scope="module")
def artifacts(b2_artifacts: dict[str, bytes]) -> dict[str, bytes]:
    return b3._build_fixture_only(
        repo_root=ROOT,
        state_root=STATE,
        b2_artifacts=b2_artifacts,
    )


@pytest.fixture(scope="module")
def parsed(artifacts: dict[str, bytes]) -> dict[str, object]:
    return {
        name: json.loads(payload.decode("utf-8"))
        for name, payload in artifacts.items()
        if name.endswith(".json")
    }


@pytest.fixture(scope="module")
def reconstruction() -> tuple[dict[str, bytes], dict[str, object]]:
    b3._validate_helper_signatures()
    return b3._reconstruct_stable(ROOT, STATE)


@pytest.fixture(scope="module")
def clean_build(
    b2_artifacts: dict[str, bytes],
) -> dict[str, object]:
    original_lifecycle = b3._repository_lifecycle
    original_b2_api = (
        b2.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1
    )
    calls = 0

    @functools.wraps(original_b2_api)
    def counted(**unused: object) -> dict[str, bytes]:
        nonlocal calls
        calls += 1
        return b2_artifacts

    try:
        b3._repository_lifecycle = lambda unused: "clean-tracked-successor"
        b2.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1 = counted
        result = b3.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1(
            repo_root=ROOT,
            state_root=STATE,
        )
    finally:
        b3._repository_lifecycle = original_lifecycle
        b2.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1 = original_b2_api
    return {"artifacts": result, "B2_call_count": calls}


def _manual_digest(
    domain: bytes,
    names: Sequence[str],
    artifacts: dict[str, bytes],
) -> str:
    digest = hashlib.sha256()
    digest.update(domain)
    for name in names:
        encoded = name.encode("utf-8")
        payload = artifacts[name]
        digest.update(len(encoded).to_bytes(8, "big", signed=False))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big", signed=False))
        digest.update(payload)
    return digest.hexdigest()


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_all_keys(item) for item in value.values()))
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value))
    return set()


def _all_strings(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [item for child in value.values() for item in _all_strings(child)]
    if isinstance(value, list):
        return [item for child in value for item in _all_strings(child)]
    return []


def _changed_json_paths(left: object, right: object, prefix: str = "") -> list[str]:
    if type(left) is not type(right):
        return [prefix]
    if isinstance(left, dict):
        assert isinstance(right, dict) and set(left) == set(right)
        return [
            path
            for key in left
            for path in _changed_json_paths(
                left[key], right[key], f"{prefix}.{key}" if prefix else key
            )
        ]
    if isinstance(left, list):
        assert isinstance(right, list) and len(left) == len(right)
        return [
            path
            for index, (a, b) in enumerate(zip(left, right, strict=True))
            for path in _changed_json_paths(a, b, f"{prefix}[{index}]")
        ]
    return [] if left == right else [prefix]


def test_public_exact1_keyword_only_and_no_override_surface() -> None:
    function = (
        b3.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1
    )
    assert b3.__all__ == (function.__name__,)
    signature = inspect.signature(function)
    assert tuple(signature.parameters) == ("repo_root", "state_root")
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    assert not {
        "device_override",
        "B2_override",
        "helper_override",
        "report_override",
        "path_override",
        "training_option",
        "cache_option",
        "adapter_input",
    }.intersection(signature.parameters)
    with pytest.raises(TypeError):
        function(ROOT, STATE)  # type: ignore[misc]


def test_silent_import() -> None:
    completed = subprocess.run(
        (sys.executable, "-B", "-c", f"import {b3.__name__}"),
        cwd=ROOT,
        env={
            **os.environ,
            "PYTHONPATH": "src:.",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == b""


def test_public_precommit_lifecycle_is_rejected_before_b2(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        b3,
        "_repository_lifecycle",
        lambda unused: "precommit-untracked",
    )
    public_calls = 0
    b2_calls = 0
    original = (
        b2.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1
    )

    @functools.wraps(original)
    def forbidden(**unused: object) -> dict[str, bytes]:
        nonlocal b2_calls
        b2_calls += 1
        raise AssertionError("B2 must not be called from precommit public B3")

    monkeypatch.setattr(
        b2,
        "build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1",
        forbidden,
    )
    with pytest.raises(ValueError, match=f"^{b3.ERROR_TOKEN}$") as caught:
        public_calls += 1
        b3.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1(
            repo_root=ROOT,
            state_root=STATE,
        )
    assert type(caught.value.__cause__) is b3._ReconstructionInvariantError
    assert public_calls == 1
    assert b2_calls == 0


def test_historical_public_builders_and_adapter_are_not_called_in_product_source() -> None:
    tree = ast.parse((ROOT / b3.MODULE_PATH).read_text(encoding="utf-8"))
    forbidden = {
        "build_covapie_current11_tensor_projection_payload_bundle_v1",
        "build_covapie_current11_tensor_projection_instance_v1",
        "build_covapie_current11_task2_batch_index_remap_contract_gate_v1",
        "build_covapie_current11_task2_batch_index_remap_adapter_v1",
        "_published_gate",
        "_payload_exact8",
        "_projection_exact2",
        "_contract_exact6",
    }
    called = {
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Attribute, ast.Name))
    }
    assert not forbidden.intersection(called)


def test_product_source_has_no_monkeypatch_assignment_or_setattr() -> None:
    tree = ast.parse((ROOT / b3.MODULE_PATH).read_text(encoding="utf-8"))
    assert not any(
        isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign))
        and any(
            isinstance(target, ast.Attribute)
            for target in (
                node.targets if isinstance(node, ast.Assign) else [node.target]
            )
        )
        for node in ast.walk(tree)
    )
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "setattr"
        for node in ast.walk(tree)
    )


def test_b2_owner_identity() -> None:
    row = b3._validate_b2_owner(ROOT)
    assert row["bytes"] == 54756
    assert row["LF"] == 1464
    assert row["sha256"] == b3.B2_MODULE_SPEC["sha256"]
    assert row["git_blob"] == "f8b17a86969e41eb8a4a1bde9c65368e3cb2bd05"
    assert row["introduction_commit"] == b3.BASE_COMMIT


def test_b2_exact5_parser_and_independent_stable4_digest(
    b2_artifacts: dict[str, bytes],
) -> None:
    evidence = b3._validate_b2_artifacts(b2_artifacts)
    stable = {name: b2_artifacts[name] for name in b2.STABLE_ARTIFACT_NAMES}
    assert evidence["stable_digest"] == b3.B2_STABLE_DIGEST
    assert _manual_digest(
        b2.CONTRACT_DIGEST_DOMAIN, b2.STABLE_ARTIFACT_NAMES, stable
    ) == b3.B2_STABLE_DIGEST


def test_b2_transition_exact3(b2_artifacts: dict[str, bytes]) -> None:
    transitions = json.loads(b2_artifacts[b2.ARTIFACT_NAMES[1]])
    assert [row["object_id"] for row in transitions] == [
        "unit_000001_dossier",
        "routing_canonical",
        "routing_object",
    ]
    assert [row["historical_identity"]["st_dev"] for row in transitions] == [
        49,
        49,
        49,
    ]
    assert [
        row["authorized_current_identity"]["st_dev"] for row in transitions
    ] == [50, 50, 50]
    assert all(row["transition_authorized"] is True for row in transitions)


def test_b2_readiness_and_historical_call_boundaries(
    b2_artifacts: dict[str, bytes],
) -> None:
    report = json.loads(b2_artifacts[b2.ARTIFACT_NAMES[4]])
    readiness = report["readiness"]
    assert readiness["ready_for_remap_predecessor_successor_integration"] is True
    assert readiness[
        "ready_for_public_remap_adapter_hot_loop_contract_implementation"
    ] is False
    assert readiness["ready_for_training"] is False
    assert report["historical_public_gates_called"] is False
    assert report["heavy_remap_contract_chain_called"] is False
    assert report["remap_adapter_private_contract_called"] is False


def test_b2_error_is_preserved_as_public_cause(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        b3, "_repository_lifecycle", lambda unused: "clean-tracked-successor"
    )

    original = (
        b2.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1
    )

    @functools.wraps(original)
    def reject(**unused: object) -> dict[str, bytes]:
        raise ValueError(b2.ERROR_TOKEN)

    monkeypatch.setattr(
        b2,
        "build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1",
        reject,
    )
    with pytest.raises(ValueError, match=f"^{b3.ERROR_TOKEN}$") as caught:
        b3.build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1(
            repo_root=ROOT,
            state_root=STATE,
        )
    assert type(caught.value.__cause__) is ValueError
    assert str(caught.value.__cause__) == b2.ERROR_TOKEN


def test_helper_owner_exact_identities() -> None:
    rows = b3._validate_helper_owners(ROOT)
    assert [row["owner_name"] for row in rows] == ["payload", "instance", "remap"]
    assert {
        row["owner_name"]: (row["bytes"], row["LF"], row["sha256"], row["git_blob"])
        for row in rows
    } == {
        name: (spec["bytes"], spec["LF"], spec["sha256"], spec["git_blob"])
        for name, spec in b3.HELPER_OWNER_SPECS.items()
    }


def test_helper_owner_commit_lineage() -> None:
    rows = b3._validate_helper_owners(ROOT)
    assert [row["introduction_commit"] for row in rows] == [
        "bc927ef679a6605339d8879559f69fc5ab3002a7",
        "124543d39ab8f2bc27e748ad2e2c57387730ba47",
        "6502321ca56ce8895adb3ee20587c383dfbda767",
    ]
    assert all(row["head_and_worktree_exact"] is True for row in rows)


def test_helper_exact_signatures_are_frozen() -> None:
    rows = b3._validate_helper_signatures()
    assert len(rows) == b3.FROZEN_HELPER_SIGNATURE_COUNT == 29
    assert sum(row["owner_name"] == "payload" for row in rows) == 10
    assert sum(row["owner_name"] == "instance" for row in rows) == 5
    assert sum(row["owner_name"] == "remap" for row in rows) == 14


def test_signature_drift_fails_before_helper_execution(
    monkeypatch: pytest.MonkeyPatch,
    b2_artifacts: dict[str, bytes],
) -> None:
    calls = 0

    def drifted(unexpected: object) -> dict[str, bytes]:
        nonlocal calls
        calls += 1
        return {}

    monkeypatch.setattr(payload_owner, "_read_formal", drifted)
    with pytest.raises(b3._HistoricalHelperContractError):
        b3._build_fixture_only(
            repo_root=ROOT,
            state_root=STATE,
            b2_artifacts=b2_artifacts,
        )
    assert calls == 0


def test_owner_drift_fails_before_helper_execution(
    monkeypatch: pytest.MonkeyPatch,
    b2_artifacts: dict[str, bytes],
) -> None:
    calls = 0
    original_read_formal = payload_owner._read_formal

    @functools.wraps(original_read_formal)
    def counted(canonical: Path) -> dict[str, bytes]:
        nonlocal calls
        calls += 1
        return original_read_formal(canonical)

    specs = copy.deepcopy(b3.HELPER_OWNER_SPECS)
    specs["payload"]["bytes"] += 1
    monkeypatch.setattr(b3, "HELPER_OWNER_SPECS", specs)
    monkeypatch.setattr(payload_owner, "_read_formal", counted)
    with pytest.raises(b3._HistoricalHelperContractError):
        b3._build_fixture_only(
            repo_root=ROOT,
            state_root=STATE,
            b2_artifacts=b2_artifacts,
        )
    assert calls == 0


def test_payload_stable7_exact_identities(
    reconstruction: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    stable7 = reconstruction[1]["payload_stable7"]
    assert type(stable7) is dict
    assert tuple(stable7) == tuple(b3.PAYLOAD_STABLE7_IDENTITIES)
    for name, identity in b3.PAYLOAD_STABLE7_IDENTITIES.items():
        payload = stable7[name]
        assert (len(payload), payload.count(b"\n"), hashlib.sha256(payload).hexdigest()) == identity


def test_payload_stable7_digest_and_historical_report_absent(
    reconstruction: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    stable7 = reconstruction[1]["payload_stable7"]
    assert reconstruction[1]["payload_digest"] == b3.PAYLOAD_STABLE7_DIGEST
    assert _manual_digest(
        b"COVAPIE_CURRENT11_TENSOR_PROJECTION_PAYLOAD_BUNDLE_V1\0",
        tuple(stable7),
        stable7,
    ) == b3.PAYLOAD_STABLE7_DIGEST
    assert b3.PAYLOAD_HISTORICAL_REPORT_NAME not in stable7


def test_payload_report_device_sensitivity_counterfactual(
    reconstruction: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    stable7 = reconstruction[1]["payload_stable7"]
    canonical = STATE / payload_owner._FORMAL_RELATIVE
    snapshot50 = payload_owner._formal_snapshot(canonical)
    snapshot49 = copy.deepcopy(snapshot50)
    for key in ("parent", "canonical", "object"):
        value = list(snapshot49[key])
        value[0] = 49
        snapshot49[key] = tuple(value)
    for name, leaf in snapshot49["leaves"].items():
        value = list(leaf)
        value[0] = 49
        snapshot49["leaves"][name] = tuple(value)
    digest = reconstruction[1]["payload_digest"]
    report49 = payload_owner._canonical_json(
        payload_owner._report(stable7, digest, snapshot49)
    )
    report50 = payload_owner._canonical_json(
        payload_owner._report(stable7, digest, snapshot50)
    )
    assert len(report49) == len(report50) == 5229
    assert report49.count(b"\n") == report50.count(b"\n") == 144
    assert hashlib.sha256(report49).hexdigest() == (
        "05e456e762ba554aeb110dd64e2a3b4eae35ddba1a2144602da40c53873ab7c8"
    )
    assert hashlib.sha256(report50).hexdigest() == (
        "0748abeae6c1a71843f250696d16997955ec1dd862178025745fdb12e7aca689"
    )


def test_payload_report_exact_changed_json_paths(
    reconstruction: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    stable7 = reconstruction[1]["payload_stable7"]
    canonical = STATE / payload_owner._FORMAL_RELATIVE
    snapshot50 = payload_owner._formal_snapshot(canonical)
    snapshot49 = copy.deepcopy(snapshot50)
    for key in ("canonical", "object"):
        value = list(snapshot49[key])
        value[0] = 49
        snapshot49[key] = tuple(value)
    report49 = payload_owner._report(
        stable7, reconstruction[1]["payload_digest"], snapshot49
    )
    report50 = payload_owner._report(
        stable7, reconstruction[1]["payload_digest"], snapshot50
    )
    assert _changed_json_paths(report49, report50) == [
        "formal_filesystem_identity.canonical[0]",
        "formal_filesystem_identity.object[0]",
    ]


def test_projection_instance_exact_identity(
    reconstruction: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    payload = reconstruction[1]["instance_bytes"]
    assert (
        len(payload),
        payload.count(b"\n"),
        hashlib.sha256(payload).hexdigest(),
    ) == b3.PROJECTION_INSTANCE_IDENTITY
    assert reconstruction[1]["instance_digest"] == b3.PROJECTION_INSTANCE_DIGEST


def test_projection_assemble_does_not_require_payload_report(
    reconstruction: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    stable7 = reconstruction[1]["payload_stable7"]
    decoded = {
        name: payload_owner._strict_json(payload) for name, payload in stable7.items()
    }
    assert b3.PAYLOAD_HISTORICAL_REPORT_NAME not in decoded
    formal = payload_owner._read_formal(STATE / payload_owner._FORMAL_RELATIVE)
    routing = instance_owner._routing(formal, None)
    rebuilt = instance_owner._canonical_json(instance_owner._assemble(routing, decoded))
    assert hashlib.sha256(rebuilt).hexdigest() == b3.PROJECTION_INSTANCE_IDENTITY[2]


def test_projection_historical_report_not_emitted(
    reconstruction: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    assert b3.PROJECTION_HISTORICAL_REPORT_NAME not in reconstruction[0]
    assert b3.PROJECTION_HISTORICAL_REPORT_NAME not in reconstruction[1][
        "payload_stable7"
    ]


def test_remap_stable5_exact_identities(artifacts: dict[str, bytes]) -> None:
    for name, identity in b3.REMAP_STABLE5_IDENTITIES.items():
        payload = artifacts[name]
        assert (
            len(payload),
            payload.count(b"\n"),
            hashlib.sha256(payload).hexdigest(),
        ) == identity


def test_remap_stable5_independent_digest(artifacts: dict[str, bytes]) -> None:
    assert _manual_digest(
        b"COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_CONTRACT_GATE_V1\0",
        b3.STABLE_ARTIFACT_NAMES,
        artifacts,
    ) == b3.REMAP_STABLE5_DIGEST


def test_canonical_reference_success(parsed: dict[str, object]) -> None:
    output = parsed[b3.STABLE_ARTIFACT_NAMES[4]][
        "canonical_exact11_batch_reference"
    ]["output"]
    assert output["remap_status"] == "REMAPPED_EXACT"
    assert len(output["pair_values_batch_indices"]) == 11


def test_reversed_reference_success(parsed: dict[str, object]) -> None:
    case = parsed[b3.STABLE_ARTIFACT_NAMES[4]]["permutation_reference_cases"][0]
    assert case["source_sample_indices"] == list(reversed(range(11)))
    assert case["output"]["remap_status"] == "REMAPPED_EXACT"


def test_mixed_reference_success(parsed: dict[str, object]) -> None:
    case = parsed[b3.STABLE_ARTIFACT_NAMES[4]]["permutation_reference_cases"][1]
    assert case["source_sample_indices"] == [10, 4, 0, 7, 2]
    assert case["output"]["remap_status"] == "REMAPPED_EXACT"


def test_subset_reference_success(parsed: dict[str, object]) -> None:
    case = parsed[b3.STABLE_ARTIFACT_NAMES[4]]["subset_reference_cases"][0]
    assert case["source_sample_indices"] == [10, 4, 0]
    assert case["output"]["remap_status"] == "REMAPPED_EXACT"


def test_no_joint_reference_success_and_joint_none(parsed: dict[str, object]) -> None:
    output = parsed[b3.STABLE_ARTIFACT_NAMES[4]][
        "no_joint_layout_reference_case"
    ]["output"]
    assert output["remap_status"] == "REMAPPED_EXACT"
    assert output["pair_values_joint_global_indices"] is None
    assert output["provenance"]["joint_index_status"] == (
        "JOINT_INDEX_SPACE_UNAVAILABLE"
    )


def test_synthetic_reference_success_and_offsets(parsed: dict[str, object]) -> None:
    output = parsed[b3.STABLE_ARTIFACT_NAMES[4]][
        "synthetic_future_p_gt_1_reference_case"
    ]["output"]
    assert output["remap_status"] == "REMAPPED_EXACT"
    assert output["sample_pair_offsets"] == [0, 1, 3, 3]


def test_successor_exact6_order_types_and_canonical_json(
    artifacts: dict[str, bytes],
) -> None:
    assert type(artifacts) is dict
    assert tuple(artifacts) == b3.ARTIFACT_NAMES
    assert len(artifacts) == 6
    for name, payload in artifacts.items():
        assert type(payload) is bytes and payload.endswith(b"\n")
        assert b"\r" not in payload and b"\0" not in payload
        if name.endswith(".json"):
            value = json.loads(payload)
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


def test_successor_report_new_name_schema_and_old_name_not_returned(
    parsed: dict[str, object], artifacts: dict[str, bytes]
) -> None:
    assert b3.SUCCESSOR_REPORT_NAME in artifacts
    assert b3.HISTORICAL_REPORT_NAME not in artifacts
    report = parsed[b3.SUCCESSOR_REPORT_NAME]
    assert report["schema_version"] == b3.REPORT_SCHEMA
    assert report["successor_status"] == b3.SUCCESSOR_STATUS
    assert report["historical_manifest_report_name"] == b3.HISTORICAL_REPORT_NAME
    assert report["historical_manifest_report_name_is_current_output"] is False
    manifest = parsed[b3.STABLE_ARTIFACT_NAMES[0]]
    assert b3.HISTORICAL_REPORT_NAME in manifest["artifact_names"]
    assert b3.SUCCESSOR_REPORT_NAME not in manifest["artifact_names"]


def test_successor_report_execution_truth_booleans(parsed: dict[str, object]) -> None:
    report = parsed[b3.SUCCESSOR_REPORT_NAME]
    false_fields = (
        "historical_public_gate_called",
        "historical_payload_public_builder_called",
        "historical_projection_instance_public_builder_called",
        "historical_remap_contract_public_gate_called",
        "public_remap_adapter_called",
        "production_monkeypatch_used",
        "state_or_repository_write_performed",
        "payload_historical_report_emitted",
        "projection_historical_report_emitted",
        "ready_for_training",
    )
    assert all(report[field] is False for field in false_fields)
    true_fields = (
        "B2_transition_contract_called",
        "B2_transition_contract_passed",
        "stable_semantic_artifact_parity",
        "payload_stable7_parity",
        "projection_instance_stable_parity",
        "remap_stable5_parity",
        "owner_identity_validation_passed",
        "helper_signature_validation_passed",
    )
    assert all(report[field] is True for field in true_fields)


def test_successor_report_lineage_only_hash_interpretation(
    parsed: dict[str, object],
) -> None:
    report = parsed[b3.SUCCESSOR_REPORT_NAME]
    assert report["historical_payload_report_sha_embedded_as_lineage_only"] is True
    assert report[
        "historical_projection_instance_report_sha_embedded_as_lineage_only"
    ] is True
    assert report[
        "historical_embedded_report_sha_does_not_mean_report_emitted_in_successor"
    ] is True
    instance = json.loads(
        instance_owner._canonical_json(
            b3._reconstruct_stable(ROOT, STATE)[1]["instance_value"]
        )
    )
    assert instance["source_lineage"]["payload_builder"]["exact8_artifact_sha256"][
        b3.PAYLOAD_HISTORICAL_REPORT_NAME
    ] == "05e456e762ba554aeb110dd64e2a3b4eae35ddba1a2144602da40c53873ab7c8"


def test_successor_report_has_no_timestamp_mount_id_or_absolute_path(
    parsed: dict[str, object],
) -> None:
    report = parsed[b3.SUCCESSOR_REPORT_NAME]
    keys = _all_keys(report)
    assert "timestamp" not in keys
    assert "nonce" not in keys
    assert "mount_id" not in keys
    assert "parent_mount_id" not in keys
    assert not any(value.startswith("/") for value in _all_strings(report))


def test_deterministic_fixture_reconstruction(
    artifacts: dict[str, bytes], b2_artifacts: dict[str, bytes]
) -> None:
    second = b3._build_fixture_only(
        repo_root=ROOT,
        state_root=STATE,
        b2_artifacts=b2_artifacts,
    )
    assert second == artifacts


def test_no_mutation_of_historical_helper_bindings(
    b2_artifacts: dict[str, bytes],
) -> None:
    before_b2 = copy.deepcopy(b2_artifacts)
    bindings = {
        ("payload", name): getattr(payload_owner, name)
        for name in b3._PAYLOAD_SIGNATURES
    }
    bindings.update(
        {
            ("instance", name): getattr(instance_owner, name)
            for name in b3._INSTANCE_SIGNATURES
        }
    )
    bindings.update(
        {
            ("remap", name): getattr(remap_owner, name)
            for name in b3._REMAP_SIGNATURES
        }
    )
    b3._build_fixture_only(
        repo_root=ROOT,
        state_root=STATE,
        b2_artifacts=b2_artifacts,
    )
    modules = {
        "payload": payload_owner,
        "instance": instance_owner,
        "remap": remap_owner,
    }
    assert all(
        getattr(modules[owner], name) is function
        for (owner, name), function in bindings.items()
    )
    assert b2_artifacts == before_b2


def test_repository_and_formal_read_only(b2_artifacts: dict[str, bytes]) -> None:
    before_repository = b3._repository_snapshot(ROOT)
    before_formal = b3._formal_snapshot(STATE)
    b3._build_fixture_only(
        repo_root=ROOT,
        state_root=STATE,
        b2_artifacts=b2_artifacts,
    )
    assert b3._repository_snapshot(ROOT) == before_repository
    assert b3._formal_snapshot(STATE) == before_formal


def test_current_repository_lifecycle_is_allowed_profile() -> None:
    lifecycle = b3._repository_lifecycle(ROOT)
    assert lifecycle in (
        "precommit-untracked",
        "clean-tracked-successor",
    )


@pytest.mark.parametrize(
    "lifecycle", ("precommit-untracked", "clean-tracked-successor")
)
def test_lifecycle_profiles_simulated(
    monkeypatch: pytest.MonkeyPatch,
    lifecycle: str,
) -> None:
    blob = "a" * 40

    def run_git(unused: Path, arguments: Sequence[str]) -> str:
        call = tuple(arguments)
        if call == ("status", "--porcelain=v1", "--untracked-files=all"):
            if lifecycle == "precommit-untracked":
                return "\n".join(f"?? {path}" for path in b3.REPOSITORY_EXACT4)
            return ""
        if call == ("ls-files", "--stage", "--", *b3.REPOSITORY_EXACT4):
            if lifecycle == "precommit-untracked":
                return ""
            return "\n".join(
                f"100644 {blob} 0\t{path}" for path in b3.REPOSITORY_EXACT4
            )
        if call[:2] == ("hash-object", "--no-filters") or call[0] == "rev-parse":
            return blob + "\n"
        pytest.fail(f"unexpected call: {call!r}")

    monkeypatch.setattr(b3, "_run_git", run_git)
    assert b3._repository_lifecycle(ROOT) == lifecycle


def test_fifth_untracked_path_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    def run_git(unused: Path, arguments: Sequence[str]) -> str:
        if tuple(arguments) == (
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ):
            return "\n".join(
                [
                    *(f"?? {path}" for path in b3.REPOSITORY_EXACT4),
                    "?? forbidden-fifth.txt",
                ]
            )
        return ""

    monkeypatch.setattr(b3, "_run_git", run_git)
    with pytest.raises(b3._ReconstructionInvariantError):
        b3._repository_lifecycle(ROOT)


@pytest.mark.parametrize(
    "arguments",
    (
        (),
        ("--help",),
        ("--repo-root", os.fspath(ROOT)),
        ("--state-root", os.fspath(STATE)),
        (
            "--repo-root",
            os.fspath(ROOT),
            "--state-root",
            os.fspath(STATE),
            "--train",
        ),
        ("--device", "50"),
        ("--cache", "yes"),
    ),
)
def test_checker_cli_rejects_expanded_interface(arguments: tuple[str, ...]) -> None:
    completed = subprocess.run(
        (sys.executable, "-B", os.fspath(CHECKER_PATH), *arguments),
        cwd=ROOT,
        env={
            **os.environ,
            "PYTHONPATH": "src:.",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 1
    assert completed.stdout == b""
    assert completed.stderr == (b3.ERROR_TOKEN + "\n").encode("ascii")


def test_checker_precommit_branch_simulated_candidate_only(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    checker = _load_checker()
    monkeypatch.setattr(
        checker,
        "_repository_lifecycle",
        lambda unused: "precommit-untracked",
    )
    monkeypatch.setattr(
        checker.b3,
        "_repository_lifecycle",
        lambda unused: "precommit-untracked",
    )
    result = checker._main(
        (
            "--repo-root",
            os.fspath(ROOT),
            "--state-root",
            os.fspath(STATE),
        )
    )
    captured = capsys.readouterr()
    assert result == 0
    assert captured.err == ""
    assert captured.out.count("\n") == 1
    summary = json.loads(captured.out)
    assert summary["status"] == (
        "PASS_REMAP_PREDECESSOR_SUCCESSOR_PRECOMMIT_CANDIDATE_ONLY"
    )
    assert summary["repository_lifecycle"] == "precommit-untracked"
    assert summary["real_public_B3_build_performed"] is False
    assert summary["clean_successor_live_validation_pending"] is True
    assert summary["test_harness_only"] is True
    assert summary["production_path"] is False
    assert summary["production_monkeypatch_used"] is False
    assert summary["ready_for_commit_review"] is True
    assert summary["ready_for_one_heavy_parity_timing_probe"] is False
    assert captured.out == (
        json.dumps(summary, sort_keys=True, separators=(",", ":")) + "\n"
    )


def test_checker_clean_successor_path_simulated(
    monkeypatch: pytest.MonkeyPatch,
    clean_build: dict[str, object],
) -> None:
    checker = _load_checker()
    clean_artifacts = clean_build["artifacts"]
    monkeypatch.setattr(
        checker.b3,
        "build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1",
        lambda **unused: clean_artifacts,
    )
    summary = checker._clean_validation(ROOT, STATE)
    assert summary["status"] == b3.SUCCESSOR_STATUS
    assert summary["B2_transition_contract_call_count"] == 2
    assert summary["public_B3_build_count"] == 2
    assert summary["real_public_B3_build_performed"] is True
    assert summary["clean_successor_live_validation_pending"] is False
    assert summary["ready_for_one_heavy_parity_timing_probe"] is True


def test_public_clean_successor_design_calls_b2_once(
    clean_build: dict[str, object],
) -> None:
    assert clean_build["B2_call_count"] == 1
    artifacts = clean_build["artifacts"]
    report = json.loads(artifacts[b3.SUCCESSOR_REPORT_NAME])
    assert report["B2_transition_contract_call_count"] == 1
    assert report["repository_lifecycle"] == "clean-tracked-successor"
    assert report["clean_successor_live_validation_pending"] is False
    assert report["ready_for_one_heavy_parity_timing_probe"] is True


def test_canonical_mask_sentinel_still_exact5_with_scaffold_only_b3(
    reconstruction: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    masks = reconstruction[1]["instance_value"]["canonical_mask_semantics"]
    assert [(row["semantic_name"], row["display_alias"]) for row in masks] == [
        ("warhead_only", "A"),
        ("linker_plus_warhead", "B"),
        ("scaffold_plus_warhead", "B2"),
        ("scaffold_only", "B3"),
        ("scaffold_plus_linker_plus_warhead", "C"),
    ]


def test_training_and_integration_readiness_remains_fail_closed(
    parsed: dict[str, object],
) -> None:
    report = parsed[b3.SUCCESSOR_REPORT_NAME]
    assert report[
        "ready_for_public_remap_adapter_hot_loop_contract_implementation"
    ] is False
    assert report["current_adapter_directly_accepts_successor_exact6"] is False
    assert report["current_compiler_context_uses_successor_authority"] is False
    assert report["compiler_context_rebuild_device_identity_risk"] is True
    assert report["ready_for_dataloader_integration"] is False
    assert report["ready_for_model_integration"] is False
    assert report["ready_for_loss_integration"] is False
    assert report["feature_semantics_reaudit_required_before_training"] is True
    assert report["ready_for_training"] is False
    assert report["commit_created"] is False
    assert report["push_performed"] is False


def test_candidate_exact4_file_safety() -> None:
    assert len(b3.REPOSITORY_EXACT4) == 4
    for relative in b3.REPOSITORY_EXACT4:
        path = ROOT / relative
        metadata = path.lstat()
        payload = path.read_bytes()
        assert stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
        assert stat.S_IMODE(metadata.st_mode) == 0o644
        assert 0 < len(payload) < 1024 * 1024
        assert not payload.startswith(b"\xef\xbb\xbf")
        assert b"\0" not in payload and b"\r" not in payload
        assert payload.endswith(b"\n") and not payload.endswith(b"\n\n")
        assert all(
            not line.rstrip(b"\r\n").endswith((b" ", b"\t"))
            for line in payload.splitlines(keepends=True)
        )
        payload.decode("utf-8")
