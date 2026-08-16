"""Current11 authoritative training-supervision materialization V1.

The product path is pure and in-memory: callers provide an explicit authority
payload and receive the exact source dictionary consumed by the published
training tensorizer.  File-system discovery and review-packet publication are
separate, explicitly named offline helpers.  No path in this module reads a
checkpoint, invokes Git, imports RDKit, or executes a model/training operation.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import re
from pathlib import Path
from typing import NoReturn

from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    AUTHORITATIVE_SUPERVISION_SCHEMA_V1,
    _REQUIRED_AUTHORITY_FIELDS,
    _RUNTIME_DERIVED_FORBIDDEN_INPUTS,
)
from covalent_ext.covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1 import (
    CHECKPOINT_CHANNEL_ORDER,
    CHECKPOINT_TOKEN_TO_INDEX,
    project_type_symbols_to_checkpoint_heavy_v1,
)


__all__ = (
    "CURRENT11_SAMPLE_KEYS_V1",
    "MACHINE_AUTHORITY_PAYLOAD_SCHEMA_V1",
    "TRAINABLE_SUPERVISION_MATERIALIZATION_SCHEMA_V1",
    "build_current11_role_seed_review_packet_v1",
    "build_current11_training_supervision_v1",
    "load_covapie_current11_machine_authority_payload_v1",
    "validate_authoritative_current11_training_supervision_v1",
    "write_current11_role_seed_review_packet_v1",
)


MATERIALIZER_ERROR = (
    "COVAPIE_CURRENT11_TRAINABLE_SUPERVISION_MATERIALIZER_V1_ERROR"
)
MACHINE_AUTHORITY_PAYLOAD_SCHEMA_V1 = (
    "covapie_current11_machine_authority_payload_v1"
)
TRAINABLE_SUPERVISION_MATERIALIZATION_SCHEMA_V1 = (
    "covapie_current11_trainable_supervision_materialization_v1"
)
CURRENT11_SAMPLE_KEYS_V1 = tuple(
    f"CYS_SG_SAMPLE_INDEX_{index:06d}" for index in range(1, 12)
)
AUTHORITY_CLASSES_V1 = frozenset((
    "AUTHORITATIVE_HUMAN_GOLD",
    "AUTHORITATIVE_MACHINE_DERIVED",
    "CANDIDATE_ONLY",
    "MISSING",
    "NOT_APPLICABLE",
))
ROLE_NAMES_V1 = ("scaffold", "linker", "warhead")
ROLE_NAME_TO_ID_V1 = {name: index for index, name in enumerate(ROLE_NAMES_V1)}
SPLITS_V1 = ("train", "val", "test")
_SAMPLE_KEY = re.compile(r"^CYS_SG_SAMPLE_INDEX_[0-9]{6}$")
_SELF_REVIEWER_IDS = frozenset(("codex", "openai", "chatgpt", "gpt"))
_CUSTOM_RUNTIME_FORBIDDEN = frozenset((
    "sixth_mask",
    "seed_as_role",
    "seed_role_id",
    "seed_task_id",
    "canonical_seed_mask",
))
_RUNTIME_FORBIDDEN = _RUNTIME_DERIVED_FORBIDDEN_INPUTS | _CUSTOM_RUNTIME_FORBIDDEN

_TOP_FIELDS = frozenset(("schema_version", "sample_order", "samples"))
_SAMPLE_FIELDS = frozenset((
    "sample_key",
    "pdb_id",
    "ligand_comp_id",
    "split",
    "source_split_value",
    "ligand_nodes",
    "pocket_nodes",
    "target_residue",
    "target_reactive_pocket_local_index",
    "positive_pair",
    "observed_complex_pair_distance_angstrom",
    "observed_complex_pair_distance_valid",
    "pre_post_geometry_target_angstrom",
    "pre_post_geometry_component_valid_mask",
    "pre_post_geometry_component_loss_mask",
    "role_authority",
    "seed_authority",
    "review_evidence",
    "mandatory_provenance_valid",
))
_LIGAND_NODE_FIELDS = frozenset((
    "retained_local_index",
    "source_row_index",
    "parser_local_index",
    "atom_site_id",
    "element",
    "atom_name",
    "coordinates",
    "one_hot",
))
_POCKET_NODE_FIELDS = _LIGAND_NODE_FIELDS | frozenset((
    "residue_name",
    "auth_asym_id",
    "auth_seq_id",
    "label_asym_id",
    "label_seq_id",
))
_TARGET_FIELDS = frozenset((
    "model_num",
    "auth_asym_id",
    "auth_seq_id",
    "insertion_code",
    "residue_name",
    "label_asym_id",
    "label_seq_id",
    "reactive_atom_name",
    "reactive_element",
    "reactive_atom_site_id",
    "authority_class",
))
_PAIR_FIELDS = frozenset((
    "ligand_local_index",
    "ligand_source_row_index",
    "ligand_atom_site_id",
    "pocket_local_index",
    "pocket_source_row_index",
    "pocket_atom_site_id",
    "output17_ligand_flat_index",
    "output17_pocket_flat_index",
    "output17_parser_ligand_local_index",
    "output17_parser_pocket_local_index",
    "authority_class",
))
_ROLE_AUTHORITY_FIELDS = frozenset((
    "authority_class",
    "role_ids",
    "role_valid",
    "candidate_role_names",
    "proposal_only",
    "human_approved",
    "review_disposition",
    "reviewer_id",
    "attestation",
))
_SEED_AUTHORITY_FIELDS = frozenset((
    "authority_class",
    "mask",
    "valid",
    "candidate_mask",
    "proposal_only",
    "human_approved",
    "review_disposition",
    "reviewer_id",
    "attestation",
))
_REVIEW_EVIDENCE_FIELDS = frozenset((
    "warhead_authority_class",
    "reviewed_warhead_atom_ids",
    "reviewed_warhead_present_local_indices",
    "reviewed_warhead_unmapped_atom_ids",
    "reviewed_boundary_records",
    "murcko_scaffold_smiles",
    "murcko_scaffold_status",
    "brics_input_status",
    "reaction_family_id",
    "reaction_family_authority_status",
    "warhead_rule_id",
    "warhead_rule_authority_status",
    "proposal_rationale",
))
_BOUNDARY_FIELDS = frozenset((
    "warhead_attachment_atom_id",
    "nonwarhead_boundary_atom_id",
    "boundary_bond_order",
    "boundary_bond_id",
))
_OUTPUT17_SAMPLE_FIELDS = frozenset((
    "sample_index_row_id",
    "sample_preparation_input_id",
    "pdb_id",
    "ligand_comp_id",
))

_SAMPLE_INDEX = Path(
    "data/derived/covalent_small/"
    "covapie_unified_independence_group_assignment_and_sample_index_merge_smoke_v0/"
    "unified_sample_index.csv"
)
_SPLIT_ASSIGNMENT = Path(
    "data/derived/covalent_small/"
    "covapie_unified_leakage_split_materialization_smoke_v0/"
    "covapie_sample_split_assignment.csv"
)
_PAIR_MAPPING = Path(
    "data/derived/covalent_small/"
    "covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_"
    "evidence_validation_v1/"
    "covapie_atom_pair_atom_table_mapping_validation_matrix.csv"
)
_ROLE_AUTHORITY_MATRIX = Path(
    "data/derived/covalent_small/"
    "covapie_role_annotation_input_authority_gap_resolution_v1/"
    "covapie_current11_role_input_authority_matrix.csv"
)
_FAMILY_RULE_MATRIX = Path(
    "data/derived/covalent_small/"
    "covapie_current11_reaction_family_and_approved_warhead_rule_authority_binding_v1/"
    "covapie_current11_family_rule_authority_binding_matrix.csv"
)
_MURCKO_EVIDENCE = Path(
    "data/derived/covalent_small/"
    "covapie_independent_group_expansion_batch_independence_evidence_"
    "materialization_smoke_v0/covapie_ligand_graph_scaffold_evidence.csv"
)
_TARGET_AUTHORITY = Path(
    "manual-review/covapie_current11_target_residue_atom_condition_authority_bundle_v1.json"
)
_POCKET_ALIGNMENT = Path(
    "manual-review/covapie_current11_pocket_atom_identity_alignment_bundle_v1.json"
)
_UNIFIED_WARHEAD = Path(
    "manual-review/covapie_current11_unified_effective_authority_view_v1.json"
)
_ROUTING_RECORDS = Path(
    "formal-sidecars/current11-dataset-partial-supervision-routing-sidecar-v1/"
    "current11_dataset_partial_supervision_routing_records.csv"
)
_FORMAL_CARRIER = Path(
    "formal-sidecars/current11-runtime-sample-and-role-order-carrier-v1/"
    "current11_runtime_sample_and_role_order_carrier.npz"
)
_FORMAL_CARRIER_BINDING = Path(
    "formal-sidecars/current11-runtime-sample-and-role-order-carrier-v1/"
    "current11_runtime_sample_and_role_order_carrier_binding_report.json"
)


class _MaterializerInvariantError(Exception):
    pass


def _fail() -> NoReturn:
    raise _MaterializerInvariantError()


def _dict(value: object, *, fields: frozenset[str] | None = None) -> dict[str, object]:
    if type(value) is not dict:
        _fail()
    result = value
    if fields is not None and set(result) != fields:
        _fail()
    return result  # type: ignore[return-value]


def _sequence(value: object, *, length: int | None = None) -> tuple[object, ...]:
    if type(value) not in (list, tuple):
        _fail()
    result = tuple(value)
    if length is not None and len(result) != length:
        _fail()
    return result


def _bool(value: object) -> bool:
    if type(value) is not bool:
        _fail()
    return value


def _int(value: object, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        _fail()
    return value


def _float(value: object, *, allow_nan: bool = False) -> float:
    if type(value) is not float:
        _fail()
    if math.isnan(value):
        if not allow_nan:
            _fail()
    elif not math.isfinite(value) or value < 0:
        _fail()
    return value


def _text(value: object, *, allow_empty: bool = False) -> str:
    if type(value) is not str or value.strip() != value:
        _fail()
    if not allow_empty and not value:
        _fail()
    return value


def _scan_for_runtime_fields(value: object) -> None:
    if type(value) is dict:
        if set(value) & _RUNTIME_FORBIDDEN:
            _fail()
        for item in value.values():
            _scan_for_runtime_fields(item)
    elif type(value) in (list, tuple):
        for item in value:
            _scan_for_runtime_fields(item)


def _reviewer_is_human(reviewer_id: object, attestation: object) -> bool:
    reviewer = _text(reviewer_id, allow_empty=True)
    statement = _text(attestation, allow_empty=True)
    return bool(
        reviewer
        and statement
        and reviewer.casefold() not in _SELF_REVIEWER_IDS
        and not any(token in reviewer.casefold() for token in ("codex", "chatgpt"))
    )


def _validate_node(
    value: object, *, local_index: int, pocket: bool
) -> dict[str, object]:
    node = _dict(
        value, fields=_POCKET_NODE_FIELDS if pocket else _LIGAND_NODE_FIELDS
    )
    if (
        _int(node["retained_local_index"]) != local_index
        or _int(node["parser_local_index"]) != local_index
    ):
        _fail()
    _int(node["source_row_index"])
    _text(node["atom_site_id"])
    element = _text(node["element"])
    _text(node["atom_name"])
    if element == "H" or element not in CHECKPOINT_TOKEN_TO_INDEX:
        _fail()
    coordinates = _sequence(node["coordinates"], length=3)
    if any(type(item) is not float or not math.isfinite(item) for item in coordinates):
        _fail()
    one_hot = _sequence(node["one_hot"], length=10)
    if any(type(item) is not float or item not in (0.0, 1.0) for item in one_hot):
        _fail()
    if sum(one_hot) != 1.0 or one_hot[CHECKPOINT_TOKEN_TO_INDEX[element]] != 1.0:
        _fail()
    if pocket:
        for name in (
            "residue_name", "auth_asym_id", "auth_seq_id",
            "label_asym_id", "label_seq_id",
        ):
            _text(node[name])
    return node


def _target_membership(
    *, pocket_nodes: tuple[dict[str, object], ...], target: dict[str, object]
) -> tuple[bool, ...]:
    if set(target) != _TARGET_FIELDS:
        _fail()
    _int(target["model_num"], minimum=1)
    for name in (
        "auth_asym_id", "auth_seq_id", "residue_name", "label_asym_id",
        "label_seq_id", "reactive_atom_name", "reactive_element",
        "reactive_atom_site_id", "authority_class",
    ):
        _text(target[name])
    insertion = _text(target["insertion_code"], allow_empty=True)
    if insertion != "":
        # Current source tables do not carry insertion-code columns.  A future
        # nonblank target must bring an explicitly extended node contract.
        _fail()
    if (
        target["authority_class"] != "AUTHORITATIVE_MACHINE_DERIVED"
        or target["reactive_atom_name"] != "SG"
        or target["reactive_element"] != "S"
        or target["residue_name"] != "CYS"
    ):
        _fail()
    mask = tuple(
        node["auth_asym_id"] == target["auth_asym_id"]
        and node["auth_seq_id"] == target["auth_seq_id"]
        and node["label_asym_id"] == target["label_asym_id"]
        and node["label_seq_id"] == target["label_seq_id"]
        and node["residue_name"] == target["residue_name"]
        for node in pocket_nodes
    )
    if not any(mask):
        _fail()
    return mask


def _validate_geometry(sample: dict[str, object]) -> None:
    observed = _float(
        sample["observed_complex_pair_distance_angstrom"], allow_nan=True
    )
    observed_valid = _bool(sample["observed_complex_pair_distance_valid"])
    if observed_valid == math.isnan(observed):
        _fail()
    targets = _sequence(sample["pre_post_geometry_target_angstrom"], length=2)
    valid = _sequence(
        sample["pre_post_geometry_component_valid_mask"], length=2
    )
    loss = _sequence(
        sample["pre_post_geometry_component_loss_mask"], length=2
    )
    if any(type(item) is not bool for item in valid + loss):
        _fail()
    for target_value, is_valid, in_loss in zip(targets, valid, loss):
        target_float = _float(target_value, allow_nan=True)
        if in_loss and not is_valid:
            _fail()
        if is_valid:
            if math.isnan(target_float):
                _fail()
        elif not math.isnan(target_float):
            # Prevent observed/zero/mean substitution into absent pre/post.
            _fail()


def _validate_role_authority(
    value: object, *, ligand_count: int
) -> tuple[tuple[int, ...], tuple[bool, ...], bool]:
    authority = _dict(value, fields=_ROLE_AUTHORITY_FIELDS)
    authority_class = _text(authority["authority_class"])
    if authority_class not in AUTHORITY_CLASSES_V1:
        _fail()
    roles = _sequence(authority["role_ids"], length=ligand_count)
    valid = _sequence(authority["role_valid"], length=ligand_count)
    candidates = _sequence(
        authority["candidate_role_names"], length=ligand_count
    )
    if (
        any(type(item) is not int for item in roles)
        or any(type(item) is not bool for item in valid)
        or any(type(item) is not str or item not in ("", *ROLE_NAMES_V1) for item in candidates)
    ):
        _fail()
    proposal_only = _bool(authority["proposal_only"])
    human_approved = _bool(authority["human_approved"])
    _text(authority["review_disposition"])
    human = _reviewer_is_human(authority["reviewer_id"], authority["attestation"])
    is_gold = authority_class == "AUTHORITATIVE_HUMAN_GOLD"
    if is_gold:
        if (
            proposal_only
            or not human_approved
            or not human
            or not all(valid)
            or any(role not in (0, 1, 2) for role in roles)
            or set(roles) != {0, 1, 2}
        ):
            _fail()
    else:
        if human_approved or human or any(valid) or any(role != -1 for role in roles):
            _fail()
        if authority_class == "CANDIDATE_ONLY" and not proposal_only:
            _fail()
    return roles, valid, is_gold


def _validate_seed_authority(
    value: object,
    *, ligand_count: int,
) -> tuple[tuple[bool, ...], bool, bool]:
    authority = _dict(value, fields=_SEED_AUTHORITY_FIELDS)
    authority_class = _text(authority["authority_class"])
    if authority_class not in AUTHORITY_CLASSES_V1:
        _fail()
    mask = _sequence(authority["mask"], length=ligand_count)
    candidates = _sequence(authority["candidate_mask"], length=ligand_count)
    if any(type(item) is not bool for item in mask + candidates):
        _fail()
    valid = _bool(authority["valid"])
    proposal_only = _bool(authority["proposal_only"])
    human_approved = _bool(authority["human_approved"])
    _text(authority["review_disposition"])
    human = _reviewer_is_human(authority["reviewer_id"], authority["attestation"])
    is_gold = authority_class == "AUTHORITATIVE_HUMAN_GOLD"
    if is_gold:
        if (
            proposal_only
            or not human_approved
            or not human
            or not valid
            or not any(mask)
        ):
            _fail()
    else:
        if human_approved or human or valid or any(mask):
            _fail()
        if authority_class == "CANDIDATE_ONLY" and not proposal_only:
            _fail()
    return mask, valid, is_gold


def _validate_review_evidence(value: object) -> dict[str, object]:
    evidence = _dict(value, fields=_REVIEW_EVIDENCE_FIELDS)
    authority = _text(evidence["warhead_authority_class"])
    if authority not in AUTHORITY_CLASSES_V1:
        _fail()
    for field in (
        "murcko_scaffold_smiles", "murcko_scaffold_status", "brics_input_status",
        "reaction_family_id", "reaction_family_authority_status",
        "warhead_rule_id", "warhead_rule_authority_status", "proposal_rationale",
    ):
        _text(evidence[field], allow_empty=field == "murcko_scaffold_smiles")
    atom_ids = _sequence(evidence["reviewed_warhead_atom_ids"])
    present = _sequence(evidence["reviewed_warhead_present_local_indices"])
    unmapped = _sequence(evidence["reviewed_warhead_unmapped_atom_ids"])
    boundaries = _sequence(evidence["reviewed_boundary_records"])
    if (
        not atom_ids
        or any(type(item) is not str or not item for item in atom_ids)
        or len(atom_ids) != len(set(atom_ids))
        or any(type(item) is not int or item < 0 for item in present)
        or len(present) != len(set(present))
        or any(type(item) is not str or not item for item in unmapped)
        or len(unmapped) != len(set(unmapped))
        or not boundaries
        or any(
            type(item) is not dict
            or set(item) != _BOUNDARY_FIELDS
            or any(type(field) is not str or not field for field in item.values())
            for item in boundaries
        )
    ):
        _fail()
    reviewed = set(atom_ids)
    if set(unmapped) - reviewed:
        _fail()
    for boundary in boundaries:
        if (
            boundary["warhead_attachment_atom_id"] not in reviewed
            or boundary["nonwarhead_boundary_atom_id"] in reviewed
        ):
            _fail()
    return evidence


def _build_impl(authority_payload: object) -> dict[str, object]:
    payload = _dict(authority_payload, fields=_TOP_FIELDS)
    _scan_for_runtime_fields(payload)
    if payload["schema_version"] != MACHINE_AUTHORITY_PAYLOAD_SCHEMA_V1:
        _fail()
    sample_order = _sequence(payload["sample_order"], length=11)
    if sample_order != CURRENT11_SAMPLE_KEYS_V1:
        _fail()
    samples = _sequence(payload["samples"], length=11)

    ligand_offsets = [0]
    pocket_offsets = [0]
    all_roles: list[int] = []
    all_role_valid: list[bool] = []
    all_seed: list[bool] = []
    seed_valid: list[bool] = []
    admitted: list[bool] = []
    all_membership: list[bool] = []
    observed: list[float] = []
    observed_valid: list[bool] = []
    geometry: list[list[float]] = []
    geometry_valid: list[list[bool]] = []
    geometry_loss: list[list[bool]] = []
    reconciliation: list[dict[str, object]] = []

    for sample_index, raw_sample in enumerate(samples):
        sample = _dict(raw_sample, fields=_SAMPLE_FIELDS)
        key = _text(sample["sample_key"])
        if key != sample_order[sample_index] or _SAMPLE_KEY.fullmatch(key) is None:
            _fail()
        _text(sample["pdb_id"])
        _text(sample["ligand_comp_id"])
        split = _text(sample["split"])
        if split not in SPLITS_V1:
            _fail()
        source_split = _text(sample["source_split_value"])
        if {
            "train": "train",
            "validation": "val",
            "test": "test",
        }.get(source_split) != split:
            _fail()
        provenance_valid = _bool(sample["mandatory_provenance_valid"])

        raw_ligand = _sequence(sample["ligand_nodes"])
        raw_pocket = _sequence(sample["pocket_nodes"])
        if not raw_ligand or not raw_pocket:
            _fail()
        ligand_nodes = tuple(
            _validate_node(node, local_index=index, pocket=False)
            for index, node in enumerate(raw_ligand)
        )
        pocket_nodes = tuple(
            _validate_node(node, local_index=index, pocket=True)
            for index, node in enumerate(raw_pocket)
        )
        ligand_offsets.append(ligand_offsets[-1] + len(ligand_nodes))
        pocket_offsets.append(pocket_offsets[-1] + len(pocket_nodes))

        target = _dict(sample["target_residue"], fields=_TARGET_FIELDS)
        membership = _target_membership(pocket_nodes=pocket_nodes, target=target)
        reactive_local = _int(sample["target_reactive_pocket_local_index"])
        if reactive_local >= len(pocket_nodes):
            _fail()
        reactive = pocket_nodes[reactive_local]
        if (
            not membership[reactive_local]
            or reactive["atom_name"] != target["reactive_atom_name"]
            or reactive["element"] != target["reactive_element"]
            or reactive["atom_site_id"] != target["reactive_atom_site_id"]
            or sum(
                node["atom_name"] == target["reactive_atom_name"]
                and node["atom_site_id"] == target["reactive_atom_site_id"]
                for node in pocket_nodes
            ) != 1
        ):
            _fail()

        pair = _dict(sample["positive_pair"], fields=_PAIR_FIELDS)
        ligand_local = _int(pair["ligand_local_index"])
        pocket_local = _int(pair["pocket_local_index"])
        if ligand_local >= len(ligand_nodes) or pocket_local >= len(pocket_nodes):
            _fail()
        ligand_node = ligand_nodes[ligand_local]
        pocket_node = pocket_nodes[pocket_local]
        if (
            pair["authority_class"] != "AUTHORITATIVE_MACHINE_DERIVED"
            or pocket_local != reactive_local
            or not membership[pocket_local]
            or pair["ligand_source_row_index"] != ligand_node["source_row_index"]
            or pair["pocket_source_row_index"] != pocket_node["source_row_index"]
            or pair["ligand_atom_site_id"] != ligand_node["atom_site_id"]
            or pair["pocket_atom_site_id"] != pocket_node["atom_site_id"]
            or pair["output17_ligand_flat_index"]
            != ligand_offsets[-2] + ligand_local
            or pair["output17_pocket_flat_index"]
            != pocket_offsets[-2] + pocket_local
            or pair["output17_parser_ligand_local_index"] != ligand_local
            or pair["output17_parser_pocket_local_index"] != pocket_local
        ):
            _fail()

        _validate_geometry(sample)
        roles, role_valid, roles_gold = _validate_role_authority(
            sample["role_authority"], ligand_count=len(ligand_nodes)
        )
        seed, is_seed_valid, seed_gold = _validate_seed_authority(
            sample["seed_authority"],
            ligand_count=len(ligand_nodes),
        )
        evidence = _validate_review_evidence(sample["review_evidence"])
        present_indices = tuple(
            evidence["reviewed_warhead_present_local_indices"]
        )
        reviewed_ids = set(evidence["reviewed_warhead_atom_ids"])
        unmapped_ids = set(evidence["reviewed_warhead_unmapped_atom_ids"])
        ligand_atom_names = tuple(node["atom_name"] for node in ligand_nodes)
        ligand_atom_name_set = set(ligand_atom_names)
        if (
            len(ligand_atom_names) != len(ligand_atom_name_set)
            or any(index >= len(ligand_nodes) for index in present_indices)
            or len(present_indices) != len(reviewed_ids - unmapped_ids)
            or {
                ligand_nodes[index]["atom_name"] for index in present_indices
            }
            != reviewed_ids - unmapped_ids
            or unmapped_ids != reviewed_ids - ligand_atom_name_set
            or any(
                boundary["warhead_attachment_atom_id"] not in ligand_atom_name_set
                or boundary["nonwarhead_boundary_atom_id"] not in ligand_atom_name_set
                for boundary in evidence["reviewed_boundary_records"]
            )
        ):
            _fail()

        sample_admitted = bool(
            provenance_valid
            and roles_gold
            and seed_gold
            and evidence["warhead_authority_class"]
            == "AUTHORITATIVE_HUMAN_GOLD"
        )
        all_roles.extend(roles)
        all_role_valid.extend(role_valid)
        all_seed.extend(seed)
        seed_valid.append(is_seed_valid)
        admitted.append(sample_admitted)
        all_membership.extend(membership)
        observed.append(sample["observed_complex_pair_distance_angstrom"])
        observed_valid.append(sample["observed_complex_pair_distance_valid"])
        geometry.append(list(sample["pre_post_geometry_target_angstrom"]))
        geometry_valid.append(
            list(sample["pre_post_geometry_component_valid_mask"])
        )
        geometry_loss.append(
            list(sample["pre_post_geometry_component_loss_mask"])
        )
        blockers: list[str] = []
        if not roles_gold:
            blockers.append("EXACT3_ROLE_HUMAN_GOLD_MISSING")
        if not seed_gold:
            blockers.append("MINIMAL_SEED_HUMAN_GOLD_MISSING")
        if not provenance_valid:
            blockers.append("MANDATORY_PROVENANCE_INVALID")
        reconciliation.append({
            "sample_key": key,
            "pdb_id": sample["pdb_id"],
            "ligand_comp_id": sample["ligand_comp_id"],
            "retained_ligand_heavy_atom_count": len(ligand_nodes),
            "retained_pocket_heavy_atom_count": len(pocket_nodes),
            "target_residue_membership_count": sum(membership),
            "target_reactive_pocket_local_index": reactive_local,
            "positive_ligand_local_index": ligand_local,
            "positive_pocket_local_index": pocket_local,
            "split": split,
            "sample_identity_authority": "AUTHORITATIVE_MACHINE_DERIVED",
            "retained_projection_authority": "AUTHORITATIVE_MACHINE_DERIVED",
            "target_membership_authority": "AUTHORITATIVE_MACHINE_DERIVED",
            "positive_pair_authority": "AUTHORITATIVE_MACHINE_DERIVED",
            "exact3_role_authority": (
                "AUTHORITATIVE_HUMAN_GOLD" if roles_gold else sample["role_authority"]["authority_class"]
            ),
            "minimal_seed_authority": (
                "AUTHORITATIVE_HUMAN_GOLD" if seed_gold else sample["seed_authority"]["authority_class"]
            ),
            "warhead_boundary_authority": evidence["warhead_authority_class"],
            "split_authority": "AUTHORITATIVE_MACHINE_DERIVED",
            "supported_atom_status": "AUTHORITATIVE_MACHINE_DERIVED",
            "observed_geometry_authority": (
                "AUTHORITATIVE_MACHINE_DERIVED"
                if sample["observed_complex_pair_distance_valid"] else "MISSING"
            ),
            "pre_geometry_authority": (
                "AUTHORITATIVE_MACHINE_DERIVED"
                if sample["pre_post_geometry_component_valid_mask"][0] else "MISSING"
            ),
            "post_geometry_authority": (
                "AUTHORITATIVE_MACHINE_DERIVED"
                if sample["pre_post_geometry_component_valid_mask"][1] else "MISSING"
            ),
            "sample_training_admitted": sample_admitted,
            "training_admission_blockers": blockers,
        })

    supervision: dict[str, object] = {
        "schema_version": AUTHORITATIVE_SUPERVISION_SCHEMA_V1,
        "sample_keys": list(sample_order),
        "ligand_node_offsets": ligand_offsets,
        "pocket_node_offsets": pocket_offsets,
        "ligand_role_id": all_roles,
        "ligand_role_valid": all_role_valid,
        "ligand_minimal_seed_or_anchor_mask": all_seed,
        "ligand_minimal_seed_or_anchor_valid": seed_valid,
        "sample_training_admitted": admitted,
        "target_residue_membership_mask": all_membership,
        "observed_complex_pair_distance_angstrom": observed,
        "observed_complex_pair_distance_valid": observed_valid,
        "pre_post_geometry_target_angstrom": geometry,
        "pre_post_geometry_component_valid_mask": geometry_valid,
        "pre_post_geometry_component_loss_mask": geometry_loss,
    }
    validate_authoritative_current11_training_supervision_v1(
        authoritative_supervision=supervision
    )
    return {
        "schema_version": TRAINABLE_SUPERVISION_MATERIALIZATION_SCHEMA_V1,
        "authoritative_supervision": supervision,
        "reconciliation_records": reconciliation,
        "summary": {
            "sample_count": 11,
            "target_residue_membership_count": sum(
                row["target_residue_membership_count"] > 0
                for row in reconciliation
            ),
            "target_reactive_atom_consistency_count": 11,
            "positive_pair_consistency_count": 11,
            "supported_atom_sample_count": 11,
            "unsupported_atom_count": 0,
            "split_binding_count": 11,
            "observed_geometry_count": sum(observed_valid),
            "pre_geometry_authoritative_count": sum(row[0] for row in geometry_valid),
            "post_geometry_authoritative_count": sum(row[1] for row in geometry_valid),
            "exact3_role_human_gold_count": sum(
                row["exact3_role_authority"] == "AUTHORITATIVE_HUMAN_GOLD"
                for row in reconciliation
            ),
            "minimal_seed_human_gold_count": sum(
                row["minimal_seed_authority"] == "AUTHORITATIVE_HUMAN_GOLD"
                for row in reconciliation
            ),
            "real_admitted_sample_count": sum(admitted),
            "checkpoint_channel_order": CHECKPOINT_CHANNEL_ORDER,
        },
    }


def build_current11_training_supervision_v1(
    *, authority_payload: object
) -> dict[str, object]:
    """Build exact tensorizer source fields from an explicit authority payload."""

    try:
        return _build_impl(authority_payload)
    except Exception as error:
        if type(error) is ValueError and str(error) == MATERIALIZER_ERROR:
            raise
        raise ValueError(MATERIALIZER_ERROR) from error


def validate_authoritative_current11_training_supervision_v1(
    *, authoritative_supervision: object
) -> None:
    """Validate the exact published source schema without runtime derivation."""

    try:
        source = _dict(authoritative_supervision)
        if (
            set(source) != _REQUIRED_AUTHORITY_FIELDS
            or set(source) & _RUNTIME_DERIVED_FORBIDDEN_INPUTS
            or source.get("schema_version") != AUTHORITATIVE_SUPERVISION_SCHEMA_V1
            or tuple(_sequence(source.get("sample_keys"), length=11))
            != CURRENT11_SAMPLE_KEYS_V1
        ):
            _fail()
        ligand_roles = _sequence(source.get("ligand_role_id"))
        role_valid = _sequence(
            source.get("ligand_role_valid"), length=len(ligand_roles)
        )
        seed = _sequence(
            source.get("ligand_minimal_seed_or_anchor_mask"),
            length=len(ligand_roles),
        )
        membership = _sequence(source.get("target_residue_membership_mask"))
        if (
            not ligand_roles
            or not membership
            or any(type(item) is not int for item in ligand_roles)
            or any(type(item) is not bool for item in role_valid + seed + membership)
        ):
            _fail()
        ligand_offsets = _sequence(source.get("ligand_node_offsets"), length=12)
        pocket_offsets = _sequence(source.get("pocket_node_offsets"), length=12)
        if (
            any(type(item) is not int for item in ligand_offsets + pocket_offsets)
            or ligand_offsets[0] != 0
            or pocket_offsets[0] != 0
            or ligand_offsets[-1] != len(ligand_roles)
            or pocket_offsets[-1] != len(membership)
            or any(a >= b for a, b in zip(ligand_offsets, ligand_offsets[1:]))
            or any(a >= b for a, b in zip(pocket_offsets, pocket_offsets[1:]))
        ):
            _fail()
        admitted = _sequence(source.get("sample_training_admitted"), length=11)
        seed_valid = _sequence(
            source.get("ligand_minimal_seed_or_anchor_valid"), length=11
        )
        if any(type(item) is not bool for item in admitted + seed_valid):
            _fail()
        for sample in range(11):
            left, right = ligand_offsets[sample:sample + 2]
            sample_roles = ligand_roles[left:right]
            sample_role_valid = role_valid[left:right]
            sample_seed = seed[left:right]
            if any(
                (valid and role not in (0, 1, 2))
                or (not valid and role != -1)
                for role, valid in zip(sample_roles, sample_role_valid)
            ):
                _fail()
            if admitted[sample] and (
                not all(sample_role_valid) or set(sample_roles) != {0, 1, 2}
            ):
                _fail()
            selected_seed = tuple(
                index for index, selected in enumerate(sample_seed) if selected
            )
            if seed_valid[sample] != bool(selected_seed):
                _fail()
            if admitted[sample] and not seed_valid[sample]:
                _fail()
            pleft, pright = pocket_offsets[sample:sample + 2]
            if admitted[sample] and not any(membership[pleft:pright]):
                _fail()
        observed = _sequence(
            source.get("observed_complex_pair_distance_angstrom"), length=11
        )
        observed_valid = _sequence(
            source.get("observed_complex_pair_distance_valid"), length=11
        )
        geometry = _sequence(
            source.get("pre_post_geometry_target_angstrom"), length=11
        )
        geometry_valid = _sequence(
            source.get("pre_post_geometry_component_valid_mask"), length=11
        )
        geometry_loss = _sequence(
            source.get("pre_post_geometry_component_loss_mask"), length=11
        )
        for index in range(11):
            synthetic = {
                "observed_complex_pair_distance_angstrom": observed[index],
                "observed_complex_pair_distance_valid": observed_valid[index],
                "pre_post_geometry_target_angstrom": geometry[index],
                "pre_post_geometry_component_valid_mask": geometry_valid[index],
                "pre_post_geometry_component_loss_mask": geometry_loss[index],
            }
            _validate_geometry(synthetic)
    except Exception as error:
        if type(error) is ValueError and str(error) == MATERIALIZER_ERROR:
            raise
        raise ValueError(MATERIALIZER_ERROR) from error


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def _csv_path(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _json_path(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return _dict(value)


def _rows_by_key(
    rows: list[dict[str, str]], *, key: str = "sample_index_row_id"
) -> dict[str, dict[str, str]]:
    result = {row[key]: row for row in rows}
    if len(result) != len(rows):
        _fail()
    return result


def _load_offline_impl(
    *, repo_root: Path, state_root: Path, runtime_output17: object
) -> dict[str, object]:
    import numpy as np

    repo = repo_root.resolve()
    state = state_root.resolve()
    sample_rows = _csv_path(repo / _SAMPLE_INDEX)
    split_rows = _rows_by_key(_csv_path(repo / _SPLIT_ASSIGNMENT))
    role_rows = _rows_by_key(_csv_path(repo / _ROLE_AUTHORITY_MATRIX))
    family_rows = _rows_by_key(_csv_path(repo / _FAMILY_RULE_MATRIX))
    murcko_rows = _rows_by_key(_csv_path(repo / _MURCKO_EVIDENCE))
    pair_rows = _csv_path(repo / _PAIR_MAPPING)
    pair_by_role = {
        (row["sample_index_row_id"], row["entity_role"]): row
        for row in pair_rows
    }
    if len(pair_by_role) != 22:
        _fail()
    target_bundle = _json_path(state / _TARGET_AUTHORITY)
    alignment_bundle = _json_path(state / _POCKET_ALIGNMENT)
    warhead_bundle = _json_path(state / _UNIFIED_WARHEAD)
    target_by_key = {
        row["sample_index_row_id"]: row
        for row in target_bundle.get("target_residue_atom_condition_records", [])
    }
    alignment_by_key = {
        row["sample_index_row_id"]: row
        for row in alignment_bundle.get("pocket_atom_identity_alignment_records", [])
    }
    warhead_by_key = {
        row["sample_index_row_id"]: row
        for row in warhead_bundle.get("effective_authority_records", [])
    }
    routing_rows = _csv_path(state / _ROUTING_RECORDS)
    routing = {
        (row["sample_index_row_id"], row["semantic_task_name"]): row
        for row in routing_rows
    }
    binding = _json_path(state / _FORMAL_CARRIER_BINDING)
    carrier_path = state / _FORMAL_CARRIER
    if _sha_file(carrier_path) != binding.get("runtime_npz_sha256"):
        _fail()
    output17 = _dict(runtime_output17)
    runtime_order = _sequence(output17.get("batch_sample_order"), length=11)
    runtime_records = tuple(
        _dict(item, fields=_OUTPUT17_SAMPLE_FIELDS) for item in runtime_order
    )
    runtime_keys = tuple(item["sample_index_row_id"] for item in runtime_records)
    if (
        output17.get("remap_status") != "REMAPPED_EXACT"
        or output17.get("failure_reason") != "NONE"
        or runtime_keys != CURRENT11_SAMPLE_KEYS_V1
        or output17.get("pair_values_joint_global_indices") is not None
    ):
        _fail()
    runtime_pairs = _sequence(output17.get("pair_values_batch_indices"), length=11)
    parser_pairs = _sequence(
        output17.get("pair_values_parser_local_indices"), length=11
    )
    if (
        tuple(output17.get("pair_sample_indices", ())) != tuple(range(11))
        or tuple(output17.get("sample_pair_offsets", ())) != tuple(range(12))
        or tuple(output17.get("entry_validity", ())) != (True,) * 11
        or tuple(output17.get("sample_validity", ())) != (True,) * 11
    ):
        _fail()

    if (
        len(sample_rows) != 11
        or tuple(row["sample_index_row_id"] for row in sample_rows)
        != CURRENT11_SAMPLE_KEYS_V1
        or set(target_by_key) != set(CURRENT11_SAMPLE_KEYS_V1)
        or set(alignment_by_key) != set(CURRENT11_SAMPLE_KEYS_V1)
        or set(warhead_by_key) != set(CURRENT11_SAMPLE_KEYS_V1)
    ):
        _fail()

    with np.load(carrier_path, allow_pickle=False) as carrier:
        if tuple(str(item) for item in carrier["names"].tolist()) != CURRENT11_SAMPLE_KEYS_V1:
            _fail()
        arrays = {name: carrier[name].copy() for name in carrier.files}
    required_arrays = {
        "names", "receptors", "lig_mask", "pocket_mask", "lig_coords",
        "pocket_coords", "lig_one_hot", "pocket_one_hot",
        "lig_source_row_index", "pocket_source_row_index",
        "lig_parser_local_index", "pocket_parser_local_index",
    }
    if set(arrays) != required_arrays:
        _fail()
    ligand_offsets = [0]
    pocket_offsets = [0]
    for sample_index in range(11):
        ligand_offsets.append(
            ligand_offsets[-1] + int((arrays["lig_mask"] == sample_index).sum())
        )
        pocket_offsets.append(
            pocket_offsets[-1] + int((arrays["pocket_mask"] == sample_index).sum())
        )
    if (
        ligand_offsets[-1] != 323
        or pocket_offsets[-1] != 2202
        or not np.array_equal(
            arrays["lig_mask"],
            np.repeat(np.arange(11), np.diff(ligand_offsets)),
        )
        or not np.array_equal(
            arrays["pocket_mask"],
            np.repeat(np.arange(11), np.diff(pocket_offsets)),
        )
    ):
        _fail()

    samples: list[dict[str, object]] = []
    for sample_index, index_row in enumerate(sample_rows):
        key = index_row["sample_index_row_id"]
        runtime_record = runtime_records[sample_index]
        if (
            arrays["receptors"][sample_index] != index_row["pdb_id"]
            or runtime_record["pdb_id"] != index_row["pdb_id"]
            or runtime_record["ligand_comp_id"] != index_row["ligand_comp_id"]
            or runtime_record["sample_preparation_input_id"]
            != index_row["sample_preparation_input_id"]
            or role_rows[key]["role_seed_human_gold_review_completed"] != "false"
            or role_rows[key]["warhead_boundary_human_review_completed"] != "true"
        ):
            _fail()
        ligand_table_path = repo / index_row["ligand_atom_table_path"]
        pocket_table_path = repo / index_row["pocket_atom_table_path"]
        ligand_pair_row = pair_by_role[(key, "ligand_atom")]
        pocket_pair_row = pair_by_role[(key, "target_residue_atom")]
        if (
            _sha_file(ligand_table_path) != ligand_pair_row["target_table_sha256"]
            or _sha_file(pocket_table_path) != pocket_pair_row["target_table_sha256"]
        ):
            _fail()
        ligand_source = _csv_path(ligand_table_path)
        pocket_source = _csv_path(pocket_table_path)
        ligand_projection = project_type_symbols_to_checkpoint_heavy_v1(
            tuple(row.get("type_symbol") for row in ligand_source)
        )
        pocket_projection = project_type_symbols_to_checkpoint_heavy_v1(
            tuple(row.get("type_symbol") for row in pocket_source)
        )
        if ligand_projection.sample_rejected or pocket_projection.sample_rejected:
            _fail()
        ligand_retained = [
            (source_index, row)
            for source_index, (row, keep) in enumerate(
                zip(ligand_source, ligand_projection.keep_mask)
            )
            if keep
        ]
        pocket_retained = [
            (source_index, row)
            for source_index, (row, keep) in enumerate(
                zip(pocket_source, pocket_projection.keep_mask)
            )
            if keep
        ]
        lstart, lend = ligand_offsets[sample_index:sample_index + 2]
        pstart, pend = pocket_offsets[sample_index:sample_index + 2]

        def nodes(
            retained: list[tuple[int, dict[str, str]]],
            *, start: int,
            role: str,
        ) -> list[dict[str, object]]:
            source_indices = arrays[f"{role}_source_row_index"][start:start + len(retained)]
            parser_indices = arrays[f"{role}_parser_local_index"][start:start + len(retained)]
            coordinates = arrays[f"{role}_coords"][start:start + len(retained)]
            one_hot = arrays[f"{role}_one_hot"][start:start + len(retained)]
            result: list[dict[str, object]] = []
            for local, (source_index, row) in enumerate(retained):
                expected_one_hot = [0.0] * 10
                expected_one_hot[CHECKPOINT_TOKEN_TO_INDEX[row["type_symbol"]]] = 1.0
                expected_coords = np.asarray(
                    [float(row[name]) for name in ("x", "y", "z")],
                    dtype=np.float32,
                )
                if (
                    int(source_indices[local]) != source_index
                    or int(parser_indices[local]) != local
                    or not np.array_equal(coordinates[local], expected_coords)
                    or one_hot[local].tolist() != expected_one_hot
                ):
                    _fail()
                node: dict[str, object] = {
                    "retained_local_index": local,
                    "source_row_index": source_index,
                    "parser_local_index": local,
                    "atom_site_id": row["atom_site_id"],
                    "element": row["type_symbol"],
                    "atom_name": row["atom_name"],
                    "coordinates": [float(item) for item in coordinates[local]],
                    "one_hot": [float(item) for item in one_hot[local]],
                }
                if role == "pocket":
                    node.update({
                        "residue_name": row["residue_name"],
                        "auth_asym_id": row["auth_asym_id"],
                        "auth_seq_id": row["auth_seq_id"],
                        "label_asym_id": row["label_asym_id"],
                        "label_seq_id": row["label_seq_id"],
                    })
                result.append(node)
            return result

        ligand_nodes = nodes(ligand_retained, start=lstart, role="lig")
        pocket_nodes = nodes(pocket_retained, start=pstart, role="pocket")
        target = target_by_key[key]
        alignment = alignment_by_key[key]
        target_local = int(alignment["target_retained_model_local_index"])
        if (
            alignment["alignment_status"] != "alignment_ready_unique"
            or alignment["target_indicator_true_count"] != 1
            or target_local >= len(pocket_nodes)
            or pocket_nodes[target_local]["atom_site_id"] != target["source_atom_site_id"]
        ):
            _fail()
        ligand_source_index = int(ligand_pair_row["matched_row_index_0based"])
        pocket_source_index = int(pocket_pair_row["matched_row_index_0based"])
        ligand_local_matches = [
            local for local, (source_index, _row) in enumerate(ligand_retained)
            if source_index == ligand_source_index
        ]
        pocket_local_matches = [
            local for local, (source_index, _row) in enumerate(pocket_retained)
            if source_index == pocket_source_index
        ]
        if len(ligand_local_matches) != 1 or pocket_local_matches != [target_local]:
            _fail()
        ligand_local = ligand_local_matches[0]
        runtime_pair = _sequence(runtime_pairs[sample_index], length=2)
        parser_pair = _sequence(parser_pairs[sample_index], length=2)
        if (
            runtime_pair != (pstart + target_local, lstart + ligand_local)
            or parser_pair != (target_local, ligand_local)
        ):
            _fail()
        observed = float(index_row["bond_distance_angstrom"])
        coordinate_distance = float(np.linalg.norm(
            arrays["lig_coords"][lstart + ligand_local]
            - arrays["pocket_coords"][pstart + target_local]
        ))
        if abs(coordinate_distance - observed) > 0.0015:
            _fail()
        if routing[(key, "observed_complex_geometry_supervision")][
            "eligibility_state"
        ] != "admissible_as_observed_geometry_only":
            _fail()
        for task in (
            "pre_covalent_geometry_supervision",
            "post_covalent_geometry_supervision",
        ):
            if not routing[(key, task)]["eligibility_state"].startswith("blocked_"):
                _fail()
        split_source = split_rows[key]["assigned_split"]
        split = {"train": "train", "validation": "val", "test": "test"}.get(split_source)
        if split is None or split_rows[key]["sample_split_assignment_passed"] != "True":
            _fail()
        effective = warhead_by_key[key]["effective_authority_record"]
        if (
            effective["sample_index_row_id"] != key
            or effective["pdb_id"] != index_row["pdb_id"]
            or effective["ligand_comp_id"] != index_row["ligand_comp_id"]
            or effective["authority_status"] != "active"
        ):
            _fail()
        reviewed_ids = list(effective["reviewed_warhead_atom_ids"])
        present_indices = [
            node["retained_local_index"]
            for node in ligand_nodes
            if node["atom_name"] in reviewed_ids
        ]
        present_names = {ligand_nodes[index]["atom_name"] for index in present_indices}
        unmapped_ids = [name for name in reviewed_ids if name not in present_names]
        boundaries = effective.get("reviewed_boundary_records")
        if boundaries is None:
            boundaries = [{
                "warhead_attachment_atom_id": effective["reviewed_warhead_attachment_atom_id"],
                "nonwarhead_boundary_atom_id": effective["reviewed_nonwarhead_boundary_atom_id"],
                "boundary_bond_order": effective["reviewed_attachment_boundary_bond_order"],
                "boundary_bond_id": effective["reviewed_boundary_bond_id"],
            }]
        family = family_rows[key]
        murcko = murcko_rows[key]
        candidate_roles = [
            "warhead" if index in set(present_indices) else ""
            for index in range(len(ligand_nodes))
        ]
        samples.append({
            "sample_key": key,
            "pdb_id": index_row["pdb_id"],
            "ligand_comp_id": index_row["ligand_comp_id"],
            "split": split,
            "source_split_value": split_source,
            "ligand_nodes": ligand_nodes,
            "pocket_nodes": pocket_nodes,
            "target_residue": {
                "model_num": int(target["protein_model_num"]),
                "auth_asym_id": target["protein_auth_asym_id"],
                "auth_seq_id": target["protein_auth_seq_id"],
                "insertion_code": target["protein_pdbx_PDB_ins_code"],
                "residue_name": target["protein_auth_comp_id"],
                "label_asym_id": target["protein_label_asym_id"],
                "label_seq_id": target["protein_label_seq_id"],
                "reactive_atom_name": target["protein_auth_atom_id"],
                "reactive_element": target["protein_type_symbol"],
                "reactive_atom_site_id": target["source_atom_site_id"],
                "authority_class": "AUTHORITATIVE_MACHINE_DERIVED",
            },
            "target_reactive_pocket_local_index": target_local,
            "positive_pair": {
                "ligand_local_index": ligand_local,
                "ligand_source_row_index": ligand_source_index,
                "ligand_atom_site_id": ligand_nodes[ligand_local]["atom_site_id"],
                "pocket_local_index": target_local,
                "pocket_source_row_index": pocket_source_index,
                "pocket_atom_site_id": pocket_nodes[target_local]["atom_site_id"],
                "output17_ligand_flat_index": lstart + ligand_local,
                "output17_pocket_flat_index": pstart + target_local,
                "output17_parser_ligand_local_index": ligand_local,
                "output17_parser_pocket_local_index": target_local,
                "authority_class": "AUTHORITATIVE_MACHINE_DERIVED",
            },
            "observed_complex_pair_distance_angstrom": observed,
            "observed_complex_pair_distance_valid": True,
            "pre_post_geometry_target_angstrom": [float("nan"), float("nan")],
            "pre_post_geometry_component_valid_mask": [False, False],
            "pre_post_geometry_component_loss_mask": [False, False],
            "role_authority": {
                "authority_class": "CANDIDATE_ONLY",
                "role_ids": [-1] * len(ligand_nodes),
                "role_valid": [False] * len(ligand_nodes),
                "candidate_role_names": candidate_roles,
                "proposal_only": True,
                "human_approved": False,
                "review_disposition": "human_exact3_review_missing",
                "reviewer_id": "",
                "attestation": "",
            },
            "seed_authority": {
                "authority_class": "MISSING",
                "mask": [False] * len(ligand_nodes),
                "valid": False,
                "candidate_mask": [False] * len(ligand_nodes),
                "proposal_only": True,
                "human_approved": False,
                "review_disposition": "human_minimal_seed_review_missing",
                "reviewer_id": "",
                "attestation": "",
            },
            "review_evidence": {
                "warhead_authority_class": "AUTHORITATIVE_HUMAN_GOLD",
                "reviewed_warhead_atom_ids": reviewed_ids,
                "reviewed_warhead_present_local_indices": present_indices,
                "reviewed_warhead_unmapped_atom_ids": unmapped_ids,
                "reviewed_boundary_records": list(boundaries),
                "murcko_scaffold_smiles": murcko["murcko_scaffold_smiles"],
                "murcko_scaffold_status": murcko["murcko_scaffold_status"],
                "brics_input_status": role_rows[key]["brics_input_status"],
                "reaction_family_id": family["candidate_reaction_family_id"],
                "reaction_family_authority_status": family["reaction_family_authority_status"],
                "warhead_rule_id": family["candidate_warhead_rule_id"],
                "warhead_rule_authority_status": family["warhead_rule_approval_status"],
                "proposal_rationale": (
                    "partial_reviewed_warhead_projection_only;"
                    "scaffold_linker_and_seed_require_human_review"
                ),
            },
            "mandatory_provenance_valid": True,
        })
    return {
        "schema_version": MACHINE_AUTHORITY_PAYLOAD_SCHEMA_V1,
        "sample_order": list(CURRENT11_SAMPLE_KEYS_V1),
        "samples": samples,
    }


def load_covapie_current11_machine_authority_payload_v1(
    *, repo_root: Path, state_root: Path, runtime_output17: object
) -> dict[str, object]:
    """Offline loader for the SHA-bound repo/state Current11 authority."""

    try:
        return _load_offline_impl(
            repo_root=repo_root,
            state_root=state_root,
            runtime_output17=runtime_output17,
        )
    except Exception as error:
        if type(error) is ValueError and str(error) == MATERIALIZER_ERROR:
            raise
        raise ValueError(MATERIALIZER_ERROR) from error


def _csv_bytes(columns: tuple[str, ...], rows: list[dict[str, object]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer, fieldnames=columns, extrasaction="raise", lineterminator="\n"
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue().encode("utf-8")


def _json_cell(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def build_current11_role_seed_review_packet_v1(
    *, authority_payload: object, materialization: object
) -> dict[str, bytes]:
    """Return deterministic, candidate-only human-review packet bytes."""

    try:
        payload = _dict(authority_payload, fields=_TOP_FIELDS)
        result = _dict(materialization)
        if (
            result.get("schema_version")
            != TRAINABLE_SUPERVISION_MATERIALIZATION_SCHEMA_V1
            or result.get("summary", {}).get("real_admitted_sample_count") != 0
        ):
            _fail()
        samples = _sequence(payload["samples"], length=11)
        worklist: list[dict[str, object]] = []
        evidence_rows: list[dict[str, object]] = []
        decision_rows: list[dict[str, object]] = []
        for raw_sample in samples:
            sample = _dict(raw_sample, fields=_SAMPLE_FIELDS)
            review = _dict(sample["review_evidence"], fields=_REVIEW_EVIDENCE_FIELDS)
            pair = _dict(sample["positive_pair"], fields=_PAIR_FIELDS)
            target = _dict(sample["target_residue"], fields=_TARGET_FIELDS)
            ligand_nodes = _sequence(sample["ligand_nodes"])
            pocket_nodes = _sequence(sample["pocket_nodes"])
            membership = _target_membership(
                pocket_nodes=tuple(
                    _validate_node(node, local_index=index, pocket=True)
                    for index, node in enumerate(pocket_nodes)
                ),
                target=target,
            )
            blockers = (
                "EXACT3_ROLE_HUMAN_GOLD_MISSING;"
                "MINIMAL_SEED_HUMAN_GOLD_MISSING"
            )
            worklist.append({
                "sample_key": sample["sample_key"],
                "pdb_id": sample["pdb_id"],
                "ligand_comp_id": sample["ligand_comp_id"],
                "split": sample["split"],
                "retained_ligand_heavy_atom_count": len(ligand_nodes),
                "retained_pocket_heavy_atom_count": len(pocket_nodes),
                "target_residue_identity": (
                    f"{target['auth_asym_id']}:{target['auth_seq_id']}:"
                    f"{target['insertion_code'] or '<blank>'}:{target['residue_name']}"
                ),
                "target_residue_membership_local_indices": _json_cell(
                    [index for index, item in enumerate(membership) if item]
                ),
                "target_reactive_pocket_local_index": sample["target_reactive_pocket_local_index"],
                "positive_ligand_local_index": pair["ligand_local_index"],
                "positive_pocket_local_index": pair["pocket_local_index"],
                "observed_complex_pair_distance_angstrom": sample["observed_complex_pair_distance_angstrom"],
                "reviewed_warhead_atom_ids": _json_cell(review["reviewed_warhead_atom_ids"]),
                "reviewed_warhead_present_local_indices": _json_cell(review["reviewed_warhead_present_local_indices"]),
                "reviewed_warhead_unmapped_atom_ids": _json_cell(review["reviewed_warhead_unmapped_atom_ids"]),
                "reviewed_boundary_records": _json_cell(review["reviewed_boundary_records"]),
                "warhead_index_space": "retained_heavy_ligand_local_index_0based",
                "murcko_scaffold_smiles": review["murcko_scaffold_smiles"],
                "murcko_scaffold_status": review["murcko_scaffold_status"],
                "brics_input_status": review["brics_input_status"],
                "reaction_family_id": review["reaction_family_id"],
                "reaction_family_authority_status": review["reaction_family_authority_status"],
                "warhead_rule_id": review["warhead_rule_id"],
                "warhead_rule_authority_status": review["warhead_rule_authority_status"],
                "candidate_role_proposal_status": "partial_reviewed_warhead_projection_only",
                "candidate_seed_proposal_status": "not_generated_human_review_required",
                "proposal_only": "true",
                "human_approved": "false",
                "training_authorized": "false",
                "machine_checks_passed": "true",
                "training_blockers": blockers,
            })
            role_authority = _dict(sample["role_authority"], fields=_ROLE_AUTHORITY_FIELDS)
            present = set(review["reviewed_warhead_present_local_indices"])
            boundary_by_name: dict[str, list[str]] = {}
            for boundary in review["reviewed_boundary_records"]:
                boundary_by_name.setdefault(
                    boundary["warhead_attachment_atom_id"], []
                ).append("reviewed_warhead_attachment")
                boundary_by_name.setdefault(
                    boundary["nonwarhead_boundary_atom_id"], []
                ).append("reviewed_nonwarhead_boundary")
            for local, raw_node in enumerate(ligand_nodes):
                node = _validate_node(raw_node, local_index=local, pocket=False)
                evidence_rows.append({
                    "sample_key": sample["sample_key"],
                    "pdb_id": sample["pdb_id"],
                    "ligand_comp_id": sample["ligand_comp_id"],
                    "retained_heavy_ligand_local_index_0based": local,
                    "source_ligand_row_index_0based": node["source_row_index"],
                    "atom_site_id": node["atom_site_id"],
                    "element": node["element"],
                    "atom_name": node["atom_name"],
                    "x": format(node["coordinates"][0], ".9g"),
                    "y": format(node["coordinates"][1], ".9g"),
                    "z": format(node["coordinates"][2], ".9g"),
                    "is_positive_covalent_ligand_atom": str(local == pair["ligand_local_index"]).lower(),
                    "reviewed_warhead_atom": str(local in present).lower(),
                    "reviewed_boundary_roles": ";".join(boundary_by_name.get(node["atom_name"], [])),
                    "candidate_role_proposal": role_authority["candidate_role_names"][local],
                    "candidate_seed_proposal": "false",
                    "proposal_rationale": review["proposal_rationale"],
                    "murcko_scaffold_smiles_evidence": review["murcko_scaffold_smiles"],
                    "murcko_scaffold_status": review["murcko_scaffold_status"],
                    "brics_input_status": review["brics_input_status"],
                    "proposal_only": "true",
                    "human_approved": "false",
                    "training_authorized": "false",
                })
                decision_rows.append({
                    "sample_key": sample["sample_key"],
                    "pdb_id": sample["pdb_id"],
                    "ligand_comp_id": sample["ligand_comp_id"],
                    "retained_heavy_ligand_local_index_0based": local,
                    "atom_site_id": node["atom_site_id"],
                    "atom_name": node["atom_name"],
                    "role_decision": "",
                    "minimal_seed_or_anchor_membership": "",
                    "reviewer_id": "",
                    "review_decision": "",
                    "review_timestamp": "",
                    "attestation": "",
                    "review_notes": "",
                })
        work_columns = tuple(worklist[0])
        evidence_columns = tuple(evidence_rows[0])
        decision_columns = tuple(decision_rows[0])
        readme = (
            "# Current11 Exact3 role and minimal-seed human review V1\n\n"
            "This packet covers the exact 11 Current11 samples. Machine checks "
            "for retained-heavy ordering, checkpoint Exact10 atom mapping, target-"
            "residue membership, reactive CYS SG, Task2 positive pair, split, and "
            "observed geometry passed. Pre/post geometry is unavailable and was not "
            "substituted.\n\n"
            "All role/seed suggestions are candidate-only: `proposal_only=true`, "
            "`human_approved=false`, and `training_authorized=false`. The partial "
            "role suggestion marks only reviewed warhead atoms that remain in the "
            "observed retained-heavy ligand; it does not infer scaffold/linker.\n\n"
            "A human reviewer must assign exactly one of scaffold/linker/warhead to "
            "every retained-heavy ligand atom, with all three classes nonempty, "
            "disjoint, and exhaustive. The seed/anchor is a separate, role-orthogonal "
            "conditioning sidecar. Under the published V1 contract, `valid=true` "
            "requires a nonempty selection of retained-heavy ligand atoms and "
            "`valid=false` requires an empty selection; there is no exact-cardinality "
            "or Exact3-role-subset requirement. It is neither a fourth role nor a "
            "sixth mask. Fill "
            "the decision CSV without changing atom identity/index columns. Reviewer "
            "identity, decision, timestamp, and attestation are intentionally blank.\n"
        ).encode("utf-8")
        return {
            "README.md": readme,
            "current11_role_seed_review_worklist.csv": _csv_bytes(
                work_columns, worklist
            ),
            "current11_role_seed_atom_evidence.csv": _csv_bytes(
                evidence_columns, evidence_rows
            ),
            "current11_role_seed_review_decisions.csv": _csv_bytes(
                decision_columns, decision_rows
            ),
        }
    except Exception as error:
        if type(error) is ValueError and str(error) == MATERIALIZER_ERROR:
            raise
        raise ValueError(MATERIALIZER_ERROR) from error


def write_current11_role_seed_review_packet_v1(
    *, packet_files: object, output_dir: Path
) -> tuple[Path, ...]:
    """Offline no-overwrite writer with exact 0755/0644 physical modes."""

    try:
        files = _dict(packet_files)
        if set(files) != {
            "README.md",
            "current11_role_seed_review_worklist.csv",
            "current11_role_seed_atom_evidence.csv",
            "current11_role_seed_review_decisions.csv",
        } or output_dir.exists() or not output_dir.parent.is_dir():
            _fail()
        if any(type(name) is not str or type(payload) is not bytes for name, payload in files.items()):
            _fail()
        output_dir.mkdir(mode=0o755)
        os.chmod(output_dir, 0o755)
        written: list[Path] = []
        for name, payload in files.items():
            path = output_dir / name
            with path.open("xb") as handle:
                handle.write(payload)
            os.chmod(path, 0o644)
            written.append(path)
        return tuple(written)
    except Exception as error:
        if type(error) is ValueError and str(error) == MATERIALIZER_ERROR:
            raise
        raise ValueError(MATERIALIZER_ERROR) from error
