"""Standalone masked-conditional VLB/NLL evaluator for formal validation4 V1.

The primary metric is a conditional likelihood over the supplied Current11
active mask.  It is not the training L2 objective and it deliberately excludes
the historical ligand-node prior.  Task 4 additionally exposes the historical
joint-NLL boundary diagnostic with the full-ligand node prior.
"""

from __future__ import annotations

import contextlib
import csv
from dataclasses import dataclass, fields
import hashlib
import io
import json
import math
from pathlib import Path
import stat
import time
from typing import Mapping, NoReturn, Sequence

import torch
import torch.nn.functional as F
from torch import nn
from torch_scatter import scatter_add, scatter_mean

from covalent_ext.biopython_compat import (
    patch_biopython_polypeptide_three_to_one,
)


patch_biopython_polypeptide_three_to_one()

from covalent_ext import (
    covapie_batch001_positive_structural_input_v1 as structural_owner,
)
from covalent_ext import (
    covapie_batch001_to_existing_mixed_profile_supervision_bridge_v1
    as preview_owner,
)
from covalent_ext import covapie_current11_checkpoint_migration_v1 as migration_owner
from covalent_ext.covapie_current11_auxiliary_model_and_loss_v1 import (
    CovapieCurrent11AuxiliaryModelV1,
)
from covalent_ext.covapie_current11_training_lightning_module_v1 import (
    run_covapie_current11_functional_dynamics_with_hidden_v1,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CANONICAL_TASKS_V1,
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


__all__ = (
    "FORMAL_VALIDATION4_MASKED_VLB_NLL_ERROR_V1",
    "PRIMARY_METRIC_NAME_V1",
    "HISTORICAL_JOINT_DIAGNOSTIC_NAME_V1",
    "FORMAL_VALIDATION_EVENT_IDS_V1",
    "FORMAL_VALIDATION_ROOT_SEEDS_V1",
    "FormalValidationEstimateV1",
    "FormalValidationEventTaskMeanV1",
    "FormalValidationEventMeanV1",
    "FormalValidation4MaskedVlbNllResultV1",
    "ValidationKeyedDrawV1",
    "coordinate_dimension_for_masked_likelihood_v1",
    "derive_formal_validation_child_seed_v1",
    "build_formal_validation_keyed_draw_v1",
    "masked_active_epsilon_error_v1",
    "historical_eval_loss_t_v1",
    "masked_t0_coordinate_loss_v1",
    "masked_gaussian_coordinate_constant_loss_v1",
    "masked_normalization_delta_log_px_v1",
    "compose_masked_conditional_vlb_nll_v1",
    "validate_formal_evaluation_module_state_v1",
    "run_covapie_current11_formal_validation4_masked_vlb_nll_v1",
)


FORMAL_VALIDATION4_MASKED_VLB_NLL_ERROR_V1 = (
    "COVAPIE_CURRENT11_FORMAL_VALIDATION4_MASKED_VLB_NLL_V1_ERROR"
)
PRIMARY_METRIC_NAME_V1 = "MASKED_CONDITIONAL_VLB_NLL_V1"
HISTORICAL_JOINT_DIAGNOSTIC_NAME_V1 = (
    "HISTORICAL_JOINT_NLL_WITH_NODE_PRIOR_DIAGNOSTIC_V1"
)
EXPECTED_BASELINE_HEAD_V1 = "a010f4c0f570f43f22d7a1c9403f3147f2be7c80"
CHECKPOINT_RELATIVE_PATH_V1 = Path("checkpoints/crossdocked_fullatom_cond.ckpt")
CHECKPOINT_SHA256_V1 = (
    "07f86764bf569aafbc40a9c15fc02de8e2550437dd0f17f657eab3abe66c372c"
)
MODEL_INITIALIZATION_SEED_V1 = 20260821
VALIDATION_TENSORIZATION_SENTINEL_SEED_V1 = 785270185393261049
PAIR_CONTRASTIVE_TEMPERATURE_V1 = 1.0
GEOMETRY_SMOOTH_L1_BETA_V1 = 1.0
PRIMARY_COMPONENT_WEIGHTS_METADATA_V1 = (
    ("base_diffusion", 1.0),
    ("covalent_pair_prediction", 1.0),
    ("POST_geometry_candidate", 1.0),
    ("covalent_pair_contrastive", 0.1),
)

FORMAL_VALIDATION_EVENT_IDS_V1 = (
    "COVAPIE_CYS_SG_EVENT_V1:3I4A:A:CYS:274-:SG:C:LN5:CZ",
    "COVAPIE_CYS_SG_EVENT_V1:3I4A:B:CYS:274-:SG:D:LN5:CZ",
    "COVAPIE_CYS_SG_EVENT_V1:3O6T:A:CYS:37-:SG:E:PX5:C15",
    "COVAPIE_CYS_SG_EVENT_V1:3O6T:C:CYS:37-:SG:G:PX5:C15",
)
FORMAL_TRAIN_EVENT_IDS_V1 = (
    "COVAPIE_CYS_SG_EVENT_V1:3LOK:A:CYS:345-:SG:C:DJK:C51",
    "COVAPIE_CYS_SG_EVENT_V1:3LOK:B:CYS:345-:SG:D:DJK:C51",
    "COVAPIE_CYS_SG_EVENT_V1:2ZK1:A:CYS:285-:SG:C:PTG:C8",
    "COVAPIE_CYS_SG_EVENT_V1:2ZK1:B:CYS:285-:SG:D:PTG:C8",
    "COVAPIE_CYS_SG_EVENT_V1:2ZK2:A:CYS:285-:SG:D:PTG:C8",
)
FORMAL_VALIDATION_ROOT_SEEDS_V1 = (
    5475773696358545661,
    4502185737657980518,
    4471455199196535378,
    4502278954409160509,
)
FORMAL_LEAKAGE_GROUPS_V1 = (
    ("DJK", "COVAPIE_EXPANSION_LEAKAGE_GROUP_B603B4C07705F93D", "train"),
    ("PTG", "COVAPIE_EXPANSION_LEAKAGE_GROUP_3157B39692D4D3EA", "train"),
    ("LN5", "COVAPIE_EXPANSION_LEAKAGE_GROUP_8B76795E5CE26D95", "validation"),
    ("PX5", "COVAPIE_EXPANSION_LEAKAGE_GROUP_AD79B40D8A505F37", "validation"),
)
PROFILE_TASK_MATRIX_V1 = (
    ("STRICT_LINKER_PRESENT", (0, 1, 2, 3, 4)),
    ("DIRECT_ATTACHMENT_OPTIONAL_LINKER", (0, 3, 4)),
)
TASK_TO_GENERATED_ROLES_V1 = tuple(
    (int(task[0]), str(task[1]), str(task[2]), tuple(task[3]))
    for task in CANONICAL_TASKS_V1
)

FORMAL_SPLIT_RELATIVE_PATH_V1 = Path(
    "data/derived/covalent_small/"
    "covapie_batch001_formal_split_leakage_admission_v1/"
    "covapie_batch001_formal_event_split_admission_v1.csv"
)
FORMAL_REGISTRY_RELATIVE_PATH_V1 = FORMAL_SPLIT_RELATIVE_PATH_V1.parent / (
    "covapie_batch001_formal_leakage_component_registry_v1.json"
)
STRUCTURAL_EVIDENCE_RELATIVE_PATH_V1 = Path(
    "data/derived/covalent_small/"
    "covapie_batch001_to_existing_mixed_profile_supervision_bridge_v1/"
    "covapie_batch001_model_bound_structural_evidence_v1.json"
)

# Every directly consumed semantic owner and published artifact is bound to the
# current a010f4c tree.  Transitive structural payloads are independently bound
# again by the published structural owner before it returns any record.
BOUND_SOURCE_AND_ARTIFACT_SHA256_V1 = (
    ("src/covalent_ext/covapie_current11_training_lightning_module_v1.py", "d3d21b920785f791652cb456465a8bb375a09cdf0e24e5e84415b01f82cd6485"),
    ("src/covalent_ext/covapie_current11_auxiliary_model_and_loss_v1.py", "5bf91b3af56ec0e5c2dec3ebb13e56695ca74c17bbbbb65f35e8d9249d6fc60f"),
    ("src/covalent_ext/covapie_current11_training_tensorizer_v1.py", "9fdc3f7f101fab5e5e5452e3d8e9f9b0b1e6e5fa8254a261f36310a1dfd0b606"),
    ("src/covalent_ext/covapie_batch001_positive_structural_input_v1.py", "c4cada3c5d3e8e86176b097cc5546854122162055437e4667288ba2f82629067"),
    ("src/covalent_ext/covapie_batch001_to_existing_mixed_profile_supervision_bridge_v1.py", "168c819e0422b110880676c1a99b82a8531e94f9849a3dcfb7d4c45dbdd73400"),
    ("src/covalent_ext/covapie_batch001_formal_split_leakage_admission_v1.py", "9841cb03ef67a6e8bbcffe1cbe0d7332a575da0e2ce5e3208a965afa45ad0d0c"),
    ("src/covalent_ext/covapie_current11_checkpoint_migration_v1.py", "fc36fb23844e6e5d2be2e1e43fcd0afe580d8b86faacca31bd69b8fe70f75ef3"),
    ("src/covalent_ext/covapie_current11_checkpoint_migration_and_real_one_batch_train_path_smoke_v1.py", "e92d68fc7126eb2c3e20341ad1a3ae3dd48509533761694c482edca01d70df61"),
    ("src/covalent_ext/checkpoint_compatible_model_instantiation.py", "dfd9957465460f66bc08ac12c264040fae0e2a300eb7359929c780dfa85d3024"),
    ("src/covalent_ext/diffsbdd_model_instantiation.py", "5bc98bad19bad27a4260ce01d68194fbfe46096bd3955b7ff5e5efa4c70d5613"),
    ("src/covalent_ext/covapie_current11_task2_lightning_module_v1.py", "38ed7a2b272520720935021782547f01d1d2cf36b636ce7319e6751fb54dcd98"),
    ("src/covalent_ext/covapie_direct_attachment_optional_linker_runtime_v1.py", "434285a43fa0158e62d40f48ed95d137f5fd68ea9b00101cc20674025849c535"),
    ("src/covalent_ext/covapie_tensor_label_and_loss_mask_contract_design_v1.py", "3d2d03cda56dfb4a54370444f255f9bb0ab433aaeb837901e769098272ff51ac"),
    ("src/covalent_ext/covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1.py", "1d80862e7c4fa3215ac3f307a45ce3bc8f1e0d4613728133a0ea3118df2df241"),
    ("src/covalent_ext/covapie_bulk_cys_sg_dataset_expansion_v1.py", "ef17777a634284a94662ac3277c02a7fb4efa20375d84fcf88ac074c61e69ce0"),
    ("src/covalent_ext/biopython_compat.py", "629cb43f889cff04e1aaf4ffa228c4e4c158f1b07845ed0ac9456a40645dc975"),
    ("equivariant_diffusion/conditional_model.py", "a61dc44f376b3efc0365f558b09470f71b35dd2606c216f5abf0ba06d5a1b4a9"),
    ("equivariant_diffusion/en_diffusion.py", "46a00db84d05ea568786b99b42b1b20c448cec8a99638d162b23b59794172b10"),
    ("lightning_modules.py", "7431b5cf24d4f918df961eb97c75f2e296c8b3c523fb627063f3a6c2f08fc983"),
    (FORMAL_SPLIT_RELATIVE_PATH_V1.as_posix(), "d3416ed382e6f208f79f2285138893dde3bf627653606fed8a4c3c73666001c7"),
    (FORMAL_REGISTRY_RELATIVE_PATH_V1.as_posix(), "76e6ecae7dfde7c9e5081a0164f9a72628e4f30550e831a8f8ba5cd3d1d16544"),
    (STRUCTURAL_EVIDENCE_RELATIVE_PATH_V1.as_posix(), "cca589fa4ac372c159b2e00ba4f59a7c794e21a10f1b3fcffbd477de42cd8f2e"),
    ("src/covalent_ext/covapie_expanded_cys_sg_mixed_profile_tensorizer_v1.py", "c95bac177ba2ef1dd519bb5659cb97a8367484b1e41553be56fe3b2789ceb932"),
)

_DEFAULT_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_STATE_ROOT = _DEFAULT_REPOSITORY_ROOT.parent / "covapie-state"
_DEFAULT_CACHE_ROOT = _DEFAULT_STATE_ROOT / "bulk-multisource-cys-sg-v1/rcsb"
_PATH_TYPE = type(Path())
_RNG_NAMESPACE_V1 = b"COVAPIE_FORMAL_VALIDATION4_MASKED_VLB_NLL_V1\0"
_RNG_STAGES_V1 = frozenset(("MAIN_TIMESTEP", "MAIN_NOISE", "T0_NOISE"))


@dataclass(frozen=True)
class ValidationKeyedDrawV1:
    canonical_event_id: str
    canonical_task_id: int
    root_validation_seed: int
    main_timestep_int: int
    generated_local_indices: tuple[int, ...]
    main_generated_epsilon: torch.Tensor
    t0_generated_epsilon: torch.Tensor


@dataclass(frozen=True)
class FormalValidationEstimateV1:
    canonical_event_id: str
    pdb_id: str
    ligand_component_id: str
    formal_split: str
    leakage_group: str
    profile: str
    canonical_task_id: int
    canonical_task_name: str
    canonical_task_alias: str
    root_validation_seed: int
    main_timestep_int: int
    generated_atom_count: int
    fixed_atom_count: int
    coordinate_dimension: int
    main_active_epsilon_error: float
    SNR_weight: float
    loss_t: float
    t0_coordinate_loss: float
    t0_categorical_loss: float
    negative_log_coordinate_constant: float
    kl_prior: float
    masked_delta_log_px: float
    masked_conditional_vlb_nll: float
    task4_log_pN: float | None
    task4_historical_joint_nll_with_node_prior_diagnostic: float | None
    pair_BCE: float
    POST_geometry_loss: float
    POST_geometry_prediction_angstrom: float
    POST_geometry_target_angstrom: float
    pair_contrastive_loss: float
    PRE_geometry_valid: bool
    target_cys_sg_indicator_count: int
    pair_candidate_count: int
    fixed_ligand_clean_main: bool
    fixed_ligand_clean_t0: bool


@dataclass(frozen=True)
class FormalValidationEventTaskMeanV1:
    canonical_event_id: str
    profile: str
    canonical_task_id: int
    seed_count: int
    masked_conditional_vlb_nll: float
    pair_BCE: float
    POST_geometry_loss: float
    pair_contrastive_loss: float
    task4_historical_joint_nll_with_node_prior_diagnostic: float | None


@dataclass(frozen=True)
class FormalValidationEventMeanV1:
    canonical_event_id: str
    profile: str
    applicable_task_count: int
    masked_conditional_vlb_nll: float


@dataclass(frozen=True)
class FormalValidation4MaskedVlbNllResultV1:
    implementation_status: str
    primary_metric_name: str
    historical_joint_diagnostic_name: str
    formal_validation_event_ids: tuple[str, ...]
    formal_train_event_ids: tuple[str, ...]
    formal_leakage_groups: tuple[tuple[str, str, str], ...]
    train_validation_leakage_group_intersection_count: int
    profile_task_matrix: tuple[tuple[str, tuple[int, ...]], ...]
    root_validation_seeds: tuple[int, ...]
    formal_validation_event_count: int
    formal_validation_task_event_count: int
    formal_validation_estimate_count: int
    formal_validation_task_slice_evaluation_count: int
    main_dynamics_task_slice_call_count: int
    t0_dynamics_task_slice_call_count: int
    total_dynamics_task_slice_call_count: int
    actual_functional_dynamics_call_count: int
    per_estimate_rows: tuple[FormalValidationEstimateV1, ...]
    per_event_task_seed_means: tuple[FormalValidationEventTaskMeanV1, ...]
    per_event_means: tuple[FormalValidationEventMeanV1, ...]
    event_macro_masked_conditional_vlb_nll: float
    micro_masked_conditional_vlb_nll: float
    profile_means: tuple[tuple[str, float], ...]
    profile_balanced_masked_conditional_vlb_nll: float
    mean_pair_BCE: float
    mean_POST_geometry_loss: float
    mean_POST_geometry_prediction_angstrom: float
    mean_POST_geometry_target_angstrom: float
    mean_pair_contrastive_loss: float
    mean_task4_historical_joint_nll_with_node_prior_diagnostic: float
    migration_counts: tuple[tuple[str, int], ...]
    architecture: tuple[tuple[str, object], ...]
    parameters_unchanged: bool
    buffers_unchanged: bool
    gradient_states_unchanged: bool
    checkpoint_sha256_before: str
    checkpoint_sha256_after: str
    checkpoint_unchanged: bool
    source_bindings: tuple[tuple[str, str], ...]
    runtime_elapsed_seconds: float
    model_eval_mode_verified: bool
    ddpm_eval_mode_verified: bool
    auxiliary_eval_mode_verified: bool
    gradient_recording_disabled: bool
    metric_tensors_require_grad: bool
    all_validation_events_not_training_admitted: bool
    all_applicable_primary_metrics_finite: bool
    all_applicable_auxiliary_metrics_finite: bool
    partial_tasks_fixed_ligand_clean: bool
    partial_tasks_coordinate_dimension_exact: bool
    task4_zero_com_coordinate_dimension_exact: bool
    main_timestep_domain_exact_1_to_T: bool
    separate_t0_forward_verified: bool
    target_cys_sg_same_indicator_main_and_t0: bool
    primary_includes_log_pN: bool
    task4_historical_joint_nll_diagnostic_available: bool
    PRE_geometry_valid_count: int
    POST_geometry_valid_count: int
    pair_contrastive_temperature: float
    geometry_smooth_l1_beta: float
    current_candidate_weights_metadata: tuple[tuple[str, float], ...]
    production_geometry_weight_finalized: bool
    reaction_family_authority_consumed: bool
    optimizer_created: bool
    optimizer_step_performed: bool
    backward_performed: bool
    Trainer_used: bool
    training_performed: bool
    CPU_only: bool
    GPU_used: bool
    network_used: bool
    full_training_authorized: bool
    ready_for_lightning_validation_integration: bool
    ready_for_gpt_review: bool


@dataclass(frozen=True)
class _FormalAuthorityV1:
    validation_rows: tuple[tuple[str, str, str], ...]
    train_rows: tuple[tuple[str, str, str], ...]


@dataclass(frozen=True)
class _ValidationTraceV1:
    diffusion_epsilon_prediction_ligand: torch.Tensor
    denoised_ligand_xh: torch.Tensor
    diffusion_timestep_int: torch.Tensor
    ligand_node_hidden: torch.Tensor
    pocket_node_hidden: torch.Tensor
    clean_centered_pocket_xh: torch.Tensor
    coordinate_normalization: float


@dataclass(frozen=True)
class _SliceOutputV1:
    estimates: tuple[FormalValidationEstimateV1, ...]
    main_calls: int
    t0_calls: int
    fixed_clean: bool
    indicator_reused: bool
    tensors_require_grad: bool


class _ValidationInvariantError(Exception):
    pass


def _fail(reason: str) -> NoReturn:
    raise _ValidationInvariantError(reason)


def _public_error(error: Exception) -> NoReturn:
    if type(error) is ValueError and str(error) == FORMAL_VALIDATION4_MASKED_VLB_NLL_ERROR_V1:
        raise error
    raise ValueError(FORMAL_VALIDATION4_MASKED_VLB_NLL_ERROR_V1) from error


def _require_root(value: object, *, default: Path, reason: str) -> Path:
    path = default if value is None else value
    if type(path) is not _PATH_TYPE or not path.is_absolute():
        _fail(reason)
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise _ValidationInvariantError(reason) from error
    if resolved != path or path.is_symlink() or not path.is_dir():
        _fail(reason)
    return path


def _sha256_file(path: Path) -> str:
    try:
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            _fail("BOUND_FILE_NOT_REGULAR")
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError as error:
        raise _ValidationInvariantError("BOUND_FILE_READ_FAILED") from error


def _verify_bound_sources(repository_root: Path) -> tuple[tuple[str, str], ...]:
    actual: list[tuple[str, str]] = []
    for relative, expected in BOUND_SOURCE_AND_ARTIFACT_SHA256_V1:
        digest = _sha256_file(repository_root / relative)
        if digest != expected:
            _fail("SOURCE_SHA256_MISMATCH:" + relative)
        actual.append((relative, digest))
    return tuple(actual)


def _read_text(path: Path) -> str:
    try:
        return path.read_bytes().decode("utf-8")
    except (OSError, UnicodeError) as error:
        raise _ValidationInvariantError("BOUND_TEXT_READ_FAILED") from error


def _audit_formal_authority(repository_root: Path) -> _FormalAuthorityV1:
    try:
        rows = tuple(csv.DictReader(io.StringIO(_read_text(
            repository_root / FORMAL_SPLIT_RELATIVE_PATH_V1
        ))))
        registry = json.loads(_read_text(
            repository_root / FORMAL_REGISTRY_RELATIVE_PATH_V1
        ))
    except (csv.Error, json.JSONDecodeError) as error:
        raise _ValidationInvariantError("FORMAL_AUTHORITY_PARSE_FAILED") from error
    if (
        len(rows) != 13
        or len({row.get("canonical_event_id") for row in rows}) != 13
        or any(row.get("sample_training_admitted") != "false" for row in rows)
        or any(row.get("model_training_activation_authorized") != "false" for row in rows)
    ):
        _fail("FORMAL_AUTHORITY_POPULATION_INVALID")
    validation = tuple(
        (row["canonical_event_id"], row["ligand_component_id"], row["formal_leakage_group_id"])
        for row in rows
        if row["assigned_split"] == "validation"
        and row["split_admission_authoritative"] == "true"
    )
    train = tuple(
        (row["canonical_event_id"], row["ligand_component_id"], row["formal_leakage_group_id"])
        for row in rows
        if row["assigned_split"] == "train"
        and row["split_admission_authoritative"] == "true"
    )
    if (
        tuple(item[0] for item in validation) != FORMAL_VALIDATION_EVENT_IDS_V1
        or tuple(item[0] for item in train) != FORMAL_TRAIN_EVENT_IDS_V1
        or tuple((item[1], item[2], "validation") for item in validation[::2])
        != FORMAL_LEAKAGE_GROUPS_V1[2:]
        or set(item[2] for item in validation) & set(item[2] for item in train)
    ):
        _fail("FORMAL_SPLIT_OR_LEAKAGE_DOMAIN_INVALID")
    components = registry.get("components") if type(registry) is dict else None
    if type(components) is not list or len(components) != 4:
        _fail("FORMAL_COMPONENT_REGISTRY_INVALID")
    non_target = {
        event_id
        for component in components
        for event_id in component.get("non_target_component_event_ids", ())
    }
    if non_target & set(FORMAL_VALIDATION_EVENT_IDS_V1):
        _fail("VALIDATION_EVENT_IS_NON_TARGET_COMPONENT_MEMBER")
    return _FormalAuthorityV1(validation_rows=validation, train_rows=train)


def coordinate_dimension_for_masked_likelihood_v1(
    *, generated_atom_count: int, all_generated: bool, n_dims: int = 3,
) -> int:
    try:
        if (
            type(generated_atom_count) is not int
            or generated_atom_count <= 0
            or type(all_generated) is not bool
            or type(n_dims) is not int
            or n_dims <= 0
            or (all_generated and generated_atom_count < 2)
        ):
            _fail("COORDINATE_DIMENSION_ARGUMENT_INVALID")
        return n_dims * (generated_atom_count - int(all_generated))
    except Exception as error:
        _public_error(error)


def derive_formal_validation_child_seed_v1(
    *, canonical_event_id: str, canonical_task_id: int,
    root_validation_seed: int, stochastic_stage: str,
) -> int:
    try:
        if (
            type(canonical_event_id) is not str
            or canonical_event_id not in FORMAL_VALIDATION_EVENT_IDS_V1
            or type(canonical_task_id) is not int
            or canonical_task_id not in range(5)
            or type(root_validation_seed) is not int
            or root_validation_seed not in FORMAL_VALIDATION_ROOT_SEEDS_V1
            or stochastic_stage not in _RNG_STAGES_V1
        ):
            _fail("CHILD_SEED_DOMAIN_INVALID")
        payload = b"\0".join((
            _RNG_NAMESPACE_V1,
            canonical_event_id.encode("ascii"),
            str(canonical_task_id).encode("ascii"),
            str(root_validation_seed).encode("ascii"),
            stochastic_stage.encode("ascii"),
        ))
        return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & (2**63 - 1)
    except Exception as error:
        _public_error(error)


def build_formal_validation_keyed_draw_v1(
    *, canonical_event_id: str, canonical_task_id: int,
    root_validation_seed: int, generated_local_indices: Sequence[int],
    ligand_atom_count: int, feature_dimension: int, timesteps: int,
) -> ValidationKeyedDrawV1:
    try:
        generated = tuple(generated_local_indices)
        if (
            type(ligand_atom_count) is not int
            or type(feature_dimension) is not int
            or type(timesteps) is not int
            or ligand_atom_count <= 0
            or feature_dimension <= 0
            or timesteps <= 0
            or not generated
            or len(set(generated)) != len(generated)
            or any(type(index) is not int or index not in range(ligand_atom_count) for index in generated)
        ):
            _fail("KEYED_DRAW_SHAPE_DOMAIN_INVALID")
        timestep_generator = torch.Generator(device="cpu")
        timestep_generator.manual_seed(derive_formal_validation_child_seed_v1(
            canonical_event_id=canonical_event_id,
            canonical_task_id=canonical_task_id,
            root_validation_seed=root_validation_seed,
            stochastic_stage="MAIN_TIMESTEP",
        ))
        main_timestep = int(torch.randint(
            1, timesteps + 1, (1,), generator=timestep_generator,
        ).item())
        noises: list[torch.Tensor] = []
        for stage in ("MAIN_NOISE", "T0_NOISE"):
            generator = torch.Generator(device="cpu")
            generator.manual_seed(derive_formal_validation_child_seed_v1(
                canonical_event_id=canonical_event_id,
                canonical_task_id=canonical_task_id,
                root_validation_seed=root_validation_seed,
                stochastic_stage=stage,
            ))
            noises.append(torch.randn(
                (len(generated), feature_dimension),
                generator=generator,
                dtype=torch.float32,
            ))
        return ValidationKeyedDrawV1(
            canonical_event_id=canonical_event_id,
            canonical_task_id=canonical_task_id,
            root_validation_seed=root_validation_seed,
            main_timestep_int=main_timestep,
            generated_local_indices=generated,
            main_generated_epsilon=noises[0],
            t0_generated_epsilon=noises[1],
        )
    except Exception as error:
        _public_error(error)


def masked_gaussian_coordinate_constant_loss_v1(
    *, gamma_0: torch.Tensor, coordinate_dimensions: torch.Tensor,
) -> torch.Tensor:
    try:
        if (
            not isinstance(gamma_0, torch.Tensor)
            or not isinstance(coordinate_dimensions, torch.Tensor)
            or gamma_0.ndim not in (1, 2)
            or coordinate_dimensions.ndim != 1
            or len(gamma_0) != len(coordinate_dimensions)
            or bool((coordinate_dimensions <= 0).any().item())
        ):
            _fail("GAUSSIAN_CONSTANT_ARGUMENT_INVALID")
        return coordinate_dimensions.to(gamma_0.dtype) * (
            0.5 * gamma_0.reshape(len(gamma_0)) + 0.5 * math.log(2.0 * math.pi)
        )
    except Exception as error:
        _public_error(error)


def masked_active_epsilon_error_v1(
    *, sampled_epsilon: torch.Tensor, predicted_epsilon: torch.Tensor,
    active_mask: torch.Tensor, ligand_batch_index: torch.Tensor,
    batch_size: int,
) -> torch.Tensor:
    try:
        if (
            not isinstance(sampled_epsilon, torch.Tensor)
            or not isinstance(predicted_epsilon, torch.Tensor)
            or sampled_epsilon.shape != predicted_epsilon.shape
            or sampled_epsilon.ndim != 2
            or not isinstance(active_mask, torch.Tensor)
            or active_mask.dtype != torch.bool
            or active_mask.shape != (len(sampled_epsilon),)
            or not isinstance(ligand_batch_index, torch.Tensor)
            or ligand_batch_index.dtype != torch.long
            or ligand_batch_index.shape != active_mask.shape
            or type(batch_size) is not int
            or batch_size <= 0
        ):
            _fail("MASKED_EPSILON_ERROR_ARGUMENT_INVALID")
        row_error = (
            (sampled_epsilon - predicted_epsilon).square().sum(dim=1)
            * active_mask.to(sampled_epsilon.dtype)
        )
        return scatter_add(
            row_error, ligand_batch_index, dim=0, dim_size=batch_size,
        )
    except Exception as error:
        _public_error(error)


def historical_eval_loss_t_v1(
    *, active_epsilon_error: torch.Tensor, gamma_s: torch.Tensor,
    gamma_t: torch.Tensor, timesteps: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    try:
        if (
            not isinstance(active_epsilon_error, torch.Tensor)
            or active_epsilon_error.ndim != 1
            or not isinstance(gamma_s, torch.Tensor)
            or not isinstance(gamma_t, torch.Tensor)
            or gamma_s.shape != gamma_t.shape
            or gamma_s.numel() != len(active_epsilon_error)
            or type(timesteps) is not int
            or timesteps <= 0
        ):
            _fail("HISTORICAL_EVAL_LOSS_T_ARGUMENT_INVALID")
        snr_weight = 1.0 - torch.exp(-(gamma_s - gamma_t)).reshape(
            len(active_epsilon_error)
        )
        loss_t = -timesteps * 0.5 * snr_weight * active_epsilon_error
        return snr_weight, loss_t
    except Exception as error:
        _public_error(error)


def masked_t0_coordinate_loss_v1(
    *, sampled_epsilon: torch.Tensor, predicted_epsilon: torch.Tensor,
    active_mask: torch.Tensor, ligand_batch_index: torch.Tensor,
    batch_size: int, n_dims: int = 3,
) -> torch.Tensor:
    try:
        if type(n_dims) is not int or n_dims <= 0 or n_dims > sampled_epsilon.shape[1]:
            _fail("T0_COORDINATE_DIMENSION_INVALID")
        coordinate_error = masked_active_epsilon_error_v1(
            sampled_epsilon=sampled_epsilon[:, :n_dims],
            predicted_epsilon=predicted_epsilon[:, :n_dims],
            active_mask=active_mask,
            ligand_batch_index=ligand_batch_index,
            batch_size=batch_size,
        )
        return 0.5 * coordinate_error
    except Exception as error:
        _public_error(error)


def masked_normalization_delta_log_px_v1(
    *, coordinate_dimensions: torch.Tensor, coordinate_normalization: float,
) -> torch.Tensor:
    try:
        if (
            not isinstance(coordinate_dimensions, torch.Tensor)
            or coordinate_dimensions.ndim != 1
            or type(coordinate_normalization) is not float
            or not math.isfinite(coordinate_normalization)
            or coordinate_normalization <= 0
        ):
            _fail("NORMALIZATION_JACOBIAN_ARGUMENT_INVALID")
        return -coordinate_dimensions.to(torch.float32) * math.log(coordinate_normalization)
    except Exception as error:
        _public_error(error)


def compose_masked_conditional_vlb_nll_v1(
    *, loss_t: torch.Tensor, loss_0_x: torch.Tensor, loss_0_h: torch.Tensor,
    negative_log_coordinate_constant: torch.Tensor, kl_prior: torch.Tensor,
    masked_delta_log_px: torch.Tensor,
) -> torch.Tensor:
    try:
        values = (
            loss_t, loss_0_x, loss_0_h, negative_log_coordinate_constant,
            kl_prior, masked_delta_log_px,
        )
        if (
            any(not isinstance(value, torch.Tensor) or value.ndim != 1 for value in values)
            or len({len(value) for value in values}) != 1
        ):
            _fail("PRIMARY_COMPOSITION_ARGUMENT_INVALID")
        result = loss_t + loss_0_x + loss_0_h + negative_log_coordinate_constant + kl_prior - masked_delta_log_px
        if not bool(torch.isfinite(result).all().item()):
            _fail("PRIMARY_COMPOSITION_NONFINITE")
        return result
    except Exception as error:
        _public_error(error)


def validate_formal_evaluation_module_state_v1(*, model: nn.Module) -> bool:
    try:
        ddpm = getattr(model, "ddpm", None)
        auxiliary = getattr(model, "covapie_current11_auxiliary_model_v1", None)
        if (
            not isinstance(model, nn.Module)
            or not isinstance(ddpm, nn.Module)
            or not isinstance(auxiliary, CovapieCurrent11AuxiliaryModelV1)
            or model.training
            or ddpm.training
            or auxiliary.training
            or ddpm.dynamics.training
            or any(parameter.device.type != "cpu" for parameter in model.parameters())
            or any(buffer.device.type != "cpu" for buffer in model.buffers())
        ):
            _fail("FORMAL_EVALUATION_REQUIRES_ALREADY_EVAL_CPU_MODULES")
        return True
    except Exception as error:
        _public_error(error)


def _profile_name(record: object) -> str:
    if record.role_profile == preview_owner.STRICT_LINKER_PRESENT_V1:
        return "STRICT_LINKER_PRESENT"
    if record.role_profile == preview_owner.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1:
        return "DIRECT_ATTACHMENT_OPTIONAL_LINKER"
    _fail("ROLE_PROFILE_INVALID")


def _task_batches(
    records: tuple[object, ...],
) -> tuple[tuple[int, object], ...]:
    result: list[tuple[int, object]] = []
    for task_id in range(5):
        selected = tuple(
            record for record in records
            if task_id in record.applicable_canonical_task_ids
        )
        preview = preview_owner._tensorize_records_v1(
            records=selected,
            task_ids=(task_id,) * len(selected),
            epoch=0,
            task_schedule_seed=VALIDATION_TENSORIZATION_SENTINEL_SEED_V1,
        )
        supervision = preview.supervision
        if (
            preview.canonical_task_ids != (task_id,) * len(selected)
            or bool(supervision.sample_training_admitted.any().item())
            or bool(supervision.ligand_active_diffusion_loss_mask.any().item())
            or bool(supervision.pair_head_candidate_loss_mask.any().item())
            or bool(supervision.pair_contrastive_sample_loss_mask.any().item())
            or bool(supervision.pre_post_geometry_component_loss_mask.any().item())
        ):
            _fail("VALIDATION_TENSORIZATION_ACTIVATED_TRAINING_MASK")
        result.append((task_id, preview))
    if tuple(len(preview.sample_identities) for unused, preview in result) != (4, 2, 2, 4, 4):
        _fail("VALIDATION_TASK_EVENT_MATRIX_INVALID")
    return tuple(result)


def _build_noise_batch(
    *, preview: object, task_id: int, root_seed: int, timesteps: int,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    supervision = preview.supervision
    ligand_mask = preview.model_input_batch["lig_mask"]
    feature_dimension = 13
    main_t = torch.empty((len(preview.sample_identities), 1), dtype=torch.float32)
    main_noise = torch.zeros((len(ligand_mask), feature_dimension), dtype=torch.float32)
    t0_noise = torch.zeros_like(main_noise)
    for sample, event_id in enumerate(preview.sample_identities):
        node_indices = torch.nonzero(ligand_mask == sample).flatten()
        active_local = torch.nonzero(
            supervision.ligand_base_generation_mask[node_indices, 0]
        ).flatten().tolist()
        draw = build_formal_validation_keyed_draw_v1(
            canonical_event_id=event_id,
            canonical_task_id=task_id,
            root_validation_seed=root_seed,
            generated_local_indices=active_local,
            ligand_atom_count=len(node_indices),
            feature_dimension=feature_dimension,
            timesteps=timesteps,
        )
        active_flat = node_indices[torch.tensor(active_local, dtype=torch.long)]
        main_t[sample, 0] = draw.main_timestep_int
        main_noise[active_flat] = draw.main_generated_epsilon
        t0_noise[active_flat] = draw.t0_generated_epsilon
    return main_t, main_noise, t0_noise


def _center_clean(
    *, ddpm: nn.Module, ligand: Mapping[str, torch.Tensor],
    pocket: Mapping[str, torch.Tensor], supervision: object, task_id: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    ligand_normalized = {key: value.clone() for key, value in ligand.items()}
    pocket_normalized = {key: value.clone() for key, value in pocket.items()}
    ddpm.normalize(ligand_normalized, pocket_normalized)
    xh_ligand = torch.cat((ligand_normalized["x"], ligand_normalized["one_hot"]), dim=1)
    xh_pocket = torch.cat((pocket_normalized["x"], pocket_normalized["one_hot"]), dim=1)
    ligand_mask = ligand_normalized["mask"]
    pocket_mask = pocket_normalized["mask"]
    if task_id == 4:
        xh_ligand[:, :ddpm.n_dims], xh_pocket[:, :ddpm.n_dims] = ddpm.remove_mean_batch(
            xh_ligand[:, :ddpm.n_dims], xh_pocket[:, :ddpm.n_dims],
            ligand_mask, pocket_mask,
        )
    else:
        fixed = supervision.ligand_base_fixed_mask[:, 0]
        batch_size = len(ligand_normalized["size"])
        if not bool(fixed.any().item()):
            _fail("PARTIAL_TASK_FIXED_REFERENCE_ABSENT")
        reference = scatter_mean(
            xh_ligand[:, :ddpm.n_dims][fixed],
            ligand_mask[fixed], dim=0, dim_size=batch_size,
        )
        xh_ligand[:, :ddpm.n_dims] -= reference[ligand_mask]
        xh_pocket[:, :ddpm.n_dims] -= reference[pocket_mask]
    return xh_ligand, xh_pocket


def _assemble_noised(
    *, ddpm: nn.Module, clean_ligand: torch.Tensor,
    clean_pocket: torch.Tensor, ligand_mask: torch.Tensor,
    pocket_mask: torch.Tensor, active: torch.Tensor,
    gamma: torch.Tensor, epsilon: torch.Tensor, task_id: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    alpha = ddpm.alpha(gamma, clean_ligand)
    sigma = ddpm.sigma(gamma, clean_ligand)
    generated = alpha[ligand_mask] * clean_ligand + sigma[ligand_mask] * epsilon
    z_ligand = torch.where(active.unsqueeze(1), generated, clean_ligand)
    conditioned_pocket = clean_pocket.clone()
    if task_id == 4:
        z_ligand[:, :ddpm.n_dims], conditioned_pocket[:, :ddpm.n_dims] = ddpm.remove_mean_batch(
            z_ligand[:, :ddpm.n_dims], conditioned_pocket[:, :ddpm.n_dims],
            ligand_mask, pocket_mask,
        )
    return z_ligand, conditioned_pocket


def _masked_categorical_loss(
    *, ddpm: nn.Module, normalized_true_one_hot: torch.Tensor,
    z_ligand: torch.Tensor, gamma_0: torch.Tensor,
    active: torch.Tensor, ligand_mask: torch.Tensor, batch_size: int,
) -> torch.Tensor:
    z_h = z_ligand[:, ddpm.n_dims:]
    sigma_0 = ddpm.sigma(gamma_0, z_ligand)
    sigma_cat = sigma_0 * ddpm.norm_values[1]
    true_one_hot = normalized_true_one_hot * ddpm.norm_values[1] + ddpm.norm_biases[1]
    estimated = z_h * ddpm.norm_values[1] + ddpm.norm_biases[1]
    centered = estimated - 1.0
    log_proportional = torch.log(
        ddpm.cdf_standard_gaussian((centered + 0.5) / sigma_cat[ligand_mask])
        - ddpm.cdf_standard_gaussian((centered - 0.5) / sigma_cat[ligand_mask])
        + 1.0e-10
    )
    log_probabilities = log_proportional - torch.logsumexp(
        log_proportional, dim=1, keepdim=True,
    )
    row_log_probability = (log_probabilities * true_one_hot).sum(dim=1)
    return -scatter_add(
        row_log_probability * active.to(row_log_probability.dtype),
        ligand_mask, dim=0, dim_size=batch_size,
    )


def _masked_kl_prior(
    *, ddpm: nn.Module, clean_ligand: torch.Tensor,
    ligand_mask: torch.Tensor, active: torch.Tensor,
    coordinate_dimensions: torch.Tensor, batch_size: int,
) -> torch.Tensor:
    gamma_t = ddpm.gamma(torch.ones((batch_size, 1), dtype=clean_ligand.dtype))
    alpha_t = ddpm.alpha(gamma_t, clean_ligand)
    mu = alpha_t[ligand_mask] * clean_ligand
    mu_x, mu_h = mu[:, :ddpm.n_dims], mu[:, ddpm.n_dims:]
    active_float = active.to(mu.dtype)
    mu_norm_x = scatter_add(
        mu_x.square().sum(dim=1) * active_float,
        ligand_mask, dim=0, dim_size=batch_size,
    )
    mu_norm_h = scatter_add(
        mu_h.square().sum(dim=1) * active_float,
        ligand_mask, dim=0, dim_size=batch_size,
    )
    sigma_x = ddpm.sigma(gamma_t, mu_x).reshape(batch_size)
    sigma_h = ddpm.sigma(gamma_t, mu_h).reshape(batch_size)
    ones_x, ones_h = torch.ones_like(sigma_x), torch.ones_like(sigma_h)
    kl_x = ddpm.gaussian_KL(mu_norm_x, sigma_x, ones_x, d=coordinate_dimensions)
    # Historical ConditionalDDPM uses d=1 for the feature KL variance term.
    kl_h = ddpm.gaussian_KL(mu_norm_h, sigma_h, ones_h, d=1)
    return kl_x + kl_h


def _validation_auxiliary_reducers(
    *, model_output: object, supervision: CovapieCurrent11TrainingSupervisionTensorsV1,
) -> tuple[tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor], ...]:
    logits = model_output.pair_logits
    geometry = model_output.pre_post_geometry_predictions_angstrom
    result = []
    for sample in range(len(supervision.canonical_task_id)):
        start = int(supervision.pair_candidate_offsets[sample].item())
        end = int(supervision.pair_candidate_offsets[sample + 1].item())
        positive = int(supervision.pair_positive_candidate_index[sample].item())
        segment_positive = supervision.pair_candidate_is_positive[start:end]
        segment_negative = supervision.pair_candidate_is_negative[start:end]
        valid_components = supervision.pre_post_geometry_component_valid_mask[sample]
        loss_components = supervision.pre_post_geometry_component_loss_mask[sample]
        if (
            not bool(supervision.pair_positive_candidate_valid[sample].item())
            or not start <= positive < end
            or int(segment_positive.sum().item()) != 1
            or not bool(segment_positive[positive - start].item())
            or not bool((segment_positive ^ segment_negative).all().item())
            or valid_components.tolist() != [False, True]
            or bool(loss_components.any().item())
        ):
            _fail("VALIDATION_AUXILIARY_LABEL_DOMAIN_INVALID")
        positive_bce = F.binary_cross_entropy_with_logits(logits[positive], logits.new_ones(()))
        negative_logits = logits[start:end][segment_negative]
        if len(negative_logits) == 0:
            _fail("VALIDATION_PAIR_NEGATIVE_DOMAIN_EMPTY")
        negative_bce = F.binary_cross_entropy_with_logits(
            negative_logits, torch.zeros_like(negative_logits), reduction="mean",
        )
        pair_bce = 0.5 * positive_bce + 0.5 * negative_bce
        positive_ordinal = positive - start
        contrastive = -F.log_softmax(
            logits[start:end] / PAIR_CONTRASTIVE_TEMPERATURE_V1, dim=0,
        )[positive_ordinal]
        post_prediction = geometry[positive, 1]
        post_target = supervision.pre_post_geometry_target_angstrom[sample, 1]
        post_loss = F.smooth_l1_loss(
            post_prediction, post_target, reduction="none", beta=GEOMETRY_SMOOTH_L1_BETA_V1,
        )
        result.append((pair_bce, post_loss, post_prediction, post_target, contrastive))
    return tuple(result)


def _evaluate_slice(
    *, model: nn.Module, preview: object, task_id: int, root_seed: int,
    leakage_by_event: Mapping[str, str], record_by_event: Mapping[str, object],
) -> _SliceOutputV1:
    if torch.is_grad_enabled():
        _fail("GRADIENT_RECORDING_ENABLED_IN_MODEL_EVALUATION_REGION")
    validate_formal_evaluation_module_state_v1(model=model)
    ddpm = model.ddpm
    auxiliary = model.covapie_current11_auxiliary_model_v1
    supervision = preview.supervision
    ligand, pocket = model.get_ligand_and_pocket(preview.model_input_batch)
    ligand_mask, pocket_mask = ligand["mask"], pocket["mask"]
    active = supervision.ligand_base_generation_mask[:, 0]
    fixed = supervision.ligand_base_fixed_mask[:, 0]
    batch_size = len(ligand["size"])
    if (
        not torch.equal(active, ~fixed)
        or bool(supervision.sample_training_admitted.any().item())
        or bool(supervision.ligand_active_diffusion_loss_mask.any().item())
    ):
        _fail("VALIDATION_MASK_OR_ADMISSION_INVALID")
    indicator = supervision.target_residue_reactive_atom_mask[:, 0]
    indicator_counts = scatter_add(indicator.long(), pocket_mask, dim=0, dim_size=batch_size)
    if indicator_counts.tolist() != [1] * batch_size:
        _fail("TARGET_CYS_SG_INDICATOR_NOT_EXACTLY_ONE")
    role_delta = auxiliary.encode_role_mask_anchor_v1(
        supervision=supervision, ligand_batch_index=ligand_mask,
    )
    clean_ligand, clean_pocket = _center_clean(
        ddpm=ddpm, ligand=ligand, pocket=pocket,
        supervision=supervision, task_id=task_id,
    )
    main_t_int, main_epsilon, t0_epsilon = _build_noise_batch(
        preview=preview, task_id=task_id, root_seed=root_seed, timesteps=ddpm.T,
    )
    s = (main_t_int - 1.0) / ddpm.T
    t = main_t_int / ddpm.T
    gamma_s = ddpm.inflate_batch_array(ddpm.gamma(s), ligand["x"])
    gamma_t = ddpm.inflate_batch_array(ddpm.gamma(t), ligand["x"])
    z_main, pocket_main = _assemble_noised(
        ddpm=ddpm, clean_ligand=clean_ligand, clean_pocket=clean_pocket,
        ligand_mask=ligand_mask, pocket_mask=pocket_mask, active=active,
        gamma=gamma_t, epsilon=main_epsilon, task_id=task_id,
    )
    main_output = run_covapie_current11_functional_dynamics_with_hidden_v1(
        ddpm=ddpm, xh_atoms=z_main, xh_residues=pocket_main, t=t,
        mask_atoms=ligand_mask, mask_residues=pocket_mask,
        ligand_coordinate_update_mask=active.unsqueeze(1),
        role_mask_anchor_hidden_delta=role_delta,
        pocket_target_residue_atom_condition_indicator=indicator,
    )
    main_prediction = main_output.decoded_ligand_dynamics
    denoised_generated = ddpm.xh_given_zt_and_epsilon(
        z_main, main_prediction, gamma_t, ligand_mask,
    )
    denoised_ligand = (
        denoised_generated if task_id == 4
        else torch.where(active.unsqueeze(1), denoised_generated, clean_ligand)
    )
    t0 = torch.zeros((batch_size, 1), dtype=clean_ligand.dtype)
    gamma_0 = ddpm.inflate_batch_array(ddpm.gamma(t0), ligand["x"])
    z_t0, pocket_t0 = _assemble_noised(
        ddpm=ddpm, clean_ligand=clean_ligand, clean_pocket=clean_pocket,
        ligand_mask=ligand_mask, pocket_mask=pocket_mask, active=active,
        gamma=gamma_0, epsilon=t0_epsilon, task_id=task_id,
    )
    t0_output = run_covapie_current11_functional_dynamics_with_hidden_v1(
        ddpm=ddpm, xh_atoms=z_t0, xh_residues=pocket_t0, t=t0,
        mask_atoms=ligand_mask, mask_residues=pocket_mask,
        ligand_coordinate_update_mask=active.unsqueeze(1),
        role_mask_anchor_hidden_delta=role_delta,
        pocket_target_residue_atom_condition_indicator=indicator,
    )
    t0_prediction = t0_output.decoded_ligand_dynamics
    main_error = masked_active_epsilon_error_v1(
        sampled_epsilon=main_epsilon, predicted_epsilon=main_prediction,
        active_mask=active, ligand_batch_index=ligand_mask,
        batch_size=batch_size,
    )
    snr_weight, loss_t = historical_eval_loss_t_v1(
        active_epsilon_error=main_error, gamma_s=gamma_s,
        gamma_t=gamma_t, timesteps=ddpm.T,
    )
    loss_0_x = masked_t0_coordinate_loss_v1(
        sampled_epsilon=t0_epsilon, predicted_epsilon=t0_prediction,
        active_mask=active, ligand_batch_index=ligand_mask,
        batch_size=batch_size, n_dims=ddpm.n_dims,
    )
    normalized_true_one_hot = clean_ligand[:, ddpm.n_dims:]
    loss_0_h = _masked_categorical_loss(
        ddpm=ddpm, normalized_true_one_hot=normalized_true_one_hot,
        z_ligand=z_t0, gamma_0=gamma_0, active=active,
        ligand_mask=ligand_mask, batch_size=batch_size,
    )
    generated_count = scatter_add(active.long(), ligand_mask, dim=0, dim_size=batch_size)
    fixed_count = ligand["size"] - generated_count
    coordinate_dimensions = generated_count * ddpm.n_dims
    if task_id == 4:
        coordinate_dimensions = (generated_count - 1) * ddpm.n_dims
    neg_constant = masked_gaussian_coordinate_constant_loss_v1(
        gamma_0=gamma_0[:, 0], coordinate_dimensions=coordinate_dimensions,
    )
    kl_prior = _masked_kl_prior(
        ddpm=ddpm, clean_ligand=clean_ligand, ligand_mask=ligand_mask,
        active=active, coordinate_dimensions=coordinate_dimensions,
        batch_size=batch_size,
    )
    normalization = float(ddpm.norm_values[0])
    delta_log_px = masked_normalization_delta_log_px_v1(
        coordinate_dimensions=coordinate_dimensions,
        coordinate_normalization=normalization,
    ).to(loss_t.dtype)
    primary = compose_masked_conditional_vlb_nll_v1(
        loss_t=loss_t, loss_0_x=loss_0_x, loss_0_h=loss_0_h,
        negative_log_coordinate_constant=neg_constant,
        kl_prior=kl_prior, masked_delta_log_px=delta_log_px,
    )
    log_pn = ddpm.log_pN(ligand["size"], pocket["size"]) if task_id == 4 else None
    joint = primary - log_pn if log_pn is not None else None
    trace = _ValidationTraceV1(
        diffusion_epsilon_prediction_ligand=main_prediction,
        denoised_ligand_xh=denoised_ligand,
        diffusion_timestep_int=main_t_int[:, 0].long(),
        ligand_node_hidden=main_output.ligand_node_hidden,
        pocket_node_hidden=main_output.pocket_node_hidden,
        clean_centered_pocket_xh=pocket_main,
        coordinate_normalization=normalization,
    )
    model_output = auxiliary(
        diffusion_trace=trace, supervision=supervision,
        role_mask_anchor_hidden_delta=role_delta,
    )
    reducers = _validation_auxiliary_reducers(
        model_output=model_output, supervision=supervision,
    )
    tensor_values = (
        main_prediction, t0_prediction, main_error, snr_weight, loss_t,
        loss_0_x, loss_0_h, neg_constant, kl_prior, delta_log_px, primary,
        model_output.pair_logits,
        model_output.pre_post_geometry_predictions_angstrom,
    )
    if (
        any(not bool(torch.isfinite(value).all().item()) for value in tensor_values)
        or (joint is not None and not bool(torch.isfinite(joint).all().item()))
    ):
        _fail("NONFINITE_FORMAL_VALIDATION_METRIC")
    fixed_main_clean = task_id == 4 or bool(torch.equal(z_main[fixed], clean_ligand[fixed]))
    fixed_t0_clean = task_id == 4 or bool(torch.equal(z_t0[fixed], clean_ligand[fixed]))
    task_name, task_alias = TASK_TO_GENERATED_ROLES_V1[task_id][1:3]
    estimates: list[FormalValidationEstimateV1] = []
    for sample, event_id in enumerate(preview.sample_identities):
        record = record_by_event[event_id]
        pair_count = int(
            supervision.pair_candidate_offsets[sample + 1].item()
            - supervision.pair_candidate_offsets[sample].item()
        )
        pair_bce, post_loss, post_prediction, post_target, contrastive = reducers[sample]
        estimates.append(FormalValidationEstimateV1(
            canonical_event_id=event_id,
            pdb_id=record.pdb_id,
            ligand_component_id=record.ligand_component_id,
            formal_split="validation",
            leakage_group=leakage_by_event[event_id],
            profile=_profile_name(record),
            canonical_task_id=task_id,
            canonical_task_name=task_name,
            canonical_task_alias=task_alias,
            root_validation_seed=root_seed,
            main_timestep_int=int(main_t_int[sample, 0].item()),
            generated_atom_count=int(generated_count[sample].item()),
            fixed_atom_count=int(fixed_count[sample].item()),
            coordinate_dimension=int(coordinate_dimensions[sample].item()),
            main_active_epsilon_error=float(main_error[sample].item()),
            SNR_weight=float(snr_weight[sample].item()),
            loss_t=float(loss_t[sample].item()),
            t0_coordinate_loss=float(loss_0_x[sample].item()),
            t0_categorical_loss=float(loss_0_h[sample].item()),
            negative_log_coordinate_constant=float(neg_constant[sample].item()),
            kl_prior=float(kl_prior[sample].item()),
            masked_delta_log_px=float(delta_log_px[sample].item()),
            masked_conditional_vlb_nll=float(primary[sample].item()),
            task4_log_pN=None if log_pn is None else float(log_pn[sample].item()),
            task4_historical_joint_nll_with_node_prior_diagnostic=(
                None if joint is None else float(joint[sample].item())
            ),
            pair_BCE=float(pair_bce.item()),
            POST_geometry_loss=float(post_loss.item()),
            POST_geometry_prediction_angstrom=float(post_prediction.item()),
            POST_geometry_target_angstrom=float(post_target.item()),
            pair_contrastive_loss=float(contrastive.item()),
            PRE_geometry_valid=False,
            target_cys_sg_indicator_count=int(indicator_counts[sample].item()),
            pair_candidate_count=pair_count,
            fixed_ligand_clean_main=fixed_main_clean,
            fixed_ligand_clean_t0=fixed_t0_clean,
        ))
    return _SliceOutputV1(
        estimates=tuple(estimates), main_calls=1, t0_calls=1,
        fixed_clean=fixed_main_clean and fixed_t0_clean,
        indicator_reused=True,
        tensors_require_grad=any(value.requires_grad for value in tensor_values),
    )


def _means(values: Sequence[float]) -> float:
    if not values or any(not math.isfinite(value) for value in values):
        _fail("AGGREGATION_VALUE_DOMAIN_INVALID")
    return math.fsum(values) / len(values)


def _aggregate(
    estimates: tuple[FormalValidationEstimateV1, ...],
) -> tuple[
    tuple[FormalValidationEventTaskMeanV1, ...],
    tuple[FormalValidationEventMeanV1, ...], float, float,
    tuple[tuple[str, float], ...], float,
]:
    task_means: list[FormalValidationEventTaskMeanV1] = []
    for event_id in FORMAL_VALIDATION_EVENT_IDS_V1:
        event_rows = tuple(row for row in estimates if row.canonical_event_id == event_id)
        tasks = tuple(dict.fromkeys(row.canonical_task_id for row in event_rows))
        for task_id in tasks:
            rows = tuple(row for row in event_rows if row.canonical_task_id == task_id)
            if len(rows) != 4 or {row.root_validation_seed for row in rows} != set(FORMAL_VALIDATION_ROOT_SEEDS_V1):
                _fail("EVENT_TASK_SEED_DOMAIN_INVALID")
            joints = tuple(
                row.task4_historical_joint_nll_with_node_prior_diagnostic
                for row in rows
            )
            task_means.append(FormalValidationEventTaskMeanV1(
                canonical_event_id=event_id,
                profile=rows[0].profile,
                canonical_task_id=task_id,
                seed_count=4,
                masked_conditional_vlb_nll=_means(tuple(row.masked_conditional_vlb_nll for row in rows)),
                pair_BCE=_means(tuple(row.pair_BCE for row in rows)),
                POST_geometry_loss=_means(tuple(row.POST_geometry_loss for row in rows)),
                pair_contrastive_loss=_means(tuple(row.pair_contrastive_loss for row in rows)),
                task4_historical_joint_nll_with_node_prior_diagnostic=(
                    None if task_id != 4 else _means(tuple(float(value) for value in joints if value is not None))
                ),
            ))
    if len(task_means) != 16:
        _fail("EVENT_TASK_MEAN_COUNT_INVALID")
    event_means: list[FormalValidationEventMeanV1] = []
    for event_id in FORMAL_VALIDATION_EVENT_IDS_V1:
        rows = tuple(row for row in task_means if row.canonical_event_id == event_id)
        event_means.append(FormalValidationEventMeanV1(
            canonical_event_id=event_id,
            profile=rows[0].profile,
            applicable_task_count=len(rows),
            masked_conditional_vlb_nll=_means(tuple(row.masked_conditional_vlb_nll for row in rows)),
        ))
    event_macro = _means(tuple(row.masked_conditional_vlb_nll for row in event_means))
    micro = _means(tuple(row.masked_conditional_vlb_nll for row in task_means))
    profile_means = tuple(
        (profile, _means(tuple(
            row.masked_conditional_vlb_nll for row in event_means if row.profile == profile
        )))
        for profile, unused in PROFILE_TASK_MATRIX_V1
    )
    profile_balanced = _means(tuple(value for unused, value in profile_means))
    return tuple(task_means), tuple(event_means), event_macro, micro, profile_means, profile_balanced


def _snapshot_parameters(model: nn.Module) -> dict[str, torch.Tensor]:
    return {name: value.detach().clone() for name, value in model.named_parameters()}


def _snapshot_buffers(model: nn.Module) -> dict[str, torch.Tensor]:
    return {name: value.detach().clone() for name, value in model.named_buffers()}


def _snapshot_grads(model: nn.Module) -> dict[str, torch.Tensor | None]:
    return {
        name: None if value.grad is None else value.grad.detach().clone()
        for name, value in model.named_parameters()
    }


def _same_snapshot(before: Mapping[str, torch.Tensor], after: Mapping[str, torch.Tensor]) -> bool:
    return before.keys() == after.keys() and all(torch.equal(before[name], after[name]) for name in before)


def _same_grads(before: Mapping[str, torch.Tensor | None], model: nn.Module) -> bool:
    current = dict(model.named_parameters())
    if before.keys() != current.keys():
        return False
    for name, expected in before.items():
        actual = current[name].grad
        if expected is None:
            if actual is not None:
                return False
        elif actual is None or not torch.equal(expected, actual):
            return False
    return True


@contextlib.contextmanager
def _deterministic_cpu_context():
    rng_state = torch.random.get_rng_state()
    previous_threads = torch.get_num_threads()
    deterministic_enabled = torch.are_deterministic_algorithms_enabled()
    deterministic_warn_only = torch.is_deterministic_algorithms_warn_only_enabled()
    try:
        torch.set_num_threads(1)
        torch.use_deterministic_algorithms(True)
        yield
    finally:
        torch.random.set_rng_state(rng_state)
        torch.use_deterministic_algorithms(
            deterministic_enabled, warn_only=deterministic_warn_only,
        )
        torch.set_num_threads(previous_threads)


def _run_impl(
    *, repository_root: Path, state_root: Path, cache_root: Path,
    checkpoint_path: Path,
) -> FormalValidation4MaskedVlbNllResultV1:
    started = time.perf_counter()
    source_bindings = _verify_bound_sources(repository_root)
    checkpoint_before = _sha256_file(checkpoint_path)
    if checkpoint_before != CHECKPOINT_SHA256_V1:
        _fail("CHECKPOINT_SHA256_MISMATCH")
    authority = _audit_formal_authority(repository_root)
    records_all = structural_owner.build_covapie_batch001_positive_structural_records_v1(
        repository_root=repository_root, cache_root=cache_root,
    )
    by_event_all = {record.canonical_event_id: record for record in records_all}
    records = tuple(by_event_all[event_id] for event_id in FORMAL_VALIDATION_EVENT_IDS_V1)
    if len(records_all) != 13 or len(by_event_all) != 13:
        _fail("STRUCTURAL_OWNER_POPULATION_INVALID")
    for record in records:
        structural_owner.validate_covapie_batch001_positive_structural_record_v1(record)
    expected_domains = {
        "LN5": (13, 5, 3, 5, (0, 1, 2, 3, 4)),
        "PX5": (17, 9, 0, 8, (0, 3, 4)),
    }
    for record in records:
        expected = expected_domains[record.ligand_component_id]
        actual = (
            len(record.ligand_retained_heavy_atoms),
            len(record.scaffold_retained_local_indices),
            len(record.linker_retained_local_indices),
            len(record.warhead_retained_local_indices),
            record.applicable_canonical_task_ids,
        )
        if actual != expected or record.sample_training_admitted:
            _fail("VALIDATION_PROFILE_ROLE_OR_LABEL_DOMAIN_INVALID")
    batches = _task_batches(records)
    from covalent_ext import (  # imported only by the bounded fresh-model wrapper
        covapie_current11_checkpoint_migration_and_real_one_batch_train_path_smoke_v1
        as instantiation_owner,
    )
    checkpoint_payload = migration_owner.load_covapie_current11_legacy_checkpoint_v1(
        checkpoint_path=checkpoint_path,
    )
    with _deterministic_cpu_context():
        torch.random.default_generator.manual_seed(MODEL_INITIALIZATION_SEED_V1)
        model = instantiation_owner._instantiate_current11_model_v1(
            repo_root=repository_root, state_root=state_root, device="cpu",
        )
        migration = migration_owner.migrate_covapie_current11_legacy_checkpoint_state_dict_v1(
            model=model, checkpoint_state_dict=checkpoint_payload["state_dict"],
        )
        migration_names = (
            "checkpoint_key_count", "target_model_key_count", "shared_key_count",
            "target_only_key_count", "checkpoint_only_key_count",
            "shared_shape_mismatch_count", "shared_checkpoint_tensor_equality_count",
        )
        migration_counts = tuple((name, int(migration[name])) for name in migration_names)
        if dict(migration_counts) != {
            "checkpoint_key_count": 122,
            "target_model_key_count": 141,
            "shared_key_count": 122,
            "target_only_key_count": 19,
            "checkpoint_only_key_count": 0,
            "shared_shape_mismatch_count": 0,
            "shared_checkpoint_tensor_equality_count": 122,
        }:
            _fail("CHECKPOINT_MIGRATION_COUNTS_INVALID")
        legacy_constructor = checkpoint_payload.get("legacy_constructor")
        historical_node_histogram = (
            legacy_constructor.get("node_histogram")
            if type(legacy_constructor) is dict else None
        )
        if (
            type(historical_node_histogram) is not list
            or len(historical_node_histogram) != 107
            or any(type(row) is not list or len(row) != 1671 for row in historical_node_histogram)
            or legacy_constructor.get("node_histogram_source")
            != "exact_legacy_checkpoint_hyperparameters"
            or legacy_constructor.get("synthetic_node_histogram_used") is not False
        ):
            _fail("HISTORICAL_NODE_HISTOGRAM_AUTHORITY_INVALID")
        # The shared instantiation helper intentionally uses a tiny synthetic
        # constructor-only histogram.  It is not evaluation semantics.  Restore
        # the exact checkpoint-bound historical size prior before any log_pN.
        with contextlib.redirect_stdout(io.StringIO()):
            model.ddpm.size_distribution = type(model.ddpm.size_distribution)(
                historical_node_histogram
            )
        model.eval()
        validate_formal_evaluation_module_state_v1(model=model)
        parameter_before = _snapshot_parameters(model)
        buffer_before = _snapshot_buffers(model)
        grad_before = _snapshot_grads(model)
        leakage_by_event = {event: group for event, unused, group in authority.validation_rows}
        estimates: list[FormalValidationEstimateV1] = []
        main_calls = t0_calls = 0
        fixed_clean = indicator_reused = True
        tensors_require_grad = False
        with torch.inference_mode():
            for root_seed in FORMAL_VALIDATION_ROOT_SEEDS_V1:
                for task_id, preview in batches:
                    output = _evaluate_slice(
                        model=model, preview=preview, task_id=task_id,
                        root_seed=root_seed, leakage_by_event=leakage_by_event,
                        record_by_event=by_event_all,
                    )
                    estimates.extend(output.estimates)
                    main_calls += output.main_calls
                    t0_calls += output.t0_calls
                    fixed_clean = fixed_clean and output.fixed_clean
                    indicator_reused = indicator_reused and output.indicator_reused
                    tensors_require_grad = tensors_require_grad or output.tensors_require_grad
        parameters_unchanged = _same_snapshot(parameter_before, _snapshot_parameters(model))
        buffers_unchanged = _same_snapshot(buffer_before, _snapshot_buffers(model))
        grads_unchanged = _same_grads(grad_before, model)
        architecture = (
            ("device", "cpu"), ("mode", model.mode),
            ("pocket_representation", model.pocket_representation),
            ("atom_nf", model.atom_nf), ("residue_nf", model.aa_nf),
            ("timesteps", model.ddpm.T),
            ("node_histogram_shape", (107, 1671)),
            ("node_histogram_source", "exact_legacy_checkpoint_hyperparameters"),
            ("joint_nf", model.covapie_current11_auxiliary_model_v1.joint_nf),
            ("hidden_nf", model.ddpm.dynamics.egnn.hidden_nf),
            ("egnn_layers", model.ddpm.dynamics.egnn.n_layers),
        )
    estimate_tuple = tuple(estimates)
    if len(estimate_tuple) != 64 or main_calls != 20 or t0_calls != 20:
        _fail("FORMAL_EXECUTION_COUNT_INVALID")
    event_task, event_means, event_macro, micro, profile_means, profile_balanced = _aggregate(estimate_tuple)
    primary_values = tuple(row.masked_conditional_vlb_nll for row in estimate_tuple)
    auxiliary_values = tuple(
        value for row in estimate_tuple
        for value in (row.pair_BCE, row.POST_geometry_loss, row.pair_contrastive_loss)
    )
    task4_joint = tuple(
        float(row.task4_historical_joint_nll_with_node_prior_diagnostic)
        for row in estimate_tuple
        if row.task4_historical_joint_nll_with_node_prior_diagnostic is not None
    )
    checkpoint_after = _sha256_file(checkpoint_path)
    if (
        not parameters_unchanged or not buffers_unchanged or not grads_unchanged
        or checkpoint_after != checkpoint_before
    ):
        _fail("MODEL_OR_CHECKPOINT_MUTATED")
    partial_rows = tuple(row for row in estimate_tuple if row.canonical_task_id != 4)
    task4_rows = tuple(row for row in estimate_tuple if row.canonical_task_id == 4)
    partial_dimensions_exact = all(
        row.coordinate_dimension == 3 * row.generated_atom_count for row in partial_rows
    )
    task4_dimensions_exact = all(
        row.coordinate_dimension == 3 * (row.generated_atom_count - 1) for row in task4_rows
    )
    result = FormalValidation4MaskedVlbNllResultV1(
        implementation_status="passed",
        primary_metric_name=PRIMARY_METRIC_NAME_V1,
        historical_joint_diagnostic_name=HISTORICAL_JOINT_DIAGNOSTIC_NAME_V1,
        formal_validation_event_ids=FORMAL_VALIDATION_EVENT_IDS_V1,
        formal_train_event_ids=FORMAL_TRAIN_EVENT_IDS_V1,
        formal_leakage_groups=FORMAL_LEAKAGE_GROUPS_V1,
        train_validation_leakage_group_intersection_count=0,
        profile_task_matrix=PROFILE_TASK_MATRIX_V1,
        root_validation_seeds=FORMAL_VALIDATION_ROOT_SEEDS_V1,
        formal_validation_event_count=4,
        formal_validation_task_event_count=16,
        formal_validation_estimate_count=64,
        formal_validation_task_slice_evaluation_count=20,
        main_dynamics_task_slice_call_count=main_calls,
        t0_dynamics_task_slice_call_count=t0_calls,
        total_dynamics_task_slice_call_count=main_calls + t0_calls,
        actual_functional_dynamics_call_count=main_calls + t0_calls,
        per_estimate_rows=estimate_tuple,
        per_event_task_seed_means=event_task,
        per_event_means=event_means,
        event_macro_masked_conditional_vlb_nll=event_macro,
        micro_masked_conditional_vlb_nll=micro,
        profile_means=profile_means,
        profile_balanced_masked_conditional_vlb_nll=profile_balanced,
        mean_pair_BCE=_means(tuple(row.pair_BCE for row in estimate_tuple)),
        mean_POST_geometry_loss=_means(tuple(row.POST_geometry_loss for row in estimate_tuple)),
        mean_POST_geometry_prediction_angstrom=_means(tuple(row.POST_geometry_prediction_angstrom for row in estimate_tuple)),
        mean_POST_geometry_target_angstrom=_means(tuple(row.POST_geometry_target_angstrom for row in estimate_tuple)),
        mean_pair_contrastive_loss=_means(tuple(row.pair_contrastive_loss for row in estimate_tuple)),
        mean_task4_historical_joint_nll_with_node_prior_diagnostic=_means(task4_joint),
        migration_counts=migration_counts,
        architecture=architecture,
        parameters_unchanged=parameters_unchanged,
        buffers_unchanged=buffers_unchanged,
        gradient_states_unchanged=grads_unchanged,
        checkpoint_sha256_before=checkpoint_before,
        checkpoint_sha256_after=checkpoint_after,
        checkpoint_unchanged=checkpoint_after == checkpoint_before,
        source_bindings=source_bindings,
        runtime_elapsed_seconds=time.perf_counter() - started,
        model_eval_mode_verified=True,
        ddpm_eval_mode_verified=True,
        auxiliary_eval_mode_verified=True,
        gradient_recording_disabled=True,
        metric_tensors_require_grad=tensors_require_grad,
        all_validation_events_not_training_admitted=True,
        all_applicable_primary_metrics_finite=all(math.isfinite(value) for value in primary_values),
        all_applicable_auxiliary_metrics_finite=all(math.isfinite(value) for value in auxiliary_values),
        partial_tasks_fixed_ligand_clean=fixed_clean and all(
            row.fixed_ligand_clean_main and row.fixed_ligand_clean_t0 for row in partial_rows
        ),
        partial_tasks_coordinate_dimension_exact=partial_dimensions_exact,
        task4_zero_com_coordinate_dimension_exact=task4_dimensions_exact,
        main_timestep_domain_exact_1_to_T=all(1 <= row.main_timestep_int <= 500 for row in estimate_tuple),
        separate_t0_forward_verified=t0_calls == main_calls == 20,
        target_cys_sg_same_indicator_main_and_t0=indicator_reused,
        primary_includes_log_pN=False,
        task4_historical_joint_nll_diagnostic_available=len(task4_joint) == 16,
        PRE_geometry_valid_count=sum(int(row.PRE_geometry_valid) for row in estimate_tuple),
        POST_geometry_valid_count=len(estimate_tuple),
        pair_contrastive_temperature=PAIR_CONTRASTIVE_TEMPERATURE_V1,
        geometry_smooth_l1_beta=GEOMETRY_SMOOTH_L1_BETA_V1,
        current_candidate_weights_metadata=PRIMARY_COMPONENT_WEIGHTS_METADATA_V1,
        production_geometry_weight_finalized=False,
        reaction_family_authority_consumed=False,
        optimizer_created=False,
        optimizer_step_performed=False,
        backward_performed=False,
        Trainer_used=False,
        training_performed=False,
        CPU_only=True,
        GPU_used=False,
        network_used=False,
        full_training_authorized=False,
        ready_for_lightning_validation_integration=True,
        ready_for_gpt_review=True,
    )
    if (
        result.metric_tensors_require_grad
        or not result.all_applicable_primary_metrics_finite
        or not result.all_applicable_auxiliary_metrics_finite
        or not result.partial_tasks_fixed_ligand_clean
        or not result.partial_tasks_coordinate_dimension_exact
        or not result.task4_zero_com_coordinate_dimension_exact
        or result.PRE_geometry_valid_count != 0
        or result.POST_geometry_valid_count != 64
    ):
        _fail("FINAL_READINESS_INVARIANT_FAILED")
    return result


def run_covapie_current11_formal_validation4_masked_vlb_nll_v1(
    *, repository_root: Path | None = None, state_root: Path | None = None,
    cache_root: Path | None = None, checkpoint_path: Path | None = None,
) -> FormalValidation4MaskedVlbNllResultV1:
    """Run the exact four-event, four-seed bounded evaluator once on CPU."""

    try:
        repository = _require_root(
            repository_root, default=_DEFAULT_REPOSITORY_ROOT,
            reason="REPOSITORY_ROOT_INVALID",
        )
        state = _require_root(
            state_root, default=_DEFAULT_STATE_ROOT, reason="STATE_ROOT_INVALID",
        )
        cache = _require_root(
            cache_root, default=_DEFAULT_CACHE_ROOT, reason="CACHE_ROOT_INVALID",
        )
        checkpoint = repository / CHECKPOINT_RELATIVE_PATH_V1 if checkpoint_path is None else checkpoint_path
        if type(checkpoint) is not _PATH_TYPE or checkpoint != repository / CHECKPOINT_RELATIVE_PATH_V1:
            _fail("CHECKPOINT_PATH_NOT_EXACT_PUBLISHED_PATH")
        return _run_impl(
            repository_root=repository, state_root=state, cache_root=cache,
            checkpoint_path=checkpoint,
        )
    except Exception as error:
        _public_error(error)
