# CI audit: <repo> (<date>)

Mode: OBSERVE · Window: <from> → <to> · Sample: <n> runs (<m> with jobs) or static-only · Source: <available config, policy and telemetry>

## Answer

<One paragraph: the top bottleneck on the required path, the first intervention, expected wall-clock and runner-minute saving with confidence, and no-change findings. Separate actual acceleration from moving work to another category. If CI already meets its chosen objective with sound gates, say so.>

## Detected stack

| Item | Value | Evidence |
|---|---|---|
| CI provider(s) and coverage | <one row per provider: observed active / configured but unconfirmed / unknown; measured / snapshot / static> | <files, provider settings or run IDs> |
| Languages / package manager | | |
| Monorepo graph | none / Nx / Turbo / … | |
| Test runners | | |
| Required checks | | current snapshot's `raw/required_checks.json`; source completeness/app identity |
| Trust boundaries | fork PRs? `pull_request_target`? deploy jobs? | |

## Merge admission and evidence

Use [native provider guidance](../references/01-discovery-matrix.md#merge-admission-evidence).
Link evidence for the same target repository, candidate, event, workflow, producer
and attempt; current settings alone do not prove historical enforcement.

| Field | Evidence to record |
|---|---|
| Enforcing SCM / rule | <SCM host, repository and target branch, effective required queue/train and full aggregate on every candidate, authenticated policy source and as-of time> |
| Executor / workflow / event | <CI executor, workflow or pipeline, native event and ref> |
| Expected producer / check | <trusted publisher identity and required check context from the effective rule> |
| Actual producer / check | <observed publisher identity, check context, conclusion, reported SHA and evidence link> |
| Combined candidate / base / attempt | <candidate SHA, current base SHA, queued predecessors, run ID, attempt, completion and observation times> |
| Full-suite inventory / result | <independently expected vs observed commands, jobs, tests, shards, reports and coverage; trusted checkout evidence per required job; exact results and policy/build-input fingerprints> |
| Strict admission / bypass decision | <eligible / blocked / unverified; effective bypass or alternate path; rule and check-source evidence at the decision; blocker or next authorized read-only proof> |

The reported SHA and the actual SHA executed by every required job must both match
the combined candidate SHA. Correct status attachment cannot excuse a wrong checkout.
Require fresh full execution, a passing required aggregate and no effective bypass.
Skipped, neutral, failed, cancelled or timed-out required work never passes, even
if the native aggregate is green. A stale result, wrong producer or PR-head status
is not candidate proof. Mark known violations **blocked** and denied or missing proof
**unverified**; neither is eligible. Preserve the first failure even if a later run
is green.

## Four validation categories

Use the [validation architecture](../references/08-validation-architecture.md). Classify each command by inspected behavior, not its name; a command may cover more than one category.

| Category | Verified commands / unique failure modes | Trigger and exact revision | Gate / required completion boundary | Coverage / evidence gaps |
|---|---|---|---|---|
| 1. Code rules | | | authoritative CI; installed fast pre-push hook | |
| 2. Change correctness | relevant tests; FULL conditions | | PR acceptance | |
| 3. Integrated main | full required suite | combined queue candidate | full suite before main admission | |
| 4. Release readiness | artifact, compatibility and rollout checks | immutable artifact digest | release / promotion | |

Main policy: full suite in the required merge queue/train before main. See [merge admission and evidence](#merge-admission-and-evidence) for the decision and blockers. Post-push/nightly runs are supplemental.

Queue controls: <full inventory, no test-result cache replay, unique concurrency group, all entries pass>. PR-only selection fallback: <documented FULL triggers, or keep full PR suite>. Preserve or grow rules and required checks; list any activation blocker.

## PR feedback objective

Use the [strict performance targets](../references/14-two-minute-ci.md#acceptance-and-audit).
Record target, observed value and coverage separately. For each proven enforced
stage/job bound, report at-limit and over-limit results as failures. Do not treat
rolling percentile or cache targets as per-run deadlines.

| Metric | p50 | p95 | n / window | Start → finish / limitations |
|---|---|---|---|---|
| Latest-revision PR feedback | unknown | unknown | | exact push receipt → first authoritative, trustworthy success or failure for that revision's first execution; report outcomes separately |
| First-push PR journey | unknown | unknown | | first push in PR window → first trustworthy complete green for a current revision, including repair/re-push delays |
| Pre-main queue validation | unknown | unknown | | queue entry → authoritative result for the exact combined candidate; separate queue wait and full suite execution |
| Post-push observations | unknown | unknown | | main push receipt → supplemental result for the exact main SHA; not admission evidence |
| Censored outcomes and breaches | | | | counts and oldest age of unvalidated, cancelled, superseded, unfinished and budget-aborted work |

Timestamp provenance: <provider push/event receipt / named diagnostic proxy /
unavailable>. Break out approval wait, dependency wait and runner wait without
subtracting them from elapsed feedback; include dispatch, setup and final
reporting. Retain earlier failures; execution retries are diagnostic only.
For an approval-only predecessor, record the [required hold evidence](../references/08-validation-architecture.md#pr-feedback-budget);
approval does not restart the clock.

## Baseline

Snapshot ID/hash manifest: <path/identity>. Enumeration and retention limits:
<complete within selected query / capped / unknown>. Cohort identity: <event,
workflow/config, runner, trust, cache, workload>. Failed fetches and missing attempt
history: <counts and effect>. Normalized dependency graph: <source/expansion proof>.

| Metric | p50 | p95 | n | Definition / limitation |
|---|---|---|---|---|
| analyzer push→green proxy | | | | approximation, not a substitute for the PR objective above |
| slowest workflow wall | | | | |
| each job: runner wait | | | | use native timing where proven; name any created → started proxy and distinguish dependency and approval waits |
| each job: setup | | | | explicit phase markers; missing evidence unknown |
| each job: running | | | | preserve work inventory and outcomes |
| slowest required job: runner elapsed | | | | start → completion, including setup/save/teardown; distinguish it from the longest required path |
| lint, format, typecheck, test work per shard | | | | record separately per applicable command/shard with provenance |
| each job: teardown/unattributed | | | | do not add overlapping percentiles |
| setup share | | | | |
| shard skew | | | | |
| suspected same-run retry recovery | | | | logs distinguish flakiness, repair and intentional reruns |
| first-pass failure rate | | | | verify attempts; separate intentional reruns and repair delay |
| gap to runner-up job | | | | observational only; dependency-path recomputation determines possible saving |
| exact eligible PR dependency-cache hits | unknown | | | exact primary-key hits / full eligible denominator; separately show fallback, misses, errors and unknowns |
| local pre-push wall time | unknown | | | installed hook, including startup; not a CI result |
| cost per merge | unknown | | | needs pricing |

Critical path: `<job A> → <job B> → <job C>` (see `critical-path.md`). Gating job: `<name>`, last in <k>/<n> runs, required: yes / no / unknown. Config changed in window: no / yes → `--since <date>`.

## Live research

Follow [live research](../references/16-live-research.md). Use dated primary
sources to compare only material alternatives with the incumbent and the smallest
compatible tune.

| Public component | Current → candidate | Version/support and compatibility | Source URL and date checked | Decision / unresolved gap |
|---|---|---|---|---|
| <tool, feature, runner or rates> | | | | |

Cost basis: <plan/SKU, metered scope, native per-item rounding/rate, shared allowances,
currency/period, matched volume and successful-merge denominator>. Report runner
time, native billable units and money separately; distinguish actual billing from
estimates. Include all billable cohorts (including failures and reruns) and material
ancillary/self-hosted costs per the [cost contract](../references/14-two-minute-ci.md#small-prs-and-cost).
Missing required inputs mean unknown cost or savings, not zero.

## Option screen

For each family record applicability and a disposition: **keep**, **tune**,
**replacement candidate**, **insufficient evidence**, or **not applicable**.
Do not mark missing evidence as not applicable. The
[playbook](../references/02-optimization-playbook.md) governs adoption; consult
the [conditional defaults](../references/14-two-minute-ci.md#runner-and-setup-changes) for matching measured bottlenecks.

| Family | Applicability | Disposition | Reason / next proof |
|---|---|---|---|
| Faster runner | | | <runner wait or execution bottleneck; capacity, scaling and cost evidence> |
| Lint/typecheck | | | <addressable check time; framework and diagnostic/output parity> |
| Workers/shards | | | <slowest shard, resource limits, isolation and complete reports> |
| Cache/checkout | | | <setup/transfer cost, cold path, trust and needed history> |
| Parallel jobs/steps | | | <independent required work after accounting for capacity, setup and transport> |
| Affected tasks | | | <verified graph and FULL fallback vs a cheap full PR suite> |
| Hooks | | | <requested, applicable and fast; CI stays authoritative> |

## Ranked recommendations

Shortlist only material choices, including keep when it wins. Label each effect
**observed**, **modelled** or **unknown**. Distinguish required-path acceleration,
redistribution and cost-only savings. A static lead is not a measured gain.

| # | Choice vs incumbent | Effect / bottleneck | Δ required-path p50/p95 | Δ runner-min/mo | Δ native units / money | Evidence / n | Risk / effort | Next proof |
|---|---|---|---|---|---|---|---|---|
| 1 | <top material choice or keep> | | | | | | | |

Combined wall-clock saving: <recomputed path or unknown, not the sum of rows>.
Recompute total runner minutes separately; don't double-count shared work.
Show comparability, sample size and uncertainty per the [measurement guide](../references/04-measurement-benchmarking.md#evidence-tiers).

## Evidence identity and release eligibility

For explicit release questions or relevant versioned release evidence, use the
[release automation review](../references/17-release-automation.md). Name the actual release host
and project separately from the enforcing SCM and CI executor; a mirror is not host
evidence. Record KEEP / ADOPT / FIX / NOT APPLICABLE, observed release state,
recommended workflow, dated sources, exact approval boundaries, evidence gaps,
verification, rollback, and one next action.

- Source identities: <PR/base/candidate/final-main SHAs and verified mapping; rerun if equivalence is unproven>.
- Workload and policy fingerprint: <commands/test IDs/coverage/graph/workflow/toolchain/build inputs; no secrets>.
- Artifact: <immutable digest, exact build source, provenance, required evidence links and expiry>.
- Eligibility: <full-green source + matching policy/artifact + category 4 checks for this stage; preflight before initial exposure, telemetry before further promotion; later main commits inherit no green>.
- Release plan: <flag states and staged exposure with telemetry thresholds/window/minimum samples/abort owner, or package/staging/consumer compatibility gates>.
- Migration/data effects: <compatibility, recovery or roll-forward proof; feature flags alone insufficient>.
- Release/deploy/publish authorization: <existing scope or required separate action; gate success alone grants none>.
- Evaluation result: <policy fingerprint, evidence observation age, requested result and exact status>. Use `--require` when consuming an evaluator result as a gate; successful report generation alone is not validation success.
- Rollout identity: <deployment ID, environment, active-stage activation time; telemetry window after activation; comparable baseline proof when relative thresholds are used>.

## Migration proof

- Selected-versus-FULL shadow comparison on identical representative revisions: <results, test identities, real omitted-defect negative control, unknowns>.
- Test pruning, if proposed: <two-week failure log, protected coverage, proved redundant detection and retained guard>.
- Failure probes: <child failure, unexpected skip, cancellation/timeout, missing report/shard, wrong/stale SHA or policy/artifact mismatch all reject green/eligibility>.
- Workload state: <same / reduced / increased / changed / unknown; match identities, not counts, before claiming same-work speed>.
- If redistributed: <work retained across PR + queue + post-push + release; total runner-minutes; PR gain; full-green delay; changed detection window/risk>.
- Planned trials, cached results and local template checks do not establish hosted or model performance.

## Risks found (independent of speed)

- <false-green pattern, privileged trigger, unpinned action, missing timeout…> — file:line — severity

## Next reversible action

<One read-only measurement, or one proposed experiment/change with a success
criterion, negative proof, stop/rollback condition and owner. Record approval
needed before any write, remote dispatch, paid trial or live settings change.>

## No-change findings

- <module>: NOT APPLICABLE because <evidence>.

## Limits of this audit

- <missing data, low samples, approximations>

For ranked causes, give observed savings per affected push and runner-minutes
separately from a modeled upper bound. Include affected pushes / total and days
observed. If the ranking depends on an unmeasured ceiling, state which comparison
would decide it. Label each outside claim as a provider fact, reported case,
calculation or policy choice, with date and scope.
