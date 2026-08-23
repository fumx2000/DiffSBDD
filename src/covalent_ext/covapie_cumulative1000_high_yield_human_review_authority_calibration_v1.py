"""Prepare three high-yield cumulative1000 human-review calibration units.

This successor is deliberately non-authoritative.  It reconciles the frozen
review queue with current decisions, performs read-only positive-shadow
comparisons, and emits blank human-review forms.  It never changes admission,
split, role, reaction-family, warhead-rule, or negative-rule authority.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any

import networkx as nx

from covalent_ext.covapie_bulk_cys_sg_dataset_expansion_v1 import parse_ccd_cif_v1


SCHEMA_VERSION = (
    "covapie_cumulative1000_high_yield_human_review_authority_calibration_v1"
)
BASELINE_HEAD = "66199a5fac0c03d527187bb29abf0104311fc654"
BASELINE_PARENT = "4a648e83e066d7d5d90467b3f4f3fee3eb69b09b"
BASELINE_TREE = "d5b0d08a7f2ff7d579d8164b2ce96b53565adbaa"
BASELINE_SUBJECT = "add CovaPIE existing positive runtime and split closure v1"
PUBLICATION_SUBJECT = (
    "add CovaPIE cumulative1000 high-yield human review authority calibration v1"
)

OUTPUT_ROOT_RELATIVE = Path(
    "data/derived/covalent_small/"
    "covapie_cumulative1000_high_yield_human_review_authority_calibration_v1"
)
RECONCILIATION = "covapie_cumulative1000_current_review_status_reconciliation_v1.csv"
SHADOW = "covapie_cumulative1000_strict_positive_shadow_inventory_v1.csv"
SELECTED = "covapie_cumulative1000_selected_calibration_units_v1.csv"
PACKET = "covapie_cumulative1000_human_review_calibration_packet_v1.json"
MANIFEST = "covapie_cumulative1000_high_yield_authority_calibration_manifest_v1.json"
SUMMARY = "covapie_cumulative1000_high_yield_authority_calibration_summary_v1.json"
OUTPUT_FILENAMES = (RECONCILIATION, SHADOW, SELECTED, PACKET, MANIFEST, SUMMARY)

SOURCE_RELATIVE = Path(
    "src/covalent_ext/"
    "covapie_cumulative1000_high_yield_human_review_authority_calibration_v1.py"
)
CHECKER_RELATIVE = Path(
    "scripts/"
    "check_covapie_cumulative1000_high_yield_human_review_authority_calibration_v1.py"
)
TEST_RELATIVE = Path(
    "tests/"
    "test_covapie_cumulative1000_high_yield_human_review_authority_calibration_v1.py"
)
AUTHORIZED_PATHS = frozenset(
    {
        SOURCE_RELATIVE.as_posix(),
        CHECKER_RELATIVE.as_posix(),
        TEST_RELATIVE.as_posix(),
        *((OUTPUT_ROOT_RELATIVE / name).as_posix() for name in OUTPUT_FILENAMES),
    }
)

DERIVED = Path("data/derived/covalent_small")
CLOSURE_ROOT = DERIVED / "covapie_existing_positive_runtime_and_split_closure_v1"
POSITIVE_INDEX = CLOSURE_ROOT / "covapie_current_runtime_model_usable_positive_index_v1.csv"
CLOSURE_MANIFEST = CLOSURE_ROOT / "covapie_existing_positive_runtime_and_split_closure_manifest_v1.json"
CLOSURE_SUMMARY = CLOSURE_ROOT / "covapie_existing_positive_runtime_and_split_closure_summary_v1.json"
SCALEUP_ROOT = DERIVED / "covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_v1"
CENSUS = SCALEUP_ROOT / "covapie_bulk_cys_sg_cumulative_1000_model_usable_census_v1.csv"
QUEUE = SCALEUP_ROOT / "covapie_bulk_cys_sg_priority_human_review_queue_v1.csv"
SCALEUP_PROCESSING = SCALEUP_ROOT / "covapie_bulk_cys_sg_ranks_0501_1000_processing_outcomes_v1.json"
SCALEUP_SUMMARY = SCALEUP_ROOT / "covapie_bulk_cys_sg_model_usable_auto_admission_scaleup_summary_v1.json"
DECISIONS = (
    DERIVED
    / "covapie_bulk_post_only_cys_sg_human_review_v1"
    / "covapie_post_only_human_review_decisions_v1.json"
)
SUCCESSOR_DECISIONS = (
    DERIVED
    / "covapie_batch001_completed_decision_ingestion_and_task_label_availability_v1"
    / "covapie_batch001_completed_human_decision_snapshot_v1.json"
)
BRIDGE = (
    DERIVED
    / "covapie_batch001_to_existing_mixed_profile_supervision_bridge_v1"
    / "covapie_batch001_model_bound_structural_evidence_v1.json"
)
ROUTING = (
    DERIVED
    / "covapie_cumulative_500_supported_post_only_two_rule_routing_v1"
    / "covapie_cumulative_500_event_routing_inventory_v1.csv"
)
CANONICAL = (
    DERIVED
    / "covapie_bulk_cys_sg_dataset_expansion_v1"
    / "bulk_pilot_v1"
    / "cross_source_canonical_event_manifest_v1.json"
)
PRODUCTION_REGISTRY = (
    DERIVED
    / "covapie_cys_sg_dataset_expansion_pipeline_v1"
    / "6di9_gjj_approved_v1"
    / "reusable_authority_registry_v1.json"
)

FIRST500_PROCESSING_PARENT = Path(
    "covapie-state/bulk-500-controlled-execution-v1/attempt-001/"
    "cumulative_processing_view_v1.json"
)
CCD_CACHE_ROOT_PARENT = Path("covapie-state/bulk-multisource-cys-sg-v1")
CCD_CACHE_MANIFEST_PARENT = CCD_CACHE_ROOT_PARENT / "cache_manifest_v1.json"
K36_CARRIER_PARENT = Path(
    "covapie-state/formal-sidecars/k36-w1-recovered7-effective-supervision-v1/"
    "covapie_k36_w1_recovered7_effective_supervision_v1.json"
)

BOUND_REPOSITORY_SHA256 = {
    POSITIVE_INDEX: "5485305a750129e437ef68b43c758f9f0586add41fe54ee1d621b6c5bde62410",
    CLOSURE_MANIFEST: "5a94d4a35a0cc7b5495175bd4e94e26ab2a8ba796ed59ea1e1e4695575936944",
    CLOSURE_SUMMARY: "2c00779a087063124a12915ec71b3666e5b39a9c882ec15fd12cf2d26dec13be",
    CENSUS: "5998991f4a777dc8364d773e68a438837e656983aab805dae388b64c3619dbc5",
    QUEUE: "a2c701324b9ffbcd6dcb28cc098fcdc614d7b2a0ad849f1872f62472ce21cee2",
    SCALEUP_PROCESSING: "4f5ee75a645ee560cb8e272fd3ead8ba7a446dadf9aece38f12f0eeecad16e5f",
    SCALEUP_SUMMARY: "e0e0c64c07b32f1e9f6b3d8ed4c9af6ec9b7db77eeb80345e2de7eab54e65561",
    DECISIONS: "c2060a8b0a8123fbc6b9c11f2e70a9443367b63467bf9f9cf913a4c780168441",
    SUCCESSOR_DECISIONS: "c0c887b9026638484ae453d68a6fc654e3bd1b3bce7aa222f8a285d4878e0200",
    BRIDGE: "cca589fa4ac372c159b2e00ba4f59a7c794e21a10f1b3fcffbd477de42cd8f2e",
    ROUTING: "ea4ec17fed58d2a7100173ada17a0956a5c37ef4690899f415a9b497c8508173",
    CANONICAL: "d3f35987af92fca669b85d62a86914c7a01bf35d867c4a779e7fc08e76445dae",
    PRODUCTION_REGISTRY: "c6f150bd82b1ea45121aa96e1fefb6af3be64584117cc462f74b2e10fd1913e9",
}
BOUND_PARENT_SHA256 = {
    FIRST500_PROCESSING_PARENT: "a27d4bf7977d5a175387af83021270c68f9cf3e8db391113dc6f1ff22f0bfc44",
    CCD_CACHE_MANIFEST_PARENT: "10057a8fd7e34c5e63a912a44f242926247aef15cffefa942dceb910d3f1cd58",
    K36_CARRIER_PARENT: "bd448b021ee0882f4bfe0826206616b83cdc7f69d9544f4533098aceed3a558c",
}

RECONCILIATION_HEADER = (
    "raw_priority_rank",
    "raw_review_unit_id",
    "raw_unit_event_count",
    "canonical_event_id",
    "current_review_status",
    "current_status_authority_sources_json",
    "calibration_eligible",
    "calibration_exclusion_reason",
)
SHADOW_HEADER = (
    "canonical_event_id",
    "review_unit_id",
    "raw_priority_rank",
    "current_review_status",
    "ligand_component_id",
    "ccd_component_graph_sha256",
    "ccd_heavy_atom_graph_sha256",
    "ccd_heavy_atom_count",
    "formal_charge_representation_json",
    "formal_charge_representation_authoritative",
    "ligand_reactive_atom",
    "ligand_reactive_element",
    "reactive_center_radius1_sha256",
    "reactive_center_radius2_sha256",
    "ccd_retained_heavy_atom_coverage_complete",
    "explicit_cys_sg_endpoint_semantics",
    "source_atom_id_namespace",
    "positive_reference_event_count",
    "shadow_status",
    "strict_shadow_match",
    "matching_positive_reference_event_ids_json",
    "matching_positive_reference_components_json",
    "shadow_mapping_status",
    "reactive_preserving_isomorphism_count",
    "distinct_role_assignment_count",
    "machine_role_transfer_candidate_only_json",
    "shadow_authoritative",
    "shadow_model_usable",
    "shadow_training_admitted",
)
SELECTED_HEADER = (
    "selection_order",
    "selection_lane",
    "review_unit_id",
    "raw_priority_rank",
    "current_reconciled_rank",
    "raw_event_count",
    "effective_single_decision_event_yield",
    "unit_coherence_status",
    "canonical_event_ids_json",
    "pdb_ids_json",
    "ligand_component_ids_json",
    "ccd_component_graph_sha256",
    "ccd_heavy_atom_graph_sha256",
    "ligand_reactive_atom",
    "ligand_reactive_element",
    "reactive_center_radius1_sha256",
    "reactive_center_radius2_sha256",
    "full_coordinate_event_count",
    "exact_reactive_pair_event_count",
    "POST_geometry_available_event_count",
    "representation_blockers_json",
    "leakage_conflicts_json",
    "current_decision_state_reconciliation_json",
    "strict_positive_shadow_reference_ids_json",
    "shadow_mapping_status",
    "candidate_reusable_authority_scope_hypothesis",
    "event_count_if_human_negative",
    "event_count_if_sample_bound_positive",
    "event_count_if_exact_component_reuse_later_approved",
    "event_count_if_exact_signature_reuse_later_approved",
    "unlock_simulation_status",
    "source_sha_bindings_json",
)

CURRENTLY_UNREVIEWED = "CURRENTLY_UNREVIEWED"
CURRENTLY_IN_PROGRESS = "CURRENTLY_IN_PROGRESS"
COMPLETED_HUMAN_POSITIVE = "COMPLETED_HUMAN_POSITIVE"
COMPLETED_HUMAN_NEGATIVE = "COMPLETED_HUMAN_NEGATIVE"
COMPLETED_PARTIAL_AUTHORITY = "COMPLETED_PARTIAL_AUTHORITY"
CURRENT_RUNTIME_MODEL_USABLE = "CURRENT_RUNTIME_MODEL_USABLE"
PUBLISHED_EXACT_AUTO_NEGATIVE = "PUBLISHED_EXACT_AUTO_NEGATIVE"

NO_SHADOW = "NO_CURRENT_POSITIVE_SHADOW_MATCH"
EXACT_COMPONENT = "EXACT_COMPONENT_REUSE_SHADOW"
EXACT_CENTER = "EXACT_COMPONENT_REACTIVE_CENTER_SHADOW"
UNIQUE_TRANSFER = "UNIQUE_GRAPH_ISOMORPHIC_ROLE_TRANSFER_CANDIDATE"
AMBIGUOUS = "AMBIGUOUS_GRAPH_AUTOMORPHISM_SHADOW"
REFERENCE_CONFLICT = "CURRENT_POSITIVE_REFERENCE_CONFLICT"
GRAPH_ONLY = "GRAPH_ISOMORPHIC_NO_TRANSFERABLE_ROLE_SHADOW"
STRICT_SHADOW_STATUSES = frozenset((EXACT_COMPONENT, EXACT_CENTER, UNIQUE_TRANSFER))


class CalibrationSafetyError(ValueError):
    """Raised when review preparation cannot remain fail closed."""


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _json_cell(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _csv_bytes(header: Sequence[str], rows: Sequence[Mapping[str, object]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=header, extrasaction="raise", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_bytes())
    if type(value) is not dict:
        raise CalibrationSafetyError("JSON_ROOT_NOT_OBJECT:" + path.as_posix())
    return value


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _binding(path: Path, display: str) -> dict[str, object]:
    payload = path.read_bytes()
    return {"path": display, "byte_count": len(payload), "sha256": _sha(payload)}


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    if temporary.exists():
        temporary.unlink()
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _git(repo_root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.strip()


_RAW_DIFF_HEADER = re.compile(
    r"^:([0-7]{6}) ([0-7]{6}) ([0-9a-f]{40}) ([0-9a-f]{40}) "
    r"([ACDMRTUXB](?:[0-9]{1,3})?)$"
)


def _observe_published_commit_diff_v1(
    repo_root: Path, *, parent: str, head: str
) -> dict[str, list[str]]:
    try:
        raw = _git(
            repo_root,
            "diff-tree",
            "--no-commit-id",
            "-r",
            "--raw",
            "-z",
            "--no-abbrev",
            "--find-renames",
            "--find-copies-harder",
            parent,
            head,
        )
    except (subprocess.CalledProcessError, UnicodeError) as exc:
        raise CalibrationSafetyError("PUBLISHED_COMMIT_DIFF_UNREADABLE") from exc
    if not raw:
        return {
            "published_diff_statuses": [],
            "published_diff_modes": [],
            "published_diff_paths": [],
        }
    if not raw.endswith("\0"):
        raise CalibrationSafetyError("PUBLISHED_COMMIT_DIFF_MALFORMED")
    tokens = raw[:-1].split("\0")
    entries: list[tuple[str, str, str]] = []
    index = 0
    while index < len(tokens):
        match = _RAW_DIFF_HEADER.fullmatch(tokens[index])
        if match is None:
            raise CalibrationSafetyError("PUBLISHED_COMMIT_DIFF_MALFORMED")
        old_mode, new_mode, old_object, new_object, status = match.groups()
        status_code = status[0]
        if (status_code in {"R", "C"}) != (len(status) > 1):
            raise CalibrationSafetyError("PUBLISHED_COMMIT_DIFF_MALFORMED")
        if status_code == "A":
            modes_valid = old_mode == "000000" and new_mode != "000000"
            objects_valid = set(old_object) == {"0"} and set(new_object) != {"0"}
        elif status_code == "D":
            modes_valid = old_mode != "000000" and new_mode == "000000"
            objects_valid = set(old_object) != {"0"} and set(new_object) == {"0"}
        else:
            modes_valid = old_mode != "000000" and new_mode != "000000"
            objects_valid = set(old_object) != {"0"} and set(new_object) != {"0"}
        if not modes_valid or not objects_valid:
            raise CalibrationSafetyError("PUBLISHED_COMMIT_DIFF_MALFORMED")
        path_count = 2 if status_code in {"R", "C"} else 1
        if index + path_count >= len(tokens):
            raise CalibrationSafetyError("PUBLISHED_COMMIT_DIFF_MALFORMED")
        paths = tokens[index + 1 : index + 1 + path_count]
        if any(
            not path
            or path.startswith("/")
            or any(part in {"", ".", ".."} for part in path.split("/"))
            for path in paths
        ):
            raise CalibrationSafetyError("PUBLISHED_COMMIT_DIFF_MALFORMED")
        entries.append((paths[-1], status, new_mode))
        index += 1 + path_count
    entries.sort(key=lambda entry: entry[0])
    paths = [entry[0] for entry in entries]
    if len(paths) != len(set(paths)):
        raise CalibrationSafetyError("PUBLISHED_COMMIT_DIFF_MALFORMED")
    return {
        "published_diff_statuses": [entry[1] for entry in entries],
        "published_diff_modes": [entry[2] for entry in entries],
        "published_diff_paths": paths,
    }


def verify_bound_inputs_v1(repo_root: Path) -> list[dict[str, object]]:
    root = repo_root.resolve()
    bindings: list[dict[str, object]] = []
    for relative, expected in sorted(
        BOUND_REPOSITORY_SHA256.items(), key=lambda item: item[0].as_posix()
    ):
        path = root / relative
        if not path.is_file():
            raise CalibrationSafetyError("BOUND_INPUT_MISSING:" + relative.as_posix())
        observed = _binding(path, relative.as_posix())
        if observed["sha256"] != expected:
            raise CalibrationSafetyError(
                "BOUND_INPUT_SHA256_MISMATCH:" + relative.as_posix()
            )
        bindings.append(observed)
    for relative, expected in sorted(
        BOUND_PARENT_SHA256.items(), key=lambda item: item[0].as_posix()
    ):
        path = root.parent / relative
        if not path.is_file():
            raise CalibrationSafetyError(
                "BOUND_PARENT_INPUT_MISSING:" + relative.as_posix()
            )
        observed = _binding(path, relative.as_posix())
        if observed["sha256"] != expected:
            raise CalibrationSafetyError(
                "BOUND_PARENT_INPUT_SHA256_MISMATCH:" + relative.as_posix()
            )
        bindings.append(observed)
    return bindings


def observe_repository_state_v1(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    head = _git(root, "rev-parse", "HEAD")
    head_parent = _git(root, "rev-parse", "HEAD^")
    origin = _git(root, "rev-parse", "refs/remotes/origin/main")
    ahead, behind = _git(
        root, "rev-list", "--left-right", "--count", "HEAD...refs/remotes/origin/main"
    ).split()
    status_lines = _git(root, "status", "--porcelain=v1", "--untracked-files=all")
    tracked = _git(root, "diff", "--name-only").splitlines()
    staged = _git(root, "diff", "--cached", "--name-only").splitlines()
    untracked = _git(root, "ls-files", "--others", "--exclude-standard").splitlines()
    observation = {
        "branch": _git(root, "branch", "--show-current"),
        "HEAD": head,
        "HEAD_parent": head_parent,
        "HEAD_tree": _git(root, "rev-parse", "HEAD^{tree}"),
        "HEAD_subject": _git(root, "log", "-1", "--format=%s"),
        "origin_main": origin,
        "ahead": int(ahead),
        "behind": int(behind),
        "status_lines": status_lines.splitlines() if status_lines else [],
        "tracked_modifications": sorted(line for line in tracked if line),
        "staged": sorted(line for line in staged if line),
        "untracked": sorted(line for line in untracked if line),
        "published_diff_statuses": [],
        "published_diff_modes": [],
        "published_diff_paths": [],
    }
    if head_parent == BASELINE_HEAD:
        observation.update(
            _observe_published_commit_diff_v1(root, parent=head_parent, head=head)
        )
    return observation


def classify_repository_profile_v1(observation: Mapping[str, Any]) -> str:
    branch = observation.get("branch")
    head = observation.get("HEAD")
    origin = observation.get("origin_main")
    if branch != "main":
        raise CalibrationSafetyError("REPOSITORY_BRANCH_INVALID")
    if head == BASELINE_HEAD:
        if (
            observation.get("HEAD_parent") != BASELINE_PARENT
            or observation.get("HEAD_tree") != BASELINE_TREE
            or observation.get("HEAD_subject") != BASELINE_SUBJECT
            or origin != BASELINE_HEAD
            or observation.get("ahead") != 0
            or observation.get("behind") != 0
            or observation.get("tracked_modifications") != []
            or observation.get("staged") != []
            or not set(observation.get("untracked", ())) <= AUTHORIZED_PATHS
        ):
            raise CalibrationSafetyError("CANDIDATE_PRECOMMIT_PROFILE_INVALID")
        return "candidate_precommit_untracked"
    if (
        observation.get("HEAD_parent") == BASELINE_HEAD
        and observation.get("HEAD_subject") == PUBLICATION_SUBJECT
        and origin == head
        and observation.get("ahead") == 0
        and observation.get("behind") == 0
        and observation.get("tracked_modifications") == []
        and observation.get("staged") == []
        and observation.get("untracked") == []
        and observation.get("published_diff_statuses") == ["A"] * 9
        and observation.get("published_diff_modes") == ["100644"] * 9
        and set(observation.get("published_diff_paths", ())) == AUTHORIZED_PATHS
    ):
        return "published_successor"
    raise CalibrationSafetyError("UNSUPPORTED_REPOSITORY_PROFILE")


def _heavy_graph_dict(graph: Mapping[str, Any]) -> dict[str, Any]:
    atoms = [
        {
            "atom_id": str(atom["atom_id"]),
            "element": str(atom["type_symbol"]).upper(),
            "formal_charge": int(atom.get("charge") or 0),
            "aromatic": str(atom.get("aromatic_flag") or "N").upper(),
        }
        for atom in graph.get("ccd_atom_inventory", ())
        if str(atom.get("type_symbol")).upper() != "H"
    ]
    atom_ids = {atom["atom_id"] for atom in atoms}
    bonds = [
        {
            "atom_id_1": min(str(bond["atom_id_1"]), str(bond["atom_id_2"])),
            "atom_id_2": max(str(bond["atom_id_1"]), str(bond["atom_id_2"])),
            "order": str(bond.get("value_order") or "").upper(),
            "aromatic": str(bond.get("pdbx_aromatic_flag") or "N").upper(),
        }
        for bond in graph.get("ccd_bond_inventory", ())
        if str(bond.get("atom_id_1")) in atom_ids
        and str(bond.get("atom_id_2")) in atom_ids
    ]
    return {
        "atoms": sorted(atoms, key=lambda item: item["atom_id"]),
        "bonds": sorted(
            bonds,
            key=lambda item: (
                item["atom_id_1"], item["atom_id_2"], item["order"], item["aromatic"]
            ),
        ),
    }


def heavy_graph_sha256_v1(graph: Mapping[str, Any]) -> str:
    return _sha(_json_bytes(_heavy_graph_dict(graph)))


def _networkx_graph(graph: Mapping[str, Any]) -> nx.Graph:
    heavy = _heavy_graph_dict(graph)
    result = nx.Graph()
    for atom in heavy["atoms"]:
        result.add_node(
            atom["atom_id"],
            element=atom["element"],
            formal_charge=atom["formal_charge"],
            aromatic=atom["aromatic"],
        )
    for bond in heavy["bonds"]:
        result.add_edge(
            bond["atom_id_1"],
            bond["atom_id_2"],
            order=bond["order"],
            aromatic=bond["aromatic"],
        )
    return result


def _graph_prefilter(graph: nx.Graph) -> tuple[object, ...]:
    return (
        len(graph),
        graph.number_of_edges(),
        tuple(
            sorted(
                Counter(
                    (data["element"], data["formal_charge"], data["aromatic"])
                    for _node, data in graph.nodes(data=True)
                ).items()
            )
        ),
        tuple(
            sorted(
                Counter(
                    (data["order"], data["aromatic"])
                    for _left, _right, data in graph.edges(data=True)
                ).items()
            )
        ),
    )


def compare_graph_shadow_v1(
    *,
    candidate_component_id: str,
    candidate_graph: Mapping[str, Any],
    candidate_reactive_atom: str,
    reference_component_id: str,
    reference_graph: Mapping[str, Any],
    reference_reactive_atom: str,
    reference_roles: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Compare exact heavy graphs without promoting the result to authority."""

    candidate = _networkx_graph(candidate_graph)
    reference = _networkx_graph(reference_graph)
    if candidate_reactive_atom not in candidate or reference_reactive_atom not in reference:
        raise CalibrationSafetyError("REACTIVE_ATOM_MISSING_FROM_HEAVY_GRAPH")
    role_names = ("scaffold_atom_ids", "linker_atom_ids", "warhead_atom_ids")
    transfer_roles: dict[str, tuple[str, ...]] | None = None
    if reference_roles is not None and reference_roles.get("transfer_eligible") is True:
        transfer_roles = {
            name: tuple(str(atom) for atom in reference_roles.get(name, ()))
            for name in role_names
        }
        role_sets = [set(transfer_roles[name]) for name in role_names]
        if any(not values <= set(reference) for values in role_sets):
            raise CalibrationSafetyError("REFERENCE_ROLE_ATOM_MISSING_FROM_GRAPH")
        if any(role_sets[left] & role_sets[right] for left in range(3) for right in range(left)):
            raise CalibrationSafetyError("REFERENCE_ROLE_PARTITION_OVERLAP")
        if set().union(*role_sets) != set(reference):
            raise CalibrationSafetyError("REFERENCE_ROLE_PARTITION_NOT_EXHAUSTIVE")

    if candidate_component_id == reference_component_id:
        if candidate_graph.get("ccd_component_graph_sha256") != reference_graph.get(
            "ccd_component_graph_sha256"
        ):
            return {
                "status": REFERENCE_CONFLICT,
                "mapping_status": "SAME_CCD_ID_GRAPH_SHA256_CONFLICT",
                "isomorphism_count": 0,
                "reactive_preserving_isomorphism_count": 0,
                "distinct_role_assignment_count": 0,
                "mapping": {},
                "candidate_roles": None,
            }
        if set(candidate) != set(reference):
            raise CalibrationSafetyError("EXACT_COMPONENT_ATOM_NAMESPACE_DRIFT")
        mapping = {atom: atom for atom in sorted(reference)}
        candidate_roles = None
        if transfer_roles is not None and candidate_reactive_atom == reference_reactive_atom:
            candidate_roles = {
                name: list(transfer_roles[name]) for name in role_names
            }
            candidate_roles["role_profile"] = str(reference_roles["role_profile"])
        return {
            "status": (
                EXACT_CENTER
                if candidate_reactive_atom == reference_reactive_atom
                else EXACT_COMPONENT
            ),
            "mapping_status": "EXACT_CCD_ATOM_IDENTITY_NAMESPACE_MAPPING",
            "isomorphism_count": 1,
            "reactive_preserving_isomorphism_count": int(
                candidate_reactive_atom == reference_reactive_atom
            ),
            "distinct_role_assignment_count": int(candidate_roles is not None),
            "mapping": mapping,
            "candidate_roles": candidate_roles,
        }

    if _graph_prefilter(candidate) != _graph_prefilter(reference):
        return {
            "status": NO_SHADOW,
            "mapping_status": "HEAVY_GRAPH_PREFILTER_MISMATCH",
            "isomorphism_count": 0,
            "reactive_preserving_isomorphism_count": 0,
            "distinct_role_assignment_count": 0,
            "mapping": {},
            "candidate_roles": None,
        }
    matcher = nx.algorithms.isomorphism.GraphMatcher(
        reference,
        candidate,
        node_match=lambda left, right: left == right,
        edge_match=lambda left, right: left == right,
    )
    mapping_count = 0
    reactive_count = 0
    representative: dict[str, str] = {}
    role_outputs: dict[tuple[tuple[str, ...], ...], dict[str, list[str]]] = {}
    for mapping in matcher.isomorphisms_iter():
        mapping_count += 1
        if mapping.get(reference_reactive_atom) != candidate_reactive_atom:
            continue
        reactive_count += 1
        if not representative:
            representative = dict(sorted(mapping.items()))
        if transfer_roles is not None:
            transferred = {
                name: sorted(mapping[atom] for atom in transfer_roles[name])
                for name in role_names
            }
            key = tuple(tuple(transferred[name]) for name in role_names)
            role_outputs[key] = transferred
    if reactive_count == 0:
        return {
            "status": NO_SHADOW,
            "mapping_status": "GRAPH_ISOMORPHIC_BUT_REACTIVE_CENTER_NOT_PRESERVED",
            "isomorphism_count": mapping_count,
            "reactive_preserving_isomorphism_count": 0,
            "distinct_role_assignment_count": 0,
            "mapping": {},
            "candidate_roles": None,
        }
    if transfer_roles is None:
        return {
            "status": GRAPH_ONLY,
            "mapping_status": "REACTIVE_PRESERVING_GRAPH_ISOMORPHISM_WITHOUT_FULL_ROLE_PARTITION",
            "isomorphism_count": mapping_count,
            "reactive_preserving_isomorphism_count": reactive_count,
            "distinct_role_assignment_count": 0,
            "mapping": representative,
            "candidate_roles": None,
        }
    if len(role_outputs) != 1:
        return {
            "status": AMBIGUOUS,
            "mapping_status": "AUTOMORPHISMS_PRODUCE_DIFFERENT_ROLE_ASSIGNMENTS",
            "isomorphism_count": mapping_count,
            "reactive_preserving_isomorphism_count": reactive_count,
            "distinct_role_assignment_count": len(role_outputs),
            "mapping": {},
            "candidate_roles": None,
        }
    candidate_roles = next(iter(role_outputs.values()))
    candidate_roles["role_profile"] = str(reference_roles["role_profile"])
    return {
        "status": UNIQUE_TRANSFER,
        "mapping_status": "ALL_REACTIVE_PRESERVING_AUTOMORPHISMS_YIELD_ONE_ROLE_ASSIGNMENT",
        "isomorphism_count": mapping_count,
        "reactive_preserving_isomorphism_count": reactive_count,
        "distinct_role_assignment_count": 1,
        "mapping": representative,
        "candidate_roles": candidate_roles,
    }


def _load_role_partitions(
    *, inputs: Mapping[str, Any], positive_rows: Sequence[Mapping[str, str]]
) -> dict[str, dict[str, Any]]:
    roles: dict[str, dict[str, Any]] = {}
    for event in inputs["bridge"]["events"]:
        roles[str(event["canonical_event_id"])] = {
            "scaffold_atom_ids": list(event["scaffold_atom_ids"]),
            "linker_atom_ids": list(event["linker_atom_ids"]),
            "warhead_atom_ids": list(event["warhead_atom_ids"]),
            "role_profile": str(event["role_profile"]),
            "partition_scope": "FULL_CCD_HEAVY_ATOM_PARTITION",
            "transfer_eligible": True,
            "source": BRIDGE.as_posix(),
        }
    for unit in inputs["decisions"]["units"]:
        unit_roles = unit.get("roles") or {}
        if not (
            unit.get("workflow_status") == "COMPLETED"
            and unit.get("training_domain_relevance_decision")
            == "RELEVANT_FOR_COVAPIE_POST_ONLY_V1"
            and unit_roles.get("scaffold_atom_ids")
            and unit_roles.get("warhead_atom_ids")
        ):
            continue
        role_profile = (
            "STRICT_LINKER_PRESENT_V1"
            if unit_roles.get("linker_atom_ids")
            else "DIRECT_ATTACHMENT_OPTIONAL_LINKER_V1"
        )
        record = {
            "scaffold_atom_ids": list(unit_roles["scaffold_atom_ids"]),
            "linker_atom_ids": list(unit_roles["linker_atom_ids"]),
            "warhead_atom_ids": list(unit_roles["warhead_atom_ids"]),
            "role_profile": role_profile,
            "partition_scope": "FULL_CCD_HEAVY_ATOM_PARTITION",
            "transfer_eligible": True,
            "source": DECISIONS.as_posix(),
        }
        for event in unit["events"]:
            roles[str(event["canonical_event_id"])] = record
    carrier_by_identity = {
        str(record["sample_identity"]): record
        for record in inputs["k36_carrier"]["effective_supervision_records"]
    }
    for row in positive_rows:
        if row["lineage_id"] != "EXACT16_K36_DIRECT_ATTACHMENT_LINEAGE":
            continue
        record = carrier_by_identity[row["sample_identity"]]
        roles[row["canonical_event_id"]] = {
            "scaffold_atom_ids": list(record["reviewed_scaffold_atom_ids"]),
            "linker_atom_ids": list(record["reviewed_linker_atom_ids"]),
            "warhead_atom_ids": list(record["reviewed_warhead_role_atom_ids"]),
            "role_profile": str(record["role_profile"]),
            "partition_scope": "RETAINED_HEAVY_PARTITION_MASKED_PRECURSOR_EXCLUDED",
            "masked_precursor_atom_ids": list(record["masked_precursor_provenance_atom_ids"]),
            "transfer_eligible": False,
            "source": K36_CARRIER_PARENT.as_posix(),
        }
    positive_by_identity = {row["sample_identity"]: row for row in positive_rows}
    for authority in inputs["production_registry"]["authorities"]:
        source = json.loads(authority["source_human_review_record_canonical_json"])
        identity = str(source["candidate_identity"])
        if identity not in positive_by_identity:
            raise CalibrationSafetyError("PRODUCTION_ROLE_REFERENCE_IDENTITY_MISSING")
        atom_names = {
            int(item["atom_id"]): str(item["pdb_atom_name"])
            for item in source["machine_evidence"]["existing_role_warhead_proposal"][
                "atom_labels"
            ]
        }
        roles[positive_by_identity[identity]["canonical_event_id"]] = {
            name: [atom_names[int(index)] for index in source["reviewed_" + name]]
            for name in ("scaffold_atom_ids", "linker_atom_ids", "warhead_atom_ids")
        } | {
            "role_profile": str(source["role_profile"]),
            "partition_scope": "FULL_CCD_HEAVY_ATOM_PARTITION",
            "transfer_eligible": True,
            "source": PRODUCTION_REGISTRY.as_posix(),
        }
    return roles


def load_inputs_v1(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    bindings = verify_bound_inputs_v1(root)
    queue_rows = _read_csv(root / QUEUE)
    census_rows = _read_csv(root / CENSUS)
    positive_rows = _read_csv(root / POSITIVE_INDEX)
    decisions = _read_json(root / DECISIONS)
    successor = _read_json(root / SUCCESSOR_DECISIONS)
    canonical = _read_json(root / CANONICAL)
    first_processing = _read_json(root.parent / FIRST500_PROCESSING_PARENT)
    second_processing = _read_json(root / SCALEUP_PROCESSING)
    routing_rows = _read_csv(root / ROUTING)
    if (
        len(queue_rows) != 131
        or sum(int(row["event_count"]) for row in queue_rows) != 338
        or len(census_rows) != 1000
        or len(positive_rows) != 37
        or sum(row["current_runtime_model_usable"] == "true" for row in positive_rows)
        != 36
    ):
        raise CalibrationSafetyError("PUBLISHED_BASELINE_COUNT_DRIFT")
    runtime_rows = [
        row for row in positive_rows if row["current_runtime_model_usable"] == "true"
    ]
    partial_rows = [
        row for row in positive_rows if row["current_runtime_model_usable"] != "true"
    ]
    if (
        len(partial_rows) != 1
        or ":AJ3:" not in partial_rows[0]["canonical_event_id"]
        or Counter(
            row["formal_split"]
            for row in runtime_rows
            if row["formal_split_authoritative"] == "true"
        )
        != Counter({"train": 14, "validation": 8, "test": 14})
    ):
        raise CalibrationSafetyError("CURRENT_POSITIVE_CONTRACT_DRIFT")
    queue_events: list[str] = []
    for row in queue_rows:
        event_ids = json.loads(row["canonical_event_ids_json"])
        if len(event_ids) != int(row["event_count"]) or len(event_ids) != len(set(event_ids)):
            raise CalibrationSafetyError("RAW_QUEUE_UNIT_EVENT_COUNT_INVALID")
        queue_events.extend(event_ids)
    if len(queue_events) != 338 or len(queue_events) != len(set(queue_events)):
        raise CalibrationSafetyError("RAW_QUEUE_EVENT_PARTITION_INVALID")
    canonical_events = canonical.get("canonical_events")
    if type(canonical_events) is not list or len(canonical_events) != 2387:
        raise CalibrationSafetyError("CANONICAL_EVENT_MANIFEST_INVALID")
    canonical_by_id = {str(event["canonical_event_id"]): event for event in canonical_events}
    if not set(queue_events) <= set(canonical_by_id):
        raise CalibrationSafetyError("RAW_QUEUE_EVENT_MISSING_FROM_CANONICAL_MANIFEST")
    outcome_by_id: dict[str, Mapping[str, Any]] = {}
    wrapper_by_id: dict[str, dict[str, Any]] = {}
    for wrapper in first_processing.get("events", ()):
        outcome = wrapper.get("processing_outcome") or {}
        event_id = str(outcome.get("canonical_event_id"))
        outcome_by_id[event_id] = outcome
        wrapper_by_id[event_id] = dict(wrapper)
    for wrapper in second_processing.get("events", ()):
        event_id = str(wrapper.get("canonical_event_id"))
        outcome_by_id[event_id] = wrapper["processing_outcome"]
        wrapper_by_id[event_id] = dict(wrapper)
    if len(outcome_by_id) != 1000 or not set(queue_events) <= set(outcome_by_id):
        raise CalibrationSafetyError("PROCESSING_OUTCOME_COVERAGE_INVALID")
    routing_by_id = {row["canonical_event_id"]: row for row in routing_rows}
    if len(routing_by_id) != 500:
        raise CalibrationSafetyError("FIRST500_ROUTING_COVERAGE_INVALID")
    census_by_id = {row["canonical_event_id"]: row for row in census_rows}
    if len(census_by_id) != 1000 or not set(queue_events) <= set(census_by_id):
        raise CalibrationSafetyError("CENSUS_EVENT_COVERAGE_INVALID")
    loaded: dict[str, Any] = {
        "repo_root": root,
        "bindings": bindings,
        "queue_rows": queue_rows,
        "queue_events": queue_events,
        "census_rows": census_rows,
        "census_by_id": census_by_id,
        "positive_rows": positive_rows,
        "runtime_positive_rows": runtime_rows,
        "partial_positive_rows": partial_rows,
        "decisions": decisions,
        "successor": successor,
        "bridge": _read_json(root / BRIDGE),
        "production_registry": _read_json(root / PRODUCTION_REGISTRY),
        "k36_carrier": _read_json(root.parent / K36_CARRIER_PARENT),
        "canonical_by_id": canonical_by_id,
        "outcome_by_id": outcome_by_id,
        "wrapper_by_id": wrapper_by_id,
        "routing_by_id": routing_by_id,
    }
    loaded["role_partitions"] = _load_role_partitions(
        inputs=loaded, positive_rows=runtime_rows
    )
    return loaded


def _decision_sets(inputs: Mapping[str, Any]) -> dict[str, set[str]]:
    completed_positive: set[str] = set()
    completed_negative: set[str] = set()
    in_progress: set[str] = set()
    for unit in inputs["decisions"]["units"]:
        event_ids = {str(event["canonical_event_id"]) for event in unit.get("events", ())}
        if unit.get("workflow_status") == "IN_PROGRESS":
            in_progress.update(event_ids)
        elif unit.get("workflow_status") == "COMPLETED":
            if (
                unit.get("training_domain_relevance_decision")
                == "NOT_RELEVANT_TO_COVAPIE_SMALL_MOLECULE_TASK"
            ):
                completed_negative.update(event_ids)
            elif unit.get("training_domain_relevance_decision") == (
                "RELEVANT_FOR_COVAPIE_POST_ONLY_V1"
            ):
                completed_positive.update(
                    event["canonical_event_id"]
                    for event in unit.get("events", ())
                    if event.get("event_training_use_decision") == "INCLUDE"
                )
    successor = inputs["successor"]
    counts = successor.get("counts") or {}
    if (
        counts.get("completed_positive_event_count") != 13
        or counts.get("completed_negative_event_count") != 24
        or counts.get("duplicate_event_count") != 0
    ):
        raise CalibrationSafetyError("SUCCESSOR_DECISION_COUNTS_INVALID")
    successor_events: set[str] = set()
    for item in successor["completed_human_decisions"]:
        event_ids = {
            str(event["canonical_event_id"])
            for event in item["human_decision"]["events"]
        }
        if successor_events & event_ids:
            raise CalibrationSafetyError("SUCCESSOR_DECISION_EVENT_DUPLICATE")
        successor_events.update(event_ids)
        if item["completed_lane"] == "COMPLETED_TASK_DOMAIN_NEGATIVE":
            completed_negative.update(event_ids)
        elif item["completed_lane"] == "COMPLETED_POSITIVE_CHEMISTRY":
            completed_positive.update(event_ids)
        else:
            raise CalibrationSafetyError("SUCCESSOR_DECISION_LANE_INVALID")
    held = successor["held_out_in_progress"]
    held_units = [
        row
        for row in inputs["queue_rows"]
        if row["review_unit_id"] == held["review_unit_id"]
    ]
    if (
        len(held_units) != 1
        or int(held_units[0]["event_count"])
        != held["held_out_in_progress_event_count"]
        or held.get("workflow_status") != "IN_PROGRESS"
    ):
        raise CalibrationSafetyError("SUCCESSOR_IN_PROGRESS_UNIT_BINDING_INVALID")
    in_progress.update(json.loads(held_units[0]["canonical_event_ids_json"]))
    runtime = {row["canonical_event_id"] for row in inputs["runtime_positive_rows"]}
    partial = {row["canonical_event_id"] for row in inputs["partial_positive_rows"]}
    exact_negative = {
        row["canonical_event_id"]
        for row in inputs["census_rows"]
        if row["terminal_route"] == "AUTO_NEGATIVE_EXACT_RULE"
        or bool(row.get("negative_rule_id"))
    }
    return {
        COMPLETED_HUMAN_POSITIVE: completed_positive,
        COMPLETED_HUMAN_NEGATIVE: completed_negative,
        CURRENTLY_IN_PROGRESS: in_progress,
        CURRENT_RUNTIME_MODEL_USABLE: runtime,
        COMPLETED_PARTIAL_AUTHORITY: partial,
        PUBLISHED_EXACT_AUTO_NEGATIVE: exact_negative,
    }


def reconcile_review_queue_v1(inputs: Mapping[str, Any]) -> tuple[list[dict[str, object]], dict[str, Any]]:
    memberships = _decision_sets(inputs)
    source_by_status = {
        COMPLETED_HUMAN_POSITIVE: [SUCCESSOR_DECISIONS.as_posix(), DECISIONS.as_posix()],
        COMPLETED_HUMAN_NEGATIVE: [SUCCESSOR_DECISIONS.as_posix(), DECISIONS.as_posix()],
        CURRENTLY_IN_PROGRESS: [SUCCESSOR_DECISIONS.as_posix(), DECISIONS.as_posix()],
        CURRENT_RUNTIME_MODEL_USABLE: [POSITIVE_INDEX.as_posix()],
        COMPLETED_PARTIAL_AUTHORITY: [POSITIVE_INDEX.as_posix()],
        PUBLISHED_EXACT_AUTO_NEGATIVE: [CENSUS.as_posix()],
    }
    rows: list[dict[str, object]] = []
    status_counts: Counter[str] = Counter()
    unit_statuses: dict[str, set[str]] = defaultdict(set)
    for queue_row in inputs["queue_rows"]:
        for event_id in json.loads(queue_row["canonical_event_ids_json"]):
            observed = [status for status, events in memberships.items() if event_id in events]
            if len(observed) > 1:
                raise CalibrationSafetyError(
                    "EVENT_ASSIGNED_MULTIPLE_REVIEW_STATUSES:" + event_id
                )
            status = observed[0] if observed else CURRENTLY_UNREVIEWED
            eligible = status == CURRENTLY_UNREVIEWED
            status_counts[status] += 1
            unit_statuses[queue_row["review_unit_id"]].add(status)
            row = {
                "raw_priority_rank": int(queue_row["priority_rank"]),
                "raw_review_unit_id": queue_row["review_unit_id"],
                "raw_unit_event_count": int(queue_row["event_count"]),
                "canonical_event_id": event_id,
                "current_review_status": status,
                "current_status_authority_sources_json": _json_cell(
                    source_by_status.get(status, [QUEUE.as_posix()])
                ),
                "calibration_eligible": str(eligible).lower(),
                "calibration_exclusion_reason": "" if eligible else status,
            }
            rows.append({field: row[field] for field in RECONCILIATION_HEADER})
    if len(rows) != 338 or len({row["canonical_event_id"] for row in rows}) != 338:
        raise CalibrationSafetyError("RECONCILIATION_EVENT_COVERAGE_INVALID")
    eligible_units = {
        unit for unit, statuses in unit_statuses.items() if statuses == {CURRENTLY_UNREVIEWED}
    }
    mixed_units = {
        unit for unit, statuses in unit_statuses.items() if len(statuses) > 1
    }
    if mixed_units:
        raise CalibrationSafetyError("RAW_REVIEW_UNIT_MIXES_CURRENT_DECISION_STATES")
    summary = {
        "raw_snapshot_review_event_count": len(rows),
        "raw_snapshot_review_unit_count": len(unit_statuses),
        "current_runtime_positive_excluded_event_count": status_counts[
            CURRENT_RUNTIME_MODEL_USABLE
        ],
        "completed_human_positive_excluded_event_count": status_counts[
            COMPLETED_HUMAN_POSITIVE
        ],
        "completed_human_negative_excluded_event_count": status_counts[
            COMPLETED_HUMAN_NEGATIVE
        ],
        "in_progress_excluded_event_count": status_counts[CURRENTLY_IN_PROGRESS],
        "published_exact_auto_negative_excluded_event_count": status_counts[
            PUBLISHED_EXACT_AUTO_NEGATIVE
        ],
        "currently_unreviewed_event_count": status_counts[CURRENTLY_UNREVIEWED],
        "currently_unreviewed_unit_count": len(eligible_units),
        "partial_authority_incomplete_event_count": len(
            memberships[COMPLETED_PARTIAL_AUTHORITY]
        ),
        "eligible_unit_ids": sorted(eligible_units),
    }
    summary["completed_or_superseded_event_count"] = sum(
        int(summary[key])
        for key in (
            "current_runtime_positive_excluded_event_count",
            "completed_human_positive_excluded_event_count",
            "completed_human_negative_excluded_event_count",
            "published_exact_auto_negative_excluded_event_count",
        )
    )
    summary["in_progress_event_count"] = summary["in_progress_excluded_event_count"]
    summary["new_calibration_eligible_event_count"] = summary[
        "currently_unreviewed_event_count"
    ]
    summary["new_calibration_eligible_unit_count"] = summary[
        "currently_unreviewed_unit_count"
    ]
    if (
        summary["completed_human_negative_excluded_event_count"] != 24
        or summary["in_progress_excluded_event_count"] != 9
        or summary["currently_unreviewed_event_count"] != 305
        or summary["currently_unreviewed_unit_count"] != 126
        or summary["partial_authority_incomplete_event_count"] != 1
    ):
        raise CalibrationSafetyError("CURRENT_RECONCILIATION_FACTS_INVALID")
    return rows, summary


def _reference_records(
    inputs: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, object]]]:
    cache_root = inputs["repo_root"].parent / CCD_CACHE_ROOT_PARENT
    manifest = _read_json(cache_root / "cache_manifest_v1.json")
    manifest_by_path = {
        str(item["relative_path"]): item for item in manifest.get("payloads", ())
    }
    records: list[dict[str, Any]] = []
    ccd_bindings: dict[str, dict[str, object]] = {}
    for positive in sorted(
        inputs["runtime_positive_rows"], key=lambda row: row["canonical_event_id"]
    ):
        event_id = positive["canonical_event_id"]
        event = inputs["canonical_by_id"][event_id]
        component = str(event["ligand_component_id"])
        relative = f"rcsb/ccd/{component}.cif"
        path = cache_root / relative
        source = manifest_by_path.get(relative)
        if source is None or not path.is_file():
            raise CalibrationSafetyError("POSITIVE_REFERENCE_CCD_CACHE_MISSING:" + component)
        binding = _binding(path, (CCD_CACHE_ROOT_PARENT / relative).as_posix())
        if (
            binding["sha256"] != source.get("sha256")
            or binding["byte_count"] != source.get("byte_count")
        ):
            raise CalibrationSafetyError("POSITIVE_REFERENCE_CCD_CACHE_DRIFT:" + component)
        ccd_bindings[component] = binding
        graph = parse_ccd_cif_v1(path.read_bytes(), ccd_id=component)
        role = inputs["role_partitions"].get(event_id)
        record = {
            "positive_event_id": event_id,
            "lineage_id": positive["lineage_id"],
            "component_id": component,
            "reactive_atom": str(event["ligand_reactive_atom"]),
            "graph": graph,
            "heavy_graph_sha256": heavy_graph_sha256_v1(graph),
            "role_partition": role,
            "role_partition_availability": (
                role["partition_scope"]
                if role is not None
                else "ROLE_PARTITION_NOT_EXPOSED_BY_BOUND_REFERENCE_EVIDENCE"
            ),
            "role_profile": "" if role is None else role["role_profile"],
        }
        records.append(record)
    if len(records) != 36 or len({row["positive_event_id"] for row in records}) != 36:
        raise CalibrationSafetyError("POSITIVE_REFERENCE_COVERAGE_INVALID")
    return records, [ccd_bindings[key] for key in sorted(ccd_bindings)]


def _formal_charge_json(graph: Mapping[str, Any]) -> str:
    return _json_cell(
        [
            [atom["atom_id"], atom["formal_charge"]]
            for atom in _heavy_graph_dict(graph)["atoms"]
        ]
    )


def build_shadow_inventory_v1(
    *,
    inputs: Mapping[str, Any],
    reconciliation_rows: Sequence[Mapping[str, object]],
) -> tuple[list[dict[str, object]], dict[str, Any]]:
    references, ccd_bindings = _reference_records(inputs)
    reconciliation = {
        str(row["canonical_event_id"]): row for row in reconciliation_rows
    }
    queue_by_event = {
        event_id: row
        for row in inputs["queue_rows"]
        for event_id in json.loads(row["canonical_event_ids_json"])
    }
    strength = {
        UNIQUE_TRANSFER: 0,
        EXACT_CENTER: 1,
        EXACT_COMPONENT: 2,
        AMBIGUOUS: 3,
        GRAPH_ONLY: 4,
        REFERENCE_CONFLICT: 5,
        NO_SHADOW: 6,
    }
    rows: list[dict[str, object]] = []
    status_counts: Counter[str] = Counter()
    strict_units: set[str] = set()
    for event_id in sorted(
        event
        for event, row in reconciliation.items()
        if row["current_review_status"] == CURRENTLY_UNREVIEWED
    ):
        event = inputs["canonical_by_id"][event_id]
        outcome = inputs["outcome_by_id"][event_id]
        structural = outcome.get("structural_processing") or {}
        graph = structural.get("ccd_component_graph") or {}
        if not graph.get("ccd_component_graph_sha256"):
            raise CalibrationSafetyError("UNREVIEWED_EVENT_CCD_GRAPH_MISSING:" + event_id)
        comparisons: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for reference in references:
            result = compare_graph_shadow_v1(
                candidate_component_id=str(event["ligand_component_id"]),
                candidate_graph=graph,
                candidate_reactive_atom=str(event["ligand_reactive_atom"]),
                reference_component_id=reference["component_id"],
                reference_graph=reference["graph"],
                reference_reactive_atom=reference["reactive_atom"],
                reference_roles=reference["role_partition"],
            )
            if result["status"] != NO_SHADOW:
                comparisons.append((reference, result))
        if comparisons:
            strongest_value = min(strength[result["status"]] for _ref, result in comparisons)
            strongest = [
                (reference, result)
                for reference, result in comparisons
                if strength[result["status"]] == strongest_value
            ]
            status = strongest[0][1]["status"]
        else:
            strongest = []
            status = NO_SHADOW
        role_candidates = [
            (reference, result)
            for reference, result in strongest
            if result.get("candidate_roles") is not None
        ]
        machine_candidate: dict[str, Any] | None = None
        if role_candidates:
            candidate_digests = {
                _sha(_json_bytes(result["candidate_roles"]))
                for _reference, result in role_candidates
            }
            if len(candidate_digests) != 1:
                status = REFERENCE_CONFLICT
            else:
                reference, result = role_candidates[0]
                machine_candidate = {
                    "candidate_status": "MACHINE_ROLE_TRANSFER_CANDIDATE_ONLY",
                    "authoritative": False,
                    "reference_positive_event_ids": sorted(
                        ref["positive_event_id"] for ref, _value in role_candidates
                    ),
                    "exact_mapping_reference_to_candidate": result["mapping"],
                    "scaffold_candidate_atoms": result["candidate_roles"][
                        "scaffold_atom_ids"
                    ],
                    "linker_candidate_atoms": result["candidate_roles"][
                        "linker_atom_ids"
                    ],
                    "warhead_candidate_atoms": result["candidate_roles"][
                        "warhead_atom_ids"
                    ],
                    "role_profile_candidate": result["candidate_roles"]["role_profile"],
                    "mapping_uniqueness_proof": {
                        "mapping_status": result["mapping_status"],
                        "reactive_preserving_isomorphism_count": result[
                            "reactive_preserving_isomorphism_count"
                        ],
                        "distinct_role_assignment_count": result[
                            "distinct_role_assignment_count"
                        ],
                        "all_reference_candidates_same_role_partition": True,
                    },
                }
        queue_row = queue_by_event[event_id]
        pre = outcome.get("pre_representability") or {}
        matching_refs = sorted(
            reference["positive_event_id"] for reference, _result in comparisons
        )
        matching_components = sorted(
            {reference["component_id"] for reference, _result in comparisons}
        )
        strict = status in STRICT_SHADOW_STATUSES
        status_counts[status] += 1
        if strict:
            strict_units.add(queue_row["review_unit_id"])
        representative_result = (
            strongest[0][1]
            if strongest
            else {
                "mapping_status": "NO_EXACT_OR_ISOMORPHIC_REFERENCE_MATCH",
                "reactive_preserving_isomorphism_count": 0,
                "distinct_role_assignment_count": 0,
            }
        )
        row = {
            "canonical_event_id": event_id,
            "review_unit_id": queue_row["review_unit_id"],
            "raw_priority_rank": int(queue_row["priority_rank"]),
            "current_review_status": CURRENTLY_UNREVIEWED,
            "ligand_component_id": event["ligand_component_id"],
            "ccd_component_graph_sha256": graph["ccd_component_graph_sha256"],
            "ccd_heavy_atom_graph_sha256": heavy_graph_sha256_v1(graph),
            "ccd_heavy_atom_count": len(_heavy_graph_dict(graph)["atoms"]),
            "formal_charge_representation_json": _formal_charge_json(graph),
            "formal_charge_representation_authoritative": str(
                bool(pre.get("formal_charge_pattern_authoritative"))
            ).lower(),
            "ligand_reactive_atom": event["ligand_reactive_atom"],
            "ligand_reactive_element": structural.get("ligand_reactive_element") or "",
            "reactive_center_radius1_sha256": structural.get(
                "reactive_center_radius1_sha256"
            )
            or "",
            "reactive_center_radius2_sha256": structural.get(
                "reactive_center_radius2_sha256"
            )
            or "",
            "ccd_retained_heavy_atom_coverage_complete": str(
                pre.get("ccd_retained_atom_coverage_complete") is True
            ).lower(),
            "explicit_cys_sg_endpoint_semantics": str(
                structural.get("explicit_covalent_evidence") is True
                and str(event.get("protein_residue_name")).upper() == "CYS"
                and str(event.get("protein_reactive_atom")).upper() == "SG"
            ).lower(),
            "source_atom_id_namespace": "WWPDB_CCD_ATOM_ID",
            "positive_reference_event_count": 36,
            "shadow_status": status,
            "strict_shadow_match": str(strict).lower(),
            "matching_positive_reference_event_ids_json": _json_cell(matching_refs),
            "matching_positive_reference_components_json": _json_cell(
                matching_components
            ),
            "shadow_mapping_status": representative_result["mapping_status"],
            "reactive_preserving_isomorphism_count": representative_result[
                "reactive_preserving_isomorphism_count"
            ],
            "distinct_role_assignment_count": representative_result[
                "distinct_role_assignment_count"
            ],
            "machine_role_transfer_candidate_only_json": _json_cell(
                machine_candidate or {}
            ),
            "shadow_authoritative": "false",
            "shadow_model_usable": "false",
            "shadow_training_admitted": "false",
        }
        rows.append({field: row[field] for field in SHADOW_HEADER})
    if len(rows) != 305 or any(row["positive_reference_event_count"] != 36 for row in rows):
        raise CalibrationSafetyError("SHADOW_INVENTORY_COVERAGE_INVALID")
    summary = {
        "current_positive_reference_event_count": 36,
        "current_positive_reference_component_count": len(
            {record["component_id"] for record in references}
        ),
        "full_CCD_role_partition_reference_event_count": sum(
            record["role_partition"] is not None
            and record["role_partition"].get("transfer_eligible") is True
            for record in references
        ),
        "nontransferable_or_unexposed_role_reference_event_count": sum(
            record["role_partition"] is None
            or record["role_partition"].get("transfer_eligible") is not True
            for record in references
        ),
        "strict_positive_shadow_event_count": sum(
            row["strict_shadow_match"] == "true" for row in rows
        ),
        "strict_positive_shadow_unit_count": len(strict_units),
        "unique_graph_isomorphic_role_transfer_candidate_event_count": status_counts[
            UNIQUE_TRANSFER
        ],
        "ambiguous_graph_automorphism_shadow_event_count": status_counts[AMBIGUOUS],
        "shadow_status_counts": dict(sorted(status_counts.items())),
        "positive_reference_records": [
            {
                "positive_event_id": record["positive_event_id"],
                "lineage_id": record["lineage_id"],
                "component_id": record["component_id"],
                "reactive_atom": record["reactive_atom"],
                "ccd_component_graph_sha256": record["graph"][
                    "ccd_component_graph_sha256"
                ],
                "ccd_heavy_atom_graph_sha256": record["heavy_graph_sha256"],
                "role_partition_availability": record[
                    "role_partition_availability"
                ],
                "role_profile": record["role_profile"],
            }
            for record in references
        ],
        "reference_ccd_source_bindings": ccd_bindings,
    }
    if (
        summary["strict_positive_shadow_event_count"] != 5
        or summary["strict_positive_shadow_unit_count"] != 3
    ):
        raise CalibrationSafetyError("STRICT_SHADOW_CURRENT_FACTS_INVALID")
    return rows, summary


def _coherence_signature(
    *, inputs: Mapping[str, Any], event_id: str, shadow_row: Mapping[str, object]
) -> tuple[str, ...]:
    outcome = inputs["outcome_by_id"][event_id]
    structural = outcome.get("structural_processing") or {}
    pre = outcome.get("pre_representability") or {}
    graph = structural.get("ccd_component_graph") or {}
    role_candidate = json.loads(
        str(shadow_row["machine_role_transfer_candidate_only_json"])
    )
    return (
        str(inputs["canonical_by_id"][event_id]["ligand_component_id"]),
        str(inputs["canonical_by_id"][event_id]["ligand_reactive_atom"]),
        str(graph.get("ccd_component_graph_sha256") or ""),
        str(shadow_row["ccd_heavy_atom_graph_sha256"]),
        str(structural.get("reactive_center_radius1_sha256") or ""),
        str(structural.get("reactive_center_radius2_sha256") or ""),
        str(pre.get("status") or ""),
        str(pre.get("pre_source_graph_sha256") or ""),
        str(pre.get("pre_reactive_center_radius2_sha256") or ""),
        str(bool(pre.get("atom_loss_flag"))),
        _formal_charge_json(graph),
        str(shadow_row["shadow_status"]),
        _sha(_json_bytes(role_candidate)),
    )


def analyze_units_v1(
    *,
    inputs: Mapping[str, Any],
    reconciliation_summary: Mapping[str, Any],
    shadow_rows: Sequence[Mapping[str, object]],
) -> list[dict[str, Any]]:
    eligible = set(reconciliation_summary["eligible_unit_ids"])
    shadow_by_id = {str(row["canonical_event_id"]): row for row in shadow_rows}
    units: list[dict[str, Any]] = []
    for queue_row in inputs["queue_rows"]:
        if queue_row["review_unit_id"] not in eligible:
            continue
        event_ids = json.loads(queue_row["canonical_event_ids_json"])
        signatures: dict[tuple[str, ...], list[str]] = defaultdict(list)
        for event_id in event_ids:
            signatures[
                _coherence_signature(
                    inputs=inputs, event_id=event_id, shadow_row=shadow_by_id[event_id]
                )
            ].append(event_id)
        coherent = len(signatures) == 1
        effective = max(len(values) for values in signatures.values())
        representative_id = sorted(
            signatures.values(), key=lambda values: (-len(values), values)
        )[0][0]
        representative_shadow = shadow_by_id[representative_id]
        outcome = inputs["outcome_by_id"][representative_id]
        structural = outcome["structural_processing"]
        strict_rows = [
            shadow_by_id[event_id]
            for event_id in event_ids
            if shadow_by_id[event_id]["strict_shadow_match"] == "true"
        ]
        status_strength = {
            UNIQUE_TRANSFER: 0,
            EXACT_CENTER: 1,
            EXACT_COMPONENT: 2,
            NO_SHADOW: 9,
        }
        strongest_status = min(
            (str(row["shadow_status"]) for row in strict_rows),
            key=lambda status: status_strength.get(status, 8),
            default=NO_SHADOW,
        )
        units.append(
            {
                "review_unit_id": queue_row["review_unit_id"],
                "raw_priority_rank": int(queue_row["priority_rank"]),
                "raw_event_count": len(event_ids),
                "effective_single_decision_event_yield": effective,
                "unit_coherence_status": (
                    "UNIT_COHERENT_SINGLE_DECISION"
                    if coherent
                    else "UNIT_REQUIRES_SUBDIVISION"
                ),
                "coherent_subgroup_count": len(signatures),
                "selected_coherent_event_ids": sorted(
                    max(signatures.values(), key=lambda values: (len(values), values))
                ),
                "canonical_event_ids": event_ids,
                "pdb_ids": json.loads(queue_row["pdb_ids_json"]),
                "ligand_component_ids": json.loads(
                    queue_row["ligand_component_ids_json"]
                ),
                "representative_event_id": representative_id,
                "ccd_component_graph_sha256": representative_shadow[
                    "ccd_component_graph_sha256"
                ],
                "ccd_heavy_atom_graph_sha256": representative_shadow[
                    "ccd_heavy_atom_graph_sha256"
                ],
                "ligand_reactive_atom": representative_shadow[
                    "ligand_reactive_atom"
                ],
                "ligand_reactive_element": representative_shadow[
                    "ligand_reactive_element"
                ],
                "reactive_center_radius1_sha256": representative_shadow[
                    "reactive_center_radius1_sha256"
                ],
                "reactive_center_radius2_sha256": representative_shadow[
                    "reactive_center_radius2_sha256"
                ],
                "strongest_shadow_status": strongest_status,
                "strict_shadow_reference_ids": sorted(
                    {
                        reference
                        for row in strict_rows
                        for reference in json.loads(
                            str(row["matching_positive_reference_event_ids_json"])
                        )
                    }
                ),
                "machine_role_transfer_candidate_only": json.loads(
                    str(
                        next(
                            (
                                row["machine_role_transfer_candidate_only_json"]
                                for row in strict_rows
                                if json.loads(
                                    str(
                                        row[
                                            "machine_role_transfer_candidate_only_json"
                                        ]
                                    )
                                )
                            ),
                            "{}",
                        )
                    )
                ),
                "full_coordinate_event_count": int(
                    queue_row["full_coordinate_event_count"]
                ),
                "exact_reactive_pair_event_count": int(
                    queue_row["exact_reactive_pair_event_count"]
                ),
                "POST_geometry_available_event_count": int(
                    queue_row["POST_geometry_available_event_count"]
                ),
                "representation_blocked_event_count": int(
                    queue_row["representation_blocked_event_count"]
                ),
                "leakage_conflict_event_count": int(
                    queue_row["leakage_conflict_event_count"]
                ),
                "representative_outcome": outcome,
            }
        )
    if len(units) != 126 or sum(unit["raw_event_count"] for unit in units) != 305:
        raise CalibrationSafetyError("ELIGIBLE_UNIT_COVERAGE_INVALID")
    return units


def select_calibration_units_v1(units: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    if any(unit["unit_coherence_status"] != "UNIT_COHERENT_SINGLE_DECISION" for unit in units):
        raise CalibrationSafetyError("CURRENT_ELIGIBLE_UNIT_REQUIRES_SUBDIVISION")
    shadow_tier = {UNIQUE_TRANSFER: 0, EXACT_CENTER: 1, EXACT_COMPONENT: 2}
    shadow_candidates = [
        unit for unit in units if unit["strongest_shadow_status"] in shadow_tier
    ]
    if shadow_candidates:
        lane_a = min(
            shadow_candidates,
            key=lambda unit: (
                shadow_tier[unit["strongest_shadow_status"]],
                -int(unit["effective_single_decision_event_yield"]),
                int(unit["raw_priority_rank"]),
                str(unit["review_unit_id"]),
            ),
        )
        lane_a_name = "STRICT_POSITIVE_REUSE_CALIBRATION"
    else:
        lane_a = min(
            units,
            key=lambda unit: (
                -int(unit["effective_single_decision_event_yield"]),
                int(unit["raw_priority_rank"]),
                str(unit["review_unit_id"]),
            ),
        )
        lane_a_name = "MAXIMUM_EVENT_YIELD_NOVEL_CALIBRATION_FALLBACK"
    remaining = [unit for unit in units if unit["review_unit_id"] != lane_a["review_unit_id"]]
    lane_b = min(
        remaining,
        key=lambda unit: (
            -int(unit["effective_single_decision_event_yield"]),
            int(unit["raw_priority_rank"]),
            str(unit["review_unit_id"]),
        ),
    )
    chosen = (lane_a, lane_b)
    diverse = [
        unit
        for unit in remaining
        if unit["review_unit_id"] != lane_b["review_unit_id"]
        and unit["ccd_component_graph_sha256"]
        and unit["reactive_center_radius2_sha256"]
        and all(
            unit["ccd_component_graph_sha256"]
            != selected["ccd_component_graph_sha256"]
            and unit["reactive_center_radius2_sha256"]
            != selected["reactive_center_radius2_sha256"]
            for selected in chosen
        )
    ]
    if not diverse:
        raise CalibrationSafetyError("LANE_C_CHEMISTRY_DIVERSITY_UNAVAILABLE")
    lane_c = min(
        diverse,
        key=lambda unit: (
            -int(unit["effective_single_decision_event_yield"]),
            int(unit["raw_priority_rank"]),
            str(unit["review_unit_id"]),
        ),
    )
    selected = []
    for order, (lane, unit) in enumerate(
        (
            (lane_a_name, lane_a),
            ("MAXIMUM_EVENT_YIELD_NOVEL_CALIBRATION", lane_b),
            ("CHEMISTRY_DIVERSITY_CALIBRATION", lane_c),
        ),
        start=1,
    ):
        selected.append({**unit, "selection_order": order, "selection_lane": lane})
    if len({unit["review_unit_id"] for unit in selected}) != 3:
        raise CalibrationSafetyError("SELECTED_UNIT_IDENTITY_NOT_DISTINCT")
    return selected


def validate_selection_against_reconciliation_v1(
    *,
    selected: Sequence[Mapping[str, Any]],
    reconciliation_rows: Sequence[Mapping[str, object]],
) -> None:
    """Prove that no completed, active, positive, or negative row was selected."""

    status_by_event = {
        str(row["canonical_event_id"]): str(row["current_review_status"])
        for row in reconciliation_rows
    }
    if len(status_by_event) != len(reconciliation_rows):
        raise CalibrationSafetyError("RECONCILIATION_EVENT_DUPLICATE")
    if len(selected) > 3 or len({unit["review_unit_id"] for unit in selected}) != len(
        selected
    ):
        raise CalibrationSafetyError("SELECTED_UNIT_COUNT_OR_IDENTITY_INVALID")
    selected_events: set[str] = set()
    for unit in selected:
        event_ids = [str(event) for event in unit["canonical_event_ids"]]
        if selected_events & set(event_ids):
            raise CalibrationSafetyError("EVENT_SELECTED_BY_TWO_CALIBRATION_UNITS")
        selected_events.update(event_ids)
        for event_id in event_ids:
            status = status_by_event.get(event_id)
            if status is None:
                raise CalibrationSafetyError("SELECTED_EVENT_MISSING_FROM_RECONCILIATION")
            if status != CURRENTLY_UNREVIEWED:
                raise CalibrationSafetyError("INELIGIBLE_REVIEW_STATUS_SELECTED:" + status)


def _negative_evaluations(inputs: Mapping[str, Any], event_id: str) -> list[dict[str, str]]:
    wrapper = inputs["wrapper_by_id"][event_id]
    if wrapper.get("exact_rule_evaluations") is not None:
        return [dict(item) for item in wrapper["exact_rule_evaluations"]]
    route = inputs["routing_by_id"].get(event_id)
    if route is None:
        raise CalibrationSafetyError("NEGATIVE_RULE_EVIDENCE_MISSING:" + event_id)
    return [
        {
            "rule_id": route["ts_dump_rule_id"],
            "status": route["ts_dump_rule_status"],
            "reason": route["ts_dump_rule_reason"],
        },
        {
            "rule_id": route["dtt_rule_id"],
            "status": route["dtt_rule_status"],
            "reason": route["dtt_rule_reason"],
        },
    ]


def _event_anomalies(outcome: Mapping[str, Any]) -> list[str]:
    structural = outcome.get("structural_processing") or {}
    pre = outcome.get("pre_representability") or {}
    anomalies = list(outcome.get("terminal_reasons") or ())
    if not structural.get("reactive_center_radius2_sha256"):
        anomalies.append("REACTIVE_CENTER_RADIUS2_UNAVAILABLE")
    if pre.get("formal_charge_pattern_authoritative") is not True:
        anomalies.append("FORMAL_CHARGE_REPRESENTATION_NOT_AUTHORITATIVE")
    if pre.get("status") != "PRE_REACTION_RESOLVED":
        anomalies.append(str(pre.get("status") or "PRE_REACTION_STATUS_MISSING"))
    if pre.get("atom_loss_flag"):
        anomalies.append("ATOM_LOSS_FLAG")
    leakage = structural.get("leakage_evidence") or {}
    if leakage.get("complete") is not True:
        anomalies.append("LEAKAGE_EVIDENCE_INCOMPLETE")
    return sorted(set(anomalies))


def _event_packet(
    *, inputs: Mapping[str, Any], event_id: str, shadow: Mapping[str, object]
) -> dict[str, Any]:
    event = inputs["canonical_by_id"][event_id]
    outcome = inputs["outcome_by_id"][event_id]
    structural = outcome["structural_processing"]
    pre = outcome["pre_representability"]
    census = inputs["census_by_id"][event_id]
    return {
        "canonical_event_identity": event_id,
        "protein_Cys_SG_endpoint": {
            "pdb_id": event["pdb_id"],
            "label_asym_id": event["protein_instance"],
            "auth_chain": event.get("protein_auth_chain") or "",
            "residue_name": event["protein_residue_name"],
            "residue_number": event["protein_residue_number"],
            "atom_id": event["protein_reactive_atom"],
        },
        "ligand_reactive_endpoint": {
            "component_id": event["ligand_component_id"],
            "ligand_instance": event["ligand_instance"],
            "atom_id": event["ligand_reactive_atom"],
            "element": structural.get("ligand_reactive_element") or "",
            "atom_id_namespace": "WWPDB_CCD_ATOM_ID",
        },
        "selected_struct_conn_identity": structural["selected_connection_id"],
        "POST_distance_angstrom": structural["post_distance_angstrom"],
        "ligand_heavy_atom_count": structural["ligand_heavy_atom_count"],
        "pocket_heavy_atom_count": structural["pocket_heavy_atom_count"],
        "feature_compatibility": census["feature_status"],
        "CCD_retained_coverage": {
            "complete": pre["ccd_retained_atom_coverage_complete"],
            "CCD_heavy_atom_count": pre["ccd_heavy_atom_count"],
            "retained_heavy_atom_count": pre["retained_heavy_atom_count"],
            "CCD_atoms_missing_from_retained": pre["ccd_atoms_missing_from_retained"],
            "retained_atoms_missing_from_CCD": pre["retained_atoms_missing_from_ccd"],
        },
        "raw_pair_availability": census["reactive_pair_label_available"] == "true",
        "POST_availability": census["POST_geometry_label_available"] == "true",
        "exact_pair_evidence": {
            "explicit_covalent_evidence": structural["explicit_covalent_evidence"],
            "distance_only_event_inference_used": structural[
                "distance_only_event_inference_used"
            ],
            "selected_connection_id": structural["selected_connection_id"],
        },
        "leakage_status": census["leakage_status"],
        "leakage_group": census["leakage_group_id"],
        "current_split_status": {
            "formal_split": census["formal_split_if_authoritative"],
            "training_split_admission_ready": census["training_split_admission_ready"],
        },
        "negative_rule_evaluations": _negative_evaluations(inputs, event_id),
        "existing_reusable_chemistry_match_result": {
            "existing_exact_authority_match": outcome["existing_exact_authority_match"],
            "exact_signature_status": outcome["exact_signature_status"],
            "authority_match_evaluation": outcome["authority_match_evaluation"],
        },
        "strict_positive_shadow": {
            "status": shadow["shadow_status"],
            "reference_event_ids": json.loads(
                str(shadow["matching_positive_reference_event_ids_json"])
            ),
            "authoritative": False,
        },
        "event_specific_anomaly_flags": _event_anomalies(outcome),
    }


def _scope_options(unit: Mapping[str, Any]) -> list[dict[str, Any]]:
    common = {
        "status": "NON_AUTHORITATIVE_SCOPE_OPTION_ONLY",
        "production_authority_created": False,
    }
    return [
        {
            **common,
            "scope_option": "SAMPLE_BOUND_ONLY",
            "required_human_attestations": [
                "training_domain_relevance_decision",
                "each_event_training_use_decision",
                "reactive_atom_confirmation",
                "complete_role_partition_and_role_profile",
                "review_rationale_reviewer_id_and_attestation",
            ],
            "required_invariant_checks": [
                "exact_canonical_event_identity",
                "explicit_Cys_SG_endpoint_pair",
                "finite_POST_geometry",
            ],
        },
        {
            **common,
            "scope_option": "EXACT_COMPONENT_REUSE_CANDIDATE",
            "required_human_attestations": [
                "explicit_approval_of_exact_component_scope",
                "explicit_role_transfer_scope",
                "cross_event_reactive_center_equivalence",
            ],
            "required_invariant_checks": [
                "exact_CCD_component_id_and_graph_SHA256",
                "exact_CCD_atom_ID_namespace",
                "exact_reactive_atom_ID_and_element",
                "identical_formal_charge_and_retained_coverage_contract",
            ],
        },
        {
            **common,
            "scope_option": "EXACT_CHEMISTRY_SIGNATURE_REUSABLE_CANDIDATE",
            "required_human_attestations": [
                "explicit_reusable_chemistry_scope_approval",
                "reaction_family_and_warhead_rule_authority_approval",
                "role_rule_scope_and_cross_signature_prohibition",
            ],
            "required_invariant_checks": [
                "authoritative_pre_reaction_graph_available",
                "exact_chemistry_signature_computable_and_equal",
                "unique_reactive_atom_mapping",
                "automorphism_safe_role_mapping",
                "production_registry_successor_gate",
            ],
        },
    ]


def _unlock_simulation(unit: Mapping[str, Any]) -> dict[str, Any]:
    effective = int(unit["effective_single_decision_event_yield"])
    exact_signature_computable = unit["representative_outcome"]["exact_signature_status"] not in {
        "EXACT_SIGNATURE_NOT_COMPUTABLE_PRE_GRAPH",
        "EXACT_SIGNATURE_NOT_COMPUTABLE",
    }
    return {
        "status": "HYPOTHETICAL_NOT_AUTHORITY",
        "event_count_if_human_negative": effective,
        "event_count_if_sample_bound_positive": effective,
        "event_count_if_exact_component_reuse_later_approved": effective,
        "event_count_if_exact_signature_reuse_later_approved": (
            effective if exact_signature_computable else 0
        ),
        "exact_signature_projection_note": (
            "EXACT_SIGNATURE_EQUALITY_CURRENTLY_PROVABLE"
            if exact_signature_computable
            else "ZERO_CURRENTLY_PROVABLE_BECAUSE_PRE_GRAPH_SIGNATURE_IS_NOT_COMPUTABLE"
        ),
        "multi_event_predicate": (
            "same published review-unit component graph, CCD atom namespace, reactive atom, "
            "radius fingerprints, PRE status, charge representation, and atom-loss state"
        ),
        "census_or_model_usable_state_changed": False,
    }


def _human_form(event_ids: Sequence[str]) -> dict[str, Any]:
    return {
        "training_domain_relevance_decision": "UNDECIDED",
        "event_training_use_decisions": [
            {
                "canonical_event_id": event_id,
                "event_training_use_decision": "UNDECIDED",
            }
            for event_id in event_ids
        ],
        "reactive_atom_confirmation": "UNDECIDED",
        "warhead_atom_ids": [],
        "warhead_atom_ids_decision_state": "UNDECIDED",
        "scaffold_atom_ids": [],
        "scaffold_atom_ids_decision_state": "UNDECIDED",
        "linker_atom_ids": [],
        "linker_atom_ids_decision_state": "UNDECIDED",
        "role_profile": "UNDECIDED",
        "warhead_family_decision": "UNDECIDED",
        "reaction_family_decision": "UNDECIDED",
        "reusable_authority_scope_decision": "UNDECIDED",
        "review_rationale": "UNDECIDED",
        "reviewer_id": "UNDECIDED",
        "attestation": "UNDECIDED",
    }


def build_artifacts_v1(repo_root: Path) -> dict[str, bytes]:
    inputs = load_inputs_v1(repo_root)
    reconciliation_rows, reconciliation_summary = reconcile_review_queue_v1(inputs)
    shadow_rows, shadow_summary = build_shadow_inventory_v1(
        inputs=inputs, reconciliation_rows=reconciliation_rows
    )
    units = analyze_units_v1(
        inputs=inputs,
        reconciliation_summary=reconciliation_summary,
        shadow_rows=shadow_rows,
    )
    selected = select_calibration_units_v1(units)
    validate_selection_against_reconciliation_v1(
        selected=selected, reconciliation_rows=reconciliation_rows
    )
    reconciled_order = {
        unit["review_unit_id"]: rank
        for rank, unit in enumerate(
            sorted(
                units,
                key=lambda unit: (
                    -int(unit["effective_single_decision_event_yield"]),
                    {
                        UNIQUE_TRANSFER: 0,
                        EXACT_CENTER: 1,
                        EXACT_COMPONENT: 2,
                    }.get(unit["strongest_shadow_status"], 9),
                    int(unit["raw_priority_rank"]),
                    str(unit["review_unit_id"]),
                ),
            ),
            start=1,
        )
    }
    shadow_by_id = {row["canonical_event_id"]: row for row in shadow_rows}
    selected_rows: list[dict[str, object]] = []
    packet_units: list[dict[str, Any]] = []
    selected_source_paths = [
        QUEUE.as_posix(),
        CENSUS.as_posix(),
        SCALEUP_PROCESSING.as_posix(),
        FIRST500_PROCESSING_PARENT.as_posix(),
        ROUTING.as_posix(),
        POSITIVE_INDEX.as_posix(),
        DECISIONS.as_posix(),
        SUCCESSOR_DECISIONS.as_posix(),
    ]
    binding_by_path = {binding["path"]: binding for binding in inputs["bindings"]}
    selected_source_bindings = [binding_by_path[path] for path in selected_source_paths]
    for unit in selected:
        unlock = _unlock_simulation(unit)
        event_ids = list(unit["canonical_event_ids"])
        anomalies = {
            event_id: _event_anomalies(inputs["outcome_by_id"][event_id])
            for event_id in event_ids
        }
        representation = sorted(
            {
                anomaly
                for values in anomalies.values()
                for anomaly in values
                if "PRE_" in anomaly
                or "REPRESENT" in anomaly
                or "FORMAL_CHARGE" in anomaly
            }
        )
        leakage = sorted(
            event_id
            for event_id in event_ids
            if inputs["census_by_id"][event_id]["leakage_status"]
            not in {"", "NEW_COMPONENT_PENDING_SPLIT", "NEW_EXPANSION_COMPONENT"}
        )
        hypothesis = (
            "EXACT_COMPONENT_REUSE_CANDIDATE_ONLY"
            if unit["strongest_shadow_status"] in {EXACT_CENTER, EXACT_COMPONENT}
            else "SAMPLE_BOUND_ONLY_CANDIDATE"
        )
        row = {
            "selection_order": unit["selection_order"],
            "selection_lane": unit["selection_lane"],
            "review_unit_id": unit["review_unit_id"],
            "raw_priority_rank": unit["raw_priority_rank"],
            "current_reconciled_rank": reconciled_order[unit["review_unit_id"]],
            "raw_event_count": unit["raw_event_count"],
            "effective_single_decision_event_yield": unit[
                "effective_single_decision_event_yield"
            ],
            "unit_coherence_status": unit["unit_coherence_status"],
            "canonical_event_ids_json": _json_cell(event_ids),
            "pdb_ids_json": _json_cell(unit["pdb_ids"]),
            "ligand_component_ids_json": _json_cell(unit["ligand_component_ids"]),
            "ccd_component_graph_sha256": unit["ccd_component_graph_sha256"],
            "ccd_heavy_atom_graph_sha256": unit["ccd_heavy_atom_graph_sha256"],
            "ligand_reactive_atom": unit["ligand_reactive_atom"],
            "ligand_reactive_element": unit["ligand_reactive_element"],
            "reactive_center_radius1_sha256": unit[
                "reactive_center_radius1_sha256"
            ],
            "reactive_center_radius2_sha256": unit[
                "reactive_center_radius2_sha256"
            ],
            "full_coordinate_event_count": unit["full_coordinate_event_count"],
            "exact_reactive_pair_event_count": unit[
                "exact_reactive_pair_event_count"
            ],
            "POST_geometry_available_event_count": unit[
                "POST_geometry_available_event_count"
            ],
            "representation_blockers_json": _json_cell(representation),
            "leakage_conflicts_json": _json_cell(leakage),
            "current_decision_state_reconciliation_json": _json_cell(
                {CURRENTLY_UNREVIEWED: len(event_ids)}
            ),
            "strict_positive_shadow_reference_ids_json": _json_cell(
                unit["strict_shadow_reference_ids"]
            ),
            "shadow_mapping_status": unit["strongest_shadow_status"],
            "candidate_reusable_authority_scope_hypothesis": hypothesis,
            "event_count_if_human_negative": unlock[
                "event_count_if_human_negative"
            ],
            "event_count_if_sample_bound_positive": unlock[
                "event_count_if_sample_bound_positive"
            ],
            "event_count_if_exact_component_reuse_later_approved": unlock[
                "event_count_if_exact_component_reuse_later_approved"
            ],
            "event_count_if_exact_signature_reuse_later_approved": unlock[
                "event_count_if_exact_signature_reuse_later_approved"
            ],
            "unlock_simulation_status": "HYPOTHETICAL_NOT_AUTHORITY",
            "source_sha_bindings_json": _json_cell(selected_source_bindings),
        }
        selected_rows.append({field: row[field] for field in SELECTED_HEADER})
        packet_units.append(
            {
                "review_unit_id": unit["review_unit_id"],
                "selection_lane": unit["selection_lane"],
                "raw_queue_rank": unit["raw_priority_rank"],
                "current_reconciled_rank": reconciled_order[unit["review_unit_id"]],
                "raw_event_count": unit["raw_event_count"],
                "effective_single_decision_event_yield": unit[
                    "effective_single_decision_event_yield"
                ],
                "unit_coherence_status": unit["unit_coherence_status"],
                "canonical_event_ids": event_ids,
                "PDB_ids": unit["pdb_ids"],
                "ligand_component_ids": unit["ligand_component_ids"],
                "CCD_graph_SHA256": unit["ccd_component_graph_sha256"],
                "CCD_heavy_atom_graph_SHA256": unit[
                    "ccd_heavy_atom_graph_sha256"
                ],
                "reactive_atom_ID": unit["ligand_reactive_atom"],
                "reactive_atom_element": unit["ligand_reactive_element"],
                "radius1_fingerprint": unit["reactive_center_radius1_sha256"],
                "radius2_fingerprint": unit["reactive_center_radius2_sha256"],
                "full_coordinate_count": unit["full_coordinate_event_count"],
                "exact_pair_count": unit["exact_reactive_pair_event_count"],
                "POST_valid_count": unit["POST_geometry_available_event_count"],
                "representation_blockers": representation,
                "leakage_conflicts": leakage,
                "current_decision_state_reconciliation": {
                    CURRENTLY_UNREVIEWED: len(event_ids)
                },
                "strict_positive_shadow_reference_IDs": unit[
                    "strict_shadow_reference_ids"
                ],
                "shadow_mapping_status": unit["strongest_shadow_status"],
                "candidate_reusable_authority_scope_hypothesis": hypothesis,
                "machine_role_transfer_candidate_only": (
                    unit["machine_role_transfer_candidate_only"] or None
                ),
                "reusable_authority_scope_options_candidate_only": _scope_options(unit),
                "hypothetical_unlock_simulation": unlock,
                "events": [
                    _event_packet(
                        inputs=inputs,
                        event_id=event_id,
                        shadow=shadow_by_id[event_id],
                    )
                    for event_id in event_ids
                ],
                "human_review_form": _human_form(event_ids),
                "source_SHA_bindings": selected_source_bindings,
            }
        )

    reconciliation_payload = _csv_bytes(RECONCILIATION_HEADER, reconciliation_rows)
    shadow_payload = _csv_bytes(SHADOW_HEADER, shadow_rows)
    selected_payload = _csv_bytes(SELECTED_HEADER, selected_rows)
    packet = {
        "schema_version": SCHEMA_VERSION,
        "packet_role": "HUMAN_REVIEW_PREPARATION_ONLY_NO_DECISIONS",
        "authority_boundary": {
            "human_review_decision_created": False,
            "new_positive_authority_created": False,
            "new_negative_authority_created": False,
            "new_reaction_family_authority_created": False,
            "new_warhead_rule_authority_created": False,
            "new_reusable_chemistry_authority_created": False,
            "shadow_is_authority": False,
            "shadow_is_model_usable": False,
            "shadow_is_training_admission": False,
        },
        "source_SHA_bindings": inputs["bindings"],
        "reconciliation_summary": {
            key: value
            for key, value in reconciliation_summary.items()
            if key != "eligible_unit_ids"
        },
        "all_current_36_positive_reference_coverage": {
            key: value
            for key, value in shadow_summary.items()
            if key
            in {
                "current_positive_reference_event_count",
                "current_positive_reference_component_count",
                "full_CCD_role_partition_reference_event_count",
                "nontransferable_or_unexposed_role_reference_event_count",
                "positive_reference_records",
                "reference_ccd_source_bindings",
            }
        },
        "selection_contract": {
            "selected_unit_count": len(selected),
            "strict_positive_shadow_calibration_available": bool(
                shadow_summary["strict_positive_shadow_event_count"]
            ),
            "lane_A": "strict-shadow strength then effective yield then raw rank and unit ID",
            "lane_B": "maximum effective yield under exclusions",
            "lane_C": "maximum yield with different graph and radius2 from A and B",
            "biological_name_or_target_popularity_used": False,
        },
        "review_units": packet_units,
    }
    packet_payload = _json_bytes(packet)
    selected_total = sum(
        int(unit["effective_single_decision_event_yield"]) for unit in selected
    )
    summary = {
        "schema_version": SCHEMA_VERSION,
        "high_yield_human_review_authority_calibration_built": True,
        "baseline": {
            "HEAD": BASELINE_HEAD,
            "parent": BASELINE_PARENT,
            "tree": BASELINE_TREE,
            "subject": BASELINE_SUBJECT,
        },
        "reconciliation": {
            key: value
            for key, value in reconciliation_summary.items()
            if key != "eligible_unit_ids"
        },
        "calibration_eligible_event_count": reconciliation_summary[
            "currently_unreviewed_event_count"
        ],
        "calibration_eligible_unit_count": reconciliation_summary[
            "currently_unreviewed_unit_count"
        ],
        "strict_shadow": {
            key: value
            for key, value in shadow_summary.items()
            if key
            not in {"positive_reference_records", "reference_ccd_source_bindings"}
        },
        "unit_coherence": {
            "eligible_unit_count": len(units),
            "coherent_unit_count": sum(
                unit["unit_coherence_status"] == "UNIT_COHERENT_SINGLE_DECISION"
                for unit in units
            ),
            "unit_requires_subdivision_count": sum(
                unit["unit_coherence_status"] == "UNIT_REQUIRES_SUBDIVISION"
                for unit in units
            ),
        },
        "selection": {
            "selected_calibration_unit_count": len(selected),
            "selected_calibration_total_raw_event_yield": sum(
                int(unit["raw_event_count"]) for unit in selected
            ),
            "selected_calibration_total_effective_single_decision_event_yield": selected_total,
            "units": [
                {
                    "selection_lane": unit["selection_lane"],
                    "review_unit_id": unit["review_unit_id"],
                    "raw_event_yield": unit["raw_event_count"],
                    "effective_event_yield": unit[
                        "effective_single_decision_event_yield"
                    ],
                }
                for unit in selected
            ],
        },
        "authority_and_execution_safety": {
            "human_review_decision_created": False,
            "new_positive_authority_created": False,
            "new_negative_authority_created": False,
            "new_reaction_family_authority_created": False,
            "new_warhead_rule_authority_created": False,
            "existing_14_8_14_split_changed": False,
            "training_performed": False,
            "Trainer_used": False,
            "backward_performed": False,
            "optimizer_created": False,
            "network_performed": False,
            "bulk_ranks1001_1500_processed": False,
            "cumulative1000_rebuild_invoked": False,
            "cumulative1000_replay_invoked": False,
            "data_augmentation_performed": False,
            "feature_semantics_audit_reopened": False,
        },
        "candidate_precommit_profile_contract_supported": True,
        "published_successor_profile_contract_supported": True,
        "ready_for_human_review": True,
        "ready_for_gpt_review": True,
        "ready_for_publication": True,
        "recommended_next_step_exactly": (
            "gpt_audit_high_yield_calibration_packet_then_human_review_selected_units"
        ),
        "artifact_sha256_excluding_manifest_and_summary": {
            RECONCILIATION: _sha(reconciliation_payload),
            SHADOW: _sha(shadow_payload),
            SELECTED: _sha(selected_payload),
            PACKET: _sha(packet_payload),
        },
    }
    summary_payload = _json_bytes(summary)
    candidate_source_bindings = [
        _binding(inputs["repo_root"] / path, path.as_posix())
        for path in (SOURCE_RELATIVE, CHECKER_RELATIVE, TEST_RELATIVE)
    ]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "baseline_HEAD": BASELINE_HEAD,
        "baseline_parent": BASELINE_PARENT,
        "publication_subject": PUBLICATION_SUBJECT,
        "frozen_input_bindings": inputs["bindings"],
        "positive_reference_CCD_bindings": shadow_summary[
            "reference_ccd_source_bindings"
        ],
        "candidate_source_bindings": candidate_source_bindings,
        "output_sha256_excluding_manifest": {
            RECONCILIATION: _sha(reconciliation_payload),
            SHADOW: _sha(shadow_payload),
            SELECTED: _sha(selected_payload),
            PACKET: _sha(packet_payload),
            SUMMARY: _sha(summary_payload),
        },
        "exact9_contract": {
            "paths": sorted(AUTHORIZED_PATHS),
            "file_count": 9,
            "mode": "100644",
            "candidate_profile": "candidate_precommit_untracked",
            "published_profile": "published_successor",
        },
        "authority_contract": {
            "existing_decisions_modified": False,
            "current_positive_index_modified": False,
            "current_split_assignments_modified": False,
            "production_reusable_authority_registry_modified": False,
            "negative_rule_registry_modified": False,
            "shadow_non_authoritative": True,
            "human_decision_fields_all_undecided": True,
        },
        "training_performed": False,
        "network_performed": False,
    }
    artifacts = {
        RECONCILIATION: reconciliation_payload,
        SHADOW: shadow_payload,
        SELECTED: selected_payload,
        PACKET: packet_payload,
        MANIFEST: _json_bytes(manifest),
        SUMMARY: summary_payload,
    }
    if tuple(artifacts) != OUTPUT_FILENAMES:
        raise CalibrationSafetyError("OUTPUT_ARTIFACT_SET_INVALID")
    validate_artifacts_v1(artifacts)
    return artifacts


def validate_artifacts_v1(artifacts: Mapping[str, bytes]) -> None:
    if tuple(artifacts) != OUTPUT_FILENAMES:
        raise CalibrationSafetyError("ARTIFACT_FILE_SET_INVALID")
    reconciliation = list(
        csv.DictReader(io.StringIO(artifacts[RECONCILIATION].decode("utf-8")))
    )
    shadow = list(csv.DictReader(io.StringIO(artifacts[SHADOW].decode("utf-8"))))
    selected = list(csv.DictReader(io.StringIO(artifacts[SELECTED].decode("utf-8"))))
    packet = json.loads(artifacts[PACKET])
    summary = json.loads(artifacts[SUMMARY])
    manifest = json.loads(artifacts[MANIFEST])
    if (
        len(reconciliation) != 338
        or len({row["canonical_event_id"] for row in reconciliation}) != 338
        or Counter(row["current_review_status"] for row in reconciliation)
        != Counter(
            {
                CURRENTLY_UNREVIEWED: 305,
                COMPLETED_HUMAN_NEGATIVE: 24,
                CURRENTLY_IN_PROGRESS: 9,
            }
        )
    ):
        raise CalibrationSafetyError("MATERIALIZED_RECONCILIATION_INVALID")
    if (
        len(shadow) != 305
        or any(row["current_review_status"] != CURRENTLY_UNREVIEWED for row in shadow)
        or any(row["positive_reference_event_count"] != "36" for row in shadow)
        or any(
            row[field] != "false"
            for row in shadow
            for field in (
                "shadow_authoritative",
                "shadow_model_usable",
                "shadow_training_admitted",
            )
        )
    ):
        raise CalibrationSafetyError("MATERIALIZED_SHADOW_INVENTORY_INVALID")
    if (
        len(selected) != 3
        or len({row["review_unit_id"] for row in selected}) != 3
        or any(row["unit_coherence_status"] != "UNIT_COHERENT_SINGLE_DECISION" for row in selected)
        or any(row["unlock_simulation_status"] != "HYPOTHETICAL_NOT_AUTHORITY" for row in selected)
    ):
        raise CalibrationSafetyError("MATERIALIZED_SELECTION_INVALID")
    if len(packet.get("review_units", ())) != 3:
        raise CalibrationSafetyError("MATERIALIZED_PACKET_UNIT_COUNT_INVALID")
    for unit in packet["review_units"]:
        form = unit.get("human_review_form") or {}
        undecided = (
            "training_domain_relevance_decision",
            "reactive_atom_confirmation",
            "role_profile",
            "warhead_family_decision",
            "reaction_family_decision",
            "reusable_authority_scope_decision",
            "review_rationale",
            "reviewer_id",
            "attestation",
        )
        if any(form.get(field) != "UNDECIDED" for field in undecided):
            raise CalibrationSafetyError("HUMAN_DECISION_FIELD_NOT_UNDECIDED")
        if any(form.get(field) != [] for field in (
            "warhead_atom_ids", "scaffold_atom_ids", "linker_atom_ids"
        )):
            raise CalibrationSafetyError("HUMAN_ROLE_FIELD_MACHINE_PREFILLED")
        if len(unit.get("events", ())) != unit["raw_event_count"]:
            raise CalibrationSafetyError("PACKET_EVENT_COVERAGE_INVALID")
        if unit["hypothetical_unlock_simulation"]["status"] != (
            "HYPOTHETICAL_NOT_AUTHORITY"
        ):
            raise CalibrationSafetyError("PACKET_UNLOCK_NOT_MARKED_HYPOTHETICAL")
    if (
        summary.get("high_yield_human_review_authority_calibration_built") is not True
        or summary["selection"]["selected_calibration_unit_count"] != 3
        or summary["authority_and_execution_safety"]["training_performed"] is not False
        or manifest["exact9_contract"]["file_count"] != 9
        or manifest["authority_contract"]["shadow_non_authoritative"] is not True
    ):
        raise CalibrationSafetyError("SUMMARY_OR_MANIFEST_CONTRACT_INVALID")
    for name, expected in manifest["output_sha256_excluding_manifest"].items():
        if _sha(artifacts[name]) != expected:
            raise CalibrationSafetyError("MANIFEST_OUTPUT_SHA256_MISMATCH:" + name)


def check_materialized_v1(repo_root: Path) -> dict[str, Any]:
    expected = build_artifacts_v1(repo_root)
    output_root = repo_root.resolve() / OUTPUT_ROOT_RELATIVE
    observed: dict[str, bytes] = {}
    if not output_root.is_dir():
        raise CalibrationSafetyError("OUTPUT_ROOT_MISSING")
    names = sorted(path.name for path in output_root.iterdir() if path.is_file())
    if names != sorted(OUTPUT_FILENAMES):
        raise CalibrationSafetyError("OUTPUT_ROOT_FILE_SET_INVALID")
    for name in OUTPUT_FILENAMES:
        payload = (output_root / name).read_bytes()
        if payload != expected[name]:
            raise CalibrationSafetyError("MATERIALIZED_BYTES_MISMATCH:" + name)
        observed[name] = payload
    validate_artifacts_v1(observed)
    observation = observe_repository_state_v1(repo_root)
    profile = classify_repository_profile_v1(observation)
    if profile == "candidate_precommit_untracked" and set(observation["untracked"]) != AUTHORIZED_PATHS:
        raise CalibrationSafetyError("CANDIDATE_EXACT9_UNTRACKED_SET_INVALID")
    return {
        "profile": profile,
        "sha256": {name: _sha(payload) for name, payload in observed.items()},
        "summary": json.loads(observed[SUMMARY]),
    }


def materialize_v1(repo_root: Path) -> dict[str, str]:
    observation = observe_repository_state_v1(repo_root)
    if classify_repository_profile_v1(observation) != "candidate_precommit_untracked":
        raise CalibrationSafetyError("MATERIALIZATION_REQUIRES_CANDIDATE_PROFILE")
    artifacts = build_artifacts_v1(repo_root)
    if artifacts != build_artifacts_v1(repo_root):
        raise CalibrationSafetyError("DETERMINISTIC_DOUBLE_BUILD_FAILED")
    output_root = repo_root.resolve() / OUTPUT_ROOT_RELATIVE
    if output_root.exists():
        existing = sorted(path.name for path in output_root.iterdir() if path.is_file())
        if any(name not in OUTPUT_FILENAMES for name in existing):
            raise CalibrationSafetyError("OUTPUT_ROOT_CONTAINS_UNAUTHORIZED_FILE")
    for name, payload in artifacts.items():
        _atomic_write(output_root / name, payload)
    return {name: _sha(payload) for name, payload in artifacts.items()}


if __name__ == "__main__":
    repository = Path(__file__).resolve().parents[2]
    for filename, digest in materialize_v1(repository).items():
        print(f"{filename}={digest}")
