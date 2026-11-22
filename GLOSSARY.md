# CI optimisation

`ci-optimiser` evaluates how a repository verifies changes and releases tested
source or artifacts.

## Release language

**Release PR**:
A proposal for the next version and its changelog. Merging it is distinct from
making the release visible to users.

**Draft release**:
An unpublished release record. Its presence is not evidence that users can
obtain the release.

**Published release**:
A release made available to its intended audience. It does not imply a separate
registry publication or deployment.

**CI approval hold**:
A workflow attempt waiting for a maintainer to authorize execution. An
approval-only attempt has a verified record of zero jobs executed.
