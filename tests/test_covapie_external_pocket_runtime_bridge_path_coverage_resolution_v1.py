from __future__ import annotations

import hashlib
import inspect
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import covapie_external_pocket_runtime_bridge_path_coverage_resolution_v1 as resolution


STATE = ROOT.parent / "covapie-state" / "manual-review"
AUTHORITY = STATE / "covapie_current11_target_residue_atom_condition_authority_bundle_v1.json"
ALIGNMENT = STATE / "covapie_current11_pocket_atom_identity_alignment_bundle_v1.json"
ADAPTER = STATE / "covapie_current11_target_residue_atom_condition_adapter_bundle_v1.json"
ADAPTER_GATE = STATE / "covapie_current11_target_residue_atom_condition_adapter_gate_bundle_v1.json"
ERROR = "COVAPIE_EXTERNAL_POCKET_RUNTIME_BRIDGE_PATH_COVERAGE_INVALID"


@pytest.fixture(scope="session")
def formal_bytes() -> tuple[bytes, bytes, bytes, bytes]:
    return AUTHORITY.read_bytes(), ALIGNMENT.read_bytes(), ADAPTER.read_bytes(), ADAPTER_GATE.read_bytes()


def _build(formal_bytes: tuple[bytes, bytes, bytes, bytes]) -> dict:
    authority, alignment, adapter, gate = formal_bytes
    return resolution.resolve_covapie_external_pocket_runtime_bridge_path_coverage_v1(
        source_authority_bundle=authority,
        source_alignment_bundle=alignment,
        source_adapter_bundle=adapter,
        source_adapter_gate_bundle=gate,
        repo_root=ROOT,
    )


@pytest.fixture(scope="session")
def response(formal_bytes) -> dict:
    return _build(formal_bytes)


def _canonical_error(action) -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}$"):
        action()


def _selector(**changes) -> dict:
    value = {
        "chain_id": "A",
        "residue_sequence_number": 279,
        "residue_insertion_code": " ",
        "residue_name": "CYS",
        "atom_name": "SG",
        "element": "S",
    }
    value.update(changes)
    return value


class Chain:
    def __init__(self, chain_id: str):
        self.id = chain_id


class Residue:
    def __init__(self, chain: Chain, number: int, name: str = "CYS", insertion: str = " ", disordered: bool = False):
        self._chain = chain
        self.id = (" ", number, insertion)
        self._name = name
        self._disordered = disordered

    def get_parent(self):
        return self._chain

    def get_resname(self):
        return self._name

    def is_disordered(self):
        return self._disordered


class Atom:
    def __init__(self, residue: Residue, name: str, element: str, disordered: bool = False):
        self._residue = residue
        self._name = name
        self.element = element
        self._disordered = disordered

    def get_parent(self):
        return self._residue

    def get_name(self):
        return self._name

    def get_coord(self):
        raise AssertionError("coordinates must not be read for identity")

    def is_disordered(self):
        return self._disordered


def _atoms(*, duplicate=False, target_disordered=False, residue_disordered=False):
    chain = Chain("A")
    target_residue = Residue(chain, 279, disordered=residue_disordered)
    atoms = [
        Atom(Residue(chain, 10, name="ALA"), "CA", "C"),
        Atom(target_residue, "CB", "C"),
        Atom(target_residue, "SG", "S", disordered=target_disordered),
        Atom(Residue(Chain("B"), 279), "SG", "S"),
    ]
    if duplicate:
        atoms.append(Atom(target_residue, "SG", "S"))
    return atoms


def _walk(value):
    if isinstance(value, dict):
        for nested in value.values():
            yield from _walk(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            yield from _walk(nested)
    else:
        yield value


def test_public_signature_all_and_keyword_only() -> None:
    assert resolution.__all__ == (
        "resolve_covapie_external_pocket_runtime_bridge_path_coverage_v1",
    )
    signature = inspect.signature(resolution.resolve_covapie_external_pocket_runtime_bridge_path_coverage_v1)
    assert tuple(signature.parameters) == (
        "source_authority_bundle", "source_alignment_bundle", "source_adapter_bundle",
        "source_adapter_gate_bundle", "repo_root",
    )
    assert all(value.kind is inspect.Parameter.KEYWORD_ONLY for value in signature.parameters.values())


def test_silent_import() -> None:
    environment = dict(os.environ, PYTHONPATH=str(SRC), PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run(
        [sys.executable, "-c", "import covalent_ext.covapie_external_pocket_runtime_bridge_path_coverage_resolution_v1"],
        cwd="/", env=environment, text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


@pytest.mark.parametrize("index", range(4))
def test_four_formal_bundles_exactly_bound(formal_bytes, index) -> None:
    changed = list(formal_bytes)
    changed[index] = changed[index][:-1] + bytes([changed[index][-1] ^ 1])
    _canonical_error(lambda: _build(tuple(changed)))


def test_formal_transport_hashes(response) -> None:
    assert response["source_authority_bundle_transport_sha256"] == hashlib.sha256(AUTHORITY.read_bytes()).hexdigest()
    assert response["source_alignment_bundle_transport_sha256"] == hashlib.sha256(ALIGNMENT.read_bytes()).hexdigest()
    assert response["source_adapter_bundle_transport_sha256"] == hashlib.sha256(ADAPTER.read_bytes()).hexdigest()
    assert response["source_adapter_gate_bundle_transport_sha256"] == hashlib.sha256(ADAPTER_GATE.read_bytes()).hexdigest()


def test_adapter_gate_is_recompiled_by_predecessor(formal_bytes, monkeypatch) -> None:
    calls = 0
    original = resolution.predecessor.adapter_gate.evaluate_covapie_target_residue_atom_condition_adapter_gate_v1

    def wrapped(**kwargs):
        nonlocal calls
        calls += 1
        return original(**kwargs)

    monkeypatch.setattr(resolution.predecessor.adapter_gate, "evaluate_covapie_target_residue_atom_condition_adapter_gate_v1", wrapped)
    _build(formal_bytes)
    assert calls == 1


def test_predecessor_function_is_reinvoked(formal_bytes, monkeypatch) -> None:
    calls = 0
    original = resolution.predecessor.design_covapie_target_residue_atom_condition_runtime_bridge_v1

    def wrapped(**kwargs):
        nonlocal calls
        calls += 1
        return original(**kwargs)

    monkeypatch.setattr(resolution.predecessor, "design_covapie_target_residue_atom_condition_runtime_bridge_v1", wrapped)
    _build(formal_bytes)
    assert calls == 1


def test_predecessor_production_and_response_hash(response) -> None:
    assert response["source_runtime_bridge_design_production_sha256"] == hashlib.sha256(
        (SRC / "covalent_ext/covapie_target_residue_atom_condition_runtime_bridge_design_v1.py").read_bytes()
    ).hexdigest()
    assert response["source_runtime_bridge_design_response_sha256"] == "1c90069e6d64916504f6a6e1e0d852e95351dc261e36ea3eab3d0ef4880ec6f2"


def test_predecessor_unique_blocker_reproduced(response) -> None:
    assert response["source_runtime_bridge_blocker"] == "generate_ligands->prepare_pocket->ConditionalDDPM.sample_given_pocket_or_inpaint"


def test_exact36_and_digest(response) -> None:
    assert len(response) == 36
    assert tuple(response) == resolution.EXTERNAL_PATH_COVERAGE_RESOLUTION_FIELDS
    assert response["external_path_coverage_resolution_sha256"] == resolution._digest_record(
        response, resolution.EXTERNAL_PATH_COVERAGE_RESOLUTION_FIELDS, "external_path_coverage_resolution_sha256"
    )


def test_deterministic(formal_bytes, response) -> None:
    assert _build(formal_bytes) == response


def test_zero_repository_writes(formal_bytes) -> None:
    command = ["git", "status", "--porcelain=v1", "--untracked-files=all"]
    before = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=True).stdout
    _build(formal_bytes)
    after = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=True).stdout
    assert after == before


def test_inputs_unchanged(formal_bytes) -> None:
    snapshots = tuple(bytes(value) for value in formal_bytes)
    _build(formal_bytes)
    assert formal_bytes == snapshots


def test_no_path_objects_in_response(response) -> None:
    assert not any(isinstance(value, Path) for value in _walk(response))


def test_generate_current_interface(response) -> None:
    interface = response["generate_ligands_current_interface"]
    assert interface["positional_parameters"][:5] == ["self", "pdb_file", "n_samples", "pocket_ids", "ref_ligand"]
    assert interface["var_keyword"] == "kwargs"
    assert interface["selector_argument_currently_explicit"] is False
    assert interface["selector_must_not_enter_kwargs"] is True
    assert interface["bypasses_get_ligand_and_pocket"] is True


def test_prepare_current_interface_and_return_keys(response) -> None:
    interface = response["prepare_pocket_current_interface"]
    assert interface["positional_parameters"] == ["self", "biopython_residues", "repeats"]
    assert interface["current_return_keys"] == ["x", "one_hot", "size", "mask"]
    assert interface["full_atom_base_sequence"] == "pocket_atoms"
    assert interface["sidecar_currently_returned"] is False


def test_all_mandatory_runtime_sources_audited(response) -> None:
    paths = [record["source_path"] for record in response["audited_runtime_source_records"]]
    assert paths[:4] == [
        "lightning_modules.py", "dataset.py", "equivariant_diffusion/conditional_model.py",
        "equivariant_diffusion/en_diffusion.py",
    ]
    assert all(record["audited"] is True for record in response["audited_runtime_source_records"])


def test_all_generate_call_sites_audited(response) -> None:
    assert [record["caller_path"] for record in response["generate_ligands_call_site_records"]] == [
        "generate_ligands.py", "test.py", "colab/DiffSBDD.ipynb",
    ]
    assert all(record["covered"] is True for record in response["generate_ligands_call_site_records"])


def test_all_prepare_call_sites_audited(response) -> None:
    records = response["cli_or_public_caller_forwarding_contract"]["prepare_pocket_call_site_records"]
    assert [record["caller_path"] for record in records] == [
        "lightning_modules.py", "optimize.py", "inpaint.py", "scripts/covalent_inpaint_demo.py",
    ]
    assert all(record["covered"] is True for record in records)


def test_pocket_ids_and_ref_ligand_routes_are_frozen(response) -> None:
    assert response["generate_ligands_current_interface"]["pocket_selection_routes"] == ["pocket_ids", "ref_ligand"]
    assert response["target_membership_policy"]["applies_to_routes"] == ["pocket_ids", "ref_ligand"]


def test_selector_exact6_and_valid_cys_sg() -> None:
    assert resolution.TARGET_RESIDUE_ATOM_CONDITION_SPEC_FIELDS == (
        "chain_id", "residue_sequence_number", "residue_insertion_code",
        "residue_name", "atom_name", "element",
    )
    assert resolution._validate_target_residue_atom_condition_spec(_selector()) == _selector()


@pytest.mark.parametrize("chain", ["", None, 1])
def test_selector_chain_missing_or_empty_rejected(chain) -> None:
    _canonical_error(lambda: resolution._validate_target_residue_atom_condition_spec(_selector(chain_id=chain)))


@pytest.mark.parametrize("number", [True, False, "279", 279.0, None])
def test_selector_residue_number_bool_or_nonint_rejected(number) -> None:
    _canonical_error(lambda: resolution._validate_target_residue_atom_condition_spec(_selector(residue_sequence_number=number)))


@pytest.mark.parametrize("insertion", ["A", "", "  ", None])
def test_nonblank_or_non_single_insertion_rejected(insertion) -> None:
    _canonical_error(lambda: resolution._validate_target_residue_atom_condition_spec(_selector(residue_insertion_code=insertion)))


@pytest.mark.parametrize(("field", "value"), [("residue_name", "ALA"), ("atom_name", "CA"), ("element", "C")])
def test_non_cys_sg_s_rejected(field, value) -> None:
    _canonical_error(lambda: resolution._validate_target_residue_atom_condition_spec(_selector(**{field: value})))


def test_selector_extra_or_missing_field_rejected() -> None:
    extra = _selector(extra="bad")
    missing = _selector()
    del missing["chain_id"]
    _canonical_error(lambda: resolution._validate_target_residue_atom_condition_spec(extra))
    _canonical_error(lambda: resolution._validate_target_residue_atom_condition_spec(missing))


def test_ca_profile_selector_present_rejected_contract(response) -> None:
    policy = response["pocket_representation_policy"]
    assert policy["full_atom_required_when_selector_present"] is True
    assert policy["CA_selector_present_rejected"] is True
    assert policy["fabricate_SG_indicator_for_CA"] is False


def test_exact_pocket_atom_order_location_and_no_coordinate_use() -> None:
    assert resolution._locate_target_atom_in_pocket_atoms(_atoms(), _selector(), {"C": 0, "S": 1}) == 2


def test_target_absent_rejected() -> None:
    atoms = _atoms()
    _canonical_error(lambda: resolution._locate_target_atom_in_pocket_atoms(atoms, _selector(chain_id="Z"), {"S": 1}))


def test_duplicate_target_rejected() -> None:
    _canonical_error(lambda: resolution._locate_target_atom_in_pocket_atoms(_atoms(duplicate=True), _selector(), {"S": 1}))


@pytest.mark.parametrize("atom_disordered,residue_disordered", [(True, False), (False, True)])
def test_disordered_target_rejected(atom_disordered, residue_disordered) -> None:
    _canonical_error(lambda: resolution._locate_target_atom_in_pocket_atoms(
        _atoms(target_disordered=atom_disordered, residue_disordered=residue_disordered), _selector(), {"S": 1}
    ))


def test_target_element_must_be_checkpoint_representable() -> None:
    _canonical_error(lambda: resolution._locate_target_atom_in_pocket_atoms(_atoms(), _selector(), {"C": 0}))


def test_target_must_already_be_in_pocket_and_no_append(response) -> None:
    policy = response["target_membership_policy"]
    assert policy["target_must_already_be_in_selected_pocket"] is True
    assert policy["auto_append_target_residue"] is False
    assert policy["reorder_residues_or_atoms"] is False


def test_repeat_one_indicator_contract() -> None:
    result = resolution._build_repeated_indicator_design_oracle(pocket_atom_count=4, target_local_index=2, repeats=1)
    tensor = torch.tensor(result["repeated_indicator"], dtype=torch.bool)
    assert tensor.dtype is torch.bool
    assert tensor.tolist() == [False, False, True, False]
    assert tensor.sum().item() == 1


def test_repeat_many_one_true_per_sample_and_mask_alignment() -> None:
    result = resolution._build_repeated_indicator_design_oracle(pocket_atom_count=4, target_local_index=2, repeats=3)
    indicator = torch.tensor(result["repeated_indicator"], dtype=torch.bool)
    mask = torch.tensor(result["pocket_mask"], dtype=torch.long)
    assert indicator.numel() == 12
    assert indicator.reshape(3, 4).sum(dim=1).tolist() == [1, 1, 1]
    assert mask[indicator].tolist() == torch.arange(3).tolist()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"pocket_atom_count": 0, "target_local_index": 0, "repeats": 1},
        {"pocket_atom_count": 2, "target_local_index": 2, "repeats": 1},
        {"pocket_atom_count": 2, "target_local_index": 0, "repeats": 0},
        {"pocket_atom_count": True, "target_local_index": 0, "repeats": 1},
    ],
)
def test_invalid_repeat_or_index_fails_closed(kwargs) -> None:
    _canonical_error(lambda: resolution._build_repeated_indicator_design_oracle(**kwargs))


def test_legacy_absent_creates_no_key(response) -> None:
    assert response["legacy_external_path_policy"]["destination_key_absent"] is True
    sidecar = response["prepared_pocket_sidecar_contract"]
    assert sidecar["selector_absent_key_absent"] is True
    assert sidecar["selector_absent_all_false_tensor"] is False


def test_conditional_and_inpainting_paths_are_symmetric(response) -> None:
    conditional = response["conditional_generation_path_contract"]
    inpainting = response["inpainting_path_contract"]
    assert conditional["covered"] is True
    assert inpainting["covered"] is True
    assert conditional["same_prepared_pocket_sidecar_carried"] is True
    assert inpainting["same_prepared_pocket_sidecar_carried"] is True
    assert conditional["indicator_consumed_by_model"] is inpainting["indicator_consumed_by_model"] is False


def test_all_public_callers_have_forwarding_contract(response) -> None:
    contract = response["cli_or_public_caller_forwarding_contract"]
    assert contract["generate_ligands_call_site_count"] == 3
    assert contract["prepare_pocket_call_site_count"] == 4
    assert contract["all_public_callers_have_forwarding_contract"] is True
    assert contract["public_python_example"]["named_argument"] == "target_residue_atom_condition_spec"


@pytest.mark.parametrize(
    ("candidate", "decision"),
    [
        ("explicit_structured_selector_forwarded_generate_ligands_to_prepare_pocket", "accepted"),
        ("exact_identity_match_in_actual_pocket_atoms_order", "accepted"),
        ("same_name_bool_sidecar_repeated_by_sample_block", "accepted"),
        ("infer_unique_cys_or_sg", "rejected"),
        ("nearest_coordinate_or_nearest_ref_ligand_selection", "rejected"),
        ("auto_append_target_residue_to_pocket", "rejected"),
        ("user_supplied_local_node_index", "rejected"),
        ("user_supplied_pdb_atom_serial_as_primary_identity", "rejected"),
        ("all_false_placeholder", "rejected"),
        ("append_indicator_to_pocket_one_hot", "rejected"),
        ("global_mutable_target_state", "rejected"),
        ("disordered_altloc_target_semantics", "deferred"),
        ("nonblank_insertion_code_pocket_ids_extension", "deferred"),
        ("DDPM_or_EGNN_model_consumption", "deferred"),
        ("mixed_noncovalent_zero_target_semantics", "deferred"),
    ],
)
def test_candidate_decision_matrix(response, candidate, decision) -> None:
    actual = {item["candidate"]: item["decision"] for item in response["candidate_decisions"]}
    assert actual[candidate] == decision


def test_five_masks_exact_including_scaffold_only(response) -> None:
    assert response["canonical_mask_semantic_names"] == [
        "warhead_only", "linker_plus_warhead", "scaffold_plus_warhead",
        "scaffold_only", "scaffold_plus_linker_plus_warhead",
    ]
    assert len(response["canonical_mask_semantic_names"]) == 5


def test_checkpoint_compatibility(response) -> None:
    decision = response["checkpoint_compatibility_decision"]
    keys = [key for key in decision if key.startswith(("append_", "change_", "modify_", "new_", "base_"))]
    assert keys
    assert all(decision[key] is False for key in keys)


def test_no_model_consumption_forward_loss_or_training_change(response) -> None:
    assert response["conditional_generation_path_contract"]["indicator_passed_into_dynamics"] is False
    assert response["inpainting_path_contract"]["indicator_passed_into_dynamics"] is False
    decision = response["checkpoint_compatibility_decision"]
    assert decision["modify_dataset"] is False
    assert decision["modify_ConditionalDDPM"] is False
    assert decision["modify_EGNNDynamics"] is False


def test_resolution_ready_and_next_step_derived(response) -> None:
    assert response["unresolved_path_blockers"] == []
    assert response["ready_for_runtime_bridge_implementation"] is True
    assert response["recommended_next_step"] == "implement_covapie_target_residue_atom_condition_runtime_bridge_v1"
    assert response["feature_semantics_audit_required_before_training"] is True


def test_response_validator_fails_if_readiness_is_hardcoded_drift(response) -> None:
    changed = deepcopy(response)
    changed["ready_for_runtime_bridge_implementation"] = False
    changed["external_path_coverage_resolution_sha256"] = resolution._digest_record(
        changed, resolution.EXTERNAL_PATH_COVERAGE_RESOLUTION_FIELDS, "external_path_coverage_resolution_sha256"
    )
    _canonical_error(lambda: resolution._validate_response(changed))


def test_response_digest_drift_fails_closed(response) -> None:
    changed = deepcopy(response)
    changed["external_path_coverage_resolution_sha256"] = "0" * 64
    _canonical_error(lambda: resolution._validate_response(changed))


def test_resigned_nested_semantic_contract_drift_is_rejected(response) -> None:
    mutations = (
        lambda value: value["target_selector_fixed_v1_semantics"].__setitem__("residue_name", "ALA"),
        lambda value: value["target_selector_validation_contract"].__setitem__("coordinate_identity_matching_allowed", True),
        lambda value: value["pocket_representation_policy"].__setitem__("CA_selector_present_rejected", False),
        lambda value: value["target_membership_policy"].__setitem__("auto_append_target_residue", True),
        lambda value: value["target_atom_order_binding_policy"].__setitem__("coordinates_used_for_identity", True),
        lambda value: value["repeated_indicator_policy"].__setitem__("per_sample_true_count", 0),
        lambda value: value["prepared_pocket_sidecar_contract"].__setitem__("field_name", "wrong"),
        lambda value: value["legacy_external_path_policy"].__setitem__("destination_key_absent", False),
        lambda value: value["checkpoint_compatibility_decision"].__setitem__("append_to_pocket_one_hot", True),
        lambda value: value["candidate_decisions"][3].__setitem__("decision", "accepted"),
    )
    for mutate in mutations:
        changed = deepcopy(response)
        mutate(changed)
        changed["external_path_coverage_resolution_sha256"] = resolution._digest_record(
            changed,
            resolution.EXTERNAL_PATH_COVERAGE_RESOLUTION_FIELDS,
            "external_path_coverage_resolution_sha256",
        )
        assert changed["external_path_coverage_resolution_sha256"] != response["external_path_coverage_resolution_sha256"]
        _canonical_error(lambda changed=changed: resolution._validate_response(changed))


def test_resigned_source_and_caller_contract_drift_is_rejected(response) -> None:
    mutations = (
        lambda value: value.__setitem__("source_authority_bundle_transport_sha256", "0" * 64),
        lambda value: value.__setitem__("source_runtime_bridge_design_production_sha256", "0" * 64),
        lambda value: value["audited_runtime_source_records"][0].__setitem__("source_sha256", "0" * 64),
        lambda value: value["generate_ligands_call_site_records"][0].__setitem__("caller_path", "wrong.py"),
        lambda value: value["generate_ligands_call_site_records"][0].__setitem__("future_selector_forwarding_surface", "wrong_surface"),
        lambda value: value["cli_or_public_caller_forwarding_contract"]["prepare_pocket_call_site_records"][0].__setitem__("future_selector_forwarding_surface", "wrong_surface"),
        lambda value: value["generate_ligands_call_site_records"][1].__setitem__("caller_path", "covered_but_wrong.py"),
    )
    for mutate in mutations:
        changed = deepcopy(response)
        mutate(changed)
        assert all(record["covered"] is True for record in changed["generate_ligands_call_site_records"])
        changed["external_path_coverage_resolution_sha256"] = resolution._digest_record(
            changed,
            resolution.EXTERNAL_PATH_COVERAGE_RESOLUTION_FIELDS,
            "external_path_coverage_resolution_sha256",
        )
        assert changed["external_path_coverage_resolution_sha256"] != response["external_path_coverage_resolution_sha256"]
        _canonical_error(lambda changed=changed: resolution._validate_response(changed))


def test_runtime_source_drift_fails_closed(formal_bytes, monkeypatch) -> None:
    changed = list(resolution._RUNTIME_SOURCE_SHA256S)
    changed[0] = (changed[0][0], "0" * 64)
    monkeypatch.setattr(resolution, "_RUNTIME_SOURCE_SHA256S", tuple(changed))
    _canonical_error(lambda: _build(formal_bytes))


def test_caller_source_drift_fails_closed(formal_bytes, monkeypatch) -> None:
    changed = list(resolution._CALLER_SOURCE_SHA256S)
    changed[0] = (changed[0][0], "0" * 64)
    monkeypatch.setattr(resolution, "_CALLER_SOURCE_SHA256S", tuple(changed))
    _canonical_error(lambda: _build(formal_bytes))


def test_predecessor_constant_drift_fails_closed(formal_bytes, monkeypatch) -> None:
    monkeypatch.setattr(resolution.predecessor, "CANONICAL_MASK_SEMANTIC_NAMES", ("drift",))
    _canonical_error(lambda: _build(formal_bytes))


def test_runtime_sources_remain_frozen() -> None:
    for path, expected in (*resolution._RUNTIME_SOURCE_SHA256S, *resolution._CALLER_SOURCE_SHA256S):
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
