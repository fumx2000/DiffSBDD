from __future__ import annotations

import ast
import gzip
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest
import torch

from covalent_ext import (
    covapie_ffq_project_level_authority_ingestion_and_effective_supervision_successor_v1
    as ffq_successor,
)
from covalent_ext import covapie_ffq_supervised_forward_adapter_v1 as subject


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT = ROOT / "checkpoints/crossdocked_fullatom_cond.ckpt"
SOURCE = ROOT / "src/covalent_ext/covapie_ffq_supervised_forward_adapter_v1.py"
ATOM_SITE_COLUMNS = (
    "_atom_site.group_PDB",
    "_atom_site.id",
    "_atom_site.type_symbol",
    "_atom_site.label_atom_id",
    "_atom_site.label_alt_id",
    "_atom_site.label_comp_id",
    "_atom_site.label_asym_id",
    "_atom_site.label_seq_id",
    "_atom_site.Cartn_x",
    "_atom_site.Cartn_y",
    "_atom_site.Cartn_z",
    "_atom_site.occupancy",
    "_atom_site.auth_seq_id",
    "_atom_site.auth_comp_id",
    "_atom_site.auth_asym_id",
    "_atom_site.auth_atom_id",
    "_atom_site.pdbx_PDB_ins_code",
    "_atom_site.pdbx_PDB_model_num",
)
TARGET_ATOMS = (
    ("N", "N"),
    ("CA", "C"),
    ("C", "C"),
    ("O", "O"),
    ("CB", "C"),
    ("SG", "S"),
)
LIGAND_ORDER_0 = ("O3", "C2", "P1", "O1", "C1", "O4", "C3", "O2")
LIGAND_ORDER_1_WITH_H = (
    "H1",
    "O2",
    "C3",
    "O4",
    "C1",
    "O1",
    "P1",
    "C2",
    "O3",
)


def _record(pdb_id: str) -> dict[str, Any]:
    event_id = (
        "COVAPIE_CYS_SG_EVENT_V1:3VCY:A:CYS:116-:SG:E:FFQ:C1"
        if pdb_id == "3VCY"
        else "COVAPIE_CYS_SG_EVENT_V1:4R7U:A:CYS:116-:SG:F:FFQ:C1"
    )
    return ffq_successor._expected_record(
        {
            "canonical_event_id": event_id,
            "pdb_id": pdb_id,
            "completed_lane": (
                "COMPLETED_HUMAN_POSITIVE_TRAINING_CANDIDATE"
                if pdb_id == "3VCY"
                else "COMPLETED_HUMAN_CHEMISTRY_POSITIVE_TRAINING_EXCLUDED"
            ),
        }
    )


def _row(
    *,
    group: str,
    atom_id: str,
    symbol: str,
    component: str,
    label_asym: str,
    label_seq: str,
    auth_asym: str,
    auth_seq: str,
    xyz: tuple[float, float, float],
) -> dict[str, str]:
    return {
        "_atom_site.group_PDB": group,
        "_atom_site.id": "",
        "_atom_site.type_symbol": symbol,
        "_atom_site.label_atom_id": atom_id,
        "_atom_site.label_alt_id": ".",
        "_atom_site.label_comp_id": component,
        "_atom_site.label_asym_id": label_asym,
        "_atom_site.label_seq_id": label_seq,
        "_atom_site.Cartn_x": f"{xyz[0]:.3f}",
        "_atom_site.Cartn_y": f"{xyz[1]:.3f}",
        "_atom_site.Cartn_z": f"{xyz[2]:.3f}",
        "_atom_site.occupancy": "1.00",
        "_atom_site.auth_seq_id": auth_seq,
        "_atom_site.auth_comp_id": component,
        "_atom_site.auth_asym_id": auth_asym,
        "_atom_site.auth_atom_id": atom_id,
        "_atom_site.pdbx_PDB_ins_code": ".",
        "_atom_site.pdbx_PDB_model_num": "1",
    }


def _symbol(atom_id: str) -> str:
    return "H" if atom_id.startswith("H") else atom_id[0]


def _payload(pdb_id: str) -> bytes:
    base = 10.0 if pdb_id == "3VCY" else 30.0
    ligand_asym = "E" if pdb_id == "3VCY" else "F"
    ligand_order = LIGAND_ORDER_0 if pdb_id == "3VCY" else LIGAND_ORDER_1_WITH_H
    extra_before = 0 if pdb_id == "3VCY" else 3
    extra_after = 2 if pdb_id == "3VCY" else 0
    rows: list[dict[str, str]] = []
    for index in range(extra_before):
        rows.append(
            _row(
                group="ATOM",
                atom_id=f"X{index}",
                symbol="C",
                component="ALA",
                label_asym="A",
                label_seq=str(100 + index),
                auth_asym="A",
                auth_seq=str(100 + index),
                xyz=(base + 1.0, base + 0.1 * index, base),
            )
        )
    for index, (atom_id, symbol) in enumerate(TARGET_ATOMS):
        rows.append(
            _row(
                group="ATOM",
                atom_id=atom_id,
                symbol=symbol,
                component="CYS",
                label_asym="A",
                label_seq="116",
                auth_asym="A",
                auth_seq="116",
                xyz=(base + 1.0 + 0.1 * index, base, base),
            )
        )
    for index in range(extra_after):
        rows.append(
            _row(
                group="ATOM",
                atom_id=f"Y{index}",
                symbol="N",
                component="GLY",
                label_asym="A",
                label_seq=str(130 + index),
                auth_asym="A",
                auth_seq=str(130 + index),
                xyz=(base + 0.5, base + 0.1 * index, base),
            )
        )
    rows.append(
        _row(
            group="ATOM",
            atom_id="FAR",
            symbol="C",
            component="GLY",
            label_asym="A",
            label_seq="999",
            auth_asym="A",
            auth_seq="999",
            xyz=(base + 20.0, base, base),
        )
    )
    for index, atom_id in enumerate(ligand_order):
        rows.append(
            _row(
                group="HETATM",
                atom_id=atom_id,
                symbol=_symbol(atom_id),
                component="FFQ",
                label_asym=ligand_asym,
                label_seq=".",
                auth_asym="A",
                auth_seq="501",
                xyz=(base + 0.1 * index, base, base),
            )
        )
    for index, row in enumerate(rows, start=1):
        row["_atom_site.id"] = str(index)
    lines = [f"data_{pdb_id}", f"_entry.id {pdb_id}", "#", "loop_", *ATOM_SITE_COLUMNS]
    lines.extend(" ".join(row[column] for column in ATOM_SITE_COLUMNS) for row in rows)
    lines.append("#")
    return gzip.compress(("\n".join(lines) + "\n").encode(), mtime=0)


def _sample(pdb_id: str, task_id: int = 0) -> dict[str, object]:
    return {
        "cif_gz_payload": _payload(pdb_id),
        "effective_supervision_record": _record(pdb_id),
        "canonical_task_id": task_id,
    }


def _synthetic_samples() -> list[dict[str, object]]:
    return [_sample("3VCY"), _sample("4R7U")]


def _run(
    samples: list[dict[str, object]], *, state_root: Path
) -> subject.FFQTaskASupervisedForwardResultV1:
    return subject.run_covapie_ffq_task_a_supervised_forward_v1(
        samples=samples,
        checkpoint_path=CHECKPOINT,
        repository_root=ROOT,
        state_root=state_root,
    )


@pytest.fixture(scope="module")
def portable_state_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    state_root = tmp_path_factory.mktemp("empty-runtime-root")
    assert tuple(state_root.iterdir()) == ()
    return state_root


@pytest.fixture(scope="module")
def synthetic_run(portable_state_root: Path) -> tuple[
    subject.FFQTaskASupervisedForwardResultV1, torch.Tensor, torch.Tensor
]:
    rng_before = torch.random.get_rng_state().clone()
    result = _run(_synthetic_samples(), state_root=portable_state_root)
    rng_after = torch.random.get_rng_state().clone()
    return result, rng_before, rng_after


@pytest.fixture(scope="module")
def synthetic_result(
    synthetic_run: tuple[
        subject.FFQTaskASupervisedForwardResultV1, torch.Tensor, torch.Tensor
    ],
) -> subject.FFQTaskASupervisedForwardResultV1:
    return synthetic_run[0]


@pytest.fixture(scope="module")
def repeated_result(
    portable_state_root: Path,
) -> subject.FFQTaskASupervisedForwardResultV1:
    return _run(_synthetic_samples(), state_root=portable_state_root)


def test_task_a_two_sample_forward_preserves_identity_and_admission(
    synthetic_result: subject.FFQTaskASupervisedForwardResultV1,
) -> None:
    assert len(synthetic_result.sample_identities) == 2
    assert synthetic_result.structural_batch_summary["sample_admission"] == (
        False,
        False,
    )
    assert not synthetic_result.supervision.sample_training_admitted.any()
    assert synthetic_result.supervision.canonical_task_id.tolist() == [0, 0]
    assert synthetic_result.supervision.canonical_task_valid.tolist() == [True, True]


def test_loss_masks_and_task_a_seed_semantics_remain_false(
    synthetic_result: subject.FFQTaskASupervisedForwardResultV1,
) -> None:
    supervision = synthetic_result.supervision
    assert not supervision.ligand_active_diffusion_loss_mask.any()
    assert not supervision.pair_head_candidate_loss_mask.any()
    assert not supervision.pair_contrastive_sample_loss_mask.any()
    assert not supervision.pre_post_geometry_component_loss_mask.any()
    assert not supervision.ligand_minimal_seed_or_anchor_mask.any()
    assert supervision.ligand_minimal_seed_or_anchor_valid.tolist() == [False, False]


def test_anchor_distances_are_valid_mechanical_features(
    synthetic_result: subject.FFQTaskASupervisedForwardResultV1,
) -> None:
    supervision = synthetic_result.supervision
    assert supervision.ligand_anchor_distance_angstrom.shape == (16, 1)
    assert supervision.ligand_anchor_distance_valid.all()
    assert torch.isfinite(supervision.ligand_anchor_distance_angstrom).all()
    assert (supervision.ligand_anchor_distance_angstrom >= 0).all()
    assert supervision.observed_complex_pair_distance_valid.all()


def test_pair_domain_counts_labels_and_losses_are_independent(
    synthetic_result: subject.FFQTaskASupervisedForwardResultV1,
) -> None:
    supervision = synthetic_result.supervision
    assert supervision.pair_candidate_offsets.tolist() == [0, 48, 96]
    assert len(supervision.pair_candidate_is_positive) == 96
    assert supervision.pair_candidate_is_positive.sum().item() == 2
    assert supervision.pair_candidate_is_negative.sum().item() == 94
    assert supervision.pair_negative_count.tolist() == [47, 47]
    assert supervision.pair_positive_candidate_valid.tolist() == [True, True]
    assert not supervision.pair_head_candidate_loss_mask.any()


def test_positive_pair_flat_indices_bind_to_structural_owner(
    synthetic_result: subject.FFQTaskASupervisedForwardResultV1,
) -> None:
    result = synthetic_result
    supervision = result.supervision
    indices = supervision.pair_positive_candidate_index
    assert torch.equal(
        supervision.pair_candidate_ligand_flat_index[indices],
        result.structural_alignment.ligand_reactive_flat_indices,
    )
    assert torch.equal(
        supervision.pair_candidate_pocket_flat_index[indices],
        result.structural_alignment.target_reactive_flat_indices,
    )
    assert supervision.pair_candidate_batch_index[indices].tolist() == [0, 1]


def test_public_checkpoint_migration_is_exact_and_checkpoint_authentic(
    synthetic_result: subject.FFQTaskASupervisedForwardResultV1,
) -> None:
    migration = synthetic_result.migration_summary
    assert migration["checkpoint_key_count"] == 122
    assert migration["target_model_key_count"] == 141
    assert migration["shared_key_count"] == 122
    assert migration["target_only_key_count"] == 19
    assert migration["checkpoint_only_key_count"] == 0
    assert migration["shared_shape_mismatch_count"] == 0
    assert migration["migration_missing_keys"] == ()
    assert migration["migration_unexpected_keys"] == ()
    assert migration["shared_checkpoint_tensor_equality_count"] == 122
    assert migration["node_histogram_source"] == "legacy_constructor.node_histogram"
    assert migration["node_histogram_shape"] == (107, 1671)


def test_zero_initial_conditioning_is_preserved(
    synthetic_result: subject.FFQTaskASupervisedForwardResultV1,
) -> None:
    assert synthetic_result.target_residue_embedding_max_abs == 0.0
    assert synthetic_result.role_mask_anchor_hidden_delta_exact_zero
    assert torch.equal(
        synthetic_result.role_mask_anchor_hidden_delta,
        torch.zeros_like(synthetic_result.role_mask_anchor_hidden_delta),
    )


def test_target_indicator_is_exactly_one_sg_per_sample(
    synthetic_result: subject.FFQTaskASupervisedForwardResultV1,
) -> None:
    result = synthetic_result
    indicator = result.supervision.target_residue_reactive_atom_mask[:, 0]
    pocket_mask = result.structural_alignment.model_input_batch["pocket_mask"]
    assert torch.bincount(pocket_mask[indicator], minlength=2).tolist() == [1, 1]
    assert torch.nonzero(indicator).flatten().tolist() == (
        result.structural_alignment.target_reactive_flat_indices.tolist()
    )


def test_task_a_generation_and_fixed_counts_are_four_each(
    synthetic_result: subject.FFQTaskASupervisedForwardResultV1,
) -> None:
    supervision = synthetic_result.supervision
    ligand_mask = synthetic_result.structural_alignment.model_input_batch["lig_mask"]
    generated = supervision.ligand_base_generation_mask[:, 0]
    fixed = supervision.ligand_base_fixed_mask[:, 0]
    assert torch.bincount(ligand_mask[generated], minlength=2).tolist() == [4, 4]
    assert torch.bincount(ligand_mask[fixed], minlength=2).tolist() == [4, 4]
    assert torch.equal(generated, ~fixed)


def test_masked_noising_and_denoising_keep_fixed_rows_exact(
    synthetic_result: subject.FFQTaskASupervisedForwardResultV1,
) -> None:
    result = synthetic_result
    fixed = result.supervision.ligand_base_fixed_mask[:, 0]
    assert torch.equal(result.noised_ligand_xh[fixed], result.clean_ligand_xh[fixed])
    assert torch.equal(
        result.model_output.denoised_ligand_xh[fixed],
        result.clean_ligand_xh[fixed],
    )
    assert not result.sampled_epsilon_ligand[fixed].any()


def test_functional_dynamics_is_finite_and_coordinate_masked(
    synthetic_result: subject.FFQTaskASupervisedForwardResultV1,
) -> None:
    result = synthetic_result
    output = result.functional_dynamics_output
    assert output.decoded_ligand_dynamics.shape == (16, 13)
    assert output.decoded_pocket_dynamics.shape[0] == result.clean_pocket_xh.shape[0]
    assert torch.isfinite(output.decoded_ligand_dynamics).all()
    assert torch.isfinite(output.decoded_pocket_dynamics).all()
    fixed = result.supervision.ligand_base_fixed_mask[:, 0]
    assert torch.equal(
        output.decoded_ligand_dynamics[fixed, :3],
        torch.zeros_like(output.decoded_ligand_dynamics[fixed, :3]),
    )
    assert torch.equal(
        output.coordinate_update_mask[:16, 0].bool(),
        result.supervision.ligand_base_generation_mask[:, 0],
    )
    assert not output.coordinate_update_mask[16:].any()


def test_pair_and_geometry_raw_outputs_are_bounded_fresh_predictions(
    synthetic_result: subject.FFQTaskASupervisedForwardResultV1,
) -> None:
    output = synthetic_result.model_output
    assert output.pair_logits.shape == (96,)
    assert output.pair_embeddings.shape[0] == 96
    assert torch.isfinite(output.pair_logits).all()
    assert output.pre_post_geometry_predictions_angstrom.shape == (96, 2)
    assert torch.isfinite(output.pre_post_geometry_predictions_angstrom).all()
    assert (output.pre_post_geometry_predictions_angstrom > 0).all()
    assert output.target_pair_consistency.tolist() == [True, True]


def test_geometry_supervision_remains_unavailable(
    synthetic_result: subject.FFQTaskASupervisedForwardResultV1,
) -> None:
    supervision = synthetic_result.supervision
    assert torch.isnan(supervision.pre_post_geometry_target_angstrom).all()
    assert not supervision.pre_post_geometry_component_valid_mask.any()
    assert not supervision.pre_post_geometry_component_loss_mask.any()
    assert synthetic_result.raw_geometry_prediction_available
    assert not synthetic_result.geometry_authority_available


def test_state_inputs_grads_and_execution_boundary_are_immutable(
    synthetic_result: subject.FFQTaskASupervisedForwardResultV1,
) -> None:
    result = synthetic_result
    assert result.state_tensor_changed_count == 0
    assert result.input_tensor_changed_count == 0
    assert result.all_parameter_grads_none
    assert result.model_eval_mode_verified
    assert result.ddpm_eval_mode_verified
    assert result.auxiliary_eval_mode_verified
    assert result.gradient_recording_disabled
    assert not result.joint_objective_loss_executed
    assert not result.base_diffusion_loss_executed
    assert not result.pair_loss_executed
    assert not result.geometry_loss_executed
    assert not result.contrastive_loss_executed
    assert not result.current11_runtime_executed
    assert not result.training_performed
    assert not result.backward_performed
    assert not result.optimizer_step_performed
    assert not result.parameter_update_performed


def test_adapter_does_not_change_global_torch_rng(
    synthetic_run: tuple[
        subject.FFQTaskASupervisedForwardResultV1, torch.Tensor, torch.Tensor
    ],
) -> None:
    _, before, after = synthetic_run
    assert torch.equal(before, after)


def test_independent_calls_are_deterministic(
    synthetic_result: subject.FFQTaskASupervisedForwardResultV1,
    repeated_result: subject.FFQTaskASupervisedForwardResultV1,
) -> None:
    left = synthetic_result
    right = repeated_result
    tensors = (
        (left.functional_dynamics_output.decoded_ligand_dynamics,
         right.functional_dynamics_output.decoded_ligand_dynamics),
        (left.functional_dynamics_output.decoded_pocket_dynamics,
         right.functional_dynamics_output.decoded_pocket_dynamics),
        (left.functional_dynamics_output.ligand_node_hidden,
         right.functional_dynamics_output.ligand_node_hidden),
        (left.functional_dynamics_output.pocket_node_hidden,
         right.functional_dynamics_output.pocket_node_hidden),
        (left.model_output.pair_logits, right.model_output.pair_logits),
        (left.model_output.pre_post_geometry_predictions_angstrom,
         right.model_output.pre_post_geometry_predictions_angstrom),
    )
    assert all(torch.equal(first, second) for first, second in tensors)


@pytest.mark.parametrize("task_id", [1, 2, 3, 4])
def test_non_task_a_fails_with_exact_reason(
    task_id: int, portable_state_root: Path
) -> None:
    samples = _synthetic_samples()
    samples[1]["canonical_task_id"] = task_id
    with pytest.raises(
        subject.FFQSupervisedForwardAdapterError,
        match=subject.TASK_NOT_SUPPORTED_BY_FFQ_SUPERVISED_FORWARD_V1,
    ):
        _run(samples, state_root=portable_state_root)


def test_checkpoint_sha_drift_fails_closed_without_checkpoint_copy(
    portable_state_root: Path,
) -> None:
    with pytest.raises(subject.FFQSupervisedForwardAdapterError):
        subject.run_covapie_ffq_task_a_supervised_forward_v1(
            samples=_synthetic_samples(),
            checkpoint_path=SOURCE,
            repository_root=ROOT,
            state_root=portable_state_root,
        )


def test_public_migration_rejects_an_augmented_model_key_mismatch(
    monkeypatch: pytest.MonkeyPatch, portable_state_root: Path
) -> None:
    original = subject._instantiate_augmented_model_v1

    def mismatched_model(**kwargs: object) -> torch.nn.Module:
        model = original(**kwargs)
        model.register_parameter(
            "ffq_migration_mismatch_probe",
            torch.nn.Parameter(torch.zeros(1)),
        )
        return model

    monkeypatch.setattr(subject, "_instantiate_augmented_model_v1", mismatched_model)
    with pytest.raises(subject.FFQSupervisedForwardAdapterError):
        _run(_synthetic_samples(), state_root=portable_state_root)


def test_unknown_extra_sample_field_still_fails_in_structural_owner(
    portable_state_root: Path,
) -> None:
    samples = _synthetic_samples()
    samples[0]["unknown_extra_field"] = "forbidden"
    with pytest.raises(subject.FFQSupervisedForwardAdapterError):
        _run(samples, state_root=portable_state_root)


@pytest.mark.parametrize("device", ["cuda", "cpu:0", "CPU"])
def test_non_exact_cpu_device_fails_closed(
    device: str, portable_state_root: Path
) -> None:
    with pytest.raises(subject.FFQSupervisedForwardAdapterError):
        subject.run_covapie_ffq_task_a_supervised_forward_v1(
            samples=_synthetic_samples(),
            checkpoint_path=CHECKPOINT,
            repository_root=ROOT,
            state_root=portable_state_root,
            device=device,
        )


def test_production_ast_has_no_forbidden_training_or_loss_calls() -> None:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    called_names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if isinstance(function, ast.Name):
            called_names.add(function.id)
        elif isinstance(function, ast.Attribute):
            called_names.add(function.attr)
    assert called_names.isdisjoint(
        {
            "forward",
            "run_covapie_current11_five_mask_diffusion_and_hidden_readout_v1",
            "compute_covapie_current11_training_losses_v1",
            "training_step",
            "validation_step",
            "test_step",
            "backward",
            "grad",
            "configure_optimizers",
            "optimizer",
            "fit",
        }
    )


def test_import_has_no_output_or_filesystem_write(tmp_path: Path) -> None:
    environment = dict(os.environ)
    environment.update(
        {
            "PYTHONPATH": os.pathsep.join((str(ROOT), str(ROOT / "src"))),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONWARNINGS": "ignore",
        }
    )
    process = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            "import covalent_ext.covapie_ffq_supervised_forward_adapter_v1",
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode == 0
    assert process.stdout == ""
    assert process.stderr == ""
    assert tuple(tmp_path.iterdir()) == ()


def test_augmented_constructor_uses_validated_legacy_checkpoint_semantics(
    synthetic_result: subject.FFQTaskASupervisedForwardResultV1,
    portable_state_root: Path,
) -> None:
    migration = synthetic_result.migration_summary
    assert migration["model_constructor_source"] == (
        "validated_legacy_checkpoint_constructor"
    )
    assert migration["node_histogram_source"] == "legacy_constructor.node_histogram"
    assert migration["legacy_constructor_node_histogram_shape"] == (107, 1671)
    assert migration["current_yaml_model_semantics_consumed"] is False
    assert migration["runtime_device_override"] == ("egnn_params.device",)
    assert migration["constructor_dataset"] == "crossdock"
    assert migration["constructor_batch_size"] == 16
    assert migration["crossdock_exact10_full_atom_mapping_verified"] is True
    assert migration["crossdock_exact10_tokens"] == (
        "C", "N", "O", "S", "B", "Br", "Cl", "P", "I", "F"
    )
    assert tuple(portable_state_root.iterdir()) == ()


def test_production_constructor_has_no_current_yaml_semantic_dependency() -> None:
    production_tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    referenced_names = {
        node.id for node in ast.walk(production_tree) if isinstance(node, ast.Name)
    }
    assert referenced_names.isdisjoint(
        {
            "BEST_CONFIG_CANDIDATE_PATH",
            "CONFIG_PREVIEW_PATH",
            "load_config_preview_v0",
            "build_checkpoint_compatible_config_v0",
            "_constructor_config_from_compatible_config",
            "_temporary_10d_dataset_info",
        }
    )
    committed_test_source = Path(__file__).read_text(encoding="utf-8")
    committed_tree = ast.parse(committed_test_source)
    committed_names = {
        node.id for node in ast.walk(committed_tree) if isinstance(node, ast.Name)
    }
    assert "REAL" + "_CACHE" not in committed_names
    external_fragments = (
        "bulk-model-usable-" + "auto-admission-scaleup-v1",
        "manual-review-" + "aids",
        "../covapie-" + "state",
    )
    assert all(fragment not in committed_test_source for fragment in external_fragments)
