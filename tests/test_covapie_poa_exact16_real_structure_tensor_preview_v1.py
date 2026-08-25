from __future__ import annotations

from dataclasses import replace
import gzip
import hashlib
import os
from pathlib import Path
import subprocess
import sys
from typing import Callable

import pytest
import torch

from covalent_ext import (
    covapie_completed_human_decision_reconciliation_v1 as reconciliation,
)
from covalent_ext import (
    covapie_direct_attachment_optional_linker_runtime_v1 as direct_runtime,
)
from covalent_ext import (
    covapie_poa_exact16_real_structure_tensor_preview_v1 as subject,
)
from covalent_ext import (
    covapie_poa_sample_level_effective_supervision_v1 as metadata_owner,
)
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    CovapieCurrent11TrainingSupervisionTensorsV1,
)


ROOT = Path(__file__).resolve().parents[1]
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
    ("N", "N", 1.20),
    ("CA", "C", 1.35),
    ("C", "C", 1.50),
    ("O", "O", 1.65),
    ("CB", "C", 1.80),
    ("SG", "S", 2.02),
)
LIGAND_ATOMS = (
    ("C1", "C", 0.00),
    ("H1", "H", 0.10),
    ("C2", "C", 0.20),
    ("O2", "O", 0.40),
    ("O1P", "O", 0.60),
    ("O2P", "O", 0.80),
    ("O3P", "O", 1.00),
    ("P", "P", 1.20),
)


def _event_id(pdb_id: str, ordinal: int) -> str:
    ligand_asym = subject._EXPECTED_LIGAND_ASYMS[pdb_id][ordinal]
    protein_chain = chr(ord("A") + ordinal)
    return (
        f"COVAPIE_CYS_SG_EVENT_V1:{pdb_id}:{protein_chain}:"
        f"CYS:291-:SG:{ligand_asym}:POA:C2"
    )


def _record(
    pdb_id: str, ordinal: int = 0
) -> metadata_owner.POASampleLevelEffectiveSupervisionRecordV1:
    excluded = pdb_id == "4I3V"
    return metadata_owner.POASampleLevelEffectiveSupervisionRecordV1(
        schema_version=metadata_owner.SCHEMA_VERSION,
        canonical_event_id=_event_id(pdb_id, ordinal),
        review_unit_id=metadata_owner.REVIEW_UNIT_ID,
        pdb_id=pdb_id,
        subgroup_id=subject._EXPECTED_SUBGROUPS[pdb_id],
        human_review_completed=True,
        legacy_completed_review_status=reconciliation.COMPLETED_HUMAN_POSITIVE,
        task_relevance_disposition=reconciliation.TASK_RELEVANT,
        chemistry_disposition=reconciliation.CHEMISTRY_POSITIVE,
        training_use_disposition=(
            reconciliation.TRAINING_EXCLUDE
            if excluded
            else reconciliation.TRAINING_INCLUDE
        ),
        human_training_excluded=excluded,
        nongeometry_future_candidate=not excluded,
        chemistry_state_training_target_available=False,
        target_residue_name="CYS",
        target_residue_atom_id="SG",
        ligand_component_id="POA",
        ligand_reactive_atom_id="C2",
        reactive_pair_authority_available=True,
        pair_candidate_domain_materialized=False,
        source_role_profile=metadata_owner.SOURCE_ROLE_PROFILE,
        runtime_role_profile=direct_runtime.STRICT_LINKER_PRESENT_V1,
        scaffold_atom_ids=("P", "O1P", "O2P", "O3P"),
        linker_atom_ids=("C1",),
        warhead_atom_ids=("C2", "O2"),
        role_partition_authority_available=True,
        valid_task_ids=(0, 1, 2, 3, 4),
        task_structural_mask_labels_available=True,
        task_C_role_mask_available=True,
        task_C_minimal_seed_authority_available=False,
        precursor_evidence_status="PRECURSOR_EVIDENCE_NOT_ESTABLISHED",
        PRE_reaction_graph_authority_available=False,
        PRE_reaction_bond_order_authority_available=False,
        PRE_geometry_training_authority_available=False,
        POST_geometry_training_authority_available=False,
        reaction_family_authority_available=False,
        reaction_family_target_available=False,
        warhead_rule_authority_available=False,
        warhead_rule_target_available=False,
        warhead_type_target_available=False,
        split_authoritative=False,
        training_admitted=False,
    )


def _full_effective_supervision(
) -> metadata_owner.POASampleLevelEffectiveSupervisionResultV1:
    records = tuple(
        _record(pdb_id, ordinal)
        for pdb_id in ("4I3U", "4I3V")
        for ordinal in range(8)
    )
    result = metadata_owner.POASampleLevelEffectiveSupervisionResultV1(
        records=records,
        summary=metadata_owner._summary_from_records(records),
        source_provenance=(
            metadata_owner.POASampleLevelEffectiveSupervisionSourceProvenanceV1(
                formal_decision_path="synthetic/poa_formal_human_decision_v1.json",
                formal_decision_path_namespace="synthetic",
                formal_decision_byte_count=1,
                formal_decision_sha256="0" * 64,
                formal_decision_schema=metadata_owner.FORMAL_DECISION_SCHEMA,
                review_unit_id=metadata_owner.REVIEW_UNIT_ID,
                reconciliation_owner=(
                    "covalent_ext."
                    "covapie_completed_human_decision_reconciliation_v1"
                ),
                reconciliation_projection="project_poa_formal_decision_v1",
            )
        ),
    )
    assert metadata_owner.validate_covapie_poa_sample_level_effective_supervision_v1(
        result
    )
    return result


def _row(
    *,
    group: str,
    atom_id: str,
    symbol: str,
    component: str,
    label_asym: str,
    auth_asym: str,
    auth_seq: str,
    x: float,
    label_seq: str = ".",
    altloc: str = ".",
) -> dict[str, str]:
    return {
        "_atom_site.group_PDB": group,
        "_atom_site.id": "",
        "_atom_site.type_symbol": symbol,
        "_atom_site.label_atom_id": atom_id,
        "_atom_site.label_alt_id": altloc,
        "_atom_site.label_comp_id": component,
        "_atom_site.label_asym_id": label_asym,
        "_atom_site.label_seq_id": label_seq,
        "_atom_site.Cartn_x": f"{x:.3f}",
        "_atom_site.Cartn_y": "0.000",
        "_atom_site.Cartn_z": "0.000",
        "_atom_site.occupancy": "1.00",
        "_atom_site.auth_seq_id": auth_seq,
        "_atom_site.auth_comp_id": component,
        "_atom_site.auth_asym_id": auth_asym,
        "_atom_site.auth_atom_id": atom_id,
        "_atom_site.pdbx_PDB_ins_code": ".",
        "_atom_site.pdbx_PDB_model_num": "1",
    }


def _payload(
    pdb_id: str,
    *,
    entry_id: str | None = None,
    omit_ligand_atom: str | None = None,
    duplicate_ligand_c2: bool = False,
    ligand_symbol_overrides: dict[str, str] | None = None,
    omit_target: bool = False,
    omit_sg: bool = False,
    duplicate_sg: bool = False,
    target_outside_pocket: bool = False,
    unsupported_pocket_symbol: str | None = None,
    relevant_altloc_b: bool = False,
    translate: float = 0.0,
) -> bytes:
    ligand_asym = subject._EXPECTED_LIGAND_ASYMS[pdb_id][0]
    symbol_overrides = ligand_symbol_overrides or {}
    rows: list[dict[str, str]] = []
    target_shift = 20.0 if target_outside_pocket else 0.0
    if not omit_target:
        for atom_id, symbol, x in TARGET_ATOMS:
            if atom_id == "SG" and omit_sg:
                continue
            rows.append(
                _row(
                    group="ATOM",
                    atom_id=atom_id,
                    symbol=symbol,
                    component="CYS",
                    label_asym="A",
                    auth_asym="A",
                    auth_seq="291",
                    label_seq="291",
                    x=x + target_shift + translate,
                )
            )
        if duplicate_sg:
            rows.append(
                _row(
                    group="ATOM",
                    atom_id="SG",
                    symbol="S",
                    component="CYS",
                    label_asym="A",
                    auth_asym="A",
                    auth_seq="291",
                    label_seq="291",
                    x=2.12 + target_shift + translate,
                )
            )
    rows.extend(
        (
            _row(
                group="ATOM",
                atom_id="ALA_CLOSE",
                symbol=unsupported_pocket_symbol or "C",
                component="ALA",
                label_asym="A",
                auth_asym="A",
                auth_seq="300",
                label_seq="300",
                x=0.30 + translate,
                altloc="A" if relevant_altloc_b else ".",
            ),
            _row(
                group="ATOM",
                atom_id="ALA_FAR",
                symbol="N",
                component="ALA",
                label_asym="A",
                auth_asym="A",
                auth_seq="300",
                label_seq="300",
                x=12.00 + translate,
            ),
            _row(
                group="ATOM",
                atom_id="HPOCKET",
                symbol="H",
                component="ALA",
                label_asym="A",
                auth_asym="A",
                auth_seq="300",
                label_seq="300",
                x=0.40 + translate,
            ),
        )
    )
    if relevant_altloc_b:
        rows.append(
            _row(
                group="ATOM",
                atom_id="ALA_CLOSE",
                symbol="C",
                component="ALA",
                label_asym="A",
                auth_asym="A",
                auth_seq="300",
                label_seq="300",
                x=0.35 + translate,
                altloc="B",
            )
        )
    rows.append(
        _row(
            group="ATOM",
            atom_id="FAR",
            symbol="C",
            component="GLY",
            label_asym="A",
            auth_asym="A",
            auth_seq="999",
            label_seq="999",
            x=30.0 + translate,
        )
    )
    for atom_id, symbol, x in LIGAND_ATOMS:
        if atom_id == omit_ligand_atom:
            continue
        rows.append(
            _row(
                group="HETATM",
                atom_id=atom_id,
                symbol=symbol_overrides.get(atom_id, symbol),
                component="POA",
                label_asym=ligand_asym,
                auth_asym=ligand_asym,
                auth_seq="501",
                x=x + translate,
            )
        )
        if atom_id == "C2" and duplicate_ligand_c2:
            rows.append(
                _row(
                    group="HETATM",
                    atom_id="C2",
                    symbol="C",
                    component="POA",
                    label_asym=ligand_asym,
                    auth_asym=ligand_asym,
                    auth_seq="501",
                    x=x + 0.01 + translate,
                )
            )
    for index, row in enumerate(rows, start=1):
        row["_atom_site.id"] = str(index)
    actual_entry = entry_id or pdb_id
    lines = [
        f"data_{actual_entry}",
        f"_entry.id {actual_entry}",
        "#",
        "loop_",
        *ATOM_SITE_COLUMNS,
    ]
    lines.extend(" ".join(row[column] for column in ATOM_SITE_COLUMNS) for row in rows)
    lines.append("#")
    return gzip.compress(("\n".join(lines) + "\n").encode("utf-8"), mtime=0)


def _records() -> tuple[
    metadata_owner.POASampleLevelEffectiveSupervisionRecordV1,
    metadata_owner.POASampleLevelEffectiveSupervisionRecordV1,
]:
    return _record("4I3U"), _record("4I3V")


def _build(
    task0: int = 0,
    task1: int = 0,
    *,
    records: tuple[
        metadata_owner.POASampleLevelEffectiveSupervisionRecordV1, ...
    ] | None = None,
    payloads: dict[str, bytes] | None = None,
) -> subject.POAExact16RealStructureTensorPreviewV1:
    selected_records = records or _records()
    selected_payloads = payloads or {
        "4I3U": _payload("4I3U"),
        "4I3V": _payload("4I3V", translate=20.0),
    }
    task_values = (task0, task1)
    return subject._assemble_core_v1(
        structure_payloads_by_pdb=selected_payloads,
        records=selected_records,
        canonical_task_ids_by_event={
            record.canonical_event_id: task_values[index]
            for index, record in enumerate(selected_records)
        },
    )


def _assert_error(call: Callable[[], object], reason: str) -> None:
    with pytest.raises(
        subject.POAExact16RealStructureTensorPreviewError,
        match=subject.ERROR_TOKEN + ".*" + reason,
    ):
        call()


def test_private_portable_core_builds_existing_supervision_dataclass() -> None:
    preview = _build()
    assert isinstance(
        preview.supervision, CovapieCurrent11TrainingSupervisionTensorsV1
    )
    assert preview.sample_identities == tuple(
        record.canonical_event_id for record in _records()
    )
    assert preview.model_input_batch["names"] == list(preview.sample_identities)
    assert preview.model_input_batch["receptors"] == ["4I3U", "4I3V"]
    assert preview.model_forward_executed is False
    assert preview.loss_executed is False
    assert preview.training_performed is False
    assert preview.ready_for_training is False


def test_exact10_h_filtering_model_shapes_and_source_local_indices() -> None:
    preview = _build()
    model = preview.model_input_batch
    assert model["num_lig_atoms"].tolist() == [7, 7]
    assert model["num_pocket_nodes"].tolist() == [8, 8]
    assert model["lig_coords"].shape == (14, 3)
    assert model["pocket_coords"].shape == (16, 3)
    assert model["lig_one_hot"].shape == (14, 10)
    assert model["pocket_one_hot"].shape == (16, 10)
    assert model["lig_coords"].dtype == model["pocket_coords"].dtype == torch.float32
    assert model["lig_one_hot"].dtype == model["pocket_one_hot"].dtype == torch.float32
    assert model["lig_one_hot"].argmax(1).tolist() == list(
        subject.EXPECTED_LIGAND_CHANNELS_V1 * 2
    )
    assert model["lig_parser_local_index"].tolist() == list(range(7)) * 2
    assert model["pocket_parser_local_index"].tolist() == list(range(8)) * 2
    # Explicit H was present before both projections but owns no retained row.
    assert len(model["lig_source_row_index"]) == 14
    assert len(model["pocket_source_row_index"]) == 16
    assert preview.ligand_reactive_atom_local_index.tolist() == [1, 1]


def test_role_projection_target_exact6_and_reactive_indices() -> None:
    preview = _build()
    supervision = preview.supervision
    assert supervision.ligand_role_id.tolist() == list(
        subject.EXPECTED_ROLE_ID_MODEL_ORDER_V1 * 2
    )
    assert supervision.ligand_role_valid.all()
    assert preview.ligand_node_offsets == (0, 7, 14)
    assert preview.pocket_node_offsets == (0, 8, 16)
    assert preview.ligand_reactive_atom_flat_index.tolist() == [1, 8]
    assert supervision.target_residue_membership_mask.sum().item() == 12
    assert supervision.target_residue_reactive_atom_mask.sum().item() == 2
    assert supervision.target_residue_reactive_atom_local_index.tolist() == [5, 5]
    assert supervision.target_residue_reactive_atom_flat_index.tolist() == [5, 13]
    pocket_channels = preview.model_input_batch["pocket_one_hot"].argmax(1)
    assert pocket_channels[
        supervision.target_residue_reactive_atom_flat_index
    ].tolist() == [3, 3]


@pytest.mark.parametrize(
    ("task_id", "generated", "fixed"),
    ((0, 2, 5), (1, 3, 4), (2, 6, 1), (3, 4, 3), (4, 7, 0)),
)
def test_all_exact5_masks_include_B3(
    task_id: int, generated: int, fixed: int
) -> None:
    supervision = _build(task_id, task_id).supervision
    generation = supervision.ligand_base_generation_mask.reshape(2, 7)
    fixed_mask = supervision.ligand_base_fixed_mask.reshape(2, 7)
    assert generation.sum(1).tolist() == [generated, generated]
    assert fixed_mask.sum(1).tolist() == [fixed, fixed]
    assert torch.equal(
        supervision.ligand_base_target_mask,
        supervision.ligand_base_generation_mask,
    )
    assert torch.equal(
        supervision.ligand_base_context_mask,
        supervision.ligand_base_fixed_mask,
    )


def test_joint_per_sample_centering_and_distance_translation_invariance() -> None:
    preview = _build()
    model = preview.model_input_batch
    for sample in range(2):
        combined = torch.cat(
            (
                model["lig_coords"][model["lig_mask"] == sample],
                model["pocket_coords"][model["pocket_mask"] == sample],
            )
        )
        assert torch.allclose(combined.mean(0), torch.zeros(3), atol=3e-6)
    assert torch.allclose(
        preview.supervision.observed_complex_pair_distance_angstrom,
        torch.tensor([[1.82], [1.82]], dtype=torch.float32),
        atol=1e-5,
    )
    first = _build(
        records=(_record("4I3U"),),
        payloads={"4I3U": _payload("4I3U")},
    )
    translated = _build(
        records=(_record("4I3U"),),
        payloads={"4I3U": _payload("4I3U", translate=100.0)},
    )
    assert torch.allclose(
        first.supervision.observed_complex_pair_distance_angstrom,
        translated.supervision.observed_complex_pair_distance_angstrom,
        atol=1e-5,
    )


def test_pair_candidate_domain_is_exact42_with_one_positive_per_sample() -> None:
    supervision = _build().supervision
    assert supervision.pair_candidate_offsets.tolist() == [0, 42, 84]
    assert len(supervision.pair_candidate_batch_index) == 84
    assert supervision.pair_candidate_is_positive.sum().item() == 2
    assert supervision.pair_candidate_is_negative.sum().item() == 82
    assert supervision.pair_positive_candidate_valid.tolist() == [True, True]
    assert supervision.pair_negative_count.tolist() == [41, 41]
    positive = supervision.pair_positive_candidate_index
    assert supervision.pair_candidate_ligand_local_index[positive].tolist() == [1, 1]
    assert supervision.pair_candidate_residue_local_index[positive].tolist() == [5, 5]
    assert not supervision.pair_head_candidate_loss_mask.any()
    assert not supervision.pair_contrastive_sample_loss_mask.any()


def test_preview_admission_seed_and_geometry_boundaries_stay_inactive() -> None:
    preview = _build(4, 4)
    supervision = preview.supervision
    assert not supervision.sample_training_admitted.any()
    assert not supervision.ligand_active_diffusion_loss_mask.any()
    assert not supervision.ligand_minimal_seed_or_anchor_mask.any()
    assert not supervision.ligand_minimal_seed_or_anchor_valid.any()
    assert supervision.ligand_anchor_distance_valid.all()
    assert torch.isfinite(supervision.ligand_anchor_distance_angstrom).all()
    assert supervision.observed_complex_pair_distance_valid.all()
    assert torch.isfinite(supervision.observed_complex_pair_distance_angstrom).all()
    assert torch.equal(
        supervision.pre_post_geometry_target_angstrom,
        torch.zeros((2, 2), dtype=torch.float32),
    )
    assert not supervision.pre_post_geometry_component_valid_mask.any()
    assert not supervision.pre_post_geometry_component_loss_mask.any()


def test_G1_and_G2_routing_preserves_excluded_chemistry_positive_structure() -> None:
    preview = _build()
    assert preview.training_use_dispositions == (
        "INCLUDE",
        "EXCLUDE_FROM_TRAINING_ONLY",
    )
    assert preview.human_training_excluded == (False, True)
    assert preview.nongeometry_future_candidate == (True, False)
    assert preview.summary.G1_include_count == 1
    assert preview.summary.G2_training_excluded_positive_count == 1
    assert preview.summary.sample_training_admitted_count == 0
    assert preview.summary.observed_pair_distance_valid_count == 2
    assert preview.summary.PRE_geometry_target_valid_count == 0
    assert preview.summary.POST_geometry_target_valid_count == 0


def test_source_binding_validator_is_exact_and_does_not_weaken_public_constants() -> None:
    payload = _payload("4I3U")
    expected = {"4I3U": (len(payload), hashlib.sha256(payload).hexdigest())}
    bindings = subject._validate_structure_payload_bindings_v1(
        {"4I3U": payload}, expected_bindings=expected
    )
    assert bindings == (
        subject.POARealStructureSourceBindingV1(
            "4I3U", len(payload), hashlib.sha256(payload).hexdigest()
        ),
    )
    _assert_error(
        lambda: subject._validate_structure_payload_bindings_v1(
            {"4I3U": payload},
            expected_bindings={"4I3U": (len(payload), "0" * 64)},
        ),
        "STRUCTURE_PAYLOAD_SOURCE_BINDING_INVALID",
    )
    assert subject.EXPECTED_REAL_STRUCTURE_BINDINGS_V1["4I3U"] == (
        763278,
        "518c56586f11896b1dd080d867a5bf9d231f6c1362db24c436a7ef2cb11c9a28",
    )


@pytest.mark.parametrize(
    ("payload_overrides", "reason"),
    (
        ({"entry_id": "9XYZ"}, "MMCIF_ENTRY_EVENT_PDB_MISMATCH"),
        ({"omit_ligand_atom": "C2"}, "ROLE_ATOM_ID_NOT_EXACTLY_ONE:C2"),
        ({"duplicate_ligand_c2": True}, "DUPLICATE_LABEL_ATOM_ID"),
        ({"omit_target": True}, "TARGET_RESIDUE_NOT_IN_MODEL_BOUND_POCKET"),
        ({"omit_sg": True}, "TARGET_RESIDUE_REACTIVE_ATOM_NOT_EXACTLY_ONE"),
        ({"duplicate_sg": True}, "TARGET_RESIDUE_REACTIVE_ATOM_NOT_EXACTLY_ONE"),
        ({"target_outside_pocket": True}, "TARGET_RESIDUE_NOT_IN_MODEL_BOUND_POCKET"),
        (
            {"ligand_symbol_overrides": {"O2": "Zn"}},
            "LIGAND_EXACT10_SAMPLE_REJECTED",
        ),
        ({"unsupported_pocket_symbol": "Zn"}, "POCKET_EXACT10_SAMPLE_REJECTED"),
        ({"relevant_altloc_b": True}, "CHECKPOINT_POCKET_ALTLOC_SEMANTICS_AMBIGUOUS"),
        (
            {"ligand_symbol_overrides": {"P": "H"}},
            "ROLE_ATOM_MISSING_AFTER_PROJECTION:P",
        ),
    ),
)
def test_structural_fail_closed_mutations(
    payload_overrides: dict[str, object], reason: str
) -> None:
    payloads = {
        "4I3U": _payload("4I3U", **payload_overrides),
        "4I3V": _payload("4I3V", translate=20.0),
    }
    _assert_error(lambda: _build(payloads=payloads), reason)


def test_invalid_task_id_and_sixth_task_fail_closed() -> None:
    for task_id in (-1, 5, True):
        _assert_error(lambda task_id=task_id: _build(task_id, 0), "CANONICAL_TASK_ID_INVALID")


def test_metadata_event_pdb_and_ligand_asym_mismatches_fail_closed() -> None:
    first, second = _records()
    pdb_mismatch = replace(first, pdb_id="4I3V")
    _assert_error(
        lambda: _build(records=(pdb_mismatch, second)),
        "METADATA_RECORD_SEMANTICS_INVALID",
    )
    asym_mismatch = replace(
        first, canonical_event_id=first.canonical_event_id.replace(":I:POA", ":Z:POA")
    )
    _assert_error(
        lambda: _build(records=(asym_mismatch, second)),
        "METADATA_RECORD_SEMANTICS_INVALID",
    )


def test_cross_sample_duplicate_event_fails_closed() -> None:
    first = _record("4I3U")
    _assert_error(
        lambda: subject._assemble_core_v1(
            structure_payloads_by_pdb={"4I3U": _payload("4I3U")},
            records=(first, first),
            canonical_task_ids_by_event={first.canonical_event_id: 0},
        ),
        "CROSS_SAMPLE_DUPLICATE_EVENT",
    )


def test_structure_payload_mapping_missing_and_extra_keys_fail_closed() -> None:
    effective = _full_effective_supervision()
    tasks = {record.canonical_event_id: 0 for record in effective.records}
    _assert_error(
        lambda: subject.assemble_covapie_poa_exact16_real_structure_tensor_preview_v1(
            structure_payloads_by_pdb={"4I3U": b""},
            effective_supervision=effective,
            canonical_task_ids_by_event=tasks,
        ),
        "STRUCTURE_PAYLOAD_MAPPING_KEYS_INVALID",
    )
    _assert_error(
        lambda: subject.assemble_covapie_poa_exact16_real_structure_tensor_preview_v1(
            structure_payloads_by_pdb={
                "4I3U": b"",
                "4I3V": b"",
                "9XYZ": b"",
            },
            effective_supervision=effective,
            canonical_task_ids_by_event=tasks,
        ),
        "STRUCTURE_PAYLOAD_MAPPING_KEYS_INVALID",
    )


def test_public_real_entry_rejects_wrong_exact_source_sha_before_parsing() -> None:
    effective = _full_effective_supervision()
    tasks = {record.canonical_event_id: 0 for record in effective.records}
    _assert_error(
        lambda: subject.assemble_covapie_poa_exact16_real_structure_tensor_preview_v1(
            structure_payloads_by_pdb={"4I3U": b"gzip", "4I3V": b"gzip"},
            effective_supervision=effective,
            canonical_task_ids_by_event=tasks,
        ),
        "STRUCTURE_PAYLOAD_SOURCE_BINDING_INVALID",
    )


def test_centering_and_model_shape_invariant_failure_is_detected() -> None:
    preview = _build()
    model = dict(preview.model_input_batch)
    model["lig_coords"] = model["lig_coords"][:-1]
    broken = replace(preview, model_input_batch=model)
    _assert_error(
        lambda: subject._validate_preview_impl_v1(
            broken, expected_sample_count=2, require_real_exact16=False
        ),
        "TENSOR_SHAPE_DTYPE_OR_DEVICE_INVALID:lig_coords",
    )
    model = dict(preview.model_input_batch)
    model["lig_coords"] = model["lig_coords"].clone()
    model["lig_coords"][0, 0] += 1.0
    broken = replace(preview, model_input_batch=model)
    _assert_error(
        lambda: subject._validate_preview_impl_v1(
            broken, expected_sample_count=2, require_real_exact16=False
        ),
        "PER_SAMPLE_JOINT_CENTERING_INVALID",
    )


def test_pair_positive_not_unique_fails_closed_validation() -> None:
    preview = _build()
    values = {
        field.name: getattr(preview.supervision, field.name)
        for field in subject.fields(CovapieCurrent11TrainingSupervisionTensorsV1)
    }
    values["pair_candidate_is_positive"] = values[
        "pair_candidate_is_positive"
    ].clone()
    values["pair_candidate_is_positive"][0] = True
    broken = replace(
        preview,
        supervision=CovapieCurrent11TrainingSupervisionTensorsV1(**values),
    )
    _assert_error(
        lambda: subject._validate_preview_impl_v1(
            broken, expected_sample_count=2, require_real_exact16=False
        ),
        "PAIR_CANDIDATE_PROJECTION_INVALID:pair_candidate_is_positive",
    )


def test_task_mapping_missing_event_and_extra_event_fail_closed() -> None:
    records = _records()
    payloads = {"4I3U": _payload("4I3U"), "4I3V": _payload("4I3V")}
    _assert_error(
        lambda: subject._assemble_core_v1(
            structure_payloads_by_pdb=payloads,
            records=records,
            canonical_task_ids_by_event={records[0].canonical_event_id: 0},
        ),
        "CANONICAL_TASK_MAPPING_KEYS_INVALID",
    )
    _assert_error(
        lambda: subject._assemble_core_v1(
            structure_payloads_by_pdb=payloads,
            records=records,
            canonical_task_ids_by_event={
                records[0].canonical_event_id: 0,
                records[1].canonical_event_id: 0,
                "extra": 0,
            },
        ),
        "CANONICAL_TASK_MAPPING_KEYS_INVALID",
    )


def test_deterministic_double_build_is_tensor_identical() -> None:
    first, second = _build(3, 3), _build(3, 3)
    assert first.summary == second.summary
    assert first.structure_source_bindings == second.structure_source_bindings
    for name, value in first.model_input_batch.items():
        if isinstance(value, torch.Tensor):
            assert torch.equal(value, second.model_input_batch[name])
        else:
            assert value == second.model_input_batch[name]
    for field in subject.fields(CovapieCurrent11TrainingSupervisionTensorsV1):
        assert torch.equal(
            getattr(first.supervision, field.name),
            getattr(second.supervision, field.name),
        )


def test_public_validator_rejects_portable_small_N_as_not_real_exact16() -> None:
    _assert_error(
        lambda: subject.validate_covapie_poa_exact16_real_structure_tensor_preview_v1(
            _build()
        ),
        "PREVIEW_SAMPLE_METADATA_INVALID",
    )


def test_import_has_no_output_or_filesystem_side_effect(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = os.pathsep.join((str(ROOT), str(ROOT / "src")))
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import covalent_ext."
            "covapie_poa_exact16_real_structure_tensor_preview_v1",
        ],
        cwd=tmp_path,
        env=env,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 0
    assert result.stdout == result.stderr == ""
    assert list(tmp_path.iterdir()) == []
