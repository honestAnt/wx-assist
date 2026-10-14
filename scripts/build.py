#!/usr/bin/env python3
"""Build a native wx-assist artifact for the current operating system.

Examples:
    python scripts/build.py              # no-RAG binary
    python scripts/build.py --rag        # full binary
    python scripts/build.py --both
"""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _artifact(exe_name: str) -> str:
    system = platform.system()
    if system == "Windows":
        return f"dist/{exe_name}.exe"
    if system == "Darwin":
        return f"dist/{exe_name}.app"
    return f"dist/{exe_name}"


def _build(spec: str) -> None:
    if shutil.which("pyinstaller") is None:
        print("pyinstaller is not on PATH. Install it with: pip install pyinstaller", file=sys.stderr)
        raise SystemExit(1)
    cmd = [sys.executable, "-m", "PyInstaller", spec, "--noconfirm"]
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build wx-assist for this OS")
    parser.add_argument("--rag", action="store_true", help="build the full RAG variant")
    parser.add_argument("--both", action="store_true", help="build both variants")
    args = parser.parse_args()

    ui_dist = ROOT / "ui" / "dist"
    if not ui_dist.exists():
        print("ui/dist is missing. Run: cd ui && npm install && npm run build", file=sys.stderr)
        raise SystemExit(1)

    if args.both:
        jobs = [("build.spec", "wx-assist_no_rag"), ("build_rag.spec", "wx-assist")]
    elif args.rag:
        jobs = [("build_rag.spec", "wx-assist")]
    else:
        jobs = [("build.spec", "wx-assist_no_rag")]

    for spec, name in jobs:
        _build(spec)
        print(f"artifact: {_artifact(name)}")


if __name__ == "__main__":
    main()
