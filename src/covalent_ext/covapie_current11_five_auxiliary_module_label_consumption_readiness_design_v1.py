"""Audit Current11 label readiness for five future auxiliary modules."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from covalent_ext import (
    covapie_current11_multi_boundary_human_review_ingestion_contract_design_v1
    as multi_design,
)
from covalent_ext import (
    covapie_current11_unified_effective_authority_view_v1 as unified_view,
)
from covalent_ext import (
    covapie_current11_warhead_atom_set_and_attachment_boundary_review_ingestion_gate_design_v1
    as legacy_design,
)


__all__ = ()


_ERROR = "CURRENT11_FIVE_AUXILIARY_MODULE_LABEL_READINESS_DESIGN_INVALID"
_DESIGN_VERSION = (
    "covapie_current11_five_auxiliary_module_label_consumption_readiness_"
    "design_v1"
)
_FORMAL_VIEW_FILESYSTEM_SHA256 = (
    "f4178987f3c3eed0e248f6d3d5f22cb8bce1839d39ab08aff0bff9d2ef9f3774"
)
_FORMAL_VIEW_INTERNAL_SHA256 = (
    "4feb9f1e6531c12a3c653d5c07c37e641d534c20c470f7cad96b902633cab335"
)
_MASK_CONTRACT_SOURCE_PATH = Path(
    "src/covalent_ext/covapie_tensor_label_and_loss_mask_contract_design_v1.py"
)
_MASK_CONTRACT_SOURCE_SHA256 = (
    "3d2d03cda56dfb4a54370444f255f9bb0ab433aaeb837901e769098272ff51ac"
)
_CANONICAL_MASK_TASKS = (
    (0, "warhead_only", "A"),
    (1, "linker_plus_warhead", "B"),
    (2, "scaffold_plus_warhead", "B2"),
    (3, "scaffold_only", "B3"),
    (4, "scaffold_plus_linker_plus_warhead", "C"),
)
_CANONICAL_MASK_NAMES = tuple(item[1] for item in _CANONICAL_MASK_TASKS)
_CANONICAL_MASK_ALIASES = tuple(
    (item[1], item[2]) for item in _CANONICAL_MASK_TASKS
)
_EXPECTED_SAMPLES = tuple(
    f"CYS_SG_SAMPLE_INDEX_{number:06d}" for number in range(1, 12)
)
_LEGACY_SAMPLES = (*_EXPECTED_SAMPLES[:5], _EXPECTED_SAMPLES[10])
_MULTI_SAMPLES = _EXPECTED_SAMPLES[5:10]
_LEGACY_NAMESPACE = "legacy_exact_one_boundary_v1"
_MULTI_NAMESPACE = "exact_two_boundaries_multi_boundary_v1"
_LEGACY_PRECEDENCE_REASON = "ACTIVE_LEGACY_EXACT_ONE_ONLY"
_MULTI_PRECEDENCE_REASON = (
    "ACTIVE_EXACT_TWO_SELECTED_OVER_QUARANTINED_EXACT_ONE_FOR_EFFECTIVE_VIEW"
)
_SHA256 = re.compile(r"[0-9a-f]{64}")

_READINESS_STATUSES = (
    "authority_ready",
    "authority_ready_requires_vocabulary_audit",
    "partial_requires_additional_contract",
    "absent_requires_new_authority",
)
_MODULE_READINESS_STATUSES = (
    "partial_foundation_only",
    "blocked_missing_canonical_labels",
)
_SIGNAL_NAMES = (
    "warhead_type_identity",
    "warhead_atom_set",
    "ligand_internal_warhead_boundary",
    "target_residue_atom_condition",
    "ligand_atom_to_residue_atom_pair",
    "pre_post_covalent_geometry",
    "scaffold_linker_anchor_atom_roles",
    "contrastive_negative_sampling_policy",
)
_MODULE_NAMES = (
    "target_residue_atom_condition_adapter",
    "role_mask_anchor_encoding",
    "covalent_pair_prediction_head",
    "pre_post_geometry_prediction_head",
    "covalent_pair_contrastive_loss",
)
_LINEAGE_ONLY_FIELD_PATHS = (
    "effective_authority_records[].source_resolution_record_sha256",
    "effective_authority_records[].source_authority_record_sha256",
    "effective_authority_records[].unified_effective_authority_record_sha256",
    "effective_authority_records[].precedence_reason",
    "effective_authority_records[].effective_authority_record.source_*_sha256",
    "effective_authority_records[].effective_authority_record.reviewer_id",
    "effective_authority_records[].effective_authority_record.reviewer_provenance_attestor_id",
    "effective_authority_records[].effective_authority_record.review_rationale_sha256",
    "effective_authority_records[].effective_authority_record.review_notes_sha256",
    "effective_authority_records[].effective_authority_record.review_decision",
    "effective_authority_records[].effective_authority_record.authority_disposition",
    "effective_authority_records[].effective_authority_record.authority_record_sha256",
    "effective_authority_records[].effective_authority_record.multi_boundary_authority_record_sha256",
    "effective_authority_records[].effective_authority_record.submission_source_label",
    "unified_effective_authority_view_sha256",
)
_SIGNAL_FIELDS = (
    "signal_name",
    "semantic_definition",
    "source_field_paths",
    "authoritative_sample_coverage",
    "readiness_status",
    "allowed_future_consumers",
    "forbidden_interpretations",
    "missing_semantics",
    "source_is_audit_only",
    "signal_readiness_record_sha256",
)
_MODULE_FIELDS = (
    "module_name",
    "module_purpose",
    "required_signals",
    "available_authoritative_signals",
    "missing_or_partial_signals",
    "readiness_status",
    "implementation_allowed",
    "training_allowed",
    "next_required_contract",
    "feature_semantics_audit_required",
    "module_readiness_record_sha256",
)
_RESPONSE_FIELDS = (
    "five_auxiliary_module_label_consumption_readiness_design_version",
    "source_unified_effective_authority_view_filesystem_sha256",
    "source_unified_effective_authority_view_sha256",
    "canonical_mask_names",
    "canonical_mask_aliases",
    "signal_readiness_records",
    "module_readiness_records",
    "implementation_ready_module_count",
    "ready_for_model_module_implementation",
    "design_response_sha256",
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=True,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except (
        TypeError,
        ValueError,
        UnicodeEncodeError,
        RecursionError,
        OverflowError,
    ) as error:
        raise ValueError(_ERROR) from error


def _record_sha256(
    record: Mapping[str, Any],
    fields: Sequence[str],
    digest_field: str,
) -> str:
    try:
        unsigned = {
            field: record[field] for field in fields if field != digest_field
        }
    except (KeyError, TypeError) as error:
        raise ValueError(_ERROR) from error
    return _sha256(_canonical_json_bytes(unsigned))


def _validate_mask_contract(repo_root: Path) -> None:
    path = repo_root / _MASK_CONTRACT_SOURCE_PATH
    try:
        payload = path.read_bytes()
        if _sha256(payload) != _MASK_CONTRACT_SOURCE_SHA256:
            raise ValueError(_ERROR)
        tree = ast.parse(payload.decode("utf-8"), filename=str(path))
        assignments = tuple(
            node for node in tree.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id == "CANONICAL_TASKS"
                for target in node.targets
            )
        )
        if (
            len(assignments) != 1
            or ast.literal_eval(assignments[0].value) != _CANONICAL_MASK_TASKS
            or len(_CANONICAL_MASK_TASKS) != 5
            or _CANONICAL_MASK_TASKS[3] != (3, "scaffold_only", "B3")
        ):
            raise ValueError(_ERROR)
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error


def _validate_unified_view(payload: bytes) -> dict[str, Any]:
    if (
        type(payload) is not bytes
        or _sha256(payload) != _FORMAL_VIEW_FILESYSTEM_SHA256
    ):
        raise ValueError(_ERROR)
    try:
        view = unified_view._strict_json_object(payload)
    except Exception as error:
        raise ValueError(_ERROR) from error
    if (
        tuple(view) != unified_view.EXACT16_VIEW_FIELDS
        or view["unified_effective_authority_view_version"]
        != unified_view.UNIFIED_EFFECTIVE_VIEW_VERSION
        or view["unified_effective_authority_view_sha256"]
        != _FORMAL_VIEW_INTERNAL_SHA256
        or view["unified_effective_authority_view_sha256"]
        != _record_sha256(
            view,
            unified_view.EXACT16_VIEW_FIELDS,
            "unified_effective_authority_view_sha256",
        )
        or view["sample_order"] != list(_EXPECTED_SAMPLES)
        or type(view["effective_authority_records"]) is not list
        or view["effective_authority_record_count"] != 11
        or view["effective_legacy_exact_one_count"] != 6
        or view["effective_multi_boundary_exact_two_count"] != 5
        or len(view["effective_authority_records"]) != 11
    ):
        raise ValueError(_ERROR)

    legacy_count = 0
    multi_count = 0
    source_authority_sha256s: set[str] = set()
    for index, record in enumerate(view["effective_authority_records"]):
        sample = _EXPECTED_SAMPLES[index]
        if (
            type(record) is not dict
            or tuple(record) != unified_view.EXACT10_EFFECTIVE_RECORD_FIELDS
            or record["unified_effective_authority_record_version"]
            != unified_view.EFFECTIVE_RECORD_VERSION
            or record["sample_index_row_id"] != sample
            or _SHA256.fullmatch(record["source_resolution_record_sha256"])
            is None
            or _SHA256.fullmatch(record["source_authority_record_sha256"])
            is None
            or record["source_authority_record_sha256"]
            in source_authority_sha256s
            or record["unified_effective_authority_record_sha256"]
            != _record_sha256(
                record,
                unified_view.EXACT10_EFFECTIVE_RECORD_FIELDS,
                "unified_effective_authority_record_sha256",
            )
            or type(record["effective_authority_record"]) is not dict
        ):
            raise ValueError(_ERROR)
        source_authority_sha256s.add(record["source_authority_record_sha256"])
        authority = record["effective_authority_record"]
        try:
            if sample in _LEGACY_SAMPLES:
                legacy_design.validate_authority_record(authority)
                expected = (
                    _LEGACY_NAMESPACE,
                    1,
                    _LEGACY_PRECEDENCE_REASON,
                    authority["authority_record_version"],
                    authority["authority_record_sha256"],
                )
                legacy_count += 1
            elif sample in _MULTI_SAMPLES:
                multi_design._validate_authority_record(authority)
                expected = (
                    _MULTI_NAMESPACE,
                    2,
                    _MULTI_PRECEDENCE_REASON,
                    authority["multi_boundary_authority_record_version"],
                    authority["multi_boundary_authority_record_sha256"],
                )
                multi_count += 1
            else:
                raise ValueError(_ERROR)
        except Exception as error:
            raise ValueError(_ERROR) from error
        observed = (
            record["effective_authority_namespace"],
            record["effective_boundary_cardinality"],
            record["precedence_reason"],
            record["source_authority_record_version"],
            record["source_authority_record_sha256"],
        )
        if observed != expected or authority["sample_index_row_id"] != sample:
            raise ValueError(_ERROR)
    if (legacy_count, multi_count) != (6, 5):
        raise ValueError(_ERROR)
    return view


def _signal_record(
    *,
    signal_name: str,
    semantic_definition: str,
    source_field_paths: tuple[str, ...],
    authoritative_sample_coverage: str,
    readiness_status: str,
    allowed_future_consumers: tuple[str, ...],
    forbidden_interpretations: tuple[str, ...],
    missing_semantics: tuple[str, ...],
    source_is_audit_only: bool,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "signal_name": signal_name,
        "semantic_definition": semantic_definition,
        "source_field_paths": source_field_paths,
        "authoritative_sample_coverage": authoritative_sample_coverage,
        "readiness_status": readiness_status,
        "allowed_future_consumers": allowed_future_consumers,
        "forbidden_interpretations": forbidden_interpretations,
        "missing_semantics": missing_semantics,
        "source_is_audit_only": source_is_audit_only,
        "signal_readiness_record_sha256": "",
    }
    if (
        tuple(record) != _SIGNAL_FIELDS
        or signal_name not in _SIGNAL_NAMES
        or readiness_status not in _READINESS_STATUSES
    ):
        raise ValueError(_ERROR)
    record["signal_readiness_record_sha256"] = _record_sha256(
        record, _SIGNAL_FIELDS, "signal_readiness_record_sha256"
    )
    return record


def _build_signal_records() -> tuple[dict[str, Any], ...]:
    effective = "effective_authority_records[].effective_authority_record."
    records = (
        _signal_record(
            signal_name="warhead_type_identity",
            semantic_definition=(
                "Reviewed warhead class, reaction-family, and warhead-rule identity; "
                "IDs are authoritative but their training vocabulary is not yet frozen."
            ),
            source_field_paths=(
                effective + "warhead_type_candidate_class_id",
                effective + "reaction_family_id",
                effective + "warhead_rule_id",
            ),
            authoritative_sample_coverage="11/11",
            readiness_status="authority_ready_requires_vocabulary_audit",
            allowed_future_consumers=(
                "target_residue_atom_condition_adapter",
                "role_mask_anchor_encoding",
            ),
            forbidden_interpretations=(
                "direct_numeric_or_categorical_model_feature_before_vocabulary_audit",
                "unknown_class_policy_already_frozen",
            ),
            missing_semantics=(
                "class_vocabulary",
                "unknown_policy",
                "feature_semantics_audit",
            ),
            source_is_audit_only=False,
        ),
        _signal_record(
            signal_name="warhead_atom_set",
            semantic_definition="Reviewed ligand atom IDs comprising the warhead.",
            source_field_paths=(effective + "reviewed_warhead_atom_ids",),
            authoritative_sample_coverage="11/11",
            readiness_status="authority_ready",
            allowed_future_consumers=("role_mask_anchor_encoding",),
            forbidden_interpretations=(
                "complete_scaffold_linker_anchor_role_assignment",
                "ligand_atom_to_residue_atom_pair",
            ),
            missing_semantics=(),
            source_is_audit_only=False,
        ),
        _signal_record(
            signal_name="ligand_internal_warhead_boundary",
            semantic_definition=(
                "Reviewed ligand warhead to ligand non-warhead attachment boundary; "
                "this is not a ligand-protein covalent pair."
            ),
            source_field_paths=(
                effective + "reviewed_warhead_attachment_atom_id",
                effective + "reviewed_nonwarhead_boundary_atom_id",
                effective + "reviewed_boundary_bond_id",
                effective + "reviewed_boundary_records",
            ),
            authoritative_sample_coverage="11/11",
            readiness_status="authority_ready",
            allowed_future_consumers=("role_mask_anchor_encoding",),
            forbidden_interpretations=("ligand_atom_to_residue_atom_pair",),
            missing_semantics=(),
            source_is_audit_only=False,
        ),
        _signal_record(
            signal_name="target_residue_atom_condition",
            semantic_definition=(
                "Canonical sample-level protein chain, residue, insertion-code, and "
                "residue-atom identity used to condition a covalent model."
            ),
            source_field_paths=(),
            authoritative_sample_coverage="0/11",
            readiness_status="partial_requires_additional_contract",
            allowed_future_consumers=(
                "target_residue_atom_condition_adapter",
                "covalent_pair_prediction_head",
            ),
            forbidden_interpretations=(
                "project_level_cys_sg_scope_as_sample_level_canonical_condition",
            ),
            missing_semantics=(
                "protein_chain_id",
                "protein_residue_name",
                "protein_residue_number",
                "protein_insertion_code",
                "protein_residue_atom_name",
            ),
            source_is_audit_only=False,
        ),
        _signal_record(
            signal_name="ligand_atom_to_residue_atom_pair",
            semantic_definition=(
                "Explicit positive pair linking one ligand reactive atom to one "
                "protein residue atom."
            ),
            source_field_paths=(),
            authoritative_sample_coverage="0/11",
            readiness_status="absent_requires_new_authority",
            allowed_future_consumers=(
                "covalent_pair_prediction_head",
                "pre_post_geometry_prediction_head",
                "covalent_pair_contrastive_loss",
            ),
            forbidden_interpretations=(
                "ligand_internal_warhead_boundary_as_positive_pair",
            ),
            missing_semantics=(
                "ligand_reactive_atom_id",
                "protein_residue_atom_identity",
                "canonical_positive_pair_id",
            ),
            source_is_audit_only=False,
        ),
        _signal_record(
            signal_name="pre_post_covalent_geometry",
            semantic_definition=(
                "Paired pre- and post-covalent distances and orientation geometry "
                "with units, frame, and validity."
            ),
            source_field_paths=(),
            authoritative_sample_coverage="0/11",
            readiness_status="absent_requires_new_authority",
            allowed_future_consumers=("pre_post_geometry_prediction_head",),
            forbidden_interpretations=(
                "ligand_internal_boundary_bond_order_as_covalent_geometry",
            ),
            missing_semantics=(
                "pre_distance",
                "post_distance",
                "bond_angle",
                "dihedral",
                "units",
                "reference_frame",
                "geometry_validity",
            ),
            source_is_audit_only=False,
        ),
        _signal_record(
            signal_name="scaffold_linker_anchor_atom_roles",
            semantic_definition=(
                "Sample-level ligand atom-role authority for scaffold, linker, "
                "anchors, and minimal seed."
            ),
            source_field_paths=(effective + "reviewed_warhead_atom_ids",),
            authoritative_sample_coverage="0/11",
            readiness_status="partial_requires_additional_contract",
            allowed_future_consumers=("role_mask_anchor_encoding",),
            forbidden_interpretations=(
                "warhead_atom_set_as_complete_ligand_role_partition",
                "canonical_mask_names_as_sample_level_atom_roles",
            ),
            missing_semantics=(
                "scaffold_atom_ids",
                "linker_atom_ids",
                "anchor_atom_ids",
                "minimal_seed_atom_ids",
            ),
            source_is_audit_only=False,
        ),
        _signal_record(
            signal_name="contrastive_negative_sampling_policy",
            semantic_definition=(
                "Leakage-safe policy that binds canonical positive pairs to valid "
                "negative candidate groups."
            ),
            source_field_paths=(),
            authoritative_sample_coverage="0/11",
            readiness_status="absent_requires_new_authority",
            allowed_future_consumers=("covalent_pair_contrastive_loss",),
            forbidden_interpretations=(
                "unreviewed_pair_candidates_as_training_negatives",
            ),
            missing_semantics=(
                "positive_pair_id",
                "negative_candidate_group",
                "hard_negative_policy",
                "same_ligand_exclusion",
                "same_target_exclusion",
                "same_reaction_family_policy",
            ),
            source_is_audit_only=False,
        ),
    )
    if tuple(record["signal_name"] for record in records) != _SIGNAL_NAMES:
        raise ValueError(_ERROR)
    return records


def _module_record(
    *,
    module_name: str,
    module_purpose: str,
    required_signals: tuple[str, ...],
    available_authoritative_signals: tuple[str, ...],
    missing_or_partial_signals: tuple[str, ...],
    readiness_status: str,
    next_required_contract: str,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "module_name": module_name,
        "module_purpose": module_purpose,
        "required_signals": required_signals,
        "available_authoritative_signals": available_authoritative_signals,
        "missing_or_partial_signals": missing_or_partial_signals,
        "readiness_status": readiness_status,
        "implementation_allowed": False,
        "training_allowed": False,
        "next_required_contract": next_required_contract,
        "feature_semantics_audit_required": True,
        "module_readiness_record_sha256": "",
    }
    if (
        tuple(record) != _MODULE_FIELDS
        or module_name not in _MODULE_NAMES
        or readiness_status not in _MODULE_READINESS_STATUSES
        or not set(required_signals).issubset(_SIGNAL_NAMES)
    ):
        raise ValueError(_ERROR)
    record["module_readiness_record_sha256"] = _record_sha256(
        record, _MODULE_FIELDS, "module_readiness_record_sha256"
    )
    return record


def _build_module_records() -> tuple[dict[str, Any], ...]:
    records = (
        _module_record(
            module_name="target_residue_atom_condition_adapter",
            module_purpose=(
                "Adapt canonical sample-level target residue-atom identity into a "
                "future conditioning representation."
            ),
            required_signals=("target_residue_atom_condition",),
            available_authoritative_signals=(),
            missing_or_partial_signals=("target_residue_atom_condition",),
            readiness_status="partial_foundation_only",
            next_required_contract=(
                "design_covapie_target_residue_atom_condition_contract_v1"
            ),
        ),
        _module_record(
            module_name="role_mask_anchor_encoding",
            module_purpose=(
                "Encode the five canonical masks from complete sample-level ligand "
                "atom roles and anchors."
            ),
            required_signals=(
                "warhead_atom_set",
                "ligand_internal_warhead_boundary",
                "scaffold_linker_anchor_atom_roles",
            ),
            available_authoritative_signals=(
                "warhead_atom_set",
                "ligand_internal_warhead_boundary",
            ),
            missing_or_partial_signals=("scaffold_linker_anchor_atom_roles",),
            readiness_status="partial_foundation_only",
            next_required_contract=(
                "design_covapie_scaffold_linker_anchor_role_authority_contract_v1"
            ),
        ),
        _module_record(
            module_name="covalent_pair_prediction_head",
            module_purpose=(
                "Predict the canonical ligand reactive atom to protein residue-atom "
                "pair."
            ),
            required_signals=(
                "target_residue_atom_condition",
                "ligand_atom_to_residue_atom_pair",
            ),
            available_authoritative_signals=(),
            missing_or_partial_signals=(
                "target_residue_atom_condition",
                "ligand_atom_to_residue_atom_pair",
            ),
            readiness_status="blocked_missing_canonical_labels",
            next_required_contract=(
                "design_covapie_ligand_residue_covalent_pair_label_contract_v1"
            ),
        ),
        _module_record(
            module_name="pre_post_geometry_prediction_head",
            module_purpose=(
                "Predict validated pre/post covalent geometry for a canonical "
                "ligand-residue atom pair."
            ),
            required_signals=(
                "ligand_atom_to_residue_atom_pair",
                "pre_post_covalent_geometry",
            ),
            available_authoritative_signals=(),
            missing_or_partial_signals=(
                "ligand_atom_to_residue_atom_pair",
                "pre_post_covalent_geometry",
            ),
            readiness_status="blocked_missing_canonical_labels",
            next_required_contract=(
                "design_covapie_pre_post_covalent_geometry_label_contract_v1"
            ),
        ),
        _module_record(
            module_name="covalent_pair_contrastive_loss",
            module_purpose=(
                "Contrast canonical positive pairs against leakage-safe negative "
                "groups under the pair-head semantics."
            ),
            required_signals=(
                "ligand_atom_to_residue_atom_pair",
                "contrastive_negative_sampling_policy",
            ),
            available_authoritative_signals=(),
            missing_or_partial_signals=(
                "ligand_atom_to_residue_atom_pair",
                "contrastive_negative_sampling_policy",
            ),
            readiness_status="blocked_missing_canonical_labels",
            next_required_contract=(
                "design_covapie_covalent_pair_contrastive_sampling_contract_v1"
            ),
        ),
    )
    if tuple(record["module_name"] for record in records) != _MODULE_NAMES:
        raise ValueError(_ERROR)
    return records


def _reference_design_covapie_current11_five_auxiliary_module_label_consumption_readiness_v1(
    *,
    source_unified_effective_authority_view: bytes,
    repo_root: Path,
) -> dict[str, Any]:
    """Return a deterministic, in-memory, fail-closed readiness design."""

    if (
        type(source_unified_effective_authority_view) is not bytes
        or type(repo_root) is not type(Path())
    ):
        raise ValueError(_ERROR)
    source_snapshot = bytes(source_unified_effective_authority_view)
    try:
        _validate_mask_contract(repo_root)
        view = _validate_unified_view(source_unified_effective_authority_view)
        signals = _build_signal_records()
        modules = _build_module_records()
        implementation_ready_count = sum(
            record["implementation_allowed"] is True for record in modules
        )
        response: dict[str, Any] = {
            "five_auxiliary_module_label_consumption_readiness_design_version":
                _DESIGN_VERSION,
            "source_unified_effective_authority_view_filesystem_sha256":
                _sha256(source_unified_effective_authority_view),
            "source_unified_effective_authority_view_sha256":
                view["unified_effective_authority_view_sha256"],
            "canonical_mask_names": _CANONICAL_MASK_NAMES,
            "canonical_mask_aliases": _CANONICAL_MASK_ALIASES,
            "signal_readiness_records": signals,
            "module_readiness_records": modules,
            "implementation_ready_module_count": implementation_ready_count,
            "ready_for_model_module_implementation": False,
            "design_response_sha256": "",
        }
        if (
            tuple(response) != _RESPONSE_FIELDS
            or len(signals) != 8
            or len(modules) != 5
            or implementation_ready_count != 0
            or any(record["implementation_allowed"] for record in modules)
            or any(record["training_allowed"] for record in modules)
            or source_snapshot != source_unified_effective_authority_view
        ):
            raise ValueError(_ERROR)
        response["design_response_sha256"] = _record_sha256(
            response, _RESPONSE_FIELDS, "design_response_sha256"
        )
        return response
    except Exception as error:
        if type(error) is ValueError and str(error) == _ERROR:
            raise
        raise ValueError(_ERROR) from error
