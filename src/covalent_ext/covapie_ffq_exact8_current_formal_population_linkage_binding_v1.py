"""Bind the FFQ Exact8 seeds to the current formal population, read-only.

The result is deliberately non-authoritative.  It reconstructs the published
15-group formal population, closes the Exact8 seeds only inside the two frozen
predictor lanes, and reports unresolved relation inputs without converting
them to negative evidence.  It never assigns a split or admits a sample.
"""

from __future__ import annotations

from collections import Counter, deque
from collections.abc import Mapping, Sequence
import csv
from dataclasses import dataclass, fields, replace
import hashlib
import io
import json
from pathlib import Path
import re
from typing import Any, NoReturn

from covalent_ext import covapie_bulk_cys_sg_dataset_expansion_v1 as linkage_owner
from covalent_ext import covapie_poa_full_component_formal_split_authority_v1 as poa_owner


__all__ = (
    "AXES_V1",
    "BindingInputsV1",
    "EventEvidenceV1",
    "FormalGroupV1",
    "FFQExact8CurrentFormalPopulationLinkageBindingResultV1",
    "build_covapie_ffq_exact8_current_formal_population_linkage_binding_v1",
    "compute_covapie_ffq_exact8_current_formal_population_linkage_binding_v1",
    "load_covapie_ffq_exact8_current_formal_population_linkage_binding_inputs_v1",
    "validate_covapie_ffq_exact8_current_formal_population_linkage_binding_v1",
)


ERROR_V1 = "COVAPIE_FFQ_EXACT8_CURRENT_FORMAL_POPULATION_LINKAGE_BINDING_V1_ERROR"
SCHEMA_VERSION_V1 = "covapie_ffq_exact8_current_formal_population_linkage_binding_v1"

AXES_V1 = (
    "LIGAND_GRAPH",
    "LIGAND_SCAFFOLD",
    "PROTEIN_ACCESSION",
    "PROTEIN_EXACT_SEQUENCE",
    "PROTEIN_SEQUENCE_IDENTITY_GE_0.5",
)
CANONICAL_EXACT5_V1 = (
    "warhead_only",
    "linker_plus_warhead",
    "scaffold_plus_warhead",
    "scaffold_only",
    "scaffold_plus_linker_plus_warhead",
)
SPLITS_V1 = ("train", "validation", "test")

STATUS_COMPLETE_NO_LINKAGE = "COMPLETE_NO_FORMAL_POPULATION_LINKAGE"
STATUS_COMPLETE_WITH_LINKAGE = "COMPLETE_WITH_FORMAL_POPULATION_LINKAGE"
STATUS_INCOMPLETE = "INCOMPLETE_UNKNOWN_RELATIONS"
STATUS_CROSS_SPLIT_CONFLICT = "CROSS_SPLIT_CONFLICT"

_EVENT_RE = re.compile(
    r"^COVAPIE_CYS_SG_EVENT_V1:(?P<pdb>[^:]+):[^:]+:CYS:[^:]+:SG:"
    r"[^:]+:(?P<ligand>[^:]+):[^:]+$"
)
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_FFQ_GRAPH_SHA256 = "013e4fc7db58df8de217d81ae81734f68c522cc6d0b4741f1696dd9471660d95"

_EXACT4_SCRIPT = (
    "covapie-state/local-tools/ffq-exact4-existing-split-group-binding-v1/"
    "inspect_ffq_exact4_existing_split_group_binding_v1.py"
)
_EXACT4_REPORT = (
    "covapie-state/local-tools/ffq-exact4-existing-split-group-binding-v1/"
    "ffq_exact4_existing_split_group_binding_v1.json"
)
_SEQUENCE_SCRIPT = (
    "covapie-state/local-tools/ffq-exact8-formal-group-sequence-linkage-v1/"
    "audit_ffq_exact8_formal_group_sequence_linkage_v1.py"
)
_SEQUENCE_REPORT = (
    "covapie-state/local-tools/ffq-exact8-formal-group-sequence-linkage-v1/"
    "ffq_exact8_formal_group_sequence_linkage_v1.json"
)
_SCAFFOLD_SCRIPT = (
    "covapie-state/local-tools/ffq-exact8-candidate-scaffold-evidence-v1/"
    "audit_ffq_exact8_candidate_scaffold_evidence_v1.py"
)
_SCAFFOLD_REPORT = (
    "covapie-state/local-tools/ffq-exact8-candidate-scaffold-evidence-v1/"
    "ffq_exact8_candidate_scaffold_evidence_v1.json"
)
_CUMULATIVE_VIEW = (
    "covapie-state/bulk-500-controlled-execution-v1/attempt-001/"
    "cumulative_processing_view_v1.json"
)
_RANKS_VIEW = (
    "data/derived/covalent_small/"
    "covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1/"
    "covapie_bulk_cys_sg_ranks_0501_1000_processing_outcomes_v1.json"
)
_CLOSURE = (
    "data/derived/covalent_small/"
    "covapie_existing_positive_runtime_and_split_closure_v1/"
    "covapie_existing_positive_leakage_split_closure_inventory_v1.csv"
)
_BATCH_COMPONENTS = (
    "data/derived/covalent_small/"
    "covapie_batch001_formal_split_leakage_admission_v1/"
    "covapie_batch001_formal_leakage_component_registry_v1.json"
)
_NDU_COMPONENT = (
    "data/derived/covalent_small/"
    "covapie_batch001_ndu4_leakage_recovery_and_formal_split_admission_v1/"
    "covapie_batch001_ndu4_full_component_registry_v1.json"
)
_CURRENT_CENSUS = (
    "data/derived/covalent_small/"
    "covapie_cumulative1000_current_global_readiness_census_with_ei3_v1/"
    "covapie_cumulative1000_current_global_readiness_census_with_ei3_v1.csv"
)
_POA_OWNER = "src/covalent_ext/covapie_poa_full_component_formal_split_authority_v1.py"
_LINKAGE_OWNER = "src/covalent_ext/covapie_bulk_cys_sg_dataset_expansion_v1.py"


@dataclass(frozen=True, slots=True)
class _SourceSpecV1:
    role: str
    path_scope: str
    relative_path: str
    byte_count: int
    sha256: str
    schema: str


_SOURCE_SPECS_V1 = (
    _SourceSpecV1("FROZEN_EXACT4_DIAGNOSTIC_IMPLEMENTATION", "REPOSITORY_PARENT", _EXACT4_SCRIPT, 101186, "5e04c2ba38a1ea7858dded9c0dc568e5dacf6c45506840049e116e3ca455cd91", "PYTHON_SOURCE_READ_ONLY"),
    _SourceSpecV1("FROZEN_EXACT4_DIAGNOSTIC_REPORT", "REPOSITORY_PARENT", _EXACT4_REPORT, 300163, "7312abe32c1e0f0df8e5dd660a57ef8c54e82c5480d3f168dc0ca6153854af49", "ffq_exact4_existing_split_group_binding_metadata_only_diagnostic_v1_revised1"),
    _SourceSpecV1("FROZEN_EXACT8_SEQUENCE_AUDIT_IMPLEMENTATION", "REPOSITORY_PARENT", _SEQUENCE_SCRIPT, 54707, "23f87d37b499861705ae16f619f7d267102f727f16fbc3f287507f793a6e1305", "PYTHON_SOURCE_READ_ONLY"),
    _SourceSpecV1("FROZEN_EXACT8_SEQUENCE_AUDIT_REPORT", "REPOSITORY_PARENT", _SEQUENCE_REPORT, 509363, "9f8830a62673c4c47d2def55ad8c69de16ca2a27ff93de5d4d4094a62a7ced16", "ffq_exact8_formal_group_sequence_linkage_v1"),
    _SourceSpecV1("FROZEN_EXACT8_SCAFFOLD_AUDIT_IMPLEMENTATION", "REPOSITORY_PARENT", _SCAFFOLD_SCRIPT, 43475, "e5657f976935fb5f7fc2f69a81c2bcf22745233402af93296a4f8cf25333e1e4", "PYTHON_SOURCE_READ_ONLY"),
    _SourceSpecV1("FROZEN_EXACT8_SCAFFOLD_AUDIT_REPORT", "REPOSITORY_PARENT", _SCAFFOLD_REPORT, 27412, "df8833a216375dd76375b75dd5776c4b117eb8dd7b801013998b3037f8924727", "ffq_exact8_candidate_scaffold_evidence_v1"),
    _SourceSpecV1("PREDICTOR_HISTORICAL_CONTROL_INCREMENTAL_VIEW", "REPOSITORY_PARENT", _CUMULATIVE_VIEW, 6469651, "a27d4bf7977d5a175387af83021270c68f9cf3e8db391113dc6f1ff22f0bfc44", "covapie_bulk_500_event_executor_v1"),
    _SourceSpecV1("PREDICTOR_RANKS_0501_1000_VIEW", "REPOSITORY_ROOT", _RANKS_VIEW, 5988559, "4f5ee75a645ee560cb8e272fd3ead8ba7a446dadf9aece38f12f0eeecad16e5f", "covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1"),
    _SourceSpecV1("PUBLISHED_FORMAL_SPLIT_CLOSURE", "REPOSITORY_ROOT", _CLOSURE, 16053, "2f673a8ca76217af1517d8254de79799d4fea333d9892af13a3ab0eeb90d8259", "CSV:covapie_existing_positive_leakage_split_closure_inventory_v1"),
    _SourceSpecV1("PUBLISHED_BATCH001_FULL_COMPONENT_REGISTRY", "REPOSITORY_ROOT", _BATCH_COMPONENTS, 10237, "76e6ecae7dfde7c9e5081a0164f9a72628e4f30550e831a8f8ba5cd3d1d16544", "covapie_batch001_formal_leakage_component_registry_v1"),
    _SourceSpecV1("PUBLISHED_NDU_FULL_COMPONENT_REGISTRY", "REPOSITORY_ROOT", _NDU_COMPONENT, 19107, "3f0edbca6d2b43226321ac71e46b593029e18bc31ddc4693d6077530fe7996d2", "covapie_batch001_ndu4_full_component_registry_v1"),
    _SourceSpecV1("CURRENT_GLOBAL_DISPOSITION_CENSUS", "REPOSITORY_ROOT", _CURRENT_CENSUS, 560934, "459c92f27883d9d47fc5d5c6ccdb6969943f9fcf9194da0399900cd06e3f2966", "CSV:covapie_cumulative1000_current_global_readiness_census_with_ei3_v1"),
    _SourceSpecV1("PUBLISHED_POA_FORMAL_POPULATION_OWNER", "REPOSITORY_ROOT", _POA_OWNER, 83848, "fa466fc335b664bec5063711a6da9576b0781594f9818f7f34be9f6090d491a8", "PYTHON_SOURCE_READ_ONLY"),
    _SourceSpecV1("PUBLISHED_FIVE_AXIS_LINKAGE_OWNER", "REPOSITORY_ROOT", _LINKAGE_OWNER, 172604, "ef17777a634284a94662ac3277c02a7fb4efa20375d84fcf88ac074c61e69ce0", "PYTHON_SOURCE_READ_ONLY"),
)


@dataclass(frozen=True, slots=True)
class SourceBindingV1:
    role: str
    path_scope: str
    relative_path: str
    byte_count: int
    sha256: str
    schema: str


@dataclass(frozen=True, slots=True)
class EventEvidenceV1:
    canonical_event_id: str
    pdb_id: str
    ligand_component_id: str
    source_role: str
    source_lane: str
    evidence_complete: bool
    ligand_graph_sha256: str
    ligand_scaffold_sha256: str
    protein_accession: str
    protein_monomer_sequence_sha256: str
    protein_one_letter_sequence: str
    protein_one_letter_sequence_sha256: str


@dataclass(frozen=True, slots=True)
class FormalGroupV1:
    formal_group_id: str
    formal_split: str
    leakage_key: str
    member_identity_count: int
    full_event_count: int
    member_pdb_ligand_identities: tuple[str, ...]
    full_member_canonical_event_ids: tuple[str, ...]
    old57_member_canonical_event_ids: tuple[str, ...]
    membership_sources: tuple[str, ...]
    identifier_lineage: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TrainingDispositionV1:
    canonical_event_id: str
    training_use_disposition: str
    human_training_excluded: bool
    formal_split_authoritative: bool
    formal_split: str


@dataclass(frozen=True, slots=True)
class AxisCoverageV1:
    axis: str
    logical_pair_count: int
    current_evidence_judged_logical_pair_count: int
    policy_short_circuit_logical_pair_count: int
    unknown_logical_pair_count: int
    frozen_report_coverage_overlap_pair_count: int
    positive_pair_count: int
    negative_pair_count: int


@dataclass(frozen=True, slots=True)
class VerifiedEdgeV1:
    left_event_id: str
    right_event_id: str
    positive_axes: tuple[str, ...]
    unknown_axes: tuple[str, ...]
    left_source_role: str
    right_source_role: str


@dataclass(frozen=True, slots=True)
class UnknownRelationV1:
    closure_event_id: str
    universe_event_id: str
    unknown_axes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class FormalMemberCoverageV1:
    formal_group_id: str
    formal_member_event_id: str
    comparison_count_by_axis: tuple[tuple[str, int], ...]
    positive_count_by_axis: tuple[tuple[str, int], ...]
    unknown_count_by_axis: tuple[tuple[str, int], ...]
    all_axes_complete: bool


@dataclass(frozen=True, slots=True)
class FormalGroupReachabilityV1:
    formal_group_id: str
    formal_split: str
    full_event_count: int
    member_identity_count: int
    positive_axes: tuple[str, ...]
    unknown_pair_count: int
    reachable: bool


@dataclass(frozen=True, slots=True)
class BindingInputsV1:
    source_bindings: tuple[SourceBindingV1, ...]
    formal_authority_source_binding_sha256: str
    predictor_lane_counts: tuple[tuple[str, int], ...]
    universe_events: tuple[EventEvidenceV1, ...]
    formal_groups: tuple[FormalGroupV1, ...]
    specified_seed_event_ids: tuple[str, ...]
    required_seed_event_ids: tuple[str, ...]
    frozen_report_covered_pairs: tuple[tuple[str, str], ...]
    verified_empty_scaffold_graph_sha256: str
    training_dispositions: tuple[TrainingDispositionV1, ...]
    expected_formal_population_inventory_sha256: str
    canonical_exact5: tuple[str, ...] = CANONICAL_EXACT5_V1


@dataclass(frozen=True, slots=True)
class FFQExact8CurrentFormalPopulationLinkageBindingResultV1:
    schema_version: str
    source_bindings: tuple[SourceBindingV1, ...]
    source_semantic_sha256: str
    formal_authority_source_binding_sha256: str
    predictor_lane_counts: tuple[tuple[str, int], ...]
    predictor_universe_event_count: int
    predictor_universe_event_inventory_sha256: str
    formal_groups: tuple[FormalGroupV1, ...]
    current_formal_group_count: int
    current_formal_event_count: int
    current_formal_identity_count: int
    old_formal_scope_event_count: int
    formal_population_added_event_ids: tuple[str, ...]
    specified_seed_event_ids: tuple[str, ...]
    closure_event_ids: tuple[str, ...]
    newly_discovered_linked_event_ids: tuple[str, ...]
    verified_component_edges: tuple[VerifiedEdgeV1, ...]
    closure_unknown_relations: tuple[UnknownRelationV1, ...]
    closure_complete_within_frozen_universe: bool
    formal_population_comparison_complete: bool
    universe_axis_coverage: tuple[AxisCoverageV1, ...]
    formal_population_axis_coverage: tuple[AxisCoverageV1, ...]
    formal_member_coverage: tuple[FormalMemberCoverageV1, ...]
    formal_group_reachability: tuple[FormalGroupReachabilityV1, ...]
    reachable_formal_group_ids: tuple[str, ...]
    reachable_formal_splits: tuple[str, ...]
    cross_split_conflict: bool
    binding_status: str
    seed_training_dispositions: tuple[TrainingDispositionV1, ...]
    newly_discovered_training_dispositions: tuple[TrainingDispositionV1, ...]
    newly_discovered_missing_disposition_event_ids: tuple[str, ...]
    seed_disposition_readback_complete: bool
    newly_discovered_disposition_readback_complete: bool
    closure_disposition_readback_complete: bool
    permissions: tuple[tuple[str, bool], ...]
    canonical_exact5: tuple[str, ...]
    output_semantic_sha256: str


_PERMISSIONS_V1 = tuple(sorted({
    "NEW_FFQ_FORMAL_SPLIT_AUTHORITY_CREATED": False,
    "FORMAL_SPLIT_ASSIGNMENT_CREATED": False,
    "EXISTING_SPLIT_CHANGED": False,
    "FORMAL_ADMISSION_CREATED": False,
    "REAL_POST_TARGET_CREATED": False,
    "REAL_SAMPLE_LOSS_MASKS_ENABLED": False,
    "NEW_HUMAN_OR_SCIENTIFIC_AUTHORITY_CREATED": False,
    "MODEL_OR_LOSS_EXECUTED": False,
    "GLOBAL_INDEPENDENCE_PROVED": False,
    "GLOBAL_TRAINING_AUDIT_CLOSED": False,
    "TRAINING_STARTED": False,
    "READY_FOR_TRAINING": False,
    "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER": True,
    "STEP12D_IS_ONLY_SMOKE_LEGALITY_CHECK": True,
}.items()))


def _fail(reason: str) -> NoReturn:
    raise ValueError(f"{ERROR_V1}:{reason}")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _primitive(value: object) -> object:
    if hasattr(value, "__dataclass_fields__"):
        return {field.name: _primitive(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_primitive(item) for item in value]
    if isinstance(value, list):
        return [_primitive(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _primitive(item) for key, item in sorted(value.items())}
    return value


def canonical_json_bytes_v1(value: object) -> bytes:
    return (json.dumps(
        _primitive(value), sort_keys=True, separators=(",", ":"),
        ensure_ascii=True, allow_nan=False,
    ) + "\n").encode("utf-8")


def _inventory_sha256(values: Sequence[str]) -> str:
    return _sha256(canonical_json_bytes_v1(list(sorted(values))))


def _formal_inventory_sha256(groups: Sequence[FormalGroupV1]) -> str:
    return _sha256(canonical_json_bytes_v1(tuple(sorted(
        groups, key=lambda item: item.formal_group_id,
    ))))


def _event_identity(event_id: str) -> tuple[str, str, str]:
    match = _EVENT_RE.fullmatch(event_id) if type(event_id) is str else None
    if match is None:
        _fail("CANONICAL_EVENT_ID_INVALID")
    pdb_id, ligand = match.group("pdb"), match.group("ligand")
    return pdb_id, ligand, f"{pdb_id}/{ligand}"


def _json(payload: bytes, reason: str) -> dict[str, Any]:
    try:
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=lambda pairs: _unique_object(pairs, reason),
            parse_constant=lambda value: (_fail(reason + ":NONFINITE_JSON")),
        )
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{ERROR_V1}:{reason}:JSON_INVALID") from error
    if type(value) is not dict:
        _fail(reason + ":TOP_LEVEL_NOT_OBJECT")
    return value


def _unique_object(pairs: list[tuple[str, Any]], reason: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail(reason + ":DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _csv(payload: bytes, reason: str) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
        rows = list(reader)
    except (UnicodeError, csv.Error) as error:
        raise ValueError(f"{ERROR_V1}:{reason}:CSV_INVALID") from error
    header = tuple(reader.fieldnames or ())
    if not header or any(None in row for row in rows):
        _fail(reason + ":CSV_SCHEMA_INVALID")
    return header, rows


def _source_path(repo: Path, spec: _SourceSpecV1) -> Path:
    base = repo if spec.path_scope == "REPOSITORY_ROOT" else repo.parent
    path = base / spec.relative_path
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise ValueError(f"{ERROR_V1}:SOURCE_MISSING:{spec.role}") from error
    expected = (base.resolve() / spec.relative_path).resolve()
    if resolved != expected or not path.is_file() or path.is_symlink():
        _fail("SOURCE_NOT_REGULAR:" + spec.role)
    return path


def _read_bound_payloads_v1(repo_root: Path) -> tuple[dict[str, bytes], tuple[SourceBindingV1, ...]]:
    if not isinstance(repo_root, Path) or not repo_root.is_dir() or repo_root.is_symlink():
        _fail("REPO_ROOT_INVALID")
    repo = repo_root.resolve()
    payloads: dict[str, bytes] = {}
    bindings: list[SourceBindingV1] = []
    for spec in _SOURCE_SPECS_V1:
        payload = _source_path(repo, spec).read_bytes()
        if len(payload) != spec.byte_count:
            _fail("SOURCE_BYTE_COUNT_MISMATCH:" + spec.role)
        if _sha256(payload) != spec.sha256:
            _fail("SOURCE_SHA256_MISMATCH:" + spec.role)
        payloads[spec.role] = payload
        bindings.append(SourceBindingV1(
            spec.role, spec.path_scope, spec.relative_path,
            len(payload), spec.sha256, spec.schema,
        ))
    return payloads, tuple(bindings)


def _validate_source_bindings(bindings: object) -> None:
    if type(bindings) is not tuple or len(bindings) != len(_SOURCE_SPECS_V1):
        _fail("SOURCE_BINDING_INVENTORY_INVALID")
    for binding, spec in zip(bindings, _SOURCE_SPECS_V1, strict=True):
        if binding != SourceBindingV1(
            spec.role, spec.path_scope, spec.relative_path,
            spec.byte_count, spec.sha256, spec.schema,
        ):
            _fail("SOURCE_BINDING_INVALID:" + spec.role)


def _event_from_outcome(
    outcome: Mapping[str, Any], *, source_role: str, source_lane: str,
) -> EventEvidenceV1:
    event_id = outcome.get("canonical_event_id")
    pdb_id, ligand, _identity = _event_identity(str(event_id))
    if outcome.get("pdb_id") != pdb_id or outcome.get("ligand_component_id") != ligand:
        _fail("UNIVERSE_EVENT_IDENTITY_MISMATCH")
    structural = outcome.get("structural_processing")
    evidence = structural.get("leakage_evidence") if type(structural) is dict else None
    if type(evidence) is not dict:
        evidence = {}
    sequence = evidence.get("protein_sequence", "")
    values = {
        "ligand_graph_sha256": evidence.get("ligand_graph_sha256", ""),
        "ligand_scaffold_sha256": evidence.get("ligand_scaffold_sha256", ""),
        "protein_accession": evidence.get("protein_accession", ""),
        "protein_monomer_sequence_sha256": evidence.get("protein_sequence_sha256", ""),
        "protein_one_letter_sequence": sequence,
    }
    if any(type(value) is not str for value in values.values()):
        _fail("UNIVERSE_EVIDENCE_FIELD_TYPE_INVALID")
    for name in (
        "ligand_graph_sha256", "ligand_scaffold_sha256",
        "protein_monomer_sequence_sha256",
    ):
        value = values[name]
        if value and _SHA_RE.fullmatch(value) is None:
            _fail("UNIVERSE_EVIDENCE_DIGEST_INVALID:" + name)
    return EventEvidenceV1(
        canonical_event_id=str(event_id), pdb_id=pdb_id,
        ligand_component_id=ligand, source_role=source_role,
        source_lane=source_lane, evidence_complete=evidence.get("complete") is True,
        protein_one_letter_sequence_sha256=(
            _sha256(sequence.encode("utf-8")) if sequence else ""
        ),
        **values,
    )


def _parse_universe(payloads: Mapping[str, bytes]) -> tuple[
    tuple[EventEvidenceV1, ...], tuple[tuple[str, int], ...],
]:
    cumulative = _json(payloads["PREDICTOR_HISTORICAL_CONTROL_INCREMENTAL_VIEW"], "CUMULATIVE_VIEW")
    ranks = _json(payloads["PREDICTOR_RANKS_0501_1000_VIEW"], "RANKS_VIEW")
    if (
        cumulative.get("schema_version") != "covapie_bulk_500_event_executor_v1"
        or cumulative.get("cumulative_new_event_count") != 500
        or cumulative.get("frozen_predecessor_event_count") != 250
        or cumulative.get("newly_executed_event_count") != 250
        or cumulative.get("known_controls_separate") is not True
        or type(cumulative.get("events")) is not list
        or len(cumulative["events"]) != 500
        or type(cumulative.get("known_control_references")) is not list
        or len(cumulative["known_control_references"]) != 27
    ):
        _fail("CUMULATIVE_VIEW_SCHEMA_OR_POPULATION_INVALID")
    if (
        ranks.get("schema_version")
        != "covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1"
        or ranks.get("rank_start") != 501
        or ranks.get("rank_end") != 1000
        or ranks.get("terminal_outcome_count") != 500
        or ranks.get("structural_processing_performed") is not True
        or ranks.get("training_performed") is not False
        or type(ranks.get("events")) is not list
        or len(ranks["events"]) != 500
    ):
        _fail("RANKS_VIEW_SCHEMA_OR_POPULATION_INVALID")
    records: list[EventEvidenceV1] = []
    lanes: Counter[str] = Counter()
    for wrapper in cumulative["events"]:
        if type(wrapper) is not dict or type(wrapper.get("processing_outcome")) is not dict:
            _fail("CUMULATIVE_EVENT_WRAPPER_INVALID")
        lane = str(wrapper.get("lane", ""))
        records.append(_event_from_outcome(
            wrapper["processing_outcome"], source_role="PREDICTOR_HISTORICAL_CONTROL_INCREMENTAL_VIEW",
            source_lane=lane,
        ))
        lanes[lane] += 1
    for wrapper in cumulative["known_control_references"]:
        if type(wrapper) is not dict or type(wrapper.get("processing_outcome")) is not dict:
            _fail("CONTROL_EVENT_WRAPPER_INVALID")
        lane = str(wrapper.get("lane", ""))
        records.append(_event_from_outcome(
            wrapper["processing_outcome"], source_role="PREDICTOR_HISTORICAL_CONTROL_INCREMENTAL_VIEW",
            source_lane=lane,
        ))
        lanes[lane] += 1
    for wrapper in ranks["events"]:
        if type(wrapper) is not dict or type(wrapper.get("processing_outcome")) is not dict:
            _fail("RANKS_EVENT_WRAPPER_INVALID")
        rank = wrapper.get("scaleup_rank")
        if type(rank) is not int or not 501 <= rank <= 1000:
            _fail("RANKS_EVENT_RANK_INVALID")
        lane = "RANKS_0501_1000"
        records.append(_event_from_outcome(
            wrapper["processing_outcome"], source_role="PREDICTOR_RANKS_0501_1000_VIEW",
            source_lane=lane,
        ))
        lanes[lane] += 1
    normalized = _normalize_events(records)
    if len(normalized) != 1027:
        _fail("PREDICTOR_UNIVERSE_EVENT_COUNT_INVALID")
    return normalized, tuple(sorted(lanes.items()))


def _normalize_events(events: Sequence[EventEvidenceV1]) -> tuple[EventEvidenceV1, ...]:
    by_id: dict[str, EventEvidenceV1] = {}
    for event in events:
        if type(event) is not EventEvidenceV1:
            _fail("UNIVERSE_EVENT_TYPE_INVALID")
        _validate_event(event)
        previous = by_id.get(event.canonical_event_id)
        if previous is not None and previous != event:
            _fail("CONFLICTING_DUPLICATE_UNIVERSE_EVENT")
        by_id[event.canonical_event_id] = event
    if not by_id:
        _fail("UNIVERSE_EMPTY")
    return tuple(by_id[event_id] for event_id in sorted(by_id))


def _validate_event(event: EventEvidenceV1) -> None:
    pdb_id, ligand, _identity = _event_identity(event.canonical_event_id)
    if (
        event.pdb_id != pdb_id or event.ligand_component_id != ligand
        or not event.source_role or not event.source_lane
        or type(event.evidence_complete) is not bool
        or any(type(getattr(event, name)) is not str for name in (
            "ligand_graph_sha256", "ligand_scaffold_sha256", "protein_accession",
            "protein_monomer_sequence_sha256", "protein_one_letter_sequence",
            "protein_one_letter_sequence_sha256",
        ))
    ):
        _fail("UNIVERSE_EVENT_SEMANTICS_INVALID")
    for name in (
        "ligand_graph_sha256", "ligand_scaffold_sha256",
        "protein_monomer_sequence_sha256", "protein_one_letter_sequence_sha256",
    ):
        value = getattr(event, name)
        if value and _SHA_RE.fullmatch(value) is None:
            _fail("UNIVERSE_EVENT_DIGEST_INVALID:" + name)
    expected_text_sha = (
        _sha256(event.protein_one_letter_sequence.encode("utf-8"))
        if event.protein_one_letter_sequence else ""
    )
    if event.protein_one_letter_sequence_sha256 != expected_text_sha:
        _fail("MONOMER_AND_ONE_LETTER_DIGEST_DEFINITIONS_CONFLATED")


def _member_sets_from_sequence_report(
    report: Mapping[str, Any],
) -> tuple[dict[str, tuple[str, ...]], tuple[str, ...]]:
    if (
        report.get("schema_version") != "ffq_exact8_formal_group_sequence_linkage_v1"
        or report.get("task_id") != "audit_ffq_exact8_formal_group_sequence_linkage_v1"
        or report.get("execution_status") != "PASS"
        or report.get("semantic_result")
        != "SCOPED_SEQUENCE_AXIS_COMPLETE_NO_THRESHOLD_MATCH"
    ):
        _fail("SEQUENCE_REPORT_CONTRACT_INVALID")
    groups = report.get("formal_group_member_coverage")
    seed_rows = report.get("exact8_sequence_inputs")
    if type(groups) is not list or len(groups) != 14 or type(seed_rows) is not list:
        _fail("SEQUENCE_REPORT_POPULATION_INVALID")
    by_group: dict[str, tuple[str, ...]] = {}
    for row in groups:
        members = row.get("members") if type(row) is dict else None
        if type(members) is not list:
            _fail("SEQUENCE_REPORT_GROUP_INVALID")
        event_ids = tuple(sorted(
            str(item.get("formal_member_event_id"))
            for item in members if type(item) is dict
        ))
        group_id = str(row.get("formal_group_id"))
        if (
            not group_id or len(event_ids) != len(members)
            or len(set(event_ids)) != len(event_ids)
            or row.get("declared_member_count") != len(event_ids)
            or row.get("required_comparison_count") != len(event_ids) * 8
        ):
            _fail("SEQUENCE_REPORT_GROUP_MEMBER_INVENTORY_INVALID")
        by_group[group_id] = event_ids
    seeds = tuple(sorted(str(row.get("event_id")) for row in seed_rows if type(row) is dict))
    if (
        len(seeds) != len(seed_rows) or len(seeds) != 8 or len(set(seeds)) != 8
        or sum(":3VCY:" in item for item in seeds) != 4
        or sum(":4R7U:" in item for item in seeds) != 4
    ):
        _fail("SPECIFIED_EXACT8_SEED_INVENTORY_INVALID")
    return by_group, seeds


def _validate_old_evidence_reports(
    payloads: Mapping[str, bytes], events: Sequence[EventEvidenceV1],
    old_by_group: Mapping[str, tuple[str, ...]], seeds: tuple[str, ...],
) -> None:
    exact4 = _json(payloads["FROZEN_EXACT4_DIAGNOSTIC_REPORT"], "EXACT4_REPORT")
    scaffold = _json(payloads["FROZEN_EXACT8_SCAFFOLD_AUDIT_REPORT"], "SCAFFOLD_REPORT")
    sequence = _json(payloads["FROZEN_EXACT8_SEQUENCE_AUDIT_REPORT"], "SEQUENCE_REPORT")
    if (
        exact4.get("schema_version")
        != "ffq_exact4_existing_split_group_binding_metadata_only_diagnostic_v1_revised1"
        or exact4.get("execution_status") != "PASS"
        or exact4.get("semantic_result") != "INSUFFICIENT_PERSISTED_METADATA"
        or scaffold.get("schema_version") != "ffq_exact8_candidate_scaffold_evidence_v1"
        or scaffold.get("execution_status") != "PASS"
        or scaffold.get("semantic_result")
        != "SCOPED_SCAFFOLD_AXIS_COMPLETE_VERIFIED_EMPTY_KEY_POLICY_NON_LINKING"
    ):
        _fail("FROZEN_REPORT_SCHEMA_OR_SEMANTICS_INVALID")

    exact4_component = exact4.get("persisted_candidate_component", {})
    exact4_events = tuple(sorted(exact4_component.get("component_event_ids", ())))
    scaffold_events = tuple(sorted(
        str(row.get("canonical_event_id"))
        for row in scaffold.get("exact8_event_binding", ()) if type(row) is dict
    ))
    if exact4_events != seeds or scaffold_events != seeds:
        _fail("FROZEN_REPORT_EXACT8_EVENT_BINDING_MISMATCH")
    if (
        exact4_component.get("persisted_ligand_graph_sha256_exactly_equal_across_exact8")
        is not True
        or exact4_component.get("empty_scaffold_identifiers_interpreted_as_dissimilarity")
        is not False
    ):
        _fail("EXACT4_CANDIDATE_GRAPH_OR_SCAFFOLD_SEMANTICS_INVALID")
    scaffold_computation = scaffold.get("candidate_scaffold_computation", {})
    scaffold_coverage = scaffold.get("scaffold_linkage_coverage", {})
    if (
        scaffold_computation.get("component_id") != "FFQ"
        or scaffold_computation.get("classification") != "VERIFIED_EMPTY_MURCKO_SCAFFOLD"
        or scaffold_computation.get("published_canonical_ligand_graph_sha256")
        != _FFQ_GRAPH_SHA256
        or scaffold_computation.get("empty_string_sha256_fabricated_as_key") is not False
        or scaffold_coverage.get("logical_event_member_pair_count") != 456
        or scaffold_coverage.get("verified_empty_key_policy_short_circuit_pair_count") != 456
        or scaffold_coverage.get("actual_nonempty_scaffold_key_comparison_count") != 0
        or scaffold_coverage.get("positive_scaffold_linkage_pair_count") != 0
        or scaffold_coverage.get("unknown_pair_count") != 0
    ):
        _fail("SCAFFOLD_REPORT_POLICY_EVIDENCE_INVALID")
    for row in scaffold.get("exact8_event_binding", ()):
        if (
            type(row) is not dict
            or row.get("classification") != "VERIFIED_EMPTY_MURCKO_SCAFFOLD"
            or row.get("persisted_graph_sha256") != _FFQ_GRAPH_SHA256
            or row.get("persisted_scaffold_key_nonempty") is not False
        ):
            _fail("SCAFFOLD_REPORT_EVENT_BINDING_INVALID")

    scaffold_groups = {
        str(row.get("formal_group_id")): tuple(sorted(row.get("declared_member_event_ids", ())))
        for row in scaffold.get("formal_group_member_scope", ()) if type(row) is dict
    }
    if scaffold_groups != dict(old_by_group):
        _fail("SCAFFOLD_REPORT_FORMAL_MEMBER_SCOPE_MISMATCH")

    formal_table = exact4.get("formal_registry_coverage", {}).get(
        "formal_group_correspondence_table"
    )
    if type(formal_table) is not list or len(formal_table) != 14:
        _fail("EXACT4_FORMAL_GROUP_TABLE_INVALID")
    exact4_groups: dict[str, tuple[str, ...]] = {}
    for row in formal_table:
        if type(row) is not dict:
            _fail("EXACT4_FORMAL_GROUP_ROW_INVALID")
        group_id = str(row.get("formal_group_id"))
        membership = row.get("membership", {})
        exact4_groups[group_id] = tuple(sorted(membership.get("declared_exact_event_ids", ())))
        comparison = row.get("persisted_identifier_comparison", {})
        results = {
            item.get("namespace"): item.get("status")
            for item in comparison.get("key_type_results", ()) if type(item) is dict
        }
        if (
            results.get("LIGAND_GRAPH") != "NO_EQUAL_STRING_IN_SAVED_VALUES"
            or results.get("PROTEIN_ACCESSION") != "NO_EQUAL_STRING_IN_SAVED_VALUES"
            or results.get("PROTEIN_EXACT_SEQUENCE") != "NO_EQUAL_STRING_IN_SAVED_VALUES"
            or results.get("LIGAND_SCAFFOLD") != "CANDIDATE_VALUE_MISSING"
            or comparison.get("equal_match_namespaces") != []
        ):
            _fail("EXACT4_IDENTIFIER_RESULT_NOT_REUSABLE")
    if exact4_groups != dict(old_by_group):
        _fail("EXACT4_FORMAL_MEMBER_SCOPE_MISMATCH")
    relation = exact4.get("persisted_relation_closure", {})
    if relation.get("persisted_identifier_comparison_edges") != []:
        _fail("EXACT4_UNEXPECTED_FORMAL_IDENTIFIER_LINK")

    event_by_id = {event.canonical_event_id: event for event in events}
    sequence_input_rows = [
        *sequence.get("exact8_sequence_inputs", ()),
        *sequence.get("formal_member_sequence_inputs", ()),
    ]
    if len(sequence_input_rows) != 65:
        _fail("SEQUENCE_INPUT_RECORD_COUNT_INVALID")
    for row in sequence_input_rows:
        event_id = row.get("event_id") if type(row) is dict else None
        event = event_by_id.get(str(event_id))
        if (
            event is None or not event.protein_one_letter_sequence
            or row.get("comparison_input_sha256")
            != event.protein_one_letter_sequence_sha256
            or row.get("persisted_sequence_sha256")
            != event.protein_monomer_sequence_sha256
            or row.get("persisted_digest_matches_comparison_input_sha256") is not False
            or row.get("sequence_available_for_comparison") is not True
        ):
            _fail("SEQUENCE_INPUT_DIGEST_BINDING_INVALID")
    expected_pairs = {(seed, event_id) for seed in seeds for members in old_by_group.values() for event_id in members}
    observed_pairs: set[tuple[str, str]] = set()
    for row in sequence.get("event_member_comparisons", ()):
        if type(row) is not dict:
            _fail("SEQUENCE_COMPARISON_ROW_INVALID")
        pair = (str(row.get("exact8_event_id")), str(row.get("formal_member_event_id")))
        left, right = event_by_id.get(pair[0]), event_by_id.get(pair[1])
        if (
            pair in observed_pairs or left is None or right is None
            or row.get("comparison_status") != "VERIFIED_IDENTITY_LT_0_5"
            or row.get("threshold_satisfied") is not False
            or row.get("exact_identity_score") is not None
            or row.get("unknown_reasons") != []
            or row.get("exact8_comparison_input_sha256")
            != left.protein_one_letter_sequence_sha256
            or row.get("formal_member_comparison_input_sha256")
            != right.protein_one_letter_sequence_sha256
        ):
            _fail("SEQUENCE_COMPARISON_BINDING_INVALID")
        observed_pairs.add(pair)
    if observed_pairs != expected_pairs:
        _fail("SEQUENCE_COMPARISON_PAIR_COVERAGE_INVALID")


def _parse_formal_groups(
    payloads: Mapping[str, bytes], repo: Path, events: Sequence[EventEvidenceV1],
    old_by_group: Mapping[str, tuple[str, ...]],
) -> tuple[tuple[FormalGroupV1, ...], str]:
    closure_header, closure_rows = _csv(
        payloads["PUBLISHED_FORMAL_SPLIT_CLOSURE"], "FORMAL_CLOSURE"
    )
    required_closure = {
        "canonical_event_id", "leakage_key", "leakage_group_id_after",
        "formal_split_authoritative_after", "formal_split_after",
    }
    if not required_closure <= set(closure_header):
        _fail("FORMAL_CLOSURE_HEADER_INVALID")
    old_from_owners: dict[str, set[str]] = {}
    split_claims: dict[str, str] = {}
    keys: dict[str, str] = {}
    sources: dict[str, set[str]] = {}
    lineage: dict[str, set[str]] = {}
    for row in closure_rows:
        if row["formal_split_authoritative_after"] != "true":
            continue
        group_id = row["leakage_group_id_after"]
        old_from_owners.setdefault(group_id, set()).add(row["canonical_event_id"])
        split_claims.setdefault(group_id, row["formal_split_after"])
        keys.setdefault(group_id, row["leakage_key"])
        if split_claims[group_id] != row["formal_split_after"] or keys[group_id] != row["leakage_key"]:
            _fail("FORMAL_CLOSURE_GROUP_CONFLICT")
        sources.setdefault(group_id, set()).add("PUBLISHED_FORMAL_SPLIT_CLOSURE")
        lineage.setdefault(group_id, set()).add(
            "PUBLISHED_CLOSURE_IDENTIFIER:" + row["leakage_key"]
        )

    batch = _json(payloads["PUBLISHED_BATCH001_FULL_COMPONENT_REGISTRY"], "BATCH_COMPONENTS")
    if (
        batch.get("schema_version") != "covapie_batch001_formal_leakage_component_registry_v1"
        or batch.get("component_count") != 4 or type(batch.get("components")) is not list
        or len(batch["components"]) != 4
    ):
        _fail("BATCH_COMPONENT_REGISTRY_INVALID")
    for component in batch["components"]:
        if type(component) is not dict:
            _fail("BATCH_COMPONENT_INVALID")
        group_id = str(component.get("formal_group_id"))
        member_ids = component.get("full_member_canonical_event_ids")
        if (
            type(member_ids) is not list or component.get("full_event_count") != len(member_ids)
            or component.get("full_identity_count")
            != len(component.get("full_member_pdb_ligand_identities", ()))
            or component.get("formal_assignment_is_authority_candidate") is not True
        ):
            _fail("BATCH_COMPONENT_MEMBERSHIP_INVALID")
        old_from_owners.setdefault(group_id, set()).update(member_ids)
        split_claims[group_id] = str(component.get("formal_split"))
        keys[group_id] = str(component.get("leakage_key"))
        sources.setdefault(group_id, set()).add("PUBLISHED_BATCH001_FULL_COMPONENT_REGISTRY")
        lineage.setdefault(group_id, set()).add(
            "READ_ONLY_TO_FORMAL_GROUP:"
            + str(component.get("read_only_group_id")) + "->" + group_id
        )
        lineage[group_id].add(
            "READ_ONLY_TO_FORMAL_SPLIT:"
            + str(component.get("read_only_split")) + "->"
            + str(component.get("formal_split"))
        )
    normalized_old = {group_id: tuple(sorted(ids)) for group_id, ids in old_from_owners.items()}
    if normalized_old != dict(old_by_group) or sum(map(len, normalized_old.values())) != 57:
        _fail("OLD57_OWNER_RECONSTRUCTION_MISMATCH")

    current = {group_id: set(ids) for group_id, ids in normalized_old.items()}
    ndu = _json(payloads["PUBLISHED_NDU_FULL_COMPONENT_REGISTRY"], "NDU_COMPONENT")
    components = ndu.get("components") if type(ndu) is dict else None
    if (
        ndu.get("schema_version") != "covapie_batch001_ndu4_full_component_registry_v1"
        or ndu.get("component_count") != 1 or type(components) is not list
        or len(components) != 1
    ):
        _fail("NDU_COMPONENT_REGISTRY_INVALID")
    ndu_row = components[0]
    ndu_group = str(ndu_row.get("formal_group_id"))
    ndu_events = ndu_row.get("full_member_canonical_event_ids")
    if (
        type(ndu_events) is not list or len(ndu_events) != 33
        or ndu_row.get("full_event_count") != len(ndu_events)
        or ndu_row.get("full_identity_count")
        != len(ndu_row.get("full_member_pdb_ligand_identities", ()))
        or ndu_row.get("formal_assignment_status")
        != "EXISTING_FROZEN_GROUP_SPLIT_INHERITED"
        or not current.get(ndu_group, set()) < set(ndu_events)
    ):
        _fail("NDU_FULL_COMPONENT_MEMBERSHIP_INVALID")
    current[ndu_group] = set(ndu_events)
    split_claims[ndu_group] = str(ndu_row.get("formal_split"))
    keys[ndu_group] = str(ndu_row.get("leakage_key"))
    sources.setdefault(ndu_group, set()).add("PUBLISHED_NDU_FULL_COMPONENT_REGISTRY")
    lineage.setdefault(ndu_group, set()).update({
        "NDU_FULL_COMPONENT_EXTENDS_OLD_SCOPE:5->33",
        "EXISTING_FROZEN_GROUP_SPLIT_INHERITED",
    })

    authority = poa_owner.build_covapie_poa_full_component_formal_split_authority_v1(
        repo_root=repo,
    )
    poa_owner.validate_covapie_poa_full_component_formal_split_authority_v1(authority)
    if (
        authority.before_summary.group_count != 14
        or authority.before_summary.identity_count != 45
        or authority.after_summary.group_count != 15
        or authority.after_summary.identity_count != 48
        or len(authority.full_member_canonical_event_ids) != 24
        or len(authority.full_member_pdb_ligand_identities) != 3
        or authority.formal_split_authoritative is not True
    ):
        _fail("POA_CURRENT_FORMAL_POPULATION_CONTRACT_INVALID")
    current[authority.formal_group_id] = set(authority.full_member_canonical_event_ids)
    split_claims[authority.formal_group_id] = authority.formal_split
    keys[authority.formal_group_id] = authority.leakage_key
    sources[authority.formal_group_id] = {"PUBLISHED_POA_FORMAL_POPULATION_OWNER"}
    lineage[authority.formal_group_id] = {
        "ADDITIVE_POA_FORMAL_GROUP_AFTER_FROZEN14",
        "FORMAL_SPLIT_RESERVATION_ONLY_NOT_SAMPLE_ADMISSION",
    }

    owner_groups = {group.final_leakage_group_id: group for group in authority.existing_frozen_groups_before}
    if len(owner_groups) != 14:
        _fail("POA_FROZEN14_INVENTORY_INVALID")
    owner_groups[authority.formal_group_id] = type("_POAGroup", (), {
        "leakage_key": authority.leakage_key,
        "assigned_split": authority.formal_split,
        "member_count": len(authority.full_member_pdb_ligand_identities),
        "member_identities": authority.full_member_pdb_ligand_identities,
    })()
    if set(current) != set(owner_groups) or len(current) != 15:
        _fail("CURRENT_FORMAL_GROUP_SET_INVALID")
    event_by_id = {event.canonical_event_id: event for event in events}
    result: list[FormalGroupV1] = []
    for group_id in sorted(current):
        owner_group = owner_groups[group_id]
        event_ids = tuple(sorted(current[group_id]))
        identities = tuple(sorted({_event_identity(event_id)[2] for event_id in event_ids}))
        if (
            any(event_id not in event_by_id for event_id in event_ids)
            or tuple(owner_group.member_identities) != identities
            or owner_group.member_count != len(identities)
            or owner_group.assigned_split != split_claims[group_id]
        ):
            _fail("CURRENT_FORMAL_GROUP_MEMBER_OR_SPLIT_BINDING_INVALID:" + group_id)
        sources.setdefault(group_id, set()).add(
            "PUBLISHED_POA_FORMAL_POPULATION_OWNER_TRANSITIVE"
        )
        recorded_key = keys.get(group_id)
        if recorded_key and recorded_key != owner_group.leakage_key:
            lineage.setdefault(group_id, set()).add(
                "RECORDED_IDENTIFIER_ALIAS:"
                + recorded_key + "->" + owner_group.leakage_key
            )
        lineage.setdefault(group_id, set()).add(
            "CANONICAL_LEAKAGE_KEY:" + owner_group.leakage_key
        )
        result.append(FormalGroupV1(
            formal_group_id=group_id,
            formal_split=owner_group.assigned_split,
            leakage_key=owner_group.leakage_key,
            member_identity_count=len(identities),
            full_event_count=len(event_ids),
            member_pdb_ligand_identities=identities,
            full_member_canonical_event_ids=event_ids,
            old57_member_canonical_event_ids=old_by_group.get(group_id, ()),
            membership_sources=tuple(sorted(sources[group_id])),
            identifier_lineage=tuple(sorted(lineage[group_id])),
        ))
    if sum(group.full_event_count for group in result) != 109:
        _fail("CURRENT_FORMAL_EVENT_COUNT_INVALID")
    authority_binding_sha = _sha256(canonical_json_bytes_v1(tuple(
        (item.artifact_role, item.repository_relative_path, item.byte_count, item.sha256)
        for item in authority.source_bindings
    )))
    return tuple(result), authority_binding_sha


def _parse_training_dispositions(
    payload: bytes, *, required_event_ids: set[str], readback_scope_event_ids: set[str],
) -> tuple[TrainingDispositionV1, ...]:
    header, rows = _csv(payload, "CURRENT_CENSUS")
    required = {
        "canonical_event_id", "training_use_disposition", "human_training_excluded",
        "formal_split_authoritative", "formal_split",
    }
    if not required <= set(header):
        _fail("CURRENT_CENSUS_HEADER_INVALID")
    result = []
    seen: set[str] = set()
    for row in rows:
        event_id = row["canonical_event_id"]
        if event_id not in readback_scope_event_ids:
            continue
        if event_id in seen:
            _fail("CURRENT_CENSUS_EVENT_DUPLICATED")
        seen.add(event_id)
        if row["human_training_excluded"] not in {"true", "false"} or row["formal_split_authoritative"] not in {"true", "false"}:
            _fail("CURRENT_CENSUS_BOOLEAN_INVALID")
        result.append(TrainingDispositionV1(
            canonical_event_id=event_id,
            training_use_disposition=row["training_use_disposition"],
            human_training_excluded=row["human_training_excluded"] == "true",
            formal_split_authoritative=row["formal_split_authoritative"] == "true",
            formal_split=row["formal_split"],
        ))
    if not required_event_ids <= seen:
        _fail("CURRENT_CENSUS_REQUIRED_EVENT_MISSING")
    return tuple(sorted(result, key=lambda item: item.canonical_event_id))


def load_covapie_ffq_exact8_current_formal_population_linkage_binding_inputs_v1(
    *, repo_root: Path,
) -> BindingInputsV1:
    """Read and SHA-bind the frozen inputs; do not execute local-tools scripts."""

    payloads, bindings = _read_bound_payloads_v1(repo_root)
    events, lane_counts = _parse_universe(payloads)
    sequence_report = _json(
        payloads["FROZEN_EXACT8_SEQUENCE_AUDIT_REPORT"], "SEQUENCE_REPORT"
    )
    old_by_group, seeds = _member_sets_from_sequence_report(sequence_report)
    _validate_old_evidence_reports(payloads, events, old_by_group, seeds)
    formal_groups, formal_authority_sha = _parse_formal_groups(
        payloads, repo_root.resolve(), events, old_by_group,
    )
    old_ids = {event_id for group in formal_groups for event_id in group.old57_member_canonical_event_ids}
    frozen_report_pairs = tuple(sorted(
        (seed, member) for seed in seeds for member in old_ids
    ))
    dispositions = _parse_training_dispositions(
        payloads["CURRENT_GLOBAL_DISPOSITION_CENSUS"],
        required_event_ids=set(seeds),
        readback_scope_event_ids={
            event.canonical_event_id for event in events
        },
    )
    disposition_by_id = {item.canonical_event_id: item for item in dispositions}
    if any(
        disposition_by_id[seed].training_use_disposition
        != ("INCLUDE" if ":3VCY:" in seed else "EXCLUDE_FROM_TRAINING_ONLY")
        for seed in seeds
    ):
        _fail("EXACT8_TRAINING_DISPOSITION_CHANGED")
    return BindingInputsV1(
        source_bindings=bindings,
        formal_authority_source_binding_sha256=formal_authority_sha,
        predictor_lane_counts=lane_counts,
        universe_events=events,
        formal_groups=formal_groups,
        specified_seed_event_ids=seeds,
        required_seed_event_ids=seeds,
        frozen_report_covered_pairs=frozen_report_pairs,
        verified_empty_scaffold_graph_sha256=_FFQ_GRAPH_SHA256,
        training_dispositions=dispositions,
        expected_formal_population_inventory_sha256=_formal_inventory_sha256(formal_groups),
    )


def _normalize_groups(groups: Sequence[FormalGroupV1]) -> tuple[FormalGroupV1, ...]:
    by_id: dict[str, FormalGroupV1] = {}
    all_events: set[str] = set()
    all_identities: set[str] = set()
    for group in groups:
        if type(group) is not FormalGroupV1:
            _fail("FORMAL_GROUP_TYPE_INVALID")
        event_ids = group.full_member_canonical_event_ids
        identities = group.member_pdb_ligand_identities
        old_ids = group.old57_member_canonical_event_ids
        if (
            not group.formal_group_id or group.formal_group_id in by_id
            or group.formal_split not in SPLITS_V1 or not group.leakage_key
            or type(group.member_identity_count) is not int
            or type(group.full_event_count) is not int
            or group.member_identity_count != len(identities)
            or group.full_event_count != len(event_ids)
            or group.member_identity_count <= 0 or group.full_event_count <= 0
            or event_ids != tuple(sorted(set(event_ids)))
            or identities != tuple(sorted(set(identities)))
            or old_ids != tuple(sorted(set(old_ids)))
            or not set(old_ids) <= set(event_ids)
            or not group.membership_sources
            or not group.identifier_lineage
        ):
            _fail("FORMAL_GROUP_FIELDS_OR_COUNTS_INVALID")
        derived = tuple(sorted({_event_identity(event_id)[2] for event_id in event_ids}))
        if derived != identities:
            _fail("FORMAL_EVENT_AND_IDENTITY_COUNTS_CONFLATED")
        if all_events.intersection(event_ids) or all_identities.intersection(identities):
            _fail("FORMAL_GROUP_MEMBERSHIP_OVERLAP")
        all_events.update(event_ids)
        all_identities.update(identities)
        by_id[group.formal_group_id] = group
    if not by_id:
        _fail("FORMAL_GROUP_POPULATION_EMPTY")
    return tuple(by_id[group_id] for group_id in sorted(by_id))


def _normalize_dispositions(
    rows: Sequence[TrainingDispositionV1], universe_ids: set[str],
) -> dict[str, TrainingDispositionV1]:
    result: dict[str, TrainingDispositionV1] = {}
    for row in rows:
        if (
            type(row) is not TrainingDispositionV1
            or row.canonical_event_id not in universe_ids
            or row.canonical_event_id in result
            or not row.training_use_disposition
            or type(row.human_training_excluded) is not bool
            or type(row.formal_split_authoritative) is not bool
            or (row.formal_split_authoritative and row.formal_split not in SPLITS_V1)
            or (not row.formal_split_authoritative and row.formal_split != "")
        ):
            _fail("TRAINING_DISPOSITION_INVALID")
        result[row.canonical_event_id] = row
    return result


def _validate_inputs(inputs: BindingInputsV1) -> tuple[
    tuple[EventEvidenceV1, ...], tuple[FormalGroupV1, ...],
    dict[str, TrainingDispositionV1], set[tuple[str, str]],
]:
    if type(inputs) is not BindingInputsV1:
        _fail("INPUT_TYPE_INVALID")
    if inputs.canonical_exact5 != CANONICAL_EXACT5_V1:
        _fail("CANONICAL_EXACT5_CONTRACT_CHANGED")
    if (
        not inputs.formal_authority_source_binding_sha256
        or _SHA_RE.fullmatch(inputs.formal_authority_source_binding_sha256) is None
        or _SHA_RE.fullmatch(inputs.expected_formal_population_inventory_sha256) is None
    ):
        _fail("INPUT_SEMANTIC_BINDING_DIGEST_INVALID")
    if inputs.source_bindings:
        roles = [item.role for item in inputs.source_bindings]
        if (
            len(set(roles)) != len(roles)
            or any(type(item) is not SourceBindingV1 for item in inputs.source_bindings)
            or any(
                not item.role or not item.path_scope or not item.relative_path
                or type(item.byte_count) is not int or item.byte_count < 0
                or _SHA_RE.fullmatch(item.sha256) is None or not item.schema
                for item in inputs.source_bindings
            )
        ):
            _fail("INPUT_SOURCE_BINDING_INVALID")
    events = _normalize_events(inputs.universe_events)
    event_by_id = {event.canonical_event_id: event for event in events}
    groups = _normalize_groups(inputs.formal_groups)
    if _formal_inventory_sha256(groups) != inputs.expected_formal_population_inventory_sha256:
        _fail("FORMAL_POPULATION_INVENTORY_BINDING_MISMATCH")
    formal_ids = {event_id for group in groups for event_id in group.full_member_canonical_event_ids}
    if not formal_ids <= set(event_by_id):
        _fail("FORMAL_MEMBER_ABSENT_FROM_PREDICTOR_UNIVERSE")
    specified = inputs.specified_seed_event_ids
    required = inputs.required_seed_event_ids
    if (
        specified != tuple(sorted(set(specified)))
        or required != tuple(sorted(set(required)))
        or specified != required or not specified
        or not set(specified) <= set(event_by_id)
    ):
        _fail("SPECIFIED_SEED_INVENTORY_INVALID")
    if inputs.verified_empty_scaffold_graph_sha256 and _SHA_RE.fullmatch(
        inputs.verified_empty_scaffold_graph_sha256
    ) is None:
        _fail("EMPTY_SCAFFOLD_GRAPH_BINDING_INVALID")
    old_ids = {event_id for group in groups for event_id in group.old57_member_canonical_event_ids}
    expected_reuse = {(seed, member) for seed in specified for member in old_ids}
    historical_overlap = set(inputs.frozen_report_covered_pairs)
    if (
        len(historical_overlap) != len(inputs.frozen_report_covered_pairs)
        or historical_overlap != expected_reuse
    ):
        _fail("FROZEN_REPORT_COVERAGE_PAIR_SCOPE_INVALID")
    dispositions = _normalize_dispositions(inputs.training_dispositions, set(event_by_id))
    if not set(specified) <= set(dispositions):
        _fail("SPECIFIED_SEED_DISPOSITION_MISSING")
    for event_id in specified:
        row = dispositions[event_id]
        expected = (
            "INCLUDE" if ":3VCY:" in event_id else
            "EXCLUDE_FROM_TRAINING_ONLY" if ":4R7U:" in event_id else None
        )
        if expected is not None and (
            row.training_use_disposition != expected
            or row.human_training_excluded != (expected == "EXCLUDE_FROM_TRAINING_ONLY")
            or row.formal_split_authoritative is not False
            or row.formal_split != ""
        ):
            _fail("SPECIFIED_SEED_TRAINING_DISPOSITION_CHANGED")
    return events, groups, dispositions, historical_overlap


def _is_verified_empty_scaffold(event: EventEvidenceV1, graph_sha256: str) -> bool:
    return bool(
        graph_sha256 and event.ligand_component_id == "FFQ"
        and event.ligand_graph_sha256 == graph_sha256
        and event.ligand_scaffold_sha256 == ""
    )


def _axis_status(
    axis: str, left: EventEvidenceV1, right: EventEvidenceV1,
    *, empty_scaffold_graph_sha256: str,
) -> tuple[str, bool]:
    if axis == "LIGAND_SCAFFOLD":
        if _is_verified_empty_scaffold(left, empty_scaffold_graph_sha256) or _is_verified_empty_scaffold(
            right, empty_scaffold_graph_sha256
        ):
            return "NEGATIVE", True
        left_value, right_value = left.ligand_scaffold_sha256, right.ligand_scaffold_sha256
    elif axis == "LIGAND_GRAPH":
        left_value, right_value = left.ligand_graph_sha256, right.ligand_graph_sha256
    elif axis == "PROTEIN_ACCESSION":
        left_value, right_value = left.protein_accession, right.protein_accession
    elif axis == "PROTEIN_EXACT_SEQUENCE":
        left_value = left.protein_monomer_sequence_sha256
        right_value = right.protein_monomer_sequence_sha256
    elif axis == "PROTEIN_SEQUENCE_IDENTITY_GE_0.5":
        left_value = left.protein_one_letter_sequence
        right_value = right.protein_one_letter_sequence
        if not left_value or not right_value:
            return "UNKNOWN", False
        linked = linkage_owner._policy_global_identity_at_least_half_v1(
            left_value, right_value
        )
        return ("POSITIVE" if linked else "NEGATIVE"), False
    else:
        _fail("UNKNOWN_LINKAGE_AXIS")
    if not left_value or not right_value:
        return "UNKNOWN", False
    return ("POSITIVE" if left_value == right_value else "NEGATIVE"), False


def _pair_statuses(
    left: EventEvidenceV1, right: EventEvidenceV1, *, empty_graph: str,
) -> tuple[tuple[str, str, bool], ...]:
    return tuple(
        (axis, *_axis_status(
            axis, left, right, empty_scaffold_graph_sha256=empty_graph,
        ))
        for axis in AXES_V1
    )


def _close_component(
    seeds: Sequence[str], event_by_id: Mapping[str, EventEvidenceV1], *, empty_graph: str,
) -> tuple[tuple[str, ...], dict[str, str]]:
    closure = set(seeds)
    discovery_parent: dict[str, str] = {}
    while True:
        additions: dict[str, str] = {}
        outside = sorted(set(event_by_id) - closure)
        for left_id in sorted(closure):
            left = event_by_id[left_id]
            for right_id in outside:
                statuses = _pair_statuses(
                    left, event_by_id[right_id], empty_graph=empty_graph,
                )
                if any(status == "POSITIVE" for _axis, status, _short in statuses):
                    additions.setdefault(right_id, left_id)
        if not additions:
            break
        closure.update(additions)
        discovery_parent.update(additions)
    return tuple(sorted(closure)), discovery_parent


def _pairs_touching(ids: Sequence[str], selected: set[str]) -> tuple[tuple[str, str], ...]:
    return tuple(
        (left, right)
        for index, left in enumerate(ids)
        for right in ids[index + 1:]
        if left in selected or right in selected
    )


def _coverage(
    *, pairs: Sequence[tuple[str, str]], event_by_id: Mapping[str, EventEvidenceV1],
    empty_graph: str, frozen_report_covered_pairs: set[tuple[str, str]],
    annotate_frozen_report_overlap: bool,
) -> tuple[AxisCoverageV1, ...]:
    counters = {axis: Counter() for axis in AXES_V1}
    for left_id, right_id in pairs:
        statuses = _pair_statuses(
            event_by_id[left_id], event_by_id[right_id], empty_graph=empty_graph,
        )
        canonical_pair = (left_id, right_id)
        reverse_pair = (right_id, left_id)
        historical_overlap = annotate_frozen_report_overlap and (
            canonical_pair in frozen_report_covered_pairs
            or reverse_pair in frozen_report_covered_pairs
        )
        for axis, status, short_circuit in statuses:
            counters[axis][status] += 1
            if short_circuit:
                counters[axis]["SHORT_CIRCUIT"] += 1
            elif status != "UNKNOWN":
                counters[axis]["CURRENT_EVIDENCE_JUDGMENT"] += 1
            if historical_overlap:
                counters[axis]["FROZEN_REPORT_OVERLAP"] += 1
    result = tuple(AxisCoverageV1(
        axis=axis,
        logical_pair_count=len(pairs),
        current_evidence_judged_logical_pair_count=(
            counters[axis]["CURRENT_EVIDENCE_JUDGMENT"]
        ),
        policy_short_circuit_logical_pair_count=counters[axis]["SHORT_CIRCUIT"],
        unknown_logical_pair_count=counters[axis]["UNKNOWN"],
        frozen_report_coverage_overlap_pair_count=(
            counters[axis]["FROZEN_REPORT_OVERLAP"]
        ),
        positive_pair_count=counters[axis]["POSITIVE"],
        negative_pair_count=counters[axis]["NEGATIVE"],
    ) for axis in AXES_V1)
    for item in result:
        if (
            item.positive_pair_count + item.negative_pair_count
            + item.unknown_logical_pair_count != item.logical_pair_count
            or item.current_evidence_judged_logical_pair_count
            + item.policy_short_circuit_logical_pair_count
            + item.unknown_logical_pair_count != item.logical_pair_count
            or not 0 <= item.frozen_report_coverage_overlap_pair_count <= item.logical_pair_count
        ):
            _fail("AXIS_COVERAGE_PARTITION_INVALID")
    return result


def _source_semantic_sha256(inputs: BindingInputsV1) -> str:
    return _sha256(canonical_json_bytes_v1({
        "source_bindings": inputs.source_bindings,
        "formal_authority_source_binding_sha256": inputs.formal_authority_source_binding_sha256,
        "formal_population_inventory_sha256": inputs.expected_formal_population_inventory_sha256,
        "universe_event_inventory_sha256": _inventory_sha256(
            list({item.canonical_event_id for item in inputs.universe_events})
        ),
        "specified_seed_event_ids": inputs.specified_seed_event_ids,
        "axes": AXES_V1,
    }))


def _result_output_sha256(
    result: FFQExact8CurrentFormalPopulationLinkageBindingResultV1,
) -> str:
    value = _primitive(result)
    assert isinstance(value, dict)
    value.pop("output_semantic_sha256", None)
    return _sha256(canonical_json_bytes_v1(value))


def compute_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(
    inputs: BindingInputsV1,
) -> FFQExact8CurrentFormalPopulationLinkageBindingResultV1:
    """Purely compute the scoped component and formal-population relation."""

    events, groups, dispositions, historical_overlap_pairs = _validate_inputs(inputs)
    event_by_id = {event.canonical_event_id: event for event in events}
    closure, _discovery_parent = _close_component(
        inputs.specified_seed_event_ids, event_by_id,
        empty_graph=inputs.verified_empty_scaffold_graph_sha256,
    )
    closure_set = set(closure)
    all_ids = tuple(event_by_id)
    universe_pairs = _pairs_touching(all_ids, closure_set)
    universe_coverage = _coverage(
        pairs=universe_pairs, event_by_id=event_by_id,
        empty_graph=inputs.verified_empty_scaffold_graph_sha256,
        frozen_report_covered_pairs=historical_overlap_pairs,
        annotate_frozen_report_overlap=True,
    )

    component_edges: list[VerifiedEdgeV1] = []
    unknown_relations: list[UnknownRelationV1] = []
    for left_id, right_id in universe_pairs:
        statuses = _pair_statuses(
            event_by_id[left_id], event_by_id[right_id],
            empty_graph=inputs.verified_empty_scaffold_graph_sha256,
        )
        positives = tuple(axis for axis, status, _short in statuses if status == "POSITIVE")
        unknowns = tuple(axis for axis, status, _short in statuses if status == "UNKNOWN")
        if positives and left_id in closure_set and right_id in closure_set:
            component_edges.append(VerifiedEdgeV1(
                left_event_id=left_id, right_event_id=right_id,
                positive_axes=positives, unknown_axes=unknowns,
                left_source_role=event_by_id[left_id].source_role,
                right_source_role=event_by_id[right_id].source_role,
            ))
        if unknowns and (left_id in closure_set) != (right_id in closure_set):
            closure_id, universe_id = (
                (left_id, right_id) if left_id in closure_set else (right_id, left_id)
            )
            unknown_relations.append(UnknownRelationV1(
                closure_event_id=closure_id,
                universe_event_id=universe_id,
                unknown_axes=unknowns,
            ))
    unknown_relations.sort(key=lambda item: (
        item.closure_event_id, item.universe_event_id, item.unknown_axes,
    ))

    formal_ids = tuple(sorted(
        event_id for group in groups for event_id in group.full_member_canonical_event_ids
    ))
    formal_pairs = tuple(
        (closure_id, formal_id) for closure_id in closure for formal_id in formal_ids
    )
    formal_coverage = _coverage(
        pairs=formal_pairs, event_by_id=event_by_id,
        empty_graph=inputs.verified_empty_scaffold_graph_sha256,
        frozen_report_covered_pairs=historical_overlap_pairs,
        annotate_frozen_report_overlap=True,
    )
    member_coverage: list[FormalMemberCoverageV1] = []
    group_reachability: list[FormalGroupReachabilityV1] = []
    for group in groups:
        group_positive_axes: set[str] = set()
        group_unknown = 0
        for member_id in group.full_member_canonical_event_ids:
            positive = Counter()
            unknown = Counter()
            comparisons = Counter()
            for closure_id in closure:
                for axis, status, _short in _pair_statuses(
                    event_by_id[closure_id], event_by_id[member_id],
                    empty_graph=inputs.verified_empty_scaffold_graph_sha256,
                ):
                    comparisons[axis] += 1
                    if status == "POSITIVE":
                        positive[axis] += 1
                        group_positive_axes.add(axis)
                    elif status == "UNKNOWN":
                        unknown[axis] += 1
                        group_unknown += 1
            member_coverage.append(FormalMemberCoverageV1(
                formal_group_id=group.formal_group_id,
                formal_member_event_id=member_id,
                comparison_count_by_axis=tuple((axis, comparisons[axis]) for axis in AXES_V1),
                positive_count_by_axis=tuple((axis, positive[axis]) for axis in AXES_V1),
                unknown_count_by_axis=tuple((axis, unknown[axis]) for axis in AXES_V1),
                all_axes_complete=not any(unknown.values()),
            ))
        group_reachability.append(FormalGroupReachabilityV1(
            formal_group_id=group.formal_group_id,
            formal_split=group.formal_split,
            full_event_count=group.full_event_count,
            member_identity_count=group.member_identity_count,
            positive_axes=tuple(sorted(group_positive_axes)),
            unknown_pair_count=group_unknown,
            reachable=bool(group_positive_axes),
        ))
    member_coverage.sort(key=lambda item: (
        item.formal_group_id, item.formal_member_event_id,
    ))
    group_reachability.sort(key=lambda item: item.formal_group_id)
    reachable_groups = tuple(
        item.formal_group_id for item in group_reachability if item.reachable
    )
    reachable_splits = tuple(sorted({
        item.formal_split for item in group_reachability if item.reachable
    }))
    cross_split = len(reachable_splits) > 1
    formal_complete = all(item.all_axes_complete for item in member_coverage)
    closure_complete = not unknown_relations
    if cross_split:
        status = STATUS_CROSS_SPLIT_CONFLICT
    elif not closure_complete or not formal_complete:
        status = STATUS_INCOMPLETE
    elif reachable_groups:
        status = STATUS_COMPLETE_WITH_LINKAGE
    else:
        status = STATUS_COMPLETE_NO_LINKAGE

    old_ids = {event_id for group in groups for event_id in group.old57_member_canonical_event_ids}
    formal_event_set = set(formal_ids)
    seed_dispositions = tuple(dispositions[event_id] for event_id in inputs.specified_seed_event_ids)
    newly_discovered = tuple(sorted(closure_set - set(inputs.specified_seed_event_ids)))
    new_dispositions = tuple(
        dispositions[event_id] for event_id in newly_discovered
        if event_id in dispositions
    )
    new_missing_dispositions = tuple(
        event_id for event_id in newly_discovered if event_id not in dispositions
    )
    preliminary = FFQExact8CurrentFormalPopulationLinkageBindingResultV1(
        schema_version=SCHEMA_VERSION_V1,
        source_bindings=inputs.source_bindings,
        source_semantic_sha256=_source_semantic_sha256(inputs),
        formal_authority_source_binding_sha256=inputs.formal_authority_source_binding_sha256,
        predictor_lane_counts=inputs.predictor_lane_counts,
        predictor_universe_event_count=len(events),
        predictor_universe_event_inventory_sha256=_inventory_sha256(all_ids),
        formal_groups=groups,
        current_formal_group_count=len(groups),
        current_formal_event_count=len(formal_event_set),
        current_formal_identity_count=sum(group.member_identity_count for group in groups),
        old_formal_scope_event_count=len(old_ids),
        formal_population_added_event_ids=tuple(sorted(formal_event_set - old_ids)),
        specified_seed_event_ids=inputs.specified_seed_event_ids,
        closure_event_ids=closure,
        newly_discovered_linked_event_ids=newly_discovered,
        verified_component_edges=tuple(component_edges),
        closure_unknown_relations=tuple(unknown_relations),
        closure_complete_within_frozen_universe=closure_complete,
        formal_population_comparison_complete=formal_complete,
        universe_axis_coverage=universe_coverage,
        formal_population_axis_coverage=formal_coverage,
        formal_member_coverage=tuple(member_coverage),
        formal_group_reachability=tuple(group_reachability),
        reachable_formal_group_ids=reachable_groups,
        reachable_formal_splits=reachable_splits,
        cross_split_conflict=cross_split,
        binding_status=status,
        seed_training_dispositions=seed_dispositions,
        newly_discovered_training_dispositions=new_dispositions,
        newly_discovered_missing_disposition_event_ids=new_missing_dispositions,
        seed_disposition_readback_complete=True,
        newly_discovered_disposition_readback_complete=not new_missing_dispositions,
        closure_disposition_readback_complete=not new_missing_dispositions,
        permissions=_PERMISSIONS_V1,
        canonical_exact5=CANONICAL_EXACT5_V1,
        output_semantic_sha256="",
    )
    return replace(preliminary, output_semantic_sha256=_result_output_sha256(preliminary))


def validate_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(
    result: FFQExact8CurrentFormalPopulationLinkageBindingResultV1,
    *, inputs: BindingInputsV1,
) -> bool:
    """Recompute sets, counts, relations, permissions, and semantic digest."""

    if type(result) is not FFQExact8CurrentFormalPopulationLinkageBindingResultV1:
        _fail("RESULT_TYPE_INVALID")
    expected = compute_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(inputs)
    if result != expected:
        _fail("RESULT_DOES_NOT_MATCH_RECOMPUTED_BINDING")
    if result.output_semantic_sha256 != _result_output_sha256(result):
        _fail("RESULT_OUTPUT_SEMANTIC_SHA256_INVALID")
    if result.permissions != _PERMISSIONS_V1 or result.canonical_exact5 != CANONICAL_EXACT5_V1:
        _fail("RESULT_PERMISSION_OR_MASK_BOUNDARY_INVALID")
    return True


def build_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(
    *, repo_root: Path,
) -> FFQExact8CurrentFormalPopulationLinkageBindingResultV1:
    """Load frozen sources, compute the non-authoritative binding, and validate."""

    inputs = load_covapie_ffq_exact8_current_formal_population_linkage_binding_inputs_v1(
        repo_root=repo_root,
    )
    _validate_source_bindings(inputs.source_bindings)
    if (
        len(inputs.specified_seed_event_ids) != 8
        or sum(":3VCY:" in event_id for event_id in inputs.specified_seed_event_ids) != 4
        or sum(":4R7U:" in event_id for event_id in inputs.specified_seed_event_ids) != 4
    ):
        _fail("REAL_EXACT8_SEED_CONTRACT_INVALID")
    result = compute_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(inputs)
    validate_covapie_ffq_exact8_current_formal_population_linkage_binding_v1(
        result, inputs=inputs,
    )
    return result
