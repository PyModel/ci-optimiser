# Self-hosted fixed fleets

Reviewed **2026-11-26**. Load when `discover_repo.py` emits adapter
`self-hosted-fleet`, or when inspected jobs use self-hosted runners. These are
experiments, not defaults. Missing timings, prices and peak RSS stay **unknown**.
The [strict contract](14-two-minute-ci.md) and [security rules](03-security-correctness.md)
outrank speed. Facts below are from [fleet sources](06-official-sources.md#self-hosted-fleet-sources-2026-11-26);
anything not listed there is not confirmed.

Hosted, Blacksmith and Depot pools stay in [module 1](02-optimization-playbook.md#1-fast-runners).
This file is the private fixed-fleet branch of that module.

## When this applies

A small or medium GitHub Actions fleet you already own: Linux build hosts, a
macOS/iOS host, and polyglot work (Android/Gradle, JS/Turborepo/pnpm, Go,
Playwright, Docker). The win, when there is one, is less work on the wrong
machine and warm local disk. It is not an autoscaler.

Do not adopt Actions Runner Controller or the scale-set client on a fixed machine
count. GitHub recommends ARC for organizations that already run Kubernetes.
Autoscaling is documented with **ephemeral** runners; persistent runners are not
the recommended autoscaling shape, because a job can still be assigned while a
persistent runner shuts down. An autoscaler does not add throughput you have no
capacity to scale into.

## Order

Screen in this order. Apply the first item that is the measured required-path
bottleneck. One change at a time. Keep the incumbent when it wins.

| Order | Experiment | Existing contract it must not weaken |
|---|---|---|
| 1 | Job-level path selection plus an always-on aggregate | [Required checks](03-security-correctness.md#required-checks-and-skips). Selection narrows PR feedback only. |
| 2 | Route by hardware profile. Keep low-RAM hosts and Macs out of the heavy Linux pool | Label match is not a priority scheduler. See [routing](#routing-and-slots). |
| 3 | Size concurrent slots from measured peak RSS, not CPU cores | Missing RSS is unknown. Do not invent a slot count. |
| 4 | Prefer warm local disk over `actions/cache` on persistent runners | [Module 4](02-optimization-playbook.md#4-caching-and-blobless-clone). Compare archive-on and archive-off from the same warm disk. |
| 5 | Gradle: one JVM-arg identity, build cache and configuration cache as separate trials | [Android adapter](10-stack-adapters.md#android-and-gradle). |
| 6 | LAN remote caches (Gradle HTTP, Turborepo) only inside the trust boundary | [Cache poisoning](03-security-correctness.md#cache-poisoning). |
| 7 | Shard Playwright onto idle slots that fit the measured RSS | [Playwright adapter](10-stack-adapters.md#playwright). |
| 8 | PR `cancel-in-progress`, plus a per-job group for a heavy slot | [Concurrency recipe](07-config-recipes.md#parallel-jobs--one-aggregate-required-check). Never cancel queue or main. |
| 9 | Install pnpm itself; do not pay the Corepack shim on every invocation | Trusted jobs alone may write the store. |
| 10 | Pre-job cleanup hook and a disk-space fail | Nonzero exit fails the job. No retries. |
| 11 | zram only as a spike net, never as another slot | Not a measured gain. See [not confirmed](06-official-sources.md#not-confirmed-for-self-hosted-fleets-2026-11-26). |
| 12 | LAN proxies after local disks are warm | Docker Hub pull-through is Hub-only. |
| 13 | ARC or another autoscaler | Skip unless elastic capacity, isolation, logs and cost are reviewed. |

Affected graphs still need a reachable base. A shallow checkout is the known
Turborepo failure mode in module 4 (`fetch-depth: 0` with `filter: blob:none`
when history is required). Do not add a second checkout rule here.

## Trust

Public repositories and fork PRs stay on ephemeral runners. A persistent runner
executes workflow code on your hardware.

A private trusted fixed fleet may keep persistent runners only when all of these
hold:

- Untrusted events do not run there, or they use isolated homes and cannot write shared caches.
- Trusted jobs never restore a cache an untrusted job wrote. GitHub's PR cache scope does not apply to a local disk or an anonymous LAN server.
- Concurrent slots do not share a Gradle user home until concurrent use is proven safe. Shared-home lock contention is not confirmed.
- The cleanup hook fails the job when disk is below the reviewed threshold. It does not delete evidence of the failure.
- The merge queue still runs the full suite on the combined candidate. PR selection does not satisfy that gate.

The [fresh-runner default](14-two-minute-ci.md#runner-and-setup-changes) still
applies to hosted and untrusted paths. Persistent state is an exception after a
paired measurement, not a new default.

## Routing and slots

Documented assignment picks an online idle runner that matches **all** `runs-on`
labels and groups. The reviewed routing section has no weight or priority field.
If the assigned runner does not pick up the job within 60 seconds, the job is
re-queued. A job that stays queued more than 24 hours fails. A label with no
idle match waits; it does not fall back to a smaller host.

Removing a slot without removing the pool label still lets that host claim heavy
work. Re-check labels after reprovisioning. Whether replacement drops custom
labels is not confirmed.

Example labels, not a GitHub default: a high-RAM Linux host carries the shared
pool plus `heavy` and `quick`; a 16 GB host carries one `heavy` slot and one
`quick` slot; a Mac carries `macos-arm64` / `ios` and is not in the heavy Linux
pool. A repository variable may hold the shared label list so one change retargets
the pool. Verify the variable before relying on it. iOS stays on the Apple Silicon
host. A Linux VM on that Mac is not a heavy Android slot unless measured memory
and virtualization say so.

Size slots only from measured peak RSS:

```text
max slots = floor((host RAM - OS and cache-service reserve) / measured per-job peak RSS)
```

Reserve the OS and any co-hosted cache process. Replace the hypotheses below
with `/usr/bin/time -v`, cgroup `memory.peak`, or the host equivalent before
changing slot count. They are not adoption gates.

| Workload | Hypothesis until measured |
|---|---|
| Android / Gradle plus test JVMs | 8–10 GB; one heavy slot on a 16 GB host |
| Web / Next monorepo build | 3–4 GB; cap the Node heap from the measurement |
| Go build and `go test -race` | 2–3 GB if the peak fits the shared pool |
| Playwright shard, 1–2 workers | 2–3 GB on an idle light slot |
| Lint, typecheck, repo checks | 1–2 GB |

## Caches

Runner communication for cache upload and download includes
`*.blob.core.windows.net`. The default repository cache limit is 10 GB; entries
not accessed for 7 days are removed; usage above 10 GB can be billed. On a
persistent runner, restoring that archive over an already-warm disk can add time.
Record runner image, local disk, action archive and toolchain separately.
[Module 4](02-optimization-playbook.md#4-caching-and-blobless-clone) is the
measurement contract. Untrusted events do not save caches trusted jobs restore.

| Layer | What to try | Stop if |
|---|---|---|
| Gradle user home | Keep it on local disk. `setup-gradle` preserves an existing home unless `cache-overwrite-existing` is true. Its cache cleanup runs before a GitHub cache save, on success by default. | The GitHub archive is slower than the warm disk, or two slots share one home. |
| Gradle build cache | `org.gradle.caching=true`. A LAN HTTP cache may push from trusted CI and stay read-only elsewhere only after writers are authenticated. | The server accepts anonymous writes, or cold fallback fails. |
| Configuration cache | Separate trial from the task-output cache. Use warn mode while plugins are incompatible. | A plugin incompatibility fails the required build. |
| Turborepo | Trusted remote cache, with signature verification where that capability is configured. Keep a local cache outside the workspace if the pinned checkout cleans the workspace. | Checkout clean behavior is unconfirmed on the pin, or untrusted jobs can write the cache. |
| Go | Local `GOCACHE` and `GOMODCACHE` are a different layer from `setup-go`'s archive. | The archive restore adds time on an already-warm disk. |
| pnpm | Install pnpm itself. Corepack's shim starts Node on every invocation. Caching the store is not guaranteed to be faster. `pnpm cache path` prints the metadata cache since v11.22.0; verify the installed pin. | An untrusted job can write the store or metadata cache. |
| Playwright browsers | Do not cloud-cache browser binaries; documented restore time is comparable to download time. Preinstall on a persistent runner only after measuring install against reuse. | A version bump leaves a stale browser and the job still passes. |
| Docker Hub | A pull-through mirror avoids repeat Hub pulls and is Hub-only. It does not mirror another private registry. `registry-mirrors` in the daemon config points clients at it. | The mirror holds Hub credentials: those private resources become available on the mirror. |

## Gradle and Playwright

Gradle reuses a daemon only when Java home, Java version and JVM args are
identical. A different `-Xmx` spawns another long-lived daemon. Standardize
`org.gradle.jvmargs` after measuring. Do not paste a heap template. Android's
guide raises the heap (examples 4, 6 or 8 GB) when garbage collection exceeds
15% of build time, and requires an explicit `MaxMetaspaceSize` when the default
memory limit changes. On a 16 GB host, fewer concurrent Gradle builds beat a
larger heap if the slot is already full. Kotlin daemon args are not covered by
the reviewed Gradle daemon page; confirm them before standardizing.

Playwright recommends `workers: 1` in CI for stability, and allows more workers
on a powerful self-hosted system. Shard for wider parallelism. On this fleet,
use 1–2 workers per shard only when the slot's measured RSS fits, enable
`fullyParallel` only when tests are independent within a file, and keep the
existing shard, blob-report and merge gate. A missing shard fails the aggregate.

## Cleanup hook

Set `ACTIONS_RUNNER_HOOK_JOB_STARTED` to an absolute path of an executable script
outside the `actions-runner` directory, via the environment or the runner `.env`.
The hook runs synchronously, blocks job start, and has **no timeout**. Exit 0
lets the job start. Any other exit fails the job. `continue-on-error` does not
apply. Do not print secrets; repository readers can see the log. Put a timeout
in the script. A disk guard that exits nonzero below a reviewed free-space
threshold is a fail-closed check. Prune only reviewed stray containers and temp
paths outside preserved caches. Do not widen the hook to hide a failed job.

## Measure

Baseline several days, then change one thing. Report median and p90/p95 with n.
Group jobs by `runner_name` and labels. `started_at − created_at` is a queue
proxy, not isolated runner wait. Record OOM kills and free disk. Absence of a
check is unknown, not zero OOM and not zero disk-full failures. Watch shared-pool
queue p90, heavy-build median and p90, and useful cache hit rate. A hit-rate
target never overrides a measured regression.

## Pitfalls

- A workflow skipped by top-level `paths` leaves a required check Pending. Gate jobs, not the workflow.
- An in-workspace cache is at risk if checkout cleans the workspace. Confirm that on the pinned checkout; the clean command is not confirmed here.
- Inconsistent Gradle JVM args multiply daemons.
- A host left on the pool label still claims heavy jobs after its slot count is reduced.
- Do not migrate off a cache server on an unverified end-of-support date.
