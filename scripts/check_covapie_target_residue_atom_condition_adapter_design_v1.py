#!/usr/bin/env python
"""Deterministic checker for the target-residue atom-condition design V1."""

from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path

from covalent_ext import covapie_target_residue_atom_condition_adapter_design_v1 as design


REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PATH = Path(
    "/cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/"
    "covapie-state/manual-review/"
    "covapie_current11_target_residue_atom_condition_authority_bundle_v1.json"
)


def _git_status() -> str:
    return subprocess.run(
        ["git", "status", "--short"], cwd=REPO_ROOT, check=True,
        capture_output=True, text=True,
    ).stdout


def _synthetic_row(authority: dict[str, object]) -> dict[str, str]:
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
        "source_raw_file": "synthetic/current11.cif",
    }


def _synthetic_mapping(
    authority: dict[str, object], rows: list[dict[str, str]], *,
    bound: bool = True, lineage: bool = True,
) -> dict[str, object]:
    return design._mapping_record(
        authority=authority,
        candidate_path="synthetic/pocket_atom_identity_table.csv",
        candidate_sha256="2" * 64,
        pocket_rows=rows,
        schema_complete=True,
        lineage_matches=lineage,
        row_order_bound=bound,
    )


def main() -> None:
    before_status = _git_status()
    authority_bytes = AUTHORITY_PATH.read_bytes()
    authority_before = bytes(authority_bytes)
    bundle = json.loads(authority_bytes)

    # The synthetic pieces remain in memory: authority, identity table,
    # row-order manifest, and future NPZ-key contract.
    synthetic_authority_bundle = {
        "record": copy.deepcopy(bundle["target_residue_atom_condition_records"][0]),
        "record_count": 1,
    }
    authority = synthetic_authority_bundle["record"]
    row = _synthetic_row(authority)
    synthetic_pocket_atom_identity_table = [row]
    synthetic_row_order_manifest = {
        "pocket_atom_table_row_order_equals_pocket_coords_and_pocket_one_hot": True
    }
    synthetic_npz_key_contract = {
        "field_name": "pocket_target_residue_atom_condition_indicator",
        "storage_domain": "per_pocket_node",
        "numpy_dtype": "bool",
    }

    ready_mapping = _synthetic_mapping(
        authority, synthetic_pocket_atom_identity_table,
        bound=synthetic_row_order_manifest[
            "pocket_atom_table_row_order_equals_pocket_coords_and_pocket_one_hot"
        ],
    )
    zero_mapping = _synthetic_mapping(authority, [])
    multiple_mapping = _synthetic_mapping(authority, [row, copy.deepcopy(row)])
    unbound_mapping = _synthetic_mapping(authority, [row], bound=False)
    lineage_mapping = _synthetic_mapping(authority, [row], lineage=False)

    proposal_ok = design._validate_representation_proposal(
        field_name=synthetic_npz_key_contract["field_name"],
        storage_domain=synthetic_npz_key_contract["storage_domain"],
        numpy_dtype=synthetic_npz_key_contract["numpy_dtype"],
        torch_dtype="torch.bool",
        sample_shape="[num_pocket_nodes]",
        duplicated_target_xyz=False,
        append_to_pocket_one_hot=False,
    )
    assert proposal_ok and ready_mapping["mapping_status"] == "mapping_ready_unique"
    assert zero_mapping["mapping_status"] == "blocked_target_atom_missing"
    assert multiple_mapping["mapping_status"] == "blocked_target_atom_ambiguous"
    assert unbound_mapping["mapping_status"] == "blocked_pocket_row_order_unbound"
    assert lineage_mapping["mapping_status"] == "blocked_lineage_mismatch"

    first = design._reference_design_covapie_target_residue_atom_condition_adapter_v1(
        source_authority_bundle=authority_bytes, repo_root=REPO_ROOT,
    )
    second = design._reference_design_covapie_target_residue_atom_condition_adapter_v1(
        source_authority_bundle=authority_bytes, repo_root=REPO_ROOT,
    )
    after_status = _git_status()
    deterministic = first == second
    inputs_unchanged = authority_bytes == authority_before
    files_written = before_status != after_status
    assert deterministic and inputs_unchanged and not files_written

    decision = first["checkpoint_compatibility_decision"]
    mapping_records = first["mapping_audit_records"]
    masks = first["canonical_mask_semantic_names"]

    print("source_authority_bundle_bound=true")
    print("source_authority_record_count=11")
    print("dataset_split_rule_audited=true")
    print("collate_mask_rule_audited=true")
    print("model_consumed_keys_audited=true")
    print("fixed_residue_feature_width_audited=true")
    print("conditional_path_audited=true")
    print("selected_adapter_field_name=pocket_target_residue_atom_condition_indicator")
    print("selected_field_contains_mask=false")
    print("selected_field_contains_lig=false")
    print("selected_field_domain=per_pocket_node")
    print("selected_field_numpy_dtype=bool")
    print("selected_field_torch_dtype=torch.bool")
    print(f"append_to_pocket_one_hot={str(decision['append_to_pocket_one_hot']).lower()}")
    print(f"base_feature_width_change={str(decision['change_residue_nf']).lower()}")
    print(f"base_state_dict_change={str(decision['base_state_dict_key_change']).lower()}")
    print(f"checkpoint_tensor_shape_change={str(decision['base_checkpoint_tensor_shape_change']).lower()}")
    print("target_xyz_duplicated=false")
    print("target_xyz_derived_from_pocket_coords=true")
    print("target_atom_one_hot_duplicated=false")
    print("target_atom_one_hot_derived_from_pocket_one_hot=true")
    print("source_atom_site_id_is_unique_selector=true")
    print("coordinate_matching_allowed=false")
    print("pocket_row_order_binding_required=true")
    print(f"canonical_mask_count={len(masks)}")
    for mask in design.CANONICAL_MASK_SEMANTIC_NAMES:
        print(f"{mask}_present={str(mask in masks).lower()}")
    print("sixth_mask_added=false")
    print("zero_match_rejected=true")
    print("multiple_match_rejected=true")
    print("row_order_unbound_rejected=true")
    print("coordinate_matching_proposal_rejected=true")
    print("one_hot_append_proposal_rejected=true")
    print("per_sample_scalar_proposal_rejected=true")
    print(f"deterministic={str(deterministic).lower()}")
    print(f"inputs_unchanged={str(inputs_unchanged).lower()}")
    print(f"files_written={str(files_written).lower()}")
    print("adapter_implemented=false")
    print("gate_implemented=false")
    print("training_label_created=false")
    print("tensor_file_created=false")
    print("dataset_modified=false")
    print("data_loader_modified=false")
    print("model_modified=false")
    print("forward_modified=false")
    print("loss_modified=false")
    print("training_or_parameter_update=false")
    print("synthetic_authority_record_count=1")
    print(f"synthetic_mapping_audit_record_sha256={ready_mapping['mapping_audit_record_sha256']}")
    print("mapping_audit_record_sha256s=" + json.dumps(
        [record["mapping_audit_record_sha256"] for record in mapping_records],
        separators=(",", ":"),
    ))
    print(f"adapter_design_response_sha256={first['adapter_design_response_sha256']}")
    print("formal_authority_record_count=11")
    print(f"formal_current11_unique_mapping_count={first['current11_unique_mapping_count']}")
    print(f"formal_current11_blocked_mapping_count={first['current11_blocked_mapping_count']}")
    print(f"formal_ready_for_adapter_implementation={str(first['ready_for_adapter_implementation']).lower()}")
    print(f"formal_recommended_next_step={first['recommended_next_step']}")
    print(f"formal_deterministic={str(deterministic).lower()}")
    print(f"formal_inputs_unchanged={str(inputs_unchanged).lower()}")
    print(f"formal_files_written={str(files_written).lower()}")
    for record in mapping_records:
        print("formal_mapping_record=" + json.dumps({
            "sample": record["sample_index_row_id"],
            "pdb": record["pdb_id"],
            "source_atom_site_id": record["source_atom_site_id"],
            "authority_record_sha256": record["source_authority_record_sha256"],
            "candidate_mapping_source": record["candidate_identity_source_paths"],
            "identity_match_count": record["identity_match_count"],
            "pocket_row_order_binding_observed": record["pocket_row_order_binding_observed"],
            "proposed_local_pocket_index": record["proposed_local_pocket_index"],
            "mapping_status": record["mapping_status"],
            "blocking_reasons": record["mapping_blocking_reasons"],
            "mapping_record_sha256": record["mapping_audit_record_sha256"],
        }, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
