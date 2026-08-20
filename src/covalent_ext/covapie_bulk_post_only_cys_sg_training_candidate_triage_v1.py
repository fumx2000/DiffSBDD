"""Build the additive CovaPIE post-only CYS-SG review lane V1.

This module is deliberately read-only with respect to the published bulk
artifacts, task cache, chemistry authority registry, and cumulative leakage
registry.  It creates a review-candidate inventory, not production authority.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any

from covalent_ext import covapie_bulk_cys_sg_dataset_expansion_v1 as bulk


SCHEMA_VERSION = "covapie_bulk_post_only_cys_sg_training_candidate_triage_v1"
STAGE = "covapie_bulk_post_only_cys_sg_training_candidate_triage_v1"
BASE_HEAD = "fcfbad99eb7a634b571259f5c1abe5272990ede1"
BASE_SUBJECT = "resolve CovaPIE bulk historical leakage extension v1"

INPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_cys_sg_dataset_expansion_v1/bulk_pilot_v1"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_post_only_cys_sg_training_candidate_triage_v1"
)
CACHE_ROOT_RELATIVE_TO_REPOSITORY_PARENT = Path(
    "covapie-state/bulk-multisource-cys-sg-v1"
)

INPUT_SHA256 = {
    "bulk_acquisition_manifest_v1.json": (
        "b12b0e29d223d7469c81e6cbfe0d8eaf7aa4f8a18368b65843df8e63c75afe46"
    ),
    "bulk_human_review_clusters_v1.json": (
        "ebe2343ec21b9fc9006c162975beb2e8fb4a7a419def97df8948e3b62339a06d"
    ),
    "bulk_processing_outcomes_v1.json": (
        "0270dd93a31427042d02f7751ab7b46679308c7f1ee5207a5560b199a6a94d57"
    ),
    "bulk_source_access_resolution_v1.json": (
        "a31567f3b2202b3b1c29d22fd2c2d908192bed2bb659b273861cd3dacc6c5bc9"
    ),
    "bulk_summary_v1.json": (
        "5af3abd8cc7f608352f1a6636cb810cbb404f439cc8083b9111be80654117462"
    ),
    "covalentindb_discovery_snapshot_v1.json": (
        "4352bdc005112f2710864e04a8011c03c2c19472ce20adac7ed5bd52a63a78e3"
    ),
    "covbinderinpdb_discovery_snapshot_v1.json": (
        "c1d492941dc0d9e46c6aa483823fc942d044eef6a0cf778822a0d93d2770dfe2"
    ),
    "covpdb_discovery_snapshot_v1.json": (
        "25c29f297a080d1ca86a6f5722e63e0adf37b51ff6df3d0465642cbe670b24e4"
    ),
    "cross_source_canonical_event_manifest_v1.json": (
        "d3f35987af92fca669b85d62a86914c7a01bf35d867c4a779e7fc08e76445dae"
    ),
    "rcsb_pdb_direct_discovery_snapshot_v1.json": (
        "3d374ce4d3863e4ede44523cc5172115097693912c04689ef7ef56b1ca235fdb"
    ),
}

PROTECTED_REGISTRY_SHA256 = {
    bulk.AUTHORITY_REGISTRY_RELATIVE: bulk.AUTHORITY_REGISTRY_SHA256,
    bulk.LEAKAGE_REGISTRY_RELATIVE: bulk.LEAKAGE_REGISTRY_SHA256,
}

EXPECTED_TASK_CACHE_DIGEST = (
    "35b704a02bdccd433f210235746be37fd7866c3e5b5ae8582d22e1b350ef69bd"
)
EXPECTED_TASK_CACHE_FILE_COUNT = 429
EXPECTED_TASK_CACHE_TOTAL_BYTES = 568379653

EVENT_INVENTORY = "covapie_bulk_post_only_training_candidate_event_inventory_v1.csv"
REVIEW_UNIT_INVENTORY = (
    "covapie_bulk_post_only_training_review_unit_inventory_v1.csv"
)
DOMAIN_EVIDENCE = (
    "covapie_bulk_post_only_training_domain_relevance_evidence_v1.csv"
)
SUMMARY = "covapie_bulk_post_only_training_candidate_summary_v1.json"
REVIEW_PACKET = "covapie_bulk_post_only_training_human_review_packet_v1.json"
GUIDE = "README.md"
OUTPUT_FILENAMES = (
    EVENT_INVENTORY,
    REVIEW_UNIT_INVENTORY,
    DOMAIN_EVIDENCE,
    SUMMARY,
    REVIEW_PACKET,
    GUIDE,
)

POST_ONLY_CANDIDATE = "POST_ONLY_V1_REVIEW_CANDIDATE"
BLOCKED_LEAKAGE = "BLOCKED_EXISTING_GROUP_CONFLICT"
BLOCKED_REPRESENTATION = "BLOCKED_REPRESENTATION_GAP"
OUTSIDE_STRUCTURAL = "OUTSIDE_STRUCTURAL_ELIGIBILITY"
KNOWN_EXISTING = "KNOWN_EXISTING_OUTSIDE_NEW_POPULATION"

RELEVANCE_SUPPORTED = "COVALENT_SMALL_MOLECULE_TASK_RELEVANCE_SUPPORTED"
RELEVANCE_NON_TARGET = "LIKELY_BIOCHEMICAL_OR_NON_TARGET_GENERATION_EVENT"
RELEVANCE_REVIEW = "TASK_RELEVANCE_HUMAN_REVIEW_REQUIRED"
RELEVANCE_INSUFFICIENT = "TASK_RELEVANCE_EVIDENCE_INSUFFICIENT"
RELEVANCE_NOT_EVALUATED = "NOT_EVALUATED_OUTSIDE_POST_ONLY_REVIEW_CANDIDATE"

UNIT_HUMAN_DECISION_FIELDS = (
    "review_status",
    "training_domain_relevance_decision",
    "warhead_family_decision",
    "warhead_atom_set_decision",
    "reactive_atom_confirmation",
    "scaffold_linker_warhead_role_decision",
    "reviewer_id",
    "review_rationale",
)

EVENT_HUMAN_DECISION_FIELDS = (
    "post_geometry_training_usable",
    "event_training_use_decision",
    "event_exclusion_reason",
)

EVENT_HEADER = (
    "canonical_event_id", "pdb_id", "ligand_component_id",
    "source_datasets_json", "population_status", "post_only_partition",
    "structural_model_eligible", "feature_compatible",
    "explicit_cys_sg_event", "usable_post_complex_structural_evidence",
    "target_residue_identity", "target_cys_chain_residue",
    "protein_reactive_atom", "ligand_instance", "ligand_reactive_atom",
    "ligand_reactive_element", "selected_connection_id",
    "selected_protein_endpoint_coordinates_json",
    "selected_ligand_endpoint_coordinates_json", "post_distance_angstrom",
    "reported_distance_angstrom", "selected_protein_altloc",
    "selected_ligand_altloc", "ligand_heavy_atom_count",
    "pocket_heavy_atom_count", "full_ligand_coordinates_recoverable",
    "exact_ccd_observed_heavy_atom_identity_coverage",
    "exact_ccd_observed_heavy_atom_element_agreement",
    "reactive_ligand_atom_exact_coverage",
    "canonical_pocket_coordinates_recoverable",
    "ligand_atom_inventory_sha256", "pocket_atom_inventory_sha256",
    "observed_heavy_atom_map_sha256", "ccd_heavy_atom_map_sha256",
    "ccd_component_graph_sha256", "reactive_center_radius1_fingerprint",
    "reactive_center_radius2_fingerprint", "reactive_center_local_topology",
    "source_annotations_json", "annotation_conflicts_json",
    "leakage_classification", "predicted_group_id", "predicted_split",
    "leakage_linking_axes_json", "pre_status",
    "pre_status_diagnostic_only_for_post_only_triage",
    "training_domain_relevance_status",
    "training_domain_relevance_human_review_required",
    "post_geometry_auxiliary_labels_status",
    "production_chemistry_authority_status", "production_approval_created",
    "terminal_outcome", "terminal_reasons_json",
)

REVIEW_UNIT_HEADER = (
    "review_unit_id", "cluster_id", "event_count", "canonical_event_ids_json",
    "pdb_ids_json", "ligand_component_ids_json",
    "representative_canonical_event_id", "source_datasets_json",
    "source_annotations_json", "target_cys_identities_json",
    "ligand_reactive_atom", "ligand_reactive_elements_json",
    "reactive_center_local_topologies_json", "ccd_component_graph_sha256",
    "reactive_center_radius1_fingerprints_json",
    "reactive_center_radius2_fingerprint", "post_distance_min_angstrom",
    "post_distance_max_angstrom", "post_distance_mean_angstrom",
    "post_distance_distribution_json", "altloc_status",
    "ligand_heavy_atom_count_min", "ligand_heavy_atom_count_max",
    "pocket_coordinate_availability", "leakage_groups_json",
    "predicted_splits_json", "leakage_linking_axes_json", "pre_statuses_json",
    "pre_status_non_blocking_for_post_only_eligibility",
    "training_domain_relevance_status_distribution_json",
    "reasons_needing_human_review_json", "predecessor_review_unit_reused",
    "chemistry_identity_boundary_validated", "production_approval_created",
    "ccd_heavy_atom_inventory_count", "ccd_bond_inventory_count",
    "representative_observed_heavy_atom_coordinate_count",
    "exact_ccd_observed_coverage_status", "events_for_review_count",
    "event_level_human_decision_fields_json",
    *UNIT_HUMAN_DECISION_FIELDS,
)

DOMAIN_EVIDENCE_HEADER = (
    "canonical_event_id", "training_domain_relevance_status",
    "human_review_required", "source_dataset", "source_record_id",
    "evidence_field", "evidence_value", "evidence_used_for_machine_status",
    "evidence_role", "source_payload_sha256",
    "event_source_payload_sha256s_json", "binding_artifact_path",
    "binding_artifact_sha256", "source_annotation_is_production_authority",
    "classification_rule",
)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _json_cell(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _boolean(value: bool) -> str:
    return "true" if value else "false"


def _csv_bytes(header: Sequence[str], rows: Sequence[Mapping[str, object]]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output, fieldnames=list(header), lineterminator="\n", extrasaction="raise"
    )
    writer.writeheader()
    for row in rows:
        if tuple(row) != tuple(header):
            raise ValueError("CSV_ROW_SCHEMA_MISMATCH")
        writer.writerow(row)
    return output.getvalue().encode("utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON_ROOT_NOT_OBJECT:" + path.name)
    return value


def _git(repo_root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments], cwd=repo_root, check=True, capture_output=True, text=True
    )
    return completed.stdout.strip()


def verify_base_git_binding_v1(repo_root: Path) -> dict[str, object]:
    head = _git(repo_root, "rev-parse", "HEAD")
    origin = _git(repo_root, "rev-parse", "origin/main")
    subject = _git(repo_root, "show", "-s", "--format=%s", "HEAD")
    divergence = _git(repo_root, "rev-list", "--left-right", "--count", "HEAD...origin/main")
    try:
        ahead_text, behind_text = divergence.split()
        ahead, behind = int(ahead_text), int(behind_text)
    except (ValueError, TypeError) as error:
        raise ValueError("GIT_DIVERGENCE_OUTPUT_INVALID") from error
    if head != BASE_HEAD:
        raise ValueError("BASE_HEAD_BINDING_MISMATCH")
    if origin != BASE_HEAD:
        raise ValueError("ORIGIN_MAIN_BINDING_MISMATCH")
    if (ahead, behind) != (0, 0):
        raise ValueError("BASE_AHEAD_BEHIND_MISMATCH")
    if subject != BASE_SUBJECT:
        raise ValueError("BASE_SUBJECT_BINDING_MISMATCH")
    return {
        "head": head, "origin_main": origin, "ahead": ahead, "behind": behind,
        "head_subject": subject,
    }


def verify_bound_inputs_v1(repo_root: Path) -> dict[str, str]:
    input_root = repo_root / INPUT_ROOT_RELATIVE
    observed: dict[str, str] = {}
    for name, expected in INPUT_SHA256.items():
        path = input_root / name
        if not path.is_file():
            raise ValueError("BOUND_INPUT_MISSING:" + name)
        digest = _sha(path.read_bytes())
        if digest != expected:
            raise ValueError("BOUND_INPUT_SHA256_MISMATCH:" + name)
        observed[(INPUT_ROOT_RELATIVE / name).as_posix()] = digest
    for relative, expected in PROTECTED_REGISTRY_SHA256.items():
        path = repo_root / relative
        if not path.is_file() or _sha(path.read_bytes()) != expected:
            raise ValueError("PROTECTED_REGISTRY_SHA256_MISMATCH:" + relative.as_posix())
    return dict(sorted(observed.items()))


def task_cache_content_digest_v1(cache_root: Path) -> dict[str, object]:
    cache_root = cache_root.resolve()
    if not cache_root.is_dir():
        raise ValueError("TASK_CACHE_ROOT_MISSING")
    files: list[Path] = []
    for path in cache_root.rglob("*"):
        if path.is_symlink():
            raise ValueError("TASK_CACHE_SYMLINK_FORBIDDEN")
        if path.is_file():
            files.append(path)
    files.sort(key=lambda path: path.relative_to(cache_root).as_posix())
    aggregate = hashlib.sha256()
    total_bytes = 0
    for path in files:
        payload = path.read_bytes()
        total_bytes += len(payload)
        relative = path.relative_to(cache_root).as_posix()
        aggregate.update(f"{_sha(payload)}  ./{relative}\n".encode("utf-8"))
    result: dict[str, object] = {
        "digest_algorithm": "SHA256_OF_SORTED_SHA256SUM_RELATIVE_PATH_LINES_V1",
        "content_digest_sha256": aggregate.hexdigest(),
        "file_count": len(files),
        "total_bytes": total_bytes,
    }
    if result["content_digest_sha256"] != EXPECTED_TASK_CACHE_DIGEST:
        raise ValueError("TASK_CACHE_CONTENT_DIGEST_MISMATCH")
    if result["file_count"] != EXPECTED_TASK_CACHE_FILE_COUNT:
        raise ValueError("TASK_CACHE_FILE_COUNT_MISMATCH")
    if result["total_bytes"] != EXPECTED_TASK_CACHE_TOTAL_BYTES:
        raise ValueError("TASK_CACHE_TOTAL_BYTES_MISMATCH")
    return result


def post_only_partition_v1(
    outcome: Mapping[str, Any], *, known_event: bool,
) -> str:
    if known_event:
        return KNOWN_EXISTING
    stage = outcome.get("stage_statuses", {}).get(
        "BULK_09_MODEL_AND_FEATURE_COMPATIBILITY"
    )
    if stage != "PASSED":
        return OUTSIDE_STRUCTURAL
    route = outcome.get("terminal_outcome")
    if route == "HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY":
        return POST_ONLY_CANDIDATE
    if route == "LEAKAGE_EXISTING_GROUP_CONFLICT":
        return BLOCKED_LEAKAGE
    if route == "QUARANTINE_REPRESENTATION_GAP":
        return BLOCKED_REPRESENTATION
    raise ValueError("STRUCTURALLY_ELIGIBLE_NEW_EVENT_PARTITION_UNRESOLVED")


def classify_training_domain_relevance_v1(
    event: Mapping[str, Any],
) -> tuple[str, str]:
    reactions = sorted({
        str(annotation["reaction"]).strip().lower()
        for annotation in event.get("source_annotations", [])
        if annotation.get("source_dataset") == "SOURCE_COVBINDERINPDB"
        and str(annotation.get("reaction") or "").strip()
    })
    if not reactions:
        return (
            RELEVANCE_INSUFFICIENT,
            "NO_SPECIALIST_REACTION_FIELD; HUMAN REVIEW REQUIRED",
        )
    if len(reactions) != 1:
        return (
            RELEVANCE_REVIEW,
            "AMBIGUOUS_SPECIALIST_REACTION_FIELDS; HUMAN REVIEW REQUIRED",
        )
    reaction = reactions[0]
    if reaction in {"inhibitor", "probe"}:
        return (
            RELEVANCE_SUPPORTED,
            "SPECIALIST_REACTION_FIELD_IN_EXACT_SUPPORTING_VOCABULARY",
        )
    if reaction == "substrate":
        return (
            RELEVANCE_NON_TARGET,
            "SPECIALIST_REACTION_FIELD_EQUALS_SUBSTRATE; LIKELY STATUS ONLY",
        )
    return (
        RELEVANCE_REVIEW,
        "SPECIALIST_REACTION_FIELD_NOT_MACHINE_DISPOSITIVE; HUMAN REVIEW REQUIRED",
    )


def _source_payload_sha(
    annotation: Mapping[str, Any], snapshots: Mapping[str, Mapping[str, Any]],
) -> str:
    dataset = str(annotation.get("source_dataset") or "")
    record_id = str(annotation.get("source_record_id") or "")
    if dataset == "SOURCE_COVBINDERINPDB":
        return str(snapshots["covbinder"].get("source_payload_sha256") or "")
    if dataset == "SOURCE_COVPDB" and record_id.startswith("CovPDB_complexes/"):
        return str(snapshots["covpdb"].get("complex_archive_sha256") or "")
    if dataset == "SOURCE_COVPDB":
        return str(snapshots["covpdb"].get("source_payload_sha256") or "")
    return ""


def _normalized_element(value: object, *, owner: str) -> str:
    element = str(value or "").strip().title()
    if not element:
        raise ValueError(owner + "_ELEMENT_EMPTY")
    return element


def exact_ccd_observed_heavy_atom_coverage_v1(
    *, observed_atoms: Sequence[Mapping[str, Any]],
    ccd_atoms: Sequence[Mapping[str, Any]], reactive_atom_id: str,
) -> dict[str, Any]:
    """Prove exact atom-wise heavy-atom coverage, never count-only coverage."""

    reactive_atom_id = str(reactive_atom_id).strip()
    if not reactive_atom_id:
        raise ValueError("REACTIVE_LIGAND_ATOM_ID_EMPTY")
    observed_heavy: list[dict[str, Any]] = []
    for atom in observed_atoms:
        element = _normalized_element(atom.get("element"), owner="OBSERVED_ATOM")
        if element == "H":
            continue
        atom_id = str(atom.get("atom_id") or "").strip()
        if not atom_id:
            raise ValueError("OBSERVED_HEAVY_ATOM_ID_EMPTY")
        coordinates = []
        for field in ("x", "y", "z"):
            try:
                coordinate = float(atom[field])
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(
                    "OBSERVED_HEAVY_ATOM_COORDINATE_INVALID:" + atom_id + ":" + field
                ) from error
            if not math.isfinite(coordinate):
                raise ValueError(
                    "OBSERVED_HEAVY_ATOM_COORDINATE_NONFINITE:" + atom_id + ":" + field
                )
            coordinates.append(coordinate)
        observed_heavy.append({
            "atom_id": atom_id,
            "element": element,
            "x": coordinates[0],
            "y": coordinates[1],
            "z": coordinates[2],
            "selected_altloc": atom.get("selected_altloc"),
            "selected_model": str(atom.get("selected_model") or "1"),
        })
    reactive_observed_count = sum(
        atom["atom_id"] == reactive_atom_id for atom in observed_heavy
    )
    if reactive_observed_count != 1:
        raise ValueError(
            "REACTIVE_LIGAND_ATOM_OBSERVED_COUNT_INVALID:"
            + reactive_atom_id + ":" + str(reactive_observed_count)
        )
    observed_counts = Counter(atom["atom_id"] for atom in observed_heavy)
    observed_duplicates = sorted(
        atom_id for atom_id, count in observed_counts.items() if count != 1
    )
    if observed_duplicates:
        raise ValueError(
            "OBSERVED_HEAVY_ATOM_ID_DUPLICATE:" + ",".join(observed_duplicates)
        )

    ccd_heavy: list[dict[str, Any]] = []
    for atom in ccd_atoms:
        element = _normalized_element(
            atom.get("element", atom.get("type_symbol")), owner="CCD_ATOM"
        )
        if element == "H":
            continue
        atom_id = str(atom.get("atom_id") or "").strip()
        if not atom_id:
            raise ValueError("CCD_HEAVY_ATOM_ID_EMPTY")
        ccd_heavy.append({
            "atom_id": atom_id,
            "element": element,
            "formal_charge": atom.get("formal_charge", atom.get("charge")),
            "aromatic_flag": atom.get("aromatic_flag"),
        })
    ccd_counts = Counter(atom["atom_id"] for atom in ccd_heavy)
    ccd_duplicates = sorted(
        atom_id for atom_id, count in ccd_counts.items() if count != 1
    )
    if ccd_duplicates:
        raise ValueError("CCD_HEAVY_ATOM_ID_DUPLICATE:" + ",".join(ccd_duplicates))
    reactive_ccd_count = sum(atom["atom_id"] == reactive_atom_id for atom in ccd_heavy)
    if reactive_ccd_count != 1:
        raise ValueError(
            "REACTIVE_LIGAND_ATOM_CCD_COUNT_INVALID:"
            + reactive_atom_id + ":" + str(reactive_ccd_count)
        )

    observed_by_id = {atom["atom_id"]: atom for atom in observed_heavy}
    ccd_by_id = {atom["atom_id"]: atom for atom in ccd_heavy}
    missing_observed = sorted(set(ccd_by_id) - set(observed_by_id))
    unexpected_observed = sorted(set(observed_by_id) - set(ccd_by_id))
    if missing_observed or unexpected_observed:
        raise ValueError(
            "EXACT_CCD_OBSERVED_HEAVY_ATOM_ID_SET_MISMATCH:"
            "missing_observed=" + ",".join(missing_observed)
            + ";unexpected_observed=" + ",".join(unexpected_observed)
        )
    element_mismatches = [
        f"{atom_id}:{ccd_by_id[atom_id]['element']}:{observed_by_id[atom_id]['element']}"
        for atom_id in sorted(ccd_by_id)
        if ccd_by_id[atom_id]["element"] != observed_by_id[atom_id]["element"]
    ]
    if element_mismatches:
        raise ValueError(
            "EXACT_CCD_OBSERVED_HEAVY_ATOM_ELEMENT_MISMATCH:"
            + ",".join(element_mismatches)
        )
    observed_heavy.sort(key=lambda atom: atom["atom_id"])
    ccd_heavy.sort(key=lambda atom: atom["atom_id"])
    return {
        "status": "EXACT_CCD_OBSERVED_HEAVY_ATOM_IDENTITY_AND_ELEMENT_COVERAGE",
        "exact_atom_identity_coverage": True,
        "exact_element_agreement": True,
        "reactive_atom_exact_coverage": True,
        "observed_heavy_atom_map": observed_heavy,
        "ccd_heavy_atom_map": ccd_heavy,
        "observed_heavy_atom_map_sha256": _sha(_json_bytes(observed_heavy)),
        "ccd_heavy_atom_map_sha256": _sha(_json_bytes(ccd_heavy)),
    }


def _required_ccd_radius_heavy_atom_ids_v1(
    *, ccd: Mapping[str, Any], reactive_atom_id: str, radius: int = 2,
) -> list[str]:
    elements = {
        str(atom.get("atom_id") or ""): _normalized_element(
            atom.get("type_symbol"), owner="CCD_ATOM"
        )
        for atom in ccd.get("ccd_atom_inventory", [])
    }
    adjacency: dict[str, set[str]] = defaultdict(set)
    for bond in ccd.get("ccd_bond_inventory", []):
        first = str(bond.get("atom_id_1") or "")
        second = str(bond.get("atom_id_2") or "")
        if first and second:
            adjacency[first].add(second)
            adjacency[second].add(first)
    visited = {reactive_atom_id}
    frontier = {reactive_atom_id}
    for _step in range(radius):
        frontier = {
            neighbor for atom_id in frontier for neighbor in adjacency.get(atom_id, set())
        } - visited
        visited.update(frontier)
    return sorted(
        atom_id for atom_id in visited if elements.get(atom_id) not in {None, "H"}
    )


def _coordinate_audit_v1(
    *, candidate_events: Sequence[Mapping[str, Any]],
    outcome_by_id: Mapping[str, Mapping[str, Any]],
    acquisition: Mapping[str, Mapping[str, Any]], cache_root: Path,
) -> dict[str, dict[str, object]]:
    events_by_pdb: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for event in candidate_events:
        events_by_pdb[str(event["pdb_id"])].append(event)
    result: dict[str, dict[str, object]] = {}
    failures: list[str] = []
    for pdb_id in sorted(events_by_pdb):
        row = acquisition.get(pdb_id)
        if row is None or row.get("acquisition_status") != "SOURCE_VERIFIED":
            raise ValueError("CANDIDATE_STRUCTURE_ACQUISITION_NOT_VERIFIED:" + pdb_id)
        path = cache_root / "rcsb" / "structures" / f"{pdb_id}.cif.gz"
        payload = path.read_bytes()
        if _sha(payload) != row.get("compressed_sha256"):
            raise ValueError("CANDIDATE_MMCIF_CACHE_SHA256_MISMATCH:" + pdb_id)
        if len(payload) != int(row.get("compressed_byte_count", -1)):
            raise ValueError("CANDIDATE_MMCIF_CACHE_SIZE_MISMATCH:" + pdb_id)
        text = bulk._validate_mmcif_payload(payload, pdb_id)
        atom_rows = bulk.atom_site_owner.extract_atom_site_loop_rows_v0(text)
        _tags, connections, status, error = bulk.struct_conn_owner.parse_struct_conn_loop(text)
        if status == "raw_parse_error":
            raise ValueError("CANDIDATE_STRUCT_CONN_PARSE_ERROR:" + error)
        for event in sorted(
            events_by_pdb[pdb_id], key=lambda item: str(item["canonical_event_id"])
        ):
            event_id = str(event["canonical_event_id"])
            outcome = outcome_by_id[event_id]
            structural = outcome["structural_processing"]
            selected_id = str(structural["selected_connection_id"])
            matches = []
            for connection in connections:
                endpoints = bulk._connection_matches_event(connection, event)
                if endpoints is not None and bulk._conn_value(connection, "id") == selected_id:
                    matches.append((connection, endpoints[0], endpoints[1]))
            if len(matches) != 1:
                raise ValueError("SELECTED_CONNECTION_NOT_UNIQUE:" + event_id)
            _connection, protein_endpoint, ligand_endpoint = matches[0]
            protein_candidates = bulk._endpoint_candidates(
                atom_rows, endpoint=protein_endpoint, event=event, protein=True
            )
            ligand_candidates = bulk._endpoint_candidates(
                atom_rows, endpoint=ligand_endpoint, event=event, protein=False
            )
            selected_protein, selected_ligand = bulk._select_endpoint_pair(
                protein_candidates,
                ligand_candidates,
                reported_distance=structural["reported_distance_angstrom"],
            )
            protein_coordinates = list(bulk._coordinates(selected_protein))
            ligand_coordinates = list(bulk._coordinates(selected_ligand))
            if protein_coordinates != structural["protein_endpoint_coordinates"]:
                raise ValueError("PROTEIN_ENDPOINT_REPLAY_MISMATCH:" + event_id)
            if ligand_coordinates != structural["ligand_endpoint_coordinates"]:
                raise ValueError("LIGAND_ENDPOINT_REPLAY_MISMATCH:" + event_id)
            distance = round(math.dist(protein_coordinates, ligand_coordinates), 6)
            if distance != structural["post_distance_angstrom"]:
                raise ValueError("POST_DISTANCE_REPLAY_MISMATCH:" + event_id)
            ligand_atoms = bulk._selected_ligand_atoms(atom_rows, event, selected_ligand)
            pocket_atoms = bulk._selected_pocket_atoms(atom_rows, ligand_atoms)
            ligand_payload = bulk._canonical_json([
                {
                    "atom": bulk._atom_value(atom, "label_atom_id"),
                    "element": bulk._atom_value(atom, "type_symbol").title(),
                    "coordinates": list(bulk._coordinates(atom)),
                }
                for atom in ligand_atoms
            ])
            pocket_payload = bulk._canonical_json([
                {
                    "asym": bulk._atom_value(atom, "label_asym_id"),
                    "seq": bulk._atom_value(atom, "label_seq_id"),
                    "atom": bulk._atom_value(atom, "label_atom_id"),
                    "element": bulk._atom_value(atom, "type_symbol").title(),
                    "coordinates": list(bulk._coordinates(atom)),
                }
                for atom in pocket_atoms
            ])
            ligand_hash = _sha(ligand_payload)
            pocket_hash = _sha(pocket_payload)
            if ligand_hash != structural["ligand_atom_inventory_sha256"]:
                raise ValueError("LIGAND_COORDINATE_INVENTORY_REPLAY_MISMATCH:" + event_id)
            if pocket_hash != structural["pocket_atom_inventory_sha256"]:
                raise ValueError("POCKET_COORDINATE_INVENTORY_REPLAY_MISMATCH:" + event_id)
            ligand_heavy = bulk._element_inventory(ligand_atoms)
            pocket_heavy = bulk._element_inventory(pocket_atoms)
            ccd = structural.get("ccd_component_graph") or {}
            observed_atoms = [
                {
                    "atom_id": bulk._atom_value(atom, "label_atom_id"),
                    "element": bulk._atom_value(atom, "type_symbol").title(),
                    "x": bulk._coordinates(atom)[0],
                    "y": bulk._coordinates(atom)[1],
                    "z": bulk._coordinates(atom)[2],
                    "selected_altloc": (
                        bulk._atom_value(atom, "label_alt_id") or None
                    ),
                    "selected_model": (
                        bulk._atom_value(atom, "pdbx_PDB_model_num") or "1"
                    ),
                }
                for atom in ligand_atoms
            ]
            try:
                exact_coverage = exact_ccd_observed_heavy_atom_coverage_v1(
                    observed_atoms=observed_atoms,
                    ccd_atoms=ccd.get("ccd_atom_inventory", []),
                    reactive_atom_id=str(event["ligand_reactive_atom"]),
                )
            except ValueError as error:
                failures.append(event_id + "=" + str(error))
                continue
            full_ligand = bool(
                ligand_heavy
                and exact_coverage["exact_atom_identity_coverage"]
                and exact_coverage["exact_element_agreement"]
                and exact_coverage["reactive_atom_exact_coverage"]
            )
            pocket_available = bool(
                pocket_heavy
                and len(pocket_heavy) == structural["pocket_heavy_atom_count"]
            )
            required_radius2_ids = _required_ccd_radius_heavy_atom_ids_v1(
                ccd=ccd, reactive_atom_id=str(event["ligand_reactive_atom"]),
            )
            observed_ids = {
                str(atom["atom_id"])
                for atom in exact_coverage["observed_heavy_atom_map"]
            }
            result[event_id] = {
                "full_ligand_coordinates_recoverable": full_ligand,
                "exact_ccd_observed_heavy_atom_identity_coverage": True,
                "exact_ccd_observed_heavy_atom_element_agreement": True,
                "reactive_ligand_atom_exact_coverage": True,
                "canonical_pocket_coordinates_recoverable": pocket_available,
                "ligand_atom_inventory_sha256": ligand_hash,
                "pocket_atom_inventory_sha256": pocket_hash,
                "observed_heavy_atom_map": exact_coverage["observed_heavy_atom_map"],
                "ccd_heavy_atom_map": exact_coverage["ccd_heavy_atom_map"],
                "observed_heavy_atom_map_sha256": exact_coverage[
                    "observed_heavy_atom_map_sha256"
                ],
                "ccd_heavy_atom_map_sha256": exact_coverage[
                    "ccd_heavy_atom_map_sha256"
                ],
                "exact_ccd_observed_coverage_status": exact_coverage["status"],
                "required_radius2_heavy_atom_ids": required_radius2_ids,
                "required_local_heavy_atoms_observed": (
                    set(required_radius2_ids) <= observed_ids
                ),
            }
    if failures:
        raise ValueError(
            "REAL_CANDIDATE_EXACT_ATOM_IDENTITY_AUDIT_FAILED:"
            + "|".join(failures)
        )
    if set(result) != {str(event["canonical_event_id"]) for event in candidate_events}:
        raise ValueError("CANDIDATE_COORDINATE_AUDIT_COVERAGE_MISMATCH")
    return result


def validate_cluster_integrity_v1(
    *, units: Sequence[Mapping[str, Any]],
    clusters: Sequence[Mapping[str, Any]], candidate_ids: set[str],
) -> tuple[dict[str, str], dict[str, object]]:
    unit_by_id: dict[str, Mapping[str, Any]] = {}
    for unit in units:
        unit_id = str(unit["review_unit_id"])
        if unit_id in unit_by_id:
            raise ValueError("DUPLICATE_REVIEW_UNIT_ID:" + unit_id)
        unit_by_id[unit_id] = unit
    cluster_by_unit: dict[str, str] = {}
    all_cluster_events: list[str] = []
    seen_cluster_ids: set[str] = set()
    for cluster in clusters:
        cluster_id = str(cluster["cluster_id"])
        if cluster_id in seen_cluster_ids:
            raise ValueError("DUPLICATE_REVIEW_CLUSTER_ID:" + cluster_id)
        seen_cluster_ids.add(cluster_id)
        referenced_units = [str(value) for value in cluster["review_unit_ids"]]
        if len(referenced_units) != len(set(referenced_units)):
            raise ValueError("DUPLICATE_REVIEW_UNIT_WITHIN_CLUSTER:" + cluster_id)
        missing_units = sorted(set(referenced_units) - set(unit_by_id))
        if missing_units:
            raise ValueError(
                "CLUSTER_REFERENCES_UNKNOWN_REVIEW_UNIT:"
                + cluster_id + ":" + ",".join(missing_units)
            )
        declared_events = [str(value) for value in cluster["canonical_event_ids"]]
        if len(declared_events) != len(set(declared_events)):
            raise ValueError("DUPLICATE_EVENT_WITHIN_CLUSTER:" + cluster_id)
        unit_union = sorted({
            str(event_id)
            for unit_id in referenced_units
            for event_id in unit_by_id[unit_id]["canonical_event_ids"]
        })
        if sorted(declared_events) != unit_union or len(declared_events) != len(unit_union):
            raise ValueError("CLUSTER_TO_REVIEW_UNIT_EVENT_UNION_MISMATCH:" + cluster_id)
        all_cluster_events.extend(declared_events)
        for unit_id in referenced_units:
            if unit_id in cluster_by_unit:
                raise ValueError("REVIEW_UNIT_IN_MULTIPLE_CLUSTERS:" + unit_id)
            cluster_by_unit[unit_id] = cluster_id
    duplicate_across_clusters = sorted(
        event_id for event_id, count in Counter(all_cluster_events).items()
        if count != 1
    )
    if duplicate_across_clusters:
        raise ValueError(
            "DUPLICATE_EVENT_ACROSS_CLUSTERS:" + ",".join(duplicate_across_clusters)
        )
    if set(cluster_by_unit) != set(unit_by_id):
        raise ValueError("REVIEW_CLUSTER_UNIT_COVERAGE_MISMATCH")
    if set(all_cluster_events) != candidate_ids:
        raise ValueError("REVIEW_CLUSTER_CANDIDATE_COVERAGE_MISMATCH")
    return cluster_by_unit, {
        "review_unit_coverage_count": len(cluster_by_unit),
        "canonical_event_coverage_count": len(all_cluster_events),
        "duplicate_event_across_clusters_count": 0,
        "every_review_unit_exactly_one_cluster": True,
        "exact_cluster_to_review_unit_event_union": True,
        "cluster_union_equals_candidate_ids": True,
    }


def _validate_and_index_review_units_v1(
    *, artifact: Mapping[str, Any], candidate_ids: set[str],
    event_by_id: Mapping[str, Mapping[str, Any]],
    outcome_by_id: Mapping[str, Mapping[str, Any]],
) -> tuple[list[Mapping[str, Any]], dict[str, str], dict[str, object]]:
    units = artifact.get("review_units")
    clusters = artifact.get("clusters")
    if not isinstance(units, list) or not isinstance(clusters, list):
        raise ValueError("PREDECESSOR_REVIEW_ARTIFACT_SCHEMA_INVALID")
    seen: list[str] = []
    for unit in units:
        event_ids = [str(value) for value in unit["canonical_event_ids"]]
        if int(unit["event_count"]) != len(event_ids) or not event_ids:
            raise ValueError("REVIEW_UNIT_EVENT_COUNT_INVALID")
        seen.extend(event_ids)
        events = [event_by_id[event_id] for event_id in event_ids]
        outcomes = [outcome_by_id[event_id] for event_id in event_ids]
        components = {str(event["ligand_component_id"]) for event in events}
        reactive_atoms = {str(event["ligand_reactive_atom"]) for event in events}
        graph_hashes = {
            str(outcome["structural_processing"]["ccd_component_graph"][
                "ccd_component_graph_sha256"
            ])
            for outcome in outcomes
        }
        radius2 = {
            str(
                outcome["structural_processing"].get(
                    "reactive_center_radius2_sha256"
                ) or "UNAVAILABLE"
            )
            for outcome in outcomes
        }
        topologies = {
            str(
                outcome["structural_processing"].get(
                    "reactive_center_local_topology"
                ) or "UNAVAILABLE"
            )
            for outcome in outcomes
        }
        if not (
            len(components) == len(reactive_atoms) == len(graph_hashes)
            == len(radius2) == len(topologies) == 1
        ):
            raise ValueError("REVIEW_UNIT_CHEMISTRY_IDENTITY_BOUNDARY_INVALID")
        if components != set(unit["ligand_component_ids"]):
            raise ValueError("REVIEW_UNIT_COMPONENT_BINDING_INVALID")
        if reactive_atoms != {str(unit["reactive_atom"])}:
            raise ValueError("REVIEW_UNIT_REACTIVE_ATOM_BINDING_INVALID")
        if graph_hashes != {str(unit["ccd_component_graph_sha256"])}:
            raise ValueError("REVIEW_UNIT_CCD_GRAPH_BINDING_INVALID")
        expected_radius2 = str(
            unit["reactive_center_radius2_fingerprint"] or "UNAVAILABLE"
        )
        if radius2 != {expected_radius2}:
            raise ValueError("REVIEW_UNIT_RADIUS2_BINDING_INVALID")
    if len(seen) != len(set(seen)):
        raise ValueError("DUPLICATE_EVENT_ACROSS_REVIEW_UNITS")
    if set(seen) != candidate_ids:
        raise ValueError("REVIEW_UNIT_CANDIDATE_COVERAGE_MISMATCH")
    cluster_by_unit, cluster_integrity = validate_cluster_integrity_v1(
        units=units, clusters=clusters, candidate_ids=candidate_ids,
    )
    return units, cluster_by_unit, cluster_integrity


def _event_inventory_row(
    *, event: Mapping[str, Any], outcome: Mapping[str, Any], partition: str,
    coordinate: Mapping[str, object] | None, relevance_status: str,
) -> dict[str, object]:
    structural = outcome.get("structural_processing") or {}
    ccd = structural.get("ccd_component_graph") or {}
    is_candidate = partition == POST_ONLY_CANDIDATE
    structurally_eligible = outcome.get("stage_statuses", {}).get(
        "BULK_09_MODEL_AND_FEATURE_COMPATIBILITY"
    ) == "PASSED"
    complete_post = bool(
        is_candidate
        and structural.get("explicit_covalent_evidence") is True
        and coordinate
        and coordinate["full_ligand_coordinates_recoverable"]
        and coordinate["exact_ccd_observed_heavy_atom_identity_coverage"]
        and coordinate["exact_ccd_observed_heavy_atom_element_agreement"]
        and coordinate["reactive_ligand_atom_exact_coverage"]
        and coordinate["canonical_pocket_coordinates_recoverable"]
    )
    auxiliary = (
        "DERIVABLE_FROM_OBSERVED_POST_COORDINATES"
        if complete_post
        and structural.get("post_distance_angstrom") is not None
        and ccd.get("ccd_component_graph_sha256")
        and structural.get("reactive_center_radius2_sha256")
        and structural.get("reactive_center_local_topology")
        and coordinate
        and coordinate["required_local_heavy_atoms_observed"]
        else "NOT_AUDITED_OUTSIDE_POST_ONLY_REVIEW_CANDIDATE"
        if not is_candidate
        else "POST_COORDINATE_EVIDENCE_INCOMPLETE"
    )
    target_identity = (
        f"{event['protein_instance']}:CYS:{event['protein_residue_number']}"
        if is_candidate else ""
    )
    target_chain_residue = (
        f"{event.get('protein_auth_chain') or event['protein_instance']}:{event['protein_residue_number']}"
        if is_candidate else ""
    )
    row = {
        "canonical_event_id": event["canonical_event_id"],
        "pdb_id": event["pdb_id"],
        "ligand_component_id": event["ligand_component_id"],
        "source_datasets_json": _json_cell(event["source_datasets"]),
        "population_status": (
            "KNOWN_EXISTING_EVENT" if partition == KNOWN_EXISTING
            else "NEW_UNIQUE_CANDIDATE_EVENT"
        ),
        "post_only_partition": partition,
        "structural_model_eligible": _boolean(structurally_eligible),
        "feature_compatible": _boolean(
            structural.get("feature_projection_status") == "passed"
        ),
        "explicit_cys_sg_event": _boolean(
            structural.get("explicit_covalent_evidence") is True
        ),
        "usable_post_complex_structural_evidence": _boolean(complete_post),
        "target_residue_identity": target_identity,
        "target_cys_chain_residue": target_chain_residue,
        "protein_reactive_atom": event["protein_reactive_atom"] if is_candidate else "",
        "ligand_instance": event["ligand_instance"] if is_candidate else "",
        "ligand_reactive_atom": event["ligand_reactive_atom"] if is_candidate else "",
        "ligand_reactive_element": structural.get("ligand_reactive_element", "") if is_candidate else "",
        "selected_connection_id": structural.get("selected_connection_id", "") if is_candidate else "",
        "selected_protein_endpoint_coordinates_json": _json_cell(
            structural.get("protein_endpoint_coordinates", []) if is_candidate else []
        ),
        "selected_ligand_endpoint_coordinates_json": _json_cell(
            structural.get("ligand_endpoint_coordinates", []) if is_candidate else []
        ),
        "post_distance_angstrom": structural.get("post_distance_angstrom", "") if is_candidate else "",
        "reported_distance_angstrom": structural.get("reported_distance_angstrom", "") if is_candidate else "",
        "selected_protein_altloc": structural.get("selected_protein_altloc") or "" if is_candidate else "",
        "selected_ligand_altloc": structural.get("selected_ligand_altloc") or "" if is_candidate else "",
        "ligand_heavy_atom_count": structural.get("ligand_heavy_atom_count", "") if is_candidate else "",
        "pocket_heavy_atom_count": structural.get("pocket_heavy_atom_count", "") if is_candidate else "",
        "full_ligand_coordinates_recoverable": _boolean(bool(
            coordinate and coordinate["full_ligand_coordinates_recoverable"]
        )),
        "exact_ccd_observed_heavy_atom_identity_coverage": _boolean(bool(
            coordinate
            and coordinate["exact_ccd_observed_heavy_atom_identity_coverage"]
        )),
        "exact_ccd_observed_heavy_atom_element_agreement": _boolean(bool(
            coordinate
            and coordinate["exact_ccd_observed_heavy_atom_element_agreement"]
        )),
        "reactive_ligand_atom_exact_coverage": _boolean(bool(
            coordinate and coordinate["reactive_ligand_atom_exact_coverage"]
        )),
        "canonical_pocket_coordinates_recoverable": _boolean(bool(
            coordinate and coordinate["canonical_pocket_coordinates_recoverable"]
        )),
        "ligand_atom_inventory_sha256": structural.get("ligand_atom_inventory_sha256", "") if is_candidate else "",
        "pocket_atom_inventory_sha256": structural.get("pocket_atom_inventory_sha256", "") if is_candidate else "",
        "observed_heavy_atom_map_sha256": (
            coordinate["observed_heavy_atom_map_sha256"] if coordinate else ""
        ),
        "ccd_heavy_atom_map_sha256": (
            coordinate["ccd_heavy_atom_map_sha256"] if coordinate else ""
        ),
        "ccd_component_graph_sha256": ccd.get("ccd_component_graph_sha256", "") if is_candidate else "",
        "reactive_center_radius1_fingerprint": structural.get("reactive_center_radius1_sha256", "") if is_candidate else "",
        "reactive_center_radius2_fingerprint": structural.get("reactive_center_radius2_sha256", "") if is_candidate else "",
        "reactive_center_local_topology": structural.get("reactive_center_local_topology", "") if is_candidate else "",
        "source_annotations_json": _json_cell(event["source_annotations"] if is_candidate else []),
        "annotation_conflicts_json": _json_cell(event["annotation_conflict_fields"] if is_candidate else []),
        "leakage_classification": outcome.get("leakage_classification", ""),
        "predicted_group_id": outcome.get("predicted_group_id") or "",
        "predicted_split": outcome.get("predicted_split", ""),
        "leakage_linking_axes_json": _json_cell(outcome.get("leakage_linking_axes", [])),
        "pre_status": outcome.get("pre_representability", {}).get("status", ""),
        "pre_status_diagnostic_only_for_post_only_triage": _boolean(is_candidate),
        "training_domain_relevance_status": relevance_status,
        "training_domain_relevance_human_review_required": _boolean(is_candidate),
        "post_geometry_auxiliary_labels_status": auxiliary,
        "production_chemistry_authority_status": "NOT_EVALUATED_OR_CREATED_BY_POST_ONLY_LANE",
        "production_approval_created": "false",
        "terminal_outcome": outcome["terminal_outcome"],
        "terminal_reasons_json": _json_cell(outcome["terminal_reasons"]),
    }
    return {field: row[field] for field in EVENT_HEADER}


def _normalized_ccd_atom_inventory_v1(ccd: Mapping[str, Any]) -> list[dict[str, Any]]:
    atoms: list[dict[str, Any]] = []
    seen: set[str] = set()
    for atom in ccd.get("ccd_atom_inventory", []):
        atom_id = str(atom.get("atom_id") or "").strip()
        if not atom_id:
            raise ValueError("CCD_ATOM_INVENTORY_ID_EMPTY")
        if atom_id in seen:
            raise ValueError("CCD_ATOM_INVENTORY_ID_DUPLICATE:" + atom_id)
        seen.add(atom_id)
        atoms.append({
            "atom_id": atom_id,
            "element": _normalized_element(
                atom.get("type_symbol"), owner="CCD_ATOM"
            ),
            "formal_charge": atom.get("charge"),
            "aromatic_flag": atom.get("aromatic_flag"),
        })
    return sorted(atoms, key=lambda atom: str(atom["atom_id"]))


def _normalized_ccd_bond_inventory_v1(ccd: Mapping[str, Any]) -> list[dict[str, Any]]:
    bonds: list[dict[str, Any]] = []
    for bond in ccd.get("ccd_bond_inventory", []):
        first = str(bond.get("atom_id_1") or "").strip()
        second = str(bond.get("atom_id_2") or "").strip()
        order = str(bond.get("value_order") or "").strip()
        if not first or not second or not order:
            raise ValueError("CCD_BOND_INVENTORY_RECORD_INCOMPLETE")
        bonds.append({
            "atom_id_1": first,
            "atom_id_2": second,
            "bond_order": order,
            "aromatic_flag": bond.get("pdbx_aromatic_flag"),
        })
    return sorted(
        bonds,
        key=lambda bond: (
            str(bond["atom_id_1"]), str(bond["atom_id_2"]),
            str(bond["bond_order"]), str(bond["aromatic_flag"]),
        ),
    )


def _reactive_atom_evidence_v1(
    *, ccd: Mapping[str, Any], ccd_heavy_atom_map: Sequence[Mapping[str, Any]],
    reactive_atom_id: str,
) -> dict[str, Any]:
    matches = [
        dict(atom) for atom in ccd_heavy_atom_map
        if atom["atom_id"] == reactive_atom_id
    ]
    if len(matches) != 1:
        raise ValueError("UNIT_REACTIVE_ATOM_CCD_RECORD_NOT_EXACTLY_ONE")
    all_ccd_atoms = {
        str(atom["atom_id"]): atom
        for atom in _normalized_ccd_atom_inventory_v1(ccd)
    }
    neighbors: list[dict[str, Any]] = []
    for bond in _normalized_ccd_bond_inventory_v1(ccd):
        if bond["atom_id_1"] == reactive_atom_id:
            neighbor_id = str(bond["atom_id_2"])
        elif bond["atom_id_2"] == reactive_atom_id:
            neighbor_id = str(bond["atom_id_1"])
        else:
            continue
        if neighbor_id not in all_ccd_atoms:
            raise ValueError("UNIT_REACTIVE_NEIGHBOR_CCD_ATOM_MISSING:" + neighbor_id)
        neighbors.append({
            "neighbor_atom": all_ccd_atoms[neighbor_id],
            "bond_order": bond["bond_order"],
            "aromatic_flag": bond["aromatic_flag"],
        })
    return {
        "ligand_reactive_atom": reactive_atom_id,
        "reactive_atom_element": matches[0]["element"],
        "reactive_atom_ccd_record": matches[0],
        "reactive_atom_immediate_neighbors": sorted(
            neighbors, key=lambda value: str(value["neighbor_atom"]["atom_id"])
        ),
        "radius1_adjacency_source": "SHA_BOUND_PUBLISHED_CCD_BOND_INVENTORY",
    }


def _event_for_review_v1(
    *, event: Mapping[str, Any], outcome: Mapping[str, Any],
    coordinate: Mapping[str, object], relevance_status: str,
) -> dict[str, Any]:
    structural = outcome["structural_processing"]
    ccd = structural["ccd_component_graph"]
    value: dict[str, Any] = {
        "canonical_event_id": event["canonical_event_id"],
        "pdb_id": event["pdb_id"],
        "ligand_component_id": event["ligand_component_id"],
        "target_cys_identity": (
            f"{event['pdb_id']}:{event['protein_instance']}:CYS:"
            f"{event['protein_residue_number']}:SG"
        ),
        "protein_reactive_atom": event["protein_reactive_atom"],
        "ligand_reactive_atom": event["ligand_reactive_atom"],
        "selected_connection_id": structural["selected_connection_id"],
        "protein_endpoint_coordinates": structural["protein_endpoint_coordinates"],
        "ligand_endpoint_coordinates": structural["ligand_endpoint_coordinates"],
        "post_distance_angstrom": structural["post_distance_angstrom"],
        "reported_distance_angstrom": structural["reported_distance_angstrom"],
        "protein_altloc": structural.get("selected_protein_altloc"),
        "ligand_altloc": structural.get("selected_ligand_altloc"),
        "full_ligand_coordinate_exact_coverage_status": coordinate[
            "exact_ccd_observed_coverage_status"
        ],
        "exact_ccd_observed_heavy_atom_identity_coverage": coordinate[
            "exact_ccd_observed_heavy_atom_identity_coverage"
        ],
        "exact_ccd_observed_heavy_atom_element_agreement": coordinate[
            "exact_ccd_observed_heavy_atom_element_agreement"
        ],
        "reactive_ligand_atom_exact_coverage": coordinate[
            "reactive_ligand_atom_exact_coverage"
        ],
        "observed_heavy_atom_map_sha256": coordinate[
            "observed_heavy_atom_map_sha256"
        ],
        "pocket_coordinate_availability": coordinate[
            "canonical_pocket_coordinates_recoverable"
        ],
        "ccd_component_graph_sha256": ccd["ccd_component_graph_sha256"],
        "reactive_center_radius1_fingerprint": structural.get(
            "reactive_center_radius1_sha256"
        ),
        "reactive_center_radius1_status": (
            "PUBLISHED_EVIDENCE_AVAILABLE"
            if structural.get("reactive_center_radius1_sha256")
            else "REACTIVE_CENTER_TOPOLOGY_UNAVAILABLE"
        ),
        "reactive_center_radius2_fingerprint": structural.get(
            "reactive_center_radius2_sha256"
        ),
        "reactive_center_radius2_status": (
            "PUBLISHED_EVIDENCE_AVAILABLE"
            if structural.get("reactive_center_radius2_sha256")
            else "REACTIVE_CENTER_TOPOLOGY_UNAVAILABLE"
        ),
        "reactive_center_local_topology": structural.get(
            "reactive_center_local_topology"
        ),
        "reactive_center_local_topology_status": (
            "PUBLISHED_EVIDENCE_AVAILABLE"
            if structural.get("reactive_center_local_topology")
            else "REACTIVE_CENTER_TOPOLOGY_UNAVAILABLE"
        ),
        "required_radius2_heavy_atom_ids": coordinate[
            "required_radius2_heavy_atom_ids"
        ],
        "required_local_heavy_atoms_observed": coordinate[
            "required_local_heavy_atoms_observed"
        ],
        "training_domain_machine_triage_status": relevance_status,
        "source_annotation_summary": event["source_annotations"],
        "source_annotation_role": "SUPPORTING_TRIAGE_EVIDENCE_ONLY",
        "predicted_leakage_group": outcome.get("predicted_group_id"),
        "predicted_split": outcome["predicted_split"],
        "pre_status": outcome["pre_representability"]["status"],
        "pre_status_role": (
            "DIAGNOSTIC_NOT_A_POST_ONLY_ELIGIBILITY_HARD_BLOCKER"
        ),
    }
    return {
        **value,
        **{field: "" for field in EVENT_HUMAN_DECISION_FIELDS},
    }


def _build_review_units_v1(
    *, units: Sequence[Mapping[str, Any]], cluster_by_unit: Mapping[str, str],
    event_by_id: Mapping[str, Mapping[str, Any]],
    outcome_by_id: Mapping[str, Mapping[str, Any]],
    coordinate_audit: Mapping[str, Mapping[str, object]],
    relevance_by_id: Mapping[str, str],
) -> tuple[list[dict[str, object]], list[dict[str, Any]]]:
    csv_rows: list[dict[str, object]] = []
    packet_units: list[dict[str, Any]] = []
    for unit in sorted(units, key=lambda item: str(item["review_unit_id"])):
        event_ids = [str(value) for value in unit["canonical_event_ids"]]
        events = [event_by_id[event_id] for event_id in event_ids]
        outcomes = [outcome_by_id[event_id] for event_id in event_ids]
        structural = [outcome["structural_processing"] for outcome in outcomes]
        distances = sorted(float(item["post_distance_angstrom"]) for item in structural)
        altlocs = sorted({
            _json_cell({
                "protein": item.get("selected_protein_altloc"),
                "ligand": item.get("selected_ligand_altloc"),
            })
            for item in structural
        })
        annotations = sorted(
            {
                _json_cell(annotation)
                for event in events for annotation in event["source_annotations"]
            }
        )
        status_counts = dict(sorted(Counter(
            relevance_by_id[event_id] for event_id in event_ids
        ).items()))
        reasons = [
            "TRAINING_DOMAIN_RELEVANCE_HUMAN_DECISION_REQUIRED",
            "WARHEAD_FAMILY_AND_ATOM_SET_HUMAN_DECISION_REQUIRED",
            "SCAFFOLD_LINKER_WARHEAD_ROLE_HUMAN_DECISION_REQUIRED",
            "EVENT_LEVEL_POST_GEOMETRY_TRAINING_USABILITY_HUMAN_CONFIRMATION_REQUIRED",
        ]
        local_topologies = sorted({
            str(item.get("reactive_center_local_topology") or "UNAVAILABLE")
            for item in structural
        })
        if local_topologies == ["UNAVAILABLE"]:
            reasons.append(
                "REACTIVE_CENTER_TOPOLOGY_UNAVAILABLE; UNIT RETAINED ONLY WITH "
                "EXACT COMPONENT_REACTIVE_ATOM_CCD_GRAPH BOUNDARY"
            )
        representative_event_id = event_ids[0]
        representative_coordinate = coordinate_audit[representative_event_id]
        representative_outcome = outcome_by_id[representative_event_id]
        ccd = representative_outcome["structural_processing"]["ccd_component_graph"]
        ccd_map_hashes = {
            str(coordinate_audit[event_id]["ccd_heavy_atom_map_sha256"])
            for event_id in event_ids
        }
        if ccd_map_hashes != {
            str(representative_coordinate["ccd_heavy_atom_map_sha256"])
        }:
            raise ValueError("REVIEW_UNIT_CCD_HEAVY_ATOM_MAP_IDENTITY_MISMATCH")
        ccd_bonds = _normalized_ccd_bond_inventory_v1(ccd)
        machine_evidence = {
            "evidence_role": "HUMAN_REVIEW_EVIDENCE_NOT_CHEMISTRY_AUTHORITY",
            "ccd_component_graph_sha256": ccd["ccd_component_graph_sha256"],
            "ccd_heavy_atom_map_sha256": representative_coordinate[
                "ccd_heavy_atom_map_sha256"
            ],
            "ccd_atom_inventory": _normalized_ccd_atom_inventory_v1(ccd),
            "ccd_heavy_atom_inventory": representative_coordinate[
                "ccd_heavy_atom_map"
            ],
            "ccd_bond_inventory": ccd_bonds,
            "reactive_atom_evidence": _reactive_atom_evidence_v1(
                ccd=ccd,
                ccd_heavy_atom_map=representative_coordinate["ccd_heavy_atom_map"],
                reactive_atom_id=str(unit["reactive_atom"]),
            ),
            "representative_canonical_event_id": representative_event_id,
            "representative_observed_heavy_atom_map_sha256": (
                representative_coordinate["observed_heavy_atom_map_sha256"]
            ),
            "representative_observed_ligand_atom_coordinates": (
                representative_coordinate["observed_heavy_atom_map"]
            ),
            "exact_coverage_status": representative_coordinate[
                "exact_ccd_observed_coverage_status"
            ],
            "source_annotation_role": "SUPPORTING_TRIAGE_EVIDENCE_ONLY",
        }
        events_for_review = [
            _event_for_review_v1(
                event=event_by_id[event_id], outcome=outcome_by_id[event_id],
                coordinate=coordinate_audit[event_id],
                relevance_status=relevance_by_id[event_id],
            )
            for event_id in event_ids
        ]
        common: dict[str, Any] = {
            "review_unit_id": unit["review_unit_id"],
            "cluster_id": cluster_by_unit[str(unit["review_unit_id"])],
            "event_count": len(event_ids),
            "canonical_event_ids": event_ids,
            "pdb_ids": sorted({str(event["pdb_id"]) for event in events}),
            "ligand_component_ids": sorted({str(event["ligand_component_id"]) for event in events}),
            "representative_canonical_event_id": representative_event_id,
            "source_datasets": sorted({
                str(source) for event in events for source in event["source_datasets"]
            }),
            "source_annotations": [json.loads(value) for value in annotations],
            "source_annotation_role": "SUPPORTING_TRIAGE_EVIDENCE_ONLY",
            "target_cys_identities": sorted({
                f"{event['pdb_id']}:{event['protein_instance']}:CYS:{event['protein_residue_number']}:SG"
                for event in events
            }),
            "ligand_reactive_atom": unit["reactive_atom"],
            "ligand_reactive_elements": sorted({
                str(item["ligand_reactive_element"]) for item in structural
            }),
            "reactive_center_local_topologies": local_topologies,
            "ccd_component_graph_sha256": unit["ccd_component_graph_sha256"],
            "reactive_center_radius1_fingerprints": sorted({
                str(item.get("reactive_center_radius1_sha256") or "UNAVAILABLE")
                for item in structural
            }),
            "reactive_center_radius2_fingerprint": (
                unit["reactive_center_radius2_fingerprint"] or "UNAVAILABLE"
            ),
            "post_distance_min_angstrom": min(distances),
            "post_distance_max_angstrom": max(distances),
            "post_distance_mean_angstrom": round(sum(distances) / len(distances), 6),
            "post_distance_distribution_angstrom": distances,
            "altloc_status": "NO_ALTLOC" if altlocs == [_json_cell({"ligand": None, "protein": None})] else "ALTLOC_PRESENT:" + _json_cell([json.loads(value) for value in altlocs]),
            "ligand_heavy_atom_count_min": min(int(item["ligand_heavy_atom_count"]) for item in structural),
            "ligand_heavy_atom_count_max": max(int(item["ligand_heavy_atom_count"]) for item in structural),
            "pocket_coordinate_availability": (
                "ALL_EVENTS_RECOVERABLE" if all(
                    coordinate_audit[event_id]["canonical_pocket_coordinates_recoverable"]
                    for event_id in event_ids
                ) else "INCOMPLETE"
            ),
            "leakage_groups": sorted({
                str(outcome["predicted_group_id"])
                for outcome in outcomes if outcome.get("predicted_group_id")
            }),
            "predicted_splits": sorted({str(outcome["predicted_split"]) for outcome in outcomes}),
            "leakage_linking_axes": sorted({
                str(axis) for outcome in outcomes for axis in outcome["leakage_linking_axes"]
            }),
            "pre_statuses": sorted({
                str(outcome["pre_representability"]["status"]) for outcome in outcomes
            }),
            "pre_status_non_blocking_for_post_only_eligibility": True,
            "training_domain_relevance_status_distribution": status_counts,
            "reasons_needing_human_review": reasons,
            "predecessor_review_unit_reused": True,
            "chemistry_identity_boundary_validated": True,
            "production_approval_created": False,
            "machine_chemistry_evidence": machine_evidence,
            "events_for_review": events_for_review,
        }
        decisions = {field: "" for field in UNIT_HUMAN_DECISION_FIELDS}
        packet_units.append({**common, **decisions})
        csv_value = {
            "review_unit_id": common["review_unit_id"],
            "cluster_id": common["cluster_id"],
            "event_count": common["event_count"],
            "canonical_event_ids_json": _json_cell(common["canonical_event_ids"]),
            "pdb_ids_json": _json_cell(common["pdb_ids"]),
            "ligand_component_ids_json": _json_cell(common["ligand_component_ids"]),
            "representative_canonical_event_id": common["representative_canonical_event_id"],
            "source_datasets_json": _json_cell(common["source_datasets"]),
            "source_annotations_json": _json_cell(common["source_annotations"]),
            "target_cys_identities_json": _json_cell(common["target_cys_identities"]),
            "ligand_reactive_atom": common["ligand_reactive_atom"],
            "ligand_reactive_elements_json": _json_cell(common["ligand_reactive_elements"]),
            "reactive_center_local_topologies_json": _json_cell(common["reactive_center_local_topologies"]),
            "ccd_component_graph_sha256": common["ccd_component_graph_sha256"],
            "reactive_center_radius1_fingerprints_json": _json_cell(common["reactive_center_radius1_fingerprints"]),
            "reactive_center_radius2_fingerprint": common["reactive_center_radius2_fingerprint"],
            "post_distance_min_angstrom": common["post_distance_min_angstrom"],
            "post_distance_max_angstrom": common["post_distance_max_angstrom"],
            "post_distance_mean_angstrom": common["post_distance_mean_angstrom"],
            "post_distance_distribution_json": _json_cell(common["post_distance_distribution_angstrom"]),
            "altloc_status": common["altloc_status"],
            "ligand_heavy_atom_count_min": common["ligand_heavy_atom_count_min"],
            "ligand_heavy_atom_count_max": common["ligand_heavy_atom_count_max"],
            "pocket_coordinate_availability": common["pocket_coordinate_availability"],
            "leakage_groups_json": _json_cell(common["leakage_groups"]),
            "predicted_splits_json": _json_cell(common["predicted_splits"]),
            "leakage_linking_axes_json": _json_cell(common["leakage_linking_axes"]),
            "pre_statuses_json": _json_cell(common["pre_statuses"]),
            "pre_status_non_blocking_for_post_only_eligibility": "true",
            "training_domain_relevance_status_distribution_json": _json_cell(status_counts),
            "reasons_needing_human_review_json": _json_cell(reasons),
            "predecessor_review_unit_reused": "true",
            "chemistry_identity_boundary_validated": "true",
            "production_approval_created": "false",
            "ccd_heavy_atom_inventory_count": len(
                machine_evidence["ccd_heavy_atom_inventory"]
            ),
            "ccd_bond_inventory_count": len(
                machine_evidence["ccd_bond_inventory"]
            ),
            "representative_observed_heavy_atom_coordinate_count": len(
                machine_evidence[
                    "representative_observed_ligand_atom_coordinates"
                ]
            ),
            "exact_ccd_observed_coverage_status": machine_evidence[
                "exact_coverage_status"
            ],
            "events_for_review_count": len(events_for_review),
            "event_level_human_decision_fields_json": _json_cell(
                list(EVENT_HUMAN_DECISION_FIELDS)
            ),
            **decisions,
        }
        csv_rows.append({field: csv_value[field] for field in REVIEW_UNIT_HEADER})
    return csv_rows, packet_units


def _guide_bytes(counts: Mapping[str, int]) -> bytes:
    text = f"""# CovaPIE post-only CYS-SG training-candidate triage V1

This additive lane contains {counts['candidate']} review candidates in
{counts['review_units']} chemistry-bounded review units. It does not grant
production chemistry authority and it does not materialize training samples.

## Boundary

A post-only V1 training candidate is an explicit, feature-compatible Cys-SG
event with recoverable observed post-complex ligand and pocket coordinates and
without a terminal leakage conflict or representation gap. Accurate
experimental pre-covalent geometry is not required for candidate review. PRE
status remains diagnostic and may support chemistry interpretation.

Existing production chemistry authority rules are unchanged. Source labels are
supporting triage evidence only; they are not exact chemistry signatures,
human approvals, warhead truth, or production admission. Review decisions must
be supplied by a human in the blank fields of `{REVIEW_PACKET}`.

## Two-level human-review workflow

First, review `training_domain_relevance_decision` at unit level. If the human
decision is `NOT_RELEVANT_TO_COVAPIE_SMALL_MOLECULE_TASK`, exclude the unit and
do not spend time assigning warhead or role labels. Only a human decision of
`RELEVANT_FOR_COVAPIE_POST_ONLY_V1` proceeds to unit-level warhead family,
warhead atom set, reactive-atom confirmation, and scaffold/linker/warhead role
decisions.

Second, review every `events_for_review` record independently. The blank
`post_geometry_training_usable`, `event_training_use_decision`, and
`event_exclusion_reason` fields are event/pose-level decisions; they must not be
propagated from another event in the same chemistry unit. The packet provides
the complete SHA-bound CCD atom/bond evidence and representative observed
heavy-atom coordinates needed for chemistry review. These are evidence, not
new authority.

## Population

- Canonical events: {counts['canonical']}
- Known existing events excluded from the new lane: {counts['known']}
- New events: {counts['new']}
- Structurally eligible new events: {counts['structural']}
- Post-only review candidates: {counts['candidate']}
- Existing-group leakage conflicts blocked: {counts['leakage']}
- Representation gaps blocked: {counts['representation']}
- Outside structural eligibility: {counts['outside']}

The 23 predecessor clusters are retained only for review ordering and batching.
The {counts['review_units']} review units retain component identity, reactive
atom, and CCD graph identity. Reactive-center topology is also uniform within
each unit when available; {counts['topology_unavailable_units']} units expose a
uniformly unavailable topology state and are retained only inside the stricter
exact component/reactive-atom/CCD-graph boundary. Clusters must never be used
as chemistry authority, decision-propagation, or training-label authority
units. There are {counts['multi_event_units']} multi-event units containing
{counts['events_in_multi_event_units']} events; their geometry decisions remain
independent.
"""
    return text.encode("utf-8")


def build_artifacts_v1(
    *, repo_root: Path, cache_root: Path, verify_git_binding: bool = True,
) -> dict[str, bytes]:
    repo_root = repo_root.resolve()
    cache_root = cache_root.resolve()
    git_state = (
        verify_base_git_binding_v1(repo_root) if verify_git_binding
        else {
            "head": BASE_HEAD, "origin_main": BASE_HEAD, "ahead": 0,
            "behind": 0, "head_subject": BASE_SUBJECT,
        }
    )
    input_hashes_before = verify_bound_inputs_v1(repo_root)
    cache_before = task_cache_content_digest_v1(cache_root)
    source_root = repo_root / INPUT_ROOT_RELATIVE
    predecessor_summary = _read_json(source_root / "bulk_summary_v1.json")
    outcome_artifact = _read_json(source_root / "bulk_processing_outcomes_v1.json")
    canonical_artifact = _read_json(
        source_root / "cross_source_canonical_event_manifest_v1.json"
    )
    review_artifact = _read_json(source_root / "bulk_human_review_clusters_v1.json")
    acquisition_artifact = _read_json(source_root / "bulk_acquisition_manifest_v1.json")
    snapshots = {
        "covbinder": _read_json(source_root / "covbinderinpdb_discovery_snapshot_v1.json"),
        "covpdb": _read_json(source_root / "covpdb_discovery_snapshot_v1.json"),
        "rcsb": _read_json(source_root / "rcsb_pdb_direct_discovery_snapshot_v1.json"),
    }
    # Explicit reads keep every declared published input inside the SHA-bound source set.
    _read_json(source_root / "bulk_source_access_resolution_v1.json")
    _read_json(source_root / "covalentindb_discovery_snapshot_v1.json")

    events = canonical_artifact.get("canonical_events")
    outcomes = outcome_artifact.get("events")
    if not isinstance(events, list) or not isinstance(outcomes, list):
        raise ValueError("PREDECESSOR_EVENT_ARTIFACT_SCHEMA_INVALID")
    event_by_id = {str(item["canonical_event_id"]): item for item in events}
    outcome_by_id = {str(item["canonical_event_id"]): item for item in outcomes}
    if len(event_by_id) != len(events) or set(event_by_id) != set(outcome_by_id):
        raise ValueError("CANONICAL_EVENT_OUTCOME_IDENTITY_MISMATCH")
    known_ids = {
        event_id for event_id, outcome in outcome_by_id.items()
        if str(outcome["terminal_outcome"]).startswith("KNOWN_")
    }
    partitions = {
        event_id: post_only_partition_v1(
            outcome_by_id[event_id], known_event=event_id in known_ids
        )
        for event_id in sorted(event_by_id)
    }
    counts = Counter(partitions.values())
    canonical_count = len(event_by_id)
    known_count = len(known_ids)
    new_count = canonical_count - known_count
    structural_count = (
        counts[POST_ONLY_CANDIDATE]
        + counts[BLOCKED_LEAKAGE]
        + counts[BLOCKED_REPRESENTATION]
    )
    expected = {
        "canonical_unique_event_count": canonical_count,
        "known_existing_event_count": known_count,
        "new_unique_candidate_event_count": new_count,
        "structurally_model_eligible_new_event_count": structural_count,
    }
    for key, value in expected.items():
        if predecessor_summary.get(key) != value:
            raise ValueError("PREDECESSOR_SUMMARY_RECONCILIATION_MISMATCH:" + key)
    if counts[OUTSIDE_STRUCTURAL] + structural_count != new_count:
        raise ValueError("NEW_POPULATION_PARTITION_RECONCILIATION_FAILED")
    route_counts = predecessor_summary.get("terminal_route_counts", {})
    if not (
        counts[POST_ONLY_CANDIDATE]
        == route_counts.get("HUMAN_REVIEW_REQUIRED_PRE_CHEMISTRY")
        and counts[BLOCKED_LEAKAGE]
        == route_counts.get("LEAKAGE_EXISTING_GROUP_CONFLICT")
        and counts[BLOCKED_REPRESENTATION]
        == route_counts.get("QUARANTINE_REPRESENTATION_GAP")
    ):
        raise ValueError("STRUCTURAL_ELIGIBILITY_TERMINAL_RECONCILIATION_FAILED")
    if predecessor_summary.get("production_trainable_new_sample_count") != 0:
        raise ValueError("PREDECESSOR_PRODUCTION_NEW_SAMPLE_COUNT_CHANGED")
    if predecessor_summary.get("authorized_data_population_after") != 19:
        raise ValueError("PREDECESSOR_AUTHORIZED_POPULATION_CHANGED")

    candidate_ids = {
        event_id for event_id, partition in partitions.items()
        if partition == POST_ONLY_CANDIDATE
    }
    candidate_events = [event_by_id[event_id] for event_id in sorted(candidate_ids)]
    acquisition = {
        str(item["pdb_id"]): item for item in acquisition_artifact.get("structures", [])
    }
    coordinate_audit = _coordinate_audit_v1(
        candidate_events=candidate_events, outcome_by_id=outcome_by_id,
        acquisition=acquisition, cache_root=cache_root,
    )
    if not all(
        outcome_by_id[event_id]["structural_processing"].get("explicit_covalent_evidence")
        and outcome_by_id[event_id]["structural_processing"].get("feature_projection_status") == "passed"
        and coordinate_audit[event_id]["full_ligand_coordinates_recoverable"]
        and coordinate_audit[event_id][
            "exact_ccd_observed_heavy_atom_identity_coverage"
        ]
        and coordinate_audit[event_id][
            "exact_ccd_observed_heavy_atom_element_agreement"
        ]
        and coordinate_audit[event_id]["reactive_ligand_atom_exact_coverage"]
        and coordinate_audit[event_id]["canonical_pocket_coordinates_recoverable"]
        for event_id in candidate_ids
    ):
        raise ValueError("POST_ONLY_CANDIDATE_STRUCTURAL_CONTRACT_FAILED")

    units, cluster_by_unit, cluster_integrity = _validate_and_index_review_units_v1(
        artifact=review_artifact, candidate_ids=candidate_ids,
        event_by_id=event_by_id, outcome_by_id=outcome_by_id,
    )
    relevance: dict[str, str] = {}
    classification_rules: dict[str, str] = {}
    for event_id in sorted(candidate_ids):
        relevance[event_id], classification_rules[event_id] = (
            classify_training_domain_relevance_v1(event_by_id[event_id])
        )

    event_rows = []
    for event_id in sorted(event_by_id):
        partition = partitions[event_id]
        event_rows.append(_event_inventory_row(
            event=event_by_id[event_id], outcome=outcome_by_id[event_id],
            partition=partition, coordinate=coordinate_audit.get(event_id),
            relevance_status=(
                relevance[event_id] if event_id in relevance else RELEVANCE_NOT_EVALUATED
            ),
        ))

    evidence_rows: list[dict[str, object]] = []
    binding_path = (
        INPUT_ROOT_RELATIVE / "cross_source_canonical_event_manifest_v1.json"
    ).as_posix()
    binding_sha = INPUT_SHA256["cross_source_canonical_event_manifest_v1.json"]
    for event_id in sorted(candidate_ids):
        event = event_by_id[event_id]
        used_reactions = {
            str(annotation["reaction"]).strip().lower()
            for annotation in event["source_annotations"]
            if annotation.get("source_dataset") == "SOURCE_COVBINDERINPDB"
            and str(annotation.get("reaction") or "").strip()
        }
        for annotation in sorted(
            event["source_annotations"], key=lambda value: (
                str(value.get("source_dataset")), str(value.get("source_record_id"))
            )
        ):
            for field in ("covalent_event", "reaction", "warhead"):
                value = annotation.get(field)
                if value is None or str(value).strip() == "":
                    continue
                used = bool(
                    field == "reaction"
                    and annotation.get("source_dataset") == "SOURCE_COVBINDERINPDB"
                    and len(used_reactions) == 1
                )
                raw = {
                    "canonical_event_id": event_id,
                    "training_domain_relevance_status": relevance[event_id],
                    "human_review_required": "true",
                    "source_dataset": annotation["source_dataset"],
                    "source_record_id": annotation["source_record_id"],
                    "evidence_field": "source_annotations." + field,
                    "evidence_value": value,
                    "evidence_used_for_machine_status": _boolean(used),
                    "evidence_role": "SUPPORTING_TRIAGE_EVIDENCE_ONLY",
                    "source_payload_sha256": _source_payload_sha(annotation, snapshots),
                    "event_source_payload_sha256s_json": _json_cell(event["source_payload_sha256s"]),
                    "binding_artifact_path": binding_path,
                    "binding_artifact_sha256": binding_sha,
                    "source_annotation_is_production_authority": "false",
                    "classification_rule": classification_rules[event_id],
                }
                evidence_rows.append({field_name: raw[field_name] for field_name in DOMAIN_EVIDENCE_HEADER})

    unit_rows, packet_units = _build_review_units_v1(
        units=units, cluster_by_unit=cluster_by_unit, event_by_id=event_by_id,
        outcome_by_id=outcome_by_id, coordinate_audit=coordinate_audit,
        relevance_by_id=relevance,
    )
    event_bytes = _csv_bytes(EVENT_HEADER, event_rows)
    unit_bytes = _csv_bytes(REVIEW_UNIT_HEADER, unit_rows)
    evidence_bytes = _csv_bytes(DOMAIN_EVIDENCE_HEADER, evidence_rows)
    cluster_count = len(review_artifact["clusters"])
    topology_unavailable_unit_count = sum(
        unit["reactive_center_local_topologies"] == ["UNAVAILABLE"]
        for unit in packet_units
    )
    multi_event_units = [
        unit for unit in packet_units if int(unit["event_count"]) > 1
    ]
    events_in_multi_event_units = sum(
        int(unit["event_count"]) for unit in multi_event_units
    )
    packet_event_ids = [
        str(event["canonical_event_id"])
        for unit in packet_units for event in unit["events_for_review"]
    ]
    if len(packet_event_ids) != len(set(packet_event_ids)):
        raise ValueError("DUPLICATE_EVENT_ACROSS_PACKET_EVENTS_FOR_REVIEW")
    if set(packet_event_ids) != candidate_ids:
        raise ValueError("PACKET_EVENTS_FOR_REVIEW_COVERAGE_MISMATCH")
    packet_chemistry_evidence_complete = all(
        unit["machine_chemistry_evidence"]["ccd_atom_inventory"]
        and unit["machine_chemistry_evidence"]["ccd_heavy_atom_inventory"]
        and unit["machine_chemistry_evidence"]["ccd_bond_inventory"]
        and unit["machine_chemistry_evidence"]["reactive_atom_evidence"]
        and unit["machine_chemistry_evidence"][
            "representative_observed_ligand_atom_coordinates"
        ]
        for unit in packet_units
    )
    if not packet_chemistry_evidence_complete:
        raise ValueError("PACKET_CHEMISTRY_EVIDENCE_INCOMPLETE")
    compact_counts = {
        "canonical": canonical_count, "known": known_count, "new": new_count,
        "structural": structural_count, "candidate": counts[POST_ONLY_CANDIDATE],
        "leakage": counts[BLOCKED_LEAKAGE],
        "representation": counts[BLOCKED_REPRESENTATION],
        "outside": counts[OUTSIDE_STRUCTURAL], "review_units": len(units),
        "topology_unavailable_units": topology_unavailable_unit_count,
        "multi_event_units": len(multi_event_units),
        "events_in_multi_event_units": events_in_multi_event_units,
    }
    packet = {
        "schema_version": SCHEMA_VERSION,
        "packet_role": "HUMAN_REVIEW_INPUT_NOT_AUTHORITY",
        "post_only_v1_training_candidate_count": counts[POST_ONLY_CANDIDATE],
        "review_unit_count": len(units),
        "review_cluster_count": cluster_count,
        "review_unit_reactive_center_topology_unavailable_count": (
            topology_unavailable_unit_count
        ),
        "recommended_human_click_count": len(units),
        "clusters_are_prioritization_and_batching_only": True,
        "review_units_are_not_chemistry_authority": True,
        "accurate_experimental_pre_covalent_geometry_required": False,
        "pre_status_is_post_only_eligibility_hard_blocker": False,
        "existing_production_chemistry_authority_semantics_changed": False,
        "unit_human_decision_fields_must_remain_blank_until_human_review": list(
            UNIT_HUMAN_DECISION_FIELDS
        ),
        "event_human_decision_fields_must_remain_blank_until_human_review": list(
            EVENT_HUMAN_DECISION_FIELDS
        ),
        "review_workflow": {
            "first": (
                "UNIT_LEVEL_TRAINING_DOMAIN_RELEVANCE; STOP UNIT REVIEW IF "
                "NOT_RELEVANT_TO_COVAPIE_SMALL_MOLECULE_TASK"
            ),
            "second_if_relevant": (
                "UNIT_LEVEL_WARHEAD_REACTIVE_ATOM_AND_ROLE_DECISIONS"
            ),
            "third": (
                "INDEPENDENT_EVENT_LEVEL_POST_GEOMETRY_AND_TRAINING_USE_DECISIONS"
            ),
        },
        "review_instructions": [
            "FIRST decide unit-level task-domain relevance for protein-pocket-conditioned small-molecule Cys-SG generation.",
            "If NOT_RELEVANT_TO_COVAPIE_SMALL_MOLECULE_TASK, stop and exclude the unit without warhead/role work.",
            "Only if RELEVANT_FOR_COVAPIE_POST_ONLY_V1, confirm unit-level reactive atom, warhead family/atom set, and role labels.",
            "Then decide post geometry and training use independently for every events_for_review record.",
            "Do not require an accurate experimental pre-covalent 3D pose for V1 candidate review.",
            "Treat source annotations as supporting evidence, never production chemistry authority.",
        ],
        "review_units": packet_units,
    }
    packet_bytes = _json_bytes(packet)
    guide_bytes = _guide_bytes(compact_counts)
    preliminary = {
        EVENT_INVENTORY: event_bytes,
        REVIEW_UNIT_INVENTORY: unit_bytes,
        DOMAIN_EVIDENCE: evidence_bytes,
        REVIEW_PACKET: packet_bytes,
        GUIDE: guide_bytes,
    }
    relevance_counts = Counter(relevance.values())
    exact_pair_count = sum(
        bool(
            outcome_by_id[event_id]["structural_processing"].get("selected_connection_id")
            and event_by_id[event_id].get("protein_reactive_atom") == "SG"
            and event_by_id[event_id].get("ligand_reactive_atom")
        )
        for event_id in candidate_ids
    )
    exact_identity_count = sum(
        bool(coordinate_audit[event_id][
            "exact_ccd_observed_heavy_atom_identity_coverage"
        ])
        for event_id in candidate_ids
    )
    exact_element_count = sum(
        bool(coordinate_audit[event_id][
            "exact_ccd_observed_heavy_atom_element_agreement"
        ])
        for event_id in candidate_ids
    )
    reactive_atom_exact_count = sum(
        bool(coordinate_audit[event_id]["reactive_ligand_atom_exact_coverage"])
        for event_id in candidate_ids
    )
    summary = {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "base_git_binding": git_state,
        "input_artifact_sha256": input_hashes_before,
        "task_cache": cache_before,
        "population": {
            "canonical_unique_event_count": canonical_count,
            "known_existing_event_count": known_count,
            "new_unique_candidate_event_count": new_count,
            "structurally_model_eligible_new_event_count": structural_count,
            "post_only_v1_review_candidate_count": counts[POST_ONLY_CANDIDATE],
            "blocked_existing_group_conflict_count": counts[BLOCKED_LEAKAGE],
            "blocked_representation_gap_count": counts[BLOCKED_REPRESENTATION],
            "outside_structural_eligibility_count": counts[OUTSIDE_STRUCTURAL],
            "canonical_reconciliation": canonical_count == known_count + new_count,
            "new_population_reconciliation": new_count == structural_count + counts[OUTSIDE_STRUCTURAL],
            "structural_population_reconciliation": structural_count == counts[POST_ONLY_CANDIDATE] + counts[BLOCKED_LEAKAGE] + counts[BLOCKED_REPRESENTATION],
            "production_trainable_new_sample_count": 0,
            "authorized_data_population_after": 19,
        },
        "exact_atom_identity_audit": {
            "candidate_count": len(candidate_ids),
            "exact_ccd_observed_heavy_atom_id_set_coverage_count": (
                exact_identity_count
            ),
            "exact_ccd_observed_heavy_atom_element_consistent_count": (
                exact_element_count
            ),
            "reactive_ligand_atom_exact_coverage_count": (
                reactive_atom_exact_count
            ),
            "failure_count": 0,
            "failure_identities": [],
            "coverage_contract": (
                "EXACT_CCD_OBSERVED_HEAVY_ATOM_IDENTITY_AND_ELEMENT_COVERAGE"
            ),
            "count_equality_alone_accepted": False,
        },
        "post_supervision_readiness": {
            "exact_reactive_pair_count": exact_pair_count,
            "exact_ccd_observed_heavy_atom_identity_coverage_count": (
                exact_identity_count
            ),
            "exact_ccd_observed_heavy_atom_element_agreement_count": (
                exact_element_count
            ),
            "reactive_ligand_atom_exact_coverage_count": reactive_atom_exact_count,
            "source_derived_post_bond_distance_count": sum(
                outcome_by_id[event_id]["structural_processing"].get("post_distance_angstrom") is not None
                for event_id in candidate_ids
            ),
            "full_ligand_coordinate_availability_count": sum(
                bool(coordinate_audit[event_id]["full_ligand_coordinates_recoverable"])
                for event_id in candidate_ids
            ),
            "pocket_coordinate_availability_count": sum(
                bool(coordinate_audit[event_id]["canonical_pocket_coordinates_recoverable"])
                for event_id in candidate_ids
            ),
            "ccd_graph_count": sum(
                bool(outcome_by_id[event_id]["structural_processing"].get("ccd_component_graph", {}).get("ccd_component_graph_sha256"))
                for event_id in candidate_ids
            ),
            "reactive_center_radius2_topology_count": sum(
                bool(outcome_by_id[event_id]["structural_processing"].get("reactive_center_radius2_sha256"))
                for event_id in candidate_ids
            ),
            "post_geometry_auxiliary_labels_derivable_count": sum(
                row["post_geometry_auxiliary_labels_status"] == "DERIVABLE_FROM_OBSERVED_POST_COORDINATES"
                for row in event_rows
            ),
            "derivable_quantities_are_not_new_loss_definitions": True,
        },
        "training_domain_relevance": {
            "machine_supported_relevant_count": relevance_counts[RELEVANCE_SUPPORTED],
            "likely_biochemical_or_non_target_count": relevance_counts[RELEVANCE_NON_TARGET],
            "task_relevance_human_review_required_count": relevance_counts[RELEVANCE_REVIEW],
            "task_relevance_evidence_insufficient_count": relevance_counts[RELEVANCE_INSUFFICIENT],
            "all_candidates_still_require_human_decision": True,
            "molecule_name_or_warhead_label_used_for_machine_classification": False,
            "source_annotations_create_chemistry_authority": False,
        },
        "human_review_workload": {
            "event_count": counts[POST_ONLY_CANDIDATE],
            "review_unit_count": len(units),
            "cluster_count": cluster_count,
            "recommended_human_click_count": len(units),
            "predecessor_review_units_reused_without_merge": True,
            "cross_component_chemistry_merge_performed": False,
            "reactive_center_topology_unavailable_review_unit_count": (
                topology_unavailable_unit_count
            ),
            "multi_event_review_unit_count": len(multi_event_units),
            "event_count_inside_multi_event_units": events_in_multi_event_units,
            "unit_human_decision_fields": list(UNIT_HUMAN_DECISION_FIELDS),
            "event_human_decision_fields": list(EVENT_HUMAN_DECISION_FIELDS),
            "all_human_decision_fields_blank": True,
            "full_ccd_atom_and_bond_evidence_present": True,
            "representative_observed_coordinate_evidence_present": True,
        },
        "cluster_integrity": cluster_integrity,
        "pre_policy": {
            "accurate_pre_geometry_required_for_v1_training": False,
            "pre_status_is_post_only_training_hard_blocker": False,
            "existing_production_chemistry_authority_semantics_changed": False,
            "pre_status_role": "DIAGNOSTIC_SUPPORTING_INFORMATION_FOR_POST_ONLY_TRIAGE",
        },
        "safety": {
            "network_performed": False,
            "cache_modified": False,
            "production_approval_created": False,
            "production_materialization_performed": False,
            "chemistry_registry_modified": False,
            "cumulative_registry_modified": False,
            "model_or_training_path_modified": False,
        },
        "output_sha256_excluding_summary": {
            name: _sha(payload) for name, payload in sorted(preliminary.items())
        },
        "ready_for_gpt_review": True,
        "recommended_next_step_exactly": (
            f"perform_human_review_of_{len(units)}_post_only_v1_review_units"
        ),
    }
    artifacts = {**preliminary, SUMMARY: _json_bytes(summary)}
    artifacts = {name: artifacts[name] for name in OUTPUT_FILENAMES}
    if verify_bound_inputs_v1(repo_root) != input_hashes_before:
        raise ValueError("SOURCE_INPUTS_MODIFIED_DURING_BUILD")
    if task_cache_content_digest_v1(cache_root) != cache_before:
        raise ValueError("TASK_CACHE_MODIFIED_DURING_BUILD")
    return artifacts


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def materialize_v1(
    *, repo_root: Path, cache_root: Path, output_root: Path | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    target = (
        output_root.resolve() if output_root is not None
        else repo_root / OUTPUT_ROOT_RELATIVE
    )
    if target != repo_root / OUTPUT_ROOT_RELATIVE:
        try:
            target.relative_to(Path(tempfile.gettempdir()).resolve())
        except ValueError as error:
            raise ValueError("OUTPUT_ROOT_OUTSIDE_AUTHORIZED_PATH") from error
    artifacts = build_artifacts_v1(repo_root=repo_root, cache_root=cache_root)
    for name in OUTPUT_FILENAMES:
        _atomic_write(target / name, artifacts[name])
    return json.loads(artifacts[SUMMARY])


def verify_deterministic_replay_v1(
    *, repo_root: Path, cache_root: Path,
) -> dict[str, str]:
    target = repo_root.resolve() / OUTPUT_ROOT_RELATIVE
    observed = {name: (target / name).read_bytes() for name in OUTPUT_FILENAMES}
    replay = build_artifacts_v1(repo_root=repo_root, cache_root=cache_root)
    result: dict[str, str] = {}
    for name in OUTPUT_FILENAMES:
        if observed[name] != replay[name]:
            raise ValueError("OUTPUT_NOT_BYTE_IDENTICAL_ON_REPLAY:" + name)
        result[name] = _sha(observed[name])
    return result
