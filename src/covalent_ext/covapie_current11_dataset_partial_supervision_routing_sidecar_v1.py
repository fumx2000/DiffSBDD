"""Build the read-only Current11 dataset partial-supervision routing sidecar."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import stat
import subprocess
from collections import Counter
from pathlib import Path
from typing import Mapping, Sequence

from covalent_ext.covapie_current11_unit_000001_partial_supervision_routing_gate_v1 import (
    evaluate_covapie_current11_unit_000001_partial_supervision_routing_gate_v1,
)


__all__ = (
    "build_covapie_current11_dataset_partial_supervision_routing_sidecar_v1",
)

SCHEMA_VERSION = "covapie_current11_dataset_partial_supervision_routing_sidecar_v1"
ERROR_TOKEN = "COVAPIE_CURRENT11_DATASET_PARTIAL_SUPERVISION_ROUTING_SIDECAR_V1_ERROR"
BASE_COMMIT = "05a86e7f293d75a2e890850208ee49b9d1c821f6"
FORMAL_COMMIT_SUBJECT = "add CovaPIE Current11 dataset partial supervision routing sidecar v1"
BRANCH = "main"
_PATH_TYPE = type(Path())

MODULE_PATH = (
    "src/covalent_ext/"
    "covapie_current11_dataset_partial_supervision_routing_sidecar_v1.py"
)
SCRIPT_PATH = (
    "scripts/check_covapie_current11_dataset_partial_supervision_routing_sidecar_v1.py"
)
TEST_PATH = (
    "tests/test_covapie_current11_dataset_partial_supervision_routing_sidecar_v1.py"
)
GUIDE_PATH = (
    "docs/covapie_current11_dataset_partial_supervision_routing_sidecar_v1_guide.md"
)
CANDIDATE_PATHS = tuple(sorted((MODULE_PATH, SCRIPT_PATH, TEST_PATH, GUIDE_PATH)))

ARTIFACT_NAMES = (
    "current11_dataset_partial_supervision_routing_records.csv",
    "current11_dataset_partial_supervision_task_coverage.csv",
    "current11_dataset_partial_supervision_sample_coverage.csv",
    "current11_dataset_partial_supervision_routing_manifest.json",
)

EXPECTED_SAMPLES = (
    ("CYS_SG_SAMPLE_INDEX_000001", "6BV6", "JUG"),
    ("CYS_SG_SAMPLE_INDEX_000002", "6BV8", "JUG"),
    ("CYS_SG_SAMPLE_INDEX_000003", "6BV5", "JUG"),
    ("CYS_SG_SAMPLE_INDEX_000004", "1AEC", "E64"),
    ("CYS_SG_SAMPLE_INDEX_000005", "1AIM", "ZYA"),
    ("CYS_SG_SAMPLE_INDEX_000006", "1AU3", "PCM"),
    ("CYS_SG_SAMPLE_INDEX_000007", "1AU4", "INP"),
    ("CYS_SG_SAMPLE_INDEX_000008", "1AYU", "INA"),
    ("CYS_SG_SAMPLE_INDEX_000009", "1AYV", "IN6"),
    ("CYS_SG_SAMPLE_INDEX_000010", "1AYW", "IN3"),
    ("CYS_SG_SAMPLE_INDEX_000011", "1B02", "UFP"),
)
UNIT_SAMPLE_IDS = frozenset((EXPECTED_SAMPLES[7][0], EXPECTED_SAMPLES[9][0]))
UNIT_STATE_PROJECTION_SHA256 = (
    "fd016edf634c73aea4b0976ffce966cd1fecc1c37fe9dd8507c7708a075f65ac"
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
BLOCKING_REASON_VOCABULARY = (
    "NONE",
    "OBSERVED_COMPLEX_GEOMETRY_ONLY",
    "AUTHORITATIVE_LINK_BOND_ORDER_MISSING",
    "CANDIDATE_LABEL_NOT_APPROVED",
    "PRIMARY_ROLE_AUTHORITY_INCOMPLETE",
    "PRE_COVALENT_GEOMETRY_MISSING",
    "DEDICATED_TRANSFORMATION_REVIEW_MISSING",
    "POST_STATE_AMBIGUOUS",
    "REACTION_ATOM_MAP_MISSING",
    "CANDIDATE_TRANSFORMATION_SEMANTICS_ONLY",
    "BOND_ORDER_DELTA_MISSING",
    "FORMAL_CHARGE_DELTA_MISSING",
    "PROTONATION_TRANSFER_MISSING",
    "SAMPLE_SPECIFIC_REVERSIBILITY_MISSING",
    "FULL_TRANSFORMATION_INCOMPLETE",
)
EVIDENCE_SCOPE_VOCABULARY = (
    "CANONICAL_SAMPLE_IDENTITY",
    "EXPLICIT_BINARY_COVALENT_EVENT",
    "EXPLICIT_LIGAND_RESIDUE_ATOM_PAIR",
    "AUTHORITATIVE_LINK_BOND_ORDER_ABSENT",
    "CANDIDATE_FAMILY_OR_WARHEAD_TYPE",
    "REVIEWED_WARHEAD_BOUNDARY_ONLY",
    "CANONICAL_MASK_CONTRACT_WITHOUT_PRIMARY_ROLES",
    "OBSERVED_COMPLEX_COORDINATE_DISTANCE",
    "PRE_COVALENT_GEOMETRY_ABSENT",
    "POST_COVALENT_STATE_UNRESOLVED",
    "COMPLETE_POST_STATE_GRAPH_UNRESOLVED",
    "REACTION_ATOM_MAP_ABSENT",
    "CANDIDATE_FORMED_EDGE",
    "CANDIDATE_OR_AMBIGUOUS_BROKEN_EDGE",
    "BOND_ORDER_DELTA_ABSENT",
    "FORMAL_CHARGE_DELTA_ABSENT",
    "PROTONATION_TRANSFER_ABSENT",
    "CANDIDATE_LEAVING_GROUP",
    "SAMPLE_REVERSIBILITY_UNRESOLVED",
    "FULL_TRANSFORMATION_UNRESOLVED",
)

EXPECTED_GLOBAL_COUNTS = {
    "admissible_now": 44,
    "admissible_as_observed_geometry_only": 11,
    "candidate_only_not_authoritative": 55,
    "blocked_missing_evidence": 103,
    "blocked_state_ambiguity": 7,
    "blocked_missing_human_approval": 55,
    "not_applicable": 0,
}

REPO_SOURCES = {
    "canonical_final_index": (
        "data/derived/covalent_small/covapie_final_dataset_materialization_smoke_v0/"
        "final_dataset_index.csv",
        "c4c31888cb0f7c148b00656ccf22ab68fab842fcdafdee049b2f420eddc1302d",
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
    "candidate_family_assignments": (
        "data/derived/covalent_small/"
        "covapie_current11_cys_sg_reaction_family_and_warhead_rule_assignments_v1/"
        "covapie_current11_cys_sg_candidate_assignment_authority.csv",
        "bc49e2f1ca112ceae30c91fa492386f6012c9005fc5137b40d3daec2343ef5d9",
    ),
    "family_rule_authority_binding": (
        "data/derived/covalent_small/"
        "covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1/"
        "covapie_current11_family_rule_authority_binding_matrix.csv",
        "7064c1d0153ba1399bfdae8affcf21ead3f27e8a933987cd025ba5101a92bb61",
    ),
    "role_input_authority": (
        "data/derived/covalent_small/covapie_role_annotation_input_authority_gap_resolution_v1/"
        "covapie_current11_role_input_authority_matrix.csv",
        "fc7897121bf216488c239ecd2ad678bc23501f72db1fea85212b083c5af7b06b",
    ),
    "canonical_mask_truth_table": (
        "data/derived/covalent_small/"
        "covapie_canonical_five_level_role_and_task_mask_materialization_contract_v1/"
        "covapie_canonical_task_truth_table.csv",
        "586d483f67b9108af1af820b892b477329a1b6de24b0ad0b9ee46cebbaba20e5",
    ),
    "unit_000001_gate_module": (
        "src/covalent_ext/covapie_current11_unit_000001_partial_supervision_routing_gate_v1.py",
        "30750f6996f4c203690261df33995b0cf3baaf2c7c8684999faea325f2171759",
    ),
}

_SAMPLE_ARTIFACT_HASHES = (
    ("443126984185d9e180df9096a1d4251c85b0b67cf8903ebad8a09723be739855", "ad6c1b97e6f67e8cfddf934f66e780e67dc5e5764eb78a73ced578909944476f"),
    ("c145b864c1c2d0d2f6f7e0e2e3797fca25d304180553518720dda0d503a3f497", "4a7f61620b86ba832729744d45045141f7c7b0504f9d79b8acc4652fef429c4d"),
    ("3f27937fbca0c54142e7bdfa204f1527b084b9185a4e1afb4078cd6dc0924f9d", "482ab27961fd57d0a91ebeccc88d1f926fb1991f5ca029f3a7e0183b3422e3fb"),
    ("d447fdaa30c7e805c7fc1644e5dde410403881905bef72c6601b1aa24d50be90", "231604eadff0c6247b32b8f64d7151cc5423245da57705db0cd9a31624f0deb4"),
    ("9234209cc4a87d5764e3a0e8964d93838f7a0f4ffd394d3930643807d7ccb8de", "3f8efd3a81ba6bd57bcdeaa9dd1b482ae41c52b6b270193da9c044a51ae9e5fb"),
    ("1d9a50c6737d97c5f6a0e9b1750526981a47283b7a10c5b8a89681c4424dbe82", "798eba5ec3dcfc79642a334647dda6a86e9956ae78e1cfcac59988baf1dfd54e"),
    ("92fd91f65cb80f83cc05b6511ff5d8ca7c67988e0150df3445d1fff780a319cb", "fea7bffe928500854fa367326098cc6564ae6fe6124275b1dc6b5638009056fb"),
    ("e02fd270854f92bc25e037c9a233e6c3de43cf8fdabd13e0a32f816d493b12a9", "bf68477bccf748c347f4198f71fa95a65899f684a510b73d17ae9e566917bc5e"),
    ("9a45d2dd5d7e127dc05ef6281034f524c6a9112f8c3c898258d07d5c64dc1756", "5fb89da106edb0b89345267b70b0f92343ab4a5c32214579e17333950314516c"),
    ("232b86af84dcade653b54d39f435763ddb21196c9f893973e60d4afdebe1f263", "58148a7ea77024eee27f871d618d4e257d3649bfd6a420b2ea6d4050dbcffe8f"),
    ("02667ad8fef7202de78d998a0f1b55c9626ed37736f31190f2021563398b8142", "ec82aa4b3cd6ad253aad2b7f17b227cb2e7787b42d30af6b0c6d589832885c2a"),
)
_SAMPLE_ARTIFACT_ROOTS = (
    "covapie_sample_preparation_execution_smoke_v0/samples/6BV6_JUG",
    "covapie_sample_preparation_execution_smoke_v0/samples/6BV8_JUG",
    "covapie_sample_preparation_execution_smoke_v0/samples/6BV5_JUG",
    "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/samples/1AEC_E64",
    "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/samples/1AIM_ZYA",
    "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/samples/1AU3_PCM",
    "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/samples/1AU4_INP",
    "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/samples/1AYU_INA",
    "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/samples/1AYV_IN6",
    "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/samples/1AYW_IN3",
    "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/samples/1B02_UFP",
)
for _sample, _artifact_root, _hashes in zip(
    EXPECTED_SAMPLES, _SAMPLE_ARTIFACT_ROOTS, _SAMPLE_ARTIFACT_HASHES, strict=True
):
    _sample_id = _sample[0]
    _prefix = f"data/derived/covalent_small/{_artifact_root}"
    REPO_SOURCES[f"event_table_{_sample_id}"] = (
        f"{_prefix}/covalent_event_table.csv", _hashes[0]
    )
    REPO_SOURCES[f"observed_pair_table_{_sample_id}"] = (
        f"{_prefix}/ligand_residue_atom_pair_table.csv", _hashes[1]
    )

STATE_SOURCES = {
    "coverage_audit_lineage": (
        "review-scratch/current11-dataset-partial-supervision-coverage-v1/"
        "current11_dataset_partial_supervision_coverage_audit_report.md",
        "abeaae7e072c7434957a7c6d869a3f20a780df127bdcfb686f2e8661b0ade54a",
    ),
    "unified_boundary_authority": (
        "manual-review/covapie_current11_unified_effective_authority_view_v1.json",
        "f4178987f3c3eed0e248f6d3d5f22cb8bce1839d39ab08aff0bff9d2ef9f3774",
    ),
    "formal_family_rule_worklist": (
        "manual-review/current11-family-rule-approval-v1/family_rule_approval_worklist.csv",
        "9a85c03384a09620a1c168b023d3a1de2ebb1fed57589e55449ec1672d6c3add",
    ),
    "formal_transformation_worklist": (
        "manual-review/current11-reaction-transformation-review-v1/"
        "transformation_evidence_worklist.csv",
        "c7063e8070de3ecd1fdf4dfc19ffd91ef09dbeac48d80fbc6f01c9369d647423",
    ),
}

RECORD_FIELDS = (
    "sample_index_row_id", "pdb_id", "ligand_comp_id", "semantic_task_name",
    "eligibility_state", "direct_authority_found", "evidence_scope",
    "blocking_reason_code", "supporting_source_ids_json",
    "dedicated_transformation_review_available", "availability_mask_required",
    "current_runtime_consumer_available", "training_loss_authorized",
)
TASK_COVERAGE_FIELDS = (
    "semantic_task_name", "admissible_now_sample_count",
    "observed_geometry_only_sample_count", "candidate_only_sample_count",
    "blocked_missing_evidence_sample_count", "blocked_state_ambiguity_sample_count",
    "blocked_missing_human_approval_sample_count", "not_applicable_sample_count",
    "total_sample_count", "current_runtime_consumer_available", "training_loss_authorized",
)
SAMPLE_COVERAGE_FIELDS = (
    "sample_index_row_id", "pdb_id", "ligand_comp_id", "admissible_now_task_count",
    "observed_geometry_only_task_count", "candidate_only_task_count",
    "blocked_missing_evidence_task_count", "blocked_state_ambiguity_task_count",
    "blocked_missing_human_approval_task_count", "not_applicable_task_count",
    "total_task_count", "dedicated_transformation_review_available",
    "dataset_level_routing_derivable", "current_runtime_consumer_available",
    "training_loss_authorized", "ready_for_tensor_materialization", "ready_for_training",
)
MANIFEST_FIELDS = frozenset((
    "schema_version", "base_commit", "sample_count", "semantic_task_count",
    "routing_record_count", "canonical_sample_identity", "semantic_task_names",
    "eligibility_state_vocabulary", "blocking_reason_vocabulary",
    "evidence_scope_vocabulary", "canonical_mask_semantics", "source_bindings",
    "unit_000001_parity", "global_state_counts", "task_coverage_summary",
    "sample_coverage_summary", "dedicated_transformation_review_samples",
    "samples_missing_dedicated_transformation_review",
    "sidecar_files_excluding_manifest", "readiness", "repository_lifecycle",
))


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
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
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


def _select_exact(rows: Sequence[Mapping[str, object]], **criteria: object) -> dict[str, object]:
    selected = [row for row in rows if all(row.get(key) == value for key, value in criteria.items())]
    if len(selected) != 1:
        _fail()
    return dict(selected[0])


def _validate_samples(payload: bytes) -> tuple[list[dict[str, str]], dict[str, tuple[str, str]]]:
    _fields, rows = _csv_rows(payload)
    identity = tuple((row.get("sample_index_row_id"), row.get("pdb_id"), row.get("ligand_comp_id")) for row in rows)
    if identity != EXPECTED_SAMPLES or len({item[0] for item in identity}) != 11 or len(set(identity)) != 11:
        _fail()
    artifact_paths: dict[str, tuple[str, str]] = {}
    for row, hashes in zip(rows, _SAMPLE_ARTIFACT_HASHES, strict=True):
        if (
            row.get("expected_het_id") != row.get("ligand_comp_id")
            or row.get("covalent_event_count") != "1"
            or row.get("ligand_residue_atom_pair_count") != "1"
            or row.get("covalent_residue_name") != "CYS"
            or row.get("covalent_residue_atom_name") != "SG"
            or row.get("conn_id") != "covale1"
            or row.get("conn_type_id") != "covale"
        ):
            _fail()
        event_path = row.get("covalent_event_table_path", "")
        pair_path = row.get("ligand_residue_atom_pair_table_path", "")
        if not event_path or not pair_path or event_path.startswith("/") or pair_path.startswith("/"):
            _fail()
        artifact_paths[row["sample_index_row_id"]] = (event_path, pair_path)
        if (
            REPO_SOURCES[f"event_table_{row['sample_index_row_id']}"] != (event_path, hashes[0])
            or REPO_SOURCES[f"observed_pair_table_{row['sample_index_row_id']}"]
            != (pair_path, hashes[1])
        ):
            _fail()
    return rows, artifact_paths


def _validate_pair_sources(
    samples: Sequence[Mapping[str, str]], payloads: Mapping[str, bytes]
) -> dict[str, str]:
    _fields, pairs = _csv_rows(payloads["canonical_pair_matrix"])
    _mapping_fields, mappings = _csv_rows(payloads["atom_table_mapping_matrix"])
    distances: dict[str, str] = {}
    if len(pairs) != 11 or len(mappings) != 22:
        _fail()
    for sample in samples:
        sample_id = sample["sample_index_row_id"]
        pair = _select_exact(pairs, sample_index_row_id=sample_id)
        if (
            pair.get("pdb_id") != sample["pdb_id"]
            or pair.get("ligand_comp_id") != sample["ligand_comp_id"]
            or pair.get("event_id") != sample["sample_preparation_input_id"]
            or pair.get("residue_comp_id") != "CYS"
            or pair.get("residue_atom_name") != "SG"
            or pair.get("ligand_atom_name") != sample["ligand_covalent_atom_name"]
            or pair.get("explicit_bond_authority_class") != "validated_struct_conn"
            or pair.get("canonical_record_valid") != "true"
            or pair.get("explicit_authority_preserved") != "true"
            or pair.get("verified") != "true"
        ):
            _fail()
        selected = [row for row in mappings if row.get("sample_index_row_id") == sample_id]
        if len(selected) != 2 or {row.get("entity_role") for row in selected} != {
            "target_residue_atom", "ligand_atom"
        }:
            _fail()
        for mapping in selected:
            if (
                mapping.get("pdb_id") != sample["pdb_id"]
                or mapping.get("candidate_match_count") != "1"
                or mapping.get("expected_match_count") != "1"
                or mapping.get("mapping_outcome") != "mapped"
                or mapping.get("mapping_reason") != "exact_one_identity_mapping"
                or mapping.get("distance_used_for_mapping_selection") != "false"
                or mapping.get("atom_site_id_matches") != "true"
                or mapping.get("verified") != "true"
            ):
                _fail()
        _event_fields, events = _csv_rows(payloads[f"event_table_{sample_id}"])
        _pair_fields, observed_rows = _csv_rows(payloads[f"observed_pair_table_{sample_id}"])
        event = _select_exact(events, sample_preparation_input_id=sample["sample_preparation_input_id"])
        observed = _select_exact(observed_rows, sample_preparation_input_id=sample["sample_preparation_input_id"])
        try:
            distance = float(observed.get("bond_distance_angstrom", ""))
        except ValueError:
            _fail()
        if (
            not math.isfinite(distance)
            or distance <= 0
            or observed.get("pdb_id") != sample["pdb_id"]
            or observed.get("expected_het_id") != sample["ligand_comp_id"]
            or observed.get("residue_atom_name") != "SG"
            or observed.get("ligand_atom_name") != sample["ligand_covalent_atom_name"]
            or observed.get("validation_status") not in {
                "validated_from_raw_struct_conn_and_atom_site",
                "validated_from_step14al_struct_conn_and_raw_atom_site",
            }
            or event.get("pdb_id") != sample["pdb_id"]
            or event.get("expected_het_id") != sample["ligand_comp_id"]
            or event.get("conn_id") != "covale1"
            or event.get("conn_type_id") != "covale"
            or event.get("residue_atom_name") != "SG"
            or event.get("ligand_atom_name") != sample["ligand_covalent_atom_name"]
            or event.get("event_source") not in {
                "raw_struct_conn", "raw_struct_conn_step14al_crosschecked"
            }
            or event.get("event_status") != "validated"
            or distance != float(sample["bond_distance_angstrom"])
        ):
            _fail()
        distances[sample_id] = observed["bond_distance_angstrom"]
    return distances


def _validate_boundary(samples: Sequence[Mapping[str, str]], payload: bytes) -> None:
    view = _json(payload, dict)
    if (
        view.get("unified_effective_authority_view_version")
        != "covapie_current11_unified_effective_authority_view_v1"
        or view.get("sample_order") != [row["sample_index_row_id"] for row in samples]
        or view.get("effective_authority_record_count") != 11
        or type(view.get("effective_authority_records")) is not list
    ):
        _fail()
    records = view["effective_authority_records"]
    for sample in samples:
        outer = _select_exact(records, sample_index_row_id=sample["sample_index_row_id"])
        record = outer.get("effective_authority_record")
        if type(record) is not dict:
            _fail()
        boundary_available = (
            record.get("exact_one_attachment_boundary_authority_available") is True
            or record.get("exact_two_attachment_boundaries_authority_available") is True
        )
        if (
            record.get("sample_index_row_id") != sample["sample_index_row_id"]
            or record.get("pdb_id") != sample["pdb_id"]
            or record.get("ligand_comp_id") != sample["ligand_comp_id"]
            or record.get("authority_status") != "active"
            or record.get("sample_quarantined") is not False
            or record.get("complete_warhead_atom_set_authority_available") is not True
            or not boundary_available
            or not record.get("reviewed_warhead_atom_ids")
        ):
            _fail()


def _validate_candidates_and_roles(
    samples: Sequence[Mapping[str, str]], payloads: Mapping[str, bytes]
) -> dict[str, dict[str, object]]:
    _fields, candidates = _csv_rows(payloads["candidate_family_assignments"])
    _binding_fields, bindings = _csv_rows(payloads["family_rule_authority_binding"])
    _role_fields, roles = _csv_rows(payloads["role_input_authority"])
    if len(candidates) != 11 or len(bindings) != 11 or len(roles) != 11:
        _fail()
    report: dict[str, dict[str, object]] = {}
    for sample in samples:
        sample_id = sample["sample_index_row_id"]
        candidate = _select_exact(candidates, sample_index_row_id=sample_id)
        binding = _select_exact(bindings, sample_index_row_id=sample_id)
        role = _select_exact(roles, sample_index_row_id=sample_id)
        family = candidate.get("candidate_reaction_family_id", "")
        rule = candidate.get("candidate_warhead_rule_id", "")
        if (
            candidate.get("pdb_id") != sample["pdb_id"]
            or candidate.get("ligand_comp_id") != sample["ligand_comp_id"]
            or not family or not rule
            or candidate.get("candidate_rule_assignment_exact_one") != "true"
            or candidate.get("candidate_family_assignment_exact_one") != "true"
            or candidate.get("candidate_warhead_type_semantic_name", "") == ""
            or candidate.get("review_status") != "not_reviewed"
            or candidate.get("training_label_status") != "not_approved_for_training"
            or candidate.get("training_label_approved") != "false"
            or candidate.get("verified") != "true"
            or binding.get("pdb_id") != sample["pdb_id"]
            or binding.get("ligand_identity") != sample["ligand_comp_id"]
            or binding.get("candidate_reaction_family_id") != family
            or binding.get("candidate_warhead_rule_id") != rule
            or binding.get("reaction_family_authority_status") != "candidate_only"
            or binding.get("warhead_rule_approval_status") != "candidate_only"
            or binding.get("reaction_family_identity_explicitly_attested") != "false"
            or binding.get("warhead_rule_identity_explicitly_attested") != "false"
            or binding.get("warhead_rule_full_semantics_explicitly_attested") != "false"
            or binding.get("verified") != "true"
            or role.get("pdb_id") != sample["pdb_id"]
            or role.get("ligand_identity") != sample["ligand_comp_id"]
            or role.get("reaction_family_status") != "candidate_only"
            or role.get("approved_warhead_rule_status") != "candidate_only"
            or role.get("role_seed_human_gold_review_completed") != "false"
            or role.get("role_proposal_input_authority_ready") != "false"
            or role.get("verified") != "true"
        ):
            _fail()
        report[sample_id] = {"family": family, "rule": rule}
    return report


def _validate_masks(payload: bytes) -> list[dict[str, str]]:
    _fields, rows = _csv_rows(payload)
    actual = tuple((row.get("semantic_name"), row.get("display_alias")) for row in rows)
    if actual != CANONICAL_MASK_SEMANTICS or any(row.get("verified") != "true" for row in rows):
        _fail()
    return [{"semantic_name": name, "display_alias": alias} for name, alias in actual]


def _validate_worklists(
    samples: Sequence[Mapping[str, str]], candidates: Mapping[str, Mapping[str, object]],
    family_payload: bytes, transformation_payload: bytes,
) -> dict[str, dict[str, object]]:
    _fields, family_rows = _csv_rows(family_payload)
    _trans_fields, transformation_rows = _csv_rows(transformation_payload)
    if len(family_rows) != 7 or len(transformation_rows) != 1:
        _fail()
    by_sample: dict[str, dict[str, object]] = {}
    seen: list[str] = []
    for row in family_rows:
        try:
            member_ids = json.loads(row.get("sample_index_row_ids", ""))
            leaving_group = json.loads(row.get("candidate_leaving_group_summary", ""))
        except (TypeError, ValueError):
            _fail()
        if (
            type(member_ids) is not list or not member_ids
            or type(leaving_group) is not dict
            or set(leaving_group) != {"allowed_elements", "required_count"}
            or type(leaving_group["allowed_elements"]) is not list
            or type(leaving_group["required_count"]) is not int
            or row.get("sample_count") != str(len(member_ids))
            or row.get("formed_bond_order") != "single"
            or row.get("candidate_reaction_delta_class") not in {
                "intact_parent_atom_inventory_match", "covalent_leaving_group_loss"
            }
            or row.get("current_binding_conclusion") != "family_and_rule_not_authoritative"
            or any(row.get(field) for field in (
                "reaction_family_review_decision", "warhead_rule_review_decision",
                "review_completed", "reaction_family_identity_explicitly_attested",
                "warhead_rule_identity_explicitly_attested",
                "warhead_rule_full_semantics_explicitly_attested",
            ))
        ):
            _fail()
        for sample_id in member_ids:
            if sample_id in seen or sample_id not in candidates:
                _fail()
            seen.append(sample_id)
            if (
                row.get("reaction_family_id") != candidates[sample_id]["family"]
                or row.get("warhead_rule_id") != candidates[sample_id]["rule"]
            ):
                _fail()
            by_sample[sample_id] = {
                "candidate_broken_edge_available": True,
                "candidate_leaving_group_available": True,
            }
    if set(seen) != {row["sample_index_row_id"] for row in samples}:
        _fail()
    transformation = transformation_rows[0]
    try:
        dedicated = json.loads(transformation.get("sample_index_row_ids_json", ""))
    except (TypeError, ValueError):
        _fail()
    if (
        dedicated != [EXPECTED_SAMPLES[7][0], EXPECTED_SAMPLES[9][0]]
        or transformation.get("sample_count") != "2"
        or transformation.get("post_reaction_authority_status") != "absent"
        or transformation.get("schema_gap_detected") != "true"
        or any(transformation.get(field) for field in (
            "reviewed_transformation_version", "reviewed_atom_map_contract_json",
            "reviewed_formed_edges_json", "reviewed_broken_edges_json",
            "reviewed_reversibility_semantics", "transformation_review_decision",
            "review_completed",
        ))
    ):
        _fail()
    for sample_id in by_sample:
        by_sample[sample_id]["dedicated_transformation_review_available"] = sample_id in dedicated
    return by_sample


_OTHER9_STATES = {
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
    "canonical_mask_scaffold_plus_linker_plus_warhead": "blocked_missing_human_approval",
    "observed_complex_geometry_supervision": "admissible_as_observed_geometry_only",
    "pre_covalent_geometry_supervision": "blocked_missing_evidence",
    "post_covalent_geometry_supervision": "blocked_missing_evidence",
    "complete_post_state_graph_supervision": "blocked_missing_evidence",
    "reaction_atom_map_supervision": "blocked_missing_evidence",
    "formed_edge_supervision": "candidate_only_not_authoritative",
    "broken_edge_supervision": "candidate_only_not_authoritative",
    "bond_order_delta_supervision": "blocked_missing_evidence",
    "formal_charge_delta_supervision": "blocked_missing_evidence",
    "protonation_transfer_supervision": "blocked_missing_evidence",
    "leaving_group_supervision": "candidate_only_not_authoritative",
    "reversibility_supervision": "blocked_missing_evidence",
    "full_transformation_supervision": "blocked_missing_evidence",
}

_TASK_METADATA = {
    "sample_identity_supervision": ("CANONICAL_SAMPLE_IDENTITY", "NONE"),
    "explicit_covalent_event_supervision": ("EXPLICIT_BINARY_COVALENT_EVENT", "NONE"),
    "ligand_residue_atom_pair_supervision": ("EXPLICIT_LIGAND_RESIDUE_ATOM_PAIR", "NONE"),
    "covalent_link_bond_order_supervision": ("AUTHORITATIVE_LINK_BOND_ORDER_ABSENT", "AUTHORITATIVE_LINK_BOND_ORDER_MISSING"),
    "warhead_type_supervision": ("CANDIDATE_FAMILY_OR_WARHEAD_TYPE", "CANDIDATE_LABEL_NOT_APPROVED"),
    "reaction_family_supervision": ("CANDIDATE_FAMILY_OR_WARHEAD_TYPE", "CANDIDATE_LABEL_NOT_APPROVED"),
    "warhead_boundary_supervision": ("REVIEWED_WARHEAD_BOUNDARY_ONLY", "NONE"),
    "canonical_mask_warhead_only": ("CANONICAL_MASK_CONTRACT_WITHOUT_PRIMARY_ROLES", "PRIMARY_ROLE_AUTHORITY_INCOMPLETE"),
    "canonical_mask_linker_plus_warhead": ("CANONICAL_MASK_CONTRACT_WITHOUT_PRIMARY_ROLES", "PRIMARY_ROLE_AUTHORITY_INCOMPLETE"),
    "canonical_mask_scaffold_plus_warhead": ("CANONICAL_MASK_CONTRACT_WITHOUT_PRIMARY_ROLES", "PRIMARY_ROLE_AUTHORITY_INCOMPLETE"),
    "canonical_mask_scaffold_only": ("CANONICAL_MASK_CONTRACT_WITHOUT_PRIMARY_ROLES", "PRIMARY_ROLE_AUTHORITY_INCOMPLETE"),
    "canonical_mask_scaffold_plus_linker_plus_warhead": ("CANONICAL_MASK_CONTRACT_WITHOUT_PRIMARY_ROLES", "PRIMARY_ROLE_AUTHORITY_INCOMPLETE"),
    "observed_complex_geometry_supervision": ("OBSERVED_COMPLEX_COORDINATE_DISTANCE", "OBSERVED_COMPLEX_GEOMETRY_ONLY"),
    "pre_covalent_geometry_supervision": ("PRE_COVALENT_GEOMETRY_ABSENT", "PRE_COVALENT_GEOMETRY_MISSING"),
    "post_covalent_geometry_supervision": ("POST_COVALENT_STATE_UNRESOLVED", "DEDICATED_TRANSFORMATION_REVIEW_MISSING"),
    "complete_post_state_graph_supervision": ("COMPLETE_POST_STATE_GRAPH_UNRESOLVED", "DEDICATED_TRANSFORMATION_REVIEW_MISSING"),
    "reaction_atom_map_supervision": ("REACTION_ATOM_MAP_ABSENT", "REACTION_ATOM_MAP_MISSING"),
    "formed_edge_supervision": ("CANDIDATE_FORMED_EDGE", "CANDIDATE_TRANSFORMATION_SEMANTICS_ONLY"),
    "broken_edge_supervision": ("CANDIDATE_OR_AMBIGUOUS_BROKEN_EDGE", "CANDIDATE_TRANSFORMATION_SEMANTICS_ONLY"),
    "bond_order_delta_supervision": ("BOND_ORDER_DELTA_ABSENT", "BOND_ORDER_DELTA_MISSING"),
    "formal_charge_delta_supervision": ("FORMAL_CHARGE_DELTA_ABSENT", "FORMAL_CHARGE_DELTA_MISSING"),
    "protonation_transfer_supervision": ("PROTONATION_TRANSFER_ABSENT", "PROTONATION_TRANSFER_MISSING"),
    "leaving_group_supervision": ("CANDIDATE_LEAVING_GROUP", "CANDIDATE_TRANSFORMATION_SEMANTICS_ONLY"),
    "reversibility_supervision": ("SAMPLE_REVERSIBILITY_UNRESOLVED", "SAMPLE_SPECIFIC_REVERSIBILITY_MISSING"),
    "full_transformation_supervision": ("FULL_TRANSFORMATION_UNRESOLVED", "FULL_TRANSFORMATION_INCOMPLETE"),
}


def _sources_for(task: str, sample_id: str) -> list[str]:
    if task == "sample_identity_supervision":
        return ["canonical_final_index"]
    if task == "explicit_covalent_event_supervision":
        return [f"event_table_{sample_id}", "canonical_pair_matrix", "atom_table_mapping_matrix"]
    if task == "ligand_residue_atom_pair_supervision":
        return ["canonical_pair_matrix", "atom_table_mapping_matrix"]
    if task == "covalent_link_bond_order_supervision":
        return [f"event_table_{sample_id}", "formal_family_rule_worklist"]
    if task in ("warhead_type_supervision", "reaction_family_supervision"):
        return ["candidate_family_assignments", "family_rule_authority_binding", "formal_family_rule_worklist"]
    if task == "warhead_boundary_supervision":
        return ["unified_boundary_authority"]
    if task.startswith("canonical_mask_"):
        return ["canonical_mask_truth_table", "role_input_authority", "unified_boundary_authority"]
    if task == "observed_complex_geometry_supervision":
        return [f"observed_pair_table_{sample_id}"]
    if task in ("formed_edge_supervision", "broken_edge_supervision", "leaving_group_supervision"):
        return ["formal_family_rule_worklist", "canonical_pair_matrix"]
    if task != "pre_covalent_geometry_supervision":
        return ["formal_transformation_worklist"]
    return []


def _unit_records(unit: Mapping[str, object]) -> dict[tuple[str, str], Mapping[str, object]]:
    if (
        unit.get("schema_version") != "covapie_current11_unit_000001_partial_supervision_routing_gate_v1"
        or unit.get("semantic_task_names") != list(SEMANTIC_TASK_NAMES)
        or unit.get("eligibility_state_vocabulary") != list(ELIGIBILITY_STATE_VOCABULARY)
        or unit.get("repository_lifecycle", {}).get("lifecycle_profile")
        != "partial_supervision_routing_gate_published_successor"
        or unit.get("repository_lifecycle", {}).get("formal_candidate_commit") != BASE_COMMIT
        or type(unit.get("routing_records")) is not list
        or len(unit["routing_records"]) != 50
    ):
        _fail()
    projection = [
        [
            record.get("sample_index_row_id"), record.get("semantic_task_name"),
            record.get("eligibility_state"),
        ]
        for record in unit["routing_records"]
        if type(record) is dict
    ]
    projection_bytes = json.dumps(
        projection, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")
    if _sha256(projection_bytes) != UNIT_STATE_PROJECTION_SHA256:
        _fail()
    records: dict[tuple[str, str], Mapping[str, object]] = {}
    for record in unit["routing_records"]:
        if type(record) is not dict:
            _fail()
        key = (record.get("sample_index_row_id"), record.get("semantic_task_name"))
        if key in records or key[0] not in UNIT_SAMPLE_IDS or key[1] not in SEMANTIC_TASK_NAMES:
            _fail()
        records[key] = record
    if len(records) != 50:
        _fail()
    return records


def _record_metadata(task: str, state: str, dedicated: bool) -> tuple[str, str]:
    scope, reason = _TASK_METADATA[task]
    if dedicated and state == "blocked_state_ambiguity":
        reason = "POST_STATE_AMBIGUOUS"
    if dedicated and task == "reversibility_supervision" and state == "candidate_only_not_authoritative":
        reason = "CANDIDATE_TRANSFORMATION_SEMANTICS_ONLY"
    return scope, reason


def _build_records(
    samples: Sequence[Mapping[str, str]], worklist: Mapping[str, Mapping[str, object]],
    unit_records: Mapping[tuple[str, str], Mapping[str, object]],
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for sample in samples:
        sample_id = sample["sample_index_row_id"]
        dedicated = worklist[sample_id]["dedicated_transformation_review_available"] is True
        for task in SEMANTIC_TASK_NAMES:
            if sample_id in UNIT_SAMPLE_IDS:
                state = unit_records[(sample_id, task)].get("eligibility_state")
            else:
                state = _OTHER9_STATES[task]
            if state not in ELIGIBILITY_STATE_VOCABULARY:
                _fail()
            if (
                task == "broken_edge_supervision"
                and not worklist[sample_id]["candidate_broken_edge_available"]
                and state == "candidate_only_not_authoritative"
            ) or (
                task == "leaving_group_supervision"
                and not worklist[sample_id]["candidate_leaving_group_available"]
                and state == "candidate_only_not_authoritative"
            ):
                _fail()
            scope, reason = _record_metadata(task, state, dedicated)
            source_ids = _sources_for(task, sample_id)
            if sample_id in UNIT_SAMPLE_IDS:
                source_ids = list(dict.fromkeys((
                    "published_unit_000001_gate", *source_ids,
                )))
            records.append({
                "sample_index_row_id": sample_id,
                "pdb_id": sample["pdb_id"],
                "ligand_comp_id": sample["ligand_comp_id"],
                "semantic_task_name": task,
                "eligibility_state": state,
                "direct_authority_found": state in {
                    "admissible_now", "admissible_as_observed_geometry_only"
                },
                "evidence_scope": scope,
                "blocking_reason_code": reason,
                "supporting_source_ids_json": json.dumps(
                    source_ids, separators=(",", ":"), ensure_ascii=True
                ),
                "dedicated_transformation_review_available": dedicated,
                "availability_mask_required": True,
                "current_runtime_consumer_available": False,
                "training_loss_authorized": False,
            })
    return records


def _coverage(records: Sequence[Mapping[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    task_rows: list[dict[str, object]] = []
    for task in SEMANTIC_TASK_NAMES:
        counts = Counter(row["eligibility_state"] for row in records if row["semantic_task_name"] == task)
        task_rows.append({
            "semantic_task_name": task,
            "admissible_now_sample_count": counts["admissible_now"],
            "observed_geometry_only_sample_count": counts["admissible_as_observed_geometry_only"],
            "candidate_only_sample_count": counts["candidate_only_not_authoritative"],
            "blocked_missing_evidence_sample_count": counts["blocked_missing_evidence"],
            "blocked_state_ambiguity_sample_count": counts["blocked_state_ambiguity"],
            "blocked_missing_human_approval_sample_count": counts["blocked_missing_human_approval"],
            "not_applicable_sample_count": counts["not_applicable"],
            "total_sample_count": 11,
            "current_runtime_consumer_available": False,
            "training_loss_authorized": False,
        })
    sample_rows: list[dict[str, object]] = []
    for sample_id, pdb_id, ligand in EXPECTED_SAMPLES:
        selected = [row for row in records if row["sample_index_row_id"] == sample_id]
        counts = Counter(row["eligibility_state"] for row in selected)
        sample_rows.append({
            "sample_index_row_id": sample_id, "pdb_id": pdb_id, "ligand_comp_id": ligand,
            "admissible_now_task_count": counts["admissible_now"],
            "observed_geometry_only_task_count": counts["admissible_as_observed_geometry_only"],
            "candidate_only_task_count": counts["candidate_only_not_authoritative"],
            "blocked_missing_evidence_task_count": counts["blocked_missing_evidence"],
            "blocked_state_ambiguity_task_count": counts["blocked_state_ambiguity"],
            "blocked_missing_human_approval_task_count": counts["blocked_missing_human_approval"],
            "not_applicable_task_count": counts["not_applicable"],
            "total_task_count": 25,
            "dedicated_transformation_review_available": sample_id in UNIT_SAMPLE_IDS,
            "dataset_level_routing_derivable": True,
            "current_runtime_consumer_available": False,
            "training_loss_authorized": False,
            "ready_for_tensor_materialization": False,
            "ready_for_training": False,
        })
    return task_rows, sample_rows


def _bool_text(value: object) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value)


def _csv_bytes(fields: Sequence[str], rows: Sequence[Mapping[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: _bool_text(row[field]) for field in fields})
    return stream.getvalue().encode("utf-8")


def _readiness() -> dict[str, bool]:
    return {
        "dataset_partial_supervision_routing_sidecar_implemented": True,
        "dataset_level_routing_derivable_for_all_current11": True,
        "unit_000001_parity_passed": True,
        "runtime_consumer_available": False,
        "training_loss_authorized": False,
        "tensor_materialized": False,
        "repository_schema_changed": False,
        "formal_state_modified": False,
        "formal_worklist_modified": False,
        "formal_dossier_modified": False,
        "authority_changed": False,
        "model_changed": False,
        "training_performed": False,
        "ready_for_sidecar_validation": True,
        "ready_for_formal_sidecar_materialization": False,
        "ready_for_tensor_materialization": False,
        "ready_for_dataloader_integration": False,
        "ready_for_model_integration": False,
        "feature_semantics_reaudit_required_before_training": True,
        "ready_for_training": False,
    }


def _run_git(repo_root: Path, args: Sequence[str]) -> str:
    try:
        result = subprocess.run(
            ("git", *args), cwd=repo_root, check=False, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if result.returncode != 0:
            _fail()
        return result.stdout.decode("utf-8")
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR_TOKEN:
            raise
        raise ValueError(ERROR_TOKEN) from error


def _is_hex(value: object) -> bool:
    return type(value) is str and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def _is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    result = subprocess.run(
        ("git", "merge-base", "--is-ancestor", ancestor, descendant), cwd=repo_root,
        check=False, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if result.returncode not in (0, 1):
        _fail()
    return result.returncode == 0


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
    ahead, behind = _run_git(repo_root, ("rev-list", "--left-right", "--count", "HEAD...refs/remotes/origin/main")).split()
    revisions = set(_run_git(repo_root, ("rev-list", f"{BASE_COMMIT}..{head}")).splitlines())
    revisions.update(_run_git(repo_root, ("rev-list", f"{BASE_COMMIT}..{origin}")).splitlines())
    path_commits: list[dict[str, object]] = []
    for commit in sorted(revisions):
        statuses: dict[str, str] = {}
        for line in _run_git(repo_root, ("diff-tree", "--root", "--no-commit-id", "--name-status", "-r", commit)).splitlines():
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
        path_commits.append({
            "commit": commit,
            "parents": _run_git(repo_root, ("show", "-s", "--format=%P", commit)).split(),
            "subject": _run_git(repo_root, ("show", "-s", "--format=%s", commit)).strip(),
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
        "live_paths": {path: _live_identity(repo_root, path) for path in CANDIDATE_PATHS},
    }


def _derive_lifecycle(facts: object) -> dict[str, object]:
    try:
        if (
            type(facts) is not dict or facts.get("branch") != BRANCH
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
                "lifecycle_profile": "dataset_partial_supervision_sidecar_precommit_candidate",
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
                "lifecycle_profile": "dataset_partial_supervision_sidecar_published_successor",
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
            "lifecycle_profile": "dataset_partial_supervision_sidecar_committed_unpushed",
            "origin_main": BASE_COMMIT, "ahead": 1, "behind": 0,
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR_TOKEN:
            raise
        raise ValueError(ERROR_TOKEN) from error


def _source_bindings(
    repo_payloads: Mapping[str, bytes], state_payloads: Mapping[str, bytes],
    unit: Mapping[str, object],
) -> dict[str, object]:
    bindings: dict[str, object] = {}
    for source_id, (relative, digest) in REPO_SOURCES.items():
        bindings[source_id] = {
            "root": "repo_root", "relative_path": relative, "sha256": digest,
            "bytes": len(repo_payloads[source_id]), "read_only": True,
        }
    for source_id, (relative, digest) in STATE_SOURCES.items():
        bindings[source_id] = {
            "root": "state_root", "relative_path": relative, "sha256": digest,
            "bytes": len(state_payloads[source_id]), "read_only": True,
        }
    bindings["published_unit_000001_gate"] = {
        "source_kind": "published_derived_gate",
        "public_api": "evaluate_covapie_current11_unit_000001_partial_supervision_routing_gate_v1",
        "schema_version": "covapie_current11_unit_000001_partial_supervision_routing_gate_v1",
        "module_source_id": "unit_000001_gate_module",
        "state_projection_sha256": UNIT_STATE_PROJECTION_SHA256,
        "formal_candidate_commit": unit["repository_lifecycle"]["formal_candidate_commit"],
        "lifecycle_profile": unit["repository_lifecycle"]["lifecycle_profile"],
        "read_only": True,
    }
    return bindings


def _artifact_identity(payload: bytes) -> dict[str, object]:
    return {"bytes": len(payload), "lines": payload.count(b"\n"), "sha256": _sha256(payload)}


def _validate_manifest_contract(
    manifest: Mapping[str, object], records: Sequence[Mapping[str, object]],
    task_rows: Sequence[Mapping[str, object]], sample_rows: Sequence[Mapping[str, object]],
) -> None:
    try:
        forbidden_record_fields = {
            "global_sample_eligible", "ready_for_training", "default_label",
            "inferred_bond_order",
        }
        source_bindings = manifest.get("source_bindings", {})
        source_ids = set(source_bindings)
        expected_unit_binding = {
            "source_kind": "published_derived_gate",
            "public_api": "evaluate_covapie_current11_unit_000001_partial_supervision_routing_gate_v1",
            "schema_version": "covapie_current11_unit_000001_partial_supervision_routing_gate_v1",
            "module_source_id": "unit_000001_gate_module",
            "state_projection_sha256": UNIT_STATE_PROJECTION_SHA256,
            "formal_candidate_commit": BASE_COMMIT,
            "lifecycle_profile": "partial_supervision_routing_gate_published_successor",
            "read_only": True,
        }
        readiness = manifest.get("readiness", {})
        required_true = {
            "dataset_partial_supervision_routing_sidecar_implemented",
            "dataset_level_routing_derivable_for_all_current11",
            "unit_000001_parity_passed", "ready_for_sidecar_validation",
            "feature_semantics_reaudit_required_before_training",
        }
        required_false = set(_readiness()) - required_true
        if (
            set(manifest) != MANIFEST_FIELDS
            or manifest.get("schema_version") != SCHEMA_VERSION
            or manifest.get("base_commit") != BASE_COMMIT
            or manifest.get("sample_count") != 11
            or manifest.get("semantic_task_count") != 25
            or manifest.get("routing_record_count") != 275
            or manifest.get("semantic_task_names") != list(SEMANTIC_TASK_NAMES)
            or manifest.get("eligibility_state_vocabulary") != list(ELIGIBILITY_STATE_VOCABULARY)
            or manifest.get("blocking_reason_vocabulary") != list(BLOCKING_REASON_VOCABULARY)
            or manifest.get("evidence_scope_vocabulary") != list(EVIDENCE_SCOPE_VOCABULARY)
            or manifest.get("global_state_counts") != EXPECTED_GLOBAL_COUNTS
            or manifest.get("task_coverage_summary") != list(task_rows)
            or manifest.get("sample_coverage_summary") != list(sample_rows)
            or manifest.get("readiness") != _readiness()
            or type(readiness) is not dict
            or any(readiness.get(key) is not True for key in required_true)
            or any(readiness.get(key) is not False for key in required_false)
            or set(manifest.get("sidecar_files_excluding_manifest", {}))
            != set(ARTIFACT_NAMES[:3])
            or ARTIFACT_NAMES[3] in manifest.get("sidecar_files_excluding_manifest", {})
            or not source_ids
            or source_bindings.get("published_unit_000001_gate") != expected_unit_binding
            or len(records) != 275
        ):
            _fail()
        for record in records:
            try:
                supporting = json.loads(str(record.get("supporting_source_ids_json")))
            except (TypeError, ValueError):
                _fail()
            if (
                tuple(record) != RECORD_FIELDS
                or forbidden_record_fields.intersection(record)
                or record.get("eligibility_state") not in ELIGIBILITY_STATE_VOCABULARY
                or record.get("evidence_scope") not in EVIDENCE_SCOPE_VOCABULARY
                or record.get("blocking_reason_code") not in BLOCKING_REASON_VOCABULARY
                or type(supporting) is not list
                or any(type(source_id) is not str for source_id in supporting)
                or len(supporting) != len(set(supporting))
                or any(Path(source_id).is_absolute() for source_id in supporting)
                or record.get("supporting_source_ids_json") != json.dumps(
                    supporting, separators=(",", ":"), ensure_ascii=True
                )
                or not set(supporting).issubset(source_ids)
                or supporting.count("published_unit_000001_gate")
                != (1 if record.get("sample_index_row_id") in UNIT_SAMPLE_IDS else 0)
                or record.get("availability_mask_required") is not True
                or record.get("current_runtime_consumer_available") is not False
                or record.get("training_loss_authorized") is not False
            ):
                _fail()
        if (
            any(tuple(row) != TASK_COVERAGE_FIELDS for row in task_rows)
            or any(tuple(row) != SAMPLE_COVERAGE_FIELDS for row in sample_rows)
            or any(
                row["current_runtime_consumer_available"] is not False
                or row["training_loss_authorized"] is not False
                for row in (*task_rows, *sample_rows)
            )
            or any(
                row["ready_for_tensor_materialization"] is not False
                or row["ready_for_training"] is not False
                for row in sample_rows
            )
        ):
            _fail()
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR_TOKEN:
            raise
        raise ValueError(ERROR_TOKEN) from error


def _validate_artifacts(artifacts: Mapping[str, bytes]) -> None:
    if tuple(artifacts) != ARTIFACT_NAMES or len(artifacts) != 4:
        _fail()
    for payload in artifacts.values():
        if (
            type(payload) is not bytes or not payload or len(payload) >= 1024 * 1024
            or payload.startswith(b"\xef\xbb\xbf") or b"\0" in payload
            or b"\r" in payload or not payload.endswith(b"\n")
            or payload.endswith(b"\n\n")
        ):
            _fail()
        payload.decode("utf-8")


def build_covapie_current11_dataset_partial_supervision_routing_sidecar_v1(
    *,
    repo_root: Path,
    state_root: Path,
) -> dict[str, bytes]:
    """Validate direct sources and return deterministic in-memory Exact4 bytes."""

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
        samples, _artifact_paths = _validate_samples(repo_payloads["canonical_final_index"])
        state_payloads = {
            source_id: _read_frozen(state, relative, digest)
            for source_id, (relative, digest) in STATE_SOURCES.items()
        }
        coverage = state_payloads["coverage_audit_lineage"]
        if len(coverage) != 164395 or coverage.count(b"\n") != 547:
            _fail()
        _validate_pair_sources(samples, repo_payloads)
        _validate_boundary(samples, state_payloads["unified_boundary_authority"])
        candidates = _validate_candidates_and_roles(samples, repo_payloads)
        masks = _validate_masks(repo_payloads["canonical_mask_truth_table"])
        worklist = _validate_worklists(
            samples, candidates, state_payloads["formal_family_rule_worklist"],
            state_payloads["formal_transformation_worklist"],
        )
        unit = evaluate_covapie_current11_unit_000001_partial_supervision_routing_gate_v1(
            repo_root=repository, state_root=state
        )
        unit_records = _unit_records(unit)
        records = _build_records(samples, worklist, unit_records)
        counts = Counter(record["eligibility_state"] for record in records)
        if len(records) != 275 or {state: counts[state] for state in ELIGIBILITY_STATE_VOCABULARY} != EXPECTED_GLOBAL_COUNTS:
            _fail()
        task_rows, sample_rows = _coverage(records)
        if any(sum(int(row[field]) for field in TASK_COVERAGE_FIELDS[1:8]) != 11 for row in task_rows):
            _fail()
        if any(sum(int(row[field]) for field in SAMPLE_COVERAGE_FIELDS[3:10]) != 25 for row in sample_rows):
            _fail()

        records_csv = _csv_bytes(RECORD_FIELDS, records)
        task_csv = _csv_bytes(TASK_COVERAGE_FIELDS, task_rows)
        sample_csv = _csv_bytes(SAMPLE_COVERAGE_FIELDS, sample_rows)
        csv_artifacts = {
            ARTIFACT_NAMES[0]: records_csv,
            ARTIFACT_NAMES[1]: task_csv,
            ARTIFACT_NAMES[2]: sample_csv,
        }
        lifecycle = _derive_lifecycle(_collect_lifecycle(repository))
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "base_commit": BASE_COMMIT,
            "sample_count": 11,
            "semantic_task_count": 25,
            "routing_record_count": 275,
            "canonical_sample_identity": [
                {"sample_index_row_id": sample_id, "pdb_id": pdb, "ligand_comp_id": ligand}
                for sample_id, pdb, ligand in EXPECTED_SAMPLES
            ],
            "semantic_task_names": list(SEMANTIC_TASK_NAMES),
            "eligibility_state_vocabulary": list(ELIGIBILITY_STATE_VOCABULARY),
            "blocking_reason_vocabulary": list(BLOCKING_REASON_VOCABULARY),
            "evidence_scope_vocabulary": list(EVIDENCE_SCOPE_VOCABULARY),
            "canonical_mask_semantics": masks,
            "source_bindings": _source_bindings(repo_payloads, state_payloads, unit),
            "unit_000001_parity": {
                "passed": True, "routing_record_count": 50,
                "state_counts": {
                    state_name: sum(
                        record["eligibility_state"] == state_name
                        for record in unit["routing_records"]
                    ) for state_name in ELIGIBILITY_STATE_VOCABULARY
                },
                "sample_index_row_ids": [EXPECTED_SAMPLES[7][0], EXPECTED_SAMPLES[9][0]],
            },
            "global_state_counts": EXPECTED_GLOBAL_COUNTS,
            "task_coverage_summary": task_rows,
            "sample_coverage_summary": sample_rows,
            "dedicated_transformation_review_samples": [EXPECTED_SAMPLES[7][0], EXPECTED_SAMPLES[9][0]],
            "samples_missing_dedicated_transformation_review": [
                sample_id for sample_id, _pdb, _ligand in EXPECTED_SAMPLES if sample_id not in UNIT_SAMPLE_IDS
            ],
            "sidecar_files_excluding_manifest": {
                name: _artifact_identity(payload) for name, payload in csv_artifacts.items()
            },
            "readiness": _readiness(),
            "repository_lifecycle": lifecycle,
        }
        _validate_manifest_contract(manifest, records, task_rows, sample_rows)
        manifest_bytes = (
            json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False) + "\n"
        ).encode("utf-8")
        artifacts = {**csv_artifacts, ARTIFACT_NAMES[3]: manifest_bytes}
        _validate_artifacts(artifacts)
        return artifacts
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR_TOKEN:
            raise
        raise ValueError(ERROR_TOKEN) from error
