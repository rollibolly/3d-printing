#!/usr/bin/env python3
"""Copy OrcaSlicer user profiles (machine/filament/process) for the Voron into slicer/orca/.

Usage: python scripts/export_orca.py [--prune]

Profiles belonging to other printers (Creality/Ender) are skipped. Run after
changing profiles in Orca, then review `git diff` and commit.
"""
import argparse
import json
import os
import re
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEST = REPO_ROOT / "slicer" / "orca"
ORCA_USER = Path(os.environ["APPDATA"]) / "OrcaSlicer" / "user"
SKIP = re.compile(r"creality|ender", re.IGNORECASE)
SECRET_KEYS = ("printhost_apikey", "printhost_password", "printhost_user")


def profile_dir():
    dirs = [d for d in ORCA_USER.iterdir() if d.is_dir() and d.name != "default"]
    if len(dirs) != 1:
        raise SystemExit(f"expected one Orca user dir in {ORCA_USER}, found {[d.name for d in dirs]}")
    return dirs[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prune", action="store_true", help="delete exported profiles no longer in Orca")
    args = parser.parse_args()

    src_root = profile_dir()
    exported = set()
    for src in src_root.rglob("*.json"):
        rel = src.relative_to(src_root)
        data = json.loads(src.read_text(encoding="utf-8"))
        if SKIP.search(src.stem) or SKIP.search(data.get("inherits", "")):
            continue
        if any(data.get(k) for k in SECRET_KEYS):
            raise SystemExit(f"{rel} contains print host credentials; refusing to export")
        dest = DEST / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        exported.add(dest)
        print(f"exported {rel.as_posix()}")
    if args.prune:
        for stale in set(DEST.rglob("*.json")) - exported:
            stale.unlink()
            print(f"removed  {stale.relative_to(DEST).as_posix()}")


if __name__ == "__main__":
    main()
