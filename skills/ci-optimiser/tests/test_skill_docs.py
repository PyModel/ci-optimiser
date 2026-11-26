"""Packaging and installed report contract checks."""
from __future__ import annotations

import re
import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r"\]\(([^)\s]+)\)")
FENCE = re.compile(r"^```.*?^```", re.S | re.M)


def slug(heading: str) -> str:
    s = heading.strip().lower()
    s = re.sub(r"[^\w\- ]", "", s)
    return s.replace(" ", "-")


def anchors(path: Path) -> set[str]:
    text = FENCE.sub("", path.read_text())
    return {slug(m.group(1)) for m in re.finditer(r"^#{1,6} (.+)$", text, re.M)}


def source_root() -> Path | None:
    """Installed bundles do not depend on checkout-only README/CI/hook files."""
    candidate = ROOT.parent.parent
    if ROOT.name == "ci-optimiser" and ROOT.parent.name == "skills" and (candidate / ".git").exists():
        return candidate
    return None


def broken_links(root: Path, *, boundary: Path | None = None) -> list[str]:
    problems = []
    for md in sorted(root.rglob("*.md")):
        if ".git" in md.parts or ".ci-audit" in md.parts or ".claude" in md.parts:
            continue
        for target in LINK.findall(FENCE.sub("", md.read_text())):
            if re.match(r"^[a-z]+:", target) or target.startswith("<"):
                continue
            file_part, _, anchor = target.partition("#")
            dest = (md.parent / file_part).resolve() if file_part else md
            rel = md.relative_to(root)
            if boundary is not None and not dest.is_relative_to(boundary.resolve()):
                problems.append(f"{rel}: link leaves installed bundle: {target}")
                continue
            if not dest.exists():
                problems.append(f"{rel}: missing {target}")
            elif anchor and dest.suffix == ".md" and anchor not in anchors(dest):
                problems.append(f"{rel}: missing anchor {target}")
    return problems


class SkillDocsTest(unittest.TestCase):
    def test_frontmatter(self):
        text = (ROOT / "SKILL.md").read_text()
        self.assertTrue(text.startswith("---\n"))
        front = text.split("---", 2)[1]
        self.assertRegex(front, r"(?m)^name: ci-optimiser$")
        self.assertRegex(front, r"(?m)^description: >-\n  Use when ")
        desc = " ".join(l.strip() for l in front.split("description: >-", 1)[1].splitlines())
        self.assertLessEqual(len(desc), 1024)

    def test_skill_md_size(self):
        core = ROOT / "SKILL.md"
        self.assertLessEqual(len(core.read_text().splitlines()), 200)
        self.assertLessEqual(len(core.read_bytes()), 13 * 1024)

    def test_links_resolve(self):
        self.assertEqual(broken_links(ROOT, boundary=ROOT), [])
        repository = source_root()
        if repository is not None:
            self.assertEqual(broken_links(repository), [])

    def test_audit_report_distinguishes_admission_execution_and_release(self):
        report = (ROOT / "templates/audit-report.md").read_text()
        sections = dict(
            re.findall(r"^## ([^\n]+)\n(.*?)(?=^## |\Z)", report, re.M | re.S)
        )
        self.assertIn("Merge admission and evidence", sections)
        admission = sections["Merge admission and evidence"]
        rows = dict(re.findall(r"^\| ([^|]+?) \| ([^|]+?) \|$", admission, re.M))
        for field, markers in {
            "Enforcing SCM / rule": ("target branch", "required queue/train", "policy source"),
            "Executor / workflow / event": ("executor", "workflow", "event"),
            "Expected producer / check": ("trusted publisher", "check context"),
            "Actual producer / check": ("observed publisher", "check context", "reported SHA"),
            "Combined candidate / base / attempt": ("candidate SHA", "base SHA", "run ID", "attempt"),
            "Full-suite inventory / result": ("expected", "observed", "tests", "shards", "reports"),
            "Strict admission / bypass decision": ("eligible", "blocked", "unverified", "bypass"),
        }.items():
            with self.subTest(field=field):
                self.assertIn(field, rows)
                for marker in markers:
                    self.assertIn(marker, rows[field])
        proof = " ".join(admission.split())
        self.assertIn(
            "reported SHA and the actual SHA executed by every required job "
            "must both match the combined candidate SHA", proof,
        )
        for rejected in ("stale", "wrong producer", "skipped", "neutral", "pr-head", "missing proof"):
            self.assertIn(rejected, proof.casefold())
        guidance = (ROOT / "references/01-discovery-matrix.md").read_text()
        self.assertIn("06-official-sources.md#merge-admission-sources-2026-11-22", guidance)
        sources = (ROOT / "references/06-official-sources.md").read_text()
        dated_sources = sources.split("## Merge admission sources (2026-11-22)\n", 1)[1].split("\n## ", 1)[0]
        for url in (
            "configuring-pull-request-merges/managing-a-merge-queue",
            "troubleshooting-required-status-checks",
            "buildkite.com/docs/pipelines/source-control/github#running-builds-on-merge-queues",
            "docs.gitlab.com/ci/pipelines/merge_trains#enforce-merge-trains",
            "learn.microsoft.com/en-us/azure/devops/repos/git/branch-policies",
        ):
            with self.subTest(source=url):
                self.assertIn(url, dated_sources)
        release = sections["Evidence identity and release eligibility"]
        self.assertIn("actual release host", release)
        self.assertIn("../references/17-release-automation.md", release)
        self.assertIn("KEEP / ADOPT / FIX / NOT APPLICABLE", release)

    def test_audit_report_screens_options_and_separates_feedback_outcomes(self):
        report = (ROOT / "templates/audit-report.md").read_text()
        sections = dict(re.findall(r"^## ([^\n]+)\n(.*?)(?=^## |\Z)", report, re.M | re.S))
        screen = sections.get("Option screen", "")
        families = re.findall(r"^\| ([^|]+?) \|.*$", screen, re.M)
        self.assertCountEqual(families, [
            "Family", "Faster runner", "Lint/typecheck", "Workers/shards",
            "Cache/checkout", "Parallel jobs/steps", "Affected tasks", "Hooks",
        ])
        for field in ("Disposition", "Reason / next proof", "keep", "not applicable"):
            self.assertIn(field, screen)
        self.assertIn("Ranked recommendations", sections)
        self.assertIn("Next reversible action", sections)

        feedback = sections["PR feedback objective"]
        for metric, markers in {
            "Latest-revision PR feedback": ("exact push receipt", "trustworthy success or failure", "first execution"),
            "First-push PR journey": ("first push", "green"),
            "Pre-main queue validation": ("exact combined candidate", "full suite"),
            "Post-push observations": ("exact main SHA", "supplemental"),
        }.items():
            with self.subTest(metric=metric):
                row = re.search(rf"(?m)^\| {metric} \|(.+)$", feedback)
                self.assertIsNotNone(row)
                for marker in markers:
                    self.assertIn(marker, row[1])
        for marker in ("approval wait", "dependency wait", "runner wait", "diagnostic", "censored"):
            self.assertIn(marker, feedback.casefold())
        self.assertIn("../references/16-live-research.md", sections["Live research"])
        self.assertIn("native billable units", sections["Live research"])

        sources = (ROOT / "references/06-official-sources.md").read_text()
        holds = sources.split("## PR approval-only attempt evidence (2026-11-20)\n", 1)[1].split("\n## ", 1)[0]
        for endpoint in (
            "workflow-runs#get-a-workflow-run-attempt",
            "workflow-jobs#list-jobs-for-a-workflow-run-attempt",
        ):
            self.assertIn(endpoint, holds)

    def test_bundle_entrypoint_license_and_source_scaffolding(self):
        self.assertEqual(list(ROOT.rglob("SKILL.md")), [ROOT / "SKILL.md"])
        self.assertTrue((ROOT / "LICENSE").is_file())
        repository = source_root()
        if repository is not None:
            self.assertFalse((repository / "SKILL.md").exists())
            for path in ("README.md", "AGENTS.md", "LICENSE", ".githooks/pre-push",
                         ".github/workflows/ci.yml", ".github/dependabot.yml"):
                self.assertTrue((repository / path).is_file(), path)
            self.assertTrue(os.access(repository / ".githooks/pre-push", os.X_OK))
            self.assertEqual((ROOT / "LICENSE").read_bytes(), (repository / "LICENSE").read_bytes())

    def test_bun_checker_guidance_verifies_exact_pin(self):
        sources = (ROOT / "references/06-official-sources.md").read_text()
        row = next(line for line in sources.splitlines() if line.startswith("| Bun type checker |"))
        self.assertNotRegex(row, r"follows TS .* since|needs `@types/bun`")
        self.assertIn("compiler embedded in the exact Bun pin", row)

    def test_github_queue_guidance_distinguishes_actions_from_external_ci(self):
        for path in (
            "SKILL.md", "templates/agent-prompt.md", "references/08-validation-architecture.md",
            "references/14-two-minute-ci.md",
        ):
            with self.subTest(path=path):
                text = " ".join((ROOT / path).read_text().split())
                self.assertIsNotNone(
                    re.search(r"GitHub Actions[^.]*\bmerge_group\b", text),
                    "Scope the merge_group workflow prescription to GitHub Actions",
                )
                self.assertIsNotNone(
                    re.search(r"external CI[^.]*queue event[^.]*candidate[^.]*publisher", text),
                    "Require native event, candidate, and publisher proof from external CI",
                )
                self.assertIn("01-discovery-matrix.md#merge-admission-evidence", text)

    def test_agent_prompt_binds_github_checks_and_each_job_to_queue_candidate(self):
        text = " ".join((ROOT / "templates/agent-prompt.md").read_text().split())
        queue_step = text.split("3. Classify", 1)[1].split("4. Fill", 1)[0]
        self.assertRegex(
            queue_step,
            r"GitHub Actions[^.]*`merge_group`[^.]*reported check SHA and each job's "
            r"checkout and build SHA to match the exact queue candidate SHA",
        )

    def test_parallel_artifact_gate_requires_exact_provenance_and_negative_controls(self):
        for path, heading in (
            ("02-optimization-playbook.md", "5. Parallel jobs"),
            ("10-stack-adapters.md", "Artifact transport"),
        ):
            with self.subTest(path=path):
                text = (ROOT / "references" / path).read_text()
                section = text.split(f"## {heading}\n", 1)[1].split("\n## ", 1)[0]
                gate = " ".join(section.split("**Gate", 1)[1].split())
                for marker in (
                    "producer", "consumer", "SHA", "run ID", "attempt", "immutable artifact ID",
                    "digest", "Reject latest-success", "stale", "mismatched", "missing",
                    "must fail the consumer and required aggregate",
                ):
                    self.assertTrue(marker in gate, f"Missing {marker!r} from the artifact gate")

    def test_installed_strict_profile_sets_exclusive_targets(self):
        guide = "14-two-minute-ci.md"
        profile = (ROOT / "references" / guide).read_text()
        acceptance = profile.split("## Acceptance and audit\n", 1)[1].split("\n## ", 1)[0]
        targets = dict(re.findall(r"^\| ([^|]+?) \| `([^`]+)` \|$", acceptance, re.M))
        self.assertEqual(targets, {
            "First-execution PR feedback": "p50 <60 s / p95 <120 s",
            "Per-job runner wait": "<5 s",
            "Per-job setup": "<15 s",
            "Slowest required job, elapsed on runner": "<35 s",
            "Lint work": "<1 s",
            "Format work": "<1 s",
            "Typecheck work": "<5 s",
            "Test work per shard": "<30 s",
            "Exact eligible PR dependency-cache hits": ">95%",
            "Local pre-push wall time": "<9 s",
        })
        self.assertIn("fail at equality", acceptance)
        self.assertIn(targets["First-execution PR feedback"], (ROOT / "SKILL.md").read_text())
        pruning = profile.split("## Two-week pruning review\n", 1)[1].split("\n## ", 1)[0]
        self.assertRegex(" ".join(pruning.split()), r"Do not prune [^.]*\bauthorization\b[^.]* tests\b")
        for path, prefix in (
            ("SKILL.md", "references/"),
            ("templates/agent-prompt.md", "../references/"),
            ("templates/audit-report.md", "../references/"),
            ("templates/optimization-pr.md", "../references/"),
        ):
            with self.subTest(path=path):
                text = (ROOT / path).read_text()
                self.assertIn(f"]({prefix}{guide}#acceptance-and-audit)", text)
                self.assertNotRegex(text, r"<180 (?:s|seconds)\b")

    def test_self_hosted_fleet_stays_behind_the_existing_contracts(self):
        skill = (ROOT / "SKILL.md").read_text()
        self.assertIn("references/19-self-hosted-fleet.md", skill)
        self.assertIn("untrusted jobs cannot write shared caches", skill)
        fleet = (ROOT / "references/19-self-hosted-fleet.md").read_text()
        for target in (
            "03-security-correctness.md#required-checks-and-skips",
            "02-optimization-playbook.md#4-caching-and-blobless-clone",
            "06-official-sources.md#self-hosted-fleet-sources-2026-11-26",
            "06-official-sources.md#not-confirmed-for-self-hosted-fleets-2026-11-26",
        ):
            self.assertIn(target, fleet)
        self.assertNotIn("2027.1", fleet)
        sources = (ROOT / "references/06-official-sources.md").read_text()
        section = sources.split("## Self-hosted fleet sources (2026-11-26)\n", 1)[1].split("\n## ", 1)[0]
        for url in (
            "https://docs.github.com/en/actions/reference/runners/self-hosted-runners",
            "https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/run-scripts",
            "https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching",
            "https://pnpm.io/continuous-integration",
            "https://playwright.dev/docs/ci",
            "https://docs.gradle.org/current/userguide/gradle_daemon.html",
            "https://developer.android.com/build/optimize-your-build",
            "https://docs.docker.com/docker-hub/image-library/mirror/",
        ):
            self.assertIn(url, section)

    def test_checker_can_fail(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            (p / "a.md").write_text("# Top\n[x](b.md) [y](a.md#nope) [z](a.md#top) [w](https://e.x)\n")
            self.assertEqual(broken_links(p), ["a.md: missing b.md", "a.md: missing anchor a.md#nope"])


if __name__ == "__main__":
    unittest.main()
