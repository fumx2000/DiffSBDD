#!/usr/bin/env python3
"""Independently audit and materialize current CovaPIE atom-pair semantics."""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import subprocess
import sys
from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from covalent_ext import (  # noqa: E402
    covapie_covalent_bond_atom_pair_current_semantics_and_downstream_consumers_audit_gate_v1
    as audit,
)


BASE_COMMIT = "976da60a5af7b7ba71597c1202955a45db6b6cf1"
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE covalent bond atom-pair current-semantics audit v1"
)
STAGE = (
    "covapie_covalent_bond_atom_pair_current_semantics_and_"
    "downstream_consumers_audit_gate_v1"
)
OUTPUT_ROOT = Path("data/derived/covalent_small") / STAGE
LINEAGE_NAME = "covapie_covalent_bond_atom_pair_source_lineage_inventory.csv"
REPRESENTATION_NAME = (
    "covapie_covalent_bond_atom_pair_current_representation_audit.csv"
)
CONSUMER_NAME = (
    "covapie_covalent_bond_atom_pair_downstream_consumer_inventory.csv"
)
UNRESOLVED_NAME = (
    "covapie_covalent_bond_atom_pair_unresolved_semantics_inventory.csv"
)
ISSUE_NAME = "covapie_covalent_bond_atom_pair_issue_readiness_inventory.csv"
MANIFEST_NAME = (
    "covapie_covalent_bond_atom_pair_current_semantics_and_"
    "downstream_consumers_audit_manifest.json"
)
OUTPUT_NAMES = (
    LINEAGE_NAME,
    REPRESENTATION_NAME,
    CONSUMER_NAME,
    UNRESOLVED_NAME,
    ISSUE_NAME,
    MANIFEST_NAME,
)
EXACT10 = (
    Path("src/covalent_ext")
    / (
        "covapie_covalent_bond_atom_pair_current_semantics_and_"
        "downstream_consumers_audit_gate_v1.py"
    ),
    Path("tests")
    / (
        "test_covapie_covalent_bond_atom_pair_current_semantics_and_"
        "downstream_consumers_audit_gate_v1.py"
    ),
    Path("scripts")
    / (
        "check_covapie_covalent_bond_atom_pair_current_semantics_and_"
        "downstream_consumers_audit_gate_v1.py"
    ),
    Path("docs")
    / (
        "covapie_covalent_bond_atom_pair_current_semantics_and_"
        "downstream_consumers_audit_gate_v1_summary.md"
    ),
    *(OUTPUT_ROOT / name for name in OUTPUT_NAMES),
)
PREDECESSOR_ISSUE_PATH = (
    Path("data/derived/covalent_small")
    / (
        "covapie_post_admission_control_plane_completion_and_"
        "next_training_preparation_blocker_review_gate_v1"
    )
    / "covapie_post_admission_control_plane_issue_readiness_inventory.csv"
)
PREDECESSOR_ISSUE_SHA256 = (
    "fb4d2dfae7ffc056e3856c94e2f5a135"
    "d468eb3801144f9a698f95d9b812ace7"
)
FINAL_DATASET_PATH = (
    "data/derived/covalent_small/"
    "covapie_final_dataset_materialization_smoke_v0/final_dataset_index.csv"
)
FINAL_QA_MANIFEST_PATH = (
    "data/derived/covalent_small/covapie_final_dataset_qa_gate_v1/"
    "covapie_final_dataset_qa_v1_manifest.json"
)
FEATURE_AUDIT_PATH = (
    "data/derived/covalent_small/covapie_feature_semantics_audit_gate_v0/"
    "covapie_auxiliary_label_semantics_audit.csv"
)
TENSORIZATION_PATH = (
    "data/derived/covalent_small/"
    "covapie_feature_semantics_tensorization_audit_gate_v0/"
    "covapie_label_tensorization_blocker_audit.csv"
)
ORIGINAL_PRODUCER_PATH = (
    "data/derived/covalent_small/"
    "covapie_cys_sg_ready_candidate_materialization_gate_v0/"
    "covapie_cys_sg_ready_candidate_inventory.csv"
)
EXPANSION_PRODUCER_PATH = (
    "data/derived/covalent_small/"
    "covapie_independent_group_expansion_struct_conn_crosscheck_smoke_v0/"
    "covapie_struct_conn_candidate_crosscheck_audit.csv"
)
EXPANSION_RELEVANT_ROWS_PATH = (
    "data/derived/covalent_small/"
    "covapie_independent_group_expansion_struct_conn_crosscheck_smoke_v0/"
    "covapie_struct_conn_relevant_row_inventory.csv"
)
ORIGINAL_SAMPLE_INDEX_PATH = (
    "data/derived/covalent_small/"
    "covapie_sample_index_materialization_smoke_v0/sample_index.csv"
)
EXPANSION_SAMPLE_INDEX_PATH = (
    "data/derived/covalent_small/"
    "covapie_independent_group_expansion_batch_sample_index_"
    "materialization_smoke_v0/expansion_batch_sample_index.csv"
)
UNIFIED_SAMPLE_INDEX_PATH = (
    "data/derived/covalent_small/"
    "covapie_unified_independence_group_assignment_and_sample_index_"
    "merge_smoke_v0/unified_sample_index.csv"
)
SPLIT_PATHS = (
    "data/derived/covalent_small/"
    "covapie_unified_leakage_split_materialization_smoke_v0/"
    "train_sample_index.csv",
    "data/derived/covalent_small/"
    "covapie_unified_leakage_split_materialization_smoke_v0/"
    "validation_sample_index.csv",
    "data/derived/covalent_small/"
    "covapie_unified_leakage_split_materialization_smoke_v0/"
    "test_sample_index.csv",
)
MODEL_INPUT_DESIGN_PATH = (
    "src/covalent_ext/"
    "real_covalent_confirmed_candidate_model_input_design_gate.py"
)
CANONICAL_MASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
MATCHED_TERMS = (
    "covalent_bond_atom_pair",
    "ligand_residue_atom_pair",
    "ligand_residue_atom_pair_label",
    "residue_atom_name",
    "ligand_atom_name",
    "covalent_residue_atom_name",
    "ligand_covalent_atom_name",
    "ligand_residue_atom_pair_label_status",
    "ligand_residue_atom_pair_table_path",
    "ligand_residue_atom_pair_count",
    "covalent_event_table_path",
    "post_covalent_bond_distance_angstrom",
    "struct_conn",
    "SG--CAG",
    "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
)
MODEL_CONSUMER_TERMS = (
    "covalent_bond_atom_pair",
    "ligand_residue_atom_pair",
    "ligand_residue_atom_pair_label",
    "ligand_residue_atom_pair_table_path",
    "residue_atom_name",
    "ligand_atom_name",
    "covalent_residue_atom_name",
    "ligand_covalent_atom_name",
    "post_covalent_bond_distance_angstrom",
)
CONSUMER_ROLES = {
    "producer",
    "semantic_transformer",
    "materializer",
    "validator",
    "qa_gate",
    "schema_declaration",
    "status_declaration",
    "path_reference",
    "report_or_manifest",
    "test_only",
    "tensorization_blocker",
    "dataloader_consumer",
    "model_forward_consumer",
    "loss_consumer",
    "training_target_consumer",
    "documentation_only",
}

LINEAGE_COLUMNS = (
    "lineage_order",
    "lineage_role",
    "source_path",
    "source_symbol_or_selector",
    "selector_kind",
    "selector_expression",
    "expected_record_count",
    "observed_record_count",
    "input_field_or_evidence",
    "output_field",
    "representation_before",
    "representation_after",
    "semantic_transformation",
    "predecessor_projection",
    "observed_projection",
    "predecessor_successor_projection_verified",
    "explicit_bond_authority_required",
    "explicit_bond_authority_observed",
    "distance_only_inference_used",
    "current_source_of_truth",
    "committed_in_base",
    "source_sha256",
    "selector_verified",
    "verified",
)
REPRESENTATION_COLUMNS = (
    "source_artifact",
    "source_row_identity",
    "sample_or_event_id",
    "pdb_id",
    "ligand_comp_id_or_het_id",
    "residue_name",
    "residue_chain_id",
    "residue_index",
    "residue_insertion_code_if_available",
    "residue_atom_name",
    "ligand_atom_name",
    "stored_covalent_bond_atom_pair",
    "pair_reconstructed_from_separate_fields",
    "stored_matches_reconstructed",
    "explicit_bond_evidence_type",
    "conn_id_if_available",
    "conn_type_id_if_available",
    "current_validation_status",
    "current_training_use_status",
    "event_pair_cardinality",
    "observed_delimiter",
    "observed_ordering",
    "value_identity_kind",
    "verified",
)
CONSUMER_COLUMNS = (
    "consumer_path",
    "consumer_symbol_or_selector",
    "matched_term",
    "consumer_role",
    "reads_pair_value",
    "reads_pair_status_only",
    "reads_pair_table_path_only",
    "interprets_pair_order",
    "interprets_pair_delimiter",
    "maps_to_protein_atom_index",
    "maps_to_ligand_atom_index",
    "creates_tensor",
    "uses_in_collate",
    "uses_in_forward",
    "uses_in_loss",
    "uses_as_training_target",
    "current_behavior",
    "semantic_assumption",
    "source_sha256",
    "verified",
)
UNRESOLVED_COLUMNS = (
    "semantics_item",
    "current_observed_state",
    "currently_formally_defined",
    "current_evidence_path",
    "risk_if_left_implicit",
    "required_for_encoding_contract",
    "required_for_feature_semantics_audit",
    "required_for_tensorization",
    "required_for_model_integration",
    "decision_made_current_audit",
    "deferred_to_next_contract",
    "verified",
)
UNRESOLVED_SPECS = (
    ("future canonical pair ordering", "current rows visibly store residue atom then ligand atom; future order is not normative", "direction ambiguity"),
    ("future serialization grammar", "current values use two atom-name tokens separated by --", "ambiguous parsing"),
    ("delimiter escaping or atom-name character boundary", "no escaping contract is committed", "non-generic serialization"),
    ("residue atom identity namespace", "current producers expose mixed auth/label locator fields and atom names", "identity mismatch"),
    ("ligand atom identity namespace", "current producers expose atom names from explicit struct_conn evidence", "identity mismatch"),
    ("chain residue index insertion code in pair identity", "current serialized pair omits locator context", "cross-residue collision"),
    ("altloc and model identity", "not represented in current pair string", "ambiguous atom row"),
    ("ligand comp ID in pair identity", "present beside pair but absent from pair string", "cross-ligand collision"),
    ("protein full-atom table row mapping", "no mapping from pair string to protein table index", "cannot tensorize"),
    ("pocket atom table row mapping", "no mapping from pair string to pocket table index", "cannot tensorize"),
    ("ligand atom table row mapping", "no mapping from pair string to ligand table index", "cannot tensorize"),
    ("atom-table row ordering stability", "not audited for pair-index stability", "unstable indices"),
    ("tensor index base", "no index base is selected", "off-by-one errors"),
    ("one zero many pair cardinality", "current 11 rows each expose exactly one pair", "generic cardinality undefined"),
    ("duplicate pair policy", "duplicate serialized values occur across distinct events", "incorrect deduplication"),
    ("conflicting explicit-bond policy", "no conflict is observed in current 11 events", "fail-open conflict handling"),
    ("missing or invalid pair policy", "current canonical rows are non-empty and validated", "undefined masking or rejection"),
    ("pair directionality and symmetry", "current text is visibly ordered but future directionality is unspecified", "target mismatch"),
    ("current Cys-SG compatibility", "current scope is Cys-SG evidence with multiple ligand atom names", "backward incompatibility"),
    ("label tensor shape", "no pair label tensor exists", "shape incompatibility"),
    ("label mask and loss-mask semantics", "no pair loss-mask contract exists", "invalid loss contribution"),
    ("negative or nonbond pair definition", "only positive explicit-bond evidence is materialized", "undefined negatives"),
    ("future pair-head target interface", "only future auxiliary-task references exist", "model interface mismatch"),
    ("checkpoint compatibility impact", "no pair head or pair loss has been integrated", "checkpoint breakage"),
)


def _run_git(*args: str, allow_no_match: bool = False) -> bytes:
    result = subprocess.run(
        ("git", *args),
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    allowed = (0, 1) if allow_no_match else (0,)
    if result.returncode not in allowed:
        raise AssertionError(
            f"git command failed: {' '.join(args)}\n"
            + result.stderr.decode("utf-8", errors="replace")
        )
    return result.stdout


@lru_cache(maxsize=None)
def _git_show(path: str | Path) -> bytes:
    return _run_git("show", f"{BASE_COMMIT}:{Path(path).as_posix()}")


def _blob_sha(path: str | Path) -> str:
    return hashlib.sha256(_git_show(path)).hexdigest()


def _csv_from_bytes(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _base_csv(path: str | Path) -> list[dict[str, str]]:
    return _csv_from_bytes(_git_show(path))


def _base_json(path: str | Path) -> dict[str, object]:
    value = json.loads(_git_show(path))
    if type(value) is not dict:
        raise AssertionError(f"BASE JSON is not an object: {path}")
    return value


def _bool(value: bool) -> str:
    return "true" if value else "false"


def _csv_bytes(
    columns: tuple[str, ...], rows: tuple[dict[str, str], ...]
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


@dataclass(frozen=True)
class AtomPairProducerProjection:
    producer_branch: str
    producer_record_id: str
    event_identity: str
    pdb_id: str
    ligand_identity: str
    residue_identity: str
    residue_atom_name: str
    ligand_atom_name: str
    covalent_bond_atom_pair: str
    conn_id: str
    conn_type_id: str
    explicit_bond_authority: bool
    selector_verified: bool


@dataclass(frozen=True)
class AtomPairLayerProjection:
    layer_name: str
    source_record_id: str
    event_identity: str
    pdb_id: str
    ligand_identity: str
    residue_identity: str
    residue_atom_name: str
    ligand_atom_name: str
    covalent_bond_atom_pair: str
    conn_id: str
    conn_type_id: str
    explicit_bond_authority: bool


@dataclass(frozen=True)
class ProducerProjectionValidation:
    producer_projection_verified: bool
    producer_conflict_present: bool
    producer_conflict_event_ids: tuple[str, ...]
    explicit_bond_authority_verified: bool
    layer_projection_status: tuple[tuple[str, bool], ...]
    mismatch_reasons: tuple[str, ...]


@dataclass(frozen=True)
class ExecutableLineageEvidence:
    lineage_rows: tuple[dict[str, str], ...]
    producer_projections: tuple[AtomPairProducerProjection, ...]
    producer_validation: ProducerProjectionValidation
    lineage_selectors_executed: bool
    lineage_transition_projections_verified: bool
    original_producer_record_count: int
    expansion_producer_record_count: int
    original_sample_index_record_count: int
    expansion_sample_index_record_count: int
    unified_sample_index_record_count: int
    split_union_record_count: int
    final_dataset_record_count: int
    split_partition_verified: bool


def _event_identity(pdb_id: str, ligand_identity: str) -> str:
    return f"{pdb_id}/{ligand_identity}"


def _pair(residue_atom_name: str, ligand_atom_name: str) -> str:
    return f"{residue_atom_name}--{ligand_atom_name}"


def _residue_identity(
    residue_name: str, chain_id: str, residue_index: str
) -> str:
    return f"{residue_name}|{chain_id}|{residue_index}"


def build_original_producer_projections(
    rows: list[dict[str, str]] | None = None,
) -> tuple[AtomPairProducerProjection, ...]:
    source_rows = _base_csv(ORIGINAL_PRODUCER_PATH) if rows is None else rows
    selected = [
        row
        for row in source_rows
        if row.get("ready_candidate_scope")
        == "cys_sg_struct_conn_validated_ligand_event_v0"
    ]
    projections = []
    for row in selected:
        reconstructed = _pair(
            row.get("residue_atom_name", ""),
            row.get("ligand_atom_name", ""),
        )
        selector_verified = (
            row.get("ready_candidate_row_passed") == "True"
            and row.get("ready_for_sample_preparation") == "True"
            and row.get("ready_candidate_status", "").startswith(
                "ready_candidate_materialized"
            )
            and row.get("covalent_bond_atom_pair") == reconstructed
            and row.get("conn_id", "") != ""
            and row.get("conn_type_id") == "covale"
        )
        ligand = row.get("ligand_comp_id", "") or row.get(
            "expected_het_id", ""
        )
        projections.append(
            AtomPairProducerProjection(
                producer_branch="original",
                producer_record_id=row.get("ready_candidate_id", ""),
                event_identity=_event_identity(row.get("pdb_id", ""), ligand),
                pdb_id=row.get("pdb_id", ""),
                ligand_identity=ligand,
                residue_identity=_residue_identity(
                    row.get("covpdb_residue_name", ""),
                    row.get("covpdb_chain_id", ""),
                    row.get("covpdb_residue_index", ""),
                ),
                residue_atom_name=row.get("residue_atom_name", ""),
                ligand_atom_name=row.get("ligand_atom_name", ""),
                covalent_bond_atom_pair=row.get(
                    "covalent_bond_atom_pair", ""
                ),
                conn_id=row.get("conn_id", ""),
                conn_type_id=row.get("conn_type_id", ""),
                explicit_bond_authority=(
                    row.get("conn_id", "") != ""
                    and row.get("conn_type_id") == "covale"
                    and "struct_conn" in row.get("ready_candidate_scope", "")
                ),
                selector_verified=selector_verified,
            )
        )
    return tuple(sorted(projections, key=lambda item: item.event_identity))


def build_expansion_producer_projections(
    rows: list[dict[str, str]] | None = None,
    relevant_rows: list[dict[str, str]] | None = None,
) -> tuple[AtomPairProducerProjection, ...]:
    source_rows = _base_csv(EXPANSION_PRODUCER_PATH) if rows is None else rows
    authority_rows = (
        _base_csv(EXPANSION_RELEVANT_ROWS_PATH)
        if relevant_rows is None
        else relevant_rows
    )
    selected = [
        row
        for row in source_rows
        if row.get("confirmed_covalent_candidate") == "True"
        and row.get("eligible_for_batch_sample_preparation") == "True"
        and row.get("crosscheck_classification")
        == "confirmed_unique_exact_match"
    ]
    projections = []
    for row in selected:
        authority_matches = [
            item
            for item in authority_rows
            if item.get("pdb_id") == row.get("pdb_id")
            and item.get("expected_het_id") == row.get("expected_het_id")
            and item.get("struct_conn_id")
            == row.get("selected_struct_conn_id")
            and item.get("exact_cys_sg_expected_het_match") == "True"
            and item.get("ligand_covalent_atom_name_if_exact")
            == row.get("selected_ligand_atom_name")
        ]
        authority = authority_matches[0] if len(authority_matches) == 1 else {}
        reconstructed = _pair(
            row.get("selected_cys_atom_name", ""),
            row.get("selected_ligand_atom_name", ""),
        )
        selector_verified = (
            row.get("crosscheck_status") == "passed"
            and row.get("exact_match_count") == "1"
            and row.get("selected_struct_conn_id", "") != ""
            and len(authority_matches) == 1
            and authority.get("conn_type_id") == "covale"
        )
        ligand = row.get("selected_ligand_comp_id", "") or row.get(
            "expected_het_id", ""
        )
        projections.append(
            AtomPairProducerProjection(
                producer_branch="expansion",
                producer_record_id=row.get("candidate_crosscheck_id", ""),
                event_identity=_event_identity(row.get("pdb_id", ""), ligand),
                pdb_id=row.get("pdb_id", ""),
                ligand_identity=ligand,
                residue_identity=_residue_identity(
                    "CYS",
                    row.get("selected_cys_chain_id", ""),
                    row.get("selected_cys_seq_id", ""),
                ),
                residue_atom_name=row.get("selected_cys_atom_name", ""),
                ligand_atom_name=row.get("selected_ligand_atom_name", ""),
                covalent_bond_atom_pair=reconstructed,
                conn_id=row.get("selected_struct_conn_id", ""),
                conn_type_id=authority.get("conn_type_id", ""),
                explicit_bond_authority=(
                    selector_verified
                    and authority.get("conn_type_id") == "covale"
                ),
                selector_verified=selector_verified,
            )
        )
    return tuple(sorted(projections, key=lambda item: item.event_identity))


def _event_projection(row: Mapping[str, str], layer: str) -> AtomPairLayerProjection:
    ligand = row.get("ligand_comp_id", "")
    return AtomPairLayerProjection(
        layer_name=layer,
        source_record_id=row.get("sample_preparation_input_id", ""),
        event_identity=_event_identity(row.get("pdb_id", ""), ligand),
        pdb_id=row.get("pdb_id", ""),
        ligand_identity=ligand,
        residue_identity=_residue_identity(
            row.get("residue_comp_id", ""),
            row.get("residue_auth_asym_id", "")
            or row.get("residue_label_asym_id", ""),
            row.get("residue_auth_seq_id", "")
            or row.get("residue_label_seq_id", ""),
        ),
        residue_atom_name=row.get("residue_atom_name", ""),
        ligand_atom_name=row.get("ligand_atom_name", ""),
        covalent_bond_atom_pair=row.get("covalent_bond_atom_pair", ""),
        conn_id=row.get("conn_id", ""),
        conn_type_id=row.get("conn_type_id", ""),
        explicit_bond_authority=(
            row.get("conn_id", "") != ""
            and row.get("conn_type_id") == "covale"
            and "struct_conn" in row.get("event_source", "")
            and row.get("event_status") == "validated"
        ),
    )


def _pair_projection(row: Mapping[str, str], layer: str) -> AtomPairLayerProjection:
    ligand = row.get("expected_het_id", "")
    return AtomPairLayerProjection(
        layer_name=layer,
        source_record_id=row.get("sample_preparation_input_id", ""),
        event_identity=_event_identity(row.get("pdb_id", ""), ligand),
        pdb_id=row.get("pdb_id", ""),
        ligand_identity=ligand,
        residue_identity="",
        residue_atom_name=row.get("residue_atom_name", ""),
        ligand_atom_name=row.get("ligand_atom_name", ""),
        covalent_bond_atom_pair=row.get("covalent_bond_atom_pair", ""),
        conn_id="",
        conn_type_id="",
        explicit_bond_authority=(
            "struct_conn" in row.get("validation_status", "")
            and row.get("validation_status", "").startswith("validated_from_")
        ),
    )


def _index_projection(row: Mapping[str, str], layer: str) -> AtomPairLayerProjection:
    ligand = row.get("ligand_comp_id", "") or row.get("expected_het_id", "")
    return AtomPairLayerProjection(
        layer_name=layer,
        source_record_id=row.get("sample_index_row_id", ""),
        event_identity=_event_identity(row.get("pdb_id", ""), ligand),
        pdb_id=row.get("pdb_id", ""),
        ligand_identity=ligand,
        residue_identity=_residue_identity(
            row.get("covalent_residue_name", ""),
            row.get("covalent_residue_chain_id", ""),
            row.get("covalent_residue_index", ""),
        ),
        residue_atom_name=row.get("covalent_residue_atom_name", ""),
        ligand_atom_name=row.get("ligand_covalent_atom_name", ""),
        covalent_bond_atom_pair=row.get("covalent_bond_atom_pair", ""),
        conn_id=row.get("conn_id", ""),
        conn_type_id=row.get("conn_type_id", ""),
        explicit_bond_authority=(
            row.get("conn_id", "") != ""
            and row.get("conn_type_id") == "covale"
            and row.get("covalent_event_count") == "1"
            and row.get("ligand_residue_atom_pair_count") == "1"
            and row.get("covalent_event_table_path", "") != ""
            and row.get("ligand_residue_atom_pair_table_path", "") != ""
        ),
    )


def _projection_summary(
    projections: tuple[AtomPairProducerProjection | AtomPairLayerProjection, ...],
) -> str:
    values = [
        f"{item.event_identity}={item.covalent_bond_atom_pair}"
        for item in sorted(projections, key=lambda value: value.event_identity)
    ]
    return f"count={len(values)};" + "|".join(values)


def validate_producer_projection_chain(
    producers: tuple[AtomPairProducerProjection, ...],
    layers: Mapping[str, tuple[AtomPairLayerProjection, ...]],
    expected_layer_counts: Mapping[str, int],
    expected_layer_event_ids: Mapping[str, frozenset[str]] | None = None,
) -> ProducerProjectionValidation:
    reasons = []
    producers_by_key: dict[str, list[AtomPairProducerProjection]] = defaultdict(list)
    for projection in producers:
        producers_by_key[projection.event_identity].append(projection)
    conflicts = {
        key
        for key, values in producers_by_key.items()
        if len(values) != 1
        or len({item.covalent_bond_atom_pair for item in values}) != 1
        or len({item.producer_branch for item in values}) != 1
    }
    producer_index = {
        key: values[0]
        for key, values in producers_by_key.items()
        if len(values) == 1
    }
    if len(producers) != 11 or len(producer_index) != 11:
        reasons.append("producer_projection_count_or_identity_not_exact11")
    for projection in producers:
        if (
            not projection.selector_verified
            or not projection.explicit_bond_authority
            or projection.covalent_bond_atom_pair
            != _pair(
                projection.residue_atom_name, projection.ligand_atom_name
            )
        ):
            reasons.append(
                f"producer_projection_invalid:{projection.event_identity}"
            )
    layer_status = []
    authority_ok = all(
        item.explicit_bond_authority for item in producers
    )
    for layer_name, projections in layers.items():
        expected_count = expected_layer_counts[layer_name]
        expected_keys = (
            set(producer_index)
            if expected_layer_event_ids is None
            else set(expected_layer_event_ids[layer_name])
        )
        layer_by_key: dict[str, list[AtomPairLayerProjection]] = defaultdict(list)
        for projection in projections:
            layer_by_key[projection.event_identity].append(projection)
        layer_ok = len(projections) == expected_count
        if len(layer_by_key) != expected_count:
            layer_ok = False
        for key, values in layer_by_key.items():
            if len(values) != 1:
                layer_ok = False
                reasons.append(f"{layer_name}:duplicate_event:{key}")
                conflicts.add(key)
                continue
            observed = values[0]
            expected = producer_index.get(key)
            if expected is None or key not in expected_keys:
                layer_ok = False
                reasons.append(f"{layer_name}:unexpected_event:{key}")
                continue
            comparable = (
                observed.pdb_id == expected.pdb_id
                and observed.ligand_identity == expected.ligand_identity
                and observed.residue_atom_name == expected.residue_atom_name
                and observed.ligand_atom_name == expected.ligand_atom_name
                and observed.covalent_bond_atom_pair
                == expected.covalent_bond_atom_pair
                and (
                    not observed.residue_identity
                    or observed.residue_identity == expected.residue_identity
                )
                and (
                    not observed.conn_id
                    or observed.conn_id == expected.conn_id
                )
                and (
                    not observed.conn_type_id
                    or observed.conn_type_id == expected.conn_type_id
                )
                and observed.explicit_bond_authority
            )
            if not comparable:
                layer_ok = False
                reasons.append(f"{layer_name}:projection_mismatch:{key}")
                conflicts.add(key)
            authority_ok = authority_ok and observed.explicit_bond_authority
        missing = sorted(expected_keys - set(layer_by_key))
        if missing:
            layer_ok = False
            reasons.extend(
                f"{layer_name}:missing_event:{key}" for key in missing
            )
        layer_status.append((layer_name, layer_ok))
    unique_reasons = tuple(sorted(set(reasons)))
    producer_conflict = bool(conflicts or unique_reasons)
    return ProducerProjectionValidation(
        producer_projection_verified=(
            not producer_conflict
            and len(producer_index) == 11
            and all(value for _, value in layer_status)
            and authority_ok
        ),
        producer_conflict_present=producer_conflict,
        producer_conflict_event_ids=tuple(sorted(conflicts)),
        explicit_bond_authority_verified=authority_ok,
        layer_projection_status=tuple(layer_status),
        mismatch_reasons=unique_reasons,
    )


def validate_split_partitions(
    split_rows: Mapping[str, list[dict[str, str]]],
    unified_rows: list[dict[str, str]],
) -> tuple[bool, tuple[dict[str, str], ...]]:
    id_sets = {
        name: {row["sample_index_row_id"] for row in rows}
        for name, rows in split_rows.items()
    }
    names = tuple(sorted(id_sets))
    overlap = any(
        id_sets[names[left]] & id_sets[names[right]]
        for left in range(len(names))
        for right in range(left + 1, len(names))
    )
    union = set().union(*(id_sets[name] for name in names))
    unified_ids = {row["sample_index_row_id"] for row in unified_rows}
    combined = tuple(
        row
        for name in ("train", "validation", "test")
        for row in split_rows[name]
    )
    return (
        not overlap and union == unified_ids and len(combined) == len(union),
        combined,
    )


def _combined_source_sha(paths: tuple[str, ...]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(_git_show(path))
        digest.update(b"\0")
    return digest.hexdigest()


def _lineage_row(
    *,
    order: int,
    role: str,
    paths: tuple[str, ...],
    selector_kind: str,
    selector_expression: str,
    expected_count: int,
    observed_count: int,
    input_field: str,
    output_field: str,
    before: str,
    after: str,
    transformation: str,
    predecessor_projection: str,
    observed_projection: str,
    projection_verified: bool,
    authority_required: bool,
    authority_observed: bool,
    current_source: bool = False,
) -> dict[str, str]:
    selector_verified = (
        observed_count == expected_count and projection_verified
    )
    verified = (
        selector_verified
        and projection_verified
        and (not authority_required or authority_observed)
    )
    return {
        "lineage_order": str(order),
        "lineage_role": role,
        "source_path": "|".join(paths),
        "source_symbol_or_selector": selector_expression,
        "selector_kind": selector_kind,
        "selector_expression": selector_expression,
        "expected_record_count": str(expected_count),
        "observed_record_count": str(observed_count),
        "input_field_or_evidence": input_field,
        "output_field": output_field,
        "representation_before": before,
        "representation_after": after,
        "semantic_transformation": transformation,
        "predecessor_projection": predecessor_projection,
        "observed_projection": observed_projection,
        "predecessor_successor_projection_verified": _bool(
            projection_verified
        ),
        "explicit_bond_authority_required": _bool(authority_required),
        "explicit_bond_authority_observed": _bool(authority_observed),
        "distance_only_inference_used": "false",
        "current_source_of_truth": _bool(current_source),
        "committed_in_base": "true",
        "source_sha256": _combined_source_sha(paths),
        "selector_verified": _bool(selector_verified),
        "verified": _bool(verified),
    }


def _model_design_selector_verified() -> bool:
    source = _git_show(MODEL_INPUT_DESIGN_PATH).decode("utf-8")
    tree = ast.parse(source)
    string_values = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    forbidden_functions = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(term in node.name.lower() for term in ("forward", "loss", "collate"))
    }
    tensor_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and (
            (
                isinstance(node.func, ast.Name)
                and node.func.id.lower() in {"tensor", "as_tensor"}
            )
            or (
                isinstance(node.func, ast.Attribute)
                and node.func.attr.lower() in {"tensor", "as_tensor"}
            )
        )
    ]
    imported_roots = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    return (
        "ligand_residue_atom_pair_label_status" in string_values
        and "ligand_residue_atom_pair_label_semantics" in string_values
        and not forbidden_functions
        and not tensor_calls
        and "torch" not in imported_roots
    )


@lru_cache(maxsize=1)
def build_executable_lineage_evidence() -> ExecutableLineageEvidence:
    original = build_original_producer_projections()
    expansion = build_expansion_producer_projections()
    producers = tuple(
        sorted((*original, *expansion), key=lambda item: item.event_identity)
    )
    original_keys = {item.event_identity for item in original}
    expansion_keys = {item.event_identity for item in expansion}
    final_rows = _base_csv(FINAL_DATASET_PATH)
    event_rows_by_key = {}
    pair_rows_by_key = {}
    event_paths_by_key = {}
    pair_paths_by_key = {}
    for final_row in final_rows:
        key = _event_identity(
            final_row["pdb_id"], final_row["ligand_comp_id"]
        )
        event_path = final_row["covalent_event_table_path"]
        pair_path = final_row["ligand_residue_atom_pair_table_path"]
        event_rows = _base_csv(event_path)
        pair_rows = _base_csv(pair_path)
        if len(event_rows) == 1:
            event_rows_by_key[key] = event_rows[0]
        if len(pair_rows) == 1:
            pair_rows_by_key[key] = pair_rows[0]
        event_paths_by_key[key] = event_path
        pair_paths_by_key[key] = pair_path
    original_events = tuple(
        _event_projection(event_rows_by_key[key], "original_event_tables")
        for key in sorted(original_keys & set(event_rows_by_key))
    )
    expansion_events = tuple(
        _event_projection(event_rows_by_key[key], "expansion_event_tables")
        for key in sorted(expansion_keys & set(event_rows_by_key))
    )
    original_pairs = tuple(
        _pair_projection(pair_rows_by_key[key], "original_pair_tables")
        for key in sorted(original_keys & set(pair_rows_by_key))
    )
    expansion_pairs = tuple(
        _pair_projection(pair_rows_by_key[key], "expansion_pair_tables")
        for key in sorted(expansion_keys & set(pair_rows_by_key))
    )
    original_index_rows = _base_csv(ORIGINAL_SAMPLE_INDEX_PATH)
    expansion_index_rows = _base_csv(EXPANSION_SAMPLE_INDEX_PATH)
    unified_rows = _base_csv(UNIFIED_SAMPLE_INDEX_PATH)
    split_rows = {
        name: _base_csv(path)
        for name, path in zip(
            ("train", "validation", "test"), SPLIT_PATHS, strict=True
        )
    }
    split_ok, split_union_rows = validate_split_partitions(
        split_rows, unified_rows
    )
    layers = {
        "original_event_tables": original_events,
        "expansion_event_tables": expansion_events,
        "original_pair_tables": original_pairs,
        "expansion_pair_tables": expansion_pairs,
        "original_sample_index": tuple(
            _index_projection(row, "original_sample_index")
            for row in original_index_rows
        ),
        "expansion_sample_index": tuple(
            _index_projection(row, "expansion_sample_index")
            for row in expansion_index_rows
        ),
        "unified_sample_index": tuple(
            _index_projection(row, "unified_sample_index")
            for row in unified_rows
        ),
        "split_union": tuple(
            _index_projection(row, "split_union")
            for row in split_union_rows
        ),
        "final_dataset": tuple(
            _index_projection(row, "final_dataset") for row in final_rows
        ),
    }
    expected_counts = {
        "original_event_tables": 3,
        "expansion_event_tables": 8,
        "original_pair_tables": 3,
        "expansion_pair_tables": 8,
        "original_sample_index": 3,
        "expansion_sample_index": 8,
        "unified_sample_index": 11,
        "split_union": 11,
        "final_dataset": 11,
    }
    all_keys = frozenset(original_keys | expansion_keys)
    expected_event_ids = {
        "original_event_tables": frozenset(original_keys),
        "expansion_event_tables": frozenset(expansion_keys),
        "original_pair_tables": frozenset(original_keys),
        "expansion_pair_tables": frozenset(expansion_keys),
        "original_sample_index": frozenset(original_keys),
        "expansion_sample_index": frozenset(expansion_keys),
        "unified_sample_index": all_keys,
        "split_union": all_keys,
        "final_dataset": all_keys,
    }
    validation = validate_producer_projection_chain(
        producers, layers, expected_counts, expected_event_ids
    )
    layer_status = dict(validation.layer_projection_status)
    original_projection_ok = (
        len(original) == 3
        and len({item.event_identity for item in original}) == 3
        and all(
            item.selector_verified
            and item.explicit_bond_authority
            and item.covalent_bond_atom_pair
            == _pair(item.residue_atom_name, item.ligand_atom_name)
            for item in original
        )
    )
    expansion_projection_ok = (
        len(expansion) == 8
        and len({item.event_identity for item in expansion}) == 8
        and all(
            item.selector_verified
            and item.explicit_bond_authority
            and item.covalent_bond_atom_pair
            == _pair(item.residue_atom_name, item.ligand_atom_name)
            for item in expansion
        )
    )
    qa = _base_json(FINAL_QA_MANIFEST_PATH)
    qa_ok = (
        qa.get("final_dataset_row_count") == 11
        and qa.get("all_schema_lineage_qa_passed") is True
        and qa.get("canonical_mask_task_count") == 5
        and qa.get("ready_for_training") is False
    )
    feature_matches = [
        row
        for row in _base_csv(FEATURE_AUDIT_PATH)
        if row.get("auxiliary_label_name")
        == "ligand_residue_atom_pair_label"
    ]
    feature_ok = (
        len(feature_matches) == 1
        and feature_matches[0].get("required_before_training") == "True"
        and feature_matches[0].get("current_materialized") == "True"
        and "audit atom pair semantics"
        in feature_matches[0].get("future_required_action", "")
    )
    tensor_matches = [
        row
        for row in _base_csv(TENSORIZATION_PATH)
        if row.get("label_blocker_item")
        == "covalent_atom_pair_label_not_training_final"
    ]
    tensor_ok = (
        len(tensor_matches) == 1
        and tensor_matches[0].get("current_tensorization_status") == "blocked"
        and tensor_matches[0].get(
            "blocks_actual_tensor_dataloader_smoke"
        )
        == "True"
        and tensor_matches[0].get("blocks_training") == "True"
    )
    model_ok = _model_design_selector_verified()
    original_event_paths = tuple(
        event_paths_by_key[key] for key in sorted(original_keys)
    )
    expansion_event_paths = tuple(
        event_paths_by_key[key] for key in sorted(expansion_keys)
    )
    original_pair_paths = tuple(
        pair_paths_by_key[key] for key in sorted(original_keys)
    )
    expansion_pair_paths = tuple(
        pair_paths_by_key[key] for key in sorted(expansion_keys)
    )
    producer_summary = _projection_summary(producers)
    row_specs = (
        (1, "explicit_bond_producer_original", (ORIGINAL_PRODUCER_PATH,), "csv_filter", "ready_candidate_scope=cys_sg_struct_conn_validated_ligand_event_v0", 3, len(original), "validated struct_conn candidate fields", "AtomPairProducerProjection", "explicit bond partner fields", "3 original producer projections", "none", _projection_summary(original), original_projection_ok, True, all(item.explicit_bond_authority for item in original), False),
        (2, "explicit_bond_producer_expansion", (EXPANSION_PRODUCER_PATH, EXPANSION_RELEVANT_ROWS_PATH), "csv_filter_join", "confirmed_unique_exact_match and exact relevant struct_conn row", 8, len(expansion), "crosscheck and relevant struct_conn fields", "AtomPairProducerProjection", "explicit crosscheck fields", "8 expansion producer projections", "none", _projection_summary(expansion), expansion_projection_ok, True, all(item.explicit_bond_authority for item in expansion), False),
        (3, "event_materializer_original", original_event_paths, "dynamic_path_dereference", "final rows in original producer keys -> covalent_event_table_path", 3, len(original_events), "original producer projections", "event table projections", "producer atom identities", "validated event metadata", _projection_summary(original), _projection_summary(original_events), layer_status["original_event_tables"], True, all(item.explicit_bond_authority for item in original_events), False),
        (4, "event_materializer_expansion", expansion_event_paths, "dynamic_path_dereference", "final rows in expansion producer keys -> covalent_event_table_path", 8, len(expansion_events), "expansion producer projections", "event table projections", "producer atom identities", "validated event metadata", _projection_summary(expansion), _projection_summary(expansion_events), layer_status["expansion_event_tables"], True, all(item.explicit_bond_authority for item in expansion_events), False),
        (5, "pair_table_materializer_original", original_pair_paths, "dynamic_path_dereference", "final rows in original producer keys -> ligand_residue_atom_pair_table_path", 3, len(original_pairs), "original producer projections", "pair table projections", "explicit pair identities", "atom-name pair plus coordinates", _projection_summary(original), _projection_summary(original_pairs), layer_status["original_pair_tables"], True, all(item.explicit_bond_authority for item in original_pairs), False),
        (6, "pair_table_materializer_expansion", expansion_pair_paths, "dynamic_path_dereference", "final rows in expansion producer keys -> ligand_residue_atom_pair_table_path", 8, len(expansion_pairs), "expansion producer projections", "pair table projections", "explicit pair identities", "atom-name pair plus coordinates", _projection_summary(expansion), _projection_summary(expansion_pairs), layer_status["expansion_pair_tables"], True, all(item.explicit_bond_authority for item in expansion_pairs), False),
        (7, "sample_index_materializer_original", (ORIGINAL_SAMPLE_INDEX_PATH,), "csv_all_rows", "all original sample-index rows", 3, len(original_index_rows), "original event and pair projections", "original sample-index projections", "event/pair metadata", "sample metadata string plus paths/counts", _projection_summary(original), _projection_summary(layers["original_sample_index"]), layer_status["original_sample_index"], True, all(item.explicit_bond_authority for item in layers["original_sample_index"]), False),
        (8, "sample_index_materializer_expansion", (EXPANSION_SAMPLE_INDEX_PATH,), "csv_all_rows", "all expansion sample-index rows", 8, len(expansion_index_rows), "expansion event and pair projections", "expansion sample-index projections", "event/pair metadata", "sample metadata string plus paths/counts", _projection_summary(expansion), _projection_summary(layers["expansion_sample_index"]), layer_status["expansion_sample_index"], True, all(item.explicit_bond_authority for item in layers["expansion_sample_index"]), False),
        (9, "successor_merge", (UNIFIED_SAMPLE_INDEX_PATH,), "set_union", "original IDs union expansion IDs; intersection empty", 11, len(unified_rows), "two disjoint sample indexes", "unified sample-index projections", "3+8 sample rows", "11 unified rows", producer_summary, _projection_summary(layers["unified_sample_index"]), layer_status["unified_sample_index"] and not (original_keys & expansion_keys), True, all(item.explicit_bond_authority for item in layers["unified_sample_index"]), False),
        (10, "split_materializer", SPLIT_PATHS, "partition_union", "train validation test disjoint union equals unified", 11, len(split_union_rows), "unified projections", "split-union projections", "11 unified rows", "three disjoint split artifacts", _projection_summary(layers["unified_sample_index"]), _projection_summary(layers["split_union"]), layer_status["split_union"] and split_ok, True, all(item.explicit_bond_authority for item in layers["split_union"]), False),
        (11, "current_materialized_source_of_truth", (FINAL_DATASET_PATH,), "identity_set_equality", "split union identity and pair projection equals final", 11, len(final_rows), "split-union projections", "final-dataset projections", "split-preserved metadata", "canonical 11-row final dataset", _projection_summary(layers["split_union"]), _projection_summary(layers["final_dataset"]), layer_status["final_dataset"], True, all(item.explicit_bond_authority for item in layers["final_dataset"]), True),
        (12, "current_qa_gate", (FINAL_QA_MANIFEST_PATH,), "json_selector_conjunction", "final_dataset_row_count=11 and QA/mask/training fields exact", 1, int(qa_ok), "final dataset", "QA status", "11 final projections", "validated final-dataset status", _projection_summary(layers["final_dataset"]), "row_count=11;schema_lineage=true;masks=5;ready_for_training=false", qa_ok, False, False, False),
        (13, "feature_semantics_audit_reference", (FEATURE_AUDIT_PATH,), "csv_exact_row", "auxiliary_label_name=ligand_residue_atom_pair_label", 1, len(feature_matches), "materialized pair metadata", "feature-audit-required status", "pair metadata", "status only; not tensor or target", "final_pair_metadata_present", "audit_required=true;materialized=true", feature_ok, False, False, False),
        (14, "tensorization_blocker", (TENSORIZATION_PATH,), "csv_exact_row", "label_blocker_item=covalent_atom_pair_label_not_training_final", 1, len(tensor_matches), "feature status", "blocked tensorization status", "metadata string", "blocked dataloader and training", "feature_audit_required", "tensorization=blocked;dataloader=true;training=true", tensor_ok, False, False, False),
        (15, "future_model_input_reference", (MODEL_INPUT_DESIGN_PATH,), "python_ast", "exact design/status string constants; no tensor/forward/loss/collate implementation", 2, 2 if model_ok else 0, "future auxiliary label concept", "design/status references", "metadata/status", "future reference only", "tensorization_blocked", "design_status_refs=2;runtime_consumers=0", model_ok, False, False, False),
    )
    lineage_rows = tuple(
        _lineage_row(
            order=spec[0],
            role=spec[1],
            paths=spec[2],
            selector_kind=spec[3],
            selector_expression=spec[4],
            expected_count=spec[5],
            observed_count=spec[6],
            input_field=spec[7],
            output_field=spec[8],
            before=spec[9],
            after=spec[10],
            transformation="executable selector and projection validation",
            predecessor_projection=spec[11],
            observed_projection=spec[12],
            projection_verified=spec[13],
            authority_required=spec[14],
            authority_observed=spec[15],
            current_source=spec[16],
        )
        for spec in row_specs
    )
    selectors_ok = all(row["selector_verified"] == "true" for row in lineage_rows)
    transitions_ok = all(
        row["predecessor_successor_projection_verified"] == "true"
        and row["verified"] == "true"
        for row in lineage_rows
    )
    return ExecutableLineageEvidence(
        lineage_rows=lineage_rows,
        producer_projections=producers,
        producer_validation=validation,
        lineage_selectors_executed=selectors_ok,
        lineage_transition_projections_verified=transitions_ok,
        original_producer_record_count=len(original),
        expansion_producer_record_count=len(expansion),
        original_sample_index_record_count=len(original_index_rows),
        expansion_sample_index_record_count=len(expansion_index_rows),
        unified_sample_index_record_count=len(unified_rows),
        split_union_record_count=len(split_union_rows),
        final_dataset_record_count=len(final_rows),
        split_partition_verified=split_ok,
    )


def build_source_lineage_rows() -> tuple[dict[str, str], ...]:
    return build_executable_lineage_evidence().lineage_rows


def _event_and_pair_rows(
    final_row: Mapping[str, str],
) -> tuple[dict[str, str], dict[str, str]]:
    event_rows = _base_csv(final_row["covalent_event_table_path"])
    pair_rows = _base_csv(final_row["ligand_residue_atom_pair_table_path"])
    if len(event_rows) != 1 or len(pair_rows) != 1:
        raise AssertionError(
            f"non-single pair cardinality: {final_row['sample_index_row_id']}"
        )
    return event_rows[0], pair_rows[0]


def build_current_representation_rows() -> tuple[dict[str, str], ...]:
    final_rows = _base_csv(FINAL_DATASET_PATH)
    qa = _base_json(FINAL_QA_MANIFEST_PATH)
    if (
        len(final_rows) != 11
        or qa.get("final_dataset_row_count") != len(final_rows)
        or qa.get("all_schema_lineage_qa_passed") is not True
    ):
        raise AssertionError("current final-dataset QA lineage is incomplete")
    output = []
    for row in final_rows:
        event, pair = _event_and_pair_rows(row)
        reconstructed = (
            f"{row['covalent_residue_atom_name']}--"
            f"{row['ligand_covalent_atom_name']}"
        )
        values = {
            row["covalent_bond_atom_pair"],
            event["covalent_bond_atom_pair"],
            pair["covalent_bond_atom_pair"],
            reconstructed,
            f"{pair['residue_atom_name']}--{pair['ligand_atom_name']}",
        }
        explicit = (
            event.get("conn_id") == row["conn_id"]
            and event.get("conn_type_id") == row["conn_type_id"] == "covale"
            and "struct_conn" in event.get("event_source", "")
            and event.get("event_status") == "validated"
            and pair.get("validation_status", "").startswith("validated_from_")
        )
        verified = (
            len(values) == 1
            and explicit
            and row["covalent_event_count"] == "1"
            and row["ligand_residue_atom_pair_count"] == "1"
            and row["ready_for_training_current_step"] == "False"
        )
        output.append(
            {
                "source_artifact": FINAL_DATASET_PATH,
                "source_row_identity": row["sample_index_row_id"],
                "sample_or_event_id": row["sample_preparation_input_id"],
                "pdb_id": row["pdb_id"],
                "ligand_comp_id_or_het_id": row["ligand_comp_id"],
                "residue_name": row["covalent_residue_name"],
                "residue_chain_id": row["covalent_residue_chain_id"],
                "residue_index": row["covalent_residue_index"],
                "residue_insertion_code_if_available": "",
                "residue_atom_name": row["covalent_residue_atom_name"],
                "ligand_atom_name": row["ligand_covalent_atom_name"],
                "stored_covalent_bond_atom_pair": row[
                    "covalent_bond_atom_pair"
                ],
                "pair_reconstructed_from_separate_fields": reconstructed,
                "stored_matches_reconstructed": _bool(len(values) == 1),
                "explicit_bond_evidence_type": (
                    f"validated_struct_conn:{event['event_source']}"
                ),
                "conn_id_if_available": row["conn_id"],
                "conn_type_id_if_available": row["conn_type_id"],
                "current_validation_status": (
                    f"{event['event_status']}|{pair['validation_status']}|"
                    "final_dataset_qa_v1_passed"
                ),
                "current_training_use_status": (
                    "metadata_only_not_training_final_ready_for_training_false"
                ),
                "event_pair_cardinality": "1",
                "observed_delimiter": "--",
                "observed_ordering": (
                    "residue_atom_name_then_ligand_atom_name"
                ),
                "value_identity_kind": (
                    "atom_name_pair_not_atom_table_index_pair"
                ),
                "verified": _bool(verified),
            }
        )
    return tuple(output)


@lru_cache(maxsize=1)
def _grep_occurrences() -> dict[tuple[str, str], list[int]]:
    args = ["grep", "-n", "-I"]
    for term in MATCHED_TERMS:
        args.extend(("-e", term))
    args.extend(
        (
            BASE_COMMIT,
            "--",
            "src",
            "tests",
            "scripts",
            "docs",
            "data/derived",
            "equivariant_diffusion",
            "lightning_modules.py",
            "dataset.py",
            ":(exclude)data/raw/**",
            ":(exclude,glob)**/*.pt",
            ":(exclude,glob)**/*.ckpt",
            ":(exclude,glob)**/*.pth",
            ":(exclude,glob)**/*.pkl",
            ":(exclude,glob)**/*.lmdb",
            ":(exclude,glob)**/*.npz",
        )
    )
    payload = _run_git(*args, allow_no_match=True).decode(
        "utf-8", errors="strict"
    )
    found: dict[tuple[str, str], list[int]] = defaultdict(list)
    prefix = BASE_COMMIT + ":"
    for output_line in payload.splitlines():
        if not output_line.startswith(prefix):
            raise AssertionError("unexpected git grep output")
        path, line_number, text = output_line[len(prefix) :].split(":", 2)
        for term in MATCHED_TERMS:
            if term in text:
                found[(path, term)].append(int(line_number))
    return found


def _consumer_role(path: str, term: str) -> str:
    name = Path(path).name.lower()
    lowered = path.lower()
    if path.startswith("tests/"):
        return "test_only"
    if path.startswith("docs/"):
        return "documentation_only"
    if path.startswith("scripts/"):
        return "qa_gate"
    if path.startswith(("equivariant_diffusion/", "lightning_modules.py")):
        raise AssertionError(f"unexpected model-path consumer: {path}")
    if path == "dataset.py":
        raise AssertionError("unexpected dataloader consumer")
    if path.startswith("data/derived/"):
        if "tensorization" in lowered:
            return "tensorization_blocker"
        if "schema" in name or "contract" in name or "mapping" in name:
            return "schema_declaration"
        if "status" in name or "issue" in name or "readiness" in name:
            return "status_declaration"
        if "path" in term and name.endswith((".json", ".csv")):
            return "path_reference"
        if "qa" in name or "validation" in name or "audit" in name:
            return "validator"
        if "manifest" in name or "report" in name or "inventory" in name:
            return "report_or_manifest"
        return "materializer"
    if "tensorization" in lowered:
        return "tensorization_blocker"
    if "qa_gate" in lowered or "validation" in lowered:
        return "qa_gate"
    if "schema" in lowered or "design" in lowered or "contract" in lowered:
        return "schema_declaration"
    if "sample_preparation" in lowered or "struct_conn" in lowered:
        return "producer"
    if "materialization" in lowered or "sample_index" in lowered:
        return "materializer"
    return "semantic_transformer"


def _source_reads_value(path: str, term: str) -> bool:
    if not path.startswith("src/") or term not in {
        "covalent_bond_atom_pair",
        "residue_atom_name",
        "ligand_atom_name",
        "covalent_residue_atom_name",
        "ligand_covalent_atom_name",
    }:
        return False
    text = _git_show(path).decode("utf-8")
    probes = (
        f'["{term}"]',
        f"['{term}']",
        f'.get("{term}"',
        f".get('{term}'",
    )
    return any(probe in text for probe in probes)


def build_downstream_consumer_rows() -> tuple[dict[str, str], ...]:
    occurrences = _grep_occurrences()
    rows = []
    for (path, term), numbers in sorted(occurrences.items()):
        role = _consumer_role(path, term)
        if role not in CONSUMER_ROLES:
            raise AssertionError(f"invalid consumer role: {role}")
        reads_value = _source_reads_value(path, term)
        status_only = (
            "status" in term
            or term == "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED"
            or role in {"status_declaration", "tensorization_blocker"}
        )
        path_only = (
            term
            in {
                "ligand_residue_atom_pair_table_path",
                "covalent_event_table_path",
            }
            and not reads_value
        )
        text = _git_show(path).decode("utf-8", errors="strict")
        interprets_delimiter = (
            term in {"covalent_bond_atom_pair", "SG--CAG"}
            and ("--" in text)
            and role
            in {"producer", "semantic_transformer", "materializer", "validator"}
        )
        interprets_order = interprets_delimiter and (
            "residue_atom_name" in text or "covalent_residue_atom_name" in text
        )
        rows.append(
            {
                "consumer_path": path,
                "consumer_symbol_or_selector": (
                    f"git grep {BASE_COMMIT};term={term};"
                    f"occurrences={len(numbers)};"
                    f"first_line={min(numbers)};last_line={max(numbers)}"
                ),
                "matched_term": term,
                "consumer_role": role,
                "reads_pair_value": _bool(reads_value),
                "reads_pair_status_only": _bool(status_only),
                "reads_pair_table_path_only": _bool(path_only),
                "interprets_pair_order": _bool(interprets_order),
                "interprets_pair_delimiter": _bool(interprets_delimiter),
                "maps_to_protein_atom_index": "false",
                "maps_to_ligand_atom_index": "false",
                "creates_tensor": "false",
                "uses_in_collate": "false",
                "uses_in_forward": "false",
                "uses_in_loss": "false",
                "uses_as_training_target": "false",
                "current_behavior": (
                    "reads_or_transforms_committed_metadata"
                    if reads_value
                    else "declares_validates_reports_or_references_only"
                ),
                "semantic_assumption": (
                    "observed atom-name metadata; no future encoding implied"
                ),
                "source_sha256": hashlib.sha256(
                    text.encode("utf-8")
                ).hexdigest(),
                "verified": "true",
            }
        )
    if not rows:
        raise AssertionError("BASE grep produced no audit references")
    return tuple(rows)


def _negative_model_consumer_matches() -> dict[str, bool]:
    matches = {}
    for scope in ("equivariant_diffusion", "lightning_modules.py", "dataset.py"):
        args = ["grep", "-n", "-I"]
        for term in MODEL_CONSUMER_TERMS:
            args.extend(("-e", term))
        args.extend((BASE_COMMIT, "--", scope))
        matches[scope] = bool(_run_git(*args, allow_no_match=True))
    return matches


def _negative_model_consumer_check() -> None:
    matches = _negative_model_consumer_matches()
    unexpected = sorted(scope for scope, present in matches.items() if present)
    if unexpected:
        raise AssertionError(
            "unexpected actual model/dataloader match: " + "|".join(unexpected)
        )


def build_unresolved_semantics_rows() -> tuple[dict[str, str], ...]:
    if len(UNRESOLVED_SPECS) != 24:
        raise AssertionError("unresolved semantics inventory is not Exact24")
    rows = []
    for item, observed, risk in UNRESOLVED_SPECS:
        rows.append(
            {
                "semantics_item": item,
                "current_observed_state": observed,
                "currently_formally_defined": "false",
                "current_evidence_path": FINAL_DATASET_PATH,
                "risk_if_left_implicit": risk,
                "required_for_encoding_contract": "true",
                "required_for_feature_semantics_audit": _bool(
                    item
                    not in {
                        "checkpoint compatibility impact",
                        "protein full-atom table row mapping",
                        "pocket atom table row mapping",
                    }
                ),
                "required_for_tensorization": _bool(
                    item
                    not in {
                        "current Cys-SG compatibility",
                        "checkpoint compatibility impact",
                    }
                ),
                "required_for_model_integration": "true",
                "decision_made_current_audit": "false",
                "deferred_to_next_contract": "true",
                "verified": "true",
            }
        )
    return tuple(rows)


def _verify_masks_and_training_gate() -> None:
    qa = _base_json(FINAL_QA_MANIFEST_PATH)
    observed_masks = tuple(
        (item[0], item[1])
        for item in qa.get("canonical_mask_pairs", ())
        if isinstance(item, list) and len(item) == 2
    )
    if observed_masks != CANONICAL_MASKS:
        raise AssertionError("canonical Exact5 mask contract changed")
    if (
        qa.get("canonical_mask_task_count") != 5
        or qa.get("feature_semantics_known_for_training") is not False
        or qa.get("model_forward_called") is not False
        or qa.get("loss_compute_called") is not False
        or qa.get("optimizer_created") is not False
        or qa.get("ready_for_training") is not False
    ):
        raise AssertionError("final QA training boundary changed")
    tensor_rows = _base_csv(TENSORIZATION_PATH)
    blockers = {row["label_blocker_item"]: row for row in tensor_rows}
    required = (
        "covalent_atom_pair_label_not_training_final",
        "batch_collate_for_labels_blocked",
        "loss_integration_blocked",
        "training_targets_blocked",
    )
    if any(
        blockers.get(item, {}).get("current_tensorization_status") != "blocked"
        for item in required
    ):
        raise AssertionError("pair tensorization/training blocker changed")


def _issue_payload_and_rows() -> tuple[bytes, list[dict[str, str]]]:
    payload = _git_show(PREDECESSOR_ISSUE_PATH)
    if hashlib.sha256(payload).hexdigest() != PREDECESSOR_ISSUE_SHA256:
        raise AssertionError("predecessor issue inventory SHA changed")
    rows = _csv_from_bytes(payload)
    effective = [
        row["issue_id"]
        for row in rows
        if row["successor_effective_status"] == "open"
    ]
    if effective != [
        "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
        "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
    ]:
        raise AssertionError("effective-open issue set changed")
    return payload, rows


@dataclass(frozen=True)
class DerivedAuditEvidence:
    current_source_lineage_verified: bool
    current_representation_inventory_complete: bool
    current_consumer_inventory_complete: bool
    current_semantics_internally_consistent: bool
    explicit_bond_authority_verified: bool
    distance_only_inference_used: bool
    current_pair_is_metadata_string: bool
    current_pair_is_tensor_index_pair: bool
    current_dataloader_consumer_present: bool
    current_model_forward_consumer_present: bool
    current_loss_consumer_present: bool
    current_training_target_tensor_present: bool
    unresolved_semantics_inventory_complete: bool
    record_conflict_present: bool
    record_conflict_event_ids: tuple[str, ...]
    producer_conflict_present: bool
    producer_projection_verified: bool


def record_conflict_event_ids(
    representation: tuple[dict[str, str], ...],
) -> tuple[str, ...]:
    pairs_by_event: dict[str, set[str]] = defaultdict(set)
    for row in representation:
        pairs_by_event[row["sample_or_event_id"]].add(
            row["stored_covalent_bond_atom_pair"]
        )
    return tuple(
        sorted(
            event_identity
            for event_identity, pairs in pairs_by_event.items()
            if len(pairs) > 1
        )
    )


def _consumer_inventory_complete(
    consumers: tuple[dict[str, str], ...],
) -> bool:
    occurrences = _grep_occurrences()
    expected_keys = set(occurrences)
    observed_keys = {
        (row["consumer_path"], row["matched_term"]) for row in consumers
    }
    if expected_keys != observed_keys or len(consumers) != len(expected_keys):
        return False
    rows_by_key = {
        (row["consumer_path"], row["matched_term"]): row for row in consumers
    }
    for key, numbers in occurrences.items():
        path, term = key
        expected_selector = (
            f"git grep {BASE_COMMIT};term={term};"
            f"occurrences={len(numbers)};"
            f"first_line={min(numbers)};last_line={max(numbers)}"
        )
        row = rows_by_key[key]
        if (
            row["consumer_symbol_or_selector"] != expected_selector
            or row["verified"] != "true"
            or row["source_sha256"] != _blob_sha(path)
        ):
            return False
    return True


def derive_audit_evidence(
    *,
    lineage_evidence: ExecutableLineageEvidence,
    representation: tuple[dict[str, str], ...],
    consumers: tuple[dict[str, str], ...],
    unresolved: tuple[dict[str, str], ...],
) -> DerivedAuditEvidence:
    record_conflicts = record_conflict_event_ids(representation)
    negative_matches = _negative_model_consumer_matches()
    lineage_verified = (
        len(lineage_evidence.lineage_rows) == 15
        and lineage_evidence.lineage_selectors_executed
        and lineage_evidence.lineage_transition_projections_verified
        and all(
            row["selector_verified"] == "true"
            and row["predecessor_successor_projection_verified"] == "true"
            and row["verified"] == "true"
            for row in lineage_evidence.lineage_rows
        )
    )
    representation_complete = (
        len(representation) == 11
        and len({row["sample_or_event_id"] for row in representation}) == 11
        and all(
            row["verified"] == "true"
            and row["stored_matches_reconstructed"] == "true"
            and row["stored_covalent_bond_atom_pair"]
            == row["pair_reconstructed_from_separate_fields"]
            for row in representation
        )
    )
    consumer_complete = (
        _consumer_inventory_complete(consumers)
        and not any(negative_matches.values())
    )
    producer_validation = lineage_evidence.producer_validation
    producer_verified = (
        producer_validation.producer_projection_verified
        and lineage_evidence.original_producer_record_count == 3
        and lineage_evidence.expansion_producer_record_count == 8
        and len(lineage_evidence.producer_projections) == 11
        and lineage_evidence.original_sample_index_record_count == 3
        and lineage_evidence.expansion_sample_index_record_count == 8
        and lineage_evidence.unified_sample_index_record_count == 11
        and lineage_evidence.split_union_record_count == 11
        and lineage_evidence.final_dataset_record_count == 11
        and lineage_evidence.split_partition_verified
    )
    dataloader_present = (
        negative_matches.get("dataset.py", False)
        or any(
            row["consumer_role"] == "dataloader_consumer"
            or row["uses_in_collate"] == "true"
            for row in consumers
        )
    )
    model_forward_present = (
        negative_matches.get("equivariant_diffusion", False)
        or negative_matches.get("lightning_modules.py", False)
        or any(
            row["consumer_role"] == "model_forward_consumer"
            or row["uses_in_forward"] == "true"
            for row in consumers
        )
    )
    loss_present = any(
        row["consumer_role"] == "loss_consumer"
        or row["uses_in_loss"] == "true"
        for row in consumers
    )
    target_present = any(
        row["consumer_role"] == "training_target_consumer"
        or row["uses_as_training_target"] == "true"
        for row in consumers
    )
    pair_is_metadata = bool(representation) and all(
        row["value_identity_kind"]
        == "atom_name_pair_not_atom_table_index_pair"
        and row["observed_delimiter"] == "--"
        and row["observed_ordering"]
        == "residue_atom_name_then_ligand_atom_name"
        for row in representation
    )
    pair_is_tensor_index = any(
        row["value_identity_kind"] != "atom_name_pair_not_atom_table_index_pair"
        for row in representation
    ) or any(
        row["maps_to_protein_atom_index"] == "true"
        or row["maps_to_ligand_atom_index"] == "true"
        or row["creates_tensor"] == "true"
        for row in consumers
    )
    unresolved_complete = (
        len(unresolved) == 24
        and len({row["semantics_item"] for row in unresolved}) == 24
        and all(
            row["currently_formally_defined"] == "false"
            and row["decision_made_current_audit"] == "false"
            and row["deferred_to_next_contract"] == "true"
            and row["verified"] == "true"
            for row in unresolved
        )
    )
    distance_only = any(
        row["distance_only_inference_used"] == "true"
        for row in lineage_evidence.lineage_rows
    ) or any(
        not row["explicit_bond_evidence_type"].startswith(
            "validated_struct_conn:"
        )
        for row in representation
    )
    explicit_authority = (
        producer_validation.explicit_bond_authority_verified
        and all(
            row["explicit_bond_evidence_type"].startswith(
                "validated_struct_conn:"
            )
            and row["conn_id_if_available"] != ""
            and row["conn_type_id_if_available"] == "covale"
            for row in representation
        )
    )
    producer_conflict = producer_validation.producer_conflict_present
    return DerivedAuditEvidence(
        current_source_lineage_verified=lineage_verified,
        current_representation_inventory_complete=representation_complete,
        current_consumer_inventory_complete=consumer_complete,
        current_semantics_internally_consistent=(
            not record_conflicts
            and not producer_conflict
            and producer_verified
        ),
        explicit_bond_authority_verified=explicit_authority,
        distance_only_inference_used=distance_only,
        current_pair_is_metadata_string=pair_is_metadata,
        current_pair_is_tensor_index_pair=pair_is_tensor_index,
        current_dataloader_consumer_present=dataloader_present,
        current_model_forward_consumer_present=model_forward_present,
        current_loss_consumer_present=loss_present,
        current_training_target_tensor_present=target_present,
        unresolved_semantics_inventory_complete=unresolved_complete,
        record_conflict_present=bool(record_conflicts),
        record_conflict_event_ids=record_conflicts,
        producer_conflict_present=producer_conflict,
        producer_projection_verified=producer_verified,
    )


def _audit_decision(evidence: DerivedAuditEvidence):
    return audit.audit_covapie_covalent_bond_atom_pair_current_semantics_and_downstream_consumers_v1(
        current_source_lineage_verified=evidence.current_source_lineage_verified,
        current_representation_inventory_complete=(
            evidence.current_representation_inventory_complete
        ),
        current_consumer_inventory_complete=(
            evidence.current_consumer_inventory_complete
        ),
        current_semantics_internally_consistent=(
            evidence.current_semantics_internally_consistent
        ),
        explicit_bond_authority_verified=(
            evidence.explicit_bond_authority_verified
        ),
        distance_only_inference_used=evidence.distance_only_inference_used,
        current_pair_is_metadata_string=evidence.current_pair_is_metadata_string,
        current_pair_is_tensor_index_pair=(
            evidence.current_pair_is_tensor_index_pair
        ),
        current_dataloader_consumer_present=(
            evidence.current_dataloader_consumer_present
        ),
        current_model_forward_consumer_present=(
            evidence.current_model_forward_consumer_present
        ),
        current_loss_consumer_present=evidence.current_loss_consumer_present,
        current_training_target_tensor_present=(
            evidence.current_training_target_tensor_present
        ),
        unresolved_semantics_inventory_complete=(
            evidence.unresolved_semantics_inventory_complete
        ),
    )


def _manifest(
    csv_payloads: Mapping[str, bytes],
    lineage_evidence: ExecutableLineageEvidence,
    derived_evidence: DerivedAuditEvidence,
    decision: audit.CovalentBondAtomPairCurrentSemanticsAuditDecision,
    representation: tuple[dict[str, str], ...],
    consumers: tuple[dict[str, str], ...],
    unresolved: tuple[dict[str, str], ...],
    issue_rows: list[dict[str, str]],
) -> dict[str, object]:
    lineage = lineage_evidence.lineage_rows
    pairs = [row["stored_covalent_bond_atom_pair"] for row in representation]
    pair_counts = Counter(pairs)
    role_counts = Counter(row["consumer_role"] for row in consumers)
    return {
        **asdict(decision),
        "project": "CovaPIE",
        "stage": STAGE,
        "base_commit": BASE_COMMIT,
        "formal_commit_subject": FORMAL_COMMIT_SUBJECT,
        "covalent_bond_atom_pair_current_semantics_audit_completed": True,
        "observed_current_scope": "current Cys-SG golden evidence",
        "observed_current_order": "residue atom name then ligand atom name",
        "observed_current_delimiter": "--",
        "observed_current_representation_is_future_contract": False,
        "current_source_of_truth": FINAL_DATASET_PATH,
        "lineage_selectors_executed": (
            lineage_evidence.lineage_selectors_executed
        ),
        "lineage_transition_projections_verified": (
            lineage_evidence.lineage_transition_projections_verified
        ),
        "original_producer_record_count": (
            lineage_evidence.original_producer_record_count
        ),
        "expansion_producer_record_count": (
            lineage_evidence.expansion_producer_record_count
        ),
        "producer_projection_record_count": len(
            lineage_evidence.producer_projections
        ),
        "producer_projection_verified": (
            derived_evidence.producer_projection_verified
        ),
        "producer_projection_mismatch_reasons": list(
            lineage_evidence.producer_validation.mismatch_reasons
        ),
        "original_sample_index_record_count": (
            lineage_evidence.original_sample_index_record_count
        ),
        "expansion_sample_index_record_count": (
            lineage_evidence.expansion_sample_index_record_count
        ),
        "unified_sample_index_record_count": (
            lineage_evidence.unified_sample_index_record_count
        ),
        "split_union_record_count": (
            lineage_evidence.split_union_record_count
        ),
        "split_partition_verified": (
            lineage_evidence.split_partition_verified
        ),
        "final_dataset_record_count": (
            lineage_evidence.final_dataset_record_count
        ),
        "source_lineage_row_count": len(lineage),
        "representation_row_count": len(representation),
        "consumer_row_count": len(consumers),
        "consumer_role_counts": dict(sorted(role_counts.items())),
        "unresolved_semantics_row_count": len(unresolved),
        "issue_inventory_data_row_count": len(issue_rows),
        "observed_record_count": len(representation),
        "observed_event_count": len(
            {row["sample_or_event_id"] for row in representation}
        ),
        "observed_unique_pair_value_count": len(set(pairs)),
        "observed_pair_values": sorted(set(pairs)),
        "observed_null_pair_count": sum(not pair for pair in pairs),
        "observed_duplicate_pair_record_count": sum(
            count - 1 for count in pair_counts.values() if count > 1
        ),
        "observed_conflicting_pair_count": len(
            derived_evidence.record_conflict_event_ids
        ),
        "observed_conflicting_event_ids": list(
            derived_evidence.record_conflict_event_ids
        ),
        "observed_pair_cardinality_by_event": {
            row["sample_or_event_id"]: 1 for row in representation
        },
        "record_conflict_present": (
            derived_evidence.record_conflict_present
        ),
        "producer_conflict_present": (
            derived_evidence.producer_conflict_present
        ),
        "producer_conflict_event_ids": list(
            lineage_evidence.producer_validation.producer_conflict_event_ids
        ),
        "future_ordering_semantics_defined": False,
        "future_index_mapping_defined": False,
        "future_tensor_shape_defined": False,
        "future_loss_mask_semantics_defined": False,
        "provider_issue_resolved": False,
        "issue_status_changed": False,
        "resolved_issue_count": 0,
        "new_issue_count": 0,
        "deleted_issue_count": 0,
        "provider_used": False,
        "download_used": False,
        "raw_read": False,
        "raw_write": False,
        "checkpoint_access": False,
        "model_changed": False,
        "dataloader_changed": False,
        "forward_changed": False,
        "loss_changed": False,
        "backward_used": False,
        "optimizer_used": False,
        "parameter_update_used": False,
        "training_used": False,
        "feature_semantics_audit_required_before_training": True,
        "feature_semantics_known": False,
        "unknown_atom_feature_policy_resolved": False,
        "unknown_atom_feature_policy": "UNKNOWN_ATOM_FEATURE_POLICY",
        "step12d_warning": (
            "Step12D was a smoke legality check, not a final "
            "training-feature contract"
        ),
        "canonical_masks": [
            {"semantic_name": name, "alias": alias}
            for name, alias in CANONICAL_MASKS
        ],
        "exact10_files": [path.as_posix() for path in EXACT10],
        "issue_inventory_source_sha256": PREDECESSOR_ISSUE_SHA256,
        "evidence_sha256": {
            name: hashlib.sha256(payload).hexdigest()
            for name, payload in csv_payloads.items()
        },
    }


def build_evidence_payloads() -> dict[str, bytes]:
    _negative_model_consumer_check()
    _verify_masks_and_training_gate()
    lineage_evidence = build_executable_lineage_evidence()
    lineage = lineage_evidence.lineage_rows
    representation = build_current_representation_rows()
    consumers = build_downstream_consumer_rows()
    unresolved = build_unresolved_semantics_rows()
    issue_payload, issue_rows = _issue_payload_and_rows()
    derived_evidence = derive_audit_evidence(
        lineage_evidence=lineage_evidence,
        representation=representation,
        consumers=consumers,
        unresolved=unresolved,
    )
    if (
        any(row["verified"] != "true" for row in lineage)
        or any(row["verified"] != "true" for row in representation)
        or any(row["verified"] != "true" for row in consumers)
        or any(row["verified"] != "true" for row in unresolved)
        or any(
            row["decision_made_current_audit"] != "false"
            or row["deferred_to_next_contract"] != "true"
            for row in unresolved
        )
    ):
        raise AssertionError("audit evidence failed closed")
    decisions = tuple(_audit_decision(derived_evidence) for _ in range(3))
    serialized = tuple(
        audit.serialize_covalent_bond_atom_pair_current_semantics_audit_decision(
            item
        )
        for item in decisions
    )
    if not (
        decisions[0] == decisions[1] == decisions[2]
        and serialized[0] == serialized[1] == serialized[2]
        and decisions[0].outcome == "audited"
    ):
        raise AssertionError("audit decision is not deterministic and audited")
    csv_payloads = {
        LINEAGE_NAME: _csv_bytes(LINEAGE_COLUMNS, lineage),
        REPRESENTATION_NAME: _csv_bytes(
            REPRESENTATION_COLUMNS, representation
        ),
        CONSUMER_NAME: _csv_bytes(CONSUMER_COLUMNS, consumers),
        UNRESOLVED_NAME: _csv_bytes(UNRESOLVED_COLUMNS, unresolved),
        ISSUE_NAME: issue_payload,
    }
    manifest = _manifest(
        csv_payloads,
        lineage_evidence,
        derived_evidence,
        decisions[0],
        representation,
        consumers,
        unresolved,
        issue_rows,
    )
    return {
        **csv_payloads,
        MANIFEST_NAME: (
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8"),
    }


def verify_payloads(payloads: Mapping[str, bytes]) -> dict[str, object]:
    if tuple(payloads) != OUTPUT_NAMES:
        raise AssertionError("payload set is not Exact6")
    for name in OUTPUT_NAMES:
        path = ROOT / OUTPUT_ROOT / name
        if (
            not path.is_file()
            or path.is_symlink()
            or path.read_bytes() != payloads[name]
        ):
            raise AssertionError(f"materialized evidence mismatch: {name}")
    manifest = json.loads(payloads[MANIFEST_NAME])
    required_true = (
        "covalent_bond_atom_pair_current_semantics_audit_completed",
        "lineage_selectors_executed",
        "lineage_transition_projections_verified",
        "producer_projection_verified",
        "split_partition_verified",
        "current_source_lineage_verified",
        "current_representation_inventory_complete",
        "current_consumer_inventory_complete",
        "current_semantics_internally_consistent",
        "explicit_bond_authority_verified",
        "current_pair_is_metadata_string",
        "unresolved_semantics_inventory_complete",
        "ready_for_encoding_contract_design",
        "feature_semantics_audit_required_before_training",
    )
    required_false = (
        "distance_only_inference_used",
        "current_pair_is_tensor_index_pair",
        "current_dataloader_consumer_present",
        "current_model_forward_consumer_present",
        "current_loss_consumer_present",
        "current_training_target_tensor_present",
        "record_conflict_present",
        "producer_conflict_present",
        "atom_pair_issue_resolved",
        "provider_issue_resolved",
        "issue_status_changed",
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
    if any(manifest.get(item) is not True for item in required_true):
        raise AssertionError("required true manifest field failed")
    if any(manifest.get(item) is not False for item in required_false):
        raise AssertionError("required false manifest field failed")
    if (
        manifest.get("outcome") != "audited"
        or manifest.get("observed_record_count") != 11
        or manifest.get("observed_event_count") != 11
        or manifest.get("observed_unique_pair_value_count") != 7
        or manifest.get("observed_null_pair_count") != 0
        or manifest.get("observed_conflicting_pair_count") != 0
        or manifest.get("original_producer_record_count") != 3
        or manifest.get("expansion_producer_record_count") != 8
        or manifest.get("producer_projection_record_count") != 11
        or manifest.get("original_sample_index_record_count") != 3
        or manifest.get("expansion_sample_index_record_count") != 8
        or manifest.get("unified_sample_index_record_count") != 11
        or manifest.get("split_union_record_count") != 11
        or manifest.get("final_dataset_record_count") != 11
        or manifest.get("issue_inventory_source_sha256")
        != PREDECESSOR_ISSUE_SHA256
        or manifest.get("recommended_next_step")
        != audit.RECOMMENDED_NEXT_STEP
    ):
        raise AssertionError("manifest audit statistics or continuity mismatch")
    expected_hashes = manifest["evidence_sha256"]
    if not isinstance(expected_hashes, Mapping):
        raise AssertionError("evidence hashes are not a mapping")
    for name in OUTPUT_NAMES[:-1]:
        if expected_hashes.get(name) != hashlib.sha256(payloads[name]).hexdigest():
            raise AssertionError(f"output SHA mismatch: {name}")
    return manifest


def main() -> int:
    payloads = build_evidence_payloads()
    if payloads != build_evidence_payloads() or payloads != build_evidence_payloads():
        raise AssertionError("three complete evidence builds differ")
    (ROOT / OUTPUT_ROOT).mkdir(parents=True, exist_ok=True)
    for name, payload in payloads.items():
        (ROOT / OUTPUT_ROOT / name).write_bytes(payload)
    manifest = verify_payloads(payloads)
    lines = (
        "audit_completed=true",
        "lineage_selectors_executed=true",
        "lineage_transition_projections_verified=true",
        "original_producer_record_count=3",
        "expansion_producer_record_count=8",
        "producer_projection_record_count=11",
        "producer_projection_verified=true",
        "original_sample_index_record_count=3",
        "expansion_sample_index_record_count=8",
        "unified_sample_index_record_count=11",
        "split_union_record_count=11",
        "final_dataset_record_count=11",
        "record_conflict_present=false",
        "producer_conflict_present=false",
        "current_source_lineage_verified=true",
        "current_representation_inventory_complete=true",
        "current_consumer_inventory_complete=true",
        "current_semantics_internally_consistent=true",
        "explicit_bond_authority_verified=true",
        "distance_only_inference_used=false",
        "current_pair_is_metadata_string=true",
        "current_pair_is_tensor_index_pair=false",
        "current_dataloader_consumer_present=false",
        "current_model_forward_consumer_present=false",
        "current_loss_consumer_present=false",
        "current_training_target_tensor_present=false",
        "unresolved_semantics_inventory_complete=true",
        "atom_pair_issue_resolved=false",
        "provider_issue_resolved=false",
        "ready_for_encoding_contract_design=true",
        "feature_semantics_audit_completed=false",
        "ready_for_training=false",
        f"source_lineage_rows={manifest['source_lineage_row_count']}",
        f"representation_rows={manifest['representation_row_count']}",
        f"consumer_rows={manifest['consumer_row_count']}",
        f"unresolved_semantics_rows={manifest['unresolved_semantics_row_count']}",
        f"issue_rows={manifest['issue_inventory_data_row_count']}",
        f"observed_record_count={manifest['observed_record_count']}",
        f"observed_event_count={manifest['observed_event_count']}",
        (
            "observed_unique_pair_value_count="
            f"{manifest['observed_unique_pair_value_count']}"
        ),
        (
            "observed_conflicting_pair_count="
            f"{manifest['observed_conflicting_pair_count']}"
        ),
    )
    sys.stdout.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
