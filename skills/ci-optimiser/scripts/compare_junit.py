"""Compare bounded JUnit reports for one explicitly selected job/matrix leg."""
import argparse
from collections import Counter
import hashlib
from itertools import islice
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

MAX_FILES = 4096
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024
MAX_ENTRIES = 250_000


def inventory(directory):
    counts = Counter()
    problems = Counter()
    if directory.is_symlink():
        raise ValueError("expected a real report directory")
    files = sorted(islice(directory.rglob("*.xml"), MAX_FILES + 1))
    if not files or len(files) > MAX_FILES:
        raise ValueError(f"expected 1..{MAX_FILES} XML reports")

    def record(counter, key):
        counter[key] += 1
        if len(counts) + len(problems) > MAX_ENTRIES:
            raise ValueError("JUnit inventory exceeds the entry limit")

    def walk(node, suites, filename):
        tag = node.tag
        if tag == "testcase":
            name = node.get("name")
            if not name or not name.strip():
                raise ValueError("test identity is incomplete")
            identity = (*suites, filename, node.get("classname", ""), name)
            fields = {child.tag for child in node}
            status = {node.get(k, "").lower() for k in ("status", "result")}
            outcomes = set()
            words = {
                "error": {"error", "errored"},
                "skipped": {"skipped", "notrun", "disabled", "suppressed", "ignored", "pending"},
                "failure": {"failure", "failed"},
                "ran": {"passed", "pass", "success"},
            }
            for result, labels in words.items():
                if result in fields or status & labels:
                    outcomes.add(result)
            if len(outcomes) > 1 or status - {"", "run", "completed"} - set.union(*words.values()):
                raise ValueError("ambiguous test outcome")
            outcome = next(iter(outcomes), "ran")
            record(counts, (identity, outcome))
            for child in node:
                if child.tag in {"rerunError", "rerunFailure", "flakyError", "flakyFailure"}:
                    record(problems, (identity, "retry"))
            return Counter({outcome: 1})
        if tag not in {"testsuite", "testsuites"}:
            return Counter()
        if tag == "testsuite":
            suites = (*suites, node.get("name", ""))
        totals = Counter()
        for child in node:
            if child.tag in {"failure", "error"}:
                detail = (child.get("type", "").strip(), child.get("message", "").strip(),
                          (child.text or "").strip())
                fingerprint = hashlib.sha256(json.dumps(detail).encode("ascii")).hexdigest() if any(detail) else ""
                record(problems, (suites, child.tag, fingerprint))
            else:
                totals.update(walk(child, suites, child.get("file", filename)))
        if "tests" in node.attrib and int(node.attrib["tests"]) != sum(totals.values()):
            raise ValueError("declared test total differs from visible cases")
        for attr, outcome in (("errors", "error"), ("failures", "failure"), ("skipped", "skipped"), ("disabled", "skipped")):
            if attr in node.attrib and not 0 <= int(node.attrib[attr]) <= totals[outcome]:
                raise ValueError("unattributed suite outcome")
        return totals

    remaining = MAX_TOTAL_BYTES
    for path in files:
        if path.is_symlink() or path.resolve() != directory.resolve() / path.relative_to(directory):
            raise ValueError("report path crosses a symlink")
        if not path.is_file():
            raise ValueError("invalid report file")
        limit = min(MAX_FILE_BYTES, remaining)
        with path.open("rb") as report:
            raw = report.read(limit + 1)
        if len(raw) > limit:
            raise ValueError("JUnit report exceeds the per-file or aggregate byte limit")
        remaining -= len(raw)
        if b"<!DOCTYPE" in raw.upper().replace(b"\0", b""):
            raise ValueError("DTD in report")
        root = ET.fromstring(raw)
        for node in root.iter():
            node.tag = node.tag.rsplit("}", 1)[-1]
        if not walk(root, (), root.get("file", "")):
            raise ValueError("empty or unsupported report")
    return counts, problems


def compare(before, after):
    old, old_problems = inventory(before)
    new, new_problems = inventory(after)
    if not any(result in {"ran", "failure"} for _, result in old):
        raise ValueError("baseline contains no executed tests")
    old_suites = {key[:2] for key in old_problems if len(key) == 3}
    new_suites = {key[:2] for key in new_problems if len(key) == 3}
    for scope, tag in old_suites & new_suites:
        if (scope, tag, "") in old_problems or (scope, tag, "") in new_problems:
            raise ValueError("matching suite errors lack identifying detail")
    issues = []
    collisions = []
    for key in sorted({identity for identity, _ in old | new}):
        a, b = ([arm[key, o] for o in ("ran", "failure", "error", "skipped")] for arm in (old, new))
        if max(sum(a), sum(b)) > 1:
            collisions.append(key)
        if sum(b) < sum(a) or sum(b[:2]) < sum(a[:2]) or any(y > x for x, y in zip(a[1:], b[1:])):
            issues.append(key)
    return {"changed_outcomes": issues, "new_suite_or_retry_errors": sorted((new_problems - old_problems).keys()),
            "duplicate_identities": collisions}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", required=True, type=Path)
    parser.add_argument("--after", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = compare(args.before, args.after)
    except (OSError, ValueError, ET.ParseError, RecursionError):
        print("incomplete or invalid JUnit evidence", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True))
    if result["changed_outcomes"] or result["new_suite_or_retry_errors"]:
        return 1
    return 2 if result["duplicate_identities"] else 0


if __name__ == "__main__":
    sys.exit(main())
