"""Materialize Current11 observed-to-parent atom and projected graph authority."""

from __future__ import annotations

import csv
import dataclasses
import hashlib
import io
import json
import subprocess
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


BASE_COMMIT = "34ff4dbb94a5caf4f8b393152e9694e5a8d7c2ce"
BASE_PARENT = "f8f6945c86a4258387e57691e206753d0b193793"
BASE_TREE = "e0276fd276cea27ddb617f5fa28dfd71ad35c9ba"
BASE_SUBJECT = "add CovaPIE Exact9 audited CCD parent graph authority v1"
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE Current11 observed atom projection authority v1"
)
SCHEMA_VERSION = (
    "covapie_current11_observed_to_parent_atom_projection_authority_v1"
)
AUTHORITY_CLASS = (
    "BASE_tracked_observed_atom_name_to_sha_attested_parent_ccd_exact_mapping"
)
OUTPUT_ROOT = Path("data/derived/covalent_small") / SCHEMA_VERSION

EXACT9_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_exact9_audited_local_ccd_parent_graph_authority_v1.py"
)
EXACT9_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_exact9_audited_local_ccd_parent_graph_authority_v1"
)
PARENT_ATOMS = EXACT9_ROOT / "covapie_exact9_parent_heavy_atom_authority.csv"
PARENT_BONDS = EXACT9_ROOT / "covapie_exact9_parent_heavy_bond_authority.csv"
PARENT_READINESS = (
    EXACT9_ROOT / "covapie_current11_parent_component_graph_readiness_matrix.csv"
)
EXACT9_MANIFEST = (
    EXACT9_ROOT
    / "covapie_exact9_audited_local_ccd_parent_graph_authority_manifest.json"
)
GRAPH_EVIDENCE = Path(
    "data/derived/covalent_small/"
    "covapie_independent_group_expansion_batch_independence_evidence_"
    "materialization_smoke_v0/covapie_ligand_graph_scaffold_evidence.csv"
)
FINAL_INDEX = Path(
    "data/derived/covalent_small/"
    "covapie_final_dataset_materialization_smoke_v0/final_dataset_index.csv"
)
ATOM_PAIR_MAPPING = Path(
    "data/derived/covalent_small/"
    "covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_"
    "evidence_validation_v1/"
    "covapie_atom_pair_atom_table_mapping_validation_matrix.csv"
)
HEAVY_PROJECTION = Path(
    "data/derived/covalent_small/"
    "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1/"
    "covapie_heavy_atom_disposition_and_index_projection_matrix.csv"
)
SAMPLE_PROJECTION = Path(
    "data/derived/covalent_small/"
    "covapie_training_feature_semantics_and_unknown_atom_policy_resolution_v1/"
    "covapie_sample_heavy_atom_projection_validation_matrix.csv"
)

LIGAND_ATOM_TABLES = (
    Path(
        "data/derived/covalent_small/covapie_sample_preparation_execution_"
        "smoke_v0/samples/6BV6_JUG/ligand_atom_table.csv"
    ),
    Path(
        "data/derived/covalent_small/covapie_sample_preparation_execution_"
        "smoke_v0/samples/6BV8_JUG/ligand_atom_table.csv"
    ),
    Path(
        "data/derived/covalent_small/covapie_sample_preparation_execution_"
        "smoke_v0/samples/6BV5_JUG/ligand_atom_table.csv"
    ),
    Path(
        "data/derived/covalent_small/covapie_independent_group_expansion_batch_"
        "sample_preparation_execution_smoke_v0/samples/1AEC_E64/"
        "ligand_atom_table.csv"
    ),
    Path(
        "data/derived/covalent_small/covapie_independent_group_expansion_batch_"
        "sample_preparation_execution_smoke_v0/samples/1AIM_ZYA/"
        "ligand_atom_table.csv"
    ),
    Path(
        "data/derived/covalent_small/covapie_independent_group_expansion_batch_"
        "sample_preparation_execution_smoke_v0/samples/1AU3_PCM/"
        "ligand_atom_table.csv"
    ),
    Path(
        "data/derived/covalent_small/covapie_independent_group_expansion_batch_"
        "sample_preparation_execution_smoke_v0/samples/1AU4_INP/"
        "ligand_atom_table.csv"
    ),
    Path(
        "data/derived/covalent_small/covapie_independent_group_expansion_batch_"
        "sample_preparation_execution_smoke_v0/samples/1AYU_INA/"
        "ligand_atom_table.csv"
    ),
    Path(
        "data/derived/covalent_small/covapie_independent_group_expansion_batch_"
        "sample_preparation_execution_smoke_v0/samples/1AYV_IN6/"
        "ligand_atom_table.csv"
    ),
    Path(
        "data/derived/covalent_small/covapie_independent_group_expansion_batch_"
        "sample_preparation_execution_smoke_v0/samples/1AYW_IN3/"
        "ligand_atom_table.csv"
    ),
    Path(
        "data/derived/covalent_small/covapie_independent_group_expansion_batch_"
        "sample_preparation_execution_smoke_v0/samples/1B02_UFP/"
        "ligand_atom_table.csv"
    ),
)

FROZEN_BASE_SHA256 = {
    EXACT9_SOURCE:
        "b2bc177fdd2e10cfc643329f08a12a22684eaa6317a398ae1d4d1b834525d4cd",
    PARENT_ATOMS:
        "d50b052c2ed2573ccfdcf66470a077744ad11f4a083daee11f20d794b3b23fe7",
    PARENT_BONDS:
        "26957b9f78217c808d2dc021cfab1a2bf78dd1708c46c49f220ae32a3a09ebbf",
    PARENT_READINESS:
        "3e49c995250862b5d2ad6ef69da05e27ada9c908d4ed278257c6258f55d7bfd9",
    EXACT9_MANIFEST:
        "c1d6157b89d54ce0d195bad620fda4db44b5a73f3f21a2c659d7fdaadc35fd51",
    GRAPH_EVIDENCE:
        "982a9f89a89d3a4ad6a3e468cfd16d2fdfd5435cbf6d593e086fbd7fadd3ec73",
    FINAL_INDEX:
        "c4c31888cb0f7c148b00656ccf22ab68fab842fcdafdee049b2f420eddc1302d",
    ATOM_PAIR_MAPPING:
        "9f26b25ed11d186a02a1f859de10a105605ce3af13805ac5a4be1ad73199df45",
    HEAVY_PROJECTION:
        "b53f438edffab32f78d07df839b8c8437ec4223e31bd8a8885deedf32497b4be",
    SAMPLE_PROJECTION:
        "63f1df49d9a6f4e0efbee6c8bb474deabaedea9cef91f27d2cf49f7caeee6f96",
    LIGAND_ATOM_TABLES[0]:
        "c91bb14b37c9b7231cb0e2fac4e2ba39ce65d65b6a9481b1e83b83890f2e1650",
    LIGAND_ATOM_TABLES[1]:
        "13d2148bbcf544b62bd256b7ab8f14f31187d550a9e75d8c6d72deddada87d4a",
    LIGAND_ATOM_TABLES[2]:
        "0f375a441d3d1718dfdbf084aebae0c4612aaae7905c8131018bed671fb6c70e",
    LIGAND_ATOM_TABLES[3]:
        "02f4f7157da8318076290de0b36d21c2e40233e45e315264a67209dd2b4dc0cf",
    LIGAND_ATOM_TABLES[4]:
        "a813b57350cfd2bfae664c7b0d7d92a0d5359b8b1274d39eae0a97a76f61bdfa",
    LIGAND_ATOM_TABLES[5]:
        "90c70d05a0a9c1026c90a6c85b9e1989afa8c51671fe084cbb7f063b9427616a",
    LIGAND_ATOM_TABLES[6]:
        "d6f3a76db2a5448141403007708682ed2278b6bd1137b3be65a95ea615912665",
    LIGAND_ATOM_TABLES[7]:
        "3ea203e5ee078792c31edc83074629ba29dda72f6c4f7d90b0aad1246673e399",
    LIGAND_ATOM_TABLES[8]:
        "dfdaa3d37f81a79e51fee9e24434eca353ce922bda0c927fedb053566276bf49",
    LIGAND_ATOM_TABLES[9]:
        "f8f3a1b5b9143b797acc18724e83be2fb0b89876b66081a584e908b83ed0a67c",
    LIGAND_ATOM_TABLES[10]:
        "f33a8ebf2edda9cb63e2f81d10812f549bf57858e6ae2ffcbde6282a49c35e9e",
}

SOURCE_INVENTORY_FILE = "covapie_observed_atom_projection_source_inventory.csv"
MAPPING_FILE = "covapie_current11_observed_to_parent_atom_mapping_authority.csv"
BOND_FILE = (
    "covapie_current11_parent_and_observed_projected_bond_authority.csv"
)
READINESS_FILE = "covapie_current11_observed_projection_readiness_matrix.csv"
FAILURE_FILE = "covapie_current11_observed_projection_failure_matrix.csv"
MANIFEST_FILE = (
    "covapie_current11_observed_to_parent_atom_projection_authority_manifest.json"
)
OUTPUT_FILES = (
    SOURCE_INVENTORY_FILE,
    MAPPING_FILE,
    BOND_FILE,
    READINESS_FILE,
    FAILURE_FILE,
    MANIFEST_FILE,
)
EXACT10_PATHS = (
    Path(
        "src/covalent_ext/"
        "covapie_current11_observed_to_parent_atom_projection_authority_v1.py"
    ),
    Path(
        "tests/"
        "test_covapie_current11_observed_to_parent_atom_projection_authority_v1.py"
    ),
    Path(
        "scripts/"
        "check_covapie_current11_observed_to_parent_atom_projection_authority_v1.py"
    ),
    Path(
        "docs/"
        "covapie_current11_observed_to_parent_atom_projection_authority_v1_summary.md"
    ),
    *(OUTPUT_ROOT / name for name in OUTPUT_FILES),
)

SOURCE_COLUMNS = (
    "source_path", "source_sha256", "source_kind", "BASE_tracked",
    "row_level_atom_names_present", "element_present",
    "source_row_index_present", "retained_local_index_present",
    "Current11_coverage", "authority_class", "blocking_reasons", "verified",
)
MAPPING_COLUMNS = (
    "sample_index_row_id", "pdb_id", "ligand_comp_id",
    "observed_atom_name", "observed_type_symbol",
    "source_full_atom_row_index", "retained_heavy_local_index_0based",
    "parent_ccd_atom_id", "parent_ccd_type_symbol",
    "parent_ccd_formal_charge", "parent_ccd_heavy_atom_row_index_0based",
    "atom_name_exact_match", "element_exact_match", "reactive_ligand_atom",
    "component_parent_graph_sha256", "observed_graph_sha256",
    "mapping_authority_source_path", "mapping_authority_source_sha256",
    "authority_class", "verified",
)
BOND_COLUMNS = (
    "sample_index_row_id", "pdb_id", "ligand_comp_id",
    "parent_ccd_atom_id_1", "parent_ccd_atom_id_2",
    "normalized_bond_order", "retained_heavy_local_index_1",
    "retained_heavy_local_index_1_valid", "retained_heavy_local_index_2",
    "retained_heavy_local_index_2_valid", "projected_to_observed_graph",
    "projection_disposition", "component_parent_graph_sha256",
    "observed_graph_sha256", "verified",
)
READINESS_COLUMNS = (
    "sample_index_row_id", "pdb_id", "ligand_comp_id",
    "parent_component_graph_authority_available",
    "observed_atom_projection_exact", "observed_projected_graph_available",
    "parent_graph_valid", "observed_graph_valid",
    "pre_reaction_connectivity_available",
    "pre_reaction_bond_order_available", "observed_atom_count",
    "projected_bond_count", "observed_graph_sha256",
    "reactive_ligand_atom_available", "retained_local_index_contiguous",
    "reaction_family_label_available", "approved_warhead_rule_available",
    "role_proposal_available", "minimal_seed_proposal_available",
    "human_gold_review_completed", "ready_for_mask_materialization",
    "ready_for_tensorization", "ready_for_model_integration",
    "ready_for_training", "planned_covalent_model_module_count",
    "integrated_covalent_model_module_count", "blocking_reasons", "verified",
)
FAILURE_COLUMNS = (
    "failure_case", "mutation_signature", "mutated_fields",
    "expected_reasons", "observed_reasons", "expected_reasons_verified",
    "fails_closed", "ready_for_reaction_family_rule_design",
    "ready_for_role_proposal_generation", "ready_for_mask_materialization",
    "ready_for_model_integration", "ready_for_training", "verified",
)

NORMALIZED_BOND_ORDERS = frozenset(("single", "double", "triple", "aromatic"))


@dataclass(frozen=True)
class ObservedAtom:
    sample_index_row_id: str
    pdb_id: str
    ligand_comp_id: str
    atom_name: str
    type_symbol: str
    source_full_atom_row_index: int
    retained_heavy_local_index_0based: int
    reactive_ligand_atom: bool
    source_path: Path
    source_sha256: str


@dataclass(frozen=True)
class ProjectionResult:
    source_rows: tuple[Mapping[str, Any], ...]
    mapping_rows: tuple[Mapping[str, Any], ...]
    bond_rows: tuple[Mapping[str, Any], ...]
    readiness_rows: tuple[Mapping[str, Any], ...]
    failure_rows: tuple[Mapping[str, Any], ...]
    sample_graph_sha256: Mapping[str, str]
    parent_expanded_atom_count: int
    parent_expanded_bond_count: int
    projected_bond_count: int
    verified_leaving_group_bond_count: int
    missing_parent_atom_count: int
    unexplained_missing_parent_atom_count: int
    transaction_succeeded: bool
    transaction_blocking_reasons: tuple[str, ...]


@dataclass(frozen=True)
class FailureScenario:
    observed_source_present: bool = True
    observed_source_base_tracked: bool = True
    sample_coverage_complete: bool = True
    atom_row_coverage_complete: bool = True
    duplicate_sample_identity_count: int = 0
    duplicate_observed_atom_name_count: int = 0
    duplicate_source_full_row_index_count: int = 0
    duplicate_retained_local_index_count: int = 0
    retained_local_indices_contiguous: bool = True
    observed_atom_name_present: bool = True
    parent_ccd_atom_present: bool = True
    element_matches: bool = True
    reactive_atom_count: int = 1
    unexpected_observed_atom_count: int = 0
    unexplained_parent_atom_missing_count: int = 0
    leaving_group_evidence_consistent: bool = True
    leaving_group_parent_bond_present: bool = True
    projected_bond_endpoint_complete: bool = True
    duplicate_projected_bond_count: int = 0
    observed_graph_connected: bool = True
    graph_sha_deterministic: bool = True
    partial_materialization_attempted: bool = False
    execution_boundary_crossed: bool = False


@dataclass(frozen=True)
class FailureObservation:
    reasons: tuple[str, ...]
    fails_closed: bool
    ready_for_reaction_family_rule_design: bool
    ready_for_role_proposal_generation: bool
    ready_for_mask_materialization: bool
    ready_for_model_integration: bool
    ready_for_training: bool


BASELINE_SCENARIO = FailureScenario()
FAILURE_MUTATIONS: dict[str, tuple[str, Any, str]] = {
    "observed source missing":
        ("observed_source_present", False, "observed_source_missing"),
    "observed source not BASE tracked":
        ("observed_source_base_tracked", False, "observed_source_not_BASE_tracked"),
    "sample coverage incomplete":
        ("sample_coverage_complete", False, "sample_coverage_incomplete"),
    "atom row coverage incomplete":
        ("atom_row_coverage_complete", False, "atom_row_coverage_incomplete"),
    "duplicate sample identity":
        ("duplicate_sample_identity_count", 1, "duplicate_sample_identity"),
    "duplicate observed atom name":
        ("duplicate_observed_atom_name_count", 1, "duplicate_observed_atom_name"),
    "duplicate source full-row index":
        (
            "duplicate_source_full_row_index_count", 1,
            "duplicate_source_full_row_index",
        ),
    "duplicate retained local index":
        (
            "duplicate_retained_local_index_count", 1,
            "duplicate_retained_local_index",
        ),
    "non-contiguous retained local index":
        (
            "retained_local_indices_contiguous", False,
            "retained_local_index_noncontiguous",
        ),
    "observed atom name missing":
        ("observed_atom_name_present", False, "observed_atom_name_missing"),
    "parent CCD atom missing":
        ("parent_ccd_atom_present", False, "parent_CCD_atom_missing"),
    "element mismatch":
        ("element_matches", False, "observed_parent_element_mismatch"),
    "reactive atom absent":
        ("reactive_atom_count", 0, "reactive_ligand_atom_absent"),
    "reactive atom duplicated":
        ("reactive_atom_count", 2, "reactive_ligand_atom_duplicated"),
    "unexpected observed atom":
        ("unexpected_observed_atom_count", 1, "unexpected_observed_atom"),
    "unexplained parent atom missing":
        (
            "unexplained_parent_atom_missing_count", 1,
            "unexplained_parent_atom_missing",
        ),
    "leaving-group evidence inconsistent":
        (
            "leaving_group_evidence_consistent", False,
            "leaving_group_evidence_inconsistent",
        ),
    "leaving-group parent bond missing":
        (
            "leaving_group_parent_bond_present", False,
            "leaving_group_parent_bond_missing",
        ),
    "projected bond endpoint missing":
        (
            "projected_bond_endpoint_complete", False,
            "projected_bond_endpoint_missing",
        ),
    "duplicate projected bond":
        ("duplicate_projected_bond_count", 1, "duplicate_projected_bond"),
    "observed graph disconnected":
        ("observed_graph_connected", False, "observed_graph_disconnected"),
    "graph SHA nondeterministic":
        ("graph_sha_deterministic", False, "observed_graph_SHA_nondeterministic"),
    "partial materialization attempted":
        (
            "partial_materialization_attempted", True,
            "partial_materialization_attempted",
        ),
    "execution boundary crossed":
        ("execution_boundary_crossed", True, "execution_boundary_crossed"),
}


def _git(repo_root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ("git", *arguments),
        cwd=repo_root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            "git_command_failed:" + " ".join(arguments) + ":"
            + result.stderr.decode("utf-8", errors="replace")
        )
    return result


def base_bytes(repo_root: Path, relative_path: Path) -> bytes:
    """Read one frozen tracked source using the formal BASE object."""

    return _git(
        repo_root, "show", f"{BASE_COMMIT}:{relative_path.as_posix()}"
    ).stdout


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


def _csv_header(payload: bytes) -> tuple[str, ...]:
    reader = csv.reader(io.StringIO(payload.decode("utf-8")))
    return tuple(next(reader))


def _csv_bytes(
    columns: Sequence[str], rows: Iterable[Mapping[str, Any]]
) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=columns, lineterminator="\n", extrasaction="raise"
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({column: _cell(row.get(column, "")) for column in columns})
    return stream.getvalue().encode("utf-8")


def _cell(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return ""
    return str(value)


def _lower_bool(value: str) -> bool:
    if value not in ("true", "false"):
        raise ValueError("lowercase_boolean_invalid")
    return value == "true"


def _source_bool(value: str) -> bool:
    if value not in ("True", "False"):
        raise ValueError("source_boolean_invalid")
    return value == "True"


def validate_execution_boundary_v2(repo_root: Path) -> str:
    """Classify and validate the pre-commit or exact-successor lifecycle."""

    shown = _git(
        repo_root, "show", "-s", "--format=%H%n%P%n%T%n%s", BASE_COMMIT
    ).stdout.decode("utf-8").splitlines()
    expected = [BASE_COMMIT, BASE_PARENT, BASE_TREE, BASE_SUBJECT]
    if shown != expected:
        raise ValueError("formal_BASE_identity_mismatch")
    head = _git(repo_root, "rev-parse", "HEAD").stdout.decode().strip()
    if head == BASE_COMMIT:
        return "pre_commit"

    commit_payload = _git(repo_root, "cat-file", "commit", head).stdout
    headers, separator, message = commit_payload.partition(b"\n\n")
    if not separator:
        raise ValueError("successor_commit_object_malformed")
    parents = tuple(
        line.removeprefix(b"parent ").decode("ascii")
        for line in headers.splitlines()
        if line.startswith(b"parent ")
    )
    if parents != (BASE_COMMIT,):
        raise ValueError("successor_parent_not_exact_BASE")
    subject, subject_separator, body = message.partition(b"\n")
    if (
        not subject_separator
        or subject.decode("utf-8", errors="strict") != FORMAL_COMMIT_SUBJECT
    ):
        raise ValueError("successor_subject_mismatch")
    if body:
        raise ValueError("successor_commit_body_nonempty")

    changed = tuple(
        item.decode("utf-8", errors="strict")
        for item in _git(
            repo_root,
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            "-z",
            head,
        ).stdout.split(b"\0")
        if item
    )
    exact_names = tuple(path.as_posix() for path in EXACT10_PATHS)
    if len(changed) != len(exact_names) or set(changed) != set(exact_names):
        raise ValueError("successor_changed_path_inventory_mismatch")

    tree_rows = tuple(
        item
        for item in _git(
            repo_root, "ls-tree", "-r", "-z", head, "--", *exact_names
        ).stdout.split(b"\0")
        if item
    )
    observed_names: list[str] = []
    for row in tree_rows:
        metadata, tab, name = row.partition(b"\t")
        if not tab or not metadata.startswith(b"100644 blob "):
            raise ValueError("successor_exact10_file_mode_invalid")
        observed_names.append(name.decode("utf-8", errors="strict"))
    if (
        len(observed_names) != len(exact_names)
        or set(observed_names) != set(exact_names)
    ):
        raise ValueError("successor_exact10_tree_inventory_mismatch")

    branch = _git(
        repo_root, "symbolic-ref", "--quiet", "--short", "HEAD", check=False
    )
    if branch.returncode != 0:
        return "detached_candidate_post_commit"
    if branch.stdout.decode("utf-8").strip() != "main":
        raise ValueError("successor_formal_branch_not_main")
    origin = _git(
        repo_root,
        "rev-parse",
        "--verify",
        "refs/remotes/origin/main",
        check=False,
    )
    if origin.returncode != 0:
        raise ValueError("successor_origin_main_missing")
    origin_main = origin.stdout.decode("utf-8").strip()
    if origin_main == BASE_COMMIT:
        return "formal_main_post_commit_unpushed"
    if origin_main == head:
        return "formal_main_post_push"
    raise ValueError("successor_origin_main_lifecycle_mismatch")


def load_frozen_sources(repo_root: Path) -> dict[Path, bytes]:
    """Read and SHA-freeze every actually checked candidate from BASE."""

    validate_execution_boundary_v2(repo_root)
    payloads: dict[Path, bytes] = {}
    for path, expected_sha in FROZEN_BASE_SHA256.items():
        payload = base_bytes(repo_root, path)
        if _sha256(payload) != expected_sha:
            raise ValueError(f"BASE_source_SHA_mismatch:{path.as_posix()}")
        payloads[path] = payload
    return payloads


def canonical_observed_graph_sha256(
    atoms: Iterable[tuple[str, str, int]],
    bonds: Iterable[tuple[str, str, str]],
) -> str:
    payload = {
        "atoms": [
            list(item)
            for item in sorted(
                (name, element, int(charge))
                for name, element, charge in atoms
            )
        ],
        "bonds": [
            list(item)
            for item in sorted(
                (min(left, right), max(left, right), order)
                for left, right, order in bonds
            )
        ],
    }
    return _sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def _connected(vertices: set[str], edges: set[tuple[str, str]]) -> bool:
    if not vertices:
        return False
    adjacency = {vertex: set() for vertex in vertices}
    for left, right in edges:
        adjacency[left].add(right)
        adjacency[right].add(left)
    visited: set[str] = set()
    queue = deque([min(vertices)])
    while queue:
        vertex = queue.popleft()
        if vertex in visited:
            continue
        visited.add(vertex)
        queue.extend(sorted(adjacency[vertex] - visited))
    return visited == vertices


def observe_failure_scenario(scenario: FailureScenario) -> FailureObservation:
    reasons: list[str] = []
    if not scenario.observed_source_present:
        reasons.append("observed_source_missing")
    if not scenario.observed_source_base_tracked:
        reasons.append("observed_source_not_BASE_tracked")
    if not scenario.sample_coverage_complete:
        reasons.append("sample_coverage_incomplete")
    if not scenario.atom_row_coverage_complete:
        reasons.append("atom_row_coverage_incomplete")
    if scenario.duplicate_sample_identity_count:
        reasons.append("duplicate_sample_identity")
    if scenario.duplicate_observed_atom_name_count:
        reasons.append("duplicate_observed_atom_name")
    if scenario.duplicate_source_full_row_index_count:
        reasons.append("duplicate_source_full_row_index")
    if scenario.duplicate_retained_local_index_count:
        reasons.append("duplicate_retained_local_index")
    if not scenario.retained_local_indices_contiguous:
        reasons.append("retained_local_index_noncontiguous")
    if not scenario.observed_atom_name_present:
        reasons.append("observed_atom_name_missing")
    if not scenario.parent_ccd_atom_present:
        reasons.append("parent_CCD_atom_missing")
    if not scenario.element_matches:
        reasons.append("observed_parent_element_mismatch")
    if scenario.reactive_atom_count == 0:
        reasons.append("reactive_ligand_atom_absent")
    if scenario.reactive_atom_count > 1:
        reasons.append("reactive_ligand_atom_duplicated")
    if scenario.unexpected_observed_atom_count:
        reasons.append("unexpected_observed_atom")
    if scenario.unexplained_parent_atom_missing_count:
        reasons.append("unexplained_parent_atom_missing")
    if not scenario.leaving_group_evidence_consistent:
        reasons.append("leaving_group_evidence_inconsistent")
    if not scenario.leaving_group_parent_bond_present:
        reasons.append("leaving_group_parent_bond_missing")
    if not scenario.projected_bond_endpoint_complete:
        reasons.append("projected_bond_endpoint_missing")
    if scenario.duplicate_projected_bond_count:
        reasons.append("duplicate_projected_bond")
    if not scenario.observed_graph_connected:
        reasons.append("observed_graph_disconnected")
    if not scenario.graph_sha_deterministic:
        reasons.append("observed_graph_SHA_nondeterministic")
    if scenario.partial_materialization_attempted:
        reasons.append("partial_materialization_attempted")
    if scenario.execution_boundary_crossed:
        reasons.append("execution_boundary_crossed")
    unique_reasons = tuple(dict.fromkeys(reasons))
    blocked = bool(unique_reasons)
    return FailureObservation(
        reasons=unique_reasons,
        fails_closed=blocked,
        ready_for_reaction_family_rule_design=False,
        ready_for_role_proposal_generation=False,
        ready_for_mask_materialization=False,
        ready_for_model_integration=False,
        ready_for_training=False,
    )


def build_failure_rows() -> tuple[Mapping[str, Any], ...]:
    baseline = observe_failure_scenario(BASELINE_SCENARIO)
    if baseline.reasons:
        raise ValueError("failure_baseline_not_clean")
    rows: list[Mapping[str, Any]] = []
    signatures: set[str] = set()
    for case, (field, value, expected_reason) in FAILURE_MUTATIONS.items():
        old_value = getattr(BASELINE_SCENARIO, field)
        if type(old_value) is not type(value) or old_value == value:
            raise ValueError("failure_mutation_not_exact_typed")
        scenario = dataclasses.replace(BASELINE_SCENARIO, **{field: value})
        observation = observe_failure_scenario(scenario)
        mutated = {field: value}
        signature = _sha256(
            json.dumps(
                mutated, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        )
        if signature in signatures:
            raise ValueError("failure_mutation_signature_duplicate")
        signatures.add(signature)
        expected_verified = expected_reason in observation.reasons
        if not expected_verified or not observation.fails_closed:
            raise ValueError("failure_mutation_did_not_fail_closed")
        rows.append({
            "failure_case": case,
            "mutation_signature": signature,
            "mutated_fields": json.dumps(
                mutated, sort_keys=True, separators=(",", ":")
            ),
            "expected_reasons": expected_reason,
            "observed_reasons": ";".join(observation.reasons),
            "expected_reasons_verified": expected_verified,
            "fails_closed": observation.fails_closed,
            "ready_for_reaction_family_rule_design":
                observation.ready_for_reaction_family_rule_design,
            "ready_for_role_proposal_generation":
                observation.ready_for_role_proposal_generation,
            "ready_for_mask_materialization":
                observation.ready_for_mask_materialization,
            "ready_for_model_integration":
                observation.ready_for_model_integration,
            "ready_for_training": observation.ready_for_training,
            "verified": True,
        })
    return tuple(rows)


def _source_inventory(
    payloads: Mapping[Path, bytes],
    retained_counts: Mapping[Path, int],
) -> tuple[Mapping[str, Any], ...]:
    rows: list[Mapping[str, Any]] = []
    for path in FROZEN_BASE_SHA256:
        header = _csv_header(payloads[path]) if path.suffix == ".csv" else ()
        if path == EXACT9_SOURCE:
            kind = "Exact9_parent_graph_production_source"
        elif path == PARENT_ATOMS:
            kind = "Exact9_parent_heavy_atom_authority"
        elif path == PARENT_BONDS:
            kind = "Exact9_parent_heavy_bond_authority"
        elif path == PARENT_READINESS:
            kind = "Current11_parent_graph_readiness_identity_authority"
        elif path == EXACT9_MANIFEST:
            kind = "Exact9_parent_graph_manifest"
        elif path == GRAPH_EVIDENCE:
            kind = "Current11_atom_inventory_and_leaving_group_evidence"
        elif path == FINAL_INDEX:
            kind = "original_Current3_sample_index"
        elif path == ATOM_PAIR_MAPPING:
            kind = "Current11_reactive_atom_row_mapping_validation"
        elif path == HEAVY_PROJECTION:
            kind = "Current11_retained_heavy_source_and_local_index_authority"
        elif path == SAMPLE_PROJECTION:
            kind = "Current11_sample_heavy_projection_validation"
        else:
            kind = "BASE_tracked_observed_ligand_full_atom_row_authority"

        if path == HEAVY_PROJECTION:
            coverage = "11/11 samples;323/323 retained-heavy ligand rows"
            authority_class = (
                "BASE_tracked_retained_heavy_source_row_and_local_index_authority"
            )
        elif path in LIGAND_ATOM_TABLES:
            coverage = (
                f"1/11 samples;{retained_counts.get(path, 0)} retained-heavy rows"
            )
            authority_class = "BASE_tracked_observed_atom_name_row_authority"
        elif path in (PARENT_ATOMS, PARENT_BONDS, EXACT9_MANIFEST, EXACT9_SOURCE):
            coverage = "9/9 parent components"
            authority_class = "BASE_tracked_Exact9_parent_graph_authority"
        elif path in (
            PARENT_READINESS, GRAPH_EVIDENCE, ATOM_PAIR_MAPPING, SAMPLE_PROJECTION
        ):
            coverage = "11/11 samples"
            authority_class = "BASE_tracked_Current11_supporting_evidence"
        elif path == FINAL_INDEX:
            coverage = "3/11 samples"
            authority_class = "BASE_tracked_original_sample_index_evidence"
        else:
            coverage = "supporting source"
            authority_class = "BASE_tracked_supporting_evidence"

        row_level_names = (
            path in LIGAND_ATOM_TABLES and "atom_name" in header
        )
        element_present = (
            "type_symbol" in header or "ccd_type_symbol" in header
        )
        source_index_present = (
            "source_atom_row_index_0based" in header
            or "source_full_atom_row_index" in header
        )
        retained_index_present = (
            "projected_heavy_atom_row_index_0based" in header
            or "retained_heavy_local_index_0based" in header
        )
        rows.append({
            "source_path": path.as_posix(),
            "source_sha256": FROZEN_BASE_SHA256[path],
            "source_kind": kind,
            "BASE_tracked": True,
            "row_level_atom_names_present": row_level_names,
            "element_present": element_present,
            "source_row_index_present": source_index_present,
            "retained_local_index_present": retained_index_present,
            "Current11_coverage": coverage,
            "authority_class": authority_class,
            "blocking_reasons": "",
            "verified": True,
        })
    return tuple(rows)


def _phase_a(
    payloads: Mapping[Path, bytes],
) -> tuple[
    tuple[dict[str, str], ...],
    tuple[ObservedAtom, ...],
    dict[str, dict[str, str]],
    tuple[Mapping[str, Any], ...],
]:
    samples = tuple(_csv_rows(payloads[PARENT_READINESS]))
    if len(samples) != 11:
        raise ValueError("sample_coverage_incomplete")
    identities = [
        (row["sample_index_row_id"], row["pdb_id"], row["ligand_comp_id"])
        for row in samples
    ]
    if len(set(identities)) != 11:
        raise ValueError("duplicate_sample_identity")
    if len({row["sample_index_row_id"] for row in samples}) != 11:
        raise ValueError("duplicate_sample_identity")
    if len({row["ligand_comp_id"] for row in samples}) != 9:
        raise ValueError("Current11_component_closure_invalid")
    sample_by_id = {row["sample_index_row_id"]: row for row in samples}

    evidence_rows = _csv_rows(payloads[GRAPH_EVIDENCE])
    evidence_by_id = {row["sample_index_row_id"]: row for row in evidence_rows}
    if set(evidence_by_id) != set(sample_by_id) or len(evidence_rows) != 11:
        raise ValueError("sample_coverage_incomplete")
    for sample_id, sample in sample_by_id.items():
        evidence = evidence_by_id[sample_id]
        if (
            evidence["pdb_id"] != sample["pdb_id"]
            or evidence["ligand_comp_id"] != sample["ligand_comp_id"]
        ):
            raise ValueError("sample_identity_mismatch")

    source_table_rows = {
        path: _csv_rows(payloads[path]) for path in LIGAND_ATOM_TABLES
    }
    projection_rows = [
        row for row in _csv_rows(payloads[HEAVY_PROJECTION])
        if row["domain"] == "ligand_atom"
    ]
    retained_rows = [
        row for row in projection_rows
        if _lower_bool(row["retained_for_checkpoint_model"])
    ]
    if len(retained_rows) != 323:
        raise ValueError("atom_row_coverage_incomplete")

    observed: list[ObservedAtom] = []
    retained_counts: dict[Path, int] = defaultdict(int)
    for row in retained_rows:
        sample_id = row["sample_index_row_id"]
        if sample_id not in sample_by_id:
            raise ValueError("sample_coverage_incomplete")
        sample = sample_by_id[sample_id]
        if (
            row["pdb_id"] != sample["pdb_id"]
            or row["ligand_identity"] != sample["ligand_comp_id"]
        ):
            raise ValueError("sample_identity_mismatch")
        source_path = Path(row["source_table_path"])
        if source_path not in source_table_rows:
            raise ValueError("observed_source_not_BASE_tracked")
        if row["source_table_sha256"] != FROZEN_BASE_SHA256[source_path]:
            raise ValueError("observed_source_SHA_mismatch")
        try:
            source_index = int(row["source_atom_row_index_0based"])
            local_index = int(row["projected_heavy_atom_row_index_0based"])
            source_row = source_table_rows[source_path][source_index]
        except (ValueError, IndexError) as exc:
            raise ValueError("source_full_atom_row_index_invalid") from exc
        if (
            source_row["pdb_id"] != sample["pdb_id"]
            or source_row["ligand_comp_id"] != sample["ligand_comp_id"]
            or source_row["expected_het_id"] != sample["ligand_comp_id"]
        ):
            raise ValueError("source_row_sample_identity_mismatch")
        atom_name = source_row["atom_name"]
        if not atom_name:
            raise ValueError("observed_atom_name_missing")
        if source_row["type_symbol"] != row["type_symbol"]:
            raise ValueError("source_projection_element_mismatch")
        if row["projection_disposition"] != "retain_checkpoint_10d":
            raise ValueError("retained_heavy_disposition_invalid")
        observed.append(ObservedAtom(
            sample_index_row_id=sample_id,
            pdb_id=sample["pdb_id"],
            ligand_comp_id=sample["ligand_comp_id"],
            atom_name=atom_name,
            type_symbol=row["type_symbol"],
            source_full_atom_row_index=source_index,
            retained_heavy_local_index_0based=local_index,
            reactive_ligand_atom=_source_bool(
                source_row["is_covalent_ligand_atom"]
            ),
            source_path=source_path,
            source_sha256=FROZEN_BASE_SHA256[source_path],
        ))
        retained_counts[source_path] += 1

    for sample_id in sample_by_id:
        subset = [atom for atom in observed if atom.sample_index_row_id == sample_id]
        if not subset:
            raise ValueError("sample_coverage_incomplete")
        names = [atom.atom_name for atom in subset]
        source_indices = [atom.source_full_atom_row_index for atom in subset]
        local_indices = [
            atom.retained_heavy_local_index_0based for atom in subset
        ]
        if len(names) != len(set(names)):
            raise ValueError("duplicate_observed_atom_name")
        if len(source_indices) != len(set(source_indices)):
            raise ValueError("duplicate_source_full_row_index")
        if len(local_indices) != len(set(local_indices)):
            raise ValueError("duplicate_retained_local_index")
        if sorted(local_indices) != list(range(len(subset))):
            raise ValueError("retained_local_index_noncontiguous")
        reactive = [atom for atom in subset if atom.reactive_ligand_atom]
        if not reactive:
            raise ValueError("reactive_ligand_atom_absent")
        if len(reactive) != 1:
            raise ValueError("reactive_ligand_atom_duplicated")
        evidence = evidence_by_id[sample_id]
        if evidence["ligand_covalent_atom_name"] != reactive[0].atom_name:
            raise ValueError("reactive_ligand_atom_evidence_mismatch")
        evidence_observed = set(
            filter(None, evidence["observed_post_covalent_heavy_atom_ids"].split(";"))
        )
        if evidence_observed != set(names):
            raise ValueError("observed_atom_inventory_evidence_mismatch")

    pair_rows = [
        row for row in _csv_rows(payloads[ATOM_PAIR_MAPPING])
        if row["entity_role"] == "ligand_atom"
    ]
    if len(pair_rows) != 11:
        raise ValueError("reactive_atom_mapping_coverage_incomplete")
    pair_by_id = {row["sample_index_row_id"]: row for row in pair_rows}
    if set(pair_by_id) != set(sample_by_id):
        raise ValueError("reactive_atom_mapping_coverage_incomplete")
    for sample_id in sample_by_id:
        reactive = next(
            atom for atom in observed
            if atom.sample_index_row_id == sample_id and atom.reactive_ligand_atom
        )
        pair = pair_by_id[sample_id]
        if (
            pair["target_table_path"] != reactive.source_path.as_posix()
            or pair["target_table_sha256"] != reactive.source_sha256
            or int(pair["matched_row_index_0based"])
                != reactive.source_full_atom_row_index
            or pair["candidate_match_count"] != "1"
            or pair["mapping_outcome"] != "mapped"
            or pair["mapping_reason"] != "exact_one_identity_mapping"
            or pair["verified"] != "true"
        ):
            raise ValueError("reactive_atom_row_mapping_inconsistent")

    sample_validation = _csv_rows(payloads[SAMPLE_PROJECTION])
    if len(sample_validation) != 11:
        raise ValueError("sample_coverage_incomplete")
    retained_by_sample = {
        row["sample_index_row_id"]: int(row["retained_ligand_heavy_count"])
        for row in sample_validation
    }
    for sample_id in sample_by_id:
        actual = sum(atom.sample_index_row_id == sample_id for atom in observed)
        if retained_by_sample.get(sample_id) != actual:
            raise ValueError("atom_row_coverage_incomplete")

    source_rows = _source_inventory(payloads, retained_counts)
    return samples, tuple(observed), evidence_by_id, source_rows


def _phase_b(
    payloads: Mapping[Path, bytes],
    samples: Sequence[Mapping[str, str]],
    observed: Sequence[ObservedAtom],
    evidence_by_id: Mapping[str, Mapping[str, str]],
    source_rows: tuple[Mapping[str, Any], ...],
) -> ProjectionResult:
    parent_atoms = _csv_rows(payloads[PARENT_ATOMS])
    parent_bonds = _csv_rows(payloads[PARENT_BONDS])
    atoms_by_component: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    bonds_by_component: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in parent_atoms:
        if row["verified"] != "true":
            raise ValueError("parent_atom_authority_unverified")
        atom_id = row["ccd_atom_id"]
        if atom_id in atoms_by_component[row["ligand_comp_id"]]:
            raise ValueError("duplicate_parent_CCD_atom")
        atoms_by_component[row["ligand_comp_id"]][atom_id] = row
    for row in parent_bonds:
        if row["verified"] != "true":
            raise ValueError("parent_bond_authority_unverified")
        if row["normalized_bond_order"] not in NORMALIZED_BOND_ORDERS:
            raise ValueError("normalized_bond_order_invalid")
        bonds_by_component[row["ligand_comp_id"]].append(row)

    parent_expanded_atom_count = sum(
        len(atoms_by_component[sample["ligand_comp_id"]]) for sample in samples
    )
    if parent_expanded_atom_count != 324:
        raise ValueError("parent_expanded_atom_count_invalid")
    if len(observed) != 323:
        raise ValueError("atom_row_coverage_incomplete")

    observed_by_sample: dict[str, list[ObservedAtom]] = defaultdict(list)
    for atom in observed:
        observed_by_sample[atom.sample_index_row_id].append(atom)

    parent_lookup_by_sample: dict[str, dict[str, dict[str, str]]] = {}
    missing_records: list[tuple[str, str, str]] = []
    unexplained_missing: list[tuple[str, str, str]] = []
    for sample in samples:
        sample_id = sample["sample_index_row_id"]
        component = sample["ligand_comp_id"]
        parent_lookup = atoms_by_component[component]
        parent_lookup_by_sample[sample_id] = parent_lookup
        names = {atom.atom_name for atom in observed_by_sample[sample_id]}
        unexpected = names - set(parent_lookup)
        if unexpected:
            raise ValueError("unexpected_observed_atom")
        missing = sorted(set(parent_lookup) - names)
        evidence = evidence_by_id[sample_id]
        allowed = set(filter(None, evidence["leaving_group_atom_ids"].split(";")))
        for atom_id in missing:
            record = (sample_id, component, atom_id)
            missing_records.append(record)
            if (
                atom_id not in allowed
                or evidence["reaction_delta_class"]
                    != "covalent_leaving_group_loss"
                or evidence["parent_leaving_group_bond_verified"] != "True"
            ):
                unexplained_missing.append(record)
    if missing_records != [
        ("CYS_SG_SAMPLE_INDEX_000005", "ZYA", "F1")
    ]:
        raise ValueError("unexplained_parent_atom_missing")
    if unexplained_missing:
        raise ValueError("unexplained_parent_atom_missing")
    f1 = atoms_by_component["ZYA"].get("F1")
    if f1 is None:
        raise ValueError("parent_CCD_atom_missing")
    zya_evidence = evidence_by_id["CYS_SG_SAMPLE_INDEX_000005"]
    if (
        f1["ccd_type_symbol"] != "F"
        or zya_evidence["missing_parent_heavy_atom_ids"] != "F1"
        or zya_evidence["unexpected_observed_heavy_atom_ids"] != ""
        or zya_evidence["atom_inventory_reconciliation_status"]
            != "validated_post_covalent_leaving_group_loss"
        or zya_evidence["atom_inventory_reconciliation_passed"] != "True"
        or zya_evidence["parent_ccd_heavy_atom_count"] != "29"
        or zya_evidence["observed_post_covalent_heavy_atom_count"] != "28"
        or zya_evidence["heavy_atom_count_delta"] != "-1"
    ):
        raise ValueError("leaving_group_evidence_inconsistent")
    f1_bonds = [
        row for row in bonds_by_component["ZYA"]
        if "F1" in (row["parent_ccd_atom_id_1"], row["parent_ccd_atom_id_2"])
    ]
    if not f1_bonds:
        raise ValueError("leaving_group_parent_bond_missing")

    mapped_parent: dict[tuple[str, str], dict[str, str]] = {}
    for atom in observed:
        parent = parent_lookup_by_sample[atom.sample_index_row_id].get(atom.atom_name)
        if parent is None:
            raise ValueError("parent_CCD_atom_missing")
        if parent["ccd_atom_id"] != atom.atom_name:
            raise ValueError("atom_name_exact_match_failed")
        if parent["ccd_type_symbol"] != atom.type_symbol:
            raise ValueError("observed_parent_element_mismatch")
        mapped_parent[(atom.sample_index_row_id, atom.atom_name)] = parent

    provisional_bonds: list[dict[str, Any]] = []
    graph_edges_by_sample: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    parent_expanded_bond_count = 0
    verified_leaving_group_bond_count = 0
    for sample in samples:
        sample_id = sample["sample_index_row_id"]
        component = sample["ligand_comp_id"]
        atom_by_name = {
            atom.atom_name: atom for atom in observed_by_sample[sample_id]
        }
        evidence = evidence_by_id[sample_id]
        allowed_missing = set(
            filter(None, evidence["leaving_group_atom_ids"].split(";"))
        )
        seen_edges: set[tuple[str, str]] = set()
        for parent_bond in bonds_by_component[component]:
            parent_expanded_bond_count += 1
            left = parent_bond["parent_ccd_atom_id_1"]
            right = parent_bond["parent_ccd_atom_id_2"]
            edge = (min(left, right), max(left, right))
            if left == right:
                raise ValueError("projected_bond_self_loop")
            if edge in seen_edges:
                raise ValueError("duplicate_projected_bond")
            seen_edges.add(edge)
            left_atom = atom_by_name.get(left)
            right_atom = atom_by_name.get(right)
            if left_atom is not None and right_atom is not None:
                projected = True
                disposition = "retained_observed_bond"
                graph_edge = (*edge, parent_bond["normalized_bond_order"])
                if graph_edge in graph_edges_by_sample[sample_id]:
                    raise ValueError("duplicate_projected_bond")
                graph_edges_by_sample[sample_id].add(graph_edge)
            else:
                missing_endpoints = {
                    endpoint for endpoint, value in (
                        (left, left_atom), (right, right_atom)
                    ) if value is None
                }
                if (
                    missing_endpoints
                    and missing_endpoints <= allowed_missing
                    and evidence["reaction_delta_class"]
                        == "covalent_leaving_group_loss"
                    and evidence["parent_leaving_group_bond_verified"] == "True"
                ):
                    projected = False
                    disposition = "verified_leaving_group_endpoint_missing"
                    verified_leaving_group_bond_count += 1
                else:
                    raise ValueError("projected_bond_endpoint_missing")
            provisional_bonds.append({
                "sample_index_row_id": sample_id,
                "pdb_id": sample["pdb_id"],
                "ligand_comp_id": component,
                "parent_ccd_atom_id_1": left,
                "parent_ccd_atom_id_2": right,
                "normalized_bond_order": parent_bond["normalized_bond_order"],
                "retained_heavy_local_index_1":
                    "" if left_atom is None
                    else left_atom.retained_heavy_local_index_0based,
                "retained_heavy_local_index_1_valid": left_atom is not None,
                "retained_heavy_local_index_2":
                    "" if right_atom is None
                    else right_atom.retained_heavy_local_index_0based,
                "retained_heavy_local_index_2_valid": right_atom is not None,
                "projected_to_observed_graph": projected,
                "projection_disposition": disposition,
                "component_parent_graph_sha256":
                    sample["component_parent_graph_sha256"],
                "observed_graph_sha256": "",
                "verified": True,
            })
    if parent_expanded_bond_count != 337:
        raise ValueError("parent_expanded_bond_count_invalid")
    if verified_leaving_group_bond_count != 1:
        raise ValueError("leaving_group_evidence_inconsistent")

    sample_graph_sha: dict[str, str] = {}
    projected_bond_count = 0
    for sample in samples:
        sample_id = sample["sample_index_row_id"]
        atom_subset = observed_by_sample[sample_id]
        atom_payload = [
            (
                atom.atom_name,
                atom.type_symbol,
                int(mapped_parent[(sample_id, atom.atom_name)]["ccd_formal_charge"]),
            )
            for atom in atom_subset
        ]
        edge_payload = list(graph_edges_by_sample[sample_id])
        vertices = {atom.atom_name for atom in atom_subset}
        undirected = {(left, right) for left, right, _order in edge_payload}
        if any(left == right for left, right in undirected):
            raise ValueError("projected_bond_self_loop")
        if len(undirected) != len(edge_payload):
            raise ValueError("duplicate_projected_bond")
        if not _connected(vertices, undirected):
            raise ValueError("observed_graph_disconnected")
        sha = canonical_observed_graph_sha256(atom_payload, edge_payload)
        if (
            sha != canonical_observed_graph_sha256(
                tuple(reversed(atom_payload)), edge_payload
            )
            or sha != canonical_observed_graph_sha256(
                atom_payload, tuple(reversed(edge_payload))
            )
        ):
            raise ValueError("observed_graph_SHA_nondeterministic")
        sample_graph_sha[sample_id] = sha
        projected_bond_count += len(edge_payload)
    if projected_bond_count != 336:
        raise ValueError("projected_bond_count_invalid")

    mapping_rows: list[Mapping[str, Any]] = []
    for atom in sorted(
        observed,
        key=lambda item: (
            item.sample_index_row_id,
            item.retained_heavy_local_index_0based,
        ),
    ):
        parent = mapped_parent[(atom.sample_index_row_id, atom.atom_name)]
        mapping_rows.append({
            "sample_index_row_id": atom.sample_index_row_id,
            "pdb_id": atom.pdb_id,
            "ligand_comp_id": atom.ligand_comp_id,
            "observed_atom_name": atom.atom_name,
            "observed_type_symbol": atom.type_symbol,
            "source_full_atom_row_index": atom.source_full_atom_row_index,
            "retained_heavy_local_index_0based":
                atom.retained_heavy_local_index_0based,
            "parent_ccd_atom_id": parent["ccd_atom_id"],
            "parent_ccd_type_symbol": parent["ccd_type_symbol"],
            "parent_ccd_formal_charge": parent["ccd_formal_charge"],
            "parent_ccd_heavy_atom_row_index_0based":
                parent["ccd_heavy_atom_row_index_0based"],
            "atom_name_exact_match": True,
            "element_exact_match": True,
            "reactive_ligand_atom": atom.reactive_ligand_atom,
            "component_parent_graph_sha256":
                parent["component_parent_graph_sha256"],
            "observed_graph_sha256": sample_graph_sha[atom.sample_index_row_id],
            "mapping_authority_source_path": atom.source_path.as_posix(),
            "mapping_authority_source_sha256": atom.source_sha256,
            "authority_class": AUTHORITY_CLASS,
            "verified": True,
        })

    bond_rows = tuple({
        **row,
        "observed_graph_sha256":
            sample_graph_sha[str(row["sample_index_row_id"])],
    } for row in provisional_bonds)
    readiness_rows: list[Mapping[str, Any]] = []
    for sample in samples:
        sample_id = sample["sample_index_row_id"]
        atom_count = len(observed_by_sample[sample_id])
        sample_projected_bonds = sum(
            row["sample_index_row_id"] == sample_id
            and bool(row["projected_to_observed_graph"])
            for row in provisional_bonds
        )
        readiness_rows.append({
            "sample_index_row_id": sample_id,
            "pdb_id": sample["pdb_id"],
            "ligand_comp_id": sample["ligand_comp_id"],
            "parent_component_graph_authority_available": True,
            "observed_atom_projection_exact": True,
            "observed_projected_graph_available": True,
            "parent_graph_valid": True,
            "observed_graph_valid": True,
            "pre_reaction_connectivity_available": True,
            "pre_reaction_bond_order_available": True,
            "observed_atom_count": atom_count,
            "projected_bond_count": sample_projected_bonds,
            "observed_graph_sha256": sample_graph_sha[sample_id],
            "reactive_ligand_atom_available": True,
            "retained_local_index_contiguous": True,
            "reaction_family_label_available": False,
            "approved_warhead_rule_available": False,
            "role_proposal_available": False,
            "minimal_seed_proposal_available": False,
            "human_gold_review_completed": False,
            "ready_for_mask_materialization": False,
            "ready_for_tensorization": False,
            "ready_for_model_integration": False,
            "ready_for_training": False,
            "planned_covalent_model_module_count": 5,
            "integrated_covalent_model_module_count": 0,
            "blocking_reasons": (
                "reaction_family_labels_missing;"
                "approved_warhead_rules_missing;"
                "role_proposals_missing;minimal_seed_proposals_missing;"
                "current11_human_gold_review_missing"
            ),
            "verified": True,
        })

    return ProjectionResult(
        source_rows=source_rows,
        mapping_rows=tuple(mapping_rows),
        bond_rows=bond_rows,
        readiness_rows=tuple(readiness_rows),
        failure_rows=build_failure_rows(),
        sample_graph_sha256=dict(sorted(sample_graph_sha.items())),
        parent_expanded_atom_count=parent_expanded_atom_count,
        parent_expanded_bond_count=parent_expanded_bond_count,
        projected_bond_count=projected_bond_count,
        verified_leaving_group_bond_count=verified_leaving_group_bond_count,
        missing_parent_atom_count=len(missing_records),
        unexplained_missing_parent_atom_count=len(unexplained_missing),
        transaction_succeeded=True,
        transaction_blocking_reasons=(),
    )


def build_projection_result(repo_root: Path) -> ProjectionResult:
    payloads = load_frozen_sources(repo_root)
    samples, observed, evidence_by_id, source_rows = _phase_a(payloads)
    return _phase_b(
        payloads, samples, observed, evidence_by_id, source_rows
    )


def transaction_tables(
    phase_a_passed: bool,
    phase_b_passed: bool,
    mapping_rows: Sequence[Mapping[str, Any]],
    bond_rows: Sequence[Mapping[str, Any]],
) -> tuple[tuple[Mapping[str, Any], ...], tuple[Mapping[str, Any], ...]]:
    """Expose the all-or-none table transaction for direct negative testing."""

    if not phase_a_passed or not phase_b_passed:
        return (), ()
    return tuple(mapping_rows), tuple(bond_rows)


def _blocked_readiness(
    repo_root: Path, reason: str
) -> tuple[Mapping[str, Any], ...]:
    try:
        samples = _csv_rows(base_bytes(repo_root, PARENT_READINESS))
    except Exception:
        samples = []
    rows: list[Mapping[str, Any]] = []
    for sample in samples:
        rows.append({
            "sample_index_row_id": sample.get("sample_index_row_id", ""),
            "pdb_id": sample.get("pdb_id", ""),
            "ligand_comp_id": sample.get("ligand_comp_id", ""),
            "parent_component_graph_authority_available": False,
            "observed_atom_projection_exact": False,
            "observed_projected_graph_available": False,
            "parent_graph_valid": False,
            "observed_graph_valid": False,
            "pre_reaction_connectivity_available": False,
            "pre_reaction_bond_order_available": False,
            "observed_atom_count": 0,
            "projected_bond_count": 0,
            "observed_graph_sha256": "",
            "reactive_ligand_atom_available": False,
            "retained_local_index_contiguous": False,
            "reaction_family_label_available": False,
            "approved_warhead_rule_available": False,
            "role_proposal_available": False,
            "minimal_seed_proposal_available": False,
            "human_gold_review_completed": False,
            "ready_for_mask_materialization": False,
            "ready_for_tensorization": False,
            "ready_for_model_integration": False,
            "ready_for_training": False,
            "planned_covalent_model_module_count": 5,
            "integrated_covalent_model_module_count": 0,
            "blocking_reasons": reason,
            "verified": False,
        })
    return tuple(rows)


def build_evidence_payloads(repo_root: Path) -> dict[str, bytes]:
    """Build all six deterministic data artifacts without partial authority."""

    try:
        result = build_projection_result(repo_root)
    except Exception as exc:
        reason = str(exc) or type(exc).__name__
        try:
            payloads = load_frozen_sources(repo_root)
            source_rows = _source_inventory(payloads, {})
        except Exception:
            source_rows = ()
        mapping_rows, bond_rows = transaction_tables(False, False, (), ())
        readiness_rows = _blocked_readiness(repo_root, reason)
        failure_rows = build_failure_rows()
        result = ProjectionResult(
            source_rows=source_rows,
            mapping_rows=mapping_rows,
            bond_rows=bond_rows,
            readiness_rows=readiness_rows,
            failure_rows=failure_rows,
            sample_graph_sha256={},
            parent_expanded_atom_count=0,
            parent_expanded_bond_count=0,
            projected_bond_count=0,
            verified_leaving_group_bond_count=0,
            missing_parent_atom_count=0,
            unexplained_missing_parent_atom_count=0,
            transaction_succeeded=False,
            transaction_blocking_reasons=(reason,),
        )

    mapping_rows, bond_rows = transaction_tables(
        result.transaction_succeeded,
        result.transaction_succeeded,
        result.mapping_rows,
        result.bond_rows,
    )
    payloads = {
        SOURCE_INVENTORY_FILE: _csv_bytes(SOURCE_COLUMNS, result.source_rows),
        MAPPING_FILE: _csv_bytes(MAPPING_COLUMNS, mapping_rows),
        BOND_FILE: _csv_bytes(BOND_COLUMNS, bond_rows),
        READINESS_FILE: _csv_bytes(READINESS_COLUMNS, result.readiness_rows),
        FAILURE_FILE: _csv_bytes(FAILURE_COLUMNS, result.failure_rows),
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "formal_base_commit": BASE_COMMIT,
        "formal_base_parent": BASE_PARENT,
        "formal_base_tree": BASE_TREE,
        "formal_base_subject": BASE_SUBJECT,
        "formal_future_commit_subject": FORMAL_COMMIT_SUBJECT,
        "authority_class": AUTHORITY_CLASS,
        "transaction_succeeded": result.transaction_succeeded,
        "transaction_blocking_reasons":
            list(result.transaction_blocking_reasons),
        "phase_a_source_validation_passed": result.transaction_succeeded,
        "phase_b_projection_validation_passed": result.transaction_succeeded,
        "candidate_source_count": len(result.source_rows),
        "candidate_source_sha256": {
            path.as_posix(): sha
            for path, sha in FROZEN_BASE_SHA256.items()
        },
        "formal_observed_row_authority": {
            "retained_index_authority_path": HEAVY_PROJECTION.as_posix(),
            "retained_index_authority_sha256":
                FROZEN_BASE_SHA256[HEAVY_PROJECTION],
            "observed_atom_name_table_paths": [
                path.as_posix() for path in LIGAND_ATOM_TABLES
            ],
            "observed_atom_name_table_sha256": {
                path.as_posix(): FROZEN_BASE_SHA256[path]
                for path in LIGAND_ATOM_TABLES
            },
            "join_contract": (
                "exact sample identity + BASE source path/SHA + "
                "source_atom_row_index_0based"
            ),
        },
        "current11_sample_count": len(result.readiness_rows),
        "unique_component_count": 9 if result.transaction_succeeded else 0,
        "parent_sample_expanded_heavy_atom_count":
            result.parent_expanded_atom_count,
        "observed_retained_heavy_atom_count": len(mapping_rows),
        "exact_mapping_count": len(mapping_rows),
        "element_exact_match_count": sum(
            bool(row["element_exact_match"]) for row in mapping_rows
        ),
        "reactive_ligand_atom_count": sum(
            bool(row["reactive_ligand_atom"]) for row in mapping_rows
        ),
        "missing_parent_atom_count": result.missing_parent_atom_count,
        "verified_missing_parent_atom": (
            {
                "sample_index_row_id": "CYS_SG_SAMPLE_INDEX_000005",
                "ligand_comp_id": "ZYA",
                "parent_ccd_atom_id": "F1",
                "reaction_delta_class": "covalent_leaving_group_loss",
            } if result.transaction_succeeded else {}
        ),
        "unexplained_missing_parent_atom_count":
            result.unexplained_missing_parent_atom_count,
        "parent_sample_expanded_bond_count":
            result.parent_expanded_bond_count,
        "projected_observed_bond_count": result.projected_bond_count,
        "verified_leaving_group_endpoint_missing_bond_count":
            result.verified_leaving_group_bond_count,
        "observed_graph_sha256_by_sample": result.sample_graph_sha256,
        "observed_atom_projection_exact_count": (
            11 if result.transaction_succeeded else 0
        ),
        "observed_projected_graph_available_count": (
            11 if result.transaction_succeeded else 0
        ),
        "parent_graph_valid_count": 11 if result.transaction_succeeded else 0,
        "observed_graph_valid_count": 11 if result.transaction_succeeded else 0,
        "pre_reaction_connectivity_available_count": (
            11 if result.transaction_succeeded else 0
        ),
        "pre_reaction_bond_order_available_count": (
            11 if result.transaction_succeeded else 0
        ),
        "reaction_family_label_available_count": 0,
        "approved_warhead_rule_available_count": 0,
        "role_proposal_available_count": 0,
        "minimal_seed_proposal_available_count": 0,
        "human_gold_review_completed_count": 0,
        "ready_for_mask_materialization": False,
        "ready_for_tensorization": False,
        "ready_for_model_integration": False,
        "ready_for_training": False,
        "planned_covalent_model_module_count": 5,
        "integrated_covalent_model_module_count": 0,
        "failure_mutation_count": len(result.failure_rows),
        "failure_mutations_all_fail_closed": all(
            bool(row["fails_closed"]) for row in result.failure_rows
        ),
        "output_sha256": {
            name: _sha256(payload) for name, payload in payloads.items()
        },
        "recommended_next_step": (
            "design_covapie_cys_sg_reaction_family_and_warhead_rule_registry_v1"
            if result.transaction_succeeded
            else "resolve_covapie_current11_observed_atom_row_authority_blockers_v1"
        ),
    }
    payloads[MANIFEST_FILE] = (
        json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    )
    return payloads


def materialize(repo_root: Path) -> dict[str, bytes]:
    payloads = build_evidence_payloads(repo_root)
    output_root = repo_root / OUTPUT_ROOT
    output_root.mkdir(parents=True, exist_ok=True)
    for name in OUTPUT_FILES:
        (output_root / name).write_bytes(payloads[name])
    return payloads


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    payloads = materialize(repo_root)
    manifest = json.loads(payloads[MANIFEST_FILE])
    if not manifest["transaction_succeeded"]:
        return 1
    print(
        "current11_observed_projection_verified "
        f"mapping={manifest['exact_mapping_count']} "
        f"projected_bonds={manifest['projected_observed_bond_count']} "
        f"graphs={manifest['observed_graph_valid_count']}/11 "
        "training_ready=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
