"""Independent checker for stage-global admission orchestration runtime V1."""

from __future__ import annotations

import ast
import csv
import hashlib
import inspect
import io
import json
import os
import re
import stat
import subprocess
import sys
from collections import Counter
from pathlib import Path
from types import MappingProxyType
from typing import Any, NamedTuple, Sequence, get_type_hints

from covalent_ext import (
    covapie_bulk_download_admission_combined_candidate_verdict_and_cross_rule_aggregation_v1
    as aggregation_runtime,
)
from covalent_ext import (
    covapie_bulk_download_admission_unified_dispatch_runtime_with_admit_001_to_015
    as dispatch_runtime,
)
from covalent_ext import (
    covapie_stage_global_rule_evaluation_orchestration_contract_design_gate
    as contract,
)
from covalent_ext import (
    covapie_stage_global_rule_evaluation_orchestration_v1 as runtime,
)


ROOT = Path(__file__).resolve().parents[1]
BASE = "a677414ffcfe30db463f6bed33d1fbbedb10e398"
BASE_PARENT = "3e55b6e58668ce66ba74df8e0894b15641601e52"
BASE_TREE = "0688b000345449fae40e80659367ece799576391"
BASE_SUBJECT = (
    "add CovaPIE stage-global rule evaluation orchestration contract v1"
)
FORMAL_SUBJECT = (
    "add CovaPIE stage-global rule evaluation orchestration runtime v1"
)
LIFECYCLE_MODES = (
    "pre_commit",
    "detached_candidate_post_commit",
    "formal_main_post_commit_unpushed",
    "formal_main_post_push",
)
STAGE = "covapie_stage_global_rule_evaluation_orchestration_v1"
PRODUCTION_PATH = (
    Path("src/covalent_ext")
    / "covapie_stage_global_rule_evaluation_orchestration_v1.py"
)
PRODUCTION_SHA256 = (
    "5b5b85eceee3a9aada2dc6ae57c8af4a365dfc74677facdceeda7f0bde8a86bc"
)
CHECKER_PATH = (
    Path("scripts")
    / "check_covapie_stage_global_rule_evaluation_orchestration_v1.py"
)
TEST_PATH = (
    Path("tests")
    / "test_covapie_stage_global_rule_evaluation_orchestration_v1.py"
)
SUMMARY_PATH = (
    Path("docs")
    / "covapie_stage_global_rule_evaluation_orchestration_v1_summary.md"
)
DERIVED_ROOT = Path("data/derived/covalent_small") / STAGE
RUNTIME_NAME = "covapie_stage_global_orchestration_runtime_contract.csv"
TRACE_NAME = "covapie_stage_global_orchestration_call_trace_matrix.csv"
TRUTH_NAME = (
    "covapie_stage_global_orchestration_implementation_truth_matrix.csv"
)
SAFETY_NAME = (
    "covapie_stage_global_orchestration_implementation_safety_audit.csv"
)
ISSUE_NAME = "covapie_stage_global_orchestration_issue_readiness_inventory.csv"
MANIFEST_NAME = (
    "covapie_stage_global_rule_evaluation_orchestration_"
    "implementation_manifest.json"
)
PREDECESSOR_MANIFEST_PATH = (
    Path("data/derived/covalent_small")
    / "covapie_stage_global_rule_evaluation_orchestration_contract_v1"
    / "covapie_stage_global_rule_evaluation_orchestration_contract_manifest.json"
)
OUTPUT_NAMES = (
    RUNTIME_NAME,
    TRACE_NAME,
    TRUTH_NAME,
    SAFETY_NAME,
    ISSUE_NAME,
    MANIFEST_NAME,
)
EXACT10 = (
    PRODUCTION_PATH,
    CHECKER_PATH,
    TEST_PATH,
    SUMMARY_PATH,
) + tuple(DERIVED_ROOT / name for name in OUTPUT_NAMES)
SOURCE_BOUNDARY = (
    (
        Path("src/covalent_ext")
        / "covapie_stage_global_rule_evaluation_orchestration_"
        "contract_design_gate.py",
        "68ddcede8c56c1db51a7a49e2fb5943e12818e0412f6463238865a39a47d4548",
    ),
    (
        Path("scripts")
        / "check_covapie_stage_global_rule_evaluation_"
        "orchestration_contract_v1.py",
        "d8214e16157c22361eeb83e59590b105d92b210a407c05843b169d7ccf4eb85f",
    ),
    (
        Path("data/derived/covalent_small")
        / "covapie_stage_global_rule_evaluation_orchestration_contract_v1"
        / "covapie_stage_global_rule_evaluation_orchestration_"
        "contract_manifest.json",
        "a60448647d932bf4d541e3d2b3c48deb10e887de9ba3931ef40f1aa55c55e125",
    ),
    (
        Path("src/covalent_ext")
        / "covapie_bulk_download_admission_unified_dispatch_runtime_"
        "with_admit_001_to_015.py",
        "1fc5ac24e54d134d3f1f7054dfd2f264a2d76f17f0602bac216bb2e4e7e00bd1",
    ),
    (
        Path("data/derived/covalent_small")
        / "covapie_bulk_download_admission_unified_dispatch_runtime_"
        "with_admit_001_to_015_v1"
        / "covapie_admit_001_to_015_runtime_manifest.json",
        "0fbd5999977d025a44b4bef854d9edfda5ea0e5ed79a7d5ff7b17cef7b6186d3",
    ),
    (
        Path("src/covalent_ext")
        / "covapie_bulk_download_admission_combined_candidate_verdict_"
        "and_cross_rule_aggregation_v1.py",
        "8810d4bab34b2c5067b51dedb3edaa4a20e25c82c89576265986285e64f59904",
    ),
    (
        Path("data/derived/covalent_small")
        / "covapie_bulk_download_admission_combined_candidate_verdict_"
        "and_cross_rule_aggregation_v1"
        / "covapie_combined_candidate_verdict_and_cross_rule_aggregation_"
        "implementation_manifest.json",
        "bc8c5a5fc52b74d9e6f6e9da0b75dd69832b09213a996a4c73913660ab3d87d6",
    ),
)
ISSUE_SHA256 = (
    "fb4d2dfae7ffc056e3856c94e2f5a135d468eb3801144f9a698f95d9b812ace7"
)
CANONICAL_MASKS = (
    ("warhead_only", "A"),
    ("linker_plus_warhead", "B"),
    ("scaffold_plus_warhead", "B2"),
    ("scaffold_only", "B3"),
    ("scaffold_plus_linker_plus_warhead", "C"),
)
SAFETY_ITEMS = (
    "network",
    "provider",
    "download",
    "raw",
    "torch",
    "model",
    "checkpoint",
    "dataloader",
    "forward",
    "loss",
    "backward",
    "optimizer",
    "scheduler",
    "parameter_update",
    "checkpoint_write",
    "training_action",
    "current_permission",
    "action_permission",
    "ready_for_training",
)
PLATFORM_NAMESPACE = "refs/codex/turn-diffs"
UUID4 = (
    r"[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}"
)
PLATFORM_PATTERN = re.compile(
    rf"{re.escape(PLATFORM_NAMESPACE)}/(?:"
    rf"captures/[0-9]{{13}}/{UUID4}/base|"
    rf"checkpoints/[0-9a-f]{{64}}/[0-9a-f]{{64}}/[0-9]{{13}}/{UUID4})"
)
PLATFORM_BLOCKED_TERMS = (
    "covapie",
    "candidate",
    "temporary",
    "backup",
    "review",
)
FORMAL_REF_NAMES = (
    "refs/heads/main",
    "refs/remotes/origin/HEAD",
    "refs/remotes/origin/main",
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *args),
        cwd=ROOT,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _git_bytes(*args: str, check: bool = True) -> bytes:
    result = subprocess.run(
        ("git", *args),
        cwd=ROOT,
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def _single_git_line(*args: str) -> str:
    lines = _git(*args).stdout.splitlines()
    if len(lines) != 1 or not lines[0]:
        raise ValueError(f"Git scalar query failed: {args}")
    return lines[0]


def _verify_base() -> None:
    observed = _git(
        "show", "-s", "--format=%H%n%P%n%T%n%s", BASE
    ).stdout.splitlines()
    if observed != [BASE, BASE_PARENT, BASE_TREE, BASE_SUBJECT]:
        raise ValueError("formal BASE identity drift")


def _changed_paths(head: str) -> tuple[str, ...]:
    if head == BASE:
        return ()
    return tuple(
        line
        for line in _git(
            "diff", "--name-only", f"{BASE}..{head}"
        ).stdout.splitlines()
        if line
    )


class RefRecord(NamedTuple):
    name: str
    oid: str
    kind: str


def _ref_inventory() -> tuple[RefRecord, ...]:
    content = _git(
        "for-each-ref",
        "--sort=refname",
        "--format=%(refname)%09%(objectname)%09%(objecttype)",
    ).stdout
    records = []
    for line in content.splitlines():
        name, oid, kind = line.split("\t")
        records.append(RefRecord(name, oid, kind))
    return tuple(records)


def _assert_persistent_refs(refs: Sequence[RefRecord]) -> None:
    by_name = {record.name: record for record in refs}
    if len(by_name) != len(refs):
        raise ValueError("duplicate persistent ref inventory")
    for name in FORMAL_REF_NAMES:
        record = by_name.get(name)
        if record is None or record.kind != "commit":
            raise ValueError(f"formal ref missing or non-commit: {name}")
    for record in refs:
        if record.name in FORMAL_REF_NAMES:
            continue
        if not record.name.startswith(f"{PLATFORM_NAMESPACE}/"):
            raise ValueError(f"persistent ref forbidden: {record.name}")
        if (
            PLATFORM_PATTERN.fullmatch(record.name) is None
            or record.kind != "tree"
        ):
            raise ValueError(
                f"platform ref trust-boundary drift: {record.name}"
            )
        if any(term in record.name for term in PLATFORM_BLOCKED_TERMS):
            raise ValueError(f"platform ref blocked term: {record.name}")


def _origin_head() -> tuple[str, str]:
    symbolic = _single_git_line(
        "symbolic-ref", "refs/remotes/origin/HEAD"
    )
    resolved = _single_git_line("rev-parse", "refs/remotes/origin/HEAD")
    return symbolic, resolved


def _assert_formal_refs(
    refs: Sequence[RefRecord],
    *,
    expected_main: str,
    expected_origin: str,
    origin_head: tuple[str, str],
) -> None:
    by_name = {record.name: record for record in refs}
    if (
        by_name.get("refs/heads/main")
        != RefRecord("refs/heads/main", expected_main, "commit")
        or by_name.get("refs/remotes/origin/main")
        != RefRecord("refs/remotes/origin/main", expected_origin, "commit")
        or by_name.get("refs/remotes/origin/HEAD")
        != RefRecord("refs/remotes/origin/HEAD", expected_origin, "commit")
    ):
        raise ValueError("lifecycle formal-ref closure drift")
    if origin_head != ("refs/remotes/origin/main", expected_origin):
        raise ValueError("origin/HEAD symbolic or resolved OID drift")


class WorktreeRecord(NamedTuple):
    path: str
    head: str
    branch: str
    detached: bool


def _worktree_records() -> tuple[WorktreeRecord, ...]:
    content = _git("worktree", "list", "--porcelain").stdout
    blocks = tuple(
        block for block in content.strip().split("\n\n") if block
    )
    records = []
    for block in blocks:
        values: dict[str, str] = {}
        detached = False
        for line in block.splitlines():
            key, separator, value = line.partition(" ")
            if key == "detached" and not separator:
                detached = True
            else:
                values[key] = value
        records.append(
            WorktreeRecord(
                values.get("worktree", ""),
                values.get("HEAD", ""),
                values.get("branch", ""),
                detached,
            )
        )
    return tuple(records)


class LifecycleSnapshot(NamedTuple):
    head: str
    index: bytes
    status: bytes
    refs: tuple[RefRecord, ...]
    branch: str
    worktrees: tuple[WorktreeRecord, ...]
    origin_head_symbolic_target: str
    origin_head_resolved_oid: str
    lifecycle: str


def _assert_candidate_commit(head: str) -> None:
    parents = _single_git_line("show", "-s", "--format=%P", head).split()
    subject = _single_git_line("show", "-s", "--format=%s", head)
    if parents != [BASE] or subject != FORMAL_SUBJECT:
        raise ValueError("candidate parent/subject drift")
    changed = _changed_paths(head)
    exact = tuple(path.as_posix() for path in EXACT10)
    if set(changed) != set(exact) or len(changed) != 10:
        raise ValueError("candidate changed-file inventory drift")
    modes = _git("ls-tree", "-r", head, "--", *exact).stdout.splitlines()
    if len(modes) != 10 or any(
        not line.startswith("100644 blob ") for line in modes
    ):
        raise ValueError("candidate Exact10 Git mode drift")


def _verify_exact10_files() -> None:
    for path in EXACT10:
        target = ROOT / path
        if target.is_symlink() or not target.is_file():
            raise ValueError(f"Exact10 regular-file invariant failed: {path}")
        mode = stat.S_IMODE(target.stat(follow_symlinks=False).st_mode)
        if mode & 0o111:
            raise ValueError(f"Exact10 filesystem leaf is executable: {path}")


def _lifecycle() -> LifecycleSnapshot:
    _verify_base()
    head = _single_git_line("rev-parse", "HEAD")
    index = _git_bytes("ls-files", "--stage", "-z")
    status = _git_bytes(
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--ignored=no",
    )
    refs = _ref_inventory()
    _assert_persistent_refs(refs)
    origin_head = _origin_head()
    worktrees = _worktree_records()
    branch_query = _git("symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    branch = branch_query.stdout.strip() if branch_query.returncode == 0 else ""
    exact = tuple(path.as_posix() for path in EXACT10)

    if head == BASE:
        lifecycle = "pre_commit"
        _assert_formal_refs(
            refs,
            expected_main=BASE,
            expected_origin=BASE,
            origin_head=origin_head,
        )
        if branch != "main" or worktrees != (
            WorktreeRecord(str(ROOT), BASE, "refs/heads/main", False),
        ):
            raise ValueError("pre-commit single-main-worktree topology drift")
        entries = tuple(
            item.decode("utf-8") for item in status.split(b"\0") if item
        )
        expected = tuple(f"?? {path}" for path in EXACT10)
        if set(entries) != set(expected) or len(entries) != 10:
            raise ValueError("pre-commit Exact10 untracked inventory drift")
        if _git_bytes("ls-files", "--stage", "-z", "--", *exact):
            raise ValueError("pre-commit candidate staging residue")
    elif branch == "":
        lifecycle = "detached_candidate_post_commit"
        _assert_candidate_commit(head)
        _assert_formal_refs(
            refs,
            expected_main=BASE,
            expected_origin=BASE,
            origin_head=origin_head,
        )
        if status or len(worktrees) != 2:
            raise ValueError("detached topology/status cardinality drift")
        main_rows = tuple(
            row
            for row in worktrees
            if row == WorktreeRecord(
                row.path, BASE, "refs/heads/main", False
            )
        )
        detached_rows = tuple(
            row
            for row in worktrees
            if row
            == WorktreeRecord(str(ROOT), head, "", True)
        )
        if len(main_rows) != 1 or len(detached_rows) != 1:
            raise ValueError("detached two-worktree closure drift")
    elif branch == "main":
        _assert_candidate_commit(head)
        by_name = {record.name: record for record in refs}
        origin = by_name["refs/remotes/origin/main"].oid
        if origin == BASE:
            lifecycle = "formal_main_post_commit_unpushed"
        elif origin == head:
            lifecycle = "formal_main_post_push"
        else:
            raise ValueError("formal-main origin lifecycle drift")
        _assert_formal_refs(
            refs,
            expected_main=head,
            expected_origin=origin,
            origin_head=origin_head,
        )
        if status or worktrees != (
            WorktreeRecord(str(ROOT), head, "refs/heads/main", False),
        ):
            raise ValueError("formal-main single-worktree topology drift")
    else:
        raise ValueError("unsupported lifecycle branch/head topology")
    if lifecycle not in LIFECYCLE_MODES:
        raise ValueError("lifecycle vocabulary drift")
    _verify_exact10_files()
    return LifecycleSnapshot(
        head,
        index,
        status,
        refs,
        branch,
        worktrees,
        origin_head[0],
        origin_head[1],
        lifecycle,
    )


def _verify_source_boundary() -> None:
    for path, digest in SOURCE_BOUNDARY:
        payload = (ROOT / path).read_bytes()
        if _sha256(payload) != digest:
            raise ValueError(f"source-boundary SHA256 drift: {path}")
        if _git("diff", "--quiet", BASE, "--", path.as_posix(), check=False).returncode:
            raise ValueError(f"source boundary differs from BASE: {path}")


def _verify_public_source() -> None:
    payload = (ROOT / PRODUCTION_PATH).read_bytes()
    if _sha256(payload) != PRODUCTION_SHA256:
        raise ValueError("production runtime SHA256 drift")
    source = payload.decode("utf-8")
    tree = ast.parse(source)
    imports = {
        alias.asname: alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "covalent_ext"
        for alias in node.names
    }
    expected_imports = {
        "dispatch_runtime": (
            "covapie_bulk_download_admission_unified_dispatch_runtime_"
            "with_admit_001_to_015"
        ),
        "aggregation_runtime": (
            "covapie_bulk_download_admission_combined_candidate_verdict_"
            "and_cross_rule_aggregation_v1"
        ),
        "contract": (
            "covapie_stage_global_rule_evaluation_orchestration_"
            "contract_design_gate"
        ),
    }
    if imports != expected_imports:
        raise ValueError("production committed-module import boundary drift")
    functions = {
        node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    public = functions.get("orchestrate_stage_admission_scope")
    if public is None:
        raise ValueError("public orchestrator missing")
    positional = [item.arg for item in public.args.args]
    keyword_only = [item.arg for item in public.args.kwonlyargs]
    if (
        positional != ["scope_id", "candidate_inputs"]
        or keyword_only
        != ["batch_context", "stage_authorization_context"]
        or public.args.defaults
        or any(item is not None for item in public.args.kw_defaults)
        or public.args.vararg is not None
        or public.args.kwarg is not None
    ):
        raise ValueError("public AST signature drift")
    calls = {
        (node.func.value.id, node.func.attr)
        for node in ast.walk(public)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
    }
    required_calls = {
        ("dispatch_runtime", "evaluate_admission_rule"),
        ("aggregation_runtime", "aggregate_admission_rule_evaluations"),
        ("contract", "validate_unified_rule_evaluation_design"),
        ("contract", "validate_combined_candidate_verdict_design"),
    }
    if not required_calls.issubset(calls):
        raise ValueError("authoritative runtime call boundary drift")
    if "classify_stage_global_orchestration_contract_design" in source:
        raise ValueError("production calls design classifier")
    forbidden_imports = {
        "requests",
        "urllib",
        "torch",
        "lightning",
        "dataset",
    }
    imported_roots = {
        (node.module or "").split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    } | {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    if forbidden_imports & imported_roots:
        raise ValueError("production source crosses safety boundary")


def _verify_signature_and_identity() -> None:
    if runtime.__all__ != (
        "AdmissionCandidateOrchestrationInput",
        "CandidateAdmissionOrchestrationResult",
        "StageAdmissionOrchestrationResult",
        "StageAdmissionOrchestrationError",
        "orchestrate_stage_admission_scope",
    ):
        raise ValueError("public __all__ drift")
    shared = (
        (
            runtime.AdmissionCandidateOrchestrationInput,
            contract.AdmissionCandidateOrchestrationInput,
        ),
        (
            runtime.CandidateAdmissionOrchestrationResult,
            contract.CandidateAdmissionOrchestrationResult,
        ),
        (
            runtime.StageAdmissionOrchestrationResult,
            contract.StageAdmissionOrchestrationResult,
        ),
        (
            runtime.StageAdmissionOrchestrationError,
            contract.StageAdmissionOrchestrationError,
        ),
    )
    if any(left is not right for left, right in shared):
        raise ValueError("shared class identity drift")
    signature = inspect.signature(runtime.orchestrate_stage_admission_scope)
    parameters = tuple(signature.parameters.values())
    if (
        tuple(item.name for item in parameters)
        != (
            "scope_id",
            "candidate_inputs",
            "batch_context",
            "stage_authorization_context",
        )
        or tuple(item.kind for item in parameters)
        != (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
            inspect.Parameter.KEYWORD_ONLY,
        )
        or any(item.default is not inspect.Parameter.empty for item in parameters)
    ):
        raise ValueError("runtime inspect signature drift")
    hints = get_type_hints(runtime.orchestrate_stage_admission_scope)
    if (
        hints.get("scope_id") is not str
        or hints.get("return") is not contract.StageAdmissionOrchestrationResult
    ):
        raise ValueError("runtime annotation identity drift")
    if (
        runtime.orchestrate_stage_admission_scope.__globals__.get(
            "dispatch_runtime"
        )
        is not dispatch_runtime
        or runtime.orchestrate_stage_admission_scope.__globals__.get(
            "aggregation_runtime"
        )
        is not aggregation_runtime
    ):
        raise ValueError("runtime module-object resolution drift")


def _evaluation(rule_id: str, outcome: str = "passed"):
    return dispatch_runtime.UnifiedAdmissionRuleEvaluation(
        schema_version=dispatch_runtime.RESULT_SCHEMA_VERSION,
        admission_rule_id=rule_id,
        admission_rule_name=contract.RULE_NAMES[rule_id],
        outcome=outcome,
        passed=outcome == "passed",
        blocks_candidate=outcome != "passed",
        reason="" if outcome == "passed" else f"{rule_id}_{outcome.upper()}",
        normalized_values=(),
        validated_candidate_fields=(),
        consumed_candidate_fields=(),
        consumed_context_items=(),
        evaluator_io_used=False,
        adapter_id=contract.ADAPTER_IDS[rule_id],
    )


def _inputs(count: int):
    inputs = tuple(
        contract.AdmissionCandidateOrchestrationInput(
            {"candidate_index": index},
            {"evaluation_index": index},
            {"download_index": index},
        )
        for index in range(count)
    )
    return inputs, {"batch": "caller"}, {"authorization": "caller"}


def _unsafe_verdict(source: object, mutation: str) -> object:
    values = dict(vars(source))
    if mutation == "wrong_scope":
        values["scope_id"] = "wrong_scope"
    elif mutation == "copied_normal_vector":
        values["rule_evaluations"] = tuple([*source.rule_evaluations])
    elif mutation == "rejected_wrong_reason":
        values["reason"] = "COMBINED_ADMISSION_REQUIRED_RULE_INVALID"
    elif mutation == "rejected_nonempty_diagnostics":
        values["evaluated_rule_ids"] = source.required_rule_ids
    else:
        raise ValueError(f"unknown malformed aggregator mutation: {mutation}")
    malformed = object.__new__(
        aggregation_runtime.CombinedAdmissionCandidateVerdict
    )
    for name in aggregation_runtime.RESULT_FIELDS:
        object.__setattr__(malformed, name, values[name])
    return malformed


def _probe_run(
    scope: str,
    count: int,
    *,
    outcomes=None,
    handler_behavior=None,
    aggregator_behavior=None,
):
    candidate_inputs, batch, authorization = _inputs(count)
    record_indexes = {
        id(item.candidate_record): index
        for index, item in enumerate(candidate_inputs)
    }
    dispatch_calls: list[dict[str, Any]] = []
    aggregate_calls: list[tuple[Any, Any]] = []
    outcomes = outcomes or {}

    def make_handler(rule_id):
        def handler(
            candidate_record,
            *,
            batch_context,
            evaluation_context,
            download_result_context,
            stage_authorization_context,
        ):
            candidate_index = (
                -1
                if candidate_record
                is contract.STAGE_GLOBAL_CANDIDATE_SENTINEL
                else record_indexes[id(candidate_record)]
            )
            dispatch_calls.append(
                {
                    "candidate_index": candidate_index,
                    "rule_id": rule_id,
                    "candidate_record": candidate_record,
                    "batch_context": batch_context,
                    "evaluation_context": evaluation_context,
                    "download_result_context": download_result_context,
                    "stage_authorization_context": stage_authorization_context,
                }
            )
            if handler_behavior == (candidate_index, rule_id, "exception"):
                raise RuntimeError("private-dispatch-message")
            if handler_behavior == (candidate_index, rule_id, "malformed"):
                return object()
            if handler_behavior == (candidate_index, rule_id, "interrupt"):
                raise KeyboardInterrupt
            return _evaluation(rule_id, outcomes.get((candidate_index, rule_id), "passed"))

        return handler

    original_registry = dispatch_runtime.EVALUATOR_REGISTRY
    original_aggregator = aggregation_runtime.aggregate_admission_rule_evaluations
    dispatch_runtime.EVALUATOR_REGISTRY = MappingProxyType(
        {rule_id: make_handler(rule_id) for rule_id in contract.RULE_NAMES}
    )

    def aggregate(scope_id, *, ordered_rule_evaluations):
        aggregate_calls.append((scope_id, ordered_rule_evaluations))
        index = len(aggregate_calls) - 1
        if aggregator_behavior == (index, "exception"):
            raise RuntimeError("private-aggregator-message")
        if aggregator_behavior == (index, "interrupt"):
            raise KeyboardInterrupt
        verdict = original_aggregator(
            scope_id, ordered_rule_evaluations=ordered_rule_evaluations
        )
        behavior = (
            aggregator_behavior[1]
            if aggregator_behavior is not None
            and aggregator_behavior[0] == index
            else ""
        )
        if behavior == "wrong_type":
            return object()
        if behavior in (
            "wrong_scope",
            "copied_normal_vector",
            "rejected_wrong_reason",
            "rejected_nonempty_diagnostics",
        ):
            return _unsafe_verdict(verdict, behavior)
        return verdict

    aggregation_runtime.aggregate_admission_rule_evaluations = aggregate
    try:
        result = runtime.orchestrate_stage_admission_scope(
            scope,
            candidate_inputs,
            batch_context=batch,
            stage_authorization_context=authorization,
        )
        return (
            "result",
            result,
            dispatch_calls,
            aggregate_calls,
            candidate_inputs,
            batch,
            authorization,
        )
    except BaseException as error:
        return (
            "error",
            error,
            dispatch_calls,
            aggregate_calls,
            candidate_inputs,
            batch,
            authorization,
        )
    finally:
        dispatch_runtime.EVALUATOR_REGISTRY = original_registry
        aggregation_runtime.aggregate_admission_rule_evaluations = (
            original_aggregator
        )


def _verify_routes(
    calls, candidate_inputs, batch, authorization
) -> None:
    evaluation_rules = {
        "ADMIT_004",
        "ADMIT_006",
        "ADMIT_007",
        "ADMIT_008",
        "ADMIT_009",
        "ADMIT_010",
        "ADMIT_011",
        "ADMIT_012",
        "ADMIT_013",
    }
    for call in calls:
        index = call["candidate_index"]
        rule_id = call["rule_id"]
        if index == -1:
            conditions = (
                call["candidate_record"]
                is contract.STAGE_GLOBAL_CANDIDATE_SENTINEL,
                call["batch_context"] is None,
                call["evaluation_context"] is None,
                call["download_result_context"] is None,
                call["stage_authorization_context"] is authorization,
            )
        else:
            item = candidate_inputs[index]
            conditions = (
                call["candidate_record"] is item.candidate_record,
                call["batch_context"]
                is (batch if rule_id in {"ADMIT_001", "ADMIT_009"} else None),
                call["evaluation_context"]
                is (
                    item.evaluation_context
                    if rule_id in evaluation_rules
                    else None
                ),
                call["download_result_context"]
                is (
                    item.download_result_context
                    if rule_id in {"ADMIT_012", "ADMIT_013"}
                    else None
                ),
                call["stage_authorization_context"] is None,
            )
        if not all(conditions):
            raise ValueError(f"context identity route drift: {index}/{rule_id}")


def _verify_positive_case(scope: str, count: int) -> dict[str, int]:
    probe = _probe_run(scope, count)
    if probe[0] != "result":
        raise ValueError("positive runtime case raised")
    _, result, calls, aggregates, inputs, batch, authorization = probe
    stage_ids = contract.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope]
    candidate_ids = contract.CANDIDATE_RULE_IDS_BY_SCOPE[scope]
    required = contract.REQUIRED_RULE_IDS[scope]
    expected_order = [(-1, rule_id) for rule_id in stage_ids]
    expected_order.extend(
        (index, rule_id)
        for index in range(count)
        for rule_id in candidate_ids
    )
    if [(call["candidate_index"], call["rule_id"]) for call in calls] != expected_order:
        raise ValueError("dispatcher call order drift")
    if (
        type(result) is not contract.StageAdmissionOrchestrationResult
        or result.dispatcher_call_count != len(stage_ids) + count * len(candidate_ids)
        or result.aggregator_call_count != count
        or result.orchestration_io_used is not False
        or result.action_permission_granted is not False
        or len(aggregates) != count
    ):
        raise ValueError("stage result/cardinality drift")
    _verify_routes(calls, inputs, batch, authorization)
    for index, candidate in enumerate(result.candidate_results):
        vector = candidate.ordered_rule_evaluations
        if (
            type(candidate) is not contract.CandidateAdmissionOrchestrationResult
            or candidate.candidate_index != index
            or candidate.dispatcher_call_count != len(candidate_ids)
            or candidate.aggregator_call_count != 1
            or aggregates[index][1] is not vector
            or candidate.combined_verdict.rule_evaluations is not vector
            or candidate.combined_verdict.evaluated_rule_ids != required
            or tuple(item.admission_rule_id for item in vector) != required
        ):
            raise ValueError("candidate/vector identity drift")
        for stage_index, rule_id in enumerate(stage_ids):
            if (
                vector[required.index(rule_id)]
                is not result.stage_global_rule_evaluations[stage_index]
            ):
                raise ValueError("stage-global identity reuse drift")
    return {
        "dispatcher_calls": len(calls),
        "aggregator_calls": len(aggregates),
    }


def _assert_error_probe(
    probe: tuple[Any, ...],
    *,
    expected_code: str,
    expected_candidate_index: int,
    expected_rule_id: str,
    expected_dispatcher_count: int,
    expected_aggregator_count: int,
    expected_cause_type: str,
) -> None:
    if probe[0] != "error":
        raise ValueError("error case returned a partial stage result")
    error, calls, aggregates = probe[1], probe[2], probe[3]
    if type(error) is not contract.StageAdmissionOrchestrationError:
        raise ValueError("error case returned wrong exception type")
    expected_cause = (
        RuntimeError if expected_cause_type == "RuntimeError" else None
    )
    if (
        (expected_cause is None and error.__cause__ is not None)
        or (
            expected_cause is not None
            and type(error.__cause__) is not expected_cause
        )
    ):
        raise ValueError("orchestration error __cause__ presence/type drift")
    cause_name = type(error.__cause__).__name__ if error.__cause__ else ""
    observed = (
        error.code,
        error.candidate_index,
        error.admission_rule_id,
        error.dispatcher_call_count,
        error.aggregator_call_count,
        error.cause_type,
        cause_name,
        len(calls),
        len(aggregates),
        (
            len(calls) == expected_dispatcher_count
            and len(aggregates) == expected_aggregator_count
        ),
    )
    expected = (
        expected_code,
        expected_candidate_index,
        expected_rule_id,
        expected_dispatcher_count,
        expected_aggregator_count,
        expected_cause_type,
        expected_cause_type,
        expected_dispatcher_count,
        expected_aggregator_count,
        True,
    )
    if observed != expected:
        raise ValueError(
            f"complete orchestration error projection drift: {observed!r}"
        )
    if "private-" in error.reason:
        raise ValueError("orchestration error reason leaked cause text")


def _verify_runtime_matrix() -> dict[str, Any]:
    for scope in contract.SCOPE_IDS:
        _verify_positive_case(scope, 1)
    _verify_positive_case(contract.SCOPE_IDS[-1], 3)

    training_scope = contract.SCOPE_IDS[-1]
    outcome_cases = (
        {(-1, "ADMIT_014"): "blocked"},
        {(0, "ADMIT_004"): "invalid"},
        {(0, "ADMIT_006"): "rejected"},
        {(0, "ADMIT_006"): "rejected", (0, "ADMIT_007"): "blocked"},
    )
    for outcomes in outcome_cases:
        probe = _probe_run(training_scope, 3, outcomes=outcomes)
        if probe[0] != "result":
            raise ValueError("normal outcome short-circuited")
        result, calls, aggregates = probe[1], probe[2], probe[3]
        if len(calls) != 41 or len(aggregates) != 3:
            raise ValueError("normal outcome call completion drift")
        for candidate in result.candidate_results:
            rejected = any(
                item.outcome == "rejected"
                for item in candidate.ordered_rule_evaluations
            )
            if rejected and (
                candidate.combined_verdict.outcome != "invalid"
                or candidate.combined_verdict.reason
                != aggregation_runtime.EVALUATION_INVARIANT_INVALID_REASON
                or candidate.combined_verdict.evaluated_rule_ids
                or candidate.combined_verdict.rule_evaluations
                or candidate.combined_verdict.invalid_rule_ids
                or candidate.combined_verdict.blocked_rule_ids
                or candidate.combined_verdict.failing_rule_ids
            ):
                raise ValueError("rejected canonical projection drift")

    stage_exception_count = 0
    for scope in contract.SCOPE_IDS:
        for position, rule_id in enumerate(
            contract.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope], 1
        ):
            probe = _probe_run(
                scope,
                3,
                handler_behavior=(-1, rule_id, "exception"),
            )
            _assert_error_probe(
                probe,
                expected_code=contract.ERROR_CODES[5],
                expected_candidate_index=-1,
                expected_rule_id=rule_id,
                expected_dispatcher_count=position,
                expected_aggregator_count=0,
                expected_cause_type="RuntimeError",
            )
            stage_exception_count += 1

    candidate_exception_count = 0
    for scope in contract.SCOPE_IDS:
        stage_count = len(contract.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope])
        candidate_ids = contract.CANDIDATE_RULE_IDS_BY_SCOPE[scope]
        candidate_count = len(candidate_ids)
        positions = (1, (candidate_count + 1) // 2, candidate_count)
        for candidate_index in (0, 1, 2):
            for position in positions:
                rule_id = candidate_ids[position - 1]
                probe = _probe_run(
                    scope,
                    3,
                    handler_behavior=(
                        candidate_index,
                        rule_id,
                        "exception",
                    ),
                )
                _assert_error_probe(
                    probe,
                    expected_code=contract.ERROR_CODES[5],
                    expected_candidate_index=candidate_index,
                    expected_rule_id=rule_id,
                    expected_dispatcher_count=(
                        stage_count
                        + candidate_index * candidate_count
                        + position
                    ),
                    expected_aggregator_count=candidate_index,
                    expected_cause_type="RuntimeError",
                )
                candidate_exception_count += 1

    dispatcher_malformed_count = 0
    for scope in contract.SCOPE_IDS:
        stage_ids = contract.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope]
        for position, rule_id in enumerate(stage_ids, 1):
            probe = _probe_run(
                scope,
                3,
                handler_behavior=(-1, rule_id, "malformed"),
            )
            _assert_error_probe(
                probe,
                expected_code=contract.ERROR_CODES[6],
                expected_candidate_index=-1,
                expected_rule_id=rule_id,
                expected_dispatcher_count=position,
                expected_aggregator_count=0,
                expected_cause_type="",
            )
            dispatcher_malformed_count += 1
        candidate_ids = contract.CANDIDATE_RULE_IDS_BY_SCOPE[scope]
        position = (len(candidate_ids) + 1) // 2
        rule_id = candidate_ids[position - 1]
        probe = _probe_run(
            scope,
            3,
            handler_behavior=(1, rule_id, "malformed"),
        )
        _assert_error_probe(
            probe,
            expected_code=contract.ERROR_CODES[6],
            expected_candidate_index=1,
            expected_rule_id=rule_id,
            expected_dispatcher_count=(
                len(stage_ids) + len(candidate_ids) + position
            ),
            expected_aggregator_count=1,
            expected_cause_type="",
        )
        dispatcher_malformed_count += 1

    stage_count = len(
        contract.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[training_scope]
    )
    candidate_count = len(
        contract.CANDIDATE_RULE_IDS_BY_SCOPE[training_scope]
    )
    for candidate_index in (0, 1, 2):
        probe = _probe_run(
            training_scope,
            3,
            aggregator_behavior=(candidate_index, "exception"),
        )
        _assert_error_probe(
            probe,
            expected_code=contract.ERROR_CODES[7],
            expected_candidate_index=candidate_index,
            expected_rule_id="",
            expected_dispatcher_count=(
                stage_count + (candidate_index + 1) * candidate_count
            ),
            expected_aggregator_count=candidate_index + 1,
            expected_cause_type="RuntimeError",
        )

    malformed_variants = (
        "wrong_type",
        "wrong_scope",
        "copied_normal_vector",
        "rejected_wrong_reason",
        "rejected_nonempty_diagnostics",
    )
    for mutation in malformed_variants:
        outcomes = (
            {(1, "ADMIT_006"): "rejected"}
            if mutation.startswith("rejected_")
            else {}
        )
        probe = _probe_run(
            training_scope,
            3,
            outcomes=outcomes,
            aggregator_behavior=(1, mutation),
        )
        _assert_error_probe(
            probe,
            expected_code=contract.ERROR_CODES[7],
            expected_candidate_index=1,
            expected_rule_id="",
            expected_dispatcher_count=stage_count + 2 * candidate_count,
            expected_aggregator_count=2,
            expected_cause_type="",
        )

    dispatcher_interrupt = _probe_run(
        training_scope,
        3,
        handler_behavior=(-1, "ADMIT_014", "interrupt"),
    )
    if (
        dispatcher_interrupt[0] != "error"
        or type(dispatcher_interrupt[1]) is not KeyboardInterrupt
        or len(dispatcher_interrupt[2]) != 1
        or dispatcher_interrupt[3]
    ):
        raise ValueError("dispatcher BaseException propagation drift")
    aggregator_interrupt = _probe_run(
        training_scope,
        3,
        aggregator_behavior=(1, "interrupt"),
    )
    if (
        aggregator_interrupt[0] != "error"
        or type(aggregator_interrupt[1]) is not KeyboardInterrupt
        or len(aggregator_interrupt[2]) != stage_count + 2 * candidate_count
        or len(aggregator_interrupt[3]) != 2
    ):
        raise ValueError("aggregator BaseException propagation drift")

    candidate_inputs, batch, authorization = _inputs(1)
    original = dispatch_runtime.EVALUATOR_REGISTRY
    called = []

    def forbidden(*args: object, **kwargs: object) -> object:
        called.append(True)
        return object()

    dispatch_runtime.EVALUATOR_REGISTRY = MappingProxyType(
        {rule_id: forbidden for rule_id in contract.RULE_NAMES}
    )
    try:
        try:
            runtime.orchestrate_stage_admission_scope(
                1,
                (),
                batch_context=object(),
                stage_authorization_context=object(),
            )
        except contract.StageAdmissionOrchestrationError as error:
            observed = (
                error.code,
                error.candidate_index,
                error.admission_rule_id,
                error.dispatcher_call_count,
                error.aggregator_call_count,
                error.cause_type,
                error.__cause__,
            )
            expected = (
                contract.ERROR_CODES[0],
                -1,
                "",
                0,
                0,
                "",
                None,
            )
            if observed != expected:
                raise ValueError("prevalidation zero-call projection drift")
        else:
            raise ValueError("prevalidation failed open")
    finally:
        dispatch_runtime.EVALUATOR_REGISTRY = original
    if called:
        raise ValueError("prevalidation called dispatcher")
    return {
        "positive_case_count": 5,
        "normal_no_short_circuit_case_count": len(outcome_cases),
        "stage_dispatch_exception_case_count": stage_exception_count,
        "candidate_dispatch_exception_case_count": candidate_exception_count,
        "dispatcher_malformed_case_count": dispatcher_malformed_count,
        "aggregator_exception_case_count": 3,
        "aggregator_malformed_case_count": len(malformed_variants),
        "base_exception_case_count": 2,
        "complete_error_projection_verified": True,
        "corruption_stops_later_candidates": True,
        "partial_stage_result_returned": False,
        "committed_dispatcher_called": True,
        "committed_aggregator_called": True,
    }


def _read_csv(name: str) -> tuple[dict[str, str], ...]:
    payload = (ROOT / DERIVED_ROOT / name).read_text(encoding="utf-8")
    return tuple(csv.DictReader(io.StringIO(payload)))


def _expected_trace_route(rule_id: str, candidate_index: int) -> str:
    if candidate_index == -1:
        return "stage_authorization_context=caller_identity;others=None"
    routes = []
    if rule_id in ("ADMIT_001", "ADMIT_009"):
        routes.append("batch=caller_identity")
    if rule_id in (
        "ADMIT_004",
        "ADMIT_006",
        "ADMIT_007",
        "ADMIT_008",
        "ADMIT_009",
        "ADMIT_010",
        "ADMIT_011",
        "ADMIT_012",
        "ADMIT_013",
    ):
        routes.append("evaluation=candidate_identity")
    if rule_id in ("ADMIT_012", "ADMIT_013"):
        routes.append("download=candidate_identity")
    routes.append("stage_authorization=None")
    return ";".join(routes)


def _verify_actual_trace_rows(trace_rows: tuple[dict[str, str], ...]) -> None:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in trace_rows:
        grouped.setdefault(row["case_id"], []).append(row)
    expected_cases = tuple(
        (f"{scope}:N=1:all_passed", scope, 1)
        for scope in contract.SCOPE_IDS
    ) + (
        (
            f"{contract.SCOPE_IDS[-1]}:N=3:all_passed",
            contract.SCOPE_IDS[-1],
            3,
        ),
    )
    error_case_id = (
        f"{contract.SCOPE_IDS[-1]}:N=3:"
        "aggregator_malformed_candidate_1"
    )
    if tuple(grouped) != tuple(item[0] for item in expected_cases) + (
        error_case_id,
    ):
        raise ValueError("call-trace executable-case inventory drift")
    for case_id, scope, candidate_count in expected_cases:
        stage_ids = contract.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope]
        candidate_ids = contract.CANDIDATE_RULE_IDS_BY_SCOPE[scope]
        expected: list[tuple[int, str, str, int, int, str]] = []
        dispatcher_attempt = 0
        aggregator_attempt = 0
        for rule_id in stage_ids:
            dispatcher_attempt += 1
            expected.append(
                (
                    -1,
                    rule_id,
                    "stage_global_once",
                    dispatcher_attempt,
                    0,
                    _expected_trace_route(rule_id, -1),
                )
            )
        for candidate_index in range(candidate_count):
            for rule_id in candidate_ids:
                dispatcher_attempt += 1
                expected.append(
                    (
                        candidate_index,
                        rule_id,
                        "candidate_scoped",
                        dispatcher_attempt,
                        0,
                        _expected_trace_route(rule_id, candidate_index),
                    )
                )
            aggregator_attempt += 1
            expected.append(
                (
                    candidate_index,
                    "",
                    "candidate_aggregator",
                    dispatcher_attempt,
                    aggregator_attempt,
                    "ordered_vector_keyword_identity",
                )
            )
        rows = grouped[case_id]
        if len(rows) != len(expected):
            raise ValueError("call-trace event cardinality drift")
        for event_sequence, (row, projection) in enumerate(
            zip(rows, expected, strict=True), 1
        ):
            (
                candidate_index,
                rule_id,
                domain,
                expected_dispatcher_attempt,
                expected_aggregator_attempt,
                route,
            ) = projection
            observed = (
                row["scope_id"],
                int(row["candidate_index"]),
                int(row["call_sequence"]),
                row["rule_id"],
                row["execution_domain"],
                row["context_route"],
                int(row["dispatcher_attempt_number"]),
                int(row["aggregator_attempt_number"]),
                row["returned_outcome"],
                row["identity_checks"],
            )
            expected_row = (
                scope,
                candidate_index,
                event_sequence,
                rule_id,
                domain,
                route,
                expected_dispatcher_attempt,
                expected_aggregator_attempt,
                "passed",
                "true",
            )
            if observed != expected_row:
                raise ValueError(
                    f"call-trace actual event projection drift: {case_id}"
                )
    scope = contract.SCOPE_IDS[-1]
    stage_ids = contract.STAGE_GLOBAL_RULE_IDS_BY_SCOPE[scope]
    candidate_ids = contract.CANDIDATE_RULE_IDS_BY_SCOPE[scope]
    expected_error: list[tuple[int, str, str, int, int, str, str]] = []
    dispatcher_attempt = 0
    for rule_id in stage_ids:
        dispatcher_attempt += 1
        expected_error.append(
            (
                -1,
                rule_id,
                "stage_global_once",
                dispatcher_attempt,
                0,
                _expected_trace_route(rule_id, -1),
                "passed",
            )
        )
    for candidate_index in (0, 1):
        for rule_id in candidate_ids:
            dispatcher_attempt += 1
            expected_error.append(
                (
                    candidate_index,
                    rule_id,
                    "candidate_scoped",
                    dispatcher_attempt,
                    0,
                    _expected_trace_route(rule_id, candidate_index),
                    "passed",
                )
            )
        expected_error.append(
            (
                candidate_index,
                "",
                "candidate_aggregator",
                dispatcher_attempt,
                candidate_index + 1,
                "ordered_vector_keyword_identity",
                "passed" if candidate_index == 0 else "error",
            )
        )
    rows = grouped[error_case_id]
    if len(rows) != len(expected_error):
        raise ValueError("error call-trace event cardinality drift")
    for event_sequence, (row, projection) in enumerate(
        zip(rows, expected_error, strict=True), 1
    ):
        (
            candidate_index,
            rule_id,
            domain,
            dispatcher_attempt,
            aggregator_attempt,
            route,
            outcome,
        ) = projection
        observed = (
            row["scope_id"],
            int(row["candidate_index"]),
            int(row["call_sequence"]),
            row["rule_id"],
            row["execution_domain"],
            row["context_route"],
            int(row["dispatcher_attempt_number"]),
            int(row["aggregator_attempt_number"]),
            row["returned_outcome"],
            row["identity_checks"],
        )
        expected_row = (
            scope,
            candidate_index,
            event_sequence,
            rule_id,
            domain,
            route,
            dispatcher_attempt,
            aggregator_attempt,
            outcome,
            "true",
        )
        if observed != expected_row:
            raise ValueError("error call-trace actual event projection drift")
    if any(int(row["candidate_index"]) == 2 for row in rows):
        raise ValueError("error call trace executed candidate 2")


def _verify_evidence() -> dict[str, Any]:
    payloads = {
        name: (ROOT / DERIVED_ROOT / name).read_bytes()
        for name in OUTPUT_NAMES
    }
    runtime_rows = _read_csv(RUNTIME_NAME)
    trace_rows = _read_csv(TRACE_NAME)
    truth_rows = _read_csv(TRUTH_NAME)
    safety_rows = _read_csv(SAFETY_NAME)
    issue_rows = _read_csv(ISSUE_NAME)
    if (
        not runtime_rows
        or not trace_rows
        or not truth_rows
        or not safety_rows
        or any(row.get("passed") != "true" for row in runtime_rows)
        or any(row.get("passed") != "true" for row in truth_rows)
        or any(row.get("passed") != "true" for row in safety_rows)
        or any(row.get("identity_checks") != "true" for row in trace_rows)
    ):
        raise ValueError("evidence pass/identity rows invalid")
    required_truth_groups = {
        "prevalidation_zero_call_projection",
        "stage_dispatch_exception_formula",
        "candidate_dispatch_exception_formula",
        "dispatcher_malformed_formula",
        "aggregator_exception_formula",
        "aggregator_malformed_formula",
        "corruption_stops_later_candidates",
        "baseexception_propagation",
        "stage_global_identity_reuse",
        "normal_vector_identity",
        "rejected_canonical",
        "no_normal_outcome_short_circuit",
    }
    observed_truth_groups = {row["case_group"] for row in truth_rows}
    if not required_truth_groups.issubset(observed_truth_groups):
        raise ValueError("truth-matrix required group inventory drift")
    _verify_actual_trace_rows(trace_rows)
    if tuple(row["safety_item"] for row in safety_rows) != SAFETY_ITEMS:
        raise ValueError("safety Exact19 inventory drift")
    if any(
        row["expected"] != "false" or row["observed"] != "false"
        for row in safety_rows
    ):
        raise ValueError("safety boundary is not fail-closed")
    if _sha256(payloads[ISSUE_NAME]) != ISSUE_SHA256:
        raise ValueError("issue inventory continuity SHA256 drift")
    effective_open = tuple(
        row["issue_id"]
        for row in issue_rows
        if row["successor_effective_status"] == "open"
    )
    if effective_open != (
        "COVALENT_ATOM_PAIR_ENCODING_UNRESOLVED",
        "REAL_PROVIDER_EXPORT_BLOCKING_ROWS_PRESENT",
    ):
        raise ValueError("effective-open issue inventory drift")

    manifest = json.loads(payloads[MANIFEST_NAME])
    expected_hashes = {
        name: _sha256(payloads[name])
        for name in OUTPUT_NAMES
        if name != MANIFEST_NAME
    }
    if manifest.get("artifact_sha256") != expected_hashes:
        raise ValueError("manifest artifact SHA256 drift")
    count_checks = (
        manifest.get("runtime_contract_row_count") == len(runtime_rows),
        manifest.get("call_trace_row_count") == len(trace_rows),
        manifest.get("truth_matrix_row_count") == len(truth_rows),
        manifest.get("truth_matrix_group_count")
        == len({row["case_group"] for row in truth_rows}),
        manifest.get("safety_audit_row_count") == len(safety_rows),
        manifest.get("issue_inventory_row_count") == len(issue_rows),
    )
    if not all(count_checks):
        raise ValueError("manifest row/group count drift")
    masks = tuple(
        (item["semantic_name"], item["alias"])
        for item in manifest.get("canonical_masks", ())
    )
    if manifest.get("canonical_mask_count") != 5 or masks != CANONICAL_MASKS:
        raise ValueError("canonical five-mask contract drift")
    required_true = (
        "all_checks_passed",
        "stage_global_rule_evaluation_orchestration_contract_frozen",
        "stage_global_rule_evaluation_orchestration_implemented",
        "dispatcher_runtime_called_by_orchestrator",
        "aggregator_runtime_called_by_orchestrator",
        "stage_global_exactly_once_runtime_verified",
        "candidate_vector_assembly_runtime_verified",
        "orchestration_error_runtime_verified",
        "feature_semantics_audit_required_before_training",
    )
    required_false = (
        "download_action_implemented",
        "training_action_implemented",
        "current_permission",
        "action_permission_granted",
        "feature_semantics_audit_completed",
        "ready_for_training",
        "unknown_atom_feature_policy_resolved",
        "feature_semantics_known",
    )
    if any(manifest.get(name) is not True for name in required_true):
        raise ValueError("manifest required-true readiness drift")
    if any(manifest.get(name) is not False for name in required_false):
        raise ValueError("manifest required-false readiness drift")
    if manifest.get("step12d_warning") != (
        "Step12D was a smoke legality check, not a final "
        "training-feature contract"
    ):
        raise ValueError("feature-semantics warning drift")
    predecessor_manifest = json.loads(
        _git(
            "show", f"{BASE}:{PREDECESSOR_MANIFEST_PATH.as_posix()}"
        ).stdout
    )
    predecessor_pre = predecessor_manifest.get("precondition_continuity", {})
    expected_pre = {
        name: predecessor_pre[name]
        for name in (
            "row_count",
            "transition_count",
            "complete_count",
            "supported_but_not_frozen_count",
            "incomplete_count",
            "implementation_blocking_count",
            "remaining_open_precondition_ids",
        )
    }
    expected_pre["newly_resolved_count"] = 0
    pre = manifest.get("precondition_continuity")
    if pre != expected_pre:
        raise ValueError("PRE continuity drift")
    if manifest.get("recommended_next_step") != (
        "run_covapie_stage_global_rule_evaluation_orchestration_"
        "in_memory_integration_smoke_v1"
    ):
        raise ValueError("recommended next step drift")
    expected_support = {
        path.as_posix(): _sha256((ROOT / path).read_bytes())
        for path in EXACT10[:4]
    }
    if manifest.get("support_file_sha256") != expected_support:
        raise ValueError("support file SHA256 drift")
    return {
        "runtime_contract_rows": len(runtime_rows),
        "call_trace_rows": len(trace_rows),
        "truth_rows": len(truth_rows),
        "truth_groups": len({row["case_group"] for row in truth_rows}),
        "safety_rows": len(safety_rows),
        "issue_rows": len(issue_rows),
        "artifact_sha256": expected_hashes,
        "manifest_sha256": _sha256(payloads[MANIFEST_NAME]),
    }


def _verify_repository_safety() -> None:
    forbidden_suffixes = (
        ".pt",
        ".ckpt",
        ".pth",
        ".pkl",
        ".lmdb",
        ".tar",
        ".zip",
        ".tgz",
        ".npz",
        ".tmp",
        ".part",
    )
    if any(path.suffix in forbidden_suffixes for path in EXACT10):
        raise ValueError("Exact10 forbidden suffix")
    for path in EXACT10:
        target = ROOT / path
        if target.stat().st_size > 100 * 1024 * 1024:
            raise ValueError("Exact10 file exceeds 100 MiB")
    protected = (
        "data/raw",
        "checkpoints",
        "equivariant_diffusion",
        "lightning_modules.py",
        "dataset.py",
        "data/prepare_crossdocked.py",
    )
    changed = set(_changed_paths(_single_git_line("rev-parse", "HEAD")))
    if any(
        item == prefix or item.startswith(f"{prefix}/")
        for item in changed
        for prefix in protected
    ):
        raise ValueError("protected source changed")


def _assert_lifecycle_stable(
    initial: LifecycleSnapshot, final: LifecycleSnapshot
) -> None:
    if initial != final:
        drifted = tuple(
            name
            for name, first_value, final_value in zip(
                LifecycleSnapshot._fields, initial, final, strict=True
            )
            if first_value != final_value
        )
        raise ValueError(
            "checker lifecycle snapshot drift: " + ",".join(drifted)
        )


def main() -> int:
    initial = _lifecycle()
    _verify_source_boundary()
    _verify_public_source()
    _verify_signature_and_identity()
    runtime_report = _verify_runtime_matrix()
    evidence_report = _verify_evidence()
    _verify_repository_safety()
    final = _lifecycle()
    _assert_lifecycle_stable(initial, final)
    refs = {record.name: record.oid for record in final.refs}
    report = {
        "all_checks_passed": True,
        "lifecycle": final.lifecycle,
        "head": final.head,
        "branch": final.branch or "DETACHED",
        "origin_main": refs["refs/remotes/origin/main"],
        "origin_head_symbolic_target": final.origin_head_symbolic_target,
        "origin_head_resolved_oid": final.origin_head_resolved_oid,
        "index_sha256": _sha256(final.index),
        "status_sha256": _sha256(final.status),
        "status_entry_count": len(
            tuple(item for item in final.status.split(b"\0") if item)
        ),
        "persistent_ref_count": len(final.refs),
        "worktree_count": len(final.worktrees),
        **runtime_report,
        **evidence_report,
        "base_commit": BASE,
        "exact10_count": len(EXACT10),
        "source_boundary_count": len(SOURCE_BOUNDARY),
        "lifecycle_mode_count": len(LIFECYCLE_MODES),
        "canonical_mask_count": len(CANONICAL_MASKS),
        "current_permission": False,
        "action_permission_granted": False,
        "feature_semantics_audit_completed": False,
        "ready_for_training": False,
    }
    if (
        report["current_permission"] is not False
        or report["action_permission_granted"] is not False
        or report["ready_for_training"] is not False
    ):
        raise ValueError("checker readiness assertion failed")
    sys.stdout.write(json.dumps(report, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
