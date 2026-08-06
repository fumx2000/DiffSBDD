from __future__ import annotations

import ast
import copy
import csv
import hashlib
import inspect
import io
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_current11_runtime_sample_and_role_order_carrier_contract_gate_v1 as gate,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
STATE_ROOT = REPO_ROOT.parent / "covapie-state"
MODULE = REPO_ROOT / gate._REPOSITORY_EXACT4[0]
CHECKER = REPO_ROOT / gate._REPOSITORY_EXACT4[1]
DESIGN = STATE_ROOT / gate._DESIGN_RELATIVE
ERROR = gate._ERROR


def _git_status() -> bytes:
    return subprocess.run(
        ("git", "status", "--porcelain=v1", "--untracked-files=all"),
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _json(name: str, artifacts: dict[str, bytes]) -> dict[str, object]:
    value = json.loads(
        artifacts[name].decode("utf-8"),
        parse_constant=lambda _value: (_ for _ in ()).throw(AssertionError()),
    )
    assert type(value) is dict
    return value


def _csv(name: str, artifacts: dict[str, bytes]) -> list[dict[str, str]]:
    return list(
        csv.DictReader(
            io.StringIO(artifacts[name].decode("utf-8"), newline=""),
            strict=True,
        )
    )


@pytest.fixture(scope="session")
def build_evidence() -> dict[str, object]:
    status_before = _git_status()
    formal_before = gate._formal_snapshot(STATE_ROOT / gate._FORMAL_RELATIVE)
    design_before = (
        DESIGN.lstat().st_mode,
        DESIGN.lstat().st_size,
        DESIGN.lstat().st_mtime_ns,
        hashlib.sha256(DESIGN.read_bytes()).hexdigest(),
    )
    reads: list[str] = []
    adapter_calls: list[dict[str, object]] = []
    adapter_exact2: list[dict[str, bytes]] = []
    remap_exact6: list[dict[str, bytes]] = []
    original = gate._read_regular
    original_adapter = (
        gate._adapter.build_covapie_current11_task2_batch_index_remap_adapter_v1
    )
    original_remap = (
        gate._remap_gate.build_covapie_current11_task2_batch_index_remap_contract_gate_v1
    )

    def observed(root: Path, relative: str, expected_sha256: str | None = None) -> bytes:
        assert relative != gate._DESIGN_RELATIVE
        reads.append(relative)
        return original(root, relative, expected_sha256)

    def observed_adapter(**kwargs: object) -> dict[str, bytes]:
        adapter_calls.append(copy.deepcopy(kwargs))
        result = original_adapter(**kwargs)
        adapter_exact2.append(copy.deepcopy(result))
        return result

    def observed_remap(**kwargs: object) -> dict[str, bytes]:
        result = original_remap(**kwargs)
        remap_exact6.append(copy.deepcopy(result))
        return result

    gate._read_regular = observed
    gate._adapter.build_covapie_current11_task2_batch_index_remap_adapter_v1 = (
        observed_adapter
    )
    gate._remap_gate.build_covapie_current11_task2_batch_index_remap_contract_gate_v1 = (
        observed_remap
    )
    try:
        first = gate.build_covapie_current11_runtime_sample_and_role_order_carrier_contract_gate_v1(
            repo_root=REPO_ROOT,
            state_root=STATE_ROOT,
        )
        second = gate.build_covapie_current11_runtime_sample_and_role_order_carrier_contract_gate_v1(
            repo_root=REPO_ROOT,
            state_root=STATE_ROOT,
        )
    finally:
        gate._read_regular = original
        gate._adapter.build_covapie_current11_task2_batch_index_remap_adapter_v1 = (
            original_adapter
        )
        gate._remap_gate.build_covapie_current11_task2_batch_index_remap_contract_gate_v1 = (
            original_remap
        )
    return {
        "first": first,
        "second": second,
        "reads": reads,
        "adapter_calls": adapter_calls,
        "adapter_exact2": adapter_exact2,
        "remap_exact6": remap_exact6,
        "status_before": status_before,
        "status_after": _git_status(),
        "formal_before": formal_before,
        "formal_after": gate._formal_snapshot(STATE_ROOT / gate._FORMAL_RELATIVE),
        "design_before": design_before,
        "design_after": (
            DESIGN.lstat().st_mode,
            DESIGN.lstat().st_size,
            DESIGN.lstat().st_mtime_ns,
            hashlib.sha256(DESIGN.read_bytes()).hexdigest(),
        ),
    }


@pytest.fixture(scope="session")
def artifacts(build_evidence: dict[str, object]) -> dict[str, bytes]:
    value = build_evidence["first"]
    assert type(value) is dict
    return value


@pytest.fixture(scope="session")
def manifest(artifacts: dict[str, bytes]) -> dict[str, object]:
    return _json(gate._MANIFEST, artifacts)


@pytest.fixture(scope="session")
def role_registry(artifacts: dict[str, bytes]) -> dict[str, object]:
    return _json(gate._ROLE_REGISTRY, artifacts)


@pytest.fixture(scope="session")
def public_predecessor_fixture(build_evidence: dict[str, object]) -> dict[str, object]:
    calls = build_evidence["adapter_calls"]
    exact2 = build_evidence["adapter_exact2"]
    exact6 = build_evidence["remap_exact6"]
    assert type(calls) is list and len(calls) == 2
    assert type(exact2) is list and len(exact2) == 2
    assert type(exact6) is list and len(exact6) >= 2
    assert calls[0] == calls[1]
    assert exact2[0] == exact2[1]
    return {
        "adapter_input": copy.deepcopy(calls[0]["adapter_input"]),
        "exact2": copy.deepcopy(exact2[0]),
        "exact6": copy.deepcopy(exact6[0]),
    }


def test_unique_keyword_only_public_api() -> None:
    assert gate.__all__ == (
        "build_covapie_current11_runtime_sample_and_role_order_carrier_contract_gate_v1",
    )
    signature = inspect.signature(
        gate.build_covapie_current11_runtime_sample_and_role_order_carrier_contract_gate_v1
    )
    assert tuple(signature.parameters) == ("repo_root", "state_root")
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    assert signature.return_annotation == "dict[str, bytes]"


def test_exact_builtin_dict_and_exact6_order(artifacts: dict[str, bytes]) -> None:
    assert type(artifacts) is dict
    assert tuple(artifacts) == gate._ARTIFACT_NAMES
    assert len(artifacts) == 6
    assert all(type(value) is bytes for value in artifacts.values())


def test_import_is_silent_and_does_not_import_heavy_libraries() -> None:
    command = (
        "import sys; "
        "import covalent_ext.covapie_current11_runtime_sample_and_role_order_carrier_contract_gate_v1; "
        "print(','.join(x for x in ('torch','numpy','rdkit','openbabel') if x in sys.modules))"
    )
    result = subprocess.run(
        (sys.executable, "-c", command),
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": "src", "PYTHONDONTWRITEBYTECODE": "1"},
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert result.stdout == "\n"
    assert result.stderr == ""


def test_module_imports_only_stdlib_and_local_covalent_ext() -> None:
    tree = ast.parse(MODULE.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    allowed = {
        "__future__",
        "ast",
        "copy",
        "csv",
        "hashlib",
        "io",
        "json",
        "os",
        "re",
        "stat",
        "contextlib",
        "pathlib",
        "typing",
    }
    assert all(name.split(".")[0] in allowed | {"covalent_ext"} for name in imports)
    source = MODULE.read_text(encoding="utf-8")
    assert "import subprocess" not in source
    assert "checkpoint" not in " ".join(imports).lower()


def test_double_build_is_byte_identical(build_evidence: dict[str, object]) -> None:
    assert build_evidence["first"] == build_evidence["second"]
    assert len(build_evidence["adapter_calls"]) == 2


def test_build_changes_neither_git_nor_formal_state(build_evidence: dict[str, object]) -> None:
    assert build_evidence["status_before"] == build_evidence["status_after"]
    assert build_evidence["formal_before"] == build_evidence["formal_after"]


def test_design_markdown_is_not_runtime_read_and_did_not_drift(
    build_evidence: dict[str, object],
) -> None:
    assert gate._DESIGN_RELATIVE not in build_evidence["reads"]
    assert build_evidence["design_before"] == build_evidence["design_after"]
    mode, size, _mtime, digest = build_evidence["design_after"]
    assert stat.S_IMODE(mode) == 0o644
    assert size == gate._DESIGN_BYTES
    assert digest == gate._DESIGN_SHA256


def test_all_artifacts_have_canonical_transport(artifacts: dict[str, bytes]) -> None:
    for name, payload in artifacts.items():
        assert 0 < len(payload) < 1024 * 1024
        assert not payload.startswith(b"\xef\xbb\xbf")
        assert b"\0" not in payload
        assert b"\r" not in payload
        assert payload.endswith(b"\n")
        assert not payload.endswith(b"\n\n")
        if name.endswith(".json"):
            assert gate._json(gate._strict_json(payload)) == payload


def test_stable_artifacts_exclude_machine_and_lifecycle_state(
    artifacts: dict[str, bytes],
) -> None:
    joined = b"\n".join(artifacts[name] for name in gate._STABLE_NAMES)
    forbidden = (
        str(REPO_ROOT).encode(),
        str(STATE_ROOT).encode(),
        b'"HEAD"',
        b"origin/main",
        b"ahead",
        b"behind",
        b"inode",
        b"mtime",
    )
    assert all(token not in joined for token in forbidden)


def test_precommit_exact4_compatibility_and_finally_restore(monkeypatch: pytest.MonkeyPatch) -> None:
    owner = gate._adapter._projection_contract_gate
    exact4 = "\n".join(f"?? {path}" for path in gate._REPOSITORY_EXACT4)

    def fake(_root: Path, _arguments: object) -> str:
        return exact4

    monkeypatch.setattr(owner, "_run_git", fake)
    with gate._predecessor_status_compatibility():
        wrapped = owner._run_git
        assert wrapped(REPO_ROOT, ("status", "--porcelain=v1", "--untracked-files=all")) == ""
    assert owner._run_git is fake


def test_committed_clean_lifecycle_compatibility(monkeypatch: pytest.MonkeyPatch) -> None:
    owner = gate._adapter._projection_contract_gate

    def fake(_root: Path, _arguments: object) -> str:
        return ""

    monkeypatch.setattr(owner, "_run_git", fake)
    with gate._predecessor_status_compatibility():
        assert owner._run_git(REPO_ROOT, ("status", "--porcelain=v1", "--untracked-files=all")) == ""


def test_fifth_untracked_is_preserved(monkeypatch: pytest.MonkeyPatch) -> None:
    owner = gate._adapter._projection_contract_gate
    fifth = "?? fifth_untracked_must_fail.txt"

    def fake(_root: Path, _arguments: object) -> str:
        return fifth

    monkeypatch.setattr(owner, "_run_git", fake)
    with gate._predecessor_status_compatibility():
        assert owner._run_git(REPO_ROOT, ("status", "--porcelain=v1", "--untracked-files=all")) == fifth


def test_fifth_untracked_causes_published_predecessor_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner = gate._adapter._projection_contract_gate
    original = owner._run_git

    def with_fifth(root: Path, arguments: object) -> str:
        output = original(root, arguments)
        if tuple(arguments) == ("status", "--porcelain=v1", "--untracked-files=all"):
            return output + ("\n" if output else "") + "?? fifth_untracked_must_fail.txt"
        return output

    monkeypatch.setattr(owner, "_run_git", with_fifth)
    with gate._predecessor_status_compatibility():
        with pytest.raises(ValueError, match=f"^{owner.ERROR_TOKEN}$"):
            owner._repository_lifecycle(REPO_ROOT)
    assert owner._run_git is with_fifth


@pytest.mark.parametrize("prefix", [" M ", "M  ", "A  ", "R  ", "D  ", "T  ", "UU "])
def test_non_untracked_exact4_status_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    prefix: str,
) -> None:
    owner = gate._adapter._projection_contract_gate
    line = prefix + gate._REPOSITORY_EXACT4[0]

    def fake(_root: Path, _arguments: object) -> str:
        return line

    monkeypatch.setattr(owner, "_run_git", fake)
    with gate._predecessor_status_compatibility():
        with pytest.raises(ValueError, match=f"^{ERROR}$"):
            owner._run_git(REPO_ROOT, ("status", "--porcelain=v1", "--untracked-files=all"))
    assert owner._run_git is fake


def test_predecessor_identities_and_results(
    manifest: dict[str, object], artifacts: dict[str, bytes]
) -> None:
    lineage = manifest["source_lineage"]
    adapter = lineage["public_task2_remap_adapter_v1"]
    remap = lineage["task2_remap_contract_gate_v1"]
    projection = lineage["projection_lineage"]
    report = _json(gate._REPORT, artifacts)
    assert adapter == {
        "relative_path": gate._ADAPTER_RELATIVE,
        "bytes": gate._ADAPTER_BYTES,
        "LF": gate._ADAPTER_LF,
        "SHA256": gate._ADAPTER_SHA256,
        "Git_blob": gate._ADAPTER_BLOB,
        "commit": gate._ADAPTER_COMMIT,
        "stable_output_digest": gate._ADAPTER_OUTPUT_DIGEST,
        "checker_identity": {
            "relative_path": gate._ADAPTER_CHECKER_RELATIVE,
            "bytes": gate._ADAPTER_CHECKER_BYTES,
            "LF": gate._ADAPTER_CHECKER_LF,
            "SHA256": gate._ADAPTER_CHECKER_SHA256,
            "Git_blob": gate._ADAPTER_CHECKER_BLOB,
        },
        "public_adapter_api_called": True,
        "adapter_exact2_identity_verified": True,
        "canonical_remap_status": "REMAPPED_EXACT",
        "canonical_failure_reason": "NONE",
    }
    assert remap["contract_digest"] == gate._REMAP_DIGEST
    assert remap["commit"] == gate._REMAP_COMMIT
    assert projection == {
        "projection_instance_digest": gate._PROJECTION_DIGEST,
        "payload_bundle_digest": gate._PAYLOAD_DIGEST,
        "projection_contract_digest": gate._PROJECTION_CONTRACT_DIGEST,
    }
    assert report["adapter_predecessor_passed"] is True
    assert report["adapter_stable_output_digest"] == gate._ADAPTER_OUTPUT_DIGEST
    assert report["public_adapter_api_called"] is True
    assert report["adapter_exact2_identity_verified"] is True
    assert report["adapter_canonical_remap_status"] == "REMAPPED_EXACT"
    assert report["adapter_canonical_failure_reason"] == "NONE"
    assert report["remap_contract_predecessor_passed"] is True


def test_public_adapter_exact2_order_identities_status_and_digests(
    public_predecessor_fixture: dict[str, object],
) -> None:
    exact2 = public_predecessor_fixture["exact2"]
    assert type(exact2) is dict
    assert tuple(exact2) == gate._ADAPTER_ARTIFACT_NAMES
    output_payload = exact2[gate._ADAPTER_OUTPUT_NAME]
    report_payload = exact2[gate._ADAPTER_REPORT_NAME]
    assert (
        len(output_payload),
        output_payload.count(b"\n"),
        hashlib.sha256(output_payload).hexdigest(),
    ) == (
        gate._ADAPTER_OUTPUT_BYTES,
        gate._ADAPTER_OUTPUT_LF,
        gate._ADAPTER_OUTPUT_SHA256,
    )
    assert (
        len(report_payload),
        report_payload.count(b"\n"),
        hashlib.sha256(report_payload).hexdigest(),
    ) == (
        gate._ADAPTER_REPORT_BYTES,
        gate._ADAPTER_REPORT_LF,
        gate._ADAPTER_REPORT_SHA256,
    )
    output, report = gate._validate_adapter_exact2(exact2)
    assert output["remap_status"] == "REMAPPED_EXACT"
    assert output["failure_reason"] == "NONE"
    assert report["adapter_status"] == "PASS_IN_MEMORY_TASK2_BATCH_INDEX_REMAP_ONLY"
    assert report["remap_output_digest"] == gate._ADAPTER_OUTPUT_DIGEST
    assert report["remap_contract_digest"] == gate._REMAP_DIGEST
    assert gate._adapter_output_digest(output_payload) == gate._ADAPTER_OUTPUT_DIGEST


def test_public_adapter_api_called_once_with_exact_canonical_copy_inside_wrapper(
    monkeypatch: pytest.MonkeyPatch,
    public_predecessor_fixture: dict[str, object],
) -> None:
    owner = gate._adapter._projection_contract_gate
    exact6 = public_predecessor_fixture["exact6"]
    exact2 = public_predecessor_fixture["exact2"]
    expected_input = public_predecessor_fixture["adapter_input"]
    calls: list[dict[str, object]] = []

    def fake_git(_root: Path, _arguments: object) -> str:
        return ""

    def fake_remap(**_kwargs: object) -> dict[str, bytes]:
        return copy.deepcopy(exact6)

    def fake_adapter(**kwargs: object) -> dict[str, bytes]:
        assert owner._run_git is not fake_git
        calls.append(copy.deepcopy(kwargs))
        return copy.deepcopy(exact2)

    monkeypatch.setattr(owner, "_run_git", fake_git)
    monkeypatch.setattr(
        gate._remap_gate,
        "build_covapie_current11_task2_batch_index_remap_contract_gate_v1",
        fake_remap,
    )
    monkeypatch.setattr(
        gate._adapter,
        "build_covapie_current11_task2_batch_index_remap_adapter_v1",
        fake_adapter,
    )
    _vectors, output, report = gate._predecessors(REPO_ROOT, STATE_ROOT)
    assert owner._run_git is fake_git
    assert len(calls) == 1
    assert calls[0] == {
        "repo_root": REPO_ROOT,
        "state_root": STATE_ROOT,
        "adapter_input": expected_input,
    }
    assert output["remap_status"] == "REMAPPED_EXACT"
    assert report == {
        "adapter_status": "PASS_IN_MEMORY_TASK2_BATCH_INDEX_REMAP_ONLY",
        "remap_output_digest": gate._ADAPTER_OUTPUT_DIGEST,
        "remap_contract_digest": gate._REMAP_DIGEST,
        "public_adapter_api_called": True,
        "adapter_exact2_identity_verified": True,
        "adapter_canonical_remap_status": "REMAPPED_EXACT",
        "adapter_canonical_failure_reason": "NONE",
    }


def _mutated_public_exact2(kind: str, source: dict[str, bytes]) -> dict[str, bytes]:
    exact2 = copy.deepcopy(source)
    if kind == "wrong_order":
        return {
            gate._ADAPTER_REPORT_NAME: exact2[gate._ADAPTER_REPORT_NAME],
            gate._ADAPTER_OUTPUT_NAME: exact2[gate._ADAPTER_OUTPUT_NAME],
        }
    if kind == "wrong_output_bytes":
        exact2[gate._ADAPTER_OUTPUT_NAME] += b"x"
    elif kind == "wrong_report_bytes":
        exact2[gate._ADAPTER_REPORT_NAME] += b"x"
    elif kind == "wrong_status":
        output = gate._strict_json(exact2[gate._ADAPTER_OUTPUT_NAME])
        output["remap_status"] = "SCHEMA_VERSION_MISMATCH"
        exact2[gate._ADAPTER_OUTPUT_NAME] = gate._json(output)
    elif kind == "wrong_digest":
        report = gate._strict_json(exact2[gate._ADAPTER_REPORT_NAME])
        report["remap_output_digest"] = "0" * 64
        exact2[gate._ADAPTER_REPORT_NAME] = gate._json(report)
    else:
        raise AssertionError(kind)
    return exact2


@pytest.mark.parametrize(
    "kind",
    ("wrong_order", "wrong_output_bytes", "wrong_report_bytes", "wrong_status", "wrong_digest"),
)
def test_public_adapter_malformed_exact2_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    public_predecessor_fixture: dict[str, object],
    kind: str,
) -> None:
    exact6 = public_predecessor_fixture["exact6"]
    exact2 = _mutated_public_exact2(kind, public_predecessor_fixture["exact2"])
    monkeypatch.setattr(
        gate._remap_gate,
        "build_covapie_current11_task2_batch_index_remap_contract_gate_v1",
        lambda **_kwargs: copy.deepcopy(exact6),
    )
    monkeypatch.setattr(
        gate._adapter,
        "build_covapie_current11_task2_batch_index_remap_adapter_v1",
        lambda **_kwargs: copy.deepcopy(exact2),
    )
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        gate._predecessors(REPO_ROOT, STATE_ROOT)


def test_public_adapter_exception_is_unified_and_wrapper_restores(
    monkeypatch: pytest.MonkeyPatch,
    public_predecessor_fixture: dict[str, object],
) -> None:
    owner = gate._adapter._projection_contract_gate
    original = owner._run_git
    exact6 = public_predecessor_fixture["exact6"]
    monkeypatch.setattr(
        gate._remap_gate,
        "build_covapie_current11_task2_batch_index_remap_contract_gate_v1",
        lambda **_kwargs: copy.deepcopy(exact6),
    )

    def raises(**_kwargs: object) -> dict[str, bytes]:
        raise RuntimeError("public adapter failure")

    monkeypatch.setattr(
        gate._adapter,
        "build_covapie_current11_task2_batch_index_remap_adapter_v1",
        raises,
    )
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        gate._predecessors(REPO_ROOT, STATE_ROOT)
    assert owner._run_git is original


def test_gate_does_not_call_adapter_private_execution_or_serialization_helpers() -> None:
    source = MODULE.read_text(encoding="utf-8")
    for forbidden in (
        "_adapter._remap_engine(",
        "_adapter._validate_output(",
        "_adapter._json(",
        "_adapter._stable_output_digest(",
    ):
        assert forbidden not in source


def test_runtime_source_inventory_and_semantic_anchors(manifest: dict[str, object]) -> None:
    sources = manifest["source_lineage"]["runtime_sources"]
    assert len(sources) == 7
    assert [row["relative_path"] for row in sources] == list(gate._RUNTIME_SOURCES)
    for row in sources:
        expected = gate._RUNTIME_SOURCES[row["relative_path"]]
        assert (row["bytes"], row["LF"], row["SHA256"], row["Git_blob"]) == expected
        assert row["validated_symbols"] == list(gate._RUNTIME_SYMBOLS[row["relative_path"]])
        assert row["semantic_anchors"] == list(gate._RUNTIME_ANCHORS[row["relative_path"]])


def test_dataset_names_collate_size_mask_and_centering_semantics(
    manifest: dict[str, object],
) -> None:
    semantics = manifest["runtime_source_semantics"]["dataset_transport"]
    assert all(semantics.values())
    lightning = manifest["runtime_source_semantics"]["lightning_transport"]
    assert lightning == {
        "train_shuffle": True,
        "validation_shuffle": False,
        "test_shuffle": False,
        "transform_boundary_optional": True,
        "checked_default_virtual_nodes": False,
        "model_boundary_uses_role_sizes_and_masks": True,
    }


def test_append_virtual_nodes_is_detected_and_forbidden(manifest: dict[str, object]) -> None:
    virtual = manifest["runtime_source_semantics"]["append_virtual_nodes"]
    assert virtual["appends_to_ligand_tail"] is True
    assert virtual["changes_num_lig_atoms"] is True
    assert virtual["extends_lig_mask"] is True
    assert virtual["adds_num_virtual_atoms"] is True
    assert virtual["allowed_by_v1"] is False
    assert manifest["virtual_node_policy"] == "no_virtual_nodes_v1"


def test_v1_v2_materializers_have_no_runtime_consumer_or_tensor(
    manifest: dict[str, object],
) -> None:
    readiness = manifest["runtime_source_semantics"]["materializer_readiness"]
    assert readiness["v1_formal_sidecar_materialized"] is True
    assert readiness["v2_formal_sidecar_materialized"] is True
    assert readiness["runtime_consumer_available"] is False
    assert readiness["tensor_materialized"] is False
    assert readiness["ready_for_tensor_materialization"] is False
    assert readiness["ready_for_dataloader_integration"] is False


def test_temporary_probe_is_feasibility_evidence_only(manifest: dict[str, object]) -> None:
    evidence = manifest["temporary_reference_evidence"]
    assert evidence["temporary_reference_feasibility_passed"] is True
    assert evidence["unicode_names_shape_11_transport_observed"] is True
    assert evidence["collate_sample_order_preserved"] is True
    assert evidence["names_equal_exact11_row_ids_observed"] is True
    assert evidence["pocket_role_order_and_indicator_preserved"] is True
    assert evidence["temporary_artifact_cleaned"] is True
    assert evidence["formal_runtime_authority"] is False
    assert evidence["persistent_runtime_artifact"] is False
    boundary = manifest["formal_authority_boundary"]
    assert not any(boundary.values())


def test_sample_registry_exact11_and_typed_indices(artifacts: dict[str, bytes]) -> None:
    rows = _csv(gate._SAMPLE_REGISTRY, artifacts)
    assert len(rows) == 11
    assert [int(row["sample_index_0based"]) for row in rows] == list(range(11))
    assert [row["sample_index_row_id"] for row in rows] == list(gate._EXPECTED_SAMPLE_IDS)
    assert all(row["expected_name"] == row["sample_index_row_id"] for row in rows)
    assert all(row["expected_receptor"] == row["pdb_id"] for row in rows)
    assert all(row["sample_key_schema_version"] == gate._SAMPLE_KEY_SCHEMA for row in rows)
    assert all(row["sample_key_exact_one"] == "true" for row in rows)
    assert all(row["runtime_carrier_materialized"] == "false" for row in rows)


def test_sample_keys_are_unique_despite_repeated_jug(artifacts: dict[str, bytes]) -> None:
    rows = _csv(gate._SAMPLE_REGISTRY, artifacts)
    keys = [row["sample_index_row_id"] for row in rows]
    assert len(keys) == len(set(keys)) == 11
    jug = [row for row in rows if row["ligand_comp_id"] == "JUG"]
    assert len(jug) == 3
    assert len({row["sample_index_row_id"] for row in jug}) == 3


def test_sample_key_contract_does_not_claim_formal_runtime_key(
    manifest: dict[str, object],
) -> None:
    contract = manifest["sample_key_contract"]
    assert contract["schema_version"] == gate._SAMPLE_KEY_SCHEMA
    assert contract["field_name"] == "names"
    assert contract["logical_shape"] == "[S]"
    assert contract["runtime_batch_sample_key_available"] is False
    assert contract["runtime_batch_sample_key_exact_one_for_current11"] is False
    assert contract["receptors"]["sample_identity_authority"] is False


def test_role_registry_exact22_role_major_order(role_registry: dict[str, object]) -> None:
    records = role_registry["role_order_records"]
    assert role_registry["schema_version"] == gate._ROLE_REGISTRY_SCHEMA
    assert role_registry["role_order"] == ["pocket", "ligand"]
    assert len(records) == 22
    assert [row["role"] for row in records] == ["pocket"] * 11 + ["ligand"] * 11
    assert [row["sample_index_0based"] for row in records[:11]] == list(range(11))
    assert [row["sample_index_0based"] for row in records[11:]] == list(range(11))


def test_role_table_authority_and_counts(role_registry: dict[str, object]) -> None:
    records = role_registry["role_order_records"]
    for row in records:
        path = REPO_ROOT / row["source_table_relative_path"]
        payload = path.read_bytes()
        assert row["source_table_root_kind"] == "repo_root"
        assert hashlib.sha256(payload).hexdigest() == row["source_table_sha256"]
        assert len(list(csv.DictReader(io.StringIO(payload.decode())))) == row["source_row_count"]
        assert row["unsupported_nonhydrogen_count"] == 0
        assert row["runtime_role_order_materialized"] is False


def test_h_drop_and_retained_vectors(role_registry: dict[str, object]) -> None:
    pocket = role_registry["role_order_records"][:11]
    ligand = role_registry["role_order_records"][11:]
    assert tuple(row["retained_heavy_count"] for row in pocket) == gate._EXPECTED_POCKET_RETAINED
    assert tuple(row["retained_heavy_count"] for row in ligand) == gate._EXPECTED_LIGAND_RETAINED
    assert tuple(row["explicit_hydrogen_count"] for row in pocket) == gate._EXPECTED_POCKET_H
    assert tuple(row["explicit_hydrogen_count"] for row in ligand) == gate._EXPECTED_LIGAND_H


def test_full_projected_source_row_vectors(role_registry: dict[str, object]) -> None:
    for row in role_registry["role_order_records"]:
        projected = row["projected_source_row_indices_int64"]
        assert len(projected) == row["retained_heavy_count"]
        assert all(type(value) is int and 0 <= value < row["source_row_count"] for value in projected)
        assert all(left < right for left, right in zip(projected, projected[1:]))
        assert row["selected_task2_source_row_index_0based"] in projected


def test_full_source_to_projected_vectors_use_null_not_minus_one(
    role_registry: dict[str, object],
) -> None:
    for row in role_registry["role_order_records"]:
        mapping = row["source_to_projected_index_nullable_int64"]
        projected = row["projected_source_row_indices_int64"]
        assert len(mapping) == row["source_row_count"]
        assert -1 not in mapping
        assert [value for value in mapping if value is not None] == list(range(len(projected)))
        assert sum(value is None for value in mapping) == row["explicit_hydrogen_count"]
        for local, source_index in enumerate(projected):
            assert mapping[source_index] == local


def test_selected_task2_endpoint_is_only_a_full_order_cross_check(
    role_registry: dict[str, object],
) -> None:
    for row in role_registry["role_order_records"]:
        source_index = row["selected_task2_source_row_index_0based"]
        local_index = row["selected_task2_parser_local_index_0based"]
        assert row["source_to_projected_index_nullable_int64"][source_index] == local_index
        assert len(row["projected_source_row_indices_int64"]) > 1


def test_full_exact8_identity_sequence_digests(role_registry: dict[str, object]) -> None:
    digests = []
    for row in role_registry["role_order_records"]:
        value = row["projected_atom_identity_sequence_sha256"]
        assert type(value) is str and len(value) == 64
        int(value, 16)
        digest_copy = dict(row)
        recorded = digest_copy.pop("role_order_record_sha256")
        assert recorded == hashlib.sha256(gate._compact_json(digest_copy)).hexdigest()
        digests.append(value)
    assert len(set(digests)) == 22
    framing = role_registry["identity_sequence_framing"]
    assert framing["fields_in_semantic_order"] == list(gate._ATOM_IDENTITY_FIELDS)
    assert framing["terminal_lf"] is False


def test_role_aggregate_totals(role_registry: dict[str, object]) -> None:
    assert role_registry["aggregate_counts"] == {
        "sample_count": 11,
        "role_record_count": 22,
        "total_source_rows_pocket": 2531,
        "total_source_rows_ligand": 339,
        "total_retained_pocket": 2202,
        "total_retained_ligand": 323,
        "total_explicit_h_pocket": 329,
        "total_explicit_h_ligand": 16,
        "unsupported_nonhydrogen_count": 0,
    }


def test_carrier_manifest_schema_exact_field_order_and_kind(
    artifacts: dict[str, bytes],
) -> None:
    schema = _json(gate._CARRIER_MANIFEST_SCHEMA, artifacts)
    assert schema["schema_version"] == gate._CARRIER_SCHEMA
    assert schema["artifact_kind"] == "manifest_schema_not_manifest_instance"
    assert schema["schema_is_instance"] is False
    assert schema["top_level_field_order"] == [
        "schema_version",
        "source_contract_digest",
        "sample_key_registry_digest",
        "role_order_registry_digest",
        "runtime_artifact_kind",
        "runtime_artifact_relative_path",
        "runtime_artifact_sha256",
        "runtime_batch_schema_version",
        "sample_key_schema_version",
        "role_order_schema_version",
        "virtual_node_policy",
        "sample_order",
        "names_binding",
        "receptors_binding",
        "ligand_buffer_binding",
        "pocket_buffer_binding",
        "materialization_provenance",
        "readiness",
    ]
    fields = schema["top_level_fields"]
    assert fields["runtime_artifact_kind"]["exact_value"] == gate._RUNTIME_KIND
    assert fields["runtime_artifact_relative_path"]["actual_value_in_schema"] is None
    assert fields["runtime_artifact_sha256"]["actual_value_in_schema"] is None


def test_carrier_schema_names_receptors_and_role_buffers(artifacts: dict[str, bytes]) -> None:
    fields = _json(gate._CARRIER_MANIFEST_SCHEMA, artifacts)["top_level_fields"]
    names = fields["names_binding"]
    assert names["field_name"] == "names"
    assert names["array_dtype_family"] == "unicode_string"
    assert names["array_rank"] == 1 and names["array_length"] == 11
    assert names["exact_values_required"] is True
    receptors = fields["receptors_binding"]
    assert receptors["identity_authority"] is False
    assert receptors["consistency_only"] is True
    for role in ("ligand", "pocket"):
        binding = fields[f"{role}_buffer_binding"]
        assert binding["role"] == role
        assert binding["padding_present_required_value"] is False
        assert binding["virtual_nodes_present_required_value"] is False
        assert binding["atom_reorder_present_required_value"] is False


def test_runtime_schema_forbids_padding_crop_reorder_and_virtual(
    artifacts: dict[str, bytes], manifest: dict[str, object]
) -> None:
    schema = _json(gate._CARRIER_MANIFEST_SCHEMA, artifacts)
    assert schema["runtime_schema_contract"] == {
        "padding_present": False,
        "crop_present": False,
        "atom_reorder_present": False,
        "virtual_nodes_present": False,
        "ligand_and_pocket_role_spaces_independent": True,
    }
    contract = manifest["runtime_schema_contract"]
    assert contract["no_padding"] is True
    assert contract["no_crop"] is True
    assert contract["no_atom_reorder"] is True
    assert contract["no_virtual_nodes"] is True


def test_status_vocabulary_exact13_and_sole_success(artifacts: dict[str, bytes]) -> None:
    rows = _csv(gate._VOCABULARY, artifacts)
    assert len(rows) == 13
    assert [int(row["status_code"]) for row in rows] == list(range(13))
    assert [row["status"] for row in rows] == [row[0] for row in gate._STATUS_ROWS]
    successes = [row for row in rows if row["is_success"] == "true"]
    assert [row["status"] for row in successes] == ["CARRIER_BOUND_EXACT"]
    missing = rows[1]
    assert missing["status"] == "MATERIALIZED_CARRIER_MISSING"
    assert "not materialized" in missing["description"]
    joined = " ".join(row["description"] for row in rows).lower()
    assert all(word not in joined for word in ("maybe", "probably", "best_match", "nearest"))


def test_fail_closed_invariant_count_and_required_semantics(manifest: dict[str, object]) -> None:
    invariants = manifest["fail_closed_invariants"]
    assert len(invariants) == 30
    joined = "\n".join(invariants)
    for required in (
        "names is the sole sample identity carrier",
        "ligand and pocket are independent role spaces",
        "minus-one sentinel",
        "unsupported nonhydrogen",
        "runtime padding is forbidden",
        "runtime crop is forbidden",
        "runtime atom reorder is forbidden",
        "runtime virtual nodes are forbidden",
        "temporary NPZ probe",
        "shuffle changes only batch order",
    ):
        assert required in joined


def test_stable_digest_manual_framing_and_report_exclusion(artifacts: dict[str, bytes]) -> None:
    assert gate._DOMAIN_TAG == (
        b"COVAPIE_CURRENT11_RUNTIME_SAMPLE_AND_ROLE_ORDER_CARRIER_CONTRACT_GATE_V1\0"
    )
    assert not gate._DOMAIN_TAG.endswith(b" ")
    assert gate._DOMAIN_TAG.count(b"\0") == 1
    assert gate._DOMAIN_TAG.endswith(b"\0")
    digest = hashlib.sha256()
    digest.update(gate._DOMAIN_TAG)
    for name in gate._STABLE_NAMES:
        encoded = name.encode("utf-8")
        payload = artifacts[name]
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    report = _json(gate._REPORT, artifacts)
    assert digest.hexdigest() == gate._stable_digest(artifacts)
    assert report["contract_digest"] == digest.hexdigest()
    changed = dict(artifacts)
    changed[gate._REPORT] += b"ignored"
    assert gate._stable_digest(changed) == digest.hexdigest()


def test_stable_digest_known_vector() -> None:
    fixture = {name: f"payload-{index}\n".encode() for index, name in enumerate(gate._STABLE_NAMES)}
    assert gate._stable_digest(fixture) == "2d5f7671ff8733e9dd84a3ed38da1678ec93a395dfd01be89148a649abdc7d86"


def test_four_frozen_stable_artifact_identities_are_unchanged(
    artifacts: dict[str, bytes],
) -> None:
    expected = {
        gate._SAMPLE_REGISTRY: (
            1858,
            12,
            "a119522026ffce887049b2d2475e2763df4ed0035e730f7b4a58b2d0c14e7671",
        ),
        gate._ROLE_REGISTRY: (
            98412,
            6043,
            "b1092570d94edde242dc8d5f01a5af75cba539e4c8ce4ae6c901809649478053",
        ),
        gate._CARRIER_MANIFEST_SCHEMA: (
            6007,
            185,
            "5a543a638b400c920ffe0fdc4acd16615534ab10b50258ea58899231b5e87cba",
        ),
        gate._VOCABULARY: (
            1436,
            14,
            "d54c2452f70445c127704c2410a296fd7059e8621c59839ff3bf00d3a0dc57a8",
        ),
    }
    assert {
        name: (len(artifacts[name]), artifacts[name].count(b"\n"), hashlib.sha256(artifacts[name]).hexdigest())
        for name in expected
    } == expected


def test_revised_manifest_report_and_stable_contract_identities(
    artifacts: dict[str, bytes],
) -> None:
    expected = {
        gate._MANIFEST: (
            27982,
            610,
            "b5a9110277d66023623e2aa92d3d4ef664c6755ccff7a6ec41467981e58276a2",
        ),
        gate._REPORT: (
            4991,
            116,
            "be40fc6d9b1b0bae4e245482c6fe509ff4bc8d3f16d8513477c2baeb1ccc357a",
        ),
    }
    assert {
        name: (len(artifacts[name]), artifacts[name].count(b"\n"), hashlib.sha256(artifacts[name]).hexdigest())
        for name in expected
    } == expected
    digest = "360ee9a2a75efae3189922426a53ebccf3f2e0fbc9c2fb33980112a6c5438b14"
    assert gate._stable_digest(artifacts) == digest
    assert _json(gate._REPORT, artifacts)["contract_digest"] == digest
    assert all(digest.encode() not in artifacts[name] for name in gate._STABLE_NAMES)


def test_checkpoint_compatibility_uses_canonical_exact_dict(
    manifest: dict[str, object],
) -> None:
    assert manifest["checkpoint_compatibility"] == {
        "checkpoint_state_dict_change_required": False,
        "base_model_parameter_shape_change_required": False,
        "base_atom_feature_width_change_required": False,
        "egnn_or_se3_backbone_change_required": False,
        "checkpoint_bytes_read": False,
    }


def test_stable_artifacts_do_not_contain_self_digest(artifacts: dict[str, bytes]) -> None:
    digest = _json(gate._REPORT, artifacts)["contract_digest"].encode()
    assert all(digest not in artifacts[name] for name in gate._STABLE_NAMES)


def test_gate_report_status_counts_and_readiness(artifacts: dict[str, bytes]) -> None:
    report = _json(gate._REPORT, artifacts)
    assert report["gate_status"] == "PASS_CONTRACT_ONLY"
    assert report["artifact_file_count"] == 6
    assert report["runtime_source_identity_count"] == 7
    assert report["sample_key_registry_count"] == 11
    assert report["role_order_record_count"] == 22
    assert report["source_atom_table_count"] == 22
    assert report["full_projected_order_recomputed"] is True
    assert report["full_atom_identity_sequence_digests_built"] is True
    assert report["temporary_reference_feasibility_passed"] is True
    assert report["temporary_reference_is_formal_authority"] is False
    assert report["status_vocabulary_count"] == 13
    assert report["fail_closed_invariant_count"] == 30


def test_readiness_exact_truthful_boundary(manifest: dict[str, object]) -> None:
    readiness = manifest["readiness"]
    true_fields = {
        "runtime_sample_and_role_order_carrier_contract_gate_implemented",
        "runtime_sample_and_role_order_carrier_contract_gate_passed",
        "runtime_sample_and_role_order_carrier_contract_designed",
        "sample_key_registry_built_in_memory",
        "role_order_registry_built_in_memory",
        "full_role_order_bound_to_source_tables",
        "temporary_reference_feasibility_passed",
        "current11_atom_identity_provider_available",
        "ready_for_runtime_sample_and_role_order_carrier_materializer_implementation",
        "ready_for_runtime_batch_observation_extractor_design",
        "feature_semantics_reaudit_required_before_training",
    }
    false_fields = set(readiness) - true_fields
    assert all(readiness[field] is True for field in true_fields)
    assert all(readiness[field] is False for field in false_fields)
    assert readiness["general_non_source_identity_provider_available"] is False
    assert readiness["formal_runtime_carrier_materialized"] is False
    assert readiness["runtime_batch_sample_key_available"] is False
    assert readiness["runtime_batch_sample_key_exact_one_for_current11"] is False
    assert readiness["runtime_batch_role_order_binding_available"] is False
    assert readiness["ready_for_batch_descriptor_compiler_contract_gate_implementation"] is False
    assert readiness["ready_for_task2_batch_descriptor_compiler_implementation"] is False
    assert readiness["ready_for_dataloader_integration"] is False
    assert readiness["ready_for_model_integration"] is False
    assert readiness["ready_for_loss_integration"] is False
    assert readiness["ready_for_training"] is False


def test_source_identity_drift_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    original = gate._RUNTIME_SOURCES["dataset.py"]
    monkeypatch.setitem(
        gate._RUNTIME_SOURCES,
        "dataset.py",
        (original[0], original[1], "0" * 64, original[3]),
    )
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        gate._runtime_inventory(REPO_ROOT)


def test_projection_rejects_invalid_and_unsupported_symbols() -> None:
    supported = frozenset(("C", "N", "O", "S", "B", "Br", "Cl", "P", "I", "F"))
    assert gate._classify("H", supported) == "explicit_hydrogen"
    assert gate._classify("C", supported) == "supported_checkpoint_heavy_atom"
    assert gate._classify("Xe", supported) == "unsupported_nonhydrogen"
    assert gate._classify(" c ", supported) == "missing_or_invalid"
    assert gate._classify(None, supported) == "missing_or_invalid"


def test_valid_checker_cli_is_canonical_one_line_and_read_only(
    artifacts: dict[str, bytes],
) -> None:
    status_before = _git_status()
    formal_before = gate._formal_snapshot(STATE_ROOT / gate._FORMAL_RELATIVE)
    result = subprocess.run(
        (
            sys.executable,
            str(CHECKER),
            "--repo-root",
            str(REPO_ROOT),
            "--state-root",
            str(STATE_ROOT),
        ),
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": "src", "PYTHONDONTWRITEBYTECODE": "1"},
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.count("\n") == 1
    parsed = json.loads(result.stdout)
    assert parsed == _json(gate._REPORT, artifacts)
    assert result.stdout == json.dumps(parsed, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    assert _git_status() == status_before
    assert gate._formal_snapshot(STATE_ROOT / gate._FORMAL_RELATIVE) == formal_before


@pytest.mark.parametrize(
    "arguments",
    [
        (),
        ("-h",),
        ("--help",),
        ("--repo-root", str(REPO_ROOT)),
        ("--state-root", str(STATE_ROOT)),
        ("--repo-root", str(REPO_ROOT), "--state-root", str(STATE_ROOT), "extra"),
        ("--repo-root", str(REPO_ROOT), "--state-root", str(STATE_ROOT), "--output", "x"),
        ("--repo-root", str(REPO_ROOT), "--state-root", str(STATE_ROOT), "--write"),
        ("--repo-root", str(REPO_ROOT), "--state-root", str(STATE_ROOT), "--npz", "x"),
        ("--repo-root", str(REPO_ROOT), "--state-root", str(STATE_ROOT), "--carrier", "x"),
        ("--repo-root", str(REPO_ROOT), "--state-root", str(STATE_ROOT), "--tensor"),
        ("--repo-root", str(REPO_ROOT), "--state-root", str(STATE_ROOT), "--train"),
    ],
)
def test_invalid_checker_cli_fails_with_exact_token(arguments: tuple[str, ...]) -> None:
    result = subprocess.run(
        (sys.executable, str(CHECKER), *arguments),
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": "src", "PYTHONDONTWRITEBYTECODE": "1"},
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == ERROR + "\n"
