# Strict performance contract

Reviewed 2026-11-22. This is the source of truth for skill targets. Older examples
and deployed policies keep their own semantics; none certifies this profile by
default. Targets are not vendor guarantees or measurements. Choose stack/provider
optimizations with [live research](16-live-research.md) and target evidence.

## Contents

- [Acceptance and audit](#acceptance-and-audit)
- [Queue and cancellation](#queue-and-cancellation)
- [Runner and setup changes](#runner-and-setup-changes)
- [Parallel work and test reuse](#parallel-work-and-test-reuse)
- [Two-week pruning review](#two-week-pruning-review)
- [Selection negative control](#selection-negative-control)
- [Local enforcement](#local-enforcement)
- [Budget enforcement](#budget-enforcement)
- [Small PRs and cost](#small-prs-and-cost)

## Acceptance and audit

| Metric | Target |
|---|---|
| First-execution PR feedback | `p50 <60 s / p95 <120 s` |
| Per-job runner wait | `<5 s` |
| Per-job setup | `<15 s` |
| Slowest required job, elapsed on runner | `<35 s` |
| Lint work | `<1 s` |
| Format work | `<1 s` |
| Typecheck work | `<5 s` |
| Test work per shard | `<30 s` |
| Exact eligible PR dependency-cache hits | `>95%` |
| Local pre-push wall time | `<9 s` |

Use the complete applicable cohort for rolling targets. Enforce only proven
stage/job bounds (including local pre-push where applicable); fail at equality
or over the enforced limit. Report unmet or unknown objectives, not false greens.
Do not copy these numbers into an unmeasured pipeline or substitute them for its
existing limits. Define build and reporting bounds from the measured path.
Preserve or grow the rules and required checks even when targets are missed.

Retrieve up to the last 150 runs by default (configurable), paginating jobs and attempts, including failures,
cancellations and incomplete runs. Retention or fewer available runs limits the
sample; never fabricate the remainder. Split event, workflow/config era, runner,
cache state and first execution versus diagnostic rerun. Keep a failed original
attempt even when a later attempt passed. No check rerun substitutes for a code fix.

Report one row per job: runner wait, setup, work and runner elapsed p50/p95, n,
outcomes, timestamp source and gaps. Runner wait starts when the job is eligible for
a runner. Setup is runner start to first required work; runner elapsed is runner
start to job completion, including setup, work, save, teardown and gaps. Time each
required command; test work per shard is not whole-job time. Expose reporting and
unattributed time. Resolve step names against the commands; analyzer heuristics
and a created-to-start timestamp pair are diagnostic proxies, not proof of
isolated phases. Keep approval and dependency wait separate.

Rank the largest measured bucket on the required DAG. Do not sum parallel jobs
or their percentiles to estimate PR time. Record total runner seconds separately.
Use one stated percentile method across comparisons (the analyzer uses nearest-rank). A small sample's p95 is descriptive; one fast run cannot establish a reliable tail.
Use the [PR feedback budget](08-validation-architecture.md#pr-feedback-budget)
for first-execution outcomes, the PR-only approval exception and the full PR journey.

## Queue and cancellation

Enumerate the baseline suite, new tests, platform/database variants, build/type/coverage and migration obligations. Existing protection may omit required work; do not equate its current check list with the complete suite. Require that full suite on the actual combined queue candidate before main admission.
Preserve the existing required aggregate identity. For GitHub Actions, use this
`merge_group` and concurrency pattern:

```yaml
on:
  pull_request:
  merge_group:
    types: [checks_requested]
  push:
    branches: [main]
concurrency:
  group: ci-verify-v2-${{ github.event_name == 'pull_request' && github.run_attempt == 1 && contains(fromJSON('["opened","synchronize","reopened"]'), github.event.action) && format('pr-{0}', github.event.pull_request.number) || format('run-{0}-{1}', github.run_id, github.run_attempt) }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' && github.run_attempt == 1 && contains(fromJSON('["opened","synchronize","reopened"]'), github.event.action) }}
```

For external CI, [verify the native queue event, exact candidate and expected check publisher](01-discovery-matrix.md#merge-admission-evidence).
Use unique queue/main concurrency groups. A shared group can discard a pending
candidate even with `cancel-in-progress: false`. Cancel only superseded PR work;
release runners, processes and databases when cancelled.

Verify the provider rule requires the merge queue and full aggregate, and requires
every queue entry to pass. Preserve existing review/security requirements; remove
any bypass only within the authorized scope. Do not use admin bypass yourself.
Adding YAML does not activate a ruleset. Public organization repositories support
GitHub merge queues without an Enterprise upgrade; inspect actual repository eligibility.

Disable affected selection and task-result cache reads on the queue. Examples:

```sh
nx run-many -t test --skip-nx-cache
turbo run test --force
```

These force execution; they do not replace inventory, coverage or report checks.
Keep dependency/transform caches only where they cannot replay test conclusions.
Scheduled full runs supplement the queue. Post-push validation cannot protect main
retroactively. If activation is blocked, finish the code/PR and report the exact blocker.

## Runner and setup changes

Compare the current pool and smallest native tune first. If a measured GitHub
runner bottleneck warrants a switch, prefer Blacksmith among compatible candidates
and test warm ephemeral images where supported. Verify organization GitHub App
access, plan, capacity, architecture, trust isolation, permissions and cleanup.
Use a fresh runner per job; warm toolchain state must be trusted and pinned, with
no secrets, prior test results or untrusted work carried forward. Compare cold and
warm runs at the same load, including wait, setup and execution. Keep the incumbent
if parity, speed or cost does not justify switching. See the [dated sources](06-official-sources.md#strict-profile-tool-checks-2026-11-22).

Seed trusted dependency caches from trusted main where supported. For JS,
compare exact-key `node_modules`, package stores and cold installs when setup
dominates. Require exact OS/image, arch, runtime ABI/version,
package-manager version, lockfile, workspace layout, install flags, trusted lifecycle
settings and patch/config compatibility. Do not restore a broad old dependency tree
as valid without a frozen reconciliation. Never put secrets in caches.

Count only primary-key exact restores toward the target; distinguish fallback,
miss, restore error and unknown. Use a complete, nonempty denominator of all
eligible PR restore opportunities; unresolved eligibility or outcomes cannot certify it.
Lockfile changes legitimately miss; report them, seed after trusted integration, and
never reuse incompatible dependencies to improve the rate. A cold path must work.
Trusted jobs must not consume artifacts or cache entries writable by untrusted PRs.

When jobs need full history, benchmark a compatible partial clone:

```yaml
with:
  filter: blob:none
  fetch-depth: 0
  persist-credentials: false
```

For direct Git use `git clone --filter=blob:none URL`; do not use `--depth=0`.
Measure deferred blob reads as part of the entire job, not only checkout. Keep shallow
or another strategy when it is faster or cheaper and all required history exists.
Do not add dependency caches to a dependency-free repository merely to fill a checklist.

## Parallel work and test reuse

Run independent required checks concurrently; share setup when measured faster
after accounting for capacity, contention and artifact transport. Do not add
avoidable serial work. If checks share a job, collect and list every check failure
before returning nonzero. Keep genuine build, artifact and schema dependencies.
For shared artifacts, apply the [parallel jobs gate](02-optimization-playbook.md#5-parallel-jobs).
The authoritative aggregate may depend on all required children and must fail
closed on failure, unexpected skip, cancellation, timeout, absent legs or missing
reports. A cost-only candidate is not a speed recommendation.

Where tests dominate, measure CPU, memory, I/O and database contention. Prefer
more cores before adding shards when scaling is proven and within approved spend.
Cap workers against actual capacity; reserve resources for services. Record file
timings on full main runs. Split files over 20 s without losing shared lifecycle,
test identities or coverage; keep an unsplittable file and record the blocker.
If sharding, balance by measured file duration and record the randomization seed
within each shard. Give each DB-backed shard its own database and isolate workers
within a shard. Prove the exact union (no missing or duplicate assignments) and
merged coverage before the aggregate passes. For JS reuse, see
[per-file cleanup and seeded tests](15-toolchain-migration.md#vitest-reuse-and-scheduling).

## Two-week pruning review

For two weeks, classify every test failure with its run/seed, cause, and what
would still catch it: unique regression, duplicate detection, test/state leak,
or runner/infrastructure failure. Leave unclassified and unobserved coverage intact.
Do not prune authentication, authorization, privacy, migration or concurrency
tests under this procedure. Remove only a proven redundant change detector: show
a real defect that the retained check still catches at the same boundary and
prove the rule/test coverage stays intact. Get test-owner review before removal;
retain any unique check. Fix leaks and flakes instead of muting them.

Document banned patterns in the target repo's agent/test guidance: arbitrary
sleeps for readiness, unseeded randomness, order-dependent or shared mutable
fixtures, and retries, quarantine or swallowed failures used to obtain green.

## Selection negative control

Keep a cheap full PR suite if selection would not help. If selecting, use a real
dependency graph and document FULL triggers. Unknown base, graph or coverage and
high-risk changes (e.g. auth, privacy, payments, schema/migrations and CI/selector
policy) force FULL. Map shared contracts/fixtures, lockfiles, generated clients
and runtime/compiler config; use FULL when that mapping is unproven. Include
edited tests and transitive consumers. Malformed results or unexplained empty
selection force FULL or a failed guard.

Prove the failure path with actual execution in a disposable branch/fixture:

1. Record a clean baseline and complete test inventory.
2. Change a dependency so a downstream test genuinely fails.
3. Deliberately hide that dependency edge/change from the selector.
4. Execute the selected work and an independent unfiltered FULL oracle on the same
   revision/environment; retain test IDs, exit codes and reports.
5. Require the comparison/selection guard to fail when selection is green and FULL
   is red. Also prove complete selection catches the same defect directly.
6. Remove the deliberate defect in a new revision and retain the regression test.

Use `evaluate_shadow.py` to compare normalized evidence; invalid/incomplete evidence
must fail. A green selector alone is not a negative control, and invented JSON
outcomes do not prove actual command/transport wiring. Keep the real queue FULL.

## Local enforcement

Preserve the existing working manager or executable hooks and their behavior.
When requested, prefer real hk staged/pre-push hooks only if the repository
needs a manager and measurement supports it. A suggested config is not an
installed hook. Verify installation, executable mode and failure propagation,
and keep changes reversible. See [hk source](06-official-sources.md#strict-profile-tool-checks-2026-11-22).

On pre-commit, format and lint staged applicable files. On pre-push, run the
relevant authoritative CI checks at the same pins and settings; include affected
projects and reverse dependents where required. Pass paths as NUL-delimited
data/argv, never shell-expanded text. Handle new branches, force pushes,
renames/deletions and missing bases conservatively. Measure full pre-push wall
time against the target, including startup. CI stays authoritative because
hooks can be bypassed.

## Budget enforcement

Use `run_budget.py --seconds BOUND --label STAGE -- COMMAND` with a proven
substituted bound. It executes once, preserves failures and fails at equality.
On POSIX, supervise an owned process group; commands must not daemonize or
escape it. Windows fallback controls only the direct child; use an appropriate
supervisor when descendant cleanup is required. This measures work, not waiting,
setup or fleet p95.
Keep provider job timeouts bounded as a final containment limit; never widen them
to hide a regression. A timeout is red even if a signal handler exits zero.

Use explicit phase markers and provider timestamps for waiting/setup/job budgets.
Validate exact job/attempt/SHA identity, all pagination, expected inventory and
successful outcomes. Fail missing/malformed evidence; a zero-exit report writer is
not a passing evaluator. A live verifier cannot certify its own future completion:
mark that duration pending, guard its command, and audit its completion afterwards.
Queues with no assigned runner cannot self-timeout; monitor their age separately.
Do not enforce a duration from an unproven proxy. Once an evidence-backed gate is
active, missing required evidence blocks it; it does not exempt the job.

Evaluate rolling p50/p95 and cache targets from a sufficiently sized comparable
cohort without deleting slow/failed observations. Do not turn synthetic fixtures,
local timings, success-only samples or an unenforced JSON policy into a CI SLO claim.

## Small PRs and cost

Keep one small, authorized PR per intervention: runner migration, tool replacement,
selection and isolation ship separately. Compare exact old/new versions on the
same source and workload, warm and cold. List unique detection, missing behavior,
required fallbacks and real run links. Report incomplete evidence as unknown.

Collect account/app activation, permissions, secrets and incremental spend in one
list after completing everything else. A normal Blacksmith runner migration does
not inherently require a PAT or a new application secret. Quote current rates,
remaining organization-wide allowance, billing granularity and monthly volume.

Apply native SKU rounding/rates per billable item before summing. Include **all
billable cohorts**: queue, main, verification, failures and reruns where billed.
Separate runner time, native units and money; a quota multiplier is not a price.
Add material storage, transfer and idle costs, and list self-hosted equipment
and operator costs apart from vendor bills. Do not multiply the critical path
by one price. Public GitHub standard hosted compute is free; a Blacksmith public
repository is not automatically free. Check the [dated price sources](06-official-sources.md#strict-profile-tool-checks-2026-11-22)
and actual account rates and allowances. Finish with before/after PR wall time,
runner usage, native billable units and cost, with sample sizes; distinguish bills
from estimates and mark missing prices, allowances or after-results unknown.
