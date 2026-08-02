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
from copy import deepcopy
from pathlib import Path

import pytest
import torch

from covalent_ext import covapie_target_residue_atom_condition_runtime_bridge_gate_v1 as gate


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT.parent / "covapie-state/manual-review"
ERROR = "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_RUNTIME_BRIDGE_GATE_INVALID"
RUNTIME_ERROR = "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_RUNTIME_BRIDGE_INVALID"
FORMAL_INPUTS = {
    "source_authority_bundle": STATE / "covapie_current11_target_residue_atom_condition_authority_bundle_v1.json",
    "source_alignment_bundle": STATE / "covapie_current11_pocket_atom_identity_alignment_bundle_v1.json",
    "source_adapter_bundle": STATE / "covapie_current11_target_residue_atom_condition_adapter_bundle_v1.json",
    "source_adapter_gate_bundle": STATE / "covapie_current11_target_residue_atom_condition_adapter_gate_bundle_v1.json",
}
EXPECTED_TRANSPORTS = {
    "source_authority_bundle": "a95ae52e091a7117b241269eebd891f3ee97e3ae4a6b4e14fa441ab6a1ed2096",
    "source_alignment_bundle": "7f80a810ff35c4ea5d61262021379767a4d15202badd8ec6a6b846405147d842",
    "source_adapter_bundle": "983c25ea8c52ca54f0c0292990a625e9a9cf0d2370cb517d66a84801d957b65a",
    "source_adapter_gate_bundle": "c7e2c9eec92d560fc55206399d9b27df511733821ce3233c3546da38d9992a9d",
}
EXPECTED_LOCAL = (49, 15, 12, 33, 31, 50, 48, 53, 52, 53, 84)
EXPECTED_FLAT = (49, 81, 182, 299, 505, 712, 988, 1260, 1516, 1766, 2058)


def _inputs():
    return {name: path.read_bytes() for name, path in FORMAL_INPUTS.items()}


def _error(action):
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        action()


@pytest.fixture(scope="session")
def formal_inputs():
    return _inputs()


@pytest.fixture(scope="session")
def bundle(formal_inputs):
    before = subprocess.run(
        ["git", "status", "--porcelain=v1", "-uall"], cwd=ROOT,
        check=True, capture_output=True,
    ).stdout
    result = gate.evaluate_covapie_target_residue_atom_condition_runtime_bridge_gate_v1(
        **formal_inputs, repo_root=ROOT
    )
    after = subprocess.run(
        ["git", "status", "--porcelain=v1", "-uall"], cwd=ROOT,
        check=True, capture_output=True,
    ).stdout
    assert before == after
    return result


def test_public_signature_all_and_silent_import():
    function = gate.evaluate_covapie_target_residue_atom_condition_runtime_bridge_gate_v1
    assert gate.__all__ == (
        "evaluate_covapie_target_residue_atom_condition_runtime_bridge_gate_v1",
    )
    signature = inspect.signature(function)
    assert tuple(signature.parameters) == (
        "source_authority_bundle",
        "source_alignment_bundle",
        "source_adapter_bundle",
        "source_adapter_gate_bundle",
        "repo_root",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            "import covalent_ext.covapie_target_residue_atom_condition_runtime_bridge_gate_v1",
        ],
        cwd=ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": "src"},
        check=False,
        capture_output=True,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == b""


@pytest.mark.parametrize("name", tuple(FORMAL_INPUTS))
def test_formal_bundle_transport_binding(name, formal_inputs):
    assert hashlib.sha256(formal_inputs[name]).hexdigest() == EXPECTED_TRANSPORTS[name]
    decoded = gate._strict_json(formal_inputs[name])
    assert gate._canonical_json_bytes(decoded) == formal_inputs[name]


def test_adapter_gate_schema_digest_and_canonical_bytes(formal_inputs):
    decoded = gate._strict_json(formal_inputs["source_adapter_gate_bundle"])
    assert gate.adapter_gate._validate_gate_bundle(decoded, require_field_order=False)
    assert decoded["target_residue_atom_condition_adapter_gate_bundle_sha256"] == (
        "97821184d8c76618bb549dd708132bd9579687c6f3a0ba8007d0bbc80d7d6602"
    )


def test_external_resolution_production_and_response_binding(bundle):
    path = ROOT / "src/covalent_ext/covapie_external_pocket_runtime_bridge_path_coverage_resolution_v1.py"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == (
        "02bbf44ca3602576b252678f499a1219e4d3ee2db170ed2abd474983cf5a3232"
    )
    assert bundle["source_external_path_resolution_response_sha256"] == (
        "8406e5baef6e67fca331d54963f56e6ac9137c5f1afa3a963e7010c491afa9dc"
    )


def test_runtime_commit_parent_subject_and_ancestry():
    metadata = subprocess.run(
        ["git", "show", "-s", "--format=%H%n%P%n%s", gate._IMPLEMENTATION_COMMIT],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    assert metadata == [gate._IMPLEMENTATION_COMMIT, gate._BASE_COMMIT, gate._IMPLEMENTATION_SUBJECT]
    assert subprocess.run(
        ["git", "merge-base", "--is-ancestor", gate._IMPLEMENTATION_COMMIT, "HEAD"],
        cwd=ROOT, check=False, capture_output=True,
    ).returncode == 0


@pytest.mark.parametrize("relative_path,expected", tuple(gate._RUNTIME_FILES.items()))
def test_commit_and_working_runtime_files_are_exact(relative_path, expected):
    committed = subprocess.run(
        ["git", "show", f"{gate._IMPLEMENTATION_COMMIT}:{relative_path}"],
        cwd=ROOT, check=True, capture_output=True,
    ).stdout
    current = (ROOT / relative_path).read_bytes()
    assert current == committed
    assert hashlib.sha256(current).hexdigest() == expected


def test_runtime_checker_two_runs_and_stdout_sha():
    stdout, facts = gate._run_runtime_checker(ROOT)
    assert hashlib.sha256(stdout).hexdigest() == gate._RUNTIME_CHECKER_STDOUT_SHA256
    assert facts["collated_current11_indicator_length"] == "2202"
    assert facts["collated_current11_indicator_true_count"] == "11"
    assert facts["runtime_bridge_gate_implemented"] == "false"


def test_exact20_record_fields_and_exact39_bundle_fields(bundle):
    assert len(gate.RUNTIME_BRIDGE_GATE_RECORD_FIELDS) == 20
    assert len(gate.RUNTIME_BRIDGE_GATE_BUNDLE_FIELDS) == 39
    assert tuple(bundle) == gate.RUNTIME_BRIDGE_GATE_BUNDLE_FIELDS
    assert tuple(bundle["current11_record_fields"]) == gate.RUNTIME_BRIDGE_GATE_RECORD_FIELDS


def test_current11_order_counts_local_flat_and_mask_records(bundle):
    records = bundle["current11_records"]
    assert len(records) == bundle["current11_record_count"] == 11
    assert tuple(record["sample"] for record in records) == tuple(
        f"CYS_SG_SAMPLE_INDEX_{index:06d}" for index in range(1, 12)
    )
    assert tuple(record["expected_local_true_index"] for record in records) == EXPECTED_LOCAL
    assert tuple(record["runtime_local_true_index"] for record in records) == EXPECTED_LOCAL
    assert tuple(record["expected_flat_true_index"] for record in records) == EXPECTED_FLAT
    assert tuple(record["runtime_flat_true_index"] for record in records) == EXPECTED_FLAT
    assert tuple(record["runtime_mask_sample_id"] for record in records) == tuple(range(11))
    assert bundle["total_runtime_pocket_node_count"] == 2202
    assert bundle["total_runtime_indicator_true_count"] == 11


@pytest.mark.parametrize("index", range(11))
def test_each_current11_record_runtime_evidence_and_digest(bundle, index):
    record = bundle["current11_records"][index]
    assert tuple(record) == gate.RUNTIME_BRIDGE_GATE_RECORD_FIELDS
    assert record["runtime_indicator_dtype"] == "torch.bool"
    assert record["runtime_indicator_length"] == record["retained_pocket_node_count"]
    assert record["runtime_indicator_true_count"] == 1
    assert record["runtime_target_s_feature_index"] == 3
    assert record["runtime_pocket_one_hot_width"] == 10
    assert record["sidecar_field_name"] == gate._FIELD
    assert record["node_order_preserved"] is True
    assert record["status"] == "runtime_bridge_gate_ready_unique"
    assert record["blockers"] == []
    assert gate._validate_record(record, require_field_order=True)


def test_bundle_digest_canonical_and_deterministic(bundle, formal_inputs):
    assert gate._validate_bundle(bundle, require_field_order=True)
    payload = gate._bundle_bytes(bundle)
    assert not payload.endswith(b"\n")
    assert gate._canonical_json_bytes(json.loads(payload)) == payload
    second = gate.evaluate_covapie_target_residue_atom_condition_runtime_bridge_gate_v1(
        **formal_inputs, repo_root=ROOT
    )
    assert second == bundle
    assert gate._bundle_bytes(second) == payload


def test_inputs_unchanged_no_paths_and_readiness_is_evidence_derived(bundle, formal_inputs):
    snapshots = {name: bytes(value) for name, value in formal_inputs.items()}
    assert formal_inputs == snapshots
    assert not any(isinstance(value, Path) for value in gate._walk_values(bundle))
    evidence_fields = (
        "legacy_collated_absent_parity",
        "legacy_prepare_pocket_ca_parity",
        "legacy_prepare_pocket_full_atom_parity",
        "external_selector_exact6_validated",
        "external_prepare_pocket_repeat_validated",
        "conditional_branch_sidecar_carried",
        "inpainting_branch_sidecar_carried",
        "authorized_lightning_ast_boundary_valid",
        "checkpoint_compatibility_preserved",
    )
    assert bundle["ready_for_model_consumption_design"] is all(
        bundle[field] for field in evidence_fields
    )


def test_legacy_external_branch_and_model_boundaries(bundle):
    assert bundle["legacy_collated_absent_parity"] is True
    assert bundle["legacy_prepare_pocket_ca_parity"] is True
    assert bundle["legacy_prepare_pocket_full_atom_parity"] is True
    assert bundle["external_selector_exact6_validated"] is True
    assert bundle["external_prepare_pocket_repeat_validated"] is True
    assert bundle["conditional_branch_sidecar_carried"] is True
    assert bundle["inpainting_branch_sidecar_carried"] is True
    assert bundle["repository_cli_selector_forwarding_implemented"] is False
    assert bundle["indicator_consumed_by_model"] is False
    assert bundle["indicator_passed_into_dynamics"] is False


def test_ast_forward_training_eval_and_checkpoint_boundaries(bundle):
    current = ast.parse((ROOT / "lightning_modules.py").read_text())
    base = ast.parse(subprocess.run(
        ["git", "show", f"{gate._BASE_COMMIT}:lightning_modules.py"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout)
    current_methods = gate._method_map(current)
    base_methods = gate._method_map(base)
    assert {
        name for name in base_methods if current_methods[name] != base_methods[name]
    } == set(gate._METHODS)
    assert all(current_methods[name] == base_methods[name] for name in (
        "forward", "training_step", "_shared_eval", "validation_step", "test_step"
    ))
    assert bundle["authorized_lightning_ast_boundary_valid"] is True
    assert bundle["checkpoint_compatibility_preserved"] is True


@pytest.mark.parametrize("relative_path,expected", tuple(gate._PROTECTED_SOURCES.items()))
def test_model_sources_unchanged(relative_path, expected):
    assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected


def test_checkpoint_size_hash_and_no_state_contract_change():
    checkpoint = ROOT / "checkpoints/crossdocked_fullatom_cond.ckpt"
    assert checkpoint.stat().st_size == 17861341
    assert hashlib.sha256(checkpoint.read_bytes()).hexdigest() == gate._CHECKPOINT_SHA256
    source = (ROOT / "lightning_modules.py").read_text()
    for text in ("register_buffer(", "register_parameter(", "add_module(", "nn.Parameter("):
        assert text not in source


@pytest.mark.parametrize("relative_path,expected", tuple(gate._CALLER_SHA256S.items()))
def test_repository_callers_unchanged(relative_path, expected):
    assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected


def test_canonical_five_masks_include_scaffold_only():
    assert gate.CANONICAL_MASK_SEMANTIC_NAMES == (
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    )


@pytest.mark.parametrize(
    "parameter,bad_value",
    [
        ("source_authority_bundle", bytearray(b"x")),
        ("source_alignment_bundle", "x"),
        ("source_adapter_bundle", memoryview(b"x")),
        ("source_adapter_gate_bundle", None),
        ("repo_root", str(ROOT)),
    ],
)
def test_public_api_rejects_wrong_types_canonically(formal_inputs, parameter, bad_value):
    arguments = {**formal_inputs, "repo_root": ROOT}
    arguments[parameter] = bad_value
    _error(lambda: gate.evaluate_covapie_target_residue_atom_condition_runtime_bridge_gate_v1(**arguments))


@pytest.mark.parametrize("name", tuple(FORMAL_INPUTS))
def test_bundle_byte_drift_fails_closed(formal_inputs, name):
    arguments = dict(formal_inputs)
    arguments[name] = arguments[name][:-1] + bytes([arguments[name][-1] ^ 1])
    _error(lambda: gate.evaluate_covapie_target_residue_atom_condition_runtime_bridge_gate_v1(
        **arguments, repo_root=ROOT
    ))


def test_runtime_source_drift_fails_closed_before_checker(formal_inputs, monkeypatch):
    original = gate._read_regular

    def drift(path, **kwargs):
        payload = original(path, **kwargs)
        if path == ROOT / "lightning_modules.py":
            return payload + b"\n"
        return payload

    monkeypatch.setattr(gate, "_read_regular", drift)
    _error(lambda: gate.evaluate_covapie_target_residue_atom_condition_runtime_bridge_gate_v1(
        **formal_inputs, repo_root=ROOT
    ))


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("runtime_indicator_dtype", "torch.int64"),
        ("runtime_indicator_true_count", 0),
        ("runtime_indicator_true_count", 2),
        ("runtime_indicator_length", 0),
        ("runtime_local_true_index", 0),
        ("runtime_target_s_feature_index", 2),
        ("runtime_pocket_one_hot_width", 9),
        ("runtime_mask_sample_id", True),
        ("node_order_preserved", False),
        ("status", "ready"),
    ],
)
def test_record_tampering_fails_closed(bundle, field, bad_value):
    record = deepcopy(bundle["current11_records"][0])
    record[field] = bad_value
    _error(lambda: gate._validate_record(record, require_field_order=True))


def _resign_records_and_bundle(candidate, record_indices):
    for index in record_indices:
        record = candidate["current11_records"][index]
        record["runtime_bridge_gate_record_sha256"] = gate._digest_record(
            record,
            gate.RUNTIME_BRIDGE_GATE_RECORD_FIELDS,
            "runtime_bridge_gate_record_sha256",
        )
    candidate["runtime_bridge_gate_bundle_sha256"] = gate._digest_record(
        candidate,
        gate.RUNTIME_BRIDGE_GATE_BUNDLE_FIELDS,
        "runtime_bridge_gate_bundle_sha256",
    )


def test_resigned_current11_record_lineage_drift_is_rejected(bundle):
    attacks = (
        {"pdb_id": "WRONG"},
        {"source_adapter_record_sha256": "0" * 64},
        {
            "retained_pocket_node_count": (
                bundle["current11_records"][0]["retained_pocket_node_count"] + 1
            ),
            "runtime_indicator_length": (
                bundle["current11_records"][0]["runtime_indicator_length"] + 1
            ),
        },
    )
    for changes in attacks:
        candidate = deepcopy(bundle)
        candidate["current11_records"][0].update(changes)
        _resign_records_and_bundle(candidate, (0,))
        _error(lambda candidate=candidate: gate._validate_bundle(
            candidate, require_field_order=True
        ))


def test_resigned_current11_cross_record_aggregate_and_offset_drift_is_rejected(bundle):
    compensated_counts = deepcopy(bundle)
    for index, delta in ((0, 1), (1, -1)):
        record = compensated_counts["current11_records"][index]
        record["retained_pocket_node_count"] += delta
        record["runtime_indicator_length"] += delta
    _resign_records_and_bundle(compensated_counts, (0, 1))

    offset = deepcopy(bundle)
    offset_record = offset["current11_records"][1]
    offset_record["expected_flat_true_index"] += 1
    offset_record["runtime_flat_true_index"] += 1
    _resign_records_and_bundle(offset, (1,))

    mask = deepcopy(bundle)
    mask["current11_records"][0]["runtime_mask_sample_id"] = 1
    _resign_records_and_bundle(mask, (0,))

    for candidate in (compensated_counts, offset, mask):
        _error(lambda candidate=candidate: gate._validate_bundle(
            candidate, require_field_order=True
        ))


def test_isolated_runtime_rejects_all_indicator_shapes_and_counts():
    runtime = gate._load_runtime((ROOT / "lightning_modules.py").read_text(), include_bridge=True)
    invalid = (
        torch.tensor([0, 1, 1, 0, 0]),
        torch.tensor([False, False, True, False, False]),
        torch.tensor([True, True, True, False, False]),
        torch.tensor([False, True, True, False]),
        torch.tensor([[False], [True], [True], [False], [False]]),
    )
    for indicator in invalid:
        with pytest.raises(ValueError, match=f"^{RUNTIME_ERROR}$"):
            gate._model(runtime).get_ligand_and_pocket(gate._batch((2, 3), indicator))


def test_selector_negative_matrix_and_repeat_matrix():
    runtime = gate._load_runtime((ROOT / "lightning_modules.py").read_text(), include_bridge=True)
    invalid_selectors = (
        {**gate._spec(), "extra": 1},
        {key: value for key, value in gate._spec().items() if key != "element"},
        gate._spec(chain_id=""), gate._spec(chain_id=1),
        gate._spec(residue_sequence_number=True), gate._spec(residue_sequence_number="145"),
        gate._spec(residue_insertion_code="A"), gate._spec(residue_name="SER"),
        gate._spec(atom_name="CA"), gate._spec(element="C"),
    )
    for selector in invalid_selectors:
        with pytest.raises(ValueError, match=f"^{RUNTIME_ERROR}$"):
            runtime._validate_covapie_target_residue_atom_condition_spec_v1(selector)
    for repeats in (0, -1, True, 1.5):
        with pytest.raises(ValueError, match=f"^{RUNTIME_ERROR}$"):
            gate._model(runtime).prepare_pocket(
                gate._full_atom_residues(), repeats,
                target_residue_atom_condition_spec=gate._spec(),
            )


def test_materializer_published_idempotent_mismatch_and_cleanup(tmp_path, bundle, formal_inputs, monkeypatch):
    monkeypatch.setattr(
        gate,
        "evaluate_covapie_target_residue_atom_condition_runtime_bridge_gate_v1",
        lambda **kwargs: deepcopy(bundle),
    )
    output = tmp_path / "bundle.json"
    first = gate._materialize_covapie_current11_target_residue_atom_condition_runtime_bridge_gate_bundle_v1(
        **formal_inputs, repo_root=ROOT, output_path=output
    )
    before = output.stat()
    payload = output.read_bytes()
    second = gate._materialize_covapie_current11_target_residue_atom_condition_runtime_bridge_gate_bundle_v1(
        **formal_inputs, repo_root=ROOT, output_path=output
    )
    after = output.stat()
    assert first["publication_mode"] == "published_new"
    assert second["publication_mode"] == "idempotent_existing"
    assert before.st_ino == after.st_ino
    assert before.st_mtime_ns == after.st_mtime_ns
    assert output.read_bytes() == payload
    assert stat.S_IMODE(after.st_mode) == 0o644 and after.st_nlink == 1
    assert not list(tmp_path.glob(".*.tmp"))
    mismatch = tmp_path / "mismatch.json"
    mismatch.write_bytes(b"different")
    mismatch.chmod(0o644)
    mismatch_before = mismatch.stat()
    _error(lambda: gate._materialize_covapie_current11_target_residue_atom_condition_runtime_bridge_gate_bundle_v1(
        **formal_inputs, repo_root=ROOT, output_path=mismatch
    ))
    mismatch_after = mismatch.stat()
    assert mismatch.read_bytes() == b"different"
    assert mismatch_before.st_ino == mismatch_after.st_ino
    assert mismatch_before.st_mtime_ns == mismatch_after.st_mtime_ns
    assert not list(tmp_path.glob(".*.tmp"))

    failure = tmp_path / "failure.json"

    def fail_link(*args, **kwargs):
        raise OSError("injected publication failure")

    monkeypatch.setattr(gate.os, "link", fail_link)
    _error(lambda: gate._materialize_covapie_current11_target_residue_atom_condition_runtime_bridge_gate_bundle_v1(
        **formal_inputs, repo_root=ROOT, output_path=failure
    ))
    assert not failure.exists()
    assert not list(tmp_path.glob(".*.tmp"))


def test_no_model_forward_backward_optimizer_or_network_execution_in_gate_source():
    tree = ast.parse(Path(gate.__file__).read_text())
    evaluated_calls = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    assert "backward" not in evaluated_calls
    assert "step" not in evaluated_calls
    assert "urlopen" not in evaluated_calls
    assert "requests" not in Path(gate.__file__).read_text()
