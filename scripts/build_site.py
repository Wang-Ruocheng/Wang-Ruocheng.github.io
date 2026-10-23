#!/usr/bin/env python3
"""Rebuild site pages/search/metadata from the shared records in data/.

Usage: python3 scripts/build_site.py [--with-cv]
The optional CV step needs reportlab; the website steps use only Python's
standard library. All generated files remain ready for static GitHub Pages.
"""

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--with-cv", action="store_true", help="also rebuild both CV PDF copies")
    args = parser.parse_args()
    scripts = ["build_publications.py", "build_homepage.py", "clean_legacy_site.py"]
    if args.with_cv:
        scripts.append("build_cv.py")
    for script in scripts:
        subprocess.run([sys.executable, str(ROOT / "scripts" / script)], cwd=ROOT, check=True)
