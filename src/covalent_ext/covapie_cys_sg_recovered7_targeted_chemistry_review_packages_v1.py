"""Build deterministic, authority-neutral recovered7 chemistry review packages.

This owner consumes the published recovered7 mechanical-closure evidence.  It
does not repeat structure recovery, infer reaction chemistry, or execute a
human decision.  Exact chemistry-signature equality is the only class reuse
criterion.
"""

from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from covalent_ext import (
    covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1
    as role_contract,
)


SCHEMA_VERSION = "covapie_cys_sg_recovered7_targeted_chemistry_review_packages_v1"
CHEMISTRY_REVIEW_SIGNATURE_VERSION = "covapie_recovered7_chemistry_review_signature_v1"
REVIEW_RECORD_VERSION = "covapie_recovered7_targeted_chemistry_review_record_v1"
PACKAGE_INDEX_VERSION = "covapie_recovered7_chemistry_review_package_index_v1"
PUBLISHED_CLOSURE_COMMIT = "68ff4ff290e6fa94d771491e05cd681f9305a661"

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_ROOT = Path(
    "/cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037/covapie-state"
)
OUTPUT_ROOT = Path("data/derived/covalent_small") / SCHEMA_VERSION
MANUAL_REVIEW_AID_ROOT = Path(
    "manual-review-aids/recovered7-targeted-chemistry-review-v1"
)

INDEX_FILE = "covapie_recovered7_chemistry_review_package_index.csv"
EVIDENCE_FILE = "covapie_recovered7_chemistry_review_package_evidence.json"
MANIFEST_FILE = "covapie_recovered7_chemistry_review_packages_manifest.json"
OUTPUT_FILES = (INDEX_FILE, EVIDENCE_FILE, MANIFEST_FILE)

CLOSURE_ROOT = Path("data/derived/covalent_small") / (
    "covapie_cys_sg_recovered7_canonical_topology_exact10_pocket_closure_v1"
)
CLOSURE_OWNER = Path("src/covalent_ext") / (
    "covapie_cys_sg_recovered7_canonical_topology_exact10_pocket_closure_v1.py"
)
CLOSURE_TEST = Path("tests") / (
    "test_covapie_cys_sg_recovered7_canonical_topology_exact10_pocket_closure_v1.py"
)
CLOSURE_MATRIX = CLOSURE_ROOT / "covapie_cys_sg_recovered7_canonical_closure_matrix.csv"
CLOSURE_EVIDENCE = CLOSURE_ROOT / (
    "covapie_cys_sg_recovered7_canonical_model_graph_and_pocket_evidence.json"
)
CLOSURE_MANIFEST = CLOSURE_ROOT / "covapie_cys_sg_recovered7_canonical_closure_manifest.json"

PUBLISHED_CLOSURE_SOURCE_HASHES = {
    CLOSURE_OWNER: "b52da9d5b1807d797fdb4571efd89504c0e0ddbc3f51acec1071e6a31027f069",
    CLOSURE_TEST: "3043026a1f81d0a1898034454eae4da2e7ee87e2c68c0a6487479f10a025c1e7",
    CLOSURE_MATRIX: "ee0ef9a33344f6204ebb6b54b3b6b1d6e8fe2956754efefbe76e71ba2214d796",
    CLOSURE_EVIDENCE: "c0a5196f94284bc78c49f1a981798c85b1fd5869237d54f30ba239321c3eb799",
    CLOSURE_MANIFEST: "334b6e95795f17d21d82ef341eeb9fa048d01f4eb826ac549a8251fcc5a13316",
}

CURRENT11_CANDIDATE_ASSIGNMENTS = Path(
    "data/derived/covalent_small/"
    "covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1/"
    "covapie_current11_cys_sg_candidate_assignment_authority.csv"
)
CURRENT11_EFFECTIVE_AUTHORITY = Path(
    "manual-review/covapie_current11_unified_effective_authority_view_v1.json"
)
REVIEWER_HINT_SOURCE_HASHES = {
    CURRENT11_CANDIDATE_ASSIGNMENTS: (
        "bc49e2f1ca112ceae30c91fa492386f6012c9005fc5137b40d3daec2343ef5d9"
    ),
    CURRENT11_EFFECTIVE_AUTHORITY: (
        "f4178987f3c3eed0e248f6d3d5f22cb8bce1839d39ab08aff0bff9d2ef9f3774"
    ),
}

REUSED_ARCHITECTURE = {
    "reaction_family_review_package": {
        "owner": "src/covalent_ext/covapie_current11_cys_sg_reaction_family_and_warhead_rule_review_packages_v1.py",
        "functions": [
            "unreviewed_template_payload_sha256",
            "_class_template",
            "_sample_template",
        ],
        "sha256": "052be7badc65a7eaeec1568e5954a2141a29c08bd0ef85c203e758daaa8b78ec",
    },
    "warhead_boundary_review_package": {
        "owner": "src/covalent_ext/covapie_current11_warhead_atom_set_and_attachment_boundary_review_packages_v1.py",
        "functions": [
            "review_record_sha256",
            "unreviewed_template_payload_sha256",
            "validate_review_record",
        ],
        "sha256": "7534a11b6c29f3d5d3268de34773e1d2ca5075624dbf05e30672705fa294e6c0",
    },
    "role_review_package": {
        "owner": "src/covalent_ext/covapie_current11_trainable_supervision_materializer_v1.py",
        "functions": [
            "build_current11_role_seed_review_packet_v1",
            "write_current11_role_seed_review_packet_v1",
        ],
        "sha256": "0dddcb645dc26eacc864fa2c6b59db5cbd34ed2da3e8bf7abb26d5daee9672ff",
    },
    "role_partition_contract": {
        "owner": "src/covalent_ext/covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py",
        "functions": ["validate_exact3_partition"],
        "sha256": "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b",
    },
    "submission_compiler": {
        "owner": "src/covalent_ext/covapie_current11_real_human_review_submission_bundle_compiler_v1.py",
        "functions": [
            "compile_covapie_current11_real_human_review_submission_bundle_v1"
        ],
        "sha256": "d9d76dd1538e4e929d988f3ad39f11bf390b2ffbb9158ed93238604f4457791d",
    },
    "ingestion_execution": {
        "owner": "src/covalent_ext/covapie_current11_real_human_review_ingestion_execution_bundle_v1.py",
        "functions": [
            "build_covapie_current11_real_human_review_ingestion_execution_bundle_v1"
        ],
        "sha256": "78d0124c7fba182f75542a128ee7a2707580e7f05dcbdc24103eae5bebbb969c",
    },
    "effective_authority": {
        "owner": "src/covalent_ext/covapie_current11_unified_effective_authority_view_v1.py",
        "functions": ["build_covapie_current11_unified_effective_authority_view_v1"],
        "sha256": "c8f2af8fc0d5dd2f8c42e527cc3db34620b2992f567d59f32a19842254dac4f4",
    },
}

RECOVERED_IDENTITIES = (
    "2DJF/1ZB",
    "2R9F/K2Z",
    "4DCD/K36",
    "6WTT/K36",
    "4F49/K36",
    "6L70/K36",
    "5WKJ/K36",
)
UNRESOLVED_STRUCTURAL_REVIEW_IDENTITIES = frozenset(
    ("1A54/MDC", "6VWE/JY1", "6WTJ/K36", "7C8U/K36", "6WTK/UED")
)

REVIEW_SCOPES = (
    "NOT_REVIEWED",
    "EXACT_CHEMISTRY_SIGNATURE_REUSABLE",
    "SAMPLE_BOUND_ONLY",
    "QUARANTINE",
)
AUTHORITY_ACTIONS = ("", "USE_EXISTING_REVIEWED_ID", "NEW_AUTHORITY_REQUIRED")
UNRESOLVED_AUTHORITY_DIMENSIONS = (
    "reaction_family",
    "warhead_rule_or_warhead_chemistry",
    "warhead_heavy_atom_set",
    "warhead_attachment_atom",
    "nonwarhead_boundary_atom",
    "attachment_boundary_bond_and_order",
    "scaffold_atom_set",
    "linker_atom_set",
    "warhead_role_atom_set",
    "minimal_seed_atom_set",
    "review_scope",
)

REVIEW_RECORD_FIELDS = (
    "review_record_version",
    "review_class_id",
    "chemistry_review_signature_sha256",
    "review_class_member_count",
    "review_class_member_identities",
    "review_status",
    "review_scope",
    "reviewed_sample_bound_member_identity",
    "reviewed_reaction_family_authority_action",
    "reviewed_reaction_family_id",
    "reviewed_warhead_rule_authority_action",
    "reviewed_warhead_rule_id",
    "reviewed_warhead_atom_ids",
    "reviewed_warhead_attachment_atom_id",
    "reviewed_nonwarhead_boundary_atom_id",
    "reviewed_attachment_boundary_bond_order",
    "reviewed_scaffold_atom_ids",
    "reviewed_linker_atom_ids",
    "reviewed_warhead_role_atom_ids",
    "reviewed_minimal_seed_atom_ids",
    "reviewer_id",
    "review_rationale",
    "review_notes",
    "review_record_sha256",
)
REVIEW_LIST_FIELDS = frozenset(
    (
        "review_class_member_identities",
        "reviewed_warhead_atom_ids",
        "reviewed_scaffold_atom_ids",
        "reviewed_linker_atom_ids",
        "reviewed_warhead_role_atom_ids",
        "reviewed_minimal_seed_atom_ids",
    )
)
REVIEW_INT_FIELDS = frozenset(("review_class_member_count",))
DECISION_FIELDS = (
    "reviewed_sample_bound_member_identity",
    "reviewed_reaction_family_authority_action",
    "reviewed_reaction_family_id",
    "reviewed_warhead_rule_authority_action",
    "reviewed_warhead_rule_id",
    "reviewed_warhead_atom_ids",
    "reviewed_warhead_attachment_atom_id",
    "reviewed_nonwarhead_boundary_atom_id",
    "reviewed_attachment_boundary_bond_order",
    "reviewed_scaffold_atom_ids",
    "reviewed_linker_atom_ids",
    "reviewed_warhead_role_atom_ids",
    "reviewed_minimal_seed_atom_ids",
)

INDEX_COLUMNS = (
    "package_index_version",
    "package_item_order_0based",
    "canonical_candidate_id",
    "sample_identity",
    "pdb_id",
    "ligand_component_id",
    "review_class_id",
    "chemistry_review_signature_sha256",
    "review_class_member_count",
    "review_class_representative_identity",
    "sample_applicability_record_sha256",
    "current_downstream_status",
    "current_primary_issue",
    "manual_review_required",
    "human_decision_redundant_with_class_if_reusable_scope",
    "review_status",
)

ATOM_BOND_TABLE_COLUMNS = (
    "record_type",
    "atom_id",
    "element",
    "observed_reaction_state",
    "topology_heavy_atom_not_observed",
    "reactive_ligand_atom",
    "bond_atom_id_1",
    "bond_atom_id_2",
    "bond_order",
    "bond_incident_to_reactive_atom",
    "bond_incident_to_unobserved_atom",
    "evidence_note",
)

_FORBIDDEN_SIGNATURE_KEYS = frozenset(
    (
        "pdb_id",
        "coordinates",
        "x",
        "y",
        "z",
        "protein_chain",
        "protein_residue_number",
        "auth_asym_id",
        "label_asym_id",
        "auth_seq_id",
        "label_seq_id",
        "source_atom_site_row_index_0based",
        "atom_site_id",
        "altloc",
        "label_alt_id",
        "occupancy",
        "selected_model",
    )
)
_FORBIDDEN_REVIEWER_IDS = frozenset(("codex", "openai", "chatgpt", "gpt"))


class ReviewPackageValidationError(ValueError):
    """Raised when a frozen package or future review record fails closed."""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _cell(value: object) -> object:
    if type(value) in (list, dict):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    if type(value) is bool:
        return str(value).lower()
    return value


def _csv_bytes(columns: Sequence[str], rows: Iterable[Mapping[str, Any]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer, fieldnames=columns, extrasaction="raise", lineterminator="\n"
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({field: _cell(row[field]) for field in columns})
    return buffer.getvalue().encode("utf-8")


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _utf8_sorted(values: Iterable[str]) -> list[str]:
    return sorted(values, key=lambda value: value.encode("utf-8"))


def _canonical_bond(left: str, right: str, order: str) -> dict[str, str]:
    first, second = _utf8_sorted((left, right))
    return {"atom_id_1": first, "atom_id_2": second, "bond_order": order}


def _read_sha_bound(path: Path, expected_sha256: str) -> bytes:
    payload = path.read_bytes()
    if _sha256(payload) != expected_sha256:
        raise ReviewPackageValidationError(f"SOURCE_SHA256_MISMATCH:{path.as_posix()}")
    return payload


def _repo_source(repo_root: Path, path: Path) -> Path:
    return repo_root / path


def _state_source(state_root: Path, path: Path) -> Path:
    return state_root / path


def validate_published_source_bindings_v1(
    repo_root: Path = REPO_ROOT, state_root: Path = STATE_ROOT
) -> dict[str, bytes]:
    """Read and SHA-bind closure products and the audited reusable architecture."""

    payloads: dict[str, bytes] = {}
    for relative, expected in PUBLISHED_CLOSURE_SOURCE_HASHES.items():
        payloads[relative.as_posix()] = _read_sha_bound(
            _repo_source(repo_root, relative), expected
        )
    for record in REUSED_ARCHITECTURE.values():
        relative = Path(record["owner"])
        payloads[relative.as_posix()] = _read_sha_bound(
            _repo_source(repo_root, relative), record["sha256"]
        )
    payloads[CURRENT11_CANDIDATE_ASSIGNMENTS.as_posix()] = _read_sha_bound(
        _repo_source(repo_root, CURRENT11_CANDIDATE_ASSIGNMENTS),
        REVIEWER_HINT_SOURCE_HASHES[CURRENT11_CANDIDATE_ASSIGNMENTS],
    )
    payloads[f"covapie-state/{CURRENT11_EFFECTIVE_AUTHORITY.as_posix()}"] = (
        _read_sha_bound(
            _state_source(state_root, CURRENT11_EFFECTIVE_AUTHORITY),
            REVIEWER_HINT_SOURCE_HASHES[CURRENT11_EFFECTIVE_AUTHORITY],
        )
    )
    return payloads


def _contains_key(value: object, target: str) -> bool:
    if type(value) is dict:
        return target in value or any(_contains_key(item, target) for item in value.values())
    if type(value) is list:
        return any(_contains_key(item, target) for item in value)
    return False


def _reviewer_hint_search_summary(
    payloads: Mapping[str, bytes], recovered_components: set[str]
) -> dict[str, Any]:
    candidate_rows = _csv_rows(payloads[CURRENT11_CANDIDATE_ASSIGNMENTS.as_posix()])
    effective = json.loads(
        payloads[f"covapie-state/{CURRENT11_EFFECTIVE_AUTHORITY.as_posix()}"]
    )
    candidate_components = {row["ligand_comp_id"] for row in candidate_rows}
    effective_components = {
        wrapper["effective_authority_record"]["ligand_comp_id"]
        for wrapper in effective["effective_authority_records"]
    }
    candidate_overlap = _utf8_sorted(candidate_components & recovered_components)
    effective_overlap = _utf8_sorted(effective_components & recovered_components)
    return {
        "candidate_record_count_searched": len(candidate_rows),
        "effective_human_authority_record_count_searched": len(
            effective["effective_authority_records"]
        ),
        "recovered_component_ids": _utf8_sorted(recovered_components),
        "candidate_component_id_overlap": candidate_overlap,
        "effective_human_component_id_overlap": effective_overlap,
        "candidate_source_contains_semantic_topology_sha256": _contains_key(
            candidate_rows, "semantic_topology_sha256"
        ),
        "effective_source_contains_semantic_topology_sha256": _contains_key(
            effective, "semantic_topology_sha256"
        ),
        "exact_current11_chemistry_signature_match_count": 0,
        "prior_reference_authority_class": "NONE",
        "conclusion": (
            "NONE; no exact deterministic Current11 chemistry-signature reference "
            "is available, and component identity alone is not accepted"
        ),
    }


def _assert_signature_has_no_sample_identity(value: object) -> None:
    if type(value) is dict:
        forbidden = set(value) & _FORBIDDEN_SIGNATURE_KEYS
        if forbidden:
            raise ReviewPackageValidationError(
                "CHEMISTRY_SIGNATURE_CONTAINS_SAMPLE_IDENTITY:"
                + ",".join(_utf8_sorted(forbidden))
            )
        for item in value.values():
            _assert_signature_has_no_sample_identity(item)
    elif type(value) is list:
        for item in value:
            _assert_signature_has_no_sample_identity(item)


def derive_chemistry_review_signature_v1(
    sample: Mapping[str, Any], topology: Mapping[str, Any]
) -> dict[str, Any]:
    """Project published evidence to chemistry identity, excluding coordinates."""

    component_id = sample["ligand_component_id"]
    if component_id != topology["component_id"]:
        raise ReviewPackageValidationError("SIGNATURE_COMPONENT_TOPOLOGY_MISMATCH")
    topology_atoms = {
        atom["atom_id"]: atom["type_symbol"]
        for atom in topology["component_atoms"]
        if atom["explicit_hydrogen"] is False
    }
    observed_atoms = {
        atom["label_atom_id"]: atom["type_symbol"]
        for atom in sample["canonical_model_bound_ligand_atoms"]
    }
    if len(observed_atoms) != len(sample["canonical_model_bound_ligand_atoms"]):
        raise ReviewPackageValidationError("OBSERVED_HEAVY_ATOM_NAME_NOT_UNIQUE")
    missing = _utf8_sorted(set(topology_atoms) - set(observed_atoms))
    if missing != sample["topology_mapping"]["topology_heavy_atoms_not_observed"]:
        raise ReviewPackageValidationError("PUBLISHED_MISSING_HEAVY_ATOM_SET_DRIFT")
    if any(topology_atoms.get(atom_id) != element for atom_id, element in observed_atoms.items()):
        raise ReviewPackageValidationError("OBSERVED_TOPOLOGY_ELEMENT_MISMATCH")

    topology_inventory = [
        {"atom_id": atom_id, "element": topology_atoms[atom_id]}
        for atom_id in _utf8_sorted(topology_atoms)
    ]
    observed_inventory = [
        {"atom_id": atom_id, "element": observed_atoms[atom_id]}
        for atom_id in _utf8_sorted(observed_atoms)
    ]
    bonds = []
    for bond in topology["component_internal_bonds"]:
        if bond["atom_id_1"] in topology_atoms and bond["atom_id_2"] in topology_atoms:
            bonds.append(
                _canonical_bond(
                    bond["atom_id_1"],
                    bond["atom_id_2"],
                    bond["normalized_bond_order"],
                )
            )
    bonds.sort(
        key=lambda row: (
            row["atom_id_1"].encode("utf-8"),
            row["atom_id_2"].encode("utf-8"),
            row["bond_order"].encode("utf-8"),
        )
    )
    event = sample["explicit_event"]
    protein = event["protein_endpoint"]
    ligand = event["ligand_endpoint"]
    signature = {
        "chemistry_review_signature_version": CHEMISTRY_REVIEW_SIGNATURE_VERSION,
        "ligand_component_id": component_id,
        "semantic_topology_sha256": topology["semantic_topology_sha256"],
        "reactive_residue": "CYS",
        "reactive_residue_atom": protein["auth_atom_id"],
        "reactive_residue_atom_element": protein["type_symbol"],
        "reactive_ligand_atom": ligand["auth_atom_id"],
        "reactive_ligand_atom_element": ligand["type_symbol"],
        "canonical_model_bound_ligand_heavy_atom_inventory": observed_inventory,
        "topology_heavy_atom_inventory": topology_inventory,
        "topology_heavy_atoms_not_observed": missing,
        "canonical_internal_heavy_heavy_bond_graph_with_bond_orders": bonds,
        "reaction_specific_post_graph_proven": topology[
            "reaction_specific_post_graph_proven"
        ],
        "explicit_covalent_event": {
            "event_type": "CYS_SG_TO_LIGAND_REACTIVE_ATOM_EXPLICIT_COVALENT_EDGE",
            "evidence_kind": event["protein_ligand_covalent_event_edge"][
                "evidence_kind"
            ],
            "residue_component_id": protein["auth_comp_id"],
            "residue_atom_id": protein["auth_atom_id"],
            "residue_atom_element": protein["type_symbol"],
            "ligand_component_id": ligand["auth_comp_id"],
            "ligand_atom_id": ligand["auth_atom_id"],
            "ligand_atom_element": ligand["type_symbol"],
            "component_internal_topology_edge": False,
        },
    }
    if signature["reactive_residue_atom"] != "SG":
        raise ReviewPackageValidationError("REACTIVE_RESIDUE_ATOM_NOT_SG")
    if signature["reaction_specific_post_graph_proven"] is not False:
        raise ReviewPackageValidationError("REACTION_SPECIFIC_POST_GRAPH_UNEXPECTED")
    _assert_signature_has_no_sample_identity(signature)
    return signature


def chemistry_review_signature_sha256_v1(signature: Mapping[str, Any]) -> str:
    _assert_signature_has_no_sample_identity(signature)
    return _sha256(_canonical_json_bytes(signature))


def group_exact_chemistry_review_signatures_v1(
    signatures_by_identity: Mapping[str, Mapping[str, Any]]
) -> dict[str, list[str]]:
    """Group solely by the complete canonical signature digest."""

    groups: dict[str, list[str]] = defaultdict(list)
    for identity, signature in signatures_by_identity.items():
        groups[chemistry_review_signature_sha256_v1(signature)].append(identity)
    return {
        digest: _utf8_sorted(members)
        for digest, members in sorted(groups.items(), key=lambda item: item[0])
    }


def sample_applicability_record_sha256_v1(record: Mapping[str, Any]) -> str:
    if "applicability_record_sha256" not in record:
        raise ReviewPackageValidationError("APPLICABILITY_SHA_FIELD_MISSING")
    return _sha256(
        _canonical_json_bytes(
            {
                key: value
                for key, value in record.items()
                if key != "applicability_record_sha256"
            }
        )
    )


def review_record_sha256_v1(record: Mapping[str, Any]) -> str:
    validate_review_record_schema_v1(record)
    return _sha256(
        _canonical_json_bytes(
            {
                field: record[field]
                for field in REVIEW_RECORD_FIELDS
                if field != "review_record_sha256"
            }
        )
    )


def validate_review_record_schema_v1(record: Mapping[str, Any]) -> None:
    if type(record) is not dict or tuple(record) != REVIEW_RECORD_FIELDS:
        raise ReviewPackageValidationError("REVIEW_RECORD_FIELD_INVENTORY_INVALID")
    for field in REVIEW_RECORD_FIELDS:
        value = record[field]
        if field in REVIEW_LIST_FIELDS:
            if type(value) is not list or any(type(item) is not str for item in value):
                raise ReviewPackageValidationError(f"REVIEW_LIST_FIELD_INVALID:{field}")
            if value != _utf8_sorted(value) or len(value) != len(set(value)):
                raise ReviewPackageValidationError(f"REVIEW_LIST_NOT_SORTED_UNIQUE:{field}")
        elif field in REVIEW_INT_FIELDS:
            if type(value) is not int or value < 1:
                raise ReviewPackageValidationError(f"REVIEW_INT_FIELD_INVALID:{field}")
        elif type(value) is not str:
            raise ReviewPackageValidationError(f"REVIEW_STRING_FIELD_INVALID:{field}")
    if record["review_record_version"] != REVIEW_RECORD_VERSION:
        raise ReviewPackageValidationError("REVIEW_RECORD_VERSION_MISMATCH")
    if record["review_scope"] not in REVIEW_SCOPES:
        raise ReviewPackageValidationError("REVIEW_SCOPE_INVALID")
    if record["reviewed_reaction_family_authority_action"] not in AUTHORITY_ACTIONS:
        raise ReviewPackageValidationError("REACTION_FAMILY_ACTION_INVALID")
    if record["reviewed_warhead_rule_authority_action"] not in AUTHORITY_ACTIONS:
        raise ReviewPackageValidationError("WARHEAD_RULE_ACTION_INVALID")


def make_blank_review_record_v1(review_class: Mapping[str, Any]) -> dict[str, Any]:
    record = {
        "review_record_version": REVIEW_RECORD_VERSION,
        "review_class_id": review_class["review_class_id"],
        "chemistry_review_signature_sha256": review_class[
            "chemistry_review_signature_sha256"
        ],
        "review_class_member_count": review_class["member_sample_count"],
        "review_class_member_identities": list(review_class["member_sample_identities"]),
        "review_status": "NOT_REVIEWED",
        "review_scope": "NOT_REVIEWED",
        "reviewed_sample_bound_member_identity": "",
        "reviewed_reaction_family_authority_action": "",
        "reviewed_reaction_family_id": "",
        "reviewed_warhead_rule_authority_action": "",
        "reviewed_warhead_rule_id": "",
        "reviewed_warhead_atom_ids": [],
        "reviewed_warhead_attachment_atom_id": "",
        "reviewed_nonwarhead_boundary_atom_id": "",
        "reviewed_attachment_boundary_bond_order": "",
        "reviewed_scaffold_atom_ids": [],
        "reviewed_linker_atom_ids": [],
        "reviewed_warhead_role_atom_ids": [],
        "reviewed_minimal_seed_atom_ids": [],
        "reviewer_id": "",
        "review_rationale": "",
        "review_notes": "",
        "review_record_sha256": "",
    }
    validate_review_record_schema_v1(record)
    validate_unreviewed_template_v1(record)
    return record


def validate_unreviewed_template_v1(record: Mapping[str, Any]) -> None:
    validate_review_record_schema_v1(record)
    if record["review_status"] != "NOT_REVIEWED" or record["review_scope"] != "NOT_REVIEWED":
        raise ReviewPackageValidationError("UNREVIEWED_STATUS_OR_SCOPE_INVALID")
    for field in DECISION_FIELDS:
        if record[field] not in ("", []):
            raise ReviewPackageValidationError(f"UNREVIEWED_DECISION_PREFILLED:{field}")
    if any(record[field] for field in ("reviewer_id", "review_rationale", "review_notes")):
        raise ReviewPackageValidationError("UNREVIEWED_HUMAN_TEXT_PREFILLED")
    if record["review_record_sha256"]:
        raise ReviewPackageValidationError("UNREVIEWED_RECORD_SHA_PREFILLED")


def parse_review_record_csv_v1(row: Mapping[str, str]) -> dict[str, Any]:
    if tuple(row) != REVIEW_RECORD_FIELDS:
        raise ReviewPackageValidationError("REVIEW_CSV_FIELD_INVENTORY_INVALID")
    record: dict[str, Any] = {}
    for field in REVIEW_RECORD_FIELDS:
        if field in REVIEW_LIST_FIELDS:
            try:
                value = json.loads(row[field])
            except json.JSONDecodeError as error:
                raise ReviewPackageValidationError(
                    f"REVIEW_CSV_LIST_JSON_INVALID:{field}"
                ) from error
            record[field] = value
        elif field in REVIEW_INT_FIELDS:
            if not row[field].isdecimal():
                raise ReviewPackageValidationError(f"REVIEW_CSV_INT_INVALID:{field}")
            record[field] = int(row[field])
        else:
            record[field] = row[field]
    validate_review_record_schema_v1(record)
    return record


def _meaningful(value: object) -> bool:
    return type(value) is str and bool(value.strip())


def _validate_authority_action(record: Mapping[str, Any], action_field: str, id_field: str) -> None:
    action = record[action_field]
    identifier = record[id_field]
    if action == "USE_EXISTING_REVIEWED_ID":
        if not _meaningful(identifier):
            raise ReviewPackageValidationError(f"EXISTING_AUTHORITY_ID_REQUIRED:{id_field}")
    elif action == "NEW_AUTHORITY_REQUIRED":
        if identifier:
            raise ReviewPackageValidationError(f"NEW_AUTHORITY_ID_MUST_BE_BLANK:{id_field}")
    else:
        raise ReviewPackageValidationError(f"COMPLETED_AUTHORITY_ACTION_REQUIRED:{action_field}")


def _topology_graph(review_class: Mapping[str, Any]) -> tuple[list[str], list[dict[str, str]]]:
    signature = review_class["chemistry_review_signature"]
    atoms = [row["atom_id"] for row in signature["topology_heavy_atom_inventory"]]
    bonds = signature["canonical_internal_heavy_heavy_bond_graph_with_bond_orders"]
    return atoms, bonds


def _validate_connected_seed(
    seed: Sequence[str], scaffold: Sequence[str], bonds: Sequence[Mapping[str, str]]
) -> None:
    seed_set = set(seed)
    scaffold_set = set(scaffold)
    if not seed_set:
        raise ReviewPackageValidationError("MINIMAL_SEED_EMPTY")
    if len(seed) not in (2, 3):
        raise ReviewPackageValidationError("MINIMAL_SEED_SIZE_NOT_2_OR_3")
    if not seed_set <= scaffold_set:
        raise ReviewPackageValidationError("MINIMAL_SEED_OUTSIDE_SCAFFOLD")
    adjacency = {atom: set() for atom in seed_set}
    for bond in bonds:
        left = bond["atom_id_1"]
        right = bond["atom_id_2"]
        if left in seed_set and right in seed_set:
            adjacency[left].add(right)
            adjacency[right].add(left)
    visited: set[str] = set()
    queue: deque[str] = deque([seed[0]])
    while queue:
        atom = queue.popleft()
        if atom not in visited:
            visited.add(atom)
            queue.extend(_utf8_sorted(adjacency[atom] - visited))
    if visited != seed_set:
        raise ReviewPackageValidationError("MINIMAL_SEED_DISCONNECTED")


def validate_completed_review_record_v1(
    record: Mapping[str, Any],
    review_class: Mapping[str, Any],
    *,
    applicability_signatures: Sequence[str] = (),
) -> None:
    """Validate a synthetic future record; this function never creates authority."""

    validate_review_record_schema_v1(record)
    if record["review_status"] != "COMPLETED":
        raise ReviewPackageValidationError("COMPLETED_REVIEW_STATUS_REQUIRED")
    for field in (
        "review_class_id",
        "chemistry_review_signature_sha256",
        "review_class_member_count",
        "review_class_member_identities",
    ):
        expected_field = {
            "review_class_member_count": "member_sample_count",
            "review_class_member_identities": "member_sample_identities",
        }.get(field, field)
        if record[field] != review_class[expected_field]:
            raise ReviewPackageValidationError(f"REVIEW_CLASS_BINDING_MISMATCH:{field}")
    if not _meaningful(record["reviewer_id"]):
        raise ReviewPackageValidationError("REVIEWER_ID_REQUIRED")
    if record["reviewer_id"].strip().casefold() in _FORBIDDEN_REVIEWER_IDS:
        raise ReviewPackageValidationError("FORBIDDEN_REVIEWER_ID")
    if not _meaningful(record["review_rationale"]):
        raise ReviewPackageValidationError("REVIEW_RATIONALE_REQUIRED")
    if record["review_notes"] and not _meaningful(record["review_notes"]):
        raise ReviewPackageValidationError("REVIEW_NOTES_NOT_MEANINGFUL")
    if record["review_scope"] == "QUARANTINE":
        for field in DECISION_FIELDS:
            if record[field] not in ("", []):
                raise ReviewPackageValidationError(f"QUARANTINE_DECISION_PREFILLED:{field}")
    elif record["review_scope"] in (
        "EXACT_CHEMISTRY_SIGNATURE_REUSABLE",
        "SAMPLE_BOUND_ONLY",
    ):
        if record["review_scope"] == "EXACT_CHEMISTRY_SIGNATURE_REUSABLE":
            if record["reviewed_sample_bound_member_identity"]:
                raise ReviewPackageValidationError("REUSABLE_SCOPE_SAMPLE_BINDING_FORBIDDEN")
            if any(
                signature != record["chemistry_review_signature_sha256"]
                for signature in applicability_signatures
            ):
                raise ReviewPackageValidationError("REUSABLE_SCOPE_SIGNATURE_MISMATCH")
        else:
            if record["reviewed_sample_bound_member_identity"] not in record[
                "review_class_member_identities"
            ]:
                raise ReviewPackageValidationError("SAMPLE_BOUND_MEMBER_INVALID")
        _validate_authority_action(
            record,
            "reviewed_reaction_family_authority_action",
            "reviewed_reaction_family_id",
        )
        _validate_authority_action(
            record,
            "reviewed_warhead_rule_authority_action",
            "reviewed_warhead_rule_id",
        )
        topology_atoms, bonds = _topology_graph(review_class)
        topology_set = set(topology_atoms)
        signature = review_class["chemistry_review_signature"]
        retained = [
            row["atom_id"]
            for row in signature["canonical_model_bound_ligand_heavy_atom_inventory"]
        ]
        reactive = signature["reactive_ligand_atom"]
        warhead_atoms = record["reviewed_warhead_atom_ids"]
        if not warhead_atoms or not set(warhead_atoms) <= topology_set:
            raise ReviewPackageValidationError("WARHEAD_ATOM_SET_OUTSIDE_TOPOLOGY")
        if reactive not in warhead_atoms:
            raise ReviewPackageValidationError("REACTIVE_ATOM_OUTSIDE_WARHEAD_ATOM_SET")
        attachment = record["reviewed_warhead_attachment_atom_id"]
        nonwarhead = record["reviewed_nonwarhead_boundary_atom_id"]
        order = record["reviewed_attachment_boundary_bond_order"]
        if attachment not in topology_set or nonwarhead not in topology_set:
            raise ReviewPackageValidationError("BOUNDARY_ATOM_NOT_IN_GRAPH")
        if attachment not in warhead_atoms:
            raise ReviewPackageValidationError("WARHEAD_ATTACHMENT_OUTSIDE_WARHEAD_SET")
        if nonwarhead in warhead_atoms or attachment == nonwarhead:
            raise ReviewPackageValidationError("NONWARHEAD_BOUNDARY_IN_WARHEAD_SET")
        boundary = _canonical_bond(attachment, nonwarhead, order)
        if boundary not in bonds:
            raise ReviewPackageValidationError("BOUNDARY_BOND_NOT_IN_GRAPH")

        atom_to_index = {atom: index for index, atom in enumerate(retained)}
        role_names = (
            record["reviewed_scaffold_atom_ids"],
            record["reviewed_linker_atom_ids"],
            record["reviewed_warhead_role_atom_ids"],
        )
        if any(any(atom not in atom_to_index for atom in values) for values in role_names):
            raise ReviewPackageValidationError("ROLE_ATOM_OUTSIDE_RETAINED_HEAVY_ATOMS")
        partition_reasons = role_contract.validate_exact3_partition(
            list(range(len(retained))),
            [atom_to_index[atom] for atom in role_names[0]],
            [atom_to_index[atom] for atom in role_names[1]],
            [atom_to_index[atom] for atom in role_names[2]],
        )
        if partition_reasons:
            raise ReviewPackageValidationError(
                "ROLE_PARTITION_INVALID:" + ";".join(partition_reasons)
            )
        if reactive not in record["reviewed_warhead_role_atom_ids"]:
            raise ReviewPackageValidationError("REACTIVE_ATOM_OUTSIDE_WARHEAD_ROLE")
        _validate_connected_seed(
            record["reviewed_minimal_seed_atom_ids"],
            record["reviewed_scaffold_atom_ids"],
            bonds,
        )
    else:
        raise ReviewPackageValidationError("COMPLETED_REVIEW_SCOPE_REQUIRED")
    if not record["review_record_sha256"]:
        raise ReviewPackageValidationError("COMPLETED_REVIEW_SHA_REQUIRED")
    if record["review_record_sha256"] != review_record_sha256_v1(record):
        raise ReviewPackageValidationError("COMPLETED_REVIEW_SHA_MISMATCH")


def _local_reaction_evidence(signature: Mapping[str, Any]) -> dict[str, Any]:
    reactive = signature["reactive_ligand_atom"]
    missing = set(signature["topology_heavy_atoms_not_observed"])
    bonds = signature["canonical_internal_heavy_heavy_bond_graph_with_bond_orders"]
    return {
        "component_bonds_incident_to_reactive_atom": [
            bond
            for bond in bonds
            if reactive in (bond["atom_id_1"], bond["atom_id_2"])
        ],
        "component_bonds_incident_to_topology_heavy_atoms_not_observed": [
            bond
            for bond in bonds
            if bond["atom_id_1"] in missing or bond["atom_id_2"] in missing
        ],
        "explicit_covalent_event_edge": signature["explicit_covalent_event"],
        "interpretation_boundary": (
            "reaction-state evidence only; no leaving group, inverse reaction, PRE "
            "bond order, formal-charge change, proton transfer, or mechanism inferred"
        ),
    }


def _sample_identity(sample: Mapping[str, Any]) -> str:
    return f"{sample['pdb_id']}/{sample['ligand_component_id']}"


def _sample_applicability(
    sample: Mapping[str, Any],
    matrix_row: Mapping[str, str],
    review_class_id: str,
    signature_sha256: str,
) -> dict[str, Any]:
    event = sample["explicit_event"]
    ligand = event["ligand_endpoint"]
    protein = event["protein_endpoint"]
    mapping = sample["topology_mapping"]
    record = {
        "canonical_candidate_id": sample["canonical_candidate_id"],
        "sample_identity": _sample_identity(sample),
        "pdb_id": sample["pdb_id"],
        "ligand_component_id": sample["ligand_component_id"],
        "review_class_id": review_class_id,
        "chemistry_review_signature_sha256": signature_sha256,
        "raw_sha256": sample["raw_source"]["sha256"],
        "event_mapping_status": event["event_mapping_status"],
        "reactive_residue_atom": protein["auth_atom_id"],
        "reactive_ligand_atom": ligand["auth_atom_id"],
        "ligand_instance_identity": {
            "auth_asym_id": ligand["auth_asym_id"],
            "auth_seq_id": ligand["auth_seq_id"],
            "auth_component_id": ligand["auth_comp_id"],
            "label_asym_id": ligand["label_asym_id"],
            "label_seq_id": ligand["label_seq_id"],
        },
        "selected_model": mapping["selected_ligand_model"],
        "selected_altloc": mapping["selected_ligand_altloc"],
        "altloc_occupancy_provenance": event["altloc_occupancy_provenance"],
        "mechanical_closure_status": sample["mechanical_closure_status"],
        "exact10_status": sample["exact10"]["status"],
        "pocket_status": matrix_row["pocket_status"],
        "sample_matches_review_class_signature": True,
        "applicability_status": (
            "EXACT_CHEMISTRY_SIGNATURE_MATCH_AND_MECHANICAL_CLOSURE_PASS"
        ),
        "applicability_record_sha256": "",
    }
    record["applicability_record_sha256"] = sample_applicability_record_sha256_v1(
        record
    )
    return record


def _source_provenance() -> dict[str, Any]:
    return {
        "published_closure_commit": PUBLISHED_CLOSURE_COMMIT,
        "published_closure_source_hashes": {
            path.as_posix(): digest
            for path, digest in PUBLISHED_CLOSURE_SOURCE_HASHES.items()
        },
        "reviewer_hint_source_hashes": {
            (
                path.as_posix()
                if path != CURRENT11_EFFECTIVE_AUTHORITY
                else f"covapie-state/{path.as_posix()}"
            ): digest
            for path, digest in REVIEWER_HINT_SOURCE_HASHES.items()
        },
        "reused_review_architecture": copy.deepcopy(REUSED_ARCHITECTURE),
    }


def build_package_model_v1(
    repo_root: Path = REPO_ROOT, state_root: Path = STATE_ROOT
) -> dict[str, Any]:
    payloads = validate_published_source_bindings_v1(repo_root, state_root)
    manifest = json.loads(payloads[CLOSURE_MANIFEST.as_posix()])
    evidence = json.loads(payloads[CLOSURE_EVIDENCE.as_posix()])
    matrix_rows = _csv_rows(payloads[CLOSURE_MATRIX.as_posix()])
    if (
        manifest.get("recovered_candidate_count") != 7
        or manifest.get("mechanical_closure_pass_count") != 7
        or manifest.get("downstream_human_chemistry_review_required_count") != 7
        or manifest.get("ready_for_targeted_chemistry_review_package_generation")
        is not True
    ):
        raise ReviewPackageValidationError("PUBLISHED_CLOSURE_NOT_REVIEW_PACKAGE_READY")
    samples = evidence.get("samples")
    if type(samples) is not list or len(samples) != 7 or len(matrix_rows) != 7:
        raise ReviewPackageValidationError("REVIEW_POPULATION_COUNT_INVALID")
    identities = tuple(_sample_identity(sample) for sample in samples)
    if identities != RECOVERED_IDENTITIES:
        raise ReviewPackageValidationError("REVIEW_POPULATION_IDENTITY_DRIFT")
    if set(identities) & UNRESOLVED_STRUCTURAL_REVIEW_IDENTITIES:
        raise ReviewPackageValidationError("UNRESOLVED_STRUCTURAL_SAMPLE_INCLUDED")
    matrix_by_candidate = {row["canonical_candidate_id"]: row for row in matrix_rows}
    if len(matrix_by_candidate) != 7:
        raise ReviewPackageValidationError("CLOSURE_MATRIX_CANDIDATE_NOT_UNIQUE")

    topologies = evidence["component_topology_authorities"]
    signatures_by_identity: dict[str, dict[str, Any]] = {}
    sample_by_identity: dict[str, Mapping[str, Any]] = {}
    for sample in samples:
        identity = _sample_identity(sample)
        sample_by_identity[identity] = sample
        signatures_by_identity[identity] = derive_chemistry_review_signature_v1(
            sample, topologies[sample["ligand_component_id"]]
        )
    exact_groups = group_exact_chemistry_review_signatures_v1(signatures_by_identity)
    ordered_group_shas: list[str] = []
    for identity in identities:
        digest = chemistry_review_signature_sha256_v1(signatures_by_identity[identity])
        if digest not in ordered_group_shas:
            ordered_group_shas.append(digest)

    hint_search = _reviewer_hint_search_summary(
        payloads, {sample["ligand_component_id"] for sample in samples}
    )
    review_classes: list[dict[str, Any]] = []
    class_by_sha: dict[str, dict[str, Any]] = {}
    for signature_sha in ordered_group_shas:
        member_set = set(exact_groups[signature_sha])
        members = _utf8_sorted(member_set)
        representative = next(identity for identity in identities if identity in member_set)
        sample = sample_by_identity[representative]
        signature = signatures_by_identity[representative]
        review_class = {
            "review_class_id": (
                "COVAPIE_RECOVERED7_CHEM_REVIEW_CLASS_" + signature_sha.upper()
            ),
            "chemistry_review_signature_sha256": signature_sha,
            "chemistry_review_signature": signature,
            "member_sample_count": len(members),
            "member_sample_identities": members,
            "representative_sample_identity": representative,
            "representative_component_id": signature["ligand_component_id"],
            "reactive_ligand_atom": signature["reactive_ligand_atom"],
            "reactive_residue_atom": signature["reactive_residue_atom"],
            "semantic_topology_sha256": signature["semantic_topology_sha256"],
            "canonical_heavy_atom_inventory": signature[
                "topology_heavy_atom_inventory"
            ],
            "canonical_heavy_heavy_bond_table": signature[
                "canonical_internal_heavy_heavy_bond_graph_with_bond_orders"
            ],
            "observed_reaction_state_heavy_atom_inventory": signature[
                "canonical_model_bound_ligand_heavy_atom_inventory"
            ],
            "topology_heavy_atoms_not_observed": signature[
                "topology_heavy_atoms_not_observed"
            ],
            "reactive_center_local_graph": _local_reaction_evidence(signature),
            "explicit_covalent_event_edge": signature["explicit_covalent_event"],
            "mechanical_closure_summary": {
                "member_count": len(members),
                "required_status": "MECHANICAL_CLOSURE_PASS",
                "all_members_passed": all(
                    sample_by_identity[identity]["mechanical_closure_status"]
                    == "MECHANICAL_CLOSURE_PASS"
                    for identity in members
                ),
            },
            "exact10_pass_summary": {
                "member_count": len(members),
                "required_status": "EXACT10_PASS",
                "all_members_passed": all(
                    sample_by_identity[identity]["exact10"]["status"]
                    == "EXACT10_PASS"
                    for identity in members
                ),
            },
            "pocket_pass_summary": {
                "member_count": len(members),
                "required_status": "POCKET_PASS",
                "all_members_passed": all(
                    matrix_by_candidate[
                        sample_by_identity[identity]["canonical_candidate_id"]
                    ]["pocket_status"]
                    == "POCKET_PASS"
                    for identity in members
                ),
            },
            "prior_reference_authority_class": "NONE",
            "prior_non_authoritative_review_hints": [],
            "prior_non_authoritative_review_hint_count": 0,
            "current_unresolved_authority_dimensions": list(
                UNRESOLVED_AUTHORITY_DIMENSIONS
            ),
            "future_review_scope_options": list(REVIEW_SCOPES),
            "future_family_rule_authority_action_options": list(
                AUTHORITY_ACTIONS[1:]
            ),
            "human_authority_created": False,
        }
        if not (
            review_class["mechanical_closure_summary"]["all_members_passed"]
            and review_class["exact10_pass_summary"]["all_members_passed"]
            and review_class["pocket_pass_summary"]["all_members_passed"]
        ):
            raise ReviewPackageValidationError("CLASS_MECHANICAL_EVIDENCE_NOT_PASS")
        review_classes.append(review_class)
        class_by_sha[signature_sha] = review_class

    applicability: list[dict[str, Any]] = []
    for sample in samples:
        identity = _sample_identity(sample)
        signature_sha = chemistry_review_signature_sha256_v1(
            signatures_by_identity[identity]
        )
        review_class = class_by_sha[signature_sha]
        record = _sample_applicability(
            sample,
            matrix_by_candidate[sample["canonical_candidate_id"]],
            review_class["review_class_id"],
            signature_sha,
        )
        if record["applicability_record_sha256"] != sample_applicability_record_sha256_v1(
            record
        ):
            raise ReviewPackageValidationError("APPLICABILITY_RECORD_SHA_MISMATCH")
        applicability.append(record)

    blank_records = []
    for review_class in review_classes:
        record = make_blank_review_record_v1(review_class)
        blank_records.append(
            {
                "unreviewed_template_payload_sha256": review_record_sha256_v1(record),
                "review_record": record,
            }
        )

    k36_classes = {
        row["review_class_id"]
        for row in applicability
        if row["ligand_component_id"] == "K36"
    }
    k36_members = [
        row["sample_identity"]
        for row in applicability
        if row["ligand_component_id"] == "K36"
    ]
    return {
        "review_classes": review_classes,
        "sample_applicability": applicability,
        "blank_review_records": blank_records,
        "source_provenance": _source_provenance(),
        "reviewer_hint_search": hint_search,
        "review_candidate_identities": list(identities),
        "review_class_count": len(review_classes),
        "k36_review_class_count": len(k36_classes),
        "k36_single_chemistry_review_class": len(k36_classes) == 1,
        "k36_class_member_count": len(k36_members),
        "k36_member_identities": k36_members,
        "matrix_by_candidate": matrix_by_candidate,
    }


def _index_rows(model: Mapping[str, Any]) -> list[dict[str, Any]]:
    classes = {row["review_class_id"]: row for row in model["review_classes"]}
    rows = []
    for index, applicability in enumerate(model["sample_applicability"]):
        review_class = classes[applicability["review_class_id"]]
        member_position = review_class["member_sample_identities"].index(
            applicability["sample_identity"]
        )
        matrix = model["matrix_by_candidate"][applicability["canonical_candidate_id"]]
        rows.append(
            {
                "package_index_version": PACKAGE_INDEX_VERSION,
                "package_item_order_0based": index,
                "canonical_candidate_id": applicability["canonical_candidate_id"],
                "sample_identity": applicability["sample_identity"],
                "pdb_id": applicability["pdb_id"],
                "ligand_component_id": applicability["ligand_component_id"],
                "review_class_id": applicability["review_class_id"],
                "chemistry_review_signature_sha256": applicability[
                    "chemistry_review_signature_sha256"
                ],
                "review_class_member_count": review_class["member_sample_count"],
                "review_class_representative_identity": review_class[
                    "representative_sample_identity"
                ],
                "sample_applicability_record_sha256": applicability[
                    "applicability_record_sha256"
                ],
                "current_downstream_status": matrix[
                    "downstream_chemistry_label_status"
                ],
                "current_primary_issue": matrix["primary_remaining_issue"],
                "manual_review_required": True,
                "human_decision_redundant_with_class_if_reusable_scope": (
                    member_position > 0
                ),
                "review_status": "NOT_REVIEWED",
            }
        )
    return rows


def _review_decision_template_csv(record: Mapping[str, Any]) -> bytes:
    return _csv_bytes(REVIEW_RECORD_FIELDS, [record])


def _atom_bond_rows(review_class: Mapping[str, Any]) -> list[dict[str, Any]]:
    signature = review_class["chemistry_review_signature"]
    observed = {
        row["atom_id"]
        for row in signature["canonical_model_bound_ligand_heavy_atom_inventory"]
    }
    missing = set(signature["topology_heavy_atoms_not_observed"])
    reactive = signature["reactive_ligand_atom"]
    rows: list[dict[str, Any]] = []
    for atom in signature["topology_heavy_atom_inventory"]:
        atom_id = atom["atom_id"]
        rows.append(
            {
                "record_type": "TOPOLOGY_HEAVY_ATOM",
                "atom_id": atom_id,
                "element": atom["element"],
                "observed_reaction_state": atom_id in observed,
                "topology_heavy_atom_not_observed": atom_id in missing,
                "reactive_ligand_atom": atom_id == reactive,
                "bond_atom_id_1": "",
                "bond_atom_id_2": "",
                "bond_order": "",
                "bond_incident_to_reactive_atom": False,
                "bond_incident_to_unobserved_atom": False,
                "evidence_note": "component topology atom and reaction-state observation status",
            }
        )
    for bond in signature["canonical_internal_heavy_heavy_bond_graph_with_bond_orders"]:
        left = bond["atom_id_1"]
        right = bond["atom_id_2"]
        rows.append(
            {
                "record_type": "COMPONENT_HEAVY_HEAVY_BOND",
                "atom_id": "",
                "element": "",
                "observed_reaction_state": "",
                "topology_heavy_atom_not_observed": "",
                "reactive_ligand_atom": "",
                "bond_atom_id_1": left,
                "bond_atom_id_2": right,
                "bond_order": bond["bond_order"],
                "bond_incident_to_reactive_atom": reactive in (left, right),
                "bond_incident_to_unobserved_atom": left in missing or right in missing,
                "evidence_note": "component topology bond; no PRE interpretation",
            }
        )
    rows.append(
        {
            "record_type": "EXPLICIT_PROTEIN_LIGAND_EVENT_EDGE",
            "atom_id": "",
            "element": "",
            "observed_reaction_state": True,
            "topology_heavy_atom_not_observed": False,
            "reactive_ligand_atom": True,
            "bond_atom_id_1": "CYS:SG",
            "bond_atom_id_2": f"{signature['ligand_component_id']}:{reactive}",
            "bond_order": "NOT_INFERRED",
            "bond_incident_to_reactive_atom": True,
            "bond_incident_to_unobserved_atom": False,
            "evidence_note": "published exact struct_conn endpoint edge",
        }
    )
    return rows


def _readme_bytes(
    review_class: Mapping[str, Any], blank_wrapper: Mapping[str, Any]
) -> bytes:
    missing = review_class["topology_heavy_atoms_not_observed"]
    missing_text = ", ".join(missing) if missing else "NONE"
    members = ", ".join(review_class["member_sample_identities"])
    return (
        f"# Recovered7 targeted chemistry review: {review_class['review_class_id']}\n\n"
        f"This exact chemistry-signature class covers: {members}. One future human "
        "chemistry decision may be reused only if the reviewer selects "
        "`EXACT_CHEMISTRY_SIGNATURE_REUSABLE`; otherwise no cross-sample propagation "
        "is permitted.\n\n"
        "Already proven: exact Cys-SG event endpoints, ligand instance mapping, "
        "component topology mapping, canonical model-bound heavy atoms, Exact10, "
        "8A pocket readiness, and mechanical closure. Do not re-review those facts.\n\n"
        f"The reactive ligand atom is `{review_class['reactive_ligand_atom']}` and the "
        "reactive residue atom is `SG`. Topology heavy atoms absent from the observed "
        f"reaction-state instance: {missing_text}. These absences are evidence only; "
        "this package does not infer a leaving group, inverse reaction, PRE bond "
        "orders, formal-charge changes, proton transfers, or mechanism.\n\n"
        "The human must decide reaction family disposition/ID, warhead rule "
        "disposition/ID, warhead atom set, attachment atom, non-warhead boundary "
        "atom and bond order, scaffold/linker/warhead role partition, minimal seed, "
        "review scope, reviewer ID, and rationale. Existing IDs are optional: use "
        "`NEW_AUTHORITY_REQUIRED` with a blank ID when a later compiler must create "
        "new authority.\n\n"
        "Allowed review-scope values are `NOT_REVIEWED`, "
        "`EXACT_CHEMISTRY_SIGNATURE_REUSABLE`, `SAMPLE_BOUND_ONLY`, and "
        "`QUARANTINE`. Package generation leaves the value at `NOT_REVIEWED`.\n\n"
        "No exact Current11 chemistry-signature reviewer hint was found. Current11 "
        "sample-bound authority is not authority for this class.\n\n"
        f"Frozen signature SHA256: `{review_class['chemistry_review_signature_sha256']}`.\n"
        "Blank template status/scope: `NOT_REVIEWED` / `NOT_REVIEWED`.\n"
        f"Blank template payload SHA256: `{blank_wrapper['unreviewed_template_payload_sha256']}`.\n"
    ).encode("utf-8")


def build_manual_review_aid_artifacts_v1(
    repo_root: Path = REPO_ROOT, state_root: Path = STATE_ROOT
) -> dict[str, bytes]:
    model = build_package_model_v1(repo_root, state_root)
    blank_by_class = {
        wrapper["review_record"]["review_class_id"]: wrapper
        for wrapper in model["blank_review_records"]
    }
    applicability_by_class: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in model["sample_applicability"]:
        applicability_by_class[record["review_class_id"]].append(record)
    files: dict[str, bytes] = {}
    for review_class in model["review_classes"]:
        class_id = review_class["review_class_id"]
        wrapper = blank_by_class[class_id]
        prefix = f"{class_id}/"
        files[prefix + "README.md"] = _readme_bytes(review_class, wrapper)
        files[prefix + "chemistry_evidence.json"] = _json_bytes(
            {
                "review_class": review_class,
                "sample_applicability": applicability_by_class[class_id],
                "blank_review_record": wrapper,
                "prior_reference_authority_class": "NONE",
            }
        )
        files[prefix + "atom_and_bond_review_table.csv"] = _csv_bytes(
            ATOM_BOND_TABLE_COLUMNS, _atom_bond_rows(review_class)
        )
        files[prefix + "review_decision_template.csv"] = (
            _review_decision_template_csv(wrapper["review_record"])
        )
    return dict(sorted(files.items(), key=lambda item: item[0].encode("utf-8")))


def _manifest(
    model: Mapping[str, Any],
    index_bytes: bytes,
    evidence_bytes: bytes,
    manual_aids: Mapping[str, bytes],
) -> dict[str, Any]:
    member_counts = {
        review_class["review_class_id"]: review_class["member_sample_count"]
        for review_class in model["review_classes"]
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "published_closure_commit": PUBLISHED_CLOSURE_COMMIT,
        "published_closure_source_hashes": {
            path.as_posix(): digest
            for path, digest in PUBLISHED_CLOSURE_SOURCE_HASHES.items()
        },
        "review_candidate_count": 7,
        "sample_review_population_count": 7,
        "review_class_count": model["review_class_count"],
        "independent_human_chemistry_decision_count": model["review_class_count"],
        "review_class_member_counts": member_counts,
        "k36_review_class_count": model["k36_review_class_count"],
        "k36_single_chemistry_review_class": model[
            "k36_single_chemistry_review_class"
        ],
        "k36_class_member_count": model["k36_class_member_count"],
        "sample_applicability_record_count": len(model["sample_applicability"]),
        "blank_review_record_count": len(model["blank_review_records"]),
        "completed_human_review_count": 0,
        "human_authority_created": False,
        "reusable_authority_created": False,
        "sample_bound_authority_created": False,
        "review_packages_materialized": True,
        "manual_review_aid_class_count": model["review_class_count"],
        "manual_review_aid_file_count": len(manual_aids),
        "deterministic_output_sha256": {
            INDEX_FILE: _sha256(index_bytes),
            EVIDENCE_FILE: _sha256(evidence_bytes),
        },
        "manual_review_aid_sha256": {
            path: _sha256(payload) for path, payload in manual_aids.items()
        },
        "manifest_self_sha256_recorded": False,
        "ready_for_review_package_publication": True,
        "ready_for_human_chemistry_review_execution": True,
        "ready_for_automated_chemistry_label_execution": False,
        "ready_for_geometry_loss_activation": False,
        "ready_for_training": False,
        "distance_based_bond_inference_used": False,
        "inverse_reaction_chemistry_executed": False,
        "pre_geometry_reconstruction_executed": False,
        "leaving_group_inferred_automatically": False,
        "formal_charge_change_inferred_automatically": False,
        "proton_transfer_inferred_automatically": False,
        "network_request_executed": False,
        "raw_structure_downloaded": False,
        "topology_downloaded": False,
        "model_forward": False,
        "backward": False,
        "optimizer_step": False,
        "trainer_fit": False,
        "formal_training": False,
        "geometry_loss_activation": False,
        "rl": False,
        "published_closure_modified": False,
        "published_execution_modified": False,
        "current11_modified": False,
        "raw_modified": False,
        "recommended_next_step_exactly": (
            "review_and_publish_covapie_cys_sg_recovered7_targeted_chemistry_review_packages_v1"
        ),
    }


def build_covapie_cys_sg_recovered7_targeted_chemistry_review_package_artifacts_v1(
    repo_root: Path = REPO_ROOT, state_root: Path = STATE_ROOT
) -> dict[str, bytes]:
    model = build_package_model_v1(repo_root, state_root)
    index_bytes = _csv_bytes(INDEX_COLUMNS, _index_rows(model))
    evidence_payload = {
        "schema_version": SCHEMA_VERSION,
        "review_classes": model["review_classes"],
        "sample_applicability": model["sample_applicability"],
        "blank_review_records": model["blank_review_records"],
        "source_provenance": model["source_provenance"],
        "reviewer_hint_search": model["reviewer_hint_search"],
    }
    evidence_bytes = _json_bytes(evidence_payload)
    manual_aids = build_manual_review_aid_artifacts_v1(repo_root, state_root)
    manifest_bytes = _json_bytes(
        _manifest(model, index_bytes, evidence_bytes, manual_aids)
    )
    return {
        INDEX_FILE: index_bytes,
        EVIDENCE_FILE: evidence_bytes,
        MANIFEST_FILE: manifest_bytes,
    }


def _write_identical_or_new(
    path: Path, payload: bytes, *, replace_existing: bool = False
) -> None:
    if path.exists():
        if not path.is_file():
            raise ReviewPackageValidationError(f"OUTPUT_EXISTS_WITH_DIFFERENT_BYTES:{path}")
        if path.read_bytes() != payload:
            if not replace_existing:
                raise ReviewPackageValidationError(
                    f"OUTPUT_EXISTS_WITH_DIFFERENT_BYTES:{path}"
                )
            path.write_bytes(payload)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def materialize_covapie_cys_sg_recovered7_targeted_chemistry_review_packages_v1(
    repo_root: Path = REPO_ROOT,
    state_root: Path = STATE_ROOT,
    *,
    tracked_output_root: Path | None = None,
    manual_output_root: Path | None = None,
    replace_existing: bool = False,
) -> dict[str, str]:
    tracked = build_covapie_cys_sg_recovered7_targeted_chemistry_review_package_artifacts_v1(
        repo_root, state_root
    )
    aids = build_manual_review_aid_artifacts_v1(repo_root, state_root)
    tracked_root = (
        repo_root / OUTPUT_ROOT if tracked_output_root is None else tracked_output_root
    )
    manual_root = (
        state_root / MANUAL_REVIEW_AID_ROOT
        if manual_output_root is None
        else manual_output_root
    )
    written: dict[str, str] = {}
    for name, payload in tracked.items():
        path = tracked_root / name
        _write_identical_or_new(
            path, payload, replace_existing=replace_existing
        )
        written[path.as_posix()] = _sha256(payload)
    for relative, payload in aids.items():
        path = manual_root / relative
        _write_identical_or_new(
            path, payload, replace_existing=replace_existing
        )
        written[path.as_posix()] = _sha256(payload)
    return written


def main() -> None:
    written = materialize_covapie_cys_sg_recovered7_targeted_chemistry_review_packages_v1()
    print(json.dumps(written, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
