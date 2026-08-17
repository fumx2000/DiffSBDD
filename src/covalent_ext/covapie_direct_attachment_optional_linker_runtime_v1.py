"""Additive optional-linker runtime primitives for direct attachment V1.

This successor owner preserves the published Exact3 role and Exact5 task
vocabularies.  It admits a second role profile in which the linker role is
exactly empty and selects only the non-redundant canonical tasks A, B3, and C.
It does not create review authority or integrate the profile into the
historical Current11 tensorizer.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Mapping, NoReturn, Sequence

from covalent_ext import masking
from covalent_ext import (
    covapie_cys_sg_recovered7_targeted_chemistry_review_packages_v1
    as published_review_packages,
)
from covalent_ext import (
    covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1
    as published_role_contract,
)
from covalent_ext.schema import MaskResult


__all__ = (
    "CANONICAL_ROLE_NAMES_V1",
    "CANONICAL_ROLE_IDS_V1",
    "CANONICAL_TASKS_V1",
    "STRICT_LINKER_PRESENT_V1",
    "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1",
    "ROLE_PROFILES_V1",
    "STRICT_VALID_CANONICAL_TASK_IDS_V1",
    "DIRECT_VALID_CANONICAL_TASK_IDS_V1",
    "OPTIONAL_LINKER_RUNTIME_SCHEDULE_DOMAIN_V1",
    "SCHEDULE_DOMAINS_BY_ROLE_PROFILE_V1",
    "DIRECT_PROFILE_TASK_APPLICABILITY_V1",
    "CURRENT11_TENSORIZER_DIRECT_PROFILE_SUPPORTED_V1",
    "DIRECT_PROFILE_RUNTIME_PRIMITIVES_READY_V1",
    "EXPANDED_TENSORIZER_INTEGRATION_PENDING_V1",
    "MODEL_ARCHITECTURE_CHANGE_REQUIRED_V1",
    "ExplicitBondV1",
    "DirectScaffoldWarheadBoundaryV1",
    "RolePartitionValidationV1",
    "RoleProfileValidationV1",
    "MinimalSeedValidationV1",
    "DirectReviewRoleValidationV1",
    "LightningStructuralCompatibilityV1",
    "valid_canonical_task_ids_for_role_profile_v1",
    "canonical_task_id_for_valid_task_set_v1",
    "canonical_task_id_for_role_profile_v1",
    "validate_role_partition_for_profile_v1",
    "validate_role_profile_v1",
    "build_mask_for_role_profile_v1",
    "validate_minimal_seed_for_role_profile_v1",
    "validate_direct_attachment_review_role_payload_v1",
    "validate_current_lightning_structural_expectations_v1",
    "runtime_readiness_v1",
)


RUNTIME_ERROR = "COVAPIE_DIRECT_ATTACHMENT_OPTIONAL_LINKER_RUNTIME_V1_ERROR"

# These are aliases of the published semantic owners, not a forked vocabulary.
CANONICAL_ROLE_NAMES_V1 = published_role_contract.EXACT3_ROLES
CANONICAL_ROLE_IDS_V1 = (0, 1, 2)
CANONICAL_TASKS_V1 = published_role_contract.CANONICAL_TASKS

STRICT_LINKER_PRESENT_V1 = "STRICT_LINKER_PRESENT_V1"
DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1 = "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
ROLE_PROFILES_V1 = (
    STRICT_LINKER_PRESENT_V1,
    DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1,
)

STRICT_VALID_CANONICAL_TASK_IDS_V1 = tuple(
    task_id for task_id, *_ in CANONICAL_TASKS_V1
)
DIRECT_VALID_CANONICAL_TASK_IDS_V1 = (0, 3, 4)

OPTIONAL_LINKER_RUNTIME_SCHEDULE_DOMAIN_V1 = (
    b"COVAPIE_DIRECT_ATTACHMENT_OPTIONAL_LINKER_RUNTIME_SCHEDULE_V1\0"
)
SCHEDULE_DOMAINS_BY_ROLE_PROFILE_V1 = {
    STRICT_LINKER_PRESENT_V1: (
        OPTIONAL_LINKER_RUNTIME_SCHEDULE_DOMAIN_V1
        + b"STRICT_LINKER_PRESENT_V1\0"
    ),
    DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1: (
        OPTIONAL_LINKER_RUNTIME_SCHEDULE_DOMAIN_V1
        + b"DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1\0"
    ),
}

# Long semantic names remain authoritative; aliases are display-only context.
DIRECT_PROFILE_TASK_APPLICABILITY_V1 = (
    (0, "warhead_only", "A", True, "generate_W_condition_on_S"),
    (
        1,
        "linker_plus_warhead",
        "B",
        False,
        "not_applicable_empty_linker_redundant_with_A",
    ),
    (
        2,
        "scaffold_plus_warhead",
        "B2",
        False,
        "not_applicable_empty_non_C_fixed_context",
    ),
    (3, "scaffold_only", "B3", True, "generate_S_condition_on_W"),
    (
        4,
        "scaffold_plus_linker_plus_warhead",
        "C",
        True,
        "generate_whole_ligand_preserve_Task_C_seed_semantics",
    ),
)

CURRENT11_TENSORIZER_DIRECT_PROFILE_SUPPORTED_V1 = False
DIRECT_PROFILE_RUNTIME_PRIMITIVES_READY_V1 = True
EXPANDED_TENSORIZER_INTEGRATION_PENDING_V1 = True
MODEL_ARCHITECTURE_CHANGE_REQUIRED_V1 = False

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_AtomId = int | str


@dataclass(frozen=True)
class ExplicitBondV1:
    atom_id_1: _AtomId
    atom_id_2: _AtomId
    bond_order: str


@dataclass(frozen=True)
class DirectScaffoldWarheadBoundaryV1:
    scaffold_atom_id: _AtomId
    warhead_atom_id: _AtomId
    bond_order: str
    boundary_valid: bool


@dataclass(frozen=True)
class RolePartitionValidationV1:
    role_profile: str
    valid: bool
    reasons: tuple[str, ...]
    scaffold_count: int | None
    linker_count: int | None
    warhead_count: int | None


@dataclass(frozen=True)
class RoleProfileValidationV1:
    role_profile: str
    valid: bool
    reasons: tuple[str, ...]
    scaffold_count: int | None
    linker_count: int | None
    warhead_count: int | None
    scaffold_linker_boundary_applicable: bool
    linker_warhead_boundary_applicable: bool
    direct_scaffold_warhead_boundary_applicable: bool
    direct_scaffold_warhead_boundary: DirectScaffoldWarheadBoundaryV1 | None


@dataclass(frozen=True)
class MinimalSeedValidationV1:
    role_profile: str
    valid: bool
    reasons: tuple[str, ...]
    primary_anchor_atom_id: _AtomId | None


@dataclass(frozen=True)
class DirectReviewRoleValidationV1:
    valid: bool
    reasons: tuple[str, ...]
    review_signature_bound: bool
    reusable_scope_applicability_signatures_valid: bool
    role_validation: RoleProfileValidationV1 | None
    seed_validation: MinimalSeedValidationV1 | None


@dataclass(frozen=True)
class LightningStructuralCompatibilityV1:
    valid: bool
    reasons: tuple[str, ...]
    generated_count: int
    fixed_count: int


class _RuntimeInvariantError(Exception):
    pass


def _fail() -> NoReturn:
    raise _RuntimeInvariantError()


def _append_unique(reasons: list[str], *new_reasons: str) -> None:
    for reason in new_reasons:
        if reason and reason not in reasons:
            reasons.append(reason)


def _valid_atom_id(value: object) -> bool:
    return (
        (type(value) is int and value >= 0)
        or (
            type(value) is str
            and bool(value)
            and value.strip() == value
        )
    )


def _atom_sequence(
    value: object, *, name: str
) -> tuple[tuple[_AtomId, ...] | None, tuple[str, ...]]:
    if type(value) not in (tuple, list, range):
        return None, (f"{name}_container_invalid",)
    values = tuple(value)
    if any(not _valid_atom_id(atom) for atom in values):
        return None, (f"{name}_atom_id_invalid",)
    if len(values) != len(set(values)):
        return None, (f"{name}_duplicate_atom_id",)
    return values, ()  # type: ignore[return-value]


def _ordinal_mapping(*groups: Sequence[_AtomId]) -> dict[_AtomId, int]:
    mapping: dict[_AtomId, int] = {}
    for group in groups:
        for atom in group:
            if atom not in mapping:
                mapping[atom] = len(mapping)
    return mapping


def _published_partition_reasons(
    retained: tuple[_AtomId, ...],
    scaffold: tuple[_AtomId, ...],
    linker: tuple[_AtomId, ...],
    warhead: tuple[_AtomId, ...],
    hydrogens: tuple[_AtomId, ...],
) -> tuple[str, ...]:
    if all(
        type(atom) is int
        for group in (retained, scaffold, linker, warhead, hydrogens)
        for atom in group
    ):
        return published_role_contract.validate_exact3_partition(
            retained,  # type: ignore[arg-type]
            scaffold,  # type: ignore[arg-type]
            linker,  # type: ignore[arg-type]
            warhead,  # type: ignore[arg-type]
            hydrogen_atoms=hydrogens,  # type: ignore[arg-type]
        )
    mapping = _ordinal_mapping(
        retained, scaffold, linker, warhead, hydrogens
    )
    return published_role_contract.validate_exact3_partition(
        tuple(mapping[atom] for atom in retained),
        tuple(mapping[atom] for atom in scaffold),
        tuple(mapping[atom] for atom in linker),
        tuple(mapping[atom] for atom in warhead),
        hydrogen_atoms=tuple(mapping[atom] for atom in hydrogens),
    )


def _profile(value: object) -> str:
    if type(value) is not str or value not in ROLE_PROFILES_V1:
        raise ValueError(RUNTIME_ERROR)
    return value


def valid_canonical_task_ids_for_role_profile_v1(
    role_profile: object,
) -> tuple[int, ...]:
    """Return the canonical task IDs that are applicable to one profile."""

    profile = _profile(role_profile)
    if profile == STRICT_LINKER_PRESENT_V1:
        return STRICT_VALID_CANONICAL_TASK_IDS_V1
    return DIRECT_VALID_CANONICAL_TASK_IDS_V1


def canonical_task_id_for_valid_task_set_v1(
    *,
    sample_identity: object,
    epoch: object,
    task_schedule_seed: object,
    valid_task_ids: object,
) -> int:
    """Cycle directly over a recognized valid set with a separated domain."""

    try:
        if type(valid_task_ids) not in (tuple, list):
            _fail()
        tasks = tuple(valid_task_ids)
        if tasks == STRICT_VALID_CANONICAL_TASK_IDS_V1:
            profile = STRICT_LINKER_PRESENT_V1
        elif tasks == DIRECT_VALID_CANONICAL_TASK_IDS_V1:
            profile = DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1
        else:
            _fail()
        if (
            type(sample_identity) is not str
            or not sample_identity
            or sample_identity.strip() != sample_identity
            or type(epoch) is not int
            or epoch < 0
            or type(task_schedule_seed) is not int
            or not 0 <= task_schedule_seed <= 2**63 - 1
        ):
            _fail()
        identity = sample_identity.encode("utf-8")
        payload = (
            SCHEDULE_DOMAINS_BY_ROLE_PROFILE_V1[profile]
            + str(task_schedule_seed).encode("ascii")
            + b"\0"
            + identity
        )
        phase = int.from_bytes(
            hashlib.sha256(payload).digest()[:8],
            byteorder="big",
            signed=False,
        ) % len(tasks)
        return tasks[(phase + epoch) % len(tasks)]
    except (UnicodeEncodeError, _RuntimeInvariantError) as error:
        raise ValueError(RUNTIME_ERROR) from error


def canonical_task_id_for_role_profile_v1(
    *,
    role_profile: object,
    sample_identity: object,
    epoch: object,
    task_schedule_seed: object,
) -> int:
    return canonical_task_id_for_valid_task_set_v1(
        sample_identity=sample_identity,
        epoch=epoch,
        task_schedule_seed=task_schedule_seed,
        valid_task_ids=valid_canonical_task_ids_for_role_profile_v1(
            role_profile
        ),
    )


def validate_role_partition_for_profile_v1(
    *,
    role_profile: object,
    retained_heavy_atoms: object,
    scaffold_atoms: object,
    linker_atoms: object,
    warhead_atoms: object,
    hydrogen_atoms: object = (),
) -> RolePartitionValidationV1:
    """Validate Exact3 partition semantics, delegating to the V1 owner."""

    profile = _profile(role_profile)
    reasons: list[str] = []
    normalized: list[tuple[_AtomId, ...]] = []
    for name, value in (
        ("retained_heavy_atoms", retained_heavy_atoms),
        ("scaffold_atoms", scaffold_atoms),
        ("linker_atoms", linker_atoms),
        ("warhead_atoms", warhead_atoms),
        ("hydrogen_atoms", hydrogen_atoms),
    ):
        values, diagnostics = _atom_sequence(value, name=name)
        _append_unique(reasons, *diagnostics)
        if values is not None:
            normalized.append(values)
    if reasons:
        return RolePartitionValidationV1(
            role_profile=profile,
            valid=False,
            reasons=tuple(reasons),
            scaffold_count=None,
            linker_count=None,
            warhead_count=None,
        )
    retained, scaffold, linker, warhead, hydrogens = normalized
    published_reasons = list(
        _published_partition_reasons(
            retained, scaffold, linker, warhead, hydrogens
        )
    )
    if profile == DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1:
        published_reasons = [
            reason for reason in published_reasons if reason != "linker_empty"
        ]
        if linker:
            published_reasons.append("linker_not_empty")
    return RolePartitionValidationV1(
        role_profile=profile,
        valid=not published_reasons,
        reasons=tuple(published_reasons),
        scaffold_count=len(scaffold),
        linker_count=len(linker),
        warhead_count=len(warhead),
    )


def _normalize_explicit_bonds(
    value: object,
) -> tuple[tuple[ExplicitBondV1, ...], tuple[str, ...]]:
    if type(value) not in (tuple, list):
        return (), ("explicit_graph_bonds_container_invalid",)
    bonds: list[ExplicitBondV1] = []
    reasons: list[str] = []
    seen_pairs: set[frozenset[_AtomId]] = set()
    for raw_bond in value:
        if type(raw_bond) is ExplicitBondV1:
            bond = raw_bond
        elif type(raw_bond) is tuple and len(raw_bond) == 3:
            bond = ExplicitBondV1(*raw_bond)
        else:
            _append_unique(reasons, "explicit_graph_bond_invalid")
            continue
        if (
            not _valid_atom_id(bond.atom_id_1)
            or not _valid_atom_id(bond.atom_id_2)
            or bond.atom_id_1 == bond.atom_id_2
            or type(bond.bond_order) is not str
            or not bond.bond_order
            or bond.bond_order.strip() != bond.bond_order
        ):
            _append_unique(reasons, "explicit_graph_bond_invalid")
            continue
        pair = frozenset((bond.atom_id_1, bond.atom_id_2))
        if pair in seen_pairs:
            _append_unique(reasons, "explicit_graph_duplicate_or_parallel_bond")
            continue
        seen_pairs.add(pair)
        bonds.append(bond)
    return tuple(bonds), tuple(reasons)


def _normalize_direct_boundaries(
    value: object,
) -> tuple[tuple[tuple[_AtomId, _AtomId, str], ...], tuple[str, ...]]:
    if type(value) not in (tuple, list):
        return (), ("direct_boundaries_container_invalid",)
    boundaries: list[tuple[_AtomId, _AtomId, str]] = []
    reasons: list[str] = []
    for boundary in value:
        if type(boundary) is not tuple or len(boundary) != 3:
            _append_unique(reasons, "direct_boundary_evidence_invalid")
            continue
        scaffold_atom, warhead_atom, bond_order = boundary
        if (
            not _valid_atom_id(scaffold_atom)
            or not _valid_atom_id(warhead_atom)
            or scaffold_atom == warhead_atom
            or type(bond_order) is not str
            or not bond_order
            or bond_order.strip() != bond_order
        ):
            _append_unique(reasons, "direct_boundary_evidence_invalid")
            continue
        boundaries.append((scaffold_atom, warhead_atom, bond_order))
    return tuple(boundaries), tuple(reasons)


def _bond_key(
    atom_1: _AtomId, atom_2: _AtomId, bond_order: str
) -> tuple[frozenset[_AtomId], str]:
    return frozenset((atom_1, atom_2)), bond_order


def validate_role_profile_v1(
    *,
    role_profile: object,
    retained_heavy_atoms: object,
    scaffold_atoms: object,
    linker_atoms: object,
    warhead_atoms: object,
    reactive_atom_id: object = None,
    direct_scaffold_warhead_boundaries: object = (),
    explicit_graph_bonds: object = (),
) -> RoleProfileValidationV1:
    """Validate one strict or direct-attachment role/topology profile."""

    profile = _profile(role_profile)
    partition = validate_role_partition_for_profile_v1(
        role_profile=profile,
        retained_heavy_atoms=retained_heavy_atoms,
        scaffold_atoms=scaffold_atoms,
        linker_atoms=linker_atoms,
        warhead_atoms=warhead_atoms,
    )
    if profile == STRICT_LINKER_PRESENT_V1:
        return RoleProfileValidationV1(
            role_profile=profile,
            valid=partition.valid,
            reasons=partition.reasons,
            scaffold_count=partition.scaffold_count,
            linker_count=partition.linker_count,
            warhead_count=partition.warhead_count,
            scaffold_linker_boundary_applicable=True,
            linker_warhead_boundary_applicable=True,
            direct_scaffold_warhead_boundary_applicable=False,
            direct_scaffold_warhead_boundary=None,
        )

    reasons = list(partition.reasons)
    scaffold, scaffold_diagnostics = _atom_sequence(
        scaffold_atoms, name="scaffold_atoms"
    )
    warhead, warhead_diagnostics = _atom_sequence(
        warhead_atoms, name="warhead_atoms"
    )
    _append_unique(reasons, *scaffold_diagnostics, *warhead_diagnostics)
    scaffold_set = set(scaffold or ())
    warhead_set = set(warhead or ())
    if not _valid_atom_id(reactive_atom_id):
        _append_unique(reasons, "reactive_atom_id_invalid")
    elif reactive_atom_id not in warhead_set:
        _append_unique(reasons, "reactive_atom_outside_warhead")

    bonds, bond_diagnostics = _normalize_explicit_bonds(explicit_graph_bonds)
    boundaries, boundary_diagnostics = _normalize_direct_boundaries(
        direct_scaffold_warhead_boundaries
    )
    _append_unique(reasons, *bond_diagnostics, *boundary_diagnostics)

    graph_boundaries: list[tuple[_AtomId, _AtomId, str]] = []
    for bond in bonds:
        if bond.atom_id_1 in scaffold_set and bond.atom_id_2 in warhead_set:
            graph_boundaries.append(
                (bond.atom_id_1, bond.atom_id_2, bond.bond_order)
            )
        elif bond.atom_id_2 in scaffold_set and bond.atom_id_1 in warhead_set:
            graph_boundaries.append(
                (bond.atom_id_2, bond.atom_id_1, bond.bond_order)
            )

    if len(boundaries) == 0:
        _append_unique(reasons, "direct_boundary_missing")
    elif len(boundaries) > 1:
        _append_unique(reasons, "multiple_direct_boundaries")
    if len(graph_boundaries) == 0:
        _append_unique(reasons, "direct_boundary_missing_from_explicit_graph")
    elif len(graph_boundaries) > 1:
        _append_unique(reasons, "multiple_direct_boundaries_in_explicit_graph")

    boundary_result: DirectScaffoldWarheadBoundaryV1 | None = None
    if len(boundaries) == 1:
        scaffold_atom, warhead_atom, bond_order = boundaries[0]
        role_sides_valid = (
            scaffold_atom in scaffold_set and warhead_atom in warhead_set
        )
        if not role_sides_valid:
            _append_unique(reasons, "direct_boundary_role_sides_inconsistent")
        graph_keys = {
            _bond_key(bond.atom_id_1, bond.atom_id_2, bond.bond_order)
            for bond in bonds
        }
        graph_member = (
            _bond_key(scaffold_atom, warhead_atom, bond_order) in graph_keys
        )
        if not graph_member:
            _append_unique(
                reasons, "direct_boundary_bond_absent_from_explicit_graph"
            )
        unique_graph_boundary_matches = (
            len(graph_boundaries) == 1
            and graph_boundaries[0]
            == (scaffold_atom, warhead_atom, bond_order)
        )
        boundary_result = DirectScaffoldWarheadBoundaryV1(
            scaffold_atom_id=scaffold_atom,
            warhead_atom_id=warhead_atom,
            bond_order=bond_order,
            boundary_valid=(
                role_sides_valid
                and graph_member
                and unique_graph_boundary_matches
            ),
        )

    return RoleProfileValidationV1(
        role_profile=profile,
        valid=not reasons,
        reasons=tuple(reasons),
        scaffold_count=partition.scaffold_count,
        linker_count=partition.linker_count,
        warhead_count=partition.warhead_count,
        scaffold_linker_boundary_applicable=False,
        linker_warhead_boundary_applicable=False,
        direct_scaffold_warhead_boundary_applicable=True,
        direct_scaffold_warhead_boundary=boundary_result,
    )


def _task_row(task_id: int) -> tuple[Any, ...]:
    matches = tuple(row for row in CANONICAL_TASKS_V1 if row[0] == task_id)
    if len(matches) != 1:
        raise ValueError(RUNTIME_ERROR)
    return matches[0]


def build_mask_for_role_profile_v1(
    *,
    role_profile: object,
    canonical_task_id: object,
    scaffold_atoms: object,
    linker_atoms: object,
    warhead_atoms: object,
    num_ligand_atoms: object,
) -> MaskResult:
    """Build a strict mask or one of the three direct-profile masks."""

    profile = _profile(role_profile)
    if type(canonical_task_id) is not int:
        raise ValueError(RUNTIME_ERROR)
    valid_tasks = valid_canonical_task_ids_for_role_profile_v1(profile)
    if canonical_task_id not in valid_tasks:
        raise ValueError(f"{RUNTIME_ERROR}:TASK_NOT_APPLICABLE")
    if type(num_ligand_atoms) is not int or num_ligand_atoms <= 0:
        raise ValueError(RUNTIME_ERROR)
    partition = validate_role_partition_for_profile_v1(
        role_profile=profile,
        retained_heavy_atoms=range(num_ligand_atoms),
        scaffold_atoms=scaffold_atoms,
        linker_atoms=linker_atoms,
        warhead_atoms=warhead_atoms,
    )
    if not partition.valid:
        raise ValueError(
            f"{RUNTIME_ERROR}:ROLE_PARTITION_INVALID:"
            + ";".join(partition.reasons)
        )
    task_row = _task_row(canonical_task_id)
    semantic_name = task_row[1]
    if profile == STRICT_LINKER_PRESENT_V1:
        return masking.build_canonical_mask(
            mask_semantic=semantic_name,
            scaffold_atoms=scaffold_atoms,  # type: ignore[arg-type]
            linker_atoms=linker_atoms,  # type: ignore[arg-type]
            warhead_atoms=warhead_atoms,  # type: ignore[arg-type]
            num_ligand_atoms=num_ligand_atoms,
        )
    visible_by_task = {
        0: scaffold_atoms,
        3: warhead_atoms,
        4: (),
    }
    mask_level = masking.resolve_canonical_mask_semantic(semantic_name)
    return masking.make_mask_result(
        mask_level,
        visible_by_task[canonical_task_id],  # type: ignore[arg-type]
        num_ligand_atoms,
    )


def validate_minimal_seed_for_role_profile_v1(
    *,
    role_profile: object,
    seed_atoms: object,
    scaffold_atoms: object,
    linker_atoms: object,
    warhead_atoms: object,
    explicit_graph_bonds: object,
    primary_anchor_atom_id: object = None,
    direct_boundary: object = None,
) -> MinimalSeedValidationV1:
    """Validate the published 2/3-node connected scaffold seed invariant."""

    profile = _profile(role_profile)
    reasons: list[str] = []
    normalized: list[tuple[_AtomId, ...]] = []
    for name, value in (
        ("seed_atoms", seed_atoms),
        ("scaffold_atoms", scaffold_atoms),
        ("linker_atoms", linker_atoms),
        ("warhead_atoms", warhead_atoms),
    ):
        atoms, diagnostics = _atom_sequence(value, name=name)
        _append_unique(reasons, *diagnostics)
        if atoms is not None:
            normalized.append(atoms)
    bonds, bond_diagnostics = _normalize_explicit_bonds(explicit_graph_bonds)
    _append_unique(reasons, *bond_diagnostics)
    if reasons:
        return MinimalSeedValidationV1(profile, False, tuple(reasons), None)
    seed, scaffold, linker, warhead = normalized

    anchor: _AtomId | None
    if profile == DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1:
        if linker:
            _append_unique(reasons, "linker_not_empty")
        if type(direct_boundary) is not DirectScaffoldWarheadBoundaryV1:
            _append_unique(reasons, "direct_seed_boundary_missing_or_invalid")
            anchor = None
        else:
            anchor = direct_boundary.scaffold_atom_id
            if (
                direct_boundary.boundary_valid is not True
                or anchor not in set(scaffold)
                or direct_boundary.warhead_atom_id not in set(warhead)
            ):
                _append_unique(reasons, "direct_seed_boundary_missing_or_invalid")
            graph_keys = {
                _bond_key(bond.atom_id_1, bond.atom_id_2, bond.bond_order)
                for bond in bonds
            }
            if (
                _bond_key(
                    direct_boundary.scaffold_atom_id,
                    direct_boundary.warhead_atom_id,
                    direct_boundary.bond_order,
                )
                not in graph_keys
            ):
                _append_unique(reasons, "direct_seed_boundary_missing_or_invalid")
    else:
        if not _valid_atom_id(primary_anchor_atom_id):
            _append_unique(reasons, "primary_anchor_atom_id_invalid")
            anchor = None
        else:
            anchor = primary_anchor_atom_id  # type: ignore[assignment]

    if anchor is not None:
        mapping = _ordinal_mapping(
            scaffold, linker, warhead, seed, (anchor,)
        )
        scaffold_edges = tuple(
            (mapping[bond.atom_id_1], mapping[bond.atom_id_2])
            for bond in bonds
            if bond.atom_id_1 in set(scaffold)
            and bond.atom_id_2 in set(scaffold)
        )
        seed_reasons = published_role_contract.validate_minimal_seed(
            tuple(mapping[atom] for atom in seed),
            tuple(mapping[atom] for atom in scaffold),
            tuple(mapping[atom] for atom in linker),
            tuple(mapping[atom] for atom in warhead),
            scaffold_edges,
            mapping[anchor],
        )
        _append_unique(reasons, *seed_reasons)
    return MinimalSeedValidationV1(
        role_profile=profile,
        valid=not reasons,
        reasons=tuple(reasons),
        primary_anchor_atom_id=anchor,
    )


def _review_inventory(value: object) -> tuple[_AtomId, ...] | None:
    if type(value) is not list:
        return None
    atoms: list[_AtomId] = []
    for row in value:
        if not isinstance(row, Mapping) or not _valid_atom_id(row.get("atom_id")):
            return None
        atoms.append(row["atom_id"])  # type: ignore[arg-type]
    if len(atoms) != len(set(atoms)):
        return None
    return tuple(atoms)


def _review_bonds(value: object) -> tuple[ExplicitBondV1, ...] | None:
    if type(value) is not list:
        return None
    bonds: list[ExplicitBondV1] = []
    for row in value:
        if not isinstance(row, Mapping):
            return None
        bonds.append(
            ExplicitBondV1(
                atom_id_1=row.get("atom_id_1"),  # type: ignore[arg-type]
                atom_id_2=row.get("atom_id_2"),  # type: ignore[arg-type]
                bond_order=row.get("bond_order"),  # type: ignore[arg-type]
            )
        )
    _, diagnostics = _normalize_explicit_bonds(bonds)
    if diagnostics:
        return None
    return tuple(bonds)


def validate_direct_attachment_review_role_payload_v1(
    *,
    review_record: object,
    chemistry_review_signature: object,
    expected_review_signature_sha256: object,
    applicability_signatures: object = (),
) -> DirectReviewRoleValidationV1:
    """Validate only future direct ROLE/BORDER/SEED review fields.

    The caller supplies the frozen signature binding.  This helper neither
    validates a completed authority record as a whole nor creates authority.
    """

    reasons: list[str] = []
    signature_bound = False
    applicability_valid = False
    if not isinstance(review_record, Mapping):
        _append_unique(reasons, "review_record_mapping_invalid")
    if not isinstance(chemistry_review_signature, Mapping):
        _append_unique(reasons, "chemistry_review_signature_mapping_invalid")
    if (
        type(expected_review_signature_sha256) is not str
        or _SHA256.fullmatch(expected_review_signature_sha256) is None
    ):
        _append_unique(reasons, "expected_review_signature_sha256_invalid")
    if reasons:
        return DirectReviewRoleValidationV1(
            False, tuple(reasons), False, False, None, None
        )
    record = review_record
    signature = chemistry_review_signature
    record_signature_matches = (
        record.get("chemistry_review_signature_sha256")
        == expected_review_signature_sha256
    )
    if not record_signature_matches:
        _append_unique(reasons, "review_signature_binding_mismatch")
    try:
        content_signature_matches = (
            published_review_packages.chemistry_review_signature_sha256_v1(
                signature
            )
            == expected_review_signature_sha256
        )
    except (TypeError, ValueError):
        content_signature_matches = False
    if not content_signature_matches:
        _append_unique(
            reasons, "chemistry_review_signature_content_sha256_mismatch"
        )
    signature_bound = record_signature_matches and content_signature_matches

    review_scope = record.get("review_scope")
    if review_scope == "EXACT_CHEMISTRY_SIGNATURE_REUSABLE":
        if type(applicability_signatures) not in (tuple, list) or any(
            type(value) is not str for value in applicability_signatures
        ):
            _append_unique(reasons, "applicability_signatures_invalid")
        elif not applicability_signatures:
            _append_unique(
                reasons, "reusable_scope_applicability_signatures_missing"
            )
        elif any(
            value != expected_review_signature_sha256
            for value in applicability_signatures
        ):
            _append_unique(reasons, "reusable_scope_signature_mismatch")
        else:
            applicability_valid = True
    elif review_scope == "SAMPLE_BOUND_ONLY":
        # For this bounded result field, True means the selected scope's
        # applicability condition is satisfied; sample-bound scope needs no
        # cross-sample signature list.
        applicability_valid = True
    else:
        _append_unique(reasons, "direct_review_role_scope_invalid")

    retained = _review_inventory(
        signature.get("canonical_model_bound_ligand_heavy_atom_inventory")
    )
    bonds = _review_bonds(
        signature.get(
            "canonical_internal_heavy_heavy_bond_graph_with_bond_orders"
        )
    )
    reactive_atom = signature.get("reactive_ligand_atom")
    if retained is None:
        _append_unique(reasons, "review_retained_inventory_invalid")
    if bonds is None:
        _append_unique(reasons, "review_explicit_graph_invalid")
    required_record_fields = (
        "reviewed_scaffold_atom_ids",
        "reviewed_linker_atom_ids",
        "reviewed_warhead_role_atom_ids",
        "reviewed_minimal_seed_atom_ids",
        "reviewed_warhead_attachment_atom_id",
        "reviewed_nonwarhead_boundary_atom_id",
        "reviewed_attachment_boundary_bond_order",
    )
    for field in required_record_fields:
        if field not in record:
            _append_unique(reasons, f"review_field_missing:{field}")
    if retained is None or bonds is None or any(
        field not in record for field in required_record_fields
    ):
        return DirectReviewRoleValidationV1(
            False,
            tuple(reasons),
            signature_bound,
            applicability_valid,
            None,
            None,
        )

    boundary = (
        record["reviewed_nonwarhead_boundary_atom_id"],
        record["reviewed_warhead_attachment_atom_id"],
        record["reviewed_attachment_boundary_bond_order"],
    )
    role_validation = validate_role_profile_v1(
        role_profile=DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1,
        retained_heavy_atoms=retained,
        scaffold_atoms=record["reviewed_scaffold_atom_ids"],
        linker_atoms=record["reviewed_linker_atom_ids"],
        warhead_atoms=record["reviewed_warhead_role_atom_ids"],
        reactive_atom_id=reactive_atom,
        direct_scaffold_warhead_boundaries=(boundary,),
        explicit_graph_bonds=bonds,
    )
    _append_unique(reasons, *role_validation.reasons)
    seed_validation: MinimalSeedValidationV1 | None = None
    if role_validation.direct_scaffold_warhead_boundary is not None:
        seed_validation = validate_minimal_seed_for_role_profile_v1(
            role_profile=DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1,
            seed_atoms=record["reviewed_minimal_seed_atom_ids"],
            scaffold_atoms=record["reviewed_scaffold_atom_ids"],
            linker_atoms=record["reviewed_linker_atom_ids"],
            warhead_atoms=record["reviewed_warhead_role_atom_ids"],
            explicit_graph_bonds=bonds,
            direct_boundary=role_validation.direct_scaffold_warhead_boundary,
        )
        _append_unique(reasons, *seed_validation.reasons)
    else:
        _append_unique(reasons, "direct_seed_boundary_missing_or_invalid")
    return DirectReviewRoleValidationV1(
        valid=not reasons,
        reasons=tuple(reasons),
        review_signature_bound=signature_bound,
        reusable_scope_applicability_signatures_valid=applicability_valid,
        role_validation=role_validation,
        seed_validation=seed_validation,
    )


def validate_current_lightning_structural_expectations_v1(
    *,
    role_profile: object,
    canonical_task_id: object,
    ligand_role_ids: object,
    mask_result: object,
) -> LightningStructuralCompatibilityV1:
    """Probe the mask invariants consumed by the current Lightning bridge."""

    profile = _profile(role_profile)
    reasons: list[str] = []
    if type(canonical_task_id) is not int or canonical_task_id not in (
        valid_canonical_task_ids_for_role_profile_v1(profile)
    ):
        _append_unique(reasons, "canonical_task_not_applicable")
    roles: tuple[int, ...] = ()
    if type(ligand_role_ids) not in (tuple, list) or any(
        type(role) is not int or role not in CANONICAL_ROLE_IDS_V1
        for role in ligand_role_ids
    ):
        _append_unique(reasons, "ligand_role_ids_invalid")
    else:
        roles = tuple(ligand_role_ids)
        expected_roles = (
            {0, 1, 2}
            if profile == STRICT_LINKER_PRESENT_V1
            else {0, 2}
        )
        if set(roles) != expected_roles:
            _append_unique(reasons, "role_profile_node_roles_invalid")
    if type(mask_result) is not MaskResult:
        _append_unique(reasons, "mask_result_invalid")
        return LightningStructuralCompatibilityV1(
            False, tuple(reasons), 0, 0
        )
    generated = mask_result.masked_atoms
    fixed = mask_result.visible_atoms
    if len(roles) != len(generated) + len(fixed):
        _append_unique(reasons, "mask_role_length_mismatch")
    if not generated:
        _append_unique(reasons, "generated_region_empty")
    if canonical_task_id != 4 and not fixed:
        _append_unique(reasons, "non_C_fixed_region_empty")
    if canonical_task_id == 4 and fixed:
        _append_unique(reasons, "C_fixed_region_not_empty")
    if not reasons or all(
        reason
        not in (
            "canonical_task_not_applicable",
            "ligand_role_ids_invalid",
            "mask_role_length_mismatch",
        )
        for reason in reasons
    ):
        if type(canonical_task_id) is int and canonical_task_id in range(5):
            target_role_names = set(_task_row(canonical_task_id)[3])
            role_id_by_name = dict(zip(CANONICAL_ROLE_NAMES_V1, (0, 1, 2)))
            target_role_ids = {
                role_id_by_name[name] for name in target_role_names
            }
            expected_generated = tuple(
                index
                for index, role_id in enumerate(roles)
                if role_id in target_role_ids
            )
            if generated != expected_generated:
                _append_unique(reasons, "generation_mask_task_role_mismatch")
    expected_fixed_values = tuple(
        1 if index in set(fixed) else 0 for index in range(len(roles))
    )
    try:
        observed_fixed_values = tuple(
            int(value) for value in mask_result.lig_fixed.tolist()
        )
    except (AttributeError, TypeError, ValueError):
        observed_fixed_values = ()
    if observed_fixed_values != expected_fixed_values:
        _append_unique(reasons, "lig_fixed_mask_mismatch")
    return LightningStructuralCompatibilityV1(
        valid=not reasons,
        reasons=tuple(reasons),
        generated_count=len(generated),
        fixed_count=len(fixed),
    )


def runtime_readiness_v1() -> dict[str, bool]:
    """Return the bounded successor-runtime readiness boundary."""

    return {
        "direct_attachment_optional_linker_runtime_implemented": True,
        "direct_attachment_role_profile_supported": True,
        "direct_attachment_task_applicability_supported": True,
        "direct_attachment_direct_boundary_supported": True,
        "direct_attachment_seed_semantics_supported": True,
        "direct_attachment_review_role_validation_supported": True,
        "current11_tensorizer_direct_profile_supported": (
            CURRENT11_TENSORIZER_DIRECT_PROFILE_SUPPORTED_V1
        ),
        "direct_profile_runtime_primitives_ready": (
            DIRECT_PROFILE_RUNTIME_PRIMITIVES_READY_V1
        ),
        "expanded_tensorizer_integration_pending": (
            EXPANDED_TENSORIZER_INTEGRATION_PENDING_V1
        ),
        "model_architecture_change_required": (
            MODEL_ARCHITECTURE_CHANGE_REQUIRED_V1
        ),
    }
