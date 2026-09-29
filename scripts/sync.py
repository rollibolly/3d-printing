#!/usr/bin/env python3
"""Sync the Voron's Klipper config between the printer and this repo via the Moonraker API.

Usage:
    python scripts/sync.py pull            # printer -> repo (config/)
    python scripts/sync.py status          # show files that differ between printer and repo
    python scripts/sync.py push [FILE...]  # repo -> printer (all changed files, or only the given ones)
    python scripts/sync.py restart         # FIRMWARE_RESTART-free Klipper config reload (RESTART)

Only files that Moonraker reports as writable are tracked; read-only entries are
symlinks into upstream repos (mainsail.cfg, KAMP/Configuration/...) and are
managed by Moonraker's update manager. Klipper's SAVE_CONFIG backups and other
dated backups are skipped as well, since git replaces them.
"""
import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

PRINTER = os.environ.get("VORON_HOST", "http://192.168.3.50")
REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_ROOT / "config"

IGNORE = [
    re.compile(r"(^|/)printer-\d{8}_\d{6}\.cfg$"),  # SAVE_CONFIG backups
    re.compile(r"\.\d{4}-\d{2}-\d{2}-\d{4}$"),       # e.g. crowsnest.conf.2026-07-01-1112
    re.compile(r"\.bkp$"),
]


def api(path, data=None, headers=None, method=None):
    req = urllib.request.Request(PRINTER + path, data=data, headers=headers or {}, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def remote_files():
    files = json.loads(api("/server/files/list?root=config"))["result"]
    return {
        f["path"]: f
        for f in files
        if "w" in f["permissions"] and not any(p.search(f["path"]) for p in IGNORE)
    }


def download(path):
    return api("/server/files/config/" + urllib.parse.quote(path))


def local_files():
    return {p.relative_to(CONFIG_DIR).as_posix(): p for p in CONFIG_DIR.rglob("*") if p.is_file()}


def norm(data):
    return data.replace(b"\r\n", b"\n")


def diff_state():
    remote = remote_files()
    local = local_files()
    changed, only_remote, only_local = [], [], []
    for path in sorted(remote.keys() | local.keys()):
        if path not in local:
            only_remote.append(path)
        elif path not in remote:
            only_local.append(path)
        elif norm(download(path)) != norm(local[path].read_bytes()):
            changed.append(path)
    return changed, only_remote, only_local


def cmd_pull(args):
    remote = remote_files()
    local = local_files()
    for path in sorted(remote):
        dest = CONFIG_DIR / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(norm(download(path)))
        print(f"pulled  {path}")
    for path in sorted(local.keys() - remote.keys()):
        if args.prune:
            local[path].unlink()
            print(f"removed {path} (no longer on printer)")
        else:
            print(f"warning {path} exists only locally (use --prune to delete)")


def cmd_status(args):
    changed, only_remote, only_local = diff_state()
    for p in changed:
        print(f"modified     {p}")
    for p in only_remote:
        print(f"printer-only {p}")
    for p in only_local:
        print(f"repo-only    {p}")
    if not (changed or only_remote or only_local):
        print("in sync")


def upload(path):
    boundary = uuid.uuid4().hex
    parent, name = path.rsplit("/", 1) if "/" in path else ("", path)
    content = norm((CONFIG_DIR / path).read_bytes())
    parts = [
        f'--{boundary}\r\nContent-Disposition: form-data; name="root"\r\n\r\nconfig\r\n',
        f'--{boundary}\r\nContent-Disposition: form-data; name="path"\r\n\r\n{parent}\r\n',
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\n'
        "Content-Type: application/octet-stream\r\n\r\n",
    ]
    body = "".join(parts).encode() + content + f"\r\n--{boundary}--\r\n".encode()
    api("/server/files/upload", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}, method="POST")


def cmd_push(args):
    if args.files:
        targets = [Path(f).resolve().relative_to(CONFIG_DIR).as_posix() if Path(f).exists()
                   else f for f in args.files]
    else:
        changed, _, only_local = diff_state()
        targets = changed + only_local
    if not targets:
        print("nothing to push")
        return
    for path in targets:
        upload(path)
        print(f"pushed  {path}")
    print("Run `python scripts/sync.py restart` (or RESTART in the console) to load the changes.")


def cmd_restart(args):
    api("/printer/gcode/script?script=RESTART", method="POST")
    print("RESTART sent")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pull")
    p.add_argument("--prune", action="store_true", help="delete repo files no longer on the printer")
    p.set_defaults(func=cmd_pull)
    sub.add_parser("status").set_defaults(func=cmd_status)
    p = sub.add_parser("push")
    p.add_argument("files", nargs="*")
    p.set_defaults(func=cmd_push)
    sub.add_parser("restart").set_defaults(func=cmd_restart)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
