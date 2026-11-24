"""Read a single cache step on stdin and emit redacted diagnostic observations."""
import hashlib
import json
import re
import sys


def observation(line):
    text = re.sub(r"^\d{4}-\d\d-\d\dT[\d:.]+Z\s+", "", line.strip())
    for pattern, outcome in (
        (r"Cache restored from key: (.+)", "restored_match_unknown"),
        (r"Cache not found for input keys: (.+)", "miss"),
        (r"Cache hit occurred on the primary key (.+), not saving cache\.", "exact_hit"),
        (r"Cache saved with key: (.+)", "saved"),
    ):
        match = re.fullmatch(pattern, text)
        if match:
            key = match[1].split(",", 1)[0].strip()
            return {"observation": outcome, "key_sha256": hashlib.sha256(key.encode()).hexdigest()}
    return None


if __name__ == "__main__":
    found = False
    for line in sys.stdin:
        item = observation(line)
        if item:
            print(json.dumps(item))
            found = True
    if not found:
        print(json.dumps({"observation": "unknown"}))
