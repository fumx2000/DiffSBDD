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
from types import ModuleType
from typing import Sequence

import pytest


ROOT = Path(__file__).resolve().parents[1]
STATE = (ROOT.parent / "covapie-state").resolve(strict=True)
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_current11_task2_batch_index_remap_adapter_v1 as runtime_owner,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_task2_batch_index_remap_contract_gate_v1
    as reference_owner,
)
from covalent_ext import (  # noqa: E402
    covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1
    as gate,
)


CHECKER_PATH = ROOT / gate.SCRIPT_PATH


def _load_checker() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "covapie_output17_semantic_reconciliation_checker_test",
        CHECKER_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return gate.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1(
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
def evidence() -> dict[str, object]:
    gate._validate_helper_signatures()
    return gate._pure_semantic_evidence()


def _manual_digest(artifacts: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    digest.update(
        b"COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_OUTPUT17_SEMANTIC_"
        b"RECONCILIATION_CONTRACT_GATE_V1\0"
    )
    for name in gate.STABLE_ARTIFACT_NAMES:
        encoded = name.encode("utf-8")
        payload = artifacts[name]
        digest.update(len(encoded).to_bytes(8, "big", signed=False))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big", signed=False))
        digest.update(payload)
    return digest.hexdigest()


def _core(output: dict[str, object]) -> dict[str, object]:
    return {name: output[name] for name in gate.CORE15_FIELD_ORDER}


def _subprocess_env() -> dict[str, str]:
    return {
        **os.environ,
        "PYTHONPATH": "src:.",
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def test_public_exact1_keyword_only_signature() -> None:
    function = (
        gate.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1
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


def test_public_api_rejects_positional_arguments() -> None:
    with pytest.raises(TypeError):
        gate.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1(
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
                "covapie_current11_task2_batch_index_remap_output17_semantic_"
                "reconciliation_contract_gate_v1"
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
        "COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_OUTPUT17_SEMANTIC_"
        "RECONCILIATION_CONTRACT_GATE_V1_ERROR"
    )
    with pytest.raises(ValueError, match=f"^{gate.ERROR_TOKEN}$"):
        gate.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1(
            repo_root=Path("."),
            state_root=STATE,
        )


def test_exact6_order_and_bytes(artifacts: dict[str, bytes]) -> None:
    assert type(artifacts) is dict
    assert tuple(artifacts) == gate.ARTIFACT_NAMES
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


def test_exact17_order_frozen(parsed: dict[str, dict[str, object]]) -> None:
    assert tuple(runtime_owner._OUTPUT_FIELD_ORDER) == gate.EXACT17_FIELD_ORDER
    assert parsed[gate.FIELD_PARTITION_NAME]["exact17_field_order"] == list(
        gate.EXACT17_FIELD_ORDER
    )
    assert len(gate.EXACT17_FIELD_ORDER) == 17


def test_core15_order_frozen(parsed: dict[str, dict[str, object]]) -> None:
    fields = parsed[gate.FIELD_PARTITION_NAME]
    assert tuple(fields["successful_cross_producer_core15_field_order"]) == (
        gate.CORE15_FIELD_ORDER
    )
    assert gate.CORE15_FIELD_ORDER == gate.EXACT17_FIELD_ORDER[:15]


def test_metadata2_exact(parsed: dict[str, dict[str, object]]) -> None:
    fields = parsed[gate.FIELD_PARTITION_NAME]
    assert fields["producer_metadata_fields"] == ["provenance", "readiness"]
    assert gate.PRODUCER_METADATA_FIELDS == ("provenance", "readiness")


def test_runtime_target_exact(parsed: dict[str, dict[str, object]]) -> None:
    manifest = parsed[gate.MANIFEST_NAME]
    parity = parsed[gate.PARITY_CONTRACT_NAME]
    assert manifest["runtime_fast_path_output17_target"] == (
        "current_public_adapter_output17_v1"
    )
    assert parity["runtime_fast_path"]["runtime_target"] == gate.RUNTIME_TARGET
    assert parity["runtime_fast_path"]["runtime_golden_producer"] == (
        gate.RUNTIME_TARGET
    )


def test_selected_reconciliation_model_exact(
    parsed: dict[str, dict[str, object]],
) -> None:
    assert parsed[gate.PARITY_CONTRACT_NAME]["selected_reconciliation_model"] == (
        "B_plus_E_success_plus_runtime_whole_failure_exact_plus_historical_"
        "failure_self_validation"
    )


@pytest.mark.parametrize(
    "name",
    tuple(gate.REVIEWED_EVIDENCE_SPECS),
)
def test_reviewed_report_identities_exact(name: str) -> None:
    spec = gate.REVIEWED_EVIDENCE_SPECS[name]
    path = STATE / spec["relative_path"]
    metadata = path.lstat()
    payload = path.read_bytes()
    assert stat.S_ISREG(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode)
    assert stat.S_IMODE(metadata.st_mode) == 0o644
    assert (len(payload), payload.count(b"\n"), hashlib.sha256(payload).hexdigest()) == (
        spec["bytes"],
        spec["LF"],
        spec["sha256"],
    )


@pytest.mark.parametrize("name", tuple(gate.OWNER_SPECS))
def test_production_owner_identities_exact(name: str) -> None:
    row = gate._verify_owner_identity(ROOT, name, gate.OWNER_SPECS[name])
    assert row["head_and_worktree_exact"] is True
    assert row["git_mode"] == "100644"
    assert row["worktree_mode"] == "0644"
    assert row["commit_ancestor_or_equal_head"] is True


def test_helper_signatures_exact9() -> None:
    rows = gate._validate_helper_signatures()
    assert len(rows) == gate.FROZEN_HELPER_SIGNATURE_COUNT == 9
    assert [row["helper_name"] for row in rows] == [
        *gate.REFERENCE_HELPER_SIGNATURES,
        *gate.RUNTIME_HELPER_SIGNATURES,
    ]


def test_owner_drift_fails_before_pure_helpers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    specs = copy.deepcopy(gate.OWNER_SPECS)
    specs["current_runtime_adapter"]["sha256"] = "0" * 64
    calls = 0

    def forbidden() -> dict[str, object]:
        nonlocal calls
        calls += 1
        pytest.fail("pure helper execution must follow owner validation")

    monkeypatch.setattr(gate, "OWNER_SPECS", specs)
    monkeypatch.setattr(gate, "_pure_semantic_evidence", forbidden)
    with pytest.raises(ValueError, match=f"^{gate.ERROR_TOKEN}$"):
        gate.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1(
            repo_root=ROOT,
            state_root=STATE,
        )
    assert calls == 0


def test_helper_signature_drift_fails_before_pure_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def drift(unused: bool) -> dict[str, bool]:
        return {}

    def forbidden() -> dict[str, object]:
        nonlocal calls
        calls += 1
        pytest.fail("semantic evidence must follow helper signature validation")

    monkeypatch.setattr(runtime_owner, "_readiness", drift)
    monkeypatch.setattr(gate, "_pure_semantic_evidence", forbidden)
    with pytest.raises(ValueError, match=f"^{gate.ERROR_TOKEN}$"):
        gate.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1(
            repo_root=ROOT,
            state_root=STATE,
        )
    assert calls == 0


def test_reference_success_joint_metadata_exact(evidence: dict[str, object]) -> None:
    output = evidence["outputs"]["joint_reference"]
    assert tuple(output["provenance"]) == gate.REFERENCE_SUCCESS_PROVENANCE_KEYS
    assert output["provenance"] == {
        "joint_index_status": "REMAPPED_EXACT",
        "joint_layout_descriptor": gate.JOINT_LAYOUT,
        "reference_contract_evaluator_only": True,
    }
    assert output["readiness"] == gate.REFERENCE_READINESS
    gate._validate_reference_metadata(output, success=True)


def test_reference_success_no_joint_metadata_exact(
    evidence: dict[str, object],
) -> None:
    output = evidence["outputs"]["no_joint_reference"]
    assert output["provenance"] == {
        "joint_index_status": "JOINT_INDEX_SPACE_UNAVAILABLE",
        "joint_layout_descriptor": None,
        "reference_contract_evaluator_only": True,
    }
    gate._validate_reference_metadata(output, success=True)


def test_reference_failure_metadata_exact(evidence: dict[str, object]) -> None:
    output = evidence["outputs"]["schema_reference"]
    assert tuple(output["provenance"]) == gate.REFERENCE_FAILURE_PROVENANCE_KEYS
    assert output["provenance"] == {
        "joint_index_status": "JOINT_INDEX_SPACE_UNAVAILABLE",
        "reference_contract_evaluator_only": True,
    }
    assert output["readiness"] == gate.REFERENCE_READINESS
    gate._validate_reference_metadata(output, success=False)


def test_reference_failure_descriptor_absent_not_null(
    evidence: dict[str, object],
) -> None:
    provenance = evidence["outputs"]["schema_reference"]["provenance"]
    assert "joint_layout_descriptor" not in provenance


def test_runtime_success_provenance_exact10(evidence: dict[str, object]) -> None:
    output = evidence["outputs"]["joint_runtime"]
    assert tuple(output["provenance"]) == gate.RUNTIME_PROVENANCE_KEYS
    assert len(output["provenance"]) == 10
    assert output["provenance"] == gate._expected_runtime_provenance(
        success=True,
        descriptor=gate.JOINT_LAYOUT,
    )
    gate._validate_runtime_metadata(output, success=True)


def test_runtime_no_joint_provenance_exact(evidence: dict[str, object]) -> None:
    output = evidence["outputs"]["no_joint_runtime"]
    assert output["provenance"]["joint_layout_descriptor"] is None
    assert output["provenance"]["joint_index_status"] == (
        "JOINT_INDEX_SPACE_UNAVAILABLE"
    )
    gate._validate_runtime_metadata(output, success=True)


def test_runtime_failure_provenance_exact(evidence: dict[str, object]) -> None:
    output = evidence["outputs"]["schema_runtime"]
    assert output["provenance"] == gate._expected_runtime_provenance(
        success=False,
        descriptor=None,
    )
    gate._validate_runtime_metadata(output, success=False)


def test_runtime_success_readiness_exact17(evidence: dict[str, object]) -> None:
    readiness = evidence["outputs"]["joint_runtime"]["readiness"]
    assert tuple(readiness) == gate.RUNTIME_READINESS_KEYS
    assert len(readiness) == 17
    assert readiness == gate._runtime_readiness(True)


def test_runtime_failure_readiness_exact17(evidence: dict[str, object]) -> None:
    readiness = evidence["outputs"]["schema_runtime"]["readiness"]
    assert tuple(readiness) == gate.RUNTIME_READINESS_KEYS
    assert len(readiness) == 17
    assert readiness == gate._runtime_readiness(False)


def test_synthetic_joint_core15_exact(evidence: dict[str, object]) -> None:
    reference = evidence["outputs"]["joint_reference"]
    runtime = evidence["outputs"]["joint_runtime"]
    assert gate._deep_exact(_core(reference), _core(runtime))


def test_synthetic_joint_shared_provenance_exact(
    evidence: dict[str, object],
) -> None:
    reference = evidence["outputs"]["joint_reference"]["provenance"]
    runtime = evidence["outputs"]["joint_runtime"]["provenance"]
    assert all(
        gate._deep_exact(reference[field], runtime[field])
        for field in gate.SHARED_SUCCESS_PROVENANCE_FIELDS
    )


def test_synthetic_joint_whole_output17_mismatch_expected(
    evidence: dict[str, object],
) -> None:
    reference = evidence["outputs"]["joint_reference"]
    runtime = evidence["outputs"]["joint_runtime"]
    assert not gate._deep_exact(reference, runtime)
    assert [
        field
        for field in gate.EXACT17_FIELD_ORDER
        if not gate._deep_exact(reference[field], runtime[field])
    ] == ["provenance", "readiness"]


def test_no_joint_core15_and_shared_provenance_parity(
    evidence: dict[str, object],
) -> None:
    reference = evidence["outputs"]["no_joint_reference"]
    runtime = evidence["outputs"]["no_joint_runtime"]
    gate._require_core15_parity(reference, runtime)
    gate._validate_shared_success_provenance(reference, runtime)
    assert reference["pair_values_joint_global_indices"] is None


def test_subset_not_in_batch_core15_parity(evidence: dict[str, object]) -> None:
    reference = evidence["outputs"]["subset_reference"]
    runtime = evidence["outputs"]["subset_runtime"]
    gate._require_core15_parity(reference, runtime)
    statuses = [row["status"] for row in reference["source_entry_outcomes"]]
    assert statuses.count("NOT_IN_BATCH") == 2


def test_subset_overall_success(evidence: dict[str, object]) -> None:
    reference = evidence["outputs"]["subset_reference"]
    runtime = evidence["outputs"]["subset_runtime"]
    assert reference["remap_status"] == runtime["remap_status"] == (
        "REMAPPED_EXACT"
    )


def test_schema_mismatch_common_status_reason(evidence: dict[str, object]) -> None:
    reference = evidence["outputs"]["schema_reference"]
    runtime = evidence["outputs"]["schema_runtime"]
    assert reference["remap_status"] == runtime["remap_status"] == (
        "SCHEMA_VERSION_MISMATCH"
    )
    assert reference["failure_reason"] == runtime["failure_reason"]


def test_schema_mismatch_known_core15_nonparity(
    evidence: dict[str, object],
) -> None:
    reference = evidence["outputs"]["schema_reference"]
    runtime = evidence["outputs"]["schema_runtime"]
    assert gate._core_difference_fields(reference, runtime) == [
        "sample_pair_offsets",
        "sample_validity",
    ]
    assert reference["sample_pair_offsets"] == [0]
    assert reference["sample_validity"] == []
    assert runtime["sample_pair_offsets"] == [0, 0, 0, 0]
    assert runtime["sample_validity"] == [False, False, False]


def test_nonzero_runtime_hard_failure_entry(evidence: dict[str, object]) -> None:
    runtime = evidence["outputs"]["hard_runtime"]
    assert runtime["remap_status"] == "SOURCE_ROW_OUT_OF_RANGE"
    assert runtime["source_entry_outcomes"][2]["status"] == (
        "SOURCE_ROW_OUT_OF_RANGE"
    )
    assert runtime["source_entry_outcomes"][0]["status"] == "ENTRY_INVALID"


def test_historical_hard_failure_entry_zero(evidence: dict[str, object]) -> None:
    reference = evidence["outputs"]["hard_reference"]
    runtime = evidence["outputs"]["hard_runtime"]
    assert reference["source_entry_outcomes"][0]["status"] == (
        "SOURCE_ROW_OUT_OF_RANGE"
    )
    assert not gate._deep_exact(
        reference["source_entry_outcomes"],
        runtime["source_entry_outcomes"],
    )


def test_universal_failure_core15_exact_forbidden(
    parsed: dict[str, dict[str, object]],
) -> None:
    fields = parsed[gate.FIELD_PARTITION_NAME]
    parity = parsed[gate.PARITY_CONTRACT_NAME]
    report = parsed[gate.REPORT_NAME]
    assert fields["universal_failure_core15_cross_producer_authority"] is False
    assert parity["universal_failure_core15_cross_producer_parity"] is False
    assert report["universal_failure_core15_cross_producer_parity"] is False


def test_runtime_fast_success_and_failure_whole_target(
    parsed: dict[str, dict[str, object]],
) -> None:
    parity = parsed[gate.PARITY_CONTRACT_NAME]["runtime_fast_path"]
    report = parsed[gate.REPORT_NAME]
    assert parity == {
        "failure": True,
        "old_adapter_report_authoritative": False,
        "runtime_golden_producer": gate.RUNTIME_TARGET,
        "runtime_target": gate.RUNTIME_TARGET,
        "runtime_whole_output17_exact_required": True,
        "success": True,
    }
    assert report["runtime_success_whole_output17_target_exact"] is True
    assert report["runtime_failure_whole_output17_target_exact"] is True


def test_option_verdicts_exact(parsed: dict[str, dict[str, object]]) -> None:
    assert parsed[gate.PARITY_CONTRACT_NAME]["option_verdicts"] == {
        "Option_A": "REJECT",
        "Option_B": "ACCEPT",
        "Option_C": "REJECT_V1",
        "Option_D": "REJECT_V1",
        "Option_E_success": "ACCEPT",
        "Option_E_universal_failure": "REJECT",
    }


def test_negative_matrix_exact26_and_executed(
    parsed: dict[str, dict[str, object]],
    evidence: dict[str, object],
) -> None:
    negative = parsed[gate.NEGATIVE_MATRIX_NAME]
    assert negative["case_count"] == len(gate.NEGATIVE_CASES) == 26
    assert [row["case_id"] for row in negative["cases"]] == [
        case_id for case_id, unused in gate.NEGATIVE_CASES
    ]
    assert gate._execute_negative_matrix(evidence) == [
        case_id for case_id, unused in gate.NEGATIVE_CASES
    ]


def test_no_semantic_promotion(parsed: dict[str, dict[str, object]]) -> None:
    metadata = parsed[gate.METADATA_CONTRACT_NAME]
    reference = metadata["validators"]["reference_success_metadata_v1"]
    runtime = metadata["validators"]["runtime_success_metadata_v1"]
    assert reference["readiness_exact_constant_values"][
        "public_adapter_implemented"
    ] is False
    assert "public_adapter_implemented" not in runtime[
        "readiness_exact_constant_values"
    ]
    assert "reference_contract_evaluator_only" not in runtime[
        "provenance_exact_key_order"
    ]
    assert metadata["historical_snapshot_must_not_propagate_to_runtime"] is True


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


def test_public_build_supports_clean_tracked_successor_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        gate,
        "_repository_lifecycle",
        lambda unused: "clean-tracked-successor",
    )
    result = gate.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1(
        repo_root=ROOT,
        state_root=STATE,
    )
    report = json.loads(result[gate.REPORT_NAME])
    assert report["repository_lifecycle"] == "clean-tracked-successor"
    assert report["gate_status"] == gate.GATE_STATUS


def test_fifth_repository_path_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    def run_git(unused: Path, arguments: Sequence[str]) -> str:
        if tuple(arguments) == (
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ):
            return "\n".join(
                [
                    *(f"?? {path}" for path in gate.REPOSITORY_EXACT4),
                    "?? forbidden-fifth.txt",
                ]
            )
        return ""

    monkeypatch.setattr(gate, "_run_git", run_git)
    with pytest.raises(gate._ContractInvariantError):
        gate._repository_lifecycle(ROOT)


def test_gate_source_forbids_public_heavy_products() -> None:
    tree = ast.parse((ROOT / gate.MODULE_PATH).read_text(encoding="utf-8"))
    forbidden = {
        "build_covapie_current11_task2_batch_index_remap_adapter_v1",
        "build_covapie_current11_task2_batch_index_remap_contract_gate_v1",
        "build_covapie_current11_task2_batch_index_remap_predecessor_successor_v1",
        "build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1",
        "_contract_exact6",
    }
    called = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    } | {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert called.isdisjoint(forbidden)


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
            "--cache",
            "yes",
        ),
        (
            "--repo-root",
            os.fspath(ROOT),
            "--state-root",
            os.fspath(STATE),
            "--train",
        ),
    ),
)
def test_checker_cli_rejects_expanded_interface(
    arguments: tuple[str, ...],
) -> None:
    completed = subprocess.run(
        (sys.executable, "-B", os.fspath(CHECKER_PATH), *arguments),
        cwd=ROOT,
        env=_subprocess_env(),
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 1
    assert completed.stdout == b""
    assert completed.stderr == (gate.ERROR_TOKEN + "\n").encode("ascii")


def test_checker_double_build_and_compact_json() -> None:
    completed = subprocess.run(
        (
            sys.executable,
            "-B",
            os.fspath(CHECKER_PATH),
            "--repo-root",
            os.fspath(ROOT),
            "--state-root",
            os.fspath(STATE),
        ),
        cwd=ROOT,
        env=_subprocess_env(),
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stderr == b""
    assert completed.stdout.count(b"\n") == 1
    summary = json.loads(completed.stdout)
    assert summary["status"] == gate.GATE_STATUS
    assert summary["public_gate_build_count"] == 2
    assert summary["double_build_byte_identical"] is True
    assert completed.stdout == (
        json.dumps(summary, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("ascii")


def test_repository_and_reviewed_evidence_read_only() -> None:
    before_repository = gate._repository_snapshot(ROOT)
    before_evidence = gate._evidence_snapshot(STATE)
    gate.build_covapie_current11_task2_batch_index_remap_output17_semantic_reconciliation_contract_gate_v1(
        repo_root=ROOT,
        state_root=STATE,
    )
    assert gate._repository_snapshot(ROOT) == before_repository
    assert gate._evidence_snapshot(STATE) == before_evidence


def test_canonical_mask_sentinel_exact5_including_scaffold_only_b3(
    parsed: dict[str, dict[str, object]],
) -> None:
    masks = parsed[gate.MANIFEST_NAME]["canonical_mask_semantics"]
    assert [(row["semantic_name"], row["display_alias"]) for row in masks] == [
        ("warhead_only", "A"),
        ("linker_plus_warhead", "B"),
        ("scaffold_plus_warhead", "B2"),
        ("scaffold_only", "B3"),
        ("scaffold_plus_linker_plus_warhead", "C"),
    ]


def test_readiness_remains_fail_closed(
    parsed: dict[str, dict[str, object]],
) -> None:
    readiness = parsed[gate.REPORT_NAME]["readiness"]
    assert readiness["ready_for_output17_lightweight_semantic_parity_probe"] is True
    assert readiness[
        "ready_for_public_remap_adapter_hot_loop_contract_implementation"
    ] is False
    assert readiness["ready_for_remap_hot_loop_contract_gate"] is False
    assert readiness["hot_loop_blocker"] == (
        "output17_lightweight_semantic_parity_probe_not_yet_passed"
    )
    assert readiness["current_adapter_directly_accepts_successor_exact6"] is False
    assert readiness["current_compiler_context_uses_successor_authority"] is False
    assert readiness["compiler_context_rebuild_device_identity_risk"] is True
    assert readiness["ready_for_dataloader_integration"] is False
    assert readiness["ready_for_model_integration"] is False
    assert readiness["ready_for_loss_integration"] is False
    assert readiness["feature_semantics_reaudit_required_before_training"] is True
    assert readiness["ready_for_training"] is False
    assert readiness["checkpoint_bytes_read"] is False
    assert readiness["model_parameter_shape_change_required"] is False
    assert readiness["commit_created"] is False
    assert readiness["push_performed"] is False


def test_historical_immutability_flags_exact(
    parsed: dict[str, dict[str, object]],
) -> None:
    assert parsed[gate.MANIFEST_NAME]["historical_immutability"] == {
        "current_adapter_frozen": True,
        "historical_reference_vectors_frozen": True,
        "historical_remap_contract_gate_frozen": True,
        "historical_stable5_frozen": True,
        "published_successor_frozen": True,
    }


def test_candidate_exact4_file_safety() -> None:
    assert len(gate.REPOSITORY_EXACT4) == 4
    for relative in gate.REPOSITORY_EXACT4:
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
