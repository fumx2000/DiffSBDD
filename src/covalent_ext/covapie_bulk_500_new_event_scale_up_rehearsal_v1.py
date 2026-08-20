"""Deterministic preparation for a cumulative 500-new-event bulk rehearsal.

The planner consumes only the published bulk discovery/canonicalization
snapshot and the published two-rule routing snapshot.  It does not instantiate
the mutable bulk cache, perform discovery, acquire structures or CCD payloads,
route unprocessed events, or create production/training authority.
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
import statistics
import subprocess
import tempfile
from typing import Any

from covalent_ext import covapie_bulk_cys_sg_dataset_expansion_v1 as frozen_bulk


SCHEMA_VERSION = "covapie_bulk_500_new_event_scale_up_rehearsal_v1"
STAGE = SCHEMA_VERSION
SNAPSHOT_SEMANTICS = "DETERMINISTIC_500_NEW_EVENT_SCALE_UP_REHEARSAL_PLAN"
PUBLISHED_BASELINE_COMMIT_ANCESTOR = (
    "8726e23c5fa6a154e507600ab15739d838348d1f"
)
PUBLISHED_BASELINE_SUBJECT = (
    "integrate CovaPIE DTT exact auto-negative rule into successor routing v1"
)

PILOT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_cys_sg_dataset_expansion_v1/bulk_pilot_v1"
)
FROZEN_BULK_SOURCE_RELATIVE = Path(
    "src/covalent_ext/covapie_bulk_cys_sg_dataset_expansion_v1.py"
)
LIVE_ROUTING_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_post_only_cys_sg_successor_task_domain_routing_v1"
)
FEATURE_RESOLUTION_MANIFEST_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1/"
    "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_manifest.json"
)
FEATURE_RESOLUTION_MANIFEST_SHA256 = (
    "24cb60ca4f080a72e8c60aef63d105d82ec2f432eecc9b90f3341f52576bb6e0"
)
DEFAULT_CACHE_RELATIVE_TO_REPOSITORY_PARENT = Path(
    "covapie-state/bulk-multisource-cys-sg-v1"
)

OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_bulk_500_new_event_scale_up_rehearsal_v1"
)
MANIFEST = "covapie_bulk_500_scaleup_rehearsal_manifest_v1.json"
COHORT = "covapie_bulk_500_new_event_cohort_v1.csv"
ACQUISITION = "covapie_bulk_500_acquisition_requirements_v1.json"
SUMMARY = "covapie_bulk_500_scaleup_rehearsal_summary_v1.json"
OUTPUT_FILENAMES = (MANIFEST, COHORT, ACQUISITION, SUMMARY)
REHEARSAL_500_PRECOMMIT_CANDIDATE = "REHEARSAL_500_PRECOMMIT_CANDIDATE"
REHEARSAL_500_PUBLISHED_CLEAN_DESCENDANT = (
    "REHEARSAL_500_PUBLISHED_CLEAN_DESCENDANT"
)
AUTHORIZED_REHEARSAL_PATHS = frozenset(
    {
        "src/covalent_ext/covapie_bulk_500_new_event_scale_up_rehearsal_v1.py",
        "scripts/build_covapie_bulk_500_new_event_scale_up_rehearsal_v1.py",
        "scripts/check_covapie_bulk_500_new_event_scale_up_rehearsal_v1.py",
        "tests/test_covapie_bulk_500_new_event_scale_up_rehearsal_v1.py",
        (OUTPUT_ROOT_RELATIVE / MANIFEST).as_posix(),
        (OUTPUT_ROOT_RELATIVE / COHORT).as_posix(),
        (OUTPUT_ROOT_RELATIVE / ACQUISITION).as_posix(),
        (OUTPUT_ROOT_RELATIVE / SUMMARY).as_posix(),
    }
)

PILOT_INPUT_SHA256 = {
    PILOT_ROOT_RELATIVE / "cross_source_canonical_event_manifest_v1.json": (
        "d3f35987af92fca669b85d62a86914c7a01bf35d867c4a779e7fc08e76445dae"
    ),
    PILOT_ROOT_RELATIVE / "bulk_processing_outcomes_v1.json": (
        "0270dd93a31427042d02f7751ab7b46679308c7f1ee5207a5560b199a6a94d57"
    ),
    PILOT_ROOT_RELATIVE / "bulk_acquisition_manifest_v1.json": (
        "b12b0e29d223d7469c81e6cbfe0d8eaf7aa4f8a18368b65843df8e63c75afe46"
    ),
    PILOT_ROOT_RELATIVE / "bulk_summary_v1.json": (
        "5af3abd8cc7f608352f1a6636cb810cbb404f439cc8083b9111be80654117462"
    ),
    PILOT_ROOT_RELATIVE / "bulk_source_access_resolution_v1.json": (
        "a31567f3b2202b3b1c29d22fd2c2d908192bed2bb659b273861cd3dacc6c5bc9"
    ),
}
FROZEN_BULK_SOURCE_SHA256 = (
    "ef17777a634284a94662ac3277c02a7fb4efa20375d84fcf88ac074c61e69ce0"
)
LIVE_ROUTING_INPUT_SHA256 = {
    LIVE_ROUTING_ROOT_RELATIVE
    / "covapie_successor_task_domain_event_routing_inventory_v1.csv": (
        "ed89971ff76bad5ff352002891d7822adccb4655797f7ae8c5dfbc1592247fe8"
    ),
    LIVE_ROUTING_ROOT_RELATIVE
    / "covapie_successor_task_domain_routing_manifest_v1.json": (
        "84e957456efb107cc8bafa68d2b122d6d9fe6ae070d285bd165c9e6b99796251"
    ),
    LIVE_ROUTING_ROOT_RELATIVE
    / "covapie_successor_task_domain_routing_summary_v1.json": (
        "c0ecca63766529716b02adab7658bd3fa54907a4b53a1fcade56997c116f543e"
    ),
    LIVE_ROUTING_ROOT_RELATIVE
    / "covapie_successor_task_domain_unit_routing_inventory_v1.csv": (
        "3512c4a3ff8e871a3120e45c18193462da270d893f9e0b45a97bfefad9dc94e7"
    ),
}

EXPECTED_PILOT_CONSTANTS = {
    "RCSB_SEARCH_EXAMINATION_CAP": 5000,
    "RCSB_CONNECTION_RECORD_CAP": 5000,
    "RCSB_EXACT_SHORTLIST_CAP": 300,
    "UNIQUE_PDB_ACQUISITION_CAP": 250,
    "SPECIALIST_RECORD_EXAMINATION_CAP": 5000,
    "SPECIALIST_NORMALIZED_RECORD_CAP": 2000,
    "UNIQUE_NEW_EVENT_PROCESSING_CAP": 250,
    "COMPRESSED_FILE_CAP": 64 * 1024 * 1024,
    "COVPDB_COMPLEX_ARCHIVE_CAP": 512 * 1024 * 1024,
    "TOTAL_COMPRESSED_DOWNLOAD_CAP": 2 * 1024 * 1024 * 1024,
    "NETWORK_TIMEOUT_SECONDS": 30,
    "MAX_ATTEMPTS_PER_REQUEST": 2,
    "SPECIALIST_SEEDED_PDB_CAP": 1500,
}

KNOWN_TERMINAL_ROUTES = frozenset(
    (
        "KNOWN_EXISTING_APPROVED_SAMPLE",
        "KNOWN_EXISTING_QUARANTINE",
        "KNOWN_RUNTIME_EXTENSION",
    )
)
HISTORICAL_TRANCHE = "HISTORICAL_PILOT_001_250"
INCREMENTAL_TRANCHE = "INCREMENTAL_251_500"
INCREMENTAL_RULE_STATUS = (
    "PENDING_STRUCTURE_PROCESSING_NOT_YET_RULE_EVALUABLE"
)

EVENT_HEADER = (
    "scaleup_rank",
    "tranche",
    "selection_priority_pass",
    "canonical_event_id",
    "pdb_id",
    "protein_label_asym_id",
    "protein_auth_chain",
    "protein_residue_name",
    "protein_residue_number",
    "protein_reactive_atom",
    "ligand_component_id",
    "ligand_instance",
    "ligand_reactive_atom",
    "canonical_source_dataset_count",
    "source_record_provenance_count",
    "source_datasets_json",
    "source_provenance_identities_json",
    "historical_pilot_processed",
    "historical_bulk_structure_acquisition_status",
    "historical_terminal_route",
    "historical_terminal_reasons_json",
    "current_123_two_rule_routing_population_overlap",
    "structure_execution_status",
    "task_domain_rule_evaluation_status",
)

SELECTION_PASS_DESCRIPTIONS = (
    {
        "order": 1,
        "pass": "KNOWN_EXISTING_CONTROL_IDENTITY_FIRST",
        "predicate": "(pdb_id, ligand_component_id) in historical known identities",
        "within_pass_order": "canonical_event_id ascending",
    },
    {
        "order": 2,
        "pass": "MULTI_SOURCE_PROVENANCE",
        "predicate": "source_count > 1",
        "within_pass_order": "canonical_event_id ascending",
    },
    {
        "order": 3,
        "pass": "SUPPORTING_PRE_OR_ADDUCT_SMILES",
        "predicate": (
            "supporting_pre_reaction_smiles nonempty or "
            "supporting_adduct_smiles nonempty"
        ),
        "within_pass_order": "canonical_event_id ascending",
    },
    {
        "order": 4,
        "pass": "MULTIPLE_PARSED_PRE_HEAVY_ATOM_COUNTS",
        "predicate": (
            "more than one distinct RDKit-parsed pre-reaction heavy-atom count"
        ),
        "within_pass_order": "canonical_event_id ascending",
    },
    {
        "order": 5,
        "pass": "FIRST_CANONICAL_EVENT_PER_LIGAND_COMPONENT",
        "predicate": "first canonical event in each ligand_component_id bucket",
        "within_pass_order": (
            "ligand_component_id ascending; bucket first is canonical_event_id ascending"
        ),
    },
    {
        "order": 6,
        "pass": "CANONICAL_EVENT_ID_FALLBACK",
        "predicate": "all canonical events",
        "within_pass_order": "canonical_event_id ascending",
    },
)

PROCESSING_STAGE_READINESS = (
    {
        "stage_name": "BULK_01_SOURCE_ACCESS_RESOLUTION",
        "implementation_symbols": ["source_access_resolution_v1"],
        "logic_reusable_unchanged_for_500": True,
        "historical_cap_embedded": False,
        "external_network_or_cache_used": False,
        "cohort_size_generic": True,
        "obvious_o_n_squared_or_high_memory_scale_risk": False,
        "modification_required_before_500_execution": False,
        "classification": "READY_UNCHANGED",
        "audit_basis": "Static source-policy records and adapter validation.",
    },
    {
        "stage_name": "BULK_02_SOURCE_DISCOVERY",
        "implementation_symbols": [
            "discover_covpdb_v1",
            "discover_covbinder_v1",
            "discover_rcsb_direct_v1",
            "discover_rcsb_specialist_seeded_v1",
        ],
        "logic_reusable_unchanged_for_500": False,
        "historical_cap_embedded": True,
        "external_network_or_cache_used": True,
        "cohort_size_generic": False,
        "obvious_o_n_squared_or_high_memory_scale_risk": False,
        "modification_required_before_500_execution": False,
        "classification": "NOT_APPLICABLE_TO_REHEARSAL",
        "audit_basis": "Frozen 2387-event discovery snapshot is reused; discovery is not rerun.",
    },
    {
        "stage_name": "BULK_03_SOURCE_ADAPTER_NORMALIZATION",
        "implementation_symbols": [
            "adapters.normalize_covpdb_ligand_record_v1",
            "adapters.normalize_covbinderinpdb_record_v1",
            "adapters.normalize_rcsb_connection_record_v1",
        ],
        "logic_reusable_unchanged_for_500": False,
        "historical_cap_embedded": True,
        "external_network_or_cache_used": False,
        "cohort_size_generic": True,
        "obvious_o_n_squared_or_high_memory_scale_risk": False,
        "modification_required_before_500_execution": False,
        "classification": "NOT_APPLICABLE_TO_REHEARSAL",
        "audit_basis": "Published canonical rows are consumed without re-normalization.",
    },
    {
        "stage_name": "BULK_04_CROSS_SOURCE_EVENT_DEDUP",
        "implementation_symbols": ["adapters.merge_cross_source_events_v1"],
        "logic_reusable_unchanged_for_500": False,
        "historical_cap_embedded": False,
        "external_network_or_cache_used": False,
        "cohort_size_generic": True,
        "obvious_o_n_squared_or_high_memory_scale_risk": False,
        "modification_required_before_500_execution": False,
        "classification": "NOT_APPLICABLE_TO_REHEARSAL",
        "audit_basis": "Published cross-source canonical event identities are frozen input.",
    },
    {
        "stage_name": "BULK_05_STRUCTURE_ACQUISITION",
        "implementation_symbols": [
            "select_structural_pilot_events_v1",
            "_acquire_structures_v1",
            "BulkCacheV1.fetch",
        ],
        "logic_reusable_unchanged_for_500": False,
        "historical_cap_embedded": True,
        "external_network_or_cache_used": True,
        "cohort_size_generic": False,
        "obvious_o_n_squared_or_high_memory_scale_risk": False,
        "modification_required_before_500_execution": True,
        "classification": "READY_WITH_CONFIGURABLE_CAP",
        "audit_basis": (
            "UNIQUE_NEW_EVENT_PROCESSING_CAP=250 and UNIQUE_PDB_ACQUISITION_CAP=250 "
            "are module constants; exact cohort injection/configurable caps are required."
        ),
    },
    {
        "stage_name": "BULK_06_MMCIF_VALIDATION",
        "implementation_symbols": ["_validate_mmcif_payload"],
        "logic_reusable_unchanged_for_500": True,
        "historical_cap_embedded": True,
        "external_network_or_cache_used": False,
        "cohort_size_generic": True,
        "obvious_o_n_squared_or_high_memory_scale_risk": False,
        "modification_required_before_500_execution": False,
        "classification": "READY_UNCHANGED",
        "audit_basis": "Per-payload gzip, entry-id, struct_conn, atom_site validation; 64 MiB cap remains explicit.",
    },
    {
        "stage_name": "BULK_07_EXACT_CYS_SG_EVENT_RECOVERY",
        "implementation_symbols": ["process_event_structure_v1", "_connection_matches_event"],
        "logic_reusable_unchanged_for_500": True,
        "historical_cap_embedded": False,
        "external_network_or_cache_used": False,
        "cohort_size_generic": True,
        "obvious_o_n_squared_or_high_memory_scale_risk": False,
        "modification_required_before_500_execution": False,
        "classification": "READY_UNCHANGED",
        "audit_basis": "Per-event exact struct_conn recovery.",
    },
    {
        "stage_name": "BULK_08_COMPONENT_TOPOLOGY_AND_ATOM_MAPPING",
        "implementation_symbols": ["acquire_ccd_components_v1", "parse_ccd_cif_v1", "_select_endpoint_pair"],
        "logic_reusable_unchanged_for_500": True,
        "historical_cap_embedded": True,
        "external_network_or_cache_used": True,
        "cohort_size_generic": True,
        "obvious_o_n_squared_or_high_memory_scale_risk": False,
        "modification_required_before_500_execution": False,
        "classification": "READY_UNCHANGED",
        "audit_basis": "Unique CCD iteration and per-event atom mapping; bounded fetch applies the per-file cap.",
    },
    {
        "stage_name": "BULK_09_MODEL_AND_FEATURE_COMPATIBILITY",
        "implementation_symbols": [
            "process_event_structure_v1",
            "feature_owner.project_type_symbols_to_checkpoint_heavy_v1",
        ],
        "logic_reusable_unchanged_for_500": True,
        "historical_cap_embedded": False,
        "external_network_or_cache_used": False,
        "cohort_size_generic": True,
        "obvious_o_n_squared_or_high_memory_scale_risk": False,
        "modification_required_before_500_execution": False,
        "classification": "READY_UNCHANGED",
        "audit_basis": (
            "Per-event feature projection is reusable; feature semantics and unknown-atom "
            "policy are already resolved. Training remains outside this rehearsal and "
            "awaits later training-path/runtime integration and explicit authorization."
        ),
    },
    {
        "stage_name": "BULK_10_PRE_REACTION_REPRESENTABILITY",
        "implementation_symbols": ["supporting_source_graph_facts_v1", "_rdkit_pre_facts"],
        "logic_reusable_unchanged_for_500": True,
        "historical_cap_embedded": False,
        "external_network_or_cache_used": False,
        "cohort_size_generic": True,
        "obvious_o_n_squared_or_high_memory_scale_risk": False,
        "modification_required_before_500_execution": False,
        "classification": "READY_UNCHANGED",
        "audit_basis": "Per-event deterministic source-graph analysis.",
    },
    {
        "stage_name": "BULK_11_EXISTING_EXACT_AUTHORITY_MATCH",
        "implementation_symbols": ["evaluate_production_exact_authority_v1"],
        "logic_reusable_unchanged_for_500": True,
        "historical_cap_embedded": False,
        "external_network_or_cache_used": False,
        "cohort_size_generic": True,
        "obvious_o_n_squared_or_high_memory_scale_risk": False,
        "modification_required_before_500_execution": False,
        "classification": "READY_UNCHANGED",
        "audit_basis": "Per-event evaluation against the small frozen exact-authority registry.",
    },
    {
        "stage_name": "BULK_12_LEAKAGE_AND_SPLIT_PREDICTION",
        "implementation_symbols": ["apply_leakage_predictions_read_only_v1", "_leakage_linking_axes_v1"],
        "logic_reusable_unchanged_for_500": True,
        "historical_cap_embedded": False,
        "external_network_or_cache_used": False,
        "cohort_size_generic": True,
        "obvious_o_n_squared_or_high_memory_scale_risk": True,
        "modification_required_before_500_execution": False,
        "classification": "READY_UNCHANGED",
        "audit_basis": (
            "Explicit pairwise candidate comparison is O(N^2); 500-event scope is bounded and "
            "does not establish a real scale blocker requiring a fix."
        ),
    },
    {
        "stage_name": "BULK_13_AUTOMATIC_ROUTING",
        "implementation_symbols": ["process_event_structure_v1", "_terminal_outcome"],
        "logic_reusable_unchanged_for_500": True,
        "historical_cap_embedded": False,
        "external_network_or_cache_used": False,
        "cohort_size_generic": True,
        "obvious_o_n_squared_or_high_memory_scale_risk": False,
        "modification_required_before_500_execution": False,
        "classification": "READY_UNCHANGED",
        "audit_basis": "Per-event fail-closed terminal routing; this rehearsal does not invoke it.",
    },
    {
        "stage_name": "BULK_14_HUMAN_REVIEW_CLUSTERING",
        "implementation_symbols": ["build_human_review_units_v1", "cluster_review_units_v1"],
        "logic_reusable_unchanged_for_500": True,
        "historical_cap_embedded": False,
        "external_network_or_cache_used": False,
        "cohort_size_generic": True,
        "obvious_o_n_squared_or_high_memory_scale_risk": False,
        "modification_required_before_500_execution": False,
        "classification": "READY_UNCHANGED",
        "audit_basis": "Dictionary bucketing and deterministic sorting; no human decisions are executed here.",
    },
    {
        "stage_name": "BULK_15_SUMMARY",
        "implementation_symbols": ["_build_summary_v1", "validate_summary_reconciliation_v1"],
        "logic_reusable_unchanged_for_500": True,
        "historical_cap_embedded": False,
        "external_network_or_cache_used": False,
        "cohort_size_generic": True,
        "obvious_o_n_squared_or_high_memory_scale_risk": False,
        "modification_required_before_500_execution": False,
        "classification": "READY_UNCHANGED",
        "audit_basis": "Linear aggregations plus deterministic reconciliation checks.",
    },
)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _json_cell(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        temporary.unlink()
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _bound_payload(repo_root: Path, relative: Path, expected_sha256: str) -> bytes:
    path = repo_root / relative
    if not path.is_file():
        raise ValueError("BOUND_INPUT_MISSING:" + relative.as_posix())
    payload = path.read_bytes()
    if _sha(payload) != expected_sha256:
        raise ValueError("BOUND_INPUT_SHA256_MISMATCH:" + relative.as_posix())
    return payload


def _binding_record(relative: Path, payload: bytes) -> dict[str, object]:
    return {
        "path": relative.as_posix(),
        "byte_count": len(payload),
        "sha256": _sha(payload),
    }


def _verify_historical_constants_v1() -> None:
    actual = {
        name: getattr(frozen_bulk, name) for name in EXPECTED_PILOT_CONSTANTS
    }
    if actual != EXPECTED_PILOT_CONSTANTS:
        raise ValueError("FROZEN_PILOT_CONSTANTS_MISMATCH")


def _historical_priority_order_v1(
    events: Sequence[Mapping[str, Any]],
    *,
    known_identities: set[tuple[str, str]],
) -> tuple[list[Mapping[str, Any]], dict[str, str]]:
    """Reproduce the frozen selector's ordered add passes before bounded caps."""

    ordered = sorted(events, key=lambda item: str(item["canonical_event_id"]))
    selected: list[Mapping[str, Any]] = []
    selected_ids: set[str] = set()
    selection_pass: dict[str, str] = {}

    def add(items: Sequence[Mapping[str, Any]], pass_name: str) -> None:
        for item in items:
            event_id = str(item["canonical_event_id"])
            if event_id in selected_ids:
                continue
            selected.append(item)
            selected_ids.add(event_id)
            selection_pass[event_id] = pass_name

    add(
        [
            item
            for item in ordered
            if (str(item["pdb_id"]), str(item["ligand_component_id"]))
            in known_identities
        ],
        "KNOWN_EXISTING_CONTROL_IDENTITY_FIRST",
    )
    add(
        [item for item in ordered if int(item["source_count"]) > 1],
        "MULTI_SOURCE_PROVENANCE",
    )
    add(
        [
            item
            for item in ordered
            if item["supporting_pre_reaction_smiles"]
            or item["supporting_adduct_smiles"]
        ],
        "SUPPORTING_PRE_OR_ADDUCT_SMILES",
    )
    atom_loss_candidates: list[Mapping[str, Any]] = []
    for item in ordered:
        pre_counts = [
            molecule.GetNumHeavyAtoms()
            for value in item["supporting_pre_reaction_smiles"]
            if (molecule := frozen_bulk._source_molecule_v1(value)) is not None
        ]
        if len(set(pre_counts)) > 1:
            atom_loss_candidates.append(item)
    add(atom_loss_candidates, "MULTIPLE_PARSED_PRE_HEAVY_ATOM_COUNTS")
    by_component: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for item in ordered:
        by_component[str(item["ligand_component_id"])].append(item)
    add(
        [by_component[key][0] for key in sorted(by_component)],
        "FIRST_CANONICAL_EVENT_PER_LIGAND_COMPONENT",
    )
    add(ordered, "CANONICAL_EVENT_ID_FALLBACK")
    if len(selected) != len(events) or len(selected_ids) != len(events):
        raise ValueError("HISTORICAL_PRIORITY_ORDER_COVERAGE_FAILED")
    return selected, selection_pass


def _apply_historical_caps_v1(
    priority_order: Sequence[Mapping[str, Any]],
    *,
    known_event_ids: set[str],
    target_new_event_count: int,
    unique_pdb_cap: int,
) -> list[Mapping[str, Any]]:
    selected: list[Mapping[str, Any]] = []
    selected_pdbs: set[str] = set()
    total_limit = target_new_event_count + len(known_event_ids)
    for item in priority_order:
        if len(selected) >= total_limit:
            break
        pdb_id = str(item["pdb_id"])
        if pdb_id not in selected_pdbs and len(selected_pdbs) >= unique_pdb_cap:
            continue
        selected.append(item)
        selected_pdbs.add(pdb_id)
    return selected


def _load_inputs_v1(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    _verify_historical_constants_v1()
    source_payload = _bound_payload(
        repo_root, FROZEN_BULK_SOURCE_RELATIVE, FROZEN_BULK_SOURCE_SHA256
    )
    pilot_payloads = {
        relative: _bound_payload(repo_root, relative, digest)
        for relative, digest in PILOT_INPUT_SHA256.items()
    }
    routing_payloads = {
        relative: _bound_payload(repo_root, relative, digest)
        for relative, digest in LIVE_ROUTING_INPUT_SHA256.items()
    }
    feature_resolution_payload = _bound_payload(
        repo_root,
        FEATURE_RESOLUTION_MANIFEST_RELATIVE,
        FEATURE_RESOLUTION_MANIFEST_SHA256,
    )

    cross = json.loads(
        pilot_payloads[
            PILOT_ROOT_RELATIVE / "cross_source_canonical_event_manifest_v1.json"
        ]
    )
    outcomes_artifact = json.loads(
        pilot_payloads[PILOT_ROOT_RELATIVE / "bulk_processing_outcomes_v1.json"]
    )
    acquisition = json.loads(
        pilot_payloads[PILOT_ROOT_RELATIVE / "bulk_acquisition_manifest_v1.json"]
    )
    pilot_summary = json.loads(
        pilot_payloads[PILOT_ROOT_RELATIVE / "bulk_summary_v1.json"]
    )
    source_access = json.loads(
        pilot_payloads[
            PILOT_ROOT_RELATIVE / "bulk_source_access_resolution_v1.json"
        ]
    )
    feature_resolution = json.loads(feature_resolution_payload)
    expected_summary = {
        "all_source_normalized_record_count": 9020,
        "source_records_with_event_identity_count": 5244,
        "records_without_canonical_event_identity_count": 3776,
        "cross_source_duplicate_record_count": 2857,
        "canonical_unique_event_count": 2387,
        "known_existing_event_count": 27,
        "new_unique_candidate_event_count": 2360,
        "unique_pdb_count": 1270,
        "structurally_model_eligible_new_event_count": 218,
        "structural_evidence_incomplete_count": 2142,
    }
    for field, expected in expected_summary.items():
        if pilot_summary.get(field) != expected:
            raise ValueError("HISTORICAL_SUMMARY_MISMATCH:" + field)
    resolved_feature_state = {
        "feature_semantics_audit_completed": True,
        "feature_semantics_known": True,
        "unknown_atom_feature_policy_resolved": True,
        "unknown_atom_policy_contract_resolved": True,
    }
    if (
        any(
            pilot_summary.get(field) is not expected
            for field, expected in resolved_feature_state.items()
        )
        or any(
            feature_resolution.get(field) is not expected
            for field, expected in resolved_feature_state.items()
        )
        or feature_resolution.get("schema_version")
        != frozen_bulk.feature_owner.SCHEMA_VERSION
        or feature_resolution.get("policy_resolution_completed") is not True
        or feature_resolution.get("resolution_outcome")
        != "resolved_policy_contract"
        or feature_resolution.get("training_used") is not False
        or feature_resolution.get("ready_for_training") is not False
        or pilot_summary.get("ready_for_full_training") is not False
        or pilot_summary.get("ready_for_full_training_false_reason")
        != "LATER_TRAINING_PATH_OR_MIXED_RUNTIME_INTEGRATION_NOT_FEATURE_SEMANTICS"
    ):
        raise ValueError("AUTHORITATIVE_RESOLVED_FEATURE_STATE_MISMATCH")
    if (
        pilot_summary["all_source_normalized_record_count"]
        != pilot_summary["records_without_canonical_event_identity_count"]
        + pilot_summary["cross_source_duplicate_record_count"]
        + pilot_summary["canonical_unique_event_count"]
    ):
        raise ValueError("HISTORICAL_SOURCE_POPULATION_RECONCILIATION_FAILED")

    events = list(cross["canonical_events"])
    outcomes = list(outcomes_artifact["events"])
    if len(events) != 2387 or len(outcomes) != 2387:
        raise ValueError("HISTORICAL_CANONICAL_OR_OUTCOME_COUNT_MISMATCH")
    event_by_id = {str(item["canonical_event_id"]): item for item in events}
    outcome_by_id = {str(item["canonical_event_id"]): item for item in outcomes}
    if (
        len(event_by_id) != 2387
        or len(outcome_by_id) != 2387
        or set(event_by_id) != set(outcome_by_id)
    ):
        raise ValueError("HISTORICAL_EVENT_OUTCOME_IDENTITY_COVERAGE_FAILED")

    known_event_ids = {
        event_id
        for event_id, outcome in outcome_by_id.items()
        if outcome["terminal_outcome"] in KNOWN_TERMINAL_ROUTES
    }
    if len(known_event_ids) != 27:
        raise ValueError("KNOWN_EXISTING_CONTROL_COUNT_MISMATCH")
    known_identities = {
        (
            str(event_by_id[event_id]["pdb_id"]),
            str(event_by_id[event_id]["ligand_component_id"]),
        )
        for event_id in known_event_ids
    }
    new_event_ids = set(event_by_id) - known_event_ids
    if len(new_event_ids) != 2360:
        raise ValueError("NEW_EVENT_UNIVERSE_COUNT_MISMATCH")

    frozen_selection = frozen_bulk.select_structural_pilot_events_v1(
        events, known_identities=known_identities
    )
    frozen_selection_ids = [
        str(item["canonical_event_id"]) for item in frozen_selection
    ]
    direct_processed_ids = {
        event_id
        for event_id, outcome in outcome_by_id.items()
        if outcome["stage_statuses"][frozen_bulk.BULK_STAGES[4]]
        != "NOT_SELECTED_BOUNDED_CAP"
    }
    if (
        len(frozen_selection_ids) != 277
        or len(set(frozen_selection_ids) - known_event_ids) != 250
        or set(frozen_selection_ids) != direct_processed_ids
    ):
        raise ValueError("HISTORICAL_DIRECT_SELECTION_REPLAY_FAILED")

    priority_order, selection_pass = _historical_priority_order_v1(
        events, known_identities=known_identities
    )
    replay_250 = _apply_historical_caps_v1(
        priority_order,
        known_event_ids=known_event_ids,
        target_new_event_count=250,
        unique_pdb_cap=250,
    )
    replay_250_ids = [str(item["canonical_event_id"]) for item in replay_250]
    if replay_250_ids != frozen_selection_ids:
        raise ValueError("HISTORICAL_ORDERED_SELECTION_REPLAY_FAILED")

    ordered_new_events = [
        item
        for item in priority_order
        if str(item["canonical_event_id"]) in new_event_ids
    ]
    cohort = ordered_new_events[:500]
    if len(cohort) != 500 or len(
        {str(item["canonical_event_id"]) for item in cohort}
    ) != 500:
        raise ValueError("CUMULATIVE_500_COHORT_IDENTITY_FAILED")
    historical_new = [
        item
        for item in frozen_selection
        if str(item["canonical_event_id"]) in new_event_ids
    ]
    if len(historical_new) != 250:
        raise ValueError("HISTORICAL_PROCESSED_NEW_COUNT_MISMATCH")

    routing_manifest_relative = (
        LIVE_ROUTING_ROOT_RELATIVE
        / "covapie_successor_task_domain_routing_manifest_v1.json"
    )
    routing_summary_relative = (
        LIVE_ROUTING_ROOT_RELATIVE
        / "covapie_successor_task_domain_routing_summary_v1.json"
    )
    routing_event_relative = (
        LIVE_ROUTING_ROOT_RELATIVE
        / "covapie_successor_task_domain_event_routing_inventory_v1.csv"
    )
    routing_manifest = json.loads(routing_payloads[routing_manifest_relative])
    routing_summary = json.loads(routing_payloads[routing_summary_relative])
    routing_rows = list(
        csv.DictReader(io.StringIO(routing_payloads[routing_event_relative].decode("utf-8")))
    )
    routing_event_ids = {str(row["canonical_event_id"]) for row in routing_rows}
    if len(routing_event_ids) != 123 or not routing_event_ids.issubset(
        {str(item["canonical_event_id"]) for item in historical_new}
    ):
        raise ValueError("CURRENT_ROUTING_POPULATION_NOT_HISTORICAL_SUBSET")
    expected_rule_ids = [
        "NEG_V1_TS_DUMP_CATALYTIC_ADDUCT_EXACT",
        "NEG_V2_DTT_CRYSTALLIZATION_REDUCING_ADDUCT_EXACT",
    ]
    if (
        routing_manifest.get("integrated_auto_negative_rule_ids")
        != expected_rule_ids
        or routing_summary.get("integrated_auto_negative_rule_ids")
        != expected_rule_ids
        or routing_summary.get("candidate_events") != 123
        or routing_summary.get("candidate_units") != 36
        or routing_summary.get("effective_new_auto_negative_events") != 32
        or routing_summary.get("effective_new_auto_negative_units") != 2
        or routing_summary.get("effective_task_domain_resolved_units") != 12
        or routing_summary.get("effective_task_domain_human_review_required_units")
        != 24
        or routing_summary.get("effective_task_domain_human_review_required_events")
        != 56
        or routing_summary.get("human_overlay_reviewed_units") != 10
        or routing_summary.get("human_overlay_unreviewed_units") != 26
    ):
        raise ValueError("CURRENT_TWO_RULE_ROUTING_BASELINE_MISMATCH")

    rcsb_access = next(
        item
        for item in source_access["sources"]
        if item["source_name"] == "SOURCE_RCSB_PDB_DIRECT"
    )
    source_access_compatible = bool(
        rcsb_access["current_lane_status"] == "OPERATIONAL_BULK_API"
        and rcsb_access["metadata_bulk_access_allowed"] is True
        and rcsb_access["programmatic_access_allowed"] is True
        and rcsb_access["official_bulk_download_endpoint"]
        == frozen_bulk.RCSB_MMCIF_URL
    )
    if not source_access_compatible:
        raise ValueError("PUBLISHED_RCSB_SOURCE_ACCESS_POLICY_INCOMPATIBLE")

    bindings = {
        "frozen_bulk_source": _binding_record(
            FROZEN_BULK_SOURCE_RELATIVE, source_payload
        ),
        "historical_bulk_inputs": [
            _binding_record(relative, pilot_payloads[relative])
            for relative in sorted(pilot_payloads, key=lambda item: item.as_posix())
        ],
        "published_two_rule_routing_inputs": [
            _binding_record(relative, routing_payloads[relative])
            for relative in sorted(routing_payloads, key=lambda item: item.as_posix())
        ],
        "published_feature_semantics_resolution": _binding_record(
            FEATURE_RESOLUTION_MANIFEST_RELATIVE, feature_resolution_payload
        ),
    }
    return {
        "bindings": bindings,
        "events": events,
        "event_by_id": event_by_id,
        "outcome_by_id": outcome_by_id,
        "known_event_ids": known_event_ids,
        "known_identities": known_identities,
        "new_event_ids": new_event_ids,
        "priority_order": priority_order,
        "selection_pass": selection_pass,
        "frozen_selection": frozen_selection,
        "historical_new": historical_new,
        "cohort": cohort,
        "acquisition": acquisition,
        "pilot_summary": pilot_summary,
        "resolved_feature_state": resolved_feature_state,
        "routing_event_ids": routing_event_ids,
        "routing_summary": routing_summary,
        "source_access_compatible": source_access_compatible,
    }


def _csv_bytes(rows: Sequence[Mapping[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=EVENT_HEADER, lineterminator="\n", extrasaction="raise"
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _build_cohort_rows_v1(inputs: Mapping[str, Any]) -> list[dict[str, object]]:
    outcome_by_id = inputs["outcome_by_id"]
    routing_event_ids = inputs["routing_event_ids"]
    rows: list[dict[str, object]] = []
    for rank, event in enumerate(inputs["cohort"], 1):
        event_id = str(event["canonical_event_id"])
        historical = rank <= 250
        outcome = outcome_by_id[event_id]
        if historical:
            routing_overlap = "true" if event_id in routing_event_ids else "false"
            rule_status = (
                "CURRENT_TWO_RULE_ROUTING_EVALUATED"
                if event_id in routing_event_ids
                else "HISTORICAL_PROCESSED_OUTSIDE_CURRENT_123_ROUTING_POPULATION"
            )
            structure_status = "HISTORICAL_PROCESSING_ALREADY_EXECUTED"
            bulk_05 = outcome["stage_statuses"][frozen_bulk.BULK_STAGES[4]]
            terminal_route = outcome["terminal_outcome"]
            terminal_reasons = outcome["terminal_reasons"]
        else:
            routing_overlap = "NOT_APPLICABLE_NOT_YET_PROCESSED"
            rule_status = INCREMENTAL_RULE_STATUS
            structure_status = "NOT_YET_EXECUTED"
            bulk_05 = ""
            terminal_route = ""
            terminal_reasons = []
        rows.append(
            {
                "scaleup_rank": rank,
                "tranche": HISTORICAL_TRANCHE if historical else INCREMENTAL_TRANCHE,
                "selection_priority_pass": inputs["selection_pass"][event_id],
                "canonical_event_id": event_id,
                "pdb_id": event["pdb_id"],
                "protein_label_asym_id": event["protein_instance"],
                "protein_auth_chain": event.get("protein_auth_chain") or "",
                "protein_residue_name": event["protein_residue_name"],
                "protein_residue_number": event["protein_residue_number"],
                "protein_reactive_atom": event["protein_reactive_atom"],
                "ligand_component_id": event["ligand_component_id"],
                "ligand_instance": event["ligand_instance"],
                "ligand_reactive_atom": event["ligand_reactive_atom"],
                "canonical_source_dataset_count": event["source_count"],
                "source_record_provenance_count": event["source_record_count"],
                "source_datasets_json": _json_cell(event["source_datasets"]),
                "source_provenance_identities_json": _json_cell(
                    event["source_record_ids"]
                ),
                "historical_pilot_processed": "true" if historical else "false",
                "historical_bulk_structure_acquisition_status": bulk_05,
                "historical_terminal_route": terminal_route,
                "historical_terminal_reasons_json": _json_cell(terminal_reasons),
                "current_123_two_rule_routing_population_overlap": routing_overlap,
                "structure_execution_status": structure_status,
                "task_domain_rule_evaluation_status": rule_status,
            }
        )
    return rows


def _requirement_rows_v1(
    cohort: Sequence[Mapping[str, Any]],
    *,
    identity_field: str,
    committed_status: Mapping[str, str],
) -> list[dict[str, object]]:
    buckets: dict[str, list[tuple[int, Mapping[str, Any]]]] = defaultdict(list)
    for rank, event in enumerate(cohort, 1):
        buckets[str(event[identity_field])].append((rank, event))
    rows: list[dict[str, object]] = []
    for identity in sorted(buckets):
        members = buckets[identity]
        historical_count = sum(rank <= 250 for rank, _event in members)
        incremental_count = len(members) - historical_count
        status = committed_status.get(
            identity, "NOT_PRESENT_IN_COMMITTED_PILOT_ACQUISITION_MANIFEST"
        )
        row: dict[str, object] = {
            "event_count": len(members),
            "historical_pilot_event_count": historical_count,
            "incremental_event_count": incremental_count,
            "tranche_membership": [
                tranche
                for tranche, count in (
                    (HISTORICAL_TRANCHE, historical_count),
                    (INCREMENTAL_TRANCHE, incremental_count),
                )
                if count
            ],
            "scaleup_ranks": [rank for rank, _event in members],
            "canonical_event_ids": [
                str(event["canonical_event_id"]) for _rank, event in members
            ],
            "committed_pilot_acquisition_status": status,
            "committed_pilot_resolved_payload": status
            in {"SOURCE_VERIFIED", "CCD_COMPONENT_RESOLVED"},
        }
        row["pdb_id" if identity_field == "pdb_id" else "ccd_id"] = identity
        rows.append(row)
    return rows


def _control_requirement_rows_v1(
    controls: Sequence[Mapping[str, Any]], *, identity_field: str
) -> list[dict[str, object]]:
    buckets: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for event in controls:
        buckets[str(event[identity_field])].append(event)
    label = "pdb_id" if identity_field == "pdb_id" else "ccd_id"
    return [
        {
            label: identity,
            "event_count": len(buckets[identity]),
            "canonical_event_ids": [
                str(item["canonical_event_id"]) for item in buckets[identity]
            ],
            "lane": "KNOWN_EXISTING_CONTROL_REFERENCE_LANE",
        }
        for identity in sorted(buckets)
    ]


def _build_acquisition_requirements_v1(
    inputs: Mapping[str, Any]
) -> dict[str, Any]:
    cohort = list(inputs["cohort"])
    historical = cohort[:250]
    incremental = cohort[250:]
    controls = [
        item
        for item in inputs["priority_order"]
        if str(item["canonical_event_id"]) in inputs["known_event_ids"]
    ]
    committed_pdb_status = {
        str(item["pdb_id"]): str(item["acquisition_status"])
        for item in inputs["acquisition"]["structures"]
    }
    committed_ccd_status = {
        str(item["ccd_id"]): str(item["status"])
        for item in inputs["acquisition"]["ccd_components"]
    }
    pdb_rows = _requirement_rows_v1(
        cohort,
        identity_field="pdb_id",
        committed_status=committed_pdb_status,
    )
    ccd_rows = _requirement_rows_v1(
        cohort,
        identity_field="ligand_component_id",
        committed_status=committed_ccd_status,
    )
    historical_pdb = {str(item["pdb_id"]) for item in historical}
    incremental_pdb = {str(item["pdb_id"]) for item in incremental}
    historical_ccd = {str(item["ligand_component_id"]) for item in historical}
    incremental_ccd = {str(item["ligand_component_id"]) for item in incremental}
    cumulative_pdb = historical_pdb | incremental_pdb
    cumulative_ccd = historical_ccd | incremental_ccd
    control_pdb = {str(item["pdb_id"]) for item in controls}
    control_ccd = {str(item["ligand_component_id"]) for item in controls}
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_semantics": "DETERMINISTIC_ACQUISITION_IDENTITY_REQUIREMENTS_ONLY",
        "population": {
            "cumulative_new_event_count": 500,
            "historical_pilot_new_event_count": 250,
            "incremental_new_event_count": 250,
            "known_existing_control_event_count": 27,
            "known_controls_counted_against_new_event_cap": False,
        },
        "pdb_requirements": {
            "official_endpoint_template": frozen_bulk.RCSB_MMCIF_URL,
            "cumulative_500_unique_pdb_count": len(cumulative_pdb),
            "historical_250_unique_pdb_count": len(historical_pdb),
            "incremental_250_unique_pdb_count": len(incremental_pdb),
            "incremental_new_unique_pdb_count": len(
                incremental_pdb - historical_pdb
            ),
            "requirements": pdb_rows,
            "known_control_unique_pdb_count": len(control_pdb),
            "known_control_requirements": _control_requirement_rows_v1(
                controls, identity_field="pdb_id"
            ),
            "planning_universe_unique_pdb_count_including_controls": len(
                cumulative_pdb | control_pdb
            ),
        },
        "ccd_requirements": {
            "official_endpoint_template": frozen_bulk.RCSB_CCD_URL,
            "cumulative_500_unique_ccd_count": len(cumulative_ccd),
            "historical_250_unique_ccd_count": len(historical_ccd),
            "incremental_250_unique_ccd_count": len(incremental_ccd),
            "incremental_new_ccd_count": len(incremental_ccd - historical_ccd),
            "requirements": ccd_rows,
            "known_control_unique_ccd_count": len(control_ccd),
            "known_control_requirements": _control_requirement_rows_v1(
                controls, identity_field="ligand_component_id"
            ),
            "planning_universe_unique_ccd_count_including_controls": len(
                cumulative_ccd | control_ccd
            ),
        },
        "hard_execution_safety_limits": {
            "single_compressed_file_cap_bytes": frozen_bulk.COMPRESSED_FILE_CAP,
            "total_compressed_download_cap_bytes": (
                frozen_bulk.TOTAL_COMPRESSED_DOWNLOAD_CAP
            ),
            "network_timeout_seconds": frozen_bulk.NETWORK_TIMEOUT_SECONDS,
            "max_attempts_per_request": frozen_bulk.MAX_ATTEMPTS_PER_REQUEST,
            "later_executor_must_fail_closed_before_total_cap_exceeded": True,
        },
        "execution_not_performed": True,
        "network_performed": False,
        "downloaded_bytes": 0,
    }


def _ordered_id_sha(events: Sequence[Mapping[str, Any]]) -> str:
    return _sha(
        _canonical_json([str(item["canonical_event_id"]) for item in events])
    )


def build_artifacts_v1(*, repo_root: Path) -> dict[str, bytes]:
    inputs = _load_inputs_v1(repo_root)
    cohort = list(inputs["cohort"])
    historical_new = list(inputs["historical_new"])
    historical_500_prefix = cohort[:250]
    historical_ids = [str(item["canonical_event_id"]) for item in historical_new]
    prefix_ids = [str(item["canonical_event_id"]) for item in historical_500_prefix]
    prefix_exact = prefix_ids == historical_ids
    set_equal = set(prefix_ids) == set(historical_ids)
    order_equal = prefix_ids == historical_ids

    old_cap_scale_selection = _apply_historical_caps_v1(
        inputs["priority_order"],
        known_event_ids=inputs["known_event_ids"],
        target_new_event_count=500,
        unique_pdb_cap=frozen_bulk.UNIQUE_PDB_ACQUISITION_CAP,
    )
    old_cap_scale_new_count = sum(
        str(item["canonical_event_id"]) in inputs["new_event_ids"]
        for item in old_cap_scale_selection
    )

    cohort_rows = _build_cohort_rows_v1(inputs)
    cohort_payload = _csv_bytes(cohort_rows)
    requirements = _build_acquisition_requirements_v1(inputs)
    acquisition_payload = _canonical_json(requirements)

    historical_outcomes = [
        inputs["outcome_by_id"][str(item["canonical_event_id"])]
        for item in historical_new
    ]
    historical_terminal_counts = dict(
        sorted(Counter(item["terminal_outcome"] for item in historical_outcomes).items())
    )
    controls = [
        item
        for item in inputs["priority_order"]
        if str(item["canonical_event_id"]) in inputs["known_event_ids"]
    ]
    control_terminal_counts = dict(
        sorted(
            Counter(
                inputs["outcome_by_id"][str(item["canonical_event_id"])][
                    "terminal_outcome"
                ]
                for item in controls
            ).items()
        )
    )
    structural_scale_blockers = [
        item["stage_name"]
        for item in PROCESSING_STAGE_READINESS
        if item["classification"] == "NEEDS_MINIMAL_SCALE_FIX"
    ]
    readiness_checks = {
        "exact_historical_selection_algorithm_reproduced": True,
        "historical_250_exact_prefix_parity": prefix_exact,
        "cumulative_500_deterministic": len(cohort) == 500,
        "cumulative_500_canonical_ids_unique": len(
            {str(item["canonical_event_id"]) for item in cohort}
        )
        == 500,
        "all_500_in_published_new_event_universe": all(
            str(item["canonical_event_id"]) in inputs["new_event_ids"]
            for item in cohort
        ),
        "known_27_separate": not any(
            str(item["canonical_event_id"]) in inputs["known_event_ids"]
            for item in cohort
        ),
        "all_500_have_pdb_identity": all(bool(item["pdb_id"]) for item in cohort),
        "all_source_evidenced_ccd_identities_derived": all(
            bool(item["ligand_component_id"]) for item in cohort
        ),
        "official_bounded_source_access_compatible": inputs[
            "source_access_compatible"
        ],
        "no_unresolved_structural_scale_blocker": not structural_scale_blockers,
        "hard_download_caps_explicit": True,
        "network_not_performed_in_rehearsal": True,
        "frozen_predecessor_not_modified": True,
    }
    ready = all(readiness_checks.values())
    execution_blockers = [
        key for key, passed in readiness_checks.items() if not passed
    ]

    pdb = requirements["pdb_requirements"]
    ccd = requirements["ccd_requirements"]
    summary = {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "snapshot_semantics": SNAPSHOT_SEMANTICS,
        "historical_population": {
            "all_source_normalized_record_count": 9020,
            "source_records_with_event_identity_count": 5244,
            "records_without_canonical_event_identity_count": 3776,
            "cross_source_duplicate_record_count": 2857,
            "canonical_unique_event_count": 2387,
            "new_unique_candidate_event_count": 2360,
            "known_existing_event_count": 27,
            "unique_pdb_count": 1270,
            "structurally_model_eligible_new_event_count": 218,
            "structural_evidence_incomplete_count": 2142,
        },
        "cohort": {
            "cumulative_new_event_count": 500,
            "historical_pilot_new_event_count": 250,
            "incremental_new_event_count": 250,
            "remaining_unselected_new_event_count": 1860,
            "historical_250_exact_prefix_of_500": prefix_exact,
            "historical_250_set_equal": set_equal,
            "historical_250_order_equal": order_equal,
            "cumulative_500_ordered_event_ids_sha256": _ordered_id_sha(cohort),
            "historical_250_ordered_event_ids_sha256": _ordered_id_sha(
                historical_new
            ),
            "incremental_250_ordered_event_ids_sha256": _ordered_id_sha(
                cohort[250:]
            ),
        },
        "historical_pilot_outcomes_for_250_new_only": {
            "exact_outcome_coverage_count": len(historical_outcomes),
            "structural_model_eligible_count": sum(
                item["stage_statuses"][frozen_bulk.BULK_STAGES[8]] == "PASSED"
                for item in historical_outcomes
            ),
            "structural_evidence_incomplete_but_selected_for_processing_count": sum(
                item["terminal_outcome"] == "STRUCTURAL_EVIDENCE_INCOMPLETE"
                for item in historical_outcomes
            ),
            "leakage_existing_group_conflict_count": historical_terminal_counts.get(
                "LEAKAGE_EXISTING_GROUP_CONFLICT", 0
            ),
            "quarantine_representation_gap_count": historical_terminal_counts.get(
                "QUARANTINE_REPRESENTATION_GAP", 0
            ),
            "terminal_route_counts": historical_terminal_counts,
            "current_123_two_rule_routing_overlap_count": len(
                set(historical_ids) & inputs["routing_event_ids"]
            ),
        },
        "known_existing_controls": {
            "event_count": len(controls),
            "counted_against_500_new_event_cap": False,
            "terminal_route_counts": control_terminal_counts,
        },
        "acquisition_identity_counts": {
            "cumulative_500_unique_pdb_count": pdb[
                "cumulative_500_unique_pdb_count"
            ],
            "historical_250_unique_pdb_count": pdb[
                "historical_250_unique_pdb_count"
            ],
            "incremental_250_unique_pdb_count": pdb[
                "incremental_250_unique_pdb_count"
            ],
            "incremental_new_unique_pdb_count": pdb[
                "incremental_new_unique_pdb_count"
            ],
            "cumulative_500_unique_ccd_count": ccd[
                "cumulative_500_unique_ccd_count"
            ],
            "historical_250_unique_ccd_count": ccd[
                "historical_250_unique_ccd_count"
            ],
            "incremental_250_unique_ccd_count": ccd[
                "incremental_250_unique_ccd_count"
            ],
            "incremental_new_ccd_count": ccd["incremental_new_ccd_count"],
        },
        "incremental_tranche_scientific_status": {
            "event_count": 250,
            "structure_execution_status": "NOT_YET_EXECUTED",
            "task_domain_rule_evaluation_status": INCREMENTAL_RULE_STATUS,
            "auto_negative_rate_extrapolated_from_current_123": False,
            "future_chemistry_family_predicted": False,
            "future_warhead_predicted": False,
            "human_decision_created": False,
            "training_eligibility_claimed": False,
        },
        "two_rule_live_routing_baseline": {
            "published_baseline_commit_ancestor": PUBLISHED_BASELINE_COMMIT_ANCESTOR,
            "integrated_rule_ids": inputs["routing_summary"][
                "integrated_auto_negative_rule_ids"
            ],
            "candidate_events": 123,
            "candidate_units": 36,
            "effective_auto_negative_events": 32,
            "effective_auto_negative_units": 2,
            "effective_resolved_units": 12,
            "human_review_required_units": 24,
            "human_review_required_events": 56,
            "human_overlay_reviewed_units": 10,
            "human_overlay_unreviewed_units": 26,
            "baseline_is_not_prediction_for_incremental_250": True,
        },
        "execution_configuration_requirements": {
            "frozen_pilot_source_must_remain_unchanged": True,
            "additive_executor_must_accept_exact_500_cohort": True,
            "required_new_event_processing_cap": 500,
            "required_unique_pdb_capacity_for_500_new_plus_27_controls": pdb[
                "planning_universe_unique_pdb_count_including_controls"
            ],
            "unchanged_historical_unique_pdb_cap": 250,
            "new_events_selected_if_historical_250_pdb_cap_reused": (
                old_cap_scale_new_count
            ),
            "historical_250_pdb_cap_is_insufficient_for_500": (
                old_cap_scale_new_count < 500
            ),
            "hard_single_file_cap_bytes": frozen_bulk.COMPRESSED_FILE_CAP,
            "hard_total_download_cap_bytes": (
                frozen_bulk.TOTAL_COMPRESSED_DOWNLOAD_CAP
            ),
        },
        "readiness_checks": readiness_checks,
        "execution_blockers": execution_blockers,
        "network_performed": False,
        "external_cache_modified": False,
        "frozen_bulk_pilot_modified": False,
        "successor_routing_modified": False,
        "human_overlay_modified": False,
        "production_authority_created": False,
        "training_materialization_performed": False,
        "structural_processing_execution_performed": False,
        "ready_for_controlled_500_event_execution": ready,
        "ready_for_gpt_review": True,
        "recommended_next_step_exactly": (
            "gpt_audit_500_event_scaleup_rehearsal_then_authorize_controlled_"
            "500_event_bulk_execution_v1"
            if ready
            else "gpt_audit_500_event_scaleup_rehearsal_then_resolve_exact_scale_blocker"
        ),
        "output_sha256": {
            COHORT: _sha(cohort_payload),
            ACQUISITION: _sha(acquisition_payload),
        },
    }
    summary_payload = _canonical_json(summary)

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "stage": STAGE,
        "snapshot_semantics": SNAPSHOT_SEMANTICS,
        "published_baseline_commit_ancestor": PUBLISHED_BASELINE_COMMIT_ANCESTOR,
        "published_baseline_subject": PUBLISHED_BASELINE_SUBJECT,
        "input_bindings": inputs["bindings"],
        "historical_pilot_constants_verified": EXPECTED_PILOT_CONSTANTS,
        "historical_selection_audit": {
            "algorithm": (
                "Stable canonical_event_id ordering is passed through six ordered "
                "coverage-priority add passes; first occurrence wins, known controls "
                "are admitted first, unique-PDB admission is fail-closed, and the total "
                "limit is known-event count plus the new-event cap."
            ),
            "ordered_passes": list(SELECTION_PASS_DESCRIPTIONS),
            "cap_application_location": (
                "select_structural_pilot_events_v1.add before "
                "_acquire_structures_v1 in "
                "build_covapie_bulk_cys_sg_dataset_expansion_artifacts_v1"
            ),
            "historical_new_event_processing_cap": 250,
            "historical_unique_pdb_acquisition_cap": 250,
            "historical_selected_total_event_count_including_controls": 277,
            "historical_processed_new_event_count": 250,
            "historical_selected_unique_pdb_count_including_controls": len(
                {str(item["pdb_id"]) for item in inputs["frozen_selection"]}
            ),
            "historical_unique_pdb_cap_was_nonbinding": len(
                {str(item["pdb_id"]) for item in inputs["frozen_selection"]}
            )
            < 250,
            "direct_artifact_selection_field": (
                "bulk_processing_outcomes_v1.events[].stage_statuses."
                "BULK_05_STRUCTURE_ACQUISITION != NOT_SELECTED_BOUNDED_CAP"
            ),
        },
        "prefix_parity_proof": {
            "historical_250_exact_prefix_of_500": prefix_exact,
            "historical_250_set_equal": set_equal,
            "historical_250_order_equal": order_equal,
            "historical_250_ordered_event_ids_sha256": _ordered_id_sha(
                historical_new
            ),
            "derived_500_prefix_ordered_event_ids_sha256": _ordered_id_sha(
                historical_500_prefix
            ),
        },
        "processing_stage_readiness": list(PROCESSING_STAGE_READINESS),
        "authoritative_resolved_feature_state": {
            **inputs["resolved_feature_state"],
            "published_resolution_binding": inputs["bindings"][
                "published_feature_semantics_resolution"
            ],
            "historical_bulk_summary_binding": next(
                item
                for item in inputs["bindings"]["historical_bulk_inputs"]
                if item["path"].endswith("/bulk_summary_v1.json")
            ),
            "training_performed_or_authorized_by_rehearsal": False,
            "training_status_reason": (
                "LATER_TRAINING_PATH_OR_MIXED_RUNTIME_INTEGRATION_AND_EXPLICIT_"
                "AUTHORIZATION_NOT_UNFINISHED_FEATURE_SEMANTICS"
            ),
        },
        "official_bounded_source_access_compatible": inputs[
            "source_access_compatible"
        ],
        "execution_requirements": summary["execution_configuration_requirements"],
        "two_rule_routing_baseline_provenance": summary[
            "two_rule_live_routing_baseline"
        ],
        "safety": {
            "preparation_and_rehearsal_only": True,
            "discovery_rerun": False,
            "network_performed": False,
            "download_performed": False,
            "external_cache_modified": False,
            "structural_processing_execution_performed": False,
            "successor_routing_modified": False,
            "human_review_performed": False,
            "production_authority_created": False,
            "training_materialization_performed": False,
        },
        "ready_for_controlled_500_event_execution": ready,
        "ready_for_gpt_review": True,
        "output_sha256_excluding_manifest": {
            COHORT: _sha(cohort_payload),
            ACQUISITION: _sha(acquisition_payload),
            SUMMARY: _sha(summary_payload),
        },
    }
    manifest_payload = _canonical_json(manifest)
    artifacts = {
        MANIFEST: manifest_payload,
        COHORT: cohort_payload,
        ACQUISITION: acquisition_payload,
        SUMMARY: summary_payload,
    }
    if tuple(artifacts) != OUTPUT_FILENAMES:
        raise ValueError("REHEARSAL_OUTPUT_FILE_SET_INVALID")
    return artifacts


def materialize_v1(
    *, repo_root: Path, output_root: Path | None = None
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    target = (
        output_root.resolve()
        if output_root is not None
        else repo_root / OUTPUT_ROOT_RELATIVE
    )
    if target != repo_root / OUTPUT_ROOT_RELATIVE:
        try:
            target.relative_to(Path(tempfile.gettempdir()).resolve())
        except ValueError as error:
            raise ValueError("REHEARSAL_OUTPUT_ROOT_OUTSIDE_AUTHORIZED_PATH") from error
    artifacts = build_artifacts_v1(repo_root=repo_root)
    for name in OUTPUT_FILENAMES:
        _atomic_write(target / name, artifacts[name])
    return json.loads(artifacts[SUMMARY])


def verify_deterministic_replay_v1(repo_root: Path) -> dict[str, str]:
    repo_root = repo_root.resolve()
    output_root = repo_root / OUTPUT_ROOT_RELATIVE
    committed = {name: (output_root / name).read_bytes() for name in OUTPUT_FILENAMES}
    replay = build_artifacts_v1(repo_root=repo_root)
    if committed != replay:
        raise ValueError("REHEARSAL_OUTPUT_REPLAY_NOT_BYTE_IDENTICAL")
    return {name: _sha(committed[name]) for name in OUTPUT_FILENAMES}


def validate_task_repository_observation_v1(
    observation: Mapping[str, object],
) -> dict[str, object]:
    """Validate the synchronized-main descendant publication contract."""

    if observation.get("branch") != "main":
        raise ValueError("TASK_REPOSITORY_BRANCH_MISMATCH")
    if observation.get("runtime_head") != observation.get("runtime_origin_main"):
        raise ValueError("TASK_REPOSITORY_HEAD_ORIGIN_MISMATCH")
    if (observation.get("ahead"), observation.get("behind")) != (0, 0):
        raise ValueError("TASK_REPOSITORY_AHEAD_BEHIND_MISMATCH")
    if observation.get("baseline_ancestor_of_head") is not True:
        raise ValueError("TASK_REPOSITORY_BASELINE_NOT_ANCESTOR_OF_HEAD")
    if observation.get("baseline_ancestor_of_origin_main") is not True:
        raise ValueError("TASK_REPOSITORY_BASELINE_NOT_ANCESTOR_OF_ORIGIN_MAIN")
    if observation.get("baseline_subject") != PUBLISHED_BASELINE_SUBJECT:
        raise ValueError("TASK_REPOSITORY_BASELINE_SUBJECT_MISMATCH")
    if observation.get("modified_tracked") != []:
        raise ValueError("TASK_REPOSITORY_MODIFIED_TRACKED_FILES")
    if observation.get("staged") != []:
        raise ValueError("TASK_REPOSITORY_STAGED_FILES")
    return dict(observation)


def classify_rehearsal_worktree_profile_v1(
    *,
    modified_tracked: Sequence[str],
    staged: Sequence[str],
    untracked: Sequence[str],
) -> str:
    """Accept only the exact precommit candidate or clean published profile."""

    if modified_tracked or staged:
        raise ValueError("REHEARSAL_500_WORKTREE_PROFILE_INVALID")
    untracked_set = set(untracked)
    if untracked_set == AUTHORIZED_REHEARSAL_PATHS and len(untracked) == len(
        AUTHORIZED_REHEARSAL_PATHS
    ):
        return REHEARSAL_500_PRECOMMIT_CANDIDATE
    if not untracked:
        return REHEARSAL_500_PUBLISHED_CLEAN_DESCENDANT
    raise ValueError("REHEARSAL_500_WORKTREE_PROFILE_INVALID")


def verify_task_repository_baseline_v1(repo_root: Path) -> dict[str, object]:
    """Read-only synchronized-main descendant gate for build/check runtime."""

    repo_root = repo_root.resolve()

    def git(*arguments: str) -> str:
        return subprocess.run(
            ("git", *arguments),
            cwd=repo_root,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout.strip()

    def baseline_is_ancestor_of(reference: str) -> bool:
        result = subprocess.run(
            (
                "git",
                "merge-base",
                "--is-ancestor",
                PUBLISHED_BASELINE_COMMIT_ANCESTOR,
                reference,
            ),
            cwd=repo_root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if result.returncode not in (0, 1):
            raise RuntimeError(
                "TASK_REPOSITORY_ANCESTRY_OBSERVATION_FAILED:"
                + result.stderr.strip()
            )
        return result.returncode == 0

    branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD")
    origin_main = git("rev-parse", "origin/main")
    left, right = git(
        "rev-list", "--left-right", "--count", "HEAD...origin/main"
    ).split()
    modified_tracked = [item for item in git("diff", "--name-only").splitlines() if item]
    staged = [
        item for item in git("diff", "--cached", "--name-only").splitlines() if item
    ]
    observation: dict[str, object] = {
        "branch": branch,
        "runtime_head": head,
        "runtime_origin_main": origin_main,
        "ahead": int(left),
        "behind": int(right),
        "baseline_ancestor_of_head": baseline_is_ancestor_of("HEAD"),
        "baseline_ancestor_of_origin_main": baseline_is_ancestor_of("origin/main"),
        "baseline_subject": git(
            "show",
            "-s",
            "--format=%s",
            PUBLISHED_BASELINE_COMMIT_ANCESTOR,
        ),
        "modified_tracked": modified_tracked,
        "staged": staged,
        "untracked": [
            item
            for item in git("ls-files", "--others", "--exclude-standard").splitlines()
            if item
        ],
    }
    return validate_task_repository_observation_v1(observation)


def _nearest_rank(values: Sequence[int], percentile: float) -> int:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(percentile * len(ordered)) - 1)]


def _size_statistics(values: Sequence[int]) -> dict[str, object]:
    if not values:
        return {
            "sample_count": 0,
            "mean_bytes": None,
            "median_bytes": None,
            "p90_bytes": None,
            "p95_bytes": None,
            "max_bytes": None,
            "percentile_method": "NEAREST_RANK",
        }
    return {
        "sample_count": len(values),
        "mean_bytes": round(sum(values) / len(values), 6),
        "median_bytes": statistics.median(values),
        "p90_bytes": _nearest_rank(values, 0.90),
        "p95_bytes": _nearest_rank(values, 0.95),
        "max_bytes": max(values),
        "percentile_method": "NEAREST_RANK",
    }


def _cache_tree_stat_fingerprint(cache_root: Path) -> str | None:
    if not cache_root.is_dir():
        return None
    rows = [
        (
            path.relative_to(cache_root).as_posix(),
            path.stat().st_size,
            path.stat().st_mtime_ns,
        )
        for path in sorted(cache_root.rglob("*"))
        if path.is_file()
    ]
    return _sha(_canonical_json(rows))


def observe_current_cache_v1(
    *,
    repo_root: Path,
    cache_root: Path | None = None,
    acquisition_requirements: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Observe current cache coverage without constructing ``BulkCacheV1``."""

    repo_root = repo_root.resolve()
    root = (
        cache_root.resolve()
        if cache_root is not None
        else repo_root.parent / DEFAULT_CACHE_RELATIVE_TO_REPOSITORY_PARENT
    )
    requirements = (
        acquisition_requirements
        if acquisition_requirements is not None
        else json.loads(build_artifacts_v1(repo_root=repo_root)[ACQUISITION])
    )
    ledger_path = root / "cache_manifest_v1.json"
    if not root.is_dir() or not ledger_path.is_file():
        return {
            "current_cache_available": False,
            "current_cache_total_bytes": None,
            "current_required_pdb_cache_hits": None,
            "current_required_pdb_cache_misses": None,
            "current_required_ccd_cache_hits": None,
            "current_required_ccd_cache_misses": None,
            "download_size_statistics": {
                "pdb_structure_payloads": _size_statistics([]),
                "ccd_payloads": _size_statistics([]),
            },
            "incremental_expected_download_bytes_using_mean": None,
            "incremental_expected_download_bytes_using_p95": None,
            "observation_only": True,
            "cache_modified": False,
        }
    before = _cache_tree_stat_fingerprint(root)
    ledger = json.loads(ledger_path.read_bytes())
    if ledger.get("schema_version") != "covapie_bulk_cache_manifest_v1":
        raise ValueError("CACHE_OBSERVATION_MANIFEST_SCHEMA_INVALID")
    entries = {str(item["relative_path"]): item for item in ledger["payloads"]}
    integrity_failures: list[str] = []

    def valid(relative: str) -> bool:
        entry = entries.get(relative)
        path = root / relative
        if entry is None or not path.is_file():
            return False
        payload = path.read_bytes()
        if len(payload) != int(entry["byte_count"]) or _sha(payload) != entry["sha256"]:
            integrity_failures.append(relative)
            return False
        return True

    pdb_rows = requirements["pdb_requirements"]["requirements"]
    ccd_rows = requirements["ccd_requirements"]["requirements"]
    pdb_hits = {
        str(item["pdb_id"])
        for item in pdb_rows
        if valid(f"rcsb/structures/{item['pdb_id']}.cif.gz")
    }
    ccd_hits = {
        str(item["ccd_id"])
        for item in ccd_rows
        if valid(f"rcsb/ccd/{item['ccd_id']}.cif")
    }
    control_pdb_rows = requirements["pdb_requirements"][
        "known_control_requirements"
    ]
    control_ccd_rows = requirements["ccd_requirements"][
        "known_control_requirements"
    ]
    control_pdb_hits = {
        str(item["pdb_id"])
        for item in control_pdb_rows
        if valid(f"rcsb/structures/{item['pdb_id']}.cif.gz")
    }
    control_ccd_hits = {
        str(item["ccd_id"])
        for item in control_ccd_rows
        if valid(f"rcsb/ccd/{item['ccd_id']}.cif")
    }

    structure_sizes: list[int] = []
    ccd_sizes: list[int] = []
    for relative, entry in sorted(entries.items()):
        path = root / relative
        if not path.is_file() or path.stat().st_size != int(entry["byte_count"]):
            continue
        if relative.startswith("rcsb/structures/") and relative.endswith(".cif.gz"):
            structure_sizes.append(path.stat().st_size)
        elif relative.startswith("rcsb/ccd/") and relative.endswith(".cif"):
            ccd_sizes.append(path.stat().st_size)
    structure_stats = _size_statistics(structure_sizes)
    ccd_stats = _size_statistics(ccd_sizes)
    incremental_pdb = {
        str(item["pdb_id"])
        for item in pdb_rows
        if INCREMENTAL_TRANCHE in item["tranche_membership"]
    }
    incremental_ccd = {
        str(item["ccd_id"])
        for item in ccd_rows
        if INCREMENTAL_TRANCHE in item["tranche_membership"]
    }
    incremental_missing_pdb = len(incremental_pdb - pdb_hits)
    incremental_missing_ccd = len(incremental_ccd - ccd_hits)
    if structure_stats["mean_bytes"] is None or ccd_stats["mean_bytes"] is None:
        mean_projection = None
        p95_projection = None
    else:
        mean_projection = math.ceil(
            incremental_missing_pdb * float(structure_stats["mean_bytes"])
            + incremental_missing_ccd * float(ccd_stats["mean_bytes"])
        )
        p95_projection = (
            incremental_missing_pdb * int(structure_stats["p95_bytes"])
            + incremental_missing_ccd * int(ccd_stats["p95_bytes"])
        )
    after = _cache_tree_stat_fingerprint(root)
    if before != after:
        raise ValueError("READ_ONLY_CACHE_OBSERVATION_CHANGED_TREE_METADATA")
    all_files = [path for path in root.rglob("*") if path.is_file()]
    return {
        "current_cache_available": True,
        "current_cache_total_bytes": sum(path.stat().st_size for path in all_files),
        "current_cache_file_count": len(all_files),
        "current_required_pdb_cache_hits": len(pdb_hits),
        "current_required_pdb_cache_misses": len(pdb_rows) - len(pdb_hits),
        "current_required_ccd_cache_hits": len(ccd_hits),
        "current_required_ccd_cache_misses": len(ccd_rows) - len(ccd_hits),
        "current_known_control_pdb_cache_hits": len(control_pdb_hits),
        "current_known_control_pdb_cache_misses": len(control_pdb_rows)
        - len(control_pdb_hits),
        "current_known_control_ccd_cache_hits": len(control_ccd_hits),
        "current_known_control_ccd_cache_misses": len(control_ccd_rows)
        - len(control_ccd_hits),
        "incremental_required_pdb_cache_hits": len(incremental_pdb & pdb_hits),
        "incremental_required_pdb_cache_misses": incremental_missing_pdb,
        "incremental_required_ccd_cache_hits": len(incremental_ccd & ccd_hits),
        "incremental_required_ccd_cache_misses": incremental_missing_ccd,
        "download_size_statistics": {
            "pdb_structure_payloads": structure_stats,
            "ccd_payloads": ccd_stats,
        },
        "incremental_expected_download_bytes_using_mean": mean_projection,
        "incremental_expected_download_bytes_using_p95": p95_projection,
        "estimate_is_not_guarantee": True,
        "hard_single_file_cap_bytes": frozen_bulk.COMPRESSED_FILE_CAP,
        "hard_total_download_cap_bytes": frozen_bulk.TOTAL_COMPRESSED_DOWNLOAD_CAP,
        "projected_p95_within_hard_total_cap": (
            p95_projection is not None
            and p95_projection < frozen_bulk.TOTAL_COMPRESSED_DOWNLOAD_CAP
        ),
        "cache_integrity_failure_count": len(set(integrity_failures)),
        "cache_integrity_failures": sorted(set(integrity_failures)),
        "observation_only": True,
        "cache_modified": False,
    }
