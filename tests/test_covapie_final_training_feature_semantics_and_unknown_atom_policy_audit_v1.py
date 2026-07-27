from __future__ import annotations

import ast
import csv
import io
import json
import os
import subprocess
import sys
from dataclasses import FrozenInstanceError, asdict, replace
from functools import lru_cache
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from covalent_ext import (  # noqa: E402
    covapie_final_training_feature_semantics_and_unknown_atom_policy_audit_v1
    as audit,
)
from covalent_ext import covapie_hermetic_git_lifecycle_harness_v1 as lifecycle  # noqa: E402
import check_covapie_final_training_feature_semantics_and_unknown_atom_policy_audit_v1 as checker  # noqa: E402

NESTED_LIFECYCLE_ENV = "COVAPIE_FEATURE_AUDIT_NESTED_LIFECYCLE"


def _git(*args: str) -> bytes:
    return subprocess.run(
        ("git", *args),
        cwd=ROOT,
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _base(path: str | Path) -> bytes:
    return _git("show", f"{audit.BASE_COMMIT}:{Path(path).as_posix()}")


def _rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _truth(value: object) -> bool:
    return value is True or str(value).lower() == "true"


@lru_cache(maxsize=1)
def _result() -> dict[str, object]:
    return audit.derive_covapie_final_training_feature_semantics_audit_v1(ROOT)


@lru_cache(maxsize=1)
def _artifacts() -> dict[str, bytes]:
    return audit.build_covapie_final_training_feature_semantics_audit_artifacts_v1(ROOT)


def _manifest() -> dict[str, object]:
    return json.loads(_artifacts()[audit.MANIFEST_FILE])


def test_public_api_and_frozen_decision() -> None:
    assert audit.__all__ == (
        "FinalTrainingFeatureSemanticsAuditDecision",
        "FeatureSemanticsAuditScenario",
        "FeatureSemanticsFailureObservation",
        "build_covapie_final_training_feature_semantics_audit_artifacts_v1",
        "derive_covapie_final_training_feature_semantics_audit_v1",
        "evaluate_unknown_atom_case_v1",
        "serialize_covapie_final_training_feature_semantics_audit_decision_v1",
        "validate_covapie_final_training_feature_semantics_scenario_v1",
    )
    decision = _result()["decision"]
    with pytest.raises(FrozenInstanceError):
        decision.outcome = "invalid"  # type: ignore[misc]
    assert audit.FinalTrainingFeatureSemanticsAuditDecision.__dataclass_params__.frozen


def test_exact_base_identity() -> None:
    observed = _git(
        "show", "-s", "--format=%H%n%P%n%T%n%s", audit.BASE_COMMIT
    ).decode().splitlines()
    assert observed == [
        audit.BASE_COMMIT, audit.BASE_PARENT, audit.BASE_TREE, audit.BASE_SUBJECT
    ]


def test_quarantine_predecessor_sha_and_readiness() -> None:
    payloads, verified = audit._verify_predecessor(ROOT)
    assert verified is True
    assert {
        path: audit._sha(payload) for path, payload in payloads.items()
    } == audit.FROZEN_SHA256
    manifest = json.loads(payloads[audit.QUARANTINE_MANIFEST])
    assert manifest["ready_for_feature_semantics_audit"] is True
    assert manifest["effective_open_issue_count"] == 0
    assert manifest["feature_semantics_known"] is False
    assert manifest["unknown_atom_feature_policy_resolved"] is False


def test_current_effective_open_issues_are_empty() -> None:
    predecessor = json.loads(_base(audit.QUARANTINE_MANIFEST))
    assert predecessor["effective_open_issue_count"] == 0
    assert predecessor["effective_open_issues"] == []
    issue_rows = _rows(_base(audit.PREDECESSOR_ISSUES))
    assert len(issue_rows) == 30
    assert all(row["successor_effective_status"] == "resolved" for row in issue_rows)


def test_dynamic_source_discovery() -> None:
    discovery = _result()["discovery"]
    assert discovery["checkpoint_producer"] == Path(
        "src/covalent_ext/real_covalent_pretrained_forward_loss_smoke.py"
    )
    assert discovery["lightning_consumer"] == Path("lightning_modules.py")
    assert discovery["dynamics_consumer"] == Path(
        "equivariant_diffusion/dynamics.py"
    )
    assert discovery["fullatom_preprocessor"] == Path("process_crossdock.py")
    assert discovery["dataset_collate"] == Path("dataset.py")


def test_existing_feature_semantics_v0_source_test_checker_and_artifacts_found() -> None:
    paths = {
        path.as_posix() for path in _result()["discovery"]["feature_v0"]
    }
    assert {
        "src/covalent_ext/covapie_feature_semantics_audit_gate.py",
        "tests/test_covapie_feature_semantics_audit_gate_v0.py",
        "scripts/check_covapie_feature_semantics_audit_gate_v0.py",
        "data/derived/covalent_small/covapie_feature_semantics_audit_gate_v0/"
        "covapie_feature_semantics_audit_gate_manifest.json",
        "docs/covapie_feature_semantics_audit_gate_v0_summary.md",
    }.issubset(paths)


def test_existing_tensorization_audit_v0_found() -> None:
    paths = {
        path.as_posix() for path in _result()["discovery"]["tensor_v0"]
    }
    assert {
        "src/covalent_ext/covapie_feature_semantics_tensorization_audit_gate.py",
        "tests/test_covapie_feature_semantics_tensorization_audit_gate_v0.py",
        "scripts/check_covapie_feature_semantics_tensorization_audit_gate_v0.py",
        "data/derived/covalent_small/"
        "covapie_feature_semantics_tensorization_audit_gate_v0/"
        "covapie_feature_semantics_tensorization_audit_gate_manifest.json",
    }.issubset(paths)


def test_step12d_source_test_checker_and_artifacts_found() -> None:
    paths = {path.as_posix() for path in _result()["discovery"]["step12d"]}
    assert {
        "src/covalent_ext/real_covalent_pretrained_forward_loss_smoke.py",
        "tests/test_real_covalent_pretrained_forward_loss_smoke_v0.py",
        "scripts/check_real_covalent_pretrained_forward_loss_smoke_v0.py",
        "data/derived/covalent_small/real_covalent_pretrained_forward_loss_smoke_v0/"
        "real_covalent_pretrained_forward_loss_smoke_manifest.json",
    }.issubset(paths)


def test_feature_status_closed_set_and_counts() -> None:
    rows = _result()["registry_rows"]
    assert len(rows) == 30
    assert {row["feature_status"] for row in rows} <= audit.FEATURE_STATUSES
    assert sum(row["feature_status"] == "current_model_input" for row in rows) == 10
    assert sum(row["feature_status"] == "current_data_metadata_only" for row in rows) == 10
    assert sum(row["feature_status"] == "future_planned_not_integrated" for row in rows) == 6
    assert sum(row["feature_status"] == "not_a_training_feature" for row in rows) == 4


def test_evidence_status_closed_set_and_freeze_counts() -> None:
    rows = _result()["registry_rows"]
    assert {row["evidence_status"] for row in rows} <= audit.EVIDENCE_STATUSES
    decision = _result()["decision"]
    assert decision.explicit_semantics_count == 16
    assert decision.deterministically_derived_semantics_count == 7
    assert decision.ambiguous_semantics_count == 0
    assert decision.missing_semantics_count == 0
    assert decision.contradictory_semantics_count == 0


def test_current_model_input_complete_list() -> None:
    ids = [
        row["feature_id"] for row in _result()["registry_rows"]
        if row["feature_status"] == "current_model_input"
    ]
    assert ids == [
        "model_ligand_atom_categorical_10d",
        "model_pocket_atom_categorical_10d",
        "model_ligand_coordinates",
        "model_pocket_coordinates",
        "model_ligand_batch_membership",
        "model_pocket_batch_membership",
        "model_ligand_node_count",
        "model_pocket_node_count",
        "model_diffusion_time",
        "model_inpaint_fixed_ligand_mask",
    ]


def test_current_model_inputs_have_producer_and_consumer_lineage() -> None:
    rows = [
        row for row in _result()["registry_rows"]
        if row["feature_status"] == "current_model_input"
    ]
    assert all(row["producer_path"] and row["producer_symbol"] for row in rows)
    assert all(row["consumer_path"] and row["consumer_symbol"] for row in rows)
    assert all(row["consumer_operation"] for row in rows)
    assert _result()["decision"].all_current_model_input_semantics_frozen is True


def test_current_model_input_dtype_rank_shape_width() -> None:
    rows = [
        row for row in _result()["registry_rows"]
        if row["feature_status"] == "current_model_input"
    ]
    assert all(row["runtime_dtype"] not in {"", "not_applicable"} for row in rows)
    assert all(row["tensor_rank"] not in {"", "not_applicable"} for row in rows)
    assert all(row["tensor_shape_or_width"] not in {"", "not_applicable"} for row in rows)
    categorical = [row for row in rows if "categorical_10d" in row["feature_id"]]
    assert all(row["checkpoint_compatible_current_width"] == "10" for row in categorical)
    assert all(row["runtime_dtype"] == "torch.float32" for row in categorical)
    assert all(row["tensor_shape_or_width"] == "[N,10]" for row in categorical)


def test_vocabulary_channel_ordering_and_checkpoint_mapping() -> None:
    expected = "C:0|N:1|O:2|S:3|B:4|Br:5|Cl:6|P:7|I:8|F:9"
    rows = {
        row["feature_id"]: row for row in _result()["registry_rows"]
    }
    for feature_id in (
        "model_ligand_atom_categorical_10d",
        "model_pocket_atom_categorical_10d",
    ):
        assert rows[feature_id]["vocabulary_or_value_domain"] == expected
        assert rows[feature_id]["channel_or_index_meaning"] == expected
        assert "all-zero" in rows[feature_id]["unknown_value_semantics"]
    assert audit.CHECKPOINT_ATOMIC_NUMBER_TO_INDEX == {
        6: 0, 7: 1, 8: 2, 16: 3, 5: 4,
        35: 5, 17: 6, 15: 7, 53: 8, 9: 9,
    }


def test_coordinate_unit_frame_and_normalization() -> None:
    rows = {
        row["feature_id"]: row for row in _result()["registry_rows"]
    }
    for feature_id in ("model_ligand_coordinates", "model_pocket_coordinates"):
        row = rows[feature_id]
        assert row["coordinate_unit"] == "angstrom"
        assert row["coordinate_frame"] == (
            "per-sample joint ligand+pocket unweighted atom-centroid centered"
        )
        assert row["normalization_or_scaling"] == (
            "center subtraction then divide by normalize_factors[0]=1"
        )
        assert row["tensor_shape_or_width"] == "[N,3]"


def test_graph_membership_node_and_edge_mask_boundary() -> None:
    rows = {
        row["feature_id"]: row for row in _result()["registry_rows"]
    }
    assert rows["model_ligand_batch_membership"]["index_base"] == "0"
    assert rows["model_pocket_batch_membership"]["mask_semantics"] == (
        "equal membership defines same-sample adjacency"
    )
    assert rows["adapter_padded_node_validity_masks"]["feature_status"] == (
        "not_a_training_feature"
    )
    assert rows["external_edge_mask"]["feature_status"] == "not_a_training_feature"
    assert "get_edges" in rows["external_edge_mask"]["evidence_reason"]


def test_protein_unknown_policy_is_independently_unresolved() -> None:
    decision = _result()["decision"]
    assert decision.protein_unknown_atom_policy == "unknown_atom_policy_unresolved"
    assert decision.protein_unknown_atom_policy_resolved is False
    rows = [
        row for row in _result()["unknown_rows"]
        if row["domain"] == "protein_or_pocket_atom"
    ]
    assert len(rows) == 20


def test_ligand_unknown_policy_is_independently_unresolved() -> None:
    decision = _result()["decision"]
    assert decision.ligand_unknown_atom_policy == "unknown_atom_policy_unresolved"
    assert decision.ligand_unknown_atom_policy_resolved is False
    rows = [
        row for row in _result()["unknown_rows"]
        if row["domain"] == "ligand_atom"
    ]
    assert len(rows) == 20


def test_unknown_policy_matrix_executes_formal_evaluator() -> None:
    direct = audit.evaluate_unknown_atom_case_v1(
        "protein_or_pocket_atom",
        "unsupported token",
        current_unsupported_count=329,
    )
    row = next(
        row for row in _result()["unknown_rows"]
        if row["domain"] == "protein_or_pocket_atom"
        and row["case_id"] == "unsupported token"
    )
    assert row == direct
    assert direct["fails_closed"] is False
    assert "all-zero" in direct["observed_current_behavior"]


def test_checkpoint_width_compatibility_preserved_without_new_channel() -> None:
    decision = _result()["decision"]
    assert decision.checkpoint_compatibility_preserved is True
    assert decision.model_changed is False
    assert decision.dataloader_changed is False
    rows = _result()["unknown_rows"]
    width = [
        row for row in rows if row["case_id"] == "new channel width change"
    ]
    assert len(width) == 2
    assert all(row["checkpoint_width_effect"] == "incompatible_10_to_11" for row in width)


def test_silent_carbon_zero_and_first_index_fallbacks_not_accepted() -> None:
    rows = _result()["unknown_rows"]
    carbon = [row for row in rows if row["case_id"] == "silent carbon fallback"]
    zero = [row for row in rows if row["case_id"] == "silent zero-vector fallback"]
    first = [row for row in rows if row["case_id"] == "silent first-index fallback"]
    assert len(carbon) == len(zero) == len(first) == 2
    assert all(_truth(row["fails_closed"]) for row in carbon + first)
    assert all(not _truth(row["fails_closed"]) for row in zero)
    assert all(row["allowed_training_policy"] == "unknown_atom_policy_unresolved" for row in zero)


def test_no_atom_name_element_inference() -> None:
    source = (ROOT / checker.EXACT10[0]).read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_atom_coverage"
    )
    segment = ast.get_source_segment(source, function)
    assert segment is not None
    assert 'row.get("type_symbol"' in segment
    assert "atom_name" not in segment


def test_11_sample_22_table_atom_coverage() -> None:
    coverage = {row["domain"]: row for row in _result()["coverage_rows"]}
    assert coverage["protein_or_pocket_atom"] == {
        "domain": "protein_or_pocket_atom",
        "source_table_count": 11,
        "atom_row_count": 2531,
        "observed_explicit_element_or_token_count": 2531,
        "observed_vocabulary": {"C": 1323, "H": 329, "N": 405, "O": 442, "S": 32},
        "supported_row_count": 2202,
        "unknown_or_unsupported_row_count": 329,
        "missing_feature_value_count": 0,
        "policy_disposition": "unknown_atom_policy_unresolved",
        "verified": True,
    }
    assert coverage["ligand_atom"] == {
        "domain": "ligand_atom",
        "source_table_count": 11,
        "atom_row_count": 339,
        "observed_explicit_element_or_token_count": 339,
        "observed_vocabulary": {"C": 227, "F": 1, "H": 16, "N": 34, "O": 59, "P": 1, "S": 1},
        "supported_row_count": 323,
        "unknown_or_unsupported_row_count": 16,
        "missing_feature_value_count": 0,
        "policy_disposition": "unknown_atom_policy_unresolved",
        "verified": True,
    }


def test_canonical_exact5_masks_and_b3() -> None:
    assert audit.CANONICAL_MASKS == (
        ("warhead_only", "A"),
        ("linker_plus_warhead", "B"),
        ("scaffold_plus_warhead", "B2"),
        ("scaffold_only", "B3"),
        ("scaffold_plus_linker_plus_warhead", "C"),
    )
    assert _manifest()["canonical_mask_count"] == 5
    assert _manifest()["canonical_masks"][3] == {
        "semantic_name": "scaffold_only", "display_alias": "B3"
    }


def test_metadata_only_features_do_not_masquerade_as_model_input() -> None:
    metadata = [
        row for row in _result()["registry_rows"]
        if row["feature_status"] == "current_data_metadata_only"
    ]
    assert [row["feature_id"] for row in metadata] == [
        "data_pocket_type_symbol",
        "data_ligand_type_symbol",
        "data_pocket_xyz",
        "data_ligand_xyz",
        "data_canonical_covalent_task_masks",
        "data_target_residue_locator",
        "data_covalent_atom_pair_and_indices",
        "data_warhead_type",
        "data_pre_post_geometry",
        "data_quarantine_control_plane",
    ]
    assert all(not _truth(row["training_consumed"]) for row in metadata)
    assert all(not row["consumer_path"] for row in metadata)


def test_five_planned_modules_remain_zero_of_five() -> None:
    manifest = _manifest()
    assert manifest["planned_covalent_model_module_count"] == 5
    assert manifest["integrated_covalent_model_module_count"] == 0
    assert manifest["planned_covalent_model_modules"] == list(
        audit.PLANNED_COVALENT_MODEL_MODULES
    )
    future = [
        row["feature_name"] for row in _result()["registry_rows"]
        if row["feature_id"].startswith("future_covalent_model_module_")
    ]
    assert future == list(audit.PLANNED_COVALENT_MODEL_MODULES)


def test_step12d_is_smoke_legality_not_final_semantics_authority() -> None:
    manifest = _manifest()
    assert manifest["step12d_smoke_legality_verified"] is True
    assert manifest["step12d_final_feature_semantics_contract"] is False
    assert manifest["step12d_training_readiness_authority"] is False
    step12d = json.loads(_base(
        "data/derived/covalent_small/real_covalent_pretrained_forward_loss_smoke_v0/"
        "real_covalent_pretrained_forward_loss_smoke_manifest.json"
    ))
    assert step12d["real_covalent_pretrained_forward_loss_smoke_passed"] is True
    assert step12d["formal_training_allowed"] is False


def test_feature_semantics_known_strict_conditions() -> None:
    decision = _result()["decision"]
    assert decision.all_current_model_input_semantics_frozen is True
    assert decision.feature_semantics_audit_completed is True
    assert decision.feature_semantics_known is False
    assert decision.unknown_atom_feature_policy_resolved is False
    resolved = audit.validate_covapie_final_training_feature_semantics_scenario_v1(
        replace(
            audit.FeatureSemanticsAuditScenario(),
            protein_policy="fail_closed_rejection_required_for_checkpoint_compatibility",
            ligand_policy="fail_closed_rejection_required_for_checkpoint_compatibility",
            protein_policy_marked_resolved=True,
            ligand_policy_marked_resolved=True,
            semantics_marked_known=True,
            ready_contract_design=True,
        )
    )
    assert resolved.feature_semantics_known is True
    assert resolved.ready_for_tensor_label_loss_mask_contract_design is True


def test_dynamic_next_step() -> None:
    decision = _result()["decision"]
    assert decision.recommended_next_step == (
        "resolve_covapie_training_feature_semantics_and_unknown_atom_policy_gaps_v1"
    )
    assert "training" not in decision.recommended_next_step.split("_")[-1]
    contradictory = replace(
        decision, contradictory_semantics_count=1,
        recommended_next_step="resolve_covapie_training_feature_semantics_contradictions_v1"
    )
    assert contradictory.recommended_next_step.endswith("contradictions_v1")


def test_issue_inventory_exact2_and_byte_equivalent_inheritance() -> None:
    payload = _artifacts()[audit.ISSUE_INVENTORY_FILE]
    predecessor = _base(audit.PREDECESSOR_ISSUES)
    assert payload.startswith(predecessor)
    rows = _rows(payload)
    assert len(rows) == 32
    assert [row["issue_id"] for row in rows[-2:]] == [
        "FINAL_TRAINING_FEATURE_SEMANTICS_UNRESOLVED",
        "UNKNOWN_ATOM_FEATURE_POLICY_UNRESOLVED",
    ]
    assert rows[-2]["successor_effective_status"] == "resolved"
    assert rows[-1]["successor_effective_status"] == "open"


def test_failure_matrix_really_executes_formal_validator() -> None:
    rows = _result()["failure_rows"]
    assert len(rows) == len(audit.FAILURE_CASES) == 34
    assert [row["failure_case"] for row in rows] == list(audit.FAILURE_CASES)
    assert all(row["observed_outcome"] == "invalid" for row in rows)
    assert all(row["fails_closed"] and row["verified"] for row in rows)
    direct = audit.validate_covapie_final_training_feature_semantics_scenario_v1(
        replace(
            audit.FeatureSemanticsAuditScenario(),
            silent_zero_vector_fallback=True,
        )
    )
    assert direct.outcome == "invalid"
    assert "silent_zero_vector_fallback" in direct.reasons


def test_deterministic_decision_serialization_and_all_evidence_bytes() -> None:
    first = audit.derive_covapie_final_training_feature_semantics_audit_v1(ROOT)
    second = audit.derive_covapie_final_training_feature_semantics_audit_v1(ROOT)
    third = audit.derive_covapie_final_training_feature_semantics_audit_v1(ROOT)
    assert first["decision"] == second["decision"] == third["decision"]
    assert first["source_rows"] == second["source_rows"] == third["source_rows"]
    assert first["registry_rows"] == second["registry_rows"] == third["registry_rows"]
    assert first["unknown_rows"] == second["unknown_rows"] == third["unknown_rows"]
    assert first["failure_rows"] == second["failure_rows"] == third["failure_rows"]
    assert first["issue_payload"] == second["issue_payload"] == third["issue_payload"]
    assert (
        audit.serialize_covapie_final_training_feature_semantics_audit_decision_v1(
            first["decision"]
        )
        == audit.serialize_covapie_final_training_feature_semantics_audit_decision_v1(
            third["decision"]
        )
    )
    assert _artifacts() == audit.build_covapie_final_training_feature_semantics_audit_artifacts_v1(ROOT)


def test_materialized_evidence_and_manifest_hashes() -> None:
    assert set(_artifacts()) == set(audit.OUTPUT_FILES)
    for name, payload in _artifacts().items():
        assert (ROOT / audit.OUTPUT_ROOT / name).read_bytes() == payload
    manifest = _manifest()
    assert manifest["source_inventory_row_count"] == 73
    assert manifest["feature_registry_row_count"] == 30
    assert manifest["unknown_policy_matrix_row_count"] == 40
    assert manifest["failure_matrix_row_count"] == 34
    for name, expected in manifest["evidence_sha256"].items():
        assert audit._sha(_artifacts()[name]) == expected


def test_readiness_stays_closed_and_no_execution_boundary_crossed() -> None:
    manifest = _manifest()
    assert manifest["feature_semantics_audit_completed"] is True
    assert manifest["audit_outcome"] == "audited_with_blockers"
    assert manifest["ready_for_tensor_label_loss_mask_contract_design"] is False
    assert manifest["ready_for_tensorization"] is False
    assert manifest["ready_for_model_integration"] is False
    assert manifest["ready_for_training"] is False
    for key in (
        "tensorization_used", "checkpoint_access", "model_changed",
        "dataloader_changed", "forward_changed", "loss_changed",
        "training_used", "raw_read", "raw_write", "provider_used",
        "network_used", "download_used",
    ):
        assert manifest[key] is False


def test_source_inventory_complete_base_bound_and_safe() -> None:
    rows = _result()["source_rows"]
    assert len(rows) == 73
    assert sum(row["source_role"] == "pocket_atom_table" for row in rows) == 11
    assert sum(row["source_role"] == "ligand_atom_table" for row in rows) == 11
    assert all(row["committed_in_base"] and row["verified"] for row in rows)
    assert all(not row["source_path"].startswith("data/raw/") for row in rows)
    forbidden = {".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".npz"}
    assert all(Path(row["source_path"]).suffix.lower() not in forbidden for row in rows)


def test_checker_independently_reconstructs_and_stdout_is_stable() -> None:
    environment = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": "src",
    }
    command = (sys.executable, "-B", checker.EXACT10[2].as_posix())
    first = subprocess.run(
        command, cwd=ROOT, env=environment, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    second = subprocess.run(
        command, cwd=ROOT, env=environment, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    assert first.stderr == second.stderr == b""
    assert first.stdout == second.stdout
    assert b"audit_outcome=audited_with_blockers" in first.stdout
    assert b"protein_unknown_atom_policy=unknown_atom_policy_unresolved" in first.stdout
    assert b"ready_for_training=false" in first.stdout


def test_exact10_paths_modes_and_no_symlinks_or_forbidden_suffixes() -> None:
    assert len(checker.EXACT10) == len(set(checker.EXACT10)) == 10
    forbidden = {
        ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip",
        ".tgz", ".npz", ".tmp", ".part",
    }
    for path in checker.EXACT10:
        target = ROOT / path
        assert target.is_file() and not target.is_symlink()
        assert target.stat().st_mode & 0o777 == 0o644
        assert path.suffix.lower() not in forbidden
        assert target.stat().st_size < 100 * 1024 * 1024


def test_shared_lifecycle_three_states(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if os.environ.get(NESTED_LIFECYCLE_ENV) == "1":
        assert _result()["decision"].outcome == "audited_with_blockers"
        return
    real_capture = lifecycle._capture_state
    states: list[str] = []
    checker_outputs: list[bytes] = []

    def capture(repository: Path, **kwargs):
        state = real_capture(repository, **kwargs)
        if state.lifecycle in (
            "pre_commit",
            "formal_main_post_commit_unpushed",
            "formal_main_post_push",
        ):
            environment = {
                **os.environ,
                NESTED_LIFECYCLE_ENV: "1",
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONPATH": "src",
            }
            targeted = subprocess.run(
                (
                    sys.executable, "-m", "pytest", "-q",
                    "-p", "no:cacheprovider", checker.EXACT10[1].as_posix(),
                ),
                cwd=repository,
                env=environment,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            assert targeted.returncode == 0, targeted.stdout + targeted.stderr
            assert targeted.stderr == b""
            checked = subprocess.run(
                (sys.executable, "-B", checker.EXACT10[2].as_posix()),
                cwd=repository,
                env=environment,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            assert checked.returncode == 0, checked.stdout + checked.stderr
            assert checked.stderr == b""
            states.append(state.lifecycle)
            checker_outputs.append(checked.stdout)
        return state

    monkeypatch.setattr(lifecycle, "_capture_state", capture)
    report = lifecycle.exercise_hermetic_git_lifecycle_matrix(
        ROOT,
        tmp_path,
        base_commit=audit.BASE_COMMIT,
        formal_commit_subject=audit.FORMAL_COMMIT_SUBJECT,
        exact_paths=checker.EXACT10,
    )
    assert states == [
        "pre_commit",
        "formal_main_post_commit_unpushed",
        "formal_main_post_push",
    ]
    assert checker_outputs[0] == checker_outputs[1] == checker_outputs[2]
    assert report.candidate_parent == audit.BASE_COMMIT
    assert report.candidate_subject == audit.FORMAL_COMMIT_SUBJECT
    assert report.exact_path_count == 10
    assert report.cleanup_verified is True
