# CI investigation protocols

Use the applicable protocol at discovery, experiment design and post-merge review.

## Workflow safety

**Narrow PR cancellation.** Share a group only for eligible first attempts that test code. Isolate metadata events and historical reruns. Check case-insensitive group collisions across callers, reusable workflows and matrix jobs. Verify cancellation while children run and while a required gate is waiting. Merge must remain blocked.

**Prove folded jobs independently.** Force each constituent command to fail in turn. Preserve its working directory, environment, output and exit code. Check shared ports, files, services and credentials before consolidating jobs.

**Measure the full tool or checkout change.** Include deferred blob downloads in the history-consuming operation and verify its output. Compare approved prebuilt tools at the same version and features. Backtest hang cutoffs against the longest successful jobs and verify a timeout reaches the required gate.

## Evidence and diagnosis

**Close the observation window.** Predeclare both cutoffs and a stopping rule, verify the deployed merge is in scope and wait for every run started in the window to settle. Report exclusions, unfinished runs and new failures. Leave a reproducible pending measurement when evidence is insufficient.

**Report comparable observational uncertainty.** For independent historical cohorts, consider a rank-based shift estimate and interval with assumptions about independence and distribution shape. Show median, sample sizes, failures and tails separately. Use comparable sample sizes when comparing maxima. Use the existing paired benchmark for controlled experiments.

**Close each intervention with a receipt.** Record exact sampling commands, median and tail, runner use, failures, named test parity and verdict. Record mixed, slower and inconclusive outcomes. Separate provisional branch evidence from post-merge results. Share externally only with authorization.

**Rank observed gains separately from ceilings.** Apply a candidate to affected runs only, cap the gain by time actually spent, recompute the required path per unique push and normalize by observed days. Keep off-path compute and rerun delays separate. If a larger ceiling could reverse the ranking, name the measurement that resolves it.

**Turn clues into a diagnostic index.** For each suspected cause, list the clue, confirming evidence, plausible alternative, applicable fix and next measurement. Examples include a silent compile versus a hang and a missing cache versus an unobserved restore.

**Collect within a shared API budget.** Prefer existing snapshots for diagnosis. Estimate calls, reserve configurable quota, check remaining quota during pagination and preserve partial status/reset time. Verify private scratch destinations are untracked and free of symlink redirection before writing there.

## Cache diagnosis

**Correct PR cache scope.** Include a non-default PR base branch in restore-scope guidance. Check for an existing trusted writer before recommending a new warming job.

**Distinguish cache failure modes.** Trace the first writer to an immutable key across jobs sharing its ref and paths. Inspect compiler-cache miss reasons after archive hits. Distinguish retention, eviction and manual deletion using history and actual workflow cadence.

**Normalize cache log evidence.** Emit fixed outcome labels and opaque key IDs. Interpret cache-hit by action and version. Keep ambiguous multi-step matches unknown. Compare complete setup weighted by exact hits, fallback hits and misses against an equivalent uncached arm, including first-run warm-up.

## Tests and reliability

**Compare executed tests directly.** Read JUnit across every expected job and matrix leg. Compare stable test identities and multiplicity across resharding. Detect new skips, retry-only passes, suite errors, missing bodies and failures even when counts match. Report identity collisions and missing reports explicitly.

**Prove the changed test still catches its bug.** For changes to tests, mocks or setup, reintroduce a known defect locally and require the specific changed test to fail for the expected reason. Restore clean state and rerun. Flag changed expected values for review.

**Profile the slowest tests on the gating shard.** Use complete CI durations when available. Mark top-N reports incomplete. Rank by wall time on the last required shard for wait, and by work across all shards for compute. Account for overlap and shared fixtures.

**Preserve the behavior under test.** Check repeated setup, unused services, sleeps and real dependencies. Fake only a dependency outside the behavior being verified. Keep serialization, auth and timing coverage where relevant. Backtest optional per-test budgets on healthy CI observations.

**Reproduce flakes under the original conditions.** Link failures to test identities, distinguish infrastructure failures, and rank by observed frequency and cost. Preserve the original workers, record seed and load, then isolate order, shared state, clock, service or product races. Search for siblings with the demonstrated cause.

**Size flake verification from the failure rate.** Prefer a deterministic regression. Otherwise predeclare an estimation batch, derive a conservative lower failure-rate bound, and size the unchanged post-fix run to detect recurrence. State independence assumptions. Zero observed failures gives no usable lower bound.

## Push discipline

**Quantify avoidable CI rounds.** Count distinct CI-triggering revisions per PR, disclose truncated windows, sample catch-up merges, and measure overlapping superseded work and failed/cancelled minutes. Classify failures that caught real bugs separately.

**Measure hook payback.** Replay historical lint/type failures against the hook. Compare time to those failures with total local hook time across all attempts, including blocked and corrected pushes. Measure runner-minutes separately. Evaluate hook and policy changes in separate cohorts.

**Make agent push rules concrete.** Preserve full output and exit status, forbid self-authored check results and gratuitous branch updates, and inspect bypass actors. Offer project-specific escalation limits and client hooks only where they fit existing policy.

## Skill quality and distribution

**Exercise the skill on miniature repositories.** Pair planted causes with offline history, an immutable starting revision and outcome checks that survive agent commits. Cover diagnosis, repair, preservation of checks and a faster candidate that loses a test. Retain blinded grading for agent reasoning.

**Test the graders themselves.** Run each checker on an untouched sample, a known-good fix and false-green changes. Try dropped exit codes, retries, changed assertions and missing checks. Document which properties require executing a command or inspecting a diff.

**Label the basis of guidance.** Distinguish provider facts, another team’s reported outcome, arithmetic and chosen policy. Attach source, date and applicability. Keep third-party savings out of projected gains unless local measurements support them.

**Record independently inspectable outcomes.** Allow result rows with linked public runs, before/after cohorts, by-name parity and mixed or negative verdicts. Keep private or screenshot-only examples labeled.

**Document first use and portability.** Show one first-run prompt, ranked output and expected collection cost. Distinguish installation, discovery, invocation and successful task execution for each supported agent. Document uninstall for both managed copies and symlinks. Clarify installed-helper versus target-repo paths.

**Check what ships and what gets reported.** Scan distributed examples, docs and fixtures for credential patterns and private paths, reporting only location and category. Ask contributors for failing agent behavior, context, expected result and a regression case.

## Measurement worksheet

For independent observational cohorts, the median of all candidate-minus-baseline
pairs estimates the location shift. Give an interval obtained by inverting a
two-sample rank test only when its assumptions hold; disclose ties, dependent
runs and changes in distribution shape. Keep post-merge drift and experimental
causation separate. For small unequal groups show both ranges and n; comparing
raw maxima favors the smaller sample. Retain the existing preliminary thresholds.

For x failures in a prespecified sample of n independent trials, obtain the lower
endpoint L of a two-sided 95% exact binomial interval. Plan at least
ceil(log(0.05)/log(1-L)) trials at the original load. When L is zero the experiment
cannot size a meaningful retest. Record seeds, conditions and every failure.

| Clue | Confirmation and competing explanation | Intervention and proof |
|---|---|---|
| Long quiet step | Check progress signals and longest healthy duration; a silent compiler can be working | Test a hang cutoff and confirm failure reaches the aggregate |
| Restore succeeds but builds are cold | Inspect tool hit counters, flags, job paths and which writer won | Change one key dimension and compare whole setup time |
| Cache disappears | Compare inventory over time with retention, deletion activity and release cadence | Change save policy only for proven unused entries |
| Long queue | Inspect eligibility, dependencies, approval, concurrency and runner availability | Model the constraint and check eligible-to-start time |
| Many short jobs | Measure repeated setup on the required path | Inject each child failure and verify preserved outputs |
| Slow test shard | Inspect complete timings and concurrent fixtures | Change the dominating fixture or test and replant a known defect |
| Many failed pushes | Classify the failed command and replay it on the historical changed files | Count preventable rounds and total measured hook cost |
| Apparent catch-up churn | Sample merge parents, conflict resolution and protection requirements | Remove avoidable updates and compare distinct CI heads per new PR |

For each unique push, model its change in required finish time capped at the affected
work for that push. Sum these changes over all pushes and divide by observed days.
For hooks, subtract aggregate local time over *every* invocation from avoided time
to a trustworthy failure. Price avoided runner work separately. For cache economics,
weight complete setup by observed outcome frequencies, including restore, residual
install and save. Missing durations or weights leave expected savings unknown.

Use [compare_junit.py](../scripts/compare_junit.py) with `--before DIR --after DIR`
once per expected job/platform leg. Stage all its shards in each directory and
verify the expected artifact manifest on each side first. Names, nested suites,
file and class identify tests across shard moves. Suite errors match by type,
message and diagnostic text within the same suite. Exit 1 signals regression.
Exit 2 means invalid or ambiguous evidence, including overlapping suite errors
with no identifying details or reports beyond the resource limits. Each side
accepts up to 4,096 XML files, 16 MiB per file, 128 MiB total and 250,000 distinct
outcome and diagnostic entries. This comparison supplements the runner's own
required test and coverage gates.

Pipe one reviewed action step from a private local log into
[cache_log_labels.py](../scripts/cache_log_labels.py). Its JSON lines contain
fixed observations and hashed keys. Keep unmatched formats unknown. A restore
message leaves exactness unknown; pair the documented output of the pinned
action with its opportunity before recording an exact hit. Mixed or unattributed
steps cannot establish a hit rate. Keep log files private and out of Git.

Before collecting, inspect the available core quota and reset time. Pass
`--reserve-requests N` to the GitHub history collector to stop further requests
once a response reaches that floor. Shared concurrent consumers may also consume
quota. Prefer a newly created user-private directory outside the checkout. When
an in-checkout destination is explicitly needed, first require a successful empty
`git ls-files -- <destination>` and inspect each destination component and existing
child for symbolic links. Use private external scratch if either check is uncertain.
