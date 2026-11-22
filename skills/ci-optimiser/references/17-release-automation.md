# Release automation review

Use this for release questions or relevant release evidence, not as a mandatory
part of a speed audit. Read-only by default. Keep working automation unless the
target benefits from changing it. A workflow proposal is not permission to edit,
change live rules or credentials, approve CI, merge, tag, publish, or deploy.

## Decide what fits

1. Identify the active provider, release branches, latest published tags,
   version files, changelog, package boundaries, and artifact or registry
   destinations. Confirm which automation actually runs; a config file is
   not proof. Identify who owns CI approval, release review, and publication.
2. Recommend **Release Please** when a GitHub repository wants Conventional
   Commits to drive version and changelog PRs. Keep a working alternative
   if it fits; on another provider use its native release path or say
   `not applicable`. A private GitHub mirror does not make GitHub the release host.
3. Use the [live research procedure](16-live-research.md) and [dated release
   sources](06-official-sources.md#release-automation-2026-11-22). Verify the
   latest stable compatible action or CLI, runner runtime, platform, inputs,
   token behavior, required settings and any costs. Cite exact revisions and
   dates; if unavailable, mark current compatibility unverified.
4. Reconcile published tag, version, and changelog before bootstrapping.
   Preserve history and existing tag format. Use one version for one product;
   use independently versioned manifest packages only where they release
   independently. Verify package paths, tag collisions and dependencies.
   Add maintenance or prerelease branches only when needed.

## Design the workflow

| Boundary | Recommendation |
|---|---|
| Source admission | Keep the full suite, stable required checks and configured merge queue. On GitHub Actions verify that the checks also run on `merge_group`. A release PR gets the same protection. Report an unsupported or unverified gate; do not work around it. |
| Release input | Check the **actual merged commit subject** the bot will parse. For squash merges, inspect how GitHub derives it from the PR title or commit message. Prefer a lightweight title check and explicit conventional squash titles; verify that a title edit or override cannot silently evade the intended rule. Do not duplicate the full suite for a title-only check. |
| Proposal | Run the bot from trusted release-branch evidence. Use the repo's SemVer policy to propose version and changelog. Typically `feat:` drives a minor and `fix:` a patch; check pre-1.0 or package strategy exceptions. A maintainer reviews the proposed version and notes; intentional overrides need a reason. |
| Trigger trust | If chaining off `workflow_run`, check the upstream workflow identity, repo, event, release branch, success, and exact tested SHA before allowing writes. A green PR run is not trusted release evidence. Start read-only or with no permissions, scope writes to the jobs that need them, and pin actions to verified full SHAs. Never run untrusted PR code or consume unverified artifacts/cache under release credentials. |
| Publish | For a simple source release, prefer the smallest reviewed flow. If public exposure requires package or artifact checks, keep the release draft until the version, tag, tested SHA, and relevant artifact digests/provenance match. An attestation proves provenance, not test success. Make publishing authority explicit: if merging a named release PR authorizes later publication, document that consequence before merge. |
| Registry or deploy | Treat these as separate operations. Verify the downstream event and credential scopes; do not assume a tag or release made with `GITHUB_TOKEN` starts another workflow. For packages, prefer supported trusted publishing with narrowly scoped identity. Do not add deployment or registry access to a source-only release. |

In both a simple tag flow and a verified package flow, the order is:

```text
trusted CI → release PR → review + required merge queue → exact release source
→ publish (verify an unpublished candidate first when product policy calls for it)
```

Start with `GITHUB_TOKEN` if maintainers can approve bot-created PR runs. On
GitHub.com, eligible `opened`, `synchronize` and `reopened` bot PR events can
create approval-required runs. Verify on the actual provider/version rather than
copying blanket guidance that the built-in token never starts PR CI. Check
whether organization settings allow Actions to create PRs. Recommend a scoped
GitHub App installation token only when unattended CI is required and authorized;
do not recommend a personal token by default.

Serialize conflicting writes for the same release target. Bind a proposed or
draft release to its expected SHA, version, tag and identifier. If the intended
identity changes or a write is uncertain, stop and reread provider state. Do not
silently retarget an older job to the latest branch tip or create another tag to
make a failed release appear green.

## Diagnose the actual state

| Observation | What to check and recommend |
|---|---|
| Workflow succeeded, no release PR | Inspect the input range, configured releasable types, logs and existing release PR state. A malformed squash title that the parser skipped is different from a valid range with no releasable changes. For an already squash-merged eligible change, a reviewed `BEGIN_COMMIT_OVERRIDE` in the original PR body can correct its release input on a subsequent eligible run. It does not rewrite history or trigger an event by itself. Do not clear release state labels blindly or rerun failed acceptance to obtain a green. |
| Release PR awaits CI approval | Confirm first-party bot identity, exact PR head and the approval-required attempt. Call it a hold with no execution only when a complete attempt-scoped inventory proves zero jobs. A maintainer may approve that CI run; approval alone does not make CI pass or authorize publication. Do not reclassify an actual failed attempt. |
| Required checks red, missing, or pending | Say which boundary is blocked; fix a real failure and validate the new revision. Do not remove checks, use an earlier green or skip the queue. |
| Release PR merged, no published release | Check trusted source CI, draft and tag identity, artifact verification and publication result separately. A created tag, green proposal job or unpublished draft is not evidence of publication. A mismatch blocks publication; preserve the candidate and diagnose it. |
| Release published | Verify the live release state and tag/SHA; check registry or deployment separately if in scope. |

## Verify and report

Use fixtures or an authorized sandbox to check a valid `feat:` subject, a
malformed squash title, no eligible changes, bot approval holds, failed required
CI, and mismatched SHA/tag evidence. A fixture or workflow lint pass does not
prove hosted behavior. Link real runs or provider settings when available.

Return **KEEP / ADOPT / FIX / NOT APPLICABLE** with the observed state, workflow
shape, dated sources, required settings, approval points, open evidence, how to
verify, and how to stop or roll back safely without rewriting tags or history.
Separate human approval wait, merge-queue wait, CI, package verification, time to
publication and runner cost. Unknown intervals and costs are not zero. Close with
one actionable next step; do not make the change in an audit.

See [versioned behavior cases](../evals/README.md) for the recommendation scenarios.
