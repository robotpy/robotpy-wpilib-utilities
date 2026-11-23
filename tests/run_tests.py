#!/usr/bin/env python3

from pathlib import Path
import sys
import subprocess

if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    subprocess.check_call([sys.executable, "-m", "pytest"], cwd=root)

    for example in sorted((root.parent / "examples").iterdir()):
        if example.is_dir():
            print(f"Testing example: {example.name}", flush=True)
            subprocess.check_call(
                [sys.executable, "-m", "robotpy", "test", "--builtin"], cwd=example
            )
