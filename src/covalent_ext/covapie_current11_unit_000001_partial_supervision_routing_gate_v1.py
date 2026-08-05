"""Read-only task-level partial-supervision routing gate for Current11 unit 1."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import shlex
import stat
import subprocess
from collections import Counter
from pathlib import Path
from typing import Mapping, Sequence


__all__ = (
    "evaluate_covapie_current11_unit_000001_partial_supervision_routing_gate_v1",
)

SCHEMA_VERSION = "covapie_current11_unit_000001_partial_supervision_routing_gate_v1"
ERROR_TOKEN = "COVAPIE_CURRENT11_UNIT_000001_PARTIAL_SUPERVISION_ROUTING_GATE_V1_ERROR"
BASE_COMMIT = "74afd2c5c8465550eff77b88afe85dd57835d143"
BASE_TREE = "fe891d48eb6904809ce9a2ab0b7ea7cc2a456f8c"
BASE_PARENT = "9fbb1da5da504e6dadd89ace90a9e5959f1ba3de"
BASE_SUBJECT = "add CovaPIE Current11 reaction transformation human review dossier v1"
FORMAL_COMMIT_SUBJECT = "add CovaPIE Current11 partial supervision routing gate v1"
BRANCH = "main"
REVIEW_UNIT_ID = "CURRENT11_REACTION_TRANSFORMATION_REVIEW_UNIT_000001"
_PATH_TYPE = type(Path())

MODULE_PATH = (
    "src/covalent_ext/"
    "covapie_current11_unit_000001_partial_supervision_routing_gate_v1.py"
)
SCRIPT_PATH = (
    "scripts/check_covapie_current11_unit_000001_"
    "partial_supervision_routing_gate_v1.py"
)
TEST_PATH = (
    "tests/test_covapie_current11_unit_000001_"
    "partial_supervision_routing_gate_v1.py"
)
GUIDE_PATH = (
    "docs/covapie_current11_unit_000001_"
    "partial_supervision_routing_gate_v1_guide.md"
)
CANDIDATE_PATHS = tuple(sorted((MODULE_PATH, SCRIPT_PATH, TEST_PATH, GUIDE_PATH)))

SAMPLES = (
    ("CYS_SG_SAMPLE_INDEX_000008", "1AYU", "INA", "CYS_SG_EXPANSION_PREP_000005", "4"),
    ("CYS_SG_SAMPLE_INDEX_000010", "1AYW", "IN3", "CYS_SG_EXPANSION_PREP_000007", "8"),
)
SEMANTIC_TASK_NAMES = (
    "sample_identity_supervision",
    "explicit_covalent_event_supervision",
    "ligand_residue_atom_pair_supervision",
    "covalent_link_bond_order_supervision",
    "warhead_type_supervision",
    "reaction_family_supervision",
    "warhead_boundary_supervision",
    "canonical_mask_warhead_only",
    "canonical_mask_linker_plus_warhead",
    "canonical_mask_scaffold_plus_warhead",
    "canonical_mask_scaffold_only",
    "canonical_mask_scaffold_plus_linker_plus_warhead",
    "observed_complex_geometry_supervision",
    "pre_covalent_geometry_supervision",
    "post_covalent_geometry_supervision",
    "complete_post_state_graph_supervision",
    "reaction_atom_map_supervision",
    "formed_edge_supervision",
    "broken_edge_supervision",
    "bond_order_delta_supervision",
    "formal_charge_delta_supervision",
    "protonation_transfer_supervision",
    "leaving_group_supervision",
    "reversibility_supervision",
    "full_transformation_supervision",
)
ELIGIBILITY_STATE_VOCABULARY = (
    "admissible_now",
    "admissible_as_observed_geometry_only",
    "candidate_only_not_authoritative",
    "blocked_missing_evidence",
    "blocked_state_ambiguity",
    "blocked_missing_human_approval",
    "not_applicable",
)
CANONICAL_MASK_SEMANTICS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)

ROUTING_STATES_COMMON = {
    "sample_identity_supervision": "admissible_now",
    "explicit_covalent_event_supervision": "admissible_now",
    "ligand_residue_atom_pair_supervision": "admissible_now",
    "covalent_link_bond_order_supervision": "blocked_missing_evidence",
    "warhead_type_supervision": "candidate_only_not_authoritative",
    "reaction_family_supervision": "candidate_only_not_authoritative",
    "warhead_boundary_supervision": "admissible_now",
    "canonical_mask_warhead_only": "blocked_missing_human_approval",
    "canonical_mask_linker_plus_warhead": "blocked_missing_human_approval",
    "canonical_mask_scaffold_plus_warhead": "blocked_missing_human_approval",
    "canonical_mask_scaffold_only": "blocked_missing_human_approval",
    "canonical_mask_scaffold_plus_linker_plus_warhead": (
        "blocked_missing_human_approval"
    ),
    "observed_complex_geometry_supervision": (
        "admissible_as_observed_geometry_only"
    ),
    "pre_covalent_geometry_supervision": "blocked_missing_evidence",
    "post_covalent_geometry_supervision": "blocked_state_ambiguity",
    "complete_post_state_graph_supervision": "blocked_state_ambiguity",
    "reaction_atom_map_supervision": "blocked_missing_evidence",
    "formed_edge_supervision": "candidate_only_not_authoritative",
    "bond_order_delta_supervision": "blocked_missing_evidence",
    "formal_charge_delta_supervision": "blocked_missing_evidence",
    "protonation_transfer_supervision": "blocked_missing_evidence",
    "leaving_group_supervision": "candidate_only_not_authoritative",
    "full_transformation_supervision": "blocked_state_ambiguity",
}

REPO_SOURCES = {
    "mmcif_1ayu": (
        "data/raw/covalent_sources/covpdb/independent_group_expansion_batch_000001/1ayu.cif",
        "7a50b94adc96bef4222da8e55e7cdb3e854cdd80015fcf76b3a54f4cbf6a2830",
    ),
    "mmcif_1ayw": (
        "data/raw/covalent_sources/covpdb/independent_group_expansion_batch_000001/1ayw.cif",
        "e8402436f23cbccc6317342c5a2f0ffb01acb0ced0ed29df5f6029e9fabcb07d",
    ),
    "canonical_pair_matrix": (
        "data/derived/covalent_small/"
        "covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_evidence_validation_v1/"
        "covapie_atom_pair_canonical_record_validation_matrix.csv",
        "c756e6ce601bad1d10cfba5cac6129f9f688d00451cc1d805edff938ccee6ca0",
    ),
    "atom_table_mapping_matrix": (
        "data/derived/covalent_small/"
        "covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_evidence_validation_v1/"
        "covapie_atom_pair_atom_table_mapping_validation_matrix.csv",
        "9f26b25ed11d186a02a1f859de10a105605ce3af13805ac5a4be1ad73199df45",
    ),
    "observed_pair_table_1ayu": (
        "data/derived/covalent_small/"
        "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/"
        "samples/1AYU_INA/ligand_residue_atom_pair_table.csv",
        "bf68477bccf748c347f4198f71fa95a65899f684a510b73d17ae9e566917bc5e",
    ),
    "observed_pair_table_1ayw": (
        "data/derived/covalent_small/"
        "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/"
        "samples/1AYW_IN3/ligand_residue_atom_pair_table.csv",
        "58148a7ea77024eee27f871d618d4e257d3649bfd6a420b2ea6d4050dbcffe8f",
    ),
    "candidate_family_assignments": (
        "data/derived/covalent_small/"
        "covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1/"
        "covapie_current11_cys_sg_candidate_assignment_authority.csv",
        "bc49e2f1ca112ceae30c91fa492386f6012c9005fc5137b40d3daec2343ef5d9",
    ),
    "canonical_mask_truth_table": (
        "data/derived/covalent_small/"
        "covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1/"
        "covapie_canonical_task_truth_table.csv",
        "586d483f67b9108af1af820b892b477329a1b6de24b0ad0b9ee46cebbaba20e5",
    ),
}
STATE_SOURCES = {
    "routing_audit_report": (
        "review-scratch/current11-unit-000001-partial-supervision-routing-v1/"
        "partial_supervision_routing_audit_report.md",
        "00359dd0e108e7e9dbd350147d8a2c489c72b85a8095c115e6bd9212effa6e45",
    ),
    "local_evidence_audit_report": (
        "review-scratch/current11-unit-000001-transformation-evidence-availability-v1/"
        "local_transformation_evidence_availability_report.md",
        "1082725c9eda01324a5b4b54e9f5b930cd9237ad6793d60b22b684c354cbc480",
    ),
    "primary_literature_report": (
        "review-scratch/current11-unit-000001-primary-literature-evidence-v1/"
        "primary_literature_transformation_evidence_report.md",
        "685c30afa9beb54765d2365a99c4b9a717ecdb472d96f40b37f9e00550a71a0b",
    ),
    "primary_source_manifest": (
        "review-scratch/current11-unit-000001-primary-literature-evidence-v1/"
        "primary_source_manifest.json",
        "07817a17f7be45163bb1a41c1f1740f19de4eb7ee329fb10f3dca56599824c43",
    ),
    "primary_source_inventory": (
        "review-scratch/current11-unit-000001-primary-literature-evidence-v1/"
        "primary_source_inventory.csv",
        "841e4f2c9ec9491d75d3065d797bf8d705e29c618e5984ffedcfe1017b73f4e5",
    ),
    "primary_article": (
        "review-scratch/current11-unit-000001-primary-literature-evidence-v1/"
        "primary_article_source.html",
        "7ac6506b45c6d2753383523b84c0693a039af54598a79cdcc9b4c1f5ca6dfc3d",
    ),
    "unified_boundary_authority": (
        "manual-review/covapie_current11_unified_effective_authority_view_v1.json",
        "f4178987f3c3eed0e248f6d3d5f22cb8bce1839d39ab08aff0bff9d2ef9f3774",
    ),
    "formal_transformation_worklist": (
        "manual-review/current11-reaction-transformation-review-v1/"
        "transformation_evidence_worklist.csv",
        "c7063e8070de3ecd1fdf4dfc19ffd91ef09dbeac48d80fbc6f01c9369d647423",
    ),
    "formal_family_rule_worklist": (
        "manual-review/current11-family-rule-approval-v1/"
        "family_rule_approval_worklist.csv",
        "9a85c03384a09620a1c168b023d3a1de2ebb1fed57589e55449ec1672d6c3add",
    ),
}

DOSSIER_RELATIVE = (
    "manual-review-aids/current11-reaction-transformation-review-v1/"
    + REVIEW_UNIT_ID
)
DOSSIER_IDENTITY = (49, 196008339793)
DOSSIER_SHA256 = {
    "README.md": "99fa7532e4f8d3545caa6d3907e0df3338eac464426fe7f109dd6d6f0f476610",
    "candidate_local_graph.svg": "2daad45b6d2b1b35bdfb38ddfc1f5cb38cdf58eabbe31c591273714a6dafdc96",
    "dossier_manifest.json": "96e19c2d01ec1edc517e1090d73c4b21d5d6a5dcd79ca6dbeff7defcffb14202",
    "frozen_transformation_review_summary.json": "0ec37a92bdc947e771dfe0804a1d15d26fde32ba725d95661b4db228c5cc513a",
    "human_transformation_evidence_questionnaire.md": "cc30376d7315575f9f24f2e71accb5ae3adcabc0e96c354c52e7eef2dfd75b57",
    "sample_transformation_gap_evidence.csv": "599c75f0f97896c0eea73dbde5041a446f23cb5d30e7da36c186a908561e1134",
    "source_authority_inventory_snapshot.csv": "fb638a9573cfba0561879b8f8b030c453bd5b3fe693c983eb6fa65f1b7cc4e28",
    "structured_json_schema_templates.json": "ddde07b4b28ee45163d0cb09a9e08ea8712c255a20b1b7fd72dbb7da110f07c6",
}

TRANSFORMATION_FIELDS = (
    "transformation_review_unit_id", "parent_review_unit_id", "reaction_family_id",
    "warhead_rule_id", "sample_index_row_ids_json", "sample_count",
    "target_residue_types_json", "target_residue_reactive_atom_name",
    "ligand_reactive_atom_ids_by_sample_json",
    "effective_attachment_boundaries_by_sample_json",
    "candidate_local_graph_rule_sha256", "candidate_formed_bond_order",
    "pre_reaction_center_bond_order_sum",
    "conditional_post_bond_order_sum_if_internal_bonds_unchanged",
    "post_reaction_authority_status", "schema_gap_detected",
    "reviewed_transformation_version", "reviewed_transformation_class",
    "reviewed_transformation_scope", "reviewed_atom_map_contract_json",
    "reviewed_attachment_boundary_map_numbers_by_sample_json",
    "reviewed_pre_atom_state_contract_json", "reviewed_post_atom_state_contract_json",
    "reviewed_formed_edges_json", "reviewed_broken_edges_json",
    "reviewed_bond_order_changes_json", "reviewed_formal_charge_changes_json",
    "reviewed_protonation_transfer_contract_json", "reviewed_leaving_group_contract_json",
    "reviewed_reversibility_semantics", "reviewed_post_state_evidence_type",
    "reviewed_post_state_evidence_source", "reviewed_post_state_evidence_sha256",
    "transformation_identity_explicitly_attested",
    "transformation_full_semantics_explicitly_attested",
    "transformation_review_decision", "review_rationale", "review_notes",
    "reviewer_id", "attestor_id", "review_completed",
)
FUTURE_FIELDS = TRANSFORMATION_FIELDS[16:]


def _fail() -> None:
    raise ValueError(ERROR_TOKEN)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_frozen(root: Path, relative: str, expected_sha256: str) -> bytes:
    try:
        path = root / relative
        metadata = path.lstat()
        payload = path.read_bytes()
        if (
            path.is_symlink()
            or not stat.S_ISREG(metadata.st_mode)
            or len(payload) >= 1024 * 1024
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\0" in payload
            or _sha256(payload) != expected_sha256
        ):
            _fail()
        payload.decode("utf-8")
        return payload
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR_TOKEN:
            raise
        raise ValueError(ERROR_TOKEN) from error


def _csv_rows(payload: bytes) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    try:
        text = payload.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        fields = tuple(reader.fieldnames or ())
        rows = list(reader)
        if not fields or any(None in row or tuple(row) != fields for row in rows):
            _fail()
        return fields, rows
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR_TOKEN:
            raise
        raise ValueError(ERROR_TOKEN) from error


def _json(payload: bytes, expected_type: type) -> object:
    try:
        value = json.loads(payload.decode("utf-8"))
        if type(value) is not expected_type:
            _fail()
        return value
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR_TOKEN:
            raise
        raise ValueError(ERROR_TOKEN) from error


def _mmcif_struct_conn(payload: bytes) -> list[dict[str, str]]:
    try:
        lines = payload.decode("utf-8").splitlines()
        for index, line in enumerate(lines):
            if line.strip() != "loop_":
                continue
            fields: list[str] = []
            cursor = index + 1
            while cursor < len(lines) and lines[cursor].startswith("_struct_conn."):
                fields.append(lines[cursor].strip())
                cursor += 1
            if not fields:
                continue
            rows: list[dict[str, str]] = []
            while cursor < len(lines) and lines[cursor].strip() != "#":
                tokens = shlex.split(lines[cursor], comments=False, posix=True)
                if tokens:
                    if len(tokens) != len(fields):
                        _fail()
                    rows.append(dict(zip(fields, tokens, strict=True)))
                cursor += 1
            return rows
        _fail()
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR_TOKEN:
            raise
        raise ValueError(ERROR_TOKEN) from error


def _validate_struct_conn(payload: bytes, *, ligand: str, distance: str) -> dict[str, str]:
    rows = [row for row in _mmcif_struct_conn(payload) if row["_struct_conn.id"] == "covale1"]
    if len(rows) != 1:
        _fail()
    row = rows[0]
    expected = {
        "_struct_conn.conn_type_id": "covale",
        "_struct_conn.ptnr1_label_comp_id": "CYS",
        "_struct_conn.ptnr1_label_atom_id": "SG",
        "_struct_conn.ptnr1_auth_comp_id": "CYS",
        "_struct_conn.ptnr2_label_comp_id": ligand,
        "_struct_conn.ptnr2_label_atom_id": "C21",
        "_struct_conn.ptnr2_auth_comp_id": ligand,
        "_struct_conn.pdbx_value_order": "?",
        "_struct_conn.pdbx_dist_value": distance,
    }
    if any(row.get(key) != value for key, value in expected.items()):
        _fail()
    return row


def _select_exact(rows: Sequence[Mapping[str, str]], **criteria: str) -> dict[str, str]:
    selected = [row for row in rows if all(row.get(key) == value for key, value in criteria.items())]
    if len(selected) != 1:
        _fail()
    return dict(selected[0])


def _validate_pair_evidence(payloads: Mapping[str, bytes]) -> dict[str, object]:
    _, canonical = _csv_rows(payloads["canonical_pair_matrix"])
    _, mappings = _csv_rows(payloads["atom_table_mapping_matrix"])
    report: dict[str, object] = {}
    for sample, pdb, ligand, event, _compound in SAMPLES:
        pair = _select_exact(canonical, sample_index_row_id=sample)
        if (
            pair.get("pdb_id") != pdb
            or pair.get("ligand_comp_id") != ligand
            or pair.get("residue_comp_id") != "CYS"
            or pair.get("residue_atom_name") != "SG"
            or pair.get("ligand_atom_name") != "C21"
            or pair.get("explicit_bond_authority_class") != "validated_struct_conn"
            or pair.get("canonical_record_valid") != "true"
            or pair.get("explicit_authority_preserved") != "true"
            or pair.get("verified") != "true"
        ):
            _fail()
        mapped = [row for row in mappings if row.get("sample_index_row_id") == sample]
        if len(mapped) != 2 or {row.get("entity_role") for row in mapped} != {
            "target_residue_atom", "ligand_atom"
        }:
            _fail()
        for row in mapped:
            if (
                row.get("candidate_match_count") != "1"
                or row.get("expected_match_count") != "1"
                or row.get("mapping_outcome") != "mapped"
                or row.get("mapping_reason") != "exact_one_identity_mapping"
                or row.get("distance_used_for_mapping_selection") != "false"
                or row.get("atom_site_id_matches") != "true"
                or row.get("verified") != "true"
            ):
                _fail()
        pair_key = "observed_pair_table_1ayu" if pdb == "1AYU" else "observed_pair_table_1ayw"
        _, observed_rows = _csv_rows(payloads[pair_key])
        observed = _select_exact(observed_rows, sample_preparation_input_id=event)
        expected_distance = "1.799" if pdb == "1AYU" else "1.794"
        if (
            observed.get("pdb_id") != pdb
            or observed.get("expected_het_id") != ligand
            or observed.get("residue_atom_name") != "SG"
            or observed.get("ligand_atom_name") != "C21"
            or observed.get("bond_distance_angstrom") != expected_distance
            or observed.get("validation_status")
            != "validated_from_step14al_struct_conn_and_raw_atom_site"
        ):
            _fail()
        report[sample] = {
            "explicit_bond_authority_class": "validated_struct_conn",
            "exact_one_mapping_role_count": 2,
            "distance_angstrom": expected_distance,
            "distance_authority_scope": "observed_complex_geometry_only",
        }
    return report


def _validate_boundary_authority(payload: bytes) -> dict[str, object]:
    view = _json(payload, dict)
    if not isinstance(view, dict) or view.get("unified_effective_authority_view_version") != (
        "covapie_current11_unified_effective_authority_view_v1"
    ):
        _fail()
    records = view.get("effective_authority_records")
    if type(records) is not list:
        _fail()
    report: dict[str, object] = {}
    for sample, pdb, ligand, _event, _compound in SAMPLES:
        outer = _select_exact(records, sample_index_row_id=sample)
        record = outer.get("effective_authority_record")
        if type(record) is not dict:
            _fail()
        boundaries = record.get("reviewed_boundary_records")
        atoms = record.get("reviewed_warhead_atom_ids")
        forbidden_partition_keys = {
            "reviewed_scaffold_atom_ids", "reviewed_linker_atom_ids",
            "complete_primary_role_partition_available",
        }
        if (
            outer.get("effective_authority_namespace") != "exact_two_boundaries_multi_boundary_v1"
            or outer.get("effective_boundary_cardinality") != 2
            or record.get("pdb_id") != pdb
            or record.get("ligand_comp_id") != ligand
            or record.get("authority_status") != "active"
            or record.get("sample_quarantined") is not False
            or record.get("complete_warhead_atom_set_authority_available") is not True
            or record.get("exact_two_attachment_boundaries_authority_available") is not True
            or type(atoms) is not list
            or not atoms
            or len(atoms) != len(set(atoms))
            or type(boundaries) is not list
            or len(boundaries) != 2
            or forbidden_partition_keys.intersection(record)
        ):
            _fail()
        report[sample] = {
            "authority_status": "active",
            "sample_quarantined": False,
            "reviewed_warhead_atom_count": len(atoms),
            "reviewed_boundary_record_count": 2,
            "complete_primary_role_partition_available": False,
        }
    return report


def _validate_candidate_assignments(payload: bytes) -> dict[str, object]:
    _, rows = _csv_rows(payload)
    result: dict[str, object] = {}
    for sample, pdb, ligand, _event, _compound in SAMPLES:
        row = _select_exact(rows, sample_index_row_id=sample)
        if (
            row.get("pdb_id") != pdb
            or row.get("ligand_comp_id") != ligand
            or row.get("candidate_rule_assignment_exact_one") != "true"
            or row.get("candidate_family_assignment_exact_one") != "true"
            or row.get("assignment_status") != "machine_derived_candidate_assignment_materialized"
            or row.get("review_status") != "not_reviewed"
            or row.get("training_label_status") != "not_approved_for_training"
            or row.get("formal_reaction_family_label_available") != "false"
            or row.get("approved_warhead_rule_available") != "false"
            or row.get("training_label_approved") != "false"
            or row.get("verified") != "true"
        ):
            _fail()
        result[sample] = {
            "candidate_reaction_family_id": row["candidate_reaction_family_id"],
            "warhead_type_candidate_class_id": row["warhead_type_candidate_class_id"],
            "authority_status": "candidate_only_not_authoritative",
        }
    return result


def _validate_family_worklist(payload: bytes) -> dict[str, object]:
    fields, rows = _csv_rows(payload)
    row = _select_exact(rows, review_unit_id="CURRENT11_FAMILY_RULE_APPROVAL_REVIEW_UNIT_000001")
    reviewed = fields[22:]
    if (
        row.get("current_binding_conclusion") != "family_and_rule_not_authoritative"
        or row.get("approved_warhead_smarts_currently_available") != "false"
        or row.get("formal_equivalent_structural_contract_currently_available") != "false"
        or not reviewed
        or any(row[field] != "" for field in reviewed)
    ):
        _fail()
    return {
        "review_unit_id": row["review_unit_id"],
        "approval_field_count": len(reviewed),
        "approval_nonblank_count": 0,
        "full_semantics_attested": False,
    }


def _validate_transformation_worklist(payload: bytes) -> dict[str, object]:
    fields, rows = _csv_rows(payload)
    if fields != TRANSFORMATION_FIELDS or len(rows) != 1:
        _fail()
    row = rows[0]
    exact16 = {
        "transformation_review_unit_id": REVIEW_UNIT_ID,
        "parent_review_unit_id": "CURRENT11_FAMILY_RULE_APPROVAL_REVIEW_UNIT_000001",
        "reaction_family_id": "COVAPIE_CYS_SG_REACTION_FAMILY_11AA213C661B48E3",
        "warhead_rule_id": "COVAPIE_CYS_SG_WARHEAD_RULE_106441A31FA4F951",
        "sample_index_row_ids_json": '["CYS_SG_SAMPLE_INDEX_000008","CYS_SG_SAMPLE_INDEX_000010"]',
        "sample_count": "2",
        "target_residue_types_json": '["CYS"]',
        "target_residue_reactive_atom_name": "SG",
        "ligand_reactive_atom_ids_by_sample_json": (
            '{"samples":{"CYS_SG_SAMPLE_INDEX_000008":"C21",'
            '"CYS_SG_SAMPLE_INDEX_000010":"C21"}}'
        ),
        "candidate_local_graph_rule_sha256": (
            "106441a31fa4f9516c174c5a0fa89709e820ebeeff419ba30883ea34a1c26bb6"
        ),
        "candidate_formed_bond_order": "single",
        "pre_reaction_center_bond_order_sum": "4",
        "conditional_post_bond_order_sum_if_internal_bonds_unchanged": "5",
        "post_reaction_authority_status": "absent",
        "schema_gap_detected": "true",
    }
    boundaries = json.loads(row["effective_attachment_boundaries_by_sample_json"])
    if (
        any(row.get(key) != value for key, value in exact16.items())
        or type(boundaries) is not dict
        or tuple(boundaries.get("samples", {})) != (SAMPLES[0][0], SAMPLES[1][0])
        or any(len(boundaries["samples"][sample]) != 2 for sample, *_rest in SAMPLES)
        or any(row[field] != "" for field in FUTURE_FIELDS)
    ):
        _fail()
    return {
        "row_count": 1,
        "field_count": 41,
        "frozen_field_count": 16,
        "future_field_count": 25,
        "future_nonblank_count": 0,
        "missing_semantics": "blank_not_empty_list_not_not_claimed_not_false_not_negative_label",
    }


def _validate_literature(manifest_payload: bytes, inventory_payload: bytes) -> dict[str, bool]:
    manifest = _json(manifest_payload, dict)
    _, rows = _csv_rows(inventory_payload)
    if not isinstance(manifest, dict) or manifest.get("compound_pdb_mapping_verified") != {
        "4": "1AYU", "8": "1AYW", "9": "1AYV"
    }:
        _fail()
    by_id = {row.get("evidence_id"): row for row in rows}
    expected_evidence_ids = (
        {f"PL-E{index:03d}" for index in range(1, 25)}
        - {"PL-E003", "PL-E004"}
    ) | {"DB-E003", "DB-E004"}
    if len(by_id) != len(rows) or set(by_id) != expected_evidence_ids:
        _fail()
    class_scope = by_id["PL-E023"]
    release = by_id["PL-E020"]
    irreversibility = by_id["PL-E018"]
    uncertainty = by_id["PL-E019"]
    if (
        class_scope.get("sample_specific") != "false"
        or class_scope.get("state_scope") != "general_mechanistic_class"
        or release.get("compound_id") != "4"
        or release.get("sample_index_row_id") != SAMPLES[0][0]
        or release.get("state_scope") != "solution_phase_assay"
        or irreversibility.get("compound_id") != "4"
        or irreversibility.get("experimental_modality") != "kinetic_observation"
        or uncertainty.get("compound_id") != "4"
        or "very slow release" not in uncertainty.get("paraphrased_claim", "")
        or any(
            row.get("compound_id") == "8"
            and row.get("experimental_modality") == "kinetic_observation"
            for row in rows
        )
    ):
        _fail()
    return {
        "class_scope_potential_leaving_group_evidence_found": True,
        "compound4_solution_release_product_evidence_found": True,
        "crystallographic_leaving_group_contract_supported": False,
        "complete_leaving_group_contract_supported": False,
        "compound4_apparent_irreversibility_evidence_found": True,
        "compound4_definitive_irreversibility_supported": False,
        "compound4_slow_release_uncertainty_present": True,
        "compound8_reversibility_evidence_found": False,
        "complete_reversibility_contract_supported": False,
    }


def _validate_masks(payload: bytes) -> list[dict[str, str]]:
    _, rows = _csv_rows(payload)
    observed = tuple((row.get("semantic_name"), row.get("display_alias")) for row in rows)
    if observed != CANONICAL_MASK_SEMANTICS or any(row.get("verified") != "true" for row in rows):
        _fail()
    return [
        {"semantic_name": semantic_name, "display_alias": display_alias}
        for semantic_name, display_alias in CANONICAL_MASK_SEMANTICS
    ]


def _validate_dossier(state_root: Path) -> dict[str, object]:
    try:
        dossier = state_root / DOSSIER_RELATIVE
        metadata = dossier.lstat()
        children = tuple(sorted(dossier.iterdir(), key=lambda item: item.name))
        if (
            dossier.is_symlink()
            or not stat.S_ISDIR(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o755
            or (metadata.st_dev, metadata.st_ino) != DOSSIER_IDENTITY
            or tuple(child.name for child in children) != tuple(sorted(DOSSIER_SHA256))
        ):
            _fail()
        for child in children:
            child_metadata = child.lstat()
            payload = child.read_bytes()
            if (
                child.is_symlink()
                or not stat.S_ISREG(child_metadata.st_mode)
                or stat.S_IMODE(child_metadata.st_mode) != 0o644
                or _sha256(payload) != DOSSIER_SHA256[child.name]
            ):
                _fail()
        return {
            "review_unit_id": REVIEW_UNIT_ID,
            "directory_identity": [metadata.st_dev, metadata.st_ino],
            "directory_mode": "0755",
            "exact_file_count": 8,
            "exact8_sha256_verified": True,
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR_TOKEN:
            raise
        raise ValueError(ERROR_TOKEN) from error


def _record_text(task: str, sample: str, distance: str) -> tuple[str, str, str, str, list[str]]:
    common: dict[str, tuple[str, str, str, str, list[str]]] = {
        "sample_identity_supervision": (
            "frozen sample identity and literature deposition mapping", "sample_identity",
            "", "identity provenance QA", ["formal_transformation_worklist", "primary_source_inventory"],
        ),
        "explicit_covalent_event_supervision": (
            "official covale1 plus validated explicit authority", "binary_explicit_event",
            "bond order remains unknown but is not required for binary event scope",
            "future gated binary event metadata", ["mmcif_1ayu" if sample == SAMPLES[0][0] else "mmcif_1ayw", "canonical_pair_matrix"],
        ),
        "ligand_residue_atom_pair_supervision": (
            "validated_struct_conn SG-C21 with exact-one role mappings", "explicit_atom_pair",
            "no current runtime adapter", "future gated pair sidecar",
            ["canonical_pair_matrix", "atom_table_mapping_matrix"],
        ),
        "covalent_link_bond_order_supervision": (
            "official _struct_conn.pdbx_value_order is ?", "missing_authoritative_bond_order",
            "candidate single is not authority", "evidence acquisition or human review",
            ["mmcif_1ayu" if sample == SAMPLES[0][0] else "mmcif_1ayw", "formal_transformation_worklist"],
        ),
        "warhead_type_supervision": (
            "machine-derived candidate class only", "candidate_family_rule",
            "warhead type and rule are not approved", "candidate tracking only",
            ["candidate_family_assignments", "formal_family_rule_worklist"],
        ),
        "reaction_family_supervision": (
            "machine-derived candidate family only", "candidate_family_rule",
            "family identity and full semantics are not attested", "family/rule human review only",
            ["candidate_family_assignments", "formal_family_rule_worklist"],
        ),
        "warhead_boundary_supervision": (
            "active human-reviewed warhead atom set and exact-two boundaries", "warhead_boundary_only",
            "does not establish complete scaffold/linker/warhead partition",
            "boundary metadata supervision", ["unified_boundary_authority"],
        ),
        "observed_complex_geometry_supervision": (
            f"validated observed SG-C21 distance {distance} angstrom", "observed_complex_coordinates",
            "not normalized pre/post geometry or a complete graph", "observed-coordinate geometry QA",
            ["observed_pair_table_1ayu" if sample == SAMPLES[0][0] else "observed_pair_table_1ayw"],
        ),
        "pre_covalent_geometry_supervision": (
            "no sample-bound pre-covalent geometry", "missing_pre_geometry",
            "isolated topology is not pre-complex geometry", "acquire explicit pre-state geometry", []
        ),
        "post_covalent_geometry_supervision": (
            "crystal and solution evidence describe non-interchangeable states", "state_ambiguous_geometry",
            "no unique normalized post state", "retain observed geometry only", ["primary_source_inventory"],
        ),
        "complete_post_state_graph_supervision": (
            "explicit link with unresolved complete state", "state_ambiguous_graph",
            "unique complete post graph absent", "human state resolution", ["primary_source_inventory", "formal_transformation_worklist"],
        ),
        "reaction_atom_map_supervision": (
            "identity mapping is not a reaction atom map", "missing_reaction_map",
            "map numbers are blank", "acquire curated mapped package", ["formal_transformation_worklist"],
        ),
        "formed_edge_supervision": (
            "SG-C21 endpoint pair is an unreviewed formed-edge candidate", "candidate_formed_edge",
            "exact order and reaction map absent", "human review candidate only", ["canonical_pair_matrix", "formal_transformation_worklist"],
        ),
        "bond_order_delta_supervision": (
            "proposed mechanism is not an exact delta", "missing_bond_order_delta",
            "reviewed delta remains blank", "acquire mapped delta", ["formal_transformation_worklist"],
        ),
        "formal_charge_delta_supervision": (
            "post-state charges are absent", "missing_charge_delta",
            "reviewed charge delta remains blank", "acquire post-charge authority", ["formal_transformation_worklist"],
        ),
        "protonation_transfer_supervision": (
            "no explicit proton-transfer contract", "missing_protonation_transfer",
            "hydrogen policy remains blank", "human-curated contract only", ["formal_transformation_worklist"],
        ),
        "leaving_group_supervision": (
            "class-scope potential leaving group evidence", "candidate_leaving_group",
            "not a sample-complete crystallographic contract", "human review cue only", ["primary_source_inventory"],
        ),
        "full_transformation_supervision": (
            "partial link and state evidence only", "state_ambiguous_full_transformation",
            "map, unique graph, order, deltas, charge and protonation are incomplete",
            "exclude from full transformation training", ["formal_transformation_worklist", "primary_source_inventory"],
        ),
    }
    if task.startswith("canonical_mask_"):
        return (
            "canonical Exact5 truth table with mandatory B3", "canonical_mask_contract_only",
            "complete nonempty mutually exclusive scaffold/linker/warhead authority is absent",
            "await primary-role human approval", ["canonical_mask_truth_table", "unified_boundary_authority"],
        )
    if task == "broken_edge_supervision":
        if sample == SAMPLES[0][0]:
            return (
                "compound-4 solution/workup release product", "candidate_solution_broken_edge",
                "cleavage time/state and exact broken edge remain unresolved",
                "evidence triage only", ["primary_source_inventory"],
            )
        return (
            "crystal cleavage cannot be excluded and solution state is separate", "state_ambiguous_broken_edge",
            "no transferable sample-specific exact broken edge", "resolve state; do not label",
            ["primary_source_inventory"],
        )
    if task == "reversibility_supervision":
        if sample == SAMPLES[0][0]:
            return (
                "compound-4 apparent irreversibility with slow-release uncertainty", "candidate_kinetic_reversibility",
                "definitive irreversibility is unsupported", "qualified human review cue only",
                ["primary_source_inventory"],
            )
        return (
            "no compound-8-specific reversibility result", "missing_sample_reversibility",
            "compound-4 evidence cannot propagate to compound 8", "exclude from reversibility supervision",
            ["primary_source_inventory"],
        )
    if task not in common:
        _fail()
    return common[task]


def _build_routing_records() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for sample, pdb, ligand, _event, _compound in SAMPLES:
        states = dict(ROUTING_STATES_COMMON)
        states["broken_edge_supervision"] = (
            "candidate_only_not_authoritative" if sample == SAMPLES[0][0]
            else "blocked_state_ambiguity"
        )
        states["reversibility_supervision"] = (
            "candidate_only_not_authoritative" if sample == SAMPLES[0][0]
            else "blocked_missing_evidence"
        )
        if tuple(states) != tuple(task for task in SEMANTIC_TASK_NAMES if task in states):
            states = {task: states[task] for task in SEMANTIC_TASK_NAMES}
        distance = "1.799" if pdb == "1AYU" else "1.794"
        for task in SEMANTIC_TASK_NAMES:
            authority, scope, gap, safe_use, sources = _record_text(task, sample, distance)
            records.append({
                "sample_index_row_id": sample,
                "pdb_id": pdb,
                "ligand_comp_id": ligand,
                "semantic_task_name": task,
                "eligibility_state": states[task],
                "authority_basis": authority,
                "evidence_scope": scope,
                "supporting_source_ids": sources,
                "blocking_gap": gap,
                "safe_next_use": safe_use,
                "availability_mask_required": True,
                "current_runtime_consumer_available": False,
                "training_loss_authorized": False,
            })
    return records


def _summary(records: Sequence[Mapping[str, object]]) -> dict[str, object]:
    counts = Counter(record["eligibility_state"] for record in records)
    result = {
        "sample_count": 2,
        "semantic_task_count": 25,
        "routing_record_count": 50,
        "admissible_now_task_sample_pair_count": counts["admissible_now"],
        "observed_geometry_only_task_sample_pair_count": counts[
            "admissible_as_observed_geometry_only"
        ],
        "candidate_only_task_sample_pair_count": counts["candidate_only_not_authoritative"],
        "blocked_missing_evidence_task_sample_pair_count": counts["blocked_missing_evidence"],
        "blocked_state_ambiguity_task_sample_pair_count": counts["blocked_state_ambiguity"],
        "blocked_missing_human_approval_task_sample_pair_count": counts[
            "blocked_missing_human_approval"
        ],
        "not_applicable_task_sample_pair_count": counts["not_applicable"],
        "explicit_pair_supervision_admissible": True,
        "link_bond_order_supervision_admissible": False,
        "observed_complex_geometry_admissible": True,
        "pre_covalent_geometry_supervision_admissible": False,
        "normalized_post_covalent_geometry_supervision_admissible": False,
        "full_post_state_supervision_admissible": False,
        "full_transformation_supervision_admissible": False,
        "canonical_mask_exact5_preserved": True,
        "current_runtime_consumer_available": False,
        "training_loss_authorized": False,
        "checkpoint_compatibility_impact": "none_metadata_only_gate",
    }
    expected_counts = (8, 2, 10, 13, 7, 10, 0)
    actual_counts = tuple(result[key] for key in (
        "admissible_now_task_sample_pair_count",
        "observed_geometry_only_task_sample_pair_count",
        "candidate_only_task_sample_pair_count",
        "blocked_missing_evidence_task_sample_pair_count",
        "blocked_state_ambiguity_task_sample_pair_count",
        "blocked_missing_human_approval_task_sample_pair_count",
        "not_applicable_task_sample_pair_count",
    ))
    if actual_counts != expected_counts:
        _fail()
    return result


def _readiness() -> dict[str, bool]:
    return {
        "partial_supervision_routing_gate_implemented": True,
        "evidence_level_partial_supervision_routes_available": True,
        "runtime_partial_supervision_consumer_available": False,
        "training_loss_authorized": False,
        "repository_schema_changed": False,
        "formal_worklist_modified": False,
        "formal_dossier_modified": False,
        "authority_changed": False,
        "tensor_materialized": False,
        "model_changed": False,
        "training_performed": False,
        "ready_for_partial_supervision_gate_validation": True,
        "ready_for_partial_supervision_tensor_materialization": False,
        "ready_for_dataloader_integration": False,
        "ready_for_model_integration": False,
        "ready_for_formal_worklist_update": False,
        "ready_for_semantic_validation": False,
        "feature_semantics_reaudit_required_before_training": True,
        "ready_for_training": False,
    }


def _run_git(repo_root: Path, args: Sequence[str]) -> str:
    try:
        completed = subprocess.run(
            ("git", *args), cwd=repo_root, check=False, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if completed.returncode != 0:
            _fail()
        return completed.stdout.decode("utf-8")
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR_TOKEN:
            raise
        raise ValueError(ERROR_TOKEN) from error


def _is_hex(value: object) -> bool:
    return type(value) is str and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def _is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    completed = subprocess.run(
        ("git", "merge-base", "--is-ancestor", ancestor, descendant), cwd=repo_root,
        check=False, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if completed.returncode not in (0, 1):
        _fail()
    return completed.returncode == 0


def _live_identity(repo_root: Path, relative: str) -> dict[str, object]:
    path = repo_root / relative
    metadata = path.lstat()
    if path.is_symlink() or not stat.S_ISREG(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != 0o644:
        _fail()
    blob = _run_git(repo_root, ("hash-object", "--no-filters", "--", relative)).strip()
    line = _run_git(repo_root, ("ls-files", "--stage", "--", relative)).strip()
    if not _is_hex(blob):
        _fail()
    if not line:
        return {"tracked": False, "mode": "100644", "blob": blob}
    metadata_text, listed = line.split("\t", 1)
    mode, index_blob, stage = metadata_text.split()
    if listed != relative or stage != "0" or not _is_hex(index_blob):
        _fail()
    return {"tracked": True, "mode": mode, "index_blob": index_blob, "blob": blob}


def _collect_lifecycle(repo_root: Path) -> dict[str, object]:
    head = _run_git(repo_root, ("rev-parse", "HEAD")).strip()
    origin = _run_git(repo_root, ("rev-parse", "refs/remotes/origin/main")).strip()
    ahead, behind = _run_git(
        repo_root, ("rev-list", "--left-right", "--count", "HEAD...refs/remotes/origin/main")
    ).split()
    revisions = set(_run_git(repo_root, ("rev-list", f"{BASE_COMMIT}..{head}")).splitlines())
    revisions.update(_run_git(repo_root, ("rev-list", f"{BASE_COMMIT}..{origin}")).splitlines())
    path_commits: list[dict[str, object]] = []
    for commit in sorted(revisions):
        statuses = {}
        for line in _run_git(
            repo_root, ("diff-tree", "--root", "--no-commit-id", "--name-status", "-r", commit)
        ).splitlines():
            parts = line.split("\t")
            if len(parts) == 2:
                statuses[parts[1]] = parts[0]
        if not set(statuses).intersection(CANDIDATE_PATHS):
            continue
        modes: dict[str, str] = {}
        blobs: dict[str, str] = {}
        for relative in CANDIDATE_PATHS:
            line = _run_git(repo_root, ("ls-tree", commit, "--", relative)).strip()
            if line:
                tree_text, listed = line.split("\t", 1)
                mode, kind, blob = tree_text.split()
                if listed != relative or kind != "blob":
                    _fail()
                modes[relative] = mode
                blobs[relative] = blob
        parents = _run_git(repo_root, ("show", "-s", "--format=%P", commit)).split()
        subject = _run_git(repo_root, ("show", "-s", "--format=%s", commit)).strip()
        path_commits.append({
            "commit": commit, "parents": parents, "subject": subject,
            "changed_paths": tuple(sorted(statuses)),
            "changed_statuses": {path: statuses[path] for path in sorted(statuses)},
            "path_modes": modes, "path_blobs": blobs,
            "ancestor_head": _is_ancestor(repo_root, commit, head),
            "ancestor_origin": _is_ancestor(repo_root, commit, origin),
        })
    return {
        "head": head, "origin": origin, "ahead": int(ahead), "behind": int(behind),
        "branch": _run_git(repo_root, ("branch", "--show-current")).strip(),
        "base_ancestor_head": _is_ancestor(repo_root, BASE_COMMIT, head),
        "base_ancestor_origin": _is_ancestor(repo_root, BASE_COMMIT, origin),
        "tracked": tuple(sorted(_run_git(repo_root, ("diff", "--name-only")).splitlines())),
        "staged": tuple(sorted(_run_git(repo_root, ("diff", "--cached", "--name-only")).splitlines())),
        "untracked": tuple(sorted(_run_git(repo_root, ("ls-files", "--others", "--exclude-standard")).splitlines())),
        "porcelain": tuple(sorted(_run_git(repo_root, ("status", "--porcelain=v1", "--untracked-files=all")).splitlines())),
        "path_commits": path_commits,
        "live_paths": {relative: _live_identity(repo_root, relative) for relative in CANDIDATE_PATHS},
    }


def _derive_lifecycle(facts: object) -> dict[str, object]:
    try:
        if (
            type(facts) is not dict
            or facts.get("branch") != BRANCH
            or facts.get("base_ancestor_head") is not True
            or facts.get("base_ancestor_origin") is not True
            or type(facts.get("path_commits")) is not list
            or len(facts["path_commits"]) > 1
            or tuple(facts.get("live_paths", {})) != CANDIDATE_PATHS
        ):
            _fail()
        commits = facts["path_commits"]
        if not commits:
            if (
                facts["head"] != BASE_COMMIT or facts["origin"] != BASE_COMMIT
                or (facts["ahead"], facts["behind"]) != (0, 0)
                or facts["tracked"] or facts["staged"]
                or facts["untracked"] != CANDIDATE_PATHS
                or facts["porcelain"] != tuple(sorted(f"?? {path}" for path in CANDIDATE_PATHS))
                or any(item["tracked"] is not False for item in facts["live_paths"].values())
            ):
                _fail()
            return {
                "base_commit": BASE_COMMIT, "future_formal_subject": FORMAL_COMMIT_SUBJECT,
                "candidate_paths": list(CANDIDATE_PATHS),
                "lifecycle_profile": "partial_supervision_routing_gate_precommit_candidate",
                "formal_candidate_commit": "", "origin_main": BASE_COMMIT,
                "ahead": 0, "behind": 0,
            }
        commit = commits[0]
        if (
            not _is_hex(commit.get("commit")) or commit.get("parents") != [BASE_COMMIT]
            or commit.get("subject") != FORMAL_COMMIT_SUBJECT
            or commit.get("changed_paths") != CANDIDATE_PATHS
            or commit.get("changed_statuses") != {path: "A" for path in CANDIDATE_PATHS}
            or any(commit["path_modes"].get(path) != "100644" for path in CANDIDATE_PATHS)
            or commit.get("ancestor_head") is not True
            or any(
                facts["live_paths"][path] != {
                    "tracked": True, "mode": "100644",
                    "index_blob": commit["path_blobs"].get(path),
                    "blob": commit["path_blobs"].get(path),
                } for path in CANDIDATE_PATHS
            )
            or any(path in facts["tracked"] or path in facts["staged"] or path in facts["untracked"] for path in CANDIDATE_PATHS)
        ):
            _fail()
        common = {
            "base_commit": BASE_COMMIT, "future_formal_subject": FORMAL_COMMIT_SUBJECT,
            "candidate_paths": list(CANDIDATE_PATHS), "formal_candidate_commit": commit["commit"],
        }
        if commit.get("ancestor_origin") is True:
            return {
                **common,
                "lifecycle_profile": "partial_supervision_routing_gate_published_successor",
                "origin_main": facts["origin"], "ahead": facts["ahead"], "behind": facts["behind"],
            }
        if (
            facts["head"] != commit["commit"] or facts["origin"] != BASE_COMMIT
            or (facts["ahead"], facts["behind"]) != (1, 0)
            or facts["tracked"] or facts["staged"] or facts["untracked"] or facts["porcelain"]
        ):
            _fail()
        return {
            **common,
            "lifecycle_profile": "partial_supervision_routing_gate_committed_unpushed",
            "origin_main": BASE_COMMIT, "ahead": 1, "behind": 0,
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR_TOKEN:
            raise
        raise ValueError(ERROR_TOKEN) from error


def _validate_output_contract(response: object) -> None:
    try:
        if type(response) is not dict or tuple(response) != (
            "schema_version", "base_commit", "review_unit_id", "samples",
            "semantic_task_names", "eligibility_state_vocabulary", "canonical_mask_semantics",
            "source_bindings", "routing_records", "summary", "readiness", "repository_lifecycle",
        ):
            _fail()
        records = response["routing_records"]
        expected_samples = [
            {"sample_index_row_id": sample, "pdb_id": pdb, "ligand_comp_id": ligand}
            for sample, pdb, ligand, _event, _compound in SAMPLES
        ]
        if (
            response["schema_version"] != SCHEMA_VERSION
            or response["base_commit"] != BASE_COMMIT
            or response["review_unit_id"] != REVIEW_UNIT_ID
            or response["samples"] != expected_samples
            or type(records) is not list
            or len(records) != 50
            or records != _build_routing_records()
        ):
            _fail()
        record_keys = (
            "sample_index_row_id", "pdb_id", "ligand_comp_id", "semantic_task_name",
            "eligibility_state", "authority_basis", "evidence_scope", "supporting_source_ids",
            "blocking_gap", "safe_next_use", "availability_mask_required",
            "current_runtime_consumer_available", "training_loss_authorized",
        )
        source_ids = set(response["source_bindings"])
        for sample_index, sample in enumerate(SAMPLES):
            block = records[sample_index * 25:(sample_index + 1) * 25]
            if (
                tuple(record["semantic_task_name"] for record in block) != SEMANTIC_TASK_NAMES
                or any(record["sample_index_row_id"] != sample[0] for record in block)
            ):
                _fail()
        for record in records:
            if (
                tuple(record) != record_keys
                or record["eligibility_state"] not in ELIGIBILITY_STATE_VOCABULARY
                or type(record["supporting_source_ids"]) is not list
                or not set(record["supporting_source_ids"]).issubset(source_ids)
                or record["availability_mask_required"] is not True
                or record["current_runtime_consumer_available"] is not False
                or record["training_loss_authorized"] is not False
            ):
                _fail()
        if (
            tuple(response["semantic_task_names"]) != SEMANTIC_TASK_NAMES
            or tuple(response["eligibility_state_vocabulary"]) != ELIGIBILITY_STATE_VOCABULARY
            or tuple(
                (item.get("semantic_name"), item.get("display_alias"))
                for item in response["canonical_mask_semantics"]
            ) != CANONICAL_MASK_SEMANTICS
            or response["summary"] != _summary(records)
            or response["readiness"] != _readiness()
        ):
            _fail()
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR_TOKEN:
            raise
        raise ValueError(ERROR_TOKEN) from error


def evaluate_covapie_current11_unit_000001_partial_supervision_routing_gate_v1(
    *,
    repo_root: Path,
    state_root: Path,
) -> dict[str, object]:
    """Validate frozen evidence and return the deterministic Exact2 x Exact25 gate."""

    try:
        if (
            type(repo_root) is not _PATH_TYPE or type(state_root) is not _PATH_TYPE
            or not repo_root.is_absolute() or not state_root.is_absolute()
        ):
            _fail()
        repository = repo_root.resolve(strict=True)
        state = state_root.resolve(strict=True)
        if repository != repo_root or state != state_root or repository.is_symlink() or state.is_symlink():
            _fail()

        repo_payloads = {
            source_id: _read_frozen(repository, relative, digest)
            for source_id, (relative, digest) in REPO_SOURCES.items()
        }
        state_payloads = {
            source_id: _read_frozen(state, relative, digest)
            for source_id, (relative, digest) in STATE_SOURCES.items()
        }
        struct_conn = {
            SAMPLES[0][0]: _validate_struct_conn(repo_payloads["mmcif_1ayu"], ligand="INA", distance="1.799"),
            SAMPLES[1][0]: _validate_struct_conn(repo_payloads["mmcif_1ayw"], ligand="IN3", distance="1.794"),
        }
        pair = _validate_pair_evidence(repo_payloads)
        boundary = _validate_boundary_authority(state_payloads["unified_boundary_authority"])
        candidates = _validate_candidate_assignments(repo_payloads["candidate_family_assignments"])
        family = _validate_family_worklist(state_payloads["formal_family_rule_worklist"])
        worklist = _validate_transformation_worklist(state_payloads["formal_transformation_worklist"])
        literature = _validate_literature(
            state_payloads["primary_source_manifest"], state_payloads["primary_source_inventory"]
        )
        masks = _validate_masks(repo_payloads["canonical_mask_truth_table"])
        dossier = _validate_dossier(state)

        source_bindings: dict[str, object] = {}
        for source_id, (relative, digest) in REPO_SOURCES.items():
            source_bindings[source_id] = {
                "root": "repo_root", "relative_path": relative, "sha256": digest,
                "bytes": len(repo_payloads[source_id]), "read_only": True,
            }
        for source_id, (relative, digest) in STATE_SOURCES.items():
            source_bindings[source_id] = {
                "root": "state_root", "relative_path": relative, "sha256": digest,
                "bytes": len(state_payloads[source_id]), "read_only": True,
            }
        source_bindings["direct_evidence_validation"] = {
            "struct_conn_value_order": {sample: row["_struct_conn.pdbx_value_order"] for sample, row in struct_conn.items()},
            "pair_and_observed_geometry": pair,
            "boundary_authority": boundary,
            "candidate_family_and_warhead_type": candidates,
            "family_rule_approval": family,
            "formal_transformation_worklist": worklist,
            "literature_scope_projection": literature,
            "canonical_mask_exact5": masks,
            "formal_dossier": dossier,
        }

        records = _build_routing_records()
        response: dict[str, object] = {
            "schema_version": SCHEMA_VERSION,
            "base_commit": BASE_COMMIT,
            "review_unit_id": REVIEW_UNIT_ID,
            "samples": [
                {"sample_index_row_id": sample, "pdb_id": pdb, "ligand_comp_id": ligand}
                for sample, pdb, ligand, _event, _compound in SAMPLES
            ],
            "semantic_task_names": list(SEMANTIC_TASK_NAMES),
            "eligibility_state_vocabulary": list(ELIGIBILITY_STATE_VOCABULARY),
            "canonical_mask_semantics": masks,
            "source_bindings": source_bindings,
            "routing_records": records,
            "summary": _summary(records),
            "readiness": _readiness(),
            "repository_lifecycle": _derive_lifecycle(_collect_lifecycle(repository)),
        }
        _validate_output_contract(response)
        return response
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR_TOKEN:
            raise
        raise ValueError(ERROR_TOKEN) from error
