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
from types import ModuleType, SimpleNamespace
from typing import Sequence

import pytest


ROOT = Path(__file__).resolve().parents[1]
STATE = (ROOT.parent / "covapie-state").resolve(strict=True)
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1
    as gate,
)


CHECKER_PATH = ROOT / gate.SCRIPT_PATH
EXPECTED_DIGEST = "d39d40b634a3cdd38c43c3636dda57ffb5540ae3a9c9a4b30dfaca70e56b4cb1"


def _load_checker() -> ModuleType:
    name = "covapie_state_mount_device_transition_checker_test"
    spec = importlib.util.spec_from_file_location(name, CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _parsed(artifacts: dict[str, bytes]) -> dict[str, object]:
    return {
        name: json.loads(payload.decode("utf-8"))
        for name, payload in artifacts.items()
    }


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return gate.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1(
        repo_root=ROOT,
        state_root=STATE,
    )


@pytest.fixture(scope="module")
def parsed(artifacts: dict[str, bytes]) -> dict[str, object]:
    return _parsed(artifacts)


@pytest.fixture(scope="module")
def checker_run() -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
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
        env={
            **os.environ,
            "PYTHONPATH": "src:.",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        capture_output=True,
        check=False,
    )


def _changed_stat(value: os.stat_result, **changes: int) -> SimpleNamespace:
    fields = {
        "st_mode": value.st_mode,
        "st_dev": value.st_dev,
        "st_ino": value.st_ino,
        "st_size": value.st_size,
        "st_mtime_ns": value.st_mtime_ns,
    }
    fields.update(changes)
    return SimpleNamespace(**fields)


def _all_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return set(value) | set().union(*(_all_keys(item) for item in value.values()))
    if isinstance(value, list):
        return set().union(*(_all_keys(item) for item in value))
    return set()


def test_public_exact1_keyword_only_api() -> None:
    function = gate.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1
    assert gate.__all__ == (function.__name__,)
    signature = inspect.signature(function)
    assert tuple(signature.parameters) == ("repo_root", "state_root")
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    with pytest.raises(TypeError):
        function(ROOT, STATE)  # type: ignore[misc]


def test_silent_import_and_stdlib_only_scope() -> None:
    completed = subprocess.run(
        (sys.executable, "-B", "-c", f"import {gate.__name__}"),
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
    tree = ast.parse((ROOT / gate.MODULE_PATH).read_text(encoding="utf-8"))
    imports = {
        node.names[0].name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
    }
    imports.update(
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    )
    assert imports <= {
        "__future__",
        "ast",
        "csv",
        "hashlib",
        "io",
        "json",
        "os",
        "pathlib",
        "re",
        "stat",
        "subprocess",
        "typing",
    }


def test_historical_and_heavy_public_gates_are_not_called() -> None:
    source = (ROOT / gate.MODULE_PATH).read_text(encoding="utf-8")
    assert (
        "evaluate_covapie_current11_unit_000001_partial_supervision_routing_gate_v1("
        not in source
    )
    assert (
        "build_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1("
        not in source
    )
    assert "build_covapie_current11_task2_batch_index_remap_contract_gate_v1(" not in source
    assert "_contract_exact6" not in source


def test_exact5_order_type_and_canonical_bytes(artifacts: dict[str, bytes]) -> None:
    assert type(artifacts) is dict
    assert tuple(artifacts) == gate.ARTIFACT_NAMES
    assert len(artifacts) == 5
    for payload in artifacts.values():
        assert type(payload) is bytes and 0 < len(payload) < 1024 * 1024
        assert payload.endswith(b"\n") and not payload.endswith(b"\n\n")
        assert b"\r" not in payload and b"\0" not in payload
        assert not payload.startswith(b"\xef\xbb\xbf")
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


def test_stable_digest_framing_and_report_exclusion(
    artifacts: dict[str, bytes], parsed: dict[str, object]
) -> None:
    digest = hashlib.sha256()
    digest.update(gate.CONTRACT_DIGEST_DOMAIN)
    for name in gate.STABLE_ARTIFACT_NAMES:
        encoded = name.encode("utf-8")
        payload = artifacts[name]
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    assert digest.hexdigest() == EXPECTED_DIGEST
    report = parsed[gate.ARTIFACT_NAMES[4]]
    assert report["contract_digest"] == EXPECTED_DIGEST
    changed = dict(artifacts)
    changed[gate.ARTIFACT_NAMES[4]] = b"{}\n"
    assert gate._contract_digest(
        {name: changed[name] for name in gate.STABLE_ARTIFACT_NAMES}
    ) == EXPECTED_DIGEST


def test_transition_exact3_order_and_pairs(parsed: dict[str, object]) -> None:
    transitions = parsed[gate.ARTIFACT_NAMES[1]]
    assert isinstance(transitions, list) and len(transitions) == 3
    assert [row["object_id"] for row in transitions] == list(
        gate.TRANSITION_OBJECT_IDS
    )
    assert [
        (row["historical_identity"], row["authorized_current_identity"])
        for row in transitions
    ] == [
        (
            {"st_dev": 49, "st_ino": gate.DOSSIER_INODE},
            {"st_dev": 50, "st_ino": gate.DOSSIER_INODE},
        ),
        (
            {"st_dev": 49, "st_ino": gate.ROUTING_CANONICAL_INODE},
            {"st_dev": 50, "st_ino": gate.ROUTING_CANONICAL_INODE},
        ),
        (
            {"st_dev": 49, "st_ino": gate.ROUTING_OBJECT_INODE},
            {"st_dev": 50, "st_ino": gate.ROUTING_OBJECT_INODE},
        ),
    ]
    assert all(row["device_transition_only"] is True for row in transitions)
    assert all(row["transition_authorized"] is True for row in transitions)


def test_mount_topology_stable_fields_and_id_exclusion(
    parsed: dict[str, object], artifacts: dict[str, bytes]
) -> None:
    manifest = parsed[gate.ARTIFACT_NAMES[0]]
    topology = manifest["mount_topology"]
    assert topology == {
        "fstype": "gpfs",
        "source": "cpfs01",
        "root": gate.MOUNT_ROOT,
        "target": gate.MOUNT_TARGET,
        "historical_major_minor": "0:49",
        "current_major_minor": "0:50",
        "historical_st_dev": 49,
        "current_st_dev": 50,
        "most_specific_unique_mount_record": True,
        "transition_object_count_on_mount": 3,
    }
    lineage = parsed[gate.ARTIFACT_NAMES[2]]
    assert "mount_id" not in _all_keys(lineage)
    assert "parent_mount_id" not in _all_keys(lineage)
    report = parsed[gate.ARTIFACT_NAMES[4]]
    diagnostics = report["mount_namespace_diagnostics"]
    assert diagnostics["diagnostic_only"] is True
    assert diagnostics["stable_contract_digest_participation"] is False
    assert artifacts[gate.ARTIFACT_NAMES[4]] not in [
        artifacts[name] for name in gate.STABLE_ARTIFACT_NAMES
    ]


def test_dossier_exact8_and_manifest_semantics(parsed: dict[str, object]) -> None:
    lineage = parsed[gate.ARTIFACT_NAMES[2]]
    dossier = lineage["dossier_exact8"]
    assert dossier["state_relative_path"] == gate.DOSSIER_RELATIVE
    assert dossier["mode"] == "0755"
    assert [(row["name"], row["bytes"], row["sha256"]) for row in dossier["inventory"]] == [
        (name, spec[0], spec[2]) for name, spec in gate.DOSSIER_LEAVES.items()
    ]
    semantic = dossier["semantic_manifest_verification"]
    assert semantic["review_unit_id"] == (
        "CURRENT11_REACTION_TRANSFORMATION_REVIEW_UNIT_000001"
    )
    assert semantic["parent_review_unit_id"] == (
        "CURRENT11_FAMILY_RULE_APPROVAL_REVIEW_UNIT_000001"
    )
    assert semantic["sample_count"] == 2
    assert semantic["semantic_question_count"] == 25
    assert semantic["semantic_question_count_source_key"] == "question_count"
    assert semantic["non_authoritative_review_aid"] is True
    assert semantic["blank_or_incomplete_review_promoted_to_authority"] is False
    assert semantic["ready_for_training"] is False


def test_routing_readlink_exact(parsed: dict[str, object]) -> None:
    canonical = parsed[gate.ARTIFACT_NAMES[2]]["routing_canonical"]
    assert canonical == {
        "state_relative_path": gate.ROUTING_CANONICAL_RELATIVE,
        "readlink": gate.ROUTING_READLINK,
        "basename_only_relative_target": True,
        "resolves_to_state_relative_path": gate.ROUTING_OBJECT_RELATIVE,
        "symlink_permission_bits_in_semantic_identity": False,
    }


def test_routing_exact4_and_aggregate(parsed: dict[str, object]) -> None:
    routing = parsed[gate.ARTIFACT_NAMES[2]]["routing_object_exact4"]
    assert routing["mode"] == "0755"
    assert [(row["name"], row["bytes"], row["sha256"]) for row in routing["inventory"]] == [
        (name, spec[0], spec[2]) for name, spec in gate.ROUTING_LEAVES.items()
    ]
    assert routing["aggregate_sha256"] == gate.ROUTING_AGGREGATE
    assert routing["aggregate_domain"] == (
        "COVAPIE_CURRENT11_DATASET_PARTIAL_SUPERVISION_ROUTING_SIDECAR_"
        "GPFS_ATOMIC_ALIAS_V2"
    )


def test_routing_semantic_manifest_checks(parsed: dict[str, object]) -> None:
    semantic = parsed[gate.ARTIFACT_NAMES[2]]["routing_object_exact4"][
        "semantic_manifest_verification"
    ]
    assert semantic["sample_identity_order_count"] == 11
    assert semantic["semantic_task_order_count"] == 25
    assert semantic["routing_record_cardinality"] == 275
    assert semantic["canonical_mask_semantics"] == [
        {"semantic_name": semantic_name, "display_alias": alias}
        for semantic_name, alias in gate.CANONICAL_MASKS
    ]
    assert semantic["canonical_mask_semantics"][3] == {
        "semantic_name": "scaffold_only",
        "display_alias": "B3",
    }
    assert semantic["ready_for_dataloader_integration"] is False
    assert semantic["ready_for_model_integration"] is False
    assert semantic["ready_for_loss_integration"] is False
    assert semantic["loss_integration_published_source_key"] == (
        "training_loss_authorized"
    )
    assert semantic["feature_semantics_reaudit_required_before_training"] is True
    assert semantic["ready_for_training"] is False


def test_historical_exact8_repository_identity_table(parsed: dict[str, object]) -> None:
    groups = parsed[gate.ARTIFACT_NAMES[2]]["historical_repository_lineage"]
    assert [group["introduction_commit"] for group in groups] == [
        gate.UNIT_INTRODUCTION_COMMIT,
        gate.PROJECTION_INTRODUCTION_COMMIT,
    ]
    rows = [row for group in groups for row in group["current_head_exact4"]]
    assert len(rows) == 8
    assert {
        row["path"]: (
            row["bytes"],
            row["LF"],
            row["sha256"],
            row["git_blob"],
            row["git_mode"],
        )
        for row in rows
    } == {
        path: (*spec[:3], spec[3], "100644")
        for path, spec in gate.HISTORICAL_FILE_SPECS.items()
    }
    assert groups[0]["historical_identity_constants"] == {
        "DOSSIER_IDENTITY": [49, gate.DOSSIER_INODE]
    }
    assert groups[1]["historical_identity_constants"] == {
        "CANONICAL_IDENTITY": [49, gate.ROUTING_CANONICAL_INODE],
        "OBJECT_IDENTITY": [49, gate.ROUTING_OBJECT_INODE],
    }


def test_precondition_report_identity(parsed: dict[str, object]) -> None:
    identity = parsed[gate.ARTIFACT_NAMES[2]]["precondition_report"]
    assert identity == {
        "state_relative_path": gate.PRECONDITION_RELATIVE,
        "bytes": 31396,
        "LF": 619,
        "sha256": "ea4583db1101cf19b78e10ad7c28a99f330d140150c2362231f312c21b2cf345",
        "mode": "0644",
        "reviewed_predecessor_evidence": True,
        "substitutes_for_current_state_validation": False,
    }


def test_negative_matrix_complete(parsed: dict[str, object]) -> None:
    matrix = parsed[gate.ARTIFACT_NAMES[3]]
    assert len(matrix) == len(gate.NEGATIVE_CASE_IDS) == 24
    assert [row["case_index"] for row in matrix] == list(range(24))
    assert [row["case_id"] for row in matrix] == list(gate.NEGATIVE_CASE_IDS)
    assert {row["expected_result"] for row in matrix} == {"fail_closed"}
    assert {row["error_token"] for row in matrix} == {gate.ERROR_TOKEN}


@pytest.mark.parametrize(
    ("index", "field", "value"),
    (
        (0, "historical_identity", {"st_dev": 48, "st_ino": gate.DOSSIER_INODE}),
        (0, "authorized_current_identity", {"st_dev": 49, "st_ino": gate.DOSSIER_INODE}),
        (0, "authorized_current_identity", {"st_dev": 51, "st_ino": gate.DOSSIER_INODE}),
        (0, "authorized_current_identity", {"st_dev": 50, "st_ino": gate.DOSSIER_INODE + 1}),
        (0, "state_relative_path", "wrong/path"),
        (0, "object_kind", "symlink"),
        (1, "authorized_current_identity", {"st_dev": 50, "st_ino": gate.ROUTING_CANONICAL_INODE + 1}),
        (2, "authorized_current_identity", {"st_dev": 50, "st_ino": gate.ROUTING_OBJECT_INODE + 1}),
    ),
)
def test_transition_identity_path_type_drift_fails_closed(
    index: int, field: str, value: object
) -> None:
    records = copy.deepcopy(gate._expected_transition_records())
    records[index][field] = value
    with pytest.raises(ValueError, match=f"^{gate.ERROR_TOKEN}$"):
        gate._validate_transition_records(records)


@pytest.mark.parametrize("mutation", ("missing", "extra", "reordered"))
def test_transition_object_set_drift_fails_closed(mutation: str) -> None:
    records = copy.deepcopy(gate._expected_transition_records())
    if mutation == "missing":
        records.pop()
    elif mutation == "extra":
        records.append(copy.deepcopy(records[-1]))
    else:
        records[0], records[1] = records[1], records[0]
    with pytest.raises(ValueError, match=f"^{gate.ERROR_TOKEN}$"):
        gate._validate_transition_records(records)


def test_wrong_live_device_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    dossier_path = STATE / gate.DOSSIER_RELATIVE
    original = gate._lstat

    def changed(path: Path) -> object:
        value = original(path)
        if path == dossier_path:
            return _changed_stat(value, st_dev=51)
        return value

    monkeypatch.setattr(gate, "_lstat", changed)
    with pytest.raises(ValueError, match=f"^{gate.ERROR_TOKEN}$"):
        gate._inspect_dossier(STATE)


def test_wrong_live_inode_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    object_path = STATE / gate.ROUTING_OBJECT_RELATIVE
    original = gate._lstat

    def changed(path: Path) -> object:
        value = original(path)
        if path == object_path:
            return _changed_stat(value, st_ino=gate.ROUTING_OBJECT_INODE + 1)
        return value

    monkeypatch.setattr(gate, "_lstat", changed)
    with pytest.raises(ValueError, match=f"^{gate.ERROR_TOKEN}$"):
        gate._inspect_routing_object(STATE)


def test_readlink_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate, "_readlink", lambda _path: "wrong-target")
    with pytest.raises(ValueError, match=f"^{gate.ERROR_TOKEN}$"):
        gate._inspect_routing_canonical(STATE)


def test_inventory_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    dossier_path = STATE / gate.DOSSIER_RELATIVE
    original = gate._listdir

    def changed(path: Path) -> tuple[str, ...]:
        value = original(path)
        if path == dossier_path:
            return (*value, "fourth_object_or_extra_child")
        return value

    monkeypatch.setattr(gate, "_listdir", changed)
    with pytest.raises(ValueError, match=f"^{gate.ERROR_TOKEN}$"):
        gate._inspect_dossier(STATE)


def test_leaf_content_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    target = STATE / gate.DOSSIER_RELATIVE / "README.md"
    original = gate._read_bytes

    def changed(path: Path) -> bytes:
        payload = original(path)
        return b"X" + payload[1:] if path == target else payload

    monkeypatch.setattr(gate, "_read_bytes", changed)
    with pytest.raises(ValueError, match=f"^{gate.ERROR_TOKEN}$"):
        gate._inspect_dossier(STATE)


def test_aggregate_content_drift_fails_closed() -> None:
    object_path = STATE / gate.ROUTING_OBJECT_RELATIVE
    payloads = {name: (object_path / name).read_bytes() for name in gate.ROUTING_LEAVES}
    assert gate._aggregate_sha256(payloads) == gate.ROUTING_AGGREGATE
    payloads[next(iter(payloads))] += b"x"
    assert gate._aggregate_sha256(payloads) != gate.ROUTING_AGGREGATE


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("source", "wrong"),
        ("fstype", "wrong"),
        ("root", "/wrong"),
        ("target", "/wrong"),
        ("major_minor", "0:51"),
    ),
)
def test_mount_topology_drift_fails_closed(field: str, value: str) -> None:
    record: dict[str, object] = {
        "mount_id": 1,
        "parent_mount_id": 2,
        "major_minor": gate.CURRENT_MAJOR_MINOR,
        "root": gate.MOUNT_ROOT,
        "target": gate.MOUNT_TARGET,
        "fstype": gate.MOUNT_FSTYPE,
        "source": gate.MOUNT_SOURCE,
    }
    record[field] = value
    with pytest.raises(ValueError, match=f"^{gate.ERROR_TOKEN}$"):
        gate._validate_mount_topology_record(record)


def test_mountinfo_octal_unescape() -> None:
    payload = (
        b"10 9 0:50 /root\\040with\\134slash /target\\040path rw - gpfs "
        b"source\\040name rw\n"
    )
    record = gate._parse_mountinfo(payload)[0]
    assert record["root"] == "/root with\\slash"
    assert record["target"] == "/target path"
    assert record["source"] == "source name"


def test_no_wildcard_or_caller_override_semantics(parsed: dict[str, object]) -> None:
    signature = inspect.signature(
        gate.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1
    )
    assert tuple(signature.parameters) == ("repo_root", "state_root")
    transitions = parsed[gate.ARTIFACT_NAMES[1]]
    assert all(type(row["historical_identity"]["st_dev"]) is int for row in transitions)
    assert all(
        type(row["authorized_current_identity"]["st_dev"]) is int
        for row in transitions
    )
    assert not {
        "device_override",
        "path_override",
        "allow_list",
        "ignore_device",
        "transition_parameter",
        "mount_id_parameter",
    }.intersection(_all_keys(parsed[gate.ARTIFACT_NAMES[0]]))


def test_readiness_fail_closed(parsed: dict[str, object]) -> None:
    readiness = parsed[gate.ARTIFACT_NAMES[4]]["readiness"]
    assert readiness["state_mount_device_transition_contract_gate_passed"] is True
    assert readiness["mount_device_transition_only"] is True
    assert readiness["ready_for_remap_predecessor_successor_integration"] is True
    assert readiness[
        "ready_for_public_remap_adapter_hot_loop_contract_implementation"
    ] is False
    assert readiness["compiler_context_rebuild_device_identity_risk"] is True
    assert readiness["ready_for_dataloader_integration"] is False
    assert readiness["ready_for_model_integration"] is False
    assert readiness["ready_for_loss_integration"] is False
    assert readiness["feature_semantics_reaudit_required_before_training"] is True
    assert readiness["ready_for_training"] is False
    assert readiness["checkpoint_bytes_read"] is False
    assert readiness["model_parameter_shape_change_required"] is False


def test_deterministic_double_public_build(artifacts: dict[str, bytes]) -> None:
    second = gate.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1(
        repo_root=ROOT,
        state_root=STATE,
    )
    assert second == artifacts


def test_public_gate_is_repo_and_state_read_only() -> None:
    before_repo = gate._direct_repository_snapshot(ROOT)
    before_state = gate._direct_state_snapshot(STATE)
    gate.build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1(
        repo_root=ROOT,
        state_root=STATE,
    )
    assert gate._direct_repository_snapshot(ROOT) == before_repo
    assert gate._direct_state_snapshot(STATE) == before_state


@pytest.mark.parametrize("lifecycle", ("precommit-untracked", "clean-tracked-successor"))
def test_checker_repository_lifecycle_profiles(
    monkeypatch: pytest.MonkeyPatch, lifecycle: str
) -> None:
    checker = _load_checker()
    blob = "a" * 40

    def run_git(_repo: Path, arguments: Sequence[str]) -> str:
        call = tuple(arguments)
        if call == ("status", "--porcelain=v1", "--untracked-files=all"):
            if lifecycle == "precommit-untracked":
                return "\n".join(f"?? {path}" for path in gate.REPOSITORY_EXACT4) + "\n"
            return ""
        if call == ("ls-files", "--stage", "--", *gate.REPOSITORY_EXACT4):
            if lifecycle == "precommit-untracked":
                return ""
            return "\n".join(
                f"100644 {blob} 0\t{path}" for path in gate.REPOSITORY_EXACT4
            ) + "\n"
        if call[:2] == ("hash-object", "--no-filters") or call[0] == "rev-parse":
            return blob + "\n"
        pytest.fail(f"unexpected git call: {call!r}")

    monkeypatch.setattr(checker, "_run_git", run_git)
    assert checker._repository_lifecycle(ROOT) == lifecycle


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
                [
                    *(f"?? {path}" for path in gate.REPOSITORY_EXACT4),
                    "?? forbidden-fifth.txt",
                ]
            )
        return ""

    monkeypatch.setattr(checker, "_run_git", run_git)
    with pytest.raises(ValueError, match=f"^{gate.ERROR_TOKEN}$"):
        checker._repository_lifecycle(ROOT)


def test_checker_cli_pass_and_dynamic_lifecycle(
    checker_run: subprocess.CompletedProcess[bytes],
) -> None:
    assert checker_run.returncode == 0
    assert checker_run.stderr == b""
    assert checker_run.stdout.count(b"\n") == 1
    summary = json.loads(checker_run.stdout)
    checker = _load_checker()
    expected_lifecycle = checker._repository_lifecycle(ROOT)
    assert expected_lifecycle in ("precommit-untracked", "clean-tracked-successor")
    assert summary["repository_lifecycle"] == expected_lifecycle
    assert summary["status"] == "PASS_STATE_MOUNT_DEVICE_TRANSITION_CONTRACT_ONLY"
    assert summary["contract_digest"] == EXPECTED_DIGEST
    assert summary["public_gate_build_count"] == 2
    assert summary["double_build_byte_identical"] is True
    assert summary["repository_unchanged"] is True
    assert summary["state_unchanged"] is True
    assert summary["historical_public_gates_called"] is False
    assert summary["heavy_remap_contract_chain_called"] is False
    assert checker_run.stdout == (
        json.dumps(summary, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


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
        ("--allow-list", "49,50"),
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
    assert completed.stderr == (gate.ERROR_TOKEN + "\n").encode("ascii")


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
