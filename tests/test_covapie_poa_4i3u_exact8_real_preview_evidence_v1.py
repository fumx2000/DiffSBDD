from __future__ import annotations

import copy
from dataclasses import replace
import hashlib
import importlib
import importlib.util
import os
from pathlib import Path
import sys

import pytest
import torch

from covalent_ext import covapie_poa_sample_level_effective_supervision_v1 as metadata_owner


def _load_candidate_module():
    candidate_path = os.environ.get("COVAPIE_POA_EXACT8_CANDIDATE_MODULE")
    if candidate_path:
        path = Path(candidate_path)
        spec = importlib.util.spec_from_file_location(
            "covapie_poa_4i3u_exact8_real_preview_evidence_v1", path
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    return importlib.import_module(
        "covalent_ext.covapie_poa_4i3u_exact8_real_preview_evidence_v1"
    )


candidate = _load_candidate_module()


@pytest.fixture(scope="session")
def real_inputs():
    repository_root = Path(os.environ["COVAPIE_REPOSITORY_ROOT"])
    state_root = Path(os.environ["COVAPIE_STATE_ROOT"])
    formal_path = state_root / candidate.FORMAL_DECISION_STATE_RELATIVE
    structure_path = state_root / candidate.STRUCTURE_STATE_RELATIVE
    formal_payload = formal_path.read_bytes()
    structure_payload = structure_path.read_bytes()
    formal_digest = hashlib.sha256(formal_payload).hexdigest()
    structure_digest = hashlib.sha256(structure_payload).hexdigest()
    effective = metadata_owner.build_covapie_poa_sample_level_effective_supervision_v1(
        formal_payload
    )
    assert metadata_owner.validate_covapie_poa_sample_level_effective_supervision_v1(
        effective
    )
    inputs = {"4I3U": structure_payload}
    return {
        "repository_root": repository_root,
        "state_root": state_root,
        "formal_path": formal_path,
        "structure_path": structure_path,
        "formal_payload": formal_payload,
        "structure_payload": structure_payload,
        "formal_digest": formal_digest,
        "structure_digest": structure_digest,
        "effective": effective,
        "inputs": inputs,
    }


@pytest.fixture(scope="session")
def real_double_build(real_inputs):
    kwargs = {
        "repository_root": real_inputs["repository_root"],
        "formal_decision_payload": real_inputs["formal_payload"],
        "effective_supervision": real_inputs["effective"],
        "structure_payloads_by_pdb": real_inputs["inputs"],
    }
    first = candidate.assemble_covapie_poa_4i3u_exact8_real_preview_evidence_v1(
        **kwargs
    )
    second = candidate.assemble_covapie_poa_4i3u_exact8_real_preview_evidence_v1(
        **kwargs
    )
    first_payload = (
        candidate.build_covapie_poa_4i3u_exact8_real_preview_evidence_payload_v1(
            first, **kwargs
        )
    )
    second_payload = (
        candidate.build_covapie_poa_4i3u_exact8_real_preview_evidence_payload_v1(
            second, **kwargs
        )
    )
    first_bytes = candidate._canonical_json_bytes(first_payload)
    second_bytes = candidate._canonical_json_bytes(second_payload)
    return {
        "first": first,
        "second": second,
        "first_payload": first_payload,
        "second_payload": second_payload,
        "first_bytes": first_bytes,
        "second_bytes": second_bytes,
        "kwargs": kwargs,
    }


def _assert_rejected(preview, real_double_build, match: str | None = None):
    with pytest.raises(
        candidate.POA4I3UExact8RealPreviewEvidenceError,
        match=match,
    ):
        candidate.validate_covapie_poa_4i3u_exact8_real_preview_evidence_v1(
            preview, **real_double_build["kwargs"]
        )


def test_real_formal_source_metadata_exact8_and_public_validator_normal_path(
    real_inputs, real_double_build
):
    assert candidate.validate_covapie_poa_4i3u_exact8_real_preview_evidence_v1(
        real_double_build["first"], **real_double_build["kwargs"]
    )
    effective = real_inputs["effective"]
    assert len(effective.records) == 16
    assert tuple(row.canonical_event_id for row in effective.records[:8]) == (
        candidate.EXPECTED_EVENT_IDS_V1
    )
    assert all(row.training_use_disposition == "INCLUDE" for row in effective.records[:8])
    assert all(row.human_training_excluded is False for row in effective.records[:8])
    assert all(row.training_admitted is False for row in effective.records)
    assert all(row.pair_candidate_domain_materialized is False for row in effective.records)


def test_wrong_structure_sha_rejected_before_structural_core(real_inputs, monkeypatch):
    core_called = False

    def forbidden_core(**_kwargs):
        nonlocal core_called
        core_called = True
        raise AssertionError("structural core must not run")

    monkeypatch.setattr(candidate.preview_owner, "_assemble_core_v1", forbidden_core)
    corrupted = bytearray(real_inputs["structure_payload"])
    corrupted[-1] ^= 1
    with pytest.raises(
        candidate.POA4I3UExact8RealPreviewEvidenceError,
        match="STRUCTURE_PAYLOAD_SOURCE_BINDING_INVALID",
    ):
        candidate.assemble_covapie_poa_4i3u_exact8_real_preview_evidence_v1(
            repository_root=real_inputs["repository_root"],
            formal_decision_payload=real_inputs["formal_payload"],
            effective_supervision=real_inputs["effective"],
            structure_payloads_by_pdb={"4I3U": bytes(corrupted)},
        )
    assert core_called is False


def test_wrong_formal_source_and_non_4i3u_structure_mapping_rejected(real_inputs):
    corrupted = bytearray(real_inputs["formal_payload"])
    corrupted[-2] ^= 1
    with pytest.raises(
        candidate.POA4I3UExact8RealPreviewEvidenceError,
        match="FORMAL_DECISION_SOURCE_BINDING_INVALID",
    ):
        candidate.assemble_covapie_poa_4i3u_exact8_real_preview_evidence_v1(
            repository_root=real_inputs["repository_root"],
            formal_decision_payload=bytes(corrupted),
            effective_supervision=real_inputs["effective"],
            structure_payloads_by_pdb=real_inputs["inputs"],
        )
    with pytest.raises(
        candidate.POA4I3UExact8RealPreviewEvidenceError,
        match="STRUCTURE_PAYLOAD_MAPPING_MUST_BE_ONLY_4I3U",
    ):
        candidate.assemble_covapie_poa_4i3u_exact8_real_preview_evidence_v1(
            repository_root=real_inputs["repository_root"],
            formal_decision_payload=real_inputs["formal_payload"],
            effective_supervision=real_inputs["effective"],
            structure_payloads_by_pdb={
                "4I3U": real_inputs["structure_payload"],
                "4I3V": b"not-read-or-parsed",
            },
        )


@pytest.mark.parametrize("mutation", ("duplicate", "order", "exclude", "other_pdb"))
def test_wrong_event_set_order_exclude_or_other_pdb_rejected(
    mutation, real_double_build
):
    preview = real_double_build["first"]
    identities = list(preview.sample_identities)
    if mutation == "duplicate":
        identities[1] = identities[0]
    elif mutation == "order":
        identities[0], identities[1] = identities[1], identities[0]
    elif mutation == "exclude":
        identities[0] = candidate.EXPECTED_EXCLUDED_EVENT_IDS_V1[0]
    else:
        identities[0] = identities[0].replace("4I3U", "4I3W")
    _assert_rejected(
        replace(preview, sample_identities=tuple(identities)),
        real_double_build,
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "source_index",
        "parser_local_index",
        "reactive_flat_index",
        "cross_sample_pair",
        "positive_endpoint",
        "element_channel",
        "target_membership",
    ),
)
def test_index_pair_feature_and_target_membership_corruption_rejected(
    mutation, real_double_build
):
    preview = copy.deepcopy(real_double_build["first"])
    model = preview.model_input_batch
    supervision = preview.supervision
    if mutation == "source_index":
        model["lig_source_row_index"][6] += 1000
    elif mutation == "parser_local_index":
        model["lig_parser_local_index"][0] = 1
    elif mutation == "reactive_flat_index":
        preview.ligand_reactive_atom_flat_index[0] += 1
    elif mutation == "cross_sample_pair":
        supervision.pair_candidate_batch_index[42] = 0
    elif mutation == "positive_endpoint":
        supervision.pair_positive_candidate_index[0] += 1
    elif mutation == "element_channel":
        model["lig_one_hot"][0].zero_()
        model["lig_one_hot"][0, 1] = 1.0
    elif mutation == "target_membership":
        start, end = preview.pocket_node_offsets[:2]
        mask = supervision.target_residue_membership_mask[start:end, 0]
        member = int(torch.nonzero(mask, as_tuple=False)[0].item())
        nonmember = int(torch.nonzero(~mask, as_tuple=False)[0].item())
        mask[member] = False
        mask[nonmember] = True
    _assert_rejected(preview, real_double_build)


@pytest.mark.parametrize("domain", ("ligand", "pocket"))
@pytest.mark.parametrize("encoding", ("soft", "signed"))
def test_source_aligned_full_one_hot_rejects_non_binary_encoding(
    domain, encoding, real_double_build
):
    preview = copy.deepcopy(real_double_build["first"])
    field = "lig_one_hot" if domain == "ligand" else "pocket_one_hot"
    tensor = preview.model_input_batch[field]
    original_shape = tensor.shape
    original_dtype = tensor.dtype
    original_device = tensor.device
    correct_channel = int(tensor[0].argmax().item())
    other_channel = (correct_channel + 1) % tensor.shape[1]
    tensor[0].zero_()
    if encoding == "soft":
        tensor[0, correct_channel] = 0.75
        tensor[0, other_channel] = 0.25
    else:
        tensor[0, correct_channel] = 1.25
        tensor[0, other_channel] = -0.25

    expected = candidate.structure_owner._one_hot(
        (correct_channel,), device=torch.device("cpu")
    )[0]
    assert tensor.shape == original_shape
    assert tensor.dtype == original_dtype
    assert tensor.device == original_device
    assert tensor[0].sum().item() == 1.0
    assert tensor[0].argmax().item() == correct_channel
    assert not torch.equal(tensor[0], expected)

    reason = (
        "INDEPENDENT_LIGAND_SOURCE_ALIGNED_EXACT10_ONE_HOT_INVALID"
        if domain == "ligand"
        else "INDEPENDENT_POCKET_SOURCE_ALIGNED_EXACT10_ONE_HOT_INVALID"
    )
    with pytest.raises(
        candidate.POA4I3UExact8RealPreviewEvidenceError,
        match=reason,
    ):
        candidate.validate_covapie_poa_4i3u_exact8_real_preview_evidence_v1(
            preview, **real_double_build["kwargs"]
        )
    with pytest.raises(
        candidate.POA4I3UExact8RealPreviewEvidenceError,
        match=reason,
    ):
        candidate.build_covapie_poa_4i3u_exact8_real_preview_evidence_payload_v1(
            preview, **real_double_build["kwargs"]
        )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("training_admission_created", True),
        ("training_dataset_changed", True),
        ("model_forward_executed", True),
        ("loss_executed", True),
        ("optimizer_created", True),
        ("ready_for_training", True),
    ),
)
def test_admission_model_loss_and_training_flags_cannot_be_promoted(
    field, value, real_double_build
):
    _assert_rejected(
        replace(real_double_build["first"], **{field: value}),
        real_double_build,
    )


def test_real_double_build_is_byte_deterministic_and_exact5_includes_b3(
    real_double_build,
):
    assert real_double_build["first_bytes"] == real_double_build["second_bytes"]
    payload = real_double_build["first_payload"]
    assert len(payload["events"]) == 8
    assert all(len(row["pair_domain"]["candidates"]) == 42 for row in payload["events"])
    assert all(
        [mask["semantic_long_name"] for mask in row["canonical_exact5_structural_masks"]]
        == [task[1] for task in candidate.CANONICAL_TASKS_V1]
        for row in payload["events"]
    )
    assert all(
        row["canonical_exact5_structural_masks"][3]["short_alias"] == "B3"
        for row in payload["events"]
    )


def test_geometry_zero_placeholders_preserved_without_nan_adapter(real_double_build):
    preview = real_double_build["first"]
    geometry = preview.supervision.pre_post_geometry_target_angstrom
    assert torch.isfinite(geometry).all().item()
    assert not geometry.any().item()
    assert not preview.supervision.pre_post_geometry_component_valid_mask.any().item()
    assert not preview.supervision.pre_post_geometry_component_loss_mask.any().item()
    markers = real_double_build["first_payload"]["inactive_and_safety_markers"]
    assert markers["NAN_GEOMETRY_CONSUMER_CONVERSION_APPLIED"] is False
    assert markers["TASK_C_SEED_AUTHORITY_CREATED"] is False
    assert markers["READY_FOR_TRAINING"] is False


def test_inputs_metadata_and_real_source_files_are_not_modified(
    real_inputs, real_double_build
):
    del real_double_build
    assert hashlib.sha256(real_inputs["formal_payload"]).hexdigest() == real_inputs[
        "formal_digest"
    ]
    assert hashlib.sha256(real_inputs["structure_payload"]).hexdigest() == real_inputs[
        "structure_digest"
    ]
    assert hashlib.sha256(real_inputs["formal_path"].read_bytes()).hexdigest() == (
        real_inputs["formal_digest"]
    )
    assert hashlib.sha256(real_inputs["structure_path"].read_bytes()).hexdigest() == (
        real_inputs["structure_digest"]
    )
    assert all(
        record.pair_candidate_domain_materialized is False
        and record.training_admitted is False
        for record in real_inputs["effective"].records
    )


def test_public_api_does_not_expose_expected_sha_override():
    import inspect

    parameters = inspect.signature(
        candidate.assemble_covapie_poa_4i3u_exact8_real_preview_evidence_v1
    ).parameters
    assert "expected_structure_bindings" not in parameters
    assert "device" not in parameters
    assert "canonical_task_ids_by_event" not in parameters
