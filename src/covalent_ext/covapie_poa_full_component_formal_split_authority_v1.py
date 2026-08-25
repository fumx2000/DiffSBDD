"""Create the POA full-component formal split authority, V1.

This owner binds the committed 24-event/3-identity leakage component, rebuilds
the current 14 frozen leakage groups from their published owners, and applies
the generic additive split policy with an independent one-group oracle.  A
formal split is only a leakage reservation: this module never admits a sample
to training and never activates model training.
"""

from __future__ import annotations

from collections import Counter, deque
from collections.abc import Mapping, Sequence
import csv
from dataclasses import dataclass, fields
from fractions import Fraction
import hashlib
import io
import json
from itertools import product
from pathlib import Path
import re
from types import SimpleNamespace
from typing import Any, NoReturn

from covalent_ext import covapie_bulk_cys_sg_dataset_expansion_v1 as bulk_owner
from covalent_ext import covapie_cys_sg_dataset_expansion_pipeline_v1 as split_owner


__all__ = (
    "COVAPIE_POA_FULL_COMPONENT_FORMAL_SPLIT_AUTHORITY_V1_ERROR",
    "POA_CANONICAL_EVENT_INVENTORY_SHA256_V1",
    "POA_FROZEN14_INVENTORY_SHA256_V1",
    "POAFullComponentFormalSplitSourceBindingV1",
    "POAFullComponentFormalSplitRecordV1",
    "POAFullComponentFormalSplitSummaryV1",
    "POAFullComponentFormalSplitOracleV1",
    "POAFullComponentFormalSplitAuthorityResultV1",
    "build_covapie_poa_full_component_formal_split_authority_v1",
    "validate_covapie_poa_full_component_formal_split_authority_v1",
)


COVAPIE_POA_FULL_COMPONENT_FORMAL_SPLIT_AUTHORITY_V1_ERROR = (
    "COVAPIE_POA_FULL_COMPONENT_FORMAL_SPLIT_AUTHORITY_V1_ERROR"
)

POA_CLASSIFICATION_V1 = "NEW_EXPANSION_COMPONENT"
POA_LEAKAGE_KEY_V1 = (
    "COVAPIE_BULK_READ_ONLY_COMPONENT_V1:"
    "15b5453e3ecb325bb4573a66a06174c23e66b0128f0767036d329a9720473b4d"
)
POA_FORMAL_GROUP_ID_V1 = "COVAPIE_EXPANSION_LEAKAGE_GROUP_F70DB37A8004AF17"
POA_READ_ONLY_PREDICTED_SPLIT_V1 = "train"
POA_FORMAL_SPLIT_V1 = "train"
POA_IDENTITIES_V1 = ("4I3U/POA", "4I3V/POA", "4I3W/G3H")
POA_LINKING_AXES_V1 = (
    "LIGAND_GRAPH",
    "PROTEIN_ACCESSION",
    "PROTEIN_EXACT_SEQUENCE",
    "PROTEIN_SEQUENCE_IDENTITY_GE_0.5",
)
POA_CANONICAL_EVENT_INVENTORY_SHA256_V1 = (
    "71403d2f65a6bbabfe3cca620a0b397a0947648331bc3c4c947dbff93128e049"
)
POA_FROZEN14_INVENTORY_SHA256_V1 = (
    "d10efe9c95b85aea4215de68b88df4094d021a06b7b08dd83c116b2c08842a4d"
)

_SPLITS_V1 = ("train", "validation", "test")
_RANK_V1 = {name: index for index, name in enumerate(_SPLITS_V1)}
_TARGET_V1 = {
    "train": Fraction(7, 10),
    "validation": Fraction(3, 20),
    "test": Fraction(3, 20),
}
_IDENTITY_V1 = re.compile(
    r"^[A-Z0-9][A-Z0-9_.:-]*/[A-Z0-9][A-Z0-9_.:-]*$"
)
_EVENT_ID_V1 = re.compile(
    r"^COVAPIE_CYS_SG_EVENT_V1:(?P<pdb>[^:]+):[^:]+:CYS:[^:]+:SG:"
    r"[^:]+:(?P<ligand>[^:]+):[^:]+$"
)

_PROCESSING_VIEW_V1 = (
    "data/derived/covalent_small/"
    "covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1/"
    "covapie_bulk_cys_sg_ranks_0501_1000_processing_outcomes_v1.json"
)
_BASELINE_GROUP_MEMBERS_V1 = (
    "data/derived/covalent_small/"
    "covapie_unified_independence_group_assignment_and_sample_index_merge_"
    "smoke_v0/covapie_final_leakage_group_assignment.csv"
)
_BASELINE_GROUP_SPLITS_V1 = (
    "data/derived/covalent_small/"
    "covapie_unified_leakage_split_materialization_smoke_v0/"
    "covapie_leakage_group_split_assignment.csv"
)
_CUMULATIVE_REGISTRY_V1 = (
    "data/derived/covalent_small/"
    "covapie_cys_sg_dataset_expansion_pipeline_v1/6di9_gjj_approved_v1/"
    "cumulative_leakage_registry_v1.json"
)
_BATCH001_COMPONENTS_V1 = (
    "data/derived/covalent_small/"
    "covapie_batch001_formal_split_leakage_admission_v1/"
    "covapie_batch001_formal_leakage_component_registry_v1.json"
)
_NDU_COMPONENT_V1 = (
    "data/derived/covalent_small/"
    "covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_v1/"
    "covapie_batch001_ndu4_full_component_registry_v1.json"
)
_EXISTING_POSITIVE_CLOSURE_V1 = (
    "data/derived/covalent_small/"
    "covapie_existing_positive_runtime_and_split_closure_v1/"
    "covapie_existing_positive_leakage_split_closure_inventory_v1.csv"
)
_BULK_PROCESSING_V1 = (
    "data/derived/covalent_small/"
    "covapie_bulk_cys_sg_dataset_expansion_v1/bulk_pilot_v1/"
    "bulk_processing_outcomes_v1.json"
)
_MISSING_SEQUENCE_EVIDENCE_V1 = (
    "data/derived/covalent_small/"
    "covapie_poa_full_component_formal_split_authority_v1/"
    "covapie_poa_missing_frozen_component_protein_sequence_evidence_v1.json"
)

_SOURCE_SPECS_V1 = (
    (
        "POA_FULL_COMPONENT_PROCESSING_VIEW",
        _PROCESSING_VIEW_V1,
        "4f5ee75a645ee560cb8e272fd3ead8ba7a446dadf9aece38f12f0eeecad16e5f",
    ),
    (
        "HISTORICAL_EXACT5_GROUP_MEMBERS",
        _BASELINE_GROUP_MEMBERS_V1,
        "768c964f22e19a8fb6232b1fa26c531e53d023042abcd9b1bcca44df2b4f4416",
    ),
    (
        "HISTORICAL_EXACT5_SPLIT_POLICY",
        _BASELINE_GROUP_SPLITS_V1,
        "ed62fcf56ad87d8a49743517329c97aa98d3a781562fa403b4b43a9b9ea3ffc3",
    ),
    (
        "CUMULATIVE_EXPANSION_GROUP_REGISTRY",
        _CUMULATIVE_REGISTRY_V1,
        "24a58a6f9cc551c9b38527c1bfbf64aa2661bf1173b8eabcb44428513bfe15c8",
    ),
    (
        "CUMULATIVE_SUCCESSOR_PIPELINE_RUN",
        "data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/"
        "6di9_gjj_approved_v1/pipeline_run_v1.json",
        "bd68d9f20fdb99882520c5cdb82e452a52633b09869fac0e727ebba733638dd8",
    ),
    (
        "CUMULATIVE_SUCCESSOR_MATERIALIZED_SAMPLE",
        "data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/"
        "6di9_gjj_approved_v1/samples/8483b1e83aa8e1b6.materialized.json",
        "254b76c7c9da09d559adbb59489b39ed39d95934d34362dfe53cecbee28ed6bd",
    ),
    (
        "CUMULATIVE_PUBLISHED_PIPELINE_RUN",
        "data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/"
        "5f2e_5ut_approved_v1/pipeline_run_v1.json",
        "8f56116f02709caf2ecbbad59479dce7772c3fb83fd9aef59a7ff9f6b8233980",
    ),
    (
        "CUMULATIVE_PUBLISHED_MATERIALIZED_SAMPLE",
        "data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/"
        "5f2e_5ut_approved_v1/samples/7aeb236b1946e96f.materialized.json",
        "c7120c9c12e2b2d8fc1ec0bd214ac6096cf1b377d93bafb237a275842349e03b",
    ),
    (
        "CUMULATIVE_SUCCESSOR_PIPELINE_RUN",
        "data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/"
        "6oim_mov_approved_v1/pipeline_run_v1.json",
        "f29293befa064970baaaa9e5c456f8b0de3d37b83c8700ebf5adc0ed37640355",
    ),
    (
        "CUMULATIVE_SUCCESSOR_MATERIALIZED_SAMPLE",
        "data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/"
        "6oim_mov_approved_v1/samples/a23745e87b364fe7.materialized.json",
        "edeb70f3a38a72f785def1e0eb42046793aa884d370fd7096b12eca877fb6b40",
    ),
    (
        "BATCH001_FORMAL_FULL_COMPONENT_REGISTRY",
        _BATCH001_COMPONENTS_V1,
        "76e6ecae7dfde7c9e5081a0164f9a72628e4f30550e831a8f8ba5cd3d1d16544",
    ),
    (
        "NDU_FULL_COMPONENT_RECOVERY_REGISTRY",
        _NDU_COMPONENT_V1,
        "3f0edbca6d2b43226321ac71e46b593029e18bc31ddc4693d6077530fe7996d2",
    ),
    (
        "EXISTING_POSITIVE_SPLIT_CLOSURE",
        _EXISTING_POSITIVE_CLOSURE_V1,
        "2f673a8ca76217af1517d8254de79799d4fea333d9892af13a3ab0eeb90d8259",
    ),
    (
        "CURRENT_LINKING_AXIS_REFERENCE_EVIDENCE",
        _BULK_PROCESSING_V1,
        "0270dd93a31427042d02f7751ab7b46679308c7f1ee5207a5560b199a6a94d57",
    ),
    (
        "MISSING_FROZEN_COMPONENT_RAW_PROTEIN_SEQUENCE_EVIDENCE_CARRIER",
        _MISSING_SEQUENCE_EVIDENCE_V1,
        "ed73ec02a2ffc07b515fbde1d54f2818b2003e2a0d551143c544972b0592fc5d",
    ),
)
_SOURCE_SHA_BY_PATH_V1 = {path: sha for _role, path, sha in _SOURCE_SPECS_V1}
_SOURCE_BYTE_COUNT_BY_PATH_V1 = {
    _PROCESSING_VIEW_V1: 5988559,
    _BASELINE_GROUP_MEMBERS_V1: 6316,
    _BASELINE_GROUP_SPLITS_V1: 1823,
    _CUMULATIVE_REGISTRY_V1: 2704,
    (
        "data/derived/covalent_small/"
        "covapie_cys_sg_dataset_expansion_pipeline_v1/6di9_gjj_approved_v1/"
        "pipeline_run_v1.json"
    ): 47337,
    (
        "data/derived/covalent_small/"
        "covapie_cys_sg_dataset_expansion_pipeline_v1/6di9_gjj_approved_v1/"
        "samples/8483b1e83aa8e1b6.materialized.json"
    ): 788,
    (
        "data/derived/covalent_small/"
        "covapie_cys_sg_dataset_expansion_pipeline_v1/5f2e_5ut_approved_v1/"
        "pipeline_run_v1.json"
    ): 45233,
    (
        "data/derived/covalent_small/"
        "covapie_cys_sg_dataset_expansion_pipeline_v1/5f2e_5ut_approved_v1/"
        "samples/7aeb236b1946e96f.materialized.json"
    ): 787,
    (
        "data/derived/covalent_small/"
        "covapie_cys_sg_dataset_expansion_pipeline_v1/6oim_mov_approved_v1/"
        "pipeline_run_v1.json"
    ): 49123,
    (
        "data/derived/covalent_small/"
        "covapie_cys_sg_dataset_expansion_pipeline_v1/6oim_mov_approved_v1/"
        "samples/a23745e87b364fe7.materialized.json"
    ): 787,
    _BATCH001_COMPONENTS_V1: 10237,
    _NDU_COMPONENT_V1: 19107,
    _EXISTING_POSITIVE_CLOSURE_V1: 16053,
    _BULK_PROCESSING_V1: 6845166,
    _MISSING_SEQUENCE_EVIDENCE_V1: 5922,
}

_EXPECTED_FROZEN_GROUP_SUMMARY_V1 = {
    "COVAPIE_LEAKAGE_GROUP_000001": ("train", 3),
    "COVAPIE_LEAKAGE_GROUP_000002": ("validation", 1),
    "COVAPIE_LEAKAGE_GROUP_000003": ("validation", 1),
    "COVAPIE_LEAKAGE_GROUP_000004": ("train", 5),
    "COVAPIE_LEAKAGE_GROUP_000005": ("test", 9),
    "COVAPIE_EXPANSION_LEAKAGE_GROUP_1004A7009A23CEA8": ("test", 2),
    "COVAPIE_EXPANSION_LEAKAGE_GROUP_29510E7F8D2A7A5F": ("train", 1),
    "COVAPIE_EXPANSION_LEAKAGE_GROUP_3157B39692D4D3EA": ("train", 9),
    "COVAPIE_EXPANSION_LEAKAGE_GROUP_8B76795E5CE26D95": ("validation", 1),
    "COVAPIE_EXPANSION_LEAKAGE_GROUP_AD79B40D8A505F37": ("validation", 1),
    "COVAPIE_EXPANSION_LEAKAGE_GROUP_B603B4C07705F93D": ("train", 5),
    "COVAPIE_EXPANSION_LEAKAGE_GROUP_E9D0DFDD004B6129": ("test", 1),
    "COVAPIE_EXPANSION_LEAKAGE_GROUP_7F26B737102D844D": ("validation", 1),
    "COVAPIE_EXPANSION_LEAKAGE_GROUP_0AC2E11AA7B6CEE0": ("test", 5),
}
_COMPONENT_REGISTRY_GROUP_IDS_V1 = frozenset({
    "COVAPIE_LEAKAGE_GROUP_000005",
    "COVAPIE_EXPANSION_LEAKAGE_GROUP_3157B39692D4D3EA",
    "COVAPIE_EXPANSION_LEAKAGE_GROUP_8B76795E5CE26D95",
    "COVAPIE_EXPANSION_LEAKAGE_GROUP_AD79B40D8A505F37",
    "COVAPIE_EXPANSION_LEAKAGE_GROUP_B603B4C07705F93D",
})
_MISSING_SEQUENCE_OWNER_BY_SHA_V1 = {
    "023281a4593e0ac1a65d6a2144f94f5bfcc2f652ceaba8fef5e094bcc7a8c31c": (
        "PTG", "COVAPIE_EXPANSION_LEAKAGE_GROUP_3157B39692D4D3EA",
    ),
    "2588ce2c9f90f875b577f6e9216e647be13263eb23648093b435375b85c9d622": (
        "PX5", "COVAPIE_EXPANSION_LEAKAGE_GROUP_AD79B40D8A505F37",
    ),
    "4cbc9547525595371398c7cf68a5aa845a9a54a3bb7834e5d29e9bbcd5a0191d": (
        "PTG", "COVAPIE_EXPANSION_LEAKAGE_GROUP_3157B39692D4D3EA",
    ),
    "9b72a2981ca04ca721cab81977b1321fae3e291d54333d300d49c09fea734d44": (
        "PTG", "COVAPIE_EXPANSION_LEAKAGE_GROUP_3157B39692D4D3EA",
    ),
    "d2b820b1e9b21d4643e873bfa4d8fa261312444c167dfbf8feaf4cbeebb600b7": (
        "DJK", "COVAPIE_EXPANSION_LEAKAGE_GROUP_B603B4C07705F93D",
    ),
    "f03e2556d3491b068a9a4ba8120b8e74e4a940d749d35d25022bccbde41229d0": (
        "PTG", "COVAPIE_EXPANSION_LEAKAGE_GROUP_3157B39692D4D3EA",
    ),
}
_EXPECTED_COMPONENT_SEQUENCE_SHAS_V1 = frozenset({
    *_MISSING_SEQUENCE_OWNER_BY_SHA_V1,
    "060823e0f298266cbc2c6281505a6310f24bad94e74223f1af13a7cbe603da15",
    "13321caa4faf35b2e1365239fdeb950565b323e195293a338445d1094adec0e8",
    "1f8113a43a87f0ca1d568a37b516dcf3ecffd613c04514a77e0032e18c6dee38",
    "6719485856207b3cfd517b78181d0e2f3f0a9906cb96fd970d8923d23fca2119",
    "95a47a78dbcf434f60977032cbbafd33f1ed6b1aa3ed17439926aa8635d28776",
    "a7d9421d9af786eb1816207e2d758ed71a5a8853184cb8a3cbc59674539bbd80",
    "b3355cd684d2ecb0db5eaa39f1e10cec389628b85d2236ef4f1efce6d973c333",
    "b527eb652d12b87156fabde8bdad091e29e6c4b6c7f31b0dfecfbcbfedc448d7",
    "f59ac11a38155d82df6219e40e6cd5e1612cd5a58130294fcd840a05ac5b2ebd",
})
_EXTERNAL_SEQUENCE_SOURCE_BINDING_V1 = {
    "byte_count": 3043911,
    "path": (
        "covapie-state/bulk-500-controlled-execution-v1/attempt-001/"
        "incremental_processing_outcomes_v1.json"
    ),
    "path_scope": "REPOSITORY_PARENT",
    "sha256": "d891a267dc4493cfceda33b70ab4a200d9f806e1bff38c4b6f39b69a1a3548d7",
}
_SEQUENCE_EVIDENCE_BOUNDARY_V1 = {
    "leakage_sequence_sha256_basis": (
        'SHA256(";".join(_entity_poly_seq.mon_id).encode("utf-8"))'
    ),
    "policy_authority": False,
    "raw_sequence_text_sha256_basis": (
        'SHA256(protein_sequence.encode("utf-8"))'
    ),
    "registry_authority": False,
    "runtime_external_source_dependency": False,
    "training_artifact": False,
}
_STANDARD_MONOMER_BY_ONE_LETTER_V1 = {
    "A": "ALA", "R": "ARG", "N": "ASN", "D": "ASP", "C": "CYS",
    "Q": "GLN", "E": "GLU", "G": "GLY", "H": "HIS", "I": "ILE",
    "L": "LEU", "K": "LYS", "M": "MET", "F": "PHE", "P": "PRO",
    "S": "SER", "T": "THR", "W": "TRP", "Y": "TYR", "V": "VAL",
}


class POAFullComponentFormalSplitAuthorityError(ValueError):
    """Raised unless the complete formal-split contract is proven."""


def _fail(reason: str) -> NoReturn:
    raise POAFullComponentFormalSplitAuthorityError(
        f"{COVAPIE_POA_FULL_COMPONENT_FORMAL_SPLIT_AUTHORITY_V1_ERROR}:{reason}"
    )


@dataclass(frozen=True, slots=True)
class POAFullComponentFormalSplitSourceBindingV1:
    artifact_role: str
    repository_relative_path: str
    byte_count: int
    sha256: str


@dataclass(frozen=True, slots=True)
class POAFullComponentFormalSplitRecordV1:
    canonical_event_id: str
    pdb_ligand_identity: str
    formal_leakage_group_id: str
    formal_split: str
    formal_split_authoritative: bool
    sample_training_admitted: bool
    model_training_activation_authorized: bool


@dataclass(frozen=True, slots=True)
class POAFullComponentFormalSplitSummaryV1:
    group_count: int
    identity_count: int
    train_group_count: int
    validation_group_count: int
    test_group_count: int
    train_identity_count: int
    validation_identity_count: int
    test_identity_count: int


@dataclass(frozen=True, slots=True)
class POAFullComponentFormalSplitOracleV1:
    candidate_assignment_count: int
    valid_assignment_count: int
    selected_split: str
    selected_sample_counts: tuple[int, int, int]
    selected_group_counts: tuple[int, int, int]
    selected_objective: tuple[Fraction, Fraction, Fraction]
    tie_count_before_signature: int
    lexicographic_tie_break_verified: bool
    selected_assignment: tuple[tuple[str, str, str], ...]


@dataclass(frozen=True, slots=True)
class POAFullComponentFormalSplitAuthorityResultV1:
    source_bindings: tuple[POAFullComponentFormalSplitSourceBindingV1, ...]
    leakage_classification: str
    leakage_key: str
    full_component_group_id: str
    full_member_pdb_ligand_identities: tuple[str, ...]
    full_member_canonical_event_ids: tuple[str, ...]
    canonical_event_inventory_sha256: str
    linking_axes: tuple[str, ...]
    exact16_event_ids: tuple[str, ...]
    external_g3h_event_ids: tuple[str, ...]
    read_only_predicted_split: str
    read_only_prediction_is_authority: bool
    read_only_prediction_copied_as_formal_authority: bool
    formal_group_id: str
    formal_split: str
    formal_split_authoritative: bool
    records: tuple[POAFullComponentFormalSplitRecordV1, ...]
    existing_frozen_groups_before: tuple[split_owner.LeakageGroupAssignmentV1, ...]
    existing_frozen_groups_after: tuple[split_owner.LeakageGroupAssignmentV1, ...]
    frozen_inventory_sha256: str
    before_summary: POAFullComponentFormalSplitSummaryV1
    after_summary: POAFullComponentFormalSplitSummaryV1
    generic_owner_assignment: tuple[tuple[str, str, str], ...]
    independent_oracle: POAFullComponentFormalSplitOracleV1
    generic_owner_oracle_parity: bool
    input_order_independence_verified: bool
    existing_frozen_splits_changed: bool
    cross_split_leakage_conflict: bool
    cross_link_conflict_authoritatively_proven: bool
    cross_link_reference_group_count: int
    cross_link_reference_count: int
    cross_link_comparison_count: int
    sequence_identity_reference_group_count: int
    sequence_identity_reference_sequence_count: int
    raw_sequence_reference_count: int
    sequence_identity_comparison_count: int
    protein_sequence_identity_axis_cross_link_coverage_complete: bool
    randomization_used: bool
    random_seed: int | None
    manual_split_override: bool
    sample_training_admitted: bool
    model_training_activation_authorized: bool
    ready_for_training: bool


@dataclass(frozen=True, slots=True)
class _POAComponentEvidenceV1:
    classification: str
    leakage_key: str
    read_only_group_id: str
    read_only_split: str
    identities: tuple[str, ...]
    event_ids: tuple[str, ...]
    evidence_by_event: tuple[tuple[str, Mapping[str, Any]], ...]
    linking_axes: tuple[str, ...]
    component_axis_values: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _SequenceIdentityAuditV1:
    frozen_reference_group_count: int
    reference_group_count: int
    reference_sequence_count: int
    reference_count: int
    raw_sequence_reference_count: int
    comparison_count: int
    sequence_identity_comparison_count: int


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("utf-8")


def _json(payload: bytes, reason: str) -> Any:
    try:
        return json.loads(payload.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise POAFullComponentFormalSplitAuthorityError(
            f"{COVAPIE_POA_FULL_COMPONENT_FORMAL_SPLIT_AUTHORITY_V1_ERROR}:"
            f"{reason}:JSON_INVALID"
        ) from error


def _csv_rows(payload: bytes, reason: str) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
        rows = list(reader)
    except (UnicodeError, csv.Error) as error:
        raise POAFullComponentFormalSplitAuthorityError(
            f"{COVAPIE_POA_FULL_COMPONENT_FORMAL_SPLIT_AUTHORITY_V1_ERROR}:"
            f"{reason}:CSV_INVALID"
        ) from error
    header = tuple(reader.fieldnames or ())
    if not header or not rows or any(None in row for row in rows):
        _fail(reason + ":CSV_SCHEMA_INVALID")
    return header, rows


def _require_repo_root(value: object) -> Path:
    if not isinstance(value, Path):
        _fail("REPO_ROOT_TYPE_INVALID")
    try:
        resolved = value.resolve(strict=True)
    except OSError as error:
        raise POAFullComponentFormalSplitAuthorityError(
            f"{COVAPIE_POA_FULL_COMPONENT_FORMAL_SPLIT_AUTHORITY_V1_ERROR}:"
            "REPO_ROOT_UNAVAILABLE"
        ) from error
    if not resolved.is_dir() or value.is_symlink():
        _fail("REPO_ROOT_INVALID")
    return resolved


def _read_bound_sources_v1(
    repo: Path,
) -> tuple[dict[str, bytes], tuple[POAFullComponentFormalSplitSourceBindingV1, ...]]:
    payloads: dict[str, bytes] = {}
    bindings: list[POAFullComponentFormalSplitSourceBindingV1] = []
    for role, relative, expected_sha in _SOURCE_SPECS_V1:
        path = repo / relative
        if not path.is_file() or path.is_symlink():
            _fail("SOURCE_MISSING_OR_NOT_REGULAR:" + relative)
        try:
            payload = path.read_bytes()
        except OSError as error:
            raise POAFullComponentFormalSplitAuthorityError(
                f"{COVAPIE_POA_FULL_COMPONENT_FORMAL_SPLIT_AUTHORITY_V1_ERROR}:"
                f"SOURCE_UNREADABLE:{relative}"
            ) from error
        observed_sha = _sha256(payload)
        if observed_sha != expected_sha:
            _fail("SOURCE_SHA256_MISMATCH:" + relative)
        payloads[relative] = payload
        bindings.append(POAFullComponentFormalSplitSourceBindingV1(
            artifact_role=role,
            repository_relative_path=relative,
            byte_count=len(payload),
            sha256=observed_sha,
        ))
    return payloads, tuple(bindings)


def _identity_from_event_id_v1(event_id: object) -> str:
    if type(event_id) is not str:
        _fail("CANONICAL_EVENT_ID_TYPE_INVALID")
    match = _EVENT_ID_V1.fullmatch(event_id)
    if match is None:
        _fail("CANONICAL_EVENT_ID_INVALID:" + event_id)
    return f"{match.group('pdb')}/{match.group('ligand')}"


def _new_group(
    *, leakage_key: object, group_id: object, split: object,
    member_identities: object, reason: str,
) -> split_owner.LeakageGroupAssignmentV1:
    if (
        type(leakage_key) is not str
        or not leakage_key
        or type(group_id) is not str
        or not group_id
        or split not in _SPLITS_V1
        or type(member_identities) not in (list, tuple)
    ):
        _fail(reason + ":GROUP_FIELDS_INVALID")
    members = tuple(member_identities)
    if (
        not members
        or members != tuple(sorted(members))
        or len(set(members)) != len(members)
        or any(type(item) is not str or _IDENTITY_V1.fullmatch(item) is None for item in members)
    ):
        _fail(reason + ":MEMBER_IDENTITIES_INVALID")
    return split_owner.LeakageGroupAssignmentV1(
        leakage_key=leakage_key,
        final_leakage_group_id=group_id,
        member_count=len(members),
        assigned_split=split,
        frozen=True,
        member_identities=members,
    )


def _historical_groups_v1(payloads: Mapping[str, bytes]) -> list[split_owner.LeakageGroupAssignmentV1]:
    _header, member_rows = _csv_rows(
        payloads[_BASELINE_GROUP_MEMBERS_V1], "HISTORICAL_GROUP_MEMBERS"
    )
    _split_header, split_rows = _csv_rows(
        payloads[_BASELINE_GROUP_SPLITS_V1], "HISTORICAL_GROUP_SPLITS"
    )
    members_by_group: dict[str, list[str]] = {}
    for row in member_rows:
        if row.get("final_group_assignment_passed") != "True":
            _fail("HISTORICAL_GROUP_MEMBER_NOT_AUTHORITATIVE")
        identity = f"{row.get('pdb_id', '')}/{row.get('ligand_comp_id', '')}"
        members_by_group.setdefault(row.get("final_leakage_group_id", ""), []).append(identity)
    result: list[split_owner.LeakageGroupAssignmentV1] = []
    for row in split_rows:
        group_id = row.get("final_leakage_group_id")
        members = tuple(sorted(members_by_group.get(str(group_id), ())))
        if (
            row.get("split_policy") != "deterministic_final_leakage_group_exhaustive_ratio_fit_v1"
            or row.get("group_split_assignment_passed") != "True"
            or row.get("group_kept_intact") != "True"
            or row.get("member_count") != str(len(members))
        ):
            _fail("HISTORICAL_GROUP_SPLIT_INVALID")
        result.append(_new_group(
            leakage_key=group_id,
            group_id=group_id,
            split=row.get("assigned_split"),
            member_identities=members,
            reason="HISTORICAL_GROUP",
        ))
    if len(result) != 5 or set(members_by_group) != {
        group.final_leakage_group_id for group in result
    }:
        _fail("HISTORICAL_EXACT5_POPULATION_INVALID")
    return result


def _cumulative_groups_v1(payloads: Mapping[str, bytes]) -> list[split_owner.LeakageGroupAssignmentV1]:
    parsed = _json(payloads[_CUMULATIVE_REGISTRY_V1], "CUMULATIVE_REGISTRY")
    if (
        type(parsed) is not dict
        or parsed.get("schema_version")
        != split_owner.CUMULATIVE_EXPANSION_LEAKAGE_REGISTRY_SCHEMA_V1
        or parsed.get("policy_id")
        != split_owner.CUMULATIVE_EXPANSION_LEAKAGE_POLICY_ID_V1
        or type(parsed.get("groups")) is not list
        or len(parsed["groups"]) != 2
        or type(parsed.get("provenance")) is not dict
        or type(parsed["provenance"].get("source_artifacts")) is not list
    ):
        _fail("CUMULATIVE_REGISTRY_SCHEMA_INVALID")
    registry_dir = Path(_CUMULATIVE_REGISTRY_V1).parent
    observed_provenance: set[tuple[str, str]] = set()
    for item in parsed["provenance"]["source_artifacts"]:
        if type(item) is not dict:
            _fail("CUMULATIVE_PROVENANCE_INVALID")
        path = item.get("path")
        scope = item.get("path_scope")
        if scope == "REGISTRY_DIRECTORY_RELATIVE" and type(path) is str:
            relative = (registry_dir / path).as_posix()
        elif scope == "REPOSITORY_ROOT_RELATIVE" and type(path) is str:
            relative = Path(path).as_posix()
        else:
            _fail("CUMULATIVE_PROVENANCE_PATH_INVALID")
        sha = item.get("sha256")
        if (
            _SOURCE_SHA_BY_PATH_V1.get(relative) != sha
            or _sha256(payloads[relative]) != sha
        ):
            _fail("CUMULATIVE_PROVENANCE_SHA256_INVALID:" + relative)
        observed_provenance.add((relative, str(sha)))
    expected_provenance = {
        (path, sha) for _role, path, sha in _SOURCE_SPECS_V1
        if path in {
            _BASELINE_GROUP_SPLITS_V1,
            "data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/6di9_gjj_approved_v1/pipeline_run_v1.json",
            "data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/6di9_gjj_approved_v1/samples/8483b1e83aa8e1b6.materialized.json",
            "data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/5f2e_5ut_approved_v1/pipeline_run_v1.json",
            "data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/5f2e_5ut_approved_v1/samples/7aeb236b1946e96f.materialized.json",
            "data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/6oim_mov_approved_v1/pipeline_run_v1.json",
            "data/derived/covalent_small/covapie_cys_sg_dataset_expansion_pipeline_v1/6oim_mov_approved_v1/samples/a23745e87b364fe7.materialized.json",
        }
    }
    if observed_provenance != expected_provenance:
        _fail("CUMULATIVE_PROVENANCE_INVENTORY_INVALID")
    result = []
    for row in parsed["groups"]:
        if type(row) is not dict or row.get("member_count") != len(row.get("member_identities", ())):
            _fail("CUMULATIVE_GROUP_INVALID")
        result.append(_new_group(
            leakage_key=row.get("leakage_key"),
            group_id=row.get("final_leakage_group_id"),
            split=row.get("assigned_split"),
            member_identities=row.get("member_identities"),
            reason="CUMULATIVE_GROUP",
        ))
    return result


def _batch_groups_v1(
    payloads: Mapping[str, bytes],
) -> tuple[list[split_owner.LeakageGroupAssignmentV1], Mapping[str, Any]]:
    parsed = _json(payloads[_BATCH001_COMPONENTS_V1], "BATCH001_COMPONENTS")
    if (
        type(parsed) is not dict
        or parsed.get("schema_version") != "covapie_batch001_formal_leakage_component_registry_v1"
        or parsed.get("artifact_role")
        != "ADDITIVE_FULL_COMPONENT_LEAKAGE_MEMBERSHIP_AND_FORMAL_SPLIT_RESERVATION"
        or parsed.get("component_count") != 4
        or type(parsed.get("components")) is not list
        or len(parsed["components"]) != 4
    ):
        _fail("BATCH001_COMPONENT_REGISTRY_INVALID")
    result = []
    for row in parsed["components"]:
        if (
            type(row) is not dict
            or row.get("classification") != "NEW_EXPANSION_COMPONENT"
            or row.get("formal_assignment_is_authority_candidate") is not True
            or row.get("group_parity") is not True
            or row.get("full_identity_count") != len(row.get("full_member_pdb_ligand_identities", ()))
            or row.get("full_event_count") != len(row.get("full_member_canonical_event_ids", ()))
            or type(row.get("source_evidence_linking_axis_values")) is not list
            or not row["source_evidence_linking_axis_values"]
        ):
            _fail("BATCH001_COMPONENT_INVALID")
        result.append(_new_group(
            leakage_key=row.get("leakage_key"),
            group_id=row.get("formal_group_id"),
            split=row.get("formal_split"),
            member_identities=row.get("full_member_pdb_ligand_identities"),
            reason="BATCH001_COMPONENT",
        ))
    return result, parsed


def _apply_ndu_recovery_v1(
    groups: list[split_owner.LeakageGroupAssignmentV1],
    payloads: Mapping[str, bytes],
) -> Mapping[str, Any]:
    parsed = _json(payloads[_NDU_COMPONENT_V1], "NDU_COMPONENT")
    components = parsed.get("components") if type(parsed) is dict else None
    if (
        type(parsed) is not dict
        or parsed.get("schema_version") != "covapie_batch001_ndu4_full_component_registry_v1"
        or parsed.get("component_count") != 1
        or type(components) is not list
        or len(components) != 1
    ):
        _fail("NDU_COMPONENT_REGISTRY_INVALID")
    row = components[0]
    if (
        type(row) is not dict
        or row.get("classification") != "HISTORICAL_BASELINE_COMPONENT"
        or row.get("formal_assignment_status") != "EXISTING_FROZEN_GROUP_SPLIT_INHERITED"
        or row.get("group_existed_pre_recovery") is not True
        or row.get("full_identity_count") != len(row.get("full_member_pdb_ligand_identities", ()))
        or type(row.get("source_evidence_linking_axis_values")) is not list
        or not row["source_evidence_linking_axis_values"]
    ):
        _fail("NDU_COMPONENT_INVALID")
    matches = [
        (index, group) for index, group in enumerate(groups)
        if group.final_leakage_group_id == row.get("formal_group_id")
    ]
    if len(matches) != 1:
        _fail("NDU_HISTORICAL_GROUP_OWNER_INVALID")
    index, prior = matches[0]
    replacement = _new_group(
        leakage_key=row.get("leakage_key"),
        group_id=row.get("formal_group_id"),
        split=row.get("formal_split"),
        member_identities=row.get("full_member_pdb_ligand_identities"),
        reason="NDU_COMPONENT",
    )
    if (
        replacement.leakage_key != prior.leakage_key
        or replacement.assigned_split != prior.assigned_split
        or not set(prior.member_identities) <= set(replacement.member_identities)
    ):
        _fail("NDU_HISTORICAL_GROUP_INHERITANCE_INVALID")
    groups[index] = replacement
    return parsed


def _closure_groups_v1(payloads: Mapping[str, bytes]) -> list[split_owner.LeakageGroupAssignmentV1]:
    _header, rows = _csv_rows(payloads[_EXISTING_POSITIVE_CLOSURE_V1], "EXISTING_POSITIVE_CLOSURE")
    by_group: dict[str, dict[str, Any]] = {}
    event_ids: set[str] = set()
    for row in rows:
        if not (
            row.get("formal_split_authoritative_before") == "false"
            and row.get("formal_split_authoritative_after") == "true"
        ):
            continue
        if (
            row.get("leakage_evidence_complete") != "true"
            or row.get("leakage_classification") != "NEW_EXPANSION_COMPONENT"
            or row.get("split_closure_status") != "FORMAL_SPLIT_CLOSED"
            or row.get("assignment_policy")
            != "PUBLISHED_GENERIC_ADDITIVE_COMPONENT_LEVEL_SPLIT_POLICY"
        ):
            _fail("EXISTING_POSITIVE_CLOSURE_ROW_INVALID")
        event_id = row.get("canonical_event_id", "")
        if event_id in event_ids:
            _fail("EXISTING_POSITIVE_CLOSURE_EVENT_DUPLICATED")
        event_ids.add(event_id)
        identity = _identity_from_event_id_v1(event_id)
        group_id = row.get("leakage_group_id_after", "")
        slot = by_group.setdefault(group_id, {
            "key": row.get("leakage_key"),
            "split": row.get("formal_split_after"),
            "identities": set(),
        })
        if slot["key"] != row.get("leakage_key") or slot["split"] != row.get("formal_split_after"):
            _fail("EXISTING_POSITIVE_CLOSURE_GROUP_CONFLICT")
        slot["identities"].add(identity)
    if len(by_group) != 3 or len(event_ids) != 9:
        _fail("EXISTING_POSITIVE_CLOSURE_POPULATION_INVALID")
    return [
        _new_group(
            leakage_key=slot["key"],
            group_id=group_id,
            split=slot["split"],
            member_identities=tuple(sorted(slot["identities"])),
            reason="EXISTING_POSITIVE_CLOSURE_GROUP",
        )
        for group_id, slot in sorted(by_group.items())
    ]


def _frozen_inventory_sha256_v1(groups: Sequence[split_owner.LeakageGroupAssignmentV1]) -> str:
    inventory = [{
        "assigned_split": group.assigned_split,
        "final_leakage_group_id": group.final_leakage_group_id,
        "leakage_key": group.leakage_key,
        "member_identities": list(group.member_identities),
    } for group in sorted(groups, key=lambda item: (
        item.final_leakage_group_id, item.leakage_key,
    ))]
    return _sha256(_canonical_json_bytes(inventory))


def _validate_frozen_groups_v1(
    groups: object,
) -> tuple[split_owner.LeakageGroupAssignmentV1, ...]:
    if type(groups) not in (tuple, list) or len(groups) != 14:
        _fail("FROZEN_GROUP_COUNT_INVALID")
    normalized = tuple(sorted(groups, key=lambda item: (
        getattr(item, "final_leakage_group_id", ""), getattr(item, "leakage_key", ""),
    )))
    seen_keys: set[str] = set()
    seen_ids: set[str] = set()
    seen_members: set[str] = set()
    observed_summary: dict[str, tuple[str, int]] = {}
    for group in normalized:
        if (
            type(group) is not split_owner.LeakageGroupAssignmentV1
            or group.frozen is not True
            or group.assigned_split not in _SPLITS_V1
            or group.member_count != len(group.member_identities)
            or group.member_count <= 0
            or tuple(sorted(group.member_identities)) != group.member_identities
            or len(set(group.member_identities)) != len(group.member_identities)
            or any(_IDENTITY_V1.fullmatch(item) is None for item in group.member_identities)
            or group.leakage_key in seen_keys
            or group.final_leakage_group_id in seen_ids
            or seen_members.intersection(group.member_identities)
        ):
            _fail("FROZEN_GROUP_INVENTORY_INVALID")
        seen_keys.add(group.leakage_key)
        seen_ids.add(group.final_leakage_group_id)
        seen_members.update(group.member_identities)
        observed_summary[group.final_leakage_group_id] = (
            group.assigned_split, group.member_count,
        )
    if observed_summary != _EXPECTED_FROZEN_GROUP_SUMMARY_V1:
        _fail("FROZEN_GROUP_SUMMARY_INVALID")
    if len(seen_members) != 45:
        _fail("FROZEN_IDENTITY_COUNT_INVALID")
    if _frozen_inventory_sha256_v1(normalized) != POA_FROZEN14_INVENTORY_SHA256_V1:
        _fail("FROZEN_EXACT_MEMBER_INVENTORY_INVALID")
    return normalized


def _reconstruct_frozen_groups_v1(
    payloads: Mapping[str, bytes],
) -> tuple[
    tuple[split_owner.LeakageGroupAssignmentV1, ...], Mapping[str, Any], Mapping[str, Any],
]:
    groups = _historical_groups_v1(payloads)
    groups.extend(_cumulative_groups_v1(payloads))
    batch_groups, batch_registry = _batch_groups_v1(payloads)
    groups.extend(batch_groups)
    ndu_registry = _apply_ndu_recovery_v1(groups, payloads)
    groups.extend(_closure_groups_v1(payloads))
    return _validate_frozen_groups_v1(groups), batch_registry, ndu_registry


def _extract_poa_component_from_events_v1(events: object) -> _POAComponentEvidenceV1:
    if type(events) is not list:
        _fail("PROCESSING_EVENTS_INVALID")
    selected: list[Mapping[str, Any]] = []
    for wrapper in events:
        if type(wrapper) is not dict or type(wrapper.get("processing_outcome")) is not dict:
            _fail("PROCESSING_EVENT_WRAPPER_INVALID")
        outcome = wrapper["processing_outcome"]
        if outcome.get("leakage_key") == POA_LEAKAGE_KEY_V1:
            selected.append(outcome)
    if len(selected) != 24:
        _fail("POA_FULL_COMPONENT_EVENT_COUNT_INVALID")
    event_ids: list[str] = []
    identities: set[str] = set()
    evidence_by_event: list[tuple[str, Mapping[str, Any]]] = []
    component_axis_values: tuple[str, ...] | None = None
    for outcome in selected:
        event_id = outcome.get("canonical_event_id")
        identity = f"{outcome.get('pdb_id', '')}/{outcome.get('ligand_component_id', '')}"
        if (
            type(event_id) is not str
            or _identity_from_event_id_v1(event_id) != identity
            or outcome.get("leakage_classification") != POA_CLASSIFICATION_V1
            or outcome.get("leakage_key") != POA_LEAKAGE_KEY_V1
            or outcome.get("predicted_group_id") != POA_FORMAL_GROUP_ID_V1
            or outcome.get("predicted_split") != POA_READ_ONLY_PREDICTED_SPLIT_V1
        ):
            _fail("POA_PROCESSING_OUTCOME_SEMANTICS_INVALID")
        structural = outcome.get("structural_processing")
        evidence = structural.get("leakage_evidence") if type(structural) is dict else None
        if (
            type(evidence) is not dict
            or evidence.get("complete") is not True
            or not evidence.get("ligand_graph_sha256")
            or not evidence.get("protein_accession")
            or not evidence.get("protein_sequence_sha256")
            or not evidence.get("protein_sequence")
        ):
            _fail("POA_LEAKAGE_EVIDENCE_INCOMPLETE")
        raw_component_axes = outcome.get("leakage_linking_axes")
        if (
            type(raw_component_axes) is not list
            or not raw_component_axes
            or any(type(value) is not str or not value for value in raw_component_axes)
        ):
            _fail("POA_COMPONENT_AXIS_VALUE_INVENTORY_INVALID")
        normalized_component_axes = tuple(sorted(set(raw_component_axes)))
        if len(normalized_component_axes) != len(raw_component_axes):
            _fail("POA_COMPONENT_AXIS_VALUE_DUPLICATED")
        if component_axis_values is None:
            component_axis_values = normalized_component_axes
        elif normalized_component_axes != component_axis_values:
            _fail("POA_COMPONENT_AXIS_VALUE_INVENTORY_INCONSISTENT")
        event_ids.append(event_id)
        identities.add(identity)
        evidence_by_event.append((event_id, evidence))
    sorted_events = tuple(sorted(event_ids))
    if len(set(sorted_events)) != 24:
        _fail("POA_CANONICAL_EVENT_DUPLICATED")
    sorted_identities = tuple(sorted(identities))
    if sorted_identities != POA_IDENTITIES_V1:
        _fail("POA_FULL_COMPONENT_IDENTITIES_INVALID")
    if _sha256(_canonical_json_bytes(list(sorted_events))) != POA_CANONICAL_EVENT_INVENTORY_SHA256_V1:
        _fail("POA_CANONICAL_EVENT_INVENTORY_INVALID")

    adjacency: dict[str, set[str]] = {event_id: set() for event_id in sorted_events}
    linking_axes: set[str] = set()
    evidence_map = dict(evidence_by_event)
    for index, left_id in enumerate(sorted_events):
        for right_id in sorted_events[index + 1:]:
            axes = bulk_owner._leakage_linking_axes_v1(
                evidence_map[left_id], evidence_map[right_id]
            )
            if axes:
                adjacency[left_id].add(right_id)
                adjacency[right_id].add(left_id)
                linking_axes.update(axes)
    reached: set[str] = set()
    queue = deque((sorted_events[0],))
    while queue:
        event_id = queue.popleft()
        if event_id in reached:
            continue
        reached.add(event_id)
        queue.extend(sorted(adjacency[event_id] - reached))
    if reached != set(sorted_events):
        _fail("POA_COMPONENT_NOT_SINGLE_CONNECTED_UNIT")
    if tuple(sorted(linking_axes)) != POA_LINKING_AXES_V1:
        _fail("POA_COMPONENT_LINKING_AXES_INVALID")
    derived_axis_values = tuple(sorted({
        value
        for _event_id, evidence in evidence_by_event
        for value in evidence.get("linking_axes", ())
    }))
    if component_axis_values is None or component_axis_values != derived_axis_values:
        _fail("POA_COMPONENT_AXIS_VALUE_INVENTORY_NOT_EXACTLY_DERIVED")
    return _POAComponentEvidenceV1(
        classification=POA_CLASSIFICATION_V1,
        leakage_key=POA_LEAKAGE_KEY_V1,
        read_only_group_id=POA_FORMAL_GROUP_ID_V1,
        read_only_split=POA_READ_ONLY_PREDICTED_SPLIT_V1,
        identities=sorted_identities,
        event_ids=sorted_events,
        evidence_by_event=tuple(sorted(evidence_by_event)),
        linking_axes=tuple(sorted(linking_axes)),
        component_axis_values=component_axis_values,
    )


def _extract_poa_component_v1(payload: bytes) -> _POAComponentEvidenceV1:
    parsed = _json(payload, "PROCESSING_VIEW")
    if (
        type(parsed) is not dict
        or parsed.get("schema_version")
        != "covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1"
        or parsed.get("rank_start") != 501
        or parsed.get("rank_end") != 1000
        or parsed.get("terminal_outcome_count") != 500
        or parsed.get("structural_processing_performed") is not True
        or parsed.get("training_performed") is not False
    ):
        _fail("PROCESSING_VIEW_SEMANTICS_INVALID")
    return _extract_poa_component_from_events_v1(parsed.get("events"))


def _merge_sequence_evidence_v1(
    target: dict[str, str], evidence: Mapping[str, str], *, reason: str,
) -> None:
    for sequence_sha, sequence in evidence.items():
        if (
            type(sequence_sha) is not str
            or re.fullmatch(r"[0-9a-f]{64}", sequence_sha) is None
            or type(sequence) is not str
            or not sequence
            or re.fullmatch(r"[A-Z]+", sequence) is None
        ):
            _fail(reason + ":SEQUENCE_EVIDENCE_INVALID")
        previous = target.get(sequence_sha)
        if previous is not None and previous != sequence:
            _fail(reason + ":CONFLICTING_RAW_SEQUENCE")
        target[sequence_sha] = sequence


def _producer_sequence_sha256_v1(sequence: str) -> str:
    try:
        monomers = [_STANDARD_MONOMER_BY_ONE_LETTER_V1[symbol] for symbol in sequence]
    except (KeyError, TypeError):
        _fail("PRODUCER_SEQUENCE_HASH_INPUT_INVALID")
    return _sha256(";".join(monomers).encode("utf-8"))


def _processing_sequence_evidence_v1(
    payload: bytes, *, reason: str, schema_version: str, nested: bool,
) -> dict[str, str]:
    parsed = _json(payload, reason)
    events = parsed.get("events") if type(parsed) is dict else None
    if (
        type(parsed) is not dict
        or parsed.get("schema_version") != schema_version
        or type(events) is not list
    ):
        _fail(reason + ":SCHEMA_INVALID")
    result: dict[str, str] = {}
    for row in events:
        if type(row) is not dict:
            _fail(reason + ":EVENT_INVALID")
        container = row.get("processing_outcome") if nested else row
        if type(container) is not dict:
            continue
        structural = container.get("structural_processing")
        leakage = structural.get("leakage_evidence") if type(structural) is dict else None
        if type(leakage) is not dict:
            continue
        sequence_sha = leakage.get("protein_sequence_sha256")
        sequence = leakage.get("protein_sequence")
        if not sequence_sha and not sequence:
            continue
        if type(sequence_sha) is not str or type(sequence) is not str:
            _fail(reason + ":RAW_SEQUENCE_PAIR_INVALID")
        _merge_sequence_evidence_v1(
            result, {sequence_sha: sequence}, reason=reason,
        )
    return result


def _missing_sequence_evidence_v1(payload: bytes) -> dict[str, str]:
    parsed = _json(payload, "MISSING_SEQUENCE_EVIDENCE")
    if type(parsed) is not dict or payload != _canonical_json_bytes(parsed):
        _fail("MISSING_SEQUENCE_EVIDENCE:NOT_CANONICAL_JSON")
    if set(parsed) != {
        "artifact_role", "boundary", "schema_version", "sequence_record_count",
        "sequence_records", "source_binding",
    }:
        _fail("MISSING_SEQUENCE_EVIDENCE:TOP_LEVEL_SCHEMA_INVALID")
    records = parsed.get("sequence_records")
    if (
        parsed.get("schema_version")
        != "covapie_poa_missing_frozen_component_protein_sequence_evidence_v1"
        or parsed.get("artifact_role")
        != "MISSING_FROZEN_COMPONENT_RAW_PROTEIN_SEQUENCE_EVIDENCE_CARRIER_ONLY"
        or parsed.get("boundary") != _SEQUENCE_EVIDENCE_BOUNDARY_V1
        or parsed.get("source_binding") != _EXTERNAL_SEQUENCE_SOURCE_BINDING_V1
        or parsed.get("sequence_record_count") != 6
        or type(records) is not list
        or len(records) != 6
    ):
        _fail("MISSING_SEQUENCE_EVIDENCE:CONTRACT_INVALID")
    result: dict[str, str] = {}
    observed_order: list[str] = []
    for row in records:
        if type(row) is not dict or set(row) != {
            "component_name", "formal_group_id", "protein_sequence",
            "protein_sequence_sha256", "protein_sequence_text_sha256",
            "source_canonical_event_ids", "source_pdb_ligand_identities",
        }:
            _fail("MISSING_SEQUENCE_EVIDENCE:RECORD_SCHEMA_INVALID")
        sequence_sha = row.get("protein_sequence_sha256")
        sequence = row.get("protein_sequence")
        owner = _MISSING_SEQUENCE_OWNER_BY_SHA_V1.get(sequence_sha)
        if (
            owner is None
            or (row.get("component_name"), row.get("formal_group_id")) != owner
            or type(sequence) is not str
            or not sequence
            or re.fullmatch(r"[A-Z]+", sequence) is None
            or sequence_sha != _producer_sequence_sha256_v1(sequence)
            or row.get("protein_sequence_text_sha256")
            != _sha256(sequence.encode("utf-8"))
        ):
            _fail("MISSING_SEQUENCE_EVIDENCE:RECORD_SEMANTICS_INVALID")
        identities = row.get("source_pdb_ligand_identities")
        event_ids = row.get("source_canonical_event_ids")
        if (
            type(identities) is not list
            or not identities
            or identities != sorted(set(identities))
            or any(type(item) is not str or _IDENTITY_V1.fullmatch(item) is None for item in identities)
            or type(event_ids) is not list
            or not event_ids
            or event_ids != sorted(set(event_ids))
            or any(
                type(event_id) is not str
                or _identity_from_event_id_v1(event_id) not in identities
                for event_id in event_ids
            )
        ):
            _fail("MISSING_SEQUENCE_EVIDENCE:PROVENANCE_INVALID")
        observed_order.append(sequence_sha)
        _merge_sequence_evidence_v1(
            result, {sequence_sha: sequence}, reason="MISSING_SEQUENCE_EVIDENCE",
        )
    if (
        observed_order != sorted(observed_order)
        or set(result) != set(_MISSING_SEQUENCE_OWNER_BY_SHA_V1)
    ):
        _fail("MISSING_SEQUENCE_EVIDENCE:INVENTORY_INVALID")
    return result


def _component_registry_sequence_inventory_v1(
    batch_registry: Mapping[str, Any], ndu_registry: Mapping[str, Any],
) -> tuple[dict[str, tuple[str, str]], int]:
    result: dict[str, tuple[str, str]] = {}
    groups: set[str] = set()
    for registry, reason in (
        (batch_registry, "BATCH001_SEQUENCE_INVENTORY"),
        (ndu_registry, "NDU_SEQUENCE_INVENTORY"),
    ):
        rows = registry.get("components")
        if type(rows) is not list:
            _fail(reason + ":COMPONENTS_INVALID")
        for row in rows:
            if type(row) is not dict:
                _fail(reason + ":COMPONENT_INVALID")
            component_name = row.get("component_name")
            group_id = row.get("formal_group_id")
            axes = row.get("source_evidence_linking_axis_values")
            if (
                type(component_name) is not str
                or not component_name
                or group_id not in _COMPONENT_REGISTRY_GROUP_IDS_V1
                or type(axes) is not list
            ):
                _fail(reason + ":COMPONENT_SEMANTICS_INVALID")
            groups.add(group_id)
            sequence_shas = sorted(
                value.partition(":")[2]
                for value in axes
                if type(value) is str
                and value.startswith("PROTEIN_EXACT_SEQUENCE:")
            )
            if not sequence_shas:
                _fail(reason + ":SEQUENCE_INVENTORY_EMPTY")
            for sequence_sha in sequence_shas:
                if re.fullmatch(r"[0-9a-f]{64}", sequence_sha) is None:
                    _fail(reason + ":SEQUENCE_SHA256_INVALID")
                owner = (component_name, group_id)
                if sequence_sha in result and result[sequence_sha] != owner:
                    _fail(reason + ":SEQUENCE_OWNER_CONFLICT")
                result[sequence_sha] = owner
    if (
        groups != set(_COMPONENT_REGISTRY_GROUP_IDS_V1)
        or set(result) != set(_EXPECTED_COMPONENT_SEQUENCE_SHAS_V1)
    ):
        _fail("COMPONENT_REGISTRY_SEQUENCE_INVENTORY_INVALID")
    for sequence_sha, owner in _MISSING_SEQUENCE_OWNER_BY_SHA_V1.items():
        if result.get(sequence_sha) != owner:
            _fail("MISSING_SEQUENCE_OWNER_NOT_REGISTRY_DERIVED")
    return result, len(groups)


def _complete_component_sequence_evidence_v1(
    *, processing_view_payload: bytes, bulk_processing_payload: bytes,
    carrier_payload: bytes, batch_registry: Mapping[str, Any],
    ndu_registry: Mapping[str, Any],
) -> tuple[dict[str, str], int, int]:
    processing = _processing_sequence_evidence_v1(
        processing_view_payload,
        reason="PROCESSING_VIEW_SEQUENCE_EVIDENCE",
        schema_version="covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1",
        nested=True,
    )
    bulk = _processing_sequence_evidence_v1(
        bulk_processing_payload,
        reason="CURRENT_LINKING_AXIS_SEQUENCE_EVIDENCE",
        schema_version="covapie_bulk_multisource_cys_sg_dataset_expansion_v1",
        nested=False,
    )
    carrier = _missing_sequence_evidence_v1(carrier_payload)
    required, group_count = _component_registry_sequence_inventory_v1(
        batch_registry, ndu_registry,
    )
    tracked: dict[str, str] = {}
    _merge_sequence_evidence_v1(tracked, processing, reason="TRACKED_SEQUENCE_EVIDENCE")
    _merge_sequence_evidence_v1(tracked, bulk, reason="TRACKED_SEQUENCE_EVIDENCE")
    tracked_required = set(tracked).intersection(required)
    if tracked_required != set(required) - set(_MISSING_SEQUENCE_OWNER_BY_SHA_V1):
        _fail("TRACKED_COMPONENT_SEQUENCE_COVERAGE_INVALID")
    complete = dict(tracked)
    _merge_sequence_evidence_v1(complete, carrier, reason="COMPLETE_SEQUENCE_EVIDENCE")
    if not set(required).issubset(complete):
        _fail("COMPONENT_SEQUENCE_COVERAGE_INCOMPLETE")
    return (
        {sequence_sha: complete[sequence_sha] for sequence_sha in sorted(required)},
        group_count,
        len(required),
    )


def _component_axis_references_v1(
    registry: Mapping[str, Any], *, reason: str,
    protein_sequence_by_sha: Mapping[str, str],
) -> list[Mapping[str, Any]]:
    rows = registry.get("components")
    if type(rows) is not list:
        _fail(reason + ":COMPONENTS_INVALID")
    field_by_axis = {
        "LIGAND_GRAPH": "ligand_graph_sha256",
        "LIGAND_SCAFFOLD": "ligand_scaffold_sha256",
        "PROTEIN_ACCESSION": "protein_accession",
        "PROTEIN_EXACT_SEQUENCE": "protein_sequence_sha256",
    }
    references: list[Mapping[str, Any]] = []
    for row in rows:
        if type(row) is not dict:
            _fail(reason + ":COMPONENT_INVALID")
        axes = row.get("source_evidence_linking_axis_values")
        if type(axes) is not list or not axes:
            _fail(reason + ":AXIS_INVENTORY_INVALID")
        for value in axes:
            if type(value) is not str:
                _fail(reason + ":AXIS_VALUE_INVALID")
            axis, separator, observed = value.partition(":")
            field = field_by_axis.get(axis)
            if not separator or not observed or field is None:
                continue
            evidence = {
                "ligand_graph_sha256": "",
                "ligand_scaffold_sha256": "",
                "protein_accession": "",
                "protein_sequence_sha256": "",
                "protein_sequence": "",
            }
            evidence[field] = observed
            if axis == "PROTEIN_EXACT_SEQUENCE":
                sequence = protein_sequence_by_sha.get(observed)
                if type(sequence) is not str or not sequence:
                    _fail(reason + ":RAW_SEQUENCE_MISSING")
                evidence["protein_sequence"] = sequence
            references.append({
                "identity": f"{reason}:{row.get('formal_group_id')}:{axis}:{observed}",
                "leakage_key": row.get("leakage_key"),
                "group_id": row.get("formal_group_id"),
                "split": row.get("formal_split"),
                "evidence": evidence,
            })
    if not references:
        _fail(reason + ":NO_COMPARABLE_AXIS_REFERENCE")
    return references


def _bulk_current_references_v1(
    payload: bytes,
    groups: Sequence[split_owner.LeakageGroupAssignmentV1],
) -> list[Mapping[str, Any]]:
    parsed = _json(payload, "CURRENT_LINKING_AXIS_REFERENCE_EVIDENCE")
    events = parsed.get("events") if type(parsed) is dict else None
    if (
        type(parsed) is not dict
        or parsed.get("schema_version")
        != "covapie_bulk_multisource_cys_sg_dataset_expansion_v1"
        or type(events) is not list
    ):
        _fail("CURRENT_LINKING_AXIS_REFERENCE_SCHEMA_INVALID")
    direct_groups = [
        group for group in groups
        if group.final_leakage_group_id not in _COMPONENT_REGISTRY_GROUP_IDS_V1
    ]
    identity_owner = {
        identity: group
        for group in direct_groups
        for identity in group.member_identities
    }
    found: set[str] = set()
    references: list[Mapping[str, Any]] = []
    signatures: set[tuple[str, str, str, str, str, str]] = set()
    for row in events:
        if type(row) is not dict:
            _fail("CURRENT_LINKING_AXIS_EVENT_INVALID")
        identity = f"{row.get('pdb_id', '')}/{row.get('ligand_component_id', '')}"
        group = identity_owner.get(identity)
        if group is None:
            continue
        structural = row.get("structural_processing")
        evidence = structural.get("leakage_evidence") if type(structural) is dict else None
        if type(evidence) is not dict or evidence.get("complete") is not True:
            continue
        signature = (
            group.final_leakage_group_id,
            str(evidence.get("ligand_graph_sha256", "")),
            str(evidence.get("ligand_scaffold_sha256", "")),
            str(evidence.get("protein_accession", "")),
            str(evidence.get("protein_sequence_sha256", "")),
            str(evidence.get("protein_sequence", "")),
        )
        found.add(identity)
        if signature in signatures:
            continue
        signatures.add(signature)
        references.append({
            "identity": identity,
            "leakage_key": group.leakage_key,
            "group_id": group.final_leakage_group_id,
            "split": group.assigned_split,
            "evidence": evidence,
        })
    if found != set(identity_owner):
        _fail("CURRENT_LINKING_AXIS_IDENTITY_COVERAGE_INCOMPLETE")
    return references


def _detect_cross_link_conflicts_v1(
    component: _POAComponentEvidenceV1,
    groups: Sequence[split_owner.LeakageGroupAssignmentV1],
    *,
    bulk_processing_payload: bytes,
    batch_registry: Mapping[str, Any],
    ndu_registry: Mapping[str, Any],
    protein_sequence_by_sha: Mapping[str, str],
    sequence_reference_group_count: int,
    sequence_reference_sequence_count: int,
    extra_references: Sequence[Mapping[str, Any]] = (),
) -> tuple[tuple[Mapping[str, Any], ...], _SequenceIdentityAuditV1]:
    existing_members = {
        identity for group in groups for identity in group.member_identities
    }
    existing_keys = {group.leakage_key for group in groups}
    existing_ids = {group.final_leakage_group_id for group in groups}
    if existing_members.intersection(component.identities):
        _fail("POA_IDENTITY_COLLIDES_WITH_FROZEN_GROUP")
    if component.leakage_key in existing_keys:
        _fail("POA_LEAKAGE_KEY_COLLIDES_WITH_FROZEN_GROUP")
    if component.read_only_group_id in existing_ids:
        _fail("POA_GROUP_ID_COLLIDES_WITH_FROZEN_GROUP")

    registry_axis_values: set[str] = set()
    for registry, reason in (
        (batch_registry, "BATCH001_LINKING_AXIS_REFERENCE"),
        (ndu_registry, "NDU_LINKING_AXIS_REFERENCE"),
    ):
        rows = registry.get("components")
        if type(rows) is not list:
            _fail(reason + ":COMPONENTS_INVALID")
        for row in rows:
            values = row.get("source_evidence_linking_axis_values") if type(row) is dict else None
            if type(values) is not list or not values:
                _fail(reason + ":AXIS_INVENTORY_INVALID")
            registry_axis_values.update(str(value) for value in values)
    if registry_axis_values.intersection(component.component_axis_values):
        _fail("POA_COMPONENT_AXIS_VALUE_COLLIDES_WITH_FROZEN_COMPONENT")

    references = _bulk_current_references_v1(bulk_processing_payload, groups)
    references.extend(_component_axis_references_v1(
        batch_registry, reason="BATCH001_LINKING_AXIS_REFERENCE",
        protein_sequence_by_sha=protein_sequence_by_sha,
    ))
    references.extend(_component_axis_references_v1(
        ndu_registry, reason="NDU_LINKING_AXIS_REFERENCE",
        protein_sequence_by_sha=protein_sequence_by_sha,
    ))
    frozen_reference_group_ids = {
        reference.get("group_id") for reference in references
    }
    if frozen_reference_group_ids != existing_ids:
        _fail("FROZEN_REFERENCE_GROUP_COVERAGE_INCOMPLETE")
    references.extend(extra_references)
    conflicts: list[Mapping[str, Any]] = []
    comparison_count = 0
    sequence_identity_comparison_count = 0
    raw_sequence_reference_count = 0
    for reference in references:
        evidence = reference.get("evidence")
        if not isinstance(evidence, Mapping):
            _fail("CROSS_LINK_REFERENCE_EVIDENCE_INVALID")
        if evidence.get("protein_sequence"):
            raw_sequence_reference_count += 1
    for event_id, evidence in component.evidence_by_event:
        for reference in references:
            reference_evidence = reference.get("evidence")
            if not isinstance(reference_evidence, Mapping):
                _fail("CROSS_LINK_REFERENCE_EVIDENCE_INVALID")
            comparison_count += 1
            if evidence.get("protein_sequence") and reference_evidence.get("protein_sequence"):
                sequence_identity_comparison_count += 1
            axes = bulk_owner._leakage_linking_axes_v1(evidence, reference_evidence)
            if axes:
                conflicts.append({
                    "poa_event_id": event_id,
                    "existing_identity": reference.get("identity"),
                    "existing_leakage_key": reference.get("leakage_key"),
                    "existing_group_id": reference.get("group_id"),
                    "existing_split": reference.get("split"),
                    "linking_axes": tuple(axes),
                })
    normalized = tuple(sorted(conflicts, key=lambda item: (
        str(item["poa_event_id"]), str(item["existing_group_id"]),
        str(item["existing_identity"]), tuple(item["linking_axes"]),
    )))
    if (
        sequence_reference_group_count != 5
        or sequence_reference_sequence_count != 15
        or raw_sequence_reference_count < sequence_reference_sequence_count
        or sequence_identity_comparison_count <= 0
    ):
        _fail("SEQUENCE_IDENTITY_AUDIT_COVERAGE_INVALID")
    return normalized, _SequenceIdentityAuditV1(
        frozen_reference_group_count=len(frozen_reference_group_ids),
        reference_group_count=sequence_reference_group_count,
        reference_sequence_count=sequence_reference_sequence_count,
        reference_count=len(references),
        raw_sequence_reference_count=raw_sequence_reference_count,
        comparison_count=comparison_count,
        sequence_identity_comparison_count=sequence_identity_comparison_count,
    )


def _population_summary_v1(
    groups: Sequence[split_owner.LeakageGroupAssignmentV1],
) -> POAFullComponentFormalSplitSummaryV1:
    group_counts = Counter(group.assigned_split for group in groups)
    identity_counts = Counter()
    for group in groups:
        identity_counts[group.assigned_split] += group.member_count
    return POAFullComponentFormalSplitSummaryV1(
        group_count=len(groups),
        identity_count=sum(group.member_count for group in groups),
        train_group_count=group_counts["train"],
        validation_group_count=group_counts["validation"],
        test_group_count=group_counts["test"],
        train_identity_count=identity_counts["train"],
        validation_identity_count=identity_counts["validation"],
        test_identity_count=identity_counts["test"],
    )


def _formal_group_id_from_key_v1(leakage_key: str) -> str:
    digest = _sha256(_canonical_json_bytes({
        "policy": "conservative_union_final_leakage_group_v1",
        "leakage_key": leakage_key,
    }))[:16].upper()
    return "COVAPIE_EXPANSION_LEAKAGE_GROUP_" + digest


def _independent_poa_oracle_v1(
    candidates: Sequence[Any],
    *, existing_groups: Sequence[split_owner.LeakageGroupAssignmentV1],
) -> POAFullComponentFormalSplitOracleV1:
    """Independently enumerate 3^1 without calling the generic owner."""

    existing = _validate_frozen_groups_v1(existing_groups)
    identity_to_key: dict[str, str] = {}
    members_by_key: dict[str, set[str]] = {}
    for candidate in candidates:
        identity = getattr(candidate, "candidate_identity", None)
        key = getattr(candidate, "leakage_key", None)
        if (
            type(identity) is not str
            or _IDENTITY_V1.fullmatch(identity) is None
            or type(key) is not str
            or not key
            or (identity in identity_to_key and identity_to_key[identity] != key)
        ):
            _fail("ORACLE_CANDIDATE_INVALID")
        identity_to_key[identity] = key
        members_by_key.setdefault(key, set()).add(identity)
    if set(identity_to_key) != set(POA_IDENTITIES_V1) or set(members_by_key) != {POA_LEAKAGE_KEY_V1}:
        _fail("ORACLE_REQUIRES_EXACT_POA_IDENTITY_COMPONENT")
    prior_members = {
        identity for group in existing for identity in group.member_identities
    }
    if prior_members.intersection(identity_to_key):
        _fail("ORACLE_CANDIDATE_COLLIDES_WITH_EXISTING_MEMBER")

    groups: list[dict[str, Any]] = [{
        "key": group.leakage_key,
        "id": group.final_leakage_group_id,
        "member_count": group.member_count,
        "fixed_rank": _RANK_V1[group.assigned_split],
    } for group in existing]
    groups.append({
        "key": POA_LEAKAGE_KEY_V1,
        "id": _formal_group_id_from_key_v1(POA_LEAKAGE_KEY_V1),
        "member_count": len(members_by_key[POA_LEAKAGE_KEY_V1]),
        "fixed_rank": None,
    })
    groups.sort(key=lambda item: item["id"])
    new_index = next(
        index for index, item in enumerate(groups)
        if item["key"] == POA_LEAKAGE_KEY_V1
    )
    total_samples = sum(int(item["member_count"]) for item in groups)
    group_count = len(groups)
    valid: list[
        tuple[tuple[Any, ...], tuple[int, int, int], tuple[int, int, int]]
    ] = []
    for ranks in product(range(3), repeat=1):
        signature = tuple(
            ranks[0] if item["fixed_rank"] is None else item["fixed_rank"]
            for item in groups
        )
        sample_counts = tuple(sum(
            int(item["member_count"])
            for item, assigned_rank in zip(groups, signature)
            if assigned_rank == split_rank
        ) for split_rank in range(3))
        group_counts = tuple(signature.count(split_rank) for split_rank in range(3))
        if (
            min(group_counts) < 1
            or sample_counts[0] < sample_counts[1]
            or sample_counts[0] < sample_counts[2]
        ):
            continue
        pre_signature = (
            sum(abs(
                Fraction(sample_counts[index])
                - _TARGET_V1[_SPLITS_V1[index]] * total_samples
            ) for index in range(3)),
            max(abs(
                Fraction(sample_counts[index])
                - _TARGET_V1[_SPLITS_V1[index]] * total_samples
            ) for index in range(3)),
            sum(abs(
                Fraction(group_counts[index])
                - _TARGET_V1[_SPLITS_V1[index]] * group_count
            ) for index in range(3)),
        )
        valid.append((pre_signature + (signature,), sample_counts, group_counts))
    if not valid:
        _fail("ORACLE_NO_VALID_ASSIGNMENT")
    selected = min(valid, key=lambda item: item[0])
    selected_signature = selected[0][3]
    best_pre_signature = selected[0][:3]
    tied_signatures = [
        item[0][3] for item in valid if item[0][:3] == best_pre_signature
    ]
    assignment = tuple(sorted((
        str(item["key"]), str(item["id"]),
        _SPLITS_V1[selected_signature[index]],
    ) for index, item in enumerate(groups)))
    return POAFullComponentFormalSplitOracleV1(
        candidate_assignment_count=3,
        valid_assignment_count=len(valid),
        selected_split=_SPLITS_V1[selected_signature[new_index]],
        selected_sample_counts=selected[1],
        selected_group_counts=selected[2],
        selected_objective=best_pre_signature,
        tie_count_before_signature=len(tied_signatures),
        lexicographic_tie_break_verified=(
            tuple(selected_signature) == min(tied_signatures)
        ),
        selected_assignment=assignment,
    )


def _normalized_assignment_v1(
    assignment: Mapping[str, tuple[str, str]],
) -> tuple[tuple[str, str, str], ...]:
    return tuple(sorted(
        (key, group_id, split)
        for key, (group_id, split) in assignment.items()
    ))


def _poa_candidates_v1(
    identities: Sequence[str] = POA_IDENTITIES_V1,
) -> tuple[SimpleNamespace, ...]:
    return tuple(SimpleNamespace(
        candidate_identity=identity,
        leakage_key=POA_LEAKAGE_KEY_V1,
    ) for identity in identities)


def _formal_assignment_v1(
    component: _POAComponentEvidenceV1,
    groups: Sequence[split_owner.LeakageGroupAssignmentV1],
) -> tuple[
    tuple[tuple[str, str, str], ...],
    POAFullComponentFormalSplitOracleV1,
    bool,
]:
    candidates = _poa_candidates_v1(component.identities)
    generic = _normalized_assignment_v1(
        split_owner.assign_expansion_leakage_splits_v1(
            candidates, existing_groups=groups,
        )
    )
    oracle = _independent_poa_oracle_v1(candidates, existing_groups=groups)
    parity = generic == oracle.selected_assignment
    poa_rows = [row for row in generic if row[0] == POA_LEAKAGE_KEY_V1]
    if (
        not parity
        or len(poa_rows) != 1
        or poa_rows[0][1:] != (POA_FORMAL_GROUP_ID_V1, POA_FORMAL_SPLIT_V1)
    ):
        _fail("GENERIC_OWNER_ORACLE_ASSIGNMENT_MISMATCH")
    return generic, oracle, parity


def _verify_input_order_independence_v1(
    component: _POAComponentEvidenceV1,
    groups: tuple[split_owner.LeakageGroupAssignmentV1, ...],
    expected_assignment: tuple[tuple[str, str, str], ...],
    expected_oracle: POAFullComponentFormalSplitOracleV1,
) -> bool:
    candidate_orders = (
        component.identities,
        tuple(reversed(component.identities)),
        component.identities[1:] + component.identities[:1],
    )
    group_orders = (
        groups,
        tuple(reversed(groups)),
        groups[3:] + groups[:3],
    )
    for identities in candidate_orders:
        for ordered_groups in group_orders:
            candidates = _poa_candidates_v1(identities)
            generic = _normalized_assignment_v1(
                split_owner.assign_expansion_leakage_splits_v1(
                    candidates, existing_groups=ordered_groups,
                )
            )
            oracle = _independent_poa_oracle_v1(
                candidates, existing_groups=ordered_groups,
            )
            if generic != expected_assignment or oracle != expected_oracle:
                _fail("INPUT_ORDER_DEPENDENCE_DETECTED")
    return True


def _source_bindings_from_payloads_v1(
    payloads: Mapping[str, bytes],
) -> tuple[POAFullComponentFormalSplitSourceBindingV1, ...]:
    if type(payloads) is not dict or set(payloads) != set(_SOURCE_SHA_BY_PATH_V1):
        _fail("SOURCE_PAYLOAD_INVENTORY_INVALID")
    bindings = []
    for role, path, expected_sha in _SOURCE_SPECS_V1:
        payload = payloads.get(path)
        if type(payload) is not bytes or _sha256(payload) != expected_sha:
            _fail("SOURCE_SHA256_MISMATCH:" + path)
        bindings.append(POAFullComponentFormalSplitSourceBindingV1(
            artifact_role=role,
            repository_relative_path=path,
            byte_count=len(payload),
            sha256=expected_sha,
        ))
    return tuple(bindings)


def _build_from_bound_payloads_v1(
    payloads: Mapping[str, bytes],
) -> POAFullComponentFormalSplitAuthorityResultV1:
    bindings = _source_bindings_from_payloads_v1(payloads)
    component = _extract_poa_component_v1(payloads[_PROCESSING_VIEW_V1])
    groups, batch_registry, ndu_registry = _reconstruct_frozen_groups_v1(payloads)
    sequence_evidence, sequence_group_count, sequence_count = (
        _complete_component_sequence_evidence_v1(
            processing_view_payload=payloads[_PROCESSING_VIEW_V1],
            bulk_processing_payload=payloads[_BULK_PROCESSING_V1],
            carrier_payload=payloads[_MISSING_SEQUENCE_EVIDENCE_V1],
            batch_registry=batch_registry,
            ndu_registry=ndu_registry,
        )
    )
    conflicts, sequence_audit = _detect_cross_link_conflicts_v1(
        component,
        groups,
        bulk_processing_payload=payloads[_BULK_PROCESSING_V1],
        batch_registry=batch_registry,
        ndu_registry=ndu_registry,
        protein_sequence_by_sha=sequence_evidence,
        sequence_reference_group_count=sequence_group_count,
        sequence_reference_sequence_count=sequence_count,
    )
    if conflicts:
        _fail("POA_CROSS_LINK_CONFLICT_DETECTED")
    generic, oracle, parity = _formal_assignment_v1(component, groups)
    order_independent = _verify_input_order_independence_v1(
        component, groups, generic, oracle,
    )
    poa_group = split_owner.LeakageGroupAssignmentV1(
        leakage_key=POA_LEAKAGE_KEY_V1,
        final_leakage_group_id=POA_FORMAL_GROUP_ID_V1,
        member_count=3,
        assigned_split=POA_FORMAL_SPLIT_V1,
        frozen=True,
        member_identities=POA_IDENTITIES_V1,
    )
    exact16 = tuple(
        event_id for event_id in component.event_ids
        if _identity_from_event_id_v1(event_id) in POA_IDENTITIES_V1[:2]
    )
    external = tuple(
        event_id for event_id in component.event_ids
        if _identity_from_event_id_v1(event_id) == POA_IDENTITIES_V1[2]
    )
    records = tuple(POAFullComponentFormalSplitRecordV1(
        canonical_event_id=event_id,
        pdb_ligand_identity=_identity_from_event_id_v1(event_id),
        formal_leakage_group_id=POA_FORMAL_GROUP_ID_V1,
        formal_split=POA_FORMAL_SPLIT_V1,
        formal_split_authoritative=True,
        sample_training_admitted=False,
        model_training_activation_authorized=False,
    ) for event_id in component.event_ids)
    result = POAFullComponentFormalSplitAuthorityResultV1(
        source_bindings=bindings,
        leakage_classification=component.classification,
        leakage_key=component.leakage_key,
        full_component_group_id=component.read_only_group_id,
        full_member_pdb_ligand_identities=component.identities,
        full_member_canonical_event_ids=component.event_ids,
        canonical_event_inventory_sha256=POA_CANONICAL_EVENT_INVENTORY_SHA256_V1,
        linking_axes=component.linking_axes,
        exact16_event_ids=exact16,
        external_g3h_event_ids=external,
        read_only_predicted_split=component.read_only_split,
        read_only_prediction_is_authority=False,
        read_only_prediction_copied_as_formal_authority=False,
        formal_group_id=POA_FORMAL_GROUP_ID_V1,
        formal_split=POA_FORMAL_SPLIT_V1,
        formal_split_authoritative=True,
        records=records,
        existing_frozen_groups_before=groups,
        existing_frozen_groups_after=groups,
        frozen_inventory_sha256=POA_FROZEN14_INVENTORY_SHA256_V1,
        before_summary=_population_summary_v1(groups),
        after_summary=_population_summary_v1((*groups, poa_group)),
        generic_owner_assignment=generic,
        independent_oracle=oracle,
        generic_owner_oracle_parity=parity,
        input_order_independence_verified=order_independent,
        existing_frozen_splits_changed=False,
        cross_split_leakage_conflict=False,
        cross_link_conflict_authoritatively_proven=True,
        cross_link_reference_group_count=(
            sequence_audit.frozen_reference_group_count
        ),
        cross_link_reference_count=sequence_audit.reference_count,
        cross_link_comparison_count=sequence_audit.comparison_count,
        sequence_identity_reference_group_count=sequence_audit.reference_group_count,
        sequence_identity_reference_sequence_count=(
            sequence_audit.reference_sequence_count
        ),
        raw_sequence_reference_count=sequence_audit.raw_sequence_reference_count,
        sequence_identity_comparison_count=(
            sequence_audit.sequence_identity_comparison_count
        ),
        protein_sequence_identity_axis_cross_link_coverage_complete=True,
        randomization_used=False,
        random_seed=None,
        manual_split_override=False,
        sample_training_admitted=False,
        model_training_activation_authorized=False,
        ready_for_training=False,
    )
    validate_covapie_poa_full_component_formal_split_authority_v1(result)
    return result


def _validate_source_bindings_v1(value: object) -> None:
    if type(value) is not tuple or len(value) != len(_SOURCE_SPECS_V1):
        _fail("RESULT_SOURCE_BINDINGS_INVALID")
    for binding, (role, path, sha) in zip(value, _SOURCE_SPECS_V1):
        expected_byte_count = _SOURCE_BYTE_COUNT_BY_PATH_V1.get(path)
        if (
            type(binding) is not POAFullComponentFormalSplitSourceBindingV1
            or binding.artifact_role != role
            or binding.repository_relative_path != path
            or type(binding.byte_count) is not int
            or binding.byte_count != expected_byte_count
            or binding.sha256 != sha
        ):
            _fail("RESULT_SOURCE_BINDING_INVALID:" + path)


def _validate_result_impl_v1(result: object) -> bool:
    if type(result) is not POAFullComponentFormalSplitAuthorityResultV1:
        _fail("RESULT_TYPE_INVALID")
    _validate_source_bindings_v1(result.source_bindings)
    if (
        result.leakage_classification != POA_CLASSIFICATION_V1
        or result.leakage_key != POA_LEAKAGE_KEY_V1
        or result.full_component_group_id != POA_FORMAL_GROUP_ID_V1
        or result.full_member_pdb_ligand_identities != POA_IDENTITIES_V1
        or len(result.full_member_canonical_event_ids) != 24
        or tuple(sorted(result.full_member_canonical_event_ids))
        != result.full_member_canonical_event_ids
        or len(set(result.full_member_canonical_event_ids)) != 24
        or _sha256(_canonical_json_bytes(list(result.full_member_canonical_event_ids)))
        != POA_CANONICAL_EVENT_INVENTORY_SHA256_V1
        or result.canonical_event_inventory_sha256
        != POA_CANONICAL_EVENT_INVENTORY_SHA256_V1
        or result.linking_axes != POA_LINKING_AXES_V1
        or len(result.exact16_event_ids) != 16
        or len(result.external_g3h_event_ids) != 8
        or set(result.exact16_event_ids).intersection(result.external_g3h_event_ids)
        or set(result.exact16_event_ids) | set(result.external_g3h_event_ids)
        != set(result.full_member_canonical_event_ids)
        or any(
            _identity_from_event_id_v1(event_id) not in POA_IDENTITIES_V1[:2]
            for event_id in result.exact16_event_ids
        )
        or any(
            _identity_from_event_id_v1(event_id) != POA_IDENTITIES_V1[2]
            for event_id in result.external_g3h_event_ids
        )
    ):
        _fail("RESULT_FULL_COMPONENT_INVALID")
    if (
        result.read_only_predicted_split != POA_READ_ONLY_PREDICTED_SPLIT_V1
        or result.read_only_prediction_is_authority is not False
        or result.read_only_prediction_copied_as_formal_authority is not False
        or result.formal_group_id != POA_FORMAL_GROUP_ID_V1
        or result.formal_split != POA_FORMAL_SPLIT_V1
        or result.formal_split_authoritative is not True
    ):
        _fail("RESULT_FORMAL_SPLIT_SEMANTICS_INVALID")

    expected_record_fields = {
        "canonical_event_id", "pdb_ligand_identity", "formal_leakage_group_id",
        "formal_split", "formal_split_authoritative", "sample_training_admitted",
        "model_training_activation_authorized",
    }
    if {field.name for field in fields(POAFullComponentFormalSplitRecordV1)} != expected_record_fields:
        _fail("RECORD_CHEMISTRY_OR_EXTRA_FIELDS_EXPOSED")
    if type(result.records) is not tuple or len(result.records) != 24:
        _fail("RESULT_RECORD_COUNT_INVALID")
    for record, event_id in zip(result.records, result.full_member_canonical_event_ids):
        if (
            type(record) is not POAFullComponentFormalSplitRecordV1
            or record.canonical_event_id != event_id
            or record.pdb_ligand_identity != _identity_from_event_id_v1(event_id)
            or record.formal_leakage_group_id != POA_FORMAL_GROUP_ID_V1
            or record.formal_split != POA_FORMAL_SPLIT_V1
            or record.formal_split_authoritative is not True
            or record.sample_training_admitted is not False
            or record.model_training_activation_authorized is not False
        ):
            _fail("RESULT_EVENT_FORMAL_SPLIT_RECORD_INVALID")

    before = _validate_frozen_groups_v1(result.existing_frozen_groups_before)
    after = _validate_frozen_groups_v1(result.existing_frozen_groups_after)
    if (
        before != after
        or result.frozen_inventory_sha256 != POA_FROZEN14_INVENTORY_SHA256_V1
        or _frozen_inventory_sha256_v1(before) != result.frozen_inventory_sha256
        or result.existing_frozen_splits_changed is not False
    ):
        _fail("RESULT_EXISTING_FROZEN_GROUPS_CHANGED")
    expected_before = POAFullComponentFormalSplitSummaryV1(
        group_count=14,
        identity_count=45,
        train_group_count=5,
        validation_group_count=5,
        test_group_count=4,
        train_identity_count=23,
        validation_identity_count=5,
        test_identity_count=17,
    )
    expected_after = POAFullComponentFormalSplitSummaryV1(
        group_count=15,
        identity_count=48,
        train_group_count=6,
        validation_group_count=5,
        test_group_count=4,
        train_identity_count=26,
        validation_identity_count=5,
        test_identity_count=17,
    )
    if result.before_summary != expected_before or result.after_summary != expected_after:
        _fail("RESULT_POPULATION_SUMMARY_INVALID")

    expected_existing_assignment = tuple(sorted((
        group.leakage_key, group.final_leakage_group_id, group.assigned_split,
    ) for group in before))
    expected_assignment = tuple(sorted((
        *expected_existing_assignment,
        (POA_LEAKAGE_KEY_V1, POA_FORMAL_GROUP_ID_V1, POA_FORMAL_SPLIT_V1),
    )))
    oracle = result.independent_oracle
    if (
        result.generic_owner_assignment != expected_assignment
        or type(oracle) is not POAFullComponentFormalSplitOracleV1
        or oracle.candidate_assignment_count != 3
        or oracle.valid_assignment_count != 3
        or oracle.selected_split != "train"
        or oracle.selected_sample_counts != (26, 5, 17)
        or oracle.selected_group_counts != (6, 5, 4)
        or oracle.selected_objective
        != (Fraction(98, 5), Fraction(49, 5), Fraction(9, 1))
        or oracle.tie_count_before_signature != 1
        or oracle.lexicographic_tie_break_verified is not True
        or oracle.selected_assignment != expected_assignment
        or result.generic_owner_oracle_parity is not True
        or result.input_order_independence_verified is not True
    ):
        _fail("RESULT_GENERIC_OWNER_ORACLE_INVALID")
    if (
        result.cross_split_leakage_conflict is not False
        or result.cross_link_conflict_authoritatively_proven is not True
        or type(result.cross_link_reference_group_count) is not int
        or result.cross_link_reference_group_count != 14
        or type(result.cross_link_reference_count) is not int
        or result.cross_link_reference_count != 64
        or type(result.cross_link_comparison_count) is not int
        or result.cross_link_comparison_count != 1536
        or type(result.sequence_identity_reference_group_count) is not int
        or result.sequence_identity_reference_group_count != 5
        or type(result.sequence_identity_reference_sequence_count) is not int
        or result.sequence_identity_reference_sequence_count != 15
        or type(result.raw_sequence_reference_count) is not int
        or result.raw_sequence_reference_count != 33
        or type(result.sequence_identity_comparison_count) is not int
        or result.sequence_identity_comparison_count != 792
        or result.protein_sequence_identity_axis_cross_link_coverage_complete
        is not True
        or result.randomization_used is not False
        or result.random_seed is not None
        or result.manual_split_override is not False
        or result.sample_training_admitted is not False
        or result.model_training_activation_authorized is not False
        or result.ready_for_training is not False
    ):
        _fail("RESULT_SAFETY_BOUNDARY_INVALID")
    return True


def validate_covapie_poa_full_component_formal_split_authority_v1(
    result: object,
) -> bool:
    """Fail closed unless ``result`` is the exact V1 formal split authority."""

    try:
        return _validate_result_impl_v1(result)
    except POAFullComponentFormalSplitAuthorityError:
        raise
    except Exception as error:
        raise POAFullComponentFormalSplitAuthorityError(
            f"{COVAPIE_POA_FULL_COMPONENT_FORMAL_SPLIT_AUTHORITY_V1_ERROR}:"
            f"VALIDATION_REJECTED:{type(error).__name__}:{error}"
        ) from error


def build_covapie_poa_full_component_formal_split_authority_v1(
    *, repo_root: Path,
) -> POAFullComponentFormalSplitAuthorityResultV1:
    """Build from SHA-bound committed repository artifacts only."""

    try:
        repo = _require_repo_root(repo_root)
        payloads, observed_bindings = _read_bound_sources_v1(repo)
        result = _build_from_bound_payloads_v1(payloads)
        if result.source_bindings != observed_bindings:
            _fail("OBSERVED_SOURCE_BINDING_PARITY_INVALID")
        return result
    except POAFullComponentFormalSplitAuthorityError:
        raise
    except Exception as error:
        raise POAFullComponentFormalSplitAuthorityError(
            f"{COVAPIE_POA_FULL_COMPONENT_FORMAL_SPLIT_AUTHORITY_V1_ERROR}:"
            f"BUILD_REJECTED:{type(error).__name__}:{error}"
        ) from error
