from __future__ import annotations

import copy
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest
import torch

from covalent_ext import (
    covapie_ffq_direct_profile_role_mask_tensorizer_v1 as subject,
)
from covalent_ext import (
    covapie_ffq_project_level_authority_ingestion_and_effective_supervision_successor_v1
    as ffq_successor,
)
from covalent_ext import (
    covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1
    as feature_policy,
)


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_ATOM_IDS = ("C1", "C2", "C3", "O1", "O2", "O3", "O4", "P1")
PERMUTED_ATOM_IDS = ("O3", "C2", "P1", "O1", "C1", "O4", "C3", "O2")


def _record(pdb_id: str = "3VCY") -> dict[str, Any]:
    event_id = next(
        event_id
        for event_id in ffq_successor._CANONICAL_EVENT_IDS
        if f":{pdb_id}:" in event_id
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


def _symbol(atom_id: str) -> str:
    return atom_id[0]


def _rows(atom_ids: tuple[str, ...] = CANONICAL_ATOM_IDS) -> list[dict[str, Any]]:
    return [
        {
            "atom_id": atom_id,
            "type_symbol": _symbol(atom_id),
            "parser_local_index": index,
        }
        for index, atom_id in enumerate(atom_ids)
    ]


def _tensorize(
    task_id: int,
    *,
    record: dict[str, Any] | None = None,
    rows: list[dict[str, Any]] | None = None,
) -> subject.FFQDirectProfileRoleMaskTensorsV1:
    return subject.tensorize_covapie_ffq_direct_profile_role_masks_v1(
        effective_supervision_record=_record() if record is None else record,
        ligand_atom_rows=_rows() if rows is None else rows,
        canonical_task_id=task_id,
    )


def _flat(tensor: torch.Tensor) -> list[bool]:
    return tensor.squeeze(1).tolist()


def test_task_A_canonical_parser_order_builds_exact_roles_and_masks() -> None:
    result = _tensorize(0)

    assert result.canonical_task_id == 0
    assert result.task_applicable is True
    assert result.scaffold_parser_local_indices == (4, 5, 6, 7)
    assert result.linker_parser_local_indices == ()
    assert result.warhead_parser_local_indices == (0, 1, 2, 3)
    assert result.ligand_role_id.dtype == torch.long
    assert result.ligand_role_id.tolist() == [2, 2, 2, 2, 0, 0, 0, 0]
    assert result.ligand_role_valid.dtype == torch.bool
    assert result.ligand_role_valid.tolist() == [True] * 8
    assert result.ligand_base_generation_mask.shape == (8, 1)
    assert _flat(result.ligand_base_generation_mask) == [True] * 4 + [False] * 4
    assert _flat(result.ligand_base_fixed_mask) == [False] * 4 + [True] * 4
    assert torch.equal(
        result.ligand_base_generation_mask,
        result.ligand_base_target_mask,
    )
    assert torch.equal(
        result.ligand_base_fixed_mask,
        result.ligand_base_context_mask,
    )


def test_task_A_maps_atom_identity_not_row_position_or_canonical_role_order() -> None:
    rows = list(reversed(_rows(PERMUTED_ATOM_IDS)))
    result = _tensorize(0, rows=rows)

    assert result.scaffold_parser_local_indices == (7, 0, 5, 2)
    assert result.warhead_parser_local_indices == (4, 1, 6, 3)
    assert result.ligand_role_id.tolist() == [0, 2, 0, 2, 2, 0, 2, 0]
    assert _flat(result.ligand_base_generation_mask) == [
        False,
        True,
        False,
        True,
        True,
        False,
        True,
        False,
    ]


def test_explicit_hydrogen_is_excluded_before_retained_parser_local_mapping() -> None:
    atom_ids = ("C1", "C2", "H1", "C3", "O1", "O2", "O3", "O4", "P1")
    rows = _rows(atom_ids)
    rows[2]["type_symbol"] = "H"
    result = _tensorize(0, rows=rows)

    assert result.ligand_role_id.tolist() == [2, 2, 2, 2, 0, 0, 0, 0]
    assert result.warhead_parser_local_indices == (0, 1, 2, 3)
    assert result.scaffold_parser_local_indices == (4, 5, 6, 7)


def test_task_B3_generates_scaffold_and_fixes_warhead() -> None:
    result = _tensorize(3)

    assert _flat(result.ligand_base_generation_mask) == [False] * 4 + [True] * 4
    assert _flat(result.ligand_base_fixed_mask) == [True] * 4 + [False] * 4


def test_task_C_generates_whole_ligand_without_inventing_seed_supervision() -> None:
    result = _tensorize(4)

    assert _flat(result.ligand_base_generation_mask) == [True] * 8
    assert _flat(result.ligand_base_fixed_mask) == [False] * 8
    assert result.task_C_role_mask_supported is True
    assert result.task_C_minimal_seed_supervision_available is False
    assert result.full_task_C_training_supervision_ready is False
    assert result.ffq_direct_profile_unknown_atom_policy_enforced is True
    assert not hasattr(result, "ligand_minimal_seed_or_anchor_mask")


@pytest.mark.parametrize("task_id", (1, 2))
def test_tasks_B_and_B2_fail_closed_as_not_applicable(task_id: int) -> None:
    with pytest.raises(
        subject.FFQDirectProfileRoleMaskTensorizerError,
        match="TASK_NOT_APPLICABLE",
    ):
        _tensorize(task_id)


def test_missing_ffq_atom_identity_fails_closed() -> None:
    rows = _rows(CANONICAL_ATOM_IDS[:-1])
    with pytest.raises(
        subject.FFQDirectProfileRoleMaskTensorizerError,
        match="FFQ_EXACT8_HEAVY_ATOM_IDENTITY_INVALID",
    ):
        _tensorize(0, rows=rows)


def test_duplicate_ffq_atom_identity_fails_closed() -> None:
    rows = _rows()
    rows[-1]["atom_id"] = "C1"
    with pytest.raises(
        subject.FFQDirectProfileRoleMaskTensorizerError,
        match="DUPLICATE_ATOM_ID",
    ):
        _tensorize(0, rows=rows)


def test_duplicate_parser_local_index_fails_closed() -> None:
    rows = _rows()
    rows[-1]["parser_local_index"] = 0
    with pytest.raises(
        subject.FFQDirectProfileRoleMaskTensorizerError,
        match="DUPLICATE_PARSER_LOCAL_INDEX",
    ):
        _tensorize(0, rows=rows)


def test_noncontiguous_parser_local_indices_fail_closed() -> None:
    rows = _rows()
    rows[-1]["parser_local_index"] = 8
    with pytest.raises(
        subject.FFQDirectProfileRoleMaskTensorizerError,
        match="PARSER_LOCAL_INDICES_NOT_CONTIGUOUS_ZERO_BASED",
    ):
        _tensorize(0, rows=rows)


def test_unsupported_nonhydrogen_symbol_rejects_complete_sample() -> None:
    rows = _rows()
    rows[0]["type_symbol"] = "Si"
    with pytest.raises(
        subject.FFQDirectProfileRoleMaskTensorizerError,
        match="UNKNOWN_ATOM_POLICY_REJECTED_SAMPLE:0:unsupported_nonhydrogen",
    ):
        _tensorize(0, rows=rows)


@pytest.mark.parametrize("invalid_symbol", (None, "", " C"))
def test_missing_or_invalid_type_symbol_rejects_complete_sample(
    invalid_symbol: object,
) -> None:
    rows = _rows()
    rows[0]["type_symbol"] = invalid_symbol
    with pytest.raises(
        subject.FFQDirectProfileRoleMaskTensorizerError,
        match="UNKNOWN_ATOM_POLICY_REJECTED_SAMPLE:0:missing_or_invalid",
    ):
        _tensorize(0, rows=rows)


def test_published_exact10_projection_primitive_is_the_only_feature_policy_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[tuple[object, ...]] = []
    real_project = feature_policy.project_type_symbols_to_checkpoint_heavy_v1

    def recording_projection(symbols: tuple[object, ...]) -> Any:
        observed.append(symbols)
        projection = real_project(symbols)
        assert projection.outcome == "passed"
        assert projection.keep_mask == (True,) * 8
        assert projection.checkpoint_channel_indices == (0, 0, 0, 2, 2, 2, 2, 7)
        assert projection.reasons == ()
        return projection

    monkeypatch.setattr(
        subject.feature_policy,
        "project_type_symbols_to_checkpoint_heavy_v1",
        recording_projection,
    )
    result = _tensorize(0)

    assert observed == [("C", "C", "C", "O", "O", "O", "O", "P")]
    assert result.ligand_role_id.shape == (8,)
    assert not hasattr(result, "ligand_one_hot")


@pytest.mark.parametrize(
    ("field", "replacement", "error"),
    (
        (
            "reaction_family_authority_id",
            "COVAPIE_CYS_SG_REACTION_FAMILY_DRIFT",
            "REACTION_FAMILY_AUTHORITY_ID_DRIFT",
        ),
        (
            "warhead_rule_authority_id",
            "COVAPIE_CYS_SG_WARHEAD_RULE_DRIFT",
            "WARHEAD_RULE_AUTHORITY_ID_DRIFT",
        ),
    ),
)
def test_published_chemistry_authority_id_drift_fails_closed(
    field: str, replacement: str, error: str
) -> None:
    record = _record()
    record[field] = replacement
    with pytest.raises(subject.FFQDirectProfileRoleMaskTensorizerError, match=error):
        _tensorize(0, record=record)


@pytest.mark.parametrize(
    ("field", "replacement", "error"),
    (
        ("reviewed_scaffold_atom_ids", ["O2", "O3", "O4"], "SCAFFOLD_ATOM_INVENTORY_DRIFT"),
        ("reviewed_linker_atom_ids", ["C2"], "LINKER_ATOM_INVENTORY_DRIFT"),
        ("reviewed_warhead_atom_ids", ["C1", "C2", "C3"], "WARHEAD_ATOM_INVENTORY_DRIFT"),
    ),
)
def test_published_role_atom_inventory_drift_fails_closed(
    field: str, replacement: list[str], error: str
) -> None:
    record = _record()
    record[field] = replacement
    with pytest.raises(subject.FFQDirectProfileRoleMaskTensorizerError, match=error):
        _tensorize(0, record=record)


def test_3vcy_include_semantics_do_not_create_training_admission() -> None:
    record = _record("3VCY")
    before = copy.deepcopy(record)
    result = _tensorize(0, record=record)

    assert record == before
    assert record["formal_event_training_use_decision"] == "INCLUDE"
    assert record["training_admitted"] is False
    assert record["training_materialization_allowed_now"] is False
    assert record["current_runtime_model_usable"] is False
    assert not hasattr(result, "sample_training_admitted")


def test_4r7u_human_training_exclusion_is_preserved() -> None:
    record = _record("4R7U")
    before = copy.deepcopy(record)
    result = _tensorize(3, record=record)

    assert record == before
    assert record["formal_event_training_use_decision"] == "EXCLUDE_FROM_TRAINING_ONLY"
    assert record["human_training_exclusion_preserved"] is True
    assert record["training_admitted"] is False
    assert record["training_materialization_allowed_now"] is False
    assert record["current_runtime_model_usable"] is False
    assert not hasattr(result, "sample_training_admitted")


def test_double_call_is_deterministic_for_tensors_indices_and_metadata() -> None:
    first = _tensorize(4, rows=list(reversed(_rows(PERMUTED_ATOM_IDS))))
    second = _tensorize(4, rows=list(reversed(_rows(PERMUTED_ATOM_IDS))))

    for field in (
        "ligand_role_id",
        "ligand_role_valid",
        "ligand_base_generation_mask",
        "ligand_base_fixed_mask",
        "ligand_base_target_mask",
        "ligand_base_context_mask",
    ):
        assert torch.equal(getattr(first, field), getattr(second, field))
    for field in (
        "canonical_event_id",
        "canonical_task_id",
        "scaffold_parser_local_indices",
        "linker_parser_local_indices",
        "warhead_parser_local_indices",
        "task_applicable",
        "task_C_role_mask_supported",
        "task_C_minimal_seed_supervision_available",
        "full_task_C_training_supervision_ready",
        "ffq_direct_profile_unknown_atom_policy_enforced",
    ):
        assert getattr(first, field) == getattr(second, field)


def test_production_import_has_no_output() -> None:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = str(ROOT / "src")
    completed = subprocess.run(
        (
            sys.executable,
            "-c",
            "import covalent_ext.covapie_ffq_direct_profile_role_mask_tensorizer_v1",
        ),
        cwd=ROOT,
        env=environment,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert completed.returncode == 0
    assert completed.stdout == ""
    assert completed.stderr == ""
