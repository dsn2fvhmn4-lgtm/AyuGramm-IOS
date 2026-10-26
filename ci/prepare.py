#!/usr/bin/env python3
"""Apply the native port patch only to its pinned upstream source tree."""
import argparse
import json
from pathlib import Path
import subprocess
from port_sources import missing_port_sources

parser = argparse.ArgumentParser()
parser.add_argument("source", type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
source = args.source.resolve()
pin = json.loads((root / "upstream.json").read_text())
actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
if actual != pin["commit"]:
    raise SystemExit("Upstream commit differs from upstream.json; refusing to apply a mismatched patch")
patch = root / "patches" / "ayugram-ghost-mode.patch"
subprocess.run(["git", "apply", "--check", str(patch)], cwd=source, check=True)
subprocess.run(["git", "apply", str(patch)], cwd=source, check=True)
missing = missing_port_sources(source)
if missing:
    raise SystemExit("Port patch is missing required native source files:\n" + "\n".join(missing))
print("Applied native AyuGram changes to " + actual)
