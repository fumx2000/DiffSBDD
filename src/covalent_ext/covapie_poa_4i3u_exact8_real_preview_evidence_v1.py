#!/usr/bin/env python3
"""Build source-bound, inactive real-structure evidence for POA 4I3U exact8.

This successor deliberately does not create admission, invoke a model, activate
losses, or adapt inactive PRE/POST geometry placeholders.  Its public assembly
entry fixes the real source identities, CPU device, exact8 population, and Task
A.  The published exact16 public entry is not called; only its pinned private
structural core and validator implementation are reused.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, fields
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Mapping, NoReturn, Sequence

import torch

from covalent_ext import (
    covapie_completed_human_decision_reconciliation_v1 as reconciliation,
)
from covalent_ext import (
    covapie_direct_attachment_optional_linker_runtime_v1 as role_owner,
)
from covalent_ext import (
    covapie_ffq_real_structure_microbatch_alignment_v1 as structure_owner,
)
from covalent_ext import (
    covapie_mmcif_ligand_atom_identity_extractor_v1 as ligand_owner,
)
from covalent_ext import (
    covapie_poa_exact16_real_structure_tensor_preview_v1 as preview_owner,
)
from covalent_ext import (
    covapie_poa_sample_level_effective_supervision_v1 as metadata_owner,
)
from covalent_ext import (
    covapie_tensor_label_and_loss_mask_contract_design_v1 as pair_owner,
)
from covalent_ext import (
    covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1
    as feature_owner,
)


__all__ = (
    "POA4I3UExact8RealPreviewEvidenceError",
    "assemble_covapie_poa_4i3u_exact8_real_preview_evidence_v1",
    "validate_covapie_poa_4i3u_exact8_real_preview_evidence_v1",
    "build_covapie_poa_4i3u_exact8_real_preview_evidence_payload_v1",
    "generate_covapie_poa_4i3u_exact8_real_preview_evidence_v1",
)


TASK_ID = "implement_covapie_poa_4i3u_exact8_real_preview_evidence_v1"
SCHEMA_VERSION = "covapie_poa_4i3u_exact8_real_preview_evidence_v1"
ERROR_TOKEN = "COVAPIE_POA_4I3U_EXACT8_REAL_PREVIEW_EVIDENCE_V1_ERROR"
BASELINE_COMMIT = "58abc4f53a3f89e8bb40d17eb827acbec1f7fadc"
REPORT_NAME = "poa_4i3u_exact8_real_preview_evidence_v1.json"

FORMAL_DECISION_STATE_RELATIVE = Path(
    "manual-review-aids/cumulative1000-high-yield-calibration-v1/"
    "POA_COVAPIE_BULK_REVIEW_UNIT_6A4D564E712634EB/"
    "formal-human-decision-v1/poa_formal_human_decision_v1.json"
)
FORMAL_DECISION_BYTE_COUNT = 15675
FORMAL_DECISION_SHA256 = (
    "263eec2e33a7b50001f6c058959b9218601fc7fb122dc97e937b517f98c90ba8"
)
STRUCTURE_STATE_RELATIVE = Path(
    "bulk-model-usable-auto-admission-scaleup-v1/ranks-0501-1000/"
    "attempt-001/cache/rcsb/structures/4I3U.cif.gz"
)
STRUCTURE_BYTE_COUNT = 763278
STRUCTURE_SHA256 = (
    "518c56586f11896b1dd080d867a5bf9d231f6c1362db24c436a7ef2cb11c9a28"
)
EXPECTED_STRUCTURE_BINDINGS_V1 = {
    "4I3U": (STRUCTURE_BYTE_COUNT, STRUCTURE_SHA256)
}

EXPECTED_EVENT_IDS_V1 = tuple(
    "COVAPIE_CYS_SG_EVENT_V1:4I3U:"
    f"{protein_chain}:CYS:291-:SG:{ligand_asym}:POA:C2"
    for protein_chain, ligand_asym in zip("ABCDEFGH", "IJKLMNOP")
)
EXPECTED_EXCLUDED_EVENT_IDS_V1 = tuple(
    "COVAPIE_CYS_SG_EVENT_V1:4I3V:"
    f"{protein_chain}:CYS:291-:SG:{ligand_asym}:POA:C2"
    for protein_chain, ligand_asym in zip(
        "ABCDEFGH", ("J", "L", "N", "P", "R", "T", "V", "W")
    )
)
EXPECTED_FULL_EVENT_IDS_V1 = EXPECTED_EVENT_IDS_V1 + EXPECTED_EXCLUDED_EVENT_IDS_V1

CANONICAL_TASKS_V1 = (
    (0, "warhead_only", "A", 2, 5),
    (1, "linker_plus_warhead", "B", 3, 4),
    (2, "scaffold_plus_warhead", "B2", 6, 1),
    (3, "scaffold_only", "B3", 4, 3),
    (4, "scaffold_plus_linker_plus_warhead", "C", 7, 0),
)

# Directly used owners are bound by both full-file SHA256 and Git blob SHA1.
# Transitive source contracts remain the responsibility of those frozen owners.
SOURCE_SPECS_V1 = (
    (
        "exact16_structural_core_owner",
        "src/covalent_ext/covapie_poa_exact16_real_structure_tensor_preview_v1.py",
        61559,
        "91b26dd9e0aae8cbda34c769cf98d766910b9b497f5ca1133105f8858072f989",
        "1048d229f119ec4ae9f4cafd5253a060702a948c",
    ),
    (
        "sample_metadata_owner",
        "src/covalent_ext/covapie_poa_sample_level_effective_supervision_v1.py",
        42406,
        "f4656f414a5d31d5e967b39885dd5d89e9bf205135dbd29b3285e0d1e856367f",
        "747f3e830a63bd208914af64ac08cb9b4ed042c0",
    ),
    (
        "formal_decision_reconciliation_owner",
        "src/covalent_ext/covapie_completed_human_decision_reconciliation_v1.py",
        35925,
        "2fcdf85f4753cedf6fe803ae1640fbf65484cdad2bc67732b5d9fdc24b8c3548",
        "0110c3783fafe2c2b673b08ab4ca2d47f45c6d00",
    ),
    (
        "formal_split_owner",
        "src/covalent_ext/covapie_poa_full_component_formal_split_authority_v1.py",
        83848,
        "fa466fc335b664bec5063711a6da9576b0781594f9818f7f34be9f6090d491a8",
        "26cbc15ad3b52708c312b05bfa4a0ffbbc613056",
    ),
    (
        "ffq_structure_and_pocket_owner",
        "src/covalent_ext/covapie_ffq_real_structure_microbatch_alignment_v1.py",
        42076,
        "61a9fa76ce7c84116c0a37e3be6e2a44f429c5dd9812747a1e3eafce253aea0e",
        "36e744bb21bd96447a2e35a2b43ee9abadaf0a32",
    ),
    (
        "ligand_identity_extractor_owner",
        "src/covalent_ext/covapie_mmcif_ligand_atom_identity_extractor_v1.py",
        6686,
        "498263b01b8f74a39b6090f9b8a3e5a0ac01954ff6c6f36c23a16058bb145bcd",
        "c62e9c3405c0405c9f793810578794018e5047b7",
    ),
    (
        "pair_domain_owner",
        "src/covalent_ext/covapie_tensor_label_and_loss_mask_contract_design_v1.py",
        150767,
        "3d2d03cda56dfb4a54370444f255f9bb0ab433aaeb837901e769098272ff51ac",
        "05a37f5507abe9c7ac935600aeee8d2d47cc068e",
    ),
    (
        "role_mask_owner",
        "src/covalent_ext/covapie_direct_attachment_optional_linker_runtime_v1.py",
        37255,
        "434285a43fa0158e62d40f48ed95d137f5fd68ea9b00101cc20674025849c535",
        "bf57bc8c6142efb782c916a85a017bb8ebf07ab8",
    ),
    (
        "exact10_feature_owner",
        "src/covalent_ext/covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1.py",
        64861,
        "1d80862e7c4fa3215ac3f307a45ce3bc8f1e0d4613728133a0ea3118df2df241",
        "61c057af51fcb0bc9dd4ab83f917e1eece2be799",
    ),
    (
        "supervision_tensor_schema_owner",
        "src/covalent_ext/covapie_current11_training_tensorizer_v1.py",
        39144,
        "9fdc3f7f101fab5e5e5452e3d8e9f9b0b1e6e5fa8254a261f36310a1dfd0b606",
        "567f3aacd8480a743353583753e657230f80f9a5",
    ),
)


class POA4I3UExact8RealPreviewEvidenceError(ValueError):
    """Raised unless every source, population, and structural invariant holds."""


def _fail(reason: str) -> NoReturn:
    raise POA4I3UExact8RealPreviewEvidenceError(f"{ERROR_TOKEN}:{reason}")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _git_blob_sha1(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()  # noqa: S324 - Git identity


def _source_bindings(repository_root: Path | str) -> tuple[dict[str, Any], ...]:
    root = Path(repository_root)
    if not root.is_dir():
        _fail("REPOSITORY_ROOT_DIRECTORY_REQUIRED")
    bindings: list[dict[str, Any]] = []
    for role, relative, expected_bytes, expected_sha, expected_blob in SOURCE_SPECS_V1:
        path = root / relative
        if not path.is_file() or path.is_symlink():
            _fail("PINNED_SOURCE_REGULAR_FILE_REQUIRED:" + relative)
        payload = path.read_bytes()
        if (
            len(payload) != expected_bytes
            or _sha256(payload) != expected_sha
            or _git_blob_sha1(payload) != expected_blob
        ):
            _fail("PINNED_SOURCE_IDENTITY_INVALID:" + relative)
        bindings.append(
            {
                "role": role,
                "path": relative,
                "path_namespace": "repository_root_relative",
                "byte_count": expected_bytes,
                "sha256": expected_sha,
                "git_blob_sha1": expected_blob,
            }
        )
    return tuple(bindings)


def _formal_and_metadata_gate(
    formal_decision_payload: object,
    effective_supervision: object,
) -> tuple[metadata_owner.POASampleLevelEffectiveSupervisionRecordV1, ...]:
    if type(formal_decision_payload) is not bytes:
        _fail("FORMAL_DECISION_EXACT_BYTES_REQUIRED")
    if (
        len(formal_decision_payload) != FORMAL_DECISION_BYTE_COUNT
        or _sha256(formal_decision_payload) != FORMAL_DECISION_SHA256
    ):
        _fail("FORMAL_DECISION_SOURCE_BINDING_INVALID")
    try:
        normalized = reconciliation.project_poa_formal_decision_v1(
            formal_decision_payload
        )
        metadata_owner.validate_covapie_poa_sample_level_effective_supervision_v1(
            effective_supervision
        )
    except Exception as error:
        raise POA4I3UExact8RealPreviewEvidenceError(
            f"{ERROR_TOKEN}:FORMAL_METADATA_OWNER_REJECTED:"
            f"{type(error).__name__}:{error}"
        ) from error
    if type(effective_supervision) is not metadata_owner.POASampleLevelEffectiveSupervisionResultV1:
        _fail("FORMAL_METADATA_RESULT_TYPE_INVALID")
    records = effective_supervision.records
    provenance = effective_supervision.source_provenance
    normalized_ids = tuple(fact.canonical_event_id for fact in normalized.facts)
    if (
        tuple(record.canonical_event_id for record in records)
        != EXPECTED_FULL_EVENT_IDS_V1
        or set(normalized_ids) != set(EXPECTED_FULL_EVENT_IDS_V1)
        or provenance.formal_decision_byte_count != FORMAL_DECISION_BYTE_COUNT
        or provenance.formal_decision_sha256 != FORMAL_DECISION_SHA256
        or provenance.formal_decision_schema
        != reconciliation.POA_FORMAL_DECISION_SCHEMA
        or provenance.review_unit_id != reconciliation.POA_REVIEW_UNIT_ID
        or provenance.formal_decision_path_namespace != "repository_parent_relative"
    ):
        _fail("FORMAL_METADATA_SOURCE_OR_EXACT16_INVENTORY_INVALID")
    selected = records[:8]
    excluded = records[8:]
    if (
        tuple(record.canonical_event_id for record in selected)
        != EXPECTED_EVENT_IDS_V1
        or any(
            record.pdb_id != "4I3U"
            or record.training_use_disposition != "INCLUDE"
            or record.human_training_excluded is not False
            or record.nongeometry_future_candidate is not True
            or record.training_admitted is not False
            or record.pair_candidate_domain_materialized is not False
            for record in selected
        )
        or tuple(record.canonical_event_id for record in excluded)
        != EXPECTED_EXCLUDED_EVENT_IDS_V1
        or any(
            record.pdb_id != "4I3V"
            or record.training_use_disposition != "EXCLUDE_FROM_TRAINING_ONLY"
            or record.human_training_excluded is not True
            or record.training_admitted is not False
            for record in excluded
        )
    ):
        _fail("FORMAL_4I3U_INCLUDE_EXACT8_POPULATION_INVALID")
    return selected


def _structure_gate(
    structure_payloads_by_pdb: object,
) -> dict[str, bytes]:
    if not isinstance(structure_payloads_by_pdb, Mapping):
        _fail("STRUCTURE_PAYLOAD_MAPPING_REQUIRED")
    if tuple(structure_payloads_by_pdb) != ("4I3U",):
        _fail("STRUCTURE_PAYLOAD_MAPPING_MUST_BE_ONLY_4I3U")
    payload = structure_payloads_by_pdb["4I3U"]
    if type(payload) is not bytes:
        _fail("STRUCTURE_PAYLOAD_EXACT_BYTES_REQUIRED")
    if len(payload) != STRUCTURE_BYTE_COUNT or _sha256(payload) != STRUCTURE_SHA256:
        _fail("STRUCTURE_PAYLOAD_SOURCE_BINDING_INVALID:4I3U")
    return {"4I3U": payload}


def _preview_population_gate(
    preview: object,
) -> preview_owner.POAExact16RealStructureTensorPreviewV1:
    try:
        preview_owner._validate_preview_impl_v1(
            preview,
            expected_sample_count=8,
            require_real_exact16=False,
        )
    except Exception as error:
        raise POA4I3UExact8RealPreviewEvidenceError(
            f"{ERROR_TOKEN}:PINNED_SHARED_VALIDATOR_REJECTED:"
            f"{type(error).__name__}:{error}"
        ) from error
    if type(preview) is not preview_owner.POAExact16RealStructureTensorPreviewV1:
        _fail("PREVIEW_TYPE_INVALID")
    expected_binding = (
        preview_owner.POARealStructureSourceBindingV1(
            "4I3U", STRUCTURE_BYTE_COUNT, STRUCTURE_SHA256
        ),
    )
    supervision = preview.supervision
    if (
        preview.sample_identities != EXPECTED_EVENT_IDS_V1
        or preview.structure_source_bindings != expected_binding
        or preview.canonical_task_ids != (0,) * 8
        or preview.training_use_dispositions != ("INCLUDE",) * 8
        or preview.human_training_excluded != (False,) * 8
        or preview.nongeometry_future_candidate != (True,) * 8
        or preview.model_input_batch["receptors"] != ["4I3U"] * 8
        or preview.model_input_batch["lig_coords"].device.type != "cpu"
        or preview.model_input_batch["pocket_coords"].device.type != "cpu"
        or supervision.sample_training_admitted.any().item()
        or supervision.ligand_active_diffusion_loss_mask.any().item()
        or supervision.pair_head_candidate_loss_mask.any().item()
        or supervision.pair_contrastive_sample_loss_mask.any().item()
        or supervision.pre_post_geometry_target_angstrom.any().item()
        or supervision.pre_post_geometry_component_valid_mask.any().item()
        or supervision.pre_post_geometry_component_loss_mask.any().item()
        or supervision.ligand_minimal_seed_or_anchor_mask.any().item()
        or supervision.ligand_minimal_seed_or_anchor_valid.any().item()
        or preview.summary.sample_count != 8
        or preview.summary.pair_candidate_count != 336
        or preview.summary.pair_positive_count != 8
        or preview.summary.pair_negative_count != 328
        or preview.summary.G1_include_count != 8
        or preview.summary.G2_training_excluded_positive_count != 0
    ):
        _fail("REAL_4I3U_EXACT8_POPULATION_SOURCE_OR_INACTIVE_BOUNDARY_INVALID")
    return preview


def assemble_covapie_poa_4i3u_exact8_real_preview_evidence_v1(
    *,
    repository_root: Path | str,
    formal_decision_payload: bytes,
    effective_supervision: metadata_owner.POASampleLevelEffectiveSupervisionResultV1,
    structure_payloads_by_pdb: Mapping[str, bytes],
) -> preview_owner.POAExact16RealStructureTensorPreviewV1:
    """Build the fixed CPU Task-A preview after all real-source gates pass."""

    try:
        _source_bindings(repository_root)
        records = _formal_and_metadata_gate(
            formal_decision_payload, effective_supervision
        )
        payloads = _structure_gate(structure_payloads_by_pdb)
        task_ids = {record.canonical_event_id: 0 for record in records}
        preview = preview_owner._assemble_core_v1(
            structure_payloads_by_pdb=payloads,
            records=records,
            canonical_task_ids_by_event=task_ids,
            device="cpu",
            expected_structure_bindings=EXPECTED_STRUCTURE_BINDINGS_V1,
            require_real_exact16=False,
        )
        return _preview_population_gate(preview)
    except POA4I3UExact8RealPreviewEvidenceError:
        raise
    except Exception as error:
        raise POA4I3UExact8RealPreviewEvidenceError(
            f"{ERROR_TOKEN}:PUBLIC_ASSEMBLY_REJECTED:{type(error).__name__}:{error}"
        ) from error


def _tensor_descriptor(tensor: torch.Tensor) -> dict[str, Any]:
    if tensor.device.type != "cpu":
        _fail("EVIDENCE_TENSOR_NOT_CPU")
    payload = tensor.detach().contiguous().numpy().tobytes(order="C")
    return {
        "shape": list(tensor.shape),
        "dtype": str(tensor.dtype).removeprefix("torch."),
        "storage_sha256": _sha256(payload),
    }


def _coordinates(row: Mapping[str, Any]) -> list[float]:
    return [
        float(structure_owner._atom_value(row, axis))
        for axis in ("Cartn_x", "Cartn_y", "Cartn_z")
    ]


def _record_for_event(
    effective_supervision: metadata_owner.POASampleLevelEffectiveSupervisionResultV1,
    event_id: str,
) -> metadata_owner.POASampleLevelEffectiveSupervisionRecordV1:
    matches = tuple(
        record
        for record in effective_supervision.records
        if record.canonical_event_id == event_id
    )
    if len(matches) != 1:
        _fail("METADATA_EVENT_NOT_EXACTLY_ONE:" + event_id)
    return matches[0]


def _independent_event_evidence(
    *,
    preview: preview_owner.POAExact16RealStructureTensorPreviewV1,
    effective_supervision: metadata_owner.POASampleLevelEffectiveSupervisionResultV1,
    structure_payload: bytes,
) -> tuple[dict[str, Any], ...]:
    model = preview.model_input_batch
    supervision = preview.supervision
    evidence: list[dict[str, Any]] = []
    for sample, event_id in enumerate(EXPECTED_EVENT_IDS_V1):
        record = _record_for_event(effective_supervision, event_id)
        try:
            identity = structure_owner._event_identity(asdict(record))
            ligand_rows = ligand_owner.extract_covapie_ligand_atom_identity_rows_from_cif_gz_v1(
                cif_gz_payload=structure_payload,
                ligand_component_id=identity["ligand"],
                label_asym_id=identity["ligand_asym"],
                model_num=1,
            )
            atom_rows = structure_owner._parse_and_crosscheck_atom_site(
                structure_payload, expected_pdb_id="4I3U"
            )
            ligand_preprojection = structure_owner._crosscheck_ligand_rows(
                ligand_rows, atom_rows
            )
            ligand_retained, ligand_channels, source_to_projected = (
                structure_owner._projection(ligand_preprojection, domain="ligand")
            )
            scaffold, linker, warhead, role_ids = preview_owner._role_projection_v1(
                record, ligand_rows, source_to_projected
            )
            pocket_preprojection = structure_owner._build_checkpoint_model_input_pocket_v1(
                list(enumerate(atom_rows)), ligand_retained
            )
            pocket_retained, pocket_channels, _ = structure_owner._projection(
                pocket_preprojection, domain="pocket"
            )
            target_members, target_reactive = structure_owner._target_indices(
                pocket_retained, identity
            )
            ligand_reactive = structure_owner._ligand_reactive_index(
                ligand_rows, source_to_projected, record.ligand_reactive_atom_id
            )
            raw_ligand = structure_owner._coordinates(
                ligand_retained, domain="ligand", device=torch.device("cpu")
            )
            raw_pocket = structure_owner._coordinates(
                pocket_retained, domain="pocket", device=torch.device("cpu")
            )
            centered_ligand, centered_pocket = (
                structure_owner._checkpoint_center_coordinates_v1(
                    raw_ligand, raw_pocket
                )
            )
        except Exception as error:
            raise POA4I3UExact8RealPreviewEvidenceError(
                f"{ERROR_TOKEN}:INDEPENDENT_STRUCTURE_OWNER_REJECTED:"
                f"sample={sample}:{type(error).__name__}:{error}"
            ) from error

        lig_start, lig_end = preview.ligand_node_offsets[sample : sample + 2]
        pocket_start, pocket_end = preview.pocket_node_offsets[sample : sample + 2]
        if (
            lig_end - lig_start != 7
            or pocket_end - pocket_start != len(pocket_retained)
            or tuple(model["lig_source_row_index"][lig_start:lig_end].tolist())
            != tuple(source for source, _ in ligand_retained)
            or tuple(model["pocket_source_row_index"][pocket_start:pocket_end].tolist())
            != tuple(source for source, _ in pocket_retained)
            or model["lig_parser_local_index"][lig_start:lig_end].tolist()
            != list(range(7))
            or model["pocket_parser_local_index"][pocket_start:pocket_end].tolist()
            != list(range(len(pocket_retained)))
            or tuple(model["lig_one_hot"][lig_start:lig_end].argmax(1).tolist())
            != ligand_channels
            or tuple(model["pocket_one_hot"][pocket_start:pocket_end].argmax(1).tolist())
            != pocket_channels
            or not torch.equal(model["lig_coords"][lig_start:lig_end], centered_ligand)
            or not torch.equal(
                model["pocket_coords"][pocket_start:pocket_end], centered_pocket
            )
            or tuple(supervision.ligand_role_id[lig_start:lig_end].tolist())
            != role_ids
            or preview.ligand_reactive_atom_local_index[sample].item()
            != ligand_reactive
            or preview.ligand_reactive_atom_flat_index[sample].item()
            != lig_start + ligand_reactive
        ):
            _fail("INDEPENDENT_SOURCE_RETAINED_MODEL_MAPPING_INVALID:" + event_id)

        expected_ligand_one_hot = structure_owner._one_hot(
            ligand_channels, device=torch.device("cpu")
        )
        expected_pocket_one_hot = structure_owner._one_hot(
            pocket_channels, device=torch.device("cpu")
        )
        if not torch.equal(
            model["lig_one_hot"][lig_start:lig_end], expected_ligand_one_hot
        ):
            _fail(
                "INDEPENDENT_LIGAND_SOURCE_ALIGNED_EXACT10_ONE_HOT_INVALID:"
                + event_id
            )
        if not torch.equal(
            model["pocket_one_hot"][pocket_start:pocket_end], expected_pocket_one_hot
        ):
            _fail(
                "INDEPENDENT_POCKET_SOURCE_ALIGNED_EXACT10_ONE_HOT_INVALID:"
                + event_id
            )

        expected_membership = torch.zeros(len(pocket_retained), dtype=torch.bool)
        expected_membership[list(target_members)] = True
        expected_reactive = torch.zeros(len(pocket_retained), dtype=torch.bool)
        expected_reactive[target_reactive] = True
        if (
            not torch.equal(
                supervision.target_residue_membership_mask[
                    pocket_start:pocket_end, 0
                ],
                expected_membership,
            )
            or not torch.equal(
                supervision.target_residue_reactive_atom_mask[
                    pocket_start:pocket_end, 0
                ],
                expected_reactive,
            )
            or supervision.target_residue_reactive_atom_local_index[sample].item()
            != target_reactive
            or supervision.target_residue_reactive_atom_flat_index[sample].item()
            != pocket_start + target_reactive
        ):
            _fail("INDEPENDENT_TARGET_MEMBERSHIP_MAPPING_INVALID:" + event_id)

        translation = raw_ligand[0] - centered_ligand[0]
        # Float32 subtraction can differ by a few ulps across atoms.  Reuse the
        # published preview validator's joint-centering tolerance (1e-4).
        if (
            not torch.allclose(
                raw_ligand - centered_ligand,
                translation.expand_as(raw_ligand),
                atol=1e-4,
                rtol=0,
            )
            or not torch.allclose(
                raw_pocket - centered_pocket,
                translation.expand_as(raw_pocket),
                atol=1e-4,
                rtol=0,
            )
        ):
            _fail("INDEPENDENT_COMMON_TRANSLATION_INVALID:" + event_id)

        pair_spec = pair_owner.PairCandidateSampleSpec(
            batch_sample_index_0based=0,
            retained_ligand_count=7,
            retained_pocket_count=len(pocket_retained),
            target_residue_pocket_local_indices=target_members,
            positive_ligand_local_index=ligand_reactive,
            positive_pocket_local_index=target_reactive,
        )
        independent_pair = pair_owner.build_pair_candidate_records_v1(
            (pair_spec,), (0, 7), (0, len(pocket_retained))
        )
        pair_start = int(supervision.pair_candidate_offsets[sample].item())
        pair_end = int(supervision.pair_candidate_offsets[sample + 1].item())
        if pair_end - pair_start != 42:
            _fail("INDEPENDENT_EXACT42_COUNT_INVALID:" + event_id)
        pair_candidates: list[dict[str, Any]] = []
        for ordinal, independent in enumerate(independent_pair.records):
            global_index = pair_start + ordinal
            ligand_local = independent.pair_candidate_ligand_local_index
            pocket_local = independent.pair_candidate_residue_local_index
            expected_positive = (
                ligand_local == ligand_reactive and pocket_local == target_reactive
            )
            actual = (
                int(supervision.pair_candidate_batch_index[global_index].item()),
                int(supervision.pair_candidate_ligand_local_index[global_index].item()),
                int(supervision.pair_candidate_residue_local_index[global_index].item()),
                int(supervision.pair_candidate_ligand_flat_index[global_index].item()),
                int(supervision.pair_candidate_pocket_flat_index[global_index].item()),
                bool(supervision.pair_candidate_is_positive[global_index].item()),
                bool(supervision.pair_candidate_is_negative[global_index].item()),
            )
            expected = (
                sample,
                ligand_local,
                pocket_local,
                lig_start + ligand_local,
                pocket_start + pocket_local,
                expected_positive,
                not expected_positive,
            )
            if actual != expected:
                _fail("INDEPENDENT_PAIR_ENDPOINT_INVALID:" + event_id)
            ligand_atom = structure_owner._atom_value(
                ligand_retained[ligand_local][1], "label_atom_id"
            )
            pocket_atom = structure_owner._preferred_atom_name(
                pocket_retained[pocket_local][1]
            )
            if expected_positive and (ligand_atom, pocket_atom) != ("C2", "SG"):
                _fail("INDEPENDENT_POSITIVE_NOT_C2_SG:" + event_id)
            pair_candidates.append(
                {
                    "candidate_index_0based": global_index,
                    "event_candidate_ordinal_0based": ordinal,
                    "batch_sample_index_0based": sample,
                    "ligand_local_index_0based": ligand_local,
                    "ligand_flat_index_0based": lig_start + ligand_local,
                    "ligand_atom_id": ligand_atom,
                    "pocket_local_index_0based": pocket_local,
                    "pocket_flat_index_0based": pocket_start + pocket_local,
                    "pocket_atom_id": pocket_atom,
                    "is_positive": expected_positive,
                    "is_negative": not expected_positive,
                }
            )
        if (
            sum(row["is_positive"] for row in pair_candidates) != 1
            or sum(row["is_negative"] for row in pair_candidates) != 41
            or int(supervision.pair_positive_candidate_index[sample].item())
            != next(
                row["candidate_index_0based"]
                for row in pair_candidates
                if row["is_positive"]
            )
            or not bool(supervision.pair_positive_candidate_valid[sample].item())
            or int(supervision.pair_negative_count[sample].item()) != 41
        ):
            _fail("INDEPENDENT_PAIR_LABEL_COUNTS_INVALID:" + event_id)

        projected_to_extractor: dict[int, Mapping[str, object]] = {}
        for row, projected in zip(ligand_rows, source_to_projected):
            if type(projected) is int:
                projected_to_extractor[projected] = row
        ligand_atoms: list[dict[str, Any]] = []
        for local, ((source, row), channel) in enumerate(
            zip(ligand_retained, ligand_channels)
        ):
            identity_row = projected_to_extractor[local]
            ligand_atoms.append(
                {
                    "atom_id": structure_owner._atom_value(row, "label_atom_id"),
                    "atom_site_id": structure_owner._atom_value(row, "id"),
                    "type_symbol": structure_owner._atom_value(row, "type_symbol"),
                    "exact10_channel_index": channel,
                    "source_atom_site_row_index_0based": source,
                    "extractor_parser_local_index_0based": identity_row[
                        "parser_local_index"
                    ],
                    "model_parser_local_index_0based": int(
                        model["lig_parser_local_index"][lig_start + local].item()
                    ),
                    "model_sample_local_index_0based": local,
                    "model_flat_index_0based": lig_start + local,
                    "role_id": role_ids[local],
                    "raw_coordinate_angstrom": _coordinates(row),
                    "centered_coordinate_angstrom": centered_ligand[local].tolist(),
                    "is_positive_ligand_endpoint": local == ligand_reactive,
                }
            )

        pocket_nodes: list[dict[str, Any]] = []
        for local, ((source, row), channel) in enumerate(
            zip(pocket_retained, pocket_channels)
        ):
            pocket_nodes.append(
                {
                    "atom_id": structure_owner._preferred_atom_name(row),
                    "component_id": structure_owner._preferred_component(row),
                    "type_symbol": structure_owner._atom_value(row, "type_symbol"),
                    "exact10_channel_index": channel,
                    "source_atom_site_row_index_0based": source,
                    "model_parser_local_index_0based": local,
                    "model_sample_local_index_0based": local,
                    "model_flat_index_0based": pocket_start + local,
                    "auth_asym_id": structure_owner._atom_value(row, "auth_asym_id"),
                    "auth_seq_id": structure_owner._atom_value(row, "auth_seq_id"),
                    "label_asym_id": structure_owner._atom_value(row, "label_asym_id"),
                    "label_seq_id": structure_owner._atom_value(row, "label_seq_id"),
                    "is_target_cys_member": local in target_members,
                    "is_target_sg": local == target_reactive,
                }
            )
        target_atoms = []
        for local in target_members:
            source, row = pocket_retained[local]
            target_atoms.append(
                {
                    **pocket_nodes[local],
                    "raw_coordinate_angstrom": _coordinates(row),
                    "centered_coordinate_angstrom": centered_pocket[local].tolist(),
                }
            )
        if (
            [row["atom_id"] for row in ligand_atoms]
            != list(preview_owner.EXPECTED_LIGAND_MODEL_ORDER_V1)
            or [row["type_symbol"] for row in ligand_atoms]
            != ["C", "C", "O", "O", "O", "O", "P"]
            or [row["atom_id"] for row in target_atoms]
            != list(preview_owner.EXPECTED_TARGET_CYS_MODEL_ORDER_V1)
            or target_atoms[-1]["atom_id"] != "SG"
            or target_atoms[-1]["auth_seq_id"] != "291"
            or any(row["label_seq_id"] == "291" for row in target_atoms)
        ):
            _fail("INDEPENDENT_ATOM_IDENTITY_OR_RESIDUE_NAMESPACE_INVALID:" + event_id)

        masks = []
        for task_id, semantic_name, alias, generated_count, fixed_count in CANONICAL_TASKS_V1:
            mask = role_owner.build_mask_for_role_profile_v1(
                role_profile=record.runtime_role_profile,
                canonical_task_id=task_id,
                scaffold_atoms=scaffold,
                linker_atoms=linker,
                warhead_atoms=warhead,
                num_ligand_atoms=7,
            )
            if (
                len(mask.masked_atoms) != generated_count
                or len(mask.visible_atoms) != fixed_count
            ):
                _fail("INDEPENDENT_EXACT5_MASK_INVALID:" + event_id)
            masks.append(
                {
                    "canonical_task_id": task_id,
                    "semantic_long_name": semantic_name,
                    "short_alias": alias,
                    "generated_atom_local_indices": list(mask.masked_atoms),
                    "fixed_atom_local_indices": list(mask.visible_atoms),
                    "generated_count": generated_count,
                    "fixed_count": fixed_count,
                    "minimal_seed_authority_created": False,
                }
            )

        evidence.append(
            {
                "sample_ordinal_0based": sample,
                "canonical_event_id": event_id,
                "formal_metadata": {
                    "pdb_id": record.pdb_id,
                    "protein_chain": identity["protein_chain"],
                    "target_residue": "CYS",
                    "target_auth_seq_id": identity["sequence"],
                    "target_insertion_code": identity["insertion"],
                    "target_atom_id": record.target_residue_atom_id,
                    "ligand_label_asym_id": identity["ligand_asym"],
                    "ligand_component_id": record.ligand_component_id,
                    "ligand_reactive_atom_id": record.ligand_reactive_atom_id,
                    "training_use_disposition": record.training_use_disposition,
                    "human_training_excluded": record.human_training_excluded,
                    "training_admitted": record.training_admitted,
                    "source_pair_candidate_domain_materialized": (
                        record.pair_candidate_domain_materialized
                    ),
                },
                "offsets": {
                    "ligand_start": lig_start,
                    "ligand_end": lig_end,
                    "pocket_start": pocket_start,
                    "pocket_end": pocket_end,
                    "pair_start": pair_start,
                    "pair_end": pair_end,
                },
                "ligand": {
                    "source_parser_atom_count_before_heavy_projection": len(ligand_rows),
                    "retained_heavy_atom_count": len(ligand_atoms),
                    "C2_sample_local_index_0based": ligand_reactive,
                    "C2_flat_index_0based": lig_start + ligand_reactive,
                    "atoms": ligand_atoms,
                },
                "pocket": {
                    "checkpoint_compatible_full_pocket_preserved": True,
                    "node_count": len(pocket_nodes),
                    "target_cys_member_count": len(target_members),
                    "target_cys_member_local_indices_0based": list(target_members),
                    "target_SG_local_index_0based": target_reactive,
                    "target_SG_flat_index_0based": pocket_start + target_reactive,
                    "nodes": pocket_nodes,
                    "target_cys_atoms": target_atoms,
                },
                "coordinate_projection": {
                    "algorithm_owner": (
                        "covapie_ffq_real_structure_microbatch_alignment_v1."
                        "_checkpoint_center_coordinates_v1"
                    ),
                    "common_translation_angstrom": translation.tolist(),
                    "source_to_retained_to_model_mapping_pass": True,
                },
                "observed_C2_SG_distance_angstrom": float(
                    supervision.observed_complex_pair_distance_angstrom[sample, 0].item()
                ),
                "pair_domain": {
                    "materialized_in_this_preview_evidence": True,
                    "candidate_order": "ligand_local_outer_target_cys_member_local_inner",
                    "candidate_count": 42,
                    "positive_count": 1,
                    "negative_count": 41,
                    "positive_identity": "POA:C2--CYS:SG",
                    "candidates": pair_candidates,
                },
                "canonical_exact5_structural_masks": masks,
                "inactive_geometry": {
                    "PRE_target_angstrom": 0.0,
                    "POST_target_angstrom": 0.0,
                    "PRE_valid": False,
                    "POST_valid": False,
                    "PRE_loss": False,
                    "POST_loss": False,
                    "consumer_nan_conversion_applied": False,
                    "future_consumer_adapter_requirement": (
                        "convert inactive 0.0 preview placeholders to NaN only in a "
                        "future consumer adapter while preserving valid=false and loss=false"
                    ),
                },
            }
        )
    return tuple(evidence)


def validate_covapie_poa_4i3u_exact8_real_preview_evidence_v1(
    preview: object,
    *,
    repository_root: Path | str,
    formal_decision_payload: bytes,
    effective_supervision: metadata_owner.POASampleLevelEffectiveSupervisionResultV1,
    structure_payloads_by_pdb: Mapping[str, bytes],
) -> bool:
    """Validate exact8 population and source-derived indices independently."""

    try:
        _source_bindings(repository_root)
        _formal_and_metadata_gate(formal_decision_payload, effective_supervision)
        payload = _structure_gate(structure_payloads_by_pdb)["4I3U"]
        checked = _preview_population_gate(preview)
        _independent_event_evidence(
            preview=checked,
            effective_supervision=effective_supervision,
            structure_payload=payload,
        )
        return True
    except POA4I3UExact8RealPreviewEvidenceError:
        raise
    except Exception as error:
        raise POA4I3UExact8RealPreviewEvidenceError(
            f"{ERROR_TOKEN}:PUBLIC_VALIDATION_REJECTED:{type(error).__name__}:{error}"
        ) from error


def build_covapie_poa_4i3u_exact8_real_preview_evidence_payload_v1(
    preview: object,
    *,
    repository_root: Path | str,
    formal_decision_payload: bytes,
    effective_supervision: metadata_owner.POASampleLevelEffectiveSupervisionResultV1,
    structure_payloads_by_pdb: Mapping[str, bytes],
) -> dict[str, Any]:
    """Derive deterministic JSON-ready evidence from one validated preview."""

    source_bindings = _source_bindings(repository_root)
    _formal_and_metadata_gate(formal_decision_payload, effective_supervision)
    structure_payload = _structure_gate(structure_payloads_by_pdb)["4I3U"]
    checked = _preview_population_gate(preview)
    events = _independent_event_evidence(
        preview=checked,
        effective_supervision=effective_supervision,
        structure_payload=structure_payload,
    )
    model_tensor_evidence = {
        name: _tensor_descriptor(value)
        for name, value in sorted(checked.model_input_batch.items())
        if isinstance(value, torch.Tensor)
    }
    supervision_tensor_evidence = {
        field.name: _tensor_descriptor(getattr(checked.supervision, field.name))
        for field in fields(type(checked.supervision))
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "baseline_commit": BASELINE_COMMIT,
        "candidate_status": "UNPUBLISHED_REVIEW_SCRATCH_CANDIDATE",
        "source_bindings": [
            {
                "role": "formal_human_decision",
                "path": FORMAL_DECISION_STATE_RELATIVE.as_posix(),
                "path_namespace": "covapie_state_root_relative",
                "byte_count": FORMAL_DECISION_BYTE_COUNT,
                "sha256": FORMAL_DECISION_SHA256,
                "schema": reconciliation.POA_FORMAL_DECISION_SCHEMA,
                "review_unit_id": reconciliation.POA_REVIEW_UNIT_ID,
            },
            {
                "role": "real_4I3U_gzip_mmcif",
                "path": STRUCTURE_STATE_RELATIVE.as_posix(),
                "path_namespace": "covapie_state_root_relative",
                "byte_count": STRUCTURE_BYTE_COUNT,
                "sha256": STRUCTURE_SHA256,
                "compression": "gzip",
            },
            *source_bindings,
        ],
        "population": {
            "metadata_record_count_read_and_validated": 16,
            "target_population": "FORMAL_4I3U_HUMAN_INCLUDE_EXACT8",
            "target_event_count": 8,
            "target_event_ids_in_order": list(EXPECTED_EVENT_IDS_V1),
            "excluded_4I3V_event_count": 8,
            "excluded_4I3V_structure_read": False,
            "G3H_or_other_structure_read": False,
            "canonical_task_for_main_preview": {
                "canonical_task_id": 0,
                "semantic_long_name": "warhead_only",
                "short_alias": "A",
            },
        },
        "implementation_boundary": {
            "PUBLIC_EXACT16_ENTRY_REUSED": False,
            "PUBLIC_EXACT16_VALIDATOR_CLAIMED_PASSED": False,
            "PINNED_SHARED_STRUCTURAL_CORE_REUSED": True,
            "NEW_EXACT8_SOURCE_AND_POPULATION_GATE_PASS": True,
            "device": "cpu",
            "formal_metadata_builder": (
                "build_covapie_poa_sample_level_effective_supervision_v1"
            ),
            "formal_metadata_validator": (
                "validate_covapie_poa_sample_level_effective_supervision_v1"
            ),
            "old_core_require_real_exact16": False,
            "old_core_flag_interpretation": (
                "old exact16 population requirement disabled only after the new "
                "fixed real-4I3U exact8 source/population gate"
            ),
            "expected_structure_binding_supplied_to_core": True,
            "caller_supplied_expected_sha_allowed": False,
        },
        "summary": {
            **asdict(checked.summary),
            "pair_candidate_count_expected": 336,
            "pair_positive_count_expected": 8,
            "pair_negative_count_expected": 328,
            "full_pocket_not_truncated_to_target_cys": True,
            "canonical_exact5_structural_mask_check_pass": True,
            "canonical_exact5_includes_B3_and_C": True,
            "canonical_mask_count": 5,
        },
        "events": list(events),
        "tensor_descriptors": {
            "model_input": model_tensor_evidence,
            "supervision": supervision_tensor_evidence,
            "descriptor_scope": "shape_dtype_storage_digest_not_tensor_serialization",
        },
        "inactive_and_safety_markers": {
            "sample_training_admitted_count": 0,
            "active_diffusion_loss_count": 0,
            "active_pair_head_candidate_loss_count": 0,
            "active_pair_contrastive_loss_count": 0,
            "active_geometry_loss_count": 0,
            "PRE_geometry_target_representation": 0.0,
            "POST_geometry_target_representation": 0.0,
            "PRE_geometry_valid": False,
            "POST_geometry_valid": False,
            "TASK_C_SEED_AUTHORITY_CREATED": False,
            "NEW_FORMAL_ADMISSION_CREATED": False,
            "CURRENT_TRAIN12_POPULATION_CHANGED": False,
            "TRAINING_CONSUMER_ADAPTER_CREATED": False,
            "NAN_GEOMETRY_CONSUMER_CONVERSION_APPLIED": False,
            "REAL_MODEL_EXECUTED": False,
            "PARAMETER_UPDATE_PERFORMED": False,
            "READY_FOR_TRAINING": False,
            "FEATURE_SEMANTICS_AUDIT_REQUIRED_LATER": True,
            "STEP12D_IS_ONLY_SMOKE_LEGALITY_CHECK": True,
            "COMMIT_PERFORMED": False,
            "PUSH_PERFORMED": False,
            "SCIENTIFIC_NETWORK_ACCESS_PERFORMED": False,
            "SCIENTIFIC_DATA_DOWNLOADED": False,
        },
        "expected_candidate_exact3": [
            "covapie_poa_4i3u_exact8_real_preview_evidence_v1.py",
            "test_covapie_poa_4i3u_exact8_real_preview_evidence_v1.py",
            REPORT_NAME,
        ],
    }


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("ascii")


def _expected_regular_file(path: Path, expected: Path, label: str) -> bytes:
    if path.resolve() != expected.resolve():
        _fail(label + "_PATH_BINDING_INVALID")
    if not path.is_file() or path.is_symlink():
        _fail(label + "_REGULAR_FILE_REQUIRED")
    return path.read_bytes()


def generate_covapie_poa_4i3u_exact8_real_preview_evidence_v1(
    *,
    repository_root: Path | str,
    state_root: Path | str,
    formal_decision_path: Path | str,
    structure_path: Path | str,
) -> bytes:
    """Read each real input once, build twice, and return byte-stable evidence."""

    repo = Path(repository_root)
    state = Path(state_root)
    formal_path = Path(formal_decision_path)
    real_structure_path = Path(structure_path)
    formal_payload = _expected_regular_file(
        formal_path, state / FORMAL_DECISION_STATE_RELATIVE, "FORMAL_DECISION"
    )
    structure_payload = _expected_regular_file(
        real_structure_path, state / STRUCTURE_STATE_RELATIVE, "STRUCTURE_4I3U"
    )
    # The public builder and validator are intentionally used on all 16 records.
    effective = metadata_owner.build_covapie_poa_sample_level_effective_supervision_v1(
        formal_payload
    )
    metadata_owner.validate_covapie_poa_sample_level_effective_supervision_v1(
        effective
    )
    inputs = {"4I3U": structure_payload}
    first = assemble_covapie_poa_4i3u_exact8_real_preview_evidence_v1(
        repository_root=repo,
        formal_decision_payload=formal_payload,
        effective_supervision=effective,
        structure_payloads_by_pdb=inputs,
    )
    second = assemble_covapie_poa_4i3u_exact8_real_preview_evidence_v1(
        repository_root=repo,
        formal_decision_payload=formal_payload,
        effective_supervision=effective,
        structure_payloads_by_pdb=inputs,
    )
    first_payload = build_covapie_poa_4i3u_exact8_real_preview_evidence_payload_v1(
        first,
        repository_root=repo,
        formal_decision_payload=formal_payload,
        effective_supervision=effective,
        structure_payloads_by_pdb=inputs,
    )
    second_payload = build_covapie_poa_4i3u_exact8_real_preview_evidence_payload_v1(
        second,
        repository_root=repo,
        formal_decision_payload=formal_payload,
        effective_supervision=effective,
        structure_payloads_by_pdb=inputs,
    )
    accounting = {
        "formal_decision_file_read_count": 1,
        "structure_file_read_count": 1,
        "formal_metadata_compile_count": 1,
        "formal_metadata_validator_invocation_count": 6,
        "formal_decision_projection_count": 5,
        "real_preview_build_count": 2,
        "preview_core_event_processing_count_per_build": 8,
        "preview_core_event_processing_count_across_two_builds": 16,
        "independent_evidence_event_processing_count_across_two_payloads": 16,
        "total_structure_event_processing_operations": 32,
        "unique_target_event_count": 8,
        "two_builds_are_not_sixteen_distinct_events": True,
        "deterministic_real_double_build_pass": True,
    }
    first_payload["execution_accounting"] = accounting
    second_payload["execution_accounting"] = accounting
    first_bytes = _canonical_json_bytes(first_payload)
    second_bytes = _canonical_json_bytes(second_payload)
    if first_bytes != second_bytes:
        _fail("DETERMINISTIC_REAL_DOUBLE_BUILD_BYTE_MISMATCH")
    return first_bytes


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--formal-decision-path", type=Path, required=True)
    parser.add_argument("--structure-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    payload = generate_covapie_poa_4i3u_exact8_real_preview_evidence_v1(
        repository_root=args.repository_root,
        state_root=args.state_root,
        formal_decision_path=args.formal_decision_path,
        structure_path=args.structure_path,
    )
    if args.output.name != REPORT_NAME:
        _fail("OUTPUT_REPORT_NAME_INVALID")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        if args.output.read_bytes() != payload:
            _fail("EXISTING_OUTPUT_DIFFERS_REFUSE_OVERWRITE")
    else:
        args.output.write_bytes(payload)
    print("REAL_4I3U_EXACT8_PREVIEW_EXECUTED=true")
    print("REAL_STRUCTURE_BYTES_SHA_VERIFIED=true")
    print("FORMAL_METADATA_AND_EXACT8_BINDING_PASS=true")
    print("EXACT10_SOURCE_LOCAL_FLAT_INDEX_EVIDENCE_PASS=true")
    print("CHECKPOINT_COMPATIBLE_POCKET_SCOPE_PRESERVED=true")
    print("EXACT42_PAIR_DOMAIN_PER_EVENT_PASS=true")
    print("PAIR_TOTAL_POSITIVE_NEGATIVE_COUNTS=336/8/328")
    print("CANONICAL_EXACT5_STRUCTURAL_MASK_CHECK_PASS=true")
    print("PREVIEW_GEOMETRY_ZERO_PLACEHOLDER_PRESERVED=true")
    print("DETERMINISTIC_REAL_DOUBLE_BUILD_PASS=true")
    print(f"REPORT_BYTES={len(payload)}")
    print(f"REPORT_SHA256={_sha256(payload)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
