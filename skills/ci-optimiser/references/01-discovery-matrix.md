# Discovery matrix

`discover_repo.py` also emits `adapter_candidates`: positive filename/dependency
evidence routes an agent to the [stack adapters](10-stack-adapters.md). A candidate
does not establish version support, measured benefit or authorization. No additional
repository code/configuration is executed to produce these pointers. Non-JS repos
do not receive JS adapters without relevant evidence; missing signals stay unknown.

For GitHub semantics, pass a reviewed YAML-1.2-to-JSON conversion to
`inspect_workflows.py`; see [platform guidance](09-platform-updates.md). Resolve
lockfiles, caller cache limits, parallel synchronization, matrix expansion and
provider capability separately from this bounded discovery inventory.

Map what `scripts/discover_repo.py` found to the modules that may apply. A detection is a hint: open the file before you rely on it.

## Validation architecture before tool selection

Read `validation_topology` alongside `found`, `package_json` and `github_workflows`.
It locates evidence for `rules`, `change`, `integration` and `release`; it does not
prove which jobs implement those guarantees. Follow [the design procedure](08-validation-architecture.md)
to inspect commands, expand provider/reusable configuration and resolve required checks.
Treat absent markers, inaccessible provider policy, truncated scans and unparsed files
as unknown. A script called `test` may cover all tests, selected tests, or no tests.

| Evidence to inspect | Design question |
|---|---|
| Manifests, hooks, lint/type configuration | Which code-rule checks can run quickly locally and authoritatively on PRs? |
| Test configuration, graphs, fixtures, contracts, code generation | Which edited and affected tests prove the change; what forces FULL? |
| CI triggers, protected checks, queue and branch policy | Where does integrated full verification run and when is a commit certified? |
| Packaging/deployment files, flags, rollout and monitoring policy | Which product-specific release gates and telemetry exist? |
| Provider timings and expected arrival rate | Is the proposed PR budget achievable without moving unbounded work elsewhere? |

Inventory all providers before choosing a collector. `providers` groups filename
signals; `root_configs` distinguishes repository-root conventions from nested
examples or components. Verify entries against the actual checkout and repo
metadata: inspected remotes/SCM host, branch/check settings, configured project
connections, and available authorized CLI/API access. An installed tool, matching
remote host or filename is only a lead. Promote `configured_unconfirmed` to
**observed active** only on recent runs/checks bound to this repo or direct
evidence of an active provider configuration. If no signals are found, CI
location is **unknown**: check repo policy, commit statuses or existing provider
settings for custom paths, inline config and external systems. Do not install
tools/hooks, run scripts, resolve dynamic configs by execution or contact
untrusted URLs found in repo files.

## Stack → applicable modules

| Detected | Modules worth evaluating | Usually not applicable |
|---|---|---|
| `package.json` + TS/JS | all seven; module 2 (Oxlint, `bun check`, `tsc` 7) | — |
| `nx.json` / `turbo.json` / `pnpm-workspace.yaml` / Bazel / Pants / Gradle multi-project | 6 (affected) via the tool's own graph | the reference selector, except as a test oracle |
| Python (`pyproject.toml`, `uv.lock`) | 1, 3 (pytest-xdist, `--dist loadfile`), 4 (uv / pip cache), 5, 7 (ruff, mypy/pyright) | 2 (JS-only) |
| Rust (`Cargo.toml`) | 1, 3 (`cargo nextest`), 4 (target dir + registry cache, sccache), 5 | 2 |
| Go (`go.mod`) | 1, 3 (`go test -p`), 4 (module + build cache via setup-go), 5 | 2 |
| JVM (Gradle/Maven) | 1, 3, 4 (Gradle build cache, configuration cache), 5, 6 (Gradle's own up-to-date checks) | 2 |
| Single small package, CI < 3 min | 4 and 5 only if setup dominates; often **no change** | 1, 6 |
| No CI config found | report CI location unknown; inspect repo policy and provider/UI configuration | no automatic gate-removal or tool-migration proposal |

## CI provider adapters

| Provider | Local signals | Inspect statically | Evidence support |
|---|---|---|---|
| GitHub Actions | `.github/workflows/*.{yml,yaml}` | Events, `needs`, reusable workflows, matrices, runner class, cache trust and required checks/rulesets | Bundled history collector and analyzer; [field guide](12-field-guide.md) |
| GitLab CI | `.gitlab-ci.yml` | `workflow`/job `rules`, `include`/`extends`, `needs`, child pipelines, runner tags and cache policy | Static + bundled single-pipeline snapshot; [measured adapters](13-measured-adapters.md#commands-and-evidence-boundaries). History via authorized pipeline/jobs evidence |
| CircleCI | `.circleci/config.yml` | Workflow filters/`requires`, orbs, setup/continuation, executor/resource class and workspaces vs caches | Static; use authorized pipeline/workflow/jobs or Insights data if available |
| Buildkite | `.buildkite/*.{yml,yaml}` or provider config | Upload steps, `depends_on`/wait/block steps, branch filters, plugins and agent queues | Static; use authorized builds/jobs evidence if available |
| Azure Pipelines | `azure-pipelines.{yml,yaml}` or configured path | Stages/jobs and `dependsOn`, templates, conditions, pools, triggers and backing SCM branch policy | Static; use authorized build history and timeline evidence if available |
| Jenkins | `Jenkinsfile` or configured path | Declarative/scripted stages, job/multibranch config, shared libraries, agent labels, parallelism and status publishing. Do not execute Groovy | Static; use authorized controller build evidence if available |

Other recognizable configs (e.g. Bitbucket Pipelines or CodeBuild) and unfamiliar
providers get the same generic audit: map trigger → dependency DAG → runner pool
→ required result and protected merge boundary; trace scripts and cache/artifact
inputs. List unresolved external or dynamic parts. Never substitute GitHub
semantics or assume a nested config is scheduled. Validate native formats against
the dated [provider source index](06-official-sources.md#provider-configuration-sources-2026-11-22).
For external run data, calculate only metrics whose native timestamps and attempt
identities are understood. Use [normalized evidence](11-evidence-formats.md) where
semantics match; do not feed native payloads into `analyze_gh.py`.

## Workflow risk flags from discovery

| Key in `github_workflows` | Why it matters | Action |
|---|---|---|
| `pull_request_target`, `workflow_run` | privileged context; secrets reachable | read [security](03-security-correctness.md#privileged-triggers) before touching |
| `continue_on_error`, `or_true` | may hide failures behind green | prove each is intentional, or flag as a false-green risk |
| `paths_filter` on a required workflow | skipped workflow leaves required check Pending | see [skipped checks](03-security-correctness.md#required-checks-and-skips) |
| `unpinned_action` | supply-chain and reproducibility | pin to SHA per repo policy |
| `fetch_depth`, `blob_filter` | history depth for affected/merge-base | module 4/6 interaction |
| no `concurrency` | superseded pushes keep burning runners | `cancel-in-progress` for PR branches, never for default/release |
| no `timeout` | stuck jobs hold the queue for 6h default | add `timeout-minutes` from p99 × 2 |
| `secret_names` | trust boundary inventory; names only | never print values |
| `push_and_pr_unfiltered` | same-repository PR branches may run twice; fork behavior differs | confirm event/SHA duplication before changing triggers; retain intentional branch verification |
| `pr_types` with `edited`/`labeled`/… | title, label and assignee changes rerun CI on unchanged code | confirm the `types:` sits under `pull_request` (issues/release triggers match too); drop metadata events unless a job reads them |
| no `draft_gate` on heavy PR jobs | draft policy may waste work or defer useful feedback | if skipping is accepted, add `ready_for_review` to PR types and test draft→ready without a new commit; aggregate evaluates intended skips per event |
| `cancel_in_progress_false` | superseded runs finish anyway | intentional for default branch/release; otherwise see `concurrency` |
| `cron` | schedules more often than results are read | match frequency to who reads the result |
| `max_parallel` `1`, `fail_fast` `false` | serialized matrix; siblings may continue after failure | measure contention and diagnostic/coverage needs; fail-fast controls cancellation, not whether failures count |
| `submodules_or_lfs` | checkout payload in jobs that may not read it | confirm the job reads those paths before dropping |
| `sleep` | fixed waits in CI steps; readiness should poll with a bounded timeout | replace with a health check, never an unbounded loop |
| `image_latest` | floating service/container tag: non-reproducible, cache-hostile | pin a version or digest |
| `id_token_write` | OIDC token scope | job-level only, never workflow-wide |
| `no_cache_or_clean` | `--no-cache` / `rm -rf` defeating a cache or a warm runner | check whether the clean is load-bearing (self-hosted runners) |
| `action_pins`, `hints.pinned_action_ratio` | heuristic direct full-SHA share, not complete dependency trust | resolve quotes, local/reusable actions and workflow lockfiles before judging immutable-reference coverage |

## Monorepo graph sources

Prefer, in order: the build tool's graph (`nx graph --file`, `turbo run --dry=json`, `bazel query`, `pants dependents`, Gradle `projects`) → package manager workspaces (`pnpm -r ls --json`) → a hand-written map for `select_affected.py`. A hand map rots: put a test in CI that fails when a new top-level package directory appears without a rule.
