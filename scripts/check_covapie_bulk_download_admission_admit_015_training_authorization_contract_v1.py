#!/usr/bin/env python3
"""Independent fail-closed checker for ADMIT_015 training authorization v1."""
from __future__ import annotations

import ast
import csv
import hashlib
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE = "4fb86e7d6b8cd27258362cae34eec196b117c265"
PARENT = "f54c0efabfb695653c9e55b3a53bda8cf200f353"
TREE = "2a447517ce601e9440a7c1523866d459b192870c"
SUBJECT = "add CovaPIE ADMIT_015 formal evaluator interface preconditions audit v1"
STAGE = "covapie_bulk_download_admission_admit_015_training_authorization_contract_v1"
PRODUCTION = Path(
    "src/covalent_ext/"
    "covapie_bulk_download_admission_admit_015_training_authorization_contract.py"
)
CHECKER = Path(
    "scripts/"
    "check_covapie_bulk_download_admission_admit_015_training_authorization_contract_v1.py"
)
TEST = Path(
    "tests/"
    "test_covapie_bulk_download_admission_admit_015_training_authorization_contract_v1.py"
)
SUMMARY = Path(
    "docs/"
    "covapie_bulk_download_admission_admit_015_training_authorization_contract_v1_summary.md"
)
DERIVED = Path("data/derived/covalent_small") / STAGE
CONTRACT = "covapie_admit_015_training_authorization_contract.csv"
TRUTH = "covapie_admit_015_training_authorization_truth_matrix.csv"
VALUE = "covapie_admit_015_training_authorization_value_and_trust_contract.csv"
SAFETY = "covapie_admit_015_training_authorization_safety_boundary_audit.csv"
ISSUE = "covapie_admit_015_issue_readiness_inventory.csv"
MANIFEST = "covapie_admit_015_training_authorization_contract_manifest.json"
FILES = (CONTRACT, TRUTH, VALUE, SAFETY, ISSUE, MANIFEST)
EXACT10 = (PRODUCTION, CHECKER, TEST, SUMMARY, *(DERIVED / name for name in FILES))
PRODUCTION_SHA256 = "77d278f6c0666d9843c86151bb8189836639e89f93b9488c92c5e7169a3d76e1"
PRODUCTION_AST_SHA256 = "e297ae12df6f8b232a61ec82b4a0c8099e6517c1e55eae9bd2acbe600753c37d"
FROZEN_OUTPUT_SHA256 = {
    CONTRACT: "d8cdc33a8debac9959563047b54a0975c5318c09ffefc3b69b9025e8e768254d",
    TRUTH: "bc1070cb7df2db7ee05c4c8aa21ea9563a08974b620d44ee42c193c63b4fb37b",
    VALUE: "eab6be6568b3a8a8fba298eab6fff052184922a70b2893663311d437c6735d7e",
    SAFETY: "ed6fb5650716c9135157393eff6b8882781c063c569a5be5aafc550c249969d0",
    ISSUE: "f457da61bffade18999af5c069d237c30aa30a0c63efb8bb14130935fb0757ec",
    MANIFEST: "16ea4bb5f781c6f6d8277fb4142258c2bee4849b942582e48692373caee5cda1",
}

EXACT18 = (
    ("src/covalent_ext/covapie_bulk_download_admission_admit_015_formal_evaluator_interface_preconditions_audit.py", "18894150a91040b3a4c52a5f7aaedc279f6f31ededed82de1e704ec086e0cc0f"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_015_formal_evaluator_interface_precondition_inventory.csv", "c52287ac5a435e58a400be0e33e17c1096b7b0d3b2671be0398a6be03e409839"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_015_authorization_evidence_and_routing_responsibility_matrix.csv", "9713eb3ebfa474488269d17f9efff39e953405dc1d9642074a203e4837585e95"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_015_source_boundary_audit.csv", "d34374760edf3432042588eb1f258ab75e75290d8a75be579f6056352ef5cd89"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_015_safety_training_boundary_audit.csv", "967f5d22503b552ae2aaf34693799e789cbc38209d80ad1f4dd0e42bfd87587d"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_015_issue_readiness_inventory.csv", "f457da61bffade18999af5c069d237c30aa30a0c63efb8bb14130935fb0757ec"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_015_formal_evaluator_interface_preconditions_audit_v1/covapie_admit_015_formal_evaluator_interface_preconditions_manifest.json", "7f64389a018c9bc1170ffeb94d1f393aefc27f67edef1d85143659f43dc8d729"),
    ("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_design_gate_v1/covapie_bulk_download_admission_rule_registry.csv", "9b16919a08d166a8daf223c7b6a04078ae10aa00206daefc18f2c5a5060783fc"),
    ("data/derived/covalent_small/covapie_canonical_final_dataset_bulk_download_admission_implementation_precondition_gate_v1/covapie_bulk_download_admission_evaluation_context_contract.csv", "1146ba9f7dce648726b54401ece8e7f5e94e9feea8057ab29d4fea8a8bf6f8b0"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_014_download_authorization_contract_v1/covapie_admit_014_download_authorization_truth_matrix.csv", "e4f39f5178b91906639670f5c1ddb1c02b40c802de9ce386aee2a6b6d49f8482"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_014_download_authorization_contract_v1/covapie_admit_014_download_authorization_value_and_trust_contract.csv", "b22f02efdd53dce995730a05cc5c12ffa659c2d98b345afc663b118cc104752d"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_admit_014_download_authorization_contract_v1/covapie_admit_014_download_authorization_contract_manifest.json", "9c54c9d6cb11776b04938d9be048699041bfc4020dca4c00425faadaaaa5d4d2"),
    ("src/covalent_ext/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014.py", "c5f5cfc57155f34ee2435228b3bf53ae8d1f6d81c32e097c43668c0b272fd1a2"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014_v1/covapie_admit_001_to_014_runtime_manifest.json", "bf7bbe3c2158f661c6e71835bf603af76ffbb315d4ef377c9f72da246619ba40"),
    ("data/derived/covalent_small/covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_014_v1/covapie_admit_001_to_014_runtime_issue_readiness_inventory.csv", "f457da61bffade18999af5c069d237c30aa30a0c63efb8bb14130935fb0757ec"),
    ("data/derived/covalent_small/covapie_final_dataset_qa_gate_v1/covapie_final_dataset_qa_v1_manifest.json", "4f7c884379f926af52101f40a7870b243f0309af3b1637dc65c8c0691acf9f35"),
    ("data/derived/covalent_small/covapie_feature_semantics_audit_gate_v0/covapie_feature_semantics_audit_gate_manifest.json", "a625335dd670ceb53f1515237a676c25d156b510eb80113ea8c4073e1ae1879d"),
    ("data/derived/covalent_small/pretrained_masked_loss_smoke_v0/pretrained_masked_loss_smoke_manifest.json", "f2b3165d70c046f27defbe821afcc5294ff5cdf0037595cd5c42066ab27ea08b"),
)

CONTRACT_COLUMNS = (
    "routing_order", "routing_item", "envelope_or_stage", "authority_status",
    "access_or_enforcement_contract", "expected_behavior", "observed_design",
    "routing_passed",
)
TRUTH_COLUMNS = (
    "case_order", "case_id", "case_group", "stage_context_representation",
    "forbidden_envelope_representation", "expected_outcome",
    "observed_outcome", "expected_reason", "observed_reason",
    "target_key_access_count", "mapping_iteration_count", "mapping_len_count",
    "mapping_get_count", "mapping_contains_count",
    "forbidden_envelope_access_count", "case_passed",
)
VALUE_COLUMNS = (
    "contract_order", "contract_item", "contract_group", "expected_contract",
    "observed_contract", "responsibility_owner", "contract_passed",
)
SAFETY_COLUMNS = (
    "audit_order", "audit_item", "required_state", "observed_state",
    "audit_passed", "blocking_reason",
)
REASONS = (
    "", "STAGE_AUTHORIZATION_CONTEXT_REQUIRED",
    "STAGE_AUTHORIZATION_CONTEXT_MAPPING_INVALID",
    "CURRENT_STAGE_TRAINING_AUTHORIZED_MISSING",
    "STAGE_AUTHORIZATION_CONTEXT_LOOKUP_FAILED",
    "CURRENT_STAGE_TRAINING_AUTHORIZED_TYPE_INVALID",
    "TRAINING_NOT_AUTHORIZED",
)
RESOLVED_PRE = (
    "PRE_007", "PRE_008", "PRE_009", "PRE_010", "PRE_011", "PRE_012",
    "PRE_016", "PRE_017", "PRE_018", "PRE_025", "PRE_026", "PRE_027",
)
OPEN_PRE = (
    "PRE_019", "PRE_020", "PRE_021", "PRE_022", "PRE_023", "PRE_024",
    "PRE_031", "PRE_032", "PRE_033", "PRE_034", "PRE_035", "PRE_036",
    "PRE_038", "PRE_042",
)
TRUE_READINESS = (
    "admit_015_preconditions_audited",
    "admit_015_training_authorization_contract_frozen",
    "admit_015_authoritative_envelope_frozen",
    "admit_015_authoritative_key_frozen",
    "admit_015_exact_bool_contract_frozen",
    "admit_015_no_coercion_contract_frozen",
    "admit_015_failure_precedence_frozen",
    "admit_015_outcome_reason_vocabulary_frozen",
    "admit_014_admit_015_isolation_contract_frozen",
    "ready_for_admit_015_formal_evaluator_interface_contract_design",
    "feature_semantics_audit_required_before_training",
)
FALSE_READINESS = (
    "admit_015_formal_evaluator_interface_contract_frozen",
    "evaluate_admit_015_implemented",
    "admit_015_result_type_implemented",
    "admit_015_independent_oracle_implemented",
    "admit_015_standalone_evaluator_implemented",
    "admit_015_unified_adapter_contract_frozen",
    "admit_015_unified_adapter_implemented",
    "admit_015_registered_in_engine",
    "unified_dispatch_runtime_with_admit_001_to_015_implemented",
    "mandatory_training_authorization_enforcement_api_frozen",
    "mandatory_training_authorization_enforcement_implemented",
    "combined_candidate_verdict_implemented",
    "cross_rule_aggregation_implemented",
    "feature_semantics_audit_completed",
    "real_training_ready",
    "ready_for_training",
    "step12d_is_final_training_feature_contract",
)
FORBIDDEN_SUFFIXES = {
    ".pt", ".ckpt", ".pth", ".pkl", ".lmdb", ".tar", ".zip",
    ".tgz", ".npz", ".tmp", ".part",
}
Identity = tuple[int, int, int, int, int, int]


@dataclass(frozen=True)
class Source:
    path: Path
    content: bytes
    sha256: str
    mode: str
    blob: str


def _identity(item: os.stat_result) -> Identity:
    return (
        item.st_dev, item.st_ino, item.st_mode, item.st_size,
        item.st_mtime_ns, item.st_ctime_ns,
    )


def _git(args: list[str], *, text: bool = True) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=text, check=False
    )


def _pinned_read(path: Path) -> bytes:
    if (
        path.is_absolute() or not path.parts or ".." in path.parts
        or path.parts[:2] == ("data", "raw") or path.parts[0] == "checkpoints"
    ):
        raise AssertionError(f"unsafe path: {path}")
    dflags = (
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    )
    fflags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    root_stat = os.lstat(ROOT)
    root_id = _identity(root_stat)
    root_fd = os.open(ROOT, dflags)
    held = [(root_fd, root_id, None, None)]
    leaf_fd = -1
    try:
        if _identity(os.fstat(root_fd)) != root_id:
            raise AssertionError("root race")
        current = root_fd
        for part in path.parts[:-1]:
            before = os.stat(part, dir_fd=current, follow_symlinks=False)
            before_id = _identity(before)
            if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
                raise AssertionError(f"unsafe parent: {path}")
            child = os.open(part, dflags, dir_fd=current)
            if _identity(os.fstat(child)) != before_id:
                os.close(child)
                raise AssertionError(f"parent race: {path}")
            held.append((child, before_id, current, part))
            current = child
        before = os.stat(path.name, dir_fd=current, follow_symlinks=False)
        leaf_id = _identity(before)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
            raise AssertionError(f"unsafe leaf: {path}")
        leaf_fd = os.open(path.name, fflags, dir_fd=current)
        if _identity(os.fstat(leaf_fd)) != leaf_id:
            raise AssertionError(f"leaf race: {path}")
        chunks = []
        while True:
            chunk = os.read(leaf_fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        if (
            _identity(os.fstat(leaf_fd)) != leaf_id
            or _identity(
                os.stat(path.name, dir_fd=current, follow_symlinks=False)
            )
            != leaf_id
        ):
            raise AssertionError(f"pinned leaf post-read replacement: {path}")
        for fd, expected, parent_fd, name in held:
            if _identity(os.fstat(fd)) != expected:
                raise AssertionError(f"pinned parent FD drift: {path}")
            if parent_fd is not None and name is not None:
                if _identity(
                    os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
                ) != expected:
                    raise AssertionError(f"pinned parent lexical drift: {path}")
        if (
            _identity(os.fstat(root_fd)) != root_id
            or _identity(os.lstat(ROOT)) != root_id
            or _identity(os.fstat(leaf_fd)) != leaf_id
            or _identity(
                os.stat(path.name, dir_fd=current, follow_symlinks=False)
            )
            != leaf_id
        ):
            raise AssertionError(f"pinned final binding drift: {path}")
        return b"".join(chunks)
    finally:
        if leaf_fd >= 0:
            os.close(leaf_fd)
        for fd, _, _, _ in reversed(held):
            os.close(fd)


def attest_exact18() -> tuple[Source, ...]:
    identity = _git(["show", "-s", "--format=%H%n%P%n%T%n%s", BASE])
    ancestor = _git(["merge-base", "--is-ancestor", BASE, "HEAD"])
    if identity.returncode or ancestor.returncode or identity.stdout.splitlines() != [
        BASE, PARENT, TREE, SUBJECT
    ]:
        raise AssertionError("base identity/ancestry mismatch")
    result = []
    for path_text, expected_sha in EXACT18:
        path = Path(path_text)
        index = _git(["ls-files", "--stage", "--", path_text])
        tree = _git(["ls-tree", BASE, "--", path_text])
        ih, isep, ip = index.stdout.partition("\t")
        th, tsep, tp = tree.stdout.partition("\t")
        iv, tv = ih.split(), th.split()
        if (
            index.returncode or tree.returncode or not isep or not tsep
            or ip.strip() != path_text or tp.strip() != path_text
            or len(iv) != 3 or len(tv) != 3 or iv[2] != "0"
            or iv[0] not in {"100644", "100755"} or tv[0] != iv[0]
            or tv[1] != "blob" or tv[2] != iv[1]
        ):
            raise AssertionError(f"Exact18 base/index mismatch: {path}")
        content = _pinned_read(path)
        base = _git(["show", f"{BASE}:{path_text}"], text=False)
        digest = hashlib.sha256(content).hexdigest()
        if base.returncode or base.stdout != content or digest != expected_sha:
            raise AssertionError(f"Exact18 content mismatch: {path}")
        result.append(Source(path, content, digest, iv[0], iv[1]))
    return tuple(result)


def _parse_csv(data: bytes, columns: tuple[str, ...]) -> list[dict[str, str]]:
    table = list(csv.reader(io.StringIO(data.decode(), newline="")))
    if not table or tuple(table[0]) != columns:
        raise AssertionError("CSV schema mismatch")
    if any(len(row) != len(columns) for row in table[1:]):
        raise AssertionError("CSV width mismatch")
    return [dict(zip(columns, row)) for row in table[1:]]


def _csv_bytes(columns: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=columns, extrasaction="raise", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def _expected_contract_rows() -> list[dict[str, str]]:
    specs = (
        ("only authority", "stage_authorization_context", "authoritative", "ordered target __getitem__ only", "consume training target key once"),
        ("candidate source", "candidate_record", "forbidden", "zero access", "cannot authorize or override"),
        ("batch source", "batch_context", "forbidden", "zero access", "cannot authorize or override"),
        ("evaluation source", "evaluation_context", "forbidden", "zero access", "cannot authorize or override"),
        ("download-result source", "download_result_context", "forbidden", "zero access", "cannot authorize or override"),
        ("provider source", "provider_result", "forbidden", "zero access", "cannot authorize"),
        ("candidate self-report", "candidate_self_report", "forbidden", "zero access", "cannot authorize"),
        ("environment source", "environment_variable", "forbidden", "zero access", "cannot authorize"),
        ("filesystem/raw source", "filesystem_marker|raw_file", "forbidden", "zero access", "cannot authorize"),
        ("artifact/Git source", "artifact_sha256|git_commit_sha", "forbidden", "zero access", "cannot authorize"),
        ("manifest/fixture source", "manifest_self_report|test_fixture", "forbidden", "zero access", "cannot authorize"),
        ("checkpoint/config/CLI source", "checkpoint_metadata|training_config|CLI_flag", "forbidden", "zero access", "cannot authorize"),
        ("model/dataloader source", "model_state|dataloader_state", "forbidden", "zero access", "cannot authorize"),
        ("ADMIT_014 permission", "current_stage_download_authorized", "forbidden", "zero training-authority access", "download True never authorizes training"),
        ("extra stage keys", "stage_authorization_context", "allowed", "do not iterate/len/get/contains", "target-only lookup"),
        ("missing context", "stage_authorization_context", "fail_closed", "no fallback/default", REASONS[1]),
        ("invalid context", "stage_authorization_context", "fail_closed", "Mapping required", REASONS[2]),
        ("missing key", "current_stage_training_authorized", "fail_closed", "first KeyError classified missing", REASONS[3]),
        ("lookup exception", "current_stage_training_authorized", "fail_closed", "non-KeyError classified lookup failed", REASONS[4]),
        ("invalid type", "current_stage_training_authorized", "fail_closed", "exact built-in bool required", REASONS[5]),
        ("false permission", "current_stage_training_authorized", "authoritative", "hard block", REASONS[6]),
        ("true permission", "current_stage_training_authorized", "authoritative", "permission verdict only", "synthetic design pass only"),
        ("download True", "current_stage_download_authorized", "isolated", "no fallback/alias", "training remains missing or controlled by training key"),
        ("training True", "current_stage_training_authorized", "isolated", "ADMIT_014 must not consume", "download permission unchanged"),
        ("cross-key OR", "download|training", "forbidden", "no combined permission", "undefined"),
        ("cross-key AND", "download|training", "forbidden", "not a single permission", "undefined"),
        ("current permission", "current project state", "false", "synthetic True cannot change it", "training_not_authorized"),
        ("authorized execution count", "current project state", "0", "no training invocation", "0"),
        ("future stage-global guard", "real-training invocation", "future_mandatory", "evaluate once per invocation", "before protected operations"),
        ("dataloader instantiation", "pre-training", "protected action", "future ADMIT_015 pass required", "blocked count=0"),
        ("checkpoint loading", "pre-training", "protected action", "future ADMIT_015 pass required", "blocked count=0"),
        ("model initialization/forward", "pre-training", "protected action", "future ADMIT_015 pass required", "blocked count=0"),
        ("loss/backward", "pre-training", "protected action", "future ADMIT_015 pass required", "blocked count=0"),
        ("optimizer/scheduler creation", "pre-training", "protected action", "future ADMIT_015 pass required", "blocked count=0"),
        ("parameter update", "pre-training", "protected action", "future ADMIT_015 pass required", "blocked count=0"),
        ("training checkpoint write", "pre-training", "protected action", "future ADMIT_015 pass required", "blocked count=0"),
        ("training result materialization", "pre-training", "protected action", "future ADMIT_015 pass required", "blocked count=0"),
        ("aggregation independence", "combined verdict", "not_implemented", "blocked cannot be overridden", "cross-rule aggregation undefined"),
        ("enforcement API", "future training orchestration", "not_frozen", "responsibility only", "implementation absent"),
        ("pass limitation", "ADMIT_015 design pass", "permission_only", "no current readiness implication", "feature-semantics audit remains required"),
    )
    return [
        dict(zip(CONTRACT_COLUMNS, (
            str(index), item, envelope, status, access, behavior, behavior, "true",
        )))
        for index, (item, envelope, status, access, behavior)
        in enumerate(specs, 1)
    ]


def _expected_value_rows() -> list[dict[str, str]]:
    specs = (
        ("authoritative envelope", "authority", "stage_authorization_context", "evaluator"),
        ("authoritative key", "authority", "current_stage_training_authorized", "evaluator"),
        ("exact value type", "value", "type(value) is bool", "evaluator"),
        ("closed value vocabulary", "value", "False|True", "evaluator"),
        ("false semantics", "value", "blocked|TRAINING_NOT_AUTHORIZED", "evaluator"),
        ("true semantics", "value", "passed|empty reason", "evaluator"),
        ("normalization", "value", "forbidden", "evaluator"),
        ("truthiness coercion", "value", "forbidden; bool(value) not used", "evaluator"),
        ("integer coercion", "value", "forbidden", "evaluator"),
        ("string coercion", "value", "forbidden", "evaluator"),
        ("numpy.bool_ coercion", "value", "forbidden", "evaluator"),
        ("producer boundary", "trust", "trusted_future_stage_orchestrator", "trusted caller"),
        ("trust source", "trust", "invocation boundary; not mapping self-report", "trusted caller"),
        ("invocation lifetime", "freshness", "invocation-local", "trusted caller"),
        ("explicit reconstruction", "freshness", "required for every stage invocation", "trusted caller"),
        ("previous invocation replay", "freshness", "forbidden", "trusted caller"),
        ("artifact/cache/raw replay", "freshness", "forbidden", "trusted caller"),
        ("identity authentication", "trust", "outside evaluator", "future orchestration"),
        ("signature verification", "trust", "outside evaluator", "future orchestration"),
        ("cryptographic authentication", "trust", "outside evaluator", "future orchestration"),
        ("download key isolation", "isolation", "never training authority", "evaluator"),
        ("training key isolation", "isolation", "never download authority", "ADMIT_014 evaluator"),
        ("fallback/alias/OR/AND", "isolation", "all forbidden", "future orchestration"),
        ("evaluator responsibility", "responsibility", "consume and validate one exact bool", "evaluator"),
        ("caller responsibility", "responsibility", "construct fresh trusted stage context", "trusted caller"),
        ("orchestration responsibility", "responsibility", "enforce trust boundary and future pre-training guard", "future orchestration"),
    )
    return [
        dict(zip(VALUE_COLUMNS, (
            str(index), item, group, value, value, owner, "true",
        )))
        for index, (item, group, value, owner) in enumerate(specs, 1)
    ]


def _expected_safety_rows() -> list[dict[str, str]]:
    specs = (
        ("current training permission", "false", "false", "training_not_authorized"),
        ("authorized training execution count", "0", "0", "training_not_authorized"),
        ("ADMIT_015 evaluator", "absent", "absent", ""),
        ("ADMIT_015 result type", "absent", "absent", ""),
        ("ADMIT_015 independent oracle", "absent", "absent", ""),
        ("ADMIT_015 standalone evaluator", "absent", "absent", ""),
        ("ADMIT_015 adapter/handler", "absent", "absent", ""),
        ("ADMIT_015 registry/Exact15 runtime", "absent", "absent", ""),
        ("mandatory enforcement API frozen", "false", "false", ""),
        ("mandatory enforcement implemented", "false", "false", ""),
        ("blocked dataloader instantiation count", "0", "0", ""),
        ("blocked checkpoint load count", "0", "0", ""),
        ("blocked model forward count", "0", "0", ""),
        ("blocked loss count", "0", "0", ""),
        ("blocked backward count", "0", "0", ""),
        ("blocked optimizer creation count", "0", "0", ""),
        ("blocked parameter update count", "0", "0", ""),
        ("blocked checkpoint write count", "0", "0", ""),
        ("provider/network/download", "false", "false", ""),
        ("raw structure read/write", "false", "false", ""),
        ("feature semantics audit completed", "false", "false", "feature_semantics_audit_required"),
        ("Step12D final contract", "false", "false", "step12d_smoke_only"),
        ("ready for training", "false", "false", "training_not_authorized"),
        ("combined verdict", "not implemented", "not implemented", ""),
        ("cross-rule aggregation", "not implemented", "not implemented", ""),
        ("canonical mask count", "5", "5", ""),
        ("canonical mask warhead_only/A", "present", "present", ""),
        ("canonical mask linker_plus_warhead/B", "present", "present", ""),
        ("canonical mask scaffold_plus_warhead/B2", "present", "present", ""),
        ("canonical mask scaffold_only/B3", "present", "present", ""),
        ("canonical mask scaffold_plus_linker_plus_warhead/C", "present", "present", ""),
    )
    return [
        dict(zip(SAFETY_COLUMNS, (
            str(index), item, required, observed, "true", reason,
        )))
        for index, (item, required, observed, reason) in enumerate(specs, 1)
    ]


def _expected_truth_rows(sources: tuple[Source, ...]) -> list[dict[str, str]]:
    precedent = _parse_csv(sources[9].content, TRUTH_COLUMNS)
    rows = []
    for row in precedent:
        expected = dict(row)
        representation = expected["stage_context_representation"]
        if expected["case_id"] == "ADMIT015_PLUS_TRUE":
            representation = (
                "{'current_stage_download_authorized': False, "
                "'current_stage_training_authorized': True}"
            )
        elif expected["case_id"] == "ADMIT015_PLUS_FALSE":
            representation = (
                "{'current_stage_download_authorized': True, "
                "'current_stage_training_authorized': False}"
            )
        else:
            representation = representation.replace(
                "current_stage_download_authorized",
                "current_stage_training_authorized",
            )
        expected["stage_context_representation"] = representation
        for key in ("expected_reason", "observed_reason"):
            expected[key] = (
                expected[key]
                .replace(
                    "CURRENT_STAGE_DOWNLOAD_AUTHORIZED",
                    "CURRENT_STAGE_TRAINING_AUTHORIZED",
                )
                .replace("BULK_DOWNLOAD_NOT_AUTHORIZED", "TRAINING_NOT_AUTHORIZED")
            )
        rows.append(expected)
    if [row["case_id"] for row in rows] != [
        row["case_id"] for row in precedent
    ]:
        raise AssertionError("ADMIT_014 literal case identity drift")
    return rows


def _expected_transition(
    sources: tuple[Source, ...],
) -> tuple[list[dict[str, str]], str]:
    columns = tuple(next(csv.reader(io.StringIO(sources[1].content.decode()))))
    inherited = _parse_csv(sources[1].content, columns)
    rows = [dict(row) for row in inherited]
    resolved = set(RESOLVED_PRE)
    for before, row in zip(inherited, rows):
        if row["precondition_id"] in resolved:
            row["observed_state"] = (
                "frozen by ADMIT_015 training authorization contract v1"
            )
            row["completion_status"] = "complete"
            row["implementation_blocking"] = "false"
            row["resolution_or_gap"] = "authorization contract frozen"
        elif row != before:
            raise AssertionError("non-Exact12 transition drift")
    if not (
        len(rows) == 45
        and sum(row["completion_status"] == "complete" for row in rows) == 31
        and sum(
            row["completion_status"]
            == "supported_but_admit015_contract_not_frozen"
            for row in rows
        ) == 0
        and sum(row["completion_status"] == "incomplete" for row in rows) == 14
        and sum(row["implementation_blocking"] == "true" for row in rows) == 14
        and [
            row["precondition_id"] for row in rows
            if row["completion_status"] != "complete"
        ] == list(OPEN_PRE)
    ):
        raise AssertionError("independent Exact45 transition mismatch")
    digest = hashlib.sha256(_csv_bytes(columns, rows)).hexdigest()
    return rows, digest


def _duplicate_rejecting_hook(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if type(key) is not str or key in result:
            raise AssertionError("duplicate or invalid JSON key")
        result[key] = value
    return result


def _parse_manifest_exact(
    data: bytes,
    expected: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        document = json.loads(
            data.decode(), object_pairs_hook=_duplicate_rejecting_hook
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise AssertionError("manifest JSON invalid") from error
    if type(document) is not dict:
        raise AssertionError("manifest object required")
    if expected is not None:
        _assert_exact_object(document, expected, "manifest")
    return document


def _assert_exact_object(actual: Any, expected: Any, path: str) -> None:
    if type(actual) is not type(expected):
        raise AssertionError(f"{path} exact type mismatch")
    if type(expected) is dict:
        if tuple(actual) != tuple(expected):
            raise AssertionError(f"{path} exact schema/order mismatch")
        for key in expected:
            _assert_exact_object(actual[key], expected[key], f"{path}.{key}")
    elif type(expected) is list:
        if len(actual) != len(expected):
            raise AssertionError(f"{path} list length mismatch")
        for index, (left, right) in enumerate(zip(actual, expected)):
            _assert_exact_object(left, right, f"{path}[{index}]")
    elif actual != expected:
        raise AssertionError(f"{path} value mismatch")


def _expected_manifest(
    payloads: dict[str, bytes],
    sources: tuple[Source, ...],
    truth: list[dict[str, str]],
    transition_sha: str,
) -> dict[str, Any]:
    issues = sources[5].content
    readiness = {
        **{key: True for key in TRUE_READINESS},
        **{key: False for key in FALSE_READINESS},
    }
    groups = {
        group: sum(row["case_group"] == group for row in truth)
        for group in dict.fromkeys(row["case_group"] for row in truth)
    }
    output_sha = {
        name: hashlib.sha256(payloads[name]).hexdigest() for name in FILES[:-1]
    }
    manifest: dict[str, Any] = {
        "project": "CovaPIE",
        "stage": STAGE,
        "manifest_schema_version":
            "covapie_admit_015_training_authorization_contract_manifest_v1",
        "base_commit": BASE,
        "base_parent": PARENT,
        "base_tree": TREE,
        "base_subject": SUBJECT,
        "canonical_evidence_python_implementation": "cpython",
        "canonical_evidence_python_version": "3.10.4",
        "ast_attestation_cross_python_version_portable": False,
        "noncanonical_python_policy":
            "evaluator_semantic_smoke_only; artifact_build_checker_and_frozen_ast_forbidden",
        "python_runtime_migration_policy": "explicit_contract_refresh_required",
        "admission_rule_identity": {
            "admission_rule_id": "ADMIT_015",
            "admission_rule_name": "current_gate_grants_no_training_permission",
            "evidence_source": "current_design_gate",
            "required_status": "training_not_authorized_now",
            "failure_severity": "blocking",
            "blocking_reason": "training_not_authorized",
            "evaluation_phase": "current_step",
            "authorization_model": "future_explicit_authorization_context",
        },
        "authorization_contract": {
            "authoritative_envelope": "stage_authorization_context",
            "authoritative_key": "current_stage_training_authorized",
            "context_scope": "stage",
            "producer_boundary": "trusted_future_stage_orchestrator",
            "exact_builtin_type": "bool",
            "closed_value_vocabulary": [False, True],
            "normalization_or_coercion_allowed": False,
            "default_or_fallback_allowed": False,
            "forbidden_envelopes": [
                "candidate_record", "batch_context", "evaluation_context",
                "download_result_context",
            ],
            "forbidden_pseudo_authorities": [
                "candidate_record", "batch_context", "evaluation_context",
                "download_result_context", "provider_result",
                "candidate_self_report", "environment_variable",
                "filesystem_marker", "raw_file", "artifact_sha256",
                "git_commit_sha", "manifest_self_report", "test_fixture",
                "checkpoint_metadata", "training_config", "CLI_flag",
                "model_state", "dataloader_state",
                "ADMIT_014_download_permission",
            ],
        },
        "trust_boundary": {
            "trust_from_call_boundary_not_mapping_string": True,
            "context_invocation_local": True,
            "caller_reconstructs_every_invocation": True,
            "previous_invocation_replay_allowed": False,
            "artifact_cache_raw_replay_allowed": False,
            "cryptographic_authentication_in_evaluator_scope": False,
        },
        "download_training_isolation_contract": {
            "download_true_authorizes_training": False,
            "training_true_authorizes_download": False,
            "fallback_allowed": False,
            "alias_allowed": False,
            "or_allowed": False,
            "and_as_single_permission_allowed": False,
            "training_missing_reads_download_key": False,
            "future_admit_015_consumes_download_key": False,
            "admit_014_consumes_training_key": False,
            "combined_permission_semantics_defined": False,
            "cross_rule_aggregation_implemented": False,
        },
        "outcome_vocabulary": ["passed", "blocked"],
        "reason_vocabulary": list(REASONS),
        "failure_precedence": list(REASONS[1:] + ("",)),
        "truth_matrix_schema": list(TRUTH_COLUMNS),
        "truth_matrix_row_count": 40,
        "truth_matrix_group_counts": groups,
        "truth_matrix_all_cases_passed": True,
        "forbidden_envelope_access_count": 0,
        "current_permission": False,
        "authorized_admit_015_training_execution_count": 0,
        "synthetic_true_design_case_grants_current_permission": False,
        "synthetic_true_design_case_starts_real_training": False,
        "ready_for_training_now": False,
        "formal_interface_not_frozen": {
            "final_evaluator_signature": True,
            "final_result_class_name": True,
            "final_result_field_order": True,
            "independent_oracle": True,
            "standalone_evaluator": True,
            "unified_adapter": True,
            "registry_and_exact15_runtime": True,
        },
        "future_mandatory_training_authorization_responsibility": {
            "evaluate_once_each_real_training_invocation": True,
            "must_complete_before_any_protected_operation": True,
            "blocked_must_not_continue": True,
            "combined_verdict_may_override_blocked": False,
            "must_precede": [
                "dataloader instantiation", "checkpoint loading",
                "training model initialization", "model forward",
                "loss computation", "backward",
                "optimizer/scheduler creation", "parameter update",
                "training checkpoint write", "training-result materialization",
            ],
            "blocked_dataloader_instantiation_count": 0,
            "blocked_checkpoint_load_count": 0,
            "blocked_model_forward_count": 0,
            "blocked_loss_count": 0,
            "blocked_backward_count": 0,
            "blocked_optimizer_creation_count": 0,
            "blocked_parameter_update_count": 0,
            "blocked_checkpoint_write_count": 0,
            "api_frozen": False,
            "implemented": False,
        },
        "precondition_transition": {
            "row_count": 45,
            "complete_count": 31,
            "supported_but_not_frozen_count": 0,
            "incomplete_count": 14,
            "implementation_blocking_count": 14,
            "resolved_precondition_ids": list(RESOLVED_PRE),
            "remaining_open_precondition_ids": list(OPEN_PRE),
            "transition_rows_sha256": transition_sha,
        },
        "issue_continuity": {
            "row_count": 30,
            "transition_count": 0,
            "inventory_source_sha256": EXACT18[5][1],
            "byte_identical_to_preconditions_and_exact14": True,
            "coverage": ["ADMIT_015"],
            "coverage_issue_open": True,
        },
        "source_count": 18,
        "source_boundary_schema": [
            "order", "path", "sha256", "base_tree_mode", "base_tree_blob",
            "index_mode", "index_blob", "index_stage",
            "base_tree_filesystem_byte_equal", "pinned_no_follow_read",
            "final_leaf_fd_retained",
        ],
        "source_boundary": [
            {
                "order": index,
                "path": source.path.as_posix(),
                "sha256": source.sha256,
                "base_tree_mode": source.mode,
                "base_tree_blob": source.blob,
                "index_mode": source.mode,
                "index_blob": source.blob,
                "index_stage": 0,
                "base_tree_filesystem_byte_equal": True,
                "pinned_no_follow_read": True,
                "final_leaf_fd_retained": True,
            }
            for index, source in enumerate(sources, 1)
        ],
        "readiness": readiness,
        "canonical_masks": [
            {"semantic_name": "warhead_only", "alias": "A"},
            {"semantic_name": "linker_plus_warhead", "alias": "B"},
            {"semantic_name": "scaffold_plus_warhead", "alias": "B2"},
            {"semantic_name": "scaffold_only", "alias": "B3"},
            {
                "semantic_name": "scaffold_plus_linker_plus_warhead",
                "alias": "C",
            },
        ],
        "canonical_mask_count": 5,
        "canonical_mask_long_names_are_authoritative": True,
        "feature_semantics_audit_completed": False,
        "feature_semantics_audit_required_before_training": True,
        "historical_unknown_atom_feature_policy_resolved": False,
        "historical_feature_semantics_known": False,
        "step12d_status":
            "smoke_legality_only_not_final_training_feature_contract",
        "safety": {
            "formal_evaluator_or_result": False,
            "oracle_adapter_registry_exact15_runtime": False,
            "mandatory_enforcement_implementation": False,
            "dataloader": False,
            "checkpoint": False,
            "model": False,
            "forward": False,
            "loss": False,
            "backward": False,
            "optimizer": False,
            "parameter_update": False,
            "training_checkpoint_write": False,
            "provider": False,
            "network": False,
            "download": False,
            "raw_read_or_write": False,
            "real_training": False,
        },
        "exact6_schemas": {
            CONTRACT: list(CONTRACT_COLUMNS),
            TRUTH: list(TRUTH_COLUMNS),
            VALUE: list(VALUE_COLUMNS),
            SAFETY: list(SAFETY_COLUMNS),
            ISSUE: next(csv.reader(io.StringIO(issues.decode()))),
            MANIFEST: "closed JSON contract asserted by independent checker",
        },
        "exact6_row_counts": {
            CONTRACT: 40,
            TRUTH: 40,
            VALUE: 26,
            SAFETY: 31,
            ISSUE: 30,
        },
        "output_files": list(FILES),
        "output_file_count": 6,
        "output_sha256": output_sha,
        "output_sha256_excludes_manifest_self_hash": True,
        "materialization": {
            "build_before_mutation": True,
            "exclusive_leaf_create": True,
            "rename_noreplace_required": True,
            "gpfs_einval_fails_closed": True,
            "os_replace_forbidden": True,
            "inode_preserving_exact_noop": True,
            "pinned_post_read_verification": True,
            "source_final_leaf_fd_retained": True,
            "output_final_set_traversal": True,
            "staging_lexical_binding_verified": True,
            "ownership_safe_cleanup": True,
            "failure_cleanup_is_non_destructive": True,
            "failure_cleanup_unlink_forbidden": True,
            "failure_cleanup_rmdir_forbidden": True,
            "failure_staging_may_be_retained": True,
            "concurrent_eexist_fails_closed": True,
            "preexisting_exact_destination_is_noop": True,
            "successful_publish_has_no_staging_residue": True,
            "unknown_identity_objects_are_never_deleted": True,
            "nested_exact_bool_types_verified": True,
            "bool_int_equivalence_rejected": True,
            "ignored_extra_stage_artifacts_rejected": True,
            "extra_derived_roots_rejected": True,
        },
        "recommended_next_step":
            "design_covapie_admit_015_formal_evaluator_interface_contract_v1",
        "all_checks_passed": True,
    }
    manifest.update(readiness)
    return manifest


def verify_exact6_semantics(
    payloads: dict[str, bytes],
    sources: tuple[Source, ...] | None = None,
) -> dict[str, Any]:
    frozen_sources = attest_exact18() if sources is None else sources
    if tuple(payloads) != FILES:
        raise AssertionError("Exact6 name/order mismatch")
    for name in FILES:
        if hashlib.sha256(payloads[name]).hexdigest() != FROZEN_OUTPUT_SHA256[name]:
            raise AssertionError(f"frozen output SHA mismatch: {name}")
    expected_contract = _expected_contract_rows()
    expected_truth = _expected_truth_rows(frozen_sources)
    expected_value = _expected_value_rows()
    expected_safety = _expected_safety_rows()
    _, transition_sha = _expected_transition(frozen_sources)
    if _parse_csv(payloads[CONTRACT], CONTRACT_COLUMNS) != expected_contract:
        raise AssertionError("Contract Exact40 independent rebuild mismatch")
    if _parse_csv(payloads[TRUTH], TRUTH_COLUMNS) != expected_truth:
        raise AssertionError("Truth Exact40 independent rebuild mismatch")
    if _parse_csv(payloads[VALUE], VALUE_COLUMNS) != expected_value:
        raise AssertionError("Value/trust Exact26 independent rebuild mismatch")
    if _parse_csv(payloads[SAFETY], SAFETY_COLUMNS) != expected_safety:
        raise AssertionError("Safety Exact31 independent rebuild mismatch")
    if payloads[ISSUE] != frozen_sources[5].content:
        raise AssertionError("Issue Exact30 byte identity mismatch")
    issues = _parse_csv(
        payloads[ISSUE],
        tuple(next(csv.reader(io.StringIO(payloads[ISSUE].decode())))),
    )
    if len(issues) != 30:
        raise AssertionError("Issue Exact30 row count mismatch")
    expected_manifest = _expected_manifest(
        payloads, frozen_sources, expected_truth, transition_sha
    )
    actual_manifest = _parse_manifest_exact(
        payloads[MANIFEST], expected_manifest
    )
    if MANIFEST in actual_manifest["output_sha256"]:
        raise AssertionError("manifest self hash forbidden")
    return actual_manifest


def _verify_ast() -> None:
    data = _pinned_read(PRODUCTION)
    tree = ast.parse(data.decode())
    normalized = ast.dump(tree, annotate_fields=True, include_attributes=False)
    if (
        hashlib.sha256(data).hexdigest() != PRODUCTION_SHA256
        or hashlib.sha256(normalized.encode()).hexdigest() != PRODUCTION_AST_SHA256
    ):
        raise AssertionError("production SHA/AST mismatch")
    functions = {
        node.name for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    classes = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
    forbidden_functions = {
        "evaluate_admit_015", "_evaluate_registered_admit_015",
        "evaluate_admission_rule", "train", "fit", "backward", "optimizer",
    }
    if functions & forbidden_functions or "Admit015EvaluationResult" in classes:
        raise AssertionError("premature evaluator/result/runtime implementation")
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    if imports & {
        "torch", "numpy", "pytorch_lightning", "rdkit",
        "equivariant_diffusion", "dataset", "lightning_modules",
    }:
        raise AssertionError("forbidden model/training import")
    if "os.replace" in data.decode():
        raise AssertionError("os.replace forbidden")


def _load_production() -> Any:
    spec = importlib.util.spec_from_file_location("admit015_auth_candidate", ROOT / PRODUCTION)
    if spec is None or spec.loader is None:
        raise AssertionError("production import unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(spec.name, None)
    return module


def _read_exact6() -> dict[str, bytes]:
    return {name: _pinned_read(DERIVED / name) for name in FILES}


def _check_ignore(path: Path) -> bool:
    result = _git(["check-ignore", "--no-index", "-q", "--", path.as_posix()])
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    raise AssertionError(f"git check-ignore failed closed: {path}")


STAGE_FAMILY_TOKENS = (
    "covapie_bulk_download_admission_admit_015_"
    "training_authorization_contract",
    "covapie_admit_015_training_authorization_contract",
    "covapie_admit_015_training_authorization_truth_matrix",
    "covapie_admit_015_training_authorization_value_and_trust_contract",
    "covapie_admit_015_training_authorization_safety_boundary_audit",
    "covapie_admit_015_issue_readiness_inventory",
)
STAGE_FAMILY_SCAN_ROOTS = (
    Path("src/covalent_ext"),
    Path("scripts"),
    Path("tests"),
    Path("docs"),
)


def _is_stage_family_name(name: str) -> bool:
    candidate = name.lstrip(".")
    return any(token in candidate for token in STAGE_FAMILY_TOKENS)


def _is_stage_family_path(path: Path) -> bool:
    return _is_stage_family_name(path.as_posix())


def _scan_bounded_stage_root(
    scan_root: Path,
    discovered: set[Path],
) -> None:
    pending = [scan_root]
    while pending:
        current = pending.pop()
        try:
            entries = tuple(os.scandir(ROOT / current))
        except OSError as error:
            raise AssertionError(
                f"stage-family scan unavailable: {current}"
            ) from error
        for entry in entries:
            relative = current / entry.name
            if entry.is_symlink():
                raise AssertionError(
                    f"symlink blocks no-follow stage-family scan: {relative}"
                )
            if _is_stage_family_path(relative):
                discovered.add(relative)
            if entry.is_dir(follow_symlinks=False):
                pending.append(relative)


def _filesystem_stage_family() -> set[Path]:
    """Find stage-family paths independently of Git ignore visibility."""
    discovered: set[Path] = set()
    for scan_root in STAGE_FAMILY_SCAN_ROOTS:
        _scan_bounded_stage_root(scan_root, discovered)
    derived_parent = DERIVED.parent
    try:
        derived_entries = tuple(os.scandir(ROOT / derived_parent))
    except OSError as error:
        raise AssertionError("derived stage-family scan unavailable") from error
    for entry in derived_entries:
        if not _is_stage_family_name(entry.name):
            continue
        relative = derived_parent / entry.name
        discovered.add(relative)
        if entry.is_symlink():
            raise AssertionError(f"symlink derived stage-family root: {relative}")
        pending = [relative] if entry.is_dir(follow_symlinks=False) else []
        while pending:
            current = pending.pop()
            try:
                children = tuple(os.scandir(ROOT / current))
            except OSError as error:
                raise AssertionError(
                    f"derived stage-family inventory unavailable: {current}"
                ) from error
            for child in children:
                child_relative = current / child.name
                discovered.add(child_relative)
                if child.is_symlink():
                    raise AssertionError(
                        f"symlink derived stage-family path: {child_relative}"
                    )
                if child.is_dir(follow_symlinks=False):
                    pending.append(child_relative)
    expected = {path for path in EXACT10} | {DERIVED}
    for path in sorted(discovered, key=Path.as_posix):
        try:
            item = os.lstat(ROOT / path)
        except OSError as error:
            raise AssertionError(
                f"stage-family path vanished during scan: {path}"
            ) from error
        if _check_ignore(path):
            raise AssertionError(f"ignored stage-family path: {path}")
        if stat.S_ISLNK(item.st_mode):
            raise AssertionError(f"symlink stage-family path: {path}")
        if path == DERIVED:
            if not stat.S_ISDIR(item.st_mode):
                raise AssertionError("Exact6 parent is not a directory")
            continue
        if (
            not stat.S_ISREG(item.st_mode)
            or item.st_size > 100 * 1024 * 1024
            or path.suffix.lower() in FORBIDDEN_SUFFIXES
        ):
            raise AssertionError(f"unsafe stage-family artifact: {path}")
    if discovered != expected:
        raise AssertionError("filesystem stage-family allowlist mismatch")
    return discovered


def _lifecycle() -> str:
    if _git(["merge-base", "--is-ancestor", BASE, "HEAD"]).returncode:
        raise AssertionError("base is not an ancestor")
    staged = _git(["diff", "--cached", "--name-only"])
    if staged.returncode or staged.stdout:
        raise AssertionError("staged index must be empty")
    states = []
    for path in EXACT10:
        item = os.lstat(ROOT / path)
        if (
            stat.S_ISLNK(item.st_mode) or not stat.S_ISREG(item.st_mode)
            or item.st_size > 100 * 1024 * 1024
            or path.suffix.lower() in FORBIDDEN_SUFFIXES
            or _check_ignore(path)
        ):
            raise AssertionError(f"unsafe Exact10 member: {path}")
        tracked = _git(["ls-files", "--error-unmatch", "--", path.as_posix()])
        states.append("tracked" if tracked.returncode == 0 else "untracked")
    if len(set(states)) != 1:
        raise AssertionError("mixed lifecycle")
    lifecycle = "post_commit" if states[0] == "tracked" else "pre_commit"
    untracked = set(
        _git(["ls-files", "--others", "--exclude-standard"]).stdout.splitlines()
    )
    exact = {path.as_posix() for path in EXACT10}
    working = _git(["diff", "--name-only"])
    if lifecycle == "pre_commit":
        if untracked != exact or working.stdout:
            raise AssertionError("pre_commit lifecycle mismatch")
    elif untracked or working.stdout:
        raise AssertionError("post_commit lifecycle mismatch")
    if set(os.listdir(ROOT / DERIVED)) != set(FILES):
        raise AssertionError("Exact6 inventory mismatch")
    _filesystem_stage_family()
    tracked = _git(["ls-files"])
    if tracked.returncode:
        raise AssertionError("tracked inventory unavailable")
    tracked_and_untracked = set(tracked.stdout.splitlines()) | untracked
    inherited_issue_sources = {
        path for path, _ in EXACT18 if Path(path).name == ISSUE
    }
    stage_related = {
        path for path in tracked_and_untracked
        if (
            _is_stage_family_path(Path(path))
            and path not in inherited_issue_sources
        )
    }
    if stage_related != exact:
        raise AssertionError("extra tracked/untracked stage-family path")
    return lifecycle


def main() -> int:
    if (sys.implementation.name, tuple(sys.version_info[:3])) != (
        "cpython", (3, 10, 4)
    ):
        raise RuntimeError("checker requires canonical CPython 3.10.4")
    sources = attest_exact18()
    _verify_ast()
    module = _load_production()
    built = module.build_artifact_payloads()
    verify_exact6_semantics(built, sources)
    returned = module.materialize_contract()
    disk = _read_exact6()
    manifest = verify_exact6_semantics(disk, sources)
    if disk != built or returned != manifest:
        raise AssertionError("builder/materializer/disk mismatch")
    lifecycle = _lifecycle()
    report = {
        "stage": STAGE, "base_commit": BASE, "lifecycle": lifecycle,
        "exact10_count": 10, "source_count": 18,
        "contract_row_count": 40, "truth_row_count": 40,
        "truth_cases_passed": 40, "forbidden_envelope_access_count": 0,
        "precondition_complete_count": 31,
        "precondition_incomplete_count": 14,
        "precondition_blocking_count": 14, "issue_row_count": 30,
        "issue_transition_count": 0, "current_permission": False,
        "authorized_admit_015_training_execution_count": 0,
        "mandatory_enforcement_implemented": False,
        "feature_semantics_audit_completed": False,
        "ready_for_training": False,
        "recommended_next_step":
            "design_covapie_admit_015_formal_evaluator_interface_contract_v1",
        "all_checks_passed": True,
    }
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
