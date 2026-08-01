from __future__ import annotations

import hashlib
import inspect
import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import covapie_target_residue_atom_condition_runtime_bridge_design_v1 as design


STATE = ROOT.parent / "covapie-state" / "manual-review"
AUTHORITY = STATE / "covapie_current11_target_residue_atom_condition_authority_bundle_v1.json"
ALIGNMENT = STATE / "covapie_current11_pocket_atom_identity_alignment_bundle_v1.json"
ADAPTER = STATE / "covapie_current11_target_residue_atom_condition_adapter_bundle_v1.json"
ADAPTER_GATE = STATE / "covapie_current11_target_residue_atom_condition_adapter_gate_bundle_v1.json"
ERROR = "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_RUNTIME_BRIDGE_DESIGN_INVALID"


@pytest.fixture(scope="session")
def formal_bytes() -> tuple[bytes, bytes, bytes, bytes]:
    return AUTHORITY.read_bytes(), ALIGNMENT.read_bytes(), ADAPTER.read_bytes(), ADAPTER_GATE.read_bytes()


def _build(formal_bytes: tuple[bytes, bytes, bytes, bytes]) -> dict:
    authority, alignment, adapter, adapter_gate = formal_bytes
    return design.design_covapie_target_residue_atom_condition_runtime_bridge_v1(
        source_authority_bundle=authority,
        source_alignment_bundle=alignment,
        source_adapter_bundle=adapter,
        source_adapter_gate_bundle=adapter_gate,
        repo_root=ROOT,
    )


@pytest.fixture(scope="session")
def response(formal_bytes: tuple[bytes, bytes, bytes, bytes]) -> dict:
    return _build(formal_bytes)


def _canonical_error(action) -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        action()


def _walk(value):
    if isinstance(value, dict):
        for nested in value.values():
            yield from _walk(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            yield from _walk(nested)
    else:
        yield value


def test_public_signature_and_all() -> None:
    assert design.__all__ == (
        "design_covapie_target_residue_atom_condition_runtime_bridge_v1",
    )
    signature = inspect.signature(design.design_covapie_target_residue_atom_condition_runtime_bridge_v1)
    assert tuple(signature.parameters) == (
        "source_authority_bundle",
        "source_alignment_bundle",
        "source_adapter_bundle",
        "source_adapter_gate_bundle",
        "repo_root",
    )
    assert all(parameter.kind is inspect.Parameter.KEYWORD_ONLY for parameter in signature.parameters.values())


def test_silent_import() -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, "-c", "import covalent_ext.covapie_target_residue_atom_condition_runtime_bridge_design_v1"],
        cwd="/",
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


@pytest.mark.parametrize("index", range(4))
def test_four_formal_bundles_are_exactly_bound(formal_bytes, index: int) -> None:
    changed = list(formal_bytes)
    changed[index] = changed[index][:-1] + bytes([changed[index][-1] ^ 1])
    _canonical_error(lambda: _build(tuple(changed)))


def test_adapter_gate_transport_internal_and_production_sha(response) -> None:
    assert response["source_adapter_gate_bundle_transport_sha256"] == hashlib.sha256(ADAPTER_GATE.read_bytes()).hexdigest()
    assert response["source_adapter_gate_bundle_sha256"] == "97821184d8c76618bb549dd708132bd9579687c6f3a0ba8007d0bbc80d7d6602"
    assert response["source_adapter_gate_production_sha256"] == hashlib.sha256(
        (ROOT / "src/covalent_ext/covapie_target_residue_atom_condition_adapter_gate_v1.py").read_bytes()
    ).hexdigest()


def test_adapter_gate_was_recompiled_to_exact_canonical_bytes(formal_bytes, monkeypatch) -> None:
    calls = 0
    original = design.adapter_gate.evaluate_covapie_target_residue_atom_condition_adapter_gate_v1

    def wrapped(**kwargs):
        nonlocal calls
        calls += 1
        return original(**kwargs)

    monkeypatch.setattr(design.adapter_gate, "evaluate_covapie_target_residue_atom_condition_adapter_gate_v1", wrapped)
    _build(formal_bytes)
    assert calls == 1


def test_exact30(response) -> None:
    assert len(response) == 30
    assert tuple(response) == design.RUNTIME_BRIDGE_DESIGN_RESPONSE_FIELDS


def test_response_digest(response) -> None:
    expected = design._digest_record(
        response,
        design.RUNTIME_BRIDGE_DESIGN_RESPONSE_FIELDS,
        "runtime_bridge_design_response_sha256",
    )
    assert response["runtime_bridge_design_response_sha256"] == expected


def test_deterministic(formal_bytes, response) -> None:
    assert _build(formal_bytes) == response


def test_zero_repository_writes(formal_bytes) -> None:
    before = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    _build(formal_bytes)
    after = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    assert after == before


def test_inputs_unchanged(formal_bytes) -> None:
    snapshots = tuple(bytes(value) for value in formal_bytes)
    _build(formal_bytes)
    assert formal_bytes == snapshots


def test_no_path_in_response(response) -> None:
    assert not any(isinstance(value, Path) for value in _walk(response))


def test_dataset_split_and_collate_semantics(response) -> None:
    record = response["current_runtime_interface_records"][0]
    assert record["source_path"] == "dataset.py"
    assert record["field_split_by_pocket_mask"] is True
    assert record["field_collated_by_direct_torch_cat"] is True
    assert record["field_rebuilt_as_batch_membership_mask"] is False


def test_get_ligand_and_pocket_current_keys(response) -> None:
    record = response["current_runtime_interface_records"][1]
    assert record["current_ligand_keys"] == ["x", "one_hot", "size", "mask"]
    assert record["current_pocket_keys"] == ["x", "one_hot", "size", "mask"]
    assert record["runtime_bridge_implemented"] is False


def test_all_get_ligand_and_pocket_call_sites(response) -> None:
    assert response["current_runtime_interface_records"][1]["get_ligand_and_pocket_call_sites"] == [
        "forward",
        "sample_and_analyze_given_pocket",
        "sample_and_save_given_pocket",
        "sample_chain_and_save_given_pocket",
    ]


def test_training_validation_and_test_paths(response) -> None:
    assert response["training_path_coverage"]["all_paths_use_get_ligand_and_pocket"] is True
    assert response["evaluation_path_coverage"]["all_paths_use_get_ligand_and_pocket"] is True
    assert len(response["evaluation_path_coverage"]["paths"]) == 2


def test_given_pocket_sampling_and_inpainting_paths(response) -> None:
    coverage = response["conditional_sampling_path_coverage"]
    assert coverage["collated_given_pocket_paths_covered"] is True
    assert coverage["actual_inpainting_paths_audited"] is True
    assert len(coverage["paths"]) == 4
    assert coverage["all_paths_use_get_ligand_and_pocket"] is False
    assert coverage["bypassing_paths"] == [
        "generate_ligands->prepare_pocket->ConditionalDDPM.sample_given_pocket_or_inpaint"
    ]


def test_normalize_only_mutates_x_and_one_hot_and_preserves_sidecar(response) -> None:
    record = response["current_runtime_interface_records"][3]
    assert record["mutated_pocket_keys"] == ["one_hot", "x"]
    assert record["additional_pocket_keys_preserved_by_dictionary_identity"] is True
    assert response["normalization_preservation_policy"] == {
        "normalize_mutates_only_pocket_x_and_one_hot": True,
        "sidecar_key_preserved": True,
        "sidecar_value_not_normalized": True,
    }


def test_real_normalize_method_synthetically_preserves_sidecar() -> None:
    from equivariant_diffusion.en_diffusion import EnVariationalDiffusion

    indicator = torch.tensor([False, True], dtype=torch.bool)
    pocket = {
        "x": torch.tensor([[2.0, 4.0, 6.0], [8.0, 10.0, 12.0]]),
        "one_hot": torch.tensor([[1, 0], [0, 1]], dtype=torch.int64),
        design._FIELD: indicator,
    }
    fake_diffusion = SimpleNamespace(norm_values=(2.0, 4.0), norm_biases=(0.0, 0.5))
    ligand, normalized = EnVariationalDiffusion.normalize(fake_diffusion, pocket=pocket)
    assert ligand is None
    assert normalized is pocket
    assert normalized[design._FIELD] is indicator
    assert normalized[design._FIELD].dtype is torch.bool
    assert torch.equal(normalized[design._FIELD], torch.tensor([False, True]))


def test_conditional_ddpm_does_not_consume_indicator(response) -> None:
    record = response["current_runtime_interface_records"][2]
    assert record["consumed_pocket_keys"] == ["mask", "one_hot", "size", "x"]
    assert record["indicator_consumed"] is False


def test_egnn_forward_has_no_indicator(response) -> None:
    record = response["current_runtime_interface_records"][4]
    assert record["forward_arguments"] == ["xh_atoms", "xh_residues", "t", "mask_atoms", "mask_residues"]
    assert record["accepts_indicator"] is False
    assert response["indicator_passed_into_dynamics"] is False


@pytest.mark.parametrize(
    ("candidate", "decision"),
    [
        ("same_name_bool_key_in_pocket_runtime_dictionary", "accepted"),
        ("append_indicator_to_pocket_one_hot", "rejected"),
        ("per_sample_local_target_index_scalar", "rejected"),
        ("duplicate_target_xyz_or_atom_one_hot", "rejected"),
        ("module_global_singleton_cache_or_implicit_hook_state", "rejected"),
        ("modify_ConditionalDDPM_or_EGNNDynamics_or_add_condition_encoder", "deferred"),
    ],
)
def test_candidate_decision_matrix(response, candidate: str, decision: str) -> None:
    decisions = {record["candidate"]: record["decision"] for record in response["candidate_decisions"]}
    assert decisions[candidate] == decision


def test_same_name_sidecar_contract(response) -> None:
    assert response["source_batch_field_name"] == design._FIELD
    assert response["destination_pocket_field_name"] == design._FIELD
    assert response["selected_bridge_representation"] == "same_name_per_pocket_node_bool_sidecar"
    assert response["field_torch_dtype"] == "torch.bool"
    assert response["field_runtime_shape"] == "[sum(num_pocket_nodes)]"


def test_legacy_field_absent_passthrough(response) -> None:
    contract = response["field_required_when_present_contract"]
    assert response["field_optional_for_legacy_batches"] is True
    assert contract["legacy_absent_creates_destination_key"] is False
    assert contract["legacy_absent_creates_all_false_tensor"] is False


def test_present_bool_length_and_cardinality_contract() -> None:
    assert design._validate_present_indicator([False, True, False, True], [3, 1]) is True


@pytest.mark.parametrize(
    ("indicator", "counts"),
    [
        ([False, False], [2]),
        ([True, True], [2]),
        ([True], [2]),
        ([1, False], [2]),
    ],
)
def test_present_field_invalid_cases_fail_closed(indicator, counts) -> None:
    _canonical_error(lambda: design._validate_present_indicator(indicator, counts))


def test_mixed_zero_target_semantics_deferred(response) -> None:
    assert response["per_sample_cardinality_policy"]["mixed_noncovalent_zero_target_semantics_deferred"] is True
    assert response["field_required_when_present_contract"]["mixed_noncovalent_zero_target_semantics_deferred"] is True


def test_five_masks_exact_and_scaffold_only_present(response) -> None:
    assert response["canonical_mask_semantic_names"] == [
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    ]
    assert len(response["canonical_mask_semantic_names"]) == 5


def test_checkpoint_compatibility_all_changes_false(response) -> None:
    decision = response["checkpoint_compatibility_decision"]
    change_keys = [key for key in decision if key.startswith(("append_", "change_", "modify_", "new_", "base_"))]
    assert change_keys
    assert all(decision[key] is False for key in change_keys)


def test_no_model_forward_loss_or_training_modification(response) -> None:
    decision = response["checkpoint_compatibility_decision"]
    assert decision["modify_dataset"] is False
    assert decision["modify_collate"] is False
    assert decision["modify_ConditionalDDPM"] is False
    assert decision["modify_EGNNDynamics"] is False
    assert response["indicator_passed_into_dynamics"] is False


def test_actual_readiness_is_fail_closed_for_bypass(response) -> None:
    assert response["ready_for_runtime_bridge_implementation"] is False
    assert response["recommended_next_step"] == "resolve_covapie_external_pocket_runtime_bridge_path_coverage_v1"


def test_runtime_source_sha_drift_fails_closed(formal_bytes, monkeypatch) -> None:
    original = design._RUNTIME_SOURCE_SHA256S
    changed = list(original)
    changed[0] = (changed[0][0], "0" * 64)
    monkeypatch.setattr(design, "_RUNTIME_SOURCE_SHA256S", tuple(changed))
    _canonical_error(lambda: _build(formal_bytes))


def test_predecessor_constant_drift_fails_closed(formal_bytes, monkeypatch) -> None:
    monkeypatch.setattr(design.adapter_gate, "CANONICAL_MASK_SEMANTIC_NAMES", ("drift",))
    _canonical_error(lambda: _build(formal_bytes))


def test_response_validator_rejects_digest_drift(response) -> None:
    changed = deepcopy(response)
    changed["runtime_bridge_design_response_sha256"] = "0" * 64
    _canonical_error(lambda: design._validate_response(changed))


def test_runtime_sources_remain_at_frozen_hashes() -> None:
    for path, expected in design._RUNTIME_SOURCE_SHA256S:
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected


def test_formal_gate_shape_and_counts() -> None:
    gate = json.loads(ADAPTER_GATE.read_bytes())
    assert gate["target_residue_atom_condition_adapter_gate_record_count"] == 11
    assert gate["runtime_dataset_sample_count"] == 11
    assert gate["total_runtime_pocket_node_count"] == 2202
    assert gate["total_runtime_indicator_true_count"] == 11
    assert gate["ready_for_runtime_bridge_design"] is True
