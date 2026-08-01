from __future__ import annotations

import copy
import hashlib
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from covalent_ext import covapie_target_residue_atom_condition_adapter_design_v1 as design


REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PATH = Path(
    "/cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/"
    "covapie-state/manual-review/"
    "covapie_current11_target_residue_atom_condition_authority_bundle_v1.json"
)


@pytest.fixture(scope="module")
def authority_bytes() -> bytes:
    return AUTHORITY_PATH.read_bytes()


@pytest.fixture(scope="module")
def authority_records(authority_bytes: bytes) -> list[dict[str, object]]:
    return json.loads(authority_bytes)["target_residue_atom_condition_records"]


@pytest.fixture(scope="module")
def formal_response(authority_bytes: bytes) -> dict[str, object]:
    return design._reference_design_covapie_target_residue_atom_condition_adapter_v1(
        source_authority_bundle=authority_bytes,
        repo_root=REPO_ROOT,
    )


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _synthetic_pocket_row(authority: dict[str, object]) -> dict[str, str]:
    return {
        "pdb_id": str(authority["pdb_id"]),
        "atom_site_id": str(authority["source_atom_site_id"]),
        "type_symbol": str(authority["protein_type_symbol"]),
        "atom_name": str(authority["protein_auth_atom_id"]),
        "residue_name": str(authority["protein_auth_comp_id"]),
        "auth_asym_id": str(authority["protein_auth_asym_id"]),
        "auth_seq_id": str(authority["protein_auth_seq_id"]),
        "label_asym_id": str(authority["protein_label_asym_id"]),
        "label_seq_id": str(authority["protein_label_seq_id"]),
        "source_raw_file": "synthetic/source.cif",
    }


def _mapping(
    authority: dict[str, object], rows: list[dict[str, str]], *,
    schema_complete: bool = True, lineage_matches: bool = True,
    row_order_bound: bool = True, candidate_path: str = "synthetic/pocket.csv",
) -> dict[str, object]:
    return design._mapping_record(
        authority=authority,
        candidate_path=candidate_path,
        candidate_sha256="1" * 64 if candidate_path else "",
        pocket_rows=rows,
        schema_complete=schema_complete,
        lineage_matches=lineage_matches,
        row_order_bound=row_order_bound,
    )


def _proposal(**overrides: object) -> bool:
    values: dict[str, object] = {
        "field_name": "pocket_target_residue_atom_condition_indicator",
        "storage_domain": "per_pocket_node",
        "numpy_dtype": "bool",
        "torch_dtype": "torch.bool",
        "sample_shape": "[num_pocket_nodes]",
        "duplicated_target_xyz": False,
        "append_to_pocket_one_hot": False,
    }
    values.update(overrides)
    return design._validate_representation_proposal(**values)  # type: ignore[arg-type]


def test_private_signature_all_and_silent_import() -> None:
    signature = inspect.signature(
        design._reference_design_covapie_target_residue_atom_condition_adapter_v1
    )
    assert tuple(signature.parameters) == ("source_authority_bundle", "repo_root")
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    assert design.__all__ == ()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(REPO_ROOT / "src"))
    completed = subprocess.run(
        [sys.executable, "-B", "-c", "import covalent_ext.covapie_target_residue_atom_condition_adapter_design_v1"],
        cwd=REPO_ROOT, env=env, check=False, capture_output=True, text=True,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == ""


def test_authority_transport_internal_and_record_count(authority_bytes: bytes) -> None:
    bundle = json.loads(authority_bytes)
    assert len(authority_bytes) == 12964
    assert _sha(authority_bytes) == design._AUTHORITY_TRANSPORT_SHA256
    assert bundle["target_residue_atom_condition_authority_bundle_sha256"] == design._AUTHORITY_INTERNAL_SHA256
    assert bundle["target_residue_atom_condition_record_count"] == 11
    assert bundle["resolved_authoritative_count"] == 11
    assert bundle["all_records_resolved_authoritative"] is True
    assert bundle["ready_for_target_residue_atom_condition_adapter_design"] is True


def test_exact20_and_response_digest(formal_response: dict[str, object]) -> None:
    assert len(design.ADAPTER_DESIGN_RESPONSE_FIELDS) == 20
    assert tuple(formal_response) == design.ADAPTER_DESIGN_RESPONSE_FIELDS
    unsigned = dict(formal_response)
    digest = unsigned.pop("adapter_design_response_sha256")
    assert digest == _sha(_canonical(unsigned))


def test_deterministic_zero_writes_and_inputs_unchanged(authority_bytes: bytes) -> None:
    before_authority = bytes(authority_bytes)
    before_status = subprocess.run(
        ["git", "status", "--short"], cwd=REPO_ROOT, check=True,
        capture_output=True, text=True,
    ).stdout
    first = design._reference_design_covapie_target_residue_atom_condition_adapter_v1(
        source_authority_bundle=authority_bytes, repo_root=REPO_ROOT,
    )
    second = design._reference_design_covapie_target_residue_atom_condition_adapter_v1(
        source_authority_bundle=authority_bytes, repo_root=REPO_ROOT,
    )
    after_status = subprocess.run(
        ["git", "status", "--short"], cwd=REPO_ROOT, check=True,
        capture_output=True, text=True,
    ).stdout
    assert first == second
    assert authority_bytes == before_authority
    assert before_status == after_status


def test_authority_tamper_and_bad_calls_use_canonical_value_error(authority_bytes: bytes) -> None:
    tampered = bytearray(authority_bytes)
    tampered[20] ^= 1
    bad_calls = (
        {"source_authority_bundle": bytes(tampered), "repo_root": REPO_ROOT},
        {"source_authority_bundle": authority_bytes, "repo_root": str(REPO_ROOT)},
        {"source_authority_bundle": bytearray(authority_bytes), "repo_root": REPO_ROOT},
    )
    for kwargs in bad_calls:
        with pytest.raises(ValueError, match=f"^{design._ERROR}$"):
            design._reference_design_covapie_target_residue_atom_condition_adapter_v1(**kwargs)  # type: ignore[arg-type]


def test_source_module_sha_drift_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    changed = list(design._SOURCE_AUDIT)
    category, path, _digest, observation = changed[0]
    changed[0] = (category, path, "0" * 64, observation)
    monkeypatch.setattr(design, "_SOURCE_AUDIT", tuple(changed))
    with pytest.raises(ValueError, match=f"^{design._ERROR}$"):
        design._runtime_records(REPO_ROOT)


def test_runtime_dataset_and_collate_rules_are_observed(formal_response: dict[str, object]) -> None:
    records = {row["source_path"]: row for row in formal_response["current_runtime_interface_records"]}  # type: ignore[index]
    assert records["dataset.py"]["source_sha256"] == "d1c548185521692ca14be062e34d5bea617f8d3c89a22eaef4ddb13a52907c99"
    source = (REPO_ROOT / "dataset.py").read_text(encoding="utf-8")
    assert "if 'lig' in k" in source
    assert "else np.where(np.diff(data['pocket_mask']))" in source
    assert "elif 'mask' in prop:" in source
    assert "i * torch.ones(len(x[prop]))" in source


def test_model_keys_fixed_width_and_conditional_path_are_observed(formal_response: dict[str, object]) -> None:
    lightning = (REPO_ROOT / "lightning_modules.py").read_text(encoding="utf-8")
    dynamics = (REPO_ROOT / "equivariant_diffusion/dynamics.py").read_text(encoding="utf-8")
    conditional = (REPO_ROOT / "equivariant_diffusion/conditional_model.py").read_text(encoding="utf-8")
    for literal in ("'x'", "'one_hot'", "'size'", "'mask'"):
        assert literal in lightning
    assert "nn.Linear(residue_nf, 2 * residue_nf)" in dynamics
    assert "xh0_pocket = torch.cat([pocket['x'], pocket['one_hot']], dim=1)" in conditional
    assert "def forward(self, ligand, pocket, return_info=False):" in conditional
    assert formal_response["source_dynamics_module_sha256"] == "16b008598de7c61c0b5575e3af02f9b1a9e6697559864df1591314e4b4ec6b9f"


def test_selected_field_contract_and_name(formal_response: dict[str, object]) -> None:
    assert _proposal() is True
    naming = formal_response["adapter_input_contract_records"][3]  # type: ignore[index]
    assert naming == {
        "contract": "npz_key_naming",
        "field_name": "pocket_target_residue_atom_condition_indicator",
        "contains_mask": False,
        "contains_lig": False,
        "contains_pocket": True,
    }
    numeric = formal_response["adapter_output_contract_records"][0]  # type: ignore[index]
    assert numeric["storage_domain"] == "per_pocket_node"
    assert numeric["numpy_dtype"] == "bool"
    assert numeric["torch_dtype"] == "torch.bool"
    assert numeric["sample_shape"] == "[num_pocket_nodes]"
    assert numeric["batch_shape"] == "[sum(num_pocket_nodes)]"


def test_indicator_cardinality_contract() -> None:
    assert design._validate_indicator_contract(values=[False, True, False], authority_declares_covalent=True)
    assert design._validate_indicator_contract(values=[False, False], authority_declares_covalent=False)
    for values, covalent in (([True, True], True), ([False, False], True), ([True, False], False)):
        with pytest.raises(ValueError, match=f"^{design._ERROR}$"):
            design._validate_indicator_contract(values=values, authority_declares_covalent=covalent)


@pytest.mark.parametrize(
    "override",
    (
        {"storage_domain": "per_sample_scalar"},
        {"numpy_dtype": "object"},
        {"numpy_dtype": "str"},
        {"duplicated_target_xyz": True},
        {"append_to_pocket_one_hot": True},
        {"field_name": "pocket_target_mask"},
        {"field_name": "lig_target_indicator"},
    ),
)
def test_rejected_representation_proposals(override: dict[str, object]) -> None:
    with pytest.raises(ValueError, match=f"^{design._ERROR}$"):
        _proposal(**override)


def test_target_xyz_and_one_hot_are_derived_not_duplicated(formal_response: dict[str, object]) -> None:
    coordinate = next(
        row for row in formal_response["adapter_output_contract_records"]  # type: ignore[union-attr]
        if row["output_kind"] == "coordinate_contract"
    )
    assert coordinate["target_xyz_duplicated"] is False
    assert coordinate["target_xyz_derivation"] == "pocket_coords[indicator]"
    assert coordinate["target_atom_one_hot_duplicated"] is False
    assert coordinate["target_atom_one_hot_derivation"] == "pocket_one_hot[indicator]"


def test_source_atom_site_id_unique_mapping_ready_when_row_bound(authority_records: list[dict[str, object]]) -> None:
    authority = authority_records[0]
    result = _mapping(authority, [_synthetic_pocket_row(authority)])
    assert result["mapping_status"] == "mapping_ready_unique"
    assert result["identity_match_count"] == 1
    assert result["proposed_local_pocket_index"] == 0
    assert result["mapping_blocking_reasons"] == []


def test_mapping_zero_multiple_unbound_schema_and_lineage_fail_closed(authority_records: list[dict[str, object]]) -> None:
    authority = authority_records[0]
    row = _synthetic_pocket_row(authority)
    cases = (
        (_mapping(authority, []), "blocked_target_atom_missing"),
        (_mapping(authority, [row, copy.deepcopy(row)]), "blocked_target_atom_ambiguous"),
        (_mapping(authority, [row], row_order_bound=False), "blocked_pocket_row_order_unbound"),
        (_mapping(authority, [row], schema_complete=False), "blocked_schema_incomplete"),
        (_mapping(authority, [row], lineage_matches=False), "blocked_lineage_mismatch"),
        (_mapping(authority, [], candidate_path=""), "blocked_identity_source_missing"),
    )
    for result, expected in cases:
        assert result["mapping_status"] == expected
        assert result["mapping_status"] in design.MAPPING_STATUSES


def test_full_protein_identity_table_without_pocket_row_binding_is_not_ready(authority_records: list[dict[str, object]]) -> None:
    authority = authority_records[0]
    result = design._mapping_record(
        authority=authority,
        candidate_path="synthetic/full_protein_atom_table.csv",
        candidate_sha256="3" * 64,
        pocket_rows=[_synthetic_pocket_row(authority)],
        schema_complete=True,
        lineage_matches=True,
        row_order_bound=False,
    )
    assert result["identity_match_count"] == 1
    assert result["mapping_status"] == "blocked_pocket_row_order_unbound"
    assert result["pocket_row_order_binding_observed"] is False


def test_mapping_record_digest(authority_records: list[dict[str, object]]) -> None:
    record = _mapping(authority_records[0], [_synthetic_pocket_row(authority_records[0])])
    assert tuple(record) == design.MAPPING_AUDIT_RECORD_FIELDS
    unsigned = dict(record)
    digest = unsigned.pop("mapping_audit_record_sha256")
    assert digest == _sha(_canonical(unsigned))


def test_coordinate_matching_and_fallbacks_are_explicitly_rejected(formal_response: dict[str, object]) -> None:
    authority_contract = formal_response["adapter_input_contract_records"][0]  # type: ignore[index]
    cardinality_contract = formal_response["adapter_input_contract_records"][2]  # type: ignore[index]
    assert authority_contract["selector"] == "source_atom_site_id"
    assert authority_contract["coordinate_matching_allowed"] is False
    assert cardinality_contract["first_cys_fallback_allowed"] is False
    decisions = {row["candidate"]: row for row in formal_response["adapter_output_contract_records"] if row["output_kind"] == "representation_decision"}  # type: ignore[union-attr]
    assert decisions["coordinate_matching"]["accepted"] is False
    assert decisions["per_sample_target_xyz"]["accepted"] is False


def test_formal_current11_unique_identity_but_unbound_row_order(formal_response: dict[str, object]) -> None:
    records = formal_response["mapping_audit_records"]
    assert len(records) == 11  # type: ignore[arg-type]
    assert all(record["identity_match_count"] == 1 for record in records)  # type: ignore[union-attr]
    assert all(record["pocket_row_order_binding_observed"] is False for record in records)  # type: ignore[union-attr]
    assert {record["mapping_status"] for record in records} == {"blocked_pocket_row_order_unbound"}  # type: ignore[union-attr]
    assert formal_response["current11_unique_mapping_count"] == 0
    assert formal_response["current11_blocked_mapping_count"] == 11
    assert formal_response["ready_for_adapter_implementation"] is False
    assert formal_response["recommended_next_step"] == "implement_covapie_current11_pocket_atom_identity_alignment_v1"


def test_five_canonical_masks_exact_b3_and_no_sixth(formal_response: dict[str, object]) -> None:
    masks = formal_response["canonical_mask_semantic_names"]
    assert design._validate_mask_contract(masks) is True  # type: ignore[arg-type]
    assert len(masks) == 5  # type: ignore[arg-type]
    assert masks[3] == "scaffold_only"  # type: ignore[index]
    with pytest.raises(ValueError, match=f"^{design._ERROR}$"):
        design._validate_mask_contract([*masks, "sixth_mask"])  # type: ignore[misc]


def test_condition_is_orthogonal_to_all_five_masks(formal_response: dict[str, object]) -> None:
    field = formal_response["adapter_output_contract_records"][0]["field_name"]  # type: ignore[index]
    matrix = [(mask, field) for mask in formal_response["canonical_mask_semantic_names"]]  # type: ignore[union-attr]
    assert len(matrix) == 5
    assert {condition for _mask, condition in matrix} == {"pocket_target_residue_atom_condition_indicator"}


def test_checkpoint_compatibility_decision_and_checkpoint_bytes(formal_response: dict[str, object]) -> None:
    decision = formal_response["checkpoint_compatibility_decision"]
    false_keys = (
        "append_to_pocket_one_hot", "change_atom_nf", "change_residue_nf",
        "change_joint_nf", "modify_EGNNDynamics", "modify_ConditionalDDPM",
        "modify_LigandPocketDDPM", "new_base_model_parameter",
        "base_state_dict_key_change", "base_checkpoint_tensor_shape_change",
    )
    assert all(decision[key] is False for key in false_keys)  # type: ignore[index]
    checkpoint = REPO_ROOT / decision["checkpoint_path"]  # type: ignore[index]
    assert checkpoint.stat().st_size == 17861341
    assert _sha(checkpoint.read_bytes()) == design._CHECKPOINT_SHA256


def test_feature_semantics_training_gate_remains_true(formal_response: dict[str, object]) -> None:
    assert formal_response["feature_semantics_audit_required_before_training"] is True
    sidecar = formal_response["adapter_output_contract_records"][1]  # type: ignore[index]
    assert sidecar["output_kind"] == "audit_only_mapping_sidecar_schema"
    assert sidecar["materialized_now"] is False
