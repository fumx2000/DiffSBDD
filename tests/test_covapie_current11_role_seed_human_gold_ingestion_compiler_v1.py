from __future__ import annotations

import copy
import csv
import hashlib
import inspect
import io
import os
import pickle
import stat
import subprocess
import sys
from pathlib import Path
from typing import Callable

import pytest
import torch

from dataset import ProcessedLigandPocketDataset
from covalent_ext import (
    covapie_current11_role_seed_human_gold_ingestion_compiler_v1 as compiler,
)
from covalent_ext import (
    covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1
    as bridge,
)
from covalent_ext import covapie_current11_task2_lightning_runtime_integration_v1 as integration
from covalent_ext import covapie_current11_trainable_supervision_materializer_v1 as materializer
from covalent_ext.covapie_current11_training_tensorizer_v1 import (
    TENSORIZER_ERROR,
    tensorize_covapie_current11_training_supervision_v1,
)
from scripts import (
    check_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1
    as bridge_checker,
)
from scripts import check_covapie_current11_task2_runtime_caller_v1 as caller_checker


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT.parent / "covapie-state"
DECISION = STATE / compiler.CURRENT11_ROLE_SEED_HUMAN_GOLD_DECISION_RELATIVE_PATH_V1
ERROR = compiler.INGESTION_COMPILER_ERROR
EXPECTED_SAMPLE_COUNTS = (
    (5, 2, 6, 2),
    (5, 2, 6, 2),
    (5, 2, 6, 2),
    (16, 1, 8, 2),
    (22, 3, 3, 3),
    (32, 4, 7, 3),
    (32, 3, 7, 3),
    (30, 2, 10, 3),
    (30, 2, 11, 3),
    (28, 2, 10, 3),
    (11, 1, 9, 3),
)


def _environment() -> dict[str, str]:
    return {
        **os.environ,
        "PYTHONPATH": "src:.",
        "PYTHONDONTWRITEBYTECODE": "1",
    }


@pytest.fixture(scope="module")
def actual_bundle() -> dict[str, object]:
    remap_context, acquisition = bridge_checker._acquire_remap_context(
        lifecycle="precommit-untracked",
        repo_root=ROOT,
        state_root=STATE,
    )
    assert acquisition["test_harness_only"] is True
    assert acquisition["real_public_remap_context_build_performed"] is False
    assert acquisition["predecessor_public_call_counts"] == {
        "reconciliation": 1,
        "successor": 1,
        "B2": 1,
    }
    assert acquisition["formal_before_after_call_count"] == 2
    assert acquisition["production_monkeypatch_used"] is False
    compiler_context = (
        bridge.build_covapie_current11_task2_batch_descriptor_compiler_context_from_remap_context_v1(
            remap_context=remap_context,
        )
    )
    dataset = ProcessedLigandPocketDataset(
        STATE / caller_checker._FORMAL_CARRIER, center=False
    )
    raw_batch = dataset.collate_fn([dataset[index] for index in range(11)])
    batch = integration.attach_covapie_current11_task2_lightning_runtime_result_v1(
        enabled=True,
        batch=raw_batch,
        remap_context=remap_context,
        compiler_context=compiler_context,
    )
    runtime = batch[integration.SIDECAR_FIELD]
    assert type(runtime) is dict and runtime["runtime_status"] == "full_success"
    payload = materializer.load_covapie_current11_machine_authority_payload_v1(
        repo_root=ROOT,
        state_root=STATE,
        runtime_output17=runtime["remap_output17_or_none"],
    )
    before = materializer.build_current11_training_supervision_v1(
        authority_payload=payload
    )
    compiled = compiler.load_and_compile_covapie_current11_role_seed_human_gold_v1(
        state_root=STATE,
        machine_authority_payload=payload,
    )
    after = materializer.build_current11_training_supervision_v1(
        authority_payload=compiled["compiled_authority_payload"]
    )
    return {
        "batch": batch,
        "runtime": runtime,
        "payload": payload,
        "before": before,
        "compiled": compiled,
        "after": after,
    }


def _payload(actual_bundle: dict[str, object]) -> dict[str, object]:
    payload = copy.deepcopy(actual_bundle["payload"])
    assert type(payload) is dict
    return payload


def _decision_table(
    decision_bytes: bytes | None = None,
) -> tuple[list[str], list[list[str]]]:
    payload = DECISION.read_bytes() if decision_bytes is None else decision_bytes
    parsed = list(csv.reader(io.StringIO(payload.decode("utf-8"), newline=""), strict=True))
    return parsed[0], parsed[1:]


def _decision_bytes(columns: list[str], rows: list[list[str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(columns)
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def _mutated_decision(kind: str) -> bytes:
    columns, rows = _decision_table()
    if kind == "wrong_column":
        columns[0] = "wrong_sample_key"
    elif kind == "extra_column":
        columns.append("unexpected")
        for row in rows:
            row.append("")
    elif kind == "missing_column":
        columns.pop()
        for row in rows:
            row.pop()
    elif kind == "missing_row":
        rows.pop(0)
    elif kind == "duplicate_row":
        rows.insert(1, rows[0][:])
    elif kind == "extra_row":
        extra = rows[-1][:]
        extra[3:6] = ["21", "NONEXISTENT_SITE", "NONEXISTENT_ATOM"]
        rows.append(extra)
    elif kind == "sample_order_drift":
        rows[0], rows[13] = rows[13], rows[0]
    elif kind == "wrong_sample":
        rows[0][0] = "CYS_SG_SAMPLE_INDEX_999999"
    elif kind == "local_index_drift":
        rows[0][3] = "01"
    elif kind == "pdb_mismatch":
        rows[0][1] = "XXXX"
    elif kind == "ligand_mismatch":
        rows[0][2] = "XXX"
    elif kind == "atom_site_mismatch":
        rows[0][4] = "NONEXISTENT_SITE"
    elif kind in ("atom_name_mismatch", "nonexistent_atom"):
        rows[0][5] = "NONEXISTENT_ATOM"
    elif kind == "role_outside_exact3":
        rows[0][6] = "fourth_role"
    elif kind == "one_role_empty":
        for row in rows[:13]:
            if row[6] == "linker":
                row[6] = "scaffold"
    elif kind == "blank_role":
        rows[0][6] = ""
    elif kind == "invalid_seed_token":
        rows[0][7] = "True"
    elif kind == "all_false_seed":
        for row in rows[:13]:
            row[7] = "false"
    elif kind == "mixed_reviewer":
        rows[1][8] = "different-human"
    elif kind == "blank_reviewer":
        for row in rows[:13]:
            row[8] = ""
    elif kind == "self_reviewer_codex":
        for row in rows[:13]:
            row[8] = "codex"
    elif kind == "self_reviewer_chatgpt":
        for row in rows[:13]:
            row[8] = "human-chatgpt-reviewer"
    elif kind == "review_not_approve":
        for row in rows[:13]:
            row[9] = "REJECT"
    elif kind == "mixed_review_decision":
        rows[1][9] = "REJECT"
    elif kind == "blank_attestation":
        for row in rows[:13]:
            row[11] = ""
    elif kind == "mixed_attestation":
        rows[1][11] += " changed"
    elif kind == "blank_review_notes":
        for row in rows[:13]:
            row[12] = ""
    elif kind == "mixed_review_notes":
        rows[1][12] += ";changed"
    elif kind == "invalid_timestamp":
        for row in rows[:13]:
            row[10] = "2026-02-30T00:00:00Z"
    elif kind == "mixed_timestamp":
        rows[1][10] = "2026-08-16T04:37:32Z"
    else:
        raise AssertionError(kind)
    return _decision_bytes(columns, rows)


def _fails(action: Callable[[], object]) -> None:
    with pytest.raises(ValueError, match=f"^{ERROR}$") as captured:
        action()
    assert captured.value.__cause__ is not None


def test_public_api_exact_contract_and_silent_import() -> None:
    assert compiler.__all__ == (
        "HUMAN_GOLD_INGESTION_SCHEMA_V1",
        "CURRENT11_ROLE_SEED_HUMAN_GOLD_DECISION_SHA256_V1",
        "CURRENT11_ROLE_SEED_HUMAN_GOLD_DECISION_RELATIVE_PATH_V1",
        "compile_covapie_current11_role_seed_human_gold_v1",
        "load_and_compile_covapie_current11_role_seed_human_gold_v1",
    )
    assert compiler.HUMAN_GOLD_INGESTION_SCHEMA_V1 == (
        "covapie_current11_role_seed_human_gold_ingestion_v1"
    )
    assert compiler.CURRENT11_ROLE_SEED_HUMAN_GOLD_DECISION_SHA256_V1 == (
        "104cc3ec5c9cf6a250f07348695c0a52ca938ed3be082a61e4a983e6f1359ae4"
    )
    assert str(compiler.CURRENT11_ROLE_SEED_HUMAN_GOLD_DECISION_RELATIVE_PATH_V1) == (
        "manual-review-aids/current11-trainable-supervision-role-seed-v1/"
        "current11_role_seed_review_decisions.csv"
    )
    assert str(inspect.signature(
        compiler.compile_covapie_current11_role_seed_human_gold_v1
    )) == (
        "(*, machine_authority_payload: 'object', decision_csv_bytes: 'object') "
        "-> 'dict[str, object]'"
    )
    assert str(inspect.signature(
        compiler.load_and_compile_covapie_current11_role_seed_human_gold_v1
    )) == (
        "(*, state_root: 'Path', machine_authority_payload: 'object') "
        "-> 'dict[str, object]'"
    )
    completed = subprocess.run(
        (
            sys.executable,
            "-B",
            "-c",
            "from covalent_ext import "
            "covapie_current11_role_seed_human_gold_ingestion_compiler_v1",
        ),
        cwd=ROOT,
        env=_environment(),
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert completed.stdout == completed.stderr == b""


def test_actual_canonical_compiler_summary_provenance_and_exact_counts(
    actual_bundle: dict[str, object],
) -> None:
    result = actual_bundle["compiled"]
    assert type(result) is dict
    assert tuple(result) == (
        "schema_version",
        "decision_csv_sha256",
        "decision_row_count",
        "human_review_complete_sample_count",
        "role_atom_counts",
        "seed_membership_count",
        "sample_review_records",
        "compiled_authority_payload",
    )
    assert result["decision_csv_sha256"] == compiler.CURRENT11_ROLE_SEED_HUMAN_GOLD_DECISION_SHA256_V1
    assert result["decision_row_count"] == 323
    assert result["human_review_complete_sample_count"] == 11
    assert result["role_atom_counts"] == {
        "scaffold": 216,
        "linker": 24,
        "warhead": 83,
    }
    assert result["seed_membership_count"] == 29
    records = result["sample_review_records"]
    assert type(records) is list and len(records) == 11
    assert [
        (
            record["scaffold_count"],
            record["linker_count"],
            record["warhead_count"],
            record["seed_count"],
        )
        for record in records
    ] == list(EXPECTED_SAMPLE_COUNTS)
    assert all(record["reviewer_id"] == "fmx" for record in records)
    assert all(record["review_decision"] == "APPROVE" for record in records)


def test_deep_copy_preservation_input_unchanged_and_no_proposal_promotion(
    actual_bundle: dict[str, object],
) -> None:
    payload = _payload(actual_bundle)
    decision_bytes = DECISION.read_bytes()
    before_bytes = pickle.dumps(payload, protocol=5)
    first = compiler.compile_covapie_current11_role_seed_human_gold_v1(
        machine_authority_payload=payload,
        decision_csv_bytes=decision_bytes,
    )
    second = compiler.compile_covapie_current11_role_seed_human_gold_v1(
        machine_authority_payload=copy.deepcopy(payload),
        decision_csv_bytes=decision_bytes,
    )
    assert first == second
    assert pickle.dumps(payload, protocol=5) == before_bytes
    compiled_payload = first["compiled_authority_payload"]
    assert compiled_payload is not payload
    for original, compiled_sample in zip(
        payload["samples"], compiled_payload["samples"], strict=True
    ):
        original_other = {
            key: value for key, value in original.items()
            if key not in ("role_authority", "seed_authority")
        }
        compiled_other = {
            key: value for key, value in compiled_sample.items()
            if key not in ("role_authority", "seed_authority")
        }
        assert pickle.dumps(original_other, protocol=5) == pickle.dumps(
            compiled_other, protocol=5
        )
        count = len(original["ligand_nodes"])
        assert compiled_sample["role_authority"]["candidate_role_names"] == [""] * count
        assert compiled_sample["seed_authority"]["candidate_mask"] == [False] * count

    proposal_changed = copy.deepcopy(payload)
    for sample in proposal_changed["samples"]:
        candidates = sample["role_authority"]["candidate_role_names"]
        sample["role_authority"]["candidate_role_names"] = [
            "scaffold" if value != "scaffold" else "warhead" for value in candidates
        ]
    changed = compiler.compile_covapie_current11_role_seed_human_gold_v1(
        machine_authority_payload=proposal_changed,
        decision_csv_bytes=decision_bytes,
    )
    assert [
        sample["role_authority"]["role_ids"]
        for sample in changed["compiled_authority_payload"]["samples"]
    ] == [
        sample["role_authority"]["role_ids"]
        for sample in compiled_payload["samples"]
    ]


def test_actual_materializer_transition_and_authoritative_fields(
    actual_bundle: dict[str, object],
) -> None:
    before = actual_bundle["before"]
    after = actual_bundle["after"]
    assert before["summary"]["exact3_role_human_gold_count"] == 0
    assert before["summary"]["minimal_seed_human_gold_count"] == 0
    assert before["summary"]["real_admitted_sample_count"] == 0
    assert after["summary"]["exact3_role_human_gold_count"] == 11
    assert after["summary"]["minimal_seed_human_gold_count"] == 11
    assert after["summary"]["real_admitted_sample_count"] == 11
    assert after["summary"]["observed_geometry_count"] == 11
    assert after["summary"]["pre_geometry_authoritative_count"] == 0
    assert after["summary"]["post_geometry_authoritative_count"] == 0
    source = after["authoritative_supervision"]
    assert source["ligand_node_offsets"][-1] == 323
    assert source["pocket_node_offsets"][-1] == 2202
    assert source["sample_training_admitted"] == [True] * 11
    assert source["ligand_minimal_seed_or_anchor_valid"] == [True] * 11
    assert all(source["ligand_role_valid"])
    assert {role: source["ligand_role_id"].count(role) for role in (0, 1, 2)} == {
        0: 216,
        1: 24,
        2: 83,
    }
    assert sum(source["ligand_minimal_seed_or_anchor_mask"]) == 29
    assert all(source["observed_complex_pair_distance_valid"])
    assert not any(any(row) for row in source["pre_post_geometry_component_valid_mask"])
    assert not any(any(row) for row in source["pre_post_geometry_component_loss_mask"])
    assert all(value != value for row in source["pre_post_geometry_target_angstrom"] for value in row)
    assert all(record["target_residue_membership_count"] > 0 for record in after["reconciliation_records"])
    assert all(record["sample_training_admitted"] is True for record in after["reconciliation_records"])


def test_real_current11_raw_identity_matches_materialized_feature_binding(
    actual_bundle: dict[str, object],
) -> None:
    batch = actual_bundle["batch"]
    source = actual_bundle["after"]["authoritative_supervision"]
    binding = source["formal_carrier_feature_binding"]
    field_pairs = (
        ("lig_source_row_index", "ligand_source_row_index", 323),
        ("pocket_source_row_index", "pocket_source_row_index", 2202),
        ("lig_parser_local_index", "ligand_parser_local_index", 323),
        ("pocket_parser_local_index", "pocket_parser_local_index", 2202),
    )
    for raw_field, binding_field, expected_length in field_pairs:
        assert raw_field in batch
        raw = batch[raw_field]
        assert isinstance(raw, torch.Tensor)
        assert raw.dtype == torch.int64
        assert raw.ndim == 1
        assert len(raw) == expected_length
        assert raw.tolist() == binding[binding_field]


def test_real_current11_five_epoch_exact5_tensorizer_full_success(
    actual_bundle: dict[str, object],
) -> None:
    batch = actual_bundle["batch"]
    runtime = actual_bundle["runtime"]
    source = actual_bundle["after"]["authoritative_supervision"]
    coverage = [set() for _ in range(11)]
    ligand_total = source["ligand_node_offsets"][-1]
    for epoch in range(5):
        tensors = tensorize_covapie_current11_training_supervision_v1(
            batch=batch,
            runtime_result=runtime,
            authoritative_supervision=source,
            device=torch.device("cpu"),
            epoch=epoch,
            task_schedule_seed=0,
        )
        assert tensors.sample_training_admitted.tolist() == [True] * 11
        assert tensors.canonical_task_valid.tolist() == [True] * 11
        assert tensors.ligand_role_valid.tolist() == [True] * ligand_total
        assert torch.equal(
            tensors.ligand_base_generation_mask ^ tensors.ligand_base_fixed_mask,
            torch.ones((ligand_total, 1), dtype=torch.bool),
        )
        assert torch.equal(
            tensors.ligand_active_diffusion_loss_mask,
            tensors.ligand_base_generation_mask,
        )
        assert tensors.pair_candidate_is_positive.sum().item() == 11
        assert tensors.pair_positive_candidate_valid.tolist() == [True] * 11
        assert bool((tensors.pair_negative_count > 0).all().item())
        assert tensors.pre_post_geometry_component_valid_mask.sum().item() == 0
        assert tensors.pre_post_geometry_component_loss_mask.sum().item() == 0
        task_ids = tensors.canonical_task_id.tolist()
        assert tensors.ligand_minimal_seed_or_anchor_valid.tolist() == [
            task_id == 4 for task_id in task_ids
        ]
        for sample_index, task_id in enumerate(task_ids):
            coverage[sample_index].add(task_id)
    assert coverage == [set(range(5)) for _ in range(11)]


@pytest.mark.parametrize(
    "mutation",
    (
        "carbon_nitrogen_channel_permutation",
        "wrong_supported_ligand_channel",
        "ligand_source_row_mismatch",
        "pocket_source_row_mismatch",
        "within_sample_source_identity_swap",
        "parser_local_identity_mismatch",
    ),
)
def test_real_current11_feature_binding_corruptions_fail_closed(
    actual_bundle: dict[str, object], mutation: str,
) -> None:
    batch = copy.deepcopy(actual_bundle["batch"])
    runtime = batch[integration.SIDECAR_FIELD]
    source = copy.deepcopy(
        actual_bundle["after"]["authoritative_supervision"]
    )
    binding = source["formal_carrier_feature_binding"]
    if mutation == "carbon_nitrogen_channel_permutation":
        for field in ("lig_one_hot", "pocket_one_hot"):
            original = batch[field]
            permuted = original.clone()
            permuted[:, [0, 1]] = original[:, [1, 0]]
            assert bool((permuted.sum(dim=1) == 1).all().item())
            batch[field] = permuted
    elif mutation == "wrong_supported_ligand_channel":
        channel = binding["ligand_checkpoint_channel_index"][0]
        wrong_channel = (channel + 1) % 10
        batch["lig_one_hot"][0].zero_()
        batch["lig_one_hot"][0, wrong_channel] = 1.0
        assert batch["lig_one_hot"][0].sum().item() == 1.0
    elif mutation == "ligand_source_row_mismatch":
        batch["lig_source_row_index"][0] += 1
    elif mutation == "pocket_source_row_mismatch":
        batch["pocket_source_row_index"][0] += 1
    elif mutation == "within_sample_source_identity_swap":
        identities = batch["lig_source_row_index"]
        channels = binding["ligand_checkpoint_channel_index"]
        offsets = source["ligand_node_offsets"]
        same_channel_pair = next(
            (left, right)
            for start, end in zip(offsets, offsets[1:])
            for left in range(start, end)
            for right in range(left + 1, end)
            if channels[left] == channels[right]
        )
        left, right = same_channel_pair
        assert identities[left].item() != identities[right].item()
        assert torch.equal(batch["lig_one_hot"][left], batch["lig_one_hot"][right])
        identities[[left, right]] = identities[[right, left]].clone()
    else:
        batch["lig_parser_local_index"][1] = 0

    with pytest.raises(ValueError, match=f"^{TENSORIZER_ERROR}$"):
        tensorize_covapie_current11_training_supervision_v1(
            batch=batch,
            runtime_result=runtime,
            authoritative_supervision=source,
            device=torch.device("cpu"),
            epoch=0,
            task_schedule_seed=0,
        )


DECISION_FAILURES = (
    "wrong_column",
    "extra_column",
    "missing_column",
    "missing_row",
    "duplicate_row",
    "extra_row",
    "sample_order_drift",
    "wrong_sample",
    "local_index_drift",
    "pdb_mismatch",
    "ligand_mismatch",
    "atom_site_mismatch",
    "atom_name_mismatch",
    "role_outside_exact3",
    "one_role_empty",
    "blank_role",
    "invalid_seed_token",
    "all_false_seed",
    "mixed_reviewer",
    "blank_reviewer",
    "self_reviewer_codex",
    "self_reviewer_chatgpt",
    "review_not_approve",
    "mixed_review_decision",
    "blank_attestation",
    "mixed_attestation",
    "blank_review_notes",
    "mixed_review_notes",
    "invalid_timestamp",
    "mixed_timestamp",
    "nonexistent_atom",
)


@pytest.mark.parametrize("mutation", DECISION_FAILURES)
def test_decision_semantic_failure_matrix(
    actual_bundle: dict[str, object], mutation: str,
) -> None:
    payload = _payload(actual_bundle)
    _fails(lambda: compiler.compile_covapie_current11_role_seed_human_gold_v1(
        machine_authority_payload=payload,
        decision_csv_bytes=_mutated_decision(mutation),
    ))


@pytest.mark.parametrize(
    "decision_bytes",
    (
        b"\xff",
        b'sample_key,pdb_id\n"unterminated',
        b"",
    ),
    ids=("invalid_utf8", "invalid_csv_shape", "empty_csv"),
)
def test_decision_encoding_and_shape_fail_closed(
    actual_bundle: dict[str, object], decision_bytes: bytes,
) -> None:
    _fails(lambda: compiler.compile_covapie_current11_role_seed_human_gold_v1(
        machine_authority_payload=_payload(actual_bundle),
        decision_csv_bytes=decision_bytes,
    ))


MACHINE_FAILURES = (
    "wrong_schema",
    "wrong_sample_order",
    "machine_role_already_gold",
    "machine_role_partially_valid",
    "machine_seed_already_gold",
    "machine_seed_nonempty",
)


@pytest.mark.parametrize("mutation", MACHINE_FAILURES)
def test_machine_preingestion_guard_failure_matrix(
    actual_bundle: dict[str, object], mutation: str,
) -> None:
    payload = _payload(actual_bundle)
    sample = payload["samples"][0]
    count = len(sample["ligand_nodes"])
    if mutation == "wrong_schema":
        payload["schema_version"] = "wrong"
    elif mutation == "wrong_sample_order":
        payload["sample_order"] = list(reversed(payload["sample_order"]))
    elif mutation == "machine_role_already_gold":
        sample["role_authority"] = {
            "authority_class": "AUTHORITATIVE_HUMAN_GOLD",
            "role_ids": [0, 1] + [2] * (count - 2),
            "role_valid": [True] * count,
            "candidate_role_names": [""] * count,
            "proposal_only": False,
            "human_approved": True,
            "review_disposition": "already_gold",
            "reviewer_id": "human",
            "attestation": "Already reviewed.",
        }
    elif mutation == "machine_role_partially_valid":
        sample["role_authority"]["role_ids"][0] = 0
        sample["role_authority"]["role_valid"][0] = True
    elif mutation == "machine_seed_already_gold":
        sample["seed_authority"] = {
            "authority_class": "AUTHORITATIVE_HUMAN_GOLD",
            "mask": [True] + [False] * (count - 1),
            "valid": True,
            "candidate_mask": [False] * count,
            "proposal_only": False,
            "human_approved": True,
            "review_disposition": "already_gold",
            "reviewer_id": "human",
            "attestation": "Already reviewed.",
        }
    elif mutation == "machine_seed_nonempty":
        sample["seed_authority"]["mask"][0] = True
    _fails(lambda: compiler.compile_covapie_current11_role_seed_human_gold_v1(
        machine_authority_payload=payload,
        decision_csv_bytes=DECISION.read_bytes(),
    ))


def test_unknown_runtime_field_preserved_then_downstream_materializer_fails(
    actual_bundle: dict[str, object],
) -> None:
    payload = _payload(actual_bundle)
    payload["samples"][0]["canonical_task_id"] = 0
    compiled = compiler.compile_covapie_current11_role_seed_human_gold_v1(
        machine_authority_payload=payload,
        decision_csv_bytes=DECISION.read_bytes(),
    )
    assert compiled["compiled_authority_payload"]["samples"][0]["canonical_task_id"] == 0
    with pytest.raises(ValueError, match=f"^{materializer.MATERIALIZER_ERROR}$"):
        materializer.build_current11_training_supervision_v1(
            authority_payload=compiled["compiled_authority_payload"]
        )


def _write_canonical_temp(state_root: Path, payload: bytes, *, mode: int = 0o644) -> Path:
    target = state_root / compiler.CURRENT11_ROLE_SEED_HUMAN_GOLD_DECISION_RELATIVE_PATH_V1
    target.parent.mkdir(parents=True)
    target.write_bytes(payload)
    target.chmod(mode)
    return target


def test_canonical_loader_accepts_only_exact_hash_bound_artifact(
    actual_bundle: dict[str, object], tmp_path: Path,
) -> None:
    target = _write_canonical_temp(tmp_path, DECISION.read_bytes())
    result = compiler.load_and_compile_covapie_current11_role_seed_human_gold_v1(
        state_root=tmp_path,
        machine_authority_payload=_payload(actual_bundle),
    )
    assert result["decision_csv_sha256"] == compiler.CURRENT11_ROLE_SEED_HUMAN_GOLD_DECISION_SHA256_V1
    assert stat.S_IMODE(target.stat().st_mode) == 0o644


@pytest.mark.parametrize(
    "mutation",
    ("missing", "wrong_mode", "one_byte", "valid_sha_different", "alternate_file"),
)
def test_canonical_loader_failure_matrix(
    actual_bundle: dict[str, object], tmp_path: Path, mutation: str,
) -> None:
    canonical = DECISION.read_bytes()
    if mutation == "wrong_mode":
        _write_canonical_temp(tmp_path, canonical, mode=0o600)
    elif mutation == "one_byte":
        _write_canonical_temp(tmp_path, canonical + b"x")
    elif mutation == "valid_sha_different":
        columns, rows = _decision_table(canonical)
        for row in rows[:13]:
            row[12] += ";semantically_valid_hash_variant"
        variant = _decision_bytes(columns, rows)
        pure = compiler.compile_covapie_current11_role_seed_human_gold_v1(
            machine_authority_payload=_payload(actual_bundle),
            decision_csv_bytes=variant,
        )
        assert pure["decision_csv_sha256"] != compiler.CURRENT11_ROLE_SEED_HUMAN_GOLD_DECISION_SHA256_V1
        _write_canonical_temp(tmp_path, variant)
    elif mutation == "alternate_file":
        alternate = tmp_path / "alternate" / "current11_role_seed_review_decisions.csv"
        alternate.parent.mkdir(parents=True)
        alternate.write_bytes(canonical)
        alternate.chmod(0o644)
    _fails(lambda: compiler.load_and_compile_covapie_current11_role_seed_human_gold_v1(
        state_root=tmp_path,
        machine_authority_payload=_payload(actual_bundle),
    ))


def test_product_source_boundary_and_decision_file_immutable() -> None:
    source = inspect.getsource(compiler)
    pure = inspect.getsource(compiler._compile_impl)
    assert "import torch" not in source
    assert "import numpy" not in source
    assert "import rdkit" not in source.casefold()
    assert "import subprocess" not in source
    assert "requests." not in source
    assert "os.environ" not in source
    assert "read_bytes" not in pure
    assert "Path(" not in pure
    assert "open(" not in pure
    assert "subprocess" not in pure
    assert "tensorize" not in pure
    assert hashlib.sha256(DECISION.read_bytes()).hexdigest() == (
        compiler.CURRENT11_ROLE_SEED_HUMAN_GOLD_DECISION_SHA256_V1
    )
