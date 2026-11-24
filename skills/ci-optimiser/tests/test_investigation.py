from contextlib import redirect_stderr, redirect_stdout
import io
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from scripts import cache_log_labels, compare_junit


class InvestigationTest(unittest.TestCase):
    def cli(self, before, after):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for arm, reports in (("before", before), ("after", after)):
                (root / arm).mkdir()
                for index, report in enumerate(reports):
                    (root / arm / f"{index}.xml").write_text(report, encoding="utf-8")
            args = ["compare_junit", "--before", str(root / "before"), "--after", str(root / "after")]
            with patch("sys.argv", args), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                return compare_junit.main()

    def test_replaced_suite_error_is_a_regression(self):
        setup = '<testsuite name="suite"><testcase name="one"/><error type="SetupError"/></testsuite>'
        teardown = setup.replace("SetupError", "TeardownError")
        self.assertEqual(self.cli([setup], [teardown]), 1)
        self.assertEqual(self.cli([setup], [setup]), 0)

    def test_matching_unidentified_suite_errors_are_inconclusive(self):
        report = '<testsuite name="suite"><testcase name="one"/><error/></testsuite>'
        self.assertEqual(self.cli([report], [report]), 2)

    def test_aggregate_report_byte_limit(self):
        reports = [f'<testsuite><testcase name="{name}"/></testsuite>' for name in ("one", "two")]
        size = sum(len(report.encode("utf-8")) for report in reports)
        with patch.object(compare_junit, "MAX_TOTAL_BYTES", size - 1, create=True):
            self.assertEqual(self.cli(reports, reports), 2)
        with patch.object(compare_junit, "MAX_TOTAL_BYTES", size, create=True):
            self.assertEqual(self.cli(reports, reports), 0)

    def test_retained_report_entry_limit(self):
        reports = ['<testsuite><testcase name="one"/><error type="SetupError"/></testsuite>']
        with patch.object(compare_junit, "MAX_ENTRIES", 1, create=True):
            self.assertEqual(self.cli(reports, reports), 2)
        with patch.object(compare_junit, "MAX_ENTRIES", 2, create=True):
            self.assertEqual(self.cli(reports, reports), 0)

    def compare(self, before, after):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for arm, body in (("old", before), ("new", after)):
                (root / arm).mkdir()
                (root / arm / ("shard-" + arm + ".xml")).write_text("<testsuite>" + body + "</testsuite>")
            return compare_junit.compare(root / "old", root / "new")

    def test_report_parity(self):
        case = '<testcase name="one"/>'
        self.assertFalse(any(self.compare(case, case).values()))
        for changed in ('<testcase name="two"/>', '<testcase name="one"><error/></testcase>',
                        '<testcase name="one"><skipped/></testcase>', '<testcase name="one"><flakyFailure/></testcase>',
                        case + '<error/>', '<testcase name="one"><failure/></testcase>'):
            with self.subTest(changed=changed):
                self.assertTrue(any(self.compare(case, changed).values()))
        self.assertTrue(self.compare(case * 2, case)["changed_outcomes"])
        self.assertTrue(self.compare(case * 2, case * 2)["duplicate_identities"])
        for invalid in ("", '<testcase name="one" status="skipped"><failure/></testcase>',
                        '<testsuite failures="-1">' + case + '</testsuite>'):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                self.compare(case, invalid)

    def test_cache_redaction(self):
        key = "private-key-value"
        for text, label in (("Cache restored from key: ", "restored_match_unknown"),
                            ("Cache not found for input keys: ", "miss"),
                            ("Cache saved with key: ", "saved")):
            obs = cache_log_labels.observation(text + key)
            self.assertEqual(obs["observation"], label)
            self.assertNotIn(key, str(obs))
        self.assertIsNone(cache_log_labels.observation(key))

    def test_offline_grader_controls(self):
        from evals.grade_folded import grade
        fixture = Path(__file__).resolve().parents[1] / "evals/fixtures/folded/verify.sh"
        self.assertFalse(grade(fixture))
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "verify.sh"
            for content in ('exit 0', 'sh "$2"', 'sh "$1" || sh "$1"\nsh "$2"',
                            'set -e\nsh "$1"\nsh "$2"'):
                script.write_text(content)
                self.assertFalse(grade(script))
            script.write_text('status=0\nsh "$1" || status=1\nsh "$2" || status=1\nexit "$status"')
            self.assertTrue(grade(script))

    def test_quota_reserve_stops_before_the_next_page(self):
        from unittest.mock import Mock
        from scripts.collect_gh import GhClient, GhError
        response = Mock(returncode=0, stdout="HTTP/2 200 OK\nx-ratelimit-remaining: 10\nx-ratelimit-reset: 42\n\n{}")
        runner = Mock(return_value=response)
        client = GhClient(runner=runner, reserve_requests=10, clock=lambda: 30)
        self.assertEqual(client("repos/a/b"), {})
        with self.assertRaises(GhError) as caught:
            client("repos/a/b/actions/runs")
        self.assertEqual(caught.exception.retry_after, 12)
        self.assertEqual(runner.call_count, 1)

    def test_faster_candidate_loses_test(self):
        fixture = Path(__file__).resolve().parents[1] / "evals/fixtures/report-loss"
        result = compare_junit.compare(fixture / "before", fixture / "after")
        self.assertEqual([item[-1] for item in result["changed_outcomes"]], ["reject_empty"])
        self.assertFalse(any(compare_junit.compare(fixture / "before", fixture / "before").values()))

    def test_tracked_scratch(self):
        import subprocess
        from scripts.collect_gh import check_scratch
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp).resolve()
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            out = repo / "audit"
            out.mkdir()
            check_scratch(out)
            (out / "saved").touch()
            subprocess.run(["git", "-C", str(repo), "add", "audit/saved"], check=True)
            with self.assertRaises(ValueError):
                check_scratch(out)
            with tempfile.TemporaryDirectory() as outside:
                alias = Path(outside) / "alias"
                alias.symlink_to(repo, target_is_directory=True)
                with self.assertRaises(ValueError):
                    check_scratch(alias / "audit")
