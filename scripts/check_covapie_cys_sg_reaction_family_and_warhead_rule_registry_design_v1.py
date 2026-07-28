"""Independent checker for the CovaPIE Cys-SG registry design v1."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import subprocess
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[1]
BASE = "68c5ca5cf1ce5b20be5db9ce0b37e10830c09288"
BASE_PARENT = "34ff4dbb94a5caf4f8b393152e9694e5a8d7c2ce"
BASE_TREE = "971c5c6360854ae705056c99dda04e96e07fd779"
BASE_SUBJECT = "add CovaPIE Current11 observed atom projection authority v1"
SUBJECT = "add CovaPIE Cys SG reaction family and warhead rule registry design v1"
VERSION = "covapie_cys_sg_canonical_local_reaction_signature_v1"
RULE_KIND = "canonical_local_graph_exact_match_v1"
OUT = Path(
    "data/derived/covalent_small/"
    "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1"
)
SOURCE_FILE = "covapie_reaction_family_rule_design_source_inventory.csv"
FAMILY_FILE = "covapie_cys_sg_reaction_family_registry.csv"
RULE_FILE = "covapie_cys_sg_warhead_rule_registry.csv"
DESIGN_FILE = "covapie_current11_reaction_family_and_warhead_rule_design_matrix.csv"
FAILURE_FILE = "covapie_reaction_family_rule_design_failure_matrix.csv"
MANIFEST_FILE = (
    "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_manifest.json"
)
EXACT10 = (
    Path(
        "src/covalent_ext/"
        "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1.py"
    ),
    Path(
        "tests/"
        "test_covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1.py"
    ),
    Path(__file__).resolve().relative_to(ROOT),
    Path(
        "docs/"
        "covapie_cys_sg_reaction_family_and_warhead_rule_registry_design_v1_summary.md"
    ),
    *(OUT / name for name in (
        SOURCE_FILE, FAMILY_FILE, RULE_FILE, DESIGN_FILE, FAILURE_FILE,
        MANIFEST_FILE,
    )),
)

P = Path("data/derived/covalent_small")
PROJECTION = P / "covapie_current11_observed_to_parent_atom_projection_authority_v1"
MAPPING = PROJECTION / "covapie_current11_observed_to_parent_atom_mapping_authority.csv"
BONDS = PROJECTION / "covapie_current11_parent_and_observed_projected_bond_authority.csv"
READINESS = PROJECTION / "covapie_current11_observed_projection_readiness_matrix.csv"
PROJECTION_MANIFEST = (
    PROJECTION
    / "covapie_current11_observed_to_parent_atom_projection_authority_manifest.json"
)
PARENT = P / "covapie_exact9_audited_local_ccd_parent_graph_authority_v1"
PARENT_ATOMS = PARENT / "covapie_exact9_parent_heavy_atom_authority.csv"
PARENT_BONDS = PARENT / "covapie_exact9_parent_heavy_bond_authority.csv"
GRAPH = (
    P / "covapie_independent_group_expansion_batch_independence_evidence_"
    "materialization_smoke_v0/covapie_ligand_graph_scaffold_evidence.csv"
)
PAIR = (
    P / "covapie_covalent_bond_atom_pair_encoding_contract_current_canonical_"
    "evidence_validation_v1/"
    "covapie_atom_pair_atom_table_mapping_validation_matrix.csv"
)
INDEX = P / "covapie_final_dataset_materialization_smoke_v0/final_dataset_index.csv"
PREDECESSOR = Path(
    "src/covalent_ext/"
    "covapie_current11_observed_to_parent_atom_projection_authority_v1.py"
)
LIGANDS = (
    P / "covapie_sample_preparation_execution_smoke_v0/samples/6BV6_JUG/ligand_atom_table.csv",
    P / "covapie_sample_preparation_execution_smoke_v0/samples/6BV8_JUG/ligand_atom_table.csv",
    P / "covapie_sample_preparation_execution_smoke_v0/samples/6BV5_JUG/ligand_atom_table.csv",
    P / "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/samples/1AEC_E64/ligand_atom_table.csv",
    P / "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/samples/1AIM_ZYA/ligand_atom_table.csv",
    P / "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/samples/1AU3_PCM/ligand_atom_table.csv",
    P / "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/samples/1AU4_INP/ligand_atom_table.csv",
    P / "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/samples/1AYU_INA/ligand_atom_table.csv",
    P / "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/samples/1AYV_IN6/ligand_atom_table.csv",
    P / "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/samples/1AYW_IN3/ligand_atom_table.csv",
    P / "covapie_independent_group_expansion_batch_sample_preparation_execution_smoke_v0/samples/1B02_UFP/ligand_atom_table.csv",
)
SHAS = {
    PREDECESSOR: "002ff3367c5e68d8e5bde77e5460cc0f8bc83c5102157a5fd1ef88d53b73ecc5",
    MAPPING: "f803e0c5fb2585c8dae31dbff254749496f897f4bf9a5103455c6c675a132a1e",
    BONDS: "bd31b7c074c3d4226c26bfe0210b9c3460f38c5087f1157b1167749f91bfffe0",
    READINESS: "ec7bb2c203a7b13f525c413171b734fdd9f8af934b6e7e8eaf3fc6ae141128a0",
    PROJECTION_MANIFEST: "e553e9cb1518cd2c9465772758539e9610c8f81cd702dd0440e99fbd143fc0a7",
    PARENT_ATOMS: "d50b052c2ed2573ccfdcf66470a077744ad11f4a083daee11f20d794b3b23fe7",
    PARENT_BONDS: "26957b9f78217c808d2dc021cfab1a2bf78dd1708c46c49f220ae32a3a09ebbf",
    GRAPH: "982a9f89a89d3a4ad6a3e468cfd16d2fdfd5435cbf6d593e086fbd7fadd3ec73",
    PAIR: "9f26b25ed11d186a02a1f859de10a105605ce3af13805ac5a4be1ad73199df45",
    INDEX: "c4c31888cb0f7c148b00656ccf22ab68fab842fcdafdee049b2f420eddc1302d",
    LIGANDS[0]: "c91bb14b37c9b7231cb0e2fac4e2ba39ce65d65b6a9481b1e83b83890f2e1650",
    LIGANDS[1]: "13d2148bbcf544b62bd256b7ab8f14f31187d550a9e75d8c6d72deddada87d4a",
    LIGANDS[2]: "0f375a441d3d1718dfdbf084aebae0c4612aaae7905c8131018bed671fb6c70e",
    LIGANDS[3]: "02f4f7157da8318076290de0b36d21c2e40233e45e315264a67209dd2b4dc0cf",
    LIGANDS[4]: "a813b57350cfd2bfae664c7b0d7d92a0d5359b8b1274d39eae0a97a76f61bdfa",
    LIGANDS[5]: "90c70d05a0a9c1026c90a6c85b9e1989afa8c51671fe084cbb7f063b9427616a",
    LIGANDS[6]: "d6f3a76db2a5448141403007708682ed2278b6bd1137b3be65a95ea615912665",
    LIGANDS[7]: "3ea203e5ee078792c31edc83074629ba29dda72f6c4f7d90b0aad1246673e399",
    LIGANDS[8]: "dfdaa3d37f81a79e51fee9e24434eca353ce922bda0c927fedb053566276bf49",
    LIGANDS[9]: "f8f3a1b5b9143b797acc18724e83be2fb0b89876b66081a584e908b83ed0a67c",
    LIGANDS[10]: "f33a8ebf2edda9cb63e2f81d10812f549bf57858e6ae2ffcbde6282a49c35e9e",
}


def git(
    *args: str, repo_root: Path = ROOT, check: bool = True
) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ("git", *args), cwd=repo_root, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, check=False,
    )
    if check and result.returncode:
        raise RuntimeError("git_failed:" + " ".join(args))
    return result


def base(path: Path, repo_root: Path = ROOT) -> bytes:
    return git("show", f"{BASE}:{path.as_posix()}", repo_root=repo_root).stdout


def sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def rows(payload: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(payload.decode())))


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def validate_execution_boundary_independent(repo_root: Path = ROOT) -> str:
    identity = git(
        "show", "-s", "--format=%H%n%P%n%T%n%s", BASE,
        repo_root=repo_root,
    ).stdout.decode().splitlines()
    if identity != [BASE, BASE_PARENT, BASE_TREE, BASE_SUBJECT]:
        raise AssertionError("formal_BASE_identity_mismatch")
    head = git("rev-parse", "HEAD", repo_root=repo_root).stdout.decode().strip()
    if head == BASE:
        return "pre_commit"
    raw = git("cat-file", "commit", head, repo_root=repo_root).stdout
    headers, separator, message = raw.partition(b"\n\n")
    parents = [
        line[7:].decode() for line in headers.splitlines()
        if line.startswith(b"parent ")
    ]
    subject, newline, body = message.partition(b"\n")
    if (
        not separator or parents != [BASE] or not newline
        or subject.decode() != SUBJECT or body
    ):
        raise AssertionError("successor_commit_contract_mismatch")
    changed = {
        item.decode() for item in git(
            "diff-tree", "--no-commit-id", "--name-only", "-r", "-z", head,
            repo_root=repo_root,
        ).stdout.split(b"\0") if item
    }
    if changed != {path.as_posix() for path in EXACT10}:
        raise AssertionError("successor_exact10_mismatch")
    tree = [
        item for item in git(
            "ls-tree", "-r", "-z", head, "--",
            *(path.as_posix() for path in EXACT10),
            repo_root=repo_root,
        ).stdout.split(b"\0") if item
    ]
    if len(tree) != 10 or any(
        not item.partition(b"\t")[0].startswith(b"100644 blob ") for item in tree
    ):
        raise AssertionError("successor_modes_mismatch")
    branch = git(
        "symbolic-ref", "--quiet", "--short", "HEAD",
        repo_root=repo_root, check=False,
    )
    if branch.returncode:
        return "detached_candidate_post_commit"
    if branch.stdout.strip() != b"main":
        raise AssertionError("successor_branch_mismatch")
    origin = git(
        "rev-parse", "--verify", "refs/remotes/origin/main", repo_root=repo_root
    ).stdout.strip()
    if origin.decode() == BASE:
        return "formal_main_post_commit_unpushed"
    if origin.decode() == head:
        return "formal_main_post_push"
    raise AssertionError("successor_origin_lifecycle_mismatch")


def distances(center: str, bond_rows: Iterable[Mapping[str, str]]) -> dict[str, int]:
    adjacency: dict[str, set[str]] = defaultdict(set)
    for row in bond_rows:
        left, right = row["parent_ccd_atom_id_1"], row["parent_ccd_atom_id_2"]
        adjacency[left].add(right)
        adjacency[right].add(left)
    result = {center: 0}
    queue = deque([center])
    while queue:
        atom = queue.popleft()
        for neighbor in sorted(adjacency[atom]):
            if neighbor not in result:
                result[neighbor] = result[atom] + 1
                queue.append(neighbor)
    return result


def reconstruct(
    center: str,
    atom_rows: Mapping[str, Mapping[str, str]],
    bond_rows: list[Mapping[str, str]],
    retained: set[str],
    leaving: set[str],
    delta: str,
    radius: int,
) -> tuple[str, str, str]:
    distance = distances(center, bond_rows)
    if len(distance) != len(atom_rows):
        raise AssertionError("disconnected_parent_graph")
    selected = {key for key, value in distance.items() if value <= radius}
    atoms = [{
        "parent_ccd_atom_id": atom,
        "relative_graph_distance": distance[atom],
        "element": atom_rows[atom]["ccd_type_symbol"],
        "formal_charge": int(atom_rows[atom]["ccd_formal_charge"]),
        "is_leaving_group": atom in leaving,
        "is_retained_observed": atom in retained,
    } for atom in sorted(selected, key=lambda item: (distance[item], item))]
    bonds = sorted(({
        "endpoint_1_parent_ccd_atom_id": min(
            row["parent_ccd_atom_id_1"], row["parent_ccd_atom_id_2"]
        ),
        "endpoint_2_parent_ccd_atom_id": max(
            row["parent_ccd_atom_id_1"], row["parent_ccd_atom_id_2"]
        ),
        "normalized_bond_order": row["normalized_bond_order"],
        "projected_disposition": row["projection_disposition"],
    } for row in bond_rows if (
        row["parent_ccd_atom_id_1"] in selected
        and row["parent_ccd_atom_id_2"] in selected
    )), key=canonical)
    reaction = {
        "reaction_delta_class": delta,
        "leaving_group_count": len(leaving),
        "leaving_group_elements": sorted(
            atom_rows[item]["ccd_type_symbol"] for item in leaving
        ),
    }
    target = {"residue": "CYS", "residue_atom": "SG", "formed_bond_order": "single"}
    provenance = {
        "canonical_signature_version": VERSION,
        "radius": radius,
        "center_atom": {
            "parent_ccd_atom_id": center,
            "element": atom_rows[center]["ccd_type_symbol"],
            "formal_charge": int(atom_rows[center]["ccd_formal_charge"]),
            "reactive": True,
        },
        "local_atoms": atoms, "local_bonds": bonds,
        "target_condition": target, "reaction_delta": reaction,
    }
    incident: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for row in bonds:
        left = row["endpoint_1_parent_ccd_atom_id"]
        right = row["endpoint_2_parent_ccd_atom_id"]
        value = (row["normalized_bond_order"], row["projected_disposition"])
        incident[left].append(value)
        incident[right].append(value)
    ordered = sorted(
        (item for item in atoms if item["parent_ccd_atom_id"] != center),
        key=lambda item: (
            item["relative_graph_distance"], item["element"],
            item["formal_charge"], item["is_leaving_group"],
            item["is_retained_observed"],
            tuple(sorted(incident[item["parent_ccd_atom_id"]])),
            item["parent_ccd_atom_id"],
        ),
    )
    labels = {center: "center"}
    labels.update({
        item["parent_ccd_atom_id"]: f"local_atom_{index:03d}"
        for index, item in enumerate(ordered, 1)
    })
    rule_atoms = [{
        "canonical_local_atom_id": labels[item["parent_ccd_atom_id"]],
        "relative_graph_distance": item["relative_graph_distance"],
        "element": item["element"], "formal_charge": item["formal_charge"],
        "is_leaving_group": item["is_leaving_group"],
        "is_retained_observed": item["is_retained_observed"],
    } for item in [atoms[0], *ordered]]
    rule_bonds = sorted(({
        "canonical_endpoint_1": min(
            labels[row["endpoint_1_parent_ccd_atom_id"]],
            labels[row["endpoint_2_parent_ccd_atom_id"]],
        ),
        "canonical_endpoint_2": max(
            labels[row["endpoint_1_parent_ccd_atom_id"]],
            labels[row["endpoint_2_parent_ccd_atom_id"]],
        ),
        "normalized_bond_order": row["normalized_bond_order"],
        "projected_disposition": row["projected_disposition"],
    } for row in bonds), key=canonical)
    rule = {
        "rule_kind": RULE_KIND,
        "canonical_signature_version": VERSION,
        "selected_signature_radius": radius,
        "center_atom": {
            "canonical_local_atom_id": "center",
            "element": atom_rows[center]["ccd_type_symbol"],
            "formal_charge": int(atom_rows[center]["ccd_formal_charge"]),
            "reactive": True,
        },
        "local_atoms": rule_atoms, "local_bonds": rule_bonds,
        "target_condition": target, "reaction_delta": reaction,
    }
    rule_json = canonical(rule)
    return (
        sha(canonical(provenance).encode()),
        sha(rule_json.encode()),
        rule_json,
    )


def validate_materialized_assignment_identity(
    samples: list[Mapping[str, str]],
    reconstructed_rule_by_sample: Mapping[str, Mapping[str, Any]],
    materialized_design_rows: list[Mapping[str, str]],
    materialized_rule_rows: list[Mapping[str, str]],
    materialized_family_rows: list[Mapping[str, str]],
    manifest: Mapping[str, Any],
) -> None:
    """Fail closed on any break in the reconstructed rule/family identity chain."""

    design_by_sample: dict[str, Mapping[str, str]] = {}
    for row in materialized_design_rows:
        sample_id = row["sample_index_row_id"]
        if sample_id in design_by_sample:
            raise ValueError("design_sample_identity_duplicated")
        design_by_sample[sample_id] = row

    rule_by_sha256: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    rule_by_id: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    parsed_rule_by_sha256: dict[str, Mapping[str, Any]] = {}
    for row in materialized_rule_rows:
        raw_json = row["canonical_local_graph_rule_json"]
        try:
            parsed = json.loads(raw_json)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("rule_registry_JSON_invalid") from exc
        if canonical(parsed) != raw_json:
            raise ValueError("rule_registry_JSON_not_canonical")
        observed_sha = sha(raw_json.encode())
        recorded_sha = row["canonical_local_graph_rule_sha256"]
        if observed_sha != recorded_sha:
            raise ValueError("rule_registry_JSON_SHA_mismatch")
        expected_id = (
            "COVAPIE_CYS_SG_WARHEAD_RULE_" + recorded_sha[:16].upper()
        )
        if row["warhead_rule_id"] != expected_id:
            raise ValueError("rule_registry_ID_SHA_mismatch")
        if (
            row["selected_signature_radius"] != "1"
            or row["rule_kind"] != RULE_KIND
            or row["target_residue_name"] != "CYS"
            or row["target_residue_atom_name"] != "SG"
            or row["formed_bond_order"] != "single"
            or parsed.get("selected_signature_radius") != 1
            or parsed.get("rule_kind") != RULE_KIND
            or parsed.get("target_condition") != {
                "residue": "CYS",
                "residue_atom": "SG",
                "formed_bond_order": "single",
            }
        ):
            raise ValueError("rule_registry_contract_mismatch")
        if (
            row["approved_warhead_smarts"] != ""
            or row["SMARTS_status"] != "not_materialized_in_design_stage"
            or row["approved"] != "false"
        ):
            raise ValueError("rule_registry_approval_boundary_crossed")
        rule_by_sha256[recorded_sha].append(row)
        rule_by_id[row["warhead_rule_id"]].append(row)
        parsed_rule_by_sha256[recorded_sha] = parsed

    family_by_id: dict[str, list[Mapping[str, str]]] = defaultdict(list)
    family_sha_seen: set[str] = set()
    for row in materialized_family_rows:
        raw_json = row["canonical_reaction_family_signature_json"]
        try:
            parsed = json.loads(raw_json)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("family_registry_JSON_invalid") from exc
        if canonical(parsed) != raw_json:
            raise ValueError("family_registry_JSON_not_canonical")
        observed_sha = sha(raw_json.encode())
        recorded_sha = row["canonical_reaction_family_signature_sha256"]
        if observed_sha != recorded_sha:
            raise ValueError("family_registry_JSON_SHA_mismatch")
        expected_id = (
            "COVAPIE_CYS_SG_REACTION_FAMILY_" + recorded_sha[:16].upper()
        )
        if row["reaction_family_id"] != expected_id:
            raise ValueError("family_registry_ID_SHA_mismatch")
        if recorded_sha in family_sha_seen:
            raise ValueError("family_registry_SHA_duplicated")
        family_sha_seen.add(recorded_sha)
        if (
            row["selected_signature_radius"] != "1"
            or row["target_residue_name"] != "CYS"
            or row["target_residue_atom_name"] != "SG"
            or row["formed_bond_order"] != "single"
            or row["mechanism_claim_status"]
            != "topology_defined_mechanism_not_claimed"
            or row["approved"] != "false"
        ):
            raise ValueError("family_registry_contract_mismatch")
        family_by_id[row["reaction_family_id"]].append(row)

    sample_ids = [sample["sample_index_row_id"] for sample in samples]
    if (
        len(samples) != 11
        or len(set(sample_ids)) != 11
        or set(sample_ids) != set(reconstructed_rule_by_sample)
        or set(sample_ids) != set(design_by_sample)
    ):
        raise ValueError("Current11_assignment_identity_coverage_mismatch")

    current11_pdb_ids = {sample["pdb_id"] for sample in samples}
    current11_component_ids = {sample["ligand_comp_id"] for sample in samples}
    rule_sample_counts: Counter[str] = Counter()
    rule_component_sets: dict[str, set[str]] = defaultdict(set)
    family_sample_counts: Counter[str] = Counter()
    family_component_sets: dict[str, set[str]] = defaultdict(set)
    rules_by_family: dict[str, set[str]] = defaultdict(set)

    for sample in samples:
        sample_id = sample["sample_index_row_id"]
        reconstructed = reconstructed_rule_by_sample[sample_id]
        reconstructed_sha = str(reconstructed["rule_sha256"])
        candidates = rule_by_sha256.get(reconstructed_sha, [])
        if not candidates:
            raise ValueError("rule_candidate_absent")
        if len(candidates) != 1:
            raise ValueError("rule_candidate_ambiguous")
        rule_row = candidates[0]
        design_row = design_by_sample[sample_id]
        rule_id = rule_row["warhead_rule_id"]
        if design_row["candidate_warhead_rule_id"] != rule_id:
            raise ValueError(
                "assigned_rule_id_does_not_match_reconstructed_digest"
            )
        if (
            design_row["candidate_warhead_type_semantic_name"]
            != rule_row["warhead_type_semantic_name"]
        ):
            raise ValueError("assigned_rule_semantic_name_mismatch")
        if (
            design_row["rule_matches_parent_graph"] != "true"
            or design_row["rule_consistent_with_observed_delta"] != "true"
        ):
            raise ValueError("assigned_rule_evidence_flags_not_true")
        expected_elements = ";".join(reconstructed["leaving_group_elements"])
        if (
            rule_row["required_reaction_delta_class"]
            != reconstructed["reaction_delta_class"]
            or int(rule_row["required_leaving_group_count"])
            != reconstructed["leaving_group_count"]
            or rule_row["allowed_leaving_group_elements"] != expected_elements
        ):
            raise ValueError("assigned_rule_observed_delta_mismatch")

        parsed_rule = parsed_rule_by_sha256[reconstructed_sha]
        family_signature = {
            "canonical_signature_version": VERSION,
            "selected_signature_radius": 1,
            "target_condition": parsed_rule["target_condition"],
            "local_parent_graph_exact_match_rule": parsed_rule,
            "observed_parent_delta": parsed_rule["reaction_delta"],
            "leaving_group_disposition": {
                "required_count":
                    parsed_rule["reaction_delta"]["leaving_group_count"],
                "allowed_elements":
                    parsed_rule["reaction_delta"]["leaving_group_elements"],
            },
        }
        family_json = canonical(family_signature)
        family_sha = sha(family_json.encode())
        family_id = (
            "COVAPIE_CYS_SG_REACTION_FAMILY_" + family_sha[:16].upper()
        )
        if rule_row["reaction_family_id"] != family_id:
            raise ValueError("rule_family_link_mismatch")
        family_candidates = family_by_id.get(family_id, [])
        if len(family_candidates) != 1:
            raise ValueError("family_candidate_absent_or_ambiguous")
        family_row = family_candidates[0]
        if family_row["canonical_reaction_family_signature_json"] != family_json:
            raise ValueError("family_registry_signature_mismatch")
        if design_row["candidate_reaction_family_id"] != family_id:
            raise ValueError(
                "assigned_family_id_does_not_match_reconstructed_family"
            )
        if (
            design_row["candidate_reaction_family_semantic_name"]
            != family_row["reaction_family_semantic_name"]
        ):
            raise ValueError("assigned_family_semantic_name_mismatch")

        rule_name = rule_row["warhead_type_semantic_name"]
        family_name = family_row["reaction_family_semantic_name"]
        if not rule_name.endswith("__candidate_warhead_type"):
            raise ValueError("warhead_semantic_name_suffix_mismatch")
        if not family_name.endswith(
            "__topology_defined_mechanism_not_claimed"
        ):
            raise ValueError("family_semantic_name_suffix_mismatch")
        for forbidden in current11_pdb_ids | current11_component_ids:
            if forbidden in rule_name or forbidden in family_name:
                raise ValueError("semantic_name_contains_sample_identity")

        component_id = sample["ligand_comp_id"]
        rule_sample_counts[rule_id] += 1
        rule_component_sets[rule_id].add(component_id)
        family_sample_counts[family_id] += 1
        family_component_sets[family_id].add(component_id)
        rules_by_family[family_id].add(rule_id)

    if len(materialized_rule_rows) != 7:
        raise ValueError("rule_registry_row_count_mismatch")
    if len(rule_by_sha256) != 7:
        raise ValueError("rule_registry_SHA_not_unique")
    if len(rule_by_id) != 7 or any(
        len(candidates) != 1 for candidates in rule_by_id.values()
    ):
        raise ValueError("rule_registry_ID_not_unique")
    if len(materialized_family_rows) != 7:
        raise ValueError("family_registry_row_count_mismatch")
    if len(family_by_id) != 7 or any(
        len(candidates) != 1 for candidates in family_by_id.values()
    ):
        raise ValueError("family_registry_ID_not_unique")

    for row in materialized_rule_rows:
        rule_id = row["warhead_rule_id"]
        if (
            int(row["Current11_match_count"]) != rule_sample_counts[rule_id]
            or int(row["Current11_unique_component_count"])
            != len(rule_component_sets[rule_id])
        ):
            raise ValueError("rule_assignment_count_mismatch")
    for row in materialized_family_rows:
        family_id = row["reaction_family_id"]
        if (
            int(row["current11_sample_count"])
            != family_sample_counts[family_id]
            or int(row["unique_component_count"])
            != len(family_component_sets[family_id])
            or int(row["warhead_rule_count"])
            != len(rules_by_family[family_id])
        ):
            raise ValueError("family_assignment_count_mismatch")

    expected_rule_counts = dict(sorted(rule_sample_counts.items()))
    expected_family_counts = dict(sorted(family_sample_counts.items()))
    if manifest.get("rule_current11_counts") != expected_rule_counts:
        raise ValueError("manifest_rule_assignment_count_mismatch")
    if manifest.get("family_current11_counts") != expected_family_counts:
        raise ValueError("manifest_family_assignment_count_mismatch")
    if (
        manifest.get("candidate_rule_assignment_absent_count") != 0
        or manifest.get("candidate_rule_assignment_ambiguous_count") != 0
        or manifest.get("candidate_family_assignment_absent_count") != 0
        or manifest.get("candidate_family_assignment_ambiguous_count") != 0
        or manifest.get("candidate_warhead_rule_assignment_exact_one_count")
        != 11
        or manifest.get("candidate_family_assignment_exact_one_count") != 11
    ):
        raise ValueError("manifest_assignment_exact_one_count_mismatch")


EXPECTED_FAILURES = {
    "BASE source missing": "BASE_source_missing",
    "BASE source SHA mismatch": "BASE_source_SHA_mismatch",
    "Current11 sample coverage incomplete": "Current11_sample_coverage_incomplete",
    "target residue not CYS": "target_residue_not_CYS",
    "target residue atom not SG": "target_residue_atom_not_SG",
    "reactive ligand atom missing": "reactive_ligand_atom_missing",
    "reactive ligand atom duplicated": "reactive_ligand_atom_duplicated",
    "reactive parent atom missing": "reactive_parent_atom_missing",
    "parent graph SHA mismatch": "parent_graph_SHA_mismatch",
    "observed graph SHA mismatch": "observed_graph_SHA_mismatch",
    "local graph disconnected": "local_graph_disconnected",
    "unsupported bond order": "unsupported_bond_order",
    "radius signature nondeterministic": "radius_signature_nondeterministic",
    "duplicate family ID": "duplicate_reaction_family_id",
    "duplicate rule ID": "duplicate_warhead_rule_id",
    "family candidate absent": "family_candidate_absent",
    "family candidate ambiguous": "family_candidate_ambiguous",
    "warhead rule candidate absent": "warhead_rule_candidate_absent",
    "warhead rule candidate ambiguous": "warhead_rule_candidate_ambiguous",
    "rule parent-graph mismatch": "rule_parent_graph_mismatch",
    "rule observed-delta mismatch": "rule_observed_delta_mismatch",
    "mechanism overclaimed": "mechanism_overclaimed_from_topology",
    "SMARTS prematurely approved": "SMARTS_prematurely_approved",
    "partial materialization attempted": "partial_materialization_attempted",
    "execution boundary crossed": "execution_boundary_crossed",
}


def check(repo_root: Path = ROOT) -> dict[str, Any]:
    lifecycle = validate_execution_boundary_independent(repo_root)
    payloads = {}
    for path, expected in SHAS.items():
        payload = base(path, repo_root)
        if sha(payload) != expected:
            raise AssertionError("source_SHA_mismatch:" + path.as_posix())
        payloads[path] = payload
    if len(payloads) != 21:
        raise AssertionError("source_count_not_21")
    samples = rows(payloads[INDEX])
    mapping: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows(payloads[MAPPING]):
        mapping[row["sample_index_row_id"]].append(row)
    bonds: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows(payloads[BONDS]):
        bonds[row["sample_index_row_id"]].append(row)
    evidence = {
        row["sample_index_row_id"]: row for row in rows(payloads[GRAPH])
    }
    parent: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for row in rows(payloads[PARENT_ATOMS]):
        parent[row["ligand_comp_id"]][row["ccd_atom_id"]] = row
    materialized_design = {
        row["sample_index_row_id"]: row
        for row in rows((repo_root / OUT / DESIGN_FILE).read_bytes())
    }
    materialized_rules = rows((repo_root / OUT / RULE_FILE).read_bytes())
    materialized_families = rows((repo_root / OUT / FAMILY_FILE).read_bytes())
    if len(samples) != 11 or len(materialized_design) != 11:
        raise AssertionError("Current11_not_exact11")
    rule_groups = {0: set(), 1: set(), 2: set()}
    reconstructed_rule_by_sample: dict[str, Mapping[str, Any]] = {}
    for sample in samples:
        sid = sample["sample_index_row_id"]
        if (
            sample["covalent_residue_name"] != "CYS"
            or sample["covalent_residue_atom_name"] != "SG"
        ):
            raise AssertionError("target_not_CYS_SG")
        reactive = [row for row in mapping[sid] if row["reactive_ligand_atom"] == "true"]
        if len(reactive) != 1:
            raise AssertionError("reactive_not_exact_one")
        source = reactive[0]
        retained = {row["parent_ccd_atom_id"] for row in mapping[sid]}
        delta_row = evidence[sid]
        leaving = {item for item in delta_row["leaving_group_atom_ids"].split(";") if item}
        delta = (
            delta_row["reaction_delta_class"]
            or delta_row["atom_inventory_reconciliation_status"]
        )
        observed = materialized_design[sid]
        for radius in (0, 1, 2):
            provenance_sha, rule_sha, rule_json = reconstruct(
                source["parent_ccd_atom_id"], parent[sample["ligand_comp_id"]],
                bonds[sid], retained, leaving, delta, radius,
            )
            if observed[f"radius_{radius}_signature_sha256"] != provenance_sha:
                raise AssertionError("provenance_signature_mismatch")
            rule_groups[radius].add(rule_sha)
            if radius == 1:
                reconstructed_rule_by_sample[sid] = {
                    "rule_sha256": rule_sha,
                    "rule_json": rule_json,
                    "reaction_delta_class": delta,
                    "leaving_group_count": len(leaving),
                    "leaving_group_elements": sorted(
                        parent[sample["ligand_comp_id"]][item][
                            "ccd_type_symbol"
                        ]
                        for item in leaving
                    ),
                }
        if observed["selected_signature_radius"] != "1":
            raise AssertionError("selected_radius_not_1")
        false_fields = (
            "reaction_family_label_available", "approved_warhead_rule_available",
            "human_gold_review_completed", "ready_for_role_proposal_generation",
            "ready_for_minimal_seed_proposal_generation",
            "ready_for_mask_materialization", "ready_for_tensorization",
            "ready_for_model_integration", "ready_for_training",
        )
        if any(observed[field] != "false" for field in false_fields):
            raise AssertionError("execution_boundary_crossed")
    if {radius: len(values) for radius, values in rule_groups.items()} != {
        0: 2, 1: 7, 2: 7,
    }:
        raise AssertionError("independent_radius_grouping_mismatch")
    if len(materialized_rules) != 7 or len(materialized_families) != 7:
        raise AssertionError("registry_count_mismatch")
    if any(
        row["SMARTS_status"] != "not_materialized_in_design_stage"
        or row["approved_warhead_smarts"] or row["approved"] != "false"
        for row in materialized_rules
    ):
        raise AssertionError("SMARTS_or_rule_prematurely_approved")
    if any(
        row["mechanism_claim_status"]
        != "topology_defined_mechanism_not_claimed"
        for row in materialized_families
    ):
        raise AssertionError("mechanism_overclaimed")
    failures = rows((repo_root / OUT / FAILURE_FILE).read_bytes())
    if len(failures) != 25 or {
        row["failure_case"] for row in failures
    } != set(EXPECTED_FAILURES):
        raise AssertionError("failure_inventory_mismatch")
    for row in failures:
        if (
            EXPECTED_FAILURES[row["failure_case"]] not in row["observed_reasons"]
            or row["fails_closed"] != "true"
            or row["ready_for_training"] != "false"
        ):
            raise AssertionError("failure_not_closed")
    source_inventory = rows((repo_root / OUT / SOURCE_FILE).read_bytes())
    if (
        len(source_inventory) != 21
        or {row["source_path"] for row in source_inventory}
        != {path.as_posix() for path in SHAS}
    ):
        raise AssertionError("source_inventory_mismatch")
    manifest = json.loads((repo_root / OUT / MANIFEST_FILE).read_bytes())
    validate_materialized_assignment_identity(
        samples,
        reconstructed_rule_by_sample,
        list(materialized_design.values()),
        materialized_rules,
        materialized_families,
        manifest,
    )
    if (
        not manifest["transaction_succeeded"]
        or manifest["current11_sample_count"] != 11
        or manifest["reaction_family_count"] != 7
        or manifest["warhead_rule_count"] != 7
        or manifest["selected_signature_radius"] != 1
        or manifest["warhead_type_model_head_integrated"]
        or manifest["warhead_type_loss_integrated"]
        or manifest["integrated_covalent_model_module_count"] != 0
        or manifest["ready_for_training"]
    ):
        raise AssertionError("manifest_contract_mismatch")
    for name, expected in manifest["output_sha256"].items():
        if sha((repo_root / OUT / name).read_bytes()) != expected:
            raise AssertionError("materialized_output_SHA_mismatch:" + name)
    return {
        "lifecycle": lifecycle, "sources": 21, "samples": 11,
        "families": 7, "rules": 7, "failures": 25, "selected_radius": 1,
    }


def main() -> int:
    result = check()
    print(
        "cys_sg_registry_design_independent_check_passed "
        f"sources={result['sources']} samples={result['samples']}/11 "
        f"families={result['families']} "
        f"rules={result['rules']} failures={result['failures']} "
        f"radius={result['selected_radius']} training_ready=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
