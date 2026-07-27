#!/usr/bin/env python3
"""Independent checker for the CovaPIE atom-pair encoding Exact10."""

from __future__ import annotations

import csv
import hashlib
import importlib
import inspect
import io
import json
import subprocess
import sys
from dataclasses import fields, replace
from pathlib import Path
from typing import get_type_hints


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

BASE_COMMIT = "6f04eb7036aa926e433a02de3e244412af038800"
BASE_PARENT = "976da60a5af7b7ba71597c1202955a45db6b6cf1"
BASE_TREE = "b629b9082cf8d8ef82c00f9af1a9524dead7a6a4"
BASE_SUBJECT = (
    "add CovaPIE covalent bond atom-pair current-semantics audit v1"
)
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE covalent bond atom-pair encoding contract v1"
)
STAGE = "covapie_covalent_bond_atom_pair_encoding_contract_design_gate_v1"
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
PRODUCTION = Path(
    "src/covalent_ext/"
    "covapie_covalent_bond_atom_pair_encoding_contract_design_gate_v1.py"
)
TEST = Path(
    "tests/"
    "test_covapie_covalent_bond_atom_pair_encoding_contract_design_gate_v1.py"
)
CHECKER = Path(
    "scripts/"
    "check_covapie_covalent_bond_atom_pair_encoding_contract_design_gate_v1.py"
)
DOC = Path(
    "docs/"
    "covapie_covalent_bond_atom_pair_encoding_contract_design_gate_v1_summary.md"
)
PUBLIC = "covapie_covalent_bond_atom_pair_encoding_public_contract.csv"
LOCATOR = "covapie_covalent_bond_atom_locator_schema_contract.csv"
POLICY = "covapie_covalent_bond_atom_pair_policy_matrix.csv"
LEGACY = "covapie_covalent_bond_atom_pair_legacy_compatibility_matrix.csv"
ISSUE = "covapie_covalent_bond_atom_pair_issue_readiness_inventory.csv"
MANIFEST = "covapie_covalent_bond_atom_pair_encoding_contract_manifest.json"
FILES = (PUBLIC, LOCATOR, POLICY, LEGACY, ISSUE, MANIFEST)
EXACT10 = (
    PRODUCTION,
    TEST,
    CHECKER,
    DOC,
    *(OUTPUT_ROOT / name for name in FILES),
)

PRE_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_covalent_bond_atom_pair_current_semantics_and_downstream_"
    "consumers_audit_gate_v1"
)
PRE_MANIFEST = PRE_ROOT / (
    "covapie_covalent_bond_atom_pair_current_semantics_and_downstream_"
    "consumers_audit_manifest.json"
)
PRE_UNRESOLVED = PRE_ROOT / (
    "covapie_covalent_bond_atom_pair_unresolved_semantics_inventory.csv"
)
PRE_REPRESENTATION = PRE_ROOT / (
    "covapie_covalent_bond_atom_pair_current_representation_audit.csv"
)
PRE_ISSUE = PRE_ROOT / (
    "covapie_covalent_bond_atom_pair_issue_readiness_inventory.csv"
)
PREDECESSORS = {
    Path(
        "src/covalent_ext/"
        "covapie_covalent_bond_atom_pair_current_semantics_and_downstream_"
        "consumers_audit_gate_v1.py"
    ): "f905174e6bb471475bc34ce6ff3d35034755daec913da2cc81bfcf94b5112112",
    PRE_MANIFEST: "334a0dfe5b37b41f134c9a66ad9b0237431e0798f926b32bda4101a8e8f0571c",
    PRE_UNRESOLVED: (
        "00722f0c2370d458cdcac7d50c18914b4f36a393e237cf2ecc40f81965bca428"
    ),
    PRE_REPRESENTATION: (
        "f63a5a8b0ed1d7ad0284a89826325f0d429ab33b202a5f2e468ae8a370eb1968"
    ),
    PRE_ISSUE: (
        "fb4d2dfae7ffc056e3856c94e2f5a135d468eb3801144f9a698f95d9b812ace7"
    ),
}

FINAL_SCHEMA = Path(
    "data/derived/covalent_small/covapie_final_dataset_design_gate_v0/"
    "covapie_final_dataset_schema_contract.csv"
)
FINAL_INDEX = Path(
    "data/derived/covalent_small/"
    "covapie_final_dataset_materialization_smoke_v0/final_dataset_index.csv"
)
TENSOR_BLOCKERS = Path(
    "data/derived/covalent_small/"
    "covapie_feature_semantics_tensorization_audit_gate_v0/"
    "covapie_label_tensorization_blocker_audit.csv"
)
DATALOADER_CONTRACT = Path(
    "data/derived/covalent_small/covapie_actual_dataloader_design_gate_v0/"
    "covapie_actual_dataloader_tensorization_input_contract.csv"
)
INDEX_EVIDENCE = {
    FINAL_SCHEMA: "2ea572efb4d9df1a168ba6b056ffa14593315ac148d589f86a5ea8f607c2469c",
    FINAL_INDEX: "c4c31888cb0f7c148b00656ccf22ab68fab842fcdafdee049b2f420eddc1302d",
    PRE_MANIFEST: "334a0dfe5b37b41f134c9a66ad9b0237431e0798f926b32bda4101a8e8f0571c",
    PRE_UNRESOLVED: "00722f0c2370d458cdcac7d50c18914b4f36a393e237cf2ecc40f81965bca428",
    TENSOR_BLOCKERS: "ce1ab5c8024b360ef72c95718898e4c052a5fd0c8a3d07c76bf92f50db64ae0a",
    DATALOADER_CONTRACT: "b88b7012cffe4d6689e14f63732e5edea64c28e22fb1b3e1c6e53cd25e9ba5eb",
}
INDEX_SELECTORS = (
    "final_dataset_schema:required pocket_atom_table_path and ligand_atom_table_path",
    "final_dataset_index:11 nonempty pocket_atom_table_path and ligand_atom_table_path values",
    "current_audit_manifest:no pair index/dataloader/forward/loss/training target",
    "unresolved_semantics:no current protein/pocket/ligand mapping; row order deferred",
    "tensorization_blockers:pair label, collate, loss, and training targets blocked",
    "dataloader_tensorization_contract:pocket/ligand sources present; pair label blocked; no pair-index contract",
)

OUTPUT_SHA256 = {
    PUBLIC: "f5094813d3c705dbd0bd083669c83ed80656720caa7a9a35926a1a82f7906850",
    LOCATOR: "9b8e1beb339b228cacb5d1eb19e6acc34c40da97c91120e667a01843e1af0544",
    POLICY: "cf9cc674ef4b23f6437cf79dd4685aee5c478b1b1367662787da44194bedf26b",
    LEGACY: "115065856229043320fb86a25eca8619ff37af8580296d85fa414baba581835f",
    ISSUE: "fb4d2dfae7ffc056e3856c94e2f5a135d468eb3801144f9a698f95d9b812ace7",
    MANIFEST: "8f0d80f7b54dd9635a1cdb1f6bd3ca0069a6c09059eeff806a6885e89a460920",
}
PRODUCTION_SHA256 = (
    "dd428bf4993dc24ed11ec54d0163c42ad161d1203433e219acba29b602a2e5ea"
)
LOCATOR_FIELDS = (
    "locator_schema_version",
    "entity_role",
    "event_id",
    "pdb_id",
    "model_id",
    "auth_asym_id",
    "auth_seq_id",
    "insertion_code",
    "label_asym_id",
    "label_seq_id",
    "comp_id",
    "atom_name",
    "altloc",
)
RECORD_FIELDS = (
    "pair_record_schema_version",
    "residue_atom_locator",
    "ligand_atom_locator",
    "explicit_bond_authority_class",
    "explicit_bond_provenance_id",
)
INDEX_EVIDENCE_FIELDS = (
    "final_dataset_pocket_atom_table_reference_present",
    "final_dataset_ligand_atom_table_reference_present",
    "current_pair_tensor_index_contract_present",
    "conflicting_existing_index_space_contract_present",
    "pair_tensorization_currently_blocked",
    "row_order_validation_deferred_to_contract_validation",
    "compatible",
    "evidence_paths",
)
PAIR_FIELDS = (
    "schema_version",
    "outcome",
    "canonical_encoding_kind",
    "pair_role_semantics",
    "explicit_bond_authority_required",
    "accepted_explicit_bond_authority_classes",
    "distance_only_inference_forbidden",
    "positive_pair_cardinality_policy",
    "residue_candidate_scope",
    "ligand_candidate_scope",
    "residue_model_index_space",
    "ligand_model_index_space",
    "model_index_base",
    "mapping_cardinality_policy",
    "missing_mapping_policy",
    "ambiguous_mapping_policy",
    "duplicate_evidence_policy",
    "conflicting_pair_policy",
    "zero_pair_policy",
    "multi_pair_policy",
    "legacy_string_role",
    "canonical_masks_share_same_pair_identity",
    "pair_tensor_materialized",
    "pair_tensor_shape_defined",
    "pair_loss_mask_defined",
    "atom_pair_issue_resolved",
    "ready_for_contract_validation",
    "ready_for_tensorization",
    "ready_for_training",
    "recommended_next_step",
)
ROLE_VOCABULARY = ("target_residue_atom", "ligand_atom")
AUTHORITY_VOCABULARY = (
    "validated_struct_conn",
    "explicit_curated_covalent_annotation",
)
MASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
LEGACY_VALUES = (
    "SG--C17",
    "SG--C2",
    "SG--C21",
    "SG--C22",
    "SG--C6",
    "SG--CAG",
    "SG--CM",
)
POLICY_CASES = (
    "valid_explicit_single_pair",
    "distance_only_candidate",
    "zero_pair",
    "exact_duplicate_evidence",
    "conflicting_duplicate",
    "multiple_distinct_pairs",
    "missing_residue_locator",
    "missing_ligand_locator",
    "ambiguous_residue_mapping",
    "ambiguous_ligand_mapping",
    "target_residue_mismatch",
    "ligand_instance_mismatch",
    "legacy_string_mismatch",
    "legacy_string_only",
    "non_zero_based_requested_index",
    "row_order_drift",
    "altloc_ambiguity",
    "model_ambiguity",
    "insertion_code_ambiguity",
    "unsupported_explicit_authority",
    "missing_explicit_authority_provenance",
    "residue_role_mismatch",
    "ligand_role_mismatch",
    "event_identity_mismatch",
    "pdb_identity_mismatch",
    "model_identity_mismatch",
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _git(*args: str) -> str:
    result = subprocess.run(
        ("git", *args),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(
            f"git {' '.join(args)} failed: "
            f"{result.stderr.decode('utf-8', errors='replace')}"
        )
    return result.stdout.decode("utf-8").strip()


def _rows(payload: bytes) -> tuple[dict[str, str], ...]:
    return tuple(
        csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    )


def _base_blob(relative: Path) -> bytes:
    result = subprocess.run(
        ("git", "show", f"{BASE_COMMIT}:{relative.as_posix()}"),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(f"committed BASE evidence missing: {relative}")
    return result.stdout


def _verify_base_and_predecessors() -> None:
    observed = _git(
        "show", "-s", "--format=%H%n%P%n%T%n%s", BASE_COMMIT
    ).splitlines()
    _assert(
        observed == [BASE_COMMIT, BASE_PARENT, BASE_TREE, BASE_SUBJECT],
        "BASE identity drift",
    )
    for relative, expected in PREDECESSORS.items():
        local_payload = (ROOT / relative).read_bytes()
        _assert(
            _sha256(local_payload) == expected,
            f"predecessor SHA drift: {relative}",
        )
        _assert(
            _base_blob(relative) == local_payload,
            f"predecessor is not byte-identical to BASE: {relative}",
        )
    manifest = json.loads((ROOT / PRE_MANIFEST).read_bytes())
    expected = {
        "outcome": "audited",
        "current_source_lineage_verified": True,
        "producer_projection_verified": True,
        "record_conflict_present": False,
        "producer_conflict_present": False,
        "explicit_bond_authority_verified": True,
        "distance_only_inference_used": False,
        "current_pair_is_metadata_string": True,
        "current_pair_is_tensor_index_pair": False,
        "ready_for_encoding_contract_design": True,
        "ready_for_training": False,
    }
    for key, value in expected.items():
        _assert(
            manifest.get(key) == value,
            f"predecessor readiness drift: {key}",
        )


def _verify_index_space_evidence(gate: object):
    for relative, expected in INDEX_EVIDENCE.items():
        payload = (ROOT / relative).read_bytes()
        _assert(
            _sha256(payload) == expected,
            f"index evidence SHA drift: {relative}",
        )
        _assert(
            _base_blob(relative) == payload,
            f"index evidence is not committed BASE content: {relative}",
        )

    schema = _rows((ROOT / FINAL_SCHEMA).read_bytes())
    schema_by_field = {row["final_dataset_field"]: row for row in schema}
    for field_name in ("pocket_atom_table_path", "ligand_atom_table_path"):
        _assert(
            schema_by_field[field_name]["schema_contract_passed"] == "True",
            f"final schema boundary missing: {field_name}",
        )
    final_rows = _rows((ROOT / FINAL_INDEX).read_bytes())
    _assert(len(final_rows) == 11, "final dataset record count drift")
    _assert(
        all(
            row["pocket_atom_table_path"]
            and row["ligand_atom_table_path"]
            for row in final_rows
        ),
        "final dataset pocket/ligand references are incomplete",
    )

    audit = json.loads((ROOT / PRE_MANIFEST).read_bytes())
    audit_false = (
        "current_pair_is_tensor_index_pair",
        "future_index_mapping_defined",
        "current_dataloader_consumer_present",
        "current_model_forward_consumer_present",
        "current_loss_consumer_present",
        "current_training_target_tensor_present",
    )
    _assert(
        all(audit[key] is False for key in audit_false),
        "current audit unexpectedly declares pair-index consumption",
    )
    unresolved = {
        row["semantics_item"]: row
        for row in _rows((ROOT / PRE_UNRESOLVED).read_bytes())
    }
    for item in (
        "protein full-atom table row mapping",
        "pocket atom table row mapping",
        "ligand atom table row mapping",
        "atom-table row ordering stability",
    ):
        row = unresolved[item]
        _assert(
            row["currently_formally_defined"] == "false"
            and row["decision_made_current_audit"] == "false"
            and row["deferred_to_next_contract"] == "true"
            and row["verified"] == "true",
            f"mapping deferral drift: {item}",
        )

    blockers = {
        row["label_blocker_item"]: row
        for row in _rows((ROOT / TENSOR_BLOCKERS).read_bytes())
    }
    for item in (
        "covalent_atom_pair_label_not_training_final",
        "batch_collate_for_labels_blocked",
        "loss_integration_blocked",
        "training_targets_blocked",
    ):
        row = blockers[item]
        _assert(
            row["current_tensorization_status"] == "blocked"
            and row["blocks_training"] == "True"
            and row["label_blocker_audit_passed"] == "True",
            f"tensorization blocker drift: {item}",
        )
    dataloader = {
        row["tensorization_item"]: row
        for row in _rows((ROOT / DATALOADER_CONTRACT).read_bytes())
    }
    _assert(
        dataloader["protein_xyz_from_derived_atom_table"][
            "source_or_policy"
        ]
        == "protein_pocket_atom_table_path",
        "pocket model-input boundary drift",
    )
    _assert(
        dataloader["ligand_xyz_from_derived_atom_table"][
            "source_or_policy"
        ]
        == "ligand_atom_table_path",
        "ligand model-input boundary drift",
    )
    _assert(
        dataloader["covalent_atom_pair_label_blocked"][
            "current_step_status"
        ]
        == "blocked_by_feature_semantics",
        "pair tensorization contract is not blocked",
    )
    conflicting_keys = {
        "covalent_atom_pair_index",
        "protein_atom_table_row_index",
        "full_protein_atom_table_row_index",
        "one_based_pocket_atom_table_row_index",
        "one_based_ligand_atom_table_row_index",
    }
    _assert(
        not (
            {
                row["future_tensor_or_metadata_key"]
                for row in dataloader.values()
            }
            & conflicting_keys
        ),
        "conflicting existing index-space contract found",
    )

    evidence = (
        gate.derive_covapie_model_input_index_space_compatibility_evidence_v1(
            ROOT
        )
    )
    _assert(type(evidence) is gate.ModelInputIndexSpaceCompatibilityEvidence, "derived evidence exact type drift")
    _assert(tuple(field.name for field in fields(type(evidence))) == INDEX_EVIDENCE_FIELDS, "derived evidence fields drift")
    _assert(evidence.compatible is True, "derived index evidence is not compatible")
    _assert(evidence.current_pair_tensor_index_contract_present is False, "derived pair-index state drift")
    _assert(evidence.conflicting_existing_index_space_contract_present is False, "derived conflict state drift")
    _assert(evidence.pair_tensorization_currently_blocked is True, "derived blocker state drift")
    _assert(evidence.row_order_validation_deferred_to_contract_validation is True, "derived row-order state drift")
    _assert(
        evidence.evidence_paths == tuple(path.as_posix() for path in INDEX_EVIDENCE),
        "derived evidence paths drift",
    )
    source = inspect.getsource(
        gate.build_covapie_covalent_bond_atom_pair_encoding_contract_artifacts_v1
    )
    _assert("model_input_index_spaces_compatible=True" not in source, "builder contains literal compatibility shortcut")
    _assert("compatible=True" not in source, "builder contains literal compatible shortcut")
    _assert(
        "derive_covapie_model_input_index_space_compatibility_evidence_v1"
        in source
        and "model_input_index_space_compatibility_evidence="
        in source,
        "builder does not use derived compatibility evidence",
    )
    return evidence


def _verify_api(gate: object) -> None:
    locator = gate.CovalentAtomLocatorContractDesign
    record_type = gate.CovalentBondAtomPairCanonicalRecordDesign
    contract_type = gate.CovalentBondAtomPairEncodingContractDesign
    evidence_type = gate.ModelInputIndexSpaceCompatibilityEvidence
    _assert(tuple(field.name for field in fields(locator)) == LOCATOR_FIELDS, "locator fields drift")
    _assert(tuple(field.name for field in fields(record_type)) == RECORD_FIELDS, "canonical record fields drift")
    _assert(tuple(field.name for field in fields(contract_type)) == PAIR_FIELDS, "pair fields drift")
    _assert(tuple(field.name for field in fields(evidence_type)) == INDEX_EVIDENCE_FIELDS, "index evidence fields drift")
    locator_hints = get_type_hints(locator)
    record_hints = get_type_hints(record_type)
    pair_hints = get_type_hints(contract_type)
    evidence_hints = get_type_hints(evidence_type)
    _assert(tuple(locator_hints) == LOCATOR_FIELDS, "locator type order drift")
    _assert(all(value is str for value in locator_hints.values()), "locator types drift")
    _assert(
        tuple(record_hints.values())
        == (str, locator, locator, str, str),
        "canonical record types drift",
    )
    expected_pair_types = (
        str, str, str, str, bool, tuple[str, ...], bool, str, str, str,
        str, str, int, str, str, str, str, str, str, str, str, bool,
        bool, bool, bool, bool, bool, bool, bool, str,
    )
    _assert(tuple(pair_hints.values()) == expected_pair_types, "pair types drift")
    _assert(
        tuple(evidence_hints.values())
        == (bool, bool, bool, bool, bool, bool, bool, tuple[str, ...]),
        "index evidence types drift",
    )
    _assert(locator.__dataclass_params__.frozen is True, "locator is not frozen")
    _assert(record_type.__dataclass_params__.frozen is True, "canonical record is not frozen")
    _assert(contract_type.__dataclass_params__.frozen is True, "pair contract is not frozen")
    _assert(evidence_type.__dataclass_params__.frozen is True, "index evidence is not frozen")
    _assert(gate.ROLE_VOCABULARY == ROLE_VOCABULARY, "role vocabulary drift")
    _assert(gate.AUTHORITY_VOCABULARY == AUTHORITY_VOCABULARY, "authority vocabulary drift")
    _assert(gate.CANONICAL_MASKS == MASKS, "mask vocabulary drift")

    good = gate.CovalentAtomLocatorContractDesign(
        "covapie_covalent_atom_locator_v1",
        "target_residue_atom",
        "EVENT",
        "1ABC",
        "",
        "A",
        "10",
        "",
        "",
        "",
        "CYS",
        "SG",
        "",
    )
    _assert(gate.validate_covapie_covalent_atom_locator_contract_design_v1(good), "valid locator rejected")
    _assert(
        not gate.validate_covapie_covalent_atom_locator_contract_design_v1(
            locator(**{**good.__dict__, "event_id": ""})
        ),
        "missing locator accepted",
    )
    ligand = locator(
        **{
            **good.__dict__,
            "entity_role": "ligand_atom",
            "auth_asym_id": "",
            "auth_seq_id": "",
            "comp_id": "LIG",
            "atom_name": "C1",
        }
    )
    record = record_type(
        "covapie_covalent_bond_atom_pair_canonical_record_v1",
        good,
        ligand,
        "validated_struct_conn",
        "struct_conn:covale1",
    )
    _assert(
        gate.validate_covapie_covalent_bond_atom_pair_canonical_record_design_v1(
            record
        ),
        "valid canonical record rejected",
    )
    _assert(
        gate.project_covapie_legacy_atom_name_pair_v1(record) == "SG--C1",
        "legacy projection drift",
    )
    invalid_records = (
        replace(record, pair_record_schema_version="wrong"),
        replace(record, residue_atom_locator=replace(good, entity_role="ligand_atom")),
        replace(record, ligand_atom_locator=replace(ligand, entity_role="target_residue_atom")),
        replace(record, ligand_atom_locator=replace(ligand, event_id="OTHER")),
        replace(record, ligand_atom_locator=replace(ligand, pdb_id="2XYZ")),
        replace(record, ligand_atom_locator=replace(ligand, model_id="2")),
        replace(record, explicit_bond_authority_class="distance"),
        replace(record, explicit_bond_provenance_id=""),
        replace(record, residue_atom_locator=replace(good, atom_name="")),
        replace(record, ligand_atom_locator=replace(ligand, atom_name="")),
    )
    for invalid_record in invalid_records:
        _assert(
            not gate.validate_covapie_covalent_bond_atom_pair_canonical_record_design_v1(
                invalid_record
            ),
            "invalid canonical record accepted",
        )
        try:
            gate.project_covapie_legacy_atom_name_pair_v1(invalid_record)
        except ValueError:
            pass
        else:
            raise ValueError("invalid canonical record projected to legacy")

    evidence = _verify_index_space_evidence(gate)
    contract = gate.design_covapie_covalent_bond_atom_pair_encoding_contract_v1(
        current_semantics_audit_precondition_verified=True,
        model_input_index_space_compatibility_evidence=evidence,
    )
    invalid = gate.design_covapie_covalent_bond_atom_pair_encoding_contract_v1(
        current_semantics_audit_precondition_verified=False,
        model_input_index_space_compatibility_evidence=evidence,
    )
    conflicting = gate.design_covapie_covalent_bond_atom_pair_encoding_contract_v1(
        current_semantics_audit_precondition_verified=True,
        model_input_index_space_compatibility_evidence=replace(
            evidence,
            conflicting_existing_index_space_contract_present=True,
        ),
    )
    indexed = gate.design_covapie_covalent_bond_atom_pair_encoding_contract_v1(
        current_semantics_audit_precondition_verified=True,
        model_input_index_space_compatibility_evidence=replace(
            evidence,
            current_pair_tensor_index_contract_present=True,
        ),
    )
    _assert(contract.outcome == "frozen", "contract did not freeze")
    _assert(contract.canonical_encoding_kind == "structured_role_labeled_record", "canonical kind drift")
    _assert(contract.accepted_explicit_bond_authority_classes == AUTHORITY_VOCABULARY, "authority contract drift")
    _assert(contract.ready_for_contract_validation is True, "validation readiness drift")
    _assert(contract.ready_for_tensorization is False, "tensorization readiness drift")
    _assert(contract.ready_for_training is False, "training readiness drift")
    _assert(invalid.outcome == "invalid" and not invalid.ready_for_contract_validation, "design failure did not fail closed")
    _assert(conflicting.outcome == "invalid", "index conflict did not fail closed")
    _assert(indexed.outcome == "invalid", "existing pair-index contract did not fail closed")
    serialized = gate.serialize_covapie_covalent_bond_atom_pair_encoding_contract_design_v1(contract)
    _assert(serialized == gate.serialize_covapie_covalent_bond_atom_pair_encoding_contract_design_v1(contract), "serialization drift")


def _verify_evidence(gate: object) -> dict[str, object]:
    _assert(
        _sha256((ROOT / PRODUCTION).read_bytes()) == PRODUCTION_SHA256,
        "production source SHA drift",
    )
    observed_files = tuple(path.name for path in (ROOT / OUTPUT_ROOT).iterdir())
    _assert(
        len(observed_files) == len(FILES) and set(observed_files) == set(FILES),
        "output file set drift",
    )
    actual = {name: (ROOT / OUTPUT_ROOT / name).read_bytes() for name in FILES}
    for name, expected in OUTPUT_SHA256.items():
        _assert(_sha256(actual[name]) == expected, f"output SHA drift: {name}")
    builds = tuple(
        gate.build_covapie_covalent_bond_atom_pair_encoding_contract_artifacts_v1(
            ROOT
        )
        for _ in range(3)
    )
    _assert(builds[0] == builds[1] == builds[2], "three builds differ")
    _assert(
        all(actual[name] == builds[0][name] for name in FILES),
        "materialized evidence differs from deterministic build",
    )

    public = _rows(actual[PUBLIC])
    _assert(len(public) == 26, "public row count drift")
    _assert(
        tuple(public[0]) == (
            "contract_area", "contract_item", "expected_value",
            "observed_value", "source_or_rationale", "verified",
        ),
        "public header drift",
    )
    _assert(all(row["verified"] == "true" for row in public), "public verification drift")
    public_items = {row["contract_item"]: row for row in public}
    _assert(public_items["canonical_encoding_kind"]["observed_value"] == "structured_role_labeled_record", "structured identity evidence drift")
    _assert(
        public_items["canonical_pair_record_schema_version"][
            "observed_value"
        ]
        == "covapie_covalent_bond_atom_pair_canonical_record_v1",
        "canonical record schema evidence drift",
    )
    for item in (
        "canonical_pair_record_exact_fields",
        "canonical_pair_record_exact_types",
        "canonical_record_validator_available",
        "canonical_record_roles_enforced",
        "canonical_record_event_identity_consistent",
        "canonical_record_pdb_identity_consistent",
        "canonical_record_model_identity_consistent",
        "explicit_authority_field_is_part_of_record",
        "explicit_provenance_id_is_part_of_record",
        "legacy_projection_function_available",
        "locator_syntax_is_not_mapping_success",
    ):
        _assert(item in public_items, f"public canonical evidence missing: {item}")
    _assert(public_items["legacy_string_role"]["observed_value"] == "legacy_display_and_backward_compatibility_projection", "legacy role evidence drift")

    locator = _rows(actual[LOCATOR])
    _assert(len(locator) == 13, "locator row count drift")
    _assert(tuple(row["field_name"] for row in locator) == LOCATOR_FIELDS, "locator evidence fields drift")
    _assert(tuple(row["field_order"] for row in locator) == tuple(map(str, range(1, 14))), "locator order drift")
    _assert(all(row["data_type"] == "str" and row["verified"] == "true" for row in locator), "locator schema verification drift")
    _assert(any("not_materialized" in row["current_materialization_status"] for row in locator), "locator evidence falsely claims full materialization")

    policy = _rows(actual[POLICY])
    _assert(len(policy) == 26, "policy row count drift")
    _assert(tuple(row["case_id"] for row in policy) == POLICY_CASES, "policy cases drift")
    for row in policy:
        decision = gate.evaluate_covapie_covalent_bond_atom_pair_policy_case_v1(row["case_id"])
        _assert(row["expected_outcome"] == decision.outcome, f"policy outcome drift: {row['case_id']}")
        _assert(row["expected_reason"] == decision.reason, f"policy reason drift: {row['case_id']}")
        if row["expected_outcome"] == "invalid":
            _assert(
                row["fails_closed"] == "true"
                and row["pair_retained"] == "false"
                and row["mapping_allowed"] == "false",
                f"policy does not fail closed: {row['case_id']}",
            )
    unknown = gate.evaluate_covapie_covalent_bond_atom_pair_policy_case_v1("unknown")
    _assert(unknown.outcome == "invalid" and unknown.fails_closed, "unknown policy did not fail closed")

    legacy = _rows(actual[LEGACY])
    _assert(len(legacy) == 7, "legacy row count drift")
    _assert(tuple(row["legacy_value"] for row in legacy) == LEGACY_VALUES, "legacy values drift")
    representation = _rows((ROOT / PRE_REPRESENTATION).read_bytes())
    representation_by_legacy = {}
    for source_row in representation:
        representation_by_legacy.setdefault(
            source_row["stored_covalent_bond_atom_pair"],
            source_row,
        )
    for row in legacy:
        source = representation_by_legacy[row["legacy_value"]]
        common = {
            "locator_schema_version": "covapie_covalent_atom_locator_v1",
            "event_id": source["sample_or_event_id"],
            "pdb_id": source["pdb_id"],
            "model_id": "",
            "label_asym_id": "",
            "label_seq_id": "",
            "altloc": "",
        }
        residue = gate.CovalentAtomLocatorContractDesign(
            entity_role="target_residue_atom",
            auth_asym_id=source["residue_chain_id"],
            auth_seq_id=source["residue_index"],
            insertion_code=source[
                "residue_insertion_code_if_available"
            ],
            comp_id=source["residue_name"],
            atom_name=source["residue_atom_name"],
            **common,
        )
        ligand = gate.CovalentAtomLocatorContractDesign(
            entity_role="ligand_atom",
            auth_asym_id="",
            auth_seq_id="",
            insertion_code="",
            comp_id=source["ligand_comp_id_or_het_id"],
            atom_name=source["ligand_atom_name"],
            **common,
        )
        record = gate.CovalentBondAtomPairCanonicalRecordDesign(
            "covapie_covalent_bond_atom_pair_canonical_record_v1",
            residue,
            ligand,
            "validated_struct_conn",
            f"{source['source_row_identity']}:{source['conn_id_if_available']}",
        )
        _assert(
            gate.validate_covapie_covalent_bond_atom_pair_canonical_record_design_v1(
                record
            ),
            "legacy fixture canonical record invalid",
        )
        reconstructed = gate.project_covapie_legacy_atom_name_pair_v1(record)
        _assert(reconstructed == row["legacy_value"] == row["reconstructed_legacy_value"], "legacy structured projection drift")
        _assert(
            row["canonical_identity_source"] == "structured_role_labeled_record"
            and row["legacy_is_display_only"] == "true"
            and row["current_cys_sg_compatible"] == "true",
            "legacy boundary drift",
        )

    _assert(actual[ISSUE] == (ROOT / PRE_ISSUE).read_bytes(), "issue inventory is not byte-identical")
    issues = _rows(actual[ISSUE])
    effective_open = tuple(
        row["issue_id"]
        for row in issues
        if row["successor_effective_status"] == "open"
    )
    _assert(
        effective_open == (
            "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
            "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
        ),
        "effective-open issues drift",
    )

    manifest = json.loads(actual[MANIFEST])
    _assert("covapie_covalent_bond_atom_pair_encoding_contract_manifest.json" not in manifest.get("evidence_sha256", {}), "manifest records its own SHA")
    true_keys = (
        "covalent_bond_atom_pair_encoding_contract_frozen",
        "current_semantics_audit_precondition_verified",
        "structured_canonical_encoding_frozen",
        "canonical_pair_record_schema_frozen",
        "canonical_pair_record_validator_available",
        "canonical_pair_record_roles_enforced",
        "canonical_pair_record_identity_consistency_enforced",
        "explicit_authority_embedded_in_canonical_record",
        "explicit_provenance_embedded_in_canonical_record",
        "legacy_projection_function_available",
        "structured_atom_locator_schema_frozen",
        "explicit_bond_authority_policy_frozen",
        "cardinality_and_fail_closed_policy_frozen",
        "legacy_compatibility_policy_frozen",
        "future_atom_table_mapping_policy_frozen",
        "model_input_index_space_compatibility_derived_from_committed_evidence",
        "model_input_index_space_compatibility_verified",
        "final_dataset_pocket_atom_table_reference_present",
        "final_dataset_ligand_atom_table_reference_present",
        "pair_tensorization_currently_blocked",
        "row_order_validation_deferred_to_contract_validation",
        "canonical_mask_pair_identity_invariant",
        "distance_only_inference_forbidden",
        "legacy_string_is_display_only",
        "ready_for_contract_validation",
        "feature_semantics_audit_required_before_training",
    )
    false_keys = (
        "legacy_string_is_canonical_identity",
        "current_pair_tensor_index_contract_present",
        "conflicting_existing_index_space_contract_present",
        "pair_tensor_materialized",
        "pair_tensor_shape_defined",
        "pair_loss_mask_defined",
        "pair_head_implemented",
        "pair_contrastive_loss_implemented",
        "encoding_contract_validation_completed",
        "atom_pair_issue_resolved",
        "provider_issue_resolved",
        "ready_for_tensorization",
        "provider_used",
        "download_used",
        "raw_read",
        "raw_write",
        "checkpoint_access",
        "model_changed",
        "dataloader_changed",
        "forward_changed",
        "loss_changed",
        "training_used",
        "feature_semantics_audit_completed",
        "feature_semantics_known",
        "unknown_atom_feature_policy_resolved",
        "ready_for_training",
    )
    for key in true_keys:
        _assert(manifest.get(key) is True, f"manifest true boundary drift: {key}")
    for key in false_keys:
        _assert(manifest.get(key) is False, f"manifest false boundary drift: {key}")
    _assert(
        tuple(
            (item["semantic_name"], item["alias"])
            for item in manifest["canonical_masks"]
        )
        == MASKS,
        "five-mask identity evidence drift",
    )
    _assert(manifest["accepted_explicit_bond_authority_classes"] == list(AUTHORITY_VOCABULARY), "manifest authority vocabulary drift")
    _assert(
        manifest["canonical_pair_record_schema_version"]
        == "covapie_covalent_bond_atom_pair_canonical_record_v1"
        and manifest["canonical_pair_record_field_count"] == 5,
        "manifest canonical record schema drift",
    )
    _assert(
        manifest["model_input_index_space_compatibility_evidence_paths"]
        == [path.as_posix() for path in INDEX_EVIDENCE],
        "manifest index evidence paths drift",
    )
    _assert(
        manifest["model_input_index_space_compatibility_evidence_sha256"]
        == {path.as_posix(): sha for path, sha in INDEX_EVIDENCE.items()},
        "manifest index evidence SHA drift",
    )
    _assert(
        manifest["model_input_index_space_compatibility_evidence_selectors"]
        == list(INDEX_SELECTORS),
        "manifest index evidence selectors drift",
    )
    _assert(manifest["positive_pair_cardinality_policy"] == "exactly_one_positive_explicit_pair_per_sample", "manifest cardinality drift")
    _assert(manifest["residue_model_index_space"] == "pocket_atom_table_row_index", "residue index space drift")
    _assert(manifest["ligand_model_index_space"] == "ligand_atom_table_row_index", "ligand index space drift")
    _assert(manifest["model_index_base"] == 0, "model index base drift")
    _assert(manifest["issue_status_changed"] is False, "issue status changed")
    _assert(
        (manifest["resolved_issue_count"], manifest["new_issue_count"], manifest["deleted_issue_count"])
        == (0, 0, 0),
        "issue continuity counts drift",
    )
    _assert(
        manifest["evidence_sha256"]
        == {name: OUTPUT_SHA256[name] for name in FILES[:-1]},
        "manifest evidence hashes drift",
    )
    return manifest


def main() -> int:
    _verify_base_and_predecessors()
    gate = importlib.import_module(
        "covalent_ext."
        "covapie_covalent_bond_atom_pair_encoding_contract_design_gate_v1"
    )
    _verify_api(gate)
    manifest = _verify_evidence(gate)
    report_keys = (
        ("encoding_contract_frozen", "covalent_bond_atom_pair_encoding_contract_frozen"),
        ("structured_canonical_encoding_frozen", "structured_canonical_encoding_frozen"),
        ("canonical_pair_record_schema_frozen", "canonical_pair_record_schema_frozen"),
        ("canonical_pair_record_schema_version", "canonical_pair_record_schema_version"),
        ("canonical_pair_record_validator_available", "canonical_pair_record_validator_available"),
        ("structured_atom_locator_schema_frozen", "structured_atom_locator_schema_frozen"),
        ("explicit_bond_authority_policy_frozen", "explicit_bond_authority_policy_frozen"),
        ("cardinality_and_fail_closed_policy_frozen", "cardinality_and_fail_closed_policy_frozen"),
        ("legacy_compatibility_policy_frozen", "legacy_compatibility_policy_frozen"),
        ("future_atom_table_mapping_policy_frozen", "future_atom_table_mapping_policy_frozen"),
        ("model_input_index_space_compatibility_derived_from_committed_evidence", "model_input_index_space_compatibility_derived_from_committed_evidence"),
        ("model_input_index_space_compatibility_verified", "model_input_index_space_compatibility_verified"),
        ("current_pair_tensor_index_contract_present", "current_pair_tensor_index_contract_present"),
        ("conflicting_existing_index_space_contract_present", "conflicting_existing_index_space_contract_present"),
        ("pair_tensorization_currently_blocked", "pair_tensorization_currently_blocked"),
        ("row_order_validation_deferred_to_contract_validation", "row_order_validation_deferred_to_contract_validation"),
        ("canonical_mask_pair_identity_invariant", "canonical_mask_pair_identity_invariant"),
        ("distance_only_inference_forbidden", "distance_only_inference_forbidden"),
        ("positive_pair_cardinality_policy", "positive_pair_cardinality_policy"),
        ("residue_model_index_space", "residue_model_index_space"),
        ("ligand_model_index_space", "ligand_model_index_space"),
        ("model_index_base", "model_index_base"),
        ("legacy_string_is_canonical_identity", "legacy_string_is_canonical_identity"),
        ("legacy_string_is_display_only", "legacy_string_is_display_only"),
        ("pair_tensor_materialized", "pair_tensor_materialized"),
        ("pair_tensor_shape_defined", "pair_tensor_shape_defined"),
        ("pair_loss_mask_defined", "pair_loss_mask_defined"),
        ("pair_head_implemented", "pair_head_implemented"),
        ("pair_contrastive_loss_implemented", "pair_contrastive_loss_implemented"),
        ("encoding_contract_validation_completed", "encoding_contract_validation_completed"),
        ("atom_pair_issue_resolved", "atom_pair_issue_resolved"),
        ("ready_for_contract_validation", "ready_for_contract_validation"),
        ("ready_for_tensorization", "ready_for_tensorization"),
        ("feature_semantics_audit_completed", "feature_semantics_audit_completed"),
        ("ready_for_training", "ready_for_training"),
    )
    for label, key in report_keys:
        value = manifest[key]
        if type(value) is bool:
            value = "true" if value else "false"
        print(f"{label}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
