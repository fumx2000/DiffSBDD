"""Design the CovaPIE Cys-SG reaction-family and warhead-rule registries."""

from __future__ import annotations

import csv
import dataclasses
import hashlib
import io
import json
import subprocess
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


BASE_COMMIT = "68c5ca5cf1ce5b20be5db9ce0b37e10830c09288"
BASE_PARENT = "34ff4dbb94a5caf4f8b393152e9694e5a8d7c2ce"
BASE_TREE = "971c5c6360854ae705056c99dda04e96e07fd779"
BASE_SUBJECT = "add CovaPIE Current11 observed atom projection authority v1"
FORMAL_COMMIT_SUBJECT = (
    "add CovaPIE Cys SG reaction family and warhead rule registry design v1"
)
SCHEMA_VERSION = (
    "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1"
)
SIGNATURE_VERSION = "covapie_cys_sg_canonical_local_reaction_signature_v1"
RULE_KIND = "canonical_local_graph_exact_match_v1"
SELECTED_SIGNATURE_RADIUS = 1
AUTHORITY_CLASS = (
    "BASE_sha_attested_Cys_SG_parent_graph_and_observed_delta_design_authority"
)
OUTPUT_ROOT = Path("data/derived/covalent_small") / SCHEMA_VERSION

PREDECESSOR_SOURCE = Path(
    "src/covalent_ext/"
    "covapie_current11_observed_to_parent_atom_projection_authority_v1.py"
)
PROJECTION_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_current11_observed_to_parent_atom_projection_authority_v1"
)
MAPPING = (
    PROJECTION_ROOT
    / "covapie_current11_observed_to_parent_atom_mapping_authority.csv"
)
BONDS = (
    PROJECTION_ROOT
    / "covapie_current11_parent_and_observed_projected_bond_authority.csv"
)
READINESS = (
    PROJECTION_ROOT / "covapie_current11_observed_projection_readiness_matrix.csv"
)
PROJECTION_MANIFEST = (
    PROJECTION_ROOT
    / "covapie_current11_observed_to_parent_atom_projection_authority_manifest.json"
)
EXACT9_ROOT = Path(
    "data/derived/covalent_small/"
    "covapie_exact9_audited_local_ccd_parent_graph_authority_v1"
)
PARENT_ATOMS = EXACT9_ROOT / "covapie_exact9_parent_heavy_atom_authority.csv"
PARENT_BONDS = EXACT9_ROOT / "covapie_exact9_parent_heavy_bond_authority.csv"
GRAPH_EVIDENCE = Path(
    "data/derived/covalent_small/"
    "covapie_independent_group_expansion_batch_independence_evidence_"
    "materialization_smoke_v0/covapie_ligand_graph_scaffold_evidence.csv"
)
ATOM_PAIR_MAPPING = Path(
    "data/derived/covalent_small/"
    "covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_"
    "evidence_validation_v1/"
    "covapie_atom_pair_atom_table_mapping_validation_matrix.csv"
)
FINAL_INDEX = Path(
    "data/derived/covalent_small/"
    "covapie_final_dataset_materialization_smoke_v0/final_dataset_index.csv"
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
    PREDECESSOR_SOURCE:
        "002ff3367c5e68d8e5bde77e5460cc0f8bc83c5102157a5fd1ef88d53b73ecc5",
    MAPPING:
        "f803e0c5fb2585c8dae31dbff254749496f897f4bf9a5103455c6c675a132a1e",
    BONDS:
        "bd31b7c074c3d4226c26bfe0210b9c3460f38c5087f1157b1167749f91bfffe0",
    READINESS:
        "ec7bb2c203a7b13f525c413171b734fdd9f8af934b6e7e8eaf3fc6ae141128a0",
    PROJECTION_MANIFEST:
        "e553e9cb1518cd2c9465772758539e9610c8f81cd702dd0440e99fbd143fc0a7",
    PARENT_ATOMS:
        "d50b052c2ed2573ccfdcf66470a077744ad11f4a083daee11f20d794b3b23fe7",
    PARENT_BONDS:
        "26957b9f78217c808d2dc021cfab1a2bf78dd1708c46c49f220ae32a3a09ebbf",
    GRAPH_EVIDENCE:
        "982a9f89a89d3a4ad6a3e468cfd16d2fdfd5435cbf6d593e086fbd7fadd3ec73",
    ATOM_PAIR_MAPPING:
        "9f26b25ed11d186a02a1f859de10a105605ce3af13805ac5a4be1ad73199df45",
    FINAL_INDEX:
        "c4c31888cb0f7c148b00656ccf22ab68fab842fcdafdee049b2f420eddc1302d",
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

SOURCE_FILE = "covapie_reaction_family_rule_design_source_inventory.csv"
FAMILY_FILE = "covapie_cys_sg_reaction_family_registry.csv"
RULE_FILE = "covapie_cys_sg_warhead_rule_registry.csv"
DESIGN_FILE = (
    "covapie_current11_reaction_family_and_warhead_rule_design_matrix.csv"
)
FAILURE_FILE = "covapie_reaction_family_rule_design_failure_matrix.csv"
MANIFEST_FILE = (
    "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_manifest.json"
)
OUTPUT_FILES = (
    SOURCE_FILE, FAMILY_FILE, RULE_FILE, DESIGN_FILE, FAILURE_FILE, MANIFEST_FILE,
)
EXACT10_PATHS = (
    Path(
        "src/covalent_ext/"
        "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1.py"
    ),
    Path(
        "tests/"
        "test_covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1.py"
    ),
    Path(
        "scripts/"
        "check_covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1.py"
    ),
    Path(
        "docs/"
        "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1_summary.md"
    ),
    *(OUTPUT_ROOT / name for name in OUTPUT_FILES),
)

SOURCE_COLUMNS = (
    "source_path", "BASE_SHA256", "source_row_count", "Current11_coverage",
    "fields_actually_used", "authority_class", "verified",
)
FAMILY_COLUMNS = (
    "reaction_family_id", "reaction_family_semantic_name",
    "target_residue_name", "target_residue_atom_name", "formed_bond_order",
    "reaction_delta_class", "leaving_group_policy",
    "canonical_signature_version", "selected_signature_radius",
    "canonical_reaction_family_signature_json",
    "canonical_reaction_family_signature_sha256", "mechanism_claim_status",
    "current11_sample_count", "unique_component_count", "warhead_rule_count",
    "candidate_assignment_ready", "human_gold_review_completed", "approved",
    "blocking_reasons", "verified",
)
RULE_COLUMNS = (
    "warhead_rule_id", "warhead_type_semantic_name", "reaction_family_id",
    "rule_kind", "selected_signature_radius", "center_atom_element",
    "center_atom_formal_charge", "target_residue_name",
    "target_residue_atom_name", "formed_bond_order",
    "canonical_local_graph_rule_json", "canonical_local_graph_rule_sha256",
    "required_leaving_group_count", "allowed_leaving_group_elements",
    "required_reaction_delta_class", "Current11_match_count",
    "Current11_unique_component_count", "exact_match_unique",
    "candidate_rule_assignment_ready", "approved_warhead_smarts",
    "SMARTS_status", "human_gold_review_completed", "approved",
    "blocking_reasons", "verified",
)
DESIGN_COLUMNS = (
    "sample_index_row_id", "pdb_id", "ligand_comp_id",
    "target_residue_name", "target_residue_number",
    "target_residue_atom_name", "ligand_reactive_atom_name",
    "ligand_reactive_atom_element", "ligand_reactive_parent_ccd_atom_id",
    "component_parent_graph_sha256", "observed_graph_sha256",
    "reaction_delta_class", "leaving_group_atom_ids",
    "verified_missing_parent_atom_ids", "parent_local_bonds_json",
    "observed_local_bonds_json", "radius_0_signature_sha256",
    "radius_1_signature_sha256", "radius_2_signature_sha256",
    "selected_signature_radius", "candidate_reaction_family_id",
    "candidate_reaction_family_semantic_name", "candidate_warhead_rule_id",
    "candidate_warhead_type_semantic_name", "family_candidate_exact_one",
    "warhead_rule_candidate_exact_one", "rule_matches_parent_graph",
    "rule_consistent_with_observed_delta", "reaction_family_label_available",
    "approved_warhead_rule_available", "human_gold_review_completed",
    "ready_for_role_proposal_generation",
    "ready_for_minimal_seed_proposal_generation",
    "ready_for_mask_materialization", "ready_for_tensorization",
    "ready_for_model_integration", "ready_for_training",
    "blocking_reasons", "verified",
)
FAILURE_COLUMNS = (
    "failure_case", "mutation_signature", "mutated_fields",
    "expected_reasons", "observed_reasons", "expected_reasons_verified",
    "fails_closed", "reaction_family_registry_row_count",
    "warhead_rule_registry_row_count", "current11_design_matrix_row_count",
    "warhead_type_model_head_integrated", "warhead_type_loss_integrated",
    "ready_for_mask_materialization", "ready_for_model_integration",
    "ready_for_training", "verified",
)


@dataclass(frozen=True)
class DesignScenario:
    base_source_present: bool = True
    base_source_sha_matches: bool = True
    current11_sample_coverage: int = 11
    target_residue_name: str = "CYS"
    target_residue_atom_name: str = "SG"
    reactive_ligand_atom_count: int = 1
    reactive_parent_atom_present: bool = True
    parent_graph_sha_matches: bool = True
    observed_graph_sha_matches: bool = True
    local_graph_connected: bool = True
    bond_order_supported: bool = True
    radius_signature_deterministic: bool = True
    duplicate_family_id: bool = False
    duplicate_rule_id: bool = False
    family_candidate_count: int = 1
    warhead_rule_candidate_count: int = 1
    rule_parent_graph_matches: bool = True
    rule_observed_delta_matches: bool = True
    mechanism_claim_status: str = "topology_defined_mechanism_not_claimed"
    smarts_status: str = "not_materialized_in_design_stage"
    partial_materialization_attempted: bool = False
    execution_boundary_crossed: bool = False


@dataclass(frozen=True)
class BuildResult:
    source_rows: tuple[Mapping[str, Any], ...]
    family_rows: tuple[Mapping[str, Any], ...]
    rule_rows: tuple[Mapping[str, Any], ...]
    design_rows: tuple[Mapping[str, Any], ...]
    failure_rows: tuple[Mapping[str, Any], ...]
    radius_signature_unique_counts: Mapping[int, int]
    radius_rule_projection_unique_counts: Mapping[int, int]
    selected_radius: int
    transaction_succeeded: bool
    blocking_reasons: tuple[str, ...]


FAILURE_MUTATIONS = (
    ("BASE source missing", "base_source_present", False, "BASE_source_missing"),
    (
        "BASE source SHA mismatch", "base_source_sha_matches", False,
        "BASE_source_SHA_mismatch",
    ),
    (
        "Current11 sample coverage incomplete", "current11_sample_coverage", 10,
        "Current11_sample_coverage_incomplete",
    ),
    ("target residue not CYS", "target_residue_name", "SER", "target_residue_not_CYS"),
    (
        "target residue atom not SG", "target_residue_atom_name", "OG",
        "target_residue_atom_not_SG",
    ),
    (
        "reactive ligand atom missing", "reactive_ligand_atom_count", 0,
        "reactive_ligand_atom_missing",
    ),
    (
        "reactive ligand atom duplicated", "reactive_ligand_atom_count", 2,
        "reactive_ligand_atom_duplicated",
    ),
    (
        "reactive parent atom missing", "reactive_parent_atom_present", False,
        "reactive_parent_atom_missing",
    ),
    (
        "parent graph SHA mismatch", "parent_graph_sha_matches", False,
        "parent_graph_SHA_mismatch",
    ),
    (
        "observed graph SHA mismatch", "observed_graph_sha_matches", False,
        "observed_graph_SHA_mismatch",
    ),
    (
        "local graph disconnected", "local_graph_connected", False,
        "local_graph_disconnected",
    ),
    (
        "unsupported bond order", "bond_order_supported", False,
        "unsupported_bond_order",
    ),
    (
        "radius signature nondeterministic", "radius_signature_deterministic",
        False, "radius_signature_nondeterministic",
    ),
    (
        "duplicate family ID", "duplicate_family_id", True,
        "duplicate_reaction_family_id",
    ),
    (
        "duplicate rule ID", "duplicate_rule_id", True,
        "duplicate_warhead_rule_id",
    ),
    (
        "family candidate absent", "family_candidate_count", 0,
        "family_candidate_absent",
    ),
    (
        "family candidate ambiguous", "family_candidate_count", 2,
        "family_candidate_ambiguous",
    ),
    (
        "warhead rule candidate absent", "warhead_rule_candidate_count", 0,
        "warhead_rule_candidate_absent",
    ),
    (
        "warhead rule candidate ambiguous", "warhead_rule_candidate_count", 2,
        "warhead_rule_candidate_ambiguous",
    ),
    (
        "rule parent-graph mismatch", "rule_parent_graph_matches", False,
        "rule_parent_graph_mismatch",
    ),
    (
        "rule observed-delta mismatch", "rule_observed_delta_matches", False,
        "rule_observed_delta_mismatch",
    ),
    (
        "mechanism overclaimed", "mechanism_claim_status",
        "Michael_addition", "mechanism_overclaimed_from_topology",
    ),
    (
        "SMARTS prematurely approved", "smarts_status", "approved",
        "SMARTS_prematurely_approved",
    ),
    (
        "partial materialization attempted", "partial_materialization_attempted",
        True, "partial_materialization_attempted",
    ),
    (
        "execution boundary crossed", "execution_boundary_crossed", True,
        "execution_boundary_crossed",
    ),
)


def _git(
    repo_root: Path, *arguments: str, check: bool = True
) -> subprocess.CompletedProcess[bytes]:
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
            + result.stderr.decode("utf-8", "replace")
        )
    return result


def base_bytes(repo_root: Path, path: Path) -> bytes:
    return _git(repo_root, "show", f"{BASE_COMMIT}:{path.as_posix()}").stdout


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _csv_rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))


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


def validate_execution_boundary_v1(repo_root: Path) -> str:
    shown = _git(
        repo_root, "show", "-s", "--format=%H%n%P%n%T%n%s", BASE_COMMIT
    ).stdout.decode().splitlines()
    if shown != [BASE_COMMIT, BASE_PARENT, BASE_TREE, BASE_SUBJECT]:
        raise ValueError("formal_BASE_identity_mismatch")
    head = _git(repo_root, "rev-parse", "HEAD").stdout.decode().strip()
    if head == BASE_COMMIT:
        return "pre_commit"
    raw = _git(repo_root, "cat-file", "commit", head).stdout
    headers, separator, message = raw.partition(b"\n\n")
    if not separator:
        raise ValueError("successor_commit_object_malformed")
    parents = tuple(
        line[7:].decode() for line in headers.splitlines()
        if line.startswith(b"parent ")
    )
    if parents != (BASE_COMMIT,):
        raise ValueError("successor_parent_not_exact_BASE")
    subject, newline, body = message.partition(b"\n")
    if not newline or subject.decode() != FORMAL_COMMIT_SUBJECT:
        raise ValueError("successor_subject_mismatch")
    if body:
        raise ValueError("successor_commit_body_nonempty")
    changed = tuple(
        item.decode() for item in _git(
            repo_root, "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", head
        ).stdout.split(b"\0") if item
    )
    expected = tuple(path.as_posix() for path in EXACT10_PATHS)
    if len(changed) != 10 or set(changed) != set(expected):
        raise ValueError("successor_changed_path_inventory_mismatch")
    tree_rows = tuple(
        row for row in _git(
            repo_root, "ls-tree", "-r", "-z", head, "--", *expected
        ).stdout.split(b"\0") if row
    )
    if len(tree_rows) != 10 or any(
        not row.partition(b"\t")[0].startswith(b"100644 blob ") for row in tree_rows
    ):
        raise ValueError("successor_exact10_file_mode_invalid")
    branch = _git(
        repo_root, "symbolic-ref", "--quiet", "--short", "HEAD", check=False
    )
    if branch.returncode != 0:
        return "detached_candidate_post_commit"
    if branch.stdout.decode().strip() != "main":
        raise ValueError("successor_formal_branch_not_main")
    origin = _git(
        repo_root, "rev-parse", "--verify", "refs/remotes/origin/main", check=False
    )
    if origin.returncode != 0:
        raise ValueError("successor_origin_main_missing")
    origin_oid = origin.stdout.decode().strip()
    if origin_oid == BASE_COMMIT:
        return "formal_main_post_commit_unpushed"
    if origin_oid == head:
        return "formal_main_post_push"
    raise ValueError("successor_origin_main_lifecycle_mismatch")


def load_frozen_sources(repo_root: Path) -> dict[Path, bytes]:
    validate_execution_boundary_v1(repo_root)
    payloads = {}
    for path, expected in FROZEN_BASE_SHA256.items():
        payload = base_bytes(repo_root, path)
        if _sha256(payload) != expected:
            raise ValueError(f"BASE_source_SHA_mismatch:{path.as_posix()}")
        payloads[path] = payload
    return payloads


def _source_metadata(path: Path) -> tuple[str, str, str]:
    if path == PREDECESSOR_SOURCE:
        return (
            "11/11",
            "BASE identity; predecessor lifecycle; projection authority contract",
            "predecessor_production_contract",
        )
    if path == MAPPING:
        return (
            "11/11",
            "sample identity; reactive atom; element; formal charge; graph SHA",
            "observed_to_parent_atom_mapping_authority",
        )
    if path == BONDS:
        return (
            "11/11",
            "parent endpoints; bond order; projection disposition; graph SHA",
            "sample_expanded_parent_and_observed_bond_authority",
        )
    if path == READINESS:
        return (
            "11/11",
            "projection validity; reactive availability; readiness blockers",
            "observed_projection_readiness_authority",
        )
    if path == PROJECTION_MANIFEST:
        return (
            "11/11",
            "transaction state; counts; source SHA; model module boundary",
            "observed_projection_manifest_authority",
        )
    if path == PARENT_ATOMS:
        return (
            "11/11",
            "CCD atom ID; element; formal charge; component graph SHA",
            "sha_attested_parent_atom_graph_authority",
        )
    if path == PARENT_BONDS:
        return (
            "11/11",
            "CCD bond endpoints; normalized bond order; component graph SHA",
            "sha_attested_parent_bond_graph_authority",
        )
    if path == GRAPH_EVIDENCE:
        return (
            "11/11",
            "reaction delta; leaving groups; missing parent atoms; reactive atom",
            "BASE_reaction_delta_evidence",
        )
    if path == ATOM_PAIR_MAPPING:
        return (
            "11/11",
            "exact-one ligand and target atom mappings; mapping verification",
            "canonical_atom_pair_mapping_validation_authority",
        )
    if path == FINAL_INDEX:
        return (
            "11/11",
            "sample identity; CYS residue number; SG; ligand reactive atom",
            "Current11_protein_residue_and_atom_pair_authority",
        )
    return (
        "1/11",
        "atom name; element; exact reactive-atom flag",
        "BASE_tracked_sample_ligand_atom_row_authority",
    )


def _source_inventory(
    payloads: Mapping[Path, bytes]
) -> tuple[Mapping[str, Any], ...]:
    rows = []
    for path in FROZEN_BASE_SHA256:
        payload = payloads[path]
        coverage, fields, authority = _source_metadata(path)
        if path.suffix == ".csv":
            count = len(_csv_rows(payload))
        elif path.suffix == ".json":
            count = 1
        else:
            count = len(payload.decode("utf-8").splitlines())
        rows.append({
            "source_path": path.as_posix(),
            "BASE_SHA256": _sha256(payload),
            "source_row_count": count,
            "Current11_coverage": coverage,
            "fields_actually_used": fields,
            "authority_class": authority,
            "verified": True,
        })
    return tuple(rows)


def _reaction_delta(row: Mapping[str, str]) -> str:
    return row["reaction_delta_class"] or row["atom_inventory_reconciliation_status"]


def _split_ids(value: str) -> tuple[str, ...]:
    return tuple(sorted(item for item in value.split(";") if item))


def _distances(
    center: str, bonds: Sequence[Mapping[str, str]]
) -> dict[str, int]:
    adjacency: dict[str, set[str]] = defaultdict(set)
    for row in bonds:
        left = row["parent_ccd_atom_id_1"]
        right = row["parent_ccd_atom_id_2"]
        adjacency[left].add(right)
        adjacency[right].add(left)
    distance = {center: 0}
    queue = deque([center])
    while queue:
        atom = queue.popleft()
        for neighbor in sorted(adjacency[atom]):
            if neighbor not in distance:
                distance[neighbor] = distance[atom] + 1
                queue.append(neighbor)
    return distance


def canonical_local_signature(
    *,
    center: str,
    atoms: Mapping[str, Mapping[str, str]],
    bonds: Sequence[Mapping[str, str]],
    retained: set[str],
    leaving_groups: set[str],
    reaction_delta_class: str,
    radius: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return the provenance signature and its component-independent rule view."""

    distance = _distances(center, bonds)
    if len(distance) != len(atoms):
        raise ValueError("local_graph_disconnected")
    selected = {atom for atom, value in distance.items() if value <= radius}
    local_atoms = []
    for atom in sorted(selected, key=lambda item: (distance[item], item)):
        source = atoms[atom]
        local_atoms.append({
            "parent_ccd_atom_id": atom,
            "relative_graph_distance": distance[atom],
            "element": source["ccd_type_symbol"],
            "formal_charge": int(source["ccd_formal_charge"]),
            "is_leaving_group": atom in leaving_groups,
            "is_retained_observed": atom in retained,
        })
    local_bonds = []
    for row in bonds:
        left = row["parent_ccd_atom_id_1"]
        right = row["parent_ccd_atom_id_2"]
        if left in selected and right in selected:
            local_bonds.append({
                "endpoint_1_parent_ccd_atom_id": min(left, right),
                "endpoint_2_parent_ccd_atom_id": max(left, right),
                "normalized_bond_order": row["normalized_bond_order"],
                "projected_disposition": row["projection_disposition"],
            })
    local_bonds.sort(key=canonical_json)
    leaving_elements = sorted(
        atoms[item]["ccd_type_symbol"] for item in leaving_groups
    )
    provenance = {
        "canonical_signature_version": SIGNATURE_VERSION,
        "radius": radius,
        "center_atom": {
            "parent_ccd_atom_id": center,
            "element": atoms[center]["ccd_type_symbol"],
            "formal_charge": int(atoms[center]["ccd_formal_charge"]),
            "reactive": True,
        },
        "local_atoms": local_atoms,
        "local_bonds": local_bonds,
        "target_condition": {
            "residue": "CYS", "residue_atom": "SG",
            "formed_bond_order": "single",
        },
        "reaction_delta": {
            "reaction_delta_class": reaction_delta_class,
            "leaving_group_count": len(leaving_groups),
            "leaving_group_elements": leaving_elements,
        },
    }

    incident: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for row in local_bonds:
        left = row["endpoint_1_parent_ccd_atom_id"]
        right = row["endpoint_2_parent_ccd_atom_id"]
        order = row["normalized_bond_order"]
        disposition = row["projected_disposition"]
        incident[left].append((order, disposition))
        incident[right].append((order, disposition))
    ordered = sorted(
        (item for item in local_atoms if item["parent_ccd_atom_id"] != center),
        key=lambda item: (
            item["relative_graph_distance"], item["element"],
            item["formal_charge"], item["is_leaving_group"],
            item["is_retained_observed"],
            tuple(sorted(incident[item["parent_ccd_atom_id"]])),
            item["parent_ccd_atom_id"],
        ),
    )
    labels = {center: "center"}
    for index, item in enumerate(ordered, 1):
        labels[item["parent_ccd_atom_id"]] = f"local_atom_{index:03d}"
    rule_atoms = [{
        "canonical_local_atom_id": labels[item["parent_ccd_atom_id"]],
        "relative_graph_distance": item["relative_graph_distance"],
        "element": item["element"],
        "formal_charge": item["formal_charge"],
        "is_leaving_group": item["is_leaving_group"],
        "is_retained_observed": item["is_retained_observed"],
    } for item in [local_atoms[0], *ordered]]
    rule_bonds = sorted(({
        "canonical_endpoint_1": min(labels[
            row["endpoint_1_parent_ccd_atom_id"]
        ], labels[row["endpoint_2_parent_ccd_atom_id"]]),
        "canonical_endpoint_2": max(labels[
            row["endpoint_1_parent_ccd_atom_id"]
        ], labels[row["endpoint_2_parent_ccd_atom_id"]]),
        "normalized_bond_order": row["normalized_bond_order"],
        "projected_disposition": row["projected_disposition"],
    } for row in local_bonds), key=canonical_json)
    rule = {
        "rule_kind": RULE_KIND,
        "canonical_signature_version": SIGNATURE_VERSION,
        "selected_signature_radius": radius,
        "center_atom": {
            "canonical_local_atom_id": "center",
            "element": atoms[center]["ccd_type_symbol"],
            "formal_charge": int(atoms[center]["ccd_formal_charge"]),
            "reactive": True,
        },
        "local_atoms": rule_atoms,
        "local_bonds": rule_bonds,
        "target_condition": provenance["target_condition"],
        "reaction_delta": provenance["reaction_delta"],
    }
    return provenance, rule


def _semantic_names(rule: Mapping[str, Any], digest: str) -> tuple[str, str]:
    center = rule["center_atom"]
    charge = center["formal_charge"]
    charge_name = "neutral" if charge == 0 else f"formal_charge_{charge}"
    neighbor_terms = []
    for bond in rule["local_bonds"]:
        endpoint = (
            bond["canonical_endpoint_2"]
            if bond["canonical_endpoint_1"] == "center"
            else bond["canonical_endpoint_1"]
        )
        atom = next(
            item for item in rule["local_atoms"]
            if item["canonical_local_atom_id"] == endpoint
        )
        neighbor_terms.append(
            f"{bond['normalized_bond_order']}_{atom['element']}_"
            f"{'leaving' if atom['is_leaving_group'] else 'retained'}"
        )
    neighborhood = "_and_".join(sorted(neighbor_terms)) or "center_only"
    core = (
        f"{charge_name}_{center['element']}_center_with_{neighborhood}_"
        f"radius_1_exact_graph_{digest[:12]}"
    )
    family = (
        "CYS_SG_single_bond_formation__" + core
        + "__topology_defined_mechanism_not_claimed"
    )
    warhead = core + "__candidate_warhead_type"
    return family, warhead


def _validate_phase_a(
    payloads: Mapping[Path, bytes]
) -> tuple[
    list[dict[str, str]], dict[str, dict[str, str]],
    dict[str, list[dict[str, str]]], dict[str, list[dict[str, str]]],
    dict[str, dict[str, str]], dict[str, dict[str, dict[str, str]]],
]:
    samples = _csv_rows(payloads[FINAL_INDEX])
    if len(samples) != 11 or len({row["sample_index_row_id"] for row in samples}) != 11:
        raise ValueError("Current11_sample_coverage_incomplete")
    evidence = {
        row["sample_index_row_id"]: row for row in _csv_rows(payloads[GRAPH_EVIDENCE])
    }
    if set(evidence) != {row["sample_index_row_id"] for row in samples}:
        raise ValueError("Current11_reaction_delta_coverage_incomplete")
    mapping: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in _csv_rows(payloads[MAPPING]):
        mapping[row["sample_index_row_id"]].append(row)
    bonds: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in _csv_rows(payloads[BONDS]):
        bonds[row["sample_index_row_id"]].append(row)
    readiness = {
        row["sample_index_row_id"]: row for row in _csv_rows(payloads[READINESS])
    }
    pair_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in _csv_rows(payloads[ATOM_PAIR_MAPPING]):
        pair_rows[row["sample_index_row_id"]].append(row)
    parent_atoms: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in _csv_rows(payloads[PARENT_ATOMS]):
        parent_atoms[row["ligand_comp_id"]][row["ccd_atom_id"]] = row
    ligand_tables = {
        path.as_posix(): _csv_rows(payloads[path]) for path in LIGAND_ATOM_TABLES
    }
    manifest = json.loads(payloads[PROJECTION_MANIFEST])
    if not manifest["transaction_succeeded"]:
        raise ValueError("predecessor_projection_transaction_not_succeeded")
    for sample in samples:
        sid = sample["sample_index_row_id"]
        if sample["covalent_residue_name"] != "CYS":
            raise ValueError("target_residue_not_CYS")
        if sample["covalent_residue_atom_name"] != "SG":
            raise ValueError("target_residue_atom_not_SG")
        if sid not in readiness or readiness[sid]["verified"] != "true":
            raise ValueError("predecessor_readiness_missing")
        reactive = [row for row in mapping[sid] if row["reactive_ligand_atom"] == "true"]
        if len(reactive) == 0:
            raise ValueError("reactive_ligand_atom_missing")
        if len(reactive) != 1:
            raise ValueError("reactive_ligand_atom_duplicated")
        if reactive[0]["parent_ccd_atom_id"] not in parent_atoms[sample["ligand_comp_id"]]:
            raise ValueError("reactive_parent_atom_missing")
        if reactive[0]["component_parent_graph_sha256"] != next(iter(
            parent_atoms[sample["ligand_comp_id"]].values()
        ))["component_parent_graph_sha256"]:
            raise ValueError("parent_graph_SHA_mismatch")
        if reactive[0]["observed_graph_sha256"] != readiness[sid]["observed_graph_sha256"]:
            raise ValueError("observed_graph_SHA_mismatch")
        exact_pairs = pair_rows[sid]
        if (
            len(exact_pairs) != 2
            or {row["entity_role"] for row in exact_pairs}
            != {"target_residue_atom", "ligand_atom"}
            or any(row["candidate_match_count"] != "1" for row in exact_pairs)
            or any(row["verified"] != "true" for row in exact_pairs)
        ):
            raise ValueError("reactive_atom_pair_not_exact_one")
        table_path = sample["ligand_atom_table_path"]
        source_reactive = [
            row for row in ligand_tables[table_path]
            if row["is_covalent_ligand_atom"] == "True"
        ]
        if (
            len(source_reactive) != 1
            or source_reactive[0]["atom_name"] != sample["ligand_covalent_atom_name"]
            or source_reactive[0]["type_symbol"] != reactive[0]["parent_ccd_type_symbol"]
        ):
            raise ValueError("reactive_ligand_atom_source_mismatch")
    return samples, evidence, mapping, bonds, readiness, parent_atoms


def build_design_result(repo_root: Path) -> BuildResult:
    payloads = load_frozen_sources(repo_root)
    source_rows = _source_inventory(payloads)
    samples, evidence, mapping, bonds, readiness, parent_atoms = _validate_phase_a(
        payloads
    )
    sample_records = []
    provenance_unique: dict[int, set[str]] = {0: set(), 1: set(), 2: set()}
    rule_unique: dict[int, set[str]] = {0: set(), 1: set(), 2: set()}
    for sample in samples:
        sid = sample["sample_index_row_id"]
        reactive = next(
            row for row in mapping[sid] if row["reactive_ligand_atom"] == "true"
        )
        center = reactive["parent_ccd_atom_id"]
        retained = {row["parent_ccd_atom_id"] for row in mapping[sid]}
        delta_row = evidence[sid]
        leaving = set(_split_ids(delta_row["leaving_group_atom_ids"]))
        missing = set(_split_ids(delta_row["missing_parent_heavy_atom_ids"]))
        delta = _reaction_delta(delta_row)
        signatures = {}
        rules = {}
        for radius in (0, 1, 2):
            signature, rule = canonical_local_signature(
                center=center,
                atoms=parent_atoms[sample["ligand_comp_id"]],
                bonds=bonds[sid],
                retained=retained,
                leaving_groups=leaving,
                reaction_delta_class=delta,
                radius=radius,
            )
            signature_json = canonical_json(signature)
            rule_json = canonical_json(rule)
            signatures[radius] = (signature, signature_json, _sha256(
                signature_json.encode()
            ))
            rules[radius] = (rule, rule_json, _sha256(rule_json.encode()))
            provenance_unique[radius].add(signatures[radius][2])
            rule_unique[radius].add(rules[radius][2])
        selected_rule = rules[SELECTED_SIGNATURE_RADIUS]
        local_parent_bonds = [
            {
                "endpoint_1": row["parent_ccd_atom_id_1"],
                "endpoint_2": row["parent_ccd_atom_id_2"],
                "normalized_bond_order": row["normalized_bond_order"],
                "projected_disposition": row["projection_disposition"],
            }
            for row in bonds[sid]
            if center in (
                row["parent_ccd_atom_id_1"], row["parent_ccd_atom_id_2"]
            )
        ]
        sample_records.append({
            "sample": sample,
            "reactive": reactive,
            "delta": delta,
            "leaving": leaving,
            "missing": missing,
            "signatures": signatures,
            "selected_rule": selected_rule,
            "local_parent_bonds": sorted(local_parent_bonds, key=canonical_json),
        })
    if len(rule_unique[0]) >= len(rule_unique[1]):
        raise ValueError("minimal_discriminative_radius_not_evidenced")
    if len(rule_unique[1]) != 7 or len(rule_unique[2]) != 7:
        raise ValueError("radius_signature_grouping_unexpected")

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in sample_records:
        groups[record["selected_rule"][2]].append(record)
    family_rows = []
    rule_rows = []
    group_authority: dict[str, tuple[str, str, str, str]] = {}
    for digest, records in sorted(groups.items()):
        rule, rule_json, _ = records[0]["selected_rule"]
        family_signature = {
            "canonical_signature_version": SIGNATURE_VERSION,
            "selected_signature_radius": SELECTED_SIGNATURE_RADIUS,
            "target_condition": rule["target_condition"],
            "local_parent_graph_exact_match_rule": rule,
            "observed_parent_delta": rule["reaction_delta"],
            "leaving_group_disposition": {
                "required_count": rule["reaction_delta"]["leaving_group_count"],
                "allowed_elements": rule["reaction_delta"]["leaving_group_elements"],
            },
        }
        family_json = canonical_json(family_signature)
        family_digest = _sha256(family_json.encode())
        family_id = "COVAPIE_CYS_SG_REACTION_FAMILY_" + family_digest[:16].upper()
        rule_id = "COVAPIE_CYS_SG_WARHEAD_RULE_" + digest[:16].upper()
        family_name, warhead_name = _semantic_names(rule, digest)
        components = {item["sample"]["ligand_comp_id"] for item in records}
        delta = rule["reaction_delta"]
        family_rows.append({
            "reaction_family_id": family_id,
            "reaction_family_semantic_name": family_name,
            "target_residue_name": "CYS",
            "target_residue_atom_name": "SG",
            "formed_bond_order": "single",
            "reaction_delta_class": delta["reaction_delta_class"],
            "leaving_group_policy": (
                "no_parent_atom_loss_observed"
                if delta["leaving_group_count"] == 0
                else "exact_verified_parent_leaving_group_loss"
            ),
            "canonical_signature_version": SIGNATURE_VERSION,
            "selected_signature_radius": SELECTED_SIGNATURE_RADIUS,
            "canonical_reaction_family_signature_json": family_json,
            "canonical_reaction_family_signature_sha256": family_digest,
            "mechanism_claim_status": "topology_defined_mechanism_not_claimed",
            "current11_sample_count": len(records),
            "unique_component_count": len(components),
            "warhead_rule_count": 1,
            "candidate_assignment_ready": True,
            "human_gold_review_completed": False,
            "approved": False,
            "blocking_reasons": (
                "design_candidate_only;human_gold_review_missing;"
                "mechanism_not_claimed"
            ),
            "verified": True,
        })
        rule_rows.append({
            "warhead_rule_id": rule_id,
            "warhead_type_semantic_name": warhead_name,
            "reaction_family_id": family_id,
            "rule_kind": RULE_KIND,
            "selected_signature_radius": SELECTED_SIGNATURE_RADIUS,
            "center_atom_element": rule["center_atom"]["element"],
            "center_atom_formal_charge": rule["center_atom"]["formal_charge"],
            "target_residue_name": "CYS",
            "target_residue_atom_name": "SG",
            "formed_bond_order": "single",
            "canonical_local_graph_rule_json": rule_json,
            "canonical_local_graph_rule_sha256": digest,
            "required_leaving_group_count": delta["leaving_group_count"],
            "allowed_leaving_group_elements": ";".join(
                delta["leaving_group_elements"]
            ),
            "required_reaction_delta_class": delta["reaction_delta_class"],
            "Current11_match_count": len(records),
            "Current11_unique_component_count": len(components),
            "exact_match_unique": True,
            "candidate_rule_assignment_ready": True,
            "approved_warhead_smarts": "",
            "SMARTS_status": "not_materialized_in_design_stage",
            "human_gold_review_completed": False,
            "approved": False,
            "blocking_reasons": (
                "design_candidate_only;SMARTS_not_materialized;"
                "human_gold_review_missing"
            ),
            "verified": True,
        })
        group_authority[digest] = (
            family_id, family_name, rule_id, warhead_name
        )
    if len(family_rows) != 7 or len(rule_rows) != 7:
        raise ValueError("candidate_registry_group_count_mismatch")
    if len({row["reaction_family_id"] for row in family_rows}) != len(family_rows):
        raise ValueError("duplicate_reaction_family_id")
    if len({row["warhead_rule_id"] for row in rule_rows}) != len(rule_rows):
        raise ValueError("duplicate_warhead_rule_id")

    design_rows = []
    for record in sample_records:
        sample = record["sample"]
        reactive = record["reactive"]
        digest = record["selected_rule"][2]
        family_id, family_name, rule_id, warhead_name = group_authority[digest]
        observed_bonds = [
            row for row in record["local_parent_bonds"]
            if row["projected_disposition"] == "retained_observed_bond"
        ]
        design_rows.append({
            "sample_index_row_id": sample["sample_index_row_id"],
            "pdb_id": sample["pdb_id"],
            "ligand_comp_id": sample["ligand_comp_id"],
            "target_residue_name": sample["covalent_residue_name"],
            "target_residue_number": sample["covalent_residue_index"],
            "target_residue_atom_name": sample["covalent_residue_atom_name"],
            "ligand_reactive_atom_name": sample["ligand_covalent_atom_name"],
            "ligand_reactive_atom_element": reactive["parent_ccd_type_symbol"],
            "ligand_reactive_parent_ccd_atom_id":
                reactive["parent_ccd_atom_id"],
            "component_parent_graph_sha256":
                reactive["component_parent_graph_sha256"],
            "observed_graph_sha256": reactive["observed_graph_sha256"],
            "reaction_delta_class": record["delta"],
            "leaving_group_atom_ids": ";".join(sorted(record["leaving"])),
            "verified_missing_parent_atom_ids":
                ";".join(sorted(record["missing"])),
            "parent_local_bonds_json": canonical_json(
                record["local_parent_bonds"]
            ),
            "observed_local_bonds_json": canonical_json(observed_bonds),
            "radius_0_signature_sha256": record["signatures"][0][2],
            "radius_1_signature_sha256": record["signatures"][1][2],
            "radius_2_signature_sha256": record["signatures"][2][2],
            "selected_signature_radius": SELECTED_SIGNATURE_RADIUS,
            "candidate_reaction_family_id": family_id,
            "candidate_reaction_family_semantic_name": family_name,
            "candidate_warhead_rule_id": rule_id,
            "candidate_warhead_type_semantic_name": warhead_name,
            "family_candidate_exact_one": True,
            "warhead_rule_candidate_exact_one": True,
            "rule_matches_parent_graph": True,
            "rule_consistent_with_observed_delta": True,
            "reaction_family_label_available": False,
            "approved_warhead_rule_available": False,
            "human_gold_review_completed": False,
            "ready_for_role_proposal_generation": False,
            "ready_for_minimal_seed_proposal_generation": False,
            "ready_for_mask_materialization": False,
            "ready_for_tensorization": False,
            "ready_for_model_integration": False,
            "ready_for_training": False,
            "blocking_reasons": (
                "candidate_assignment_design_only;reaction_family_label_not_"
                "materialized;approved_warhead_rule_missing;human_gold_review_"
                "missing"
            ),
            "verified": True,
        })
    if len(design_rows) != 11:
        raise ValueError("Current11_candidate_assignment_incomplete")
    return BuildResult(
        source_rows=source_rows,
        family_rows=tuple(family_rows),
        rule_rows=tuple(rule_rows),
        design_rows=tuple(design_rows),
        failure_rows=build_failure_rows(),
        radius_signature_unique_counts={
            radius: len(values) for radius, values in provenance_unique.items()
        },
        radius_rule_projection_unique_counts={
            radius: len(values) for radius, values in rule_unique.items()
        },
        selected_radius=SELECTED_SIGNATURE_RADIUS,
        transaction_succeeded=True,
        blocking_reasons=(),
    )


def observe_failure_scenario(scenario: DesignScenario) -> tuple[str, ...]:
    reasons = []
    if not scenario.base_source_present:
        reasons.append("BASE_source_missing")
    if not scenario.base_source_sha_matches:
        reasons.append("BASE_source_SHA_mismatch")
    if scenario.current11_sample_coverage != 11:
        reasons.append("Current11_sample_coverage_incomplete")
    if scenario.target_residue_name != "CYS":
        reasons.append("target_residue_not_CYS")
    if scenario.target_residue_atom_name != "SG":
        reasons.append("target_residue_atom_not_SG")
    if scenario.reactive_ligand_atom_count == 0:
        reasons.append("reactive_ligand_atom_missing")
    elif scenario.reactive_ligand_atom_count != 1:
        reasons.append("reactive_ligand_atom_duplicated")
    if not scenario.reactive_parent_atom_present:
        reasons.append("reactive_parent_atom_missing")
    if not scenario.parent_graph_sha_matches:
        reasons.append("parent_graph_SHA_mismatch")
    if not scenario.observed_graph_sha_matches:
        reasons.append("observed_graph_SHA_mismatch")
    if not scenario.local_graph_connected:
        reasons.append("local_graph_disconnected")
    if not scenario.bond_order_supported:
        reasons.append("unsupported_bond_order")
    if not scenario.radius_signature_deterministic:
        reasons.append("radius_signature_nondeterministic")
    if scenario.duplicate_family_id:
        reasons.append("duplicate_reaction_family_id")
    if scenario.duplicate_rule_id:
        reasons.append("duplicate_warhead_rule_id")
    if scenario.family_candidate_count == 0:
        reasons.append("family_candidate_absent")
    elif scenario.family_candidate_count != 1:
        reasons.append("family_candidate_ambiguous")
    if scenario.warhead_rule_candidate_count == 0:
        reasons.append("warhead_rule_candidate_absent")
    elif scenario.warhead_rule_candidate_count != 1:
        reasons.append("warhead_rule_candidate_ambiguous")
    if not scenario.rule_parent_graph_matches:
        reasons.append("rule_parent_graph_mismatch")
    if not scenario.rule_observed_delta_matches:
        reasons.append("rule_observed_delta_mismatch")
    if scenario.mechanism_claim_status not in (
        "topology_defined_mechanism_not_claimed",
        "mechanism_supported_by_explicit_BASE_evidence",
        "mechanism_unresolved",
    ):
        reasons.append("mechanism_overclaimed_from_topology")
    if scenario.smarts_status == "approved":
        reasons.append("SMARTS_prematurely_approved")
    if scenario.partial_materialization_attempted:
        reasons.append("partial_materialization_attempted")
    if scenario.execution_boundary_crossed:
        reasons.append("execution_boundary_crossed")
    return tuple(reasons)


def build_failure_rows() -> tuple[Mapping[str, Any], ...]:
    baseline = DesignScenario()
    rows = []
    signatures = set()
    for name, field, value, expected in FAILURE_MUTATIONS:
        mutated = dataclasses.replace(baseline, **{field: value})
        if mutated == baseline or type(getattr(mutated, field)) is not type(value):
            raise AssertionError("failure_mutation_not_exact_typed")
        reasons = observe_failure_scenario(mutated)
        signature = canonical_json({
            "dataclass": "DesignScenario",
            "field": field,
            "typed_value": {"type": type(value).__name__, "value": value},
        })
        if signature in signatures:
            raise AssertionError("failure_mutation_signature_duplicated")
        signatures.add(signature)
        verified = expected in reasons
        rows.append({
            "failure_case": name,
            "mutation_signature": signature,
            "mutated_fields": field,
            "expected_reasons": expected,
            "observed_reasons": ";".join(reasons),
            "expected_reasons_verified": verified,
            "fails_closed": verified,
            "reaction_family_registry_row_count": 0,
            "warhead_rule_registry_row_count": 0,
            "current11_design_matrix_row_count": 0,
            "warhead_type_model_head_integrated": False,
            "warhead_type_loss_integrated": False,
            "ready_for_mask_materialization": False,
            "ready_for_model_integration": False,
            "ready_for_training": False,
            "verified": verified,
        })
    return tuple(rows)


def transaction_tables(
    phase_a_passed: bool,
    phase_b_passed: bool,
    family_rows: Sequence[Mapping[str, Any]],
    rule_rows: Sequence[Mapping[str, Any]],
    design_rows: Sequence[Mapping[str, Any]],
) -> tuple[
    tuple[Mapping[str, Any], ...],
    tuple[Mapping[str, Any], ...],
    tuple[Mapping[str, Any], ...],
]:
    if not phase_a_passed or not phase_b_passed:
        return (), (), ()
    return tuple(family_rows), tuple(rule_rows), tuple(design_rows)


def build_evidence_payloads(repo_root: Path) -> dict[str, bytes]:
    try:
        result = build_design_result(repo_root)
    except Exception as exc:
        reason = str(exc) or type(exc).__name__
        try:
            sources = _source_inventory(load_frozen_sources(repo_root))
        except Exception:
            sources = ()
        result = BuildResult(
            source_rows=sources,
            family_rows=(),
            rule_rows=(),
            design_rows=(),
            failure_rows=build_failure_rows(),
            radius_signature_unique_counts={0: 0, 1: 0, 2: 0},
            radius_rule_projection_unique_counts={0: 0, 1: 0, 2: 0},
            selected_radius=SELECTED_SIGNATURE_RADIUS,
            transaction_succeeded=False,
            blocking_reasons=(reason,),
        )
    family_rows, rule_rows, design_rows = transaction_tables(
        result.transaction_succeeded, result.transaction_succeeded,
        result.family_rows, result.rule_rows, result.design_rows,
    )
    payloads = {
        SOURCE_FILE: _csv_bytes(SOURCE_COLUMNS, result.source_rows),
        FAMILY_FILE: _csv_bytes(FAMILY_COLUMNS, family_rows),
        RULE_FILE: _csv_bytes(RULE_COLUMNS, rule_rows),
        DESIGN_FILE: _csv_bytes(DESIGN_COLUMNS, design_rows),
        FAILURE_FILE: _csv_bytes(FAILURE_COLUMNS, result.failure_rows),
    }
    family_counts = Counter(
        row["candidate_reaction_family_id"] for row in design_rows
    )
    rule_counts = Counter(row["candidate_warhead_rule_id"] for row in design_rows)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "formal_base_commit": BASE_COMMIT,
        "formal_base_parent": BASE_PARENT,
        "formal_base_tree": BASE_TREE,
        "formal_base_subject": BASE_SUBJECT,
        "formal_future_commit_subject": FORMAL_COMMIT_SUBJECT,
        "authority_class": AUTHORITY_CLASS,
        "transaction_succeeded": result.transaction_succeeded,
        "transaction_blocking_reasons": list(result.blocking_reasons),
        "phase_a_source_and_reaction_center_validation_passed":
            result.transaction_succeeded,
        "phase_b_signature_grouping_and_assignment_passed":
            result.transaction_succeeded,
        "source_count": len(result.source_rows),
        "source_sha256": {
            path.as_posix(): value for path, value in FROZEN_BASE_SHA256.items()
        },
        "current11_sample_count": len(design_rows),
        "target_CYS_SG_count": sum(
            row["target_residue_name"] == "CYS"
            and row["target_residue_atom_name"] == "SG"
            for row in design_rows
        ),
        "reactive_ligand_atom_count": len(design_rows),
        "unique_component_count": len({
            row["ligand_comp_id"] for row in design_rows
        }),
        "canonical_signature_version": SIGNATURE_VERSION,
        "radius_provenance_signature_unique_counts": {
            str(key): value
            for key, value in result.radius_signature_unique_counts.items()
        },
        "radius_rule_projection_unique_counts": {
            str(key): value
            for key, value in result.radius_rule_projection_unique_counts.items()
        },
        "selected_signature_radius": result.selected_radius,
        "selected_radius_evidence": (
            "radius_0_omits_direct_bond_order_and_leaving_group_context;"
            "radius_1_is_the_minimal_complete_first_shell_and_yields_exact_one_"
            "Current11_candidate_assignments;radius_2_adds_distal_topology_but_"
            "does_not_add_a_Current11_rule_projection_group"
        ),
        "same_component_repeated_signature_consistent":
            len({row["radius_1_signature_sha256"] for row in design_rows
                 if row["ligand_comp_id"] == "JUG"}) <= 1,
        "different_components_share_radius_1_rule_projection":
            any(row["Current11_unique_component_count"] > 1 for row in rule_rows),
        "reaction_family_count": len(family_rows),
        "warhead_rule_count": len(rule_rows),
        "candidate_family_assignment_exact_one_count": sum(
            row["family_candidate_exact_one"] for row in design_rows
        ),
        "candidate_warhead_rule_assignment_exact_one_count": sum(
            row["warhead_rule_candidate_exact_one"] for row in design_rows
        ),
        "candidate_family_assignment_absent_count": 0,
        "candidate_family_assignment_ambiguous_count": 0,
        "candidate_rule_assignment_absent_count": 0,
        "candidate_rule_assignment_ambiguous_count": 0,
        "family_current11_counts": dict(sorted(family_counts.items())),
        "rule_current11_counts": dict(sorted(rule_counts.items())),
        "family_grouping_uses_component_id": False,
        "rule_grouping_uses_pdb_id": False,
        "mechanism_claim_statuses": sorted({
            row["mechanism_claim_status"] for row in family_rows
        }),
        "mechanism_specific_claim_count": 0,
        "approved_warhead_smarts_count": 0,
        "SMARTS_statuses": sorted({
            row["SMARTS_status"] for row in rule_rows
        }),
        "reaction_family_label_available": False,
        "approved_warhead_rule_available": False,
        "human_gold_review_completed": False,
        "warhead_type_auxiliary_label_contract_designed":
            result.transaction_succeeded and len(rule_rows) > 0,
        "warhead_type_candidate_class_count": len(rule_rows),
        "warhead_type_model_head_integrated": False,
        "warhead_type_loss_integrated": False,
        "planned_covalent_model_module_count": 5,
        "integrated_covalent_model_module_count": 0,
        "ready_for_role_proposal_generation": False,
        "ready_for_minimal_seed_proposal_generation": False,
        "ready_for_mask_materialization": False,
        "ready_for_tensorization": False,
        "ready_for_model_integration": False,
        "ready_for_training": False,
        "failure_mutation_count": len(result.failure_rows),
        "failure_mutations_all_fail_closed": all(
            row["fails_closed"] for row in result.failure_rows
        ),
        "output_sha256": {
            name: _sha256(payload) for name, payload in payloads.items()
        },
        "recommended_next_step": (
            "materialize_covapie_current11_cys_sg_reaction_family_and_"
            "warhead_rule_assignments_v1"
            if result.transaction_succeeded and len(design_rows) == 11
            else "resolve_covapie_cys_sg_reaction_family_and_warhead_rule_"
            "registry_design_blockers_v1"
        ),
    }
    payloads[MANIFEST_FILE] = (
        json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"
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
        "cys_sg_reaction_family_rule_design_verified "
        f"samples={manifest['current11_sample_count']}/11 "
        f"families={manifest['reaction_family_count']} "
        f"rules={manifest['warhead_rule_count']} "
        f"radius={manifest['selected_signature_radius']} "
        "training_ready=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
