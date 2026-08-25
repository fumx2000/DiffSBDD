from __future__ import annotations

from collections import Counter
import csv
import importlib.util
import io
import json
from pathlib import Path

import networkx as nx
import pytest

from covalent_ext import (
    covapie_cumulative1000_high_yield_human_review_authority_calibration_v1
    as calibration,
)
from covalent_ext.covapie_bulk_cys_sg_dataset_expansion_v1 import parse_ccd_cif_v1


REPO = Path(__file__).resolve().parents[1]
CHECKER_SPEC = importlib.util.spec_from_file_location(
    "covapie_high_yield_calibration_checker",
    REPO
    / "scripts/check_covapie_cumulative1000_high_yield_human_review_authority_calibration_v1.py",
)
if CHECKER_SPEC is None or CHECKER_SPEC.loader is None:
    raise RuntimeError("CHECKER_MODULE_SPEC_UNAVAILABLE")
checker = importlib.util.module_from_spec(CHECKER_SPEC)
CHECKER_SPEC.loader.exec_module(checker)
DERIVED = REPO / "data/derived/covalent_small"
QUEUE = (
    DERIVED
    / "covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1"
    / "covapie_bulk_cys_sg_priority_human_review_queue_v1.csv"
)
CENSUS = QUEUE.with_name("covapie_bulk_cys_sg_cumulative_1000_model_usable_census_v1.csv")
SECOND = QUEUE.with_name("covapie_bulk_cys_sg_ranks_0501_1000_processing_outcomes_v1.json")
POSITIVE = (
    DERIVED
    / "covapie_existing_positive_runtime_and_split_closure_v1"
    / "covapie_current_runtime_model_usable_positive_index_v1.csv"
)
SUCCESSOR = (
    DERIVED
    / "covapie_batch001_completed_decision_ingestion_and_task_label_availability_v1"
    / "covapie_batch001_completed_human_decision_snapshot_v1.json"
)
CANONICAL = (
    DERIVED
    / "covapie_bulk_cys_sg_dataset_expansion_v1/bulk_pilot_v1/"
    "cross_source_canonical_event_manifest_v1.json"
)
FIRST = (
    REPO.parent
    / "covapie-state/bulk-500-controlled-execution-v1/attempt-001/"
    "cumulative_processing_view_v1.json"
)
CCD_ROOT = REPO.parent / "covapie-state/bulk-multisource-cys-sg-v1/rcsb/ccd"


def _csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _artifact_csv(artifacts: dict[str, bytes], name: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(artifacts[name].decode("utf-8"))))


@pytest.fixture(scope="module")
def artifacts() -> dict[str, bytes]:
    return calibration.build_artifacts_v1(REPO)


def _independent_outcomes() -> dict[str, dict[str, object]]:
    first = json.loads(FIRST.read_text())
    second = json.loads(SECOND.read_text())
    outcomes = {
        item["processing_outcome"]["canonical_event_id"]: item["processing_outcome"]
        for item in first["events"]
    }
    outcomes.update(
        {
            item["canonical_event_id"]: item["processing_outcome"]
            for item in second["events"]
        }
    )
    return outcomes


def _independent_decision_oracle() -> tuple[set[str], set[str]]:
    successor = json.loads(SUCCESSOR.read_text())
    negatives = {
        event["canonical_event_id"]
        for item in successor["completed_human_decisions"]
        if item["completed_lane"] == "COMPLETED_TASK_DOMAIN_NEGATIVE"
        for event in item["human_decision"]["events"]
    }
    held_unit = successor["held_out_in_progress"]["review_unit_id"]
    held_rows = [row for row in _csv(QUEUE) if row["review_unit_id"] == held_unit]
    assert len(held_rows) == 1
    in_progress = set(json.loads(held_rows[0]["canonical_event_ids_json"]))
    return negatives, in_progress


def test_independent_published_and_reconciliation_oracles(artifacts) -> None:
    queue = _csv(QUEUE)
    queue_events = {
        event for row in queue for event in json.loads(row["canonical_event_ids_json"])
    }
    positives = _csv(POSITIVE)
    runtime = {row["canonical_event_id"] for row in positives if row["current_runtime_model_usable"] == "true"}
    partial = {row["canonical_event_id"] for row in positives if row["current_runtime_model_usable"] != "true"}
    negatives, in_progress = _independent_decision_oracle()
    assert len(queue) == 131
    assert len(queue_events) == 338
    assert len(runtime) == 36
    assert len(partial) == 1
    assert len(queue_events & negatives) == 24
    assert len(queue_events & in_progress) == 9
    assert not queue_events & runtime
    assert not queue_events & partial
    expected_unreviewed = queue_events - negatives - in_progress
    rows = _artifact_csv(artifacts, calibration.RECONCILIATION)
    by_status = Counter(row["current_review_status"] for row in rows)
    assert by_status == Counter(
        {
            calibration.CURRENTLY_UNREVIEWED: len(expected_unreviewed),
            calibration.COMPLETED_HUMAN_NEGATIVE: 24,
            calibration.CURRENTLY_IN_PROGRESS: 9,
        }
    )
    assert {
        row["canonical_event_id"]
        for row in rows
        if row["current_review_status"] == calibration.CURRENTLY_UNREVIEWED
    } == expected_unreviewed


def _heavy_nx(graph: dict[str, object]) -> nx.Graph:
    result = nx.Graph()
    for atom in graph["ccd_atom_inventory"]:
        if atom["type_symbol"].upper() == "H":
            continue
        result.add_node(
            atom["atom_id"],
            element=atom["type_symbol"].upper(),
            charge=int(atom.get("charge") or 0),
            aromatic=(atom.get("aromatic_flag") or "N").upper(),
        )
    for bond in graph["ccd_bond_inventory"]:
        if bond["atom_id_1"] in result and bond["atom_id_2"] in result:
            result.add_edge(
                bond["atom_id_1"],
                bond["atom_id_2"],
                order=(bond.get("value_order") or "").upper(),
                aromatic=(bond.get("pdbx_aromatic_flag") or "N").upper(),
            )
    return result


def _independent_exact_shadow_oracle() -> tuple[set[str], set[str]]:
    queue = _csv(QUEUE)
    negatives, in_progress = _independent_decision_oracle()
    excluded = negatives | in_progress
    outcomes = _independent_outcomes()
    canonical = json.loads(CANONICAL.read_text())["canonical_events"]
    canonical_by_id = {event["canonical_event_id"]: event for event in canonical}
    positive_rows = [row for row in _csv(POSITIVE) if row["current_runtime_model_usable"] == "true"]
    reference: list[tuple[str, str, str]] = []
    reference_graphs: dict[str, dict[str, object]] = {}
    for row in positive_rows:
        event = canonical_by_id[row["canonical_event_id"]]
        component = event["ligand_component_id"]
        if component not in reference_graphs:
            reference_graphs[component] = parse_ccd_cif_v1(
                (CCD_ROOT / f"{component}.cif").read_bytes(), ccd_id=component
            )
        reference.append(
            (
                component,
                event["ligand_reactive_atom"],
                reference_graphs[component]["ccd_component_graph_sha256"],
            )
        )
    exact_events: set[str] = set()
    exact_units: set[str] = set()
    candidate_graphs: dict[str, nx.Graph] = {}
    reference_nx = {component: _heavy_nx(graph) for component, graph in reference_graphs.items()}
    cross_component_reactive_isomorphism_found = False
    for unit in queue:
        event_ids = json.loads(unit["canonical_event_ids_json"])
        if set(event_ids) & excluded:
            continue
        for event_id in event_ids:
            event = canonical_by_id[event_id]
            structural = outcomes[event_id]["structural_processing"]
            graph = structural["ccd_component_graph"]
            if any(
                event["ligand_component_id"] == component
                and event["ligand_reactive_atom"] == reactive
                and graph["ccd_component_graph_sha256"] == graph_sha
                for component, reactive, graph_sha in reference
            ):
                exact_events.add(event_id)
                exact_units.add(unit["review_unit_id"])
            candidate_key = event["ligand_component_id"] + ":" + graph["ccd_component_graph_sha256"]
            candidate_graphs.setdefault(candidate_key, _heavy_nx(graph))
            candidate_nx = candidate_graphs[candidate_key]
            for component, reactive, _sha in reference:
                if component == event["ligand_component_id"]:
                    continue
                ref_nx = reference_nx[component]
                if len(ref_nx) != len(candidate_nx) or ref_nx.number_of_edges() != candidate_nx.number_of_edges():
                    continue
                matcher = nx.algorithms.isomorphism.GraphMatcher(
                    ref_nx,
                    candidate_nx,
                    node_match=lambda left, right: left == right,
                    edge_match=lambda left, right: left == right,
                )
                if any(
                    mapping.get(reactive) == event["ligand_reactive_atom"]
                    for mapping in matcher.isomorphisms_iter()
                ):
                    cross_component_reactive_isomorphism_found = True
    assert cross_component_reactive_isomorphism_found is False
    return exact_events, exact_units


def test_independent_all36_strict_shadow_oracle(artifacts) -> None:
    exact_events, exact_units = _independent_exact_shadow_oracle()
    shadow = _artifact_csv(artifacts, calibration.SHADOW)
    strict = {row["canonical_event_id"] for row in shadow if row["strict_shadow_match"] == "true"}
    strict_units = {row["review_unit_id"] for row in shadow if row["strict_shadow_match"] == "true"}
    assert strict == exact_events
    assert strict_units == exact_units
    assert len(strict) == 5
    assert len(strict_units) == 3
    assert {row["shadow_status"] for row in shadow if row["strict_shadow_match"] == "true"} == {
        calibration.EXACT_CENTER
    }
    assert all(row["positive_reference_event_count"] == "36" for row in shadow)


def _unit_evidence() -> list[dict[str, object]]:
    queue = _csv(QUEUE)
    outcomes = _independent_outcomes()
    negatives, in_progress = _independent_decision_oracle()
    excluded = negatives | in_progress
    evidence = []
    for row in queue:
        event_ids = json.loads(row["canonical_event_ids_json"])
        if set(event_ids) & excluded:
            continue
        structural = outcomes[event_ids[0]]["structural_processing"]
        evidence.append(
            {
                "unit": row["review_unit_id"],
                "rank": int(row["priority_rank"]),
                "yield": len(event_ids),
                "events": event_ids,
                "graph": structural["ccd_component_graph"]["ccd_component_graph_sha256"],
                "radius2": structural.get("reactive_center_radius2_sha256") or "",
            }
        )
    return evidence


def test_independent_selection_oracle(artifacts) -> None:
    exact_events, _units = _independent_exact_shadow_oracle()
    evidence = _unit_evidence()
    shadow_units = [unit for unit in evidence if set(unit["events"]) & exact_events]
    lane_a = min(shadow_units, key=lambda unit: (-unit["yield"], unit["rank"], unit["unit"]))
    lane_b = min(
        (unit for unit in evidence if unit["unit"] != lane_a["unit"]),
        key=lambda unit: (-unit["yield"], unit["rank"], unit["unit"]),
    )
    lane_c = min(
        (
            unit
            for unit in evidence
            if unit["unit"] not in {lane_a["unit"], lane_b["unit"]}
            and unit["graph"]
            and unit["radius2"]
            and all(
                unit["graph"] != selected["graph"]
                and unit["radius2"] != selected["radius2"]
                for selected in (lane_a, lane_b)
            )
        ),
        key=lambda unit: (-unit["yield"], unit["rank"], unit["unit"]),
    )
    selected = _artifact_csv(artifacts, calibration.SELECTED)
    assert [row["review_unit_id"] for row in selected] == [
        lane_a["unit"],
        lane_b["unit"],
        lane_c["unit"],
    ]
    assert [int(row["effective_single_decision_event_yield"]) for row in selected] == [
        lane_a["yield"],
        lane_b["yield"],
        lane_c["yield"],
    ]
    assert len(selected) <= 3
    assert len({row["review_unit_id"] for row in selected}) == len(selected)


@pytest.mark.parametrize(
    "status",
    [
        calibration.COMPLETED_HUMAN_POSITIVE,
        calibration.COMPLETED_HUMAN_NEGATIVE,
        calibration.CURRENTLY_IN_PROGRESS,
        calibration.CURRENT_RUNTIME_MODEL_USABLE,
        calibration.PUBLISHED_EXACT_AUTO_NEGATIVE,
    ],
)
def test_selection_rejects_every_ineligible_current_status(status) -> None:
    selected = [{"review_unit_id": "U", "canonical_event_ids": ["E"]}]
    rows = [{"canonical_event_id": "E", "current_review_status": status}]
    with pytest.raises(calibration.CalibrationSafetyError, match="INELIGIBLE"):
        calibration.validate_selection_against_reconciliation_v1(
            selected=selected, reconciliation_rows=rows
        )


def test_selection_rejects_silent_drop_duplicate_and_double_assignment() -> None:
    with pytest.raises(calibration.CalibrationSafetyError, match="MISSING"):
        calibration.validate_selection_against_reconciliation_v1(
            selected=[{"review_unit_id": "U", "canonical_event_ids": ["MISSING"]}],
            reconciliation_rows=[
                {
                    "canonical_event_id": "E",
                    "current_review_status": calibration.CURRENTLY_UNREVIEWED,
                }
            ],
        )
    with pytest.raises(calibration.CalibrationSafetyError, match="DUPLICATE"):
        calibration.validate_selection_against_reconciliation_v1(
            selected=[{"review_unit_id": "U", "canonical_event_ids": ["E"]}],
            reconciliation_rows=[
                {"canonical_event_id": "E", "current_review_status": calibration.CURRENTLY_UNREVIEWED},
                {"canonical_event_id": "E", "current_review_status": calibration.CURRENTLY_UNREVIEWED},
            ],
        )
    with pytest.raises(calibration.CalibrationSafetyError, match="TWO"):
        calibration.validate_selection_against_reconciliation_v1(
            selected=[
                {"review_unit_id": "U1", "canonical_event_ids": ["E"]},
                {"review_unit_id": "U2", "canonical_event_ids": ["E"]},
            ],
            reconciliation_rows=[
                {"canonical_event_id": "E", "current_review_status": calibration.CURRENTLY_UNREVIEWED}
            ],
        )


@pytest.mark.parametrize(
    "relative",
    [calibration.DECISIONS, calibration.QUEUE, calibration.POSITIVE_INDEX],
)
def test_bound_authority_sha_drift_fails_closed(monkeypatch, relative) -> None:
    monkeypatch.setitem(calibration.BOUND_REPOSITORY_SHA256, relative, "0" * 64)
    with pytest.raises(calibration.CalibrationSafetyError, match="SHA256_MISMATCH"):
        calibration.verify_bound_inputs_v1(REPO)


def _graph(component: str, atoms: list[tuple[str, str]], bonds: list[tuple[str, str]]) -> dict[str, object]:
    payload = {
        "ccd_id": component,
        "ccd_atom_inventory": [
            {"atom_id": atom, "type_symbol": element, "charge": 0, "aromatic_flag": "N"}
            for atom, element in atoms
        ],
        "ccd_bond_inventory": [
            {
                "atom_id_1": left,
                "atom_id_2": right,
                "value_order": "SING",
                "pdbx_aromatic_flag": "N",
            }
            for left, right in bonds
        ],
    }
    payload["ccd_component_graph_sha256"] = calibration._sha(calibration._json_bytes(payload))
    return payload


def test_shadow_rejects_ccd_name_only_radius_only_and_reactive_mismatch() -> None:
    reference = _graph("X", [("A", "C"), ("B", "O")], [("A", "B")])
    graph_drift = _graph("X", [("A", "C"), ("B", "N")], [("A", "B")])
    name_only = calibration.compare_graph_shadow_v1(
        candidate_component_id="X",
        candidate_graph=graph_drift,
        candidate_reactive_atom="A",
        reference_component_id="X",
        reference_graph=reference,
        reference_reactive_atom="A",
        reference_roles=None,
    )
    assert name_only["status"] == calibration.REFERENCE_CONFLICT
    unrelated = _graph("Y", [("C", "C"), ("D", "C")], [("C", "D")])
    radius_only = calibration.compare_graph_shadow_v1(
        candidate_component_id="Y",
        candidate_graph=unrelated,
        candidate_reactive_atom="C",
        reference_component_id="X",
        reference_graph=reference,
        reference_reactive_atom="A",
        reference_roles=None,
    )
    assert radius_only["status"] == calibration.NO_SHADOW
    reactive_mismatch = calibration.compare_graph_shadow_v1(
        candidate_component_id="X",
        candidate_graph=reference,
        candidate_reactive_atom="B",
        reference_component_id="X",
        reference_graph=reference,
        reference_reactive_atom="A",
        reference_roles=None,
    )
    assert reactive_mismatch["status"] == calibration.EXACT_COMPONENT
    assert reactive_mismatch["status"] != calibration.EXACT_CENTER


def test_nonunique_automorphism_is_ambiguous_and_missing_role_atom_fails() -> None:
    reference = _graph(
        "R",
        [(f"R{i}", "C") for i in range(4)],
        [("R0", "R1"), ("R1", "R2"), ("R2", "R3"), ("R3", "R0")],
    )
    candidate = _graph(
        "C",
        [(f"C{i}", "C") for i in range(4)],
        [("C0", "C1"), ("C1", "C2"), ("C2", "C3"), ("C3", "C0")],
    )
    roles = {
        "scaffold_atom_ids": ["R1"],
        "linker_atom_ids": ["R2"],
        "warhead_atom_ids": ["R0", "R3"],
        "role_profile": "STRICT_LINKER_PRESENT_V1",
        "transfer_eligible": True,
    }
    result = calibration.compare_graph_shadow_v1(
        candidate_component_id="C",
        candidate_graph=candidate,
        candidate_reactive_atom="C0",
        reference_component_id="R",
        reference_graph=reference,
        reference_reactive_atom="R0",
        reference_roles=roles,
    )
    assert result["status"] == calibration.AMBIGUOUS
    assert result["distinct_role_assignment_count"] > 1
    broken = dict(roles)
    broken["scaffold_atom_ids"] = ["MISSING"]
    with pytest.raises(calibration.CalibrationSafetyError, match="ROLE_ATOM_MISSING"):
        calibration.compare_graph_shadow_v1(
            candidate_component_id="C",
            candidate_graph=candidate,
            candidate_reactive_atom="C0",
            reference_component_id="R",
            reference_graph=reference,
            reference_reactive_atom="R0",
            reference_roles=broken,
        )


@pytest.mark.parametrize(
    "field",
    ["shadow_authoritative", "shadow_model_usable", "shadow_training_admitted"],
)
def test_shadow_cannot_be_promoted(field, artifacts) -> None:
    mutated = dict(artifacts)
    rows = _artifact_csv(mutated, calibration.SHADOW)
    rows[0][field] = "true"
    mutated[calibration.SHADOW] = calibration._csv_bytes(calibration.SHADOW_HEADER, rows)
    with pytest.raises(calibration.CalibrationSafetyError, match="SHADOW"):
        calibration.validate_artifacts_v1(mutated)


def test_packet_is_complete_blank_and_non_authoritative(artifacts) -> None:
    packet = json.loads(artifacts[calibration.PACKET])
    assert packet["authority_boundary"] == {
        "human_review_decision_created": False,
        "new_negative_authority_created": False,
        "new_positive_authority_created": False,
        "new_reaction_family_authority_created": False,
        "new_reusable_chemistry_authority_created": False,
        "new_warhead_rule_authority_created": False,
        "shadow_is_authority": False,
        "shadow_is_model_usable": False,
        "shadow_is_training_admission": False,
    }
    for unit in packet["review_units"]:
        assert len(unit["events"]) == unit["raw_event_count"]
        assert unit["source_SHA_bindings"]
        assert all({"path", "sha256", "byte_count"} <= set(binding) for binding in unit["source_SHA_bindings"])
        form = unit["human_review_form"]
        assert form["training_domain_relevance_decision"] == "UNDECIDED"
        assert form["warhead_atom_ids"] == []
        assert form["scaffold_atom_ids"] == []
        assert form["linker_atom_ids"] == []
        assert all(
            event["event_training_use_decision"] == "UNDECIDED"
            for event in form["event_training_use_decisions"]
        )
        assert unit["hypothetical_unlock_simulation"]["status"] == "HYPOTHETICAL_NOT_AUTHORITY"
        for event in unit["events"]:
            assert event["selected_struct_conn_identity"]
            assert event["POST_distance_angstrom"] > 0
            assert event["exact_pair_evidence"]["explicit_covalent_evidence"] is True
            assert len(event["negative_rule_evaluations"]) == 2
            assert "event_specific_anomaly_flags" in event


def test_unit_coherence_and_determinism(artifacts) -> None:
    summary = json.loads(artifacts[calibration.SUMMARY])
    assert summary["unit_coherence"] == {
        "coherent_unit_count": 126,
        "eligible_unit_count": 126,
        "unit_requires_subdivision_count": 0,
    }
    assert artifacts == calibration.build_artifacts_v1(REPO)


def test_candidate_and_published_profiles() -> None:
    candidate = {
        "branch": "main",
        "HEAD": calibration.BASELINE_HEAD,
        "HEAD_parent": calibration.BASELINE_PARENT,
        "HEAD_tree": calibration.BASELINE_TREE,
        "HEAD_subject": calibration.BASELINE_SUBJECT,
        "origin_main": calibration.BASELINE_HEAD,
        "ahead": 0,
        "behind": 0,
        "tracked_modifications": [],
        "staged": [],
        "untracked": sorted(calibration.AUTHORIZED_PATHS),
        "published_diff_statuses": [],
        "published_diff_modes": [],
        "published_diff_paths": [],
    }
    assert (
        calibration.classify_repository_profile_v1(candidate)
        == "candidate_precommit_untracked"
    )

    published = {
        "branch": "main",
        "HEAD": "f" * 40,
        "HEAD_parent": calibration.BASELINE_HEAD,
        "HEAD_tree": "0" * 40,
        "HEAD_subject": calibration.PUBLICATION_SUBJECT,
        "origin_main": "f" * 40,
        "ahead": 0,
        "behind": 0,
        "tracked_modifications": [],
        "staged": [],
        "untracked": [],
        "published_diff_statuses": ["A"] * 9,
        "published_diff_modes": ["100644"] * 9,
        "published_diff_paths": sorted(calibration.AUTHORIZED_PATHS),
    }
    assert calibration.classify_repository_profile_v1(published) == "published_successor"
    published["published_diff_modes"] = ["100755"] + ["100644"] * 8
    with pytest.raises(calibration.CalibrationSafetyError):
        calibration.classify_repository_profile_v1(published)


def test_checker_accepts_published_profile_and_rejects_third_profile(
    monkeypatch,
) -> None:
    materialized = {
        "profile": "published_successor",
        "sha256": {},
        "summary": {
            "authority_and_execution_safety": {},
            "reconciliation": {},
            "strict_shadow": {},
            "selection": {
                "units": [
                    {"selection_lane": "A"},
                    {"selection_lane": "B"},
                    {"selection_lane": "C"},
                ]
            },
        },
    }
    monkeypatch.setattr(
        checker.calibration,
        "check_materialized_v1",
        lambda _repo_root: materialized,
    )
    result = checker.run_check(REPO)
    assert result["actual_repository_profile"] == "published_successor"
    assert result["actual_repository_profile_supported"] is True

    materialized["profile"] = "committed_unpushed"
    with pytest.raises(calibration.CalibrationSafetyError, match="ACTUAL_PROFILE_INVALID"):
        checker.run_check(REPO)


def _published_git_outputs(raw_diff: str) -> dict[tuple[str, ...], str]:
    head = "f" * 40
    return {
        ("rev-parse", "HEAD"): head,
        ("rev-parse", "HEAD^"): calibration.BASELINE_HEAD,
        ("rev-parse", "refs/remotes/origin/main"): head,
        (
            "rev-list",
            "--left-right",
            "--count",
            "HEAD...refs/remotes/origin/main",
        ): "0 0",
        ("status", "--porcelain=v1", "--untracked-files=all"): "",
        ("diff", "--name-only"): "",
        ("diff", "--cached", "--name-only"): "",
        ("ls-files", "--others", "--exclude-standard"): "",
        ("branch", "--show-current"): "main",
        ("rev-parse", "HEAD^{tree}"): "e" * 40,
        ("log", "-1", "--format=%s"): calibration.PUBLICATION_SUBJECT,
        (
            "diff-tree",
            "--no-commit-id",
            "-r",
            "--raw",
            "-z",
            "--no-abbrev",
            "--find-renames",
            "--find-copies-harder",
            calibration.BASELINE_HEAD,
            head,
        ): raw_diff,
    }


def _raw_published_diff(*, changed_status: str = "A", changed_mode: str = "100644") -> str:
    records = []
    for index, path in enumerate(sorted(calibration.AUTHORIZED_PATHS)):
        if index == 0 and changed_status == "M":
            old_mode = "100644"
            old_object = "2" * 40
        else:
            old_mode = "000000"
            old_object = "0" * 40
        new_mode = changed_mode if index == 0 else "100644"
        status = changed_status if index == 0 else "A"
        records.extend(
            [
                f":{old_mode} {new_mode} {old_object} {'1' * 40} {status}",
                path,
            ]
        )
    return "\0".join(records) + "\0"


def test_observer_classifies_real_published_successor_diff(monkeypatch) -> None:
    outputs = _published_git_outputs(_raw_published_diff())

    def fake_git(_repo_root: Path, *arguments: str) -> str:
        return outputs[arguments]

    monkeypatch.setattr(calibration, "_git", fake_git)
    observation = calibration.observe_repository_state_v1(REPO)
    assert observation["published_diff_statuses"] == ["A"] * 9
    assert observation["published_diff_modes"] == ["100644"] * 9
    assert observation["published_diff_paths"] == sorted(calibration.AUTHORIZED_PATHS)
    assert calibration.classify_repository_profile_v1(observation) == "published_successor"


@pytest.mark.parametrize(
    ("changed_status", "changed_mode"),
    [("M", "100644"), ("A", "100755")],
)
def test_observer_rejects_wrong_published_status_or_mode(
    monkeypatch, changed_status: str, changed_mode: str
) -> None:
    outputs = _published_git_outputs(
        _raw_published_diff(
            changed_status=changed_status,
            changed_mode=changed_mode,
        )
    )

    def fake_git(_repo_root: Path, *arguments: str) -> str:
        return outputs[arguments]

    monkeypatch.setattr(calibration, "_git", fake_git)
    observation = calibration.observe_repository_state_v1(REPO)
    with pytest.raises(calibration.CalibrationSafetyError, match="UNSUPPORTED"):
        calibration.classify_repository_profile_v1(observation)


def test_observer_fails_closed_on_malformed_published_diff(monkeypatch) -> None:
    outputs = _published_git_outputs(
        ":000000 100644 0000000 malformed A\0authorized/path\0"
    )

    def fake_git(_repo_root: Path, *arguments: str) -> str:
        return outputs[arguments]

    monkeypatch.setattr(calibration, "_git", fake_git)
    with pytest.raises(calibration.CalibrationSafetyError, match="MALFORMED"):
        calibration.observe_repository_state_v1(REPO)
