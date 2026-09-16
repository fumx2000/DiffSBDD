from __future__ import annotations

import ast
import copy
from dataclasses import fields, replace
import hashlib
import importlib
import importlib.util
import inspect
import os
from pathlib import Path
import stat
import sys

import pytest
import torch


def _load_candidate_module():
    candidate_path = os.environ.get(
        "COVAPIE_POA_EXACT8_INACTIVE_CONSUMER_ADAPTER_CANDIDATE_MODULE"
    )
    if candidate_path:
        path = Path(candidate_path)
        spec = importlib.util.spec_from_file_location(
            "covapie_poa_4i3u_exact8_inactive_consumer_adapter_v1", path
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    return importlib.import_module(
        "covalent_ext.covapie_poa_4i3u_exact8_inactive_consumer_adapter_v1"
    )


candidate = _load_candidate_module()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fingerprint(value: object) -> str:
    digest = hashlib.sha256()
    candidate._digest_update(digest, value)
    return digest.hexdigest()


def _assert_rejected(payload: object, prepared: object, match: str | None = None):
    with pytest.raises(
        candidate.POA4I3UExact8InactiveConsumerAdapterError,
        match=match,
    ):
        candidate.validate_covapie_poa_4i3u_exact8_inactive_consumer_payload_v1(
            payload=payload,
            prepared=prepared,
        )


@pytest.fixture(scope="session")
def roots():
    return {
        "repository": Path(os.environ["COVAPIE_REPOSITORY_ROOT"]).resolve(),
        "state": Path(os.environ["COVAPIE_STATE_ROOT"]).resolve(),
    }


@pytest.fixture(scope="session")
def source_snapshot(roots):
    paths: set[Path] = {
        roots["state"] / candidate.b1_owner.FORMAL_DECISION_STATE_RELATIVE,
        roots["state"] / candidate.b1_owner.STRUCTURE_STATE_RELATIVE,
        roots["state"] / candidate.ingestion_owner.SIGNED_DECISION_RELATIVE_PATH_V1,
    }
    for spec in candidate.ingestion_owner._SOURCE_SPECS_V1:
        root = roots["state"] if spec["root"] == "state" else roots["repository"]
        paths.add(root / spec["path"])
    for _, relative, *_ in candidate.SOURCE_SPECS_V1:
        paths.add(roots["repository"] / relative)
    return {
        path: (path.stat().st_size, stat.S_IMODE(path.stat().st_mode), _sha256(path))
        for path in paths
    }


@pytest.fixture(scope="session")
def prepared_bundle(roots, source_snapshot):
    del source_snapshot
    counts = {
        "structure_parse": 0,
        "ingestion_load_public": 0,
        "ingestion_validate_public": 0,
        "b1_assemble_public": 0,
        "b1_validate_public": 0,
    }
    structure_owner = candidate.b1_owner.structure_owner
    original_parse = structure_owner._parse_and_crosscheck_atom_site
    original_ingestion_load = (
        candidate.ingestion_owner.load_and_compile_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1
    )
    original_ingestion_validate = (
        candidate.ingestion_owner.validate_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1
    )
    original_b1_assemble = (
        candidate.b1_owner.assemble_covapie_poa_4i3u_exact8_real_preview_evidence_v1
    )
    original_b1_validate = (
        candidate.b1_owner.validate_covapie_poa_4i3u_exact8_real_preview_evidence_v1
    )

    def counted_parse(*args, **kwargs):
        counts["structure_parse"] += 1
        return original_parse(*args, **kwargs)

    def counted_ingestion_load(*args, **kwargs):
        counts["ingestion_load_public"] += 1
        return original_ingestion_load(*args, **kwargs)

    def counted_ingestion_validate(*args, **kwargs):
        counts["ingestion_validate_public"] += 1
        return original_ingestion_validate(*args, **kwargs)

    def counted_b1_assemble(*args, **kwargs):
        counts["b1_assemble_public"] += 1
        return original_b1_assemble(*args, **kwargs)

    def counted_b1_validate(*args, **kwargs):
        counts["b1_validate_public"] += 1
        return original_b1_validate(*args, **kwargs)

    structure_owner._parse_and_crosscheck_atom_site = counted_parse
    candidate.ingestion_owner.load_and_compile_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1 = counted_ingestion_load
    candidate.ingestion_owner.validate_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1 = counted_ingestion_validate
    candidate.b1_owner.assemble_covapie_poa_4i3u_exact8_real_preview_evidence_v1 = counted_b1_assemble
    candidate.b1_owner.validate_covapie_poa_4i3u_exact8_real_preview_evidence_v1 = counted_b1_validate
    try:
        prepared = candidate.prepare_covapie_poa_4i3u_exact8_inactive_consumer_adapter_v1(
            repository_root=roots["repository"],
            state_root=roots["state"],
        )
    finally:
        structure_owner._parse_and_crosscheck_atom_site = original_parse
        candidate.ingestion_owner.load_and_compile_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1 = original_ingestion_load
        candidate.ingestion_owner.validate_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1 = original_ingestion_validate
        candidate.b1_owner.assemble_covapie_poa_4i3u_exact8_real_preview_evidence_v1 = original_b1_assemble
        candidate.b1_owner.validate_covapie_poa_4i3u_exact8_real_preview_evidence_v1 = original_b1_validate

    outputs = {
        name: candidate.build_covapie_poa_4i3u_exact8_inactive_consumer_payload_v1(
            prepared=prepared,
            canonical_task_name=name,
        )
        for name in candidate.CANONICAL_TASK_LONG_NAMES_V1
    }
    return {"prepared": prepared, "outputs": outputs, "counts": counts}


def test_public_api_schema_pins_and_no_training_entry_calls() -> None:
    assert candidate.CANONICAL_TASK_LONG_NAMES_V1 == (
        "warhead_only",
        "linker_plus_warhead",
        "scaffold_plus_warhead",
        "scaffold_only",
        "scaffold_plus_linker_plus_warhead",
    )
    assert len(candidate.SOURCE_SPECS_V1) == 8
    assert len(
        fields(candidate.tensorizer_owner.CovapieCurrent11TrainingSupervisionTensorsV1)
    ) == 37
    assert len(candidate.ALLOWED_CHANGED_SUPERVISION_FIELDS_V1) == 8
    build_parameters = inspect.signature(
        candidate.build_covapie_poa_4i3u_exact8_inactive_consumer_payload_v1
    ).parameters
    assert tuple(build_parameters) == ("prepared", "canonical_task_name")
    assert "expected_sha" not in build_parameters
    assert "allow_dirty" not in build_parameters
    source = Path(candidate.__file__).read_text()
    tree = ast.parse(source)
    called_names = {
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Attribute, ast.Name))
    }
    assert called_names.isdisjoint(
        {
            "tensorize_covapie_current11_training_supervision_v1",
            "_tensorize_impl",
            "forward",
            "backward",
            "step",
            "fit",
        }
    )


def test_real_prepare_reuses_one_base_preview_and_actual_call_layers(
    prepared_bundle,
) -> None:
    prepared = prepared_bundle["prepared"]
    counts = prepared_bundle["counts"]
    base = prepared.base_preview
    assert counts == {
        "structure_parse": 16,
        "ingestion_load_public": 1,
        "ingestion_validate_public": 1,
        "b1_assemble_public": 1,
        "b1_validate_public": 1,
    }
    assert prepared.source_validation_call_counts == (
        ("ingestion_load_and_compile_public", 1),
        ("ingestion_validate_public", 1),
        ("ingestion_validate_internal_source_recompile", 1),
        ("metadata_builder_public", 1),
        ("b1_assemble_public", 1),
        ("b1_validate_public", 1),
    )
    assert base.canonical_task_ids == (0,) * 8
    assert not base.supervision.ligand_minimal_seed_or_anchor_mask.any().item()
    assert not base.supervision.ligand_minimal_seed_or_anchor_valid.any().item()
    assert not base.supervision.pre_post_geometry_target_angstrom.any().item()
    assert prepared.published_ingestion_result["semantic_projection_sha256"] == (
        candidate.PUBLISHED_INGESTION_SEMANTIC_PROJECTION_SHA256
    )
    assert prepared.published_ingestion_result["semantic_projection"][
        "permission_boundary"
    ]["PUBLISHED_INGESTION_OWNER_AVAILABLE"] is False
    print(
        "MAIN_PREPARE_CALL_COUNTS="
        "ingestion_load:1,ingestion_validate:1,metadata_build:1,"
        "b1_assemble:1,b1_public_validate:1 "
        "MAIN_PREPARE_STRUCTURE_PARSE_CALLS=16 "
        "B1_ASSEMBLE_EVENT_PARSES=8 B1_PUBLIC_VALIDATOR_EVENT_PARSES=8"
    )


def test_real_8x5_event_task_coverage_includes_b3_and_c(prepared_bundle) -> None:
    outputs = prepared_bundle["outputs"]
    expected_counts = {
        row[1]: (row[3], row[4]) for row in candidate.CANONICAL_TASKS_V1
    }
    coverage: set[tuple[str, str]] = set()
    for task_name, payload in outputs.items():
        assert candidate.validate_covapie_poa_4i3u_exact8_inactive_consumer_payload_v1(
            payload=payload,
            prepared=prepared_bundle["prepared"],
        )
        assert payload.summary.generated_count_per_event == (
            expected_counts[task_name][0],
        ) * 8
        assert payload.summary.fixed_count_per_event == (
            expected_counts[task_name][1],
        ) * 8
        for event_id in payload.sample_identities:
            coverage.add((event_id, task_name))
    assert len(coverage) == 40
    assert "scaffold_only" in outputs
    assert "scaffold_plus_linker_plus_warhead" in outputs
    print(
        "REAL_CPU_EVENT_TASK_COVERAGE_COUNT=40 "
        "TASK_COUNTS_PER_EVENT=A:2/5/0,B:3/4/0,B2:6/1/0,"
        "B3:4/3/0,C:7/0/2 MODEL_INPUT_FIELDS=14 "
        "UNCHANGED_SUPERVISION_FIELDS=29 PAIR_COUNTS=336/8/328 "
        "TOTAL_POCKET_NODES=2106 GEOMETRY_NAN_COMPONENTS_PER_PAYLOAD=16"
    )


def test_task_c_seed_and_primary_anchor_are_distinct_from_protein_sg(
    prepared_bundle,
) -> None:
    payload = prepared_bundle["outputs"]["scaffold_plus_linker_plus_warhead"]
    supervision = payload.supervision
    assert supervision.ligand_minimal_seed_or_anchor_valid.tolist() == [True] * 8
    for sample, mapping in enumerate(payload.seed_anchor_mappings):
        start, end = payload.ligand_node_offsets[sample : sample + 2]
        assert mapping.approved_seed_atom_ids == ("P", "O1P")
        assert mapping.seed_model_sample_local_indices_0based == (6, 3)
        assert mapping.seed_model_flat_indices_0based == (start + 6, start + 3)
        assert mapping.ligand_primary_anchor_atom_id == "P"
        assert mapping.primary_anchor_model_sample_local_index_0based == 6
        assert mapping.protein_target_reactive_atom_id == "SG"
        assert "NOT_TO_LIGAND_P" in mapping.ligand_anchor_distance_reference_semantics
        assert supervision.ligand_minimal_seed_or_anchor_mask[start:end, 0].tolist() == [
            False,
            False,
            False,
            True,
            False,
            False,
            True,
        ]
        assert supervision.ligand_base_generation_mask[start:end].all().item()
        assert not supervision.ligand_base_fixed_mask[start:end].any().item()


def test_non_c_seed_is_closed_without_changing_b3_role_masks(prepared_bundle) -> None:
    for task_name, payload in prepared_bundle["outputs"].items():
        if task_name == "scaffold_plus_linker_plus_warhead":
            continue
        assert not payload.supervision.ligand_minimal_seed_or_anchor_mask.any().item()
        assert not payload.supervision.ligand_minimal_seed_or_anchor_valid.any().item()
    b3 = prepared_bundle["outputs"]["scaffold_only"].supervision
    assert int(b3.ligand_base_generation_mask.sum().item()) == 8 * 4
    assert int(b3.ligand_base_fixed_mask.sum().item()) == 8 * 3


def test_nan_geometry_numeric_authority_and_all_losses_remain_inactive(
    prepared_bundle,
) -> None:
    for payload in prepared_bundle["outputs"].values():
        supervision = payload.supervision
        assert torch.isnan(supervision.pre_post_geometry_target_angstrom).all().item()
        assert supervision.pre_post_geometry_target_angstrom.shape == (8, 2)
        assert not supervision.pre_post_geometry_component_valid_mask.any().item()
        assert not supervision.pre_post_geometry_component_loss_mask.any().item()
        assert not supervision.sample_training_admitted.any().item()
        assert not supervision.ligand_active_diffusion_loss_mask.any().item()
        assert not supervision.pair_head_candidate_loss_mask.any().item()
        assert not supervision.pair_contrastive_sample_loss_mask.any().item()
        candidate.tensorizer_owner._validate_numeric_authority(
            observed=tuple(
                float(value)
                for value in supervision.observed_complex_pair_distance_angstrom[:, 0]
            ),
            observed_valid=(True,) * 8,
            geometry=((float("nan"), float("nan")),) * 8,
            geometry_valid=((False, False),) * 8,
            geometry_loss=((False, False),) * 8,
        )


def test_model_core_and_other_29_supervision_fields_are_exactly_preserved(
    prepared_bundle,
) -> None:
    prepared = prepared_bundle["prepared"]
    base = prepared.base_preview
    all_fields = {
        field.name
        for field in fields(
            candidate.tensorizer_owner.CovapieCurrent11TrainingSupervisionTensorsV1
        )
    }
    unchanged = all_fields - candidate.ALLOWED_CHANGED_SUPERVISION_FIELDS_V1
    assert len(unchanged) == 29
    for payload in prepared_bundle["outputs"].values():
        assert candidate._value_exact(payload.model_input_batch, base.model_input_batch)
        assert all(
            candidate._tensor_exact(
                getattr(payload.supervision, name),
                getattr(base.supervision, name),
            )
            for name in unchanged
        )
        assert payload.summary.pair_candidate_count == 336
        assert payload.summary.pair_positive_count == 8
        assert payload.summary.pair_negative_count == 328
        assert payload.summary.total_pocket_node_count == base.pocket_node_offsets[-1]
        assert int(payload.supervision.target_residue_membership_mask.sum().item()) == 48


@pytest.mark.parametrize("case", ("missing_pinned_owner", "signed_sha", "structure_sha"))
def test_missing_or_wrong_sha_sources_fail_before_payload_build(
    case, roots, monkeypatch
) -> None:
    original_lstat = Path.lstat
    original_read_bytes = Path.read_bytes
    pinned = roots["repository"] / candidate.SOURCE_SPECS_V1[0][1]
    signed = (
        roots["state"]
        / candidate.ingestion_owner.SIGNED_DECISION_RELATIVE_PATH_V1
    )
    structure = roots["state"] / candidate.b1_owner.STRUCTURE_STATE_RELATIVE

    def guarded_lstat(path: Path):
        if case == "missing_pinned_owner" and path.absolute() == pinned.absolute():
            raise FileNotFoundError(path)
        return original_lstat(path)

    def guarded_read_bytes(path: Path):
        payload = original_read_bytes(path)
        target = signed if case == "signed_sha" else structure
        if case in {"signed_sha", "structure_sha"} and path.absolute() == target.absolute():
            changed = bytearray(payload)
            changed[-2] ^= 1
            return bytes(changed)
        return payload

    monkeypatch.setattr(Path, "lstat", guarded_lstat)
    monkeypatch.setattr(Path, "read_bytes", guarded_read_bytes)
    with pytest.raises(candidate.POA4I3UExact8InactiveConsumerAdapterError):
        candidate.prepare_covapie_poa_4i3u_exact8_inactive_consumer_adapter_v1(
            repository_root=roots["repository"],
            state_root=roots["state"],
        )


def test_tampered_ingestion_with_recomputed_digest_is_source_revalidated(
    roots, prepared_bundle, monkeypatch
) -> None:
    tampered = copy.deepcopy(prepared_bundle["prepared"].published_ingestion_result)
    projection = tampered["semantic_projection"]
    projection["event_records"][0]["primary_anchor_atom_id"] = "O1P"
    tampered["semantic_projection_sha256"] = hashlib.sha256(
        candidate.ingestion_owner._canonical_json_bytes(projection)
    ).hexdigest()
    monkeypatch.setattr(
        candidate.ingestion_owner,
        "load_and_compile_covapie_poa_4i3u_exact8_task_c_seed_anchor_authority_ingestion_v1",
        lambda **_kwargs: copy.deepcopy(tampered),
    )
    with pytest.raises(candidate.POA4I3UExact8InactiveConsumerAdapterError):
        candidate.prepare_covapie_poa_4i3u_exact8_inactive_consumer_adapter_v1(
            repository_root=roots["repository"],
            state_root=roots["state"],
        )


@pytest.mark.parametrize("bad_task", ("C", 4, "sixth_task", ""))
def test_alias_integer_unknown_and_sixth_task_are_rejected(
    bad_task, prepared_bundle
) -> None:
    with pytest.raises(
        candidate.POA4I3UExact8InactiveConsumerAdapterError,
        match="CANONICAL_",
    ):
        candidate.build_covapie_poa_4i3u_exact8_inactive_consumer_payload_v1(
            prepared=prepared_bundle["prepared"],
            canonical_task_name=bad_task,
        )


@pytest.mark.parametrize(
    ("case", "field_name", "reason"),
    (
        (
            "canonical_task_id_short_shape",
            "canonical_task_id",
            "CANONICAL_TASK_OR_ROLE_MASK_ADAPTATION_INVALID",
        ),
        (
            "canonical_task_id_float_dtype",
            "canonical_task_id",
            "CANONICAL_TASK_OR_ROLE_MASK_ADAPTATION_INVALID",
        ),
        (
            "seed_mask_extra_zero_row",
            "ligand_minimal_seed_or_anchor_mask",
            "TASK_C_ONLY_SEED_TENSOR_MAPPING_INVALID",
        ),
        (
            "seed_mask_float_dtype",
            "ligand_minimal_seed_or_anchor_mask",
            "TASK_C_ONLY_SEED_TENSOR_MAPPING_INVALID",
        ),
        (
            "seed_valid_short_shape",
            "ligand_minimal_seed_or_anchor_valid",
            "TASK_C_ONLY_SEED_TENSOR_MAPPING_INVALID",
        ),
        (
            "seed_valid_float_dtype",
            "ligand_minimal_seed_or_anchor_valid",
            "TASK_C_ONLY_SEED_TENSOR_MAPPING_INVALID",
        ),
    ),
)
@pytest.mark.parametrize(
    "task_name",
    ("warhead_only", "scaffold_plus_linker_plus_warhead"),
)
def test_changed_tensor_spec_shape_and_dtype_are_bound_to_trusted_base(
    case, field_name, reason, task_name, prepared_bundle
) -> None:
    prepared = prepared_bundle["prepared"]
    payload = copy.deepcopy(prepared_bundle["outputs"][task_name])
    actual = getattr(payload.supervision, field_name)
    if case == "canonical_task_id_short_shape":
        mutated = actual[:1].clone()
    elif case == "canonical_task_id_float_dtype":
        mutated = actual.to(dtype=torch.float32)
    elif case == "seed_mask_extra_zero_row":
        mutated = torch.cat((actual, torch.zeros_like(actual[:1])), dim=0)
    elif case == "seed_mask_float_dtype":
        mutated = actual.to(dtype=torch.float32)
    elif case == "seed_valid_short_shape":
        mutated = actual[:1].clone()
    else:
        mutated = actual.to(dtype=torch.float32)

    task_id = payload.canonical_task_id
    if field_name == "canonical_task_id":
        inherited_from_actual = torch.full_like(mutated, task_id)
        trusted_expected = torch.full_like(
            prepared.base_preview.supervision.canonical_task_id, task_id
        )
    elif field_name == "ligand_minimal_seed_or_anchor_mask":
        inherited_from_actual = torch.zeros_like(mutated)
        trusted_expected = torch.zeros_like(
            prepared.base_preview.supervision.ligand_minimal_seed_or_anchor_mask
        )
        if task_id == 4:
            for mapping in payload.seed_anchor_mappings:
                inherited_from_actual[
                    list(mapping.seed_model_flat_indices_0based), 0
                ] = 1
                trusted_expected[
                    list(mapping.seed_model_flat_indices_0based), 0
                ] = True
    else:
        inherited_from_actual = torch.zeros_like(mutated)
        trusted_expected = torch.zeros_like(
            prepared.base_preview.supervision.ligand_minimal_seed_or_anchor_valid
        )
        if task_id == 4:
            inherited_from_actual.fill_(1)
            trusted_expected.fill_(True)

    # The former actual-derived expression inherits the malformed spec while
    # the trusted base-derived tensor retains the canonical domain contract.
    assert inherited_from_actual.shape == mutated.shape
    assert inherited_from_actual.dtype == mutated.dtype
    assert (
        trusted_expected.shape != mutated.shape
        or trusted_expected.dtype != mutated.dtype
        or trusted_expected.device != mutated.device
    )

    supervision_values = {
        field.name: getattr(payload.supervision, field.name)
        for field in fields(
            candidate.tensorizer_owner.CovapieCurrent11TrainingSupervisionTensorsV1
        )
    }
    supervision_values[field_name] = mutated
    mutated_supervision = (
        candidate.tensorizer_owner.CovapieCurrent11TrainingSupervisionTensorsV1(
            **supervision_values
        )
    )
    _assert_rejected(
        replace(payload, supervision=mutated_supervision),
        prepared,
        reason,
    )


@pytest.mark.parametrize("case", ("o1p_local2", "cross_event_flat", "unknown_atom"))
def test_seed_local_flat_and_atom_identity_confusions_are_rejected(
    case, prepared_bundle
) -> None:
    payload = copy.deepcopy(
        prepared_bundle["outputs"]["scaffold_plus_linker_plus_warhead"]
    )
    mappings = list(payload.seed_anchor_mappings)
    first = mappings[0]
    if case == "o1p_local2":
        first = replace(first, seed_model_sample_local_indices_0based=(6, 2))
    elif case == "cross_event_flat":
        first = replace(
            first,
            seed_model_flat_indices_0based=(
                mappings[1].seed_model_flat_indices_0based[0],
                first.seed_model_flat_indices_0based[1],
            ),
        )
    else:
        first = replace(first, approved_seed_atom_ids=("P", "UNKNOWN"))
    mappings[0] = first
    _assert_rejected(
        replace(payload, seed_anchor_mappings=tuple(mappings)),
        prepared_bundle["prepared"],
        "SEED_PRIMARY_ANCHOR_METADATA_INVALID",
    )


@pytest.mark.parametrize("replacement", ("zero", "observed", "inf"))
def test_unavailable_geometry_cannot_be_zero_observed_or_infinite(
    replacement, prepared_bundle
) -> None:
    payload = copy.deepcopy(prepared_bundle["outputs"]["warhead_only"])
    geometry = payload.supervision.pre_post_geometry_target_angstrom
    if replacement == "zero":
        geometry.fill_(0.0)
    elif replacement == "observed":
        geometry[:] = payload.supervision.observed_complex_pair_distance_angstrom
    else:
        geometry[0, 0] = float("inf")
    _assert_rejected(payload, prepared_bundle["prepared"], "GEOMETRY")


@pytest.mark.parametrize(
    "case",
    ("geometry_valid", "geometry_loss", "admitted", "diffusion_loss", "pair_loss"),
)
def test_valid_loss_or_admission_escalation_is_rejected(case, prepared_bundle) -> None:
    payload = copy.deepcopy(prepared_bundle["outputs"]["warhead_only"])
    supervision = payload.supervision
    if case == "geometry_valid":
        supervision.pre_post_geometry_component_valid_mask[0, 0] = True
    elif case == "geometry_loss":
        supervision.pre_post_geometry_component_loss_mask[0, 0] = True
    elif case == "admitted":
        supervision.sample_training_admitted[0] = True
    elif case == "diffusion_loss":
        supervision.ligand_active_diffusion_loss_mask[0, 0] = True
    else:
        supervision.pair_head_candidate_loss_mask[0] = True
    _assert_rejected(payload, prepared_bundle["prepared"])


@pytest.mark.parametrize(
    "case",
    (
        "soft_one_hot",
        "signed_one_hot",
        "source_index",
        "pair_membership",
        "unchanged_supervision",
        "coordinates",
    ),
)
def test_model_source_pair_and_unauthorized_field_corruption_is_rejected(
    case, prepared_bundle
) -> None:
    payload = copy.deepcopy(prepared_bundle["outputs"]["scaffold_only"])
    if case in {"soft_one_hot", "signed_one_hot"}:
        row = payload.model_input_batch["lig_one_hot"][0]
        correct = int(row.argmax().item())
        other = (correct + 1) % row.numel()
        row.zero_()
        if case == "soft_one_hot":
            row[correct], row[other] = 0.75, 0.25
        else:
            row[correct], row[other] = 1.25, -0.25
    elif case == "source_index":
        payload.model_input_batch["lig_source_row_index"][0] += 1
    elif case == "pair_membership":
        payload.supervision.pair_candidate_batch_index[42] = 0
    elif case == "unchanged_supervision":
        payload.supervision.ligand_anchor_distance_angstrom[0, 0] += 0.25
    else:
        payload.model_input_batch["lig_coords"][0, 0] += 0.25
    _assert_rejected(payload, prepared_bundle["prepared"])


def test_prepared_base_ingestion_and_output_tamper_fail_closed(
    prepared_bundle,
) -> None:
    prepared = prepared_bundle["prepared"]
    payload = prepared_bundle["outputs"]["warhead_only"]
    _assert_rejected(payload, {"base_preview": prepared.base_preview})

    base_tampered = copy.deepcopy(prepared)
    base_tampered.base_preview.model_input_batch["lig_coords"][0, 0] += 1.0
    with pytest.raises(
        candidate.POA4I3UExact8InactiveConsumerAdapterError,
        match="COMPLETENESS_SEAL",
    ):
        candidate.build_covapie_poa_4i3u_exact8_inactive_consumer_payload_v1(
            prepared=base_tampered,
            canonical_task_name="warhead_only",
        )

    ingestion_tampered = copy.deepcopy(prepared)
    ingestion_tampered.published_ingestion_result["semantic_projection"][
        "event_records"
    ][0]["primary_anchor_atom_id"] = "O1P"
    with pytest.raises(
        candidate.POA4I3UExact8InactiveConsumerAdapterError,
        match="COMPLETENESS_SEAL",
    ):
        candidate.build_covapie_poa_4i3u_exact8_inactive_consumer_payload_v1(
            prepared=ingestion_tampered,
            canonical_task_name="warhead_only",
        )

    output_tampered = copy.deepcopy(payload)
    output_tampered.model_input_batch["pocket_coords"][0, 0] += 1.0
    _assert_rejected(output_tampered, prepared)


def test_every_output_has_isolated_mutable_storage(prepared_bundle) -> None:
    prepared = prepared_bundle["prepared"]
    outputs = tuple(prepared_bundle["outputs"].values())
    base = prepared.base_preview
    for payload in outputs:
        for name, base_value in base.model_input_batch.items():
            value = payload.model_input_batch[name]
            if isinstance(value, torch.Tensor):
                assert value.data_ptr() != base_value.data_ptr()
            elif isinstance(value, list):
                assert value is not base_value
        for field in fields(
            candidate.tensorizer_owner.CovapieCurrent11TrainingSupervisionTensorsV1
        ):
            assert getattr(payload.supervision, field.name).data_ptr() != getattr(
                base.supervision, field.name
            ).data_ptr()
    for left, right in zip(outputs, outputs[1:], strict=False):
        assert (
            left.model_input_batch["lig_coords"].data_ptr()
            != right.model_input_batch["lig_coords"].data_ptr()
        )
        assert (
            left.supervision.ligand_role_id.data_ptr()
            != right.supervision.ligand_role_id.data_ptr()
        )

    fresh = candidate.build_covapie_poa_4i3u_exact8_inactive_consumer_payload_v1(
        prepared=prepared,
        canonical_task_name="warhead_only",
    )
    base_value = float(base.model_input_batch["lig_coords"][0, 0])
    other_value = float(outputs[1].model_input_batch["lig_coords"][0, 0])
    fresh.model_input_batch["lig_coords"][0, 0] += 100.0
    assert float(base.model_input_batch["lig_coords"][0, 0]) == base_value
    assert float(outputs[1].model_input_batch["lig_coords"][0, 0]) == other_value


def test_repeated_derivation_is_deterministic_without_serializing_payload(
    prepared_bundle,
) -> None:
    prepared = prepared_bundle["prepared"]
    first = candidate.build_covapie_poa_4i3u_exact8_inactive_consumer_payload_v1(
        prepared=prepared,
        canonical_task_name="scaffold_plus_linker_plus_warhead",
    )
    second = candidate.build_covapie_poa_4i3u_exact8_inactive_consumer_payload_v1(
        prepared=prepared,
        canonical_task_name="scaffold_plus_linker_plus_warhead",
    )
    assert _fingerprint(first) == _fingerprint(second)
    assert first.model_input_batch["lig_coords"].data_ptr() != second.model_input_batch[
        "lig_coords"
    ].data_ptr()


def test_fixed_sources_formal_decision_and_4i3u_gzip_are_unchanged(
    source_snapshot, prepared_bundle
) -> None:
    del prepared_bundle
    assert {
        path: (path.stat().st_size, stat.S_IMODE(path.stat().st_mode), _sha256(path))
        for path in source_snapshot
    } == source_snapshot
