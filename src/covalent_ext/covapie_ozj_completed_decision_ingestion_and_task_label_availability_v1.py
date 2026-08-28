"""Ingest the frozen OZJ Exact4 human decision as deterministic metadata.

This additive owner projects only sample-level authority already present in the
formal human decision.  The reviewer approved D5 INCLUDE; this ingestion then
deterministically derives future-admission candidacy under the published YUN
INCLUDE contract.  That candidacy is not human-approved admission, formal
training admission, materialization, runtime usability, tensor authority, or
parameter-update authorization.  No chemistry reinterpretation, reconciliation,
global census refresh, PRE/POST reconstruction, model work, or training occurs.
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
    "OZJIngestionSafetyError",
    "load_frozen_formal_decision_v1",
    "validate_completed_decision_projection_v1",
    "build_artifacts_v1",
    "materialize_artifacts_v1",
    "check_materialized_v1",
)

SCHEMA_VERSION = "covapie_ozj_completed_decision_ingestion_and_task_label_availability_v1"
SNAPSHOT_SCHEMA_VERSION = "covapie_ozj_completed_human_decision_snapshot_v1"
MATRIX_SCHEMA_VERSION = "covapie_ozj_event_task_label_availability_v1"
SUMMARY_SCHEMA_VERSION = "covapie_ozj_completed_decision_ingestion_summary_v1"
MANIFEST_SCHEMA_VERSION = "covapie_ozj_completed_decision_ingestion_manifest_v1"

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_ozj_completed_decision_ingestion_and_task_label_availability_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/"
    "check_covapie_ozj_completed_decision_ingestion_and_task_label_availability_v1.py"
)
TEST_RELATIVE = Path(
    "tests/"
    "test_covapie_ozj_completed_decision_ingestion_and_task_label_availability_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_ozj_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT = "covapie_ozj_completed_human_decision_snapshot_v1.json"
MATRIX = "covapie_ozj_event_task_label_availability_v1.csv"
SUMMARY = "covapie_ozj_completed_decision_ingestion_summary_v1.json"
MANIFEST = "covapie_ozj_completed_decision_ingestion_manifest_v1.json"
OUTPUT_FILENAMES = (SNAPSHOT, MATRIX, SUMMARY, MANIFEST)
OUTPUT_RELATIVE_PATHS = tuple(OUTPUT_ROOT_RELATIVE / name for name in OUTPUT_FILENAMES)
CANDIDATE_PUBLICATION_PATHS = (
    SOURCE_RELATIVE,
    CHECKER_RELATIVE,
    TEST_RELATIVE,
    *OUTPUT_RELATIVE_PATHS,
)

# Frozen only after full semantic validation of the source-derived projection.
# These are derived-projection contract digests, never human/science authority.
_EXPECTED_SNAPSHOT_SHA256_V1 = (
    "3458c3559963b09f69495ffe8cf43511a1e84b7de5ad0c84279ccdcd100a4b25"
)
_EXPECTED_MATRIX_SHA256_V1 = (
    "b039dbde52e2fe6a46866cdce0a378fc6dcc942e4a552845ce664fd80f1009d3"
)
_EXPECTED_SUMMARY_SHA256_V1 = (
    "305bb814c97a450e8dc95961433daf1e9aca942537469153a89d7e322c6c3214"
)

FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT = Path(
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "OZJ_COVAPIE_BULK_REVIEW_UNIT_18734D9C06222450/"
    "formal-human-decision-v1/ozj_formal_human_decision_v1.json"
)
FORMAL_DECISION_BYTE_COUNT = 28914
FORMAL_DECISION_SHA256 = (
    "0b14271a4541e69d768e28b6433c87b8b22c21505f6e3bdf075bb94381c3c606"
)
FORMAL_DECISION_SCHEMA = "covapie_ozj_exact4_formal_human_decision_v1"
FORMAL_SEMANTIC_CANONICAL_SHA256 = (
    "c88e6e58d80999d0aaaaa4dbb2a08fe6ac641e2950c625aac4a319154c40fc87"
)
EXPECTED_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_18734D9C06222450"
EXPECTED_APPROVED_AT_UTC = "2026-08-28T14:03:16Z"
EXPECTED_ROLE_PROFILE = "STRICT_LINKER_PRESENT_V1"
EXPECTED_D6 = (
    "OZJ Exact4 represents the target-directed, structure-based-designed TbPTR1 "
    "inhibitor compound observed in PDB 4CL8 covalently linked to the native "
    "Cys168 SG through ligand atom CAF. The medicinal-chemistry context "
    "intentionally uses the 3-formylphenyl region for Cys168 covalent anchoring "
    "and represents a medicinal antiparasitic covalent-inhibitor context rather "
    "than a sample-preparation modification or catalytic-intermediate context. "
    "Candidate1 is selected as the sample-level role partition, with CAF/OAD as "
    "the warhead-derived formyl region, the intervening phenyl region as linker, "
    "and the remaining pyrrolopyrimidine/cyano/diamino recognition core as "
    "scaffold. Source component bond-order evidence and the observed SG-CAF "
    "event connection are preserved as distinct evidence and are not promoted "
    "here to independently validated complete event-specific POST topology or "
    "PRE authority. No event-specific disposition exception is applied, and no "
    "reusable reaction-family, warhead-rule, warhead-type, or cross-sample "
    "authority is created."
)
AUTHORITY_SOURCE = "FORMAL_OZJ_HUMAN_DECISION"
AUTHORITY_SCOPE = "SAMPLE_LEVEL_OZJ_EXACT4_ONLY"
HUMAN_CONTEXT_SCOPE = "EXACT4_SAMPLE_LEVEL_HUMAN_APPROVED_CONTEXT_ONLY"
SOURCE_CCD_AUTHORITY_SCOPE = "FROZEN_COMPONENT_IDENTITY_PROVENANCE_ONLY"
FORMAL_FUTURE_STATUS = "DEFERRED_TO_DOWNSTREAM_INGESTION_AND_CENSUS"
FUTURE_STATUS = "CANDIDATE_REQUIRES_INDEPENDENT_FUTURE_ADMISSION"

EXPECTED_EVENTS = (
    ("COVAPIE_CYS_SG_EVENT_V1:4CL8:A:CYS:168-:SG:E:OZJ:CAF", 670, "4CL8", 1, "A", "CYS:168-", None, "E", None, "covale1", 1.712004, "1.712004"),
    ("COVAPIE_CYS_SG_EVENT_V1:4CL8:B:CYS:168-:SG:I:OZJ:CAF", 671, "4CL8", 1, "B", "CYS:168-", None, "I", None, "covale2", 1.721461, "1.721461"),
    ("COVAPIE_CYS_SG_EVENT_V1:4CL8:C:CYS:168-:SG:L:OZJ:CAF", 672, "4CL8", 1, "C", "CYS:168-", None, "L", None, "covale3", 1.722389, "1.722389"),
    ("COVAPIE_CYS_SG_EVENT_V1:4CL8:D:CYS:168-:SG:O:OZJ:CAF", 673, "4CL8", 1, "D", "CYS:168-", None, "O", None, "covale4", 1.725425, "1.725425"),
)
EXPECTED_EVENT_IDS = tuple(row[0] for row in EXPECTED_EVENTS)
EXPECTED_RANKS = tuple(row[1] for row in EXPECTED_EVENTS)
EXPECTED_HEAVY_ATOMS = (
    "C2", "C4", "C5", "C6", "CAE", "CAF", "CAG", "CAH", "CAI", "CAJ",
    "CAP", "CAQ", "CAR", "CAS", "N1", "N3", "NAA", "NAB", "NAC", "NAM", "OAD",
)
EXPECTED_WARHEAD = ("CAF", "OAD")
EXPECTED_LINKER = ("CAG", "CAH", "CAI", "CAJ", "CAP", "CAQ")
EXPECTED_SCAFFOLD = (
    "C2", "C4", "C5", "C6", "CAE", "CAR", "CAS", "N1", "N3", "NAA", "NAB", "NAC", "NAM",
)

CANONICAL_TASKS = (
    (0, "warhead_only", "A", ("warhead",), ("scaffold", "linker")),
    (1, "linker_plus_warhead", "B", ("linker", "warhead"), ("scaffold",)),
    (2, "scaffold_plus_warhead", "B2", ("scaffold", "warhead"), ("linker",)),
    (3, "scaffold_only", "B3", ("scaffold",), ("linker", "warhead")),
    (4, "scaffold_plus_linker_plus_warhead", "C", ("scaffold", "linker", "warhead"), ("minimal_seed",)),
)
STRICT_VALID_TASK_IDS = (0, 1, 2, 3, 4)

RUNTIME_SOURCE_RELATIVE = Path(
    "src/covalent_ext/covapie_direct_attachment_optional_linker_runtime_v1.py"
)
CANONICAL_TASK_SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py"
)
IMMUTABLE_SEMANTIC_OWNER_BINDINGS = (
    (RUNTIME_SOURCE_RELATIVE, 37255, "434285a43fa0158e62d40f48ed95d137f5fd68ea9b00101cc20674025849c535", "strict_profile_runtime_semantics_owner"),
    (CANONICAL_TASK_SOURCE_RELATIVE, 67274, "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b", "canonical_role_and_task_semantics_owner"),
)

FROZEN_REVIEW_PACKAGE_BINDINGS = (
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/OZJ_COVAPIE_BULK_REVIEW_UNIT_18734D9C06222450/review-preparation-v1/ozj_machine_evidence_manifest_v1.json"), 12619, "b71963967755c82ce28538c6e2a8bbc47db7ed2be68373a4f7240a860adcd48e", "OZJ_MACHINE_EVIDENCE_MANIFEST_REVIEWED_BYTES", "0664"),
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/OZJ_COVAPIE_BULK_REVIEW_UNIT_18734D9C06222450/review-preparation-v1/ozj_exact4_event_review_v1.csv"), 4553, "a8d973dff1c819a1a71746e106787d3e94e2694f79cc7dd5a1c1604c906ca805", "OZJ_EXACT4_EVENT_REVIEWED_BYTES", "0664"),
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/OZJ_COVAPIE_BULK_REVIEW_UNIT_18734D9C06222450/review-preparation-v1/ozj_graph_and_role_candidates_v1.json"), 17565, "c53b82e206960fc7703c00835f55b070e772e85955d4ac387d6726b1cdb68099", "OZJ_GRAPH_AND_ROLE_CANDIDATES_REVIEWED_BYTES", "0664"),
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/OZJ_COVAPIE_BULK_REVIEW_UNIT_18734D9C06222450/review-preparation-v1/HUMAN_REVIEW_GUIDE.md"), 3397, "d6f1c6e53788dbb64a6dfddb65827c60ce4202831f233914fe49f9207709ed9e", "OZJ_HUMAN_REVIEW_GUIDE_REVIEWED_BYTES", "0664"),
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/OZJ_COVAPIE_BULK_REVIEW_UNIT_18734D9C06222450/review-preparation-v1/ozj_unsigned_human_decision_template_v1.json"), 3546, "c2b11ad7fedc44bda9709449b7719ddfc889f2edabda707fd92e76fb2f7f3d5f", "OZJ_UNSIGNED_DECISION_TEMPLATE_REVIEWED_BYTES", "0664"),
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/OZJ_COVAPIE_BULK_REVIEW_UNIT_18734D9C06222450/review-preparation-v1/ligand_ozj_review_package_v1.py"), 98093, "5891c013758118799ac57798674db7c81764955e6b3174cf3942d2870f3e10c5", "OZJ_REVIEW_PACKAGE_VALIDATOR_REVIEWED_BYTES", "0664"),
)

ARCHITECTURE_PRECEDENT_BINDINGS = (
    (Path("src/covalent_ext/covapie_cht_completed_decision_ingestion_and_task_label_availability_v1.py"), 103035, "7a5561f1cb35465a2dbe6af8121f06a07b7aea6d82051e3945352cf1c669aff7", "CHT_LATEST_INGESTION_ARCHITECTURE_PRECEDENT"),
    (Path("data/derived/covalent_small/covapie_cht_completed_decision_ingestion_and_task_label_availability_v1/covapie_cht_event_task_label_availability_v1.csv"), 10225, "a754c0764ec61eacf7ec64dabdc370e4bca5a00abdfb94ea3923b52be55df6b6", "CHT_STRICT_EXACT5_MATRIX_PRECEDENT"),
)
INCLUDE_REPOSITORY_PRECEDENT_BINDINGS = (
    (Path("src/covalent_ext/covapie_yun_completed_decision_ingestion_and_task_label_availability_v1.py"), 82003, "8339aaa2c57fe1637ab4e4feb7db964fc76224957687d2e0752e28ba3b093928", "YUN_INCLUDE_INGESTION_PRECEDENT_OWNER"),
    (Path("data/derived/covalent_small/covapie_yun_completed_decision_ingestion_and_task_label_availability_v1/covapie_yun_event_task_label_availability_v1.csv"), 13886, "f5c58990490282a9a3ab5218f8ed83f8cead6062fdeb06c4fedc10665630ca0e", "YUN_INCLUDE_PUBLISHED_MATRIX_PRECEDENT"),
)
INCLUDE_PARENT_PRECEDENT_BINDINGS = (
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/YUN_COVAPIE_BULK_REVIEW_UNIT_1138FFC288DFD03D/formal-human-decision-v1/yun_formal_human_decision_v1.json"), 30722, "b4eeebe03354e820d9658225997c34b58b41c66f4dfe126230024306816e1140", "YUN_INCLUDE_FORMAL_PRECEDENT"),
)

CURRENT_CENSUS_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_cht_v1"
)
CURRENT_CENSUS_BINDINGS = (
    (Path("src/covalent_ext/covapie_cumulative1000_current_global_readiness_census_with_cht_v1.py"), 63414, "e478b41dca9555bda1caab2cacd3160f3b0cc98c744d50f2eb46a915fccb6f14", "current_CHT_refreshed_census_owner"),
    (CURRENT_CENSUS_ROOT / "covapie_cumulative1000_current_global_readiness_census_with_cht_v1.csv", 523894, "b51bff3d31d910fa4990a1482e0d3b05364fed86a9cf503de833ddf8851f6384", "current_CHT_refreshed_census_csv"),
    (CURRENT_CENSUS_ROOT / "covapie_cumulative1000_current_global_readiness_summary_with_cht_v1.json", 15828, "b2130b1f0b9cf36455f1bf00e6e5c32e9a4ef250f18bb25f7a902af67c79e0b3", "current_CHT_refreshed_census_summary"),
    (CURRENT_CENSUS_ROOT / "covapie_cumulative1000_current_global_readiness_manifest_with_cht_v1.json", 38794, "168f2a713aa9b0ee6904f414330518342ca553495d17340d94ad9df1f8bc1f33", "current_CHT_refreshed_census_manifest"),
)


class OZJIngestionSafetyError(ValueError):
    """Raised when the frozen OZJ ingestion contract cannot be proven."""


def _fail(reason: str) -> None:
    raise OZJIngestionSafetyError(reason)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _json_cell(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _csv_bytes(header: Sequence[str], rows: Sequence[Mapping[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=header,
        extrasaction="raise",
        lineterminator="\n",
    )
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
        raise OZJIngestionSafetyError("BOUND_SOURCE_READ_FAILED:" + label) from error
    if len(payload) != expected_bytes:
        _fail("BOUND_SOURCE_BYTE_COUNT_MISMATCH:" + label)
    if _sha(payload) != expected_sha256:
        _fail("BOUND_SOURCE_SHA256_MISMATCH:" + label)
    if (
        expected_mode is not None
        and format(path.stat().st_mode & 0o7777, "04o") != expected_mode
    ):
        _fail("BOUND_SOURCE_MODE_MISMATCH:" + label)
    return payload


def _literal_assignments(path: Path, names: Sequence[str]) -> dict[str, object]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, SyntaxError) as error:
        raise OZJIngestionSafetyError("SOURCE_AST_READ_FAILED:" + path.name) from error
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
                    raise OZJIngestionSafetyError(
                        "SOURCE_CONTRACT_NOT_LITERAL:" + target.id
                    ) from error
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
        "ligand_component_id": "OZJ",
        "reviewer_id": "fmx",
        "attestor_id": "fmx",
        "approved": True,
        "unsigned": False,
        "approved_at_utc": EXPECTED_APPROVED_AT_UTC,
        "verification_status": "MATCHED",
    }


def _expected_evidence_provenance() -> dict[str, object]:
    rows = [
        {
            "source_role": role.lower(),
            "path": path.as_posix(),
            "byte_count": byte_count,
            "sha256": sha256,
            "mode": mode,
            "predecessor_immutable": True,
            "verification_status": "SHA256_SIZE_MODE_VERIFIED",
        }
        for path, byte_count, sha256, role, mode in FROZEN_REVIEW_PACKAGE_BINDINGS
    ]
    formal_roles = (
        "machine_evidence_manifest", "exact4_event_review",
        "graph_and_role_candidates", "human_review_guide",
        "unsigned_human_decision_template", "package_builder_and_validator",
    )
    for row, role in zip(rows, formal_roles, strict=True):
        row["source_role"] = role
    return {
        "source_package_path": str(FROZEN_REVIEW_PACKAGE_BINDINGS[0][0].parent),
        "path_namespace": "project_parent_relative",
        "exact6_file_count": 6,
        "existing_package_materialized_validation": "PASS",
        "reviewed_machine_evidence_only": True,
        "human_authorization_origin": "EXTERNAL_EXPLICIT_HUMAN_APPROVAL",
        "exact6_SHA_bindings": rows,
        "formal_schema_precedents_read_only": [
            "covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/YUN_COVAPIE_BULK_REVIEW_UNIT_1138FFC288DFD03D/formal-human-decision-v1/yun_formal_human_decision_v1.json",
            "covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/CHT_COVAPIE_BULK_REVIEW_UNIT_BCA0E7B8C2B33410/formal-human-decision-v1/cht_formal_human_decision_v1.json",
            "covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/NEQ_COVAPIE_BULK_REVIEW_UNIT_0E0F340A9F98DA62/formal-human-decision-v1/neq_formal_human_decision_v1.json",
            "covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/1F8_COVAPIE_BULK_REVIEW_UNIT_9723B0F9EC07CC81/formal-human-decision-v1/1f8_formal_human_decision_v1.json",
        ],
    }


def _expected_raw_event(row: tuple[object, ...]) -> dict[str, object]:
    (
        event_id,
        rank,
        pdb_id,
        model_number,
        protein_chain,
        residue_id,
        protein_altloc,
        ligand_chain,
        ligand_altloc,
        connection,
        distance,
        _lexeme,
    ) = row
    return {
        "canonical_event_id": event_id,
        "scaleup_rank": rank,
        "pdb_id": pdb_id,
        "model_number": model_number,
        "protein_asym": protein_chain,
        "cys_residue_id": residue_id,
        "protein_altloc": protein_altloc,
        "ligand_component_id": "OZJ",
        "ligand_asym": ligand_chain,
        "ligand_altloc": ligand_altloc,
        "selected_connection_id": connection,
        "POST_distance_angstrom": distance,
        "D1_task_relevance": "RELEVANT",
        "D2_chemistry": "POSITIVE",
        "negative_chemistry": False,
        "task_domain_negative": False,
        "D3_reactive_pair": "CONFIRM_OBSERVED_PAIR",
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "CAF",
        "ligand_reactive_atom_element": "C",
        "reactive_pair_human_authoritative": True,
        "D4_role_partition": "SELECT_CANDIDATE_1",
        "selected_role_candidate_index_0based": 1,
        "role_partition_human_authoritative": True,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "D5_training_use": "INCLUDE",
        "human_training_excluded": False,
        "training_use_allowed": True,
        "training_use_include": True,
        "training_admitted": False,
        "D6_context_reference": "UNIT_LEVEL_HUMAN_APPROVED_CONTEXT",
        "event_specific_disposition_exception": False,
        "decision_finalized": True,
    }


def _event_context_inventory() -> list[dict[str, object]]:
    return [
        {
            "canonical_event_id": row[0], "pdb_id": row[2],
            "protein_asym": row[4], "cys_residue_id": row[5],
            "ligand_asym": row[7],
        }
        for row in EXPECTED_EVENTS
    ]


def _event_projection(raw: Mapping[str, object], lexeme: str) -> dict[str, object]:
    return {
            "canonical_event_id": raw["canonical_event_id"],
            "scaleup_rank": raw["scaleup_rank"],
            "pdb_id": raw["pdb_id"],
            "model_number": raw["model_number"],
            "protein_chain_or_asym": raw["protein_asym"],
            "cys_residue_id": raw["cys_residue_id"],
            "protein_altloc": raw["protein_altloc"],
            "ligand_component_id": raw["ligand_component_id"],
            "ligand_chain_or_asym": raw["ligand_asym"],
            "ligand_altloc": raw["ligand_altloc"],
            "selected_connection_id": raw["selected_connection_id"],
            "POST_distance_angstrom": raw["POST_distance_angstrom"],
            "POST_distance_frozen_lexeme": lexeme,
            "task_relevant": True,
            "chemistry_known_positive": True,
            "negative_chemistry": False,
            "task_domain_negative": False,
            "reactive_pair_human_decision_available": True,
            "reactive_pair_human_authoritative": True,
            "protein_reactive_atom": "SG",
            "ligand_reactive_atom": "CAF",
            "ligand_reactive_atom_element": "C",
            "role_partition_human_decision_available": True,
            "role_partition_human_authoritative": True,
            "selected_role_candidate_index_0based": 1,
            "role_profile": EXPECTED_ROLE_PROFILE,
            "formal_event_training_use_decision": "INCLUDE",
            "event_training_use_human_decision_available": True,
            "training_use_allowed": True,
            "training_use_include": True,
            "human_training_excluded": False,
            "formal_future_training_admission_candidate": None,
            "formal_future_training_admission_candidate_status": FORMAL_FUTURE_STATUS,
            "candidate_for_future_training_admission": True,
            "future_training_admission_status": FUTURE_STATUS,
            "future_training_candidate_derived_by_ingestion": True,
            "future_training_candidate_is_training_admission": False,
            "training_admitted": False,
            "training_materialization_allowed_now": False,
            "current_runtime_model_usable": False,
            "event_specific_disposition_exception": False,
            "source_CAF_OAD_bond_order": "DOUB",
            "source_CCD_component_graph_authority_scope": SOURCE_CCD_AUTHORITY_SCOPE,
            "explicit_SG_CAF_connection_available": True,
            "complete_POST_adduct_topology_authority_available": False,
            "PRE_topology_authority_available": False,
            "PRE_geometry_authority_available": False,
            "PRE_geometry_training_label_available_now": False,
            "PRE_precursor_topology_authority_available": False,
            "PRE_reconstruction_performed": False,
            "POST_bond_order_reconstruction_performed": False,
            "second_reconstructed_POST_graph_created": False,
            "POST_source_evidence_available": True,
            "POST_geometry_training_label_available_now": False,
            "reaction_family_target_available": False,
            "warhead_rule_target_available": False,
            "warhead_type_target_available": False,
            "reusable_chemistry_authority_available": False,
            "reusable_pair_authority_available": False,
            "reusable_role_authority_available": False,
            "model_bound_pair_target_created": False,
            "tensor_target_created": False,
            "training_admission_created": False,
            "formal_split_authority_created": False,
            "parameter_update_authorization": False,
            "authority_source": AUTHORITY_SOURCE,
            "authority_scope": AUTHORITY_SCOPE,
            "authority_ingested": True,
            "authority_created_by_this_ingestion": False,
    }


def _role_snapshot() -> dict[str, object]:
    return {
        "human_role_partition_choice": "SELECT_CANDIDATE_1",
        "selected_candidate_index_0based": 1,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "exact_heavy_atom_count": 21,
        "exact_heavy_atom_ids": list(EXPECTED_HEAVY_ATOMS),
        "warhead_atoms": list(EXPECTED_WARHEAD),
        "frozen_source_warhead_atoms_source_order": list(EXPECTED_WARHEAD),
        "warhead_atom_set_exactly_matches_frozen_candidate": True,
        "linker_atoms": list(EXPECTED_LINKER),
        "frozen_source_linker_atoms_source_order": list(EXPECTED_LINKER),
        "scaffold_atoms": list(EXPECTED_SCAFFOLD),
        "frozen_source_scaffold_atoms_source_order": list(EXPECTED_SCAFFOLD),
        "boundary_bonds": [
            {
                "atom_id_1": "CAF",
                "atom_id_2": "CAP",
                "bond_order": "SING",
                "boundary_between_roles": ["warhead", "linker"],
            },
            {
                "atom_id_1": "CAQ",
                "atom_id_2": "CAS",
                "bond_order": "SING",
                "boundary_between_roles": ["linker", "scaffold"],
            },
        ],
        "heavy_atom_disjoint": True,
        "heavy_atom_exhaustive": True,
        "warhead_connected": True,
        "linker_empty": False,
        "linker_connected": True,
        "scaffold_connected": True,
        "sample_level_role_decision_exists_in_source": True,
        "sample_level_role_decision_created_by_ingestion": False,
        "machine_selected": False,
        "reactive_CAF_in_warhead": True,
        "machine_recommended": False,
        "machine_recommended_candidate": None,
    }


def _canonical_task_contract() -> dict[str, object]:
    applicability = [
        {
            "task_id": task_id,
            "semantic_long_name": semantic,
            "display_alias": alias,
            "structurally_applicable": task_id in STRICT_VALID_TASK_IDS,
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
        "strict_profile_applicable_task_ids": list(STRICT_VALID_TASK_IDS),
        "strict_profile_applicable_task_count": 5,
        "strict_profile_task_applicability": applicability,
        "D5_INCLUDE_does_not_change_structural_applicability": True,
    }


def _scientific_context() -> dict[str, object]:
    return {
        "D6_exact_choice": EXPECTED_D6,
        "scope": HUMAN_CONTEXT_SCOPE,
        "semantic_context": "target-directed, structure-based-designed TbPTR1 covalent inhibitor; 3-formylphenyl-mediated native Cys168 anchoring; medicinal antiparasitic inhibitor context; not sample-preparation modification; not catalytic-intermediate context",
        "target_directed_TbPTR1_context": True,
        "structure_based_covalent_inhibitor_context": True,
        "native_Cys168_anchoring_context": True,
        "medicinal_antiparasitic_context": True,
        "sample_preparation_modification_context": False,
        "catalytic_intermediate_context": False,
        "event_specific_disposition_exception": False,
        "event_specific_disposition_exception_count": 0,
        "all_exact5_receive_same_D1_through_D5_disposition": True,
        "sample_specific_context_converted_to_reusable_authority": False,
    }


def _frozen_graph_snapshot() -> dict[str, object]:
    return {
        "heavy_atom_count": 21,
        "heavy_atom_ids": list(EXPECTED_HEAVY_ATOMS),
        "element_inventory": {"C": 14, "N": 6, "O": 1},
        "heavy_bond_count": 23,
        "connected_component_count": 1,
        "reactive_atom": "CAF",
        "CAF_element": "C", "CAF_formal_charge": 0,
        "CAF_aromatic": False,
        "CAF_one_hop": ["CAP", "OAD"],
        "CAF_exactly_two_hop": ["CAH", "CAJ"],
        "CAF_OAD_source_bond_order": "DOUB",
        "processing_graph_sha256": "16bdc88f7d1b0767ffd77f410c51c65a72801d2b45b0135406d0f11b749793fe",
        "canonical_heavy_graph_sha256": "ab959c9640a9553db8d109bcad7bb6148e347db57294ce8efc2325804a5d8a40",
    }


def _source_ccd_and_event_topology_boundary() -> dict[str, object]:
    return {
        "source_CCD_component_graph_heavy_atom_count": 21,
        "source_CCD_component_graph_authority_scope": SOURCE_CCD_AUTHORITY_SCOPE,
        "source_CAF_OAD_bond": {
            "atom_id_1": "CAF", "atom_id_2": "OAD", "bond_order": "DOUB",
        },
        "source_CAF_OAD_bond_order": "DOUB",
        "explicit_observed_SG_CAF_connection_available": True,
        "explicit_observed_SG_CAF_connection_event_count": 4,
        "complete_authoritative_POST_adduct_bond_order_topology_available": False,
        "complete_POST_topology_authority_available": False,
        "PRE_topology_authority_available": False,
        "PRE_geometry_authority_available": False,
        "PRE_reconstruction_performed": False,
        "POST_bond_order_reconstruction_performed": False,
        "second_reconstructed_POST_graph_created": False,
    }


def _geometry_boundary() -> dict[str, object]:
    return {
        "POST_source_evidence_count": 4,
        "POST_observed_SG_CAF_distances_angstrom": [
            {
                "scaleup_rank": row[1],
                "pdb_id": row[2],
                "cys_residue_id": row[5],
                "distance": row[10],
                "distance_frozen_lexeme": row[11],
            }
            for row in EXPECTED_EVENTS
        ],
        "POST_geometry_training_authority_count": 0,
        "POST_geometry_training_target_count": 0,
        "PRE_status": "PRE_REACTION_UNRESOLVED_NOT_CREATED",
        "PRE_geometry_authority_count": 0,
        "PRE_geometry_training_target_count": 0,
        "PRE_precursor_topology_authority_count": 0,
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
        "training_use_include": True,
        "formal_future_training_admission_candidate": None,
        "formal_future_training_admission_candidate_status": FORMAL_FUTURE_STATUS,
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
        "negative_chemistry": False,
        "task_domain_negative": False,
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
        "new_reusable_authority_created": False,
    }


def _authority_boundary() -> dict[str, object]:
    return {
        "formal_human_decision_modified": False,
        "snapshot_created_by_ingestion": True,
        "human_authority_ingested": True,
        "human_authority_created_by_ingestion": False,
        "future_training_candidate_derived_by_ingestion": True,
        "future_training_candidate_is_training_admission": False,
        "new_human_authority_created": False,
        "reaction_family_authority_created": False,
        "warhead_rule_authority_created": False,
        "warhead_type_authority_created": False,
        "reusable_chemistry_authority_created": False,
        "reusable_pair_authority_created": False,
        "reusable_role_authority_created": False,
        "complete_POST_topology_authority_created": False,
        "PRE_topology_authority_created": False,
        "PRE_geometry_authority_created": False,
        "POST_geometry_training_authority_created": False,
        "training_admission_created": False,
        "training_admitted": False,
        "candidate_for_future_training_admission": True,
        "training_dataset_changed": False,
        "training_materialization_allowed_now": False,
        "formal_split_authority_created": False,
        "current_runtime_model_usable": False,
        "model_bound_pair_target_created": False,
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
    expected_keys = {
        "approved", "attestor_id", "authority_boundary",
        "canonical_Exact5_and_sample_applicability", "canonical_event_ids",
        "decision_status", "downstream_status", "duplicate_event_count",
        "event_context_inventory", "event_level_human_decisions",
        "evidence_provenance", "exact_event_count", "extra_event_count",
        "feature_semantics_audit_item", "feature_semantics_status",
        "formal_authority_created", "frozen_OZJ_graph", "geometry_boundary",
        "human_approval", "human_approval_recorded", "human_approved_context",
        "human_decision_created", "human_review_completed",
        "human_review_decision_created", "ligand_component_id",
        "omitted_event_count", "pdb_event_counts", "pdb_ids",
        "prior_review_state", "published_global_state_unchanged", "ranks",
        "reaction_family_authority", "reactive_pair_human_decision",
        "ready_for_training", "record_role", "reusable_authority_boundary",
        "review_unit_id", "reviewer_id", "schema_version",
        "selected_role_partition", "source_CCD_and_event_topology_boundary",
        "training_admitted", "training_prerequisite_warning",
        "training_use_human_decision", "unique_event_count",
        "unit_level_human_decisions", "unsigned", "warhead_rule_authority",
        "warhead_type_authority",
    }
    if set(formal) != expected_keys:
        _fail("FORMAL_TOP_LEVEL_FIELD_SET_INVALID")
    expected_top = {
        "schema_version": FORMAL_DECISION_SCHEMA,
        "record_role": "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY",
        "decision_status": "HUMAN_APPROVED_SAMPLE_LEVEL_DECISION",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "ligand_component_id": "OZJ",
        "exact_event_count": 4,
        "unique_event_count": 4,
        "duplicate_event_count": 0,
        "omitted_event_count": 0,
        "extra_event_count": 0,
        "canonical_event_ids": list(EXPECTED_EVENT_IDS),
        "ranks": list(EXPECTED_RANKS),
        "pdb_ids": ["4CL8"],
        "pdb_event_counts": {"4CL8": 4},
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
        "training_admitted": False,
        "ready_for_training": False,
    }
    for field, expected in expected_top.items():
        if formal[field] != expected:
            _fail("FORMAL_TOP_LEVEL_SEMANTICS_INVALID:" + field)

    approval = formal["human_approval"]
    if (
        approval["D1_task_relevance"] != "RELEVANT"
        or approval["D2_chemistry"] != "POSITIVE"
        or approval["D3_reactive_pair"] != "CONFIRM_OBSERVED_PAIR"
        or approval["D4_role_partition"] != "SELECT_CANDIDATE_1"
        or approval["D5_training_use"] != "INCLUDE"
        or approval["D6_scientific_context"] != EXPECTED_D6
        or approval["approved_at_utc"] != EXPECTED_APPROVED_AT_UTC
        or approval["reviewer_id"] != "fmx"
        or approval["attestor_id"] != "fmx"
        or approval["current_authorization_source"]
        != "EXTERNAL_EXPLICIT_HUMAN_APPROVAL"
        or approval["human_selected_role_candidate_index_0based"] != 1
        or approval["machine_auto_selection_performed"] is not False
        or approval["machine_recommended_candidate"] is not None
        or approval["approval_recorded"] is not True
        or approval["human_choices_externally_authorized"] is not True
    ):
        _fail("FORMAL_HUMAN_APPROVAL_SEMANTICS_INVALID")
    if formal["evidence_provenance"] != _expected_evidence_provenance():
        _fail("FORMAL_EXACT6_EVIDENCE_PROVENANCE_DRIFT")
    if formal["event_level_human_decisions"] != [
        _expected_raw_event(row) for row in EXPECTED_EVENTS
    ]:
        _fail("FORMAL_EXACT4_EVENT_SEMANTICS_INVALID")
    if formal["event_context_inventory"] != _event_context_inventory():
        _fail("FORMAL_EVENT_CONTEXT_INVENTORY_DRIFT")

    pair = formal["reactive_pair_human_decision"]
    if (
        pair["D3_human_choice"] != "CONFIRM_OBSERVED_PAIR"
        or pair["authority_scope"] != "EXACT4_SAMPLE_LEVEL_ONLY"
        or pair["protein_reactive_atom"] != "SG"
        or pair["ligand_reactive_atom"] != "CAF"
        or pair["ligand_reactive_atom_element"] != "C"
        or pair["observed_pair"] != "CYS168_SG_TO_OZJ_CAF"
        or pair["reactive_pair_human_authoritative"] is not True
        or pair["reactive_pair_human_authoritative_event_count"] != 4
        or pair["model_bound_reactive_pair_target_created"] is not False
        or pair["tensor_target_created"] is not False
        or pair["cross_sample_reusable_pair_authority_created"] is not False
        or pair["training_admission_created"] is not False
    ):
        _fail("FORMAL_REACTIVE_PAIR_SEMANTICS_DRIFT")

    graph = formal["frozen_OZJ_graph"]
    caf = graph["CAF"]
    role = formal["selected_role_partition"]
    exact5 = formal["canonical_Exact5_and_sample_applicability"]
    if (
        graph["heavy_atom_count"] != 21
        or graph["heavy_atom_ids"] != list(EXPECTED_HEAVY_ATOMS)
        or graph["element_counts"] != {"C": 14, "N": 6, "O": 1}
        or graph["heavy_bond_count"] != 23
        or graph["connected_component_count"] != 1
        or graph["processing_graph_digest"]
        != "16bdc88f7d1b0767ffd77f410c51c65a72801d2b45b0135406d0f11b749793fe"
        or graph["canonical_heavy_graph_digest"]
        != "ab959c9640a9553db8d109bcad7bb6148e347db57294ce8efc2325804a5d8a40"
        or graph["CAF_OAD_source_bond"]["bond_order"] != "DOUB"
        or caf["element"] != "C"
        or caf["formal_charge"] != 0
        or caf["aromatic_flag"] != "N"
        or caf["one_hop"] != ["CAP", "OAD"]
        or caf["exact_two_hop"] != ["CAH", "CAJ"]
        or role["D4_human_choice"] != "SELECT_CANDIDATE_1"
        or role["selected_candidate_index_0based"] != 1
        or role["role_profile"] != EXPECTED_ROLE_PROFILE
        or role["warhead_atoms"] != list(EXPECTED_WARHEAD)
        or role["linker_atoms"] != list(EXPECTED_LINKER)
        or role["scaffold_atoms"] != list(EXPECTED_SCAFFOLD)
        or role["boundary_bonds"]
        != [
            {
                "atom_id_1": "CAF", "atom_id_2": "CAP",
                "bond_order": "SING", "role_1": "warhead",
                "role_2": "linker", "source_heavy_heavy_bond": True,
            },
            {
                "atom_id_1": "CAQ", "atom_id_2": "CAS",
                "bond_order": "SING", "role_1": "linker",
                "role_2": "scaffold", "source_heavy_heavy_bond": True,
            },
        ]
        or role["applicable_canonical_task_ids"] != [0, 1, 2, 3, 4]
        or role["heavy_atom_disjoint"] is not True
        or role["heavy_atom_exhaustive"] is not True
        or role["warhead_connected"] is not True
        or role["linker_connected"] is not True
        or role["scaffold_connected"] is not True
        or role["CAF_in_warhead"] is not True
        or role["human_selected"] is not True
        or role["machine_selected"] is not False
        or role["machine_recommended"] is not False
        or role["machine_auto_selection_performed"] is not False
        or exact5["task_count"] != 5
        or exact5["B3_present"] is not True
        or exact5["sixth_task_present"] is not False
        or exact5["sample_applicable_task_ids"] != [0, 1, 2, 3, 4]
        or exact5["D5_INCLUDE_does_not_change_structural_applicability"] is not True
        or exact5["tasks"]
        != [
            {
                "task_id": task_id, "semantic_name": semantic,
                "display_alias": alias, "structurally_applicable": True,
            }
            for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
        ]
    ):
        _fail("FORMAL_CANDIDATE1_OR_EXACT5_DRIFT")

    context = formal["human_approved_context"]
    topology = formal["source_CCD_and_event_topology_boundary"]
    geometry = formal["geometry_boundary"]
    training = formal["training_use_human_decision"]
    if (
        context["semantic_context"] != _scientific_context()["semantic_context"]
        or context["unit_level_context_applies_to_exact_event_count"] != 4
        or context["no_event_specific_disposition_exception"] is not True
        or context["event_specific_disposition_exception_count"] != 0
        or topology["source_CCD_component_graph_authority_scope"]
        != SOURCE_CCD_AUTHORITY_SCOPE
        or topology["source_CAF_OAD_bond_order"] != "DOUB"
        or topology["observed_explicit_SG_CAF_connection_available"] is not True
        or topology["observed_explicit_SG_CAF_connection_event_count"] != 4
        or topology["combined_representation_is_authoritative_complete_POST_adduct_topology"]
        is not False
        or topology["complete_POST_adduct_topology_authority_created"] is not False
        or topology["PRE_precursor_topology_authority_created"] is not False
        or topology["PRE_geometry_authority_created"] is not False
        or topology["PRE_reconstruction_performed"] is not False
        or topology["POST_bond_order_reconstruction_performed"] is not False
        or topology["reconstructed_POST_graph_created"] is not False
        or geometry["POST_observed_SG_CAF_distances_angstrom"]
        != [
            {"distance": row[10], "scaleup_rank": row[1]}
            for row in EXPECTED_EVENTS
        ]
        or geometry["POST_geometry_training_authority_created"] is not False
        or geometry["POST_geometry_training_target_created"] is not False
        or geometry["PRE_status"] != "PRE_REACTION_UNRESOLVED_NOT_CREATED"
        or geometry["PRE_geometry_authority_created"] is not False
        or geometry["PRE_geometry_training_target_created"] is not False
        or geometry["PRE_precursor_topology_authority_created"] is not False
        or geometry["PRE_zero_fill_performed"] is not False
        or geometry["POST_to_PRE_copy_performed"] is not False
        or geometry["PRE_coordinate_reconstruction_performed"] is not False
        or training["D5_human_choice"] != "INCLUDE"
        or training["human_training_excluded"] is not False
        or training["training_use_allowed"] is not True
        or training["training_use_include"] is not True
        or training["future_training_admission_candidate"] is not None
        or training["future_training_admission_candidate_status"]
        != FORMAL_FUTURE_STATUS
        or training["formal_training_admitted"] is not False
        or training["training_admission_created"] is not False
        or training["training_materialization_allowed_now"] is not False
        or training["training_materialization_performed"] is not False
        or training["formal_split_authority_created"] is not False
        or training["tensor_target_created"] is not False
        or training["runtime_model_usable"] is not False
        or training["parameter_update_authorization"] is not False
    ):
        _fail("FORMAL_CONTEXT_TOPOLOGY_GEOMETRY_OR_INCLUDE_BOUNDARY_INVALID")

    for field in (
        "reaction_family_authority", "warhead_rule_authority",
        "warhead_type_authority",
    ):
        authority = formal[field]
        if (
            authority["status"] != "NOT_CREATED"
            or authority["authority_created"] is not False
            or authority["authority_value"] is not None
        ):
            _fail("FORMAL_AUXILIARY_AUTHORITY_INVALID:" + field)
    reusable = formal["reusable_authority_boundary"]
    prohibited_reusable = (
        "CYS_ALDEHYDE_generic_rule_created", "FORMYL_reusable_rule_created",
        "OZJ_reusable_chemistry_rule_created", "PRE_topology_authority_created",
        "complete_POST_topology_authority_created", "cross_sample_rule_created",
        "reaction_family_authority_created", "reusable_chemistry_authority_created",
        "reusable_pair_authority_created", "reusable_role_authority_created",
        "training_admission_authority_created", "warhead_rule_authority_created",
        "warhead_type_authority_created",
    )
    if any(reusable[field] is not False for field in prohibited_reusable):
        _fail("FORMAL_REUSABLE_AUTHORITY_BOUNDARY_INVALID")
    boundary = formal["authority_boundary"]
    prohibited_true = (
        "POST_geometry_training_authority_created",
        "POST_geometry_training_target_created", "PRE_geometry_authority_created",
        "PRE_precursor_topology_authority_created", "PRE_reconstruction_performed",
        "auxiliary_head_executed", "backward_performed", "batch_modified",
        "commit_performed", "complete_POST_adduct_topology_authority_created",
        "complete_PRE_topology_authority_created",
        "completed_decision_ingestion_performed", "fine_tune_performed",
        "formal_split_authority_created", "global_census_updated",
        "global_reconciliation_updated", "loader_modified", "loss_executed",
        "machine_auto_selection_performed", "model_forward_performed",
        "model_training_activation_authorized", "network_accessed",
        "optimizer_created", "optimizer_step_performed",
        "parameter_update_authorization", "parameter_update_performed",
        "push_performed", "reaction_family_authority_created",
        "ready_for_training", "repository_modified",
        "reusable_chemistry_authority_created",
        "reusable_reactive_pair_authority_created",
        "reusable_role_authority_created", "runtime_model_usable",
        "scientific_network_acquisition_performed", "tensor_integration_performed",
        "training_admission_created", "training_admitted",
        "training_dataset_changed", "training_performed",
        "warhead_rule_authority_created", "warhead_type_authority_created",
    )
    if any(boundary[field] is not False for field in prohibited_true):
        _fail("FORMAL_AUTHORITY_OR_TRAINING_BOUNDARY_INVALID")
    if formal["downstream_status"] != {
        "formal_human_decision_created": True,
        "completed_decision_ingestion": "NOT_DONE",
        "reconciliation": "NOT_DONE",
        "global_census_refresh": "NOT_DONE",
        "training": "NOT_STARTED",
    }:
        _fail("FORMAL_DOWNSTREAM_STATUS_INVALID")
    if formal["published_global_state_unchanged"] != {
        "OZJ_current_global_status": "CURRENTLY_UNREVIEWED",
        "future_training_admission_candidate_count": 19,
        "positive_count": 100,
        "reactive_pair_sample_authority_count": 100,
        "role_partition_sample_authority_count": 100,
        "task_relevant_count": 101,
        "training_EXCLUDE_count": 64,
        "training_INCLUDE_count": 36,
    }:
        _fail("FORMAL_PUBLISHED_GLOBAL_BOUNDARY_INVALID")
    return {
        "events": [
            _event_projection(event, EXPECTED_EVENTS[index][11])
            for index, event in enumerate(formal["event_level_human_decisions"])
        ],
        "event_context_inventory": _event_context_inventory(),
        "role": _role_snapshot(),
        "scientific_context": _scientific_context(),
        "source_ccd_and_event_topology_boundary":
            _source_ccd_and_event_topology_boundary(),
        "geometry_boundary": _geometry_boundary(),
        "training_boundary": _training_boundary(),
    }

def _semantic_owner_bindings(
    repo_root: Path, overrides: Mapping[Path, Path]
) -> list[dict[str, object]]:
    for relative, byte_count, sha256, role in IMMUTABLE_SEMANTIC_OWNER_BINDINGS:
        _verify_payload(
            overrides.get(relative, repo_root / relative),
            byte_count,
            sha256,
            role,
        )
    runtime = _literal_assignments(
        overrides.get(RUNTIME_SOURCE_RELATIVE, repo_root / RUNTIME_SOURCE_RELATIVE),
        ("STRICT_LINKER_PRESENT_V1",),
    )
    canonical = _literal_assignments(
        overrides.get(
            CANONICAL_TASK_SOURCE_RELATIVE,
            repo_root / CANONICAL_TASK_SOURCE_RELATIVE,
        ),
        ("EXACT3_ROLES", "CANONICAL_TASKS"),
    )
    if runtime["STRICT_LINKER_PRESENT_V1"] != EXPECTED_ROLE_PROFILE:
        _fail("STRICT_PROFILE_RUNTIME_CONTRACT_DRIFT")
    if (
        canonical["EXACT3_ROLES"] != ("scaffold", "linker", "warhead")
        or canonical["CANONICAL_TASKS"] != CANONICAL_TASKS
    ):
        _fail("GLOBAL_CANONICAL_EXACT5_TASK_CONTRACT_DRIFT")
    return _binding_rows(
        IMMUTABLE_SEMANTIC_OWNER_BINDINGS,
        namespace="repository_relative",
    )


def _frozen_review_bindings(
    repository_parent: Path, overrides: Mapping[Path, Path]
) -> list[dict[str, object]]:
    for relative, byte_count, sha256, role, mode in FROZEN_REVIEW_PACKAGE_BINDINGS:
        _verify_payload(
            overrides.get(relative, repository_parent / relative),
            byte_count,
            sha256,
            role,
            mode,
        )
    return [
        {
            "path": path.as_posix(),
            "path_namespace": "project_parent_relative",
            "byte_count": byte_count,
            "sha256": sha256,
            "sha256_scope": "file_bytes",
            "source_role": role,
            "mode": mode,
            "verification_status": "MATCHED",
        }
        for path, byte_count, sha256, role, mode in FROZEN_REVIEW_PACKAGE_BINDINGS
    ]


def _architecture_precedent_bindings(
    repo_root: Path, overrides: Mapping[Path, Path]
) -> list[dict[str, object]]:
    payloads: dict[str, bytes] = {}
    for relative, byte_count, sha256, role in ARCHITECTURE_PRECEDENT_BINDINGS:
        payloads[role] = _verify_payload(
            overrides.get(relative, repo_root / relative),
            byte_count, sha256, role,
        )
    try:
        rows = list(
            csv.DictReader(
                io.StringIO(
                    payloads["CHT_STRICT_EXACT5_MATRIX_PRECEDENT"].decode("utf-8")
                )
            )
        )
    except UnicodeDecodeError as error:
        raise OZJIngestionSafetyError(
            "CHT_ARCHITECTURE_PRECEDENT_PARSE_FAILED"
        ) from error
    if len(rows) != 5 or any(
        row.get("role_profile") != EXPECTED_ROLE_PROFILE
        or row.get("strict_profile_applicable_task_ids_json") != "[0,1,2,3,4]"
        or json.loads(row.get("canonical_task_applicability_json", "[]"))[3]
        .get("semantic_long_name") != "scaffold_only"
        for row in rows
    ):
        _fail("CHT_STRICT_EXACT5_ARCHITECTURE_PRECEDENT_INVALID")
    return _binding_rows(
        ARCHITECTURE_PRECEDENT_BINDINGS, namespace="repository_relative"
    )


def _include_precedent_bindings(
    repo_root: Path, overrides: Mapping[Path, Path]
) -> list[dict[str, object]]:
    payloads: dict[str, bytes] = {}
    for relative, byte_count, sha256, role in INCLUDE_REPOSITORY_PRECEDENT_BINDINGS:
        payloads[role] = _verify_payload(
            overrides.get(relative, repo_root / relative),
            byte_count, sha256, role,
        )
    for relative, byte_count, sha256, role in INCLUDE_PARENT_PRECEDENT_BINDINGS:
        payloads[role] = _verify_payload(
            overrides.get(relative, repo_root.parent / relative),
            byte_count, sha256, role,
        )
    try:
        rows = list(
            csv.DictReader(
                io.StringIO(
                    payloads["YUN_INCLUDE_PUBLISHED_MATRIX_PRECEDENT"].decode(
                        "utf-8"
                    )
                )
            )
        )
        formal = json.loads(payloads["YUN_INCLUDE_FORMAL_PRECEDENT"])
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OZJIngestionSafetyError("YUN_INCLUDE_PRECEDENT_PARSE_FAILED") from error
    training = formal.get("training_use_human_decision", {})
    if (
        training.get("D5_human_choice") != "INCLUDE"
        or training.get("human_training_excluded") is not False
        or training.get("training_use_include") is not True
        or training.get("future_training_admission_candidate") is not None
        or training.get("future_training_admission_candidate_status")
        != FORMAL_FUTURE_STATUS
        or training.get("formal_training_admitted") is not False
        or training.get("training_admission_created") is not False
    ):
        _fail("YUN_INCLUDE_FORMAL_NULL_DEFERRED_PRECEDENT_INVALID")
    if len(rows) != 7 or any(
        row.get("formal_event_training_use_decision") != "INCLUDE"
        or row.get("human_training_excluded") != "false"
        or row.get("training_use_allowed") != "true"
        or row.get("candidate_for_future_training_admission") != "true"
        or row.get("future_training_admission_status") != FUTURE_STATUS
        or row.get("future_training_candidate_derived_by_ingestion") != "true"
        or row.get("future_training_candidate_is_training_admission") != "false"
        or row.get("training_admitted") != "false"
        or row.get("training_materialization_allowed_now") != "false"
        or row.get("current_runtime_model_usable") != "false"
        for row in rows
    ):
        _fail("YUN_INCLUDE_INGESTION_DERIVATION_PRECEDENT_INVALID")
    return [
        *_binding_rows(
            INCLUDE_REPOSITORY_PRECEDENT_BINDINGS,
            namespace="repository_relative",
        ),
        *_binding_rows(
            INCLUDE_PARENT_PRECEDENT_BINDINGS,
            namespace="repository_parent_relative",
        ),
    ]

def _current_census_bindings(
    repo_root: Path, overrides: Mapping[Path, Path]
) -> list[dict[str, object]]:
    payloads: dict[Path, bytes] = {}
    for relative, byte_count, sha256, role in CURRENT_CENSUS_BINDINGS:
        payloads[relative] = _verify_payload(
            overrides.get(relative, repo_root / relative),
            byte_count,
            sha256,
            role,
        )
    csv_relative = CURRENT_CENSUS_BINDINGS[1][0]
    summary_relative = CURRENT_CENSUS_BINDINGS[2][0]
    try:
        rows = list(
            csv.DictReader(
                io.StringIO(payloads[csv_relative].decode("utf-8"))
            )
        )
        summary = json.loads(payloads[summary_relative])
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OZJIngestionSafetyError("CURRENT_CENSUS_PARSE_FAILED") from error
    authority = summary.get("authority_boundary", {})
    training = summary.get("training_stage", {})
    if (
        summary.get("schema_version")
        != "covapie_cumulative1000_current_global_readiness_census_with_cht_v1"
        or summary.get("chemistry", {}).get("POSITIVE", {}).get("count") != 100
        or summary.get("task_relevance", {}).get("RELEVANT", {}).get("count") != 101
        or summary.get("training_use", {})
        .get("EXCLUDE_FROM_TRAINING_ONLY", {})
        .get("count")
        != 64
        or training.get("training_use_include_count") != 36
        or training.get("future_training_admission_candidate_count") != 19
        or authority.get("next_priority_review_ligand") != "OZJ"
        or authority.get("next_priority_review_event_count") != 4
        or authority.get("next_priority_review_unit") != EXPECTED_REVIEW_UNIT_ID
    ):
        _fail("CURRENT_CENSUS_SUMMARY_BOUNDARY_INVALID")
    ozj = [row for row in rows if row.get("ligand_component_id") == "OZJ"]
    if (
        len(ozj) != 4
        or tuple(row.get("canonical_event_id") for row in ozj) != EXPECTED_EVENT_IDS
        or [int(row["scaleup_rank"]) for row in ozj] != list(EXPECTED_RANKS)
        or any(
            row.get("current_global_status") != "CURRENTLY_UNREVIEWED"
            or row.get("current_review_status") != "CURRENTLY_UNREVIEWED"
            or row.get("chemistry_disposition") != "UNRESOLVED"
            or row.get("task_relevance_disposition") != "UNRESOLVED"
            or row.get("training_use_disposition") != "UNRESOLVED"
            for row in ozj
        )
    ):
        _fail("CURRENT_CENSUS_OZJ_PRIOR_STATE_INVALID")
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
        formal_path,
        FORMAL_DECISION_BYTE_COUNT,
        FORMAL_DECISION_SHA256,
        "formal_OZJ_human_decision",
    )
    try:
        formal = json.loads(payload)
    except json.JSONDecodeError as error:
        raise OZJIngestionSafetyError("FORMAL_DECISION_JSON_INVALID") from error
    normalized = _validate_formal_decision_v1(formal)
    return {
        "formal": formal,
        "normalized": normalized,
        "formal_decision_binding": _formal_binding(),
        "frozen_review_package_bindings": _frozen_review_bindings(
            repo_root.parent,
            overrides,
        ),
        "immutable_semantic_owner_bindings": _semantic_owner_bindings(
            repo_root,
            overrides,
        ),
        "architecture_precedent_bindings": _architecture_precedent_bindings(
            repo_root,
            overrides,
        ),
        "include_semantic_precedent_bindings": _include_precedent_bindings(
            repo_root,
            overrides,
        ),
        "current_published_census_bindings": _current_census_bindings(
            repo_root,
            overrides,
        ),
    }


def _snapshot(bound: Mapping[str, Any]) -> dict[str, object]:
    normalized = bound["normalized"]
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "snapshot_role":
            "ADDITIVE_IMMUTABLE_OZJ_COMPLETED_HUMAN_DECISION_INGESTION",
        "snapshot_created_by_ingestion": True,
        "human_authority_ingested": True,
        "human_authority_created_by_ingestion": False,
        "future_training_candidate_derived_by_ingestion": True,
        "future_training_candidate_is_training_admission": False,
        "formal_decision_binding": bound["formal_decision_binding"],
        "frozen_preparation_exact6_provenance":
            bound["frozen_review_package_bindings"],
        "precedent_semantics": {
            "CHT_latest_ingestion_architecture_verified": True,
            "CHT_STRICT_Exact5_precedent_verified": True,
            "YUN_INCLUDE_formal_null_deferred_precedent_verified": True,
            "YUN_INCLUDE_ingestion_derived_true_precedent_verified": True,
            "adopted_separation": {
                "human_reviewer_approved_D5": "INCLUDE",
                "formal_future_training_admission_candidate": None,
                "formal_future_training_admission_candidate_status":
                    FORMAL_FUTURE_STATUS,
                "candidate_for_future_training_admission": True,
                "future_training_admission_status": FUTURE_STATUS,
                "future_training_candidate_derived_by_ingestion": True,
                "future_training_candidate_is_training_admission": False,
                "training_admitted": False,
            },
        },
        "reviewer_id": "fmx",
        "attestor_id": "fmx",
        "approved_at_utc": EXPECTED_APPROVED_AT_UTC,
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "ligand_component_id": "OZJ",
        "event_count": 4,
        "events": normalized["events"],
        "event_context_inventory": normalized["event_context_inventory"],
        "unit_level_D1_D6": {
            "D1": "RELEVANT",
            "D2": "POSITIVE",
            "D3": "CONFIRM_OBSERVED_PAIR",
            "D4": "SELECT_CANDIDATE_1",
            "D5": "INCLUDE",
            "D6": EXPECTED_D6,
        },
        "reactive_pair": {
            "human_decision_available": True,
            "human_authoritative": True,
            "authoritative_event_count": 4,
            "protein_reactive_atom": "SG",
            "ligand_reactive_atom": "CAF",
            "ligand_reactive_atom_element": "C",
            "pair": "CYS168_SG_TO_OZJ_CAF",
            "model_bound_pair_target_created": False,
            "tensor_target_created": False,
            "reusable_pair_authority_created": False,
            "training_admission_created": False,
        },
        "selected_role_partition": normalized["role"],
        "canonical_task_contract": _canonical_task_contract(),
        "scientific_context": normalized["scientific_context"],
        "frozen_OZJ_source_graph": _frozen_graph_snapshot(),
        "source_CCD_and_event_topology_boundary":
            normalized["source_ccd_and_event_topology_boundary"],
        "geometry_boundary": normalized["geometry_boundary"],
        "formal_training_use_source_boundary": {
            "formal_event_training_use_decision": "INCLUDE",
            "event_training_use_human_decision_available": True,
            "human_training_excluded": False,
            "training_use_allowed": True,
            "training_use_include": True,
            "future_training_admission_candidate": None,
            "future_training_admission_candidate_status": FORMAL_FUTURE_STATUS,
            "formal_training_admitted": False,
            "training_admission_created": False,
            "training_materialization_allowed_now": False,
            "training_materialization_performed": False,
            "formal_split_authority_created": False,
            "tensor_target_created": False,
            "runtime_model_usable": False,
            "parameter_update_authorization": False,
        },
        "downstream_ingestion_boundary": normalized["training_boundary"],
        "auxiliary_and_reusable_boundary": _reusable_boundary(),
        "current_published_global_boundary": {
            "published_global_positive_count_remains": 100,
            "published_task_relevant_count_remains": 101,
            "published_training_INCLUDE_count_remains": 36,
            "published_training_EXCLUDE_count_remains": 64,
            "published_future_training_candidate_count_remains": 19,
            "published_pair_authority_count_remains": 100,
            "published_role_authority_count_remains": 100,
            "current_published_OZJ_status": "CURRENTLY_UNREVIEWED",
            "global_reconciliation_update": "NOT_DONE",
            "global_census_update": "NOT_DONE",
        },
        "expected_future_census_derivation_informational_only": {
            "requires_future_OZJ_reconciliation_and_census_refresh": True,
            "chemistry_positive_expected": 104,
            "task_relevant_expected": 105,
            "training_INCLUDE_expected": 40,
            "training_EXCLUDE_expected": 64,
            "future_training_candidates_expected": 23,
            "sample_pair_expected": 104,
            "sample_role_expected": 104,
            "STRICT_expected": 48,
            "DIRECT_expected": 56,
            "canonical_exact5_expected": {
                "A": 104, "B": 48, "B2": 48, "B3": 104, "C": 104,
            },
            "completed_positive_human_review_expected": {
                "event_count": 87, "unit_count": 11,
            },
            "pending_expected": {"event_count": 227, "unit_count": 116},
            "materialized_as_current_global_state": False,
        },
        "downstream_non_actions": {
            "OZJ_reconciliation": "NOT_DONE_THIS_STEP",
            "global_census_refresh": "NOT_DONE_THIS_STEP",
            "formal_training_admission": "NOT_DONE_THIS_STEP",
            "split_tensor_model_training": "NOT_DONE_THIS_STEP",
            "feature_semantics_audit": "NOT_DONE_THIS_STEP",
        },
        "feature_semantics": {
            "status": "AUDIT_REQUIRED_LATER",
            "step12d_status":
                "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
            "audit_item": (
                "The human-approved 3-formylphenyl-mediated Cys168 context "
                "and source CAF-OAD DOUB evidence must not be converted without "
                "an independent feature-semantics audit into authoritative PRE "
                "topology, complete POST topology, reusable chemistry, or a "
                "training feature."
            ),
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
    "reactive_pair_human_decision_available",
    "reactive_pair_human_authoritative", "protein_reactive_atom",
    "ligand_reactive_atom", "ligand_reactive_atom_element",
    "role_partition_human_decision_available",
    "role_partition_human_authoritative",
    "selected_role_candidate_index_0based", "role_profile",
    "warhead_atoms_json", "linker_atoms_json", "scaffold_atoms_json",
    "boundary_bonds_json", "global_canonical_task_count",
    "canonical_task_applicability_json",
    "strict_profile_applicable_task_ids_json",
    "formal_event_training_use_decision",
    "event_training_use_human_decision_available",
    "human_training_excluded", "training_use_allowed", "training_use_include",
    "formal_future_training_admission_candidate",
    "formal_future_training_admission_candidate_status",
    "candidate_for_future_training_admission",
    "future_training_admission_status",
    "future_training_candidate_derived_by_ingestion",
    "future_training_candidate_is_training_admission",
    "training_admitted", "training_admission_created",
    "training_materialization_allowed_now", "current_runtime_model_usable",
    "formal_split_authority_created", "tensor_target_created",
    "parameter_update_authorization", "source_CAF_OAD_bond_order",
    "explicit_SG_CAF_connection_available",
    "complete_POST_adduct_topology_authority_available",
    "PRE_topology_authority_available", "PRE_geometry_authority_available",
    "POST_source_evidence_available",
    "POST_geometry_training_label_available_now",
    "reaction_family_target_available", "warhead_rule_target_available",
    "warhead_type_target_available",
    "reusable_chemistry_authority_available",
    "reusable_pair_authority_available", "reusable_role_authority_available",
    "authority_source", "authority_scope", "authority_ingested",
    "authority_created_by_this_ingestion",
)


def _matrix_rows(snapshot: Mapping[str, Any]) -> list[dict[str, object]]:
    role = _role_snapshot()
    applicability = _canonical_task_contract()[
        "strict_profile_task_applicability"
    ]
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
                "protein_altloc": ""
                if event["protein_altloc"] is None
                else event["protein_altloc"],
                "ligand_component_id": "OZJ",
                "ligand_chain_or_asym": event["ligand_chain_or_asym"],
                "ligand_altloc": ""
                if event["ligand_altloc"] is None
                else event["ligand_altloc"],
                "selected_connection_id": event["selected_connection_id"],
                "POST_distance_angstrom": event["POST_distance_frozen_lexeme"],
                "human_task_relevance_decision": "RELEVANT",
                "chemistry_known_positive": "true",
                "negative_chemistry": "false",
                "task_domain_negative": "false",
                "reactive_pair_human_decision_available": "true",
                "reactive_pair_human_authoritative": "true",
                "protein_reactive_atom": "SG",
                "ligand_reactive_atom": "CAF",
                "ligand_reactive_atom_element": "C",
                "role_partition_human_decision_available": "true",
                "role_partition_human_authoritative": "true",
                "selected_role_candidate_index_0based": "1",
                "role_profile": EXPECTED_ROLE_PROFILE,
                "warhead_atoms_json": _json_cell(list(EXPECTED_WARHEAD)),
                "linker_atoms_json": _json_cell(list(EXPECTED_LINKER)),
                "scaffold_atoms_json": _json_cell(list(EXPECTED_SCAFFOLD)),
                "boundary_bonds_json": _json_cell(role["boundary_bonds"]),
                "global_canonical_task_count": "5",
                "canonical_task_applicability_json": _json_cell(applicability),
                "strict_profile_applicable_task_ids_json": "[0,1,2,3,4]",
                "formal_event_training_use_decision": "INCLUDE",
                "event_training_use_human_decision_available": "true",
                "human_training_excluded": "false",
                "training_use_allowed": "true",
                "training_use_include": "true",
                "formal_future_training_admission_candidate": "null",
                "formal_future_training_admission_candidate_status":
                    FORMAL_FUTURE_STATUS,
                "candidate_for_future_training_admission": "true",
                "future_training_admission_status": FUTURE_STATUS,
                "future_training_candidate_derived_by_ingestion": "true",
                "future_training_candidate_is_training_admission": "false",
                "training_admitted": "false",
                "training_admission_created": "false",
                "training_materialization_allowed_now": "false",
                "current_runtime_model_usable": "false",
                "formal_split_authority_created": "false",
                "tensor_target_created": "false",
                "parameter_update_authorization": "false",
                "source_CAF_OAD_bond_order": "DOUB",
                "explicit_SG_CAF_connection_available": "true",
                "complete_POST_adduct_topology_authority_available": "false",
                "PRE_topology_authority_available": "false",
                "PRE_geometry_authority_available": "false",
                "POST_source_evidence_available": "true",
                "POST_geometry_training_label_available_now": "false",
                "reaction_family_target_available": "false",
                "warhead_rule_target_available": "false",
                "warhead_type_target_available": "false",
                "reusable_chemistry_authority_available": "false",
                "reusable_pair_authority_available": "false",
                "reusable_role_authority_available": "false",
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
        "event_count": 4,
        "task_relevant_count": 4,
        "chemistry_positive_count": 4,
        "OZJ_source_local_positive_count": 4,
        "source_local_positive_count": 4,
        "completed_human_positive_count": 4,
        "reactive_pair_human_authority_count": 4,
        "role_partition_human_authority_count": 4,
        "direct_profile_count": 0,
        "strict_profile_count": 4,
        "human_training_INCLUDE_count": 4,
        "human_training_EXCLUDE_count": 0,
        "training_use_allowed_count": 4,
        "formal_future_training_admission_candidate_count": 0,
        "formal_future_training_admission_candidate_status":
            FORMAL_FUTURE_STATUS,
        "future_training_admission_candidate_count": 4,
        "future_training_admission_status": FUTURE_STATUS,
        "future_training_candidate_derived_by_ingestion_count": 4,
        "future_training_candidate_is_training_admission": False,
        "training_admitted_count": 0,
        "formal_training_admitted_count": 0,
        "training_materialization_allowed_count": 0,
        "current_runtime_model_usable_count": 0,
        "POST_source_evidence_count": 4,
        "POST_geometry_training_authority_count": 0,
        "POST_geometry_training_target_count": 0,
        "PRE_geometry_authority_count": 0,
        "PRE_geometry_training_target_count": 0,
        "PRE_precursor_topology_authority_count": 0,
        "PRE_reconstruction_count": 0,
        "explicit_SG_CAF_connection_count": 4,
        "complete_POST_topology_authority_count": 0,
        "reaction_family_target_count": 0,
        "warhead_rule_target_count": 0,
        "warhead_type_target_count": 0,
        "reusable_chemistry_authority_available": False,
        "reusable_pair_authority_available": False,
        "reusable_role_authority_available": False,
        "global_canonical_task_count": 5,
        "strict_profile_applicable_task_count_per_event": 5,
        "formal_human_decision_ingested": True,
        "human_authority_created_by_ingestion": False,
        "completed_decision_ingestion_status": "DONE_THIS_STEP",
        "published_global_positive_count_remains": 100,
        "published_task_relevant_count_remains": 101,
        "published_training_INCLUDE_count_remains": 36,
        "published_training_EXCLUDE_count_remains": 64,
        "published_future_training_candidate_count_remains": 19,
        "published_pair_authority_count_remains": 100,
        "published_role_authority_count_remains": 100,
        "current_published_OZJ_status": "CURRENTLY_UNREVIEWED",
        "global_reconciliation_update_status": "NOT_DONE_THIS_STEP",
        "global_census_update_status": "NOT_DONE_THIS_STEP",
        "expected_future_census_derivation_informational_only": {
            "chemistry_positive": 104,
            "task_relevant": 105,
            "training_INCLUDE": 40,
            "training_EXCLUDE": 64,
            "future_candidates": 23,
            "sample_pair": 104,
            "sample_role": 104,
            "STRICT": 48,
            "DIRECT": 56,
            "A": 104,
            "B": 48,
            "B2": 48,
            "B3": 104,
            "C": 104,
            "completed_positive_human_review_events": 87,
            "completed_positive_human_review_units": 11,
            "pending_events": 227,
            "pending_units": 116,
        },
        "source_CAF_OAD_bond_order": "DOUB",
        "complete_POST_topology_authority_available": False,
        "PRE_topology_authority_available": False,
        "PRE_geometry_authority_available": False,
        "feature_semantics": "AUDIT_REQUIRED_LATER",
        "step12d_status":
            "SMOKE_LEGALITY_CHECK_NOT_FINAL_TRAINING_FEATURE_CONTRACT",
        "ready_for_OZJ_reconciliation_successor": True,
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
        raise OZJIngestionSafetyError("UTF8_INVALID:" + label) from error
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
                "path": relative.as_posix(),
                "path_namespace": "repository_relative",
                "byte_count": len(payload),
                "sha256": _sha(payload),
                "sha256_scope": "file_bytes",
                "source_role": role,
            }
        )
    return rows


def _expected_review_bindings() -> list[dict[str, object]]:
    return [
        {
            "path": path.as_posix(),
            "path_namespace": "project_parent_relative",
            "byte_count": count,
            "sha256": digest,
            "sha256_scope": "file_bytes",
            "source_role": role,
            "mode": mode,
            "verification_status": "MATCHED",
        }
        for path, count, digest, role, mode in FROZEN_REVIEW_PACKAGE_BINDINGS
    ]


def _expected_architecture_precedent_bindings() -> list[dict[str, object]]:
    return _binding_rows(
        ARCHITECTURE_PRECEDENT_BINDINGS,
        namespace="repository_relative",
    )


def _expected_include_bindings() -> list[dict[str, object]]:
    return [
        *_binding_rows(
            INCLUDE_REPOSITORY_PRECEDENT_BINDINGS,
            namespace="repository_relative",
        ),
        *_binding_rows(
            INCLUDE_PARENT_PRECEDENT_BINDINGS,
            namespace="repository_parent_relative",
        ),
    ]


def _expected_owner_bindings() -> list[dict[str, object]]:
    return _binding_rows(
        IMMUTABLE_SEMANTIC_OWNER_BINDINGS,
        namespace="repository_relative",
    )


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
            "event_context_inventory": _event_context_inventory(),
            "role": _role_snapshot(),
            "scientific_context": _scientific_context(),
            "source_ccd_and_event_topology_boundary": _source_ccd_and_event_topology_boundary(),
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
        "artifact_role": "OZJ_COMPLETED_DECISION_AND_EVENT_TASK_LABEL_AVAILABILITY_NOT_RECONCILIATION_OR_ADMISSION",
        "candidate_publication_file_count": 7,
        "output_artifact_count": 4,
        "source_path": SOURCE_RELATIVE.as_posix(),
        "checker_path": CHECKER_RELATIVE.as_posix(),
        "test_path": TEST_RELATIVE.as_posix(),
        "output_paths": [path.as_posix() for path in OUTPUT_RELATIVE_PATHS],
        "formal_decision_binding": bound["formal_decision_binding"],
        "frozen_formal_evidence_provenance": bound[
            "frozen_review_package_bindings"
        ],
        "architecture_precedent_bindings": bound["architecture_precedent_bindings"],
        "include_semantic_precedent_bindings": bound[
            "include_semantic_precedent_bindings"
        ],
        "immutable_semantic_owner_bindings": bound[
            "immutable_semantic_owner_bindings"
        ],
        "current_published_census_bindings": bound[
            "current_published_census_bindings"
        ],
        "current_published_census_boundary": {
            "published_global_positive_count_remains": 100,
            "published_task_relevant_count_remains": 101,
            "published_training_INCLUDE_count_remains": 36,
            "published_training_EXCLUDE_count_remains": 64,
            "published_future_training_candidate_count_remains": 19,
            "current_next_priority_review_ligand": "OZJ",
            "current_next_priority_review_event_count": 4,
            "current_OZJ_review_status": "CURRENTLY_UNREVIEWED",
            "global_reconciliation_update_status": "NOT_DONE_THIS_STEP",
            "global_census_update_status": "NOT_DONE_THIS_STEP",
        },
        "candidate_source_bindings": _candidate_source_bindings(repo_root),
        "canonical_task_contract": _canonical_task_contract(),
        "counts": {
            key: value
            for key, value in _summary().items()
            if type(value) is int and type(value) is not bool
        },
        "human_authority_ingestion_semantics": {
            "authority_source": AUTHORITY_SOURCE,
            "authority_scope": AUTHORITY_SCOPE,
            "authority_ingested": True,
            "authority_created_by_ingestion": False,
            "formal_event_training_use_decision": "INCLUDE",
            "human_training_excluded": False,
            "training_use_allowed": True,
            "training_use_include": True,
            "formal_future_training_admission_candidate": None,
            "formal_future_training_admission_candidate_status":
                FORMAL_FUTURE_STATUS,
            "candidate_for_future_training_admission": True,
            "future_training_admission_status": FUTURE_STATUS,
            "future_training_candidate_derived_by_ingestion": True,
            "future_training_candidate_is_training_admission": False,
            "training_admitted": False,
        },
        "source_CCD_and_topology_boundary": _source_ccd_and_event_topology_boundary(),
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
        "published_global_positive_count_remains": 100,
        "published_task_relevant_count_remains": 101,
        "published_training_INCLUDE_count_remains": 36,
        "published_training_EXCLUDE_count_remains": 64,
        "published_future_training_candidate_count_remains": 19,
        "expected_future_census_derivation_materialized": False,
        "feature_semantics_audit_required_before_formal_training": True,
        "step12d_is_only_smoke_legality_not_final_training_feature_contract": True,
        "ready_for_OZJ_reconciliation_successor": True,
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
        "generated_at",
        "generated_at_utc",
        "ingested_at",
        "ingested_at_utc",
        "hostname",
        "host_name",
        "pid",
        "process_id",
        "uuid",
        "git_head",
        "git_parent",
        "commit_subject",
        "origin_main",
        "ahead",
        "behind",
        "candidate_lifecycle_profile",
        "published_lifecycle_profile",
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
            "path",
            "path_namespace",
            "byte_count",
            "sha256",
            "sha256_scope",
            "source_role",
        }:
            _fail("MANIFEST_CANDIDATE_SOURCE_BINDING_SCHEMA_INVALID")
        if (
            observed["path"] != path
            or observed["path_namespace"] != "repository_relative"
            or type(observed["byte_count"]) is not int
            or observed["byte_count"] <= 0
            or type(observed["sha256"]) is not str
            or len(observed["sha256"]) != 64
            or any(
                character not in "0123456789abcdef"
                for character in observed["sha256"]
            )
            or observed["sha256_scope"] != "file_bytes"
            or observed["source_role"] != role
        ):
            _fail("MANIFEST_CANDIDATE_SOURCE_BINDING_INVALID:" + path)


def _validate_derived_projection_digests(
    artifacts: Mapping[str, bytes]
) -> None:
    for name, digest in (
        (SNAPSHOT, _EXPECTED_SNAPSHOT_SHA256_V1),
        (MATRIX, _EXPECTED_MATRIX_SHA256_V1),
        (SUMMARY, _EXPECTED_SUMMARY_SHA256_V1),
    ):
        if (
            len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
            or digest == "0" * 64
        ):
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
        matrix = list(
            csv.DictReader(io.StringIO(artifacts[MATRIX].decode("utf-8")))
        )
        summary = json.loads(artifacts[SUMMARY])
        manifest = json.loads(artifacts[MANIFEST])
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise OZJIngestionSafetyError("OUTPUT_PARSE_FAILED") from error
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
        len(matrix) != 4
        or tuple(row["canonical_event_id"] for row in matrix)
        != EXPECTED_EVENT_IDS
        or len({row["canonical_event_id"] for row in matrix}) != 4
        or [int(row["scaleup_rank"]) for row in matrix]
        != list(EXPECTED_RANKS)
    ):
        _fail("MATRIX_EXACT4_INVALID")
    required_true = (
        "chemistry_known_positive",
        "reactive_pair_human_decision_available",
        "reactive_pair_human_authoritative",
        "role_partition_human_decision_available",
        "role_partition_human_authoritative",
        "event_training_use_human_decision_available",
        "training_use_allowed", "training_use_include",
        "candidate_for_future_training_admission",
        "future_training_candidate_derived_by_ingestion",
        "explicit_SG_CAF_connection_available",
        "POST_source_evidence_available", "authority_ingested",
    )
    required_false = (
        "negative_chemistry", "task_domain_negative",
        "human_training_excluded",
        "future_training_candidate_is_training_admission",
        "training_admitted", "training_admission_created",
        "training_materialization_allowed_now",
        "current_runtime_model_usable", "formal_split_authority_created",
        "tensor_target_created", "parameter_update_authorization",
        "complete_POST_adduct_topology_authority_available",
        "PRE_topology_authority_available",
        "PRE_geometry_authority_available",
        "POST_geometry_training_label_available_now",
        "reaction_family_target_available",
        "warhead_rule_target_available", "warhead_type_target_available",
        "reusable_chemistry_authority_available",
        "reusable_pair_authority_available",
        "reusable_role_authority_available",
        "authority_created_by_this_ingestion",
    )
    for index, row in enumerate(matrix):
        if any(row[field] != "true" for field in required_true):
            _fail("MATRIX_REQUIRED_TRUE_FLAG_INVALID")
        if any(row[field] != "false" for field in required_false):
            _fail("MATRIX_REQUIRED_FALSE_FLAG_INVALID")
        applicability = json.loads(row["canonical_task_applicability_json"])
        expected = EXPECTED_EVENTS[index]
        if (
            row["pdb_id"] != "4CL8"
            or row["model_number"] != "1"
            or row["protein_chain_or_asym"] != expected[4]
            or row["cys_residue_id"] != "CYS:168-"
            or row["protein_altloc"] != ""
            or row["ligand_component_id"] != "OZJ"
            or row["ligand_chain_or_asym"] != expected[7]
            or row["ligand_altloc"] != ""
            or row["selected_connection_id"] != expected[9]
            or row["POST_distance_angstrom"] != expected[11]
            or row["human_task_relevance_decision"] != "RELEVANT"
            or row["protein_reactive_atom"] != "SG"
            or row["ligand_reactive_atom"] != "CAF"
            or row["ligand_reactive_atom_element"] != "C"
            or row["selected_role_candidate_index_0based"] != "1"
            or row["role_profile"] != EXPECTED_ROLE_PROFILE
            or json.loads(row["warhead_atoms_json"]) != list(EXPECTED_WARHEAD)
            or json.loads(row["linker_atoms_json"]) != list(EXPECTED_LINKER)
            or json.loads(row["scaffold_atoms_json"]) != list(EXPECTED_SCAFFOLD)
            or row["strict_profile_applicable_task_ids_json"]
            != "[0,1,2,3,4]"
            or row["formal_event_training_use_decision"] != "INCLUDE"
            or row["formal_future_training_admission_candidate"] != "null"
            or row["formal_future_training_admission_candidate_status"]
            != FORMAL_FUTURE_STATUS
            or row["future_training_admission_status"] != FUTURE_STATUS
            or row["source_CAF_OAD_bond_order"] != "DOUB"
            or len(applicability) != 5
            or [
                item["task_id"]
                for item in applicability
                if item["structurally_applicable"]
            ] != [0, 1, 2, 3, 4]
            or applicability[1]["semantic_long_name"]
            != "linker_plus_warhead"
            or applicability[2]["semantic_long_name"]
            != "scaffold_plus_warhead"
            or applicability[3]["semantic_long_name"] != "scaffold_only"
        ):
            _fail(
                "MATRIX_OZJ_PROVENANCE_CANDIDATE1_INCLUDE_OR_EXACT5_INVALID"
            )

    expected_manifest_keys = {
        "schema_version", "stage", "artifact_role",
        "candidate_publication_file_count", "output_artifact_count",
        "source_path", "checker_path", "test_path", "output_paths",
        "formal_decision_binding", "frozen_formal_evidence_provenance",
        "architecture_precedent_bindings",
        "include_semantic_precedent_bindings",
        "immutable_semantic_owner_bindings",
        "current_published_census_bindings",
        "current_published_census_boundary", "candidate_source_bindings",
        "canonical_task_contract", "counts",
        "human_authority_ingestion_semantics",
        "source_CCD_and_topology_boundary", "output_artifact_bindings",
        "manifest_self_sha256_recorded", "manifest_self_sha256_policy",
        "deterministic", "completed_decision_ingestion_status",
        "global_reconciliation_update_status",
        "global_census_update_status",
        "published_global_positive_count_remains",
        "published_task_relevant_count_remains",
        "published_training_INCLUDE_count_remains",
        "published_training_EXCLUDE_count_remains",
        "published_future_training_candidate_count_remains",
        "expected_future_census_derivation_materialized",
        "feature_semantics_audit_required_before_formal_training",
        "step12d_is_only_smoke_legality_not_final_training_feature_contract",
        "ready_for_OZJ_reconciliation_successor", "ready_for_training",
        "authority_boundary",
    }
    if type(manifest) is not dict or set(manifest) != expected_manifest_keys:
        _fail("MANIFEST_SCHEMA_INVALID")
    if (
        manifest["schema_version"] != MANIFEST_SCHEMA_VERSION
        or manifest["stage"] != SCHEMA_VERSION
        or manifest["artifact_role"]
        != "OZJ_COMPLETED_DECISION_AND_EVENT_TASK_LABEL_AVAILABILITY_NOT_RECONCILIATION_OR_ADMISSION"
        or manifest["candidate_publication_file_count"] != 7
        or manifest["output_artifact_count"] != 4
        or manifest["source_path"] != SOURCE_RELATIVE.as_posix()
        or manifest["checker_path"] != CHECKER_RELATIVE.as_posix()
        or manifest["test_path"] != TEST_RELATIVE.as_posix()
        or manifest["output_paths"]
        != [path.as_posix() for path in OUTPUT_RELATIVE_PATHS]
        or manifest["formal_decision_binding"] != _formal_binding()
        or manifest["frozen_formal_evidence_provenance"]
        != _expected_review_bindings()
        or manifest["architecture_precedent_bindings"]
        != _expected_architecture_precedent_bindings()
        or manifest["include_semantic_precedent_bindings"]
        != _expected_include_bindings()
        or manifest["immutable_semantic_owner_bindings"]
        != _expected_owner_bindings()
        or manifest["current_published_census_bindings"]
        != _expected_census_bindings()
        or manifest["canonical_task_contract"] != _canonical_task_contract()
        or manifest["source_CCD_and_topology_boundary"]
        != _source_ccd_and_event_topology_boundary()
        or manifest["authority_boundary"] != _authority_boundary()
        or manifest["manifest_self_sha256_recorded"] is not False
        or manifest["manifest_self_sha256_policy"] != "SELF_SHA256_PROHIBITED"
        or manifest["deterministic"] is not True
        or manifest["completed_decision_ingestion_status"] != "DONE_THIS_STEP"
        or manifest["global_reconciliation_update_status"]
        != "NOT_DONE_THIS_STEP"
        or manifest["global_census_update_status"] != "NOT_DONE_THIS_STEP"
        or manifest["published_global_positive_count_remains"] != 100
        or manifest["published_task_relevant_count_remains"] != 101
        or manifest["published_training_INCLUDE_count_remains"] != 36
        or manifest["published_training_EXCLUDE_count_remains"] != 64
        or manifest["published_future_training_candidate_count_remains"] != 19
        or manifest["expected_future_census_derivation_materialized"]
        is not False
        or manifest["feature_semantics_audit_required_before_formal_training"]
        is not True
        or manifest[
            "step12d_is_only_smoke_legality_not_final_training_feature_contract"
        ] is not True
        or manifest["ready_for_OZJ_reconciliation_successor"] is not True
        or manifest["ready_for_training"] is not False
    ):
        _fail("MANIFEST_BOUNDARY_OR_SOURCE_BINDING_INVALID")
    if manifest["current_published_census_boundary"] != {
        "published_global_positive_count_remains": 100,
        "published_task_relevant_count_remains": 101,
        "published_training_INCLUDE_count_remains": 36,
        "published_training_EXCLUDE_count_remains": 64,
        "published_future_training_candidate_count_remains": 19,
        "current_next_priority_review_ligand": "OZJ",
        "current_next_priority_review_event_count": 4,
        "current_OZJ_review_status": "CURRENTLY_UNREVIEWED",
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
        key: value
        for key, value in _summary().items()
        if type(value) is int and type(value) is not bool
    }:
        _fail("MANIFEST_COUNTS_INVALID")
    if manifest["human_authority_ingestion_semantics"] != {
        "authority_source": AUTHORITY_SOURCE,
        "authority_scope": AUTHORITY_SCOPE,
        "authority_ingested": True,
        "authority_created_by_ingestion": False,
        "formal_event_training_use_decision": "INCLUDE",
        "human_training_excluded": False,
        "training_use_allowed": True,
        "training_use_include": True,
        "formal_future_training_admission_candidate": None,
        "formal_future_training_admission_candidate_status":
            FORMAL_FUTURE_STATUS,
        "candidate_for_future_training_admission": True,
        "future_training_admission_status": FUTURE_STATUS,
        "future_training_candidate_derived_by_ingestion": True,
        "future_training_candidate_is_training_admission": False,
        "training_admitted": False,
    }:
        _fail("MANIFEST_HUMAN_AUTHORITY_BOUNDARY_INVALID")
    _validate_derived_projection_digests(artifacts)
    if repo_root is not None:
        repo_root = repo_root.resolve()
        bound = load_frozen_formal_decision_v1(repo_root)
        if snapshot != _snapshot(bound):
            _fail("SNAPSHOT_DIRECT_FORMAL_SOURCE_PROJECTION_INVALID")
        if manifest["candidate_source_bindings"] != _candidate_source_bindings(
            repo_root
        ):
            _fail("MANIFEST_CANDIDATE_SOURCE_BINDINGS_INVALID")

def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def materialize_artifacts_v1(
    repo_root: Path, *, output_root: Path | None = None
) -> dict[str, bytes]:
    """Build and atomically materialize only the Exact4 outputs."""

    repo_root = repo_root.resolve()
    artifacts = build_artifacts_v1(repo_root)
    destination = (
        output_root.resolve()
        if output_root is not None
        else repo_root / OUTPUT_ROOT_RELATIVE
    )
    if destination.exists():
        unexpected = {
            path.name
            for path in destination.iterdir()
            if path.name not in OUTPUT_FILENAMES
        }
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
        "artifact_sha256": {
            name: _sha(observed[name]) for name in OUTPUT_FILENAMES
        },
        "formal_decision_sha256": FORMAL_DECISION_SHA256,
        "event_count": 4,
        "chemistry_positive_count": 4,
        "human_training_INCLUDE_count": 4,
        "training_use_allowed_count": 4,
        "future_training_admission_candidate_count": 4,
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
    print("event_count=4")
    print("chemistry_positive_count=4")
    print("human_training_INCLUDE_count=4")
    print("training_use_allowed_count=4")
    print("future_training_admission_candidate_count=4")
    print("training_admitted_count=0")
    print("published_global_positive_count_remains=100")
    print("published_training_INCLUDE_count_remains=36")
    print("published_future_training_candidate_count_remains=19")
    print("ready_for_training=false")
    for name in OUTPUT_FILENAMES:
        print(name + "_sha256=" + _sha(artifacts[name]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
