"""Pure in-memory design audit for the CovaPIE target-atom adapter V1.

This module deliberately does not implement an adapter, a gate, tensor
materialization, or a model change.  Its private reference entry point binds a
frozen authority bundle to the repository interfaces and reports whether the
existing pocket identity evidence is sufficient for a later implementation.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import shlex
import stat
from pathlib import Path
from typing import Any, Mapping, Sequence


__all__ = ()


_ERROR = "COVAPIE_TARGET_RESIDUE_ATOM_CONDITION_ADAPTER_DESIGN_INVALID"
_VERSION = "covapie_target_residue_atom_condition_adapter_design_v1"
_FIELD = "pocket_target_residue_atom_condition_indicator"
_AUTHORITY_TRANSPORT_SHA256 = (
    "a95ae52e091a7117b241269eebd891f3ee97e3ae4a6b4e14fa441ab6a1ed2096"
)
_AUTHORITY_INTERNAL_SHA256 = (
    "d22073b7c70580d7968533775df42ca64507a6d7911e52efc1b10acd4473f39a"
)
_AUTHORITY_PRODUCTION_SHA256 = (
    "1cf8839382bccfb595a841493a0e22c550578c02f2592dc7481ff67b078d7248"
)
_CHECKPOINT_SHA256 = (
    "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
)
_CHECKPOINT_SIZE = 17861341
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_MAX_BYTES = 16 * 1024 * 1024

CANONICAL_MASK_SEMANTIC_NAMES = (
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
)
CANONICAL_MASK_DISPLAY_ALIASES = ("A", "B", "B2", "B3", "C")

ADAPTER_DESIGN_RESPONSE_FIELDS = (
    "target_residue_atom_condition_adapter_design_version",
    "source_authority_bundle_transport_sha256",
    "source_authority_bundle_sha256",
    "source_authority_production_sha256",
    "source_dataset_module_sha256",
    "source_lightning_module_sha256",
    "source_dynamics_module_sha256",
    "source_conditional_model_sha256",
    "canonical_mask_semantic_names",
    "current_runtime_interface_records",
    "adapter_input_contract_records",
    "adapter_output_contract_records",
    "mapping_audit_records",
    "checkpoint_compatibility_decision",
    "current11_unique_mapping_count",
    "current11_blocked_mapping_count",
    "ready_for_adapter_implementation",
    "recommended_next_step",
    "feature_semantics_audit_required_before_training",
    "adapter_design_response_sha256",
)

MAPPING_AUDIT_RECORD_FIELDS = (
    "sample_index_row_id",
    "pdb_id",
    "source_authority_record_sha256",
    "source_atom_site_id",
    "candidate_identity_source_paths",
    "matched_identity_source_path",
    "matched_identity_source_sha256",
    "identity_match_count",
    "pocket_row_order_binding_observed",
    "proposed_local_pocket_index",
    "mapping_status",
    "mapping_blocking_reasons",
    "mapping_audit_record_sha256",
)

MAPPING_STATUSES = (
    "mapping_ready_unique",
    "blocked_identity_source_missing",
    "blocked_identity_source_ambiguous",
    "blocked_target_atom_missing",
    "blocked_target_atom_ambiguous",
    "blocked_pocket_row_order_unbound",
    "blocked_schema_incomplete",
    "blocked_lineage_mismatch",
)

_SOURCE_AUDIT = (
    ("authority_production", "src/covalent_ext/covapie_current11_target_residue_atom_condition_authority_v1.py", "1cf8839382bccfb595a841493a0e22c550578c02f2592dc7481ff67b078d7248", "frozen_current11_authority_producer"),
    ("dataset_runtime", "dataset.py", "d1c548185521692ca14be062e34d5bea617f8d3c89a22eaef4ddb13a52907c99", "non_names_fields_split_by_lig_substring_else_pocket_mask"),
    ("lightning_runtime", "lightning_modules.py", "2b771068eda19b6f783e12ff483a02ab6ef8264108f3af5e486d3381fb1e7fb6", "model_consumes_only_x_one_hot_size_mask"),
    ("dynamics_runtime", "equivariant_diffusion/dynamics.py", "16b008598de7c61c0b5575e3af02f9b1a9e6697559864df1591314e4b4ec6b9f", "residue_encoder_input_width_is_residue_nf"),
    ("conditional_runtime", "equivariant_diffusion/conditional_model.py", "260bb941e05a3beaa0f1aef7aebba86aa2474d5f5db75637ec1498e3ad0e47b4", "pocket_x_and_one_hot_are_concatenated_without_condition_argument"),
    ("legacy_npz_writer_crossdock", "process_crossdock.py", "760a68011ea6be89ab49edc652d5505954566d8bc05355e9f75106c9f5d728c0", "legacy_crossdocked_npz_writer"),
    ("legacy_npz_writer_bindingmoad", "process_bindingmoad.py", "f3fd5757a66728ca73b93543fe8f1b6ab7e94555c87d2755794b459e95b64c84", "legacy_bindingmoad_npz_writer"),
    ("covalent_npz_writer", "scripts/materialize_training_tensor_npz_v0.py", "7d2a3f835b0a5124df94c9ee63eea8755c212211ff758b12b78c990adcd3b947", "historical_three_sample_full_protein_npz_writer_missing_B3"),
    ("covalent_npz_loader_collate", "src/covalent_ext/npz_dataset.py", "40f9eff875c6a40304f2e8c0ca623dbc3244980903ef6b24c49babf3f2ce84d3", "padded_historical_covalent_loader_not_base_dataset_collate"),
    ("current11_pocket_producer_initial", "src/covalent_ext/covapie_sample_preparation_execution_smoke.py", "0bb67a720595ce8b5211ba56f6913f1d6333828846abba326af8b2f9965eca8b", "produces_three_current11_pocket_atom_tables"),
    ("current11_pocket_producer_expansion", "src/covalent_ext/covapie_independent_group_expansion_batch_sample_preparation_execution_smoke.py", "1b04a32a580ef2dbb18048fe50f609bd188dd89c378d83474a1b32822f1e4932", "produces_eight_current11_pocket_atom_tables"),
    ("current11_sample_index", "data/derived/covalent_small/covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0/unified_sample_index.csv", "d610e7171ad976f16055584582335ce756ed0210e6c15d6b55a1a234bc92c326", "binds_current11_samples_to_pocket_table_paths_not_tensor_row_order"),
    ("historical_full_atom_extractor", "src/covalent_ext/real_covalent_confirmed_candidate_full_atom_extraction_smoke.py", "59c755bfc90be3228f3284f7a8ce66c2dfe21d6ebaa0cb81170f466dc5b65e19", "historical_three_sample_full_atom_tables"),
    ("historical_pocket_extractor", "src/covalent_ext/real_covalent_confirmed_candidate_pocket_extraction_smoke.py", "d9102d92655f2f270f859d06e076ecebccf45c60b8e8a6c9e9a61b7fd664f8e8", "historical_three_sample_pocket_table_preserves_atom_site_id"),
    ("batch_to_diffsbdd_adapter", "src/covalent_ext/diffsbdd_input_adapter.py", "c9fb07156e4643561a8d2902d021cd27637cc4c76d50f80d3cf45d4ab1b42ae6", "flattens_padded_protein_rows_to_pocket_coords_and_one_hot"),
    ("shape_adapter", "src/covalent_ext/diffsbdd_shape_smoke.py", "c6b610dceff763cc6e400fc630bab1d2568b296bbb0a5fd811bf83ea6ad8f265", "maps_adapter_batch_fields_to_pocket_x_and_one_hot"),
    ("forward_shape_adapter", "src/covalent_ext/diffsbdd_forward_shape_smoke.py", "a6aca892e19207fd07e0bf7112999b8599206ccbbcec9be72fdb481b2c4c37b3", "maps_collated_rows_to_diffsbdd_pocket_coords_and_one_hot"),
    ("checkpoint_instantiation_adapter", "src/covalent_ext/checkpoint_compatible_model_instantiation.py", "dfd9957465460f66bc08ac12c264040fae0e2a300eb7359929c780dfa85d3024", "constructs_checkpoint_width_pocket_one_hot"),
    ("pretrained_masked_loss_adapter", "src/covalent_ext/pretrained_masked_loss_smoke.py", "e4ca13b35686287870b648333b4d38ef6911a2df29fe0c43604da8c11831bb7a", "historical_checkpoint_compatible_pocket_conversion"),
    ("b3_pretrained_masked_loss_adapter", "src/covalent_ext/b3_pretrained_masked_loss_smoke.py", "ab0844b27fae768ba5010e3cfd2d87736e35089a30d1aad10b9191cf04883854", "B3_checkpoint_compatible_pocket_conversion"),
    ("real_feature_semantics_adapter", "src/covalent_ext/real_covalent_feature_semantics_audit.py", "c08779e2206a093059a4bb8f959d2a675c39c947373a463301b99d13f99b2d69", "audits_real_pocket_coords_and_one_hot_conversion"),
    ("filtered_runtime_projection", "src/covalent_ext/real_covalent_feature_semantics_audit_debug.py", "f6a7b1cf74a09d84e1acd240b90c3a100be1d0ecb8546def5bde2c98dc4ebca1", "filters_pocket_rows_before_checkpoint_compatible_features"),
    ("noncheckpoint_pocket_filter", "src/covalent_ext/real_covalent_noncheckpoint_pocket_atom_filter_gate.py", "613ca88ace814a637a9c3117d81a173d2b7b50509cc921e65dc8310795c5dec0", "audits_filtered_pocket_node_projection"),
    ("real_pretrained_forward_adapter", "src/covalent_ext/real_covalent_pretrained_forward_loss_smoke.py", "6a7053a413364746b5ce2e818580405001f5883139815deafbeb41f564e90c43", "constructs_real_checkpoint_width_pocket_one_hot"),
    ("base_collate_test", "tests/test_training_tensor_npz_dataloader_v0.py", "ca070e2518a2693dc70a2482a4b678330da631b6cb42b7c10456da082f8ee3bc", "current_covalent_collate_regression"),
    ("batch_adapter_collate_test", "tests/test_training_tensor_batch_adapter_v0.py", "32b475f9dad33597f39fa0e6593bfcc20c06cca93512e18deac66f44957676b8", "batch_adapter_collate_regression"),
    ("model_input_collate_test", "tests/test_training_tensor_model_input_mapping_v0.py", "447e8bac20815cdba4ff925ff2fd5307fb28ed20555dbe558ad253ec02e85604", "model_input_mapping_collate_regression"),
    ("diffsbdd_interface_collate_test", "tests/test_diffsbdd_input_interface_v0.py", "62cee680aaf9f7be8a4ed59aa7992025a8838b64400666f83566b0ce7d717980", "diffsbdd_input_collate_regression"),
    ("diffsbdd_shape_collate_test", "tests/test_diffsbdd_adapter_shape_smoke_v0.py", "bd990a7d51967173f253488a7d25fd46e9f80e49e0cdcee1f2af6d3e88a29b4a", "diffsbdd_shape_collate_regression"),
    ("diffsbdd_forward_collate_test", "tests/test_diffsbdd_single_batch_forward_shape_smoke_v0.py", "59897b681e0c9bf708f0f9511339efaa795acc5b4e424da842d4f91b836fee6e", "diffsbdd_forward_collate_regression"),
    ("feature_mapping_collate_test", "tests/test_real_covalent_feature_mapping_loader_gate_v0.py", "b6542c898dddf73f3fe4c307d373a46c47294d857dffb42f58abdc3e00c80309", "real_feature_mapping_collate_regression"),
    ("training_preflight_collate_test", "tests/test_training_preflight_v0.py", "db811e83e08a84a65db2a8089d43c4502f39d9ea34b2832760de2a7859c0308a", "training_preflight_collate_regression"),
    ("tiny_training_collate_test", "tests/test_tiny_covalent_training_smoke_v0.py", "a8ca7666ded0fed04c6c85c907d2f6bb49d78a092153b9ba65ad970b957db9f2", "historical_tiny_training_collate_regression_not_executed_here"),
    ("historical_full_atom_pocket_test", "tests/test_real_covalent_confirmed_candidate_pocket_extraction_smoke_v0.py", "e5e51373a93aed047d6a2f1e2905a7dd609223fe16aa078dbc4f036a9200612d", "pocket_atom_table_order_and_membership_test"),
    ("checkpoint_compatible_smoke", "src/covalent_ext/checkpoint_compatible_pretrained_load_smoke.py", "9d4312c47675e70837ffcf403645e60748ee7e6561eaf9ee6e2a346f954aeb39", "checkpoint_load_smoke_without_parameter_update"),
    ("checkpoint_compatible_smoke_test", "tests/test_checkpoint_compatible_instantiation_wrapper_v0.py", "6956176d1dd920e69fe7a679a6973b8ecc7c8d89debf9c852b053cf21d950caf", "checkpoint_shape_compatible_wrapper_regression"),
)

_POCKET_TABLE_SHA256S = {
    "data/derived/covalent_small/covapie_sample_preparation_execution_smoke_v0/samples/6BV6_JUG/pocket_atom_table.csv": "8304b32fe3744010e9fed4c0cdbf1036f3550130b6ceeb0b4e72f6cf467bf09a",
    "data/derived/covalent_small/covapie_sample_preparation_execution_smoke_v0/samples/6BV8_JUG/pocket_atom_table.csv": "da421e99a42825bac551884475741bec3bbc15feac2ea7ed7dcbd4e53fcd98a5",
    "data/derived/covalent_small/covapie_sample_preparation_execution_smoke_v0/samples/6BV5_JUG/pocket_atom_table.csv": "1ef54fbbb7d8adf336de6ef29a064a3b689c67a8223240e65986b788a9ad7df8",
    "data/derived/covalent_small/covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/samples/1AEC_E64/pocket_atom_table.csv": "e61676d8f9c67730ea2b38ff7951665d7d7dbe2a6e288621c854f8497883cb97",
    "data/derived/covalent_small/covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/samples/1AIM_ZYA/pocket_atom_table.csv": "e5faa522a02499b47bdc7b3d1bb5cf4d948f343027ce8bd9f897abda8ede2aad",
    "data/derived/covalent_small/covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/samples/1AU3_PCM/pocket_atom_table.csv": "a025544e56c94b95993800cf30877e9171d798b8d58835ca6090ae7fc4365a98",
    "data/derived/covalent_small/covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/samples/1AU4_INP/pocket_atom_table.csv": "16e16364e689fda2d06a84a3ac794bb46d27938de991b968fa28b6da0a7f303f",
    "data/derived/covalent_small/covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/samples/1AYU_INA/pocket_atom_table.csv": "82f2b7e0603d6c7fd07c54a45fd91b0b643932e78f56e10ba2627effd7e69a8a",
    "data/derived/covalent_small/covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/samples/1AYV_IN6/pocket_atom_table.csv": "905e15f4f66cee2c177945c89d3cc53084224e69361fc29968d0b607f7c1ba71",
    "data/derived/covalent_small/covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/samples/1AYW_IN3/pocket_atom_table.csv": "2e5049958a9ebe29a8905c2d6e8b7a24bca4bbdbd742e13f9156319fb42b4ec8",
    "data/derived/covalent_small/covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/samples/1B02_UFP/pocket_atom_table.csv": "0b076e502a8a0e31c1e136b40e347c8815b4d671dce0f74b987c5e536b423b0a",
}


class _DuplicateKeyError(ValueError):
    pass


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")


def _digest_record(record: Mapping[str, Any], fields: Sequence[str], digest_field: str) -> str:
    if tuple(record) != tuple(fields):
        raise ValueError(_ERROR)
    return _sha256(_canonical_json_bytes({key: record[key] for key in fields if key != digest_field}))


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError(key)
        result[key] = value
    return result


def _strict_json(payload: bytes) -> dict[str, Any]:
    if type(payload) is not bytes or not payload or len(payload) >= _MAX_BYTES or payload.endswith((b"\n", b"\r")):
        raise ValueError(_ERROR)
    try:
        result = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique_object)
    except Exception as error:
        raise ValueError(_ERROR) from error
    if type(result) is not dict:
        raise ValueError(_ERROR)
    return result


def _read_regular(repo_root: Path, relative: str, *, maximum: int = _MAX_BYTES) -> bytes:
    try:
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError(_ERROR)
        path = repo_root / relative_path
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise ValueError(_ERROR)
        if metadata.st_size <= 0 or metadata.st_size >= maximum:
            raise ValueError(_ERROR)
        payload = path.read_bytes()
        if len(payload) != metadata.st_size:
            raise ValueError(_ERROR)
        return payload
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    try:
        text = payload.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError(_ERROR)
        rows = list(reader)
        if not rows or any(None in row for row in rows):
            raise ValueError(_ERROR)
        return rows
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _normalise_optional(value: str) -> str:
    return "" if value in {".", "?"} else value


def _mmcif_atom_rows(payload: bytes) -> list[dict[str, str]]:
    try:
        lines = payload.decode("utf-8").splitlines()
        result: list[dict[str, str]] = []
        index = 0
        while index < len(lines):
            if lines[index].strip() != "loop_":
                index += 1
                continue
            index += 1
            headers: list[str] = []
            while index < len(lines) and lines[index].strip().startswith("_"):
                headers.append(lines[index].strip().split()[0])
                index += 1
            if not headers or not all(header.startswith("_atom_site.") for header in headers):
                continue
            tokens: list[str] = []
            while index < len(lines):
                stripped = lines[index].strip()
                if not stripped or stripped.startswith("#"):
                    index += 1
                    if stripped.startswith("#"):
                        break
                    continue
                if stripped == "loop_" or stripped.startswith("_") or stripped.startswith("data_"):
                    break
                tokens.extend(shlex.split(lines[index], posix=True))
                index += 1
            if len(tokens) % len(headers):
                raise ValueError(_ERROR)
            result.extend(dict(zip(headers, tokens[start:start + len(headers)])) for start in range(0, len(tokens), len(headers)))
            break
        if not result:
            raise ValueError(_ERROR)
        return result
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _authority_identity_matches_raw(authority: Mapping[str, Any], raw: Mapping[str, str]) -> bool:
    pairs = (
        ("protein_model_num", "_atom_site.pdbx_PDB_model_num"),
        ("protein_auth_asym_id", "_atom_site.auth_asym_id"),
        ("protein_auth_comp_id", "_atom_site.auth_comp_id"),
        ("protein_auth_seq_id", "_atom_site.auth_seq_id"),
        ("protein_auth_atom_id", "_atom_site.auth_atom_id"),
        ("protein_type_symbol", "_atom_site.type_symbol"),
        ("protein_label_asym_id", "_atom_site.label_asym_id"),
        ("protein_label_comp_id", "_atom_site.label_comp_id"),
        ("protein_label_seq_id", "_atom_site.label_seq_id"),
        ("protein_label_atom_id", "_atom_site.label_atom_id"),
    )
    if any(raw.get(raw_key) != authority.get(authority_key) for authority_key, raw_key in pairs):
        return False
    return (
        _normalise_optional(raw.get("_atom_site.pdbx_PDB_ins_code", "")) == authority["protein_pdbx_PDB_ins_code"]
        and _normalise_optional(raw.get("_atom_site.label_alt_id", "")) == authority["protein_label_alt_id"]
    )


def _authority_identity_matches_pocket(authority: Mapping[str, Any], pocket: Mapping[str, str]) -> bool:
    return all((
        pocket.get("pdb_id") == authority.get("pdb_id"),
        pocket.get("atom_site_id") == authority.get("source_atom_site_id"),
        pocket.get("type_symbol") == authority.get("protein_type_symbol"),
        pocket.get("atom_name") == authority.get("protein_auth_atom_id"),
        pocket.get("residue_name") == authority.get("protein_auth_comp_id"),
        pocket.get("auth_asym_id") == authority.get("protein_auth_asym_id"),
        pocket.get("auth_seq_id") == authority.get("protein_auth_seq_id"),
        pocket.get("label_asym_id") == authority.get("protein_label_asym_id"),
        pocket.get("label_seq_id") == authority.get("protein_label_seq_id"),
    ))


def _mapping_record(
    *, authority: Mapping[str, Any], candidate_path: str, candidate_sha256: str,
    pocket_rows: Sequence[Mapping[str, str]], schema_complete: bool,
    lineage_matches: bool, row_order_bound: bool,
) -> dict[str, Any]:
    matches = [
        (index, row) for index, row in enumerate(pocket_rows)
        if row.get("atom_site_id") == authority.get("source_atom_site_id")
    ] if schema_complete else []
    matched_identity = len(matches) == 1 and _authority_identity_matches_pocket(authority, matches[0][1])
    if not candidate_path:
        status, reasons = "blocked_identity_source_missing", ["pocket_atom_identity_source_missing"]
    elif not schema_complete:
        status, reasons = "blocked_schema_incomplete", ["pocket_atom_identity_schema_incomplete"]
    elif not matches:
        status, reasons = "blocked_target_atom_missing", ["source_atom_site_id_not_found_in_pocket_atom_table"]
    elif len(matches) > 1:
        status, reasons = "blocked_target_atom_ambiguous", ["source_atom_site_id_not_unique_in_pocket_atom_table"]
    elif not matched_identity or not lineage_matches:
        status, reasons = "blocked_lineage_mismatch", ["authority_identity_or_source_lineage_mismatch"]
    elif not row_order_bound:
        status, reasons = "blocked_pocket_row_order_unbound", ["pocket_table_row_order_not_bound_to_pocket_coords_and_pocket_one_hot"]
    else:
        status, reasons = "mapping_ready_unique", []
    record: dict[str, Any] = {
        "sample_index_row_id": authority.get("sample_index_row_id", ""),
        "pdb_id": authority.get("pdb_id", ""),
        "source_authority_record_sha256": authority.get("target_residue_atom_condition_record_sha256", ""),
        "source_atom_site_id": authority.get("source_atom_site_id", ""),
        "candidate_identity_source_paths": [candidate_path] if candidate_path else [],
        "matched_identity_source_path": candidate_path if len(matches) == 1 else "",
        "matched_identity_source_sha256": candidate_sha256 if len(matches) == 1 else "",
        "identity_match_count": len(matches),
        "pocket_row_order_binding_observed": bool(row_order_bound),
        "proposed_local_pocket_index": matches[0][0] if len(matches) == 1 else None,
        "mapping_status": status,
        "mapping_blocking_reasons": reasons,
        "mapping_audit_record_sha256": "",
    }
    record["mapping_audit_record_sha256"] = _digest_record(
        record, MAPPING_AUDIT_RECORD_FIELDS, "mapping_audit_record_sha256"
    )
    return record


def _validate_indicator_contract(
    *, values: Sequence[bool], authority_declares_covalent: bool,
) -> bool:
    """Reference cardinality validator; it creates no tensor or derived view."""
    try:
        if (
            type(values) not in {list, tuple}
            or not values
            or type(authority_declares_covalent) is not bool
            or any(type(value) is not bool for value in values)
        ):
            raise ValueError(_ERROR)
        true_count = sum(values)
        if true_count > 1 or (authority_declares_covalent and true_count != 1):
            raise ValueError(_ERROR)
        if not authority_declares_covalent and true_count != 0:
            raise ValueError(_ERROR)
        return True
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _validate_representation_proposal(
    *, field_name: str, storage_domain: str, numpy_dtype: str,
    torch_dtype: str, sample_shape: str, duplicated_target_xyz: bool,
    append_to_pocket_one_hot: bool,
) -> bool:
    """Fail closed unless the proposal is exactly the accepted V1 field."""
    try:
        accepted = (
            field_name == _FIELD
            and "mask" not in field_name
            and "lig" not in field_name
            and "pocket" in field_name
            and storage_domain == "per_pocket_node"
            and numpy_dtype == "bool"
            and torch_dtype == "torch.bool"
            and sample_shape == "[num_pocket_nodes]"
            and duplicated_target_xyz is False
            and append_to_pocket_one_hot is False
        )
        if not accepted:
            raise ValueError(_ERROR)
        return True
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _validate_mask_contract(mask_names: Sequence[str]) -> bool:
    try:
        if tuple(mask_names) != CANONICAL_MASK_SEMANTIC_NAMES:
            raise ValueError(_ERROR)
        return True
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _validate_authority_bundle(bundle: Mapping[str, Any]) -> list[dict[str, Any]]:
    required = (
        "target_residue_atom_condition_authority_bundle_version",
        "target_residue_atom_condition_records",
        "target_residue_atom_condition_record_count",
        "resolved_authoritative_count",
        "all_records_resolved_authoritative",
        "ready_for_target_residue_atom_condition_adapter_design",
        "feature_semantics_audit_required_before_training",
        "target_residue_atom_condition_authority_bundle_sha256",
    )
    if any(key not in bundle for key in required):
        raise ValueError(_ERROR)
    records = bundle["target_residue_atom_condition_records"]
    if (
        type(records) is not list or len(records) != 11
        or bundle["target_residue_atom_condition_record_count"] != 11
        or bundle["resolved_authoritative_count"] != 11
        or bundle["all_records_resolved_authoritative"] is not True
        or bundle["ready_for_target_residue_atom_condition_adapter_design"] is not True
        or bundle["feature_semantics_audit_required_before_training"] is not True
        or bundle["target_residue_atom_condition_authority_bundle_sha256"] != _AUTHORITY_INTERNAL_SHA256
    ):
        raise ValueError(_ERROR)
    expected_samples = [f"CYS_SG_SAMPLE_INDEX_{index:06d}" for index in range(1, 12)]
    if [record.get("sample_index_row_id") for record in records] != expected_samples:
        raise ValueError(_ERROR)
    for record in records:
        if (
            record.get("condition_authority_status") != "resolved_authoritative"
            or not _SHA256_RE.fullmatch(str(record.get("target_residue_atom_condition_record_sha256", "")))
            or not _SHA256_RE.fullmatch(str(record.get("source_structure_filesystem_sha256", "")))
            or not _SHA256_RE.fullmatch(str(record.get("source_condition_evidence_sha256", "")))
        ):
            raise ValueError(_ERROR)
    unsigned = dict(bundle)
    unsigned.pop("target_residue_atom_condition_authority_bundle_sha256")
    if _sha256(_canonical_json_bytes(unsigned)) != _AUTHORITY_INTERNAL_SHA256:
        raise ValueError(_ERROR)
    return records


def _runtime_records(repo_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for category, path, expected, observation in _SOURCE_AUDIT:
        payload = _read_regular(repo_root, path)
        observed = _sha256(payload)
        if observed != expected:
            raise ValueError(_ERROR)
        records.append({
            "interface_category": category,
            "source_path": path,
            "source_sha256": observed,
            "observed_contract": observation,
        })
    return records


def _formal_mapping_records(repo_root: Path, authority_records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    index_path = "data/derived/covalent_small/covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0/unified_sample_index.csv"
    index_rows = _csv_rows(_read_regular(repo_root, index_path))
    index_by_id = {row.get("sample_index_row_id"): row for row in index_rows}
    if len(index_by_id) != 11:
        raise ValueError(_ERROR)
    output: list[dict[str, Any]] = []
    required_pocket_fields = {
        "pdb_id", "atom_site_id", "type_symbol", "atom_name", "residue_name",
        "auth_asym_id", "auth_seq_id", "label_asym_id", "label_seq_id",
        "source_raw_file",
    }
    for authority in authority_records:
        index_row = index_by_id.get(authority["sample_index_row_id"])
        if index_row is None or index_row.get("pdb_id") != authority["pdb_id"]:
            raise ValueError(_ERROR)
        candidate_path = index_row.get("pocket_atom_table_path", "")
        expected_sha = _POCKET_TABLE_SHA256S.get(candidate_path)
        if expected_sha is None:
            raise ValueError(_ERROR)
        pocket_payload = _read_regular(repo_root, candidate_path)
        pocket_sha = _sha256(pocket_payload)
        if pocket_sha != expected_sha:
            raise ValueError(_ERROR)
        pocket_rows = _csv_rows(pocket_payload)
        schema_complete = required_pocket_fields <= set(pocket_rows[0])
        matches = [row for row in pocket_rows if row.get("atom_site_id") == authority["source_atom_site_id"]]
        lineage_matches = False
        if schema_complete and len(matches) == 1:
            raw_path = matches[0].get("source_raw_file", "")
            raw_payload = _read_regular(repo_root, raw_path, maximum=2 * 1024 * 1024)
            raw_sha_matches = _sha256(raw_payload) == authority["source_structure_filesystem_sha256"]
            raw_matches = [row for row in _mmcif_atom_rows(raw_payload) if row.get("_atom_site.id") == authority["source_atom_site_id"]]
            lineage_matches = (
                raw_sha_matches and len(raw_matches) == 1
                and _authority_identity_matches_raw(authority, raw_matches[0])
            )
        output.append(_mapping_record(
            authority=authority,
            candidate_path=candidate_path,
            candidate_sha256=pocket_sha,
            pocket_rows=pocket_rows,
            schema_complete=schema_complete,
            lineage_matches=lineage_matches,
            row_order_bound=False,
        ))
    return output


def _input_contract_records() -> list[dict[str, Any]]:
    return [
        {"contract": "authority_identity", "selector": "source_atom_site_id", "cross_validation": "all_authority_identity_and_lineage_fields", "coordinate_matching_allowed": False},
        {"contract": "pocket_identity_source", "required": True, "domain": "per_pocket_node", "row_order_binding": "must_equal_pocket_coords_and_pocket_one_hot_node_order"},
        {"contract": "cardinality", "resolved_covalent_true_count": 1, "explicit_noncovalent_true_count": 0, "multiple_true_allowed": False, "first_cys_fallback_allowed": False},
        {"contract": "npz_key_naming", "field_name": _FIELD, "contains_mask": "mask" in _FIELD, "contains_lig": "lig" in _FIELD, "contains_pocket": "pocket" in _FIELD},
    ]


def _output_contract_records() -> list[dict[str, Any]]:
    return [
        {"output_kind": "model_consumable_numeric_field", "field_name": _FIELD, "storage_domain": "per_pocket_node", "numpy_dtype": "bool", "torch_dtype": "torch.bool", "sample_shape": "[num_pocket_nodes]", "batch_shape": "[sum(num_pocket_nodes)]", "lineage_strings_in_tensor": False},
        {"output_kind": "audit_only_mapping_sidecar_schema", "materialized_now": False, "fields": ["sample_index_row_id", "pdb_id", "source_authority_record_sha256", "source_condition_evidence_sha256", "source_structure_filesystem_sha256", "source_atom_site_id", "pocket_atom_identity_source_path", "pocket_atom_identity_source_sha256", "matched_pocket_row_index_local", "match_count", "pocket_row_order_binding_status", "mapping_status", "mapping_blocking_reasons", "mapping_record_sha256"]},
        {"output_kind": "derived_runtime_views", "persisted_in_npz": False, "fields": ["target_condition_present", "target_condition_local_index", "target_condition_flat_index", "target_condition_xyz", "target_condition_atom_one_hot"], "derivation_precondition": "validated_indicator_cardinality"},
        {"output_kind": "coordinate_contract", "target_xyz_duplicated": False, "target_xyz_derivation": "pocket_coords[indicator]", "target_atom_one_hot_duplicated": False, "target_atom_one_hot_derivation": "pocket_one_hot[indicator]"},
        {"output_kind": "representation_decision", "candidate": "append_channel_to_pocket_one_hot", "accepted": False, "reason": "changes_residue_nf_and_checkpoint_parameter_shapes"},
        {"output_kind": "representation_decision", "candidate": "per_sample_local_index", "accepted": False, "reason": "unsupported_scalar_collate_and_fragile_under_node_reordering"},
        {"output_kind": "representation_decision", "candidate": "per_sample_target_xyz", "accepted": False, "reason": "duplicates_coordinates_and_drifts_under_centering_rotation_or_transform"},
        {"output_kind": "representation_decision", "candidate": "coordinate_matching", "accepted": False, "reason": "floating_coordinates_are_not_identity"},
        {"output_kind": "representation_decision", "candidate": "per_pocket_node_indicator", "accepted": True, "reason": "preserves_node_alignment_without_changing_feature_width"},
        {"output_kind": "representation_decision", "candidate": "modify_egnn_state_dict", "accepted": False, "reason": "breaks_base_checkpoint_key_or_tensor_shape_compatibility"},
        {"output_kind": "representation_decision", "candidate": "independent_sidecar_and_gate_path", "accepted": True, "reason": "keeps_lineage_audit_separate_from_model_numeric_tensors"},
    ]


def _checkpoint_decision() -> dict[str, Any]:
    return {
        "append_to_pocket_one_hot": False,
        "change_atom_nf": False,
        "change_residue_nf": False,
        "change_joint_nf": False,
        "modify_EGNNDynamics": False,
        "modify_ConditionalDDPM": False,
        "modify_LigandPocketDDPM": False,
        "new_base_model_parameter": False,
        "base_state_dict_key_change": False,
        "base_checkpoint_tensor_shape_change": False,
        "checkpoint_path": "checkpoints/crossdocked_fullatom_cond.ckpt",
        "checkpoint_size": _CHECKPOINT_SIZE,
        "checkpoint_sha256": _CHECKPOINT_SHA256,
        "extra_batch_key_unconsumed_by_model_changes_parameters": False,
        "future_gate_or_sidecar_requires_separate_design_and_checkpoint_gate": True,
    }


def _reference_design_covapie_target_residue_atom_condition_adapter_v1(
    *, source_authority_bundle: bytes, repo_root: Path,
) -> dict[str, Any]:
    """Return the deterministic Exact20 design response without writing files."""
    try:
        if type(source_authority_bundle) is not bytes or not isinstance(repo_root, Path):
            raise ValueError(_ERROR)
        if _sha256(source_authority_bundle) != _AUTHORITY_TRANSPORT_SHA256:
            raise ValueError(_ERROR)
        authority_bundle = _strict_json(source_authority_bundle)
        authority_records = _validate_authority_bundle(authority_bundle)
        runtime_records = _runtime_records(repo_root)
        checkpoint_payload = _read_regular(repo_root, "checkpoints/crossdocked_fullatom_cond.ckpt", maximum=32 * 1024 * 1024)
        if len(checkpoint_payload) != _CHECKPOINT_SIZE or _sha256(checkpoint_payload) != _CHECKPOINT_SHA256:
            raise ValueError(_ERROR)
        mapping_records = _formal_mapping_records(repo_root, authority_records)
        unique_count = sum(record["mapping_status"] == "mapping_ready_unique" for record in mapping_records)
        blocked_count = len(mapping_records) - unique_count
        ready = unique_count == 11 and blocked_count == 0
        sha_by_path = {record["source_path"]: record["source_sha256"] for record in runtime_records}
        response: dict[str, Any] = {
            "target_residue_atom_condition_adapter_design_version": _VERSION,
            "source_authority_bundle_transport_sha256": _AUTHORITY_TRANSPORT_SHA256,
            "source_authority_bundle_sha256": _AUTHORITY_INTERNAL_SHA256,
            "source_authority_production_sha256": _AUTHORITY_PRODUCTION_SHA256,
            "source_dataset_module_sha256": sha_by_path["dataset.py"],
            "source_lightning_module_sha256": sha_by_path["lightning_modules.py"],
            "source_dynamics_module_sha256": sha_by_path["equivariant_diffusion/dynamics.py"],
            "source_conditional_model_sha256": sha_by_path["equivariant_diffusion/conditional_model.py"],
            "canonical_mask_semantic_names": list(CANONICAL_MASK_SEMANTIC_NAMES),
            "current_runtime_interface_records": runtime_records,
            "adapter_input_contract_records": _input_contract_records(),
            "adapter_output_contract_records": _output_contract_records(),
            "mapping_audit_records": mapping_records,
            "checkpoint_compatibility_decision": _checkpoint_decision(),
            "current11_unique_mapping_count": unique_count,
            "current11_blocked_mapping_count": blocked_count,
            "ready_for_adapter_implementation": ready,
            "recommended_next_step": "implement_covapie_target_residue_atom_condition_adapter_v1" if ready else "implement_covapie_current11_pocket_atom_identity_alignment_v1",
            "feature_semantics_audit_required_before_training": True,
            "adapter_design_response_sha256": "",
        }
        response["adapter_design_response_sha256"] = _digest_record(
            response, ADAPTER_DESIGN_RESPONSE_FIELDS, "adapter_design_response_sha256"
        )
        return response
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
