"""Keep private identifiers out of shipped text without printing matching contents."""
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch


PATTERNS = {
    "token": re.compile(r"\b(?:gh[pousr]_[a-zA-Z0-9]{36,}|github_pat_[a-zA-Z0-9_]{40,}|AKIA[A-Z0-9]{16})\b"),
    "private key": re.compile(r"-----BEGIN (?:OPENSSH |RSA |EC )?PRIVATE KEY-----"),
    "home directory": re.compile(r"/(?:Users|home)/[a-zA-Z][\w.-]+/"),
    "private hostname": re.compile(r"\b[\w-]+\.(?:internal|corp|tail[0-9a-f]+\.ts\.net)\b"),
}


def findings(path, text):
    return [(str(path), line_no, category) for line_no, line in enumerate(text.splitlines(), 1)
            for category, pattern in PATTERNS.items() if pattern.search(line)]


class PublicMaterialTest(unittest.TestCase):
    def test_detector_reports_location_only(self):
        self.assertEqual(findings("example", "ghp_" + "A" * 36), [("example", 1, "token")])

    def test_public_scan_checks_extensionless_text(self):
        token = "ghp_" + "A" * 36
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            hook = root / "skills/ci-optimiser/scripts/pre-push"
            hook.parent.mkdir(parents=True)
            hook.write_text(token, encoding="utf-8")
            with patch(__name__ + ".__file__", str(root / ".github/tests/test_public_material.py")):
                with self.assertRaisesRegex(AssertionError, "pre-push.*1.*token") as caught:
                    self.test_public_files()
        self.assertNotIn(token, str(caught.exception))

    def test_public_files(self):
        root = Path(__file__).resolve().parents[2]
        paths = [*root.glob("*.md"), root / "LICENSE"]
        for directory in ("skills/ci-optimiser", "docs", "assets"):
            paths.extend((root / directory).rglob("*"))
        hits = []
        for path in paths:
            if path.is_file() and path.suffix not in {".png", ".pyc"}:
                hits.extend(findings(path.relative_to(root), path.read_text(encoding="utf-8")))
        self.assertEqual(hits, [])
