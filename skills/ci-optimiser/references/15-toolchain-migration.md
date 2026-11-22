# Toolchain migration without lost checks

Reviewed 2026-11-22. When a measured JavaScript/TypeScript bottleneck warrants a
replacement, prefer the verified Bun and TypeScript 7 candidates below over a
broader migration. Compare the incumbent and the smallest tune first. Prefer
stable pins; use an exact canary only when a needed feature has no suitable
stable path and the exact build passes parity. Verify with
[live research](16-live-research.md); vendor benchmarks are not repo evidence.

## Contents

- [Parity contract](#parity-contract)
- [Migration matrix](#migration-matrix)
- [Type checking and local checks](#type-checking-and-local-checks)
- [Lint and format coverage](#lint-and-format-coverage)
- [Installs and restored dependencies](#installs-and-restored-dependencies)
- [Bun test compatibility](#bun-test-compatibility)
- [Vitest reuse and scheduling](#vitest-reuse-and-scheduling)
- [Reviewed sources](#reviewed-sources)

## Parity contract

Before each switch, run old and new on the same revision, inputs, machine class,
and cold/warm conditions. Record exact versions, command, checked-file/test
inventory, diagnostics, exit status, elapsed time, peak memory and cache state.
Add representative known-bad fixtures, including framework/custom rules and
reverse dependents; two green runs alone do not establish equivalent detection.
List every old-only diagnostic and excluded file with its disposition. Preserve
or grow rules and required checks; keep the old tool or a scoped fallback until
every required detection is covered at the same boundary. Keep one small,
authorized change per PR with linked real before/after runs. Never rerun a
failure to replace its result, weaken options, extend timeouts, or skip tests to
claim parity. Separate benchmark repetitions from acceptance checks.

## Migration matrix

| Existing check | Candidate | Evidence required before removal |
|---|---|---|
| ESLint | Verified `bun lint --no-script`, or standalone pinned Oxlint | Effective rules/options/severities, overrides, plugins, ignores and diagnostics; retain unsupported required rules until replaced. |
| TypeScript typecheck | `bun check --no-script`; TypeScript 7 fallback | Entire project/reference graph, old-only diagnostics, framework generators and negative fixtures; preserve declaration/build validation separately. |
| Local typecheck | Pinned `tsrs --noEmit --fast` | Compare with the authoritative CI compiler on the actual graph and representative errors; document conformance gaps and retain the necessary fallback. |
| Prettier | Verified `bun fmt --no-script --check`, or Oxfmt npm package | Full format inventory, supported plugins/options and reviewed output differences; verify files the standalone binary would omit. |
| npm/yarn/pnpm install and scripts | Bun, committed `bun.lock`, frozen install | Workspace/peer/patch resolution, lifecycle scripts, native/generated outputs, production runtime and script behavior. |
| Isolated Vitest files | Measured `isolate: false` candidate | Same full inventory, executable cleanup, randomized file/test order, stable coverage and no leaked workers/resources. |
| Vitest execution | Verified `bun test`, retaining `vitest` imports where supported | Runtime, declaration and config compatibility, fixtures and hooks, exact tests, failed assertions, reports and coverage. |

## Type checking and local checks

Use the actual installed binaries; verify that the pinned Bun supports its
built-in checker. A package script named `check` overrides bare `bun check`.
Always use `--no-script` in generic automation. Inspect both Bun and its embedded
TypeScript version, then compare against the matching compiler where practical:

```sh
bun --version
bun -p process.versions.typescript
bun check --no-script --all
# For a project-reference graph:
bun check --no-script -b --all
./node_modules/.bin/tsc --version
./node_modules/.bin/tsrs --noEmit --fast
```

Discover the TypeScript 7 package and executable instead of assuming an old
preview: current RC/stable uses `tsc`; earlier `@typescript/native-preview` used
`tsgo`. Record the exact version and supported flags. Keep framework-specific
checks and declaration emission: Bun checking emits neither `.d.ts` nor build
outputs and may read referenced source instead of built declarations. Generate
required types/declarations before checks that depend on them, then parallelize
independent lint, typecheck, build and test work.

Do not substitute `bun check --aot`: its dependency diagnostics/exit behavior
differs from the ordinary required checker. Check TS5-to-TS7 defaults, explicit
`types`, removed options, Yarn PnP and plugin compatibility; fix incompatibilities
without loosening the established checking contract. tsrs conformance is a
measured condition, not a claim inferred from its name or speed.

Follow [local enforcement](14-two-minute-ci.md#local-enforcement). Format/lint
changed files, but typecheck affected projects and reverse dependents with the
actual tsconfig graph. Checking only a changed file and its imports can miss
broken consumers.

## Lint and format coverage

The [1.4.4-tagged Bun docs](06-official-sources.md#strict-profile-tool-checks-2026-11-22)
put built-in lint on canary only. Moving docs describe `.oxlintrc.json` and
`--no-script`; they do not prove the stable pin supports the command. Check the
exact binary and effective rules before trying it. Use stable standalone Oxlint
or the incumbent if an exact canary is not justified.

Export ESLint's effective configuration before migration. Use Oxlint's migration
tool for supported flat configs, and review custom local plugins manually. Enable
all applicable supported rules and framework/test plugins. `-D all` does not
enable plugins and excludes nursery rules; assess nursery rules separately.
Record conflicting/inapplicable rules instead of accepting a noisy config or
blanket disables. Make required warnings fail and report unused disable comments.
Retain a scoped ESLint residual only for demonstrated missing behavior.

Oxlint's `--type-aware --type-check` reports types only in linted files and honors
lint ignores. Keep a whole-project checker; do not infer equivalent coverage from
a combined green result. Compare both `tsrs` and `oxlint-tsgolint` when relevant;
installing tsrs can change the backend automatically, so pin and record it.

Prefer `bun fmt --no-script --check` in CI once the exact pin proves built-in
dispatch and nonwriting checks even with a `fmt` package script present. Verify
exit status, file inventory and options; keep the current formatter if parity is
unproven. Migrate Prettier options/ignores explicitly and review formatting changes.
Oxfmt's default print width differs, arbitrary Prettier plugins are unsupported,
and not every configuration source/option transfers. Use its npm distribution
when required formats use bundled Prettier: the standalone release binary skips
those formats. Verify framework packages/options for Svelte/Astro and the checked
inventory for MDX, Angular and other delegated formats before deleting Prettier.

## Installs and restored dependencies

Use `bun ci` or `bun install --frozen-lockfile`; do not assume CI enables frozen
installs. Compare lockfile resolution and production build/runtime behavior
before removing old package managers, their lockfiles and obsolete scripts.
Review lifecycle trust explicitly; do not blindly trust every dependency.

Seed exact `node_modules` caches from trusted main builds. Include OS/architecture,
runtime/package-manager version, lockfile, all dependency manifests, patches,
install configuration and lifecycle trust inputs in compatibility keys. Run frozen
verification after restore; measure restore plus verification against cold install.
Do not treat a broad fallback dependency tree as an exact usable hit.

A frozen Bun install does not rerun lifecycle scripts for packages already in
restored `node_modules`. Invalidate or explicitly rebuild when native ABI,
generation, patch or trust inputs change; verify expected generated/native outputs.
Measure exact usable PR hits separately from fallback hits, misses, failed restores
and unknowns. Do not raise the hit rate by accepting stale dependency state.

## Bun test compatibility

Try `bun test` on the exact pin and real project only when a test-runner change
fits the measured bottleneck. Current docs describe `vitest` imports and
`--isolate=modules`; the 1.4.4-tagged test docs do not establish either. Treat
support, runtime behavior and coverage as unknown until the pinned executable and
target project prove them. Do not rewrite imports or remove Vitest to force adoption.

Compare project config, plugins, environments, global/setup hooks, declaration
types, fixture injection, mocks, assertions, test IDs and reports/coverage. In the
documented compatibility mode, `inject` cannot supply Vitest global setup values
and some assertions need `chai` at runtime. Keep those dependencies and any needed
Vitest lanes until parity. Where the pin supports `bun test --randomize --seed N`,
record each seed and prove per-file cleanup; keep isolation where required. Do not
widen timeouts or retry to pass the comparison.

## Vitest reuse and scheduling

Profile environment, import, transform, setup and test execution first. Benchmark
`isolate: false` with compatible pools; VM pools do not use this setting in the
same way. Use `vitest doctor` if the pinned version supports it to find candidates,
then validate on real runs: its best warm timings are not CI p50/p95 evidence.

Register executable cleanup in `setupFiles` and document the same contract in
`AGENTS.md`. Setup files rerun before every file even without isolation; imported
modules and worker globals remain shared. Reset state after each file and, where
needed, after each test: mocks, timers, environment/globals, DOM/storage, event and
request handlers, pending async work, DB data/transactions and application caches.
Await teardown and assert resource cleanup. Reinitializing the whole app or
clearing every module after every file defeats the intended reuse; implement
targeted resets. Keep isolation for demonstrated incompatible projects while
repairing leaks; never suppress their failing tests.

Run with `retry: 0`, forbid focused tests in CI, and keep unhandled failures fatal.
Record random seeds and use shuffled files/tests to detect ordering dependencies:

```sh
./node_modules/.bin/vitest run --sequence.shuffle --sequence.seed=12345
```

Vary and record seeds; reproduce a failing seed for diagnosis without erasing it.
Probe files alone and retain results for at least three recorded shuffled full-suite
runs with unchanged inventory and coverage; compare flakes over 20+ runs before
retiring isolation. Duration balance comes before within-shard shuffling, which
trades away longest-first order. Apply the
[worker and shard contract](14-two-minute-ci.md#parallel-work-and-test-reuse).

## Reviewed sources

See the dated [source index](06-official-sources.md), including the
[2026-11-22 Bun checks](06-official-sources.md#strict-profile-tool-checks-2026-11-22).

- Bun: [checker](https://bun.sh/docs/runtime/check), [install](https://bun.com/docs/pm/cli/install), [lifecycle](https://bun.com/docs/pm/lifecycle).
- TypeScript: [native-port migration](https://github.com/microsoft/TypeScript-go), [current compiler](https://github.com/microsoft/TypeScript).
- tsrs: [compiler and conformance](https://github.com/oxc-project/tsrs), [Oxlint integration, 2026-11-17](https://oxc.rs/blog/2026-11-17-faster-type-aware-linting-with-tsrs).
- Oxlint: [migration](https://oxc.rs/docs/guide/usage/linter/migrate-from-eslint.html), [CLI/rule categories](https://oxc.rs/docs/guide/usage/linter/cli), [type-aware scope](https://oxc.rs/docs/guide/usage/linter/type-aware.html).
- Oxfmt: [migration](https://oxc.rs/docs/guide/usage/formatter/migrate-from-prettier.html), [limitations](https://oxc.rs/docs/guide/usage/formatter/unsupported-features), [language/distribution coverage](https://oxc.rs/docs/guide/usage/formatter/language-support).
- Vitest: [performance](https://vitest.dev/guide/improving-performance), [doctor](https://vitest.dev/guide/cli), [setup](https://vitest.dev/config/setupfiles), [sequence](https://vitest.dev/config/sequence), [parallelism](https://vitest.dev/guide/parallelism).
