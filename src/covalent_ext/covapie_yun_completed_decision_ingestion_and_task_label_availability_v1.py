"""Ingest the frozen YUN Exact7 human decision as deterministic metadata.

This additive projection validates and ingests authority already present in the
formal human decision.  D5 INCLUDE is projected as future-admission candidacy
under the published FFQ/POA separation; it is not training admission,
materialization, runtime usability, tensor authority, or parameter-update
authorization.  This owner does not reinterpret chemistry, reconstruct PRE
topology or geometry, reconcile global state, tensorize data, or train.
"""

from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
from typing import Any


__all__ = (
    "YUNIngestionSafetyError",
    "load_frozen_formal_decision_v1",
    "validate_completed_decision_projection_v1",
    "build_artifacts_v1",
    "materialize_artifacts_v1",
    "check_materialized_v1",
)

SCHEMA_VERSION = "covapie_yun_completed_decision_ingestion_and_task_label_availability_v1"
SNAPSHOT_SCHEMA_VERSION = "covapie_yun_completed_human_decision_snapshot_v1"
MATRIX_SCHEMA_VERSION = "covapie_yun_event_task_label_availability_v1"
SUMMARY_SCHEMA_VERSION = "covapie_yun_completed_decision_ingestion_summary_v1"
MANIFEST_SCHEMA_VERSION = "covapie_yun_completed_decision_ingestion_manifest_v1"

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_yun_completed_decision_ingestion_and_task_label_availability_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/"
    "check_covapie_yun_completed_decision_ingestion_and_task_label_availability_v1.py"
)
TEST_RELATIVE = Path(
    "tests/"
    "test_covapie_yun_completed_decision_ingestion_and_task_label_availability_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_yun_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT = "covapie_yun_completed_human_decision_snapshot_v1.json"
MATRIX = "covapie_yun_event_task_label_availability_v1.csv"
SUMMARY = "covapie_yun_completed_decision_ingestion_summary_v1.json"
MANIFEST = "covapie_yun_completed_decision_ingestion_manifest_v1.json"
OUTPUT_FILENAMES = (SNAPSHOT, MATRIX, SUMMARY, MANIFEST)
OUTPUT_RELATIVE_PATHS = tuple(OUTPUT_ROOT_RELATIVE / name for name in OUTPUT_FILENAMES)
CANDIDATE_PUBLICATION_PATHS = (
    SOURCE_RELATIVE,
    CHECKER_RELATIVE,
    TEST_RELATIVE,
    *OUTPUT_RELATIVE_PATHS,
)

# Frozen after semantic validation of the fully source-derived projection.
# These are derived-projection contract digests, never human/science authority.
_EXPECTED_SNAPSHOT_SHA256_V1 = (
    "6ce626eb5fcbc8f875f727732daa6047ac35152319db8cfe444725e648d6a012"
)
_EXPECTED_MATRIX_SHA256_V1 = (
    "f5c58990490282a9a3ab5218f8ed83f8cead6062fdeb06c4fedc10665630ca0e"
)
_EXPECTED_SUMMARY_SHA256_V1 = (
    "899faf081224d113bd6e8b277464dbb0b0ee1a992d5262d9b34736b68f42c32e"
)

FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT = Path(
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "YUN_COVAPIE_BULK_REVIEW_UNIT_1138FFC288DFD03D/"
    "formal-human-decision-v1/yun_formal_human_decision_v1.json"
)
FORMAL_DECISION_BYTE_COUNT = 30722
FORMAL_DECISION_SHA256 = (
    "b4eeebe03354e820d9658225997c34b58b41c66f4dfe126230024306816e1140"
)
FORMAL_DECISION_SCHEMA = "covapie_yun_exact7_formal_human_decision_v1"
FORMAL_SEMANTIC_CANONICAL_SHA256 = (
    "ec54b265d568ce6123031583a0504630d73e89c0aea019a09f89f7f18d2a4de0"
)
EXPECTED_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_1138FFC288DFD03D"
EXPECTED_APPROVED_AT_UTC = "2026-08-27T13:43:03Z"
EXPECTED_ROLE_PROFILE = "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
EXPECTED_D6 = (
    "PD168393 irreversible EGFR acrylamide inhibitor / post-Michael-addition "
    "productized YUN context; no event-specific disposition exception"
)
AUTHORITY_SOURCE = "FORMAL_YUN_HUMAN_DECISION"
AUTHORITY_SCOPE = "SAMPLE_LEVEL_YUN_EXACT7_ONLY"
HUMAN_CONTEXT_SCOPE = "SAMPLE_SPECIFIC_YUN_EXACT7_ONLY"
FUTURE_STATUS = "CANDIDATE_REQUIRES_INDEPENDENT_FUTURE_ADMISSION"
POST_SOURCE_STATUS = "PRESENT_IN_UPSTREAM_EVIDENCE_LINEAGE_NOT_REAUTHORIZED_HERE"

EXPECTED_EVENTS = (
    ("COVAPIE_CYS_SG_EVENT_V1:4LL0:A:CYS:797-:SG:C:YUN:CAN", 783, "4LL0", 1, "A", "CYS:797-", None, "C", None, "covale1", 1.829505, "1.829505"),
    ("COVAPIE_CYS_SG_EVENT_V1:4LL0:B:CYS:797-:SG:D:YUN:CAN", 784, "4LL0", 1, "B", "CYS:797-", None, "D", None, "covale2", 1.829190, "1.829190"),
    ("COVAPIE_CYS_SG_EVENT_V1:4LRM:A:CYS:800-:SG:F:YUN:CAN", 786, "4LRM", 1, "A", "CYS:800-", None, "F", None, "covale1", 1.756770, "1.756770"),
    ("COVAPIE_CYS_SG_EVENT_V1:4LRM:B:CYS:800-:SG:G:YUN:CAN", 787, "4LRM", 1, "B", "CYS:800-", None, "G", None, "covale2", 1.759076, "1.759076"),
    ("COVAPIE_CYS_SG_EVENT_V1:4LRM:C:CYS:800-:SG:H:YUN:CAN", 788, "4LRM", 1, "C", "CYS:800-", None, "H", None, "covale3", 1.759789, "1.759789"),
    ("COVAPIE_CYS_SG_EVENT_V1:4LRM:D:CYS:800-:SG:I:YUN:CAN", 789, "4LRM", 1, "D", "CYS:800-", None, "I", None, "covale4", 1.753841, "1.753841"),
    ("COVAPIE_CYS_SG_EVENT_V1:4LRM:E:CYS:800-:SG:J:YUN:CAN", 790, "4LRM", 1, "E", "CYS:800-", None, "J", None, "covale5", 1.757155, "1.757155"),
)
EXPECTED_EVENT_IDS = tuple(row[0] for row in EXPECTED_EVENTS)
EXPECTED_RANKS = tuple(row[1] for row in EXPECTED_EVENTS)

EXPECTED_HEAVY_ATOMS = (
    "BR", "C2", "C4", "C5", "C6", "CAF", "CAH", "CAI", "CAJ", "CAK",
    "CAL", "CAM", "CAN", "CAO", "CAW", "CAX", "CAY", "CAZ", "N1", "N3",
    "NAS", "NAT", "OAC",
)
EXPECTED_WARHEAD = ("NAS", "CAW", "OAC", "CAO", "CAN")
EXPECTED_SOURCE_WARHEAD_ORDER = ("CAN", "CAO", "CAW", "OAC", "NAS")
EXPECTED_LINKER: tuple[str, ...] = ()
EXPECTED_SCAFFOLD = (
    "BR", "C2", "C4", "C5", "C6", "CAF", "CAH", "CAI", "CAJ", "CAK",
    "CAL", "CAM", "CAX", "CAY", "CAZ", "N1", "N3", "NAT",
)

CANONICAL_TASKS = (
    (0, "warhead_only", "A", ("warhead",), ("scaffold", "linker")),
    (1, "linker_plus_warhead", "B", ("linker", "warhead"), ("scaffold",)),
    (2, "scaffold_plus_warhead", "B2", ("scaffold", "warhead"), ("linker",)),
    (3, "scaffold_only", "B3", ("scaffold",), ("linker", "warhead")),
    (4, "scaffold_plus_linker_plus_warhead", "C", ("scaffold", "linker", "warhead"), ("minimal_seed",)),
)
DIRECT_VALID_TASK_IDS = (0, 3, 4)

RUNTIME_SOURCE_RELATIVE = Path(
    "src/covalent_ext/covapie_direct_attachment_optional_linker_runtime_v1.py"
)
CANONICAL_TASK_SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"
)
IMMUTABLE_SEMANTIC_OWNER_BINDINGS = (
    (RUNTIME_SOURCE_RELATIVE, 37255, "434285a43fa0158e62d40f48ed95d137f5fd68ea9b00101cc20674025849c535", "direct_profile_runtime_semantics_owner"),
    (CANONICAL_TASK_SOURCE_RELATIVE, 67274, "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b", "canonical_role_and_task_semantics_owner"),
)

FROZEN_REVIEW_PACKAGE_BINDINGS = (
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/YUN_COVAPIE_BULK_REVIEW_UNIT_1138FFC288DFD03D/review-preparation-v1/yun_machine_evidence_manifest_v1.json"), 14731, "1cb6ee17aa371e1bb42ae439a41e53fad6ea5a00b19c38b850845b6ac1fce9a2", "YUN_MACHINE_EVIDENCE_MANIFEST_REVIEWED_BYTES", "0644"),
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/YUN_COVAPIE_BULK_REVIEW_UNIT_1138FFC288DFD03D/review-preparation-v1/yun_exact7_event_review_v1.csv"), 6269, "42f7ce062df9fd666bbfe64b84227a4d0a5eedb16e2fb8e7f679cc7d5c4c8cf8", "YUN_EXACT7_EVENT_REVIEWED_BYTES", "0644"),
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/YUN_COVAPIE_BULK_REVIEW_UNIT_1138FFC288DFD03D/review-preparation-v1/yun_graph_and_role_candidates_v1.json"), 21826, "b88acddf582a032f3c47ca225b0e2062fca65a347ce327caae08af735ed46c5c", "YUN_GRAPH_AND_ROLE_CANDIDATES_REVIEWED_BYTES", "0644"),
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/YUN_COVAPIE_BULK_REVIEW_UNIT_1138FFC288DFD03D/review-preparation-v1/HUMAN_REVIEW_GUIDE.md"), 6282, "a1a319caf55b181e13f8d4ced2862d992783cb1c527044f03ad61fe7dc9a1fa6", "YUN_HUMAN_REVIEW_GUIDE_REVIEWED_BYTES", "0644"),
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/YUN_COVAPIE_BULK_REVIEW_UNIT_1138FFC288DFD03D/review-preparation-v1/yun_unsigned_human_decision_template_v1.json"), 4354, "e50b202b53d36a54f49bf5ad9701eb99edfd5ed6e89ab29e7dbfc7923a5ca563", "YUN_UNSIGNED_DECISION_TEMPLATE_REVIEWED_BYTES", "0644"),
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/YUN_COVAPIE_BULK_REVIEW_UNIT_1138FFC288DFD03D/review-preparation-v1/ligand_yun_review_package_v1.py"), 92480, "14ed4693329f8aa951b804faa5f83000d389b08a05b53888444ad53fdec8e905", "YUN_REVIEW_PACKAGE_VALIDATOR_REVIEWED_BYTES", "0755"),
)

INCLUDE_REPOSITORY_PRECEDENT_BINDINGS = (
    (Path("src/covalent_ext/covapie_ffq_completed_decision_ingestion_and_task_label_availability_v1.py"), 66788, "2e71c3132a15f500d54430075688c37dc79469b096328943795c98a728fca7ce", "FFQ_INCLUDE_INGESTION_PRECEDENT_OWNER"),
    (Path("data/derived/covalent_small/covapie_ffq_completed_decision_ingestion_and_task_label_availability_v1/covapie_ffq_event_task_label_availability_v1.csv"), 21239, "781972cbee68403805bb0266db65221b0973cb61e666925264dc0d50524090a0", "FFQ_INCLUDE_PUBLISHED_MATRIX_PRECEDENT"),
)
INCLUDE_PARENT_PRECEDENT_BINDINGS = (
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/FFQ_COVAPIE_BULK_REVIEW_UNIT_431D2725ADFC9E9D/formal-human-decision-v1/ffq_formal_human_decision_v1.json"), 14197, "ba0670519064399b2ecb0c73631009c8c6c4d3c14512377ecfaad0d87388e149", "FFQ_INCLUDE_FORMAL_PRECEDENT"),
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/POA_COVAPIE_BULK_REVIEW_UNIT_6A4D564E712634EB/formal-human-decision-v1/poa_formal_human_decision_v1.json"), 15675, "263eec2e33a7b50001f6c058959b9218601fc7fb122dc97e937b517f98c90ba8", "POA_INCLUDE_FORMAL_PRECEDENT"),
)

CURRENT_CENSUS_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_1f8_v1"
)
CURRENT_CENSUS_BINDINGS = (
    (Path("src/covalent_ext/covapie_cumulative1000_current_global_readiness_census_with_1f8_v1.py"), 55130, "cacb60cc5436b7744e7a545f275da44eb33a38825d04d91248ed91146f25f972", "current_1F8_refreshed_census_owner"),
    (CURRENT_CENSUS_ROOT / "covapie_cumulative1000_current_global_readiness_census_with_1f8_v1.csv", 514588, "31d6add9d59d5eb9b40e8603eb9631230a75efa1f52590c3556827f62441175d", "current_1F8_refreshed_census_csv"),
    (CURRENT_CENSUS_ROOT / "covapie_cumulative1000_current_global_readiness_summary_with_1f8_v1.json", 15062, "9a341222ff0932603f900042579b47f6969c50259bfd0d89d75dffe55bf3641f", "current_1F8_refreshed_census_summary"),
    (CURRENT_CENSUS_ROOT / "covapie_cumulative1000_current_global_readiness_manifest_with_1f8_v1.json", 30872, "e9c159fa53550d3fd0a62e9cad0017255bae23a1952f8066e92ca4a56b0b7602", "current_1F8_refreshed_census_manifest"),
)


class YUNIngestionSafetyError(ValueError):
    """Raised when the frozen YUN ingestion contract cannot be proven."""


def _fail(reason: str) -> None:
    raise YUNIngestionSafetyError(reason)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _json_cell(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _csv_bytes(header: Sequence[str], rows: Sequence[Mapping[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=header, extrasaction="raise", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _verify_payload(
    path: Path,
    expected_bytes: int,
    expected_sha256: str,
    label: str,
    expected_mode: str | None = None,
) -> bytes:
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise YUNIngestionSafetyError("BOUND_SOURCE_READ_FAILED:" + label) from error
    if len(payload) != expected_bytes:
        _fail("BOUND_SOURCE_BYTE_COUNT_MISMATCH:" + label)
    if _sha(payload) != expected_sha256:
        _fail("BOUND_SOURCE_SHA256_MISMATCH:" + label)
    if expected_mode is not None and format(path.stat().st_mode & 0o7777, "04o") != expected_mode:
        _fail("BOUND_SOURCE_MODE_MISMATCH:" + label)
    return payload


def _literal_assignments(path: Path, names: Sequence[str]) -> dict[str, object]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, SyntaxError) as error:
        raise YUNIngestionSafetyError("SOURCE_AST_READ_FAILED:" + path.name) from error
    wanted = set(names)
    values: dict[str, object] = {}
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Name) and target.id in wanted:
                try:
                    values[target.id] = ast.literal_eval(node.value)
                except (ValueError, TypeError) as error:
                    raise YUNIngestionSafetyError("SOURCE_CONTRACT_NOT_LITERAL:" + target.id) from error
    if set(values) != wanted:
        _fail("SOURCE_CONTRACT_ASSIGNMENTS_MISSING")
    return values


def _binding_rows(
    bindings: Sequence[tuple[Path, int, str, str]], *, namespace: str
) -> list[dict[str, object]]:
    return [
        {
            "path": relative.as_posix(),
            "path_namespace": namespace,
            "byte_count": byte_count,
            "sha256": sha256,
            "sha256_scope": "file_bytes",
            "source_role": role,
            "verification_status": "MATCHED",
        }
        for relative, byte_count, sha256, role in bindings
    ]


def _formal_binding() -> dict[str, object]:
    return {
        "path": FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT.as_posix(),
        "path_namespace": "repository_parent_relative",
        "byte_count": FORMAL_DECISION_BYTE_COUNT,
        "sha256": FORMAL_DECISION_SHA256,
        "sha256_scope": "file_bytes",
        "schema_version": FORMAL_DECISION_SCHEMA,
        "record_role": "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY",
        "decision_status": "HUMAN_APPROVED_SAMPLE_LEVEL_DECISION",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "ligand_component_id": "YUN",
        "reviewer_id": "fmx",
        "attestor_id": "fmx",
        "approved": True,
        "unsigned": False,
        "approved_at_utc": EXPECTED_APPROVED_AT_UTC,
        "verification_status": "MATCHED",
    }


def _expected_evidence_provenance() -> dict[str, object]:
    rows = []
    for path, byte_count, sha256, _role, mode in FROZEN_REVIEW_PACKAGE_BINDINGS:
        rows.append(
            {
                "name": path.name,
                "path": path.as_posix(),
                "byte_count": byte_count,
                "sha256": sha256,
                "mode": mode,
            }
        )
    return {
        "source_package_path": str(FROZEN_REVIEW_PACKAGE_BINDINGS[0][0].parent),
        "path_namespace": "project_parent_relative",
        "reviewed_machine_evidence_only": True,
        "existing_package_materialized_validation": "PASS",
        "exact6_file_count": 6,
        "exact6_SHA_bindings": rows,
        "human_authorization_origin": "EXTERNAL_EXPLICIT_HUMAN_APPROVAL",
    }


def _expected_raw_event(row: tuple[object, ...]) -> dict[str, object]:
    (
        event_id, rank, pdb_id, model_number, protein_chain, residue_id,
        protein_altloc, ligand_chain, ligand_altloc, connection, distance, _lexeme,
    ) = row
    return {
        "canonical_event_id": event_id,
        "scaleup_rank": rank,
        "pdb_id": pdb_id,
        "model_number": model_number,
        "protein_chain_or_asym": protein_chain,
        "cys_residue_id": residue_id,
        "protein_altloc": protein_altloc,
        "ligand_component_id": "YUN",
        "ligand_chain_or_asym": ligand_chain,
        "ligand_altloc": ligand_altloc,
        "selected_connection_id": connection,
        "POST_distance_angstrom": distance,
        "D1_task_relevance": "RELEVANT",
        "D2_chemistry_support": "POSITIVE",
        "negative_chemistry": False,
        "task_domain_negative": False,
        "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "CAN",
        "ligand_reactive_atom_element": "C",
        "reactive_pair_human_authoritative": True,
        "D4_role_partition": "SELECT_CANDIDATE_4",
        "selected_role_candidate_index_0based": 4,
        "role_partition_human_authoritative": True,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "D5_training_use": "INCLUDE",
        "human_training_excluded": False,
        "human_training_use_include": True,
        "training_admitted": False,
        "D6_context_reference": "UNIT_LEVEL_HUMAN_APPROVED_CONTEXT",
        "event_specific_disposition_exception": False,
        "decision_finalized": True,
    }


def _event_projection(raw: Mapping[str, object], lexeme: str) -> dict[str, object]:
    projected = dict(raw)
    projected.update(
        {
            "POST_distance_frozen_lexeme": lexeme,
            "task_relevant": True,
            "chemistry_known_positive": True,
            "reactive_pair_human_decision_available": True,
            "role_partition_human_decision_available": True,
            "event_training_use_human_decision_available": True,
            "training_use_allowed": True,
            "candidate_for_future_training_admission": True,
            "future_training_admission_status": FUTURE_STATUS,
            "future_training_candidate_derived_by_ingestion": True,
            "future_training_candidate_is_training_admission": False,
            "training_materialization_allowed_now": False,
            "current_runtime_model_usable": False,
            "POST_source_evidence_available": True,
            "POST_geometry_source_evidence_status": POST_SOURCE_STATUS,
            "POST_geometry_training_label_available_now": False,
            "PRE_geometry_authority_available": False,
            "PRE_geometry_training_label_available_now": False,
            "PRE_precursor_topology_authority_available": False,
            "PRE_acrylamide_bond_order_authority_available": False,
            "PRE_CAO_CAN_bond_order_authority_available": False,
            "PRE_reconstruction_performed": False,
            "reaction_family_target_available": False,
            "warhead_rule_target_available": False,
            "warhead_type_target_available": False,
            "reusable_chemistry_authority_available": False,
            "reusable_pair_authority_available": False,
            "reusable_role_authority_available": False,
            "model_bound_pair_target_created_by_ingestion": False,
            "tensor_target_created": False,
            "training_admission_created": False,
            "formal_split_authority_created": False,
            "parameter_update_authorization": False,
            "observed_post_product_state": True,
            "observed_CAO_CAN_bond_order": "SING",
            "authority_source": AUTHORITY_SOURCE,
            "authority_scope": AUTHORITY_SCOPE,
            "authority_ingested": True,
            "authority_created_by_this_ingestion": False,
        }
    )
    return projected


def _role_snapshot() -> dict[str, object]:
    return {
        "human_role_partition_choice": "SELECT_CANDIDATE_4",
        "selected_candidate_index_0based": 4,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "exact_heavy_atom_count": 23,
        "exact_heavy_atom_ids": list(EXPECTED_HEAVY_ATOMS),
        "warhead_atoms": list(EXPECTED_WARHEAD),
        "frozen_source_warhead_atoms_source_order": list(EXPECTED_SOURCE_WARHEAD_ORDER),
        "warhead_atom_set_exactly_matches_frozen_candidate": True,
        "linker_atoms": [],
        "scaffold_atoms": list(EXPECTED_SCAFFOLD),
        "boundary_bonds": [
            {
                "atom_id_1": "CAZ",
                "atom_id_2": "NAS",
                "bond_order": "SING",
                "boundary_between_roles": ["scaffold", "warhead"],
            }
        ],
        "heavy_atom_disjoint": True,
        "heavy_atom_exhaustive": True,
        "warhead_connected": True,
        "linker_empty": True,
        "linker_connected_or_empty": True,
        "scaffold_connected": True,
        "sample_level_role_decision_exists_in_source": True,
        "sample_level_role_decision_created_by_ingestion": False,
        "machine_selected": False,
        "machine_recommended_candidate": None,
    }


def _canonical_task_contract() -> dict[str, object]:
    applicability = [
        {
            "task_id": task_id,
            "semantic_long_name": semantic,
            "display_alias": alias,
            "structurally_applicable": task_id in DIRECT_VALID_TASK_IDS,
            "role_profile": EXPECTED_ROLE_PROFILE,
        }
        for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
    ]
    return {
        "global_canonical_tasks": [
            {
                "task_id": task_id,
                "semantic_long_name": semantic,
                "display_alias": alias,
                "generated_roles": list(generated),
                "fixed_or_seed_roles": list(fixed),
            }
            for task_id, semantic, alias, generated, fixed in CANONICAL_TASKS
        ],
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task_created": False,
        "canonical_task_vocabulary_changed": False,
        "direct_profile_applicable_task_ids": list(DIRECT_VALID_TASK_IDS),
        "direct_profile_applicable_task_count": 3,
        "direct_profile_task_applicability": applicability,
        "D5_INCLUDE_does_not_change_structural_applicability": True,
    }


def _scientific_context() -> dict[str, object]:
    return {
        "D6_exact_choice": EXPECTED_D6,
        "scope": HUMAN_CONTEXT_SCOPE,
        "compound_context": "PD168393",
        "target_context": "EGFR",
        "irreversible_inhibitor_context": True,
        "acrylamide_scientific_context": True,
        "Michael_addition_scientific_context": True,
        "observed_post_Michael_productized_context": True,
        "native_homologous_covalent_cysteine_context": True,
        "engineered_cysteine_site": False,
        "PDB_specific_cysteine_context": {"4LL0": "CYS:797-", "4LRM": "CYS:800-"},
        "event_specific_disposition_exception": False,
        "sample_specific_context_converted_to_reusable_authority": False,
    }


def _observed_graph_pre_boundary() -> dict[str, object]:
    return {
        "observed_graph_identity": "YUN_FROZEN_OBSERVED_POST_MICHAEL_PRODUCT_HEAVY_ATOM_GRAPH",
        "observed_reactive_atom": "CAN",
        "observed_reactive_atom_element": "C",
        "observed_graph_heavy_atom_count": 23,
        "observed_graph_retains_precursor_heavy_atom_inventory": True,
        "observed_graph_is_post_covalent_product_state": True,
        "observed_CAO_CAN_bond_order": "SING",
        "observed_graph_is_authoritative_complete_PRE_bond_order_topology": False,
        "observed_graph_is_authoritative_PRE_geometry": False,
        "observed_graph_is_authoritative_PRE_precursor_topology": False,
        "authoritative_PRE_precursor_topology": None,
        "authoritative_PRE_acrylamide_bond_order_topology": None,
        "PRE_CAO_CAN_bond_order_authority": None,
        "PRE_CAO_CAN_double_bond_authority_created": False,
        "PRE_precursor_topology_authority_created": False,
        "PRE_acrylamide_bond_order_authority_created": False,
        "PRE_geometry_authority_created": False,
        "PRE_reconstruction_performed": False,
        "PRE_bond_order_reconstruction_performed": False,
        "second_PRE_graph_created": False,
    }


def _geometry_boundary() -> dict[str, object]:
    return {
        "POST_source_evidence_count": 7,
        "POST_geometry_source_evidence_status": POST_SOURCE_STATUS,
        "POST_geometry_training_authority_count": 0,
        "POST_geometry_training_label_available_now": False,
        "PRE_status": "PRE_REACTION_UNRESOLVED",
        "PRE_geometry_authority_count": 0,
        "PRE_geometry_training_target_count": 0,
        "PRE_precursor_topology_authority_count": 0,
        "PRE_acrylamide_bond_order_authority_count": 0,
        "PRE_CAO_CAN_bond_order_authority_count": 0,
        "PRE_reconstruction_count": 0,
        "POST_to_PRE_copy_performed": False,
        "PRE_zero_fill_performed": False,
    }


def _training_boundary() -> dict[str, object]:
    return {
        "formal_event_training_use_decision": "INCLUDE",
        "event_training_use_human_decision_available": True,
        "human_training_excluded": False,
        "training_use_allowed": True,
        "candidate_for_future_training_admission": True,
        "future_training_admission_status": FUTURE_STATUS,
        "future_training_candidate_derived_by_ingestion": True,
        "future_training_candidate_is_training_admission": False,
        "training_admitted": False,
        "training_admission_created": False,
        "training_materialization_allowed_now": False,
        "current_runtime_model_usable": False,
        "formal_split_authority_created": False,
        "tensor_target_created": False,
        "parameter_update_authorization": False,
        "ready_for_training": False,
    }


def _reusable_boundary() -> dict[str, object]:
    return {
        "reaction_family_target_available": False,
        "reaction_family_target_count": 0,
        "warhead_rule_target_available": False,
        "warhead_rule_target_count": 0,
        "warhead_type_target_available": False,
        "warhead_type_target_count": 0,
        "reusable_chemistry_authority_available": False,
        "reusable_pair_authority_available": False,
        "reusable_role_authority_available": False,
    }


def _authority_boundary() -> dict[str, object]:
    return {
        "formal_human_decision_modified": False,
        "snapshot_created_by_ingestion": True,
        "human_authority_ingested": True,
        "human_authority_created_by_ingestion": False,
        "future_training_candidate_derived_by_ingestion": True,
        "future_training_candidate_is_training_admission": False,
        "reusable_chemistry_authority_created": False,
        "reusable_pair_authority_created": False,
        "reusable_role_authority_created": False,
        "reaction_family_authority_created": False,
        "warhead_rule_authority_created": False,
        "warhead_type_authority_created": False,
        "PRE_topology_authority_created": False,
        "PRE_geometry_authority_created": False,
        "POST_geometry_training_authority_created": False,
        "training_admission_created": False,
        "training_admitted": False,
        "training_dataset_changed": False,
        "training_materialization_allowed_now": False,
        "formal_split_authority_created": False,
        "current_runtime_model_usable": False,
        "model_bound_pair_target_created_by_ingestion": False,
        "tensor_target_created": False,
        "parameter_update_authorization": False,
        "global_reconciliation_updated": False,
        "global_census_updated": False,
        "tensor_integration_performed": False,
        "loader_modified": False,
        "batch_modified": False,
        "model_forward_performed": False,
        "auxiliary_head_executed": False,
        "loss_executed": False,
        "backward_performed": False,
        "optimizer_created": False,
        "optimizer_step_performed": False,
        "parameter_update_performed": False,
        "fine_tune_performed": False,
        "training_performed": False,
        "network_accessed": False,
        "scientific_network_acquisition_performed": False,
        "commit_performed": False,
        "push_performed": False,
        "ready_for_training": False,
    }


def _validate_formal_decision_v1(formal: Mapping[str, Any]) -> dict[str, object]:
    """Close every nested field and project only frozen sample authority."""

    if type(formal) is not dict:
        _fail("FORMAL_DECISION_TOP_LEVEL_NOT_OBJECT")
    if _sha(_json_bytes(dict(formal))) != FORMAL_SEMANTIC_CANONICAL_SHA256:
        _fail("FORMAL_COMPLETE_NESTED_SEMANTIC_DIGEST_INVALID")
    expected_top = {
        "schema_version": FORMAL_DECISION_SCHEMA,
        "record_role": "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY",
        "decision_status": "HUMAN_APPROVED_SAMPLE_LEVEL_DECISION",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "ligand_component_id": "YUN",
        "exact_event_count": 7,
        "unique_event_count": 7,
        "duplicate_event_count": 0,
        "omission_event_count": 0,
        "extra_event_count": 0,
        "canonical_event_ids": list(EXPECTED_EVENT_IDS),
        "scaleup_ranks": list(EXPECTED_RANKS),
        "pdb_ids": ["4LL0", "4LRM"],
        "reviewer_id": "fmx",
        "attestor_id": "fmx",
        "approved": True,
        "unsigned": False,
        "human_review_completed": True,
        "human_decision_created": True,
        "human_review_decision_created": True,
        "human_approval_recorded": True,
        "formal_authority_created": True,
        "feature_semantics_status": "AUDIT_REQUIRED_LATER",
    }
    for field, expected in expected_top.items():
        if formal.get(field) != expected:
            _fail("FORMAL_TOP_LEVEL_SEMANTICS_INVALID:" + field)
    approval = formal["human_approval"]
    if (
        approval["approved_at_utc"] != EXPECTED_APPROVED_AT_UTC
        or approval["reviewer_id"] != "fmx"
        or approval["attestor_id"] != "fmx"
        or approval["current_authorization_source"] != "EXTERNAL_EXPLICIT_HUMAN_APPROVAL"
        or approval["D1_task_relevance"] != "RELEVANT"
        or approval["D2_chemistry_support"] != "POSITIVE"
        or approval["D3_reactive_pair"] != "CONFIRM_OBSERVED_PAIR"
        or approval["D4_role_partition"] != "SELECT_CANDIDATE_4"
        or approval["D5_training_use"] != "INCLUDE"
        or approval["D6_scientific_context"] != EXPECTED_D6
    ):
        _fail("FORMAL_HUMAN_APPROVAL_SEMANTICS_INVALID")
    if formal["evidence_provenance"] != _expected_evidence_provenance():
        _fail("FORMAL_EXACT6_EVIDENCE_PROVENANCE_DRIFT")
    raw_events = formal["event_level_human_decisions"]
    expected_raw = [_expected_raw_event(row) for row in EXPECTED_EVENTS]
    if raw_events != expected_raw:
        _fail("FORMAL_EXACT7_EVENT_SEMANTICS_INVALID")

    pair = formal["reactive_pair_human_decision"]
    if (
        pair["D3_human_choice"] != "CONFIRM_OBSERVED_PAIR"
        or pair["applies_to_exact_event_count"] != 7
        or pair["protein_reactive_atom"] != "SG"
        or pair["ligand_reactive_atom"] != "CAN"
        or pair["ligand_reactive_atom_element"] != "C"
        or pair["pdb_specific_pairs"] != [
            {"pdb_id": "4LL0", "cys_residue_id": "CYS:797-", "observed_pair": "CYS797_SG_TO_YUN_CAN", "event_count": 2},
            {"pdb_id": "4LRM", "cys_residue_id": "CYS:800-", "observed_pair": "CYS800_SG_TO_YUN_CAN", "event_count": 5},
        ]
        or pair["reactive_pair_human_authoritative_event_count"] != 7
        or pair["model_bound_pair_integration_created"] is not False
        or pair["tensor_target_created"] is not False
        or pair["cross_sample_reusable_pair_authority_created"] is not False
        or pair["training_admission_created"] is not False
    ):
        _fail("FORMAL_REACTIVE_PAIR_SEMANTICS_DRIFT")
    graph = formal["frozen_YUN_graph"]
    role = formal["selected_role_partition"]
    exact5 = formal["canonical_Exact5_and_sample_applicability"]
    if (
        graph["heavy_atom_count"] != 23
        or graph["heavy_atom_ids"] != list(EXPECTED_HEAVY_ATOMS)
        or graph["reactive_atom"] != "CAN"
        or graph["CAN_element"] != "C"
        or role["selected_candidate_index_0based"] != 4
        or role["role_profile"] != EXPECTED_ROLE_PROFILE
        or role["warhead_atoms"] != list(EXPECTED_WARHEAD)
        or role["frozen_source_warhead_atoms_source_order"] != list(EXPECTED_SOURCE_WARHEAD_ORDER)
        or set(role["warhead_atoms"]) != set(role["frozen_source_warhead_atoms_source_order"])
        or role["linker_atoms"] != []
        or role["scaffold_atoms"] != list(EXPECTED_SCAFFOLD)
        or role["boundary_bonds"] != [{"atom_id_1": "CAZ", "atom_id_2": "NAS", "bond_order": "SING", "role_1": "scaffold", "role_2": "warhead"}]
        or role["applicable_canonical_task_ids"] != [0, 3, 4]
        or role["machine_selected"] is not False
        or role["machine_recommended_candidate"] is not None
        or exact5["task_count"] != 5
        or exact5["B3_present"] is not True
        or exact5["sixth_task_present"] is not False
        or exact5["sample_applicable_task_ids"] != [0, 3, 4]
        or exact5["tasks"] != [
            {"task_id": task_id, "semantic_name": semantic, "display_alias": alias, "structurally_applicable": task_id in DIRECT_VALID_TASK_IDS}
            for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
        ]
    ):
        _fail("FORMAL_CANDIDATE4_OR_EXACT5_DRIFT")
    observed = formal["observed_graph_pre_boundary"]
    geometry = formal["geometry_boundary"]
    training = formal["training_use_human_decision"]
    if (
        observed["observed_graph_identity"] != "YUN_FROZEN_OBSERVED_POST_MICHAEL_PRODUCT_HEAVY_ATOM_GRAPH"
        or observed["observed_reactive_atom_element"] != "C"
        or observed["observed_graph_is_post_covalent_product_state"] is not True
        or observed["observed_CAO_CAN_bond_order"] != "SING"
        or observed["authoritative_PRE_precursor_topology"] is not None
        or observed["authoritative_PRE_acrylamide_bond_order_topology"] is not None
        or observed["PRE_CAO_CAN_bond_order_authority"] is not None
        or observed["PRE_CAO_CAN_double_bond_authority_created"] is not False
        or observed["PRE_reconstruction_performed"] is not False
        or observed["second_PRE_graph_created"] is not False
        or geometry["POST_geometry_training_authority_created"] is not False
        or geometry["POST_geometry_training_target_created"] is not False
        or geometry["PRE_status"] != "PRE_REACTION_UNRESOLVED"
        or geometry["PRE_geometry_authority_created"] is not False
        or geometry["PRE_geometry_training_target_created"] is not False
        or geometry["PRE_precursor_topology_authority_created"] is not False
        or geometry["PRE_zero_fill_performed"] is not False
        or geometry["POST_to_PRE_copy_performed"] is not False
        or geometry["PRE_coordinate_reconstruction_performed"] is not False
        or training["D5_human_choice"] != "INCLUDE"
        or training["human_training_excluded"] is not False
        or training["training_use_include"] is not True
        or training["future_training_admission_candidate"] is not None
        or training["future_training_admission_candidate_status"] != "DEFERRED_TO_DOWNSTREAM_INGESTION_AND_CENSUS"
        or training["formal_training_admitted"] is not False
        or training["training_admission_created"] is not False
        or training["training_materialization_performed"] is not False
        or training["tensor_target_created"] is not False
        or training["formal_split_authority_created"] is not False
        or training["runtime_model_usable"] is not False
        or training["parameter_update_authorization"] is not False
    ):
        _fail("FORMAL_OBSERVED_PRE_GEOMETRY_OR_TRAINING_BOUNDARY_INVALID")
    for field in ("reaction_family_authority", "warhead_rule_authority", "warhead_type_authority"):
        if formal[field][next(key for key in formal[field] if key.endswith("authority_created"))] is not False:
            _fail("FORMAL_AUXILIARY_AUTHORITY_INVALID:" + field)
    boundary = formal["authority_boundary"]
    prohibited_true = (
        "reaction_family_authority_created", "warhead_rule_authority_created",
        "warhead_type_authority_created", "reusable_chemistry_authority_created",
        "reusable_pair_authority_created", "reusable_role_authority_created",
        "PRE_authority_created", "POST_geometry_training_authority_created",
        "training_admission_created", "training_dataset_changed",
        "formal_split_authority_created", "runtime_admission_created",
        "tensor_integration_performed", "loader_modified", "batch_modified",
        "model_forward_executed", "auxiliary_head_executed", "loss_executed",
        "backward_executed", "optimizer_created", "optimizer_step_executed",
        "parameter_update_executed", "fine_tune_performed", "training_performed",
        "network_accessed", "scientific_network_acquisition_performed",
        "commit_performed", "push_performed", "READY_FOR_TRAINING",
    )
    if any(boundary[field] is not False for field in prohibited_true):
        _fail("FORMAL_AUTHORITY_OR_TRAINING_BOUNDARY_INVALID")
    if formal["downstream_status"] != {
        "formal_human_decision_created": True,
        "completed_decision_ingestion": "NOT_DONE",
        "global_reconciliation_update": "NOT_DONE",
        "global_census_update": "NOT_DONE",
        "training": "NOT_STARTED",
    }:
        _fail("FORMAL_DOWNSTREAM_STATUS_INVALID")
    return {
        "events": [
            _event_projection(event, EXPECTED_EVENTS[index][11])
            for index, event in enumerate(raw_events)
        ],
        "role": _role_snapshot(),
        "scientific_context": _scientific_context(),
        "observed_graph_pre_boundary": _observed_graph_pre_boundary(),
        "geometry_boundary": _geometry_boundary(),
        "training_boundary": _training_boundary(),
    }


def _semantic_owner_bindings(repo_root: Path, overrides: Mapping[Path, Path]) -> list[dict[str, object]]:
    for relative, byte_count, sha256, role in IMMUTABLE_SEMANTIC_OWNER_BINDINGS:
        _verify_payload(overrides.get(relative, repo_root / relative), byte_count, sha256, role)
    runtime = _literal_assignments(
        overrides.get(RUNTIME_SOURCE_RELATIVE, repo_root / RUNTIME_SOURCE_RELATIVE),
        ("DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",),
    )
    canonical = _literal_assignments(
        overrides.get(CANONICAL_TASK_SOURCE_RELATIVE, repo_root / CANONICAL_TASK_SOURCE_RELATIVE),
        ("EXACT3_ROLES", "CANONICAL_TASKS"),
    )
    if runtime["DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"] != EXPECTED_ROLE_PROFILE:
        _fail("DIRECT_PROFILE_RUNTIME_CONTRACT_DRIFT")
    if canonical["EXACT3_ROLES"] != ("scaffold", "linker", "warhead") or canonical["CANONICAL_TASKS"] != CANONICAL_TASKS:
        _fail("GLOBAL_CANONICAL_EXACT5_TASK_CONTRACT_DRIFT")
    return _binding_rows(IMMUTABLE_SEMANTIC_OWNER_BINDINGS, namespace="repository_relative")


def _frozen_review_bindings(repository_parent: Path, overrides: Mapping[Path, Path]) -> list[dict[str, object]]:
    for relative, byte_count, sha256, role, mode in FROZEN_REVIEW_PACKAGE_BINDINGS:
        _verify_payload(overrides.get(relative, repository_parent / relative), byte_count, sha256, role, mode)
    return [
        {
            "path": path.as_posix(), "path_namespace": "project_parent_relative",
            "byte_count": byte_count, "sha256": sha256, "sha256_scope": "file_bytes",
            "source_role": role, "mode": mode, "verification_status": "MATCHED",
        }
        for path, byte_count, sha256, role, mode in FROZEN_REVIEW_PACKAGE_BINDINGS
    ]


def _include_precedent_bindings(repo_root: Path, overrides: Mapping[Path, Path]) -> list[dict[str, object]]:
    payloads: dict[str, bytes] = {}
    for relative, byte_count, sha256, role in INCLUDE_REPOSITORY_PRECEDENT_BINDINGS:
        payloads[role] = _verify_payload(overrides.get(relative, repo_root / relative), byte_count, sha256, role)
    for relative, byte_count, sha256, role in INCLUDE_PARENT_PRECEDENT_BINDINGS:
        payloads[role] = _verify_payload(overrides.get(relative, repo_root.parent / relative), byte_count, sha256, role)
    try:
        ffq_rows = list(csv.DictReader(io.StringIO(payloads["FFQ_INCLUDE_PUBLISHED_MATRIX_PRECEDENT"].decode("utf-8"))))
        poa = json.loads(payloads["POA_INCLUDE_FORMAL_PRECEDENT"])
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise YUNIngestionSafetyError("INCLUDE_PRECEDENT_PARSE_FAILED") from error
    included = [row for row in ffq_rows if row.get("formal_event_training_use_decision") == "INCLUDE"]
    if len(included) != 4 or any(
        row.get("training_use_allowed") != "true"
        or row.get("candidate_for_future_training_admission") != "true"
        or row.get("future_training_admission_status") != FUTURE_STATUS
        or row.get("training_admitted") != "false"
        or row.get("training_materialization_allowed_now") != "false"
        or row.get("current_runtime_model_usable") != "false"
        for row in included
    ):
        _fail("FFQ_INCLUDE_SEMANTIC_PRECEDENT_INVALID")
    poa_include = [
        row for row in poa.get("subgroup_human_decisions", [])
        if row.get("event_training_use_decision") == "INCLUDE"
    ]
    if (
        len(poa_include) != 1
        or poa_include[0].get("training_admission_created") is not False
        or poa.get("authority_boundary", {}).get("training_admission_created") is not False
        or poa.get("authority_boundary", {}).get("ready_for_training") is not False
    ):
        _fail("POA_INCLUDE_SEMANTIC_PRECEDENT_INVALID")
    return [
        *_binding_rows(INCLUDE_REPOSITORY_PRECEDENT_BINDINGS, namespace="repository_relative"),
        *_binding_rows(INCLUDE_PARENT_PRECEDENT_BINDINGS, namespace="repository_parent_relative"),
    ]


def _current_census_bindings(repo_root: Path, overrides: Mapping[Path, Path]) -> list[dict[str, object]]:
    payloads: dict[Path, bytes] = {}
    for relative, byte_count, sha256, role in CURRENT_CENSUS_BINDINGS:
        payloads[relative] = _verify_payload(overrides.get(relative, repo_root / relative), byte_count, sha256, role)
    csv_relative = CURRENT_CENSUS_BINDINGS[1][0]
    summary_relative = CURRENT_CENSUS_BINDINGS[2][0]
    try:
        rows = list(csv.DictReader(io.StringIO(payloads[csv_relative].decode("utf-8"))))
        summary = json.loads(payloads[summary_relative])
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise YUNIngestionSafetyError("CURRENT_CENSUS_PARSE_FAILED") from error
    boundary = summary.get("authority_boundary", {})
    training = summary.get("training_stage", {})
    if (
        summary.get("schema_version") != "covapie_cumulative1000_current_global_readiness_census_with_1f8_v1"
        or summary.get("chemistry", {}).get("POSITIVE", {}).get("count") != 82
        or training.get("future_training_admission_candidate_count") != 12
        or training.get("training_use_include_count") != 29
        or boundary.get("next_priority_review_ligand") != "YUN"
        or boundary.get("next_priority_review_event_count") != 7
        or boundary.get("next_priority_review_unit") != EXPECTED_REVIEW_UNIT_ID
    ):
        _fail("CURRENT_CENSUS_SUMMARY_BOUNDARY_INVALID")
    yun = [row for row in rows if row.get("ligand_component_id") == "YUN"]
    if (
        len(yun) != 7
        or tuple(row.get("canonical_event_id") for row in yun) != EXPECTED_EVENT_IDS
        or [int(row["scaleup_rank"]) for row in yun] != list(EXPECTED_RANKS)
        or any(
            row.get("current_global_status") != "CURRENTLY_UNREVIEWED"
            or row.get("current_review_status") != "CURRENTLY_UNREVIEWED"
            or row.get("chemistry_disposition") != "UNRESOLVED"
            for row in yun
        )
    ):
        _fail("CURRENT_CENSUS_YUN_PRIOR_STATE_INVALID")
    return _binding_rows(CURRENT_CENSUS_BINDINGS, namespace="repository_relative")


def load_frozen_formal_decision_v1(
    repo_root: Path,
    *,
    formal_decision_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]:
    """Load and strictly validate the formal decision and every used source."""

    repo_root = repo_root.resolve()
    overrides = repository_path_overrides or {}
    formal_path = (
        formal_decision_path.resolve()
        if formal_decision_path is not None
        else repo_root.parent / FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT
    )
    payload = _verify_payload(
        formal_path, FORMAL_DECISION_BYTE_COUNT, FORMAL_DECISION_SHA256,
        "formal_YUN_human_decision",
    )
    try:
        formal = json.loads(payload)
    except json.JSONDecodeError as error:
        raise YUNIngestionSafetyError("FORMAL_DECISION_JSON_INVALID") from error
    normalized = _validate_formal_decision_v1(formal)
    return {
        "formal": formal,
        "normalized": normalized,
        "formal_decision_binding": _formal_binding(),
        "frozen_review_package_bindings": _frozen_review_bindings(repo_root.parent, overrides),
        "immutable_semantic_owner_bindings": _semantic_owner_bindings(repo_root, overrides),
        "include_semantic_precedent_bindings": _include_precedent_bindings(repo_root, overrides),
        "current_published_census_bindings": _current_census_bindings(repo_root, overrides),
    }


def _snapshot(bound: Mapping[str, Any]) -> dict[str, object]:
    normalized = bound["normalized"]
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "snapshot_role": "ADDITIVE_IMMUTABLE_YUN_COMPLETED_HUMAN_DECISION_INGESTION",
        "snapshot_created_by_ingestion": True,
        "human_authority_ingested": True,
        "human_authority_created_by_ingestion": False,
        "formal_decision_binding": bound["formal_decision_binding"],
        "frozen_exact6_evidence_provenance": bound["frozen_review_package_bindings"],
        "include_semantic_precedent": {
            "FFQ_INCLUDE_precedent_verified": True,
            "POA_INCLUDE_precedent_verified": True,
            "adopted_separation": _training_boundary(),
        },
        "reviewer_id": "fmx",
        "attestor_id": "fmx",
        "approved_at_utc": EXPECTED_APPROVED_AT_UTC,
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "ligand_component_id": "YUN",
        "event_count": 7,
        "events": normalized["events"],
        "unit_level_D1_D6": {
            "D1": "RELEVANT", "D2": "POSITIVE", "D3": "CONFIRM_OBSERVED_PAIR",
            "D4": "SELECT_CANDIDATE_4", "D5": "INCLUDE", "D6": EXPECTED_D6,
        },
        "reactive_pair": {
            "human_decision_available": True,
            "human_authoritative": True,
            "authoritative_event_count": 7,
            "protein_reactive_atom": "SG",
            "ligand_reactive_atom": "CAN",
            "ligand_reactive_atom_element": "C",
            "PDB_specific_pairs": {"4LL0": "CYS797_SG_TO_YUN_CAN", "4LRM": "CYS800_SG_TO_YUN_CAN"},
            "model_bound_pair_target_created_by_ingestion": False,
            "tensor_target_created": False,
            "reusable_reactive_pair_authority": False,
        },
        "selected_role_partition": normalized["role"],
        "canonical_task_contract": _canonical_task_contract(),
        "scientific_context": normalized["scientific_context"],
        "observed_graph_PRE_boundary": normalized["observed_graph_pre_boundary"],
        "geometry_boundary": normalized["geometry_boundary"],
        "training_boundary": normalized["training_boundary"],
        "auxiliary_and_reusable_boundary": _reusable_boundary(),
        "current_published_global_boundary": {
            "published_global_positive_count_remains": 82,
            "published_training_include_count_remains": 29,
            "published_future_training_admission_candidate_count_remains": 12,
            "current_published_YUN_status": "CURRENTLY_UNREVIEWED",
            "global_reconciliation_update": "NOT_DONE",
            "global_census_update": "NOT_DONE",
        },
        "expected_future_census_derivation_informational_only": {
            "requires_future_YUN_reconciliation_and_census_refresh": True,
            "chemistry_positive_expected": 89,
            "task_relevant_expected": 90,
            "training_INCLUDE_expected": 36,
            "training_EXCLUDE_expected": 53,
            "sample_pair_expected": 89,
            "sample_role_expected": 89,
            "DIRECT_expected": 50,
            "STRICT_expected": 39,
            "future_admission_candidates_expected": 19,
            "materialized_as_current_global_state": False,
        },
        "downstream_non_actions": {
            "YUN_reconciliation": "NOT_DONE_THIS_STEP",
            "global_census_refresh": "NOT_DONE_THIS_STEP",
            "training_preparation": "NOT_DONE_THIS_STEP",
            "feature_semantics_audit": "NOT_DONE_THIS_STEP",
            "tensor_model_training": "NOT_DONE_THIS_STEP",
        },
        "authority_boundary": _authority_boundary(),
    }


MATRIX_HEADER = (
    "canonical_event_id", "scaleup_rank", "pdb_id", "model_number",
    "protein_chain_or_asym", "cys_residue_id", "protein_altloc",
    "ligand_component_id", "ligand_chain_or_asym", "ligand_altloc",
    "selected_connection_id", "POST_distance_angstrom",
    "human_task_relevance_decision", "chemistry_known_positive",
    "negative_chemistry", "task_domain_negative",
    "reactive_pair_human_decision_available", "reactive_pair_human_authoritative",
    "protein_reactive_atom", "ligand_reactive_atom", "ligand_reactive_atom_element",
    "role_partition_human_decision_available", "role_partition_human_authoritative",
    "selected_role_candidate_index_0based", "role_profile", "warhead_atoms_json",
    "linker_atoms_json", "scaffold_atoms_json", "boundary_bonds_json",
    "global_canonical_task_count", "canonical_task_applicability_json",
    "direct_profile_applicable_task_ids_json", "formal_event_training_use_decision",
    "event_training_use_human_decision_available", "training_use_allowed",
    "human_training_excluded", "candidate_for_future_training_admission",
    "future_training_admission_status", "training_admitted",
    "training_materialization_allowed_now", "current_runtime_model_usable",
    "observed_post_product_state", "observed_CAO_CAN_bond_order",
    "PRE_CAO_CAN_bond_order_authority_available", "POST_source_evidence_available",
    "POST_geometry_source_evidence_status", "POST_geometry_training_label_available_now",
    "PRE_geometry_authority_available", "PRE_geometry_training_label_available_now",
    "PRE_precursor_topology_authority_available", "reaction_family_target_available",
    "warhead_rule_target_available", "warhead_type_target_available",
    "reusable_chemistry_authority_available", "reusable_pair_authority_available",
    "reusable_role_authority_available", "future_training_candidate_derived_by_ingestion",
    "future_training_candidate_is_training_admission", "authority_source",
    "authority_scope", "authority_ingested", "authority_created_by_this_ingestion",
)


def _matrix_rows(snapshot: Mapping[str, Any]) -> list[dict[str, object]]:
    role = _role_snapshot()
    applicability = _canonical_task_contract()["direct_profile_task_applicability"]
    rows: list[dict[str, object]] = []
    for event in snapshot["events"]:
        rows.append(
            {
                "canonical_event_id": event["canonical_event_id"],
                "scaleup_rank": str(event["scaleup_rank"]),
                "pdb_id": event["pdb_id"],
                "model_number": str(event["model_number"]),
                "protein_chain_or_asym": event["protein_chain_or_asym"],
                "cys_residue_id": event["cys_residue_id"],
                "protein_altloc": "" if event["protein_altloc"] is None else event["protein_altloc"],
                "ligand_component_id": "YUN",
                "ligand_chain_or_asym": event["ligand_chain_or_asym"],
                "ligand_altloc": "" if event["ligand_altloc"] is None else event["ligand_altloc"],
                "selected_connection_id": event["selected_connection_id"],
                "POST_distance_angstrom": event["POST_distance_frozen_lexeme"],
                "human_task_relevance_decision": "RELEVANT",
                "chemistry_known_positive": "true",
                "negative_chemistry": "false",
                "task_domain_negative": "false",
                "reactive_pair_human_decision_available": "true",
                "reactive_pair_human_authoritative": "true",
                "protein_reactive_atom": "SG",
                "ligand_reactive_atom": "CAN",
                "ligand_reactive_atom_element": "C",
                "role_partition_human_decision_available": "true",
                "role_partition_human_authoritative": "true",
                "selected_role_candidate_index_0based": "4",
                "role_profile": EXPECTED_ROLE_PROFILE,
                "warhead_atoms_json": _json_cell(list(EXPECTED_WARHEAD)),
                "linker_atoms_json": "[]",
                "scaffold_atoms_json": _json_cell(list(EXPECTED_SCAFFOLD)),
                "boundary_bonds_json": _json_cell(role["boundary_bonds"]),
                "global_canonical_task_count": "5",
                "canonical_task_applicability_json": _json_cell(applicability),
                "direct_profile_applicable_task_ids_json": "[0,3,4]",
                "formal_event_training_use_decision": "INCLUDE",
                "event_training_use_human_decision_available": "true",
                "training_use_allowed": "true",
                "human_training_excluded": "false",
                "candidate_for_future_training_admission": "true",
                "future_training_admission_status": FUTURE_STATUS,
                "training_admitted": "false",
                "training_materialization_allowed_now": "false",
                "current_runtime_model_usable": "false",
                "observed_post_product_state": "true",
                "observed_CAO_CAN_bond_order": "SING",
                "PRE_CAO_CAN_bond_order_authority_available": "false",
                "POST_source_evidence_available": "true",
                "POST_geometry_source_evidence_status": POST_SOURCE_STATUS,
                "POST_geometry_training_label_available_now": "false",
                "PRE_geometry_authority_available": "false",
                "PRE_geometry_training_label_available_now": "false",
                "PRE_precursor_topology_authority_available": "false",
                "reaction_family_target_available": "false",
                "warhead_rule_target_available": "false",
                "warhead_type_target_available": "false",
                "reusable_chemistry_authority_available": "false",
                "reusable_pair_authority_available": "false",
                "reusable_role_authority_available": "false",
                "future_training_candidate_derived_by_ingestion": "true",
                "future_training_candidate_is_training_admission": "false",
                "authority_source": AUTHORITY_SOURCE,
                "authority_scope": AUTHORITY_SCOPE,
                "authority_ingested": "true",
                "authority_created_by_this_ingestion": "false",
            }
        )
    return rows


def _summary() -> dict[str, object]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "event_count": 7,
        "task_relevant_count": 7,
        "chemistry_positive_count": 7,
        "YUN_source_local_positive_count": 7,
        "source_local_positive_count": 7,
        "completed_human_positive_count": 7,
        "reactive_pair_human_authority_count": 7,
        "role_partition_human_authority_count": 7,
        "direct_profile_count": 7,
        "strict_profile_count": 0,
        "human_training_INCLUDE_count": 7,
        "human_training_EXCLUDE_count": 0,
        "training_use_allowed_count": 7,
        "future_training_admission_candidate_count": 7,
        "future_training_admission_status": FUTURE_STATUS,
        "future_training_candidate_derived_by_ingestion": True,
        "training_admitted_count": 0,
        "formal_training_admitted_count": 0,
        "training_materialization_allowed_count": 0,
        "current_runtime_model_usable_count": 0,
        "POST_source_evidence_count": 7,
        "POST_geometry_training_authority_count": 0,
        "POST_geometry_training_label_available_now": False,
        "PRE_geometry_authority_count": 0,
        "PRE_geometry_training_target_count": 0,
        "PRE_precursor_topology_authority_count": 0,
        "PRE_acrylamide_bond_order_authority_count": 0,
        "PRE_CAO_CAN_bond_order_authority_count": 0,
        "PRE_reconstruction_count": 0,
        "reaction_family_target_count": 0,
        "warhead_rule_target_count": 0,
        "warhead_type_target_count": 0,
        "reusable_chemistry_authority_available": False,
        "reusable_pair_authority_available": False,
        "reusable_role_authority_available": False,
        "global_canonical_task_count": 5,
        "direct_profile_applicable_task_count_per_event": 3,
        "formal_human_decision_ingested": True,
        "human_authority_created_by_ingestion": False,
        "completed_decision_ingestion_status": "DONE_THIS_STEP",
        "published_global_positive_count_remains": 82,
        "published_training_include_count_remains": 29,
        "published_future_training_admission_candidate_count_remains": 12,
        "current_published_YUN_status": "CURRENTLY_UNREVIEWED",
        "global_reconciliation_update_status": "NOT_DONE_THIS_STEP",
        "global_census_update_status": "NOT_DONE_THIS_STEP",
        "expected_future_census_derivation_informational_only": {
            "chemistry_positive": 89, "task_relevant": 90, "training_INCLUDE": 36,
            "training_EXCLUDE": 53, "sample_pair": 89, "sample_role": 89,
            "DIRECT": 50, "STRICT": 39, "future_candidates": 19,
        },
        "feature_semantics": "AUDIT_REQUIRED_LATER",
        "step12d_status": "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
        "ready_for_YUN_reconciliation_successor": True,
        "ready_for_training": False,
        "authority_boundary": _authority_boundary(),
    }


def _validate_text_payload(label: str, payload: bytes) -> None:
    if (
        type(payload) is not bytes
        or payload.startswith(b"\xef\xbb\xbf")
        or b"\x00" in payload
        or b"\r" in payload
        or not payload.endswith(b"\n")
        or payload.endswith(b"\n\n")
    ):
        _fail("TEXT_INVARIANT_INVALID:" + label)
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise YUNIngestionSafetyError("UTF8_INVALID:" + label) from error
    if any(line.endswith((" ", "\t")) for line in text.splitlines()):
        _fail("TRAILING_WHITESPACE_INVALID:" + label)


def _candidate_source_bindings(repo_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for relative, role in (
        (SOURCE_RELATIVE, "production_owner"),
        (CHECKER_RELATIVE, "fail_closed_checker"),
        (TEST_RELATIVE, "targeted_test_contract"),
    ):
        path = repo_root / relative
        if not path.is_file() or path.is_symlink():
            _fail("CANDIDATE_SOURCE_NOT_REGULAR:" + relative.as_posix())
        payload = path.read_bytes()
        _validate_text_payload(relative.as_posix(), payload)
        rows.append(
            {
                "path": relative.as_posix(), "path_namespace": "repository_relative",
                "byte_count": len(payload), "sha256": _sha(payload),
                "sha256_scope": "file_bytes", "source_role": role,
            }
        )
    return rows


def _expected_review_bindings() -> list[dict[str, object]]:
    return [
        {
            "path": path.as_posix(), "path_namespace": "project_parent_relative",
            "byte_count": count, "sha256": digest, "sha256_scope": "file_bytes",
            "source_role": role, "mode": mode, "verification_status": "MATCHED",
        }
        for path, count, digest, role, mode in FROZEN_REVIEW_PACKAGE_BINDINGS
    ]


def _expected_include_bindings() -> list[dict[str, object]]:
    return [
        *_binding_rows(INCLUDE_REPOSITORY_PRECEDENT_BINDINGS, namespace="repository_relative"),
        *_binding_rows(INCLUDE_PARENT_PRECEDENT_BINDINGS, namespace="repository_parent_relative"),
    ]


def _expected_owner_bindings() -> list[dict[str, object]]:
    return _binding_rows(IMMUTABLE_SEMANTIC_OWNER_BINDINGS, namespace="repository_relative")


def _expected_census_bindings() -> list[dict[str, object]]:
    return _binding_rows(CURRENT_CENSUS_BINDINGS, namespace="repository_relative")


def _standalone_bound() -> dict[str, object]:
    return {
        "formal_decision_binding": _formal_binding(),
        "frozen_review_package_bindings": _expected_review_bindings(),
        "normalized": {
            "events": [
                _event_projection(_expected_raw_event(row), row[11])
                for row in EXPECTED_EVENTS
            ],
            "role": _role_snapshot(),
            "scientific_context": _scientific_context(),
            "observed_graph_pre_boundary": _observed_graph_pre_boundary(),
            "geometry_boundary": _geometry_boundary(),
            "training_boundary": _training_boundary(),
        },
    }


def _build_artifacts_unvalidated(
    repo_root: Path,
    *,
    formal_decision_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, bytes]:
    bound = load_frozen_formal_decision_v1(
        repo_root,
        formal_decision_path=formal_decision_path,
        repository_path_overrides=repository_path_overrides,
    )
    snapshot = _snapshot(bound)
    snapshot_payload = _json_bytes(snapshot)
    matrix_payload = _csv_bytes(MATRIX_HEADER, _matrix_rows(snapshot))
    summary_payload = _json_bytes(_summary())
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "artifact_role": "YUN_COMPLETED_DECISION_AND_EVENT_TASK_LABEL_AVAILABILITY_NOT_ADMISSION",
        "candidate_publication_file_count": 7,
        "output_artifact_count": 4,
        "source_path": SOURCE_RELATIVE.as_posix(),
        "checker_path": CHECKER_RELATIVE.as_posix(),
        "test_path": TEST_RELATIVE.as_posix(),
        "output_paths": [path.as_posix() for path in OUTPUT_RELATIVE_PATHS],
        "formal_decision_binding": bound["formal_decision_binding"],
        "frozen_formal_evidence_provenance": bound["frozen_review_package_bindings"],
        "include_semantic_precedent_bindings": bound["include_semantic_precedent_bindings"],
        "immutable_semantic_owner_bindings": bound["immutable_semantic_owner_bindings"],
        "current_published_census_bindings": bound["current_published_census_bindings"],
        "current_published_census_boundary": {
            "published_global_positive_count_remains": 82,
            "published_training_include_count_remains": 29,
            "published_future_training_admission_candidate_count_remains": 12,
            "current_next_priority_review_ligand": "YUN",
            "current_next_priority_review_event_count": 7,
            "current_YUN_review_status": "CURRENTLY_UNREVIEWED",
            "global_reconciliation_update_status": "NOT_DONE_THIS_STEP",
            "global_census_update_status": "NOT_DONE_THIS_STEP",
        },
        "candidate_source_bindings": _candidate_source_bindings(repo_root),
        "canonical_task_contract": _canonical_task_contract(),
        "counts": {
            key: value for key, value in _summary().items()
            if type(value) is int and type(value) is not bool
        },
        "human_authority_ingestion_semantics": {
            "authority_source": AUTHORITY_SOURCE,
            "authority_scope": AUTHORITY_SCOPE,
            "authority_ingested": True,
            "authority_created_by_ingestion": False,
            "future_training_candidate_derived_by_ingestion": True,
            "future_training_candidate_is_training_admission": False,
        },
        "output_artifact_bindings": {
            SNAPSHOT: {"sha256": _sha(snapshot_payload)},
            MATRIX: {"sha256": _sha(matrix_payload)},
            SUMMARY: {"sha256": _sha(summary_payload)},
        },
        "manifest_self_sha256_recorded": False,
        "manifest_self_sha256_policy": "SELF_SHA256_PROHIBITED",
        "deterministic": True,
        "completed_decision_ingestion_status": "DONE_THIS_STEP",
        "global_reconciliation_update_status": "NOT_DONE_THIS_STEP",
        "global_census_update_status": "NOT_DONE_THIS_STEP",
        "published_global_positive_count_remains": 82,
        "expected_future_census_derivation_materialized": False,
        "feature_semantics_audit_required_before_formal_training": True,
        "step12d_is_only_smoke_legality_not_final_training_feature_contract": True,
        "ready_for_YUN_reconciliation_successor": True,
        "ready_for_training": False,
        "authority_boundary": _authority_boundary(),
    }
    return {
        SNAPSHOT: snapshot_payload,
        MATRIX: matrix_payload,
        SUMMARY: summary_payload,
        MANIFEST: _json_bytes(manifest),
    }


def build_artifacts_v1(
    repo_root: Path,
    *,
    formal_decision_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, bytes]:
    """Build the deterministic Exact4 source projection in memory."""

    artifacts = _build_artifacts_unvalidated(
        repo_root.resolve(),
        formal_decision_path=formal_decision_path,
        repository_path_overrides=repository_path_overrides,
    )
    validate_completed_decision_projection_v1(artifacts, repo_root=repo_root)
    return artifacts


def _reject_dynamic_metadata(value: object) -> None:
    forbidden = {
        "generated_at", "generated_at_utc", "ingested_at", "ingested_at_utc",
        "hostname", "host_name", "pid", "process_id", "uuid", "git_head",
        "git_parent", "commit_subject", "origin_main", "ahead", "behind",
        "candidate_lifecycle_profile", "published_lifecycle_profile",
    }
    if type(value) is dict:
        for key, child in value.items():
            if key in forbidden:
                _fail("DYNAMIC_OR_LIFECYCLE_METADATA_FORBIDDEN:" + key)
            _reject_dynamic_metadata(child)
    elif type(value) is list:
        for child in value:
            _reject_dynamic_metadata(child)


def _validate_candidate_bindings_shape(value: object) -> None:
    if type(value) is not list or len(value) != 3:
        _fail("MANIFEST_CANDIDATE_SOURCE_BINDING_COUNT_INVALID")
    expected = (
        (SOURCE_RELATIVE.as_posix(), "production_owner"),
        (CHECKER_RELATIVE.as_posix(), "fail_closed_checker"),
        (TEST_RELATIVE.as_posix(), "targeted_test_contract"),
    )
    for observed, (path, role) in zip(value, expected, strict=True):
        if type(observed) is not dict or set(observed) != {
            "path", "path_namespace", "byte_count", "sha256", "sha256_scope", "source_role",
        }:
            _fail("MANIFEST_CANDIDATE_SOURCE_BINDING_SCHEMA_INVALID")
        if (
            observed["path"] != path
            or observed["path_namespace"] != "repository_relative"
            or type(observed["byte_count"]) is not int
            or observed["byte_count"] <= 0
            or type(observed["sha256"]) is not str
            or len(observed["sha256"]) != 64
            or any(character not in "0123456789abcdef" for character in observed["sha256"])
            or observed["sha256_scope"] != "file_bytes"
            or observed["source_role"] != role
        ):
            _fail("MANIFEST_CANDIDATE_SOURCE_BINDING_INVALID:" + path)


def _validate_derived_projection_digests(artifacts: Mapping[str, bytes]) -> None:
    for name, digest in (
        (SNAPSHOT, _EXPECTED_SNAPSHOT_SHA256_V1),
        (MATRIX, _EXPECTED_MATRIX_SHA256_V1),
        (SUMMARY, _EXPECTED_SUMMARY_SHA256_V1),
    ):
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest) or digest == "0" * 64:
            _fail("DERIVED_PROJECTION_CONTRACT_DIGEST_NOT_FROZEN:" + name)
        if _sha(artifacts[name]) != digest:
            _fail(name.upper() + "_EXACT_PROJECTION_SHA256_INVALID")


def validate_completed_decision_projection_v1(
    artifacts: Mapping[str, bytes], *, repo_root: Path | None = None
) -> None:
    """Validate Exact4 evidence and close standalone coordinated drift."""

    if tuple(artifacts) != OUTPUT_FILENAMES:
        _fail("OUTPUT_ARTIFACT_EXACT4_INVALID")
    for name, payload in artifacts.items():
        _validate_text_payload(name, payload)
    try:
        snapshot = json.loads(artifacts[SNAPSHOT])
        matrix = list(csv.DictReader(io.StringIO(artifacts[MATRIX].decode("utf-8"))))
        summary = json.loads(artifacts[SUMMARY])
        manifest = json.loads(artifacts[MANIFEST])
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise YUNIngestionSafetyError("OUTPUT_PARSE_FAILED") from error
    for document in (snapshot, summary, manifest):
        _reject_dynamic_metadata(document)
    if snapshot != _snapshot(_standalone_bound()):
        _fail("SNAPSHOT_EXACT_SOURCE_PROJECTION_INVALID")
    if summary != _summary():
        _fail("SUMMARY_EXACT_COUNTS_OR_BOUNDARY_INVALID")
    if (list(matrix[0]) if matrix else []) != list(MATRIX_HEADER):
        _fail("MATRIX_HEADER_INVALID")
    if artifacts[MATRIX] != _csv_bytes(MATRIX_HEADER, _matrix_rows(snapshot)):
        _fail("MATRIX_DIRECT_EVIDENCE_INVALID")
    if (
        len(matrix) != 7
        or tuple(row["canonical_event_id"] for row in matrix) != EXPECTED_EVENT_IDS
        or len({row["canonical_event_id"] for row in matrix}) != 7
        or [int(row["scaleup_rank"]) for row in matrix] != list(EXPECTED_RANKS)
    ):
        _fail("MATRIX_EXACT7_INVALID")
    required_true = (
        "chemistry_known_positive", "reactive_pair_human_decision_available",
        "reactive_pair_human_authoritative", "role_partition_human_decision_available",
        "role_partition_human_authoritative", "event_training_use_human_decision_available",
        "training_use_allowed", "candidate_for_future_training_admission",
        "observed_post_product_state", "POST_source_evidence_available",
        "future_training_candidate_derived_by_ingestion", "authority_ingested",
    )
    required_false = (
        "negative_chemistry", "task_domain_negative", "human_training_excluded",
        "training_admitted", "training_materialization_allowed_now",
        "current_runtime_model_usable", "PRE_CAO_CAN_bond_order_authority_available",
        "POST_geometry_training_label_available_now", "PRE_geometry_authority_available",
        "PRE_geometry_training_label_available_now", "PRE_precursor_topology_authority_available",
        "reaction_family_target_available", "warhead_rule_target_available",
        "warhead_type_target_available", "reusable_chemistry_authority_available",
        "reusable_pair_authority_available", "reusable_role_authority_available",
        "future_training_candidate_is_training_admission", "authority_created_by_this_ingestion",
    )
    for index, row in enumerate(matrix):
        if any(row[field] != "true" for field in required_true):
            _fail("MATRIX_REQUIRED_TRUE_FLAG_INVALID")
        if any(row[field] != "false" for field in required_false):
            _fail("MATRIX_REQUIRED_FALSE_FLAG_INVALID")
        applicability = json.loads(row["canonical_task_applicability_json"])
        if (
            row["cys_residue_id"] != EXPECTED_EVENTS[index][5]
            or row["protein_reactive_atom"] != "SG"
            or row["ligand_reactive_atom"] != "CAN"
            or row["ligand_reactive_atom_element"] != "C"
            or row["selected_role_candidate_index_0based"] != "4"
            or row["role_profile"] != EXPECTED_ROLE_PROFILE
            or row["direct_profile_applicable_task_ids_json"] != "[0,3,4]"
            or row["formal_event_training_use_decision"] != "INCLUDE"
            or row["future_training_admission_status"] != FUTURE_STATUS
            or row["observed_CAO_CAN_bond_order"] != "SING"
            or row["POST_geometry_source_evidence_status"] != POST_SOURCE_STATUS
            or len(applicability) != 5
            or [x["task_id"] for x in applicability if x["structurally_applicable"]] != [0, 3, 4]
            or applicability[3]["semantic_long_name"] != "scaffold_only"
        ):
            _fail("MATRIX_PROVENANCE_CANDIDATE4_INCLUDE_OR_EXACT5_INVALID")
    expected_manifest_keys = {
        "schema_version", "stage", "artifact_role", "candidate_publication_file_count",
        "output_artifact_count", "source_path", "checker_path", "test_path", "output_paths",
        "formal_decision_binding", "frozen_formal_evidence_provenance",
        "include_semantic_precedent_bindings", "immutable_semantic_owner_bindings",
        "current_published_census_bindings", "current_published_census_boundary",
        "candidate_source_bindings", "canonical_task_contract", "counts",
        "human_authority_ingestion_semantics", "output_artifact_bindings",
        "manifest_self_sha256_recorded", "manifest_self_sha256_policy", "deterministic",
        "completed_decision_ingestion_status", "global_reconciliation_update_status",
        "global_census_update_status", "published_global_positive_count_remains",
        "expected_future_census_derivation_materialized",
        "feature_semantics_audit_required_before_formal_training",
        "step12d_is_only_smoke_legality_not_final_training_feature_contract",
        "ready_for_YUN_reconciliation_successor", "ready_for_training", "authority_boundary",
    }
    if type(manifest) is not dict or set(manifest) != expected_manifest_keys:
        _fail("MANIFEST_SCHEMA_INVALID")
    if (
        manifest["schema_version"] != MANIFEST_SCHEMA_VERSION
        or manifest["stage"] != SCHEMA_VERSION
        or manifest["artifact_role"] != "YUN_COMPLETED_DECISION_AND_EVENT_TASK_LABEL_AVAILABILITY_NOT_ADMISSION"
        or manifest["candidate_publication_file_count"] != 7
        or manifest["output_artifact_count"] != 4
        or manifest["source_path"] != SOURCE_RELATIVE.as_posix()
        or manifest["checker_path"] != CHECKER_RELATIVE.as_posix()
        or manifest["test_path"] != TEST_RELATIVE.as_posix()
        or manifest["output_paths"] != [path.as_posix() for path in OUTPUT_RELATIVE_PATHS]
        or manifest["formal_decision_binding"] != _formal_binding()
        or manifest["frozen_formal_evidence_provenance"] != _expected_review_bindings()
        or manifest["include_semantic_precedent_bindings"] != _expected_include_bindings()
        or manifest["immutable_semantic_owner_bindings"] != _expected_owner_bindings()
        or manifest["current_published_census_bindings"] != _expected_census_bindings()
        or manifest["canonical_task_contract"] != _canonical_task_contract()
        or manifest["authority_boundary"] != _authority_boundary()
        or manifest["manifest_self_sha256_recorded"] is not False
        or manifest["manifest_self_sha256_policy"] != "SELF_SHA256_PROHIBITED"
        or manifest["deterministic"] is not True
        or manifest["completed_decision_ingestion_status"] != "DONE_THIS_STEP"
        or manifest["global_reconciliation_update_status"] != "NOT_DONE_THIS_STEP"
        or manifest["global_census_update_status"] != "NOT_DONE_THIS_STEP"
        or manifest["published_global_positive_count_remains"] != 82
        or manifest["expected_future_census_derivation_materialized"] is not False
        or manifest["feature_semantics_audit_required_before_formal_training"] is not True
        or manifest["step12d_is_only_smoke_legality_not_final_training_feature_contract"] is not True
        or manifest["ready_for_YUN_reconciliation_successor"] is not True
        or manifest["ready_for_training"] is not False
    ):
        _fail("MANIFEST_BOUNDARY_OR_SOURCE_BINDING_INVALID")
    if manifest["current_published_census_boundary"] != {
        "published_global_positive_count_remains": 82,
        "published_training_include_count_remains": 29,
        "published_future_training_admission_candidate_count_remains": 12,
        "current_next_priority_review_ligand": "YUN",
        "current_next_priority_review_event_count": 7,
        "current_YUN_review_status": "CURRENTLY_UNREVIEWED",
        "global_reconciliation_update_status": "NOT_DONE_THIS_STEP",
        "global_census_update_status": "NOT_DONE_THIS_STEP",
    }:
        _fail("MANIFEST_CURRENT_CENSUS_BOUNDARY_INVALID")
    _validate_candidate_bindings_shape(manifest["candidate_source_bindings"])
    if manifest["output_artifact_bindings"] != {
        SNAPSHOT: {"sha256": _sha(artifacts[SNAPSHOT])},
        MATRIX: {"sha256": _sha(artifacts[MATRIX])},
        SUMMARY: {"sha256": _sha(artifacts[SUMMARY])},
    }:
        _fail("MANIFEST_OUTPUT_BINDINGS_INVALID")
    if manifest["counts"] != {
        key: value for key, value in _summary().items()
        if type(value) is int and type(value) is not bool
    }:
        _fail("MANIFEST_COUNTS_INVALID")
    if manifest["human_authority_ingestion_semantics"] != {
        "authority_source": AUTHORITY_SOURCE,
        "authority_scope": AUTHORITY_SCOPE,
        "authority_ingested": True,
        "authority_created_by_ingestion": False,
        "future_training_candidate_derived_by_ingestion": True,
        "future_training_candidate_is_training_admission": False,
    }:
        _fail("MANIFEST_HUMAN_AUTHORITY_BOUNDARY_INVALID")
    _validate_derived_projection_digests(artifacts)
    if repo_root is not None:
        repo_root = repo_root.resolve()
        bound = load_frozen_formal_decision_v1(repo_root)
        if snapshot != _snapshot(bound):
            _fail("SNAPSHOT_DIRECT_FORMAL_SOURCE_PROJECTION_INVALID")
        if manifest["candidate_source_bindings"] != _candidate_source_bindings(repo_root):
            _fail("MANIFEST_CANDIDATE_SOURCE_BINDINGS_INVALID")


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def materialize_artifacts_v1(repo_root: Path, *, output_root: Path | None = None) -> dict[str, bytes]:
    """Build and atomically materialize only the Exact4 outputs."""

    repo_root = repo_root.resolve()
    artifacts = build_artifacts_v1(repo_root)
    destination = output_root.resolve() if output_root is not None else repo_root / OUTPUT_ROOT_RELATIVE
    if destination.exists():
        unexpected = {path.name for path in destination.iterdir() if path.name not in OUTPUT_FILENAMES}
        if unexpected:
            _fail("OUTPUT_DIRECTORY_CONTAINS_UNEXPECTED_FILES")
    for name in OUTPUT_FILENAMES:
        _atomic_write(destination / name, artifacts[name])
    return artifacts


def check_materialized_v1(repo_root: Path) -> dict[str, object]:
    repo_root = repo_root.resolve()
    expected = build_artifacts_v1(repo_root)
    output_root = repo_root / OUTPUT_ROOT_RELATIVE
    if not output_root.is_dir() or output_root.is_symlink():
        _fail("OUTPUT_DIRECTORY_MISSING_OR_INVALID")
    if {path.name for path in output_root.iterdir()} != set(OUTPUT_FILENAMES):
        _fail("MATERIALIZED_OUTPUT_EXACT4_INVALID")
    observed: dict[str, bytes] = {}
    for name in OUTPUT_FILENAMES:
        path = output_root / name
        if not path.is_file() or path.is_symlink():
            _fail("MATERIALIZED_OUTPUT_NOT_REGULAR:" + name)
        observed[name] = path.read_bytes()
        if observed[name] != expected[name]:
            _fail("MATERIALIZED_OUTPUT_BYTES_MISMATCH:" + name)
    validate_completed_decision_projection_v1(observed, repo_root=repo_root)
    return {
        "materialized_output_valid": True,
        "output_artifact_count": 4,
        "candidate_publication_file_count": 7,
        "artifact_sha256": {name: _sha(observed[name]) for name in OUTPUT_FILENAMES},
        "formal_decision_sha256": FORMAL_DECISION_SHA256,
        "event_count": 7,
        "chemistry_positive_count": 7,
        "training_include_count": 7,
        "future_training_admission_candidate_count": 7,
        "training_admitted_count": 0,
        "training_materialization_allowed_count": 0,
        "current_runtime_model_usable_count": 0,
        "deterministic_rebuild_matches_materialized": True,
        "ready_for_training": False,
    }


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    artifacts = materialize_artifacts_v1(repo_root)
    print("formal_human_decision_ingested=true")
    print("event_count=7")
    print("chemistry_positive_count=7")
    print("training_include_count=7")
    print("future_training_admission_candidate_count=7")
    print("training_admitted_count=0")
    print("published_global_positive_count_remains=82")
    print("ready_for_training=false")
    for name in OUTPUT_FILENAMES:
        print(name + "_sha256=" + _sha(artifacts[name]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
