"""Fail-closed Current11 remap state mount-device transition contract V1."""

from __future__ import annotations

import ast
import csv
import hashlib
import io
import json
import os
import re
import stat
import subprocess
from pathlib import Path
from typing import Mapping, NoReturn, Sequence


__all__ = (
    "build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1",
)

ERROR_TOKEN = (
    "COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_STATE_MOUNT_DEVICE_"
    "TRANSITION_CONTRACT_GATE_V1_ERROR"
)
BASE_COMMIT = "83beddbcd468caeb38a6b8a86c15f31dfd430d79"
BRANCH = "main"
HISTORICAL_DEVICE = 49
AUTHORIZED_CURRENT_DEVICE = 50
HISTORICAL_MAJOR_MINOR = "0:49"
CURRENT_MAJOR_MINOR = "0:50"

MODULE_PATH = (
    "src/covalent_ext/covapie_current11_task2_batch_index_remap_state_mount_"
    "device_transition_contract_gate_v1.py"
)
SCRIPT_PATH = (
    "scripts/check_covapie_current11_task2_batch_index_remap_state_mount_"
    "device_transition_contract_gate_v1.py"
)
TEST_PATH = (
    "tests/test_covapie_current11_task2_batch_index_remap_state_mount_device_"
    "transition_contract_gate_v1.py"
)
GUIDE_PATH = (
    "docs/covapie_current11_task2_batch_index_remap_state_mount_device_"
    "transition_contract_gate_v1_guide.md"
)
REPOSITORY_EXACT4 = (MODULE_PATH, SCRIPT_PATH, TEST_PATH, GUIDE_PATH)

ARTIFACT_NAMES = (
    "current11_task2_batch_index_remap_state_mount_device_transition_contract_manifest.json",
    "current11_task2_batch_index_remap_state_mount_device_transition_objects.json",
    "current11_task2_batch_index_remap_state_mount_device_transition_lineage_evidence.json",
    "current11_task2_batch_index_remap_state_mount_device_transition_negative_matrix.json",
    "current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_report.json",
)
STABLE_ARTIFACT_NAMES = ARTIFACT_NAMES[:4]
CONTRACT_DIGEST_DOMAIN = (
    b"COVAPIE_CURRENT11_TASK2_BATCH_INDEX_REMAP_STATE_MOUNT_DEVICE_"
    b"TRANSITION_CONTRACT_GATE_V1\0"
)

PRECONDITION_RELATIVE = (
    "review-scratch/current11-state-mount-device-identity-transition-"
    "precondition-v1/state_mount_device_identity_transition_precondition_report.md"
)
PRECONDITION_SPEC = {
    "bytes": 31396,
    "LF": 619,
    "sha256": "ea4583db1101cf19b78e10ad7c28a99f330d140150c2362231f312c21b2cf345",
    "mode": "0644",
}

DOSSIER_RELATIVE = (
    "manual-review-aids/current11-reaction-transformation-review-v1/"
    "CURRENT11_REACTION_TRANSFORMATION_REVIEW_UNIT_000001"
)
ROUTING_CANONICAL_RELATIVE = (
    "formal-sidecars/current11-dataset-partial-supervision-routing-sidecar-v1"
)
ROUTING_READLINK = (
    ".current11-dataset-partial-supervision-routing-sidecar-v2.object-sha256-"
    "24f95099ba1ba0b81724535cb17c5d4d32c360f71c87422571210a2178ddb49c-"
    "1fd8cf5823427e941b11c7b2560a336f"
)
ROUTING_OBJECT_RELATIVE = f"formal-sidecars/{ROUTING_READLINK}"

TRANSITION_OBJECT_IDS = (
    "unit_000001_dossier",
    "routing_canonical",
    "routing_object",
)
DOSSIER_INODE = 196008339793
ROUTING_CANONICAL_INODE = 69442074366
ROUTING_OBJECT_INODE = 69442074217

DOSSIER_LEAVES = {
    "README.md": (990, 17, "99fa7532e4f8d3545caa6d3907e0df3338eac464426fe7f109dd6d6f0f476610"),
    "candidate_local_graph.svg": (5440, 53, "2daad45b6d2b1b35bdfb38ddfc1f5cb38cdf58eabbe31c591273714a6dafdc96"),
    "dossier_manifest.json": (5669, 109, "96e19c2d01ec1edc517e1090d73c4b21d5d6a5dcd79ca6dbeff7defcffb14202"),
    "frozen_transformation_review_summary.json": (1710, 40, "0ec37a92bdc947e771dfe0804a1d15d26fde32ba725d95661b4db228c5cc513a"),
    "human_transformation_evidence_questionnaire.md": (9112, 256, "cc30376d7315575f9f24f2e71accb5ae3adcabc0e96c354c52e7eef2dfd75b57"),
    "sample_transformation_gap_evidence.csv": (2415, 3, "599c75f0f97896c0eea73dbde5041a446f23cb5d30e7da36c186a908561e1134"),
    "source_authority_inventory_snapshot.csv": (13357, 36, "fb638a9573cfba0561879b8f8b030c453bd5b3fe693c983eb6fa65f1b7cc4e28"),
    "structured_json_schema_templates.json": (2847, 110, "ddde07b4b28ee45163d0cb09a9e08ea8712c255a20b1b7fd72dbb7da110f07c6"),
}
ROUTING_LEAVES = {
    "current11_dataset_partial_supervision_routing_records.csv": (
        69557,
        276,
        "751e32f46ab386604386167bdffd38f762472bbc9fdff4af7167a979ac68af03",
    ),
    "current11_dataset_partial_supervision_task_coverage.csv": (
        1883,
        26,
        "ee8bfe7f0bed65e6858ae318695470abc3a92de3ca72d2548e2d5c4e950aa2b7",
    ),
    "current11_dataset_partial_supervision_sample_coverage.csv": (
        1445,
        12,
        "7cd2ecd99caca09f94019d543793f70de6d9cb86ff431fbd49782b76b2814b5e",
    ),
    "current11_dataset_partial_supervision_routing_manifest.json": (
        43109,
        1044,
        "3a2c2e8170f20ed0a8ea97798a5945ec846cd36d81fe950aa58fee6311984a7d",
    ),
}
ROUTING_AGGREGATE_DOMAIN = (
    b"COVAPIE_CURRENT11_DATASET_PARTIAL_SUPERVISION_ROUTING_SIDECAR_"
    b"GPFS_ATOMIC_ALIAS_V2\0"
)
ROUTING_AGGREGATE = (
    "24f95099ba1ba0b81724535cb17c5d4d32c360f71c87422571210a2178ddb49c"
)

MOUNT_FSTYPE = "gpfs"
MOUNT_SOURCE = "cpfs01"
MOUNT_ROOT = "/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037"
MOUNT_TARGET = "/cpfs01/projects-HDD/cfff-7a25f11bdb65_HDD/fmx_25111030037"

SAMPLE_ORDER = (
    ("CYS_SG_SAMPLE_INDEX_000001", "6BV6", "JUG"),
    ("CYS_SG_SAMPLE_INDEX_000002", "6BV8", "JUG"),
    ("CYS_SG_SAMPLE_INDEX_000003", "6BV5", "JUG"),
    ("CYS_SG_SAMPLE_INDEX_000004", "1AEC", "E64"),
    ("CYS_SG_SAMPLE_INDEX_000005", "1AIM", "ZYA"),
    ("CYS_SG_SAMPLE_INDEX_000006", "1AU3", "PCM"),
    ("CYS_SG_SAMPLE_INDEX_000007", "1AU4", "INP"),
    ("CYS_SG_SAMPLE_INDEX_000008", "1AYU", "INA"),
    ("CYS_SG_SAMPLE_INDEX_000009", "1AYV", "IN6"),
    ("CYS_SG_SAMPLE_INDEX_000010", "1AYW", "IN3"),
    ("CYS_SG_SAMPLE_INDEX_000011", "1B02", "UFP"),
)
TASK_ORDER = (
    "sample_identity_supervision",
    "explicit_covalent_event_supervision",
    "ligand_residue_atom_pair_supervision",
    "covalent_link_bond_order_supervision",
    "warhead_type_supervision",
    "reaction_family_supervision",
    "warhead_boundary_supervision",
    "canonical_mask_warhead_only",
    "canonical_mask_linker_plus_warhead",
    "canonical_mask_scaffold_plus_warhead",
    "canonical_mask_scaffold_only",
    "canonical_mask_scaffold_plus_linker_plus_warhead",
    "observed_complex_geometry_supervision",
    "pre_covalent_geometry_supervision",
    "post_covalent_geometry_supervision",
    "complete_post_state_graph_supervision",
    "reaction_atom_map_supervision",
    "formed_edge_supervision",
    "broken_edge_supervision",
    "bond_order_delta_supervision",
    "formal_charge_delta_supervision",
    "protonation_transfer_supervision",
    "leaving_group_supervision",
    "reversibility_supervision",
    "full_transformation_supervision",
)
CANONICAL_MASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
ROUTING_RECORD_COLUMNS = (
    "sample_index_row_id",
    "pdb_id",
    "ligand_comp_id",
    "semantic_task_name",
    "eligibility_state",
    "direct_authority_found",
    "evidence_scope",
    "blocking_reason_code",
    "supporting_source_ids_json",
    "dedicated_transformation_review_available",
    "availability_mask_required",
    "current_runtime_consumer_available",
    "training_loss_authorized",
)

UNIT_INTRODUCTION_COMMIT = "05a86e7f293d75a2e890850208ee49b9d1c821f6"
PROJECTION_INTRODUCTION_COMMIT = "df9aa9d0b2a91df577b4182e0afdcf4cdfc3bbce"
UNIT_MODULE = (
    "src/covalent_ext/covapie_current11_unit_000001_partial_supervision_"
    "routing_gate_v1.py"
)
PROJECTION_MODULE = (
    "src/covalent_ext/covapie_current11_dataset_routing_sidecar_tensor_"
    "projection_contract_gate_v1.py"
)
HISTORICAL_GROUPS = (
    {
        "lineage_id": "unit_000001_partial_supervision_routing_gate_v1",
        "introduction_commit": UNIT_INTRODUCTION_COMMIT,
        "introduction_parent": "74afd2c5c8465550eff77b88afe85dd57835d143",
        "introduction_subject": "add CovaPIE Current11 partial supervision routing gate v1",
        "module_path": UNIT_MODULE,
        "identity_constants": {"DOSSIER_IDENTITY": [49, DOSSIER_INODE]},
        "paths": (
            UNIT_MODULE,
            "scripts/check_covapie_current11_unit_000001_partial_supervision_routing_gate_v1.py",
            "tests/test_covapie_current11_unit_000001_partial_supervision_routing_gate_v1.py",
            "docs/covapie_current11_unit_000001_partial_supervision_routing_gate_v1_guide.md",
        ),
    },
    {
        "lineage_id": "dataset_routing_sidecar_tensor_projection_contract_gate_v1",
        "introduction_commit": PROJECTION_INTRODUCTION_COMMIT,
        "introduction_parent": "2c9af439780a78c2fcbb10f5fe0d629bd1a57847",
        "introduction_subject": "add CovaPIE Current11 routing tensor projection contract gate v1",
        "module_path": PROJECTION_MODULE,
        "identity_constants": {
            "CANONICAL_IDENTITY": [49, ROUTING_CANONICAL_INODE],
            "OBJECT_IDENTITY": [49, ROUTING_OBJECT_INODE],
        },
        "paths": (
            PROJECTION_MODULE,
            "scripts/check_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1.py",
            "tests/test_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1.py",
            "docs/covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1_guide.md",
        ),
    },
)
HISTORICAL_FILE_SPECS = {
    UNIT_MODULE: (56661, 1221, "30750f6996f4c203690261df33995b0cf3baaf2c7c8684999faea325f2171759", "a87f0d7cacbbea4ead3ddc2c91a8e41f19085539"),
    "scripts/check_covapie_current11_unit_000001_partial_supervision_routing_gate_v1.py": (1667, 61, "86c0dbeb933108d6fda3277f2d06d6094e1b92b9f921f58b2009a799d3fa64c4", "c613ce498873fa04b6031138ab105f75edc537de"),
    "tests/test_covapie_current11_unit_000001_partial_supervision_routing_gate_v1.py": (30193, 746, "e94183ec2f1d50a76f601d26b5a10ab8d59e7ec4d1140bca6963c6709d90119f", "2c2508347771c444ef23a200245022c10e347585"),
    "docs/covapie_current11_unit_000001_partial_supervision_routing_gate_v1_guide.md": (5461, 116, "9d5cd21d1b8869b5fa245268a502cdc4bf2731968978249aa0febcde515842fb", "848571026da69183704a940aacd2fbf43e8c07c8"),
    PROJECTION_MODULE: (71459, 1372, "d46ebaf163abf862aadb35301efa649eac6dc799da434e29f58f95deae2cbe0f", "9152aa5e850394bfaab62264ecffce4a8c0848b1"),
    "scripts/check_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1.py": (1763, 61, "49b631d4c95c779a12863635c72e59a6377cf0c4005e942d1d0f40da6b4f2800", "11d7a08ba5be447452c8c23e4626d8a20ab4f170"),
    "tests/test_covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1.py": (30812, 718, "8bc2a7088c883c299f9d6049ee5b6741682fa88e12c4c93206998f2b2fca6dc8", "a145bc389ec1a249ade49959274afdb303cbaa16"),
    "docs/covapie_current11_dataset_routing_sidecar_tensor_projection_contract_gate_v1_guide.md": (4333, 40, "1aee65ba6deb4ed309da11e648e37ec4bcbd42f1691f78a6ec989e699b7f7ea6", "5041910299a675d4927dc8bdf70f21b11bd9a6c5"),
}

NEGATIVE_CASE_IDS = (
    "wrong_historical_dossier_dev",
    "wrong_current_dossier_dev",
    "dossier_inode_drift",
    "dossier_path_drift",
    "dossier_type_or_mode_drift",
    "dossier_child_missing",
    "dossier_child_extra",
    "dossier_leaf_size_or_sha256_drift",
    "wrong_historical_canonical_dev",
    "wrong_current_canonical_dev",
    "canonical_inode_drift",
    "canonical_readlink_drift",
    "wrong_object_historical_or_current_dev",
    "object_inode_drift",
    "routing_object_child_missing_or_extra",
    "routing_leaf_size_sha256_or_aggregate_drift",
    "mount_source_fstype_root_target_or_current_major_minor_drift",
    "transition_object_omitted_extra_or_reordered",
    "precondition_report_drift",
    "historical_gate_source_identity_drift",
    "semantic_manifest_drift",
    "current_dev_49_is_not_transition_pass",
    "current_dev_51_rejected",
    "wildcard_or_allow_list_semantics_forbidden",
)

_PATH_TYPE = type(Path())
_MOUNT_ESCAPE = re.compile(r"\\([0-7]{3})")


def _fail() -> NoReturn:
    raise ValueError(ERROR_TOKEN)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _lstat(path: Path) -> os.stat_result:
    return path.lstat()


def _read_bytes(path: Path) -> bytes:
    return path.read_bytes()


def _listdir(path: Path) -> tuple[str, ...]:
    return tuple(sorted(os.listdir(path)))


def _readlink(path: Path) -> str:
    return os.readlink(path)


def _mountinfo_bytes() -> bytes:
    return Path("/proc/self/mountinfo").read_bytes()


def _canonical_json(value: object) -> bytes:
    try:
        text = json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise ValueError(ERROR_TOKEN) from error
    return (text + "\n").encode("utf-8")


def _strict_json(payload: bytes) -> object:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(ERROR_TOKEN) from error
    if _canonical_json(value) != payload:
        _fail()
    return value


def _require_root(path: Path) -> Path:
    if type(path) is not _PATH_TYPE or not path.is_absolute():
        _fail()
    try:
        metadata = path.lstat()
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ValueError(ERROR_TOKEN) from error
    if (
        resolved != path
        or stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
    ):
        _fail()
    return path


def _run_git(repo_root: Path, arguments: Sequence[str]) -> str:
    try:
        completed = subprocess.run(
            ("git", *arguments),
            cwd=repo_root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="strict",
            check=False,
        )
    except (OSError, UnicodeError) as error:
        raise ValueError(ERROR_TOKEN) from error
    if completed.returncode != 0 or completed.stderr:
        _fail()
    return completed.stdout


def _validate_repository_lineage(repo_root: Path) -> None:
    if _run_git(repo_root, ("branch", "--show-current")).strip() != BRANCH:
        _fail()
    _run_git(repo_root, ("cat-file", "-e", f"{BASE_COMMIT}^{{commit}}"))
    _run_git(repo_root, ("merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"))


def _safe_candidate_files(repo_root: Path) -> None:
    for relative in REPOSITORY_EXACT4:
        path = repo_root / relative
        try:
            metadata = path.lstat()
            payload = path.read_bytes()
        except OSError as error:
            raise ValueError(ERROR_TOKEN) from error
        if (
            stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o644
            or not payload
            or len(payload) >= 1024 * 1024
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\0" in payload
            or b"\r" in payload
            or not payload.endswith(b"\n")
            or payload.endswith(b"\n\n")
            or any(
                line.rstrip(b"\r\n").endswith((b" ", b"\t"))
                for line in payload.splitlines(keepends=True)
            )
        ):
            _fail()
        try:
            payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(ERROR_TOKEN) from error


def _repository_lifecycle(repo_root: Path) -> str:
    status = _run_git(
        repo_root, ("status", "--porcelain=v1", "--untracked-files=all")
    ).splitlines()
    index = _run_git(
        repo_root, ("ls-files", "--stage", "--", *REPOSITORY_EXACT4)
    ).splitlines()
    expected = {f"?? {relative}" for relative in REPOSITORY_EXACT4}
    if set(status) == expected and len(status) == len(REPOSITORY_EXACT4):
        if index:
            _fail()
        _safe_candidate_files(repo_root)
        return "precommit-untracked"
    if status or len(index) != len(REPOSITORY_EXACT4):
        _fail()
    seen: set[str] = set()
    for row in index:
        try:
            metadata, relative = row.split("\t", 1)
            mode, blob, stage = metadata.split()
        except ValueError as error:
            raise ValueError(ERROR_TOKEN) from error
        if (
            relative not in REPOSITORY_EXACT4
            or relative in seen
            or mode != "100644"
            or stage != "0"
            or _run_git(
                repo_root, ("hash-object", "--no-filters", "--", relative)
            ).strip()
            != blob
            or _run_git(repo_root, ("rev-parse", f"HEAD:{relative}")).strip()
            != blob
        ):
            _fail()
        seen.add(relative)
    if seen != set(REPOSITORY_EXACT4):
        _fail()
    _safe_candidate_files(repo_root)
    return "clean-tracked-successor"


def _assignment_literals(payload: bytes, names: Mapping[str, list[int]]) -> None:
    try:
        tree = ast.parse(payload.decode("utf-8"))
    except (UnicodeDecodeError, SyntaxError) as error:
        raise ValueError(ERROR_TOKEN) from error
    observed: dict[str, object] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id in names:
            try:
                observed[target.id] = ast.literal_eval(node.value)
            except (ValueError, TypeError) as error:
                raise ValueError(ERROR_TOKEN) from error
    if observed != {name: tuple(value) for name, value in names.items()}:
        _fail()


def _verify_historical_repository_lineage(repo_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    payloads: dict[str, bytes] = {}
    for relative, (size, lines, digest, blob) in HISTORICAL_FILE_SPECS.items():
        path = repo_root / relative
        try:
            metadata = _lstat(path)
            payload = _read_bytes(path)
        except OSError as error:
            raise ValueError(ERROR_TOKEN) from error
        tree_row = _run_git(repo_root, ("ls-tree", "HEAD", "--", relative)).strip()
        try:
            tree_metadata, listed = tree_row.split("\t", 1)
            tree_mode, tree_kind, tree_blob = tree_metadata.split()
        except ValueError as error:
            raise ValueError(ERROR_TOKEN) from error
        if (
            listed != relative
            or tree_mode != "100644"
            or tree_kind != "blob"
            or tree_blob != blob
            or stat.S_ISLNK(metadata.st_mode)
            or not stat.S_ISREG(metadata.st_mode)
            or stat.S_IMODE(metadata.st_mode) != 0o644
            or len(payload) != size
            or payload.count(b"\n") != lines
            or _sha256(payload) != digest
            or _run_git(
                repo_root, ("hash-object", "--no-filters", "--", relative)
            ).strip()
            != blob
        ):
            _fail()
        payloads[relative] = payload
        rows.append(
            {
                "path": relative,
                "bytes": size,
                "LF": lines,
                "sha256": digest,
                "git_blob": blob,
                "git_mode": "100644",
                "head_and_worktree_exact": True,
            }
        )
    for group in HISTORICAL_GROUPS:
        commit = str(group["introduction_commit"])
        _run_git(repo_root, ("cat-file", "-e", f"{commit}^{{commit}}"))
        _run_git(repo_root, ("merge-base", "--is-ancestor", commit, "HEAD"))
        if (
            _run_git(repo_root, ("show", "-s", "--format=%P", commit)).strip()
            != group["introduction_parent"]
            or _run_git(
                repo_root, ("show", "-s", "--format=%s", commit)
            ).strip()
            != group["introduction_subject"]
        ):
            _fail()
        statuses: dict[str, str] = {}
        for line in _run_git(
            repo_root,
            ("diff-tree", "--no-commit-id", "--name-status", "-r", commit),
        ).splitlines():
            parts = line.split("\t")
            if len(parts) == 2 and parts[1] in group["paths"]:
                statuses[parts[1]] = parts[0]
        if statuses != {path: "A" for path in group["paths"]}:
            _fail()
        introduction_payload = _run_git(
            repo_root, ("show", f"{commit}:{group['module_path']}")
        ).encode("utf-8")
        _assignment_literals(introduction_payload, group["identity_constants"])
        _assignment_literals(payloads[str(group["module_path"])], group["identity_constants"])
    return rows


def _read_regular_exact(
    path: Path, expected: tuple[int, int, str]
) -> tuple[bytes, dict[str, object]]:
    try:
        metadata = _lstat(path)
        payload = _read_bytes(path)
    except OSError as error:
        raise ValueError(ERROR_TOKEN) from error
    size, lines, digest = expected
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != 0o644
        or len(payload) != size
        or payload.count(b"\n") != lines
        or _sha256(payload) != digest
    ):
        _fail()
    return payload, {
        "name": path.name,
        "bytes": size,
        "LF": lines,
        "sha256": digest,
        "mode": "0644",
        "kind": "regular_file",
        "non_symlink": True,
    }


def _verify_precondition_report(state_root: Path) -> dict[str, object]:
    payload, identity = _read_regular_exact(
        state_root / PRECONDITION_RELATIVE,
        (
            int(PRECONDITION_SPEC["bytes"]),
            int(PRECONDITION_SPEC["LF"]),
            str(PRECONDITION_SPEC["sha256"]),
        ),
    )
    try:
        payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(ERROR_TOKEN) from error
    return {
        "state_relative_path": PRECONDITION_RELATIVE,
        **{key: identity[key] for key in ("bytes", "LF", "sha256", "mode")},
        "reviewed_predecessor_evidence": True,
        "substitutes_for_current_state_validation": False,
    }


def _parse_json(payload: bytes) -> dict[str, object]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(ERROR_TOKEN) from error
    if type(value) is not dict:
        _fail()
    return value


def _validate_dossier_manifest(payload: bytes) -> dict[str, object]:
    manifest = _parse_json(payload)
    false_fields = (
        "approval_decision_generated",
        "atom_map_answers_generated",
        "authority_bundle_generated",
        "authority_changed",
        "full_semantics_attestation_completed",
        "human_answers_prefilled",
        "identity_attestation_completed",
        "post_state_generated",
        "review_ingested",
        "review_submission_compiled",
    )
    if (
        manifest.get("review_unit_id")
        != "CURRENT11_REACTION_TRANSFORMATION_REVIEW_UNIT_000001"
        or manifest.get("parent_review_unit_id")
        != "CURRENT11_FAMILY_RULE_APPROVAL_REVIEW_UNIT_000001"
        or manifest.get("sample_count") != 2
        or manifest.get("question_count") != 25
        or manifest.get("dossier_file_count") != 8
        or manifest.get("non_authoritative_review_aid") is not True
        or manifest.get("ready_for_training") is not False
        or any(manifest.get(field) is not False for field in false_fields)
    ):
        _fail()
    expected_self_excluding = {
        name: spec[2] for name, spec in DOSSIER_LEAVES.items() if name != "dossier_manifest.json"
    }
    if manifest.get("dossier_file_sha256") != expected_self_excluding:
        _fail()
    return {
        "review_unit_id": manifest["review_unit_id"],
        "parent_review_unit_id": manifest["parent_review_unit_id"],
        "sample_count": 2,
        "semantic_question_count": 25,
        "semantic_question_count_source_key": "question_count",
        "non_authoritative_review_aid": True,
        "blank_or_incomplete_review_promoted_to_authority": False,
        "ready_for_training": False,
    }


def _inspect_dossier(state_root: Path) -> dict[str, object]:
    path = state_root / DOSSIER_RELATIVE
    try:
        metadata = _lstat(path)
        inventory = _listdir(path)
    except OSError as error:
        raise ValueError(ERROR_TOKEN) from error
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != 0o755
        or (int(metadata.st_dev), int(metadata.st_ino))
        != (AUTHORIZED_CURRENT_DEVICE, DOSSIER_INODE)
        or inventory != tuple(sorted(DOSSIER_LEAVES))
    ):
        _fail()
    payloads: dict[str, bytes] = {}
    rows: list[dict[str, object]] = []
    for name, expected in DOSSIER_LEAVES.items():
        payload, row = _read_regular_exact(path / name, expected)
        payloads[name] = payload
        rows.append(row)
    semantic = _validate_dossier_manifest(payloads["dossier_manifest.json"])
    return {
        "state_relative_path": DOSSIER_RELATIVE,
        "kind": "directory",
        "mode": "0755",
        "current_identity": {
            "st_dev": int(metadata.st_dev),
            "st_ino": int(metadata.st_ino),
        },
        "inventory": rows,
        "semantic_manifest_verification": semantic,
    }


def _inspect_routing_canonical(state_root: Path) -> dict[str, object]:
    path = state_root / ROUTING_CANONICAL_RELATIVE
    try:
        metadata = _lstat(path)
        target = _readlink(path)
    except OSError as error:
        raise ValueError(ERROR_TOKEN) from error
    if (
        not stat.S_ISLNK(metadata.st_mode)
        or (int(metadata.st_dev), int(metadata.st_ino))
        != (AUTHORIZED_CURRENT_DEVICE, ROUTING_CANONICAL_INODE)
        or target != ROUTING_READLINK
        or Path(target).is_absolute()
        or Path(target).name != target
        or "/" in target
        or target in (".", "..")
    ):
        _fail()
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise ValueError(ERROR_TOKEN) from error
    expected = state_root / ROUTING_OBJECT_RELATIVE
    if resolved != expected:
        _fail()
    return {
        "state_relative_path": ROUTING_CANONICAL_RELATIVE,
        "kind": "symlink",
        "current_identity": {
            "st_dev": int(metadata.st_dev),
            "st_ino": int(metadata.st_ino),
        },
        "readlink": target,
        "basename_only_relative_target": True,
        "resolves_to_state_relative_path": ROUTING_OBJECT_RELATIVE,
        "symlink_permission_bits_in_semantic_identity": False,
    }


def _aggregate_sha256(payloads: Mapping[str, bytes]) -> str:
    if type(payloads) is not dict or tuple(payloads) != tuple(ROUTING_LEAVES):
        _fail()
    digest = hashlib.sha256()
    digest.update(ROUTING_AGGREGATE_DOMAIN)
    for name in ROUTING_LEAVES:
        payload = payloads[name]
        if type(payload) is not bytes:
            _fail()
        encoded = name.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big", signed=False))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big", signed=False))
        digest.update(payload)
    return digest.hexdigest()


def _validate_routing_semantics(payloads: Mapping[str, bytes]) -> dict[str, object]:
    records_name = "current11_dataset_partial_supervision_routing_records.csv"
    manifest_name = "current11_dataset_partial_supervision_routing_manifest.json"
    try:
        reader = csv.DictReader(
            io.StringIO(payloads[records_name].decode("utf-8"), newline="")
        )
        records = list(reader)
    except (UnicodeDecodeError, csv.Error) as error:
        raise ValueError(ERROR_TOKEN) from error
    if (
        tuple(reader.fieldnames or ()) != ROUTING_RECORD_COLUMNS
        or len(records) != 275
        or any(None in row or tuple(row) != ROUTING_RECORD_COLUMNS for row in records)
    ):
        _fail()
    for index, row in enumerate(records):
        sample = SAMPLE_ORDER[index // len(TASK_ORDER)]
        task = TASK_ORDER[index % len(TASK_ORDER)]
        if (
            tuple(
                row[key]
                for key in ("sample_index_row_id", "pdb_id", "ligand_comp_id")
            )
            != sample
            or row["semantic_task_name"] != task
            or row["current_runtime_consumer_available"] != "false"
            or row["training_loss_authorized"] != "false"
        ):
            _fail()
    manifest = _parse_json(payloads[manifest_name])
    expected_samples = [
        {"sample_index_row_id": sample, "pdb_id": pdb, "ligand_comp_id": ligand}
        for sample, pdb, ligand in SAMPLE_ORDER
    ]
    expected_masks = [
        {"semantic_name": semantic, "display_alias": alias}
        for semantic, alias in CANONICAL_MASKS
    ]
    readiness = manifest.get("readiness")
    if (
        manifest.get("schema_version")
        != "covapie_current11_dataset_partial_supervision_routing_sidecar_v1"
        or manifest.get("sample_count") != 11
        or manifest.get("semantic_task_count") != 25
        or manifest.get("routing_record_count") != 275
        or manifest.get("canonical_sample_identity") != expected_samples
        or manifest.get("semantic_task_names") != list(TASK_ORDER)
        or manifest.get("canonical_mask_semantics") != expected_masks
        or type(readiness) is not dict
        or readiness.get("ready_for_dataloader_integration") is not False
        or readiness.get("ready_for_model_integration") is not False
        or readiness.get("training_loss_authorized") is not False
        or readiness.get("runtime_consumer_available") is not False
        or readiness.get("feature_semantics_reaudit_required_before_training")
        is not True
        or readiness.get("ready_for_training") is not False
    ):
        _fail()
    return {
        "sample_identity_order_count": 11,
        "sample_identity_order_exact": True,
        "semantic_task_order_count": 25,
        "semantic_task_order_exact": True,
        "routing_record_cardinality": 275,
        "routing_record_identity_and_order_exact": True,
        "canonical_mask_semantics": expected_masks,
        "ready_for_dataloader_integration": False,
        "ready_for_model_integration": False,
        "ready_for_loss_integration": False,
        "loss_integration_published_source_key": "training_loss_authorized",
        "feature_semantics_reaudit_required_before_training": True,
        "ready_for_training": False,
    }


def _inspect_routing_object(state_root: Path) -> dict[str, object]:
    path = state_root / ROUTING_OBJECT_RELATIVE
    try:
        metadata = _lstat(path)
        inventory = _listdir(path)
    except OSError as error:
        raise ValueError(ERROR_TOKEN) from error
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != 0o755
        or (int(metadata.st_dev), int(metadata.st_ino))
        != (AUTHORIZED_CURRENT_DEVICE, ROUTING_OBJECT_INODE)
        or inventory != tuple(sorted(ROUTING_LEAVES))
    ):
        _fail()
    payloads: dict[str, bytes] = {}
    rows: list[dict[str, object]] = []
    for name, expected in ROUTING_LEAVES.items():
        payload, row = _read_regular_exact(path / name, expected)
        payloads[name] = payload
        rows.append(row)
    aggregate = _aggregate_sha256(payloads)
    if aggregate != ROUTING_AGGREGATE:
        _fail()
    semantic = _validate_routing_semantics(payloads)
    return {
        "state_relative_path": ROUTING_OBJECT_RELATIVE,
        "kind": "directory",
        "mode": "0755",
        "current_identity": {
            "st_dev": int(metadata.st_dev),
            "st_ino": int(metadata.st_ino),
        },
        "inventory": rows,
        "aggregate_sha256": aggregate,
        "aggregate_domain": ROUTING_AGGREGATE_DOMAIN[:-1].decode("ascii"),
        "aggregate_framing": "uint64be_name_length_name_uint64be_payload_length_payload",
        "semantic_manifest_verification": semantic,
    }


def _unescape_mount_field(value: str) -> str:
    def replace(match: re.Match[str]) -> str:
        decoded = chr(int(match.group(1), 8))
        if decoded == "\0":
            _fail()
        return decoded

    return _MOUNT_ESCAPE.sub(replace, value)


def _parse_mountinfo(payload: bytes) -> list[dict[str, object]]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(ERROR_TOKEN) from error
    records: list[dict[str, object]] = []
    for line in text.splitlines():
        fields = line.split()
        if "-" not in fields:
            _fail()
        separator = fields.index("-")
        if separator < 6 or len(fields) < separator + 4:
            _fail()
        try:
            mount_id = int(fields[0])
            parent_id = int(fields[1])
        except ValueError as error:
            raise ValueError(ERROR_TOKEN) from error
        records.append(
            {
                "mount_id": mount_id,
                "parent_mount_id": parent_id,
                "major_minor": fields[2],
                "root": _unescape_mount_field(fields[3]),
                "target": _unescape_mount_field(fields[4]),
                "fstype": fields[separator + 1],
                "source": _unescape_mount_field(fields[separator + 2]),
            }
        )
    if not records:
        _fail()
    return records


def _within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _validate_mount_topology_record(record: Mapping[str, object]) -> None:
    if (
        type(record) is not dict
        or record.get("fstype") != MOUNT_FSTYPE
        or record.get("source") != MOUNT_SOURCE
        or record.get("root") != MOUNT_ROOT
        or record.get("target") != MOUNT_TARGET
        or record.get("major_minor") != CURRENT_MAJOR_MINOR
        or type(record.get("mount_id")) is not int
        or type(record.get("parent_mount_id")) is not int
    ):
        _fail()


def _inspect_mount_topology(
    state_root: Path,
    *,
    dossier: Mapping[str, object],
    canonical: Mapping[str, object],
    routing_object: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    records = _parse_mountinfo(_mountinfo_bytes())
    covering = [
        record
        for record in records
        if _within(state_root, Path(str(record["target"])))
    ]
    if not covering:
        _fail()
    maximum = max(len(Path(str(record["target"])).parts) for record in covering)
    selected = [
        record
        for record in covering
        if len(Path(str(record["target"])).parts) == maximum
    ]
    if len(selected) != 1:
        _fail()
    record = selected[0]
    _validate_mount_topology_record(record)
    target = Path(MOUNT_TARGET)
    exact_paths = (
        state_root / DOSSIER_RELATIVE,
        state_root / ROUTING_CANONICAL_RELATIVE,
        state_root / ROUTING_OBJECT_RELATIVE,
    )
    for path in exact_paths:
        try:
            metadata = _lstat(path)
            resolved = path.resolve(strict=True)
        except (OSError, RuntimeError) as error:
            raise ValueError(ERROR_TOKEN) from error
        if (
            not _within(path, target)
            or not _within(resolved, target)
            or int(metadata.st_dev) != AUTHORIZED_CURRENT_DEVICE
        ):
            _fail()
    if (
        int(_lstat(state_root).st_dev) != AUTHORIZED_CURRENT_DEVICE
        or os.major(AUTHORIZED_CURRENT_DEVICE) != 0
        or os.minor(AUTHORIZED_CURRENT_DEVICE) != 50
        or dossier.get("current_identity", {}).get("st_dev")
        != AUTHORIZED_CURRENT_DEVICE
        or canonical.get("current_identity", {}).get("st_dev")
        != AUTHORIZED_CURRENT_DEVICE
        or routing_object.get("current_identity", {}).get("st_dev")
        != AUTHORIZED_CURRENT_DEVICE
    ):
        _fail()
    stable = {
        "fstype": MOUNT_FSTYPE,
        "source": MOUNT_SOURCE,
        "root": MOUNT_ROOT,
        "target": MOUNT_TARGET,
        "historical_major_minor": HISTORICAL_MAJOR_MINOR,
        "current_major_minor": CURRENT_MAJOR_MINOR,
        "historical_st_dev": HISTORICAL_DEVICE,
        "current_st_dev": AUTHORIZED_CURRENT_DEVICE,
        "most_specific_unique_mount_record": True,
        "transition_object_count_on_mount": 3,
    }
    diagnostics = {
        "diagnostic_only": True,
        "mount_id": record["mount_id"],
        "parent_mount_id": record["parent_mount_id"],
        "stable_contract_digest_participation": False,
        "gate_admission_semantic_identity": False,
    }
    return stable, diagnostics


def _expected_transition_records() -> list[dict[str, object]]:
    common = {
        "device_transition_only": True,
        "transition_authorized": True,
    }
    return [
        {
            "transition_index": 0,
            "object_id": "unit_000001_dossier",
            "state_relative_path": DOSSIER_RELATIVE,
            "object_kind": "directory",
            "historical_identity": {"st_dev": 49, "st_ino": DOSSIER_INODE},
            "authorized_current_identity": {"st_dev": 50, "st_ino": DOSSIER_INODE},
            **common,
            "lineage_checks": {
                "path_exact": True,
                "type_exact": True,
                "inode_exact": True,
                "mode_exact_or_not_applicable": True,
                "readlink_exact_or_not_applicable": "not_applicable",
                "inventory_exact": True,
                "leaf_sizes_exact": True,
                "leaf_sha256_exact": True,
                "aggregate_exact_or_not_applicable": "not_applicable",
                "semantic_manifest_exact": True,
                "mount_topology_exact": True,
            },
        },
        {
            "transition_index": 1,
            "object_id": "routing_canonical",
            "state_relative_path": ROUTING_CANONICAL_RELATIVE,
            "object_kind": "symlink",
            "historical_identity": {"st_dev": 49, "st_ino": ROUTING_CANONICAL_INODE},
            "authorized_current_identity": {"st_dev": 50, "st_ino": ROUTING_CANONICAL_INODE},
            **common,
            "lineage_checks": {
                "path_exact": True,
                "type_exact": True,
                "inode_exact": True,
                "mode_exact_or_not_applicable": "not_applicable",
                "readlink_exact_or_not_applicable": True,
                "inventory_exact": "not_applicable",
                "leaf_sizes_exact": "not_applicable",
                "leaf_sha256_exact": "not_applicable",
                "aggregate_exact_or_not_applicable": True,
                "semantic_manifest_exact": "not_applicable",
                "mount_topology_exact": True,
            },
        },
        {
            "transition_index": 2,
            "object_id": "routing_object",
            "state_relative_path": ROUTING_OBJECT_RELATIVE,
            "object_kind": "directory",
            "historical_identity": {"st_dev": 49, "st_ino": ROUTING_OBJECT_INODE},
            "authorized_current_identity": {"st_dev": 50, "st_ino": ROUTING_OBJECT_INODE},
            **common,
            "lineage_checks": {
                "path_exact": True,
                "type_exact": True,
                "inode_exact": True,
                "mode_exact_or_not_applicable": True,
                "readlink_exact_or_not_applicable": "not_applicable",
                "inventory_exact": True,
                "leaf_sizes_exact": True,
                "leaf_sha256_exact": True,
                "aggregate_exact_or_not_applicable": True,
                "semantic_manifest_exact": True,
                "mount_topology_exact": True,
            },
        },
    ]


def _validate_transition_records(records: object) -> None:
    expected = _expected_transition_records()
    if type(records) is not list or records != expected or len(records) != 3:
        _fail()
    if [row["object_id"] for row in records] != list(TRANSITION_OBJECT_IDS):
        _fail()
    for row in records:
        historical = row["historical_identity"]
        current = row["authorized_current_identity"]
        if (
            historical["st_dev"] != HISTORICAL_DEVICE
            or current["st_dev"] != AUTHORIZED_CURRENT_DEVICE
            or historical["st_ino"] != current["st_ino"]
            or row["device_transition_only"] is not True
            or row["transition_authorized"] is not True
        ):
            _fail()


def _readiness() -> dict[str, bool]:
    return {
        "state_mount_device_transition_contract_designed": True,
        "state_mount_device_transition_contract_gate_implemented": True,
        "state_mount_device_transition_contract_gate_passed": True,
        "mount_device_transition_only": True,
        "ready_for_remap_predecessor_successor_integration": True,
        "ready_for_public_remap_adapter_hot_loop_contract_implementation": False,
        "compiler_context_rebuild_device_identity_risk": True,
        "ready_for_dataloader_integration": False,
        "ready_for_model_integration": False,
        "ready_for_loss_integration": False,
        "feature_semantics_reaudit_required_before_training": True,
        "ready_for_training": False,
        "checkpoint_bytes_read": False,
        "model_parameter_shape_change_required": False,
        "commit_created": False,
        "push_performed": False,
    }


def _negative_matrix() -> list[dict[str, object]]:
    return [
        {
            "case_index": index,
            "case_id": case_id,
            "expected_result": "fail_closed",
            "error_token": ERROR_TOKEN,
        }
        for index, case_id in enumerate(NEGATIVE_CASE_IDS)
    ]


def _historical_groups_for_artifact(
    historical_rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    by_path = {str(row["path"]): dict(row) for row in historical_rows}
    return [
        {
            "lineage_id": group["lineage_id"],
            "introduction_commit": group["introduction_commit"],
            "introduction_parent": group["introduction_parent"],
            "introduction_subject": group["introduction_subject"],
            "historical_identity_constants": group["identity_constants"],
            "current_head_exact4": [by_path[path] for path in group["paths"]],
        }
        for group in HISTORICAL_GROUPS
    ]


def _manifest(
    *,
    historical_groups: list[dict[str, object]],
    precondition: Mapping[str, object],
    topology: Mapping[str, object],
) -> dict[str, object]:
    return {
        "schema_version": "covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_manifest_v1",
        "contract_name": "covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate",
        "contract_version": "v1",
        "base_commit": BASE_COMMIT,
        "scope": "Current11 Task2 remap predecessor reachable state-device transition only",
        "historical_device_identity_intent": "lifecycle_snapshot",
        "mount_device_transition_only": True,
        "mount_restoration_engineering_recommended": False,
        "transition_object_count": 3,
        "historical_device": HISTORICAL_DEVICE,
        "authorized_current_device": AUTHORIZED_CURRENT_DEVICE,
        "mount_topology": dict(topology),
        "stable_semantic_exclusions": [
            "mount_id",
            "parent_mount_id",
            "namespace_inode",
            "mtime",
            "ctime",
            "atime",
            "directory_size",
            "timestamp",
            "random_nonce",
        ],
        "historical_gate_lineage": historical_groups,
        "precondition_report": dict(precondition),
        "repository_lifecycle_contract": {
            "accepted_profiles": ["precommit-untracked", "clean-tracked-successor"],
            "branch": BRANCH,
            "base_commit_must_be_ancestor_or_equal_head": True,
            "origin_main_used_for_admission": False,
        },
        "readiness": _readiness(),
    }


def _lineage_evidence(
    *,
    historical_groups: list[dict[str, object]],
    precondition: Mapping[str, object],
    dossier: Mapping[str, object],
    canonical: Mapping[str, object],
    routing_object: Mapping[str, object],
    topology: Mapping[str, object],
) -> dict[str, object]:
    return {
        "schema_version": "covapie_current11_task2_batch_index_remap_state_mount_device_transition_lineage_evidence_v1",
        "historical_repository_lineage": historical_groups,
        "precondition_report": dict(precondition),
        "dossier_exact8": {
            "state_relative_path": dossier["state_relative_path"],
            "mode": dossier["mode"],
            "inventory": dossier["inventory"],
            "semantic_manifest_verification": dossier[
                "semantic_manifest_verification"
            ],
        },
        "routing_canonical": {
            "state_relative_path": canonical["state_relative_path"],
            "readlink": canonical["readlink"],
            "basename_only_relative_target": True,
            "resolves_to_state_relative_path": ROUTING_OBJECT_RELATIVE,
            "symlink_permission_bits_in_semantic_identity": False,
        },
        "routing_object_exact4": {
            "state_relative_path": routing_object["state_relative_path"],
            "mode": routing_object["mode"],
            "inventory": routing_object["inventory"],
            "aggregate_sha256": routing_object["aggregate_sha256"],
            "aggregate_domain": routing_object["aggregate_domain"],
            "aggregate_framing": routing_object["aggregate_framing"],
            "semantic_manifest_verification": routing_object[
                "semantic_manifest_verification"
            ],
        },
        "mount_topology_semantic_evidence": dict(topology),
        "current_mount_id_or_parent_mount_id_recorded_in_stable_evidence": False,
    }


def _contract_digest(artifacts: Mapping[str, bytes]) -> str:
    if type(artifacts) is not dict or tuple(artifacts) != STABLE_ARTIFACT_NAMES:
        _fail()
    digest = hashlib.sha256()
    digest.update(CONTRACT_DIGEST_DOMAIN)
    for name in STABLE_ARTIFACT_NAMES:
        encoded = name.encode("utf-8")
        payload = artifacts[name]
        if type(payload) is not bytes:
            _fail()
        digest.update(len(encoded).to_bytes(8, "big", signed=False))
        digest.update(encoded)
        digest.update(len(payload).to_bytes(8, "big", signed=False))
        digest.update(payload)
    return digest.hexdigest()


def _artifact_report_rows(stable: Mapping[str, bytes]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, name in enumerate(ARTIFACT_NAMES):
        row: dict[str, object] = {
            "artifact_index": index,
            "artifact_name": name,
            "stable_contract_digest_participation": name in STABLE_ARTIFACT_NAMES,
        }
        if name in stable:
            row.update(
                {
                    "bytes": len(stable[name]),
                    "LF": stable[name].count(b"\n"),
                    "sha256": _sha256(stable[name]),
                }
            )
        else:
            row["content_identity"] = "self_excluded"
        rows.append(row)
    return rows


def _validate_artifacts(artifacts: object) -> None:
    if type(artifacts) is not dict or tuple(artifacts) != ARTIFACT_NAMES:
        _fail()
    parsed: dict[str, object] = {}
    for name, payload in artifacts.items():
        if (
            type(payload) is not bytes
            or not payload
            or len(payload) >= 1024 * 1024
            or payload.startswith(b"\xef\xbb\xbf")
            or b"\0" in payload
            or b"\r" in payload
            or not payload.endswith(b"\n")
            or payload.endswith(b"\n\n")
        ):
            _fail()
        parsed[name] = _strict_json(payload)
    stable = {name: artifacts[name] for name in STABLE_ARTIFACT_NAMES}
    transitions = parsed[ARTIFACT_NAMES[1]]
    negatives = parsed[ARTIFACT_NAMES[3]]
    report = parsed[ARTIFACT_NAMES[4]]
    _validate_transition_records(transitions)
    if (
        negatives != _negative_matrix()
        or type(report) is not dict
        or report.get("gate_status")
        != "PASS_STATE_MOUNT_DEVICE_TRANSITION_CONTRACT_ONLY"
        or report.get("contract_digest") != _contract_digest(stable)
        or report.get("transition_object_count") != 3
        or report.get("negative_case_count") != len(NEGATIVE_CASE_IDS)
        or report.get("readiness") != _readiness()
    ):
        _fail()


def _direct_path_item(path: Path) -> tuple[object, ...]:
    metadata = path.lstat()
    payload = path.read_bytes() if stat.S_ISREG(metadata.st_mode) else None
    return (
        int(metadata.st_dev),
        int(metadata.st_ino),
        stat.S_IFMT(metadata.st_mode),
        stat.S_IMODE(metadata.st_mode),
        int(metadata.st_size),
        int(metadata.st_mtime_ns),
        None if payload is None else _sha256(payload),
    )


def _direct_state_snapshot(state_root: Path) -> tuple[object, ...]:
    dossier = state_root / DOSSIER_RELATIVE
    canonical = state_root / ROUTING_CANONICAL_RELATIVE
    routing_object = state_root / ROUTING_OBJECT_RELATIVE
    precondition = state_root / PRECONDITION_RELATIVE
    dossier_names = tuple(sorted(os.listdir(dossier)))
    routing_names = tuple(sorted(os.listdir(routing_object)))
    return (
        _direct_path_item(state_root),
        _direct_path_item(precondition),
        _direct_path_item(dossier),
        dossier_names,
        tuple((name, _direct_path_item(dossier / name)) for name in dossier_names),
        _direct_path_item(canonical),
        os.readlink(canonical),
        _direct_path_item(routing_object),
        routing_names,
        tuple(
            (name, _direct_path_item(routing_object / name))
            for name in routing_names
        ),
    )


def _direct_repository_snapshot(repo_root: Path) -> tuple[object, ...]:
    paths = (*REPOSITORY_EXACT4, *HISTORICAL_FILE_SPECS)
    return (
        _run_git(repo_root, ("status", "--porcelain=v1", "--untracked-files=all")),
        _run_git(repo_root, ("diff", "--name-status")),
        _run_git(repo_root, ("diff", "--cached", "--name-status")),
        _run_git(repo_root, ("rev-parse", "HEAD")),
        tuple((relative, _direct_path_item(repo_root / relative)) for relative in paths),
    )


def _build_impl(*, repo_root: Path, state_root: Path) -> dict[str, bytes]:
    repository = _require_root(repo_root)
    state = _require_root(state_root)
    before_repository = _direct_repository_snapshot(repository)
    before_state = _direct_state_snapshot(state)

    _validate_repository_lineage(repository)
    lifecycle = _repository_lifecycle(repository)
    historical_rows = _verify_historical_repository_lineage(repository)
    historical_groups = _historical_groups_for_artifact(historical_rows)
    precondition = _verify_precondition_report(state)
    dossier = _inspect_dossier(state)
    canonical = _inspect_routing_canonical(state)
    routing_object = _inspect_routing_object(state)
    topology, mount_diagnostics = _inspect_mount_topology(
        state,
        dossier=dossier,
        canonical=canonical,
        routing_object=routing_object,
    )

    transitions = _expected_transition_records()
    _validate_transition_records(transitions)
    stable_values = (
        _manifest(
            historical_groups=historical_groups,
            precondition=precondition,
            topology=topology,
        ),
        transitions,
        _lineage_evidence(
            historical_groups=historical_groups,
            precondition=precondition,
            dossier=dossier,
            canonical=canonical,
            routing_object=routing_object,
            topology=topology,
        ),
        _negative_matrix(),
    )
    stable = dict(
        zip(
            STABLE_ARTIFACT_NAMES,
            (_canonical_json(value) for value in stable_values),
            strict=True,
        )
    )
    stable_second = dict(
        zip(
            STABLE_ARTIFACT_NAMES,
            (_canonical_json(value) for value in stable_values),
            strict=True,
        )
    )
    if stable != stable_second:
        _fail()
    digest = _contract_digest(stable)
    report = {
        "schema_version": "covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_report_v1",
        "gate_status": "PASS_STATE_MOUNT_DEVICE_TRANSITION_CONTRACT_ONLY",
        "contract_digest": digest,
        "artifact_file_count": 5,
        "artifact_identities": _artifact_report_rows(stable),
        "repository_lifecycle": lifecycle,
        "transition_object_count": 3,
        "transition_object_ids": list(TRANSITION_OBJECT_IDS),
        "transition_authorized_count": 3,
        "negative_case_count": len(NEGATIVE_CASE_IDS),
        "stable_artifact_double_serialization_identical": True,
        "historical_public_gates_called": False,
        "heavy_remap_contract_chain_called": False,
        "remap_adapter_private_contract_called": False,
        "state_or_repository_write_performed": False,
        "mount_namespace_diagnostics": mount_diagnostics,
        "readiness": _readiness(),
    }
    artifacts = dict(stable)
    artifacts[ARTIFACT_NAMES[4]] = _canonical_json(report)
    _validate_artifacts(artifacts)
    if (
        _direct_repository_snapshot(repository) != before_repository
        or _direct_state_snapshot(state) != before_state
    ):
        _fail()
    return artifacts


def build_covapie_current11_task2_batch_index_remap_state_mount_device_transition_contract_gate_v1(
    *,
    repo_root: Path,
    state_root: Path,
) -> dict[str, bytes]:
    """Validate Exact3 device-only lineage and return deterministic Exact5 bytes."""

    try:
        return _build_impl(repo_root=repo_root, state_root=state_root)
    except Exception as error:
        if type(error) is ValueError and str(error) == ERROR_TOKEN:
            raise
        raise ValueError(ERROR_TOKEN) from error
