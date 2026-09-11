from __future__ import annotations

import copy
from dataclasses import FrozenInstanceError, fields, replace
from functools import lru_cache
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable, Mapping

import pytest
import torch

from covalent_ext import (
    covapie_ffq_exact4_post_source_index_binding_v1 as subject,
)
from covalent_ext import (
    covapie_ffq_project_level_authority_ingestion_and_effective_supervision_successor_v1
    as effective_owner,
)


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT.parent / "covapie-state"
UNIT = STATE / (
    "manual-review-aids/cumulative1000-high-yield-calibration-v1/"
    "FFQ_COVAPIE_BULK_REVIEW_UNIT_431D2725ADFC9E9D"
)
LABEL_USE_PATH = UNIT / (
    "post-distance-label-use-formal-human-decision-v1/"
    "ffq_post_label_use_formal_human_decision_v1.json"
)
OBSERVATION_PATH = UNIT / (
    "post-geometry-formal-human-decision-v1/"
    "ffq_post_geometry_formal_human_decision_v1.json"
)
STRUCTURE_PATH = STATE / (
    "bulk-model-usable-auto-admission-scaleup-v1/ranks-0501-1000/"
    "attempt-001/cache/rcsb/structures/3VCY.cif.gz"
)
CHECKER_PATH = ROOT / (
    "scripts/check_covapie_ffq_project_level_authority_ingestion_and_"
    "effective_supervision_successor_v1.py"
)
EVENT_4R7U_A = "COVAPIE_CYS_SG_EVENT_V1:4R7U:A:CYS:116-:SG:F:FFQ:C1"

checker_spec = importlib.util.spec_from_file_location(
    "ffq_exact4_post_binding_effective_checker", CHECKER_PATH
)
assert checker_spec is not None and checker_spec.loader is not None
checker = importlib.util.module_from_spec(checker_spec)
sys.modules[checker_spec.name] = checker
checker_spec.loader.exec_module(checker)


def _required_bytes(path: Path, expected_sha256: str) -> bytes:
    assert path.is_file() and not path.is_symlink()
    payload = path.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == expected_sha256
    return payload


@pytest.fixture(scope="module")
def frozen_inputs() -> dict[str, bytes]:
    label = _required_bytes(LABEL_USE_PATH, subject.LABEL_USE_FORMAL_SHA256_V1)
    observation = _required_bytes(
        OBSERVATION_PATH, subject.POST_OBSERVATION_FORMAL_SHA256_V1
    )
    structure = _required_bytes(STRUCTURE_PATH, subject.STRUCTURE_PAYLOAD_SHA256_V1)
    assert len(label) == 29507
    assert len(observation) == 86399
    assert len(structure) == subject.STRUCTURE_PAYLOAD_BYTE_COUNT_V1
    return {"label": label, "observation": observation, "structure": structure}


@lru_cache(maxsize=1)
def _real_effective_records() -> tuple[dict[str, Any], ...]:
    inputs = checker._read_inputs(ROOT)
    checker._validate_receipts_and_canonical_authorities(inputs)
    build_inputs = {
        key: value
        for key, value in inputs.items()
        if key not in ("family_receipt", "rule_receipt")
    }
    result = effective_owner.build_covapie_ffq_project_level_authority_effective_supervision_v1(
        **build_inputs
    )
    effective_owner.validate_covapie_ffq_project_level_authority_effective_supervision_v1(
        result
    )
    records = result["effective_supervision_records"]
    assert type(records) is list and len(records) == 8
    return tuple(records)


def _record(event_id: str) -> dict[str, Any]:
    matches = [
        record
        for record in _real_effective_records()
        if record.get("canonical_event_id") == event_id
    ]
    assert len(matches) == 1
    return copy.deepcopy(matches[0])


def _samples(
    structure_payload: bytes,
    event_ids: tuple[str, ...] = subject._EVENT_IDS,
) -> list[dict[str, object]]:
    return [
        {
            "cif_gz_payload": structure_payload,
            "effective_supervision_record": _record(event_id),
            "canonical_task_id": 0,
        }
        for event_id in event_ids
    ]


def _build(
    frozen_inputs: Mapping[str, bytes],
    *,
    event_ids: tuple[str, ...] = subject._EVENT_IDS,
) -> subject.FFQExact4PostSourceIndexBindingResultV1:
    return subject.build_covapie_ffq_exact4_post_source_index_binding_v1(
        samples=_samples(frozen_inputs["structure"], event_ids),
        label_use_formal_bytes=frozen_inputs["label"],
        post_observation_formal_bytes=frozen_inputs["observation"],
    )


@pytest.fixture(scope="module")
def canonical_result(
    frozen_inputs: Mapping[str, bytes],
) -> subject.FFQExact4PostSourceIndexBindingResultV1:
    return _build(frozen_inputs)


@pytest.fixture(scope="module")
def reversed_result(
    frozen_inputs: Mapping[str, bytes],
) -> subject.FFQExact4PostSourceIndexBindingResultV1:
    return _build(frozen_inputs, event_ids=tuple(reversed(subject._EVENT_IDS)))


@pytest.fixture(scope="module")
def validation_context(
    frozen_inputs: Mapping[str, bytes],
    canonical_result: subject.FFQExact4PostSourceIndexBindingResultV1,
) -> tuple[
    tuple[Mapping[str, Any], ...],
    dict[str, subject._ResolvedEventSourceV1],
    subject.alignment_owner.FFQRealStructureMicrobatchAlignmentV1,
]:
    label = subject._strict_frozen_json(
        frozen_inputs["label"],
        expected_sha256=subject.LABEL_USE_FORMAL_SHA256_V1,
        label="LABEL_USE_FORMAL",
    )
    observation = subject._strict_frozen_json(
        frozen_inputs["observation"],
        expected_sha256=subject.POST_OBSERVATION_FORMAL_SHA256_V1,
        label="POST_OBSERVATION_FORMAL",
    )
    formal = subject._validate_formal_documents_v1(label, observation)
    samples = subject._validate_samples(_samples(frozen_inputs["structure"]))
    resolved = subject._resolve_structure_sources(samples, formal)
    return samples, resolved, canonical_result.structural_alignment


def _assert_no_float(value: object) -> None:
    assert type(value) is not float
    if isinstance(value, tuple):
        for child in value:
            _assert_no_float(child)
    elif hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_float(getattr(value, field.name))


def _assert_alignments_identical(left: object, right: object) -> None:
    assert type(left) is type(right)
    for field in fields(left):
        left_value = getattr(left, field.name)
        right_value = getattr(right, field.name)
        if type(left_value) is dict:
            assert left_value.keys() == right_value.keys()
            assert all(
                torch.equal(left_value[key], right_value[key]) for key in left_value
            ), field.name
        elif type(left_value) is torch.Tensor:
            assert torch.equal(left_value, right_value), field.name
        else:
            assert left_value == right_value, field.name


def test_real_exact4_canonical_order_binds_approved_sources_without_target_values(
    canonical_result: subject.FFQExact4PostSourceIndexBindingResultV1,
) -> None:
    bindings = canonical_result.source_index_bindings
    assert tuple(binding.canonical_event_id for binding in bindings) == subject._EVENT_IDS
    assert tuple(binding.batch_ordinal for binding in bindings) == (0, 1, 2, 3)
    assert tuple(binding.ligand_C1.source_atom_site_row_index_0based for binding in bindings) == (
        12535,
        12632,
        12695,
        12759,
    )
    assert tuple(binding.protein_SG.source_atom_site_row_index_0based for binding in bindings) == (
        867,
        3990,
        7114,
        10257,
    )
    assert tuple(binding.ligand_C1.local_node_index for binding in bindings) == (0, 0, 0, 0)
    assert tuple(binding.ligand_C1.flat_node_index for binding in bindings) == (0, 8, 16, 24)
    assert tuple(binding.protein_SG.local_node_index for binding in bindings) == (64, 84, 84, 83)
    assert tuple(binding.protein_SG.flat_node_index for binding in bindings) == (64, 248, 413, 588)
    assert tuple(binding.ligand_C1.source_identity.atom_site_id for binding in bindings) == (
        "12536",
        "12633",
        "12696",
        "12760",
    )
    assert tuple(binding.protein_SG.source_identity.atom_site_id for binding in bindings) == (
        "868",
        "3991",
        "7115",
        "10258",
    )
    for index, binding in enumerate(bindings):
        assert binding.task_semantic_name == "warhead_only"
        assert binding.canonical_task_id == 0
        assert binding.purpose == "independent_hidden_post_distance_v1"
        assert binding.component_index == 1
        assert binding.unit == "angstrom"
        assert binding.label_use_event_decision_locator == f"/formal_event_decisions/{index}"
        assert binding.post_observation_event_locator == f"/formal_event_decisions/{index}"
        assert binding.post_observation_distance_field_locator == (
            f"/formal_event_decisions/{index}/approved_observations/"
            "SG_C1_observed_distance"
        )
        assert binding.pocket_seed_policy == "fixed_scaffold_warhead_only_v1"
        _assert_no_float(binding)
    with pytest.raises(FrozenInstanceError):
        bindings[0].batch_ordinal = 9  # type: ignore[misc]

    alignment = canonical_result.structural_alignment
    assert frozenset(alignment.model_input_batch) == subject._MODEL_INPUT_FIELDS
    assert not torch.any(alignment.sample_training_admitted).item()
    assert not torch.any(alignment.geometry_target_available).item()
    assert alignment.model_forward is False
    assert alignment.training_performed is False
    assert not hasattr(canonical_result, "training_target")
    assert not hasattr(canonical_result, "geometry_supervision")
    assert not hasattr(canonical_result, "loss_mask")


def test_real_reordered_batch_reassembles_indices_while_source_locators_stay_event_bound(
    canonical_result: subject.FFQExact4PostSourceIndexBindingResultV1,
    reversed_result: subject.FFQExact4PostSourceIndexBindingResultV1,
) -> None:
    reversed_ids = tuple(reversed(subject._EVENT_IDS))
    assert reversed_result.structural_alignment.sample_identities == reversed_ids
    assert tuple(binding.canonical_event_id for binding in reversed_result.source_index_bindings) == reversed_ids
    assert tuple(binding.batch_ordinal for binding in reversed_result.source_index_bindings) == (0, 1, 2, 3)
    assert tuple(binding.ligand_C1.flat_node_index for binding in reversed_result.source_index_bindings) == (0, 8, 16, 24)
    assert tuple(binding.protein_SG.flat_node_index for binding in reversed_result.source_index_bindings) == (83, 248, 424, 569)

    canonical = {binding.canonical_event_id: binding for binding in canonical_result.source_index_bindings}
    reordered = {binding.canonical_event_id: binding for binding in reversed_result.source_index_bindings}
    for event_id in subject._EVENT_IDS:
        assert reordered[event_id].label_use_event_decision_locator == canonical[event_id].label_use_event_decision_locator
        assert reordered[event_id].post_observation_event_locator == canonical[event_id].post_observation_event_locator
        assert reordered[event_id].post_observation_distance_field_locator == canonical[event_id].post_observation_distance_field_locator
        assert reordered[event_id].ligand_C1.source_atom_site_row_index_0based == canonical[event_id].ligand_C1.source_atom_site_row_index_0based
        assert reordered[event_id].protein_SG.source_atom_site_row_index_0based == canonical[event_id].protein_SG.source_atom_site_row_index_0based
    assert reordered[subject._EVENT_IDS[0]].ligand_C1.flat_node_index == 24
    assert reordered[subject._EVENT_IDS[0]].protein_SG.flat_node_index == 569
    assert reordered[subject._EVENT_IDS[-1]].ligand_C1.flat_node_index == 0
    assert reordered[subject._EVENT_IDS[-1]].protein_SG.flat_node_index == 83


def _missing(samples: list[dict[str, object]]) -> object:
    return samples[:-1]


def _extra(samples: list[dict[str, object]]) -> object:
    return samples + [copy.deepcopy(samples[0])]


def _duplicate(samples: list[dict[str, object]]) -> object:
    samples[-1] = copy.deepcopy(samples[0])
    return samples


def _excluded_4r7u(samples: list[dict[str, object]]) -> object:
    samples[-1]["effective_supervision_record"] = _record(EVENT_4R7U_A)
    return samples


def _wrong_task(samples: list[dict[str, object]]) -> object:
    samples[0]["canonical_task_id"] = 3
    return samples


@pytest.mark.parametrize(
    ("mutate", "reason"),
    (
        (_missing, "SAMPLES_EXACT4_LIST_OR_TUPLE_REQUIRED"),
        (_extra, "SAMPLES_EXACT4_LIST_OR_TUPLE_REQUIRED"),
        (_duplicate, "SAMPLE_EVENT_POPULATION_MUST_EQUAL_EXACT4"),
        (_excluded_4r7u, "EVENT_ID_NOT_EXACT4"),
        (_wrong_task, "TASK_ID_0_REQUIRED"),
    ),
)
def test_sample_population_and_task_contract_fail_closed(
    frozen_inputs: Mapping[str, bytes],
    mutate: Callable[[list[dict[str, object]]], object],
    reason: str,
) -> None:
    samples = mutate(_samples(frozen_inputs["structure"]))
    with pytest.raises(subject.FFQExact4PostSourceIndexBindingError, match=reason):
        subject.build_covapie_ffq_exact4_post_source_index_binding_v1(
            samples=samples,
            label_use_formal_bytes=frozen_inputs["label"],
            post_observation_formal_bytes=frozen_inputs["observation"],
        )


@pytest.mark.parametrize(
    ("input_name", "reason"),
    (
        ("label", "LABEL_USE_FORMAL_SHA256_MISMATCH"),
        ("observation", "POST_OBSERVATION_FORMAL_SHA256_MISMATCH"),
        ("structure", "FROZEN_STRUCTURE_PAYLOAD_MISMATCH"),
    ),
)
def test_frozen_formal_or_structure_tamper_stops_before_assembler(
    frozen_inputs: Mapping[str, bytes],
    monkeypatch: pytest.MonkeyPatch,
    input_name: str,
    reason: str,
) -> None:
    called = False

    def unexpected_assembler(**_: object) -> object:
        nonlocal called
        called = True
        raise AssertionError("assembler must not run after source validation failure")

    monkeypatch.setattr(
        subject.alignment_owner,
        "assemble_covapie_ffq_real_structure_microbatch_alignment_v1",
        unexpected_assembler,
    )
    values = dict(frozen_inputs)
    payload = values[input_name]
    values[input_name] = payload[:-1] + bytes([payload[-1] ^ 1])
    with pytest.raises(subject.FFQExact4PostSourceIndexBindingError, match=reason):
        subject.build_covapie_ffq_exact4_post_source_index_binding_v1(
            samples=_samples(values["structure"]),
            label_use_formal_bytes=values["label"],
            post_observation_formal_bytes=values["observation"],
        )
    assert called is False


def test_cross_formal_locator_tamper_is_semantically_rejected(
    frozen_inputs: Mapping[str, bytes],
) -> None:
    label = json.loads(frozen_inputs["label"])
    observation = json.loads(frozen_inputs["observation"])
    event = label["formal_event_decisions"][0]
    decision = event["scoped_label_definition_and_use_decision"]
    history = event["historical_post_observation_source_readback"]
    for container in (decision, history):
        container["source_event_locator"] = "/formal_event_decisions/1"
        container["source_distance_field_locator"] = (
            "/formal_event_decisions/1/approved_observations/SG_C1_observed_distance"
        )
    with pytest.raises(
        subject.FFQExact4PostSourceIndexBindingError,
        match="CROSS_FORMAL_EVENT_LOCATOR_BINDING_INVALID",
    ):
        subject._validate_formal_documents_v1(label, observation)


def test_swapped_formal_endpoints_are_rejected_by_identity(
    frozen_inputs: Mapping[str, bytes],
) -> None:
    label = json.loads(frozen_inputs["label"])
    observation = json.loads(frozen_inputs["observation"])
    endpoints = observation["formal_event_decisions"][0][
        "endpoint_identity_and_source_quality"
    ]
    endpoints["ligand_endpoint"], endpoints["protein_endpoint"] = (
        endpoints["protein_endpoint"],
        endpoints["ligand_endpoint"],
    )
    with pytest.raises(
        subject.FFQExact4PostSourceIndexBindingError,
        match="LIGAND_C1_CANONICAL_IDENTITY_MISMATCH",
    ):
        subject._validate_formal_documents_v1(label, observation)


def _with_batch_tensor(
    alignment: subject.alignment_owner.FFQRealStructureMicrobatchAlignmentV1,
    key: str,
    mutate: Callable[[torch.Tensor], None],
) -> subject.alignment_owner.FFQRealStructureMicrobatchAlignmentV1:
    batch = dict(alignment.model_input_batch)
    tensor = batch[key].clone()
    mutate(tensor)
    batch[key] = tensor
    return replace(alignment, model_input_batch=batch)


def _with_tensor_field(
    alignment: subject.alignment_owner.FFQRealStructureMicrobatchAlignmentV1,
    name: str,
    mutate: Callable[[torch.Tensor], None],
) -> subject.alignment_owner.FFQRealStructureMicrobatchAlignmentV1:
    tensor = getattr(alignment, name).clone()
    mutate(tensor)
    return replace(alignment, **{name: tensor})


@pytest.mark.parametrize(
    ("case", "reason"),
    (
        ("source_row", "SAMPLE_SEGMENT_OR_SOURCE_INSTANCE_INVALID"),
        ("cross_sample", "POSITIVE_PAIR_ENDPOINT_BINDING_INVALID"),
        ("fixed_generated", "FIXED_GENERATED_MASK_CONFLICT"),
        ("admitted", "TRAINING_ADMISSION_UPGRADE_FORBIDDEN"),
        ("geometry", "GEOMETRY_AVAILABILITY_UPGRADE_FORBIDDEN"),
    ),
)
def test_post_assembler_acceptance_rejects_scoped_index_role_and_status_mutations(
    validation_context: tuple[
        tuple[Mapping[str, Any], ...],
        dict[str, subject._ResolvedEventSourceV1],
        subject.alignment_owner.FFQRealStructureMicrobatchAlignmentV1,
    ],
    case: str,
    reason: str,
) -> None:
    samples, resolved, alignment = validation_context
    if case == "source_row":
        mutated = _with_batch_tensor(
            alignment,
            "lig_source_row_index",
            lambda tensor: tensor.__setitem__(0, tensor[0] + 1),
        )
    elif case == "cross_sample":
        mutated = _with_tensor_field(
            alignment,
            "positive_pair_ligand_flat_indices",
            lambda tensor: tensor.__setitem__(0, alignment.ligand_node_offsets[1]),
        )
    elif case == "fixed_generated":
        mutated = _with_tensor_field(
            alignment,
            "ligand_fixed_mask",
            lambda tensor: tensor.__setitem__((0, 0), True),
        )
    elif case == "admitted":
        mutated = _with_tensor_field(
            alignment,
            "sample_training_admitted",
            lambda tensor: tensor.__setitem__(0, True),
        )
    else:
        mutated = _with_tensor_field(
            alignment,
            "geometry_target_available",
            lambda tensor: tensor.__setitem__(0, True),
        )
    with pytest.raises(subject.FFQExact4PostSourceIndexBindingError, match=reason):
        subject._validate_alignment_and_build_bindings_v1(
            samples=samples, resolved_sources=resolved, alignment=mutated
        )


def test_public_api_explicitly_passes_fixed_policy_and_parses_unique_source_once(
    frozen_inputs: Mapping[str, bytes], monkeypatch: pytest.MonkeyPatch
) -> None:
    observed: dict[str, object] = {"parse_calls": 0}
    real_assembler = (
        subject.alignment_owner.assemble_covapie_ffq_real_structure_microbatch_alignment_v1
    )
    real_parser = subject.alignment_owner._parse_and_crosscheck_atom_site

    def assembler_spy(**kwargs: object) -> object:
        observed["assembler_kwargs"] = kwargs
        return real_assembler(**kwargs)

    def parser_spy(payload: bytes, *, expected_pdb_id: str) -> object:
        observed["parse_calls"] = int(observed["parse_calls"]) + 1
        return real_parser(payload, expected_pdb_id=expected_pdb_id)

    monkeypatch.setattr(
        subject.alignment_owner,
        "assemble_covapie_ffq_real_structure_microbatch_alignment_v1",
        assembler_spy,
    )
    monkeypatch.setattr(subject, "_parse_structure_payload_v1", parser_spy)
    result = _build(frozen_inputs)
    assert len(result.source_index_bindings) == 4
    kwargs = observed["assembler_kwargs"]
    assert type(kwargs) is dict
    assert kwargs["device"] == "cpu"
    assert kwargs["pocket_seed_policy"] == "fixed_scaffold_warhead_only_v1"
    assert observed["parse_calls"] == 1


def test_repeated_real_build_is_deterministic_and_does_not_mutate_inputs(
    frozen_inputs: Mapping[str, bytes],
    canonical_result: subject.FFQExact4PostSourceIndexBindingResultV1,
) -> None:
    samples = _samples(frozen_inputs["structure"])
    before_samples = copy.deepcopy(samples)
    label_before = bytes(frozen_inputs["label"])
    observation_before = bytes(frozen_inputs["observation"])
    repeated = subject.build_covapie_ffq_exact4_post_source_index_binding_v1(
        samples=samples,
        label_use_formal_bytes=frozen_inputs["label"],
        post_observation_formal_bytes=frozen_inputs["observation"],
    )
    assert samples == before_samples
    assert frozen_inputs["label"] == label_before
    assert frozen_inputs["observation"] == observation_before
    assert repeated.source_index_bindings == canonical_result.source_index_bindings
    _assert_alignments_identical(
        repeated.structural_alignment, canonical_result.structural_alignment
    )


def test_public_signature_has_no_alignment_or_sha_override_and_import_is_read_only(
    tmp_path: Path,
) -> None:
    signature = inspect.signature(
        subject.build_covapie_ffq_exact4_post_source_index_binding_v1
    )
    assert tuple(signature.parameters) == (
        "samples",
        "label_use_formal_bytes",
        "post_observation_formal_bytes",
    )
    assert all(
        parameter.kind is inspect.Parameter.KEYWORD_ONLY
        for parameter in signature.parameters.values()
    )
    source = inspect.getsource(subject)
    for forbidden in (
        "subprocess",
        "requests",
        "urlopen",
        "write_text(",
        "write_bytes(",
        "torch.save",
    ):
        assert forbidden not in source

    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join((str(ROOT / "src"), str(ROOT)))
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    command = [
        "/usr/bin/python",
        "-B",
        "-c",
        "import covalent_ext.covapie_ffq_exact4_post_source_index_binding_v1",
    ]
    before = tuple(tmp_path.iterdir())
    completed = subprocess.run(
        command,
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        shell=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == ""
    assert tuple(tmp_path.iterdir()) == before
