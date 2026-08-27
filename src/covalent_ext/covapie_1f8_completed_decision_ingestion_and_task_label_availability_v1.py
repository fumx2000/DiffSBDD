"""Ingest the frozen 1F8 Exact8 human decision as deterministic metadata.

This additive projection validates and ingests authority already present in the
formal human decision.  It does not reinterpret 1F8 chemistry, create reusable
authority, reconstruct PRE topology or geometry, reconcile global state, admit
training samples, tensorize data, execute a model, or train parameters.
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
    "OneF8IngestionSafetyError",
    "load_frozen_formal_decision_v1",
    "validate_completed_decision_projection_v1",
    "build_artifacts_v1",
    "materialize_artifacts_v1",
    "check_materialized_v1",
)

SCHEMA_VERSION = (
    "covapie_1f8_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT_SCHEMA_VERSION = "covapie_1f8_completed_human_decision_snapshot_v1"
MATRIX_SCHEMA_VERSION = "covapie_1f8_event_task_label_availability_v1"
SUMMARY_SCHEMA_VERSION = "covapie_1f8_completed_decision_ingestion_summary_v1"
MANIFEST_SCHEMA_VERSION = "covapie_1f8_completed_decision_ingestion_manifest_v1"

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_1f8_completed_decision_ingestion_and_task_label_availability_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/"
    "check_covapie_1f8_completed_decision_ingestion_and_task_label_availability_v1.py"
)
TEST_RELATIVE = Path(
    "tests/"
    "test_covapie_1f8_completed_decision_ingestion_and_task_label_availability_v1.py"
)
OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_1f8_completed_decision_ingestion_and_task_label_availability_v1"
)
SNAPSHOT = "covapie_1f8_completed_human_decision_snapshot_v1.json"
MATRIX = "covapie_1f8_event_task_label_availability_v1.csv"
SUMMARY = "covapie_1f8_completed_decision_ingestion_summary_v1.json"
MANIFEST = "covapie_1f8_completed_decision_ingestion_manifest_v1.json"
OUTPUT_FILENAMES = (SNAPSHOT, MATRIX, SUMMARY, MANIFEST)
OUTPUT_RELATIVE_PATHS = tuple(OUTPUT_ROOT_RELATIVE / name for name in OUTPUT_FILENAMES)
CANDIDATE_PUBLICATION_PATHS = (
    SOURCE_RELATIVE,
    CHECKER_RELATIVE,
    TEST_RELATIVE,
    *OUTPUT_RELATIVE_PATHS,
)

# Frozen only after semantic validation of the fully source-derived projection.
# These are projection-contract digests, never human or chemistry authority.
_EXPECTED_SNAPSHOT_SHA256_V1 = (
    "6bb77da9f93e541ba8eb2ad9a048aeabc1fc198189055259fe6610ec62da9281"
)
_EXPECTED_MATRIX_SHA256_V1 = (
    "63520f56ddb1c9fa9f962fc79c009549897e18299139e6b160498ca48080fb30"
)
_EXPECTED_SUMMARY_SHA256_V1 = (
    "4dbf12efd1000bc29bb049052d868223ff12dd78743220062aa6895523444e93"
)

FORMAL_DECISION_RELATIVE_TO_REPOSITORY_PARENT = Path(
    "covapie-state/manual-review-aids/"
    "cumulative1000-high-yield-calibration-v1/"
    "1F8_COVAPIE_BULK_REVIEW_UNIT_9723B0F9EC07CC81/"
    "formal-human-decision-v1/1f8_formal_human_decision_v1.json"
)
FORMAL_DECISION_BYTE_COUNT = 31063
FORMAL_DECISION_SHA256 = (
    "6a73022e20e2562f95197b9f314b92b0ecead1cebbadf1c17d5ca292eee59e96"
)
FORMAL_DECISION_SCHEMA = "covapie_1f8_exact8_formal_human_decision_v1"
FORMAL_SEMANTIC_CANONICAL_SHA256 = (
    "7d9a7779b56fdd225bb25a1c3671b6e25d76e1c691b191a32875bd00400f6c64"
)
EXPECTED_REVIEW_UNIT_ID = "COVAPIE_BULK_REVIEW_UNIT_9723B0F9EC07CC81"
EXPECTED_APPROVED_AT_UTC = "2026-08-26T15:39:36Z"
EXPECTED_ROLE_PROFILE = "STRICT_LINKER_PRESENT_V1"
EXPECTED_CANDIDATE_ID = "1F8_GRAPH_LOCAL_CANDIDATE_07"
EXPECTED_D6 = (
    "engineered PDK1 T148C allosteric disulfide-trapping inhibitor / "
    "observed retained-fragment context; no event-specific disposition exception"
)
AUTHORITY_SOURCE = "FORMAL_1F8_HUMAN_DECISION"
AUTHORITY_SCOPE = "SAMPLE_LEVEL_1F8_EXACT8_ONLY"
HUMAN_CONTEXT_SCOPE = "SAMPLE_SPECIFIC_1F8_EXACT8_ONLY"

EXPECTED_EVENTS = (
    ("COVAPIE_CYS_SG_EVENT_V1:3ORX:A:CYS:148-:SG:I:1F8:SD", 499, "3ORX", 1, "A", "CYS:148-", None, "I", None, "covale1", 2.013127, "2.013127"),
    ("COVAPIE_CYS_SG_EVENT_V1:3ORX:B:CYS:148-:SG:K:1F8:SD", 500, "3ORX", 1, "B", "CYS:148-", None, "K", None, "covale4", 2.012284, "2.012284"),
    ("COVAPIE_CYS_SG_EVENT_V1:3ORX:C:CYS:148-:SG:M:1F8:SD", 501, "3ORX", 1, "C", "CYS:148-", None, "M", None, "covale7", 2.012909, "2.012909"),
    ("COVAPIE_CYS_SG_EVENT_V1:3ORX:D:CYS:148-:SG:O:1F8:SD", 502, "3ORX", 1, "D", "CYS:148-", None, "O", None, "covale10", 2.015611, "2.015611"),
    ("COVAPIE_CYS_SG_EVENT_V1:3ORX:E:CYS:148-:SG:Q:1F8:SD", 503, "3ORX", 1, "E", "CYS:148-", None, "Q", None, "covale13", 2.006085, "2.006085"),
    ("COVAPIE_CYS_SG_EVENT_V1:3ORX:F:CYS:148-:SG:R:1F8:SD", 504, "3ORX", 1, "F", "CYS:148-", None, "R", None, "covale14", 2.009122, "2.009122"),
    ("COVAPIE_CYS_SG_EVENT_V1:3ORX:G:CYS:148-:SG:S:1F8:SD", 505, "3ORX", 1, "G", "CYS:148-", None, "S", None, "covale16", 2.007103, "2.007103"),
    ("COVAPIE_CYS_SG_EVENT_V1:3ORX:H:CYS:148-:SG:T:1F8:SD", 506, "3ORX", 1, "H", "CYS:148-", None, "T", None, "covale18", 2.007699, "2.007699"),
)
EXPECTED_EVENT_IDS = tuple(row[0] for row in EXPECTED_EVENTS)
EXPECTED_RANKS = tuple(row[1] for row in EXPECTED_EVENTS)

EXPECTED_HEAVY_ATOMS = (
    "C15", "C16", "C18", "C20", "C21", "C22", "C24", "C25",
    "C26", "C27", "C28", "C29", "N17", "O19", "O23", "SD",
)
EXPECTED_WARHEAD = ("SD",)
EXPECTED_LINKER = ("C15", "C16", "N17")
EXPECTED_SCAFFOLD = (
    "C18", "C20", "C21", "C22", "C24", "C25", "C26", "C27",
    "C28", "C29", "O19", "O23",
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
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/1F8_COVAPIE_BULK_REVIEW_UNIT_9723B0F9EC07CC81/review-preparation-v1/1f8_machine_evidence_manifest_v1.json"), 14376, "08893a01024915f0f2ba3a162120b21275fed2be6b7f87deaefaea60be14f384", "1F8_MACHINE_EVIDENCE_MANIFEST_REVIEWED_BYTES", "0644"),
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/1F8_COVAPIE_BULK_REVIEW_UNIT_9723B0F9EC07CC81/review-preparation-v1/1f8_exact8_event_review_v1.csv"), 6397, "5a09f1b84f9dd5007ba1006d20e02abc445bbb9add12c690eaad9dd244fc0fc9", "1F8_EXACT8_EVENT_REVIEWED_BYTES", "0644"),
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/1F8_COVAPIE_BULK_REVIEW_UNIT_9723B0F9EC07CC81/review-preparation-v1/1f8_graph_and_role_candidates_v1.json"), 21184, "126505746b611881b22278c6745d54a944de753a2124291f215f0b25ba12a8c9", "1F8_GRAPH_AND_ROLE_CANDIDATES_REVIEWED_BYTES", "0644"),
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/1F8_COVAPIE_BULK_REVIEW_UNIT_9723B0F9EC07CC81/review-preparation-v1/HUMAN_REVIEW_GUIDE.md"), 5164, "79780b2d6a506c70cd6450d308d1d569b7aa579af5d2be337b4fd5f5cda050d9", "1F8_HUMAN_REVIEW_GUIDE_REVIEWED_BYTES", "0644"),
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/1F8_COVAPIE_BULK_REVIEW_UNIT_9723B0F9EC07CC81/review-preparation-v1/1f8_unsigned_human_decision_template_v1.json"), 8144, "abd6c583b184561e9525d538ba9fda109ccfa34815d15014288d6ea743f3c4ab", "1F8_UNSIGNED_DECISION_TEMPLATE_REVIEWED_BYTES", "0644"),
    (Path("covapie-state/manual-review-aids/cumulative1000-high-yield-calibration-v1/1F8_COVAPIE_BULK_REVIEW_UNIT_9723B0F9EC07CC81/review-preparation-v1/ligand_1f8_review_package_v1.py"), 88849, "3fe962d32533281d386dd663a1d54f291407de0868d97231343e4df390c64bca", "1F8_REVIEW_PACKAGE_VALIDATOR_REVIEWED_BYTES", "0755"),
)

CURRENT_CENSUS_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_2vs_v1"
)
CURRENT_CENSUS_BINDINGS = (
    (Path("src/covalent_ext/covapie_cumulative1000_current_global_readiness_census_with_2vs_v1.py"), 54575, "0d574a3ae76caca7d6c90a226382a55f3f26e1fe9c229cf76ac1c10cdc3f3c47", "current_2VS_refreshed_census_owner"),
    (CURRENT_CENSUS_ROOT / "covapie_cumulative1000_current_global_readiness_census_with_2vs_v1.csv", 510436, "e0e4eb86d2961e2db2ca139ffe5492cfe9675b768826be85a3d0516b532ae24a", "current_2VS_refreshed_census_csv"),
    (CURRENT_CENSUS_ROOT / "covapie_cumulative1000_current_global_readiness_summary_with_2vs_v1.json", 14888, "1b5cca68c2b81426cfae86921a666d8766dc40d31032c24ba90888f0b88588f7", "current_2VS_refreshed_census_summary"),
    (CURRENT_CENSUS_ROOT / "covapie_cumulative1000_current_global_readiness_manifest_with_2vs_v1.json", 28229, "ff6aaf5a9be58628dc859639f0558f970a50585213db4d2095012072940a031a", "current_2VS_refreshed_census_manifest"),
)

EXPECTED_SCIENTIFIC_CONTEXT_TEXT = (
    "1F8 Exact8 represents the observed covalent allosteric disulfide-trapping "
    "complex of engineered PDK1 T148C with inhibitory fragment 1F8 in the "
    "allosteric/PIF-pocket context. The observed protein-ligand covalent pair is "
    "Cys148 SG ↔ 1F8 SD. The frozen PDB/CCD 1F8 component represents the retained "
    "protein-bound fragment after the disulfide-trapping reaction. The observed "
    "frozen 1F8 graph is not treated as authoritative complete pre-reaction "
    "disulfide reagent or precursor topology. The pre-reaction disulfide-trapping "
    "reagent contains reaction-partner topology that is not represented as complete "
    "authoritative PRE topology in the observed frozen CCD component. Cys148 is an "
    "engineered T148C site rather than a native PDK1 cysteine site. This is a "
    "chemistry-positive covalent allosteric inhibitor example, but the present V1 "
    "decision excludes the Exact8 from training because the observed retained-fragment "
    "graph does not by itself establish the complete authoritative PRE disulfide "
    "reagent topology for training. No event-specific disposition exception is "
    "applied. No reusable reaction-family, warhead-rule, warhead-type, PRE-geometry, "
    "PRE precursor-topology, cross-sample reusable chemistry, or training-admission "
    "authority is created."
)


class OneF8IngestionSafetyError(ValueError):
    """Raised when the frozen 1F8 ingestion contract cannot be proven."""


def _fail(reason: str) -> None:
    raise OneF8IngestionSafetyError(reason)


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


def _csv_bytes(
    header: Sequence[str], rows: Sequence[Mapping[str, object]]
) -> bytes:
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
    path: Path, expected_bytes: int, expected_sha256: str, label: str
) -> bytes:
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise OneF8IngestionSafetyError(
            "BOUND_SOURCE_READ_FAILED:" + label
        ) from error
    if len(payload) != expected_bytes:
        _fail("BOUND_SOURCE_BYTE_COUNT_MISMATCH:" + label)
    if _sha(payload) != expected_sha256:
        _fail("BOUND_SOURCE_SHA256_MISMATCH:" + label)
    return payload


def _literal_assignments(path: Path, names: Sequence[str]) -> dict[str, object]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, SyntaxError) as error:
        raise OneF8IngestionSafetyError(
            "SOURCE_AST_READ_FAILED:" + path.name
        ) from error
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
                    raise OneF8IngestionSafetyError(
                        "SOURCE_CONTRACT_NOT_LITERAL:" + target.id
                    ) from error
    if set(values) != wanted:
        _fail("SOURCE_CONTRACT_ASSIGNMENTS_MISSING")
    return values


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
        "ligand_component_id": "1F8",
        "reviewer_id": "fmx",
        "attestor_id": "fmx",
        "approved_at_utc": EXPECTED_APPROVED_AT_UTC,
        "verification_status": "MATCHED",
    }


def _expected_evidence_provenance() -> list[dict[str, object]]:
    # This project_parent_relative namespace is frozen inside the formal source.
    # It is deliberately distinct from the ingestion binding above.
    return [
        {
            "source_role": role,
            "path": path.as_posix(),
            "path_namespace": "project_parent_relative",
            "byte_count": byte_count,
            "sha256": sha256,
            "sha256_scope": "file_bytes",
            "mode": mode,
            "predecessor_immutable": True,
            "verification_status": "MATCHED",
        }
        for path, byte_count, sha256, role, mode in FROZEN_REVIEW_PACKAGE_BINDINGS
    ]


def _expected_human_approval() -> dict[str, object]:
    return {
        "approval_recorded": True,
        "approved": True,
        "approved_at_utc": EXPECTED_APPROVED_AT_UTC,
        "reviewer_id": "fmx",
        "attestor_id": "fmx",
        "reviewer_provenance_attested": True,
        "attestation": "D1-D6_EXPLICITLY_AUTHORIZED_AS_RECORDED",
        "authorization_source": "EXTERNAL_EXPLICIT_HUMAN_APPROVAL",
        "overall_decision": "APPROVE_1F8_EXACT8_D1_D6_SAMPLE_LEVEL_DECISIONS",
        "human_choices_externally_authorized": True,
        "unsigned": False,
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
        distance_lexeme,
    ) = row
    return {
        "canonical_event_id": event_id,
        "scaleup_rank": rank,
        "pdb_id": pdb_id,
        "model_number": model_number,
        "protein_chain_or_asym": protein_chain,
        "cys_residue_id": residue_id,
        "protein_altloc": protein_altloc,
        "ligand_component_id": "1F8",
        "ligand_chain_or_asym": ligand_chain,
        "ligand_altloc": ligand_altloc,
        "selected_connection_id": connection,
        "POST_distance_angstrom": distance,
        "POST_distance_frozen_lexeme": distance_lexeme,
        "D1_human_task_relevance_decision": "RELEVANT",
        "D2_human_chemistry_support_disposition": "POSITIVE",
        "negative_chemistry": False,
        "task_domain_negative": False,
        "D3_human_reactive_pair_decision": "CONFIRM_OBSERVED_PAIR",
        "protein_reactive_atom": "SG",
        "ligand_reactive_atom": "SD",
        "ligand_reactive_atom_element": "S",
        "reactive_pair_human_authoritative": True,
        "D4_human_role_partition_choice": "SELECT_CANDIDATE_7",
        "selected_role_candidate_index_0based": 7,
        "role_partition_human_authoritative": True,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "D5_human_training_use_disposition": "EXCLUDE_FROM_TRAINING_ONLY",
        "human_training_excluded": True,
        "training_admitted": False,
        "D6_context_reference": "UNIT_LEVEL_HUMAN_APPROVED_CONTEXT",
        "event_specific_disposition_exception": False,
        "decision_finalized": True,
    }


def _event_projection(raw: Mapping[str, object]) -> dict[str, object]:
    projected = dict(raw)
    projected.update(
        {
            "task_relevant": True,
            "chemistry_known_positive": True,
            "reactive_pair_human_decision_available": True,
            "role_partition_human_decision_available": True,
            "training_use_human_decision_available": True,
            "training_use_allowed": False,
            "POST_source_evidence_available": True,
            "POST_source_provenance": "FROZEN_FORMAL_EVENT_AND_BOUND_REVIEW_PACKAGE",
            "POST_geometry_training_label_available_now": False,
            "PRE_geometry_authority_available": False,
            "PRE_geometry_training_label_available_now": False,
            "PRE_precursor_topology_authority_available": False,
            "complete_PRE_disulfide_reagent_authority_available": False,
            "PRE_precursor_reconstruction_performed": False,
            "reaction_family_target_available": False,
            "warhead_rule_target_available": False,
            "warhead_type_target_available": False,
            "reusable_chemistry_authority_available": False,
            "reusable_pair_authority_available": False,
            "reusable_role_authority_available": False,
            "complete_PRE_warhead_authority_available": False,
            "candidate_for_future_training_admission": False,
            "training_materialization_allowed_now": False,
            "current_runtime_model_usable": False,
            "model_bound_pair_target_created_by_ingestion": False,
            "tensor_target_created": False,
            "training_admission_created": False,
            "authority_source": AUTHORITY_SOURCE,
            "authority_scope": AUTHORITY_SCOPE,
            "authority_ingested": True,
            "authority_created_by_this_ingestion": False,
        }
    )
    return projected


def _role_snapshot() -> dict[str, object]:
    return {
        "selected_candidate_index_0based": 7,
        "selected_candidate_id": EXPECTED_CANDIDATE_ID,
        "role_profile": EXPECTED_ROLE_PROFILE,
        "exact_heavy_atom_count": 16,
        "exact_heavy_atom_ids": list(EXPECTED_HEAVY_ATOMS),
        "warhead_atoms": list(EXPECTED_WARHEAD),
        "linker_atoms": list(EXPECTED_LINKER),
        "scaffold_atoms": list(EXPECTED_SCAFFOLD),
        "boundary_bonds": [
            {
                "atom_id_1": "C15",
                "atom_id_2": "SD",
                "bond_order": "SING",
                "boundary_between_roles": ["linker", "warhead"],
            },
            {
                "atom_id_1": "C18",
                "atom_id_2": "N17",
                "bond_order": "SING",
                "boundary_between_roles": ["scaffold", "linker"],
            },
        ],
        "heavy_atom_disjoint": True,
        "heavy_atom_exhaustive": True,
        "warhead_connected": True,
        "linker_empty": False,
        "linker_connected": True,
        "linker_atoms_on_scaffold_warhead_paths": True,
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
            "structurally_applicable": True,
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
    }


def _scientific_context() -> dict[str, object]:
    return {
        "D6_exact_choice": EXPECTED_D6,
        "scope": HUMAN_CONTEXT_SCOPE,
        "scientific_context_scope": HUMAN_CONTEXT_SCOPE,
        "human_approved_scientific_context": EXPECTED_SCIENTIFIC_CONTEXT_TEXT,
        "engineered_target_site": "PDK1_T148C",
        "native_cysteine_site": False,
        "medicinal_covalent_inhibitor_context": True,
        "allosteric_inhibitor_context": True,
        "disulfide_trapping_context": True,
        "observed_retained_fragment_context": True,
        "event_specific_disposition_exception": False,
        "event_specific_disposition_exception_count": 0,
    }


def _observed_graph_pre_boundary() -> dict[str, object]:
    return {
        "observed_graph_identity": "1F8_FROZEN_OBSERVED_RETAINED_FRAGMENT_HEAVY_ATOM_GRAPH",
        "observed_reactive_atom": "SD",
        "observed_reactive_atom_element": "S",
        "observed_graph_heavy_atom_count": 16,
        "observed_graph_connected_component_count": 1,
        "observed_reactive_atom_one_hop_neighbors": ["C15"],
        "observed_reactive_atom_exact_two_hop_neighbors": ["C16"],
        "processing_graph_digest": "39530d2538d25f1a29011ee7368e340d31ffd44242aa4351aea5681aeedbd9e7",
        "canonical_heavy_graph_digest": "c994655c10ed258e5f92ea16daebabedfe7c28a25a2b1a8c86de6f065d69d332",
        "observed_graph_represents_retained_fragment": True,
        "observed_graph_is_complete_authoritative_PRE_reagent": False,
        "observed_graph_is_authoritative_PRE_geometry": False,
        "observed_graph_is_authoritative_PRE_precursor_topology": False,
        "authoritative_PRE_precursor_topology": None,
        "authoritative_complete_PRE_disulfide_reagent_topology": None,
        "PRE_precursor_topology_authority_created": False,
        "PRE_complete_disulfide_reagent_authority_created": False,
        "PRE_precursor_reconstruction_performed": False,
        "PRE_geometry_authority_created": False,
        "human_selected_observed_warhead_atoms": ["SD"],
        "complete_PRE_warhead_topology_authority_created": False,
        "reusable_warhead_rule_created": False,
        "warhead_type_authority_created": False,
    }


def _formal_authority_boundary() -> dict[str, object]:
    return {
        "formal_sample_level_authority_created": True,
        "task_relevance_sample_level_human_authority_created": True,
        "chemistry_sample_level_human_authority_created": True,
        "human_sample_level_reactive_pair_authority_created": True,
        "human_sample_level_role_partition_authority_created": True,
        "human_sample_level_training_use_authority_created": True,
        "reactive_pair_human_authoritative": True,
        "role_partition_human_authoritative": True,
        "human_choices_externally_authorized": True,
        "machine_auto_selection_performed": False,
        "machine_recommended_candidate": None,
        "POST_geometry_training_authority_created": False,
        "POST_geometry_training_target_created": False,
        "PRE_geometry_authority_created": False,
        "PRE_precursor_topology_authority_created": False,
        "PRE_complete_disulfide_reagent_authority_created": False,
        "PRE_precursor_reconstruction_performed": False,
        "complete_PRE_warhead_topology_authority_created": False,
        "reaction_family_authority_created": False,
        "warhead_rule_authority_created": False,
        "warhead_type_authority_created": False,
        "reusable_chemistry_authority_created": False,
        "reusable_reactive_pair_authority_created": False,
        "reusable_role_authority_created": False,
        "training_admission_created": False,
        "training_admitted": False,
        "training_dataset_changed": False,
        "completed_decision_ingestion_performed": False,
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
        "model_training_activation_authorized": False,
        "ready_for_training": False,
        "repository_modified": False,
        "network_accessed": False,
        "scientific_network_acquisition_performed": False,
        "commit_performed": False,
        "push_performed": False,
    }


def _validate_formal_decision_v1(formal: Mapping[str, Any]) -> dict[str, object]:
    expected_keys = {
        "schema_version", "record_role", "decision_status", "review_unit_id",
        "ligand_component_id", "exact_event_count", "unique_event_count",
        "duplicate_event_count", "omitted_event_count", "extra_event_count",
        "ranks", "pdb_ids", "canonical_event_ids", "reviewer_id", "attestor_id",
        "approved", "unsigned", "human_review_completed", "human_decision_created",
        "human_review_decision_created", "human_approval_recorded",
        "formal_authority_created", "human_approval", "evidence_provenance",
        "prior_review_state", "unit_level_human_decisions",
        "event_level_human_decisions", "reactive_pair_human_decision",
        "selected_role_partition", "human_approved_context",
        "observed_graph_pre_boundary", "geometry_boundary",
        "training_use_human_decision", "reaction_family_authority",
        "warhead_rule_authority", "warhead_type_authority",
        "reusable_authority_boundary", "authority_boundary", "downstream_status",
        "feature_semantics_status", "training_admitted", "ready_for_training",
    }
    if set(formal) != expected_keys:
        _fail("FORMAL_TOP_LEVEL_FIELD_SET_INVALID")
    expected_top = {
        "schema_version": FORMAL_DECISION_SCHEMA,
        "record_role": "COMPLETED_SAMPLE_LEVEL_HUMAN_DECISION_NO_REUSABLE_AUTHORITY",
        "decision_status": "HUMAN_APPROVED_SAMPLE_LEVEL_DECISION",
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "ligand_component_id": "1F8",
        "exact_event_count": 8,
        "unique_event_count": 8,
        "duplicate_event_count": 0,
        "omitted_event_count": 0,
        "extra_event_count": 0,
        "ranks": list(EXPECTED_RANKS),
        "pdb_ids": ["3ORX"],
        "canonical_event_ids": list(EXPECTED_EVENT_IDS),
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
        if formal.get(field) != expected:
            _fail("FORMAL_TOP_LEVEL_SEMANTICS_INVALID:" + field)
    if formal.get("human_approval") != _expected_human_approval():
        _fail("FORMAL_HUMAN_APPROVAL_FIELDS_INVALID")
    if formal.get("evidence_provenance") != _expected_evidence_provenance():
        _fail("FORMAL_EVIDENCE_PROVENANCE_DRIFT")

    prior = formal.get("prior_review_state")
    if type(prior) is not dict or prior != {
        "prior_review_status": "CURRENTLY_UNREVIEWED",
        "prior_review_inventory_status": "CURRENTLY_UNREVIEWED_NO_PRIOR_1F8_REVIEW_WORK_FOUND",
        "prior_formal_human_decision_found": False,
        "prior_signed_human_decision_found": False,
        "prior_partial_authority_found": False,
        "prior_authority_source_paths": [],
        "current_authorization_source": "EXTERNAL_EXPLICIT_HUMAN_APPROVAL",
        "reviewer_id": "fmx",
        "attestor_id": "fmx",
        "current_human_decision": "FINALIZED_BY_CURRENT_EXPLICIT_HUMAN_AUTHORIZATION",
    }:
        _fail("FORMAL_PRIOR_REVIEW_STATE_INVALID")

    unit = formal.get("unit_level_human_decisions")
    if type(unit) is not dict or (
        unit.get("exact_event_count") != 8
        or unit.get("completed_human_review_event_count") != 8
        or unit.get("D1_task_relevance_decision") != "RELEVANT"
        or unit.get("D2_chemistry_support_disposition") != "POSITIVE"
        or unit.get("negative_chemistry") is not False
        or unit.get("task_domain_negative") is not False
        or unit.get("D3_reactive_pair_decision") != "CONFIRM_OBSERVED_PAIR"
        or unit.get("D4_role_partition_decision") != "SELECT_CANDIDATE_7"
        or unit.get("D5_training_use_disposition") != "EXCLUDE_FROM_TRAINING_ONLY"
        or unit.get("D6_context") != EXPECTED_D6
        or unit.get("event_specific_disposition_exception_count") != 0
        or unit.get("future_training_admission_candidate_count") != 0
        or unit.get("training_admission_created") is not False
        or unit.get("training_admitted_count") != 0
        or unit.get("human_training_excluded_positive_event_count") != 8
        or unit.get("machine_auto_selection_performed") is not False
        or unit.get("machine_recommended_candidate") is not None
    ):
        _fail("FORMAL_UNIT_DECISION_SEMANTICS_INVALID")

    raw_events = formal.get("event_level_human_decisions")
    if type(raw_events) is not list or len(raw_events) != 8:
        _fail("FORMAL_EXACT8_EVENT_COUNT_INVALID")
    if any(type(event) is not dict for event in raw_events):
        _fail("FORMAL_EVENT_NOT_OBJECT")
    raw_ids = [event.get("canonical_event_id") for event in raw_events]
    if len(set(raw_ids)) != 8:
        _fail("FORMAL_EVENT_ID_DUPLICATE")
    if tuple(raw_ids) != EXPECTED_EVENT_IDS:
        _fail("FORMAL_EVENT_ID_COVERAGE_INVALID")
    expected_raw = [_expected_raw_event(row) for row in EXPECTED_EVENTS]
    for observed, expected in zip(raw_events, expected_raw, strict=True):
        if observed != expected:
            differing = sorted(
                key
                for key in set(observed) | set(expected)
                if observed.get(key) != expected.get(key)
            )
            _fail("FORMAL_EVENT_SEMANTICS_INVALID:" + (differing[0] if differing else "schema"))

    pair = formal.get("reactive_pair_human_decision")
    if type(pair) is not dict or (
        pair.get("D3_human_choice") != "CONFIRM_OBSERVED_PAIR"
        or pair.get("exact_event_count") != 8
        or pair.get("protein_component_id") != "CYS"
        or pair.get("protein_residue_id") != "148-"
        or pair.get("protein_reactive_atom") != "SG"
        or pair.get("ligand_component_id") != "1F8"
        or pair.get("ligand_reactive_atom") != "SD"
        or pair.get("ligand_reactive_atom_element") != "S"
        or pair.get("reactive_pair_human_authoritative") is not True
        or pair.get("reactive_pair_human_authoritative_event_count") != 8
        or pair.get("reactive_pair_authority_scope") != AUTHORITY_SCOPE
        or pair.get("model_bound_pair_integration_created") is not False
        or pair.get("tensor_target_created") is not False
        or pair.get("training_admission_created") is not False
        or pair.get("reusable_reactive_pair_authority_created") is not False
    ):
        _fail("FORMAL_REACTIVE_PAIR_SEMANTICS_DRIFT")

    role = formal.get("selected_role_partition")
    if type(role) is not dict or (
        role.get("human_role_partition_choice") != "SELECT_CANDIDATE_7"
        or role.get("candidate_index_0based") != 7
        or role.get("candidate_id") != EXPECTED_CANDIDATE_ID
        or role.get("role_profile") != EXPECTED_ROLE_PROFILE
        or role.get("exact_heavy_atom_count") != 16
        or role.get("exact_heavy_atom_ids") != list(EXPECTED_HEAVY_ATOMS)
        or role.get("warhead_atoms") != list(EXPECTED_WARHEAD)
        or role.get("linker_atoms") != list(EXPECTED_LINKER)
        or role.get("scaffold_atoms") != list(EXPECTED_SCAFFOLD)
        or role.get("boundary_bonds") != [
            {"atom_id_1": "C15", "atom_id_2": "SD", "bond_order": "SING", "role_1": "linker", "role_2": "warhead"},
            {"atom_id_1": "C18", "atom_id_2": "N17", "bond_order": "SING", "role_1": "scaffold", "role_2": "linker"},
        ]
        or role.get("boundary_bond_count") != 2
        or role.get("heavy_atom_disjoint") is not True
        or role.get("heavy_atom_exhaustive") is not True
        or role.get("warhead_connected") is not True
        or role.get("linker_connected_or_empty") is not True
        or role.get("linker_atoms_on_scaffold_warhead_paths") is not True
        or role.get("scaffold_connected") is not True
        or role.get("applicable_canonical_task_ids") != [0, 1, 2, 3, 4]
        or role.get("sample_structurally_inapplicable_canonical_task_ids") != []
        or role.get("complete_PRE_warhead_topology_authority_created") is not False
        or role.get("machine_selected") is not False
        or role.get("machine_recommended_candidate") is not None
    ):
        _fail("FORMAL_SELECTED_ROLE_PARTITION_DRIFT")
    exact5 = role.get("global_canonical_Exact5")
    if type(exact5) is not dict or (
        exact5.get("B3_present") is not True
        or exact5.get("sixth_task_present") is not False
        or exact5.get("task_count") != 5
        or exact5.get("tasks") != [
            {"display_alias": alias, "semantic_name": semantic, "task_id": task_id}
            for task_id, semantic, alias, _generated, _fixed in CANONICAL_TASKS
        ]
    ):
        _fail("FORMAL_GLOBAL_EXACT5_DRIFT")

    if formal.get("human_approved_context") != _scientific_context():
        _fail("FORMAL_SCIENTIFIC_CONTEXT_BOUNDARY_INVALID")
    if formal.get("observed_graph_pre_boundary") != _observed_graph_pre_boundary():
        _fail("FORMAL_OBSERVED_GRAPH_PRE_BOUNDARY_INVALID")
    geometry = formal.get("geometry_boundary")
    if type(geometry) is not dict or (
        geometry.get("POST_evidence_provenance_preserved") is not True
        or geometry.get("POST_geometry_training_authority_created") is not False
        or geometry.get("POST_geometry_training_target_created") is not False
        or geometry.get("POST_to_PRE_copy_performed") is not False
        or geometry.get("PRE_status") != "PRE_REACTION_UNRESOLVED"
        or geometry.get("PRE_geometry_status") != "PRE_REACTION_UNRESOLVED"
        or geometry.get("PRE_geometry_authority_created") is not False
        or geometry.get("PRE_geometry_training_target_created") is not False
        or geometry.get("PRE_precursor_topology_authority_created") is not False
        or geometry.get("PRE_zero_fill_performed") is not False
        or geometry.get("PRE_coordinate_reconstruction_performed") is not False
        or geometry.get("PRE_precursor_reconstruction_performed") is not False
        or geometry.get("complete_disulfide_reconstruction_performed") is not False
    ):
        _fail("FORMAL_GEOMETRY_BOUNDARY_INVALID")
    training = formal.get("training_use_human_decision")
    if type(training) is not dict or (
        training.get("D5_human_choice") != "EXCLUDE_FROM_TRAINING_ONLY"
        or training.get("chemistry_positive_event_count") != 8
        or training.get("human_training_excluded_positive_event_count") != 8
        or training.get("training_include_event_count") != 0
        or training.get("future_training_admission_candidate_count") != 0
        or training.get("training_admitted_count") != 0
        or training.get("training_exclusion_is_chemistry_negative") is not False
        or training.get("training_admission_created") is not False
        or training.get("training_dataset_changed") is not False
    ):
        _fail("FORMAL_TRAINING_USE_SEMANTICS_INVALID")
    empty_authority = {"status": "NOT_CREATED", "authority_created": False, "authority_value": None}
    for field in ("reaction_family_authority", "warhead_rule_authority", "warhead_type_authority"):
        if formal.get(field) != empty_authority:
            _fail("FORMAL_AUXILIARY_AUTHORITY_INVALID:" + field)
    reusable = formal.get("reusable_authority_boundary")
    if type(reusable) is not dict or any(
        reusable.get(field) is not False
        for field in (
            "reaction_family_authority_created", "warhead_rule_authority_created",
            "warhead_type_authority_created", "reusable_chemistry_authority_created",
            "reusable_reactive_pair_authority_created", "reusable_role_authority_created",
            "cross_sample_reusable_rule_created", "PDK1_T148C_reusable_rule_created",
            "disulfide_reusable_reaction_family_authority_created",
            "complete_PRE_warhead_authority_created",
        )
    ):
        _fail("FORMAL_REUSABLE_AUTHORITY_BOUNDARY_INVALID")
    if formal.get("authority_boundary") != _formal_authority_boundary():
        _fail("FORMAL_AUTHORITY_OR_TRAINING_BOUNDARY_INVALID")
    if formal.get("downstream_status") != {
        "formal_human_decision_created": True,
        "completed_decision_ingestion": "NOT_DONE",
        "global_reconciliation_update": "NOT_DONE",
        "global_census_update": "NOT_DONE",
        "training": "NOT_STARTED",
    }:
        _fail("FORMAL_DOWNSTREAM_STATUS_INVALID")

    # Exact formal bytes preserve numeric lexemes.  This canonical digest also
    # closes every nested JSON semantic field against mutation in direct tests.
    if _sha(_json_bytes(dict(formal))) != FORMAL_SEMANTIC_CANONICAL_SHA256:
        _fail("FORMAL_COMPLETE_NESTED_SEMANTIC_DIGEST_INVALID")
    return {
        "events": [_event_projection(event) for event in raw_events],
        "role": _role_snapshot(),
        "scientific_context": _scientific_context(),
        "observed_graph_pre_boundary": _observed_graph_pre_boundary(),
        "formal_authority_boundary": _formal_authority_boundary(),
    }


def _binding_rows(
    bindings: Sequence[tuple[Path, int, str, str]],
    *,
    namespace: str,
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


def _semantic_owner_bindings(
    repo_root: Path, overrides: Mapping[Path, Path]
) -> list[dict[str, object]]:
    for relative, byte_count, sha256, role in IMMUTABLE_SEMANTIC_OWNER_BINDINGS:
        _verify_payload(overrides.get(relative, repo_root / relative), byte_count, sha256, role)
    runtime_values = _literal_assignments(
        overrides.get(RUNTIME_SOURCE_RELATIVE, repo_root / RUNTIME_SOURCE_RELATIVE),
        ("STRICT_LINKER_PRESENT_V1",),
    )
    canonical_values = _literal_assignments(
        overrides.get(CANONICAL_TASK_SOURCE_RELATIVE, repo_root / CANONICAL_TASK_SOURCE_RELATIVE),
        ("EXACT3_ROLES", "CANONICAL_TASKS"),
    )
    if runtime_values["STRICT_LINKER_PRESENT_V1"] != EXPECTED_ROLE_PROFILE:
        _fail("STRICT_PROFILE_RUNTIME_CONTRACT_DRIFT")
    if (
        canonical_values["EXACT3_ROLES"] != ("scaffold", "linker", "warhead")
        or canonical_values["CANONICAL_TASKS"] != CANONICAL_TASKS
    ):
        _fail("GLOBAL_CANONICAL_EXACT5_TASK_CONTRACT_DRIFT")
    return _binding_rows(IMMUTABLE_SEMANTIC_OWNER_BINDINGS, namespace="repository_relative")


def _frozen_review_bindings(
    repository_parent: Path, overrides: Mapping[Path, Path]
) -> list[dict[str, object]]:
    for relative, byte_count, sha256, role, _mode in FROZEN_REVIEW_PACKAGE_BINDINGS:
        _verify_payload(overrides.get(relative, repository_parent / relative), byte_count, sha256, role)
    return _expected_evidence_provenance()


def _current_census_bindings(
    repo_root: Path, overrides: Mapping[Path, Path]
) -> list[dict[str, object]]:
    payloads: dict[Path, bytes] = {}
    for relative, byte_count, sha256, role in CURRENT_CENSUS_BINDINGS:
        payloads[relative] = _verify_payload(
            overrides.get(relative, repo_root / relative), byte_count, sha256, role
        )
    summary_relative = CURRENT_CENSUS_BINDINGS[2][0]
    csv_relative = CURRENT_CENSUS_BINDINGS[1][0]
    try:
        summary = json.loads(payloads[summary_relative])
        rows = list(csv.DictReader(io.StringIO(payloads[csv_relative].decode("utf-8"))))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise OneF8IngestionSafetyError("CURRENT_CENSUS_PARSE_FAILED") from error
    boundary = summary.get("authority_boundary") if type(summary) is dict else None
    chemistry = summary.get("chemistry") if type(summary) is dict else None
    if (
        summary.get("schema_version") != "covapie_cumulative1000_current_global_readiness_census_with_2vs_v1"
        or type(chemistry) is not dict
        or chemistry.get("POSITIVE", {}).get("count") != 74
        or type(boundary) is not dict
        or boundary.get("next_priority_review_ligand") != "1F8"
        or boundary.get("next_priority_review_event_count") != 8
        or boundary.get("next_priority_review_unit") != EXPECTED_REVIEW_UNIT_ID
    ):
        _fail("CURRENT_CENSUS_SUMMARY_BOUNDARY_INVALID")
    one_f8 = [row for row in rows if row.get("ligand_component_id") == "1F8"]
    if (
        len(one_f8) != 8
        or tuple(row.get("canonical_event_id") for row in one_f8) != EXPECTED_EVENT_IDS
        or [int(row["scaleup_rank"]) for row in one_f8] != list(EXPECTED_RANKS)
        or any(
            row.get("current_global_status") != "CURRENTLY_UNREVIEWED"
            or row.get("current_review_status") != "CURRENTLY_UNREVIEWED"
            or row.get("chemistry_disposition") != "UNRESOLVED"
            for row in one_f8
        )
    ):
        _fail("CURRENT_CENSUS_1F8_PRIOR_STATE_INVALID")
    return _binding_rows(CURRENT_CENSUS_BINDINGS, namespace="repository_relative")


def load_frozen_formal_decision_v1(
    repo_root: Path,
    *,
    formal_decision_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, object]:
    """Load and strictly validate the formal decision and every bound source."""

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
        "formal_1F8_human_decision",
    )
    try:
        formal = json.loads(payload)
    except json.JSONDecodeError as error:
        raise OneF8IngestionSafetyError("FORMAL_DECISION_JSON_INVALID") from error
    if type(formal) is not dict:
        _fail("FORMAL_DECISION_TOP_LEVEL_NOT_OBJECT")
    normalized = _validate_formal_decision_v1(formal)
    return {
        "formal": formal,
        "normalized": normalized,
        "formal_decision_binding": _formal_binding(),
        "immutable_semantic_owner_bindings": _semantic_owner_bindings(repo_root, overrides),
        "frozen_review_package_bindings": _frozen_review_bindings(repo_root.parent, overrides),
        "current_published_census_bindings": _current_census_bindings(repo_root, overrides),
    }


def _authority_boundary() -> dict[str, bool]:
    return {
        "formal_human_decision_modified": False,
        "sample_level_human_authority_created_by_ingestion": False,
        "sample_level_human_authority_ingested": True,
        "snapshot_created_by_ingestion": True,
        "current_global_review_status_updated_by_ingestion": False,
        "new_reusable_authority_created": False,
        "reaction_family_authority_created": False,
        "warhead_rule_authority_created": False,
        "warhead_type_authority_created": False,
        "reusable_chemistry_authority_created": False,
        "reusable_reactive_pair_authority_created": False,
        "reusable_role_authority_created": False,
        "complete_PRE_warhead_authority_created": False,
        "complete_PRE_disulfide_reagent_authority_created": False,
        "PRE_geometry_authority_created": False,
        "PRE_precursor_topology_authority_created": False,
        "PRE_precursor_reconstruction_performed": False,
        "PRE_coordinate_reconstruction_performed": False,
        "POST_geometry_training_authority_created": False,
        "POST_to_PRE_copy_performed": False,
        "PRE_zero_fill_performed": False,
        "tensor_integration_performed": False,
        "tensor_target_created": False,
        "model_bound_pair_target_created_by_ingestion": False,
        "model_forward_performed": False,
        "training_admission_created": False,
        "training_dataset_changed": False,
        "training_performed": False,
        "global_reconciliation_updated": False,
        "global_census_updated": False,
    }


def _snapshot(bound: Mapping[str, Any]) -> dict[str, object]:
    normalized = bound["normalized"]
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "snapshot_role": "ADDITIVE_IMMUTABLE_1F8_COMPLETED_HUMAN_DECISION_INGESTION",
        "snapshot_created_by_ingestion": True,
        "human_authority_created_by_ingestion": False,
        "human_authority_ingested": True,
        "formal_decision_binding": bound["formal_decision_binding"],
        "frozen_formal_evidence_provenance": bound["frozen_review_package_bindings"],
        "review_unit_id": EXPECTED_REVIEW_UNIT_ID,
        "ligand_component_id": "1F8",
        "reviewer_id": "fmx",
        "attestor_id": "fmx",
        "approved_at_utc": EXPECTED_APPROVED_AT_UTC,
        "formal_prior_review_status": "CURRENTLY_UNREVIEWED",
        "formal_prior_review_inventory_status": "CURRENTLY_UNREVIEWED_NO_PRIOR_1F8_REVIEW_WORK_FOUND",
        "current_global_review_status_updated_by_ingestion": False,
        "authority_provenance": {
            "authority_source": AUTHORITY_SOURCE,
            "authority_scope": AUTHORITY_SCOPE,
            "authority_ingested": True,
            "authority_created_by_ingestion": False,
            "sample_level_human_authority_exists_in_source": True,
            "sample_level_human_authority_created_by_ingestion": False,
        },
        "unit_level_D1_D6": {
            "D1": "RELEVANT",
            "D2": "POSITIVE",
            "D3": "CONFIRM_OBSERVED_PAIR",
            "D4": "SELECT_CANDIDATE_7",
            "D5": "EXCLUDE_FROM_TRAINING_ONLY",
            "D6": EXPECTED_D6,
        },
        "events": normalized["events"],
        "reactive_pair": {
            "protein_reactive_atom": "SG",
            "ligand_reactive_atom": "SD",
            "ligand_reactive_atom_element": "S",
            "human_decision_available": True,
            "human_authoritative": True,
            "human_authority_event_count": 8,
            "human_authority_created_by_ingestion": False,
            "model_bound_pair_target_created_by_ingestion": False,
            "tensor_target_created": False,
            "training_admission_created": False,
            "reusable_reactive_pair_authority": False,
        },
        "selected_role_partition": normalized["role"],
        "canonical_task_contract": _canonical_task_contract(),
        "scientific_context": normalized["scientific_context"],
        "observed_graph_PRE_boundary": normalized["observed_graph_pre_boundary"],
        "geometry_boundary": {
            "POST_source_evidence_count": 8,
            "POST_geometry_training_authority_count": 0,
            "POST_geometry_training_label_available_now": False,
            "PRE_status": "PRE_REACTION_UNRESOLVED",
            "PRE_geometry_authority_count": 0,
            "PRE_geometry_training_target_count": 0,
            "PRE_precursor_topology_authority_count": 0,
            "complete_PRE_disulfide_reagent_authority_count": 0,
            "POST_to_PRE_copy_performed": False,
            "PRE_zero_fill_performed": False,
            "PRE_coordinate_reconstruction_performed": False,
            "PRE_precursor_reconstruction_performed": False,
            "complete_disulfide_reconstruction_performed": False,
        },
        "reusable_authority_boundary": {
            "reaction_family_target_available": False,
            "reaction_family_target_count": 0,
            "warhead_rule_target_available": False,
            "warhead_rule_target_count": 0,
            "warhead_type_target_available": False,
            "warhead_type_target_count": 0,
            "reusable_chemistry_authority_available": False,
            "reusable_pair_authority_available": False,
            "reusable_role_authority_available": False,
            "complete_PRE_warhead_authority_available": False,
            "complete_PRE_disulfide_reagent_authority_available": False,
            "new_reusable_authority_created": False,
        },
        "training_boundary": {
            "formal_event_training_use_decision": "EXCLUDE_FROM_TRAINING_ONLY",
            "chemistry_positive_count": 8,
            "training_excluded_positive_count": 8,
            "training_include_count": 0,
            "candidate_for_future_training_admission_count": 0,
            "training_admitted_count": 0,
            "training_materialization_allowed_count": 0,
            "current_runtime_model_usable_count": 0,
            "ready_for_training": False,
            "feature_semantics": "AUDIT_REQUIRED_LATER",
        },
        "current_global_state_boundary": {
            "published_global_positive_count_remains": 74,
            "global_reconciliation_update_status": "NOT_DONE_THIS_STEP",
            "global_census_update_status": "NOT_DONE_THIS_STEP",
            "current_global_review_status_updated_by_ingestion": False,
            "current_published_1F8_review_status": "CURRENTLY_UNREVIEWED",
        },
        "downstream_non_actions": {
            "global_reconciliation_update_status": "NOT_DONE_THIS_STEP",
            "global_census_update_status": "NOT_DONE_THIS_STEP",
            "tensorization_status": "NOT_DONE_THIS_STEP",
            "training_status": "NOT_DONE_THIS_STEP",
        },
        "authority_boundary": _authority_boundary(),
        "formal_authority_boundary_source": normalized["formal_authority_boundary"],
    }


MATRIX_HEADER = (
    "canonical_event_id", "scaleup_rank", "pdb_id", "model_number",
    "protein_chain_or_asym", "cys_residue_id", "protein_altloc",
    "ligand_chain_or_asym", "ligand_altloc", "selected_connection_id",
    "POST_distance_angstrom", "POST_distance_frozen_lexeme",
    "human_task_relevance_decision", "chemistry_known_positive",
    "negative_chemistry", "task_domain_negative",
    "reactive_pair_human_decision_available", "reactive_pair_human_authoritative",
    "protein_reactive_atom", "ligand_reactive_atom", "ligand_reactive_atom_element",
    "role_partition_human_decision_available", "role_partition_human_authoritative",
    "selected_role_candidate_index_0based", "role_profile", "warhead_atoms_json",
    "linker_atoms_json", "scaffold_atoms_json", "boundary_bonds_json",
    "global_canonical_task_count", "canonical_task_applicability_json",
    "strict_profile_applicable_task_ids_json", "formal_event_training_use_decision",
    "human_training_excluded", "training_use_allowed", "engineered_target_site",
    "native_cysteine_site", "medicinal_covalent_inhibitor_context",
    "allosteric_inhibitor_context", "disulfide_trapping_context",
    "observed_retained_fragment_context",
    "observed_graph_is_complete_authoritative_PRE_reagent",
    "POST_source_evidence_available", "POST_geometry_training_label_available_now",
    "PRE_geometry_authority_available", "PRE_geometry_training_label_available_now",
    "PRE_precursor_topology_authority_available",
    "complete_PRE_disulfide_reagent_authority_available",
    "PRE_precursor_reconstruction_performed", "reaction_family_target_available",
    "warhead_rule_target_available", "warhead_type_target_available",
    "candidate_for_future_training_admission", "training_admitted",
    "training_materialization_allowed_now", "current_runtime_model_usable",
    "authority_source", "authority_ingested", "authority_created_by_this_ingestion",
)


def _matrix_rows(snapshot: Mapping[str, Any]) -> list[dict[str, object]]:
    role = _role_snapshot()
    applicability = _canonical_task_contract()["strict_profile_task_applicability"]
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
                "ligand_chain_or_asym": event["ligand_chain_or_asym"],
                "ligand_altloc": "" if event["ligand_altloc"] is None else event["ligand_altloc"],
                "selected_connection_id": event["selected_connection_id"],
                "POST_distance_angstrom": str(event["POST_distance_angstrom"]),
                "POST_distance_frozen_lexeme": event["POST_distance_frozen_lexeme"],
                "human_task_relevance_decision": "RELEVANT",
                "chemistry_known_positive": "true",
                "negative_chemistry": "false",
                "task_domain_negative": "false",
                "reactive_pair_human_decision_available": "true",
                "reactive_pair_human_authoritative": "true",
                "protein_reactive_atom": "SG",
                "ligand_reactive_atom": "SD",
                "ligand_reactive_atom_element": "S",
                "role_partition_human_decision_available": "true",
                "role_partition_human_authoritative": "true",
                "selected_role_candidate_index_0based": "7",
                "role_profile": EXPECTED_ROLE_PROFILE,
                "warhead_atoms_json": _json_cell(list(EXPECTED_WARHEAD)),
                "linker_atoms_json": _json_cell(list(EXPECTED_LINKER)),
                "scaffold_atoms_json": _json_cell(list(EXPECTED_SCAFFOLD)),
                "boundary_bonds_json": _json_cell(role["boundary_bonds"]),
                "global_canonical_task_count": "5",
                "canonical_task_applicability_json": _json_cell(applicability),
                "strict_profile_applicable_task_ids_json": "[0,1,2,3,4]",
                "formal_event_training_use_decision": "EXCLUDE_FROM_TRAINING_ONLY",
                "human_training_excluded": "true",
                "training_use_allowed": "false",
                "engineered_target_site": "PDK1_T148C",
                "native_cysteine_site": "false",
                "medicinal_covalent_inhibitor_context": "true",
                "allosteric_inhibitor_context": "true",
                "disulfide_trapping_context": "true",
                "observed_retained_fragment_context": "true",
                "observed_graph_is_complete_authoritative_PRE_reagent": "false",
                "POST_source_evidence_available": "true",
                "POST_geometry_training_label_available_now": "false",
                "PRE_geometry_authority_available": "false",
                "PRE_geometry_training_label_available_now": "false",
                "PRE_precursor_topology_authority_available": "false",
                "complete_PRE_disulfide_reagent_authority_available": "false",
                "PRE_precursor_reconstruction_performed": "false",
                "reaction_family_target_available": "false",
                "warhead_rule_target_available": "false",
                "warhead_type_target_available": "false",
                "candidate_for_future_training_admission": "false",
                "training_admitted": "false",
                "training_materialization_allowed_now": "false",
                "current_runtime_model_usable": "false",
                "authority_source": AUTHORITY_SOURCE,
                "authority_ingested": "true",
                "authority_created_by_this_ingestion": "false",
            }
        )
    return rows


def _summary() -> dict[str, object]:
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "stage": SCHEMA_VERSION,
        "event_count": 8,
        "task_relevant_count": 8,
        "chemistry_positive_count": 8,
        "1F8_source_local_positive_count": 8,
        "source_local_positive_count": 8,
        "completed_human_positive_count": 8,
        "reactive_pair_human_authority_count": 8,
        "role_partition_human_authority_count": 8,
        "strict_profile_count": 8,
        "direct_profile_count": 0,
        "global_canonical_task_count": 5,
        "strict_profile_applicable_task_count_per_event": 5,
        "POST_source_evidence_count": 8,
        "POST_geometry_training_authority_count": 0,
        "PRE_geometry_authority_count": 0,
        "PRE_geometry_training_target_count": 0,
        "PRE_precursor_topology_authority_count": 0,
        "complete_PRE_disulfide_reagent_authority_count": 0,
        "reaction_family_target_count": 0,
        "warhead_rule_target_count": 0,
        "warhead_type_target_count": 0,
        "training_excluded_positive_count": 8,
        "training_include_count": 0,
        "future_training_admission_candidate_count": 0,
        "training_admitted_count": 0,
        "training_materialization_allowed_count": 0,
        "current_runtime_model_usable_count": 0,
        "ready_for_training": False,
        "formal_human_decision_ingested": True,
        "completed_decision_ingestion_status": "DONE_THIS_STEP",
        "global_reconciliation_update_status": "NOT_DONE_THIS_STEP",
        "global_census_update_status": "NOT_DONE_THIS_STEP",
        "published_global_positive_count_remains": 74,
        "ready_for_1F8_reconciliation_successor": True,
        "feature_semantics": "AUDIT_REQUIRED_LATER",
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
        raise OneF8IngestionSafetyError("UTF8_INVALID:" + label) from error
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


def _standalone_bound() -> dict[str, object]:
    return {
        "formal_decision_binding": _formal_binding(),
        "frozen_review_package_bindings": _expected_evidence_provenance(),
        "normalized": {
            "events": [_event_projection(_expected_raw_event(row)) for row in EXPECTED_EVENTS],
            "role": _role_snapshot(),
            "scientific_context": _scientific_context(),
            "observed_graph_pre_boundary": _observed_graph_pre_boundary(),
            "formal_authority_boundary": _formal_authority_boundary(),
        },
    }


def _expected_owner_bindings() -> list[dict[str, object]]:
    return _binding_rows(IMMUTABLE_SEMANTIC_OWNER_BINDINGS, namespace="repository_relative")


def _expected_census_bindings() -> list[dict[str, object]]:
    return _binding_rows(CURRENT_CENSUS_BINDINGS, namespace="repository_relative")


def build_artifacts_v1(
    repo_root: Path,
    *,
    formal_decision_path: Path | None = None,
    repository_path_overrides: Mapping[Path, Path] | None = None,
) -> dict[str, bytes]:
    """Build the deterministic Exact4 source projection in memory."""

    repo_root = repo_root.resolve()
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
        "artifact_role": "1F8_COMPLETED_DECISION_AND_EVENT_TASK_LABEL_AVAILABILITY_NOT_ADMISSION",
        "candidate_publication_file_count": 7,
        "output_artifact_count": 4,
        "source_path": SOURCE_RELATIVE.as_posix(),
        "checker_path": CHECKER_RELATIVE.as_posix(),
        "test_path": TEST_RELATIVE.as_posix(),
        "output_paths": [path.as_posix() for path in OUTPUT_RELATIVE_PATHS],
        "formal_decision_binding": bound["formal_decision_binding"],
        "frozen_formal_evidence_provenance": bound["frozen_review_package_bindings"],
        "immutable_semantic_owner_bindings": bound["immutable_semantic_owner_bindings"],
        "current_published_census_bindings": bound["current_published_census_bindings"],
        "current_published_census_boundary": {
            "published_global_positive_count_remains": 74,
            "current_next_priority_review_ligand": "1F8",
            "current_next_priority_review_event_count": 8,
            "current_1F8_review_status": "CURRENTLY_UNREVIEWED",
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
            "sample_level_human_authority_exists_in_source": True,
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
        "published_global_positive_count_remains": 74,
        "feature_semantics_audit_required_before_formal_training": True,
        "ready_for_1F8_reconciliation_successor": True,
        "ready_for_training": False,
        "authority_boundary": _authority_boundary(),
    }
    artifacts = {
        SNAPSHOT: snapshot_payload,
        MATRIX: matrix_payload,
        SUMMARY: summary_payload,
        MANIFEST: _json_bytes(manifest),
    }
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
    expected = (
        (SNAPSHOT, _EXPECTED_SNAPSHOT_SHA256_V1),
        (MATRIX, _EXPECTED_MATRIX_SHA256_V1),
        (SUMMARY, _EXPECTED_SUMMARY_SHA256_V1),
    )
    for name, digest in expected:
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
    """Validate Exact4 direct evidence, including standalone coordinated drift."""

    if tuple(artifacts) != OUTPUT_FILENAMES:
        _fail("OUTPUT_ARTIFACT_EXACT4_INVALID")
    for name, payload in artifacts.items():
        _validate_text_payload(name, payload)
    try:
        snapshot = json.loads(artifacts[SNAPSHOT])
        summary = json.loads(artifacts[SUMMARY])
        manifest = json.loads(artifacts[MANIFEST])
        matrix = list(csv.DictReader(io.StringIO(artifacts[MATRIX].decode("utf-8"))))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise OneF8IngestionSafetyError("OUTPUT_PARSE_FAILED") from error
    for document in (snapshot, summary, manifest):
        _reject_dynamic_metadata(document)
    if summary != _summary():
        _fail("SUMMARY_EXACT_COUNTS_OR_BOUNDARY_INVALID")
    if snapshot != _snapshot(_standalone_bound()):
        _fail("SNAPSHOT_EXACT_SOURCE_PROJECTION_INVALID")
    if (
        len(snapshot["events"]) != 8
        or tuple(event["canonical_event_id"] for event in snapshot["events"]) != EXPECTED_EVENT_IDS
        or [event["scaleup_rank"] for event in snapshot["events"]] != list(EXPECTED_RANKS)
        or len({event["canonical_event_id"] for event in snapshot["events"]}) != 8
    ):
        _fail("SNAPSHOT_EXACT8_COVERAGE_INVALID")
    if snapshot["selected_role_partition"] != _role_snapshot():
        _fail("SNAPSHOT_CANDIDATE7_ROLE_CONTRACT_INVALID")
    if snapshot["canonical_task_contract"] != _canonical_task_contract():
        _fail("SNAPSHOT_GLOBAL_EXACT5_CONTRACT_INVALID")
    if snapshot["authority_boundary"] != _authority_boundary():
        _fail("SNAPSHOT_AUTHORITY_BOUNDARY_INVALID")

    if (list(matrix[0].keys()) if matrix else []) != list(MATRIX_HEADER):
        _fail("MATRIX_HEADER_INVALID")
    if (
        len(matrix) != 8
        or tuple(row["canonical_event_id"] for row in matrix) != EXPECTED_EVENT_IDS
        or len({row["canonical_event_id"] for row in matrix}) != 8
        or [int(row["scaleup_rank"]) for row in matrix] != list(EXPECTED_RANKS)
    ):
        _fail("MATRIX_EXACT8_INVALID")
    if artifacts[MATRIX] != _csv_bytes(MATRIX_HEADER, _matrix_rows(snapshot)):
        _fail("MATRIX_DIRECT_EVIDENCE_INVALID")
    true_fields = (
        "chemistry_known_positive", "reactive_pair_human_decision_available",
        "reactive_pair_human_authoritative", "role_partition_human_decision_available",
        "role_partition_human_authoritative", "human_training_excluded",
        "medicinal_covalent_inhibitor_context", "allosteric_inhibitor_context",
        "disulfide_trapping_context", "observed_retained_fragment_context",
        "POST_source_evidence_available", "authority_ingested",
    )
    false_fields = (
        "negative_chemistry", "task_domain_negative", "training_use_allowed",
        "native_cysteine_site", "observed_graph_is_complete_authoritative_PRE_reagent",
        "POST_geometry_training_label_available_now", "PRE_geometry_authority_available",
        "PRE_geometry_training_label_available_now", "PRE_precursor_topology_authority_available",
        "complete_PRE_disulfide_reagent_authority_available",
        "PRE_precursor_reconstruction_performed", "reaction_family_target_available",
        "warhead_rule_target_available", "warhead_type_target_available",
        "candidate_for_future_training_admission", "training_admitted",
        "training_materialization_allowed_now", "current_runtime_model_usable",
        "authority_created_by_this_ingestion",
    )
    for index, row in enumerate(matrix):
        if any(row[field] != "true" for field in true_fields):
            _fail("MATRIX_REQUIRED_TRUE_FLAG_INVALID")
        if any(row[field] != "false" for field in false_fields):
            _fail("MATRIX_REQUIRED_FALSE_FLAG_INVALID")
        expected_event = EXPECTED_EVENTS[index]
        applicability = json.loads(row["canonical_task_applicability_json"])
        if (
            row["model_number"] != "1"
            or row["protein_altloc"] != ""
            or row["ligand_altloc"] != ""
            or row["protein_reactive_atom"] != "SG"
            or row["ligand_reactive_atom"] != "SD"
            or row["ligand_reactive_atom_element"] != "S"
            or row["selected_role_candidate_index_0based"] != "7"
            or row["role_profile"] != EXPECTED_ROLE_PROFILE
            or row["POST_distance_angstrom"] != str(expected_event[10])
            or row["POST_distance_frozen_lexeme"] != expected_event[11]
            or row["global_canonical_task_count"] != "5"
            or row["strict_profile_applicable_task_ids_json"] != "[0,1,2,3,4]"
            or len(applicability) != 5
            or [item["task_id"] for item in applicability if item["structurally_applicable"]] != [0, 1, 2, 3, 4]
            or applicability[3]["semantic_long_name"] != "scaffold_only"
        ):
            _fail("MATRIX_PROVENANCE_CANDIDATE7_OR_EXACT5_INVALID")

    expected_manifest_keys = {
        "schema_version", "stage", "artifact_role", "candidate_publication_file_count",
        "output_artifact_count", "source_path", "checker_path", "test_path",
        "output_paths", "formal_decision_binding", "frozen_formal_evidence_provenance",
        "immutable_semantic_owner_bindings", "current_published_census_bindings",
        "current_published_census_boundary", "candidate_source_bindings",
        "canonical_task_contract", "counts", "human_authority_ingestion_semantics",
        "output_artifact_bindings", "manifest_self_sha256_recorded",
        "manifest_self_sha256_policy", "deterministic",
        "completed_decision_ingestion_status", "global_reconciliation_update_status",
        "global_census_update_status", "published_global_positive_count_remains",
        "feature_semantics_audit_required_before_formal_training",
        "ready_for_1F8_reconciliation_successor", "ready_for_training",
        "authority_boundary",
    }
    if type(manifest) is not dict or set(manifest) != expected_manifest_keys:
        _fail("MANIFEST_SCHEMA_INVALID")
    if (
        manifest["schema_version"] != MANIFEST_SCHEMA_VERSION
        or manifest["stage"] != SCHEMA_VERSION
        or manifest["artifact_role"] != "1F8_COMPLETED_DECISION_AND_EVENT_TASK_LABEL_AVAILABILITY_NOT_ADMISSION"
        or manifest["candidate_publication_file_count"] != 7
        or manifest["output_artifact_count"] != 4
        or manifest["source_path"] != SOURCE_RELATIVE.as_posix()
        or manifest["checker_path"] != CHECKER_RELATIVE.as_posix()
        or manifest["test_path"] != TEST_RELATIVE.as_posix()
        or manifest["output_paths"] != [path.as_posix() for path in OUTPUT_RELATIVE_PATHS]
        or manifest["formal_decision_binding"] != _formal_binding()
        or manifest["frozen_formal_evidence_provenance"] != _expected_evidence_provenance()
        or manifest["immutable_semantic_owner_bindings"] != _expected_owner_bindings()
        or manifest["current_published_census_bindings"] != _expected_census_bindings()
        or manifest["current_published_census_boundary"] != {
            "published_global_positive_count_remains": 74,
            "current_next_priority_review_ligand": "1F8",
            "current_next_priority_review_event_count": 8,
            "current_1F8_review_status": "CURRENTLY_UNREVIEWED",
            "global_reconciliation_update_status": "NOT_DONE_THIS_STEP",
            "global_census_update_status": "NOT_DONE_THIS_STEP",
        }
        or manifest["canonical_task_contract"] != _canonical_task_contract()
        or manifest["authority_boundary"] != _authority_boundary()
        or manifest["manifest_self_sha256_recorded"] is not False
        or manifest["manifest_self_sha256_policy"] != "SELF_SHA256_PROHIBITED"
        or manifest["deterministic"] is not True
        or manifest["completed_decision_ingestion_status"] != "DONE_THIS_STEP"
        or manifest["global_reconciliation_update_status"] != "NOT_DONE_THIS_STEP"
        or manifest["global_census_update_status"] != "NOT_DONE_THIS_STEP"
        or manifest["published_global_positive_count_remains"] != 74
        or manifest["feature_semantics_audit_required_before_formal_training"] is not True
        or manifest["ready_for_1F8_reconciliation_successor"] is not True
        or manifest["ready_for_training"] is not False
    ):
        _fail("MANIFEST_BOUNDARY_OR_SOURCE_BINDING_INVALID")
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
        "sample_level_human_authority_exists_in_source": True,
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
        if (
            manifest["frozen_formal_evidence_provenance"] != bound["frozen_review_package_bindings"]
            or manifest["immutable_semantic_owner_bindings"] != bound["immutable_semantic_owner_bindings"]
            or manifest["current_published_census_bindings"] != bound["current_published_census_bindings"]
        ):
            _fail("MANIFEST_FROZEN_SOURCE_BINDINGS_INVALID")


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
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
        "event_count": 8,
        "chemistry_positive_count": 8,
        "training_excluded_positive_count": 8,
        "training_include_count": 0,
        "future_training_admission_candidate_count": 0,
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
    print("event_count=8")
    print("chemistry_positive_count=8")
    print("training_excluded_positive_count=8")
    print("training_include_count=0")
    print("training_admitted_count=0")
    print("published_global_positive_count_remains=74")
    print("ready_for_training=false")
    for name in OUTPUT_FILENAMES:
        print(name + "_sha256=" + _sha(artifacts[name]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
