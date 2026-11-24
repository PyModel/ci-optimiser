"""Grade a candidate shell entrypoint inside an already isolated evaluation environment."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def grade(candidate):
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for codes in ((0, 0), (7, 0), (0, 7), (7, 7)):
            args = []
            for i, code in enumerate(codes):
                task = root / f"task-{i}"
                task.write_text(f'echo {i} >> "$TRACE"\nexit {code}\n')
                args.append(str(task))
            trace = root / "trace"
            trace.write_text("")
            run = subprocess.run(["sh", str(candidate.resolve()), *args], cwd=root,
                                 env={"PATH": os.defpath, "TRACE": str(trace)}, timeout=5,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if sorted(trace.read_text().splitlines()) != ["0", "1"] or bool(run.returncode) != any(codes):
                return False
    return True


if __name__ == "__main__":
    sys.exit(0 if grade(Path(sys.argv[1])) else 1)
