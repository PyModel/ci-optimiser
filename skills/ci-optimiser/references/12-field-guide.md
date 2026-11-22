# Audit field guide

Load when conducting an audit or preparing a scoped optimization PR. Apply the [strict contract](14-two-minute-ci.md) first; old policy formats remain diagnostic compatibility only.

## Entry checklist (before any change)

Script paths are relative to this skill's directory. Use a private scratch
directory (`AUDIT`) outside the target checkout for evidence; leave repo files and
Git metadata untouched in `OBSERVE`. Scripts require Python 3.10+ stdlib; read
each script's `--help` before using it.

1. Read repo policy, actual CI config and merge requirements. For a proposed change
   to a deliberate setting, read its history. Inventory from the canonical,
   nonsymlinked repo root: `python3 scripts/discover_repo.py --root REPO > AUDIT/discovery.json`.
   Keep raw evidence private: parsed fields may contain sensitive literals.
2. Verify the detected providers, actual commands, tools/pins and dependency graph
   with the [discovery matrix](01-discovery-matrix.md). Map triggers, includes,
   checks required at each boundary and the full-suite gate. Distinguish fork
   PR, trusted branch, queue and release permissions.
3. Prefer the requested connector or an existing authorized provider connection.
   Sample up to 150 runs across outcomes, configurable; split PR, main, scheduled,
   config eras and attempts. Record where history or policy is inaccessible. A
   non-GitHub provider may have only native exports, a snapshot or static evidence;
   never coerce missing fields into the GitHub format or collect past authorization.
4. Report metric coverage (required-path p50/p95, waiting, setup, execution, runner
   usage, cache efficiency and retries). Separate outcomes and sources; missing
   metrics are **unknown**, never zero. Do not call the longest job the required
   path without its dependencies and gate identity. Use the [safety policy](03-security-correctness.md)
   and relevant [stack adapters](10-stack-adapters.md).
5. Verify current options and costs with [live research](16-live-research.md),
   then complete the audit even if you have only static evidence.

### GitHub Actions history

- With authenticated read-only access to the verified target, collect:
  `python3 scripts/collect_gh.py --repo OWNER/REPO --limit 150 --include-incomplete --retries 0 --out AUDIT`.
  Use `--event pull_request --target-branch main` or `--event push --branch main`
  for scoped cohorts; `--branch` filters history, not protection. Exit 3 means
  evidence is incomplete. If only protection is inaccessible, request timing-only
  evidence with `--timings-only`; report protection as unknown.
- Analyze: `python3 scripts/analyze_gh.py --input AUDIT --output AUDIT/metrics.json`.
  It separates attempts and reports runner usage and rounding estimates, not a bill.
  Add `--graph`, `--cohort-context`, `--pricing` or `--since` only
  with matching reviewed evidence. Run-created latency is a diagnostic proxy.
- For safety/eligibility review, `inspect_workflows.py` accepts YAML 1.2 normalized
  to JSON; resolve matrices and reusable workflows separately. `evaluate_validation.py`
  evaluates reviewed policy and normalized evidence for an exact candidate; it
  does not authenticate sources or certify the strict percentile/queue contract.
  See [evidence formats](11-evidence-formats.md).

**Evidence rule:** every number in an audit carries source, time window, sample size, metric definition and limitations. Compare the same workflow, event and runner class; keep fork PRs apart from privileged release builds. A YAML pattern match is a lead, not a finding: a finding needs positive evidence from this repo's runs ([evidence tiers](04-measurement-benchmarking.md#evidence-tiers)).

**Two axes:** size every candidate on Δ wall-clock and Δ runner-minutes separately. Upstream jobs can shorten the critical path even when they finish before the last job; recompute the dependency graph. Distinguish execution acceleration from moving work between validation categories ([sizing](04-measurement-benchmarking.md#sizing-and-combining-savings)).

## Operating workflow

### A. Diagnose and prioritize (no modifications)

1. Complete the four-category current/proposed map and policy decision, then reconstruct the DAG; separate queue, setup, steps and critical path. GitHub's jobs API gives timings; the `needs` edges come from YAML. Preserve existing gates while unknowns are resolved.
2. Screen the seven modules and fill the ranked recommendations table. Name why
   high-profile but inapplicable options don't fit.
3. Order by **measured saving in the biggest bucket on the required path**, with correctness first; do not impose a tool-migration order before measurement. [Measurement guide](04-measurement-benchmarking.md).
4. Run the [pre-publish review](03-security-correctness.md#before-publishing-a-report), then deliver the report and proposed sequence. If scoped implementation is already authorized, continue; otherwise stop before the unapproved action.

### B. Benchmark one change

1. Freeze baseline commit, toolchain versions, runner architecture and config. Measure warm cache, cold cache and queue separately.
2. Run ≥10 comparable repetitions; low-sample tails remain preliminary. `benchmark.py` runs **exactly** the argv after `--`, with no shell:
   `python3 scripts/benchmark.py --label baseline --runs 10 --metadata REPO/.ci-audit/benchmark-context.json --out REPO/.ci-audit/experiments/baseline.json -- npm test`
   Compare with `--baseline`, or use reviewed JSON `--candidate-command` for balanced paired trials. Declare workload/toolchain/cache/runner identity; capture source before and after. Failed warmups, source mutation, incomplete process-group cleanup or missing comparability invalidate a claim. POSIX process groups are cleanup, not a sandbox. Review commands for side effects: deployments, payments, migrations and destructive operations are never benchmarked.
3. Compare p50/p95 wall time, end-to-end required-check time, spend per merge, cache restores, flakes, diagnostics, tests run, coverage, builds and artifacts. A correctness or security regression rejects the change whatever the speed-up.
4. Selector changes: run `scripts/select_affected.py` against adversarial diffs (lockfile, root config, CI file, schema, migration, cross-package rename); it is a reference oracle, not a substitute for the build tool's graph.
5. Record the experiment and decide `ADOPT`, `REJECT`, or `INSUFFICIENT EVIDENCE`.

### C. Implement and verify

- **One independently reversible PR per intervention.** Runner migration, test selection, test isolation and permission changes each ship alone. Use the [optimization PR template](../templates/optimization-pr.md); config starting points are in [recipes](07-config-recipes.md).
- Keep existing check names and required gates. Run full relevant verification on the change, and prove each changed gate goes red on a probe commit.
- Workflow permissions or cache trust boundaries changed → security-owner review. Cost, vendor or trust jurisdiction changed → project-owner review. Coverage, isolation or affected selection changed → test-owner review plus mutation checks.
- Success is claimed from post-merge CI telemetry, not local benchmarks: reruns, workload state and gate migration per [CI-side verification](04-measurement-benchmarking.md#ci-side-verification).
- Gate redistribution: shadow selected vs full results, retain the full-suite oracle, prove event-specific aggregates and exact release provenance, and account for risk/latency transferred to integration. A smaller PR workload is not a same-work speed-up.

### D. Monitor, adapt, roll back

Track p50/p95 push→green, queue/setup breakdown, p95 critical path, cache efficiency, reruns, skipped-vs-full selection, cost per merged PR, false greens, escaped defects and release provenance. Re-assess after each change: bottlenecks move. When another job becomes the gate, report the new gate, not the old job's gain as wait removed. Enforce waiting <10 s, setup <30 s, lint/typecheck <5 s and test work <60 s per shard. Investigate any retry, false green or threshold breach; report rolling PR p50/p95 separately. Rollback triggers: [measurement guide](04-measurement-benchmarking.md#monitoring-and-rollback).

Check the agreed PR budget and category-3 completion/freshness independently. Give full pre-main queue runs unique concurrency groups; post-push coalescing cannot replace them. A failed full run blocks eligibility for that commit; follow the repo's fix-forward/revert policy and incident owner. Missing rollout telemetry pauses promotion.

## Output contract

Return the report and only evidence artifacts that apply. The following is a
suggested private scratch layout; never create placeholder measurements:

```text
AUDIT/                      # outside the target worktree
  discovery.json
  validation-plan.md        # four categories, evidence, budget and accepted policy
  current.json              # atomic pointer to latest collection snapshot
  snapshots/<id>/raw/        # immutable provider payloads + hash/completeness manifest
  metrics.json
  research.md               # dated current/candidate sources, compatibility, price gaps
  validation-policy.json    # reviewed expectations and fingerprinted policy
  validation-evidence.json  # authenticated/verified provider facts, normalized
  validation-result.json    # budget, integration, release and rollout decisions
  ci-audit-report.md        # from templates/audit-report.md
  critical-path.md
  cache-audit.md
  flake-audit.md
  optimization-backlog.md
  experiments/*.json
  rollback-plan.md
```

The report states the detected stack, four-category plan, PR budget, full-suite and release contracts, top bottleneck, seven-module status, risks, baselines, confidence and limits, ordered PR plan, acceptance criteria, no-change findings, cost trade-offs and rollback. Template: [audit report](../templates/audit-report.md). Worked shapes: [examples](05-worked-examples.md).
