from __future__ import annotations

import ast
import csv
import dataclasses
import hashlib
import io
import json
import os
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(SCRIPTS))

from covalent_ext import (  # noqa: E402
    covapie_hermetic_git_lifecycle_harness_v1 as lifecycle,
)
from covalent_ext import (  # noqa: E402
    covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1
    as resolution,
)
import check_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1 as checker  # noqa: E402

NESTED_LIFECYCLE_ENV = "COVAPIE_UNKNOWN_POLICY_RESOLUTION_NESTED_LIFECYCLE"


def _git(*args: str) -> bytes:
    return subprocess.run(
        ("git", *args),
        cwd=ROOT,
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _base(path: Path) -> bytes:
    _git("cat-file", "-e", f"{resolution.BASE_COMMIT}:{path.as_posix()}")
    return _git("show", f"{resolution.BASE_COMMIT}:{path.as_posix()}")


def _rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _truth(value: object) -> bool:
    return value is True or str(value).lower() == "true"


@lru_cache(maxsize=1)
def _result() -> dict:
    return (
        resolution.derive_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1(
            ROOT
        )
    )


@lru_cache(maxsize=1)
def _artifacts() -> dict[str, bytes]:
    return (
        resolution.build_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_artifacts_v1(
            ROOT
        )
    )


def test_public_api_and_frozen_decision() -> None:
    decision = _result()["decision"]
    assert dataclasses.is_dataclass(decision)
    assert decision.schema_version == resolution.SCHEMA_VERSION
    assert decision.outcome == "resolved_policy_contract"
    with pytest.raises(dataclasses.FrozenInstanceError):
        decision.outcome = "invalid"  # type: ignore[misc]
    assert set(resolution.__all__) >= {
        "TrainingFeatureSemanticsAndUnknownAtomPolicyResolutionDecision",
        "classify_type_symbol_v1",
        "project_type_symbols_to_checkpoint_heavy_v1",
        "validate_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_scenario_v1",
    }


def test_base_identity_and_parent_tree_subject() -> None:
    observed = _git(
        "show",
        "-s",
        "--format=%H%n%P%n%T%n%s",
        resolution.BASE_COMMIT,
    ).decode().splitlines()
    assert observed == [
        resolution.BASE_COMMIT,
        resolution.BASE_PARENT,
        resolution.BASE_TREE,
        resolution.BASE_SUBJECT,
    ]


def test_frozen_predecessor_sha256() -> None:
    for path, expected in resolution.FROZEN_SHA256.items():
        assert hashlib.sha256(_base(path)).hexdigest() == expected


def test_predecessor_has_exact_unique_open_issue() -> None:
    manifest = json.loads(_base(resolution.PREDECESSOR_MANIFEST))
    assert manifest["effective_open_issue_count"] == 1
    assert manifest["effective_open_issues"] == [
        "UNKNOWN_ATOM_FEATURE_POLICY_UNRESOLVED"
    ]
    assert manifest["feature_semantics_known"] is False
    assert manifest["unknown_atom_feature_policy_resolved"] is False


def test_noh_checkpoint_config_lineage() -> None:
    text = _base(resolution.CHECKPOINT_CONFIG).decode()
    assert "dataset: 'crossdock'" in text
    assert "processed_crossdock_noH_full" in text
    assert "pocket_representation: 'full-atom'" in text
    assert "normalize_factors: [1, 4]" in text


def test_checkpoint_vocabulary_is_exact10() -> None:
    assert resolution.CHECKPOINT_TOKEN_TO_INDEX == {
        "C": 0, "N": 1, "O": 2, "S": 3, "B": 4,
        "Br": 5, "Cl": 6, "P": 7, "I": 8, "F": 9,
    }
    assert resolution.CHECKPOINT_CHANNEL_ORDER == (
        "C:0|N:1|O:2|S:3|B:4|Br:5|Cl:6|P:7|I:8|F:9"
    )


def test_preview_11d_boundary_is_not_checkpoint_authority() -> None:
    lineage = _result()["lineage"]
    assert lineage["preview_channel_order_preserved"] is True
    assert lineage["preview_or_intermediate_only"] is True
    assert lineage["preview_11d_checkpoint_authority"] is False
    assert resolution.PREVIEW_CHANNEL_ORDER.endswith("|others:10")


def test_current_smoke_zero_vector_behavior_is_observed() -> None:
    lineage = _result()["lineage"]
    assert lineage["observed_smoke_zero_vector_behavior"] is True


def test_zero_vector_final_policy_is_forbidden() -> None:
    decision = _result()["decision"]
    manifest = json.loads(_artifacts()[resolution.MANIFEST_FILE])
    assert decision.silent_zero_vector_fallback_allowed is False
    assert manifest["silent_zero_vector_fallback_allowed"] is False
    assert manifest["others_channel_checkpoint_input_allowed"] is False
    assert manifest["new_unknown_channel_allowed"] is False


def test_explicit_hydrogen_classification_and_projection() -> None:
    assert resolution.classify_type_symbol_v1("H") == "explicit_hydrogen"
    projection = resolution.project_type_symbols_to_checkpoint_heavy_v1(
        ("C", "H", "O")
    )
    assert projection.outcome == "passed"
    assert projection.keep_mask == (True, False, True)
    assert projection.source_to_projected_index == (0, None, 1)
    assert projection.checkpoint_channel_indices == (0, None, 2)
    assert projection.sample_rejected is False


@pytest.mark.parametrize("symbol,index", resolution.CHECKPOINT_TOKEN_TO_INDEX.items())
def test_supported_heavy_classification_and_channel(
    symbol: str, index: int
) -> None:
    assert (
        resolution.classify_type_symbol_v1(symbol)
        == "supported_checkpoint_heavy_atom"
    )
    projection = resolution.project_type_symbols_to_checkpoint_heavy_v1((symbol,))
    assert projection.checkpoint_channel_indices == (index,)
    assert projection.keep_mask == (True,)


def test_unsupported_nonhydrogen_rejects_complete_sample() -> None:
    assert resolution.classify_type_symbol_v1("Se") == "unsupported_nonhydrogen"
    projection = resolution.project_type_symbols_to_checkpoint_heavy_v1(
        ("C", "Se", "H")
    )
    assert projection.outcome == "invalid"
    assert projection.sample_rejected is True
    assert projection.keep_mask == (False, False, False)
    assert projection.source_to_projected_index == (None, None, None)


@pytest.mark.parametrize("value", (None, "", " H", "H ", "carbon", "CA", 6))
def test_missing_or_invalid_symbol_rejects(value: object) -> None:
    assert resolution.classify_type_symbol_v1(value) == "missing_or_invalid"
    projection = resolution.project_type_symbols_to_checkpoint_heavy_v1((value,))
    assert projection.outcome == "invalid"
    assert projection.sample_rejected is True


def test_classification_helper_has_no_atom_name_inference() -> None:
    source = (ROOT / checker.EXACT10[0]).read_text()
    tree = ast.parse(source)
    functions = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "classify_type_symbol_v1"
    ]
    assert len(functions) == 1
    function = functions[0]
    assert [arg.arg for arg in function.args.args] == ["type_symbol"]
    assert not any(
        (isinstance(node, ast.Name) and node.id == "atom_name")
        or (isinstance(node, ast.Constant) and node.value == "atom_name")
        for node in ast.walk(function)
    )


def test_exact22_source_tables() -> None:
    table_rows = [
        row
        for row in _result()["source_rows"]
        if row["source_role"] in {"pocket_atom_table", "ligand_atom_table"}
    ]
    assert len(table_rows) == 22
    assert len({row["source_path"] for row in table_rows}) == 22


def test_exact2870_source_atom_rows() -> None:
    assert len(_result()["disposition_rows"]) == 2870
    assert _result()["counts"]["source_atom_row_count"] == 2870


def test_exact345_hydrogen_exclusions() -> None:
    rows = _result()["disposition_rows"]
    hydrogens = [
        row for row in rows if row["symbol_class"] == "explicit_hydrogen"
    ]
    assert len(hydrogens) == 345
    assert all(
        row["projection_disposition"] == "exclude_explicit_hydrogen"
        for row in hydrogens
    )


def test_exact2525_retained_heavy_rows() -> None:
    retained = [
        row
        for row in _result()["disposition_rows"]
        if row["retained_for_checkpoint_model"]
    ]
    assert len(retained) == 2525
    assert all(row["checkpoint_channel_index"] in range(10) for row in retained)


def test_per_domain_counts_are_exact() -> None:
    assert _result()["counts"] == resolution.EXPECTED_COUNTS


def test_projected_source_order_is_preserved() -> None:
    grouped: dict[tuple[str, str], list[dict]] = {}
    for row in _result()["disposition_rows"]:
        grouped.setdefault(
            (row["sample_index_row_id"], row["domain"]), []
        ).append(row)
    for rows in grouped.values():
        retained = [row for row in rows if row["retained_for_checkpoint_model"]]
        assert [
            row["source_atom_row_index_0based"] for row in retained
        ] == sorted(row["source_atom_row_index_0based"] for row in retained)


def test_projected_indices_are_contiguous_and_unique() -> None:
    grouped: dict[tuple[str, str], list[int]] = {}
    for row in _result()["disposition_rows"]:
        if row["retained_for_checkpoint_model"]:
            grouped.setdefault(
                (row["sample_index_row_id"], row["domain"]), []
            ).append(row["projected_heavy_atom_row_index_0based"])
    for indices in grouped.values():
        assert indices == list(range(len(indices)))
        assert len(indices) == len(set(indices))


def test_hydrogen_has_no_projected_index_or_channel() -> None:
    rows = [
        row
        for row in _result()["disposition_rows"]
        if row["symbol_class"] == "explicit_hydrogen"
    ]
    assert all(
        row["projected_heavy_atom_row_index_0based"] is None
        and row["checkpoint_channel_index"] is None
        and not row["sample_rejected"]
        for row in rows
    )


def test_retained_rows_have_exact_checkpoint_channels() -> None:
    for row in _result()["disposition_rows"]:
        if row["retained_for_checkpoint_model"]:
            assert (
                row["checkpoint_channel_index"]
                == resolution.CHECKPOINT_TOKEN_TO_INDEX[row["type_symbol"]]
            )


def test_exact11_sample_projections_pass() -> None:
    rows = _result()["sample_rows"]
    assert len(rows) == 11
    assert all(row["sample_policy_outcome"] == "passed" for row in rows)
    assert all(row["retained_joint_atom_count"] > 0 for row in rows)


def test_exact11_atom_pair_remaps() -> None:
    rows = _result()["sample_rows"]
    assert sum(row["pair_projection_exact_one"] for row in rows) == 11
    assert all(
        row["projected_residue_pair_row_index_0based"] is not None
        and row["projected_ligand_pair_row_index_0based"] is not None
        for row in rows
    )


def test_pair_atoms_are_retained_heavy_atoms() -> None:
    assert all(
        row["residue_pair_atom_retained"]
        and row["ligand_pair_atom_retained"]
        for row in _result()["sample_rows"]
    )


def test_filter_precedes_centering_and_uses_heavy_joint_set() -> None:
    rows = _result()["sample_rows"]
    assert all(row["hydrogen_filter_before_centering"] for row in rows)
    assert {
        row["centering_node_set"] for row in rows
    } == {"retained_ligand_plus_pocket_heavy_atoms"}


def test_filter_precedes_masks_counts_batches_and_pair_indices() -> None:
    manifest = json.loads(_artifacts()[resolution.MANIFEST_FILE])
    for key in (
        "hydrogen_filter_before_coordinate_centering",
        "hydrogen_filter_before_node_count",
        "hydrogen_filter_before_batch_membership",
        "hydrogen_filter_before_mask_projection",
        "hydrogen_filter_before_atom_pair_index_projection",
    ):
        assert manifest[key] is True
    assert set(manifest["shared_retained_heavy_projection_consumers"]) == set(
        resolution.SHARED_PROJECTION_CONSUMERS
    )


def test_checkpoint_width_remains10_after_projection() -> None:
    decision = _result()["decision"]
    assert decision.checkpoint_categorical_width == 10
    assert decision.checkpoint_channel_order_preserved is True
    assert {
        row["checkpoint_width_after_projection"]
        for row in _result()["sample_rows"]
    } == {10}


def test_canonical_masks_are_exact5_and_include_b3() -> None:
    manifest = json.loads(_artifacts()[resolution.MANIFEST_FILE])
    observed = tuple(
        (row["semantic_name"], row["display_alias"])
        for row in manifest["canonical_masks"]
    )
    assert observed == resolution.CANONICAL_MASKS
    assert ("scaffold_only", "B3") in observed
    assert manifest["canonical_mask_tensors_materialized"] is False


def test_issue_transition_changes_exactly_four_fields() -> None:
    before = _rows(_base(resolution.PREDECESSOR_ISSUES))
    after = _result()["issue_rows"]
    mutable = {
        "successor_effective_status",
        "successor_transition_stage",
        "successor_transition_action",
        "successor_transition_evidence",
    }
    assert len(before) == len(after) == 32
    for old, new in zip(before, after):
        if old["issue_id"] != "UNKNOWN_ATOM_FEATURE_POLICY_UNRESOLVED":
            assert old == new
        else:
            assert {
                key for key in old if old[key] != new[key]
            } == mutable
            assert new["successor_effective_status"] == "resolved"
    assert before[30] == after[30]


def test_feature_semantics_known_requires_complete_success() -> None:
    success = (
        resolution.validate_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_scenario_v1(
            resolution.TrainingFeatureSemanticsResolutionScenario()
        )
    )
    failure = (
        resolution.validate_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_scenario_v1(
            dataclasses.replace(
                resolution.TrainingFeatureSemanticsResolutionScenario(),
                complete_projection_evidence=False,
            )
        )
    )
    assert success.feature_semantics_known is True
    assert failure.feature_semantics_known is False
    assert failure.unknown_issue_effective_status == "open"


def test_contract_design_readiness_is_strict() -> None:
    decision = _result()["decision"]
    assert decision.unknown_atom_policy_contract_resolved is True
    assert decision.ready_for_tensor_label_loss_mask_contract_design is True
    assert decision.ready_for_tensorization is False
    assert decision.ready_for_model_integration is False
    assert decision.ready_for_training is False


def test_runtime_is_not_integrated_and_boundaries_remain_closed() -> None:
    decision = _result()["decision"]
    manifest = json.loads(_artifacts()[resolution.MANIFEST_FILE])
    assert decision.unknown_atom_runtime_enforcement_integrated is False
    for key in (
        "tensorization_used",
        "checkpoint_access",
        "model_changed",
        "dataloader_changed",
        "forward_changed",
        "loss_changed",
        "training_used",
        "raw_read",
        "raw_write",
        "network_used",
        "download_used",
    ):
        assert manifest[key] is False


def test_failure_matrix_executes_exact32_formal_cases() -> None:
    rows = resolution.build_failure_matrix_rows_v1()
    assert [row["failure_case"] for row in rows] == list(
        resolution.FAILURE_CASES
    )
    assert len(rows) == 32
    assert all(
        row["observed_outcome"] == "invalid"
        and not row["unknown_atom_policy_contract_resolved"]
        and not row["feature_semantics_known"]
        and not row["ready_for_tensor_label_loss_mask_contract_design"]
        and not row["ready_for_tensorization"]
        and not row["ready_for_model_integration"]
        and not row["ready_for_training"]
        and row["unknown_issue_effective_status"] == "open"
        and row["fails_closed"]
        and row["verified"]
        for row in rows
    )


def test_three_builds_and_decisions_are_byte_deterministic() -> None:
    builds = [
        resolution.build_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_artifacts_v1(
            ROOT
        )
        for _ in range(3)
    ]
    assert builds[0] == builds[1] == builds[2]
    decisions = [
        resolution.derive_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1(
            ROOT
        )["decision"]
        for _ in range(3)
    ]
    assert decisions[0] == decisions[1] == decisions[2]
    serialized = [
        resolution.serialize_covapie_training_feature_semantics_and_unknown_atom_policy_resolution_decision_v1(
            decision
        )
        for decision in decisions
    ]
    assert serialized[0] == serialized[1] == serialized[2]


def test_materialized_evidence_matches_builder_and_sha_map() -> None:
    artifacts = _artifacts()
    assert tuple(artifacts) == resolution.OUTPUT_FILES
    for name, payload in artifacts.items():
        assert (ROOT / resolution.OUTPUT_ROOT / name).read_bytes() == payload
    manifest = json.loads(artifacts[resolution.MANIFEST_FILE])
    for name, digest in manifest["evidence_sha256"].items():
        assert hashlib.sha256(artifacts[name]).hexdigest() == digest


def test_isolated_import_has_no_output_or_side_effects(tmp_path: Path) -> None:
    result = subprocess.run(
        (
            sys.executable,
            "-B",
            "-c",
            "from covalent_ext import "
            "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1",
        ),
        cwd=tmp_path,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": str(SRC),
        },
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 0
    assert result.stdout == result.stderr == b""
    assert list(tmp_path.iterdir()) == []


def test_independent_checker_passes_and_is_deterministic() -> None:
    command = (sys.executable, "-B", checker.EXACT10[2].as_posix())
    environment = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": "src",
    }
    first = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    second = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert first.returncode == second.returncode == 0
    assert first.stderr == second.stderr == b""
    assert first.stdout == second.stdout
    assert b"resolution_outcome=resolved_policy_contract" in first.stdout
    assert b"source_atom_row_count=2870" in first.stdout
    assert b"ready_for_training=false" in first.stdout


def test_exact10_paths_modes_and_safety() -> None:
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
        assert _result()["decision"].outcome == "resolved_policy_contract"
        return
    real_capture = lifecycle._capture_state
    states: list[str] = []
    checker_outputs: list[bytes] = []
    targeted_pass_counts: list[int] = []

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
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "-p",
                    "no:cacheprovider",
                    checker.EXACT10[1].as_posix(),
                ),
                cwd=repository,
                env=environment,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            assert targeted.returncode == 0, targeted.stdout + targeted.stderr
            assert targeted.stderr == b""
            summary = targeted.stdout.decode().strip().splitlines()[-1]
            targeted_pass_counts.append(int(summary.split()[0]))
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
        base_commit=resolution.BASE_COMMIT,
        formal_commit_subject=resolution.FORMAL_COMMIT_SUBJECT,
        exact_paths=checker.EXACT10,
    )
    assert states == [
        "pre_commit",
        "formal_main_post_commit_unpushed",
        "formal_main_post_push",
    ]
    assert targeted_pass_counts[0] == targeted_pass_counts[1] == targeted_pass_counts[2]
    assert checker_outputs[0] == checker_outputs[1] == checker_outputs[2]
    assert report.candidate_parent == resolution.BASE_COMMIT
    assert report.candidate_subject == resolution.FORMAL_COMMIT_SUBJECT
    assert report.exact_path_count == 10
    assert report.cleanup_verified is True
