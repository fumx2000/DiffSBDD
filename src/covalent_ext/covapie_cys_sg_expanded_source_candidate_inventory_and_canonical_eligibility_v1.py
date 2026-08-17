"""Build the bounded CovaPIE Cys-SG Stage-A candidate registry.

This owner is deliberately metadata-only.  Repository evidence is read from
the frozen baseline commit, state-side authorities are SHA-bound, and the
only writable operation is the explicit three-file materializer.  It does not
read raw structures, run chemistry/geometry, load a model, or train.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import stat
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from covalent_ext import (
    covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1
    as exact10_owner,
)

__all__ = (
    "Exact10EligibilityDecision",
    "build_covapie_cys_sg_expanded_source_candidate_inventory_and_canonical_eligibility_artifacts_v1",
    "evaluate_exact10_model_bound_graph_v1",
    "materialize_covapie_cys_sg_expanded_source_candidate_inventory_and_canonical_eligibility_v1",
    "verify_payload_sha256_v1",
)

SCHEMA_VERSION = (
    "covapie_cys_sg_expanded_source_candidate_inventory_and_"
    "canonical_eligibility_v1"
)
BASELINE_COMMIT = "de6767f730e10e90af910def8a3f2d1a43eecfed"
DESIGN_REPORT_SHA256 = (
    "1851e488426aa7d034a903c38e6eb6826aa013da8b083cfeb7ea936b291426d1"
)
CURRENT11_STATE_SHA256 = (
    "f4178987f3c3eed0e248f6d3d5f22cb8bce1839d39ab08aff0bff9d2ef9f3774"
)
CURRENT11_TARGET_STATE_SHA256 = (
    "a95ae52e091a7117b241269eebd891f3ee97e3ae4a6b4e14fa441ab6a1ed2096"
)
GOLDEN_SET_ID = "COVAPIE_CURRENT11_GOLD_V1"
FEATURE_SEMANTICS_POLICY_ID = (
    exact10_owner.SCHEMA_VERSION
    + ":"
    + exact10_owner.CHECKPOINT_CHANNEL_ORDER
)
RECOMMENDED_NEXT_STEP = (
    "review_and_publish_covapie_cys_sg_expanded_source_candidate_"
    "inventory_and_canonical_eligibility_v1"
)

REPO_ROOT = Path(__file__).resolve().parents[2]
STATE_ROOT = REPO_ROOT.parent / "covapie-state"
DESIGN_REPORT_RELATIVE = Path(
    "review-scratch/cys-sg-expanded-dataset-and-pre-covalent-geometry-v1/"
    "cys_sg_expanded_dataset_and_pre_covalent_geometry_design_report.md"
)
CURRENT11_STATE_RELATIVE = Path(
    "manual-review/covapie_current11_unified_effective_authority_view_v1.json"
)
CURRENT11_TARGET_STATE_RELATIVE = Path(
    "manual-review/"
    "covapie_current11_target_residue_atom_condition_authority_bundle_v1.json"
)
OUTPUT_ROOT = (
    Path("data/derived/covalent_small")
    / "covapie_cys_sg_expanded_source_candidate_inventory_and_"
    "canonical_eligibility_v1"
)
CANDIDATE_FILE = "covapie_cys_sg_expanded_candidate_inventory_and_eligibility.csv"
ISSUE_FILE = "covapie_cys_sg_expanded_candidate_issue_inventory.csv"
MANIFEST_FILE = "covapie_cys_sg_expanded_candidate_inventory_manifest.json"
OUTPUT_FILES = (CANDIDATE_FILE, ISSUE_FILE, MANIFEST_FILE)

SOURCE_REGISTRY = Path(
    "data/derived/covalent_small/"
    "real_covalent_multi_source_dataset_ingestion_design_gate_v0/"
    "real_covalent_multi_source_dataset_ingestion_design_gate_table.csv"
)
COVPDB_INVENTORY = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_acquired_annotation_manual_review_gate_v0/"
    "covapie_cys_sg_combined_acquired_annotation_inventory.csv"
)
EXPANSION_SOURCE_INVENTORY = Path(
    "data/derived/covalent_small/"
    "covapie_independent_group_expansion_design_gate_v0/"
    "covapie_expansion_candidate_source_inventory.csv"
)
EXPANSION_EXCLUSION = Path(
    "data/derived/covalent_small/"
    "covapie_independent_group_expansion_design_gate_v0/"
    "covapie_expansion_candidate_exclusion_audit.csv"
)
CURRENT11_MEMBERSHIP = Path(
    "data/derived/covalent_small/"
    "covapie_final_dataset_materialization_smoke_v0/"
    "covapie_final_dataset_membership.csv"
)
CURRENT11_INDEX = Path(
    "data/derived/covalent_small/"
    "covapie_final_dataset_materialization_smoke_v0/final_dataset_index.csv"
)
CURRENT11_PAIR = Path(
    "data/derived/covalent_small/"
    "covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_"
    "evidence_validation_v1/"
    "covapie_atom_pair_canonical_record_validation_matrix.csv"
)
FEATURE_MANIFEST = Path(
    "data/derived/covalent_small/"
    "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1/"
    "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_"
    "manifest.json"
)
DIRECT_CONFIRMED = Path(
    "data/derived/covalent_small/"
    "real_covalent_struct_conn_candidate_manual_review_fill_validation_v0/"
    "real_covalent_struct_conn_confirmed_candidate_table.csv"
)
DIRECT_PAIR = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_coordinate_pair_sanity_gate_v1_"
    "altloc_aware/"
    "real_covalent_confirmed_candidate_coordinate_pair_sanity_table_v1_"
    "altloc_aware.csv"
)
DIRECT_TOPOLOGY_ATOMS = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_"
    "exported_step8_topology_v0/ligand_observed_atom_topology_smoke_table.csv"
)
DIRECT_TOPOLOGY_AUDIT = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_ligand_topology_smoke_retry_with_"
    "exported_step8_topology_v0/ligand_topology_smoke_retry_audit.csv"
)
DIRECT_POCKET_ATOMS = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_pocket_extraction_smoke_v0/"
    "real_covalent_confirmed_candidate_pocket_atom_table.csv"
)
DIRECT_POCKET_AUDIT = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_pocket_extraction_smoke_v0/"
    "real_covalent_confirmed_candidate_pocket_extraction_audit.csv"
)
DIRECT_MODEL_INDEX = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_model_input_materialization_smoke_v0/"
    "model_input_smoke_index.csv"
)
DIRECT_MODEL_QA = Path(
    "data/derived/covalent_small/"
    "real_covalent_confirmed_candidate_model_input_qa_gate_v0/"
    "model_input_smoke_row_qa_audit.csv"
)
DIRECT_PARENT_POST_AUDIT = Path(
    "data/derived/covalent_small/pre_reaction_graph/"
    "pre_reaction_training_readiness_gate_report.csv"
)

FROZEN_INPUT_SHA256: Mapping[Path, str] = {
    SOURCE_REGISTRY:
        "d5d4dd2637a057b1cc1defc2b160e9752d75bd42e067a24e6d1a1d5e01175777",
    COVPDB_INVENTORY:
        "c9307724ff851fdab13a3b2f71887fb8759fbb99b444d44054af02d472ff575b",
    EXPANSION_SOURCE_INVENTORY:
        "6d387be4e12609b04972be6da5d963067c964876024707613fe8a02b03ec0dda",
    EXPANSION_EXCLUSION:
        "ffecf93fc899ec36bbc31f723cf6d3c99c5d6e4f0991561b9e804e54bb1f3621",
    CURRENT11_MEMBERSHIP:
        "ddf1705176c8680d90e0e216a9af3d1501c6a821764c3e7138a28269e687a977",
    CURRENT11_INDEX:
        "c4c31888cb0f7c148b00656ccf22ab68fab842fcdafdee049b2f420eddc1302d",
    CURRENT11_PAIR:
        "c756e6ce601bad1d10cfba5cac6129f9f688d00451cc1d805edff938ccee6ca0",
    FEATURE_MANIFEST:
        "24cb60ca4f080a72e8c60aef63d105d82ec2f432eecc9b90f3341f52576bb6e0",
    DIRECT_CONFIRMED:
        "981c59f1131ae8c5f1bb17680986eccda9d85a44caf0f44d1711246283f04186",
    DIRECT_PAIR:
        "0293909b9a3ab96063eda3e5eed12609793cc8837ed7e2cd33d8681d0f8249c9",
    DIRECT_TOPOLOGY_ATOMS:
        "b47d03598a077e6201e21585c683fe46a7423d99fae231b47c303657bad89c59",
    DIRECT_TOPOLOGY_AUDIT:
        "3c81d30381e507453121ef05343f9f718e9f0df2a329fd6b7a9d14a46d63d317",
    DIRECT_POCKET_ATOMS:
        "77dc7777d44ec48ecc985c9c7d66d603756781455b7b3d5c9151dd5800ceaee9",
    DIRECT_POCKET_AUDIT:
        "62ad3b4ff4f79bcb41bd1ff6497701cc07c02d809522360e8c0a2a454838ded6",
    DIRECT_MODEL_INDEX:
        "56737d79596a50a0cc223a8736cb998ae54f45b0495173934d1199238557628c",
    DIRECT_MODEL_QA:
        "485a686547f649ecc1119a0ac825fea405dbd34f2a1aff8b37bfea66ce81004b",
    DIRECT_PARENT_POST_AUDIT:
        "a2cc8ddab41e6439e1d0b2577fdb3514aefb617881975226d6e6bd73ecad8c2d",
}

INPUT_ROLES: Mapping[Path, str] = {
    SOURCE_REGISTRY: "registered_source_identity_authority",
    COVPDB_INVENTORY: "covpdb_visible_candidate_inventory",
    EXPANSION_SOURCE_INVENTORY: "covpdb_candidate_crosscheck_status",
    EXPANSION_EXCLUSION: "duplicate_and_failure_evidence",
    CURRENT11_MEMBERSHIP: "current11_membership_authority",
    CURRENT11_INDEX: "current11_coordinate_pocket_sample_authority",
    CURRENT11_PAIR: "current11_reactive_pair_authority",
    FEATURE_MANIFEST: "exact10_feature_semantics_authority",
    DIRECT_CONFIRMED: "direct_local_exact_event_authority",
    DIRECT_PAIR: "direct_local_coordinate_authority",
    DIRECT_TOPOLOGY_ATOMS: "direct_local_model_bound_ligand_node_authority",
    DIRECT_TOPOLOGY_AUDIT: "direct_local_topology_authority",
    DIRECT_POCKET_ATOMS: "direct_local_model_bound_pocket_node_authority",
    DIRECT_POCKET_AUDIT: "direct_local_pocket_readiness_authority",
    DIRECT_MODEL_INDEX: "direct_local_model_bound_graph_path_authority",
    DIRECT_MODEL_QA: "direct_local_model_input_dependency_qa",
    DIRECT_PARENT_POST_AUDIT: "direct_local_legacy_parent_post_topology_qa",
}

REGISTERED_SOURCE_IDENTITIES = (
    "CovPDB",
    "CovBinderInPDB",
    "CovalentInDB",
    "PDB/mmCIF direct",
    "local curated",
)
PARTIALLY_OPERATIONAL_LOCAL_SOURCE_IDENTITIES = (
    "CovPDB",
    "PDB/mmCIF direct",
    "local curated",
)
PILOT_IDENTITIES = (
    ("1ATK", "E64"),
    ("5F2E", "5UT"),
    ("6OIM", "MOV"),
    ("6DI9", "GJJ"),
    ("1A54", "MDC"),
    ("2DJF", "1ZB"),
    ("6VWE", "JY1"),
    ("4DCD", "K36"),
)
DISPOSITIONS = (
    "GOLD_REFERENCE",
    "ELIGIBLE_FOR_STAGE_B",
    "HUMAN_REVIEW_REQUIRED",
    "REJECT",
)
COMPONENT_FIELDS = (
    "source_identity_status",
    "cys_sg_event_status",
    "reactive_pair_status",
    "coordinate_status",
    "ligand_component_identity_status",
    "parent_post_topology_status",
    "exact10_status",
    "pocket_readiness_status",
    "gold_duplicate_status",
    "canonical_eligibility_status",
)

CANDIDATE_COLUMNS = (
    "canonical_candidate_id",
    "candidate_registry_index",
    "source_identity",
    "source_provenance_identities",
    "source_record_identity",
    "source_record_version",
    "pdb_id",
    "protein_chain",
    "cys_residue_sequence",
    "cys_insertion_code",
    "ligand_component_id",
    "ligand_instance_if_available",
    "reactive_residue_atom",
    "reactive_ligand_atom_if_known",
    "dataset_confidence_tier",
    "golden_set_id_or_none",
    "current11_gold_match",
    "structural_event_key_if_resolved",
    "exact_pair_evidenced",
    "source_formula_contains_Rh",
    "canonical_model_graph_contains_Rh",
    *COMPONENT_FIELDS,
    "registry_disposition",
    "primary_issue_code_or_NONE",
    "predecessor_row_identity",
    "predecessor_source_path",
    "predecessor_source_sha256",
    "evidence_identity_ids",
)
ISSUE_COLUMNS = (
    "issue_inventory_index",
    "canonical_candidate_id",
    "issue_stage",
    "issue_code",
    "severity_disposition_effect",
    "evidence_owner_or_source",
    "review_required",
    "fundamental_reject",
    "resolved_or_open",
)


@dataclass(frozen=True)
class Exact10EligibilityDecision:
    status: str
    sample_rejected: bool
    canonical_graph_evidence_available: bool
    retained_heavy_atom_count: int
    excluded_explicit_hydrogen_count: int
    unsupported_or_invalid_node_count: int


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def verify_payload_sha256_v1(
    payload: bytes, expected_sha256: str, authority_identity: str,
) -> None:
    if _sha256(payload) != expected_sha256:
        raise ValueError(f"STAGE_A_SOURCE_SHA_MISMATCH:{authority_identity}")


def _git(repo_root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ("git", *args),
        cwd=repo_root,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise ValueError(
            "STAGE_A_GIT_READ_FAILED:"
            + result.stderr.decode("utf-8", "replace").strip()
        )
    return result.stdout


def _baseline_payload(repo_root: Path, path: Path) -> bytes:
    payload = _git(repo_root, "show", f"{BASELINE_COMMIT}:{path.as_posix()}")
    verify_payload_sha256_v1(payload, FROZEN_INPUT_SHA256[path], path.as_posix())
    return payload


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _json_object(payload: bytes) -> dict[str, Any]:
    value = json.loads(payload)
    if type(value) is not dict:
        raise ValueError("STAGE_A_EXPECTED_JSON_OBJECT")
    return value


def _truth(value: object) -> bool:
    return value is True or str(value).lower() == "true"


def _csv_scalar(value: Any) -> Any:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    return value


def _csv_bytes(rows: Sequence[Mapping[str, Any]], columns: Sequence[str]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=columns,
        extrasaction="raise",
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({column: _csv_scalar(row[column]) for column in columns})
    return buffer.getvalue().encode("utf-8")


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            indent=2,
        )
        + "\n"
    ).encode("utf-8")


def evaluate_exact10_model_bound_graph_v1(
    type_symbols: Sequence[object] | None,
    *,
    source_formula_unsupported_elements: Sequence[str] = (),
) -> Exact10EligibilityDecision:
    """Apply the frozen Exact10 owner only to an authoritative model graph.

    Formula-only evidence never substitutes for graph membership.  When a
    graph is supplied, the upstream projection owner decides H exclusion and
    complete-sample rejection without an unknown/other fallback.
    """

    if type_symbols is None:
        status = (
            "EXACT10_FORMULA_UNSUPPORTED_NODE_INCLUSION_UNRESOLVED"
            if source_formula_unsupported_elements
            else "EXACT10_MODEL_GRAPH_EVIDENCE_MISSING"
        )
        return Exact10EligibilityDecision(status, False, False, 0, 0, 0)

    projection = exact10_owner.project_type_symbols_to_checkpoint_heavy_v1(
        type_symbols
    )
    invalid_count = sum(
        value in {"unsupported_nonhydrogen", "missing_or_invalid"}
        for value in projection.symbol_classes
    )
    if projection.sample_rejected:
        return Exact10EligibilityDecision(
            "EXACT10_MODEL_BOUND_GRAPH_REJECTED",
            True,
            True,
            0,
            sum(value == "explicit_hydrogen" for value in projection.symbol_classes),
            invalid_count,
        )
    return Exact10EligibilityDecision(
        "EXACT10_MODEL_BOUND_GRAPH_VALIDATED",
        False,
        True,
        sum(projection.keep_mask),
        sum(value == "explicit_hydrogen" for value in projection.symbol_classes),
        0,
    )


def _event_key(
    *,
    pdb_id: str,
    protein_chain: str,
    cys_sequence: str,
    cys_insertion: str,
    ligand_chain: str,
    ligand_component: str,
    ligand_sequence: str,
    ligand_atom: str,
) -> str:
    return (
        f"PDB={pdb_id}|PROTEIN={protein_chain}:CYS:{cys_sequence}:"
        f"{cys_insertion}:SG|LIGAND={ligand_chain}:{ligand_component}:"
        f"{ligand_sequence}:NONE:{ligand_atom}"
    )


def _candidate_id(source_identity: str, source_record_identity: str) -> str:
    token = re.sub(r"[^A-Za-z0-9]+", "_", source_identity).strip("_").upper()
    record = re.sub(
        r"[^A-Za-z0-9]+", "_", source_record_identity
    ).strip("_").upper()
    return f"COVAPIE_CYS_SG_CANDIDATE_V1_{token}_{record}"


def _issue(
    candidate_id: str,
    stage: str,
    code: str,
    effect: str,
    owner: str,
    *,
    review_required: bool,
    fundamental_reject: bool,
    resolved: bool,
) -> dict[str, Any]:
    return {
        "issue_inventory_index": 0,
        "canonical_candidate_id": candidate_id,
        "issue_stage": stage,
        "issue_code": code,
        "severity_disposition_effect": effect,
        "evidence_owner_or_source": owner,
        "review_required": review_required,
        "fundamental_reject": fundamental_reject,
        "resolved_or_open": "RESOLVED" if resolved else "OPEN",
    }


def _load_inputs(
    repo_root: Path, state_root: Path,
) -> tuple[dict[Path, bytes], bytes, bytes, bytes]:
    payloads = {
        path: _baseline_payload(repo_root, path) for path in FROZEN_INPUT_SHA256
    }
    design = (state_root / DESIGN_REPORT_RELATIVE).read_bytes()
    verify_payload_sha256_v1(
        design, DESIGN_REPORT_SHA256, "state://" + DESIGN_REPORT_RELATIVE.as_posix()
    )
    current11_state = (state_root / CURRENT11_STATE_RELATIVE).read_bytes()
    verify_payload_sha256_v1(
        current11_state,
        CURRENT11_STATE_SHA256,
        "state://" + CURRENT11_STATE_RELATIVE.as_posix(),
    )
    current11_target_state = (
        state_root / CURRENT11_TARGET_STATE_RELATIVE
    ).read_bytes()
    verify_payload_sha256_v1(
        current11_target_state,
        CURRENT11_TARGET_STATE_SHA256,
        "state://" + CURRENT11_TARGET_STATE_RELATIVE.as_posix(),
    )
    return payloads, design, current11_state, current11_target_state


def _validate_source_registry(payload: bytes) -> tuple[str, ...]:
    rows = _csv_rows(payload)
    selected = [row for row in rows if row["row_type"] == "source_registry_schema"]
    if len(selected) != 1:
        raise ValueError("STAGE_A_SOURCE_REGISTRY_AUTHORITY_MISSING")
    evidence = json.loads(selected[0]["evidence"])
    identities = tuple(evidence["planned_source_registry_entries"])
    if identities != REGISTERED_SOURCE_IDENTITIES:
        raise ValueError("STAGE_A_REGISTERED_SOURCE_IDENTITIES_MISMATCH")
    return identities


def _validate_feature_policy(payload: bytes) -> None:
    manifest = _json_object(payload)
    expected = {
        "schema_version": exact10_owner.SCHEMA_VERSION,
        "feature_semantics_known": True,
        "unknown_atom_policy_contract_resolved": True,
        "checkpoint_categorical_width": 10,
        "checkpoint_channel_order": exact10_owner.CHECKPOINT_CHANNEL_ORDER,
        "explicit_hydrogen_handling":
            exact10_owner.EXPLICIT_HYDROGEN_POLICY,
        "unsupported_nonhydrogen_handling":
            exact10_owner.UNSUPPORTED_NONHYDROGEN_POLICY,
        "new_unknown_channel_allowed": False,
        "others_channel_checkpoint_input_allowed": False,
        "silent_zero_vector_fallback_allowed": False,
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise ValueError(f"STAGE_A_EXACT10_POLICY_MISMATCH:{key}")


def _build_registry(
    payloads: Mapping[Path, bytes],
    current11_state_payload: bytes,
    current11_target_state_payload: bytes,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    covpdb_rows = _csv_rows(payloads[COVPDB_INVENTORY])
    expansion_rows = _csv_rows(payloads[EXPANSION_SOURCE_INVENTORY])
    exclusion_rows = _csv_rows(payloads[EXPANSION_EXCLUSION])
    membership_rows = _csv_rows(payloads[CURRENT11_MEMBERSHIP])
    current11_index_rows = _csv_rows(payloads[CURRENT11_INDEX])
    pair_rows = _csv_rows(payloads[CURRENT11_PAIR])
    direct_rows = _csv_rows(payloads[DIRECT_CONFIRMED])
    direct_pair_rows = _csv_rows(payloads[DIRECT_PAIR])
    topology_atom_rows = _csv_rows(payloads[DIRECT_TOPOLOGY_ATOMS])
    topology_audit_rows = _csv_rows(payloads[DIRECT_TOPOLOGY_AUDIT])
    pocket_atom_rows = _csv_rows(payloads[DIRECT_POCKET_ATOMS])
    pocket_audit_rows = _csv_rows(payloads[DIRECT_POCKET_AUDIT])
    model_index_rows = _csv_rows(payloads[DIRECT_MODEL_INDEX])
    model_qa_rows = _csv_rows(payloads[DIRECT_MODEL_QA])
    parent_post_rows = _csv_rows(payloads[DIRECT_PARENT_POST_AUDIT])
    effective = _json_object(current11_state_payload)
    target_authority = _json_object(current11_target_state_payload)

    if (len(covpdb_rows), len(expansion_rows), len(exclusion_rows)) != (25, 25, 17):
        raise ValueError("STAGE_A_COVPDB_DENOMINATOR_MISMATCH")
    if (
        len(membership_rows) != 11
        or len(current11_index_rows) != 11
        or len(pair_rows) != 11
        or effective.get("effective_authority_record_count") != 11
        or target_authority.get("target_residue_atom_condition_record_count")
        != 11
        or target_authority.get("all_records_resolved_authoritative") is not True
    ):
        raise ValueError("STAGE_A_CURRENT11_DENOMINATOR_MISMATCH")
    if not all(row["verified"] == "true" for row in pair_rows):
        raise ValueError("STAGE_A_CURRENT11_PAIR_AUTHORITY_INVALID")
    if len(direct_rows) != 3 or len(direct_pair_rows) != 3:
        raise ValueError("STAGE_A_DIRECT_LOCAL_DENOMINATOR_MISMATCH")

    expansion_by_candidate = {
        row["source_candidate_id"]: row for row in expansion_rows
    }
    if len(expansion_by_candidate) != 25:
        raise ValueError("STAGE_A_EXPANSION_SOURCE_IDENTITY_COLLISION")
    exclusions = {
        (row["pdb_id"], row["expected_het_id"]): row
        for row in exclusion_rows
    }
    membership_by_key = {
        (row["pdb_id"], row["ligand_comp_id"]): row
        for row in membership_rows
    }
    index_by_sample = {
        row["sample_index_row_id"]: row for row in current11_index_rows
    }
    pair_by_sample = {row["sample_index_row_id"]: row for row in pair_rows}
    effective_by_sample = {
        row["sample_index_row_id"]: row
        for row in effective["effective_authority_records"]
    }
    target_by_sample = {
        row["sample_index_row_id"]: row
        for row in target_authority["target_residue_atom_condition_records"]
    }
    expected_sample_ids = set(index_by_sample)
    if (
        set(pair_by_sample) != expected_sample_ids
        or set(effective_by_sample) != expected_sample_ids
        or set(target_by_sample) != expected_sample_ids
    ):
        raise ValueError("STAGE_A_CURRENT11_AUTHORITY_JOIN_MISMATCH")

    direct_pair_by_review = {
        row["review_row_id"]: row for row in direct_pair_rows
    }
    topology_audit_by_review = {
        row["review_row_id"]: row for row in topology_audit_rows
    }
    pocket_audit_by_review = {
        row["review_row_id"]: row for row in pocket_audit_rows
    }
    model_index_by_review = {
        row["review_row_id"]: row for row in model_index_rows
    }
    model_qa_by_review = {row["review_row_id"]: row for row in model_qa_rows}
    topology_symbols: dict[str, list[str]] = defaultdict(list)
    for row in topology_atom_rows:
        topology_symbols[row["review_row_id"]].append(row["atom_symbol"])
    pocket_symbols: dict[str, list[str]] = defaultdict(list)
    for row in pocket_atom_rows:
        pocket_symbols[row["review_row_id"]].append(row["type_symbol"])
    if len(parent_post_rows) != 3 or not all(
        _truth(row["atom_block_identical"])
        and _truth(row["coordinate_block_identical"])
        and _truth(row["allowed_bond_order_change_only"])
        and _truth(row["pre_reaction_sdf_qa_passed"])
        for row in parent_post_rows
    ):
        raise ValueError("STAGE_A_DIRECT_PARENT_POST_TOPOLOGY_INVALID")

    registry: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    covpdb_sha = FROZEN_INPUT_SHA256[COVPDB_INVENTORY]

    for source_row, combined in zip(expansion_rows, covpdb_rows):
        if (
            source_row["source_candidate_id"] != combined["source_candidate_id"]
            or source_row["pdb_id"] != combined["pdb_id"]
            or source_row["expected_het_id"]
            != combined["suggested_ligand_comp_id"]
        ):
            raise ValueError("STAGE_A_COVPDB_PREDECESSOR_ORDER_MISMATCH")
        pdb_id = combined["pdb_id"]
        ligand = combined["suggested_ligand_comp_id"]
        key = (pdb_id, ligand)
        candidate_id = _candidate_id("CovPDB", combined["source_candidate_id"])
        gold = membership_by_key.get(key)
        exact_pair = False
        structural_key = "NONE"
        ligand_instance = "NONE"
        reactive_atom = combined["suggested_ligand_atom_name"] or "NONE"
        gold_match = "NONE"
        source_formula_rh = " Rh" in (" " + combined["ccd_formula"])
        graph_rh: bool | str = "EVIDENCE_NOT_AVAILABLE"

        if gold is not None:
            sample_id = gold["sample_index_row_id"]
            index = index_by_sample[sample_id]
            pair = pair_by_sample[sample_id]
            target = target_by_sample[sample_id]
            authority_record = effective_by_sample[sample_id][
                "effective_authority_record"
            ]
            if (
                index["pdb_id"] != pdb_id
                or pair["pdb_id"] != pdb_id
                or pair["ligand_comp_id"] != ligand
                or authority_record["pdb_id"] != pdb_id
                or authority_record["ligand_comp_id"] != ligand
                or pair["residue_comp_id"] != "CYS"
                or pair["residue_atom_name"] != "SG"
                or target["pdb_id"] != pdb_id
                or target["protein_auth_asym_id"]
                != pair["residue_auth_asym_id"]
                or target["protein_auth_seq_id"]
                != pair["residue_auth_seq_id"]
                or target["protein_auth_comp_id"] != "CYS"
                or target["protein_auth_atom_id"] != "SG"
                or target["condition_authority_status"]
                != "resolved_authoritative"
            ):
                raise ValueError("STAGE_A_CURRENT11_ROW_BINDING_MISMATCH")
            exact_pair = True
            reactive_atom = pair["ligand_atom_name"]
            cys_insertion = target["protein_pdbx_PDB_ins_code"] or "NONE"
            graph_rh = False
            ligand_instance = (
                pair["ligand_auth_asym_id"] + ":" + pair["ligand_auth_seq_id"]
            )
            structural_key = _event_key(
                pdb_id=pdb_id,
                protein_chain=pair["residue_auth_asym_id"],
                cys_sequence=pair["residue_auth_seq_id"],
                cys_insertion=cys_insertion,
                ligand_chain=pair["ligand_auth_asym_id"],
                ligand_component=ligand,
                ligand_sequence=pair["ligand_auth_seq_id"],
                ligand_atom=reactive_atom,
            )
            gold_match = sample_id
            component_values = {
                "source_identity_status": "REGISTERED_SOURCE_IDENTITY_VALIDATED",
                "cys_sg_event_status": "EXACT_CYS_SG_CANONICAL",
                "reactive_pair_status": "EXACT_REACTIVE_PAIR_CANONICAL",
                "coordinate_status": "COORDINATES_VALIDATED",
                "ligand_component_identity_status": "LIGAND_COMPONENT_VALIDATED",
                "parent_post_topology_status": "CURRENT11_PARENT_POST_TOPOLOGY_VALIDATED",
                "exact10_status": "EXACT10_MODEL_BOUND_GRAPH_VALIDATED",
                "pocket_readiness_status": "POCKET_MATERIALIZED_VALIDATED",
                "gold_duplicate_status": "CURRENT11_GOLD_PRIMARY",
                "canonical_eligibility_status": "GOLD_PROTECTED",
            }
            disposition = "GOLD_REFERENCE"
            primary_issue = "NONE"
            confidence = "GOLD"
            golden_id = GOLDEN_SET_ID
            protein_chain = pair["residue_auth_asym_id"]
            cys_sequence = pair["residue_auth_seq_id"]
            evidence_ids = (
                "covpdb_inventory|current11_membership|current11_pair|"
                "current11_target_residue_atom_authority|"
                "current11_effective_authority|exact10_policy"
            )
        else:
            protein_chain = combined["covpdb_chain_id"] or "NONE"
            cys_sequence = combined["covpdb_residue_index"] or "NONE"
            cys_insertion = "NONE"
            confidence = "EXPANSION_CANDIDATE"
            golden_id = "NONE"
            component_values = {
                "source_identity_status": "REGISTERED_SOURCE_IDENTITY_VALIDATED",
                "cys_sg_event_status": "CYS_PRESENT_SG_EVENT_EVIDENCE_MISSING",
                "reactive_pair_status": "REACTIVE_PAIR_EVIDENCE_MISSING",
                "coordinate_status": "COORDINATE_EVIDENCE_MISSING",
                "ligand_component_identity_status": "LIGAND_COMPONENT_METADATA_BOUND",
                "parent_post_topology_status": "PARENT_POST_TOPOLOGY_EVIDENCE_MISSING",
                "exact10_status": "EXACT10_MODEL_GRAPH_EVIDENCE_MISSING",
                "pocket_readiness_status": "POCKET_EVIDENCE_MISSING",
                "gold_duplicate_status": "NO_KNOWN_GOLD_DUPLICATE",
                "canonical_eligibility_status": "STAGE_A_EVIDENCE_INCOMPLETE",
            }
            disposition = "HUMAN_REVIEW_REQUIRED"
            primary_issue = "SG_EVENT_EVIDENCE_MISSING"
            evidence_ids = (
                "covpdb_inventory|expansion_source_inventory|expansion_exclusion"
            )

            if key == ("1ATK", "E64"):
                exclusion = exclusions.get(key)
                if exclusion is None or exclusion["exclusion_reason_code"] != (
                    "lower_priority_duplicate_het_representative"
                ):
                    raise ValueError("STAGE_A_1ATK_DUPLICATE_EVIDENCE_MISSING")
                exact_pair = True
                gold_match = membership_by_key[("1AEC", "E64")][
                    "sample_index_row_id"
                ]
                component_values.update({
                    "cys_sg_event_status":
                        "EXACT_PAIR_EVIDENCE_CANONICAL_INSTANCE_UNRESOLVED",
                    "reactive_pair_status":
                        "EXACT_PAIR_EVIDENCED_PENDING_CANONICAL_INSTANCE",
                    "gold_duplicate_status":
                        "KNOWN_LOWER_PRIORITY_GOLD_DUPLICATE",
                    "canonical_eligibility_status":
                        "STAGE_A_FUNDAMENTAL_REJECT",
                })
                disposition = "REJECT"
                primary_issue = "KNOWN_LOWER_PRIORITY_GOLD_DUPLICATE"
                issues.append(_issue(
                    candidate_id,
                    "GOLD_DUPLICATE",
                    primary_issue,
                    disposition,
                    "covapie_expansion_candidate_exclusion_audit",
                    review_required=False,
                    fundamental_reject=True,
                    resolved=True,
                ))
            elif key == ("6BV9", "JUG"):
                exclusion = exclusions.get(key)
                if exclusion is None or exclusion["exclusion_reason_code"] != (
                    "known_ligand_comp_mismatch"
                ):
                    raise ValueError("STAGE_A_6BV9_MISMATCH_EVIDENCE_MISSING")
                component_values.update({
                    "cys_sg_event_status": "CYS_SG_EVENT_COMPONENT_MISMATCH",
                    "reactive_pair_status": "REACTIVE_PAIR_COMPONENT_MISMATCH",
                    "coordinate_status": "COORDINATE_COMPONENT_MISMATCH",
                    "ligand_component_identity_status":
                        "LIGAND_COMPONENT_MISMATCH",
                    "canonical_eligibility_status":
                        "STAGE_A_FUNDAMENTAL_REJECT",
                })
                disposition = "REJECT"
                primary_issue = "LIGAND_COMPONENT_MISMATCH"
                issues.append(_issue(
                    candidate_id,
                    "LIGAND_COMPONENT_IDENTITY",
                    primary_issue,
                    disposition,
                    "covapie_expansion_candidate_source_inventory",
                    review_required=False,
                    fundamental_reject=True,
                    resolved=True,
                ))
            else:
                if key == ("1A54", "MDC"):
                    primary_issue = "STRUCT_CONN_LOOP_ABSENT"
                issues.append(_issue(
                    candidate_id,
                    "CYS_SG_EVENT",
                    primary_issue,
                    disposition,
                    "covapie_expansion_candidate_source_inventory",
                    review_required=True,
                    fundamental_reject=False,
                    resolved=False,
                ))
                if key == ("6VWE", "JY1"):
                    if not source_formula_rh:
                        raise ValueError("STAGE_A_6VWE_RH_FORMULA_EVIDENCE_MISSING")
                    exact10 = evaluate_exact10_model_bound_graph_v1(
                        None, source_formula_unsupported_elements=("Rh",)
                    )
                    component_values["exact10_status"] = exact10.status
                    primary_issue = (
                        "EXACT10_FORMULA_RH_GRAPH_INCLUSION_UNRESOLVED"
                    )
                    issues.append(_issue(
                        candidate_id,
                        "EXACT10",
                        primary_issue,
                        disposition,
                        "covpdb_source_formula_plus_exact10_policy",
                        review_required=True,
                        fundamental_reject=False,
                        resolved=False,
                    ))

        registry.append({
            "canonical_candidate_id": candidate_id,
            "candidate_registry_index": len(registry) + 1,
            "source_identity": "CovPDB",
            "source_provenance_identities": "CovPDB",
            "source_record_identity": combined["source_candidate_id"],
            "source_record_version": combined["candidate_source_stage"],
            "pdb_id": pdb_id,
            "protein_chain": protein_chain,
            "cys_residue_sequence": cys_sequence,
            "cys_insertion_code": cys_insertion,
            "ligand_component_id": ligand,
            "ligand_instance_if_available": ligand_instance,
            "reactive_residue_atom": "SG",
            "reactive_ligand_atom_if_known": reactive_atom,
            "dataset_confidence_tier": confidence,
            "golden_set_id_or_none": golden_id,
            "current11_gold_match": gold_match,
            "structural_event_key_if_resolved": structural_key,
            "exact_pair_evidenced": exact_pair,
            "source_formula_contains_Rh": source_formula_rh,
            "canonical_model_graph_contains_Rh": graph_rh,
            **component_values,
            "registry_disposition": disposition,
            "primary_issue_code_or_NONE": primary_issue,
            "predecessor_row_identity": source_row["expansion_source_record_id"],
            "predecessor_source_path": COVPDB_INVENTORY.as_posix(),
            "predecessor_source_sha256": covpdb_sha,
            "evidence_identity_ids": evidence_ids,
        })

    direct_sha = FROZEN_INPUT_SHA256[DIRECT_CONFIRMED]
    for direct in direct_rows:
        review_id = direct["review_row_id"]
        pair = direct_pair_by_review.get(review_id)
        topology = topology_audit_by_review.get(review_id)
        pocket = pocket_audit_by_review.get(review_id)
        model_index = model_index_by_review.get(review_id)
        model_qa = model_qa_by_review.get(review_id)
        if None in (pair, topology, pocket, model_index, model_qa):
            raise ValueError("STAGE_A_DIRECT_LOCAL_EVIDENCE_JOIN_MISSING")
        if not (
            _truth(direct["manual_review_validated"])
            and _truth(direct["coordinate_extraction_ready"])
            and _truth(pair["coordinate_pair_sanity_passed"])
            and _truth(pair["coordinates_extracted"])
            and _truth(topology["topology_smoke_retry_passed"])
            and _truth(pocket["pocket_extraction_passed"])
            and _truth(model_qa["model_input_smoke_row_qa_passed"])
            and model_index["residue_name"] == "CYS"
            and model_index["residue_atom_name"] == "SG"
        ):
            raise ValueError("STAGE_A_DIRECT_LOCAL_COMPONENT_EVIDENCE_INVALID")
        symbols = topology_symbols[review_id] + pocket_symbols[review_id]
        exact10 = evaluate_exact10_model_bound_graph_v1(symbols)
        if exact10.sample_rejected or not exact10.canonical_graph_evidence_available:
            raise ValueError("STAGE_A_DIRECT_LOCAL_EXACT10_INVALID")

        pdb_id = direct["pdb_id"]
        ligand = direct["manual_confirmed_ligand_comp_id"]
        candidate_id = _candidate_id(
            "PDB/mmCIF direct", direct["confirmed_candidate_id"]
        )
        protein_chain = direct["ptnr1_auth_asym_id"]
        cys_sequence = direct["ptnr1_auth_seq_id"]
        ligand_chain = direct["ptnr2_auth_asym_id"]
        ligand_sequence = direct["ptnr2_auth_seq_id"]
        ligand_atom = direct["manual_confirmed_ligand_atom_id"]
        structural_key = _event_key(
            pdb_id=pdb_id,
            protein_chain=protein_chain,
            cys_sequence=cys_sequence,
            cys_insertion="NONE",
            ligand_chain=ligand_chain,
            ligand_component=ligand,
            ligand_sequence=ligand_sequence,
            ligand_atom=ligand_atom,
        )
        registry.append({
            "canonical_candidate_id": candidate_id,
            "candidate_registry_index": len(registry) + 1,
            "source_identity": "PDB/mmCIF direct",
            "source_provenance_identities": "PDB/mmCIF direct|local curated",
            "source_record_identity": direct["confirmed_candidate_id"],
            "source_record_version":
                "real_covalent_struct_conn_candidate_manual_review_fill_"
                "validation_v0",
            "pdb_id": pdb_id,
            "protein_chain": protein_chain,
            "cys_residue_sequence": cys_sequence,
            "cys_insertion_code": "NONE",
            "ligand_component_id": ligand,
            "ligand_instance_if_available":
                ligand_chain + ":" + ligand_sequence,
            "reactive_residue_atom": "SG",
            "reactive_ligand_atom_if_known": ligand_atom,
            "dataset_confidence_tier": "EXPANSION_CANDIDATE",
            "golden_set_id_or_none": "NONE",
            "current11_gold_match": "NONE",
            "structural_event_key_if_resolved": structural_key,
            "exact_pair_evidenced": True,
            "source_formula_contains_Rh": False,
            "canonical_model_graph_contains_Rh": False,
            "source_identity_status": "REGISTERED_SOURCE_IDENTITY_VALIDATED",
            "cys_sg_event_status": "EXACT_CYS_SG_CANONICAL",
            "reactive_pair_status": "EXACT_REACTIVE_PAIR_CANONICAL",
            "coordinate_status": "COORDINATES_VALIDATED",
            "ligand_component_identity_status": "LIGAND_COMPONENT_VALIDATED",
            "parent_post_topology_status":
                "LEGACY_PARENT_POST_TOPOLOGY_VALIDATED_FOR_STAGE_A",
            "exact10_status": exact10.status,
            "pocket_readiness_status": "POCKET_MATERIALIZED_VALIDATED",
            "gold_duplicate_status": "NO_KNOWN_GOLD_DUPLICATE",
            "canonical_eligibility_status": "STAGE_A_CANONICAL_ELIGIBLE",
            "registry_disposition": "ELIGIBLE_FOR_STAGE_B",
            "primary_issue_code_or_NONE": "NONE",
            "predecessor_row_identity": direct["confirmed_candidate_id"],
            "predecessor_source_path": DIRECT_CONFIRMED.as_posix(),
            "predecessor_source_sha256": direct_sha,
            "evidence_identity_ids": (
                "direct_local_confirmed_event|direct_local_coordinate_pair|"
                "direct_local_topology|direct_local_pocket|"
                "direct_local_model_graph|exact10_policy"
            ),
        })

    if len(registry) != 28 or len({row["canonical_candidate_id"] for row in registry}) != 28:
        raise ValueError("STAGE_A_REGISTRY_CARDINALITY_OR_IDENTITY_INVALID")
    if len({row["structural_event_key_if_resolved"] for row in registry if row[
        "structural_event_key_if_resolved"
    ] != "NONE"}) != 14:
        raise ValueError("STAGE_A_STRUCTURAL_EVENT_IDENTITY_COLLISION")

    issues.sort(key=lambda row: (
        row["canonical_candidate_id"], row["issue_stage"], row["issue_code"]
    ))
    for index, row in enumerate(issues, start=1):
        row["issue_inventory_index"] = index
    return registry, issues


def _input_evidence_inventory(
    payloads: Mapping[Path, bytes],
    design: bytes,
    current11_state: bytes,
    current11_target_state: bytes,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path, payload in payloads.items():
        is_csv = path.suffix == ".csv"
        rows.append({
            "path_or_authority_identity": path.as_posix(),
            "source_role": INPUT_ROLES[path],
            "sha256": _sha256(payload),
            "row_or_relevant_identity_count":
                len(_csv_rows(payload)) if is_csv else 1,
        })
    rows.extend((
        {
            "path_or_authority_identity":
                "state://" + DESIGN_REPORT_RELATIVE.as_posix(),
            "source_role": "stage_a_design_authority",
            "sha256": _sha256(design),
            "row_or_relevant_identity_count": 1,
        },
        {
            "path_or_authority_identity":
                "state://" + CURRENT11_STATE_RELATIVE.as_posix(),
            "source_role": "current11_effective_human_authority",
            "sha256": _sha256(current11_state),
            "row_or_relevant_identity_count": 11,
        },
        {
            "path_or_authority_identity":
                "state://" + CURRENT11_TARGET_STATE_RELATIVE.as_posix(),
            "source_role": "current11_target_residue_atom_authority",
            "sha256": _sha256(current11_target_state),
            "row_or_relevant_identity_count": 11,
        },
    ))
    return sorted(rows, key=lambda row: row["path_or_authority_identity"])


def _manifest(
    registry: Sequence[Mapping[str, Any]],
    issues: Sequence[Mapping[str, Any]],
    input_inventory: Sequence[Mapping[str, Any]],
    candidate_payload: bytes,
    issue_payload: bytes,
) -> dict[str, Any]:
    dispositions = Counter(row["registry_disposition"] for row in registry)
    gold_count = sum(row["dataset_confidence_tier"] == "GOLD" for row in registry)
    exact_rows = [row for row in registry if row["exact_pair_evidenced"] is True]
    source_counts = Counter(row["source_identity"] for row in registry)
    primary_source_counts = {
        source: source_counts.get(source, 0)
        for source in REGISTERED_SOURCE_IDENTITIES
    }
    provenance_counts = {
        source: sum(
            source in row["source_provenance_identities"].split("|")
            for row in registry
        )
        for source in REGISTERED_SOURCE_IDENTITIES
    }
    component_counts = {
        field: dict(sorted(Counter(row[field] for row in registry).items()))
        for field in COMPONENT_FIELDS
    }
    issue_ids = {row["canonical_candidate_id"] for row in issues}
    non_gold = [row for row in registry if row["dataset_confidence_tier"] != "GOLD"]
    review_or_reject = [
        row for row in non_gold
        if row["registry_disposition"] in {"HUMAN_REVIEW_REQUIRED", "REJECT"}
    ]
    pilot_matches = {
        f"{pdb_id}/{ligand}": next(
            (
                row["canonical_candidate_id"] for row in registry
                if (row["pdb_id"], row["ligand_component_id"])
                == (pdb_id, ligand)
            ),
            "NONE",
        )
        for pdb_id, ligand in PILOT_IDENTITIES
    }
    pilot_complete = all(value != "NONE" for value in pilot_matches.values())
    disposition_complete = (
        len(non_gold) == 17
        and all(row["registry_disposition"] in DISPOSITIONS[1:] for row in non_gold)
    )
    issue_coverage = all(
        row["canonical_candidate_id"] in issue_ids for row in review_or_reject
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "baseline_commit": BASELINE_COMMIT,
        "design_report_path": "state://" + DESIGN_REPORT_RELATIVE.as_posix(),
        "design_report_sha256": DESIGN_REPORT_SHA256,
        "candidate_scope": "EXACT5_ADDITIONS_ONLY",
        "input_evidence_identities": list(input_inventory),
        "registry_candidate_count": len(registry),
        "current11_gold_count": gold_count,
        "non_gold_expansion_candidate_count": len(registry) - gold_count,
        "exact_pair_evidenced_total_count": len(exact_rows),
        "exact_pair_evidenced_gold_count": sum(
            row["dataset_confidence_tier"] == "GOLD" for row in exact_rows
        ),
        "exact_pair_evidenced_non_gold_count": sum(
            row["dataset_confidence_tier"] != "GOLD" for row in exact_rows
        ),
        "gold_reference_count": dispositions["GOLD_REFERENCE"],
        "eligible_for_stage_b_count": dispositions["ELIGIBLE_FOR_STAGE_B"],
        "human_review_required_count": dispositions["HUMAN_REVIEW_REQUIRED"],
        "reject_count": dispositions["REJECT"],
        "issue_row_count": len(issues),
        "source_counts": primary_source_counts,
        "source_provenance_identity_counts": provenance_counts,
        "registered_source_identity_count": len(REGISTERED_SOURCE_IDENTITIES),
        "partially_operational_local_source_path_count":
            len(PARTIALLY_OPERATIONAL_LOCAL_SOURCE_IDENTITIES),
        "component_status_counts": component_counts,
        "known_gold_duplicate_count": sum(
            row["gold_duplicate_status"]
            == "KNOWN_LOWER_PRIORITY_GOLD_DUPLICATE"
            for row in registry
        ),
        "all_non_gold_candidates_disposition_complete": disposition_complete,
        "all_reject_review_have_issue_rows": issue_coverage,
        "eight_pilot_identity_to_candidate_id": pilot_matches,
        "eight_pilot_identities_present": pilot_complete,
        "deterministic_output_hashes": {
            CANDIDATE_FILE: _sha256(candidate_payload),
            ISSUE_FILE: _sha256(issue_payload),
        },
        "manifest_self_sha256_recorded": False,
        "feature_semantics_policy_id": FEATURE_SEMANTICS_POLICY_ID,
        "exact10_checkpoint_channel_order":
            exact10_owner.CHECKPOINT_CHANNEL_ORDER,
        "unknown_other_channel_added": False,
        "zero_vector_fallback_added": False,
        "geometry_executed": False,
        "geometry_weight": 0.0,
        "geometry_loss_activation": False,
        "inverse_reaction_templates_created": False,
        "rdkit_minimization_executed": False,
        "model_executed": False,
        "model_forward": False,
        "backward": False,
        "optimizer_step": False,
        "trainer_fit": False,
        "rl": False,
        "training_executed": False,
        "bulk_download_executed": False,
        "ready_for_stage_a_publication":
            len(registry) == 28 and disposition_complete and issue_coverage,
        "ready_for_stage_b_automated_label_and_geometry_pilot":
            len(registry) == 28
            and disposition_complete
            and issue_coverage
            and pilot_complete,
        "ready_for_bulk_expansion": False,
        "ready_for_geometry_loss_activation": False,
        "ready_for_formal_training": False,
        "ready_for_training": False,
        "recommended_next_step": RECOMMENDED_NEXT_STEP,
    }


def build_covapie_cys_sg_expanded_source_candidate_inventory_and_canonical_eligibility_artifacts_v1(
    *,
    repo_root: Path = REPO_ROOT,
    state_root: Path = STATE_ROOT,
) -> dict[str, bytes]:
    payloads, design, current11_state, current11_target_state = _load_inputs(
        repo_root, state_root
    )
    _validate_source_registry(payloads[SOURCE_REGISTRY])
    _validate_feature_policy(payloads[FEATURE_MANIFEST])
    registry, issues = _build_registry(
        payloads, current11_state, current11_target_state
    )
    candidate_payload = _csv_bytes(registry, CANDIDATE_COLUMNS)
    issue_payload = _csv_bytes(issues, ISSUE_COLUMNS)
    manifest = _manifest(
        registry,
        issues,
        _input_evidence_inventory(
            payloads, design, current11_state, current11_target_state
        ),
        candidate_payload,
        issue_payload,
    )
    return {
        CANDIDATE_FILE: candidate_payload,
        ISSUE_FILE: issue_payload,
        MANIFEST_FILE: _json_bytes(manifest),
    }


def materialize_covapie_cys_sg_expanded_source_candidate_inventory_and_canonical_eligibility_v1(
    output_root: Path = REPO_ROOT / OUTPUT_ROOT,
    *,
    repo_root: Path = REPO_ROOT,
    state_root: Path = STATE_ROOT,
) -> dict[str, str]:
    artifacts = (
        build_covapie_cys_sg_expanded_source_candidate_inventory_and_canonical_eligibility_artifacts_v1(
            repo_root=repo_root, state_root=state_root
        )
    )
    output_root.mkdir(parents=True, exist_ok=True, mode=0o755)
    os.chmod(output_root, 0o755)
    hashes: dict[str, str] = {}
    for filename in OUTPUT_FILES:
        path = output_root / filename
        path.write_bytes(artifacts[filename])
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        hashes[filename] = _sha256(artifacts[filename])
    return hashes


def main() -> None:
    hashes = (
        materialize_covapie_cys_sg_expanded_source_candidate_inventory_and_canonical_eligibility_v1()
    )
    print(json.dumps(hashes, sort_keys=True))


if __name__ == "__main__":
    main()
