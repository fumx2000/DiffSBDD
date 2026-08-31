#!/usr/bin/env python3
"""Check the CovaPIE source-binding V2 active-consumer integration overlay."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import inspect
import io
import json
from pathlib import Path
import stat
import subprocess
from typing import Callable, Mapping

from covalent_ext import (
    covapie_source_binding_active_consumer_integration_v2 as subject,
)
from covalent_ext import covapie_source_binding_policy_v2 as source_binding_v2


ROOT = Path(__file__).resolve().parents[1]
BASELINE_HEAD = "1e77d93929e491e589060269416b34fe47c0fb15"
BASELINE_TREE = "fd8605cb698a22297cee02a3156ca13483dfe96e"
BASELINE_SUBJECT = "add CovaPIE 2A2 source binding successor v2"
MAX_FILE_BYTES = 1024 * 1024

EXACT4_PATHS = (
    "src/covalent_ext/covapie_source_binding_active_consumer_integration_v2.py",
    "scripts/check_covapie_source_binding_active_consumer_integration_v2.py",
    "tests/test_covapie_source_binding_active_consumer_integration_v2.py",
    "docs/covapie_source_binding_active_consumer_integration_v2_guide.md",
)

CONSUMERS = ("YUN", "NEQ", "CHT", "OZJ", "F24", "2A2")

PUBLIC_RESULT_KEYS = (
    "schema_version",
    "filesystem_source_acceptance_authority",
    "sample_scientific_projection_authority",
    "current_global_state_authority",
    "active_consumer_order",
    "active_consumer_count",
    "per_consumer_projection_digests",
    "artifact_projection_count",
    "current_global_counts",
    "current_canonical_tasks",
    "current_human_review_counts",
    "current_training_runtime_counts",
    "current_geometry_counts",
    "all_V2_successor_sources_bound",
    "all_V2_projections_executed",
    "all_V1_scientific_projections_preserved",
    "current_2A2_census_bound",
    "current_2A2_census_unchanged",
    "global_canonical_task_count",
    "B3_present",
    "sixth_task_present",
    "scientific_authority_reinterpreted",
    "global_census_refreshed",
    "reconciliation_executed",
    "training_admission_created",
    "data_materialized",
    "v2_migration_phase_b2_effective_state_integrated",
    "ready_for_v2_migration_phase_b3_historical_immutability_proof",
    "ready_for_training",
)

B1_SPEC = (
    "SOURCE_BINDING_POLICY_V2",
    "src/covalent_ext/covapie_source_binding_policy_v2.py",
    3704,
    "c17f3532e6004b347ff62e5d354ac1843f384196c2207127e17971acd2e2d4ee",
)

SUCCESSOR_SPECS = (
    (
        "YUN",
        "src/covalent_ext/covapie_yun_completed_decision_ingestion_and_task_label_availability_v2.py",
        21294,
        "a10c929ea86258ac39bc787b3108d622b65c97617e62b19a44bf3711fbffbd52",
        "scripts/check_covapie_yun_completed_decision_ingestion_and_task_label_availability_v2.py",
        28382,
        "f0de27832eb557d1f1150ecddc00a023c7e1d81642cc1c92ef606b302c2a54b2",
        "5a34e260e57598ab62905f0171e43a67acc188e2",
    ),
    (
        "NEQ",
        "src/covalent_ext/covapie_neq_completed_decision_ingestion_and_task_label_availability_v2.py",
        26491,
        "21c6d4f13589a72d8762185108eaa26387c124121bdbbed8f6258b689b0a9b4d",
        "scripts/check_covapie_neq_completed_decision_ingestion_and_task_label_availability_v2.py",
        36383,
        "07c8a64442752a39aaba448db79b5f8299ea97524485e75be956de62337e465b",
        "baab1358bcc8f776df20d8dc76ed476d51ba27f3",
    ),
    (
        "CHT",
        "src/covalent_ext/covapie_cht_completed_decision_ingestion_and_task_label_availability_v2.py",
        27636,
        "e163f77de8bb03f107efc955ce8662291f9b39deb0ba341b72494d07b97cf87a",
        "scripts/check_covapie_cht_completed_decision_ingestion_and_task_label_availability_v2.py",
        38205,
        "9642786fb9807da59f189a4a9023b0e9310c06780b357054b464179ddc5a226d",
        "9e7d520de0baa5e5f107985f45b97f576bbd8fc0",
    ),
    (
        "OZJ",
        "src/covalent_ext/covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2.py",
        30745,
        "51af9985cf4de28d48cc55eab71b536472220221d160ee6070677512ba22ef21",
        "scripts/check_covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2.py",
        42913,
        "dec67ac8e86273d49b3da048a7286b900b1171f93ffe85a07a6c1830383dd825",
        "33d08ee6069592f0fe28ca53bed5615f578d10fc",
    ),
    (
        "F24",
        "src/covalent_ext/covapie_f24_completed_decision_ingestion_and_task_label_availability_v2.py",
        25212,
        "c83aa221721849cff1ee9e3fed4154204333edb6207ec6cceb70348802bcf253",
        "scripts/check_covapie_f24_completed_decision_ingestion_and_task_label_availability_v2.py",
        44863,
        "51a8af193c8c2eeb097a53cac66a25c0688b5e9066c6e07f0891fbbf897746a9",
        "a81be8b1260d14b385b0faf05e2ddcc56bd403d8",
    ),
    (
        "2A2",
        "src/covalent_ext/covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2.py",
        34512,
        "9f6c7c935358cc2f8dd1d5e71c285abc5c22eb7160be74afa12f42c85de4a0a9",
        "scripts/check_covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2.py",
        49029,
        "0a132b715abbfcb7c53f7b354d1b7cb6211993d2355675d3631843bd5aef905c",
        "1e77d93929e491e589060269416b34fe47c0fb15",
    ),
)

PROJECTION_SPECS = (
    (
        "YUN",
        (
            ("covapie_yun_completed_human_decision_snapshot_v1.json", 34388, "6ce626eb5fcbc8f875f727732daa6047ac35152319db8cfe444725e648d6a012"),
            ("covapie_yun_event_task_label_availability_v1.csv", 13886, "f5c58990490282a9a3ab5218f8ed83f8cead6062fdeb06c4fedc10665630ca0e"),
            ("covapie_yun_completed_decision_ingestion_summary_v1.json", 3983, "899faf081224d113bd6e8b277464dbb0b0ee1a992d5262d9b34736b68f42c32e"),
            ("covapie_yun_completed_decision_ingestion_manifest_v1.json", 16350, "18eb6bbfcebb0498b84da22d2e32770f10cf3f3a03f4db6aa58b0c9e6d34204c"),
        ),
    ),
    (
        "NEQ",
        (
            ("covapie_neq_completed_human_decision_snapshot_v1.json", 33094, "9f3b8a29410852fe9fdd42cea10f8778e84a1ffe0627b1795fd6380989a2db1c"),
            ("covapie_neq_event_task_label_availability_v1.csv", 11706, "b4b9a301440724464cb92f1b0f28ef1151b24b12eb3ec001a971dacda3632d4a"),
            ("covapie_neq_completed_decision_ingestion_summary_v1.json", 4196, "a6e3fe3326e1cc51746817b547d0b737d3f4be56fe4d5427667c11d9bf019ef3"),
            ("covapie_neq_completed_decision_ingestion_manifest_v1.json", 18257, "4c6ad894929b93a0f450bcad56488aa2c4993de58e88660fd14819b3bd332488"),
        ),
    ),
    (
        "CHT",
        (
            ("covapie_cht_completed_human_decision_snapshot_v1.json", 30409, "9185ecb6ee62349c4f4cc9c384c30c1fa6d5dedc9e3eaa50e2e352f72e74a163"),
            ("covapie_cht_event_task_label_availability_v1.csv", 10225, "a754c0764ec61eacf7ec64dabdc370e4bca5a00abdfb94ea3923b52be55df6b6"),
            ("covapie_cht_completed_decision_ingestion_summary_v1.json", 4266, "22e89e8938438f01d35aa1b66be0613f5fc532cd495f9b424b5500458eee91f6"),
            ("covapie_cht_completed_decision_ingestion_manifest_v1.json", 18366, "f4614719cd554c47eb67f895415e8595f00a346095ffb53cffd4bffec0e85b59"),
        ),
    ),
    (
        "OZJ",
        (
            ("covapie_ozj_completed_human_decision_snapshot_v1.json", 31404, "3458c3559963b09f69495ffe8cf43511a1e84b7de5ad0c84279ccdcd100a4b25"),
            ("covapie_ozj_event_task_label_availability_v1.csv", 9031, "b039dbde52e2fe6a46866cdce0a378fc6dcc942e4a552845ce664fd80f1009d3"),
            ("covapie_ozj_completed_decision_ingestion_summary_v1.json", 4803, "305bb814c97a450e8dc95961433daf1e9aca942537469153a89d7e322c6c3214"),
            ("covapie_ozj_completed_decision_ingestion_manifest_v1.json", 18554, "ca1e305920afd724c138ed572764bd3147039345034ebd172dfb1e274a4a1468"),
        ),
    ),
    (
        "F24",
        (
            ("covapie_f24_completed_human_decision_snapshot_v1.json", 22044, "d53ff475b0d86b076b5649916cd7118821e8c883daba5727b1efd7f051b8de11"),
            ("covapie_f24_event_task_label_availability_v1.csv", 7641, "516c3ea3ac291c5039e1def72a891b54fd42d5aa45388f27b436a655467cd28c"),
            ("covapie_f24_completed_decision_ingestion_summary_v1.json", 3462, "be67578dac2c6593bc75b256cd9c344c90f8650662443ff5cd316bb68b18b385"),
            ("covapie_f24_completed_decision_ingestion_manifest_v1.json", 16125, "02f56545297fb78c2b2cbd205115d9dca680a8446bfb753109428b698bdd5dfd"),
        ),
    ),
    (
        "2A2",
        (
            ("covapie_2a2_completed_human_decision_snapshot_v1.json", 29063, "87cfffd1c9e2e82db6d9aeba2dfedc907b459d89c0160c50fb9fbddee7393000"),
            ("covapie_2a2_event_task_label_availability_v1.csv", 8950, "f6533013dcb2eea5fcee579d906c7ab3009d1db8c9f2d9f906aca5ee0122f52b"),
            ("covapie_2a2_completed_decision_ingestion_summary_v1.json", 4623, "6c5a92910becab41a4e3af0317fa3438d6a682e1dac4d4ef1d4e48fe34773ea2"),
            ("covapie_2a2_completed_decision_ingestion_manifest_v1.json", 19083, "af20556b9a9197d2c9ddfd3fc19d01ef43a51f935aa1fdc29bac0e4c5f410287"),
        ),
    ),
)

CENSUS_ROOT = "data/derived/covalent_small/covapie_cumulative1000_current_global_readiness_census_with_2a2_v1"
CENSUS_SPECS = (
    (
        "CURRENT_2A2_CENSUS_CSV",
        CENSUS_ROOT + "/covapie_cumulative1000_current_global_readiness_census_with_2a2_v1.csv",
        529994,
        "5b56422e9c8d0ec6c09fe71c49d51fff0c7e7a9720ccf3c4c20dc324e409c57d",
    ),
    (
        "CURRENT_2A2_CENSUS_SUMMARY",
        CENSUS_ROOT + "/covapie_cumulative1000_current_global_readiness_summary_with_2a2_v1.json",
        17389,
        "3217bf5e45de40e66f1af22d000a48fef81548c6431c3e6d9349c4824b1c80f3",
    ),
    (
        "CURRENT_2A2_CENSUS_MANIFEST",
        CENSUS_ROOT + "/covapie_cumulative1000_current_global_readiness_manifest_with_2a2_v1.json",
        47068,
        "c30f8f52fc20495a06f7bead98ac80197f434eeb0b4776a1ef2c152f13d1e2b7",
    ),
)

EXPECTED_TASKS = (
    (0, "warhead_only", "A", 112),
    (1, "linker_plus_warhead", "B", 52),
    (2, "scaffold_plus_warhead", "B2", 52),
    (3, "scaffold_only", "B3", 112),
    (4, "scaffold_plus_linker_plus_warhead", "C", 112),
)

SUMMARY_VALUES = (
    (("chemistry", "POSITIVE", "count"), 112),
    (("task_relevance", "RELEVANT", "count"), 113),
    (("training_use", "INCLUDE", "count"), 44),
    (("training_use", "EXCLUDE_FROM_TRAINING_ONLY", "count"), 68),
    (("training_stage", "future_training_admission_candidate_count"), 27),
    (("reactive_pair", "sample_level_authoritative_pair_count"), 112),
    (("role", "role_partition_sample_authoritative_count"), 112),
    (("human_review", "completed_positive_event_count"), 95),
    (("human_review", "completed_positive_unit_count"), 13),
    (("human_review", "completed_negative_event_count"), 24),
    (("human_review", "completed_negative_unit_count"), 4),
    (("human_review", "completed_event_count"), 119),
    (("human_review", "completed_unit_count"), 17),
    (("human_review", "unreviewed_event_count"), 219),
    (("human_review", "unreviewed_unit_count"), 114),
    (("human_review", "pending_event_count"), 219),
    (("human_review", "current_pending_review_unit_count"), 114),
    (("training_stage", "formal_training_admitted_count"), 5),
    (("training_stage", "current_runtime_model_usable_count"), 17),
    (("geometry", "POST_source_evidence_available_count"), 867),
    (("geometry", "POST_sample_authoritative_count"), 21),
    (("geometry", "POST_training_target_available_count"), 17),
    (("geometry", "PRE_source_evidence_available_count"), 0),
    (("geometry", "PRE_sample_authoritative_count"), 0),
    (("geometry", "PRE_training_target_available_count"), 0),
    (("geometry", "POST_to_PRE_promotion_performed"), False),
    (("geometry", "PRE_zero_fill_performed"), False),
    (("geometry", "PRE_is_v1_hard_requirement"), False),
    (("canonical_exact5", "task_count"), 5),
    (("canonical_exact5", "B3_present"), True),
    (("canonical_exact5", "sixth_task_present"), False),
    (("authority_boundary", "I12_REVIEW_STARTED"), False),
    (("authority_boundary", "training_admission_created"), False),
    (("authority_boundary", "training_started"), False),
    (("authority_boundary", "READY_FOR_TRAINING"), False),
)


def _git(*arguments: str, root: Path) -> str:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode:
        raise ValueError("GIT_COMMAND_FAILED:" + arguments[0])
    return completed.stdout.rstrip("\n")


def classify_lifecycle_from_facts(
    *,
    tracked_exact4: set[str],
    ordinary_untracked: set[str],
    status_entries: tuple[str, ...],
    working_diff: set[str],
    cached_diff: set[str],
) -> str:
    expected = set(EXACT4_PATHS)
    if (
        not tracked_exact4
        and ordinary_untracked == expected
        and tuple(sorted(status_entries))
        == tuple(f"?? {path}" for path in sorted(expected))
        and not working_diff
        and not cached_diff
    ):
        return "CANDIDATE_UNTRACKED"
    if (
        tracked_exact4 == expected
        and not ordinary_untracked
        and not status_entries
        and not working_diff
        and not cached_diff
    ):
        return "TRACKED_CLEAN"
    raise ValueError("GIT_LIFECYCLE_PROFILE_INVALID")


def validate_repository_relation_from_facts(
    *,
    profile: str,
    head: str,
    origin_main: str,
    ahead: int,
    behind: int,
    parent_shas: tuple[str, ...],
    changed_paths: set[str],
) -> None:
    if profile == "CANDIDATE_UNTRACKED":
        if not (
            head == BASELINE_HEAD
            and origin_main == BASELINE_HEAD
            and (ahead, behind) == (0, 0)
            and not parent_shas
            and not changed_paths
        ):
            raise ValueError("CANDIDATE_REPOSITORY_RELATION_INVALID")
        return
    if profile != "TRACKED_CLEAN":
        raise ValueError("REPOSITORY_RELATION_PROFILE_INVALID")
    if (
        head == BASELINE_HEAD
        or parent_shas != (BASELINE_HEAD,)
        or changed_paths != set(EXACT4_PATHS)
    ):
        raise ValueError("TRACKED_CLEAN_COMMIT_IDENTITY_INVALID")
    if not (
        (origin_main == BASELINE_HEAD and (ahead, behind) == (1, 0))
        or (origin_main == head and (ahead, behind) == (0, 0))
    ):
        raise ValueError("TRACKED_CLEAN_REPOSITORY_RELATION_INVALID")


def verify_git_lifecycle(root: Path) -> str:
    identity = _git(
        "show", "-s", "--format=%T%n%s", BASELINE_HEAD, root=root
    ).splitlines()
    if identity != [BASELINE_TREE, BASELINE_SUBJECT]:
        raise ValueError("BASELINE_TREE_OR_SUBJECT_INVALID")
    tracked = set(
        filter(
            None,
            _git("ls-files", "--", *EXACT4_PATHS, root=root).splitlines(),
        )
    )
    untracked = set(
        filter(
            None,
            _git(
                "ls-files", "--others", "--exclude-standard", root=root
            ).splitlines(),
        )
    )
    status = tuple(
        filter(
            None,
            _git(
                "status", "--porcelain=v1", "--untracked-files=all", root=root
            ).splitlines(),
        )
    )
    working = set(
        filter(None, _git("diff", "--name-only", root=root).splitlines())
    )
    cached = set(
        filter(
            None,
            _git("diff", "--cached", "--name-only", root=root).splitlines(),
        )
    )
    profile = classify_lifecycle_from_facts(
        tracked_exact4=tracked,
        ordinary_untracked=untracked,
        status_entries=status,
        working_diff=working,
        cached_diff=cached,
    )
    head = _git("rev-parse", "HEAD", root=root)
    origin_main = _git("rev-parse", "origin/main", root=root)
    relation = _git(
        "rev-list", "--left-right", "--count", "HEAD...origin/main", root=root
    ).split()
    if len(relation) != 2 or any(not item.isdigit() for item in relation):
        raise ValueError("REPOSITORY_RELATION_COUNT_INVALID")
    ahead, behind = (int(item) for item in relation)
    if profile == "TRACKED_CLEAN":
        parents = tuple(_git("show", "-s", "--format=%P", "HEAD", root=root).split())
        changed = set(
            filter(
                None,
                _git(
                    "diff-tree",
                    "--no-commit-id",
                    "--name-only",
                    "-r",
                    "HEAD",
                    root=root,
                ).splitlines(),
            )
        )
    else:
        parents = ()
        changed = set()
    validate_repository_relation_from_facts(
        profile=profile,
        head=head,
        origin_main=origin_main,
        ahead=ahead,
        behind=behind,
        parent_shas=parents,
        changed_paths=changed,
    )
    return profile


def _verify_exact4_hygiene(root: Path) -> dict[str, dict[str, object]]:
    result: dict[str, dict[str, object]] = {}
    for relative in EXACT4_PATHS:
        path = root / relative
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise ValueError("EXACT4_NOT_REGULAR:" + relative)
        mode = stat.S_IMODE(metadata.st_mode)
        if mode not in {0o644, 0o664} or metadata.st_mode & (
            stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        ):
            raise ValueError("EXACT4_MODE_INVALID:" + relative)
        payload = path.read_bytes()
        if not payload or len(payload) >= MAX_FILE_BYTES:
            raise ValueError("EXACT4_SIZE_INVALID:" + relative)
        if payload.startswith(b"\xef\xbb\xbf"):
            raise ValueError("EXACT4_BOM_FORBIDDEN:" + relative)
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError("EXACT4_UTF8_INVALID:" + relative) from error
        if "\x00" in text or "\r" in text:
            raise ValueError("EXACT4_NUL_OR_CR_FORBIDDEN:" + relative)
        if not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
            raise ValueError("EXACT4_FINAL_LF_INVALID:" + relative)
        if any(line.endswith((" ", "\t")) for line in text.splitlines()):
            raise ValueError("EXACT4_TRAILING_WHITESPACE:" + relative)
        result[relative] = {
            "byte_count": len(payload),
            "loc": len(text.splitlines()),
            "mode": format(mode, "04o"),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    return result


def _verify_public_api() -> None:
    expected = (
        "SourceBindingActiveConsumerIntegrationV2Error",
        "verify_covapie_source_binding_active_consumer_integration_v2",
    )
    if subject.__all__ != expected:
        raise ValueError("PUBLIC_ALL_INVALID")
    signature = inspect.signature(
        subject.verify_covapie_source_binding_active_consumer_integration_v2
    )
    parameters = tuple(signature.parameters.values())
    if (
        len(parameters) != 1
        or parameters[0].name != "repo_root"
        or parameters[0].kind is not inspect.Parameter.KEYWORD_ONLY
        or parameters[0].annotation != "Path"
        or signature.return_annotation != "dict[str, object]"
    ):
        raise ValueError("PUBLIC_VERIFIER_SIGNATURE_INVALID")
    public_names = {
        name
        for name, value in vars(subject).items()
        if not name.startswith("_")
        and (inspect.isclass(value) or inspect.isfunction(value))
        and getattr(value, "__module__", None) == subject.__name__
    }
    if public_names != set(expected):
        raise ValueError("PUBLIC_API_SURFACE_INVALID")


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


def _direct_calls(function: ast.FunctionDef) -> tuple[str, ...]:
    calls = [
        (_call_name(node), node.lineno)
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
    ]
    return tuple(name for name, _line in sorted(calls, key=lambda item: item[1]))


def _verify_production_ast(root: Path) -> None:
    path = root / EXACT4_PATHS[0]
    tree = ast.parse(path.read_bytes().decode("utf-8"), filename=str(path))
    imported_consumers: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            if any(alias.name in {"os", "subprocess", "torch"} for alias in node.names):
                raise ValueError("PRODUCTION_FORBIDDEN_IMPORT")
        if isinstance(node, ast.ImportFrom) and node.module == "covalent_ext":
            imported_consumers.update(alias.name for alias in node.names)
    expected_imports = {
        "covapie_source_binding_policy_v2",
        "covapie_yun_completed_decision_ingestion_and_task_label_availability_v2",
        "covapie_neq_completed_decision_ingestion_and_task_label_availability_v2",
        "covapie_cht_completed_decision_ingestion_and_task_label_availability_v2",
        "covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2",
        "covapie_f24_completed_decision_ingestion_and_task_label_availability_v2",
        "covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2",
    }
    if imported_consumers != expected_imports:
        raise ValueError("PRODUCTION_V2_IMPORT_INVENTORY_INVALID")
    if any(name.endswith("_v1") or "_v1." in name for name in imported_consumers):
        raise ValueError("PRODUCTION_V1_IMPORT_FORBIDDEN")

    forbidden_calls = {
        "open",
        "read_bytes",
        "read_text",
        "write_bytes",
        "write_text",
        "mkdir",
        "replace",
        "rename",
        "unlink",
        "system",
        "Popen",
        "run",
        "materialize",
        "reconcile",
    }
    calls = [_call_name(node) for node in ast.walk(tree) if isinstance(node, ast.Call)]
    prohibited = sorted(set(calls) & forbidden_calls)
    if prohibited:
        raise ValueError("PRODUCTION_FORBIDDEN_CALLS:" + ",".join(prohibited))
    if any(
        isinstance(node, ast.Attribute) and node.attr in {"S_IMODE", "st_mode"}
        for node in ast.walk(tree)
    ):
        raise ValueError("PRODUCTION_EXACT_MODE_LOGIC_FORBIDDEN")
    if "verify_content_identity_v2" in calls:
        raise ValueError("PRODUCTION_CONTENT_ONLY_BINDING_FORBIDDEN")

    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    wrapper_targets = {
        "_project_yun_v2": "verify_published_yun_v1_projection_v2",
        "_project_neq_v2": "verify_published_neq_v1_projection_v2",
        "_project_cht_v2": "verify_published_cht_v1_projection_v2",
        "_project_ozj_v2": "verify_published_ozj_v1_projection_v2",
        "_project_f24_v2": "verify_published_f24_v1_projection_v2",
        "_project_two_a2_v2": "verify_published_two_a2_v1_projection_v2",
    }
    for wrapper, target in wrapper_targets.items():
        if wrapper not in functions or _direct_calls(functions[wrapper]) != (target,):
            raise ValueError("PROJECTION_WRAPPER_CALL_GRAPH_INVALID:" + wrapper)
    public = functions[
        "verify_covapie_source_binding_active_consumer_integration_v2"
    ]
    public_calls = _direct_calls(public)
    required_order = (
        "_bind_all_published_sources",
        *wrapper_targets,
        "_verify_projection_digests",
        "_verify_current_census",
    )
    positions: list[int] = []
    for call in required_order:
        if public_calls.count(call) != 1:
            raise ValueError("PUBLIC_CALL_COUNT_INVALID:" + call)
        positions.append(public_calls.index(call))
    if positions != sorted(positions):
        raise ValueError("PUBLIC_INTEGRATION_ORDER_INVALID")
    bind_calls = _direct_calls(functions["_bind_source"])
    if bind_calls.count("verify_bound_source_v2") != 1:
        raise ValueError("B1_COMBINED_HELPER_CALL_INVALID")


def _bind(root: Path, spec: tuple[str, str, int, str]) -> bytes:
    label, relative, byte_count, sha256 = spec
    return source_binding_v2.verify_bound_source_v2(
        path=root / relative,
        expected_byte_count=byte_count,
        expected_sha256=sha256,
        label=label,
        expected_executable=False,
    )


def _verify_published_dependencies(root: Path) -> dict[str, object]:
    _bind(root, B1_SPEC)
    result: dict[str, object] = {}
    for (
        consumer,
        owner_path,
        owner_bytes,
        owner_sha,
        checker_path,
        checker_bytes,
        checker_sha,
        commit,
    ) in SUCCESSOR_SPECS:
        _bind(root, (consumer + "_V2_OWNER", owner_path, owner_bytes, owner_sha))
        _bind(
            root,
            (consumer + "_V2_CHECKER", checker_path, checker_bytes, checker_sha),
        )
        completed = subprocess.run(
            ("git", "merge-base", "--is-ancestor", commit, "HEAD"),
            cwd=root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if completed.returncode != 0:
            raise ValueError("PUBLISHED_COMMIT_NOT_ANCESTOR:" + consumer)
        result[consumer] = {
            "owner_byte_count": owner_bytes,
            "owner_sha256": owner_sha,
            "checker_byte_count": checker_bytes,
            "checker_sha256": checker_sha,
            "published_commit": commit,
            "bound": True,
        }
    return result


def _projection_wrapper(
    *,
    consumer: str,
    original: Callable[..., dict[str, bytes]],
    events: list[str],
    captured: dict[str, dict[str, bytes]],
) -> Callable[..., dict[str, bytes]]:
    def wrapper(*, repo_root: Path) -> dict[str, bytes]:
        events.append("PROJECT:" + consumer)
        artifacts = original(repo_root=repo_root)
        captured[consumer] = artifacts
        return artifacts

    return wrapper


def _verify_behavioral_order(
    root: Path,
) -> tuple[dict[str, object], dict[str, dict[str, bytes]]]:
    events: list[str] = []
    captured: dict[str, dict[str, bytes]] = {}
    original_bind = subject._bind_source

    def recording_bind(
        *, repo_root: Path, spec: tuple[str, Path, int, str]
    ) -> bytes:
        events.append(spec[0])
        return original_bind(repo_root=repo_root, spec=spec)

    wrappers = (
        ("YUN", "_project_yun_v2"),
        ("NEQ", "_project_neq_v2"),
        ("CHT", "_project_cht_v2"),
        ("OZJ", "_project_ozj_v2"),
        ("F24", "_project_f24_v2"),
        ("2A2", "_project_two_a2_v2"),
    )
    originals = {name: getattr(subject, name) for _consumer, name in wrappers}
    subject._bind_source = recording_bind
    for consumer, name in wrappers:
        setattr(
            subject,
            name,
            _projection_wrapper(
                consumer=consumer,
                original=originals[name],
                events=events,
                captured=captured,
            ),
        )
    try:
        result = subject.verify_covapie_source_binding_active_consumer_integration_v2(
            repo_root=root
        )
    finally:
        subject._bind_source = original_bind
        for name, original in originals.items():
            setattr(subject, name, original)

    expected_events = [B1_SPEC[0]]
    for consumer in CONSUMERS:
        expected_events.extend((consumer + "_V2_OWNER", consumer + "_V2_CHECKER"))
    expected_events.extend(spec[0] for spec in CENSUS_SPECS)
    expected_events.extend("PROJECT:" + consumer for consumer in CONSUMERS)
    if events != expected_events:
        raise ValueError("BEHAVIORAL_INTEGRATION_ORDER_INVALID")
    if tuple(captured) != CONSUMERS:
        raise ValueError("BEHAVIORAL_PROJECTION_INVENTORY_INVALID")
    return result, captured


def _verify_projection_artifacts(
    captured: Mapping[str, Mapping[str, bytes]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    total = 0
    for consumer, specs in PROJECTION_SPECS:
        artifacts = captured[consumer]
        if tuple(artifacts) != tuple(filename for filename, _size, _sha in specs):
            raise ValueError("V1_PROJECTION_INVENTORY_INVALID:" + consumer)
        inventory: dict[str, object] = {}
        for filename, byte_count, sha256 in specs:
            payload = artifacts[filename]
            if (
                type(payload) is not bytes
                or len(payload) != byte_count
                or hashlib.sha256(payload).hexdigest() != sha256
            ):
                raise ValueError("V1_PROJECTION_IDENTITY_INVALID:" + consumer)
            inventory[filename] = {"byte_count": byte_count, "sha256": sha256}
            total += 1
        result[consumer] = inventory
    if total != 24:
        raise ValueError("V1_PROJECTION_TOTAL_INVALID")
    return result


def _at(document: Mapping[str, object], path: tuple[str, ...]) -> object:
    value: object = document
    for key in path:
        if not isinstance(value, dict) or key not in value:
            raise ValueError("CENSUS_SUMMARY_PATH_MISSING:" + ".".join(path))
        value = value[key]
    return value


def _verify_census(root: Path) -> dict[str, object]:
    payloads = {spec[0]: _bind(root, spec) for spec in CENSUS_SPECS}
    summary = json.loads(payloads["CURRENT_2A2_CENSUS_SUMMARY"])
    manifest = json.loads(payloads["CURRENT_2A2_CENSUS_MANIFEST"])
    if type(summary) is not dict or type(manifest) is not dict:
        raise ValueError("CURRENT_CENSUS_JSON_DOCUMENT_INVALID")
    for path, expected in SUMMARY_VALUES:
        actual = _at(summary, path)
        if type(actual) is not type(expected) or actual != expected:
            raise ValueError("CURRENT_CENSUS_SUMMARY_VALUE_INVALID:" + ".".join(path))
    tasks = _at(summary, ("canonical_exact5", "tasks"))
    expected_tasks = [
        {
            "display_alias": alias,
            "semantic_name": name,
            "structurally_applicable_authoritative_role_count": count,
            "task_id": task_id,
        }
        for task_id, name, alias, count in EXPECTED_TASKS
    ]
    if tasks != expected_tasks:
        raise ValueError("CURRENT_CENSUS_EXACT5_INVALID")

    reader = csv.DictReader(
        io.StringIO(
            payloads["CURRENT_2A2_CENSUS_CSV"].decode("utf-8"), newline=""
        )
    )
    header = tuple(reader.fieldnames or ())
    if "pre_geometry_source_evidence_available" in header:
        raise ValueError("PRE_SOURCE_EVIDENCE_CSV_FIELD_UNEXPECTED")
    if not {
        "post_geometry_source_evidence_available",
        "post_geometry_sample_authoritative",
        "post_geometry_training_target_available",
        "pre_geometry_authoritative",
        "pre_geometry_training_target_available",
    }.issubset(header):
        raise ValueError("GEOMETRY_CSV_FIELDS_MISSING")
    rows = tuple(reader)
    if len(rows) != 1000:
        raise ValueError("CURRENT_CENSUS_ROWS_INVALID")

    global_counts = {
        "positive": sum(row["chemistry_disposition"] == "POSITIVE" for row in rows),
        "relevant": sum(row["task_relevance_disposition"] == "RELEVANT" for row in rows),
        "INCLUDE": sum(row["training_use_disposition"] == "INCLUDE" for row in rows),
        "EXCLUDE_FROM_TRAINING_ONLY": sum(row["training_use_disposition"] == "EXCLUDE_FROM_TRAINING_ONLY" for row in rows),
        "future_training_admission_candidate": sum(row["future_training_admission_candidate"] == "true" for row in rows),
        "sample_level_pair_authority": sum(row["reactive_pair_sample_authoritative"] == "true" for row in rows),
        "sample_level_role_authority": sum(row["role_partition_sample_authoritative"] == "true" for row in rows),
    }
    expected_global_counts = {
        "positive": 112,
        "relevant": 113,
        "INCLUDE": 44,
        "EXCLUDE_FROM_TRAINING_ONLY": 68,
        "future_training_admission_candidate": 27,
        "sample_level_pair_authority": 112,
        "sample_level_role_authority": 112,
    }
    if global_counts != expected_global_counts:
        raise ValueError("CURRENT_CENSUS_GLOBAL_COUNTS_INVALID")

    task_counts = {task_id: 0 for task_id, *_rest in EXPECTED_TASKS}
    for row in rows:
        ids = json.loads(row["structurally_applicable_task_ids_json"])
        if ids is not None:
            for task_id in ids:
                task_counts[task_id] += 1
    if task_counts != {task_id: count for task_id, _name, _alias, count in EXPECTED_TASKS}:
        raise ValueError("CURRENT_CENSUS_DIRECT_TASK_COUNTS_INVALID")
    canonical_tasks = {
        name: {
            "display_alias": alias,
            "structurally_applicable_authoritative_role_count": task_counts[task_id],
        }
        for task_id, name, alias, _count in EXPECTED_TASKS
    }

    completed_positive = tuple(
        row
        for row in rows
        if row["priority_review_in_scope"] == "true"
        and row["human_review_completed"] == "true"
        and row["chemistry_disposition"] == "POSITIVE"
    )
    completed_negative = tuple(
        row
        for row in rows
        if row["priority_review_in_scope"] == "true"
        and row["human_review_completed"] == "true"
        and row["chemistry_disposition"] == "NOT_ESTABLISHED"
    )
    unreviewed = tuple(
        row for row in rows if row["current_global_status"] == "CURRENTLY_UNREVIEWED"
    )
    human_review_counts = {
        "completed_positive_event_count": len(completed_positive),
        "completed_positive_unit_count": len(
            {row["review_unit_id"] for row in completed_positive}
        ),
        "completed_negative_event_count": len(completed_negative),
        "completed_negative_unit_count": len(
            {row["review_unit_id"] for row in completed_negative}
        ),
        "completed_event_count": len(completed_positive) + len(completed_negative),
        "completed_unit_count": len(
            {
                row["review_unit_id"]
                for row in (*completed_positive, *completed_negative)
            }
        ),
        "unreviewed_event_count": len(unreviewed),
        "unreviewed_unit_count": len(
            {row["review_unit_id"] for row in unreviewed}
        ),
    }
    if human_review_counts != {
        "completed_positive_event_count": 95,
        "completed_positive_unit_count": 13,
        "completed_negative_event_count": 24,
        "completed_negative_unit_count": 4,
        "completed_event_count": 119,
        "completed_unit_count": 17,
        "unreviewed_event_count": 219,
        "unreviewed_unit_count": 114,
    }:
        raise ValueError("CURRENT_CENSUS_HUMAN_REVIEW_COUNTS_INVALID")

    training_runtime_counts = {
        "formal_training_admitted_count": sum(
            row["formal_training_admitted"] == "true" for row in rows
        ),
        "current_runtime_model_usable_count": sum(
            row["current_runtime_model_usable"] == "true" for row in rows
        ),
    }
    if training_runtime_counts != {
        "formal_training_admitted_count": 5,
        "current_runtime_model_usable_count": 17,
    }:
        raise ValueError("CURRENT_CENSUS_TRAINING_RUNTIME_COUNTS_INVALID")

    geometry_counts = {
        "POST_source_evidence_available_count": sum(
            row["post_geometry_source_evidence_available"] == "true" for row in rows
        ),
        "POST_sample_authoritative_count": sum(
            row["post_geometry_sample_authoritative"] == "true" for row in rows
        ),
        "POST_training_target_available_count": sum(
            row["post_geometry_training_target_available"] == "true" for row in rows
        ),
        "PRE_source_evidence_available_count": _at(
            summary, ("geometry", "PRE_source_evidence_available_count")
        ),
        "PRE_sample_authoritative_count": sum(
            row["pre_geometry_authoritative"] == "true" for row in rows
        ),
        "PRE_training_target_available_count": sum(
            row["pre_geometry_training_target_available"] == "true" for row in rows
        ),
    }
    expected_geometry_counts = {
        "POST_source_evidence_available_count": 867,
        "POST_sample_authoritative_count": 21,
        "POST_training_target_available_count": 17,
        "PRE_source_evidence_available_count": 0,
        "PRE_sample_authoritative_count": 0,
        "PRE_training_target_available_count": 0,
    }
    if geometry_counts != expected_geometry_counts:
        raise ValueError("CURRENT_CENSUS_GEOMETRY_COUNTS_INVALID")
    for key in (
        "POST_source_evidence_available_count",
        "POST_sample_authoritative_count",
        "POST_training_target_available_count",
        "PRE_sample_authoritative_count",
        "PRE_training_target_available_count",
    ):
        if _at(summary, ("geometry", key)) != geometry_counts[key]:
            raise ValueError("GEOMETRY_CSV_SUMMARY_CROSS_CHECK_FAILED:" + key)

    output_bindings = manifest.get("output_bindings_excluding_manifest_self")
    if not isinstance(output_bindings, list) or [
        (item.get("path"), item.get("byte_count"), item.get("sha256"))
        for item in output_bindings
        if isinstance(item, dict)
    ] != [
        (CENSUS_SPECS[0][1], CENSUS_SPECS[0][2], CENSUS_SPECS[0][3]),
        (CENSUS_SPECS[1][1], CENSUS_SPECS[1][2], CENSUS_SPECS[1][3]),
    ]:
        raise ValueError("CURRENT_CENSUS_MANIFEST_BINDINGS_INVALID")
    return {
        "global_counts": global_counts,
        "canonical_tasks": canonical_tasks,
        "human_review_counts": human_review_counts,
        "training_runtime_counts": training_runtime_counts,
        "geometry_counts": geometry_counts,
        "task_counts": task_counts,
        "csv_header": header,
        "pre_source_evidence_semantics_distinct_from_sample_authority": (
            "pre_geometry_source_evidence_available" not in header
            and geometry_counts["PRE_source_evidence_available_count"]
            == _at(summary, ("geometry", "PRE_source_evidence_available_count"))
            and geometry_counts["PRE_sample_authoritative_count"]
            == sum(row["pre_geometry_authoritative"] == "true" for row in rows)
        ),
        "summary_field_paths_verified": [".".join(path) for path, _value in SUMMARY_VALUES],
    }


def _verify_result(
    result: Mapping[str, object],
    *,
    projections: Mapping[str, object],
    census: Mapping[str, object],
) -> bool:
    if tuple(result) != PUBLIC_RESULT_KEYS or len(result) != 29:
        raise ValueError("INTEGRATION_RESULT_KEY_INVENTORY_INVALID")
    expected_scalars = {
        "schema_version": "covapie_source_binding_active_consumer_integration_v2",
        "filesystem_source_acceptance_authority": "SOURCE_BINDING_POLICY_V2",
        "sample_scientific_projection_authority": "PUBLISHED_V1_ARTIFACTS",
        "current_global_state_authority": "PUBLISHED_2A2_V1_GLOBAL_CENSUS",
        "active_consumer_count": 6,
        "artifact_projection_count": 24,
        "all_V2_successor_sources_bound": True,
        "all_V2_projections_executed": True,
        "all_V1_scientific_projections_preserved": True,
        "current_2A2_census_bound": True,
        "current_2A2_census_unchanged": True,
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task_present": False,
        "scientific_authority_reinterpreted": False,
        "global_census_refreshed": False,
        "reconciliation_executed": False,
        "training_admission_created": False,
        "data_materialized": False,
        "v2_migration_phase_b2_effective_state_integrated": True,
        "ready_for_v2_migration_phase_b3_historical_immutability_proof": True,
        "ready_for_training": False,
    }
    for key, expected in expected_scalars.items():
        if result.get(key) != expected or type(result.get(key)) is not type(expected):
            raise ValueError("INTEGRATION_RESULT_INVALID:" + key)
    if result.get("active_consumer_order") != list(CONSUMERS):
        raise ValueError("INTEGRATION_RESULT_CONSUMER_ORDER_INVALID")
    expected_payloads = {
        "per_consumer_projection_digests": projections,
        "current_global_counts": census["global_counts"],
        "current_canonical_tasks": census["canonical_tasks"],
        "current_human_review_counts": census["human_review_counts"],
        "current_training_runtime_counts": census["training_runtime_counts"],
        "current_geometry_counts": census["geometry_counts"],
    }
    for key, expected in expected_payloads.items():
        if result.get(key) != expected:
            raise ValueError("INTEGRATION_RESULT_PAYLOAD_INVALID:" + key)
    return True


def run_check_v2(repo_root: Path = ROOT) -> dict[str, object]:
    root = repo_root.resolve()
    lifecycle = verify_git_lifecycle(root)
    exact4 = _verify_exact4_hygiene(root)
    _verify_public_api()
    _verify_production_ast(root)
    dependencies = _verify_published_dependencies(root)
    integration, captured = _verify_behavioral_order(root)
    projections = _verify_projection_artifacts(captured)
    census = _verify_census(root)
    public_result_verified = _verify_result(
        integration,
        projections=projections,
        census=census,
    )
    return {
        "lifecycle": lifecycle,
        "exact4": exact4,
        "dependencies": dependencies,
        "projections": projections,
        "census": census,
        "active_consumer_count": 6,
        "artifact_projection_count": 24,
        "all_v2_successor_sources_bound": True,
        "all_v2_projections_executed": True,
        "all_v1_scientific_projections_preserved": True,
        "current_2a2_census_unchanged": True,
        "effective_filesystem_source_binding_authority_v2": True,
        "published_v1_scientific_authority_preserved": True,
        "published_2a2_v1_global_state_authority_preserved": True,
        "global_canonical_task_count": 5,
        "B3_present": True,
        "sixth_task_present": False,
        "pre_source_evidence_semantics_distinct_from_sample_authority": census[
            "pre_source_evidence_semantics_distinct_from_sample_authority"
        ],
        "public_effective_state_result_fully_verified": public_result_verified,
        "v2_migration_phase_b2_effective_state_integrated": integration[
            "v2_migration_phase_b2_effective_state_integrated"
        ],
        "ready_for_v2_migration_phase_b3_historical_immutability_proof": True,
        "ready_for_training": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    result = run_check_v2(parser.parse_args().repo_root)
    required_true = (
        "all_v2_successor_sources_bound",
        "all_v2_projections_executed",
        "all_v1_scientific_projections_preserved",
        "current_2a2_census_unchanged",
        "effective_filesystem_source_binding_authority_v2",
        "published_v1_scientific_authority_preserved",
        "published_2a2_v1_global_state_authority_preserved",
        "B3_present",
        "pre_source_evidence_semantics_distinct_from_sample_authority",
        "public_effective_state_result_fully_verified",
        "v2_migration_phase_b2_effective_state_integrated",
        "ready_for_v2_migration_phase_b3_historical_immutability_proof",
    )
    if any(result[key] is not True for key in required_true):
        raise ValueError("CHECKER_REQUIRED_TRUE_ASSERTION_FAILED")
    if result["sixth_task_present"] is not False or result["ready_for_training"] is not False:
        raise ValueError("CHECKER_REQUIRED_FALSE_ASSERTION_FAILED")
    print("PASS")
    for key in (
        "lifecycle",
        "active_consumer_count",
        "artifact_projection_count",
        "all_v2_successor_sources_bound",
        "all_v2_projections_executed",
        "all_v1_scientific_projections_preserved",
        "current_2a2_census_unchanged",
        "effective_filesystem_source_binding_authority_v2",
        "published_v1_scientific_authority_preserved",
        "published_2a2_v1_global_state_authority_preserved",
        "global_canonical_task_count",
        "B3_present",
        "sixth_task_present",
        "pre_source_evidence_semantics_distinct_from_sample_authority",
        "public_effective_state_result_fully_verified",
        "v2_migration_phase_b2_effective_state_integrated",
        "ready_for_v2_migration_phase_b3_historical_immutability_proof",
        "ready_for_training",
    ):
        print(f"{key}={str(result[key]).lower() if isinstance(result[key], bool) else result[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
