#!/usr/bin/env python3
"""Scan documentation for outdated cloud references."""
from pathlib import Path
import sys

BANNED = ["DigitalOcean", "digitalocean", "GCP"]


def main() -> int:
    docs = Path("docs")
    bad = False
    for md in docs.rglob("*.md"):
        text = md.read_text(errors="ignore")
        for term in BANNED:
            if term in text:
                print(f"{md}: contains '{term}'")
                bad = True
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
