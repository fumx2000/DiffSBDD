from __future__ import annotations

import copy
import hashlib
import json
import os
import stat
import subprocess
from dataclasses import fields
from pathlib import Path

import pytest
import torch

from covalent_ext import (
    covapie_expanded_cys_sg_mixed_profile_tensorizer_v1 as subject,
)
from covalent_ext import (
    covapie_k36_w1_recovered7_authority_ingestion_and_effective_supervision_successor_v1
    as successor,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
    tensorize_covapie_current11_training_supervision_v1,
)


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT.parent / "covapie-state"
CARRIER = STATE / subject.K36_EFFECTIVE_CARRIER_RELATIVE_PATH_V1
EVIDENCE = ROOT / subject.K36_STRUCTURAL_EVIDENCE_RELATIVE_PATH_V1
ERROR = subject.MIXED_PROFILE_TENSORIZER_ERROR_V1
K36_LIGAND_NODE_ORDER = (
    "C7", "O8", "C9", "O10", "C1", "C2", "C3", "C4", "C5", "C6",
    "N11", "C12", "C17", "O18", "C13", "C14", "C15", "C16", "N19",
    "C20", "C21", "O22", "C24", "C25", "C26", "C27", "N28", "C29",
    "O30",
)
K36_TARGET_SG_LOCAL_INDEX = {
    "4DCD/K36": 150,
    "4F49/K36": 122,
    "5WKJ/K36": 112,
    "6L70/K36": 109,
    "6WTT/K36": 113,
}
CORE_FIELDS = frozenset((
    "names",
    "receptors",
    "lig_coords",
    "pocket_coords",
    "lig_one_hot",
    "pocket_one_hot",
    "lig_source_row_index",
    "pocket_source_row_index",
    "lig_parser_local_index",
    "pocket_parser_local_index",
    "num_lig_atoms",
    "num_pocket_nodes",
    "lig_mask",
    "pocket_mask",
))


def _k36(identity: str, task_id: int):
    return subject.tensorize_covapie_expanded_cys_sg_sample_v1(
        sample_identity=identity,
        task_id=task_id,
        repository_root=ROOT,
        state_root=STATE,
    )


def _assert_tensor_exact(left: torch.Tensor, right: torch.Tensor) -> None:
    assert left.dtype == right.dtype
    assert left.shape == right.shape
    assert left.device == right.device
    if left.dtype.is_floating_point or left.dtype.is_complex:
        torch.testing.assert_close(
            left, right, rtol=0, atol=0, equal_nan=True
        )
    else:
        assert torch.equal(left, right)


def _assert_supervision_exact(
    left: CovapieCurrent11TrainingSupervisionTensorsV1,
    right: CovapieCurrent11TrainingSupervisionTensorsV1,
) -> None:
    assert type(left) is type(right) is CovapieCurrent11TrainingSupervisionTensorsV1
    for field in fields(CovapieCurrent11TrainingSupervisionTensorsV1):
        _assert_tensor_exact(getattr(left, field.name), getattr(right, field.name))


def _assert_current11_singleton_parity(
    *,
    reference: CovapieCurrent11TrainingSupervisionTensorsV1,
    observed: CovapieCurrent11TrainingSupervisionTensorsV1,
    authority: dict[str, object],
    sample_ordinal: int,
) -> None:
    ligand_offsets = authority["ligand_node_offsets"]
    pocket_offsets = authority["pocket_node_offsets"]
    assert type(ligand_offsets) is list and type(pocket_offsets) is list
    ligand_start, ligand_end = ligand_offsets[sample_ordinal:sample_ordinal + 2]
    pocket_start, pocket_end = pocket_offsets[sample_ordinal:sample_ordinal + 2]
    candidate_start = int(reference.pair_candidate_offsets[sample_ordinal].item())
    candidate_end = int(reference.pair_candidate_offsets[sample_ordinal + 1].item())
    sample_fields = (
        "sample_training_admitted",
        "canonical_task_id",
        "canonical_task_valid",
        "ligand_minimal_seed_or_anchor_valid",
        "target_residue_reactive_atom_local_index",
        "target_residue_condition_valid",
        "pair_positive_candidate_valid",
        "pair_negative_count",
        "pair_contrastive_sample_loss_mask",
        "observed_complex_pair_distance_angstrom",
        "observed_complex_pair_distance_valid",
        "pre_post_geometry_target_angstrom",
        "pre_post_geometry_component_valid_mask",
        "pre_post_geometry_component_loss_mask",
    )
    for name in sample_fields:
        expected = getattr(reference, name)[sample_ordinal:sample_ordinal + 1]
        _assert_tensor_exact(expected, getattr(observed, name))
    ligand_fields = (
        "ligand_role_id",
        "ligand_role_valid",
        "ligand_base_generation_mask",
        "ligand_base_fixed_mask",
        "ligand_base_target_mask",
        "ligand_base_context_mask",
        "ligand_active_diffusion_loss_mask",
        "ligand_minimal_seed_or_anchor_mask",
        "ligand_anchor_distance_angstrom",
        "ligand_anchor_distance_valid",
    )
    for name in ligand_fields:
        expected = getattr(reference, name)[ligand_start:ligand_end]
        _assert_tensor_exact(expected, getattr(observed, name))
    for name in (
        "target_residue_membership_mask",
        "target_residue_reactive_atom_mask",
    ):
        expected = getattr(reference, name)[pocket_start:pocket_end]
        _assert_tensor_exact(expected, getattr(observed, name))
    _assert_tensor_exact(
        reference.target_residue_reactive_atom_flat_index[
            sample_ordinal:sample_ordinal + 1
        ] - pocket_start,
        observed.target_residue_reactive_atom_flat_index,
    )
    assert observed.pair_candidate_offsets.tolist() == [
        0, candidate_end - candidate_start
    ]
    assert observed.pair_candidate_batch_index.tolist() == [
        0
    ] * (candidate_end - candidate_start)
    direct_candidate_fields = (
        "pair_candidate_ligand_local_index",
        "pair_candidate_residue_local_index",
        "pair_candidate_is_positive",
        "pair_candidate_is_negative",
        "pair_head_candidate_loss_mask",
    )
    for name in direct_candidate_fields:
        expected = getattr(reference, name)[candidate_start:candidate_end]
        _assert_tensor_exact(expected, getattr(observed, name))
    _assert_tensor_exact(
        reference.pair_candidate_ligand_flat_index[
            candidate_start:candidate_end
        ] - ligand_start,
        observed.pair_candidate_ligand_flat_index,
    )
    _assert_tensor_exact(
        reference.pair_candidate_pocket_flat_index[
            candidate_start:candidate_end
        ] - pocket_start,
        observed.pair_candidate_pocket_flat_index,
    )
    _assert_tensor_exact(
        reference.pair_positive_candidate_index[
            sample_ordinal:sample_ordinal + 1
        ] - candidate_start,
        observed.pair_positive_candidate_index,
    )


def _parsed_sources():
    records = subject._validated_k36_carrier_semantics_v1(CARRIER.read_bytes())
    samples, topology = subject._validated_k36_structural_semantics_v1(
        EVIDENCE.read_bytes()
    )
    return records, samples, topology


def test_global_exact3_exact5_and_per_sample_applicability() -> None:
    assert subject.GLOBAL_ROLE_VOCABULARY_V1 == (
        (0, "scaffold"), (1, "linker"), (2, "warhead"),
    )
    assert subject.GLOBAL_TASK_VOCABULARY_V1 == (
        (0, "warhead_only", "A", (2,)),
        (1, "linker_plus_warhead", "B", (1, 2)),
        (2, "scaffold_plus_warhead", "B2", (0, 2)),
        (3, "scaffold_only", "B3", (0,)),
        (4, "scaffold_plus_linker_plus_warhead", "C", (0, 1, 2)),
    )
    assert len(subject.GLOBAL_TASK_VOCABULARY_V1) == 5
    for identity in subject.K36_MEMBER_IDENTITIES_V1:
        assert subject.valid_task_ids_for_covapie_expanded_cys_sg_sample_v1(
            identity
        ) == (0, 3, 4)
    assert subject.CURRENT11_MEMBER_IDENTITIES_V1 == tuple(
        f"CYS_SG_SAMPLE_INDEX_{index:06d}" for index in range(1, 12)
    )
    assert len(
        set(subject.CURRENT11_MEMBER_IDENTITIES_V1)
        | set(subject.K36_MEMBER_IDENTITIES_V1)
    ) == 16
    assert set(subject.CURRENT11_MEMBER_IDENTITIES_V1).isdisjoint(
        subject.K36_MEMBER_IDENTITIES_V1
    )
    for index in range(1, 12):
        assert subject.valid_task_ids_for_covapie_expanded_cys_sg_sample_v1(
            f"CYS_SG_SAMPLE_INDEX_{index:06d}"
        ) == (0, 1, 2, 3, 4)


@pytest.mark.parametrize(
    "identity",
    (
        "CYS_SG_SAMPLE_INDEX_000000",
        "CYS_SG_SAMPLE_INDEX_000012",
        "CYS_SG_SAMPLE_INDEX_999999",
        "2R9F/K2Z",
        "2DJF/1ZB",
        "arbitrary malformed identity",
    ),
)
def test_out_of_exact16_population_fails_closed_in_both_public_apis(
    identity: str,
) -> None:
    reason = "SAMPLE_IDENTITY_NOT_IN_INTEGRATION_POPULATION"
    with pytest.raises(ValueError, match=f"^{ERROR}:{reason}$"):
        subject.valid_task_ids_for_covapie_expanded_cys_sg_sample_v1(identity)
    with pytest.raises(ValueError, match=f"^{ERROR}:{reason}$"):
        subject.tensorize_covapie_expanded_cys_sg_sample_v1(
            sample_identity=identity,
            task_id=0,
        )


@pytest.mark.parametrize("exception_type", (KeyboardInterrupt, SystemExit))
def test_process_control_exceptions_propagate_through_valid_task_api(
    monkeypatch: pytest.MonkeyPatch,
    exception_type: type[BaseException],
) -> None:
    def interrupt(unused: object) -> str:
        del unused
        raise exception_type()

    monkeypatch.setattr(subject, "_profile_for_identity", interrupt)
    with pytest.raises(exception_type):
        subject.valid_task_ids_for_covapie_expanded_cys_sg_sample_v1(
            "4DCD/K36"
        )


@pytest.mark.parametrize("exception_type", (KeyboardInterrupt, SystemExit))
def test_process_control_exceptions_propagate_through_tensorize_api(
    monkeypatch: pytest.MonkeyPatch,
    exception_type: type[BaseException],
) -> None:
    def interrupt(task_id: object, *, profile: str) -> int:
        del task_id, profile
        raise exception_type()

    monkeypatch.setattr(subject, "_require_task", interrupt)
    with pytest.raises(exception_type):
        subject.tensorize_covapie_expanded_cys_sg_sample_v1(
            sample_identity="4DCD/K36",
            task_id=0,
        )


def test_production_has_no_baseexception_catch_and_ordinary_invalid_is_valueerror(
) -> None:
    source = Path(subject.__file__).read_text(encoding="utf-8")
    assert "except BaseException" not in source
    with pytest.raises(
        ValueError,
        match=(
            f"^{ERROR}:SAMPLE_IDENTITY_NOT_IN_INTEGRATION_POPULATION$"
        ),
    ):
        subject.valid_task_ids_for_covapie_expanded_cys_sg_sample_v1(
            "CYS_SG_SAMPLE_INDEX_000012"
        )


def test_k36_exact15_real_structural_tensorization_matrix() -> None:
    valid_instance_count = 0
    for identity in subject.K36_MEMBER_IDENTITIES_V1:
        for task_id in subject.K36_VALID_TASK_IDS_V1:
            result = _k36(identity, task_id)
            valid_instance_count += 1
            assert type(result.supervision) is (
                CovapieCurrent11TrainingSupervisionTensorsV1
            )
            assert result.role_profile == (
                subject.DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1
            )
            assert result.valid_task_ids == (0, 3, 4)
            assert CORE_FIELDS.issubset(result.model_input_batch)
            batch = result.model_input_batch
            supervision = result.supervision
            assert batch["names"] == [identity]
            assert batch["receptors"] == [identity.split("/", 1)[0]]
            assert batch["lig_coords"].shape == (29, 3)
            assert batch["lig_one_hot"].shape == (29, 10)
            assert batch["pocket_one_hot"].shape[1] == 10
            assert batch["num_lig_atoms"].tolist() == [29]
            assert batch["num_pocket_nodes"].tolist() == [
                len(batch["pocket_coords"])
            ]
            for name in CORE_FIELDS - {"names", "receptors"}:
                value = batch[name]
                assert isinstance(value, torch.Tensor)
                if value.dtype.is_floating_point:
                    assert bool(torch.isfinite(value).all().item())
            assert bool((batch["lig_one_hot"].sum(dim=1) == 1).all().item())
            assert bool((batch["pocket_one_hot"].sum(dim=1) == 1).all().item())
            assert supervision.canonical_task_id.tolist() == [task_id]
            assert supervision.canonical_task_valid.tolist() == [True]
            assert supervision.sample_training_admitted.tolist() == [True]
            assert supervision.ligand_role_id.bincount(minlength=3).tolist() == [
                27, 0, 2,
            ]
            assert supervision.ligand_role_valid.tolist() == [True] * 29
            generated = torch.nonzero(
                supervision.ligand_base_generation_mask[:, 0],
                as_tuple=False,
            ).flatten().tolist()
            fixed = torch.nonzero(
                supervision.ligand_base_fixed_mask[:, 0],
                as_tuple=False,
            ).flatten().tolist()
            if task_id == 0:
                assert generated == [20, 21]
                assert fixed == list(range(20)) + list(range(22, 29))
            elif task_id == 3:
                assert generated == list(range(20)) + list(range(22, 29))
                assert fixed == [20, 21]
            else:
                assert generated == list(range(29))
                assert fixed == []
            assert torch.equal(
                supervision.ligand_base_generation_mask,
                supervision.ligand_base_target_mask,
            )
            assert torch.equal(
                supervision.ligand_base_fixed_mask,
                supervision.ligand_base_context_mask,
            )
            expected_seed = [18, 19] if task_id == 4 else []
            assert torch.nonzero(
                supervision.ligand_minimal_seed_or_anchor_mask[:, 0],
                as_tuple=False,
            ).flatten().tolist() == expected_seed
            assert supervision.ligand_minimal_seed_or_anchor_valid.tolist() == [
                task_id == 4
            ]
            target_sg = K36_TARGET_SG_LOCAL_INDEX[identity]
            assert supervision.target_residue_reactive_atom_local_index.tolist() == [
                target_sg
            ]
            assert supervision.target_residue_reactive_atom_flat_index.tolist() == [
                target_sg
            ]
            assert int(
                supervision.target_residue_reactive_atom_mask.sum().item()
            ) == 1
            positive_index = int(
                supervision.pair_positive_candidate_index[0].item()
            )
            assert supervision.pair_candidate_ligand_local_index[
                positive_index
            ].item() == 20
            assert supervision.pair_candidate_pocket_flat_index[
                positive_index
            ].item() == target_sg
            assert int(supervision.pair_candidate_is_positive.sum().item()) == 1
            assert torch.equal(
                supervision.pair_candidate_is_negative,
                ~supervision.pair_candidate_is_positive,
            )
            assert bool(
                torch.isfinite(
                    supervision.observed_complex_pair_distance_angstrom
                ).all().item()
            )
            assert bool(
                torch.isfinite(
                    supervision.ligand_anchor_distance_angstrom
                ).all().item()
            )
            assert torch.isnan(
                supervision.pre_post_geometry_target_angstrom
            ).all()
            assert not supervision.pre_post_geometry_component_valid_mask.any()
            assert not supervision.pre_post_geometry_component_loss_mask.any()
    assert valid_instance_count == 15


def test_k36_exact10_invalid_task_matrix_fails_closed() -> None:
    invalid_count = 0
    for identity in subject.K36_MEMBER_IDENTITIES_V1:
        for task_id in subject.K36_NOT_APPLICABLE_TASK_IDS_V1:
            with pytest.raises(
                ValueError,
                match=(
                    f"^{ERROR}:TASK_NOT_APPLICABLE_FOR_ROLE_PROFILE$"
                ),
            ):
                _k36(identity, task_id)
            invalid_count += 1
    assert invalid_count == 10


def test_k36_authoritative_order_exact10_and_endpoint_indices() -> None:
    records, samples, topology = _parsed_sources()
    assert tuple(sorted(records)) == subject.K36_MEMBER_IDENTITIES_V1
    assert tuple(sorted(samples)) == subject.K36_MEMBER_IDENTITIES_V1
    assert topology["semantic_topology_sha256"] == (
        subject.K36_TOPOLOGY_SEMANTIC_SHA256_V1
    )
    for identity in subject.K36_MEMBER_IDENTITIES_V1:
        rows = samples[identity]["canonical_model_bound_ligand_atoms"]
        assert tuple(row["label_atom_id"] for row in rows) == (
            K36_LIGAND_NODE_ORDER
        )
        result = _k36(identity, 0)
        assert result.model_input_batch["lig_parser_local_index"].tolist() == (
            list(range(29))
        )
        assert result.model_input_batch["lig_one_hot"].argmax(dim=1).tolist() == [
            row["exact10_channel_index"] for row in rows
        ]
        assert K36_LIGAND_NODE_ORDER[18:22] == (
            "N19", "C20", "C21", "O22"
        )


def test_carrier_hash_records_and_historical_false_are_distinct_from_materialization(
) -> None:
    payload = CARRIER.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == (
        subject.K36_EFFECTIVE_CARRIER_SHA256_V1
    )
    parsed = successor.strict_parse_authority_json_v1(payload)
    records = subject._validated_k36_carrier_semantics_v1(payload)
    assert {
        identity: record["effective_supervision_record_sha256"]
        for identity, record in records.items()
    } == subject.K36_RECORD_SHA256_BY_IDENTITY_V1
    summary = parsed["ingestion_effective_authority_summary"]
    assert summary["effective_supervision_materialized"] is False
    assert summary["state_modified"] is False
    assert _k36("4DCD/K36", 0).supervision.sample_training_admitted.item()


def _reverse_objects(value: object) -> object:
    if type(value) is dict:
        return {
            key: _reverse_objects(item)
            for key, item in reversed(tuple(value.items()))
        }
    if type(value) is list:
        return [_reverse_objects(item) for item in value]
    return value


def test_carrier_json_key_order_is_semantically_irrelevant() -> None:
    parsed = successor.strict_parse_authority_json_v1(CARRIER.read_bytes())
    reordered = json.dumps(
        _reverse_objects(parsed),
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("ascii")
    assert hashlib.sha256(reordered).hexdigest() != (
        subject.K36_EFFECTIVE_CARRIER_SHA256_V1
    )
    records = subject._validated_k36_carrier_semantics_v1(reordered)
    assert tuple(sorted(records)) == subject.K36_MEMBER_IDENTITIES_V1


def test_public_path_rejects_carrier_sha_drift(tmp_path: Path) -> None:
    state = tmp_path / "state"
    target = state / subject.K36_EFFECTIVE_CARRIER_RELATIVE_PATH_V1
    target.parent.mkdir(parents=True)
    target.write_bytes(CARRIER.read_bytes() + b"\n")
    with pytest.raises(ValueError, match=f"^{ERROR}:SOURCE_SHA256_MISMATCH$"):
        subject.tensorize_covapie_expanded_cys_sg_sample_v1(
            sample_identity="4DCD/K36",
            task_id=0,
            repository_root=ROOT,
            state_root=state,
        )


def _mutate_carrier(parsed: dict[str, object], mutation: str) -> None:
    records = parsed["effective_supervision_records"]
    assert type(records) is list
    first = records[0]
    assert type(first) is dict
    if mutation == "record_hash_drift":
        first["effective_supervision_record_sha256"] = "0" * 64
    elif mutation == "missing_member":
        records.pop()
    elif mutation == "duplicate_member":
        records[-1] = copy.deepcopy(first)
    elif mutation == "wrong_family":
        first["reaction_family_authority_id"] = "WRONG"
    elif mutation == "wrong_rule":
        first["warhead_rule_authority_id"] = "WRONG"
    elif mutation == "wrong_active_warhead":
        first["reviewed_active_warhead_atom_ids"] = ["C20", "O22"]
    elif mutation == "nonempty_linker":
        first["reviewed_linker_atom_ids"] = ["C20"]
        first["reviewed_linker_atom_count"] = 1
    elif mutation == "wrong_role_profile":
        first["role_profile"] = "STRICT_LINKER_PRESENT_V1"
    elif mutation == "wrong_valid_tasks":
        first["valid_task_ids"] = [0, 1, 3, 4]
    elif mutation == "boundary":
        first["direct_boundary_semantics"]["scaffold_side_atom_id"] = "N19"
    elif mutation == "target_sg":
        first["target_residue_atom_id"] = "CB"
    elif mutation == "reactive_c21":
        first["ligand_reactive_atom_id"] = "C20"
    elif mutation == "seed":
        first["minimal_seed_atom_ids"] = ["C20", "C24"]
    elif mutation == "geometry":
        first["PRE_geometry_supervision_authority_status"] = "ESTABLISHED"
    else:
        raise AssertionError(mutation)


@pytest.mark.parametrize(
    "mutation",
    (
        "record_hash_drift",
        "missing_member",
        "duplicate_member",
        "wrong_family",
        "wrong_rule",
        "wrong_active_warhead",
        "nonempty_linker",
        "wrong_role_profile",
        "wrong_valid_tasks",
        "boundary",
        "target_sg",
        "reactive_c21",
        "seed",
        "geometry",
    ),
)
def test_carrier_semantic_mutations_fail_closed(mutation: str) -> None:
    parsed = successor.strict_parse_authority_json_v1(CARRIER.read_bytes())
    _mutate_carrier(parsed, mutation)
    payload = json.dumps(
        parsed, ensure_ascii=True, allow_nan=False, separators=(",", ":")
    ).encode("ascii")
    with pytest.raises(subject._MixedProfileInvariantError):
        subject._validated_k36_carrier_semantics_v1(payload)


def _mutate_structural_sample(sample: dict[str, object], mutation: str) -> None:
    ligand = sample["canonical_model_bound_ligand_atoms"]
    assert type(ligand) is list
    if mutation == "ligand_missing":
        ligand.pop()
    elif mutation == "ligand_duplicate":
        ligand[-1] = copy.deepcopy(ligand[0])
    elif mutation == "order_mapping_ambiguity":
        ligand[-1]["source_atom_site_row_index_0based"] = ligand[0][
            "source_atom_site_row_index_0based"
        ]
    elif mutation == "explicit_hydrogen":
        ligand[-1]["type_symbol"] = "H"
    elif mutation == "unsupported_non_h":
        ligand[-1]["type_symbol"] = "Xe"
    elif mutation == "channel_corruption":
        ligand[-1]["exact10_channel_index"] = 1
    elif mutation == "target_sg_mutation":
        sample["explicit_event"]["protein_endpoint"]["auth_atom_id"] = "CB"
    elif mutation == "pair_positive_mutation":
        sample["explicit_event"]["protein_ligand_covalent_event_edge"][
            "ligand_atom_name"
        ] = "C20"
    else:
        raise AssertionError(mutation)


@pytest.mark.parametrize(
    "mutation",
    (
        "ligand_missing",
        "ligand_duplicate",
        "order_mapping_ambiguity",
        "explicit_hydrogen",
        "unsupported_non_h",
        "channel_corruption",
        "target_sg_mutation",
        "pair_positive_mutation",
    ),
)
def test_structural_identity_feature_target_pair_mutations_fail_closed(
    mutation: str,
) -> None:
    records, samples, topology = _parsed_sources()
    sample = copy.deepcopy(samples["4DCD/K36"])
    _mutate_structural_sample(sample, mutation)
    with pytest.raises(subject._MixedProfileInvariantError):
        subject._validated_k36_sample_sources_v1(
            repository_root=ROOT,
            record=copy.deepcopy(records["4DCD/K36"]),
            structural_sample=sample,
            topology=copy.deepcopy(topology),
        )


def test_k36_determinism_reversed_selection_order_and_no_source_mutation() -> None:
    carrier_before = CARRIER.read_bytes()
    evidence_before = EVIDENCE.read_bytes()
    forward = {
        identity: _k36(identity, 4)
        for identity in subject.K36_MEMBER_IDENTITIES_V1
    }
    reverse = {
        identity: _k36(identity, 4)
        for identity in reversed(subject.K36_MEMBER_IDENTITIES_V1)
    }
    for identity in subject.K36_MEMBER_IDENTITIES_V1:
        left, right = forward[identity], reverse[identity]
        _assert_supervision_exact(left.supervision, right.supervision)
        for name in CORE_FIELDS - {"names", "receptors"}:
            _assert_tensor_exact(
                left.model_input_batch[name], right.model_input_batch[name]
            )
    assert CARRIER.read_bytes() == carrier_before
    assert EVIDENCE.read_bytes() == evidence_before


def _normalize_clone_modes(root: Path) -> None:
    for path in root.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        mode = stat.S_IMODE(path.stat().st_mode)
        path.chmod(0o755 if mode & 0o111 else 0o644)


@pytest.fixture(scope="module")
def real_current11_inputs(tmp_path_factory: pytest.TempPathFactory):
    from covalent_ext import (
        covapie_current11_checkpoint_migration_and_real_one_batch_train_path_smoke_v1
        as current11_smoke,
    )

    temporary = tmp_path_factory.mktemp("covapie_current11_golden")
    repository = temporary / "repository"
    completed = subprocess.run(
        (
            "git", "clone", "--local", "--no-hardlinks", str(ROOT),
            str(repository),
        ),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    _normalize_clone_modes(repository)
    built = current11_smoke._build_real_current11_batch_v1(
        repo_root=repository,
        state_root=STATE,
    )
    assert built["real_sample_count"] == 11
    assert built["real_ligand_node_count"] == 323
    assert built["real_pocket_node_count"] == 2202
    assert built["formal_carrier_sha256"] == (
        "ea3aa7c94b7c88993493662ad6ba7fd95e547ec62612a072f8248a515657e910"
    )
    return built


def test_current11_real_golden_all_samples_all_tasks_exact_parity(
    real_current11_inputs: dict[str, object],
) -> None:
    batch = real_current11_inputs["model_batch"]
    runtime = real_current11_inputs["runtime"]
    authority = real_current11_inputs["authoritative_supervision"]
    assert type(batch) is dict and type(runtime) is dict and type(authority) is dict
    sample_keys = authority["sample_keys"]
    assert type(sample_keys) is list and len(sample_keys) == 11
    original_tensors = {
        name: (value, value.clone())
        for name, value in batch.items()
        if isinstance(value, torch.Tensor)
    }
    observed_tasks = {key: [] for key in sample_keys}
    for epoch in range(5):
        reference = tensorize_covapie_current11_training_supervision_v1(
            batch=batch,
            runtime_result=runtime,
            authoritative_supervision=authority,
            device="cpu",
            epoch=epoch,
            task_schedule_seed=0,
        )
        ligand_offsets = authority["ligand_node_offsets"]
        pocket_offsets = authority["pocket_node_offsets"]
        assert type(ligand_offsets) is list and type(pocket_offsets) is list
        for requested_index, requested_identity in enumerate(sample_keys):
            requested_task = int(
                reference.canonical_task_id[requested_index].item()
            )
            mixed = subject.tensorize_covapie_expanded_cys_sg_sample_v1(
                sample_identity=requested_identity,
                task_id=requested_task,
                device="cpu",
                epoch=epoch,
                task_schedule_seed=0,
                current11_batch=batch,
                current11_runtime_result=runtime,
                current11_authoritative_supervision=authority,
            )
            assert mixed.model_input_batch is not batch
            assert mixed.model_input_batch["names"] == [requested_identity]
            ligand_start, ligand_end = ligand_offsets[
                requested_index:requested_index + 2
            ]
            pocket_start, pocket_end = pocket_offsets[
                requested_index:requested_index + 2
            ]
            for name in (
                "lig_coords", "lig_one_hot", "lig_source_row_index",
                "lig_parser_local_index",
            ):
                _assert_tensor_exact(
                    batch[name][ligand_start:ligand_end],
                    mixed.model_input_batch[name],
                )
            for name in (
                "pocket_coords", "pocket_one_hot", "pocket_source_row_index",
                "pocket_parser_local_index",
            ):
                _assert_tensor_exact(
                    batch[name][pocket_start:pocket_end],
                    mixed.model_input_batch[name],
                )
            assert mixed.model_input_batch["num_lig_atoms"].tolist() == [
                ligand_end - ligand_start
            ]
            assert mixed.model_input_batch["num_pocket_nodes"].tolist() == [
                pocket_end - pocket_start
            ]
            assert not mixed.model_input_batch["lig_mask"].any()
            assert not mixed.model_input_batch["pocket_mask"].any()
            assert mixed.role_profile == subject.STRICT_LINKER_PRESENT_V1
            assert mixed.valid_task_ids == (0, 1, 2, 3, 4)
            _assert_current11_singleton_parity(
                reference=reference,
                observed=mixed.supervision,
                authority=authority,
                sample_ordinal=requested_index,
            )
            observed_tasks[requested_identity].append(requested_task)
    assert all(sorted(tasks) == [0, 1, 2, 3, 4] for tasks in observed_tasks.values())
    for name, (identity, before) in original_tensors.items():
        assert batch[name] is identity
        _assert_tensor_exact(batch[name], before)


def test_current11_explicit_task_schedule_mismatch_fails_closed(
    real_current11_inputs: dict[str, object],
) -> None:
    batch = real_current11_inputs["model_batch"]
    runtime = real_current11_inputs["runtime"]
    authority = real_current11_inputs["authoritative_supervision"]
    sample = authority["sample_keys"][0]
    reference = tensorize_covapie_current11_training_supervision_v1(
        batch=batch,
        runtime_result=runtime,
        authoritative_supervision=authority,
        device="cpu",
        epoch=0,
        task_schedule_seed=0,
    )
    wrong_task = (int(reference.canonical_task_id[0].item()) + 1) % 5
    with pytest.raises(
        ValueError,
        match=f"^{ERROR}:CURRENT11_REQUESTED_TASK_SCHEDULE_MISMATCH$",
    ):
        subject.tensorize_covapie_expanded_cys_sg_sample_v1(
            sample_identity=sample,
            task_id=wrong_task,
            epoch=0,
            current11_batch=batch,
            current11_runtime_result=runtime,
            current11_authoritative_supervision=authority,
        )


def test_mixed_profile_same_public_api_selection_smoke(
    real_current11_inputs: dict[str, object],
) -> None:
    batch = real_current11_inputs["model_batch"]
    runtime = real_current11_inputs["runtime"]
    authority = real_current11_inputs["authoritative_supervision"]
    current_identity = authority["sample_keys"][0]
    current = subject.tensorize_covapie_expanded_cys_sg_sample_v1(
        sample_identity=current_identity,
        task_id=0,
        current11_batch=batch,
        current11_runtime_result=runtime,
        current11_authoritative_supervision=authority,
    )
    direct = subject.tensorize_covapie_expanded_cys_sg_sample_v1(
        sample_identity="4DCD/K36",
        task_id=0,
        repository_root=ROOT,
        state_root=STATE,
    )
    assert type(current) is type(direct) is (
        subject.CovapieExpandedCysSgTensorizedSampleV1
    )
    assert type(current.supervision) is type(direct.supervision) is (
        CovapieCurrent11TrainingSupervisionTensorsV1
    )
    assert current.model_input_batch["names"] == [current_identity]
    assert direct.model_input_batch["names"] == ["4DCD/K36"]
    assert current.model_input_batch["num_lig_atoms"].shape == (1,)
    assert direct.model_input_batch["num_lig_atoms"].shape == (1,)
    assert CORE_FIELDS.issubset(current.model_input_batch)
    assert CORE_FIELDS.issubset(direct.model_input_batch)
    assert current.valid_task_ids == (0, 1, 2, 3, 4)
    assert direct.valid_task_ids == (0, 3, 4)
    assert current.role_profile != direct.role_profile
    assert current.model_input_batch["lig_one_hot"].shape[1] == 10
    assert direct.model_input_batch["lig_one_hot"].shape[1] == 10


def test_import_has_no_output_side_effects() -> None:
    completed = subprocess.run(
        (
            os.environ.get("PYTHON", "python"),
            "-c",
            "import covalent_ext.covapie_expanded_cys_sg_mixed_profile_tensorizer_v1",
        ),
        cwd=ROOT,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": ".:src",
        },
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""
