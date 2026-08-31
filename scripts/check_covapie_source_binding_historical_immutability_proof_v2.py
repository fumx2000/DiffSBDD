#!/usr/bin/env python3
"""Check the read-only Phase-B3 historical immutability proof."""

from __future__ import annotations

import argparse
import ast
from collections import Counter
import csv
import hashlib
import inspect
import io
import json
from pathlib import Path, PurePosixPath
import stat
import subprocess

from covalent_ext import (
    covapie_source_binding_historical_immutability_proof_v2 as subject,
)
from covalent_ext import covapie_source_binding_policy_v2 as source_binding_v2


ROOT = Path(__file__).resolve().parents[1]
BASELINE_HEAD = "049d446e0fa854fab9986a9e2fb302d0b9547231"
BASELINE_TREE = "f4671ea46de9f0781e33be5778fd08aebdf8ce39"
BASELINE_SUBJECT = "add CovaPIE source binding active consumer integration v2"
PHASE_A_COMMIT = "26555ff6240ee53c817726331c8353dcb62dc82e"
PHASE_A_TREE = "24280fbf73dd8785268b64889193b4735b8ca875"
PHASE_A_SUBJECT = "add CovaPIE source binding filesystem mode authority v2 audit"
MAX_FILE_BYTES = 1024 * 1024

EXACT4_PATHS = (
    "src/covalent_ext/covapie_source_binding_historical_immutability_proof_v2.py",
    "scripts/check_covapie_source_binding_historical_immutability_proof_v2.py",
    "tests/test_covapie_source_binding_historical_immutability_proof_v2.py",
    "docs/covapie_source_binding_historical_immutability_proof_v2_guide.md",
)

MIGRATION_COMMITS = (
    (
        "94a59fef2922b8a450fe06538111ca62a0b78190",
        "add CovaPIE source binding policy v2",
    ),
    (
        "5a34e260e57598ab62905f0171e43a67acc188e2",
        "add CovaPIE YUN source binding successor v2",
    ),
    (
        "baab1358bcc8f776df20d8dc76ed476d51ba27f3",
        "add CovaPIE NEQ source binding successor v2",
    ),
    (
        "9e7d520de0baa5e5f107985f45b97f576bbd8fc0",
        "add CovaPIE CHT source binding successor v2",
    ),
    (
        "33d08ee6069592f0fe28ca53bed5615f578d10fc",
        "add CovaPIE OZJ source binding successor v2",
    ),
    (
        "a81be8b1260d14b385b0faf05e2ddcc56bd403d8",
        "add CovaPIE F24 source binding successor v2",
    ),
    (
        "1e77d93929e491e589060269416b34fe47c0fb15",
        "add CovaPIE 2A2 source binding successor v2",
    ),
    (BASELINE_HEAD, BASELINE_SUBJECT),
)

MIGRATION_EXACT32_PATHS = (
    "docs/covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2_guide.md",
    "docs/covapie_cht_completed_decision_ingestion_and_task_label_availability_v2_guide.md",
    "docs/covapie_f24_completed_decision_ingestion_and_task_label_availability_v2_guide.md",
    "docs/covapie_neq_completed_decision_ingestion_and_task_label_availability_v2_guide.md",
    "docs/covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2_guide.md",
    "docs/covapie_source_binding_active_consumer_integration_v2_guide.md",
    "docs/covapie_source_binding_policy_v2_guide.md",
    "docs/covapie_yun_completed_decision_ingestion_and_task_label_availability_v2_guide.md",
    "scripts/check_covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2.py",
    "scripts/check_covapie_cht_completed_decision_ingestion_and_task_label_availability_v2.py",
    "scripts/check_covapie_f24_completed_decision_ingestion_and_task_label_availability_v2.py",
    "scripts/check_covapie_neq_completed_decision_ingestion_and_task_label_availability_v2.py",
    "scripts/check_covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2.py",
    "scripts/check_covapie_source_binding_active_consumer_integration_v2.py",
    "scripts/check_covapie_source_binding_policy_v2.py",
    "scripts/check_covapie_yun_completed_decision_ingestion_and_task_label_availability_v2.py",
    "src/covalent_ext/covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2.py",
    "src/covalent_ext/covapie_cht_completed_decision_ingestion_and_task_label_availability_v2.py",
    "src/covalent_ext/covapie_f24_completed_decision_ingestion_and_task_label_availability_v2.py",
    "src/covalent_ext/covapie_neq_completed_decision_ingestion_and_task_label_availability_v2.py",
    "src/covalent_ext/covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2.py",
    "src/covalent_ext/covapie_source_binding_active_consumer_integration_v2.py",
    "src/covalent_ext/covapie_source_binding_policy_v2.py",
    "src/covalent_ext/covapie_yun_completed_decision_ingestion_and_task_label_availability_v2.py",
    "tests/test_covapie_2a2_completed_decision_ingestion_and_task_label_availability_v2.py",
    "tests/test_covapie_cht_completed_decision_ingestion_and_task_label_availability_v2.py",
    "tests/test_covapie_f24_completed_decision_ingestion_and_task_label_availability_v2.py",
    "tests/test_covapie_neq_completed_decision_ingestion_and_task_label_availability_v2.py",
    "tests/test_covapie_ozj_completed_decision_ingestion_and_task_label_availability_v2.py",
    "tests/test_covapie_source_binding_active_consumer_integration_v2.py",
    "tests/test_covapie_source_binding_policy_v2.py",
    "tests/test_covapie_yun_completed_decision_ingestion_and_task_label_availability_v2.py",
)

AUDIT_ROOT = (
    "data/derived/covalent_small/"
    "covapie_source_binding_filesystem_mode_authority_v2_audit"
)
INVENTORY_PATH = (
    AUDIT_ROOT + "/covapie_source_binding_filesystem_mode_authority_v2_inventory.csv"
)
SUMMARY_PATH = (
    AUDIT_ROOT + "/covapie_source_binding_filesystem_mode_authority_v2_summary.json"
)
MANIFEST_PATH = (
    AUDIT_ROOT + "/covapie_source_binding_filesystem_mode_authority_v2_manifest.json"
)
AUDIT_SPECS = (
    (
        "PHASE_A_INVENTORY",
        INVENTORY_PATH,
        927298,
        "1a883153737428482e7e49b95ba26ab1b6790d1ff2daf3697cceaa3a722d26da",
    ),
    (
        "PHASE_A_SUMMARY",
        SUMMARY_PATH,
        8728,
        "fe27c9e9aadbad76f8c330bf19286b840038cc0576b1a2de96fcd0546b5d10b0",
    ),
    (
        "PHASE_A_MANIFEST",
        MANIFEST_PATH,
        609232,
        "bdd86d533517972013b20397865079ce666562845bde19d03987d58ba676af2b",
    ),
)
PUBLISHED_SOURCE_SPECS = (
    (
        "SOURCE_BINDING_POLICY_V2",
        "src/covalent_ext/covapie_source_binding_policy_v2.py",
        3704,
        "c17f3532e6004b347ff62e5d354ac1843f384196c2207127e17971acd2e2d4ee",
    ),
    (
        "SOURCE_BINDING_ACTIVE_CONSUMER_INTEGRATION_V2",
        "src/covalent_ext/covapie_source_binding_active_consumer_integration_v2.py",
        33699,
        "42583a1b66c0a4a46ce653acdbd9e110f5988d39efc7a1ba3572bfc8b67c1022",
    ),
    (
        "SOURCE_BINDING_ACTIVE_CONSUMER_INTEGRATION_V2_CHECKER",
        "scripts/check_covapie_source_binding_active_consumer_integration_v2.py",
        44670,
        "067559e1d663ae707cffe2a73b74415a1a383d4dedc098c7d1c2affe8e6c7416",
    ),
)
ACTIVE_V1_TARGETS = (
    "scripts/check_covapie_2a2_completed_decision_ingestion_and_task_label_availability_v1.py",
    "scripts/check_covapie_f24_completed_decision_ingestion_and_task_label_availability_v1.py",
    "src/covalent_ext/covapie_2a2_completed_decision_ingestion_and_task_label_availability_v1.py",
    "src/covalent_ext/covapie_cht_completed_decision_ingestion_and_task_label_availability_v1.py",
    "src/covalent_ext/covapie_f24_completed_decision_ingestion_and_task_label_availability_v1.py",
    "src/covalent_ext/covapie_neq_completed_decision_ingestion_and_task_label_availability_v1.py",
    "src/covalent_ext/covapie_ozj_completed_decision_ingestion_and_task_label_availability_v1.py",
    "src/covalent_ext/covapie_yun_completed_decision_ingestion_and_task_label_availability_v1.py",
)
KNOWN_REGRESSION_SPECS = (
    (
        "published_role_profile_runtime_owner",
        "src/covalent_ext/covapie_direct_attachment_optional_linker_runtime_v1.py",
        37255,
        "434285a43fa0158e62d40f48ed95d137f5fd68ea9b00101cc20674025849c535",
        "0644",
    ),
    (
        "canonical_role_and_task_semantics_owner",
        "src/covalent_ext/"
        "covapie_ligand_role_and_minimal_seed_annotation_contract_design_v1.py",
        67274,
        "18e386ea0412d917d4e3d9f6c15374cdbd680ea243e7b51c0045ae889a215f8b",
        "0644",
    ),
    (
        "published_1f8_event_task_label_availability",
        "data/derived/covalent_small/"
        "covapie_1f8_completed_decision_ingestion_and_task_label_availability_v1/"
        "covapie_1f8_event_task_label_availability_v1.csv",
        14662,
        "63520f56ddb1c9fa9f962fc79c009549897e18299139e6b160498ca48080fb30",
        "0600",
    ),
)

SCAN_SCOPE_COUNTS = {
    "repository_python_files_scanned": 1199,
    "derived_json_files_inspected": 528,
    "external_authority_provenance_json_files_inspected": 14,
    "external_covapie_state_python_files_scanned": 14,
    "authority_provenance_json_files_inspected": 542,
    "total_files_scanned": 1755,
}
LIFECYCLE_COUNTS = {
    "ACTIVE_CURRENT_DEPENDENCY": 1576,
    "HISTORICAL_IMMUTABLE_V1": 261,
    "NEW_CURRENT_V2_REFERENCE": 0,
    "TEST_ONLY": 334,
    "DOCUMENTATION_ONLY": 0,
}
DISPOSITION_COUNTS = {
    "PRESERVE_AS_IS": 1979,
    "PRESERVE_HISTORICAL_BUT_DO_NOT_PROPAGATE": 180,
    "V2_MIGRATION_REQUIRED": 12,
    "REVIEW_REQUIRED": 0,
}
SEMANTIC_COUNTS = {
    "SEMANTIC_SOURCE_IDENTITY_EXACT_POSIX_MODE": 198,
    "SECURITY_HYGIENE_MODE_CHECK": 1295,
    "CANDIDATE_ARTIFACT_MODE_HYGIENE": 144,
    "GIT_EXECUTABLE_BIT_OR_FILE_CLASS_CONTRACT": 421,
    "REPORTING_OR_DIAGNOSTIC_MODE_METADATA": 113,
    "AMBIGUOUS_REQUIRES_HUMAN_REVIEW": 0,
}

PUBLIC_RESULT_KEYS = (
    "schema_version",
    "phase_a_audit_commit",
    "phase_b2_published_commit",
    "migration_commit_count",
    "migration_added_path_count",
    "migration_modified_path_count",
    "migration_deleted_path_count",
    "migration_renamed_path_count",
    "phase_a_scanned_source_binding_count",
    "repository_scanned_source_binding_count",
    "external_covapie_state_scanned_source_binding_count",
    "historical_immutable_occurrence_count",
    "preserve_historical_do_not_propagate_occurrence_count",
    "phase_a_v2_migration_required_occurrence_count",
    "ambiguous_review_required_occurrence_count",
    "active_v1_migration_target_file_count",
    "known_regression_reference_count",
    "historical_occurrence_source_unmapped_count",
    "preserve_historical_source_unmapped_count",
    "all_phase_a_scanned_source_bytes_unchanged",
    "all_repository_scanned_source_bytes_unchanged",
    "all_external_covapie_state_scanned_source_bytes_unchanged",
    "all_historical_immutable_occurrence_sources_unchanged",
    "all_preserve_historical_occurrence_sources_unchanged",
    "all_active_v1_migration_target_bytes_unchanged",
    "known_regression_reference_bytes_unchanged",
    "phase_a_audit_artifacts_unchanged",
    "filesystem_source_acceptance_authority",
    "sample_scientific_projection_authority",
    "current_global_state_authority",
    "historical_immutability_reference",
    "historical_v1_authority_modified",
    "historical_validator_rewrite_performed",
    "historical_exact_mode_metadata_rewritten",
    "historical_exact_mode_metadata_preserved",
    "scientific_authority_reinterpreted",
    "current_census_refreshed",
    "reconciliation_executed",
    "data_materialized",
    "b2_integration_verified",
    "active_consumer_count",
    "artifact_projection_count",
    "all_V2_successor_sources_bound",
    "all_V2_projections_executed",
    "all_V1_scientific_projections_preserved",
    "current_2A2_census_unchanged",
    "global_canonical_task_count",
    "B3_present",
    "sixth_task_present",
    "v2_migration_phase_b3_historical_immutability_proven",
    "ready_for_v2_migration_phase_b4_future_guard",
    "ready_for_training",
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _git(*arguments: str, root: Path, binary: bool = False) -> str | bytes:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode:
        raise ValueError("GIT_COMMAND_FAILED:" + arguments[0])
    if binary:
        return completed.stdout
    return completed.stdout.decode("utf-8").rstrip("\n")


def _git_blob(root: Path, commit: str, relative: str) -> bytes:
    payload = _git("show", f"{commit}:{relative}", root=root, binary=True)
    assert isinstance(payload, bytes)
    return payload


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
    baseline_identity = str(
        _git("show", "-s", "--format=%T%n%s", BASELINE_HEAD, root=root)
    ).splitlines()
    if baseline_identity != [BASELINE_TREE, BASELINE_SUBJECT]:
        raise ValueError("BASELINE_TREE_OR_SUBJECT_INVALID")
    tracked = set(
        filter(
            None,
            str(_git("ls-files", "--", *EXACT4_PATHS, root=root)).splitlines(),
        )
    )
    untracked = set(
        filter(
            None,
            str(
                _git("ls-files", "--others", "--exclude-standard", root=root)
            ).splitlines(),
        )
    )
    status = tuple(
        filter(
            None,
            str(
                _git(
                    "status",
                    "--porcelain=v1",
                    "--untracked-files=all",
                    root=root,
                )
            ).splitlines(),
        )
    )
    working = set(
        filter(None, str(_git("diff", "--name-only", root=root)).splitlines())
    )
    cached = set(
        filter(
            None,
            str(_git("diff", "--cached", "--name-only", root=root)).splitlines(),
        )
    )
    profile = classify_lifecycle_from_facts(
        tracked_exact4=tracked,
        ordinary_untracked=untracked,
        status_entries=status,
        working_diff=working,
        cached_diff=cached,
    )
    head = str(_git("rev-parse", "HEAD", root=root))
    origin_main = str(_git("rev-parse", "origin/main", root=root))
    relation = str(
        _git("rev-list", "--left-right", "--count", "HEAD...origin/main", root=root)
    ).split()
    if len(relation) != 2 or any(not item.isdigit() for item in relation):
        raise ValueError("REPOSITORY_RELATION_COUNT_INVALID")
    ahead, behind = (int(item) for item in relation)
    if profile == "TRACKED_CLEAN":
        parents = tuple(
            str(_git("show", "-s", "--format=%P", "HEAD", root=root)).split()
        )
        changed = set(
            filter(
                None,
                str(
                    _git(
                        "diff-tree",
                        "--no-commit-id",
                        "--name-only",
                        "-r",
                        "HEAD",
                        root=root,
                    )
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
            "sha256": _sha256(payload),
        }
    return result


def _verify_public_api_and_ast(root: Path) -> None:
    expected_api = (
        "SourceBindingHistoricalImmutabilityProofV2Error",
        "verify_covapie_source_binding_historical_immutability_proof_v2",
    )
    if subject.__all__ != expected_api:
        raise ValueError("PUBLIC_ALL_INVALID")
    signature = inspect.signature(
        subject.verify_covapie_source_binding_historical_immutability_proof_v2
    )
    parameters = tuple(signature.parameters.values())
    if not (
        len(parameters) == 1
        and parameters[0].name == "repo_root"
        and parameters[0].kind is inspect.Parameter.KEYWORD_ONLY
        and parameters[0].annotation == "Path"
        and signature.return_annotation == "dict[str, object]"
    ):
        raise ValueError("PUBLIC_VERIFIER_SIGNATURE_INVALID")
    public_names = {
        name
        for name, value in vars(subject).items()
        if not name.startswith("_")
        and (inspect.isclass(value) or inspect.isfunction(value))
        and getattr(value, "__module__", None) == subject.__name__
    }
    if public_names != set(expected_api):
        raise ValueError("PUBLIC_API_SURFACE_INVALID")

    production_path = root / EXACT4_PATHS[0]
    tree = ast.parse(production_path.read_bytes().decode("utf-8"))
    covalent_imports: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "covalent_ext":
            covalent_imports.update(alias.name for alias in node.names)
    if covalent_imports != {
        "covapie_source_binding_policy_v2",
        "covapie_source_binding_active_consumer_integration_v2",
    }:
        raise ValueError("PRODUCTION_IMPORT_BOUNDARY_INVALID")
    if any("_v1" in name for name in covalent_imports):
        raise ValueError("PRODUCTION_V1_IMPORT_FORBIDDEN")
    forbidden_calls = {
        "open",
        "write_bytes",
        "write_text",
        "mkdir",
        "rename",
        "replace",
        "unlink",
        "chmod",
        "materialize",
        "reconcile",
        "train",
        "fit",
    }
    calls = {
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, (ast.Attribute, ast.Name))
    }
    if calls & forbidden_calls:
        raise ValueError("PRODUCTION_MUTATION_OR_TRAINING_CALL_FORBIDDEN")
    if any(
        isinstance(node, ast.Attribute) and node.attr in {"S_IMODE", "st_mode"}
        for node in ast.walk(tree)
    ):
        raise ValueError("PRODUCTION_EXACT_NUMERIC_MODE_LOGIC_FORBIDDEN")
    if subject._ALLOWED_GIT_COMMANDS != frozenset(
        {"rev-parse", "merge-base", "rev-list", "show", "diff"}
    ):
        raise ValueError("PRODUCTION_GIT_ALLOWLIST_INVALID")


def _verify_history_and_delta(root: Path) -> dict[str, int | bool]:
    phase_a = str(
        _git("show", "-s", "--format=%T%n%s%n%P", PHASE_A_COMMIT, root=root)
    ).splitlines()
    if phase_a != [
        PHASE_A_TREE,
        PHASE_A_SUBJECT,
        "89a8cf17a235cdca9eecad275794a5a86be2e01d",
    ]:
        raise ValueError("PHASE_A_IDENTITY_INVALID")
    phase_b2 = str(
        _git("show", "-s", "--format=%T%n%s%n%P", BASELINE_HEAD, root=root)
    ).splitlines()
    if phase_b2 != [
        BASELINE_TREE,
        BASELINE_SUBJECT,
        "1e77d93929e491e589060269416b34fe47c0fb15",
    ]:
        raise ValueError("PHASE_B2_IDENTITY_INVALID")
    if str(_git("merge-base", PHASE_A_COMMIT, BASELINE_HEAD, root=root)) != (
        PHASE_A_COMMIT
    ):
        raise ValueError("PHASE_A_MERGE_BASE_INVALID")
    if str(
        _git(
            "rev-list",
            "--left-right",
            "--count",
            f"{PHASE_A_COMMIT}...{BASELINE_HEAD}",
            root=root,
        )
    ).split() != ["0", "8"]:
        raise ValueError("MIGRATION_AHEAD_BEHIND_INVALID")
    commits = tuple(
        filter(
            None,
            str(
                _git(
                    "rev-list",
                    "--reverse",
                    f"{PHASE_A_COMMIT}..{BASELINE_HEAD}",
                    root=root,
                )
            ).splitlines(),
        )
    )
    if commits != tuple(commit for commit, _subject in MIGRATION_COMMITS):
        raise ValueError("MIGRATION_COMMIT_CHAIN_INVALID")
    parent = PHASE_A_COMMIT
    for commit, expected_subject in MIGRATION_COMMITS:
        identity = str(
            _git("show", "-s", "--format=%P%n%s", commit, root=root)
        ).splitlines()
        if identity != [parent, expected_subject]:
            raise ValueError("MIGRATION_NOT_LINEAR:" + commit)
        parent = commit
    expected_rows = tuple("A\t" + path for path in MIGRATION_EXACT32_PATHS)
    rename_aware = tuple(
        filter(
            None,
            str(
                _git(
                    "diff",
                    "--name-status",
                    "-M",
                    "-C",
                    PHASE_A_COMMIT,
                    BASELINE_HEAD,
                    root=root,
                )
            ).splitlines(),
        )
    )
    no_renames = tuple(
        filter(
            None,
            str(
                _git(
                    "diff",
                    "--name-status",
                    "--no-renames",
                    PHASE_A_COMMIT,
                    BASELINE_HEAD,
                    root=root,
                )
            ).splitlines(),
        )
    )
    if rename_aware != expected_rows or no_renames != expected_rows:
        raise ValueError("MIGRATION_EXACT32_DELTA_INVALID")
    return {
        "migration_commit_count": len(commits),
        "migration_added_path_count": len(rename_aware),
        "migration_modified_path_count": 0,
        "migration_deleted_path_count": 0,
        "migration_renamed_path_count": 0,
        "exact_chain": True,
        "single_parent_linear": True,
        "exact32": True,
    }


def _bind(
    root: Path,
    *,
    label: str,
    relative: str,
    byte_count: int,
    sha256: str,
    expected_executable: bool | None,
) -> bytes:
    return source_binding_v2.verify_bound_source_v2(
        path=root / relative,
        expected_byte_count=byte_count,
        expected_sha256=sha256,
        label=label,
        expected_executable=expected_executable,
    )


def _resolve_binding(root: Path, record: dict[str, object]) -> Path:
    relative = record.get("path")
    namespace = record.get("path_namespace")
    if type(relative) is not str or type(namespace) is not str:
        raise ValueError("BINDING_PATH_OR_NAMESPACE_INVALID")
    pure = PurePosixPath(relative)
    if not relative or pure.is_absolute() or ".." in pure.parts:
        raise ValueError("BINDING_PATH_ESCAPE")
    if namespace == "repository_relative":
        allowed = root.resolve()
        path = root / Path(pure.as_posix())
    elif namespace == "repository_parent_relative":
        allowed = (root.parent / "covapie-state").resolve()
        path = root.parent / Path(pure.as_posix())
    else:
        raise ValueError("BINDING_NAMESPACE_INVALID")
    try:
        path.resolve().relative_to(allowed)
    except ValueError as error:
        raise ValueError("BINDING_ROOT_ESCAPE") from error
    return path


def _normalized_counts(
    rows: list[dict[str, str]], field: str, expected: dict[str, int]
) -> dict[str, int]:
    counts = Counter(row[field] for row in rows)
    if set(counts) - set(expected):
        raise ValueError("INVENTORY_ENUM_INVALID:" + field)
    return {name: counts.get(name, 0) for name in expected}


def _verify_frozen_provenance(root: Path) -> dict[str, object]:
    for label, relative, byte_count, sha256 in PUBLISHED_SOURCE_SPECS:
        _bind(
            root,
            label=label,
            relative=relative,
            byte_count=byte_count,
            sha256=sha256,
            expected_executable=False,
        )

    payloads: dict[str, bytes] = {}
    for label, relative, byte_count, sha256 in AUDIT_SPECS:
        phase_a = _git_blob(root, PHASE_A_COMMIT, relative)
        phase_b2 = _git_blob(root, BASELINE_HEAD, relative)
        current = _bind(
            root,
            label=label,
            relative=relative,
            byte_count=byte_count,
            sha256=sha256,
            expected_executable=None,
        )
        if (
            len(phase_a) != byte_count
            or _sha256(phase_a) != sha256
            or phase_b2 != phase_a
            or current != phase_a
        ):
            raise ValueError("PHASE_A_AUDIT_ARTIFACT_DRIFT:" + label)
        payloads[relative] = phase_a
    manifest = json.loads(payloads[MANIFEST_PATH].decode("utf-8"))
    summary = json.loads(payloads[SUMMARY_PATH].decode("utf-8"))
    if manifest.get("scan_scope_counts") != SCAN_SCOPE_COUNTS:
        raise ValueError("PHASE_A_SCAN_COUNTS_INVALID")
    scanned = manifest.get("scanned_source_bindings")
    if type(scanned) is not list or len(scanned) != 1755:
        raise ValueError("PHASE_A_BINDING_COUNT_INVALID")
    binding_fields = {
        "artifact_role",
        "path",
        "path_namespace",
        "byte_count",
        "sha256",
    }
    identities: set[tuple[str, str]] = set()
    namespace_counts: Counter[str] = Counter()
    for index, record in enumerate(scanned):
        if type(record) is not dict or set(record) != binding_fields:
            raise ValueError("PHASE_A_BINDING_SCHEMA_INVALID")
        namespace = record["path_namespace"]
        relative = record["path"]
        byte_count = record["byte_count"]
        sha256 = record["sha256"]
        if (
            type(namespace) is not str
            or type(relative) is not str
            or type(byte_count) is not int
            or type(sha256) is not str
        ):
            raise ValueError("PHASE_A_BINDING_VALUE_INVALID")
        identity = (namespace, relative)
        if identity in identities:
            raise ValueError("PHASE_A_BINDING_DUPLICATE")
        path = _resolve_binding(root, record)
        source_binding_v2.verify_bound_source_v2(
            path=path,
            expected_byte_count=byte_count,
            expected_sha256=sha256,
            label=f"CHECKER_PHASE_A_SOURCE_{index}",
            expected_executable=None,
        )
        identities.add(identity)
        namespace_counts[namespace] += 1
    if namespace_counts != {
        "repository_relative": 1727,
        "repository_parent_relative": 28,
    }:
        raise ValueError("PHASE_A_NAMESPACE_COUNTS_INVALID")

    reader = csv.DictReader(
        io.StringIO(payloads[INVENTORY_PATH].decode("utf-8"), newline="")
    )
    rows = list(reader)
    if len(rows) != 2171:
        raise ValueError("PHASE_A_OCCURRENCE_COUNT_INVALID")
    if _normalized_counts(rows, "lifecycle_class", LIFECYCLE_COUNTS) != (
        LIFECYCLE_COUNTS
    ):
        raise ValueError("PHASE_A_LIFECYCLE_COUNTS_INVALID")
    if _normalized_counts(rows, "debt_disposition", DISPOSITION_COUNTS) != (
        DISPOSITION_COUNTS
    ):
        raise ValueError("PHASE_A_DISPOSITION_COUNTS_INVALID")
    if _normalized_counts(rows, "semantic_class", SEMANTIC_COUNTS) != (
        SEMANTIC_COUNTS
    ):
        raise ValueError("PHASE_A_SEMANTIC_COUNTS_INVALID")
    all_occurrence_identities = {
        (row["source_path_namespace"], row["source_path"]) for row in rows
    }
    historical_identities = {
        (row["source_path_namespace"], row["source_path"])
        for row in rows
        if row["lifecycle_class"] == "HISTORICAL_IMMUTABLE_V1"
    }
    preserve_identities = {
        (row["source_path_namespace"], row["source_path"])
        for row in rows
        if row["debt_disposition"]
        == "PRESERVE_HISTORICAL_BUT_DO_NOT_PROPAGATE"
    }
    if not all_occurrence_identities <= identities:
        raise ValueError("PHASE_A_OCCURRENCE_SOURCE_UNMAPPED")
    if historical_identities - identities or preserve_identities - identities:
        raise ValueError("PHASE_A_HISTORICAL_SOURCE_UNMAPPED")

    inventory_counts = summary.get("inventory_counts")
    if type(inventory_counts) is not dict or (
        inventory_counts.get("active_v2_migration_target_files")
        != list(ACTIVE_V1_TARGETS)
    ):
        raise ValueError("PHASE_A_ACTIVE_TARGET_INVENTORY_INVALID")
    for relative in ACTIVE_V1_TARGETS:
        phase_a = _git_blob(root, PHASE_A_COMMIT, relative)
        phase_b2 = _git_blob(root, BASELINE_HEAD, relative)
        if phase_a != phase_b2:
            raise ValueError("ACTIVE_V1_TARGET_GIT_DRIFT:" + relative)
        _bind(
            root,
            label="CHECKER_ACTIVE_V1_TARGET:" + relative,
            relative=relative,
            byte_count=len(phase_a),
            sha256=_sha256(phase_a),
            expected_executable=None,
        )

    cases = summary.get("known_regression_cases")
    if type(cases) is not list or len(cases) != 3:
        raise ValueError("KNOWN_REGRESSION_CASES_NOT_EXACT3")
    if [case.get("expected_mode") for case in cases] != ["0644", "0644", "0600"]:
        raise ValueError("HISTORICAL_EXACT_MODE_METADATA_DRIFT")
    if [case.get("source_role") for case in cases] != [
        spec[0] for spec in KNOWN_REGRESSION_SPECS
    ]:
        raise ValueError("KNOWN_REGRESSION_ROLE_DRIFT")
    for _role, relative, byte_count, sha256, _historical_mode in (
        KNOWN_REGRESSION_SPECS
    ):
        phase_a = _git_blob(root, PHASE_A_COMMIT, relative)
        phase_b2 = _git_blob(root, BASELINE_HEAD, relative)
        if (
            phase_a != phase_b2
            or len(phase_a) != byte_count
            or _sha256(phase_a) != sha256
        ):
            raise ValueError("KNOWN_REGRESSION_GIT_DRIFT:" + relative)
        _bind(
            root,
            label="CHECKER_KNOWN_REGRESSION:" + relative,
            relative=relative,
            byte_count=byte_count,
            sha256=sha256,
            expected_executable=None,
        )

    return {
        "phase_a_scanned_source_binding_count": len(scanned),
        "repository_scanned_source_binding_count": namespace_counts[
            "repository_relative"
        ],
        "external_covapie_state_scanned_source_binding_count": namespace_counts[
            "repository_parent_relative"
        ],
        "historical_immutable_occurrence_count": LIFECYCLE_COUNTS[
            "HISTORICAL_IMMUTABLE_V1"
        ],
        "preserve_historical_do_not_propagate_occurrence_count": (
            DISPOSITION_COUNTS["PRESERVE_HISTORICAL_BUT_DO_NOT_PROPAGATE"]
        ),
        "phase_a_v2_migration_required_occurrence_count": DISPOSITION_COUNTS[
            "V2_MIGRATION_REQUIRED"
        ],
        "ambiguous_review_required_occurrence_count": 0,
        "active_v1_migration_target_file_count": len(ACTIVE_V1_TARGETS),
        "known_regression_reference_count": len(KNOWN_REGRESSION_SPECS),
        "historical_occurrence_source_unmapped_count": 0,
        "preserve_historical_source_unmapped_count": 0,
        "all_phase_a_scanned_source_bytes_unchanged": True,
        "all_repository_scanned_source_bytes_unchanged": True,
        "all_external_covapie_state_scanned_source_bytes_unchanged": True,
        "all_historical_immutable_occurrence_sources_unchanged": True,
        "all_active_v1_migration_target_bytes_unchanged": True,
        "known_regression_reference_bytes_unchanged": True,
        "phase_a_audit_artifacts_unchanged": True,
        "historical_exact_mode_metadata_preserved": True,
    }


def _verify_subject_behavior(root: Path) -> tuple[dict[str, object], int]:
    original = subject.integration_v2.verify_covapie_source_binding_active_consumer_integration_v2
    calls = 0

    def recording_integration(*, repo_root: Path) -> dict[str, object]:
        nonlocal calls
        calls += 1
        return original(repo_root=repo_root)

    subject.integration_v2.verify_covapie_source_binding_active_consumer_integration_v2 = (
        recording_integration
    )
    try:
        result = subject.verify_covapie_source_binding_historical_immutability_proof_v2(
            repo_root=root
        )
    finally:
        subject.integration_v2.verify_covapie_source_binding_active_consumer_integration_v2 = (
            original
        )
    if calls != 1:
        raise ValueError("PUBLISHED_B2_INTEGRATION_CALL_COUNT_INVALID")
    if tuple(result) != PUBLIC_RESULT_KEYS:
        raise ValueError("PUBLIC_RESULT_KEYS_INVALID")
    expected_scalars = {
        "schema_version": "covapie_source_binding_historical_immutability_proof_v2",
        "phase_a_audit_commit": PHASE_A_COMMIT,
        "phase_b2_published_commit": BASELINE_HEAD,
        "migration_commit_count": 8,
        "migration_added_path_count": 32,
        "migration_modified_path_count": 0,
        "migration_deleted_path_count": 0,
        "migration_renamed_path_count": 0,
        "phase_a_scanned_source_binding_count": 1755,
        "repository_scanned_source_binding_count": 1727,
        "external_covapie_state_scanned_source_binding_count": 28,
        "historical_immutable_occurrence_count": 261,
        "preserve_historical_do_not_propagate_occurrence_count": 180,
        "phase_a_v2_migration_required_occurrence_count": 12,
        "ambiguous_review_required_occurrence_count": 0,
        "active_v1_migration_target_file_count": 8,
        "known_regression_reference_count": 3,
        "historical_occurrence_source_unmapped_count": 0,
        "preserve_historical_source_unmapped_count": 0,
        "filesystem_source_acceptance_authority": "SOURCE_BINDING_POLICY_V2",
        "sample_scientific_projection_authority": "PUBLISHED_V1_ARTIFACTS",
        "current_global_state_authority": "PUBLISHED_2A2_V1_GLOBAL_CENSUS",
        "historical_immutability_reference": (
            "PHASE_A_AUDIT_FROZEN_SOURCE_BINDINGS"
        ),
        "active_consumer_count": 6,
        "artifact_projection_count": 24,
        "global_canonical_task_count": 5,
    }
    for key, expected in expected_scalars.items():
        if result.get(key) != expected or type(result.get(key)) is not type(expected):
            raise ValueError("PUBLIC_RESULT_SCALAR_INVALID:" + key)
    required_true = {
        "all_phase_a_scanned_source_bytes_unchanged",
        "all_repository_scanned_source_bytes_unchanged",
        "all_external_covapie_state_scanned_source_bytes_unchanged",
        "all_historical_immutable_occurrence_sources_unchanged",
        "all_preserve_historical_occurrence_sources_unchanged",
        "all_active_v1_migration_target_bytes_unchanged",
        "known_regression_reference_bytes_unchanged",
        "phase_a_audit_artifacts_unchanged",
        "historical_exact_mode_metadata_preserved",
        "b2_integration_verified",
        "all_V2_successor_sources_bound",
        "all_V2_projections_executed",
        "all_V1_scientific_projections_preserved",
        "current_2A2_census_unchanged",
        "B3_present",
        "v2_migration_phase_b3_historical_immutability_proven",
        "ready_for_v2_migration_phase_b4_future_guard",
    }
    required_false = {
        "historical_v1_authority_modified",
        "historical_validator_rewrite_performed",
        "historical_exact_mode_metadata_rewritten",
        "scientific_authority_reinterpreted",
        "current_census_refreshed",
        "reconciliation_executed",
        "data_materialized",
        "sixth_task_present",
        "ready_for_training",
    }
    if any(result.get(key) is not True for key in required_true):
        raise ValueError("PUBLIC_RESULT_REQUIRED_TRUE_INVALID")
    if any(result.get(key) is not False for key in required_false):
        raise ValueError("PUBLIC_RESULT_REQUIRED_FALSE_INVALID")
    return result, calls


def run_check_v2(repo_root: Path = ROOT) -> dict[str, object]:
    root = repo_root.resolve()
    lifecycle = verify_git_lifecycle(root)
    exact4 = _verify_exact4_hygiene(root)
    _verify_public_api_and_ast(root)
    history = _verify_history_and_delta(root)
    provenance = _verify_frozen_provenance(root)
    public_result, b2_calls = _verify_subject_behavior(root)
    for key, value in {**history, **provenance}.items():
        if key in public_result and public_result[key] != value:
            raise ValueError("INDEPENDENT_CHECK_DISAGREES_WITH_PUBLIC_RESULT:" + key)
    return {
        "lifecycle": lifecycle,
        "exact4": exact4,
        **history,
        **provenance,
        "historical_exact_mode_metadata_rewritten": False,
        "historical_validator_rewrite_performed": False,
        "b2_integration_verified": public_result["b2_integration_verified"],
        "b2_integration_call_count": b2_calls,
        "active_consumer_count": public_result["active_consumer_count"],
        "artifact_projection_count": public_result["artifact_projection_count"],
        "all_V1_scientific_projections_preserved": public_result[
            "all_V1_scientific_projections_preserved"
        ],
        "current_2A2_census_unchanged": public_result[
            "current_2A2_census_unchanged"
        ],
        "global_canonical_task_count": public_result[
            "global_canonical_task_count"
        ],
        "B3_present": public_result["B3_present"],
        "sixth_task_present": public_result["sixth_task_present"],
        "v2_migration_phase_b3_historical_immutability_proven": public_result[
            "v2_migration_phase_b3_historical_immutability_proven"
        ],
        "ready_for_v2_migration_phase_b4_future_guard": public_result[
            "ready_for_v2_migration_phase_b4_future_guard"
        ],
        "ready_for_training": public_result["ready_for_training"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    result = run_check_v2(parser.parse_args().repo_root)
    required_true = (
        "exact_chain",
        "single_parent_linear",
        "exact32",
        "all_phase_a_scanned_source_bytes_unchanged",
        "all_repository_scanned_source_bytes_unchanged",
        "all_external_covapie_state_scanned_source_bytes_unchanged",
        "all_historical_immutable_occurrence_sources_unchanged",
        "all_active_v1_migration_target_bytes_unchanged",
        "known_regression_reference_bytes_unchanged",
        "phase_a_audit_artifacts_unchanged",
        "historical_exact_mode_metadata_preserved",
        "b2_integration_verified",
        "all_V1_scientific_projections_preserved",
        "current_2A2_census_unchanged",
        "B3_present",
        "v2_migration_phase_b3_historical_immutability_proven",
        "ready_for_v2_migration_phase_b4_future_guard",
    )
    if any(result[key] is not True for key in required_true):
        raise ValueError("CHECKER_REQUIRED_TRUE_ASSERTION_FAILED")
    if (
        result["historical_exact_mode_metadata_rewritten"] is not False
        or result["historical_validator_rewrite_performed"] is not False
        or result["sixth_task_present"] is not False
        or result["ready_for_training"] is not False
    ):
        raise ValueError("CHECKER_REQUIRED_FALSE_ASSERTION_FAILED")
    print("PASS")
    for key in (
        "lifecycle",
        "migration_commit_count",
        "migration_added_path_count",
        "migration_modified_path_count",
        "migration_deleted_path_count",
        "phase_a_scanned_source_binding_count",
        "repository_scanned_source_binding_count",
        "external_covapie_state_scanned_source_binding_count",
        "historical_immutable_occurrence_count",
        "preserve_historical_do_not_propagate_occurrence_count",
        "active_v1_migration_target_file_count",
        "known_regression_reference_count",
        "all_phase_a_scanned_source_bytes_unchanged",
        "all_repository_scanned_source_bytes_unchanged",
        "all_external_covapie_state_scanned_source_bytes_unchanged",
        "all_historical_immutable_occurrence_sources_unchanged",
        "all_active_v1_migration_target_bytes_unchanged",
        "known_regression_reference_bytes_unchanged",
        "historical_exact_mode_metadata_rewritten",
        "historical_validator_rewrite_performed",
        "b2_integration_verified",
        "global_canonical_task_count",
        "B3_present",
        "sixth_task_present",
        "v2_migration_phase_b3_historical_immutability_proven",
        "ready_for_v2_migration_phase_b4_future_guard",
        "ready_for_training",
    ):
        value = result[key]
        print(f"{key}={str(value).lower() if isinstance(value, bool) else value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
