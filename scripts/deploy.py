#!/usr/bin/env python3
"""Deploy config/ from this repo to the printer, restart what's affected, and roll back if Klipper fails.

Usage:
    python scripts/deploy.py               # deploy committed HEAD (asks for confirmation)
    python scripts/deploy.py --dry-run     # only show what would change
    python scripts/deploy.py --yes         # no confirmation prompt
    python scripts/deploy.py --allow-dirty # deploy the working tree incl. uncommitted edits
    python scripts/deploy.py --delete      # also delete printer files that were removed from the repo
    python scripts/deploy.py --force       # overwrite printer-side edits that were never pulled
    python scripts/deploy.py --no-restart  # upload only
    python scripts/deploy.py --status      # show what was last deployed

Safety checks, in order:
  1. Refuses while a print is running or paused (a RESTART would kill it).
  2. Refuses if config/ has uncommitted changes (unless --allow-dirty), so every deploy is a commit.
  3. Refuses if a file on the printer was edited since it was last pulled (its content isn't anywhere
     in git history), so changes made in Mainsail or by SAVE_CONFIG aren't silently overwritten.
     Fix by running `python scripts/sync.py pull` and committing, then deploy again.
After uploading it restarts only what the changed files need (Klipper, Moonraker, crowsnest,
KlipperScreen, sonar), waits for Klipper to come back, and if Klipper reports an error it restores
the previous files and restarts again. The deployed commit is recorded in Moonraker's database.
"""
import argparse
import json
import subprocess
import sys
import time
import urllib.error
from datetime import datetime, timezone

import sync

DB_NAMESPACE = "voron_repo"

# Files whose changes need a service restart instead of (or besides) a Klipper RESTART.
SERVICE_FILES = {
    "moonraker.conf": "moonraker",
    "crowsnest.conf": "crowsnest",
    "KlipperScreen.conf": "KlipperScreen",
    "sonar.conf": "sonar",
}


def git(*args, input=None):
    return subprocess.run(["git", "-C", str(sync.REPO_ROOT), *args], input=input,
                          capture_output=True, check=True).stdout


def head_commit(dirty):
    sha = git("rev-parse", "--short", "HEAD").decode().strip()
    return sha + ("-dirty" if dirty else "")


def config_dirty():
    return bool(git("status", "--porcelain", "--", "config").strip())


def source_files(use_worktree):
    """Files to deploy: {printer path: content}."""
    if use_worktree:
        return {path: sync.norm(p.read_bytes()) for path, p in sync.local_files().items()}
    names = git("ls-tree", "-r", "--name-only", "HEAD", "--", "config").decode().splitlines()
    return {n[len("config/"):]: sync.norm(git("show", f"HEAD:{n}")) for n in names}


def known_blobs(path):
    """Every blob hash config/<path> has had in git history."""
    out = git("log", "--all", "--format=", "--raw", "--no-abbrev", "--", f"config/{path}").decode()
    blobs = set()
    for line in out.splitlines():
        fields = line.split()
        if len(fields) >= 4:
            blobs.update(fields[2:4])
    return blobs


def blob_hash(content):
    return git("hash-object", "--stdin", input=content).decode().strip()


def print_state():
    res = json.loads(sync.api("/printer/objects/query?print_stats=state"))
    return res["result"]["status"]["print_stats"]["state"]


def klippy_state():
    try:
        info = json.loads(sync.api("/printer/info"))["result"]
        return info["state"], info.get("state_message", "")
    except (urllib.error.URLError, ConnectionError, TimeoutError):
        return "unreachable", ""


def wait_for_klipper(timeout=120):
    time.sleep(3)
    deadline = time.time() + timeout
    state, msg = klippy_state()
    while time.time() < deadline:
        state, msg = klippy_state()
        if state in ("ready", "error", "shutdown"):
            return state, msg
        time.sleep(2)
    return state, msg or "timed out waiting for Klipper"


def wait_for_moonraker(timeout=60):
    time.sleep(3)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            sync.api("/server/info")
            return True
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            time.sleep(2)
    return False


def restart_klipper():
    try:
        sync.api("/printer/restart", method="POST")
    except urllib.error.HTTPError:
        # Klipper in error state can reject RESTART; fall back to restarting the service
        sync.api("/machine/services/restart?service=klipper", method="POST")


def record_deploy(commit, files):
    value = {"commit": commit, "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "files": files}
    body = json.dumps({"namespace": DB_NAMESPACE, "key": "last_deploy", "value": value}).encode()
    sync.api("/server/database/item", data=body, headers={"Content-Type": "application/json"},
             method="POST")


def cmd_status():
    try:
        res = json.loads(sync.api(f"/server/database/item?namespace={DB_NAMESPACE}&key=last_deploy"))
        print(json.dumps(res["result"]["value"], indent=2))
    except urllib.error.HTTPError:
        print("no deploy recorded yet")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--yes", "-y", action="store_true", help="skip the confirmation prompt")
    parser.add_argument("--allow-dirty", action="store_true", help="deploy uncommitted working tree")
    parser.add_argument("--delete", action="store_true", help="delete printer files removed from the repo")
    parser.add_argument("--force", action="store_true", help="overwrite unpulled printer-side edits")
    parser.add_argument("--no-restart", action="store_true")
    parser.add_argument("--status", action="store_true", help="show the last recorded deploy")
    args = parser.parse_args()

    if args.status:
        return cmd_status()

    state = print_state()
    if state in ("printing", "paused"):
        sys.exit(f"Printer is {state}; not deploying.")

    dirty = config_dirty()
    if dirty and not args.allow_dirty:
        sys.exit("config/ has uncommitted changes. Commit them first (or use --allow-dirty).")
    commit = head_commit(dirty and args.allow_dirty)

    source = source_files(use_worktree=args.allow_dirty)
    remote = sync.remote_files()
    previous = {}   # printer content before deploy, for rollback
    changed, added, drifted = [], [], []
    for path, content in sorted(source.items()):
        if path not in remote:
            added.append(path)
            continue
        current = sync.norm(sync.download(path))
        if current == content:
            continue
        previous[path] = current
        changed.append(path)
        if blob_hash(current) not in known_blobs(path):
            drifted.append(path)

    removed, unknown = [], []
    for path in sorted(remote.keys() - source.keys()):
        (removed if known_blobs(path) else unknown).append(path)

    for p in changed:
        print(f"update  {p}" + ("   <-- edited on printer since last pull!" if p in drifted else ""))
    for p in added:
        print(f"add     {p}")
    for p in removed:
        print(f"delete  {p}" + ("" if args.delete else "   (skipped, use --delete)"))
    for p in unknown:
        print(f"note    {p} exists only on the printer (not in git); leaving it alone")

    to_delete = removed if args.delete else []
    if not (changed or added or to_delete):
        print(f"Printer already matches {commit}.")
        return
    if drifted and not args.force:
        sys.exit("\nSome printer files have changes that were never pulled. Run "
                 "`python scripts/sync.py pull`, commit, and deploy again (or use --force).")
    if args.dry_run:
        return
    if not args.yes and input(f"\nDeploy {commit} to the printer? [y/N] ").strip().lower() != "y":
        sys.exit("Aborted.")

    for path in to_delete:
        previous[path] = sync.norm(sync.download(path))
        sync.delete(path)
        print(f"deleted {path}")
    for path in changed + added:
        sync.upload(path, source[path])
        print(f"uploaded {path}")

    touched = changed + added + to_delete
    services = sorted({SERVICE_FILES[p] for p in touched if p in SERVICE_FILES})
    needs_klipper = any(p not in SERVICE_FILES for p in touched)

    if args.no_restart:
        print("Uploaded; skipping restarts as requested.")
    else:
        for service in services:
            if service == "moonraker":
                continue  # restart last: it serves this API
            sync.api(f"/machine/services/restart?service={service}", method="POST")
            print(f"restarted {service}")
        if needs_klipper:
            print("Restarting Klipper...")
            restart_klipper()
            state, msg = wait_for_klipper()
            if state != "ready":
                print(f"\nKlipper failed to start ({state}):\n{msg}\n")
                if state == "startup" or "Unable to connect" in msg:
                    print("Klipper can't reach its MCUs. If the mainboard (USB-CAN bridge) was reset for a\n"
                          "config CRC change, check `ssh voron ip -br link show can0` is UP; the Pi needs\n"
                          "`allow-hotplug can0` in /etc/network/interfaces.d/can0.\n")
                print("Rolling back to the previous printer files...")
                for path in added:
                    sync.delete(path)
                for path, content in previous.items():
                    sync.upload(path, content)
                restart_klipper()
                state, msg = wait_for_klipper()
                print(f"Klipper after rollback: {state}" + (f"\n{msg}" if state != "ready" else ""))
                sys.exit(1)
            print("Klipper is ready.")
        if "moonraker" in services:
            print("Restarting Moonraker...")
            try:
                sync.api("/server/restart", method="POST")
            except (urllib.error.URLError, ConnectionError):
                pass
            if not wait_for_moonraker():
                sys.exit("Moonraker did not come back; check moonraker.log over SSH (`ssh voron`).")
            print("Moonraker is back.")

    record_deploy(commit, touched)
    print(f"Deployed {commit}.")


if __name__ == "__main__":
    main()
