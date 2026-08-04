#!/usr/bin/env python3
"""Read-only checker for the Current11 reaction-transformation overlay."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import stat
import subprocess
import sys
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import covalent_ext.covapie_current11_reaction_transformation_evidence_overlay_contract_v1 as overlay  # noqa: E402


_REQUIRED_STRUCTURED_SCHEMA_NAMES = (
    "reviewed_atom_map_contract_json",
    "reviewed_attachment_boundary_map_numbers_by_sample_json",
    "reviewed_pre_or_post_atom_state_contract_json",
    "reviewed_edge_list_json",
    "reviewed_bond_order_changes_json",
    "reviewed_formal_charge_changes_json",
    "reviewed_protonation_transfer_contract_json",
    "reviewed_leaving_group_contract_json",
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _git(repo_root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ("git", "-C", str(repo_root), *args),
        check=False,
        stdin=subprocess.DEVNULL,
        capture_output=True,
    )
    if result.returncode != 0 or result.stderr:
        raise ValueError(overlay.ERROR)
    return result.stdout


def _csv(payload: bytes) -> tuple[tuple[str, ...], list[dict[str, str]]]:
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    return tuple(reader.fieldnames or ()), list(reader)


def _check_structured_schema_contract(schemas: object | None = None) -> None:
    """Independently check the future structured-JSON schema definitions."""

    value = overlay.STRUCTURED_JSON_SCHEMAS if schemas is None else schemas
    if type(value) is not dict or tuple(value) != _REQUIRED_STRUCTURED_SCHEMA_NAMES:
        raise ValueError(overlay.ERROR)
    if any(
        type(schema) is not dict
        or tuple(schema) != ("samples",)
        or type(schema["samples"]) is not dict
        or tuple(schema["samples"]) != ("<sample_id>",)
        for schema in value.values()
    ):
        raise ValueError(overlay.ERROR)

    attachment = value[
        "reviewed_attachment_boundary_map_numbers_by_sample_json"
    ]["samples"]["<sample_id>"]
    attachment_keys = (
        "warhead_attachment_atom_map_number",
        "nonwarhead_boundary_atom_map_number",
        "bond_order",
    )
    if (
        type(attachment) is not list
        or len(attachment) != 2
        or any(type(record) is not dict for record in attachment)
        or any(tuple(record) != attachment_keys for record in attachment)
        or attachment[0] != attachment[1]
    ):
        raise ValueError(overlay.ERROR)

    leaving_group = value[
        "reviewed_leaving_group_contract_json"
    ]["samples"]["<sample_id>"]
    if type(leaving_group) is not dict:
        raise ValueError(overlay.ERROR)
    records = leaving_group.get("leaving_group_records")
    if (
        tuple(leaving_group) != ("status", "leaving_group_records")
        or leaving_group["status"] != "<explicitly_attested or not_claimed>"
        or type(records) is not list
        or len(records) != 1
        or type(records[0]) is not dict
        or tuple(records[0]) != ("leaving_atom_map_numbers", "broken_edge")
        or type(records[0]["broken_edge"]) is not dict
        or tuple(records[0]["broken_edge"])
        != ("map_number_1", "map_number_2", "pre_bond_order")
    ):
        raise ValueError(overlay.ERROR)

    protonation = value[
        "reviewed_protonation_transfer_contract_json"
    ]["samples"]["<sample_id>"]
    if (
        type(protonation) is not dict
        or protonation.get("status") != "<explicitly_attested or not_claimed>"
        or "explicitly_attested" not in leaving_group["status"]
        or "not_claimed" not in leaving_group["status"]
    ):
        raise ValueError(overlay.ERROR)


def _state_path(state_root: Path, namespace: str, source_path: str) -> Path:
    if namespace == "sha_bound_formal_state" and source_path.startswith("state://"):
        return state_root / source_path[len("state://"):]
    if namespace == "non_authoritative_state_aid" and source_path.startswith("state-aid://"):
        return state_root / source_path[len("state-aid://"):]
    raise ValueError(overlay.ERROR)


def _check_files(repo_root: Path) -> dict[str, dict[str, object]]:
    records = {}
    for relative in overlay.CANDIDATE_PATHS:
        path = repo_root / relative
        metadata = path.lstat()
        payload = path.read_bytes()
        if (
            not stat.S_ISREG(metadata.st_mode)
            or path.is_symlink()
            or stat.S_IMODE(metadata.st_mode) != 0o644
            or not payload
            or len(payload) >= 1024 * 1024
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\x00" in payload
        ):
            raise ValueError(overlay.ERROR)
        records[relative] = {
            "bytes": len(payload),
            "lines": len(payload.splitlines()),
            "mode": "0644",
            "sha256": _sha256(payload),
        }
    return records


def _check_source_inventory(repo_root: Path, state_root: Path) -> int:
    payload = (repo_root / overlay.SOURCE_INVENTORY_PATH).read_bytes()
    fields, rows = _csv(payload)
    if fields != overlay.SOURCE_INVENTORY_COLUMNS or len(rows) != len(overlay.SOURCE_EVIDENCE):
        raise ValueError(overlay.ERROR)
    if [row["evidence_id"] for row in rows] != [source.evidence_id for source in overlay.SOURCE_EVIDENCE]:
        raise ValueError(overlay.ERROR)
    post_authority_count = 0
    for row in rows:
        if row["source_namespace"] == "git_object":
            source_payload = _git(
                repo_root,
                "show",
                f'{row["source_commit_or_direct_producer"]}:{row["source_path"]}',
            )
        else:
            source = _state_path(
                state_root, row["source_namespace"], row["source_path"]
            )
            metadata = source.lstat()
            if not stat.S_ISREG(metadata.st_mode) or source.is_symlink():
                raise ValueError(overlay.ERROR)
            source_payload = source.read_bytes()
        if (
            _sha256(source_payload) != row["source_sha256"]
            or row["authority_scope"] not in overlay.AUTHORITY_SCOPES
            or row["authoritative_for_transformation"] != "false"
            or row["verified"] != "true"
        ):
            raise ValueError(overlay.ERROR)
        post_authority_count += (
            row["authority_scope"] == "formal_post_reaction_transformation_authority"
        )
    dossier_rows = [row for row in rows if row["source_namespace"] == "non_authoritative_state_aid"]
    if (
        len(dossier_rows) != 6
        or any(row["authority_scope"] != "non_authoritative_review_aid" for row in dossier_rows)
        or any(row["lineage_note"] != "non_authoritative_human_review_aid_crosscheck" for row in dossier_rows)
    ):
        raise ValueError(overlay.ERROR)
    return post_authority_count


def _check_schema(repo_root: Path) -> dict[str, int]:
    field_fields, fields = _csv((repo_root / overlay.FIELD_CONTRACT_PATH).read_bytes())
    gap_fields, gaps = _csv((repo_root / overlay.GAP_MATRIX_PATH).read_bytes())
    failure_fields, failures = _csv((repo_root / overlay.FAILURE_MATRIX_PATH).read_bytes())
    manifest = json.loads((repo_root / overlay.MANIFEST_PATH).read_bytes())
    leaving_group_fields = [
        row for row in fields
        if row["field_name"] == "reviewed_leaving_group_contract_json"
    ]
    if (
        field_fields != overlay.FIELD_CONTRACT_COLUMNS
        or gap_fields != overlay.GAP_MATRIX_COLUMNS
        or failure_fields != overlay.FAILURE_MATRIX_COLUMNS
        or len(fields) != 41
        or [row["field_name"] for row in fields] != list(overlay.ALL_FIELDS)
        or [row["field_order_0based"] for row in fields] != [str(i) for i in range(41)]
        or any(row["field_scope"] not in overlay.FIELD_SCOPES for row in fields)
        or any(row["initial_value"] or row["prefilled"] != "false" for row in fields[16:])
        or len(leaving_group_fields) != 1
        or leaving_group_fields[0]["initial_value"] != ""
        or leaving_group_fields[0]["prefilled"] != "false"
        or len(gaps) != 2
        or [row["sample_index_row_id"] for row in gaps] != list(overlay.SAMPLE_IDS)
        or any(row["ligand_reactive_atom_id"] != "C21" for row in gaps)
        or any(row["target_residue_atom"] != "CYS:SG" for row in gaps)
        or any(row["pre_reaction_center_bond_order_sum"] != "4" for row in gaps)
        or any(row["conditional_post_bond_order_sum_if_internal_bonds_unchanged"] != "5" for row in gaps)
        or any(row["effective_boundary_cardinality"] != "2" for row in gaps)
        or any(row["post_reaction_graph_authority"] != "missing" for row in gaps)
        or len(failures) != 28
        or [row["case_id"] for row in failures] != [f"X{i:02d}" for i in range(1, 29)]
        or manifest["field_contract_row_count"] != 41
        or manifest["failure_case_count"] != 28
        or manifest["formal_post_reaction_authority_count"] != 0
        or manifest["candidate_valence_ledger_is_gap_signal_only"] is not True
        or manifest["candidate_valence_ledger_is_reaction_authority"] is not False
        or manifest["approved_smarts_generated"] is not False
        or manifest["approval_decision_generated"] is not False
        or manifest["formal_worklist_modified"] is not False
        or manifest["authority_changed"] is not False
        or manifest["feature_semantics_reaudit_required_before_training"] is not True
        or manifest["ready_for_training"] is not False
        or set(manifest["evidence_sha256"]) != {
            Path(path).name for path in overlay.ARTIFACT_PATHS[:-1]
        }
        or "covapie_reaction_transformation_overlay_manifest.json" in manifest["evidence_sha256"]
    ):
        raise ValueError(overlay.ERROR)
    for relative in overlay.ARTIFACT_PATHS[:-1]:
        if manifest["evidence_sha256"][Path(relative).name] != _sha256(
            (repo_root / relative).read_bytes()
        ):
            raise ValueError(overlay.ERROR)
    return {
        "field_count": len(fields),
        "frozen_field_count": sum(row["frozen"] == "true" for row in fields),
        "future_field_count": sum(row["human_or_authority_fillable"] == "true" for row in fields),
        "gap_count": len(gaps),
        "failure_count": len(failures),
    }


def _git_source(repo_root: Path, evidence_id: str) -> bytes:
    matches = [source for source in overlay.SOURCE_EVIDENCE if source.evidence_id == evidence_id]
    if len(matches) != 1 or matches[0].namespace != "git_object":
        raise ValueError(overlay.ERROR)
    source = matches[0]
    return _git(repo_root, "show", f"{source.producer}:{source.path}")


def _check_frozen_state(repo_root: Path, state_root: Path) -> dict[str, object]:
    canonical = state_root / "manual-review" / overlay.WORKSPACE_NAME
    object_directory = canonical.parent / overlay.WORKSPACE_TARGET
    canonical_meta = canonical.lstat()
    object_meta = object_directory.lstat()
    workspace_entries = tuple(sorted(object_directory.iterdir(), key=lambda path: path.name))
    if (
        not stat.S_ISLNK(canonical_meta.st_mode)
        or str(canonical.readlink()) != overlay.WORKSPACE_TARGET
        or (canonical_meta.st_dev, canonical_meta.st_ino)
        != (
            overlay.WORKSPACE_IDENTITY["canonical_st_dev"],
            overlay.WORKSPACE_IDENTITY["canonical_st_ino"],
        )
        or not stat.S_ISDIR(object_meta.st_mode)
        or object_directory.is_symlink()
        or (object_meta.st_dev, object_meta.st_ino)
        != (
            overlay.WORKSPACE_IDENTITY["object_st_dev"],
            overlay.WORKSPACE_IDENTITY["object_st_ino"],
        )
        or stat.S_IMODE(object_meta.st_mode) != 0o755
        or tuple(path.name for path in workspace_entries)
        != tuple(sorted(overlay.WORKSPACE_SHA256))
        or any(
            _sha256(path.read_bytes()) != overlay.WORKSPACE_SHA256[path.name]
            for path in workspace_entries
        )
    ):
        raise ValueError(overlay.ERROR)
    _worklist_fields, worklist = _csv(
        (object_directory / "family_rule_approval_worklist.csv").read_bytes()
    )
    units = [row for row in worklist if row["review_unit_id"] == overlay.PARENT_REVIEW_UNIT_ID]
    if (
        len(worklist) != 7
        or len(units) != 1
        or any(row[field] for row in worklist for field in overlay.HISTORICAL_HUMAN_FIELDS)
        or units[0]["reaction_family_id"] != overlay.REACTION_FAMILY_ID
        or units[0]["warhead_rule_id"] != overlay.WARHEAD_RULE_ID
        or units[0]["candidate_local_graph_rule_sha256"]
        != overlay.CANDIDATE_LOCAL_GRAPH_SHA256
    ):
        raise ValueError(overlay.ERROR)

    dossier = state_root / overlay.DOSSIER_RELATIVE
    dossier_meta = dossier.lstat()
    dossier_entries = tuple(sorted(dossier.iterdir(), key=lambda path: path.name))
    if (
        not stat.S_ISDIR(dossier_meta.st_mode)
        or dossier.is_symlink()
        or (dossier_meta.st_dev, dossier_meta.st_ino)
        != (overlay.DOSSIER_IDENTITY["st_dev"], overlay.DOSSIER_IDENTITY["st_ino"])
        or stat.S_IMODE(dossier_meta.st_mode) != 0o755
        or tuple(path.name for path in dossier_entries)
        != tuple(sorted(overlay.DOSSIER_SHA256))
        or any(
            _sha256(path.read_bytes()) != overlay.DOSSIER_SHA256[path.name]
            for path in dossier_entries
        )
    ):
        raise ValueError(overlay.ERROR)
    questionnaire = (dossier / "human_review_questionnaire.md").read_text(encoding="utf-8").splitlines()
    if any(questionnaire.count(f"{field}:") != 1 for field in overlay.HISTORICAL_HUMAN_FIELDS):
        raise ValueError(overlay.ERROR)

    _assignment_fields, assignments = _csv(_git_source(repo_root, "A01"))
    selected = [row for row in assignments if row["sample_index_row_id"] in overlay.SAMPLE_IDS]
    if (
        [row["sample_index_row_id"] for row in selected] != list(overlay.SAMPLE_IDS)
        or any(row["ligand_reactive_atom_name"] != "C21" for row in selected)
        or any(row["target_residue_name"] != "CYS" for row in selected)
        or any(row["target_residue_atom_name"] != "SG" for row in selected)
    ):
        raise ValueError(overlay.ERROR)

    _rule_fields, rules = _csv(_git_source(repo_root, "G01"))
    selected_rules = [row for row in rules if row["warhead_rule_id"] == overlay.WARHEAD_RULE_ID]
    if len(selected_rules) != 1:
        raise ValueError(overlay.ERROR)
    graph = json.loads(selected_rules[0]["canonical_local_graph_rule_json"])
    order = {"single": 1, "double": 2, "triple": 3, "aromatic": 1.5}
    pre_sum = sum(order[bond["normalized_bond_order"]] for bond in graph["local_bonds"])
    if (
        pre_sum != 4
        or selected_rules[0]["formed_bond_order"] != "single"
        or selected_rules[0]["canonical_local_graph_rule_sha256"]
        != overlay.CANDIDATE_LOCAL_GRAPH_SHA256
        or selected_rules[0]["approved_warhead_smarts"] != ""
    ):
        raise ValueError(overlay.ERROR)

    _pair_fields, pairs = _csv(_git_source(repo_root, "C02"))
    selected_pairs = [row for row in pairs if row["sample_index_row_id"] in overlay.SAMPLE_IDS]
    if (
        len(selected_pairs) != 2
        or any(row["residue_comp_id"] != "CYS" for row in selected_pairs)
        or any(row["residue_atom_name"] != "SG" for row in selected_pairs)
        or any(row["ligand_atom_name"] != "C21" for row in selected_pairs)
        or any(row["canonical_record_valid"] != "true" for row in selected_pairs)
    ):
        raise ValueError(overlay.ERROR)

    unified = json.loads(
        (state_root / "manual-review/covapie_current11_unified_effective_authority_view_v1.json").read_bytes()
    )
    boundaries = [
        row for row in unified["effective_authority_records"]
        if row["sample_index_row_id"] in overlay.SAMPLE_IDS
    ]
    if (
        len(boundaries) != 2
        or any(row["effective_boundary_cardinality"] != 2 for row in boundaries)
        or any(
            len(row["effective_authority_record"]["reviewed_boundary_records"]) != 2
            for row in boundaries
        )
    ):
        raise ValueError(overlay.ERROR)
    return {
        "workspace_canonical_inode": canonical_meta.st_ino,
        "workspace_object_inode": object_meta.st_ino,
        "dossier_inode": dossier_meta.st_ino,
        "human_cell_count": len(worklist) * len(overlay.HISTORICAL_HUMAN_FIELDS),
        "human_nonblank_count": 0,
        "pre_reaction_center_bond_order_sum": int(pre_sum),
        "conditional_post_bond_order_sum_if_internal_bonds_unchanged": int(pre_sum) + 1,
    }


def _check_safety(repo_root: Path) -> None:
    protected = (
        "equivariant_diffusion",
        "lightning_modules.py",
        "dataset.py",
        "data/prepare_crossdocked.py",
    )
    changed = set(_git(repo_root, "diff", "--name-only").decode("utf-8").splitlines())
    staged = set(_git(repo_root, "diff", "--cached", "--name-only").decode("utf-8").splitlines())
    if any(path == prefix or path.startswith(prefix + "/") for path in changed | staged for prefix in protected):
        raise ValueError(overlay.ERROR)
    forbidden = (".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip", ".tgz", ".npz", ".tmp", ".part")
    ordinary_untracked = _git(
        repo_root, "ls-files", "--others", "--exclude-standard"
    ).decode("utf-8").splitlines()
    if any(path.endswith(forbidden) or path.startswith("data/raw/") for path in ordinary_untracked):
        raise ValueError(overlay.ERROR)


def check(repo_root: Path, state_root: Path) -> dict[str, object]:
    repository = repo_root.resolve(strict=True)
    state = state_root.resolve(strict=True)
    _check_structured_schema_contract()
    files = _check_files(repository)
    post_authority_count = _check_source_inventory(repository, state)
    counts = _check_schema(repository)
    frozen = _check_frozen_state(repository, state)
    _check_safety(repository)
    response = overlay.evaluate_covapie_current11_reaction_transformation_evidence_overlay_contract_v1(
        repo_root=repository,
        state_root=state,
    )
    if post_authority_count != 0 or response["formal_post_reaction_authority_count"] != 0:
        raise ValueError(overlay.ERROR)
    return {
        "checker_version": overlay.SCHEMA_VERSION,
        "base_commit": overlay.BASE_COMMIT,
        "parent_review_unit_id": overlay.PARENT_REVIEW_UNIT_ID,
        "transformation_review_unit_id": overlay.TRANSFORMATION_REVIEW_UNIT_ID,
        "sample_count": 2,
        **counts,
        "source_inventory_row_count": len(overlay.SOURCE_EVIDENCE),
        **frozen,
        "formal_post_reaction_authority_count": 0,
        "candidate_valence_ledger_is_gap_signal_only": True,
        "candidate_valence_ledger_is_reaction_authority": False,
        "approved_smarts_generated": False,
        "approval_decision_generated": False,
        "formal_worklist_modified": False,
        "authority_changed": False,
        "feature_semantics_reaudit_required_before_training": True,
        "ready_for_training": False,
        "lifecycle_profile": response["lifecycle_profile"],
        "artifact_sha256": response["artifact_sha256"],
        "response_sha256": response["response_sha256"],
        "candidate_file_sha256": {
            path: record["sha256"] for path, record in files.items()
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--state-root", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = check(args.repo_root, args.state_root)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(report, sort_keys=True, ensure_ascii=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
