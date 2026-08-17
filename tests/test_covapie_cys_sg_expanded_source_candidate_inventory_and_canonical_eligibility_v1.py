from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from covalent_ext import (
    covapie_cys_sg_expanded_source_candidate_inventory_and_canonical_eligibility_v1
    as stage_a,
)
from covalent_ext import (
    covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1
    as exact10_owner,
)


def _rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return (
        stage_a.build_covapie_cys_sg_expanded_source_candidate_inventory_and_canonical_eligibility_artifacts_v1()
    )


@pytest.fixture(scope="module")
def registry(artifacts: dict[str, bytes]) -> list[dict[str, str]]:
    return _rows(artifacts[stage_a.CANDIDATE_FILE])


@pytest.fixture(scope="module")
def issues(artifacts: dict[str, bytes]) -> list[dict[str, str]]:
    return _rows(artifacts[stage_a.ISSUE_FILE])


@pytest.fixture(scope="module")
def manifest(artifacts: dict[str, bytes]) -> dict[str, object]:
    return json.loads(artifacts[stage_a.MANIFEST_FILE])


def test_design_report_and_baseline_bound_input_contract(
    manifest: dict[str, object],
) -> None:
    assert stage_a.BASELINE_COMMIT == "de6767f730e10e90af910def8a3f2d1a43eecfed"
    assert stage_a.DESIGN_REPORT_SHA256 == (
        "1851e488426aa7d034a903c38e6eb6826aa013da8b083cfeb7ea936b291426d1"
    )
    assert manifest["baseline_commit"] == stage_a.BASELINE_COMMIT
    assert manifest["design_report_sha256"] == stage_a.DESIGN_REPORT_SHA256
    assert str(manifest["design_report_path"]).startswith("state://")
    evidence = manifest["input_evidence_identities"]
    assert isinstance(evidence, list)
    identities = [row["path_or_authority_identity"] for row in evidence]
    assert identities == sorted(identities)
    assert all(not identity.startswith("/") for identity in identities)
    assert len(evidence) == len(stage_a.FROZEN_INPUT_SHA256) + 3
    assert all(len(row["sha256"]) == 64 for row in evidence)


def test_source_sha_contract_fails_closed() -> None:
    stage_a.verify_payload_sha256_v1(b"a", hashlib.sha256(b"a").hexdigest(), "x")
    with pytest.raises(ValueError, match="STAGE_A_SOURCE_SHA_MISMATCH"):
        stage_a.verify_payload_sha256_v1(b"a", hashlib.sha256(b"b").hexdigest(), "x")


def test_successor_build_uses_frozen_inputs_without_live_git_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_git = stage_a._git

    def frozen_baseline_git(repo_root: Path, *args: str) -> bytes:
        if (
            len(args) == 2
            and args[0] == "show"
            and args[1].startswith(stage_a.BASELINE_COMMIT + ":")
        ):
            return original_git(repo_root, *args)
        raise AssertionError(f"live Git identity consulted: {args!r}")

    monkeypatch.setattr(stage_a, "_git", frozen_baseline_git)
    successor_artifacts = (
        stage_a.build_covapie_cys_sg_expanded_source_candidate_inventory_and_canonical_eligibility_artifacts_v1()
    )
    canonical_root = stage_a.REPO_ROOT / stage_a.OUTPUT_ROOT
    assert successor_artifacts == {
        filename: (canonical_root / filename).read_bytes()
        for filename in stage_a.OUTPUT_FILES
    }


def test_candidate_union_cardinality_denominators_and_unique_ids(
    registry: list[dict[str, str]], manifest: dict[str, object],
) -> None:
    assert len(registry) == 28
    assert len({row["canonical_candidate_id"] for row in registry}) == 28
    assert [int(row["candidate_registry_index"]) for row in registry] == list(
        range(1, 29)
    )
    assert manifest["registry_candidate_count"] == 28
    assert manifest["current11_gold_count"] == 11
    assert manifest["non_gold_expansion_candidate_count"] == 17
    assert sum(row["dataset_confidence_tier"] == "GOLD" for row in registry) == 11


def test_direct_local_candidates_are_nonoverlapping_and_not_double_counted(
    registry: list[dict[str, str]], manifest: dict[str, object],
) -> None:
    expected = {("6DI9", "GJJ"), ("5F2E", "5UT"), ("6OIM", "MOV")}
    for identity in expected:
        matches = [
            row for row in registry
            if (row["pdb_id"], row["ligand_component_id"]) == identity
        ]
        assert len(matches) == 1
        assert matches[0]["source_identity"] == "PDB/mmCIF direct"
        assert matches[0]["source_provenance_identities"] == (
            "PDB/mmCIF direct|local curated"
        )
        assert matches[0]["registry_disposition"] == "ELIGIBLE_FOR_STAGE_B"
    assert manifest["source_counts"] == {
        "CovPDB": 25,
        "CovBinderInPDB": 0,
        "CovalentInDB": 0,
        "PDB/mmCIF direct": 3,
        "local curated": 0,
    }
    assert manifest["source_provenance_identity_counts"]["local curated"] == 3


def test_current11_exact11_are_protected_gold_references(
    registry: list[dict[str, str]], manifest: dict[str, object],
) -> None:
    expected = {
        ("6BV6", "JUG"),
        ("6BV8", "JUG"),
        ("6BV5", "JUG"),
        ("1AEC", "E64"),
        ("1AIM", "ZYA"),
        ("1AU3", "PCM"),
        ("1AU4", "INP"),
        ("1AYU", "INA"),
        ("1AYV", "IN6"),
        ("1AYW", "IN3"),
        ("1B02", "UFP"),
    }
    gold = [row for row in registry if row["dataset_confidence_tier"] == "GOLD"]
    assert {(row["pdb_id"], row["ligand_component_id"]) for row in gold} == expected
    assert all(row["golden_set_id_or_none"] == stage_a.GOLDEN_SET_ID for row in gold)
    assert all(row["registry_disposition"] == "GOLD_REFERENCE" for row in gold)
    assert all(row["registry_disposition"] != "ELIGIBLE_FOR_STAGE_B" for row in gold)
    assert manifest["gold_reference_count"] == 11


def test_known_1atk_duplicate_stays_visible_and_is_not_eligible(
    registry: list[dict[str, str]], manifest: dict[str, object],
) -> None:
    rows = [
        row for row in registry
        if (row["pdb_id"], row["ligand_component_id"]) == ("1ATK", "E64")
    ]
    assert len(rows) == 1
    row = rows[0]
    assert row["exact_pair_evidenced"] == "true"
    assert row["current11_gold_match"] == "CYS_SG_SAMPLE_INDEX_000004"
    assert row["gold_duplicate_status"] == "KNOWN_LOWER_PRIORITY_GOLD_DUPLICATE"
    assert row["registry_disposition"] == "REJECT"
    assert manifest["known_gold_duplicate_count"] == 1


def test_exact_pair_evidence_denominators_are_separate(
    registry: list[dict[str, str]], manifest: dict[str, object],
) -> None:
    exact = [row for row in registry if row["exact_pair_evidenced"] == "true"]
    assert len(exact) == 15
    assert sum(row["dataset_confidence_tier"] == "GOLD" for row in exact) == 11
    assert sum(row["dataset_confidence_tier"] != "GOLD" for row in exact) == 4
    assert manifest["exact_pair_evidenced_total_count"] == 15
    assert manifest["exact_pair_evidenced_gold_count"] == 11
    assert manifest["exact_pair_evidenced_non_gold_count"] == 4


def test_all_non_gold_rows_have_one_bounded_disposition(
    registry: list[dict[str, str]], manifest: dict[str, object],
) -> None:
    non_gold = [row for row in registry if row["dataset_confidence_tier"] != "GOLD"]
    assert len(non_gold) == 17
    assert all(
        row["registry_disposition"]
        in {"ELIGIBLE_FOR_STAGE_B", "HUMAN_REVIEW_REQUIRED", "REJECT"}
        for row in non_gold
    )
    assert manifest["eligible_for_stage_b_count"] == 3
    assert manifest["human_review_required_count"] == 12
    assert manifest["reject_count"] == 2
    assert manifest["all_non_gold_candidates_disposition_complete"] is True
    for row in registry:
        for field in stage_a.COMPONENT_FIELDS:
            assert row[field]
            assert row[field].replace("_", "").isalnum()


def test_review_and_reject_issue_coverage_and_fundamental_separation(
    registry: list[dict[str, str]],
    issues: list[dict[str, str]],
    manifest: dict[str, object],
) -> None:
    issue_ids = {row["canonical_candidate_id"] for row in issues}
    review_or_reject = [
        row for row in registry
        if row["dataset_confidence_tier"] != "GOLD"
        and row["registry_disposition"] in {"HUMAN_REVIEW_REQUIRED", "REJECT"}
    ]
    assert all(row["canonical_candidate_id"] in issue_ids for row in review_or_reject)
    eligible_ids = {
        row["canonical_candidate_id"] for row in registry
        if row["registry_disposition"] == "ELIGIBLE_FOR_STAGE_B"
    }
    fundamental_ids = {
        row["canonical_candidate_id"] for row in issues
        if row["fundamental_reject"] == "true"
    }
    assert eligible_ids.isdisjoint(fundamental_ids)
    assert len(issues) == manifest["issue_row_count"] == 15
    assert manifest["all_reject_review_have_issue_rows"] is True


def test_6vwe_formula_rh_is_not_model_graph_inclusion_or_auto_reject(
    registry: list[dict[str, str]], issues: list[dict[str, str]],
) -> None:
    row = next(
        row for row in registry
        if (row["pdb_id"], row["ligand_component_id"]) == ("6VWE", "JY1")
    )
    assert row["source_formula_contains_Rh"] == "true"
    assert row["canonical_model_graph_contains_Rh"] == "EVIDENCE_NOT_AVAILABLE"
    assert row["exact10_status"] == (
        "EXACT10_FORMULA_UNSUPPORTED_NODE_INCLUSION_UNRESOLVED"
    )
    assert row["registry_disposition"] == "HUMAN_REVIEW_REQUIRED"
    rh_issue = next(
        issue for issue in issues
        if issue["canonical_candidate_id"] == row["canonical_candidate_id"]
        and issue["issue_code"]
        == "EXACT10_FORMULA_RH_GRAPH_INCLUSION_UNRESOLVED"
    )
    assert rh_issue["fundamental_reject"] == "false"
    assert rh_issue["review_required"] == "true"


def test_authoritative_unsupported_non_h_node_rejects_exact10() -> None:
    decision = stage_a.evaluate_exact10_model_bound_graph_v1(("C", "Rh"))
    assert decision.canonical_graph_evidence_available is True
    assert decision.sample_rejected is True
    assert decision.unsupported_or_invalid_node_count == 1
    assert decision.status == "EXACT10_MODEL_BOUND_GRAPH_REJECTED"


def test_explicit_h_is_excluded_without_new_channel_or_fallback(
    manifest: dict[str, object],
) -> None:
    decision = stage_a.evaluate_exact10_model_bound_graph_v1(("H", "C"))
    assert decision.sample_rejected is False
    assert decision.excluded_explicit_hydrogen_count == 1
    assert decision.retained_heavy_atom_count == 1
    assert exact10_owner.CHECKPOINT_TOKEN_TO_INDEX == {
        "C": 0,
        "N": 1,
        "O": 2,
        "S": 3,
        "B": 4,
        "Br": 5,
        "Cl": 6,
        "P": 7,
        "I": 8,
        "F": 9,
    }
    assert "H" not in exact10_owner.CHECKPOINT_TOKEN_TO_INDEX
    assert "other" not in exact10_owner.CHECKPOINT_TOKEN_TO_INDEX
    assert "unknown" not in exact10_owner.CHECKPOINT_TOKEN_TO_INDEX
    assert manifest["unknown_other_channel_added"] is False
    assert manifest["zero_vector_fallback_added"] is False


def test_missing_exact_event_never_silently_passes(
    registry: list[dict[str, str]],
) -> None:
    missing = [
        row for row in registry
        if row["reactive_pair_status"] == "REACTIVE_PAIR_EVIDENCE_MISSING"
    ]
    assert missing
    assert all(row["registry_disposition"] == "HUMAN_REVIEW_REQUIRED" for row in missing)


def test_manifest_counts_and_output_hashes_match_serialized_rows(
    artifacts: dict[str, bytes],
    registry: list[dict[str, str]],
    issues: list[dict[str, str]],
    manifest: dict[str, object],
) -> None:
    assert manifest["registry_candidate_count"] == len(registry)
    assert manifest["issue_row_count"] == len(issues)
    for filename in (stage_a.CANDIDATE_FILE, stage_a.ISSUE_FILE):
        assert manifest["deterministic_output_hashes"][filename] == hashlib.sha256(
            artifacts[filename]
        ).hexdigest()
    assert manifest["manifest_self_sha256_recorded"] is False


def test_second_build_and_materialization_are_byte_identical(
    artifacts: dict[str, bytes], tmp_path: Path,
) -> None:
    second = (
        stage_a.build_covapie_cys_sg_expanded_source_candidate_inventory_and_canonical_eligibility_artifacts_v1()
    )
    assert second == artifacts
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    stage_a.materialize_covapie_cys_sg_expanded_source_candidate_inventory_and_canonical_eligibility_v1(
        first_root
    )
    stage_a.materialize_covapie_cys_sg_expanded_source_candidate_inventory_and_canonical_eligibility_v1(
        second_root
    )
    for filename in stage_a.OUTPUT_FILES:
        assert (first_root / filename).read_bytes() == (second_root / filename).read_bytes()
        assert (first_root / filename).read_bytes() == artifacts[filename]
        assert stat.S_IMODE((first_root / filename).stat().st_mode) == 0o644
    assert stat.S_IMODE(first_root.stat().st_mode) == 0o755


def test_import_has_no_writes_network_or_heavy_chemistry_side_effects(
    tmp_path: Path,
) -> None:
    module_name = (
        "covalent_ext.covapie_cys_sg_expanded_source_candidate_inventory_"
        "and_canonical_eligibility_v1"
    )
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = os.pathsep.join(
        (str(stage_a.REPO_ROOT), str(stage_a.REPO_ROOT / "src"))
    )
    result = subprocess.run(
        (sys.executable, "-c", f"import {module_name}"),
        cwd=tmp_path,
        env=env,
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert list(tmp_path.iterdir()) == []
    source = Path(stage_a.__file__).read_text(encoding="utf-8").lower()
    assert "import requests" not in source
    assert "import urllib" not in source
    assert "import rdkit" not in source


def test_eight_pilot_identities_and_readiness_freezes(
    manifest: dict[str, object],
) -> None:
    assert manifest["eight_pilot_identities_present"] is True
    assert len(manifest["eight_pilot_identity_to_candidate_id"]) == 8
    assert manifest["registered_source_identity_count"] == 5
    assert manifest["partially_operational_local_source_path_count"] == 3
    assert manifest["ready_for_stage_a_publication"] is True
    assert manifest["ready_for_stage_b_automated_label_and_geometry_pilot"] is True
    assert manifest["ready_for_bulk_expansion"] is False
    assert manifest["ready_for_geometry_loss_activation"] is False
    assert manifest["ready_for_formal_training"] is False
    assert manifest["ready_for_training"] is False


def test_geometry_model_and_training_execution_are_hard_false(
    manifest: dict[str, object],
) -> None:
    for field in (
        "geometry_executed",
        "geometry_loss_activation",
        "inverse_reaction_templates_created",
        "rdkit_minimization_executed",
        "model_executed",
        "model_forward",
        "backward",
        "optimizer_step",
        "trainer_fit",
        "rl",
        "training_executed",
        "bulk_download_executed",
    ):
        assert manifest[field] is False
    assert manifest["geometry_weight"] == 0.0
